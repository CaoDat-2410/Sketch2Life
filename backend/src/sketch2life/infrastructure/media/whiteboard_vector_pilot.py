"""Opt-in authored-path whiteboard pilot; not a raster-to-vector converter.

The scene JSON contains reviewed object paths and colors.  This renderer makes
their ordering and drawing motion inspectable before any L4/TTS integration.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from sketch2life.infrastructure.media.whiteboard_mvp_renderer import (
    WhiteboardMvpRenderResult,
    WhiteboardMvpRenderSpec,
)


def _color(value: Any) -> tuple[int, int, int]:
    if not isinstance(value, str) or len(value) != 7 or not value.startswith("#"):
        raise ValueError("vector color must be #rrggbb")
    try:
        return tuple(bytes.fromhex(value[1:]))  # type: ignore[return-value]
    except ValueError as error:
        raise ValueError("vector color must be #rrggbb") from error


def _point(value: Any, width: int, height: int) -> tuple[float, float]:
    if (
        not isinstance(value, list)
        or len(value) != 2
        or any(isinstance(n, bool) or not isinstance(n, (int, float)) for n in value)
    ):
        raise ValueError("vector point must be [x, y]")
    x, y = float(value[0]), float(value[1])
    if not (math.isfinite(x) and math.isfinite(y) and -20 <= x <= width + 20
            and -20 <= y <= height + 20):
        raise ValueError("vector point outside scene bounds")
    return x, y


def validate_vector_scene(scene: Any) -> dict[str, Any]:
    """Validate the small reviewed path-pack contract before encoding."""

    if not isinstance(scene, dict) or scene.get("version") != 1:
        raise ValueError("vector scene version must be 1")
    width, height = scene.get("width"), scene.get("height")
    if (isinstance(width, bool) or isinstance(height, bool)
            or not isinstance(width, int) or not isinstance(height, int)
            or not 128 <= width <= 1920 or not 128 <= height <= 1080):
        raise ValueError("invalid vector scene dimensions")
    objects = scene.get("objects")
    if not isinstance(objects, list) or not 1 <= len(objects) <= 32:
        raise ValueError("vector scene needs 1-32 objects")
    ids: set[str] = set()
    for obj in objects:
        if not isinstance(obj, dict) or not isinstance(obj.get("id"), str):
            raise ValueError("invalid vector object")
        if not obj["id"] or obj["id"] in ids:
            raise ValueError("vector object ids must be unique")
        ids.add(obj["id"])
        start, end = obj.get("start"), obj.get("end")
        if (not isinstance(start, (int, float)) or isinstance(start, bool)
                or not isinstance(end, (int, float)) or isinstance(end, bool)
                or not 0 <= start < end <= 1):
            raise ValueError("vector object window must be within 0..1")
        strokes = obj.get("strokes")
        if not isinstance(strokes, list) or not 1 <= len(strokes) <= 128:
            raise ValueError("vector object needs 1-128 strokes")
        for stroke in strokes:
            if not isinstance(stroke, dict):
                raise ValueError("invalid vector stroke")
            points = stroke.get("points")
            if not isinstance(points, list) or not 2 <= len(points) <= 512:
                raise ValueError("vector stroke needs 2-512 points")
            for point in points:
                _point(point, width, height)
            pen_width = stroke.get("width", 2.0)
            if (isinstance(pen_width, bool) or not isinstance(pen_width, (int, float))
                    or not math.isfinite(pen_width) or not 0.5 <= pen_width <= 12):
                raise ValueError("invalid vector stroke width")
            _color(stroke.get("color", "#25272b"))
        fills = obj.get("fills", [])
        if not isinstance(fills, list) or len(fills) > 64:
            raise ValueError("invalid vector fills")
        for fill in fills:
            if not isinstance(fill, dict) or not isinstance(fill.get("polygon"), list):
                raise ValueError("invalid vector fill")
            if not 3 <= len(fill["polygon"]) <= 512:
                raise ValueError("vector fill needs 3-512 points")
            for point in fill["polygon"]:
                _point(point, width, height)
            _color(fill.get("color"))
    return scene


def _partial_path(points: list[tuple[float, float]], fraction: float) -> list[tuple[float, float]]:
    if fraction <= 0:
        return []
    lengths = [math.dist(a, b) for a, b in zip(points, points[1:], strict=False)]
    remaining = sum(lengths) * min(1.0, fraction)
    out = [points[0]]
    for index, length in enumerate(lengths):
        if remaining >= length:
            out.append(points[index + 1])
            remaining -= length
        elif length > 0:
            ratio = remaining / length
            a, b = points[index], points[index + 1]
            out.append((a[0] + (b[0] - a[0]) * ratio,
                        a[1] + (b[1] - a[1]) * ratio))
            break
    return out


def _paint_frame(scene: dict[str, Any], progress: float, size: tuple[int, int]):
    from PIL import Image, ImageChops, ImageDraw

    width, height = size
    sx, sy = width / scene["width"], height / scene["height"]
    scale = (sx + sy) / 2
    canvas = Image.new("RGB", size, (252, 250, 246))
    draw = ImageDraw.Draw(canvas)
    for obj in scene["objects"]:
        local = max(0.0, min(1.0, (progress - obj["start"]) / (obj["end"] - obj["start"])))
        if local <= 0:
            continue
        # Color follows the contours; never flashes in before the object starts.
        color_progress = max(0.0, min(1.0, (local - 0.78) / 0.22))
        if color_progress:
            for fill in obj.get("fills", []):
                polygon = [(round(x * sx), round(y * sy)) for x, y in fill["polygon"]]
                left = min(x for x, _ in polygon)
                right = max(x for x, _ in polygon)
                top = min(y for _, y in polygon)
                bottom = max(y for _, y in polygon)
                clip = Image.new("L", size)
                ImageDraw.Draw(clip).polygon(polygon, fill=255)
                brush = Image.new("L", size)
                brush_draw = ImageDraw.Draw(brush)
                spacing = max(3, round(4.5 * scale))
                brush_width = max(2, round(3.8 * scale))
                sweep = max(0, bottom - top) * 0.22
                positions = range(left - round(sweep) - spacing, right + spacing, spacing)
                count = math.ceil(len(positions) * color_progress)
                for position in list(positions)[:count]:
                    brush_draw.line(
                        (position, top, position + sweep, bottom),
                        fill=245, width=brush_width,
                    )
                mask = ImageChops.multiply(clip, brush)
                canvas.paste(_color(fill["color"]), (0, 0, width, height), mask)
            draw = ImageDraw.Draw(canvas)
        strokes = obj["strokes"]
        lengths = [sum(math.dist(a, b) for a, b in zip(
            stroke["points"], stroke["points"][1:], strict=False))
            for stroke in strokes]
        remaining = sum(lengths) * local
        for stroke_index, (stroke, length) in enumerate(zip(strokes, lengths, strict=True)):
            fraction = min(1.0, remaining / length) if length else 1.0
            remaining = max(0.0, remaining - length)
            path = _partial_path(stroke["points"], fraction)
            if len(path) < 2:
                continue
            points = [(round(x * sx), round(y * sy)) for x, y in path]
            ink = _color(stroke.get("color", "#25272b"))
            pen_width = max(1, round(stroke.get("width", 2.0) * scale))
            # Small deterministic pressure variation, never frame-random jitter.
            pressure = 1 + 0.08 * math.sin(stroke_index * 1.7)
            pen_width = max(1, round(pen_width * pressure))
            draw.line(points, fill=ink, width=pen_width, joint="curve")
            radius = pen_width / 2
            for x, y in (points[0], points[-1]):
                draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=ink)
    return canvas


def render_vector_scene(
    scene_path: str | Path,
    output_path: str | Path,
    *,
    spec: WhiteboardMvpRenderSpec | None = None,
    still_directory: str | Path | None = None,
) -> WhiteboardMvpRenderResult:
    """Encode an authored, object-paced path pack as a silent H.264 pilot."""

    import imageio.v2 as imageio
    import numpy as np

    render_spec = spec or WhiteboardMvpRenderSpec(duration_seconds=8)
    render_spec.validate()
    scene = validate_vector_scene(json.loads(Path(scene_path).read_text(encoding="utf-8")))
    target = Path(output_path)
    if target.exists():
        raise FileExistsError("vector pilot output already exists")
    target.parent.mkdir(parents=True, exist_ok=True)
    stills = Path(still_directory) if still_directory is not None else None
    if stills is not None:
        if stills.exists():
            raise FileExistsError("vector pilot still directory already exists")
        stills.mkdir(parents=True)
    frame_count = round(render_spec.fps * render_spec.duration_seconds)
    writer = imageio.get_writer(
        target, fps=render_spec.fps, codec="libx264", pixelformat="yuv420p", quality=8
    )
    try:
        for frame_index in range(frame_count):
            progress = frame_index / max(1, frame_count - 1)
            frame = _paint_frame(scene, progress, (render_spec.width, render_spec.height))
            writer.append_data(np.asarray(frame))
            if stills is not None and frame_index in {
                round((frame_count - 1) * share) for share in (0.25, 0.55, 1.0)
            }:
                frame.save(stills / f"frame-{frame_index:03d}.png")
    finally:
        writer.close()
    size_bytes = target.stat().st_size
    if size_bytes > render_spec.max_size_bytes:
        raise ValueError("vector pilot exceeds encoded size limit")
    return WhiteboardMvpRenderResult(
        output_path=str(target), width=render_spec.width, height=render_spec.height,
        fps=render_spec.fps, duration_seconds=render_spec.duration_seconds,
        codec="h264", size_bytes=size_bytes,
    )


__all__ = ["render_vector_scene", "validate_vector_scene"]
