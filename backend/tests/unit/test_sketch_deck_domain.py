from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

import pytest

import sketch2life.infrastructure.lesson_occurrences.sketch_decks as sketch_decks
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.domain.lesson_occurrences.sketch_deck import (
    DrawingStepInput,
    SketchDeckDrawingInputs,
    SketchDeckRuleError,
    SketchDeckStep,
    can_transition,
    revision_content_hash,
    steps_content_hash,
    validate_drawing_inputs,
    validate_ready_steps,
)
from sketch2life.infrastructure.lesson_occurrences.documents import DocumentError
from sketch2life.infrastructure.lesson_occurrences.sketch_decks import (
    PreparedSketchDeck,
    SketchDeckRevisionService,
)


def _step(activity_id: str, group: str, index: int) -> SketchDeckStep:
    return SketchDeckStep(
        plan_activity_id=activity_id,
        instruction_group_key=group,
        step_index=index,
        step_kind="DRAW",
        subject_key="tree",
        short_title=f"Step {index}",
        child_facing_prompt=f"Draw part {index}",
        teacher_explanation=f"Explain part {index}.",
        bounded_layout_hints={"region": f"{index}"},
    )


def test_state_machine_keeps_generating_terminal_and_ready_stale_or_superseded() -> None:
    assert can_transition("GENERATING", "READY")
    assert can_transition("GENERATING", "FAILED")
    assert can_transition("READY", "STALE")
    assert can_transition("READY", "SUPERSEDED")
    assert not can_transition("FAILED", "READY")
    assert not can_transition("STALE", "READY")
    assert not can_transition("SUPERSEDED", "STALE")


@pytest.mark.parametrize("step_count", [4, 8])
def test_drawing_inputs_accept_srs_4_to_8_steps(step_count: int) -> None:
    inputs = SketchDeckDrawingInputs(
        review_confirmed=True,
        topic="Tree",
        drawing_steps=tuple(
            DrawingStepInput(f"action {i}", f"placement {i}") for i in range(step_count)
        ),
        subject_knowledge=("Trees have trunks and leaves.",),
    )

    assert validate_drawing_inputs(inputs) == inputs


@pytest.mark.parametrize("step_count", [3, 9])
def test_drawing_inputs_reject_values_outside_srs_step_bounds(step_count: int) -> None:
    inputs = SketchDeckDrawingInputs(
        review_confirmed=True,
        topic="Tree",
        drawing_steps=tuple(
            DrawingStepInput(f"action {i}", f"placement {i}") for i in range(step_count)
        ),
        subject_knowledge=("Trees have trunks and leaves.",),
    )

    with pytest.raises(SketchDeckRuleError, match="INVALID_REQUEST"):
        validate_drawing_inputs(inputs)


def test_subject_knowledge_matches_worker_item_bounds() -> None:
    inputs = SketchDeckDrawingInputs(
        review_confirmed=True,
        topic="Tree",
        drawing_steps=tuple(DrawingStepInput(f"action {i}", f"placement {i}") for i in range(4)),
        subject_knowledge=tuple("x" * 240 for _ in range(8)),
    )
    assert validate_drawing_inputs(inputs) == inputs

    too_large = replace(inputs, subject_knowledge=("x" * 241,))
    with pytest.raises(SketchDeckRuleError, match="INVALID_REQUEST"):
        validate_drawing_inputs(too_large)


def test_revision_content_hash_covers_review_inputs_and_generated_steps() -> None:
    inputs = SketchDeckDrawingInputs(
        review_confirmed=True,
        topic="Tree",
        drawing_steps=tuple(DrawingStepInput(f"action {i}", f"placement {i}") for i in range(4)),
        subject_knowledge=("Trees have trunks and leaves.",),
    )
    changed = replace(inputs, subject_knowledge=("Trees have roots and leaves.",))
    age_confirmed = replace(inputs, teacher_confirmed_age_band_ref="age-36-71-months-v1")
    generated = tuple(_step("activity-a", "guide-a", index) for index in range(1, 5))

    assert revision_content_hash(inputs, generated) != revision_content_hash(changed, generated)
    assert revision_content_hash(inputs, generated) != revision_content_hash(
        age_confirmed, generated
    )


def test_idempotency_fingerprint_replays_identical_inputs_and_conflicts_on_changes() -> None:
    service = SketchDeckRevisionService.__new__(SketchDeckRevisionService)
    inputs = SketchDeckDrawingInputs(
        review_confirmed=True,
        topic="Tree",
        drawing_steps=tuple(DrawingStepInput(f"action {i}", f"placement {i}") for i in range(4)),
        subject_knowledge=("Trees have trunks and leaves.",),
    )
    common = {
        "occurrence_id": "occurrence-1",
        "expected_plan_revision_id": "plan-1",
        "expected_plan_hash": "a" * 64,
    }
    fingerprint = service.fingerprint(**common, drawing_inputs=inputs)
    receipt = SimpleNamespace(
        request_fingerprint=fingerprint,
        response_json={"sketch_deck_revision_id": "revision-1"},
        response_status=201,
    )

    replay = service._replay(receipt, service.fingerprint(**common, drawing_inputs=inputs))
    assert replay.body["sketch_deck_revision_id"] == "revision-1"

    changed = replace(inputs, topic="Tree canopy")
    with pytest.raises(DocumentError) as caught:
        service._replay(receipt, service.fingerprint(**common, drawing_inputs=changed))
    assert caught.value.code == "INVALID_IDEMPOTENCY_KEY"


def _activity_row() -> dict[str, object]:
    return {
        "plan_activity_id": "activity-1",
        "activity_kind": "LESSON",
        "activity_snapshot": {
            "title": "Tree observation",
            "objective": "Notice parts of a tree.",
            "materials_text": "Paper and pencils.",
            "preparation_text": "Prepare a clear workspace.",
            "instructions_text": "Observe, then draw.",
            "safety_notes": "Use pencils safely.",
        },
    }


def _custom_activity_row() -> dict[str, object]:
    return {
        "plan_activity_id": "activity-custom-1",
        "activity_kind": "CUSTOM",
        "activity_snapshot": None,
        "custom_title": "Observe a tree",
        "custom_description": "Look at the trunk and leaves, then describe what you notice.",
        "safety_checklist_version": "teacher-custom-activity-v1",
        "checklist_result": {
            "items": [{"item_id": "adult_supervision", "checked": True}]
        },
        "confirmed_by": "synthetic-teacher",
        "confirmed_at": "2026-11-27T00:00:00Z",
    }


class _QueryResult:
    def __init__(
        self,
        *,
        row: dict[str, object] | None = None,
        rows: tuple[dict[str, object], ...] = (),
    ) -> None:
        self.row = row
        self.rows = rows

    def mappings(self) -> _QueryResult:
        return self

    def one_or_none(self) -> dict[str, object] | None:
        return self.row

    def all(self) -> tuple[dict[str, object], ...]:
        return self.rows


class _QueryDb:
    def __init__(self, results: tuple[_QueryResult, ...]) -> None:
        self.results = iter(results)
        self.execute_count = 0

    def execute(self, _statement: object) -> _QueryResult:
        self.execute_count += 1
        return next(self.results)

    def rollback(self) -> None:
        pass


def _prepare_sketch_deck(
    monkeypatch: pytest.MonkeyPatch,
    *,
    plan: dict[str, object],
    query_results: tuple[_QueryResult, ...],
    teacher_confirmed_age_band_ref: str | None = None,
) -> tuple[PreparedSketchDeck, _QueryDb]:
    db = _QueryDb(query_results)
    service = SketchDeckRevisionService(db)  # type: ignore[arg-type]
    monkeypatch.setattr(
        sketch_decks,
        "authorize_occurrence",
        lambda *_args, **_kwargs: SimpleNamespace(occurrence={}),
    )
    monkeypatch.setattr(service, "_approved_plan", lambda **_kwargs: plan)
    drawing_inputs = SketchDeckDrawingInputs(
        review_confirmed=True,
        topic="Tree",
        drawing_steps=tuple(
            DrawingStepInput(f"action {index}", f"placement {index}") for index in range(4)
        ),
        subject_knowledge=("Trees have roots.",),
        teacher_confirmed_age_band_ref=teacher_confirmed_age_band_ref,
    )
    prepared = service.prepare_worker_input(
        principal=VerifiedPrincipal(
            subject="synthetic-teacher", issuer="test", roles=frozenset()
        ),
        occurrence_id="occurrence-1",
        expected_plan_revision_id="plan-1",
        expected_plan_hash="a" * 64,
        drawing_inputs=drawing_inputs,
    )
    return prepared, db


def test_prepare_worker_input_accepts_teacher_confirmed_age_without_library_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = {
        "source_lesson_version_id": None,
        "source_lesson_version_hash": None,
        "objectives": ["Notice parts of a tree."],
    }
    prepared, db = _prepare_sketch_deck(
        monkeypatch,
        plan=plan,
        query_results=(_QueryResult(rows=(_custom_activity_row(),)),),
        teacher_confirmed_age_band_ref="age-72-107-months-v1",
    )

    assert prepared.target_age_band == "age-72-107-months-v1"
    assert prepared.worker_input["target_age_months"] == 90
    assert prepared.plan_activity_ids == ("activity-custom-1",)
    assert prepared.worker_input["activities"] == [
        {
            "activity_ref": "activity-custom-1",
            "title": "Observe a tree",
            "description": "Look at the trunk and leaves, then describe what you notice.",
        }
    ]
    assert db.execute_count == 1


def test_prepare_worker_input_rejects_custom_activity_without_satisfied_checklist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = {
        "source_lesson_version_id": None,
        "source_lesson_version_hash": None,
        "objectives": ["Notice parts of a tree."],
    }
    activity = _custom_activity_row()
    activity["checklist_result"] = {
        "items": [{"item_id": "adult_supervision", "checked": False}]
    }

    with pytest.raises(DocumentError) as caught:
        _prepare_sketch_deck(
            monkeypatch,
            plan=plan,
            query_results=(_QueryResult(rows=(activity,)),),
            teacher_confirmed_age_band_ref="age-72-107-months-v1",
        )

    assert caught.value.status_code == 409
    assert caught.value.code == "SKETCH_DECK_PLAN_INCOMPLETE"


@pytest.mark.parametrize(
    ("source", "field", "value", "expected_field"),
    [
        ("plan", "objectives", ["x" * 201], "objectives[0]"),
        ("plan", "objectives", ["   "], "objectives[0]"),
        ("plan", "objectives", [], "objectives"),
        ("plan", "objectives", ["Notice trees."] * 5, "objectives"),
        ("activity", "title", "x" * 121, "activities[0].title"),
        ("activity", "title", "   ", "activities[0].title"),
        ("activity", "activity_ref", "invalid/ref", "activities[0].activity_ref"),
        ("activity", "objective", "x" * 201, "activities[0].goal"),
        ("activity", "objective", "   ", "activities[0].goal"),
        ("activity", "materials_text", "x" * 501, "activities[0].materials"),
        ("activity", "materials_text", "   ", "activities[0].materials"),
        ("activity", "preparation_text", "x" * 501, "activities[0].preparation"),
        ("activity", "preparation_text", "   ", "activities[0].preparation"),
        ("activity", "instructions_text", "x" * 1_201, "activities[0].instructions"),
        ("activity", "instructions_text", "   ", "activities[0].instructions"),
        ("activity", "safety_notes", "x" * 501, "activities[0].safety_notes"),
        ("activity", "safety_notes", "   ", "activities[0].safety_notes"),
        ("custom", "custom_title", "x" * 161, "activities[0].title"),
        ("custom", "custom_title", "   ", "activities[0].title"),
        ("custom", "custom_description", "x" * 4_001, "activities[0].description"),
        ("custom", "custom_description", "   ", "activities[0].description"),
    ],
)
def test_prepare_worker_input_rejects_stored_fields_outside_worker_limits(
    monkeypatch: pytest.MonkeyPatch,
    source: str,
    field: str,
    value: object,
    expected_field: str,
) -> None:
    plan = {
        "source_lesson_version_id": None,
        "source_lesson_version_hash": None,
        "objectives": ["Notice parts of a tree."],
    }
    activity = _activity_row()
    if source == "plan":
        plan[field] = value
    elif source == "custom":
        activity = _custom_activity_row()
        activity[field] = value
    elif field == "activity_ref":
        activity["plan_activity_id"] = value
    elif field == "title":
        activity["activity_snapshot"][field] = value  # type: ignore[index]
    else:
        snapshot_key = field
        activity["activity_snapshot"][snapshot_key] = value  # type: ignore[index]

    with pytest.raises(DocumentError) as caught:
        _prepare_sketch_deck(
            monkeypatch,
            plan=plan,
            query_results=(_QueryResult(rows=(activity,)),),
            teacher_confirmed_age_band_ref="age-72-107-months-v1",
        )

    assert caught.value.status_code == 400
    assert caught.value.code == "INVALID_REQUEST"
    assert caught.value.field_errors == [
        {"field": expected_field, "code": "INVALID_FORMAT"}
    ]


@pytest.mark.parametrize("activity_count", [0, 7])
def test_prepare_worker_input_rejects_stored_activity_count_outside_worker_limits(
    monkeypatch: pytest.MonkeyPatch, activity_count: int
) -> None:
    plan = {
        "source_lesson_version_id": None,
        "source_lesson_version_hash": None,
        "objectives": ["Notice parts of a tree."],
    }
    rows = tuple(
        {**_activity_row(), "plan_activity_id": f"activity-{index}"}
        for index in range(activity_count)
    )

    with pytest.raises(DocumentError) as caught:
        _prepare_sketch_deck(
            monkeypatch,
            plan=plan,
            query_results=(_QueryResult(rows=rows),),
            teacher_confirmed_age_band_ref="age-72-107-months-v1",
        )

    assert caught.value.status_code == 400
    assert caught.value.code == "INVALID_REQUEST"
    assert caught.value.field_errors == [
        {"field": "activities", "code": "INVALID_FORMAT"}
    ]


def test_prepare_worker_input_preserves_legacy_36_71_source_age_band(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = {
        "source_lesson_version_id": "lesson-version-1",
        "source_lesson_version_hash": "source-hash",
        "objectives": ["Notice parts of a tree."],
    }
    source = {
        "content_json": {"target_age_band_ref": "36-71"},
        "structured_content_hash": "source-hash",
    }
    prepared, db = _prepare_sketch_deck(
        monkeypatch,
        plan=plan,
        query_results=(
            _QueryResult(row=source),
            _QueryResult(rows=(_activity_row(),)),
        ),
    )

    assert prepared.target_age_band == "36-71"
    assert prepared.worker_input["target_age_months"] == 54
    assert db.execute_count == 2


def test_ready_steps_require_every_activity_and_four_to_eight_ordered_steps_per_group() -> None:
    steps = tuple(_step("activity-a", "guide-a", index) for index in range(1, 5)) + tuple(
        _step("activity-b", "guide-b", index) for index in range(1, 9)
    )

    result = validate_ready_steps(("activity-a", "activity-b"), steps)

    assert len(result) == 12
    assert steps_content_hash(result) == steps_content_hash(steps)


def test_ready_steps_allow_a_guide_group_without_a_plan_activity() -> None:
    assigned = tuple(_step("activity-a", "guide-a", index) for index in range(1, 5))
    unassigned = tuple(
        replace(_step("activity-a", "guide-b", index), plan_activity_id=None)
        for index in range(1, 5)
    )

    result = validate_ready_steps(("activity-a",), assigned + unassigned)

    assert len(result) == 8


def test_ready_steps_reject_missing_coverage_and_non_contiguous_order() -> None:
    with pytest.raises(SketchDeckRuleError, match="MODAL_OUTPUT_CONTRACT_INVALID"):
        validate_ready_steps(
            ("activity-a", "activity-b"),
            tuple(_step("activity-a", "guide-a", index) for index in range(1, 5)),
        )

    broken = tuple(_step("activity-a", "guide-a", index) for index in (1, 2, 4, 5))
    with pytest.raises(SketchDeckRuleError, match="MODAL_OUTPUT_CONTRACT_INVALID"):
        validate_ready_steps(("activity-a",), broken)


def test_ready_steps_reject_oversized_layout_hints() -> None:
    steps = list(_step("activity-a", "guide-a", index) for index in range(1, 5))
    steps[0] = replace(steps[0], bounded_layout_hints={"value": "x" * 16_500})

    with pytest.raises(SketchDeckRuleError, match="MODAL_OUTPUT_CONTRACT_INVALID"):
        validate_ready_steps(("activity-a",), steps)
