from __future__ import annotations

import pytest

from sketch2life.infrastructure.svg.openclipart_guide import build_openclipart_guide
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
    ).encode()


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


def test_curated_turtle_guide_preserves_the_full_color_reference() -> None:
    result = build_openclipart_guide("turtle")

    assert result is not None
    assert result.reference_source.asset_id == "openclipart-turtle-illustration-v1"
    assert len(result.reference_illustration.paths) == 8
    assert max(len(path.d) for path in result.reference_illustration.paths) > 8_192
    assert (
        max(len(path.d) for path in result.reference_illustration.paths) <= MAX_REFERENCE_PATH_CHARS
    )
    assert len(result.generated.stages) == 6
