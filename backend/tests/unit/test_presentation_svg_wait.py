"""The slide SVG draft waits long enough for a cold Qwen3.8 container."""

from __future__ import annotations

from sketch2life.infrastructure.lesson_occurrences import presentation_svg_modal as svg


def test_svg_draft_waits_long_enough_for_a_cold_container() -> None:
    assert svg.SVG_DRAFT_WAIT_SECONDS >= 600
    assert svg.SVG_DRAFT_WAIT_SECONDS <= 1800
