from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

from fastapi import FastAPI

from sketch2life.interfaces.http.routers.parent_video_candidates import (
    _candidate_response,
    router,
)


def test_parent_video_candidate_routes_publish_the_private_preview_contract() -> None:
    app = FastAPI()
    app.include_router(router)
    paths = app.openapi()["paths"]

    create_path = "/v1/story-runs/{run_id}/video-generations"
    current_path = f"{create_path}/current"
    item_path = f"{create_path}/{{video_candidate_id}}"
    preview_path = f"{item_path}/preview"
    assert {create_path, current_path, item_path, preview_path} <= set(paths)

    create = paths[create_path]["post"]
    assert "202" in create["responses"]
    idempotency = next(
        parameter
        for parameter in create["parameters"]
        if parameter["name"] == "Idempotency-Key"
    )
    assert idempotency["in"] == "header"
    assert idempotency["required"] is True

    preview = paths[preview_path]["get"]
    assert "video/mp4" in preview["responses"]["200"]["content"]


def test_ready_candidate_response_projects_only_public_metadata_fields() -> None:
    public_metadata = {
        "duration_seconds": 30.0,
        "width": 1280,
        "height": 720,
        "fps": 24.0,
        "video_codec": "h264",
        "audio_streams": 0,
        "scene_count": 5,
        "video_profile": "ltx25-distilled-bf16-fp8-cpu-offload-l40s-v1",
        "model_id": "Lightricks/LTX-2.5",
        "model_revision": "49b093a39c19169a8a81721dcc541e07e945232f",
        "technical_validation": "PASS",
        "consistency_validation": "NOT_RUN",
        "safety_validation": "NOT_RUN",
        "product_playable": False,
    }
    persisted_metadata = {
        **public_metadata,
        "output_sha256": "a" * 64,
        "output_size_bytes": 4_289_168,
        "output_manifest_sha256": "b" * 64,
    }
    now = datetime.now(UTC)
    record = SimpleNamespace(
        video_candidate_id="00000000-0000-0000-0000-000000000001",
        run_id="00000000-0000-0000-0000-000000000002",
        story_revision_id="00000000-0000-0000-0000-000000000003",
        story_revision_no=1,
        story_sha256="c" * 64,
        state="CANDIDATE_READY",
        safe_failure_code=None,
        output_metadata=persisted_metadata,
        output_asset_ref="private://video-candidate",
        created_at=now,
        updated_at=now,
    )

    response = _candidate_response(record)

    assert response.state == "CANDIDATE_READY"
    assert response.preview_available is True
    assert response.product_playable is False
    assert response.safety_validation == "NOT_RUN"
    assert response.metadata is not None
    assert response.metadata.model_dump() == public_metadata

