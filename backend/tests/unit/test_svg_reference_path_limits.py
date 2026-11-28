from __future__ import annotations

import pytest

from sketch2life.infrastructure.svg.sanitizer import (
    MAX_REFERENCE_PATH_CHARS,
    SvgInputRejected,
    sanitize_svg_source,
)


def _svg_with_path(path_data: str) -> bytes:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        f'<path id="bounded-path" d="{path_data}" fill="none" stroke="#20293b"/>'
        "</svg>"
    ).encode("utf-8")


def test_svg_sanitizer_keeps_the_default_path_limit() -> None:
    path_data = "M0 0 " + "L1 1 " * 2_000

    with pytest.raises(SvgInputRejected, match="SVG_PATH_DATA_INVALID"):
        sanitize_svg_source(_svg_with_path(path_data))


def test_svg_sanitizer_allows_only_the_explicit_bounded_reference_limit() -> None:
    path_data = "M0 0 " + "L1 1 " * 2_000
    sanitized = sanitize_svg_source(
        _svg_with_path(path_data),
        max_path_chars=MAX_REFERENCE_PATH_CHARS,
    )
    assert len(sanitized.document["paths"][0]["d"]) > 8_192

    too_long = "M0 0 " + "L1 1 " * 7_000
    with pytest.raises(SvgInputRejected, match="SVG_PATH_DATA_INVALID"):
        sanitize_svg_source(
            _svg_with_path(too_long),
            max_path_chars=MAX_REFERENCE_PATH_CHARS,
        )
