from __future__ import annotations

import json

import pytest

from sketch2life.infrastructure.media.whiteboard_stroke_extraction import (
    extract_image_line_art,
    extract_mask_contours,
)


def test_extract_mask_contours_writes_source_bound_artifact(tmp_path) -> None:
    Image = pytest.importorskip("PIL.Image")
    mask_path = tmp_path / "mask.png"
    output_path = tmp_path / "strokes.json"
    image = Image.new("L", (20, 20), 0)
    for x in range(5, 15):
        for y in range(4, 16):
            image.putpixel((x, y), 255)
    image.save(mask_path)

    result = extract_mask_contours(
        mask_path,
        output_path,
        source_hash="a" * 64,
    )
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert result.source_hash == "a" * 64
    assert result.stroke_count == 1
    assert result.point_count > 0
    assert payload["source_hash"] == "a" * 64
    assert payload["strokes"][0]["points"]


def test_extract_mask_contours_rejects_empty_mask(tmp_path) -> None:
    Image = pytest.importorskip("PIL.Image")
    mask_path = tmp_path / "empty.png"
    Image.new("L", (20, 20), 0).save(mask_path)

    with pytest.raises(ValueError, match="MASK_EMPTY"):
        extract_mask_contours(mask_path, tmp_path / "strokes.json", source_hash="a" * 64)


def test_extract_image_line_art_keeps_separate_marks_as_separate_strokes(tmp_path) -> None:
    Image = pytest.importorskip("PIL.Image")
    ImageDraw = pytest.importorskip("PIL.ImageDraw")
    image = Image.new("RGB", (160, 80), "white")
    draw = ImageDraw.Draw(image)
    draw.line((10, 15, 45, 15), fill="black", width=4)
    draw.line((105, 55, 145, 55), fill="black", width=4)
    source = tmp_path / "source.png"
    image.save(source)

    result = extract_image_line_art(source, tmp_path / "strokes.json", source_hash="b" * 64)
    payload = json.loads((tmp_path / "strokes.json").read_text(encoding="utf-8"))

    assert result.stroke_count >= 2
    assert all(
        abs(b[0] - a[0]) <= 1 and abs(b[1] - a[1]) <= 1
        for stroke in payload["strokes"]
        for a, b in zip(stroke["points"], stroke["points"][1:], strict=False)
    )
