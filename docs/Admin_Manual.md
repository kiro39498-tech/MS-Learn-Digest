# Admin Manual
## MS Learn Digest

---

## Admin Panel Access

The admin testing panel is available at `/admin/testing` in the frontend. All admin API endpoints are under `/api/admin/*`.

> **Production note:** Set `ADMIN_ENABLED=false` in your `.env` to disable all admin endpoints in production environments.

---

## SMTP Testing

### Check SMTP Connection
```bash
GET /api/admin/smtp-check
```
Tests the SMTP connection and authentication without sending an email. Returns:
- `smtp_connection: "success"` — SMTP is configured and working
- `smtp_connection: "failed"` + error detail — use this to diagnose issues

### Send Test Email
```bash
POST /api/admin/send-test-email
{"email": "your@email.com"}
```
Sends a plain confirmation email. Use this to verify end-to-end delivery.

### Get SMTP Config
```bash
GET /api/admin/config
```
Shows current SMTP configuration. Password is masked (`abc*****`).

---

## Catalog Sync Management

The MS Learn Catalog API is synced automatically once per day. The `catalog_cache` table must have data before any digests can be generated.

### Check Cache Status
```bash
GET /api/admin/catalog-cache/stats
```
Returns:
```json
{
  "total_cached": 10542,
  "modules": 9823,
  "learning_paths": 719,
  "latest_last_modified": "2026-06-10T15:00:00+00:00",
  "latest_synced_at": "2026-06-10T02:05:00+00:00",
  "last_sync_status": "success",
  "sync_needed": false
}
```

If `total_cached = 0` or `sync_needed = true`, run a manual sync.

### Trigger Manual Sync
```bash
POST /api/admin/catalog-sync
```
Fetches modules and learningPaths from `learn.microsoft.com/api/catalog/` and upserts into `catalog_cache`. This is the same operation the nightly scheduler runs.

Expected response:
```json
{
  "status": "completed",
  "fetched": 10542,
  "upserted": 10542,
  "duration_seconds": 180,
  "next_scheduled_sync": "02:00 UTC daily"
}
```

> **Note:** This can take 2–5 minutes. The admin UI has a long timeout (360 seconds) for this reason.

### Preview Matched Content
```bash
POST /api/admin/catalog-cache/preview
{"topic_slugs": ["azure", "security"], "frequency": "weekly"}
```
Shows exactly which catalog items would match for a given topic set and frequency window. Use this to diagnose "no content" issues.

---

## Digest Testing

### Preview Digest in Browser
Open: `GET /api/admin/preview-digest`

Renders the digest HTML template with sample content in the browser. Use this to verify the email template looks correct.

### Send Sample Digest
```bash
POST /api/admin/send-test-digest
{"email": "you@example.com", "user_name": "Learner"}
```
Sends a digest email with hardcoded sample content (3 Microsoft Learn items). Does not use real catalog data.

### Send Real Digest (For Logged-In User)
```bash
POST /api/admin/test/send-my-digest
Authorization: Bearer <your-JWT>
```
Generates and sends a real digest for your account using actual `catalog_cache` data. This is the most reliable way to test the full digest pipeline.

If it returns `status: "no_content"`, the diagnostic section shows:
- `catalog_total` — total items in cache (0 = need to run sync)
- `catalog_items_matched` — items matching your topics
- `window_start` — the start of the frequency window being searched

---

## Learning Engine Testing

### Check Learning Engine Status
```bash
GET /api/learning/status
```
Returns whether the learning tables exist and curriculum is seeded.

### Seed Learning Curriculum
```bash
POST /api/learning/seed
```
Loads all learning tracks and modules from the curriculum definition. Safe to call multiple times (idempotent).

### Send Learning Lesson (Admin)
```bash
POST /api/admin/learning/send-lesson
Authorization: Bearer <your-JWT>
```
Immediately delivers the next lesson for your active learning subscriptions.

---

## Onboarding Diagnostics

### Debug Onboarding State
```bash
GET /api/admin/debug/onboarding
Authorization: Bearer <your-JWT>
```
Returns:
```json
{
  "email": "user@example.com",
  "is_onboarded": true,
  "is_onboarded_auto_healed": false,
  "subscription_count": 3,
  "subscribed_topics": [{"name": "Azure", "slug": "azure"}],
  "preferences_exist": true,
  "can_receive_digest": true,
  "verdict": "✅ Ready — has subscriptions and will receive digests"
}
```

If `is_onboarded = false` but subscriptions exist, this endpoint auto-heals the flag.

---

## Team Testing

### Create Test Team
```bash
POST /api/admin/teams/test-create
Authorization: Bearer <your-JWT>
{"team_name": "Test Engineering Team"}
```

### Invite to Test Team
```bash
POST /api/admin/teams/{team_id}/test-invite
Authorization: Bearer <your-JWT>
{"email": "member@example.com"}
```

### Accept Invitation (Without Logging In)
```bash
POST /api/admin/teams/invite/{token}/accept
```
Useful for testing the acceptance flow without requiring the invitee to have an account.

### Send Team Digest
```bash
POST /api/admin/teams/{team_id}/test-digest
Authorization: Bearer <your-JWT>
```
Generates and sends a real team newsletter using catalog_cache data.

---

## Scheduler Monitoring

The APScheduler runs in-process (inside the FastAPI/Uvicorn process). There is no separate worker or scheduler UI.

### Scheduled Jobs

| Job | Schedule | What it does |
|---|---|---|
| `catalog_sync_job` | Daily at `CATALOG_SYNC_HOUR:CATALOG_SYNC_MINUTE` UTC (default 02:00) | Fetches MS Learn catalog and upserts `catalog_cache` |
| `digest_dispatch_job` | Once every hour | Sends due individual and team digests |
| `learning_dispatch_job` | Once every hour | Delivers due learning lessons |
| `seed_topics_job` | Once on startup | Seeds system topic tree |
| `seed_learning_job` | Once on startup | Seeds learning curriculum |

### Monitoring via Logs

All scheduler activity is logged to stdout. Key log patterns:

```
JOB: catalog_sync | START | scheduled=02:00 UTC
JOB: catalog_sync | COMPLETE | fetched=10542 upserted=10542 duration=180s

JOB: digest_dispatch | START | utc=2026-06-10 08:00 dow=1
JOB: digest_dispatch | user=user@email.com | freq=weekly day=0 due=YES
DIGEST | user=user@email.com | EMAIL SENT | id=uuid

JOB: learning_dispatch | START | due_subscriptions=5
LEARNING | user=uuid topic=Azure seq=3 | SENT to email@example.com
```

### Configuring Catalog Sync Time

In `.env`:
```env
CATALOG_SYNC_HOUR=2
CATALOG_SYNC_MINUTE=0
```
Restart the backend for changes to take effect.

---

## Database Administration

### Run Migrations
```bash
cd backend
alembic upgrade head
```

### Check Current Migration
```bash
alembic current
```

### View Migration History
```bash
alembic history
```

### Rollback One Migration
```bash
alembic downgrade -1
```

### Reset Database (Development Only)
```bash
# Drop and recreate database
dropdb mslearndigest
createdb mslearndigest
alembic upgrade head
```

---

## Log Analysis

Logs use the format:
```
2026-06-10 08:05:00 | INFO     | app.services.digest.generator  | DIGEST | user=u@e.com | EMAIL SENT
```

### Common Log Prefixes

| Prefix | Module | Meaning |
|---|---|---|
| `DIGEST |` | digest/generator.py | Digest generation events |
| `JOB: catalog_sync |` | core/scheduler.py | Catalog sync job events |
| `JOB: digest_dispatch |` | core/scheduler.py | Digest delivery job events |
| `JOB: learning_dispatch |` | core/scheduler.py | Learning delivery job events |
| `LEARNING |` | learning/newsletter_generator.py | Lesson delivery events |
| `LESSON_GEN |` | learning/lesson_generator.py | Groq lesson generation |
| `GROQ |` | ai/groq_client.py | Groq API call stats |
| `SYNC |` | ingestion/sync.py | Catalog sync progress |
| `CATALOG |` | ingestion/catalog_client.py | Catalog API fetch |
| `INVITE |` | repositories/team_repository.py | Team invitation events |
| `EMAIL_AUTH |` | services/email_auth_service.py | Magic-link auth events |
| `SMTP_TEST |` | services/email/smtp_client.py | SMTP test events |
| `EMAIL_SEND |` | services/email/smtp_client.py | Email delivery events |
| `DISCOVERY |` | learning/resource_discovery.py | Resource scraping events |

---

## Production Checklist

Before going to production:

- [ ] Set `APP_ENV=production`
- [ ] Set `ADMIN_ENABLED=false` (or keep `true` if admin access is needed)
- [ ] Generate a strong `JWT_SECRET_KEY` (32+ random characters)
- [ ] Set `FRONTEND_URL` to your production domain
- [ ] Set `GOOGLE_REDIRECT_URI` to your production callback URL
- [ ] Add production domain to Google OAuth authorized redirect URIs
- [ ] Run `alembic upgrade head` against production database
- [ ] Trigger initial catalog sync: `POST /api/admin/catalog-sync`
- [ ] Verify SMTP: `GET /api/admin/smtp-check`
- [ ] Send test digest: `POST /api/admin/send-test-digest`
