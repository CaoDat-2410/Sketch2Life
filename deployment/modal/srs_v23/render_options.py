"""FEAT-098 B2: speed options of the scene renderer. One is on only once its clips are accepted.

Named in one setting, comma separated, read when the video app is deployed (``none``: all off):

- ``conv_vae``: the convolution video VAE instead of the diffusion VAE (lighter, faster decoding; softer possible).
- ``small``: render 960x576 and scale to 720p (two-stage LTX needs multiples of 64, so not 960x544).
- ``fps16``: render 16 frames a second and interpolate to 24 with ffmpeg.

The delivered clip keeps one profile: 1280x720 at 24 frames a second with the planned frame count.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

OPTIONS_ENV: Final = "SKETCH2LIFE_VIDEO_OPTIONS"
OUTPUT_WIDTH: Final = 1280
OUTPUT_HEIGHT: Final = 720
OUTPUT_FPS: Final = 24
_NAMES: Final = ("conv_vae", "small", "fps16")
# The owner's choice from the measured clips (2026-11-27); a deploy uses it unless the setting says otherwise.
ACCEPTED: Final = "conv_vae,small"


@dataclass(frozen=True, slots=True)
class RenderOptions:
    conv_vae: bool = False
    small: bool = False
    fps16: bool = False

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(name for name in _NAMES if getattr(self, name))

    @property
    def width(self) -> int:
        return 960 if self.small else OUTPUT_WIDTH

    @property
    def height(self) -> int:
        return 576 if self.small else 768

    @property
    def fps(self) -> int:
        return 16 if self.fps16 else OUTPUT_FPS

    def video_filter(self, *, target_frame_count: int, generated_frame_count: int) -> str:
        """The ffmpeg filter that turns a rendered clip into the delivered profile."""

        time_scale = (target_frame_count / OUTPUT_FPS) / (generated_frame_count / self.fps)
        picture_height = self.width * 9 // 16
        filters = [
            f"setpts=PTS*{time_scale:.12f}",
            f"crop={self.width}:{picture_height}:0:{(self.height - picture_height) // 2}",
        ]
        scale = [f"scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:flags=lanczos"] if self.small else []
        if self.fps16:
            # Interpolated before scaling (fewer pixels); the last frame is repeated because interpolation stops short.
            filters += [f"minterpolate=fps={OUTPUT_FPS}", "tpad=stop_mode=clone:stop_duration=1", *scale]
        else:
            filters += [*scale, f"fps={OUTPUT_FPS}"]
        filters += [f"trim=end_frame={target_frame_count}", f"setpts=N/({OUTPUT_FPS}*TB)"]
        return ",".join(filters)


def parse_options(text: str) -> RenderOptions:
    names = {part.strip() for part in text.split(",") if part.strip()} - {"none"}
    if not names <= set(_NAMES):
        raise ValueError("VIDEO_RENDER_OPTION_UNKNOWN")
    return RenderOptions(**dict.fromkeys(names, True))


__all__ = ["ACCEPTED", "OPTIONS_ENV", "RenderOptions", "parse_options"]
