"""BE2-01 Phase A job orchestration: create, dispatch, start, progress, completion, retry,
cancel, owner notices and CMD-44 status query (candidate; fake-port verified only).

Guard order follows SRS B19.11/B22.1/B22.3: principal + disclosure authority, receipt lookup,
then (new mutations only) current eligibility, semantic dedup and one atomic commit.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import timedelta
from hashlib import sha256

from sketch2life.application.ports.ai_jobs import (
    AiJobRepository,
    AiJobUnitOfWork,
    ArtifactDescriptor,
    ArtifactPort,
    AuditEvent,
    AuditPort,
    AuthorizationAction,
    AuthorizationPort,
    CancellationNotice,
    ClockPort,
    CommandReceipt,
    CommandScopeKey,
    CompletionReceipt,
    DispatchMessage,
    DispatchQueuePort,
    EligibilityDecision,
    EligibilityPort,
    IdGeneratorPort,
    Principal,
    PrincipalRole,
    SemanticRequestKey,
    WorkerCapabilityVerifier,
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
}
GENERIC_PUBLIC_MESSAGE = "The AI step could not finish."
# Guard verdicts that leave the active attempt completable: no artifact state change (R03a).
TEMPORARY_VERDICTS = frozenset({PreconditionVerdict.INVALID_STATE,
                                PreconditionVerdict.INPUT_MISMATCH})
# Failure codes a worker may report verbatim; anything else maps to PROVIDER_ERROR.
WORKER_FAILURE_CODES = frozenset(
    {"PROVIDER_TIMEOUT", "PROVIDER_UNAVAILABLE", "PROVIDER_ERROR", "OUTPUT_MALFORMED"}
)


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
    retry_policy: JobRetryPolicy = FIXTURE_RETRY_POLICY
    poll_policy: JobPollPolicy = FIXTURE_POLL_POLICY


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
        if not self._allowed(principal, AuthorizationAction.CREATE_JOB, scope):
            raise AiJobError("FORBIDDEN_SCOPE", 403, "Not permitted for this scope.")
        key = CommandScopeKey(
            principal.organization_id,
            principal.principal_id,
            CREATE_CONTRACT,
            command.target_id,
            command.idempotency_key,
        )
        fingerprint = command.fingerprint()
        now = self._d.clock.now()
        with self._d.repository.transaction() as tx:
            replay = self._replay(tx, principal, key, fingerprint)
            if replay is not None:
                return replay
            eligibility = self._d.eligibility.check(
                scope=scope, request_ref=command.request_ref, job_type=command.job_type
            )
            if not eligibility.eligible:
                raise self._eligibility_error(eligibility)
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
            existing_id = tx.find_semantic(semantic)
            if existing_id is not None:
                existing = tx.get_job(existing_id)
                if existing is None or not self._allowed(
                    principal, AuthorizationAction.READ_JOB, existing.scope
                ):
                    raise _not_found()
                tx.put_command_receipt(
                    CommandReceipt(key, fingerprint, existing.job_id, "deduplicated",
                                   existing.job_revision, now)
                )
                self._audit("job.create.deduplicated", existing)
                return CommandResult(existing.job_id, existing.job_revision, "deduplicated", False)
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
                CommandReceipt(key, fingerprint, job.job_id, "created", job.job_revision, now)
            )
            tx.add_outbox(self._dispatch_message(job))
        self._audit("job.created", job)
        return CommandResult(job.job_id, job.job_revision, "created", False)

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
        with self._d.repository.transaction() as tx:
            job = tx.get_job(command.job_id)
            if job is None or not self._readable(principal, job):
                raise _not_found()
            if not self._allowed(principal, AuthorizationAction.CANCEL_JOB, job.scope):
                raise AiJobError("FORBIDDEN_SCOPE", 403, "Not permitted for this scope.")
            replay = self._replay(tx, principal, key, fingerprint)
            if replay is not None:
                return replay
            if command.expected_job_revision is None:
                raise AiJobError("PRECONDITION_REQUIRED", 428, "If-Match is required.")
            if command.expected_job_revision != job.job_revision:
                raise AiJobError("STALE_AGGREGATE", 412, "The job has changed; reload it.")
            if job.state not in jobs.CANCELLABLE_STATES:
                raise AiJobError("INVALID_STATE", 409, "The job can no longer be cancelled.")
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
        self._audit("job.cancelled", updated, command.reason_code)
        return CommandResult(updated.job_id, updated.job_revision, "cancelled", False)

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
    def dispatch_outbox(self) -> int:
        """Send pending outbox entries; current eligibility is rechecked before enqueue."""

        sent = 0
        denied: list[AiJob] = []
        with self._d.repository.transaction() as tx:
            for message in tx.pending_outbox():
                job = tx.get_job(message.job_id)
                if (
                    job is None
                    or job.state is not JobState.QUEUED
                    or job.active_attempt.attempt_id != message.attempt_id
                ):
                    tx.mark_dispatched(message.message_id)
                    continue
                eligibility = self._check(job)
                if not eligibility.eligible:
                    reason = eligibility.reason_code or "CONSENT_REVOKED"
                    updated = jobs.cancel(job, reason_code=reason,
                                          public_message=public_message(reason),
                                          now=self._d.clock.now())
                    tx.cas_job(expected_revision=job.job_revision, job=updated)
                    tx.mark_dispatched(message.message_id)
                    denied.append(updated)
                    continue
                try:
                    self._d.queue.enqueue(message)
                except QueueUnavailable:
                    continue
                tx.mark_dispatched(message.message_id)
                sent += 1
        for job in denied:
            self._audit("job.dispatch_denied", job, job.failure.code if job.failure else None)
        return sent

    def start_attempt(self, capability: str, job_id: str, attempt_id: str) -> StartResult:
        self._require_worker(capability, job_id)
        with self._d.repository.transaction() as tx:
            job = self._get(tx, job_id)
            if job.active_attempt.attempt_id != attempt_id:
                return StartResult(False, "ATTEMPT_NOT_ACTIVE")
            if job.state is JobState.RUNNING:
                return StartResult(False, "DUPLICATE_DELIVERY")
            if job.state is not JobState.QUEUED:
                return StartResult(False, "JOB_NOT_QUEUED")
            eligibility = self._check(job)
            if not eligibility.eligible:
                reason = eligibility.reason_code or "CONSENT_REVOKED"
                updated = jobs.cancel(
                    job, reason_code=reason, public_message=public_message(reason),
                    now=self._d.clock.now(),
                )
                tx.cas_job(expected_revision=job.job_revision, job=updated)
                result = StartResult(False, reason)
            else:
                updated = jobs.start_attempt(job, attempt_id, self._d.clock.now())
                tx.cas_job(expected_revision=job.job_revision, job=updated)
                result = StartResult(True, None)
        self._audit("job.start" if result.started else "job.start_denied", updated,
                    result.reason_code)
        return result

    def report_progress(
        self, capability: str, job_id: str, attempt_id: str, progress: JobProgress
    ) -> bool:
        self._require_worker(capability, job_id)
        with self._d.repository.transaction() as tx:
            job = self._get(tx, job_id)
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
        with self._d.repository.transaction() as tx:
            job = self._get(tx, claim.job_id)
            prior = tx.get_completion_receipt(claim.job_id, claim.attempt_id)
            if prior is not None:
                if prior.fingerprint == fingerprint:
                    return prior
                self._audit("job.completion_conflict", job, "COMPLETION_CONFLICT", details)
                raise AiJobError("COMPLETION_CONFLICT", 409, "Conflicting completion.")
            normalised = self._normalise_claim(claim, details)
            reason: str | None
            if normalised is None:
                updated, disposition, reason = job, ResultDisposition.REJECTED, "MALFORMED_CLAIM"
            else:
                updated, disposition, reason = self._decide_completion(job, normalised)
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
                tx.cas_job(expected_revision=job.job_revision, job=updated)
                tx.put_completion_receipt(receipt)
        details["disposition"] = str(disposition)
        self._audit("job.completion" if authoritative else "job.completion_rejected", updated,
                    reason, details)
        return receipt

    def expire_overdue_attempts(self) -> tuple[str, ...]:
        now = self._d.clock.now()
        expired: list[str] = []
        with self._d.repository.transaction() as tx:
            for job in tx.list_jobs():
                started = job.started_at
                if job.state is not JobState.RUNNING or started is None:
                    continue
                if now - started < _ms(job.retry_policy.attempt_timeout_ms):
                    continue
                updated = jobs.record_failure(
                    job, job.active_attempt.attempt_id, code="PROVIDER_TIMEOUT",
                    retryable=True, public_message=public_message("PROVIDER_TIMEOUT"), now=now,
                )
                tx.cas_job(expected_revision=job.job_revision, job=updated)
                expired.append(job.job_id)
        return tuple(expired)

    def run_due_retries(self) -> tuple[str, ...]:
        with self._d.repository.transaction() as tx:
            due = [
                (job.job_id, job.active_attempt.attempt_number)
                for job in tx.list_jobs()
                if job.state is JobState.FAILED_RETRYABLE
                and job.retry_not_before is not None
                and job.retry_not_before <= self._d.clock.now()
            ]
        return tuple(job_id for job_id, number in due if self.retry_job(job_id, number))

    def retry_job(self, job_id: str, scheduled_for_attempt: int) -> bool:
        """Scheduled retry callback; stale callbacks (cancelled/advanced jobs) are no-ops."""

        now = self._d.clock.now()
        with self._d.repository.transaction() as tx:
            job = self._get(tx, job_id)
            if (
                job.state is not JobState.FAILED_RETRYABLE
                or job.active_attempt.attempt_number != scheduled_for_attempt
                or job.retry_not_before is None
                or now < job.retry_not_before
            ):
                return False
            eligibility = self._check(job)
            if not eligibility.eligible:
                reason = eligibility.reason_code or "CONSENT_REVOKED"
                updated = jobs.cancel(job, reason_code=reason,
                                      public_message=public_message(reason), now=now)
                tx.cas_job(expected_revision=job.job_revision, job=updated)
                requeued = False
            else:
                updated = jobs.requeue_for_retry(job, new_attempt_id=self._d.ids.new_id("att"),
                                                 now=now)
                tx.cas_job(expected_revision=job.job_revision, job=updated)
                tx.add_outbox(self._dispatch_message(updated))
                requeued = True
        self._audit("job.requeued" if requeued else "job.retry_denied", updated)
        return requeued

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
        self, job: AiJob, claim: CompletionClaim
    ) -> tuple[AiJob, ResultDisposition, str | None]:
        now = self._d.clock.now()
        output_refs = self._owned_refs(job, claim)
        verdict = check_completion_preconditions(job, claim)
        if verdict is not PreconditionVerdict.PROCEED:
            if verdict is PreconditionVerdict.INPUT_MISMATCH:
                self._audit("job.completion_input_mismatch", job, str(verdict))
            if verdict not in TEMPORARY_VERDICTS:
                # The attempt can no longer complete: its own outputs are final rejects.
                self._quarantine(output_refs, str(verdict))
            return job, VERDICT_DISPOSITION[verdict], str(verdict)
        attempt_id = claim.attempt_id
        eligibility = self._check(job)
        if not eligibility.eligible:
            reason = eligibility.reason_code or "CONSENT_REVOKED"
            self._quarantine(output_refs, reason)
            updated = jobs.cancel(job, reason_code=reason, public_message=public_message(reason),
                                  now=now)
            return updated, ResultDisposition.REJECTED, reason
        if claim.kind is OutcomeKind.FAILURE:
            code = claim.failure_code or "PROVIDER_ERROR"
            updated = jobs.record_failure(job, attempt_id, code=code, retryable=claim.retryable,
                                          public_message=public_message(code), now=now)
            return updated, ResultDisposition.ACCEPTED, code
        if claim.moderation is Moderation.UNSAFE:
            self._quarantine(output_refs, "UNSAFE_CONTENT")
            updated = jobs.block_unsafe(job, attempt_id,
                                        public_message=public_message("UNSAFE_CONTENT"), now=now)
            return updated, ResultDisposition.REJECTED, "UNSAFE_CONTENT"
        results = self._validated_outputs(job, claim)
        if results is None:
            self._quarantine(output_refs, "OUTPUT_MALFORMED")
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
        self, job: AiJob, claim: CompletionClaim
    ) -> tuple[ResultRef, ...] | None:
        if not claim.outputs:
            return None
        refs: list[ResultRef] = []
        for output in claim.outputs:
            descriptor = self._d.artifacts.describe(output.artifact_ref)
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

    def _allowed(self, principal: Principal, action: AuthorizationAction, scope: JobScope) -> bool:
        if principal.organization_id != scope.organization_id:
            return False
        return self._d.authorization.decide(principal, action, scope).allowed

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

    def _get(self, tx: AiJobUnitOfWork, job_id: str) -> AiJob:
        job = tx.get_job(job_id)
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

    def _owned_refs(self, job: AiJob, claim: CompletionClaim) -> tuple[str, ...]:
        """Refs this worker may affect: same organization and produced by this job/attempt.
        Unknown or foreign refs are never mutated, even on rejection paths."""

        owned: list[str] = []
        for output in claim.outputs:
            descriptor = self._d.artifacts.describe(output.artifact_ref)
            if descriptor is not None and _produced_by(descriptor, job, claim.attempt_id):
                owned.append(output.artifact_ref)
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
    "JobStatusResult",
    "QueueUnavailable",
    "StartResult",
    "project_job",
    "public_message",
]
