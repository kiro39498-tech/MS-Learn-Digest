# AI Architecture Documentation
## MS Learn Digest

---

## Overview

MS Learn Digest uses **Groq API** (model: `llama-3.3-70b-versatile`) for two distinct AI tasks:

| Task | Class | Called By | Output |
|---|---|---|---|
| **Digest generation** | `GroqClient` | `DigestGenerator` (scheduler) | `executive_summary` + per-item `newsletter_summary`, `why_it_matters`, `key_takeaways` |
| **Lesson generation** | `LessonGeneratorService` | `LearningNewsletterGenerator` (scheduler) | Full structured lesson JSON (explanation, diagram, quiz, exercise, etc.) |

---

## Groq Integration

**Provider:** Groq Cloud — `https://api.groq.com`  
**SDK:** `groq` Python async client (`AsyncGroq`)  
**Model:** `llama-3.3-70b-versatile` (configurable via `GROQ_MODEL`)  
**Response format:** `{"type": "json_object"}` on all calls — strict JSON output enforced  
**Temperature:** `0.3` on all calls — consistent, factual output  
**API Key:** Set via `GROQ_API_KEY` environment variable

### Configuration (`core/config.py`):
```python
GROQ_API_KEY: str = ""
GROQ_MODEL: str = "llama-3.3-70b-versatile"
```

---

## Digest Generation (`services/ai/groq_client.py`)

### Purpose
Transforms raw MS Learn catalog metadata into a professionally written newsletter with:
- A 2–3 sentence executive summary of the period's updates
- Per-item: newsletter summary, why it matters, and key takeaways

### Trigger
Called from `DigestGenerator._get_or_generate()` during the digest dispatch scheduler job, **only on cache miss**. The in-memory `dispatch_cache` dict (scoped to one scheduler run) ensures identical topic+frequency+content combinations share a single Groq call.

### Input Preparation
```python
payload_items = [
    {
        "uid": item["uid"],
        "title": item["title"],
        "summary": _truncate(item.get("summary") or "", max_words=100),
    }
    for item in items
]
```
Summaries are truncated to 100 words (~130 tokens) to control input cost.

### Prompt Design
```
You are writing a Microsoft Learn newsletter for professionals interested in: {topics_str}.
The newsletter covers Microsoft Learn updates from {window_label}.
Here are the {N} modules/learning paths to include:
{json.dumps(payload_items, indent=2)}

Output a single JSON object with EXACTLY this structure:
{
  "executive_summary": "...",
  "items": [{"uid": "...", "newsletter_summary": "...", "why_it_matters": "...", "key_takeaways": [...]}]
}

Rules:
- Include every uid from the input in items[].
- Be specific and practical. Avoid generic phrases like "enhance your skills".
- Output ONLY valid JSON. No markdown. No preamble.
```

### Expected Output Schema
```json
{
  "executive_summary": "This week Microsoft Learn published...",
  "items": [
    {
      "uid": "learn.wwl.module-name",
      "newsletter_summary": "2-sentence engaging description...",
      "why_it_matters": "1 sentence on concrete business value...",
      "key_takeaways": ["Takeaway 1", "Takeaway 2", "Takeaway 3"]
    }
  ]
}
```

### Fallback Strategy
If Groq fails for any reason, `_get_or_generate()` builds a minimal `ai_result` from catalog metadata:
```python
ai_result = {
    "executive_summary": f"Here are {len(matched)} Microsoft Learn updates for {topic_names}.",
    "items": [
        {
            "uid": item.uid,
            "newsletter_summary": item.summary or f"New content: {item.title}",
            "why_it_matters": "Expand your Microsoft Learn expertise.",
            "key_takeaways": [],
        }
        for item in matched
    ],
}
```
This guarantees digest delivery even when the AI provider is unavailable.

### Caching
- **Dispatch cache:** In-memory `dict` created per scheduler run, keyed by `SHA-256(topic_slugs + frequency + sorted_uids)[:16]`
- **Not persisted:** Cache is discarded when the scheduler job completes or the process restarts
- **Impact:** First digest run after restart makes one Groq call per unique content set; subsequent runs within the same scheduler cycle reuse the result

---

## Lesson Generation (`services/learning/lesson_generator.py`)

### Purpose
Generates a comprehensive, technically deep educational lesson for each module in a learning track. The output is a complete structured JSON lesson that rivals a professional Microsoft course.

### Trigger
Called from `LearningNewsletterGenerator.deliver()` when `generated_lessons` cache misses for a module.

### Persona Prompt
```
You are a Senior Microsoft Certified Trainer with 15+ years of enterprise consulting experience.
You teach complex Microsoft technologies to professionals at Fortune 500 companies.
Your lessons are technical, deep, practical, and prepare learners for real-world work AND certification exams.
```

### Input Variables
| Variable | Source |
|---|---|
| `topic_name` | `LearningTopic.name` |
| `module_title` | `LearningModule.title` |
| `sequence_number` | `LearningModule.sequence_number` |
| `total_modules` | `LearningTopic.total_modules` |
| `learning_objectives` | `LearningModule.learning_objectives[]` |
| `keywords` | `LearningModule.keywords[]` |
| `difficulty_level` | `LearningModule.difficulty_level` |
| `skill_level` | `LearningModule.skill_level` (overrides difficulty_level) |
| `phase_name` | `LearningModule.phase_name` |
| `is_milestone` | `LearningModule.is_milestone` |
| `resources` | Output of `ResourceDiscovery.discover_resources()` |

### Skill Level Guidance
Different audience guidance is injected per skill level:

| Level | Guidance Injected |
|---|---|
| `beginner` | "Assume zero prior knowledge. Use simple language. Lots of analogies. Avoid jargon unless you define it immediately." |
| `intermediate` | "Assume working knowledge. Go deeper. Show real configs and code. Discuss trade-offs." |
| `advanced` | "Assume strong experience. Cover architecture decisions, performance implications, gotchas, and enterprise patterns." |
| `expert` | "Write for a principal engineer or architect. System design considerations, edge cases, cost/scale trade-offs, and enterprise governance." |

### Complete Output Schema
```json
{
  "module_title": "string",
  "skill_level": "beginner|intermediate|advanced|expert",
  "phase_name": "string",
  "is_milestone": false,
  "estimated_read_minutes": 15,
  "today_goal": "One sentence: what the learner will DO after this lesson",
  "why_this_matters": "2-3 sentences: real enterprise business context",
  "introduction": "2-3 sentences introducing the topic",
  "explanation": "DEEP technical explanation — minimum 4-6 paragraphs",
  "architecture_diagram": "graph TD\n  A[Client] --> B[Service]\n  B --> C[Database]",
  "key_concepts": [
    {"term": "VNet", "definition": "Virtual network in Azure..."}
  ],
  "real_world_example": {
    "company_type": "Retail bank",
    "scenario": "3-4 sentences describing real scenario...",
    "lessons_learned": ["Insight 1", "Insight 2"]
  },
  "common_mistakes": [
    {"mistake": "...", "consequence": "...", "fix": "..."}
  ],
  "practical_exercise": {
    "title": "...",
    "objective": "...",
    "prerequisites": ["..."],
    "steps": ["Step 1: ...", "Step 2: ..."],
    "expected_outcome": "...",
    "challenge_extension": "..."
  },
  "questions": {
    "beginner": [{"question": "...", "model_answer": "..."}],
    "advanced": [{"question": "...", "model_answer": "..."}]
  },
  "quiz": [
    {
      "question": "...",
      "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
      "correct_answer": "A) ...",
      "explanation": "..."
    }
  ],
  "summary": ["Key takeaway 1", "Key takeaway 2", "Key takeaway 3", "Key takeaway 4"],
  "next_lesson_preview": "Next: Module 4 — ...",
  "further_reading": [
    {"title": "...", "url": "https://learn.microsoft.com/...", "type": "official_docs"}
  ]
}
```

### Generation Rules Enforced by Prompt
- `key_concepts`: exactly 5–8 terms
- `common_mistakes`: exactly 3–5 items
- `beginner questions`: exactly 2 questions
- `advanced questions`: exactly 3 questions
- `quiz`: exactly 5–8 questions
- `summary`: exactly 4–6 bullet points as JSON array
- `architecture_diagram`: valid Mermaid syntax, newlines escaped as `\n`
- `further_reading`: 2–4 official Microsoft links

### Fallback Strategy
`_fallback_lesson()` returns a minimal valid JSON object with:
- Generic `today_goal`, `explanation`, `introduction` based on module title
- Minimal `key_concepts`, `quiz`, `practical_exercise`
- Link to `https://learn.microsoft.com`

This ensures lesson emails are never blocked by Groq failures.

---

## Resource Discovery for Lesson Context

Before generating a lesson, `ResourceDiscovery.discover_resources()` provides real documentation content as context for the Groq prompt.

### Flow
1. Build search queries:
   - `"{module_title} {topic_name} Microsoft Learn"`
   - `"{module_title} {topic_name} documentation site:learn.microsoft.com"`
   - `"{keywords[:3]} microsoft learn tutorial"`
2. Search DuckDuckGo (`duckduckgo_search` library), sort results by domain priority
3. Scrape up to 3 top-priority URLs (BeautifulSoup, `lxml` parser)
4. Extract main content area (skips nav, footer, scripts)
5. Truncate to 4,000 characters per page
6. Pass as context block in lesson prompt

### Domain Priority Scoring
| Domain | Score |
|---|---|
| `learn.microsoft.com` | 10 |
| `docs.microsoft.com` | 9 |
| `microsoft.com` | 8 |
| `azure.microsoft.com` | 8 |
| `techcommunity.microsoft.com` | 6 |
| `devblogs.microsoft.com` | 5 |
| Other | 1 |

Higher-priority domains are fetched first to maximise the quality of Groq's context.

### Graceful Degradation
- `duckduckgo_search` not installed → returns empty list
- Search fails → returns empty list
- Page timeout (10s) → skips that URL
- HTTP error → skips that URL
- Insufficient content (<200 chars) → skips that URL

When no resources are found, the prompt falls back to: `"Use your deep knowledge of {topic_name} — {module_title}."`

---

## Caching Strategy

| Cache | Type | Key | Scope | Duration |
|---|---|---|---|---|
| `dispatch_cache` | In-memory `dict` | `SHA256(topics+freq+uids)[:16]` | Single scheduler run | Until next dispatch job runs |
| `generated_lessons` | PostgreSQL table | `module_id` (UNIQUE) | All users | Permanent (until row deleted) |

The `generated_lessons` cache is the most important: once a lesson is generated for a module, every future subscriber to that module receives the cached version — Groq is never called again for that module.

---

## Token Usage Estimates

| Use Case | Approx Input Tokens | Approx Output Tokens |
|---|---|---|
| Digest (30 items) | ~4,500 | ~2,000 |
| Lesson (with 3 resource pages) | ~5,000–8,000 | ~3,000–4,096 |

Groq's `llama-3.3-70b-versatile` has a 131,072 token context window, so even large inputs are well within limits. `max_tokens=4096` is set on lesson generation to cap output.

---

## AI Model Limitations

- Groq API may rate limit or return errors under high load — both fallback strategies prevent service interruption
- `dispatch_cache` is in-memory only — process restarts clear it
- Resource discovery depends on DuckDuckGo availability and page accessibility
- Scraped content quality varies — official Microsoft Learn pages produce the best results
- Mermaid diagram syntax occasionally requires manual review for complex architectures
