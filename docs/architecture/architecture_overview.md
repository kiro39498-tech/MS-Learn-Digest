# Architecture Documentation
## MS Learn Digest

---

## 1. Context Diagram (Level 0)

```mermaid
C4Context
    title MS Learn Digest — System Context

    Person(user, "Individual User", "Subscribes to topics and learning tracks, receives newsletters")
    Person(teamAdmin, "Team Admin", "Creates teams, invites members, manages team newsletters")
    Person(admin, "Platform Admin", "Tests SMTP, triggers syncs, monitors system")

    System(msld, "MS Learn Digest", "Personalised Microsoft Learn intelligence platform — AI newsletters, learning tracks, team newsletters")

    System_Ext(google, "Google OAuth 2.0", "Authentication provider")
    System_Ext(msLearn, "MS Learn Catalog API", "learn.microsoft.com/api/catalog/ — source of all content metadata")
    System_Ext(groq, "Groq API", "LLM service — Llama 3.3 70B — AI content generation")
    System_Ext(gmail, "Gmail SMTP", "Email delivery — STARTTLS port 587")
    System_Ext(ddg, "DuckDuckGo Search", "Resource discovery for lesson context")

    Rel(user, msld, "Uses", "HTTPS / JWT")
    Rel(teamAdmin, msld, "Manages teams", "HTTPS / JWT")
    Rel(admin, msld, "Operates", "HTTPS / JWT")
    Rel(msld, google, "OAuth code exchange", "HTTPS")
    Rel(msld, msLearn, "Fetches catalog metadata", "HTTPS REST")
    Rel(msld, groq, "Generates AI content", "HTTPS REST")
    Rel(msld, gmail, "Sends HTML emails", "SMTP TLS")
    Rel(msld, ddg, "Discovers lesson resources", "HTTPS")
```

---

## 2. Logical Architecture Diagram

```mermaid
graph TB
    subgraph "Presentation Layer"
        FE["React 19 SPA (Vite 8)\nTailwind CSS + Lucide React"]
    end

    subgraph "API Layer (FastAPI)"
        AUTH["/api/auth\nGoogle OAuth + Magic-Link"]
        USERS["/api/users\nProfile + Preferences"]
        TOPICS["/api/topics\nHierarchical Taxonomy"]
        DIGESTS["/api/digests\nDigest History"]
        LEARNING["/api/learning\nTracks + Phases + Progress"]
        TEAMS["/api/teams\nTeam + Newsletter Management"]
        ADMIN["/api/admin\nTesting + Diagnostics"]
    end

    subgraph "Service Layer"
        AS["AuthService\nEmailAuthService"]
        DS["DigestGenerator\n(Jinja2 rendering)"]
        LS["LearningNewsletterGenerator\nLessonGeneratorService"]
        CS["CatalogSyncService\nCatalogClient"]
        ES["EmailClient\n(smtplib)"]
        GS["GroqClient\n(digest + lesson generation)"]
        RD["ResourceDiscovery\n(DuckDuckGo + BeautifulSoup)"]
    end

    subgraph "Repository Layer"
        UR[UserRepository]
        TR[TopicRepository]
        DR[DigestRepository]
        LR[LearningRepository]
        TMR[TeamRepository]
    end

    subgraph "Scheduler (APScheduler)"
        SYNC["catalog_sync_job\n(daily 02:00 UTC)"]
        DISP["digest_dispatch_job\n(hourly)"]
        LEARN["learning_dispatch_job\n(hourly)"]
    end

    subgraph "Data Layer"
        PG[(PostgreSQL 14+\n20 tables)]
    end

    subgraph "External Services"
        GOOGLE[Google OAuth API]
        CATALOG[MS Learn Catalog API]
        GROQ_API[Groq API\nLlama 3.3 70B]
        SMTP_EXT[Gmail SMTP]
        DDG[DuckDuckGo Search]
    end

    FE -->|JWT Bearer| API Layer
    API Layer --> Service Layer
    Service Layer --> Repository Layer
    Repository Layer --> PG
    Scheduler --> Service Layer
    AS --> GOOGLE
    CS --> CATALOG
    GS --> GROQ_API
    ES --> SMTP_EXT
    RD --> DDG
```

---

## 3. Application Architecture Diagram

```mermaid
graph LR
    subgraph "Frontend (port 5173)"
        LAND[LandingPage]
        CB[AuthCallback]
        ECB[EmailAuthCallback]
        OB[Onboarding]
        DASH[Dashboard]
        PREF[Preferences]
        LC[LearningCenter]
        TEAMS_P[Teams]
        DD[DigestDetail]
        TI[TeamInvite]
        AT[AdminTesting]
        API_JS[api.js\nAxios + JWT interceptor]
    end

    subgraph "Backend (port 8000)"
        subgraph "FastAPI App"
            MAIN[main.py\nlifespan + CORS]
            ROUTER[api/__init__.py\nAPIRouter aggregator]
        end

        subgraph "Core"
            CFG[config.py\nPydantic Settings]
            SEC[security.py\nJWT + Bearer]
            SCH[scheduler.py\nAPScheduler jobs]
            DB[database.py\nSessionLocal]
            LOG[logging.py\nStructured stdout]
        end
    end

    LAND --> CB
    CB --> API_JS
    LAND --> ECB
    ECB --> API_JS
    API_JS -->|HTTP/JWT| ROUTER
    MAIN --> ROUTER
    MAIN --> SCH
    CFG --> MAIN
```

---

## 4. Deployment Architecture Diagram

```mermaid
graph TB
    subgraph "Developer Machine / Server"
        subgraph "Frontend Process"
            VITE["Vite Dev Server\nhttp://localhost:5173\nnpm run dev"]
        end

        subgraph "Backend Process"
            UVICORN["Uvicorn\nhttp://localhost:8000\npython -m uvicorn app.main:app"]
            APSCH["APScheduler\n(in-process, AsyncIOScheduler)"]
            UVICORN --> APSCH
        end

        subgraph "Database"
            POSTGRES["PostgreSQL 14+\nlocalhost:5432\nmslearndigest database"]
        end
    end

    subgraph "External Cloud Services"
        GROQ_D["Groq Cloud\napi.groq.com\nLlama 3.3 70B"]
        GAUTH["Google Auth\naccounts.google.com\noauth2.googleapis.com"]
        GSMTP["Gmail SMTP\nsmtp.gmail.com:587"]
        MSCAT["MS Learn Catalog\nlearn.microsoft.com/api/catalog/"]
        DDG_D["DuckDuckGo Search\nduckduckgo.com"]
    end

    VITE -->|Axios HTTP| UVICORN
    UVICORN -->|SQLAlchemy| POSTGRES
    UVICORN -->|HTTPS| GROQ_D
    UVICORN -->|HTTPS| GAUTH
    UVICORN -->|STARTTLS| GSMTP
    APSCH -->|HTTPS| MSCAT
    APSCH -->|HTTPS| DDG_D
```

---

## 5. Architecture Layers

| Layer | Technology | Responsibility |
|---|---|---|
| **Presentation** | React 19 + Vite + Tailwind | UI rendering, routing, state management (AuthContext) |
| **API Gateway** | FastAPI routers | Request validation, authentication, response serialization |
| **Service** | Python service classes | Business logic, orchestration, external API calls |
| **Repository** | SQLAlchemy repository pattern | Database access, query optimization |
| **Data** | PostgreSQL + Alembic | Persistence, schema evolution |
| **Scheduler** | APScheduler AsyncIOScheduler | Background jobs (sync, digest dispatch, learning dispatch) |
| **Email** | smtplib + Jinja2 templates | Email rendering and delivery |
| **AI** | Groq API + DuckDuckGo + BeautifulSoup | Content generation and resource discovery |
| **External Integration** | MS Learn Catalog API | Source of truth for learning content metadata |

---

## 6. Data Flow: Digest Generation

```mermaid
sequenceDiagram
    participant SCH as Scheduler (hourly)
    participant DG as DigestGenerator
    participant PG as PostgreSQL
    participant GR as Groq API
    participant SMTP as Gmail SMTP

    SCH->>PG: Query users with subscriptions + preferences
    loop Each due user
        DG->>PG: Get topic subscriptions
        DG->>PG: resolve_descendant_ids()
        DG->>PG: Query catalog_cache WHERE last_modified >= window
        DG->>DG: Filter by products/subjects overlap (Python)
        alt cache_key in dispatch_cache
            DG->>DG: Reuse cached Groq result
        else
            DG->>GR: generate_digest(items, topics, frequency)
            GR-->>DG: {executive_summary, items[]}
            DG->>DG: Store in dispatch_cache
        end
        DG->>DG: Render digest_email.html (Jinja2)
        DG->>PG: INSERT digest + digest_items
        DG->>SMTP: send_email(HTML)
        DG->>PG: UPDATE digest.status = sent/failed
    end
```

---

## 7. Data Flow: Learning Lesson Delivery

```mermaid
sequenceDiagram
    participant SCH as Scheduler (hourly)
    participant LNG as LearningNewsletterGenerator
    participant RD as ResourceDiscovery
    participant PG as PostgreSQL
    participant GR as Groq API
    participant SMTP as Gmail SMTP

    SCH->>PG: get_all_due_subscriptions()
    loop Each due subscription
        LNG->>PG: get_module(topic_id, current_seq)
        LNG->>PG: get_generated_lesson(module_id)
        alt lesson in cache
            PG-->>LNG: cached content_json
        else
            LNG->>RD: discover_resources(topic, module, keywords)
            RD->>RD: DuckDuckGo search
            RD->>RD: Scrape up to 3 pages (BeautifulSoup)
            RD-->>LNG: [{url, content}]
            LNG->>GR: generate_lesson(module_data + resources)
            GR-->>LNG: {explanation, diagram, quiz, exercise...}
            LNG->>PG: save_generated_lesson(module_id, content_json)
        end
        LNG->>LNG: Render learning_email.html
        LNG->>SMTP: send_email(subject, HTML)
        LNG->>PG: update_streak + record_analytics
        LNG->>PG: advance_module (phase-aware)
    end
```
