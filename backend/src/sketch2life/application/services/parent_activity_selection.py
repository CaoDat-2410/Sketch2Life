"""Parent main-activity list and selection over the Lesson Library catalog (goal v4, T-2e-a).

SRS l.386, l.514, l.527, l.1412, l.1667. The list is what
``ParentActivitySuggestionService.prepare`` returns for the stored run context (at most 12 age-fit
activities, deterministic order); no AI call.
A selection is accepted only when the activity is a member of the list recomputed at that moment, so
a hidden, unpublished, over-age or unsafe activity can never be chosen by a hand-made reference. The
repository runs the recomputation as a resolver under the run row lock, after the idempotency replay
(``ParentStoryRunRepositoryPort.select_activity``), so a replay never recomputes the list.
"""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from typing import Any

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_activity_catalog import ParentActivityCatalogPort
from sketch2life.application.ports.parent_story_runs import (
    ParentActivityContext,
    ParentActivityPin,
    ParentStoryRunError,
    ParentStoryRunRepositoryPort,
    ParentStoryRunView,
    StoryStartedCallback,
)
from sketch2life.application.services.parent_activity_suggestions import (
    ParentActivitySuggestionError,
    ParentActivitySuggestionService,
    PreparedParentActivitySuggestion,
)

ACTIVITY_PIN_SCHEMA = "sketch2life.parent-activity-pin.v1"
# The list fields shown to the adult and copied into the stored snapshot (no storage URL, no ids
# other than the activity reference).
_ACTIVITY_TEXT_FIELDS = (
    "title",
    "objective",
    "materials_text",
    "preparation_text",
    "instructions_text",
    "observation_notes",
    "safety_notes",
    "activity_kind",
)


def _activity_ref(candidate: Any) -> dict[str, Any]:
    return {
        "lesson_id": candidate.lesson_id,
        "version_id": candidate.version_id,
        "content_sha256": candidate.content_sha256,
        "activity_index": candidate.activity_index,
    }


# The stored snapshot is bounded at 32768 bytes by the table (``ck_as_snapshot_bound``); the margin
# covers ``selected_at`` and the JSON spacing of the database text form. An activity that would not
# fit is not listed, so nothing listed is ever unselectable.
SNAPSHOT_BOUND_BYTES = 32_000


def activity_item(candidate: Any) -> dict[str, Any]:
    """One list item: the activity reference, its text, its source and its lesson."""

    activity = candidate.activity
    return {
        "activity_ref": _activity_ref(candidate),
        **{name: activity[name] for name in _ACTIVITY_TEXT_FIELDS},
        "source": candidate.source,
        "lesson_title": candidate.lesson_title,
        "lesson_topic": candidate.lesson_topic,
    }


def activity_pin_snapshot(candidate: Any) -> dict[str, Any]:
    """The stored snapshot body of a selection, without ``selected_at`` (the repository adds it)."""

    item = activity_item(candidate)
    return {"schema": ACTIVITY_PIN_SCHEMA, **item}


def _fits_snapshot(candidate: Any) -> bool:
    encoded = json.dumps(activity_pin_snapshot(candidate), ensure_ascii=False).encode("utf-8")
    return len(encoded) <= SNAPSHOT_BOUND_BYTES


def _listed(prepared: PreparedParentActivitySuggestion) -> Iterator[Any]:
    """The candidates the adult may see and choose: in the service's order, within the bound."""

    for ref in sorted(prepared.candidates_by_ref):
        candidate = prepared.candidates_by_ref[ref]
        if _fits_snapshot(candidate):
            yield candidate


class ParentActivitySelectionService:
    def __init__(
        self,
        repository: ParentStoryRunRepositoryPort,
        catalog: ParentActivityCatalogPort,
    ) -> None:
        self._repository = repository
        self._suggestions = ParentActivitySuggestionService(catalog)

    def _prepare(
        self, principal: VerifiedPrincipal, context: ParentActivityContext
    ) -> PreparedParentActivitySuggestion:
        try:
            return self._suggestions.prepare(
                parent_principal_ref=principal.subject,
                context_snapshot=context.context_snapshot,
                subject_label=context.subject_label,
                visible_features=context.visible_features,
                pinned_lesson_snapshot=context.lesson_pin_snapshot,
            )
        except ParentActivitySuggestionError:
            # The age, the drawing context or the pin cannot give a list: the run is not in a state
            # that can choose an activity (the code is the published state-transition code).
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION") from None

    def list_activities(self, *, principal: VerifiedPrincipal, run_id: str) -> dict[str, Any]:
        context = self._repository.read_activity_context(principal=principal, run_id=run_id)
        prepared = self._prepare(principal, context)
        items = [activity_item(candidate) for candidate in _listed(prepared)]
        return {
            "items": items,
            "basis": {
                "age_band": prepared.worker_input["age_band_months"],
                "pinned_lesson": context.lesson_pin_snapshot is not None,
                "no_candidate": not items,
            },
        }

    def select_activity(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_revision: int,
        activity_ref: Mapping[str, Any],
        idempotency_key: str,
        on_story_started: StoryStartedCallback | None = None,
    ) -> ParentStoryRunView:
        def resolve(context: ParentActivityContext) -> ParentActivityPin:
            prepared = self._prepare(principal, context)
            wanted = dict(activity_ref)
            for candidate in _listed(prepared):
                if _activity_ref(candidate) == wanted:
                    return ParentActivityPin(
                        lesson_id=candidate.lesson_id,
                        version_id=candidate.version_id,
                        content_sha256=candidate.content_sha256,
                        activity_index=candidate.activity_index,
                        snapshot=activity_pin_snapshot(candidate),
                    )
            # An accessible but unlisted activity is as absent as an inaccessible one.
            raise ParentStoryRunError(404, "RESOURCE_NOT_FOUND")

        return self._repository.select_activity(
            principal=principal,
            run_id=run_id,
            expected_revision=expected_revision,
            activity_ref=activity_ref,
            idempotency_key=idempotency_key,
            resolve=resolve,
            on_story_started=on_story_started,
        )


__all__ = [
    "ACTIVITY_PIN_SCHEMA",
    "ParentActivitySelectionService",
    "activity_item",
    "activity_pin_snapshot",
]
