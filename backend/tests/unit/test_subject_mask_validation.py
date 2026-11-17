from io import BytesIO

import pytest
from PIL import Image, ImageDraw

from sketch2life.application.services.auto_rig.mask_validation import subject_mask_rejection


def _png(image: Image.Image) -> bytes:
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


@pytest.mark.parametrize(
    ("rows", "reason"),
    [(0, "MASK_AREA_INVALID"), (15, None), (16, "MASK_AREA_INVALID"), (20, "MASK_AREA_INVALID")],
)
def test_subject_mask_uses_renderer_area_boundaries(rows: int, reason: str | None) -> None:
    source = _png(Image.new("RGB", (20, 20), "white"))
    mask = Image.new("L", (20, 20), 0)
    if rows:
        ImageDraw.Draw(mask).rectangle((0, 0, 19, rows - 1), fill=255)
    assert subject_mask_rejection(source, _png(mask)) == reason


@pytest.mark.parametrize("mode", ["RGBA", "LA"])
def test_white_but_transparent_mask_is_empty(mode: str) -> None:
    source = _png(Image.new("RGB", (20, 20), "white"))
    color = (255, 255, 255, 0) if mode == "RGBA" else (255, 0)
    assert subject_mask_rejection(
        source, _png(Image.new(mode, (20, 20), color))
    ) == "MASK_AREA_INVALID"


def test_color_average_matches_renderer_instead_of_luminance() -> None:
    source = _png(Image.new("RGB", (20, 20), "white"))
    # Average RGB = 8 is outside; conventional luminance would admit this green.
    assert subject_mask_rejection(
        source, _png(Image.new("RGBA", (20, 20), (0, 24, 0, 255)))
    ) == "MASK_AREA_INVALID"
    mask = Image.new("RGBA", (20, 20), (0, 0, 0, 255))
    ImageDraw.Draw(mask).rectangle((0, 0, 19, 14), fill=(0, 26, 0, 255))
    assert subject_mask_rejection(source, _png(mask)) is None


def test_mismatched_dimensions_are_rejected() -> None:
    assert subject_mask_rejection(
        _png(Image.new("RGB", (20, 20), "white")),
        _png(Image.new("L", (10, 20), 255)),
    ) == "MASK_DIMENSIONS_INVALID"


def test_corrupt_png_is_rejected_without_pixel_decode_failure_escaping() -> None:
    source = _png(Image.new("RGB", (20, 20), "white"))
    assert subject_mask_rejection(source, b"\x89PNG\r\n\x1a\ninvalid") == "MASK_ENCODING_INVALID"
