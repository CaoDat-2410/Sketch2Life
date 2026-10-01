"""Transient, bounded subject-only image crops for the post-Gate-B planner."""

from __future__ import annotations

import io

from PIL import Image

from sketch2life.contracts.schemas.scene_exploration import SourceRegionV1

_MAX_SOURCE_BYTES = 5_000_000
_MAX_CROP_BYTES = 1_000_000
_MAX_OUTPUT_EDGE = 512


class PixiSubjectCropUnavailable(Exception):
    """No safely bounded, mask-grounded crop could be produced."""


def build_pixi_subject_crop(
    source_bytes: bytes, parent_mask_png: bytes
) -> tuple[bytes, str, SourceRegionV1]:
    if (
        not source_bytes
        or len(source_bytes) > _MAX_SOURCE_BYTES
        or not parent_mask_png
        or len(parent_mask_png) > _MAX_SOURCE_BYTES
    ):
        raise PixiSubjectCropUnavailable from None
    try:
        with Image.open(io.BytesIO(source_bytes)) as source_file:
            source = source_file.convert("RGB")
        with Image.open(io.BytesIO(parent_mask_png)) as mask_file:
            mask = mask_file.convert("L")
    except (OSError, ValueError):
        raise PixiSubjectCropUnavailable from None
    if source.size != mask.size:
        raise PixiSubjectCropUnavailable from None
    binary = mask.point(lambda value: 255 if value >= 128 else 0)
    subject_bounds = binary.getbbox()
    if subject_bounds is None:
        raise PixiSubjectCropUnavailable from None

    left, top, right, bottom = subject_bounds
    source_width, source_height = source.size
    subject_region = SourceRegionV1(
        x=left / source_width,
        y=top / source_height,
        width=(right - left) / source_width,
        height=(bottom - top) / source_height,
    )
    subject_area_ratio = ((right - left) * (bottom - top)) / (source_width * source_height)
    if subject_area_ratio >= 0.95:
        # A near-full-frame mask is not a minimized crop; do not upload the source by default.
        raise PixiSubjectCropUnavailable from None
    padding_x = max(4, round((right - left) * 0.08))
    padding_y = max(4, round((bottom - top) * 0.08))
    bounds = (
        max(0, left - padding_x),
        max(0, top - padding_y),
        min(source_width, right + padding_x),
        min(source_height, bottom + padding_y),
    )
    crop = source.crop(bounds)
    crop.thumbnail((_MAX_OUTPUT_EDGE, _MAX_OUTPUT_EDGE), Image.Resampling.LANCZOS)

    png = io.BytesIO()
    crop.save(png, format="PNG", optimize=True)
    image_bytes = png.getvalue()
    if len(image_bytes) <= _MAX_CROP_BYTES:
        return image_bytes, "image/png", subject_region
    jpeg = io.BytesIO()
    crop.save(jpeg, format="JPEG", quality=82, optimize=True)
    image_bytes = jpeg.getvalue()
    if not image_bytes or len(image_bytes) > _MAX_CROP_BYTES:
        raise PixiSubjectCropUnavailable from None
    return image_bytes, "image/jpeg", subject_region


__all__ = ["PixiSubjectCropUnavailable", "build_pixi_subject_crop"]
