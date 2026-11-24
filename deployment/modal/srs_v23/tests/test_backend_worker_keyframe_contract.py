"""FEAT-087 M5: what the backend builds is exactly what the video worker accepts."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

MODAL_DIR = Path(__file__).resolve().parents[1]
BACKEND_SRC = MODAL_DIR.parents[2] / "backend" / "src"
for p in (str(MODAL_DIR), str(BACKEND_SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from sketch2life.application.parent_subject_roles import (
    apply_subject_roles,
    normalize_worker_candidate,
)
from sketch2life.application.ports.parent_video_candidates import (
    ParentVideoCandidateScene,
    ParentVideoCandidateSource,
)
from sketch2life.application.services.parent_video_candidate_service import (
    _build_input_manifest,
)
from sketch2life.application.story_staging import STAGING_SCHEMA, pack_story_content
from sketch2life.application.video_keyframe_plan import keyframe_inputs_from

SPEC = importlib.util.spec_from_file_location(
    "video_app_contract_x", MODAL_DIR / "video_app.py"
)
assert SPEC is not None and SPEC.loader is not None
video_app = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(video_app)


def _source(inputs):
    scenes = tuple(
        ParentVideoCandidateScene(
            scene_index=i,
            title=f"Cảnh {i}",
            action=f"Con rùa bước chậm ở cảnh {i}.",
            visual_prompt="The turtle walks slowly toward the leaf and keeps going.",
            duration_ms=6_000,
            character_anchors=("mai xanh",),
        )
        for i in range(1, 6)
    )
    return ParentVideoCandidateSource(
        run_id="00000000-0000-4000-8000-000000000001",
        profile_id="p",
        story_revision_id="00000000-0000-4000-8000-000000000002",
        story_revision_no=1,
        story_sha256="a" * 64,
        story_duration_ms=30_000,
        source_asset_ref="x",
        source_asset_version=1,
        source_asset_sha256="b" * 64,
        source_media_type="image/png",
        source_size_bytes=10,
        confirmed_subject="con rùa",
        activity_selection_id="00000000-0000-4000-8000-000000000003",
        activity_snapshot_sha256="c" * 64,
        scenes=scenes,
        keyframe_inputs=inputs,
    )


def _inputs(states, leaf_approved=True):
    candidate = normalize_worker_candidate(
        {
            "understanding_schema": "sketch2life.drawing-understanding.v2",
            "main_subject": {
                "label": "con rùa",
                "visible_features": ["mai"],
                "facing": "right",
                "box": [2, 6, 12, 16],
            },
            "secondary_subjects": [
                {"label": "chiếc lá", "visible_features": [], "box": [14, 9, 19, 15]}
            ],
            "confidence": 0.9,
            "candidate_subject": "con rùa",
            "visible_features": ["mai"],
        }
    )
    candidate = apply_subject_roles(
        candidate,
        [
            {"entity_id": "main", "label": "con rùa", "role": "main"},
            {
                "entity_id": "sec-1",
                "label": "chiếc lá",
                "role": "secondary" if leaf_approved else "excluded",
            },
        ],
    )
    staging = {
        "schema_version": STAGING_SCHEMA,
        "scenes": [
            {
                "scene_index": i,
                "main_end": {
                    "position": "left-middle",
                    "facing": "right",
                    "scale": "same",
                },
                "secondary_end": [{"entity_id": "sec-1", "state": states[i - 1]}]
                if leaf_approved
                else [],
            }
            for i in range(1, 6)
        ],
    }
    return keyframe_inputs_from(
        candidate,
        pack_story_content(
            {"opening": "a", "middle": "b", "ending": "c"}, staging, None
        ),
    )


def _parse(manifest):
    return video_app._parse_story_input(
        json.dumps(manifest, ensure_ascii=True).encode()
    )


def test_the_eat_the_leaf_manifest_is_accepted_by_the_worker() -> None:
    manifest = _build_input_manifest(
        _source(_inputs(("unchanged",) * 3 + ("partly_gone", "gone")))
    )
    parsed = _parse(manifest)
    assert parsed["keyframe_plan"]["render_mode"] == "keyframe"
    assert parsed["scene_visual_plan"]["schema_version"].endswith("visual-plan.v3")


def test_a_manifest_without_approved_secondaries_is_accepted() -> None:
    manifest = _build_input_manifest(
        _source(_inputs(("unchanged",) * 5, leaf_approved=False))
    )
    parsed = _parse(manifest)
    assert parsed["keyframe_plan"]["secondaries"] == []
    assert parsed["scene_visual_plan"]["schema_version"].endswith("visual-plan.v2")


def test_a_fallback_manifest_is_accepted_by_the_worker() -> None:
    parsed = _parse(_build_input_manifest(_source(None)))
    assert parsed["keyframe_plan"]["render_mode"] == "fallback"


def test_the_worker_compiles_a_v8_prompt_for_every_scene_of_the_backend_plan() -> None:
    manifest = _build_input_manifest(
        _source(_inputs(("unchanged",) * 3 + ("partly_gone", "gone")))
    )
    parsed = _parse(manifest)
    prompts = [
        video_app.compile_keyframe_scene_prompt(scene, parsed["scene_visual_plan"])
        for scene in parsed["scenes"]
    ]
    assert (
        "is gone from the paper" in prompts[4]
        and "is gone from the paper" not in prompts[3]
    )
    assert all(len(p) < 2_000 for p in prompts)
