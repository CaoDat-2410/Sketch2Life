"""Offline phase/path diagnostics, not a video renderer or approval authority."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw

from sketch2life.application.services.story_world_errors import StoryWorldError
from sketch2life.contracts.schemas.story_strokes_v2 import ObjectStrokeV2

MAX_PATHS = 4096
MAX_POINTS = 200_000
MAX_PIXELS = 1920 * 1080


@dataclass(frozen=True)
class PacingAssumptions:
    """Reviewable native-pixel assumptions; not measured human drawing speed."""

    fps: int = 24
    ink_pixels_per_second: float = 180.
    color_pixels_per_second: float = 300.
    pen_up_pixels_per_second: float = 600.
    minimum_down_frames: int = 4
    minimum_up_frames: int = 2

    def validate(self) -> None:
        values = (self.ink_pixels_per_second, self.color_pixels_per_second,
                  self.pen_up_pixels_per_second)
        if self.fps < 8 or self.fps > 60 or any(
            not math.isfinite(v) or v <= 0 for v in values
        ) or self.minimum_down_frames < 2 or self.minimum_up_frames < 1:
            raise StoryWorldError("DRAW_TIMING_INFEASIBLE", "invalid pacing assumptions")


def path_length(path: ObjectStrokeV2) -> float:
    return sum(math.dist(a, b) for a, b in zip(path.points, path.points[1:], strict=False))


def path_coverage(size: tuple[int, int], paths: tuple[ObjectStrokeV2, ...]) -> np.ndarray:
    width, height = size
    if width < 1 or height < 1 or width * height > MAX_PIXELS or max(size) > 2048:
        raise StoryWorldError("NEEDS_STROKE_REVIEW", "diagnostic canvas budget exceeded")
    if len(paths) > MAX_PATHS or sum(len(p.points) for p in paths) > MAX_POINTS:
        raise StoryWorldError("NEEDS_STROKE_REVIEW", "diagnostic path/point budget exceeded")
    image = Image.new("L", size, 0)
    draw = ImageDraw.Draw(image)
    for path in paths:
        if any(not 0 <= x < width or not 0 <= y < height for x, y in path.points):
            raise StoryWorldError("NEEDS_STROKE_REVIEW", "path outside native canvas")
        draw.line(path.points, fill=255, width=path.brush_width, joint="curve")
        radius = max(1, path.brush_width // 2)
        for x, y in (path.points[0], path.points[-1]):
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=255)
    return np.asarray(image) > 0


def separate_phase_masks(
    source: Image.Image, groups: dict[str, tuple[ObjectStrokeV2, ...]],
) -> tuple[dict[str, np.ndarray], dict[str, int]]:
    """Conservative neutral dark source-ink heuristic; ambiguous regions need review.

    Colored contours are deferred to COLOR. Never reveal the entire cutout in ink
    phases; never recolor a source pixel. Source RGBA is read-only.
    """
    rgba = np.asarray(source.convert("RGBA"), dtype=np.int16)
    active = rgba[:, :, 3] > 0
    rgb = rgba[:, :, :3]
    ink = active & (rgb.max(axis=2) <= 165) & (rgb.max(axis=2) - rgb.min(axis=2) <= 70)
    coverage = {phase: path_coverage(source.size, groups[phase]) & active
                for phase in ("OUTLINE", "DETAIL", "COLOR")}
    outline = coverage["OUTLINE"] & ink
    detail = coverage["DETAIL"] & ink & ~outline
    color = coverage["COLOR"] & active
    masks = {"OUTLINE": outline, "DETAIL": detail, "COLOR": color}
    counts = {
        "source_pixels": int(active.sum()), "selected_neutral_ink_pixels": int(ink.sum()),
        "ink_not_reached_by_outline_detail": int((ink & ~(outline | detail)).sum()),
        "color_source_pixels_uncovered": int((active & ~color).sum()),
        "outline_boundary_pixels_deferred_to_color": int((coverage["OUTLINE"] & ~ink).sum()),
        "ink_color_overlap_pixels": int(((outline | detail) & color).sum()),
    }
    return masks, counts


def timed_pen_paths(
    paths: tuple[ObjectStrokeV2, ...], pacing: PacingAssumptions,
    *, previous_endpoint: tuple[int, int] | None = None,
) -> tuple[list[dict], dict[str, float]]:
    """Measure native paths; explicitly represent pen-up travel and pen-down time."""
    pacing.validate()
    if len(paths) > MAX_PATHS or sum(len(p.points) for p in paths) > MAX_POINTS:
        raise StoryWorldError("NEEDS_STROKE_REVIEW", "timing path/point budget exceeded")
    cursor = down_total = up_total = travel = up_travel = 0.
    rows = []
    prior = previous_endpoint
    for path in paths:
        length = path_length(path)
        distance = math.dist(prior, path.points[0]) if prior is not None else 0.
        up = max(pacing.minimum_up_frames / pacing.fps,
                 distance / pacing.pen_up_pixels_per_second) if prior is not None else 0.
        speed = pacing.color_pixels_per_second if path.phase == "COLOR" else (
            pacing.ink_pixels_per_second
        )
        down = max(pacing.minimum_down_frames / pacing.fps, length / speed)
        rows.append({"stroke_id": path.stroke_id, "phase": path.phase,
                     "pen_up_from": list(prior) if prior is not None else None,
                     "pen_up_to": list(path.points[0]), "pen_up_start": cursor,
                     "pen_down_start": cursor + up, "pen_down_end": cursor + up + down,
                     "pen_up_seconds": up, "pen_down_seconds": down,
                     "down_length_pixels": length, "up_length_pixels": distance})
        cursor += up + down
        down_total += down
        up_total += up
        travel += length
        up_travel += distance
        prior = path.points[-1]
    return rows, {"estimated_seconds": cursor, "pen_down_seconds": down_total,
                  "pen_up_seconds": up_total, "down_travel_pixels": travel,
                  "up_travel_pixels": up_travel}
