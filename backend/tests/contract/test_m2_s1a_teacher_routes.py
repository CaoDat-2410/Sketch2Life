from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.dialects import postgresql

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.contracts.schemas.be1_runtime import (
    CreateAssignmentRequest,
    CreateProfileRequest,
)
from sketch2life.interfaces.http.routers import be1_registry


def _principal(subject: str = "synthetic-school-manager") -> VerifiedPrincipal:
    return VerifiedPrincipal(
        subject=subject,
        issuer="synthetic-test-issuer",
        roles=frozenset(),
        token_id="synthetic-token",
    )


def test_teacher_requests_do_not_accept_client_identity_or_consent_fields() -> None:
    assignment = CreateAssignmentRequest(subject="synthetic-teacher")
    assert assignment.model_dump() == {"subject": "synthetic-teacher"}
    with pytest.raises(ValidationError):
        CreateAssignmentRequest(
            subject="synthetic-teacher",
            role="teacher",
            class_id="synthetic-class",
        )

    profile = CreateProfileRequest(
        class_id="synthetic-class",
        display_name="Synthetic learner",
        age_months=120,
    )
    assert profile.model_dump() == {
        "class_id": "synthetic-class",
        "display_name": "Synthetic learner",
        "age_months": 120,
    }
    with pytest.raises(ValidationError):
        CreateProfileRequest(
            class_id="synthetic-class",
            display_name="Synthetic learner",
            age_months=121,
        )
    with pytest.raises(ValidationError):
        CreateProfileRequest(
            child_id="synthetic-client-id",
            consent_id="synthetic-consent",
            purpose_ref="synthetic-purpose",
            class_id="synthetic-class",
            display_name="Synthetic learner",
            age_months=60,
        )
    with pytest.raises(ValidationError):
        CreateProfileRequest(
            class_id="synthetic-class",
            display_name="Learner",
            age_months=60,
        )


class _AssignmentSession:
    def __init__(self, classroom: object, teacher_count: int) -> None:
        self.values = [classroom, teacher_count]
        self.statements: list[object] = []
        self.added: list[object] = []

    def scalar(self, statement: object) -> object:
        self.statements.append(statement)
        return self.values.pop(0)

    def get(self, _model: object, _key: str) -> object:
        return SimpleNamespace(issuer="synthetic-test-issuer")

    def add(self, row: object) -> None:
        self.added.append(row)

    def flush(self) -> None:
        return None


def test_class_teacher_assignment_locks_class_before_count_and_create(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    classroom = SimpleNamespace(class_id="synthetic-class", organization_id="synthetic-org")
    db = _AssignmentSession(classroom, 0)
    manager_assignment = SimpleNamespace(class_id=None, role="school_admin")
    monkeypatch.setattr(
        be1_registry,
        "require_assignment",
        lambda *_args, **_kwargs: (manager_assignment,),
    )
    monkeypatch.setattr(be1_registry, "audit", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(be1_registry, "event", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(be1_registry, "commit", lambda *_args, **_kwargs: None)

    response = be1_registry.assign_class_teacher(
        "synthetic-class",
        CreateAssignmentRequest(subject="synthetic-teacher"),
        _principal(),
        cast(be1_registry.Session, db),
    )

    statement_sql = str(db.statements[0].compile(dialect=postgresql.dialect()))
    assert "FOR UPDATE" in statement_sql
    assert response["role"] == "teacher"
    assert response["class_id"] == "synthetic-class"
    assert len(db.added) == 1
    added_row = cast(SimpleNamespace, db.added[0])
    assert added_row.organization_id == "synthetic-org"


def test_second_active_class_teacher_is_rejected_without_identity_disclosure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    classroom = SimpleNamespace(class_id="synthetic-class", organization_id="synthetic-org")
    db = _AssignmentSession(classroom, 1)
    manager_assignment = SimpleNamespace(class_id=None, role="school_admin")
    monkeypatch.setattr(
        be1_registry,
        "require_assignment",
        lambda *_args, **_kwargs: (manager_assignment,),
    )

    with pytest.raises(HTTPException) as error:
        be1_registry.assign_class_teacher(
            "synthetic-class",
            CreateAssignmentRequest(subject="synthetic-second-teacher"),
            _principal(),
            cast(be1_registry.Session, db),
        )

    assert error.value.status_code == 409
    assert error.value.detail == {
        "code": "CLASS_TEACHER_EXISTS",
        "message": "Class already has an active Teacher",
    }
    assert "synthetic-second-teacher" not in str(error.value.detail)
    assert db.added == []


def test_missing_class_assignment_uses_generic_scope_denial(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = _AssignmentSession(None, 0)
    monkeypatch.setattr(
        be1_registry,
        "require_assignment",
        lambda *_args, **_kwargs: pytest.fail("missing class must be denied first"),
    )

    with pytest.raises(HTTPException) as error:
        be1_registry.assign_class_teacher(
            "synthetic-missing-class",
            CreateAssignmentRequest(subject="synthetic-teacher"),
            _principal(),
            cast(be1_registry.Session, db),
        )

    assert error.value.status_code == 403
    assert error.value.detail == {
        "code": "SCOPE_DENIED",
        "message": "Access to this resource is not permitted",
    }
    assert db.added == []


def test_profile_requires_exact_class_teacher_assignment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeSession:
        def __init__(self) -> None:
            self.added: list[object] = []

        def scalar(self, _statement: object) -> object:
            return SimpleNamespace(class_id="synthetic-class")

        def add_all(self, rows: list[object]) -> None:
            self.added.extend(rows)

    organization_assignment = SimpleNamespace(class_id=None, role="teacher")
    monkeypatch.setattr(
        be1_registry,
        "require_assignment",
        lambda *_args, **_kwargs: (organization_assignment,),
    )
    db = FakeSession()
    runtime = cast(
        be1_registry.Be1Runtime,
        SimpleNamespace(settings=SimpleNamespace(env="test", synthetic_pilot_enabled=True)),
    )

    with pytest.raises(HTTPException) as error:
        be1_registry.create_profile(
            "synthetic-org",
            "synthetic-class",
            CreateProfileRequest(
                class_id="synthetic-class",
                display_name="Synthetic learner",
                age_months=60,
            ),
            _principal("synthetic-teacher"),
            runtime=runtime,
            db=cast(be1_registry.Session, db),
        )

    assert error.value.status_code == 403
    assert error.value.detail == {
        "code": "SCOPE_DENIED",
        "message": "Access to this resource is not permitted",
    }
    assert db.added == []


@pytest.mark.parametrize(
    ("organization_id", "classroom"),
    (
        ("synthetic-org", None),
        (
            "synthetic-other-org",
            SimpleNamespace(class_id="synthetic-class", organization_id="synthetic-org"),
        ),
    ),
)
def test_missing_or_wrong_class_scope_uses_generic_denial(
    monkeypatch: pytest.MonkeyPatch,
    organization_id: str,
    classroom: SimpleNamespace | None,
) -> None:
    class FakeSession:
        def scalar(self, _statement: object) -> object | None:
            if classroom is None or classroom.organization_id != organization_id:
                return None
            return classroom

    def unexpected_assignment_lookup(*_args: object, **_kwargs: object) -> tuple[object, ...]:
        pytest.fail("a missing class must be denied before assignment lookup")

    monkeypatch.setattr(be1_registry, "require_assignment", unexpected_assignment_lookup)
    runtime = cast(
        be1_registry.Be1Runtime,
        SimpleNamespace(settings=SimpleNamespace(env="test", synthetic_pilot_enabled=True)),
    )
    with pytest.raises(HTTPException) as error:
        be1_registry.create_profile(
            organization_id,
            "synthetic-class",
            CreateProfileRequest(
                class_id="synthetic-class",
                display_name="Synthetic learner",
                age_months=60,
            ),
            _principal("synthetic-teacher"),
            runtime=runtime,
            db=cast(be1_registry.Session, FakeSession()),
        )

    assert error.value.status_code == 403
    assert error.value.detail == {
        "code": "SCOPE_DENIED",
        "message": "Access to this resource is not permitted",
    }
