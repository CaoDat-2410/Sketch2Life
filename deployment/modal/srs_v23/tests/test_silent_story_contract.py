from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import story_visual_plan

MODAL_DIR = Path(__file__).resolve().parents[1]
if str(MODAL_DIR) not in sys.path:
    sys.path.insert(0, str(MODAL_DIR))

SPEC = importlib.util.spec_from_file_location(
    "sketch2life_modal_video_story_contract",
    MODAL_DIR / "video_app.py",
)
assert SPEC is not None and SPEC.loader is not None
video_worker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(video_worker)


def _manifest() -> dict:
    story_sha256 = "a" * 64
    scenes = [
        {
            "scene_id": f"scene-{index}",
            "scene_index": index,
            "title": f"Scene {index}",
            "action": f"Approved action {index}.",
            "visual_prompt": f"Old descriptive prompt {index}.",
            "duration_seconds": 6.0,
            "seed": 100 + index,
            "confirmed_anchor_ids": ["source subject"],
        }
        for index in range(1, 6)
    ]
    visual_plan = {
        "schema_version": story_visual_plan.STORY_VISUAL_PLAN_SCHEMA,
        "source_story_sha256": story_sha256,
        "entities": [
            {
                "entity_id": "subject-main",
                "kind": "subject",
                "source": "source_drawing",
                "label": "the original subject",
                "appearance": "Preserve this exact subject from the source drawing.",
            },
            {
                "entity_id": "prop-leaf",
                "kind": "prop",
                "source": "story_directed",
                "label": "one leaf",
                "appearance": "One broad green leaf with a simple stem and outline.",
            },
        ],
        "scenes": [],
    }
    for index, scene in enumerate(scenes, start=1):
        visible = ["subject-main"] + (["prop-leaf"] if index >= 2 else [])
        visual_plan["scenes"].append(
            {
                "scene_id": scene["scene_id"],
                "approved_action": scene["action"],
                "duration_seconds": scene["duration_seconds"],
                "visible_entity_ids": visible,
                "introduced_entity_ids": ["prop-leaf"] if index == 2 else [],
                "removed_entity_ids": [],
                "continuity_in": "Continue the prior final pose and entity state.",
                "continuity_out": "Keep the subject and required props in the next scene.",
                "spatial_direction": "Keep the leaf beside the subject.",
                "model_action_instruction": (
                    f"Faithfully animate approved action {index} as one slow, readable motion."
                ),
                "camera_motion": "locked",
            }
        )
    manifest = {
        "schema_version": video_worker.STORY_INPUT_SCHEMA,
        "story_revision_id": "revision-1",
        "story_sha256": story_sha256,
        "storyboard_sha256": "b" * 64,
        "source_drawing_ref": "input/drawing.png",
        "source_drawing_sha256": "c" * 64,
        "target_duration_seconds": 30.0,
        "scene_count": len(scenes),
        "scenes": scenes,
        "scene_visual_plan": visual_plan,
    }
    render_plan_payload = {
        "schema_version": manifest["schema_version"],
        "story_revision_id": manifest["story_revision_id"],
        "story_sha256": manifest["story_sha256"],
        "storyboard_sha256": manifest["storyboard_sha256"],
        "source_drawing_sha256": manifest["source_drawing_sha256"],
        "target_duration_seconds": manifest["target_duration_seconds"],
        "scenes": scenes,
        "scene_visual_plan": visual_plan,
    }
    manifest["render_plan_sha256"] = video_worker.canonical_sha256(render_plan_payload)
    return manifest


def _parse(manifest: dict) -> dict:
    return video_worker._parse_story_input(
        json.dumps(
            manifest, ensure_ascii=True, sort_keys=True, separators=(",", ":")
        ).encode()
    )


def test_story_contract_keeps_confirmed_storyboard_and_hashes_render_plan_separately() -> (
    None
):
    manifest = _manifest()

    parsed = _parse(manifest)

    assert parsed["storyboard_sha256"] == "b" * 64
    assert parsed["render_plan_sha256"] == manifest["render_plan_sha256"]


def test_story_contract_requires_versioned_visual_plan_for_legacy_input() -> None:
    manifest = _manifest()
    manifest["schema_version"] = "sketch2life.modal.silent-story-video-input.v1"

    with pytest.raises(video_worker.WorkerContractError) as error:
        _parse(manifest)

    assert str(error.value) == "VIDEO_STORY_VISUAL_PLAN_REQUIRED"


def test_story_contract_rejects_action_that_does_not_match_confirmed_story() -> None:
    manifest = _manifest()
    manifest["scene_visual_plan"]["scenes"][1]["approved_action"] = "Different action."
    render_plan = {
        "schema_version": manifest["schema_version"],
        "story_revision_id": manifest["story_revision_id"],
        "story_sha256": manifest["story_sha256"],
        "storyboard_sha256": manifest["storyboard_sha256"],
        "source_drawing_sha256": manifest["source_drawing_sha256"],
        "target_duration_seconds": manifest["target_duration_seconds"],
        "scenes": manifest["scenes"],
        "scene_visual_plan": manifest["scene_visual_plan"],
    }
    manifest["render_plan_sha256"] = video_worker.canonical_sha256(render_plan)

    with pytest.raises(video_worker.WorkerContractError) as error:
        _parse(manifest)

    assert str(error.value) == "VIDEO_STORY_VISUAL_TRANSITION_INVALID"


def test_story_contract_rejects_manifest_tampering_after_render_hash() -> None:
    manifest = _manifest()
    manifest["scenes"][1]["title"] = "Tampered title"

    with pytest.raises(video_worker.WorkerContractError) as error:
        _parse(manifest)

    assert str(error.value) == "VIDEO_STORY_RENDER_PLAN_HASH_MISMATCH"


def test_story_contract_requires_exact_frame_alignment_with_total_runtime() -> None:
    manifest = _manifest()
    for index, duration in ((0, 5.98), (1, 5.98), (2, 6.04)):
        manifest["scenes"][index]["duration_seconds"] = duration
        manifest["scene_visual_plan"]["scenes"][index]["duration_seconds"] = duration
    render_plan = {
        "schema_version": manifest["schema_version"],
        "story_revision_id": manifest["story_revision_id"],
        "story_sha256": manifest["story_sha256"],
        "storyboard_sha256": manifest["storyboard_sha256"],
        "source_drawing_sha256": manifest["source_drawing_sha256"],
        "target_duration_seconds": manifest["target_duration_seconds"],
        "scenes": manifest["scenes"],
        "scene_visual_plan": manifest["scene_visual_plan"],
    }
    manifest["render_plan_sha256"] = video_worker.canonical_sha256(render_plan)

    with pytest.raises(video_worker.WorkerContractError) as error:
        _parse(manifest)

    assert str(error.value) == "VIDEO_STORY_TIMELINE_FRAME_ALIGNMENT_INVALID"


def test_story_output_echoes_the_source_drawing_hash_and_confirmed_story_hashes() -> None:
    manifest = _manifest()
    request = SimpleNamespace(
        job_id="job-1", generation_id="generation-1", attempt_id="attempt-1"
    )

    result = video_worker._build_silent_story_output_payload(
        request,
        manifest,
        output_sha256="d" * 64,
        output_size_bytes=1234,
        output_manifest_sha256="e" * 64,
        final_details={
            "duration_seconds": 30.0,
            "width": 1280,
            "height": 720,
            "fps": 24.0,
            "video_codec": "h264",
            "audio_streams": 0,
        },
        runtime={},
    )

    assert result["source_drawing_sha256"] == manifest["source_drawing_sha256"]
    assert result["story_sha256"] == manifest["story_sha256"]
    assert result["storyboard_sha256"] == manifest["storyboard_sha256"]
    assert result["status"] == "CANDIDATE_READY"
    assert result["product_playable"] is False
