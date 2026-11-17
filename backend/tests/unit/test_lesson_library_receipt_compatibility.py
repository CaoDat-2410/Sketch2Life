"""Offline checks for pre-revision Parent Group command receipts."""

from __future__ import annotations

from typing import Any, cast

import pytest
from sketch2life.infrastructure.lesson_library.service import (
    LessonLibraryError,
    LessonLibraryService,
)

ORG_ID = "synthetic-org-01"
GROUP_ID = "synthetic-group-01"
MEMBERSHIP_ID = "synthetic-membership-01"
PARENT_ID = "synthetic-parent-01"
INVITE_SCOPE = f"POST /organizations/{ORG_ID}/parent-groups/{GROUP_ID}/invitations"
ACCEPT_SCOPE = f"POST /me/parent-group-invitations/{MEMBERSHIP_ID}/accept"
INVITE_PAYLOAD = {"parent_principal_ref": PARENT_ID}
ACCEPT_PAYLOAD = {"membership_id": MEMBERSHIP_ID}

LEGACY_INVITATION = {
    "contract": "ParentGroupInvitationV1",
    "membership_id": MEMBERSHIP_ID,
    "parent_group_id": GROUP_ID,
    "state": "INVITED",
    "invited_at": "2026-10-31T09:00:00Z",
    "expires_at": "2026-11-30T09:00:00Z",
    "accepted_at": None,
}
LEGACY_ACCEPTANCE = {
    "contract": "ParentGroupMembershipV1",
    "membership_id": MEMBERSHIP_ID,
    "parent_group_id": GROUP_ID,
    "state": "ACTIVE",
    "invited_at": "2026-10-31T09:00:00Z",
    "expires_at": "2026-11-30T09:00:00Z",
    "accepted_at": "2026-10-31T09:05:00Z",
}


class FakeResult:
    def __init__(self, row: dict[str, Any] | None) -> None:
        self.row = row

    def mappings(self) -> FakeResult:
        return self

    def one_or_none(self) -> dict[str, Any] | None:
        return self.row


class FakeReceiptDb:
    """Return synthetic receipt/membership rows and reject every write method."""

    def __init__(
        self,
        receipt: dict[str, Any],
        membership: dict[str, Any] | None,
    ) -> None:
        self.receipt = receipt
        self.membership = membership
        self.statements: list[Any] = []
        self.add_calls = 0
        self.flush_calls = 0
        self.commit_calls = 0

    def execute(self, statement: Any) -> FakeResult:
        self.statements.append(statement)
        compiled_values = set(statement.compile().params.values())
        identity_values = {
            self.receipt["organization_id"],
            self.receipt["principal_ref"],
            self.receipt["operation_scope"],
            self.receipt["idempotency_key"],
        }
        sql = str(statement).lower()
        if "command_receipts" in sql:
            if identity_values.issubset(compiled_values):
                return FakeResult(self.receipt)
            return FakeResult(None)
        if "be1_parent_group_members" in sql:
            return FakeResult(self.membership)
        raise AssertionError(f"unexpected statement in offline replay test: {sql}")

    def add(self, _value: object) -> None:
        self.add_calls += 1
        raise AssertionError("receipt replay must not add ORM rows")

    def flush(self) -> None:
        self.flush_calls += 1
        raise AssertionError("receipt replay must not flush writes")

    def commit(self) -> None:
        self.commit_calls += 1
        raise AssertionError("receipt replay must not commit writes")


def _service(db: FakeReceiptDb) -> LessonLibraryService:
    service = object.__new__(LessonLibraryService)
    cast(Any, service).db = db
    return service


def _receipt(
    *,
    scope: str = INVITE_SCOPE,
    payload: dict[str, Any] = INVITE_PAYLOAD,
    response: dict[str, Any] | list[Any] = LEGACY_INVITATION,
    fingerprint: str | None = None,
    principal_ref: str = "synthetic-manager-01",
) -> dict[str, Any]:
    return {
        "organization_id": ORG_ID,
        "principal_ref": principal_ref,
        "operation_scope": scope,
        "idempotency_key": "synthetic-key-01",
        "request_fingerprint": fingerprint or LessonLibraryService._fingerprint(payload),
        "response_json": response,
    }


def _membership(*, revision: int = 7) -> dict[str, Any]:
    return {
        "organization_id": ORG_ID,
        "membership_id": MEMBERSHIP_ID,
        "parent_group_id": GROUP_ID,
        "parent_principal_ref": PARENT_ID,
        "revision": revision,
    }


def test_current_receipt_is_returned_unchanged_without_inferred_provenance() -> None:
    from sketch2life.contracts.schemas.lesson_library import ParentGroupInvitationV1
    from sketch2life.infrastructure.lesson_library.receipt_compat import (
        upgrade_parent_group_receipt,
    )

    current = {**LEGACY_INVITATION, "revision": 4}

    result = upgrade_parent_group_receipt(
        operation_scope=INVITE_SCOPE,
        response=current,
        membership_row=None,
    )

    assert result == current
    assert ParentGroupInvitationV1.model_validate(result).revision_source is None


@pytest.mark.parametrize(
    ("scope", "payload", "legacy", "expected_contract"),
    [
        (INVITE_SCOPE, INVITE_PAYLOAD, LEGACY_INVITATION, "ParentGroupInvitationV1"),
        (ACCEPT_SCOPE, ACCEPT_PAYLOAD, LEGACY_ACCEPTANCE, "ParentGroupMembershipV1"),
    ],
)
def test_legacy_receipt_replay_reconstructs_revision_without_writes(
    scope: str,
    payload: dict[str, Any],
    legacy: dict[str, Any],
    expected_contract: str,
) -> None:
    from sketch2life.contracts.schemas.lesson_library import (
        ParentGroupInvitationV1,
        ParentGroupMembershipV1,
    )

    receipt = _receipt(
        scope=scope,
        payload=payload,
        response=legacy,
        principal_ref=PARENT_ID if scope == ACCEPT_SCOPE else "synthetic-manager-01",
    )
    db = FakeReceiptDb(receipt, _membership())

    result = _service(db)._replay(
        organization_id=ORG_ID,
        actor=receipt["principal_ref"],
        scope=scope,
        key=receipt["idempotency_key"],
        payload=payload,
    )

    assert result is not None
    assert result["contract"] == expected_contract
    assert result["revision"] == 7
    assert result["revision_source"] == "reconstructed_from_current_row"
    model = ParentGroupInvitationV1 if scope == INVITE_SCOPE else ParentGroupMembershipV1
    assert model.model_validate(result).revision_source == "reconstructed_from_current_row"
    assert len(db.statements) == 2
    assert all(statement.is_select for statement in db.statements)
    assert (db.add_calls, db.flush_calls, db.commit_calls) == (0, 0, 0)


def test_legacy_receipt_without_current_membership_is_typed_failure() -> None:
    receipt = _receipt()
    db = FakeReceiptDb(receipt, None)

    with pytest.raises(LessonLibraryError) as exc_info:
        _service(db)._replay(
            organization_id=ORG_ID,
            actor=receipt["principal_ref"],
            scope=INVITE_SCOPE,
            key=receipt["idempotency_key"],
            payload=INVITE_PAYLOAD,
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "IDEMPOTENCY_RECEIPT_INCOMPATIBLE"


def test_reused_key_with_different_fingerprint_stays_409() -> None:
    receipt = _receipt(fingerprint="0" * 64)
    db = FakeReceiptDb(receipt, _membership())

    with pytest.raises(LessonLibraryError) as exc_info:
        _service(db)._replay(
            organization_id=ORG_ID,
            actor=receipt["principal_ref"],
            scope=INVITE_SCOPE,
            key=receipt["idempotency_key"],
            payload=INVITE_PAYLOAD,
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "IDEMPOTENCY_KEY_REUSED"
    assert len(db.statements) == 1


def test_malformed_receipt_response_is_typed_failure() -> None:
    receipt = _receipt(response=["not", "an", "object"])
    db = FakeReceiptDb(receipt, None)

    with pytest.raises(LessonLibraryError) as exc_info:
        _service(db)._replay(
            organization_id=ORG_ID,
            actor=receipt["principal_ref"],
            scope=INVITE_SCOPE,
            key=receipt["idempotency_key"],
            payload=INVITE_PAYLOAD,
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "IDEMPOTENCY_RECEIPT_INCOMPATIBLE"


@pytest.mark.parametrize(
    ("organization_id", "principal_ref", "scope"),
    [
        (
            "synthetic-other-org-01",
            "synthetic-manager-01",
            "POST /organizations/synthetic-other-org-01/parent-groups/"
            "synthetic-group-01/invitations",
        ),
        (ORG_ID, "synthetic-other-principal-01", INVITE_SCOPE),
    ],
)
def test_receipt_from_another_organization_or_principal_is_not_visible(
    organization_id: str,
    principal_ref: str,
    scope: str,
) -> None:
    receipt = _receipt()
    db = FakeReceiptDb(receipt, _membership())

    result = _service(db)._replay(
        organization_id=organization_id,
        actor=principal_ref,
        scope=scope,
        key=receipt["idempotency_key"],
        payload=INVITE_PAYLOAD,
    )

    assert result is None
    assert len(db.statements) == 1
