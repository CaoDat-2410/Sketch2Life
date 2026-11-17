"""Owned09 HTTP candidates, not a fork of shared DATA-24 or an access grant."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sketch2life.contracts.schemas.ai_contract_candidates import (
    ExactContentReviewRecordV1,
    OpaqueId,
    Sha256Hex,
)


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class StartVideoPlayback(_Strict):
    """Assertions compared to owner-resolved exact subject, NEVER authority.

    Path video and verified server org/session are not client body fields.
    Session CAS is explicit here; review If-Match belongs to CMD-41 only.
    """

    target_version: int = Field(ge=1, le=2**63 - 1)
    target_hash: Sha256Hex
    subject_digest: Sha256Hex
    review_id: OpaqueId
    review_revision: int = Field(ge=1, le=2**63 - 1)
    expected_session_revision: int = Field(ge=0, le=2**63 - 1)


class VideoReviewRecorded(_Strict):
    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    video_id: OpaqueId
    target_version: int = Field(ge=1)
    target_hash: Sha256Hex
    record: ExactContentReviewRecordV1
    current_review_revision: int = Field(ge=1)
    replayed: bool

    @model_validator(mode="after")
    def consistent_revision(self) -> VideoReviewRecorded:
        if (
            self.current_review_revision < self.record.review_revision
            or (
                not self.replayed
                and (
                    self.current_review_revision != self.record.review_revision
                    or self.record.state != "effective"
                )
            )
            or (
                self.record.state == "effective"
                and self.current_review_revision != self.record.review_revision
            )
        ):
            raise ValueError("VIDEO_REVIEW_INVALID_PROJECTION")
        return self


class VideoPlaybackResult(_Strict):
    """Historical receipt status only; not live playing, media URL or permission."""

    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    status: Literal["pending", "confirmed", "rejected"]
    operation_key: Sha256Hex
    reason_code: Literal[
        "VIDEO_PLAYBACK_PENDING", "VIDEO_PLAYBACK_CONFIRMED", "VIDEO_PLAYBACK_REJECTED"
    ]
    receipt_id: OpaqueId | None

    @model_validator(mode="after")
    def consistent_receipt(self) -> VideoPlaybackResult:
        if self.reason_code != "VIDEO_PLAYBACK_" + self.status.upper() or (
            (self.status == "pending") != (self.receipt_id is None)
        ):
            raise ValueError("VIDEO_PLAYBACK_INVALID_PROJECTION")
        return self
