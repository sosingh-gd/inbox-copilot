"""Session cookies, CSRF protection and token encryption.

Auth model: the backend completes Google OAuth, stores Google tokens server-side, and gives
the browser an opaque, httpOnly session cookie. Only a SHA-256 hash of the session ID is
stored, and Google refresh tokens are encrypted at rest with Fernet.
"""

import hashlib
import secrets
from datetime import datetime

from cryptography.fernet import Fernet, InvalidToken
from fastapi import Request, Response

from app.core.config import get_settings
from app.core.errors import PermissionDeniedError

SESSION_COOKIE_NAME = "inbox_copilot_session"
CSRF_HEADER = "X-Requested-With"
CSRF_HEADER_VALUE = "XmlHttpRequest"
SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


# --- CSRF ------------------------------------------------------------------------------


def require_csrf_header(request: Request) -> None:
    """Reject state-changing requests that lack the custom header.

    Browsers cannot send custom headers cross-site without a CORS preflight, which the API
    only allows for explicitly configured origins. Together with SameSite=Lax cookies this
    blocks cross-site request forgery.
    """
    if request.method in SAFE_METHODS:
        return
    if request.headers.get(CSRF_HEADER) != CSRF_HEADER_VALUE:
        raise PermissionDeniedError("Required request header is missing.", code="csrf_check_failed")


# --- Session IDs and cookies -----------------------------------------------------------


def new_session_id() -> str:
    return secrets.token_urlsafe(32)


def hash_session_id(session_id: str) -> str:
    return hashlib.sha256(session_id.encode()).hexdigest()


def set_session_cookie(response: Response, session_id: str, expires_at: datetime) -> None:
    settings = get_settings()
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
        max_age=settings.session_ttl_days * 24 * 60 * 60,
        expires=expires_at,
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        SESSION_COOKIE_NAME,
        path="/",
        secure=get_settings().cookie_secure,
        httponly=True,
        samesite="lax",
    )


# --- Token encryption ------------------------------------------------------------------


class TokenDecryptionError(Exception):
    pass


def _fernet() -> Fernet:
    try:
        return Fernet(get_settings().token_encryption_key.encode())
    except (ValueError, TypeError) as exc:
        raise RuntimeError("TOKEN_ENCRYPTION_KEY must be a valid Fernet key") from exc


def encrypt_token(token: str) -> str:
    return _fernet().encrypt(token.encode()).decode()


def decrypt_token(token: str) -> str:
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken as exc:
        raise TokenDecryptionError from exc
