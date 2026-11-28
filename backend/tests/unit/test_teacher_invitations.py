"""Unit tests for Teacher invitation orchestration with local fakes."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from email.message import EmailMessage
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import (
    IdentityAccountConflict,
    IdentityAccountProfile,
    IdentityAccountProvisioner,
    IdentityAccountProvisioningUnavailable,
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
    TeacherInvitationResult,
    TeacherInvitationSetupUnavailable,
    TeacherInvitationStoreUnavailable,
    TeacherInvitationUnitOfWork,
)
from sketch2life.application.services.teacher_invitations import TeacherInvitationService
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.infrastructure.persistence.platform_models import EmailDeliveryModel
from sketch2life.infrastructure.platform_admin.email_worker import deliver_pending

KEY = b"teacher-invitation-test-key-at-least-32-bytes"
EMAIL = "Teacher.Sentinel@Example.test"
SUBJECT = "provider-uid-sentinel"
ORG = "school-sentinel"
ACTOR = "manager-uid-sentinel"
ISSUER = "synthetic-issuer"


@dataclass
class FakeProvisioner(IdentityAccountProvisioner):
    identities: dict[str, ProvisionedIdentity] = field(default_factory=dict)
    lookup_error: Exception | None = None
    create_error: Exception | None = None
    lookups: list[str] = field(default_factory=list)
    creations: list[str] = field(default_factory=list)
    deletions: list[str] = field(default_factory=list)

    def create_password_account(self, *, email: str, password: str) -> ProvisionedIdentity:
        raise AssertionError("not used")

    def create_account(self, *, email: str, display_name: str | None = None) -> ProvisionedIdentity:
        self.creations.append(email)
        if self.create_error is not None:
            raise self.create_error
        identity = ProvisionedIdentity(SUBJECT, ISSUER)
        self.identities[email] = identity
        return identity

    def delete_account(self, subject: str) -> None:
        self.deletions.append(subject)
        self.identities = {
            email: identity
            for email, identity in self.identities.items()
            if identity.subject != subject
        }

    def set_account_disabled(self, subject: str, disabled: bool) -> None:
        raise AssertionError("not used")

    def get_account_profiles(self, subjects: list[str]) -> dict[str, IdentityAccountProfile]:
        raise AssertionError("not used")

    def find_account_by_email(self, email: str) -> ProvisionedIdentity | None:
        self.lookups.append(email)
        if self.lookup_error is not None:
            raise self.lookup_error
        return self.identities.get(email)


class FakeUnitOfWork(TeacherInvitationUnitOfWork):
    def __init__(self, repository: FakeRepository) -> None:
        self.repository = repository

    def lock_command(
        self, *, principal_ref: str, operation_scope: str, idempotency_key: str
    ) -> None:
        return None

    def lock_invitation_scope(
        self,
        *,
        organization_id: str,
        email_lock_fingerprint: str,
        organization_email_lock_fingerprint: str,
    ) -> None:
        return None

    def lock_identity(self, *, identity_lock_fingerprint: str) -> None:
        return None

    def lock_invitation_account(self, *, account_ref: str) -> None:
        return None

    def get_receipt(
        self, *, principal_ref: str, operation_scope: str, idempotency_key: str
    ) -> TeacherInvitationReceipt | None:
        return self.repository.find_receipt(
            principal_ref=principal_ref,
            operation_scope=operation_scope,
            idempotency_key=idempotency_key,
        )

    def identity_by_subject(self, *, subject: str) -> TeacherInvitationIdentityState | None:
        return self.repository.identities.get(subject)

    def teacher_assignments(
        self, *, organization_id: str, subject: str
    ) -> tuple[TeacherInvitationAssignmentState, ...]:
        return self.repository.assignments.get((organization_id, subject), ())

    def create_pending_identity(
        self, *, provisioned_identity: ProvisionedIdentity, account_ref: str
    ) -> TeacherInvitationIdentityState:
        state = TeacherInvitationIdentityState(
            subject=provisioned_identity.subject,
            account_ref=account_ref,
            issuer=provisioned_identity.issuer,
            state="pending_verification",
            account_role="teacher",
            email_verification_required=True,
        )
        self.repository.identities[state.subject] = state
        return state

    def create_pending_teacher_assignment(self, *, organization_id: str, subject: str) -> None:
        self.repository.assignments[(organization_id, subject)] = (
            TeacherInvitationAssignmentState(
                role="teacher",
                class_id=None,
                active=False,
                pending_activation=True,
            ),
        )

    def pending_invitation_by_account(
        self, *, organization_id: str, account_ref: str
    ) -> TeacherInvitationIdentityState | None:
        identity = next(
            (
                row
                for row in self.repository.identities.values()
                if row.account_ref == account_ref
                and row.state == "pending_verification"
                and row.account_role == "teacher"
                and row.email_verification_required
            ),
            None,
        )
        assignments = (
            self.repository.assignments.get((organization_id, identity.subject), ())
            if identity is not None
            else ()
        )
        if identity is None or len(assignments) != 1:
            return None
        assignment = assignments[0]
        if (
            assignment.class_id is not None
            or assignment.active
            or not assignment.pending_activation
        ):
            return None
        return identity

    def queue_password_setup(self, *, subject: str) -> None:
        self.repository.outbox_subjects.append(subject)

    def record_audit(
        self,
        *,
        organization_id: str,
        audit_actor_ref: str,
        action: str,
        account_ref: str,
    ) -> None:
        self.repository.audit_rows.append(
            {
                "organization_id": organization_id,
                "actor_ref": audit_actor_ref,
                "action": action,
                "resource_id": account_ref,
            }
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
        self.repository.receipts[(principal_ref, operation_scope, idempotency_key)] = (
            TeacherInvitationReceipt(request_fingerprint, result)
        )


@dataclass
class FakeRepository:
    identities: dict[str, TeacherInvitationIdentityState] = field(default_factory=dict)
    assignments: dict[tuple[str, str], tuple[TeacherInvitationAssignmentState, ...]] = field(
        default_factory=dict
    )
    receipts: dict[tuple[str, str, str], TeacherInvitationReceipt] = field(default_factory=dict)
    outbox_subjects: list[str] = field(default_factory=list)
    audit_rows: list[dict[str, str]] = field(default_factory=list)
    commit_error: Exception | None = None

    @contextmanager
    def transaction(self) -> Iterator[FakeUnitOfWork]:
        yield FakeUnitOfWork(self)
        if self.commit_error is not None:
            raise self.commit_error

    def find_receipt(
        self, *, principal_ref: str, operation_scope: str, idempotency_key: str
    ) -> TeacherInvitationReceipt | None:
        return self.receipts.get((principal_ref, operation_scope, idempotency_key))


def _service(
    repository: FakeRepository | None = None,
    provisioner: IdentityAccountProvisioner | None = None,
    key: bytes | None = KEY,
) -> tuple[TeacherInvitationService, FakeRepository, FakeProvisioner]:
    store = repository or FakeRepository()
    provider = provisioner or FakeProvisioner()
    return (
        TeacherInvitationService(
            repository=store,
            identity_provisioner=provider,
            receipt_hmac_key=key,
        ),
        store,
        provider,
    )


def _invite(
    service: TeacherInvitationService,
    *,
    email: str = EMAIL,
    key: str = "invite-1",
) -> TeacherInvitationResult:
    return service.invite_teacher(
        principal_subject=ACTOR,
        principal_issuer=ISSUER,
        organization_id=ORG,
        email=email,
        idempotency_key=key,
    )


def test_new_invitation_normalizes_address_and_stores_only_safe_receipt_and_audit() -> None:
    service, repository, provider = _service()

    result = _invite(service)

    assert result.status == "PENDING_VERIFICATION"
    assert len(result.account_ref) == 36
    assert provider.lookups == [EMAIL.strip().casefold()]
    assert provider.creations == [EMAIL.strip().casefold()]
    assert repository.outbox_subjects == [SUBJECT]
    assert len(repository.assignments[(ORG, SUBJECT)]) == 1
    receipt = next(iter(repository.receipts.values()))
    assert receipt.result == result
    assert EMAIL.casefold() not in repr(receipt)
    assert SUBJECT not in repr(receipt)
    audit = repository.audit_rows[0]
    assert audit["actor_ref"] != ACTOR
    assert SUBJECT not in repr(audit)
    assert EMAIL.casefold() not in repr(audit)


def test_exact_idempotent_replay_returns_safe_result_without_provider_call() -> None:
    service, repository, provider = _service()
    created = _invite(service)
    lookup_count = len(provider.lookups)
    create_count = len(provider.creations)

    replay = _invite(service)

    assert replay == created
    assert len(provider.lookups) == lookup_count
    assert len(provider.creations) == create_count
    assert len(repository.outbox_subjects) == 1


def test_same_key_with_changed_address_uses_generic_idempotency_error() -> None:
    service, _, _ = _service()
    _invite(service)

    with pytest.raises(TeacherInvitationIdempotencyMismatch):
        _invite(service, email="different@example.test")


def test_pending_teacher_without_this_org_assignment_gets_generic_conflict() -> None:
    identity = ProvisionedIdentity(SUBJECT, ISSUER)
    provider = FakeProvisioner(identities={EMAIL.casefold(): identity})
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
    service, _, _ = _service(repository=repository, provisioner=provider)

    with pytest.raises(TeacherInvitationSetupUnavailable):
        _invite(service)

    assert (ORG, SUBJECT) not in repository.assignments
    assert repository.outbox_subjects == []


def test_repeat_invite_for_same_org_pending_teacher_queues_one_resend() -> None:
    identity = ProvisionedIdentity(SUBJECT, ISSUER)
    provider = FakeProvisioner(identities={EMAIL.casefold(): identity})
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
    service, _, _ = _service(repository=repository, provisioner=provider)

    result = _invite(service)

    assert result.account_ref == "account-ref-1"
    assert len(repository.assignments[(ORG, SUBJECT)]) == 1
    assert repository.outbox_subjects == [SUBJECT]


@pytest.mark.parametrize(
    ("state", "role", "verification_required"),
    [
        ("active", "teacher", False),
        ("disabled", "teacher", True),
        ("pending_verification", "parent", True),
        ("pending_verification", "school_manager", True),
        ("pending_verification", "teacher", False),
    ],
)
def test_existing_non_pending_teacher_matrix_refuses_generically(
    state: str, role: str, verification_required: bool
) -> None:
    provider = FakeProvisioner(identities={EMAIL.casefold(): ProvisionedIdentity(SUBJECT, ISSUER)})
    repository = FakeRepository(
        identities={
            SUBJECT: TeacherInvitationIdentityState(
                subject=SUBJECT,
                account_ref="account-ref-1",
                issuer=ISSUER,
                state=state,
                account_role=role,
                email_verification_required=verification_required,
            )
        }
    )
    service, _, _ = _service(repository=repository, provisioner=provider)

    with pytest.raises(TeacherInvitationSetupUnavailable):
        _invite(service)

    assert repository.outbox_subjects == []
    assert repository.audit_rows == []
    assert repository.receipts == {}


def test_pending_teacher_of_another_org_gets_generic_conflict_and_no_account_ref() -> None:
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
        assignments={
            ("other-school", SUBJECT): (
                TeacherInvitationAssignmentState(
                    role="teacher",
                    class_id=None,
                    active=False,
                    pending_activation=True,
                ),
            )
        },
    )
    service, _, _ = _service(repository=repository, provisioner=provider)

    with pytest.raises(TeacherInvitationSetupUnavailable):
        _invite(service)

    assert (ORG, SUBJECT) not in repository.assignments


def test_resend_requires_a_same_org_pending_teacher_and_is_idempotent() -> None:
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
    service, _, _ = _service(repository=repository)
    args = {
        "principal_subject": ACTOR,
        "principal_issuer": ISSUER,
        "organization_id": ORG,
        "account_ref": "account-ref-1",
        "idempotency_key": "resend-1",
    }

    first = service.resend_teacher_invitation(**args)
    replay = service.resend_teacher_invitation(**args)

    assert first == replay
    assert repository.outbox_subjects == [SUBJECT]
    assert len(repository.audit_rows) == 1


def test_resend_absent_invitation_is_not_found() -> None:
    service, _, _ = _service()

    with pytest.raises(TeacherInvitationNotFound):
        service.resend_teacher_invitation(
            principal_subject=ACTOR,
            principal_issuer=ISSUER,
            organization_id=ORG,
            account_ref="unknown-account",
            idempotency_key="resend-unknown",
        )


@pytest.mark.parametrize(
    ("organization_id", "state", "verification_required"),
    [
        (ORG, "active", False),
        (ORG, "disabled", True),
        ("other-school", "pending_verification", True),
    ],
)
def test_resend_active_disabled_or_foreign_invitation_is_not_found(
    organization_id: str,
    state: str,
    verification_required: bool,
) -> None:
    repository = FakeRepository(
        identities={
            SUBJECT: TeacherInvitationIdentityState(
                subject=SUBJECT,
                account_ref="account-ref-state",
                issuer=ISSUER,
                state=state,
                account_role="teacher",
                email_verification_required=verification_required,
            )
        },
        assignments={
            (organization_id, SUBJECT): (
                TeacherInvitationAssignmentState(
                    role="teacher",
                    class_id=None,
                    active=state == "active",
                    pending_activation=state == "pending_verification",
                ),
            )
        },
    )
    service, _, _ = _service(repository=repository)

    with pytest.raises(TeacherInvitationNotFound):
        service.resend_teacher_invitation(
            principal_subject=ACTOR,
            principal_issuer=ISSUER,
            organization_id=ORG,
            account_ref="account-ref-state",
            idempotency_key=f"resend-{state}-{organization_id}",
        )


def test_missing_fingerprint_key_and_provider_fail_closed() -> None:
    no_key, _, _ = _service(key=None)
    with pytest.raises(TeacherInvitationKeyUnavailable):
        _invite(no_key)

    no_provider = TeacherInvitationService(
        repository=FakeRepository(),
        identity_provisioner=None,
        receipt_hmac_key=KEY,
    )
    with pytest.raises(TeacherInvitationIdentityUnavailable):
        _invite(no_provider)


def test_new_provider_identity_is_compensated_when_persistence_commit_fails() -> None:
    repository = FakeRepository(commit_error=TeacherInvitationStoreUnavailable())
    provider = FakeProvisioner()
    service, _, _ = _service(repository=repository, provisioner=provider)

    with pytest.raises(TeacherInvitationStoreUnavailable):
        _invite(service)

    assert provider.deletions == [SUBJECT]
    assert provider.identities == {}


def test_fake_email_worker_builds_action_links_only_for_the_send_call() -> None:
    engine = create_engine("sqlite://")
    AdultIdentityModel.__table__.create(engine)
    EmailDeliveryModel.__table__.create(engine)
    sent: list[EmailMessage] = []

    class FakeEmailIdentityProvider:
        def get_user(self, subject: str) -> SimpleNamespace:
            assert subject == SUBJECT
            return SimpleNamespace(email=EMAIL.casefold(), disabled=False)

        def password_link(self, email: str) -> str:
            assert email == EMAIL.casefold()
            return "https://example.test/setup?token=synthetic-setup-token"

        def verification_link(self, email: str) -> str:
            assert email == EMAIL.casefold()
            return "https://example.test/verify?token=synthetic-verify-token"

    with Session(engine) as db:
        db.add(
            AdultIdentityModel(
                account_id="worker-account-ref",
                subject=SUBJECT,
                issuer=ISSUER,
                state="pending_verification",
                email_verification_required=True,
                account_role="teacher",
                role_revision=1,
            )
        )
        db.add(
            EmailDeliveryModel(
                delivery_id=str(uuid4()),
                recipient_ref=SUBJECT,
                template="password_setup",
                state="pending",
                attempts=0,
            )
        )
        db.commit()

        result = deliver_pending(
            db,
            SimpleNamespace(smtp_from="no-reply@example.test"),
            FakeEmailIdentityProvider(),
            sent.append,
        )

        row = db.scalar(select(EmailDeliveryModel))
        assert result == {"sent": 1, "failed": 0}
        assert row is not None and row.state == "sent"
        assert "synthetic-setup-token" in sent[0].get_body(("plain",)).get_content()
        assert "synthetic-verify-token" in sent[0].get_body(("plain",)).get_content()
        assert "synthetic-setup-token" not in repr(row)
        assert "synthetic-verify-token" not in repr(row)
    engine.dispose()


@pytest.mark.parametrize(
    ("provider_error", "expected_error"),
    [
        (IdentityAccountConflict(), TeacherInvitationSetupUnavailable),
        (
            IdentityAccountProvisioningUnavailable("private provider detail"),
            TeacherInvitationIdentityUnavailable,
        ),
    ],
)
def test_provider_errors_do_not_escape_as_identity_details(
    provider_error: Exception, expected_error: type[Exception]
) -> None:
    provider = FakeProvisioner(lookup_error=provider_error)
    service, _, _ = _service(provisioner=provider)

    with pytest.raises(expected_error) as error:
        _invite(service)

    assert "private provider detail" not in str(error.value)
