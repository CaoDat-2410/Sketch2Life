from __future__ import annotations

from typing import Any

import pytest

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
)

RUN_ID = "11111111-1111-4111-8111-111111111111"
PRINCIPAL = VerifiedPrincipal("parent-1", "issuer-1", frozenset())


class _NoSelectionResult:
    def mappings(self) -> _NoSelectionResult:
        return self

    def one_or_none(self) -> None:
        return None


class _DatabaseFreeSession:
    def __init__(self) -> None:
        self.statements: list[Any] = []

    def execute(self, statement: Any) -> _NoSelectionResult:
        self.statements.append(statement)
        return _NoSelectionResult()


def test_first_story_input_reservation_refuses_when_selection_is_not_stored(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _DatabaseFreeSession()
    repository = SqlParentStoryRunRepository(session)  # type: ignore[arg-type]
    run = {
        "run_id": RUN_ID,
        "run_state": "PREPARATION_REVIEW",
        "understanding_revision": 2,
        "version": 1,
        "revision": 1,
    }
    monkeypatch.setattr(repository, "_owned_run", lambda *_args, **_kwargs: run)
    monkeypatch.setattr(repository, "_lock_idempotency", lambda **_kwargs: None)
    monkeypatch.setattr(repository, "_find_idempotency_receipt", lambda **_kwargs: None)

    with pytest.raises(ParentStoryRunError) as refused:
        repository.reserve_story_revision(
            principal=PRINCIPAL,
            run_id=RUN_ID,
            expected_understanding_revision=2,
            rewrite_instruction=None,
            idempotency_key="synthetic-key",
            story_revision_id="synthetic-story-revision",
            model_id="synthetic-model",
            model_revision="synthetic-revision",
            prompt_version="synthetic-prompt",
            require_activity_selection=True,
        )

    assert (refused.value.status_code, refused.value.code) == (
        409,
        "PARENT_ACTIVITY_SELECTION_REQUIRED",
    )
    assert len(session.statements) == 1
