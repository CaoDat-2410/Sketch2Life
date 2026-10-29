"""Closed codec, owned schema and frozen migration offline checks, NOT SQL execution."""

import io
import runpy
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine

from sketch2life.application.ports.preset_automation import Decision, LocalReceipt
from sketch2life.application.preset_governance import receipt_key
from sketch2life.domain.preset_automation.model import (
    EffectReceipt,
    IntentState,
    PresetError,
    Stamp,
)
from sketch2life.infrastructure.preset_automation.codec import decode, encode
from sketch2life.infrastructure.preset_automation.sql import (
    PresetRows,
    SqlPresetStore,
    validate_change,
)
from sketch2life.infrastructure.preset_automation.tables import METADATA
from tests.preset_automation_fixtures import NOW, library
from tests.unit.test_preset_automation_domain import intent


def migration():
    return runpy.run_path(
        str(
            Path(__file__).resolve().parents[2]
            / "alembic/versions/20261019_pa_0001_preset_automation.py"
        )
    )


def objects():
    row = intent()
    return [
        library(),
        library(True),
        row,
        LocalReceipt("teacher", "key", "a" * 64, row.intent_id, 1, 1),
        EffectReceipt(
            row.intent_id,
            "school",
            "session",
            row.hash,
            "applied",
            row.observed,
            Stamp(1, 2, 1, 2),
            "native",
            "applied",
        ),
        Decision(
            "decision",
            "school",
            "session",
            "teacher",
            "rule",
            row.source,
            row.observed,
            "assumed-policy",
            "queued",
            row.intent_id,
            NOW,
        ),
    ]


@pytest.mark.parametrize("index", range(6))
def test_closed_native_codec_roundtrip(index):
    value = objects()[index]
    assert decode(encode(value)) == value


@pytest.mark.parametrize(
    "mutation",
    [
        "format",
        "kind",
        "extra",
        "missing",
        "boolrevision",
        "nullrevision",
        "unknownstate",
        "extra_body",
        "tuple_string",
        "naive_time",
        "bad_hash",
    ],
)
def test_stored_payload_corruption_never_loads(mutation):
    payload = deepcopy(encode(library()))
    if mutation == "format":
        payload["format"] = "other"
    elif mutation == "kind":
        payload["kind"] = "dynamic.import.Class"
    elif mutation == "extra":
        payload["unexpected"] = True
    elif mutation == "missing":
        payload["value"].pop("actor")
    elif mutation == "boolrevision":
        payload["value"]["revision"] = True
    elif mutation == "nullrevision":
        payload["value"]["revision"] = None
    elif mutation == "unknownstate":
        payload["value"]["versions"][0]["state"] = "effective"
    elif mutation == "extra_body":
        payload["value"]["versions"][0]["body"]["autoapprove"] = True
    elif mutation == "tuple_string":
        payload["value"]["versions"] = "not-array"
    elif mutation == "naive_time":
        payload["value"]["changed_at"] = "2026-10-19T12:00:00"
    else:
        payload = encode(objects()[4])
        payload["value"]["intent_hash"] = "x" * 64
    with pytest.raises(PresetError, match="STORAGE_CORRUPT"):
        decode(payload)


def test_own_tables_no_crossowner_fk_and_frozen_offline_migration():
    assert set(METADATA.tables) == {"preset_automation.head", "preset_automation.history"}
    assert all(not t.foreign_keys for t in METADATA.tables.values())
    output = io.StringIO()
    with Operations.context(
        MigrationContext.configure(
            dialect_name="postgresql", opts={"as_sql": True, "output_buffer": output}
        )
    ):
        migration()["upgrade"]()
        migration()["downgrade"]()
    ddl = output.getvalue()
    assert "CREATE SCHEMA" in ddl and "guard_rows" in ddl and "terminal intent" in ddl
    assert "CASCADE" not in ddl and "core." not in ddl


def test_sqlite_not_substituted_for_postgres():
    engine = create_engine("sqlite://")
    try:
        with (
            pytest.raises(PresetError, match="POSTGRESQL_REQUIRED"),
            SqlPresetStore(engine).transaction("school", "session"),
        ):
            pass
    finally:
        engine.dispose()


@pytest.mark.parametrize("root", [2, 3, 4, 5])
def test_immutable_receipts_decisions_and_terminal_intent(root):
    row = objects()[root]
    if root == 2:
        row = replace(row, state=IntentState.APPLIED)
    with pytest.raises(PresetError):
        validate_change(row, row)


@pytest.mark.parametrize(
    "org,scope,key",
    [
        ("other", "library", "preset"),
        ("school", "session", "preset"),
        ("school", "library", "other"),
    ],
)
def test_scope_envelope_mismatch_rejected_without_sql(org, scope, key):
    engine = create_engine("sqlite://")
    try:
        with engine.connect() as conn:
            # Bypass constructor only to isolate deterministic envelope validation.
            rows = object.__new__(PresetRows)
            rows.conn, rows.org, rows.scope = conn, org, scope
            with pytest.raises(PresetError):
                rows._bind(key, library())
    finally:
        engine.dispose()


def test_receipt_key_binds_actor_not_only_client_key():
    assert receipt_key("teacher", "key") != receipt_key("other", "key")
