"""Dependency-backed renderer for source-preserving whiteboard videos."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

WhiteboardMotion = Literal["INTRO", "FOCUS", "DEMONSTRATE", "RECAP"]


@dataclass(frozen=True)
class WhiteboardMvpRenderSpec:
    """Output constraints validated by the FEAT-018 MVP evidence."""

    width: int = 1280
    height: int = 720
    fps: int = 30
    duration_seconds: float = 8.0
    max_size_bytes: int = 12 * 1024 * 1024

    def validate(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("render dimensions must be positive")
        if self.width % 16 or self.height % 16:
            raise ValueError("render dimensions must be divisible by 16")
        if self.fps <= 0:
            raise ValueError("render fps must be positive")
        if not 5.0 <= self.duration_seconds <= 45.0:
            raise ValueError("render duration must be between 5 and 45 seconds")


@dataclass(frozen=True)
class WhiteboardMvpRenderResult:
    output_path: str
    width: int
    height: int
    fps: int
    duration_seconds: float
    codec: str
    size_bytes: int


def render_progressive_reveal(
    cutout_path: str | Path,
    output_path: str | Path,
    *,
    spec: WhiteboardMvpRenderSpec | None = None,
    motion_schedule: tuple[WhiteboardMotion, ...] = (),
    motion_durations_seconds: tuple[float, ...] = (),
) -> WhiteboardMvpRenderResult:
    """Render an RGBA cutout to the contract-compatible MVP MP4."""

    try:
        import imageio.v2 as imageio
        import numpy as np
        from PIL import Image
    except ImportError as error:  # pragma: no cover - environment-dependent
        raise RuntimeError(
            "whiteboard renderer requires the whiteboard-renderer dependencies"
        ) from error

    render_spec = spec or WhiteboardMvpRenderSpec()
    render_spec.validate()
    if len(motion_schedule) > 5:
        raise ValueError("whiteboard motion schedule is too long")
    _validate_motion_durations(motion_schedule, motion_durations_seconds)

    source = Image.open(cutout_path).convert("RGBA")
    source.thumbnail((560, 560), Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", (render_spec.width, render_spec.height))
    x = (render_spec.width - source.width) // 2
    y = (render_spec.height - source.height) // 2
    canvas.alpha_composite(source, (x, y))

    rgba = np.asarray(canvas)
    rgb = rgba[:, :, :3].astype(np.float32)
    alpha = rgba[:, :, 3].astype(np.float32) / 255.0
    stroke_points = _ordered_boundary_points(alpha > 0.05)
    y_ratio = np.arange(render_spec.height, dtype=np.float32)[:, None]
    y_ratio /= render_spec.height
    frame_count = round(render_spec.fps * render_spec.duration_seconds)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    writer = imageio.get_writer(
        output,
        fps=render_spec.fps,
        codec="libx264",
        pixelformat="yuv420p",
        quality=8,
    )
    try:
        for frame_index in range(frame_count):
            progress = frame_index / max(1, frame_count - 1)
            reveal_position = progress * 1.2 - 0.1
            reveal_alpha = np.clip(
                (reveal_position - y_ratio) / 0.08,
                0.0,
                1.0,
            )
            frame_alpha = alpha * reveal_alpha
            white = np.ones_like(rgb) * 255
            frame = (
                rgb * frame_alpha[:, :, None]
                + white * (1.0 - frame_alpha[:, :, None])
            ).astype(np.uint8)
            frame = _draw_progressive_strokes(frame, stroke_points, progress)
            if motion_schedule:
                motion_index, motion_progress = _motion_position(
                    progress, motion_schedule, motion_durations_seconds
                )
                frame = _apply_motion(
                    frame,
                    motion_schedule[motion_index],
                    motion_progress,
                )
            writer.append_data(frame)
    finally:
        writer.close()

    size_bytes = output.stat().st_size
    if size_bytes > render_spec.max_size_bytes:
        raise ValueError("encoded whiteboard MP4 exceeds the size limit")

    return WhiteboardMvpRenderResult(
        output_path=str(output),
        width=render_spec.width,
        height=render_spec.height,
        fps=render_spec.fps,
        duration_seconds=render_spec.duration_seconds,
        codec="H264_AVC_HIGH_L4_1",
        size_bytes=size_bytes,
    )


def render_stroke_animation(
    stroke_path: str | Path,
    output_path: str | Path,
    *,
    spec: WhiteboardMvpRenderSpec | None = None,
    motion_schedule: tuple[WhiteboardMotion, ...] = (),
    motion_durations_seconds: tuple[float, ...] = (),
) -> WhiteboardMvpRenderResult:
    """Render a stroke artifact as a line-by-line whiteboard animation.

    The renderer intentionally draws only the recovered strokes on a white
    canvas. This makes the drawing process the primary motion; camera emphasis
    is applied only after the current stroke frame has been composed.
    """

    try:
        import imageio.v2 as imageio
        import numpy as np
        from PIL import Image, ImageDraw
    except ImportError as error:  # pragma: no cover - environment-dependent
        raise RuntimeError(
            "whiteboard renderer requires the whiteboard-renderer dependencies"
        ) from error

    render_spec = spec or WhiteboardMvpRenderSpec()
    render_spec.validate()
    if len(motion_schedule) > 5:
        raise ValueError("whiteboard motion schedule is too long")
    _validate_motion_durations(motion_schedule, motion_durations_seconds)

    payload = json.loads(Path(stroke_path).read_text(encoding="utf-8"))
    if payload.get("artifact_type") != "whiteboard_strokes_v1":
        raise ValueError("invalid whiteboard stroke artifact type")
    source_width = int(payload.get("width", 0))
    source_height = int(payload.get("height", 0))
    if source_width <= 0 or source_height <= 0:
        raise ValueError("stroke artifact dimensions must be positive")

    raw_strokes = payload.get("strokes")
    if not isinstance(raw_strokes, list) or not raw_strokes:
        raise ValueError("stroke artifact has no strokes")

    scale = min(
        render_spec.width * 0.78 / source_width,
        render_spec.height * 0.82 / source_height,
    )
    offset_x = (render_spec.width - source_width * scale) / 2
    offset_y = (render_spec.height - source_height * scale) / 2
    strokes: list[list[tuple[int, int]]] = []
    stroke_colors: list[tuple[int, int, int]] = []
    source_strokes: list[dict] = []
    for raw_stroke in raw_strokes:
        raw_points = raw_stroke.get("points") if isinstance(raw_stroke, dict) else None
        if not isinstance(raw_points, list):
            continue
        points = [
            (
                round(offset_x + float(point[0]) * scale),
                round(offset_y + float(point[1]) * scale),
            )
            for point in raw_points
            if isinstance(point, list) and len(point) >= 2
        ]
        if len(points) >= 2:
            strokes.append(points)
            source_strokes.append(raw_stroke)
            raw_color = raw_stroke.get("color", [35, 35, 35])
            if (
                not isinstance(raw_color, list)
                or len(raw_color) != 3
                or any(
                    not isinstance(channel, int) or not 0 <= channel <= 255
                    for channel in raw_color
                )
            ):
                raise ValueError("stroke color must be an RGB triplet")
            stroke_colors.append(tuple(raw_color))
    if not strokes:
        raise ValueError("stroke artifact has no drawable points")

    color_regions = []
    color_layer_sha256 = payload.get("color_layer_sha256")
    if color_layer_sha256 is not None:
        if not isinstance(color_layer_sha256, str) or len(color_layer_sha256) != 64:
            raise ValueError("invalid color layer hash")
        color_layer_path = Path(stroke_path).with_suffix(".color.png")
        with color_layer_path.open("rb") as source:
            if hashlib.file_digest(source, "sha256").hexdigest() != color_layer_sha256:
                raise ValueError("color layer hash mismatch")
        color_layer = Image.open(color_layer_path).convert("RGBA")
        if color_layer.size != (source_width, source_height):
            raise ValueError("color layer dimensions do not match strokes")
        from sketch2life.infrastructure.media.whiteboard_color_regions import (
            prepare_color_regions,
        )

        color_regions = prepare_color_regions(
            color_layer, source_strokes, scale=scale, offset_x=offset_x, offset_y=offset_y
        )

    segment_count = sum(max(0, len(points) - 1) for points in strokes)
    ink_scale = 2
    smooth_strokes = [
        [(x * ink_scale, y * ink_scale) for x, y in points]
        for points in strokes
    ]
    frame_count = round(render_spec.fps * render_spec.duration_seconds)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    writer = imageio.get_writer(
        output,
        fps=render_spec.fps,
        codec="libx264",
        pixelformat="yuv420p",
        quality=8,
    )
    ink = Image.new(
        "RGB",
        (render_spec.width * ink_scale, render_spec.height * ink_scale),
        "white",
    )
    ink_draw = ImageDraw.Draw(ink)
    colored = Image.new("RGBA", (render_spec.width, render_spec.height))
    color_steps = [0] * len(color_regions)
    stroke_index = 0
    stroke_segment = 0
    rendered_segments = 0
    active_point = None
    try:
        for frame_index in range(frame_count):
            progress = frame_index / max(1, frame_count - 1)
            drawing_progress = (
                min(1.0, progress / 0.78)
                if color_regions
                else min(1.0, progress * 1.08)
            )
            visible_segments = round(segment_count * drawing_progress)
            while rendered_segments < visible_segments:
                points = smooth_strokes[stroke_index]
                stroke_color = stroke_colors[stroke_index]
                count = min(
                    len(points) - 1 - stroke_segment,
                    visible_segments - rendered_segments,
                )
                if count == 1 and points[stroke_segment] == points[stroke_segment + 1]:
                    x, y = points[stroke_segment]
                    radius = 2 * ink_scale
                    ink_draw.ellipse(
                        (x - radius, y - radius, x + radius, y + radius),
                        fill=stroke_color,
                    )
                else:
                    ink_draw.line(
                        points[stroke_segment : stroke_segment + count + 1],
                        fill=stroke_color,
                        width=4 * ink_scale,
                        joint="curve",
                    )
                    radius = 2 * ink_scale
                    for x, y in (points[stroke_segment], points[stroke_segment + count]):
                        ink_draw.ellipse(
                            (x - radius, y - radius, x + radius, y + radius),
                            fill=stroke_color,
                        )
                stroke_segment += count
                rendered_segments += count
                active_point = strokes[stroke_index][stroke_segment]
                if stroke_segment == len(points) - 1:
                    stroke_index += 1
                    stroke_segment = 0
            image = ink.resize(
                (render_spec.width, render_spec.height), Image.Resampling.LANCZOS
            )
            for region_index, (region, (region_x, region_y), trigger) in enumerate(color_regions):
                start = 0.78 * trigger / max(1, segment_count)
                desired = min(4, max(0, int((progress - start) / 0.12 * 4)))
                if frame_index == frame_count - 1:
                    desired = 4
                previous = color_steps[region_index]
                if desired > previous:
                    left = round(region.width * previous / 4)
                    right = round(region.width * desired / 4)
                    if right > left:
                        colored.alpha_composite(
                            region.crop((left, 0, right, region.height)),
                            (region_x + left, region_y),
                        )
                    color_steps[region_index] = desired
            if color_regions:
                image.paste(colored, (0, 0), colored)
            if active_point is not None and visible_segments < segment_count:
                draw = ImageDraw.Draw(image, "RGBA")
                _draw_marker_hand(draw, active_point)
            frame = np.asarray(image)
            if motion_schedule:
                motion_index, motion_progress = _motion_position(
                    progress, motion_schedule, motion_durations_seconds
                )
                frame = _apply_motion(frame, motion_schedule[motion_index], motion_progress)
            writer.append_data(frame)
    finally:
        writer.close()

    size_bytes = output.stat().st_size
    if size_bytes > render_spec.max_size_bytes:
        raise ValueError("encoded whiteboard MP4 exceeds the size limit")
    return WhiteboardMvpRenderResult(
        output_path=str(output),
        width=render_spec.width,
        height=render_spec.height,
        fps=render_spec.fps,
        duration_seconds=render_spec.duration_seconds,
        codec="H264_AVC_HIGH_L4_1",
        size_bytes=size_bytes,
    )


def _validate_motion_durations(
    motion_schedule: tuple[WhiteboardMotion, ...],
    motion_durations_seconds: tuple[float, ...],
) -> None:
    if motion_durations_seconds and len(motion_durations_seconds) != len(motion_schedule):
        raise ValueError("motion durations must align with the motion schedule")
    if motion_durations_seconds and any(duration <= 0 for duration in motion_durations_seconds):
        raise ValueError("motion durations must be positive")


def _motion_position(
    progress: float,
    motion_schedule: tuple[WhiteboardMotion, ...],
    motion_durations_seconds: tuple[float, ...],
) -> tuple[int, float]:
    if not motion_durations_seconds:
        schedule_position = progress * len(motion_schedule)
        index = min(len(motion_schedule) - 1, int(schedule_position))
        return index, schedule_position - index
    total = sum(motion_durations_seconds)
    position = min(total, progress * total)
    cursor = 0.0
    for index, duration in enumerate(motion_durations_seconds):
        if position <= cursor + duration or index == len(motion_durations_seconds) - 1:
            return index, min(1.0, max(0.0, (position - cursor) / duration))
        cursor += duration
    return len(motion_schedule) - 1, 1.0


def _apply_motion(frame, motion: WhiteboardMotion, progress: float = 0.0):
    """Add visible storyboard motion without introducing unreviewed claims."""

    import numpy as np
    from PIL import Image, ImageDraw

    height, width = frame.shape[:2]
    if motion == "INTRO":
        scale = 0.92 + (0.08 * progress)
        return _center_scale(frame, scale)

    if motion == "FOCUS":
        scale = 1.12 + (0.12 * progress)
        crop_height = round(height / scale)
        crop_width = round(width / scale)
        top = (height - crop_height) // 2
        left = (width - crop_width) // 2
        focused = Image.fromarray(
            frame[top : top + crop_height, left : left + crop_width]
        )
        return np.asarray(focused.resize((width, height), Image.Resampling.LANCZOS))

    if motion == "DEMONSTRATE":
        image = Image.fromarray(frame)
        draw = ImageDraw.Draw(image, "RGBA")
        center_x, center_y = width // 2, height // 2
        radius = round(min(width, height) * (0.14 + 0.05 * progress))
        blue = (43, 105, 176, 220)
        gold = (234, 159, 45, 220)
        draw.ellipse(
            (center_x - radius, center_y - radius, center_x + radius, center_y + radius),
            outline=gold,
            width=8,
        )
        arrow_y = round(height * (0.78 - 0.20 * progress))
        margin = round(width * 0.16)
        draw.line((margin, arrow_y, width - margin, arrow_y), fill=blue, width=7)
        draw.polygon(
            ((margin, arrow_y), (margin + 34, arrow_y - 24), (margin + 34, arrow_y + 24)),
            fill=blue,
        )
        draw.polygon(
            ((width - margin, arrow_y), (width - margin - 34, arrow_y - 24),
             (width - margin - 34, arrow_y + 24)),
            fill=blue,
        )
        return np.asarray(image)

    if motion == "RECAP":
        return _center_scale(frame, 1.06 - (0.06 * progress))

    return frame


def _center_scale(frame, scale: float):
    """Scale around the canvas center while preserving the output dimensions."""

    import numpy as np
    from PIL import Image

    height, width = frame.shape[:2]
    if scale <= 1.0:
        return frame
    crop_height = max(1, round(height / scale))
    crop_width = max(1, round(width / scale))
    top = (height - crop_height) // 2
    left = (width - crop_width) // 2
    cropped = Image.fromarray(frame[top : top + crop_height, left : left + crop_width])
    return np.asarray(cropped.resize((width, height), Image.Resampling.LANCZOS))


def _ordered_boundary_points(mask):
    """Return a deterministic contour-like order for progressive drawing."""

    import numpy as np

    ys, xs = np.where(mask)
    if len(xs) == 0:
        return []
    points = np.column_stack((xs, ys)).astype(np.int32)
    if len(points) > 8000:
        sample = np.linspace(0, len(points) - 1, 8000, dtype=np.int32)
        points = points[sample]
    center = points.mean(axis=0)
    angles = np.arctan2(points[:, 1] - center[1], points[:, 0] - center[0])
    order = np.argsort(angles)
    return [tuple(point) for point in points[order].tolist()]


def _draw_progressive_strokes(frame, points, progress: float):
    """Draw the subject contour and move a visible marker hand with the pen."""

    import numpy as np
    from PIL import Image, ImageDraw

    if len(points) < 2 or progress <= 0:
        return frame
    visible_count = max(2, round(len(points) * min(1.0, progress * 1.35)))
    image = Image.fromarray(frame)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.line(
        points[:visible_count],
        fill=(35, 35, 35, 235),
        width=4,
        joint="curve",
    )
    _draw_marker_hand(draw, points[visible_count - 1])
    return np.asarray(image)


def _draw_marker_hand(draw, point):
    """Draw a small whiteboard hand/marker cursor at the active stroke point."""

    x, y = point
    hand_x, hand_y = x + 22, y + 28
    outline = (28, 34, 42, 255)
    skin = (255, 224, 190, 255)
    sleeve = (54, 112, 190, 255)
    draw.line((x, y, hand_x, hand_y - 8), fill=(43, 105, 176, 255), width=5)
    draw.line((x, y, x + 14, y - 18), fill=outline, width=4)
    draw.ellipse(
        (hand_x - 15, hand_y - 12, hand_x + 17, hand_y + 23),
        fill=skin,
        outline=outline,
        width=3,
    )
    draw.rounded_rectangle(
        (hand_x - 17, hand_y + 13, hand_x + 19, hand_y + 31),
        radius=8,
        fill=sleeve,
        outline=outline,
        width=3,
    )
    draw.line(
        (hand_x - 4, hand_y - 8, hand_x + 4, hand_y - 25),
        fill=skin,
        width=8,
    )


__all__ = [
    "WhiteboardMvpRenderResult",
    "WhiteboardMvpRenderSpec",
    "WhiteboardMotion",
    "render_progressive_reveal",
    "render_stroke_animation",
]
