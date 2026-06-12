# MS Learn Digest & Team Newsletter Agent — Implementation Plan

## Overview

Build a production-ready MVP that monitors the Microsoft Learn Catalog API, enriches content with Groq AI, and delivers personalized/team newsletters via Gmail SMTP. The platform supports Google OAuth login, topic subscriptions, team management, and digest history.

---

## Project Structure

```
MS-Learn-Digest/
├── backend/
│   ├── alembic/                    # Database migrations
│   │   ├── versions/
│   │   └── env.py
│   ├── app/
│   │   ├── api/                    # FastAPI route handlers
│   │   │   ├── __init__.py
│   │   │   ├── auth.py             # POST /auth/google
│   │   │   ├── users.py            # GET /users/me
│   │   │   ├── topics.py           # GET /topics, POST /topics/subscribe
│   │   │   ├── teams.py            # POST /teams, POST /teams/{id}/invite, GET /teams
│   │   │   ├── newsletters.py     # POST /newsletters, GET /newsletters
│   │   │   └── digests.py          # GET /digests, GET /digests/{id}
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── topic.py
│   │   │   ├── team.py
│   │   │   ├── content.py
│   │   │   ├── digest.py
│   │   │   └── newsletter.py
│   │   ├── schemas/                # Pydantic request/response schemas
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── user.py
│   │   │   ├── topic.py
│   │   │   ├── team.py
│   │   │   ├── content.py
│   │   │   ├── digest.py
│   │   │   └── newsletter.py
│   │   ├── services/               # Business logic layer
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── user_service.py
│   │   │   ├── topic_service.py
│   │   │   ├── team_service.py
│   │   │   ├── content_service.py
│   │   │   ├── digest_service.py
│   │   │   └── newsletter_service.py
│   │   ├── repositories/           # Database access layer
│   │   │   ├── __init__.py
│   │   │   ├── user_repo.py
│   │   │   ├── topic_repo.py
│   │   │   ├── team_repo.py
│   │   │   ├── content_repo.py
│   │   │   └── digest_repo.py
│   │   ├── jobs/                   # APScheduler tasks
│   │   │   ├── __init__.py
│   │   │   ├── scheduler.py
│   │   │   ├── catalog_sync.py
│   │   │   ├── content_enrichment.py
│   │   │   └── digest_generation.py
│   │   ├── ai/                     # Groq AI integration
│   │   │   ├── __init__.py
│   │   │   ├── groq_client.py
│   │   │   └── prompts.py
│   │   ├── ingestion/              # MS Learn Catalog API client
│   │   │   ├── __init__.py
│   │   │   ├── catalog_client.py
│   │   │   └── content_scraper.py
│   │   ├── email/                  # Gmail SMTP integration
│   │   │   ├── __init__.py
│   │   │   ├── smtp_client.py
│   │   │   └── templates.py
│   │   ├── core/                   # App configuration & utilities
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── security.py
│   │   │   └── logging.py
│   │   └── main.py                 # FastAPI app entry point
│   ├── alembic.ini
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/             # Reusable UI components
│   │   │   ├── Layout/
│   │   │   ├── Navbar/
│   │   │   ├── DigestCard/
│   │   │   ├── TopicSelector/
│   │   │   ├── TeamCard/
│   │   │   └── common/
│   │   ├── pages/                  # Route pages
│   │   │   ├── Landing.jsx
│   │   │   ├── Onboarding.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── DigestHistory.jsx
│   │   │   ├── DigestView.jsx
│   │   │   ├── TeamManagement.jsx
│   │   │   └── AdminDashboard.jsx
│   │   ├── hooks/                  # Custom React hooks
│   │   │   ├── useAuth.js
│   │   │   ├── useTopics.js
│   │   │   ├── useDigests.js
│   │   │   └── useTeams.js
│   │   ├── services/               # API client layer
│   │   │   ├── api.js
│   │   │   ├── authService.js
│   │   │   ├── topicService.js
│   │   │   ├── digestService.js
│   │   │   └── teamService.js
│   │   ├── context/                # React context providers
│   │   │   └── AuthContext.jsx
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.jsx
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .env
├── .env.example
└── README.md
```

---

## Database Schema Design

### Core Tables

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    google_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    avatar_url TEXT,
    role VARCHAR(50) DEFAULT 'individual',  -- 'individual', 'admin'
    is_onboarded BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- User preferences
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    frequency VARCHAR(50) DEFAULT 'weekly',    -- 'daily', 'weekly', 'biweekly', 'monthly'
    delivery_time TIME DEFAULT '08:00:00',
    delivery_day INTEGER DEFAULT 1,            -- 0=Mon, 6=Sun (for weekly)
    timezone VARCHAR(100) DEFAULT 'UTC',
    UNIQUE(user_id)
);

-- Topics (system-defined, extensible)
CREATE TABLE topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    is_system BOOLEAN DEFAULT TRUE,
    catalog_products TEXT[],                   -- Mapped MS Learn product IDs
    catalog_subjects TEXT[],                   -- Mapped MS Learn subject IDs
    created_at TIMESTAMP DEFAULT NOW()
);

-- User topic subscriptions
CREATE TABLE user_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    topic_id UUID REFERENCES topics(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, topic_id)
);

-- Teams
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    admin_id UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Team members
CREATE TABLE team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    email VARCHAR(255) NOT NULL,              -- Allow inviting non-registered users
    role VARCHAR(50) DEFAULT 'member',        -- 'admin', 'member'
    status VARCHAR(50) DEFAULT 'invited',     -- 'invited', 'active'
    joined_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(team_id, email)
);

-- Team newsletters (newsletter configuration)
CREATE TABLE team_newsletters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    frequency VARCHAR(50) DEFAULT 'weekly',
    delivery_time TIME DEFAULT '09:00:00',
    delivery_day INTEGER DEFAULT 0,
    timezone VARCHAR(100) DEFAULT 'UTC',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Newsletter topic selections
CREATE TABLE newsletter_topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    newsletter_id UUID REFERENCES team_newsletters(id) ON DELETE CASCADE,
    topic_id UUID REFERENCES topics(id) ON DELETE CASCADE,
    UNIQUE(newsletter_id, topic_id)
);

-- Content (synced from MS Learn Catalog API)
CREATE TABLE content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    uid VARCHAR(500) UNIQUE NOT NULL,         -- MS Learn UID
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    content_type VARCHAR(100) NOT NULL,       -- 'module', 'learningPath', 'certification', 'exam', 'appliedSkill'
    summary TEXT,
    duration_minutes INTEGER,
    levels TEXT[],                             -- ['beginner', 'intermediate', 'advanced']
    roles TEXT[],                              -- ['developer', 'administrator', ...]
    products TEXT[],                           -- ['azure', 'azure-ai', ...]
    subjects TEXT[],
    icon_url TEXT,
    popularity FLOAT,
    locale VARCHAR(20) DEFAULT 'en-us',
    last_modified TIMESTAMP,                  -- From MS Learn API
    first_seen TIMESTAMP DEFAULT NOW(),       -- When we first discovered it
    last_seen TIMESTAMP DEFAULT NOW(),        -- Last time it appeared in catalog
    is_new BOOLEAN DEFAULT TRUE,              -- New since last digest cycle
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Content details (scraped rich content)
CREATE TABLE content_details (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id UUID REFERENCES content(id) ON DELETE CASCADE,
    learning_objectives TEXT[],
    prerequisites TEXT[],
    unit_titles TEXT[],
    scraped_summary TEXT,
    raw_text TEXT,                             -- Truncated extracted text
    scrape_status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'completed', 'failed'
    scraped_at TIMESTAMP,
    UNIQUE(content_id)
);

-- Content AI enrichment (generated once, stored permanently)
CREATE TABLE content_ai (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id UUID REFERENCES content(id) ON DELETE CASCADE,
    classified_topics TEXT[],                  -- AI-detected topics
    audience TEXT[],                           -- ['Developer', 'AI Engineer', ...]
    difficulty VARCHAR(50),                    -- 'Beginner', 'Intermediate', 'Advanced'
    why_it_matters TEXT,
    key_takeaways TEXT[],
    recommended_audience TEXT,
    newsletter_summary TEXT,
    ai_model VARCHAR(100),
    processed_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(content_id)
);

-- Content-to-topic mapping (after AI classification)
CREATE TABLE content_topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id UUID REFERENCES content(id) ON DELETE CASCADE,
    topic_id UUID REFERENCES topics(id) ON DELETE CASCADE,
    confidence FLOAT DEFAULT 1.0,
    UNIQUE(content_id, topic_id)
);

-- Digests (generated newsletters)
CREATE TABLE digests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    digest_type VARCHAR(50) NOT NULL,         -- 'individual', 'team'
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    team_id UUID REFERENCES teams(id) ON DELETE SET NULL,
    newsletter_id UUID REFERENCES team_newsletters(id) ON DELETE SET NULL,
    content_html TEXT NOT NULL,                -- Rendered HTML
    content_json JSONB,                       -- Structured digest data
    topic_names TEXT[],
    period_start TIMESTAMP,
    period_end TIMESTAMP,
    sent_at TIMESTAMP,
    status VARCHAR(50) DEFAULT 'generated',   -- 'generated', 'sent', 'failed'
    recipient_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Digest items (content included in each digest)
CREATE TABLE digest_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    digest_id UUID REFERENCES digests(id) ON DELETE CASCADE,
    content_id UUID REFERENCES content(id) ON DELETE SET NULL,
    position INTEGER,                         -- Order in digest
    section VARCHAR(100),                     -- 'new_modules', 'updated_paths', 'trending'
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Milestone Breakdown

### Milestone 1: Project Scaffolding & Infrastructure

**Backend:**
- Initialize FastAPI project with proper directory structure
- Configure SQLAlchemy with PostgreSQL async support
- Set up Alembic for migrations
- Create `.env` loading via `pydantic-settings`
- Configure structured logging
- Create Docker + docker-compose setup (FastAPI + PostgreSQL)

**Frontend:**
- Scaffold Vite + React project with `create-vite`
- Install dependencies: React Router, Tailwind CSS v3, Axios
- Set up project structure (pages, components, hooks, services, context)
- Configure Vite proxy to backend

**Deliverables:** Both services start, connect to PostgreSQL, and a health check endpoint responds.

---

### Milestone 2: Database Models, Auth & Core API

**Backend:**
- Create all SQLAlchemy models (12 tables as designed above)
- Generate initial Alembic migration
- Implement Google OAuth flow:
  - Frontend redirects to Google consent
  - Backend receives auth code → exchanges for tokens → extracts user info
  - Create/update user in DB, return JWT
- Implement JWT middleware for route protection
- Create core API endpoints:
  - `POST /auth/google` — exchange Google auth code for JWT
  - `GET /users/me` — get current user profile + preferences
  - `GET /topics` — list all system topics
  - `POST /topics/subscribe` — subscribe to selected topics + set preferences

**Frontend:**
- Implement Google Login button (using `@react-oauth/google`)
- Create `AuthContext` with JWT storage
- Build protected route wrapper
- Create Onboarding page (topic selection + frequency + delivery time)

**Deliverables:** Users can sign in with Google, select topics, and configure newsletter preferences.

---

### Milestone 3: Content Ingestion Pipeline

**Backend:**
- Build `CatalogClient` to fetch from `https://learn.microsoft.com/api/catalog/`
  - Fetch modules, learningPaths, certifications, exams, appliedSkills
  - Use `last_modified` parameter for incremental sync
- Build sync logic:
  - Compare fetched content UIDs against local DB
  - Insert new content, update changed content
  - Mark `is_new = True` for content not seen before
  - Update `last_seen` for all matched content
- Build `ContentScraper` to extract rich details from MS Learn URLs:
  - Use `httpx` to fetch page content
  - Parse with `BeautifulSoup` to extract:
    - Learning objectives
    - Prerequisites
    - Module unit titles
  - Store in `content_details` table
  - Truncate raw text to ~1000 words
- Set up APScheduler:
  - `catalog_sync` job — runs daily at 02:00 UTC
  - `content_enrichment` job — runs hourly, processes pending items in batches

**Deliverables:** Database populates with real MS Learn content. Scraper extracts structured details.

---

### Milestone 4: AI Enrichment via Groq

**Backend:**
- Build `GroqClient` wrapper:
  - Initialize with `GROQ_API_KEY`
  - Use model: `llama-3.3-70b-versatile`
  - Implement retry logic with exponential backoff
- Build AI processing pipeline for each content item:
  - **Input:** Structured payload (title, summary, objectives, units) — max 1000 words
  - **Output (single prompt, JSON response):**
    - `classified_topics`: Array of topic labels
    - `audience`: Array of role labels
    - `difficulty`: Beginner/Intermediate/Advanced
    - `why_it_matters`: 2-3 sentence summary
    - `key_takeaways`: Array of 3-5 bullet points
    - `recommended_audience`: One-line description
    - `newsletter_summary`: Paragraph for newsletter inclusion
  - Store results in `content_ai` table
  - Map classified topics to `content_topics` join table
- Implement token optimization:
  - Pre-process content to structured format before sending
  - Never send raw HTML/full pages
  - Cache results permanently — never re-process same content

**System Topics → Catalog Mapping:**

| System Topic | MS Learn Products/Subjects |
|---|---|
| Azure | `azure` |
| Azure AI | `azure-ai-services`, `azure-openai`, `azure-machine-learning` |
| Azure AI Foundry | `microsoft-foundry`, `foundry-tools` |
| Fabric | `fabric` |
| Copilot | `microsoft-365-copilot`, `copilot` |
| Security | `security`, `cloud-security` |
| Entra ID | `entra-id`, `identity-access` |
| Power Platform | `power-platform`, `power-apps`, `power-automate`, `power-bi` |
| DevOps | `azure-devops`, `github`, `devops` |
| AKS | `azure-kubernetes-service` |
| Data Engineering | `data-engineering` |

**Deliverables:** AI enriches all ingested content with topic classification, audience, difficulty, and newsletter summaries.

---

### Milestone 5: Newsletter Generation & Email Delivery

**Backend:**
- Build newsletter generation service:
  - **Individual digest flow:**
    1. Query user subscriptions → get topic IDs
    2. Find content matching those topics where `is_new = True` or updated since last digest
    3. Group by section (New Modules, Updated Learning Paths)
    4. Include: Executive Summary, Topic Sections, Weekly Trends, Recommended Path
    5. Use Groq to generate executive summary for the digest
    6. Render HTML email template
    7. Store in `digests` table with `content_json` and `content_html`
  - **Team digest flow:**
    1. Get newsletter config → topics
    2. Generate single digest (same as individual but for team topics)
    3. Deliver to all team members
- Build HTML email templates:
  - Professional, responsive email design
  - Sections: Executive Summary → Topic Items → Trends → Recommendations → Links
  - Each item: Title, Why It Matters, Key Takeaways, Audience, Difficulty, MS Learn Link
- Build SMTP email client:
  - Configure with `SMTP_SERVER`, `SMTP_PORT`, `SMTP_EMAIL`, `SMTP_PASSWORD`
  - Send from `mslearndigest@gmail.com` (or configured sender)
  - Support HTML emails with proper MIME formatting
- Set up digest scheduler:
  - Check all user preferences and team newsletters
  - Generate digests at configured times
  - Mark `is_new = False` on content after inclusion in digests
- API endpoints:
  - `POST /newsletters` — create team newsletter config
  - `GET /newsletters` — list newsletters for admin's teams
  - `GET /digests` — list digest history for current user
  - `GET /digests/{id}` — get full digest content

**Deliverables:** Newsletters generated and delivered via email on schedule. Digest history stored.

---

### Milestone 6: React Frontend (Premium UI)

**Design System:**
- Dark mode with glass morphism
- Color palette: Deep navy (#0a0f1e), electric blue (#3b82f6), violet accents (#8b5cf6), emerald (#10b981)
- Font: Inter from Google Fonts
- Smooth transitions, micro-animations, gradient borders
- Responsive design (mobile → desktop)

**Pages:**

1. **Landing Page** — Hero section with animated gradient, feature cards, Google Login CTA
2. **Onboarding** — Multi-step wizard: Topic grid → Frequency selector → Time picker → Confirmation
3. **Dashboard** — Subscription overview, next digest countdown, recent stats, quick actions
4. **Digest History** — Filterable list of past newsletters with search
5. **Digest View** — Full rendered newsletter in a reader-friendly format
6. **Team Management** — Create teams, invite members (email), configure team newsletters
7. **Admin Dashboard** — Team overview, newsletter configs, member management

**Components:**
- `Navbar` — Responsive nav with user avatar dropdown
- `TopicSelector` — Interactive topic grid with selection state
- `DigestCard` — Preview card for digest history
- `TeamCard` — Team overview with member count
- `StatsCard` — Animated statistics display
- `FrequencyPicker` — Visual frequency selection
- `TimePicker` — Custom time picker
- `Modal` — Reusable modal with backdrop blur
- `Button`, `Badge`, `Input`, `Select` — Design system primitives

---

## Open Questions

> [!IMPORTANT]
> **PostgreSQL Setup**: The plan uses Docker to run PostgreSQL. Confirm you want to use Docker for both the database and the backend, or do you have an existing PostgreSQL instance?

> [!IMPORTANT]
> **Google OAuth Redirect URI**: For local development, I'll configure `http://localhost:5173` as the frontend origin and `http://localhost:8000/auth/google/callback` as the redirect. The Google Cloud Console project (Client ID in your `.env`) must have these URIs registered. Should I proceed with these defaults?

> [!IMPORTANT]
> **TailwindCSS Version**: Your tech stack specifies Tailwind CSS. Should I use **Tailwind v3** (stable, utility-first) or **Tailwind v4** (latest, CSS-first)? I'll default to **v3** unless you say otherwise.

---

## Verification Plan

### Automated Tests
- Backend: Run `pytest` for API endpoints (auth flow, CRUD operations, content sync)
- Database: Verify migrations apply cleanly with `alembic upgrade head`
- Frontend: Run `npm run build` to verify no compilation errors

### Manual Verification
- Google OAuth: Complete sign-in flow end-to-end
- Content Sync: Trigger manual sync and verify content appears in DB
- AI Enrichment: Verify Groq processes content and stores results
- Email: Send test newsletter and verify delivery
- Full Flow: Sign up → Select Topics → Trigger Digest → Receive Email → View History

### Docker Validation
- `docker-compose up` starts all services
- Frontend accessible at `http://localhost:5173`
- Backend accessible at `http://localhost:8000`
- Database accessible internally at `postgres:5432`

---

## Execution Order

| Phase | Milestone | Est. Files |
|-------|-----------|-----------|
| 1 | Project Scaffolding & Docker | ~15 |
| 2 | Database Models, Auth & Core API | ~25 |
| 3 | Content Ingestion Pipeline | ~8 |
| 4 | AI Enrichment via Groq | ~5 |
| 5 | Newsletter Generation & Email | ~10 |
| 6 | React Frontend (All Pages) | ~35 |

**Total estimated files: ~98**

I will build this incrementally, milestone by milestone, ensuring each phase works before proceeding.
