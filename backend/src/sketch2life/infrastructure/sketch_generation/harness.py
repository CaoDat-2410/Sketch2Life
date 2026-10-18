"""BE2-04 SK1 synthetic harnesses (FIXTURE_ONLY; no provider, network, Studio or database).

* ``build_sketch_unit_harness`` — real BE2-01 ``AiJobService`` over its fakes, a scripted
  handoff reader and ``CounterDecisionPort``: service-level tests without BE2-02/03.
* ``build_sketch_chain_harness`` — plan §6.5: rebuilds the A1 composition from public A1
  parts (``build_assistance_harness`` is neither called nor changed), with ONE
  ``CoordinatedSketchArtifactPort`` shared by the A1-facing and the sketch ``AiJobService``.
* ``JobTypeRouter`` — the only consumer of the shared queue in chain/race tests (SK-PR02).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from hashlib import sha256

from sketch2life.application.ports.ai_jobs import (
    AuthorizationAction,
    CompletionReceipt,
    Principal,
    WorkerDispatchEnvelope,
)
from sketch2life.application.ports.assistance import CanvasFacts, GroupRoster
from sketch2life.application.ports.sketch_generation import SketchHandoffV1
from sketch2life.application.services.ai_jobs import (
    FIXTURE_RETRY_POLICY,
    AiJobDependencies,
    AiJobError,
    AiJobService,
)
from sketch2life.application.services.assistance import (
    AssistanceDependencies,
    AssistanceService,
)
from sketch2life.application.services.provider_copy_lifecycle import ProviderCopyLifecycleService
from sketch2life.application.services.sketch_generation import (
    OpenResult,
    SketchDependencies,
    SketchGenerationService,
    event_view,
)
from sketch2life.application.services.vision_analysis import (
    VisionAnalysisDependencies,
    VisionAnalysisService,
)
from sketch2life.domain.assistance import Contributor
from sketch2life.domain.sketch_proposal import (
    SKETCH_JOB_TYPE,
    HandoffBinding,
    HandoffKind,
    MeaningBasis,
    SketchPolicySnapshot,
    SketchProposal,
    SourcePin,
)
from sketch2life.domain.vision_analysis import VISION_ANALYSIS_JOB_TYPE
from sketch2life.domain.vision_context import FIXTURE_AGE_BAND_POLICY
from sketch2life.infrastructure.ai_jobs.fakes import (
    FakeArtifacts,
    FakeAudit,
    FakeAuthorization,
    FakeClock,
    FakeEligibility,
    FakeOwnerFences,
    FakeProviderCopyAdapter,
    FakeQueue,
    FakeWorkerCapability,
    InMemoryAiJobStore,
    InMemoryProviderCopyRegistry,
    SequentialIds,
    artifact_fence_scope,
)
from sketch2life.infrastructure.assistance.adapters import (
    AiJobRepositoryReader,
    AiJobServicePort,
    AssistanceEligibility,
    AssistancePinPort,
    CoordinatedAiJobRepository,
    CoordinatedAnalysisRepository,
    VisionAnalysisOutcomes,
)
from sketch2life.infrastructure.assistance.fakes import (
    AssistanceCommitCoordinator,
    DeviceBinding,
    FakeAssistanceAuthority,
    FakeAssistanceOwner,
    FakeAssistanceSource,
    FixtureAssistancePolicy,
    HookedOwnerFences,
    InMemoryAssistanceStore,
    RecordingSketchStage,
    TeacherScope,
    fixture_policy,
)
from sketch2life.infrastructure.assistance.harness import (
    CANVAS_G,
    CANVAS_P,
    CHILD_A,
    CHILD_B,
    CHILD_C,
    CLASS,
    CONTEXT_REVISION,
    DEVICE_A,
    DEVICE_GA,
    DEVICE_GB,
    FIXTURE_START,
    GROUP,
    LEVEL_2,
    ORG,
    OTHER_CLASS_TEACHER,
    OUTSIDER,
    PURPOSE,
    READER,
    SESSION,
    TEACHER,
    AssistanceHarness,
    make_source,
)
from sketch2life.infrastructure.sketch_generation.adapters import (
    AiJobSketchPort,
    AiJobSketchReader,
    ArtifactAuditEntry,
    ArtifactPortView,
    AssistanceHandoffReader,
    CoordinatedSketchArtifactPort,
    CoordinatedSketchRepository,
    FenceDecisionPort,
    SketchChainEligibility,
    SketchCopyRegistrar,
    SketchEligibility,
    SketchProviderAdapter,
    SketchStageAdapter,
    cleanup_sink,
    sketch_policy_fence_scope,
)
from sketch2life.infrastructure.sketch_generation.fakes import (
    CounterDecisionPort,
    DeviceGrant,
    FakeSketchAuthority,
    FixtureDerivedArtifactAdmission,
    FixtureSketchPolicy,
    InMemorySketchStore,
    ScriptedHandoffReader,
    ScriptedSketchGenerator,
    default_outcome,
    fixture_sketch_policy,
)
from sketch2life.infrastructure.vision_analysis.fakes import (
    DeviceBinding as VisionDeviceBinding,
)
from sketch2life.infrastructure.vision_analysis.fakes import (
    FakeAdmission,
    FakeAnalysisAuthority,
    FakeAnalysisContext,
    FakeAnalysisSource,
    FakeVisionContextSource,
    FakeVisionObservationProvider,
    InMemoryAnalysisStore,
    TeacherGrant,
)
from sketch2life.infrastructure.vision_analysis.job_lineage import AiJobRepositoryLineage

ALL_JOB_ACTIONS = frozenset({AuthorizationAction.CREATE_JOB, AuthorizationAction.READ_JOB,
                             AuthorizationAction.CANCEL_JOB})


def _hex(label: str) -> str:
    return sha256(label.encode()).hexdigest()


def _sketch_authority() -> FakeSketchAuthority:
    authority = FakeSketchAuthority()
    authority.teachers[TEACHER.principal_id] = (ORG, frozenset({CLASS}))
    authority.teachers[OTHER_CLASS_TEACHER.principal_id] = (ORG, frozenset({"class_fx_b"}))
    authority.teachers[OUTSIDER.principal_id] = (OUTSIDER.organization_id, frozenset({CLASS}))
    authority.devices[DEVICE_A.principal_id] = DeviceGrant(ORG, SESSION, CHILD_A)
    authority.devices[DEVICE_GA.principal_id] = DeviceGrant(ORG, SESSION, CHILD_A)
    authority.devices[DEVICE_GB.principal_id] = DeviceGrant(ORG, SESSION, CHILD_B)
    return authority


def _copy_lifecycle() -> tuple[InMemoryProviderCopyRegistry, FakeProviderCopyAdapter,
                               ProviderCopyLifecycleService]:
    registry, adapter = InMemoryProviderCopyRegistry(), FakeProviderCopyAdapter()
    return registry, adapter, ProviderCopyLifecycleService(registry, adapter)


# ===================================================================== unit harness
def make_binding(assistance_id: str = "assist_fx_001", *, level: str = LEVEL_2,
                 kind: HandoffKind = HandoffKind.ANALYSIS,
                 audience: tuple[str, ...] = (CHILD_A,), requester: Principal = DEVICE_A,
                 purpose: str = PURPOSE, meaning: MeaningBasis | None = None,
                 request_revision: int = 1, analysis_revision: int = 1,
                 canvas_id: str = CANVAS_P) -> HandoffBinding:
    """Synthetic 04-owned projection for service tests (no BE2-03/02 types)."""

    render_sha = _hex(f"render:{assistance_id}")
    group = audience != (CHILD_A,)
    return HandoffBinding(
        assistance_id=assistance_id, request_revision=request_revision, handoff_kind=kind,
        cache_source_assistance_id="assist_fx_source" if kind is HandoffKind.CACHE_HIT else None,
        analysis_id=f"analysis_{assistance_id}", analysis_revision=analysis_revision,
        vision_job_id=f"job_vision_{assistance_id}", vision_attempt_id=f"att_{assistance_id}",
        organization_id=ORG, class_id=CLASS, session_id=SESSION, canvas_id=canvas_id,
        group_id=GROUP if group else None, target_kind="group" if group else "individual",
        target_ref=GROUP if group else CHILD_A, audience=audience,
        roster_revision=1 if group else None, contributor_participant_id=audience[0],
        purpose_code=purpose,
        source=SourcePin(f"snapshot_{assistance_id}", f"checkpoint_{assistance_id}", 1, 40,
                         _hex(f"checkpoint:{assistance_id}"), f"render_{assistance_id}",
                         render_sha, "image/png", f"admission_{assistance_id}",
                         _hex(f"input:{assistance_id}")),
        context_revision=CONTEXT_REVISION, requested_level=level,
        request_policy_id="fixture.drawing_assistance.v0", request_policy_version="1",
        requester_principal_id=requester.principal_id, requester_kind=str(requester.role),
        assistance_context_digest=_hex(f"context:{assistance_id}"),
        meaning=meaning or MeaningBasis("unconfirmed", None, ()),
    )


@dataclass
class SketchUnitHarness:
    clock: FakeClock
    ids: SequentialIds
    fences: FakeOwnerFences
    job_store: InMemoryAiJobStore
    owner_eligibility: FakeEligibility
    job_authorization: FakeAuthorization
    artifacts: FakeArtifacts
    queue: FakeQueue
    capabilities: FakeWorkerCapability
    jobs: AiJobService
    decision: CounterDecisionPort
    store: InMemorySketchStore
    eligibility: SketchEligibility
    handoffs: ScriptedHandoffReader
    policy: FixtureSketchPolicy
    generator: ScriptedSketchGenerator
    admission: FixtureDerivedArtifactAdmission
    job_port: AiJobSketchPort
    job_reader: AiJobSketchReader
    copy_registry: InMemoryProviderCopyRegistry
    copy_adapter: FakeProviderCopyAdapter
    copies: ProviderCopyLifecycleService
    authority: FakeSketchAuthority
    provider: SketchProviderAdapter
    service: SketchGenerationService

    def add(self, binding: HandoffBinding) -> HandoffBinding:
        self.handoffs.add(SketchHandoffV1(binding))
        return binding

    def open(self, binding: HandoffBinding | None = None) -> OpenResult:
        binding = self.add(binding or make_binding())
        return self.service.open_from_handoff(ORG, binding.assistance_id)

    def proposal(self, proposal_id: str) -> SketchProposal:
        proposal = self.store.peek(proposal_id)
        assert proposal is not None
        return proposal

    def work_once(self, *, crash_after_provider: bool = False) -> (
        CompletionReceipt | str | None
    ):
        """Dispatch, start, run the sketch worker step, complete (no shared queue here)."""

        self.jobs.dispatch_outbox()
        envelope = self.queue.receive()
        if envelope is None:
            return None
        message = envelope.message
        started = self.jobs.start_attempt(envelope.capability, message.job_id,
                                          message.attempt_id)
        if not started.started:
            return started.reason_code
        claim = self.provider.run(message)
        if crash_after_provider:
            return "CRASHED_BEFORE_COMPLETION"
        return self.jobs.accept_completion(envelope.capability, claim)

    def run(self, proposal_id: str) -> SketchProposal:
        self.work_once()
        self.service.reconcile(proposal_id)
        return self.proposal(proposal_id)


def build_sketch_unit_harness(*, policy: SketchPolicySnapshot | None = None,
                              start: datetime = FIXTURE_START) -> SketchUnitHarness:
    clock, ids, fences = FakeClock(start), SequentialIds(), FakeOwnerFences()
    job_store = InMemoryAiJobStore(fences)
    owner_eligibility = FakeEligibility(fences)
    decision = CounterDecisionPort()
    store = InMemorySketchStore(decision, fences,
                                on_invalidation=lambda org: decision.bump(f"org:{org}"))
    eligibility = SketchEligibility(owner_eligibility, store)
    job_authorization = FakeAuthorization(fences)
    for principal in (TEACHER, DEVICE_A, DEVICE_GA, DEVICE_GB):
        job_authorization.grant(principal.principal_id, set(ALL_JOB_ACTIONS),
                                session_ids=None if principal is TEACHER else {SESSION})
    artifacts, queue, capabilities = FakeArtifacts(fences), FakeQueue(), FakeWorkerCapability()
    jobs = AiJobService(AiJobDependencies(
        repository=job_store, authorization=job_authorization, eligibility=eligibility,
        worker_capability=capabilities, clock=clock, ids=ids, artifacts=artifacts,
        audit=FakeAudit(), queue=queue, capability_issuer=capabilities,
        retry_policy=FIXTURE_RETRY_POLICY,
    ))
    handoffs = ScriptedHandoffReader()
    sketch_policy = FixtureSketchPolicy(policy or fixture_sketch_policy())
    generator = ScriptedSketchGenerator()
    admission = FixtureDerivedArtifactAdmission(artifacts)
    job_port, job_reader = AiJobSketchPort(jobs), AiJobSketchReader(job_store)
    registry, copy_adapter, copies = _copy_lifecycle()
    authority = _sketch_authority()
    holder: dict[str, SketchGenerationService] = {}
    provider = SketchProviderAdapter(lambda: holder["service"])
    service = SketchGenerationService(SketchDependencies(
        repository=store, handoffs=handoffs, decision=decision, policy=sketch_policy,
        generator=generator, admission=admission, artifacts=artifacts, jobs=job_port,
        job_reader=job_reader, copies=SketchCopyRegistrar(copies), authority=authority,
        clock=clock, ids=ids, quarantine=cleanup_sink(artifacts),
    ))
    holder["service"] = service
    return SketchUnitHarness(
        clock=clock, ids=ids, fences=fences, job_store=job_store,
        owner_eligibility=owner_eligibility, job_authorization=job_authorization,
        artifacts=artifacts, queue=queue, capabilities=capabilities, jobs=jobs,
        decision=decision, store=store, eligibility=eligibility, handoffs=handoffs,
        policy=sketch_policy, generator=generator, admission=admission, job_port=job_port,
        job_reader=job_reader, copy_registry=registry, copy_adapter=copy_adapter,
        copies=copies, authority=authority, provider=provider, service=service,
    )


# ===================================================================== router (SK-PR02)
@dataclass(frozen=True, slots=True)
class RouteResult:
    job_type: str
    job_id: str
    attempt_id: str
    started: bool
    reason: str | None
    outcome: object = None


class UnknownJobType(RuntimeError):
    """A queue message whose job type has no route; it is redelivered first."""


class JobTypeRouter:
    """Reads ``message.job_type`` BEFORE any start; proceeds only when ``started`` is True."""

    ROUTES = (VISION_ANALYSIS_JOB_TYPE, SKETCH_JOB_TYPE)

    def __init__(self, harness: AssistanceHarness, sketch_jobs: AiJobService,
                 provider: SketchProviderAdapter) -> None:
        self._h = harness
        self._sketch_jobs = sketch_jobs
        self._provider = provider
        self.calls: list[tuple[str, str]] = []
        self.crash_after_provider = False
        self.last_sketch: WorkerDispatchEnvelope | None = None

    def run_next(self) -> RouteResult | None:
        envelope = self._h.queue.receive()
        if envelope is None:
            return None
        message = envelope.message
        if message.job_type == VISION_ANALYSIS_JOB_TYPE:
            return self._vision(envelope)
        if message.job_type == SKETCH_JOB_TYPE:
            return self._sketch(envelope)
        self._h.queue.redeliver(envelope)
        raise UnknownJobType(message.job_type)

    def _start(self, service: AiJobService, envelope: WorkerDispatchEnvelope,
               job_type: str) -> RouteResult | None:
        message = envelope.message
        self.calls.append(("start", job_type))
        try:
            started = service.start_attempt(envelope.capability, message.job_id,
                                            message.attempt_id)
        except AiJobError as error:
            return RouteResult(job_type, message.job_id, message.attempt_id, False, error.code)
        if not started.started:
            return RouteResult(job_type, message.job_id, message.attempt_id, False,
                               started.reason_code)
        return None

    def _vision(self, envelope: WorkerDispatchEnvelope) -> RouteResult:
        message = envelope.message
        refused = self._start(self._h.jobs, envelope, VISION_ANALYSIS_JOB_TYPE)
        if refused is not None:
            return refused
        self._h.last_envelope = envelope
        self.calls.append(("finish_vision", message.job_id))
        outcome = self._h.finish_vision(message.job_id, message.attempt_id)
        return RouteResult(VISION_ANALYSIS_JOB_TYPE, message.job_id, message.attempt_id, True,
                           None, outcome)

    def _sketch(self, envelope: WorkerDispatchEnvelope) -> RouteResult:
        message = envelope.message
        refused = self._start(self._sketch_jobs, envelope, SKETCH_JOB_TYPE)
        if refused is not None:
            return refused
        self.last_sketch = envelope
        self.calls.append(("provider", message.job_id))
        claim = self._provider.run(message)
        if self.crash_after_provider:
            self.crash_after_provider = False
            return RouteResult(SKETCH_JOB_TYPE, message.job_id, message.attempt_id, True,
                               "CRASHED_BEFORE_COMPLETION", claim)
        self.calls.append(("accept", message.job_id))
        receipt = self._sketch_jobs.accept_completion(envelope.capability, claim)
        return RouteResult(SKETCH_JOB_TYPE, message.job_id, message.attempt_id, True,
                           receipt.reason_code, receipt)


# ===================================================================== chain harness
@dataclass
class SketchChainHarness:
    h: AssistanceHarness
    raw_artifacts: FakeArtifacts
    artifact_port: CoordinatedSketchArtifactPort
    a1_job_deps: AiJobDependencies
    sketch_job_deps: AiJobDependencies
    cleanup_view: ArtifactPortView
    sketch_jobs: AiJobService
    sketch_eligibility: SketchEligibility
    store: InMemorySketchStore
    repository: CoordinatedSketchRepository
    decision: FenceDecisionPort
    policy: FixtureSketchPolicy
    generator: ScriptedSketchGenerator
    admission: FixtureDerivedArtifactAdmission
    job_port: AiJobSketchPort
    job_reader: AiJobSketchReader
    copy_registry: InMemoryProviderCopyRegistry
    copy_adapter: FakeProviderCopyAdapter
    copies: ProviderCopyLifecycleService
    authority: FakeSketchAuthority
    handoffs: AssistanceHandoffReader
    stage: SketchStageAdapter
    provider: SketchProviderAdapter
    service: SketchGenerationService
    router: JobTypeRouter
    forwarded: int = 0
    dropped_hints: list[str] = field(default_factory=list)
    side_routes: list[RouteResult] = field(default_factory=list)

    # ------------------------------------------------------------- BE2-03 side
    def ready(self, command: object | None = None) -> str:
        """Submit an A1 request and run its Vision job through the router (never
        ``h.run_vision``/``h.start_next`` on the shared queue)."""

        result = self.h.submit(command)  # type: ignore[arg-type]
        assistance_id = result.request.assistance_id
        self.h.dispatch()
        jobs = self.h.job_store.snapshot().jobs.values()
        target_job = next((job for job in jobs
                           if job.active_attempt.request_ref.request_id == assistance_id), None)
        assert target_job is not None, "submitted request has no dispatched Vision job"
        while True:  # FIFO: envelopes queued ahead of this Vision job are routed first
            routed = self.router.run_next()
            assert routed is not None, "no Vision envelope for the submitted request"
            if routed.job_id != target_job.job_id:
                self.side_routes.append(routed)
                continue
            assert routed.job_type == VISION_ANALYSIS_JOB_TYPE
            assert routed.started, routed
            break
        self.h.service.reconcile(assistance_id)
        self.h.clock.advance(seconds=6)  # outside the A1 fixture debounce window
        return assistance_id

    def forward_hints(self, *, drop: bool = False) -> int:
        """Move recorded BE2-03 intents into the 04 inbox; ``drop`` simulates a lost callback."""

        intents = self.h.sketch.intents[self.forwarded:]
        self.forwarded = len(self.h.sketch.intents)
        for intent in intents:
            if drop:
                self.dropped_hints.append(intent.intent_id)
            else:
                self.stage.request_sketch(intent)
        return len(intents)

    def open_ready(self, command: object | None = None) -> str:
        assistance_id = self.ready(command)
        self.forward_hints()
        self.service.process_inbox(ORG)
        proposal_id = self.proposal_for(assistance_id)
        assert proposal_id is not None
        return proposal_id

    def proposal_for(self, assistance_id: str) -> str | None:
        with self.store.transaction() as tx:
            return tx.find_by_assistance(ORG, assistance_id)

    def proposal(self, proposal_id: str) -> SketchProposal:
        proposal = self.store.peek(proposal_id)
        assert proposal is not None
        return proposal

    # ------------------------------------------------------------- BE2-04 side
    def run_sketch(self, proposal_id: str, *, reconcile: bool = True) -> RouteResult | None:
        self.sketch_jobs.dispatch_outbox()
        routed = self.router.run_next()
        if reconcile:
            self.service.reconcile(proposal_id)
        return routed

    def publish_policy(self, snapshot: SketchPolicySnapshot | None) -> bool:
        """Fixture policy change: one coordinated publication that bumps sketch-policy."""

        def publication() -> None:
            self.policy.snapshot = snapshot
            self.h.fences.bump(sketch_policy_fence_scope(ORG))

        return self.h.coordinator.request_publication(publication)

    def owner_quarantine(self, refs: tuple[str, ...], reason: str = "OWNER_QUARANTINE") -> bool:
        return self.artifact_port.owner_quarantine(refs, reason, caller="owner")

    # ------------------------------------------------------------- SK-C10 audit
    def audit_violations(self) -> list[str]:
        return artifact_audit_violations(self.artifact_port.audit, self.h.fences)

    def port_identity_ok(self) -> bool:
        ports = (self.a1_job_deps.artifacts, self.sketch_job_deps.artifacts, self.cleanup_view)
        return all(isinstance(p, ArtifactPortView) and p.port is self.artifact_port
                   for p in ports)


def artifact_audit_violations(audit: list[ArtifactAuditEntry],
                              fences: FakeOwnerFences) -> list[str]:
    """SK-C10: each ``artifact:<ref>`` bump has exactly one ``bumped=True`` audit entry."""

    violations: list[str] = []
    prefix = artifact_fence_scope("")
    bumped: dict[str, int] = {}
    for entry in audit:
        if entry.bumped:
            bumped[entry.ref] = bumped.get(entry.ref, 0) + 1
    for scope, epoch in sorted(fences.epochs.items()):
        if not scope.startswith(prefix) or epoch == 0:
            continue
        ref = scope[len(prefix):]
        if bumped.get(ref, 0) != epoch:
            violations.append(f"{ref}: epoch {epoch}, audited bumps {bumped.get(ref, 0)}")
    for ref, count in sorted(bumped.items()):
        if fences.epochs[artifact_fence_scope(ref)] != count:
            violations.append(f"{ref}: audited bumps {count} without matching epoch")
    return violations


def _canvas_facts(canvas_id: str, *, mode: str, group: str | None,
                  personal: str | None) -> CanvasFacts:
    """Public ``CanvasFacts`` built directly (the A1 ``_canvas`` helper is private)."""

    return CanvasFacts(
        organization_id=ORG, class_id=CLASS, session_id=SESSION, canvas_id=canvas_id,
        mode=mode, group_id=group, personal_participant_id=personal, session_active=True,
        document_epoch=1, context_revision=CONTEXT_REVISION, region_policy_revision=2,
        regions={"region_fx_open": None, "region_fx_b_only": frozenset({CHILD_B})},
        age_policy_ref="age-policy:36-155-months:proposed",
    )


def build_sketch_chain_harness(*, auto_schedule: bool = True,
                               start: datetime = FIXTURE_START,
                               sketch_policy: SketchPolicySnapshot | None = None,
                               ) -> SketchChainHarness:
    """Rebuild A1 from public parts, sharing coordinated artifacts and routing retry eligibility
    by job type: Vision delegates to A1, while Sketch uses its proposal-aware eligibility."""

    clock = FakeClock(start)
    ids = SequentialIds()
    coordinator = AssistanceCommitCoordinator()
    fences = HookedOwnerFences()
    job_store = InMemoryAiJobStore(fences)
    job_repository = CoordinatedAiJobRepository(job_store, coordinator)
    owner_eligibility = FakeEligibility(fences)
    store = InMemoryAssistanceStore(coordinator, fences)
    eligibility = AssistanceEligibility(owner_eligibility, store, coordinator)
    decision = FenceDecisionPort(fences, coordinator)
    sketch_store = InMemorySketchStore(decision, fences)
    repository = CoordinatedSketchRepository(sketch_store, coordinator)
    sketch_eligibility = SketchEligibility(eligibility, repository, coordinator)
    chain_eligibility = SketchChainEligibility(eligibility, sketch_eligibility)
    job_authorization = FakeAuthorization(fences)
    raw_artifacts = FakeArtifacts(fences)
    artifact_port = CoordinatedSketchArtifactPort(raw_artifacts, coordinator, fences)
    queue = FakeQueue()
    capabilities = FakeWorkerCapability()
    a1_job_deps = AiJobDependencies(
        repository=job_repository, authorization=job_authorization,
        eligibility=chain_eligibility,
        worker_capability=capabilities, clock=clock, ids=ids,
        artifacts=artifact_port.view("h.jobs"), audit=FakeAudit(), queue=queue,
        capability_issuer=capabilities,
    )
    jobs = AiJobService(a1_job_deps)
    job_authorization.grant(TEACHER.principal_id, set(ALL_JOB_ACTIONS))
    for device in (DEVICE_A, DEVICE_GA, DEVICE_GB):
        job_authorization.grant(device.principal_id, set(ALL_JOB_ACTIONS),
                                session_ids={SESSION})

    owner = FakeAssistanceOwner()
    owner.canvases[CANVAS_P] = _canvas_facts(CANVAS_P, mode="personal", group=None,
                                             personal=CHILD_A)
    owner.canvases[CANVAS_G] = _canvas_facts(CANVAS_G, mode="collaborative", group=GROUP,
                                             personal=None)
    owner.rosters[(SESSION, GROUP)] = GroupRoster(GROUP, (CHILD_A, CHILD_B), 1)
    owner.turns[CANVAS_G] = Contributor(CHILD_A, "turn_fx_ga", 1)
    for child, months in ((CHILD_A, 60), (CHILD_B, 120), (CHILD_C, 100)):
        owner.set_member(child, months=months, purposes=frozenset({PURPOSE}))
    authority = FakeAssistanceAuthority()
    authority.teachers[TEACHER.principal_id] = TeacherScope(ORG, frozenset({CLASS}))
    authority.teachers[OTHER_CLASS_TEACHER.principal_id] = TeacherScope(
        ORG, frozenset({"class_fx_b"}))
    authority.teachers[OUTSIDER.principal_id] = TeacherScope(OUTSIDER.organization_id,
                                                             frozenset({CLASS}))
    # Fixture configuration (plan §6.5): the injected handoff reader is a scoped Teacher.
    authority.teachers[READER.principal_id] = TeacherScope(ORG, frozenset({CLASS}))
    authority.devices[DEVICE_A.principal_id] = DeviceBinding(
        ORG, SESSION, CANVAS_P, CHILD_A, "turn_fx_a1", 1)
    authority.devices[DEVICE_GA.principal_id] = DeviceBinding(
        ORG, SESSION, CANVAS_G, CHILD_A, "turn_fx_ga", 1)
    authority.devices[DEVICE_GB.principal_id] = DeviceBinding(
        ORG, SESSION, CANVAS_G, CHILD_B, "turn_fx_gb", 1)
    source_p, image_p = make_source(CANVAS_P, "fx_p")
    source_g, image_g = make_source(CANVAS_G, "fx_g")
    sources = FakeAssistanceSource()
    sources.add(ORG, CANVAS_P, source_p)
    sources.add(ORG, CANVAS_G, source_g)
    policy = FixtureAssistancePolicy(fixture_policy())

    vision_store = InMemoryAnalysisStore()
    vision_repository = CoordinatedAnalysisRepository(vision_store, coordinator, fences,
                                                      default_organization_id=ORG)
    vision_sources = FakeAnalysisSource()
    vision_admission = FakeAdmission()
    for resolved, image in ((source_p, image_p), (source_g, image_g)):
        vision_sources.add(resolved.snapshot, image)
        assert resolved.admission is not None
        vision_admission.add(resolved.admission, organization_id=ORG)
    vision_authority = FakeAnalysisAuthority()
    vision_authority.grant_teacher(TEACHER.principal_id, TeacherGrant(ORG, frozenset({CLASS})))
    vision_authority.grant_teacher(READER.principal_id, TeacherGrant(ORG, frozenset({CLASS})))
    vision_authority.bind_device(DEVICE_A.principal_id, VisionDeviceBinding(
        ORG, SESSION, CANVAS_P, None, CHILD_A, "turn_fx_a1"))
    vision_context = FakeAnalysisContext()
    for canvas_id in (CANVAS_P, CANVAS_G):
        vision_context.set_context(SESSION, canvas_id, CONTEXT_REVISION, topic_ref="topic_fx")
    for child, months in ((CHILD_A, 60), (CHILD_B, 120), (CHILD_C, 100)):
        vision_context.set_participant(child, age_months=months, purposes=frozenset({PURPOSE}))
    vision_provider = FakeVisionObservationProvider(clock=clock.now)

    holder: dict[str, AssistanceService] = {}
    vision = VisionAnalysisService(VisionAnalysisDependencies(
        repository=vision_repository, authority=vision_authority, context=vision_context,
        sources=vision_sources, admission=vision_admission,
        requests=AssistancePinPort(lambda: holder["service"]),
        jobs=AiJobRepositoryLineage(job_repository), provider=vision_provider, clock=clock,
        ids=ids, context_sources=FakeVisionContextSource(vision_context),
        age_band_policy=FIXTURE_AGE_BAND_POLICY,
    ))
    outcomes = VisionAnalysisOutcomes(vision, vision_repository, READER)
    job_port = AiJobServicePort(jobs)
    reader = AiJobRepositoryReader(job_repository)
    recording = RecordingSketchStage()
    service = AssistanceService(AssistanceDependencies(
        repository=store, owner=owner, authority=authority, sources=sources, policy=policy,
        jobs=job_port, job_reader=reader, analyses=outcomes, sketch_stage=recording,
        clock=clock, ids=ids, auto_schedule=auto_schedule,
    ))
    holder["service"] = service
    h = AssistanceHarness(
        clock=clock, ids=ids, coordinator=coordinator, fences=fences, job_store=job_store,
        job_repository=job_repository, owner_eligibility=owner_eligibility,
        eligibility=eligibility, job_authorization=job_authorization, artifacts=raw_artifacts,
        queue=queue, capabilities=capabilities, jobs=jobs, store=store, owner=owner,
        authority=authority, sources=sources, policy=policy, job_port=job_port, reader=reader,
        sketch=recording, vision=vision, vision_store=vision_store,
        vision_sources=vision_sources, vision_admission=vision_admission,
        vision_context=vision_context, vision_provider=vision_provider, outcomes=outcomes,
        service=service, source_p=source_p, source_g=source_g,
    )

    # ------------------------------------------------------------------ BE2-04
    sketch_job_deps = AiJobDependencies(
        repository=job_repository, authorization=job_authorization,
        eligibility=sketch_eligibility, worker_capability=capabilities, clock=clock, ids=ids,
        artifacts=artifact_port.view("sketch_jobs"), audit=FakeAudit(), queue=queue,
        capability_issuer=capabilities, retry_policy=FIXTURE_RETRY_POLICY,
    )
    sketch_jobs = AiJobService(sketch_job_deps)
    sketch_fixture_policy = FixtureSketchPolicy(sketch_policy or fixture_sketch_policy())
    generator = ScriptedSketchGenerator()
    admission = FixtureDerivedArtifactAdmission(raw_artifacts)
    sketch_job_port = AiJobSketchPort(sketch_jobs)
    sketch_job_reader = AiJobSketchReader(job_repository)
    registry, copy_adapter, copies = _copy_lifecycle()
    sketch_authority = _sketch_authority()
    handoffs = AssistanceHandoffReader(lambda: holder["service"], vision, owner, sources,
                                       READER)
    cleanup_view = artifact_port.view("c9")
    sketch_holder: dict[str, SketchGenerationService] = {}
    provider = SketchProviderAdapter(lambda: sketch_holder["service"])
    sketch_service = SketchGenerationService(SketchDependencies(
        repository=repository, handoffs=handoffs, decision=decision,
        policy=sketch_fixture_policy, generator=generator, admission=admission,
        artifacts=artifact_port, jobs=sketch_job_port, job_reader=sketch_job_reader,
        copies=SketchCopyRegistrar(copies), authority=sketch_authority, clock=clock, ids=ids,
        quarantine=cleanup_sink(cleanup_view),
    ))
    sketch_holder["service"] = sketch_service
    stage = SketchStageAdapter(lambda: sketch_holder["service"], ORG)
    router = JobTypeRouter(h, sketch_jobs, provider)
    return SketchChainHarness(
        h=h, raw_artifacts=raw_artifacts, artifact_port=artifact_port,
        a1_job_deps=a1_job_deps, sketch_job_deps=sketch_job_deps, cleanup_view=cleanup_view,
        sketch_jobs=sketch_jobs, sketch_eligibility=sketch_eligibility, store=sketch_store,
        repository=repository, decision=decision, policy=sketch_fixture_policy,
        generator=generator, admission=admission, job_port=sketch_job_port,
        job_reader=sketch_job_reader, copy_registry=registry, copy_adapter=copy_adapter,
        copies=copies, authority=sketch_authority, handoffs=handoffs, stage=stage,
        provider=provider, service=sketch_service, router=router,
    )


EXAMPLES_FIXTURE_ID = "FEAT-050-SK1-H-AI-REVIEW"


def build_sketch_examples() -> dict[str, object]:
    """Deterministic H-AI-REVIEW producer examples (0.1-candidate, synthetic) built from the
    chain: a promoted overlay record, its Child view, a blocked-unsafe event and the fixture
    copy report of the promoted proposal's provider-copy scope."""

    c = build_sketch_chain_harness()
    proposal_id = c.open_ready(c.h.command(level=LEVEL_2, intent="example overlay sketch"))
    c.run_sketch(proposal_id)
    assistance_id = c.proposal(proposal_id).binding.assistance_id
    record = c.service.get_record(TEACHER, proposal_id)
    device = c.service.device_view(DEVICE_A, assistance_id)

    c.generator.script = lambda request: default_outcome(request, unsafe=True)
    blocked_id = c.open_ready(c.h.command(level=LEVEL_2, intent="example unsafe sketch"))
    c.run_sketch(blocked_id)
    c.generator.script = None
    (blocked_event,) = [e for e in c.store.snapshot().events
                        if e.proposal_id == blocked_id and e.event_type == "sketch.blocked_unsafe"]

    scope_ref = f"sketch_proposal:{proposal_id}"
    c.copies.purge_scope(ORG, scope_ref, "example_purge_key")
    copies = [{
        "copy_id": copy.copy_id, "kind": copy.kind, "status": copy.status,
        "report_label": copy.report_label, "receipt_id": copy.receipt_id,
        "evidence_kind": copy.evidence_kind, "reason_code": copy.reason_code,
        "actual_deletion_proven": copy.actual_deletion_proven,
    } for copy in c.copies.discover(ORG, scope_ref)]
    return {
        "fixture_id": EXAMPLES_FIXTURE_ID,
        "synthetic_data": True,
        "contract_version": "0.1-candidate",
        "record_pending": record,
        "notice_blocked": event_view(blocked_event),
        "device_view": device,
        "provider_copy_report": {
            "contract_name": "ProviderCopyLifecycleReport",
            "contract_version": "0.1-candidate",
            "contract_owner": "BE2-14",
            "fake_support_owner": "BE2-01",
            "fixture_marker": True,
            "organization_id": ORG,
            "scope_ref": scope_ref,
            "copies": copies,
        },
    }


__all__ = [
    "ALL_JOB_ACTIONS",
    "JobTypeRouter",
    "RouteResult",
    "SketchChainHarness",
    "SketchUnitHarness",
    "UnknownJobType",
    "EXAMPLES_FIXTURE_ID",
    "artifact_audit_violations",
    "build_sketch_chain_harness",
    "build_sketch_examples",
    "build_sketch_unit_harness",
    "make_binding",
]
