from __future__ import annotations

import pytest
from pydantic import ValidationError
from sketch2life.contracts.schemas.ai_story import (
    ParentStoryGenerationRequest,
    StoryRevisionDraftV1,
    validate_butterfly_lifecycle_v1,
)
from sketch2life.contracts.schemas.story_run_lite import CreateRunRequest


def _story(*, incorrect_lifecycle: bool = False) -> dict[str, object]:
    story_text = {
        "opening": "Trên chiếc lá có một chấm trứng nhỏ.",
        "middle": "Trứng nở thành sâu bướm. Sâu bướm ăn lá, lớn lên rồi hóa nhộng.",
        "ending": (
            "Bướm trưởng thành chui ra khỏi nhộng và bay đến bông hoa."
            if not incorrect_lifecycle
            else "Trứng nở thành bướm. Bướm đi tìm tổ trên cành cây."
        ),
    }
    return {
        "schema_version": "sketch2life.story-revision.v1",
        "language": "vi",
        "title": "Hành trình của bướm",
        "story": story_text,
        "duration_ms": 30_000,
        "scenes": [
            {
                "scene_index": index,
                "title": f"Cảnh {index}",
                "action": "Một chấm trứng nằm trên chiếc lá."
                if index == 1
                else "Sâu bướm quan sát chiếc lá.",
                "visual_prompt": "Đường nét cánh bướm đơn giản, giữ nguyên hình dáng tranh.",
                "narration": "Cùng quan sát chiếc lá.",
                "start_ms": (index - 1) * 6_000,
                "duration_ms": 6_000,
                "character_anchors": ["viền cánh tròn", "thân bướm mảnh"],
            }
            for index in range(1, 6)
        ],
    }


def test_parent_story_generation_request_rejects_activity_selection_and_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        ParentStoryGenerationRequest.model_validate(
            {"expected_understanding_revision": 1, "activities": ["ACT-01"]}
        )


def test_create_run_requires_exact_child_age_instead_of_silently_assuming_five_years() -> None:
    with pytest.raises(ValidationError):
        CreateRunRequest.model_validate({"profile_ref": "synthetic-parent-demo"})
    assert (
        CreateRunRequest.model_validate(
            {"profile_ref": "synthetic-parent-demo", "child_age_months": 48}
        ).child_age_months
        == 48
    )


def test_story_revision_requires_ordered_scenes_and_total_duration_between_30_and_90_seconds() -> (
    None
):
    parsed = StoryRevisionDraftV1.model_validate(_story())
    assert len(parsed.scenes) == 5
    assert parsed.duration_ms == 30_000

    invalid = _story()
    invalid["scenes"][2]["start_ms"] = 1_000
    with pytest.raises(ValidationError, match="sequential"):
        StoryRevisionDraftV1.model_validate(invalid)


def test_butterfly_fact_guard_accepts_lifecycle_and_rejects_prior_errors() -> None:
    valid = StoryRevisionDraftV1.model_validate(_story())
    validate_butterfly_lifecycle_v1(valid, confirmed_subject="bướm")

    invalid = StoryRevisionDraftV1.model_validate(_story(incorrect_lifecycle=True))
    with pytest.raises(ValueError, match="EDUCATIONAL_FACT_CHECK_FAILED"):
        validate_butterfly_lifecycle_v1(invalid, confirmed_subject="butterfly")


@pytest.mark.parametrize(
    "incorrect_claim",
    ["Trứng nở thành bướm trưởng thành.", "Bướm trưởng thành đi tìm tổ."],
)
def test_butterfly_fact_guard_rejects_wrong_claim_even_when_all_phases_are_present(
    incorrect_claim: str,
) -> None:
    payload = _story()
    payload["story"]["ending"] += " " + incorrect_claim
    draft = StoryRevisionDraftV1.model_validate(payload)
    with pytest.raises(ValueError, match="EDUCATIONAL_FACT_CHECK_FAILED"):
        validate_butterfly_lifecycle_v1(draft, confirmed_subject="bướm")


def test_story_scene_count_is_bounded_to_srs_range() -> None:
    invalid = _story()
    invalid["scenes"] = invalid["scenes"][:4]
    with pytest.raises(ValidationError):
        StoryRevisionDraftV1.model_validate(invalid)
