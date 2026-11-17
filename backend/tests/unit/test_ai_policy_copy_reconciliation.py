"""ASSUMED receipt verifier + MEMORY, not authenticated provider evidence or SQL proof."""

from dataclasses import FrozenInstanceError, replace
from datetime import timedelta

import pytest

from sketch2life.application.ai_policy_copy_reconciliation import (
    ProviderCopyOperationReceiptVerifier,
)
from sketch2life.contracts.schemas.ai_policy_copy_reconciliation import VerifiedOperationReceipt
from sketch2life.domain.ai_jobs.provider_copy import CopyStatus, report_label
from sketch2life.domain.ai_policy.model import PolicyError
from tests.ai_policy_copy_dispatch_fixtures import dispatch
from tests.ai_policy_copy_dispatch_fixtures import setup as dispatch_setup
from tests.ai_policy_copy_operation_fixtures import AssumedOperationBoundary
from tests.unit.test_ai_policy_domain import NOW


class AssumedReceiptBoundary(AssumedOperationBoundary):
    def __init__(self, inventory):
        super().__init__(inventory)
        self.proof_changes, self.proofs = {}, []
        self.fail_proof = False
        self.after_proof = None

    def verify_operation_receipt(self, binding, digest):
        assert self.inventory.held and not self.inventory.in_transaction
        self.proofs.append((binding, digest))
        if self.fail_proof:
            raise RuntimeError("synthetic-private-proof-url")
        proof = VerifiedOperationReceipt(
            binding_digest=digest,
            reference=binding.reference,
            outcome="deleted"
            if binding.envelope.command.operation == "purge"
            else "cancel_confirmed",
            verified=True,
            evidence_kind="fixture",
            expires_at=NOW + timedelta(minutes=10),
        )
        if self.after_proof:
            self.after_proof()
        return proof.model_copy(update=self.proof_changes)


def setup(operation="purge"):
    dispatcher, owner, hook, store, envelope = dispatch_setup(operation=operation)
    from sketch2life.contracts.schemas.ai_policy_copy import CopyReceiptReference

    hook.changes = dict(
        outcome="receipt_available",
        reference=CopyReceiptReference(ref="fixture-receipt", hash="c" * 64),
    )
    dispatch(dispatcher, envelope)
    boundary = AssumedReceiptBoundary(owner.inventory)
    verifier = ProviderCopyOperationReceiptVerifier(store, boundary, clock=lambda: NOW)
    return verifier, boundary, store, envelope


def verify(verifier, envelope, revision=2):
    return verifier.verify(
        "operator", "school", envelope.command, envelope.operation_key, expected_revision=revision
    )


def original(store, envelope):
    return store.scopes["school", "scope"]["rows"][envelope.target.copy_id].initial_copy()


def test_exact_operation_revision_profile_reference_and_owner_revision_are_bound():
    verifier, boundary, store, envelope = setup()
    with verify(verifier, envelope) as lease:
        assert lease.binding.envelope == envelope and lease.binding.delivery_revision == 2
        assert lease.binding.reference.hash == "c" * 64
        result = lease.apply_purge(original(store, envelope))
        assert result.status is CopyStatus.DELETED
        assert (
            not result.actual_deletion_proven
            and report_label(result) == "fixture_deleted_not_actual"
        )
        with pytest.raises(FrozenInstanceError):
            lease.proof = None
    assert len(boundary.proofs) == 1
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_RECEIPT_LEASE_CLOSED"):
        lease.apply_purge(original(store, envelope))


@pytest.mark.parametrize(
    "kind,verified,outcome,status",
    [
        ("fixture", True, "deleted", CopyStatus.DELETED),
        ("provider", True, "deleted", CopyStatus.DELETED),
        ("provider", False, "deleted", CopyStatus.PENDING),
        ("provider", True, "pending", CopyStatus.PENDING),
        ("fixture", True, "unsupported", CopyStatus.UNSUPPORTED),
        ("fixture", True, "exception", CopyStatus.EXCEPTION),
    ],
)
def test_foundation_purge_transitions_preserve_fixture_and_unverified_semantics(
    kind, verified, outcome, status
):
    verifier, boundary, store, envelope = setup()
    boundary.proof_changes = dict(evidence_kind=kind, verified=verified, outcome=outcome)
    with verify(verifier, envelope) as lease:
        result = lease.apply_purge(original(store, envelope))
        assert result.status is status
        # Synthetic provider-kind output tests classification, not actual deletion.
        assert result.actual_deletion_proven == (
            kind == "provider" and verified and outcome == "deleted"
        )


@pytest.mark.parametrize(
    "kind,verified,confirmed,actual",
    [
        ("fixture", True, True, False),
        ("provider", True, True, True),
        ("provider", False, False, False),
    ],
)
def test_cancel_confirmation_is_separate_and_fixture_never_actual(
    kind, verified, confirmed, actual
):
    verifier, boundary, store, envelope = setup("cancel")
    boundary.proof_changes = dict(evidence_kind=kind, verified=verified)
    with verify(verifier, envelope) as lease:
        assert lease.cancellation_confirmed() is confirmed
        assert lease.cancellation_confirmed(actual_only=True) is actual
        with pytest.raises(PolicyError, match="AI_POLICY_COPY_SCOPE_MISMATCH"):
            lease.apply_purge(original(store, envelope))
    assert original(store, envelope).status is CopyStatus.DISCOVERED


@pytest.mark.parametrize(
    "operation,outcome", [("purge", "cancel_confirmed"), ("cancel", "deleted")]
)
def test_wrong_operation_outcome_cannot_be_used_as_acknowledgment(operation, outcome):
    verifier, boundary, _, envelope = setup(operation)
    boundary.proof_changes = {"outcome": outcome}
    with (
        pytest.raises(PolicyError, match="AI_POLICY_COPY_RECEIPT_OPERATION_MISMATCH"),
        verify(verifier, envelope),
    ):
        pass


@pytest.mark.parametrize(
    "change,code",
    [
        ({"binding_digest": "f" * 64}, "AI_POLICY_COPY_RECEIPT_MISMATCH"),
        ({"verified": 1}, "AI_POLICY_COPY_RECEIPT_MISMATCH"),
        ({"expires_at": NOW}, "AI_POLICY_COPY_RECEIPT_EXPIRED"),
        ({"evidence_kind": "claimed_provider"}, "AI_POLICY_COPY_RECEIPT_MISMATCH"),
    ],
)
def test_forged_native_malformed_or_expired_proof_fails_closed(change, code):
    verifier, boundary, _, envelope = setup()
    boundary.proof_changes = change
    with pytest.raises(PolicyError, match=code), verify(verifier, envelope):
        pass


def test_current_read_authority_denial_before_inventory_and_proof_lookup():
    verifier, boundary, store, envelope = setup()
    before = store.commits
    boundary.changes = {"allowed": False}
    with pytest.raises(PolicyError, match="AI_POLICY_FORBIDDEN"), verify(verifier, envelope):
        pass
    assert store.commits == before and not boundary.proofs


def test_revoked_rights_after_verification_do_not_yield_a_valid_lease():
    verifier, boundary, _, envelope = setup()
    boundary.after_proof = lambda: setattr(boundary, "changes", {"allowed": False})
    with pytest.raises(PolicyError, match="AI_POLICY_FORBIDDEN"), verify(verifier, envelope):
        pass


def test_receipt_deadline_is_rechecked_during_lease_and_lease_closes_on_failure():
    verifier, _, _, envelope = setup()
    with (
        pytest.raises(PolicyError, match="AI_POLICY_COPY_RECEIPT_EXPIRED"),
        verify(verifier, envelope) as lease,
    ):
        verifier.clock = lambda: NOW + timedelta(minutes=11)
        lease.confirm()
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_RECEIPT_LEASE_CLOSED"):
        lease.confirm()


@pytest.mark.parametrize("revision", [True, 0, 1, 3])
def test_bad_or_stale_delivery_revision_cannot_be_verified(revision):
    verifier, boundary, _, envelope = setup()
    with pytest.raises(PolicyError), verify(verifier, envelope, revision):
        pass
    assert not boundary.proofs


def test_original_profile_cannot_be_resolved_to_latest_version():
    verifier, boundary, _, envelope = setup()
    boundary.profile = boundary.profile.model_copy(update={"version": 2})
    with (
        pytest.raises(PolicyError, match="AI_POLICY_COPY_PROFILE_MISMATCH"),
        verify(verifier, envelope),
    ):
        pass


def test_purge_cannot_apply_to_another_copy_or_be_used_as_cancel_confirmation():
    verifier, _, store, envelope = setup()
    with verify(verifier, envelope) as lease:
        with pytest.raises(PolicyError, match="AI_POLICY_COPY_SCOPE_MISMATCH"):
            lease.apply_purge(replace(original(store, envelope), copy_id="other"))
        with pytest.raises(PolicyError, match="AI_POLICY_COPY_RECEIPT_OPERATION_MISMATCH"):
            lease.cancellation_confirmed()


def test_private_verifier_error_is_sanitized():
    verifier, boundary, _, envelope = setup()
    boundary.fail_proof = True
    with (
        pytest.raises(PolicyError, match="^AI_POLICY_COPY_DEPENDENCY_UNAVAILABLE$"),
        verify(verifier, envelope),
    ):
        pass


def test_wrong_reference_hash_cannot_replace_recorded_delivery_reference():
    verifier, boundary, _, envelope = setup()
    from sketch2life.contracts.schemas.ai_policy_copy import CopyReceiptReference

    boundary.proof_changes = {
        "reference": CopyReceiptReference(ref="fixture-receipt", hash="f" * 64)
    }
    with (
        pytest.raises(PolicyError, match="AI_POLICY_COPY_RECEIPT_MISMATCH"),
        verify(verifier, envelope),
    ):
        pass


def test_non_receipt_delivery_state_is_not_authoritative_receipt_availability():
    from sketch2life.domain.ai_policy.copy_delivery import (
        DeliveryResponse,
        DeliveryStatus,
        HookOutcome,
    )

    verifier, boundary, store, envelope = setup()
    deliveries = store.scopes["school", "scope"]["deliveries"]
    deliveries[envelope.operation_key] = replace(
        deliveries[envelope.operation_key],
        status=DeliveryStatus.PENDING,
        last_response=DeliveryResponse(
            envelope.operation_key,
            envelope.binding_digest,
            HookOutcome.PENDING,
            reason_code="WAITING",
        ),
    )
    with (
        pytest.raises(PolicyError, match="AI_POLICY_COPY_RECEIPT_NOT_AVAILABLE"),
        verify(verifier, envelope),
    ):
        pass
    assert not boundary.proofs


def test_current_rights_are_rechecked_before_lease_use_and_exit():
    verifier, boundary, _, envelope = setup()
    with (
        pytest.raises(PolicyError, match="AI_POLICY_FORBIDDEN"),
        verify(verifier, envelope) as lease,
    ):
        boundary.changes = {"allowed": False}
        lease.confirm()
