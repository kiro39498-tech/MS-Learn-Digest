"""
SMTP Client — Gmail delivery with detailed structured logging.
"""

import smtplib
import socket
import logging
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Tuple

from app.core.config import settings

logger = logging.getLogger(__name__)


class SMTPResult:
    """Structured result from an SMTP operation."""
    def __init__(self, success: bool, message: str, detail: str = ""):
        self.success = success
        self.message = message
        self.detail = detail

    def to_dict(self) -> dict:
        return {"success": self.success, "message": self.message, "detail": self.detail}


class EmailClient:
    def __init__(self):
        self.server = settings.SMTP_SERVER
        self.port = settings.SMTP_PORT
        self.username = settings.SMTP_EMAIL
        self.password = settings.SMTP_PASSWORD
        self.sender = settings.SMTP_EMAIL

    # ── Connection test ────────────────────────────────────────────────────

    def test_connection(self) -> SMTPResult:
        """
        Opens an SMTP connection, authenticates, and immediately disconnects.
        Does NOT send any email. Returns a structured result.
        """
        ts = datetime.now(timezone.utc).isoformat()

        if not self.username or not self.password:
            msg = "SMTP credentials are not configured (SMTP_EMAIL / SMTP_PASSWORD are empty)."
            logger.error(f"[{ts}] SMTP_TEST | FAIL | {msg}")
            return SMTPResult(False, msg)

        logger.info(f"[{ts}] SMTP_TEST | START | server={self.server}:{self.port} user={self.username}")

        try:
            with smtplib.SMTP(self.server, self.port, timeout=10) as conn:
                # EHLO
                conn.ehlo()
                logger.info(f"[{ts}] SMTP_TEST | EHLO OK")

                # STARTTLS
                conn.starttls()
                logger.info(f"[{ts}] SMTP_TEST | STARTTLS OK")

                # AUTH
                conn.login(self.username, self.password)
                logger.info(f"[{ts}] SMTP_TEST | AUTH OK | user={self.username}")

            logger.info(f"[{ts}] SMTP_TEST | SUCCESS")
            return SMTPResult(
                True,
                "SMTP connection and authentication succeeded.",
                f"server={self.server}:{self.port} user={self.username}",
            )

        except smtplib.SMTPAuthenticationError as exc:
            detail = (
                "Authentication failed. For Gmail: ensure you are using an App Password "
                "(not your account password). Enable 2FA, then generate an App Password at "
                "https://myaccount.google.com/apppasswords"
            )
            logger.error(f"[{ts}] SMTP_TEST | AUTH_FAIL | {exc}")
            return SMTPResult(False, f"Authentication failed: {exc}", detail)

        except smtplib.SMTPConnectError as exc:
            detail = f"Could not connect to {self.server}:{self.port}. Check firewall / port accessibility."
            logger.error(f"[{ts}] SMTP_TEST | CONNECT_FAIL | {exc}")
            return SMTPResult(False, f"Connection failed: {exc}", detail)

        except socket.timeout:
            detail = f"Connection to {self.server}:{self.port} timed out after 10 seconds."
            logger.error(f"[{ts}] SMTP_TEST | TIMEOUT")
            return SMTPResult(False, "Connection timed out.", detail)

        except Exception as exc:
            logger.error(f"[{ts}] SMTP_TEST | ERROR | {type(exc).__name__}: {exc}")
            return SMTPResult(False, f"Unexpected error: {exc}", type(exc).__name__)

    # ── Send email ─────────────────────────────────────────────────────────

    def send_email(self, recipient: str, subject: str, html_body: str) -> bool:
        """
        Send a single HTML email. Returns True on success, False on failure.
        Uses quoted-printable encoding on the HTML body to handle large templates
        and stay within SMTP line-length limits.
        """
        ts = datetime.now(timezone.utc).isoformat()

        if not self.username or not self.password:
            logger.error(f"[{ts}] EMAIL_SEND | FAIL | SMTP credentials not configured")
            return False

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{settings.APP_NAME} <{self.sender}>"
        message["To"] = recipient

        # Use quoted-printable encoding so large HTML bodies (20-50 KB) don't
        # exceed SMTP 998-char line limits and are accepted by Gmail / Outlook.
        html_part = MIMEText(html_body, "html", "utf-8")
        html_part.replace_header("Content-Transfer-Encoding", "quoted-printable")
        from quopri import encodestring as _qp_encode
        html_part.set_payload(
            _qp_encode(html_body.encode("utf-8")).decode("ascii"),
            charset=None,
        )
        message.attach(html_part)

        logger.info(
            f"[{ts}] EMAIL_SEND | START | to={recipient} "
            f"subject={subject!r} html_bytes={len(html_body.encode('utf-8')):,}"
        )

        try:
            with smtplib.SMTP(self.server, self.port, timeout=30) as conn:
                conn.ehlo()
                conn.starttls()
                conn.login(self.username, self.password)
                conn.sendmail(self.sender, recipient, message.as_bytes())

            logger.info(f"[{ts}] EMAIL_SEND | SUCCESS | to={recipient}")
            return True

        except smtplib.SMTPAuthenticationError as exc:
            logger.error(
                f"[{ts}] EMAIL_SEND | AUTH_FAIL | to={recipient} | "
                "Check Gmail App Password. See: https://myaccount.google.com/apppasswords"
            )
            return False

        except smtplib.SMTPRecipientsRefused as exc:
            logger.error(f"[{ts}] EMAIL_SEND | RECIPIENT_REFUSED | to={recipient} | {exc}")
            return False

        except smtplib.SMTPDataError as exc:
            logger.error(
                f"[{ts}] EMAIL_SEND | DATA_ERROR | to={recipient} | "
                f"code={exc.smtp_code} msg={exc.smtp_error!r}"
            )
            return False

        except smtplib.SMTPServerDisconnected as exc:
            logger.error(f"[{ts}] EMAIL_SEND | DISCONNECTED | to={recipient} | {exc}")
            return False

        except Exception as exc:
            logger.error(
                f"[{ts}] EMAIL_SEND | ERROR | to={recipient} | "
                f"{type(exc).__name__}: {exc}"
            )
            return False

    # ── Send with result ───────────────────────────────────────────────────

    def send_email_with_result(self, recipient: str, subject: str, html_body: str) -> SMTPResult:
        """
        Same as send_email but returns a structured SMTPResult instead of bool.
        Used by admin endpoints that need detailed feedback.
        """
        ts = datetime.now(timezone.utc).isoformat()

        if not self.username or not self.password:
            return SMTPResult(False, "SMTP credentials not configured.", "Set SMTP_EMAIL and SMTP_PASSWORD in .env")

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{settings.APP_NAME} <{self.sender}>"
        message["To"] = recipient

        html_part = MIMEText(html_body, "html", "utf-8")
        html_part.replace_header("Content-Transfer-Encoding", "quoted-printable")
        from quopri import encodestring as _qp_encode
        html_part.set_payload(
            _qp_encode(html_body.encode("utf-8")).decode("ascii"),
            charset=None,
        )
        message.attach(html_part)

        logger.info(
            f"[{ts}] EMAIL_SEND | START | to={recipient} "
            f"subject={subject!r} html_bytes={len(html_body.encode('utf-8')):,}"
        )

        try:
            with smtplib.SMTP(self.server, self.port, timeout=30) as conn:
                conn.ehlo()
                conn.starttls()
                conn.login(self.username, self.password)
                conn.sendmail(self.sender, recipient, message.as_bytes())

            logger.info(f"[{ts}] EMAIL_SEND | SUCCESS | to={recipient}")
            return SMTPResult(True, f"Email delivered to {recipient}.", f"sent_at={ts}")

        except smtplib.SMTPAuthenticationError as exc:
            detail = (
                "Gmail rejected credentials. Use an App Password, not your account password. "
                "Generate at: https://myaccount.google.com/apppasswords"
            )
            logger.error(f"[{ts}] EMAIL_SEND | AUTH_FAIL | {exc}")
            return SMTPResult(False, "Authentication failed.", detail)

        except smtplib.SMTPRecipientsRefused as exc:
            logger.error(f"[{ts}] EMAIL_SEND | RECIPIENT_REFUSED | {exc}")
            return SMTPResult(False, f"Recipient refused: {recipient}", str(exc))

        except smtplib.SMTPDataError as exc:
            logger.error(f"[{ts}] EMAIL_SEND | DATA_ERROR | code={exc.smtp_code} msg={exc.smtp_error!r}")
            return SMTPResult(False, f"SMTP data error (code {exc.smtp_code})", repr(exc.smtp_error))

        except smtplib.SMTPServerDisconnected as exc:
            logger.error(f"[{ts}] EMAIL_SEND | DISCONNECTED | {exc}")
            return SMTPResult(False, "Server disconnected unexpectedly.", str(exc))

        except Exception as exc:
            logger.error(f"[{ts}] EMAIL_SEND | ERROR | {type(exc).__name__}: {exc}")
            return SMTPResult(False, f"Unexpected error: {exc}", type(exc).__name__)
