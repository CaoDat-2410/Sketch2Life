"""BE2-01 job orchestration: create, dispatch, start, progress, completion, retry, cancel,
owner notices and CMD-44 status query (candidate).

Guard order follows SRS B19.11/B22.1/B22.3: principal + disclosure authority, receipt lookup,
then (new mutations only) current eligibility, semantic dedup and one atomic commit.

Phase B B3 (plan revision 3 Δ3/Δ5): owner decisions are taken outside the write transaction;
the write transaction re-reads, holds their owner fences on its own connection before any
mutation and commits. A stale or missing fence rolls back and re-decides once; a
``UniqueConflict`` rolls the whole candidate back and a fresh round re-reads the winner.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from hashlib import sha256
from typing import TypeVar

from sketch2life.application.ports.ai_jobs import (
    AiJobRepository,
    AiJobUnitOfWork,
    ArtifactDescriptor,
    ArtifactPort,
    AttemptDispatch,
    AuditEvent,
    AuditPort,
    AuthorizationAction,
    AuthorizationDecision,
    AuthorizationPort,
    CancellationNotice,
    ClaimedDispatch,
    ClockPort,
    CommandReceipt,
    CommandScopeKey,
    CompletionReceipt,
    DispatchMessage,
    DispatchQueuePort,
    EligibilityDecision,
    EligibilityPort,
    IdGeneratorPort,
    OwnerFence,
    Principal,
    PrincipalRole,
    SemanticRequestKey,
    UniqueConflict,
    WorkerCapabilityIssuer,
    WorkerCapabilityVerifier,
    WorkerDispatchEnvelope,
)
from sketch2life.domain.ai_jobs import model as jobs
from sketch2life.domain.ai_jobs.completion import (
    VERDICT_DISPOSITION,
    CompletionClaim,
    Moderation,
    OutcomeKind,
    PreconditionVerdict,
    canonical_sha256,
    check_completion_preconditions,
)
from sketch2life.domain.ai_jobs.model import (
    AiJob,
    JobPollPolicy,
    JobProgress,
    JobRetryPolicy,
    JobScope,
    JobState,
    RequestRef,
    ResultDisposition,
    ResultRef,
)

CREATE_CONTRACT = "CreateAiJob"
CANCEL_CONTRACT = "CancelAiJob"

# Named fixture policies (PROPOSED). Values mirror SRS PROPOSED rows; not production policy.
FIXTURE_RETRY_POLICY = JobRetryPolicy(
    policy_id="fixture.job_retry.v0",
    max_attempts=3,
    backoff_base_ms=1000,
    backoff_multiplier=2,
    backoff_max_ms=8000,
    attempt_timeout_ms=30000,
)
@dataclass(frozen=True, slots=True)
class DispatchPolicy:
    """Named dispatch/recovery fixture values (decision record §5.1). PROPOSED, never
    production policy."""

    policy_id: str
    start_timeout_ms: int
    max_publishes: int
    lease_ms: int
    claim_limit: int
    status: str = "PROPOSED"

    @property
    def start_timeout(self) -> timedelta:
        return timedelta(milliseconds=self.start_timeout_ms)

    @property
    def lease(self) -> timedelta:
        return timedelta(milliseconds=self.lease_ms)


FIXTURE_DISPATCH_POLICY = DispatchPolicy(
    policy_id="fixture.durable_jobs.v0",
    start_timeout_ms=5000,
    max_publishes=3,
    lease_ms=10000,
    claim_limit=50,
)
DEFAULT_DISPATCH_OWNER = "dispatcher_fx"
FIXTURE_POLL_POLICY = JobPollPolicy(
    policy_id="fixture.job_poll.v0",
    min_interval_ms=2000,
    max_interval_ms=10000,
    backoff_step_seconds=10,
)

PUBLIC_MESSAGES: Mapping[str, str] = {
    "PROVIDER_TIMEOUT": "The AI step took too long.",
    "PROVIDER_UNAVAILABLE": "The AI service is temporarily unavailable.",
    "PROVIDER_ERROR": "The AI step could not finish.",
    "OUTPUT_MALFORMED": "The AI result could not be used.",
    "UNSAFE_CONTENT": "The AI result was blocked by safety checks.",
    "CANCELLED_BY_TEACHER": "The teacher cancelled this request.",
    "CONSENT_REVOKED": "This request is no longer permitted.",
    "SESSION_ENDED": "The session has ended.",
    "CONTENT_RECALLED": "The source content was withdrawn.",
    "SOURCE_EXPIRED": "The source content has expired.",
    "KILL_SWITCH": "This AI feature is paused by policy.",
    "BUDGET_EXCEEDED": "The AI budget for this request is used up.",
    "DISPATCH_LOST": "The AI step did not start in time.",
}
GENERIC_PUBLIC_MESSAGE = "The AI step could not finish."
# Guard verdicts that leave the active attempt completable: no artifact state change (R03a).
TEMPORARY_VERDICTS = frozenset({PreconditionVerdict.INVALID_STATE,
                                PreconditionVerdict.INPUT_MISMATCH})
# Failure codes a worker may report verbatim; anything else maps to PROVIDER_ERROR.
WORKER_FAILURE_CODES = frozenset(
    {"PROVIDER_TIMEOUT", "PROVIDER_UNAVAILABLE", "PROVIDER_ERROR", "OUTPUT_MALFORMED"}
)
# Write rounds per use case (plan §5.1 step 3, §7.2): the first round plus one re-decision.
DECISION_ROUNDS = 2


def public_message(code: str) -> str:
    return PUBLIC_MESSAGES.get(code, GENERIC_PUBLIC_MESSAGE)


class AiJobError(Exception):
    """Typed, safe application error; never carries provider/internal diagnostics."""

    def __init__(
        self, code: str, http_status: int, message: str, *, retryable: bool = False
    ) -> None:
        super().__init__(code)
        self.code = code
        self.http_status = http_status
        self.public_message = message
        self.retryable = retryable


ELIGIBILITY_ERRORS: Mapping[str, tuple[int, str]] = {
    "CONSENT_REVOKED": (403, "CONSENT_REQUIRED"),
    "SESSION_ENDED": (409, "INVALID_STATE"),
    "CONTENT_RECALLED": (409, "CONTENT_RECALLED"),
    "SOURCE_EXPIRED": (409, "STALE_CONTEXT"),
    "KILL_SWITCH": (409, "POLICY_UNRESOLVED"),
    "BUDGET_EXCEEDED": (429, "BUDGET_EXCEEDED"),
}


def _not_found() -> AiJobError:
    return AiJobError("RESOURCE_NOT_FOUND", 404, "Resource not found.")


def _unresolved(code: str) -> AiJobError:
    """Typed retryable outcome after the bounded rounds (stale fence or unique conflict)."""

    if code == "STALE_CONTEXT":
        return AiJobError(code, 409, "The request context changed; try again.", retryable=True)
    return AiJobError("IDEMPOTENCY_CONFLICT", 409, "A concurrent request is still settling.",
                      retryable=True)


class _StaleOwnerDecision(Exception):
    """A decision's owner fence is stale or missing; the write transaction rolls back."""


class _PriorReceipt(Exception):
    """A completion receipt raced in between the read and the write transaction."""

    def __init__(self, receipt: CompletionReceipt) -> None:
        super().__init__(receipt.receipt_id)
        self.receipt = receipt


@dataclass
class _CompletionEffects:
    """Effects decided inside a completion write; applied only after its commit."""

    audits: list[tuple[str, AiJob, str | None]] = field(default_factory=list)
    quarantines: list[tuple[tuple[str, ...], str]] = field(default_factory=list)
    artifact_fences: tuple[OwnerFence | None, ...] = ()


@dataclass(frozen=True, slots=True)
class CreateJobCommand:
    principal: Principal
    idempotency_key: str
    job_type: str
    target_id: str
    purpose_code: str
    session_id: str | None
    subject_refs: tuple[str, ...]
    request_ref: RequestRef
    correlation_id: str

    def fingerprint(self) -> str:
        return canonical_sha256(
            {
                "contract_name": CREATE_CONTRACT,
                "job_type": self.job_type,
                "target_id": self.target_id,
                "purpose_code": self.purpose_code,
                "session_id": self.session_id,
                "subject_refs": sorted(self.subject_refs),
                "request_ref": {
                    "request_id": self.request_ref.request_id,
                    "request_revision": self.request_ref.request_revision,
                    "input_hash": self.request_ref.input_hash,
                    "context_revision": self.request_ref.context_revision,
                },
            }
        )


@dataclass(frozen=True, slots=True)
class CancelJobCommand:
    principal: Principal
    idempotency_key: str
    job_id: str
    expected_job_revision: int | None
    reason_code: str = "CANCELLED_BY_TEACHER"

    def fingerprint(self) -> str:
        return canonical_sha256(
            {
                "contract_name": CANCEL_CONTRACT,
                "job_id": self.job_id,
                "expected_job_revision": self.expected_job_revision,
                "reason_code": self.reason_code,
            }
        )


@dataclass(frozen=True, slots=True)
class CommandResult:
    job_id: str
    job_revision: int
    outcome: str
    replayed: bool


@dataclass(frozen=True, slots=True)
class StartResult:
    started: bool
    reason_code: str | None


@dataclass(frozen=True, slots=True)
class JobStatusResult:
    etag: str
    not_modified: bool
    role: PrincipalRole
    view: Mapping[str, object] | None


@dataclass(frozen=True, slots=True)
class AiJobDependencies:
    repository: AiJobRepository
    authorization: AuthorizationPort
    eligibility: EligibilityPort
    worker_capability: WorkerCapabilityVerifier
    clock: ClockPort
    ids: IdGeneratorPort
    artifacts: ArtifactPort
    audit: AuditPort
    queue: DispatchQueuePort
    capability_issuer: WorkerCapabilityIssuer
    retry_policy: JobRetryPolicy = FIXTURE_RETRY_POLICY
    poll_policy: JobPollPolicy = FIXTURE_POLL_POLICY
    dispatch_policy: DispatchPolicy = FIXTURE_DISPATCH_POLICY


class QueueUnavailable(Exception):
    """Raised by queue adapters; the job stays recoverably queued in the outbox."""


class AiJobService:
    def __init__(self, deps: AiJobDependencies) -> None:
        self._d = deps

    # ----------------------------------------------------------------- commands
    def create_job(self, command: CreateJobCommand) -> CommandResult:
        principal = command.principal
        if not command.idempotency_key or len(command.idempotency_key) > 120:
            raise AiJobError("MALFORMED_REQUEST", 400, "Idempotency-Key is required.")
        scope = JobScope(
            organization_id=principal.organization_id,
            session_id=command.session_id,
            subject_refs=tuple(sorted(command.subject_refs)),
            purpose_code=command.purpose_code,
            target_id=command.target_id,
        )
        authorization = self._decide(principal, AuthorizationAction.CREATE_JOB, scope)
        if not authorization.allowed:
            raise AiJobError("FORBIDDEN_SCOPE", 403, "Not permitted for this scope.")
        key = CommandScopeKey(
            principal.organization_id,
            principal.principal_id,
            CREATE_CONTRACT,
            command.target_id,
            command.idempotency_key,
        )
        fingerprint = command.fingerprint()
        semantic = SemanticRequestKey(
            principal.organization_id,
            command.job_type,
            command.request_ref.request_id,
            command.request_ref.request_revision,
            command.request_ref.input_hash,
            command.request_ref.context_revision,
            scope.target_id,
            scope.purpose_code,
            scope.session_id,
            scope.subject_refs,
        )
        failure = "IDEMPOTENCY_CONFLICT"
        for round_number in range(DECISION_ROUNDS):
            if round_number:
                authorization = self._decide(principal, AuthorizationAction.CREATE_JOB, scope)
                if not authorization.allowed:
                    raise AiJobError("FORBIDDEN_SCOPE", 403, "Not permitted for this scope.")
            now = self._d.clock.now()
            with self._d.repository.transaction() as tx:
                replay = self._replay(tx, principal, key, fingerprint)
                if replay is not None:
                    return replay
                winner_id = tx.find_semantic(semantic)
                winner = tx.get_job(winner_id) if winner_id is not None else None
            eligibility = self._d.eligibility.check(
                scope=scope, request_ref=command.request_ref, job_type=command.job_type
            )
            if not eligibility.eligible:
                raise self._eligibility_error(eligibility)
            if winner_id is not None and (
                winner is None
                or not self._allowed(principal, AuthorizationAction.READ_JOB, winner.scope)
            ):
                raise _not_found()
            try:
                with self._d.repository.transaction() as tx:
                    replay = self._replay(tx, principal, key, fingerprint)
                    if replay is not None:
                        return replay
                    if tx.find_semantic(semantic) != winner_id:
                        raise UniqueConflict("semantic_request")
                    self._hold(tx, authorization.fence, eligibility.fence)
                    if winner_id is not None:
                        current = self._get(tx, winner_id)
                        tx.put_command_receipt(
                            CommandReceipt(key, fingerprint, current.job_id, "deduplicated",
                                           current.job_revision, now)
                        )
                        event = self._audit_intent(tx, "job.create.deduplicated", current,
                                                   discriminator=_key_discriminator(key))
                        result = CommandResult(current.job_id, current.job_revision,
                                               "deduplicated", False)
                    else:
                        job = jobs.create_job(
                            job_id=self._d.ids.new_id("job"),
                            attempt_id=self._d.ids.new_id("att"),
                            job_type=command.job_type,
                            scope=scope,
                            request_ref=command.request_ref,
                            correlation_id=command.correlation_id,
                            retry_policy=self._d.retry_policy,
                            now=now,
                        )
                        tx.insert_job(job)
                        tx.put_semantic(semantic, job.job_id)
                        tx.put_command_receipt(
                            CommandReceipt(key, fingerprint, job.job_id, "created",
                                           job.job_revision, now)
                        )
                        tx.add_outbox(self._dispatch_message(job), now=now)
                        event = self._audit_intent(tx, "job.created", job,
                                                   discriminator=job.job_id)
                        result = CommandResult(job.job_id, job.job_revision, "created", False)
            except UniqueConflict:
                failure = "IDEMPOTENCY_CONFLICT"
                continue
            except _StaleOwnerDecision:
                failure = "STALE_CONTEXT"
                continue
            self._d.audit.record(event)
            return result
        raise _unresolved(failure)

    def cancel_job(self, command: CancelJobCommand) -> CommandResult:
        principal = command.principal
        key = CommandScopeKey(
            principal.organization_id,
            principal.principal_id,
            CANCEL_CONTRACT,
            command.job_id,
            command.idempotency_key,
        )
        fingerprint = command.fingerprint()
        failure = "IDEMPOTENCY_CONFLICT"
        for _ in range(DECISION_ROUNDS):
            with self._d.repository.transaction() as tx:
                job = tx.get_job(command.job_id)
            if job is None or not self._readable(principal, job):
                raise _not_found()
            decision = self._decide(principal, AuthorizationAction.CANCEL_JOB, job.scope)
            if not decision.allowed:
                raise AiJobError("FORBIDDEN_SCOPE", 403, "Not permitted for this scope.")
            try:
                with self._d.repository.transaction() as tx:
                    job = self._get(tx, command.job_id, for_update=True)
                    replay = self._replay(tx, principal, key, fingerprint)
                    if replay is not None:
                        return replay
                    if command.expected_job_revision is None:
                        raise AiJobError("PRECONDITION_REQUIRED", 428, "If-Match is required.")
                    if command.expected_job_revision != job.job_revision:
                        raise AiJobError("STALE_AGGREGATE", 412,
                                         "The job has changed; reload it.")
                    if job.state not in jobs.CANCELLABLE_STATES:
                        raise AiJobError("INVALID_STATE", 409,
                                         "The job can no longer be cancelled.")
                    self._hold(tx, decision.fence)
                    updated = jobs.cancel(
                        job,
                        reason_code=command.reason_code,
                        public_message=public_message(command.reason_code),
                        now=self._d.clock.now(),
                    )
                    tx.cas_job(expected_revision=job.job_revision, job=updated)
                    tx.put_command_receipt(
                        CommandReceipt(key, fingerprint, job.job_id, "cancelled",
                                       updated.job_revision, updated.updated_at)
                    )
                    event = self._audit_intent(tx, "job.cancelled", updated, command.reason_code,
                                               discriminator=_key_discriminator(key))
            except UniqueConflict:
                failure = "IDEMPOTENCY_CONFLICT"
                continue
            except _StaleOwnerDecision:
                failure = "STALE_CONTEXT"
                continue
            self._d.audit.record(event)
            return CommandResult(updated.job_id, updated.job_revision, "cancelled", False)
        raise _unresolved(failure)

    def apply_cancellation_notice(self, notice: CancellationNotice) -> tuple[str, ...]:
        """Owner-port notice; idempotent by ``notice_id``. Invalidates scheduled retries."""

        cancelled: list[AiJob] = []
        with self._d.repository.transaction() as tx:
            if tx.notice_seen(notice.notice_id):
                return ()
            for job in tx.list_jobs():
                if job.organization_id != notice.organization_id or job.is_terminal:
                    continue
                if not _notice_matches(notice, job):
                    continue
                updated = jobs.cancel(
                    job,
                    reason_code=notice.reason_code,
                    public_message=public_message(notice.reason_code),
                    now=self._d.clock.now(),
                )
                tx.cas_job(expected_revision=job.job_revision, job=updated)
                cancelled.append(updated)
            tx.record_notice(notice.notice_id)
        for job in cancelled:
            self._audit("job.cancelled_by_notice", job, notice.reason_code)
        return tuple(job.job_id for job in cancelled)

    # ------------------------------------------------------------ dispatch/worker
    def dispatch_outbox(self, *, owner: str = DEFAULT_DISPATCH_OWNER) -> int:
        """Fenced outbox dispatch (Δ6, Δ14): lease a bounded batch, then per row decide
        eligibility, hold its fence in a short acceptance transaction, mint the capability and
        enqueue outside SQL, and acknowledge with the fenced bundle. Returns enqueued count."""

        policy = self._d.dispatch_policy
        with self._d.repository.transaction() as tx:
            claims = tx.claim_outbox(owner, self._d.clock.now(), policy.lease, policy.claim_limit)
        return sum(1 for claim in claims if self._dispatch_one(claim))

    def _dispatch_one(self, claim: ClaimedDispatch) -> bool:
        message, lease = claim.message, claim.lease
        for _ in range(DECISION_ROUNDS):
            with self._d.repository.transaction() as tx:
                job = tx.get_job(message.job_id)
            if job is None or not _dispatchable(job, message):
                with self._d.repository.transaction() as tx:
                    tx.dispose_outbox(lease, "ATTEMPT_NOT_DISPATCHABLE")
                return False
            eligibility = self._check(job)
            denied: AiJob | None = None
            try:
                with self._d.repository.transaction() as tx:
                    if not tx.lease_current(lease):
                        return False  # a newer holder owns this row now
                    job = self._get(tx, message.job_id, for_update=True)
                    if not _dispatchable(job, message):
                        tx.dispose_outbox(lease, "ATTEMPT_NOT_DISPATCHABLE")
                        return False
                    self._hold(tx, eligibility.fence)
                    if not eligibility.eligible:
                        reason = eligibility.reason_code or "CONSENT_REVOKED"
                        denied = jobs.cancel(job, reason_code=reason,
                                             public_message=public_message(reason),
                                             now=self._d.clock.now())
                        tx.cas_job(expected_revision=job.job_revision, job=denied)
                        tx.dispose_outbox(lease, reason)
            except _StaleOwnerDecision:
                continue
            if denied is not None:
                self._audit("job.dispatch_denied", denied, denied.failure.code
                            if denied.failure else None)
                return False
            return self._publish(claim)
        with self._d.repository.transaction() as tx:
            tx.release_outbox(lease, "STALE_CONTEXT")
        return False

    def _publish(self, claim: ClaimedDispatch) -> bool:
        """External effect outside SQL; no lock is held across the broker call."""

        message = claim.message
        capability = self._d.capability_issuer.issue(
            message.job_id, message.attempt_id, self._d.clock.now()
        )
        try:
            self._d.queue.enqueue(WorkerDispatchEnvelope(message, capability))
        except QueueUnavailable:
            with self._d.repository.transaction() as tx:
                tx.release_outbox(claim.lease, "QUEUE_UNAVAILABLE")
            return False
        with self._d.repository.transaction() as tx:
            # A stale holder's or repeated acknowledgement is a no-op for the whole bundle.
            tx.ack_dispatch(claim.lease, self._d.clock.now())
        return True

    def recover_unstarted_dispatches(self) -> tuple[tuple[str, str], ...]:
        """Reconciler sweep (Δ7/Δ11/Δ13): an active queued attempt published but not durably
        started within the start timeout is republished as the same attempt until the publish
        bound, then closed with ``record_dispatch_loss``. Returns ``(job_id, outcome)``."""

        policy = self._d.dispatch_policy
        return self._sweep(
            lambda tx, now: tx.queued_dispatched_not_started(now, policy.start_timeout,
                                                             policy.claim_limit),
            self._recover_unstarted,
        )

    def _recover_unstarted(self, due: AttemptDispatch) -> tuple[str, str] | None:
        policy = self._d.dispatch_policy
        now = self._d.clock.now()
        with self._d.repository.transaction() as tx:
            job = self._get(tx, due.job_id, for_update=True)
            current = tx.attempt_dispatch(due.attempt_id)
            if (
                current is None
                or job.job_revision != due.job_revision
                or job.state is not JobState.QUEUED
                or job.active_attempt.attempt_id != due.attempt_id
                or job.active_attempt.started_at is not None
                or current.dispatched_at is None
                or now - current.dispatched_at < policy.start_timeout
                or tx.has_pending_dispatch(due.attempt_id)
            ):
                return None  # start won, the job settled, or a recovery intent is pending
            if current.dispatch_count < policy.max_publishes:
                tx.add_outbox(self._dispatch_message(job), now=now)
                outcome = "republished"
            else:
                updated = jobs.record_dispatch_loss(
                    job, due.attempt_id, public_message=public_message(jobs.DISPATCH_LOST),
                    now=now,
                )
                tx.cas_job(expected_revision=job.job_revision, job=updated)
                outcome = "dispatch_lost"
        if outcome == "dispatch_lost":
            self._audit("job.dispatch_lost", updated, jobs.DISPATCH_LOST)
        return (due.job_id, outcome)

    def start_attempt(self, capability: str, job_id: str, attempt_id: str) -> StartResult:
        self._require_worker(capability, job_id)
        for _ in range(DECISION_ROUNDS):
            with self._d.repository.transaction() as tx:
                job = self._get(tx, job_id)
            eligibility = self._check(job)
            try:
                with self._d.repository.transaction() as tx:
                    job = self._get(tx, job_id, for_update=True)
                    if job.active_attempt.attempt_id != attempt_id:
                        return StartResult(False, "ATTEMPT_NOT_ACTIVE")
                    if job.state is JobState.RUNNING:
                        return StartResult(False, "DUPLICATE_DELIVERY")
                    if job.state is not JobState.QUEUED:
                        return StartResult(False, "JOB_NOT_QUEUED")
                    self._hold(tx, eligibility.fence)
                    if not eligibility.eligible:
                        reason = eligibility.reason_code or "CONSENT_REVOKED"
                        updated = jobs.cancel(
                            job, reason_code=reason, public_message=public_message(reason),
                            now=self._d.clock.now(),
                        )
                        result = StartResult(False, reason)
                    else:
                        updated = jobs.start_attempt(job, attempt_id, self._d.clock.now())
                        result = StartResult(True, None)
                    tx.cas_job(expected_revision=job.job_revision, job=updated)
            except _StaleOwnerDecision:
                continue
            self._audit("job.start" if result.started else "job.start_denied", updated,
                        result.reason_code)
            return result
        return StartResult(False, "STALE_CONTEXT")

    def report_progress(
        self, capability: str, job_id: str, attempt_id: str, progress: JobProgress
    ) -> bool:
        self._require_worker(capability, job_id)
        with self._d.repository.transaction() as tx:
            job = self._get(tx, job_id, for_update=True)
            if job.active_attempt.attempt_id != attempt_id or job.state is not JobState.RUNNING:
                return False
            updated = jobs.report_progress(job, attempt_id, progress, self._d.clock.now())
            if updated is not job:
                tx.cas_job(expected_revision=job.job_revision, job=updated)
        return True

    def accept_completion(self, capability: str, claim: CompletionClaim) -> CompletionReceipt:
        """Only a completion that settles the attempt (changes the job) takes the immutable
        ``(job_id, attempt_id)`` slot. Guard rejections that leave the job unchanged return a
        non-authoritative receipt, so a later valid claim of the active attempt still lands."""

        if not isinstance(claim.job_id, str) or not isinstance(claim.attempt_id, str):
            raise AiJobError("MALFORMED_REQUEST", 400, "Malformed completion identity.")
        self._require_worker(capability, claim.job_id)
        fingerprint = claim.fingerprint()
        details = {"attempt_id": claim.attempt_id}
        if claim.diagnostic:
            details["diagnostic_sha256"] = sha256(claim.diagnostic.encode("utf-8")).hexdigest()
        for _ in range(DECISION_ROUNDS):
            with self._d.repository.transaction() as tx:
                job = self._get(tx, claim.job_id)
                prior = tx.get_completion_receipt(claim.job_id, claim.attempt_id)
            if prior is not None:
                return self._completion_replay(prior, fingerprint, job, details)
            normalised = self._normalise_claim(claim, details)
            eligibility = self._check(job) if normalised is not None else None
            descriptors = self._describe_outputs(normalised) if normalised is not None else {}
            effects = _CompletionEffects()
            reason: str | None
            try:
                with self._d.repository.transaction() as tx:
                    job = self._get(tx, claim.job_id, for_update=True)
                    raced = tx.get_completion_receipt(claim.job_id, claim.attempt_id)
                    if raced is not None:
                        raise _PriorReceipt(raced)
                    if normalised is None or eligibility is None:
                        updated, disposition, reason = (job, ResultDisposition.REJECTED,
                                                        "MALFORMED_CLAIM")
                    else:
                        updated, disposition, reason = self._decide_completion(
                            job, normalised, eligibility, descriptors, effects
                        )
                    authoritative = updated is not job
                    receipt = CompletionReceipt(
                        receipt_id=self._d.ids.new_id("rcpt"),
                        job_id=job.job_id,
                        attempt_id=claim.attempt_id,
                        fingerprint=fingerprint,
                        disposition=disposition,
                        reason_code=reason,
                        job_revision_after=updated.job_revision,
                        recorded_at=self._d.clock.now(),
                        authoritative=authoritative,
                    )
                    if authoritative:
                        fence = eligibility.fence if eligibility is not None else None
                        self._hold(tx, fence, *effects.artifact_fences)
                        tx.cas_job(expected_revision=job.job_revision, job=updated)
                        tx.put_completion_receipt(receipt)
            except _PriorReceipt as race:
                return self._completion_replay(race.receipt, fingerprint, job, details)
            except _StaleOwnerDecision:
                continue
            for event_type, subject, verdict in effects.audits:
                self._audit(event_type, subject, verdict)
            for refs, quarantine_reason in effects.quarantines:
                self._quarantine(refs, quarantine_reason)
            details["disposition"] = str(disposition)
            self._audit("job.completion" if authoritative else "job.completion_rejected",
                        updated, reason, details)
            return receipt
        raise _unresolved("STALE_CONTEXT")

    def expire_overdue_attempts(self) -> tuple[str, ...]:
        """Overdue-running sweep (Δ11): policy-timeout failure, targeted paged query."""

        return self._sweep(
            lambda tx, now: tx.overdue_running(now, self._d.dispatch_policy.claim_limit),
            self._expire_overdue,
        )

    def _expire_overdue(self, job_id: str) -> str | None:
        now = self._d.clock.now()
        with self._d.repository.transaction() as tx:
            job = self._get(tx, job_id, for_update=True)
            started = job.started_at
            if (
                job.state is not JobState.RUNNING
                or started is None
                or now - started < _ms(job.retry_policy.attempt_timeout_ms)
            ):
                return None
            updated = jobs.record_failure(
                job, job.active_attempt.attempt_id, code="PROVIDER_TIMEOUT",
                retryable=True, public_message=public_message("PROVIDER_TIMEOUT"), now=now,
            )
            tx.cas_job(expected_revision=job.job_revision, job=updated)
        return job_id

    def run_due_retries(self) -> tuple[str, ...]:
        """Due-retry sweep (Δ11): targeted paged query, then the fenced ``retry_job``."""

        return self._sweep(
            lambda tx, now: tx.due_retries(now, self._d.dispatch_policy.claim_limit),
            lambda due: due[0] if self.retry_job(due[0], due[1]) else None,
        )

    def _sweep(
        self,
        query: Callable[[AiJobUnitOfWork, datetime], tuple[_Due, ...]],
        handle: Callable[[_Due], _Out | None],
    ) -> tuple[_Out, ...]:
        """Repeat a targeted page until it is empty or a page makes no progress; rows that
        stayed due (lost race, stale fence) are left for the next sweep. No seen-marker."""

        done: list[_Out] = []
        while True:
            with self._d.repository.transaction() as tx:
                page = query(tx, self._d.clock.now())
            progressed = [out for out in map(handle, page) if out is not None]
            done.extend(progressed)
            if not page or not progressed:
                return tuple(done)

    def retry_job(self, job_id: str, scheduled_for_attempt: int) -> bool:
        """Scheduled retry callback; stale callbacks (cancelled/advanced jobs) are no-ops."""

        for _ in range(DECISION_ROUNDS):
            now = self._d.clock.now()
            with self._d.repository.transaction() as tx:
                job = self._get(tx, job_id)
            if not _retry_due(job, scheduled_for_attempt, now):
                return False
            eligibility = self._check(job)
            try:
                with self._d.repository.transaction() as tx:
                    job = self._get(tx, job_id, for_update=True)
                    if not _retry_due(job, scheduled_for_attempt, now):
                        return False
                    self._hold(tx, eligibility.fence)
                    if not eligibility.eligible:
                        reason = eligibility.reason_code or "CONSENT_REVOKED"
                        updated = jobs.cancel(job, reason_code=reason,
                                              public_message=public_message(reason), now=now)
                        tx.cas_job(expected_revision=job.job_revision, job=updated)
                        requeued = False
                    else:
                        updated = jobs.requeue_for_retry(
                            job, new_attempt_id=self._d.ids.new_id("att"), now=now
                        )
                        tx.cas_job(expected_revision=job.job_revision, job=updated)
                        tx.add_outbox(self._dispatch_message(updated), now=now)
                        requeued = True
            except _StaleOwnerDecision:
                continue
            self._audit("job.requeued" if requeued else "job.retry_denied", updated)
            return requeued
        return False

    # -------------------------------------------------------------------- query
    def get_job_status(
        self, principal: Principal, job_id: str, if_none_match: str | None = None
    ) -> JobStatusResult:
        with self._d.repository.transaction() as tx:
            job = tx.get_job(job_id)
        if job is None or not self._readable(principal, job):
            raise _not_found()
        expose_results = (
            principal.role is PrincipalRole.TEACHER
            and job.state is JobState.SUCCEEDED
            and job.result_disposition is ResultDisposition.ACCEPTED
            and self._check(job).eligible
        )
        poll_after = jobs.poll_after_ms(job, self._d.poll_policy, self._d.clock.now())
        variant = sha256(
            f"{principal.role}|{expose_results}|{poll_after}".encode()
        ).hexdigest()[:8]
        etag = f'"job:{job.job_id}:{job.job_revision}:{variant}"'
        if if_none_match is not None and etag in _etag_candidates(if_none_match):
            return JobStatusResult(etag, True, principal.role, None)
        view = project_job(job, principal.role, expose_results, poll_after)
        return JobStatusResult(etag, False, principal.role, view)

    # ------------------------------------------------------------------ helpers
    def _decide_completion(
        self,
        job: AiJob,
        claim: CompletionClaim,
        eligibility: EligibilityDecision,
        descriptors: Mapping[str, ArtifactDescriptor | None],
        effects: _CompletionEffects,
    ) -> tuple[AiJob, ResultDisposition, str | None]:
        """Pure decision over pre-fetched owner decisions; side effects go to ``effects``."""

        now = self._d.clock.now()
        owned = self._owned_descriptors(job, claim, descriptors)
        output_refs = tuple(descriptor.artifact_ref for descriptor in owned)
        verdict = check_completion_preconditions(job, claim)
        if verdict is not PreconditionVerdict.PROCEED:
            if verdict is PreconditionVerdict.INPUT_MISMATCH:
                effects.audits.append(("job.completion_input_mismatch", job, str(verdict)))
            if verdict not in TEMPORARY_VERDICTS:
                # The attempt can no longer complete: its own outputs are final rejects.
                effects.quarantines.append((output_refs, str(verdict)))
            return job, VERDICT_DISPOSITION[verdict], str(verdict)
        attempt_id = claim.attempt_id
        if not eligibility.eligible:
            reason = eligibility.reason_code or "CONSENT_REVOKED"
            effects.quarantines.append((output_refs, reason))
            updated = jobs.cancel(job, reason_code=reason, public_message=public_message(reason),
                                  now=now)
            return updated, ResultDisposition.REJECTED, reason
        if claim.kind is OutcomeKind.FAILURE:
            code = claim.failure_code or "PROVIDER_ERROR"
            updated = jobs.record_failure(job, attempt_id, code=code, retryable=claim.retryable,
                                          public_message=public_message(code), now=now)
            return updated, ResultDisposition.ACCEPTED, code
        if claim.moderation is Moderation.UNSAFE:
            effects.quarantines.append((output_refs, "UNSAFE_CONTENT"))
            updated = jobs.block_unsafe(job, attempt_id,
                                        public_message=public_message("UNSAFE_CONTENT"), now=now)
            return updated, ResultDisposition.REJECTED, "UNSAFE_CONTENT"
        # Admission depends on the owned outputs' artifact state: hold their fences too.
        effects.artifact_fences = tuple(descriptor.fence for descriptor in owned)
        results = self._validated_outputs(job, claim, descriptors)
        if results is None:
            effects.quarantines.append((output_refs, "OUTPUT_MALFORMED"))
            updated = jobs.record_failure(job, attempt_id, code="OUTPUT_MALFORMED",
                                          retryable=False,
                                          public_message=public_message("OUTPUT_MALFORMED"),
                                          now=now)
            return updated, ResultDisposition.REJECTED, "OUTPUT_MALFORMED"
        pinned = job.active_attempt.request_ref.context_revision
        if eligibility.current_context_revision != pinned:
            note = f"source context {pinned} superseded by {eligibility.current_context_revision}"
            updated = jobs.succeed(job, attempt_id, result_refs=results,
                                   disposition=ResultDisposition.STALE, now=now, lineage_note=note)
            return updated, ResultDisposition.STALE, "STALE_CONTEXT"
        updated = jobs.succeed(job, attempt_id, result_refs=results,
                               disposition=ResultDisposition.ACCEPTED, now=now)
        return updated, ResultDisposition.ACCEPTED, None

    def _validated_outputs(
        self,
        job: AiJob,
        claim: CompletionClaim,
        descriptors: Mapping[str, ArtifactDescriptor | None],
    ) -> tuple[ResultRef, ...] | None:
        if not claim.outputs:
            return None
        refs: list[ResultRef] = []
        for output in claim.outputs:
            descriptor = descriptors.get(output.artifact_ref)
            if (
                descriptor is None
                or not _produced_by(descriptor, job, claim.attempt_id)
                or descriptor.sha256 != output.sha256
                or descriptor.quarantine_reason is not None
            ):
                return None
            refs.append(ResultRef(output.artifact_ref, output.sha256,
                                  f"{job.job_type}:{job.active_attempt.attempt_id}"))
        return tuple(refs)

    def _replay(
        self, tx: AiJobUnitOfWork, principal: Principal, key: CommandScopeKey, fingerprint: str
    ) -> CommandResult | None:
        receipt = tx.get_command_receipt(key)
        if receipt is None:
            return None
        if receipt.fingerprint != fingerprint:
            raise AiJobError("IDEMPOTENCY_PAYLOAD_MISMATCH", 409,
                             "This key was used for a different request.")
        job = tx.get_job(receipt.job_id)
        if job is None or not self._readable(principal, job):
            raise _not_found()
        return CommandResult(receipt.job_id, receipt.job_revision_at_commit, receipt.outcome, True)

    def _readable(self, principal: Principal, job: AiJob) -> bool:
        return principal.organization_id == job.organization_id and self._allowed(
            principal, AuthorizationAction.READ_JOB, job.scope
        )

    def _decide(
        self, principal: Principal, action: AuthorizationAction, scope: JobScope
    ) -> AuthorizationDecision:
        if principal.organization_id != scope.organization_id:
            return AuthorizationDecision(False, "FORBIDDEN_SCOPE")
        return self._d.authorization.decide(principal, action, scope)

    def _allowed(self, principal: Principal, action: AuthorizationAction, scope: JobScope) -> bool:
        return self._decide(principal, action, scope).allowed

    def _hold(self, tx: AiJobUnitOfWork, *fences: OwnerFence | None) -> None:
        """Hold the decisions' owner fences before any mutation (Δ3). A missing fence is
        never treated as current."""

        held = tuple(fence for fence in fences if fence is not None)
        if len(held) != len(fences) or not tx.hold_owner_fences(held).current:
            raise _StaleOwnerDecision()

    def _audit_intent(
        self,
        tx: AiJobUnitOfWork,
        event_type: str,
        job: AiJob,
        reason: str | None = None,
        *,
        discriminator: str,
    ) -> AuditEvent:
        """Durable audit intent inside the committing transaction; the deterministic
        ``event_id`` lets later delivery deduplicate (sink delivery is batch B5)."""

        event = AuditEvent(event_type, job.organization_id, job.job_id, job.correlation_id,
                           reason, {})
        event_id = canonical_sha256(
            {
                "kind": "audit",
                "event_type": event_type,
                "job_id": job.job_id,
                "attempt_id": job.active_attempt.attempt_id,
                "job_revision": job.job_revision,
                "reason": reason,
                "discriminator": discriminator,
            }
        )
        tx.add_audit_intent(event_id, event)
        return event

    def _completion_replay(
        self,
        prior: CompletionReceipt,
        fingerprint: str,
        job: AiJob,
        details: Mapping[str, str],
    ) -> CompletionReceipt:
        if prior.fingerprint == fingerprint:
            return prior
        self._audit("job.completion_conflict", job, "COMPLETION_CONFLICT", details)
        raise AiJobError("COMPLETION_CONFLICT", 409, "Conflicting completion.")

    def _describe_outputs(
        self, claim: CompletionClaim
    ) -> dict[str, ArtifactDescriptor | None]:
        return {
            output.artifact_ref: self._d.artifacts.describe(output.artifact_ref)
            for output in claim.outputs
        }

    def _check(self, job: AiJob) -> EligibilityDecision:
        return self._d.eligibility.check(
            scope=job.scope, request_ref=job.active_attempt.request_ref, job_type=job.job_type
        )

    def _eligibility_error(self, decision: EligibilityDecision) -> AiJobError:
        status, code = ELIGIBILITY_ERRORS.get(decision.reason_code or "", (403, "FORBIDDEN_SCOPE"))
        return AiJobError(code, status, public_message(decision.reason_code or ""),
                          retryable=code == "BUDGET_EXCEEDED")

    def _require_worker(self, capability: str, job_id: str) -> None:
        if not self._d.worker_capability.verify(capability, job_id):
            raise AiJobError("WORKER_CAPABILITY_INVALID", 403, "Not permitted.")

    def _get(self, tx: AiJobUnitOfWork, job_id: str, *, for_update: bool = False) -> AiJob:
        job = tx.get_job(job_id, for_update=for_update)
        if job is None:
            raise _not_found()
        return job

    def _dispatch_message(self, job: AiJob) -> DispatchMessage:
        attempt = job.active_attempt
        return DispatchMessage(
            message_id=self._d.ids.new_id("msg"),
            job_id=job.job_id,
            attempt_id=attempt.attempt_id,
            attempt_number=attempt.attempt_number,
            job_type=job.job_type,
            request_ref=attempt.request_ref,
        )

    def _owned_descriptors(
        self,
        job: AiJob,
        claim: CompletionClaim,
        descriptors: Mapping[str, ArtifactDescriptor | None],
    ) -> tuple[ArtifactDescriptor, ...]:
        """Outputs this worker may affect: same organization and produced by this job/attempt.
        Unknown or foreign refs are never mutated, even on rejection paths."""

        owned: list[ArtifactDescriptor] = []
        for output in claim.outputs:
            descriptor = descriptors.get(output.artifact_ref)
            if descriptor is not None and _produced_by(descriptor, job, claim.attempt_id):
                owned.append(descriptor)
        return tuple(owned)

    def _normalise_claim(
        self, claim: CompletionClaim, details: dict[str, str]
    ) -> CompletionClaim | None:
        """Validate the internal worker outcome before it can affect state. Unknown or
        malformed provider failure codes map to ``PROVIDER_ERROR`` (original only hashed)."""

        try:
            kind = OutcomeKind(claim.kind)
            moderation = Moderation(claim.moderation)
        except ValueError:
            return None
        if not isinstance(claim.retryable, bool):
            return None
        if kind is OutcomeKind.SUCCESS:
            if claim.failure_code is not None:
                return None
            return replace(claim, kind=kind, moderation=moderation)
        if claim.outputs:
            return None
        code = claim.failure_code
        if code is not None and not isinstance(code, str):
            details["provider_code_sha256"] = sha256(repr(code).encode("utf-8")).hexdigest()
            return None
        if code not in WORKER_FAILURE_CODES:
            details["provider_code_sha256"] = sha256(str(code).encode("utf-8")).hexdigest()
            code = "PROVIDER_ERROR"
        return replace(claim, kind=kind, moderation=moderation, failure_code=code)

    def _quarantine(self, refs: tuple[str, ...], reason: str) -> None:
        if refs:
            self._d.artifacts.quarantine(refs, reason)

    def _audit(
        self,
        event_type: str,
        job: AiJob,
        reason: str | None = None,
        details: Mapping[str, str] | None = None,
    ) -> None:
        self._d.audit.record(
            AuditEvent(event_type, job.organization_id, job.job_id, job.correlation_id, reason,
                       dict(details or {}))
        )


# Role allowlists (candidate). Order is the projection order.
TEACHER_FIELDS = (
    "job_id", "organization_id", "job_type", "job_revision", "request_ref", "attempt_id",
    "attempt_number", "state", "result_disposition", "created_at", "updated_at",
    "correlation_id", "started_at", "completed_at", "progress", "result_refs", "failure",
    "poll_after_ms",
)
ADMIN_FIELDS = TEACHER_FIELDS
DEVICE_FIELDS = ("job_id", "job_type", "job_revision", "state", "progress", "failure",
                 "poll_after_ms")


def project_job(
    job: AiJob, role: PrincipalRole, expose_results: bool, poll_after: int | None
) -> dict[str, object]:
    attempt = job.active_attempt
    failure: dict[str, object] | None = None
    if job.failure is not None:
        failure = {
            "code": job.failure.code,
            "retryable": job.failure.retryable,
            "public_message": job.failure.public_message,
            "attempts_remaining": job.failure.attempts_remaining,
        }
    full: dict[str, object] = {
        "job_id": job.job_id,
        "organization_id": job.organization_id,
        "job_type": job.job_type,
        "job_revision": job.job_revision,
        "request_ref": {
            "request_id": attempt.request_ref.request_id,
            "request_revision": attempt.request_ref.request_revision,
            "input_hash": attempt.request_ref.input_hash,
            "context_revision": attempt.request_ref.context_revision,
        },
        "attempt_id": attempt.attempt_id,
        "attempt_number": attempt.attempt_number,
        "state": str(job.state),
        "result_disposition": (
            str(job.result_disposition) if job.result_disposition is not None else None
        ),
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "correlation_id": job.correlation_id,
        "started_at": attempt.started_at,
        "completed_at": job.completed_at,
        "progress": {
            "kind": str(job.progress.kind),
            "value": job.progress.value,
            "stage_label": job.progress.stage_label,
        },
        "result_refs": (
            [{"artifact_ref": r.artifact_ref, "sha256": r.sha256} for r in job.result_refs]
            if expose_results
            else []
        ),
        "failure": failure,
        "poll_after_ms": poll_after,
    }
    if role is PrincipalRole.DEVICE:
        view = {name: full[name] for name in DEVICE_FIELDS}
        if failure is not None:
            view["failure"] = {k: failure[k] for k in ("code", "retryable", "public_message")}
        return view
    allowed = TEACHER_FIELDS if role is PrincipalRole.TEACHER else ADMIN_FIELDS
    return {name: full[name] for name in allowed}


def _produced_by(descriptor: ArtifactDescriptor, job: AiJob, attempt_id: str) -> bool:
    return (
        descriptor.organization_id == job.organization_id
        and descriptor.producer_job_id == job.job_id
        and descriptor.producer_attempt_id == attempt_id
    )


_Due = TypeVar("_Due")
_Out = TypeVar("_Out")


def _dispatchable(job: AiJob, message: DispatchMessage) -> bool:
    return job.state is JobState.QUEUED and job.active_attempt.attempt_id == message.attempt_id


def _retry_due(job: AiJob, scheduled_for_attempt: int, now: datetime) -> bool:
    return (
        job.state is JobState.FAILED_RETRYABLE
        and job.active_attempt.attempt_number == scheduled_for_attempt
        and job.retry_not_before is not None
        and now >= job.retry_not_before
    )


def _key_discriminator(key: CommandScopeKey) -> str:
    return canonical_sha256(
        [key.organization_id, key.principal_id, key.contract_name, key.target_id,
         key.idempotency_key]
    )


def _notice_matches(notice: CancellationNotice, job: AiJob) -> bool:
    if notice.session_id is not None and job.scope.session_id == notice.session_id:
        return True
    if notice.job_type is not None and job.job_type == notice.job_type:
        return True
    return notice.subject_ref is not None and notice.subject_ref in job.scope.subject_refs


def _etag_candidates(header: str) -> set[str]:
    return {part.strip().removeprefix("W/") for part in header.split(",") if part.strip()}


def _ms(value: int) -> timedelta:
    return timedelta(milliseconds=value)


__all__ = [
    "CANCEL_CONTRACT",
    "CREATE_CONTRACT",
    "DECISION_ROUNDS",
    "DEFAULT_DISPATCH_OWNER",
    "FIXTURE_DISPATCH_POLICY",
    "DEVICE_FIELDS",
    "FIXTURE_POLL_POLICY",
    "FIXTURE_RETRY_POLICY",
    "TEACHER_FIELDS",
    "WORKER_FAILURE_CODES",
    "AiJobDependencies",
    "AiJobError",
    "AiJobService",
    "CancelJobCommand",
    "CommandResult",
    "CreateJobCommand",
    "DispatchPolicy",
    "JobStatusResult",
    "QueueUnavailable",
    "StartResult",
    "project_job",
    "public_message",
]
