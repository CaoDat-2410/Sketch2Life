"""Start the video container while the Parent reads the story to confirm it (FEAT-094 S6).

Getting an L40S and loading the preparation models takes minutes. The call carries no data; if the adult abandons the
story, the idle container stops by itself after five minutes.
"""

from __future__ import annotations

from typing import Final

from sketch2life.infrastructure.ai.modal_qwen_warm_up import QwenWarmUp
from sketch2life.infrastructure.story_video.modal_scene_renderer import APP_NAME, FUNCTION_NAME

IDLE_WINDOW_SECONDS: Final = 240.0  # shorter than the container's idle time, so a second story keeps it up


class VideoWarmUp(QwenWarmUp):
    APP = APP_NAME
    FUNCTION = FUNCTION_NAME
    PAYLOAD = {"prepare_warmup": True}
    EVENT = "video_warm_up_not_dispatched"
    WINDOW = IDLE_WINDOW_SECONDS


__all__ = ["VideoWarmUp"]
