"""BE2-05 service acceptance over the real BE2-04 chain (plan candidate R2 §10)."""

from __future__ import annotations

from dataclasses import replace

import pytest

from sketch2life.application.services.sketch_generation import ReviseLevelCommand
from sketch2life.application.services.sketch_review import ReviewCommand, SketchReviewError
from sketch2life.contracts.schemas.ai_contract_candidates import SHAPE_SPECS, check_shape
from sketch2life.domain.sketch_review import EntryState, ModerationOutcome
from sketch2life.infrastructure.assistance.harness import (
    ADMIN,
    CHILD_A,
    CHILD_B,
    CHILD_C,
    DEVICE_A,
    GROUP,
    LEVEL,
    ORG,
    OTHER_CLASS_TEACHER,
    OUTSIDER,
    TEACHER,
)
from sketch2life.infrastructure.sketch_review.harness import (
    SketchReviewHarness,
    build_sketch_review_harness,
)


@pytest.fixture
def h() -> SketchReviewHarness:
    return build_sketch_review_harness()


def _error(fn: object, *args: object, **kwargs: object) -> SketchReviewError:
    with pytest.raises(SketchReviewError) as raised:
        fn(*args, **kwargs)  # type: ignore[operator]
    return raised.value


def _entries(h: SketchReviewHarness, proposal_id: str) -> dict[str, EntryState]:
    return {e.review_id: e.state for e in h.store.snapshot().entries.get(proposal_id, ())}


# ------------------------------------------------------------------ positive
def test_rv_p01_real_proposal_approved_exactly(h: SketchReviewHarness) -> None:
    proposal_id = h.pending()
    record_before = h.chain.service.get_record(TEACHER, proposal_id)
    assert h.moderate(proposal_id).outcome is ModerationOutcome.PASSED  # type: ignore[attr-defined]
    result = h.review(proposal_id, "approve")
    assert result.status == 201 and not result.replayed
    data = result.data
    assert data["record"]["state"] == "effective" and data["record"]["review_revision"] == 1
    target = h.target(proposal_id)
    assert data["target"] == {"kind": "sketch_proposal", "id": proposal_id,
                              "version": target.proposal_version, "hash": target.content_sha256}
    projection = h.service.projection(TEACHER, proposal_id)
    assert projection["pipeline_state"] == "approved"
    assert projection["approval_ref"] == data["record"]["review_id"]
    assert projection["moderation_state"] == "passed"
    assert h.chain.service.get_record(TEACHER, proposal_id) == record_before  # 04 untouched


def test_rv_p02_only_reviewed_audience_receives(h: SketchReviewHarness) -> None:
    proposal_id = h.pending(level=LEVEL, group=True)
    h.moderate(proposal_id)
    h.review(proposal_id, "approve", participants=(CHILD_A,), groups=(GROUP,))
    from sketch2life.infrastructure.assistance.harness import DEVICE_GB
    assert h.service.child_payload(DEVICE_A, proposal_id)["status"] == "available"
    assert h.service.child_payload(DEVICE_GB, proposal_id)["status"] != "available"


def test_rv_p03_replay_and_semantic_duplicate(h: SketchReviewHarness) -> None:
    proposal_id = h.pending()
    h.moderate(proposal_id)
    etag = h.etag(proposal_id)
    first = h.review(proposal_id, "approve", key="key_fx_dup", etag=etag)
    replay = h.review(proposal_id, "approve", key="key_fx_dup", etag=etag)
    assert replay.replayed and replay.status == first.status
    assert {k: v for k, v in replay.data.items() if k != "replayed"} == {
        k: v for k, v in first.data.items() if k != "replayed"}
    duplicate = h.review(proposal_id, "approve", key="key_fx_dup_2")  # fresh ETag
    assert duplicate.status == 200 and duplicate.data["semantic_duplicate"] is True
    assert duplicate.data["record"]["review_id"] == first.data["record"]["review_id"]
    assert len(_entries(h, proposal_id)) == 1


@pytest.mark.parametrize("decision", ["reject", "request_changes"])
def test_rv_p04_reject_and_request_changes_recorded(h: SketchReviewHarness,
                                                     decision: str) -> None:
    proposal_id = h.pending()
    h.moderate(proposal_id)
    result = h.review(proposal_id, decision)
    assert result.status == 201 and result.data["decision"] == decision
    queue = h.service.queue_item(TEACHER, proposal_id)
    assert queue["current_decision"] == decision and queue["version_terminal"] is True
    assert h.service.child_payload(DEVICE_A, proposal_id)["status"] == "unavailable"


def test_rv_p05_approve_then_reject_same_key_revokes(h: SketchReviewHarness) -> None:
    proposal_id = h.pending()
    h.moderate(proposal_id)
    approve = h.review(proposal_id, "approve")
    assert h.service.child_payload(DEVICE_A, proposal_id)["status"] == "available"
    h.review(proposal_id, "reject")
    assert _entries(h, proposal_id)[approve.data["record"]["review_id"]] is EntryState.REVOKED
    assert h.service.child_payload(DEVICE_A, proposal_id)["status"] == "unavailable"


def _revise(h: SketchReviewHarness, proposal_id: str, level: str) -> None:
    proposal = h.chain.proposal(proposal_id)
    h.chain.service.revise_level(ReviseLevelCommand(
        TEACHER, proposal_id, h.key(), proposal.etag(), level))
    h.chain.run_sketch(proposal_id)


def test_rv_p06_new_version_reviewable_after_reject(h: SketchReviewHarness) -> None:
    proposal_id = h.pending()
    h.moderate(proposal_id)
    h.review(proposal_id, "reject")
    _revise(h, proposal_id, LEVEL)
    v2 = h.target(proposal_id)
    assert v2.proposal_version == 2 and v2.reviewable
    h.moderate(proposal_id)
    assert h.review(proposal_id, "approve").status == 201
    assert h.service.child_payload(DEVICE_A, proposal_id)["status"] == "available"


def test_rv_p07_views_and_composed_projection_conform(h: SketchReviewHarness) -> None:
    proposal_id = h.pending()
    h.moderate(proposal_id)
    h.review(proposal_id, "approve")
    projection = h.service.projection(TEACHER, proposal_id)
    assert check_shape("DATA-23", projection) == []
    assert SHAPE_SPECS["DATA-23"].owner_card == "BE2-04"


def test_rv_p08_audit_sample_without_content(h: SketchReviewHarness) -> None:
    proposal_id = h.pending()
    h.moderate(proposal_id)
    h.review(proposal_id, "approve")
    audit = h.store.snapshot().audit
    assert len(audit) == 1 and audit[0].decision == "approve"
    assert "Fixture prompt" not in repr(audit)


def test_rv_p09_text_only_fences_result_document(h: SketchReviewHarness) -> None:
    proposal_id = h.pending(level=LEVEL)
    target = h.target(proposal_id)
    assert target.asset is None and target.result_document is not None
    scopes = h.tokens.scopes(target, TEACHER)
    assert f"artifact:{target.result_document.artifact_ref}" in scopes


def test_rv_p10_reject_policy_change_then_new_version_approved(h: SketchReviewHarness) -> None:
    proposal_id = h.pending()
    h.moderate(proposal_id)
    h.review(proposal_id, "reject")
    assert h.policy.snapshot is not None
    h.publish_review_policy(replace(h.policy.snapshot, version="2"))
    h.service.refresh(proposal_id, ORG)
    _revise(h, proposal_id, LEVEL)
    h.moderate(proposal_id)
    assert h.review(proposal_id, "approve").status == 201
    assert len(h.store.snapshot().markers) == 1  # v1 marker stays


# ------------------------------------------------------------------ negative
def test_rv_n03_blocked_moderation_has_no_bypass(h: SketchReviewHarness) -> None:
    proposal_id = h.pending(unsafe=True)
    refs = set(h.target(proposal_id).ref_set)
    record = h.moderate(proposal_id)
    assert record.outcome is ModerationOutcome.BLOCKED  # type: ignore[attr-defined]
    assert _error(h.review, proposal_id, "approve").code == "INVALID_STATE"
    assert h.service.projection(TEACHER, proposal_id)["pipeline_state"] == "blocked_unsafe"
    snapshot = h.store.snapshot()
    assert len(snapshot.quarantine) == 1 and not snapshot.delivered
    assert not h.chain.raw_artifacts.quarantined  # sink not called inside the unit
    h.artifacts._port.fail_next_quarantine = True  # type: ignore[attr-defined]
    assert h.service.deliver_quarantine() == 0  # sink failure: intent stays pending
    assert h.service.deliver_quarantine() == 1
    assert h.service.deliver_quarantine() == 0  # idempotent
    assert set(h.chain.raw_artifacts.quarantined) == refs


def test_rv_n03b_blocked_detected_on_approve_without_prior_moderation(
    h: SketchReviewHarness,
) -> None:
    proposal_id = h.pending(unsafe=True)
    assert _error(h.review, proposal_id, "approve").code == "INVALID_STATE"
    snapshot = h.store.snapshot()
    assert len(snapshot.moderation) == 1 and len(snapshot.quarantine) == 1
    assert not snapshot.entries


def test_rv_n04_admin_device_and_no_preset_path(h: SketchReviewHarness) -> None:
    proposal_id = h.pending()
    h.moderate(proposal_id)
    assert _error(h.review, proposal_id, principal=ADMIN, etag="x").code == "FORBIDDEN_SCOPE"
    assert _error(h.review, proposal_id, principal=DEVICE_A,
                  etag="x").code == "RESOURCE_NOT_FOUND"
    public = {name for name in dir(h.service) if not name.startswith("_")}
    assert public == {"apply_target_notice", "child_payload", "deliver_quarantine",
                      "eligibility", "moderate", "projection", "queue_item", "record_review",
                      "refresh"}


def test_rv_n05_other_class_and_other_org_are_not_found(h: SketchReviewHarness) -> None:
    proposal_id = h.pending()
    for principal in (OTHER_CLASS_TEACHER, OUTSIDER):
        assert _error(h.review, proposal_id, principal=principal,
                      etag="x").code == "RESOURCE_NOT_FOUND"
        assert _error(h.service.queue_item, principal,
                      proposal_id).code == "RESOURCE_NOT_FOUND"


def test_rv_n06_if_match_required_and_current(h: SketchReviewHarness) -> None:
    proposal_id = h.pending()
    h.moderate(proposal_id)
    assert _error(h.review, proposal_id, etag=None).code == "PRECONDITION_REQUIRED"
    old = h.etag(proposal_id)
    h.review(proposal_id, "approve")
    stale = _error(h.review, proposal_id, "reject", etag=old)
    assert stale.code == "STALE_AGGREGATE" and stale.status == 412
    assert stale.current_revisions["decision_revision"] == 1
    sketch_etag = h.chain.proposal(proposal_id).etag()
    assert _error(h.review, proposal_id, etag=sketch_etag).code == "STALE_AGGREGATE"


def test_rv_n07_target_mismatch_and_path(h: SketchReviewHarness) -> None:
    proposal_id = h.pending()
    h.moderate(proposal_id)
    target = h.target(proposal_id)
    wrong = h.command(proposal_id, target=replace(target, content_sha256="0" * 64))
    assert _error(h.review, proposal_id, body=wrong).code == "STALE_CONTEXT"
    wrong_ctx = h.command(proposal_id, target=replace(target, context_revision=99))
    assert _error(h.review, proposal_id, body=wrong_ctx).code == "STALE_CONTEXT"
    other = h.command(proposal_id).model_copy(update={"target_id": "sketch_fx9999"})
    assert _error(h.review, proposal_id, body=other).code == "FIELD_VALIDATION_FAILED"


def test_rv_n08_reason_required_and_generic_context_refused(h: SketchReviewHarness) -> None:
    proposal_id = h.pending()
    h.moderate(proposal_id)
    body = h.command(proposal_id, "reject").model_dump_json().replace(
        '"reason":"Fixture reason for reject"', '"reason":null')
    assert _error(h.review, proposal_id, body=body).code == "FIELD_VALIDATION_FAILED"
    blank = h.command(proposal_id, "reject", reason="   ")
    assert _error(h.review, proposal_id, body=blank).code == "FIELD_VALIDATION_FAILED"
    extra = h.command(proposal_id).model_dump_json()[:-1] + ',"unknown":1}'
    assert _error(h.review, proposal_id, body=extra).code == "FIELD_NOT_ALLOWED"


def test_rv_n09_audience_and_consent(h: SketchReviewHarness) -> None:
    proposal_id = h.pending()
    h.moderate(proposal_id)
    assert _error(h.review, proposal_id,
                  participants=(CHILD_B,)).code == "FIELD_VALIDATION_FAILED"
    assert _error(h.review, proposal_id,
                  consent=((CHILD_A, 9),)).code == "STALE_CONTEXT"
    h.context.sessions[(ORG, h.target(proposal_id).session_id)].consent_effective.discard(CHILD_A)
    assert _error(h.review, proposal_id).code == "CONSENT_REQUIRED"


def test_rv_n10_target_not_pending(h: SketchReviewHarness) -> None:
    proposal_id = h.pending()
    h.revoke_producer_consent()
    assert h.target(proposal_id).pipeline_state == "stale"  # 04 public revalidation
    etag = h.etag(proposal_id)
    assert _error(h.review, proposal_id, etag=etag).code == "INVALID_STATE"


def test_rv_n12_payload_mismatch_and_replay_after_scope_loss(h: SketchReviewHarness) -> None:
    proposal_id = h.pending()
    h.moderate(proposal_id)
    etag = h.etag(proposal_id)
    h.review(proposal_id, "approve", key="key_fx_n12", etag=etag)
    assert _error(h.review, proposal_id, "reject", key="key_fx_n12",
                  etag=etag).code == "IDEMPOTENCY_PAYLOAD_MISMATCH"
    del h.authority.teachers[TEACHER.principal_id]
    assert _error(h.review, proposal_id, "approve", key="key_fx_n12",
                  etag=etag).code == "RESOURCE_NOT_FOUND"


def test_rv_n12b_malformed_key(h: SketchReviewHarness) -> None:
    proposal_id = h.pending()
    for key in ("", "k" * 121):
        command = ReviewCommand(TEACHER, proposal_id, key, "x", h.command(proposal_id))
        assert _error(h.service.record_review, command).code == "MALFORMED_REQUEST"


def test_rv_n13_policy_unresolved_and_policy_change_stales(h: SketchReviewHarness) -> None:
    proposal_id = h.pending()
    h.moderate(proposal_id)
    approve = h.review(proposal_id, "approve")
    assert h.policy.snapshot is not None
    h.publish_review_policy(replace(h.policy.snapshot, version="2"))
    assert h.service.child_payload(DEVICE_A, proposal_id)["status"] != "available"
    assert h.service.refresh(proposal_id, ORG) == (approve.data["record"]["review_id"],)
    h.publish_review_policy(None)
    assert _error(h.review, proposal_id).code == "POLICY_UNRESOLVED"


@pytest.mark.parametrize("decision", ["reject", "request_changes"])
def test_rv_n16_terminal_blocks_reapproval(h: SketchReviewHarness, decision: str) -> None:
    proposal_id = h.pending()
    h.moderate(proposal_id)
    h.review(proposal_id, decision)
    assert _error(h.review, proposal_id, "approve").code == "INVALID_STATE"
    assert h.service.child_payload(DEVICE_A, proposal_id)["status"] == "unavailable"


@pytest.mark.parametrize("decision", ["reject", "request_changes"])
def test_rv_n18_n19_terminal_survives_05_policy_stale(h: SketchReviewHarness,
                                                      decision: str) -> None:
    proposal_id = h.pending()
    h.moderate(proposal_id)
    first = h.review(proposal_id, decision)
    assert h.policy.snapshot is not None
    h.publish_review_policy(replace(h.policy.snapshot, version="2"))
    stale = h.service.refresh(proposal_id, ORG)
    assert stale == (first.data["record"]["review_id"],)
    assert h.target(proposal_id).reviewable  # 04 still pending v1/H
    assert _error(h.review, proposal_id, "approve").code == "INVALID_STATE"  # fresh ETag
    assert all(e.decision != "approve" for e in h.store.snapshot().entries[proposal_id])
    assert h.service.child_payload(DEVICE_A, proposal_id)["status"] == "unavailable"


def test_rv_n20_other_audience_and_context_keys_still_terminal(h: SketchReviewHarness) -> None:
    proposal_id = h.pending(level=LEVEL, group=True)
    h.moderate(proposal_id)
    h.review(proposal_id, "reject", participants=(CHILD_A,), groups=(GROUP,))
    assert _error(h.review, proposal_id, participants=(CHILD_B,),
                  groups=(GROUP,)).code == "INVALID_STATE"
    h.bump_audience_revision()
    assert _error(h.review, proposal_id, participants=(CHILD_B,),
                  groups=(GROUP,)).code == "INVALID_STATE"


def test_rv_n23_request_changes_then_reject_same_key(h: SketchReviewHarness) -> None:
    proposal_id = h.pending()
    h.moderate(proposal_id)
    rc = h.review(proposal_id, "request_changes")
    marker_before = dict(h.store.snapshot().markers)
    reject = h.review(proposal_id, "reject")  # fresh ETag, new key, same exact key
    queue = h.service.queue_item(TEACHER, proposal_id)
    assert queue["current_decision"] == "reject"
    assert h.service.projection(TEACHER, proposal_id)["pipeline_state"] == "rejected"
    assert queue["terminal_first_decision"] == "request_changes"
    assert h.store.snapshot().markers == marker_before
    states = _entries(h, proposal_id)
    assert states[rc.data["record"]["review_id"]] is EntryState.REVOKED
    assert states[reject.data["record"]["review_id"]] is EntryState.EFFECTIVE
    assert h.service.child_payload(DEVICE_A, proposal_id)["status"] == "unavailable"
    assert _error(h.review, proposal_id, "approve").code == "INVALID_STATE"


@pytest.mark.parametrize("decision", ["reject", "request_changes"])
def test_rv_n24_no_current_entry_never_reopens(h: SketchReviewHarness, decision: str) -> None:
    proposal_id = h.pending()
    h.moderate(proposal_id)
    h.review(proposal_id, decision)
    assert h.policy.snapshot is not None
    h.publish_review_policy(replace(h.policy.snapshot, version="2"))
    h.service.refresh(proposal_id, ORG)
    queue = h.service.queue_item(TEACHER, proposal_id)
    assert queue["current_decision"] is None and queue["version_terminal"] is True
    assert queue["approve_allowed"] is False and queue["pipeline_state"] != "approved"
    assert _error(h.review, proposal_id, "approve").code == "INVALID_STATE"
    assert h.service.child_payload(DEVICE_A, proposal_id)["status"] == "unavailable"
    markers = dict(h.store.snapshot().markers)
    renewed = h.review(proposal_id, "reject")
    queue = h.service.queue_item(TEACHER, proposal_id)
    assert queue["current_decision"] == "reject"
    assert renewed.data["record"]["state"] == "effective"
    assert h.store.snapshot().markers == markers


def test_queue_hides_content_when_blocked_or_rejected(h: SketchReviewHarness) -> None:
    proposal_id = h.pending()
    queue = h.service.queue_item(TEACHER, proposal_id)
    assert queue["text_or_question"] is not None  # pending, not blocked: Teacher preview
    h.moderate(proposal_id)
    h.review(proposal_id, "reject")
    assert h.service.projection(TEACHER, proposal_id)["text_or_question"] is None
    assert CHILD_C not in h.target(proposal_id).audience
