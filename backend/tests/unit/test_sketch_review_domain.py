"""BE2-05 domain: exact key, append-only entries, terminal marker (OD-07-A), D-1, D-3."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

import pytest

from sketch2life.domain.sketch_review import (
    Decision,
    EntryState,
    ModerationOutcome,
    ModerationRecord,
    ReviewAudience,
    ReviewEntry,
    ReviewHead,
    ReviewTarget,
    SketchReviewRuleViolation,
    TargetAsset,
    TerminalVersion,
    apply_decision,
    compose_projection,
    current_entry,
    mark_stale,
    marker_matches_history,
    normalize_reason,
    parse_review_etag,
    review_etag,
    review_key,
    target_identity,
)

NOW = datetime(2026, 10, 19, 9, 0, tzinfo=UTC)
H1 = "a" * 64
H2 = "b" * 64


def _target(**changes: object) -> ReviewTarget:
    values: dict[str, object] = dict(
        proposal_id="sketch_fx_1", organization_id="org_fx", record_version=4,
        review_revision=1, proposal_version=1, pipeline_state="pending_teacher_review",
        moderation_state="pending", status_reason=None, level="level_fx_2",
        display_mode="overlay", text="Fixture prompt?",
        asset=TargetAsset("artifact_fx_asset", "c" * 64, "image/png", 87),
        result_document=TargetAsset("artifact_fx_doc", "d" * 64, "application/json", 300),
        content_sha256=H1, producer={"adapter_id": "fake"}, job_id="job_fx", attempt_id="att_fx",
        session_id="session_fx", class_id="class_fx", canvas_id="canvas_fx", group_id="group_fx",
        audience=("child_a", "child_b"), contributor="child_a", purpose_code="ai_drawing",
        context_revision=3, roster_revision=1, analysis_id="analysis_fx", analysis_revision=1,
        meaning_digest="e" * 64, source_snapshot_ref="snapshot_fx", source_input_hash="f" * 64,
        policy_ref={"policy_id": "p04", "version": "1", "status": "FIXTURE"})
    values.update(changes)
    return ReviewTarget(**values)  # type: ignore[arg-type]


def _audience(*participants: str, revision: int = 5) -> ReviewAudience:
    return ReviewAudience("session_fx", ("group_fx",), participants, revision, (("child_a", 1),))


def _entry(review_id: str, revision: int, decision: Decision, *, participants: tuple[str, ...]
           = ("child_a",), version: int = 1, digest: str = H1,
           policy: str = "rp@1|p04@1") -> ReviewEntry:
    audience = _audience(*participants)
    key = review_key(proposal_id="sketch_fx_1", version=version, content_sha256=digest,
                     audience=audience, context_revision=3, policy_version=policy)
    return ReviewEntry(review_id, revision, decision,
                       None if decision is Decision.APPROVE else "Fixture reason",
                       "teacher_fx", NOW, "sketch_fx_1", version, digest, 3, audience, policy,
                       1, key)


def test_target_ref_set_includes_result_document_and_text_only() -> None:
    target = _target()
    assert target.ref_set == ("artifact_fx_asset", "artifact_fx_doc")
    text_only = _target(asset=None, display_mode="side_reference")
    assert text_only.ref_set == ("artifact_fx_doc",)  # RV-P09: text-only still fences a ref
    assert target_identity(text_only) != target_identity(target)


def test_identity_changes_with_producer_revisions_or_content() -> None:
    base = target_identity(_target())
    assert target_identity(_target(record_version=5)) != base
    assert target_identity(_target(review_revision=2)) != base
    assert target_identity(_target(content_sha256=H2)) != base
    assert target_identity(_target(text="other")) == base  # text is covered by content_sha256


def test_review_key_distinguishes_audience_consent_policy() -> None:
    a = _entry("r1", 1, Decision.APPROVE, participants=("child_a",))
    b = _entry("r2", 2, Decision.APPROVE, participants=("child_b",))
    c = _entry("r3", 3, Decision.APPROVE, policy="rp@2|p04@1")
    assert len({a.key, b.key, c.key}) == 3


def test_reject_inserts_marker_and_revokes_every_approve_of_version_d1() -> None:
    approve_a = _entry("r1", 1, Decision.APPROVE, participants=("child_a",))
    approve_b = _entry("r2", 2, Decision.APPROVE, participants=("child_b",))
    other_version = _entry("r9", 3, Decision.APPROVE, version=2, digest=H2)
    reject = _entry("r3", 4, Decision.REJECT, participants=("child_b",))
    outcome = apply_decision((approve_a, approve_b, other_version), None, reject, NOW)
    states = {e.review_id: e.state for e in outcome.entries}
    assert states == {"r1": EntryState.REVOKED, "r2": EntryState.REVOKED,
                      "r9": EntryState.EFFECTIVE, "r3": EntryState.EFFECTIVE}
    assert outcome.marker is not None and outcome.marker.first_decision is Decision.REJECT
    assert outcome.current is not None and outcome.current.review_id == "r3"


def test_approve_on_terminal_version_is_refused() -> None:
    reject = _entry("r1", 1, Decision.REQUEST_CHANGES)
    first = apply_decision((), None, reject, NOW)
    with pytest.raises(TerminalVersion):
        apply_decision(first.entries, first.marker,
                       _entry("r2", 2, Decision.APPROVE, participants=("child_b",)), NOW)


def test_request_changes_then_reject_keeps_marker_and_moves_current_d3() -> None:
    rc = _entry("r1", 1, Decision.REQUEST_CHANGES)
    first = apply_decision((), None, rc, NOW)
    reject = _entry("r2", 2, Decision.REJECT)  # same exact key
    second = apply_decision(first.entries, first.marker, reject, NOW)
    assert second.marker is None  # the original marker is kept, not replaced
    assert {e.review_id: e.state for e in second.entries} == {
        "r1": EntryState.REVOKED, "r2": EntryState.EFFECTIVE}
    assert second.current is not None and second.current.decision is Decision.REJECT
    assert first.marker is not None and first.marker.first_decision is Decision.REQUEST_CHANGES
    projection = compose_projection(_target(), current=second.current, current_applicable=True,
                                    entries=second.entries, marker=first.marker,
                                    moderation=None)
    assert (projection.pipeline_state, projection.review_decision) == ("rejected", "reject")


def test_no_current_entry_keeps_version_terminal_rv_n24() -> None:
    reject = _entry("r1", 1, Decision.REJECT)
    outcome = apply_decision((), None, reject, NOW)
    entries, changed = mark_stale(outcome.entries, frozenset({"r1"}))
    assert [e.state for e in changed] == [EntryState.STALE]
    assert current_entry(entries, (1, H1)) is None
    projection = compose_projection(_target(), current=None, current_applicable=False,
                                    entries=entries, marker=outcome.marker, moderation=None)
    assert projection.pipeline_state == "rejected"
    assert projection.review_decision is None
    assert projection.version_terminal and not projection.approve_allowed
    assert marker_matches_history(entries, outcome.marker, (1, H1))


def test_marker_history_equivalence_rv_n21() -> None:
    approve = _entry("r1", 1, Decision.APPROVE)
    first = apply_decision((), None, approve, NOW)
    assert marker_matches_history(first.entries, first.marker, (1, H1))
    rc = apply_decision(first.entries, None, _entry("r2", 2, Decision.REQUEST_CHANGES), NOW)
    assert rc.marker is not None
    assert marker_matches_history(rc.entries, rc.marker, (1, H1))
    assert not marker_matches_history(rc.entries, None, (1, H1))


def test_projection_precedence_blocked_and_approved() -> None:
    approve = _entry("r1", 1, Decision.APPROVE)
    blocked = ModerationRecord("sketch_fx_1", 1, H1, (), ModerationOutcome.BLOCKED,
                               "UNSAFE_TEXT", "rp@1", NOW)
    p = compose_projection(_target(), current=approve, current_applicable=True,
                           entries=(approve,), marker=None, moderation=blocked)
    assert p.pipeline_state == "blocked_unsafe" and p.approval_ref is None
    passed = replace(blocked, outcome=ModerationOutcome.PASSED, reason_code=None)
    p = compose_projection(_target(), current=approve, current_applicable=True,
                           entries=(approve,), marker=None, moderation=passed)
    assert (p.pipeline_state, p.approval_ref, p.moderation_state) == ("approved", "r1", "passed")
    p = compose_projection(_target(), current=approve, current_applicable=False,
                           entries=(approve,), marker=None, moderation=passed)
    assert p.pipeline_state == "pending_teacher_review" and p.approval_ref is None


def test_etag_round_trip_and_rejects_foreign_forms() -> None:
    etag = review_etag("sketch_fx_1", 2, 3, 4)
    assert parse_review_etag(etag) == ("sketch_fx_1", 2, 3, 4)
    assert parse_review_etag('"sketch-proposal:sketch_fx_1:2:3"') is None
    assert parse_review_etag("sketch-review:sketch_fx_1:2:3:4") is None


@pytest.mark.parametrize("value", ["", "   ", "x" * 129, "bad\x07reason", 5])
def test_reason_bounds(value: object) -> None:
    with pytest.raises(SketchReviewRuleViolation):
        normalize_reason(value)


def test_reason_is_nfc_and_trimmed() -> None:
    assert normalize_reason("  Café ") == "Café"
    assert len(normalize_reason("x" * 128)) == 128


def test_head_current_pointer_per_version() -> None:
    head = ReviewHead("sketch_fx_1", "org_fx").with_current((1, H1), "r1")
    head = head.with_current((2, H2), "r2").with_current((1, H1), None)
    assert head.current_entry_id((1, H1)) is None
    assert head.current_entry_id((2, H2)) == "r2"


def test_entry_invariants() -> None:
    with pytest.raises(SketchReviewRuleViolation):
        _entry("r1", 0, Decision.APPROVE)
    with pytest.raises(SketchReviewRuleViolation):
        replace(_entry("r1", 1, Decision.REJECT), reason=None)
