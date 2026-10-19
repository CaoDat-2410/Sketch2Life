"""Public 05 metadata, same-decision reads and device-bound 03 authority acceptance."""

from __future__ import annotations

from dataclasses import replace

import pytest

from sketch2life.application.ports.ai_jobs import Principal
from sketch2life.application.services.sketch_review import EligibilityDecision
from sketch2life.infrastructure.assistance.harness import (
    ADMIN,
    CANVAS_G,
    CHILD_A,
    CHILD_B,
    DEVICE_A,
    DEVICE_GA,
    DEVICE_GB,
    OTHER_CLASS_TEACHER,
    OUTSIDER,
    TEACHER,
)
from sketch2life.infrastructure.child_response.harness import (
    ChildResponseHarness,
    build_child_response_harness,
)


@pytest.fixture
def h() -> ChildResponseHarness:
    return build_child_response_harness()


def test_authorize_projects_only_allowlisted_server_metadata(h: ChildResponseHarness) -> None:
    proposal_id = h.approved()
    target = h.review.target(proposal_id)
    access = h.access.authorize(DEVICE_A, proposal_id,
                                expected_proposal_version=target.proposal_version)
    assert access is not None
    assert access.proposal_version == target.proposal_version
    assert access.content_sha256 == target.content_sha256
    assert access.participant_id == CHILD_A
    assert set(access.model_dump()) == {
        "organization_id", "class_id", "session_id", "canvas_id", "proposal_id",
        "proposal_version", "content_sha256", "participant_id", "review_ref",
    }


def test_read_uses_one_eligibility_result_and_never_calls_child_payload(
    h: ChildResponseHarness, monkeypatch: pytest.MonkeyPatch,
) -> None:
    proposal_id = h.approved()
    original = h.review.service.eligibility
    calls: list[str] = []

    def observe(principal: Principal, proposal_id: str, *, asset_ref: str | None = None,
                content_sha256: str | None = None,
                review_ref: str | None = None) -> EligibilityDecision:
        calls.append(proposal_id)
        return original(principal, proposal_id, asset_ref=asset_ref,
                        content_sha256=content_sha256, review_ref=review_ref)

    def forbidden_second_read(*args: object, **kwargs: object) -> None:
        raise AssertionError("child_payload must not select a second producer snapshot")

    monkeypatch.setattr(h.review.service, "eligibility", observe)
    monkeypatch.setattr(h.review.service, "child_payload", forbidden_second_read)
    read = h.access.read(DEVICE_A, proposal_id)
    assert read is not None and read.payload.status == "available"
    assert calls == [proposal_id]
    assert read.payload.proposal_id == read.access.proposal_id
    assert read.payload.review_ref == read.access.review_ref
    target = h.review.target(proposal_id)
    assert read.payload.text_or_question == target.text
    assert read.payload.overlay_asset_ref == (
        None if target.asset is None else target.asset.artifact_ref)


@pytest.mark.parametrize("field", ["expected_proposal_version", "review_ref", "content_sha256"])
def test_exact_version_review_and_hash_mismatch_fail_closed(
    h: ChildResponseHarness, field: str,
) -> None:
    proposal_id = h.approved()
    values = {"expected_proposal_version": 99,
              "review_ref": "review_fx_unrelated", "content_sha256": "0" * 64}
    assert h.access.authorize(DEVICE_A, proposal_id, **{field: values[field]}) is None  # type: ignore[arg-type]


def test_producer_group_audience_cannot_authorize_unreviewed_child(h: ChildResponseHarness) -> None:
    proposal_id = h.approved(group=True, participants=(CHILD_A,))
    assert h.review.target(proposal_id).audience == (CHILD_A, CHILD_B)
    assert h.access.authorize(DEVICE_GA, proposal_id) is not None
    assert h.access.read(DEVICE_GB, proposal_id) is None


def test_missing_pending_and_cross_organization_access_return_no_snapshot(
    h: ChildResponseHarness,
) -> None:
    proposal_id = h.pending()
    assert h.access.authorize(DEVICE_A, proposal_id) is None
    assert h.access.authorize(DEVICE_A, "proposal_fx_absent") is None
    assert h.access.authorize(OUTSIDER, proposal_id) is None
    assert h.access.authorize(TEACHER, proposal_id) is None


def test_eligibility_failure_never_exposes_a_partial_target(
    h: ChildResponseHarness, monkeypatch: pytest.MonkeyPatch,
) -> None:
    proposal_id = h.approved()

    def unavailable(*args: object, **kwargs: object) -> None:
        raise RuntimeError("private dependency diagnostic")

    monkeypatch.setattr(h.review.service, "eligibility", unavailable)
    assert h.access.authorize(DEVICE_A, proposal_id) is None
    assert h.access.read(DEVICE_A, proposal_id) is None


def test_allowed_turn_participant_must_match_05_participant(h: ChildResponseHarness) -> None:
    proposal_id = h.approved(group=True)
    access = h.access.authorize(DEVICE_GA, proposal_id)
    assert access is not None
    # Both fixtures independently permit their own participant; the composed decision must match.
    h.review.chain.h.authority.devices[DEVICE_GA.principal_id].participant_id = CHILD_B
    assert h.authority.new_operation(DEVICE_GA, access, "turn_fx_ga") is None


def test_device_turn_must_belong_to_pinned_canvas(h: ChildResponseHarness) -> None:
    proposal_id = h.approved(group=True)
    access = h.access.authorize(DEVICE_A, proposal_id)
    assert access is not None and access.canvas_id == CANVAS_G
    # DEVICE_A passes 05's participant/session gate but is bound to the personal canvas in 03.
    assert h.authority.new_operation(DEVICE_A, access, "turn_fx_a1") is None


@pytest.mark.parametrize("change", ["inactive", "organization", "session", "canvas", "class"])
def test_canvas_facts_are_checked_even_when_turn_authority_would_allow(
    h: ChildResponseHarness, change: str,
) -> None:
    proposal_id = h.approved()
    access = h.access.authorize(DEVICE_A, proposal_id)
    assert access is not None
    owner = h.review.chain.h.owner
    canvas = owner.canvases[access.canvas_id]
    changes: dict[str, dict[str, object]] = {
        "inactive": {"session_active": False},
        "organization": {"organization_id": "org_fx_other"},
        "session": {"session_id": "session_fx_other"},
        "canvas": {"canvas_id": "canvas_fx_other"},
        "class": {"class_id": "class_fx_other"},
    }
    owner.canvases[access.canvas_id] = replace(canvas, **changes[change])  # type: ignore[arg-type]
    assert h.authority.new_operation(DEVICE_A, access, "turn_fx_a1") is None


@pytest.mark.parametrize("change", ["null", "closed", "wrong", "revoked"])
def test_new_operation_requires_current_non_null_matching_turn(
    h: ChildResponseHarness, change: str,
) -> None:
    proposal_id = h.approved()
    access = h.access.authorize(DEVICE_A, proposal_id)
    assert access is not None
    device = h.review.chain.h.authority.devices[DEVICE_A.principal_id]
    turn_id = "turn_fx_a1"
    if change == "null":
        device.turn_id = None
    elif change == "closed":
        h.close_turn()
    elif change == "wrong":
        turn_id = "turn_fx_old"
    else:
        h.review.chain.h.authority.revoked.add(DEVICE_A.principal_id)
    assert h.authority.new_operation(DEVICE_A, access, turn_id) is None


def test_receipt_disclosure_survives_turn_close_but_not_binding_change(
    h: ChildResponseHarness,
) -> None:
    proposal_id = h.approved()
    access = h.access.authorize(DEVICE_A, proposal_id)
    assert access is not None
    h.close_turn()
    assert h.authority.can_disclose(DEVICE_A, access)
    assert h.authority.new_operation(DEVICE_A, access, "turn_fx_a1") is None
    h.rebind(DEVICE_A, CHILD_B, "turn_fx_b2")
    assert not h.authority.can_disclose(DEVICE_A, access)


def test_teacher_visibility_requires_current_teacher_class_session_assignment(
    h: ChildResponseHarness,
) -> None:
    access = h.access.authorize(DEVICE_A, h.approved())
    assert access is not None
    assert h.authority.teacher_allowed(TEACHER, access)
    for principal in (ADMIN, OTHER_CLASS_TEACHER, OUTSIDER, DEVICE_A):
        assert not h.authority.teacher_allowed(principal, access)
    h.authority.teachers.pop(TEACHER.principal_id)
    assert not h.authority.teacher_allowed(TEACHER, access)
