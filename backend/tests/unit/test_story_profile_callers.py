from __future__ import annotations

from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi import Response

from sketch2life.application.ports.parent_story_runs import ParentStoryRevisionReservation
from sketch2life.contracts.schemas.modal_ai import ParentStoryRequestV1
from sketch2life.infrastructure.ai.modal_function_client import (
    STORY_MODEL_ID,
    STORY_MODEL_REVISION,
)
from sketch2life.infrastructure.config.settings import Settings
from sketch2life.infrastructure.persistence.parent_story_repository import (
    parent_story_revision_worker_input,
)
from sketch2life.infrastructure.story_run_lite import composition as story_lite_composition
from sketch2life.infrastructure.story_run_lite.repository import build_story_run_lite_worker_input
from sketch2life.interfaces.http.routers import parent_ai


def _activity() -> dict[str, str]:
    return {
        "title": "Observe a garden",
        "objective": "Notice colors and shapes.",
        "materials_text": "",
        "preparation_text": "",
        "instructions_text": "Observe from a safe distance.",
        "observation_notes": "",
        "safety_notes": "Stay with an adult.",
        "activity_kind": "outdoor",
    }


def _catalog_selection() -> dict[str, object]:
    return {
        "activity_snapshot": _activity(),
        "activity_snapshot_sha256": "c" * 64,
        "lesson_id": "lesson-1",
        "version_id": "version-1",
        "content_sha256": "b" * 64,
    }


def _parent_worker_input(rewrite_instruction: str | None = None) -> dict[str, object]:
    return parent_story_revision_worker_input(
        run={"subject_label": "butterfly"},
        input_row={"original_sha256": "a" * 64, "context_revision": 3},
        context={"age_months": 60, "topic": "animals"},
        understanding_revision=2,
        idea_text="Tell a short story about looking closely.",
        visible_features=["two wings"],
        rewrite_instruction=rewrite_instruction,
        selection=_catalog_selection(),
    )


@pytest.mark.parametrize("rewrite_instruction", [None, "Add a gentle ending."])
def test_story_run_lite_dispatches_the_dev_activity_bound_contract(
    rewrite_instruction: str | None, monkeypatch
) -> None:
    monkeypatch.setenv("STORYRUN_LITE_STORY_MODE", "modal_function")
    calls: list[dict[str, object]] = []

    class _FakeClient:
        def __init__(self, **kwargs: object) -> None:
            calls.append({"constructor": kwargs})

        def generate(self, context: dict[str, object]) -> tuple[dict[str, object], str]:
            calls.append(context)
            return {"story": "A safe synthetic story."}, "fc-fake-story"

    monkeypatch.setattr(story_lite_composition, "ModalStoryFunctionClient", _FakeClient)
    client = story_lite_composition._configured_story_generator()
    worker_input = build_story_run_lite_worker_input(
        topic="animals",
        confirmed_subject="butterfly",
        understanding_revision=1,
        drawing_sha256="a" * 64,
        visible_features=["two wings"],
        child_age_months=60,
        adult_confirmed_idea="A short story about a butterfly.",
        rewrite_instruction=rewrite_instruction,
        primary_activity=_activity(),
    )

    assert client is not None
    client.generate({"worker_input": worker_input})
    assert calls[0] == {"constructor": {}}
    submitted = calls[1]["worker_input"]
    assert isinstance(submitted, dict)
    assert submitted["schema_version"] == "sketch2life.story-generation-input.v3"
    assert submitted["role"] == "PARENT"
    assert submitted["topic"] == "animals"
    assert submitted["primary_activity"] == _activity()
    assert submitted["rewrite_instruction"] == rewrite_instruction


@pytest.mark.parametrize("rewrite_instruction", [None, "Add a gentle ending."])
def test_parent_ai_dispatches_v3_and_records_the_dev_model(
    rewrite_instruction: str | None, monkeypatch
) -> None:
    settings = Settings(_env_file=None, ai_provider="modal_dev", env="local")
    worker_input = _parent_worker_input(rewrite_instruction)
    reservation = ParentStoryRevisionReservation(
        run_id="00000000-0000-4000-8000-000000000001",
        story_revision_id="00000000-0000-4000-8000-000000000002",
        revision_no=1,
        understanding_revision=2,
        context_revision=3,
        source_asset_sha256="a" * 64,
        worker_input=worker_input,
        request_sha256="d" * 64,
        receipt_id="receipt-1",
    )
    capture: dict[str, object] = {}

    class _Service:
        def reserve_story_revision(self, **kwargs):
            capture["reserve"] = kwargs
            return reservation

    class _FakeClient:
        def generate(self, context: dict[str, object]) -> tuple[dict[str, object], str]:
            submitted = context["worker_input"]
            assert isinstance(submitted, dict)
            assert submitted["schema_version"] == "sketch2life.story-generation-input.v3"
            assert submitted["role"] == "PARENT"
            assert submitted["primary_activity"] == _activity()
            capture["worker_input"] = submitted
            return {"title": "Synthetic story", "scenes": []}, "fc-fake-story"

    class _CompletedRecord:
        story_content = {"title": "Synthetic story"}
        story_sha256 = "e" * 64

    monkeypatch.setattr(parent_ai, "_require_parent", lambda *_args: None)
    monkeypatch.setattr(parent_ai, "_require_modal_dev", lambda: None)
    monkeypatch.setattr(parent_ai, "get_settings", lambda: settings)
    monkeypatch.setattr(parent_ai, "SqlParentStoryRunRepository", lambda _db: object())
    monkeypatch.setattr(parent_ai, "_story_service", lambda _db: _Service())
    monkeypatch.setattr(parent_ai, "ModalStoryFunctionClient", _FakeClient)
    monkeypatch.setattr(parent_ai, "ParentStoryRunRecord", _CompletedRecord)
    monkeypatch.setattr(parent_ai, "_story_response", lambda _record: {"run_id": "fake"})

    def _complete(_repository, **kwargs):
        capture["complete"] = kwargs
        return _CompletedRecord()

    monkeypatch.setattr(parent_ai, "complete_generated_story", _complete)
    body = parent_ai.generate_story_revision(
        UUID("00000000-0000-4000-8000-000000000001"),
        ParentStoryRequestV1(
            expected_understanding_revision=2, rewrite_instruction=rewrite_instruction
        ),
        Response(),
        "idempotency-key",
        principal=SimpleNamespace(subject="parent"),
        db=object(),
    )

    reserve_kwargs = capture["reserve"]
    complete_kwargs = capture["complete"]
    assert reserve_kwargs["model_id"] == STORY_MODEL_ID
    assert reserve_kwargs["model_revision"] == STORY_MODEL_REVISION
    assert complete_kwargs["model_id"] == STORY_MODEL_ID
    assert complete_kwargs["model_revision"] == STORY_MODEL_REVISION
    assert capture["worker_input"]["rewrite_instruction"] == rewrite_instruction
    assert body["model"] == {"id": STORY_MODEL_ID, "revision": STORY_MODEL_REVISION}
