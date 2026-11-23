"""Port of the inline (already finished) AI job record (FEAT-066 goal v3, T-3b, TD-15).

A producer whose work is done inside the request (the occurrence document extraction, SRS l.1653)
still answers with a job resource (SRS l.779, l.806) so a client has one polling contract. The job
row is written terminal in the producer's own transaction: ``created``, ``started`` and
``succeeded`` at one instant, one attempt, one result ref. It is never queued, never dispatched and
never swept, so the recorder writes no outbox row, no semantic request and no command receipt.
``succeeded`` means "extraction finished", not "plan approved" (UC-04: review comes later).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class InlineSucceededJob:
    """Everything a terminal inline job needs; ids are chosen by the producer."""

    job_id: str
    attempt_id: str
    correlation_id: str
    job_type: str
    organization_id: str
    purpose_code: str
    target_id: str
    request_id: str
    request_revision: int
    input_hash: str
    result_artifact_ref: str
    result_sha256: str
    result_provenance: str
    policy_id: str
    attempt_timeout_ms: int
    at: datetime


class InlineJobRecorder(Protocol):
    def record_succeeded(self, job: InlineSucceededJob) -> None:
        """Insert the finished job on the caller's open transaction; never commits."""
        ...


__all__ = ["InlineJobRecorder", "InlineSucceededJob"]
