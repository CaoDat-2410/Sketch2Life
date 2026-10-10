"""Versioned semantic strategy adapter for offline V2; source pixels remain immutable.

Region inference is not semantic recognition or reconstruction of JPEG pen history.
Authored overrides and uncertain new source packs require review, never server approval.
"""

from __future__ import annotations

import hashlib
import math
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Literal

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from sketch2life.contracts.schemas.semantic_drawing_v2 import (
    DrawingBudget,
    SemanticStroke,
    TextStoryBeat,
)
from sketch2life.contracts.schemas.story_strokes_v2 import ObjectStrokeV2
from sketch2life.infrastructure.media.whiteboard_renderer_v2 import _partial_points
from sketch2life.infrastructure.media.whiteboard_slice_feasibility import (
    PacingAssumptions,
    path_length,
    timed_pen_paths,
)


@dataclass
class SemanticAsset:
    object_id: str
    source: Image.Image
    provenance: str
    source_hash: str
    regions: dict[str, np.ndarray]
    strokes: tuple[SemanticStroke, ...]
    ink: Image.Image
    review_status: str
    style_profile: dict


def footprint(size: tuple[int, int], path: ObjectStrokeV2, fraction: float) -> np.ndarray:
    image = Image.new("L", size, 0)
    if fraction <= 0:
        return np.asarray(image) > 0
    points = _partial_points(path, min(1.0, fraction))
    draw = ImageDraw.Draw(image)
    draw.line(points, fill=255, width=path.brush_width, joint="curve")
    r = max(0.5, path.brush_width / 2)
    for x, y in (points[0], points[-1]):
        draw.ellipse((x - r, y - r, x + r, y + r), fill=255)
    return np.asarray(image) > 0


def contours(mask: np.ndarray) -> list[tuple]:
    """Trace actual pixel-cell boundary edges globally, not tiles or generic geometry."""
    edges: dict[tuple, list] = defaultdict(list)
    h, w = mask.shape
    for y, x in zip(*np.nonzero(mask), strict=True):
        for a, b, outside in (
            ((x, y), (x + 1, y), y == 0 or not mask[y - 1, x]),
            ((x + 1, y), (x + 1, y + 1), x == w - 1 or not mask[y, x + 1]),
            ((x + 1, y + 1), (x, y + 1), y == h - 1 or not mask[y + 1, x]),
            ((x, y + 1), (x, y), x == 0 or not mask[y, x - 1]),
        ):
            if outside:
                edges[a].append(b)
    result = []
    while edges:
        start = min(edges)
        current, points = start, [start]
        while current in edges:
            nxt = edges[current].pop()
            if not edges[current]:
                del edges[current]
            points.append(nxt)
            current = nxt
            if current == start:
                break
        points = [(int(min(w - 1, x)), int(min(h - 1, y))) for x, y in points]
        # Only discard redundant collinear samples, never replace contour with a polygon box.
        reduced = [points[0]]
        for i in range(1, len(points) - 1):
            a, b, c = points[i - 1 : i + 2]
            if (b[0] - a[0], b[1] - a[1]) != (c[0] - b[0], c[1] - b[1]):
                reduced.append(b)
        reduced.append(points[-1])
        if len(set(reduced)) >= 3:
            result.append(tuple(reduced))
    return sorted(result, key=len, reverse=True)


def components(mask: np.ndarray, minimum: int = 32) -> list[np.ndarray]:
    pool = {(int(x), int(y)) for y, x in zip(*np.nonzero(mask), strict=True)}
    output = []
    while pool:
        seed = min(pool)
        pool.remove(seed)
        queue, points = deque([seed]), [seed]
        while queue:
            x, y = queue.popleft()
            for p in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if p in pool:
                    pool.remove(p)
                    queue.append(p)
                    points.append(p)
        if len(points) >= minimum:
            region = np.zeros(mask.shape, dtype=bool)
            for x, y in points:
                region[y, x] = True
            output.append(region)
    return output


def region_brush(mask: np.ndarray, size: tuple[int, int], name: str) -> list[ObjectStrokeV2]:
    """PCA-directed alternating curved hatching, clipped to one region, no tile scan.

    Connections are accepted only with evidence inside the actual mask.
    Residual pigment is brushed explicitly, never snapped into final frame.
    """
    ys, xs = np.nonzero(mask)
    if not len(xs):
        return []
    coords = np.column_stack((xs, ys)).astype(float)
    center = coords.mean(axis=0)
    covariance = np.cov(coords.T) if len(coords) > 2 else np.eye(2)
    _, vectors = np.linalg.eigh(covariance)
    u = vectors[:, -1]
    v = np.array([-u[1], u[0]])
    projected = (coords - center) @ np.column_stack((u, v))
    width = max(3, min(16, round(math.sqrt(len(xs)) / 10)))
    paths: list[ObjectStrokeV2] = []
    current: list[tuple[int, int]] = []

    def inside(p: tuple[int, int]) -> bool:
        return 0 <= p[0] < size[0] and 0 <= p[1] < size[1] and bool(mask[p[1], p[0]])

    def emit() -> None:
        nonlocal current
        if current:
            if len(current) == 1:
                current *= 2
            paths.append(
                ObjectStrokeV2(
                    stroke_id=f"color-{name}-{len(paths)}",
                    phase="COLOR",
                    points=tuple(current),
                    brush_width=width,
                    color_rgb=(0, 0, 0),
                )
            )
        current = []

    for row, offset in enumerate(
        np.arange(projected[:, 1].min(), projected[:, 1].max() + 1, max(2, width * 0.7))
    ):
        positions = np.arange(projected[:, 0].min(), projected[:, 0].max() + 1, 1.0)
        if row % 2:
            positions = positions[::-1]
        for value in positions:
            p = center + value * u + (offset + 0.8 * math.sin(value / 13 + row * 0.7)) * v
            xy = (round(p[0]), round(p[1]))
            if not inside(xy):
                if current:
                    emit()
                continue
            if current and math.dist(current[-1], xy) > 2:
                a = current[-1]
                n = max(1, math.ceil(math.dist(a, xy)))
                if not all(
                    inside(
                        (round(a[0] + (xy[0] - a[0]) * t / n), round(a[1] + (xy[1] - a[1]) * t / n))
                    )
                    for t in range(n + 1)
                ):
                    emit()
            if not current or current[-1] != xy:
                current.append(xy)
    emit()
    covered = np.zeros(mask.shape, dtype=bool)
    for path in paths:
        covered |= footprint(size, path, 1.0) & mask
    # Finite sparse cleanup: still literal brush trajectories with pen-up, not an opacity patch.
    for y, x in zip(*np.nonzero(mask & ~covered), strict=True):
        if covered[y, x]:
            continue
        p = (int(x), int(y))
        path = ObjectStrokeV2(
            stroke_id=f"color-{name}-{len(paths)}",
            phase="COLOR",
            points=(p, p),
            brush_width=width,
            color_rgb=(0, 0, 0),
        )
        paths.append(path)
        covered |= footprint(size, path, 1.0) & mask
    return paths


class SemanticStrokeStrategyV1:
    """Explicit versioned adapter; legacy extract_object_strokes contracts stay intact."""

    def prepare(
        self,
        image: Image.Image,
        object_id: str,
        provenance: str,
        source_hash: str,
        *,
        authored: tuple[ObjectStrokeV2, ...] | None = None,
        region_overrides: dict[str, np.ndarray] | None = None,
        protected_identity: bool = False,
    ) -> SemanticAsset:
        source = image.convert("RGBA")
        active = np.asarray(source)[:, :, 3] > 0
        if source.width * source.height > 512 * 512 or not active.any():
            raise ValueError("NEEDS_STROKE_REVIEW: canvas/empty asset")
        regions = region_overrides
        if regions is None:
            # Softened color clustering is region evidence, not recognition of roof/face/etc.
            labels = np.asarray(
                source.convert("RGB").filter(ImageFilter.MedianFilter(5)).quantize(colors=6)
            )
            regions = {f"palette-{i}": active & (labels == i) for i in np.unique(labels[active])}
        if any(mask.shape != active.shape or np.any(mask & ~active) for mask in regions.values()):
            raise ValueError("NEEDS_MASK_REVIEW: region coordinates or source leakage")
        union = np.zeros(active.shape, dtype=bool)
        for mask in regions.values():
            union |= mask
        if not np.array_equal(union, active):
            raise ValueError("NEEDS_MASK_REVIEW: regions do not cover source alpha")
        strokes = []
        if authored:
            for p in authored:
                if p.phase != "COLOR":
                    strokes.append(
                        SemanticStroke(
                            p,
                            "PRIMARY_CONTOUR" if p.phase == "OUTLINE" else "DISTINCTIVE_DETAIL",
                            "ink",
                            True,
                        )
                    )
        else:
            # Preserve source contours globally; no fixed shape template or tile split.
            candidates: list[
                tuple[str, tuple, Literal["PRIMARY_CONTOUR", "DISTINCTIVE_DETAIL"]]
            ] = [("whole", contour, "PRIMARY_CONTOUR") for contour in contours(active)]
            for region_id, mask in regions.items():
                for component in components(mask, 64):
                    candidates.extend(
                        (region_id, p, "DISTINCTIVE_DETAIL") for p in contours(component)
                    )
            for _name, points, role in candidates:
                if len(points) < 4:
                    continue
                p = ObjectStrokeV2(
                    stroke_id=f"ink-{len(strokes)}",
                    phase="OUTLINE" if role == "PRIMARY_CONTOUR" else "DETAIL",
                    points=points,
                    brush_width=2,
                    color_rgb=(55, 55, 55),
                )
                length = path_length(p)
                if length < 12:
                    continue
                optional = length < 24 and not protected_identity
                strokes.append(
                    SemanticStroke(p, "OPTIONAL_TEXTURE" if optional else role, "ink", not optional)
                )
        for region_id, mask in regions.items():
            for path in region_brush(mask, source.size, region_id):
                strokes.append(SemanticStroke(path, "COLOR_REGION", region_id, True))
        if len(strokes) > 4096 or sum(len(s.path.points) for s in strokes) > 200_000:
            raise ValueError("NEEDS_STROKE_REVIEW: bounded paths/points exceeded")
        # Temporary source-derived neutral ink layer, never mutate source pixels.
        gray = np.asarray(source.convert("L")).copy()
        ink = np.asarray(source).copy()
        ink[:, :, :3] = np.minimum(gray, 90)[:, :, None]
        ink[:, :, 3] = 0
        evidence = np.zeros(active.shape, dtype=bool)
        for s in strokes:
            if s.path.phase != "COLOR":
                evidence |= footprint(source.size, s.path, 1.0) & active
        ink[:, :, 3] = np.where(evidence, np.asarray(source)[:, :, 3], 0)
        status = "AUTHORED_TECHNICAL_PROOF_ONLY" if authored else "NEEDS_SEMANTIC_PATH_REVIEW"
        if protected_identity and not authored:
            status = "NEEDS_IDENTITY_DETAIL_REVIEW"
        style = {
            "source_sha256": source_hash,
            "pixel_hash": hashlib.sha256(source.tobytes()).hexdigest(),
            "ink_provenance": "TEMPORARY_SOURCE_GRAYSCALE_CLAMP_NOT_ORIGINAL_INK",
            "region_method": "OVERRIDE" if region_overrides else "MEDIAN_PALETTE_CANDIDATE",
            "original_stroke_history_recovered": False,
        }
        return SemanticAsset(
            object_id,
            source,
            provenance,
            source_hash,
            regions,
            tuple(strokes),
            Image.fromarray(ink),
            status,
            style,
        )


def optimize(asset: SemanticAsset, budget: DrawingBudget) -> dict:
    if not all(math.isfinite(v) and v > 0 for v in (budget.target_seconds, budget.beat_seconds)):
        raise ValueError("TIMING_INFEASIBLE: invalid budget")
    scale = float(asset.style_profile.get("presentation_scale", 1.0))
    if not 0.05 <= scale <= 1.0:
        raise ValueError("INVALID_PRESENTATION_SCALE")
    profile = PacingAssumptions(
        fps=budget.fps,
        ink_pixels_per_second=budget.ink_speed / scale,
        color_pixels_per_second=budget.brush_speed / scale,
        pen_up_pixels_per_second=budget.travel_speed / scale,
    )
    choices: list[dict] = []
    for lod in ("HIGH_DETAIL", "BALANCED", "FAST_STORY"):
        selected = [s for s in asset.strokes if lod == "HIGH_DETAIL" or s.essential]
        # FAST_STORY preserves all primary/distinctive features and regions, not eyes/hair deletion.
        ordered = []
        prior = None
        for phase in ("OUTLINE", "DETAIL", "COLOR"):
            remaining = [s for s in selected if s.path.phase == phase]
            while remaining:
                chosen = min(
                    remaining, key=lambda s: math.dist(prior, s.path.points[0]) if prior else 0
                )
                ordered.append(chosen)
                prior = chosen.path.points[-1]
                remaining.remove(chosen)
        rows, stats = timed_pen_paths(tuple(s.path for s in ordered), profile)
        # Smoothstep peak speed is1.5x average: lengthen down time, never exceed given speed cap.
        cursor = 0.0
        for row in rows:
            row["pen_up_start"] = cursor
            cursor += row["pen_up_seconds"] * 1.5
            row["pen_up_seconds"] *= 1.5
            row["pen_down_start"] = cursor
            row["pen_down_seconds"] *= 1.5
            cursor += row["pen_down_seconds"]
            row["pen_down_end"] = cursor
        choices.append(
            {
                "lod": lod,
                "seconds": cursor,
                "rows": rows,
                "strokes": ordered,
                "raw_pacing_seconds": stats["estimated_seconds"],
            }
        )
        if cursor <= min(budget.target_seconds, budget.beat_seconds):
            break
    result = choices[-1]
    result.update(
        status="FEASIBLE"
        if result["seconds"] <= min(budget.target_seconds, budget.beat_seconds)
        else "TIMING_INFEASIBLE",
        target_seconds=budget.target_seconds,
        beat_seconds=budget.beat_seconds,
        alternatives=[{"lod": c["lod"], "seconds": c["seconds"]} for c in choices],
    )
    return result


def eased(fraction: float) -> float:
    x = max(0.0, min(1.0, fraction))
    return x * x * (3 - 2 * x)


class SemanticProgress:
    def __init__(self, asset: SemanticAsset, schedule: dict):
        self.asset, self.schedule = asset, schedule
        self.ink = np.zeros((asset.source.height, asset.source.width), dtype=bool)
        self.color = self.ink.copy()
        self.index, self.last_time = 0, -1.0

    def admit(self, stroke: SemanticStroke, fraction: float) -> np.ndarray:
        mask = footprint(self.asset.source.size, stroke.path, fraction)
        active = np.asarray(self.asset.source)[:, :, 3] > 0
        return mask & (
            self.asset.regions[stroke.region_id] if stroke.path.phase == "COLOR" else active
        )

    def at(self, seconds: float) -> tuple[Image.Image, dict, dict]:
        if seconds < self.last_time:
            raise ValueError("MONOTONIC_TIMELINE_REQUIRED")
        self.last_time = seconds
        rows, strokes = self.schedule["rows"], self.schedule["strokes"]
        while self.index < len(rows) and seconds >= rows[self.index]["pen_down_end"]:
            s = strokes[self.index]
            destination = self.color if s.path.phase == "COLOR" else self.ink
            destination |= self.admit(s, 1.0)
            self.index += 1
        ink, color = self.ink.copy(), self.color.copy()
        trace: dict = {"state": "REST", "tip": None, "phase": None, "stroke_id": None}
        if self.index < len(rows):
            r, s = rows[self.index], strokes[self.index]
            trace.update(phase=s.path.phase, stroke_id=s.path.stroke_id)
            if seconds <= r["pen_up_start"]:
                trace["state"] = "IDLE"
            elif seconds < r["pen_down_start"]:
                t = eased((seconds - r["pen_up_start"]) / r["pen_up_seconds"])
                trace.update(
                    state="UP",
                    tip=[
                        a + (b - a) * t
                        for a, b in zip(r["pen_up_from"], r["pen_up_to"], strict=True)
                    ],
                )
            else:
                t = eased((seconds - r["pen_down_start"]) / r["pen_down_seconds"])
                mask = self.admit(s, t)
                if s.path.phase == "COLOR":
                    color |= mask
                else:
                    ink |= mask
                trace.update(state="DOWN", tip=list(_partial_points(s.path, t)[-1]), fraction=t)
        original = np.asarray(self.asset.source).copy()
        temp = np.asarray(self.asset.ink).copy()
        visible = original.copy()
        visible[ink & ~color] = temp[ink & ~color]
        visible[:, :, 3] = np.where(color | ink, original[:, :, 3], 0)
        return Image.fromarray(visible), trace, {"ink": ink, "color": color}


def integrate_beats(beats: list[TextStoryBeat], assets: dict[str, SemanticAsset]) -> list[dict]:
    timeline = []
    cursor = 0.0
    drawn = set()
    for beat in beats:
        if not beat.local_demo_approved:
            raise ValueError("NEEDS_APPROVAL")
        if beat.transition != "DRAW_MORE":
            raise ValueError("UNSUPPORTED_ACTION: partial erase/page transitions not implemented")
        if beat.object_id not in assets:
            raise ValueError("SOURCE_ASSET_MISMATCH")
        if beat.object_id in drawn:
            raise ValueError("UNSUPPORTED_ACTION: repeated draw needs explicit emphasis action")
        schedule = optimize(
            assets[beat.object_id], DrawingBudget(beat.budget_seconds, beat.budget_seconds)
        )
        timeline.append(
            {
                "beat": beat,
                "start": cursor,
                "end": cursor + schedule["seconds"],
                "schedule": schedule,
                "cue_kind": "SIMULATED_TEXT_NOT_AUDIO",
                "scene_state": "PERSIST_PREVIOUS_OBJECTS",
                "production_gate": "NOT_VERIFIED",
            }
        )
        cursor += schedule["seconds"]
        drawn.add(beat.object_id)
    return timeline
