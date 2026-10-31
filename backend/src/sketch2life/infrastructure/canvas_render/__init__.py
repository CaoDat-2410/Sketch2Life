"""Versioned, CPU-only rendering and receipt contracts for accepted BE1 canvas sources."""

from sketch2life.infrastructure.canvas_render.renderer import (
    CANVAS_EXPORT_SPEC_VERSION,
    CANVAS_RENDERER_VERSION,
    CanvasAdmissionReceiptV1,
    CanvasRenderHandoffV1,
    CanvasRenderResultV1,
    RenderDerivationV1,
    profile_width_pixels,
    render_canvas_source,
)

__all__ = [
    "CANVAS_EXPORT_SPEC_VERSION",
    "CANVAS_RENDERER_VERSION",
    "CanvasAdmissionReceiptV1",
    "CanvasRenderHandoffV1",
    "CanvasRenderResultV1",
    "RenderDerivationV1",
    "profile_width_pixels",
    "render_canvas_source",
]
