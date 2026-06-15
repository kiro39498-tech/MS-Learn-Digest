"""
Admin API — Testing, diagnostics, catalog cache management, and team testing.

All endpoints require ADMIN_ENABLED=true (default in development).
In production set ADMIN_ENABLED=false to disable them entirely.

Endpoints:
  GET  /api/admin/config
  GET  /api/admin/smtp-check
  POST /api/admin/send-test-email
  POST /api/admin/generate-test-digest
  POST /api/admin/send-test-digest
  GET  /api/admin/preview-digest
  POST /api/admin/catalog-sync
  GET  /api/admin/catalog-cache/stats
  POST /api/admin/catalog-cache/preview
  POST /api/admin/test/send-my-digest
  GET  /api/admin/debug/onboarding
  POST /api/admin/teams/test-create
  POST /api/admin/teams/{team_id}/test-invite
  POST /api/admin/teams/invite/{token}/accept
  POST /api/admin/teams/{team_id}/test-digest
  GET  /api/admin/teams/{team_id}/delivery-status
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user_id
from app.services.email.smtp_client import EmailClient
from app.services.digest.generator import DigestGenerator
from app.models.digest import Digest
from app.models.catalog_cache import CatalogCache

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Guard ──────────────────────────────────────────────────────────────────────

def _check_admin_enabled():
    if settings.APP_ENV == "production" and not getattr(settings, "ADMIN_ENABLED", False):
        raise HTTPException(
            status_code=403,
            detail="Admin endpoints are disabled in production. Set ADMIN_ENABLED=true to override.",
        )


# ── Request schemas ────────────────────────────────────────────────────────────

class TestEmailRequest(BaseModel):
    email: EmailStr


class TestDigestRequest(BaseModel):
    email: EmailStr
    user_name: Optional[str] = "Learner"


class CatalogPreviewRequest(BaseModel):
    topic_slugs: List[str]
    frequency: str = "weekly"


class TestTeamCreateRequest(BaseModel):
    team_name: str = "Test Engineering Team"


class TestTeamInviteRequest(BaseModel):
    email: EmailStr


# ── Sample data ────────────────────────────────────────────────────────────────

_SAMPLE_ITEMS = [
    {
        "uid": "learn.wwl.security-copilot-describe-core-features",
        "title": "Describe the core features of Microsoft Security Copilot",
        "url": "https://learn.microsoft.com/en-us/training/modules/security-copilot-describe-core-features/",
        "content_type": "module",
        "duration_minutes": 26,
        "newsletter_summary": "Explore how Security Copilot integrates with Microsoft Defender and Sentinel to accelerate threat investigation through natural-language queries.",
        "why_it_matters": "Security teams can reduce investigation time from hours to minutes by surfacing context and recommended actions directly inside their existing tools.",
        "key_takeaways": [
            "Security Copilot's standalone and embedded experiences",
            "Integration points with Microsoft Defender and Sentinel",
            "Key use cases: incident summarisation, threat hunting, script analysis",
        ],
    },
    {
        "uid": "learn.wwl.experiment-azure-machine-learning",
        "title": "Experiment with Azure Machine Learning",
        "url": "https://learn.microsoft.com/en-us/training/modules/experiment-azure-machine-learning/",
        "content_type": "module",
        "duration_minutes": 38,
        "newsletter_summary": "Learn to run and track ML experiments in Azure Machine Learning using the Python SDK — from logging metrics to promoting the best model.",
        "why_it_matters": "Reproducible experiment tracking is the foundation of production-grade ML pipelines and shortens the path from prototype to deployment.",
        "key_takeaways": [
            "Create and run experiments with the Azure ML Python SDK",
            "Log metrics, parameters, and artefacts during training",
            "Compare runs and register the best model",
        ],
    },
    {
        "uid": "learn.azure-linux",
        "title": "Linux on Azure",
        "url": "https://learn.microsoft.com/en-us/training/paths/azure-linux/",
        "content_type": "learningPath",
        "duration_minutes": 210,
        "newsletter_summary": "A comprehensive learning path for running Linux workloads on Azure — covering VMs, storage, networking, and security hardening.",
        "why_it_matters": "Over 60% of Azure VMs run Linux; mastering this path gives cloud engineers the skills to deploy and secure Linux workloads at enterprise scale.",
        "key_takeaways": [
            "Deploy and configure Linux VMs on Azure",
            "Implement Azure networking and storage for Linux workloads",
            "Apply security best practices and compliance controls",
        ],
    },
]

_SAMPLE_EXECUTIVE_SUMMARY = (
    "This week Microsoft Learn published updates across Security, Azure AI, and Azure infrastructure. "
    "Highlights include new Security Copilot guidance for SOC teams, Azure ML experiment tracking, "
    "and a refreshed Linux on Azure learning path."
)


def _render_test_digest(user_name: str, topic_names: list) -> str:
    from jinja2 import Environment, FileSystemLoader
    import os
    template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
    env = Environment(loader=FileSystemLoader(template_dir))
    return env.get_template("digest_email.html").render(
        digest_title="Your Weekly MS Learn Digest — Test",
        user_name=user_name,
        topic_names=topic_names or ["Azure AI", "Security", "Azure"],
        executive_summary=_SAMPLE_EXECUTIVE_SUMMARY,
        items=_SAMPLE_ITEMS,
        freq="weekly",
        item_count=len(_SAMPLE_ITEMS),
        frontend_url=settings.FRONTEND_URL,
        generated_at=datetime.now(timezone.utc).strftime("%B %d, %Y"),
    )


# ── SMTP endpoints ─────────────────────────────────────────────────────────────

@router.get("/config")
async def get_smtp_config():
    _check_admin_enabled()
    pw = settings.SMTP_PASSWORD
    preview = (
        f"{pw[:4]}{'*' * (len(pw) - 4)}" if pw and len(pw) > 4
        else ("(set)" if pw else "(not set)")
    )
    return {
        "smtp_server": settings.SMTP_SERVER,
        "smtp_port": settings.SMTP_PORT,
        "smtp_email": settings.SMTP_EMAIL or "(not set)",
        "smtp_password": preview,
        "app_env": settings.APP_ENV,
        "frontend_url": settings.FRONTEND_URL,
    }


@router.get("/smtp-check")
async def smtp_check():
    _check_admin_enabled()
    client = EmailClient()
    result = client.test_connection()
    response = {
        "smtp_connection": "success" if result.success else "failed",
        "message": result.message,
        "detail": result.detail,
        "config": {
            "server": settings.SMTP_SERVER,
            "port": settings.SMTP_PORT,
            "email": settings.SMTP_EMAIL or "(not set)",
        },
    }
    if not result.success:
        raise HTTPException(status_code=502, detail=response)
    return response


@router.post("/send-test-email")
async def send_test_email(payload: TestEmailRequest):
    _check_admin_enabled()
    html_body = f"""
<!DOCTYPE html><html><head><meta charset="utf-8"></head>
<body style="font-family:'Segoe UI',Arial,sans-serif;background:#f3f4f6;padding:32px;">
  <div style="max-width:520px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;">
    <div style="background:#0078d4;padding:28px 32px;text-align:center;">
      <h1 style="color:#fff;margin:0;font-size:22px;">SMTP Test Successful ✅</h1>
    </div>
    <div style="padding:32px;">
      <p style="color:#374151;">This is a test email from <strong>MS Learn Digest</strong>.</p>
      <p style="color:#374151;">If you received this, SMTP delivery is working correctly.</p>
      <div style="background:#f0fdf4;border:1px solid #86efac;border-radius:8px;padding:16px;">
        <p style="color:#166534;margin:0;font-weight:600;">✅ Connection OK &nbsp; ✅ Auth OK &nbsp; ✅ Delivery OK</p>
      </div>
      <p style="color:#9ca3af;font-size:12px;margin-top:20px;">
        Sent at: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}
      </p>
    </div>
  </div>
</body></html>
"""
    client = EmailClient()
    result = client.send_email_with_result(
        recipient=str(payload.email),
        subject="✅ MS Learn Digest — SMTP Test",
        html_body=html_body,
    )
    if not result.success:
        raise HTTPException(
            status_code=502,
            detail={"status": "failed", "message": result.message, "detail": result.detail},
        )
    return {"status": "sent", "recipient": str(payload.email), "sent_at": datetime.now(timezone.utc).isoformat()}


# ── Sample digest endpoints ────────────────────────────────────────────────────

@router.post("/generate-test-digest")
async def generate_test_digest(db: Session = Depends(get_db)):
    _check_admin_enabled()
    html = _render_test_digest("Learner", ["Azure AI", "Security", "Azure"])
    now = datetime.now(timezone.utc)
    digest = Digest(
        title="Test Digest — MS Learn Weekly Update",
        digest_type="individual",
        content_html=html,
        content_json={"test": True, "item_count": len(_SAMPLE_ITEMS)},
        topic_names=["Azure AI", "Security", "Azure"],
        period_start=now - timedelta(weeks=1),
        period_end=now,
        status="generated",
        recipient_count=0,
    )
    db.add(digest)
    db.commit()
    db.refresh(digest)
    return {
        "status": "generated",
        "digest_id": str(digest.id),
        "item_count": len(_SAMPLE_ITEMS),
        "preview_url": f"{settings.FRONTEND_URL}/digest/{digest.id}",
        "created_at": digest.created_at.isoformat() if digest.created_at else now.isoformat(),
    }


@router.post("/send-test-digest")
async def send_test_digest(payload: TestDigestRequest, db: Session = Depends(get_db)):
    _check_admin_enabled()
    html = _render_test_digest(payload.user_name or "Learner", ["Azure AI", "Security", "Azure"])
    now = datetime.now(timezone.utc)
    digest = Digest(
        title="Test Digest — MS Learn Weekly Update",
        digest_type="individual",
        content_html=html,
        content_json={"test": True, "sent_to": str(payload.email)},
        topic_names=["Azure AI", "Security", "Azure"],
        period_start=now - timedelta(weeks=1),
        period_end=now,
        status="generated",
        recipient_count=0,
    )
    db.add(digest)
    db.commit()
    db.refresh(digest)

    client = EmailClient()
    result = client.send_email_with_result(
        recipient=str(payload.email),
        subject="📚 MS Learn Digest — Your Weekly Update (Test)",
        html_body=html,
    )
    if result.success:
        digest.status = "sent"
        digest.sent_at = datetime.now(timezone.utc)
        digest.recipient_count = 1
        db.commit()
    else:
        digest.status = "failed"
        db.commit()
        raise HTTPException(
            status_code=502,
            detail={"status": "failed", "digest_id": str(digest.id),
                    "message": result.message, "detail": result.detail},
        )
    return {
        "status": "sent",
        "recipient": str(payload.email),
        "digest_id": str(digest.id),
        "sent_at": digest.sent_at.isoformat(),
    }


@router.get("/preview-digest", response_class=HTMLResponse)
async def preview_digest():
    _check_admin_enabled()
    return HTMLResponse(content=_render_test_digest("Learner", ["Azure AI", "Security", "Azure"]))


# ── Catalog cache endpoints ────────────────────────────────────────────────────

@router.post("/catalog-sync")
async def manual_catalog_sync(db: Session = Depends(get_db)):
    """
    Manually trigger a catalog metadata sync.
    This is the same operation the nightly scheduler runs.
    Digest generation reads from this cache — it never calls this endpoint.
    """
    _check_admin_enabled()
    logger.info("ADMIN | catalog-sync | manual trigger")
    from app.services.ingestion.sync import CatalogSyncService
    from app.models.team import SyncMetadata

    started_at = datetime.now(timezone.utc)
    try:
        result = await CatalogSyncService(db).sync_catalog()
        completed_at = datetime.now(timezone.utc)

        # Update sync_metadata
        row = db.query(SyncMetadata).filter(SyncMetadata.id == 1).first()
        if not row:
            row = SyncMetadata(id=1)
            db.add(row)
        row.last_sync_started_at = started_at
        row.last_sync_completed_at = completed_at
        row.last_sync_fetched = result.fetched
        row.last_sync_upserted = result.upserted
        row.last_sync_status = "success"
        db.commit()

    except Exception as exc:
        logger.error(f"ADMIN | catalog-sync | FAILED: {exc}", exc_info=True)
        raise HTTPException(status_code=502, detail=f"Catalog sync failed: {exc}")

    total_cached = db.query(CatalogCache).count()
    duration_s = (completed_at - started_at).seconds
    return {
        "status": "completed",
        "fetched": result.fetched,
        "upserted": result.upserted,
        "invalid_urls": result.invalid_urls,
        "total_cached": total_cached,
        "duration_seconds": duration_s,
        "next_scheduled_sync": f"{settings.CATALOG_SYNC_HOUR:02d}:{settings.CATALOG_SYNC_MINUTE:02d} UTC daily",
    }


@router.get("/catalog-cache/stats")
async def catalog_cache_stats(db: Session = Depends(get_db)):
    """Return catalog_cache health statistics including last sync time."""
    _check_admin_enabled()
    from sqlalchemy import func
    from app.models.team import SyncMetadata

    total = db.query(CatalogCache).count()
    by_type = dict(
        db.query(CatalogCache.content_type, func.count(CatalogCache.id))
        .group_by(CatalogCache.content_type)
        .all()
    )
    latest_modified = db.query(func.max(CatalogCache.last_modified)).scalar()
    latest_synced = db.query(func.max(CatalogCache.last_synced_at)).scalar()

    sync_meta = db.query(SyncMetadata).filter(SyncMetadata.id == 1).first()

    return {
        "total_cached": total,
        "modules": by_type.get("module", 0),
        "learning_paths": by_type.get("learningPath", 0),
        "latest_last_modified": latest_modified.isoformat() if latest_modified else None,
        "latest_synced_at": latest_synced.isoformat() if latest_synced else None,
        "next_scheduled_sync": f"{settings.CATALOG_SYNC_HOUR:02d}:{settings.CATALOG_SYNC_MINUTE:02d} UTC daily",
        "last_sync_status": sync_meta.last_sync_status if sync_meta else None,
        "last_sync_started_at": sync_meta.last_sync_started_at.isoformat() if sync_meta and sync_meta.last_sync_started_at else None,
        "last_sync_completed_at": sync_meta.last_sync_completed_at.isoformat() if sync_meta and sync_meta.last_sync_completed_at else None,
        "last_sync_fetched": sync_meta.last_sync_fetched if sync_meta else None,
        "last_sync_upserted": sync_meta.last_sync_upserted if sync_meta else None,
        "sync_needed": total == 0,
        "note": (
            "catalog_cache is empty — run POST /api/admin/catalog-sync."
            if total == 0
            else f"{total:,} items cached."
        ),
    }


@router.post("/catalog-cache/preview")
async def catalog_cache_preview(
    payload: CatalogPreviewRequest,
    db: Session = Depends(get_db),
):
    _check_admin_enabled()
    from app.services.digest.generator import _lookback, _query_catalog, _build_filter_sets
    from app.models.topic import Topic

    topics = db.query(Topic).filter(Topic.slug.in_(payload.topic_slugs)).all()
    if not topics:
        raise HTTPException(
            status_code=404,
            detail=f"No topics found for slugs: {payload.topic_slugs}",
        )

    products_set, subjects_set = _build_filter_sets(topics, db=db)
    since = _lookback(payload.frequency)
    matched = _query_catalog(db, since, products_set, subjects_set)

    return {
        "frequency": payload.frequency,
        "window_start": since.isoformat(),
        "topic_slugs": payload.topic_slugs,
        "matched_count": len(matched),
        "items": [
            {
                "uid": m.uid,
                "title": m.title,
                "url": m.url,
                "content_type": m.content_type,
                "last_modified": m.last_modified.isoformat() if m.last_modified else None,
            }
            for m in matched
        ],
    }


# ── Live digest trigger (authenticated) ───────────────────────────────────────

@router.post("/test/send-my-digest")
async def send_my_digest(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Immediately generate and send a real digest for the authenticated user.
    Reads from catalog_cache — does NOT trigger a catalog sync.
    """
    from app.models.user import User
    from app.models.topic import UserSubscription, Topic
    from app.repositories.digest_repository import DigestRepository
    from app.services.digest.generator import _lookback, _query_catalog, _build_filter_sets

    _check_admin_enabled()
    logger.info(f"ADMIN | send-my-digest | user_id={user_id}")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    subs = db.query(UserSubscription).filter(UserSubscription.user_id == user.id).all()
    if not subs:
        raise HTTPException(
            status_code=400,
            detail="No topic subscriptions. Subscribe to at least one topic in Preferences first.",
        )

    if not user.is_onboarded:
        user.is_onboarded = True
        db.commit()
        logger.info(f"ADMIN | send-my-digest | AUTO-HEAL | is_onboarded=True for {user.email}")

    topic_ids = [s.topic_id for s in subs]
    topics = db.query(Topic).filter(Topic.id.in_(topic_ids)).all()
    topic_slugs = [t.slug for t in topics]
    topic_names = [t.name for t in topics]
    products_set, subjects_set = _build_filter_sets(topics, db=db)

    freq = (user.preferences.frequency if user.preferences else None) or "weekly"
    since = _lookback(freq)
    matched = _query_catalog(db, since, products_set, subjects_set)
    catalog_total = db.query(CatalogCache).count()

    diagnostic = {
        "user_email": user.email,
        "subscribed_topics": topic_names,
        "frequency": freq,
        "window_start": since.isoformat(),
        "catalog_items_matched": len(matched),
        "catalog_total": catalog_total,
    }

    logger.info(
        f"ADMIN | send-my-digest | user={user.email} "
        f"topics={topic_names} freq={freq} "
        f"matched={len(matched)} catalog_total={catalog_total}"
    )

    if not matched:
        logger.warning(f"ADMIN | send-my-digest | NO MATCHES | {diagnostic}")
        return {
            "status": "no_content",
            "recipient": user.email,
            "digest_id": None,
            "smtp_status": "not_sent",
            "message": (
                "No catalog items matched your topics in the selected window. "
                "Run POST /api/admin/catalog-sync first, then retry."
                if catalog_total == 0
                else "Catalog is populated but no items matched your topics in this window."
            ),
            "diagnostic": diagnostic,
        }

    generator = DigestGenerator(db, dispatch_cache={})
    result = await generator.generate_and_send_for_user(user)

    latest = (
        db.query(Digest)
        .filter(Digest.user_id == user.id)
        .order_by(Digest.created_at.desc())
        .first()
    )

    return {
        "status": "sent" if result else "failed",
        "recipient": user.email,
        "digest_id": str(latest.id) if latest else None,
        "smtp_status": "delivered" if result else "failed",
        "diagnostic": diagnostic,
    }


# ── Debug: onboarding state ────────────────────────────────────────────────────

@router.get("/debug/onboarding")
async def debug_onboarding(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    from app.models.user import User
    from app.models.topic import UserSubscription, Topic
    from app.models.user_preference import UserPreference

    _check_admin_enabled()
    uid = UUID(user_id)
    user = db.query(User).filter(User.id == uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    subs = db.query(UserSubscription).filter(UserSubscription.user_id == uid).all()
    sub_topics = []
    for s in subs:
        t = db.query(Topic).filter(Topic.id == s.topic_id).first()
        if t:
            sub_topics.append({"id": str(t.id), "name": t.name, "slug": t.slug})

    pref = db.query(UserPreference).filter(UserPreference.user_id == uid).first()

    healed = False
    if not user.is_onboarded and subs:
        user.is_onboarded = True
        db.commit()
        db.refresh(user)
        healed = True
        logger.info(f"ADMIN | debug/onboarding | AUTO-HEAL | {user.email}")

    return {
        "user_id": str(user.id),
        "email": user.email,
        "is_onboarded": user.is_onboarded,
        "is_onboarded_auto_healed": healed,
        "subscription_count": len(subs),
        "subscribed_topics": sub_topics,
        "preferences_exist": pref is not None,
        "preferences": {
            "frequency": pref.frequency,
            "delivery_time": str(pref.delivery_time),
            "delivery_day": pref.delivery_day,
            "timezone": pref.timezone,
        } if pref else None,
        "can_receive_digest": len(subs) > 0,
        "verdict": (
            "✅ Ready — has subscriptions and will receive digests"
            if subs else
            "❌ Not ready — no topic subscriptions"
        ),
    }


# ── Team testing endpoints ─────────────────────────────────────────────────────

@router.post("/teams/test-create")
async def test_team_create(
    payload: TestTeamCreateRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Create a test team (+ newsletter) owned by the current user."""
    _check_admin_enabled()
    from app.repositories.team_repository import TeamRepository
    from app.models.topic import Topic

    repo = TeamRepository(db)
    topics = db.query(Topic).limit(3).all()
    topic_ids = [t.id for t in topics]

    team = repo.create_team_with_newsletter(
        name=payload.team_name,
        description="Auto-created for admin testing",
        admin_id=UUID(user_id),
        topic_ids=topic_ids,
        frequency="weekly",
        delivery_time_str="09:00",
        delivery_day=0,
        timezone_str="UTC",
    )

    nl = repo.get_newsletter(team.id)
    logger.info(f"ADMIN | test-create-team | team_id={team.id} name={team.name}")
    return {
        "status": "created",
        "team_id": str(team.id),
        "team_name": team.name,
        "newsletter_id": str(nl.id) if nl else None,
        "newsletter_topics": [t.name for t in topics],
        "schedule": repo.schedule_label(nl) if nl else None,
    }


@router.post("/teams/{team_id}/test-invite")
async def test_team_invite(
    team_id: UUID,
    payload: TestTeamInviteRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Invite an email to a team and send the invitation email."""
    _check_admin_enabled()
    from app.repositories.team_repository import TeamRepository
    from app.models.user import User

    repo = TeamRepository(db)
    if not repo.is_admin(team_id, UUID(user_id)):
        raise HTTPException(status_code=403, detail="Not team admin")

    team = repo.get_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    admin = db.query(User).filter(User.id == UUID(user_id)).first()

    member, invitation = repo.invite_member(
        team_id=team_id,
        email=str(payload.email),
        role="member",
        invited_by_email=admin.email if admin else None,
    )

    if invitation is None:
        return {
            "status": "already_accepted",
            "email": str(payload.email),
            "message": "Member already accepted.",
        }

    accept_url = f"{settings.FRONTEND_URL}/team-invite/{invitation.token}"
    decline_url = f"{settings.FRONTEND_URL}/team-invite/{invitation.token}?action=decline"

    from jinja2 import Environment, FileSystemLoader
    import os
    template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
    env = Environment(loader=FileSystemLoader(template_dir))
    nl = team.newsletters[0] if team.newsletters else None
    topics = [nt.topic.name for nt in (nl.topics or []) if nt.topic] if nl else []
    from app.repositories.team_repository import _schedule_label as _sl
    schedule = _sl(nl.frequency, nl.delivery_day, nl.delivery_time, nl.timezone) if nl else ""
    html_body = env.get_template("invitation_email.html").render(
        team_name=team.name,
        invited_by_email=admin.email if admin else "A team admin",
        accept_url=accept_url,
        decline_url=decline_url,
        expires_at=invitation.expires_at.strftime("%B %d, %Y at %H:%M UTC"),
        topics=topics,
        schedule_label=schedule,
        frontend_url=settings.FRONTEND_URL,
        year=datetime.now(timezone.utc).year,
    )

    email_client = EmailClient()
    email_sent = email_client.send_email(
        recipient=str(payload.email),
        subject=f"📚 You're invited to join {team.name} on MS Learn Digest",
        html_body=html_body,
    )

    logger.info(
        f"ADMIN | test-invite | team={team.name} to={payload.email} "
        f"token={invitation.token[:8]}… email_sent={email_sent}"
    )

    return {
        "status": "invited",
        "email": str(payload.email),
        "member_id": str(member.id),
        "member_status": member.status,
        "invitation_token": invitation.token,
        "invite_url": accept_url,
        "expires_at": invitation.expires_at.isoformat(),
        "email_sent": email_sent,
    }


@router.post("/teams/invite/{token}/accept")
async def admin_accept_invite(
    token: str,
    db: Session = Depends(get_db),
):
    """
    Accept an invitation without requiring the invitee to be logged in.
    Useful for testing the acceptance flow end-to-end in the admin panel.
    """
    _check_admin_enabled()
    from app.repositories.team_repository import TeamRepository

    repo = TeamRepository(db)
    member = repo.accept_invitation(token=token)
    if not member:
        raise HTTPException(
            status_code=410,
            detail="Invitation is invalid, expired, or already used.",
        )
    logger.info(f"ADMIN | accept-invite | email={member.email} member_id={member.id}")
    return {
        "status": "accepted",
        "email": member.email,
        "member_id": str(member.id),
        "member_status": member.status,
        "joined_at": member.joined_at.isoformat() if member.joined_at else None,
    }


@router.post("/teams/{team_id}/test-digest")
async def test_team_digest(
    team_id: UUID,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Generate and send a team digest to all accepted members.
    Uses catalog_cache + Groq — same as the scheduled flow.
    """
    _check_admin_enabled()
    from app.repositories.team_repository import TeamRepository

    repo = TeamRepository(db)
    if not repo.is_admin(team_id, UUID(user_id)):
        raise HTTPException(status_code=403, detail="Not team admin")

    newsletter = repo.get_newsletter(team_id)
    if not newsletter:
        raise HTTPException(status_code=400, detail="Team has no newsletter configured.")

    team = repo.get_by_id(team_id)
    accepted_members = [m for m in (team.members or []) if m.status == "accepted"] if team else []

    catalog_total = db.query(CatalogCache).count()
    if catalog_total == 0:
        return {
            "status": "no_content",
            "message": "catalog_cache is empty — run POST /api/admin/catalog-sync first.",
            "catalog_total": 0,
        }

    generator = DigestGenerator(db, dispatch_cache={})
    result = await generator.generate_and_send_for_newsletter(newsletter)

    latest = (
        db.query(Digest)
        .filter(Digest.newsletter_id == newsletter.id)
        .order_by(Digest.created_at.desc())
        .first()
    )

    logger.info(
        f"ADMIN | test-team-digest | team_id={team_id} "
        f"newsletter='{newsletter.name}' result={result} "
        f"accepted_members={len(accepted_members)}"
    )

    return {
        "status": "sent" if result else "no_content",
        "newsletter": newsletter.name,
        "digest_id": str(latest.id) if latest else None,
        "accepted_members": len(accepted_members),
        "catalog_total": catalog_total,
    }


@router.get("/teams/{team_id}/delivery-status")
async def team_delivery_status(
    team_id: UUID,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """View team membership stats and recent digest delivery history."""
    _check_admin_enabled()
    from app.repositories.team_repository import TeamRepository, _schedule_label

    repo = TeamRepository(db)
    if not repo.is_admin(team_id, UUID(user_id)):
        raise HTTPException(status_code=403, detail="Not team admin")

    team = repo.get_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    members = team.members or []
    by_status: dict = {}
    for m in members:
        by_status.setdefault(m.status, []).append(m.email)

    nl = team.newsletters[0] if team.newsletters else None

    recent_digests = (
        db.query(Digest)
        .filter(Digest.team_id == team_id)
        .order_by(Digest.created_at.desc())
        .limit(10)
        .all()
    )

    return {
        "team_id": str(team_id),
        "team_name": team.name,
        "member_count": len(members),
        "by_status": {k: {"count": len(v), "emails": v} for k, v in by_status.items()},
        "accepted_count": len(by_status.get("accepted", [])),
        "pending_count": len(by_status.get("pending", [])),
        "declined_count": len(by_status.get("declined", [])),
        "expired_count": len(by_status.get("expired", [])),
        "removed_count": len(by_status.get("removed", [])),
        "newsletter": {
            "id": str(nl.id),
            "name": nl.name,
            "frequency": nl.frequency,
            "is_active": nl.is_active,
            "schedule": _schedule_label(nl.frequency, nl.delivery_day, nl.delivery_time, nl.timezone),
            "topics": [nt.topic.name for nt in (nl.topics or []) if nt.topic],
        } if nl else None,
        "recent_digests": [
            {
                "id": str(d.id),
                "title": d.title,
                "status": d.status,
                "recipient_count": d.recipient_count,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "sent_at": d.sent_at.isoformat() if d.sent_at else None,
            }
            for d in recent_digests
        ],
    }


# ── Topic hierarchy repair ─────────────────────────────────────────────────────

@router.post("/repair-topics")
async def repair_topic_hierarchy(db: Session = Depends(get_db)):
    """
    Re-seed and repair the hierarchical topic tree.

    Useful when the DB was seeded with the old flat topic list and needs
    to be re-parented to the new hierarchy without losing existing
    user subscriptions.  Safe to run multiple times.
    """
    _check_admin_enabled()
    from app.repositories.topic_repository import TopicRepository
    from sqlalchemy import func as sqlfunc

    repo = TopicRepository(db)

    before_count = db.query(sqlfunc.count(repo.db.query.__class__)).scalar() if False else \
        db.execute(__import__('sqlalchemy').text("SELECT COUNT(*) FROM topics")).scalar()

    inserted = repo.seed_system_topics()

    after_count = db.execute(__import__('sqlalchemy').text("SELECT COUNT(*) FROM topics")).scalar()

    # Count topics by level
    level_counts = db.execute(
        __import__('sqlalchemy').text(
            "SELECT level, COUNT(*) FROM topics WHERE is_active = true GROUP BY level ORDER BY level"
        )
    ).fetchall()

    return {
        "status": "ok",
        "topics_before": before_count,
        "topics_after": after_count,
        "newly_inserted": inserted,
        "by_level": {f"level_{row[0]}": row[1] for row in level_counts},
        "message": (
            f"Inserted {inserted} new topics and repaired hierarchy."
            if inserted else
            "No new topics needed — hierarchy verified."
        ),
    }


# ── Learning Engine test endpoints ────────────────────────────────────────────

@router.get("/learning/status")
async def admin_learning_status(db: Session = Depends(get_db)):
    """
    Show learning engine status: tables, topics, modules, active subscriptions.
    """
    _check_admin_enabled()
    from sqlalchemy import text, func
    from app.repositories.learning_repository import LearningRepository

    try:
        topic_count = db.execute(text("SELECT COUNT(*) FROM learning_topics")).scalar()
        module_count = db.execute(text("SELECT COUNT(*) FROM learning_modules")).scalar()
        sub_count = db.execute(
            text("SELECT COUNT(*) FROM user_learning_subscriptions WHERE status='active'")
        ).scalar()
        lesson_count = db.execute(text("SELECT COUNT(*) FROM generated_lessons")).scalar()

        repo = LearningRepository(db)
        topics = repo.get_all_topics()

        return {
            "status": "ok",
            "topics": topic_count,
            "modules": module_count,
            "active_subscriptions": sub_count,
            "generated_lessons_cached": lesson_count,
            "topic_breakdown": [
                {"name": t.name, "modules": t.total_modules, "slug": t.slug}
                for t in topics
            ],
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@router.post("/learning/send-lesson")
async def admin_send_learning_lesson(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Immediately deliver the next lesson for ALL of the current user's
    active learning subscriptions. Useful for testing without waiting
    for the scheduler.
    """
    _check_admin_enabled()
    from app.repositories.learning_repository import LearningRepository
    from app.services.learning.newsletter_generator import LearningNewsletterGenerator

    uid = UUID(user_id)
    repo = LearningRepository(db)
    subs = repo.get_user_subscriptions(uid)
    active = [s for s in subs if s.status == "active"]

    if not active:
        return {
            "status": "no_subscriptions",
            "message": "You have no active learning subscriptions. "
                       "Go to Learning Center and enroll in a track first.",
        }

    generator = LearningNewsletterGenerator(db)
    results = []

    for sub in active:
        topic_name = sub.topic.name if sub.topic else str(sub.topic_id)
        try:
            sent = await generator.deliver(sub)
            results.append({
                "topic": topic_name,
                "module": sub.current_module_sequence,
                "status": "sent" if sent else "failed",
            })
            logger.info(
                f"ADMIN | send-learning-lesson | user={user_id} "
                f"topic={topic_name} status={'sent' if sent else 'failed'}"
            )
        except Exception as exc:
            logger.error(
                f"ADMIN | send-learning-lesson | FAILED | "
                f"user={user_id} topic={topic_name} | {exc}",
                exc_info=True,
            )
            results.append({
                "topic": topic_name,
                "module": sub.current_module_sequence,
                "status": "error",
                "error": str(exc),
            })

    sent_count = sum(1 for r in results if r["status"] == "sent")
    return {
        "status": "completed",
        "sent": sent_count,
        "total": len(results),
        "results": results,
    }
