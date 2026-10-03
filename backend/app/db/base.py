from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, Dialect, TypeDecorator
from sqlalchemy.orm import DeclarativeBase


def utc_now() -> datetime:
    return datetime.now(UTC)


class UTCDateTime(TypeDecorator[datetime]):
    """Store and return timezone-aware UTC datetimes (SQLite drops tzinfo)."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:  # noqa: ARG002
        if value is not None and value.tzinfo is None:
            raise ValueError("naive datetime; use datetime.now(UTC)")
        return value

    def process_result_value(self, value: Any, dialect: Dialect) -> datetime | None:  # noqa: ARG002
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=UTC)  # type: ignore[no-any-return]
        return value  # type: ignore[no-any-return]


class Base(DeclarativeBase):
    pass
