"""DATA-25 AsyncJobView / CMD-44 candidate wire contracts (BE2-01 Phase A).

Candidate version ``0.1-candidate``: not adopted into the shared registry. Unknown fields are
rejected and malformed values are never silently repaired.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_serializer, model_validator

CANDIDATE_VERSION = "0.1-candidate"
DATA25_OWNER = "BE2-01"

JobStateName = Literal[
    "queued",
    "running",
    "succeeded",
    "failed_retryable",
    "failed_exhausted",
    "blocked_unsafe",
    "cancelled",
]
TERMINAL = {"succeeded", "failed_exhausted", "blocked_unsafe", "cancelled"}
OpaqueId = Annotated[str, Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9_.:-]+$")]
Sha256Hex = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
ErrorCode = Annotated[str, Field(pattern=r"^[A-Z][A-Z0-9_]{1,79}$")]


class _Strict(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


def _utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


class RequestRefV1(_Strict):
    request_id: OpaqueId
    request_revision: int = Field(ge=1)
    input_hash: Sha256Hex
    context_revision: int = Field(ge=0)


class JobProgressV1(_Strict):
    kind: Literal["unknown", "stages", "percentage"]
    value: float | None = Field(default=None, ge=0, le=100, allow_inf_nan=False)
    stage_label: str | None = Field(default=None, min_length=1, max_length=80)

    @model_validator(mode="after")
    def _consistent(self) -> JobProgressV1:
        if self.kind == "unknown" and (self.value is not None or self.stage_label is not None):
            raise ValueError("unknown progress must have value=null and stage_label=null")
        if self.kind == "percentage" and self.value is None:
            raise ValueError("percentage progress requires a real value")
        if self.kind == "stages" and self.stage_label is None:
            raise ValueError("stages progress requires stage_label")
        return self


class JobFailureV1(_Strict):
    code: ErrorCode
    retryable: bool
    public_message: str = Field(min_length=1, max_length=200)
    attempts_remaining: int | None = Field(default=None, ge=0)


class ChildJobFailureV1(_Strict):
    code: ErrorCode
    retryable: bool
    public_message: str = Field(min_length=1, max_length=200)


class ResultRefV1(_Strict):
    artifact_ref: OpaqueId
    sha256: Sha256Hex


class AsyncJobViewV1(_Strict):
    """DATA-25 Teacher/Admin projection (all DATA-25 fields; refs may be withheld)."""

    job_id: OpaqueId
    organization_id: OpaqueId
    job_type: OpaqueId
    job_revision: int = Field(ge=1)
    request_ref: RequestRefV1
    attempt_id: OpaqueId
    attempt_number: int = Field(ge=1)
    state: JobStateName
    result_disposition: Literal["accepted", "stale", "rejected"] | None
    created_at: AwareDatetime
    updated_at: AwareDatetime
    correlation_id: OpaqueId
    started_at: AwareDatetime | None
    completed_at: AwareDatetime | None
    progress: JobProgressV1
    result_refs: tuple[ResultRefV1, ...] = Field(max_length=32)
    failure: JobFailureV1 | None
    poll_after_ms: int | None = Field(ge=0)

    @field_serializer("created_at", "updated_at", "started_at", "completed_at")
    def _ser_time(self, value: datetime | None) -> str | None:
        return _utc(value)

    @model_validator(mode="after")
    def _consistent(self) -> AsyncJobViewV1:
        if self.updated_at < self.created_at:
            raise ValueError("updated_at precedes created_at")
        terminal = self.state in TERMINAL
        if terminal and self.completed_at is None:
            raise ValueError("terminal state requires completed_at")
        if not terminal and self.completed_at is not None:
            raise ValueError("non-terminal state cannot have completed_at")
        if self.state == "queued" and self.started_at is not None:
            raise ValueError("queued attempt cannot have started_at")
        if self.state == "running" and self.started_at is None:
            raise ValueError("running attempt requires started_at")
        if self.state == "succeeded" and self.result_disposition not in {"accepted", "stale"}:
            raise ValueError("succeeded requires accepted or stale disposition")
        if not terminal and self.result_disposition is not None:
            raise ValueError("non-terminal state cannot carry a result disposition")
        if self.result_refs and not (
            self.state == "succeeded" and self.result_disposition == "accepted"
        ):
            raise ValueError("result_refs are only exposed for succeeded + accepted")
        _check_state_rules(self.state, self.failure is not None, self.poll_after_ms)
        return self


class AsyncJobChildViewV1(_Strict):
    """Device/Child minimal projection: no request/attempt/result refs or disposition."""

    job_id: OpaqueId
    job_type: OpaqueId
    job_revision: int = Field(ge=1)
    state: JobStateName
    progress: JobProgressV1
    failure: ChildJobFailureV1 | None
    poll_after_ms: int | None = Field(ge=0)

    @model_validator(mode="after")
    def _consistent(self) -> AsyncJobChildViewV1:
        _check_state_rules(self.state, self.failure is not None, self.poll_after_ms)
        return self


def _check_state_rules(state: str, has_failure: bool, poll_after_ms: int | None) -> None:
    """State/failure/poll rules shared by the full and Child projections."""

    if state in {"failed_retryable", "failed_exhausted", "blocked_unsafe"} and not has_failure:
        raise ValueError("failed/blocked state requires failure")
    if state == "succeeded" and has_failure:
        raise ValueError("succeeded state cannot carry failure")
    if state in TERMINAL and poll_after_ms is not None:
        raise ValueError("terminal job must not ask clients to keep polling")


class JobStatusMetaV1(_Strict):
    resource_revision: int = Field(ge=1)
    poll_after_ms: int | None = Field(ge=0)
    projection: Literal["teacher", "admin", "device"]


class AsyncJobEnvelopeV1(_Strict):
    contract_name: Literal["AsyncJobView"] = "AsyncJobView"
    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    correlation_id: OpaqueId
    data: AsyncJobViewV1
    meta: JobStatusMetaV1


class AsyncJobChildEnvelopeV1(_Strict):
    contract_name: Literal["AsyncJobChildView"] = "AsyncJobChildView"
    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    correlation_id: OpaqueId
    data: AsyncJobChildViewV1
    meta: JobStatusMetaV1


class FieldErrorV1(_Strict):
    path: str = Field(min_length=1, max_length=200)
    rule: str = Field(min_length=1, max_length=80)
    message: str = Field(min_length=1, max_length=200)


class ErrorBodyV1(_Strict):
    code: ErrorCode
    message: str = Field(min_length=1, max_length=200)
    retryable: bool
    field_errors: tuple[FieldErrorV1, ...] = ()
    current_revisions: dict[str, int] | None = None
    next_actions: tuple[str, ...] = ()


class CollaborationErrorV1(_Strict):
    contract_name: Literal["CollaborationError"] = "CollaborationError"
    contract_version: Literal["1.0-proposed"] = "1.0-proposed"
    correlation_id: OpaqueId
    error: ErrorBodyV1


class OutputRefV1(_Strict):
    artifact_ref: OpaqueId
    sha256: Sha256Hex


class JobCompletionClaimV1(_Strict):
    """Internal worker port (``W``) candidate. There is no public/Android completion route."""

    contract_name: Literal["AsyncJobCompletion"] = "AsyncJobCompletion"
    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    transport: Literal["internal_worker_port"] = "internal_worker_port"
    job_id: OpaqueId
    attempt_id: OpaqueId
    expected_request_revision: int = Field(ge=1)
    input_hash: Sha256Hex
    context_revision: int = Field(ge=0)
    kind: Literal["success", "failure"]
    outputs: tuple[OutputRefV1, ...] = Field(default=(), max_length=32)
    moderation: Literal["passed", "unsafe", "not_applicable"] = "not_applicable"
    failure_code: ErrorCode | None = None
    retryable: bool = False

    @model_validator(mode="after")
    def _consistent(self) -> JobCompletionClaimV1:
        if self.kind == "failure" and (self.failure_code is None or self.outputs):
            raise ValueError("failure claim needs failure_code and no outputs")
        if self.kind == "success" and self.failure_code is not None:
            raise ValueError("success claim cannot carry failure_code")
        return self


class CreateAiJobCommandV1(_Strict):
    """Internal producer-port candidate used by owning cards (e.g. CMD-32/CMD-40 handlers)."""

    contract_name: Literal["CreateAiJob"] = "CreateAiJob"
    contract_version: Literal["0.1-candidate"] = "0.1-candidate"
    job_type: OpaqueId
    target_id: OpaqueId
    purpose_code: OpaqueId
    session_id: OpaqueId | None
    subject_refs: tuple[OpaqueId, ...] = Field(max_length=64)
    request_ref: RequestRefV1


__all__ = [
    "CANDIDATE_VERSION",
    "DATA25_OWNER",
    "AsyncJobChildEnvelopeV1",
    "AsyncJobChildViewV1",
    "AsyncJobEnvelopeV1",
    "AsyncJobViewV1",
    "CollaborationErrorV1",
    "CreateAiJobCommandV1",
    "ErrorBodyV1",
    "FieldErrorV1",
    "JobCompletionClaimV1",
    "JobFailureV1",
    "JobProgressV1",
    "JobStatusMetaV1",
    "RequestRefV1",
    "ResultRefV1",
]
