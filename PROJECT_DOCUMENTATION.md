# MS Learn Digest — Complete Project Documentation

> **Based on full codebase inspection. All claims are grounded in actual implemented code.**

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [User Journey](#2-user-journey)
3. [Features Breakdown](#3-features-breakdown)
4. [Architecture & Technical Flow](#4-architecture--technical-flow)
5. [AI Workflow](#5-ai-workflow)
6. [Data Flow — Complete Lifecycle](#6-data-flow--complete-lifecycle)
7. [Newsletter & Digest Generation Process](#7-newsletter--digest-generation-process)
8. [Detailed Feature Documentation](#8-detailed-feature-documentation)
9. [Technical Challenges & Solutions](#9-technical-challenges--solutions)
10. [Demo Script (3–5 Minutes)](#10-demo-script-35-minutes)
11. [Resume & Portfolio Descriptions](#11-resume--portfolio-descriptions)
12. [System Architecture Diagram (Text)](#12-system-architecture-diagram-text)

---

## 1. Project Overview

### What the Project Does

MS Learn Digest is a full-stack, AI-powered learning intelligence platform that monitors the Microsoft Learn content catalog, enriches newly published or updated content with Groq LLM-generated summaries, and delivers personalized HTML digest emails to individual users and entire teams on fully configurable schedules.

A second independent engine — the **Learning Center** — provides structured, progressive learning tracks across seven technology domains. It discovers real web resources, generates lesson content via Groq, and delivers those lessons as rich HTML emails on a per-user cadence, advancing automatically through the curriculum with each delivery.

### The Problem It Solves

Microsoft publishes thousands of learning modules across Azure, Power Platform, Security, AI, DevOps, and more. The catalog changes constantly. Practitioners who want to stay current face a painful choice: manually browse a massive, ever-changing catalog, or fall behind. There is no mechanism that watches the catalog for you, filters it to your specific technology interests, and surfaces only what is new and relevant — let alone delivers it in a digestible, AI-enriched format directly to your inbox.

For teams, the problem is amplified. Engineering managers and L&D leads have no automated way to keep their whole team on the same page about Microsoft technology updates, and no easy mechanism to run structured knowledge-sharing newsletters.

MS Learn Digest solves both problems completely automatically.

### Target Users

- **Individual Microsoft technology practitioners** — Azure engineers, data engineers, Power BI developers, AI engineers, security professionals, DevOps engineers — who want a curated, AI-enriched view of new Microsoft Learn content relevant to their stack.
- **Engineering team leads and managers** who want to run automated, topic-specific learning newsletters for their entire team without manual curation effort.
- **L&D professionals** coordinating structured Microsoft technology upskilling programs across an organization.
- **Self-learners** who want a guided, progressive curriculum delivered automatically to their inbox with no course enrollment friction.

### Value Proposition

| Problem | MS Learn Digest Solution |
|---|---|
| Microsoft Learn catalog is too large to monitor manually | Daily automated sync captures every module and learning path |
| New content gets buried | AI digest surfaces only content new since your last delivery |
| No personalization | Topic subscriptions with hierarchical inheritance (subscribe to "Azure" → get all subtopics) |
| No team coordination | Team newsletter engine with invitation workflow and shared topic subscriptions |
| Learning requires active enrollment | Learning Center delivers progressive curriculum automatically to your inbox |
| AI summaries are generic | Groq generates executive summaries, key takeaways, and "why it matters" per item |

---

## 2. User Journey

### Step 1 — Landing Page

The user arrives at the React landing page (`LandingPage.jsx`). They see a marketing page with three feature cards: *AI Enriched Insights*, *Automated Digests*, and *Team Knowledge Sharing*. If the user already has a valid JWT in localStorage, the page automatically redirects them to `/dashboard`.

The single call-to-action is **"Sign in with Google"**. Clicking it triggers `handleGoogleLogin()`, which constructs a Google OAuth 2.0 authorization URL with `response_type=code`, the app's `client_id`, the `redirect_uri` pointing to `/auth/callback`, and the `email profile openid` scopes. The browser is then redirected to Google's consent screen.

*Behind the scenes:* No backend call is made yet. The OAuth flow begins entirely on the client side.

### Step 2 — Google OAuth Callback

After the user approves the Google consent screen, Google redirects back to `/auth/callback?code=<authorization_code>`. The `AuthCallback.jsx` component reads the `code` parameter from the URL and immediately calls the backend at `POST /api/auth/google` with the code and redirect URI. A `called.current` ref guard prevents the double-invocation that React 18+ StrictMode would otherwise cause.

*Behind the scenes:* The `AuthService.exchange_google_code()` method on the backend exchanges the authorization code with Google's token endpoint, retrieves an access token, then calls Google's UserInfo API to get the user's email, name, avatar URL, and Google ID. It performs an `upsert` — finding an existing user by `google_id` (falling back to email match for returning users who previously signed in differently), or creating a new `User` row. A JWT (`HS256`) is minted and returned to the frontend. The `AuthContext.login()` method stores the token in localStorage, sets it as the default `Authorization: Bearer` header on all future Axios requests, and fetches the user profile from `GET /api/users/me`.

If `is_onboarded=False`, the user is routed to `/onboarding`. If already onboarded, they land on `/dashboard`.

### Step 3 — Onboarding (New Users)

The two-step onboarding wizard (`Onboarding.jsx`) guides the user through the only required setup.

**Step 1 — Choose Your Topics:** The user sees the full hierarchical topic tree, fetched from `GET /api/topics/tree`. The tree has 9 root technology domains: Azure, Microsoft Fabric, Power Platform, Microsoft 365, Security, GitHub, AI Engineering, DevOps, and Dynamics 365. Each root expands to reveal 5–10 subtopics. The user selects any combination using checkbox-style buttons. A real-time search bar filters the visible tree. Selections persist across search queries.

**Step 2 — Set Your Schedule:** The user configures delivery frequency (daily, weekly, biweekly, monthly), day of week (for weekly/biweekly), and delivery time (hour:minute). These map to `delivery_day` (0=Monday through 6=Sunday) and `delivery_time` (a PostgreSQL TIME field).

Clicking **Finish** fires two sequential API calls: `PUT /api/users/me/preferences` (saves schedule) and `POST /api/topics/onboard` (saves topic subscriptions and flips `is_onboarded=True`). `refreshUser()` is called to pull the updated profile into context, then the user is routed to `/dashboard`.

*Behind the scenes:* `POST /api/topics/onboard` calls `TopicRepository.replace_user_subscriptions()`, which atomically deletes all existing subscriptions and inserts the new ones in a single transaction. The `is_onboarded` flag is set to `True` immediately.

### Step 4 — Dashboard

The dashboard (`Dashboard.jsx`) greets the user and shows four stat cards: next scheduled delivery (human-readable label), last digest sent (relative time), total digests sent, and number of subscribed topics. A "Send Digest Now" button calls the admin endpoint `POST /api/admin/test/send-my-digest`, which triggers an immediate real digest generation and delivery for the authenticated user.

Below the stats is a digest history list showing the most recent six digests with status pills (Generated, Sent, Failed, No Content) and links to their full HTML view.

### Step 5 — Receiving a Digest Email

At the configured delivery time, the APScheduler job fires, evaluates whether this user is due, generates an HTML digest, persists it to the database, and sends it via Gmail SMTP. The user receives a rich HTML email containing:

- A personalized greeting with their name
- An executive summary of all new content across their subscribed topics
- Individual cards for each new module/learning path with: title, content type, duration, AI-generated newsletter summary, "Why It Matters" rationale, and key takeaways
- A link back to the full digest in the application

### Step 6 — Viewing a Digest in the App

Clicking any digest in the history list or a link in the email navigates to `/digest/:id`. The `DigestDetail.jsx` page renders the stored `content_html` field inside a sandboxed `<iframe srcDoc>`, preserving the full email layout in the browser. If no HTML is stored, it falls back to a structured item list.

### Step 7 — Teams (Optional)

Users can navigate to `/teams` to create a team, configure a shared newsletter, and invite colleagues. The invite workflow sends an email with an acceptance link. Recipients can accept or decline without needing to be signed in first. Once accepted, team members receive the team newsletter in addition to (or instead of) their personal digest.

### Step 8 — Learning Center (Optional)

At `/learning`, users browse seven structured curriculum tracks. They can enroll in any track, choosing a delivery frequency. The system automatically starts at Module 1, generates a full lesson (with explanation, key concepts, real-world example, practical exercise, quiz, and next lesson preview), and delivers it by email. After each delivery, the system advances to the next module automatically.

---

## 3. Features Breakdown

### 3.1 Google OAuth Authentication
Single-click sign-in with no password management. Uses the standard OAuth 2.0 authorization code flow. JWT-based session with automatic token restoration from localStorage on page load. Auto-logout on 401 responses via Axios interceptor.

### 3.2 Hierarchical Topic Subscriptions
Nine root technology domains with 60+ subtopics form a two-level tree. Subscribing to a parent topic automatically includes all descendant subtopics via a PostgreSQL recursive CTE at query time. Topic trees are rendered in the UI with expandable sections, emoji icons, and real-time search filtering.

### 3.3 Flexible Delivery Scheduling
Each user sets an independent delivery schedule: frequency (daily/weekly/biweekly/monthly), day of week, and delivery time. The scheduler evaluates every user every 15 minutes against their configured schedule. Biweekly fires on even ISO weeks; monthly fires on the 1st of each month. All schedule logic is timezone-aware (Asia/Kolkata / IST).

### 3.4 AI-Enriched Digest Generation
For each scheduled delivery, new Microsoft Learn content (filtered by subscribed topics and the delivery time window) is sent to Groq's LLM API. The model returns a structured JSON response containing an executive summary of the entire digest and per-item enrichment: a newsletter-style summary, "why it matters" rationale, and key takeaways. This enriched content is rendered into an HTML email.

### 3.5 Groq Dispatch Cache
A SHA256 cache key is computed from the user's topic slugs, frequency, and the specific content UIDs included in the digest. If multiple users have identical subscriptions and there is overlapping content in the same dispatch run, the Groq API is called only once and the result is reused. Each user's email is still individually rendered with their personalized greeting.

### 3.6 Groq Fallback Delivery
If the Groq API call fails for any reason, the digest generator falls back to building a minimal digest using the `summary` fields already stored in `catalog_cache`. Email delivery is never blocked by LLM errors.

### 3.7 Daily Microsoft Learn Catalog Sync
An APScheduler cron job fires daily at 2:00 AM UTC. It fetches the Microsoft Learn catalog for `modules` and `learningPaths` separately (filtered API calls: ~8MB + ~3MB, vs. an unfiltered ~40MB payload), then performs a PostgreSQL `INSERT...ON CONFLICT DO UPDATE` upsert on the `uid` field, batching commits every 500 rows. The catalog cache is the single source of truth for all digest generation.

### 3.8 Team Newsletters
A team owner creates a team and simultaneously creates its newsletter (atomic transaction). They configure shared topic subscriptions, a delivery schedule, and optionally pause/resume the newsletter. The team newsletter engine mirrors the personal digest engine but generates a single email for the entire team.

### 3.9 Team Invitation Workflow
The team owner invites members by email. The system creates a `TeamInvitation` row with a `secrets.token_urlsafe(32)` secure token, sets an expiry, and sends an invitation email (rendered from a Jinja2 HTML template) with accept and decline links. Recipients can preview the invite (team name, topics, schedule) without being logged in. Accepting the invite links their user account to the team. Invitation status follows a lifecycle: pending → accepted | declined | expired | removed.

### 3.10 Digest History & HTML Preview
Every generated digest is stored in the `digests` table with full `content_html` and `content_json`. Users can browse their digest history and render any past digest exactly as it appeared in their email, inside a sandboxed `<iframe>` in the browser.

### 3.11 Progressive Learning Tracks
Seven structured curricula are hardcoded in the system: Azure Fundamentals (18 modules), Microsoft Fabric (10), Power BI (10), Azure AI (10), Azure Data Engineering (11), SQL (10), and Databricks (9). Each module has a defined sequence, difficulty level, duration estimate, learning objectives, and keywords. Users enroll and the system delivers modules automatically, advancing the curriculum pointer after each successful delivery.

### 3.12 Dynamic Lesson Generation
For each Learning Center lesson, the system: (1) performs DuckDuckGo searches for the module topic, (2) scrapes up to 3 web pages (prioritizing learn.microsoft.com), (3) sends the scraped context + module metadata to Groq, and (4) generates a complete structured lesson. Lessons are cached in the `generated_lessons` table, shared across all enrolled users, so lesson generation per module happens only once.

### 3.13 Admin Testing Panel
A comprehensive developer/admin panel at `/admin/testing` (guarded by `ADMIN_ENABLED` config flag) provides: SMTP configuration and test, catalog sync trigger and cache stats, manual digest preview and send, onboarding state debug and repair, topic hierarchy repair, and a sequential team-creation/invite/accept/digest test flow.

---

## 4. Architecture & Technical Flow

### 4.1 Frontend

**Technology:** React 19, React Router 7, Axios, Tailwind CSS 3, Vite 8, Lucide React, Headless UI

**Responsibilities:**
- Google OAuth 2.0 authorization code initiation and callback handling
- JWT storage in localStorage, automatic attachment to all API requests via Axios interceptor
- Auto-logout on 401 via response interceptor
- Hierarchical topic tree rendering with expand/collapse and real-time search filtering
- Multi-step onboarding wizard
- Digest history list and HTML preview via sandboxed iframe
- Team management UI with modals for creation, topic editing, schedule editing, and member invitation
- Learning Center browse/enroll/progress UI
- Admin testing panel with sequential test flows

**Key architectural choices:**
- `AuthContext` is the single source of truth for user identity; all protected routes read from it
- All API calls centralized in `src/services/api.js` — no ad-hoc axios calls scattered across components
- React Router 7 handles all client-side navigation; the app is a true SPA (Single Page Application)
- Protected routes enforced inside `<Layout>` which redirects to `/` if no authenticated user is found

### 4.2 Backend

**Technology:** FastAPI (Python), SQLAlchemy (ORM), Alembic (migrations), APScheduler, Pydantic (validation), Jinja2 (email templates), httpx (outbound HTTP)

**Responsibilities:**
- Google OAuth code exchange and JWT issuance
- Topic tree management and hierarchical subscription resolution
- Digest scheduling evaluation (every 15 minutes)
- Microsoft Learn catalog ingestion and caching (daily cron)
- AI digest enrichment via Groq API
- SMTP email delivery via Gmail
- Team/newsletter management and invitation workflow
- Learning curriculum management and progressive lesson delivery
- Admin testing and debug endpoints

**API structure:** All routes registered under `/api` prefix, organized into router modules:

| Router | Prefix | Key Endpoints |
|---|---|---|
| auth | `/api/auth` | `POST /google` |
| users | `/api/users` | `GET/PUT /me`, `PUT /me/preferences` |
| topics | `/api/topics` | `GET /tree`, `POST /subscribe`, `POST /onboard` |
| digests | `/api/digests` | `GET /`, `GET /:id` |
| teams | `/api/teams` | Full CRUD + newsletter + invitations |
| newsletters | `/api/newsletters` | `GET /` |
| learning | `/api/learning` | Topics, subscribe, progress, seed |
| admin | `/api/admin` | SMTP, catalog, digest testing, team testing |

### 4.3 Database Design

**Technology:** PostgreSQL 16, SQLAlchemy ORM, Alembic migrations

**Core tables and relationships:**

```
users (UUID PK)
  └── user_preferences (1:1)
  └── user_subscriptions (1:many → topics)
  └── digests (1:many)
  └── team_memberships (many:many via team_members)
  └── user_learning_subscriptions (1:many → learning_modules)

topics (self-referential tree)
  └── parent_topic_id → topics.id (nullable, NULL = root)
  └── level (0=root, 1=child)
  └── catalog_products[], catalog_subjects[] (ARRAY(TEXT))

catalog_cache (uid PK)
  └── Populated by daily sync
  └── products_json, subjects_json (JSONB)
  └── Read-only by digest generator

teams
  └── team_newsletters (1:1, UNIQUE on team_id)
      └── newsletter_topics (many:many → topics)
  └── team_members (pending/accepted/declined/expired/removed)
      └── team_invitations (secure token, expiry)

learning_topics
  └── learning_modules (sequence-ordered)
      └── generated_lessons (1:1 per module, shared cache)

user_learning_subscriptions
  └── user_id → users
  └── topic_id → learning_topics
  └── current_module_sequence (advances with each delivery)
```

### 4.4 Authentication Flow

```
Browser → GET /auth/callback?code=XXX
  → AuthCallback.jsx → POST /api/auth/google {code, redirect_uri}
    → AuthService.exchange_google_code()
      → POST https://oauth2.googleapis.com/token (exchange code for access_token)
      → GET https://www.googleapis.com/oauth2/v1/userinfo (get email, name, picture)
      → DB: find user by google_id OR email → upsert
      → create_access_token() → HS256 JWT (sub=user_id)
    → return {access_token, token_type}
  → AuthContext.login(token)
    → localStorage.setItem("token", token)
    → axios.defaults.headers.Authorization = "Bearer <token>"
    → GET /api/users/me → load user into context
    → navigate to /dashboard or /onboarding
```

### 4.5 Scheduling Architecture

APScheduler runs an `AsyncIOScheduler` inside the FastAPI process. Four jobs are registered at startup:

| Job | Trigger | Action |
|---|---|---|
| `run_catalog_sync` | Cron: 02:00 UTC daily | Fetch MS Learn catalog → upsert `catalog_cache` |
| `run_digest_dispatch` | Cron: every 15 min | Evaluate all users + team newsletters, generate + send due digests |
| `run_learning_dispatch` | Cron: every 30 min | Find due learning subscriptions, generate + deliver next lesson |
| `seed_topics` | Date: once at startup | Seeds system topic tree if `topics` table is empty |
| `seed_learning_curriculum_job` | Date: once at startup | Seeds learning curriculum if `learning_topics` is empty |

The 15-minute digest dispatch loop uses `_is_due()` to evaluate each user. This function:
1. Gets the current IST time
2. Snaps it to the current 15-minute bucket
3. Checks if the user's `delivery_time` falls within that bucket
4. For weekly/biweekly: checks `delivery_day` matches current weekday
5. For biweekly: checks the current ISO week number is even
6. For monthly: checks today is the 1st of the month

### 4.6 External Integrations

| Integration | Purpose | Implementation |
|---|---|---|
| Google OAuth 2.0 | User authentication | httpx POST to `oauth2.googleapis.com/token`, GET to `googleapis.com/oauth2/v1/userinfo` |
| Groq LLM API | Digest enrichment + lesson generation | REST API, `json_object` response format, temperature 0.3 |
| Microsoft Learn Catalog API | Content ingestion | `learn.microsoft.com/api/catalog?type=modules`, `?type=learningPaths` |
| Gmail SMTP | Email delivery | STARTTLS on port 587, Python `smtplib` |
| DuckDuckGo Search | Learning resource discovery | `duckduckgo_search` Python library, 3 queries per module |
| BeautifulSoup | Web page scraping | Scrapes up to 3 URLs per module for lesson context |

### 4.7 Deployment Architecture

```
Docker Compose (3 services):
  ├── db (postgres:16-alpine)
  │     Port: 5432
  │     Volume: postgres_data (named, persistent)
  │     Healthcheck: pg_isready
  │
  ├── backend (FastAPI + Uvicorn)
  │     Port: 8000
  │     Build: ./backend/Dockerfile
  │     Hot-reload: --reload flag (dev)
  │     Depends on: db (healthy)
  │     Volume mount: ./backend:/app
  │     Scheduler: runs inside the FastAPI process
  │
  └── frontend (React + Vite dev server)
        Port: 5173
        Build: ./frontend/Dockerfile
        Hot-reload: Vite HMR
        Volume mount: ./frontend:/app
        Anonymous volume: node_modules
        Env: VITE_API_URL=http://localhost:8000
             VITE_GOOGLE_CLIENT_ID from host env
```

---

## 5. AI Workflow

### 5.1 Digest Enrichment (Groq)

**What data is sent to the model:**

For each digest, the `GroqClient.generate_digest()` method constructs a prompt containing:
- The list of subscribed topic names (e.g., "Azure Kubernetes Service, Azure Functions")
- The delivery frequency (e.g., "weekly")
- For each catalog item: `uid`, `title`, `content_type`, and a truncated `summary` (capped at 100 words to control token budget)

**How the prompt is structured:**

The system prompt instructs the model to act as a Microsoft technical education curator. The user prompt provides the list of topics, frequency, and item summaries, then asks for a JSON response with a specific schema.

**What the model returns:**

The model responds in `json_object` format (enforced by the Groq API parameter) with this structure:
```json
{
  "executive_summary": "string — 2-3 paragraph overview of all new content",
  "items": [
    {
      "uid": "module-uid",
      "newsletter_summary": "string — newsletter-style summary of this specific item",
      "why_it_matters": "string — relevance to the subscriber's technology domain",
      "key_takeaways": ["string", "string", "string"]
    }
  ]
}
```

**Temperature:** 0.3 — kept low for factual, consistent technical summaries rather than creative variation.

**How output is formatted and delivered:**

The Groq response is merged back onto the catalog items. Both are then passed to the Jinja2 `digest_email.html` template, which renders a full HTML email with:
- Personalized header (user name, topic list, date range covered)
- Executive summary section
- Individual content cards with all AI-enriched fields
- Footer with unsubscribe / view-in-app links

The rendered HTML is stored in `digests.content_html` and sent via Gmail SMTP.

**Fallback behavior:**

If the Groq call raises any exception, the generator falls back to building items using only the `summary` field from `catalog_cache`. The executive summary in fallback mode is a simple concatenation. The email is still sent; quality is reduced but delivery is guaranteed.

**Dispatch cache:**

Before calling Groq, `_compute_cache_key()` produces a SHA256 hash of `sorted(topic_slugs) + frequency + sorted(content_uids)`. The `dispatch_cache` dict (shared across all users in a single 15-minute scheduler run) is checked first. On a hit, the Groq result is reused and only the Jinja2 render (personalization) is repeated. This is an in-memory cache that lives only for the duration of one scheduler run — it is not persisted.

### 5.2 Learning Lesson Generation (Groq + Web Scraping)

**Resource discovery (before Groq):**

`resource_discovery.discover_resources()` performs three DuckDuckGo searches per module using the module title and keywords. It collects up to 6 candidate URLs, prioritizing `learn.microsoft.com` domains. BeautifulSoup scrapes the page HTML and extracts text content up to 4,000 characters per page. Up to 3 resources are returned.

**What data is sent to the model:**

`LessonGeneratorService.generate_lesson()` sends to Groq:
- Module title, difficulty level, estimated duration
- Learning objectives (array)
- Keywords (array)
- Full scraped resource context (up to 3 pages × 4,000 chars each)

**What the model returns:**

A structured JSON lesson with these sections:
```json
{
  "introduction": "string",
  "explanation": ["paragraph1", "paragraph2", "..."],  // 3-5 paragraphs
  "key_concepts": [{"concept": "...", "description": "..."}],  // 4-6 concepts
  "real_world_example": "string",
  "practical_exercise": {
    "title": "...",
    "description": "...",
    "steps": ["step1", "step2", "..."]
  },
  "quiz": [
    {
      "question": "...",
      "options": ["A", "B", "C", "D"],
      "correct_answer": "A",
      "explanation": "..."
    }
  ],  // 3-5 questions
  "summary": ["bullet1", "bullet2", "..."],
  "next_lesson_preview": "string"
}
```

**Caching:**

The generated lesson JSON is stored in the `generated_lessons` table, keyed by `module_id`. All users enrolled in the same module receive the same lesson content. Generation happens only once per module.

**Delivery:**

The cached lesson is rendered via `learning_email.html` Jinja2 template into a full HTML email with all sections formatted. Sent via the same Gmail SMTP client. After a successful send, `advance_module()` increments `UserLearningSubscription.current_module_sequence` or marks the subscription as `completed` if the user has finished all modules.

---

## 6. Data Flow — Complete Lifecycle

### 6.1 User Signup → First Digest

```
1. USER SIGNUP
   Browser → Google OAuth → /api/auth/google
   → AuthService finds or creates User row
   → JWT minted → returned to browser
   → Stored in localStorage

2. ONBOARDING
   User selects topics from GET /api/topics/tree
   User configures schedule → PUT /api/users/me/preferences
   → UserPreference row upserted (frequency, delivery_time, delivery_day, timezone)
   POST /api/topics/onboard → UserSubscription rows created
   → User.is_onboarded = True

3. CATALOG SYNC (runs nightly at 02:00 UTC)
   CatalogClient.fetch_modules() + fetch_learning_paths()
   → MS Learn Catalog API (learn.microsoft.com/api/catalog)
   → CatalogSyncService._upsert_items()
   → catalog_cache rows inserted/updated (batched 500/commit)
   → SyncMetadata.last_sync_at updated

4. DIGEST DISPATCH (runs every 15 minutes)
   Scheduler: query all users with preferences + subscriptions
   For each user: _is_due(user) → True/False
   If due:
     a. DigestGenerator._build_filter_sets()
        → TopicRepository.resolve_descendant_ids() (recursive CTE)
        → products = union of all catalog_products[] arrays across subscribed topics
        → subjects = union of all catalog_subjects[] arrays
     b. DigestGenerator._query_catalog()
        → SELECT from catalog_cache WHERE last_modified >= window_start
        → Python filter: product/subject overlap with filter sets
     c. If no items → Digest(status="no_content") persisted, no email
     d. _compute_cache_key() → SHA256 → check dispatch_cache
     e. If cache miss: GroqClient.generate_digest() → enriched JSON
        → store in dispatch_cache
     f. Jinja2 render: digest_email.html + personalization + AI content → HTML string
     g. DigestRepository.create_digest() + add_item() per content item
     h. EmailClient.send_email() → Gmail SMTP → User's inbox
     i. DigestRepository.mark_sent() (or mark_failed() on SMTP error)

5. USER VIEWS DIGEST
   GET /api/digests/ → last 20 digests listed
   GET /api/digests/:id → full content_html returned
   Browser renders HTML in sandboxed <iframe>
```

### 6.2 Team Newsletter Lifecycle

```
1. TEAM CREATION
   POST /api/teams → TeamRepository.create_team_with_newsletter()
   → Team + TeamNewsletter created atomically
   → Owner added as accepted member

2. TOPIC CONFIGURATION
   PATCH /api/teams/:id/newsletter/topics
   → NewsletterTopic rows replaced atomically

3. MEMBER INVITATION
   POST /api/teams/:id/members/invite {email}
   → TeamMember(status=pending) + TeamInvitation(secure_token, expires_at) created
   → invitation_email.html rendered → Gmail SMTP → invited email

4. INVITATION ACCEPTANCE (public endpoint, no auth required to preview)
   GET /api/teams/invite/:token → InvitePreviewResponse (no auth)
   POST /api/teams/invite/:token/accept → accept_invitation(token, current_user_id)
   → validates token not expired, not already used
   → TeamMember.user_id linked, status=accepted

5. NEWSLETTER DISPATCH (15-minute scheduler)
   Same _is_due() logic applied to TeamNewsletter
   → DigestGenerator.generate_and_send_for_newsletter()
   → Same filter sets / catalog query / Groq enrichment / Jinja2 render
   → Single Digest row with newsletter_id set
   → Single email to team owner (current implementation)
```

### 6.3 Learning Track Lifecycle

```
1. ENROLLMENT
   POST /api/learning/subscribe {topic_id, frequency}
   → UserLearningSubscription(status=active, current_module_sequence=1, frequency) created

2. LESSON DISPATCH (every 30 minutes)
   LearningRepository.get_all_due_subscriptions()
   → is_due(sub): checks last_sent_at + frequency delta (daily=20h, weekly=6d, biweekly=13d)
   For each due subscription:
     a. Get LearningModule at current_module_sequence
     b. Check generated_lessons cache (by module_id)
     c. If cache miss:
        → resource_discovery.discover_resources() (DuckDuckGo + scrape)
        → LessonGeneratorService.generate_lesson() (Groq call)
        → Store in generated_lessons table
     d. Render learning_email.html with lesson JSON
     e. Gmail SMTP → User's inbox
     f. advance_module(): current_module_sequence++ or status=completed
     g. Update last_sent_at = now()
```

---

## 7. Newsletter & Digest Generation Process

### 7.1 Content Discovery

Every digest generation starts with `_query_catalog()`. The method:

1. Determines the lookback window based on frequency: daily=1 day, weekly=7 days, biweekly=14 days, monthly=30 days.
2. Queries `catalog_cache` for all rows where `last_modified >= window_start`. This is a broad initial fetch — no topic filtering yet.
3. Performs a Python-level filter: each catalog item's `products_json` and `subjects_json` arrays are compared against the user's resolved product/subject filter sets. An item passes if it has any overlap in either products or subjects.

### 7.2 How Filtering Works

The filter sets are built by `_build_filter_sets()`:
1. Collect all the user's subscribed topic IDs.
2. Expand each via `TopicRepository.resolve_descendant_ids()` — a PostgreSQL recursive CTE that walks the topic tree and returns all descendant IDs.
3. For all expanded topic IDs, load their `catalog_products` and `catalog_subjects` arrays from the `topics` table.
4. Union all products and subjects into two flat sets.

For example, a user subscribed only to "Azure" (root level) will have their filter set automatically expanded to include the products and subjects associated with Azure Kubernetes Service, Azure Functions, Azure Storage, Azure AI Services, and every other Azure subtopic — without the user needing to explicitly subscribe to each.

### 7.3 How Personalization Works

Personalization operates at two levels:

**Topic-level personalization:** Each user's filter sets are derived uniquely from their specific subscriptions. Two users subscribed to different topics receive entirely different content selections.

**AI-level personalization:** The Groq prompt includes the user's specific topic names, so the executive summary and "why it matters" sections are framed around their actual area of interest.

**Greeting personalization:** The Jinja2 template renders the user's name in the email header. Even when the dispatch cache is hit (same Groq result reused for multiple users), the HTML is re-rendered individually for each user.

### 7.4 How Summaries Are Generated

The Groq LLM receives the full list of content items (uid, title, content_type, truncated summary) and the user's topic interests. It returns:

- **Executive summary:** A 2-3 paragraph overview synthesizing the themes and significance of all new content in this delivery window, framed around the subscriber's technology focus.
- **Per-item newsletter summary:** A 2-3 sentence editorial summary written in newsletter style, more contextual and readable than the raw Microsoft Learn module description.
- **Why it matters:** A 1-2 sentence explanation of why this specific piece of content is relevant to someone in the subscriber's technology domain.
- **Key takeaways:** 3 bullet points — the concrete skills or knowledge the learner will gain from this module.

### 7.5 How Emails Are Created and Sent

The HTML email is rendered by Jinja2 from `digest_email.html`. The rendered string is stored in `digests.content_html` in the database, then passed to `EmailClient.send_email()`.

`EmailClient` uses Python's `smtplib` with STARTTLS on port 587 (Gmail). It creates a `MIMEMultipart('alternative')` message with both a plain text fallback and the HTML body. The SMTP connection is opened, authenticated, mail sent, and the connection closed within a single `with` block. The method returns a boolean; on failure, the `DigestRepository` marks the digest as `status="failed"`.

---

## 8. Detailed Feature Documentation

---

### Feature: Google OAuth Authentication

**Purpose:** Frictionless, passwordless sign-in tied to existing Google accounts. Eliminates credential management and leverages Google's identity infrastructure for security.

**User Experience:** One click on "Sign in with Google" on the landing page. Standard Google consent screen. Automatic redirect back to the app. No username or password fields anywhere.

**Technical Implementation:**
- Standard OAuth 2.0 authorization code flow (PKCE not implemented — uses `response_type=code` with `redirect_uri`)
- Backend exchanges code at `oauth2.googleapis.com/token` using `httpx`
- UserInfo fetched from `googleapis.com/oauth2/v1/userinfo`
- User upsert: find by `google_id` first, then `email`, then create new
- JWT: HS256, `sub=user_id`, configurable expiry via `JWT_EXPIRE_MINUTES`
- Frontend: `AuthContext` manages session state, auto-restores from localStorage, auto-clears on 401

**Business Value:** Lowers friction for sign-up dramatically. Users in corporate environments (Microsoft, Azure AD tenants) already use Google Workspace or personal Google accounts. Zero password reset support burden.

---

### Feature: Hierarchical Topic Subscriptions

**Purpose:** Allow users to subscribe at a broad level ("Azure") or a granular level ("Azure Kubernetes Service") and always receive accurately filtered content either way.

**User Experience:** An expandable two-level topic tree with emoji icons and real-time search. Root sections like "Azure" expand to reveal 5–10 subtopics. Selections persist across search queries. The selected count shown in the onboarding step summary.

**Technical Implementation:**
- `topics` table has `parent_topic_id` (self-referential FK) and `level` (0=root, 1=child)
- `catalog_products[]` and `catalog_subjects[]` arrays on each topic node define what catalog content matches
- `resolve_descendant_ids()` uses a PostgreSQL recursive CTE to walk the tree at query time
- `replace_user_subscriptions()` atomically deletes and re-inserts on every save
- Tree seeded with 9 root topics + 60+ subtopics via `TopicRepository.seed_system_topics()`

**Business Value:** Users don't need to know the exact Microsoft product taxonomy. Subscribing to "Azure" just works, and the system handles the complexity of mapping that to the right catalog filter criteria.

---

### Feature: Configurable Delivery Scheduling

**Purpose:** Let users set delivery on their own terms — not everyone wants a daily digest. Some prefer a Monday morning weekly roundup; others want biweekly or monthly summaries.

**User Experience:** Simple dropdowns in onboarding and preferences: Frequency (Daily / Weekly / Biweekly / Monthly), Day of Week (for weekly/biweekly), Delivery Time (hour/minute picker). Changes take effect at the next dispatch run.

**Technical Implementation:**
- `user_preferences` table stores `frequency` (enum string), `delivery_time` (PostgreSQL TIME), `delivery_day` (0–6 int), `timezone`
- APScheduler fires `run_digest_dispatch` every 15 minutes
- `_is_due()` function: snaps current IST time to 15-minute bucket, matches against stored `delivery_time` within that bucket
- Biweekly uses `ISO week number % 2 == 0` check
- Monthly uses `day == 1` check

**Business Value:** Respects user attention. A monthly digest is genuinely useful for someone who just wants a monthly "what did I miss" email, without the noise of daily delivery.

---

### Feature: AI-Enriched Digest Emails

**Purpose:** Raw Microsoft Learn module titles and descriptions are not compelling email content. The AI layer transforms catalog metadata into editorial-quality newsletter content.

**User Experience:** Users receive a polished HTML email with: an executive summary synthesizing the month/week's Microsoft technology news in their domain, followed by individual content cards with newsletter summaries, "why it matters" rationale, and concrete key takeaways — not just a list of links.

**Technical Implementation:**
- `GroqClient.generate_digest(items, topic_names, frequency)` → structured JSON
- `json_object` response format enforced (prevents free-form text responses)
- Temperature 0.3 for factual consistency
- Summaries truncated to 100 words each before sending to control prompt token budget
- Groq token counts and latency logged per call
- Fallback to `catalog_cache.summary` if Groq fails

**Business Value:** Users actually read the digest because it's written in newsletter style, not catalog-dump style. The "why it matters" section specifically contextualizes each item for the subscriber's technology focus area.

---

### Feature: Groq Dispatch Cache

**Purpose:** Prevent redundant LLM API calls when multiple users have identical (or overlapping) topic subscriptions and receive the same content in a given dispatch run.

**User Experience:** Transparent to the user. Each user still receives a personalized email (their name in the greeting, their topics in the header). The cache only affects whether Groq is called.

**Technical Implementation:**
- `_compute_cache_key()`: `SHA256(sorted_topic_slugs + frequency + sorted_content_uids)`
- `dispatch_cache: dict` passed to `generate_and_send_for_user()` by the scheduler
- Cache scoped to a single scheduler run (in-memory, not Redis, not persisted)
- On hit: reuse Groq JSON, re-render Jinja2 with user-specific data
- On miss: Groq call → store in cache → continue

**Business Value:** Cost and latency reduction for large deployments where many users share common topic subscriptions (e.g., an entire team subscribed to Azure).

---

### Feature: Team Newsletters

**Purpose:** Engineering teams and L&D programs need a coordinated, shared view of Microsoft technology updates — not just individual subscriptions scattered across team members.

**User Experience:** Team owner creates a team, sets a name and description, selects topics and schedule, and gets a configured newsletter. Invites colleagues by email. Each invitee receives an email with accept/decline links. Once the team is set up, the newsletter runs fully automatically.

**Technical Implementation:**
- `TeamRepository.create_team_with_newsletter()`: single transaction, atomic creation of `Team` + `TeamNewsletter` + `TeamMember` (owner, status=accepted)
- `UNIQUE(team_id)` constraint on `team_newsletters` — one newsletter per team enforced at DB level
- `TeamInvitation`: `secrets.token_urlsafe(32)` secure token, `expires_at` computed from `INVITATION_EXPIRY_HOURS`
- Public invite endpoints at `/api/teams/invite/:token` (no auth for preview and decline; auth required for accept)
- Static `/invite/` path declared before `/{team_id}` in router to prevent route shadowing
- Newsletter dispatch shares same digest engine as personal digests

**Business Value:** L&D teams can run structured, automated Microsoft technology newsletters for entire engineering departments with zero manual curation effort after initial setup.

---

### Feature: Progressive Learning Tracks (Learning Center)

**Purpose:** A digest of new content is reactive. The Learning Center is proactive — it takes users through a structured, progressive curriculum regardless of what's new in the catalog.

**User Experience:** Browse 7 curriculum tracks. Enroll with a frequency choice. Receive the first lesson by email. Open your inbox and find a complete educational module: introduction, explanation, key concepts, real-world example, hands-on exercise, quiz, and a preview of what's next. Come back to the Learning Center to see your progress bar advance module by module.

**Technical Implementation:**
- Curriculum hardcoded in `curriculum.py` with 78 total modules across 7 tracks
- `UserLearningSubscription.current_module_sequence` advances with each delivery
- `generated_lessons` table caches Groq-generated lesson JSON by `module_id`
- Resource discovery: DuckDuckGo → BeautifulSoup scraping → up to 3 pages × 4,000 chars context
- `LessonGeneratorService.generate_lesson()` → full lesson JSON schema (8 sections)
- Lesson generation happens once per module; subsequent users get cached lesson

**Business Value:** Transforms the platform from a "notification system" into a "learning system." Users can commit to structured Microsoft technology upskilling without any active effort beyond enrollment.

---

### Feature: Admin Testing Panel

**Purpose:** Provides developers and administrators with a full end-to-end testing environment without requiring a production-like environment or waiting for scheduled jobs.

**User Experience:** Visible only when `ADMIN_ENABLED=True`. Sections let the admin: test SMTP connectivity, trigger catalog sync manually, preview what a digest would look like for their account, send themselves a real digest immediately, repair topic hierarchy, and walk through the entire team creation → invite → accept → digest pipeline in a sequential UI.

**Technical Implementation:**
- All admin endpoints guarded by `_check_admin_enabled()` function
- `POST /api/admin/test/send-my-digest` — real digest for the authenticated admin user
- `POST /api/admin/smtp/check` — calls `EmailClient.test_connection()`, returns structured result
- `GET /api/admin/catalog/stats` — row count, last sync time, sample items
- Team test flow: `test-create-team` → `test-invite` → `test-accept-invite` → `test-send-digest`
- `useAction()` hook in `AdminTesting.jsx` manages loading/success/error state for each action

**Business Value:** Dramatically accelerates development and debugging. New engineers can validate the entire delivery pipeline without waiting for a scheduled job to fire or needing database access.

---

## 9. Technical Challenges & Solutions

### Challenge 1: Microsoft Learn Catalog Size (40MB+ unfiltered)

**Problem:** The Microsoft Learn Catalog API returns a single unfiltered JSON payload exceeding 40MB. Fetching this on every digest generation would be prohibitively slow and expensive.

**Solution:** A two-layer architecture. First, the `CatalogClient` uses filtered API calls (`?type=modules` and `?type=learningPaths` separately), reducing the payload to ~8MB + ~3MB. Second, a nightly cron job syncs these into the `catalog_cache` PostgreSQL table. Digest generation never calls the Microsoft Learn API — it reads only from the local cache. This decouples ingestion from delivery and makes digest generation fast and offline-tolerant.

### Challenge 2: Hierarchical Topic Matching at Query Time

**Problem:** Users subscribe to topics like "Azure" but content in the catalog is tagged with fine-grained product names like "Azure Kubernetes Service" or "Azure Functions." A flat subscription model would fail to match any content.

**Solution:** The topic tree model with `catalog_products[]` and `catalog_subjects[]` arrays on each topic node. At digest generation time, `resolve_descendant_ids()` uses a PostgreSQL recursive CTE to expand any parent subscription to all its descendants, then the system unions all their product/subject arrays into filter sets. This scales to any tree depth without O(n) recursive application-level loops.

### Challenge 3: Groq API Cost and Latency at Scale

**Problem:** If 100 users have overlapping topic subscriptions and all receive a weekly digest on the same day, calling Groq 100 times for effectively the same content is wasteful and slow.

**Solution:** The `dispatch_cache` SHA256 key pattern. Within a single 15-minute scheduler run, if users A, B, and C all receive the same set of content UIDs with the same topic slugs and frequency, Groq is called once. The result is cached in-memory for the duration of that run. Re-rendering the Jinja2 template per user is negligible. This optimization doesn't require Redis or any external infrastructure.

### Challenge 4: Delivery Must Never Be Blocked by LLM Failure

**Problem:** If the Groq API is down, rate-limited, or returns malformed JSON, digest delivery should still happen — just with reduced enrichment.

**Solution:** Both the digest generator and lesson generator wrap their Groq calls in try/except blocks with explicit fallback logic. The digest fallback uses the `summary` field from `catalog_cache` directly. The lesson fallback returns a minimal lesson skeleton. In both cases, the email is still sent and the digest/lesson is marked as delivered. Groq errors are logged but never re-raised to the email delivery layer.

### Challenge 5: OAuth Callback Double-Invocation (React StrictMode)

**Problem:** React 18+ StrictMode intentionally invokes effects twice in development. The OAuth callback component would fire the backend auth request twice, causing a race condition — the second request might fail because the authorization code is single-use.

**Solution:** A `called.current` ref flag in `AuthCallback.jsx` gates the API call. The first invocation sets `called.current = true` and proceeds. The second invocation sees `true` and returns immediately. This is a standard React StrictMode guard pattern.

### Challenge 6: Route Shadowing in FastAPI (Invitations vs. Team IDs)

**Problem:** FastAPI's router evaluates routes in registration order. The team invitation endpoints use paths like `/invite/{token}` but the team router also has `/{team_id}` as a dynamic route. Without careful ordering, `/{team_id}` would intercept all `/invite/{token}` requests.

**Solution:** Static paths (including all `/invite/` paths) are declared before the dynamic `/{team_id}` route in `teams.py`. FastAPI's router resolves the first matching route, so static paths always take priority when registered first.

### Challenge 7: Self-Referential SQLAlchemy Tree (Double Population Bug)

**Problem:** Using SQLAlchemy's `relationship` with `lazy="joined"` on the self-referential `topics` tree caused Pydantic schema population to double-count child nodes when building the topic tree.

**Solution:** The `TopicNode` Pydantic schema does NOT use `model_config = ConfigDict(from_attributes=True)` for the `children` field. The `GET /topics/tree` endpoint builds the tree manually in `_build_tree()` using a Python dict-based approach, bypassing SQLAlchemy's relationship loading entirely for the tree construction. Flat topic queries still use ORM normally.

### Challenge 8: Catalog Upsert Performance

**Problem:** The catalog contains thousands of modules and learning paths. A naive delete-all/insert-all strategy would lock the table and cause visible downtime during the nightly sync.

**Solution:** PostgreSQL `INSERT...ON CONFLICT (uid) DO UPDATE` (upsert). Rows are processed in batches of 500, with a commit after each batch. Only rows with changed content are effectively updated. The table is never empty during sync — new rows are added and existing ones are updated in place.

### Scalability Considerations

The current architecture runs the scheduler in-process with FastAPI (APScheduler `AsyncIOScheduler`). This is appropriate for a single-instance deployment. For horizontal scaling, the scheduler would need to be extracted to a dedicated worker process (Celery + Redis, or a separate APScheduler instance with distributed locking) to prevent duplicate digest deliveries from multiple instances.

The PostgreSQL connection pool (`pool_size=10, max_overflow=20`) handles moderate concurrent load. For high user volumes, read replicas and connection poolers (PgBouncer) would be the next scaling step.

---

## 10. Demo Script (3–5 Minutes)

---

*[Opening — 20 seconds]*

"Let me show you MS Learn Digest — a platform I built to solve a real problem I ran into as a Microsoft technology practitioner: keeping up with everything Microsoft publishes on their Learn platform is exhausting. There are thousands of modules across Azure, AI, Fabric, Security, and more, and the catalog changes constantly. This platform automates the entire discovery, summarization, and delivery process."

---

*[Authentication — 30 seconds]*

"Starting here on the landing page — one click on Sign in with Google kicks off a standard OAuth flow. No password, no form. The backend exchanges the authorization code with Google, fetches the user profile, and mints a JWT. If this is a new user, we land on the onboarding wizard."

---

*[Onboarding — 45 seconds]*

"The onboarding is a two-step wizard. First, I pick my technology topics from this hierarchical tree. Notice I have nine root domains — Azure, Microsoft Fabric, Power Platform, AI Engineering, and so on — each expanding to reveal more specific subtopics.

Here's something important: if I just check 'Azure' at the root level, the system expands that subscription to include all Azure subtopics automatically, using a PostgreSQL recursive CTE to walk the topic tree at query time. I'm not just subscribing to a label — I'm subscribing to the full product taxonomy underneath it.

Step two is my delivery schedule. I'll set weekly, Monday, at 8 AM. Done — I'm onboarded."

---

*[Dashboard — 30 seconds]*

"The dashboard shows me when my next delivery is, the last time I received a digest, how many total digests I've received, and how many topics I'm subscribed to. I can also hit 'Send Digest Now' to trigger an immediate generation without waiting for the scheduler — useful for demos like this.

Every 15 minutes, the scheduler checks every user against their configured schedule. When it's my time, the system queries the catalog cache for content published in my delivery window, filters it against my topic subscriptions, and sends it to Groq."

---

*[AI Digest Email — 60 seconds]*

"Here's what arrives in my inbox. This is a fully rendered HTML email. At the top — an executive summary. This isn't a dump of module titles. Groq analyzed all the new content against my Azure focus and wrote a two-paragraph editorial summary of what's new and why it matters.

Below that, individual cards for each content item. Each one has an AI-written newsletter summary, a 'Why it matters' section framed around my specific tech domain, and bullet-point key takeaways. The user experience is more like reading a tech newsletter than browsing a catalog.

I can also view this digest right here in the app — rendered in a sandboxed iframe, exactly as it appeared in email."

---

*[Teams — 30 seconds]*

"For teams — a manager creates a team, configures shared topic subscriptions and a schedule, and invites team members by email. Invitees receive a secure email link. They can preview the invitation without being logged in — see the team name, topics, schedule, expiry — and accept or decline in one click. After that, the team newsletter runs automatically on the same dispatch engine as personal digests."

---

*[Learning Center — 30 seconds]*

"The Learning Center is a different kind of feature — it's a proactive curriculum engine. Seven structured learning tracks. I enroll in Azure Data Engineering, and the system starts at Module 1. It uses DuckDuckGo to discover relevant web resources, scrapes them for context, and sends that context to Groq to generate a full educational lesson — introduction, explanation, key concepts, a hands-on exercise, a quiz. Delivered to my inbox. After each delivery, it automatically advances to the next module. Progress is tracked here — I can see exactly where I am in the curriculum."

---

*[Closing — 20 seconds]*

"The full stack is FastAPI, PostgreSQL, React, APScheduler, and Groq — containerized with Docker Compose. The engineering emphasis was on reliability: Groq failures fall back to catalog summaries so delivery is never blocked, the catalog sync is non-destructive upserts, and the dispatch cache eliminates redundant LLM calls when users share subscriptions. I built this end-to-end. Happy to go deeper on any part of it."

---

## 11. Resume & Portfolio Descriptions

---

### Resume (1–3 bullet lines)

```
MS Learn Digest | FastAPI · React · PostgreSQL · Groq LLM · APScheduler · Docker
• Built a full-stack AI-powered newsletter platform that monitors the Microsoft Learn catalog daily,
  enriches new content with Groq LLM (executive summaries, key takeaways, "why it matters"), and
  delivers personalized HTML digest emails to users and teams on configurable schedules.
• Implemented hierarchical topic subscriptions using PostgreSQL recursive CTEs, a catalog-cache
  ingestion pipeline with upsert batching, a Groq dispatch cache (SHA256 keying) to eliminate
  redundant LLM calls, and a graceful fallback delivery system ensuring zero LLM-blocked deliveries.
• Engineered a progressive Learning Center with DuckDuckGo resource discovery, BeautifulSoup
  scraping, and Groq lesson generation — automatically advancing 78-module curricula across 7
  technology tracks with per-module lesson caching shared across all enrolled users.
```

---

### LinkedIn Summary

```
🚀 Project: MS Learn Digest

An AI-powered learning intelligence platform I built end-to-end to solve the problem of staying
current with Microsoft's ever-changing Learn catalog.

What it does:
→ Monitors the MS Learn catalog daily (thousands of modules + learning paths)
→ Filters content to each user's subscribed technology domains (Azure, AI, Fabric, Power BI, etc.)
→ Enriches new content with Groq LLM: executive summaries, "why it matters," key takeaways
→ Delivers rich HTML digest emails on user-configured schedules (daily/weekly/biweekly/monthly)
→ Runs team newsletters for engineering orgs with a full invite/accept workflow
→ Delivers structured 78-module progressive curricula across 7 tech tracks via the Learning Center

Tech stack: FastAPI · React 19 · PostgreSQL · APScheduler · Groq · Gmail SMTP · Docker Compose

Key engineering highlights:
✦ Hierarchical topic subscriptions via PostgreSQL recursive CTEs
✦ Catalog-cache pattern decoupling ingestion from delivery
✦ SHA256 dispatch cache eliminating redundant Groq calls across users
✦ Groq fallback guaranteeing delivery even on LLM failures
✦ DuckDuckGo + BeautifulSoup resource discovery for lesson generation
✦ Lesson caching shared across all enrolled users (generate once, reuse forever)
```

---

### Portfolio Website Description

**MS Learn Digest — AI-Powered Microsoft Learning Newsletter Platform**

MS Learn Digest is a production-ready, full-stack application that automates the discovery, AI enrichment, and email delivery of personalized Microsoft technology learning content.

The platform syncs the entire Microsoft Learn catalog daily, matches new content against each user's hierarchical technology topic subscriptions, and uses Groq's LLM API to generate editorial-quality digest emails — complete with an executive summary, per-item newsletter summaries, contextual "why it matters" explanations, and key takeaways. Emails are delivered on user-configured schedules (daily through monthly) via Gmail SMTP.

A team newsletter engine allows engineering teams to run shared Microsoft technology digests with a full invitation and acceptance workflow. A separate Learning Center engine delivers structured, progressive curricula — 78 modules across 7 technology domains — with Groq-generated lessons enriched by live web resource discovery and scraping.

**Stack:** FastAPI · Python · React 19 · Tailwind CSS · PostgreSQL · SQLAlchemy · Alembic · APScheduler · Groq LLM · Gmail SMTP · Docker Compose

**Highlights:** Recursive CTE topic expansion · Catalog-cache ingestion pipeline · Dispatch-run Groq caching · Graceful LLM fallback delivery · DuckDuckGo + BeautifulSoup lesson enrichment · Per-module shared lesson cache

---

### GitHub README Description

```markdown
# MS Learn Digest

> AI-powered Microsoft Learn newsletter platform — monitors the catalog, enriches content 
> with Groq LLM, and delivers personalized digest emails to individuals and teams.

## What It Does

- **Daily catalog sync** — fetches the full Microsoft Learn modules + learning paths catalog
  and upserts changes into a local PostgreSQL cache
- **Personalized digests** — users subscribe to hierarchical technology topics (Azure, AI, 
  Fabric, Power BI, Security, and more); new content is filtered and AI-enriched automatically
- **Groq LLM enrichment** — executive summaries, newsletter-style item summaries, "why it 
  matters" context, and key takeaways generated per delivery
- **Flexible scheduling** — daily, weekly, biweekly, or monthly delivery at user-configured time
- **Team newsletters** — create teams, configure shared topic subscriptions, invite members 
  via secure email links, receive coordinated team digests
- **Learning Center** — 7 structured curriculum tracks (78 modules), progressive lesson 
  delivery with web resource discovery + Groq lesson generation, per-module lesson caching

## Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, SQLAlchemy, Alembic, APScheduler |
| Frontend | React 19, React Router 7, Tailwind CSS, Vite |
| Database | PostgreSQL 16 |
| AI | Groq LLM API |
| Email | Gmail SMTP (STARTTLS) |
| Ingestion | MS Learn Catalog API, DuckDuckGo, BeautifulSoup |
| Infrastructure | Docker Compose |

## Quick Start

```bash
cp .env.example .env
# fill in DATABASE_URL, SMTP_*, GOOGLE_*, GROQ_API_KEY, JWT_SECRET_KEY
docker compose up --build
# Run migrations
docker compose exec backend alembic upgrade head
```

App available at: `http://localhost:5173`
API docs: `http://localhost:8000/docs`
```

---

## 12. System Architecture Diagram (Text)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DOCKER COMPOSE                                      │
│                                                                                  │
│  ┌─────────────────────┐     ┌────────────────────────────────────────────────┐ │
│  │   FRONTEND           │     │   BACKEND (FastAPI + Uvicorn :8000)            │ │
│  │   React 19 + Vite    │     │                                                │ │
│  │   :5173              │     │  ┌─────────────────────────────────────────┐  │ │
│  │                      │ HTTP│  │   API LAYER (/api)                       │  │ │
│  │  Pages:              │◄───►│  │  auth · users · topics · digests         │  │ │
│  │  - LandingPage       │     │  │  teams · newsletters · learning · admin  │  │ │
│  │  - AuthCallback      │     │  └─────────────┬───────────────────────────┘  │ │
│  │  - Onboarding        │     │                │                              │ │
│  │  - Dashboard         │     │  ┌─────────────▼───────────────────────────┐  │ │
│  │  - Preferences       │     │  │   SERVICE LAYER                          │  │ │
│  │  - Teams             │     │  │  AuthService · DigestGenerator          │  │ │
│  │  - DigestDetail      │     │  │  CatalogSyncService · EmailClient       │  │ │
│  │  - LearningCenter    │     │  │  LessonGenerator · NewsletterGenerator  │  │ │
│  │  - AdminTesting      │     │  └───┬─────────┬──────────┬───────────────┘  │ │
│  │                      │     │      │         │          │                  │ │
│  │  Context:            │     │  ┌───▼──┐  ┌──▼────┐  ┌──▼──────┐          │ │
│  │  AuthContext         │     │  │Repos │  │ Sched │  │ Models  │          │ │
│  │                      │     │  │(ORM) │  │(APSch)│  │(SQLAlch)│          │ │
│  │  Services:           │     │  └───┬──┘  └──┬────┘  └─────────┘          │ │
│  │  api.js (Axios)      │     │      │         │                            │ │
│  └─────────────────────┘     └──────┼─────────┼────────────────────────────┘ │
│                                     │         │                               │
│  ┌──────────────────────────────────▼─────────▼────────────────────────────┐  │
│  │   PostgreSQL 16  (:5432)                                                 │  │
│  │                                                                          │  │
│  │  users · user_preferences · user_subscriptions · topics                 │  │
│  │  catalog_cache · digests · digest_items                                 │  │
│  │  teams · team_members · team_newsletters · team_invitations             │  │
│  │  newsletter_topics · sync_metadata                                      │  │
│  │  learning_topics · learning_modules · user_learning_subscriptions       │  │
│  │  generated_lessons                                                       │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘

EXTERNAL SERVICES (outbound from backend):

┌──────────────────────┐    ┌─────────────────────┐    ┌───────────────────────┐
│  Google OAuth 2.0    │    │  Groq LLM API        │    │  MS Learn Catalog API │
│  oauth2.googleapis   │    │  api.groq.com        │    │  learn.microsoft.com  │
│  .com                │    │  /chat/completions   │    │  /api/catalog         │
│  (auth code exchange │    │  (digest enrichment  │    │  (daily sync: modules │
│  + userinfo)         │    │  + lesson generation)│    │  + learning paths)    │
└──────────────────────┘    └─────────────────────┘    └───────────────────────┘

┌──────────────────────┐    ┌─────────────────────┐
│  Gmail SMTP          │    │  DuckDuckGo Search   │
│  smtp.gmail.com:587  │    │  + BeautifulSoup     │
│  (STARTTLS)          │    │  (Learning Center    │
│  (digest emails +    │    │  resource discovery  │
│  invitation emails + │    │  + page scraping)    │
│  lesson emails)      │    │                      │
└──────────────────────┘    └─────────────────────┘

SCHEDULER JOBS (running inside backend process):

┌─────────────────────────────────────────────────────────────────────┐
│  APScheduler (AsyncIOScheduler)                                     │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ run_catalog_sync      │ Cron: 02:00 UTC daily                │  │
│  │                       │ MS Learn API → catalog_cache upsert  │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │ run_digest_dispatch   │ Cron: every 15 min                   │  │
│  │                       │ Eval all users → filter → Groq →     │  │
│  │                       │ Jinja2 → SMTP → persist digest       │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │ run_learning_dispatch │ Cron: every 30 min                   │  │
│  │                       │ Find due subs → resource discovery → │  │
│  │                       │ Groq lesson → SMTP → advance module  │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │ seed_topics           │ Date: once at startup                 │  │
│  │ seed_learning_curriculum│ Date: once at startup              │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘

DATA FLOW SUMMARY:

MS Learn Catalog API
       │
       ▼  (daily, 02:00 UTC)
catalog_cache (PostgreSQL)
       │
       ▼  (every 15 min, per due user)
DigestGenerator
  ├── resolve_descendant_ids() → recursive CTE → expanded topic filter sets
  ├── query catalog_cache → Python filter by products/subjects overlap
  ├── SHA256 dispatch_cache check
  ├── [miss] → Groq API → enriched JSON → cache it
  ├── Jinja2 render → personalized HTML email
  ├── persist Digest + DigestItems (self-contained, no FK to catalog_cache)
  └── Gmail SMTP → user inbox

User Enrollment (Learning Center)
       │
       ▼  (every 30 min, per due subscription)
LearningNewsletterGenerator
  ├── get current module (sequence pointer)
  ├── check generated_lessons cache
  ├── [miss] → DuckDuckGo search → BeautifulSoup scrape → Groq lesson → cache
  ├── Jinja2 render → learning HTML email
  ├── Gmail SMTP → user inbox
  └── advance_module() → sequence++ or status=completed
```

---

*Documentation generated from full codebase inspection — June 2026.*
*All described behaviors are implemented in the actual codebase. No speculative or assumed features included.*
