"""Additional unit tests for Teacher invitation gaps identified in cold review R1."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

import pytest

from sketch2life.application.ports.identity import (
    IdentityAccountConflict,
    ProvisionedIdentity,
)
from sketch2life.application.ports.teacher_invitations import (
    TeacherInvitationAssignmentState,
    TeacherInvitationIdempotencyMismatch,
    TeacherInvitationIdentityState,
    TeacherInvitationReceipt,
    TeacherInvitationResult,
    TeacherInvitationSetupUnavailable,
    TeacherInvitationWriteConflict,
)
from sketch2life.application.services.teacher_invitations import (
    TeacherInvitationService,
    _mac,
)
from tests.unit.test_teacher_invitations import (
    ACTOR,
    EMAIL,
    ISSUER,
    KEY,
    ORG,
    SUBJECT,
    FakeProvisioner,
    FakeRepository,
    FakeUnitOfWork,
)


@dataclass
class _RaceConflictRepository(FakeRepository):
    conflict_on_commit: bool = False
    raced_receipt: TeacherInvitationReceipt | None = None
    _find_calls: int = field(default=0, init=False)

    def find_receipt(
        self, *, principal_ref: str, operation_scope: str, idempotency_key: str
    ) -> TeacherInvitationReceipt | None:
        self._find_calls += 1
        if self._find_calls >= 2 and self.raced_receipt is not None:
            return self.raced_receipt
        return super().find_receipt(
            principal_ref=principal_ref,
            operation_scope=operation_scope,
            idempotency_key=idempotency_key,
        )

    def transaction(self) -> Any:
        from contextlib import contextmanager

        @contextmanager
        def _tx():
            snapshot = deepcopy(
                (
                    self.identities,
                    self.assignments,
                    self.receipts,
                    self.outbox_subjects,
                    self.audit_rows,
                )
            )
            try:
                yield FakeUnitOfWork(self)
                if self.conflict_on_commit:
                    raise TeacherInvitationWriteConflict()
            except Exception:
                (
                    self.identities,
                    self.assignments,
                    self.receipts,
                    self.outbox_subjects,
                    self.audit_rows,
                ) = snapshot
                raise

        return _tx()


def test_existing_identity_with_mismatched_issuer_is_refused_generically() -> None:
    """covers: IMPL_REVIEW_D_T-6A_R1_20261125.md P3-5"""
    provider = FakeProvisioner(
        identities={EMAIL.casefold(): ProvisionedIdentity(SUBJECT, "other-issuer")}
    )
    repository = FakeRepository(
        identities={
            SUBJECT: TeacherInvitationIdentityState(
                subject=SUBJECT,
                account_ref="account-ref-1",
                issuer=ISSUER,
                state="pending_verification",
                account_role="teacher",
                email_verification_required=True,
            )
        }
    )
    service = TeacherInvitationService(
        repository=repository,
        identity_provisioner=provider,
        receipt_hmac_key=KEY,
    )

    with pytest.raises(TeacherInvitationSetupUnavailable):
        service.invite_teacher(
            principal_subject=ACTOR,
            principal_issuer=ISSUER,
            organization_id=ORG,
            email=EMAIL,
            idempotency_key="issuer-mismatch-key",
        )

    assert repository.outbox_subjects == []
    assert repository.audit_rows == []
    assert repository.receipts == {}


def test_write_conflict_without_raced_receipt_compensates_and_raises_setup_unavailable() -> None:
    """covers: IMPL_REVIEW_D_T-6A_R1_20261125.md P2-2"""
    provider = FakeProvisioner()
    repository = _RaceConflictRepository(conflict_on_commit=True, raced_receipt=None)
    service = TeacherInvitationService(
        repository=repository,
        identity_provisioner=provider,
        receipt_hmac_key=KEY,
    )

    with pytest.raises(TeacherInvitationSetupUnavailable):
        service.invite_teacher(
            principal_subject=ACTOR,
            principal_issuer=ISSUER,
            organization_id=ORG,
            email=EMAIL,
            idempotency_key="write-conflict-no-receipt",
        )

    assert provider.deletions == [SUBJECT]


def test_write_conflict_with_raced_receipt_replays_matching_result() -> None:
    """covers: IMPL_REVIEW_D_T-6A_R1_20261125.md P2-2"""
    provider = FakeProvisioner()
    request_fingerprint = _mac(
        KEY,
        "be1.teacher-invitation.request.v1",
        {
            "operation": "POST /api/be1/v1/organizations/{organization_id}/teacher-invitations",
            "principal": {"issuer": ISSUER, "subject": ACTOR},
            "organization_id": ORG,
            "email": EMAIL.strip().casefold(),
        },
    )
    raced_receipt = TeacherInvitationReceipt(
        request_fingerprint=request_fingerprint,
        result=TeacherInvitationResult(account_ref="raced-account-ref"),
    )
    repository = _RaceConflictRepository(conflict_on_commit=True, raced_receipt=raced_receipt)
    service = TeacherInvitationService(
        repository=repository,
        identity_provisioner=provider,
        receipt_hmac_key=KEY,
    )

    result = service.invite_teacher(
        principal_subject=ACTOR,
        principal_issuer=ISSUER,
        organization_id=ORG,
        email=EMAIL,
        idempotency_key="write-conflict-raced-receipt",
    )

    assert result == TeacherInvitationResult(account_ref="raced-account-ref")


def test_provider_create_race_falls_back_to_existing_identity_without_deleting() -> None:
    """covers: IMPL_REVIEW_D_T-6A_R1_20261125.md P2-2"""

    class RacedCreateProvisioner(FakeProvisioner):
        def create_account(
            self, *, email: str, display_name: str | None = None
        ) -> ProvisionedIdentity:
            self.creations.append(email)
            self.identities[email] = ProvisionedIdentity(SUBJECT, ISSUER)
            raise IdentityAccountConflict()

    provider = RacedCreateProvisioner()
    repository = FakeRepository(
        identities={
            SUBJECT: TeacherInvitationIdentityState(
                subject=SUBJECT,
                account_ref="account-ref-raced",
                issuer=ISSUER,
                state="pending_verification",
                account_role="teacher",
                email_verification_required=True,
            )
        },
        assignments={
            (ORG, SUBJECT): (
                TeacherInvitationAssignmentState(
                    role="teacher",
                    class_id=None,
                    active=False,
                    pending_activation=True,
                ),
            )
        },
    )
    service = TeacherInvitationService(
        repository=repository,
        identity_provisioner=provider,
        receipt_hmac_key=KEY,
    )

    result = service.invite_teacher(
        principal_subject=ACTOR,
        principal_issuer=ISSUER,
        organization_id=ORG,
        email=EMAIL,
        idempotency_key="provider-race-key",
    )

    assert result.account_ref == "account-ref-raced"
    assert provider.deletions == []
    assert repository.outbox_subjects == [SUBJECT]


def test_resend_with_mismatched_receipt_fingerprint_raises_idempotency_mismatch() -> None:
    """covers: IMPL_REVIEW_D_T-6A_R1_20261125.md Checked-Idempotency"""
    principal_ref = _mac(
        KEY,
        "be1.teacher-invitation.principal.v1",
        {"issuer": ISSUER, "subject": ACTOR},
    )
    operation_scope = (
        f"POST /api/be1/v1/organizations/{ORG}/teacher-invitations/account-ref-1/resend"
    )
    repository = FakeRepository(
        receipts={
            (principal_ref, operation_scope, "resend-key"): TeacherInvitationReceipt(
                request_fingerprint="0" * 64,
                result=TeacherInvitationResult(account_ref="account-ref-1"),
            )
        }
    )
    service = TeacherInvitationService(
        repository=repository,
        identity_provisioner=FakeProvisioner(),
        receipt_hmac_key=KEY,
    )

    with pytest.raises(TeacherInvitationIdempotencyMismatch):
        service.resend_teacher_invitation(
            principal_subject=ACTOR,
            principal_issuer=ISSUER,
            organization_id=ORG,
            account_ref="account-ref-1",
            idempotency_key="resend-key",
        )


@pytest.mark.parametrize(
    "assignments",
    [
        (
            TeacherInvitationAssignmentState(
                role="teacher",
                class_id="class-1",
                active=False,
                pending_activation=True,
            ),
        ),
        (
            TeacherInvitationAssignmentState(
                role="teacher",
                class_id=None,
                active=True,
                pending_activation=False,
            ),
        ),
        (
            TeacherInvitationAssignmentState(
                role="teacher",
                class_id=None,
                active=False,
                pending_activation=False,
            ),
        ),
        (
            TeacherInvitationAssignmentState(
                role="teacher",
                class_id=None,
                active=False,
                pending_activation=True,
            ),
            TeacherInvitationAssignmentState(
                role="teacher",
                class_id="class-1",
                active=True,
                pending_activation=False,
            ),
        ),
    ],
)
def test_pending_teacher_with_non_pending_org_assignment_shape_refused(
    assignments: tuple[TeacherInvitationAssignmentState, ...],
) -> None:
    """covers: IMPL_REVIEW_D_T-6A_R1_20261125.md Checked-409"""
    provider = FakeProvisioner(identities={EMAIL.casefold(): ProvisionedIdentity(SUBJECT, ISSUER)})
    repository = FakeRepository(
        identities={
            SUBJECT: TeacherInvitationIdentityState(
                subject=SUBJECT,
                account_ref="account-ref-1",
                issuer=ISSUER,
                state="pending_verification",
                account_role="teacher",
                email_verification_required=True,
            )
        },
        assignments={(ORG, SUBJECT): assignments},
    )
    service = TeacherInvitationService(
        repository=repository,
        identity_provisioner=provider,
        receipt_hmac_key=KEY,
    )

    with pytest.raises(TeacherInvitationSetupUnavailable):
        service.invite_teacher(
            principal_subject=ACTOR,
            principal_issuer=ISSUER,
            organization_id=ORG,
            email=EMAIL,
            idempotency_key="invalid-assignment-shape",
        )
