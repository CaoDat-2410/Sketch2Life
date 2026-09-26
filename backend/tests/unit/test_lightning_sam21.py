from __future__ import annotations

import base64
import hashlib

from sketch2life.application.ports.segmentation import SubjectSegmentationRequest
from sketch2life.contracts.schemas.scene_exploration import SourceRegionV1
from sketch2life.infrastructure.ai.lightning_sam21 import LightningSam21SegmentationAdapter

_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)
_IMAGE = b"\x89PNG\r\n\x1a\nsynthetic-image"


class _Transport:
    def __init__(self, response: dict[str, object]) -> None:
        self.response = response
        self.path: str | None = None
        self.payload: dict[str, object] | None = None

    def post_json(self, path: str, payload: dict[str, object]) -> dict[str, object]:
        self.path = path
        self.payload = payload
        return self.response


def _request() -> SubjectSegmentationRequest:
    return SubjectSegmentationRequest(
        session_id="session-1",
        source_artifact_ref="artifact:source",
        source_sha256=hashlib.sha256(_IMAGE).hexdigest(),
        target_id="anchor-bird",
        target_label="con chim",
        target_confidence=0.94,
        semantic_tags=("animal",),
        prompt_region=SourceRegionV1(x=0.2, y=0.1, width=0.5, height=0.7),
    )


def test_sam21_adapter_keeps_provider_output_behind_typed_port() -> None:
    transport = _Transport(
        {
            "contractName": "Sam21SegmentationResponseV1",
            "contractVersion": "1.0",
            "status": "SUCCEEDED",
            "adapterId": "sam21-hiera-small",
            "adapterVersion": "1",
            "sourceSha256": hashlib.sha256(_IMAGE).hexdigest(),
            "sourceRegion": {"x": 0.2, "y": 0.1, "width": 0.5, "height": 0.7},
            "confidence": 0.91,
            "maskBase64": base64.b64encode(_PNG).decode("ascii"),
            "maskContentType": "image/png",
        }
    )
    stored: list[tuple[str, str, bytes]] = []
    adapter = LightningSam21SegmentationAdapter(
        transport=transport,
        artifact_loader=lambda _: _IMAGE,
        artifact_writer=lambda session, content_type, body: (
            stored.append((session, content_type, body))
            or type(
                "Descriptor",
                (),
                {
                    "artifact_ref": "artifact:mask",
                    "sha256": hashlib.sha256(_PNG).hexdigest(),
                },
            )()
        ),
    )

    result = adapter.segment(_request())

    assert result is not None
    assert result.adapter_id == "sam21-hiera-small"
    assert result.source_region.x == 0.2
    assert result.mask_artifact_ref == "artifact:mask"
    assert result.mask_sha256 == hashlib.sha256(_PNG).hexdigest()
    assert transport.path == "/v2/rig/segment"
    assert transport.payload is not None
    assert transport.payload["prompt_region"] == {"x": 0.2, "y": 0.1, "width": 0.5, "height": 0.7}
    assert stored == [("session-1", "image/png", _PNG)]


def test_sam21_adapter_returns_none_for_typed_provider_failure() -> None:
    digest = hashlib.sha256(_IMAGE).hexdigest()
    transport = _Transport(
        {
            "contractName": "Sam21SegmentationResponseV1",
            "contractVersion": "1.0",
            "status": "FAILED",
            "adapterId": "sam21-hiera-small",
            "adapterVersion": "1",
            "sourceSha256": digest,
            "failureCode": "MASK_REJECTED",
            "retryable": False,
        }
    )
    adapter = LightningSam21SegmentationAdapter(
        transport=transport,
        artifact_loader=lambda _: _IMAGE,
    )

    assert adapter.segment(_request()) is None
