"""The Teacher Sketch Deck worker must accept exactly what the backend sends."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

_MODAL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_MODAL_DIR))
_SPEC = importlib.util.spec_from_file_location(
    "sketch2life_modal_teacher_ai_action_inputs", _MODAL_DIR / "language_audio_app.py"
)
assert _SPEC is not None and _SPEC.loader is not None
worker = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(worker)


def _deck(step_count: int, *, drawing_subject: bool) -> dict[str, Any]:
    plan: dict[str, Any] = {
        "schema_version": "sketch2life.teacher-deck-input.v1",
        "plan_revision_ref": "plan-1",
        "topic": "Con bướm",
        "target_age_months": 54,
        "objectives": ["Quan sát"],
        "drawing_steps": [
            {"step_index": index, "action": "Vẽ một nét", "placement": "Giữa trang"}
            for index in range(1, step_count + 1)
        ],
        "subject_knowledge": ["Bướm có hai cánh"],
        "activities": [
            {"activity_ref": "a1", "title": "Quan sát", "description": "Cùng quan sát"}
        ],
    }
    if drawing_subject:
        plan["drawing_subject"] = "Con bướm"
    digest = hashlib.sha256(
        json.dumps(plan, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return {**plan, "content_hash": digest}


@pytest.mark.parametrize("step_count", [4, 8])
@pytest.mark.parametrize("drawing_subject", [True, False])
def test_deck_input_accepts_the_reviewed_four_to_eight_steps(
    step_count: int, drawing_subject: bool
) -> None:
    worker._validate_teacher_deck_input(_deck(step_count, drawing_subject=drawing_subject))
    assert worker._teacher_deck_max_output_tokens(step_count) > 0


def test_deck_input_still_rejects_three_steps() -> None:
    with pytest.raises(worker.WorkerContractError):
        worker._validate_teacher_deck_input(_deck(3, drawing_subject=True))
