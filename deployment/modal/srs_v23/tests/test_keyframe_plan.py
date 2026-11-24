"""FEAT-087 M5: keyframe plan (manifest block), render modes and LTX conditioning decisions."""

from __future__ import annotations

import sys
from copy import deepcopy
from pathlib import Path

import pytest

MODAL_DIR = Path(__file__).resolve().parents[1]
if str(MODAL_DIR) not in sys.path:
    sys.path.insert(0, str(MODAL_DIR))

import keyframe_plan as kp
import story_staging_worker as ss


def _staging(scene_count=5, states=("unchanged",) * 3 + ("partly_gone", "gone")):
    return {
        "schema_version": ss.STAGING_SCHEMA,
        "scenes": [
            {
                "scene_index": i,
                "main_end": {
                    "position": "left-middle",
                    "facing": "right",
                    "scale": "same",
                },
                "secondary_end": [{"entity_id": "sec-1", "state": states[i - 1]}],
            }
            for i in range(1, scene_count + 1)
        ],
    }


def _plan(**over):
    plan = {
        "schema_version": kp.KEYFRAME_PLAN_SCHEMA,
        "render_mode": "keyframe",
        "fallback_reason": None,
        "source_facing": "right",
        "main": {"entity_id": "subject-main", "box": [2, 6, 12, 16]},
        "secondaries": [{"entity_id": "sec-1", "box": [14, 9, 19, 15]}],
        "staging": _staging(),
    }
    plan.update(over)
    return plan


def test_a_valid_keyframe_plan_passes() -> None:
    plan = _plan()
    assert kp.validate_keyframe_plan(plan, scene_count=5) is plan


def test_a_fallback_plan_needs_a_reason_and_may_have_no_boxes_or_staging() -> None:
    plan = _plan(
        render_mode="fallback",
        fallback_reason="KEYFRAME_NO_BOXES",
        main=None,
        secondaries=[],
        staging=None,
        source_facing=None,
    )
    assert kp.validate_keyframe_plan(plan, scene_count=5) is plan
    plan["fallback_reason"] = None
    with pytest.raises(kp.KeyframePlanError) as e:
        kp.validate_keyframe_plan(plan, scene_count=5)
    assert e.value.code == "KEYFRAME_PLAN_INVALID"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: p.update(render_mode="auto"),
        lambda p: p.update(extra=1),
        lambda p: p.update(source_facing="up"),
        lambda p: p["main"].update(box=[2, 6, 12]),
        lambda p: p["main"].update(box=[12, 6, 2, 16]),
        lambda p: p["main"].update(box=[0, 0, 21, 5]),
        lambda p: p["main"].update(box=[2, 6, 4, 8]),  # smaller than 4x4 cells
        lambda p: p["main"].update(entity_id="main"),
        lambda p: p["secondaries"].append({"entity_id": "sec-1", "box": [1, 1, 8, 8]}),
        lambda p: p.update(
            secondaries=[
                {"entity_id": f"sec-{i}", "box": [1, 1, 8, 8]} for i in range(1, 5)
            ]
        ),
        lambda p: p.update(staging=None),
        lambda p: p["staging"]["scenes"].pop(),
        lambda p: p["staging"]["scenes"][0]["secondary_end"][0].update(
            entity_id="sec-2"
        ),
        lambda p: p.update(fallback_reason="X"),
    ],
)
def test_malformed_keyframe_plans_are_rejected(mutate) -> None:
    plan = deepcopy(_plan())
    mutate(plan)
    with pytest.raises(kp.KeyframePlanError):
        kp.validate_keyframe_plan(plan, scene_count=5)


def test_keyframe_mode_conditions_each_scene_on_its_own_start_and_end_keyframes() -> (
    None
):
    cond = kp.scene_conditioning("keyframe", scene_index=3, scene_count=5)
    assert cond == {
        "start_keyframe": 2,
        "end_keyframe": 3,
        "start_strength": 1.0,
        "end_strength": kp.END_FRAME_STRENGTH,
    }
    first = kp.scene_conditioning("keyframe", scene_index=1, scene_count=5)
    assert first["start_keyframe"] == 0 and first["end_keyframe"] == 1


def test_fallback_mode_always_starts_from_the_original_and_has_no_end_frame() -> None:
    for i in range(1, 6):
        cond = kp.scene_conditioning("fallback", scene_index=i, scene_count=5)
        assert cond == {
            "start_keyframe": 0,
            "end_keyframe": None,
            "start_strength": 1.0,
            "end_strength": None,
        }


def test_the_end_frame_is_a_soft_guide_not_a_hard_replace() -> None:
    assert 0.5 <= kp.END_FRAME_STRENGTH < 1.0


def test_grid_boxes_map_onto_the_canvas_through_the_drawing_transform() -> None:
    import keyframe_compositor as kc

    transform = kc.CanvasTransform(scale=0.5, offset_x=100, offset_y=50)
    # a 1000x800 source drawing; grid 0..20 over the source
    assert kp.grid_box_to_canvas(
        [0, 0, 20, 20], source_size=(1000, 800), transform=transform
    ) == (
        100,
        50,
        600,
        450,
    )
    assert kp.grid_box_to_canvas(
        [10, 5, 20, 10], source_size=(1000, 800), transform=transform
    ) == (
        350,
        150,
        600,
        250,
    )
