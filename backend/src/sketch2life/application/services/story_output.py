"""Validate and store a generated story draft; shared by both Parent story routes (T-2d).

The legacy route ``/api/parent/v1/ai/story-runs/{id}/story-revisions`` (a synchronous Modal call)
and the SRS route ``POST /v1/story-runs/{id}/story-rewrites`` (a generator port after the 202) hand
the raw draft to ``complete_generated_story``. The checks are the ones the legacy route always ran
(the draft schema and the canonical content hash). FEAT-093 Amendment C removed the subject-specific
butterfly life-cycle check.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

from pydantic import ValidationError

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryLifecycleRecord,
    ParentStoryRevisionReservation,
    ParentStoryRunError,
    ParentStoryRunRecord,
    ParentStoryRunRepositoryPort,
    TeacherStoryRunRecord,
)
from sketch2life.application.video_pipeline.story_timeline import TimelineError, check_line_text
from sketch2life.contracts.schemas.ai_story import StoryRevisionDraftV1
from sketch2life.domain.learning_script import LearningScriptError, check_learning_script

STORY_OUTPUT_INVALID = "STORY_OUTPUT_INVALID"


class StoryOutputInvalid(RuntimeError):
    """The generated draft failed validation; ``code`` is the stored and reported error code."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def normalize_story_output(
    raw_story: Mapping[str, Any], *, confirmed_subject: str
) -> tuple[dict[str, Any], str]:
    """The validated draft as plain JSON and its canonical SHA-256, or ``StoryOutputInvalid``."""
    try:
        story = StoryRevisionDraftV1.model_validate(raw_story)
    except (ValidationError, ValueError):
        raise StoryOutputInvalid(STORY_OUTPUT_INVALID) from None
    normalized = story.model_dump(mode="json")
    story_hash = hashlib.sha256(
        json.dumps(
            normalized,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return normalized, story_hash


def complete_generated_story(
    repository: ParentStoryRunRepositoryPort,
    *,
    principal: VerifiedPrincipal,
    reservation: ParentStoryRevisionReservation,
    raw_story: Mapping[str, Any],
    provider_call_id: str,
    model_id: str,
    model_revision: str,
    staging: dict[str, Any] | None = None,
    staging_issue: str | None = None,
) -> ParentStoryRunRecord | TeacherStoryRunRecord:
    """Validate the draft and store it, or record the failure and raise ``StoryOutputInvalid``.

    ``ParentStoryRunError`` from the repository (a purged run, a store fault) propagates to the
    caller, which decides how to report it.
    """
    draft = dict(raw_story)
    answered_learning = draft.pop("_learning", None)
    requested = reservation.worker_input.get("learning")
    learning: dict[str, Any] | None = None
    try:
        subject = str(reservation.worker_input["confirmed_subject"])
        normalized, story_hash = normalize_story_output(draft, confirmed_subject=subject)
        if requested is not None:
            try:
                learning = check_learning_script(
                    normalized, answered_learning, request=requested, subject=subject
                )
                # The video speaks this text as confirmed, so its line rules apply before the adult sees it.
                for scene in normalized["scenes"]:
                    check_line_text(scene["narration"])
            except (LearningScriptError, TimelineError):
                raise StoryOutputInvalid(STORY_OUTPUT_INVALID) from None
    except StoryOutputInvalid as invalid:
        repository.fail_story_revision(
            principal=principal,
            reservation=reservation,
            error_code=invalid.code,
            outcome_unknown=False,
        )
        raise
    record = repository.complete_story_revision(
        reservation=reservation,
        principal=principal,
        story=normalized,
        story_sha256=story_hash,
        provider_call_id=provider_call_id,
        model_id=model_id,
        model_revision=model_revision,
        staging=staging,
        staging_issue=staging_issue,
        learning=learning,
    )
    if isinstance(record, ParentStoryLifecycleRecord):
        # complete_story_revision refuses a purged run; a projection here is never served.
        raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
    # A Teacher run's job-side completion (T-4b3a) hands back the Teacher view; the runner ignores
    # it and the Parent route never meets one (its repository has no actor).
    return record


__all__ = [
    "STORY_OUTPUT_INVALID",
    "StoryOutputInvalid",
    "complete_generated_story",
    "normalize_story_output",
]
