from __future__ import annotations

import json
from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException, Response
from sqlalchemy.exc import IntegrityError
from starlette.requests import Request

from sketch2life.application.ports.identity import IdentityAccountProfile, VerifiedPrincipal
from sketch2life.contracts.schemas.be1_runtime import CreateAssignmentRequest
from sketch2life.infrastructure.identity.identity_labels import masked_email
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    Be1CommandReceiptModel,
    Be1TeacherAssignmentTransferModel,
    ClassroomModel,
    OrganizationAssignmentModel,
)
from sketch2life.infrastructure.persistence.core_models import CoreAggregateRevisionModel
from sketch2life.interfaces.http.routers import be1_registry

_ORG = "candidate-test-org"
_CLASS = "candidate-test-class"
_MANAGER = "candidate-test-manager"
_ISSUER = "candidate-test-issuer"
_CANDIDATE = "candidate-test-teacher"
_ASSIGNMENT_ID = "11111111-1111-4111-8111-111111111111"
_PRINCIPAL = VerifiedPrincipal(subject=_MANAGER, issuer=_ISSUER, roles=frozenset())


class _Rows:
    def __init__(self, rows: list[Any]) -> None:
        self.rows = rows

    def all(self) -> list[Any]:
        return self.rows

    def __iter__(self) -> Iterator[Any]:
        return iter(self.rows)


class _FakeSession:
    def __init__(
        self,
        *,
        existing_assignment: Any = None,
        active_teacher_count: int = 0,
        candidate_rows: list[Any] | None = None,
        current_subjects: set[str] | None = None,
        flush_error: Exception | None = None,
    ) -> None:
        self.identity = AdultIdentityModel(
            subject=_MANAGER,
            issuer=_ISSUER,
            state="active",
            account_role="school_manager",
        )
        self.manager_assignment = SimpleNamespace(
            organization_id=_ORG,
            subject=_MANAGER,
            class_id=None,
            role="school_admin",
            active=True,
            assignment_id="manager-assignment",
        )
        self.classroom = SimpleNamespace(
            class_id=_CLASS,
            organization_id=_ORG,
            state="active",
            transfer_pending=False,
            revision=9,
            assignment_revision=4,
        )
        self.candidate = SimpleNamespace(subject=_CANDIDATE, account_id="candidate-ref")
        self.existing_assignment = existing_assignment
        self.active_teacher_count = active_teacher_count
        self.candidate_rows = candidate_rows or []
        self.current_subjects = current_subjects or set()
        self.flush_error = flush_error
        self.receipts: dict[tuple[str, str, str], Any] = {}
        self.added: list[Any] = []
        self.commits = 0
        self.rollbacks = 0

    def get(self, model: object, key: object) -> Any:
        if model is AdultIdentityModel and key == _MANAGER:
            return self.identity
        if model is Be1CommandReceiptModel:
            return self.receipts.get(key)  # type: ignore[arg-type]
        if model is CoreAggregateRevisionModel:
            return None
        return None

    def scalar(self, statement: Any) -> Any:
        description = statement.column_descriptions[0]
        entity = description["entity"]
        if entity is ClassroomModel:
            params = list(statement.compile().params.values())
            if self.classroom.class_id not in params:
                return None
            if self.classroom.organization_id not in params and description["name"] == "class_id":
                return None
            return self.classroom.class_id if description["name"] == "class_id" else self.classroom
        if entity is Be1TeacherAssignmentTransferModel:
            return None
        if entity is AdultIdentityModel:
            return self.candidate
        if entity is OrganizationAssignmentModel:
            return self.existing_assignment
        return None

    def scalars(self, statement: Any) -> _Rows:
        description = statement.column_descriptions[0]
        entity = description["entity"]
        if entity is AdultIdentityModel:
            return _Rows(self.candidate_rows)
        if entity is OrganizationAssignmentModel:
            if description["name"] == "subject":
                return _Rows(sorted(self.current_subjects))
            return _Rows([self.manager_assignment])
        return _Rows([])

    def execute(self, _statement: Any) -> _Rows:
        return _Rows([(_CLASS, 1, self.active_teacher_count)])

    def add(self, instance: Any) -> None:
        self.added.append(instance)
        if isinstance(instance, Be1CommandReceiptModel):
            key = (instance.principal_ref, instance.operation_scope, instance.idempotency_key)
            self.receipts[key] = instance

    def flush(self) -> None:
        if self.flush_error is not None:
            raise self.flush_error

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


def _request_with_key(key: str) -> Request:
    path = f"/api/be1/v1/classes/{_CLASS}/assignments"
    return Request(
        {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": path,
            "raw_path": path.encode("ascii"),
            "query_string": b"",
            "headers": [(b"idempotency-key", key.encode("ascii"))],
            "client": ("testclient", 123),
            "server": ("testserver", 80),
        }
    )


def _assign(
    session: _FakeSession,
    *,
    key: str,
    runtime: Any = None,
) -> dict[str, object]:
    return be1_registry.assign_class_teacher(
        _CLASS,
        CreateAssignmentRequest(candidate_ref="candidate-ref"),
        request=_request_with_key(key),
        response=Response(),
        idempotency_key=key,
        if_match='"4"',
        principal=_PRINCIPAL,
        db=session,
        runtime=runtime,
    )


def _candidate_request(provisioner: Any) -> Request:
    app = SimpleNamespace(state=SimpleNamespace(identity_account_provisioner=provisioner))
    return Request(
        {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/api/be1/v1/organizations/candidate-test-org/teacher-candidates",
            "raw_path": b"/api/be1/v1/organizations/candidate-test-org/teacher-candidates",
            "query_string": b"",
            "headers": [],
            "client": ("testclient", 123),
            "server": ("testserver", 80),
            "app": app,
        }
    )


@pytest.mark.parametrize(
    ("email", "expected"),
    [
        ("alexander@example.test", "al***@example.test"),
        ("x@one.test", "x***@one.test"),
        (None, None),
        ("malformed-address", None),
    ],
)
def test_candidate_email_masking(email: str | None, expected: str | None) -> None:
    assert masked_email(email) == expected


def test_reactivates_inactive_assignment_and_replays_same_body() -> None:
    old_row = OrganizationAssignmentModel(
        assignment_id=_ASSIGNMENT_ID,
        organization_id=_ORG,
        subject=_CANDIDATE,
        class_id=_CLASS,
        role="teacher",
        active=False,
        pending_activation=True,
    )
    session = _FakeSession(existing_assignment=old_row)

    first = _assign(session, key="reactivate-key")

    assert first == {
        "contract": "Be1AdultAssignmentV1",
        "assignment_id": _ASSIGNMENT_ID,
        "candidate_ref": "candidate-ref",
        "role": "teacher",
        "class_id": _CLASS,
        "active": True,
        "assignment_revision": 5,
    }
    assert old_row.active is True
    assert old_row.pending_activation is False
    assert session.classroom.revision == 10
    assert session.classroom.assignment_revision == 5
    assert session.commits == 1

    audit_rows = [row for row in session.added if getattr(row, "resource_type", None)]
    event_rows = [row for row in session.added if getattr(row, "event_type", None)]
    assert len(audit_rows) == len(event_rows) == 1
    assert audit_rows[0].resource_id == _ASSIGNMENT_ID
    assert event_rows[0].payload["assignment_id"] == _ASSIGNMENT_ID

    replay = _assign(session, key="reactivate-key")
    assert replay == first
    assert session.classroom.revision == 10
    assert session.classroom.assignment_revision == 5
    assert session.commits == 1


def test_active_assignment_still_conflicts(monkeypatch: pytest.MonkeyPatch) -> None:
    active_row = OrganizationAssignmentModel(
        assignment_id=_ASSIGNMENT_ID,
        organization_id=_ORG,
        subject=_CANDIDATE,
        class_id=_CLASS,
        role="teacher",
        active=True,
    )
    session = _FakeSession(existing_assignment=active_row, active_teacher_count=1)
    runtime = SimpleNamespace(settings=SimpleNamespace(profile_receipt_hmac_key=None))
    monkeypatch.setattr(
        be1_registry, "_transfer_fingerprint", lambda *_args, **_kwargs: "fingerprint"
    )

    def conflict(*_args: Any, **_kwargs: Any) -> Any:
        raise be1_registry.failure(409, "RESOURCE_CONFLICT", "conflict")

    monkeypatch.setattr(be1_registry, "_execute_transfer", conflict)
    with pytest.raises(HTTPException) as caught:
        _assign(session, key="active-key", runtime=runtime)

    assert caught.value.status_code == 409
    assert caught.value.detail["code"] == "RESOURCE_CONFLICT"
    assert session.classroom.revision == 9
    assert session.classroom.assignment_revision == 4


def test_flush_integrity_race_still_answers_409() -> None:
    inactive_row = OrganizationAssignmentModel(
        assignment_id=_ASSIGNMENT_ID,
        organization_id=_ORG,
        subject=_CANDIDATE,
        class_id=_CLASS,
        role="teacher",
        active=False,
    )
    session = _FakeSession(
        existing_assignment=inactive_row,
        flush_error=IntegrityError("UPDATE", {}, RuntimeError("unique race")),
    )

    with pytest.raises(HTTPException) as caught:
        _assign(session, key="race-key")

    assert caught.value.status_code == 409
    assert caught.value.detail["code"] == "RESOURCE_CONFLICT"
    assert session.rollbacks == 1


def test_candidate_fields_current_state_and_email_privacy(caplog: pytest.LogCaptureFixture) -> None:
    candidate_rows = [
        SimpleNamespace(account_id=f"ref-{index}", subject=f"subject-{index}")
        for index in range(4)
    ]
    raw_emails = [
        "alexander@example.test",
        "x@one.test",
        None,
        "malformed-address",
    ]
    profiles = {
        f"subject-{index}": IdentityAccountProfile(
            subject=f"subject-{index}", email=email, display_name=f"Teacher {index}"
        )
        for index, email in enumerate(raw_emails)
    }
    provisioner = SimpleNamespace(
        get_account_profiles=lambda subjects: {subject: profiles[subject] for subject in subjects}
    )
    request = _candidate_request(provisioner)
    session = _FakeSession(
        candidate_rows=candidate_rows,
        current_subjects={"subject-0"},
    )

    without_class = be1_registry.list_teacher_candidates(
        _ORG,
        request,
        limit=25,
        cursor=None,
        class_id=None,
        principal=_PRINCIPAL,
        db=session,
    )
    with_class = be1_registry.list_teacher_candidates(
        _ORG,
        request,
        limit=25,
        cursor=None,
        class_id=_CLASS,
        principal=_PRINCIPAL,
        db=session,
    )

    assert without_class["contract"] == with_class["contract"] == "Be1TeacherCandidatePageV1"
    assert all(item["is_current"] is False for item in without_class["items"])
    assert [item["is_current"] for item in with_class["items"]] == [True, False, False, False]
    assert [item["email_masked"] for item in with_class["items"]] == [
        "al***@example.test",
        "x***@one.test",
        None,
        None,
    ]
    assert all(
        set(item) == {"candidate_ref", "display_name", "email_masked", "is_current"}
        for item in with_class["items"]
    )
    encoded = json.dumps(with_class)
    for email in raw_emails:
        if email is not None:
            assert email not in encoded
            assert email not in caplog.text


def test_candidate_foreign_class_id_uses_scope_404() -> None:
    provisioner = SimpleNamespace(get_account_profiles=lambda _subjects: {})
    session = _FakeSession()

    with pytest.raises(HTTPException) as caught:
        be1_registry.list_teacher_candidates(
            _ORG,
            _candidate_request(provisioner),
            limit=25,
            cursor=None,
            class_id="foreign-class",
            principal=_PRINCIPAL,
            db=session,
        )

    assert caught.value.status_code == 404
    assert caught.value.detail == {
        "code": "RESOURCE_NOT_FOUND",
        "message": "The requested resource was not found",
    }
