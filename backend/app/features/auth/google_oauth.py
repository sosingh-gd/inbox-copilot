"""Thin wrapper around Google's OAuth libraries, so the rest of the app never touches them.

Tests replace GoogleOAuthClient through FastAPI's dependency overrides.
"""

import os
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from app.core.config import GOOGLE_OAUTH_SCOPES, Settings

# Google may grant a subset or superset of the requested scopes; don't treat that as fatal.
os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")

TOKEN_URI = "https://oauth2.googleapis.com/token"  # noqa: S105 - a URL, not a secret
REVOKE_URI = "https://oauth2.googleapis.com/revoke"


class OAuthExchangeError(Exception):
    pass


class TokenRevocationError(Exception):
    pass


@dataclass(frozen=True)
class OAuthResult:
    google_sub: str
    email: str
    access_token: str | None
    refresh_token: str | None
    expiry: datetime | None  # aware UTC
    scopes: list[str]


def _as_aware_utc(value: datetime | None) -> datetime | None:
    """google-auth uses naive UTC datetimes; the database stores aware ones."""
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=UTC)


def _as_naive_utc(value: datetime | None) -> datetime | None:
    if value is None or value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


class GoogleOAuthClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def exchange_code(self, code: str) -> OAuthResult:
        """Exchange the popup's one-time code for tokens and verify the ID token."""
        client_config = {
            "web": {
                "client_id": self._settings.google_client_id,
                "client_secret": self._settings.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": TOKEN_URI,
            }
        }
        try:
            flow = Flow.from_client_config(
                client_config, scopes=list(GOOGLE_OAUTH_SCOPES), redirect_uri="postmessage"
            )
            flow.fetch_token(code=code)
            credentials = flow.credentials
            claims = id_token.verify_oauth2_token(  # type: ignore[no-untyped-call]
                credentials.id_token,
                GoogleRequest(),
                audience=self._settings.google_client_id,
                clock_skew_in_seconds=10,
            )
        except Exception as exc:
            raise OAuthExchangeError("Google sign-in failed") from exc

        if not claims.get("sub") or not claims.get("email"):
            raise OAuthExchangeError("Google identity is missing a subject or email")

        scopes = credentials.granted_scopes or credentials.scopes or GOOGLE_OAUTH_SCOPES
        return OAuthResult(
            google_sub=claims["sub"],
            email=claims["email"],
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            expiry=_as_aware_utc(credentials.expiry),
            scopes=list(scopes),
        )

    def revoke(self, token: str) -> None:
        request = Request(
            REVOKE_URI,
            data=urlencode({"token": token}).encode(),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=10) as response:  # noqa: S310 - fixed https URL
                if response.status >= 400:
                    raise TokenRevocationError("Google token revocation failed")
        except OSError as exc:
            raise TokenRevocationError("Google token revocation failed") from exc

    def build_credentials(
        self,
        *,
        refresh_token: str,
        access_token: str | None,
        expiry: datetime | None,
        scopes: list[str],
    ) -> Credentials:
        credentials = Credentials(  # type: ignore[no-untyped-call]
            token=access_token,
            refresh_token=refresh_token,
            token_uri=TOKEN_URI,
            client_id=self._settings.google_client_id,
            client_secret=self._settings.google_client_secret,
            scopes=scopes or list(GOOGLE_OAUTH_SCOPES),
        )
        credentials.expiry = _as_naive_utc(expiry)
        return credentials

    def refresh_if_needed(self, credentials: Credentials) -> bool:
        """Refresh an expired access token. Returns True if a refresh happened.

        Raises RefreshError if Google rejects the refresh token.
        """
        if credentials.token and not credentials.expired:
            return False
        credentials.refresh(GoogleRequest())  # type: ignore[no-untyped-call]
        return True


def credentials_expiry(credentials: Credentials) -> datetime | None:
    return _as_aware_utc(credentials.expiry)


__all__ = [
    "GoogleOAuthClient",
    "OAuthExchangeError",
    "OAuthResult",
    "RefreshError",
    "TokenRevocationError",
    "credentials_expiry",
]
