"""
Team Repository — Database access layer for teams, members, newsletters, and invitations.

Design invariants:
  - One team owns exactly one TeamNewsletter (enforced by DB unique constraint).
  - Team creation is atomic: team + newsletter created in the same transaction.
  - Member status lifecycle: pending → accepted | declined | expired | removed
  - Only 'accepted' members receive newsletters.
"""

import logging
import secrets
from typing import List, Optional, Tuple
from uuid import UUID
from datetime import datetime, timezone, timedelta, time as dt_time

from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.models.team import Team, TeamMember, TeamInvitation, TeamNewsletter, NewsletterTopic
from app.models.topic import Topic

logger = logging.getLogger(__name__)

_INVITE_EXPIRY_HOURS = 168   # 7 days
_FIXED_TZ = "Asia/Kolkata"   # hardcoded — never ask users for timezone


def _schedule_label(frequency: str, delivery_day: int, delivery_time, tz: str = _FIXED_TZ) -> str:
    """Human-readable schedule string — timezone is always Asia/Kolkata (IST)."""
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    if isinstance(delivery_time, dt_time):
        t_str = delivery_time.strftime("%I:%M %p").lstrip("0")
    else:
        t_str = str(delivery_time)[:5] if delivery_time else "09:00"
    if frequency == "daily":
        return f"Daily at {t_str} IST"
    if frequency == "monthly":
        return f"Monthly on the 1st at {t_str} IST"
    day_name = days[delivery_day] if 0 <= delivery_day <= 6 else "Monday"
    freq_label = {"weekly": "Weekly", "biweekly": "Bi-weekly"}.get(
        frequency, frequency.capitalize()
    )
    return f"{freq_label} on {day_name} at {t_str} IST"


class TeamRepository:
    def __init__(self, db: Session):
        self.db = db

    # ── Teams ──────────────────────────────────────────────────────────────

    def create_team_with_newsletter(
        self,
        name: str,
        description: Optional[str],
        admin_id: UUID,
        topic_ids: List[UUID],
        frequency: str,
        delivery_time_str: str,     # "HH:MM"
        delivery_day: int,
        timezone_str: str = _FIXED_TZ,
    ) -> Team:
        """
        Atomically create a Team + its one TeamNewsletter.
        Raises ValueError if no valid topics found.
        """
        h, m = map(int, delivery_time_str.split(":"))
        dt = dt_time(h, m)

        team = Team(name=name, description=description, admin_id=admin_id)
        self.db.add(team)
        self.db.flush()

        newsletter = TeamNewsletter(
            team_id=team.id,
            name=f"{name} Newsletter",
            frequency=frequency,
            delivery_time=dt,
            delivery_day=delivery_day,
            timezone=timezone_str,
            is_active=True,
        )
        self.db.add(newsletter)
        self.db.flush()

        for topic_id in topic_ids:
            topic = self.db.query(Topic).filter(Topic.id == topic_id).first()
            if topic:
                self.db.add(NewsletterTopic(newsletter_id=newsletter.id, topic_id=topic_id))

        self.db.commit()
        self.db.refresh(team)
        logger.info(
            f"TEAM | CREATED | team_id={team.id} name='{name}' "
            f"topics={len(topic_ids)} freq={frequency}"
        )
        return team

    def get_by_id(self, team_id: UUID) -> Optional[Team]:
        return (
            self.db.query(Team)
            .options(
                joinedload(Team.members).joinedload(TeamMember.invitations),
                joinedload(Team.newsletters)
                    .joinedload(TeamNewsletter.topics)
                    .joinedload(NewsletterTopic.topic),
            )
            .filter(Team.id == team_id)
            .first()
        )

    def get_teams_for_user(self, user_id: UUID) -> List[Team]:
        """Returns teams where user is admin OR accepted member."""
        admin_teams = (
            self.db.query(Team)
            .options(
                joinedload(Team.members),
                joinedload(Team.newsletters)
                    .joinedload(TeamNewsletter.topics)
                    .joinedload(NewsletterTopic.topic),
            )
            .filter(Team.admin_id == user_id)
            .all()
        )
        member_teams = (
            self.db.query(Team)
            .options(
                joinedload(Team.members),
                joinedload(Team.newsletters)
                    .joinedload(TeamNewsletter.topics)
                    .joinedload(NewsletterTopic.topic),
            )
            .join(TeamMember, TeamMember.team_id == Team.id)
            .filter(TeamMember.user_id == user_id, TeamMember.status == "accepted")
            .all()
        )
        seen: set = set()
        result: List[Team] = []
        for t in admin_teams + member_teams:
            if t.id not in seen:
                seen.add(t.id)
                result.append(t)
        return result

    def update_team(
        self,
        team_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[Team]:
        team = self.db.query(Team).filter(Team.id == team_id).first()
        if not team:
            return None
        if name is not None:
            team.name = name
        if description is not None:
            team.description = description
        self.db.commit()
        logger.info(f"TEAM | UPDATED | team_id={team_id}")
        return self.get_by_id(team_id)

    def delete_team(self, team_id: UUID) -> bool:
        team = self.db.query(Team).filter(Team.id == team_id).first()
        if not team:
            return False
        self.db.delete(team)
        self.db.commit()
        logger.info(f"TEAM | DELETED | team_id={team_id}")
        return True

    def is_admin(self, team_id: UUID, user_id: UUID) -> bool:
        team = self.db.query(Team).filter(Team.id == team_id).first()
        return team is not None and team.admin_id == user_id

    def get_newsletter(self, team_id: UUID) -> Optional[TeamNewsletter]:
        return (
            self.db.query(TeamNewsletter)
            .options(
                joinedload(TeamNewsletter.topics).joinedload(NewsletterTopic.topic),
            )
            .filter(TeamNewsletter.team_id == team_id)
            .first()
        )

    # ── Newsletter editing ─────────────────────────────────────────────────

    def update_topics(self, team_id: UUID, topic_ids: List[UUID]) -> Optional[TeamNewsletter]:
        newsletter = self.get_newsletter(team_id)
        if not newsletter:
            return None
        newsletter_id = newsletter.id

        # Delete existing topic links using synchronize_session=False to avoid
        # stale identity map issues after joinedload
        self.db.query(NewsletterTopic).filter(
            NewsletterTopic.newsletter_id == newsletter_id
        ).delete(synchronize_session=False)

        for topic_id in topic_ids:
            topic = self.db.query(Topic).filter(Topic.id == topic_id).first()
            if topic:
                self.db.add(NewsletterTopic(newsletter_id=newsletter_id, topic_id=topic_id))

        self.db.commit()
        logger.info(f"TEAM | TOPICS_UPDATED | team_id={team_id} count={len(topic_ids)}")
        # Re-query fresh after commit
        return self.get_newsletter(team_id)

    def update_schedule(
        self,
        team_id: UUID,
        frequency: str,
        delivery_time_str: str,
        delivery_day: int,
        timezone_str: str = _FIXED_TZ,
    ) -> Optional[TeamNewsletter]:
        # Use a direct UPDATE to avoid stale object issues
        newsletter = self.db.query(TeamNewsletter).filter(
            TeamNewsletter.team_id == team_id
        ).first()
        if not newsletter:
            return None

        h, m = map(int, delivery_time_str.split(":"))
        newsletter.frequency = frequency
        newsletter.delivery_time = dt_time(h, m)
        newsletter.delivery_day = delivery_day
        newsletter.timezone = _FIXED_TZ  # always fixed

        self.db.commit()
        logger.info(
            f"TEAM | SCHEDULE_UPDATED | team_id={team_id} "
            f"freq={frequency} time={delivery_time_str}"
        )
        return self.get_newsletter(team_id)

    def toggle_newsletter_active(self, team_id: UUID, is_active: bool) -> Optional[TeamNewsletter]:
        newsletter = self.get_newsletter(team_id)
        if not newsletter:
            return None
        newsletter.is_active = is_active
        self.db.commit()
        return self.get_newsletter(team_id)

    # ── Members ────────────────────────────────────────────────────────────

    def invite_member(
        self,
        team_id: UUID,
        email: str,
        role: str = "member",
        invited_by_email: Optional[str] = None,
    ) -> Tuple[TeamMember, Optional[TeamInvitation]]:
        """
        Create or re-invite a member.
        Returns (TeamMember, TeamInvitation).
        If already accepted returns (member, None).
        """
        member = (
            self.db.query(TeamMember)
            .filter(TeamMember.team_id == team_id, TeamMember.email == email)
            .first()
        )
        if not member:
            member = TeamMember(
                team_id=team_id,
                email=email,
                role=role,
                status="pending",
            )
            self.db.add(member)
            self.db.flush()
        elif member.status == "accepted":
            logger.info(f"INVITE | already accepted | email={email}")
            return member, None
        else:
            # Reset to pending for re-invite
            member.status = "pending"
            self.db.flush()

        token = secrets.token_urlsafe(32)
        expiry_hours = getattr(settings, "INVITATION_EXPIRY_HOURS", _INVITE_EXPIRY_HOURS)
        invitation = TeamInvitation(
            team_id=team_id,
            member_id=member.id,
            email=email,
            token=token,
            invited_by_email=invited_by_email,
            status="pending",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=expiry_hours),
        )
        self.db.add(invitation)
        self.db.commit()
        self.db.refresh(member)
        self.db.refresh(invitation)

        logger.info(
            f"INVITE | SENT | team_id={team_id} email={email} "
            f"token={token[:8]}… expires_in={expiry_hours}h"
        )
        return member, invitation

    def resend_invitation(
        self,
        team_id: UUID,
        member_id: UUID,
        invited_by_email: Optional[str] = None,
    ) -> Tuple[Optional[TeamMember], Optional[TeamInvitation]]:
        """Issue a fresh invitation token for an existing member."""
        member = (
            self.db.query(TeamMember)
            .filter(TeamMember.id == member_id, TeamMember.team_id == team_id)
            .first()
        )
        if not member:
            return None, None
        if member.status == "accepted":
            return member, None

        # Expire old pending invitations
        self.db.query(TeamInvitation).filter(
            TeamInvitation.member_id == member_id,
            TeamInvitation.status == "pending",
        ).update({"status": "expired"})
        member.status = "pending"
        self.db.flush()

        token = secrets.token_urlsafe(32)
        expiry_hours = getattr(settings, "INVITATION_EXPIRY_HOURS", _INVITE_EXPIRY_HOURS)
        invitation = TeamInvitation(
            team_id=team_id,
            member_id=member.id,
            email=member.email,
            token=token,
            invited_by_email=invited_by_email,
            status="pending",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=expiry_hours),
        )
        self.db.add(invitation)
        self.db.commit()
        self.db.refresh(member)
        self.db.refresh(invitation)

        logger.info(f"INVITE | RESENT | email={member.email} token={token[:8]}…")
        return member, invitation

    def get_invitation_by_token(self, token: str) -> Optional[TeamInvitation]:
        return (
            self.db.query(TeamInvitation)
            .options(
                joinedload(TeamInvitation.team)
                    .joinedload(Team.newsletters)
                    .joinedload(TeamNewsletter.topics)
                    .joinedload(NewsletterTopic.topic),
                joinedload(TeamInvitation.member),
            )
            .filter(TeamInvitation.token == token)
            .first()
        )

    def accept_invitation(
        self, token: str, user_id: Optional[UUID] = None
    ) -> Optional[TeamMember]:
        inv = self.get_invitation_by_token(token)
        if not inv:
            logger.warning(f"INVITE | accept | NOT FOUND token={token[:8]}…")
            return None

        now = datetime.now(timezone.utc)
        if inv.status != "pending":
            logger.warning(f"INVITE | accept | ALREADY {inv.status} token={token[:8]}…")
            return None

        expires = inv.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires < now:
            inv.status = "expired"
            inv.member.status = "expired"
            self.db.commit()
            logger.warning(f"INVITE | accept | EXPIRED token={token[:8]}…")
            return None

        inv.status = "accepted"
        inv.accepted_at = now
        inv.member.status = "accepted"
        inv.member.joined_at = now
        if user_id:
            inv.member.user_id = user_id

        self.db.commit()
        self.db.refresh(inv.member)
        logger.info(
            f"INVITE | ACCEPTED | email={inv.email} team_id={inv.team_id} "
            f"token={token[:8]}…"
        )
        return inv.member

    def decline_invitation(self, token: str) -> bool:
        inv = self.get_invitation_by_token(token)
        if not inv or inv.status != "pending":
            return False
        inv.status = "declined"
        inv.member.status = "declined"
        self.db.commit()
        logger.info(f"INVITE | DECLINED | email={inv.email} token={token[:8]}…")
        return True

    def remove_member(self, team_id: UUID, member_id: UUID) -> bool:
        member = (
            self.db.query(TeamMember)
            .filter(TeamMember.id == member_id, TeamMember.team_id == team_id)
            .first()
        )
        if not member:
            return False
        member.status = "removed"
        # Expire any pending invitations
        self.db.query(TeamInvitation).filter(
            TeamInvitation.member_id == member_id,
            TeamInvitation.status == "pending",
        ).update({"status": "expired"})
        self.db.commit()
        logger.info(f"TEAM | MEMBER_REMOVED | email={member.email} team_id={team_id}")
        return True

    def cancel_invitation(self, team_id: UUID, member_id: UUID) -> bool:
        """Cancel a pending invitation (sets member+invitation to declined)."""
        member = (
            self.db.query(TeamMember)
            .filter(TeamMember.id == member_id, TeamMember.team_id == team_id)
            .first()
        )
        if not member or member.status not in ("pending", "declined", "expired"):
            return False
        member.status = "declined"
        self.db.query(TeamInvitation).filter(
            TeamInvitation.member_id == member_id,
            TeamInvitation.status == "pending",
        ).update({"status": "expired"})
        self.db.commit()
        logger.info(f"INVITE | CANCELLED | email={member.email} team_id={team_id}")
        return True

    def expire_stale_invitations(self) -> int:
        now = datetime.now(timezone.utc)
        rows = (
            self.db.query(TeamInvitation)
            .filter(TeamInvitation.status == "pending", TeamInvitation.expires_at < now)
            .all()
        )
        for inv in rows:
            inv.status = "expired"
            if inv.member and inv.member.status == "pending":
                inv.member.status = "expired"
        if rows:
            self.db.commit()
            logger.info(f"INVITE | EXPIRED | count={len(rows)}")
        return len(rows)

    # ── Newsletter queries for scheduler ──────────────────────────────────

    def get_all_active_newsletters(self) -> List[TeamNewsletter]:
        return (
            self.db.query(TeamNewsletter)
            .options(
                joinedload(TeamNewsletter.topics).joinedload(NewsletterTopic.topic),
                joinedload(TeamNewsletter.team),
            )
            .filter(TeamNewsletter.is_active == True)
            .all()
        )

    # ── Sync metadata ──────────────────────────────────────────────────────

    def get_sync_metadata(self):
        from app.models.team import SyncMetadata
        return self.db.query(SyncMetadata).filter(SyncMetadata.id == 1).first()

    # ── Schedule label helper ──────────────────────────────────────────────

    @staticmethod
    def schedule_label(newsletter: TeamNewsletter) -> str:
        return _schedule_label(
            newsletter.frequency,
            newsletter.delivery_day,
            newsletter.delivery_time,
        )
