"""BE2-01 Phase A ports: job repository/unit of work, context/authorization, queue, clock,
ids, artifacts, audit, worker capability, provider and provider-copy lifecycle.

Phase A ships deterministic fakes only. Durable implementations (transactions, outbox,
broker) belong to Phase B and need their own approval.
"""

from __future__ import annotations

from collections.abc import Mapping
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from sketch2life.domain.ai_jobs.completion import CompletionClaim
from sketch2life.domain.ai_jobs.model import AiJob, JobScope, RequestRef, ResultDisposition
from sketch2life.domain.ai_jobs.provider_copy import ProviderCopy, PurgeReceipt


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
    allowed: bool
    reason_code: str | None = None


@dataclass(frozen=True, slots=True)
class EligibilityDecision:
    """Current purpose/consent/session/recall/source/kill-switch/budget decision."""

    eligible: bool
    reason_code: str | None
    current_context_revision: int


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


@dataclass(frozen=True, slots=True)
class AuditEvent:
    event_type: str
    organization_id: str
    job_id: str | None
    correlation_id: str | None
    reason_code: str | None = None
    details: Mapping[str, str] = field(default_factory=dict)


class AiJobUnitOfWork(Protocol):
    def get_job(self, job_id: str) -> AiJob | None: ...

    def insert_job(self, job: AiJob) -> None: ...

    def cas_job(self, *, expected_revision: int, job: AiJob) -> None: ...

    def list_jobs(self) -> tuple[AiJob, ...]: ...

    def get_command_receipt(self, key: CommandScopeKey) -> CommandReceipt | None: ...

    def put_command_receipt(self, receipt: CommandReceipt) -> None: ...

    def find_semantic(self, key: SemanticRequestKey) -> str | None: ...

    def put_semantic(self, key: SemanticRequestKey, job_id: str) -> None: ...

    def get_completion_receipt(self, job_id: str, attempt_id: str) -> CompletionReceipt | None: ...

    def put_completion_receipt(self, receipt: CompletionReceipt) -> None: ...

    def add_outbox(self, message: DispatchMessage) -> None: ...

    def pending_outbox(self) -> tuple[DispatchMessage, ...]: ...

    def mark_dispatched(self, message_id: str) -> None: ...

    def notice_seen(self, notice_id: str) -> bool: ...

    def record_notice(self, notice_id: str) -> None: ...


class AiJobRepository(Protocol):
    def transaction(self) -> AbstractContextManager[AiJobUnitOfWork]: ...


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
    "IdGeneratorPort",
    "Principal",
    "PrincipalRole",
    "ProviderCopyAdapterPort",
    "ProviderCopyRegistryPort",
    "SemanticRequestKey",
    "WorkerCapabilityVerifier",
]
