"""BE2-04 SK1.2 service over the unit harness (real BE2-01 jobs, scripted handoff reader):
SK-P02, P06, P08, P09, P10, N01-N05, N08, N11, N15-N17, N20, N21, N23, N24, decision rounds."""

from __future__ import annotations

from dataclasses import replace

import pytest

from sketch2life.application.ports.ai_jobs import Principal, PrincipalRole
from sketch2life.application.ports.sketch_generation import (
    GenerationFailed,
    GenerationRequest,
    GenerationSucceeded,
    HandoffHint,
    HandoffRefusal,
    HandoffRefusalCode,
)
from sketch2life.application.services.ai_jobs import CreateJobCommand
from sketch2life.application.services.sketch_generation import (
    CancelCommand,
    NoticeKind,
    OpenOutcome,
    OwnerNotice,
    ReviseLevelCommand,
    SketchError,
)
from sketch2life.domain.ai_jobs.model import JobState, RequestRef
from sketch2life.domain.sketch_proposal import (
    LevelSource,
    MeaningBasis,
    ModerationState,
    OutputPart,
    PipelineState,
    StagedStatus,
    StatusReason,
    content_sha256,
)
from sketch2life.infrastructure.assistance.harness import (
    CHILD_A,
    CHILD_B,
    DEVICE_A,
    LEVEL,
    LEVEL_2,
    ORG,
    OTHER_CLASS_TEACHER,
    OUTSIDER,
    SESSION,
    TEACHER,
)
from sketch2life.infrastructure.sketch_generation.fakes import (
    default_outcome,
    fixture_sketch_policy,
)
from sketch2life.infrastructure.sketch_generation.harness import (
    SketchUnitHarness,
    build_sketch_unit_harness,
    make_binding,
)


@pytest.fixture
def u() -> SketchUnitHarness:
    return build_sketch_unit_harness()


def opened(u: SketchUnitHarness, level: str = LEVEL_2, **changes: object) -> str:
    result = u.open(make_binding(level=level, **changes))  # type: ignore[arg-type]
    assert result.outcome is OpenOutcome.CREATED and result.code is None, result
    assert result.proposal_id is not None
    return result.proposal_id


def ready(u: SketchUnitHarness, level: str = LEVEL_2) -> str:
    proposal_id = opened(u, level)
    assert u.run(proposal_id).current.pipeline_state is PipelineState.PENDING_TEACHER_REVIEW
    return proposal_id


def events(u: SketchUnitHarness) -> list[str]:
    return [e.event_type for e in u.store.snapshot().events]


def cancel(u: SketchUnitHarness, proposal_id: str, *, key: str | None = "key_fx_c1",
           if_match: str | None = "auto", principal: Principal = TEACHER,
           reason: str = "CANCELLED_BY_TEACHER") -> object:
    if if_match == "auto":
        if_match = u.proposal(proposal_id).etag()
    return u.service.cancel(CancelCommand(principal, proposal_id, key, if_match, reason))


def revise(u: SketchUnitHarness, proposal_id: str, level: str = LEVEL_2, *,
           key: str | None = "key_fx_r1", if_match: str | None = "auto") -> object:
    if if_match == "auto":
        if_match = u.proposal(proposal_id).etag()
    return u.service.revise_level(ReviseLevelCommand(TEACHER, proposal_id, key, if_match, level))


# ------------------------------------------------------------------ positive
def test_p02_level_one_is_text_only_side_reference(u: SketchUnitHarness) -> None:
    proposal_id = ready(u, LEVEL)
    record = u.service.get_record(TEACHER, proposal_id)
    assert record["display_mode"] == "side_reference"
    assert record["overlay_asset_ref"] is None and isinstance(record["text_or_question"], str)
    promoted = u.proposal(proposal_id).current.promoted
    assert promoted is not None and promoted.asset is None
    assert u.artifacts.describe(promoted.result_document.artifact_ref) is not None
    assert record["moderation_state"] == "pending" and record["approval_ref"] is None


def test_p06_repeated_open_is_one_proposal_one_job_one_call(u: SketchUnitHarness) -> None:
    binding = u.add(make_binding())
    first = u.service.open_from_handoff(ORG, binding.assistance_id)
    hint = HandoffHint("intent_fx_1", binding.assistance_id, 1, binding.analysis_id, 1)
    u.service.add_hint(ORG, hint)
    u.service.add_hint(ORG, hint)
    again = u.service.process_inbox(ORG)
    third = u.service.open_from_handoff(ORG, binding.assistance_id)
    assert first.outcome is OpenOutcome.CREATED
    assert [r.outcome for r in again] == [OpenOutcome.REPLAYED]
    assert third.outcome is OpenOutcome.REPLAYED and third.proposal_id == first.proposal_id
    assert first.proposal_id is not None
    u.run(first.proposal_id)
    u.run(first.proposal_id)
    assert len(u.job_store.snapshot().jobs) == 1
    assert u.generator.calls[first.proposal_id] == 1
    assert u.store.snapshot().hints == {}


def test_p08_revise_level_creates_new_version_at_revised_level(u: SketchUnitHarness) -> None:
    proposal_id = ready(u, LEVEL)
    v1_job = u.proposal(proposal_id).current.job_id
    result = revise(u, proposal_id, LEVEL_2)
    assert result.outcome == "revised" and result.proposal_version == 2  # type: ignore[attr-defined]
    proposal = u.proposal(proposal_id)
    assert proposal.current.pipeline_state is PipelineState.REQUESTED
    assert proposal.current.job_id not in {None, v1_job}  # rescheduled
    assert proposal.review_revision == 2
    assert proposal.versions[0].pipeline_state is PipelineState.STALE
    u.run(proposal_id)
    record = u.service.get_record(TEACHER, proposal_id)
    assert record["pipeline_state"] == "pending_teacher_review"
    assert record["assistance_level"] == LEVEL_2 and record["proposal_version"] == 2
    assert record["level_source"]["kind"] == "revision"  # type: ignore[index]
    assert record["overlay_asset_ref"] is not None
    assert proposal.binding.requested_level == LEVEL
    assert "sketch.superseded" in events(u)


def test_p11_revision_pins_policy_profile_across_digest_job_and_content(
    u: SketchUnitHarness,
) -> None:
    proposal_id = ready(u, LEVEL)
    original = u.proposal(proposal_id).versions[0]
    assert u.policy.snapshot is not None
    revised_policy = replace(u.policy.snapshot, version="2",
                             generator_profile_ref="fixture-sketch-profile-v2")
    u.policy.snapshot = revised_policy
    u.decision.bump(f"org:{ORG}")

    result = revise(u, proposal_id, LEVEL_2)
    assert result.proposal_version == 2  # type: ignore[attr-defined]
    proposal = u.proposal(proposal_id)
    version = proposal.current
    assert original.generator_profile_ref != version.generator_profile_ref
    assert (version.policy_version, version.generator_profile_ref) == (
        "2", "fixture-sketch-profile-v2")
    job = u.job_store.snapshot().jobs[version.job_id or ""]
    assert job.request_ref.input_hash == version.generation_digest
    u.run(proposal_id)
    request = u.generator.requests[-1]
    record = u.service.get_record(TEACHER, proposal_id)
    assert request.generation_digest == version.generation_digest
    assert request.generator_profile_ref == version.generator_profile_ref
    assert record["policy_ref"] == {
        "policy_id": version.policy_id, "version": version.policy_version,
        "status": version.policy_status,
    }
    promoted = u.proposal(proposal_id).current.promoted
    assert promoted is not None
    recomputed = content_sha256(u.proposal(proposal_id), version, text=promoted.text,
                                asset=promoted.asset, producer=promoted.producer)
    assert recomputed == promoted.content_sha256


def test_p09_teacher_record_fields_and_minimal_device_view(u: SketchUnitHarness) -> None:
    proposal_id = opened(u)
    expected = {
        "proposal_id", "proposal_version", "review_revision", "assistance_id",
        "request_revision", "source_snapshot_ref", "context_revision", "assistance_level",
        "level_source", "display_mode", "overlay_asset_ref", "text_or_question",
        "editable_bounds", "moderation_state", "pipeline_state", "created_at", "approval_ref",
        "child_response", "content_sha256", "content_withheld_reason", "organization_id",
        "session_id", "canvas_id", "group_id", "audience_participant_ids", "analysis_ref",
        "handoff_kind", "cache_source_assistance_id", "generation_job_ref", "producer_ref",
        "generation_evidence_kind", "policy_ref", "status_reason", "etag", "updated_at",
        "contract_name", "contract_version",
    }
    assistance_id = u.proposal(proposal_id).binding.assistance_id
    views = [u.service.device_view(DEVICE_A, assistance_id)]
    assert set(u.service.get_record(TEACHER, proposal_id)) == expected
    u.run(proposal_id)
    assert set(u.service.get_record(TEACHER, proposal_id)) == expected
    views.append(u.service.device_view(DEVICE_A, assistance_id))
    cancel_id = opened(u, assistance_id="assist_fx_002")
    cancel(u, cancel_id)
    views.append(u.service.device_view(DEVICE_A, "assist_fx_002"))
    assert [v["status"] for v in views] == ["pending", "pending", "unavailable"]
    for view in views:
        assert set(view) == {"contract_name", "contract_version", "assistance_id", "status"}


def test_p10_copies_registered_and_purged_by_scope(u: SketchUnitHarness) -> None:
    proposal_id = ready(u)
    scope = f"sketch_proposal:{proposal_id}"
    discovered = u.copies.discover(ORG, scope)
    assert {c.kind for c in discovered} == {"input", "job", "output"}
    purged = u.copies.purge_scope(ORG, scope, "purge_key_fx")
    assert not any(c.actual_deletion_proven for c in purged)
    assert {c.report_label for c in purged} >= {"fixture_deleted_not_actual", "pending"}
    replay = u.copies.purge_scope(ORG, scope, "purge_key_fx")
    assert replay == purged
    assert len(u.copy_adapter.purge_requests) == len(purged)


# ------------------------------------------------------------------ open refusals
@pytest.mark.parametrize("code", list(HandoffRefusalCode))
def test_n01_n03_refused_handoff_creates_no_record(u: SketchUnitHarness,
                                                   code: HandoffRefusalCode) -> None:
    u.handoffs.handoffs[(ORG, "assist_fx_refused")] = HandoffRefusal(code)
    result = u.service.open_from_handoff(ORG, "assist_fx_refused")
    assert (result.outcome, result.code, result.proposal_id) == (OpenOutcome.REFUSED, str(code),
                                                                 None)
    snapshot = u.store.snapshot()
    assert snapshot.proposals == {} and events(u) == ["sketch.open_refused"]
    assert snapshot.events[0].reason == str(code) and not u.job_store.snapshot().jobs


def test_n03_unknown_or_foreign_assistance_is_unreadable(u: SketchUnitHarness) -> None:
    binding = u.add(make_binding())
    assert u.service.open_from_handoff("org_fx_school_b", binding.assistance_id).code == (
        "HANDOFF_UNREADABLE")
    assert u.service.open_from_handoff(ORG, "assist_fx_missing").code == "HANDOFF_UNREADABLE"


@pytest.mark.parametrize("field_name", ["analysis_id", "analysis_revision", "request_revision"])
def test_n02_hint_mismatch_is_refused(u: SketchUnitHarness, field_name: str) -> None:
    binding = u.add(make_binding())
    hint = HandoffHint("intent_fx_1", binding.assistance_id, 1, binding.analysis_id, 1)
    if field_name == "analysis_id":
        hint = replace(hint, analysis_id="analysis_fx_other")
    elif field_name == "analysis_revision":
        hint = replace(hint, analysis_revision=2)
    else:
        hint = replace(hint, request_revision=2)
    u.service.add_hint(ORG, hint)
    (result,) = u.service.process_inbox(ORG)
    assert (result.outcome, result.code) == (OpenOutcome.REFUSED, "HANDOFF_MISMATCH")
    assert u.store.snapshot().proposals == {}


@pytest.mark.parametrize(("changes", "reason"), [
    ({"analysis_accepted": False}, StatusReason.ANALYSIS_NOT_APPLICABLE),
    ({"meaning": MeaningBasis("not_applicable", None, ())},
     StatusReason.ANALYSIS_NOT_APPLICABLE),
    ({"consent_ok": False}, StatusReason.CONSENT_REVOKED),
])
def test_n04_not_applicable_analysis_opens_stale_without_job(
    u: SketchUnitHarness, changes: dict[str, object], reason: StatusReason
) -> None:
    binding = u.add(make_binding())
    u.handoffs.set_current(binding.assistance_id, **changes)
    result = u.service.open_from_handoff(ORG, binding.assistance_id)
    assert result.outcome is OpenOutcome.CREATED and result.code == str(reason)
    assert result.proposal_id is not None
    proposal = u.proposal(result.proposal_id)
    assert (proposal.current.pipeline_state, proposal.current.status_reason) == (
        PipelineState.STALE, reason)
    assert not u.job_store.snapshot().jobs and not u.generator.requests


@pytest.mark.parametrize(("policy", "level", "reason"), [
    (None, LEVEL_2, StatusReason.POLICY_UNRESOLVED),
    (fixture_sketch_policy(enabled=False), LEVEL_2, StatusReason.POLICY_DISABLED),
    (fixture_sketch_policy(), "level_fx_9", StatusReason.LEVEL_NOT_ALLOWED),
    (fixture_sketch_policy(purpose_code="other_purpose"), LEVEL_2,
     StatusReason.POLICY_UNRESOLVED),
])
def test_n05_n24b_policy_refusals_fail_without_job(policy: object, level: str,
                                                    reason: StatusReason) -> None:
    u = build_sketch_unit_harness()
    u.policy.snapshot = policy  # type: ignore[assignment]
    result = u.open(make_binding(level=level))
    assert result.proposal_id is not None and result.code == str(reason)
    proposal = u.proposal(result.proposal_id)
    assert (proposal.current.pipeline_state, proposal.current.status_reason) == (
        PipelineState.FAILED, reason)
    assert proposal.current.level == level and not u.job_store.snapshot().jobs
    assert events(u) == ["sketch.failed"]


# ------------------------------------------------------------------ worker gates
def test_n08_record_generation_refuses_before_provider(u: SketchUnitHarness) -> None:
    proposal_id = opened(u)
    job_id = u.proposal(proposal_id).current.job_id
    assert job_id is not None
    attempt = u.job_store.snapshot().jobs[job_id].active_attempt.attempt_id
    with pytest.raises(SketchError):
        u.service.record_generation("job_fx_missing", "att", correlation_id="c")
    queued = u.service.record_generation(job_id, attempt, correlation_id="c")  # not running
    assert not queued.success and queued.failure_code == "PROVIDER_ERROR"
    u.jobs.dispatch_outbox()
    envelope = u.queue.receive()
    assert envelope is not None
    assert u.jobs.start_attempt(envelope.capability, job_id, attempt).started
    wrong_attempt = u.service.record_generation(job_id, "att_fx_other", correlation_id="c")
    assert not wrong_attempt.success
    # Store-level divergence of the version digest (job request_ref no longer matches).
    with u.store.transaction() as tx:
        current = tx.get(proposal_id)
        assert current is not None
        diverged = replace(current, record_version=current.record_version + 1,
                           versions=(replace(current.current, generation_digest="0" * 64),))
        tx.cas(expected_record_version=current.record_version, proposal=diverged)
    assert not u.service.record_generation(job_id, attempt, correlation_id="c").success
    # Another job type over the same proposal id never reaches the generator.
    other = u.jobs.create_job(CreateJobCommand(
        principal=TEACHER, idempotency_key="key_fx_other", job_type="vision_analysis",
        target_id=proposal_id, purpose_code="ai_drawing_assistance", session_id=SESSION,
        subject_refs=(CHILD_A,), request_ref=RequestRef(proposal_id, 1, "1" * 64, 3),
        correlation_id="corr_fx_other"))
    other_attempt = u.job_store.snapshot().jobs[other.job_id].active_attempt.attempt_id
    assert not u.service.record_generation(other.job_id, other_attempt,
                                           correlation_id="c").success
    assert not u.generator.requests and not u.store.snapshot().staged


def test_n08_cancelled_proposal_refuses_after_start(u: SketchUnitHarness) -> None:
    proposal_id = opened(u)
    u.jobs.dispatch_outbox()
    envelope = u.queue.receive()
    assert envelope is not None
    message = envelope.message
    assert u.jobs.start_attempt(envelope.capability, message.job_id, message.attempt_id).started
    with u.store.transaction() as tx:
        proposal = tx.get(proposal_id)
        assert proposal is not None
    cancel(u, proposal_id)
    claim = u.service.record_generation(message.job_id, message.attempt_id, correlation_id="c")
    assert not claim.success and not u.generator.requests


def malformed(request: GenerationRequest) -> GenerationSucceeded:
    return GenerationSucceeded((OutputPart("canvas_operations", text="draw"),), False,
                               "fake-sketch-generator", request.generator_profile_ref,
                               "fixture-config-v0", "fixture")


def test_n11_malformed_output_fails_without_staging(u: SketchUnitHarness) -> None:
    u.generator.script = malformed
    proposal_id = opened(u)
    proposal = u.run(proposal_id)
    assert (proposal.current.pipeline_state, proposal.current.status_reason) == (
        PipelineState.FAILED, StatusReason.OUTPUT_MALFORMED)
    assert not u.store.snapshot().staged
    job = u.job_store.snapshot().jobs[proposal.current.job_id or ""]
    assert job.state is JobState.FAILED_EXHAUSTED


def test_admission_refusal_is_output_malformed(u: SketchUnitHarness) -> None:
    u.admission.refuse_next = "SIGNATURE_MISMATCH"
    proposal = u.run(opened(u))
    assert proposal.current.status_reason is StatusReason.OUTPUT_MALFORMED


def test_unknown_provider_failure_code_is_mapped(u: SketchUnitHarness) -> None:
    u.generator.script = lambda r: GenerationFailed("VENDOR_SPECIFIC", False, True)
    proposal = u.run(opened(u))
    assert proposal.current.status_reason is StatusReason.PROVIDER_ERROR


# ------------------------------------------------------------------ cancel
def test_n15_cancel_receipts_and_preconditions(u: SketchUnitHarness) -> None:
    proposal_id = opened(u)
    stale_etag = u.proposal(proposal_id).etag()
    with pytest.raises(SketchError) as missing_key:
        cancel(u, proposal_id, key=None)
    assert missing_key.value.http_status == 400
    with pytest.raises(SketchError) as missing_match:
        cancel(u, proposal_id, if_match=None)
    assert missing_match.value.http_status == 428
    with pytest.raises(SketchError) as wrong_match:
        cancel(u, proposal_id, if_match='"sketch-proposal:other:1:1"')
    assert wrong_match.value.http_status == 412
    first = cancel(u, proposal_id)
    replay = cancel(u, proposal_id, if_match=stale_etag)
    assert first.replayed is False and replay.replayed is True  # type: ignore[attr-defined]
    with pytest.raises(SketchError) as mismatch:
        cancel(u, proposal_id, if_match=stale_etag, reason="OTHER_REASON")
    assert mismatch.value.http_status == 409
    proposal = u.proposal(proposal_id)
    assert proposal.current.pipeline_state is PipelineState.CANCELLED
    job = u.job_store.snapshot().jobs[proposal.current.job_id or ""]
    assert job.state is JobState.CANCELLED
    assert u.work_once() is None or not u.generator.requests
    assert not u.generator.requests


def test_cancel_receipt_replay_requires_current_authorization(u: SketchUnitHarness) -> None:
    proposal_id = opened(u)
    command = CancelCommand(TEACHER, proposal_id, "key_fx_replay_auth",
                            u.proposal(proposal_id).etag())
    assert u.service.cancel(command).replayed is False
    u.authority.teachers.pop(TEACHER.principal_id)
    with pytest.raises(SketchError) as denied:
        u.service.cancel(command)
    assert denied.value.code == "RESOURCE_NOT_FOUND"


def test_revision_receipt_replay_requires_current_authorization(u: SketchUnitHarness) -> None:
    proposal_id = ready(u, LEVEL)
    command = ReviseLevelCommand(TEACHER, proposal_id, "key_fx_revision_auth",
                                 u.proposal(proposal_id).etag(), LEVEL_2)
    assert u.service.revise_level(command).replayed is False
    u.authority.teachers.pop(TEACHER.principal_id)
    with pytest.raises(SketchError) as denied:
        u.service.revise_level(command)
    assert denied.value.code == "RESOURCE_NOT_FOUND"


def test_n16_cancel_after_pending_and_child_cancel(u: SketchUnitHarness) -> None:
    proposal_id = ready(u)
    with pytest.raises(SketchError) as pending:
        cancel(u, proposal_id)
    assert pending.value.code == "INVALID_STATE"
    other = opened(u, assistance_id="assist_fx_002")
    with pytest.raises(SketchError) as child:
        cancel(u, other, principal=DEVICE_A, key="key_fx_c2")
    assert child.value.code == "FORBIDDEN_SCOPE"


def test_n17_child_and_other_class_never_see_content(u: SketchUnitHarness) -> None:
    proposal_id = ready(u)
    child_errors = []
    for target in (proposal_id, "sketch_fx9999"):
        with pytest.raises(SketchError) as child:
            u.service.get_record(DEVICE_A, target)
        child_errors.append((child.value.code, child.value.http_status))
    assert child_errors == [("RESOURCE_NOT_FOUND", 404), ("RESOURCE_NOT_FOUND", 404)]
    for principal in (OTHER_CLASS_TEACHER, OUTSIDER):
        with pytest.raises(SketchError) as hidden:
            u.service.get_record(principal, proposal_id)
        assert hidden.value.code == "RESOURCE_NOT_FOUND"
    view = u.service.device_view(DEVICE_A, u.proposal(proposal_id).binding.assistance_id)
    assert view["status"] == "pending" and "text_or_question" not in view
    stranger = Principal("device_fx_gb", ORG, PrincipalRole.DEVICE)
    with pytest.raises(SketchError):
        u.service.device_view(stranger, u.proposal(proposal_id).binding.assistance_id)


# ------------------------------------------------------------------ revise
def test_n20_revise_level_refusals_and_replay(u: SketchUnitHarness) -> None:
    proposal_id = ready(u, LEVEL)
    requested = opened(u, LEVEL, assistance_id="assist_fx_002")
    with pytest.raises(SketchError) as wrong_state:
        revise(u, requested, key="key_fx_r0")
    assert wrong_state.value.code == "INVALID_STATE"
    v1_etag = u.proposal(proposal_id).etag()
    with pytest.raises(SketchError) as no_rule:
        revise(u, proposal_id, "level_fx_9", key="key_fx_r9")
    assert no_rule.value.http_status == 422
    first = revise(u, proposal_id, LEVEL_2)
    replay = revise(u, proposal_id, LEVEL_2, if_match=v1_etag)
    assert replay.replayed and replay.proposal_version == 2  # type: ignore[attr-defined]
    assert first.proposal_version == 2 and len(u.proposal(proposal_id).versions) == 2  # type: ignore[attr-defined]
    with pytest.raises(SketchError) as mismatch:
        revise(u, proposal_id, LEVEL, if_match=v1_etag)
    assert mismatch.value.http_status == 409
    u.run(proposal_id)
    with pytest.raises(SketchError) as old_etag:
        revise(u, proposal_id, LEVEL, key="key_fx_r2", if_match=v1_etag)
    assert old_etag.value.http_status == 412
    cancel(u, requested, key="key_fx_cx")
    with pytest.raises(SketchError) as cancelled:
        revise(u, requested, key="key_fx_r3")
    assert cancelled.value.code == "INVALID_STATE"


# ------------------------------------------------------------------ notices / currency
def test_n21_owner_notice_matching_nonmatching_and_repeat(u: SketchUnitHarness) -> None:
    proposal_id = ready(u)
    untouched = opened(u, assistance_id="assist_fx_group", audience=(CHILD_B,))
    notice = OwnerNotice("notice_fx_1", ORG, NoticeKind.CONSENT_REVOKED, participant_id=CHILD_A)
    assert u.service.apply_owner_notice(notice) == (proposal_id,)
    proposal = u.proposal(proposal_id)
    assert (proposal.current.pipeline_state, proposal.current.status_reason) == (
        PipelineState.STALE, StatusReason.CONSENT_REVOKED)
    assert proposal.review_revision == 2
    assert u.proposal(untouched).current.pipeline_state is PipelineState.REQUESTED
    assert u.service.apply_owner_notice(notice) == ()
    session = OwnerNotice("notice_fx_2", ORG, NoticeKind.SESSION_ENDED, session_id="other")
    assert u.service.apply_owner_notice(session) == ()


def test_n23_read_withholds_stale_content_without_mutation(u: SketchUnitHarness) -> None:
    proposal_id = ready(u)
    full = u.service.get_record(TEACHER, proposal_id)
    assert full["text_or_question"] is not None and full["content_withheld_reason"] is None
    before = u.proposal(proposal_id)
    u.handoffs.set_current(before.binding.assistance_id, consent_ok=False)
    withheld = u.service.get_record(TEACHER, proposal_id)
    assert withheld["text_or_question"] is None and withheld["overlay_asset_ref"] is None
    assert withheld["content_withheld_reason"] == "CONSENT_REVOKED"
    assert u.proposal(proposal_id) == before  # read never mutates
    assert u.store.snapshot().revalidations == [proposal_id]
    after = u.service.revalidate(proposal_id)
    assert after is not None and after.current.pipeline_state is PipelineState.STALE
    assert after.review_revision == before.review_revision + 1


def test_n24_open_uses_requested_level_and_reopen_keeps_revision(u: SketchUnitHarness) -> None:
    proposal_id = ready(u, LEVEL)
    v1 = u.proposal(proposal_id).versions[0]
    assert (v1.level, v1.level_source) == (LEVEL, LevelSource.REQUEST)
    revise(u, proposal_id, LEVEL_2)
    again = u.service.open_from_handoff(ORG, u.proposal(proposal_id).binding.assistance_id)
    assert (again.outcome, again.proposal_id) == (OpenOutcome.REPLAYED, proposal_id)
    current = u.proposal(proposal_id)
    assert len(current.versions) == 2 and current.current.level == LEVEL_2


def test_unsafe_staged_generation_reports_unsafe_claim(u: SketchUnitHarness) -> None:
    u.generator.script = lambda r: default_outcome(r, unsafe=True)
    proposal = u.run(opened(u))
    assert proposal.current.pipeline_state is PipelineState.BLOCKED_UNSAFE
    assert proposal.current.moderation_state is ModerationState.BLOCKED
    (staged,) = u.store.snapshot().staged.values()
    assert staged.status is StagedStatus.SUPERSEDED
    assert set(staged.refs()) <= set(u.artifacts.quarantined)


def test_decision_unresolved_after_two_changed_rounds(u: SketchUnitHarness) -> None:
    binding = u.add(make_binding())

    def bump() -> None:
        u.decision.bump(f"org:{ORG}")
        u.handoffs.after_current = bump

    u.handoffs.after_current = bump
    result = u.service.open_from_handoff(ORG, binding.assistance_id)
    assert result.outcome is OpenOutcome.UNRESOLVED and u.store.snapshot().proposals == {}
    u.handoffs.after_current = None
    assert u.service.open_from_handoff(ORG, binding.assistance_id).outcome is OpenOutcome.CREATED
