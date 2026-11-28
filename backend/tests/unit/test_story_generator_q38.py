from __future__ import annotations

import hashlib
import inspect
from typing import Any

import pytest

from sketch2life.application.ports.parent_story_inputs import (
    StoryGenerationFailure,
    StoryGenerationOutcomeUnknown,
)
from sketch2life.domain.ai_jobs.completion import canonical_json
from sketch2life.infrastructure.ai.modal_function_client import (
    STORY_MODEL_ID,
    STORY_MODEL_REVISION,
    ModalFunctionExecutionFailed,
    ModalFunctionOutcomeUnknown,
)
from sketch2life.infrastructure.ai.story_generator import (
    ModalStoryGenerator,
    to_dev_story_worker_input,
)
from sketch2life.infrastructure.story_inputs.modal_adapters import ModalParentStoryGenerator


def _activity() -> dict[str, str]:
    return {
        "title": "Observe a garden",
        "objective": "Notice colors and shapes.",
        "materials_text": "",
        "preparation_text": "",
        "instructions_text": "Observe with an adult.",
        "observation_notes": "",
        "safety_notes": "Stay with an adult.",
        "activity_kind": "outdoor",
    }


def _v3_input(**changes: Any) -> dict[str, Any]:
    activity = _activity()
    value: dict[str, Any] = {
        "schema_version": "sketch2life.story-generation-input.v3",
        "role": "PARENT",
        "language": "vi",
        "topic": "animals",
        "confirmed_subject": "butterfly",
        "understanding_revision": 2,
        "drawing_sha256": "a" * 64,
        "visible_features": ["two wings"],
        "child_age_months": 60,
        "context_revision": 3,
        "adult_confirmed_idea": "A short, safe story.",
        "rewrite_instruction": None,
        "lesson_subject_learning_notes": None,
        "lesson_direction": None,
        "primary_activity": activity,
        "primary_activity_sha256": hashlib.sha256(
            canonical_json(activity).encode("utf-8")
        ).hexdigest(),
    }
    value.update(changes)
    return value


def _v4_input(**changes: Any) -> dict[str, Any]:
    value: dict[str, Any] = {
        "schema_version": "sketch2life.story-generation-input.v4",
        "role": "PARENT",
        "language": "vi",
        "topic": "animals",
        "confirmed_subject": "butterfly",
        "understanding_revision": 2,
        "drawing_sha256": "a" * 64,
        "visible_features": ["two wings"],
        "child_age_months": 60,
        "context_revision": 3,
        "adult_confirmed_idea": "A short, safe story.",
        "activity": _activity(),
        "activity_selection_sha256": "b" * 64,
        "story_validator_version": "retired",
        "context_entries": [{"kind": "INTEREST", "text": "butterflies"}],
        "adult_rewrite_hint": "private suggestion",
        "rewrite_instruction": None,
        "lesson_subject_learning_notes": "Observe wing patterns.",
        "lesson_direction": None,
    }
    value.update(changes)
    return value


class _Client:
    def __init__(self, result: dict[str, Any] | None = None, error: Exception | None = None):
        self.result = result or {"title": "A safe story", "scenes": []}
        self.error = error
        self.calls: list[dict[str, object]] = []

    def generate(self, context: dict[str, object]) -> tuple[dict[str, Any], str]:
        self.calls.append(context)
        if self.error is not None:
            raise self.error
        return self.result, "fc-story-adapter-test"


def test_dev_v3_input_is_passed_through_without_profile_projection() -> None:
    worker = _v3_input()
    result = to_dev_story_worker_input(worker)
    assert result == worker
    assert result is not worker


def test_parent_v4_input_is_projected_to_dev_v3_and_rehashed() -> None:
    result = to_dev_story_worker_input(_v4_input())
    activity = result["primary_activity"]
    assert result["schema_version"] == "sketch2life.story-generation-input.v3"
    assert result["topic"] == "animals"
    assert result["primary_activity"] == _activity()
    assert result["primary_activity_sha256"] == hashlib.sha256(
        canonical_json(activity).encode("utf-8")
    ).hexdigest()
    assert "activity_selection_sha256" not in result
    assert "story_validator_version" not in result
    assert "context_entries" not in result
    assert "adult_rewrite_hint" not in result


def test_v4_adapter_uses_confirmed_subject_when_topic_is_absent() -> None:
    value = _v4_input()
    value.pop("topic")
    assert to_dev_story_worker_input(value)["topic"] == "butterfly"


def test_rewrite_v2_is_projected_only_when_it_has_the_selected_activity() -> None:
    value = _v4_input(schema_version="sketch2life.story-rewrite-input.v2")
    result = to_dev_story_worker_input(value)
    assert result["schema_version"] == "sketch2life.story-generation-input.v3"
    assert result["rewrite_instruction"] is None
    assert result["primary_activity"] == _activity()


def test_old_v1_input_is_rejected_before_any_worker_call() -> None:
    with pytest.raises(ValueError, match="schema is not supported"):
        to_dev_story_worker_input({"schema_version": "sketch2life.story-generation-input.v1"})


def test_v4_input_without_a_selected_activity_is_rejected() -> None:
    value = _v4_input()
    value.pop("activity")
    with pytest.raises(ValueError, match="no selected activity"):
        to_dev_story_worker_input(value)


def test_generator_advertises_both_product_roles() -> None:
    generator = ModalParentStoryGenerator(client=_Client())
    assert generator.supports_role("PARENT") is True
    assert generator.supports_role("TEACHER") is True


def test_teacher_input_is_mapped_to_the_worker_gate_role_at_the_adapter_boundary() -> None:
    client = _Client()
    generator = ModalParentStoryGenerator(client=client)  # type: ignore[arg-type]
    teacher_input = {**_v3_input(), "role": "TEACHER"}

    generator.generate(teacher_input)

    submitted = client.calls[0]["worker_input"]
    assert submitted["role"] == "PARENT"
    assert teacher_input["role"] == "TEACHER"


def test_parent_generator_sends_only_the_dev_worker_shape() -> None:
    client = _Client()
    result = ModalParentStoryGenerator(client=client).generate(_v4_input())  # type: ignore[arg-type]
    submitted = client.calls[0]["worker_input"]
    assert isinstance(submitted, dict)
    assert submitted["schema_version"] == "sketch2life.story-generation-input.v3"
    assert submitted["role"] == "PARENT"
    assert result.call_id == "fc-story-adapter-test"
    assert (result.model_id, result.model_revision) == (STORY_MODEL_ID, STORY_MODEL_REVISION)


def test_parent_generator_splits_staging_from_the_story() -> None:
    client = _Client({"title": "A safe story", "scenes": [], "_staging": None})
    result = ModalParentStoryGenerator(client=client).generate(_v3_input())  # type: ignore[arg-type]
    assert result.story == {"title": "A safe story", "scenes": []}
    assert result.staging is None


def test_parent_generator_maps_terminal_worker_errors() -> None:
    client = _Client(error=ModalFunctionExecutionFailed("STORY_OUTPUT_INVALID"))
    with pytest.raises(StoryGenerationFailure, match="STORY_OUTPUT_INVALID"):
        ModalParentStoryGenerator(client=client).generate(_v3_input())  # type: ignore[arg-type]


def test_parent_generator_maps_unknown_worker_outcomes() -> None:
    client = _Client(error=ModalFunctionOutcomeUnknown())
    with pytest.raises(StoryGenerationOutcomeUnknown):
        ModalParentStoryGenerator(client=client).generate(_v3_input())  # type: ignore[arg-type]


def test_simple_generator_uses_the_same_dev_v3_projection() -> None:
    client = _Client()
    result = ModalStoryGenerator(client=client).generate(_v4_input())  # type: ignore[arg-type]
    assert client.calls[0]["worker_input"]["schema_version"] == (
        "sketch2life.story-generation-input.v3"
    )
    assert result.model_id == STORY_MODEL_ID


def test_v3_optional_learning_fields_are_preserved_by_the_adapter() -> None:
    worker = _v3_input(
        secondary_subjects=[{"entity_id": "leaf-1", "label": "leaf", "visible_features": []}],
        learning={"subject": "butterfly"},
    )
    projected = to_dev_story_worker_input(worker)
    assert projected["secondary_subjects"] == worker["secondary_subjects"]
    assert projected["learning"] == worker["learning"]


def test_v4_mapper_preserves_reviewed_lesson_notes_and_direction() -> None:
    projected = to_dev_story_worker_input(
        _v4_input(lesson_direction="Follow the approved lesson.")
    )
    assert projected["lesson_subject_learning_notes"] == "Observe wing patterns."
    assert projected["lesson_direction"] == "Follow the approved lesson."


def test_profile_specific_adapter_names_are_gone() -> None:
    source = inspect.getsource(ModalStoryGenerator)
    assert "STORY_Q38_PROFILE" not in source
    assert "STORY_V1_PROFILE" not in source


def test_simple_generator_also_accepts_teacher_and_sends_worker_role_parent() -> None:
    client = _Client()
    generator = ModalStoryGenerator(client=client)  # type: ignore[arg-type]
    assert generator.supports_role("TEACHER") is True
    generator.generate({**_v3_input(), "role": "TEACHER"})
    assert client.calls[0]["worker_input"]["role"] == "PARENT"


def test_parent_v4_adapter_drops_unknown_activity_metadata() -> None:
    activity = {**_activity(), "source": "AI_DRAFT", "content_sha256": "c" * 64}
    projected = to_dev_story_worker_input(_v4_input(activity=activity))
    assert set(projected["primary_activity"]) == set(_activity())
    assert "source" not in projected["primary_activity"]
    assert "content_sha256" not in projected["primary_activity"]


def test_dev_model_constants_are_not_configurable_through_story_settings() -> None:
    from sketch2life.infrastructure.config.settings import Settings

    fields = set(Settings.model_fields)
    assert "story_generation_profile" not in fields
    assert "modal_qwen_profile" not in fields


def test_v4_activity_hash_changes_when_sent_activity_text_changes() -> None:
    first = to_dev_story_worker_input(_v4_input())
    changed_activity = {**_activity(), "title": "Changed title"}
    second = to_dev_story_worker_input(_v4_input(activity=changed_activity))
    assert first["primary_activity_sha256"] != second["primary_activity_sha256"]


def test_generator_uses_the_v3_worker_input_without_restoring_the_old_definition() -> None:
    client = _Client()
    input_value = _v4_input(rewrite_instruction="Keep the ending calm.")
    result = ModalParentStoryGenerator(client=client).generate(input_value)  # type: ignore[arg-type]
    submitted = client.calls[0]["worker_input"]
    assert isinstance(submitted, dict)
    assert submitted["rewrite_instruction"] == "Keep the ending calm."
    assert result.story == {"title": "A safe story", "scenes": []}


def test_simple_generator_maps_terminal_worker_errors() -> None:
    client = _Client(error=ModalFunctionExecutionFailed("STORY_OUTPUT_INVALID"))
    with pytest.raises(StoryGenerationFailure, match="STORY_OUTPUT_INVALID"):
        ModalStoryGenerator(client=client).generate(_v3_input())  # type: ignore[arg-type]


def test_simple_generator_maps_unknown_worker_outcomes() -> None:
    client = _Client(error=ModalFunctionOutcomeUnknown())
    with pytest.raises(StoryGenerationOutcomeUnknown):
        ModalStoryGenerator(client=client).generate(_v3_input())  # type: ignore[arg-type]


def test_dev_adapter_rejects_legacy_v1_schema_before_client_call() -> None:
    with pytest.raises(ValueError, match="schema is not supported"):
        to_dev_story_worker_input(
            {"schema_version": "sketch2life.story-generation-input.v1", "role": "PARENT"}
        )


def test_current_v3_activity_hash_is_forwarded_without_recalculation() -> None:
    worker = _v3_input()
    projected = to_dev_story_worker_input(worker)
    assert projected["primary_activity_sha256"] == worker["primary_activity_sha256"]
