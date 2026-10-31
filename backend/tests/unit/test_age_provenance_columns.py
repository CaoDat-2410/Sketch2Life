from __future__ import annotations

import importlib.util
import io
from collections.abc import Callable
from pathlib import Path
from typing import Protocol, cast

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.contracts.schemas.be1_runtime import CreateProfileRequest
from sketch2life.infrastructure.persistence.be1_models import ManagedProfileModel
from sketch2life.interfaces.http.routers import be1_registry
from sqlalchemy import Table
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import Dialect
from sqlalchemy.schema import DefaultClause


class _AgeProvenanceMigration(Protocol):
    def upgrade(self) -> None: ...

    def downgrade(self) -> None: ...


def test_managed_profile_has_persisted_age_source_and_revision_with_closed_checks() -> None:
    table = cast(Table, ManagedProfileModel.__table__)
    assert {"age_revision", "age_source"} <= set(table.c.keys())

    revision = table.c.age_revision
    source = table.c.age_source
    assert not revision.nullable
    assert isinstance(revision.server_default, DefaultClause)
    assert str(revision.server_default.arg) == "1"
    assert not source.nullable
    assert any(
        "age_revision >= 1" in str(check.sqltext).lower()
        for check in table.constraints
        if hasattr(check, "sqltext")
    )
    source_check = " ".join(
        str(check.sqltext)
        for check in table.constraints
        if hasattr(check, "sqltext") and "age_source" in str(check.sqltext)
    )
    assert all(
        value in source_check for value in ("LEGACY_UNKNOWN", "SYNTHETIC_FIXTURE", "ADULT_DECLARED")
    )


def test_age_provenance_migration_is_pinned_to_the_be1_core_head() -> None:
    migration = (
        Path(__file__).resolve().parents[2]
        / "alembic"
        / "versions"
        / "20261101_be1_age_provenance.py"
    )
    assert migration.is_file()
    source = migration.read_text(encoding="utf-8")
    assert 'revision = "20261101_be1_age_0001"' in source
    assert 'down_revision = "20261031_be1_se_0001"' in source
    assert "LEGACY_UNKNOWN" in source


def test_age_provenance_migration_offline_sql_is_scoped_and_reversible() -> None:
    migration_path = (
        Path(__file__).resolve().parents[2]
        / "alembic"
        / "versions"
        / "20261101_be1_age_provenance.py"
    )
    spec = importlib.util.spec_from_file_location("be1_age_provenance_migration", migration_path)
    assert spec is not None and spec.loader is not None
    migration_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration_module)
    migration = cast(_AgeProvenanceMigration, migration_module)
    dialect_factory = cast(Callable[[], Dialect], postgresql.dialect)

    upgrade_buffer = io.StringIO()
    upgrade_context = MigrationContext.configure(
        dialect=dialect_factory(),
        opts={"as_sql": True, "output_buffer": upgrade_buffer},
    )
    with Operations.context(upgrade_context):
        migration.upgrade()
    upgrade_sql = upgrade_buffer.getvalue().lower()
    assert "be1_managed_profiles" in upgrade_sql
    assert "age_revision" in upgrade_sql and "age_source" in upgrade_sql
    assert "legacy_unknown" in upgrade_sql
    assert "age_revision >= 1" in upgrade_sql
    assert "synthetic_fixture" in upgrade_sql and "adult_declared" in upgrade_sql
    assert "create table" not in upgrade_sql
    assert "drop table" not in upgrade_sql

    downgrade_buffer = io.StringIO()
    downgrade_context = MigrationContext.configure(
        dialect=dialect_factory(),
        opts={"as_sql": True, "output_buffer": downgrade_buffer},
    )
    with Operations.context(downgrade_context):
        migration.downgrade()
    downgrade_sql = downgrade_buffer.getvalue().lower()
    assert "be1_managed_profiles" in downgrade_sql
    assert "age_revision" in downgrade_sql and "age_source" in downgrade_sql
    assert "drop table" not in downgrade_sql


def test_registry_profile_creation_records_adult_declared_age_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeSession:
        def __init__(self) -> None:
            self.rows: list[object] = []

        def scalar(self, _statement: object) -> object:
            return object()

        def add_all(self, rows: list[object]) -> None:
            self.rows.extend(rows)

        def flush(self) -> None:
            return None

    monkeypatch.setattr(be1_registry, "require_assignment", lambda *args, **kwargs: None)
    monkeypatch.setattr(be1_registry, "get_class", lambda *args, **kwargs: object())
    monkeypatch.setattr(be1_registry, "audit", lambda *args, **kwargs: None)
    monkeypatch.setattr(be1_registry, "event", lambda *args, **kwargs: None)
    monkeypatch.setattr(be1_registry, "commit", lambda *args, **kwargs: None)
    db = FakeSession()
    principal = VerifiedPrincipal(
        subject="synthetic-adult",
        issuer="synthetic-test",
        roles=frozenset(),
        token_id="synthetic-token",
    )

    be1_registry.create_profile(
        "synthetic-org",
        "synthetic-class",
        CreateProfileRequest(
            child_id="synthetic-child",
            class_id="synthetic-class",
            consent_id="synthetic-consent",
            purpose_ref="synthetic-purpose",
            display_name="Synthetic profile",
            age_months=60,
        ),
        principal,
        db,  # type: ignore[arg-type]
    )

    profile = next(row for row in db.rows if isinstance(row, ManagedProfileModel))
    assert profile.age_revision == 1
    assert profile.age_source == "ADULT_DECLARED"
