"""Evidence-bounded color-component proposals inside a verified subject silhouette."""

from __future__ import annotations

import io
import math
from collections import deque
from dataclasses import dataclass
from typing import Any, cast

from PIL import Image, ImageChops

from sketch2life.contracts.schemas.auto_rig import RigArchetype
from sketch2life.contracts.schemas.scene_exploration import SourceRegionV1

_SAMPLE_EDGE = 512
_COLOR_DISTANCE_SQUARED = 55 * 55
_MIN_COMPONENT_RATIO = 0.02
_MIN_COMPONENT_PIXELS = 16
_MIN_BOUNDARY_CONTRAST = 0.30


@dataclass(frozen=True, slots=True)
class DerivedPartMask:
    part_id: str
    role: str
    bone_id: str
    source_region: SourceRegionV1
    confidence: float
    mask_png: bytes
    boundary_contrast: float
    anchor_fit: float


# Anchors nominate candidate roles only. They never partition or assign source pixels.
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
    """Propose only large, color-connected regions with visible boundaries.

    The parent mask is authoritative. Archetype anchors only assign a label to a region after
    image evidence identifies that region; they never manufacture a Voronoi partition. Therefore
    a same-color silhouette with no internal boundary returns no parts and remains subject-only.
    Processing is bounded to a 512px working image, and every output is clipped to the original
    verified parent mask after being scaled back up.
    """
    anchors = _ROLE_ANCHORS.get(archetype)
    if anchors is None:
        return ()
    try:
        with Image.open(io.BytesIO(source_image)) as source_image_file:
            source = source_image_file.convert("RGB")
        with Image.open(io.BytesIO(subject_mask_png)) as mask_file:
            original_mask = mask_file.convert("L")
    except (OSError, ValueError):
        return ()
    if source.size != original_mask.size:
        return ()

    original_mask = original_mask.point(lambda value: 255 if value >= 128 else 0)
    bounds = original_mask.getbbox()
    if bounds is None:
        return ()
    sample_size = _bounded_size(source.size)
    sample_source = source.resize(sample_size, Image.Resampling.BILINEAR)
    sample_mask = original_mask.resize(sample_size, Image.Resampling.NEAREST)
    mask_bounds = sample_mask.getbbox()
    if mask_bounds is None:
        return ()
    left, top, right, bottom = mask_bounds
    width, height = sample_size
    source_pixels = sample_source.load()
    mask_pixels = sample_mask.load()
    if source_pixels is None or mask_pixels is None:
        return ()

    visited = bytearray(width * height)
    components: list[list[int]] = []
    total_parent_pixels = sum(
        1
        for y in range(top, bottom)
        for x in range(left, right)
        if mask_pixels[x, y] != 0
    )
    min_area = max(_MIN_COMPONENT_PIXELS, round(total_parent_pixels * _MIN_COMPONENT_RATIO))

    for y in range(top, bottom):
        for x in range(left, right):
            start = y * width + x
            if mask_pixels[x, y] == 0 or visited[start]:
                continue
            visited[start] = 1
            seed_color = cast(tuple[int, ...], source_pixels[x, y])
            queue = deque([start])
            component: list[int] = []
            while queue:
                current = queue.popleft()
                component.append(current)
                current_x = current % width
                current_y = current // width
                for next_x, next_y in (
                    (current_x - 1, current_y),
                    (current_x + 1, current_y),
                    (current_x, current_y - 1),
                    (current_x, current_y + 1),
                ):
                    if not (left <= next_x < right and top <= next_y < bottom):
                        continue
                    next_index = next_y * width + next_x
                    if visited[next_index] or mask_pixels[next_x, next_y] == 0:
                        continue
                    next_color = cast(tuple[int, ...], source_pixels[next_x, next_y])
                    if _color_distance_squared(seed_color, next_color) > (
                        _COLOR_DISTANCE_SQUARED
                    ):
                        continue
                    visited[next_index] = 1
                    queue.append(next_index)
            if len(component) >= min_area:
                components.append(component)

    if len(components) < 2:
        return ()

    candidates: dict[str, tuple[float, list[int], str, str, float, float, float]] = {}
    for component in components:
        evidence = _measure_component_evidence(
            component=component,
            source_pixels=source_pixels,
            mask_pixels=mask_pixels,
            width=width,
            height=height,
        )
        if evidence is None:
            continue
        center_x, center_y, boundary_contrast = evidence
        normalized_x = (center_x - left) / max(1, right - left)
        normalized_y = (center_y - top) / max(1, bottom - top)
        role_anchor = min(
            anchors,
            key=lambda anchor: _anchor_distance(
                normalized_x, normalized_y, anchor[3], anchor[4]
            ),
        )
        anchor_distance = math.sqrt(
            _anchor_distance(normalized_x, normalized_y, role_anchor[3], role_anchor[4])
        )
        anchor_fit = max(0.0, min(1.0, 1.0 - anchor_distance / 0.65))
        confidence = round(0.65 * boundary_contrast + 0.35 * anchor_fit, 4)
        if boundary_contrast < _MIN_BOUNDARY_CONTRAST or confidence < 0.45:
            continue
        part_id, part_role, bone_id, *_ = role_anchor
        existing = candidates.get(part_id)
        score = confidence * math.sqrt(len(component))
        if existing is None or score > existing[0]:
            candidates[part_id] = (
                score,
                component,
                part_role,
                bone_id,
                confidence,
                boundary_contrast,
                anchor_fit,
            )

    if len(candidates) < 2:
        return ()

    results: list[DerivedPartMask] = []
    for part_id, (
        _score,
        component,
        role,
        bone_id,
        confidence,
        boundary_contrast,
        anchor_fit,
    ) in candidates.items():
        sample_part = Image.new("L", sample_size, 0)
        sample_pixels = sample_part.load()
        if sample_pixels is None:
            continue
        for index in component:
            sample_pixels[index % width, index // width] = 255
        full_size_part = sample_part.resize(source.size, Image.Resampling.NEAREST)
        full_size_part = ImageChops.darker(full_size_part, original_mask)
        part_bounds = full_size_part.getbbox()
        if part_bounds is None:
            continue
        min_x, min_y, max_x, max_y = part_bounds
        output = io.BytesIO()
        full_size_part.save(output, format="PNG", optimize=True)
        results.append(
            DerivedPartMask(
                part_id=part_id,
                role=role,
                bone_id=bone_id,
                source_region=SourceRegionV1(
                    x=min_x / source.width,
                    y=min_y / source.height,
                    width=(max_x + 1 - min_x) / source.width,
                    height=(max_y + 1 - min_y) / source.height,
                ),
                confidence=confidence,
                mask_png=output.getvalue(),
                boundary_contrast=boundary_contrast,
                anchor_fit=anchor_fit,
            )
        )
    return tuple(results) if len(results) >= 2 else ()


def _bounded_size(size: tuple[int, int]) -> tuple[int, int]:
    width, height = size
    scale = min(1.0, _SAMPLE_EDGE / max(width, height))
    return max(1, round(width * scale)), max(1, round(height * scale))


def _color_distance_squared(first: tuple[int, ...], second: tuple[int, ...]) -> int:
    return sum((int(a) - int(b)) ** 2 for a, b in zip(first[:3], second[:3], strict=True))


def _measure_component_evidence(
    *,
    component: list[int],
    source_pixels: Any,
    mask_pixels: Any,
    width: int,
    height: int,
) -> tuple[float, float, float] | None:
    # Pillow's pixel access object is deliberately kept private to this bounded helper.
    component_set = set(component)
    boundary_contrasts: list[float] = []
    x_total = 0
    y_total = 0
    for index in component:
        x = index % width
        y = index // width
        x_total += x
        y_total += y
        current_color = cast(tuple[int, ...], source_pixels[x, y])
        for neighbor_x, neighbor_y in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if not (0 <= neighbor_x < width and 0 <= neighbor_y < height):
                continue
            neighbor_index = neighbor_y * width + neighbor_x
            if neighbor_index in component_set or mask_pixels[neighbor_x, neighbor_y] == 0:
                continue
            neighbor_color = cast(tuple[int, ...], source_pixels[neighbor_x, neighbor_y])
            distance = math.sqrt(_color_distance_squared(current_color, neighbor_color))
            boundary_contrasts.append(min(1.0, distance / 220.0))
    if not boundary_contrasts:
        return None
    contrast = sum(boundary_contrasts) / len(boundary_contrasts)
    if contrast < _MIN_BOUNDARY_CONTRAST:
        return None
    return x_total / len(component), y_total / len(component), contrast


def _anchor_distance(u: float, v: float, anchor_x: float, anchor_y: float) -> float:
    return (u - anchor_x) ** 2 + 1.15 * (v - anchor_y) ** 2


__all__ = ["DerivedPartMask", "derive_part_masks_from_subject_mask"]
