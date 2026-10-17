"""Offline copy inventory metadata/codec/paging invariants, not actual PostgreSQL proof."""

import importlib.util
import io
import re
from pathlib import Path

import pytest
from alembic.config import Config
from pydantic import ValidationError
from sqlalchemy.dialects.postgresql import dialect
from sqlalchemy.schema import CreateTable

from alembic import command
from sketch2life.application.ports.ai_policy_copy_registry import (
    CopyRegistryPage,
    RegisteredProviderCopy,
)
from sketch2life.contracts.schemas.ai_policy import PolicyDefinitionRef
from sketch2life.contracts.schemas.ai_policy_copy import CopyReceiptReference
from sketch2life.contracts.schemas.ai_policy_copy_registry import (
    CopyCoverageObservation,
    CopyRegistryRegistration,
)
from sketch2life.domain.ai_jobs.provider_copy import CopyStatus
from sketch2life.domain.ai_policy.model import PolicyError
from sketch2life.infrastructure.ai_policy.copy_registry_sql import (
    SqlProviderCopyRegistryTransaction,
    decode_registration,
    validate_page,
)
from sketch2life.infrastructure.ai_policy.copy_registry_tables import COPY_METADATA
from sketch2life.infrastructure.config.settings import get_core_database_settings
from tests.unit.test_ai_policy_domain import NOW

ROOT = Path(__file__).resolve().parents[3]
PATH = ROOT / "backend/alembic/versions/20261017_ap_0004_copy_inventory.py"
REF = PolicyDefinitionRef(ref="fixture-profile", version=1, hash="a" * 64)


def registration(**changes):
    return CopyRegistryRegistration.model_validate(
        dict(
            organization_id="school",
            scope_ref="scope",
            copy_id="copy",
            kind="input",
            original_profile_ref=REF,
        )
        | changes
    )


def observation(**changes):
    return CopyCoverageObservation.model_validate(
        dict(
            organization_id="school",
            scope_ref="scope",
            expected_revision=0,
            registry_revision="fixture-registry",
            attestation_ref=CopyReceiptReference(ref="fixture-coverage", hash="b" * 64),
            required_sources=("fixture-input", "fixture-output"),
            observed_sources=("fixture-input",),
        )
        | changes
    )


def migration():
    spec = importlib.util.spec_from_file_location("copy_inventory_migration", PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_frozen_inventory_ddl_matches_owned_metadata_and_extends_branch():
    ddl = (
        ";".join(
            str(CreateTable(t).compile(dialect=dialect())).strip()
            for t in COPY_METADATA.sorted_tables
        )
        + ";"
    )
    assert re.sub(r"\s+", "", ddl) == re.sub(r"\s+", "", migration().DDL)
    assert migration().down_revision == "20261017_ap_0003"
    assert migration().branch_labels is None
    assert len(COPY_METADATA.tables) == 4
    assert "infrastructure" not in PATH.read_text()
    for table in COPY_METADATA.tables.values():
        assert table.schema == "ai_policy"
        assert all(fk.column.table.schema == "ai_policy" for fk in table.foreign_keys)


def test_frozen_inventory_history_and_purge_fence_guards(monkeypatch):
    statements, dropped = [], []

    class Capture:
        def execute(self, statement):
            statements.append(statement)

        def drop_table(self, name, schema):
            dropped.append((schema, name))

    module = migration()
    monkeypatch.setattr(module, "op", Capture())
    module.upgrade()
    assert sum("CREATE TABLE" in s for s in statements) == 4
    assert sum("CREATE TRIGGER" in s for s in statements) == 4
    assert any("OLD.purging AND NOT NEW.purging" in s for s in statements)
    assert any("NEW.revision <> OLD.revision + 1" in s for s in statements)
    assert any("OLD.principal_id, OLD.occurred_at, OLD.payload" in s for s in statements)
    module.downgrade()
    assert dropped == [
        ("ai_policy", name)
        for name in (
            "copy_registry_event",
            "copy_registration",
            "copy_coverage",
            "copy_scope",
        )
    ]


@pytest.mark.parametrize("direction", ["upgrade", "downgrade"])
def test_offline_branch_renders_inventory_without_foreign_modules(direction, monkeypatch):
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
            assert "CREATE TABLE ai_policy.copy_registration" in output.getvalue()
        else:
            command.downgrade(config, "ai_policy@head:20261017_ap_0003", sql=True)
            assert "DROP TABLE ai_policy.copy_scope" in output.getvalue()
            assert "DROP TABLE ai_policy.resource_scope" not in output.getvalue()
        assert "CREATE TABLE ai_jobs" not in output.getvalue()
    finally:
        get_core_database_settings.cache_clear()


@pytest.mark.parametrize("quarantined", [False, True])
def test_original_profile_codec_and_initial_metadata_reuse_foundation(quarantined):
    item = registration(original_profile_ref=REF.model_copy(update={"version": 2}))
    result = decode_registration(
        item.model_dump(mode="json") | {"initially_quarantined": quarantined}
    )
    assert result.registration.original_profile_ref.version == 2
    assert result.initial_copy().status == (
        CopyStatus.PURGE_REQUESTED if quarantined else CopyStatus.DISCOVERED
    )
    assert not result.initial_copy().actual_deletion_proven


@pytest.mark.parametrize(
    "change",
    [
        {"original_profile_ref": {"ref": "fixture", "version": True, "hash": "a" * 64}},
        {"initially_quarantined": 1},
        {"kind": "unknown"},
        {"copy_id": "https://private.example"},
    ],
)
def test_invalid_stored_registration_cannot_be_promoted(change):
    value = registration().model_dump(mode="json") | {"initially_quarantined": False} | change
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_COPY_REGISTRY_STORAGE"):
        decode_registration(value)


@pytest.mark.parametrize(
    "change",
    [
        {"required_sources": ()},
        {"required_sources": ("one", "one")},
        {"observed_sources": ("fixture-input", "fixture-input")},
        {"observed_sources": ("not-required",)},
        {"expected_revision": True},
    ],
)
def test_coverage_requires_explicit_unique_scoped_sources_and_integer_revision(change):
    with pytest.raises(ValidationError):
        observation(**change)


def test_empty_inventory_unknown_and_reported_coverage_is_not_deletion():
    assert CopyRegistryPage(0, False, (), None, None).coverage_status == "unknown"
    assert CopyRegistryPage(1, False, (), None, observation()).coverage_status == "partial"
    full = observation(observed_sources=("fixture-output", "fixture-input"))
    assert CopyRegistryPage(1, False, (), None, full).coverage_status == "reported_complete"
    assert not hasattr(full, "actual_deletion_proven")
    assert (
        RegisteredProviderCopy(registration(), True).initial_copy().status
        == CopyStatus.PURGE_REQUESTED
    )


@pytest.mark.parametrize(
    "values",
    [
        {"limit": 0},
        {"limit": 257},
        {"limit": True},
        {"after": "copy"},
        {"expected_revision": True},
        {"expected_revision": -1},
    ],
)
def test_bad_or_unversioned_cursor_rejected(values):
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_COPY_REGISTRY_PAGE"):
        validate_page(**(dict(limit=1, after=None, expected_revision=None) | values))


def test_missing_scope_read_does_not_query_later_phantom_rows():
    class Missing:
        def mappings(self):
            return self

        def one_or_none(self):
            return None

    class Connection:
        def __init__(self):
            self.calls = 0

        def execute(self, query):
            self.calls += 1
            assert self.calls == 1  # Page cannot issue post-absence queries.
            return Missing()

    connection = Connection()
    tx = SqlProviderCopyRegistryTransaction(
        connection, "school", "scope", principal_id="worker", for_update=False, clock=lambda: NOW
    )
    assert tx.page(limit=1) == CopyRegistryPage(0, False, (), None, None)
    assert tx.get("copy") is None
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_REGISTRY_READ_ONLY"):
        tx.register(registration())
    assert connection.calls == 1


@pytest.mark.parametrize("extra", ["status", "verified", "actual_deletion_proven"])
def test_registration_cannot_supply_terminal_state_or_deletion_assertions(extra):
    with pytest.raises(ValidationError):
        CopyRegistryRegistration.model_validate(
            registration().model_dump(mode="python") | {extra: True},
        )


def test_bad_audit_clock_rejected_before_copy_registration_insert():
    class Rows:
        def __init__(self, row=None):
            self.row = row

        def mappings(self):
            return self

        def one_or_none(self):
            return self.row

    class Connection:
        def __init__(self):
            self.inserted = []

        def execute(self, query):
            if query.is_insert:
                self.inserted.append(query.table.name)
                return Rows()
            if query.get_final_froms()[0].name == "copy_scope":
                return Rows({"revision": 0, "purging": False})
            return Rows()

    connection = Connection()
    tx = SqlProviderCopyRegistryTransaction(
        connection,
        "school",
        "scope",
        principal_id="worker",
        for_update=True,
        clock=lambda: NOW.replace(tzinfo=None),
    )
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_TIME"):
        tx.register(registration())
    assert connection.inserted == ["copy_scope"]
