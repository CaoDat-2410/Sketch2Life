"""Single real-AI FEAT-020 acceptance test for Lightning Studio."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from sketch2life.application.services.backend_ai_workflow import BackendWorkflowRequest
from sketch2life.interfaces.cli.workflow_demo import build_real_workflow


def test_lightning_backend_workflow_real_ai_four_band_matrix() -> None:
    """Run one real ASR/VLM workflow and assert every backend handoff contract."""

    if os.environ.get("SKETCH2LIFE_RUN_REAL_AI_E2E") != "1":
        pytest.skip("set SKETCH2LIFE_RUN_REAL_AI_E2E=1 in Lightning Studio")

    repo_root = Path(__file__).resolve().parents[3]
    workflow = build_real_workflow(repo_root)
    result = workflow.run(
        BackendWorkflowRequest(
            image_path=repo_root
            / "features/FEAT-020-backend-ai-workflow-demo/test-assets/input-image.png",
            narration_audio_path=repo_root
            / "features/FEAT-020-backend-ai-workflow-demo/test-assets/narration.wav",
            repo_root=repo_root,
            demo_autopilot=True,
        )
    )

    assert result.status == "SUCCEEDED"
    assert result.terminal_status == "BACKEND_CONTEXT_READY"
    assert result.input_mode == "MULTIMODAL"
    assert result.age_matrix_summary is not None
    assert result.age_matrix_summary.matrix_policy == "STRICT"
    assert result.age_matrix_summary.ready_age_bands == (
        "0-3",
        "3-6",
        "6-9",
        "9-12",
    )
    assert tuple(band.age_band for band in result.age_bands) == ("0-3", "3-6", "6-9", "9-12")
    assert all(band.status == "SUCCEEDED" for band in result.age_bands)
    assert all(
        band.experience_spec is not None
        and band.experience_spec["semantic_match"]["match_mode"]
        in {"EXACT", "ALIAS", "SAFE_FALLBACK"}
        for band in result.age_bands
    )
    assert all(
        band.activity_handoff is not None
        and isinstance(band.activity_handoff["duration_minutes"], dict)
        for band in result.age_bands
    )
    selection_vectors = tuple(band.selection_vector for band in result.age_bands)
    assert len(set(selection_vectors)) == len(selection_vectors)

    assert all(
        band.video is not None and band.video.status == "DEFERRED" for band in result.age_bands
    )
    assert all(band.art_render_intent is not None for band in result.age_bands)
    assert all(
        decision.actor == "DEMO_OPERATOR"
        for band in result.age_bands
        for decision in band.decisions
    )
    assert all(
        band.anchor_set is not None
        and band.experience_spec is not None
        and band.activity_handoff is not None
        and band.story_scene is not None
        for band in result.age_bands
    )
    assert result.image_sha256 == result.age_bands[0].anchor_set["source_artifact_sha256"]  # type: ignore[index]
    assert result.manifest_sha256
