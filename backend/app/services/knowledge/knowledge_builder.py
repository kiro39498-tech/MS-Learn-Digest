"""Normalize module metadata and Microsoft Learn context into one object."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import hashlib
import json
import re


@dataclass
class KnowledgeObject:
    """Pure data object consumed by focused lesson generators."""

    topic_name: str
    module_title: str
    sequence_number: int
    total_modules: int
    learning_objectives: list[str]
    keywords: list[str]
    difficulty: str
    skill_level: str
    phase_name: str = ""
    is_milestone: bool = False
    official_documentation: list[dict[str, Any]] = field(default_factory=list)
    documentation_summary: str = ""
    architecture_guidance: list[dict[str, Any]] = field(default_factory=list)
    best_practices: list[dict[str, Any]] = field(default_factory=list)
    code_samples: list[dict[str, Any]] = field(default_factory=list)
    official_urls: list[str] = field(default_factory=list)
    api_references: list[dict[str, Any]] = field(default_factory=list)
    estimated_duration_minutes: int | None = None
    documentation_hash: str = ""
    source_status: str = "available"

    def to_dict(self) -> dict[str, Any]:
        return {
            "topic_name": self.topic_name,
            "module_title": self.module_title,
            "sequence_number": self.sequence_number,
            "total_modules": self.total_modules,
            "learning_objectives": self.learning_objectives,
            "keywords": self.keywords,
            "difficulty": self.difficulty,
            "skill_level": self.skill_level,
            "phase_name": self.phase_name,
            "is_milestone": self.is_milestone,
            "official_documentation": self.official_documentation,
            "documentation_summary": self.documentation_summary,
            "architecture_guidance": self.architecture_guidance,
            "best_practices": self.best_practices,
            "code_samples": self.code_samples,
            "official_urls": self.official_urls,
            "api_references": self.api_references,
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "documentation_hash": self.documentation_hash,
            "source_status": self.source_status,
        }


class KnowledgeBuilder:
    """Build KnowledgeObject without AI generation."""

    def build(
        self,
        *,
        topic_name: str,
        module_title: str,
        sequence_number: int,
        total_modules: int,
        learning_objectives: list[str],
        keywords: list[str],
        difficulty_level: str,
        resources: list[dict[str, Any]],
        phase_name: str = "",
        is_milestone: bool = False,
        skill_level: str = "",
        mcp_context: str = "",
    ) -> KnowledgeObject:
        normalized_resources = [_normalize_resource(r) for r in resources or []]
        official_docs = [r for r in normalized_resources if _is_official(r)]
        code_samples = [r for r in official_docs if _looks_like_code_sample(r)]
        best_practices = [r for r in official_docs if _looks_like_best_practice(r)]
        architecture_guidance = [r for r in official_docs if _looks_like_architecture(r)]
        api_references = [r for r in official_docs if _looks_like_api_reference(r)]
        official_urls = _dedupe([r["url"] for r in official_docs if r.get("url")])
        documentation_summary = _build_summary(official_docs, mcp_context)
        documentation_hash = _hash_payload({
            "topic": topic_name,
            "module": module_title,
            "urls": official_urls,
            "summary": documentation_summary,
            "content": [r.get("content", "")[:1000] for r in official_docs],
        })

        return KnowledgeObject(
            topic_name=topic_name,
            module_title=module_title,
            sequence_number=sequence_number,
            total_modules=total_modules,
            learning_objectives=list(learning_objectives or []),
            keywords=list(keywords or []),
            difficulty=difficulty_level,
            skill_level=skill_level or difficulty_level,
            phase_name=phase_name,
            is_milestone=is_milestone,
            official_documentation=official_docs,
            documentation_summary=documentation_summary,
            architecture_guidance=architecture_guidance,
            best_practices=best_practices,
            code_samples=code_samples,
            official_urls=official_urls,
            api_references=api_references,
            documentation_hash=documentation_hash,
            source_status="available" if official_docs else "temporarily_unavailable",
        )


def _normalize_resource(resource: dict[str, Any]) -> dict[str, Any]:
    url = str(resource.get("url") or "")
    content = str(resource.get("content") or resource.get("summary") or "")
    title = str(resource.get("title") or url or "Microsoft Learn documentation")
    return {
        "title": title,
        "url": url,
        "content": _clean_text(content),
        "summary": _clean_text(str(resource.get("summary") or "")),
        "source": str(resource.get("source") or ""),
        "language": str(resource.get("language") or _infer_language(title, url, content)),
        "document_id": str(resource.get("document_id") or url),
        "metadata": resource.get("metadata") or {},
    }


def _is_official(resource: dict[str, Any]) -> bool:
    haystack = f"{resource.get('url', '')} {resource.get('source', '')}".lower()
    return "learn.microsoft.com" in haystack or "microsoft learn" in haystack


def _looks_like_code_sample(resource: dict[str, Any]) -> bool:
    haystack = _resource_haystack(resource)
    return any(term in haystack for term in ("sample", "code", "python", "c#", "cli", "powershell"))


def _looks_like_best_practice(resource: dict[str, Any]) -> bool:
    haystack = _resource_haystack(resource)
    return any(term in haystack for term in ("best practice", "security", "reliability", "performance", "governance"))


def _looks_like_architecture(resource: dict[str, Any]) -> bool:
    haystack = _resource_haystack(resource)
    return any(term in haystack for term in ("architecture", "design", "flow", "reference architecture"))


def _looks_like_api_reference(resource: dict[str, Any]) -> bool:
    haystack = _resource_haystack(resource)
    return "api" in haystack or "/api/" in haystack or "reference" in haystack


def _resource_haystack(resource: dict[str, Any]) -> str:
    return " ".join([
        str(resource.get("title", "")),
        str(resource.get("url", "")),
        str(resource.get("content", "")),
    ]).lower()


def _build_summary(resources: list[dict[str, Any]], mcp_context: str) -> str:
    parts: list[str] = []
    if mcp_context and "temporarily unavailable" not in mcp_context.lower():
        parts.append(_clean_text(mcp_context)[:2500])
    for resource in resources[:6]:
        summary = resource.get("summary") or _first_sentences(resource.get("content", ""))
        if summary:
            parts.append(f"{resource.get('title')}: {summary}")
    return "\n".join(parts)[:6000]


def _first_sentences(text: str, max_sentences: int = 3) -> str:
    clean = _clean_text(text)
    sentences = re.split(r"(?<=[.!?])\s+", clean)
    return " ".join(sentences[:max_sentences])[:900]


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _infer_language(title: str, url: str, content: str) -> str:
    haystack = f"{title} {url} {content}".lower()
    if "python" in haystack:
        return "Python"
    if "c#" in haystack or "csharp" in haystack:
        return "C#"
    if "azure cli" in haystack or " az " in haystack:
        return "Azure CLI"
    if "powershell" in haystack:
        return "PowerShell"
    return ""


def _hash_payload(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
