from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import GoogleCredential, LoginSession, User


class AuthRepository:
    """Data access for users, their Google credentials and login sessions."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def commit(self) -> None:
        self.session.commit()

    # --- users ---

    def get_user_by_google_sub(self, google_sub: str) -> User | None:
        return self.session.scalar(select(User).where(User.google_sub == google_sub))

    def add_user(self, user: User) -> User:
        self.session.add(user)
        self.session.flush()  # assigns user.id
        return user

    # --- Google credentials ---

    def get_credential(self, user_id: int) -> GoogleCredential | None:
        return self.session.get(GoogleCredential, user_id)

    def add_credential(self, credential: GoogleCredential) -> None:
        self.session.add(credential)

    def delete_credential(self, credential: GoogleCredential) -> None:
        self.session.delete(credential)

    # --- login sessions ---

    def add_login_session(self, login_session: LoginSession) -> None:
        self.session.add(login_session)

    def get_active_login_session(self, session_hash: str, now: datetime) -> LoginSession | None:
        return self.session.scalar(
            select(LoginSession).where(
                LoginSession.id == session_hash,
                LoginSession.expires_at > now,
            )
        )

    def delete_login_session(self, session_hash: str) -> None:
        login_session = self.session.get(LoginSession, session_hash)
        if login_session is not None:
            self.session.delete(login_session)
