"""Composition of the video admission ports from settings (FEAT-066 T-1a; OD-03, T-2z).

``story_video_adapters`` is ``unconfigured`` by default: no port is composed and the route answers
503 ``PROVIDER_UNAVAILABLE`` after its authorization and state checks. ``local_test`` composes the
accept-all local/test pair and is refused outside local/test by ``Settings`` and by the adapter
constructors. ``billing`` composes Billing quota admission when its session factory is available.
The production Story video compute-reservation adapter is not currently composed in this worktree,
so the billing mode remains fail-closed outside local/test until one is supplied.
"""

from __future__ import annotations

from collections.abc import Callable

from sqlalchemy.orm import Session

from sketch2life.application.ports.story_video import (
    StoryVideoAdapters,
    VideoComputeReservationPort,
)
from sketch2life.infrastructure.config.settings import Settings
from sketch2life.infrastructure.story_video.billing_quota_admission import (
    BillingVideoQuotaAdmission,
)
from sketch2life.infrastructure.story_video.local_adapters import build_local_video_adapters


def build_story_video_adapters(
    settings: Settings,
    *,
    session_factory: Callable[[], Session] | None = None,
    reservation: VideoComputeReservationPort | None = None,
) -> StoryVideoAdapters | None:
    if settings.story_video_adapters == "local_test":
        return build_local_video_adapters(env=settings.env)
    if settings.story_video_adapters == "billing":
        if session_factory is None:
            return None
        if reservation is None:
            if settings.env not in {"local", "test"}:
                return None
            reservation = build_local_video_adapters(env=settings.env).reservation
        return StoryVideoAdapters(
            reservation=reservation,
            quota=BillingVideoQuotaAdmission(session_factory, settings),
        )
    return None


__all__ = ["build_story_video_adapters"]
