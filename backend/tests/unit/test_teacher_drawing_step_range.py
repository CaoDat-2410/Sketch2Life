"""SRS AC-34 / FR-T-18 (Rev66): the Teacher drawing guide takes 4 to 8 steps."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from sketch2life.contracts.schemas.modal_ai import TeacherReviewedPlanRequestV1


def _plan(steps: int) -> dict[str, object]:
    return {
        "review_confirmed": True,
        "plan_revision_ref": "plan-1",
        "topic": "Butterfly",
        "target_age_months": 72,
        "objectives": ["Draw wings"],
        "drawing_steps": [{"action": f"Step {n}", "placement": "centre"} for n in range(steps)],
        "subject_knowledge": ["Butterflies have four wings"],
        "activities": [
            {
                "activity_ref": "activity-1",
                "title": "Colour wings",
                "goal": "Colour",
                "materials": "Crayons",
                "preparation": "None",
                "instructions": "Colour the wings",
                "safety_notes": "None",
            }
        ],
    }


@pytest.mark.parametrize("steps", [4, 6, 8])
def test_the_plan_accepts_four_to_eight_steps(steps: int) -> None:
    assert len(TeacherReviewedPlanRequestV1.model_validate(_plan(steps)).drawing_steps) == steps


@pytest.mark.parametrize("steps", [3, 9])
def test_the_plan_rejects_steps_outside_the_range(steps: int) -> None:
    with pytest.raises(ValidationError):
        TeacherReviewedPlanRequestV1.model_validate(_plan(steps))
