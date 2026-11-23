"""Contract checks for the Parent-to-LTX manifest adapter."""

from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

from sketch2life.application.ports.parent_video_candidates import (
    ParentVideoCandidateError,
    ParentVideoCandidateScene,
    ParentVideoCandidateSource,
)
from sketch2life.application.services.parent_video_candidate_service import (
    _build_input_manifest,
    _canonical_json,
    _nearest_model_frames,
)


def _source(*, scene_count: int = 5, scene_duration_ms: int = 6_000) -> ParentVideoCandidateSource:
    scenes = tuple(
        ParentVideoCandidateScene(
            scene_index=index,
            title=f"Cảnh {index}",
            action=f"Con rùa bước chậm qua khu vườn ở cảnh {index}.",
            visual_prompt="A small leaf drifts beside the turtle.",
            duration_ms=scene_duration_ms,
            character_anchors=("mai xanh", "chân ngắn"),
        )
        for index in range(1, scene_count + 1)
    )
    duration = scene_count * scene_duration_ms
    return ParentVideoCandidateSource(
        run_id="00000000-0000-4000-8000-000000000001",
        profile_id="synthetic-profile-1",
        story_revision_id="00000000-0000-4000-8000-000000000002",
        story_revision_no=1,
        story_sha256="a" * 64,
        story_duration_ms=duration,
        source_asset_ref="parent/test/drawing.png",
        source_asset_version=1,
        source_asset_sha256="b" * 64,
        source_media_type="image/png",
        source_size_bytes=1024,
        confirmed_subject="con rùa",
        activity_selection_id="00000000-0000-4000-8000-000000000003",
        activity_snapshot_sha256="c" * 64,
        scenes=scenes,
    )


def test_manifest_is_worker_v2_contract_and_frame_aligned() -> None:
    manifest = _build_input_manifest(_source())

    assert set(manifest) == {
        "schema_version",
        "story_revision_id",
        "story_sha256",
        "storyboard_sha256",
        "render_plan_sha256",
        "source_drawing_sha256",
        "target_duration_seconds",
        "scenes",
        "scene_visual_plan",
        "source_drawing_ref",
        "scene_count",
    }
    assert manifest["schema_version"] == "sketch2life.modal.silent-story-video-input.v2"
    assert manifest["source_drawing_ref"] == "input/drawing.png"
    assert manifest["scene_count"] == 5
    assert len(manifest["scenes"]) == 5
    assert manifest["scenes"][0]["action"].startswith("Con rùa bước")
    assert manifest["scenes"][0]["visual_prompt"] == "A small leaf drifts beside the turtle."

    frame_counts = [round(scene["duration_seconds"] * 24) for scene in manifest["scenes"]]
    assert all(
        frames == _nearest_model_frames(scene["duration_seconds"])
        for frames, scene in zip(frame_counts, manifest["scenes"], strict=True)
    )
    assert sum(frame_counts) == round(manifest["target_duration_seconds"] * 24)
    assert 30 <= manifest["target_duration_seconds"] <= 90
    assert all(1 <= scene["duration_seconds"] <= 20 for scene in manifest["scenes"])
    assert all(
        scene["visual_prompt"] == scene_plan["model_action_instruction"]
        for scene, scene_plan in zip(
            manifest["scenes"], manifest["scene_visual_plan"]["scenes"], strict=True
        )
    )
    assert (
        hashlib.sha256(
            _canonical_json(
                {
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
                    )
                }
            )
        ).hexdigest()
        == manifest["render_plan_sha256"]
    )


def test_manifest_keeps_long_story_inside_worker_duration_limit() -> None:
    manifest = _build_input_manifest(_source(scene_count=15))
    frame_counts = [round(scene["duration_seconds"] * 24) for scene in manifest["scenes"]]

    assert 30 <= manifest["target_duration_seconds"] <= 90
    assert sum(frame_counts) == round(manifest["target_duration_seconds"] * 24)
    assert len(manifest["scenes"]) == 15


def test_manifest_rejects_story_and_scene_timeline_mismatch() -> None:
    source = _source()
    mismatched = replace(source, story_duration_ms=source.story_duration_ms + 500)

    with pytest.raises(ParentVideoCandidateError, match="VIDEO_STORY_TIMELINE_INVALID"):
        _build_input_manifest(mismatched)
