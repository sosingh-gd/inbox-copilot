import os

# Configure the app before anything reads settings. "sqlite://" is a fresh in-memory
# database for every app instance, so each test starts empty.
os.environ["GOOGLE_CLIENT_ID"] = "test-client-id"
os.environ["GOOGLE_CLIENT_SECRET"] = "test-client-secret"
os.environ["TOKEN_ENCRYPTION_KEY"] = "faIkad-d1v6-ZpWnG7faKkP1BxAiWY62RwnQfpEAUNM="
os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-key"
os.environ["DATABASE_URL"] = "sqlite://"

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import (
    CSRF_HEADER,
    CSRF_HEADER_VALUE,
    SESSION_COOKIE_NAME,
    hash_session_id,
)
from app.db.session import session_factory
from app.features.auth.models import LoginSession, User
from app.main import create_app


@pytest.fixture
def app() -> FastAPI:
    return create_app()


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    # The context manager runs the lifespan, which creates the in-memory database.
    with TestClient(app, headers={CSRF_HEADER: CSRF_HEADER_VALUE}) as test_client:
        yield test_client


@pytest.fixture
def db(client: TestClient) -> Iterator[Session]:
    with session_factory()() as session:
        yield session


def create_user(
    db: Session, *, google_sub: str = "google-123", email: str = "person@example.com"
) -> User:
    user = User(google_sub=google_sub, email=email)
    db.add(user)
    db.commit()
    return user


def sign_in(
    client: TestClient, db: Session, user: User, *, session_id: str = "test-session"
) -> None:
    db.add(
        LoginSession(
            id=hash_session_id(session_id),
            user_id=user.id,
            expires_at=datetime.now(UTC) + timedelta(days=1),
        )
    )
    db.commit()
    client.cookies.set(SESSION_COOKIE_NAME, session_id)


@pytest.fixture
def user(db: Session) -> User:
    return create_user(db)


@pytest.fixture
def signed_in_client(client: TestClient, db: Session, user: User) -> TestClient:
    sign_in(client, db, user)
    return client
