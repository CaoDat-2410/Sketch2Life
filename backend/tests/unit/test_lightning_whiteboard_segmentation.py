from __future__ import annotations

import base64
import hashlib
from datetime import UTC, datetime, timedelta

from sketch2life.application.services.whiteboard_video_pipeline import LocalizedRegionBatch
from sketch2life.contracts.schemas.whiteboard_video import WhiteboardVideoJobV1
from sketch2life.infrastructure.ai.lightning_whiteboard_segmentation import (
    LightningWhiteboardSegmentationAdapter,
)


class Transport:
    source_hash = hashlib.sha256(b"source-image").hexdigest()

    def post_json(self, path, payload):
        assert path == "/v1/whiteboard/segment"
        assert payload["region_refs"] == ["region-1"]
        return {
            "source_hash": self.source_hash,
            "masks": [
                {
                    "mask_ref": "mask-1",
                    "content_base64": base64.b64encode(b"\x89PNG\r\n\x1a\nmask").decode(),
                }
            ],
        }


def test_segmentation_adapter_sinks_validated_png_mask() -> None:
    created_at = datetime(2026, 9, 24, tzinfo=UTC)
    job = WhiteboardVideoJobV1(
        job_id="job-1",
        session_id="session-1",
        experience_spec_id="spec-1",
        source_artifact_id="source-1",
        source_hash=Transport.source_hash,
        learning_thread_ref="thread-1",
        status="RUNNING",
        progress=15,
        current_stage="LOCALIZING",
        attempt=1,
        idempotency_key="idem-1",
        created_at=created_at,
        started_at=created_at + timedelta(seconds=1),
        expires_at=created_at + timedelta(minutes=3),
    )
    stored: dict[str, bytes] = {}
    adapter = LightningWhiteboardSegmentationAdapter(
        transport=Transport(),
        artifact_loader=lambda _: b"source-image",
        artifact_sink=lambda ref, content: stored.setdefault(ref, content) and ref,
    )

    result = adapter.segment(
        job,
        LocalizedRegionBatch(source_hash=Transport.source_hash, region_refs=("region-1",)),
    )

    assert result.source_hash == Transport.source_hash
    assert result.mask_refs == ("mask-1",)
    assert stored["mask-1"].startswith(b"\x89PNG")
