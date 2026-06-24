# Project Structure Documentation
## MS Learn Digest

---

## Top-Level Layout

```
MS-Learn-Digest/
├── .env                    ← Local secrets (not in git)
├── .env.example            ← Template for .env
├── .gitignore
├── README.md               ← Project overview and quick start
├── docs/                   ← All documentation (this folder)
│   ├── architecture/
│   │   └── architecture_overview.md
│   ├── Technical_Implementation_Document.md
│   ├── requirements.md
│   ├── API_Documentation.md
│   ├── AI_Architecture.md
│   ├── Learning_Engine.md
│   ├── Scheduler_Documentation.md
│   ├── Security.md
│   ├── User_Manual.md
│   ├── Admin_Manual.md
│   ├── Test_Strategy.md
│   ├── DFD.md
│   ├── sequence_diagrams.md
│   ├── component_diagram.md
│   ├── deployment_diagram.md
│   ├── Troubleshooting.md
│   └── Project_Structure.md
├── frontend/               ← React SPA (Vite 8)
└── backend/                ← FastAPI application
```

---

## Frontend Structure (`frontend/`)

```
frontend/
├── package.json            ← npm dependencies
├── vite.config.js          ← Vite configuration
├── tailwind.config.js      ← Tailwind CSS: custom colors (ms-blue, ms-dark, ms-gray, ms-light)
├── postcss.config.js       ← PostCSS configuration
├── index.html              ← Root HTML — mounts #root
└── src/
    ├── main.jsx            ← React entry point (StrictMode, createRoot)
    ├── App.jsx             ← Router, AuthProvider, all Route definitions
    ├── App.css             ← Base app styles (minimal)
    ├── index.css           ← Tailwind directives + component classes (btn-primary, card, input)
    │
    ├── pages/              ← Full-page components (route targets)
    │   ├── LandingPage.jsx     ← Login screen (Google OAuth + Email magic-link)
    │   ├── AuthCallback.jsx    ← Google OAuth redirect handler
    │   ├── EmailAuthCallback.jsx ← Email magic-link redirect handler
    │   ├── Onboarding.jsx      ← 2-step wizard: topics + schedule
    │   ├── Dashboard.jsx       ← Digest history list + stats
    │   ├── Preferences.jsx     ← Topic selection + delivery schedule settings
    │   ├── LearningCenter.jsx  ← Browse tracks / my learning / completed
    │   ├── Teams.jsx           ← Team management + newsletter configuration
    │   ├── DigestDetail.jsx    ← Full digest content viewer
    │   ├── TeamInvite.jsx      ← Public invite accept/decline page
    │   └── AdminTesting.jsx    ← Admin diagnostic and testing panel
    │
    ├── components/         ← Reusable UI components
    │   ├── Layout.jsx          ← App shell: sidebar navigation + <Outlet />
    │   ├── TopicCardGrid.jsx   ← Card-based topic selector
    │   │                         (search, category filters, expandable subtopics)
    │   ├── PhaseSelector.jsx   ← Phase enrollment modal
    │   │                         (Full Track / Select Phases toggle)
    │   └── TopicTree.jsx       ← Tree view topic selector (available, unused in production)
    │
    ├── context/
    │   └── AuthContext.jsx     ← JWT state, useAuth hook, refreshUser(), auto-redirect
    │
    └── services/
        └── api.js              ← Centralized Axios instance
                                  (baseURL, JWT interceptor, 401 auto-logout)
                                  All API function exports
```

### Key Frontend Conventions
- All API calls go through `services/api.js` — never raw axios elsewhere
- `AuthContext` is the single source of truth for user state
- Protected routes are wrapped in `<Layout>` which enforces authentication
- `clsx` used for conditional className concatenation
- `lucide-react` for all icons
- Tailwind utility classes only — no custom CSS files beyond `index.css`

---

## Backend Structure (`backend/`)

```
backend/
├── alembic.ini             ← Alembic configuration
├── requirements.txt        ← Python dependencies
│
├── alembic/                ← Database migrations
│   ├── env.py              ← Alembic env: loads DATABASE_URL, imports all models
│   ├── script.py.mako      ← Migration file template
│   └── versions/           ← 9 migration files (chronological)
│       ├── 28e549d24050_initial_schema.py          ← Core tables
│       ├── a1b2c3d4e5f6_add_content_changes.py     ← Content changes (superseded)
│       ├── b2c3d4e5f6a7_catalog_cache_refactor.py  ← Replaced content tables with catalog_cache
│       ├── c3d4e5f6a7b8_team_invitations.py        ← TeamInvitation + SyncMetadata
│       ├── d4e5f6a7b8c9_team_one_newsletter.py     ← UNIQUE(team_id) on newsletters
│       ├── e5f6a7b8c9d0_hierarchical_topics.py     ← parent_topic_id, level, is_active on topics
│       ├── f6a7b8c9d0e1_learning_tracks.py         ← Learning engine tables
│       ├── g7h8i9j0k1l2_learning_enhancement.py   ← Phases, milestones, analytics, streaks
│       └── h8i9j0k1l2m3_email_auth_phase_learning.py ← Email auth + user_phase_subscriptions
│
└── app/
    ├── main.py             ← FastAPI app, lifespan (scheduler start/stop), CORS, health check
    │
    ├── api/                ← HTTP request handlers (thin — delegate to services/repos)
    │   ├── __init__.py     ← APIRouter aggregator (imports all routers)
    │   ├── auth.py         ← /auth/* (Google OAuth + magic-link)
    │   ├── users.py        ← /users/* (profile, preferences)
    │   ├── topics.py       ← /topics/* (tree, subscriptions, onboarding)
    │   ├── digests.py      ← /digests/* (history)
    │   ├── learning.py     ← /learning/* (tracks, phases, progress)
    │   ├── teams.py        ← /teams/* (team CRUD, newsletter, members, invitations)
    │   ├── newsletters.py  ← /newsletters/* (read-only list for team admins)
    │   └── admin.py        ← /admin/* (testing, diagnostics, sync)
    │
    ├── core/               ← Cross-cutting concerns
    │   ├── config.py       ← Pydantic Settings (all environment variables)
    │   ├── database.py     ← SQLAlchemy SessionLocal, Base, get_db dependency
    │   ├── security.py     ← JWT create/decode, get_current_user_id dependency
    │   ├── scheduler.py    ← APScheduler setup, all job functions
    │   └── logging.py      ← setup_logging() — structured stdout format
    │
    ├── models/             ← SQLAlchemy ORM models (one file per domain)
    │   ├── __init__.py
    │   ├── user.py         ← User
    │   ├── user_preference.py ← UserPreference
    │   ├── auth.py         ← EmailLoginToken
    │   ├── topic.py        ← Topic, UserSubscription
    │   ├── catalog_cache.py ← CatalogCache
    │   ├── digest.py       ← Digest, DigestItem
    │   ├── team.py         ← Team, TeamMember, TeamInvitation, TeamNewsletter, NewsletterTopic, SyncMetadata
    │   ├── learning.py     ← LearningTopic, LearningModule, UserLearningSubscription,
    │   │                     UserPhaseSubscription, GeneratedLesson, LearningAnalytics,
    │   │                     LearningWeeklyReview
    │   └── content.py      ← Empty stub (content tables replaced by catalog_cache)
    │
    ├── schemas/            ← Pydantic v2 request/response models
    │   ├── __init__.py
    │   ├── auth.py         ← Token, GoogleAuthCode
    │   ├── user.py         ← UserResponse, UserPreferenceResponse, UserPreferenceCreate
    │   ├── topic.py        ← TopicFlat, TopicNode, UserSubscriptionCreate, UserSubscriptionResponse
    │   ├── digest.py       ← DigestResponse, DigestDetailResponse, DigestItemResponse
    │   ├── learning.py     ← LearningTopicResponse, LearningModuleResponse,
    │   │                     LearningProgressResponse, LearningAnalyticsResponse,
    │   │                     SubscribeRequest, UpdateFrequencyRequest
    │   ├── team.py         ← TeamResponse, TeamCreate, TeamMemberResponse, InviteResult,
    │   │                     TeamNewsletterResponse, UpdateScheduleRequest, etc.
    │   └── content.py      ← Empty stub
    │
    ├── repositories/       ← Database access layer (all SQL through SQLAlchemy ORM)
    │   ├── __init__.py
    │   ├── user_repository.py      ← UserRepository
    │   ├── topic_repository.py     ← TopicRepository (+ SYSTEM_TOPICS seed data)
    │   ├── digest_repository.py    ← DigestRepository
    │   ├── learning_repository.py  ← LearningRepository (phase-aware)
    │   └── team_repository.py      ← TeamRepository
    │
    ├── services/           ← Business logic and external integrations
    │   ├── auth_service.py         ← AuthService (Google OAuth)
    │   ├── email_auth_service.py   ← EmailAuthService (magic-link)
    │   │
    │   ├── ai/
    │   │   ├── __init__.py
    │   │   └── groq_client.py      ← GroqClient (digest generation)
    │   │
    │   ├── digest/
    │   │   ├── __init__.py
    │   │   └── generator.py        ← DigestGenerator (full pipeline)
    │   │
    │   ├── email/
    │   │   ├── __init__.py
    │   │   └── smtp_client.py      ← EmailClient (smtplib STARTTLS)
    │   │
    │   ├── ingestion/
    │   │   ├── catalog_client.py   ← CatalogClient (httpx)
    │   │   └── sync.py             ← CatalogSyncService (batch UPSERT)
    │   │
    │   └── learning/
    │       ├── __init__.py
    │       ├── curriculum.py       ← LEARNING_CURRICULUM constant (all tracks + modules)
    │       ├── lesson_generator.py ← LessonGeneratorService (Groq, Senior MCT persona)
    │       ├── newsletter_generator.py ← LearningNewsletterGenerator (deliver pipeline)
    │       ├── resource_discovery.py   ← discover_resources() (DuckDuckGo + BeautifulSoup)
    │       └── seeder.py           ← seed_learning_curriculum() (idempotent UPSERT)
    │
    └── templates/          ← Jinja2 HTML email templates
        ├── digest_email.html       ← Personalised digest newsletter
        ├── learning_email.html     ← Individual lesson delivery
        └── invitation_email.html   ← Team member invitation
```

---

## Database Layer Architecture

The data layer follows the **Repository pattern**:

```
API Handler
    └── calls Repository (SQL queries)
              └── uses SQLAlchemy Session (from get_db() dependency)
                          └── connects to PostgreSQL

Business logic (Services)
    └── calls Repository
    └── calls External APIs (Groq, SMTP, Catalog, DuckDuckGo)
```

Services are **never** injected into Repositories. Repositories are **never** aware of HTTP concerns. This separation makes both layers independently testable.

---

## Configuration Hierarchy

All application settings come from `core/config.py` (`Settings` class, Pydantic Settings v2):

```
Environment Variables (.env file)
    → Settings.model_validate() at startup
    → settings singleton imported by all modules
    → Never hardcoded in business logic
```

---

## Alembic Migration Chain

```
28e549d24050  (initial)
    ↓
a1b2c3d4e5f6  (content_changes)
    ↓
b2c3d4e5f6a7  (catalog_cache_refactor — drops content tables, adds catalog_cache)
    ↓
c3d4e5f6a7b8  (team_invitations + sync_metadata)
    ↓
d4e5f6a7b8c9  (team_one_newsletter — UNIQUE constraint)
    ↓
e5f6a7b8c9d0  (hierarchical_topics — parent_topic_id, level, is_active)
    ↓
f6a7b8c9d0e1  (learning_tracks — 4 new tables)
    ↓
g7h8i9j0k1l2  (learning_enhancement — phases, milestones, analytics, weekly_reviews)
    ↓
h8i9j0k1l2m3  (email_auth + user_phase_subscriptions — current HEAD)
```

Run `alembic upgrade head` to apply all migrations.
