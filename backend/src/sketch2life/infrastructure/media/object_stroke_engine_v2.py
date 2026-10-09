"""CPU-only source-object stroke approximation; never recreates source artwork."""

from __future__ import annotations

import hashlib
import io
from typing import Literal

import numpy as np
from PIL import Image, ImageFilter

from sketch2life.application.services.story_world_errors import StoryWorldError
from sketch2life.application.services.story_world_model import SourceAssetRegistry
from sketch2life.contracts.schemas.story_strokes_v2 import ObjectStrokeV2, SourceObjectStrokesV2


class LocalObjectAwareStrokeEngine:
    """CPU implementation of ObjectAwareStrokePort for reviewed source cutouts."""

    def extract_object(
        self, registry: SourceAssetRegistry, object_id: str,
    ) -> SourceObjectStrokesV2:
        return extract_object_strokes(registry, object_id)


def _paths(binary: np.ndarray, *, limit: int = 4000) -> list[tuple[tuple[int, int], ...]]:
    """Walk unvisited 8-neighbor edges; every pen-down step is adjacent."""
    ys, xs = np.nonzero(binary)
    points = {(int(x), int(y)) for y, x in zip(ys, xs, strict=True)}
    if len(points) > limit:
        raise StoryWorldError("NEEDS_STROKE_REVIEW", "too many candidate ink pixels")
    edges: set[tuple[tuple[int, int], tuple[int, int]]] = set()

    def edge_key(a: tuple[int, int], b: tuple[int, int]):
        return (a, b) if a <= b else (b, a)

    neighbors: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for x, y in sorted(points):
        adjacent = [
            (x + dx, y + dy) for dx, dy in
            ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1))
            if (x + dx, y + dy) in points
        ]
        neighbors[(x, y)] = sorted(adjacent)
        for other in adjacent:
            edges.add(edge_key((x, y), other))
    output: list[tuple[tuple[int, int], ...]] = []
    while edges:
        endpoints = sorted(point for point in points if any(
            edge_key(point, n) in edges for n in neighbors[point]
        ) and len(neighbors[point]) != 2)
        start = endpoints[0] if endpoints else min(edges)[0]
        path = [start]
        current = start
        while True:
            options = [n for n in neighbors[current] if edge_key(current, n) in edges]
            if not options:
                break
            nxt = options[0]
            edges.remove(edge_key(current, nxt))
            path.append(nxt)
            current = nxt
            if current == start or len(path) >= 160:
                break
        if len(path) >= 2:
            output.append(tuple(path))
    return output


def extract_object_strokes(
    registry: SourceAssetRegistry, object_id: str,
) -> SourceObjectStrokesV2:
    """Trace mask boundary, local source-color detail and scanline brush trajectories.

    This is inferred order from raster pixels. It is not the child's actual pen history.
    Unsupported/dense cases demand review rather than a substitute geometric character.
    """
    world = registry.world
    spec = next((obj for obj in world.source_objects if obj.object_id == object_id), None)
    if spec is None:
        raise StoryWorldError("SOURCE_ASSET_MISMATCH", "unknown source object ID")
    body = registry.asset_png_by_id.get(object_id)
    mask_body = registry.mask_png_by_id.get(object_id)
    if body is None or hashlib.sha256(body).hexdigest() != spec.asset_sha256:
        raise StoryWorldError("SOURCE_ASSET_MISMATCH", "source cutout missing or changed")
    if mask_body is None or hashlib.sha256(mask_body).hexdigest() != spec.source_mask_sha256:
        raise StoryWorldError("NEEDS_MASK_REVIEW", "source mask missing or changed")
    image = Image.open(io.BytesIO(body)).convert("RGBA")
    rgba = np.asarray(image)
    active = rgba[:, :, 3] > 0
    if not bool(active.any()):
        raise StoryWorldError("NEEDS_STROKE_REVIEW", "empty source cutout")
    interior = active.copy()
    for shifted in (
        np.pad(active[:-1], ((1, 0), (0, 0))),
        np.pad(active[1:], ((0, 1), (0, 0))),
        np.pad(active[:, :-1], ((0, 0), (1, 0))),
        np.pad(active[:, 1:], ((0, 0), (0, 1))),
    ):
        interior &= shifted
    boundary = active & ~interior
    if int(boundary.sum()) < 8:
        raise StoryWorldError("NEEDS_STROKE_REVIEW", "object contour is too small")
    # Local contrast is relative to each object's own colors, not a global ink threshold.
    edges = np.asarray(image.convert("RGB").filter(ImageFilter.FIND_EDGES), dtype=np.uint8)
    strength = edges.max(axis=2)
    deep = interior.copy()
    for shift in (1, 2):
        deep[shift:, :] &= interior[:-shift, :]
        deep[:-shift, :] &= interior[shift:, :]
        deep[:, shift:] &= interior[:, :-shift]
        deep[:, :-shift] &= interior[:, shift:]
    values = strength[deep]
    threshold = max(30, int(np.percentile(values, 92))) if values.size else 255
    details = deep & (strength >= threshold)
    if details.mean() > .25:
        raise StoryWorldError("NEEDS_STROKE_REVIEW", "detail tracing is too dense")
    outline = _paths(boundary)
    detail = _paths(details, limit=2000) if details.any() else []
    if not outline:
        raise StoryWorldError("NEEDS_STROKE_REVIEW", "no continuous object contour")

    def stroke(
        phase: Literal["OUTLINE", "DETAIL", "COLOR"], index: int,
        path: tuple[tuple[int, int], ...], width: int,
    ) -> ObjectStrokeV2:
        colors = [rgba[y, x, :3] for x, y in path]
        median = np.median(np.asarray(colors), axis=0).astype(int)
        return ObjectStrokeV2(
            stroke_id=f"{phase.lower()}-{index:04}", phase=phase, points=path,
            brush_width=width, color_rgb=(int(median[0]), int(median[1]), int(median[2])),
            pen_up_before=True,
        )

    # Brush trajectories follow actual mask runs, alternating direction. The renderer
    # reveals original RGBA under these tracks; no synthesized fill color is used.
    color_paths: list[ObjectStrokeV2] = []
    brush_width = 7
    for row_index, y in enumerate(range(0, image.height, 3)):
        xs = np.flatnonzero(active[y])
        if xs.size == 0:
            continue
        runs = np.split(xs, np.where(np.diff(xs) > 1)[0] + 1)
        for run in runs:
            left, right = int(run[0]), int(run[-1])
            path = ((left, y), (right, y)) if row_index % 2 == 0 else ((right, y), (left, y))
            color_paths.append(stroke("COLOR", len(color_paths) + 1, path, brush_width))
    if not color_paths:
        raise StoryWorldError("NEEDS_STROKE_REVIEW", "cannot create source-color brush paths")
    z_index = next(s.z_index for s in world.initial_states if s.object_id == object_id)
    return SourceObjectStrokesV2(
        object_id=object_id, source_image_sha256=spec.source_image_sha256,
        source_asset_ref=spec.asset_ref, source_asset_sha256=spec.asset_sha256,
        source_mask_ref=spec.source_mask_ref, source_mask_sha256=spec.source_mask_sha256,
        width=image.width, height=image.height, z_index=z_index,
        extraction_method="MASK_BOUNDARY_AND_LOCAL_CONTRAST_V1",
        outline_paths=tuple(stroke("OUTLINE", i, p, 2) for i, p in enumerate(outline, 1)),
        detail_paths=tuple(stroke("DETAIL", i, p, 2) for i, p in enumerate(detail, 1)),
        color_paths=tuple(color_paths), covered_source_pixels=int(active.sum()),
    )
