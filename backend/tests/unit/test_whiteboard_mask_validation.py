from __future__ import annotations

import pytest

from sketch2life.infrastructure.media.whiteboard_mask_validation import (
    validate_mask_file,
)


def test_mask_validation_returns_coverage_and_bbox(tmp_path) -> None:
    Image = pytest.importorskip("PIL.Image")

    mask_path = tmp_path / "mask.png"
    image = Image.new("L", (100, 80), 0)
    for x in range(20, 60):
        for y in range(10, 50):
            image.putpixel((x, y), 255)
    image.save(mask_path)

    quality = validate_mask_file(mask_path)

    assert quality.width == 100
    assert quality.height == 80
    assert quality.foreground_pixels == 1600
    assert quality.bounding_box == (20, 10, 60, 50)
    assert quality.coverage_ratio == pytest.approx(0.2)


def test_mask_validation_rejects_empty_mask(tmp_path) -> None:
    Image = pytest.importorskip("PIL.Image")

    mask_path = tmp_path / "empty.png"
    Image.new("L", (20, 20), 0).save(mask_path)

    with pytest.raises(ValueError, match="MASK_EMPTY"):
        validate_mask_file(mask_path)


def test_mask_validation_rejects_dense_mask(tmp_path) -> None:
    Image = pytest.importorskip("PIL.Image")

    mask_path = tmp_path / "dense.png"
    Image.new("L", (20, 20), 255).save(mask_path)

    with pytest.raises(ValueError, match="MASK_TOO_DENSE"):
        validate_mask_file(mask_path)
