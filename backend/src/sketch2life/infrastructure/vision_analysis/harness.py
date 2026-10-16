"""Synthetic fixture world for BE2-02 C1 tests and the consumer handoff (never live).

One school, class, session and canvas; two child participants (60 and 120 completed months,
the latter outside the legacy under-nine helper but inside the authoritative 36–155 range);
one admitted PNG render derived from one JSON checkpoint; one assistance request pin and one
running vision-analysis job attempt. No real child data, credentials or provider endpoints.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from hashlib import sha256

from sketch2life.application.ports.ai_jobs import Principal, PrincipalRole
from sketch2life.application.ports.vision_analysis import JobLineagePort, VisionObservationPort
from sketch2life.application.services.vision_analysis import (
    CorrectionCommand,
    ObservationResult,
    VisionAnalysisDependencies,
    VisionAnalysisService,
    child_correction_view,
    teacher_correction_view,
    worker_candidate_view,
)
from sketch2life.contracts.schemas.vision import VISION_POLICY_MATCH_VIEW_VERSION
from sketch2life.contracts.schemas.vision_v2 import (
    VisionProfileIdV2,
    vision_profile_catalog_hash_v2,
    vision_profile_catalog_v2,
    vision_profile_config_hash_v2,
)
from sketch2life.domain.ai_jobs.completion import canonical_json
from sketch2life.domain.ai_jobs.model import JobState
from sketch2life.domain.vision_analysis import (
    VISION_ANALYSIS_JOB_TYPE,
    AdmissionReceipt,
    AnalysisScope,
    AssistancePin,
    CheckpointBinding,
    JobLineageView,
    ObservationClaim,
    ProviderContextMode,
    RenderBinding,
    SourceSnapshot,
    analysis_etag,
    provider_result_ref,
)
from sketch2life.infrastructure.ai.vision_lexical_policy import synthetic_prohibited_lexicon
from sketch2life.infrastructure.ai_jobs.fakes import FakeClock, SequentialIds
from sketch2life.infrastructure.vision_analysis.fakes import (
    DeviceBinding,
    FakeAdmission,
    FakeAnalysisAuthority,
    FakeAnalysisContext,
    FakeAnalysisSource,
    FakeAssistanceRequests,
    FakeJobLineage,
    FakeVisionObservationProvider,
    InMemoryAnalysisStore,
    TeacherGrant,
)
from sketch2life.infrastructure.vision_analysis.legacy_v2 import LegacyVisionV2Bridge

FIXTURE_START = datetime(2026, 10, 16, 12, 0, tzinfo=UTC)
ORG = "org_fx_school_a"
OTHER_ORG = "org_fx_school_b"
CLASS = "class_fx_a"
OTHER_CLASS = "class_fx_b"
SESSION = "session_fx_001"
CANVAS = "canvas_fx_001"
CHILD_A = "participant_fx_a"
CHILD_B = "participant_fx_b"
PURPOSE = "ai_drawing_assistance"
ASSISTANCE = "assistance_fx_001"
SNAPSHOT = "snapshot_fx_001"
JOB = "job_fx0001"
ATTEMPT = "att_fx0001"
CONTEXT_REVISION = 3

TEACHER = Principal("teacher_fx_001", ORG, PrincipalRole.TEACHER)
OTHER_CLASS_TEACHER = Principal("teacher_fx_002", ORG, PrincipalRole.TEACHER)
OUTSIDER = Principal("teacher_fx_900", OTHER_ORG, PrincipalRole.TEACHER)
ADMIN = Principal("admin_fx_001", ORG, PrincipalRole.ADMIN)
DEVICE_A = Principal("device_fx_a", ORG, PrincipalRole.DEVICE)
DEVICE_B = Principal("device_fx_b", ORG, PrincipalRole.DEVICE)
DEVICE_OTHER_CANVAS = Principal("device_fx_c", ORG, PrincipalRole.DEVICE)

SYNTHETIC_RENDER = b"\x89PNG\r\n\x1a\nsynthetic non-child BE2-02 C1 render"
SYNTHETIC_CHECKPOINT = {
    "canvas_id": CANVAS,
    "document_epoch": 1,
    "checkpoint_revision": 4,
    "strokes": [{"stroke_id": "stroke_fx_1", "points": [[0.1, 0.1], [0.4, 0.5]]}],
}
CHECKPOINT_CHECKSUM = sha256(canonical_json(SYNTHETIC_CHECKPOINT).encode("utf-8")).hexdigest()
RENDER_SHA256 = sha256(SYNTHETIC_RENDER).hexdigest()


def synthetic_snapshot(*, ref: str = SNAPSHOT, render_sha256: str = RENDER_SHA256,
                       checkpoint_checksum: str = CHECKPOINT_CHECKSUM) -> SourceSnapshot:
    checkpoint = CheckpointBinding(
        checkpoint_id="checkpoint_fx_004",
        canvas_id=CANVAS,
        document_epoch=1,
        checkpoint_revision=4,
        checksum_sha256=checkpoint_checksum,
    )
    render = RenderBinding(
        render_ref="render_fx_004",
        render_sha256=render_sha256,
        media_type="image/png",
        source_checkpoint_id=checkpoint.checkpoint_id,
        source_checkpoint_checksum=checkpoint.checksum_sha256,
        renderer_version="canvas-render-fixture-v0",
    )
    return SourceSnapshot(ref, ORG, checkpoint, render)


def synthetic_admission(snapshot: SourceSnapshot, *, decision: str = "PASS") -> AdmissionReceipt:
    return AdmissionReceipt(
        receipt_id="admission_fx_004",
        receipt_sha256=sha256(b"synthetic admission receipt fx_004").hexdigest(),
        render_ref=snapshot.render.render_ref,
        render_sha256=snapshot.render.render_sha256,
        decision=decision,
        policy_version="feat018-image-admission-v1",
    )


SCOPE = AnalysisScope(
    organization_id=ORG,
    class_id=CLASS,
    session_id=SESSION,
    canvas_id=CANVAS,
    group_id=None,
    contributor_participant_id=CHILD_A,
    audience_participant_ids=(CHILD_A,),
    purpose_code=PURPOSE,
)


@dataclass
class AnalysisHarness:
    service: VisionAnalysisService
    store: InMemoryAnalysisStore
    sources: FakeAnalysisSource
    admission: FakeAdmission
    authority: FakeAnalysisAuthority
    context: FakeAnalysisContext
    requests: FakeAssistanceRequests
    jobs: FakeJobLineage
    clock: FakeClock
    ids: SequentialIds
    provider: VisionObservationPort
    snapshot: SourceSnapshot
    receipt: AdmissionReceipt
    pin: AssistancePin
    keys: list[str] = field(default_factory=list)

    def claim(self, *, job_id: str = JOB, attempt_id: str = ATTEMPT,
              **changes: object) -> ObservationClaim:
        base = ObservationClaim(
            job_id=job_id,
            job_attempt_id=attempt_id,
            assistance_id=self.pin.assistance_id,
            expected_request_revision=self.pin.request_revision,
            input_snapshot_ref=self.pin.input_snapshot_ref,
            context_revision=self.pin.context_revision,
        )
        return replace(base, **changes)  # type: ignore[arg-type]

    def set_job(self, *, job_id: str = JOB, attempt_id: str = ATTEMPT,
                state: JobState = JobState.RUNNING, **changes: object) -> JobLineageView:
        view = JobLineageView(
            job_id=job_id,
            organization_id=ORG,
            job_type=VISION_ANALYSIS_JOB_TYPE,
            state=state,
            active_attempt_id=attempt_id,
            request_id=self.pin.assistance_id,
            request_revision=self.pin.request_revision,
            input_hash=self.snapshot.input_hash(),
            context_revision=self.pin.context_revision,
            session_id=self.pin.scope.session_id,
            subject_refs=self.pin.scope.audience_participant_ids,
            purpose_code=self.pin.scope.purpose_code,
            target_id=self.pin.assistance_id,
        )
        view = replace(view, **changes)  # type: ignore[arg-type]
        self.jobs.set(view)
        return view

    def observe(self, claim: ObservationClaim | None = None) -> ObservationResult:
        return self.service.record_observation(claim or self.claim(), correlation_id="corr_fx_1")

    def accepted_analysis(self) -> str:
        result = self.observe()
        assert result.authoritative and result.analysis_id is not None
        return result.analysis_id

    def correction(
        self,
        principal: Principal,
        analysis_id: str,
        *,
        revision: int | None = 1,
        key: str | None = None,
        intended: tuple[str, ...] = ("tiger",),
        reason: str = "Child says the animal is a tiger",
        explanation: str | None = None,
        basis: str | None = None,
        context_revision: int = CONTEXT_REVISION,
        if_match: str | None = None,
    ) -> CorrectionCommand:
        if key is None:
            key = f"key_fx_{len(self.keys) + 1:03d}"
            self.keys.append(key)
        header = if_match if if_match is not None else (
            None if revision is None else analysis_etag(analysis_id, revision)
        )
        return CorrectionCommand(
            principal=principal,
            analysis_id=analysis_id,
            idempotency_key=key,
            if_match=header,
            intended_objects=intended,
            correction_reason=reason,
            expected_context_revision=context_revision,
            child_explanation=explanation,
            basis_correction_ref=basis,
        )


ProviderFactory = Callable[[FakeAnalysisSource, FakeClock], VisionObservationPort]


def build_analysis_harness(
    *,
    provider_factory: ProviderFactory | None = None,
    required_context_mode: ProviderContextMode = ProviderContextMode.IMAGE_ONLY,
    jobs: JobLineagePort | None = None,
) -> AnalysisHarness:
    clock = FakeClock(FIXTURE_START)
    ids = SequentialIds()
    store = InMemoryAnalysisStore()
    sources = FakeAnalysisSource()
    admission = FakeAdmission()
    authority = FakeAnalysisAuthority()
    context = FakeAnalysisContext()
    requests = FakeAssistanceRequests()
    job_lineage = FakeJobLineage()

    snapshot = synthetic_snapshot()
    sources.add(snapshot, SYNTHETIC_RENDER)
    receipt = synthetic_admission(snapshot)
    admission.add(receipt, organization_id=ORG)
    pin = AssistancePin(ASSISTANCE, 1, SNAPSHOT, CONTEXT_REVISION, SCOPE)
    requests.add(pin)

    context.set_context(SESSION, CANVAS, CONTEXT_REVISION, topic_ref="topic_fx_animals")
    context.set_participant(CHILD_A, age_months=60, purposes=frozenset({PURPOSE}))
    context.set_participant(CHILD_B, age_months=120, purposes=frozenset({PURPOSE}))

    authority.grant_teacher(TEACHER.principal_id, TeacherGrant(ORG, frozenset({CLASS})))
    authority.grant_teacher(
        OTHER_CLASS_TEACHER.principal_id, TeacherGrant(ORG, frozenset({OTHER_CLASS}))
    )
    authority.grant_teacher(OUTSIDER.principal_id, TeacherGrant(OTHER_ORG, frozenset({CLASS})))
    authority.bind_device(
        DEVICE_A.principal_id, DeviceBinding(ORG, SESSION, CANVAS, None, CHILD_A, "turn_fx_01")
    )
    authority.bind_device(
        DEVICE_B.principal_id, DeviceBinding(ORG, SESSION, CANVAS, None, CHILD_B, "turn_fx_02")
    )
    authority.bind_device(
        DEVICE_OTHER_CANVAS.principal_id,
        DeviceBinding(ORG, SESSION, "canvas_fx_002", None, CHILD_A, "turn_fx_03"),
    )

    provider = (
        provider_factory(sources, clock)
        if provider_factory is not None
        else FakeVisionObservationProvider(clock=clock.now)
    )
    service = VisionAnalysisService(
        VisionAnalysisDependencies(
            repository=store,
            authority=authority,
            context=context,
            sources=sources,
            admission=admission,
            requests=requests,
            jobs=jobs if jobs is not None else job_lineage,
            provider=provider,
            clock=clock,
            ids=ids,
            required_context_mode=required_context_mode,
        )
    )
    harness = AnalysisHarness(
        service=service,
        store=store,
        sources=sources,
        admission=admission,
        authority=authority,
        context=context,
        requests=requests,
        jobs=job_lineage,
        clock=clock,
        ids=ids,
        provider=provider,
        snapshot=snapshot,
        receipt=receipt,
        pin=pin,
    )
    harness.set_job()
    return harness


class _ScriptedTransport:
    """Offline transport returning one fixed synthetic V2 response (never a network call)."""

    def __init__(self, response: Mapping[str, object]) -> None:
        self.response = response
        self.calls = 0

    def post_json(self, path: str, payload: Mapping[str, object]) -> Mapping[str, object]:
        self.calls += 1
        return self.response


def _text(value: str) -> dict[str, object]:
    return {"value": value, "language": {"status": "DECLARED", "tags": ["en"]}}


def synthetic_v2_response() -> dict[str, object]:
    """A schema-valid synthetic V2 success for the fixture render: wrong label ``cat``, one
    uncalibrated (null) confidence and every legacy observation kind."""

    catalog = vision_profile_catalog_v2()
    profile = catalog.resolve(VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1)
    return {
        "contract_name": "VisionUnderstandingResultV2",
        "contract_version": "2.0",
        "correlation_id": "corr_fx_1",
        "executed_at": "2026-10-16T12:00:05Z",
        "source_image_ref": {"artifact_ref": "render_fx_004", "sha256": RENDER_SHA256},
        "profile_id": str(profile.profile_id),
        "profile_catalog_hash": vision_profile_catalog_hash_v2(catalog),
        "attempt_number": 1,
        "repair_attempted": False,
        "content_policy_version": synthetic_prohibited_lexicon().lexicon_version,
        "policy_match_view_version": VISION_POLICY_MATCH_VIEW_VERSION,
        "policy_execution_state": "PASSED",
        "status": "SUCCEEDED",
        "entities": [
            {"observation_id": "ent-1", "label": _text("cat"), "confidence": 0.71},
            {"observation_id": "ent-2", "label": _text("ball"), "confidence": None},
        ],
        "actions": [{"observation_id": "act-1", "label": _text("sitting"), "actor_ref": "ent-1",
                     "object_ref": None, "confidence": 0.4}],
        "relations": [{"observation_id": "rel-1", "predicate": _text("next to"),
                       "subject_ref": "ent-1", "object_ref": "ent-2", "confidence": None}],
        "themes": [{"observation_id": "thm-1", "label": _text("play"), "evidence_refs": ["ent-1"],
                    "confidence": 0.3}],
        "ambiguous_regions": [{"observation_id": "amb-1", "note": _text("striped area")}],
        "adapter_version": profile.adapter_version,
        "config_hash": vision_profile_config_hash_v2(profile),
        "model_provenance": profile.model_provenance.model_dump(mode="json"),
    }


def build_handoff_examples() -> dict[str, object]:
    """Deterministic H-AI-REVIEW consumer examples: offline legacy-bridge observation, Child
    tiger proposal, Teacher confirmation, record, invalidation intents and downstream meaning."""

    transport = _ScriptedTransport(synthetic_v2_response())
    h = build_analysis_harness(
        provider_factory=lambda sources, clock: LegacyVisionV2Bridge(
            transport=transport, render_loader=sources.read_render, clock=clock.now
        )
    )
    analysis_id = h.accepted_analysis()
    with h.store.transaction() as tx:
        head = tx.get_head(analysis_id)
        observation = tx.get_observation(analysis_id)
    assert head is not None and observation is not None
    candidate = worker_candidate_view(head, observation)
    h.clock.advance(seconds=20)
    proposal = h.service.submit_correction(
        h.correction(DEVICE_A, analysis_id, explanation="It has stripes and a long tail")
    )
    h.clock.advance(seconds=40)
    confirmation = h.service.submit_correction(
        h.correction(TEACHER, analysis_id, revision=2, basis=proposal.correction.correction_id,
                     reason="Teacher confirms the child's tiger")
    )
    meaning = h.service.downstream_meaning(TEACHER, analysis_id)
    provider_result = h.service.resolve_provider_result(TEACHER, provider_result_ref(analysis_id))
    return {
        "provider_result_record": {
            "result_ref": provider_result.result_ref,
            "analysis_id": provider_result.analysis_id,
            "result_contract": provider_result.result_contract,
            "result_sha256": provider_result.result_sha256,
            "canonical_json": provider_result.canonical_json,
        },
        "analysis_worker_candidate": candidate,
        "correction_child_receipt": child_correction_view(proposal),
        "correction_teacher_receipt": teacher_correction_view(confirmation),
        "analysis_record": h.service.analysis_record(TEACHER, analysis_id),
        "invalidation_intents": [
            {
                "event_id": intent.event_id,
                "analysis_id": intent.analysis_id,
                "previous_revision": intent.previous_revision,
                "analysis_revision": intent.analysis_revision,
                "reason": str(intent.reason),
                "correction_ref": intent.correction_ref,
                "occurred_at": intent.occurred_at.isoformat().replace("+00:00", "Z"),
            }
            for intent in h.store.invalidations()
        ],
        "downstream_meaning": {
            "analysis_id": meaning.analysis_id,
            "analysis_revision": meaning.analysis_revision,
            "state": str(meaning.state),
            "confirmed_concepts": list(meaning.confirmed_concepts),
            "confirmation_ref": meaning.confirmation_ref,
            "model_candidates": [
                {"label": c.label, "confidence": c.confidence, "observation_ref": c.observation_ref}
                for c in meaning.model_candidates
            ],
            "child_proposal_refs": list(meaning.child_proposal_refs),
        },
    }


__all__ = [
    "ADMIN",
    "ASSISTANCE",
    "ATTEMPT",
    "CANVAS",
    "CHECKPOINT_CHECKSUM",
    "CHILD_A",
    "CHILD_B",
    "CLASS",
    "CONTEXT_REVISION",
    "DEVICE_A",
    "DEVICE_B",
    "DEVICE_OTHER_CANVAS",
    "FIXTURE_START",
    "JOB",
    "ORG",
    "OTHER_CLASS_TEACHER",
    "OUTSIDER",
    "PURPOSE",
    "RENDER_SHA256",
    "SCOPE",
    "SESSION",
    "SNAPSHOT",
    "SYNTHETIC_RENDER",
    "TEACHER",
    "AnalysisHarness",
    "build_analysis_harness",
    "build_handoff_examples",
    "synthetic_admission",
    "synthetic_snapshot",
    "synthetic_v2_response",
]
