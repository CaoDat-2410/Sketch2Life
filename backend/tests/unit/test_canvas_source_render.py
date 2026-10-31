from __future__ import annotations

import hashlib
import io
import json
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any

import pytest
from PIL import Image


def _source_export(*, strokes: tuple[dict[str, Any], ...] | None = None):
    from sketch2life.contracts.schemas.be1_runtime import (
        CanvasSourceExportV1,
        CanvasSourceOperationV1,
    )

    payloads = strokes or (
        {
            "kind": "stroke",
            "points": [{"x": 0.1, "y": 0.5}, {"x": 0.9, "y": 0.5}],
            "color": "#FFD21F",
            "size": 5,
        },
        {
            "kind": "stroke",
            "points": [{"x": 0.5, "y": 0.1}, {"x": 0.5, "y": 0.9}],
            "color": "#1685F8",
            "size": 9,
        },
    )
    operations = [
        CanvasSourceOperationV1(
            operation_id=f"synthetic-operation-{revision}",
            participant_id="synthetic-child-1",
            document_epoch=1,
            resulting_revision=revision,
            operation_payload={
                **payload,
                "canvas_operation_profile_id": "canvas-operation-profile-v1",
            },
            payload_sha256=hashlib.sha256(
                json.dumps(
                    {
                        **payload,
                        "canvas_operation_profile_id": "canvas-operation-profile-v1",
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest(),
        )
        for revision, payload in enumerate(payloads, start=2)
    ]
    return CanvasSourceExportV1.from_operations(
        organization_id="synthetic-org-1",
        session_id="synthetic-session-1",
        canvas_id="synthetic-canvas-1",
        document_epoch=1,
        document_revision=len(operations) + 1,
        operations=operations,
    )


def test_render_canvas_export_is_1024_rgb_white_and_deterministic() -> None:
    from sketch2life.infrastructure.canvas_render.renderer import render_canvas_source

    source = _source_export()
    rendered = render_canvas_source(source)
    repeated = render_canvas_source(source)
    image = Image.open(io.BytesIO(rendered.png_bytes))

    assert image.format == "PNG"
    assert image.size == (1024, 1024)
    assert image.mode == "RGB"
    assert image.getpixel((0, 0)) == (255, 255, 255)
    assert rendered.png_bytes == repeated.png_bytes
    assert rendered.derivation.render_sha256 == hashlib.sha256(rendered.png_bytes).hexdigest()
    assert rendered.derivation.export_spec_version == "CanvasExportV1"
    assert rendered.derivation.renderer_version == "sketch2life-canvas-pillow-v1"
    assert rendered.derivation.source_sha256 == source.source_sha256
    assert (
        rendered.derivation.render_source_binding_sha256
        == repeated.derivation.render_source_binding_sha256
    )


@pytest.mark.parametrize(("token", "expected_pixels"), [(5, 13), (9, 23), (14, 36)])
def test_render_width_uses_decimal_round_half_up(token: int, expected_pixels: int) -> None:
    from sketch2life.infrastructure.canvas_render.renderer import profile_width_pixels

    assert profile_width_pixels(token) == expected_pixels


def test_render_preserves_coincident_points_and_one_point_draw_is_noop() -> None:
    from PIL import ImageDraw
    from sketch2life.infrastructure.canvas_render.renderer import (
        _draw_stroke,
        render_canvas_source,
    )

    source = _source_export(
        strokes=(
            {
                "kind": "stroke",
                "points": [{"x": 0.5, "y": 0.5}, {"x": 0.5, "y": 0.5}],
                "color": "#FF596C",
                "size": 5,
            },
        )
    )
    rendered = render_canvas_source(source)
    image = Image.open(io.BytesIO(rendered.png_bytes))
    assert image.getpixel((512, 512)) == (255, 89, 108)

    blank = Image.new("RGB", (16, 16), "#FFFFFF")
    _draw_stroke(ImageDraw.Draw(blank), [(8, 8)], "#FF596C", 13)
    assert blank.getpixel((8, 8)) == (255, 255, 255)


def test_render_rejects_operation_outside_canvas_profile() -> None:
    from sketch2life.infrastructure.canvas_render.renderer import render_canvas_source

    source = _source_export(
        strokes=(
            {
                "kind": "stroke",
                "points": [{"x": 0.1, "y": 0.2}, {"x": 0.3, "y": 0.4}],
                "color": "#FFD21F",
                "size": 7,
            },
        )
    )

    with pytest.raises(ValueError, match="canvas profile"):
        render_canvas_source(source)


def test_render_rejects_unbound_or_wrong_server_profile() -> None:
    from sketch2life.contracts.schemas.be1_runtime import (
        CanvasSourceExportV1,
        CanvasSourceOperationV1,
    )
    from sketch2life.infrastructure.canvas_render.renderer import render_canvas_source

    source = _source_export()
    operation = source.operations[0]
    payload = dict(operation.operation_payload)
    payload["canvas_operation_profile_id"] = "synthetic-wrong-profile"
    invalid_operation = CanvasSourceOperationV1(
        **{
            **operation.model_dump(),
            "operation_payload": payload,
            "payload_sha256": hashlib.sha256(
                json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest(),
        }
    )
    invalid = CanvasSourceExportV1.from_operations(
        organization_id=source.organization_id,
        session_id=source.session_id,
        canvas_id=source.canvas_id,
        document_epoch=source.document_epoch,
        document_revision=source.document_revision,
        operations=[invalid_operation, *source.operations[1:]],
    )

    with pytest.raises(ValueError, match="canvas profile"):
        render_canvas_source(invalid)


def test_render_binding_changes_with_spec_renderer_and_pillow_versions() -> None:
    from sketch2life.infrastructure.canvas_render.renderer import RenderDerivationV1

    source = _source_export()
    kwargs = {
        "source_ref": source.source_ref,
        "source_sha256": source.source_sha256,
        "render_sha256": "a" * 64,
        "pillow_version": "12.3.0",
    }
    baseline = RenderDerivationV1.from_render(**kwargs)
    assert (
        RenderDerivationV1.from_render(
            **kwargs, export_spec_version="CanvasExportV2"
        ).render_source_binding_sha256
        != baseline.render_source_binding_sha256
    )
    assert (
        RenderDerivationV1.from_render(
            **kwargs, renderer_version="renderer-next"
        ).render_source_binding_sha256
        != baseline.render_source_binding_sha256
    )
    assert (
        RenderDerivationV1.from_render(
            **{**kwargs, "pillow_version": "12.3.1"}
        ).render_source_binding_sha256
        != baseline.render_source_binding_sha256
    )
    with pytest.raises(ValueError, match="source reference"):
        replace(baseline, source_sha256="c" * 64)


def test_admission_receipt_binds_actual_decode_and_rejects_wrong_digest() -> None:
    from sketch2life.infrastructure.canvas_render.renderer import (
        CanvasAdmissionReceiptV1,
        RenderDerivationV1,
    )

    derivation = RenderDerivationV1.from_render(
        source_ref="be1-canvas-source-v1:" + "b" * 64,
        source_sha256="b" * 64,
        render_sha256="a" * 64,
    )
    receipt = CanvasAdmissionReceiptV1.create(
        derivation=derivation,
        render_artifact_ref="local-artifact:00000000-0000-0000-0000-000000000001",
        admitted_content_sha256="a" * 64,
        decoder_container="png_pipe",
        decoder_codec="png",
        decoder_pixel_format="rgb24",
        decoded_width=1024,
        decoded_height=1024,
        admitted_at=datetime(2026, 11, 1, tzinfo=UTC),
    )
    assert receipt.outcome == "ADMITTED"
    assert receipt.admitted_content_sha256 == derivation.render_sha256
    assert receipt.receipt_binding_sha256 in receipt.to_json_bytes().decode("utf-8")
    with pytest.raises(ValueError, match="receipt fields"):
        replace(receipt, admitted_content_sha256="c" * 64)

    with pytest.raises(ValueError, match="does not match"):
        CanvasAdmissionReceiptV1.create(
            derivation=derivation,
            render_artifact_ref="local-artifact:00000000-0000-0000-0000-000000000001",
            admitted_content_sha256="c" * 64,
            decoder_container="png_pipe",
            decoder_codec="png",
            decoder_pixel_format="rgb24",
            decoded_width=1024,
            decoded_height=1024,
            admitted_at=datetime(2026, 11, 1, tzinfo=UTC),
        )
