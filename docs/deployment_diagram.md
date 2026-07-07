# Deployment Diagram
## MS Learn Digest

---

## Local Development Deployment

```mermaid
graph TB
    subgraph "Developer Machine"
        subgraph "Terminal 1: Frontend"
            NPM["npm run dev\nVite 8 Dev Server\nhttp://localhost:5173\nHMR enabled"]
        end

        subgraph "Terminal 2: Backend"
            UV["python -m uvicorn app.main:app\n--host 0.0.0.0 --port 8000 --reload\nFastAPI + APScheduler"]
        end

        subgraph "PostgreSQL (local)"
            DB[("PostgreSQL 14+\nlocalhost:5432\nDatabase: mslearndigest\n20 tables")]
        end

        subgraph "Files"
            ENV[".env\nAll secrets + config"]
            TPLS["app/templates/\nJinja2 HTML email templates"]
        end
    end

    subgraph "External Cloud Services"
        GROQ["Groq API\nhttps://api.groq.com\nllama-3.3-70b-versatile\nDigest + lesson generation"]

        GAUTH["Google OAuth\nhttps://accounts.google.com\nhttps://oauth2.googleapis.com\nUser authentication"]

        GSMTP["Gmail SMTP\nsmtp.gmail.com:587\nSTARTTLS\nAll outbound email"]

        MSCAT["MS Learn Catalog API\nhttps://learn.microsoft.com/api/catalog/\nModules + LearningPaths metadata\nDaily sync"]

        DDG["DuckDuckGo Search\nResource discovery for lessons\nUp to 3 URLs per module"]
    end

    NPM -->|"axios HTTP\nAuthorization: Bearer JWT"| UV
    UV -->|"SQLAlchemy\npsycopg2"| DB
    UV -->|"httpx async\nJSON REST"| GROQ
    UV -->|"httpx async\nOAuth2"| GAUTH
    UV -->|"smtplib\nSTARTTLS"| GSMTP
    UV -->|"httpx async\nGET ?type=modules"| MSCAT
    UV -->|"requests\nDuckDuckGo + BeautifulSoup"| DDG
    ENV -.->|"loaded by\npydantic_settings"| UV
    TPLS -.->|"FileSystemLoader\nJinja2"| UV
```

---

## Process Map

```mermaid
graph LR
    subgraph "Backend Process (single Python process)"
        FAST["FastAPI Application\n(Uvicorn ASGI server)"]
        SCH["APScheduler\n(AsyncIOScheduler)\nshares event loop with FastAPI"]

        FAST <--> SCH
    end

    subgraph "Scheduled Jobs (in-process threads/coroutines)"
        J1["catalog_sync_job\n02:00 UTC daily"]
        J2["digest_dispatch_job\nhourly"]
        J3["learning_dispatch_job\nhourly"]
        J4["seed_topics_job\nonce on startup"]
        J5["seed_learning_job\nonce on startup"]
    end

    SCH --> J1
    SCH --> J2
    SCH --> J3
    SCH --> J4
    SCH --> J5
```

---

## Data Persistence Map

```mermaid
graph LR
    subgraph "PostgreSQL: mslearndigest"
        subgraph "Auth Tables"
            U[users]
            UP[user_preferences]
            ELT[email_login_tokens]
        end

        subgraph "Digest Tables"
            T[topics]
            US[user_subscriptions]
            CC[catalog_cache]
            SM[sync_metadata]
            D[digests]
            DI[digest_items]
        end

        subgraph "Team Tables"
            TM[teams]
            TMM[team_members]
            TI[team_invitations]
            TN[team_newsletters]
            NT[newsletter_topics]
        end

        subgraph "Learning Tables"
            LT[learning_topics]
            LM[learning_modules]
            ULS[user_learning_subscriptions]
            UPS[user_phase_subscriptions]
            GL[generated_lessons]
            LA[learning_analytics]
            LWR[learning_weekly_reviews]
        end
    end
```

---

## Network Ports and Protocols

| Service | Port | Protocol | Direction |
|---|---|---|---|
| Vite Dev Server | 5173 | HTTP | Browser → Vite |
| FastAPI Backend | 8000 | HTTP | Browser/Vite → FastAPI |
| PostgreSQL | 5432 | TCP | FastAPI → PostgreSQL |
| Gmail SMTP | 587 | SMTP+STARTTLS | FastAPI → Gmail |
| Groq API | 443 | HTTPS | FastAPI → Groq |
| Google OAuth | 443 | HTTPS | FastAPI ↔ Google |
| MS Learn Catalog | 443 | HTTPS | FastAPI → MS Learn |
| DuckDuckGo | 443 | HTTPS | FastAPI → DuckDuckGo |

---

## Production Deployment Notes

No Docker configuration is currently included. For production deployment:

1. **Database:** Use a managed PostgreSQL service (AWS RDS, Azure Database for PostgreSQL, Supabase)
2. **Backend:** Deploy FastAPI app behind a reverse proxy (Nginx, Caddy) on a VM or PaaS (Railway, Render, Fly.io)
3. **Frontend:** Build with `npm run build` and serve static files via CDN or the same reverse proxy
4. **Environment:** All secrets in platform environment variables (not `.env` file)
5. **HTTPS:** Enforce at the reverse proxy / load balancer level
6. **Process management:** Use `systemd`, `supervisor`, or platform-native process management to keep Uvicorn running

**Key environment changes for production:**
```env
APP_ENV=production
ADMIN_ENABLED=false
FRONTEND_URL=https://your-domain.com
GOOGLE_REDIRECT_URI=https://your-backend-domain.com/auth/google/callback
JWT_SECRET_KEY=<64+ char random string>
```
