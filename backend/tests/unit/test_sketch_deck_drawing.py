from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest
from sqlalchemy import Select

import sketch2life.infrastructure.lesson_occurrences.sketch_deck_drawing as drawing_module
import sketch2life.infrastructure.lesson_occurrences.sketch_decks as sketch_decks_module
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.domain.lesson_occurrences.sketch_deck import SketchDeckStep
from sketch2life.infrastructure.lesson_occurrences.sketch_deck_tables import (
    SKETCH_DECK_REVISIONS,
    SKETCH_DECK_STEPS,
)
from sketch2life.infrastructure.lesson_occurrences.sketch_decks import (
    SketchDeckGenerationStart,
    SketchDeckRevisionService,
)


def _steps(count: int) -> tuple[SketchDeckStep, ...]:
    return tuple(
        SketchDeckStep(
            plan_activity_id="activity-a",
            instruction_group_key="tree-guide",
            step_index=index,
            step_kind="DRAW",
            subject_key="tree",
            short_title=f"Step {index}",
            child_facing_prompt=f"Draw step {index}.",
            teacher_explanation=f"Teacher note {index}.",
            bounded_layout_hints={},
        )
        for index in range(1, count + 1)
    )


def _stroke(x: int) -> dict[str, Any]:
    return {
        "kind": "line",
        "x1": x,
        "y1": 0,
        "x2": x + 1,
        "y2": 1,
        "stroke": "#1f2937",
        "stroke_width": 2,
    }


class _Catalog:
    def __init__(self, item: dict[str, Any] | None) -> None:
        self.item = item
        self.calls: list[dict[str, Any]] = []

    def list_parent_guides(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        return {"items": [self.item] if self.item is not None else []}


def _catalog_item() -> dict[str, Any]:
    return {
        "document": {
            "view_box": "0 0 100 100",
            "paths": [
                {"path_id": "path-a", "d": "M 0 0 L 10 10", "stroke_width": 2},
                {"path_id": "path-b", "d": "M 10 10 L 20 20", "stroke_width": 2},
            ],
        },
        "guide": {
            "stages": [
                {"animation_order": ["path-a"]},
                {"animation_order": ["path-b"]},
            ]
        },
    }


def test_catalog_is_selected_before_recipe_and_subject_key_is_exact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    catalog = _Catalog(_catalog_item())
    monkeypatch.setattr(
        drawing_module,
        "find_recipe",
        lambda *_args, **_kwargs: pytest.fail("recipe lookup must follow a usable catalog guide"),
    )

    drawing = drawing_module.resolve_local_drawing(
        subject="Đàn Tree", target_age_band="age-36-71-months-v1", catalog=catalog
    )

    assert drawing is not None
    assert drawing["source"] == "catalog"
    assert len(drawing["strokes"]) == 2
    assert catalog.calls == [{"topic_key": "dan-tree", "limit": 1}]


def test_recipe_is_used_when_catalog_cannot_supply_strokes(monkeypatch: pytest.MonkeyPatch) -> None:
    recipe = SimpleNamespace(
        steps=(
            SimpleNamespace(
                strokes=(SimpleNamespace(samples=((1, 2), (3, 4))),)
            ),
        )
    )
    calls: list[tuple[list[str], str]] = []

    def find_recipe(texts: list[str], level: str) -> object:
        calls.append((texts, level))
        return recipe

    monkeypatch.setattr(drawing_module, "find_recipe", find_recipe)
    catalog = _Catalog(None)

    drawing = drawing_module.resolve_local_drawing(
        subject="Tree", target_age_band="age-36-71-months-v1", catalog=catalog
    )

    assert drawing is not None
    assert drawing["source"] == "recipe"
    assert calls == [(["Tree"], "simple")]  # also for a 36-71 months lesson


@pytest.mark.parametrize("step_count", range(4, 9))
def test_split_strokes_returns_exactly_one_ordered_group_per_step(step_count: int) -> None:
    strokes = [_stroke(index) for index in range(step_count)]

    groups = drawing_module.split_strokes(strokes, step_count)

    assert len(groups) == step_count
    assert all(len(group) == 1 for group in groups)
    assert [group[0]["x1"] for group in groups] == list(range(step_count))


def test_split_strokes_places_remainder_early_and_leaves_empty_tail_when_short() -> None:
    groups = drawing_module.split_strokes([_stroke(0), _stroke(1), _stroke(2)], 5)

    assert [len(group) for group in groups] == [1, 1, 1, 0, 0]
    assert [group[0]["x1"] for group in groups[:3]] == [0, 1, 2]


def test_attached_hints_store_only_each_step_strokes_and_share_whole_drawing_hash() -> None:
    strokes = [_stroke(index) for index in range(6)]
    whole = drawing_module._make_drawing([0, 0, 100, 100], strokes, "recipe")
    assert whole is not None

    result = drawing_module.attach_progressive_drawing(_steps(4), whole)

    hints = [step.bounded_layout_hints["drawing"] for step in result]
    assert [len(hint["strokes"]) for hint in hints] == [2, 2, 1, 1]
    assert all(hint["sha256"] == whole["sha256"] for hint in hints)
    assert all(hint["source"] == "recipe" for hint in hints)
    assert [stroke["x1"] for hint in hints for stroke in hint["strokes"]] == list(range(6))


def test_oversized_drawing_is_omitted_from_all_steps() -> None:
    large_stroke = {
        "kind": "polyline",
        "points": [[10_000, 10_000] for _ in range(2_000)],
        "stroke": "#1f2937",
        "stroke_width": 2,
    }
    whole = drawing_module._make_drawing([0, 0, 100, 100], [large_stroke] * 4, "catalog")
    assert whole is not None
    steps = _steps(4)

    result = drawing_module.attach_progressive_drawing(steps, whole)

    assert result == steps
    assert all("drawing" not in step.bounded_layout_hints for step in result)


def test_ai_draft_uses_the_existing_shape_validator_and_gets_a_whole_drawing_hash() -> None:
    style = {"stroke": "#1f2937", "stroke_width": 2}
    draft = {
        "schema_version": "sketch2life.presentation-svg-draft.v1",
        "review_required": True,
        "viewbox": [0, 0, 100, 100],
        "shapes": [
            {"kind": "circle", **style, "cx": 25, "cy": 25, "r": 10},
            {"kind": "rect", **style, "x": 40, "y": 10, "w": 20, "h": 15},
            {"kind": "line", **style, "x1": 10, "y1": 60, "x2": 30, "y2": 60},
            {"kind": "ellipse", **style, "cx": 70, "cy": 70, "rx": 10, "ry": 8},
        ],
    }

    drawing = drawing_module.drawing_from_ai_draft(draft)

    assert drawing is not None
    assert drawing["source"] == "ai_draft"
    assert len(drawing["strokes"]) == 4
    assert len(drawing["sha256"]) == 64


def test_missing_drawing_preserves_text_steps_for_ready_validation() -> None:
    steps = _steps(4)

    result = drawing_module.attach_progressive_drawing(steps, None)

    assert result == steps
    assert all(step.child_facing_prompt for step in result)


class _FakeResult:
    def __init__(self, row: Any) -> None:
        self.row = row

    def mappings(self) -> _FakeResult:
        return self

    def one_or_none(self) -> Any:
        return self.row


class _FakeDb:
    def __init__(self, revision: dict[str, Any]) -> None:
        self.revision = revision
        self.inserted_steps: list[dict[str, Any]] = []
        self.committed = False

    def execute(self, statement: Any) -> _FakeResult:
        if getattr(statement, "table", None) is SKETCH_DECK_STEPS and statement.is_insert:
            self.inserted_steps.append(
                {
                    getattr(column, "name", column): getattr(value, "value", value)
                    for column, value in statement._values.items()
                }
            )
            return _FakeResult(None)
        if isinstance(statement, Select) and SKETCH_DECK_REVISIONS in statement.get_final_froms():
            return _FakeResult(self.revision)
        if isinstance(statement, Select):
            return _FakeResult(SimpleNamespace(plan_revision_id="plan-1", content_hash="a" * 64))
        return _FakeResult(None)

    def scalar(self, _statement: Any) -> None:
        return None

    def scalars(self, _statement: Any) -> SimpleNamespace:
        return SimpleNamespace(all=lambda: [])

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        pass


@pytest.mark.parametrize("with_drawing", [False, True])
def test_complete_generation_stores_and_returns_drawing_hints_or_ready_text_only(
    monkeypatch: pytest.MonkeyPatch, with_drawing: bool
) -> None:
    revision = {
        "sketch_deck_revision_id": "deck-1",
        "occurrence_id": "occurrence-1",
        "plan_revision_id": "plan-1",
        "revision_no": 1,
        "state": "GENERATING",
        "review_confirmed": True,
        "topic": "Tree",
        "drawing_steps": [{"action": "draw", "placement": "page"}] * 4,
        "subject_knowledge": ["Trees have leaves."],
    }
    db = _FakeDb(revision)
    service = SketchDeckRevisionService(db)  # type: ignore[arg-type]
    monkeypatch.setattr(sketch_decks_module, "authorize_occurrence", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        service,
        "_revision_body",
        lambda *_args, **kwargs: {"state": kwargs["state"], "content_hash": kwargs["content_hash"]},
    )
    monkeypatch.setattr(service, "_finish_receipt", lambda **_kwargs: None)
    drawing = drawing_module._make_drawing(
        [0, 0, 100, 100], [_stroke(index) for index in range(4)], "recipe"
    )
    assert drawing is not None
    generation = SketchDeckGenerationStart(
        sketch_deck_revision_id="deck-1",
        revision_no=1,
        occurrence_id="occurrence-1",
        plan_revision_id="plan-1",
        plan_content_hash="a" * 64,
        target_age_band="age-36-71-months-v1",
        plan_activity_ids=("activity-a",),
        drawing=drawing if with_drawing else None,
    )
    worker_deck = {
        "schema_version": "sketch2life.teacher-sketch-deck.v1",
        "review_required": True,
        "topic": "Tree",
        "approved_activity_refs": ["activity-a"],
        "slides": [
            {
                "kind": "drawing_guide",
                "steps": [
                    {"step_index": index, "instruction": f"Draw {index}", "placement": "page"}
                    for index in range(1, 5)
                ],
            }
        ],
    }

    result = service.complete_generation(
        principal=VerifiedPrincipal(subject="teacher", issuer="test", roles=frozenset()),
        generation=generation,
        idempotency_key="request-1",
        deck=worker_deck,
    )

    assert result.body["state"] == "READY"
    assert db.committed is True
    assert len(db.inserted_steps) == 4
    persisted = sorted(db.inserted_steps, key=lambda row: row["step_index"])
    returned = [
        service._step_body({**row, "state": "READY", "created_at": datetime.now(UTC)})
        for row in persisted
    ]
    if with_drawing:
        hints = [step["bounded_layout_hints"]["drawing"] for step in returned]
        assert [len(hint["strokes"]) for hint in hints] == [1, 1, 1, 1]
        assert all(hint["sha256"] == drawing["sha256"] for hint in hints)
        assert all(step["line_sketch_asset_ref"] is None for step in returned)
    else:
        assert all("drawing" not in step["bounded_layout_hints"] for step in returned)


@pytest.mark.parametrize("slide_count", [4, 6, 8])
def test_recipe_strokes_are_split_by_whole_recipe_steps_with_their_words(slide_count: int) -> None:
    recipe_steps = [
        {"stroke_count": count, "instruction": f"Vẽ phần {index}"}
        for index, count in enumerate((2, 1, 3, 1, 2, 1), start=1)
    ]
    strokes = [_stroke(index) for index in range(10)]

    groups = drawing_module._split_recipe_steps(strokes, recipe_steps, slide_count)

    assert len(groups) == slide_count
    assert [stroke for group, _ in groups for stroke in group] == strokes
    boundaries = {0, 2, 3, 6, 7, 9, 10}
    offset = 0
    for group, caption in groups:
        offset += len(group)
        assert offset in boundaries  # a recipe step is never cut in two
        assert bool(caption) is bool(group)
    assert " ".join(caption for _, caption in groups if caption) == " ".join(
        f"Vẽ phần {index}." for index in range(1, 7)
    )


def test_a_real_recipe_carries_its_words_into_the_step_hints() -> None:
    drawing = drawing_module._recipe_drawing("con mèo")
    assert drawing is not None
    assert sum(step["stroke_count"] for step in drawing["recipe_steps"]) == len(drawing["strokes"])
