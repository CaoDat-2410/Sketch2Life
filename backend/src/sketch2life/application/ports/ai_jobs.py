"""BE2-01 ports: job repository/unit of work, context/authorization, queue, clock,
ids, artifacts, audit, worker capability, provider and provider-copy lifecycle.

Phase A ships deterministic fakes. Phase B batch B3 (plan revision 3 §5, Δ1–Δ5) adds owner
fences on decisions, the unit-of-work fence hold, the canonical semantic key and typed
unique conflicts; the SQL adapter lives in ``infrastructure/ai_jobs/sql``.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Mapping
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from datetime import datetime
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
    event_type: str
    organization_id: str
    job_id: str | None
    correlation_id: str | None
    reason_code: str | None = None
    details: Mapping[str, str] = field(default_factory=dict)


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
        """Durable audit intent committed with the mutation it describes (Δ5 candidate)."""
        ...

    def add_outbox(self, message: DispatchMessage) -> None: ...

    def pending_outbox(self) -> tuple[DispatchMessage, ...]: ...

    def mark_dispatched(self, message_id: str) -> None: ...

    def notice_seen(self, notice_id: str) -> bool: ...

    def record_notice(self, notice_id: str) -> None: ...


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
    def verify(self, capability: str, job_id: str) -> bool: ...


class ClockPort(Protocol):
    def now(self) -> datetime: ...


class IdGeneratorPort(Protocol):
    def new_id(self, prefix: str) -> str: ...


class ArtifactPort(Protocol):
    def describe(self, artifact_ref: str) -> ArtifactDescriptor | None: ...

    def quarantine(self, artifact_refs: tuple[str, ...], reason_code: str) -> None: ...


class AuditPort(Protocol):
    def record(self, event: AuditEvent) -> None: ...


class DispatchQueuePort(Protocol):
    def enqueue(self, message: DispatchMessage) -> None: ...


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
    "ArtifactPort",
    "AuditEvent",
    "AuditPort",
    "AuthorizationAction",
    "AuthorizationDecision",
    "AuthorizationPort",
    "CancellationNotice",
    "ClockPort",
    "CommandReceipt",
    "CommandScopeKey",
    "CompletionReceipt",
    "DispatchMessage",
    "DispatchQueuePort",
    "EligibilityDecision",
    "EligibilityPort",
    "FenceResult",
    "IdGeneratorPort",
    "JobRevisionConflict",
    "OwnerFence",
    "OwnerFencePort",
    "Principal",
    "PrincipalRole",
    "ProviderCopyAdapterPort",
    "ProviderCopyRegistryPort",
    "SemanticRequestKey",
    "UniqueConflict",
    "WorkerCapabilityVerifier",
]
