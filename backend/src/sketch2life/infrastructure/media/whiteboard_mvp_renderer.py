"""Dependency-backed MVP renderer for FEAT-018 whiteboard videos.

The renderer intentionally implements the validated Kaggle MVP: a progressive
reveal of an RGBA cutout on a white 1280x720 canvas. Stroke-order animation is
kept as a later renderer strategy.
"""

from __future__ import annotations

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

    source = Image.open(cutout_path).convert("RGBA")
    source.thumbnail((560, 560), Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", (render_spec.width, render_spec.height))
    x = (render_spec.width - source.width) // 2
    y = (render_spec.height - source.height) // 2
    canvas.alpha_composite(source, (x, y))

    rgba = np.asarray(canvas)
    rgb = rgba[:, :, :3].astype(np.float32)
    alpha = rgba[:, :, 3].astype(np.float32) / 255.0
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
            if motion_schedule:
                schedule_position = progress * len(motion_schedule)
                motion_index = min(
                    len(motion_schedule) - 1,
                    int(schedule_position),
                )
                motion_progress = schedule_position - motion_index
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


__all__ = [
    "WhiteboardMvpRenderResult",
    "WhiteboardMvpRenderSpec",
    "WhiteboardMotion",
    "render_progressive_reveal",
]
