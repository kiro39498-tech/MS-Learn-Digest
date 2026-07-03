<div align="center">

# 📘 MS Learn Digest

### AI-Powered Personalized Microsoft Learn Newsletter Platform

[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Groq](https://img.shields.io/badge/Groq-Llama_3.3_70B-F55036?logo=groq&logoColor=white)](https://groq.com/)
[![OAuth](https://img.shields.io/badge/Google-OAuth_2.0-4285F4?logo=google&logoColor=white)](https://developers.google.com/identity)
[![TailwindCSS](https://img.shields.io/badge/Tailwind-CSS-06B6D4?logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

**MS Learn Digest** is a full-stack, production-grade newsletter platform that keeps developers up to date with the latest Microsoft Learn content — automatically, intelligently, and at their own pace.

[Features](#-features) · [Tech Stack](#-tech-stack) · [Architecture](#-architecture) · [Getting Started](#-getting-started) · [API Docs](#-api-documentation) · [Contributing](#-contributing)

</div>

---

## 📖 Overview

MS Learn Digest connects to the Microsoft Learn catalog and uses the **Groq LLM (Llama 3.3 70B)** to generate concise, personalized summaries of newly updated learning modules. Users sign in with Google or a magic-link email, choose the technologies they care about, set a delivery frequency, and receive beautifully formatted newsletters straight to their inbox — no setup overhead required.

Beyond newsletters, the platform offers **structured Learning Tracks**: multi-phase, AI-generated daily lessons that teach a technology progressively, complete with curated reference links discovered via DuckDuckGo search.

**Team Newsletters** let organization admins create a shared newsletter, invite teammates via email, and manage topics and schedules for the whole group.

> The platform intentionally avoids persisting thousands of MS Learn modules. It fetches only the updates relevant to each run, keeping the database lean and the scheduler fast.

---

## ✨ Features

### 🔐 Authentication
- **Google OAuth 2.0** — one-click sign-in
- **Email Magic-Link** — passwordless login with rate limiting and expiry
- JWT-based session management (72-hour expiry, configurable)

### 🎯 Personalized Newsletters
- Browse and subscribe to Microsoft technology topics (hierarchical tree)
- Choose delivery frequency: **Daily · Weekly · Bi-weekly · Monthly**
- Set preferred delivery time (IST timezone)
- AI-generated digest emails using **Llama 3.3 70B Versatile** on Groq

### 📚 Learning Tracks
- Subscribe to structured learning paths for any technology
- **AI-generated daily lessons** with context-aware explanations
- Progressive multi-phase curriculum (Foundation → Intermediate → Advanced)
- Curated reference links auto-discovered via DuckDuckGo
- Track progress and view completed lessons

### 👥 Team Newsletters
- Create a team and associate it with a shared newsletter
- Invite members via email with tokenized invitations (72-hour expiry)
- Accept / decline invitations through a public token URL
- Admins manage topics, schedule, and membership
- Team digest history with per-delivery status

### ⏰ Automated Scheduler
- **APScheduler AsyncIOScheduler** runs entirely in-process
- Dispatches individual and team digests on each user's chosen frequency
- Daily catalog sync at a configurable UTC hour (default 2 AM)
- Fetches only newly updated MS Learn content — no full re-scans

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18, Vite, Tailwind CSS, Axios |
| **Backend** | FastAPI 0.115, Uvicorn, Python 3.11+ |
| **Database** | PostgreSQL 16, SQLAlchemy 2.0, Alembic |
| **Validation** | Pydantic v2, pydantic-settings |
| **Auth** | Google OAuth 2.0, JWT (python-jose), Magic-Link |
| **AI / LLM** | Groq SDK, Llama 3.3 70B Versatile |
| **Scheduler** | APScheduler 3.10 (AsyncIOScheduler) |
| **Email** | Gmail SMTP via Jinja2 HTML templates |
| **Web Scraping** | BeautifulSoup4, lxml, DuckDuckGo Search |
| **Containerization** | Docker, Docker Compose v3.9 |


---

## 🏗 Architecture

```mermaid
flowchart TD
    A["👤 User Browser\n(React + Vite)"] -->|HTTPS / REST| B["⚡ FastAPI Backend\n(Uvicorn)"]
    B --> C["🔐 Auth Service\n(Google OAuth / Magic-Link)"]
    B --> D["🗄 PostgreSQL\n(SQLAlchemy + Alembic)"]
    B --> E["⏰ APScheduler\n(AsyncIOScheduler)"]
    E --> F["🌐 MS Learn Catalog API\nhttps://learn.microsoft.com/api/catalog/"]
    E --> G["🤖 Groq LLM\nLlama 3.3 70B Versatile"]
    G --> H["📧 Gmail SMTP\nJinja2 HTML Templates"]
    H --> I["📬 User / Team Inbox"]
    F --> D
    C --> D
```

### Layer Responsibilities

| Layer | Responsibility |
|---|---|
| **Frontend (React/Vite)** | SPA with pages for landing, onboarding, dashboard, preferences, teams, learning center, and digest history. Communicates with the backend via a centralized Axios client with JWT bearer token injection and auto-logout on 401. |
| **Backend (FastAPI)** | RESTful API with 8 route modules. Handles auth, user preferences, topic management, digest history, team management, invitations, learning track subscriptions, and admin diagnostics. |
| **Database (PostgreSQL)** | Persistent store for users, topics, preferences, teams, invitations, digests, learning tracks, lessons, and the MS Learn catalog cache. Migrations managed by Alembic. |
| **AI Layer (Groq)** | On each scheduler run, the digest generator sends batched module descriptions to Groq (Llama 3.3 70B) to produce reader-friendly HTML summaries and lesson content. |
| **Scheduler (APScheduler)** | Runs inside the FastAPI process. Fires per-user and per-team digest jobs, the daily catalog sync job, and the learning lesson delivery job. |
| **External APIs** | Microsoft Learn Catalog API (module metadata), Google OAuth 2.0 (authentication), DuckDuckGo Search (lesson reference link discovery). |

---

## 🔄 End-to-End Workflow

```mermaid
sequenceDiagram
    participant U as User
    participant FE as React Frontend
    participant BE as FastAPI Backend
    participant DB as PostgreSQL
    participant MS as MS Learn Catalog
    participant AI as Groq LLM
    participant EM as Gmail SMTP

    U->>FE: Sign in (Google / Magic-Link)
    FE->>BE: POST /api/auth/google or /api/auth/email/*
    BE->>DB: Upsert user record
    BE-->>FE: JWT token

    U->>FE: Select topics & frequency
    FE->>BE: POST /api/topics/onboard + PUT /api/users/me/preferences
    BE->>DB: Store subscriptions & preferences

    Note over BE: Scheduler fires at user's chosen time
    BE->>MS: Fetch catalog updates (since last run)
    MS-->>DB: Cache new/updated modules
    BE->>DB: Query modules matching user topics
    BE->>AI: Summarize modules (Llama 3.3 70B)
    AI-->>BE: AI-generated HTML digest
    BE->>EM: Send personalized newsletter
    EM-->>U: 📬 Inbox
```

---

## 📁 Project Structure

```
MS-Learn-Digest/
├── .env                          # Environment variables (not committed)
├── .env.example                  # Template for environment setup
├── .gitignore
├── docker-compose.yml            # Multi-service container orchestration
│
├── backend/
│   ├── Dockerfile
│   ├── alembic.ini               # Alembic migration config
│   ├── requirements.txt
│   ├── alembic/
│   │   ├── env.py                # Migration environment
│   │   └── versions/             # Incremental schema migration scripts
│   │       ├── 28e549d24050_initial_schema.py
│   │       ├── a1b2c3d4e5f6_add_content_changes.py
│   │       ├── b2c3d4e5f6a7_catalog_cache_refactor.py
│   │       ├── c3d4e5f6a7b8_team_invitations.py
│   │       ├── d4e5f6a7b8c9_team_one_newsletter.py
│   │       ├── e5f6a7b8c9d0_hierarchical_topics.py
│   │       ├── f6a7b8c9d0e1_learning_tracks.py
│   │       ├── g7h8i9j0k1l2_learning_enhancement.py
│   │       └── h8i9j0k1l2m3_email_auth_phase_learning.py
│   └── app/
│       ├── main.py               # FastAPI app entry point, CORS, lifespan
│       ├── api/                  # Route handlers (one file per domain)
│       │   ├── auth.py           # Google OAuth + magic-link endpoints
│       │   ├── users.py          # User profile & preferences
│       │   ├── topics.py         # Topic tree, subscribe, onboard
│       │   ├── teams.py          # Team CRUD, members, invitations
│       │   ├── newsletters.py    # Newsletter config
│       │   ├── digests.py        # Digest history
│       │   ├── learning.py       # Learning tracks & progress
│       │   └── admin.py          # Admin diagnostics & testing
│       ├── core/
│       │   ├── config.py         # Pydantic settings (loads .env)
│       │   ├── database.py       # SQLAlchemy engine & session factory
│       │   ├── scheduler.py      # APScheduler setup & job registration
│       │   ├── security.py       # JWT encode/decode helpers
│       │   └── logging.py        # Structured JSON logging config
│       ├── models/               # SQLAlchemy ORM table definitions
│       ├── schemas/              # Pydantic request/response schemas
│       ├── repositories/         # Database access layer (query logic)
│       ├── services/
│       │   ├── auth_service.py   # Google token exchange, user upsert
│       │   ├── email_auth_service.py  # Magic-link generation & verification
│       │   ├── ai/               # Groq client wrapper
│       │   ├── digest/           # Digest content generation pipeline
│       │   ├── email/            # SMTP send helpers
│       │   ├── ingestion/        # MS Learn catalog fetch & cache sync
│       │   └── learning/         # Lesson generation & delivery
│       └── templates/            # Jinja2 HTML email templates
│
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── vite.config.js            # Vite config with API proxy
    └── src/
        ├── main.jsx              # React entry point
        ├── App.jsx               # Router & auth guard
        ├── services/
        │   └── api.js            # Centralized Axios client + all API calls
        ├── context/              # React Context providers (Auth, etc.)
        ├── components/           # Reusable UI components
        ├── pages/
        │   ├── LandingPage.jsx   # Public landing & sign-in
        │   ├── AuthCallback.jsx  # Google OAuth redirect handler
        │   ├── EmailAuthCallback.jsx  # Magic-link redirect handler
        │   ├── Onboarding.jsx    # First-run topic selection
        │   ├── Dashboard.jsx     # Main user dashboard
        │   ├── Preferences.jsx   # Frequency, time & topic settings
        │   ├── DigestDetail.jsx  # Full digest viewer
        │   ├── Teams.jsx         # Team management UI
        │   ├── TeamInvite.jsx    # Public invitation accept/decline page
        │   ├── LearningCenter.jsx # Learning track browser & progress
        │   └── AdminTesting.jsx  # Admin diagnostics panel
        └── assets/               # Static images & icons
```


---

## 🗄 Database Design

| Table | Purpose |
|---|---|
| `users` | Stores user profile, email, Google sub, and onboarding status |
| `topics` | Hierarchical Microsoft technology topics (parent/child tree) |
| `user_topic_subscriptions` | Many-to-many: which topics a user follows |
| `user_preferences` | Delivery frequency, preferred time, timezone per user |
| `catalog_cache` | Cached MS Learn modules (uid, title, summary, updated\_at, topic slugs) |
| `digests` | Generated newsletter records linked to a user |
| `teams` | Team records with name, admin, and creation metadata |
| `team_members` | Team membership with status (pending / active) |
| `team_invitations` | Secure tokenized invitations with expiry and status |
| `team_newsletters` | One newsletter config per team (topics, frequency, schedule) |
| `learning_topics` | Available learning track definitions (phases, modules) |
| `learning_subscriptions` | User subscriptions to learning tracks with phase selection |
| `generated_lessons` | Cached AI-generated lesson content per module |
| `learning_delivery_log` | History of lesson deliveries per user/track |
| `email_login_tokens` | Magic-link tokens (single-use, expiring) |
| `auth_providers` | Linked OAuth providers per user account |

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** and npm
- **PostgreSQL 16** (local) or use Docker Compose
- A **Google Cloud** project with OAuth 2.0 credentials
- A **Groq API** key — [console.groq.com](https://console.groq.com)
- A **Gmail App Password** for SMTP delivery

---

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/MS-Learn-Digest.git
cd MS-Learn-Digest
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Open `.env` and fill in your values (see the [Environment Variables](#-environment-variables) table below).

### 3. Backend Setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 4. Frontend Setup

```bash
cd frontend
npm install
```

### 5. Database — Run Migrations

Make sure PostgreSQL is running and `DATABASE_URL` in `.env` is correct, then:

```bash
cd backend
alembic upgrade head
```

### 6. Start the Backend

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API is now available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

### 7. Start the Frontend

```bash
cd frontend
npm run dev
```

The app is now available at `http://localhost:5173`.

### 8. Seed Learning Topics (Optional)

After signing in, visit the **Admin** panel or call:

```bash
curl -X POST http://localhost:8000/api/learning/seed \
  -H "Authorization: Bearer <your-jwt>"
```

---

### 🐳 Docker Setup (Recommended)

Run the entire stack — database, backend, and frontend — with a single command:

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |

To stop and remove containers:

```bash
docker compose down
```

To also remove the database volume:

```bash
docker compose down -v
```

> **Note:** The `backend` container mounts `./backend` as a volume and runs with `--reload`, so code changes apply instantly in development.

---

## 🔑 Environment Variables

| Variable | Required | Description | Example |
|---|---|---|---|
| `DATABASE_URL` | ✅ | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/mslearndigest` |
| `SECRET_KEY` / `JWT_SECRET_KEY` | ✅ | Secret for JWT signing — change in production | `a-long-random-string` |
| `JWT_ALGORITHM` | ✅ | JWT signing algorithm | `HS256` |
| `JWT_EXPIRATION_HOURS` | ✅ | JWT validity window | `72` |
| `GOOGLE_CLIENT_ID` | ✅ | Google OAuth 2.0 client ID | `123456.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | ✅ | Google OAuth 2.0 client secret | `GOCSPX-...` |
| `GOOGLE_REDIRECT_URI` | ✅ | OAuth callback URL | `http://localhost:8000/auth/google/callback` |
| `GROQ_API_KEY` | ✅ | Groq API key for LLM access | `gsk_...` |
| `GROQ_MODEL` | ✅ | Groq model identifier | `llama-3.3-70b-versatile` |
| `SMTP_SERVER` | ✅ | SMTP server hostname | `smtp.gmail.com` |
| `SMTP_PORT` | ✅ | SMTP port | `587` |
| `SMTP_EMAIL` | ✅ | Sender Gmail address | `digest@gmail.com` |
| `SMTP_PASSWORD` | ✅ | Gmail App Password | `abcd efgh ijkl mnop` |
| `FRONTEND_URL` | ✅ | Frontend base URL (CORS allow-list) | `http://localhost:5173` |
| `APP_ENV` | ✅ | Runtime environment | `development` or `production` |
| `LOG_LEVEL` | ✅ | Log verbosity | `INFO` |
| `CATALOG_SYNC_HOUR` | ⚙️ | UTC hour to run catalog sync | `2` |
| `INVITATION_EXPIRY_HOURS` | ⚙️ | Team invite token lifetime | `72` |
| `EMAIL_LOGIN_TOKEN_EXPIRY_MINUTES` | ⚙️ | Magic-link expiry | `15` |
| `EMAIL_LOGIN_MAX_ATTEMPTS_PER_HOUR` | ⚙️ | Magic-link rate limit | `5` |
| `VITE_GOOGLE_CLIENT_ID` | ✅ | Google client ID exposed to Vite | same as `GOOGLE_CLIENT_ID` |
| `VITE_API_URL` | ✅ | Backend base URL for Axios | `http://localhost:8000` |

> ⚠️ Never commit your `.env` file. It is already listed in `.gitignore`.


---

## 📡 API Documentation

Full interactive docs are available at `/docs` (Swagger UI) and `/redoc` when the backend is running.

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/google` | Exchange Google OAuth code for JWT |
| `POST` | `/api/auth/email/request` | Send magic-link login email |
| `POST` | `/api/auth/email/verify` | Verify magic-link token → JWT |
| `GET` | `/api/auth/providers` | List available auth providers |

### Users

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/users/me` | Get authenticated user profile |
| `PUT` | `/api/users/me/preferences` | Update frequency, time, and timezone |

### Topics

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/topics/` | List all topics |
| `GET` | `/api/topics/tree` | Get full topic hierarchy tree |
| `GET` | `/api/topics/roots` | Get root-level topics only |
| `GET` | `/api/topics/my` | Get user's subscribed topics |
| `POST` | `/api/topics/subscribe` | Subscribe to a list of topic IDs |
| `POST` | `/api/topics/onboard` | Complete onboarding with initial topics |

### Digests

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/digests/` | List all digests for current user |
| `GET` | `/api/digests/{digest_id}` | Get a specific digest by ID |

### Teams

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/teams/` | List teams the user belongs to |
| `POST` | `/api/teams/` | Create a new team + newsletter |
| `GET` | `/api/teams/{team_id}` | Get team details |
| `PATCH` | `/api/teams/{team_id}` | Update team name |
| `DELETE` | `/api/teams/{team_id}` | Delete a team |
| `GET` | `/api/teams/{team_id}/newsletter` | Get team newsletter config |
| `PATCH` | `/api/teams/{team_id}/newsletter/topics` | Update team newsletter topics |
| `PATCH` | `/api/teams/{team_id}/newsletter/schedule` | Update team delivery schedule |
| `PATCH` | `/api/teams/{team_id}/newsletter/toggle` | Enable / disable team newsletter |
| `POST` | `/api/teams/{team_id}/invite` | Invite a member by email |
| `POST` | `/api/teams/{team_id}/members/{member_id}/resend` | Resend invitation email |
| `DELETE` | `/api/teams/{team_id}/members/{member_id}` | Remove a team member |
| `GET` | `/api/teams/{team_id}/digests` | Get team digest history |
| `GET` | `/api/teams/invite/{token}` | Preview invitation details (public) |
| `POST` | `/api/teams/invite/{token}/accept` | Accept a team invitation |
| `POST` | `/api/teams/invite/{token}/decline` | Decline a team invitation |

### Learning Tracks

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/learning/topics` | List all available learning topics |
| `GET` | `/api/learning/topics/{topic_id}` | Get topic details |
| `GET` | `/api/learning/topics/{topic_id}/modules` | Get modules for a topic |
| `GET` | `/api/learning/topics/{topic_id}/phases` | Get learning phases for a topic |
| `GET` | `/api/learning/my` | Get user's active learning tracks |
| `POST` | `/api/learning/subscribe` | Subscribe to a learning track |
| `DELETE` | `/api/learning/subscribe/{topic_id}` | Unsubscribe from a track |
| `PATCH` | `/api/learning/subscribe/{topic_id}/frequency` | Update lesson frequency |
| `PATCH` | `/api/learning/subscribe/{topic_id}/phases` | Update selected phases |
| `GET` | `/api/learning/progress/{topic_id}` | Get progress for a track |
| `GET` | `/api/learning/completed` | Get completed tracks |
| `GET` | `/api/learning/analytics` | Get learning analytics |
| `GET` | `/api/learning/status` | Get overall learning status |
| `POST` | `/api/learning/seed` | Seed default learning topics |

### Admin (Development / Diagnostics)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/admin/config` | View current app config |
| `GET` | `/api/admin/smtp-check` | Test SMTP connection |
| `POST` | `/api/admin/send-test-email` | Send a test email |
| `POST` | `/api/admin/generate-test-digest` | Generate a test digest (no send) |
| `POST` | `/api/admin/send-test-digest` | Generate and send a test digest |
| `GET` | `/api/admin/preview-digest` | Preview digest HTML in browser |
| `POST` | `/api/admin/catalog-sync` | Trigger manual catalog sync |
| `GET` | `/api/admin/catalog-cache/stats` | View catalog cache statistics |
| `POST` | `/api/admin/catalog-cache/preview` | Preview filtered catalog results |
| `POST` | `/api/admin/test/send-my-digest` | Send digest to current admin user |
| `POST` | `/api/admin/learning/send-lesson` | Send learning lesson (test) |
| `DELETE` | `/api/admin/learning/lesson-cache` | Clear generated lesson cache |

> **Admin endpoints** are disabled in production by setting `ADMIN_ENABLED=False` in your `.env`.

---

## 🗂 Folder Explanation

### Backend — `backend/app/`

| Folder / File | Responsibility |
|---|---|
| `main.py` | FastAPI app factory, CORS middleware, lifespan hooks, health endpoint |
| `api/` | One route module per domain. Each file contains all endpoints for that resource. |
| `core/config.py` | Single source of truth for all environment variables via pydantic-settings |
| `core/database.py` | SQLAlchemy engine, `SessionLocal` factory, `get_db` dependency |
| `core/scheduler.py` | APScheduler setup — registers all recurring jobs on app startup |
| `core/security.py` | JWT creation and verification helpers |
| `core/logging.py` | Structured JSON logging configuration |
| `models/` | SQLAlchemy ORM class definitions mapping to PostgreSQL tables |
| `schemas/` | Pydantic v2 models for request validation and response serialization |
| `repositories/` | Thin data-access layer — all raw DB queries live here |
| `services/auth_service.py` | Google token exchange, user upsert, JWT issuance |
| `services/email_auth_service.py` | Magic-link token creation, email dispatch, verification |
| `services/ai/` | Groq SDK client wrapper and prompt engineering helpers |
| `services/digest/` | End-to-end digest generation pipeline (fetch → summarize → template) |
| `services/email/` | SMTP connection management and send helpers |
| `services/ingestion/` | MS Learn Catalog API client and catalog cache sync logic |
| `services/learning/` | AI lesson generation, phase management, delivery orchestration |
| `templates/` | Jinja2 HTML email templates for digests, lessons, and invitations |

### Frontend — `frontend/src/`

| Folder / File | Responsibility |
|---|---|
| `main.jsx` | React 18 root mount with router and context providers |
| `App.jsx` | Top-level route definitions and auth guard |
| `services/api.js` | Centralized Axios instance with JWT injection, auto-logout, and every API call |
| `context/` | React Context providers — AuthContext and any shared state |
| `components/` | Reusable UI components (navbar, topic selector, digest card, etc.) |
| `pages/LandingPage.jsx` | Public marketing / sign-in page |
| `pages/AuthCallback.jsx` | Handles Google OAuth redirect and token storage |
| `pages/EmailAuthCallback.jsx` | Handles magic-link redirect and token storage |
| `pages/Onboarding.jsx` | First-run topic selection wizard |
| `pages/Dashboard.jsx` | Authenticated home — digest feed, quick stats |
| `pages/Preferences.jsx` | Topic subscriptions, frequency, and delivery time settings |
| `pages/DigestDetail.jsx` | Full-page digest viewer with HTML content |
| `pages/Teams.jsx` | Team list, creation, member management, newsletter config |
| `pages/TeamInvite.jsx` | Public page for accepting / declining a team invitation |
| `pages/LearningCenter.jsx` | Learning track browser, subscriptions, progress tracking |
| `pages/AdminTesting.jsx` | Developer panel for SMTP tests, catalog sync, digest previews |
| `assets/` | Static images, logos, and icons |


---

## 🔒 Security

### Authentication & Authorization
- **Google OAuth 2.0** — No passwords stored for Google sign-in users
- **Magic-Link Email Auth** — Single-use, time-limited tokens (15-minute expiry) with per-address rate limiting (5 requests/hour)
- **JWT Sessions** — HS256-signed tokens with configurable expiry (default 72 hours). Stored client-side in `localStorage`; auto-cleared on 401

### API Security
- **CORS** — Strict allow-list via `FRONTEND_URL` environment variable; no wildcard origins in production
- **Input Validation** — Every request body validated by Pydantic v2 with custom field validators (e.g., regex email validation, token length checks)
- **SQL Injection Prevention** — All database queries use SQLAlchemy ORM parameterized statements; no raw string interpolation in queries
- **Team Authorization** — Admin-only operations (invite, update schedule, delete team) are gated by membership role checks in repository layer

### Infrastructure
- **Environment Variables** — All secrets loaded from `.env` via pydantic-settings; never hard-coded
- **Admin Endpoints** — `/api/admin/*` routes can be fully disabled in production by setting `ADMIN_ENABLED=False`
- **Invitation Tokens** — Team invitations use cryptographically random tokens with 72-hour expiry and single-use enforcement
- **Docker** — Services run as isolated containers; the database is not exposed beyond localhost in production deployments

---

## ⚡ Performance Optimizations

| Optimization | Details |
|---|---|
| **Incremental catalog sync** | Only newly updated MS Learn modules are fetched and cached — no full re-scan on every run |
| **Scheduler efficiency** | APScheduler runs in-process alongside FastAPI; no separate worker process or message broker needed |
| **Catalog cache (DB)** | `catalog_cache` table stores pre-fetched module data, eliminating repeated external API calls during digest generation |
| **Lesson cache** | Generated AI lessons are stored in `generated_lessons` and reused unless explicitly cleared, saving Groq API quota |
| **Database connection pooling** | SQLAlchemy's built-in connection pool reuses PostgreSQL connections across requests |
| **Database indexing** | Foreign keys and frequently queried columns (user_id, topic slugs, delivery timestamps) are indexed via Alembic migrations |
| **Jinja2 template caching** | Email templates are compiled once at import time and reused for all deliveries in a scheduler run |
| **Axios timeout** | Frontend API client enforces a 60-second request timeout to prevent hanging requests from blocking the UI |

---

## 🖼 Screenshots

> Replace the placeholders below with actual screenshots from your deployment.

### Login / Landing Page
![Login Page](docs/screenshots/login.png)

### Dashboard
![Dashboard](docs/screenshots/dashboard.png)

### Topic Selection (Onboarding)
![Topic Selection](docs/screenshots/topic-selection.png)

### Team Newsletter Management
![Team Newsletter](docs/screenshots/team-newsletter.png)

### Learning Center
![Learning Center](docs/screenshots/learning-center.png)

### Email Digest Preview
![Email Preview](docs/screenshots/email-preview.png)

---

## 🔭 Future Improvements

| Feature | Description |
|---|---|
| 🔷 **Microsoft Teams Integration** | Deliver digests as adaptive cards directly into Teams channels |
| 💬 **Slack Integration** | Post digest summaries to Slack channels via webhooks |
| ☁️ **Azure Deployment** | Terraform / Bicep templates for deploying to Azure App Service + Azure Database for PostgreSQL |
| 📊 **Analytics Dashboard** | Track open rates, click-throughs, topic popularity, and learning completion trends |
| 🌐 **Multi-language Support** | AI-translated digests in the user's preferred language |
| 🤖 **AI Topic Recommendations** | Suggest new topics to subscribe to based on existing preferences and learning history |
| 📱 **Mobile App** | React Native companion app for reading digests and lesson notifications on the go |
| 🔔 **Push Notifications** | Browser push and mobile push notifications for new lesson availability |
| 🗓 **Digest Scheduling UI** | Calendar view for visualizing and adjusting upcoming digest delivery times |
| 🔗 **Microsoft Learn SSO** | Optional sign-in via Microsoft account to pre-populate topic preferences from Learn profile |

---

## 🤝 Contributing

Contributions are welcome. Please follow these steps:

1. **Fork** the repository and create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the existing code style:
   - Python: PEP 8, type hints on all function signatures, docstrings on public methods
   - JavaScript/JSX: ESLint config in the project, functional components with hooks

3. **Test your changes** locally against a real PostgreSQL instance. Run the backend health check:
   ```bash
   curl http://localhost:8000/health
   ```

4. **Commit** with a clear message:
   ```bash
   git commit -m "feat: add push notification support"
   ```

5. **Push** and open a Pull Request against `main`. Fill out the PR template with:
   - What changed and why
   - How to test the change
   - Any breaking changes or migration notes

### Reporting Issues

Please open a GitHub Issue with:
- A clear title and description
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs or screenshots

---

## 📄 License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2025 <Your Name>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

See [LICENSE](./LICENSE) for the full text.

---

## 👤 Author

| | |
|---|---|
| **Name** | Your Name Here |
| **LinkedIn** | [linkedin.com/in/your-profile](https://linkedin.com/in/your-profile) |
| **GitHub** | [github.com/your-username](https://github.com/your-username) |
| **Email** | your-email@example.com |

---

<div align="center">

Built with ❤️ using FastAPI, React, and Groq AI

⭐ If you found this project useful, please consider starring the repository!

</div>
