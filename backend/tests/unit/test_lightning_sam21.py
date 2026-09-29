from __future__ import annotations

import base64
import hashlib
from dataclasses import replace
from io import BytesIO

from PIL import Image, ImageDraw

from sketch2life.application.ports.segmentation import SubjectSegmentationRequest
from sketch2life.contracts.schemas.scene_exploration import SourceRegionV1
from sketch2life.infrastructure.ai.lightning_sam21 import (
    LightningSam21SegmentationAdapter,
    propose_colored_component_region,
)

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


def test_sam21_adapter_preserves_independent_part_mask_artifacts() -> None:
    digest = hashlib.sha256(_IMAGE).hexdigest()
    response = {
        "contractName": "Sam21SegmentationResponseV1",
        "contractVersion": "1.0",
        "status": "SUCCEEDED",
        "adapterId": "sam21-hiera-small",
        "adapterVersion": "1",
        "sourceSha256": digest,
        "sourceRegion": {"x": 0.1, "y": 0.1, "width": 0.8, "height": 0.8},
        "confidence": 0.93,
        "maskBase64": base64.b64encode(_PNG).decode("ascii"),
        "maskContentType": "image/png",
        "partMasks": [
            {
                "partId": role,
                "role": role,
                "sourceRegion": {"x": 0.1, "y": 0.1, "width": 0.3, "height": 0.4},
                "confidence": 0.82,
                "maskBase64": base64.b64encode(_PNG).decode("ascii"),
                "maskContentType": "image/png",
            }
            for role in ("left-wing", "body", "right-wing")
        ],
    }
    transport = _Transport(response)
    stored: list[tuple[str, str, bytes]] = []

    def writer(session: str, content_type: str, body: bytes) -> object:
        artifact_id = len(stored)
        stored.append((session, content_type, body))
        return type(
            "Descriptor",
            (),
            {
                "artifact_ref": f"artifact:mask-{artifact_id}",
                "sha256": hashlib.sha256(body).hexdigest(),
            },
        )()

    adapter = LightningSam21SegmentationAdapter(
        transport=transport,
        artifact_loader=lambda _: _IMAGE,
        artifact_writer=writer,
    )
    request = replace(_request(), requested_part_roles=("left-wing", "body", "right-wing"))

    result = adapter.segment(request)

    assert result is not None
    assert [part.role for part in result.parts] == ["left-wing", "body", "right-wing"]
    assert len({part.mask_artifact_ref for part in result.parts}) == 3
    assert len(stored) == 4  # subject silhouette plus three independent part masks
    assert transport.payload is not None
    assert transport.payload["requested_part_roles"] == ["left-wing", "body", "right-wing"]


def _drawing_png(*, blank: bool = False) -> bytes:
    image = Image.new("RGB", (800, 500), "white")
    if not blank:
        draw = ImageDraw.Draw(image)
        # Separate crayon-like strokes that should be joined into one useful SAM prompt.
        draw.line((220, 230, 320, 140), fill=(20, 130, 240), width=14)
        draw.line((320, 140, 420, 230), fill=(20, 130, 240), width=14)
        draw.ellipse((250, 160, 390, 300), outline=(245, 120, 20), width=18)
        draw.line((320, 210, 320, 390), fill=(20, 130, 240), width=16)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_prompt_proposal_joins_fragmented_colored_drawing_strokes() -> None:
    region = propose_colored_component_region(_drawing_png())

    assert region is not None
    assert 0 < region.x < 1
    assert 0 < region.y < 1
    assert region.width * region.height < 0.85
    assert region.width > 0.2
    assert region.height > 0.2


def test_prompt_proposal_fails_closed_for_blank_drawing() -> None:
    assert propose_colored_component_region(_drawing_png(blank=True)) is None
