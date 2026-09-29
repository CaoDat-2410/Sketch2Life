"""Deterministic, mask-bounded fallback partitioning for common drawing archetypes."""

from __future__ import annotations

import io
from dataclasses import dataclass

from PIL import Image

from sketch2life.contracts.schemas.auto_rig import RigArchetype
from sketch2life.contracts.schemas.scene_exploration import SourceRegionV1


@dataclass(frozen=True, slots=True)
class DerivedPartMask:
    part_id: str
    role: str
    bone_id: str
    source_region: SourceRegionV1
    confidence: float
    mask_png: bytes


_ROLE_ANCHORS: dict[RigArchetype, tuple[tuple[str, str, str, float, float], ...]] = {
    RigArchetype.BUTTERFLY: (
        ("left-wing", "left-wing", "left-wing", 0.23, 0.39),
        ("body", "body", "root", 0.50, 0.50),
        ("right-wing", "right-wing", "right-wing", 0.77, 0.39),
    ),
    RigArchetype.BIRD: (
        ("head", "head", "head", 0.53, 0.18),
        ("body", "body", "root", 0.50, 0.58),
        ("wing", "wing", "wing", 0.20, 0.43),
    ),
    RigArchetype.FLOWER: (
        ("crown", "crown", "crown", 0.50, 0.27),
        ("stem", "stem", "stem", 0.50, 0.76),
    ),
    RigArchetype.TREE_BRANCH: (
        ("crown", "crown", "crown", 0.50, 0.27),
        ("stem", "stem", "stem", 0.50, 0.76),
    ),
    RigArchetype.FISH: (
        ("tail", "tail", "tail", 0.16, 0.50),
        ("body", "body", "root", 0.50, 0.50),
        ("head", "head", "head", 0.84, 0.50),
    ),
    RigArchetype.BIPED: (
        ("head", "head", "head", 0.50, 0.15),
        ("torso", "torso", "root", 0.50, 0.47),
        ("left-leg", "left-leg", "left-leg", 0.34, 0.82),
        ("right-leg", "right-leg", "right-leg", 0.66, 0.82),
    ),
}


def derive_part_masks_from_subject_mask(
    source_image: bytes,
    subject_mask_png: bytes,
    archetype: RigArchetype,
) -> tuple[DerivedPartMask, ...]:
    """Partition a verified silhouette into bounded pose targets without inventing pixels.

    The image/subject silhouette is preserved exactly: every output is a disjoint subset of the
    supplied subject mask. This deterministic fallback uses archetype-relative spatial anchors;
    it is used only when the model did not return usable independent masks and is deliberately
    unavailable for generic/unknown shapes.
    """
    anchors = _ROLE_ANCHORS.get(archetype)
    if anchors is None:
        return ()
    try:
        with Image.open(io.BytesIO(source_image)) as source:
            source_size = source.size
        with Image.open(io.BytesIO(subject_mask_png)) as mask_source:
            mask = mask_source.convert("L")
    except (OSError, ValueError):
        return ()
    if mask.size != source_size:
        return ()

    binary = mask.point(lambda value: 255 if value >= 128 else 0)
    bounds = binary.getbbox()
    if bounds is None:
        return ()
    left, top, right, bottom = bounds
    box_width = right - left
    box_height = bottom - top
    subject_pixels = binary.load()
    if subject_pixels is None:
        return ()
    width, height = binary.size
    counts = [0] * len(anchors)
    assignments = bytearray(width * height)

    for y in range(top, bottom):
        v = (y + 0.5 - top) / box_height
        for x in range(left, right):
            if subject_pixels[x, y] == 0:
                continue
            u = (x + 0.5 - left) / box_width
            selected = min(
                range(len(anchors)),
                key=lambda index: _anchor_distance(u, v, anchors[index][3], anchors[index][4]),
            )
            assignments[y * width + x] = selected + 1
            counts[selected] += 1

    total = sum(counts)
    if total == 0:
        return ()
    # Reject sliver partitions: they look like accidental crops rather than useful rig parts.
    if sum(count >= max(12, round(total * 0.025)) for count in counts) < 2:
        return ()

    results: list[DerivedPartMask] = []
    for index, (part_id, role, bone_id, _anchor_x, _anchor_y) in enumerate(anchors):
        count = counts[index]
        if count < max(12, round(total * 0.025)):
            continue
        pixels = Image.new("L", (width, height), 0)
        pixel_data = pixels.load()
        if pixel_data is None:
            continue
        min_x, min_y, max_x, max_y = width, height, -1, -1
        for y in range(top, bottom):
            row_start = y * width
            for x in range(left, right):
                if assignments[row_start + x] != index + 1:
                    continue
                pixel_data[x, y] = 255
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
        if max_x < min_x or max_y < min_y:
            continue
        output = io.BytesIO()
        pixels.save(output, format="PNG", optimize=True)
        results.append(
            DerivedPartMask(
                part_id=part_id,
                role=role,
                bone_id=bone_id,
                source_region=SourceRegionV1(
                    x=min_x / width,
                    y=min_y / height,
                    width=(max_x + 1 - min_x) / width,
                    height=(max_y + 1 - min_y) / height,
                ),
                confidence=0.7,
                mask_png=output.getvalue(),
            )
        )
    return tuple(results) if len(results) >= 2 else ()


def _anchor_distance(u: float, v: float, anchor_x: float, anchor_y: float) -> float:
    # Slightly favor vertical articulation; the supported silhouettes are mostly upright.
    return (u - anchor_x) ** 2 + 1.15 * (v - anchor_y) ** 2


__all__ = ["DerivedPartMask", "derive_part_masks_from_subject_mask"]
