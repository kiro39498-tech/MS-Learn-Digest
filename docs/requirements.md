# Requirements Document
## MS Learn Digest

**Version:** 1.0  
**Date:** June 2026

---

## 1. Functional Requirements

### FR-01: Authentication

| ID | Requirement | Status |
|---|---|---|
| FR-01-1 | Users can authenticate using Google OAuth 2.0 | ✅ Implemented |
| FR-01-2 | Users can authenticate using email magic-link (passwordless) | ✅ Implemented |
| FR-01-3 | Magic-link tokens expire in hourlyutes (configurable) | ✅ Implemented |
| FR-01-4 | Magic-link tokens are single-use | ✅ Implemented |
| FR-01-5 | Magic-link requests are rate-limited to 5 per hour per email | ✅ Implemented |
| FR-01-6 | System issues a JWT (HS256, 72-hour expiry) on successful authentication | ✅ Implemented |
| FR-01-7 | Frontend auto-logouts on 401 response | ✅ Implemented |
| FR-01-8 | Available auth providers are returned by `GET /api/auth/providers` | ✅ Implemented |

---

### FR-02: User Onboarding

| ID | Requirement | Status |
|---|---|---|
| FR-02-1 | New users are redirected to the onboarding wizard on first login | ✅ Implemented |
| FR-02-2 | Onboarding Step 1: user selects Microsoft technology topics | ✅ Implemented |
| FR-02-3 | Onboarding Step 2: user configures digest frequency, delivery day, and time | ✅ Implemented |
| FR-02-4 | Onboarding completion sets `users.is_onboarded = true` | ✅ Implemented |
| FR-02-5 | `is_onboarded` is auto-healed to `true` if user has subscriptions but flag is `false` | ✅ Implemented |

---

### FR-03: Topic Subscriptions (Digest)

| ID | Requirement | Status |
|---|---|---|
| FR-03-1 | System provides a hierarchical topic tree (root → subtopics) | ✅ Implemented |
| FR-03-2 | Topic tree is presented as cards with search and category filters | ✅ Implemented |
| FR-03-3 | Users can subscribe to root topics (subscribing to parent covers all children) | ✅ Implemented |
| FR-03-4 | Users can subscribe to individual subtopics | ✅ Implemented |
| FR-03-5 | `POST /api/topics/subscribe` atomically replaces all user subscriptions | ✅ Implemented |
| FR-03-6 | Users can update subscriptions any time via Preferences page | ✅ Implemented |
| FR-03-7 | System seeds 9 root topics and 50+ subtopics on startup (idempotent) | ✅ Implemented |

---

### FR-04: Digest Subscriptions and Delivery

| ID | Requirement | Status |
|---|---|---|
| FR-04-1 | Users select a delivery frequency: daily, weekly, bi-weekly, or monthly | ✅ Implemented |
| FR-04-2 | Users select a delivery day (for non-daily) and time | ✅ Implemented |
| FR-04-3 | Scheduler checks delivery eligibility once every hour | ✅ Implemented |
| FR-04-4 | Digest content is sourced only from `catalog_cache` (never triggers a sync) | ✅ Implemented |
| FR-04-5 | Digest content is filtered to items modified within the user's frequency window | ✅ Implemented |
| FR-04-6 | Digest content is further filtered to match user's topic subscriptions | ✅ Implemented |
| FR-04-7 | AI summary (Groq) is generated per unique topic+frequency+content combination | ✅ Implemented |
| FR-04-8 | Groq output is cached in-memory per scheduler run to avoid duplicate calls | ✅ Implemented |
| FR-04-9 | If no matching content exists, a `no_content` digest is recorded (no email) | ✅ Implemented |
| FR-04-10 | Digest history is persisted in the `digests` and `digest_items` tables | ✅ Implemented |
| FR-04-11 | Users can view digest history in the Dashboard | ✅ Implemented |
| FR-04-12 | Groq failure triggers fallback generation from catalog summaries | ✅ Implemented |

---

### FR-05: Learning Tracks

| ID | Requirement | Status |
|---|---|---|
| FR-05-1 | System provides a catalog of learning tracks (Azure Admin, Fabric, etc.) | ✅ Implemented |
| FR-05-2 | Each track has an ordered curriculum with phases, modules, skill levels, and milestones | ✅ Implemented |
| FR-05-3 | Users can browse available tracks in Learning Center | ✅ Implemented |
| FR-05-4 | Users can preview the curriculum (phases and modules) before enrolling | ✅ Implemented |
| FR-05-5 | Users enrol in a track via `POST /api/learning/subscribe` | ✅ Implemented |
| FR-05-6 | Users can select delivery frequency: daily, weekly, or bi-weekly | ✅ Implemented |
| FR-05-7 | Progress is tracked per subscription (current module, % complete, streak) | ✅ Implemented |
| FR-05-8 | Track is marked `completed` when the last module is delivered | ✅ Implemented |
| FR-05-9 | Users can unsubscribe from a track | ✅ Implemented |
| FR-05-10 | Users can update delivery frequency after enrollment | ✅ Implemented |

---

### FR-06: Phase Selection

| ID | Requirement | Status |
|---|---|---|
| FR-06-1 | Users can enrol in a full track (all phases in sequence) | ✅ Implemented |
| FR-06-2 | Users can select specific phases within a track (partial enrollment) | ✅ Implemented |
| FR-06-3 | Phase selection is recorded in `user_phase_subscriptions` | ✅ Implemented |
| FR-06-4 | Learning delivery respects phase selection — only delivers modules in selected phases | ✅ Implemented |
| FR-06-5 | `advance_module()` skips modules outside selected phases | ✅ Implemented |
| FR-06-6 | Users can edit their phase selection after enrollment | ✅ Implemented |
| FR-06-7 | Changing phases resets progress to the first module of the new phase set | ✅ Implemented |

---

### FR-07: Team Newsletters

| ID | Requirement | Status |
|---|---|---|
| FR-07-1 | Any user can create a team with a name and description | ✅ Implemented |
| FR-07-2 | Team creation atomically creates a newsletter configuration | ✅ Implemented |
| FR-07-3 | Each team has exactly one newsletter (enforced by DB unique constraint) | ✅ Implemented |
| FR-07-4 | Team admin can configure newsletter topics, frequency, and schedule | ✅ Implemented |
| FR-07-5 | Team admin can invite members by email address | ✅ Implemented |
| FR-07-6 | Invitation email is sent via SMTP with a secure time-limited token | ✅ Implemented |
| FR-07-7 | Invitees can preview team details before accepting | ✅ Implemented |
| FR-07-8 | Invitation acceptance links membership to the user's account | ✅ Implemented |
| FR-07-9 | Only `status=accepted` members receive the newsletter | ✅ Implemented |
| FR-07-10 | Team admin can resend invitations | ✅ Implemented |
| FR-07-11 | Team admin can remove members or cancel pending invitations | ✅ Implemented |
| FR-07-12 | Team admin can pause/resume the newsletter | ✅ Implemented |
| FR-07-13 | Team admin can delete the team (cascades all data) | ✅ Implemented |

---

### FR-08: Email Delivery

| ID | Requirement | Status |
|---|---|---|
| FR-08-1 | System sends HTML emails via SMTP (Gmail TLS port 587) | ✅ Implemented |
| FR-08-2 | Digest emails use `digest_email.html` Jinja2 template | ✅ Implemented |
| FR-08-3 | Learning lesson emails use `learning_email.html` Jinja2 template | ✅ Implemented |
| FR-08-4 | Invitation emails use `invitation_email.html` Jinja2 template | ✅ Implemented |
| FR-08-5 | All email templates are responsive (mobile + desktop) | ✅ Implemented |
| FR-08-6 | Email templates are compatible with Gmail and Outlook | ✅ Implemented |
| FR-08-7 | SMTP connection is tested via `GET /api/admin/smtp-check` | ✅ Implemented |

---

### FR-09: AI Content Generation

| ID | Requirement | Status |
|---|---|---|
| FR-09-1 | Digest summaries generated by Groq `llama-3.3-70b-versatile` | ✅ Implemented |
| FR-09-2 | One Groq call per unique (topic set × frequency × content set) per scheduler run | ✅ Implemented |
| FR-09-3 | Learning lessons generated by Groq with structured JSON output | ✅ Implemented |
| FR-09-4 | Lesson prompt instructs Groq to act as Senior Microsoft Certified Trainer | ✅ Implemented |
| FR-09-5 | Lesson JSON includes: explanation, Mermaid diagram, key concepts, real-world example, quiz, exercise | ✅ Implemented |
| FR-09-6 | Resource discovery uses DuckDuckGo search + BeautifulSoup scraping as context | ✅ Implemented |
| FR-09-7 | Generated lessons cached permanently in `generated_lessons` | ✅ Implemented |
| FR-09-8 | Groq failures have defined fallback behaviour (digest and lesson) | ✅ Implemented |

---

### FR-10: Admin Functions

| ID | Requirement | Status |
|---|---|---|
| FR-10-1 | Admin can test SMTP connection | ✅ Implemented |
| FR-10-2 | Admin can send a test email to any address | ✅ Implemented |
| FR-10-3 | Admin can send a test digest (sample content) to any address | ✅ Implemented |
| FR-10-4 | Admin can preview the digest HTML in browser | ✅ Implemented |
| FR-10-5 | Admin can trigger a manual catalog sync | ✅ Implemented |
| FR-10-6 | Admin can view catalog cache statistics | ✅ Implemented |
| FR-10-7 | Admin can preview matched catalog items for a topic set | ✅ Implemented |
| FR-10-8 | Admin can send a real digest for the currently logged-in user | ✅ Implemented |
| FR-10-9 | Admin endpoints are disabled in production via `ADMIN_ENABLED` flag | ✅ Implemented |

---

## 2. Non-Functional Requirements

### NFR-01: Performance

| ID | Requirement |
|---|---|
| NFR-01-1 | Catalog sync completes in < 5 minutes for full fetch (~10,000 items using filtered requests) |
| NFR-01-2 | Digest generation for a single user completes in < 30 seconds (including Groq call) |
| NFR-01-3 | Lesson generation completes in < 45 seconds (including resource discovery + Groq call) |
| NFR-01-4 | API response time for non-AI endpoints < 500ms under normal load |
| NFR-01-5 | In-process `dispatch_cache` eliminates duplicate Groq calls within a single scheduler run |

### NFR-02: Scalability

| ID | Requirement |
|---|---|
| NFR-02-1 | APScheduler runs in-process — horizontal scaling requires external scheduler coordination |
| NFR-02-2 | Generated lesson cache (`generated_lessons`) scales linearly with curriculum size, not user count |
| NFR-02-3 | PostgreSQL UPSERT (`ON CONFLICT`) handles concurrent catalog sync writes safely |

### NFR-03: Availability

| ID | Requirement |
|---|---|
| NFR-03-1 | If Groq fails during digest generation, delivery continues using catalog metadata fallback |
| NFR-03-2 | If catalog sync fails, the previous cache snapshot is used for digest delivery |
| NFR-03-3 | `misfire_grace_time` on all scheduler jobs allows up to 5 minutes late execution |
| NFR-03-4 | Health check endpoint `GET /health` available without authentication |

### NFR-04: Security

| ID | Requirement |
|---|---|
| NFR-04-1 | JWT tokens use HS256 algorithm with configurable secret key |
| NFR-04-2 | Magic-link tokens stored as SHA-256 hash only — raw token never persisted |
| NFR-04-3 | CORS restricted to configured `FRONTEND_URL` — no wildcard |
| NFR-04-4 | Admin endpoints disabled in production by default |
| NFR-04-5 | All secrets loaded from environment variables — no hardcoded secrets |
| NFR-04-6 | Input validation on all request bodies via Pydantic v2 |

### NFR-05: Reliability

| ID | Requirement |
|---|---|
| NFR-05-1 | All background jobs have exception handlers — job failure does not crash the process |
| NFR-05-2 | SMTP failures are logged with full error detail and digest marked `failed` |
| NFR-05-3 | Database operations use atomic transactions where multi-table writes are required |

### NFR-06: Maintainability

| ID | Requirement |
|---|---|
| NFR-06-1 | All database schema changes managed via Alembic migrations with upgrade/downgrade |
| NFR-06-2 | Business logic separated into repositories, services, and API layers |
| NFR-06-3 | Structured logging with consistent `MODULE | ACTION | detail` format |
| NFR-06-4 | Environment configuration centralised in `Settings` (Pydantic Settings v2) |

---

## 3. Business Rules

### BR-01: Newsletter Frequency Windows

| Frequency | Content Window | Scheduler Check |
|---|---|---|
| `daily` | Last 24 hours | Hourly, fires on matching hour:minute |
| `weekly` | Last 7 days | Hourly, fires on matching weekday + time |
| `biweekly` | Last 14 days | Hourly, fires on even ISO week numbers |
| `monthly` | Last 30 days | Hourly, fires on the 1st of the month |

### BR-02: Learning Phase Progression Rules

- Modules advance in `sequence_number` order
- Phase-aware: only modules in selected phases are delivered
- `advance_module()` marks `status=completed` when no next module exists in active list
- Changing phase selection resets `current_module_sequence` to the first module of the new set

### BR-03: Team Invitations

- Invitation expiry: configurable via `INVITATION_EXPIRY_HOURS` (default: 72 hours; `team_repository.py` default: 168 hours / 7 days)
- Invitation token: `secrets.token_urlsafe(32)` — cryptographically random, URL-safe
- Only `status=accepted` members receive newsletters
- An already-accepted member cannot be re-invited (returns `409 Conflict`)
- Re-sending an invitation to a `pending/declined/expired` member creates a new token and expires the old one

### BR-04: Learning Subscriptions

- One subscription per user per learning topic (enforced by `UNIQUE(user_id, topic_id)`)
- Re-subscribing updates frequency and phase selection on the existing record
- `is_full_track=False` requires at least one phase in `selected_phases`
- Streak increments when lesson is delivered within 1 day of the previous lesson; resets to 1 otherwise

### BR-05: Digest Generation

- Digest is generated only if `catalog_cache` contains items matching the user's topics within the frequency window
- `no_content` status is recorded even when there is nothing to send (for audit trail)
- Digest items are self-contained in `digest_items` — no dependency on `catalog_cache` rows after generation
- Team newsletters send the same HTML to all accepted members (one Groq call)

### BR-06: Topic Subscription Semantics

- Subscribing to a parent topic (e.g. "Azure") does not create child subscription rows
- At digest generation time, `resolve_descendant_ids()` expands to include all descendants
- This means content from any Azure subtopic (Networking, Compute, etc.) is included when a user subscribes to the "Azure" root
