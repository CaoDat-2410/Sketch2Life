"""SVG parsing, canonicalization, and deterministic rendering adapters."""

from sketch2life.infrastructure.svg.renderer import render_svg_document
from sketch2life.infrastructure.svg.sanitizer import (
    SanitizedSvg,
    SvgInputRejected,
    sanitize_svg_source,
)

__all__ = ["SanitizedSvg", "SvgInputRejected", "render_svg_document", "sanitize_svg_source"]
