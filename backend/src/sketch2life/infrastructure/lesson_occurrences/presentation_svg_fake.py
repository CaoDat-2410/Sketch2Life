"""Deterministic local fake for tests. Production composition must never import this module."""

from __future__ import annotations

from sketch2life.application.ports.presentation_svg import (
    PresentationSvgDraftInput,
    PresentationSvgDraftOutput,
)


class DeterministicPresentationSvgDrafter:
    def draft(self, request: PresentationSvgDraftInput) -> PresentationSvgDraftOutput:
        if request.schema_version != "sketch2life.presentation-svg-input.v1":
            raise ValueError("unsupported request schema")
        if not request.activity_title or not request.subject_text:
            raise ValueError("missing bounded input")
        source = (
            b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
            b'<circle cx="50" cy="50" r="32" fill="none" stroke="#1f2937" '
            b'stroke-width="4"/><path d="M35 55 L48 67 L69 39" fill="none" '
            b'stroke="#2563eb" stroke-width="5"/><path id="guide-3" '
            b'd="M12 15 L28 15 L28 30" fill="none" stroke="#2563eb" '
            b'stroke-width="3"/><path id="guide-4" d="M72 68 L84 80" fill="none" '
            b'stroke="#1f2937" stroke-width="3"/></svg>'
        )
        return PresentationSvgDraftOutput(
            source=source,
            generator_name="sketch2life-local-fake",
            generator_version="1",
            license_id="CC0-1.0",
        )


__all__ = ["DeterministicPresentationSvgDrafter"]
