"""Sanitized vector visual guides for approved, child-safe story props."""

from __future__ import annotations

import hashlib
import io
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

LEAF_GUIDE_SVG = b'''<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
  <path d="M 956 370 C 981 371 1006 391 1018 415 C 992 413 968 395 956 370 Z" fill="#58b93d" stroke="#1c345e" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M 1018 415 C 998 398 977 381 956 370" fill="none" stroke="#1c345e" stroke-width="2.5" stroke-linecap="round"/>
</svg>'''

_SVG_NS = "http://www.w3.org/2000/svg"
_ALLOWED_TAGS = {f"{{{_SVG_NS}}}svg", f"{{{_SVG_NS}}}path"}
_ALLOWED_ATTRIBUTES = {
    "xmlns",
    "width",
    "height",
    "viewBox",
    "d",
    "fill",
    "stroke",
    "stroke-width",
    "stroke-linecap",
    "stroke-linejoin",
}


class StoryImageGuideError(ValueError):
    """An unsafe or invalid SVG visual guide."""


def sanitize_leaf_guide_svg(svg_bytes: bytes = LEAF_GUIDE_SVG) -> bytes:
    """Validate the SVG against a tiny static-element allowlist."""

    if svg_bytes != LEAF_GUIDE_SVG:
        raise StoryImageGuideError("STORY_IMAGE_GUIDE_SVG_UNSAFE")
    try:
        root = ET.fromstring(svg_bytes)
    except (ET.ParseError, TypeError) as exc:
        raise StoryImageGuideError("STORY_IMAGE_GUIDE_SVG_INVALID") from exc
    if root.tag != f"{{{_SVG_NS}}}svg" or root.attrib != {
        "width": "1280",
        "height": "720",
        "viewBox": "0 0 1280 720",
    }:
        raise StoryImageGuideError("STORY_IMAGE_GUIDE_SVG_INVALID")
    nodes = list(root.iter())
    if len(nodes) != 3 or any(node.tag not in _ALLOWED_TAGS for node in nodes):
        raise StoryImageGuideError("STORY_IMAGE_GUIDE_SVG_UNSAFE")
    if any(set(node.attrib) - _ALLOWED_ATTRIBUTES for node in nodes):
        raise StoryImageGuideError("STORY_IMAGE_GUIDE_SVG_UNSAFE")
    if any(node.text and node.text.strip() for node in nodes):
        raise StoryImageGuideError("STORY_IMAGE_GUIDE_SVG_UNSAFE")
    return ET.tostring(root, encoding="utf-8")


def render_leaf_guide_frame(
    conditioning_frame_path: str | Path,
    output_path: str | Path,
) -> dict[str, Any]:
    """Composite the one-leaf SVG over a derived frame without changing its source."""

    from PIL import Image
    import cairosvg

    svg_bytes = sanitize_leaf_guide_svg()
    with Image.open(conditioning_frame_path) as opened:
        base = opened.convert("RGBA")
    overlay_bytes = cairosvg.svg2png(
        bytestring=svg_bytes,
        output_width=base.width,
        output_height=base.height,
    )
    with Image.open(io.BytesIO(overlay_bytes)) as opened_overlay:
        overlay = opened_overlay.convert("RGBA")
    composite = Image.alpha_composite(base, overlay).convert("RGB")
    output = Path(output_path)
    composite.save(output, format="PNG", optimize=True)
    png_sha256 = hashlib.sha256(output.read_bytes()).hexdigest()
    return {
        "guide_kind": "SINGLE_LEAF_SVG",
        "svg_sha256": hashlib.sha256(svg_bytes).hexdigest(),
        "png_sha256": png_sha256,
        "width": base.width,
        "height": base.height,
    }


def validate_leaf_guide_renderer_runtime() -> dict[str, str]:
    """Render and decode a tiny probe before the worker spends GPU time."""

    try:
        import cairosvg
        from PIL import Image
    except ImportError as exc:
        raise StoryImageGuideError("STORY_IMAGE_GUIDE_RENDERER_UNAVAILABLE") from exc

    try:
        probe_bytes = cairosvg.svg2png(
            bytestring=sanitize_leaf_guide_svg(),
            output_width=32,
            output_height=18,
        )
        with Image.open(io.BytesIO(probe_bytes)) as probe:
            probe.verify()
        with Image.open(io.BytesIO(probe_bytes)) as probe:
            if probe.size != (32, 18):
                raise StoryImageGuideError("STORY_IMAGE_GUIDE_RENDERER_BAD_DIMENSIONS")
    except StoryImageGuideError:
        raise
    except Exception as exc:
        raise StoryImageGuideError("STORY_IMAGE_GUIDE_RENDERER_FAILED") from exc

    return {
        "cairosvg_version": str(getattr(cairosvg, "__version__", "unknown")),
        "pillow_version": str(getattr(Image, "__version__", "unknown")),
    }


__all__ = [
    "LEAF_GUIDE_SVG",
    "StoryImageGuideError",
    "render_leaf_guide_frame",
    "sanitize_leaf_guide_svg",
    "validate_leaf_guide_renderer_runtime",
]
