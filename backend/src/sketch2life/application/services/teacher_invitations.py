"""Application service for School Manager Teacher invitations and resends."""

from __future__ import annotations

import contextlib
import hashlib
import hmac
import json
from typing import Any
from uuid import uuid4

from sketch2life.application.ports.identity import (
    IdentityAccountConflict,
    IdentityAccountProvisioner,
    ProvisionedIdentity,
)
from sketch2life.application.ports.teacher_invitations import (
    TeacherInvitationAssignmentState,
    TeacherInvitationIdempotencyMismatch,
    TeacherInvitationIdentityState,
    TeacherInvitationIdentityUnavailable,
    TeacherInvitationKeyUnavailable,
    TeacherInvitationNotFound,
    TeacherInvitationReceipt,
    TeacherInvitationRepository,
    TeacherInvitationResult,
    TeacherInvitationSetupUnavailable,
    TeacherInvitationWriteConflict,
)

_MIN_RECEIPT_KEY_BYTES = 32
_INVITE_OPERATION = "POST /api/be1/v1/organizations/{organization_id}/teacher-invitations"
_RESEND_OPERATION = (
    "POST /api/be1/v1/organizations/{organization_id}/teacher-invitations/"
    "{account_ref}/resend"
)


class TeacherInvitationService:
    def __init__(
        self,
        *,
        repository: TeacherInvitationRepository,
        identity_provisioner: IdentityAccountProvisioner | None,
        receipt_hmac_key: bytes | None,
    ) -> None:
        self._repository = repository
        self._identity_provisioner = identity_provisioner
        self._receipt_hmac_key = receipt_hmac_key

    def invite_teacher(
        self,
        *,
        principal_subject: str,
        principal_issuer: str,
        organization_id: str,
        email: str,
        idempotency_key: str,
    ) -> TeacherInvitationResult:
        key = self._require_key()
        provisioner = self._require_provisioner()
        normalized_email = email.strip().casefold()
        operation_scope = _INVITE_OPERATION.format(organization_id=organization_id)
        principal_ref = _mac(
            key,
            "be1.teacher-invitation.principal.v1",
            {"issuer": principal_issuer, "subject": principal_subject},
        )
        audit_actor_ref = _mac(
            key,
            "be1.teacher-invitation.audit-actor.v1",
            {"issuer": principal_issuer, "subject": principal_subject},
        )
        request_fingerprint = _mac(
            key,
            "be1.teacher-invitation.request.v1",
            {
                "operation": _INVITE_OPERATION,
                "principal": {"issuer": principal_issuer, "subject": principal_subject},
                "organization_id": organization_id,
                "email": normalized_email,
            },
        )
        email_lock_fingerprint = _mac(
            key, "be1.teacher-invitation.email-lock.v1", {"email": normalized_email}
        )
        organization_email_lock_fingerprint = _mac(
            key,
            "be1.teacher-invitation.organization-email-lock.v1",
            {"organization_id": organization_id, "email": normalized_email},
        )
        receipt_args = {
            "principal_ref": principal_ref,
            "operation_scope": operation_scope,
            "idempotency_key": idempotency_key,
        }
        receipt = self._repository.find_receipt(**receipt_args)
        if receipt is not None:
            return _replay(receipt, request_fingerprint)

        created_identity: ProvisionedIdentity | None = None
        try:
            with self._repository.transaction() as uow:
                uow.lock_command(**receipt_args)
                uow.lock_invitation_scope(
                    organization_id=organization_id,
                    email_lock_fingerprint=email_lock_fingerprint,
                    organization_email_lock_fingerprint=organization_email_lock_fingerprint,
                )
                receipt = uow.get_receipt(**receipt_args)
                if receipt is not None:
                    return _replay(receipt, request_fingerprint)

                provisioned, created = self._resolve_identity(
                    provisioner, normalized_email
                )
                if created:
                    created_identity = provisioned
                identity_lock_fingerprint = _mac(
                    key,
                    "be1.teacher-invitation.identity-lock.v1",
                    {"issuer": provisioned.issuer, "subject": provisioned.subject},
                )
                uow.lock_identity(identity_lock_fingerprint=identity_lock_fingerprint)
                identity = uow.identity_by_subject(subject=provisioned.subject)
                if identity is None:
                    if not created:
                        raise TeacherInvitationSetupUnavailable()
                    identity = uow.create_pending_identity(
                        provisioned_identity=provisioned,
                        account_ref=str(uuid4()),
                    )
                elif not _is_pending_teacher(identity, provisioned):
                    raise TeacherInvitationSetupUnavailable()

                assignments = uow.teacher_assignments(
                    organization_id=organization_id,
                    subject=provisioned.subject,
                )
                if assignments:
                    if not _is_pending_org_assignment(assignments):
                        raise TeacherInvitationSetupUnavailable()
                else:
                    if not created:
                        # Pending Teacher of another organization: never disclose its account_ref.
                        raise TeacherInvitationSetupUnavailable()
                    uow.create_pending_teacher_assignment(
                        organization_id=organization_id,
                        subject=provisioned.subject,
                    )

                result = TeacherInvitationResult(account_ref=identity.account_ref)
                uow.queue_password_setup(subject=provisioned.subject)
                uow.record_audit(
                    organization_id=organization_id,
                    audit_actor_ref=audit_actor_ref,
                    action="TEACHER_INVITATION_REQUESTED",
                    account_ref=identity.account_ref,
                )
                uow.add_receipt(
                    **receipt_args,
                    organization_id=organization_id,
                    request_fingerprint=request_fingerprint,
                    result=result,
                )
                return result
        except TeacherInvitationWriteConflict:
            raced_receipt = self._repository.find_receipt(**receipt_args)
            if raced_receipt is not None:
                return _replay(raced_receipt, request_fingerprint)
            self._discard_created_identity(provisioner, created_identity)
            raise TeacherInvitationSetupUnavailable() from None
        except Exception:
            self._discard_created_identity(provisioner, created_identity)
            raise

    def resend_teacher_invitation(
        self,
        *,
        principal_subject: str,
        principal_issuer: str,
        organization_id: str,
        account_ref: str,
        idempotency_key: str,
    ) -> TeacherInvitationResult:
        key = self._require_key()
        self._require_provisioner()
        operation_scope = _RESEND_OPERATION.format(
            organization_id=organization_id,
            account_ref=account_ref,
        )
        principal_ref = _mac(
            key,
            "be1.teacher-invitation.principal.v1",
            {"issuer": principal_issuer, "subject": principal_subject},
        )
        audit_actor_ref = _mac(
            key,
            "be1.teacher-invitation.audit-actor.v1",
            {"issuer": principal_issuer, "subject": principal_subject},
        )
        request_fingerprint = _mac(
            key,
            "be1.teacher-invitation.resend-request.v1",
            {
                "principal": {"issuer": principal_issuer, "subject": principal_subject},
                "organization_id": organization_id,
                "account_ref": account_ref,
            },
        )
        receipt_args = {
            "principal_ref": principal_ref,
            "operation_scope": operation_scope,
            "idempotency_key": idempotency_key,
        }
        receipt = self._repository.find_receipt(**receipt_args)
        if receipt is not None:
            return _replay(receipt, request_fingerprint)

        try:
            with self._repository.transaction() as uow:
                uow.lock_command(**receipt_args)
                uow.lock_invitation_account(account_ref=account_ref)
                receipt = uow.get_receipt(**receipt_args)
                if receipt is not None:
                    return _replay(receipt, request_fingerprint)

                invitation = uow.pending_invitation_by_account(
                    organization_id=organization_id,
                    account_ref=account_ref,
                )
                if invitation is None:
                    raise TeacherInvitationNotFound()
                uow.queue_password_setup(subject=invitation.subject)
                uow.record_audit(
                    organization_id=organization_id,
                    audit_actor_ref=audit_actor_ref,
                    action="TEACHER_INVITATION_RESENT",
                    account_ref=account_ref,
                )
                result = TeacherInvitationResult(account_ref=account_ref)
                uow.add_receipt(
                    **receipt_args,
                    organization_id=organization_id,
                    request_fingerprint=request_fingerprint,
                    result=result,
                )
                return result
        except TeacherInvitationWriteConflict:
            raced_receipt = self._repository.find_receipt(**receipt_args)
            if raced_receipt is not None:
                return _replay(raced_receipt, request_fingerprint)
            raise TeacherInvitationSetupUnavailable() from None

    def _require_key(self) -> bytes:
        key = self._receipt_hmac_key
        if key is None or len(key) < _MIN_RECEIPT_KEY_BYTES:
            raise TeacherInvitationKeyUnavailable()
        return key

    def _require_provisioner(self) -> IdentityAccountProvisioner:
        provisioner = self._identity_provisioner
        if provisioner is None:
            raise TeacherInvitationIdentityUnavailable()
        return provisioner

    @staticmethod
    def _discard_created_identity(
        provisioner: IdentityAccountProvisioner,
        provisioned: ProvisionedIdentity | None,
    ) -> None:
        if provisioned is None:
            return
        # Match the existing account-provisioning compensation: never log the provider UID.
        with contextlib.suppress(Exception):
            provisioner.delete_account(provisioned.subject)

    @staticmethod
    def _resolve_identity(
        provisioner: IdentityAccountProvisioner, email: str
    ) -> tuple[ProvisionedIdentity, bool]:
        try:
            existing = provisioner.find_account_by_email(email)
        except IdentityAccountConflict:
            raise TeacherInvitationSetupUnavailable() from None
        except Exception:
            raise TeacherInvitationIdentityUnavailable() from None
        if existing is not None:
            return existing, False
        try:
            return provisioner.create_account(email=email), True
        except IdentityAccountConflict:
            try:
                raced = provisioner.find_account_by_email(email)
            except Exception:
                raise TeacherInvitationIdentityUnavailable() from None
            if raced is not None:
                return raced, False
            raise TeacherInvitationSetupUnavailable() from None
        except Exception:
            raise TeacherInvitationIdentityUnavailable() from None


def _is_pending_teacher(
    identity: TeacherInvitationIdentityState, provisioned: ProvisionedIdentity
) -> bool:
    return (
        identity.issuer == provisioned.issuer
        and identity.state == "pending_verification"
        and identity.account_role == "teacher"
        and identity.email_verification_required
    )


def _is_pending_org_assignment(
    assignments: tuple[TeacherInvitationAssignmentState, ...],
) -> bool:
    if len(assignments) != 1:
        return False
    assignment = assignments[0]
    return (
        assignment.role == "teacher"
        and assignment.class_id is None
        and not assignment.active
        and assignment.pending_activation
    )


def _replay(
    receipt: TeacherInvitationReceipt, request_fingerprint: str
) -> TeacherInvitationResult:
    if not hmac.compare_digest(receipt.request_fingerprint, request_fingerprint):
        raise TeacherInvitationIdempotencyMismatch()
    return receipt.result


def _mac(key: bytes, domain: str, payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hmac.new(key, domain.encode("ascii") + b"\0" + canonical, hashlib.sha256).hexdigest()
