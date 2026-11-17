"""Runtime-only PostgreSQL engine/session construction."""

from __future__ import annotations

from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from sketch2life.infrastructure.config.settings import get_core_database_settings


class CoreDatabaseConfigurationError(RuntimeError):
    """Raised when the durable core database URL is absent or unsupported."""


def create_core_engine(database_url: str | None = None) -> Engine:
    if database_url is None:
        configured_url = get_core_database_settings().database_url
        url_value = configured_url.get_secret_value() if configured_url is not None else None
    else:
        url_value = database_url
    if not url_value:
        raise CoreDatabaseConfigurationError(
            "SKETCH2LIFE_DATABASE_URL must be set by the runtime environment"
        )
    try:
        url = make_url(url_value)
    except Exception:
        raise CoreDatabaseConfigurationError("database URL is invalid") from None
    if url.drivername not in {"postgresql", "postgresql+psycopg"}:
        raise CoreDatabaseConfigurationError("BE1-02 requires the PostgreSQL psycopg driver")
    if url.drivername == "postgresql":
        url = url.set(drivername="postgresql+psycopg")
    return create_engine(
        url,
        pool_pre_ping=True,
        hide_parameters=True,
        pool_recycle=1800,
    )


def create_core_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


__all__ = [
    "CoreDatabaseConfigurationError",
    "create_core_engine",
    "create_core_session_factory",
]
