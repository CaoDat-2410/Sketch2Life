"""Backend adapter for the optional Lightning SAM 2.1 worker."""

from __future__ import annotations

import base64
import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import ValidationError

from sketch2life.application.ports.segmentation import (
    SubjectPartSegmentationResult,
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
            proposal = propose_colored_component_prompt(
                image,
                preferred_region=request.prompt_region,
            )
            prompt_region = request.prompt_region or proposal.prompt_region
            positive_points = _merge_prompt_points(
                request.positive_points,
                proposal.positive_points,
            )
            negative_points = _merge_prompt_points(
                request.negative_points,
                proposal.negative_points,
            )
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
                    "positive_points": [{"x": x, "y": y} for x, y in positive_points],
                    "negative_points": [{"x": x, "y": y} for x, y in negative_points],
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
            parts: list[SubjectPartSegmentationResult] = []
            for part in response.part_masks:
                part_ref, part_sha256 = self._store_mask(request.session_id, part.mask_base64)
                if part_ref is None or part_sha256 is None:
                    continue
                parts.append(
                    SubjectPartSegmentationResult(
                        part_id=part.part_id,
                        role=part.role,
                        source_region=part.source_region,
                        confidence=part.confidence,
                        mask_artifact_ref=part_ref,
                        mask_sha256=part_sha256,
                        operation="SAM2.1 prompt-bounded part segmentation",
                        operation_version=response.adapter_version,
                    )
                )
            return SubjectSegmentationResult(
                source_region=response.source_region,
                confidence=response.confidence,
                adapter_id=response.adapter_id,
                adapter_version=response.adapter_version,
                mask_artifact_ref=mask_ref,
                mask_sha256=mask_sha256,
                parts=tuple(parts),
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


@dataclass(frozen=True, slots=True)
class Sam21PromptProposal:
    prompt_region: SourceRegionV1 | None
    positive_points: tuple[tuple[float, float], ...] = ()
    negative_points: tuple[tuple[float, float], ...] = ()


def propose_colored_component_prompt(
    image: bytes,
    *,
    preferred_region: SourceRegionV1 | None = None,
    include_negative: bool = True,
) -> Sam21PromptProposal:
    """Derive conservative point prompts from ink and neutral paper in the source image.

    Color/edge evidence only supplies SAM prompts. It never creates or edits a mask. An explicit
    localized region takes precedence; otherwise the existing bounded largest-ink proposal is
    used. A point is omitted when no sufficiently clear pixel exists.
    """

    region = preferred_region or propose_colored_component_region(image)
    if region is None:
        return Sam21PromptProposal(prompt_region=None)
    try:
        from io import BytesIO

        from PIL import Image

        with Image.open(BytesIO(image)) as source:
            small = source.convert("RGB")
            small.thumbnail((96, 96))
            width, height = small.size
            pixel_access = small.load()
            pixels = [pixel_access[x, y] for y in range(height) for x in range(width)]
    except (ImportError, OSError, ValueError):
        return Sam21PromptProposal(prompt_region=region)

    left = max(0, min(width, int(region.x * width)))
    top = max(0, min(height, int(region.y * height)))
    right = max(left + 1, min(width, int((region.x + region.width) * width + 0.999)))
    bottom = max(top + 1, min(height, int((region.y + region.height) * height + 0.999)))
    ink = [
        (max(red, green, blue) - min(red, green, blue) >= 20 and min(red, green, blue) < 245)
        or max(red, green, blue) < 95
        for red, green, blue in pixels
    ]

    target_ink = [
        (x, y)
        for y in range(top, bottom)
        for x in range(left, right)
        if ink[y * width + x]
    ]
    positive_points: tuple[tuple[float, float], ...] = ()
    if len(target_ink) >= 3:
        center_x = sum(x for x, _ in target_ink) / len(target_ink)
        center_y = sum(y for _, y in target_ink) / len(target_ink)
        # Prefer a dense actual-ink core, not the often-empty geometric center of a box around a
        # thin, asymmetric, or multi-part drawing.
        best_core: tuple[int, float, int, int] | None = None
        for x, y in target_ink:
            density = sum(
                ink[next_y * width + next_x]
                for next_y in range(max(0, y - 2), min(height, y + 3))
                for next_x in range(max(0, x - 2), min(width, x + 3))
            )
            if density < 3:
                continue
            candidate = (
                density,
                -((x - center_x) ** 2 + (y - center_y) ** 2),
                -y,
                -x,
            )
            if best_core is None or candidate > best_core:
                best_core = candidate
        if best_core is not None:
            x, y = -best_core[3], -best_core[2]
            positive_points = (((x + 0.5) / width, (y + 0.5) / height),)

    # A negative point is allowed only on bright, low-chroma paper outside the localized box
    # and away from every detected ink stroke. If no such point exists, do not guess.
    margin = 3
    region_center_x = (region.x + region.width / 2) * width
    region_center_y = (region.y + region.height / 2) * height
    best_negative: tuple[float, int, int] | None = None
    if include_negative:
        for y in range(0, height, 2):
            for x in range(0, width, 2):
                pixel_index = y * width + x
                if ink[pixel_index]:
                    continue
                red, green, blue = pixels[pixel_index]
                if max(red, green, blue) - min(red, green, blue) > 18:
                    continue
                if (red + green + blue) / 3 < 220:
                    continue
                if left - margin <= x < right + margin and top - margin <= y < bottom + margin:
                    continue
                if any(
                    ink[next_y * width + next_x]
                    for next_y in range(max(0, y - margin), min(height, y + margin + 1))
                    for next_x in range(max(0, x - margin), min(width, x + margin + 1))
                ):
                    continue
                distance = (x - region_center_x) ** 2 + (y - region_center_y) ** 2
                candidate = (distance, y, x)
                if best_negative is None or candidate > best_negative:
                    best_negative = candidate
    negative_points = (
        (((best_negative[2] + 0.5) / width, (best_negative[1] + 0.5) / height),)
        if best_negative is not None
        else ()
    )
    return Sam21PromptProposal(region, positive_points, negative_points)


def _merge_prompt_points(
    supplied: tuple[tuple[float, float], ...],
    proposed: tuple[tuple[float, float], ...],
) -> tuple[tuple[float, float], ...]:
    merged: list[tuple[float, float]] = []
    for point in (*supplied, *proposed):
        if point not in merged and len(merged) < 8:
            merged.append(point)
    return tuple(merged)


def propose_colored_component_region(image: bytes) -> SourceRegionV1 | None:
    """Create a conservative SAM box from visible colored ink.

    This is only a prompt proposal, never a mask. Child drawings often contain disconnected
    strokes, so the component scan first joins nearby strokes before selecting the largest
    cluster. If no reliable cluster survives, a bounded box around all visible ink is used as a
    last resort. Blank images and broad/full-canvas proposals still return ``None`` so SAM2 can
    fail closed instead of receiving an unsafe full-frame prompt.
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
            pixel_access = small.load()
            pixels = [pixel_access[x, y] for y in range(height) for x in range(width)]
    except (OSError, ValueError):
        return None
    ink = [
        (max(red, green, blue) - min(red, green, blue) >= 20 and min(red, green, blue) < 245)
        or max(red, green, blue) < 95
        for red, green, blue in pixels
    ]
    if width < 2 or height < 2:
        return None

    # Downsampling can break a child's continuous crayon stroke into many one-pixel islands.
    # Join only nearby islands; this is deliberately much smaller than the canvas so unrelated
    # subjects do not automatically become one giant prompt.
    radius = max(2, min(4, round(min(width, height) * 0.04)))
    clustered_ink = [False] * (width * height)
    ink_points = [
        (index % width, index // width) for index, is_ink in enumerate(ink) if is_ink
    ]
    for x, y in ink_points:
        for next_y in range(max(0, y - radius), min(height, y + radius + 1)):
            for next_x in range(max(0, x - radius), min(width, x + radius + 1)):
                clustered_ink[next_y * width + next_x] = True

    components: list[list[tuple[int, int]]] = []
    seen: set[tuple[int, int]] = set()
    for start_y in range(height):
        for start_x in range(width):
            start = (start_x, start_y)
            index = start_y * width + start_x
            if not clustered_ink[index] or start in seen:
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
                        if candidate in seen or not clustered_ink[next_y * width + next_x]:
                            continue
                        seen.add(candidate)
                        stack.append(candidate)
            if len(component) >= 3:
                components.append(component)
    if components:
        component = max(components, key=len)
        region = _region_from_pixel_box(component, width, height, padding=0.12)
        if region is not None:
            return region

    # Thin or low-contrast drawings may not produce a component large enough to trust. A
    # bounded aggregate prompt gives SAM2 useful context without silently authorizing a full
    # canvas mask. The final mask is still subject to the worker's area/quality gates.
    if ink_points:
        return _region_from_pixel_box(ink_points, width, height, padding=0.08)
    return None


def _region_from_pixel_box(
    points: list[tuple[int, int]],
    width: int,
    height: int,
    *,
    padding: float,
) -> SourceRegionV1 | None:
    if not points:
        return None
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    x0, x1 = min(xs) / width, (max(xs) + 1) / width
    y0, y1 = min(ys) / height, (max(ys) + 1) / height
    pad_x = max((x1 - x0) * padding, 0.02)
    pad_y = max((y1 - y0) * padding, 0.02)
    x0 = max(0.0, x0 - pad_x)
    y0 = max(0.0, y0 - pad_y)
    x1 = min(1.0, x1 + pad_x)
    y1 = min(1.0, y1 + pad_y)

    # Keep a safety margin below the runtime's 0.85 maximum. If the visible marks span almost
    # the whole image, shrink around their center rather than returning a full-frame prompt.
    max_area = 0.78
    box_width = x1 - x0
    box_height = y1 - y0
    area = box_width * box_height
    if area >= 0.85:
        scale = (max_area / area) ** 0.5
        center_x = (x0 + x1) / 2
        center_y = (y0 + y1) / 2
        box_width *= scale
        box_height *= scale
        x0 = center_x - box_width / 2
        y0 = center_y - box_height / 2
        x1 = center_x + box_width / 2
        y1 = center_y + box_height / 2
        if x0 < 0:
            x1 -= x0
            x0 = 0.0
        if y0 < 0:
            y1 -= y0
            y0 = 0.0
        if x1 > 1:
            x0 -= x1 - 1
            x1 = 1.0
        if y1 > 1:
            y0 -= y1 - 1
            y1 = 1.0
    if x1 <= x0 or y1 <= y0 or (x1 - x0) * (y1 - y0) >= 0.85:
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
