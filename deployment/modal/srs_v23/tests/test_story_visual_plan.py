from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "story_visual_plan.py"
SPEC = importlib.util.spec_from_file_location("story_visual_plan", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
visual_plan_module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = visual_plan_module
SPEC.loader.exec_module(visual_plan_module)


def _case() -> tuple[str, list[dict], dict]:
    story_sha256 = "a" * 64
    scenes = [
        {
            "scene_id": f"scene-{index}",
            "scene_index": index,
            "action": f"Approved turtle action {index}.",
            "duration_seconds": 6.0,
        }
        for index in range(1, 6)
    ]
    plan = {
        "schema_version": visual_plan_module.STORY_VISUAL_PLAN_SCHEMA,
        "source_story_sha256": story_sha256,
        "entities": [
            {
                "entity_id": "subject-main",
                "kind": "subject",
                "source": "source_drawing",
                "label": "the child-drawn turtle",
                "appearance": "Preserve the exact subject from the original drawing.",
            },
            {
                "entity_id": "prop-leaf",
                "kind": "prop",
                "source": "story_directed",
                "label": "one green leaf",
                "appearance": "A single broad green leaf with a short stem, simple 2D.",
            },
        ],
        "scenes": [],
    }
    for index, scene in enumerate(scenes, start=1):
        visible = ["subject-main"] + (["prop-leaf"] if index >= 2 else [])
        plan["scenes"].append(
            {
                "scene_id": scene["scene_id"],
                "approved_action": scene["action"],
                "duration_seconds": scene["duration_seconds"],
                "visible_entity_ids": visible,
                "introduced_entity_ids": ["prop-leaf"] if index == 2 else [],
                "removed_entity_ids": [],
                "continuity_in": "The turtle starts in the preceding scene's final pose.",
                "continuity_out": "The turtle settles in a pose that can continue next.",
                "spatial_direction": "Keep the leaf beside the turtle, clear of its outline.",
                "model_action_instruction": (
                    f"Faithfully animate the approved turtle action {index} with one clear, slow motion."
                ),
                "camera_motion": "locked",
            }
        )
    return story_sha256, scenes, plan


def test_visual_plan_validates_entity_introduction_and_persistence() -> None:
    story_sha256, scenes, plan = _case()

    actual = visual_plan_module.validate_story_visual_plan(
        plan, scenes=scenes, story_sha256=story_sha256
    )

    assert actual is plan


def test_visual_plan_rejects_prop_that_vanishes_without_scripted_removal() -> None:
    story_sha256, scenes, plan = _case()
    plan["scenes"][3]["visible_entity_ids"] = ["subject-main"]

    with pytest.raises(visual_plan_module.StoryVisualPlanError) as error:
        visual_plan_module.validate_story_visual_plan(
            plan, scenes=scenes, story_sha256=story_sha256
        )

    assert str(error.value) == "VIDEO_STORY_VISUAL_TRANSITION_INVALID"


def test_visual_plan_rejects_action_drift_from_adult_approved_scene() -> None:
    story_sha256, scenes, plan = _case()
    plan["scenes"][1]["approved_action"] = "A different action."

    with pytest.raises(visual_plan_module.StoryVisualPlanError) as error:
        visual_plan_module.validate_story_visual_plan(
            plan, scenes=scenes, story_sha256=story_sha256
        )

    assert str(error.value) == "VIDEO_STORY_VISUAL_TRANSITION_INVALID"


def test_prompt_uses_prior_scene_frame_and_requires_the_leaf() -> None:
    story_sha256, scenes, plan = _case()
    visual_plan_module.validate_story_visual_plan(
        plan, scenes=scenes, story_sha256=story_sha256
    )

    prompt = visual_plan_module.compile_scene_prompt(scenes[1], plan, first_scene=False)

    assert "last frame of the preceding scene" in prompt
    assert "Approved turtle action 2." in prompt
    assert "Entities that must remain visible" in prompt
    assert "one green leaf" in prompt
    assert "Faithfully animate the approved turtle action 2" in prompt
    assert "Camera is completely fixed" in prompt
    assert "same subject silhouette" in prompt
    assert "text, narration, subtitles" in prompt
    assert "Approved turtle action 3." not in prompt


def test_visual_plan_rejects_missing_model_action_instruction() -> None:
    story_sha256, scenes, plan = _case()
    plan["scenes"][0].pop("model_action_instruction")

    with pytest.raises(visual_plan_module.StoryVisualPlanError) as error:
        visual_plan_module.validate_story_visual_plan(
            plan, scenes=scenes, story_sha256=story_sha256
        )

    assert str(error.value) == "VIDEO_STORY_VISUAL_SCENE_INVALID"


@pytest.mark.parametrize(
    ("duration", "expected_target", "expected_generated"),
    [(6.0, 144, 145), (1.0, 24, 25), (20.0, 480, 481), (6.25, 150, 153)],
)
def test_ltx_frame_plan_maps_nearest_valid_frame_grid_to_exact_duration(
    duration: float, expected_target: int, expected_generated: int
) -> None:
    result = visual_plan_module.plan_scene_frames(duration)

    assert result["target_frame_count"] == expected_target
    assert result["generated_frame_count"] == expected_generated
    assert (expected_generated - 1) % 8 == 0
    assert result["temporal_scale"] == pytest.approx(
        expected_target / expected_generated
    )


def test_frame_plan_rejects_nan_and_boolean_durations() -> None:
    for value in (float("nan"), True, 0):
        with pytest.raises(visual_plan_module.StoryVisualPlanError):
            visual_plan_module.plan_scene_frames(value)
