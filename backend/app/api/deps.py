"""Shared dependencies for feature routers."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.features.auth.deps import CurrentUser, GoogleCredentialsDep

SessionDep = Annotated[Session, Depends(get_session)]

__all__ = ["CurrentUser", "GoogleCredentialsDep", "SessionDep"]
