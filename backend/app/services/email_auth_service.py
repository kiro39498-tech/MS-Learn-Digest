"""
Email Authentication Service — Magic-link login flow.

Flow:
  1. request_login(email)
       - Look up or create user by email
       - Generate a cryptographically random token
       - Store SHA-256 hash of token in email_login_tokens
       - Send magic-link email to user
       - Returns (success, message)

  2. verify_token(token)
       - Hash the incoming raw token
       - Find the DB row by hash
       - Check expiry and used_at
       - Mark as used
       - Upsert user (create if new, update last_login)
       - Return JWT exactly like Google OAuth users

Security:
  - Tokens are random 32-byte hex strings (64 chars)
  - Only the SHA-256 hash is stored — raw token is never persisted
  - Tokens expire in EMAIL_LOGIN_TOKEN_EXPIRY_MINUTES (default 15)
  - Tokens are single-use (used_at is set on first verification)
  - Rate limiting: max EMAIL_LOGIN_MAX_ATTEMPTS_PER_HOUR requests per email per hour
"""

import hashlib
import logging
import secrets
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.config import settings
from app.core.security import create_access_token
from app.models.auth import EmailLoginToken
from app.models.user import User
from app.services.email.smtp_client import EmailClient

logger = logging.getLogger(__name__)


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


def _send_login_email(email: str, login_url: str) -> bool:
    html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"/></head>
<body style="font-family:'Segoe UI',Arial,sans-serif;background:#f0f4f8;margin:0;padding:32px">
  <div style="max-width:520px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.08)">
    <div style="background:linear-gradient(135deg,#0078d4,#005a9e);padding:32px 36px;text-align:center">
      <h1 style="color:#fff;margin:0;font-size:22px;font-weight:700">MS Learn Digest</h1>
      <p style="color:rgba(255,255,255,.85);margin:8px 0 0;font-size:14px">Your secure login link</p>
    </div>
    <div style="padding:36px">
      <p style="color:#1a202c;font-size:16px;margin:0 0 8px">Hi there 👋</p>
      <p style="color:#4a5568;font-size:14px;line-height:1.6;margin:0 0 28px">
        Click the button below to sign in to your MS Learn Digest account.
        This link expires in <strong>{settings.EMAIL_LOGIN_TOKEN_EXPIRY_MINUTES} minutes</strong>
        and can only be used once.
      </p>
      <div style="text-align:center;margin-bottom:28px">
        <a href="{login_url}"
           style="display:inline-block;background:#0078d4;color:#fff;text-decoration:none;
                  padding:14px 32px;border-radius:8px;font-size:15px;font-weight:600;
                  letter-spacing:.3px">
          Sign in to MS Learn Digest
        </a>
      </div>
      <p style="color:#718096;font-size:12px;text-align:center;margin:0">
        If you didn't request this link, you can safely ignore this email.<br/>
        This link will expire automatically.
      </p>
    </div>
    <div style="background:#f7f8fa;border-top:1px solid #e2e8f0;padding:16px 36px;text-align:center">
      <p style="color:#a0aec0;font-size:11px;margin:0">MS Learn Digest &nbsp;·&nbsp; Secure Email Login</p>
    </div>
  </div>
</body>
</html>
"""
    client = EmailClient()
    return client.send_email(
        recipient=email,
        subject="Sign in to MS Learn Digest",
        html_body=html,
    )


class EmailAuthService:
    def __init__(self, db: Session):
        self.db = db

    # ── Rate limiting ─────────────────────────────────────────────────────

    def _check_rate_limit(self, email: str) -> bool:
        """Return True if the email is within rate limits."""
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        count = (
            self.db.query(func.count(EmailLoginToken.id))
            .filter(
                EmailLoginToken.email == email,
                EmailLoginToken.created_at >= one_hour_ago,
            )
            .scalar()
        )
        return count < settings.EMAIL_LOGIN_MAX_ATTEMPTS_PER_HOUR

    # ── Request login ─────────────────────────────────────────────────────

    def request_login(self, email: str) -> tuple[bool, str]:
        """
        Generate a magic-link token and email it to the user.
        Returns (success, message).
        """
        email = email.strip().lower()

        # Rate limit check
        if not self._check_rate_limit(email):
            logger.warning(f"EMAIL_AUTH | RATE_LIMIT | {email}")
            return False, "Too many login requests. Please wait before trying again."

        # Generate raw token and store its hash
        raw_token = secrets.token_hex(32)   # 64-char hex string
        token_hash = _hash_token(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.EMAIL_LOGIN_TOKEN_EXPIRY_MINUTES
        )

        token_row = EmailLoginToken(
            email=email,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.db.add(token_row)
        self.db.commit()

        # Build the magic-link URL pointing at the frontend
        login_url = f"{settings.FRONTEND_URL}/auth/email/callback?token={raw_token}"

        # Send the email
        sent = _send_login_email(email, login_url)
        if sent:
            logger.info(f"EMAIL_AUTH | SENT | {email} expires={expires_at.isoformat()}")
            return True, "Login link sent. Check your email."
        else:
            # Clean up unused token if email failed
            self.db.delete(token_row)
            self.db.commit()
            logger.error(f"EMAIL_AUTH | SEND_FAILED | {email}")
            return False, "Failed to send login email. Check SMTP configuration."

    # ── Verify token ──────────────────────────────────────────────────────

    def verify_token(self, raw_token: str) -> tuple[bool, str, str | None]:
        """
        Verify a magic-link token and return a JWT.
        Returns (success, message, jwt_token_or_None).
        """
        token_hash = _hash_token(raw_token)

        token_row = (
            self.db.query(EmailLoginToken)
            .filter(EmailLoginToken.token_hash == token_hash)
            .first()
        )

        if not token_row:
            logger.warning(f"EMAIL_AUTH | INVALID_TOKEN | hash={token_hash[:16]}…")
            return False, "Invalid or expired login link.", None

        now = datetime.now(timezone.utc)

        if token_row.used_at is not None:
            logger.warning(f"EMAIL_AUTH | ALREADY_USED | email={token_row.email}")
            return False, "This login link has already been used. Request a new one.", None

        if now > token_row.expires_at:
            logger.warning(f"EMAIL_AUTH | EXPIRED | email={token_row.email}")
            return False, "This login link has expired. Request a new one.", None

        # Mark token as used immediately (single-use guarantee)
        token_row.used_at = now
        self.db.commit()

        # Upsert user
        email = token_row.email
        user = self.db.query(User).filter(User.email == email).first()

        if user:
            # Existing user — update auth fields
            if user.auth_provider == "google" and not user.email_verified:
                user.email_verified = True
            # If they were google-only before, keep google as provider
            # but ensure email_verified is set
            if not user.email_verified:
                user.email_verified = True
            user.last_login = now
            self.db.commit()
            logger.info(f"EMAIL_AUTH | EXISTING_USER | {email} id={user.id}")
        else:
            # New user — create with email provider
            # Use email prefix as name, they can update it later
            name_from_email = email.split("@")[0].replace(".", " ").replace("_", " ").title()
            user = User(
                email=email,
                name=name_from_email,
                auth_provider="email",
                email_verified=True,
                is_onboarded=False,
                last_login=now,
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            logger.info(f"EMAIL_AUTH | NEW_USER | {email} id={user.id}")

        # Issue JWT — identical structure to Google OAuth
        jwt_token = create_access_token(data={"sub": str(user.id)})
        logger.info(f"EMAIL_AUTH | SUCCESS | {email} user_id={user.id}")
        return True, "Login successful.", jwt_token
