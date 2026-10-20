"""Offline shape/guard proof, not PostgreSQL runtime or executed trigger proof."""

import importlib.util
import io
import re
from dataclasses import replace
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import dialect
from sqlalchemy.schema import CreateTable

from alembic import command
from sketch2life.application.ports.ai_policy import PolicyEvent
from sketch2life.domain.ai_policy.model import PolicyError, State
from sketch2life.infrastructure.ai_policy.sql import (
    SqlPolicyTransaction,
    validate_fresh,
    validate_write,
)
from sketch2life.infrastructure.ai_policy.tables import METADATA, OUTBOX, RECEIPT, REVIEW, SCHEMA
from sketch2life.infrastructure.config.settings import get_core_database_settings
from tests.unit.test_ai_policy_domain import NOW, draft, proof, submitted

ROOT = Path(__file__).resolve().parents[3]
MIGRATION = ROOT / "backend/alembic/versions/20261017_ap_0001_policy_lifecycle.py"


def migration():
    spec = importlib.util.spec_from_file_location("policy_migration", MIGRATION)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_frozen_table_ddl_matches_runtime_metadata():
    generated = ";".join(str(CreateTable(t).compile(dialect=dialect())).strip()
                         for t in METADATA.sorted_tables) + ";"
    assert re.sub(r"\s+", "", generated) == re.sub(r"\s+", "", migration().DDL)


def test_six_tables_and_no_foreign_schema_access():
    assert {t.name for t in METADATA.tables.values()} == {
        "record", "version", "review", "receipt", "event", "outbox"}
    for table in METADATA.tables.values():
        assert table.schema == SCHEMA == "ai_policy"
        assert all(fk.column.table.schema == SCHEMA for fk in table.foreign_keys)


def test_scoped_receipt_outbox_and_unique_review_revision():
    assert {c.name for c in RECEIPT.primary_key} == {
        "organization_id", "principal_id", "request_id"}
    assert {c.name for c in OUTBOX.primary_key} == {"organization_id", "event_id"}
    assert {c.name for fk in OUTBOX.foreign_key_constraints for c in fk.columns} == {
        "organization_id", "event_id"}
    assert any(isinstance(constraint, UniqueConstraint) and {
        c.name for c in constraint.columns} == {
            "organization_id", "record_id", "version", "review_revision"}
        for constraint in REVIEW.constraints)


def test_migration_frozen_independent_branch():
    module = migration()
    assert module.down_revision is None and module.depends_on is None
    assert module.branch_labels == ("ai_policy",)
    assert "infrastructure" not in MIGRATION.read_text(encoding="utf-8")


def test_offline_upgrade_and_downgrade_record_only_owned_ddl(monkeypatch):
    module, statements, dropped = migration(), [], []

    class Capture:
        def execute(self, statement):
            statements.append(statement)

        def drop_table(self, table, schema):
            dropped.append((schema, table))

    monkeypatch.setattr(module, "op", Capture())
    module.upgrade()
    assert statements[0] == "CREATE SCHEMA ai_policy"
    assert sum("CREATE TABLE" in statement for statement in statements) == 6
    assert sum("CREATE TRIGGER" in statement for statement in statements) == 4
    assert any("TG_OP = 'DELETE'" in statement for statement in statements)
    assert any("AI_POLICY_IMMUTABLE_PUBLICATION" in statement for statement in statements)
    module.downgrade()
    assert {table for schema, table in dropped if schema == "ai_policy"} == {
        "record", "version", "review", "receipt", "event", "outbox"}


def test_environment_adds_policy_without_replacing_existing_modules():
    source = (ROOT / "backend/alembic/env.py").read_text(encoding="utf-8")
    assert "CorePersistenceBase.metadata, AI_JOBS_METADATA, CONTENT_METADATA" in source
    assert "target_metadata.append(POLICY_METADATA)" in source
    assert "_MANAGED_SCHEMAS.add(POLICY_SCHEMA)" in source


@pytest.mark.parametrize("direction", ["upgrade", "downgrade"])
def test_actual_alembic_offline_render_no_server(direction, monkeypatch):
    buffer = io.StringIO()
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL",
                       "postgresql+psycopg://placeholder:placeholder@localhost/offline_only")
    get_core_database_settings.cache_clear()
    config = Config(str(ROOT / "backend/alembic.ini"), output_buffer=buffer)
    config.set_main_option("script_location", str(ROOT / "backend/alembic"))
    try:
        if direction == "upgrade":
            command.upgrade(config, "ai_policy@head", sql=True)
            assert "CREATE TRIGGER immutable_policy_version" in buffer.getvalue()
        else:
            command.downgrade(config, "ai_policy@head:base", sql=True)
            assert "DROP SCHEMA ai_policy" in buffer.getvalue()
        assert "CREATE TABLE learning_content" not in buffer.getvalue()
        assert "CREATE TABLE ai_jobs" not in buffer.getvalue()
    finally:
        get_core_database_settings.cache_clear()


@pytest.mark.parametrize("kind", ["content.create", "ai_policy.unknown", "create",
                                  "ai_policy.publish"])
def test_invalid_event_shape_before_sql(kind):
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_EVENT"):
        validate_write(draft(), PolicyEvent("event", kind, "author", NOW))


def test_hash_mismatch_before_sql():
    with pytest.raises(PolicyError, match="AI_POLICY_HASH_MISMATCH"):
        validate_write(replace(draft(), hash="b" * 64),
                       PolicyEvent("event", "ai_policy.create", "author", NOW))


@pytest.mark.parametrize("changes", [
    {"state": State.SUBMITTED}, {"context_revision": 1}, {"review_revision": 1},
    {"reviews": (proof(submitted()),)}, {"publication_review_ids": ("proof",)},
    {"publication_policy_version": "fixture"}, {"recalled_at": NOW}, {"recall_reason": "why"},
])
def test_new_version_cannot_inherit_lifecycle(changes):
    with pytest.raises(PolicyError, match="AI_POLICY_FRESH_VERSION_REQUIRED"):
        validate_fresh(replace(draft(), **changes))


@pytest.mark.parametrize("limit,after", [(0, 0), (101, 0), (True, 0), (1, -1), (1, True)])
def test_history_page_rejected_before_connection(limit, after):
    tx = SqlPolicyTransaction(None)
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_PAGE"):
        tx.review_history("school", "record", version=1, after_revision=after, limit=limit)
