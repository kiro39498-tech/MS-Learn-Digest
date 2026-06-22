"""
Auth API — Google OAuth + Email Magic-Link

Endpoints:
  POST /api/auth/google          — Exchange Google OAuth code for JWT (existing)
  POST /api/auth/email/request   — Send magic-link to email address
  POST /api/auth/email/verify    — Verify magic-link token → JWT
  GET  /api/auth/providers       — List available auth providers
"""

import re
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import GoogleAuthCode, Token
from app.services.auth_service import AuthService
from app.services.email_auth_service import EmailAuthService

logger = logging.getLogger(__name__)
router = APIRouter()

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


# ── Schemas ───────────────────────────────────────────────────────────────────

class EmailLoginRequest(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not _EMAIL_RE.match(v):
            raise ValueError("Invalid email address")
        return v


class EmailVerifyRequest(BaseModel):
    token: str

    @field_validator("token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 32:
            raise ValueError("Invalid token format")
        return v


# ── Existing Google OAuth ─────────────────────────────────────────────────────

@router.post("/google", response_model=Token)
async def google_auth(auth_data: GoogleAuthCode, db: Session = Depends(get_db)):
    """Exchange Google OAuth code for a JWT token."""
    auth_service = AuthService(db)
    jwt_token = await auth_service.exchange_google_code(
        auth_data.code, auth_data.redirect_uri
    )
    return {"access_token": jwt_token, "token_type": "bearer"}


# ── Email magic-link ──────────────────────────────────────────────────────────

@router.post("/email/request")
async def email_login_request(
    payload: EmailLoginRequest,
    db: Session = Depends(get_db),
):
    """
    Request a magic-link login email.
    Sends a secure single-use link to the provided email address.
    The link expires in EMAIL_LOGIN_TOKEN_EXPIRY_MINUTES minutes.
    """
    service = EmailAuthService(db)
    success, message = service.request_login(payload.email)

    if not success:
        # Rate limit → 429, email send failure → 502
        if "Too many" in message:
            raise HTTPException(status_code=429, detail=message)
        raise HTTPException(status_code=502, detail=message)

    return {
        "status": "sent",
        "message": message,
        "email": payload.email,
    }


@router.post("/email/verify", response_model=Token)
async def email_login_verify(
    payload: EmailVerifyRequest,
    db: Session = Depends(get_db),
):
    """
    Verify a magic-link token and return a JWT.
    The token must not be expired or already used.
    """
    service = EmailAuthService(db)
    success, message, jwt_token = service.verify_token(payload.token)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
        )

    return {"access_token": jwt_token, "token_type": "bearer"}


@router.get("/providers")
async def get_auth_providers():
    """Return the list of available authentication providers."""
    from app.core.config import settings
    providers = [
        {
            "id": "google",
            "name": "Continue with Google",
            "type": "oauth",
            "available": bool(settings.GOOGLE_CLIENT_ID),
        },
        {
            "id": "email",
            "name": "Continue with Email",
            "type": "magic_link",
            "available": bool(settings.SMTP_EMAIL and settings.SMTP_PASSWORD),
        },
    ]
    return {"providers": providers}
