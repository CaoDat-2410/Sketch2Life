"""Application boundary for Teacher invitation persistence and transactions."""

from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Literal, Protocol

from sketch2life.application.ports.identity import ProvisionedIdentity


class TeacherInvitationError(RuntimeError):
    """Base error for the Teacher invitation use case."""


class TeacherInvitationSetupUnavailable(TeacherInvitationError):
    """The account cannot be invited under the generic public contract."""


class TeacherInvitationNotFound(TeacherInvitationError):
    """The pending invitation is absent or outside the caller's organization."""


class TeacherInvitationIdempotencyMismatch(TeacherInvitationError):
    """An Idempotency-Key was reused for different request content."""


class TeacherInvitationWriteConflict(TeacherInvitationError):
    """A persistence uniqueness race occurred while writing an invitation receipt."""


class TeacherInvitationStoreUnavailable(TeacherInvitationError):
    """The invitation store could not complete the transaction."""


class TeacherInvitationIdentityUnavailable(TeacherInvitationError):
    """The identity provider is missing or could not complete provisioning."""


class TeacherInvitationKeyUnavailable(TeacherInvitationError):
    """The configured receipt fingerprint key is missing or too short."""


@dataclass(frozen=True, slots=True)
class TeacherInvitationResult:
    account_ref: str
    status: Literal["PENDING_VERIFICATION"] = "PENDING_VERIFICATION"


@dataclass(frozen=True, slots=True)
class TeacherInvitationReceipt:
    request_fingerprint: str
    result: TeacherInvitationResult


@dataclass(frozen=True, slots=True)
class TeacherInvitationIdentityState:
    subject: str
    account_ref: str
    issuer: str
    state: str
    account_role: str | None
    email_verification_required: bool


@dataclass(frozen=True, slots=True)
class TeacherInvitationAssignmentState:
    role: str
    class_id: str | None
    active: bool
    pending_activation: bool


class TeacherInvitationUnitOfWork(Protocol):
    """Database-neutral operations held inside one invitation transaction."""

    def lock_command(
        self, *, principal_ref: str, operation_scope: str, idempotency_key: str
    ) -> None: ...

    def lock_invitation_scope(
        self,
        *,
        organization_id: str,
        email_lock_fingerprint: str,
        organization_email_lock_fingerprint: str,
    ) -> None: ...

    def lock_identity(self, *, identity_lock_fingerprint: str) -> None: ...

    def lock_invitation_account(self, *, account_ref: str) -> None: ...

    def get_receipt(
        self, *, principal_ref: str, operation_scope: str, idempotency_key: str
    ) -> TeacherInvitationReceipt | None: ...

    def identity_by_subject(self, *, subject: str) -> TeacherInvitationIdentityState | None: ...

    def teacher_assignments(
        self, *, organization_id: str, subject: str
    ) -> tuple[TeacherInvitationAssignmentState, ...]: ...

    def create_pending_identity(
        self, *, provisioned_identity: ProvisionedIdentity, account_ref: str
    ) -> TeacherInvitationIdentityState: ...

    def create_pending_teacher_assignment(self, *, organization_id: str, subject: str) -> None: ...

    def pending_invitation_by_account(
        self, *, organization_id: str, account_ref: str
    ) -> TeacherInvitationIdentityState | None: ...

    def queue_password_setup(self, *, subject: str) -> None: ...

    def record_audit(
        self,
        *,
        organization_id: str,
        audit_actor_ref: str,
        action: str,
        account_ref: str,
    ) -> None: ...

    def add_receipt(
        self,
        *,
        principal_ref: str,
        operation_scope: str,
        idempotency_key: str,
        organization_id: str,
        request_fingerprint: str,
        result: TeacherInvitationResult,
    ) -> None: ...


class TeacherInvitationRepository(Protocol):
    def transaction(self) -> AbstractContextManager[TeacherInvitationUnitOfWork]: ...

    def find_receipt(
        self, *, principal_ref: str, operation_scope: str, idempotency_key: str
    ) -> TeacherInvitationReceipt | None: ...
