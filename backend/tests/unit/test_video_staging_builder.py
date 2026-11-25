"""FEAT-093: staging derived from typed interactions (any story, not one example)."""

from __future__ import annotations

import pytest

from sketch2life.application.video_pipeline.age_profile import profile_for_age_months
from sketch2life.application.video_pipeline.staging_builder import (
    StagingError,
    build_staging,
    cell_of,
)
from sketch2life.application.video_pipeline.story_timeline import parse_timeline
from sketch2life.application.video_pipeline.timeline_planner import assign_timing
from sketch2life.application.video_pipeline.video_plan import build_video_plan

PROFILE = profile_for_age_months(48)
BOXES = {"main": (2, 6, 11, 17), "sec-1": (13, 9, 19, 15)}  # turtle left, leaf right


def _plan(interactions_by_scene, secondary="sec-1"):
    scenes = []
    for index in range(5):
        scenes.append(
            {
                "title": f"Cảnh {index + 1}", "action": "Rùa đi.", "visual_prompt": "A turtle walks, crayon style.",
                "background_prompt": "A sunny garden, crayon texture.", "narration": "Rùa con bò đi.", "dialogue": [],
                "subjects": ["main", secondary], "interactions": interactions_by_scene.get(index, []),
            }
        )
    timeline = parse_timeline(
        assign_timing(PROFILE, {"title": "Rùa con", "scenes": scenes}), profile=PROFILE, entity_ids={"main", secondary}
    )
    return build_video_plan(timeline, story_sha256="a" * 64, main_entity_id="main")


def _consume(frm, to):
    return [{"kind": "consume", "actor": "main", "target": "sec-1", "verb": "ăn", "from_state": frm, "to_state": to}]


def test_cells_come_from_the_grid_centre() -> None:
    assert cell_of((2, 6, 11, 17)) == (0, 1)
    assert cell_of((13, 9, 19, 15)) == (2, 1)


def test_a_consume_ladder_walks_the_secondary_to_partly_gone_then_gone() -> None:
    plan = _plan({2: _consume(1.0, 0.5), 3: _consume(0.5, 0.25), 4: _consume(0.25, 0.0)})

    staging = build_staging(plan, subject_boxes=BOXES, secondary_ids=("sec-1",))

    states = [scene["secondary_end"][0]["state"] for scene in staging["scenes"]]
    assert states == ["unchanged", "unchanged", "partly_gone", "partly_gone", "gone"]
    assert staging["schema_version"] == "sketch2life.story-staging.v1"
    assert [scene["scene_index"] for scene in staging["scenes"]] == [1, 2, 3, 4, 5]


def test_the_main_subject_stands_beside_the_target_and_never_in_its_cell() -> None:
    plan = _plan({2: _consume(1.0, 0.5)})

    staging = build_staging(plan, subject_boxes=BOXES, secondary_ids=("sec-1",))

    scene = staging["scenes"][2]
    assert scene["main_end"]["position"] == "center-middle"
    assert scene["main_end"]["facing"] == "right"
    assert scene["main_end"]["position"] != "right-middle"


def test_a_transfer_moves_the_secondary_next_to_the_main_subject() -> None:
    plan = _plan(
        {1: [{"kind": "transfer", "actor": "main", "target": "sec-1", "verb": "nhặt", "from_state": 1.0, "to_state": 1.0}]}
    )

    staging = build_staging(plan, subject_boxes=BOXES, secondary_ids=("sec-1",))

    entry = staging["scenes"][1]["secondary_end"][0]
    assert entry["state"] == "moved" and entry["position"] != staging["scenes"][1]["main_end"]["position"]


def test_a_story_without_interactions_keeps_everything_in_place() -> None:
    plan = _plan({})

    staging = build_staging(plan, subject_boxes=BOXES, secondary_ids=("sec-1",))

    assert {scene["secondary_end"][0]["state"] for scene in staging["scenes"]} == {"unchanged"}
    assert {scene["main_end"]["position"] for scene in staging["scenes"]} == {"left-middle"}


def test_missing_boxes_are_reported() -> None:
    plan = _plan({})

    with pytest.raises(StagingError) as error:
        build_staging(plan, subject_boxes={"main": (2, 6, 11, 17)}, secondary_ids=("sec-1",))

    assert error.value.code == "STAGING_SUBJECT_BOX_MISSING"
