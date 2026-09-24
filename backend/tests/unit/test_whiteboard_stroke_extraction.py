from __future__ import annotations

import json

import pytest

from sketch2life.infrastructure.media.whiteboard_stroke_extraction import (
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
