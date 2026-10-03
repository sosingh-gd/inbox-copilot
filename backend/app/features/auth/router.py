from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.core.security import clear_session_cookie, set_session_cookie

from .deps import AuthServiceDep, CurrentUser, SessionIdCookie
from .schemas import CurrentUserRead, GoogleLoginRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/google")
def login_with_google(
    body: GoogleLoginRequest, response: Response, service: AuthServiceDep
) -> CurrentUserRead:
    """Exchange a Google authorization code for an app session cookie."""
    login = service.login_with_google(body.code)
    set_session_cookie(response, login.session_id, login.expires_at)
    return login.user


@router.get("/me")
def read_current_user(user: CurrentUser, service: AuthServiceDep) -> CurrentUserRead:
    return service.describe(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    user: CurrentUser,
    service: AuthServiceDep,
    session_id: SessionIdCookie = None,
    revoke: Annotated[bool, Query(description="Also revoke Google access")] = False,
) -> None:
    service.logout(user, session_id, revoke_google_access=revoke)
    clear_session_cookie(response)
