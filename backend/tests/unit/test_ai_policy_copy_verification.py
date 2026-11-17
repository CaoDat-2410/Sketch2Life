"""ASSUMED verifier/current guard; reuse foundation state transitions, not deletion proof."""

from contextlib import contextmanager
from dataclasses import replace
from datetime import timedelta

import pytest
from pydantic import ValidationError

from sketch2life.application.ai_policy_copy_verification import ProviderCopyReceiptVerifier
from sketch2life.contracts.schemas.ai_policy import PolicyDefinitionRef
from sketch2life.contracts.schemas.ai_policy_copy import (
    CopyAuthorityGrant,
    CopyReceiptReference,
    ProviderCopyCommand,
    VerifiedCopyReceipt,
)
from sketch2life.domain.ai_jobs.provider_copy import (
    CopyKind,
    CopyStatus,
    ProviderCopy,
    apply_receipt,
    report_label,
    request_purge,
)
from sketch2life.domain.ai_policy.model import PolicyError
from tests.unit.test_ai_policy_domain import NOW

REF = PolicyDefinitionRef(ref="fixture-profile", version=1, hash="a" * 64)
RECEIPT = CopyReceiptReference(ref="fixture-receipt", hash="b" * 64)


def command(**changes):
    return ProviderCopyCommand.model_validate(
        dict(
            client_request_id="purge-key",
            data_request_ref=REF,
            scope_ref="scope",
            operation="purge",
        )
        | changes
    )


def copy(**changes):
    return replace(
        ProviderCopy("copy", "school", "scope", CopyKind.OUTPUT, "fixture-profile"), **changes
    )


class AssumedCopyVerifier:
    """Synthetic backend authorization/receipt verifier, not a real BE1/provider adapter."""

    def __init__(self):
        self.held, self.calls = False, 0
        self.grant_changes, self.second_changes, self.proof_changes = {}, {}, {}
        self.profile = REF
        self.bindings = []
        self.fail = False

    @contextmanager
    def guard(self, principal_id, organization_id):
        self.held = True
        try:
            yield self
        finally:
            self.held = False

    def authorize(self, request, digest):
        assert self.held
        self.calls += 1
        changes = self.grant_changes | (self.second_changes if self.calls % 2 == 0 else {})
        return CopyAuthorityGrant(
            organization_id="school",
            principal_id="operator",
            command_digest=digest,
            authority_revision="fixture-owner-revision",
            expires_at=NOW + timedelta(hours=1),
            allowed=True,
        ).model_copy(update=changes)

    def resolve_profile(self, target):
        assert self.held
        return self.profile

    def verify_receipt(self, binding, reference, digest):
        assert self.held
        self.bindings.append((binding, reference, digest))
        if self.fail:
            raise RuntimeError("synthetic-private-provider-token")
        return VerifiedCopyReceipt(
            binding_digest=digest,
            reference=reference,
            outcome="deleted",
            verified=True,
            evidence_kind="fixture",
            expires_at=NOW + timedelta(minutes=30),
        ).model_copy(update=self.proof_changes)


def setup():
    boundary = AssumedCopyVerifier()
    return ProviderCopyReceiptVerifier(boundary, clock=lambda: NOW), boundary


@contextmanager
def verify(
    service,
    *,
    request=None,
    target=None,
    reference=RECEIPT,
    principal="operator",
    organization="school",
):
    with service.purge_receipt(
        principal,
        organization,
        command() if request is None else request,
        copy() if target is None else target,
        reference,
    ) as receipt:
        yield receipt


def test_exact_fixture_receipt_reuses_existing_lifecycle_without_actual_deletion_claim():
    service, boundary = setup()
    with verify(service) as receipt:
        assert boundary.held and boundary.calls == 2
        current = apply_receipt(request_purge(copy()), receipt)
        assert current.status == CopyStatus.DELETED and not current.actual_deletion_proven
        assert report_label(current) == "fixture_deleted_not_actual"
    assert not boundary.held


def test_provider_kind_from_assumed_verifier_is_label_only_not_real_runtime_proof():
    service, boundary = setup()
    boundary.proof_changes = {"evidence_kind": "provider"}
    with verify(service) as receipt:
        current = apply_receipt(request_purge(copy()), receipt)
        assert current.actual_deletion_proven
    # This branch tests expected mapping only. No provider connected or deletion occurred.


@pytest.mark.parametrize("outcome", ["deleted", "pending", "unsupported", "exception"])
def test_unverified_or_non_deleted_outcomes_never_prove_actual_deletion(outcome):
    service, boundary = setup()
    boundary.proof_changes = {"outcome": outcome, "verified": False, "evidence_kind": "provider"}
    with verify(service) as receipt:
        current = apply_receipt(request_purge(copy()), receipt)
    assert not current.actual_deletion_proven
    assert current.status == (CopyStatus.PENDING if outcome == "deleted" else CopyStatus(outcome))
    assert report_label(current) != "deleted"


@pytest.mark.parametrize(
    "changes",
    [
        {"organization_id": "other"},
        {"scope_ref": "other"},
    ],
)
def test_cross_scope_target_denied_before_backend_verification(changes):
    service, boundary = setup()
    with (
        pytest.raises(PolicyError, match="AI_POLICY_COPY_SCOPE_MISMATCH"),
        verify(
            service,
            target=copy(**changes),
        ),
    ):
        pass
    assert not boundary.bindings and boundary.calls == 0


@pytest.mark.parametrize(
    "changes",
    [
        {"principal_id": "other"},
        {"organization_id": "other"},
        {"command_digest": "c" * 64},
        {"allowed": 1},
        {"authority_revision": 1},
    ],
)
def test_wrong_or_native_malformed_authority_grant_denied(changes):
    service, boundary = setup()
    boundary.grant_changes = changes
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_AUTHORITY_MISMATCH"), verify(service):
        pass
    assert not boundary.bindings


@pytest.mark.parametrize(
    "changes,code",
    [
        ({"allowed": False}, "AI_POLICY_FORBIDDEN"),
        ({"expires_at": NOW}, "AI_POLICY_COPY_AUTHORITY_EXPIRED"),
    ],
)
def test_current_authority_denied_or_expired(changes, code):
    service, boundary = setup()
    boundary.grant_changes = changes
    with pytest.raises(PolicyError, match=code), verify(service):
        pass
    assert not boundary.bindings


@pytest.mark.parametrize(
    "changes,code",
    [
        ({"allowed": False}, "AI_POLICY_FORBIDDEN"),
        ({"expires_at": NOW}, "AI_POLICY_COPY_AUTHORITY_EXPIRED"),
        ({"authority_revision": "changed"}, "AI_POLICY_COPY_AUTHORITY_MISMATCH"),
    ],
)
def test_revoked_expired_or_changed_authority_during_verification_cannot_yield_receipt(
    changes, code
):
    service, boundary = setup()
    boundary.second_changes = changes
    with pytest.raises(PolicyError, match=code), verify(service):
        pass
    assert len(boundary.bindings) == 1 and not boundary.held


@pytest.mark.parametrize("changes", [{"ref": "other"}, {"version": True}, {"hash": "invalid"}])
def test_wrong_or_malformed_adopted_profile_denied(changes):
    service, boundary = setup()
    boundary.profile = REF.model_copy(update=changes)
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_PROFILE_MISMATCH"), verify(service):
        pass
    assert not boundary.bindings


@pytest.mark.parametrize(
    "changes",
    [
        {"binding_digest": "c" * 64},
        {"verified": 1},
        {"evidence_kind": "unknown"},
        {"outcome": "cancelled"},
        {"reason_code": "https://private.example/secret"},
        {"reference": RECEIPT.model_copy(update={"hash": "c" * 64})},
        {"reference": RECEIPT.model_copy(update={"ref": "different"})},
    ],
)
def test_wrong_or_untyped_verified_receipt_cannot_cross_boundary(changes):
    service, boundary = setup()
    boundary.proof_changes = changes
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_RECEIPT_MISMATCH"), verify(service):
        pass
    assert not boundary.held


def test_expired_verified_receipt_cannot_yield_deletion():
    service, boundary = setup()
    boundary.proof_changes = {"expires_at": NOW}
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_RECEIPT_EXPIRED"), verify(service):
        pass


@pytest.mark.parametrize(
    "changes",
    [
        {"client_request_id": "other"},
        {"scope_ref": "other"},
        {"data_request_ref": REF.model_copy(update={"version": 2})},
    ],
)
def test_operation_scope_and_exact_data_request_are_part_of_verifier_binding(changes):
    service, boundary = setup()
    with verify(service):
        original = boundary.bindings[-1][2]
    target = copy(scope_ref=changes.get("scope_ref", "scope"))
    with verify(service, request=command(**changes), target=target):
        assert boundary.bindings[-1][2] != original


@pytest.mark.parametrize("changes", [{"copy_id": "other"}, {"kind": CopyKind.CACHE}])
def test_exact_target_identity_and_kind_are_part_of_binding(changes):
    service, boundary = setup()
    with verify(service):
        original = boundary.bindings[-1][2]
    with verify(service, target=copy(**changes)):
        assert boundary.bindings[-1][2] != original


@pytest.mark.parametrize("extra", ["verified", "allowed", "provider_url", "receipt"])
def test_client_command_cannot_supply_authority_or_receipt_assertions(extra):
    with pytest.raises(ValidationError):
        ProviderCopyCommand.model_validate(command().model_dump(mode="python") | {extra: True})


def test_cancel_is_not_a_purge_receipt_and_missing_cancel_ack_remains_open():
    service, boundary = setup()
    with (
        pytest.raises(PolicyError, match="AI_POLICY_INVALID_COPY_REQUEST"),
        verify(
            service,
            request=command(operation="cancel"),
        ),
    ):
        pass
    assert not boundary.bindings


def test_private_dependency_error_does_not_leak():
    service, boundary = setup()
    boundary.fail = True
    with (
        pytest.raises(PolicyError, match="^AI_POLICY_COPY_DEPENDENCY_UNAVAILABLE$"),
        verify(service),
    ):
        pass


def test_caller_failure_propagates_safely_and_releases_current_guard():
    service, boundary = setup()
    with (
        pytest.raises(PolicyError, match="^AI_POLICY_COPY_DEPENDENCY_UNAVAILABLE$"),
        verify(service),
    ):
        assert boundary.held
        raise RuntimeError("synthetic-private-caller-token")
    assert not boundary.held


def test_receipt_replay_still_checks_current_owner_before_verification():
    service, boundary = setup()
    with verify(service):
        pass
    boundary.grant_changes = {"allowed": False}
    with pytest.raises(PolicyError, match="AI_POLICY_FORBIDDEN"), verify(service):
        pass
    assert len(boundary.bindings) == 1


def test_clock_advancing_past_authority_deadline_during_verification_denies_yield():
    service, boundary = setup()
    ticks = iter((NOW, NOW + timedelta(hours=2)))
    service.clock = lambda: next(ticks)
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_AUTHORITY_EXPIRED"), verify(service):
        pass
    assert len(boundary.bindings) == 1


def test_exact_profile_version_and_hash_are_included_in_binding():
    service, boundary = setup()
    with verify(service):
        original = boundary.bindings[-1][2]
    # Fixture simulates another original profile reference; no real registry
    # provenance or profile-adoption proof follows from this digest test.
    boundary.profile = REF.model_copy(update={"version": 2, "hash": "d" * 64})
    with verify(service):
        assert boundary.bindings[-1][2] != original
