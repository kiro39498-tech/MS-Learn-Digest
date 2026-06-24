# Scheduler Documentation
## MS Learn Digest

---

## Overview

MS Learn Digest uses **APScheduler** (`AsyncIOScheduler`) as its background job system. The scheduler runs **in-process** inside the FastAPI/Uvicorn application — no separate worker process, no Redis, no Celery.

The scheduler is started in the FastAPI `lifespan` context manager (`main.py`):
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_scheduler()
    yield
    stop_scheduler()
```

---

## Scheduled Jobs

### 1. Catalog Cache Sync Job (`catalog_sync_job`)

| Property | Value |
|---|---|
| **Function** | `run_catalog_sync()` |
| **Trigger** | `CronTrigger(hour=CATALOG_SYNC_HOUR, minute=CATALOG_SYNC_MINUTE, timezone="UTC")` |
| **Default schedule** | Daily at 02:00 UTC |
| **Configurable via** | `CATALOG_SYNC_HOUR` and `CATALOG_SYNC_MINUTE` in `.env` |
| **misfire_grace_time** | 3600 seconds (1 hour) |

**What it does:**
1. Instantiates `CatalogSyncService`
2. Calls `service.sync_catalog()` which:
   - Fetches `?type=modules` from `learn.microsoft.com/api/catalog/`
   - Fetches `?type=learningPaths` from `learn.microsoft.com/api/catalog/`
   - UPSERTs all items into `catalog_cache` (PostgreSQL `ON CONFLICT DO UPDATE`)
   - Batches commits every 500 rows
3. Updates `sync_metadata` table (id=1) with: `started_at`, `completed_at`, `fetched`, `upserted`, `status`
4. On failure: logs error, updates `sync_metadata.status="failed"`, does **not** crash

**Why separate from digest dispatch:**  
Digest generation reads only from `catalog_cache` — it never triggers a sync. This ensures digest delivery is predictable and fast regardless of catalog API availability.

---

### 2. Digest Dispatch Job (`digest_dispatch_job`)

| Property | Value |
|---|---|
| **Function** | `run_digest_dispatch()` |
| **Trigger** | `CronTrigger(minute="0,15,30,45", timezone="UTC")` |
| **Schedule** | Every 15 minutes |
| **misfire_grace_time** | 300 seconds (5 minutes) |

**What it does:**

**For individual users:**
1. Queries all users who have topic subscriptions AND preferences
2. For each user, calls `_is_due()` to check delivery eligibility
3. For due users, calls `DigestGenerator.generate_and_send_for_user(user)`
4. Shares a single `dispatch_cache` dict across the entire run to avoid duplicate Groq calls

**For team newsletters:**
1. Queries all `TeamNewsletter` rows where `is_active=true`
2. For each newsletter, calls `_is_due()` with the newsletter's schedule
3. For due newsletters, calls `DigestGenerator.generate_and_send_for_newsletter(newsletter)`

**Delivery eligibility (`_is_due`):**
```python
def _is_due(frequency, delivery_day, utc_delivery_hour, utc_delivery_minute,
            current_utc_hour, current_utc_minute, current_dow, now_utc):
    
    # Must match the hour
    if current_utc_hour != utc_delivery_hour:
        return False
    
    # Must be in the same 15-minute bucket
    if bucket(current_utc_minute) != bucket(utc_delivery_minute):
        return False
    
    if frequency == "daily":   return True
    if frequency == "weekly":  return current_dow == delivery_day
    if frequency == "biweekly": return current_dow == delivery_day and week_num % 2 == 0
    if frequency == "monthly": return now_utc.day == 1
```

**Timezone handling:**
User delivery times are stored in their local timezone. The scheduler converts to UTC using `_local_time_to_utc_hour_minute(local_time, tz)` before comparing against the UTC wall clock.

---

### 3. Learning Dispatch Job (`learning_dispatch_job`)

| Property | Value |
|---|---|
| **Function** | `run_learning_dispatch()` |
| **Trigger** | `CronTrigger(minute="0,30", timezone="UTC")` |
| **Schedule** | Every 30 minutes |
| **misfire_grace_time** | 300 seconds (5 minutes) |

**What it does:**
1. Calls `LearningRepository.get_all_due_subscriptions()` — returns `status=active` subscriptions where `last_sent_at + frequency_delta <= now`
2. For each due subscription, calls `LearningNewsletterGenerator.deliver(sub)`
3. Each subscription is delivered independently — different tracks for the same user produce separate emails
4. Logs `sent` or `FAILED` per subscription

**Due check:**
```python
_FREQUENCY_DELTA = {
    "daily":    timedelta(hours=20),   # slightly under 24h to handle drift
    "weekly":   timedelta(days=6),
    "biweekly": timedelta(days=13),
}

def is_due(sub):
    if sub.status != "active": return False
    if sub.last_sent_at is None: return True  # never delivered yet
    delta = _FREQUENCY_DELTA.get(sub.frequency, timedelta(days=7))
    return now() >= sub.last_sent_at + delta
```

---

### 4. Seed Topics Job (`seed_topics_job`)

| Property | Value |
|---|---|
| **Function** | `seed_topics()` |
| **Trigger** | `DateTrigger` (once, immediately on startup) |

Seeds the system topic tree (9 root topics, 50+ subtopics) via `TopicRepository.seed_system_topics()`. Idempotent — skips existing slugs and repairs stale hierarchy.

---

### 5. Seed Learning Curriculum Job (`seed_learning_job`)

| Property | Value |
|---|---|
| **Function** | `seed_learning_curriculum_job()` |
| **Trigger** | `DateTrigger` (once, immediately on startup) |

Seeds all learning tracks and modules from `services/learning/curriculum.py` via `seed_learning_curriculum(db)`. Idempotent via `ON CONFLICT DO UPDATE`.

---

## Error Handling

All jobs are wrapped in `try/except`:

```python
async def run_catalog_sync():
    try:
        result = await service.sync_catalog()
        _update_sync_metadata(..., status="success")
    except Exception as exc:
        _update_sync_metadata(..., status="failed")
        logger.error(f"JOB: catalog_sync | FAILED | {exc}", exc_info=True)
    finally:
        db.close()
```

**Principles:**
- A failing job never crashes the FastAPI process
- A failing job never blocks other jobs
- `db.close()` is always called in `finally` to prevent connection leaks
- Each user/subscription is independently try/caught within the dispatch loops — one failure does not stop others

---

## Background Processing Notes

**No Redis:** All caching is in-memory (per scheduler run) or in PostgreSQL.

**No Celery:** APScheduler is used as the sole task runner. It shares the event loop with FastAPI.

**No task queue:** Jobs are not queued — they run sequentially within each job function. If the digest dispatch job takes longer than 15 minutes, the next trigger fires but APScheduler may skip or queue it (depending on `misfire_grace_time`).

**In-process isolation:** The scheduler runs in the same process as the API server. Heavy catalog syncs (~3 minutes) may consume CPU during the sync window but do not block the API event loop (async await is used throughout).

---

## Retry Logic

There is **no automatic retry** at the job level. The design philosophy is:
- **Catalog sync** failure → use previous cache snapshot (not a hard failure for users)
- **Digest failure** → recorded in `digests.status="failed"`, will not retry until next scheduled delivery window
- **Lesson failure** → `mark_sent(sub)` is called to advance `last_sent_at`, so the scheduler tries the next lesson at the next due time

For SMTP failures specifically, failed lessons/digests require manual intervention or will be retried at the next scheduled delivery window.

---

## Scheduler Configuration

All scheduler settings in `core/config.py`:

```python
CATALOG_SYNC_HOUR: int = 2         # UTC hour for daily catalog sync
CATALOG_SYNC_MINUTE: int = 0       # UTC minute for daily catalog sync
CATALOG_SYNC_INTERVAL_MINUTES: int = 60  # Legacy, kept for backward compat
```

**Changing the sync time:**
1. Update `CATALOG_SYNC_HOUR` and `CATALOG_SYNC_MINUTE` in `.env`
2. Restart the backend process
3. The scheduler reads these values in `setup_scheduler()` on startup
