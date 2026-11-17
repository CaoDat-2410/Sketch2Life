"""BE2-03 A1.1 domain: transitions (D2), monotonic budget (§9.1), digest/identity (§8.3)."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from sketch2life.domain.assistance import (
    ActorKind,
    AssistanceRequest,
    AssistanceRuleViolation,
    CheckpointRef,
    DeviceStatus,
    InvalidAssistanceTransition,
    MemberFact,
    RequestReason,
    RequestStatus,
    ReservationState,
    ResolvedFacts,
    Settlement,
    SourcePin,
    StatusReason,
    TargetKind,
    TargetScope,
    audience_refusal,
    consume,
    link_job,
    normalize_child_intent,
    semantic_identity,
    settle,
    terminate,
)
from sketch2life.infrastructure.assistance.harness import build_assistance_harness

NOW = datetime(2026, 10, 17, 13, 0, tzinfo=UTC)
SHA = "a" * 64


def member(pid: str, months: int | None = 60, *, consent: bool = True, purpose: bool = True,
           age_revision: int = 1, consent_revision: int = 1) -> MemberFact:
    return MemberFact(pid, months, f"age_{pid}", age_revision, f"consent_{pid}",
                      consent_revision, consent, purpose)


def facts(**changes: object) -> ResolvedFacts:
    base = ResolvedFacts(
        organization_id="org", class_id="class", session_id="session", canvas_id="canvas",
        group_id="group", roster_revision=1, target=TargetScope(TargetKind.GROUP, "group"),
        region_id=None, region_policy_revision=1, contributor_participant_id="p_a",
        audience=("p_a", "p_b"), members=(member("p_a"), member("p_b", 120)),
        purpose_code="purpose", age_policy_ref="age-policy", policy_id="policy",
        policy_version="1", context_revision=3,
        source=SourcePin("snap", "cp", 1, 40, SHA, "render", "b" * 64, "c" * 64),
    )
    return replace(base, **changes)  # type: ignore[arg-type]


def identity(f: ResolvedFacts, **changes: object) -> str:
    args: dict[str, object] = {
        "digest": f.digest(), "checkpoint_ref": CheckpointRef("cp", 1, 40, SHA),
        "requested_level": "level", "requester": ActorKind.TEACHER,
        "reason": RequestReason.TEACHER_REQUEST, "child_intent": None, **changes,
    }
    return semantic_identity(f, **args)  # type: ignore[arg-type]


@pytest.fixture
def request_() -> AssistanceRequest:
    h = build_assistance_harness(auto_schedule=False)
    return h.submit().request


def test_digest_and_identity_are_deterministic_and_bind_owner_facts() -> None:
    base = facts()
    assert base.digest() == facts().digest()
    # A1-N23/N24/N25 at domain level: same scalar context revision, different facts.
    moved = [
        facts(audience=("p_a", "p_c"), members=(member("p_a"), member("p_c", 100))),
        facts(members=(member("p_a", 61, age_revision=2), member("p_b", 120))),
        facts(members=(member("p_a", consent_revision=2), member("p_b", 120))),
        facts(source=replace(base.source, render_sha256="d" * 64, input_hash="e" * 64)),
        facts(roster_revision=2),
    ]
    for other in moved:
        assert other.context_revision == base.context_revision
        assert other.digest() != base.digest()
        assert identity(other) != identity(base)


def test_semantic_identity_excludes_operation_identities() -> None:
    base = facts()
    # Requester principal, keys, client ids and timestamps are not inputs at all; the reason
    # class (teacher vs device) and the child intent hash are.
    assert identity(base) == identity(base, reason=RequestReason.EXPLICIT_HELP_SIGNAL)
    assert identity(base) != identity(base, requester=ActorKind.DEVICE)
    assert identity(base, child_intent="a cat") != identity(base, child_intent="a dog")
    assert identity(base) != identity(base, requested_level="level2")


def test_audience_refusal_checks_each_member_without_averaging() -> None:
    audience = ("p_a", "p_b")
    assert audience_refusal(audience, (member("p_a"), member("p_b", 120))) is None
    # Mean of 35 and 156 months is in range; each member is checked separately.
    assert audience_refusal(audience, (member("p_a", 35), member("p_b", 156))) == (
        "AGE_NOT_SUPPORTED")
    assert audience_refusal(audience, (member("p_a"), member("p_b", None))) == (
        "AGE_NOT_SUPPORTED")
    assert audience_refusal(audience, (member("p_a"), member("p_b", consent=False))) == (
        "CONSENT_REQUIRED")
    assert audience_refusal(audience, (member("p_a"), member("p_b", purpose=False))) == (
        "CONSENT_REQUIRED")
    assert audience_refusal(("p_a", "p_a"), (member("p_a"), member("p_a"))) == (
        "AUDIENCE_DUPLICATE")
    assert audience_refusal(("p_a",), (member("p_a", 36),)) is None
    assert audience_refusal(("p_a",), (member("p_a", 155),)) is None


def test_child_intent_is_bounded_and_rejects_control_text() -> None:
    assert normalize_child_intent(None) is None
    assert normalize_child_intent("a cat") == "a cat"
    with pytest.raises(AssistanceRuleViolation):
        normalize_child_intent("x" * 4001)
    with pytest.raises(AssistanceRuleViolation):
        normalize_child_intent("bad\x00text")


def test_revision_moves_only_on_invalidating_transitions(request_: AssistanceRequest) -> None:
    """D2: link/hand-off keep the pinned revision; cancel/stale bump it."""

    linked = link_job(request_, "job_1", NOW)
    assert linked.request_revision == request_.request_revision
    assert linked.record_version == request_.record_version + 1
    cancelled = terminate(linked, RequestStatus.CANCELLED, StatusReason.CANCELLED_BY_TEACHER,
                          NOW)
    assert cancelled.request_revision == linked.request_revision + 1
    assert cancelled.etag() == f'"assistance:{request_.assistance_id}:2"'
    with pytest.raises(InvalidAssistanceTransition):
        terminate(cancelled, RequestStatus.STALE, StatusReason.CONTEXT_CHANGED, NOW)
    with pytest.raises(InvalidAssistanceTransition):
        link_job(cancelled, "job_2", NOW)


def test_budget_is_monotonic_and_release_needs_settlement(request_: AssistanceRequest) -> None:
    """§9.1: consumed never returns; held releases only when settled with no start."""

    later = NOW + timedelta(seconds=1)
    assert request_.reservation is ReservationState.HELD
    consumed = consume(request_, later)
    assert consume(consumed, later) is consumed
    with pytest.raises(InvalidAssistanceTransition):
        settle(consumed, later, any_started=False)  # not terminal yet
    cancelled = terminate(consumed, RequestStatus.CANCELLED,
                          StatusReason.CANCELLED_BY_TEACHER, later)
    settled = settle(cancelled, later, any_started=False)
    assert settled.reservation is ReservationState.CONSUMED  # consumed stays consumed
    assert settled.settlement is Settlement.SETTLED

    held = terminate(request_, RequestStatus.CANCELLED, StatusReason.CANCELLED_BY_CHILD, later)
    released = settle(held, later, any_started=False)
    assert released.reservation is ReservationState.RELEASED
    with pytest.raises(InvalidAssistanceTransition):
        consume(released, later)
    started = settle(held, later, any_started=True)
    assert started.reservation is ReservationState.CONSUMED


def test_device_status_never_implies_output_availability(request_: AssistanceRequest) -> None:
    assert request_.device_status() is DeviceStatus.PENDING
    cancelled = terminate(request_, RequestStatus.CANCELLED,
                          StatusReason.CANCELLED_BY_CHILD, NOW)
    assert cancelled.device_status() is DeviceStatus.CANCELLED
    stale = terminate(request_, RequestStatus.STALE, StatusReason.CONTEXT_CHANGED, NOW)
    assert stale.device_status() is DeviceStatus.UNAVAILABLE


def test_status_reason_invariant(request_: AssistanceRequest) -> None:
    with pytest.raises(AssistanceRuleViolation):
        replace(request_, status_reason=StatusReason.CONTEXT_CHANGED)
    with pytest.raises(AssistanceRuleViolation):
        replace(request_, status=RequestStatus.CANCELLED)
