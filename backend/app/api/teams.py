"""
Teams API

Design: one Team owns exactly one newsletter configuration.
The newsletter is created atomically with the team.

Endpoints
─────────
Teams
  GET    /teams/                          list teams for current user
  POST   /teams/                          create team + newsletter (atomic)
  GET    /teams/{id}                      get team detail
  PATCH  /teams/{id}                      update team name/description
  DELETE /teams/{id}                      delete team + all data

Newsletter (one per team)
  GET    /teams/{id}/newsletter           get newsletter config
  PATCH  /teams/{id}/newsletter/topics    replace topic list
  PATCH  /teams/{id}/newsletter/schedule  update schedule
  PATCH  /teams/{id}/newsletter/toggle    pause / resume

Members & Invitations
  POST   /teams/{id}/invite               invite member by email
  POST   /teams/{id}/members/{mid}/resend resend invitation
  DELETE /teams/{id}/members/{mid}        remove / cancel invite
  GET    /teams/invite/{token}            preview invite (public)
  POST   /teams/invite/{token}/accept     accept invite (authenticated)
  POST   /teams/invite/{token}/decline    decline invite (public)

Digest history
  GET    /teams/{id}/digests              recent digests for team
"""

import logging
import os
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user_id
from app.repositories.team_repository import TeamRepository
from app.schemas.team import (
    InviteMemberRequest,
    InvitePreviewResponse,
    InviteResult,
    TeamCreate,
    TeamDigestSummary,
    TeamMemberResponse,
    TeamNewsletterResponse,
    TeamResponse,
    TeamUpdate,
    UpdateScheduleRequest,
    UpdateTopicsRequest,
)
from app.services.email.smtp_client import EmailClient

logger = logging.getLogger(__name__)
router = APIRouter()

_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
_FREQ = {"daily": "Daily", "weekly": "Weekly", "biweekly": "Bi-weekly", "monthly": "Monthly"}


# ── Email helper ───────────────────────────────────────────────────────────────

def _render_invite_email(
    team_name: str,
    invited_by_email: str,
    accept_url: str,
    decline_url: str,
    expires_at: datetime,
    topics: List[str],
    schedule_label: str,
) -> str:
    template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
    env = Environment(loader=FileSystemLoader(template_dir))
    return env.get_template("invitation_email.html").render(
        team_name=team_name,
        invited_by_email=invited_by_email,
        accept_url=accept_url,
        decline_url=decline_url,
        expires_at=expires_at.strftime("%B %d, %Y at %H:%M UTC"),
        topics=topics,
        schedule_label=schedule_label,
        frontend_url=settings.FRONTEND_URL,
        year=datetime.now(timezone.utc).year,
    )


# ── IMPORTANT: static paths MUST come before /{team_id} ──────────────────────
# FastAPI matches routes in declaration order. /invite/{token} would be
# shadowed by /{team_id} if declared after it, causing 422 errors.

# ── Public invite endpoints ────────────────────────────────────────────────────

@router.get("/invite/{token}", response_model=InvitePreviewResponse)
async def preview_invitation(
    token: str,
    db: Session = Depends(get_db),
):
    """Public — no auth required. Returns team/topics info before the user accepts."""
    repo = TeamRepository(db)
    inv = repo.get_invitation_by_token(token)
    if not inv:
        raise HTTPException(status_code=404, detail="Invitation not found.")

    now = datetime.now(timezone.utc)
    expires = inv.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)

    if inv.status == "expired" or expires < now:
        raise HTTPException(status_code=410, detail="This invitation has expired.")
    if inv.status in ("accepted", "declined"):
        raise HTTPException(status_code=409, detail=f"This invitation has already been {inv.status}.")

    nl = inv.team.newsletters[0] if inv.team and inv.team.newsletters else None
    topics = [nt.topic.name for nt in (nl.topics if nl else []) if nt.topic]
    schedule = TeamRepository.schedule_label(nl) if nl else None

    return InvitePreviewResponse(
        team_id=inv.team_id,
        team_name=inv.team.name if inv.team else "Unknown Team",
        team_description=inv.team.description if inv.team else None,
        invited_by_email=inv.invited_by_email,
        email=inv.email,
        status=inv.status,
        expires_at=inv.expires_at,
        topics=topics,
        frequency=nl.frequency if nl else None,
        schedule_label=schedule,
    )


@router.post("/invite/{token}/accept", response_model=TeamMemberResponse)
async def accept_invitation(
    token: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Accept the invitation. Links membership to the authenticated user account."""
    repo = TeamRepository(db)
    member = repo.accept_invitation(token=token, user_id=UUID(user_id))
    if not member:
        raise HTTPException(
            status_code=410,
            detail="Invitation is invalid, expired, or has already been used.",
        )
    logger.info(f"INVITE | ACCEPTED | user_id={user_id} email={member.email}")
    return member


@router.post("/invite/{token}/decline")
async def decline_invitation(token: str, db: Session = Depends(get_db)):
    """Decline the invitation. No auth required."""
    repo = TeamRepository(db)
    ok = repo.decline_invitation(token)
    if not ok:
        raise HTTPException(
            status_code=410,
            detail="Invitation not found, already expired, or already responded to.",
        )
    return {"status": "declined"}


# ── Teams ──────────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[TeamResponse])
async def list_teams(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = TeamRepository(db)
    teams = repo.get_teams_for_user(UUID(user_id))
    return [_team_response(t) for t in teams]


@router.post("/", response_model=TeamResponse)
async def create_team(
    payload: TeamCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Create a team and its newsletter in one request."""
    if not payload.topic_ids:
        raise HTTPException(status_code=422, detail="At least one topic is required.")

    repo = TeamRepository(db)
    team = repo.create_team_with_newsletter(
        name=payload.name,
        description=payload.description,
        admin_id=UUID(user_id),
        topic_ids=payload.topic_ids,
        frequency=payload.frequency,
        delivery_time_str=payload.delivery_time,
        delivery_day=payload.delivery_day,
        # timezone_str defaults to Asia/Kolkata in the repository
    )
    return _team_response(repo.get_by_id(team.id))


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: UUID,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = TeamRepository(db)
    team = repo.get_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return _team_response(team)


@router.patch("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: UUID,
    payload: TeamUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = TeamRepository(db)
    if not repo.is_admin(team_id, UUID(user_id)):
        raise HTTPException(status_code=403, detail="Only team admins can update the team")
    team = repo.update_team(team_id, name=payload.name, description=payload.description)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return _team_response(team)


@router.delete("/{team_id}")
async def delete_team(
    team_id: UUID,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = TeamRepository(db)
    if not repo.is_admin(team_id, UUID(user_id)):
        raise HTTPException(status_code=403, detail="Only team admins can delete the team")
    ok = repo.delete_team(team_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Team not found")
    return {"status": "deleted", "team_id": str(team_id)}


# ── Newsletter (one per team) ──────────────────────────────────────────────────

@router.get("/{team_id}/newsletter", response_model=TeamNewsletterResponse)
async def get_newsletter(
    team_id: UUID,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = TeamRepository(db)
    nl = repo.get_newsletter(team_id)
    if not nl:
        raise HTTPException(status_code=404, detail="Newsletter not found for this team")
    return _nl_response(nl)


@router.patch("/{team_id}/newsletter/topics", response_model=TeamNewsletterResponse)
async def update_topics(
    team_id: UUID,
    payload: UpdateTopicsRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Replace the team newsletter's topic list."""
    repo = TeamRepository(db)
    if not repo.is_admin(team_id, UUID(user_id)):
        raise HTTPException(status_code=403, detail="Only team admins can edit topics")
    if not payload.topic_ids:
        raise HTTPException(status_code=422, detail="At least one topic is required")
    nl = repo.update_topics(team_id, payload.topic_ids)
    if not nl:
        raise HTTPException(status_code=404, detail="Newsletter not found")
    return _nl_response(nl)


@router.patch("/{team_id}/newsletter/schedule", response_model=TeamNewsletterResponse)
async def update_schedule(
    team_id: UUID,
    payload: UpdateScheduleRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Update delivery frequency, time, and day. Timezone is fixed to Asia/Kolkata."""
    repo = TeamRepository(db)
    if not repo.is_admin(team_id, UUID(user_id)):
        raise HTTPException(status_code=403, detail="Only team admins can edit the schedule")
    nl = repo.update_schedule(
        team_id=team_id,
        frequency=payload.frequency,
        delivery_time_str=payload.delivery_time,
        delivery_day=payload.delivery_day,
    )
    if not nl:
        raise HTTPException(status_code=404, detail="Newsletter not found")
    return _nl_response(nl)


@router.patch("/{team_id}/newsletter/toggle")
async def toggle_newsletter(
    team_id: UUID,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Pause or resume the team newsletter."""
    repo = TeamRepository(db)
    if not repo.is_admin(team_id, UUID(user_id)):
        raise HTTPException(status_code=403, detail="Admin only")
    nl = repo.get_newsletter(team_id)
    if not nl:
        raise HTTPException(status_code=404, detail="Newsletter not found")
    updated = repo.toggle_newsletter_active(team_id, not nl.is_active)
    return {"is_active": updated.is_active, "team_id": str(team_id)}


# ── Members & invitations ──────────────────────────────────────────────────────

@router.post("/{team_id}/invite", response_model=InviteResult)
async def invite_member(
    team_id: UUID,
    payload: InviteMemberRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Invite a member by email. Creates a PENDING member + sends invitation email."""
    repo = TeamRepository(db)
    if not repo.is_admin(team_id, UUID(user_id)):
        raise HTTPException(status_code=403, detail="Only team admins can invite members")

    team = repo.get_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    from app.models.user import User
    admin = db.query(User).filter(User.id == UUID(user_id)).first()
    invited_by_email = admin.email if admin else None

    member, invitation = repo.invite_member(
        team_id=team_id,
        email=str(payload.email),
        role=payload.role,
        invited_by_email=invited_by_email,
    )

    if invitation is None:
        raise HTTPException(
            status_code=409,
            detail=f"{payload.email} is already an accepted member of this team.",
        )

    accept_url = f"{settings.FRONTEND_URL}/team-invite/{invitation.token}"
    decline_url = f"{settings.FRONTEND_URL}/team-invite/{invitation.token}?action=decline"

    nl = team.newsletters[0] if team.newsletters else None
    topics: List[str] = [nt.topic.name for nt in (nl.topics if nl else []) if nt.topic]
    schedule = repo.schedule_label(nl) if nl else ""

    html_body = _render_invite_email(
        team_name=team.name,
        invited_by_email=invited_by_email or "A team admin",
        accept_url=accept_url,
        decline_url=decline_url,
        expires_at=invitation.expires_at,
        topics=topics,
        schedule_label=schedule,
    )
    email_sent = EmailClient().send_email(
        recipient=str(payload.email),
        subject=f"📚 You're invited to join {team.name} on MS Learn Digest",
        html_body=html_body,
    )
    logger.info(
        f"INVITE | team={team.name} to={payload.email} "
        f"token={invitation.token[:8]}… email_sent={email_sent}"
    )

    return InviteResult(
        member=TeamMemberResponse.model_validate(member),
        invitation_token=invitation.token,
        invitation_expires_at=invitation.expires_at,
        invite_url=accept_url,
        email_sent=email_sent,
    )


@router.post("/{team_id}/members/{member_id}/resend", response_model=InviteResult)
async def resend_invitation(
    team_id: UUID,
    member_id: UUID,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Resend a fresh invitation to a pending/declined/expired member."""
    repo = TeamRepository(db)
    if not repo.is_admin(team_id, UUID(user_id)):
        raise HTTPException(status_code=403, detail="Admin only")

    from app.models.user import User
    admin = db.query(User).filter(User.id == UUID(user_id)).first()

    member, invitation = repo.resend_invitation(
        team_id=team_id,
        member_id=member_id,
        invited_by_email=admin.email if admin else None,
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    if invitation is None:
        raise HTTPException(status_code=409, detail="Member is already accepted")

    team = repo.get_by_id(team_id)
    accept_url = f"{settings.FRONTEND_URL}/team-invite/{invitation.token}"
    decline_url = f"{settings.FRONTEND_URL}/team-invite/{invitation.token}?action=decline"
    nl = team.newsletters[0] if team and team.newsletters else None
    topics = [nt.topic.name for nt in (nl.topics if nl else []) if nt.topic]
    schedule = repo.schedule_label(nl) if nl else ""

    html_body = _render_invite_email(
        team_name=team.name if team else "Your Team",
        invited_by_email=admin.email if admin else "A team admin",
        accept_url=accept_url,
        decline_url=decline_url,
        expires_at=invitation.expires_at,
        topics=topics,
        schedule_label=schedule,
    )
    email_sent = EmailClient().send_email(
        recipient=member.email,
        subject=f"📚 Reminder: You're invited to join {team.name if team else 'a team'} on MS Learn Digest",
        html_body=html_body,
    )
    logger.info(f"INVITE | RESENT | email={member.email} email_sent={email_sent}")

    return InviteResult(
        member=TeamMemberResponse.model_validate(member),
        invitation_token=invitation.token,
        invitation_expires_at=invitation.expires_at,
        invite_url=accept_url,
        email_sent=email_sent,
    )


@router.delete("/{team_id}/members/{member_id}")
async def remove_member(
    team_id: UUID,
    member_id: UUID,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Remove an accepted member OR cancel a pending invitation."""
    repo = TeamRepository(db)
    if not repo.is_admin(team_id, UUID(user_id)):
        raise HTTPException(status_code=403, detail="Only team admins can remove members")
    removed = repo.remove_member(team_id=team_id, member_id=member_id)
    if not removed:
        ok = repo.cancel_invitation(team_id=team_id, member_id=member_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Member not found")
    return {"status": "removed"}


# ── Digest history ─────────────────────────────────────────────────────────────

@router.get("/{team_id}/digests", response_model=List[TeamDigestSummary])
async def list_team_digests(
    team_id: UUID,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    from app.models.digest import Digest
    repo = TeamRepository(db)
    team = repo.get_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    digests = (
        db.query(Digest)
        .filter(Digest.team_id == team_id)
        .order_by(Digest.created_at.desc())
        .limit(20)
        .all()
    )
    return digests


# ── Helpers: ORM → Pydantic (avoid session/lazy-load issues) ─────────────────

_FIXED_TZ = "Asia/Kolkata"


def _nl_response(nl_orm) -> "TeamNewsletterResponse":
    """Convert a TeamNewsletter ORM object to TeamNewsletterResponse safely."""
    from app.schemas.team import TeamNewsletterResponse, NewsletterTopicResponse
    from datetime import time as dt_time

    topic_responses = [
        NewsletterTopicResponse(
            id=nt.id,
            topic_id=nt.topic_id,
            topic_name=nt.topic.name if nt.topic else None,
            topic_slug=nt.topic.slug if nt.topic else None,
        )
        for nt in (nl_orm.topics or [])
    ]

    raw_dt = nl_orm.delivery_time
    if isinstance(raw_dt, dt_time):
        dt_str = raw_dt.strftime("%H:%M")
    elif raw_dt is not None:
        dt_str = str(raw_dt)[:5]
    else:
        dt_str = "09:00"

    return TeamNewsletterResponse(
        id=nl_orm.id,
        team_id=nl_orm.team_id,
        name=nl_orm.name,
        frequency=nl_orm.frequency or "weekly",
        delivery_time=dt_str,
        delivery_day=nl_orm.delivery_day if nl_orm.delivery_day is not None else 0,
        timezone=_FIXED_TZ,
        is_active=bool(nl_orm.is_active),
        created_at=nl_orm.created_at,
        updated_at=nl_orm.updated_at,
        topics=topic_responses,
    )


def _team_response(team) -> "TeamResponse":
    """Convert a Team ORM object to TeamResponse with a single newsletter."""
    from app.schemas.team import TeamResponse, TeamMemberResponse

    nl_orm = team.newsletters[0] if team.newsletters else None
    nl_schema = _nl_response(nl_orm) if nl_orm else None

    return TeamResponse(
        id=team.id,
        name=team.name,
        description=team.description,
        admin_id=team.admin_id,
        created_at=team.created_at,
        updated_at=team.updated_at,
        members=[TeamMemberResponse.model_validate(m) for m in (team.members or [])],
        newsletter=nl_schema,
    )
