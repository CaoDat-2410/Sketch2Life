"""BE2-03 A1 code-review regressions A1-CR01–CR05 (written before the fixes)."""

from __future__ import annotations

import threading
import unicodedata
from collections.abc import Callable
from dataclasses import replace

import pytest

from sketch2life.application.ports.assistance import ReceiptOutcome
from sketch2life.application.services.assistance import AssistanceError
from sketch2life.domain.assistance import RequestStatus, StatusReason
from sketch2life.infrastructure.ai_jobs.fakes import eligibility_fence_scope
from sketch2life.infrastructure.assistance.harness import (
    CHILD_A,
    CHILD_B,
    DEVICE_A,
    ORG,
    TEACHER,
    AssistanceHarness,
    build_assistance_harness,
)


def jobs(h: AssistanceHarness) -> int:
    return len(h.job_store.snapshot().jobs)


def completed(h: AssistanceHarness, principal: object = TEACHER) -> str:
    request = h.submit(h.command(principal)).request  # type: ignore[arg-type]
    final = h.run_vision(request.assistance_id)
    assert final.status is RequestStatus.ANALYSIS_READY
    return final.assistance_id


def once_on_clock(h: AssistanceHarness, action: Callable[[], object]) -> list[bool]:
    """Run ``action`` once on the next clock read (a seam after a decision, before commit)."""

    real = h.clock.now
    fired: list[bool] = []

    def now() -> object:
        if not fired:
            fired.append(True)
            action()
        return real()

    h.clock.now = now  # type: ignore[method-assign, assignment]
    return fired


# --------------------------------------------------------------------- A1-CR01
def test_cr01_new_key_cache_hit_requires_current_disclosure() -> None:
    h = build_assistance_harness()
    original = completed(h)
    h.authority.disclosure_revoked.add(TEACHER.principal_id)
    with pytest.raises(AssistanceError):
        h.service.read(TEACHER, original)
    # Same semantics, brand-new key: no cache provenance; inside the window it is an
    # ordinary new request and is debounced, afterwards it is created without cache.
    with pytest.raises(AssistanceError) as exc:
        h.submit(h.command(TEACHER))
    assert exc.value.code == "RATE_LIMITED"
    h.clock.advance(seconds=6)
    result = h.submit(h.command(TEACHER))
    assert result.outcome is ReceiptOutcome.CREATED
    assert h.request(result.request.assistance_id).cache_hit_of is None


def test_cr01_disclosure_withdrawn_between_cache_gate_and_commit() -> None:
    h = build_assistance_harness()
    completed(h)
    real = h.outcomes.current
    fired: list[bool] = []

    def current(organization_id: str, analysis_id: str) -> object:
        outcome = real(organization_id, analysis_id)
        if not fired:
            fired.append(True)
            h.publish_owner_change(
                lambda: h.authority.disclosure_revoked.add(TEACHER.principal_id))
        return outcome

    h.outcomes.current = current  # type: ignore[method-assign, assignment]
    h.clock.advance(seconds=6)
    result = h.submit(h.command(TEACHER))
    assert fired
    assert result.outcome is ReceiptOutcome.CREATED
    assert h.request(result.request.assistance_id).cache_hit_of is None


def test_cr01_same_scope_cache_still_hits() -> None:
    h = build_assistance_harness()
    original = completed(h)
    hit = h.submit(h.command(TEACHER))
    assert hit.outcome is ReceiptOutcome.CACHE_HIT
    cache = h.request(hit.request.assistance_id).cache_hit_of
    assert cache is not None and cache.assistance_id == original


# --------------------------------------------------------------------- A1-CR02
def test_cr02_cross_thread_owner_publication_waits_for_foundation_commit() -> None:
    h = build_assistance_harness()
    h.submit()
    h.dispatch()
    entered, done = threading.Event(), threading.Event()
    observed: dict[str, object] = {}

    def revoke() -> None:
        h.owner_eligibility.revoked_subjects.add(CHILD_A)
        h.fences.bump(eligibility_fence_scope(ORG))

    def other() -> None:
        entered.wait(2)
        observed["ran_immediately"] = h.coordinator.request_publication(revoke)
        done.set()

    def after_hold() -> None:
        entered.set()
        observed["committed_inside_start"] = done.wait(0.2)

    thread = threading.Thread(target=other)
    thread.start()
    h.fences.after_successful_hold = after_hold
    result, job_id, _ = h.start_next()
    thread.join(5)
    assert observed["committed_inside_start"] is False
    assert observed["ran_immediately"] is True
    assert result.started  # the start transaction committed first, then the revocation
    assert CHILD_A in h.owner_eligibility.revoked_subjects


def test_cr02_deferred_publication_is_serialized_with_other_threads() -> None:
    h = build_assistance_harness()
    request = h.submit().request
    h.dispatch()
    in_deferred, other_started = threading.Event(), threading.Event()
    observed: dict[str, object] = {}

    def other() -> None:
        in_deferred.wait(2)
        other_started.set()
        h.service.read(TEACHER, request.assistance_id)  # opens an assistance unit
        observed["other_finished_at"] = len(observed)

    def deferred() -> None:
        in_deferred.set()
        other_started.wait(2)
        observed["other_finished_inside_deferred"] = "other_finished_at" in observed
        threading.Event().wait(0.1)
        observed["other_finished_inside_deferred_late"] = "other_finished_at" in observed

    thread = threading.Thread(target=other)
    thread.start()
    h.fences.after_successful_hold = lambda: h.coordinator.request_publication(deferred)
    result, _, _ = h.start_next()
    thread.join(5)
    assert result.started
    assert observed["other_finished_inside_deferred_late"] is False


# --------------------------------------------------------------------- A1-CR03
def _ready_to_reconcile(h: AssistanceHarness) -> str:
    request = h.submit().request
    h.dispatch()
    started, job_id, attempt_id = h.start_next()
    assert started.started
    h.finish_vision(job_id, attempt_id)
    return request.assistance_id


def test_cr03_consent_revoked_between_handoff_gate_and_commit() -> None:
    h = build_assistance_harness()
    assistance_id = _ready_to_reconcile(h)
    fired = once_on_clock(h, lambda: h.publish_owner_change(lambda: h.revoke_consent(CHILD_A)))
    final = h.service.reconcile(assistance_id)
    assert fired and final is not None
    assert final.status is RequestStatus.STALE
    assert final.status_reason is StatusReason.CONTEXT_CHANGED
    assert h.sketch.intents == []


def test_cr03_same_revision_fact_move_between_gate_and_commit() -> None:
    h = build_assistance_harness()
    assistance_id = _ready_to_reconcile(h)
    fired = once_on_clock(h, lambda: h.publish_owner_change(
        lambda: h.owner.update_member(CHILD_A, age_revision=2)))
    final = h.service.reconcile(assistance_id)
    assert fired and final is not None
    assert final.status is RequestStatus.STALE
    assert final.status_reason is StatusReason.CONTEXT_CHANGED
    assert h.sketch.intents == []


def test_cr03_submit_redecides_when_consent_moves_before_commit() -> None:
    h = build_assistance_harness()
    fired = once_on_clock(h, lambda: h.publish_owner_change(
        lambda: h.owner.update_member(CHILD_B, consent_effective=False)))
    with pytest.raises(AssistanceError) as exc:
        h.submit(h.group_command())
    assert fired and exc.value.code == "CONSENT_REQUIRED"
    assert jobs(h) == 0


# --------------------------------------------------------------------- A1-CR04
def test_cr04_changed_intent_same_facts_is_debounced_not_superseding() -> None:
    h = build_assistance_harness()
    old = h.submit(h.command(intent="a cat")).request
    with pytest.raises(AssistanceError) as exc:
        h.submit(h.command(intent="a dog"))
    assert exc.value.code == "RATE_LIMITED"
    kept = h.request(old.assistance_id)
    assert kept.status is RequestStatus.SCHEDULED and kept.counts_for_debounce
    assert jobs(h) == 1


def test_cr04_teacher_then_child_same_window_is_debounced() -> None:
    h = build_assistance_harness()
    old = h.submit(h.command(TEACHER)).request
    with pytest.raises(AssistanceError) as exc:
        h.submit(h.command(DEVICE_A))
    assert exc.value.code == "RATE_LIMITED"
    assert h.request(old.assistance_id).status is RequestStatus.SCHEDULED
    assert jobs(h) == 1


def test_cr04_after_window_both_requests_stay_active() -> None:
    h = build_assistance_harness()
    old = h.submit(h.command(intent="a cat")).request
    h.clock.advance(seconds=6)
    new = h.submit(h.command(intent="a dog"))
    assert new.outcome is ReceiptOutcome.CREATED
    assert h.request(old.assistance_id).status is RequestStatus.SCHEDULED
    assert jobs(h) == 2


# --------------------------------------------------------------------- A1-CR05
def test_cr05_trimmed_and_nfc_intent_is_normalized_and_stored() -> None:
    h = build_assistance_harness()
    trimmed = h.submit(h.command(intent=" a cat "))
    assert h.request(trimmed.request.assistance_id).child_intent == "a cat"
    decomposed = unicodedata.normalize("NFD", "con mèo")
    assert decomposed != "con mèo"
    h.clock.advance(seconds=6)
    nfc = h.submit(h.command(intent=decomposed, level="level_fx_2"))
    assert h.request(nfc.request.assistance_id).child_intent == "con mèo"


def test_cr05_canonical_equivalent_replay_and_dedup() -> None:
    h = build_assistance_harness()
    command = h.command(key="key_norm", intent="a cat ")
    first = h.submit(command)
    replay = h.submit(replace(command, child_intent=" a cat"))
    assert replay.replayed and replay.request == first.request
    dedup = h.submit(h.command(intent="a cat"))
    assert dedup.outcome is ReceiptOutcome.DEDUPLICATED
    with pytest.raises(AssistanceError) as exc:
        h.submit(replace(command, child_intent="a dog"))
    assert exc.value.code == "IDEMPOTENCY_PAYLOAD_MISMATCH"


@pytest.mark.parametrize("intent", ["   ", "bad\x07text", "x" * 4001])
def test_cr05_invalid_intent_still_refused(intent: str) -> None:
    h = build_assistance_harness()
    with pytest.raises(AssistanceError) as exc:
        h.submit(h.command(intent=intent))
    assert exc.value.code == "FIELD_VALIDATION_FAILED"
    assert jobs(h) == 0
