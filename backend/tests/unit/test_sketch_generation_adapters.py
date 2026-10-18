"""BE2-04 SK1.3 adapters: SK-P05, SK-N01/N03 (adapter), SK-C08, SK-C09, SK-C10, eligibility,
job reader, provider mapping, fence token and coordinated ports."""

from __future__ import annotations

import ast
from collections.abc import Mapping
from pathlib import Path

import pytest

from sketch2life.application.ports.ai_jobs import (
    DispatchMessage,
    Principal,
    PrincipalRole,
    QuarantineIntent,
    WorkerDispatchEnvelope,
)
from sketch2life.application.ports.sketch_generation import (
    HANDOFF_CONTRACT_VERSION,
    HandoffRefusal,
    HandoffRefusalCode,
    SketchHandoffV1,
)
from sketch2life.application.services.sketch_generation import CancelCommand
from sketch2life.domain.ai_jobs.completion import Moderation, OutcomeKind
from sketch2life.domain.ai_jobs.model import JobScope, RequestRef
from sketch2life.domain.assistance import RequestStatus
from sketch2life.domain.sketch_proposal import SKETCH_JOB_TYPE, HandoffKind, PipelineState
from sketch2life.infrastructure.ai_jobs.fakes import artifact_fence_scope
from sketch2life.infrastructure.assistance.fakes import CoordinationError
from sketch2life.infrastructure.assistance.harness import (
    CHILD_A,
    LEVEL_2,
    ORG,
    READER,
    SESSION,
    TEACHER,
)
from sketch2life.infrastructure.sketch_generation.adapters import (
    AssistanceHandoffReader,
    sketch_policy_fence_scope,
)
from sketch2life.infrastructure.sketch_generation.fakes import default_outcome
from sketch2life.infrastructure.sketch_generation.harness import (
    JobTypeRouter,
    SketchChainHarness,
    UnknownJobType,
    build_sketch_chain_harness,
)

SRC = Path(__file__).resolve().parents[2] / "src" / "sketch2life"


@pytest.fixture
def c() -> SketchChainHarness:
    return build_sketch_chain_harness()


def resolve(c: SketchChainHarness, assistance_id: str) -> SketchHandoffV1:
    handoff = c.handoffs.resolve(ORG, assistance_id)
    assert isinstance(handoff, SketchHandoffV1), handoff
    return handoff


# ------------------------------------------------------------------ SK-P05
def test_p05_stage_adapter_records_hint_and_never_raises(c: SketchChainHarness) -> None:
    assistance_id = c.ready(c.h.command(level=LEVEL_2))
    assert c.forward_hints() == 1
    (hint,) = c.store.snapshot().hints.values()
    assert hint.assistance_id == assistance_id
    (result,) = c.service.process_inbox(ORG)
    assert result.proposal_id == c.proposal_for(assistance_id)
    second = c.ready(c.h.command(level=LEVEL_2, intent="a dog"))
    c.store.fail_next_commit = True
    assert c.forward_hints() == 1  # the failing store never raises into BE2-03
    assert c.stage.failures == ["RuntimeError"]
    assert c.proposal_for(second) is None  # recovered later by open-by-id
    assert c.service.open_from_handoff(ORG, second).proposal_id == c.proposal_for(second)


# ------------------------------------------------------------------ SK-N01 / SK-N03 adapter
def test_n01_adapter_refuses_requests_that_are_not_analysis_ready(c: SketchChainHarness) -> None:
    scheduled = c.h.submit(c.h.command(level=LEVEL_2)).request
    assert scheduled.status is not RequestStatus.ANALYSIS_READY
    refused = c.handoffs.resolve(ORG, scheduled.assistance_id)
    assert refused == HandoffRefusal(HandoffRefusalCode.NOT_READY)
    assert c.service.open_from_handoff(ORG, scheduled.assistance_id).code == "HANDOFF_NOT_READY"


def test_n03_adapter_unreadable_for_foreign_org_or_lost_disclosure(c: SketchChainHarness) -> None:
    assistance_id = c.ready(c.h.command(level=LEVEL_2))
    assert c.handoffs.resolve("org_fx_school_b", assistance_id) == HandoffRefusal(
        HandoffRefusalCode.UNREADABLE)
    del c.h.authority.teachers[READER.principal_id]
    assert c.handoffs.resolve(ORG, assistance_id) == HandoffRefusal(
        HandoffRefusalCode.UNREADABLE)
    assert c.handoffs.resolve(ORG, "assist_fx_missing") == HandoffRefusal(
        HandoffRefusalCode.UNREADABLE)
    with pytest.raises(ValueError):
        AssistanceHandoffReader(lambda: c.h.service, c.h.vision, c.h.owner, c.h.sources,
                                Principal("device_fx_a", ORG, PrincipalRole.DEVICE))


class _TamperedVision:
    """Wraps the real Vision service; changes one lineage field of the analysis record."""

    def __init__(self, inner: object, field: str) -> None:
        self._inner = inner
        self._field = field

    def analysis_record(self, principal: Principal, analysis_id: str) -> Mapping[str, object]:
        record = dict(self._inner.analysis_record(principal, analysis_id))  # type: ignore[attr-defined]
        candidate = dict(record["candidate"])
        candidate[self._field] = "tampered_fx"
        record["candidate"] = candidate
        return record

    def downstream_meaning(self, principal: Principal, analysis_id: str) -> object:
        return self._inner.downstream_meaning(principal, analysis_id)  # type: ignore[attr-defined]


@pytest.mark.parametrize("field", ["job_id", "job_attempt_id", "assistance_id"])
def test_n04_lineage_mismatch_is_refused(c: SketchChainHarness, field: str) -> None:
    assistance_id = c.ready(c.h.command(level=LEVEL_2))
    reader = AssistanceHandoffReader(lambda: c.h.service,
                                     _TamperedVision(c.h.vision, field),  # type: ignore[arg-type]
                                     c.h.owner, c.h.sources, READER)
    assert reader.resolve(ORG, assistance_id) == HandoffRefusal(HandoffRefusalCode.MISMATCH)


# ------------------------------------------------------------------ SK-C09
def test_c09_projection_analysis_and_cache_hit_paths(c: SketchChainHarness) -> None:
    first = c.ready(c.h.command(level=LEVEL_2, intent="a cat with stripes"))
    request = c.h.request(first)
    handoff = resolve(c, first)
    binding = handoff.binding
    assert handoff.contract_version == HANDOFF_CONTRACT_VERSION == "sketch-handoff-v1"
    assert request.handoff is not None
    facts = request.facts
    assert (binding.handoff_kind, binding.cache_source_assistance_id) == (HandoffKind.ANALYSIS,
                                                                          None)
    assert (binding.analysis_id, binding.analysis_revision, binding.vision_job_id,
            binding.vision_attempt_id) == (request.handoff.analysis_id,
                                           request.handoff.analysis_revision,
                                           request.handoff.job_id, request.handoff.attempt_id)
    assert (binding.organization_id, binding.class_id, binding.session_id, binding.canvas_id,
            binding.group_id, binding.audience, binding.purpose_code,
            binding.context_revision) == (facts.organization_id, facts.class_id,
                                          facts.session_id, facts.canvas_id, facts.group_id,
                                          facts.audience, facts.purpose_code,
                                          facts.context_revision)
    assert (binding.source.snapshot_ref, binding.source.input_hash,
            binding.source.render_sha256) == (facts.source.snapshot_ref, facts.source.input_hash,
                                              facts.source.render_sha256)
    assert binding.requested_level == request.requested_level == LEVEL_2
    assert binding.requester_principal_id == request.requester.principal_id
    assert binding.assistance_context_digest == request.assistance_context_digest
    assert binding.meaning.state == "unconfirmed"
    cached = c.h.submit(c.h.command(level=LEVEL_2, intent="a cat with stripes")).request
    assert cached.cache_hit_of is not None and cached.cache_hit_of.assistance_id == first
    hit = resolve(c, cached.assistance_id).binding
    assert (hit.handoff_kind, hit.cache_source_assistance_id) == (HandoffKind.CACHE_HIT, first)
    assert (hit.analysis_id, hit.vision_job_id, hit.vision_attempt_id) == (
        binding.analysis_id, binding.vision_job_id, binding.vision_attempt_id)
    assert hit.assistance_id == cached.assistance_id != first


FORBIDDEN_IMPORTS = ("sketch2life.domain.assistance", "sketch2life.application.ports.assistance",
                     "sketch2life.domain.vision", "sketch2life.application.services.vision",
                     "sketch2life.application.ports.vision", "sketch2life.infrastructure")


@pytest.mark.parametrize("relative", [
    "domain/sketch_proposal.py", "application/ports/sketch_generation.py",
    "application/services/sketch_generation.py",
])
def test_c09_domain_and_application_import_no_producer_types(relative: str) -> None:
    tree = ast.parse((SRC / relative).read_text(encoding="utf-8"))
    modules = [n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    modules += [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
    allowed_vision = {"sketch2life.domain.vision_context"}  # canonical hashing helper only
    for module in modules:
        if module in allowed_vision:
            continue
        assert not module.startswith(FORBIDDEN_IMPORTS), (relative, module)


# ------------------------------------------------------------------ eligibility / reader
def test_sketch_eligibility_rules(c: SketchChainHarness) -> None:
    proposal_id = c.open_ready(c.h.command(level=LEVEL_2))
    proposal = c.proposal(proposal_id)
    scope = JobScope(ORG, SESSION, (CHILD_A,), "ai_drawing_assistance", proposal_id)
    good = RequestRef(proposal_id, 1, proposal.current.generation_digest, 3)
    check = c.sketch_eligibility.check
    assert check(scope=scope, request_ref=good, job_type=SKETCH_JOB_TYPE).eligible
    assert check(scope=scope, request_ref=RequestRef("sketch_fx_none", 1, "0" * 64, 3),
                 job_type=SKETCH_JOB_TYPE).reason_code == "REQUEST_NOT_FOUND"
    assert check(scope=scope, request_ref=RequestRef(proposal_id, 2, good.input_hash, 3),
                 job_type=SKETCH_JOB_TYPE).reason_code == "CONTEXT_CHANGED"
    assert check(scope=scope, request_ref=RequestRef(proposal_id, 1, "0" * 64, 3),
                 job_type=SKETCH_JOB_TYPE).reason_code == "CONTEXT_CHANGED"
    other_org = JobScope("org_fx_school_b", SESSION, (CHILD_A,), "ai_drawing_assistance",
                         proposal_id)
    assert check(scope=other_org, request_ref=good,
                 job_type=SKETCH_JOB_TYPE).reason_code == "REQUEST_NOT_FOUND"
    assert check(scope=scope, request_ref=RequestRef("anything", 1, "0" * 64, 3),
                 job_type="speech_transcription").eligible  # other types pass through
    c.service.cancel(CancelCommand(TEACHER, proposal_id, "key_fx_c", proposal.etag()))
    assert check(scope=scope, request_ref=good,
                 job_type=SKETCH_JOB_TYPE).reason_code == "CANCELLED_BY_TEACHER"


def test_job_reader_and_semantic_lookup(c: SketchChainHarness) -> None:
    proposal_id = c.open_ready(c.h.command(level=LEVEL_2))
    proposal = c.proposal(proposal_id)
    job_id = proposal.current.job_id
    assert job_id is not None
    evidence = c.job_reader.get(job_id)
    assert evidence is not None and evidence.job_type == SKETCH_JOB_TYPE
    assert (evidence.request_id, evidence.request_revision, evidence.input_hash) == (
        proposal_id, 1, proposal.current.generation_digest)
    assert evidence.state == "queued" and not evidence.terminal
    assert c.job_reader.get("job_fx_missing") is None
    request = c.service._job_request(proposal)  # noqa: SLF001 - frozen schedule identity
    assert c.job_reader.find_semantic(request) == job_id


def test_provider_adapter_maps_success_unsafe_and_failure(c: SketchChainHarness) -> None:
    proposal_id = c.open_ready(c.h.command(level=LEVEL_2))
    c.router.crash_after_provider = True
    routed = c.run_sketch(proposal_id, reconcile=False)
    assert routed is not None
    claim = routed.outcome
    assert claim.kind is OutcomeKind.SUCCESS and claim.moderation is Moderation.PASSED  # type: ignore[attr-defined]
    assert len(claim.outputs) == 2  # type: ignore[attr-defined]
    c.generator.script = lambda r: default_outcome(r, unsafe=True)
    other = c.open_ready(c.h.command(level=LEVEL_2, intent="a dog"))
    c.router.crash_after_provider = True
    unsafe = c.run_sketch(other, reconcile=False)
    assert unsafe is not None and unsafe.outcome.moderation is Moderation.UNSAFE  # type: ignore[attr-defined]


# ------------------------------------------------------------------ coordination
def test_fence_token_scopes_and_artifact_epochs(c: SketchChainHarness) -> None:
    token = c.decision.token(ORG, ("artifact_fx_b", "artifact_fx_a"), "set_fx")
    assert [scope for scope, _ in token.epochs] == [
        f"eligibility:{ORG}", f"analysis:{ORG}", sketch_policy_fence_scope(ORG),
        artifact_fence_scope("artifact_fx_a"), artifact_fence_scope("artifact_fx_b")]
    c.h.fences.bump(artifact_fence_scope("artifact_fx_a"))
    assert c.decision.token(ORG, ("artifact_fx_a", "artifact_fx_b"), "set_fx") != token
    assert c.publish_policy(c.policy.snapshot) is True
    assert dict(c.decision.token(ORG, (), "x").epochs)[sketch_policy_fence_scope(ORG)] == 1


def test_coordinated_repository_refuses_inside_foundation_unit(c: SketchChainHarness) -> None:
    with c.h.coordinator.foundation(), pytest.raises(CoordinationError), \
            c.repository.transaction():
        pass


def test_coordinated_artifact_port_runs_now_or_deferred(c: SketchChainHarness) -> None:
    first = c.raw_artifacts.put(ORG, b"fx-1", job_id="job_fx", attempt_id="att_fx")
    second = c.raw_artifacts.put(ORG, b"fx-2", job_id="job_fx", attempt_id="att_fx")
    assert c.owner_quarantine((first.artifact_ref,)) is True
    with c.h.coordinator.assistance():
        assert c.owner_quarantine((second.artifact_ref,)) is False
        assert second.artifact_ref not in c.raw_artifacts.quarantined
    assert second.artifact_ref in c.raw_artifacts.quarantined
    assert [e.bumped for e in c.artifact_port.audit] == [True, True]
    c.artifact_port.fail_next_quarantine = True
    with pytest.raises(RuntimeError):
        c.artifact_port.quarantine(QuarantineIntent("evt_fx", ORG, "job_fx", "att_fx",
                                                    (first.artifact_ref,), "X"), caller="t")
    assert len(c.artifact_port.audit) == 2 and c.audit_violations() == []
    assert c.h.coordinator.deferred_failures == []


# ------------------------------------------------------------------ SK-C08 router
def test_c08_router_table_unknown_type_and_started_guard(c: SketchChainHarness) -> None:
    assert JobTypeRouter.ROUTES == ("vision_analysis", "sketch_generation")
    message = DispatchMessage("msg_fx_x", "job_fx_x", "att_fx_x", 1, "unknown_type",
                              RequestRef("req_fx", 1, "0" * 64, 3))
    c.h.queue.enqueue(WorkerDispatchEnvelope(message, "cap_fx"))
    with pytest.raises(UnknownJobType):
        c.router.run_next()
    assert [e.message.message_id for e in c.h.queue.messages] == ["msg_fx_x"]
    assert c.router.calls == []  # no start before a route is chosen
    c.h.queue.messages.clear()
    # Vision redelivered while running/finished -> started False -> nothing else is called.
    c.h.submit(c.h.command(level=LEVEL_2))
    c.h.dispatch()
    envelope = c.h.queue.messages[0]
    assert c.router.run_next() is not None
    last = c.h.last_envelope
    c.h.queue.redeliver(envelope)
    before = list(c.router.calls)
    duplicate = c.router.run_next()
    assert duplicate is not None and not duplicate.started
    assert c.router.calls[len(before):] == [("start", "vision_analysis")]
    assert c.h.last_envelope is last
    c.h.clock.advance(seconds=6)
    # Sketch refused by eligibility -> no provider / accept.
    proposal_id = c.open_ready(c.h.command(level=LEVEL_2, intent="a fish"))
    proposal = c.proposal(proposal_id)
    c.sketch_jobs.dispatch_outbox()
    c.service.cancel(CancelCommand(TEACHER, proposal_id, "key_fx_c", proposal.etag()))
    refused = None
    while (routed := c.router.run_next()) is not None:
        if routed.job_type == SKETCH_JOB_TYPE:
            refused = routed
    assert refused is not None and not refused.started
    assert not any(kind in {"provider", "accept"} for kind, _ in c.router.calls)
    assert c.provider.runs == 0


# ------------------------------------------------------------------ SK-C10
def test_c10_one_port_instance_and_raw_bypass_is_detected(c: SketchChainHarness) -> None:
    assert c.port_identity_ok()
    assert c.a1_job_deps.artifacts.port is c.sketch_job_deps.artifacts.port  # type: ignore[attr-defined]
    proposal_id = c.open_ready(c.h.command(level=LEVEL_2))
    c.run_sketch(proposal_id)
    assert c.proposal(proposal_id).current.pipeline_state is (
        PipelineState.PENDING_TEACHER_REVIEW)
    assert c.audit_violations() == []
    promoted = c.proposal(proposal_id).current.promoted
    assert promoted is not None
    c.raw_artifacts.owner_quarantine((promoted.result_document.artifact_ref,), "BYPASS")
    assert c.audit_violations() != []
