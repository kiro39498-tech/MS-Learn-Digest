"""HTTP JSON-RPC client for the Microsoft Learn MCP server."""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class MCPClientError(RuntimeError):
    """Raised when the MCP server cannot satisfy a request."""


class MicrosoftLearnMCPClient:
    """
    Minimal MCP client for the Microsoft Learn remote server.

    The client intentionally depends only on httpx so the integration remains
    lightweight. It supports standard MCP methods used here:
    initialize, notifications/initialized, tools/list, and tools/call.
    """

    def __init__(
        self,
        server_url: str | None = None,
        timeout: float | None = None,
        retries: int | None = None,
    ) -> None:
        self.server_url = (server_url or settings.MCP_SERVER_URL or "").strip()
        self.timeout = timeout if timeout is not None else settings.MCP_TIMEOUT
        self.retries = retries if retries is not None else settings.MCP_RETRIES
        self._session_id: str | None = None
        self._initialized = False
        self._request_id = 0
        self._tool_name_cache: dict[str, str] = {}

    async def list_tools(self) -> list[dict[str, Any]]:
        """Return tools exposed by the configured MCP server."""
        if not self.server_url:
            logger.warning("MCP | list_tools | skipped: MCP_SERVER_URL is not set")
            return []
        await self._initialize()
        payload = await self._request("tools/list", {})
        return payload.get("tools", []) if isinstance(payload, dict) else []

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Call an MCP tool and return its result payload."""
        if not self.server_url:
            logger.warning("MCP | call_tool | skipped: MCP_SERVER_URL is not set")
            return None
        await self._initialize()
        return await self._request(
            "tools/call",
            {"name": tool_name, "arguments": arguments},
        )

    async def search(self, query: str) -> list[dict[str, Any]]:
        """
        Search official Microsoft Learn documentation through MCP.

        The Microsoft Learn MCP server exposes a documentation search tool. The
        code discovers that tool when possible and falls back to the public name
        used by Microsoft examples.
        """
        tool_name = await self._resolve_search_tool()
        raw = await self.call_tool(tool_name, {"query": query})
        text_items = self._extract_text_items(raw)
        results: list[dict[str, Any]] = []

        for item in text_items:
            parsed = self._try_parse_json(item)
            if parsed is None:
                url = self._extract_learn_url(item)
                results.append({
                    "title": query,
                    "url": url,
                    "content": item,
                    "source": "learn.microsoft.com",
                    "document_id": url,
                })
                continue
            if isinstance(parsed, dict) and "results" in parsed and isinstance(parsed["results"], list):
                for entry in parsed["results"]:
                    ref = self._coerce_reference(entry, query)
                    if ref:
                        results.append(ref)
            elif isinstance(parsed, list):
                for entry in parsed:
                    ref = self._coerce_reference(entry, query)
                    if ref:
                        results.append(ref)
            else:
                ref = self._coerce_reference(parsed, query)
                if ref:
                    results.append(ref)

        logger.info("MCP | search | query=%r results=%s", query, len(results))
        return results

    async def fetch(self, document_id: str, url: str = "") -> dict[str, Any] | None:
        """
        Fetch a full Microsoft Learn document through MCP.

        Tool names and argument schemas can vary between MCP server versions, so
        the client discovers a documentation fetch/read tool and tries the common
        argument shapes. The returned payload is normalized into a document dict.
        """
        if not document_id and not url:
            return None

        tool_name = await self._resolve_fetch_tool()
        argument_sets = [
            {"document_id": document_id},
            {"id": document_id},
            {"url": url or document_id},
        ]
        last_error: Exception | None = None
        for arguments in argument_sets:
            if not next(iter(arguments.values())):
                continue
            try:
                raw = await self.call_tool(tool_name, arguments)
                document = self._coerce_document(raw, document_id=document_id, url=url)
                if document:
                    logger.info(
                        "MCP | fetch | tool=%s document_id=%s url=%s markdown_len=%s",
                        tool_name,
                        document.get("document_id"),
                        document.get("url"),
                        len(document.get("content", "")),
                    )
                    return document
            except Exception as exc:
                last_error = exc
                logger.debug(
                    "MCP | fetch argument shape failed | tool=%s args=%s | %s",
                    tool_name,
                    list(arguments),
                    exc,
                )

        if last_error:
            raise MCPClientError(f"MCP fetch failed for {document_id or url}: {last_error}")
        return None

    async def _resolve_search_tool(self) -> str:
        return await self._resolve_tool(
            cache_key="search",
            fallback="microsoft_docs_search",
            preferred_terms=(("docs", "search"), ("learn", "search"), ("search",)),
        )

    async def _resolve_fetch_tool(self) -> str:
        return await self._resolve_tool(
            cache_key="fetch",
            fallback="microsoft_docs_fetch",
            preferred_terms=(
                ("docs", "fetch"),
                ("docs", "get"),
                ("docs", "read"),
                ("learn", "fetch"),
                ("learn", "get"),
                ("document", "fetch"),
                ("document", "read"),
                ("fetch",),
                ("read",),
                ("get",),
            ),
        )

    async def _resolve_tool(
        self,
        cache_key: str,
        fallback: str,
        preferred_terms: tuple[tuple[str, ...], ...],
    ) -> str:
        if cache_key in self._tool_name_cache:
            return self._tool_name_cache[cache_key]

        try:
            tools = await self.list_tools()
        except Exception as exc:
            logger.warning("MCP | tools/list failed; using fallback tool | %s", exc)
            self._tool_name_cache[cache_key] = fallback
            return fallback

        names = [str(t.get("name", "")) for t in tools]
        for terms in preferred_terms:
            for candidate in names:
                lower = candidate.lower()
                if all(term in lower for term in terms):
                    self._tool_name_cache[cache_key] = candidate
                    return candidate

        self._tool_name_cache[cache_key] = fallback
        return fallback

    async def _initialize(self) -> None:
        if self._initialized:
            return

        params = {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "ms-learn-digest", "version": "1.0.0"},
        }
        await self._request("initialize", params)
        try:
            await self._notify("notifications/initialized", {})
        except Exception as exc:
            logger.debug("MCP | initialized notification skipped | %s", exc)
        self._initialized = True

    async def _request(self, method: str, params: dict[str, Any]) -> Any:
        self._request_id += 1
        request_id = self._request_id
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }
        response = await self._post(payload, method)
        if "error" in response:
            raise MCPClientError(f"{method} failed: {response['error']}")
        return response.get("result")

    async def _notify(self, method: str, params: dict[str, Any]) -> None:
        payload = {"jsonrpc": "2.0", "method": method, "params": params}
        await self._post(payload, method)

    async def _post(self, payload: dict[str, Any], method: str) -> dict[str, Any]:
        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        }
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id

        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            started = time.monotonic()
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        self.server_url,
                        json=payload,
                        headers=headers,
                    )
                latency_ms = int((time.monotonic() - started) * 1000)
                session_id = response.headers.get("mcp-session-id")
                if session_id:
                    self._session_id = session_id
                logger.info(
                    "MCP | request | method=%s status=%s latency_ms=%s attempt=%s",
                    method,
                    response.status_code,
                    latency_ms,
                    attempt + 1,
                )
                response.raise_for_status()
                if response.status_code == 202 or not response.content:
                    return {}
                return self._parse_response_payload(response)
            except Exception as exc:
                last_error = exc
                if attempt >= self.retries:
                    break
                await asyncio.sleep(min(0.25 * (2 ** attempt), 2.0))

        raise MCPClientError(f"MCP request failed for {method}: {last_error}")

    @staticmethod
    def _parse_response_payload(response: httpx.Response) -> dict[str, Any]:
        content_type = response.headers.get("content-type", "")
        if "text/event-stream" in content_type:
            for line in response.text.splitlines():
                line = line.strip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data and data != "[DONE]":
                    return json.loads(data)
            return {}
        return response.json()

    @staticmethod
    def _extract_text_items(raw: Any) -> list[str]:
        if raw is None:
            return []
        if isinstance(raw, str):
            return [raw]
        if isinstance(raw, list):
            items: list[str] = []
            for entry in raw:
                items.extend(MicrosoftLearnMCPClient._extract_text_items(entry))
            return items
        if not isinstance(raw, dict):
            return [str(raw)]

        content = raw.get("content")
        if isinstance(content, list):
            items = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    items.append(str(part.get("text", "")))
                else:
                    items.extend(MicrosoftLearnMCPClient._extract_text_items(part))
            return [item for item in items if item]

        for key in ("text", "content", "result"):
            value = raw.get(key)
            if isinstance(value, str):
                return [value]
        return [json.dumps(raw)]

    @staticmethod
    def _try_parse_json(value: str) -> Any:
        try:
            return json.loads(value)
        except Exception:
            return None

    @staticmethod
    def _coerce_reference(value: Any, default_title: str) -> dict[str, Any] | None:
        if not isinstance(value, dict):
            return None

        url = (
            value.get("url")
            or value.get("contentUrl")
            or value.get("sourceUrl")
            or value.get("href")
            or value.get("link")
            or ""
        )
        title = value.get("title") or value.get("name") or default_title
        content = (
            value.get("content")
            or value.get("snippet")
            or value.get("summary")
            or value.get("text")
            or ""
        )
        document_id = (
            value.get("document_id")
            or value.get("documentId")
            or value.get("id")
            or value.get("uid")
            or value.get("chunk_id")
            or value.get("chunkId")
            or url
        )

        return {
            "title": str(title),
            "url": str(url),
            "content": str(content),
            "source": "learn.microsoft.com",
            "document_id": str(document_id),
        }

    @classmethod
    def _coerce_document(
        cls,
        raw: Any,
        document_id: str = "",
        url: str = "",
    ) -> dict[str, Any] | None:
        """Normalize a fetch/read tool response into a full document."""
        candidates = cls._extract_candidate_dicts(raw)
        text_items = cls._extract_text_items(raw)
        non_json_texts = []
        for text in text_items:
            parsed = cls._try_parse_json(text)
            if parsed is not None:
                candidates.extend(cls._extract_candidate_dicts(parsed))
            else:
                non_json_texts.append(text)
        if non_json_texts:
            candidates.append({"content": "\n".join(non_json_texts)})

        merged: dict[str, Any] = {}
        for candidate in candidates:
            merged.update({k: v for k, v in candidate.items() if v not in (None, "")})

        if not merged:
            return None

        content = (
            merged.get("markdown")
            or merged.get("content")
            or merged.get("text")
            or merged.get("body")
            or merged.get("html")
            or ""
        )
        if isinstance(content, list):
            text_parts = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    text_parts.append(str(part.get("text", "")))
                elif isinstance(part, str):
                    text_parts.append(part)
            content = "\n".join(text_parts)
        resolved_url = (
            merged.get("url")
            or merged.get("contentUrl")
            or merged.get("sourceUrl")
            or merged.get("href")
            or url
            or cls._extract_learn_url(str(content))
            or ""
        )
        resolved_id = (
            merged.get("document_id")
            or merged.get("documentId")
            or merged.get("id")
            or document_id
            or resolved_url
        )
        title = (
            merged.get("title")
            or merged.get("name")
            or merged.get("heading")
            or document_id
            or resolved_url
            or "Microsoft Learn documentation"
        )
        summary = (
            merged.get("summary")
            or merged.get("description")
            or merged.get("snippet")
            or ""
        )

        return {
            "title": str(title),
            "url": str(resolved_url),
            "summary": str(summary),
            "content": str(content),
            "metadata": merged.get("metadata") or merged.get("meta") or {},
            "document_id": str(resolved_id),
            "source": "Microsoft Learn",
        }

    @classmethod
    def _extract_candidate_dicts(cls, raw: Any) -> list[dict[str, Any]]:
        if isinstance(raw, dict):
            candidates = [raw]
            for key in ("result", "document", "page", "data", "metadata"):
                value = raw.get(key)
                if value is not raw:
                    candidates.extend(cls._extract_candidate_dicts(value))
            content = raw.get("content")
            if isinstance(content, list):
                candidates.extend(cls._extract_candidate_dicts(content))
            return candidates
        if isinstance(raw, list):
            candidates: list[dict[str, Any]] = []
            for item in raw:
                candidates.extend(cls._extract_candidate_dicts(item))
            return candidates
        return []

    @staticmethod
    def _extract_learn_url(text: str) -> str:
        match = re.search(r"https://learn\.microsoft\.com/[^\s)>\"]+", text)
        return match.group(0) if match else ""
