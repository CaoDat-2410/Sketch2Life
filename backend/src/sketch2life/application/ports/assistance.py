"""BE2-03 application ports (A1 offline component; owner adapters are ASSUMED_CONTRACT).

BE1 owner facts (canvas/session/roster/turn/region/consent/age), source/admission, the
BE2-14 policy proposal (D10), BE2-01 job creation/history and BE2-02 analysis reads are all
consumed through these ports. Nothing here reads another module's storage directly.
"""

from __future__ import annotations

from collections.abc import Mapping
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from sketch2life.application.ports.ai_jobs import Principal
from sketch2life.domain.assistance import (
    AssistanceRequest,
    CacheHit,
    CheckpointRef,
    Contributor,
    MemberFact,
    PolicySnapshot,
)
from sketch2life.domain.vision_analysis import AdmissionReceipt, SourceSnapshot


class AssistanceUniqueConflict(Exception):
    """A uniqueness guard lost a race inside the unit of work."""


class AssistanceRevisionConflict(Exception):
    """Record-version CAS failed: another writer committed first."""


# ------------------------------------------------------------------------ records
@dataclass(frozen=True, slots=True)
class ReceiptKey:
    organization_id: str
    principal_id: str
    contract_name: str
    target_id: str
    idempotency_key: str


class ReceiptOutcome(StrEnum):
    CREATED = "created"
    DEDUPLICATED = "deduplicated"
    CACHE_HIT = "cache_hit"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class CommandReceipt:
    """Accepted-command receipt; ``snapshot`` is the request exactly as committed so that a
    replay returns the original body even after later transitions."""

    key: ReceiptKey
    fingerprint: str
    outcome: ReceiptOutcome
    snapshot: AssistanceRequest
    recorded_at: datetime


@dataclass(frozen=True, slots=True)
class AssistanceEvent:
    event_id: str
    event_type: str
    organization_id: str
    assistance_id: str | None
    request_revision: int | None
    reason: str | None
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class SketchIntent:
    """D8: simulated hand-off to the absent BE2-04 producer; never a generation claim."""

    intent_id: str
    assistance_id: str
    request_revision: int
    analysis_id: str
    analysis_revision: int
    status: str = "SIMULATED_NO_PRODUCER"


class AssistanceUnitOfWork(Protocol):
    def get(self, assistance_id: str) -> AssistanceRequest | None: ...

    def insert(self, request: AssistanceRequest) -> None: ...

    def cas(self, *, expected_record_version: int, request: AssistanceRequest) -> None: ...

    def find_active_semantic(self, organization_id: str, identity: str) -> str | None: ...

    def active_by_operation_target(
        self, organization_id: str, key: str
    ) -> tuple[AssistanceRequest, ...]: ...

    def latest_counted(self, organization_id: str, debounce_key: str) -> datetime | None: ...

    def count_reserved(
        self, organization_id: str, session_id: str, target_key: str | None
    ) -> int: ...

    def get_receipt(self, key: ReceiptKey) -> CommandReceipt | None: ...

    def put_receipt(self, receipt: CommandReceipt) -> None: ...

    def find_cache(self, organization_id: str, identity: str) -> CacheHit | None: ...

    def put_cache(self, organization_id: str, identity: str, hit: CacheHit) -> None: ...

    def add_event(self, event: AssistanceEvent) -> None: ...

    def add_sketch_intent(self, intent: SketchIntent) -> None: ...

    def notice_seen(self, notice_id: str) -> bool: ...

    def record_notice(self, notice_id: str) -> None: ...

    def list_requests(self, organization_id: str) -> tuple[AssistanceRequest, ...]: ...

    def publish_request_fence(self, organization_id: str) -> None:
        """Stage the eligibility-fence bump; it is published together with this commit."""

    def decision_epoch(self, organization_id: str) -> tuple[int, ...]:
        """Committed decision token covering owner-fact, request and analysis (Vision)
        commits. A decision read at token ``t`` may commit only while it is still ``t``
        (A1-CR03, CR03-F2)."""


class AssistanceRepository(Protocol):
    def transaction(self) -> AbstractContextManager[AssistanceUnitOfWork]: ...


# ----------------------------------------------------------------------- owner facts
@dataclass(frozen=True, slots=True)
class CanvasFacts:
    organization_id: str
    class_id: str
    session_id: str
    canvas_id: str
    mode: str  # "personal" | "collaborative"
    group_id: str | None
    personal_participant_id: str | None
    session_active: bool
    document_epoch: int
    context_revision: int
    region_policy_revision: int
    regions: Mapping[str, frozenset[str] | None]  # None = unrestricted region
    age_policy_ref: str


@dataclass(frozen=True, slots=True)
class GroupRoster:
    group_id: str
    members: tuple[str, ...]
    revision: int


class AssistanceOwnerPort(Protocol):
    """BE1 H-CLASS-CONSENT / H-SESSION-CONTROL / H-CANVAS-SYNC facts (ASSUMED_CONTRACT)."""

    def canvas(self, organization_id: str, canvas_id: str) -> CanvasFacts | None: ...

    def roster(self, session_id: str, group_id: str) -> GroupRoster | None: ...

    def members(
        self, organization_id: str, participant_ids: tuple[str, ...], purpose_code: str
    ) -> tuple[MemberFact, ...]: ...

    def current_turn(self, canvas_id: str) -> Contributor | None: ...


class AuthorityReason(StrEnum):
    NOT_IN_SCOPE = "NOT_IN_SCOPE"
    GRANT_REVOKED = "GRANT_REVOKED"
    TURN_CLOSED = "TURN_CLOSED"
    ROLE_NOT_PERMITTED = "ROLE_NOT_PERMITTED"


@dataclass(frozen=True, slots=True)
class AssistanceAuthority:
    """For a device, ``contributor`` is the server-bound participant and open turn."""

    allowed: bool
    reason: AuthorityReason | None = None
    contributor: Contributor | None = None


class AssistanceAuthorityPort(Protocol):
    def decide(self, principal: Principal, canvas: CanvasFacts) -> AssistanceAuthority: ...

    def disclose(self, principal: Principal, request: AssistanceRequest) -> bool:
        """Current read/disclosure authority for one request (checked on every replay)."""


@dataclass(frozen=True, slots=True)
class ResolvedSource:
    snapshot: SourceSnapshot
    server_sequence: int
    admission: AdmissionReceipt | None


class AssistanceSourcePort(Protocol):
    def resolve(
        self, organization_id: str, canvas_id: str, ref: CheckpointRef
    ) -> ResolvedSource | None: ...


class AssistancePolicyPort(Protocol):
    """D10 consumer proposal to the BE2-14 owner; A1 binds a FIXTURE_ONLY adapter."""

    def current(self, organization_id: str, session_id: str) -> PolicySnapshot | None: ...


# ------------------------------------------------------------------- BE2-01 / BE2-02
@dataclass(frozen=True, slots=True)
class JobCreateRequest:
    principal: Principal
    idempotency_key: str
    job_type: str
    target_id: str
    purpose_code: str
    session_id: str
    subject_refs: tuple[str, ...]
    request_id: str
    request_revision: int
    input_hash: str
    context_revision: int
    correlation_id: str


class JobCreateKind(StrEnum):
    CREATED = "created"
    REFUSED = "refused"
    RETRY = "retry"


@dataclass(frozen=True, slots=True)
class JobCreateOutcome:
    kind: JobCreateKind
    job_id: str | None = None
    code: str | None = None


class AssistanceJobPort(Protocol):
    def create(self, request: JobCreateRequest) -> JobCreateOutcome: ...

    def cancel(self, principal: Principal, job_id: str, expected_job_revision: int) -> str: ...


@dataclass(frozen=True, slots=True)
class JobEvidence:
    """Trusted read of one BE2-01 job; ``any_attempt_started`` covers every attempt."""

    job_id: str
    state: str
    job_revision: int
    terminal: bool
    any_attempt_started: bool
    active_attempt_id: str
    request_revision: int


class AssistanceJobReader(Protocol):
    def evidence(
        self, organization_id: str, assistance_id: str, known_job_ids: tuple[str, ...]
    ) -> tuple[JobEvidence, ...] | None:
        """Every job for the request (known ids plus a target scan); ``None`` = unknown."""


@dataclass(frozen=True, slots=True)
class AnalysisOutcome:
    analysis_id: str
    analysis_revision: int
    accepted_status: str
    meaning_state: str
    assistance_id: str
    request_revision: int
    job_id: str
    attempt_id: str
    snapshot_ref: str
    checkpoint_id: str
    checkpoint_checksum: str
    render_sha256: str
    context_revision: int


class AnalysisOutcomePort(Protocol):
    """Authorized current BE2-02 reads through an injected scoped Teacher reader."""

    def for_attempt(
        self, organization_id: str, job_id: str, attempt_id: str
    ) -> AnalysisOutcome | None: ...

    def current(self, organization_id: str, analysis_id: str) -> AnalysisOutcome | None: ...


class SketchStagePort(Protocol):
    def request_sketch(self, intent: SketchIntent) -> None: ...


__all__ = [
    "AnalysisOutcome",
    "AnalysisOutcomePort",
    "AssistanceAuthority",
    "AssistanceAuthorityPort",
    "AssistanceEvent",
    "AssistanceJobPort",
    "AssistanceJobReader",
    "AssistanceOwnerPort",
    "AssistancePolicyPort",
    "AssistanceRepository",
    "AssistanceRevisionConflict",
    "AssistanceSourcePort",
    "AssistanceUniqueConflict",
    "AssistanceUnitOfWork",
    "AuthorityReason",
    "CanvasFacts",
    "CommandReceipt",
    "GroupRoster",
    "JobCreateKind",
    "JobCreateOutcome",
    "JobCreateRequest",
    "JobEvidence",
    "ReceiptKey",
    "ReceiptOutcome",
    "ResolvedSource",
    "SketchIntent",
    "SketchStagePort",
]
