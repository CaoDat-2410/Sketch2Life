"""A deck built exactly as the Modal worker builds it must become storable READY steps."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest

from sketch2life.domain.lesson_occurrences.sketch_deck import (
    SketchDeckRuleError,
    validate_ready_steps,
)
from sketch2life.infrastructure.lesson_occurrences.sketch_decks import _steps_from_worker

_MODAL_DIR = Path(__file__).resolve().parents[3] / "deployment" / "modal" / "srs_v23"
sys.path.insert(0, str(_MODAL_DIR))
_SPEC = importlib.util.spec_from_file_location(
    "sketch2life_modal_deck_result", _MODAL_DIR / "language_audio_app.py"
)
assert _SPEC is not None and _SPEC.loader is not None
worker = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(worker)


def _worker_deck(activity_ids: list[str], step_count: int) -> dict[str, Any]:
    data = {
        "plan_revision_ref": "plan-1",
        "content_hash": "0" * 64,
        "topic": "Con bướm",
        "target_age_months": 54,
        "objectives": ["Quan sát"],
        "subject_knowledge": ["Bướm có hai cánh"],
        "activities": [
            {"activity_ref": ref, "title": "Quan sát", "description": "Cùng quan sát"}
            for ref in activity_ids
        ],
    }
    guide = [
        {"step_index": index, "instruction": f"Vẽ nét {index}", "placement": "Giữa trang"}
        for index in range(1, step_count + 1)
    ]
    return worker._compose_teacher_deck(data, guide)


@pytest.mark.parametrize("step_count", [4, 8])
def test_worker_deck_covers_every_plan_activity_with_ready_steps(step_count: int) -> None:
    activity_ids = [str(uuid4()), str(uuid4())]

    steps = validate_ready_steps(
        activity_ids, _steps_from_worker(_worker_deck(activity_ids, step_count), activity_ids)
    )

    assert len(steps) == 2 * step_count
    assert {step.plan_activity_id for step in steps} == set(activity_ids)
    assert {step.child_facing_prompt for step in steps} == {
        f"Vẽ nét {index}" for index in range(1, step_count + 1)
    }


@pytest.mark.parametrize(
    "damage",
    [
        lambda deck: deck.update(review_required=False),
        lambda deck: deck.update(approved_activity_refs=["another-activity"]),
        lambda deck: deck.update(slides=[]),
        lambda deck: deck["slides"][1]["steps"][0].update(step_index=2),
        lambda deck: deck["slides"][1]["steps"][0].pop("instruction"),
    ],
)
def test_a_malformed_worker_deck_fails_closed(damage: Any) -> None:
    activity_ids = [str(uuid4())]
    deck = _worker_deck(activity_ids, 4)
    damage(deck)

    with pytest.raises(SketchDeckRuleError):
        validate_ready_steps(activity_ids, _steps_from_worker(deck, activity_ids))


def test_fewer_than_four_guide_steps_are_not_ready() -> None:
    activity_ids = [str(uuid4())]

    with pytest.raises(SketchDeckRuleError):
        validate_ready_steps(
            activity_ids, _steps_from_worker(_worker_deck(activity_ids, 3), activity_ids)
        )
