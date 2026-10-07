"""Engine and session lifecycle. The engine is created in the app lifespan, not at import."""

from collections.abc import Iterator

from sqlalchemy import Engine, create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base

_engine: Engine | None = None
_sessionmaker: sessionmaker[Session] | None = None


def init_engine(url: str) -> None:
    global _engine, _sessionmaker
    if url.startswith("sqlite"):
        in_memory = url in ("sqlite://", "sqlite:///:memory:")
        _engine = create_engine(
            url,
            connect_args={"check_same_thread": False},
            # One shared connection, otherwise every connection gets its own empty database.
            poolclass=StaticPool if in_memory else None,
        )
    else:
        _engine = create_engine(url, pool_pre_ping=True)
    _sessionmaker = sessionmaker(bind=_engine, expire_on_commit=False)


def get_engine() -> Engine:
    if _engine is None:
        raise RuntimeError("engine not initialised (call init_engine in lifespan)")
    return _engine


def dispose_engine() -> None:
    if _engine is not None:
        _engine.dispose()


def create_tables() -> None:
    """Create missing tables. Replace with Alembic migrations once schemas start changing."""
    import app.db.models  # noqa: F401  - registers every model on Base.metadata

    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    _add_missing_columns(engine)


# Columns added after their table was first created: create_all only creates missing tables.
# (table, column, SQL type and default)
_ADDED_COLUMNS = [
    ("conversations", "prompt_caching", "BOOLEAN NOT NULL DEFAULT 1"),
]


def _add_missing_columns(engine: Engine) -> None:
    inspector = inspect(engine)
    with engine.begin() as connection:
        for table, column, definition in _ADDED_COLUMNS:
            existing = {c["name"] for c in inspector.get_columns(table)}
            if column not in existing:
                connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}"))


def session_factory() -> sessionmaker[Session]:
    """For work that outlives a request (SSE streams, background jobs): open short sessions."""
    if _sessionmaker is None:
        raise RuntimeError("engine not initialised (call init_engine in lifespan)")
    return _sessionmaker


def get_session() -> Iterator[Session]:
    """Request-scoped session. Services commit explicitly; uncommitted work is rolled back."""
    with session_factory()() as session:
        yield session
