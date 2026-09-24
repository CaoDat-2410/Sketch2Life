"""Dependency-backed MVP renderer for FEAT-018 whiteboard videos.

The renderer intentionally implements the validated Kaggle MVP: a progressive
reveal of an RGBA cutout on a white 1280x720 canvas. Stroke-order animation is
kept as a later renderer strategy.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


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
        if not 5.0 <= self.duration_seconds <= 10.0:
            raise ValueError("render duration must be between 5 and 10 seconds")


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


__all__ = [
    "WhiteboardMvpRenderResult",
    "WhiteboardMvpRenderSpec",
    "render_progressive_reveal",
]
