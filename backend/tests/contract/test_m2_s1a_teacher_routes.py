from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

import pytest
from fastapi import HTTPException, Response
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
    # FEAT-066 M9-B (O-3b): the command takes only the opaque candidate ref, never a subject.
    assignment = CreateAssignmentRequest(candidate_ref="synthetic-candidate")
    assert assignment.model_dump() == {"candidate_ref": "synthetic-candidate"}
    with pytest.raises(ValidationError):
        CreateAssignmentRequest(subject="synthetic-teacher")  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        CreateAssignmentRequest(  # type: ignore[call-arg]
            candidate_ref="synthetic-candidate",
            role="teacher",
            class_id="synthetic-class",
        )

    # T-7c: the class is the path only; `consent_id` is the one optional reference field.
    profile = CreateProfileRequest(display_name="Synthetic learner", age_months=120)
    assert profile.model_dump() == {
        "display_name": "Synthetic learner",
        "age_months": 120,
        "consent_id": None,
    }
    assert CreateProfileRequest(
        display_name="Synthetic learner", age_months=36, consent_id="synthetic-consent"
    ).consent_id == "synthetic-consent"
    with pytest.raises(ValidationError):
        CreateProfileRequest(display_name="Synthetic learner", age_months=121)
    with pytest.raises(ValidationError):
        CreateProfileRequest(
            child_id="synthetic-client-id",  # type: ignore[call-arg]
            purpose_ref="synthetic-purpose",
            display_name="Synthetic learner",
            age_months=60,
        )
    with pytest.raises(ValidationError):
        CreateProfileRequest(  # type: ignore[call-arg]
            class_id="synthetic-class",
            display_name="Synthetic learner",
            age_months=60,
        )
    with pytest.raises(ValidationError):
        CreateProfileRequest(display_name="Learner", age_months=60)


def test_class_lock_select_takes_for_update() -> None:
    """FEAT-066 M9-B (review R2-05): the class row is locked before the count and the insert."""
    statement = be1_registry.class_lock_select("synthetic-class")
    sql = str(statement.compile(dialect=postgresql.dialect()))
    assert "FOR UPDATE" in sql
    assert "be1_classrooms" in sql


def test_candidate_lock_select_is_one_statement_with_eligibility_for_share() -> None:
    """The candidate is read and locked FOR SHARE in the same statement as its eligibility."""
    statement = be1_registry.candidate_lock_select("synthetic-org", "synthetic-candidate")
    sql = str(statement.compile(dialect=postgresql.dialect()))
    assert "FOR SHARE OF be1_adult_identities" in sql
    assert "EXISTS" in sql
    assert "account_role" in sql and "state" in sql


def test_class_assignment_revision_grows_with_teacher_rows() -> None:
    assert be1_registry.class_assignment_revision(0) == 1
    assert be1_registry.class_assignment_revision(3) == 4


def test_missing_class_assignment_uses_generic_scope_denial(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _NoClassSession:
        def scalar(self, _statement: object) -> object:
            return None

    monkeypatch.setattr(
        be1_registry,
        "require_assignment",
        lambda *_args, **_kwargs: pytest.fail("missing class must be denied first"),
    )

    with pytest.raises(HTTPException) as error:
        be1_registry.assign_class_teacher(
            "synthetic-missing-class",
            CreateAssignmentRequest(candidate_ref="synthetic-candidate"),
            cast(Any, SimpleNamespace()),  # T0.1: the request
            Response(),
            "synthetic-key",
            '"1"',
            _principal(),
            cast(be1_registry.Session, _NoClassSession()),
        )

    assert error.value.status_code == 404
    assert error.value.detail == {
        "code": "RESOURCE_NOT_FOUND",
        "message": "The requested resource was not found",
    }


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
        SimpleNamespace(
            settings=SimpleNamespace(
                env="test", synthetic_pilot_enabled=True, real_profile_data_enabled=False
            )
        ),
    )

    with pytest.raises(HTTPException) as error:
        be1_registry.create_profile(
            "synthetic-org",
            "synthetic-class",
            CreateProfileRequest(display_name="Synthetic learner", age_months=60),
            cast(Any, SimpleNamespace()),  # T-7c: the request (never reached)
            Response(),
            "synthetic-key",
            '"1"',
            _principal("synthetic-teacher"),
            runtime=runtime,
            db=cast(be1_registry.Session, db),
        )

    assert error.value.status_code == 404
    assert error.value.detail == {
        "code": "RESOURCE_NOT_FOUND",
        "message": "The requested resource was not found",
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
        SimpleNamespace(
            settings=SimpleNamespace(
                env="test", synthetic_pilot_enabled=True, real_profile_data_enabled=False
            )
        ),
    )
    with pytest.raises(HTTPException) as error:
        be1_registry.create_profile(
            organization_id,
            "synthetic-class",
            CreateProfileRequest(display_name="Synthetic learner", age_months=60),
            cast(Any, SimpleNamespace()),  # T-7c: the request (never reached)
            Response(),
            "synthetic-key",
            '"1"',
            _principal("synthetic-teacher"),
            runtime=runtime,
            db=cast(be1_registry.Session, FakeSession()),
        )

    assert error.value.status_code == 404
    assert error.value.detail == {
        "code": "RESOURCE_NOT_FOUND",
        "message": "The requested resource was not found",
    }
