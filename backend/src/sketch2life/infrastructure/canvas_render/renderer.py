"""Deterministic Pillow renderer for authoritative `CanvasSourceExportV1` operation history."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from io import BytesIO
from threading import BoundedSemaphore
from typing import Literal

from PIL import Image, ImageDraw
from PIL import __version__ as PILLOW_VERSION

from sketch2life.contracts.schemas.be1_runtime import CanvasSourceExportV1
from sketch2life.domain.core_foundation import (
    CANVAS_OPERATION_PROFILE_V1_ID,
    canvas_operation_profile_v1_configuration,
    validate_canvas_operation_profile_v1,
)
from sketch2life.infrastructure.canvas_render import limits

CANVAS_EXPORT_SPEC_VERSION = "CanvasExportV1"
CANVAS_RENDERER_VERSION = "sketch2life-canvas-pillow-v1"
CANVAS_WIDTH = 1024
CANVAS_HEIGHT = 1024
CANVAS_BACKGROUND = "#FFFFFF"
CANVAS_MEDIA_TYPE: Literal["image/png"] = "image/png"
ADMISSION_POLICY_VERSION = "feat018-image-admission-v1"
_PIXEL_MAX = Decimal(CANVAS_WIDTH - 1)
_ROUNDING_UNIT = Decimal("1")
_RENDER_SEMAPHORE = BoundedSemaphore(1)


def _canonical_json_bytes(payload: object) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _require_sha(value: str, field: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field} must be lowercase SHA-256 hex")


def _rounded_integer(value: Decimal) -> int:
    return int(value.quantize(_ROUNDING_UNIT, rounding=ROUND_HALF_UP))


def profile_width_pixels(token: int) -> int:
    """Convert a fixed profile width ratio to pixels using decimal half-up rounding."""

    profile = canvas_operation_profile_v1_configuration()
    widths = profile["stroke_widths"]
    if not isinstance(widths, list):
        raise ValueError("canvas profile width table is invalid")
    for item in widths:
        if isinstance(item, dict) and item.get("token") == token:
            ratio = item.get("ratio")
            if not isinstance(ratio, int | float):
                break
            return _rounded_integer(Decimal(str(ratio)) * Decimal(CANVAS_WIDTH))
    raise ValueError("stroke width is outside the canvas profile")


def _pixel_coordinate(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError("canvas coordinate is not numeric")
    coordinate = Decimal(str(value))
    if not coordinate.is_finite() or not Decimal(0) <= coordinate <= Decimal(1):
        raise ValueError("canvas coordinate is outside the normalized profile")
    return _rounded_integer(coordinate * _PIXEL_MAX)


def _points(payload: dict[str, object]) -> list[tuple[int, int]]:
    raw_points = payload.get("points")
    if not isinstance(raw_points, list):
        raise ValueError("stroke points do not match the canvas profile")
    result: list[tuple[int, int]] = []
    for point in raw_points:
        if not isinstance(point, dict) or set(point) != {"x", "y"}:
            raise ValueError("stroke points do not match the canvas profile")
        result.append((_pixel_coordinate(point["x"]), _pixel_coordinate(point["y"])))
    return result


def _draw_stroke(
    draw: ImageDraw.ImageDraw,
    points: Sequence[tuple[int, int]],
    color: str,
    width: int,
) -> None:
    """Draw round-capped/round-joined segments; a defensive one-point stroke is invisible."""

    if len(points) < 2:
        return
    draw.line(points, fill=color, width=width, joint="curve")
    radius = width / 2
    for x, y in (points[0], points[-1]):
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)


@dataclass(frozen=True, slots=True)
class RenderDerivationV1:
    contract: Literal["CanvasRenderDerivationV1"]
    source_ref: str
    source_sha256: str
    export_spec_version: str
    renderer_version: str
    pillow_version: str
    width: int
    height: int
    mode: Literal["RGB"]
    background: str
    media_type: Literal["image/png"]
    render_sha256: str
    render_source_binding_sha256: str

    def __post_init__(self) -> None:
        _require_sha(self.source_sha256, "source_sha256")
        _require_sha(self.render_sha256, "render_sha256")
        _require_sha(self.render_source_binding_sha256, "render_source_binding_sha256")
        if self.source_ref != f"be1-canvas-source-v1:{self.source_sha256}":
            raise ValueError("render derivation source reference does not match its digest")
        if (
            not self.export_spec_version
            or not self.renderer_version
            or not self.pillow_version
            or (self.width, self.height, self.mode, self.background, self.media_type)
            != (CANVAS_WIDTH, CANVAS_HEIGHT, "RGB", CANVAS_BACKGROUND, CANVAS_MEDIA_TYPE)
        ):
            raise ValueError("render derivation parameters are outside CanvasExportV1")
        binding = {
            "contract": "CanvasRenderSourceBindingV1",
            "source_ref": self.source_ref,
            "source_sha256": self.source_sha256,
            "export_spec_version": self.export_spec_version,
            "renderer_version": self.renderer_version,
            "pillow_version": self.pillow_version,
            "width": self.width,
            "height": self.height,
            "mode": self.mode,
            "background": self.background,
            "media_type": self.media_type,
            "render_sha256": self.render_sha256,
        }
        if _sha256(_canonical_json_bytes(binding)) != self.render_source_binding_sha256:
            raise ValueError("render derivation source binding digest does not match")

    @classmethod
    def from_render(
        cls,
        *,
        source_ref: str,
        source_sha256: str,
        render_sha256: str,
        pillow_version: str = PILLOW_VERSION,
        export_spec_version: str = CANVAS_EXPORT_SPEC_VERSION,
        renderer_version: str = CANVAS_RENDERER_VERSION,
    ) -> RenderDerivationV1:
        _require_sha(source_sha256, "source_sha256")
        _require_sha(render_sha256, "render_sha256")
        if not source_ref or not pillow_version or not renderer_version or not export_spec_version:
            raise ValueError("render derivation is missing a versioned source binding")
        binding = {
            "contract": "CanvasRenderSourceBindingV1",
            "source_ref": source_ref,
            "source_sha256": source_sha256,
            "export_spec_version": export_spec_version,
            "renderer_version": renderer_version,
            "pillow_version": pillow_version,
            "width": CANVAS_WIDTH,
            "height": CANVAS_HEIGHT,
            "mode": "RGB",
            "background": CANVAS_BACKGROUND,
            "media_type": CANVAS_MEDIA_TYPE,
            "render_sha256": render_sha256,
        }
        return cls(
            contract="CanvasRenderDerivationV1",
            source_ref=source_ref,
            source_sha256=source_sha256,
            export_spec_version=export_spec_version,
            renderer_version=renderer_version,
            pillow_version=pillow_version,
            width=CANVAS_WIDTH,
            height=CANVAS_HEIGHT,
            mode="RGB",
            background=CANVAS_BACKGROUND,
            media_type=CANVAS_MEDIA_TYPE,
            render_sha256=render_sha256,
            render_source_binding_sha256=_sha256(_canonical_json_bytes(binding)),
        )


@dataclass(frozen=True, slots=True)
class CanvasRenderResultV1:
    png_bytes: bytes
    derivation: RenderDerivationV1


@dataclass(frozen=True, slots=True)
class CanvasAdmissionReceiptV1:
    contract: Literal["CanvasImageAdmissionReceiptV1"]
    source_ref: str
    source_sha256: str
    render_artifact_ref: str
    render_sha256: str
    render_source_binding_sha256: str
    export_spec_version: str
    renderer_version: str
    pillow_version: str
    width: int
    height: int
    mode: Literal["RGB"]
    background: str
    media_type: Literal["image/png"]
    admission_policy_version: str
    outcome: Literal["ADMITTED"]
    admitted_content_sha256: str
    decoder_container: str
    decoder_codec: str
    decoder_pixel_format: str
    decoded_width: int
    decoded_height: int
    admitted_at_utc: str
    receipt_binding_sha256: str

    def __post_init__(self) -> None:
        for field_name in (
            "source_sha256",
            "render_sha256",
            "render_source_binding_sha256",
            "admitted_content_sha256",
            "receipt_binding_sha256",
        ):
            _require_sha(getattr(self, field_name), field_name)
        if (
            self.contract != "CanvasImageAdmissionReceiptV1"
            or self.admission_policy_version != ADMISSION_POLICY_VERSION
            or self.outcome != "ADMITTED"
            or self.admitted_content_sha256 != self.render_sha256
            or self.source_ref != f"be1-canvas-source-v1:{self.source_sha256}"
            or not self.render_artifact_ref
            or not self.decoder_container
            or not self.decoder_codec
            or not self.decoder_pixel_format
            or (self.width, self.height, self.mode, self.background, self.media_type)
            != (CANVAS_WIDTH, CANVAS_HEIGHT, "RGB", CANVAS_BACKGROUND, CANVAS_MEDIA_TYPE)
            or (self.decoded_width, self.decoded_height) != (CANVAS_WIDTH, CANVAS_HEIGHT)
        ):
            raise ValueError("admission receipt fields do not match the render contract")
        try:
            timestamp = datetime.fromisoformat(self.admitted_at_utc)
        except ValueError:
            raise ValueError("admission timestamp must be ISO-8601") from None
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("admission timestamp must be timezone-aware")
        fields = asdict(self)
        fields.pop("receipt_binding_sha256")
        if _sha256(_canonical_json_bytes(fields)) != self.receipt_binding_sha256:
            raise ValueError("admission receipt binding digest does not match")

    @classmethod
    def create(
        cls,
        *,
        derivation: RenderDerivationV1,
        render_artifact_ref: str,
        admitted_content_sha256: str,
        decoder_container: str,
        decoder_codec: str,
        decoder_pixel_format: str,
        decoded_width: int,
        decoded_height: int,
        admitted_at: datetime | None = None,
    ) -> CanvasAdmissionReceiptV1:
        _require_sha(admitted_content_sha256, "admitted_content_sha256")
        if admitted_content_sha256 != derivation.render_sha256:
            raise ValueError("admission digest does not match the rendered PNG")
        if not render_artifact_ref or not decoder_container or not decoder_codec:
            raise ValueError("admission receipt is missing source or decoder metadata")
        if not decoder_pixel_format or (decoded_width, decoded_height) != (
            derivation.width,
            derivation.height,
        ):
            raise ValueError("decoded image metadata does not match the render")
        timestamp = admitted_at or datetime.now(UTC)
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("admission timestamp must be timezone-aware")
        fields: dict[str, object] = {
            "contract": "CanvasImageAdmissionReceiptV1",
            "source_ref": derivation.source_ref,
            "source_sha256": derivation.source_sha256,
            "render_artifact_ref": render_artifact_ref,
            "render_sha256": derivation.render_sha256,
            "render_source_binding_sha256": derivation.render_source_binding_sha256,
            "export_spec_version": derivation.export_spec_version,
            "renderer_version": derivation.renderer_version,
            "pillow_version": derivation.pillow_version,
            "width": derivation.width,
            "height": derivation.height,
            "mode": derivation.mode,
            "background": derivation.background,
            "media_type": derivation.media_type,
            "admission_policy_version": ADMISSION_POLICY_VERSION,
            "outcome": "ADMITTED",
            "admitted_content_sha256": admitted_content_sha256,
            "decoder_container": decoder_container,
            "decoder_codec": decoder_codec,
            "decoder_pixel_format": decoder_pixel_format,
            "decoded_width": decoded_width,
            "decoded_height": decoded_height,
            "admitted_at_utc": timestamp.astimezone(UTC).isoformat(),
        }
        receipt_binding_sha256 = _sha256(_canonical_json_bytes(fields))
        return cls(**fields, receipt_binding_sha256=receipt_binding_sha256)  # type: ignore[arg-type]

    def to_json_bytes(self) -> bytes:
        return _canonical_json_bytes(asdict(self))


@dataclass(frozen=True, slots=True)
class CanvasRenderHandoffV1:
    contract: Literal["CanvasRenderHandoffV1"]
    organization_id: str
    session_id: str
    canvas_id: str
    document_epoch: int
    document_revision: int
    source_ref: str
    source_sha256: str
    render_artifact_ref: str
    render_sha256: str
    render_source_binding_sha256: str
    receipt_artifact_ref: str
    receipt_sha256: str

    def __post_init__(self) -> None:
        for field_name in (
            "source_sha256",
            "render_sha256",
            "render_source_binding_sha256",
            "receipt_sha256",
        ):
            _require_sha(getattr(self, field_name), field_name)
        if (
            self.contract != "CanvasRenderHandoffV1"
            or not self.organization_id
            or not self.session_id
            or not self.canvas_id
            or self.document_epoch < 1
            or self.document_revision < 2
            or self.source_ref != f"be1-canvas-source-v1:{self.source_sha256}"
            or not self.render_artifact_ref
            or not self.receipt_artifact_ref
        ):
            raise ValueError("render handoff fields are outside the accepted canvas scope")


def render_canvas_source(
    source: CanvasSourceExportV1, *, deadline: float | None = None
) -> CanvasRenderResultV1:
    """Render the server-validated operation export without consulting checkpoint snapshots."""

    if deadline is None:
        deadline = limits.monotonic() + limits.RENDER_DEADLINE_SECONDS
    limits.check_render_deadline(deadline)
    limits.validate_source_capacity(source)
    limits.check_render_deadline(deadline)
    if not _RENDER_SEMAPHORE.acquire(timeout=max(0.0, deadline - limits.monotonic())):
        raise limits.CanvasRenderBusy("canvas rendering slot is busy")
    try:
        limits.check_render_deadline(deadline)
        return _render_canvas_source(source, deadline=deadline)
    finally:
        _RENDER_SEMAPHORE.release()


def _render_canvas_source(source: CanvasSourceExportV1, *, deadline: float) -> CanvasRenderResultV1:
    validated = CanvasSourceExportV1.model_validate(source.model_dump(mode="json"))
    limits.validate_source_capacity(validated)
    if (
        validated.profile_id != "canvas-operation-profile-v1"
        or validated.profile_version != "CanvasOperationProfileV1"
        or not validated.operations
    ):
        raise ValueError("canvas source is outside the canvas profile")

    limits.check_render_deadline(deadline)
    with Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), CANVAS_BACKGROUND) as image:
        draw = ImageDraw.Draw(image)
        for operation in validated.operations:
            limits.check_render_deadline(deadline)
            payload = operation.operation_payload
            if (
                not isinstance(payload, dict)
                or payload.get("canvas_operation_profile_id") != CANVAS_OPERATION_PROFILE_V1_ID
            ):
                raise ValueError("operation payload is outside the canvas profile")
            stroke_payload = dict(payload)
            stroke_payload.pop("canvas_operation_profile_id")
            try:
                accepted_payload = validate_canvas_operation_profile_v1(stroke_payload)
            except ValueError as error:
                raise ValueError("operation payload is outside the canvas profile") from error
            if accepted_payload != stroke_payload:
                raise ValueError("operation payload is outside the canvas profile")
            color = accepted_payload.get("color")
            width_token = accepted_payload.get("size")
            if not isinstance(color, str) or type(width_token) is not int:
                raise ValueError("operation payload is outside the canvas profile")
            _draw_stroke(draw, _points(accepted_payload), color, profile_width_pixels(width_token))

        limits.check_render_deadline(deadline)
        stream = BytesIO()
        image.save(stream, format="PNG", optimize=False, compress_level=9)
    limits.check_render_deadline(deadline)
    png_bytes = stream.getvalue()
    render_sha256 = _sha256(png_bytes)
    derivation = RenderDerivationV1.from_render(
        source_ref=validated.source_ref,
        source_sha256=validated.source_sha256,
        render_sha256=render_sha256,
    )
    limits.check_render_deadline(deadline)
    return CanvasRenderResultV1(png_bytes=png_bytes, derivation=derivation)


__all__ = [
    "ADMISSION_POLICY_VERSION",
    "CANVAS_BACKGROUND",
    "CANVAS_EXPORT_SPEC_VERSION",
    "CANVAS_HEIGHT",
    "CANVAS_MEDIA_TYPE",
    "CANVAS_RENDERER_VERSION",
    "CANVAS_WIDTH",
    "CanvasAdmissionReceiptV1",
    "CanvasRenderHandoffV1",
    "CanvasRenderResultV1",
    "RenderDerivationV1",
    "profile_width_pixels",
    "render_canvas_source",
]
