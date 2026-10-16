"""Alembic environment for the BE1-02 core relational schema and the BE2 ``ai_jobs`` branch.

One environment, one ``alembic_version`` table, independent module branches (``be1_core``,
``ai_jobs``). Autogenerate compares only the default schema and ``ai_jobs``; it never reflects
or drops objects in other schemas.
"""

from __future__ import annotations

from logging.config import fileConfig

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.pool import NullPool

from alembic import context
from sketch2life.infrastructure.ai_jobs.sql.tables import AI_JOBS_METADATA, AI_JOBS_SCHEMA
from sketch2life.infrastructure.config.settings import get_core_database_settings
from sketch2life.infrastructure.persistence import be1_models as _be1_models  # noqa: F401
from sketch2life.infrastructure.persistence.core_models import CorePersistenceBase

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = [CorePersistenceBase.metadata, AI_JOBS_METADATA]
_MANAGED_SCHEMAS = {None, AI_JOBS_SCHEMA}


def _include_name(name: str | None, type_: str, parent_names: object) -> bool:
    if type_ == "schema":
        return name in _MANAGED_SCHEMAS
    return True


def _database_url() -> str:
    configured = get_core_database_settings().database_url
    value = configured.get_secret_value() if configured is not None else None
    if not value:
        raise RuntimeError("SKETCH2LIFE_DATABASE_URL must be provided at runtime")
    try:
        url = make_url(value)
    except Exception:
        raise RuntimeError("SKETCH2LIFE_DATABASE_URL is invalid") from None
    if url.drivername not in {"postgresql", "postgresql+psycopg"}:
        raise RuntimeError("core migrations require PostgreSQL with psycopg")
    if url.drivername == "postgresql":
        url = url.set(drivername="postgresql+psycopg")
    return url.render_as_string(hide_password=False)


def run_migrations_offline() -> None:
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        include_schemas=True,
        include_name=_include_name,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(
        _database_url(),
        poolclass=NullPool,
        hide_parameters=True,
    )
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            include_schemas=True,
            include_name=_include_name,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
