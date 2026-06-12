# MS Learn Digest — Detailed Project Guide

This document is a deep, code-driven explanation of the MS Learn Digest project. It is written for developers, reviewers, and future maintainers who want to understand not only what the app does, but how each layer works and where the important logic lives.

---

## 1. What this project is

MS Learn Digest is an AI-assisted learning update platform built around Microsoft Learn content.

Its goal is simple:
- continuously discover Microsoft Learn modules and learning paths,
- match them to user or team interests,
- enrich them with AI-generated summaries and business value,
- and send polished HTML digest emails on a schedule.

In other words, the application turns Microsoft Learn from a passive catalog into an active, personalized newsletter pipeline.

---

## 2. High-level product behavior

At runtime, the product supports three main user personas:

1. Individual learner
   - signs in with Google OAuth,
   - chooses topics,
   - sets delivery frequency and time,
   - receives personalized digests.

2. Team admin
   - creates a team,
   - picks topics for a shared newsletter,
   - invites teammates by email,
   - sends one shared digest to all accepted members.

3. Admin / maintainer
   - checks SMTP connection,
   - sends test emails,
   - generates preview digests,
   - manually triggers catalog sync,
   - verifies delivery behavior.

---

## 3. Architecture at a glance

The system has three main runtime parts:

- Frontend: React + Vite application for UI and login flow
- Backend: FastAPI service for auth, APIs, scheduling, and digest generation
- Database: PostgreSQL for users, topics, teams, content cache, digests, and invites

The full runtime path is:

1. User signs in through the frontend.
2. Frontend calls FastAPI endpoints with a JWT token.
3. Backend loads or saves user, topic, team, and digest data in PostgreSQL.
4. A background scheduler periodically syncs Microsoft Learn catalog metadata.
5. Another background job checks due users/newsletters and generates digests.
6. The digest engine calls Groq AI to create summaries.
7. The email service sends HTML email via Gmail SMTP.

---

## 4. Repository structure and responsibilities

### Root
- docker-compose.yml
  - starts PostgreSQL, FastAPI backend, and React frontend together.
- implementation_plan.md
  - original implementation plan and technical design notes.
- walkthrough.md
  - summary of the MVP and what was built.
- TESTING.md
  - SMTP and end-to-end testing guide.

### Backend
- backend/app/main.py
  - FastAPI entry point
  - sets up CORS, lifecycle hooks, scheduler startup/shutdown, and health endpoint
- backend/app/api/
  - all route modules
  - auth, users, topics, teams, digests, admin
- backend/app/core/
  - config, database, security, logging, scheduler
- backend/app/models/
  - SQLAlchemy table definitions
- backend/app/repositories/
  - database access logic separated from API handlers
- backend/app/schemas/
  - Pydantic models for request and response validation
- backend/app/services/
  - business logic: auth, AI, digest, email, ingestion
- backend/app/templates/
  - Jinja2 HTML templates used for digest and invitation emails

### Frontend
- frontend/src/pages/
  - LandingPage, AuthCallback, Onboarding, Dashboard, Preferences, Teams, DigestDetail, AdminTesting, TeamInvite
- frontend/src/context/
  - AuthContext for login, token restoration, route redirection
- frontend/src/services/api.js
  - centralized Axios client for all API calls
- frontend/src/components/
  - layout and shared UI wrappers

---

## 5. Core runtime flow

### 5.1 Authentication flow

The authentication flow is centered on Google OAuth plus JWT.

1. The frontend opens the Google sign-in flow.
2. Google returns an authorization code to the callback page.
3. The callback page sends the code to the backend at /api/auth/google.
4. The backend validates the code with Google and returns a signed JWT.
5. The frontend stores the token in localStorage and uses it for protected calls.

Important detail:
- the backend uses JWT for all protected endpoints.
- the frontend restores the token automatically on page refresh using AuthContext.

### 5.2 Onboarding / topic subscription flow

The subscription logic is important because it affects whether a user is considered onboarded.

The backend does two things:
- saves topic subscriptions,
- marks the user as onboarded once at least one topic is present.

This is implemented in the topics API and repository layer to make onboarding resilient even if the frontend chooses a different path.

### 5.3 Team invitation flow

Teams are owned by an admin and each team has one newsletter configuration.

The flow is:
1. admin creates team + newsletter configuration,
2. admin invites one or more member emails,
3. backend sends an invite email containing accept/decline links,
4. invited user opens the link and accepts the membership,
5. the invitation becomes accepted and the member joins the team.

This is a public invitation flow, so the acceptance endpoint does not require the user to already be logged in at the moment of opening the invite page.

---

## 6. Scheduler and background jobs

The backend uses APScheduler and starts jobs at application startup.

### 6.1 Catalog sync job

Purpose:
- fetch Microsoft Learn catalog metadata,
- store it in catalog_cache,
- keep the digest system fed with fresh items.

Important behavior:
- this job runs once per day at the configured UTC hour,
- it does not generate AI output,
- it only refreshes catalog metadata.

### 6.2 Digest dispatch job

Purpose:
- look for users and teams whose scheduled delivery time has arrived,
- generate digests for due recipients,
- send them by email.

Important behavior:
- this job runs every 15 minutes,
- it reads from catalog_cache only,
- it uses a shared Groq-result cache for the duration of the dispatch run to avoid repeated AI calls for identical content.

### 6.3 Seed topics job

Purpose:
- ensure system topics exist on startup.

This makes the platform self-healing for first-run initialization.

---

## 7. How digest generation works

This is the most important business path in the project.

### Step-by-step logic

1. The scheduler identifies a user or team that is due for delivery.
2. The digest generator resolves the user’s or newsletter’s subscribed topics.
3. It converts those topic mappings into product and subject filters.
4. It queries catalog_cache for content modified within the delivery window.
5. If there are no matching items, it records a no-content digest and skips email delivery.
6. If there are matches, it builds a cache key from topic slugs and content UIDs.
7. If the cache key is already in memory, it reuses the previous Groq output.
8. If not, it calls Groq to generate:
   - executive summary,
   - item-level newsletter summaries,
   - why-it-matters explanations,
   - key takeaways.
9. The result is rendered into an HTML email template.
10. The digest is stored in the database.
11. The HTML email is sent via SMTP.

### Why the cache exists

The digest generator intentionally avoids recomputing identical AI text for the same content set during one scheduler run. This reduces cost and latency, especially when many users share the same topics and frequency.

---

## 8. The AI layer

The AI integration lives in backend/app/services/ai/groq_client.py.

The current design is intentionally minimal and efficient:
- one Groq call per digest generation cycle,
- not one call per item,
- input summaries are truncated to control token usage,
- response_format is set to JSON so the model output is machine-readable.

The AI output shape is:
- executive_summary
- items[]
  - uid
  - newsletter_summary
  - why_it_matters
  - key_takeaways

This output is later merged into the Jinja2 HTML template that becomes the email body.

---

## 9. The email layer

The SMTP delivery logic is in backend/app/services/email/smtp_client.py.

It supports:
- SMTP connection testing,
- sending plain test emails,
- sending final digest emails,
- reporting structured success or failure information.

Important detail:
- Gmail requires an App Password, not the regular account password.
- The project includes a dedicated admin testing page to validate SMTP behavior before real delivery.

---

## 10. Main backend API groups

### Auth
- POST /api/auth/google
  - exchanges Google OAuth code for JWT

### Users
- GET /api/users/me
  - returns current user profile
- PUT /api/users/me/preferences
  - updates schedule, frequency, and delivery preferences

### Topics
- GET /api/topics/
  - list available system topics
- GET /api/topics/my
  - get subscribed topics
- POST /api/topics/subscribe
  - replace topic subscriptions
- POST /api/topics/onboard
  - finalize onboarding

### Teams
- GET /api/teams/
- POST /api/teams/
- GET /api/teams/{team_id}
- PATCH /api/teams/{team_id}
- DELETE /api/teams/{team_id}
- GET /api/teams/{team_id}/newsletter
- PATCH /api/teams/{team_id}/newsletter/topics
- PATCH /api/teams/{team_id}/newsletter/schedule
- PATCH /api/teams/{team_id}/newsletter/toggle
- POST /api/teams/{team_id}/invite

### Digests
- GET /api/digests/
- GET /api/digests/{digest_id}

### Admin
- GET /api/admin/config
- GET /api/admin/smtp-check
- POST /api/admin/send-test-email
- POST /api/admin/generate-test-digest
- POST /api/admin/send-test-digest
- GET /api/admin/preview-digest
- POST /api/admin/catalog-sync

---

## 11. Frontend route map

The major pages are:

- /
  - landing page
- /auth/callback
  - OAuth callback
- /onboarding
  - first-run topic selection and onboarding
- /dashboard
  - personal digest overview
- /preferences
  - delivery frequency and topic subscriptions
- /teams
  - team management and newsletter setup
- /digest/:digestId
  - digest details view
- /team-invite/:token
  - public invitation acceptance flow
- /admin/testing
  - SMTP and digest testing dashboard

---

## 12. Important database concepts

The database is the system of record for everything except the transient catalog cache and the runtime scheduler state.

Key entities:
- users
  - user identity, profile, onboarding status
- user_preferences
  - delivery frequency, time, timezone
- topics
  - topic taxonomy used to filter Microsoft Learn content
- user_subscriptions
  - links users to topics
- teams
  - organization-level groups for shared newsletters
- team_members
  - members and invite status
- team_newsletters
  - team delivery configuration
- content / catalog_cache
  - Microsoft Learn metadata cache used for digest generation
- digests
  - persisted digest history
- digest_items
  - individual content items attached to each digest

This relational design makes it possible to generate both personal and team-wide digests from the same underlying content cache.

---

## 13. How to run the project

### Option A — Docker (recommended)

From the repository root:

```bash
docker compose up --build
```

Then open:
- frontend: http://localhost:5173
- backend: http://localhost:8000
- docs: http://localhost:8000/docs

### Option B — Manual setup

Backend:

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

---

## 14. Environment variables you must configure

The backend uses environment variables loaded from the repository root .env file.

Required categories:

- Database
  - DATABASE_URL
- SMTP / Gmail
  - SMTP_SERVER
  - SMTP_PORT
  - SMTP_EMAIL
  - SMTP_PASSWORD
- Google OAuth
  - GOOGLE_CLIENT_ID
  - GOOGLE_CLIENT_SECRET
  - GOOGLE_REDIRECT_URI
  - FRONTEND_URL
- Groq AI
  - GROQ_API_KEY
  - GROQ_MODEL
- JWT
  - JWT_SECRET_KEY
  - JWT_ALGORITHM
  - JWT_EXPIRATION_HOURS
- Application
  - APP_NAME
  - APP_ENV
  - LOG_LEVEL

The frontend also expects:
- VITE_API_URL
- VITE_GOOGLE_CLIENT_ID

---

## 15. Development notes and debugging tips

### If the backend fails to start
- verify PostgreSQL is up,
- verify DATABASE_URL is correct,
- verify the .env file is present at the repo root.

### If SMTP fails
- ensure Gmail App Password is used,
- confirm 2FA is enabled,
- verify SMTP_EMAIL and SMTP_PASSWORD are present.

### If digests are not sending
- check scheduler logs,
- confirm the user has subscribed topics,
- confirm the delivery time matches the current UTC time window,
- confirm the catalog_cache has recent entries.

### If onboarding seems broken
- verify the user has at least one topic subscription,
- note that the backend includes self-healing onboarding logic for this case.

---

## 16. What makes this project interesting technically

This project combines several real-world patterns:
- background job scheduling,
- AI-assisted content generation,
- HTML email templating,
- JWT-based auth,
- Google OAuth integration,
- relational team and subscription logic,
- catalog caching for performance and stability.

It is a practical example of a small but complete product stack that behaves like an automated newsletter production system.

---

## 17. Suggested next improvements

If you want to extend this project further, the most useful next steps are:
- add richer analytics for digest performance,
- add content scraping for full article text instead of catalog summaries,
- improve topic taxonomy and AI classification,
- add webhook-based or instant delivery options,
- add unit/integration tests for the scheduler and digest generator.

---

## 18. Summary

MS Learn Digest is not just a simple web app. It is a small AI-powered content distribution system with:
- a React frontend,
- a FastAPI backend,
- PostgreSQL persistence,
- scheduled catalog sync,
- AI-enhanced digest generation,
- automated email delivery.

This README is intentionally detailed because the real value of the project is in how its pieces connect together across the full delivery pipeline.
