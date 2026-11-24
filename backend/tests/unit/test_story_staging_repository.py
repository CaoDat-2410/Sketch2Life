"""FEAT-087 M4: staging is stored hidden inside ``story_revisions.story_content`` (no migration)."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import ParentStoryRevisionReservation
from sketch2life.application.story_staging import STAGING_SCHEMA
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
)

_PRINCIPAL = VerifiedPrincipal("parent-1", "issuer-1", frozenset({"parent"}))
_RUN_ID = "22222222-2222-4222-8222-222222222222"
_STORY_REVISION = "44444444-4444-4444-8444-444444444444"


class _Session:
    def __init__(self) -> None:
        self.statements: list[Any] = []

    def scalar(self, _statement: Any) -> str:
        return _STORY_REVISION

    def execute(self, statement: Any, *_a: Any, **_k: Any) -> Any:
        self.statements.append(statement)
        return SimpleNamespace(rowcount=1)

    def commit(self) -> None: ...

    def rollback(self) -> None:  # pragma: no cover
        raise AssertionError("unexpected rollback")


def _story() -> dict[str, Any]:
    return {
        "language": "vi",
        "title": "Rùa và chiếc lá",
        "duration_ms": 30000,
        "story": {"opening": "a", "middle": "b", "ending": "c"},
        "scenes": [],
    }


def _complete(monkeypatch: pytest.MonkeyPatch, **staging: Any) -> dict[str, Any]:
    session = _Session()
    repository = SqlParentStoryRunRepository(session)  # type: ignore[arg-type]
    monkeypatch.setattr(
        repository, "_owned_run", lambda *_a, **_k: {"run_state": "STORY_GENERATING", "version": 3}
    )
    monkeypatch.setattr(repository, "get_run", lambda *_a, **_k: "view")
    reservation = ParentStoryRevisionReservation(
        run_id=_RUN_ID,
        story_revision_id=_STORY_REVISION,
        revision_no=1,
        understanding_revision=1,
        context_revision=1,
        source_asset_sha256="a" * 64,
        worker_input={},
        request_sha256="b" * 64,
        receipt_id="55555555-5555-4555-8555-555555555555",
    )
    repository.complete_story_revision(
        principal=_PRINCIPAL,
        reservation=reservation,
        story=_story(),
        story_sha256="c" * 64,
        provider_call_id="fc-1",
        model_id="m",
        model_revision="r",
        **staging,
    )
    update = next(s for s in session.statements if s.table.name == "story_revisions")
    return update.compile().params["story_content"]


def test_staging_is_saved_beside_the_three_visible_sections(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    staging = {"schema_version": STAGING_SCHEMA, "scenes": []}
    content = _complete(monkeypatch, staging=staging, staging_issue=None)
    assert content == {"opening": "a", "middle": "b", "ending": "c", "staging": staging}


def test_a_dropped_staging_records_only_the_reason_code(monkeypatch: pytest.MonkeyPatch) -> None:
    content = _complete(monkeypatch, staging=None, staging_issue="STAGING_FIELD_INVALID")
    assert content == {
        "opening": "a",
        "middle": "b",
        "ending": "c",
        "staging_issue": "STAGING_FIELD_INVALID",
    }


def test_without_staging_arguments_the_row_is_exactly_what_it_was_before(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert _complete(monkeypatch) == {"opening": "a", "middle": "b", "ending": "c"}
