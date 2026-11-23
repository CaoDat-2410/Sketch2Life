"""Composition of the video admission ports from settings (FEAT-066 T-1a; OD-03, T-2z).

``story_video_adapters`` is ``unconfigured`` by default: no port is composed and the route answers
503 ``PROVIDER_UNAVAILABLE`` after its authorization and state checks. ``local_test`` composes the
accept-all local/test pair and is refused outside local/test by ``Settings`` and by the adapter
constructors. No production adapter exists in this task (the owner of each port builds it).
"""

from __future__ import annotations

from sketch2life.application.ports.story_video import StoryVideoAdapters
from sketch2life.infrastructure.config.settings import Settings
from sketch2life.infrastructure.story_video.local_adapters import build_local_video_adapters


def build_story_video_adapters(settings: Settings) -> StoryVideoAdapters | None:
    if settings.story_video_adapters == "local_test":
        return build_local_video_adapters(env=settings.env)
    return None


__all__ = ["build_story_video_adapters"]
