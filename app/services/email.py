"""
services/email.py – Transactional email delivery via SMTP (Gmail / SES).

Configuration (env vars):
  SMTP_HOST        – e.g. "smtp.gmail.com"
  SMTP_PORT        – 587 (STARTTLS)
  SMTP_USERNAME    – sender Gmail / SES address
  SMTP_PASSWORD    – App Password or SES SMTP secret
  SMTP_FROM        – "Varanbook <varanbookhelp@gmail.com>"
  APP_FRONTEND_URL – "https://varanbook.in"

If SMTP_HOST is not configured, emails are logged only (dev mode).
"""

from __future__ import annotations

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import structlog

logger = structlog.get_logger(__name__)

try:
    import aiosmtplib  # type: ignore[import]
    _HAS_SMTP = True
except ImportError:
    _HAS_SMTP = False


# ── Brand constants ────────────────────────────────────────────────────────────
_PRIMARY   = "#1E88E5"
_SECONDARY = "#7B1FA2"
_BG        = "#F0EEFF"
_CARD_BG   = "#FFFFFF"
_TEXT      = "#1a1a2e"
_MUTED     = "#6b7280"
_BORDER    = "#e5e7eb"


def _get_smtp_config() -> dict:
    from app.config import get_settings
    s = get_settings()
    return {
        "host":         getattr(s, "SMTP_HOST", ""),
        "port":         int(getattr(s, "SMTP_PORT", 587)),
        "username":     getattr(s, "SMTP_USERNAME", ""),
        "password":     getattr(s, "SMTP_PASSWORD", ""),
        "from_addr":    getattr(s, "SMTP_FROM", "Varanbook <noreply@varanbook.in>"),
        "frontend_url": getattr(s, "APP_FRONTEND_URL", "https://varanbook.in"),
    }


# ── Base layout ────────────────────────────────────────────────────────────────
def _base(content: str, preview: str = "") -> str:
    """Wrap content in a responsive branded email shell."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1.0" />
  <meta name="color-scheme" content="light" />
  <title>Varanbook</title>
  {'<span style="display:none;max-height:0;overflow:hidden;">' + preview + '&nbsp;&#847;&nbsp;' * 80 + '</span>' if preview else ''}
</head>
<body style="margin:0;padding:0;background-color:{_BG};font-family:'Segoe UI',Roboto,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:{_BG};padding:40px 16px;">
    <tr>
      <td align="center">

        <!-- Header -->
        <table width="560" cellpadding="0" cellspacing="0" style="max-width:560px;width:100%;">
          <tr>
            <td align="center" style="padding-bottom:24px;">
              <table cellpadding="0" cellspacing="0">
                <tr>
                  <td style="background:linear-gradient(135deg,{_PRIMARY},{_SECONDARY});border-radius:14px;padding:10px 22px;">
                    <span style="font-size:22px;font-weight:700;color:#fff;letter-spacing:-0.5px;">&#10084; Varanbook</span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>

        <!-- Card -->
        <table width="560" cellpadding="0" cellspacing="0"
               style="max-width:560px;width:100%;background:{_CARD_BG};border-radius:16px;
                      border:1px solid {_BORDER};box-shadow:0 4px 24px rgba(30,136,229,0.08);">
          <tr>
            <!-- Gradient top bar -->
            <td style="background:linear-gradient(135deg,{_PRIMARY},{_SECONDARY});
                       height:5px;border-radius:16px 16px 0 0;font-size:0;">&nbsp;</td>
          </tr>
          <tr>
            <td style="padding:36px 40px 32px;">
              {content}
            </td>
          </tr>
          <tr>
            <!-- Footer -->
            <td style="border-top:1px solid {_BORDER};padding:20px 40px;border-radius:0 0 16px 16px;background:#fafafa;">
              <p style="margin:0;font-size:12px;color:{_MUTED};text-align:center;line-height:1.6;">
                © 2026 Varanbook &nbsp;·&nbsp; Matrimonial Centre Management<br/>
                If you did not expect this email, you can safely ignore it.
              </p>
            </td>
          </tr>
        </table>

      </td>
    </tr>
  </table>
</body>
</html>"""


def _btn(label: str, url: str, color: str = _PRIMARY) -> str:
    return f"""
    <table cellpadding="0" cellspacing="0" style="margin:28px 0;">
      <tr>
        <td style="background:{color};border-radius:8px;">
          <a href="{url}"
             style="display:inline-block;padding:13px 32px;font-size:15px;font-weight:600;
                    color:#fff;text-decoration:none;letter-spacing:0.2px;">{label}</a>
        </td>
      </tr>
    </table>"""


def _h1(text: str) -> str:
    return f'<h1 style="margin:0 0 8px;font-size:24px;font-weight:700;color:{_TEXT};">{text}</h1>'


def _p(text: str, mt: int = 0) -> str:
    return f'<p style="margin:{mt}px 0 16px;font-size:15px;line-height:1.7;color:{_TEXT};">{text}</p>'


def _muted(text: str) -> str:
    return f'<p style="margin:20px 0 0;font-size:13px;color:{_MUTED};line-height:1.6;">{text}</p>'


def _info_row(label: str, value: str) -> str:
    return f"""
    <tr>
      <td style="padding:10px 16px;font-size:13px;color:{_MUTED};font-weight:600;
                 white-space:nowrap;border-bottom:1px solid {_BORDER};">{label}</td>
      <td style="padding:10px 16px;font-size:14px;color:{_TEXT};border-bottom:1px solid {_BORDER};">{value}</td>
    </tr>"""


def _info_table(*rows: str) -> str:
    inner = "".join(rows)
    return f"""
    <table width="100%" cellpadding="0" cellspacing="0"
           style="border:1px solid {_BORDER};border-radius:10px;border-collapse:collapse;margin:20px 0;">
      {inner}
    </table>"""


# ── Low-level send ─────────────────────────────────────────────────────────────
async def _send(to: str, subject: str, html_body: str) -> None:
    cfg = _get_smtp_config()

    if not cfg["host"] or not _HAS_SMTP:
        logger.info("email_dev_mode", to=to, subject=subject)
        return

    if not cfg["username"] or not cfg["password"]:
        logger.error("email_smtp_credentials_missing", to=to, subject=subject)
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = cfg["from_addr"]
    msg["To"]      = to
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


# ── Email templates ────────────────────────────────────────────────────────────
class EmailService:

    # ── Password reset ─────────────────────────────────────────────────────────
    @staticmethod
    async def send_password_reset(to_email: str, raw_token: str) -> None:
        cfg = _get_smtp_config()
        reset_url = f"{cfg['frontend_url']}/reset-password?token={raw_token}"
        content = (
            _h1("Reset your password")
            + _p("We received a request to reset the password for your Varanbook account. "
                 "Click the button below to choose a new password.", mt=4)
            + _btn("Reset Password", reset_url)
            + _muted("This link expires in <strong>1 hour</strong>. "
                     "If you did not request a password reset, no action is needed.")
        )
        await _send(to_email, "Reset your Varanbook password", _base(content, "Reset your Varanbook password"))

    # ── Member invite ──────────────────────────────────────────────────────────
    @staticmethod
    async def send_member_invite(to_email: str, temp_password: str, full_name: str = "") -> None:
        cfg = _get_smtp_config()
        login_url = f"{cfg['frontend_url']}/login"
        greeting = f"Hello, <strong>{full_name}</strong> 👋" if full_name else "Hello 👋"
        content = (
            _h1("You're invited to Varanbook")
            + _p(greeting, mt=4)
            + _p("Your matrimonial centre has created an account for you on "
                 "<strong>Varanbook</strong>. Use the credentials below to sign in "
                 "and complete your profile to start connecting with potential matches.")
            + _info_table(
                _info_row("Email", to_email),
                _info_row("Temporary Password", f"<code style='font-family:monospace;font-size:14px;"
                          f"background:#f3f4f6;padding:2px 6px;border-radius:4px;'>{temp_password}</code>"),
            )
            + _btn("Sign In to Varanbook", login_url)
            + _muted("Please change your password after your first login. "
                     "If you were not expecting this invitation, you can safely ignore this email.")
        )
        await _send(to_email, "You're invited to Varanbook", _base(content, "Your Varanbook account is ready"))

    # ── Profile shortlisted ────────────────────────────────────────────────────
    @staticmethod
    async def send_shortlist_notification(to_email: str, from_name: str) -> None:
        cfg = _get_smtp_config()
        login_url = f"{cfg['frontend_url']}/dashboard"
        content = (
            _h1("Someone is interested in you! ✨")
            + _p(f"<strong>{from_name}</strong> has expressed interest in your profile on Varanbook. "
                 "This could be the beginning of something beautiful.", mt=4)
            + _btn("View Profile & Respond", login_url)
            + _muted("Log in to see their full profile and send your response.")
        )
        await _send(to_email, f"{from_name} is interested in your profile!", _base(content))

    # ── Interest accepted ──────────────────────────────────────────────────────
    @staticmethod
    async def send_accept_notification(to_email: str, from_name: str) -> None:
        cfg = _get_smtp_config()
        login_url = f"{cfg['frontend_url']}/dashboard"
        content = (
            _h1("Great news — your interest was accepted! 🎉")
            + _p(f"<strong>{from_name}</strong> has accepted your interest on Varanbook. "
                 "You can now view their contact details and take the next step.", mt=4)
            + _btn("View Contact Details", login_url)
            + _muted("Log in to Varanbook to continue the conversation.")
        )
        await _send(to_email, f"{from_name} accepted your interest!", _base(content))

    # ── Welcome ────────────────────────────────────────────────────────────────
    @staticmethod
    async def send_welcome(to_email: str, full_name: str) -> None:
        cfg = _get_smtp_config()
        login_url = f"{cfg['frontend_url']}/dashboard"
        content = (
            _h1(f"Welcome to Varanbook, {full_name}! 🌸")
            + _p("We're delighted to have you on board. Varanbook is your trusted platform "
                 "for finding the perfect life partner through your matrimonial centre.", mt=4)
            + _p("Here's how to get started:")
            + """<ul style="margin:0 0 16px;padding-left:20px;font-size:15px;color:#1a1a2e;line-height:1.9;">
                   <li>Complete your profile with photos and personal details</li>
                   <li>Browse profiles from your matrimonial centre</li>
                   <li>Express interest and connect with potential matches</li>
                 </ul>"""
            + _btn("Complete My Profile", login_url)
        )
        await _send(to_email, f"Welcome to Varanbook, {full_name}!", _base(content, "Your journey to finding the perfect match begins"))

    # ── Subscription expired ───────────────────────────────────────────────────
    @staticmethod
    async def send_subscription_expired(to_email: str, full_name: str, plan_name: str) -> None:
        cfg = _get_smtp_config()
        plans_url = f"{cfg['frontend_url']}/plans"
        content = (
            _h1("Your membership has expired")
            + _p(f"Dear <strong>{full_name}</strong>,", mt=4)
            + _p(f"Your <strong>{plan_name}</strong> membership on Varanbook has expired. "
                 "Renew now to continue browsing profiles and sending interest requests without interruption.")
            + _btn("Renew Membership", plans_url, color=_SECONDARY)
            + _muted("Questions? Reach out to your matrimonial centre for assistance.")
        )
        await _send(to_email, f"Your {plan_name} membership has expired", _base(content))

    # ── Subscription expiry warning ────────────────────────────────────────────
    @staticmethod
    async def send_subscription_expiry_warning(
        to_email: str, full_name: str, plan_name: str, expires_on: str
    ) -> None:
        cfg = _get_smtp_config()
        plans_url = f"{cfg['frontend_url']}/plans"
        content = (
            _h1("Your membership expires soon ⏳")
            + _p(f"Dear <strong>{full_name}</strong>,", mt=4)
            + _p(f"Your <strong>{plan_name}</strong> membership will expire on "
                 f"<strong>{expires_on}</strong> — just 3 days away. "
                 "Renew early to avoid any gap in your access to profiles and matches.")
            + _btn("Renew Now", plans_url, color=_SECONDARY)
            + _muted("Renewing early ensures uninterrupted access to all features.")
        )
        await _send(to_email, f"Your {plan_name} membership expires in 3 days", _base(content))
