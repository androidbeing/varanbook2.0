"""
services/email.py – Transactional email delivery via AWS SES SMTP or aiosmtplib.

Configuration (add to .env / config.py):
  SMTP_HOST        – e.g. "email-smtp.ap-south-1.amazonaws.com"
  SMTP_PORT        – 587 (STARTTLS) or 465 (SSL)
  SMTP_USERNAME    – SES SMTP access key
  SMTP_PASSWORD    – SES SMTP secret
  SMTP_FROM        – "noreply@yourapp.in"
  APP_FRONTEND_URL – "https://app.yourapp.in" (used in reset links)

If SMTP_HOST is not configured, emails are logged only (dev mode).
"""

from __future__ import annotations

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import TYPE_CHECKING

import structlog

logger = structlog.get_logger(__name__)

try:
    import aiosmtplib  # type: ignore[import]
    _HAS_SMTP = True
except ImportError:
    _HAS_SMTP = False


def _get_smtp_config() -> dict:
    from app.config import get_settings
    s = get_settings()
    return {
        "host": getattr(s, "SMTP_HOST", ""),
        "port": int(getattr(s, "SMTP_PORT", 587)),
        "username": getattr(s, "SMTP_USERNAME", ""),
        "password": getattr(s, "SMTP_PASSWORD", ""),
        "from_addr": getattr(s, "SMTP_FROM", "noreply@example.com"),
        "frontend_url": getattr(s, "APP_FRONTEND_URL", "https://app.example.com"),
    }


async def _send(to: str, subject: str, html_body: str) -> None:
    """Low-level async send via aiosmtplib + STARTTLS."""
    cfg = _get_smtp_config()

    if not cfg["host"] or not _HAS_SMTP:
        logger.info("email_dev_mode", to=to, subject=subject)
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = cfg["from_addr"]
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html"))

    await aiosmtplib.send(  # type: ignore[attr-defined]
        msg,
        hostname=cfg["host"],
        port=cfg["port"],
        username=cfg["username"],
        password=cfg["password"],
        start_tls=True,
    )
    logger.info("email_sent", to=to, subject=subject)


class EmailService:
    """Namespace for all transactional email helpers."""

    # ── Password reset ─────────────────────────────────────────────────────────
    @staticmethod
    async def send_password_reset(to_email: str, raw_token: str) -> None:
        cfg = _get_smtp_config()
        reset_url = f"{cfg['frontend_url']}/reset-password?token={raw_token}"
        html = f"""
        <p>You requested a password reset.</p>
        <p><a href="{reset_url}">Click here to reset your password</a></p>
        <p>This link expires in <strong>1 hour</strong>.</p>
        <p>If you did not request this, ignore this email.</p>
        """
        await _send(to_email, "Password Reset – Matrimonial Manager", html)

    # ── Profile shortlisted ────────────────────────────────────────────────────
    @staticmethod
    async def send_shortlist_notification(
        to_email: str,
        from_name: str,
    ) -> None:
        html = f"""
        <p><strong>{from_name}</strong> has expressed interest in your profile.</p>
        <p>Log in to view and respond.</p>
        """
        await _send(to_email, "Someone shortlisted your profile!", html)

    # ── Profile accepted ───────────────────────────────────────────────────────
    @staticmethod
    async def send_accept_notification(
        to_email: str,
        from_name: str,
    ) -> None:
        html = f"""
        <p><strong>{from_name}</strong> has accepted your interest!</p>
        <p>Log in to view contact details.</p>
        """
        await _send(to_email, "Your interest was accepted!", html)

    # ── Welcome / verification ─────────────────────────────────────────────────
    @staticmethod
    async def send_welcome(to_email: str, full_name: str) -> None:
        html = f"""
        <p>Hello <strong>{full_name}</strong>, welcome to Matrimonial Manager!</p>
        <p>Log in to complete your profile and find your match.</p>
        """
        await _send(to_email, "Welcome to Matrimonial Manager", html)
