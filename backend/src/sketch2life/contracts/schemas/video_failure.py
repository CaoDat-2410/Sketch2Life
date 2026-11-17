"""Owned DATA-28/CMD-43 candidates; pending extension is not confirmed upstream outcome."""

from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from sketch2life.contracts.schemas.ai_contract_candidates import OpaqueId, Sha256Hex
from sketch2life.contracts.schemas.knowledge_video import VideoExactRef


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class FailureDispositionCommand(_Strict):
    action: Literal["retry", "skip", "end_session"]
    reason: str = Field(min_length=1, max_length=200)
    expected_video_version: int = Field(ge=1, le=2**63 - 1)
    expected_job_revision: int = Field(ge=1, le=2**63 - 1)
    expected_session_revision: int = Field(ge=0, le=2**63 - 1)
    retry_authorization_note: str | None = Field(default=None, min_length=1, max_length=200)

    @model_validator(mode="after")
    def valid_text(self) -> "FailureDispositionCommand":
        if not self.reason.strip() or (
            self.retry_authorization_note is not None
            and (not self.retry_authorization_note.strip() or self.action != "retry")
        ):
            raise ValueError("VIDEO_DISPOSITION_INVALID_COMMAND")
        return self


class PendingDisposition(_Strict):
    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    status: Literal["pending"] = "pending"
    disposition_id: OpaqueId
    operation_key: Sha256Hex
    reason_code: Literal["VIDEO_DISPOSITION_PENDING"] = "VIDEO_DISPOSITION_PENDING"


class ConfirmedDisposition(_Strict):
    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    disposition_id: OpaqueId
    recorded_by: OpaqueId
    recorded_at: AwareDatetime
    action: Literal["retry", "skip", "end_session"]
    reason: str = Field(min_length=1, max_length=200)
    prior_failure_ref: VideoExactRef
    session_revision: int = Field(ge=0)
    video_run_revision: int = Field(ge=1)
    outcome: Literal["retry_pending", "skipped_by_teacher", "session_ended_early"]
    new_job_id: OpaqueId | None

    @model_validator(mode="after")
    def axes(self) -> "ConfirmedDisposition":
        expected = {
            "retry": "retry_pending",
            "skip": "skipped_by_teacher",
            "end_session": "session_ended_early",
        }
        if (
            self.outcome != expected[self.action]
            or ((self.action == "retry") != (self.new_job_id is not None))
            or not self.reason.strip()
        ):
            raise ValueError("VIDEO_DISPOSITION_INVALID_PROJECTION")
        return self
