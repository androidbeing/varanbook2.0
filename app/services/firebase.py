"""
services/firebase.py – Firebase Admin SDK wrapper for phone OTP verification.

How it works:
  1. User enters their phone number in the frontend.
  2. Firebase JS SDK sends an OTP SMS and, on correct entry, returns an ID token.
  3. Frontend POSTs that token to our backend.
  4. We call firebase_admin.auth.verify_id_token() to confirm the token is valid
     and extract the verified phone number.
  5. We compare the verified phone with what the user claimed — they must match.

Configuration:
  FIREBASE_OTP_ENABLED        – set True in production to enforce OTP
  FIREBASE_SERVICE_ACCOUNT_JSON – service account JSON string (from Firebase console)
                                  Leave empty to use Application Default Credentials (ADC),
                                  which works automatically on GCP / Cloud Run.

When FIREBASE_OTP_ENABLED=False (default, dev mode) all verification calls are
no-ops so the app works without Firebase credentials locally.
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

_firebase_app = None


def _get_app():
    """Initialise Firebase Admin SDK once per process."""
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app

    try:
        import firebase_admin
        from firebase_admin import credentials
    except ImportError:
        logger.warning("firebase-admin not installed; OTP verification unavailable")
        return None

    from app.config import get_settings
    s = get_settings()

    sa_json: str = getattr(s, "FIREBASE_SERVICE_ACCOUNT_JSON", "")

    try:
        if sa_json.strip():
            # Explicit service account JSON supplied via env var
            sa_dict = json.loads(sa_json)
            cred = credentials.Certificate(sa_dict)
        else:
            # Fall back to Application Default Credentials (works on GCP/Cloud Run)
            cred = credentials.ApplicationDefault()

        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialised")
    except Exception as exc:
        logger.warning("Firebase Admin SDK init failed: %s", exc)
        _firebase_app = None

    return _firebase_app


def verify_phone_token(id_token: str, claimed_phone: str) -> str:
    """
    Verify a Firebase phone auth ID token and return the verified phone number.

    Args:
        id_token:      Firebase ID token obtained after the user completes OTP.
        claimed_phone: Phone number the user entered (E.164 format).

    Returns:
        The verified phone number from Firebase (E.164).

    Raises:
        ValueError: if the token is invalid or the phone doesn't match.
    """
    from app.config import get_settings
    s = get_settings()

    if not getattr(s, "FIREBASE_OTP_ENABLED", False):
        # Dev / test mode — skip verification
        logger.debug("firebase_otp_disabled – skipping token verification")
        return claimed_phone

    app = _get_app()
    if app is None:
        raise ValueError(
            "Firebase Admin SDK is not initialised. "
            "Check FIREBASE_SERVICE_ACCOUNT_JSON or Application Default Credentials."
        )

    try:
        from firebase_admin import auth as fb_auth
        decoded = fb_auth.verify_id_token(id_token, app=app, check_revoked=True)
    except Exception as exc:
        logger.warning("firebase_token_invalid: %s", exc)
        raise ValueError("OTP verification failed. Please try again.") from exc

    firebase_phone: str | None = decoded.get("phone_number")
    if not firebase_phone:
        raise ValueError("Token does not contain a verified phone number.")

    # Normalise both for comparison (strip spaces)
    if firebase_phone.replace(" ", "") != claimed_phone.replace(" ", ""):
        raise ValueError("Verified phone number does not match the supplied phone.")

    return firebase_phone
