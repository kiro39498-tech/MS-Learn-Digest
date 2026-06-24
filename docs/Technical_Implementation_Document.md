# Technical Implementation Document
## MS Learn Digest — Enterprise Learning Intelligence Platform

**Version:** 1.0  
**Date:** June 2026  
**Classification:** Internal / Project Submission

---

## A. Executive Summary

### Project Purpose
MS Learn Digest is a full-stack web application that transforms the Microsoft Learn catalog — over 10,000 modules and learning paths updated weekly — into personalised, AI-curated newsletters and structured learning journeys delivered directly to users' inboxes.

### Business Problem
Microsoft Learn publishes new content and updates constantly across hundreds of technology areas. Practitioners who need to stay current with Azure, Fabric, Security, GitHub, AI, and other Microsoft platforms have no practical way to monitor this volume. Manual browsing is inefficient; existing Microsoft notifications are generic, not personalised.

### Solution Overview
MS Learn Digest solves this with three integrated systems:

1. **Digest Engine** — Syncs the MS Learn Catalog API daily, matches content against user topic subscriptions, generates an AI-written personalised newsletter using Groq (Llama 3.3 70B), and delivers via SMTP.

2. **Learning Engine** — A structured curriculum platform with phased, module-by-module lessons. Each lesson is generated once by Groq (acting as a Senior Microsoft Certified Trainer), cached permanently, and delivered to all subscribers on a chosen schedule.

3. **Team Newsletter Engine** — Extends the individual digest to team contexts. A team admin creates a team, configures topics and schedule, and invites colleagues by email. All accepted members receive the same team newsletter.

### Key Benefits
- Zero manual curation — content is automatically discovered, filtered, and summarised
- Personalised to exact technology interests at topic and subtopic level
- Structured, progressive learning with phase selection and milestone projects
- Team-wide knowledge sharing via collaborative newsletters
- Enterprise-grade email delivery with full audit trail

---

## B. System Overview

MS Learn Digest enables users to:

| Capability | Implementation |
|---|---|
| **Discover Microsoft technologies** | Hierarchical topic tree (9 root categories, 50+ subtopics) with card-based selector |
| **Subscribe to topics** | `user_subscriptions` table; subscribing to a parent auto-resolves descendants for content matching |
| **Subscribe to learning tracks** | `user_learning_subscriptions` table; full track or selected phases |
| **Receive personalised newsletters** | DigestGenerator → Groq → Jinja2 template → SMTP |
| **Receive AI-generated learning lessons** | LessonGeneratorService → Groq → `learning_email.html` template → SMTP |
| **Follow structured learning journeys** | Phased curriculum (up to 7 phases per track, milestone projects included) |
| **Manage team newsletters** | TeamRepository atomic create; invitation flow with token-based email acceptance |
| **Receive scheduled content updates** | APScheduler: catalog sync daily, digest dispatch every 15 min, learning dispatch every 30 min |

---

## C. Technology Stack

| Component | Technology | Details |
|---|---|---|
| **Frontend Framework** | React 19 + Vite 8 | SPA, JSX, hot module replacement |
| **Frontend Styling** | Tailwind CSS 3 | Utility classes, custom `ms-blue`/`ms-dark` palette |
| **Frontend Routing** | React Router DOM 7 | Client-side routing, `AuthContext` for JWT state |
| **Frontend HTTP** | Axios 1.x | Centralized `api.js` with JWT interceptor and auto-logout on 401 |
| **Backend Framework** | FastAPI (Python 3.12) | Async, Pydantic v2, OpenAPI auto-docs |
| **ORM** | SQLAlchemy (async-ready Session) | Declarative models, relationship eager-loading with `joinedload` |
| **Migrations** | Alembic | 9 migration files, full upgrade/downgrade chain |
| **Database** | PostgreSQL 14+ | UUID PKs, JSONB columns, ARRAY columns, recursive CTE queries |
| **Scheduler** | APScheduler `AsyncIOScheduler` | In-process, CronTrigger, runs inside FastAPI lifespan |
| **AI Provider** | Groq API — `llama-3.3-70b-versatile` | Digest generation (batch) + lesson generation (per module) |
| **Email Service** | Python `smtplib` + Gmail STARTTLS port 587 | HTML email, MIME Multipart, App Password auth |
| **Authentication** | Google OAuth 2.0 + Email Magic-Link | `python-jose` JWT (HS256, 72h expiry) |
| **Email Templates** | Jinja2 `FileSystemLoader` | `digest_email.html`, `learning_email.html`, `invitation_email.html` |
| **Web Scraping** | Requests + BeautifulSoup4 + lxml | Resource discovery for lesson context |
| **Search** | DuckDuckGo Search (`duckduckgo_search`) | Finds Microsoft Learn pages for lesson context |
| **Settings** | Pydantic Settings v2 | Environment variable validation, `.env` file loading |
| **Logging** | Python stdlib `logging` | Structured `timestamp | level | module | message` format to stdout |
| **Redis** | Not implemented | — |
| **Celery** | Not implemented | APScheduler is used instead |
| **Docker** | Not configured | Manual setup only |

---

## D. Detailed Module Design

### D1. Authentication

**Google OAuth 2.0 Flow** (`auth_service.py`):
1. Frontend redirects user to Google's OAuth consent screen with `GOOGLE_CLIENT_ID`
2. Google returns an authorization code to `/auth/callback` on the frontend
3. Frontend POSTs code to `POST /api/auth/google`
4. `AuthService.exchange_google_code()` calls `https://oauth2.googleapis.com/token` to exchange the code for a Google access token
5. `AuthService` calls `https://www.googleapis.com/oauth2/v2/userinfo` to fetch profile
6. User is created or updated in the `users` table (`google_id`, `email`, `name`, `avatar_url`)
7. A JWT is issued (`python-jose`, HS256, 72h expiry) and returned to the frontend
8. Frontend stores JWT in `localStorage` and attaches it via `Authorization: Bearer` header on all API calls

**Email Magic-Link Flow** (`email_auth_service.py`):
1. User submits email to `POST /api/auth/email/request`
2. `EmailAuthService` rate-limits (max 5 requests/hour/email)
3. Generates `secrets.token_hex(32)` (64-char hex) — raw token never stored
4. Stores SHA-256 hash of token in `email_login_tokens` with 15-minute expiry
5. Sends HTML email with link: `{FRONTEND_URL}/auth/email/callback?token=<raw>`
6. User clicks link → frontend POSTs token to `POST /api/auth/email/verify`
7. Service hashes incoming token, finds DB row, checks expiry + `used_at`
8. Marks token used, upserts user, returns identical JWT structure as Google OAuth

**JWT Validation** (`security.py`):
- `HTTPBearer` scheme extracts token from `Authorization: Bearer` header
- `get_current_user_id()` dependency decodes JWT and returns `user_id` (UUID string)
- Used in all protected endpoints via `Depends(get_current_user_id)`

---

### D2. Topic Management

**Data Model:** `topics` table with self-referential `parent_topic_id` FK and `level` column.

**Hierarchy:**
- Level 0 = root (Azure, Fabric, Security, GitHub, AI Engineering, DevOps, M365, Power Platform, Dynamics 365)
- Level 1 = subtopics (Azure → Networking, Compute, Security, Identity…)
- Arbitrary depth supported via recursive CTE in `TopicRepository.resolve_descendant_ids()`

**Subscription Semantics:**
- Subscribing to a parent (e.g. "Azure") does **not** create child subscription rows
- At digest generation time, `resolve_descendant_ids()` expands the subscription set to include all descendants
- This keeps the `user_subscriptions` table clean while delivering parent-aware content

**Seeding:** `TopicRepository.seed_system_topics()` is called on every startup — idempotent, inserts only missing topics, repairs `parent_topic_id` for any stale rows.

---

### D3. Digest Engine

**Flow** (see `services/digest/generator.py`):

1. Load user's `UserSubscription` rows → get topic list
2. Resolve descendant topic IDs (`resolve_descendant_ids()`)
3. Build `products_set` + `subjects_set` from all topic `catalog_products`/`catalog_subjects`
4. Query `catalog_cache` WHERE `last_modified >= window_start` (window = frequency-based lookback)
5. Filter in Python: keep items where `products_json ∩ products_set ≠ ∅` OR `subjects_json ∩ subjects_set ≠ ∅`
6. Compute `cache_key = SHA256(sorted_topic_slugs + frequency + sorted_uids)[:16]`
7. If `cache_key` in `dispatch_cache` (in-memory dict shared across this scheduler run) → reuse Groq output
8. Otherwise → call `GroqClient.generate_digest()` → store in `dispatch_cache`
9. Render `digest_email.html` Jinja2 template with AI output + catalog metadata
10. Persist `Digest` + `DigestItem` rows (self-contained, no FK to catalog)
11. Send via `EmailClient.send_email()`
12. Mark digest `sent` or `failed`

**Groq Call:** Single call per unique (topic_set × frequency × content_set). Model: `llama-3.3-70b-versatile`, temperature 0.3, `json_object` response format.

**Groq Fallback:** If Groq fails, `_get_or_generate()` builds a minimal `ai_result` from catalog summaries so delivery is never blocked by an LLM failure.

---

### D4. Learning Engine

**Curriculum:** Defined in `services/learning/curriculum.py`. Each track has phases (e.g. "Phase 1: Fundamentals"), each phase has modules with `sequence_number`, `skill_level`, `is_milestone`, `learning_objectives`, and `keywords`.

**Delivery Flow** (see `services/learning/newsletter_generator.py`):

1. Scheduler calls `run_learning_dispatch()` every 30 minutes
2. `LearningRepository.get_all_due_subscriptions()` returns subscriptions where `last_sent_at + frequency_delta ≤ now`
3. For each due subscription, `LearningNewsletterGenerator.deliver(sub)` is called
4. Resolves current module (phase-aware for custom phase subscriptions)
5. Checks `generated_lessons` cache for this `module_id`
6. On cache miss: `ResourceDiscoveryService.discover_resources()` searches DuckDuckGo, scrapes up to 3 Microsoft Learn pages
7. `LessonGeneratorService.generate_lesson()` calls Groq with module metadata + scraped context
8. Groq returns structured JSON: `today_goal`, `explanation`, `architecture_diagram` (Mermaid), `key_concepts`, `real_world_example`, `practical_exercise`, `quiz`, `summary`, etc.
9. Lesson saved to `generated_lessons` — permanent cache, shared across all users
10. Rendered via `learning_email.html` Jinja2 template
11. Sent via SMTP
12. `_update_streak()` increments streak counters
13. `_record_analytics()` writes to `learning_analytics`
14. `LearningRepository.advance_module()` moves to next module in active list (phase-aware)

**Phase Selection:**
- `UserLearningSubscription.is_full_track = True` → all modules in sequence order
- `is_full_track = False` → only modules whose `phase_name` is in `user_phase_subscriptions` for this subscription
- `advance_module()` uses `get_modules_for_subscription()` which respects this filter

---

### D5. Newsletter Management (Team)

**Design:** One team owns exactly one `TeamNewsletter` (enforced by `UNIQUE(team_id)` DB constraint, added in migration `d4e5f6a7b8c9`).

**Creation:** `POST /api/teams/` creates Team + TeamNewsletter atomically in a single transaction via `TeamRepository.create_team_with_newsletter()`.

**Invitation Flow:**
1. Admin calls `POST /api/teams/{id}/invite` with member email
2. `TeamRepository.invite_member()` creates `TeamMember` (status=pending) + `TeamInvitation` (secure URL token via `secrets.token_urlsafe(32)`, configurable expiry defaulting to 72 hours per `INVITATION_EXPIRY_HOURS`)
3. `invitation_email.html` rendered and sent via SMTP
4. Invitee clicks link → `GET /api/teams/invite/{token}` returns preview
5. After auth, `POST /api/teams/invite/{token}/accept` links member to user account
6. Only `status=accepted` members receive newsletters

**Delivery:** Scheduler calls `DigestGenerator.generate_and_send_for_newsletter()` — same content for all accepted members, one Groq call shared via `dispatch_cache`.

---

### D6. Admin Dashboard

Endpoints at `/api/admin/*` (controlled by `ADMIN_ENABLED` flag):

| Endpoint | Purpose |
|---|---|
| `GET /api/admin/config` | Show SMTP config (password masked) |
| `GET /api/admin/smtp-check` | Test SMTP connection without sending |
| `POST /api/admin/send-test-email` | Send plain test email |
| `POST /api/admin/send-test-digest` | Send sample digest with hardcoded content |
| `GET /api/admin/preview-digest` | Return digest HTML in browser |
| `POST /api/admin/catalog-sync` | Trigger MS Learn catalog sync |
| `GET /api/admin/catalog-cache/stats` | Cache health: item counts, last sync time |
| `POST /api/admin/catalog-cache/preview` | Preview matched items for topic slugs |
| `POST /api/admin/test/send-my-digest` | Generate + send real digest for logged-in user |
| `GET /api/admin/debug/onboarding` | Onboarding state check + auto-heal |
| `POST /api/admin/teams/test-create` | Create a test team |
| `POST /api/admin/teams/{id}/test-invite` | Invite to test team and send email |
| `POST /api/admin/teams/{id}/test-digest` | Send team newsletter |

---

## E. End-to-End Application Flow

```
User visits / → LandingPage
  → clicks "Sign in with Google" → Google OAuth
  → AuthCallback → POST /api/auth/google → JWT stored in localStorage

First login (is_onboarded=false) → redirect to /onboarding
  Step 1: TopicCardGrid — select topics (GET /api/topics/tree)
  Step 2: Schedule — frequency + day + time
  → POST /api/topics/onboard (saves subscriptions, sets is_onboarded=true)
  → POST /api/users/me/preferences (saves schedule)
  → redirect to /dashboard

Dashboard shows digest history (GET /api/digests/)
  → click digest → GET /api/digests/{id} → DigestDetail

Scheduler (every 15 min):
  1. Check if user is due (frequency × delivery_day × delivery_time, timezone-aware)
  2. If due: query catalog_cache, call Groq, render template, send email, save Digest

Learning Center (/learning):
  → GET /api/learning/topics → browse tracks
  → click "Enrol" → PhaseSelector modal
  → POST /api/learning/subscribe {topic_id, frequency, is_full_track, selected_phases}

Scheduler (every 30 min):
  1. Find due learning subscriptions
  2. Generate/retrieve cached lesson
  3. Send via SMTP
  4. Update streak + analytics + advance module
```

---

## F. Database Design

### Tables (20 total)

| Table | Purpose |
|---|---|
| `users` | All users — Google OAuth and email-only. `auth_provider`, `email_verified`, `last_login` |
| `user_preferences` | Digest delivery preferences per user |
| `email_login_tokens` | Magic-link tokens (hash stored, not raw) |
| `topics` | Hierarchical topic taxonomy. Self-referential via `parent_topic_id` |
| `user_subscriptions` | User ↔ topic subscriptions for digest delivery |
| `catalog_cache` | MS Learn catalog metadata cache. `products_json`, `subjects_json` JSONB arrays |
| `sync_metadata` | Singleton (id=1) storing last catalog sync result |
| `digests` | Generated digest records (individual or team) |
| `digest_items` | Individual catalog items inside a digest (self-contained, no FK to catalog) |
| `teams` | Team records with admin FK |
| `team_members` | Team membership with status lifecycle: `pending → accepted / declined / expired` |
| `team_invitations` | Secure invitation tokens (raw `secrets.token_urlsafe(32)`) |
| `team_newsletters` | One per team. `UNIQUE(team_id)` enforced |
| `newsletter_topics` | Topic selections for a team newsletter |
| `learning_topics` | Learning track metadata (name, slug, total_modules, difficulty_range) |
| `learning_modules` | Ordered lessons per track with phase, skill_level, is_milestone, objectives |
| `user_learning_subscriptions` | User enrollment with progress tracking, streak counters, `is_full_track` |
| `user_phase_subscriptions` | Selected phases for a custom (non-full-track) subscription |
| `generated_lessons` | Cached AI-generated lesson JSON + HTML (one per module, shared) |
| `learning_analytics` | Per-delivery audit log for dashboard metrics |
| `learning_weekly_reviews` | Cached weekly summary emails (table exists, delivery TBD) |

### Key Indexes

- `catalog_cache.uid` (UNIQUE) — fast upsert by UID
- `catalog_cache.last_modified` — time-range queries for digest window
- `topics.slug` (UNIQUE) — catalog filter set construction
- `topics.parent_topic_id` — recursive CTE tree traversal
- `user_learning_subscriptions.(user_id, topic_id)` (UNIQUE) — one subscription per track
- `user_phase_subscriptions.(subscription_id, phase_name)` (UNIQUE) — one row per phase per sub
- `email_login_tokens.token_hash` (UNIQUE) — O(1) magic-link lookup

---

## G. API Design

The REST API follows resource-oriented design with standard HTTP methods and status codes. All protected endpoints use `Authorization: Bearer <JWT>`. See `docs/API_Documentation.md` for full endpoint reference.

**Base URL:** `http://localhost:8000/api`  
**Routers:** auth, users, topics, teams, newsletters, digests, admin, learning

---

## H. Security

| Area | Implementation |
|---|---|
| **Authentication** | JWT (HS256) + Google OAuth 2.0 + Email magic-link (SHA-256 hashed tokens) |
| **Authorization** | `Depends(get_current_user_id)` on all protected routes; team admin checks via `TeamRepository.is_admin()` |
| **Token Storage** | JWT in `localStorage` (client-side); raw magic-link tokens never persisted (only SHA-256 hash stored) |
| **Rate Limiting** | Email magic-link: 5 requests/hour/email enforced in `EmailAuthService._check_rate_limit()` |
| **Input Validation** | Pydantic v2 schemas on all request bodies; email format validated with regex in auth endpoints |
| **CORS** | Configured with exact `allow_origins=[settings.FRONTEND_URL]` — no wildcard in production |
| **Admin Guard** | `_check_admin_enabled()` checks `APP_ENV` and `ADMIN_ENABLED` flag |
| **Secrets Management** | All secrets via environment variables loaded by Pydantic Settings; `.env` excluded from git via `.gitignore` |
| **Invitation Security** | `secrets.token_urlsafe(32)` tokens; configurable expiry (default 72h); single-use (status → accepted on first use) |

---

## I. Error Handling

- **Groq failures:** `_get_or_generate()` catches all exceptions and builds a fallback `ai_result` from catalog metadata — digests never fail due to Groq
- **SMTP failures:** `send_email()` returns `bool`; digest marked `failed` in DB; structured logging with error type
- **Catalog sync failures:** Error logged; `sync_metadata` updated with `status=failed`; existing cache used for next digest run
- **Learning lesson failures:** `_fallback_lesson()` returns a minimal valid JSON object; delivery continues
- **Resource discovery failures:** Returns empty list; lesson generator uses model knowledge only

---

## J. Performance Optimizations

| Optimization | Details |
|---|---|
| **Digest dispatch cache** | In-memory `dispatch_cache` dict per scheduler run — identical topic+frequency+content combinations share one Groq call |
| **Lesson caching** | `generated_lessons` table — one Groq call per module, reused by all subscribers |
| **Catalog filtered fetches** | `CatalogClient` fetches `?type=modules` and `?type=learningPaths` separately — each is ~8 MB vs ~40 MB for unfiltered |
| **Batch upserts** | `pg_insert(...).on_conflict_do_update()` — PostgreSQL UPSERT in batches of 500 |
| **Recursive CTE** | `resolve_descendant_ids()` uses a single recursive CTE query instead of N+1 topic fetches |
| **Eager loading** | `joinedload()` on all relationship traversals to avoid N+1 in API responses |
| **In-process scheduler** | APScheduler runs inside the FastAPI process — no separate worker, no message broker |

---

## K. Known Limitations

- **No Redis:** Groq `dispatch_cache` is in-memory only — lost on restart. Each restart triggers fresh Groq calls for the next digest run.
- **No Celery:** APScheduler is single-instance; horizontal scaling would require external coordination.
- **No Docker:** Deployment requires manual environment setup.
- **SMTP only:** No SendGrid, SES, or other transactional email provider — Gmail App Password only.
- **No unsubscribe processing:** Unsubscribe link appears in footer but the endpoint is not implemented.
- **Timezone assumption for teams:** All team newsletter schedules use `Asia/Kolkata` (IST) regardless of user setting. Individual user digests do respect the timezone from preferences.
- **`learning_weekly_reviews` table exists** but the weekly review delivery job is not implemented in the scheduler.
- **DuckDuckGo dependency:** Resource discovery uses `duckduckgo_search` — rate limits or service changes could affect lesson context quality (gracefully falls back to model knowledge).
