"""BE2-04 SK1 chain acceptance: source handoff, shared queue and A1 builder parity."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import replace
from typing import Any, cast

import pytest

from sketch2life.application.ports.assistance import ReceiptOutcome
from sketch2life.application.ports.sketch_generation import (
    GenerationFailed,
    GenerationRequest,
    GenerationSucceeded,
    JobCreateKind,
    JobCreateOutcome,
    SketchJobCreate,
)
from sketch2life.application.services.ai_jobs import FIXTURE_RETRY_POLICY
from sketch2life.application.services.sketch_generation import (
    NoticeKind,
    OpenOutcome,
    OwnerNotice,
    ReviseLevelCommand,
)
from sketch2life.application.services.vision_analysis import CorrectionCommand
from sketch2life.domain.ai_jobs.completion import CompletionClaim, Moderation, OutcomeKind
from sketch2life.domain.sketch_proposal import (
    LevelSource,
    ModerationState,
    OutputPart,
    PipelineState,
    StatusReason,
    content_sha256,
)
from sketch2life.domain.vision_analysis import analysis_etag
from sketch2life.infrastructure.assistance.harness import (
    CANVAS_P,
    CHILD_A,
    CHILD_B,
    DEVICE_A,
    GROUP,
    LEVEL,
    LEVEL_2,
    ORG,
    PURPOSE,
    SESSION,
    TEACHER,
    build_assistance_harness,
    checkpoint_ref,
)
from sketch2life.infrastructure.sketch_generation.fakes import default_outcome
from sketch2life.infrastructure.sketch_generation.harness import (
    SketchChainHarness,
    build_sketch_chain_harness,
)


def _replace_attr(target: object, name: str, replacement: object) -> None:
    setattr(target, name, replacement)


@pytest.fixture
def c() -> SketchChainHarness:
    return build_sketch_chain_harness()


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


def _finish_one_vision(chain: SketchChainHarness | None, h: Any, assistance_id: str, *,
                      expect_started: bool = True) -> None:
    h.dispatch()
    if chain is not None:
        routed = chain.router.run_next()
        assert routed is not None and routed.started is expect_started
        assert routed.job_type == "vision_analysis"
    else:
        started, job_id, attempt_id = h.start_next()
        assert started.started is expect_started
        if expect_started:
            h.finish_vision(job_id, attempt_id)
    assert h.service.reconcile(assistance_id) is not None


def _snapshots(h: Any) -> tuple[object, ...]:
    return (h.store.snapshot(), h.job_store.snapshot(), h.vision_store.snapshot(),
            h.artifacts.quarantined)


def _source_state(c: SketchChainHarness) -> tuple[str, str, int]:
    resolved = c.h.sources.resolve(ORG, CANVAS_P, checkpoint_ref(c.h.source_p))
    assert resolved is not None
    canvas = c.h.owner.canvases[CANVAS_P]
    return (resolved.snapshot.input_hash(), resolved.snapshot.render.render_sha256,
            canvas.document_epoch)


def test_p01_chain_promotes_derived_output_and_keeps_source_facts_unchanged(
    c: SketchChainHarness,
) -> None:
    source_before = _source_state(c)
    proposal_id = c.open_ready(c.h.command(level=LEVEL_2))
    proposal = c.proposal(proposal_id)
    assistance_id = proposal.binding.assistance_id
    result = c.run_sketch(proposal_id)
    assert result is not None and result.started
    proposal = c.proposal(proposal_id)
    assert proposal.current.pipeline_state is PipelineState.PENDING_TEACHER_REVIEW
    assert proposal.current.moderation_state is ModerationState.PENDING
    promoted = proposal.current.promoted
    assert promoted is not None and promoted.content_sha256
    assert _source_state(c) == source_before
    if promoted.asset is not None:
        provenance = c.admission.provenance[promoted.asset.artifact_ref]
        assert provenance.origin == "ai_derived"
        assert provenance.source_refs == ((proposal.binding.source.render_ref,
                                           proposal.binding.source.render_sha256),)
    view = c.service.device_view(DEVICE_A, assistance_id)
    assert view["status"] == "pending" and "text_or_question" not in view
    assert c.audit_violations() == []


def test_p02_chain_level_one_is_text_only_side_reference(c: SketchChainHarness) -> None:
    """P02 in the chain: an A1 level_fx_1 request yields text only, no overlay asset."""

    proposal_id = c.open_ready(c.h.command(level=LEVEL))
    routed = c.run_sketch(proposal_id)
    assert routed is not None and routed.started
    proposal = c.proposal(proposal_id)
    assert proposal.current.pipeline_state is PipelineState.PENDING_TEACHER_REVIEW
    assert proposal.current.level == LEVEL == proposal.binding.requested_level
    promoted = proposal.current.promoted
    assert promoted is not None and promoted.asset is None and promoted.text
    record = c.service.get_record(TEACHER, proposal_id)
    assert record["display_mode"] == "side_reference"
    assert record["overlay_asset_ref"] is None
    assert isinstance(record["text_or_question"], str) and record["text_or_question"]
    document = c.raw_artifacts.describe(promoted.result_document.artifact_ref)
    assert document is not None and document.quarantine_reason is None
    assert document.producer_job_id == promoted.job_id
    assert document.producer_attempt_id == promoted.attempt_id
    assert c.generator.requests[-1].rule.asset.value == "forbidden"


def test_p06_chain_repeated_hint_and_id_opens_one_proposal_job_and_call(
    c: SketchChainHarness,
) -> None:
    """P06 in the chain: hint + open-by-id repeated gives one proposal, one job, one call."""

    assistance_id = c.ready(c.h.command(intent="P06 repeated open"))
    (intent,) = [i for i in c.h.sketch.intents if i.assistance_id == assistance_id]
    c.forward_hints()
    c.stage.request_sketch(intent)  # duplicate post-commit callback for the same intent
    inbox = c.service.process_inbox(ORG)
    by_id = [c.service.open_from_handoff(ORG, assistance_id) for _ in range(3)]
    proposal_id = c.proposal_for(assistance_id)
    assert proposal_id is not None
    assert [r.proposal_id for r in (*inbox, *by_id)] == [proposal_id] * (len(inbox) + 3)
    assert {r.outcome for r in by_id} == {OpenOutcome.REPLAYED}
    assert len(c.store.snapshot().proposals) == 1
    assert c.store.snapshot().hints == {}
    for _ in range(2):
        c.run_sketch(proposal_id)
    sketch_jobs = [j for j in c.h.job_store.snapshot().jobs.values()
                   if j.job_type == "sketch_generation"]
    assert len(sketch_jobs) == 1
    assert c.generator.calls[proposal_id] == 1
    assert c.proposal(proposal_id).current.pipeline_state is (
        PipelineState.PENDING_TEACHER_REVIEW)


def test_p03_group_audience_is_pinned_to_job_subject_refs(c: SketchChainHarness) -> None:
    proposal_id = c.open_ready(c.h.group_command(level=LEVEL_2))
    proposal = c.proposal(proposal_id)
    job = c.job_reader.get(proposal.current.job_id or "")
    assert proposal.binding.audience == (CHILD_A, CHILD_B)
    assert job is not None and job.job_type == "sketch_generation"
    created = next(j for j in c.h.job_store.snapshot().jobs.values()
                   if j.job_id == proposal.current.job_id)
    assert created.scope.subject_refs == (CHILD_A, CHILD_B)


def test_p04_cache_hit_opens_by_id_without_a_sketch_hint(c: SketchChainHarness) -> None:
    intent = "same cacheable intent"
    original_id = c.ready(c.h.command(intent=intent))
    cached = c.h.submit(c.h.command(intent=intent))
    assert cached.outcome is ReceiptOutcome.CACHE_HIT
    assistance_id = cached.request.assistance_id
    assert cached.request.cache_hit_of is not None
    assert not any(i.assistance_id == assistance_id for i in c.h.sketch.intents)
    result = c.service.open_from_handoff(ORG, assistance_id)
    assert result.proposal_id is not None
    proposal = c.proposal(result.proposal_id)
    assert proposal.binding.handoff_kind == "cache_hit"
    original_request = c.h.request(original_id)
    assert original_request.handoff is not None
    assert proposal.binding.analysis_id == original_request.handoff.analysis_id
    assert proposal.current.job_id is not None


def test_r12_dropped_hint_recovers_only_when_opened_by_id(c: SketchChainHarness) -> None:
    assistance_id = c.ready(c.h.command(intent="lost sketch hint"))
    assert c.forward_hints(drop=True) == 1
    assert c.proposal_for(assistance_id) is None
    opened = c.service.open_from_handoff(ORG, assistance_id)
    assert opened.outcome is OpenOutcome.CREATED and opened.proposal_id is not None
    assert c.proposal(opened.proposal_id).current.job_id is not None


def test_retryable_create_is_retried_on_open_by_id_replay(c: SketchChainHarness) -> None:
    assistance_id = c.ready(c.h.command(intent="retry sketch create"))
    create = c.job_port.create
    _replace_attr(
        c.job_port, "create",
        lambda request: JobCreateOutcome(JobCreateKind.RETRY, code="TEMPORARY"),
    )
    first = c.service.open_from_handoff(ORG, assistance_id)
    assert first.outcome is OpenOutcome.CREATED and first.proposal_id is not None
    assert c.proposal(first.proposal_id).current.job_id is None
    _replace_attr(c.job_port, "create", create)

    replay = c.service.open_from_handoff(ORG, assistance_id)
    assert replay.outcome is OpenOutcome.REPLAYED
    assert replay.proposal_id == first.proposal_id
    assert c.proposal(first.proposal_id).current.job_id is not None
    assert sum(job.job_type == "sketch_generation"
               for job in c.h.job_store.snapshot().jobs.values()) == 1


def test_n21_owner_notice_cleans_queued_sketch_job(c: SketchChainHarness) -> None:
    proposal_id = c.open_ready(c.h.command())
    proposal = c.proposal(proposal_id)
    job_id = proposal.current.job_id
    assert job_id is not None

    affected = c.service.apply_owner_notice(OwnerNotice(
        "notice_fx_chain", ORG, NoticeKind.CONSENT_REVOKED, participant_id=CHILD_A))
    assert affected == (proposal_id,)
    stale = c.proposal(proposal_id)
    assert stale.current.pipeline_state is PipelineState.STALE
    job = c.job_reader.get(job_id)
    assert job is not None and job.state == "cancelled"
    assert job.failure_code == StatusReason.CONSENT_REVOKED.value


def test_p08_p11_chain_revise_level_pins_policy_job_digest_and_content(
    c: SketchChainHarness,
) -> None:
    proposal_id = c.open_ready(c.h.command(level=LEVEL))
    first_route = c.run_sketch(proposal_id)
    assert first_route is not None and first_route.started
    before = c.proposal(proposal_id)
    assert before.current.pipeline_state is PipelineState.PENDING_TEACHER_REVIEW
    v1 = before.current
    v1_job = v1.job_id
    assert v1_job is not None and v1.level_source is LevelSource.REQUEST
    assert c.policy.snapshot is not None
    revised_policy = replace(c.policy.snapshot, version="2",
                             generator_profile_ref="fixture-sketch-profile-v2")
    assert c.publish_policy(revised_policy)

    result = c.service.revise_level(ReviseLevelCommand(
        TEACHER, proposal_id, "key_fx_chain_revise_level", before.etag(), LEVEL_2))
    assert result.outcome == "revised" and result.proposal_version == 2
    revised = c.proposal(proposal_id)
    v2 = revised.current
    assert revised.versions[0].pipeline_state is PipelineState.STALE
    assert revised.versions[0].level == LEVEL
    assert revised.versions[0].level_source is LevelSource.REQUEST
    assert v2.level == LEVEL_2 and v2.level_source is LevelSource.REVISION
    assert (v2.policy_version, v2.generator_profile_ref) == (
        "2", "fixture-sketch-profile-v2")
    assert v2.job_id not in {None, v1_job}
    job = c.job_reader.get(v2.job_id or "")
    assert job is not None and job.input_hash == v2.generation_digest

    routed = c.run_sketch(proposal_id)
    assert routed is not None and routed.started
    request = c.generator.requests[-1]
    assert request.assistance_level == LEVEL_2
    assert request.generation_digest == v2.generation_digest
    assert request.generator_profile_ref == v2.generator_profile_ref
    promoted = c.proposal(proposal_id).current.promoted
    assert promoted is not None
    assert promoted.content_sha256 == content_sha256(
        c.proposal(proposal_id), v2, text=promoted.text, asset=promoted.asset,
        producer=promoted.producer)


@pytest.mark.parametrize("change", ["none", "consent", "teacher", "render", "policy"])
def test_n23_chain_withholds_only_when_current_facts_change(
    c: SketchChainHarness, change: str,
) -> None:
    proposal_id = c.open_ready(c.h.command())
    routed = c.run_sketch(proposal_id)
    assert routed is not None and routed.started
    before = c.proposal(proposal_id)
    assert before.current.pipeline_state is PipelineState.PENDING_TEACHER_REVIEW
    assert c.service.get_record(TEACHER, proposal_id)["text_or_question"] is not None

    if change == "consent":
        assert c.h.publish_owner_change(
            lambda: c.h.owner.update_member(CHILD_A, consent_effective=False))
    elif change == "teacher":
        analysis_id = before.binding.analysis_id
        head = c.h.vision_store.snapshot().heads[analysis_id]
        c.h.vision.submit_correction(CorrectionCommand(
            principal=TEACHER, analysis_id=analysis_id,
            idempotency_key="key_fx_n23_teacher_confirm",
            if_match=analysis_etag(analysis_id, head.analysis_revision),
            intended_objects=("tiger",), correction_reason="Teacher confirmed meaning",
            expected_context_revision=head.context_revision))
    elif change == "render":
        source = c.h.source_p
        changed_render = replace(source.snapshot.render, render_ref="render_fx_n23_changed",
                                 render_sha256="f" * 64)
        c.h.sources.add(ORG, CANVAS_P, replace(
            source, snapshot=replace(source.snapshot, render=changed_render)))
    elif change == "policy":
        assert c.policy.snapshot is not None
        assert c.publish_policy(replace(c.policy.snapshot, version="2", rules={}))

    after_change = c.proposal(proposal_id)
    record = c.service.get_record(TEACHER, proposal_id)
    if change == "none":
        assert record["text_or_question"] is not None
        assert record["content_withheld_reason"] is None
        assert after_change == before
        assert c.store.snapshot().revalidations == []
        return

    expected_reason = {
        "consent": StatusReason.CONSENT_REVOKED.value,
        "teacher": StatusReason.MEANING_CHANGED.value,
        "render": StatusReason.SOURCE_CHANGED.value,
        "policy": StatusReason.POLICY_CHANGED.value,
    }[change]
    assert record["text_or_question"] is None and record["overlay_asset_ref"] is None
    assert record["content_withheld_reason"] == expected_reason
    assert after_change == before  # read-withholding does not mutate proposal state
    assert c.store.snapshot().revalidations == [proposal_id]
    stale = c.service.revalidate(proposal_id)
    assert stale is not None and stale.current.pipeline_state is PipelineState.STALE
    assert stale.review_revision == before.review_revision + 1
    assert stale.current.status_reason is not None
    assert stale.current.status_reason.value == expected_reason


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ("consent", StatusReason.CONSENT_REVOKED),
        ("session", StatusReason.SESSION_ENDED),
        ("age", StatusReason.ANALYSIS_NOT_APPLICABLE),
        ("roster", StatusReason.AUDIENCE_CHANGED),
    ],
)
def test_n06_owner_facts_changed_before_open_create_stale_without_job(
    c: SketchChainHarness, change: str, reason: StatusReason,
) -> None:
    assistance_id = c.ready(c.h.group_command() if change == "roster" else c.h.command())
    if change == "consent":
        c.h.owner.update_member(CHILD_A, consent_effective=False)
    elif change == "session":
        canvas = c.h.owner.canvases[CANVAS_P]
        c.h.owner.canvases[canvas.canvas_id] = replace(canvas, session_active=False)
    elif change == "age":
        c.h.owner.update_member(CHILD_A, months=20)
        c.h.vision_context.set_participant(CHILD_A, age_months=20,
                                           purposes=frozenset({PURPOSE}))
    else:
        roster = c.h.owner.rosters[(SESSION, GROUP)]
        c.h.owner.rosters[(SESSION, GROUP)] = replace(roster, members=(CHILD_A,), revision=2)

    opened = c.service.open_from_handoff(ORG, assistance_id)
    assert opened.outcome is OpenOutcome.CREATED and opened.proposal_id is not None
    proposal = c.proposal(opened.proposal_id)
    assert proposal.current.pipeline_state is PipelineState.STALE
    assert proposal.current.status_reason is reason
    assert not any(job.job_type == "sketch_generation"
                   for job in c.h.job_store.snapshot().jobs.values())
    assert not c.generator.calls


@pytest.mark.parametrize("refusal", ["authorization", "kill_switch", "budget"])
def test_n07_create_refusal_stales_and_never_calls_provider(
    c: SketchChainHarness, refusal: str,
) -> None:
    assistance_id = c.ready(c.h.command())
    if refusal == "authorization":
        c.h.job_authorization.revoke(DEVICE_A.principal_id)
    elif refusal == "kill_switch":
        c.h.owner_eligibility.killed_job_types.add("sketch_generation")
    else:
        create = c.job_port.create

        def exhaust_budget(request: SketchJobCreate) -> JobCreateOutcome:
            c.h.owner_eligibility.budget_exhausted_targets.add(request.target_id)
            return create(request)

        _replace_attr(c.job_port, "create", exhaust_budget)

    opened = c.service.open_from_handoff(ORG, assistance_id)
    assert opened.proposal_id is not None
    proposal = c.proposal(opened.proposal_id)
    assert proposal.current.pipeline_state is PipelineState.STALE
    assert proposal.current.status_reason is StatusReason.SCHEDULE_REFUSED
    assert not any(job.job_type == "sketch_generation"
                   for job in c.h.job_store.snapshot().jobs.values())
    assert not c.generator.calls


def test_n10_consent_revoked_during_provider_call_blocks_staging_and_promotion(
    c: SketchChainHarness,
) -> None:
    assistance_id = c.ready(c.h.command())
    proposal_id = c.service.open_from_handoff(ORG, assistance_id).proposal_id
    assert proposal_id is not None

    def revoke_during_generate(
        request: GenerationRequest,
    ) -> GenerationSucceeded | GenerationFailed:
        c.h.owner.update_member(CHILD_A, consent_effective=False)
        return default_outcome(request)

    _replace_attr(c.generator, "script", revoke_during_generate)
    routed = c.run_sketch(proposal_id)
    assert routed is not None and routed.started
    proposal = c.proposal(proposal_id)
    assert proposal.current.pipeline_state is PipelineState.STALE
    assert proposal.current.status_reason is StatusReason.CONSENT_REVOKED
    assert c.generator.calls[proposal_id] == 1
    assert c.store.snapshot().staged == {}
    assert not any(event.event_type == "sketch.proposal_ready"
                   for event in c.store.snapshot().events)


def test_n14_provider_unavailable_exhausts_fixture_retries() -> None:
    c = build_sketch_chain_harness()
    proposal_id = c.open_ready(c.h.command())
    unavailable = GenerationFailed("PROVIDER_UNAVAILABLE", True, True)
    _replace_attr(c.generator, "script", lambda _: unavailable)
    for attempt in range(1, FIXTURE_RETRY_POLICY.max_attempts + 1):
        routed = c.run_sketch(proposal_id, reconcile=False)
        assert routed is not None and routed.started
        job_id = c.proposal(proposal_id).current.job_id
        assert job_id is not None
        evidence = c.job_reader.get(job_id)
        assert evidence is not None
        if attempt < FIXTURE_RETRY_POLICY.max_attempts:
            assert evidence.state == "failed_retryable"
            backoff = FIXTURE_RETRY_POLICY.backoff_after(attempt)
            c.h.clock.advance(milliseconds=int(backoff.total_seconds() * 1000))
            assert c.sketch_jobs.run_due_retries() == (job_id,)
        else:
            assert evidence.state == "failed_exhausted"
    failed = c.service.reconcile(proposal_id)
    assert failed is not None and failed.current.pipeline_state is PipelineState.FAILED
    assert failed.current.status_reason is StatusReason.PROVIDER_UNAVAILABLE
    assert c.store.snapshot().staged == {}


def test_f5_a1_instance_retry_sweep_checks_sketch_eligibility(c: SketchChainHarness) -> None:
    proposal_id = c.open_ready(c.h.command())
    _replace_attr(c.generator, "script", lambda _: GenerationFailed(
        "PROVIDER_UNAVAILABLE", True, True))
    routed = c.run_sketch(proposal_id, reconcile=False)
    assert routed is not None and routed.started
    proposal = c.proposal(proposal_id)
    job_id = proposal.current.job_id
    assert job_id is not None
    failed = c.job_reader.get(job_id)
    assert failed is not None and failed.state == "failed_retryable"

    _replace_attr(c.service, "_cleanup_job", lambda *_: None)
    notice = OwnerNotice("notice_fx_retry", ORG, NoticeKind.CONSENT_REVOKED,
                         participant_id=CHILD_A)
    assert c.service.apply_owner_notice(notice) == (proposal_id,)
    stale = c.proposal(proposal_id)
    assert stale.current.pipeline_state is PipelineState.STALE
    still_retryable = c.job_reader.get(job_id)
    assert still_retryable is not None and still_retryable.state == "failed_retryable"
    backoff = FIXTURE_RETRY_POLICY.backoff_after(1)
    c.h.clock.advance(milliseconds=int(backoff.total_seconds() * 1000))
    assert c.h.jobs.run_due_retries() == ()
    final = c.job_reader.get(job_id)
    assert final is not None and final.state == "cancelled"
    assert final.attempt_number == 1


def test_n13_provider_timeout_exhausts_fixture_retries() -> None:
    c = build_sketch_chain_harness()
    proposal_id = c.open_ready(c.h.command())
    timeout = GenerationFailed("PROVIDER_TIMEOUT", True, True)
    _replace_attr(c.generator, "script", lambda _: timeout)
    for attempt in range(1, FIXTURE_RETRY_POLICY.max_attempts + 1):
        routed = c.run_sketch(proposal_id, reconcile=False)
        assert routed is not None and routed.started
        job_id = c.proposal(proposal_id).current.job_id
        assert job_id is not None
        evidence = c.job_reader.get(job_id)
        assert evidence is not None
        if attempt < FIXTURE_RETRY_POLICY.max_attempts:
            assert evidence.state == "failed_retryable"
            backoff = FIXTURE_RETRY_POLICY.backoff_after(attempt)
            c.h.clock.advance(milliseconds=int(backoff.total_seconds() * 1000))
            assert c.sketch_jobs.run_due_retries() == (job_id,)
        else:
            assert evidence.state == "failed_exhausted"
    failed = c.service.reconcile(proposal_id)
    assert failed is not None and failed.current.pipeline_state is PipelineState.FAILED
    assert failed.current.status_reason is StatusReason.PROVIDER_TIMEOUT
    assert c.store.snapshot().staged == {}


def test_p07_retryable_attempt_two_success_promotes_only_attempt_two(
    c: SketchChainHarness,
) -> None:
    proposal_id = c.open_ready(c.h.command())
    outcomes = iter((GenerationFailed("PROVIDER_TIMEOUT", True, True),))

    def fail_once_then_succeed(
        request: GenerationRequest,
    ) -> GenerationSucceeded | GenerationFailed:
        try:
            return next(outcomes)
        except StopIteration:
            return default_outcome(request)

    _replace_attr(c.generator, "script", fail_once_then_succeed)
    first = c.run_sketch(proposal_id, reconcile=False)
    assert first is not None and first.started
    job_id = c.proposal(proposal_id).current.job_id
    assert job_id is not None
    evidence = c.job_reader.get(job_id)
    assert evidence is not None and evidence.state == "failed_retryable"
    first_attempt_id = evidence.active_attempt_id
    backoff = FIXTURE_RETRY_POLICY.backoff_after(1)
    c.h.clock.advance(milliseconds=int(backoff.total_seconds() * 1000))
    assert c.sketch_jobs.run_due_retries() == (job_id,)

    c.sketch_jobs.dispatch_outbox()
    second = c.router.run_next()
    assert second is not None and second.started
    promoted = c.service.reconcile(proposal_id)
    assert promoted is not None and promoted.current.pipeline_state is (
        PipelineState.PENDING_TEACHER_REVIEW)
    assert promoted.current.promoted is not None
    assert promoted.current.promoted.attempt_id != first_attempt_id
    staged = c.store.snapshot().staged
    assert len(staged) == 1
    assert next(iter(staged.values())).attempt_id == promoted.current.promoted.attempt_id


def test_n18_chain_rejects_canvas_operations_without_mutating_source(
    c: SketchChainHarness,
) -> None:
    source_before = _source_state(c)
    proposal_id = c.open_ready(c.h.command())
    _replace_attr(c.generator, "script", lambda request: replace(
        default_outcome(request), parts=(OutputPart("canvas_operations", text="draw"),)))
    routed = c.run_sketch(proposal_id, reconcile=False)
    assert routed is not None and routed.started
    failed = c.service.reconcile(proposal_id)
    assert failed is not None and failed.current.pipeline_state is PipelineState.FAILED
    assert failed.current.status_reason is StatusReason.OUTPUT_MALFORMED
    assert failed.current.promoted is None
    assert _source_state(c) == source_before
    assert c.store.snapshot().staged == {}


def test_n22_child_correction_does_not_change_meaning_basis_or_block_generation(
    c: SketchChainHarness,
) -> None:
    assistance_id = c.ready(c.h.command())
    opened = c.service.open_from_handoff(ORG, assistance_id)
    assert opened.proposal_id is not None
    proposal = c.proposal(opened.proposal_id)
    analysis_id = proposal.binding.analysis_id
    head = c.h.vision_store.snapshot().heads[analysis_id]
    c.h.vision.submit_correction(CorrectionCommand(
        principal=DEVICE_A, analysis_id=analysis_id, idempotency_key="key_fx_n22_child",
        if_match=analysis_etag(analysis_id, head.analysis_revision),
        intended_objects=("tiger",), child_explanation="It has stripes",
        correction_reason="Child proposes what the picture shows",
        expected_context_revision=head.context_revision))

    routed = c.run_sketch(opened.proposal_id)
    assert routed is not None and routed.started
    ready = c.proposal(opened.proposal_id)
    assert ready.current.pipeline_state is PipelineState.PENDING_TEACHER_REVIEW
    assert ready.binding.analysis_id == analysis_id
    assert ready.binding.analysis_revision == proposal.binding.analysis_revision


def test_chain_ready_routes_the_submitted_vision_job_after_older_fifo_work(
    c: SketchChainHarness,
) -> None:
    older = c.h.submit(c.h.command(intent="older queued Vision"))
    c.h.dispatch()
    older_job = next(job for job in c.h.job_store.snapshot().jobs.values()
                     if job.active_attempt.request_ref.request_id == older.request.assistance_id)
    target = c.ready(c.h.group_command())
    assert target != older.request.assistance_id
    assert c.side_routes
    assert c.side_routes[0].job_id == older_job.job_id
    assert all(route.job_id != c.h.request(target).job_id for route in c.side_routes)
    target_request = c.h.request(target)
    assert target_request.status.value == "analysis_ready"


@pytest.mark.parametrize("scenario", ["submit", "run", "cache", "revoke", "unsafe"])
def test_c11_rebuilt_builder_matches_a1_builder(scenario: str) -> None:
    original = build_assistance_harness()
    chain = build_sketch_chain_harness()
    rebuilt = chain.h

    def submit_and_run(h: Any, router: Any | None, *, intent: str) -> str:
        request = h.submit(h.command(intent=intent)).request
        if scenario != "submit":
            _finish_one_vision(chain if router is not None else None, h, request.assistance_id)
        return cast(str, request.assistance_id)

    if scenario in {"submit", "run"}:
        submit_and_run(original, None, intent="parity A1")
        submit_and_run(rebuilt, chain.router, intent="parity A1")
    elif scenario == "cache":
        first_original = submit_and_run(original, None, intent="parity cache")
        first_rebuilt = submit_and_run(rebuilt, chain.router, intent="parity cache")
        original.clock.advance(seconds=6)
        rebuilt.clock.advance(seconds=6)
        original.submit(original.command(intent="parity cache"))
        rebuilt.submit(rebuilt.command(intent="parity cache"))
        assert original.request(first_original).handoff is not None
        assert rebuilt.request(first_rebuilt).handoff is not None
    elif scenario == "revoke":
        original_id = original.submit(original.command()).request.assistance_id
        rebuilt_id = rebuilt.submit(rebuilt.command()).request.assistance_id
        original.dispatch()
        rebuilt.dispatch()
        original.revoke_consent(CHILD_A)
        rebuilt.revoke_consent(CHILD_A)
        _finish_one_vision(None, original, original_id, expect_started=False)
        _finish_one_vision(chain, rebuilt, rebuilt_id, expect_started=False)
    else:
        def install_unsafe_completion(h: Any) -> None:
            def finish(job_id: str, attempt_id: str) -> object:
                job = h.job_store.snapshot().jobs[job_id]
                request_ref = job.active_attempt.request_ref
                output = h.artifacts.put(ORG, b"synthetic unsafe Vision output",
                                         job_id=job_id, attempt_id=attempt_id)
                envelope = h.last_envelope
                assert envelope is not None
                claim = CompletionClaim(
                    job_id, attempt_id, request_ref.request_revision, request_ref.input_hash,
                    request_ref.context_revision, OutcomeKind.SUCCESS, outputs=(output,),
                    moderation=Moderation.UNSAFE)
                return h.jobs.accept_completion(envelope.capability, claim)

            h.finish_vision = finish

        install_unsafe_completion(original)
        install_unsafe_completion(rebuilt)
        original_id = original.submit(original.command()).request.assistance_id
        rebuilt_id = rebuilt.submit(rebuilt.command()).request.assistance_id
        _finish_one_vision(None, original, original_id)
        _finish_one_vision(chain, rebuilt, rebuilt_id)

    assert _snapshots(original) == _snapshots(rebuilt)
