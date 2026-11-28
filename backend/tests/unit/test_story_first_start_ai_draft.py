from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

import pytest

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.ai.modal_function_client import (
    _current_modal_story_worker_input,
)
from sketch2life.infrastructure.persistence.story_first_start import (
    FIRST_STORY_INPUT_SCHEMA,
    FirstStoryStarter,
)
from sketch2life.infrastructure.story_run_lite import tables as story_tables

_NOW = datetime(2026, 11, 25, 8, 30, tzinfo=UTC)
_RUN_ID = "run-ai-draft"
_PRINCIPAL = VerifiedPrincipal("parent-draft", "issuer", frozenset())
_HASH = "a" * 64


class _Result:
    def __init__(self, row: Any) -> None:
        self.row = row

    def mappings(self) -> _Result:
        return self

    def one(self) -> Any:
        return self.row

    def one_or_none(self) -> Any:
        return self.row


class _Session:
    def __init__(self, run: dict[str, Any], selection: dict[str, Any]) -> None:
        self.run = run
        self.selection = selection
        self.reads = 0
        self.writes: list[Any] = []

    def execute(self, statement: Any) -> _Result:
        self.reads += 1
        if self.reads == 1:
            return _Result(self.run)
        if self.reads == 2:
            return _Result(self.selection)
        self.writes.append(statement)
        return _Result(None)

    def scalar(self, _statement: Any) -> None:
        return None


def _sha256_json(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def test_ai_draft_selection_builds_first_story_input_and_adapts_to_current_worker() -> None:
    snapshot = {
        "schema": "sketch2life.parent-activity-suggestion.v2",
        "title": "Observe a rounded shape",
        "objective": "Notice one visible detail.",
        "materials_text": "Paper and pencils.",
        "preparation_text": "Prepare a clear space.",
        "instructions_text": "Observe the shape with an adult nearby.",
        "observation_notes": "Ask which detail stands out.",
        "safety_notes": "Stay with an adult.",
        "activity_kind": "outdoor",
        "source": "AI_GENERATED_DRAFT",
        "selected_at": _NOW.isoformat(),
    }
    selection = {
        "source_kind": "AI_DRAFT",
        "lesson_id": None,
        "version_id": None,
        "content_sha256": None,
        "activity_snapshot": snapshot,
    }
    run = {
        "run_state": "PREPARATION_REVIEW",
        "understanding_revision": 4,
        "occurrence_ref": None,
        "actor_scope_ref": "parent-scope",
        "subject_label": "rounded shapes",
        "version": 3,
        "revision": 5,
    }
    input_row = {
        "context_snapshot": {"age_months": 60},
        "original_sha256": _HASH,
        "context_revision": 2,
    }
    session = _Session(run, selection)
    starter = FirstStoryStarter(
        session,  # type: ignore[arg-type]
        enabled=True,
        probe=lambda _principal, _run, _revision: (
            {},
            input_row,
            "adult idea",
            ["round outline"],
        ),
        live_run=lambda run_id: story_tables.story_runs.c.run_id == run_id,
        sha256_json=_sha256_json,
    )

    reservation = starter.start_if_ready(_RUN_ID, _PRINCIPAL, _NOW)
    assert reservation is not None
    worker_input = reservation.worker_input
    assert worker_input["schema_version"] == FIRST_STORY_INPUT_SCHEMA
    assert worker_input["activity"] == {
        "title": "Observe a rounded shape",
        "objective": "Notice one visible detail.",
        "instructions_text": "Observe the shape with an adult nearby.",
        "safety_notes": "Stay with an adult.",
        "activity_kind": "outdoor",
        "source": "AI_DRAFT",
        "lesson_id": None,
        "version_id": None,
        "content_sha256": None,
    }
    assert reservation.request_sha256 == _sha256_json(worker_input)
    assert len(session.writes) == 2

    modal_input = _current_modal_story_worker_input(worker_input)
    assert modal_input == {
        "schema_version": "sketch2life.story-generation-input.v1",
        "role": "PARENT",
        "language": "vi",
        "confirmed_subject": "rounded shapes",
        "understanding_revision": 4,
        "drawing_sha256": _HASH,
        "visible_features": ["round outline"],
        "child_age_months": 60,
        "context_revision": 2,
        "adult_confirmed_idea": "adult idea",
        "rewrite_instruction": None,
        "lesson_direction": None,
    }
    assert "activity" not in modal_input and "context_entries" not in modal_input

    invalid_worker_input = dict(worker_input)
    invalid_worker_input["activity"] = dict(worker_input["activity"])
    invalid_worker_input["activity"]["lesson_id"] = "unexpected-lesson-id"
    with pytest.raises(ValueError, match="AI_DRAFT activities cannot have lesson references"):
        _current_modal_story_worker_input(invalid_worker_input)
