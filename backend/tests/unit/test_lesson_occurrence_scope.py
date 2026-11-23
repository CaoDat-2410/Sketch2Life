"""FEAT-066 T-3a: Teacher scope facts and the upload target resolver, with fakes (no database)."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.upload_sessions import UploadTargetNotAccepting
from sketch2life.domain.lesson_occurrences.model import AssignmentFact
from sketch2life.infrastructure.lesson_occurrences import scope, upload_target
from sketch2life.infrastructure.lesson_occurrences.scope import (
    LessonOccurrenceError,
    OccurrenceAccess,
    load_caller_facts,
)
from sketch2life.infrastructure.lesson_occurrences.upload_target import (
    OccurrenceUploadTargetResolver,
)
from sketch2life.infrastructure.uploads.purposes import OCCURRENCE_DOCUMENT
from sketch2life.interfaces.http.router_composition import mount_all_routers

ISSUER = "synthetic-issuer"
PRINCIPAL = VerifiedPrincipal(subject="subject-1", issuer=ISSUER, roles=frozenset())


class FakeDb:
    """Just enough of a ``Session``: one identity row and the assignment rows to return."""

    def __init__(self, identity: Any, rows: list[Any]) -> None:
        self._identity = identity
        self._rows = rows

    def get(self, _model: object, _key: object) -> Any:
        return self._identity

    def scalars(self, _statement: object) -> Any:
        return SimpleNamespace(all=lambda: list(self._rows))


def _identity(**overrides: Any) -> SimpleNamespace:
    values: dict[str, Any] = {
        "state": "active",
        "account_role": "teacher",
        "issuer": ISSUER,
        "account_id": "acct-1",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _row(role: str = "teacher", class_id: str | None = "class-1") -> SimpleNamespace:
    return SimpleNamespace(role=role, class_id=class_id)


def test_a_valid_teacher_gets_account_ref_and_the_rows() -> None:
    facts = load_caller_facts(FakeDb(_identity(), [_row(), _row("guide", None)]), PRINCIPAL, "org")  # type: ignore[arg-type]
    assert facts is not None and facts.account_ref == "acct-1"
    assert facts.rows == (AssignmentFact("teacher", "class-1"), AssignmentFact("guide", None))


@pytest.mark.parametrize(
    "identity",
    [
        None,
        _identity(state="disabled"),
        _identity(account_role="school_manager"),
        _identity(account_role="parent"),
        _identity(account_role=None),
        _identity(issuer="another-issuer"),
    ],
)
def test_an_identity_that_is_not_a_valid_teacher_has_no_facts(identity: Any) -> None:
    assert load_caller_facts(FakeDb(identity, [_row()]), PRINCIPAL, "org") is None  # type: ignore[arg-type]


def test_a_teacher_without_a_row_in_the_organization_has_no_facts() -> None:
    assert load_caller_facts(FakeDb(_identity(), []), PRINCIPAL, "org") is None  # type: ignore[arg-type]
    blank = VerifiedPrincipal(subject="", issuer=ISSUER, roles=frozenset())
    assert load_caller_facts(FakeDb(_identity(), [_row()]), blank, "org") is None  # type: ignore[arg-type]


def _resolver(
    monkeypatch: pytest.MonkeyPatch, outcome: object, *, class_read_only: bool = False
) -> OccurrenceUploadTargetResolver:
    def fake(
        _db: object, _principal: object, occurrence_id: str, *, write: bool = False, **_: Any
    ) -> Any:
        assert write is True, "an upload needs the write rule"
        if isinstance(outcome, Exception):
            raise outcome
        return OccurrenceAccess(occurrence=outcome, account_ref="acct-1")  # type: ignore[arg-type]

    monkeypatch.setattr(upload_target, "authorize_occurrence", fake)
    # T-7b: the class of the occurrence is read from the database; the fake answers for it.
    monkeypatch.setattr(upload_target, "class_is_read_only", lambda *_a, **_k: class_read_only)
    return OccurrenceUploadTargetResolver(object())  # type: ignore[arg-type]


def test_the_resolver_answers_the_organization_scope_for_the_responsible_teacher(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    row = {"occurrence_id": "occ-1", "organization_ref": "org-1", "state": "DRAFT"}
    resolver = _resolver(monkeypatch, row)
    found = resolver.resolve(PRINCIPAL, "occ-1")
    assert found is not None
    assert (found.owner_scope_kind, found.owner_scope_ref) == ("ORGANIZATION", None)
    assert found.organization_id == "org-1"
    assert found.object_prefix == "occurrences/org-1/occ-1/" and found.object_prefix.endswith("/")
    resolver.ensure_accepting(PRINCIPAL, "occ-1")


def test_the_resolver_refuses_out_of_scope_and_archived_targets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refused = _resolver(monkeypatch, LessonOccurrenceError(404, "RESOURCE_NOT_FOUND"))
    assert refused.resolve(PRINCIPAL, "occ-1") is None
    with pytest.raises(UploadTargetNotAccepting):
        refused.ensure_accepting(PRINCIPAL, "occ-1")
    assert refused.resolve(PRINCIPAL, "x" * 37) is None and refused.resolve(PRINCIPAL, "") is None
    archived = _resolver(
        monkeypatch, {"occurrence_id": "occ-1", "organization_ref": "o", "state": "ARCHIVED"}
    )
    assert archived.resolve(PRINCIPAL, "occ-1") is not None
    with pytest.raises(UploadTargetNotAccepting):
        archived.ensure_accepting(PRINCIPAL, "occ-1")


def test_the_resolver_accepts_no_new_upload_for_a_suspended_or_archived_class(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    row = {"occurrence_id": "occ-1", "organization_ref": "org-1", "state": "DRAFT"}
    read_only = _resolver(monkeypatch, row, class_read_only=True)
    # The scope answer stays (the Teacher may still read), only a new upload is refused (T-7b).
    assert read_only.resolve(PRINCIPAL, "occ-1") is not None
    with pytest.raises(UploadTargetNotAccepting):
        read_only.ensure_accepting(PRINCIPAL, "occ-1")


def test_scope_module_is_the_single_place_that_builds_the_refusals() -> None:
    assert scope.not_found().status_code == 404 and scope.not_found().code == "RESOURCE_NOT_FOUND"


def test_mounting_registers_the_resolver_and_keeps_a_factory_that_is_already_there() -> None:
    from fastapi import FastAPI

    sentinel = object()
    cases: tuple[tuple[Any, Any], ...] = (
        (None, OccurrenceUploadTargetResolver),
        ({OCCURRENCE_DOCUMENT: sentinel}, sentinel),
    )
    for existing, expected in cases:
        application = FastAPI()
        application.state.be1_runtime = SimpleNamespace(
            settings=SimpleNamespace(env="local", synthetic_pilot_enabled=False)
        )
        if existing is not None:
            application.state.upload_target_resolver_factories = existing
        mount_all_routers(application)
        assert application.state.upload_target_resolver_factories[OCCURRENCE_DOCUMENT] is expected
        paths = set(application.openapi()["paths"])
        assert {"/v1/lesson-occurrences", "/v1/lesson-occurrences/{occurrence_id}"} <= paths
