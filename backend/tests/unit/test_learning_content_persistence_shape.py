"""Offline SQL/metadata checks. These do not prove a PostgreSQL migration works."""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

from sqlalchemy.dialects.postgresql import dialect
from sqlalchemy.schema import CreateTable

from sketch2life.infrastructure.learning_content.tables import METADATA, SCHEMA

ROOT = Path(__file__).resolve().parents[3]
MIGRATION = ROOT / "backend/alembic/versions/20261017_lc_0001_content_publication.py"


def migration():
    spec = importlib.util.spec_from_file_location("lc_migration", MIGRATION)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_frozen_ddl_matches_metadata_exactly_except_whitespace() -> None:
    generated = ";".join(str(CreateTable(t).compile(dialect=dialect())).strip()
                         for t in METADATA.sorted_tables) + ";"
    normalize = lambda s: re.sub(r"\s+", "", s)  # noqa: E731
    assert normalize(migration().DDL) == normalize(generated)


def test_all_foreign_keys_stay_in_owned_schema() -> None:
    assert len(METADATA.tables) == 6
    for table in METADATA.tables.values():
        assert table.schema == SCHEMA
        for foreign_key in table.foreign_keys:
            assert foreign_key.column.table.schema == SCHEMA


def test_migration_is_independent_frozen_branch() -> None:
    module = migration()
    assert module.down_revision is None
    assert module.branch_labels == ("learning_content",)
    assert "infrastructure" not in MIGRATION.read_text(encoding="utf-8")


def test_metadata_has_scoped_receipt_key_and_record_cas() -> None:
    receipt = METADATA.tables[SCHEMA + ".receipt"]
    assert {c.name for c in receipt.primary_key} == {
        "organization_id", "principal_id", "request_id"}
    record = METADATA.tables[SCHEMA + ".record"]
    assert record.c.revision.nullable is False
    assert {c.name for c in record.primary_key} == {"organization_id", "record_id"}


def test_alembic_environment_manages_content_without_losing_other_modules() -> None:
    source = (ROOT / "backend/alembic/env.py").read_text(encoding="utf-8")
    assert "CorePersistenceBase.metadata, AI_JOBS_METADATA, CONTENT_METADATA" in source
    assert "{None, AI_JOBS_SCHEMA, CONTENT_SCHEMA}" in source
