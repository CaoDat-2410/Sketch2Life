"""Framework-free contracts and session state for the fixture-only runtime slice."""
from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


class RuntimeRejected(ValueError):
    pass


class SessionState(StrEnum):
    CREATED = "CREATED"
    MEDIA_RECAPTURE = "MEDIA_RECAPTURE"
    UNDERSTANDING_PROPOSED = "UNDERSTANDING_PROPOSED"
    GATE_A_PENDING = "GATE_A_PENDING"
    CONTEXT_REQUIRED = "CONTEXT_REQUIRED"
    CANDIDATES_READY = "CANDIDATES_READY"
    GATE_B_PENDING = "GATE_B_PENDING"
    EXPERIENCE_READY = "EXPERIENCE_READY"
    HANDOFF_READY = "HANDOFF_READY"
    FEEDBACK_RECORDED = "FEEDBACK_RECORDED"


@dataclass(frozen=True)
class ArtifactRef:
    artifact_id: str
    artifact_version: int
    kind: str
    sha256: str | None = None

    def __post_init__(self) -> None:
        if not self.artifact_id or not self.kind or self.artifact_version < 0:
            raise RuntimeRejected("ARTIFACT_REFERENCE_INVALID")
        if self.sha256 is not None and re.fullmatch(r"[a-f0-9]{64}", self.sha256) is None:
            raise RuntimeRejected("ARTIFACT_HASH_INVALID")


@dataclass(frozen=True)
class CommandEnvelope:
    command_id: str
    session_id: str
    expected_session_version: int
    actor_ref: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def validate(self) -> None:
        if not self.command_id or not self.session_id or not self.actor_ref:
            raise RuntimeRejected("COMMAND_ID_SESSION_ID_ACTOR_REQUIRED")
        if self.expected_session_version < 0:
            raise RuntimeRejected("EXPECTED_SESSION_VERSION_INVALID")
        if self.created_at.tzinfo is None:
            raise RuntimeRejected("COMMAND_TIMESTAMP_MUST_BE_TIMEZONE_AWARE")


@dataclass(frozen=True)
class GateAConfirmation:
    meaning_version: int
    confirmed_claim_ids: tuple[str, ...]
    correction: str | None = None

    def __post_init__(self) -> None:
        if self.meaning_version < 1 or not self.confirmed_claim_ids:
            raise RuntimeRejected("GATE_A_CONFIRMATION_INVALID")


@dataclass(frozen=True)
class GateBApproval:
    activity_id: str
    activity_version: int
    objective_id: str
    objective_version: int

    def __post_init__(self) -> None:
        if not self.activity_id or not self.objective_id or self.activity_version < 0 or self.objective_version < 0:
            raise RuntimeRejected("GATE_B_APPROVAL_INVALID")


@dataclass(frozen=True)
class SessionSnapshot:
    session_id: str
    state: SessionState
    version: int
    source_artifacts: tuple[ArtifactRef, ...] = ()
    raw_understanding: Mapping[str, Any] | None = None
    gate_a: GateAConfirmation | None = None
    p1_context: Mapping[str, Any] | None = None
    gate_b: GateBApproval | None = None
    experience_artifacts: tuple[ArtifactRef, ...] = ()
    handoff_completed: bool = False
    feedback: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class JobSnapshot:
    job_id: str
    session_id: str
    status: str
    session_version: int
    result_artifact: ArtifactRef | None = None
    error_code: str | None = None
