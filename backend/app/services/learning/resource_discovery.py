"""
Resource Discovery Service

Discovers relevant Microsoft learning resources for a module using
DuckDuckGo search, then extracts clean content with BeautifulSoup.

Priority order for results:
  1. learn.microsoft.com
  2. microsoft.com
  3. azure.microsoft.com
  4. Any other official Microsoft domain

The extracted content is passed to the Groq lesson generator as context.
This service is only called once per module (lesson caching prevents repeats).
"""

import logging
import time
from typing import List, Dict
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Preferred Microsoft domains (higher score = higher priority)
_DOMAIN_PRIORITY = {
    "learn.microsoft.com": 10,
    "microsoft.com": 8,
    "azure.microsoft.com": 8,
    "techcommunity.microsoft.com": 6,
    "docs.microsoft.com": 9,
    "devblogs.microsoft.com": 5,
}

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

_FETCH_TIMEOUT = 10   # seconds per page
_MAX_CONTENT_CHARS = 4000   # chars per page to pass to LLM
_MAX_RESOURCES = 3          # how many pages to scrape per module


def _domain_score(url: str) -> int:
    """Return priority score for a URL's domain. Higher is better."""
    try:
        netloc = urlparse(url).netloc.lower()
        for domain, score in _DOMAIN_PRIORITY.items():
            if domain in netloc:
                return score
    except Exception:
        pass
    return 1


def _search_duckduckgo(query: str, max_results: int = 10) -> List[str]:
    """
    Search DuckDuckGo for relevant URLs.
    Uses the duckduckgo_search library.
    Returns a list of URLs sorted by domain priority.
    """
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        urls = [r.get("href") or r.get("url", "") for r in results if r]
        urls = [u for u in urls if u.startswith("http")]
        # Sort by domain priority (descending)
        urls.sort(key=_domain_score, reverse=True)
        logger.info(f"DISCOVERY | query={query!r} | found={len(urls)} URLs")
        return urls
    except ImportError:
        logger.warning("DISCOVERY | duckduckgo_search not installed — returning empty results")
        return []
    except Exception as exc:
        logger.warning(f"DISCOVERY | DuckDuckGo search failed: {exc}")
        return []


def _extract_content(url: str) -> str:
    """
    Fetch a page and extract meaningful text content.
    Removes navigation, footer, ads, scripts, and boilerplate.
    Returns up to _MAX_CONTENT_CHARS of clean text.
    """
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=_FETCH_TIMEOUT)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")

        # Remove noise elements
        for tag in soup(["script", "style", "nav", "footer", "header",
                         "aside", "form", "button", "iframe", "noscript",
                         ".navigation", ".sidebar", ".ads", ".cookie-banner"]):
            tag.decompose()

        # Try to get the main content area first
        main = (
            soup.find("main")
            or soup.find("article")
            or soup.find(id="main-content")
            or soup.find(class_="content")
            or soup.find(class_="main")
            or soup.body
        )

        if main:
            text = main.get_text(separator="\n", strip=True)
        else:
            text = soup.get_text(separator="\n", strip=True)

        # Clean up excessive whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean = "\n".join(lines)

        return clean[:_MAX_CONTENT_CHARS]

    except requests.exceptions.Timeout:
        logger.warning(f"DISCOVERY | TIMEOUT | {url}")
        return ""
    except requests.exceptions.HTTPError as exc:
        logger.warning(f"DISCOVERY | HTTP_ERROR | {url} | {exc}")
        return ""
    except Exception as exc:
        logger.warning(f"DISCOVERY | EXTRACT_FAIL | {url} | {exc}")
        return ""


def discover_resources(
    topic_name: str,
    module_title: str,
    keywords: List[str],
) -> List[Dict]:
    """
    Discover and extract learning resources for a module.

    Returns a list of dicts:
      [{"title": str, "url": str, "source": str, "content": str}]

    The "content" field contains extracted page text (used as LLM context).
    """
    results = []

    # Build search queries
    queries = [
        f"{module_title} {topic_name} Microsoft Learn",
        f"{module_title} {topic_name} documentation site:learn.microsoft.com",
    ]
    if keywords:
        kw_str = " ".join(keywords[:3])
        queries.append(f"{kw_str} microsoft learn tutorial")

    seen_urls: set = set()
    candidate_urls: List[str] = []

    for query in queries:
        if len(candidate_urls) >= _MAX_RESOURCES * 3:
            break
        urls = _search_duckduckgo(query, max_results=8)
        for url in urls:
            if url not in seen_urls:
                seen_urls.add(url)
                candidate_urls.append(url)

    # Sort by priority and take top candidates
    candidate_urls.sort(key=_domain_score, reverse=True)
    candidate_urls = candidate_urls[:_MAX_RESOURCES * 2]

    for url in candidate_urls:
        if len(results) >= _MAX_RESOURCES:
            break
        logger.info(f"DISCOVERY | scraping: {url}")
        content = _extract_content(url)
        if len(content) < 200:
            logger.debug(f"DISCOVERY | too little content from {url}, skipping")
            continue

        # Extract page title from URL path as fallback
        try:
            path_parts = urlparse(url).path.strip("/").split("/")
            page_title = path_parts[-1].replace("-", " ").replace("_", " ").title() if path_parts else module_title
        except Exception:
            page_title = module_title

        results.append({
            "title": page_title,
            "url": url,
            "source": urlparse(url).netloc,
            "content": content,
        })
        time.sleep(0.5)   # polite crawl delay

    logger.info(f"DISCOVERY | {module_title} | scraped {len(results)} resources")
    return results
