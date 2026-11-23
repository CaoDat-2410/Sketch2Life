"""Versioned HTTP DTOs of the Parent video routes (FEAT-066 T-1a ``video-generations``; T-1b
``video-unsuitable`` and ``complete``, SRS l.1671-1672; T-1c the playback grant and the video part
of ``StoryRunDetailV1``, SRS l.1676, l.1811).

SRS l.1670 lists the script hash, the quality-reason code and the idempotency key; the run
``expected_revision`` is a deliberate addition (l.1699: "gửi expected revision/hash", the stale
guard of the Story family) and the Android task is told. The 202 body carries the intent reference
and the state of the saga: ``ADMISSION_PENDING`` until both receipts are clear, ``ACCEPTED`` with a
``job_id`` once they are (l.1670). It never carries a storage key, a URL, a quota figure or any
provider text.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

QualityReasonCode = Literal["QUALITY_LOW", "NOT_MATCHING_STORY", "CONTENT_CONCERN", "OTHER"]
VideoGenerationState = Literal[
    "ADMISSION_PENDING",
    "ADMISSION_REJECTED",
    "ACCEPTED",
    "QUEUED",
    "GENERATING",
    "TECHNICAL_VALIDATING",
    "SAFETY_VALIDATING",
    "READY",
    "SAFETY_BLOCKED",
    "FAILED",
    "REJECTED_BY_ADULT",
    "SUPERSEDED",
]


class ParentVideoGenerationRequestV1(BaseModel):
    """The confirmed script the adult asks a video for; the reason only on a regeneration."""

    model_config = ConfigDict(extra="forbid", strict=True)

    expected_revision: int = Field(ge=1)
    story_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    quality_reason_code: QualityReasonCode | None = None


class ParentVideoUnsuitableRequestV1(BaseModel):
    """The adult marks the current ready video as not suitable (SRS l.1671).

    ``generation_id`` is the generation the adult saw (the run's current one); the reason is the
    closed safe set, never free text. ``expected_revision`` is the stale guard of the Story family.
    """

    model_config = ConfigDict(extra="forbid", strict=True)

    expected_revision: int = Field(ge=1)
    # FastAPI validates parsed JSON values in Python mode, where UUIDs arrive as strings.
    generation_id: UUID = Field(strict=False)
    reason_code: QualityReasonCode


class ParentStoryRunCompleteRequestV1(BaseModel):
    """The adult finishes the run at ``VIDEO_READY`` (SRS l.1672): not a video approval."""

    model_config = ConfigDict(extra="forbid", strict=True)

    expected_revision: int = Field(ge=1)


class ParentVideoGenerationV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generation_id: UUID
    state: VideoGenerationState
    generation_no: int | None = Field(ge=1, le=3)
    kind: Literal["INITIAL", "QUALITY_REGEN"]
    job_id: str | None = Field(
        description="Opaque job id to poll through GET /v1/jobs/{job_id}; null until accepted."
    )
    run_state: str
    run_revision: int = Field(ge=1)


class ParentVideoGenerationAcceptedV1(BaseModel):
    """202 body: the intent reference and its state (SRS l.1670)."""

    model_config = ConfigDict(extra="forbid")

    request_id: UUID
    video_generation: ParentVideoGenerationV1


VideoJobPublicState = Literal[
    "queued", "running", "succeeded", "failed_exhausted", "blocked_unsafe"
]
VideoSceneState = Literal["QUEUED", "GENERATING", "READY", "FAILED"]
PlaybackReadiness = Literal["AVAILABLE", "HIDDEN", "UNAVAILABLE"]


class ParentPlaybackGrantV1(BaseModel):
    """A short-lived grant for one ready video (SRS l.1676, l.1691). The token is a bearer
    secret: it is sent in the ``X-Playback-Token`` header of the stream route, never in a URL.
    ``asset_ref`` is an opaque handle; no bucket, key or URL is ever part of it (l.1692)."""

    model_config = ConfigDict(extra="forbid")

    token: str
    expires_at: datetime
    stream_path: str
    media_type: Literal["video/mp4"]
    asset_ref: str


class ParentPlaybackTokenResponseV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: UUID
    playback: ParentPlaybackGrantV1


class ParentVideoJobSummaryV1(BaseModel):
    """The job of the current generation, with the safe failure code set only (SRS l.875)."""

    model_config = ConfigDict(extra="forbid")

    job_id: str
    state: VideoJobPublicState
    stage: str | None
    retryable: bool
    error_code: str | None


class ParentVideoSceneStateV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scene_index: int = Field(ge=1, le=15)
    state: VideoSceneState


class ParentVideoPlaybackV1(BaseModel):
    """Playback readiness and the route that issues the token; never a token itself."""

    model_config = ConfigDict(extra="forbid")

    state: PlaybackReadiness
    asset_ref: str | None
    token_route: str | None


class ParentVideoHistoryItemV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generation_id: UUID
    generation_no: int = Field(ge=1, le=3)
    kind: Literal["INITIAL", "QUALITY_REGEN"]
    state: VideoGenerationState


class ParentStoryRunVideoV1(BaseModel):
    """The video part of ``StoryRunDetailV1`` (SRS l.1811, AC-41).

    ``video_requests_used`` and ``video_requests_remaining`` are the three-request run cap of
    FR-AI-07 (l.573), not the monthly quota. Neither a prompt, a transcript, provider text, a
    storage key nor a foreign scope is part of it.
    """

    model_config = ConfigDict(extra="forbid")

    current_generation_id: UUID
    generation_no: int | None = Field(ge=1, le=3)
    kind: Literal["INITIAL", "QUALITY_REGEN"]
    state: VideoGenerationState
    job: ParentVideoJobSummaryV1 | None
    scenes: list[ParentVideoSceneStateV1]
    playback: ParentVideoPlaybackV1
    video_requests_used: int = Field(ge=0, le=3)
    video_requests_remaining: int = Field(ge=0, le=3)
    admission_pending: bool
    history: list[ParentVideoHistoryItemV1] = Field(max_length=3)


class ParentStoryQuotaSummaryV1(BaseModel):
    """The monthly video quota summary (SRS l.1811, TD-22). Story owns no quota figure: until the
    Billing reader exists the state is the constant ``UNAVAILABLE`` and every figure is null, never
    zero. The field names follow the Billing balance read (granted, used, available, month)."""

    model_config = ConfigDict(extra="forbid")

    state: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    granted: int | None = None
    used: int | None = None
    available: int | None = None
    month: str | None = None


class ParentStoryTimelineEventV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event: str
    at: datetime


__all__ = [
    "ParentPlaybackGrantV1",
    "ParentPlaybackTokenResponseV1",
    "ParentStoryQuotaSummaryV1",
    "ParentStoryRunVideoV1",
    "ParentStoryTimelineEventV1",
    "ParentVideoHistoryItemV1",
    "ParentVideoJobSummaryV1",
    "ParentVideoPlaybackV1",
    "ParentVideoSceneStateV1",
    "PlaybackReadiness",
    "ParentStoryRunCompleteRequestV1",
    "ParentVideoGenerationAcceptedV1",
    "ParentVideoGenerationRequestV1",
    "ParentVideoGenerationV1",
    "ParentVideoUnsuitableRequestV1",
    "QualityReasonCode",
    "VideoGenerationState",
]
