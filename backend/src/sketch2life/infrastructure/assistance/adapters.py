"""BE2-03 A1 adapters over existing BE2-01/BE2-02 ports (no foundation/Vision source edits).

* ``CoordinatedAiJobRepository`` — decorator over any ``AiJobRepository``: each foundation
  transaction runs inside the shared coordinator from fence hold through commit.
* ``AssistanceEligibility`` — request-aware ``EligibilityPort`` decorator whose decision and
  fence come from one coordinator snapshot (state + epoch).
* ``AiJobRepositoryReader`` — read-only job history (every attempt's ``started_at``).
* ``AiJobServicePort`` — scheduling/cancel through the BE2-01 application service.
* ``VisionAnalysisOutcomes`` — authorized current BE2-02 reads through an injected, scoped
  Teacher reader principal (never derived from request data).
* ``AssistancePinPort`` — the BE2-02 ``AssistanceRequestPort`` produced by BE2-03.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager

from sketch2life.application.ports.ai_jobs import (
    AiJobRepository,
    AiJobUnitOfWork,
    EligibilityDecision,
    EligibilityPort,
    Principal,
    PrincipalRole,
)
from sketch2life.application.ports.assistance import (
    AnalysisOutcome,
    JobCreateKind,
    JobCreateOutcome,
    JobCreateRequest,
    JobEvidence,
)
from sketch2life.application.ports.vision_analysis import (
    AnalysisRepository,
    AnalysisUnitOfWork,
    CorrectionReceipt,
    CorrectionScopeKey,
)
from sketch2life.application.services.ai_jobs import (
    AiJobError,
    AiJobService,
    CancelJobCommand,
    CreateJobCommand,
)
from sketch2life.application.services.assistance import AssistanceService
from sketch2life.application.services.vision_analysis import (
    VisionAnalysisError,
    VisionAnalysisService,
)
from sketch2life.domain.ai_jobs.model import TERMINAL_STATES, JobScope, RequestRef
from sketch2life.domain.assistance import RequestStatus
from sketch2life.domain.vision_analysis import (
    VISION_ANALYSIS_JOB_TYPE,
    AnalysisHead,
    AssistancePin,
    InvalidationIntent,
    MeaningCorrection,
    ProviderResultRecord,
    VisionObservation,
)
from sketch2life.infrastructure.ai_jobs.fakes import FakeOwnerFences
from sketch2life.infrastructure.assistance.fakes import (
    AssistanceCommitCoordinator,
    CoordinationError,
    InMemoryAssistanceStore,
    analysis_fence_scope,
)

_INELIGIBLE = {
    RequestStatus.CANCELLED: "CANCELLED_BY_TEACHER",
    RequestStatus.STALE: "CONTEXT_CHANGED",
}


class SimulatedLostReply(RuntimeError):
    """The BE2-01 create committed but its reply never reached the scheduler (R08a)."""


class CoordinatedAiJobRepository:
    def __init__(self, inner: AiJobRepository, coordinator: AssistanceCommitCoordinator) -> None:
        self._inner = inner
        self._coordinator = coordinator

    @contextmanager
    def transaction(self) -> Iterator[AiJobUnitOfWork]:
        with self._coordinator.foundation(), self._inner.transaction() as tx:
            yield tx


class _TrackedAnalysisUnit:
    """Delegating BE2-02 unit of work that records whether anything was written."""

    def __init__(self, inner: AnalysisUnitOfWork) -> None:
        self._inner = inner
        self.wrote = False
        self.organizations: set[str] = set()

    def _write(self) -> None:
        self.wrote = True

    def get_head(self, analysis_id: str) -> AnalysisHead | None:
        return self._inner.get_head(analysis_id)

    def find_by_attempt(self, job_id: str, attempt_id: str) -> str | None:
        return self._inner.find_by_attempt(job_id, attempt_id)

    def insert_head(self, head: AnalysisHead) -> None:
        self._write()
        self.organizations.add(head.organization_id)
        self._inner.insert_head(head)

    def cas_head(self, *, expected_revision: int, head: AnalysisHead) -> None:
        self._write()
        self.organizations.add(head.organization_id)
        self._inner.cas_head(expected_revision=expected_revision, head=head)

    def insert_observation(self, observation: VisionObservation) -> None:
        self._write()
        self._inner.insert_observation(observation)

    def get_observation(self, analysis_id: str) -> VisionObservation | None:
        return self._inner.get_observation(analysis_id)

    def insert_provider_result(self, record: ProviderResultRecord) -> None:
        self._write()
        self._inner.insert_provider_result(record)

    def get_provider_result(self, result_ref: str) -> ProviderResultRecord | None:
        return self._inner.get_provider_result(result_ref)

    def append_correction(self, correction: MeaningCorrection) -> None:
        self._write()
        self._inner.append_correction(correction)

    def get_correction(self, correction_id: str) -> MeaningCorrection | None:
        return self._inner.get_correction(correction_id)

    def list_corrections(self, analysis_id: str) -> tuple[MeaningCorrection, ...]:
        return self._inner.list_corrections(analysis_id)

    def get_receipt(self, key: CorrectionScopeKey) -> CorrectionReceipt | None:
        return self._inner.get_receipt(key)

    def put_receipt(self, receipt: CorrectionReceipt) -> None:
        self._write()
        self._inner.put_receipt(receipt)

    def add_invalidation(self, intent: InvalidationIntent) -> None:
        self._write()
        self._inner.add_invalidation(intent)

    def notice_seen(self, notice_id: str) -> bool:
        return self._inner.notice_seen(notice_id)

    def record_notice(self, notice_id: str) -> None:
        self._write()
        self._inner.record_notice(notice_id)


class CoordinatedAnalysisRepository:
    """A1-CR03-F2: each BE2-02 transaction is one coordinated unit, and a committed write
    bumps the analysis epoch before the unit releases, so the commit and its epoch move are
    atomic with respect to every BE2-03 decision/commit. Vision source is unchanged."""

    def __init__(self, inner: AnalysisRepository, coordinator: AssistanceCommitCoordinator,
                 fences: FakeOwnerFences, *, default_organization_id: str) -> None:
        self._inner = inner
        self._coordinator = coordinator
        self._fences = fences
        self._default_organization_id = default_organization_id

    @contextmanager
    def transaction(self) -> Iterator[AnalysisUnitOfWork]:
        with self._coordinator.vision():
            with self._inner.transaction() as tx:
                tracked = _TrackedAnalysisUnit(tx)
                yield tracked
            # Reached only after the inner commit; a rolled-back unit bumps nothing.
            if tracked.wrote:
                for organization_id in sorted(tracked.organizations
                                              or {self._default_organization_id}):
                    self._fences.bump(analysis_fence_scope(organization_id))


class AssistanceEligibility:
    def __init__(self, owner: EligibilityPort, requests: InMemoryAssistanceStore,
                 coordinator: AssistanceCommitCoordinator) -> None:
        self._owner = owner
        self._requests = requests
        self._coordinator = coordinator
        self.after_decision: Callable[[], object] | None = None
        self.decisions = 0

    def check(self, *, scope: JobScope, request_ref: RequestRef, job_type: str) -> (
        EligibilityDecision
    ):
        def snapshot() -> EligibilityDecision:
            decision = self._owner.check(scope=scope, request_ref=request_ref, job_type=job_type)
            if job_type != VISION_ANALYSIS_JOB_TYPE:
                return decision
            request = self._requests.peek(request_ref.request_id)
            if request is None or request.facts.organization_id != scope.organization_id:
                return EligibilityDecision(False, "REQUEST_NOT_FOUND",
                                           decision.current_context_revision, decision.fence)
            if request.request_revision != request_ref.request_revision or (
                request.status in _INELIGIBLE
            ):
                reason = _INELIGIBLE.get(request.status, "CONTEXT_CHANGED")
                if request.cancelled_by is not None and request.cancelled_by.kind == "device":
                    reason = "CANCELLED_BY_CHILD"
                return EligibilityDecision(False, reason, decision.current_context_revision,
                                           decision.fence)
            return decision

        result = self._coordinator.read(snapshot)
        assert isinstance(result, EligibilityDecision)
        self.decisions += 1
        hook = self.after_decision
        if hook is not None:
            self.after_decision = None
            hook()
        return result


class AiJobRepositoryReader:
    """Trusted read-only history; never calls a mutating unit-of-work method."""

    def __init__(self, repository: AiJobRepository) -> None:
        self._repository = repository
        self.fail_next = False

    def evidence(self, organization_id: str, assistance_id: str,
                 known_job_ids: tuple[str, ...]) -> tuple[JobEvidence, ...] | None:
        if self.fail_next:
            self.fail_next = False
            return None
        try:
            with self._repository.transaction() as tx:
                jobs = {}
                for job_id in known_job_ids:
                    job = tx.get_job(job_id)
                    if job is None:
                        return None
                    jobs[job.job_id] = job
                for job in tx.list_jobs():
                    if (job.organization_id == organization_id
                            and job.job_type == VISION_ANALYSIS_JOB_TYPE
                            and job.scope.target_id == assistance_id):
                        jobs[job.job_id] = job
        except CoordinationError:
            raise  # a protocol violation is never reported as unknown evidence
        except Exception:  # unreadable history is unknown evidence, never "not started"
            return None
        return tuple(
            JobEvidence(
                job_id=job.job_id,
                state=str(job.state),
                job_revision=job.job_revision,
                terminal=job.state in TERMINAL_STATES,
                any_attempt_started=any(a.started_at is not None for a in job.attempts),
                active_attempt_id=job.active_attempt.attempt_id,
                request_revision=job.active_attempt.request_ref.request_revision,
            )
            for job in sorted(jobs.values(), key=lambda j: j.job_id)
        )


class AiJobServicePort:
    """Scheduling/cancel through BE2-01; no queue/broker call happens in ``create``."""

    def __init__(self, service: AiJobService) -> None:
        self._service = service
        self.lose_next_reply = False
        self.creates = 0

    def create(self, request: JobCreateRequest) -> JobCreateOutcome:
        self.creates += 1
        try:
            result = self._service.create_job(CreateJobCommand(
                principal=request.principal,
                idempotency_key=request.idempotency_key,
                job_type=request.job_type,
                target_id=request.target_id,
                purpose_code=request.purpose_code,
                session_id=request.session_id,
                subject_refs=request.subject_refs,
                request_ref=RequestRef(request.request_id, request.request_revision,
                                       request.input_hash, request.context_revision),
                correlation_id=request.correlation_id,
            ))
        except AiJobError as exc:
            kind = JobCreateKind.RETRY if exc.retryable and exc.code != "BUDGET_EXCEEDED" \
                else JobCreateKind.REFUSED
            return JobCreateOutcome(kind, None, exc.code)
        if self.lose_next_reply:
            self.lose_next_reply = False
            raise SimulatedLostReply(result.job_id)
        return JobCreateOutcome(JobCreateKind.CREATED, result.job_id)

    def cancel(self, principal: Principal, job_id: str, expected_job_revision: int) -> str:
        try:
            self._service.cancel_job(CancelJobCommand(
                principal=principal,
                idempotency_key=f"assist-cleanup:{job_id}:{expected_job_revision}",
                job_id=job_id,
                expected_job_revision=expected_job_revision,
                reason_code="CANCELLED_BY_TEACHER" if principal.role is PrincipalRole.TEACHER
                else "CANCELLED_BY_CHILD",
            ))
        except AiJobError as exc:
            return exc.code
        return "cancelled"


class VisionAnalysisOutcomes:
    def __init__(self, service: VisionAnalysisService, repository: AnalysisRepository,
                 reader: Principal) -> None:
        if reader.role is not PrincipalRole.TEACHER:
            raise ValueError("the injected analysis reader must be a scoped Teacher")
        self._service = service
        self._repository = repository
        self._reader = reader

    def for_attempt(self, organization_id: str, job_id: str,
                    attempt_id: str) -> AnalysisOutcome | None:
        with self._repository.transaction() as tx:
            analysis_id = tx.find_by_attempt(job_id, attempt_id)
        return None if analysis_id is None else self.current(organization_id, analysis_id)

    def current(self, organization_id: str, analysis_id: str) -> AnalysisOutcome | None:
        if self._reader.organization_id != organization_id:
            return None
        try:
            record = self._service.analysis_record(self._reader, analysis_id)
            meaning = self._service.downstream_meaning(self._reader, analysis_id)
        except VisionAnalysisError:
            return None
        candidate = record["candidate"]
        source = record["source_binding"]
        assert isinstance(candidate, dict) and isinstance(source, dict)
        checkpoint, render = source["checkpoint"], source["render"]
        assert isinstance(checkpoint, dict) and isinstance(render, dict)
        return AnalysisOutcome(
            analysis_id=str(record["analysis_id"]),
            analysis_revision=int(str(record["analysis_revision"])),
            accepted_status=str(record["accepted_status"]),
            meaning_state=str(meaning.state),
            assistance_id=str(candidate["assistance_id"]),
            request_revision=int(str(candidate["expected_request_revision"])),
            job_id=str(candidate["job_id"]),
            attempt_id=str(candidate["job_attempt_id"]),
            snapshot_ref=str(source["input_snapshot_ref"]),
            checkpoint_id=str(checkpoint["checkpoint_id"]),
            checkpoint_checksum=str(checkpoint["checksum_sha256"]),
            render_sha256=str(render["render_sha256"]),
            context_revision=int(str(candidate["context_revision"])),
        )


class AssistancePinPort:
    def __init__(self, service: Callable[[], AssistanceService]) -> None:
        self._service = service

    def get(self, assistance_id: str) -> AssistancePin | None:
        return self._service().pin(assistance_id)


__all__ = [
    "AiJobRepositoryReader",
    "AiJobServicePort",
    "AssistanceEligibility",
    "AssistancePinPort",
    "CoordinatedAiJobRepository",
    "CoordinatedAnalysisRepository",
    "SimulatedLostReply",
    "VisionAnalysisOutcomes",
]
