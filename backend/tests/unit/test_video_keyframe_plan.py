"""FEAT-087 M5: the backend builds the worker's keyframe_plan from approved roles + staging."""

from __future__ import annotations

import hashlib
import json

import pytest

from sketch2life.application.parent_subject_roles import apply_subject_roles, normalize_worker_candidate
from sketch2life.application.ports.parent_video_candidates import (
    KeyframeInputs,
    KeyframeSecondary,
)
from sketch2life.application.services.parent_video_candidate_service import (
    _build_input_manifest,
    _canonical_json,
)
from sketch2life.application.story_staging import STAGING_SCHEMA, pack_story_content
from sketch2life.application.video_keyframe_plan import (
    build_keyframe_plan,
    keyframe_inputs_from,
)

from tests.unit.test_parent_video_candidate_manifest import _source


def _candidate(approve_leaf: bool = True) -> dict:
    candidate = normalize_worker_candidate(
        {
            "understanding_schema": "sketch2life.drawing-understanding.v2",
            "main_subject": {
                "label": "con rùa",
                "visible_features": ["mai ba ô tròn"],
                "facing": "right",
                "box": [2, 6, 12, 16],
            },
            "secondary_subjects": [
                {"label": "chiếc lá", "visible_features": [], "box": [14, 9, 19, 15]},
                {"label": "con bướm", "visible_features": [], "box": [13, 1, 18, 6]},
            ],
            "confidence": 0.8,
            "candidate_subject": "con rùa",
            "visible_features": ["mai ba ô tròn"],
        }
    )
    roles = [
        {"entity_id": "main", "label": "con rùa", "role": "main"},
        {
            "entity_id": "sec-1",
            "label": "chiếc lá",
            "role": "secondary" if approve_leaf else "excluded",
        },
        {"entity_id": "sec-2", "label": "con bướm", "role": "excluded"},
    ]
    return apply_subject_roles(candidate, roles)


def _staging(states=("unchanged", "unchanged", "unchanged", "partly_gone", "gone")) -> dict:
    return {
        "schema_version": STAGING_SCHEMA,
        "scenes": [
            {
                "scene_index": i,
                "main_end": {"position": "left-middle", "facing": "right", "scale": "same"},
                "secondary_end": [{"entity_id": "sec-1", "state": states[i - 1]}],
            }
            for i in range(1, 6)
        ],
    }


def _story_content(staging=None, issue=None) -> dict:
    return pack_story_content({"opening": "a", "middle": "b", "ending": "c"}, staging, issue)


def test_inputs_use_the_main_subject_and_only_the_secondaries_the_adult_approved() -> None:
    inputs = keyframe_inputs_from(_candidate(), _story_content(_staging()))
    assert inputs is not None
    assert inputs.main_box == (2, 6, 12, 16) and inputs.facing == "right"
    assert [(s.entity_id, s.label, s.box) for s in inputs.secondaries] == [
        ("sec-1", "chiếc lá", (14, 9, 19, 15))
    ]
    assert inputs.staging is not None and inputs.staging_issue is None


def test_unapproved_objects_never_reach_the_plan() -> None:
    inputs = keyframe_inputs_from(_candidate(approve_leaf=False), _story_content(None, "STAGING_ABSENT"))
    assert inputs is not None and inputs.secondaries == ()


def test_a_v1_candidate_has_no_boxes_so_there_are_no_inputs() -> None:
    v1 = {"candidate_subject": "con rùa", "visible_features": ["mai"], "confidence": 0.5}
    assert keyframe_inputs_from(v1, _story_content(_staging())) is None
    assert keyframe_inputs_from(None, None) is None


def test_a_good_input_builds_a_keyframe_mode_plan() -> None:
    plan = build_keyframe_plan(keyframe_inputs_from(_candidate(), _story_content(_staging())), scene_count=5)
    assert plan["schema_version"] == "sketch2life.keyframe-plan.v1"
    assert plan["render_mode"] == "keyframe" and plan["fallback_reason"] is None
    assert plan["source_facing"] == "right"
    assert plan["main"] == {"entity_id": "subject-main", "box": [2, 6, 12, 16]}
    assert plan["secondaries"] == [{"entity_id": "sec-1", "box": [14, 9, 19, 15]}]
    assert plan["staging"]["scenes"][4]["secondary_end"][0]["state"] == "gone"


@pytest.mark.parametrize(
    "inputs_factory, reason",
    [
        (lambda: None, "KEYFRAME_NO_BOXES"),
        (lambda: keyframe_inputs_from(_candidate(), _story_content(None, "STAGING_FIELD_INVALID")), "KEYFRAME_STAGING_FIELD_INVALID"),
        (lambda: keyframe_inputs_from(_candidate(), {"opening": "a", "middle": "b", "ending": "c"}), "KEYFRAME_STAGING_ABSENT"),
        (
            lambda: KeyframeInputs((2, 6, 4, 8), "right", (), _staging_empty(), None),
            "KEYFRAME_BOX_INVALID",
        ),
        (
            lambda: KeyframeInputs((2, 6, 12, 16), "right", (KeyframeSecondary("sec-1", "lá", (14, 9, 19, 15)),), _staging_empty(), None),
            "KEYFRAME_STAGING_INVALID",  # staging names no sec-1
        ),
    ],
)
def test_every_unusable_input_becomes_a_fallback_plan_with_a_reason(inputs_factory, reason) -> None:
    plan = build_keyframe_plan(inputs_factory(), scene_count=5)
    assert plan["render_mode"] == "fallback" and plan["fallback_reason"] == reason
    assert plan["staging"] is None and plan["secondaries"] == []


def _staging_empty() -> dict:
    return {
        "schema_version": STAGING_SCHEMA,
        "scenes": [
            {
                "scene_index": i,
                "main_end": {"position": "left-middle", "facing": "right", "scale": "same"},
                "secondary_end": [],
            }
            for i in range(1, 6)
        ],
    }


def test_the_manifest_carries_the_plan_and_a_v3_visual_plan_with_the_removal() -> None:
    source = _source()
    inputs = keyframe_inputs_from(_candidate(), _story_content(_staging()))
    manifest = _build_input_manifest(_with_inputs(source, inputs))
    assert manifest["keyframe_plan"]["render_mode"] == "keyframe"
    visual = manifest["scene_visual_plan"]
    assert visual["schema_version"] == "sketch2life.modal.story-visual-plan.v3"
    assert [(e["entity_id"], e["kind"]) for e in visual["entities"]] == [
        ("subject-main", "subject"),
        ("sec-1", "drawn_secondary"),
    ]
    assert visual["entities"][1]["label"].endswith("chiếc lá")
    removed = [scene["removed_entity_ids"] for scene in visual["scenes"]]
    assert removed == [[], [], [], [], ["sec-1"]]
    assert all("subject-main" in scene["visible_entity_ids"] for scene in visual["scenes"])
    assert visual["scenes"][4]["visible_entity_ids"] == ["subject-main"]
    assert visual["scenes"][3]["visible_entity_ids"] == ["subject-main", "sec-1"]  # partly gone is still there


def test_without_inputs_the_manifest_has_a_fallback_plan_and_the_old_visual_plan() -> None:
    manifest = _build_input_manifest(_source())
    assert manifest["keyframe_plan"]["render_mode"] == "fallback"
    assert manifest["keyframe_plan"]["fallback_reason"] == "KEYFRAME_NO_BOXES"
    assert manifest["scene_visual_plan"]["schema_version"] == "sketch2life.modal.story-visual-plan.v2"
    assert [e["entity_id"] for e in manifest["scene_visual_plan"]["entities"]] == ["subject-main"]


def test_the_render_plan_hash_covers_the_keyframe_plan() -> None:
    manifest = _build_input_manifest(_source())
    payload = {
        key: manifest[key]
        for key in (
            "schema_version",
            "story_revision_id",
            "story_sha256",
            "storyboard_sha256",
            "source_drawing_sha256",
            "target_duration_seconds",
            "scenes",
            "scene_visual_plan",
            "keyframe_plan",
        )
    }
    assert hashlib.sha256(_canonical_json(payload)).hexdigest() == manifest["render_plan_sha256"]
    assert json.loads(_canonical_json(payload))["keyframe_plan"]["render_mode"] == "fallback"


def _with_inputs(source, inputs):
    from dataclasses import replace

    return replace(source, keyframe_inputs=inputs)
