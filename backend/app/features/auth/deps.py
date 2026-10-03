from datetime import timedelta
from typing import Annotated

from fastapi import Cookie, Depends
from google.oauth2.credentials import Credentials
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import SESSION_COOKIE_NAME
from app.db.session import get_session

from .google_oauth import GoogleOAuthClient
from .models import User
from .repository import AuthRepository
from .service import AuthService


def get_google_oauth_client() -> GoogleOAuthClient:
    return GoogleOAuthClient(get_settings())


def get_auth_service(
    session: Annotated[Session, Depends(get_session)],
    oauth: Annotated[GoogleOAuthClient, Depends(get_google_oauth_client)],
) -> AuthService:
    ttl = timedelta(days=get_settings().session_ttl_days)
    return AuthService(AuthRepository(session), oauth, ttl)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
SessionIdCookie = Annotated[str | None, Cookie(alias=SESSION_COOKIE_NAME)]


def get_current_user(service: AuthServiceDep, session_id: SessionIdCookie = None) -> User:
    return service.authenticate(session_id)


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_google_credentials(user: CurrentUser, service: AuthServiceDep) -> Credentials:
    return service.get_google_credentials(user)


GoogleCredentialsDep = Annotated[Credentials, Depends(get_google_credentials)]
