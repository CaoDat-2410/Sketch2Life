"""BE2-01 ports: job repository/unit of work, context/authorization, queue, clock,
ids, artifacts, audit, worker capability, provider and provider-copy lifecycle.

Phase A ships deterministic fakes. Phase B batch B3 (plan revision 3 §5, Δ1–Δ5) adds owner
fences on decisions, the unit-of-work fence hold, the canonical semantic key and typed
unique conflicts; the SQL adapter lives in ``infrastructure/ai_jobs/sql``. Batch B5 adds the
attempt-bound worker capability (Δ8), deterministic audit/quarantine side-effect intents with
leased delivery (Δ9/Δ15) and atomic cancellation notices (Δ10).
"""

from __future__ import annotations

import unicodedata
from collections.abc import Mapping
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Protocol

from sketch2life.domain.ai_jobs.completion import CompletionClaim, canonical_sha256
from sketch2life.domain.ai_jobs.model import AiJob, JobScope, RequestRef, ResultDisposition
from sketch2life.domain.ai_jobs.provider_copy import ProviderCopy, PurgeReceipt

OWNER_FENCE_CONTRACT = "OwnerFenceV1/0.1-candidate"


class JobRevisionConflict(ValueError):
    """CAS rejected a write because the stored job revision moved."""


class UniqueConflict(Exception):
    """A plain insert hit an existing key (Δ5). The whole unit of work must roll back before
    the caller re-reads the committed winner in a fresh transaction."""

    def __init__(self, kind: str) -> None:
        super().__init__(kind)
        self.kind = kind


@dataclass(frozen=True, slots=True)
class OwnerFence:
    """Owner decision version (Δ1): the owner bumps ``epoch`` with every decision change."""

    fence_scope: str
    epoch: int


@dataclass(frozen=True, slots=True)
class FenceResult:
    """Outcome of holding fences on the unit-of-work connection (Δ2)."""

    current: bool
    stale: tuple[OwnerFence, ...] = ()


class PrincipalRole(StrEnum):
    TEACHER = "teacher"
    ADMIN = "admin"
    DEVICE = "device"


@dataclass(frozen=True, slots=True)
class Principal:
    """Verified principal supplied by the owning identity port (P2), never by payload."""

    principal_id: str
    organization_id: str
    role: PrincipalRole


class AuthorizationAction(StrEnum):
    CREATE_JOB = "create_job"
    READ_JOB = "read_job"
    CANCEL_JOB = "cancel_job"


@dataclass(frozen=True, slots=True)
class AuthorizationDecision:
    """``fence`` is the grant version (Δ1); a missing fence is never treated as current."""

    allowed: bool
    reason_code: str | None = None
    fence: OwnerFence | None = None


@dataclass(frozen=True, slots=True)
class EligibilityDecision:
    """Current purpose/consent/session/recall/source/kill-switch/budget decision plus the
    owner fence version it was decided at (Δ1)."""

    eligible: bool
    reason_code: str | None
    current_context_revision: int
    fence: OwnerFence | None = None


@dataclass(frozen=True, slots=True)
class CommandScopeKey:
    organization_id: str
    principal_id: str
    contract_name: str
    target_id: str
    idempotency_key: str


@dataclass(frozen=True, slots=True)
class CommandReceipt:
    scope_key: CommandScopeKey
    fingerprint: str
    job_id: str
    outcome: str
    job_revision_at_commit: int
    recorded_at: datetime


@dataclass(frozen=True, slots=True)
class SemanticRequestKey:
    """Business dedup identity: pinned request plus its immutable authorized scope."""

    organization_id: str
    job_type: str
    request_id: str
    request_revision: int
    input_hash: str
    context_revision: int
    target_id: str
    purpose_code: str
    session_id: str | None
    subject_refs: tuple[str, ...]

    def sha256(self) -> str:
        """Canonical semantic identity (Δ4): NFC strings, explicit ``null`` for a missing
        session, subject refs sorted after normalisation with duplicates kept."""

        def nfc(value: str) -> str:
            return unicodedata.normalize("NFC", value)

        return canonical_sha256(
            {
                "organization_id": nfc(self.organization_id),
                "job_type": nfc(self.job_type),
                "request_id": nfc(self.request_id),
                "request_revision": self.request_revision,
                "input_hash": nfc(self.input_hash),
                "context_revision": self.context_revision,
                "target_id": nfc(self.target_id),
                "purpose_code": nfc(self.purpose_code),
                "session_id": None if self.session_id is None else nfc(self.session_id),
                "subject_refs": sorted(nfc(ref) for ref in self.subject_refs),
            }
        )


@dataclass(frozen=True, slots=True)
class CompletionReceipt:
    receipt_id: str
    job_id: str
    attempt_id: str
    fingerprint: str
    disposition: ResultDisposition
    reason_code: str | None
    job_revision_after: int
    recorded_at: datetime
    authoritative: bool = True


@dataclass(frozen=True, slots=True)
class DispatchMessage:
    """Minimal purpose-scoped payload; no adult token or provider credential."""

    message_id: str
    job_id: str
    attempt_id: str
    attempt_number: int
    job_type: str
    request_ref: RequestRef


@dataclass(frozen=True, slots=True)
class WorkerDispatchEnvelope:
    """Transient broker payload (Δ14): the dispatch message plus a capability minted right
    before publish. Never persisted; outbox rows, receipts, audit and logs stay token-free."""

    message: DispatchMessage
    capability: str = field(repr=False)


@dataclass(frozen=True, slots=True)
class OutboxLease:
    """Lease on one pending outbox row (Δ6). Only the current owner+generation may mark or
    release it; a stale holder's mark/release is a no-op."""

    message_id: str
    owner: str
    generation: int


@dataclass(frozen=True, slots=True)
class ClaimedDispatch:
    message: DispatchMessage
    lease: OutboxLease


@dataclass(frozen=True, slots=True)
class SweepCursor:
    """Keyset position inside one sweep invocation (Δ11): the row's sort time and its unique
    tie-break id. Pages continue strictly after it; nothing is persisted between sweeps."""

    at: datetime
    key: str


@dataclass(frozen=True, slots=True)
class AttemptDispatch:
    """Dispatch bookkeeping of one attempt (Δ7): last fenced publish time and publish count."""

    job_id: str
    attempt_id: str
    job_revision: int
    dispatched_at: datetime | None
    dispatch_count: int

    @property
    def cursor(self) -> SweepCursor:
        """Position in the ``queued_dispatched_not_started`` order (dispatched_at, attempt_id)."""

        if self.dispatched_at is None:
            raise ValueError("an unpublished attempt has no sweep position")
        return SweepCursor(self.dispatched_at, self.attempt_id)


@dataclass(frozen=True, slots=True)
class DueJob:
    """Row of the overdue-running and due-retry sweeps: job, active attempt number and the
    time the query orders by (attempt ``started_at`` resp. job ``retry_not_before``)."""

    job_id: str
    attempt_number: int
    due_at: datetime

    @property
    def cursor(self) -> SweepCursor:
        return SweepCursor(self.due_at, self.job_id)


@dataclass(frozen=True, slots=True)
class CancellationNotice:
    """Owner-port notice (consent revoke, session end, recall, source expiry, kill switch)."""

    notice_id: str
    organization_id: str
    reason_code: str
    session_id: str | None = None
    job_type: str | None = None
    subject_ref: str | None = None


@dataclass(frozen=True, slots=True)
class ArtifactDescriptor:
    """Artifact metadata from the owning artifact port, including producer lineage."""

    artifact_ref: str
    sha256: str
    organization_id: str
    producer_job_id: str | None = None
    producer_attempt_id: str | None = None
    quarantine_reason: str | None = None
    fence: OwnerFence | None = None


@dataclass(frozen=True, slots=True)
class AuditEvent:
    """Audit record. ``event_id`` is deterministic (Δ9): every delivery of the same intent
    carries the same value, so the sink deduplicates redeliveries."""

    event_type: str
    organization_id: str
    job_id: str | None
    correlation_id: str | None
    reason_code: str | None = None
    details: Mapping[str, str] = field(default_factory=dict)
    event_id: str = ""


@dataclass(frozen=True, slots=True)
class QuarantineIntent:
    """Quarantine of owned outputs (Δ15). ``event_id`` is computed once when the intent is
    written in the committing transaction; every redelivery sends exactly that value."""

    event_id: str
    organization_id: str
    job_id: str
    attempt_id: str
    artifact_refs: tuple[str, ...]
    reason_code: str


SideEffect = AuditEvent | QuarantineIntent


@dataclass(frozen=True, slots=True)
class ClaimedSideEffect:
    """A leased audit/quarantine outbox row (Δ9/Δ15); mark/release need the same lease.
    ``cursor`` is the row's position in the claim order (B5-R01 keyset traversal)."""

    effect: SideEffect
    lease: OutboxLease
    cursor: SweepCursor


@dataclass(frozen=True, slots=True)
class RecordedNotice:
    """Completed cancellation notice (Δ10): written only after every match was cancelled."""

    notice_id: str
    organization_id: str
    reason_code: str
    applied_count: int
    recorded_at: datetime


@dataclass(frozen=True, slots=True)
class VerifiedCapability:
    """Typed result of a successful worker capability verification (Δ8)."""

    job_id: str
    attempt_id: str
    issued_at: datetime
    expires_at: datetime
    key_id: str


class AiJobUnitOfWork(Protocol):
    """One READ COMMITTED transaction. ``insert_job``/``put_*``/``add_*`` raise
    ``UniqueConflict`` on an existing key; ``cas_job`` raises ``JobRevisionConflict``."""

    def get_job(self, job_id: str, *, for_update: bool = False) -> AiJob | None: ...

    def insert_job(self, job: AiJob) -> None: ...

    def cas_job(self, *, expected_revision: int, job: AiJob) -> None: ...

    def list_jobs(self) -> tuple[AiJob, ...]: ...

    def get_command_receipt(self, key: CommandScopeKey) -> CommandReceipt | None: ...

    def put_command_receipt(self, receipt: CommandReceipt) -> None: ...

    def find_semantic(self, key: SemanticRequestKey) -> str | None: ...

    def put_semantic(self, key: SemanticRequestKey, job_id: str) -> None: ...

    def get_completion_receipt(self, job_id: str, attempt_id: str) -> CompletionReceipt | None: ...

    def put_completion_receipt(self, receipt: CompletionReceipt) -> None: ...

    def hold_owner_fences(self, fences: tuple[OwnerFence, ...]) -> FenceResult:
        """Hold owner fences on this unit of work's connection until commit (Δ2)."""
        ...

    def add_audit_intent(self, event_id: str, event: AuditEvent) -> None:
        """Durable audit intent committed with the mutation it describes (Δ5, Δ9)."""
        ...

    def add_quarantine_intent(self, intent: QuarantineIntent) -> None:
        """Durable quarantine intent committed with the decision that requires it (Δ15)."""
        ...

    def side_effect_recorded(self, event_id: str) -> bool:
        """An audit/quarantine intent with this event id is already durable (Δ9 dedup)."""
        ...

    def pending_side_effects_count(self) -> int:
        """Count undelivered audit/quarantine rows, including leased rows. Captured once as
        the finite row budget of one delivery invocation; dispatch rows are excluded."""
        ...

    def claim_side_effects(
        self,
        owner: str,
        now: datetime,
        lease: timedelta,
        limit: int,
        after: SweepCursor | None = None,
    ) -> tuple[ClaimedSideEffect, ...]:
        """Lease up to ``limit`` undelivered audit/quarantine rows whose lease is free or
        expired, in a stable order strictly after ``after`` when given; each claim increments
        the row's lease generation (Δ6 fencing, Δ9, B5-R01)."""
        ...

    def mark_side_effect(self, lease: OutboxLease, now: datetime) -> bool:
        """Mark a delivered side effect; a stale holder's mark is a no-op. Never touches the
        attempt dispatch bookkeeping."""
        ...

    def add_outbox(self, message: DispatchMessage, *, now: datetime) -> None:
        """Pending dispatch row, available from ``now`` (service clock)."""
        ...

    def claim_outbox(
        self, owner: str, now: datetime, lease: timedelta, limit: int
    ) -> tuple[ClaimedDispatch, ...]:
        """Lease up to ``limit`` pending, unleased-or-expired dispatch rows; each claim
        increments the row's lease generation (Δ6)."""
        ...

    def lease_current(self, lease: OutboxLease) -> bool: ...

    def ack_dispatch(self, lease: OutboxLease, now: datetime) -> bool:
        """Fenced acknowledgement bundle: mark delivered and set the attempt's
        ``dispatched_at``/``dispatch_count`` together, only for the current pending lease."""
        ...

    def release_outbox(self, lease: OutboxLease, error_code: str) -> bool:
        """Current holder gives the lease back; the row stays pending."""
        ...

    def dispose_outbox(self, lease: OutboxLease, reason_code: str) -> bool:
        """Current holder settles a row that must not be published (stale/settled attempt)."""
        ...

    def attempt_dispatch(self, attempt_id: str) -> AttemptDispatch | None: ...

    def has_pending_dispatch(self, attempt_id: str) -> bool: ...

    def queued_dispatched_not_started(
        self,
        now: datetime,
        start_timeout: timedelta,
        limit: int,
        after: SweepCursor | None = None,
    ) -> tuple[AttemptDispatch, ...]:
        """Active queued attempts published at least ``start_timeout`` ago, never durably
        started, with no pending dispatch row (Δ7/Δ11). Ordered by (dispatched_at, attempt_id),
        strictly after ``after`` when given."""
        ...

    def overdue_running(
        self, now: datetime, limit: int, after: SweepCursor | None = None
    ) -> tuple[DueJob, ...]:
        """Running jobs whose active attempt exceeded its policy attempt timeout (Δ11).
        Ordered by (started_at, job_id), strictly after ``after`` when given."""
        ...

    def due_retries(
        self, now: datetime, limit: int, after: SweepCursor | None = None
    ) -> tuple[DueJob, ...]:
        """failed_retryable jobs due by ``now`` (Δ11). Ordered by (retry_not_before, job_id),
        strictly after ``after`` when given."""
        ...

    def notice_seen(self, notice_id: str) -> bool: ...

    def jobs_for_notice(self, notice: CancellationNotice) -> tuple[AiJob, ...]:
        """Every non-terminal job of the notice's organization matching its session, job type
        or subject, locked ``FOR UPDATE`` in job id order (Δ10). No limit, no paging."""
        ...

    def record_notice(
        self, notice: CancellationNotice, *, applied_count: int, now: datetime
    ) -> None:
        """Record the notice ``COMPLETE`` with its applied count; ``UniqueConflict`` if it is
        already recorded (Δ10)."""
        ...


class AiJobRepository(Protocol):
    def transaction(self) -> AbstractContextManager[AiJobUnitOfWork]: ...


class OwnerFencePort(Protocol):
    """Versioned owner fence read (D7/Q8). The owner implementation reads its fence rows
    ``FOR SHARE`` on the caller's connection and reports epochs that moved; a fence it does
    not know is stale, never current. BE2 never writes owner rows."""

    contract_version: str

    def hold(self, fences: tuple[OwnerFence, ...]) -> FenceResult: ...


class AuthorizationPort(Protocol):
    def decide(
        self, principal: Principal, action: AuthorizationAction, scope: JobScope
    ) -> AuthorizationDecision: ...


class EligibilityPort(Protocol):
    def check(self, *, scope: JobScope, request_ref: RequestRef, job_type: str) -> (
        EligibilityDecision
    ): ...


class WorkerCapabilityVerifier(Protocol):
    """Δ8: returns the typed claim of a well-formed, untampered, known-key, unexpired token,
    else ``None``. The caller compares both ids with the request."""

    def verify(self, capability: str) -> VerifiedCapability | None: ...


class WorkerCapabilityIssuer(Protocol):
    """P3 issuer (Δ14), called by the dispatcher right before enqueue, outside any SQL write.
    The token is bound to ``(job_id, attempt_id, issued_at, expires_at, key_id)`` (Δ8)."""

    def issue(self, job_id: str, attempt_id: str, now: datetime) -> str: ...


class ClockPort(Protocol):
    def now(self) -> datetime: ...


class IdGeneratorPort(Protocol):
    def new_id(self, prefix: str) -> str: ...


class ArtifactPort(Protocol):
    def describe(self, artifact_ref: str) -> ArtifactDescriptor | None: ...

    def quarantine(self, intent: QuarantineIntent) -> None:
        """Apply the intent once; a repeated ``event_id`` is a no-op at the sink (Δ15)."""
        ...


class AuditPort(Protocol):
    def record(self, event: AuditEvent) -> None:
        """At-least-once delivery; the sink deduplicates by ``event.event_id`` (Δ9)."""
        ...


class DispatchQueuePort(Protocol):
    """Broker adapter. Raises the application ``QueueUnavailable`` when the broker is down."""

    def enqueue(self, envelope: WorkerDispatchEnvelope) -> None: ...


class AiProviderPort(Protocol):
    """Provider adapter boundary used by workers; adapters build ``CompletionClaim``."""

    def run(self, message: DispatchMessage) -> CompletionClaim: ...


class ProviderCopyRegistryPort(Protocol):
    def register(self, copy: ProviderCopy) -> ProviderCopy: ...

    def get(self, copy_id: str) -> ProviderCopy | None: ...

    def save(self, copy: ProviderCopy) -> None: ...

    def list_scope(self, organization_id: str, scope_ref: str) -> tuple[ProviderCopy, ...]: ...

    def mark_scope_purging(self, organization_id: str, scope_ref: str) -> None: ...

    def is_scope_purging(self, organization_id: str, scope_ref: str) -> bool: ...

    def scope_lock(
        self, organization_id: str, scope_ref: str
    ) -> AbstractContextManager[None]: ...

    def get_purge_receipt(self, idempotency_key: str) -> PurgeReceipt | None: ...

    def put_purge_receipt(self, idempotency_key: str, receipt: PurgeReceipt) -> PurgeReceipt: ...


class ProviderCopyAdapterPort(Protocol):
    def request_cancel(self, copy: ProviderCopy) -> None: ...

    def request_purge(self, copy: ProviderCopy) -> PurgeReceipt: ...


__all__ = [
    "OWNER_FENCE_CONTRACT",
    "AiJobRepository",
    "AiJobUnitOfWork",
    "AiProviderPort",
    "ArtifactDescriptor",
    "AttemptDispatch",
    "ArtifactPort",
    "AuditEvent",
    "AuditPort",
    "AuthorizationAction",
    "AuthorizationDecision",
    "AuthorizationPort",
    "CancellationNotice",
    "ClaimedDispatch",
    "ClaimedSideEffect",
    "ClockPort",
    "CommandReceipt",
    "CommandScopeKey",
    "CompletionReceipt",
    "DispatchMessage",
    "DispatchQueuePort",
    "DueJob",
    "EligibilityDecision",
    "EligibilityPort",
    "FenceResult",
    "IdGeneratorPort",
    "JobRevisionConflict",
    "OutboxLease",
    "OwnerFence",
    "OwnerFencePort",
    "Principal",
    "PrincipalRole",
    "QuarantineIntent",
    "RecordedNotice",
    "ProviderCopyAdapterPort",
    "ProviderCopyRegistryPort",
    "SemanticRequestKey",
    "SideEffect",
    "SweepCursor",
    "UniqueConflict",
    "VerifiedCapability",
    "WorkerCapabilityIssuer",
    "WorkerCapabilityVerifier",
    "WorkerDispatchEnvelope",
]
