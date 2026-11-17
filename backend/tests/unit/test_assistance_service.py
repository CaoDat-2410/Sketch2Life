"""BE2-03 A1.3 service: positive P01–P06 and negative N01–N25 through the real service chain."""

from __future__ import annotations

from dataclasses import replace

import pytest

from sketch2life.application.ports.assistance import ReceiptOutcome
from sketch2life.application.services.assistance import AssistanceError
from sketch2life.domain.assistance import (
    Contributor,
    RequestReason,
    RequestStatus,
    ReservationState,
    StatusReason,
    TargetKind,
    TargetScope,
)
from sketch2life.infrastructure.assistance.fakes import fixture_policy
from sketch2life.infrastructure.assistance.harness import (
    ADMIN,
    CANVAS_G,
    CANVAS_P,
    CHILD_A,
    CHILD_B,
    CHILD_C,
    DEVICE_A,
    DEVICE_GA,
    DEVICE_GB,
    LEVEL_2,
    OTHER_CLASS_TEACHER,
    OUTSIDER,
    TEACHER,
    AssistanceHarness,
    build_assistance_harness,
    make_source,
)


@pytest.fixture
def h() -> AssistanceHarness:
    return build_assistance_harness()


def code(exc: pytest.ExceptionInfo[AssistanceError]) -> str:
    return exc.value.code


def jobs(h: AssistanceHarness) -> dict[str, object]:
    return dict(h.job_store.snapshot().jobs)


def requested_events(h: AssistanceHarness) -> list[str]:
    return [e.event_type for e in h.store.snapshot().events
            if e.event_type == "assistance.requested"]


def refused(h: AssistanceHarness) -> list[str | None]:
    return [e.reason for e in h.store.snapshot().events if e.event_type == "assistance.refused"]


# ------------------------------------------------------------------- positive
def test_p01_child_request_schedules_one_job_and_drawing_continues(h: AssistanceHarness) -> None:
    canvases_before = dict(h.owner.canvases)
    result = h.submit(h.command(intent="a cat"))
    assert result.outcome is ReceiptOutcome.CREATED and not result.replayed
    request = h.request(result.request.assistance_id)
    assert request.status is RequestStatus.SCHEDULED
    assert request.reservation is ReservationState.HELD
    (job,) = jobs(h).values()
    assert job.job_id == request.job_id  # type: ignore[attr-defined]
    assert job.scope.target_id == request.assistance_id  # type: ignore[attr-defined]
    assert job.scope.subject_refs == (CHILD_A,)  # type: ignore[attr-defined]
    assert job.active_attempt.request_ref.input_hash == (  # type: ignore[attr-defined]
        h.source_p.snapshot.input_hash())
    # The request never mutates the canvas and the Child's turn stays open.
    assert h.owner.canvases == canvases_before
    assert h.authority.devices[DEVICE_A.principal_id].turn_open
    assert h.vision_provider.requests == []  # no provider call before a worker runs


def test_p02_teacher_group_request_checks_each_member(h: AssistanceHarness) -> None:
    result = h.submit(h.group_command())
    request = h.request(result.request.assistance_id)
    assert request.audience == (CHILD_A, CHILD_B)
    assert [m.completed_age_months for m in request.facts.members] == [60, 120]
    assert request.contributor == Contributor(CHILD_A, "turn_fx_ga", 1)  # D5 bound turn
    (job,) = jobs(h).values()
    assert sorted(job.scope.subject_refs) == [CHILD_A, CHILD_B]  # type: ignore[attr-defined]


def test_p03_same_key_replay_returns_original_receipt(h: AssistanceHarness) -> None:
    command = h.command()
    first = h.submit(command)
    replay = h.submit(command)
    assert replay.replayed and replay.outcome is ReceiptOutcome.CREATED
    assert replay.request == first.request  # body as committed
    assert len(jobs(h)) == 1
    assert len(requested_events(h)) == 1


def test_p04_different_key_same_semantics_deduplicates_without_cost(
    h: AssistanceHarness,
) -> None:
    first = h.submit(h.command())
    second = h.submit(h.command())
    assert second.outcome is ReceiptOutcome.DEDUPLICATED
    assert second.request.assistance_id == first.request.assistance_id
    assert len(jobs(h)) == 1
    with h.store.transaction() as tx:
        assert tx.count_reserved("org_fx_school_a", "session_fx_001", None) == 1


def test_p06_child_cancels_own_request(h: AssistanceHarness) -> None:
    request = h.submit().request
    result = h.service.cancel(h.cancel_command(DEVICE_A, request.assistance_id))
    assert result.request.status is RequestStatus.CANCELLED
    assert result.request.status_reason is StatusReason.CANCELLED_BY_CHILD
    assert result.request.request_revision == 2


def test_teacher_individual_request_on_turnless_canvas_is_refused(
    h: AssistanceHarness,
) -> None:
    """D5: Teacher contributor needs a bound turn in the audience or a personal owner."""

    del h.owner.turns[CANVAS_G]
    with pytest.raises(AssistanceError) as exc:
        h.submit(h.group_command())
    assert code(exc) == "TURN_CLOSED"
    personal = h.submit(h.command(TEACHER))
    assert h.request(personal.request.assistance_id).contributor.participant_id == CHILD_A


# ------------------------------------------------------------------- negative
def test_n01_child_cannot_target_another_participant_or_group(h: AssistanceHarness) -> None:
    with pytest.raises(AssistanceError) as exc:
        h.submit(h.command(DEVICE_GA, canvas=CANVAS_G,
                           target=TargetScope(TargetKind.INDIVIDUAL, CHILD_B)))
    assert code(exc) == "FORBIDDEN_SCOPE"
    with pytest.raises(AssistanceError) as exc:
        h.submit(h.group_command(DEVICE_GA, reason=RequestReason.CHILD_REQUEST))
    assert code(exc) == "FORBIDDEN_SCOPE"
    assert jobs(h) == {} and requested_events(h) == []


def test_n02_closed_turn_or_revoked_grant(h: AssistanceHarness) -> None:
    h.authority.devices[DEVICE_A.principal_id].turn_open = False
    with pytest.raises(AssistanceError) as exc:
        h.submit()
    assert code(exc) == "TURN_CLOSED"
    h.authority.devices[DEVICE_A.principal_id].turn_open = True
    h.authority.revoked.add(DEVICE_A.principal_id)
    with pytest.raises(AssistanceError) as exc:
        h.submit()
    assert code(exc) == "GRANT_REVOKED"
    assert jobs(h) == {}


@pytest.mark.parametrize("principal", [OTHER_CLASS_TEACHER, OUTSIDER])
def test_n03_other_class_or_school_is_concealed(h: AssistanceHarness, principal: object) -> None:
    with pytest.raises(AssistanceError) as exc:
        h.submit(h.command(principal))  # type: ignore[arg-type]
    assert code(exc) == "RESOURCE_NOT_FOUND"


def test_admin_has_no_request_role(h: AssistanceHarness) -> None:
    with pytest.raises(AssistanceError) as exc:
        h.submit(h.command(ADMIN, reason=RequestReason.TEACHER_REQUEST))
    assert code(exc) == "FORBIDDEN_SCOPE"


def test_n04_one_member_without_consent_refuses_whole_group(h: AssistanceHarness) -> None:
    h.owner.update_member(CHILD_B, consent_effective=False)
    with pytest.raises(AssistanceError) as exc:
        h.submit(h.group_command())
    assert code(exc) == "CONSENT_REQUIRED"
    h.owner.update_member(CHILD_B, consent_effective=True, purposes=frozenset())
    with pytest.raises(AssistanceError) as exc:
        h.submit(h.group_command())
    assert code(exc) == "CONSENT_REQUIRED"
    assert jobs(h) == {} and requested_events(h) == []
    assert h.vision_provider.requests == []


@pytest.mark.parametrize(("child", "months"), [(CHILD_B, 156), (CHILD_B, None), (CHILD_A, 35)])
def test_n05_each_member_age_is_checked_without_averaging(
    h: AssistanceHarness, child: str, months: int | None
) -> None:
    h.set_age(child, months)
    with pytest.raises(AssistanceError) as exc:
        h.submit(h.group_command())
    assert code(exc) == "AGE_NOT_SUPPORTED"
    assert jobs(h) == {}


def test_n06_duplicate_roster_member_is_refused(h: AssistanceHarness) -> None:
    h.owner.duplicate_roster = True
    with pytest.raises(AssistanceError) as exc:
        h.submit(h.group_command())
    assert code(exc) == "DEPENDENCY_UNAVAILABLE"
    assert jobs(h) == {}


def test_n07_same_key_changed_payload_conflicts(h: AssistanceHarness) -> None:
    h.submit(h.command(key="key_fixed"))
    with pytest.raises(AssistanceError) as exc:
        h.submit(h.command(key="key_fixed", level=LEVEL_2))
    assert code(exc) == "IDEMPOTENCY_PAYLOAD_MISMATCH"
    assert len(jobs(h)) == 1


def test_n08_stale_context_checkpoint_or_admission(h: AssistanceHarness) -> None:
    with pytest.raises(AssistanceError) as exc:
        h.submit(h.command(context=2))
    assert code(exc) == "STALE_CONTEXT"
    other, _ = make_source(CANVAS_P, "fx_unknown")
    with pytest.raises(AssistanceError) as exc:
        h.submit(h.command(source=other))
    assert code(exc) == "STALE_CONTEXT"
    bad_hash = replace(h.source_p, server_sequence=41)
    with pytest.raises(AssistanceError) as exc:
        h.submit(h.command(source=bad_hash))
    assert code(exc) == "STALE_CONTEXT"
    assert h.source_p.admission is not None
    recapture = replace(h.source_p,
                        admission=replace(h.source_p.admission, decision="RECAPTURE"))
    h.sources.add("org_fx_school_a", CANVAS_P, recapture)
    with pytest.raises(AssistanceError) as exc:
        h.submit(h.command())
    assert code(exc) == "STALE_CONTEXT"
    assert jobs(h) == {}


def test_n09_policy_absent_disabled_or_level_not_allowed(h: AssistanceHarness) -> None:
    h.policy.snapshot = None
    with pytest.raises(AssistanceError) as exc:
        h.submit()
    assert code(exc) == "POLICY_UNRESOLVED"
    h.policy.snapshot = fixture_policy(assistance_enabled=False)
    with pytest.raises(AssistanceError) as exc:
        h.submit()
    assert code(exc) == "FORBIDDEN_SCOPE"
    assert refused(h) == ["ASSISTANCE_DISABLED"]
    h.policy.snapshot = fixture_policy()
    with pytest.raises(AssistanceError) as exc:
        h.submit(h.command(level="level_fx_9"))
    assert code(exc) == "FIELD_VALIDATION_FAILED"
    assert jobs(h) == {}


def test_n10_budget_exhausted_refuses_before_any_job(h: AssistanceHarness) -> None:
    h.policy.snapshot = fixture_policy(per_target_limit=1)
    h.submit()
    h.clock.advance(seconds=6)
    with pytest.raises(AssistanceError) as exc:
        h.submit(h.command(level=LEVEL_2))
    assert code(exc) == "BUDGET_EXCEEDED"
    assert len(jobs(h)) == 1 and len(requested_events(h)) == 1
    assert refused(h) == ["BUDGET_EXCEEDED"]
    h.policy.snapshot = fixture_policy(per_session_limit=1)
    with pytest.raises(AssistanceError) as exc:
        h.submit(h.group_command())
    assert code(exc) == "BUDGET_EXCEEDED"


def test_n11_debounce_window_then_allowed(h: AssistanceHarness) -> None:
    h.submit()
    h.clock.advance(seconds=2)
    with pytest.raises(AssistanceError) as exc:
        h.submit(h.command(level=LEVEL_2))
    assert code(exc) == "RATE_LIMITED" and exc.value.retry_after_s == 3
    assert refused(h) == ["RATE_LIMITED"]
    h.clock.advance(seconds=4)
    assert h.submit(h.command(level=LEVEL_2)).outcome is ReceiptOutcome.CREATED


def test_n13_child_cannot_cancel_group_or_other_participant(h: AssistanceHarness) -> None:
    group = h.submit(h.group_command()).request
    with pytest.raises(AssistanceError) as exc:
        h.service.cancel(h.cancel_command(DEVICE_GA, group.assistance_id))
    assert code(exc) == "FORBIDDEN_SCOPE"
    h.owner.turns[CANVAS_G] = Contributor(CHILD_B, "turn_fx_gb", 1)
    h.clock.advance(seconds=6)
    other = h.submit(h.command(TEACHER, canvas=CANVAS_G,
                               target=TargetScope(TargetKind.INDIVIDUAL, CHILD_B))).request
    with pytest.raises(AssistanceError) as exc:
        h.service.cancel(h.cancel_command(DEVICE_GA, other.assistance_id))
    assert code(exc) == "FORBIDDEN_SCOPE"
    # D3 literal: the bound participant's device may cancel the Teacher-initiated request.
    cancelled = h.service.cancel(h.cancel_command(DEVICE_GB, other.assistance_id))
    assert cancelled.request.status is RequestStatus.CANCELLED


def test_n14_cancel_preconditions(h: AssistanceHarness) -> None:
    request = h.submit().request
    with pytest.raises(AssistanceError) as exc:
        h.service.cancel(h.cancel_command(TEACHER, request.assistance_id, if_match=None))
    assert code(exc) == "PRECONDITION_REQUIRED"
    with pytest.raises(AssistanceError) as exc:
        h.service.cancel(h.cancel_command(TEACHER, request.assistance_id,
                                          if_match='"assistance:x:9"'))
    assert code(exc) == "STALE_AGGREGATE"
    h.service.cancel(h.cancel_command(TEACHER, request.assistance_id))
    with pytest.raises(AssistanceError) as exc:
        h.service.cancel(h.cancel_command(TEACHER, request.assistance_id))
    assert code(exc) == "INVALID_STATE"


def test_n16_receipt_replay_after_scope_revoked_is_not_disclosed(h: AssistanceHarness) -> None:
    command = h.command()
    request = h.submit(command).request
    cancel = h.cancel_command(DEVICE_A, request.assistance_id)
    h.service.cancel(cancel)
    h.authority.disclosure_revoked.add(DEVICE_A.principal_id)
    with pytest.raises(AssistanceError) as exc:
        h.service.submit(command)
    assert code(exc) == "RESOURCE_NOT_FOUND"
    with pytest.raises(AssistanceError) as exc:
        h.service.cancel(cancel)
    assert code(exc) == "RESOURCE_NOT_FOUND"


def test_n18_child_intent_rules(h: AssistanceHarness) -> None:
    with pytest.raises(AssistanceError) as exc:
        h.submit(h.command(intent="bad\x07text"))
    assert code(exc) == "FIELD_VALIDATION_FAILED"
    with pytest.raises(AssistanceError) as exc:
        h.submit(h.command(TEACHER, intent="teacher wrote this"))
    assert code(exc) == "FIELD_VALIDATION_FAILED"
    with pytest.raises(AssistanceError) as exc:
        h.submit(h.command(TEACHER, reason=RequestReason.CHILD_REQUEST))
    assert code(exc) == "FIELD_VALIDATION_FAILED"


def test_n19_paused_or_ended_session(h: AssistanceHarness) -> None:
    h.owner.canvases[CANVAS_P] = replace(h.owner.canvases[CANVAS_P], session_active=False)
    with pytest.raises(AssistanceError) as exc:
        h.submit()
    assert code(exc) == "INVALID_STATE"


def test_n20_n21_n22_cancel_idempotency(h: AssistanceHarness) -> None:
    request = h.submit().request
    with pytest.raises(AssistanceError) as exc:
        h.service.cancel(h.cancel_command(DEVICE_A, request.assistance_id, key=""))
    assert code(exc) == "MALFORMED_REQUEST"
    cancel = h.cancel_command(DEVICE_A, request.assistance_id, key="cancel_key",
                              reason="done")
    first = h.service.cancel(cancel)
    with pytest.raises(AssistanceError) as exc:
        h.service.cancel(replace(cancel, reason="changed"))
    assert code(exc) == "IDEMPOTENCY_PAYLOAD_MISMATCH"
    # N22: the request has moved on and the Child's turn is closed; the same command replays.
    h.service.reconcile(request.assistance_id)
    assert h.request(request.assistance_id).record_version > first.request.record_version
    h.authority.devices[DEVICE_A.principal_id].turn_open = False
    replay = h.service.cancel(cancel)
    assert replay.replayed and replay.request == first.request


def test_region_rules(h: AssistanceHarness) -> None:
    with pytest.raises(AssistanceError) as exc:
        h.submit(h.command(region="region_fx_missing"))
    assert code(exc) == "FIELD_VALIDATION_FAILED"
    with pytest.raises(AssistanceError) as exc:
        h.submit(h.command(region="region_fx_b_only"))
    assert code(exc) == "FORBIDDEN_SCOPE"
    assert h.submit(h.command(region="region_fx_open")).outcome is ReceiptOutcome.CREATED


# ------------------------------------------------- same-revision fact movement (PR02)
def _supersede_case(h: AssistanceHarness, change: object) -> None:
    old = h.submit(h.group_command()).request
    change()  # type: ignore[operator]
    new = h.submit(h.group_command())
    assert new.outcome is ReceiptOutcome.CREATED
    assert new.request.assistance_id != old.assistance_id
    stale = h.request(old.assistance_id)
    assert stale.status is RequestStatus.STALE
    assert stale.status_reason is StatusReason.SUPERSEDED_BY_FACT_CHANGE
    assert not stale.counts_for_debounce
    assert h.request(new.request.assistance_id).facts.context_revision == (
        stale.facts.context_revision)


def test_n23_changed_roster_same_revision_is_not_deduplicated(h: AssistanceHarness) -> None:
    _supersede_case(h, lambda: h.set_roster((CHILD_A, CHILD_C)))
    newest = max(jobs(h).values(), key=lambda j: j.job_id)  # type: ignore[attr-defined]
    assert sorted(newest.scope.subject_refs) == [CHILD_A, CHILD_C]  # type: ignore[attr-defined]


def test_n24_changed_owner_fact_same_revision_is_not_deduplicated(
    h: AssistanceHarness,
) -> None:
    _supersede_case(h, lambda: h.owner.update_member(CHILD_B, months=121, age_revision=2))


def test_n25_changed_render_same_checkpoint_is_not_deduplicated(h: AssistanceHarness) -> None:
    _supersede_case(h, lambda: h.set_render(CANVAS_G, "fx_g_rerender"))
