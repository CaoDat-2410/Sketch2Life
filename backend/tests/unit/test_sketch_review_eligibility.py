"""BE2-05 Child/artifact access fails closed (fetch, cache, subscription, ticket — fakes only)."""

from __future__ import annotations

from typing import Any

import pytest

from sketch2life.application.ports.ai_jobs import Principal
from sketch2life.infrastructure.assistance.harness import (
    CHILD_A,
    CHILD_B,
    DEVICE_A,
    DEVICE_GB,
    GROUP,
    LEVEL,
    ORG,
    TEACHER,
)
from sketch2life.infrastructure.sketch_review.harness import (
    SketchReviewHarness,
    build_sketch_review_harness,
)


@pytest.fixture
def h() -> SketchReviewHarness:
    return build_sketch_review_harness()


def _approved(h: SketchReviewHarness, **kwargs: Any) -> tuple[str, str]:
    proposal_id = h.pending(**kwargs)
    h.moderate(proposal_id)
    result = h.review(proposal_id, "approve")
    return proposal_id, str(result.data["record"]["review_id"])


def _ticket(h: SketchReviewHarness, device: Principal, proposal_id: str,
            review_ref: str | None) -> str | None:
    target = h.target(proposal_id)
    asset = target.asset or target.result_document
    assert asset is not None and target.content_sha256 is not None
    return h.ticket.issue(device, proposal_id, asset_ref=asset.artifact_ref,
                          content_sha256=target.content_sha256, review_ref=review_ref)


def test_rv_n01_child_sees_status_only_until_approved(h: SketchReviewHarness) -> None:
    proposal_id = h.pending()
    for step in ("pending", "moderated"):
        body = h.service.child_payload(DEVICE_A, proposal_id)
        assert body["status"] == "pending", step
        assert body["text_or_question"] is None and body["overlay_asset_ref"] is None
        assert body["review_ref"] is None
        h.moderate(proposal_id)
    h.review(proposal_id, "request_changes")
    body = h.service.child_payload(DEVICE_A, proposal_id)
    assert body["status"] == "unavailable" and body["text_or_question"] is None


def test_rv_n01b_blocked_and_stale_status_only() -> None:
    blocked = build_sketch_review_harness()
    proposal_id = blocked.pending(unsafe=True)
    blocked.moderate(proposal_id)
    assert blocked.service.child_payload(DEVICE_A, proposal_id)["status"] == "unavailable"
    stale = build_sketch_review_harness()
    stale_id = stale.pending()
    stale.revoke_producer_consent()
    assert stale.service.child_payload(DEVICE_A, stale_id)["status"] == "unavailable"


def test_rv_n02_guessed_artifact_ref_gets_no_ticket(h: SketchReviewHarness) -> None:
    proposal_id = h.pending()
    assert _ticket(h, DEVICE_A, proposal_id, None) is None  # pending: no approval
    h.moderate(proposal_id)
    review_ref = str(h.review(proposal_id, "approve").data["record"]["review_id"])
    assert _ticket(h, DEVICE_A, proposal_id, "skrev_guess") is None  # wrong review ref
    assert _ticket(h, DEVICE_A, proposal_id, review_ref) is not None
    target = h.target(proposal_id)
    assert h.ticket.issue(DEVICE_A, proposal_id, asset_ref="artifact_fx_guess",
                          content_sha256=target.content_sha256 or "", review_ref=review_ref) is None
    assert h.ticket.issue(TEACHER, proposal_id, asset_ref=target.ref_set[0],
                          content_sha256=target.content_sha256 or "", review_ref=review_ref) is None


@pytest.mark.parametrize("change", ["consent", "quarantine", "context", "policy"])
def test_rv_n11_access_closes_and_stays_closed(change: str) -> None:
    h = build_sketch_review_harness()
    proposal_id, review_ref = _approved(h)
    assert h.service.child_payload(DEVICE_A, proposal_id)["status"] == "available"
    if change == "consent":
        h.revoke_producer_consent()
    elif change == "quarantine":
        h.quarantine(h.target(proposal_id).ref_set)
    elif change == "context":
        h.bump_audience_revision()
    else:
        assert h.policy.snapshot is not None
        from dataclasses import replace
        h.publish_review_policy(replace(h.policy.snapshot, version="2"))
    assert h.service.child_payload(DEVICE_A, proposal_id)["status"] != "available"
    assert _ticket(h, DEVICE_A, proposal_id, review_ref) is None
    assert h.service.refresh(proposal_id, ORG) == (review_ref,)
    if change == "context":  # restore the same context revision: stale does not come back
        h.context.sessions[(ORG, h.target(proposal_id).session_id)].audience_context_revision -= 1
        assert h.service.child_payload(DEVICE_A, proposal_id)["status"] != "available"


def test_rv_n14_cache_and_subscription_do_not_leak_after_revoke(h: SketchReviewHarness) -> None:
    proposal_id, _ = _approved(h)
    assert h.cache.get(DEVICE_A, proposal_id)["status"] == "available"
    assert h.cache.get(DEVICE_A, proposal_id)["status"] == "available"
    misses = h.cache.misses
    pushed = h.dispatcher.deliver(list(h.store.snapshot().intents))
    assert pushed == 1
    h.review(proposal_id, "reject")
    assert h.cache.get(DEVICE_A, proposal_id)["status"] == "unavailable"
    assert h.cache.misses == misses + 1  # epoch changed: old cached content not reused
    before = len(h.dispatcher.pushed)
    h.dispatcher.deliver(list(h.store.snapshot().intents))
    assert len(h.dispatcher.pushed) == before


@pytest.mark.parametrize("decision", ["reject", "request_changes"])
def test_rv_n22_terminal_decision_on_audience_b_revokes_audience_a(decision: str) -> None:
    h = build_sketch_review_harness()
    proposal_id = h.pending(level=LEVEL, group=True)
    h.moderate(proposal_id)
    approve = h.review(proposal_id, "approve", participants=(CHILD_A,), groups=(GROUP,))
    review_ref = str(approve.data["record"]["review_id"])
    assert h.service.child_payload(DEVICE_A, proposal_id)["status"] == "available"
    assert h.cache.get(DEVICE_A, proposal_id)["status"] == "available"
    assert _ticket(h, DEVICE_A, proposal_id, review_ref) is not None
    h.review(proposal_id, decision, participants=(CHILD_B,), groups=(GROUP,))
    entries = {e.review_id: e for e in h.store.snapshot().entries[proposal_id]}
    assert str(entries[review_ref].state) == "revoked"
    assert h.service.child_payload(DEVICE_A, proposal_id)["status"] == "unavailable"
    assert h.cache.get(DEVICE_A, proposal_id)["status"] == "unavailable"
    assert _ticket(h, DEVICE_A, proposal_id, review_ref) is None
    assert h.service.child_payload(DEVICE_GB, proposal_id)["status"] == "unavailable"
    assert h.service.queue_item(TEACHER, proposal_id)["version_terminal"] is True


def test_rv_n17_device_never_reaches_producer_teacher_read(h: SketchReviewHarness) -> None:
    calls: list[object] = []
    original = h.chain.service.get_record

    def spy(principal: Principal, proposal_id: str) -> dict[str, object]:
        calls.append(principal)
        return original(principal, proposal_id)

    h.chain.service.get_record = spy  # type: ignore[method-assign]
    proposal_id, _ = _approved(h)
    h.service.child_payload(DEVICE_A, proposal_id)
    h.service.eligibility(DEVICE_A, proposal_id)
    _ticket(h, DEVICE_A, proposal_id, None)
    assert all(getattr(p, "role", None) is not None and str(p.role) == "teacher"  # type: ignore[attr-defined]
               for p in calls)
    assert h.targets.queue_record(DEVICE_A, proposal_id) is None
