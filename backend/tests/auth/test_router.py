from datetime import UTC, datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import SESSION_COOKIE_NAME, encrypt_token, hash_session_id
from app.features.auth.deps import get_google_oauth_client
from app.features.auth.google_oauth import GoogleOAuthClient, OAuthExchangeError, OAuthResult
from app.features.auth.models import GoogleCredential, LoginSession, User

GMAIL_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"


class FakeOAuthClient(GoogleOAuthClient):
    def __init__(self, *, refresh_token: str | None = "google-refresh-token") -> None:
        super().__init__(get_settings())
        self.refresh_token = refresh_token
        self.fail_exchange = False
        self.fail_refresh = False

    def exchange_code(self, code: str) -> OAuthResult:
        if self.fail_exchange:
            raise OAuthExchangeError("bad code")
        return OAuthResult(
            google_sub="google-123",
            email="person@example.com",
            access_token="google-access-token",
            refresh_token=self.refresh_token,
            expiry=datetime.now(UTC) + timedelta(hours=1),
            scopes=["openid", GMAIL_SCOPE],
        )

    def refresh_if_needed(self, credentials: Credentials) -> bool:
        if self.fail_refresh:
            raise RefreshError("refresh failed")  # type: ignore[no-untyped-call]
        return False


@pytest.fixture
def oauth(app: FastAPI) -> FakeOAuthClient:
    fake = FakeOAuthClient()
    app.dependency_overrides[get_google_oauth_client] = lambda: fake
    return fake


def test_google_login_sets_cookie_and_encrypts_refresh_token(
    client: TestClient, db: Session, oauth: FakeOAuthClient
) -> None:
    response = client.post("/api/v1/auth/google", json={"code": "one-time-code"})

    assert response.status_code == 200
    assert response.json() == {"email": "person@example.com", "scopes": ["openid", GMAIL_SCOPE]}
    assert "HttpOnly" in response.headers["set-cookie"]
    user = db.scalars(select(User)).one()
    credential = db.get(GoogleCredential, user.id)
    assert credential is not None
    assert credential.encrypted_refresh_token != "google-refresh-token"
    assert len(db.scalars(select(LoginSession)).all()) == 1


def test_missing_csrf_header_is_rejected(client: TestClient, oauth: FakeOAuthClient) -> None:
    response = client.post(
        "/api/v1/auth/google", json={"code": "x"}, headers={"X-Requested-With": ""}
    )

    assert response.status_code == 403
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == "csrf_check_failed"


def test_invalid_code_returns_400(client: TestClient, oauth: FakeOAuthClient) -> None:
    oauth.fail_exchange = True

    response = client.post("/api/v1/auth/google", json={"code": "bad"})

    assert response.status_code == 400
    assert response.json()["code"] == "invalid_authorization_code"


def test_first_login_without_refresh_token_requires_reconnect(
    client: TestClient, oauth: FakeOAuthClient
) -> None:
    oauth.refresh_token = None

    response = client.post("/api/v1/auth/google", json={"code": "one-time-code"})

    assert response.status_code == 400
    assert response.json()["code"] == "reconnect_required"


def test_empty_code_returns_field_errors(client: TestClient) -> None:
    response = client.post("/api/v1/auth/google", json={"code": ""})

    assert response.status_code == 422
    assert response.json()["errors"][0]["field"] == "code"


def test_me_requires_a_session(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["code"] == "unauthenticated"


def test_expired_session_returns_401(client: TestClient, db: Session, user: User) -> None:
    db.add(
        LoginSession(
            id=hash_session_id("expired"),
            user_id=user.id,
            expires_at=datetime.now(UTC) - timedelta(seconds=1),
        )
    )
    db.commit()
    client.cookies.set(SESSION_COOKIE_NAME, "expired")

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_me_returns_the_signed_in_user(signed_in_client: TestClient) -> None:
    response = signed_in_client.get("/api/v1/auth/me")

    assert response.status_code == 200
    assert response.json() == {"email": "person@example.com", "scopes": []}


def test_logout_ends_the_session(signed_in_client: TestClient) -> None:
    response = signed_in_client.post("/api/v1/auth/logout")

    assert response.status_code == 204
    assert signed_in_client.get("/api/v1/auth/me").status_code == 401


def test_google_refresh_failure_requires_reauth(
    signed_in_client: TestClient, db: Session, user: User, oauth: FakeOAuthClient
) -> None:
    db.add(
        GoogleCredential(
            user_id=user.id,
            encrypted_refresh_token=encrypt_token("refresh-token"),
            access_token="expired-access-token",
            token_expiry=datetime.now(UTC) - timedelta(hours=1),
            granted_scopes=GMAIL_SCOPE,
        )
    )
    db.commit()
    oauth.fail_refresh = True

    response = signed_in_client.get("/api/v1/emails")

    assert response.status_code == 401
    assert response.json()["code"] == "google_reauth_required"
