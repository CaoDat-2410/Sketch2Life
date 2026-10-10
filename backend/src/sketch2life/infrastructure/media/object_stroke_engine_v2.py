"""CPU-only source-object stroke approximation; never recreates source artwork."""

from __future__ import annotations

import hashlib
import io
from collections import deque
from typing import Literal

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from sketch2life.application.services.story_world_errors import StoryWorldError
from sketch2life.application.services.story_world_model import SourceAssetRegistry
from sketch2life.contracts.schemas.story_strokes_v2 import (
    ObjectStrokeV2,
    SourceObjectStrokesV2,
    StrokeProcessingDiagnosticsV2,
)

MAX_TRACE_PIXELS = 24_000
MAX_OBJECT_PATHS = 4096
TRACE_TILE_SIZE = 32  # <= 1024 pixels, below the unchanged 2000-point detail graph limit.


def _structural_details(
    image: Image.Image, deep: np.ndarray, strength: np.ndarray, threshold: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Heuristic, not semantic recognition: persistent contrast/ink vs pencil grain.

    Dark ink and strong chromatic accents protect thin stems, eyes and petals.
    Low-contrast high-frequency candidates are retained by source-color reveal.
    """
    rgb = np.asarray(image.convert("RGB"), dtype=np.int16)
    smooth = image.convert("RGB").filter(ImageFilter.GaussianBlur(.7))
    persistent = np.asarray(smooth.filter(ImageFilter.FIND_EDGES)).max(axis=2)
    dark = rgb.max(axis=2) <= 145
    chromatic = (rgb.min(axis=2) <= 100) & (rgb.max(axis=2) - rgb.min(axis=2) >= 60)
    raw = deep & (strength >= threshold)
    structural = raw & ((persistent >= max(30, threshold * .55)) | dark | chromatic)
    # Include dark thin lines missed by the percentile threshold, not flat dark masses.
    structural |= deep & dark & (strength >= 30)
    return structural, raw & ~structural


def _paths_clustered(
    binary: np.ndarray,
) -> tuple[list[tuple[tuple[int, int], ...]], int, int]:
    """Trace bounded 8-connected clusters in original asset coordinates.

    Tiles bound transient neighbor sets; they do not crop/recolor source assets.
    Every selected pixel, including isolated dots and tile seams, is retained.
    """
    total = int(binary.sum())
    if total > MAX_TRACE_PIXELS:
        raise StoryWorldError(
            "NEEDS_STROKE_REVIEW", f"{total} structural pixels exceed bounded {MAX_TRACE_PIXELS}",
        )
    offsets = ((-1, 0), (1, 0), (0, -1), (0, 1),
               (-1, -1), (1, -1), (-1, 1), (1, 1))
    output: list[tuple[tuple[int, int], ...]] = []
    clusters = maximum = visited = 0
    height, width = binary.shape
    for top in range(0, height, TRACE_TILE_SIZE):
        for left in range(0, width, TRACE_TILE_SIZE):
            ys, xs = np.nonzero(binary[top:top + TRACE_TILE_SIZE, left:left + TRACE_TILE_SIZE])
            remaining = {(int(x) + left, int(y) + top)
                         for y, x in zip(ys, xs, strict=True)}
            if not remaining:
                continue
            maximum = max(maximum, len(remaining))

            def adjacent(
                point: tuple[int, int], pool: set[tuple[int, int]] = remaining,
            ) -> list[tuple[int, int]]:
                x, y = point
                return sorted((x + dx, y + dy) for dx, dy in offsets
                              if (x + dx, y + dy) in pool)

            endpoints = deque(point for point in sorted(remaining) if len(adjacent(point)) == 1)
            while remaining:
                while endpoints and endpoints[0] not in remaining:
                    endpoints.popleft()
                current = endpoints.popleft() if endpoints else min(remaining)
                path = [current]
                remaining.remove(current)
                visited += 1
                clusters += 1
                while len(path) < 256:
                    choices = adjacent(current)
                    if not choices:
                        break
                    if len(path) < 2:
                        nxt = choices[0]
                    else:
                        vx, vy = current[0] - path[-2][0], current[1] - path[-2][1]
                        nxt = max(choices, key=lambda p: (
                            vx * (p[0] - current[0]) + vy * (p[1] - current[1]),
                            -abs(vx * (p[1] - current[1]) - vy * (p[0] - current[0])),
                            -p[1], -p[0],
                        ))
                    current = nxt
                    path.append(current)
                    remaining.remove(current)
                    visited += 1
                output.append(tuple(path if len(path) > 1 else path * 2))
                if len(output) > MAX_OBJECT_PATHS:
                    raise StoryWorldError(
                        "NEEDS_STROKE_REVIEW",
                        "too many structural pen lifts; no details discarded",
                    )
    if visited != total:
        raise StoryWorldError("NEEDS_STROKE_REVIEW", "selected structural pixels were lost")
    return output, clusters, maximum


def _coherent_details(image: Image.Image, structural: np.ndarray) -> np.ndarray:
    """Defer tiny unanchored edge islands to color; retain small dark facial marks."""
    if int(structural.sum()) > MAX_TRACE_PIXELS:
        raise StoryWorldError("NEEDS_STROKE_REVIEW", "structural coherence budget exceeded")
    remaining = set(zip(*np.nonzero(structural), strict=True))
    rgb = np.asarray(image.convert("RGB"))
    kept = np.zeros_like(structural)
    while remaining:
        first = min(remaining)
        remaining.remove(first)
        component = [first]
        queue = deque([first])
        while queue:
            y, x = queue.popleft()
            for dy, dx in ((-1, -1), (-1, 0), (-1, 1), (0, -1),
                           (0, 1), (1, -1), (1, 0), (1, 1)):
                other = (y + dy, x + dx)
                if other in remaining:
                    remaining.remove(other)
                    queue.append(other)
                    component.append(other)
        if len(component) >= 5 or any(rgb[y, x].max() <= 90 for y, x in component):
            for y, x in component:
                kept[y, x] = True
    return kept


def _join_adjacent_paths(
    paths: list[tuple[tuple[int, int], ...]],
) -> list[tuple[tuple[int, int], ...]]:
    """Join only touching endpoints, including tile seams; never bridge empty pixels."""
    pending = {i: p for i, p in enumerate(paths)}
    endpoints: dict[tuple[int, int], set[int]] = {}
    for i, path in pending.items():
        for point in (path[0], path[-1]):
            endpoints.setdefault(point, set()).add(i)
    output = []
    while pending:
        i = min(pending)
        path = pending.pop(i)
        while len(path) < 256:
            x, y = path[-1]
            choices = set()
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    choices.update(endpoints.get((x + dx, y + dy), set()))
            choices = {j for j in choices if j in pending and len(path) + len(pending[j]) <= 256}
            if not choices:
                break
            j = min(choices)
            other = pending.pop(j)
            if max(abs(x - other[0][0]), abs(y - other[0][1])) > 1:
                other = other[::-1]
            path = path + other
        output.append(path)
    return output


def _localized_color_paths(active: np.ndarray, stroke_factory) -> list[ObjectStrokeV2]:
    """Short overlapping source-mask pencil passes, no diagonal interleave gaps."""
    height, width = active.shape
    paths: list[ObjectStrokeV2] = []
    reveal = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(reveal)
    for top in range(0, height, 24):
        columns = list(range(0, width, 32))
        if (top // 24) % 2:
            columns.reverse()
        for left in columns:
            for y in range(top, min(top + 24, height), 3):
                xs = np.flatnonzero(active[y, left:left + 32]) + left
                for run in np.split(xs, np.where(np.diff(xs) > 1)[0] + 1):
                    if not run.size:
                        continue
                    points = ((int(run[0]), y), (int(run[-1]), y))
                    if (y // 3) % 2:
                        points = points[::-1]
                    paths.append(stroke_factory("COLOR", len(paths) + 1, points, 7))
                    if len(paths) > MAX_OBJECT_PATHS:
                        raise StoryWorldError(
                            "NEEDS_STROKE_REVIEW", "localized color path budget exceeded",
                        )
                    draw.line(points, fill=255, width=7)
                    for x, py in points:
                        draw.ellipse((x - 3, py - 3, x + 3, py + 3), fill=255)
    # Mask tips not intersected by sampled rows need explicit source-only dot passes.
    ys, xs = np.nonzero(active & (np.asarray(reveal) == 0))
    if len(xs) > MAX_TRACE_PIXELS:
        raise StoryWorldError("NEEDS_STROKE_REVIEW", "color tip coverage budget exceeded")
    if len(paths) + len(xs) > MAX_OBJECT_PATHS:
        raise StoryWorldError("NEEDS_STROKE_REVIEW", "localized color tip path budget exceeded")
    for y, x in zip(ys, xs, strict=True):
        point = (int(x), int(y))
        paths.append(stroke_factory("COLOR", len(paths) + 1, (point, point), 3))
    if len(paths) > MAX_OBJECT_PATHS:
        raise StoryWorldError("NEEDS_STROKE_REVIEW", "localized color path budget exceeded")
    return paths


def _pencil_color_paths(active: np.ndarray, stroke_factory) -> list[ObjectStrokeV2]:
    """Connect consecutive hatches only via mask-contained short pencil turns."""
    original = _localized_color_paths(active, stroke_factory)
    runs: list[tuple[tuple[int, int], ...]] = []
    current: tuple[tuple[int, int], ...] = ()
    for stroke in original:
        points = stroke.points
        join = False
        if current and len(current) + len(points) <= 256:
            x0, y0 = current[-1]
            x1, y1 = points[0]
            distance = max(abs(x1 - x0), abs(y1 - y0))
            if distance <= 6:
                steps = max(1, distance)
                join = all(active[round(y0 + (y1 - y0) * i / steps),
                                  round(x0 + (x1 - x0) * i / steps)]
                           for i in range(steps + 1))
        if join:
            current += points
        else:
            if current:
                runs.append(current)
            current = points
    if current:
        runs.append(current)
    paths = [stroke_factory("COLOR", i, points, 5) for i, points in enumerate(runs, 1)]
    reveal = Image.new("L", (active.shape[1], active.shape[0]), 0)
    draw = ImageDraw.Draw(reveal)
    for path in paths:
        draw.line(path.points, fill=255, width=5)
        for x, y in (path.points[0], path.points[-1]):
            draw.ellipse((x - 2, y - 2, x + 2, y + 2), fill=255)
    ys, xs = np.nonzero(active & (np.asarray(reveal) == 0))
    if len(xs) > MAX_TRACE_PIXELS or len(paths) + len(xs) > MAX_OBJECT_PATHS:
        raise StoryWorldError("NEEDS_STROKE_REVIEW", "pencil coverage/path budget exceeded")
    for y, x in zip(ys, xs, strict=True):
        p = (int(x), int(y))
        paths.append(stroke_factory("COLOR", len(paths) + 1, (p, p), 3))
    return paths


class LocalObjectAwareStrokeEngine:
    """CPU implementation of ObjectAwareStrokePort for reviewed source cutouts."""

    def __init__(
        self, strategy: Literal["legacy", "refined", "visual", "pencil"] = "refined",
    ) -> None:
        self.strategy = strategy

    def extract_object(
        self, registry: SourceAssetRegistry, object_id: str,
    ) -> SourceObjectStrokesV2:
        return extract_object_strokes(registry, object_id, strategy=self.strategy)


def _paths_legacy(binary: np.ndarray, *, limit: int = 4000) -> list[tuple[tuple[int, int], ...]]:
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


def _paths_refined(binary: np.ndarray, *, limit: int = 4000) -> list[tuple[tuple[int, int], ...]]:
    """Join adjacent source-ink pixels with straight-ahead preference at junctions.

    A pixel belongs to at most one path, avoiding the repeated 8-neighbor edge
    traversal that made the previous graph produce short duplicate fragments.
    """
    ys, xs = np.nonzero(binary)
    remaining = {(int(x), int(y)) for y, x in zip(ys, xs, strict=True)}
    if len(remaining) > limit:
        raise StoryWorldError("NEEDS_STROKE_REVIEW", "too many candidate ink pixels")
    offsets = ((-1, 0), (1, 0), (0, -1), (0, 1),
               (-1, -1), (1, -1), (-1, 1), (1, 1))

    def adjacent(point: tuple[int, int]) -> list[tuple[int, int]]:
        x, y = point
        return sorted((x + dx, y + dy) for dx, dy in offsets
                      if (x + dx, y + dy) in remaining)

    output: list[tuple[tuple[int, int], ...]] = []
    while remaining:
        endpoints = [point for point in sorted(remaining) if len(adjacent(point)) == 1]
        current = endpoints[0] if endpoints else min(remaining)
        path = [current]
        remaining.remove(current)
        while len(path) < 256:
            choices = adjacent(current)
            if not choices:
                break
            if len(path) == 1:
                nxt = choices[0]
            else:
                vx = current[0] - path[-2][0]
                vy = current[1] - path[-2][1]
                nxt = max(choices, key=lambda point: (
                    vx * (point[0] - current[0]) + vy * (point[1] - current[1]),
                    -abs(vx * (point[1] - current[1]) - vy * (point[0] - current[0])),
                    -point[1], -point[0],
                ))
            current = nxt
            path.append(current)
            remaining.remove(current)
        if len(path) >= 2:
            output.append(tuple(path))
    return output


def _natural_color_paths(
    active: np.ndarray, stroke_factory, *, descending: bool,
) -> list[ObjectStrokeV2]:
    """Diagonal, gently bent source-pixel reveals; no generated repaint texture."""
    height, width = active.shape
    paths: list[ObjectStrokeV2] = []
    for index, offset in enumerate(range(-width - 8, height + width + 9, 4)):
        # Different source objects choose opposite slants; original masked RGBA
        # is the only color visible through these brush trajectories.
        start_x = max(0, -offset) if descending else max(0, offset - height + 1)
        stop_x = min(width - 1, height - 1 - offset) if descending else min(width - 1, offset)
        if stop_x < start_x:
            continue
        xs = np.arange(start_x, stop_x + 1)
        ys = xs + offset if descending else offset - xs
        selected = xs[active[ys, xs]]
        for run in np.split(selected, np.where(np.diff(selected) > 1)[0] + 1):
            if not run.size:
                continue
            first, last = int(run[0]), int(run[-1])
            y0, y1 = (first + offset, last + offset) if descending else (
                offset - first, offset - last,
            )
            points = ((first, y0), (last, y1))
            if index % 2:
                points = (points[1], points[0])
            paths.append(stroke_factory("COLOR", len(paths) + 1, points, 11))
            if len(paths) > MAX_OBJECT_PATHS:
                raise StoryWorldError("NEEDS_STROKE_REVIEW", "too many mask-bounded color passes")
    # Spatially interleave passes (middle, left-middle, right-middle, ...)
    # instead of revealing one rigid diagonal front across the whole object.
    ordered: list[ObjectStrokeV2] = []
    intervals = deque([(0, len(paths) - 1)])
    while intervals:
        low, high = intervals.popleft()
        if low > high:
            continue
        middle = (low + high) // 2
        ordered.append(paths[middle])
        intervals.extend(((low, middle - 1), (middle + 1, high)))
    return ordered


def extract_object_strokes(
    registry: SourceAssetRegistry, object_id: str, *,
    strategy: Literal["legacy", "refined", "visual", "pencil"] = "refined",
) -> SourceObjectStrokesV2:
    """Trace mask boundary, local source-color detail and selected brush trajectories.

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
    opened = Image.open(io.BytesIO(body))
    if max(opened.size) > 2048 or opened.width * opened.height > 1920 * 1080:
        raise StoryWorldError("NEEDS_STROKE_REVIEW", "source cutout exceeds bounded canvas budget")
    image = opened.convert("RGBA")
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
    if strategy not in {"legacy", "refined", "visual", "pencil"}:
        raise ValueError("unsupported stroke strategy")
    diagnostics = None
    if strategy == "legacy":
        outline = _paths_legacy(boundary)
        detail = _paths_legacy(details, limit=2000) if details.any() else []
    else:
        structural, texture = _structural_details(image, deep, strength, threshold)
        if strategy in {"visual", "pencil"}:
            coherent = _coherent_details(image, structural)
            texture |= structural & ~coherent
            structural = coherent
        if int(boundary.sum()) <= 4000:
            legacy_outline = _paths_legacy(boundary)
            candidate_outline = _paths_refined(boundary)
            outline = candidate_outline if candidate_outline and (
                len(candidate_outline) <= len(legacy_outline)
            ) else legacy_outline
            missing = boundary.copy()
            for path in outline:
                for x, y in path:
                    missing[y, x] = False
            dots, outline_clusters, outline_maximum = _paths_clustered(missing)
            outline.extend(dots)
        else:
            outline, outline_clusters, outline_maximum = _paths_clustered(boundary)
        detail, detail_clusters, detail_maximum = _paths_clustered(structural)
        if strategy in {"visual", "pencil"}:
            outline = _join_adjacent_paths(outline)
            detail = _join_adjacent_paths(detail)
        diagnostics = StrokeProcessingDiagnosticsV2(
            raw_detail_candidates=int(details.sum()),
            structural_detail_pixels=int(structural.sum()),
            texture_candidates_deferred_to_color=int(texture.sum()), detail_threshold=threshold,
            trace_clusters=outline_clusters + detail_clusters,
            max_cluster_pixels=max(outline_maximum, detail_maximum),
            retained_structural_fraction=1.,
            texture_heuristic=("COHERENT_SOURCE_INK_V2" if strategy in {"visual", "pencil"}
                               else "PERSISTENT_COLOR_EDGE_OR_DARK_INK_V1"),
        )
    if not outline:
        raise StoryWorldError("NEEDS_STROKE_REVIEW", "no continuous object contour")

    def stroke(
        phase: Literal["OUTLINE", "DETAIL", "COLOR"], index: int,
        path: tuple[tuple[int, int], ...], width: int,
    ) -> ObjectStrokeV2:
        colors = [rgba[y, x, :3] for x, y in path if active[y, x]]
        if not colors:
            colors = [rgba[path[0][1], path[0][0], :3]]
        median = np.median(np.asarray(colors), axis=0).astype(int)
        return ObjectStrokeV2(
            stroke_id=f"{phase.lower()}-{index:04}", phase=phase, points=path,
            brush_width=width, color_rgb=(int(median[0]), int(median[1]), int(median[2])),
            pen_up_before=True,
        )

    # Brush trajectories follow actual mask runs, alternating direction. The renderer
    # reveals original RGBA under these tracks; no synthesized fill color is used.
    color_paths: list[ObjectStrokeV2] = []
    # Uniform synthetic/flat regions look worse with diagonal hatching; keep
    # the legacy fill there. Rich source texture receives the new brush path.
    texture_strength = float(rgba[:, :, :3][active].std(axis=0).mean())
    use_legacy_color = strategy == "legacy" or texture_strength <= 45.
    if strategy == "pencil":
        color_paths = _pencil_color_paths(active, stroke)
    elif strategy == "visual":
        color_paths = _localized_color_paths(active, stroke)
    elif use_legacy_color:
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
    else:
        color_paths = _natural_color_paths(
            active, stroke, descending=sum(object_id.encode("utf-8")) % 2 == 0,
        )
    if not color_paths:
        raise StoryWorldError("NEEDS_STROKE_REVIEW", "cannot create source-color brush paths")
    if len(outline) + len(detail) + len(color_paths) > MAX_OBJECT_PATHS:
        raise StoryWorldError("NEEDS_STROKE_REVIEW", "per-object stroke budget exceeded")
    z_index = next(s.z_index for s in world.initial_states if s.object_id == object_id)
    return SourceObjectStrokesV2(
        object_id=object_id, source_image_sha256=spec.source_image_sha256,
        source_asset_ref=spec.asset_ref, source_asset_sha256=spec.asset_sha256,
        source_mask_ref=spec.source_mask_ref, source_mask_sha256=spec.source_mask_sha256,
        width=image.width, height=image.height, z_index=z_index,
        extraction_method=("MASK_BOUNDARY_AND_LOCAL_CONTRAST_V1" if strategy == "legacy"
                           else "MASK_BOUNDARY_AND_PENCIL_TEXTURE_V5" if strategy == "pencil"
                           else "MASK_BOUNDARY_AND_COHERENT_TEXTURE_V4" if strategy == "visual"
                           else "MASK_BOUNDARY_AND_STRUCTURAL_TEXTURE_V3"),
        processing_diagnostics=diagnostics,
        outline_paths=tuple(stroke("OUTLINE", i, p, 2) for i, p in enumerate(outline, 1)),
        detail_paths=tuple(stroke("DETAIL", i, p, 2) for i, p in enumerate(detail, 1)),
        color_paths=tuple(color_paths), covered_source_pixels=int(active.sum()),
    )
