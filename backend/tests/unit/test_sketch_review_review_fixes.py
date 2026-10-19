"""BE2-05 regressions for the Codex implementation review (RV-CR01..RV-CR05, 2026-10-19).

Each test reproduces the reviewed counterexample on the real SK1 -> 05 fixture chain and asserts
the corrected behaviour. Owner changes use the fixture's coordinated publication + epoch bump.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from typing import Any

import pytest

from sketch2life.application.services.sketch_review import ReviewCommand, SketchReviewError
from sketch2life.domain.sketch_review import ModerationOutcome
from sketch2life.infrastructure.assistance.harness import (
    CHILD_A,
    CHILD_B,
    DEVICE_A,
    GROUP,
    LEVEL,
    ORG,
    TEACHER,
)
from sketch2life.infrastructure.sketch_review.fakes import DeviceBinding
from sketch2life.infrastructure.sketch_review.harness import (
    SketchReviewHarness,
    build_sketch_review_harness,
)


@pytest.fixture
def h() -> SketchReviewHarness:
    return build_sketch_review_harness()


def _error(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> SketchReviewError:
    with pytest.raises(SketchReviewError) as raised:
        fn(*args, **kwargs)
    return raised.value


def _blocking_policy(h: SketchReviewHarness, proposal_id: str) -> Any:
    target = h.target(proposal_id)
    assert h.policy.snapshot is not None and target.text
    return replace(h.policy.snapshot, version="2", blocked_terms=frozenset({target.text}))


# ------------------------------------------------------------------ RV-CR01
def test_rv_cr01_moderate_uses_current_policy_not_old_passed(h: SketchReviewHarness) -> None:
    proposal_id = h.pending()
    old = h.service.moderate(TEACHER, proposal_id)
    assert old.outcome is ModerationOutcome.PASSED
    h.publish_review_policy(_blocking_policy(h, proposal_id))
    current = h.service.moderate(TEACHER, proposal_id)
    assert current.outcome is ModerationOutcome.BLOCKED
    assert current.policy_version.endswith("@2") and old.policy_version.endswith("@1")
    records = h.store.snapshot().moderation
    assert old in records.values() and current in records.values()  # history kept
    intents = h.store.snapshot().quarantine
    assert len(intents) == 1  # quarantine intent for the newly blocked assessment
    assert _error(h.review, proposal_id, "approve").code == "INVALID_STATE"
    assert h.service.child_payload(DEVICE_A, proposal_id)["status"] == "unavailable"
    assert h.service.queue_item(TEACHER, proposal_id)["moderation_state"] == "blocked"
    assert not h.store.snapshot().entries


def test_rv_cr01_direct_approve_after_policy_block(h: SketchReviewHarness) -> None:
    proposal_id = h.pending()
    h.service.moderate(TEACHER, proposal_id)  # PASSED @v1
    h.publish_review_policy(_blocking_policy(h, proposal_id))
    assert _error(h.review, proposal_id, "approve").code == "INVALID_STATE"
    snapshot = h.store.snapshot()
    outcomes = sorted((m.policy_version[-2:], str(m.outcome)) for m in snapshot.moderation.values())
    assert outcomes == [("@1", "passed"), ("@2", "blocked")]
    assert len(snapshot.quarantine) == 1 and not snapshot.entries
    assert h.service.child_payload(DEVICE_A, proposal_id)["status"] == "unavailable"


def test_rv_cr01_existing_approval_closes_when_policy_blocks(h: SketchReviewHarness) -> None:
    proposal_id = h.pending()
    h.service.moderate(TEACHER, proposal_id)
    h.review(proposal_id, "approve")
    assert h.service.child_payload(DEVICE_A, proposal_id)["status"] == "available"
    h.publish_review_policy(_blocking_policy(h, proposal_id))
    body = h.service.child_payload(DEVICE_A, proposal_id)  # not yet re-moderated under v2
    assert body["status"] != "available" and body["text_or_question"] is None
    h.service.moderate(TEACHER, proposal_id)  # v2 assessment: BLOCKED
    assert h.service.child_payload(DEVICE_A, proposal_id)["status"] == "unavailable"


# ------------------------------------------------------------------ RV-CR02
def _publish_during_first_call(h: SketchReviewHarness, owner: Any, attr: str,
                               publication: Callable[[], object]) -> list[int]:
    original = getattr(owner, attr)
    fired = [0]

    def wrapper(*args: Any) -> Any:
        value = original(*args)  # the OLD value is observed first ...
        if not fired[0]:
            fired[0] = 1
            assert publication()  # ... then a coordinated publication bumps the epoch
        return value

    setattr(owner, attr, wrapper)
    return fired


@pytest.mark.parametrize("path", ["record_review", "moderate"])
def test_rv_cr02_policy_disabled_during_preliminary_read(h: SketchReviewHarness,
                                                         path: str) -> None:
    proposal_id = h.pending()
    body, etag = h.command(proposal_id), h.etag(proposal_id)
    assert h.policy.snapshot is not None
    disabled = replace(h.policy.snapshot, version="2", enabled=False)
    fired = _publish_during_first_call(h, h.policy, "current",
                                       lambda: h.publish_review_policy(disabled))
    if path == "record_review":
        error = _error(h.service.record_review,
                       ReviewCommand(TEACHER, proposal_id, h.key(), etag, body))
    else:
        error = _error(h.service.moderate, TEACHER, proposal_id)
    assert fired[0] == 1 and error.code == "POLICY_UNRESOLVED"
    snapshot = h.store.snapshot()
    assert not snapshot.entries and not snapshot.moderation


@pytest.mark.parametrize("path", ["record_review", "moderate"])
def test_rv_cr02_grant_revoked_during_preliminary_read(h: SketchReviewHarness,
                                                       path: str) -> None:
    proposal_id = h.pending()
    body, etag = h.command(proposal_id), h.etag(proposal_id)
    fired = _publish_during_first_call(
        h, h.authority, "allowed",
        lambda: h.publish_grant_change(
            TEACHER, lambda: h.authority.teachers.pop(TEACHER.principal_id)))
    if path == "record_review":
        error = _error(h.service.record_review,
                       ReviewCommand(TEACHER, proposal_id, h.key(), etag, body))
    else:
        error = _error(h.service.moderate, TEACHER, proposal_id)
    assert fired[0] == 1 and error.code == "RESOURCE_NOT_FOUND"
    snapshot = h.store.snapshot()
    assert not snapshot.entries and not snapshot.moderation


# ------------------------------------------------------------------ RV-CR03
@pytest.mark.parametrize("change", ["quarantine", "consent", "policy", "context", "device"])
def test_rv_cr03_warm_cache_never_serves_after_denial(change: str) -> None:
    h = build_sketch_review_harness()
    proposal_id = h.pending()
    h.service.moderate(TEACHER, proposal_id)
    h.review(proposal_id, "approve")
    warm = h.cache.get(DEVICE_A, proposal_id)
    assert warm["status"] == "available" and warm["text_or_question"] is not None
    assert h.cache.get(DEVICE_A, proposal_id) == warm and h.cache.reauthorized_hits == 1
    if change == "quarantine":
        h.quarantine(h.target(proposal_id).ref_set)
    elif change == "consent":
        h.revoke_producer_consent()
    elif change == "policy":
        assert h.policy.snapshot is not None
        h.publish_review_policy(replace(h.policy.snapshot, version="2"))
    elif change == "context":
        h.bump_audience_revision()
    else:  # device rebound to another participant; no 05 epoch involved
        h.authority.devices[DEVICE_A.principal_id] = DeviceBinding(ORG, "session_fx_001", CHILD_B)
    after = h.cache.get(DEVICE_A, proposal_id)  # no caller-managed refresh
    assert after["status"] != "available"
    assert after["text_or_question"] is None and after["overlay_asset_ref"] is None


# ------------------------------------------------------------------ RV-CR04
def test_rv_cr04_policy_restoration_does_not_revive(h: SketchReviewHarness) -> None:
    proposal_id = h.pending()
    original = h.policy.snapshot
    assert original is not None
    h.service.moderate(TEACHER, proposal_id)
    old = h.review(proposal_id, "approve")
    h.publish_review_policy(replace(original, version="2"))
    assert h.service.child_payload(DEVICE_A, proposal_id)["status"] != "available"
    h.publish_review_policy(original)  # same values as at approval time; NO refresh
    assert h.service.child_payload(DEVICE_A, proposal_id)["status"] != "available"
    assert h.service.eligibility(DEVICE_A, proposal_id).eligible is False
    # A fresh, explicitly authorized decision may reopen the non-terminal target.
    fresh = h.review(proposal_id, "approve")
    assert fresh.status == 201 and not fresh.data["semantic_duplicate"]
    assert fresh.data["record"]["review_id"] != old.data["record"]["review_id"]
    body = h.service.child_payload(DEVICE_A, proposal_id)
    assert body["status"] == "available" and body["review_ref"] == fresh.data["record"]["review_id"]


def test_rv_cr04_context_restoration_does_not_revive(h: SketchReviewHarness) -> None:
    proposal_id = h.pending()
    h.service.moderate(TEACHER, proposal_id)
    h.review(proposal_id, "approve")
    target = h.target(proposal_id)
    session = h.context.sessions[(target.organization_id, target.session_id)]
    h.bump_audience_revision()
    assert h.service.child_payload(DEVICE_A, proposal_id)["status"] != "available"
    h.publish_review_context(lambda: setattr(session, "audience_context_revision",
                                             session.audience_context_revision - 1))
    assert h.service.child_payload(DEVICE_A, proposal_id)["status"] != "available"
    assert h.service.projection(TEACHER, proposal_id)["pipeline_state"] != "approved"


# ------------------------------------------------------------------ RV-CR05
@pytest.mark.parametrize("transport", ["typed", "json"])
def test_rv_cr05_normalized_reason_replays(h: SketchReviewHarness, transport: str) -> None:
    proposal_id = h.pending()
    h.service.moderate(TEACHER, proposal_id)
    etag = h.etag(proposal_id)
    first = h.command(proposal_id, "reject", reason="Café")
    same = h.command(proposal_id, "reject", reason="  Café  ")

    def send(body: Any) -> Any:
        wire = body if transport == "typed" else body.model_dump_json()
        return h.service.record_review(ReviewCommand(TEACHER, proposal_id, "key_fx_cr05",
                                                     etag, wire))

    accepted = send(first)
    replay = send(same)
    assert accepted.status == 201 and replay.replayed
    assert replay.data["record"] == accepted.data["record"]
    different = h.command(proposal_id, "reject", reason="Another reason")
    assert _error(send, different).code == "IDEMPOTENCY_PAYLOAD_MISMATCH"
    assert len(h.store.snapshot().entries[proposal_id]) == 1


@pytest.mark.parametrize("transport", ["typed", "json"])
def test_rv_cr05_reordered_audience_replays(h: SketchReviewHarness, transport: str) -> None:
    proposal_id = h.pending(level=LEVEL, group=True)
    h.service.moderate(TEACHER, proposal_id)
    etag = h.etag(proposal_id)
    first = h.command(proposal_id, participants=(CHILD_A, CHILD_B), groups=(GROUP,))
    same = h.command(proposal_id, participants=(CHILD_B, CHILD_A), groups=(GROUP,))

    def send(body: Any) -> Any:
        wire = body if transport == "typed" else body.model_dump_json()
        return h.service.record_review(ReviewCommand(TEACHER, proposal_id, "key_fx_cr05a",
                                                     etag, wire))

    accepted = send(first)
    replay = send(same)
    assert accepted.status == 201 and replay.replayed
    narrower = h.command(proposal_id, participants=(CHILD_A,), groups=(GROUP,))
    assert _error(send, narrower).code == "IDEMPOTENCY_PAYLOAD_MISMATCH"
