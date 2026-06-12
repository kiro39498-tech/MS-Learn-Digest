"""
Digest Generator — Catalog-cache → Groq → Email

Flow per user/newsletter:
  1. Resolve subscribed topics → products_set + subjects_set
  2. Query catalog_cache WHERE last_modified >= window_start
     AND (products_json overlaps OR subjects_json overlaps)
  3. If no matches → skip
  4. Compute cache_key(topic_slugs, frequency, sorted UIDs)
  5. If cache_key in dispatch_cache → reuse pre-generated HTML (skip Groq)
  6. Else → single Groq call → render HTML → store in dispatch_cache
  7. Persist Digest + DigestItems (uid/title/url/content_type inline)
  8. Send email → mark_sent or mark_failed

LLM invocation rules:
  - Groq is called ONLY here, never during sync.
  - One call per unique (topic_set × frequency × content_set).
  - dispatch_cache is a plain dict scoped to one scheduler run — not persisted.
"""

import hashlib
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from jinja2 import Environment, FileSystemLoader
import os

from app.core.config import settings
from app.models.catalog_cache import CatalogCache
from app.models.topic import Topic, UserSubscription
from app.models.team import TeamNewsletter, TeamMember
from app.models.user import User
from app.repositories.digest_repository import DigestRepository
from app.repositories.topic_repository import TopicRepository  # noqa: F401 (used for type hints)
from app.services.ai.groq_client import GroqClient
from app.services.email.smtp_client import EmailClient

logger = logging.getLogger(__name__)

_WINDOWS: Dict[str, timedelta] = {
    "daily":    timedelta(days=1),
    "weekly":   timedelta(weeks=1),
    "biweekly": timedelta(weeks=2),
    "monthly":  timedelta(days=30),
}


def _lookback(frequency: str) -> datetime:
    return datetime.now(timezone.utc) - _WINDOWS.get(frequency, timedelta(weeks=1))


def _get_template_env() -> Environment:
    template_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates"
    )
    return Environment(loader=FileSystemLoader(template_dir))


def _compute_cache_key(
    topic_slugs: List[str],
    frequency: str,
    uids: List[str],
) -> str:
    payload = {
        "topics": sorted(topic_slugs),
        "freq": frequency,
        "uids": sorted(uids),
    }
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _match_topics(
    item: CatalogCache,
    products_set: set,
    subjects_set: set,
) -> bool:
    """True if the catalog item's products or subjects overlap with any subscribed topic."""
    item_products = set(item.products_json or [])
    item_subjects = set(item.subjects_json or [])
    return bool(item_products & products_set) or bool(item_subjects & subjects_set)


class DigestGenerator:
    def __init__(self, db: Session, dispatch_cache: Optional[Dict] = None):
        self.db = db
        self.digest_repo = DigestRepository(db)
        self.groq_client = GroqClient()
        self.email_client = EmailClient()
        self.env = _get_template_env()
        # Shared across all users in one scheduler run — avoids repeat Groq calls
        self.dispatch_cache: Dict[str, Dict] = dispatch_cache if dispatch_cache is not None else {}

    # ── Individual digest ──────────────────────────────────────────────────

    async def generate_and_send_for_user(self, user: User) -> bool:
        tag = f"user={user.email}"
        logger.info(f"DIGEST | {tag} | START")

        # 1. Resolve topic subscriptions
        subs = (
            self.db.query(UserSubscription)
            .filter(UserSubscription.user_id == user.id)
            .all()
        )
        if not subs:
            logger.warning(f"DIGEST | {tag} | SKIP | no subscriptions")
            return False

        topic_ids = [s.topic_id for s in subs]
        topics = self.db.query(Topic).filter(Topic.id.in_(topic_ids)).all()
        topic_slugs = [t.slug for t in topics]
        topic_names = [t.name for t in topics]

        products_set, subjects_set = _build_filter_sets(topics, db=self.db)
        logger.info(f"DIGEST | {tag} | topics={topic_names}")

        # 2. Frequency window
        freq = (user.preferences.frequency if user.preferences else None) or "weekly"
        since = _lookback(freq)
        logger.info(f"DIGEST | {tag} | frequency={freq} since={since.isoformat()}")

        # 3. Query catalog_cache
        matched = _query_catalog(self.db, since, products_set, subjects_set)
        logger.info(f"DIGEST | {tag} | matched_items={len(matched)}")

        if not matched:
            logger.warning(f"DIGEST | {tag} | NO_CONTENT | no matching catalog items in window")
            # Record the check so the dashboard shows "Last checked: …"
            self.digest_repo.create_digest(
                title=f"Your {freq.capitalize()} MS Learn Digest — No Updates",
                digest_type="individual",
                content_html="",
                content_json={"status": "no_content", "freq": freq, "topics": topic_slugs},
                topic_names=topic_names,
                period_start=since,
                period_end=datetime.now(timezone.utc),
                user_id=user.id,
                status="no_content",
            )
            self.db.commit()
            return False

        # 4-6. Cache check / Groq call
        cache_key = _compute_cache_key(topic_slugs, freq, [m.uid for m in matched])
        generated = await _get_or_generate(
            cache_key=cache_key,
            dispatch_cache=self.dispatch_cache,
            groq_client=self.groq_client,
            env=self.env,
            matched=matched,
            topic_names=topic_names,
            topic_slugs=topic_slugs,
            freq=freq,
            user_name=user.name.split(" ")[0] if user.name else "Learner",
            tag=tag,
        )

        # 7. Persist
        digest = self.digest_repo.create_digest(
            title=f"Your {freq.capitalize()} MS Learn Digest",
            digest_type="individual",
            content_html=generated["html"],
            content_json=generated["content_json"],
            topic_names=topic_names,
            period_start=since,
            period_end=datetime.now(timezone.utc),
            user_id=user.id,
        )
        for i, item in enumerate(matched):
            self.digest_repo.add_item(
                digest_id=digest.id,
                uid=item.uid,
                title=item.title,
                url=item.url,
                content_type=item.content_type,
                position=i,
                section="ms_learn_updates",
            )
        self.db.commit()
        logger.info(f"DIGEST | {tag} | digest_saved | id={digest.id}")

        # 8. Send
        subject = f"📚 Your {freq.capitalize()} MS Learn Digest — {len(matched)} updates"
        sent = self.email_client.send_email(
            recipient=user.email,
            subject=subject,
            html_body=generated["html"],
        )
        if sent:
            self.digest_repo.mark_sent(digest.id, recipient_count=1)
            logger.info(f"DIGEST | {tag} | EMAIL SENT | id={digest.id}")
        else:
            self.digest_repo.mark_failed(digest.id)
            logger.error(f"DIGEST | {tag} | EMAIL FAILED | id={digest.id}")

        return sent

    # ── Team newsletter digest ─────────────────────────────────────────────

    async def generate_and_send_for_newsletter(self, newsletter: TeamNewsletter) -> bool:
        tag = f"newsletter='{newsletter.name}'"
        logger.info(f"DIGEST | {tag} | START")

        topic_slugs = [nt.topic.slug for nt in newsletter.topics if nt.topic]
        topic_names = [nt.topic.name for nt in newsletter.topics if nt.topic]
        topics = [nt.topic for nt in newsletter.topics if nt.topic]
        products_set, subjects_set = _build_filter_sets(topics, db=self.db)
        logger.info(f"DIGEST | {tag} | topics={topic_names}")

        freq = newsletter.frequency or "weekly"
        since = _lookback(freq)
        logger.info(f"DIGEST | {tag} | frequency={freq} since={since.isoformat()}")

        matched = _query_catalog(self.db, since, products_set, subjects_set)
        logger.info(f"DIGEST | {tag} | matched_items={len(matched)}")

        if not matched:
            logger.warning(f"DIGEST | {tag} | NO_CONTENT | no matching catalog items in window")
            # Record the check in digest history — no email sent
            self.digest_repo.create_digest(
                title=f"{newsletter.name} — No Updates This {freq.capitalize()}",
                digest_type="team",
                content_html="",
                content_json={"status": "no_content", "freq": freq, "topics": topic_slugs},
                topic_names=topic_names,
                period_start=since,
                period_end=datetime.now(timezone.utc),
                team_id=newsletter.team_id,
                newsletter_id=newsletter.id,
                status="no_content",
            )
            self.db.commit()
            return False

        members = (
            self.db.query(TeamMember)
            .filter(TeamMember.team_id == newsletter.team_id, TeamMember.status == "accepted")
            .all()
        )
        if not members:
            logger.warning(f"DIGEST | {tag} | SKIP | no accepted members")
            return False

        # One Groq call per unique content set — shared across all members
        cache_key = _compute_cache_key(topic_slugs, freq, [m.uid for m in matched])
        generated = await _get_or_generate(
            cache_key=cache_key,
            dispatch_cache=self.dispatch_cache,
            groq_client=self.groq_client,
            env=self.env,
            matched=matched,
            topic_names=topic_names,
            topic_slugs=topic_slugs,
            freq=freq,
            user_name="Team",
            tag=tag,
        )

        # Persist ONE digest for the whole team
        digest = self.digest_repo.create_digest(
            title=f"{newsletter.name} — {newsletter.team.name}",
            digest_type="team",
            content_html=generated["html"],
            content_json=generated["content_json"],
            topic_names=topic_names,
            period_start=since,
            period_end=datetime.now(timezone.utc),
            team_id=newsletter.team_id,
            newsletter_id=newsletter.id,
        )
        for i, item in enumerate(matched):
            self.digest_repo.add_item(
                digest_id=digest.id,
                uid=item.uid,
                title=item.title,
                url=item.url,
                content_type=item.content_type,
                position=i,
                section="ms_learn_updates",
            )
        self.db.commit()
        logger.info(f"DIGEST | {tag} | digest_saved | id={digest.id}")

        # Send same HTML to every active member
        subject = f"📚 {newsletter.name} — {len(matched)} Microsoft Learn updates"
        sent_count = 0
        for member in members:
            ok = self.email_client.send_email(
                recipient=member.email,
                subject=subject,
                html_body=generated["html"],
            )
            if ok:
                sent_count += 1
                logger.info(f"DIGEST | {tag} | SENT | to={member.email}")
            else:
                logger.error(f"DIGEST | {tag} | FAILED | to={member.email}")

        if sent_count > 0:
            self.digest_repo.mark_sent(digest.id, recipient_count=sent_count)
        else:
            self.digest_repo.mark_failed(digest.id)

        logger.info(f"DIGEST | {tag} | DONE | sent={sent_count}/{len(members)}")
        return sent_count > 0


# ── Module-level helpers (no instance state) ──────────────────────────────────

def _build_filter_sets(topics: List[Topic], db: Session = None):
    """
    Build product/subject filter sets from a list of subscribed topics.

    If db is provided, resolve descendant topic IDs first so that subscribing
    to a parent (e.g. "Azure") automatically includes all child topic filters
    (Azure → Networking, Azure → Compute, …).
    """
    if db is not None and topics:
        from app.repositories.topic_repository import TopicRepository
        repo = TopicRepository(db)
        subscribed_ids = [t.id for t in topics]
        all_ids = repo.resolve_descendant_ids(subscribed_ids)
        if all_ids != set(subscribed_ids):
            # Reload topics including descendants
            extra_ids = all_ids - set(subscribed_ids)
            extra_topics = db.query(Topic).filter(Topic.id.in_(extra_ids)).all()
            topics = list(topics) + extra_topics

    products: set = set()
    subjects: set = set()
    for t in topics:
        products.update(t.catalog_products or [])
        subjects.update(t.catalog_subjects or [])
    return products, subjects


def _query_catalog(
    db: Session,
    since: datetime,
    products_set: set,
    subjects_set: set,
    limit: int = 50,
) -> List[CatalogCache]:
    """
    Fetch catalog_cache rows modified within [since, now].
    Topic filtering is done in Python (set intersection) after the DB query
    returns the (usually small) candidate set.
    """
    candidates = (
        db.query(CatalogCache)
        .filter(CatalogCache.last_modified >= since)
        .order_by(CatalogCache.last_modified.desc())
        .limit(limit * 4)   # over-fetch, then filter
        .all()
    )
    matched = [c for c in candidates if _match_topics(c, products_set, subjects_set)]
    return matched[:limit]


async def _get_or_generate(
    cache_key: str,
    dispatch_cache: Dict,
    groq_client: GroqClient,
    env: Environment,
    matched: List[CatalogCache],
    topic_names: List[str],
    topic_slugs: List[str],
    freq: str,
    user_name: str,
    tag: str,
) -> Dict[str, Any]:
    """
    Return cached HTML if available for this cache_key, otherwise call Groq
    and render the template. Stores the result in dispatch_cache.
    """
    if cache_key in dispatch_cache:
        logger.info(f"DIGEST | {tag} | CACHE HIT | key={cache_key}")
        # Re-render with the correct user_name greeting
        cached = dispatch_cache[cache_key]
        html = _render(env, user_name, topic_names, freq, cached["ai_result"], matched)
        return {"html": html, "content_json": cached["content_json"]}

    logger.info(f"DIGEST | {tag} | CACHE MISS | key={cache_key} | calling Groq")

    groq_payload = [
        {
            "uid": item.uid,
            "title": item.title,
            "summary": (item.summary or "")[:500],
        }
        for item in matched
    ]

    try:
        ai_result = await groq_client.generate_digest(
            items=groq_payload,
            topic_names=topic_names,
            frequency=freq,
        )
    except Exception as exc:
        # Groq fallback: build a minimal ai_result from catalog metadata
        # so digest delivery is never blocked by an LLM failure.
        logger.warning(
            f"DIGEST | {tag} | GROQ FALLBACK | Groq failed ({exc}). "
            f"Generating newsletter from catalog summaries only."
        )
        ai_result = {
            "executive_summary": (
                f"Here are {len(matched)} Microsoft Learn updates "
                f"for your subscribed topics: {', '.join(topic_names)}."
            ),
            "items": [
                {
                    "uid": item.uid,
                    "newsletter_summary": item.summary or f"New content: {item.title}",
                    "why_it_matters": "Expand your Microsoft Learn expertise.",
                    "key_takeaways": [],
                }
                for item in matched
            ],
        }

    content_json = {
        "cache_key": cache_key,
        "freq": freq,
        "topics": topic_slugs,
        "item_count": len(matched),
        "executive_summary": ai_result.get("executive_summary", ""),
    }

    # Store in dispatch_cache keyed only by cache_key (user_name varies per user)
    dispatch_cache[cache_key] = {
        "ai_result": ai_result,
        "content_json": content_json,
    }

    html = _render(env, user_name, topic_names, freq, ai_result, matched)
    return {"html": html, "content_json": content_json}


def _render(
    env: Environment,
    user_name: str,
    topic_names: List[str],
    freq: str,
    ai_result: Dict,
    matched: List[CatalogCache],
) -> str:
    """Merge AI results with catalog metadata and render the Jinja2 template."""
    # Build a uid → AI output map
    ai_by_uid: Dict[str, Dict] = {}
    for ai_item in ai_result.get("items", []):
        ai_by_uid[ai_item.get("uid", "")] = ai_item

    template_items = []
    for item in matched:
        ai = ai_by_uid.get(item.uid, {})
        template_items.append({
            "uid": item.uid,
            "title": item.title,
            "url": item.url,
            "content_type": item.content_type,
            "duration_minutes": item.duration_minutes or 0,
            "newsletter_summary": ai.get("newsletter_summary") or item.summary or "",
            "why_it_matters": ai.get("why_it_matters") or "Expand your Microsoft Learn expertise.",
            "key_takeaways": ai.get("key_takeaways") or [],
        })

    template = env.get_template("digest_email.html")
    return template.render(
        digest_title=f"Your {freq.capitalize()} MS Learn Digest",
        user_name=user_name,
        topic_names=topic_names,
        executive_summary=ai_result.get("executive_summary", ""),
        items=template_items,
        freq=freq,
        item_count=len(template_items),
        frontend_url=settings.FRONTEND_URL,
        generated_at=datetime.now(timezone.utc).strftime("%B %d, %Y"),
    )
