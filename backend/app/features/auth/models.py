from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UTCDateTime, utc_now


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    google_sub: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(320))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)

    google_credential: Mapped["GoogleCredential | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    sessions: Mapped[list["LoginSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class GoogleCredential(Base):
    __tablename__ = "google_credentials"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    encrypted_refresh_token: Mapped[str] = mapped_column(Text)
    access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_expiry: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    granted_scopes: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now, onupdate=utc_now)

    user: Mapped[User] = relationship(back_populates="google_credential")

    @property
    def scopes(self) -> list[str]:
        return self.granted_scopes.split()


class LoginSession(Base):
    __tablename__ = "sessions"

    # SHA-256 hash of the session ID. The raw ID exists only in the browser cookie.
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime(), index=True)

    user: Mapped[User] = relationship(back_populates="sessions")
