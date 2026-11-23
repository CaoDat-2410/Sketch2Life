"""Versioned Parent technical video-candidate API contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ParentVideoCandidateRequestV1(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    expected_story_revision: int = Field(ge=1, le=4)
    expected_story_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class ParentVideoCandidateMetadataV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    duration_seconds: float = Field(gt=0, le=90)
    width: int = Field(ge=1, le=1920)
    height: int = Field(ge=1, le=1080)
    fps: float = Field(gt=0, le=60)
    video_codec: str = Field(min_length=1, max_length=16)
    audio_streams: Literal[0]
    scene_count: int = Field(ge=5, le=15)
    video_profile: str = Field(min_length=1, max_length=96)
    model_id: str = Field(min_length=1, max_length=128)
    model_revision: str = Field(min_length=1, max_length=80)
    technical_validation: Literal["PASS"]
    consistency_validation: Literal["NOT_RUN"]
    safety_validation: Literal["NOT_RUN"]
    product_playable: Literal[False]


class ParentVideoCandidateV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    video_candidate_id: UUID
    story_run_id: UUID
    story_revision_id: UUID
    story_revision: int = Field(ge=1, le=4)
    story_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    state: Literal[
        "STAGING",
        "DISPATCHING",
        "QUEUED",
        "GENERATING",
        "CANDIDATE_READY",
        "FAILED",
        "AWAITING_RECONCILIATION",
    ]
    safe_failure_code: str | None = Field(default=None, max_length=80)
    metadata: ParentVideoCandidateMetadataV1 | None = None
    preview_available: bool
    product_playable: Literal[False] = False
    safety_validation: Literal["NOT_RUN"] = "NOT_RUN"
    created_at: datetime
    updated_at: datetime


class ParentVideoCandidateEnvelopeV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: UUID
    video_candidate: ParentVideoCandidateV1


class ParentCurrentVideoCandidateEnvelopeV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: UUID
    video_candidate: ParentVideoCandidateV1 | None


class ParentVideoCandidateErrorEnvelopeV1(BaseModel):
    code: str
    message: str
    correlation_id: str
    retryable: bool
    retry_after_seconds: int | None = None


__all__ = [
    "ParentCurrentVideoCandidateEnvelopeV1",
    "ParentVideoCandidateEnvelopeV1",
    "ParentVideoCandidateErrorEnvelopeV1",
    "ParentVideoCandidateMetadataV1",
    "ParentVideoCandidateRequestV1",
    "ParentVideoCandidateV1",
]
