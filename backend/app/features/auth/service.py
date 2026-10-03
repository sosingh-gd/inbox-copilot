from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from google.oauth2.credentials import Credentials

from app.core.errors import (
    BadRequestError,
    ExternalServiceError,
    GoogleReauthRequiredError,
    UnauthenticatedError,
)
from app.core.security import (
    TokenDecryptionError,
    decrypt_token,
    encrypt_token,
    hash_session_id,
    new_session_id,
)

from .google_oauth import (
    GoogleOAuthClient,
    OAuthExchangeError,
    RefreshError,
    TokenRevocationError,
    credentials_expiry,
)
from .models import GoogleCredential, LoginSession, User
from .repository import AuthRepository
from .schemas import CurrentUserRead


@dataclass(frozen=True)
class NewLoginSession:
    user: CurrentUserRead
    session_id: str  # raw value for the cookie; only its hash is stored
    expires_at: datetime


class AuthService:
    def __init__(
        self, repo: AuthRepository, oauth: GoogleOAuthClient, session_ttl: timedelta
    ) -> None:
        self.repo = repo
        self.oauth = oauth
        self.session_ttl = session_ttl

    def login_with_google(self, code: str) -> NewLoginSession:
        try:
            result = self.oauth.exchange_code(code)
        except OAuthExchangeError as exc:
            raise BadRequestError(
                "Google sign-in failed.", code="invalid_authorization_code"
            ) from exc

        user = self.repo.get_user_by_google_sub(result.google_sub)
        if user is None:
            user = self.repo.add_user(User(google_sub=result.google_sub, email=result.email))
        else:
            user.email = result.email

        credential = self.repo.get_credential(user.id)
        if result.refresh_token is not None:
            if credential is None:
                credential = GoogleCredential(user_id=user.id)
                self.repo.add_credential(credential)
            credential.encrypted_refresh_token = encrypt_token(result.refresh_token)
        elif credential is None:
            # Google only returns a refresh token on first consent. Without one we cannot
            # read Gmail or Calendar later, so ask the user to grant access again.
            raise BadRequestError(
                "Google did not provide offline access. Reconnect and grant access again.",
                code="reconnect_required",
            )
        credential.access_token = result.access_token
        credential.token_expiry = result.expiry
        credential.granted_scopes = " ".join(result.scopes)

        session_id = new_session_id()
        now = datetime.now(UTC)
        expires_at = now + self.session_ttl
        self.repo.add_login_session(
            LoginSession(
                id=hash_session_id(session_id),
                user_id=user.id,
                created_at=now,
                expires_at=expires_at,
            )
        )
        self.repo.commit()
        return NewLoginSession(
            user=CurrentUserRead(email=user.email, scopes=credential.scopes),
            session_id=session_id,
            expires_at=expires_at,
        )

    def authenticate(self, session_id: str | None) -> User:
        if not session_id:
            raise UnauthenticatedError("Authentication is required.")
        login_session = self.repo.get_active_login_session(
            hash_session_id(session_id), datetime.now(UTC)
        )
        if login_session is None:
            raise UnauthenticatedError("Session is missing or expired.")
        return login_session.user

    def describe(self, user: User) -> CurrentUserRead:
        credential = self.repo.get_credential(user.id)
        return CurrentUserRead(email=user.email, scopes=credential.scopes if credential else [])

    def logout(self, user: User, session_id: str | None, *, revoke_google_access: bool) -> None:
        if revoke_google_access:
            credential = self.repo.get_credential(user.id)
            if credential is not None:
                try:
                    self.oauth.revoke(self._refresh_token(credential))
                except TokenRevocationError as exc:
                    raise ExternalServiceError(
                        "Google access could not be revoked.", code="google_revoke_failed"
                    ) from exc
                self.repo.delete_credential(credential)
        if session_id:
            self.repo.delete_login_session(hash_session_id(session_id))
        self.repo.commit()

    def get_google_credentials(self, user: User) -> Credentials:
        """Load the user's Google credentials, refreshing (and saving) the access token."""
        credential = self.repo.get_credential(user.id)
        if credential is None:
            raise GoogleReauthRequiredError()

        credentials = self.oauth.build_credentials(
            refresh_token=self._refresh_token(credential),
            access_token=credential.access_token,
            expiry=credential.token_expiry,
            scopes=credential.scopes,
        )
        try:
            refreshed = self.oauth.refresh_if_needed(credentials)
        except RefreshError as exc:
            raise GoogleReauthRequiredError() from exc
        if refreshed:
            credential.access_token = credentials.token
            credential.token_expiry = credentials_expiry(credentials)
            self.repo.commit()
        return credentials

    @staticmethod
    def _refresh_token(credential: GoogleCredential) -> str:
        try:
            return decrypt_token(credential.encrypted_refresh_token)
        except TokenDecryptionError as exc:
            raise GoogleReauthRequiredError() from exc
