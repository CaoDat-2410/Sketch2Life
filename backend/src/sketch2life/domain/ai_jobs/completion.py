"""Pure completion-claim identity, fingerprint and disposition guards (B22.3 candidate)."""

from __future__ import annotations

import json
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256

from sketch2life.domain.ai_jobs.model import AiJob, JobState, ResultDisposition


class OutcomeKind(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"


class Moderation(StrEnum):
    PASSED = "passed"
    UNSAFE = "unsafe"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True, slots=True)
class OutputRef:
    artifact_ref: str
    sha256: str


@dataclass(frozen=True, slots=True)
class CompletionClaim:
    """Worker completion candidate; identity is ``(job_id, attempt_id)``."""

    job_id: str
    attempt_id: str
    expected_request_revision: int
    input_hash: str
    context_revision: int
    kind: OutcomeKind
    outputs: tuple[OutputRef, ...] = ()
    moderation: Moderation = Moderation.NOT_APPLICABLE
    failure_code: str | None = None
    retryable: bool = False
    diagnostic: str | None = None

    @property
    def identity(self) -> tuple[str, str]:
        return (self.job_id, self.attempt_id)

    def fingerprint(self) -> str:
        """Normalised outcome hash; diagnostics are excluded (redacted, not semantic)."""

        return canonical_sha256(
            {
                "kind": str(self.kind),
                "outputs": sorted([o.artifact_ref, o.sha256] for o in self.outputs),
                "moderation": str(self.moderation),
                "failure_code": self.failure_code,
                "retryable": self.retryable,
                "expected_request_revision": self.expected_request_revision,
                "input_hash": self.input_hash,
                "context_revision": self.context_revision,
            }
        )


class PreconditionVerdict(StrEnum):
    """Result of guards that do not need live eligibility (pure, ordered)."""

    PROCEED = "proceed"
    JOB_CANCELLED = "JOB_CANCELLED"
    JOB_TERMINAL = "JOB_TERMINAL"
    ATTEMPT_SUPERSEDED = "ATTEMPT_SUPERSEDED"
    INVALID_STATE = "INVALID_STATE"
    INPUT_MISMATCH = "INPUT_MISMATCH"


VERDICT_DISPOSITION: Mapping[PreconditionVerdict, ResultDisposition] = {
    PreconditionVerdict.JOB_CANCELLED: ResultDisposition.REJECTED,
    PreconditionVerdict.JOB_TERMINAL: ResultDisposition.STALE,
    PreconditionVerdict.ATTEMPT_SUPERSEDED: ResultDisposition.STALE,
    PreconditionVerdict.INVALID_STATE: ResultDisposition.REJECTED,
    PreconditionVerdict.INPUT_MISMATCH: ResultDisposition.REJECTED,
}


def check_completion_preconditions(job: AiJob, claim: CompletionClaim) -> PreconditionVerdict:
    """Ordered guards; a non-PROCEED verdict leaves the job unchanged."""

    if claim.job_id != job.job_id:
        raise ValueError("claim does not belong to this job")
    if job.state is JobState.CANCELLED:
        return PreconditionVerdict.JOB_CANCELLED
    if job.is_terminal:
        return PreconditionVerdict.JOB_TERMINAL
    if claim.attempt_id != job.active_attempt.attempt_id:
        return PreconditionVerdict.ATTEMPT_SUPERSEDED
    if job.state is not JobState.RUNNING:
        return PreconditionVerdict.INVALID_STATE
    pinned = job.active_attempt.request_ref
    if (
        claim.expected_request_revision != pinned.request_revision
        or claim.input_hash != pinned.input_hash
        or claim.context_revision != pinned.context_revision
    ):
        return PreconditionVerdict.INPUT_MISMATCH
    return PreconditionVerdict.PROCEED


def canonical_json(value: object) -> str:
    return json.dumps(
        _normalise(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=_non_json,
    )


def _non_json(value: object) -> str:
    """Malformed worker input must still fingerprint deterministically instead of raising."""

    return f"<{type(value).__name__}>{value!r}"


def canonical_sha256(value: object) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _normalise(value: object) -> object:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, Mapping):
        return {str(k): _normalise(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_normalise(v) for v in value]
    return value


__all__ = [
    "VERDICT_DISPOSITION",
    "CompletionClaim",
    "Moderation",
    "OutcomeKind",
    "OutputRef",
    "PreconditionVerdict",
    "canonical_json",
    "canonical_sha256",
    "check_completion_preconditions",
]
