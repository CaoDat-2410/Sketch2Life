"""SQLAlchemy persistence adapter for Teacher invitations."""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from contextlib import contextmanager
from uuid import uuid4

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import ProvisionedIdentity
from sketch2life.application.ports.teacher_invitations import (
    TeacherInvitationAssignmentState,
    TeacherInvitationIdentityState,
    TeacherInvitationReceipt,
    TeacherInvitationResult,
    TeacherInvitationStoreUnavailable,
    TeacherInvitationWriteConflict,
)
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    Be1CommandReceiptModel,
    OrganizationAssignmentModel,
)
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.infrastructure.persistence.platform_models import EmailDeliveryModel


class SqlTeacherInvitationRepository:
    """Own a request-scoped SQLAlchemy session for the invitation use case."""

    def __init__(self, db: Session) -> None:
        self._db = db

    @contextmanager
    def transaction(self) -> Iterator[SqlTeacherInvitationUnitOfWork]:
        try:
            yield SqlTeacherInvitationUnitOfWork(self._db)
            self._db.commit()
        except IntegrityError:
            self._db.rollback()
            raise TeacherInvitationWriteConflict() from None
        except SQLAlchemyError:
            self._db.rollback()
            raise TeacherInvitationStoreUnavailable() from None
        except Exception:
            self._db.rollback()
            raise

    def find_receipt(
        self, *, principal_ref: str, operation_scope: str, idempotency_key: str
    ) -> TeacherInvitationReceipt | None:
        try:
            receipt = self._db.get(
                Be1CommandReceiptModel,
                (principal_ref, operation_scope, idempotency_key),
            )
            return _receipt(receipt) if receipt is not None else None
        except SQLAlchemyError:
            self._db.rollback()
            raise TeacherInvitationStoreUnavailable() from None


class SqlTeacherInvitationUnitOfWork:
    """Persistence operations for one invitation or resend transaction."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def lock_command(
        self, *, principal_ref: str, operation_scope: str, idempotency_key: str
    ) -> None:
        self._advisory_lock(
            "be1.teacher-invitation.command.v1",
            principal_ref,
            operation_scope,
            idempotency_key,
        )

    def lock_invitation_scope(
        self,
        *,
        organization_id: str,
        email_lock_fingerprint: str,
        organization_email_lock_fingerprint: str,
    ) -> None:
        # The email-only lock also serializes one provider identity being attached to two orgs.
        self._advisory_lock("be1.teacher-invitation.email.v1", email_lock_fingerprint)
        # The organization-bound lock protects NULL-class_id Teacher assignment uniqueness.
        self._advisory_lock(
            "be1.teacher-invitation.organization-email.v1",
            organization_id,
            organization_email_lock_fingerprint,
        )

    def lock_identity(self, *, identity_lock_fingerprint: str) -> None:
        self._advisory_lock(
            "be1.teacher-invitation.identity.v1", identity_lock_fingerprint
        )

    def lock_invitation_account(self, *, account_ref: str) -> None:
        self._db.scalar(
            select(AdultIdentityModel)
            .where(AdultIdentityModel.account_id == account_ref)
            .with_for_update()
        )

    def get_receipt(
        self, *, principal_ref: str, operation_scope: str, idempotency_key: str
    ) -> TeacherInvitationReceipt | None:
        receipt = self._db.get(
            Be1CommandReceiptModel,
            (principal_ref, operation_scope, idempotency_key),
        )
        return _receipt(receipt) if receipt is not None else None

    def identity_by_subject(self, *, subject: str) -> TeacherInvitationIdentityState | None:
        identity = self._db.scalar(
            select(AdultIdentityModel)
            .where(AdultIdentityModel.subject == subject)
            .with_for_update()
        )
        return _identity_state(identity) if identity is not None else None

    def teacher_assignments(
        self, *, organization_id: str, subject: str
    ) -> tuple[TeacherInvitationAssignmentState, ...]:
        rows = self._db.scalars(
            select(OrganizationAssignmentModel)
            .where(
                OrganizationAssignmentModel.organization_id == organization_id,
                OrganizationAssignmentModel.subject == subject,
                OrganizationAssignmentModel.role == "teacher",
            )
            .with_for_update()
        )
        return tuple(
            TeacherInvitationAssignmentState(
                role=row.role,
                class_id=row.class_id,
                active=row.active,
                pending_activation=row.pending_activation,
            )
            for row in rows
        )

    def create_pending_identity(
        self, *, provisioned_identity: ProvisionedIdentity, account_ref: str
    ) -> TeacherInvitationIdentityState:
        identity = AdultIdentityModel(
            account_id=account_ref,
            subject=provisioned_identity.subject,
            issuer=provisioned_identity.issuer,
            state="pending_verification",
            email_verification_required=True,
            account_role="teacher",
            role_revision=1,
        )
        self._db.add(identity)
        return _identity_state(identity)

    def create_pending_teacher_assignment(self, *, organization_id: str, subject: str) -> None:
        self._db.add(
            OrganizationAssignmentModel(
                assignment_id=str(uuid4()),
                organization_id=organization_id,
                subject=subject,
                class_id=None,
                role="teacher",
                active=False,
                pending_activation=True,
            )
        )

    def pending_invitation_by_account(
        self, *, organization_id: str, account_ref: str
    ) -> TeacherInvitationIdentityState | None:
        identity = self._db.scalar(
            select(AdultIdentityModel)
            .where(AdultIdentityModel.account_id == account_ref)
            .with_for_update()
        )
        if (
            identity is None
            or identity.state != "pending_verification"
            or not identity.email_verification_required
            or identity.account_role != "teacher"
        ):
            return None
        assignments = self._db.scalars(
            select(OrganizationAssignmentModel)
            .where(
                OrganizationAssignmentModel.organization_id == organization_id,
                OrganizationAssignmentModel.subject == identity.subject,
                OrganizationAssignmentModel.role == "teacher",
            )
            .with_for_update()
        ).all()
        if len(assignments) != 1:
            return None
        assignment = assignments[0]
        if (
            assignment.class_id is not None
            or assignment.active
            or not assignment.pending_activation
        ):
            return None
        return _identity_state(identity)

    def queue_password_setup(self, *, subject: str) -> None:
        self._db.add(
            EmailDeliveryModel(
                delivery_id=str(uuid4()),
                recipient_ref=subject,
                template="password_setup",
                state="pending",
                attempts=0,
            )
        )

    def record_audit(
        self,
        *,
        organization_id: str,
        audit_actor_ref: str,
        action: str,
        account_ref: str,
    ) -> None:
        self._db.add(
            CoreAuditEntryModel(
                audit_id=str(uuid4()),
                organization_id=organization_id,
                actor_ref=audit_actor_ref,
                action=action,
                resource_type="adult_account",
                resource_id=account_ref,
                decision="allowed",
            )
        )

    def add_receipt(
        self,
        *,
        principal_ref: str,
        operation_scope: str,
        idempotency_key: str,
        organization_id: str,
        request_fingerprint: str,
        result: TeacherInvitationResult,
    ) -> None:
        self._db.add(
            Be1CommandReceiptModel(
                principal_ref=principal_ref,
                operation_scope=operation_scope,
                idempotency_key=idempotency_key,
                organization_id=organization_id,
                request_fingerprint=request_fingerprint,
                response_json={
                    "account_ref": result.account_ref,
                    "status": result.status,
                },
            )
        )

    def _advisory_lock(self, *scope_parts: str) -> None:
        digest = hashlib.sha256("\0".join(scope_parts).encode("utf-8")).digest()[:8]
        lock_key = int.from_bytes(digest, byteorder="big", signed=True)
        self._db.execute(
            text("SELECT pg_advisory_xact_lock(:lock_key)"),
            {"lock_key": lock_key},
        )


def _identity_state(identity: AdultIdentityModel) -> TeacherInvitationIdentityState:
    return TeacherInvitationIdentityState(
        subject=identity.subject,
        account_ref=identity.account_id,
        issuer=identity.issuer,
        state=identity.state,
        account_role=identity.account_role,
        email_verification_required=identity.email_verification_required,
    )


def _receipt(receipt: Be1CommandReceiptModel) -> TeacherInvitationReceipt:
    response = receipt.response_json
    account_ref = response.get("account_ref") if isinstance(response, dict) else None
    status = response.get("status") if isinstance(response, dict) else None
    if (
        not isinstance(response, dict)
        or set(response) != {"account_ref", "status"}
        or not isinstance(account_ref, str)
        or status != "PENDING_VERIFICATION"
    ):
        raise TeacherInvitationWriteConflict()
    return TeacherInvitationReceipt(
        request_fingerprint=receipt.request_fingerprint,
        result=TeacherInvitationResult(account_ref=account_ref),
    )
