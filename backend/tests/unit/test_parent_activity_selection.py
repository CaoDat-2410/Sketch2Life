"""FEAT-066 goal v4 T-2e-a: the Parent activity list and selection service (offline).

A fake catalog and a fake repository: the list is what ``prepare`` returns (at most 12, no AI), the
selection accepts only a member of the list recomputed at that moment, the snapshot is the item
plus its schema, and the repository decides replay, state, revision and rollback around the
resolver.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import pytest

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_activity_catalog import (
    ParentActivityCatalogPort,
    ParentActivityLesson,
)
from sketch2life.application.ports.parent_story_runs import (
    ParentActivityContext,
    ParentActivityPin,
    ParentStoryRunError,
)
from sketch2life.application.services.parent_activity_selection import (
    ACTIVITY_PIN_SCHEMA,
    ParentActivitySelectionService,
)

PRINCIPAL = VerifiedPrincipal("parent-1", "issuer-1", frozenset())
RUN_ID = "11111111-1111-4111-8111-111111111111"
HASH = "c" * 64


def _activity(
    title: str, *, kind: str = "outdoor", objective: str = "Quan sat la cay"
) -> dict[str, Any]:
    return {
        "title": title,
        "objective": objective,
        "materials_text": "",
        "preparation_text": "",
        "instructions_text": "Cung tre quan sat la cay trong san truong",
        "observation_notes": "",
        "safety_notes": "Di cung nguoi lon",
        "activity_kind": kind,
    }


def _lesson(
    lesson_id: str, activities: Sequence[Mapping[str, Any]], *, age_ref: str = "age-36-71-months-v1"
) -> ParentActivityLesson:
    return ParentActivityLesson(
        lesson_id=lesson_id,
        version_id=f"version-{lesson_id}",
        version_no=1,
        content_sha256=HASH,
        title="Bai hoc",
        topic="la cay",
        drawing_subject="la cay",
        target_age_band_ref=age_ref,
        target_age_band_version=1,
        access_source="PUBLIC",
        activities=tuple(activities),
    )


class _Catalog(ParentActivityCatalogPort):
    def __init__(self, lessons: Sequence[ParentActivityLesson]) -> None:
        self.lessons = list(lessons)
        self.calls = 0

    def list_accessible_lessons(
        self, *, parent_principal_ref: str
    ) -> Sequence[ParentActivityLesson]:
        self.calls += 1
        assert parent_principal_ref == PRINCIPAL.subject
        return self.lessons


def _context(**changes: Any) -> ParentActivityContext:
    values: dict[str, Any] = {
        "run_id": RUN_ID,
        "run_revision": 5,
        "understanding_revision": 1,
        "context_snapshot": {
            "age_months": 60,
            "topic": "la cay",
            "adult_confirmed_idea": "",
            "interests_summary": "",
        },
        "subject_label": "la cay",
        "visible_features": ["la xanh"],
        "lesson_pin_snapshot": None,
    }
    values.update(changes)
    return ParentActivityContext(**values)


class _Repository:
    def __init__(self, context: ParentActivityContext | Exception) -> None:
        self.context = context
        self.resolved: ParentActivityPin | None = None
        self.select_kwargs: dict[str, Any] = {}

    def read_activity_context(self, *, principal: VerifiedPrincipal, run_id: str) -> Any:
        if isinstance(self.context, Exception):
            raise self.context
        return self.context

    def select_activity(self, **kwargs: Any) -> Any:
        self.select_kwargs = kwargs
        # the repository calls the resolver under the lock with the stored context
        assert not isinstance(self.context, Exception)
        self.resolved = kwargs["resolve"](self.context)
        return "view"


def _service(
    lessons: Sequence[ParentActivityLesson],
    context: ParentActivityContext | Exception | None = None,
) -> tuple[ParentActivitySelectionService, _Repository, _Catalog]:
    repository = _Repository(context if context is not None else _context())
    catalog = _Catalog(lessons)
    return ParentActivitySelectionService(repository, catalog), repository, catalog  # type: ignore[arg-type]


def _ref(item: Mapping[str, Any]) -> dict[str, Any]:
    return dict(item["activity_ref"])


# ------------------------------------------------------------------------- the list
def test_the_list_returns_the_outdoor_age_fit_activities_with_their_references_and_basis() -> None:
    service, _, _ = _service(
        [_lesson("a", [_activity("Tim la cay"), _activity("Ve trong nha", kind="indoor")])]
    )
    listing = service.list_activities(principal=PRINCIPAL, run_id=RUN_ID)
    assert [item["title"] for item in listing["items"]] == ["Tim la cay"]
    item = listing["items"][0]
    assert _ref(item) == {
        "lesson_id": "a",
        "version_id": "version-a",
        "content_sha256": HASH,
        "activity_index": 0,
    }
    assert item["source"] == "PUBLIC" and item["lesson_topic"] == "la cay"
    assert set(item) == {
        "activity_ref",
        "title",
        "objective",
        "materials_text",
        "preparation_text",
        "instructions_text",
        "observation_notes",
        "safety_notes",
        "activity_kind",
        "source",
        "lesson_title",
        "lesson_topic",
    }
    assert listing["basis"] == {"age_band": "36-71", "pinned_lesson": False, "no_candidate": False}


def test_the_list_is_bounded_at_twelve_and_deterministic() -> None:
    lessons = [_lesson(f"l{index:02d}", [_activity("Tim la cay")]) for index in range(15)]
    service, _, _ = _service(lessons)
    first = service.list_activities(principal=PRINCIPAL, run_id=RUN_ID)
    again = service.list_activities(principal=PRINCIPAL, run_id=RUN_ID)
    assert len(first["items"]) == 12 and first == again
    assert [item["activity_ref"]["lesson_id"] for item in first["items"]] == [
        f"l{index:02d}" for index in range(12)
    ]


def test_no_age_fit_activity_is_an_empty_list_with_no_candidate() -> None:
    older = _lesson("a", [_activity("Tim la cay")], age_ref="age-108-120-months-v1")
    listing = _service([older])[0].list_activities(principal=PRINCIPAL, run_id=RUN_ID)
    assert listing["items"] == [] and listing["basis"]["no_candidate"] is True


def test_a_pinned_lesson_restricts_the_list_to_the_pin_and_reads_no_catalog() -> None:
    pin = {
        "lesson_id": "pinned",
        "version_id": "version-pinned",
        "version_no": 1,
        "content_sha256": HASH,
        "title": "Bai da ghim",
        "topic": "la cay",
        "drawing_subject": "la cay",
        "target_age_band_ref": "age-36-71-months-v1",
        "target_age_band_version": 1,
        "activities": [_activity("Tim la cay")],
    }
    service, _, catalog = _service(
        [_lesson("other", [_activity("Khac")])], _context(lesson_pin_snapshot=pin)
    )
    listing = service.list_activities(principal=PRINCIPAL, run_id=RUN_ID)
    assert [item["activity_ref"]["lesson_id"] for item in listing["items"]] == ["pinned"]
    assert listing["items"][0]["source"] == "PINNED_LESSON" and listing["basis"]["pinned_lesson"]
    assert catalog.calls == 0


@pytest.mark.parametrize(
    "context",
    [
        _context(context_snapshot={"age_months": 12, "topic": "x"}),
        _context(context_snapshot={"age_months": "60"}),
        _context(subject_label=" "),
        _context(lesson_pin_snapshot={"lesson_id": "only-an-id"}),
    ],
)
def test_a_context_that_cannot_give_a_list_is_409_invalid_state(
    context: ParentActivityContext,
) -> None:
    service, _, _ = _service([_lesson("a", [_activity("Tim la cay")])], context)
    with pytest.raises(ParentStoryRunError) as raised:
        service.list_activities(principal=PRINCIPAL, run_id=RUN_ID)
    assert (raised.value.status_code, raised.value.code) == (409, "INVALID_STATE_TRANSITION")


def test_the_repository_refusal_passes_through_unchanged() -> None:
    service, _, _ = _service([], ParentStoryRunError(422, "SUBJECT_NOT_CONFIRMED"))
    with pytest.raises(ParentStoryRunError) as raised:
        service.list_activities(principal=PRINCIPAL, run_id=RUN_ID)
    assert raised.value.code == "SUBJECT_NOT_CONFIRMED"


# ------------------------------------------------------------------------- the selection
def test_a_listed_activity_resolves_to_its_pin_with_the_snapshot_of_the_item() -> None:
    service, repository, _ = _service([_lesson("a", [_activity("Tim la cay")])])
    listed = service.list_activities(principal=PRINCIPAL, run_id=RUN_ID)["items"][0]
    result = service.select_activity(
        principal=PRINCIPAL,
        run_id=RUN_ID,
        expected_revision=5,
        activity_ref=_ref(listed),
        idempotency_key="key-1",
    )
    assert result == "view"
    pin = repository.resolved
    assert pin is not None
    assert (pin.lesson_id, pin.version_id, pin.content_sha256, pin.activity_index) == (
        "a",
        "version-a",
        HASH,
        0,
    )
    assert pin.snapshot == {"schema": ACTIVITY_PIN_SCHEMA, **listed}
    assert "selected_at" not in pin.snapshot  # the repository stamps the time
    assert repository.select_kwargs["expected_revision"] == 5
    assert repository.select_kwargs["idempotency_key"] == "key-1"


@pytest.mark.parametrize(
    "change",
    [
        {"lesson_id": "unknown"},
        {"version_id": "version-old"},
        {"content_sha256": "d" * 64},
        {"activity_index": 5},
    ],
)
def test_an_activity_that_is_not_in_the_list_is_the_uniform_404(change: dict[str, Any]) -> None:
    service, _, _ = _service([_lesson("a", [_activity("Tim la cay")])])
    listed = service.list_activities(principal=PRINCIPAL, run_id=RUN_ID)["items"][0]
    with pytest.raises(ParentStoryRunError) as raised:
        service.select_activity(
            principal=PRINCIPAL,
            run_id=RUN_ID,
            expected_revision=5,
            activity_ref={**_ref(listed), **change},
            idempotency_key="key-1",
        )
    assert (raised.value.status_code, raised.value.code) == (404, "RESOURCE_NOT_FOUND")


def test_an_accessible_activity_ranked_beyond_twelve_is_refused_not_selectable() -> None:
    """A hand-made reference to an accessible but unlisted activity is as absent as a hidden one."""

    lessons = [_lesson(f"l{index:02d}", [_activity("Tim la cay")]) for index in range(13)]
    service, _, _ = _service(lessons)
    thirteenth = {
        "lesson_id": "l12",
        "version_id": "version-l12",
        "content_sha256": HASH,
        "activity_index": 0,
    }
    with pytest.raises(ParentStoryRunError) as raised:
        service.select_activity(
            principal=PRINCIPAL,
            run_id=RUN_ID,
            expected_revision=5,
            activity_ref=thirteenth,
            idempotency_key="key-1",
        )
    assert raised.value.status_code == 404


def test_the_resolver_recomputes_the_list_on_every_call() -> None:
    """The service holds no list: each selection reads the catalog again under the run lock."""

    service, _, catalog = _service([_lesson("a", [_activity("Tim la cay")])])
    listed = service.list_activities(principal=PRINCIPAL, run_id=RUN_ID)["items"][0]
    assert catalog.calls == 1
    service.select_activity(
        principal=PRINCIPAL,
        run_id=RUN_ID,
        expected_revision=5,
        activity_ref=_ref(listed),
        idempotency_key="key-1",
    )
    assert catalog.calls == 2
    catalog.lessons = []  # unpublished in the meantime
    with pytest.raises(ParentStoryRunError):
        service.select_activity(
            principal=PRINCIPAL,
            run_id=RUN_ID,
            expected_revision=5,
            activity_ref=_ref(listed),
            idempotency_key="key-2",
        )
    assert catalog.calls == 3


# ------------------------------------------------------------------------- the snapshot bound
def test_an_activity_over_the_snapshot_bound_is_neither_listed_nor_selectable() -> None:
    huge = _activity("Tim la cay")
    huge["instructions_text"] = "Cung tre quan sat la cay " + "ế" * 4900  # 3 bytes each
    huge["objective"] = "Quan sat la cay " + "ế" * 900
    huge["materials_text"] = "ế" * 1900
    huge["preparation_text"] = "ế" * 1900
    huge["observation_notes"] = "ế" * 2900
    huge["safety_notes"] = "Di cung nguoi lon " + "ế" * 2900
    service, _, _ = _service([_lesson("big", [huge]), _lesson("small", [_activity("Tim la cay")])])
    listing = service.list_activities(principal=PRINCIPAL, run_id=RUN_ID)
    assert [item["activity_ref"]["lesson_id"] for item in listing["items"]] == ["small"]
    with pytest.raises(ParentStoryRunError) as raised:
        service.select_activity(
            principal=PRINCIPAL,
            run_id=RUN_ID,
            expected_revision=5,
            activity_ref={
                "lesson_id": "big",
                "version_id": "version-big",
                "content_sha256": HASH,
                "activity_index": 0,
            },
            idempotency_key="key-1",
        )
    assert raised.value.status_code == 404
