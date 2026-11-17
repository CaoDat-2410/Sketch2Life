"""BE2-04 SK1 fault and race acceptance over the in-memory shared coordinator."""

from __future__ import annotations

from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier, Event, Thread, current_thread
from typing import Any

import pytest

from sketch2life.application.ports.ai_jobs import QuarantineIntent, WorkerDispatchEnvelope
from sketch2life.application.ports.sketch_generation import (
    CleanupIntent,
    JobCreateKind,
    JobCreateOutcome,
    SketchJobCreate,
    SketchJobEvidence,
)
from sketch2life.application.services.ai_jobs import FIXTURE_RETRY_POLICY
from sketch2life.application.services.sketch_generation import (
    CancelCommand,
    NoticeKind,
    OpenOutcome,
    OwnerNotice,
    ReviseLevelCommand,
    SketchError,
)
from sketch2life.application.services.vision_analysis import CorrectionCommand
from sketch2life.domain.ai_jobs.completion import CompletionClaim, Moderation, OutcomeKind
from sketch2life.domain.sketch_proposal import PipelineState, StatusReason
from sketch2life.domain.vision_analysis import analysis_etag
from sketch2life.infrastructure.ai_jobs.fakes import (
    artifact_fence_scope,
    eligibility_fence_scope,
)
from sketch2life.infrastructure.assistance.fakes import (
    CoordinationError,
    analysis_fence_scope,
)
from sketch2life.infrastructure.assistance.harness import (
    CANVAS_P,
    CHILD_A,
    DEVICE_A,
    GROUP,
    LEVEL,
    ORG,
    SESSION,
    TEACHER,
)
from sketch2life.infrastructure.sketch_generation.adapters import LostReply
from sketch2life.infrastructure.sketch_generation.fakes import default_outcome
from sketch2life.infrastructure.sketch_generation.harness import (
    SketchChainHarness,
    build_sketch_chain_harness,
    build_sketch_unit_harness,
)


def _replace_attr(target: object, name: str, replacement: object) -> None:
    setattr(target, name, replacement)


@pytest.fixture(autouse=True)
def _audit_chain_harness_teardown(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    factory = build_sketch_chain_harness
    created: list[SketchChainHarness] = []

    def tracked(*args: Any, **kwargs: Any) -> SketchChainHarness:
        harness = factory(*args, **kwargs)
        created.append(harness)
        return harness

    monkeypatch.setitem(globals(), "build_sketch_chain_harness", tracked)
    yield
    for harness in created:
        assert harness.port_identity_ok()
        assert harness.audit_violations() == []
        assert harness.h.coordinator.deferred_failures == []


def _open(c: SketchChainHarness, *, intent: str = "race sketch") -> str:
    return c.open_ready(c.h.command(intent=intent))


def _open_for_assistance(c: SketchChainHarness, assistance_id: str) -> str:
    c.forward_hints()
    c.service.process_inbox(ORG)
    proposal_id = c.proposal_for(assistance_id)
    assert proposal_id is not None
    return proposal_id


def _stage_only(
    c: SketchChainHarness, proposal_id: str
) -> tuple[WorkerDispatchEnvelope, CompletionClaim]:
    c.router.crash_after_provider = True
    result = c.run_sketch(proposal_id, reconcile=False)
    assert result is not None and result.reason == "CRASHED_BEFORE_COMPLETION"
    envelope = c.router.last_sketch
    assert envelope is not None
    assert isinstance(result.outcome, CompletionClaim)
    c.sketch_jobs.accept_completion(envelope.capability, result.outcome)
    return envelope, result.outcome


def _publish_after_current(c: SketchChainHarness, scope: str,
                           publication: object) -> None:
    original = c.handoffs.current
    fired = False

    def current(binding: object) -> object:
        nonlocal fired
        facts = original(binding)  # type: ignore[arg-type]
        if not fired:
            fired = True

            def publish() -> None:
                publication()  # type: ignore[operator]
                c.h.fences.bump(scope)

            assert c.h.coordinator.request_publication(publish)
        return facts

    _replace_attr(c.handoffs, "current", current)


@pytest.mark.parametrize("order", ["vision_first", "sketch_first"])
def test_r22_mixed_queue_routes_both_job_types_without_losing_envelopes(
    order: str,
) -> None:
    c = build_sketch_chain_harness()
    assistance_id = c.ready(c.h.command(intent=f"mixed queue {order}"))
    if order == "vision_first":
        vision = c.h.submit(c.h.command(intent=f"second Vision {order}"))
        c.h.dispatch()
        proposal_id = _open_for_assistance(c, assistance_id)
        c.sketch_jobs.dispatch_outbox()
    else:
        proposal_id = _open_for_assistance(c, assistance_id)
        c.sketch_jobs.dispatch_outbox()
        vision = c.h.submit(c.h.command(intent=f"second Vision {order}"))
        c.h.dispatch()
    expected = ("vision_analysis", "sketch_generation") if order == "vision_first" else (
        "sketch_generation", "vision_analysis")
    results = [c.router.run_next(), c.router.run_next()]
    assert all(result is not None and result.started for result in results)
    assert tuple(result.job_type for result in results if result is not None) == expected
    assert c.router.run_next() is None
    assert c.generator.calls[proposal_id] == 1
    assert sum(kind == "finish_vision" for kind, _ in c.router.calls) == 2
    assert c.h.service.reconcile(vision.request.assistance_id) is not None
    assert c.service.reconcile(proposal_id) is not None
    assert c.proposal(proposal_id).current.pipeline_state is PipelineState.PENDING_TEACHER_REVIEW
    assert c.h.request(assistance_id).handoff is not None
    assert c.h.queue.messages == []
    assert c.audit_violations() == []


def test_r23_cancelled_sketch_is_refused_then_vision_runs() -> None:
    c = build_sketch_chain_harness()
    proposal_id = _open(c)
    c.sketch_jobs.dispatch_outbox()
    proposal = c.proposal(proposal_id)
    c.service.cancel(CancelCommand(TEACHER, proposal_id, "race_cancel_sketch",
                                   proposal.etag()))
    vision = c.h.submit(c.h.command(intent="Vision behind cancelled sketch"))
    c.h.dispatch()
    before = len(c.router.calls)
    refused = c.router.run_next()
    routed_vision = c.router.run_next()
    assert refused is not None and refused.job_type == "sketch_generation"
    assert not refused.started and refused.reason == "JOB_NOT_QUEUED"
    assert routed_vision is not None and routed_vision.started
    assert c.generator.calls.get(proposal_id, 0) == 0
    assert sum(kind == "finish_vision" for kind, _ in c.router.calls[before:]) == 1
    assert c.h.service.reconcile(vision.request.assistance_id) is not None


def test_r28_duplicate_vision_before_sketch_does_not_touch_vision_state() -> None:
    c = build_sketch_chain_harness()
    assistance_id = c.ready(c.h.command())
    c.h.submit(c.h.command(intent="second Vision for duplicate delivery"))
    c.h.dispatch()
    duplicate = c.h.queue.receive()
    assert duplicate is not None
    started = c.h.jobs.start_attempt(duplicate.capability, duplicate.message.job_id,
                                     duplicate.message.attempt_id)
    assert started.started
    c.h.queue.redeliver(duplicate)
    proposal_id = _open_for_assistance(c, assistance_id)
    c.sketch_jobs.dispatch_outbox()
    last_envelope = c.h.last_envelope
    before = list(c.router.calls)
    refused = c.router.run_next()
    assert refused is not None and refused.job_type == "vision_analysis"
    assert not refused.started and "duplicate" in (refused.reason or "").lower()
    assert c.h.last_envelope is last_envelope
    assert c.router.calls[len(before):] == [("start", "vision_analysis")]
    routed = c.router.run_next()
    assert routed is not None and routed.job_type == "sketch_generation" and routed.started
    assert c.generator.calls[proposal_id] == 1


@pytest.mark.parametrize("order", ["vision_first", "sketch_first"])
def test_r29_cancelled_vision_does_not_block_sketch_in_either_order(order: str) -> None:
    c = build_sketch_chain_harness()
    assistance_id = c.ready(c.h.command(intent=f"R29 {order}"))
    proposal_id = _open_for_assistance(c, assistance_id)
    finished_before = sum(kind == "finish_vision" for kind, _ in c.router.calls)
    if order == "sketch_first":
        c.sketch_jobs.dispatch_outbox()
    request = c.h.submit(c.h.command(intent=f"cancelled Vision {order}"))
    c.h.dispatch()
    c.h.service.cancel(c.h.cancel_command(DEVICE_A, request.request.assistance_id))
    c.sketch_jobs.dispatch_outbox()
    results = [c.router.run_next(), c.router.run_next()]
    assert all(result is not None for result in results)
    by_type = {result.job_type: result for result in results if result is not None}
    assert set(by_type) == {"vision_analysis", "sketch_generation"}
    assert not by_type["vision_analysis"].started
    assert by_type["sketch_generation"].started
    assert c.generator.calls[proposal_id] == 1
    assert sum(kind == "finish_vision" for kind, _ in c.router.calls) == finished_before
    reconciled = c.service.reconcile(proposal_id)
    assert reconciled is not None
    assert reconciled.current.pipeline_state is PipelineState.PENDING_TEACHER_REVIEW


def test_r24_quarantine_before_c8_prevents_promotion() -> None:
    c = build_sketch_chain_harness()
    proposal_id = _open(c)
    _, claim = _stage_only(c, proposal_id)
    proposal = c.proposal(proposal_id)
    assert proposal.current.job_id is not None
    staged = c.store.snapshot().staged[f"{proposal.current.job_id}:{claim.attempt_id}"]
    c.owner_quarantine(staged.refs(), "R24_OWNER")
    updated = c.service.reconcile(proposal_id)
    assert updated is not None
    assert updated.current.pipeline_state is PipelineState.STALE
    assert updated.current.status_reason is StatusReason.ARTIFACT_QUARANTINED
    assert not any(e.event_type == "sketch.proposal_ready"
                   for e in c.store.snapshot().events)


def test_r13_owner_consent_change_after_c8_read_retries_to_stale() -> None:
    c = build_sketch_chain_harness()
    proposal_id = _open(c)
    _stage_only(c, proposal_id)

    def revoke() -> None:
        c.h.owner.update_member(CHILD_A, consent_effective=False)

    _publish_after_current(c, eligibility_fence_scope(ORG), revoke)
    stale = c.service.reconcile(proposal_id)
    assert stale is not None and stale.current.pipeline_state is PipelineState.STALE
    assert stale.current.status_reason is StatusReason.CONSENT_REVOKED
    assert not any(e.event_type == "sketch.proposal_ready"
                   for e in c.store.snapshot().events)
    assert stale.current.promoted is None


def test_r14_teacher_confirmation_between_analysis_reads_retries_to_stale() -> None:
    c = build_sketch_chain_harness()
    proposal_id = _open(c)
    _stage_only(c, proposal_id)
    assistance_id = c.proposal(proposal_id).binding.assistance_id
    analysis_id = c.h.request(assistance_id).handoff.analysis_id  # type: ignore[union-attr]
    original = c.h.vision.analysis_record
    fired = False

    def after_record(principal: object, requested_analysis_id: str) -> object:
        nonlocal fired
        record = original(principal, requested_analysis_id)  # type: ignore[arg-type]
        if not fired and requested_analysis_id == analysis_id:
            fired = True
            head = c.h.vision_store.snapshot().heads[analysis_id]
            c.h.vision.submit_correction(CorrectionCommand(
                principal=TEACHER, analysis_id=analysis_id,
                idempotency_key="key_fx_r14_confirmation",
                if_match=analysis_etag(analysis_id, head.analysis_revision),
                intended_objects=("cat",), correction_reason="Teacher confirms fixture meaning",
                expected_context_revision=head.context_revision))
        return record

    _replace_attr(c.h.vision, "analysis_record", after_record)
    stale = c.service.reconcile(proposal_id)
    assert fired and stale is not None
    assert stale.current.pipeline_state is PipelineState.STALE
    assert stale.current.status_reason is StatusReason.MEANING_CHANGED
    assert stale.current.promoted is None
    assert not any(e.event_type == "sketch.proposal_ready"
                   for e in c.store.snapshot().events)


def test_r15_render_publication_after_c8_read_retries_to_source_changed() -> None:
    c = build_sketch_chain_harness()
    proposal_id = _open(c)
    _stage_only(c, proposal_id)
    original = c.h.sources.sources[(ORG, CANVAS_P, c.h.source_p.snapshot.checkpoint.checkpoint_id)]
    published = False

    def publish_render() -> None:
        nonlocal published
        render = replace(original.snapshot.render, render_ref="render_fx_r15",
                         render_sha256="f" * 64)
        c.h.sources.add(ORG, CANVAS_P,
                         replace(original, snapshot=replace(original.snapshot, render=render)))
        published = True

    _publish_after_current(c, eligibility_fence_scope(ORG), publish_render)
    stale = c.service.reconcile(proposal_id)
    assert published and stale is not None
    assert stale.current.pipeline_state is PipelineState.STALE
    assert stale.current.status_reason is StatusReason.SOURCE_CHANGED


def test_r16_policy_publication_after_c8_read_retries_to_policy_changed() -> None:
    c = build_sketch_chain_harness()
    proposal_id = _open(c)
    _stage_only(c, proposal_id)
    assert c.policy.snapshot is not None
    changed = replace(c.policy.snapshot, rules={})
    _publish_after_current(c, "sketch-policy:" + ORG,
                           lambda: c.publish_policy(changed))
    stale = c.service.reconcile(proposal_id)
    assert stale is not None and stale.current.pipeline_state is PipelineState.STALE
    assert stale.current.status_reason is StatusReason.POLICY_CHANGED


def test_r17_analysis_epoch_only_change_keeps_meaning_and_promotes_once() -> None:
    c = build_sketch_chain_harness()
    proposal_id = _open(c)
    _stage_only(c, proposal_id)
    _publish_after_current(c, analysis_fence_scope(ORG), lambda: None)
    promoted = c.service.reconcile(proposal_id)
    assert promoted is not None
    assert promoted.current.pipeline_state is PipelineState.PENDING_TEACHER_REVIEW
    assert sum(e.event_type == "sketch.proposal_ready" for e in c.store.snapshot().events) == 1


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ("consent", StatusReason.CONSENT_REVOKED),
        ("source", StatusReason.SOURCE_CHANGED),
        ("audience", StatusReason.AUDIENCE_CHANGED),
        ("context", StatusReason.CONTEXT_CHANGED),
        ("teacher_confirmation", StatusReason.MEANING_CHANGED),
    ],
)
def test_n09_changed_facts_before_provider_gate_refuse_generation(
    change: str, reason: StatusReason,
) -> None:
    c = build_sketch_chain_harness()
    command = c.h.group_command() if change == "audience" else c.h.command()
    assistance_id = c.ready(command)
    c.forward_hints()
    c.service.process_inbox(ORG)
    proposal_id = c.proposal_for(assistance_id)
    assert proposal_id is not None

    if change == "consent":
        c.h.owner.update_member(CHILD_A, consent_effective=False)
        c.h.owner_eligibility.revoked_subjects.add(CHILD_A)
    elif change == "source":
        original = c.h.sources.sources[(ORG, CANVAS_P,
                                        c.h.source_p.snapshot.checkpoint.checkpoint_id)]
        render = replace(original.snapshot.render, render_ref="render_fx_n09_changed",
                         render_sha256="e" * 64)
        c.h.sources.add(ORG, CANVAS_P,
                         replace(original, snapshot=replace(original.snapshot, render=render)))
    elif change == "audience":
        roster = c.h.owner.rosters[(SESSION, GROUP)]
        c.h.owner.rosters[(SESSION, GROUP)] = replace(roster, members=(CHILD_A,), revision=2)
    elif change == "context":
        canvas = c.h.owner.canvases[CANVAS_P]
        c.h.owner.canvases[CANVAS_P] = replace(canvas, context_revision=canvas.context_revision + 1)
    else:
        proposal = c.proposal(proposal_id)
        head = c.h.vision_store.snapshot().heads[proposal.binding.analysis_id]
        c.h.vision.submit_correction(CorrectionCommand(
            principal=TEACHER, analysis_id=head.analysis_id,
            idempotency_key="key_fx_n09_teacher_confirmation",
            if_match=analysis_etag(head.analysis_id, head.analysis_revision),
            intended_objects=("tiger",), correction_reason="Teacher confirms meaning",
            expected_context_revision=head.context_revision))

    dispatched = c.sketch_jobs.dispatch_outbox()
    if change == "consent":
        assert dispatched == 0  # foundation eligibility cancels before queue/provider entry
        assert c.router.run_next() is None
    else:
        routed = c.router.run_next()
        assert routed is not None
        assert routed.started
    updated = c.service.reconcile(proposal_id)
    assert updated is not None and updated.current.pipeline_state is PipelineState.STALE
    assert updated.current.status_reason is reason
    assert c.generator.calls.get(proposal_id, 0) == 0


def test_r18_two_unstable_decision_rounds_make_no_write_then_reconcile() -> None:
    c = build_sketch_chain_harness()
    proposal_id = _open(c)
    _stage_only(c, proposal_id)
    before = c.store.snapshot()
    original = c.handoffs.current
    reads = 0

    def change_epoch_each_round(binding: object) -> object:
        nonlocal reads
        facts = original(binding)  # type: ignore[arg-type]
        reads += 1
        assert c.h.coordinator.request_publication(
            lambda: c.h.fences.bump(analysis_fence_scope(ORG)))
        return facts

    _replace_attr(c.handoffs, "current", change_epoch_each_round)
    with pytest.raises(SketchError, match="DECISION_UNRESOLVED"):
        c.service.reconcile(proposal_id)
    after = c.store.snapshot()
    assert reads == 2
    assert after.proposals[proposal_id] == before.proposals[proposal_id]
    assert after.events == before.events and after.staged == before.staged

    _replace_attr(c.handoffs, "current", original)
    stable = c.service.reconcile(proposal_id)
    assert stable is not None
    assert stable.current.pipeline_state is PipelineState.PENDING_TEACHER_REVIEW
    assert sum(e.event_type == "sketch.proposal_ready" for e in c.store.snapshot().events) == 1


def test_r16_revise_level_rechecks_policy_after_token_change() -> None:
    c = build_sketch_unit_harness()
    proposal_id = c.open().proposal_id
    assert proposal_id is not None
    c.run(proposal_id)
    policy = c.policy.snapshot
    assert policy is not None
    token = c.decision.token
    fired = False

    def token_then_remove_rule(*args: object, **kwargs: object) -> object:
        nonlocal fired
        result = token(*args, **kwargs)  # type: ignore[arg-type]
        if not fired:
            fired = True
            c.policy.snapshot = replace(policy, rules={})
            c.decision.bump(f"org:{ORG}")
        return result

    _replace_attr(c.decision, "token", token_then_remove_rule)
    proposal = c.proposal(proposal_id)
    with pytest.raises(SketchError, match="LEVEL_NOT_ALLOWED"):
        c.service.revise_level(ReviseLevelCommand(
            TEACHER, proposal_id, "key_fx_r16_revise", proposal.etag(), LEVEL))
    assert fired and c.proposal(proposal_id).current.version == 1
    assert c.proposal(proposal_id).current.pipeline_state is PipelineState.PENDING_TEACHER_REVIEW


def test_r19_c1_owner_change_during_open_never_schedules_stale_proposal() -> None:
    c = build_sketch_chain_harness()
    assistance_id = c.ready(c.h.command())

    def revoke() -> None:
        c.h.owner.update_member(CHILD_A, consent_effective=False)

    _publish_after_current(c, eligibility_fence_scope(ORG), revoke)
    result = c.service.open_from_handoff(ORG, assistance_id)
    assert result.outcome is OpenOutcome.CREATED and result.proposal_id is not None
    proposal = c.proposal(result.proposal_id)
    assert proposal.current.pipeline_state is PipelineState.STALE
    assert proposal.current.status_reason is StatusReason.CONSENT_REVOKED
    assert proposal.current.job_id is None
    assert not any(job.job_type == "sketch_generation"
                   for job in c.h.job_store.snapshot().jobs.values())


def test_r19_c5_owner_change_prevents_provider_start() -> None:
    c = build_sketch_chain_harness()
    proposal_id = _open(c)

    def revoke() -> None:
        c.h.owner.update_member(CHILD_A, consent_effective=False)

    _publish_after_current(c, eligibility_fence_scope(ORG), revoke)
    result = c.run_sketch(proposal_id, reconcile=False)
    assert result is not None and result.started
    proposal = c.proposal(proposal_id)
    assert proposal.current.pipeline_state is PipelineState.STALE
    assert proposal.current.status_reason is StatusReason.CONSENT_REVOKED
    assert c.generator.calls.get(proposal_id, 0) == 0


def test_r20_failed_c8_commit_rolls_back_and_retry_promotes() -> None:
    c = build_sketch_chain_harness()
    proposal_id = _open(c)
    _stage_only(c, proposal_id)
    before = c.store.snapshot()
    token = c.decision.token

    def arm_failed_commit(*args: object, **kwargs: object) -> object:
        result = token(*args, **kwargs)  # type: ignore[arg-type]

        def fail() -> None:
            c.store.fail_next_commit = True

        c.store.before_commit = fail
        return result

    _replace_attr(c.decision, "token", arm_failed_commit)
    with pytest.raises(RuntimeError, match="injected sketch commit failure"):
        c.service.reconcile(proposal_id)
    after = c.store.snapshot()
    assert after.proposals[proposal_id] == before.proposals[proposal_id]
    assert after.events == before.events
    assert after.staged == before.staged
    _replace_attr(c.decision, "token", token)
    promoted = c.service.reconcile(proposal_id)
    assert promoted is not None
    assert promoted.current.pipeline_state is PipelineState.PENDING_TEACHER_REVIEW


def test_r21_unchanged_currentness_promotes_in_one_decision_round() -> None:
    c = build_sketch_chain_harness()
    proposal_id = _open(c)
    _stage_only(c, proposal_id)
    token = c.decision.token
    calls = 0

    def count_token(*args: object, **kwargs: object) -> object:
        nonlocal calls
        calls += 1
        return token(*args, **kwargs)  # type: ignore[arg-type]

    _replace_attr(c.decision, "token", count_token)
    promoted = c.service.reconcile(proposal_id)
    assert promoted is not None
    assert promoted.current.pipeline_state is PipelineState.PENDING_TEACHER_REVIEW
    assert calls == 2  # snapshot and commit check in one round


def test_r01_hint_and_open_by_id_race_to_one_proposal_and_job() -> None:
    c = build_sketch_chain_harness()
    assistance_id = c.ready(c.h.command())
    c.forward_hints()
    original = c.handoffs.current
    barrier = Barrier(2)

    def synchronize(binding: object) -> object:
        result = original(binding)  # type: ignore[arg-type]
        barrier.wait(timeout=3)
        return result

    _replace_attr(c.handoffs, "current", synchronize)
    with ThreadPoolExecutor(max_workers=2) as executor:
        inbox = executor.submit(c.service.process_inbox, ORG)
        by_id = executor.submit(c.service.open_from_handoff, ORG, assistance_id)
        inbox_result = inbox.result(timeout=5)
        by_id_result = by_id.result(timeout=5)
    assert len(inbox_result) == 1
    assert inbox_result[0].proposal_id == by_id_result.proposal_id
    assert inbox_result[0].outcome in {OpenOutcome.CREATED, OpenOutcome.REPLAYED}
    assert by_id_result.outcome in {OpenOutcome.CREATED, OpenOutcome.REPLAYED}
    assert len(c.store.snapshot().proposals) == 1
    assert sum(job.job_type == "sketch_generation"
               for job in c.h.job_store.snapshot().jobs.values()) == 1


def test_r02_lost_create_reply_reuses_semantic_job_on_retry() -> None:
    c = build_sketch_chain_harness()
    assistance_id = c.ready(c.h.command())
    original = c.job_port.create
    lost = True

    def create_then_lose(request: SketchJobCreate) -> JobCreateOutcome:
        nonlocal lost
        result = original(request)
        if lost:
            lost = False
            raise LostReply(result.job_id or "job_fx_lost_reply")
        return result

    _replace_attr(c.job_port, "create", create_then_lose)
    with pytest.raises(LostReply):
        c.service.open_from_handoff(ORG, assistance_id)
    proposal_id = c.proposal_for(assistance_id)
    assert proposal_id is not None
    assert c.proposal(proposal_id).current.pipeline_state is PipelineState.REQUESTED
    _replace_attr(c.job_port, "create", original)
    linked = c.service.schedule(proposal_id)
    assert linked is not None and linked.current.job_id is not None
    assert len(c.h.job_store.snapshot().jobs) == 2  # one Vision job plus one Sketch job
    assert sum(job.job_type == "sketch_generation"
               for job in c.h.job_store.snapshot().jobs.values()) == 1


def test_r03_lost_reply_then_revoked_requester_stales_and_blocks_orphan_start() -> None:
    c = build_sketch_chain_harness()
    assistance_id = c.ready(c.h.command())
    original = c.job_port.create
    lost = True

    def create_then_lose(request: SketchJobCreate) -> JobCreateOutcome:
        nonlocal lost
        result = original(request)
        if lost:
            lost = False
            raise LostReply(result.job_id or "job_fx_orphan")
        return result

    _replace_attr(c.job_port, "create", create_then_lose)
    with pytest.raises(LostReply):
        c.service.open_from_handoff(ORG, assistance_id)
    proposal_id = c.proposal_for(assistance_id)
    assert proposal_id is not None
    _replace_attr(c.job_port, "create", original)
    c.h.job_authorization.revoke(DEVICE_A.principal_id)
    stale = c.service.schedule(proposal_id)
    assert stale is not None and stale.current.pipeline_state is PipelineState.STALE
    assert stale.current.status_reason is StatusReason.SCHEDULE_REFUSED
    sketch_jobs = [job for job in c.h.job_store.snapshot().jobs.values()
                   if job.job_type == "sketch_generation"]
    assert len(sketch_jobs) == 1
    orphan = sketch_jobs[0]
    assert orphan.job_id in stale.current.cleanup_job_ids
    assert orphan.state.value == "queued"
    assert c.h.jobs.dispatch_outbox() == 0
    after_dispatch = c.job_reader.get(orphan.job_id)
    assert after_dispatch is not None
    assert after_dispatch.state == "cancelled"
    assert after_dispatch.failure_code == StatusReason.SCHEDULE_REFUSED.value
    assert c.generator.calls.get(proposal_id, 0) == 0


def test_schedule_link_race_does_not_cas_when_worker_link_was_cancelled() -> None:
    c = build_sketch_chain_harness()
    assistance_id = c.ready(c.h.command(intent="schedule link cancelled race"))
    original_create = c.job_port.create
    raced = False

    def create_and_cancel(request: SketchJobCreate) -> JobCreateOutcome:
        nonlocal raced
        outcome = original_create(request)
        if not raced and outcome.kind is JobCreateKind.CREATED:
            raced = True
            assert c.sketch_jobs.dispatch_outbox() == 1
            envelope = c.h.queue.receive()
            assert envelope is not None
            message = envelope.message
            assert c.sketch_jobs.start_attempt(
                envelope.capability, message.job_id, message.attempt_id).started
            claim = c.service.record_generation(
                message.job_id, message.attempt_id, correlation_id="schedule-race")
            assert claim.success
            proposal_id = c.proposal_for(assistance_id)
            assert proposal_id is not None
            proposal = c.proposal(proposal_id)
            c.service.cancel(CancelCommand(
                TEACHER, proposal_id, "key_fx_schedule_race_cancel", proposal.etag()))
        return outcome

    _replace_attr(c.job_port, "create", create_and_cancel)
    opened = c.service.open_from_handoff(ORG, assistance_id)
    assert opened.outcome is OpenOutcome.CREATED and opened.proposal_id is not None
    proposal = c.proposal(opened.proposal_id)
    assert proposal.current.pipeline_state is PipelineState.CANCELLED
    assert proposal.current.job_id is not None
    job = c.job_reader.get(proposal.current.job_id)
    assert job is not None and job.state == "cancelled"
    assert proposal.record_version == 3


@pytest.mark.parametrize(("race", "reason"), [
    ("consent", StatusReason.CONSENT_REVOKED),
    ("teacher", StatusReason.CANCELLED_BY_TEACHER),
])
def test_p3_lost_link_cleanup_cancels_orphan_with_proposal_reason(
    race: str, reason: StatusReason,
) -> None:
    """P3: an orphan whose link lost to an invalidation carries the proposal's own reason."""

    c = build_sketch_chain_harness()
    assistance_id = c.ready(c.h.command(intent=f"P3 lost link {race}"))
    original = c.job_port.create
    raced = False

    def create_then_invalidate(request: SketchJobCreate) -> JobCreateOutcome:
        nonlocal raced
        outcome = original(request)
        if not raced and outcome.kind is JobCreateKind.CREATED:
            raced = True
            proposal_id = c.proposal_for(assistance_id)
            assert proposal_id is not None
            if race == "consent":
                assert c.h.publish_owner_change(
                    lambda: c.h.owner.update_member(CHILD_A, consent_effective=False))
                assert c.service.apply_owner_notice(OwnerNotice(
                    "notice_fx_p3_consent", ORG, NoticeKind.CONSENT_REVOKED,
                    participant_id=CHILD_A)) == (proposal_id,)
            else:
                proposal = c.proposal(proposal_id)
                c.service.cancel(CancelCommand(TEACHER, proposal_id, "key_fx_p3_cancel",
                                               proposal.etag()))
        return outcome

    _replace_attr(c.job_port, "create", create_then_invalidate)
    opened = c.service.open_from_handoff(ORG, assistance_id)
    assert opened.outcome is OpenOutcome.CREATED and opened.proposal_id is not None
    proposal = c.proposal(opened.proposal_id)
    assert proposal.current.status_reason is reason
    assert proposal.current.job_id is None
    (orphan_id,) = proposal.current.cleanup_job_ids
    orphan = c.job_reader.get(orphan_id)
    assert orphan is not None and orphan.state == "cancelled"
    assert orphan.failure_code == reason.value
    assert c.h.jobs.dispatch_outbox() == 0
    assert c.router.run_next() is None
    assert c.generator.calls.get(opened.proposal_id, 0) == 0
    assert c.provider.runs == 0


def test_p3_lost_reply_schedule_refusal_cleanup_keeps_schedule_refused() -> None:
    """P3 fallback: a refused re-create with a found orphan requests SCHEDULE_REFUSED cleanup."""

    c = build_sketch_chain_harness()
    assistance_id = c.ready(c.h.command(intent="P3 schedule refused"))
    original = c.job_port.create
    lost = True

    def create_then_lose(request: SketchJobCreate) -> JobCreateOutcome:
        nonlocal lost
        result = original(request)
        if lost:
            lost = False
            raise LostReply(result.job_id or "job_fx_orphan")
        return result

    _replace_attr(c.job_port, "create", create_then_lose)
    with pytest.raises(LostReply):
        c.service.open_from_handoff(ORG, assistance_id)
    proposal_id = c.proposal_for(assistance_id)
    assert proposal_id is not None
    _replace_attr(c.job_port, "create", original)
    cancel = c.job_port.cancel
    requested: list[str] = []

    def spy_cancel(*args: Any) -> str:
        requested.append(str(args[3]))
        return cancel(*args)

    _replace_attr(c.job_port, "cancel", spy_cancel)
    c.h.job_authorization.revoke(DEVICE_A.principal_id)
    stale = c.service.schedule(proposal_id)
    assert stale is not None and stale.current.status_reason is StatusReason.SCHEDULE_REFUSED
    (orphan_id,) = stale.current.cleanup_job_ids
    assert requested == [StatusReason.SCHEDULE_REFUSED.value]
    assert c.h.jobs.dispatch_outbox() == 0
    orphan = c.job_reader.get(orphan_id)
    assert orphan is not None and orphan.state == "cancelled"
    assert orphan.failure_code == StatusReason.SCHEDULE_REFUSED.value
    assert c.generator.calls.get(proposal_id, 0) == 0


def test_r04_cancel_after_job_create_before_link_cleans_orphan_job() -> None:
    c = build_sketch_chain_harness()
    assistance_id = c.ready(c.h.command())
    original = c.job_port.create
    cancelled = False

    def create_then_cancel(request: object) -> object:
        nonlocal cancelled
        result = original(request)  # type: ignore[arg-type]
        if not cancelled:
            cancelled = True
            proposal_id = c.proposal_for(assistance_id)
            assert proposal_id is not None
            proposal = c.proposal(proposal_id)
            c.service.cancel(CancelCommand(TEACHER, proposal_id, "key_fx_r04_cancel",
                                           proposal.etag()))
        return result

    _replace_attr(c.job_port, "create", create_then_cancel)
    opened = c.service.open_from_handoff(ORG, assistance_id)
    assert opened.proposal_id is not None
    proposal = c.proposal(opened.proposal_id)
    assert cancelled and proposal.current.pipeline_state is PipelineState.CANCELLED
    assert proposal.current.cleanup_job_ids
    job = c.job_reader.get(proposal.current.cleanup_job_ids[0])
    assert job is not None and job.state == "cancelled"
    assert len([j for j in c.h.job_store.snapshot().jobs.values()
                if j.job_type == "sketch_generation"]) == 1


def test_r04_cancel_before_schedule_never_creates_job() -> None:
    c = build_sketch_chain_harness()
    assistance_id = c.ready(c.h.command())
    original = c.job_port.create

    def defer_creation(request: object) -> object:
        return JobCreateOutcome(JobCreateKind.RETRY, code="TEMPORARY")

    _replace_attr(c.job_port, "create", defer_creation)
    proposal_id = c.service.open_from_handoff(ORG, assistance_id).proposal_id
    assert proposal_id is not None
    proposal = c.proposal(proposal_id)
    c.service.cancel(CancelCommand(TEACHER, proposal_id, "key_fx_r04_before",
                                   proposal.etag()))
    _replace_attr(c.job_port, "create", original)
    c.service.schedule(proposal_id)
    assert c.proposal(proposal_id).current.pipeline_state is PipelineState.CANCELLED
    assert not any(j.job_type == "sketch_generation"
                   for j in c.h.job_store.snapshot().jobs.values())


def test_r05_cancel_between_start_and_provider_prevents_generation() -> None:
    c = build_sketch_chain_harness()
    proposal_id = _open(c)
    original = c.provider.run

    def cancel_then_record(message: object) -> object:
        proposal = c.proposal(proposal_id)
        c.service.cancel(CancelCommand(TEACHER, proposal_id, "key_fx_r05_cancel",
                                       proposal.etag()))
        return original(message)  # type: ignore[arg-type]

    _replace_attr(c.provider, "run", cancel_then_record)
    routed = c.run_sketch(proposal_id, reconcile=False)
    assert routed is not None and routed.started
    assert c.proposal(proposal_id).current.pipeline_state is PipelineState.CANCELLED
    assert c.generator.calls.get(proposal_id, 0) == 0


def test_r06_foundation_completion_defers_cancel_until_after_commit() -> None:
    c = build_sketch_chain_harness()
    proposal_id = _open(c)
    c.router.crash_after_provider = True
    interrupted = c.run_sketch(proposal_id, reconcile=False)
    assert interrupted is not None and interrupted.reason == "CRASHED_BEFORE_COMPLETION"
    envelope = c.router.last_sketch
    assert envelope is not None and isinstance(interrupted.outcome, CompletionClaim)
    proposal = c.proposal(proposal_id)

    def after_hold() -> None:
        with pytest.raises(CoordinationError), c.service._d.repository.transaction() as tx:
            tx.get(proposal_id)

        def cancel_after_completion() -> None:
            completed = c.job_reader.get(envelope.message.job_id)
            assert completed is not None and completed.state == "succeeded"
            publication_order.append("completion_committed")
            c.service.cancel(CancelCommand(
                TEACHER, proposal_id, "key_fx_r06_cancel", proposal.etag()))
            publication_order.append("cancel_committed")

        queued = c.h.coordinator.request_publication(cancel_after_completion)
        assert queued is False
        publication_order.append("cancel_deferred")

    publication_order: list[str] = []
    c.h.fences.after_successful_hold = after_hold
    receipt = c.sketch_jobs.accept_completion(envelope.capability, interrupted.outcome)
    assert receipt.disposition.value == "accepted"
    completed = c.job_reader.get(envelope.message.job_id)
    assert completed is not None and completed.state == "succeeded"
    cancelled = c.service.reconcile(proposal_id)
    assert cancelled is not None and cancelled.current.pipeline_state is PipelineState.CANCELLED
    assert cancelled.current.promoted is None
    publication_order.append("cancel_reconciled")
    assert c.service.deliver_cleanup() >= 1
    publication_order.append("quarantine_delivered")
    assert publication_order == ["cancel_deferred", "completion_committed",
                                 "cancel_committed", "cancel_reconciled",
                                 "quarantine_delivered"]
    staged = next(iter(c.store.snapshot().staged.values()))
    assert all(ref in c.raw_artifacts.quarantined for ref in staged.refs())
    assert c.audit_violations() == []


@pytest.mark.parametrize("promote_first", [True, False])
def test_r07_reconcile_cancel_order_has_one_valid_winner(promote_first: bool) -> None:
    c = build_sketch_chain_harness()
    proposal_id = _open(c)
    if promote_first:
        promoted = c.run_sketch(proposal_id)
        assert promoted is not None and promoted.started
        with pytest.raises(SketchError, match="INVALID_STATE"):
            c.service.cancel(CancelCommand(TEACHER, proposal_id, "key_fx_r07_late",
                                           c.proposal(proposal_id).etag()))
        assert c.proposal(proposal_id).current.pipeline_state is (
            PipelineState.PENDING_TEACHER_REVIEW)
    else:
        c.service.cancel(CancelCommand(TEACHER, proposal_id, "key_fx_r07_first",
                                       c.proposal(proposal_id).etag()))
        c.service.reconcile(proposal_id)
        assert c.proposal(proposal_id).current.pipeline_state is PipelineState.CANCELLED
        assert c.generator.calls.get(proposal_id, 0) == 0


def test_r08_timeout_retry_supersedes_staged_attempt_and_promotes_new_attempt() -> None:
    c = build_sketch_chain_harness()
    proposal_id = _open(c)
    c.router.crash_after_provider = True
    interrupted = c.run_sketch(proposal_id, reconcile=False)
    assert interrupted is not None and interrupted.reason == "CRASHED_BEFORE_COMPLETION"
    first = c.router.last_sketch
    first_claim = interrupted.outcome
    assert first is not None and first_claim is not None
    first_key = f"{first.message.job_id}:{first.message.attempt_id}"
    first_stage = c.store.snapshot().staged[first_key]
    c.h.clock.advance(milliseconds=FIXTURE_RETRY_POLICY.attempt_timeout_ms)
    assert c.sketch_jobs.expire_overdue_attempts() == (first.message.job_id,)
    backoff = FIXTURE_RETRY_POLICY.backoff_after(1)
    c.h.clock.advance(milliseconds=int(backoff.total_seconds() * 1000))
    assert c.sketch_jobs.run_due_retries() == (first.message.job_id,)
    assert c.sketch_jobs.dispatch_outbox() == 1
    second = c.router.run_next()
    assert second is not None and second.started
    promoted = c.service.reconcile(proposal_id)
    assert promoted is not None and promoted.current.pipeline_state is (
        PipelineState.PENDING_TEACHER_REVIEW)
    assert promoted.current.promoted is not None
    assert promoted.current.promoted.attempt_id != first.message.attempt_id
    assert c.store.snapshot().staged[first_key].status.value == "superseded"
    assert c.service.deliver_cleanup() >= 1
    assert all(ref in c.raw_artifacts.quarantined for ref in first_stage.refs())
    assert c.audit_violations() == []


def test_n13_late_success_from_expired_attempt_is_quarantined_not_promoted() -> None:
    c = build_sketch_chain_harness()
    proposal_id = _open(c)
    assert c.sketch_jobs.dispatch_outbox() == 1
    first = c.h.queue.receive()
    assert first is not None
    assert c.sketch_jobs.start_attempt(first.capability, first.message.job_id,
                                       first.message.attempt_id).started
    late_claim = c.provider.run(first.message)
    first_key = f"{first.message.job_id}:{first.message.attempt_id}"
    first_stage = c.store.snapshot().staged[first_key]

    c.h.clock.advance(milliseconds=FIXTURE_RETRY_POLICY.attempt_timeout_ms)
    assert c.sketch_jobs.expire_overdue_attempts() == (first.message.job_id,)
    backoff = FIXTURE_RETRY_POLICY.backoff_after(1)
    c.h.clock.advance(milliseconds=int(backoff.total_seconds() * 1000))
    assert c.sketch_jobs.run_due_retries() == (first.message.job_id,)
    assert c.sketch_jobs.dispatch_outbox() == 1
    second = c.h.queue.receive()
    assert second is not None and second.message.attempt_id != first.message.attempt_id
    assert c.sketch_jobs.start_attempt(second.capability, second.message.job_id,
                                       second.message.attempt_id).started

    late_receipt = c.sketch_jobs.accept_completion(first.capability, late_claim)
    assert str(late_receipt.disposition) == "stale"
    live = c.job_reader.get(first.message.job_id)
    assert live is not None and live.active_attempt_id == second.message.attempt_id
    assert all(ref in c.raw_artifacts.quarantined for ref in first_stage.refs())

    current_claim = c.provider.run(second.message)
    accepted = c.sketch_jobs.accept_completion(second.capability, current_claim)
    assert str(accepted.disposition) == "accepted"
    promoted = c.service.reconcile(proposal_id)
    assert promoted is not None
    assert promoted.current.pipeline_state is PipelineState.PENDING_TEACHER_REVIEW
    assert promoted.current.promoted is not None
    assert promoted.current.promoted.attempt_id == second.message.attempt_id
    assert promoted.current.promoted.attempt_id != first.message.attempt_id


def test_r09_completion_before_c8_reconciles_exactly_once() -> None:
    c = build_sketch_chain_harness()
    proposal_id = _open(c)
    _, claim = _stage_only(c, proposal_id)
    first = c.service.reconcile(proposal_id)
    second = c.service.reconcile(proposal_id)
    assert first is not None and second is not None
    assert first.current.pipeline_state is second.current.pipeline_state is (
        PipelineState.PENDING_TEACHER_REVIEW)
    assert first.current.promoted is not None
    assert len([e for e in c.store.snapshot().events
                if e.event_type == "sketch.proposal_ready"]) == 1
    promoted = c.proposal(proposal_id).current.promoted
    assert promoted is not None and promoted.attempt_id == claim.attempt_id


def test_r10_duplicate_sketch_delivery_never_calls_provider_twice() -> None:
    c = build_sketch_chain_harness()
    proposal_id = _open(c)
    assert c.sketch_jobs.dispatch_outbox() == 1
    envelope = c.h.queue.receive()
    assert envelope is not None
    started = c.sketch_jobs.start_attempt(envelope.capability, envelope.message.job_id,
                                          envelope.message.attempt_id)
    assert started.started
    c.h.queue.redeliver(envelope)
    refused = c.router.run_next()
    assert refused is not None and not refused.started
    assert refused.reason == "DUPLICATE_DELIVERY"
    assert c.generator.calls.get(proposal_id, 0) == 0
    claim = c.provider.run(envelope.message)
    receipt = c.sketch_jobs.accept_completion(envelope.capability, claim)
    assert receipt.disposition.value == "accepted"
    reconciled = c.service.reconcile(proposal_id)
    assert reconciled is not None
    assert reconciled.current.pipeline_state is PipelineState.PENDING_TEACHER_REVIEW
    assert c.generator.calls[proposal_id] == 1


def test_r11_c1_commit_failure_leaves_no_partial_proposal_and_retries() -> None:
    c = build_sketch_chain_harness()
    assistance_id = c.ready(c.h.command())
    token = c.decision.token
    fired = False

    def fail_insert_commit(*args: object, **kwargs: object) -> object:
        nonlocal fired
        result = token(*args, **kwargs)  # type: ignore[arg-type]
        if not fired:
            fired = True

            def fail() -> None:
                c.store.fail_next_commit = True

            c.store.before_commit = fail
        return result

    _replace_attr(c.decision, "token", fail_insert_commit)
    with pytest.raises(RuntimeError, match="injected sketch commit failure"):
        c.service.open_from_handoff(ORG, assistance_id)
    assert c.proposal_for(assistance_id) is None
    assert c.store.snapshot().events == []
    _replace_attr(c.decision, "token", token)
    result = c.service.open_from_handoff(ORG, assistance_id)
    assert result.outcome is OpenOutcome.CREATED and result.proposal_id is not None
    assert c.proposal(result.proposal_id).current.job_id is not None


def test_r11_link_commit_failure_leaves_request_unlinked_and_replay_links_once() -> None:
    c = build_sketch_chain_harness()
    assistance_id = c.ready(c.h.command(intent="R11 link failure"))
    create = c.job_port.create

    def create_then_fail_link(request: SketchJobCreate) -> JobCreateOutcome:
        outcome = create(request)
        if outcome.kind is JobCreateKind.CREATED:
            c.store.fail_next_commit = True
        return outcome

    _replace_attr(c.job_port, "create", create_then_fail_link)
    with pytest.raises(RuntimeError, match="injected sketch commit failure"):
        c.service.open_from_handoff(ORG, assistance_id)
    proposal_id = c.proposal_for(assistance_id)
    assert proposal_id is not None
    unlinked = c.proposal(proposal_id)
    assert unlinked.current.pipeline_state is PipelineState.REQUESTED
    assert unlinked.current.job_id is None
    assert not any(event.event_type == "sketch.scheduled"
                   for event in c.store.snapshot().events)
    assert c.store.snapshot().staged == {}

    _replace_attr(c.job_port, "create", create)
    replay = c.service.open_from_handoff(ORG, assistance_id)
    assert replay.outcome is OpenOutcome.REPLAYED
    linked = c.proposal(proposal_id)
    assert linked.current.job_id is not None
    assert sum(job.job_type == "sketch_generation"
               for job in c.h.job_store.snapshot().jobs.values()) == 1
    assert sum(event.event_type == "sketch.scheduled"
               for event in c.store.snapshot().events) == 1


def test_r11_stage_commit_failure_leaves_no_staged_row_and_retries() -> None:
    c = build_sketch_chain_harness()
    proposal_id = c.open_ready(c.h.command(intent="R11 stage failure"))
    assert c.sketch_jobs.dispatch_outbox() == 1
    envelope = c.h.queue.receive()
    assert envelope is not None
    message = envelope.message
    assert c.sketch_jobs.start_attempt(
        envelope.capability, message.job_id, message.attempt_id).started
    stage = c.admission.stage

    def stage_then_fail_result_commit(*args: object, **kwargs: object) -> object:
        result = stage(*args, **kwargs)  # type: ignore[arg-type]
        if args[3] == "result":
            c.store.fail_next_commit = True
        return result

    _replace_attr(c.admission, "stage", stage_then_fail_result_commit)
    with pytest.raises(RuntimeError, match="injected sketch commit failure"):
        c.provider.run(message)
    assert c.store.snapshot().staged == {}
    assert c.proposal(proposal_id).current.pipeline_state is PipelineState.ANALYZING

    _replace_attr(c.admission, "stage", stage)
    claim = c.provider.run(message)
    assert claim.kind is OutcomeKind.SUCCESS
    assert c.sketch_jobs.accept_completion(envelope.capability, claim).disposition.value == (
        "accepted")
    promoted = c.service.reconcile(proposal_id)
    assert promoted is not None
    assert promoted.current.pipeline_state is PipelineState.PENDING_TEACHER_REVIEW
    assert len(c.store.snapshot().staged) == 1


def test_r11_cancel_commit_failure_leaves_no_receipt_or_event_and_retries() -> None:
    c = build_sketch_chain_harness()
    proposal_id = c.open_ready(c.h.command(intent="R11 cancel failure"))
    before = c.proposal(proposal_id)
    command = CancelCommand(TEACHER, proposal_id, "key_fx_r11_cancel", before.etag())
    snapshot = c.store.snapshot()
    c.store.fail_next_commit = True
    with pytest.raises(RuntimeError, match="injected sketch commit failure"):
        c.service.cancel(command)
    after_failure = c.store.snapshot()
    assert after_failure.proposals[proposal_id] == before
    assert after_failure.receipts == snapshot.receipts
    assert after_failure.events == snapshot.events

    result = c.service.cancel(command)
    assert result.outcome == "cancelled"
    cancelled = c.proposal(proposal_id)
    assert cancelled.current.pipeline_state is PipelineState.CANCELLED
    assert len(c.store.snapshot().receipts) == len(snapshot.receipts) + 1
    assert sum(event.event_type == "sketch.cancelled"
               for event in c.store.snapshot().events) == 1


def test_r11_owner_notice_commit_failure_leaves_no_partial_state_and_retries() -> None:
    c = build_sketch_chain_harness()
    proposal_id = c.open_ready(c.h.command(intent="R11 notice failure"))
    before = c.proposal(proposal_id)
    job_id = before.current.job_id
    assert job_id is not None
    notice = OwnerNotice("notice_fx_r11", ORG, NoticeKind.CONSENT_REVOKED,
                         participant_id=CHILD_A)
    snapshot = c.store.snapshot()
    c.store.fail_next_commit = True
    with pytest.raises(RuntimeError, match="injected sketch commit failure"):
        c.service.apply_owner_notice(notice)
    after_failure = c.store.snapshot()
    assert after_failure.proposals[proposal_id] == before
    assert after_failure.notices == snapshot.notices
    assert after_failure.events == snapshot.events
    assert c.job_reader.get(job_id).state == "queued"  # type: ignore[union-attr]

    assert c.service.apply_owner_notice(notice) == (proposal_id,)
    stale = c.proposal(proposal_id)
    assert stale.current.pipeline_state is PipelineState.STALE
    assert stale.current.status_reason is StatusReason.CONSENT_REVOKED
    job = c.job_reader.get(job_id)
    assert job is not None and job.state == "cancelled"
    assert job.failure_code == StatusReason.CONSENT_REVOKED.value


def test_r27_retry_ref_set_change_restarts_with_new_attempt_token() -> None:
    c = build_sketch_chain_harness()
    proposal_id = _open(c)
    c.router.crash_after_provider = True
    interrupted = c.run_sketch(proposal_id, reconcile=False)
    assert interrupted is not None and interrupted.reason == "CRASHED_BEFORE_COMPLETION"
    first = c.router.last_sketch
    assert first is not None
    first_key = f"{first.message.job_id}:{first.message.attempt_id}"
    first_stage = c.store.snapshot().staged[first_key]
    c.h.clock.advance(milliseconds=FIXTURE_RETRY_POLICY.attempt_timeout_ms)
    assert c.sketch_jobs.expire_overdue_attempts() == (first.message.job_id,)
    backoff = FIXTURE_RETRY_POLICY.backoff_after(1)
    c.h.clock.advance(milliseconds=int(backoff.total_seconds() * 1000))
    assert c.sketch_jobs.run_due_retries() == (first.message.job_id,)
    assert c.sketch_jobs.dispatch_outbox() == 1
    second = c.router.run_next()
    assert second is not None and second.started
    actual_get = c.job_reader.get
    live = actual_get(first.message.job_id)
    assert live is not None and live.state == "succeeded"
    first_snapshot = replace(
        live, active_attempt_id=first.message.attempt_id, attempt_number=1,
        result_refs=first_stage.output_pairs(), state="succeeded", failure_code=None)
    reads = 0

    def lagging_once(job_id: str) -> SketchJobEvidence | None:
        nonlocal reads
        reads += 1
        return first_snapshot if reads == 1 else actual_get(job_id)

    _replace_attr(c.job_reader, "get", lagging_once)
    token = c.decision.token
    bumped = False

    def invalidate_old_ref_set(*args: object, **kwargs: object) -> object:
        nonlocal bumped
        result = token(*args, **kwargs)  # type: ignore[arg-type]
        if not bumped:
            bumped = True
            c.owner_quarantine(first_stage.refs(), "R27_OLD_ATTEMPT")
        return result

    _replace_attr(c.decision, "token", invalidate_old_ref_set)
    promoted = c.service.reconcile(proposal_id)
    assert promoted is not None
    assert promoted.current.pipeline_state is PipelineState.PENDING_TEACHER_REVIEW
    assert promoted.current.promoted is not None
    assert promoted.current.promoted.attempt_id == second.attempt_id
    assert reads == 2
    assert promoted.current.promoted.attempt_id != first.message.attempt_id
    assert sum(e.event_type == "sketch.proposal_ready"
               for e in c.store.snapshot().events) == 1


def test_r25_r31_publication_waits_for_c8_then_withholds_and_revalidates() -> None:
    c = build_sketch_chain_harness()
    proposal_id = _open(c)
    _, claim = _stage_only(c, proposal_id)
    proposal = c.proposal(proposal_id)
    staged = c.store.snapshot().staged[f"{proposal.current.job_id}:{claim.attempt_id}"]
    ref = staged.result_document.artifact_ref
    job_id = staged.job_id
    intent = QuarantineIntent("evt_fx_r31", ORG, job_id, claim.attempt_id,
                              (ref,), "R31_THREAD")
    c.h.jobs.deliver_side_effects()  # drain the completion's unrelated audit intent first
    with c.h.job_repository.transaction() as tx:
        tx.add_quarantine_intent(intent)
    token = c.decision.token
    sink_entered, release_sink, thread_done = Event(), Event(), Event()
    marked: list[int] = []

    apply_side_effect = c.h.jobs._apply_side_effect

    def pause_after_claim(effect: object) -> None:
        sink_entered.set()
        assert release_sink.wait(2)
        apply_side_effect(effect)  # type: ignore[arg-type]

    _replace_attr(c.h.jobs, "_apply_side_effect", pause_after_claim)

    def on_commit_boundary() -> None:
        assert not thread_done.is_set()
        assert ref not in c.raw_artifacts.quarantined
        release_sink.set()

    def capture_then_arm(*args: object, **kwargs: object) -> object:
        result = token(*args, **kwargs)  # type: ignore[arg-type]
        c.store.before_commit = on_commit_boundary
        return result

    _replace_attr(c.decision, "token", capture_then_arm)

    def deliver_after_claim() -> None:
        marked.append(c.h.jobs.deliver_side_effects())
        thread_done.set()

    thread = Thread(target=deliver_after_claim)
    thread.start()
    assert sink_entered.wait(2)
    promoted = c.service.reconcile(proposal_id)
    assert promoted is not None
    assert promoted.current.pipeline_state is PipelineState.PENDING_TEACHER_REVIEW
    thread.join(timeout=2)
    assert not thread.is_alive()
    assert thread_done.is_set() and marked == [1]
    assert ref in c.raw_artifacts.quarantined
    snapshot = c.h.job_store.snapshot()
    assert intent.event_id in snapshot.side_effects_delivered
    record = c.service.get_record(TEACHER, proposal_id)
    assert record["text_or_question"] is None and record["content_withheld_reason"] == (
        "ARTIFACT_QUARANTINED")
    _replace_attr(c.decision, "token", token)
    c.store.before_commit = None
    stale = c.service.revalidate(proposal_id)
    assert stale is not None and stale.current.pipeline_state is PipelineState.STALE
    assert stale.current.status_reason is StatusReason.ARTIFACT_QUARANTINED


def test_r26_deferred_quarantine_runs_after_failed_c8_commit() -> None:
    c = build_sketch_chain_harness()
    proposal_id = _open(c)
    _, claim = _stage_only(c, proposal_id)
    proposal = c.proposal(proposal_id)
    staged = c.store.snapshot().staged[f"{proposal.current.job_id}:{claim.attempt_id}"]
    ref = staged.result_document.artifact_ref
    token = c.decision.token

    def deferred_at_commit() -> None:
        assert c.owner_quarantine((ref,), "R26_DEFERRED") is False

    def capture_then_arm(*args: object, **kwargs: object) -> object:
        result = token(*args, **kwargs)  # type: ignore[arg-type]
        c.store.fail_next_commit = True
        c.store.before_commit = deferred_at_commit
        return result

    _replace_attr(c.decision, "token", capture_then_arm)
    with pytest.raises(RuntimeError, match="injected sketch commit failure"):
        c.service.reconcile(proposal_id)
    assert c.raw_artifacts.describe(ref).quarantine_reason == "R26_DEFERRED"  # type: ignore[union-attr]
    assert c.h.coordinator.deferred_failures == []
    assert c.proposal(proposal_id).current.pipeline_state is PipelineState.ANALYZING
    _replace_attr(c.decision, "token", token)
    stale = c.service.reconcile(proposal_id)
    assert stale is not None and stale.current.status_reason is StatusReason.ARTIFACT_QUARANTINED


def test_r30_failed_sink_redelivers_sketch_quarantine_through_a1_port() -> None:
    c = build_sketch_chain_harness()
    c.generator.script = lambda request: default_outcome(request, unsafe=True)
    proposal_id = _open(c)
    c.artifact_port.fail_next_quarantine = True
    result = c.run_sketch(proposal_id, reconcile=False)
    assert result is not None and result.started
    blocked = c.service.reconcile(proposal_id)
    assert blocked is not None and blocked.current.pipeline_state is PipelineState.BLOCKED_UNSAFE
    assert blocked.current.moderation_state.value == "blocked"
    teacher_record = c.service.get_record(TEACHER, proposal_id)
    assert teacher_record["status_reason"] == StatusReason.UNSAFE_CONTENT.value
    assert teacher_record["text_or_question"] is None
    assert any(event.event_type == "sketch.blocked_unsafe"
               for event in c.store.snapshot().events)
    device = c.service.device_view(DEVICE_A, blocked.binding.assistance_id)
    assert device["status"] == "unavailable"
    job = c.job_reader.get(c.proposal(proposal_id).current.job_id or "")
    assert job is not None
    pending = [effect for effect in c.h.job_store.snapshot().quarantine_intents.values()]
    assert pending and pending[0].artifact_refs
    refs = pending[0].artifact_refs
    assert c.h.jobs.deliver_side_effects() >= 1
    assert all(ref in c.raw_artifacts.quarantined for ref in refs)
    assert c.artifact_port.audit[-len(refs):][0].caller == "h.jobs"
    assert all(entry.bumped for entry in c.artifact_port.audit[-len(refs):])
    assert c.audit_violations() == []
    snapshot = c.h.job_store.snapshot()
    assert set(snapshot.side_effect_order) <= set(snapshot.side_effects_delivered)


def test_r32_same_event_redelivery_has_one_fence_bump() -> None:
    c = build_sketch_chain_harness()
    output = c.raw_artifacts.put(ORG, b"synthetic", job_id="job_fx_dedup",
                                 attempt_id="attempt_fx_dedup")
    intent = QuarantineIntent("evt_fx_dedup", ORG, "job_fx_dedup", "attempt_fx_dedup",
                              (output.artifact_ref,), "R32")
    with c.h.job_repository.transaction() as tx:
        tx.add_quarantine_intent(intent)
    lease = c.h.jobs._d.dispatch_policy.lease
    with c.h.job_repository.transaction() as tx:
        first_claim, = tx.claim_side_effects("r32-stale", c.h.clock.now(), lease, 1)
    c.h.jobs._apply_side_effect(first_claim.effect)

    c.h.clock.advance(milliseconds=int(lease.total_seconds() * 1000) + 1)
    with c.h.job_repository.transaction() as tx:
        retry_claim, = tx.claim_side_effects("r32-retry", c.h.clock.now(), lease, 1)
        assert retry_claim.lease.generation > first_claim.lease.generation
        assert not tx.mark_side_effect(first_claim.lease, c.h.clock.now())
    c.h.clock.advance(milliseconds=int(lease.total_seconds() * 1000) + 1)
    assert c.sketch_jobs.deliver_side_effects() == 1

    cleanup = CleanupIntent("evt_fx_dedup", ORG, "job_fx_dedup", "attempt_fx_dedup",
                            (output.artifact_ref,), "R32_C9")
    with c.store.transaction() as tx:
        tx.add_cleanup(cleanup)
    assert c.service.deliver_cleanup() == 1
    entries = [entry for entry in c.artifact_port.audit if entry.ref == output.artifact_ref]
    assert [entry.bumped for entry in entries] == [True, False, False]
    assert c.h.fences.epochs[artifact_fence_scope(output.artifact_ref)] == 1
    assert intent.event_id in c.h.job_store.snapshot().side_effects_delivered
    assert c.audit_violations() == []


@pytest.mark.parametrize("first_drainer", ["h.jobs", "sketch_jobs"])
def test_r33_both_job_service_instances_drain_shared_outbox(
    first_drainer: str,
) -> None:
    c = build_sketch_chain_harness()
    refs = tuple(c.raw_artifacts.put(ORG, b"outbox", job_id=f"job_fx_{i}",
                                     attempt_id=f"attempt_fx_{i}").artifact_ref
                 for i in (1, 2))
    with c.h.job_repository.transaction() as tx:
        tx.add_quarantine_intent(QuarantineIntent(
            "evt_fx_1", ORG, "job_fx_1", "attempt_fx_1", (refs[0],), "VISION"))
    first = c.h.jobs if first_drainer == "h.jobs" else c.sketch_jobs
    second = c.sketch_jobs if first_drainer == "h.jobs" else c.h.jobs
    assert first.deliver_side_effects() == 1
    with c.h.job_repository.transaction() as tx:
        tx.add_quarantine_intent(QuarantineIntent(
            "evt_fx_2", ORG, "job_fx_2", "attempt_fx_2", (refs[1],), "SKETCH"))
    assert second.deliver_side_effects() == 1
    assert second.deliver_side_effects() == 0
    assert all(ref in c.raw_artifacts.quarantined for ref in refs)
    assert len([entry for entry in c.artifact_port.audit if entry.bumped]) == 2
    assert c.audit_violations() == []


def _pending_quarantine(c: SketchChainHarness) -> dict[str, QuarantineIntent]:
    snapshot = c.h.job_store.snapshot()
    return {event_id: intent for event_id, intent in snapshot.quarantine_intents.items()
            if event_id not in snapshot.side_effects_delivered}


def _unsafe_sketch_with_failed_sink(c: SketchChainHarness, *, intent: str) -> tuple[str, str]:
    """Real Sketch UNSAFE completion whose immediate sink fails: its quarantine intent stays
    pending in the shared outbox (completion-generated, not synthetic)."""

    c.generator.script = lambda request: default_outcome(request, unsafe=True)
    proposal_id = _open(c, intent=intent)
    before = set(_pending_quarantine(c))
    c.artifact_port.fail_next_quarantine = True
    routed = c.run_sketch(proposal_id, reconcile=False)
    assert routed is not None and routed.started
    (event_id,) = set(_pending_quarantine(c)) - before
    c.generator.script = None
    return proposal_id, event_id


def _unsafe_vision_with_failed_sink(c: SketchChainHarness) -> str:
    """Real Vision UNSAFE completion through the router with a failing immediate sink."""

    h = c.h

    def finish(job_id: str, attempt_id: str) -> object:
        job = h.job_store.snapshot().jobs[job_id]
        ref = job.active_attempt.request_ref
        output = h.artifacts.put(ORG, b"synthetic unsafe Vision output",
                                 job_id=job_id, attempt_id=attempt_id)
        envelope = h.last_envelope
        assert envelope is not None
        return h.jobs.accept_completion(envelope.capability, CompletionClaim(
            job_id, attempt_id, ref.request_revision, ref.input_hash, ref.context_revision,
            OutcomeKind.SUCCESS, outputs=(output,), moderation=Moderation.UNSAFE))

    original = h.finish_vision
    _replace_attr(h, "finish_vision", finish)
    before = set(_pending_quarantine(c))
    h.submit(h.command(intent="R33 real unsafe Vision"))
    h.dispatch()
    c.artifact_port.fail_next_quarantine = True
    routed = c.router.run_next()
    _replace_attr(h, "finish_vision", original)
    assert routed is not None and routed.job_type == "vision_analysis" and routed.started
    (event_id,) = set(_pending_quarantine(c)) - before
    return event_id


def test_r31_real_completion_intent_sink_waits_for_c8_commit() -> None:
    """R31 with a completion-generated intent: thread B claims the UNSAFE Sketch quarantine and
    reaches the coordinated publication while thread A deliberately holds the C8 unit open; no
    artifact mutation, fence bump or delivery mark happens in that window, and the raw mutation
    observes the already-committed C8 state."""

    c = build_sketch_chain_harness()
    proposal_id, event_id = _unsafe_sketch_with_failed_sink(c, intent="R31 real intent")
    refs = _pending_quarantine(c)[event_id].artifact_refs
    assert refs and not any(ref in c.raw_artifacts.quarantined for ref in refs)
    epochs_before = {ref: c.h.fences.epochs[artifact_fence_scope(ref)] for ref in refs}
    order: list[str] = []
    sink_entered, release_sink, publication_attempted = Event(), Event(), Event()
    workers: list[Thread] = []
    apply_side_effect = c.h.jobs._apply_side_effect

    def pause_quarantine_after_claim(effect: object) -> None:
        if isinstance(effect, QuarantineIntent) and effect.event_id == event_id:
            sink_entered.set()
            assert release_sink.wait(2)
        apply_side_effect(effect)  # type: ignore[arg-type]

    _replace_attr(c.h.jobs, "_apply_side_effect", pause_quarantine_after_claim)

    request_publication = c.h.coordinator.request_publication

    def observe_worker_publication(publication: Any) -> bool:
        if current_thread() in workers and not publication_attempted.is_set():
            order.append("publication_attempted")
            publication_attempted.set()
        return request_publication(publication)

    _replace_attr(c.h.coordinator, "request_publication", observe_worker_publication)

    raw_owner_quarantine = c.raw_artifacts.owner_quarantine
    committed_at_mutation: list[PipelineState] = []

    def observe_raw_mutation(artifact_refs: tuple[str, ...], reason_code: str) -> None:
        committed = c.store.peek(proposal_id)
        assert committed is not None
        committed_at_mutation.append(committed.current.pipeline_state)
        order.append("raw_quarantine")
        raw_owner_quarantine(artifact_refs, reason_code)

    _replace_attr(c.raw_artifacts, "owner_quarantine", observe_raw_mutation)
    token = c.decision.token

    def hold_c8_until_worker_publishes() -> None:
        order.append("c8_holding")
        release_sink.set()
        assert publication_attempted.wait(2), "the sink never reached the coordinated publication"
        # The worker now waits on the coordinator lock that this C8 unit holds.
        assert not any(ref in c.raw_artifacts.quarantined for ref in refs)
        assert {ref: c.h.fences.epochs[artifact_fence_scope(ref)] for ref in refs} == (
            epochs_before)
        assert event_id not in c.h.job_store.snapshot().side_effects_delivered
        uncommitted = c.store.peek(proposal_id)
        assert uncommitted is not None
        assert uncommitted.current.pipeline_state is PipelineState.ANALYZING
        order.append("c8_commit")

    def capture_then_arm(*args: object, **kwargs: object) -> object:
        result = token(*args, **kwargs)  # type: ignore[arg-type]
        c.store.before_commit = hold_c8_until_worker_publishes
        return result

    _replace_attr(c.decision, "token", capture_then_arm)
    marked: list[int] = []

    def deliver() -> None:
        marked.append(c.h.jobs.deliver_side_effects())
        order.append("drain_returned")

    thread = Thread(target=deliver)
    workers.append(thread)
    thread.start()
    assert sink_entered.wait(2)
    blocked = c.service.reconcile(proposal_id)
    thread.join(timeout=3)
    assert not thread.is_alive()
    _replace_attr(c.decision, "token", token)
    c.store.before_commit = None
    assert blocked is not None and blocked.current.pipeline_state is PipelineState.BLOCKED_UNSAFE
    assert order == ["c8_holding", "publication_attempted", "c8_commit", "raw_quarantine",
                     "drain_returned"]
    assert committed_at_mutation == [PipelineState.BLOCKED_UNSAFE]
    assert all(ref in c.raw_artifacts.quarantined for ref in refs)
    assert all(c.h.fences.epochs[artifact_fence_scope(ref)] == epochs_before[ref] + 1
               for ref in refs)
    assert event_id in c.h.job_store.snapshot().side_effects_delivered
    entries = [e for e in c.artifact_port.audit if e.event_id == event_id]
    assert [(e.caller, e.bumped) for e in entries] == [("h.jobs", True)] * len(refs)
    assert not any(e.event_type == "sketch.proposal_ready" for e in c.store.snapshot().events)


@pytest.mark.parametrize("first_drainer", ["h.jobs", "sketch_jobs"])
def test_r33_real_vision_and_sketch_intents_drain_through_alternating_instances(
    first_drainer: str,
) -> None:
    """R33 with completion-generated intents: a Vision UNSAFE and a Sketch UNSAFE quarantine,
    each left pending by a failing immediate sink, drained by alternating job services."""

    c = build_sketch_chain_harness()
    first = c.h.jobs if first_drainer == "h.jobs" else c.sketch_jobs
    second = c.sketch_jobs if first_drainer == "h.jobs" else c.h.jobs
    vision_event = _unsafe_vision_with_failed_sink(c)
    vision_refs = _pending_quarantine(c)[vision_event].artifact_refs
    assert first.deliver_side_effects() >= 1
    assert vision_event not in _pending_quarantine(c)
    assert all(ref in c.raw_artifacts.quarantined for ref in vision_refs)

    c.h.clock.advance(seconds=6)
    proposal_id, sketch_event = _unsafe_sketch_with_failed_sink(c, intent="R33 real intent")
    sketch_refs = _pending_quarantine(c)[sketch_event].artifact_refs
    assert second.deliver_side_effects() >= 1
    assert second.deliver_side_effects() == 0
    assert _pending_quarantine(c) == {}
    assert all(ref in c.raw_artifacts.quarantined for ref in sketch_refs)
    blocked = c.service.reconcile(proposal_id)
    assert blocked is not None and blocked.current.pipeline_state is PipelineState.BLOCKED_UNSAFE

    callers = {first_drainer: vision_event, ("sketch_jobs" if first_drainer == "h.jobs"
                                            else "h.jobs"): sketch_event}
    for caller, event_id in callers.items():
        entries = [e for e in c.artifact_port.audit if e.event_id == event_id and e.bumped]
        assert entries and all(e.caller == caller for e in entries)
    bumped_refs = [e.ref for e in c.artifact_port.audit if e.bumped]
    assert sorted(bumped_refs) == sorted((*vision_refs, *sketch_refs))
