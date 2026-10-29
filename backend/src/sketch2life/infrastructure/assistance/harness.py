"""Synthetic A1 chain: real BE2-01 ``AiJobService`` + real BE2-02 ``VisionAnalysisService`` +
BE2-03 ``AssistanceService`` over their fakes, joined by the shared fake commit coordinator.

One school/class/session; a personal canvas for child A and a collaborative canvas for group
G (children A and B, 60 and 120 completed months). Everything is synthetic; the Vision
provider is the existing offline fake; there is no real provider, network or Sketch producer.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any

from sketch2life.application.ports.ai_jobs import (
    AuthorizationAction,
    Principal,
    PrincipalRole,
    WorkerDispatchEnvelope,
)
from sketch2life.application.ports.assistance import CanvasFacts, GroupRoster, ResolvedSource
from sketch2life.application.services.ai_jobs import AiJobDependencies, AiJobService, StartResult
from sketch2life.application.services.assistance import (
    AssistanceDependencies,
    AssistanceService,
    CancelCommand,
    CommandResult,
    SubmitCommand,
)
from sketch2life.application.services.vision_analysis import (
    VisionAnalysisDependencies,
    VisionAnalysisService,
)
from sketch2life.domain.ai_jobs.completion import (
    CompletionClaim,
    Moderation,
    OutcomeKind,
    canonical_json,
)
from sketch2life.domain.assistance import (
    AssistanceRequest,
    CheckpointRef,
    Contributor,
    RequestReason,
    TargetKind,
    TargetScope,
)
from sketch2life.domain.vision_analysis import (
    AdmissionReceipt,
    CheckpointBinding,
    ObservationClaim,
    RenderBinding,
    SourceSnapshot,
)
from sketch2life.domain.vision_context import FIXTURE_AGE_BAND_POLICY
from sketch2life.infrastructure.ai_jobs.fakes import (
    FakeArtifacts,
    FakeAudit,
    FakeAuthorization,
    FakeClock,
    FakeEligibility,
    FakeQueue,
    FakeWorkerCapability,
    InMemoryAiJobStore,
    SequentialIds,
    eligibility_fence_scope,
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

FIXTURE_START = datetime(2026, 10, 17, 13, 0, tzinfo=UTC)
ORG = "org_fx_school_a"
OTHER_ORG = "org_fx_school_b"
CLASS = "class_fx_a"
OTHER_CLASS = "class_fx_b"
SESSION = "session_fx_001"
CANVAS_P = "canvas_fx_001"
CANVAS_G = "canvas_fx_group"
GROUP = "group_fx_1"
CHILD_A = "participant_fx_a"
CHILD_B = "participant_fx_b"
CHILD_C = "participant_fx_c"
PURPOSE = "ai_drawing_assistance"
CONTEXT_REVISION = 3
LEVEL = "level_fx_1"
LEVEL_2 = "level_fx_2"

TEACHER = Principal("teacher_fx_001", ORG, PrincipalRole.TEACHER)
OTHER_CLASS_TEACHER = Principal("teacher_fx_002", ORG, PrincipalRole.TEACHER)
OUTSIDER = Principal("teacher_fx_900", OTHER_ORG, PrincipalRole.TEACHER)
ADMIN = Principal("admin_fx_001", ORG, PrincipalRole.ADMIN)
READER = Principal("teacher_fx_reader", ORG, PrincipalRole.TEACHER)
DEVICE_A = Principal("device_fx_a", ORG, PrincipalRole.DEVICE)
DEVICE_GA = Principal("device_fx_ga", ORG, PrincipalRole.DEVICE)
DEVICE_GB = Principal("device_fx_gb", ORG, PrincipalRole.DEVICE)


def make_source(canvas_id: str, label: str, *, render: bytes | None = None,
                epoch: int = 1, server_sequence: int = 40) -> tuple[ResolvedSource, bytes]:
    checkpoint_doc = {"canvas_id": canvas_id, "document_epoch": epoch, "label": label}
    checksum = sha256(canonical_json(checkpoint_doc).encode("utf-8")).hexdigest()
    image = render or f"\x89PNG synthetic {canvas_id} {label}".encode()
    checkpoint = CheckpointBinding(f"checkpoint_{label}", canvas_id, epoch, 4, checksum)
    render_binding = RenderBinding(f"render_{label}", sha256(image).hexdigest(), "image/png",
                                   checkpoint.checkpoint_id, checksum, "canvas-render-fixture-v0")
    snapshot = SourceSnapshot(f"snapshot_{label}", ORG, checkpoint, render_binding)
    admission = AdmissionReceipt(f"admission_{label}", sha256(label.encode()).hexdigest(),
                                 render_binding.render_ref, render_binding.render_sha256,
                                 "PASS", "feat018-image-admission-v1")
    return ResolvedSource(snapshot, server_sequence, admission), image


def checkpoint_ref(source: ResolvedSource) -> CheckpointRef:
    checkpoint = source.snapshot.checkpoint
    return CheckpointRef(checkpoint.checkpoint_id, checkpoint.document_epoch,
                         source.server_sequence, checkpoint.checksum_sha256)


@dataclass
class AssistanceHarness:
    clock: FakeClock
    ids: SequentialIds
    coordinator: AssistanceCommitCoordinator
    fences: HookedOwnerFences
    job_store: InMemoryAiJobStore
    job_repository: CoordinatedAiJobRepository
    owner_eligibility: FakeEligibility
    eligibility: AssistanceEligibility
    job_authorization: FakeAuthorization
    artifacts: FakeArtifacts
    queue: FakeQueue
    capabilities: FakeWorkerCapability
    jobs: AiJobService
    store: InMemoryAssistanceStore
    owner: FakeAssistanceOwner
    authority: FakeAssistanceAuthority
    sources: FakeAssistanceSource
    policy: FixtureAssistancePolicy
    job_port: AiJobServicePort
    reader: AiJobRepositoryReader
    sketch: RecordingSketchStage
    vision: VisionAnalysisService
    vision_store: InMemoryAnalysisStore
    vision_sources: FakeAnalysisSource
    vision_admission: FakeAdmission
    vision_context: FakeAnalysisContext
    vision_provider: FakeVisionObservationProvider
    outcomes: VisionAnalysisOutcomes
    service: AssistanceService
    source_p: ResolvedSource
    source_g: ResolvedSource
    keys: list[str] = field(default_factory=list)
    last_envelope: WorkerDispatchEnvelope | None = None

    # ------------------------------------------------------------- commands
    def key(self) -> str:
        key = f"key_fx_{len(self.keys) + 1:03d}"
        self.keys.append(key)
        return key

    def command(
        self,
        principal: Principal = DEVICE_A,
        *,
        key: str | None = None,
        canvas: str = CANVAS_P,
        target: TargetScope | None = None,
        source: ResolvedSource | None = None,
        level: str = LEVEL,
        reason: RequestReason | None = None,
        intent: str | None = None,
        context: int = CONTEXT_REVISION,
        client: str = "client_fx_001",
        region: str | None = None,
    ) -> SubmitCommand:
        if target is None:
            target = TargetScope(TargetKind.INDIVIDUAL, CHILD_A)
        if reason is None:
            reason = (RequestReason.TEACHER_REQUEST if principal.role is PrincipalRole.TEACHER
                      else RequestReason.CHILD_REQUEST)
        if source is None:
            source = self.source_g if canvas == CANVAS_G else self.source_p
        return SubmitCommand(
            principal=principal,
            idempotency_key=key if key is not None else self.key(),
            canvas_id=canvas,
            checkpoint_ref=checkpoint_ref(source),
            target=target,
            region_id=region,
            requested_level=level,
            child_intent=intent,
            request_reason=reason,
            context_revision=context,
            client_request_id=client,
        )

    def group_command(self, principal: Principal = TEACHER, **changes: Any) -> SubmitCommand:
        return self.command(principal, canvas=CANVAS_G,
                            target=TargetScope(TargetKind.GROUP, GROUP), **changes)

    def submit(self, command: SubmitCommand | None = None) -> CommandResult:
        return self.service.submit(command or self.command())

    def cancel_command(self, principal: Principal, assistance_id: str, *,
                       key: str | None = None, if_match: str | None = "auto",
                       reason: str | None = None) -> CancelCommand:
        if if_match == "auto":
            if_match = self.request(assistance_id).etag()
        return CancelCommand(principal, assistance_id, key if key is not None else self.key(),
                             if_match, reason)

    def request(self, assistance_id: str) -> AssistanceRequest:
        request = self.store.peek(assistance_id)
        assert request is not None
        return request

    # -------------------------------------------------------------- worker
    def dispatch(self) -> int:
        return self.jobs.dispatch_outbox()

    def start_next(self) -> tuple[StartResult, str, str]:
        envelope = self.queue.receive()
        assert envelope is not None, "no dispatch message"
        message = envelope.message
        started = self.jobs.start_attempt(envelope.capability, message.job_id,
                                          message.attempt_id)
        self.last_envelope = envelope
        return started, message.job_id, message.attempt_id

    def finish_vision(self, job_id: str, attempt_id: str, *, fail_retryable: bool = False,
                      fail_exhausted: bool = False) -> object:
        """The Vision worker step: BE2-02 observation, then BE2-01 completion."""

        job = self.job_store.snapshot().jobs[job_id]
        ref = job.active_attempt.request_ref
        assert self.last_envelope is not None
        capability = self.last_envelope.capability
        if fail_retryable or fail_exhausted:
            claim = CompletionClaim(job_id, attempt_id, ref.request_revision, ref.input_hash,
                                    ref.context_revision, OutcomeKind.FAILURE,
                                    failure_code="PROVIDER_UNAVAILABLE",
                                    retryable=fail_retryable)
            return self.jobs.accept_completion(capability, claim)
        request = self.store.peek(ref.request_id)
        assert request is not None
        result = self.vision.record_observation(ObservationClaim(
            job_id=job_id, job_attempt_id=attempt_id, assistance_id=ref.request_id,
            expected_request_revision=ref.request_revision,
            input_snapshot_ref=request.facts.source.snapshot_ref,
            context_revision=ref.context_revision), correlation_id=f"corr_{job_id}")
        if result.authoritative:
            output = self.artifacts.put(ORG, f"analysis:{result.analysis_id}".encode(),
                                        job_id=job_id, attempt_id=attempt_id)
            claim = CompletionClaim(job_id, attempt_id, ref.request_revision, ref.input_hash,
                                    ref.context_revision, OutcomeKind.SUCCESS,
                                    outputs=(output,), moderation=Moderation.PASSED)
        else:
            claim = CompletionClaim(job_id, attempt_id, ref.request_revision, ref.input_hash,
                                    ref.context_revision, OutcomeKind.FAILURE,
                                    failure_code="OUTPUT_MALFORMED", retryable=False)
        return self.jobs.accept_completion(capability, claim)

    def run_vision(self, assistance_id: str) -> AssistanceRequest:
        """Dispatch, start, observe, complete, then reconcile one request."""

        self.dispatch()
        started, job_id, attempt_id = self.start_next()
        assert started.started, started.reason_code
        self.finish_vision(job_id, attempt_id)
        reconciled = self.service.reconcile(assistance_id)
        assert reconciled is not None
        return reconciled

    def job(self, job_id: str) -> object:
        return self.job_store.snapshot().jobs[job_id]

    # ------------------------------------------------------- owner fact changes
    def publish_owner_change(self, change: Callable[[], object]) -> bool:
        """Fake owner publication: the fact change and the owner epoch bump are one
        coordinated publication (deferred when requested inside a foundation unit)."""

        def publication() -> None:
            change()
            self.fences.bump(eligibility_fence_scope(ORG))

        return self.coordinator.request_publication(publication)

    def set_age(self, participant_id: str, months: int | None) -> None:
        self.owner.update_member(participant_id, months=months)
        self.vision_context.ages[participant_id] = months

    def revoke_consent(self, participant_id: str) -> None:
        self.owner.update_member(participant_id, consent_effective=False)
        self.vision_context.revoke_consent(participant_id)
        self.owner_eligibility.revoked_subjects.add(participant_id)

    def set_roster(self, members: tuple[str, ...], revision: int | None = None) -> None:
        old = self.owner.rosters[(SESSION, GROUP)]
        self.owner.rosters[(SESSION, GROUP)] = GroupRoster(
            GROUP, members, old.revision if revision is None else revision)

    def set_render(self, canvas_id: str, label: str) -> ResolvedSource:
        """Same checkpoint ref resolving to a different render (no notice)."""

        base = self.source_p if canvas_id == CANVAS_P else self.source_g
        image = f"\x89PNG re-rendered {label}".encode()
        snapshot = base.snapshot
        render = RenderBinding(f"render_{label}", sha256(image).hexdigest(), "image/png",
                               snapshot.checkpoint.checkpoint_id,
                               snapshot.checkpoint.checksum_sha256, "canvas-render-fixture-v1")
        changed = SourceSnapshot(f"snapshot_{label}", ORG, snapshot.checkpoint, render)
        admission = AdmissionReceipt(f"admission_{label}", sha256(label.encode()).hexdigest(),
                                     render.render_ref, render.render_sha256, "PASS",
                                     "feat018-image-admission-v1")
        resolved = ResolvedSource(changed, base.server_sequence, admission)
        self.sources.add(ORG, canvas_id, resolved)
        self.vision_sources.add(changed, image)
        self.vision_admission.add(admission, organization_id=ORG)
        return resolved


def _canvas(canvas_id: str, *, mode: str, group: str | None, personal: str | None,
            regions: dict[str, frozenset[str] | None] | None = None) -> CanvasFacts:
    return CanvasFacts(
        organization_id=ORG, class_id=CLASS, session_id=SESSION, canvas_id=canvas_id,
        mode=mode, group_id=group, personal_participant_id=personal, session_active=True,
        document_epoch=1, context_revision=CONTEXT_REVISION, region_policy_revision=2,
        regions=regions or {"region_fx_open": None,
                            "region_fx_b_only": frozenset({CHILD_B})},
        age_policy_ref="age-policy:36-155-months:proposed",
    )


def build_assistance_harness(*, auto_schedule: bool = True,
                             start: datetime = FIXTURE_START) -> AssistanceHarness:
    clock = FakeClock(start)
    ids = SequentialIds()
    coordinator = AssistanceCommitCoordinator()
    fences = HookedOwnerFences()
    job_store = InMemoryAiJobStore(fences)
    job_repository = CoordinatedAiJobRepository(job_store, coordinator)
    owner_eligibility = FakeEligibility(fences)
    store = InMemoryAssistanceStore(coordinator, fences)
    eligibility = AssistanceEligibility(owner_eligibility, store, coordinator)
    job_authorization = FakeAuthorization(fences)
    artifacts = FakeArtifacts(fences)
    queue = FakeQueue()
    capabilities = FakeWorkerCapability()
    jobs = AiJobService(AiJobDependencies(
        repository=job_repository, authorization=job_authorization, eligibility=eligibility,
        worker_capability=capabilities, clock=clock, ids=ids, artifacts=artifacts,
        audit=FakeAudit(), queue=queue, capability_issuer=capabilities,
    ))
    all_actions = {AuthorizationAction.CREATE_JOB, AuthorizationAction.READ_JOB,
                   AuthorizationAction.CANCEL_JOB}
    job_authorization.grant(TEACHER.principal_id, all_actions)
    for device in (DEVICE_A, DEVICE_GA, DEVICE_GB):
        job_authorization.grant(device.principal_id, all_actions, session_ids={SESSION})

    # BE1 owner facts (ASSUMED_CONTRACT fakes).
    owner = FakeAssistanceOwner()
    owner.canvases[CANVAS_P] = _canvas(CANVAS_P, mode="personal", group=None, personal=CHILD_A)
    owner.canvases[CANVAS_G] = _canvas(CANVAS_G, mode="collaborative", group=GROUP,
                                       personal=None)
    owner.rosters[(SESSION, GROUP)] = GroupRoster(GROUP, (CHILD_A, CHILD_B), 1)
    owner.turns[CANVAS_G] = Contributor(CHILD_A, "turn_fx_ga", 1)
    for child, months in ((CHILD_A, 60), (CHILD_B, 120), (CHILD_C, 100)):
        owner.set_member(child, months=months, purposes=frozenset({PURPOSE}))
    authority = FakeAssistanceAuthority()
    authority.teachers[TEACHER.principal_id] = TeacherScope(ORG, frozenset({CLASS}))
    authority.teachers[OTHER_CLASS_TEACHER.principal_id] = TeacherScope(
        ORG, frozenset({OTHER_CLASS}))
    authority.teachers[OUTSIDER.principal_id] = TeacherScope(OTHER_ORG, frozenset({CLASS}))
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

    # BE2-02 Vision over the same synthetic facts; its request pin comes from BE2-03.
    vision_store = InMemoryAnalysisStore()
    # A1-CR03-F2: every Vision transaction is a coordinated unit whose committed writes move
    # the analysis epoch that BE2-03 decisions are validated against.
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
    provider = FakeVisionObservationProvider(clock=clock.now)

    holder: dict[str, AssistanceService] = {}
    vision = VisionAnalysisService(VisionAnalysisDependencies(
        repository=vision_repository, authority=vision_authority, context=vision_context,
        sources=vision_sources, admission=vision_admission,
        requests=AssistancePinPort(lambda: holder["service"]),
        jobs=AiJobRepositoryLineage(job_repository), provider=provider, clock=clock, ids=ids,
        context_sources=FakeVisionContextSource(vision_context),
        age_band_policy=FIXTURE_AGE_BAND_POLICY,
    ))
    outcomes = VisionAnalysisOutcomes(vision, vision_repository, READER)
    job_port = AiJobServicePort(jobs)
    reader = AiJobRepositoryReader(job_repository)
    sketch = RecordingSketchStage()
    service = AssistanceService(AssistanceDependencies(
        repository=store, owner=owner, authority=authority, sources=sources, policy=policy,
        jobs=job_port, job_reader=reader, analyses=outcomes, sketch_stage=sketch, clock=clock,
        ids=ids, auto_schedule=auto_schedule,
    ))
    holder["service"] = service
    return AssistanceHarness(
        clock=clock, ids=ids, coordinator=coordinator, fences=fences, job_store=job_store,
        job_repository=job_repository, owner_eligibility=owner_eligibility,
        eligibility=eligibility, job_authorization=job_authorization, artifacts=artifacts,
        queue=queue, capabilities=capabilities, jobs=jobs, store=store, owner=owner,
        authority=authority, sources=sources, policy=policy, job_port=job_port, reader=reader,
        sketch=sketch, vision=vision, vision_store=vision_store, vision_sources=vision_sources,
        vision_admission=vision_admission, vision_context=vision_context,
        vision_provider=provider, outcomes=outcomes, service=service, source_p=source_p,
        source_g=source_g,
    )


def build_handoff_examples() -> dict[str, object]:
    """Deterministic H-AI-REVIEW / H-OPERATIONS consumer examples (0.1-candidate, synthetic)."""

    from sketch2life.application.services.assistance import device_view, teacher_view

    h = build_assistance_harness()
    ready = h.run_vision(h.submit(h.command(intent="a cat with stripes")).request.assistance_id)
    cached = h.request(h.submit(h.command(intent="a cat with stripes")).request.assistance_id)
    h.clock.advance(seconds=6)
    group = h.submit(h.group_command()).request
    cancelled = h.service.cancel(h.cancel_command(TEACHER, group.assistance_id)).request
    events = [
        {"event_id": e.event_id, "event_type": e.event_type,
         "organization_id": e.organization_id, "assistance_id": e.assistance_id,
         "request_revision": e.request_revision, "reason": e.reason,
         "occurred_at": e.occurred_at.isoformat().replace("+00:00", "Z")}
        for e in h.store.snapshot().events
    ]
    (intent,) = h.sketch.intents
    return {
        "fixture_marker": "FIXTURE_ONLY_SYNTHETIC_NOT_ADOPTED",
        "teacher_record_analysis_ready": teacher_view(ready),
        "device_view_analysis_ready": device_view(ready, h.service.poll_after_ms),
        "teacher_record_cache_hit": teacher_view(cached),
        "teacher_record_cancelled_group": teacher_view(h.request(cancelled.assistance_id)),
        "sketch_intent": {"intent_id": intent.intent_id, "assistance_id": intent.assistance_id,
                          "request_revision": intent.request_revision,
                          "analysis_id": intent.analysis_id,
                          "analysis_revision": intent.analysis_revision,
                          "status": intent.status},
        "events": events,
    }


__all__ = [
    "ADMIN",
    "CANVAS_G",
    "CANVAS_P",
    "CHILD_A",
    "CHILD_B",
    "CHILD_C",
    "CLASS",
    "CONTEXT_REVISION",
    "DEVICE_A",
    "DEVICE_GA",
    "DEVICE_GB",
    "GROUP",
    "LEVEL",
    "LEVEL_2",
    "ORG",
    "OTHER_CLASS_TEACHER",
    "OUTSIDER",
    "PURPOSE",
    "READER",
    "SESSION",
    "TEACHER",
    "AssistanceHarness",
    "build_assistance_harness",
    "build_handoff_examples",
    "checkpoint_ref",
    "make_source",
]
