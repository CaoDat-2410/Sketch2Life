"""Owned strict CMD-40/DATA-27 candidate; not upstream DATA-26 or adopted auth."""

from __future__ import annotations

from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from sketch2life.contracts.schemas.ai_contract_candidates import OpaqueId, Sha256Hex

VideoStrategy = Literal["reviewed_library", "generate", "compose_library"]


class StrictVideoModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class VideoExactRef(StrictVideoModel):
    ref: OpaqueId
    version: int = Field(ge=1)
    hash: Sha256Hex


class CreateKnowledgeVideo(StrictVideoModel):
    """Session/org/principal come from verified server context, never this body.

    Optional library candidate is resolved/revalidated server-side; its presence
    is not a publication/rights proof. No mandatory pre-render script approval.
    """

    bundle_id: OpaqueId
    bundle_version: int = Field(ge=1)
    bundle_hash: Sha256Hex
    audience_context_revision: int = Field(ge=0)
    strategy: VideoStrategy
    candidate_library_asset_ref: VideoExactRef | None = None
    requested_profile_ref: VideoExactRef | None = None

    @model_validator(mode="after")
    def compatible_candidate(self) -> CreateKnowledgeVideo:
        if self.strategy == "generate" and self.candidate_library_asset_ref is not None:
            raise ValueError("VIDEO_STRATEGY_REF_MISMATCH")
        return self


class VideoAttemptView(StrictVideoModel):
    """Safe attempt provenance from the owning job; no worker bearer capability."""

    attempt_id: OpaqueId
    attempt_number: int = Field(ge=1)
    state: Literal[
        "queued", "running", "succeeded", "failed_retryable", "failed_exhausted",
        "blocked_unsafe", "cancelled"
    ]


class KnowledgeVideoView(StrictVideoModel):
    """Create/status projection owned08; later review/playback extensions owned09.

    Deliberately no playback URL, provider configuration or raw script. Only
    pre-review states can be produced by this component, not fake approval.
    """

    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    video_id: OpaqueId
    video_version: int = Field(ge=1)
    video_run_revision: int = Field(ge=1)
    video_review_revision: int = Field(ge=1)
    organization_id: OpaqueId
    session_id: OpaqueId
    job_id: OpaqueId
    job_revision: int = Field(ge=1)
    generation_state: Literal[
        "queued", "running", "succeeded", "failed_retryable", "failed_exhausted",
        "blocked_unsafe", "cancelled"
    ]
    review_state: Literal["pending_media", "ready_for_review"]
    playback_state: Literal["not_started"] = "not_started"
    retry_policy_version: VideoExactRef
    attempt_history: tuple[VideoAttemptView, ...]
    artifact_ref: VideoExactRef | None = None
    failed_exhausted_at: AwareDatetime | None = None
    disposition: None = None
    created_at: AwareDatetime

    @model_validator(mode="after")
    def consistent_axes(self) -> KnowledgeVideoView:
        if (len({item.attempt_id for item in self.attempt_history}) != len(self.attempt_history)
                or [item.attempt_number for item in self.attempt_history]
                != list(range(1, len(self.attempt_history) + 1))):
            raise ValueError("VIDEO_INVALID_ATTEMPT_HISTORY")
        ready = self.generation_state == "succeeded"
        if (ready != (self.artifact_ref is not None)
                or ready != (self.review_state == "ready_for_review")):
            raise ValueError("VIDEO_INCONSISTENT_AXES")
        if (self.generation_state == "failed_exhausted") != (
            self.failed_exhausted_at is not None
        ):
            raise ValueError("VIDEO_EXHAUSTION_TIME_MISMATCH")
        if self.failed_exhausted_at is not None and self.failed_exhausted_at < self.created_at:
            raise ValueError("VIDEO_INVALID_TIME")
        return self
