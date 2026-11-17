"""Forward activation migration/metadata consistency; no executed PostgreSQL proof."""

import importlib.util
import re
from pathlib import Path

from sqlalchemy.dialects.postgresql import dialect
from sqlalchemy.schema import CreateTable

from sketch2life.infrastructure.ai_policy.activation_tables import ACTIVATION_METADATA

PATH = Path(__file__).resolve().parents[3] / (
    "backend/alembic/versions/20261017_ap_0002_effective_scope.py")


def migration():
    spec = importlib.util.spec_from_file_location("policy_activation_migration", PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_forward_migration_extends_lifecycle_without_rewriting_it():
    module = migration()
    assert module.down_revision == "20261017_ap_0001" and module.branch_labels is None
    assert "infrastructure" not in PATH.read_text(encoding="utf-8")


def test_frozen_activation_ddl_matches_metadata():
    ddl = ";".join(str(CreateTable(t).compile(dialect=dialect())).strip()
                   for t in ACTIVATION_METADATA.sorted_tables) + ";"
    assert re.sub(r"\s+", "", ddl) == re.sub(r"\s+", "", migration().DDL)
    for table in ACTIVATION_METADATA.tables.values():
        assert table.schema == "ai_policy"
        assert all(fk.column.table.schema == "ai_policy" for fk in table.foreign_keys)


def test_frozen_transition_immutable_payload_allows_delivery_marker_only(monkeypatch):
    statements, dropped = [], []

    class Capture:
        def execute(self, statement):
            statements.append(statement)

        def drop_table(self, table, schema):
            dropped.append((schema, table))

    module = migration()
    monkeypatch.setattr(module, "op", Capture())
    module.upgrade()
    assert any("immutable_scope_event" in statement for statement in statements)
    assert any("OLD.payload" in statement and "NEW.payload" in statement
               for statement in statements)
    module.downgrade()
    assert dropped == [("ai_policy", "scope_transition"), ("ai_policy", "effective_scope")]
