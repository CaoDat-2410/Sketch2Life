"""BE2-03 A1-CR03-F1/F2 regressions (written before the fixes).

F1: an owner publication requested inside an atomic assistance unit must not commit inside
it; it runs after that unit exits (commit or rollback) and sees the committed state.
F2: actual Vision service commits (invalidation/correction) between a BE2-03 decision read
and its commit must be visible to the decision/commit protocol (cache and handoff)."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from sketch2life.application.ports.assistance import ReceiptOutcome
from sketch2life.application.services.vision_analysis import (
    CorrectionCommand,
    InvalidationNotice,
    VisionAnalysisError,
)
from sketch2life.domain.assistance import RequestStatus, StatusReason
from sketch2life.domain.vision_analysis import InvalidationReason, analysis_etag
from sketch2life.infrastructure.ai_jobs.fakes import eligibility_fence_scope
from sketch2life.infrastructure.assistance.fakes import CoordinationError
from sketch2life.infrastructure.assistance.harness import (
    CHILD_A,
    CONTEXT_REVISION,
    ORG,
    TEACHER,
    AssistanceHarness,
    build_assistance_harness,
)


def in_assistance(h: AssistanceHarness) -> bool:
    return bool(h.coordinator._depth("assistance") > 0)


def hook_inside_assistance_unit(h: AssistanceHarness, action: Callable[[], object]) -> list[bool]:
    """Run ``action`` once on the first clock read made inside an assistance unit (the
    event timestamp, after the unit's decision-epoch guard)."""

    real = h.clock.now
    fired: list[bool] = []

    def now() -> object:
        if not fired and in_assistance(h):
            fired.append(True)
            action()
        return real()

    h.clock.now = now  # type: ignore[method-assign, assignment]
    return fired


def hook_once_on_clock(h: AssistanceHarness, action: Callable[[], object]) -> list[bool]:
    real = h.clock.now
    fired: list[bool] = []

    def now() -> object:
        if not fired:
            fired.append(True)
            action()
        return real()

    h.clock.now = now  # type: ignore[method-assign, assignment]
    return fired


def ready_to_reconcile(h: AssistanceHarness) -> str:
    request = h.submit().request
    h.dispatch()
    started, job_id, attempt_id = h.start_next()
    assert started.started
    h.finish_vision(job_id, attempt_id)
    return request.assistance_id


def completed_teacher_request(h: AssistanceHarness) -> tuple[str, str]:
    final = h.run_vision(h.submit(h.command(TEACHER)).request.assistance_id)
    assert final.handoff is not None
    return final.assistance_id, final.handoff.analysis_id


# ------------------------------------------------------------------------- F1
def test_f1_consent_publication_inside_handoff_unit_runs_after_commit() -> None:
    h = build_assistance_harness()
    assistance_id = ready_to_reconcile(h)
    observed: dict[str, object] = {}

    def revoke() -> None:
        committed = h.store.peek(assistance_id)
        assert committed is not None
        observed["status_seen_by_callback"] = committed.status
        observed["intents_seen_by_callback"] = len(h.store.snapshot().intents)
        h.revoke_consent(CHILD_A)

    fired = hook_inside_assistance_unit(
        h, lambda: observed.setdefault("ran_immediately", h.publish_owner_change(revoke)))
    final = h.service.reconcile(assistance_id)
    assert fired and observed["ran_immediately"] is False
    # Commit order: the handoff committed first; the revocation observed it afterwards.
    assert observed["status_seen_by_callback"] is RequestStatus.ANALYSIS_READY
    assert observed["intents_seen_by_callback"] == 1
    assert final is not None and final.status is RequestStatus.ANALYSIS_READY
    assert len(h.sketch.intents) == 1
    assert not h.owner.member_rows[CHILD_A].consent_effective


def test_f1_disclosure_publication_inside_cache_unit_runs_after_commit() -> None:
    h = build_assistance_harness()
    original, _ = completed_teacher_request(h)
    observed: dict[str, object] = {}

    def withdraw() -> None:
        snapshot = h.store.snapshot()
        observed["cache_hit_committed_before_callback"] = any(
            r.cache_hit_of is not None for r in snapshot.requests.values())
        h.authority.disclosure_revoked.add(TEACHER.principal_id)

    fired = hook_inside_assistance_unit(
        h, lambda: observed.setdefault("ran_immediately", h.publish_owner_change(withdraw)))
    result = h.submit(h.command(TEACHER))
    assert fired and observed["ran_immediately"] is False
    assert observed["cache_hit_committed_before_callback"] is True
    assert result.outcome is ReceiptOutcome.CACHE_HIT  # legitimately committed first
    assert not h.authority.disclose(TEACHER, h.request(original))


def test_f1_publication_committed_before_decision_still_blocks_handoff() -> None:
    h = build_assistance_harness()
    assistance_id = ready_to_reconcile(h)
    assert h.publish_owner_change(lambda: h.revoke_consent(CHILD_A)) is True
    final = h.service.reconcile(assistance_id)
    assert final is not None and final.status is RequestStatus.STALE
    assert h.sketch.intents == []


def test_f1_rollback_with_queued_publication_publishes_nothing_staged() -> None:
    h = build_assistance_harness()
    assistance_id = ready_to_reconcile(h)
    scope = eligibility_fence_scope(ORG)
    epoch_before = h.fences.epochs[scope]
    observed: dict[str, object] = {}

    def revoke() -> None:
        committed = h.store.peek(assistance_id)
        assert committed is not None
        observed["status_seen_by_callback"] = committed.status
        observed["intents_seen_by_callback"] = len(h.store.snapshot().intents)
        h.revoke_consent(CHILD_A)

    def inside() -> None:
        h.store.fail_next_commit = True
        observed["ran_immediately"] = h.publish_owner_change(revoke)

    hook_inside_assistance_unit(h, inside)
    with pytest.raises(RuntimeError, match="injected assistance commit failure"):
        h.service.reconcile(assistance_id)
    assert observed["ran_immediately"] is False
    assert observed["status_seen_by_callback"] is RequestStatus.SCHEDULED
    assert observed["intents_seen_by_callback"] == 0
    committed = h.request(assistance_id)
    assert committed.status is RequestStatus.SCHEDULED and committed.handoff is None
    assert h.store.snapshot().intents == [] and h.sketch.intents == []
    assert h.fences.epochs[scope] == epoch_before + 1  # only the owner publication's bump
    # The coordinator is free: the next reconcile re-decides on the revoked facts.
    final = h.service.reconcile(assistance_id)
    assert final is not None and final.status is RequestStatus.STALE


def test_f1_failed_deferred_callback_inside_unit_is_recorded_and_releases() -> None:
    h = build_assistance_harness()
    assistance_id = ready_to_reconcile(h)

    def boom() -> None:
        raise ValueError("deferred owner publication failed")

    hook_inside_assistance_unit(h, lambda: h.coordinator.request_publication(boom))
    final = h.service.reconcile(assistance_id)
    assert final is not None and final.status is RequestStatus.ANALYSIS_READY
    assert [str(e) for e in h.coordinator.deferred_failures] == [
        "deferred owner publication failed"]
    assert h.service.read(TEACHER, assistance_id).status is RequestStatus.ANALYSIS_READY


# ------------------------------------------------------------------------- F2
def test_f2_vision_invalidation_between_cache_read_and_commit() -> None:
    h = build_assistance_harness()
    _, analysis_id = completed_teacher_request(h)
    h.clock.advance(seconds=6)
    real = h.outcomes.current
    calls: list[str] = []

    def current(organization_id: str, analysis: str) -> object:
        outcome = real(organization_id, analysis)
        calls.append(analysis)
        if len(calls) == 1:
            h.vision.apply_invalidation(InvalidationNotice(
                "notice_fx_f2_cache", ORG, analysis, InvalidationReason.INTENT_CHANGED))
        return outcome

    h.outcomes.current = current  # type: ignore[method-assign, assignment]
    result = h.submit(h.command(TEACHER))
    assert str(h.vision.downstream_meaning(TEACHER, analysis_id).state) == "not_applicable"
    assert result.outcome is ReceiptOutcome.CREATED
    assert h.request(result.request.assistance_id).cache_hit_of is None
    assert len(calls) >= 2  # the stale read was re-decided


def test_f2_vision_invalidation_between_handoff_gate_and_commit() -> None:
    h = build_assistance_harness()
    assistance_id = ready_to_reconcile(h)
    job_id = h.request(assistance_id).job_id
    assert job_id is not None

    def invalidate() -> None:
        analysis = next(iter(h.vision_store.snapshot().heads))
        h.vision.apply_invalidation(InvalidationNotice(
            "notice_fx_f2_handoff", ORG, analysis, InvalidationReason.CONTEXT_CHANGED))

    fired = hook_once_on_clock(h, invalidate)
    final = h.service.reconcile(assistance_id)
    assert fired and final is not None
    assert final.status is RequestStatus.STALE
    assert final.status_reason is StatusReason.CONTEXT_CHANGED
    assert h.sketch.intents == []


def test_f2_teacher_correction_commit_between_read_and_commit_is_re_decided() -> None:
    h = build_assistance_harness()
    _, analysis_id = completed_teacher_request(h)
    real = h.outcomes.current
    calls: list[int] = []

    def current(organization_id: str, analysis: str) -> object:
        outcome = real(organization_id, analysis)
        calls.append(1)
        if len(calls) == 1:
            h.vision.submit_correction(CorrectionCommand(
                principal=TEACHER, analysis_id=analysis, idempotency_key="key_fx_correct",
                if_match=analysis_etag(analysis, 1), intended_objects=("cat",),
                correction_reason="Teacher confirms a cat",
                expected_context_revision=CONTEXT_REVISION))
        return outcome

    h.outcomes.current = current  # type: ignore[method-assign, assignment]
    result = h.submit(h.command(TEACHER))
    assert len(calls) == 2  # the correction commit forced a fresh decision
    assert result.outcome is ReceiptOutcome.CACHE_HIT  # still applicable after re-decision
    assert str(h.vision.downstream_meaning(TEACHER, analysis_id).state) == "confirmed"


def test_f2_vision_call_inside_assistance_unit_is_refused() -> None:
    h = build_assistance_harness()
    _, analysis_id = completed_teacher_request(h)
    with h.store.transaction(), pytest.raises(CoordinationError):
        h.vision.downstream_meaning(TEACHER, analysis_id)


def test_f2_failed_vision_commit_does_not_move_the_decision_epoch() -> None:
    h = build_assistance_harness()
    _, analysis_id = completed_teacher_request(h)
    before = h.service._decision_epoch(ORG)
    h.vision_store.fail_next_commit = True
    with pytest.raises(VisionAnalysisError) as exc:
        h.vision.apply_invalidation(InvalidationNotice(
            "notice_fx_f2_fail", ORG, analysis_id, InvalidationReason.INTENT_CHANGED))
    assert exc.value.code == "DEPENDENCY_UNAVAILABLE"
    assert h.service._decision_epoch(ORG) == before
    # The coordinator is free and the analysis is still current.
    assert str(h.vision.downstream_meaning(TEACHER, analysis_id).state) != "not_applicable"
