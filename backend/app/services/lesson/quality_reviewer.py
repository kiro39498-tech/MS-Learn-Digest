"""Deterministic quality checks for merged lesson JSON."""

from __future__ import annotations

from typing import Any
import logging

logger = logging.getLogger(__name__)


class EmailContextValidationError(ValueError):
    """Raised when email context validation fails."""
    pass


class QualityReviewer:
    """Validate required sections and repair safe missing values."""

    def review(self, lesson: dict[str, Any]) -> dict[str, Any]:
        lesson = normalize_lesson_data(lesson)
        lesson.setdefault("today_goal", "")
        lesson.setdefault("introduction", "")
        lesson.setdefault("explanation", "")
        lesson.setdefault("key_concepts", [])
        lesson.setdefault("best_practices", [])
        lesson.setdefault("common_mistakes", [])
        lesson.setdefault("quiz", [])
        lesson.setdefault("questions", {"beginner": [], "advanced": []})
        lesson.setdefault("summary", [])
        lesson.setdefault("practical_exercise", {})
        lesson.setdefault("architecture_diagram", "No diagram available.")
        lesson["further_reading"] = [
            item for item in lesson.get("further_reading", [])
            if item.get("url", "").startswith("https://learn.microsoft.com")
        ]
        if not _valid_mermaid(lesson.get("architecture_diagram", "")):
            lesson["architecture_diagram"] = "No diagram available."
        missing = [
            key for key in ("today_goal", "introduction", "explanation")
            if not lesson.get(key)
        ]
        if missing:
            logger.warning("QUALITY_REVIEW | missing scalar sections=%s", missing)
        return lesson


def _valid_mermaid(value: str) -> bool:
    if value == "No diagram available.":
        return True
    stripped = (value or "").strip()
    return stripped.startswith(("graph ", "flowchart ", "sequenceDiagram"))


def normalize_lesson_data(lesson: dict[str, Any]) -> dict[str, Any]:
    """Recursively normalize lesson fields to prevent rendering failures."""
    if not isinstance(lesson, dict):
        return {}

    # Ensure scalar fields
    for field in ("today_goal", "introduction", "explanation", "why_this_matters", "business_relevance", "architecture_diagram"):
        val = lesson.get(field)
        if val is None:
            lesson[field] = ""
        elif not isinstance(val, str):
            lesson[field] = str(val)

    # Ensure list of strings fields
    for field in ("best_practices", "summary"):
        val = lesson.get(field)
        if val is None:
            lesson[field] = []
        elif isinstance(val, str):
            lesson[field] = [val]
        elif isinstance(val, list):
            lesson[field] = [str(x) for x in val]
        else:
            lesson[field] = [str(val)]

    # Normalize real_world_example
    rw = lesson.get("real_world_example")
    if rw is None:
        lesson["real_world_example"] = {
            "company_type": "Enterprise Scenario",
            "scenario": "",
            "implementation_notes": []
        }
    elif isinstance(rw, str):
        lesson["real_world_example"] = {
            "company_type": "Enterprise Scenario",
            "scenario": rw,
            "implementation_notes": []
        }
    elif isinstance(rw, list):
        if all(isinstance(x, str) for x in rw):
            lesson["real_world_example"] = {
                "company_type": "Enterprise Scenario",
                "scenario": " ".join(rw),
                "implementation_notes": []
            }
        elif len(rw) > 0 and isinstance(rw[0], dict):
            lesson["real_world_example"] = _normalize_rw_dict(rw[0])
        else:
            lesson["real_world_example"] = {
                "company_type": "Enterprise Scenario",
                "scenario": str(rw),
                "implementation_notes": []
            }
    elif isinstance(rw, dict):
        lesson["real_world_example"] = _normalize_rw_dict(rw)
    else:
        lesson["real_world_example"] = {
            "company_type": "Enterprise Scenario",
            "scenario": str(rw),
            "implementation_notes": []
        }

    # Normalize key_concepts
    concepts = lesson.get("key_concepts")
    if not isinstance(concepts, list):
        lesson["key_concepts"] = []
    else:
        normalized_concepts = []
        for c in concepts:
            if isinstance(c, dict):
                normalized_concepts.append({
                    "term": str(c.get("term") or c.get("name") or "Concept"),
                    "definition": str(c.get("definition") or c.get("desc") or "")
                })
            elif isinstance(c, str):
                normalized_concepts.append({
                    "term": c,
                    "definition": ""
                })
        lesson["key_concepts"] = normalized_concepts

    # Normalize quiz
    quiz = lesson.get("quiz")
    if not isinstance(quiz, list):
        lesson["quiz"] = []
    else:
        normalized_quiz = []
        for q in quiz:
            if isinstance(q, dict):
                options = q.get("options")
                if not isinstance(options, list):
                    options = [str(options)] if options is not None else []
                options = [str(o) for o in options]
                normalized_quiz.append({
                    "question": str(q.get("question") or ""),
                    "options": options,
                    "correct_answer": str(q.get("correct_answer") or ""),
                    "explanation": str(q.get("explanation") or "")
                })
        lesson["quiz"] = normalized_quiz

    # Normalize questions
    qs = lesson.get("questions")
    if not isinstance(qs, dict):
        lesson["questions"] = {"beginner": [], "advanced": []}
    else:
        for lvl in ("beginner", "advanced"):
            lvl_list = qs.get(lvl)
            if not isinstance(lvl_list, list):
                qs[lvl] = []
            else:
                normalized_lvl = []
                for q in lvl_list:
                    if isinstance(q, dict):
                        normalized_lvl.append({
                            "question": str(q.get("question") or ""),
                            "model_answer": str(q.get("model_answer") or q.get("answer") or "")
                        })
                qs[lvl] = normalized_lvl
        lesson["questions"] = qs

    return lesson


def _normalize_rw_dict(rw: dict) -> dict:
    company_type = str(rw.get("company_type") or rw.get("company") or "Enterprise Scenario")
    scenario = str(rw.get("scenario") or rw.get("description") or "")
    notes_raw = rw.get("implementation_notes") or rw.get("lessons_learned") or []
    if isinstance(notes_raw, str):
        notes = [notes_raw]
    elif isinstance(notes_raw, list):
        notes = [str(x) for x in notes_raw]
    else:
        notes = [str(notes_raw)] if notes_raw else []
    return {
        "company_type": company_type,
        "scenario": scenario,
        "implementation_notes": notes,
        "lessons_learned": notes
    }


def validate_email_context(context: dict[str, Any]) -> None:
    expected_types = {
        "topic_name": str,
        "module_title": str,
        "module_number": int,
        "total_modules": int,
        "progress_pct": int,
        "modules_remaining": int,
        "streak_days": int,
        "today_goal": str,
        "why_this_matters": str,
        "business_relevance": str,
        "introduction": str,
        "explanation": str,
        "architecture_diagram": str,
        "key_concepts": list,
        "real_world_example": dict,
        "code_walkthrough": dict,
        "hands_on_activity": dict,
        "practical_exercise": dict,
        "common_mistakes": list,
        "troubleshooting_tips": list,
        "best_practices": list,
        "summary": list,
        "questions": dict,
        "quiz": list,
        "further_reading": list,
        "resource_links": list,
    }
    
    for field, expected_type in expected_types.items():
        if field not in context:
            continue
        val = context[field]
        if val is None:
            continue
        if not isinstance(val, expected_type):
            logger.error(
                "EMAIL_CONTEXT_VALIDATION\n\nField:\n%s\n\nExpected:\n%s\n\nActual:\n%s\n\nValue:\n%s",
                field,
                expected_type.__name__,
                type(val).__name__,
                f'"{str(val)[:200]}"' if isinstance(val, str) else str(val)[:200]
            )
            raise EmailContextValidationError(
                f"Field '{field}' has invalid type: expected {expected_type.__name__}, got {type(val).__name__}"
            )
