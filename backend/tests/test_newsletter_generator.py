import pytest
import time
from typing import Any
from unittest.mock import MagicMock, patch

from app.services.lesson.quality_reviewer import (
    normalize_lesson_data,
    validate_email_context,
    EmailContextValidationError,
)
from app.services.mcp.client import MicrosoftLearnMCPClient
from app.services.learning.resource_discovery import _search_duckduckgo


# ── Normalization Tests ──

def test_normalization_valid_case():
    lesson = {
        "today_goal": "Learn tests",
        "real_world_example": {
            "company_type": "SaaS",
            "scenario": "A SaaS team tests their code",
            "implementation_notes": ["Note 1", "Note 2"]
        }
    }
    normalized = normalize_lesson_data(lesson)
    assert normalized["today_goal"] == "Learn tests"
    assert normalized["real_world_example"]["company_type"] == "SaaS"
    assert normalized["real_world_example"]["implementation_notes"] == ["Note 1", "Note 2"]
    assert normalized["real_world_example"]["lessons_learned"] == ["Note 1", "Note 2"]


def test_normalization_missing_fields_defaults():
    lesson = {}
    normalized = normalize_lesson_data(lesson)
    assert normalized["today_goal"] == ""
    assert normalized["real_world_example"]["company_type"] == "Enterprise Scenario"
    assert normalized["real_world_example"]["scenario"] == ""
    assert normalized["real_world_example"]["implementation_notes"] == []


def test_normalization_string_instead_of_dict_rw():
    lesson = {
        "real_world_example": "This is a single scenario string."
    }
    normalized = normalize_lesson_data(lesson)
    assert normalized["real_world_example"]["company_type"] == "Enterprise Scenario"
    assert normalized["real_world_example"]["scenario"] == "This is a single scenario string."
    assert normalized["real_world_example"]["implementation_notes"] == []


def test_normalization_list_of_strings_rw():
    lesson = {
        "real_world_example": ["Scenario part 1.", "Scenario part 2."]
    }
    normalized = normalize_lesson_data(lesson)
    assert normalized["real_world_example"]["company_type"] == "Enterprise Scenario"
    assert normalized["real_world_example"]["scenario"] == "Scenario part 1. Scenario part 2."
    assert normalized["real_world_example"]["implementation_notes"] == []


def test_normalization_empty_arrays():
    lesson = {
        "best_practices": [],
        "summary": [],
        "key_concepts": [],
        "quiz": [],
        "questions": {}
    }
    normalized = normalize_lesson_data(lesson)
    assert normalized["best_practices"] == []
    assert normalized["summary"] == []
    assert normalized["key_concepts"] == []
    assert normalized["quiz"] == []
    assert normalized["questions"] == {"beginner": [], "advanced": []}


# ── Context Validation Tests ──

def test_validate_context_success():
    context = {
        "topic_name": "Azure",
        "module_title": "Functions",
        "module_number": 1,
        "total_modules": 5,
        "progress_pct": 20,
        "modules_remaining": 4,
        "streak_days": 3,
        "today_goal": "Goal",
        "why_this_matters": "Matters",
        "business_relevance": "Biz",
        "introduction": "Intro",
        "explanation": "Expl",
        "architecture_diagram": "Diagram",
        "key_concepts": [],
        "real_world_example": {},
        "code_walkthrough": {},
        "hands_on_activity": {},
        "practical_exercise": {},
        "common_mistakes": [],
        "troubleshooting_tips": [],
        "best_practices": [],
        "summary": [],
        "questions": {},
        "quiz": [],
        "further_reading": [],
        "resource_links": [],
    }
    # Should not raise any exception
    validate_email_context(context)


def test_validate_context_type_mismatch():
    context = {
        "topic_name": "Azure",
        "real_world_example": "Should be a dict"
    }
    with pytest.raises(EmailContextValidationError) as exc_info:
        validate_email_context(context)
    assert "real_world_example" in str(exc_info.value)


# ── MCP Client Response Parser Tests ──

def test_mcp_client_search_results_dict():
    client = MicrosoftLearnMCPClient()
    
    # Simulate list-inside-dict search response
    raw_search = {
        "results": [
            {
                "title": "Azure Functions",
                "contentUrl": "https://learn.microsoft.com/azure-functions",
                "content": "Serverless compute",
                "id": "azure-fns-id"
            }
        ]
    }
    
    # We patch call_tool to return a text-stream block containing our JSON
    with patch.object(client, "call_tool") as mock_call:
        mock_call.return_value = {
            "content": [
                {
                    "type": "text",
                    "text": json_str(raw_search)
                }
            ]
        }
        
        results = asyncio_run(client.search("Azure Functions"))
        assert len(results) == 1
        assert results[0]["title"] == "Azure Functions"
        assert results[0]["url"] == "https://learn.microsoft.com/azure-functions"
        assert results[0]["document_id"] == "azure-fns-id"


def test_mcp_client_coerce_document_content_list():
    raw_fetch = {
        "content": [
            {
                "type": "text",
                "text": "Line 1 of documentation."
            },
            {
                "type": "text",
                "text": "Line 2 of documentation."
            }
        ],
        "url": "https://learn.microsoft.com/doc",
        "title": "Documentation Title"
    }
    
    coerced = MicrosoftLearnMCPClient._coerce_document(raw_fetch, document_id="doc-id")
    assert coerced is not None
    assert coerced["title"] == "Documentation Title"
    assert coerced["url"] == "https://learn.microsoft.com/doc"
    assert coerced["content"] == "Line 1 of documentation.\nLine 2 of documentation."


# ── DuckDuckGo Search Fallback Retry Tests ──

def test_duckduckgo_search_exponential_backoff():
    # Mock DDGS context manager to raise rate limiting errors, then succeed
    mock_ddgs_instance = MagicMock()
    
    # Mock text method to raise exceptions
    calls = []
    def mock_text(*args, **kwargs):
        calls.append(kwargs.get("query", ""))
        if len(calls) < 3:
            raise Exception("HTTP 202 Rate Limit")
        return [{"href": "https://microsoft.com/doc", "title": "Success"}]
        
    mock_ddgs_instance.text = mock_text
    
    with patch("duckduckgo_search.DDGS") as mock_ddgs, patch("time.sleep") as mock_sleep:
        mock_ddgs.return_value.__enter__.return_value = mock_ddgs_instance
        
        urls = _search_duckduckgo("test query")
        
        # Should have retried 3 times (attempts 1, 2 failed; attempt 3 succeeded)
        assert len(calls) == 3
        assert urls == ["https://microsoft.com/doc"]
        
        # Sleeps should be 1.0s and 2.0s
        mock_sleep.assert_any_call(1.0)
        mock_sleep.assert_any_call(2.0)


# ── Helper utilities ──

def json_str(obj: Any) -> str:
    import json
    return json.dumps(obj)


def asyncio_run(coro):
    import asyncio
    return asyncio.run(coro)
