"""Offline ledger shape/codec; explicitly not concurrent/durable PostgreSQL proof."""

import importlib.util
import io
import json
import re
from dataclasses import asdict, replace
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy.dialects.postgresql import dialect
from sqlalchemy.schema import CreateTable

from alembic import command
from sketch2life.domain.ai_policy import accounting as domain
from sketch2life.domain.ai_policy.model import PolicyError
from sketch2life.infrastructure.ai_policy.accounting_sql import bucket_id, decode_reservation
from sketch2life.infrastructure.ai_policy.accounting_tables import (
    ACCOUNTING_METADATA,
    RESOURCE_SCOPE,
)
from sketch2life.infrastructure.config.settings import get_core_database_settings
from tests.unit.test_ai_policy_accounting import KEY, TERMS, held, proof

ROOT = Path(__file__).resolve().parents[3]
PATH = ROOT / "backend/alembic/versions/20261017_ap_0003_resource_ledger.py"


def migration():
    spec = importlib.util.spec_from_file_location("resource_ledger_migration", PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_frozen_forward_ledger_ddl_matches_own_metadata_exactly():
    compiled = (
        ";".join(
            str(CreateTable(t).compile(dialect=dialect())).strip()
            for t in ACCOUNTING_METADATA.sorted_tables
        )
        + ";"
    )
    assert re.sub(r"\s+", "", compiled) == re.sub(r"\s+", "", migration().DDL)
    assert len(ACCOUNTING_METADATA.tables) == 5
    assert migration().down_revision == "20261017_ap_0002"
    assert migration().branch_labels is None
    assert "infrastructure" not in PATH.read_text()
    for table in ACCOUNTING_METADATA.tables.values():
        assert table.schema == "ai_policy"
        assert all(fk.column.table.schema == "ai_policy" for fk in table.foreign_keys)


def test_global_scope_key_excludes_budget_window_and_definition():
    assert {c.name for c in RESOURCE_SCOPE.primary_key} == {"organization_id", "feature_scope"}
    for name in ("resource_receipt", "resource_event"):
        table = ACCOUNTING_METADATA.tables["ai_policy." + name]
        assert {c.name for fk in table.foreign_key_constraints for c in fk.columns} == {
            "organization_id",
            "feature_scope",
            "reservation_id",
        }


def test_frozen_triggers_cover_terminal_provenance_receipts_bucket_and_audit(monkeypatch):
    statements, dropped = [], []

    class Capture:
        def execute(self, statement):
            statements.append(statement)

        def drop_table(self, name, schema):
            dropped.append((schema, name))

    module = migration()
    monkeypatch.setattr(module, "op", Capture())
    module.upgrade()
    assert sum("CREATE TABLE" in s for s in statements) == 5
    assert sum("CREATE TRIGGER" in s for s in statements) == 4
    joined = "\n".join(statements)
    assert "OLD.state <> 'reserved'" in joined
    assert "OLD.payload - ARRAY['state','settlement']" in joined
    assert "OLD.key" in joined and "NEW.key" in joined
    assert "protect_history()" in joined
    assert "OLD.occurred_at, OLD.payload" in joined
    module.downgrade()
    assert dropped == [
        ("ai_policy", name)
        for name in (
            "resource_receipt",
            "resource_event",
            "resource_reservation",
            "budget_bucket",
            "resource_scope",
        )
    ]


@pytest.mark.parametrize("direction", ["upgrade", "downgrade"])
def test_actual_offline_branch_render_includes_new_ledger_only(direction, monkeypatch):
    output = io.StringIO()
    monkeypatch.setenv(
        "SKETCH2LIFE_DATABASE_URL",
        "postgresql+psycopg://placeholder:placeholder@localhost/offline_only",
    )
    get_core_database_settings.cache_clear()
    config = Config(str(ROOT / "backend/alembic.ini"), output_buffer=output)
    config.set_main_option("script_location", str(ROOT / "backend/alembic"))
    try:
        if direction == "upgrade":
            command.upgrade(config, "ai_policy@head", sql=True)
            assert "CREATE TABLE ai_policy.resource_scope" in output.getvalue()
            assert "CREATE TRIGGER immutable_resource_reservation" in output.getvalue()
        else:
            command.downgrade(config, "ai_policy@head:20261017_ap_0002", sql=True)
            assert "DROP TABLE ai_policy.resource_scope" in output.getvalue()
            assert "DROP TABLE ai_policy.effective_scope" not in output.getvalue()
        assert "CREATE TABLE ai_jobs" not in output.getvalue()
        assert "CREATE TABLE learning_content" not in output.getvalue()
    finally:
        get_core_database_settings.cache_clear()


@pytest.mark.parametrize("terminal", [False, True])
def test_json_codec_roundtrip_keeps_exact_original_terms_and_fixture_label(terminal):
    result = held()
    if terminal:
        result = domain.settle(result.snapshot, result.reservation, proof())
    decoded = decode_reservation(json.loads(json.dumps(asdict(result.reservation))))
    assert decoded == result.reservation and decoded.terms == TERMS
    assert not decoded.actual_usage_proven


@pytest.mark.parametrize(
    "change",
    [
        {"estimated_units": True},
        {"estimated_units": -1},
        {"state": "unknown"},
        {"settlement": {}},
        {"unexpected": "field"},
        {"terms": {}},
        {"reservation_id": "bad/id"},
        {"request_digest": "not-a-hash"},
    ],
)
def test_invalid_stored_reservation_cannot_be_used_as_a_ledger_grant(change):
    raw = json.loads(json.dumps(asdict(held().reservation))) | change
    with pytest.raises(PolicyError):
        decode_reservation(raw)


@pytest.mark.parametrize(
    "key",
    [
        replace(KEY, organization_id="other"),
        replace(KEY, feature_scope="other"),
        replace(KEY, unit="other"),
        replace(KEY, window_id="other"),
        replace(KEY, definition=replace(KEY.definition, hash="b" * 64)),
    ],
)
def test_bucket_digest_binds_entire_original_budget_scope(key):
    assert bucket_id(key) != bucket_id(KEY)
    assert bucket_id(KEY) == bucket_id(replace(KEY))
