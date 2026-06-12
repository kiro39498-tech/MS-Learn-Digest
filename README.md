# MS Learn Digest & Team Newsletter Agent

**AI-powered learning intelligence platform that continuously monitors Microsoft Learn content and delivers personalized learning updates to individuals and teams.**

Transform Microsoft Learn from a passive content repository into an active knowledge distribution system. Instead of users manually searching for new content, MS Learn Digest automatically discovers, enriches, and delivers relevant updates at user-defined schedules.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Running Locally](#running-locally)
- [Running with Docker](#running-with-docker)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Background Jobs](#background-jobs)
- [Deployment](#deployment)
- [Testing](#testing)
- [Contributing](#contributing)

---

## Features

### Individual Users
- ✅ **Google OAuth Authentication** — Secure, passwordless login
- 📚 **Topic Subscriptions** — Select from 11 Microsoft technology domains
- ⏰ **Flexible Scheduling** — Daily, weekly, bi-weekly, or monthly digests
- 🧠 **AI-Enriched Content** — Groq-powered summaries and insights
- 📧 **Beautiful HTML Emails** — Production-ready newsletter templates
- 📊 **Digest History** — View and search past newsletters

### Team Admins
- 👥 **Team Management** — Create teams, invite members via email
- 📰 **Shared Newsletters** — Configure topics and schedules for teams
- 📨 **Mass Delivery** — Send identical digests to all team members
- 🔒 **Role-Based Access** — Admin-only configuration controls

### Technical
- 🌐 **Microsoft Learn Catalog Sync** — Daily catalog ingestion
- 🔍 **Web Scraping** — Extract learning objectives, prerequisites, units
- 🤖 **Groq AI Classification** — Auto-tag topics, audience, difficulty
- 📅 **APScheduler Jobs** — Catalog sync, enrichment, digest dispatch
- 🗄️ **PostgreSQL** — Normalized relational database schema
- 🐳 **Docker Compose** — Complete local development environment

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│ Microsoft Learn Catalog API                                      │
└──────────────────────┬───────────────────────────────────────────┘
                       │
                       │ Daily Sync (2 AM UTC)
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│ FastAPI Backend                                                  │
│  ├── Content Repository (PostgreSQL)                             │
│  ├── Web Scraper (BeautifulSoup)                                 │
│  ├── AI Enrichment (Groq LLM)                                    │
│  └── APScheduler Jobs                                            │
└──────────────────────┬───────────────────────────────────────────┘
                       │
                       │ Scheduled Delivery
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│ Digest Generator + Email Client (Gmail SMTP)                    │
└──────────────────────┬───────────────────────────────────────────┘
                       │
                       ├─> Individual Users
                       └─> Team Members
```

---

## Tech Stack

**Frontend:**
- React 19
- Vite 8
- React Router 7
- Tailwind CSS 3.4
- Axios 1.16
- Lucide React icons

**Backend:**
- FastAPI 0.115
- SQLAlchemy 2.0 + Alembic
- PostgreSQL 16
- APScheduler 3.10
- Groq 0.15
- BeautifulSoup4 + lxml
- Jinja2 email templates
- Python-JOSE (JWT)

**Infrastructure:**
- Docker Compose
- Uvicorn ASGI server
- Gmail SMTP

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL 16 (or use Docker)
- Google OAuth credentials ([Get here](https://console.cloud.google.com/))
- Groq API key ([Get here](https://console.groq.com/keys))
- Gmail app password ([Setup guide](https://support.google.com/accounts/answer/185833))

### 1. Clone Repository
```bash
git clone https://github.com/your-username/ms-learn-digest.git
cd ms-learn-digest
```

### 2. Environment Setup
```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Docker Quick Start (Recommended)
```bash
docker-compose up --build
```

**Access:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 4. Manual Setup (No Docker)

**Backend:**
```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
# ── Database ──
DATABASE_URL=postgresql://mslearn:mslearn_secret@localhost:5432/mslearndigest

# ── SMTP (Gmail) ──
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# ── Google OAuth ──
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
VITE_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
FRONTEND_URL=http://localhost:5173

# ── Groq AI ──
GROQ_API_KEY=gsk_your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile

# ── JWT ──
JWT_SECRET_KEY=change-this-to-a-secure-random-string-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=72

# ── Application ──
APP_NAME=MS Learn Digest
APP_ENV=development
LOG_LEVEL=INFO
```

---

## Database Setup

### Automatic (Docker)
Docker Compose automatically provisions PostgreSQL.

### Manual
```bash
# Create database
createdb mslearndigest

# Run migrations
cd backend
alembic upgrade head
```

### Database Schema
- `users` — User profiles
- `user_preferences` — Delivery schedule
- `topics` — System-defined learning topics
- `user_subscriptions` — User → Topic many-to-many
- `teams` — Team entities
- `team_members` — Team membership
- `team_newsletters` — Newsletter configuration
- `newsletter_topics` — Newsletter → Topic many-to-many
- `content` — MS Learn modules/paths
- `content_details` — Scraped web content
- `content_ai` — Groq enrichment results
- `content_topics` — Content → Topic many-to-many
- `digests` — Generated newsletters
- `digest_items` — Digest → Content many-to-many

---

## Running Locally

### Development Mode (Hot Reload)
```bash
# Terminal 1 — Backend
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev
```

### Production Build
```bash
# Backend
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm run build
npm run preview
```

---

## Running with Docker

### Full Stack
```bash
docker-compose up --build
```

### Individual Services
```bash
# Database only
docker-compose up db

# Backend only
docker-compose up backend

# Frontend only
docker-compose up frontend
```

### View Logs
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Stop All
```bash
docker-compose down
```

---

## Project Structure

```
ms-learn-digest/
├── backend/
│   ├── alembic/                  # Database migrations
│   │   └── versions/
│   │       └── 28e549d24050_initial_schema.py
│   ├── app/
│   │   ├── api/                  # FastAPI route handlers
│   │   │   ├── auth.py           # Google OAuth
│   │   │   ├── users.py          # User profile & preferences
│   │   │   ├── topics.py         # Topics & subscriptions
│   │   │   ├── teams.py          # Team management
│   │   │   ├── newsletters.py    # Newsletter configuration
│   │   │   └── digests.py        # Digest history
│   │   ├── core/
│   │   │   ├── config.py         # Environment settings
│   │   │   ├── database.py       # SQLAlchemy setup
│   │   │   ├── security.py       # JWT auth
│   │   │   ├── logging.py        # Structured logging
│   │   │   └── scheduler.py      # APScheduler jobs
│   │   ├── models/               # SQLAlchemy ORM models
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   ├── repositories/         # Data access layer
│   │   ├── services/
│   │   │   ├── ai/               # Groq AI client + enrichment
│   │   │   ├── digest/           # Digest generation
│   │   │   ├── email/            # SMTP client
│   │   │   └── ingestion/        # Catalog sync + scraper
│   │   ├── templates/
│   │   │   └── digest_email.html # Newsletter template
│   │   └── main.py               # FastAPI app entry point
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── assets/
│   │   ├── components/
│   │   │   └── Layout.jsx        # Protected route wrapper
│   │   ├── context/
│   │   │   └── AuthContext.jsx   # Global auth state
│   │   ├── pages/
│   │   │   ├── LandingPage.jsx   # Marketing homepage
│   │   │   ├── AuthCallback.jsx  # OAuth redirect handler
│   │   │   ├── Onboarding.jsx    # First-time user setup
│   │   │   ├── Dashboard.jsx     # User home
│   │   │   ├── Preferences.jsx   # Topics & schedule
│   │   │   ├── Teams.jsx         # Team management
│   │   │   └── DigestDetail.jsx  # View past digest
│   │   ├── services/
│   │   │   └── api.js            # Centralized Axios client
│   │   ├── App.jsx               # React Router
│   │   └── main.jsx
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## API Documentation

### Base URL
- Local: `http://localhost:8000`
- Interactive Docs: `http://localhost:8000/docs`

### Authentication
All protected endpoints require JWT in `Authorization: Bearer <token>` header.

### Endpoints

#### **Auth**
- `POST /api/auth/google` — Exchange Google OAuth code for JWT

#### **User**
- `GET /api/users/me` — Get current user profile
- `PUT /api/users/me/preferences` — Update delivery preferences

#### **Topics**
- `GET /api/topics/` — List all system topics
- `GET /api/topics/my` — Get user's subscribed topics
- `POST /api/topics/subscribe` — Update subscriptions
- `POST /api/topics/onboard` — Complete onboarding

#### **Teams**
- `GET /api/teams/` — List user's teams
- `POST /api/teams/` — Create team
- `GET /api/teams/{id}` — Get team details
- `POST /api/teams/{id}/invite` — Invite member
- `DELETE /api/teams/{id}/members/{memberId}` — Remove member
- `POST /api/teams/{id}/newsletters` — Create newsletter
- `GET /api/teams/{id}/newsletters` — List newsletters

#### **Digests**
- `GET /api/digests/` — List user's digest history
- `GET /api/digests/{id}` — Get full digest content

---

## Background Jobs

### 1. Catalog Sync
**Schedule:** Daily at 2:00 AM UTC  
**Duration:** ~5–15 minutes  
**Function:** Fetch MS Learn Catalog, upsert modules into PostgreSQL

### 2. Content Enrichment
**Schedule:** Every 60 minutes  
**Batch Size:** 20 items  
**Function:** Scrape module pages, run through Groq AI, store results

### 3. Digest Dispatch
**Schedule:** Every 15 minutes  
**Function:** Evaluate all user/newsletter schedules, generate + send due digests

**Example:**
- User preference: Weekly, Monday 8:00 AM
- Job runs at 8:00, 8:15, 8:30, 8:45
- Digest sent during the 8:00–8:15 window

---

## Deployment

### Docker Production Build
```bash
docker-compose -f docker-compose.prod.yml up --build -d
```

### Render / Railway / Fly.io
1. Set environment variables in dashboard
2. Connect GitHub repository
3. Deploy backend + frontend as separate services
4. Provision PostgreSQL database add-on

### Vercel (Frontend Only)
```bash
cd frontend
vercel --prod
```

---

## Testing

### Backend
```bash
cd backend
pytest
```

### Frontend
```bash
cd frontend
npm run test
```

### Manual Testing Checklist
- [ ] Google OAuth login
- [ ] Onboarding flow (topics + schedule)
- [ ] Topic subscription updates
- [ ] Preference updates
- [ ] Team creation
- [ ] Member invitation
- [ ] Newsletter creation
- [ ] Digest history view
- [ ] Digest detail iframe render

---

## Contributing

1. Fork repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## Roadmap

- [ ] Trend analytics (top topics last 30 days)
- [ ] Admin research reports (agentic AI)
- [ ] Additional data sources (Azure Updates, GitHub Docs)
- [ ] Custom topic creation
- [ ] Webhook triggers for instant delivery
- [ ] Slack/Teams integration
- [ ] Advanced filtering (roles, difficulty, duration)
- [ ] AI chatbot for digest Q&A

---

## License

MIT License — see [LICENSE](LICENSE) file for details.

---

## Support

- 📧 Email: support@mslearndigest.com
- 💬 Discord: [Join server](https://discord.gg/mslearndigest)
- 🐛 Issues: [GitHub Issues](https://github.com/your-username/ms-learn-digest/issues)

---

**Built with ❤️ for the Microsoft Learn community.**
