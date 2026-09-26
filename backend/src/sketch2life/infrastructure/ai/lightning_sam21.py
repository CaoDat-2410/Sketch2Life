"""Backend adapter for the optional Lightning SAM 2.1 worker."""

from __future__ import annotations

import base64
import hashlib
from collections.abc import Callable
from typing import Any, Literal

from pydantic import ValidationError

from sketch2life.application.ports.segmentation import (
    SubjectSegmentationPort,
    SubjectSegmentationRequest,
    SubjectSegmentationResult,
)
from sketch2life.contracts.schemas.sam21 import Sam21SegmentationResponseV1
from sketch2life.contracts.schemas.scene_exploration import SourceRegionV1
from sketch2life.infrastructure.ai.lightning_client import (
    JsonTransport,
    LightningProviderError,
)


class LightningSam21SegmentationAdapter(SubjectSegmentationPort):
    """Call SAM2.1 once per Gate-A target and keep provider output behind a typed port."""

    def __init__(
        self,
        *,
        transport: JsonTransport,
        artifact_loader: Callable[[str], bytes],
        artifact_writer: Callable[[str, str, bytes], Any] | None = None,
        endpoint_path: str = "/v2/rig/segment",
        max_input_bytes: int = 5_000_000,
        max_mask_bytes: int = 5_000_000,
    ) -> None:
        self._transport = transport
        self._artifact_loader = artifact_loader
        self._artifact_writer = artifact_writer
        self._endpoint_path = endpoint_path
        self._max_input_bytes = max_input_bytes
        self._max_mask_bytes = max_mask_bytes

    def segment(self, request: SubjectSegmentationRequest) -> SubjectSegmentationResult | None:
        try:
            image = self._artifact_loader(request.source_artifact_ref)
            if not image or len(image) > self._max_input_bytes:
                return None
            digest = hashlib.sha256(image).hexdigest()
            if digest != request.source_sha256:
                return None
            content_type = _image_content_type(image)
            if content_type is None:
                return None
            prompt_region = request.prompt_region or propose_colored_component_region(image)
            raw = self._transport.post_json(
                self._endpoint_path,
                {
                    "contract_name": "Sam21SegmentationRequestV1",
                    "contract_version": "1.0",
                    "session_id": request.session_id,
                    "target_id": request.target_id,
                    "target_label": request.target_label,
                    "target_confidence": request.target_confidence,
                    "semantic_tags": list(request.semantic_tags),
                    "prompt_region": (
                        prompt_region.model_dump(mode="json") if prompt_region is not None else None
                    ),
                    "positive_points": [{"x": x, "y": y} for x, y in request.positive_points],
                    "negative_points": [{"x": x, "y": y} for x, y in request.negative_points],
                    "requested_part_roles": list(request.requested_part_roles),
                    "source_image": {
                        "artifact_ref": request.source_artifact_ref,
                        "sha256": digest,
                        "content_type": content_type,
                        "content_base64": base64.b64encode(image).decode("ascii"),
                    },
                },
            )
            response = Sam21SegmentationResponseV1.model_validate(raw)
            if response.source_sha256 != digest or response.status != "SUCCEEDED":
                return None
            mask_ref, mask_sha256 = self._store_mask(request.session_id, response.mask_base64)
            if response.source_region is None or response.confidence is None:
                return None
            return SubjectSegmentationResult(
                source_region=response.source_region,
                confidence=response.confidence,
                adapter_id=response.adapter_id,
                adapter_version=response.adapter_version,
                mask_artifact_ref=mask_ref,
                mask_sha256=mask_sha256,
            )
        except (
            KeyError,
            LightningProviderError,
            TimeoutError,
            TypeError,
            ValueError,
            OSError,
            ValidationError,
        ):
            return None

    def _store_mask(self, session_id: str, encoded: str | None) -> tuple[str | None, str | None]:
        if encoded is None or self._artifact_writer is None:
            return None, None
        mask = base64.b64decode(encoded, validate=True)
        if (
            not mask
            or len(mask) > self._max_mask_bytes
            or not mask.startswith(b"\x89PNG\r\n\x1a\n")
        ):
            raise ValueError("segmentation mask is invalid")
        descriptor = self._artifact_writer(session_id, "image/png", mask)
        artifact_ref = getattr(descriptor, "artifact_ref", None)
        artifact_sha256 = getattr(descriptor, "sha256", None)
        if not isinstance(artifact_ref, str) or not isinstance(artifact_sha256, str):
            raise ValueError("mask artifact writer returned an invalid descriptor")
        if artifact_sha256 != hashlib.sha256(mask).hexdigest():
            raise ValueError("mask artifact digest mismatch")
        return artifact_ref, artifact_sha256


def propose_colored_component_region(image: bytes) -> SourceRegionV1 | None:
    """Create a conservative box prompt from the largest colored ink component.

    This is only a prompt proposal, never a mask.  It avoids a second Qwen call and refuses
    broad/full-canvas proposals.  SAM2 remains responsible for the final silhouette.
    """

    try:
        from PIL import Image
    except ImportError:
        return None
    try:
        from io import BytesIO

        with Image.open(BytesIO(image)) as source:
            small = source.convert("RGB")
            small.thumbnail((96, 96))
            width, height = small.size
            pixels = list(small.getdata())
    except (OSError, ValueError):
        return None
    ink = [
        (max(red, green, blue) - min(red, green, blue) >= 20 and min(red, green, blue) < 245)
        or max(red, green, blue) < 95
        for red, green, blue in pixels
    ]
    components: list[list[tuple[int, int]]] = []
    seen: set[tuple[int, int]] = set()
    for start_y in range(height):
        for start_x in range(width):
            start = (start_x, start_y)
            index = start_y * width + start_x
            if not ink[index] or start in seen:
                continue
            stack = [start]
            seen.add(start)
            component: list[tuple[int, int]] = []
            while stack:
                x, y = stack.pop()
                component.append((x, y))
                for next_y in range(max(0, y - 1), min(height, y + 2)):
                    for next_x in range(max(0, x - 1), min(width, x + 2)):
                        candidate = (next_x, next_y)
                        if candidate in seen or not ink[next_y * width + next_x]:
                            continue
                        seen.add(candidate)
                        stack.append(candidate)
            if len(component) >= 3:
                components.append(component)
    if not components:
        return None
    component = max(components, key=len)
    xs = [point[0] for point in component]
    ys = [point[1] for point in component]
    x0, x1 = min(xs) / width, (max(xs) + 1) / width
    y0, y1 = min(ys) / height, (max(ys) + 1) / height
    pad_x = max((x1 - x0) * 0.12, 0.02)
    pad_y = max((y1 - y0) * 0.12, 0.02)
    x0 = max(0.0, x0 - pad_x)
    y0 = max(0.0, y0 - pad_y)
    x1 = min(1.0, x1 + pad_x)
    y1 = min(1.0, y1 + pad_y)
    if (x1 - x0) * (y1 - y0) >= 0.85:
        return None
    return SourceRegionV1(x=x0, y=y0, width=x1 - x0, height=y1 - y0)


def _image_content_type(image: bytes) -> Literal["image/jpeg", "image/png"] | None:
    if image.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if image.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    return None


__all__ = [
    "LightningSam21SegmentationAdapter",
    "propose_colored_component_region",
]
