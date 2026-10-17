"""Offline codec/SQL write/migration shape checks, not actual PostgreSQL proof."""

import importlib.util
import re
from pathlib import Path

import pytest
from sqlalchemy.dialects.postgresql import dialect
from sqlalchemy.schema import CreateTable

from sketch2life.domain.ai_policy.copy_delivery import DeliveryStatus, HookOutcome
from sketch2life.domain.ai_policy.model import PolicyError
from sketch2life.infrastructure.ai_policy.copy_delivery_codec import (
    decode_delivery,
    encode_delivery,
)
from sketch2life.infrastructure.ai_policy.copy_registry_sql import (
    SqlProviderCopyRegistryTransaction,
)
from sketch2life.infrastructure.ai_policy.copy_registry_tables import (
    COPY_DELIVERY,
    COPY_DELIVERY_HISTORY,
)
from tests.unit.test_ai_policy_copy_delivery import claim, finish, response


@pytest.mark.parametrize("outcome", list(HookOutcome))
def test_delivery_states_roundtrip_with_claim_history_and_unverified_reference(outcome):
    state = claim()
    assert decode_delivery(encode_delivery(state)) == state
    done = finish(state, response(outcome))
    assert decode_delivery(encode_delivery(done)) == done
    assert done.status is not DeliveryStatus.QUEUED


@pytest.mark.parametrize(
    "change",
    [
        {"revision": True},
        {"status": "deleted"},
        {"claim_token": None},
        {"claim_started_at": None},
        {"claim_expires_at": None},
        {"used_tokens": []},
        {"used_tokens": ["claim-1", "claim-1"]},
        {"actual_deletion_proven": True},
        {"last_response": {}},
    ],
)
def test_storage_codec_rejects_forged_or_incomplete_claim_snapshot(change):
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_COPY_DELIVERY_STORAGE"):
        decode_delivery(encode_delivery(claim()) | change)


@pytest.mark.parametrize("revision", [0, 1])
def test_delivery_write_snapshot_history_and_event_are_in_one_transaction(revision):
    from sketch2life.domain.ai_policy.copy_delivery import DeliveryState

    old = claim() if revision else DeliveryState("a" * 64, "b" * 64)
    new = finish(old) if revision else claim()
    statements, events = [], []

    class Result:
        rowcount = 1

    class Connection:
        def execute(self, statement):
            statements.append(statement)
            return Result()

    tx = SqlProviderCopyRegistryTransaction.__new__(SqlProviderCopyRegistryTransaction)
    tx.connection, tx.writable = Connection(), True
    tx.organization_id, tx.scope_ref = "school", "scope"
    tx._advance = lambda kind, payload: events.append((kind, payload))
    assert tx._store_delivery(old, new) == new
    assert statements[0].is_update == bool(revision)
    assert [s.table.name for s in statements] == ["copy_delivery", "copy_delivery_history"]
    assert len(events) == 1 and events[0][1]["delivery_revision"] == new.revision
    assert tx._store_delivery(new, new) == new
    assert len(statements) == 2 and len(events) == 1


def test_cas_miss_does_not_append_history_or_outbox():
    class Result:
        rowcount = 0

    class Connection:
        def execute(self, statement):
            assert statement.is_update
            return Result()

    tx = SqlProviderCopyRegistryTransaction.__new__(SqlProviderCopyRegistryTransaction)
    tx.connection, tx.writable = Connection(), True
    tx.organization_id, tx.scope_ref = "school", "scope"
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_DELIVERY_STALE"):
        tx._store_delivery(claim(), finish(claim()))


@pytest.mark.parametrize(
    "change",
    [
        {"revision": 2},
        {"status": "pending"},
        {"snapshot": encode_delivery(claim()) | {"binding_digest": "f" * 64}},
    ],
)
def test_sql_read_compares_snapshot_to_original_intent_and_state_columns(change):
    from tests.ai_policy_copy_operation_fixtures import schedule, setup

    service, _, _ = setup()
    envelope = schedule(service)
    state = claim()
    # Bind the synthetic state to an actual immutable envelope from the fixture.
    from dataclasses import replace

    state = replace(
        state, operation_key=envelope.operation_key, binding_digest=envelope.binding_digest
    )
    row = dict(revision=1, status="in_flight", snapshot=encode_delivery(state)) | change

    class Rows:
        def mappings(self):
            return self

        def one_or_none(self):
            return row

    class Connection:
        def execute(self, statement):
            return Rows()

    tx = SqlProviderCopyRegistryTransaction.__new__(SqlProviderCopyRegistryTransaction)
    tx.connection = Connection()
    tx.organization_id, tx.scope_ref = "school", "scope"
    tx.get_operation = lambda key: envelope
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_COPY_DELIVERY_STORAGE"):
        tx.get_delivery(envelope.operation_key)


def test_unknown_operation_cannot_create_a_lazy_queued_state():
    tx = SqlProviderCopyRegistryTransaction.__new__(SqlProviderCopyRegistryTransaction)
    tx.get_operation = lambda key: None
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_OPERATION_NOT_FOUND"):
        tx.get_delivery("a" * 64)


def test_persistence_claim_and_finish_require_write_transaction_before_read():
    from tests.unit.test_ai_policy_copy_delivery import DEADLINE

    tx = SqlProviderCopyRegistryTransaction.__new__(SqlProviderCopyRegistryTransaction)
    tx.writable = False
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_REGISTRY_READ_ONLY"):
        tx.claim_delivery("a" * 64, expected_revision=0, token="claim", expires_at=DEADLINE)
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_REGISTRY_READ_ONLY"):
        tx.finish_delivery(response(), expected_revision=1, token="claim")


def test_forward_delivery_ddl_matches_owned_metadata_and_freezes_history(monkeypatch):
    path = (
        Path(__file__).resolve().parents[2] / "alembic/versions/20261018_ap_0007_copy_delivery.py"
    )
    spec = importlib.util.spec_from_file_location("copy_delivery_migration", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def normalized(text):
        return re.sub(r"\s+", "", text)

    generated = (
        ";".join(
            str(CreateTable(t).compile(dialect=dialect())).strip()
            for t in (COPY_DELIVERY, COPY_DELIVERY_HISTORY)
        )
        + ";"
    )
    assert normalized(generated) == normalized(module.DDL)
    assert module.down_revision == "20261018_ap_0006"
    statements, dropped = [], []

    class Capture:
        def execute(self, statement):
            statements.append(statement)

        def drop_table(self, name, schema):
            dropped.append((schema, name))

    monkeypatch.setattr(module, "op", Capture())
    module.upgrade()
    assert sum("CREATE TRIGGER" in s for s in statements) == 2
    assert any("NEW.revision <> OLD.revision + 1" in s for s in statements)
    assert any("ai_policy.protect_history()" in s for s in statements)
    module.downgrade()
    assert dropped == [("ai_policy", "copy_delivery_history"), ("ai_policy", "copy_delivery")]
