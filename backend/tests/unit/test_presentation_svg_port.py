"""The SVG drafter stays behind a minimal, fail-closed application port."""

from __future__ import annotations

from dataclasses import fields
from pathlib import Path

from sketch2life.application.ports.presentation_svg import PresentationSvgDraftInput
from sketch2life.infrastructure.lesson_occurrences.presentation_svg_fake import (
    DeterministicPresentationSvgDrafter,
)
from sketch2life.infrastructure.svg.sanitizer import sanitize_svg_source

BACKEND = Path(__file__).resolve().parents[2]


def test_production_composition_is_fail_closed_and_does_not_import_the_fake() -> None:
    composition = BACKEND / "src" / "sketch2life" / "interfaces" / "http" / "router_composition.py"
    app_composition = BACKEND / "src" / "sketch2life" / "interfaces" / "http" / "app.py"
    source = composition.read_text(encoding="utf-8")
    assert "build_presentation_svg_drafter(settings)" in source
    assert "presentation_svg_fake" not in source
    assert "presentation_svg_fake" not in app_composition.read_text(encoding="utf-8")


def test_port_input_has_only_the_bounded_activity_and_subject_fields() -> None:
    assert [field.name for field in fields(PresentationSvgDraftInput)] == [
        "schema_version", "activity_title", "subject_text",
    ]
    request = PresentationSvgDraftInput(
        schema_version="sketch2life.presentation-svg-input.v1",
        activity_title="Draw a shape",
        subject_text="butterfly",
    )
    first = DeterministicPresentationSvgDrafter().draft(request)
    second = DeterministicPresentationSvgDrafter().draft(request)
    assert first == second
    assert b"<svg" in first.source
    sanitized = sanitize_svg_source(first.source)
    assert sanitized.readiness["classification"] == "REQUIRES_MANUAL_AUTHORING"
    assert (first.generator_name, first.generator_version, first.license_id) == (
        "sketch2life-local-fake", "1", "CC0-1.0",
    )
