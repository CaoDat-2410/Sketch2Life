"""ASSUMED verifier + transactional MEMORY and offline SQL shape, not provider/PG proof."""

import importlib.util
import re
from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy.dialects.postgresql import dialect
from sqlalchemy.schema import CreateTable

from sketch2life.application.ai_policy_copy_resolution import (
    ProviderCopyReconciliationService,
    foundation_copy,
    resolution_key,
    validate_resolution,
)
from sketch2life.domain.ai_jobs.provider_copy import report_label
from sketch2life.domain.ai_policy.model import PolicyError
from sketch2life.infrastructure.ai_policy.copy_registry_sql import (
    SqlProviderCopyRegistryTransaction,
)
from sketch2life.infrastructure.ai_policy.copy_registry_tables import (
    COPY_LIFECYCLE,
    COPY_RESOLUTION,
)
from tests.unit.test_ai_policy_copy_reconciliation import setup
from tests.unit.test_ai_policy_domain import NOW


def service_setup(operation="purge"):
    verifier, boundary, store, envelope = setup(operation)
    service = ProviderCopyReconciliationService(store, verifier, clock=lambda: NOW)
    return service, boundary, store, envelope


def reconcile(service, envelope, revision=0):
    return service.reconcile(
        "operator",
        "school",
        envelope.command,
        envelope.operation_key,
        expected_delivery_revision=2,
        expected_copy_revision=revision,
    )


def test_fixture_purge_persists_current_state_full_proof_and_exact_retry_without_duplicate():
    service, boundary, store, envelope = service_setup()
    result = reconcile(service, envelope)
    assert (
        result.revision == 1
        and report_label(foundation_copy(result)) == "fixture_deleted_not_actual"
    )
    scope = store.scopes["school", "scope"]
    assert len(scope["resolutions"]) == 1
    revision = scope["revision"]
    assert reconcile(service, envelope) == result
    assert scope["revision"] == revision and len(boundary.proofs) == 2
    proof = next(iter(scope["resolutions"].values()))
    assert (
        proof.binding.envelope.target.original_profile_ref
        == result.registration.original_profile_ref
    )
    boundary.changes = {"allowed": False}
    with pytest.raises(PolicyError, match="AI_POLICY_FORBIDDEN"):
        reconcile(service, envelope)


@pytest.mark.parametrize(
    "outcome,verified,status",
    [
        ("deleted", False, "pending"),
        ("pending", True, "pending"),
        ("unsupported", True, "unsupported"),
        ("exception", True, "exception"),
    ],
)
def test_nonterminal_and_unverified_results_are_not_persisted_as_deleted(outcome, verified, status):
    service, boundary, _, envelope = service_setup()
    boundary.proof_changes = dict(outcome=outcome, verified=verified)
    result = reconcile(service, envelope)
    assert result.status == status and not foundation_copy(result).actual_deletion_proven


@pytest.mark.parametrize(
    "kind,verified,confirmed", [("fixture", True, True), ("provider", False, False)]
)
def test_cancel_acknowledgment_persists_separately_from_deletion(kind, verified, confirmed):
    service, boundary, _, envelope = service_setup("cancel")
    boundary.proof_changes = dict(evidence_kind=kind, verified=verified)
    result = reconcile(service, envelope)
    assert result.cancel_confirmed is confirmed and result.status == "cancel_requested"
    assert not foundation_copy(result).actual_deletion_proven
    assert result.cancel_evidence_kind == (kind if confirmed else None)


def test_stale_copy_revision_has_no_mutation_or_proof_history():
    service, _, store, envelope = service_setup()
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_LIFECYCLE_STALE"):
        reconcile(service, envelope, revision=4)
    assert not store.scopes["school", "scope"].get("resolutions")


def test_receipt_history_failure_rolls_back_copy_and_proof_together():
    service, _, store, envelope = service_setup()
    save = store.save_resolution

    def fail(*args):
        save(*args)
        raise PolicyError("SYNTHETIC_RESOLUTION_HISTORY_FAILURE")

    store.save_resolution = fail
    with pytest.raises(PolicyError, match="SYNTHETIC_RESOLUTION_HISTORY_FAILURE"):
        reconcile(service, envelope)
    assert not store.scopes["school", "scope"].get("lifecycle")
    assert not store.scopes["school", "scope"].get("resolutions")


def test_precommit_revocation_rolls_back_resolution_not_prior_delivery():
    service, boundary, store, envelope = service_setup()
    save = store.save_resolution

    def revoke(*args):
        save(*args)
        boundary.changes = {"allowed": False}

    store.save_resolution = revoke
    with pytest.raises(PolicyError, match="AI_POLICY_FORBIDDEN"):
        reconcile(service, envelope)
    scope = store.scopes["school", "scope"]
    assert (
        not scope.get("lifecycle")
        and scope["deliveries"][envelope.operation_key].status.value == "receipt_available"
    )


def test_delivery_changed_during_proof_lookup_is_rejected_before_copy_mutation():
    from dataclasses import replace

    service, boundary, store, envelope = service_setup()

    def changed():
        scope = store.scopes["school", "scope"]
        old = scope["deliveries"][envelope.operation_key]
        scope["deliveries"][envelope.operation_key] = replace(old, revision=old.revision + 1)

    boundary.after_proof = changed
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_DELIVERY_STALE"):
        reconcile(service, envelope)
    assert not store.scopes["school", "scope"].get("resolutions")


def test_historical_resolution_validation_rejects_forged_result_or_proof():
    service, _, store, envelope = service_setup()
    result = reconcile(service, envelope)
    observation = next(iter(store.scopes["school", "scope"]["resolutions"].values()))
    from sketch2life.contracts.schemas.ai_policy_copy_lifecycle import CopyLifecycleRecord

    before = CopyLifecycleRecord(
        registration=result.registration, revision=0, status="purge_requested"
    )
    assert validate_resolution(before, result, observation) == observation
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_COPY_RESOLUTION"):
        validate_resolution(before, result.model_copy(update={"revision": 9}), observation)
    forged = observation.model_copy(
        update={"proof": observation.proof.model_copy(update={"verified": 1})}
    )
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_COPY_RESOLUTION"):
        validate_resolution(before, result, forged)
    assert resolution_key(observation) == resolution_key(
        observation.model_copy(update={"observed_at": NOW})
    )


def test_new_verified_observation_can_resolve_previously_unverified_pending_copy():
    service, boundary, store, envelope = service_setup()
    boundary.proof_changes = {"verified": False}
    pending = reconcile(service, envelope)
    boundary.proof_changes = {"verified": True}
    done = reconcile(service, envelope, revision=pending.revision)
    assert pending.status == "pending" and done.status == "deleted"
    assert done.revision == 2 and len(store.scopes["school", "scope"]["resolutions"]) == 2


def test_verified_provider_cancel_ack_never_downgrades_to_fixture_or_pending():
    service, boundary, _, envelope = service_setup("cancel")
    boundary.proof_changes = {"evidence_kind": "provider"}
    first = reconcile(service, envelope)
    boundary.proof_changes = {"outcome": "pending", "verified": False}
    second = reconcile(service, envelope, revision=first.revision)
    assert second.cancel_confirmed and second.cancel_evidence_kind == "provider"
    assert second.status != "deleted"  # Synthetic classification, not real provider evidence.


@pytest.mark.parametrize("existing", [False, True])
def test_sql_resolution_writes_copy_cas_proof_and_event_together(existing):
    service, boundary, store, envelope = service_setup()
    from sketch2life.contracts.schemas.ai_policy_copy_lifecycle import CopyLifecycleRecord

    before = CopyLifecycleRecord(registration=envelope.target, revision=0, status="purge_requested")
    if existing:
        boundary.proof_changes = {"verified": False}
        before = reconcile(service, envelope)
        boundary.proof_changes = {"verified": True}
    after = reconcile(service, envelope, revision=before.revision)
    scope = store.scopes["school", "scope"]
    observation = list(scope["resolutions"].values())[-1]
    statements, events = [], []

    class Result:
        rowcount = 1

    class Connection:
        def execute(self, statement):
            statements.append(statement)
            return Result()

    tx = SqlProviderCopyRegistryTransaction.__new__(SqlProviderCopyRegistryTransaction)
    tx.connection, tx.writable = Connection(), True
    tx.organization_id, tx.scope_ref, tx.principal_id = "school", "scope", "operator"
    tx.get_operation = lambda key: envelope
    tx.get_delivery = lambda key: scope["deliveries"][key]
    tx.get_copy_lifecycle = lambda copy_id: before
    tx._advance = lambda kind, detail: events.append(detail)
    tx.save_resolution(before, after, observation)
    assert [s.table.name for s in statements] == ["copy_lifecycle", "copy_resolution"]
    assert statements[0].is_update == existing and len(events) == 1
    tx.writable = False
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_REGISTRY_READ_ONLY"):
        tx.save_resolution(before, after, observation)


@pytest.mark.parametrize(
    "changes", [{"cancel_confirmed": True}, {"status": "deleted"}, {"revision": True}]
)
def test_lifecycle_snapshot_rejects_unproven_native_terminal_metadata(changes):
    from sketch2life.contracts.schemas.ai_policy_copy_lifecycle import CopyLifecycleRecord
    from tests.ai_policy_copy_inventory_fixtures import registration

    with pytest.raises(ValidationError):
        CopyLifecycleRecord.model_validate(
            dict(registration=registration(), revision=0, status="discovered") | changes
        )


def test_frozen_resolution_migration_matches_owned_metadata_and_guards_history(monkeypatch):
    path = (
        Path(__file__).resolve().parents[2] / "alembic/versions/20261018_ap_0009_copy_resolution.py"
    )
    spec = importlib.util.spec_from_file_location("copy_resolution_migration", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def normalized(value):
        return re.sub(r"\s+", "", value)

    generated = (
        ";".join(
            str(CreateTable(t).compile(dialect=dialect())).strip()
            for t in (COPY_LIFECYCLE, COPY_RESOLUTION)
        )
        + ";"
    )
    assert normalized(generated) == normalized(module.DDL)
    assert module.down_revision == "20261018_ap_0008"
    statements = []

    class Capture:
        def execute(self, statement):
            statements.append(statement)

        def drop_table(self, name, schema):
            statements.append((schema, name))

    monkeypatch.setattr(module, "op", Capture())
    module.upgrade()
    assert sum("CREATE TRIGGER" in s for s in statements) == 2
    assert any(
        "cancel_evidence_kind" in s and "IS DISTINCT FROM 'provider'" in s for s in statements
    )
    module.downgrade()
    assert statements[-3:-1] == [("ai_policy", "copy_resolution"), ("ai_policy", "copy_lifecycle")]
