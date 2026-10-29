"""BE2-02 C1 application tests over the synthetic fixture world (V02–V11, V15)."""

from __future__ import annotations

from dataclasses import fields, replace
from typing import Any

import pytest

from sketch2life.application.ports.vision_analysis import (
    ObservationFailed,
    ObservationFailureCode,
)
from sketch2life.application.services.vision_analysis import (
    CorrectionResult,
    InvalidationNotice,
    MeaningState,
    ObservationDisposition,
    VisionAnalysisError,
)
from sketch2life.domain.ai_jobs.model import JobState
from sketch2life.domain.vision_analysis import (
    AcceptedStatus,
    CorrectionKind,
    InvalidationReason,
    ProviderContextMode,
)
from sketch2life.infrastructure.vision_analysis.fakes import (
    DeviceBinding,
    FakeVisionObservationProvider,
    synthetic_observation,
    synthetic_success,
)
from sketch2life.infrastructure.vision_analysis.harness import (
    ADMIN,
    CANVAS,
    CHILD_A,
    CHILD_B,
    DEVICE_A,
    DEVICE_B,
    DEVICE_OTHER_CANVAS,
    ORG,
    OTHER_CLASS_TEACHER,
    OUTSIDER,
    PURPOSE,
    SESSION,
    TEACHER,
    AnalysisHarness,
    build_analysis_harness,
    synthetic_admission,
    synthetic_snapshot,
)


@pytest.fixture
def h() -> AnalysisHarness:
    return build_analysis_harness()


def _provider(h: AnalysisHarness) -> FakeVisionObservationProvider:
    assert isinstance(h.provider, FakeVisionObservationProvider)
    return h.provider


def _error(fn: object, *args: object) -> VisionAnalysisError:
    with pytest.raises(VisionAnalysisError) as exc:
        fn(*args)  # type: ignore[operator]
    return exc.value


def _state_counts(h: AnalysisHarness) -> tuple[int, int, int, int]:
    state = h.store.snapshot()
    return (len(state.heads), len(state.corrections), len(state.receipts),
            len(state.invalidations))


# ---------------------------------------------------------------- V02 / V03
def test_v03_valid_snapshot_yields_traceable_uncertain_candidate(h: AnalysisHarness) -> None:
    _provider(h).observation = synthetic_observation(
        (("ent-1", "cat", 0.12), ("ent-2", "house", None))
    )
    result = h.observe()
    assert result.disposition is ObservationDisposition.ACCEPTED and result.authoritative
    meaning = h.service.downstream_meaning(TEACHER, result.analysis_id or "")
    # Low and unknown confidence stay candidates; nothing is promoted to the child's intent.
    assert meaning.state is MeaningState.UNCONFIRMED
    assert meaning.confirmed_concepts == ()
    assert [(c.label, c.confidence) for c in meaning.model_candidates] == [
        ("cat", 0.12), ("house", None)]
    record = h.service.analysis_record(TEACHER, result.analysis_id or "")
    candidate = record["candidate"]
    assert isinstance(candidate, dict)
    assert candidate["uncertainty"]["unknown_confidence_refs"] == ["ent-2"]
    kinds = {ref["kind"]: ref["sha256"] for ref in candidate["evidence_refs"]}
    assert kinds["source_checkpoint"] == h.snapshot.checkpoint.checksum_sha256
    assert kinds["source_render"] == h.snapshot.render.render_sha256
    assert kinds["admission_receipt"] == h.receipt.receipt_sha256
    assert len(set(kinds.values())) == 5


@pytest.mark.parametrize(
    ("mutate", "code"),
    [
        (lambda h: h.sources.snapshots.clear(), "SOURCE_NOT_FOUND"),
        (lambda h: h.admission.clear(), "ADMISSION_MISSING"),
        (lambda h: h.admission.add(synthetic_admission(h.snapshot, decision="RECAPTURE"),
                                   organization_id=ORG), "ADMISSION_NOT_PASSED"),
        (lambda h: h.sources.add(replace(h.snapshot, render=replace(
            h.snapshot.render, source_checkpoint_id="checkpoint_fx_999"))),
         "RENDER_NOT_DERIVED_FROM_CHECKPOINT"),
        (lambda h: h.sources.add(replace(h.snapshot, checkpoint=replace(
            h.snapshot.checkpoint, canvas_id="canvas_fx_009"))), "CHECKPOINT_CANVAS_MISMATCH"),
    ],
)
def test_v02_wrong_or_missing_binding_calls_no_provider_and_stores_nothing(
    h: AnalysisHarness, mutate: object, code: str
) -> None:
    mutate(h)  # type: ignore[operator]
    result = h.observe()
    assert result.disposition is ObservationDisposition.REFUSED
    assert result.code == code and not result.provider_invoked
    assert _provider(h).requests == []
    assert _state_counts(h) == (0, 0, 0, 0)


def test_v02_admission_bound_to_another_render_is_not_accepted(h: AnalysisHarness) -> None:
    other = synthetic_snapshot(render_sha256="e" * 64)
    h.admission.clear()
    h.admission.add(synthetic_admission(other), organization_id=ORG)
    result = h.observe()
    assert result.code == "ADMISSION_MISSING" and _provider(h).requests == []


def test_v02_v07_input_hash_must_bind_the_resolved_source(h: AnalysisHarness) -> None:
    h.set_job(input_hash="f" * 64)
    result = h.observe()
    assert result.disposition is ObservationDisposition.REJECTED
    assert result.code == "INPUT_MISMATCH" and _provider(h).requests == []


# ---------------------------------------------------------------------- V07
@pytest.mark.parametrize(
    ("job_changes", "claim_changes", "code"),
    [
        ({"state": JobState.CANCELLED}, {}, "JOB_CANCELLED"),
        ({"state": JobState.SUCCEEDED}, {}, "JOB_TERMINAL"),
        ({"active_attempt_id": "att_fx0002"}, {}, "ATTEMPT_SUPERSEDED"),
        ({"state": JobState.QUEUED}, {}, "INVALID_STATE"),
        ({"job_type": "sketch_assistance"}, {}, "JOB_TYPE_MISMATCH"),
        ({}, {"expected_request_revision": 2}, "REQUEST_MISMATCH"),
        ({}, {"input_snapshot_ref": "snapshot_fx_999"}, "REQUEST_MISMATCH"),
        ({}, {"job_id": "job_fx0404"}, "JOB_NOT_FOUND"),
    ],
)
def test_v07_wrong_lineage_never_creates_an_authoritative_analysis(
    h: AnalysisHarness, job_changes: dict[str, Any], claim_changes: dict[str, Any],
    code: str,
) -> None:
    h.set_job(**job_changes)
    result = h.observe(h.claim(**claim_changes))
    assert result.disposition is ObservationDisposition.REJECTED and result.code == code
    assert not result.authoritative and _provider(h).requests == []
    assert _state_counts(h) == (0, 0, 0, 0)


def test_v07_cancel_or_supersede_during_provider_call_discards_result(
    h: AnalysisHarness,
) -> None:
    _provider(h).on_observe = lambda: h.set_job(state=JobState.CANCELLED)
    result = h.observe()
    assert result.disposition is ObservationDisposition.REJECTED
    assert result.code == "JOB_CANCELLED" and result.provider_invoked
    assert _state_counts(h) == (0, 0, 0, 0)
    h2 = build_analysis_harness()
    _provider(h2).on_observe = lambda: h2.set_job(active_attempt_id="att_fx0002")
    assert h2.observe().code == "ATTEMPT_SUPERSEDED"


def test_v05_v07_consent_revoked_during_provider_call_discards_result(
    h: AnalysisHarness,
) -> None:
    _provider(h).on_observe = lambda: h.context.revoke_consent(CHILD_A)
    result = h.observe()
    assert result.disposition is ObservationDisposition.REJECTED
    assert result.code == "CONSENT_REQUIRED" and result.provider_invoked
    assert _state_counts(h) == (0, 0, 0, 0)


def test_v07_same_attempt_replays_without_a_second_provider_call(h: AnalysisHarness) -> None:
    first = h.observe()
    again = h.observe()
    assert again.replayed and again.analysis_id == first.analysis_id
    assert len(_provider(h).requests) == 1


# ---------------------------------------------------------------------- V06
def test_v06_context_change_in_flight_stores_pinned_original_as_stale(
    h: AnalysisHarness,
) -> None:
    _provider(h).on_observe = lambda: h.context.bump(SESSION, CANVAS)
    result = h.observe()
    assert result.disposition is ObservationDisposition.STALE and not result.authoritative
    assert result.code == "context_changed"
    analysis_id = result.analysis_id or ""
    with h.store.transaction() as tx:
        head = tx.get_head(analysis_id)
    assert head is not None and head.context_revision == 3
    assert head.source == h.snapshot
    meaning = h.service.downstream_meaning(TEACHER, analysis_id)
    assert meaning.state is MeaningState.NOT_APPLICABLE
    error = _error(h.service.submit_correction,
                   h.correction(TEACHER, analysis_id, context_revision=4))
    assert error.code == "STALE_CONTEXT"


def test_v06_snapshot_change_in_flight_is_stale(h: AnalysisHarness) -> None:
    moved = synthetic_snapshot(render_sha256="9" * 64)
    _provider(h).on_observe = lambda: h.sources.add(moved)
    result = h.observe()
    assert result.disposition is ObservationDisposition.STALE
    assert result.code == "source_changed"


def test_v06_at_cs_008_newer_confirmed_meaning_is_not_overwritten(h: AnalysisHarness) -> None:
    first = h.accepted_analysis()
    # The child immediately changes the drawing and intention: new context, snapshot, request.
    h.context.bump(SESSION, CANVAS)
    moved = synthetic_snapshot(ref="snapshot_fx_002", render_sha256="7" * 64)
    h.sources.add(moved)
    h.admission.add(synthetic_admission(moved), organization_id=ORG)
    h.pin = replace(h.pin, request_revision=2, input_snapshot_ref=moved.snapshot_ref,
                    context_revision=4)
    h.requests.add(h.pin)
    h.snapshot = moved
    h.set_job(job_id="job_fx0002", attempt_id="att_fx0101")
    second = h.observe(h.claim(job_id="job_fx0002", attempt_id="att_fx0101"))
    assert second.authoritative and second.analysis_id != first
    second_id = second.analysis_id or ""
    h.service.submit_correction(h.correction(TEACHER, second_id, context_revision=4))
    # A late result for the old request revision is rejected, never rebound to the new one.
    late = h.observe(h.claim(expected_request_revision=1, input_snapshot_ref="snapshot_fx_001",
                             context_revision=3))
    assert late.disposition is ObservationDisposition.REJECTED
    assert late.code == "REQUEST_MISMATCH" and not late.authoritative
    # The old analysis cannot take a correction that would compete with the new meaning.
    stale = _error(h.service.submit_correction,
                   h.correction(TEACHER, first, intended=("cat",), context_revision=4))
    assert stale.code == "STALE_CONTEXT"
    assert h.service.downstream_meaning(TEACHER, first).state is MeaningState.NOT_APPLICABLE
    current = h.service.downstream_meaning(TEACHER, second_id)
    assert current.state is MeaningState.CONFIRMED and current.confirmed_concepts == ("tiger",)


# ---------------------------------------------------------------- V04 / V11
def test_v04_cat_child_tiger_teacher_confirmation_keeps_cat_and_authors(
    h: AnalysisHarness,
) -> None:
    analysis_id = h.accepted_analysis()
    before = h.service.analysis_record(TEACHER, analysis_id)
    proposal = h.service.submit_correction(
        h.correction(DEVICE_A, analysis_id, explanation="It has stripes and a long tail")
    )
    assert proposal.correction.kind is CorrectionKind.CHILD_PROPOSAL
    assert h.service.downstream_meaning(TEACHER, analysis_id).state is MeaningState.UNCONFIRMED
    confirmation = h.service.submit_correction(
        h.correction(TEACHER, analysis_id, revision=2, basis=proposal.correction.correction_id,
                     reason="Teacher confirms the child's tiger")
    )
    meaning = h.service.downstream_meaning(TEACHER, analysis_id)
    assert meaning.state is MeaningState.CONFIRMED and meaning.confirmed_concepts == ("tiger",)
    assert meaning.model_candidates[0].label == "cat"
    after = h.service.analysis_record(TEACHER, analysis_id)
    assert after["original_observation"] == before["original_observation"]
    assert after["observation_sha256"] == before["observation_sha256"]
    corrections = after["corrections"]
    assert isinstance(corrections, list)
    authors = [(c["kind"], c["author"]["role"], c["author"]["principal_ref"]) for c in corrections]
    assert authors == [("child_proposal", "child_device", DEVICE_A.principal_id),
                       ("teacher_confirmation", "teacher", TEACHER.principal_id)]
    assert corrections[0]["author"]["participant_id"] == CHILD_A
    assert corrections[1]["basis_correction_ref"] == proposal.correction.correction_id
    assert confirmation.receipt.current_meaning_ref_after == confirmation.correction.correction_id


def test_v11_corrections_emit_versioned_invalidation_and_no_teacher_review(
    h: AnalysisHarness,
) -> None:
    analysis_id = h.accepted_analysis()
    h.service.submit_correction(h.correction(DEVICE_A, analysis_id))
    h.service.submit_correction(h.correction(TEACHER, analysis_id, revision=2))
    intents = h.store.invalidations()
    assert [(i.previous_revision, i.analysis_revision, str(i.reason)) for i in intents] == [
        (1, 2, "child_intent_proposed"), (2, 3, "teacher_meaning_confirmed")]
    assert len({i.event_id for i in intents}) == 2
    state = h.store.snapshot()
    # Only meaning records exist: no review/approval record of any kind was fabricated.
    assert set(vars(state)) == {"heads", "observations", "provider_results", "attempts",
                                "corrections",
                                "correction_order", "receipts", "invalidations",
                                "invalidation_order", "notices"}
    record = h.service.analysis_record(TEACHER, analysis_id)
    assert "review_ref" not in str(record) and "approved" not in str(record)


def test_v11_owner_invalidation_is_idempotent_and_keeps_history(h: AnalysisHarness) -> None:
    analysis_id = h.accepted_analysis()
    h.service.submit_correction(h.correction(TEACHER, analysis_id))
    notice = InvalidationNotice("notice_fx_7", ORG, analysis_id,
                                InvalidationReason.SOURCE_CHANGED)
    intent = h.service.apply_invalidation(notice)
    assert intent is not None and intent.analysis_revision == 3
    assert h.service.apply_invalidation(notice) is None
    with h.store.transaction() as tx:
        head = tx.get_head(analysis_id)
        corrections = tx.list_corrections(analysis_id)
    assert head is not None and head.accepted_status is AcceptedStatus.STALE
    assert len(corrections) == 1 and head.current_meaning_ref == corrections[0].correction_id


# ---------------------------------------------------------------------- V05
@pytest.mark.parametrize(
    ("principal", "code"),
    [
        (OUTSIDER, "RESOURCE_NOT_FOUND"),
        (OTHER_CLASS_TEACHER, "RESOURCE_NOT_FOUND"),
        (DEVICE_B, "RESOURCE_NOT_FOUND"),
        (DEVICE_OTHER_CANVAS, "RESOURCE_NOT_FOUND"),
        (ADMIN, "RESOURCE_NOT_FOUND"),
    ],
)
def test_v05_out_of_scope_principals_are_denied_and_concealed(
    h: AnalysisHarness, principal: object, code: str
) -> None:
    analysis_id = h.accepted_analysis()
    error = _error(h.service.submit_correction, h.correction(principal, analysis_id))  # type: ignore[arg-type]
    assert error.code == code
    assert _state_counts(h)[1:] == (0, 0, 0)


def test_v05_wrong_group_and_closed_or_unbound_turn_are_denied(h: AnalysisHarness) -> None:
    analysis_id = h.accepted_analysis()
    h.authority.bind_device(DEVICE_A.principal_id,
                            DeviceBinding(ORG, SESSION, CANVAS, "group_fx_2", CHILD_A, "turn_x"))
    assert _error(h.service.submit_correction,
                  h.correction(DEVICE_A, analysis_id)).code == "RESOURCE_NOT_FOUND"
    h.authority.bind_device(DEVICE_A.principal_id,
                            DeviceBinding(ORG, SESSION, CANVAS, None, CHILD_A, None))
    assert _error(h.service.submit_correction,
                  h.correction(DEVICE_A, analysis_id)).code == "FORBIDDEN_SCOPE"
    h.authority.bind_device(DEVICE_A.principal_id,
                            DeviceBinding(ORG, SESSION, CANVAS, None, CHILD_A, "turn_fx_01"))
    h.authority.close_turn(DEVICE_A.principal_id)
    assert _error(h.service.submit_correction,
                  h.correction(DEVICE_A, analysis_id)).code == "TURN_CLOSED"
    assert _state_counts(h)[1:] == (0, 0, 0)


def test_v05_revoked_grant_purpose_or_consent_is_denied(h: AnalysisHarness) -> None:
    analysis_id = h.accepted_analysis()
    h.authority.revoke(TEACHER.principal_id)
    assert _error(h.service.submit_correction,
                  h.correction(TEACHER, analysis_id)).code == "GRANT_REVOKED"
    h2 = build_analysis_harness()
    analysis_2 = h2.accepted_analysis()
    h2.context.revoke_consent(CHILD_A)
    assert _error(h2.service.submit_correction,
                  h2.correction(TEACHER, analysis_2)).code == "CONSENT_REQUIRED"
    h3 = build_analysis_harness()
    analysis_3 = h3.accepted_analysis()
    h3.context.set_participant(CHILD_A, age_months=60, purposes=frozenset({"other_purpose"}))
    assert _error(h3.service.submit_correction,
                  h3.correction(DEVICE_A, analysis_3)).code == "CONSENT_REQUIRED"


def test_v05_device_cannot_confirm_or_act_as_teacher(h: AnalysisHarness) -> None:
    analysis_id = h.accepted_analysis()
    proposal = h.service.submit_correction(h.correction(DEVICE_A, analysis_id))
    # The verified device principal always records a proposal; basis refs are teacher-only.
    assert proposal.correction.kind is CorrectionKind.CHILD_PROPOSAL
    error = _error(h.service.submit_correction,
                   h.correction(DEVICE_A, analysis_id, revision=2,
                                basis=proposal.correction.correction_id))
    assert error.code == "FIELD_NOT_ALLOWED"
    assert h.service.downstream_meaning(TEACHER, analysis_id).state is MeaningState.UNCONFIRMED
    assert _error(h.service.downstream_meaning, DEVICE_A, analysis_id).code == "FORBIDDEN_SCOPE"


def test_v05_teacher_cannot_author_the_childs_explanation(h: AnalysisHarness) -> None:
    analysis_id = h.accepted_analysis()
    error = _error(h.service.submit_correction,
                   h.correction(TEACHER, analysis_id, explanation="I think it is a tiger"))
    assert error.code == "FIELD_NOT_ALLOWED"


def test_v05_basis_must_be_a_child_proposal_of_the_same_analysis(h: AnalysisHarness) -> None:
    first = h.accepted_analysis()
    confirmation = h.service.submit_correction(h.correction(TEACHER, first))
    error = _error(h.service.submit_correction,
                   h.correction(TEACHER, first, revision=2,
                                basis=confirmation.correction.correction_id))
    assert error.code == "FIELD_VALIDATION_FAILED"
    h.set_job(job_id="job_fx0002", attempt_id="att_fx0201")
    second = h.observe(h.claim(job_id="job_fx0002", attempt_id="att_fx0201")).analysis_id or ""
    proposal = h.service.submit_correction(h.correction(DEVICE_A, second))
    cross = _error(h.service.submit_correction,
                   h.correction(TEACHER, first, revision=2,
                                basis=proposal.correction.correction_id))
    assert cross.code == "FIELD_VALIDATION_FAILED"


# ---------------------------------------------------------------- V08 / V09
def test_v08_same_key_replays_original_and_changed_payload_conflicts(
    h: AnalysisHarness,
) -> None:
    analysis_id = h.accepted_analysis()
    command = h.correction(TEACHER, analysis_id, key="key_fx_same")
    first = h.service.submit_correction(command)
    replay = h.service.submit_correction(command)
    assert replay.replayed and not first.replayed
    assert replay.receipt == first.receipt and replay.correction == first.correction
    assert replay.etag == first.etag
    assert _state_counts(h) == (1, 1, 1, 1)
    changed = replace(command, intended_objects=("lion",))
    assert _error(h.service.submit_correction, changed).code == "IDEMPOTENCY_PAYLOAD_MISMATCH"
    # Omitted and explicit-null explanation fingerprint the same; normalisation too.
    same = replace(command, intended_objects=("  tiger ",))
    assert h.service.submit_correction(same).replayed


def test_v08_key_scope_isolates_principal_and_target(h: AnalysisHarness) -> None:
    analysis_id = h.accepted_analysis()
    h.service.submit_correction(h.correction(DEVICE_A, analysis_id, key="key_fx_shared"))
    teacher = h.service.submit_correction(
        h.correction(TEACHER, analysis_id, revision=2, key="key_fx_shared")
    )
    assert not teacher.replayed and teacher.correction.kind is CorrectionKind.TEACHER_CONFIRMATION
    h.set_job(job_id="job_fx0002", attempt_id="att_fx0301")
    other = h.observe(h.claim(job_id="job_fx0002", attempt_id="att_fx0301")).analysis_id or ""
    on_other = h.service.submit_correction(h.correction(TEACHER, other, key="key_fx_shared"))
    assert not on_other.replayed and on_other.receipt.analysis_id == other


def test_v09_accepted_replay_with_old_if_match_returns_original(h: AnalysisHarness) -> None:
    analysis_id = h.accepted_analysis()
    command = h.correction(DEVICE_A, analysis_id, key="key_fx_old")
    original = h.service.submit_correction(command)
    h.service.submit_correction(h.correction(TEACHER, analysis_id, revision=2))
    h.authority.close_turn(DEVICE_A.principal_id)
    replay = h.service.submit_correction(command)  # old If-Match rev 1, closed turn
    assert replay.replayed and replay.receipt == original.receipt
    assert replay.receipt.analysis_revision_after == 2


def test_v09_revoked_actor_cannot_read_private_receipt(h: AnalysisHarness) -> None:
    analysis_id = h.accepted_analysis()
    command = h.correction(TEACHER, analysis_id, key="key_fx_revoke")
    h.service.submit_correction(command)
    h.authority.revoke(TEACHER.principal_id)
    assert _error(h.service.submit_correction, command).code == "GRANT_REVOKED"
    h2 = build_analysis_harness()
    analysis_2 = h2.accepted_analysis()
    device_command = h2.correction(DEVICE_A, analysis_2, key="key_fx_revoke")
    h2.service.submit_correction(device_command)
    h2.context.revoke_consent(CHILD_A)
    assert _error(h2.service.submit_correction, device_command).code == "CONSENT_REQUIRED"


def test_v09_unseen_command_needs_if_match_of_the_right_family_and_revision(
    h: AnalysisHarness,
) -> None:
    analysis_id = h.accepted_analysis()
    assert _error(h.service.submit_correction,
                  h.correction(TEACHER, analysis_id, revision=None)).code == "PRECONDITION_REQUIRED"
    for header in ('"session:session_fx_001:1"', f'"analysis:{analysis_id}:2"',
                   '"analysis:ana_fx0999:1"', "garbage"):
        error = _error(h.service.submit_correction,
                       h.correction(TEACHER, analysis_id, if_match=header))
        assert error.code == "STALE_AGGREGATE" and error.current_revision == 1
    assert _error(h.service.submit_correction,
                  replace(h.correction(TEACHER, analysis_id), idempotency_key=None)).code == (
        "MALFORMED_REQUEST")
    assert _state_counts(h)[1:] == (0, 0, 0)


# ---------------------------------------------------------------------- V10
def test_v10_two_writers_one_revision_one_cas_winner(h: AnalysisHarness) -> None:
    analysis_id = h.accepted_analysis()
    winner: list[CorrectionResult] = []
    h.context.on_current = lambda: winner.append(
        h.service.submit_correction(h.correction(DEVICE_A, analysis_id, key="key_fx_a"))
    )
    loser = _error(h.service.submit_correction,
                   h.correction(TEACHER, analysis_id, key="key_fx_b"))
    assert loser.code == "STALE_AGGREGATE" and loser.current_revision == 2
    assert len(winner) == 1 and winner[0].receipt.analysis_revision_after == 2
    state = h.store.snapshot()
    assert len(state.corrections) == 1 and len(state.receipts) == 1
    assert len(state.invalidations) == 1
    assert state.heads[analysis_id].analysis_revision == 2


def test_v10_injected_storage_failure_rolls_back_every_staged_effect(
    h: AnalysisHarness,
) -> None:
    analysis_id = h.accepted_analysis()
    before = h.store.snapshot()
    h.store.fail_next_commit = True
    command = h.correction(TEACHER, analysis_id, key="key_fx_fail")
    error = _error(h.service.submit_correction, command)
    assert error.code == "DEPENDENCY_UNAVAILABLE" and error.retryable
    after = h.store.snapshot()
    assert after.heads == before.heads and after.corrections == before.corrections
    assert after.receipts == {} and after.invalidations == {}
    retried = h.service.submit_correction(command)  # no receipt was reserved by the failure
    assert not retried.replayed and retried.receipt.analysis_revision_after == 2


def test_v10_observation_commit_failure_stores_nothing(h: AnalysisHarness) -> None:
    h.store.fail_next_commit = True
    assert _error(h.observe).code == "DEPENDENCY_UNAVAILABLE"
    assert _state_counts(h) == (0, 0, 0, 0)


# ---------------------------------------------------------------------- V15
def test_v15_unsafe_or_malformed_provider_output_stores_nothing(h: AnalysisHarness) -> None:
    _provider(h).scripted = [
        ObservationFailed(ObservationFailureCode.UNSAFE_CONTENT, True,
                          detail="PSYCHOLOGICAL_INFERENCE_CLAIM"),
        ObservationFailed(ObservationFailureCode.OUTPUT_MALFORMED, True),
    ]
    for code in ("UNSAFE_CONTENT", "OUTPUT_MALFORMED"):
        result = h.observe()
        assert result.disposition is ObservationDisposition.FAILED and result.code == code
        assert result.analysis_id is None
    assert _state_counts(h) == (0, 0, 0, 0)


@pytest.mark.parametrize(("age", "allowed"), [(35, False), (36, True), (120, True),
                                              (155, True), (156, False), (None, False)])
def test_v15_authoritative_age_window_not_legacy_under_nine_helper(
    age: int | None, allowed: bool
) -> None:
    h = build_analysis_harness()
    h.context.set_participant(CHILD_A, age_months=age, purposes=frozenset({PURPOSE}))
    result = h.observe()
    assert result.authoritative is allowed
    if not allowed:
        assert result.code == "AGE_NOT_SUPPORTED" and _provider(h).requests == []


def test_v15_group_audience_checks_every_participant_age_and_consent() -> None:
    h = build_analysis_harness()
    group_scope = replace(h.pin.scope, group_id="group_fx_1",
                          audience_participant_ids=(CHILD_A, CHILD_B))
    # The foundation job carries the same audience as subjects (C1-R03 scope mapping).
    h.pin = replace(h.pin, scope=group_scope)
    h.requests.add(h.pin)
    h.set_job()
    assert h.observe().authoritative  # child B is 120 months: allowed by the 36–155 rule
    h2 = build_analysis_harness()
    h2.pin = replace(h2.pin, scope=group_scope)
    h2.requests.add(h2.pin)
    h2.set_job()
    h2.context.revoke_consent(CHILD_B)
    assert h2.observe().code == "CONSENT_REQUIRED"


def test_v15_provider_never_receives_age_or_child_content() -> None:
    h = build_analysis_harness(required_context_mode=ProviderContextMode.TYPED_CONTEXT)
    analysis_id = h.accepted_analysis()
    h.service.submit_correction(h.correction(DEVICE_A, analysis_id, explanation="stripes"))
    (request,) = _provider(h).requests
    assert request.typed_context is not None
    # C2 supersedes the C1 fake-only envelope (context_revision/purpose_code/topic_ref/
    # age_policy_ref) with the pinned minimized projection + opaque binding. The guard stays
    # an exact allowlist: anonymous age bands only, never exact ages, ids or child statements.
    # Actual serialized provider bytes are checked in test_vision_context_adapter.py.
    assert {f.name for f in fields(request.typed_context)} == {"projection", "binding"}
    assert {f.name for f in fields(request.typed_context.projection)} == {
        "context_revision", "teacher_topic", "audience_age_bands", "age_band_policy_ref",
        "age_band_policy_version", "request_reason", "target_kind", "requested_level",
        "source_image_sha256"}
    assert {f.name for f in fields(request.typed_context.binding)} == {
        "context_contract", "context_contract_version", "canonical_rules_version",
        "context_revision", "payload_digest", "context_digest", "age_band_policy_ref",
        "age_band_policy_version"}
    assert {f.name for f in fields(request)} == {
        "correlation_id", "organization_id", "render", "admission", "context_mode",
        "typed_context", "processing_image_ref"}
    projected = repr(request.typed_context)
    assert "stripes" not in repr(request) and "tiger" not in repr(request)
    assert CHILD_A not in projected and "60" not in str(
        request.typed_context.projection.canonical()["audience_age_bands"])


# ---------------------------------------------------------------------- V14
def test_v14_required_typed_context_fails_closed_without_capable_provider() -> None:
    h = build_analysis_harness(
        provider_factory=lambda _s, clock: FakeVisionObservationProvider(
            clock=clock.now, supported=frozenset({ProviderContextMode.IMAGE_ONLY})
        ),
        required_context_mode=ProviderContextMode.TYPED_CONTEXT,
    )
    result = h.observe()
    assert result.disposition is ObservationDisposition.REFUSED
    assert result.code == "CONTEXT_MODE_UNSUPPORTED" and _provider(h).requests == []


def test_v14_provider_reporting_a_different_context_mode_is_malformed() -> None:
    h = build_analysis_harness(required_context_mode=ProviderContextMode.TYPED_CONTEXT)

    def image_only_answer() -> None:
        request = replace(_provider(h).requests[0], context_mode=ProviderContextMode.IMAGE_ONLY,
                          typed_context=None)
        _provider(h).scripted = [synthetic_success(request, executed_at=h.clock.now())]

    _provider(h).on_observe = image_only_answer
    assert h.observe().code == "OUTPUT_MALFORMED"
