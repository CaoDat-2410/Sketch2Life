"""Deterministic BE2-01 fakes with fault injection (fixture use only).

These adapters simulate one authoritative transaction with a process-local lock. They are
not durable storage, not database isolation and must never be wired into the live app.
B3 parity (Δ12 subset): owner fences on decisions, fence hold, canonical semantic key,
typed ``UniqueConflict`` and durable audit intents. B4 parity: leased outbox claim with
owner+generation fencing, attempt dispatch bookkeeping, targeted sweep queries, transient
dispatch envelopes and a capability issuer.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from hashlib import sha256
from threading import RLock

from sketch2life.application.ports.ai_jobs import (
    ArtifactDescriptor,
    AttemptDispatch,
    AuditEvent,
    AuthorizationAction,
    AuthorizationDecision,
    ClaimedDispatch,
    CommandReceipt,
    CommandScopeKey,
    CompletionReceipt,
    DispatchMessage,
    DueJob,
    EligibilityDecision,
    FenceResult,
    JobRevisionConflict,
    OutboxLease,
    OwnerFence,
    Principal,
    SemanticRequestKey,
    SweepCursor,
    UniqueConflict,
    WorkerDispatchEnvelope,
)
from sketch2life.application.services.ai_jobs import AiJobService, QueueUnavailable
from sketch2life.domain.ai_jobs.completion import CompletionClaim, OutputRef
from sketch2life.domain.ai_jobs.model import (
    AiJob,
    JobScope,
    JobState,
    RequestRef,
    require_aware,
)
from sketch2life.domain.ai_jobs.provider_copy import (
    EvidenceKind,
    ProviderCopy,
    PurgeReceipt,
    ReceiptOutcome,
)

FIXTURE_MARKER = "FIXTURE_ONLY_NOT_DURABLE"


class FakeOwnerFences:
    """In-memory owner fence epochs shared by the fake owner ports and the fake store.
    Tests call ``bump`` to model an owner decision change whose notice is withheld."""

    def __init__(self) -> None:
        self.epochs: dict[str, int] = defaultdict(int)
        self.holds: list[FenceResult] = []

    def fence(self, scope: str) -> OwnerFence:
        return OwnerFence(scope, self.epochs[scope])

    def bump(self, scope: str) -> int:
        self.epochs[scope] += 1
        return self.epochs[scope]

    def hold(self, fences: tuple[OwnerFence, ...]) -> FenceResult:
        stale = tuple(f for f in fences if self.epochs[f.fence_scope] != f.epoch)
        result = FenceResult(not stale, stale)
        self.holds.append(result)
        return result


def eligibility_fence_scope(organization_id: str) -> str:
    return f"eligibility:{organization_id}"


def grant_fence_scope(organization_id: str, principal_id: str) -> str:
    return f"grant:{organization_id}:{principal_id}"


def artifact_fence_scope(artifact_ref: str) -> str:
    return f"artifact:{artifact_ref}"


class FakeClock:
    def __init__(self, start: datetime) -> None:
        require_aware(start, "start")
        self._now = start

    def now(self) -> datetime:
        return self._now

    def advance(self, *, milliseconds: int = 0, seconds: int = 0) -> datetime:
        self._now += timedelta(milliseconds=milliseconds, seconds=seconds)
        return self._now


class SequentialIds:
    def __init__(self) -> None:
        self._counters: dict[str, int] = defaultdict(int)
        self._lock = RLock()

    def new_id(self, prefix: str) -> str:
        with self._lock:
            self._counters[prefix] += 1
            return f"{prefix}_fx{self._counters[prefix]:04d}"


@dataclass
class _StoreState:
    jobs: dict[str, AiJob] = field(default_factory=dict)
    command_receipts: dict[CommandScopeKey, CommandReceipt] = field(default_factory=dict)
    semantic: dict[str, str] = field(default_factory=dict)
    completion_receipts: dict[tuple[str, str], CompletionReceipt] = field(default_factory=dict)
    outbox: dict[str, DispatchMessage] = field(default_factory=dict)
    notices: set[str] = field(default_factory=set)
    audit_intents: dict[str, AuditEvent] = field(default_factory=dict)
    # Pending dispatch rows only live in ``outbox``; these carry their lease/availability.
    available_at: dict[str, datetime] = field(default_factory=dict)
    generations: dict[str, int] = field(default_factory=dict)
    leases: dict[str, tuple[str, int, datetime]] = field(default_factory=dict)
    # attempt_id -> (dispatched_at, dispatch_count)
    attempt_dispatch: dict[str, tuple[datetime | None, int]] = field(default_factory=dict)

    def copy(self) -> _StoreState:
        return _StoreState(
            jobs=dict(self.jobs),
            command_receipts=dict(self.command_receipts),
            semantic=dict(self.semantic),
            completion_receipts=dict(self.completion_receipts),
            outbox=dict(self.outbox),
            notices=set(self.notices),
            audit_intents=dict(self.audit_intents),
            available_at=dict(self.available_at),
            generations=dict(self.generations),
            leases=dict(self.leases),
            attempt_dispatch=dict(self.attempt_dispatch),
        )


class _UnitOfWork:
    def __init__(self, state: _StoreState, fences: FakeOwnerFences) -> None:
        self.state = state
        self._fences = fences

    def get_job(self, job_id: str, *, for_update: bool = False) -> AiJob | None:
        return self.state.jobs.get(job_id)

    def insert_job(self, job: AiJob) -> None:
        if job.job_id in self.state.jobs:
            raise UniqueConflict("job")
        self.state.jobs[job.job_id] = job

    def cas_job(self, *, expected_revision: int, job: AiJob) -> None:
        current = self.state.jobs.get(job.job_id)
        if current is None or current.job_revision != expected_revision:
            raise JobRevisionConflict("job revision moved")
        if job.job_revision <= expected_revision:
            raise JobRevisionConflict("replacement must advance job_revision")
        self.state.jobs[job.job_id] = job

    def list_jobs(self) -> tuple[AiJob, ...]:
        return tuple(self.state.jobs[k] for k in sorted(self.state.jobs))

    def get_command_receipt(self, key: CommandScopeKey) -> CommandReceipt | None:
        return self.state.command_receipts.get(key)

    def put_command_receipt(self, receipt: CommandReceipt) -> None:
        if receipt.scope_key in self.state.command_receipts:
            raise UniqueConflict("command_receipt")
        self.state.command_receipts[receipt.scope_key] = receipt

    def find_semantic(self, key: SemanticRequestKey) -> str | None:
        return self.state.semantic.get(key.sha256())

    def put_semantic(self, key: SemanticRequestKey, job_id: str) -> None:
        digest = key.sha256()
        if digest in self.state.semantic:
            raise UniqueConflict("semantic_request")
        self.state.semantic[digest] = job_id

    def get_completion_receipt(self, job_id: str, attempt_id: str) -> CompletionReceipt | None:
        return self.state.completion_receipts.get((job_id, attempt_id))

    def put_completion_receipt(self, receipt: CompletionReceipt) -> None:
        identity = (receipt.job_id, receipt.attempt_id)
        if identity in self.state.completion_receipts:
            raise UniqueConflict("completion_receipt")
        self.state.completion_receipts[identity] = receipt

    def hold_owner_fences(self, fences: tuple[OwnerFence, ...]) -> FenceResult:
        return self._fences.hold(fences)

    def add_audit_intent(self, event_id: str, event: AuditEvent) -> None:
        if event_id in self.state.audit_intents:
            raise UniqueConflict("outbox")
        self.state.audit_intents[event_id] = event

    def add_outbox(self, message: DispatchMessage, *, now: datetime) -> None:
        if message.message_id in self.state.outbox:
            raise UniqueConflict("outbox")
        self.state.outbox[message.message_id] = message
        self.state.available_at[message.message_id] = now
        self.state.generations[message.message_id] = 0

    def claim_outbox(
        self, owner: str, now: datetime, lease: timedelta, limit: int
    ) -> tuple[ClaimedDispatch, ...]:
        claims: list[ClaimedDispatch] = []
        for message_id in sorted(self.state.outbox,
                                 key=lambda m: (self.state.available_at[m], m)):
            held = self.state.leases.get(message_id)
            if self.state.available_at[message_id] > now or (held and held[2] > now):
                continue
            generation = self.state.generations[message_id] + 1
            self.state.generations[message_id] = generation
            self.state.leases[message_id] = (owner, generation, now + lease)
            claims.append(ClaimedDispatch(self.state.outbox[message_id],
                                          OutboxLease(message_id, owner, generation)))
            if len(claims) == limit:
                break
        return tuple(claims)

    def lease_current(self, lease: OutboxLease) -> bool:
        held = self.state.leases.get(lease.message_id)
        return (
            lease.message_id in self.state.outbox
            and held is not None
            and (held[0], held[1]) == (lease.owner, lease.generation)
        )

    def ack_dispatch(self, lease: OutboxLease, now: datetime) -> bool:
        if not self.lease_current(lease):
            return False
        message = self._settle(lease.message_id)
        dispatched_at, count = self.state.attempt_dispatch.get(message.attempt_id, (None, 0))
        self.state.attempt_dispatch[message.attempt_id] = (now, count + 1)
        return True

    def release_outbox(self, lease: OutboxLease, error_code: str) -> bool:
        if not self.lease_current(lease):
            return False
        del self.state.leases[lease.message_id]
        return True

    def dispose_outbox(self, lease: OutboxLease, reason_code: str) -> bool:
        if not self.lease_current(lease):
            return False
        self._settle(lease.message_id)
        return True

    def attempt_dispatch(self, attempt_id: str) -> AttemptDispatch | None:
        for job in self.state.jobs.values():
            for attempt in job.attempts:
                if attempt.attempt_id == attempt_id:
                    dispatched_at, count = self.state.attempt_dispatch.get(attempt_id, (None, 0))
                    return AttemptDispatch(job.job_id, attempt_id, job.job_revision,
                                           dispatched_at, count)
        return None

    def has_pending_dispatch(self, attempt_id: str) -> bool:
        return any(m.attempt_id == attempt_id for m in self.state.outbox.values())

    def queued_dispatched_not_started(
        self,
        now: datetime,
        start_timeout: timedelta,
        limit: int,
        after: SweepCursor | None = None,
    ) -> tuple[AttemptDispatch, ...]:
        due: list[AttemptDispatch] = []
        for job in self.list_jobs():
            attempt = job.active_attempt
            dispatched_at, count = self.state.attempt_dispatch.get(attempt.attempt_id, (None, 0))
            if (
                job.state is JobState.QUEUED
                and attempt.started_at is None
                and attempt.finished_at is None
                and dispatched_at is not None
                and dispatched_at <= now - start_timeout
                and not self.has_pending_dispatch(attempt.attempt_id)
            ):
                due.append(AttemptDispatch(job.job_id, attempt.attempt_id, job.job_revision,
                                           dispatched_at, count))
        return _keyset_page(due, limit, after)

    def overdue_running(
        self, now: datetime, limit: int, after: SweepCursor | None = None
    ) -> tuple[DueJob, ...]:
        overdue = [
            DueJob(job.job_id, job.active_attempt.attempt_number, job.started_at)
            for job in self.list_jobs()
            if job.state is JobState.RUNNING
            and job.started_at is not None
            and now - job.started_at
            >= timedelta(milliseconds=job.retry_policy.attempt_timeout_ms)
        ]
        return _keyset_page(overdue, limit, after)

    def due_retries(
        self, now: datetime, limit: int, after: SweepCursor | None = None
    ) -> tuple[DueJob, ...]:
        due = [
            DueJob(job.job_id, job.active_attempt.attempt_number, job.retry_not_before)
            for job in self.list_jobs()
            if job.state is JobState.FAILED_RETRYABLE
            and job.retry_not_before is not None
            and job.retry_not_before <= now
        ]
        return _keyset_page(due, limit, after)

    def _settle(self, message_id: str) -> DispatchMessage:
        self.state.leases.pop(message_id, None)
        self.state.available_at.pop(message_id, None)
        return self.state.outbox.pop(message_id)

    def notice_seen(self, notice_id: str) -> bool:
        return notice_id in self.state.notices

    def record_notice(self, notice_id: str) -> None:
        self.state.notices.add(notice_id)


def _keyset_page[Row: (AttemptDispatch, DueJob)](
    rows: list[Row], limit: int, after: SweepCursor | None
) -> tuple[Row, ...]:
    """Same order and strict keyset continuation as the SQL sweep queries."""

    ordered = sorted(rows, key=lambda row: (row.cursor.at, row.cursor.key))
    if after is not None:
        ordered = [r for r in ordered if (r.cursor.at, r.cursor.key) > (after.at, after.key)]
    return tuple(ordered[:limit])


class InMemoryAiJobStore:
    """Staged, all-or-nothing fake unit of work guarded by one re-entrant lock."""

    marker = FIXTURE_MARKER

    def __init__(self, fences: FakeOwnerFences | None = None) -> None:
        self._state = _StoreState()
        self._lock = RLock()
        self.fences = fences or FakeOwnerFences()
        self.fail_next_commit = False

    @contextmanager
    def transaction(self) -> Iterator[_UnitOfWork]:
        with self._lock:
            staged = self._state.copy()
            yield _UnitOfWork(staged, self.fences)
            if self.fail_next_commit:
                self.fail_next_commit = False
                raise RuntimeError("injected commit failure")
            self._state = staged

    def snapshot(self) -> _StoreState:
        with self._lock:
            return self._state.copy()


class FakeQueue:
    """In-memory broker carrying transient ``WorkerDispatchEnvelope`` values (Δ14)."""

    def __init__(self) -> None:
        self.messages: list[WorkerDispatchEnvelope] = []
        self.available = True
        self.delivered: list[str] = []

    def enqueue(self, envelope: WorkerDispatchEnvelope) -> None:
        if not self.available:
            raise QueueUnavailable("fake broker down")
        self.messages.append(envelope)

    def receive(self) -> WorkerDispatchEnvelope | None:
        if not self.messages:
            return None
        envelope = self.messages.pop(0)
        self.delivered.append(envelope.message.message_id)
        return envelope

    def redeliver(self, envelope: WorkerDispatchEnvelope) -> None:
        self.messages.append(envelope)


@dataclass(frozen=True, slots=True)
class _Grant:
    actions: frozenset[AuthorizationAction]
    target_ids: frozenset[str] | None
    session_ids: frozenset[str] | None


class FakeAuthorization:
    def __init__(self, fences: FakeOwnerFences | None = None) -> None:
        self._grants: dict[str, list[_Grant]] = defaultdict(list)
        self._revoked: set[str] = set()
        self.fences = fences or FakeOwnerFences()
        self.calls = 0

    def grant(
        self,
        principal_id: str,
        actions: set[AuthorizationAction],
        *,
        target_ids: set[str] | None = None,
        session_ids: set[str] | None = None,
    ) -> None:
        self._grants[principal_id].append(
            _Grant(
                frozenset(actions),
                frozenset(target_ids) if target_ids is not None else None,
                frozenset(session_ids) if session_ids is not None else None,
            )
        )
        self._revoked.discard(principal_id)

    def revoke(self, principal_id: str) -> None:
        self._revoked.add(principal_id)

    def decide(
        self, principal: Principal, action: AuthorizationAction, scope: JobScope
    ) -> AuthorizationDecision:
        self.calls += 1
        fence = self.fences.fence(
            grant_fence_scope(principal.organization_id, principal.principal_id)
        )
        if principal.principal_id in self._revoked:
            return AuthorizationDecision(False, "GRANT_REVOKED", fence)
        for grant in self._grants.get(principal.principal_id, []):
            if action not in grant.actions:
                continue
            if grant.target_ids is not None and scope.target_id not in grant.target_ids:
                continue
            if grant.session_ids is not None and scope.session_id not in grant.session_ids:
                continue
            return AuthorizationDecision(True, None, fence)
        return AuthorizationDecision(False, "FORBIDDEN_SCOPE", fence)


class FakeEligibility:
    """Owner-port fake for consent/session/recall/source/kill-switch/budget/context. Its
    decisions carry the organization eligibility fence; mutating the sets does not bump it."""

    def __init__(self, fences: FakeOwnerFences | None = None) -> None:
        self.fences = fences or FakeOwnerFences()
        self.revoked_subjects: set[str] = set()
        self.ended_sessions: set[str] = set()
        self.recalled_requests: set[str] = set()
        self.expired_requests: set[str] = set()
        self.killed_job_types: set[str] = set()
        self.budget_exhausted_targets: set[str] = set()
        self.context_revisions: dict[str, int] = {}

    def check(self, *, scope: JobScope, request_ref: RequestRef, job_type: str) -> (
        EligibilityDecision
    ):
        current = self.context_revisions.get(request_ref.request_id, request_ref.context_revision)
        reason: str | None = None
        if self.revoked_subjects.intersection(scope.subject_refs):
            reason = "CONSENT_REVOKED"
        elif scope.session_id is not None and scope.session_id in self.ended_sessions:
            reason = "SESSION_ENDED"
        elif request_ref.request_id in self.recalled_requests:
            reason = "CONTENT_RECALLED"
        elif request_ref.request_id in self.expired_requests:
            reason = "SOURCE_EXPIRED"
        elif job_type in self.killed_job_types:
            reason = "KILL_SWITCH"
        elif scope.target_id in self.budget_exhausted_targets:
            reason = "BUDGET_EXCEEDED"
        fence = self.fences.fence(eligibility_fence_scope(scope.organization_id))
        return EligibilityDecision(reason is None, reason, current, fence)


class FakeArtifacts:
    def __init__(self, fences: FakeOwnerFences | None = None) -> None:
        self.fences = fences or FakeOwnerFences()
        self._items: dict[str, ArtifactDescriptor] = {}
        self.quarantined: dict[str, str] = {}
        self._count = 0

    def put(
        self,
        organization_id: str,
        body: bytes,
        *,
        job_id: str | None = None,
        attempt_id: str | None = None,
    ) -> OutputRef:
        """Register synthetic bytes; ``job_id``/``attempt_id`` record producer lineage."""

        self._count += 1
        ref = f"artifact_fx{self._count:04d}"
        digest = sha256(body).hexdigest()
        self._items[ref] = ArtifactDescriptor(ref, digest, organization_id, job_id, attempt_id)
        return OutputRef(ref, digest)

    def describe(self, artifact_ref: str) -> ArtifactDescriptor | None:
        descriptor = self._items.get(artifact_ref)
        if descriptor is None:
            return None
        return replace(
            descriptor,
            quarantine_reason=self.quarantined.get(artifact_ref),
            fence=self.fences.fence(artifact_fence_scope(artifact_ref)),
        )

    def quarantine(self, artifact_refs: tuple[str, ...], reason_code: str) -> None:
        """Owner-side artifact state change: the first quarantine bumps the artifact fence."""

        for ref in artifact_refs:
            if ref not in self.quarantined:
                self.quarantined[ref] = reason_code
                self.fences.bump(artifact_fence_scope(ref))


class FakeAudit:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def record(self, event: AuditEvent) -> None:
        self.events.append(event)


class FakeWorkerCapability:
    """Backend-only scoped capability issuer + verifier; tokens are synthetic. Verification is
    still job-bound here; attempt binding/expiry is batch B5 (Δ8)."""

    def __init__(self) -> None:
        self._tokens: dict[str, str] = {}
        self.issued: list[tuple[str, str | None]] = []

    def issue(self, job_id: str, attempt_id: str | None = None,
              now: datetime | None = None) -> str:
        material = job_id if attempt_id is None else f"{job_id}:{attempt_id}"
        token = f"wcap_fx_{sha256(material.encode()).hexdigest()[:16]}"
        self._tokens[token] = job_id
        self.issued.append((job_id, attempt_id))
        return token

    def verify(self, capability: str, job_id: str) -> bool:
        return self._tokens.get(capability) == job_id


ProviderScript = Callable[[DispatchMessage], CompletionClaim]


class FakeProvider:
    """Scripted provider; counts semantic cost (calls per job) for dedup checks."""

    def __init__(self, script: ProviderScript) -> None:
        self._script = script
        self.calls: dict[str, int] = defaultdict(int)

    def run(self, message: DispatchMessage) -> CompletionClaim:
        self.calls[message.job_id] += 1
        return self._script(message)


@dataclass
class FakeWorker:
    """Drives queue → start → provider → completion through the internal worker port."""

    service: AiJobService
    queue: FakeQueue
    provider: FakeProvider
    capabilities: FakeWorkerCapability

    def run_once(self) -> CompletionReceipt | str | None:
        envelope = self.queue.receive()
        if envelope is None:
            return None
        message, capability = envelope.message, envelope.capability  # no self-minted token
        started = self.service.start_attempt(capability, message.job_id, message.attempt_id)
        if not started.started:
            return started.reason_code
        claim = self.provider.run(message)
        return self.service.accept_completion(capability, claim)


class InMemoryProviderCopyRegistry:
    def __init__(self) -> None:
        self._copies: dict[str, ProviderCopy] = {}
        self._purging: set[tuple[str, str]] = set()
        self._receipts: dict[str, PurgeReceipt] = {}
        self._scope_locks: dict[tuple[str, str], RLock] = defaultdict(RLock)
        self._locks_guard = RLock()

    def register(self, copy: ProviderCopy) -> ProviderCopy:
        self._copies.setdefault(copy.copy_id, copy)
        return self._copies[copy.copy_id]

    def get(self, copy_id: str) -> ProviderCopy | None:
        return self._copies.get(copy_id)

    def save(self, copy: ProviderCopy) -> None:
        self._copies[copy.copy_id] = copy

    def list_scope(self, organization_id: str, scope_ref: str) -> tuple[ProviderCopy, ...]:
        return tuple(
            copy
            for _, copy in sorted(self._copies.items())
            if copy.organization_id == organization_id and copy.scope_ref == scope_ref
        )

    def mark_scope_purging(self, organization_id: str, scope_ref: str) -> None:
        self._purging.add((organization_id, scope_ref))

    def is_scope_purging(self, organization_id: str, scope_ref: str) -> bool:
        return (organization_id, scope_ref) in self._purging

    def get_purge_receipt(self, idempotency_key: str) -> PurgeReceipt | None:
        return self._receipts.get(idempotency_key)

    @contextmanager
    def scope_lock(self, organization_id: str, scope_ref: str) -> Iterator[None]:
        """Fake atomic boundary for one (organization, scope) purge request; not durable."""

        with self._locks_guard:
            lock = self._scope_locks[(organization_id, scope_ref)]
        with lock:
            yield

    def put_purge_receipt(self, idempotency_key: str, receipt: PurgeReceipt) -> PurgeReceipt:
        """First receipt for a key wins; the stored receipt is returned to the caller."""

        return self._receipts.setdefault(idempotency_key, receipt)


class FakeProviderCopyAdapter:
    """Outcome by ``provider_profile``: fixture-deletes / -pending / -unsupported / -exception /
    -unverified. Every receipt is ``evidence_kind=fixture``; none proves actual deletion."""

    def __init__(self) -> None:
        self.cancel_requests: list[str] = []
        self.purge_requests: list[str] = []
        self._count = 0

    def request_cancel(self, copy: ProviderCopy) -> None:
        self.cancel_requests.append(copy.copy_id)

    def request_purge(self, copy: ProviderCopy) -> PurgeReceipt:
        self.purge_requests.append(copy.copy_id)
        self._count += 1
        outcome, verified, reason = {
            "fixture-deletes": (ReceiptOutcome.DELETED, True, None),
            "fixture-unverified": (ReceiptOutcome.DELETED, False, "RECEIPT_UNVERIFIED"),
            "fixture-pending": (ReceiptOutcome.PENDING, False, "PROVIDER_PURGE_IN_PROGRESS"),
            "fixture-unsupported": (ReceiptOutcome.UNSUPPORTED, False, "PURGE_NOT_SUPPORTED"),
        }.get(copy.provider_profile, (ReceiptOutcome.EXCEPTION, False, "PROVIDER_PURGE_ERROR"))
        return PurgeReceipt(
            receipt_id=f"purge_rcpt_fx{self._count:04d}",
            copy_id=copy.copy_id,
            outcome=outcome,
            verified=verified,
            evidence_kind=EvidenceKind.FIXTURE,
            reason_code=reason,
        )


__all__ = [
    "FIXTURE_MARKER",
    "FakeArtifacts",
    "FakeAudit",
    "FakeAuthorization",
    "FakeClock",
    "FakeEligibility",
    "FakeOwnerFences",
    "FakeProvider",
    "FakeProviderCopyAdapter",
    "FakeQueue",
    "FakeWorker",
    "FakeWorkerCapability",
    "InMemoryAiJobStore",
    "InMemoryProviderCopyRegistry",
    "JobRevisionConflict",
    "SequentialIds",
    "artifact_fence_scope",
    "eligibility_fence_scope",
    "grant_fence_scope",
]
