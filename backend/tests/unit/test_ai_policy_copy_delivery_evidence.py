"""ASSUMED current authority + MEMORY/offline evidence proof, no actual provider/PG."""

import importlib.util
import re
from datetime import timedelta
from pathlib import Path

import pytest
from sqlalchemy.dialects.postgresql import dialect
from sqlalchemy.schema import CreateTable

from sketch2life.application.ai_policy_copy_delivery_evidence import validate_delivery_evidence
from sketch2life.domain.ai_policy.copy_delivery import DeliveryState, DeliveryStatus
from sketch2life.domain.ai_policy.model import PolicyError
from sketch2life.infrastructure.ai_policy.copy_registry_sql import (
    SqlProviderCopyRegistryTransaction,
)
from sketch2life.infrastructure.ai_policy.copy_registry_tables import COPY_DELIVERY_AUTHORITY
from tests.ai_policy_copy_dispatch_fixtures import dispatch, setup


def observations():
    dispatcher, _, _, store, envelope = setup()
    dispatch(dispatcher, envelope)
    state = store.scopes["school", "scope"]
    return envelope, state["delivery_authority"], state["delivery_history"]


def source_states(envelope, proof, history):
    before = (
        DeliveryState(envelope.operation_key, envelope.binding_digest)
        if proof.state_revision == 0
        else history[envelope.operation_key, proof.state_revision]
    )
    after_revision = proof.state_revision + (proof.phase != "dispatch")
    return before, history[envelope.operation_key, after_revision]


def test_all_three_phase_proofs_reconstruct_after_restart_from_immutable_snapshots():
    envelope, proofs, history = observations()
    assert [p.phase for p in proofs] == ["claim", "dispatch", "completion"]
    for proof in proofs:
        before, after = source_states(envelope, proof, history)
        assert validate_delivery_evidence(proof, envelope, before, after) == proof
        assert proof.authority.grant.allowed is True
    assert proofs[0].authority.grant.command_digest != proofs[1].authority.grant.command_digest


@pytest.mark.parametrize(
    "change",
    [
        {"principal_id": "other"},
        {"organization_id": "other"},
        {"scope_ref": "other"},
        {"operation_key": "f" * 64},
        {"state_revision": True},
        {"state_revision": 9},
        {"phase": "dispatch"},
    ],
)
def test_wrong_actor_scope_key_revision_phase_proof_is_rejected(change):
    envelope, proofs, history = observations()
    before, after = source_states(envelope, proofs[0], history)
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_DELIVERY_AUTHORITY_EVIDENCE"):
        validate_delivery_evidence(proofs[0].model_copy(update=change), envelope, before, after)


@pytest.mark.parametrize(
    "grant_change",
    [
        {"allowed": False},
        {"allowed": 1},
        {"command_digest": "f" * 64},
        {"principal_id": "other"},
    ],
)
def test_native_wrong_or_forged_historical_grant_is_revalidated(grant_change):
    envelope, proofs, history = observations()
    proof = proofs[0]
    before, after = source_states(envelope, proof, history)
    forged = proof.model_copy(
        update={
            "authority": proof.authority.model_copy(
                update={"grant": proof.authority.grant.model_copy(update=grant_change)}
            )
        }
    )
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_DELIVERY_AUTHORITY_EVIDENCE"):
        validate_delivery_evidence(forged, envelope, before, after)


def test_expired_and_future_claim_observations_and_wrong_after_state_fail_closed():
    envelope, proofs, history = observations()
    proof = proofs[0]
    before, after = source_states(envelope, proof, history)
    for observed in (proof.authority.claim_deadline, proof.observed_at - timedelta(seconds=1)):
        with pytest.raises(PolicyError, match="AI_POLICY_INVALID_DELIVERY_AUTHORITY_EVIDENCE"):
            validate_delivery_evidence(
                proof.model_copy(update={"observed_at": observed}), envelope, before, after
            )
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_DELIVERY_AUTHORITY_EVIDENCE"):
        validate_delivery_evidence(proof, envelope, before, before)


@pytest.mark.parametrize("phase", ["claim", "dispatch", "completion"])
def test_evidence_insert_failure_rolls_back_its_phase_not_prior_external_effect(phase):
    dispatcher, _, hook, store, envelope = setup()
    original = store.record_delivery_authority

    def fail(proof):
        original(proof)
        if proof.phase == phase:
            raise PolicyError("SYNTHETIC_PHASE_EVIDENCE_FAILURE")

    store.record_delivery_authority = fail
    with pytest.raises(PolicyError, match="SYNTHETIC_PHASE_EVIDENCE_FAILURE"):
        dispatch(dispatcher, envelope)
    state = store.scopes["school", "scope"]
    assert [p.phase for p in state.get("delivery_authority", [])] == {
        "claim": [],
        "dispatch": ["claim"],
        "completion": ["claim", "dispatch"],
    }[phase]
    if phase == "claim":
        assert not state.get("deliveries") and not hook.calls
    else:
        assert state["deliveries"][envelope.operation_key].status is DeliveryStatus.IN_FLIGHT
        assert len(hook.calls) == (phase == "completion")


def test_successful_hook_sees_committed_claim_and_dispatch_authority_only():
    dispatcher, _, hook, store, envelope = setup()
    observed = []
    hook.on_call = lambda env: observed.append(
        [p.phase for p in store.scopes["school", "scope"]["delivery_authority"]]
    )
    dispatch(dispatcher, envelope)
    assert observed == [["claim", "dispatch"]]


def test_sql_append_binds_original_operation_and_transaction_scope():
    envelope, proofs, history = observations()
    proof = proofs[0]
    _, after = source_states(envelope, proof, history)
    writes, events = [], []

    class Connection:
        def execute(self, statement):
            writes.append(statement.compile(dialect=dialect()).params)

    tx = SqlProviderCopyRegistryTransaction.__new__(SqlProviderCopyRegistryTransaction)
    tx.connection, tx.writable = Connection(), True
    tx.organization_id, tx.scope_ref, tx.principal_id = "school", "scope", "operator"
    tx.get_operation = lambda key: envelope
    tx.get_delivery = lambda key: after
    tx._advance = lambda kind, payload: events.append((kind, payload))
    tx.record_delivery_authority(proof)
    assert len(writes) == len(events) == 1
    assert writes[0]["evidence"] == proof.model_dump(mode="json")
    assert writes[0]["operation_key"] == envelope.operation_key
    tx.principal_id = "other"
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_SCOPE_MISMATCH"):
        tx.record_delivery_authority(proof)
    tx.writable = False
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_REGISTRY_READ_ONLY"):
        tx.record_delivery_authority(proof)
    assert len(writes) == 1


def test_forward_migration_matches_metadata_and_rejects_history_update_delete(monkeypatch):
    path = (
        Path(__file__).resolve().parents[2]
        / "alembic/versions/20261018_ap_0008_delivery_authority.py"
    )
    spec = importlib.util.spec_from_file_location("delivery_authority_migration", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def normalized(value):
        return re.sub(r"\s+", "", value)

    assert normalized(
        str(CreateTable(COPY_DELIVERY_AUTHORITY).compile(dialect=dialect())) + ";"
    ) == normalized(module.DDL)
    assert module.down_revision == "20261018_ap_0007"
    statements = []

    class Capture:
        def execute(self, statement):
            statements.append(statement)

        def drop_table(self, name, schema):
            statements.append((schema, name))

    monkeypatch.setattr(module, "op", Capture())
    module.upgrade()
    assert "BEFORE UPDATE OR DELETE" in statements[1]
    assert "ai_policy.protect_history()" in statements[1]
    module.downgrade()
    assert statements[-1] == ("ai_policy", "copy_delivery_authority")
