"""
APScheduler Configuration — Background Jobs

Jobs
────
catalog_cache_sync   — once daily at CATALOG_SYNC_HOUR:CATALOG_SYNC_MINUTE UTC.
                       Populates catalog_cache from the MS Learn Catalog API.
                       Digest generation NEVER triggers this job.
                       If the sync fails, the previous successful cache is used.

digest_dispatch      — every 15 minutes.
                       Reads from catalog_cache only — never triggers a sync.

seed_topics          — once on startup.

Timezone contract
─────────────────
delivery_time stored in user's local timezone.
Scheduler converts to UTC before comparing against the UTC wall clock.
"""

import logging
from datetime import datetime, timezone, timedelta, time as dt_time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


# ── Timezone helpers ───────────────────────────────────────────────────────────

def _safe_zone(tz_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(tz_name or "UTC")
    except (ZoneInfoNotFoundError, Exception):
        logger.warning(f"SCHEDULER | Unknown timezone '{tz_name}', falling back to UTC")
        return ZoneInfo("UTC")


def _local_time_to_utc_hour_minute(local_time: dt_time, tz: ZoneInfo):
    today = datetime.now(ZoneInfo("UTC")).date()
    local_dt = datetime(
        today.year, today.month, today.day,
        local_time.hour, local_time.minute, 0,
        tzinfo=tz,
    )
    utc_dt = local_dt.astimezone(ZoneInfo("UTC"))
    return utc_dt.hour, utc_dt.minute


# ── Sync metadata helper ───────────────────────────────────────────────────────

def _update_sync_metadata(db, started_at, completed_at, fetched, upserted, status):
    try:
        from app.models.team import SyncMetadata
        row = db.query(SyncMetadata).filter(SyncMetadata.id == 1).first()
        if not row:
            row = SyncMetadata(id=1)
            db.add(row)
        row.last_sync_started_at = started_at
        row.last_sync_completed_at = completed_at
        row.last_sync_fetched = fetched
        row.last_sync_upserted = upserted
        row.last_sync_status = status
        db.commit()
    except Exception as exc:
        logger.error(f"SCHEDULER | sync_metadata update failed: {exc}")


# ── Job: Catalog cache sync ────────────────────────────────────────────────────

async def run_catalog_sync():
    """
    Fetch the MS Learn Catalog and upsert into catalog_cache.
    Runs ONCE per day (scheduled via CronTrigger).
    Digest generation reads from catalog_cache — it never calls this function.

    On failure: logs the error and updates sync_metadata with status='failed'.
    Digest delivery continues using the previous successful cache snapshot.
    """
    started_at = datetime.now(timezone.utc)
    logger.info(
        f"JOB: catalog_sync | START | "
        f"scheduled={settings.CATALOG_SYNC_HOUR:02d}:{settings.CATALOG_SYNC_MINUTE:02d} UTC"
    )
    db = SessionLocal()
    try:
        from app.services.ingestion.sync import CatalogSyncService
        service = CatalogSyncService(db)
        result = await service.sync_catalog()
        completed_at = datetime.now(timezone.utc)

        _update_sync_metadata(
            db,
            started_at=started_at,
            completed_at=completed_at,
            fetched=result.fetched,
            upserted=result.upserted,
            status="success",
        )
        logger.info(
            f"JOB: catalog_sync | COMPLETE | "
            f"fetched={result.fetched} upserted={result.upserted} "
            f"duration={(completed_at - started_at).seconds}s"
        )
    except Exception as exc:
        completed_at = datetime.now(timezone.utc)
        _update_sync_metadata(
            db,
            started_at=started_at,
            completed_at=completed_at,
            fetched=0,
            upserted=0,
            status="failed",
        )
        logger.error(
            f"JOB: catalog_sync | FAILED | {exc} | "
            f"Digests will continue using the previous successful cache snapshot.",
            exc_info=True,
        )
    finally:
        db.close()


# ── Job: Digest dispatch ───────────────────────────────────────────────────────

async def run_digest_dispatch():
    """
    Every 15 minutes: check all due users/newsletters and send digests.
    Reads ONLY from catalog_cache — never triggers a catalog sync.
    A single dispatch_cache dict is shared across all users in this run so that
    identical topic+frequency+content combinations reuse the same Groq output.
    """
    db = SessionLocal()
    try:
        from app.services.digest.generator import DigestGenerator
        from app.models.user import User
        from app.models.user_preference import UserPreference
        from app.models.topic import UserSubscription
        from app.repositories.team_repository import TeamRepository

        now_utc = datetime.now(ZoneInfo("UTC"))
        logger.info(
            f"JOB: digest_dispatch | START | "
            f"utc={now_utc.strftime('%Y-%m-%d %H:%M')} dow={now_utc.weekday()}"
        )

        # Shared Groq-result cache across this entire dispatch run
        dispatch_cache: dict = {}
        generator = DigestGenerator(db, dispatch_cache=dispatch_cache)

        # ── Individual users ──────────────────────────────────────────────
        users = (
            db.query(User)
            .join(UserPreference, UserPreference.user_id == User.id)
            .filter(
                User.id.in_(db.query(UserSubscription.user_id).distinct())
            )
            .all()
        )
        logger.info(f"JOB: digest_dispatch | {len(users)} users with subscriptions")

        sent_count = 0
        for user in users:
            pref = user.preferences
            if not pref:
                continue

            tz = _safe_zone(pref.timezone or "UTC")
            local_time = pref.delivery_time or dt_time(8, 0)
            utc_hour, utc_minute = _local_time_to_utc_hour_minute(local_time, tz)

            due = _is_due(
                frequency=pref.frequency or "weekly",
                delivery_day=pref.delivery_day if pref.delivery_day is not None else 0,
                utc_delivery_hour=utc_hour,
                utc_delivery_minute=utc_minute,
                current_utc_hour=now_utc.hour,
                current_utc_minute=now_utc.minute,
                current_dow=now_utc.weekday(),
                now_utc=now_utc,
            )

            logger.info(
                f"JOB: digest_dispatch | user={user.email} "
                f"tz={pref.timezone} local={local_time.strftime('%H:%M')} "
                f"utc={utc_hour:02d}:{utc_minute:02d} "
                f"now_utc={now_utc.strftime('%H:%M')} "
                f"freq={pref.frequency} day={pref.delivery_day} "
                f"due={'YES' if due else 'no'}"
            )

            if not due:
                continue

            logger.info(f"JOB: digest_dispatch | ELIGIBLE | {user.email}")
            try:
                result = await generator.generate_and_send_for_user(user)
                if result:
                    sent_count += 1
                logger.info(
                    f"JOB: digest_dispatch | user={user.email} | "
                    f"{'SENT' if result else 'skipped (no matching content)'}"
                )
            except Exception as exc:
                logger.error(
                    f"JOB: digest_dispatch | FAILED | user={user.email} | {exc}",
                    exc_info=True,
                )

        # ── Team newsletters ──────────────────────────────────────────────
        team_repo = TeamRepository(db)
        newsletters = team_repo.get_all_active_newsletters()
        logger.info(f"JOB: digest_dispatch | {len(newsletters)} active team newsletters")

        for newsletter in newsletters:
            tz = _safe_zone(newsletter.timezone or "UTC")
            local_time = newsletter.delivery_time or dt_time(9, 0)
            utc_hour, utc_minute = _local_time_to_utc_hour_minute(local_time, tz)

            due = _is_due(
                frequency=newsletter.frequency or "weekly",
                delivery_day=newsletter.delivery_day if newsletter.delivery_day is not None else 0,
                utc_delivery_hour=utc_hour,
                utc_delivery_minute=utc_minute,
                current_utc_hour=now_utc.hour,
                current_utc_minute=now_utc.minute,
                current_dow=now_utc.weekday(),
                now_utc=now_utc,
            )

            logger.info(
                f"JOB: digest_dispatch | newsletter='{newsletter.name}' "
                f"utc={utc_hour:02d}:{utc_minute:02d} due={'YES' if due else 'no'}"
            )

            if not due:
                continue

            logger.info(f"JOB: digest_dispatch | ELIGIBLE newsletter | '{newsletter.name}'")
            try:
                result = await generator.generate_and_send_for_newsletter(newsletter)
                logger.info(
                    f"JOB: digest_dispatch | newsletter='{newsletter.name}' | "
                    f"{'SENT' if result else 'skipped'}"
                )
            except Exception as exc:
                logger.error(
                    f"JOB: digest_dispatch | FAILED newsletter | '{newsletter.name}' | {exc}",
                    exc_info=True,
                )

        logger.info(
            f"JOB: digest_dispatch | COMPLETE | "
            f"users_sent={sent_count} groq_cache_entries={len(dispatch_cache)}"
        )

    except Exception as exc:
        logger.error(f"JOB: digest_dispatch | FATAL: {exc}", exc_info=True)
    finally:
        db.close()


def _is_due(
    frequency: str,
    delivery_day: int,
    utc_delivery_hour: int,
    utc_delivery_minute: int,
    current_utc_hour: int,
    current_utc_minute: int,
    current_dow: int,
    now_utc: datetime,
) -> bool:
    """
    Returns True when the current 15-minute bucket matches the scheduled delivery.

    Monthly: fires on the 1st of every month (no day-of-week selection needed).
    Biweekly: fires on even ISO week numbers for the chosen weekday.
    """
    def bucket(m: int) -> int:
        return (m // 15) * 15

    if current_utc_hour != utc_delivery_hour:
        return False
    if bucket(current_utc_minute) != bucket(utc_delivery_minute):
        return False

    if frequency == "daily":
        return True
    if frequency == "weekly":
        return current_dow == delivery_day
    if frequency == "biweekly":
        week_num = now_utc.isocalendar()[1]
        return current_dow == delivery_day and (week_num % 2 == 0)
    if frequency == "monthly":
        # Always send on the 1st of the month — no delivery_day needed
        return now_utc.day == 1
    return False


# ── Job: Learning newsletter dispatch ─────────────────────────────────────────

async def run_learning_dispatch():
    """
    Every 30 minutes: find all due learning subscriptions and deliver lessons.

    Each subscription is independent — Azure track and Fabric track for the
    same user produce two separate emails with different lesson content.

    This job is completely separate from run_digest_dispatch().
    It never touches catalog_cache or the digest tables.
    """
    db = SessionLocal()
    try:
        from app.repositories.learning_repository import LearningRepository
        from app.services.learning.newsletter_generator import LearningNewsletterGenerator

        repo = LearningRepository(db)
        due_subs = repo.get_all_due_subscriptions()

        now_utc = datetime.now(timezone.utc)
        logger.info(
            f"JOB: learning_dispatch | START | "
            f"utc={now_utc.strftime('%Y-%m-%d %H:%M')} | "
            f"due_subscriptions={len(due_subs)}"
        )

        if not due_subs:
            logger.info("JOB: learning_dispatch | no due subscriptions")
            return

        generator = LearningNewsletterGenerator(db)
        sent = 0
        failed = 0

        for sub in due_subs:
            try:
                result = await generator.deliver(sub)
                if result:
                    sent += 1
                else:
                    failed += 1
                logger.info(
                    f"JOB: learning_dispatch | "
                    f"user={sub.user_id} topic={sub.topic_id} | "
                    f"{'SENT' if result else 'FAILED'}"
                )
            except Exception as exc:
                failed += 1
                logger.error(
                    f"JOB: learning_dispatch | FAILED | "
                    f"user={sub.user_id} topic={sub.topic_id} | {exc}",
                    exc_info=True,
                )

        logger.info(
            f"JOB: learning_dispatch | COMPLETE | sent={sent} failed={failed}"
        )

    except Exception as exc:
        logger.error(f"JOB: learning_dispatch | FATAL: {exc}", exc_info=True)
    finally:
        db.close()


# ── Seed learning curriculum on startup ───────────────────────────────────────

async def seed_learning_curriculum_job():
    logger.info("JOB: seed_learning_curriculum — checking curriculum")
    db = SessionLocal()
    try:
        from app.services.learning.seeder import seed_learning_curriculum
        count = seed_learning_curriculum(db)
        if count:
            logger.info(f"JOB: seed_learning_curriculum — inserted {count} rows")
        else:
            logger.info("JOB: seed_learning_curriculum — curriculum already present")
    except Exception as exc:
        logger.error(f"JOB: seed_learning_curriculum — failed: {exc}", exc_info=True)
    finally:
        db.close()


# ── Seed system topics on startup ─────────────────────────────────────────────

async def seed_topics():
    logger.info("JOB: seed_topics — checking system topics")
    db = SessionLocal()
    try:
        from app.repositories.topic_repository import TopicRepository
        repo = TopicRepository(db)
        count = repo.seed_system_topics()
        if count:
            logger.info(f"JOB: seed_topics — inserted {count} topics")
        else:
            logger.info("JOB: seed_topics — all topics present")
    except Exception as exc:
        logger.error(f"JOB: seed_topics — failed: {exc}", exc_info=True)
    finally:
        db.close()


# ── Scheduler setup ────────────────────────────────────────────────────────────

def setup_scheduler():
    # ── Catalog cache sync — ONCE daily at configured UTC hour ────────────
    scheduler.add_job(
        run_catalog_sync,
        trigger=CronTrigger(
            hour=settings.CATALOG_SYNC_HOUR,
            minute=settings.CATALOG_SYNC_MINUTE,
            timezone="UTC",
        ),
        id="catalog_sync_job",
        name="MS Learn Catalog Cache Sync (daily)",
        replace_existing=True,
        misfire_grace_time=3600,  # allow up to 1 hour late start
    )

    # ── Digest dispatch — every 15 minutes ────────────────────────────────
    scheduler.add_job(
        run_digest_dispatch,
        trigger=CronTrigger(minute="0,15,30,45", timezone="UTC"),
        id="digest_dispatch_job",
        name="Digest Dispatch",
        replace_existing=True,
        misfire_grace_time=300,
    )

    # ── Learning dispatch — every 30 minutes ──────────────────────────────
    scheduler.add_job(
        run_learning_dispatch,
        trigger=CronTrigger(minute="0,30", timezone="UTC"),
        id="learning_dispatch_job",
        name="Learning Newsletter Dispatch",
        replace_existing=True,
        misfire_grace_time=300,
    )

    scheduler.start()
    logger.info(
        f"Scheduler started: "
        f"catalog_sync daily at {settings.CATALOG_SYNC_HOUR:02d}:{settings.CATALOG_SYNC_MINUTE:02d} UTC, "
        f"digest_dispatch every 15 min, "
        f"learning_dispatch every 30 min."
    )

    # Seed topics once immediately on startup
    scheduler.add_job(
        seed_topics,
        trigger="date",
        id="seed_topics_job",
        name="Seed System Topics",
    )

    # Seed learning curriculum once immediately on startup
    scheduler.add_job(
        seed_learning_curriculum_job,
        trigger="date",
        id="seed_learning_job",
        name="Seed Learning Curriculum",
    )


def stop_scheduler():
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped.")
