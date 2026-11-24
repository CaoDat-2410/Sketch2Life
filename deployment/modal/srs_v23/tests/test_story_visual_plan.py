from __future__ import annotations

import importlib.util
import re
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


def test_prompt_uses_prior_frame_and_keeps_scene_action_grounded() -> None:
    story_sha256, scenes, plan = _case()
    visual_plan_module.validate_story_visual_plan(
        plan, scenes=scenes, story_sha256=story_sha256
    )

    prompt = visual_plan_module.compile_scene_prompt(scenes[1], plan, first_scene=False)

    assert "prior scene's final frame" in prompt
    assert "Approved turtle action 2" in prompt
    assert "One continuous" in prompt
    assert "one green leaf" in prompt
    assert "clear, physically plausible progression from beginning to result" in prompt
    assert "keep the camera fixed" in prompt
    assert "subject, silhouette, proportions, palette" in prompt
    assert "thumbnail, picture-in-picture, card, frame" in prompt
    assert "readable text, subtitles, logos, narration" in prompt
    assert "Approved turtle action 3." not in prompt


def test_compiled_ltx_prompt_has_detailed_action_and_7_to_8_sentence_flow() -> None:
    _, scenes, plan = _case()
    plan["scenes"][1]["model_action_instruction"] = (
        "At first, the turtle faces the leaf without moving. "
        "Then it slowly turns its head toward the leaf. "
        "The leaf bends once as the turtle gently touches its edge. "
        "Finally, the turtle settles beside the leaf and holds still."
    )

    prompt = visual_plan_module.compile_scene_prompt(
        scenes[1], plan, first_scene=False
    )
    sentence_count = len(re.findall(r"(?<=[.!?])\s+", prompt)) + 1

    assert sentence_count == 8
    assert "faces the leaf without moving" in prompt
    assert "slowly turns its head toward the leaf" in prompt
    assert "gently touches its edge" in prompt
    assert "settles beside the leaf and holds still" in prompt
    assert "single continuous" in prompt or "continuous" in prompt
    assert "no cuts" in prompt


def test_visual_plan_accepts_model_action_at_backend_limit() -> None:
    story_sha256, scenes, plan = _case()
    plan["scenes"][0]["model_action_instruction"] = "A" * 900

    visual_plan_module.validate_story_visual_plan(
        plan, scenes=scenes, story_sha256=story_sha256
    )


def test_visual_plan_rejects_model_action_over_backend_limit() -> None:
    story_sha256, scenes, plan = _case()
    plan["scenes"][0]["model_action_instruction"] = "A" * 901

    with pytest.raises(visual_plan_module.StoryVisualPlanError) as error:
        visual_plan_module.validate_story_visual_plan(
            plan, scenes=scenes, story_sha256=story_sha256
        )

    assert str(error.value) == "VIDEO_STORY_VISUAL_TRANSITION_INVALID"


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


# ---- FEAT-087 M5: visual plan v3 (drawn secondary objects) and prompt story-i2v-v8 ----------


def _v3_case(removed_in: int | None = 5) -> tuple[str, list[dict], dict]:
    story_sha256 = "b" * 64
    scenes = [
        {
            "scene_id": f"scene-{i}",
            "scene_index": i,
            "action": f"Approved turtle action {i}.",
            "duration_seconds": 6.0,
        }
        for i in range(1, 6)
    ]
    plan = {
        "schema_version": visual_plan_module.STORY_VISUAL_PLAN_SCHEMA_V3,
        "source_story_sha256": story_sha256,
        "entities": [
            {
                "entity_id": "subject-main",
                "kind": "subject",
                "source": "source_drawing",
                "label": "child-drawn turtle",
                "appearance": "Preserve the exact subject from the original drawing.",
            },
            {
                "entity_id": "sec-1",
                "kind": "drawn_secondary",
                "source": "source_drawing",
                "label": "drawn green leaf",
                "appearance": "The leaf exactly as drawn on the original page.",
            },
        ],
        "scenes": [],
    }
    for i, scene in enumerate(scenes, start=1):
        gone = removed_in is not None and i >= removed_in
        plan["scenes"].append(
            {
                "scene_id": scene["scene_id"],
                "approved_action": scene["action"],
                "duration_seconds": 6.0,
                "visible_entity_ids": ["subject-main"] if gone else ["subject-main", "sec-1"],
                "introduced_entity_ids": [],
                "removed_entity_ids": ["sec-1"] if removed_in == i else [],
                "continuity_in": "The turtle stands at the left of the page.",
                "continuity_out": "The turtle stands nearer the leaf.",
                "spatial_direction": "left to right",
                "model_action_instruction": "The turtle walks slowly toward the leaf and bites it.",
                "camera_motion": "locked",
            }
        )
    return story_sha256, scenes, plan


def test_v3_plan_accepts_a_drawn_secondary_that_is_removed_once() -> None:
    sha, scenes, plan = _v3_case()
    assert visual_plan_module.validate_story_visual_plan(plan, scenes=scenes, story_sha256=sha) is plan


def test_v3_plan_accepts_a_drawn_secondary_that_stays() -> None:
    sha, scenes, plan = _v3_case(removed_in=None)
    assert visual_plan_module.validate_story_visual_plan(plan, scenes=scenes, story_sha256=sha)


def test_v3_plan_rejects_a_removed_drawn_secondary_that_comes_back() -> None:
    sha, scenes, plan = _v3_case(removed_in=3)
    plan["scenes"][4].update(
        visible_entity_ids=["subject-main", "sec-1"], introduced_entity_ids=["sec-1"]
    )
    with pytest.raises(visual_plan_module.StoryVisualPlanError):
        visual_plan_module.validate_story_visual_plan(plan, scenes=scenes, story_sha256=sha)


def test_v3_plan_rejects_a_drawn_secondary_that_vanishes_without_a_removal_record() -> None:
    sha, scenes, plan = _v3_case(removed_in=None)
    plan["scenes"][3]["visible_entity_ids"] = ["subject-main"]
    with pytest.raises(visual_plan_module.StoryVisualPlanError):
        visual_plan_module.validate_story_visual_plan(plan, scenes=scenes, story_sha256=sha)


def test_v3_plan_limits_drawn_secondaries_to_three_and_requires_the_drawing_as_source() -> None:
    sha, scenes, plan = _v3_case(removed_in=None)
    plan["entities"][1]["source"] = "story_directed"
    with pytest.raises(visual_plan_module.StoryVisualPlanError):
        visual_plan_module.validate_story_visual_plan(plan, scenes=scenes, story_sha256=sha)
    sha, scenes, plan = _v3_case(removed_in=None)
    for n in (2, 3, 4):
        plan["entities"].append({**plan["entities"][1], "entity_id": f"sec-{n}", "label": f"thing {n}"})
        for s in plan["scenes"]:
            s["visible_entity_ids"].append(f"sec-{n}")
    with pytest.raises(visual_plan_module.StoryVisualPlanError):
        visual_plan_module.validate_story_visual_plan(plan, scenes=scenes, story_sha256=sha)


def test_v2_plans_cannot_smuggle_in_a_drawn_secondary() -> None:
    sha, scenes, plan = _v3_case(removed_in=None)
    plan["schema_version"] = visual_plan_module.STORY_VISUAL_PLAN_SCHEMA
    with pytest.raises(visual_plan_module.StoryVisualPlanError):
        visual_plan_module.validate_story_visual_plan(plan, scenes=scenes, story_sha256=sha)


def test_v8_prompt_describes_motion_between_two_frames_and_names_the_removed_object() -> None:
    sha, scenes, plan = _v3_case(removed_in=5)
    prompt = visual_plan_module.compile_keyframe_scene_prompt(scenes[4], plan)
    assert "first frame" in prompt and "last frame" in prompt
    assert "The turtle stands at the left of the page" in prompt
    assert "drawn green leaf" in prompt and "gone" in prompt
    assert "walks slowly toward the leaf" in prompt
    assert len(prompt) < 2_000
    for forbidden in ("Never", "Do not", "don't", "must not"):
        assert forbidden not in prompt, "v8 describes what to animate, it does not enumerate bans"
    assert prompt.rstrip().endswith("no text, no frame, no cuts.")


def test_v8_prompt_for_a_scene_that_removes_nothing_keeps_secondaries_still() -> None:
    sha, scenes, plan = _v3_case(removed_in=5)
    prompt = visual_plan_module.compile_keyframe_scene_prompt(scenes[1], plan)
    assert "drawn green leaf stays" in prompt and "gone" not in prompt


def test_the_prompt_template_versions_are_distinct() -> None:
    assert visual_plan_module.PROMPT_TEMPLATE_VERSION == "story-i2v-v7"
    assert visual_plan_module.KEYFRAME_PROMPT_TEMPLATE_VERSION == "story-i2v-v8"
