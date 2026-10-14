"""Fixture harness wiring the BE2-01 service to deterministic fakes (tests/runner only)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from hashlib import sha256

from sketch2life.application.ports.ai_jobs import (
    AuthorizationAction,
    DispatchMessage,
    Principal,
    PrincipalRole,
)
from sketch2life.application.services.ai_jobs import (
    AiJobDependencies,
    AiJobService,
    CreateJobCommand,
)
from sketch2life.application.services.provider_copy_lifecycle import (
    ProviderCopyLifecycleService,
)
from sketch2life.domain.ai_jobs.completion import CompletionClaim, Moderation, OutcomeKind
from sketch2life.domain.ai_jobs.model import RequestRef
from sketch2life.infrastructure.ai_jobs.fakes import (
    FakeArtifacts,
    FakeAudit,
    FakeAuthorization,
    FakeClock,
    FakeEligibility,
    FakeProvider,
    FakeProviderCopyAdapter,
    FakeQueue,
    FakeWorker,
    FakeWorkerCapability,
    InMemoryAiJobStore,
    InMemoryProviderCopyRegistry,
    SequentialIds,
)

FIXTURE_START = datetime(2026, 10, 14, 13, 0, tzinfo=UTC)
ORG = "org_fx_school_a"
OTHER_ORG = "org_fx_school_b"
SESSION = "session_fx_001"
SUBJECT = "child_fx_001"
TARGET = "assistance_fx_001"
JOB_TYPE = "sketch_assistance"
ALL_ACTIONS = {AuthorizationAction.CREATE_JOB, AuthorizationAction.READ_JOB,
               AuthorizationAction.CANCEL_JOB}

TEACHER = Principal("teacher_fx_001", ORG, PrincipalRole.TEACHER)
TEACHER_2 = Principal("teacher_fx_002", ORG, PrincipalRole.TEACHER)
ADMIN = Principal("admin_fx_001", ORG, PrincipalRole.ADMIN)
DEVICE = Principal("device_fx_001", ORG, PrincipalRole.DEVICE)
OUTSIDER = Principal("teacher_fx_900", OTHER_ORG, PrincipalRole.TEACHER)
UNGRANTED = Principal("teacher_fx_003", ORG, PrincipalRole.TEACHER)


def input_hash(label: str) -> str:
    return sha256(f"synthetic-input:{label}".encode()).hexdigest()


def request_ref(label: str = "req_fx_001", revision: int = 1, context: int = 1) -> RequestRef:
    return RequestRef(label, revision, input_hash(f"{label}:{revision}"), context)


@dataclass
class FixtureHarness:
    clock: FakeClock
    ids: SequentialIds
    store: InMemoryAiJobStore
    authorization: FakeAuthorization
    eligibility: FakeEligibility
    artifacts: FakeArtifacts
    audit: FakeAudit
    queue: FakeQueue
    capabilities: FakeWorkerCapability
    service: AiJobService
    copy_registry: InMemoryProviderCopyRegistry
    copy_adapter: FakeProviderCopyAdapter
    copy_service: ProviderCopyLifecycleService
    scripted: dict[tuple[str, int], CompletionClaim] = field(default_factory=dict)

    def create(
        self,
        principal: Principal = TEACHER,
        *,
        key: str = "idem_fx_001",
        ref: RequestRef | None = None,
        target: str = TARGET,
        job_type: str = JOB_TYPE,
        session_id: str | None = SESSION,
        subjects: tuple[str, ...] = (SUBJECT,),
        correlation_id: str = "corr_fx_001",
    ) -> CreateJobCommand:
        return CreateJobCommand(
            principal=principal,
            idempotency_key=key,
            job_type=job_type,
            target_id=target,
            purpose_code="purpose_fx_ai_assistance",
            session_id=session_id,
            subject_refs=subjects,
            request_ref=ref or request_ref(),
            correlation_id=correlation_id,
        )

    def success_claim(self, message: DispatchMessage, *, body: bytes = b"synthetic-output",
                      moderation: Moderation = Moderation.PASSED) -> CompletionClaim:
        output = self.artifacts.put(ORG, body + message.attempt_id.encode(),
                                    job_id=message.job_id, attempt_id=message.attempt_id)
        return CompletionClaim(
            job_id=message.job_id,
            attempt_id=message.attempt_id,
            expected_request_revision=message.request_ref.request_revision,
            input_hash=message.request_ref.input_hash,
            context_revision=message.request_ref.context_revision,
            kind=OutcomeKind.SUCCESS,
            outputs=(output,),
            moderation=moderation,
        )

    def failure_claim(self, message: DispatchMessage, *, code: str = "PROVIDER_UNAVAILABLE",
                      retryable: bool = True, diagnostic: str | None = None) -> CompletionClaim:
        return CompletionClaim(
            job_id=message.job_id,
            attempt_id=message.attempt_id,
            expected_request_revision=message.request_ref.request_revision,
            input_hash=message.request_ref.input_hash,
            context_revision=message.request_ref.context_revision,
            kind=OutcomeKind.FAILURE,
            failure_code=code,
            retryable=retryable,
            diagnostic=diagnostic,
        )

    def worker(self, provider: FakeProvider) -> FakeWorker:
        return FakeWorker(self.service, self.queue, provider, self.capabilities)

    def capability(self, job_id: str) -> str:
        return self.capabilities.issue(job_id)

    def next_message(self) -> DispatchMessage:
        self.service.dispatch_outbox()
        message = self.queue.receive()
        if message is None:
            raise AssertionError("no dispatch message available")
        return message

    def start_next(self) -> DispatchMessage:
        message = self.next_message()
        started = self.service.start_attempt(
            self.capability(message.job_id), message.job_id, message.attempt_id
        )
        if not started.started:
            raise AssertionError(f"attempt did not start: {started.reason_code}")
        return message


def build_fixture_harness(start: datetime = FIXTURE_START) -> FixtureHarness:
    clock = FakeClock(start)
    ids = SequentialIds()
    store = InMemoryAiJobStore()
    authorization = FakeAuthorization()
    eligibility = FakeEligibility()
    artifacts = FakeArtifacts()
    audit = FakeAudit()
    queue = FakeQueue()
    capabilities = FakeWorkerCapability()
    service = AiJobService(
        AiJobDependencies(
            repository=store,
            authorization=authorization,
            eligibility=eligibility,
            worker_capability=capabilities,
            clock=clock,
            ids=ids,
            artifacts=artifacts,
            audit=audit,
            queue=queue,
        )
    )
    for principal in (TEACHER, TEACHER_2, ADMIN, OUTSIDER):
        authorization.grant(principal.principal_id, ALL_ACTIONS)
    authorization.grant(DEVICE.principal_id, {AuthorizationAction.READ_JOB},
                        session_ids={SESSION})
    registry = InMemoryProviderCopyRegistry()
    adapter = FakeProviderCopyAdapter()
    return FixtureHarness(
        clock=clock,
        ids=ids,
        store=store,
        authorization=authorization,
        eligibility=eligibility,
        artifacts=artifacts,
        audit=audit,
        queue=queue,
        capabilities=capabilities,
        service=service,
        copy_registry=registry,
        copy_adapter=adapter,
        copy_service=ProviderCopyLifecycleService(registry, adapter),
    )


__all__ = [
    "ADMIN",
    "DEVICE",
    "FIXTURE_START",
    "JOB_TYPE",
    "ORG",
    "OTHER_ORG",
    "OUTSIDER",
    "SESSION",
    "SUBJECT",
    "TARGET",
    "TEACHER",
    "TEACHER_2",
    "UNGRANTED",
    "FixtureHarness",
    "build_fixture_harness",
    "input_hash",
    "request_ref",
]
