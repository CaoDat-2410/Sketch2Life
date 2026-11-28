"""Adapt Parent and Teacher story inputs to the current dev story-worker contract."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import Any

from sketch2life.application.ports.parent_story_inputs import (
    StoryGenerationFailure,
    StoryGenerationOutcomeUnknown,
    StoryGenerationResult,
)
from sketch2life.domain.ai_jobs.completion import canonical_json
from sketch2life.infrastructure.ai.modal_function_client import (
    STORY_MODEL_ID,
    STORY_MODEL_REVISION,
    ModalFunctionExecutionFailed,
    ModalFunctionOutcomeUnknown,
    ModalStoryFunctionClient,
)


def to_dev_story_worker_input(worker_input: Mapping[str, Any]) -> dict[str, Any]:
    """Map the stored story envelope to the dev worker's strict v3 shape.

    The dev worker has no v4/rewrite-v2 model profile. The API-owned revision and adult-review
    gates remain outside this adapter; only the approved subject, activity text, and safe story
    context are sent to the worker. Teacher role is translated at this adapter boundary because
    the deployed worker uses role only as an input gate; its prompt does not use the role.
    """
    if worker_input.get("schema_version") == "sketch2life.story-generation-input.v3":
        mapped = dict(worker_input)
    elif worker_input.get("schema_version") in {
        "sketch2life.story-generation-input.v4",
        "sketch2life.story-rewrite-input.v2",
    }:
        activity = worker_input.get("activity") or worker_input.get("primary_activity")
        if not isinstance(activity, Mapping):
            raise ValueError("Parent story input has no selected activity")
        primary_activity = {
            "title": activity.get("title"),
            "objective": activity.get("objective"),
            "materials_text": activity.get("materials_text", ""),
            "preparation_text": activity.get("preparation_text", ""),
            "instructions_text": activity.get("instructions_text"),
            "observation_notes": activity.get("observation_notes", ""),
            "safety_notes": activity.get("safety_notes"),
            "activity_kind": activity.get("activity_kind"),
        }
        activity_hash = hashlib.sha256(
            canonical_json(primary_activity).encode("utf-8")
        ).hexdigest()
        confirmed_subject = worker_input.get("confirmed_subject")
        topic = worker_input.get("topic", confirmed_subject)
        mapped = {
            "schema_version": "sketch2life.story-generation-input.v3",
            "role": worker_input.get("role"),
            "language": worker_input.get("language"),
            "topic": topic,
            "confirmed_subject": confirmed_subject,
            "understanding_revision": worker_input.get("understanding_revision"),
            "drawing_sha256": worker_input.get("drawing_sha256"),
            "visible_features": worker_input.get("visible_features"),
            "child_age_months": worker_input.get("child_age_months"),
            "context_revision": worker_input.get("context_revision"),
            "adult_confirmed_idea": worker_input.get("adult_confirmed_idea"),
            "rewrite_instruction": worker_input.get("rewrite_instruction"),
            "lesson_subject_learning_notes": worker_input.get(
                "lesson_subject_learning_notes"
            ),
            "lesson_direction": worker_input.get("lesson_direction"),
            "primary_activity": primary_activity,
            "primary_activity_sha256": activity_hash,
        }
        secondary_subjects = worker_input.get("secondary_subjects")
        if secondary_subjects is not None:
            mapped["secondary_subjects"] = secondary_subjects
        learning = worker_input.get("learning")
        if isinstance(learning, dict):
            mapped["learning"] = learning
    else:
        raise ValueError("Parent story input schema is not supported by the dev worker")
    if mapped.get("role") == "TEACHER":
        mapped["role"] = "PARENT"
    return mapped


class ModalStoryGenerator:
    """Expose the dev story worker through the application story-generation port."""

    def __init__(self, client: ModalStoryFunctionClient | None = None) -> None:
        self._client = client or ModalStoryFunctionClient()

    def supports_role(self, role: str) -> bool:
        return role in {"PARENT", "TEACHER"}

    def generate(self, worker_input: Mapping[str, Any]) -> StoryGenerationResult:
        if not isinstance(worker_input, Mapping) or worker_input.get("role") not in {
            "PARENT",
            "TEACHER",
        }:
            raise StoryGenerationFailure("STORY_INPUT_CONTRACT_INVALID")
        try:
            story, call_id = self._client.generate(
                {"worker_input": to_dev_story_worker_input(worker_input)}
            )
        except ModalFunctionOutcomeUnknown as exc:
            raise StoryGenerationOutcomeUnknown() from exc
        except ModalFunctionExecutionFailed as exc:
            raise StoryGenerationFailure(exc.code) from None
        except ValueError:
            raise StoryGenerationFailure("STORY_INPUT_CONTRACT_INVALID") from None
        return StoryGenerationResult(
            story=story,
            call_id=call_id,
            model_id=STORY_MODEL_ID,
            model_revision=STORY_MODEL_REVISION,
        )


__all__ = ["ModalStoryGenerator", "to_dev_story_worker_input"]
