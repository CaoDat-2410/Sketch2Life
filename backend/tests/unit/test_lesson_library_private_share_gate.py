"""Offline guard for T-10d: only a PUBLIC lesson needs an approved version (FR-PL-05, BR-51).

A private share (school, named Parent, Parent group) must not read ``review_state`` on the write
side, and the Parent read statements must attach the ``APPROVED`` condition to the PUBLIC branch
only. The checks inspect the statement objects built per branch, not SQL text.
"""

from __future__ import annotations

from typing import Any, cast

import pytest
from sqlalchemy.sql import operators
from sqlalchemy.sql.elements import BinaryExpression, BindParameter
from sqlalchemy.sql.visitors import iterate

from sketch2life.infrastructure.lesson_library.service import (
    LessonLibraryError,
    LessonLibraryService,
)
from sketch2life.infrastructure.lesson_library.tables import ACCESS_GRANTS, LIBRARY_VERSIONS

ORG_ID = "synthetic-org-01"
TEACHER = "synthetic-teacher-01"
PARENT = "synthetic-parent-01"
LESSON_ID = "synthetic-lesson-01"
VERSION_ID = "synthetic-version-01"


class _RecordingMapping(dict[str, Any]):
    """A row mapping that records every key read."""

    def __init__(self, values: dict[str, Any]) -> None:
        super().__init__(values)
        self.reads: list[str] = []

    def __getitem__(self, key: str) -> Any:
        self.reads.append(key)
        return super().__getitem__(key)

    def get(self, key: str, default: Any = None) -> Any:
        self.reads.append(key)
        return super().get(key, default)


class _FakeResult:
    def __init__(self, row: _RecordingMapping) -> None:
        self._row = row

    def mappings(self) -> _FakeResult:
        return self

    def one_or_none(self) -> _RecordingMapping:
        return self._row


class _FakeDb:
    def __init__(self, row: _RecordingMapping) -> None:
        self._row = row

    def execute(self, *_args: Any, **_kwargs: Any) -> _FakeResult:
        return _FakeResult(self._row)


def _service_with_version(review_state: str) -> tuple[LessonLibraryService, _RecordingMapping]:
    version = _RecordingMapping(
        {"version_id": VERSION_ID, "lesson_id": LESSON_ID, "review_state": review_state}
    )
    service = object.__new__(LessonLibraryService)
    service.db = cast(Any, _FakeDb(version))
    service._load_lesson = lambda *_a, **_k: {  # type: ignore[method-assign]
        "created_by": TEACHER,
        "state": "ACTIVE",
    }
    service._load_group = lambda *_a, **_k: {"state": "active"}  # type: ignore[method-assign]
    service._idempotent = lambda **_k: {"state": "OK"}  # type: ignore[method-assign]
    return service, version


def _create(service: LessonLibraryService, kind: str, ref: str | None) -> dict[str, Any]:
    return service.create_access_grant(
        organization_id=ORG_ID,
        lesson_id=LESSON_ID,
        actor=TEACHER,
        version_id=VERSION_ID,
        audience_kind=kind,
        audience_ref=ref,
        capability="VIEW",
        expires_at=None,
        idempotency_key="synthetic-key",
    )


REVIEW_STATES = ["DRAFT", "PENDING_REVIEW", "CHANGES_REQUESTED", "APPROVED"]


@pytest.mark.parametrize("review_state", REVIEW_STATES)
@pytest.mark.parametrize(
    ("kind", "ref"),
    [("ORGANIZATION", ORG_ID), ("PRINCIPAL", PARENT), ("PARENT_GROUP", "synthetic-group-01")],
)
def test_private_share_is_accepted_and_never_reads_the_review_state(
    kind: str, ref: str, review_state: str
) -> None:
    service, version = _service_with_version(review_state)
    assert _create(service, kind, ref) == {"state": "OK"}
    assert "review_state" not in version.reads


def test_public_share_still_goes_to_review_without_reading_the_gate() -> None:
    service, version = _service_with_version("DRAFT")
    assert _create(service, "PUBLIC", None) == {"state": "OK"}
    assert "review_state" not in version.reads


def test_other_private_share_gates_are_unchanged() -> None:
    service, _version = _service_with_version("DRAFT")
    with pytest.raises(LessonLibraryError) as to_self:
        _create(service, "PRINCIPAL", TEACHER)
    assert (to_self.value.status_code, to_self.value.code) == (422, "INVALID_REQUEST")
    with pytest.raises(LessonLibraryError) as other_org:
        _create(service, "ORGANIZATION", "synthetic-other-org")
    assert (other_org.value.status_code, other_org.value.code) == (404, "RESOURCE_NOT_FOUND")
    inactive, _ = _service_with_version("DRAFT")
    inactive._load_group = lambda *_a, **_k: {"state": "archived"}  # type: ignore[method-assign]
    with pytest.raises(LessonLibraryError) as archived_group:
        _create(inactive, "PARENT_GROUP", "synthetic-group-01")
    assert (archived_group.value.status_code, archived_group.value.code) == (
        409,
        "INVALID_TRANSITION",
    )


def _comparisons(statement: Any) -> list[BinaryExpression[Any]]:
    criteria = statement.whereclause
    assert criteria is not None
    return [node for node in iterate(criteria) if isinstance(node, BinaryExpression)]


def _requires_approved(statement: Any) -> bool:
    for node in _comparisons(statement):
        if (
            node.operator is operators.eq
            and node.left is LIBRARY_VERSIONS.c.review_state
            and isinstance(node.right, BindParameter)
            and node.right.value == "APPROVED"
        ):
            return True
    return False


def _audience_kind(statement: Any) -> str:
    for node in _comparisons(statement):
        if (
            node.operator is operators.eq
            and node.left is ACCESS_GRANTS.c.audience_kind
            and isinstance(node.right, BindParameter)
        ):
            return str(node.right.value)
    raise AssertionError("statement has no single audience_kind equality")


def test_only_the_public_parent_read_statement_requires_an_approved_version() -> None:
    service = object.__new__(LessonLibraryService)
    service._parent_audience_refs = lambda parent_ref: (parent_ref,)  # type: ignore[method-assign]
    captured: list[Any] = []

    def capture(statement: Any, _limit: int, **_kwargs: Any) -> list[dict[str, Any]]:
        captured.append(statement)
        return []

    service._rows_as_parent_access = capture  # type: ignore[method-assign,assignment]
    assert service._parent_access_rows(parent_principal_ref=PARENT, capability="VIEW") == []
    by_kind = {_audience_kind(statement): statement for statement in captured}
    assert set(by_kind) == {"PUBLIC", "PRINCIPAL", "PARENT_GROUP"}
    assert _requires_approved(by_kind["PUBLIC"])
    assert not _requires_approved(by_kind["PRINCIPAL"])
    assert not _requires_approved(by_kind["PARENT_GROUP"])

    captured.clear()
    service._parent_access_rows(
        parent_principal_ref=PARENT, capability="VIEW", source_kind="SHARED"
    )
    assert {_audience_kind(statement) for statement in captured} == {"PRINCIPAL", "PARENT_GROUP"}
    assert not any(_requires_approved(statement) for statement in captured)
