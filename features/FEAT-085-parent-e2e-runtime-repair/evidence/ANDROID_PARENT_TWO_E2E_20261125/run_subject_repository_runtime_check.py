"""Focused repository contract check run inside the FEAT-085 API image."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.dialects import postgresql

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_profile_lookup import (
    ParentStoryProfileReference,
)
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
    _create_run_fingerprint,
    _sha256_json,
)


class Session:
    def __init__(self) -> None:
        self.statements: list[Any] = []

    def scalar(self, _statement: Any) -> None:
        return None

    def execute(self, statement: Any) -> None:
        self.statements.append(statement)

    def commit(self) -> None:
        return None

    def rollback(self) -> None:
        return None


def main() -> None:
    parent = VerifiedPrincipal("contract-parent", "contract-issuer", frozenset({"parent"}))
    profile_id = UUID("11111111-1111-4111-8111-111111111111")
    fingerprint_args = {
        "parent_profile_id": profile_id,
        "topic": "transport",
        "adult_confirmed_idea": "",
        "lesson_version_ref": None,
    }
    legacy = _sha256_json(
        {
            "parent_profile_id": str(profile_id),
            "topic": "transport",
            "adult_confirmed_idea": "",
            "lesson_version": None,
        }
    )
    assert _create_run_fingerprint(**fingerprint_args) == legacy
    assert _create_run_fingerprint(
        **fingerprint_args, intended_drawing_subject="bicycle"
    ) != _create_run_fingerprint(**fingerprint_args, intended_drawing_subject="train")

    session = Session()
    repository = SqlParentStoryRunRepository(session)  # type: ignore[arg-type]
    repository._lock_idempotency = lambda **_kwargs: None  # type: ignore[method-assign]
    repository._find_idempotency_receipt = lambda **_kwargs: None  # type: ignore[method-assign]
    repository._store_idempotency_receipt = lambda **_kwargs: "receipt"  # type: ignore[method-assign]
    repository.get_run = lambda **_kwargs: None  # type: ignore[method-assign]
    repository.create_run(
        principal=parent,
        account_id="synthetic-account",
        profile=ParentStoryProfileReference(
            profile_id=profile_id,
            profile_revision_id=UUID("33333333-3333-4333-8333-333333333333"),
            state="ACTIVE",
            data_origin="SYNTHETIC_DEV",
            age_months=60,
            interests_summary=None,
        ),
        idempotency_key="runtime-contract-check",
        run_id="22222222-2222-4222-8222-222222222222",
        topic="transport",
        adult_confirmed_idea="",
        intended_drawing_subject="bicycle",
    )
    inputs_insert = next(
        statement
        for statement in session.statements
        if getattr(getattr(statement, "table", None), "name", None) == "story_run_inputs"
        or getattr(getattr(statement, "table", None), "name", None) == "run_inputs"
    )
    parameters = dict(inputs_insert.compile(dialect=postgresql.dialect()).params)
    assert parameters["context_snapshot"]["intended_drawing_subject"] == "bicycle"

    replay_session = Session()
    replay_repository = SqlParentStoryRunRepository(replay_session)  # type: ignore[arg-type]
    replay_repository._lock_idempotency = lambda **_kwargs: None  # type: ignore[method-assign]
    captured: dict[str, Any] = {}

    def find_receipt(**kwargs: Any) -> None:
        captured.update(kwargs)
        return None

    replay_repository._find_idempotency_receipt = find_receipt  # type: ignore[method-assign]
    assert replay_repository.replay_create_run(
        principal=parent,
        account_id="synthetic-account",
        parent_profile_id=profile_id,
        idempotency_key="runtime-contract-check",
        topic="transport",
        adult_confirmed_idea="",
        intended_drawing_subject="bicycle",
    ) is None
    assert captured["fingerprint"] == _create_run_fingerprint(
        **fingerprint_args, intended_drawing_subject="bicycle"
    )
    print("RUN_SUBJECT_CREATE_REPLAY_CONTEXT_FINGERPRINT_PASS")


if __name__ == "__main__":
    main()
