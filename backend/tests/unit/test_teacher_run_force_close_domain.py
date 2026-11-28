from __future__ import annotations

import pytest

from sketch2life.application.ports.story_run_lifecycle import CANCEL_ELIGIBLE_STATES
from sketch2life.domain.teacher_run_force_close import (
    FORCE_CLOSE_ELIGIBLE_STATES,
    StoryRunForceCloseRuleError,
    build_force_close_receipt_identity,
    force_close_transition,
    normalize_force_close_reason,
)

RUN_ID = "4be7a402-dbab-4977-bd1a-63d4b580cf08"


def test_force_close_eligibility_matches_locked_nonterminal_story_states() -> None:
    assert FORCE_CLOSE_ELIGIBLE_STATES == CANCEL_ELIGIBLE_STATES


def _identity(**changes: object):
    values: dict[str, object] = {
        "principal_ref": "manager-subject",
        "organization_id": "org-1",
        "run_id": RUN_ID,
        "expected_revision": 7,
        "reason": " Teacher assignment changed ",
        "idempotency_key": "force-close-1",
    }
    values.update(changes)
    return build_force_close_receipt_identity(**values)  # type: ignore[arg-type]


def test_force_close_reason_is_trimmed_and_bounded_without_controls() -> None:
    assert normalize_force_close_reason("  approved reassignment  ") == "approved reassignment"
    assert len(normalize_force_close_reason("x" * 500)) == 500
    for reason in ("", "   ", "x" * 501, "line\nbreak", "tab\there"):
        with pytest.raises(StoryRunForceCloseRuleError) as raised:
            normalize_force_close_reason(reason)
        assert raised.value.code == "INVALID_REQUEST"


def test_force_close_fingerprint_binds_principal_target_revision_and_reason() -> None:
    baseline = _identity()
    assert len(baseline.idempotency_scope_ref) == 64
    assert len(baseline.idempotency_key_sha256) == 64
    assert len(baseline.request_fingerprint_sha256) == 64
    assert baseline.idempotency_scope_ref == _identity().idempotency_scope_ref

    for change in (
        {"principal_ref": "other-manager"},
        {"organization_id": "other-org"},
        {"run_id": "b5d5ccf5-9e10-4851-a6a2-65d215ae6c32"},
        {"expected_revision": 8},
        {"reason": "different reason"},
    ):
        assert (
            _identity(**change).request_fingerprint_sha256
            != baseline.request_fingerprint_sha256
        )

    assert _identity(principal_ref="other-manager").idempotency_scope_ref != (
        baseline.idempotency_scope_ref
    )
    assert _identity(run_id="b5d5ccf5-9e10-4851-a6a2-65d215ae6c32").idempotency_scope_ref != (
        baseline.idempotency_scope_ref
    )
    assert _identity(idempotency_key="force-close-2").idempotency_key_sha256 != (
        baseline.idempotency_key_sha256
    )


@pytest.mark.parametrize("run_state", sorted(FORCE_CLOSE_ELIGIBLE_STATES))
def test_force_close_advances_revision_and_version_once_for_each_eligible_state(
    run_state: str,
) -> None:
    transition = force_close_transition(
        run_state=run_state,
        active_owner_teacher_id="teacher-account",
        expected_revision=7,
        current_revision=7,
        current_version=11,
    )
    assert (transition.run_state, transition.revision, transition.version) == (
        "ABANDONED",
        8,
        12,
    )


@pytest.mark.parametrize(
    ("run_state", "active_owner_teacher_id"),
    [
        ("COMPLETED", "teacher-account"),
        ("FAILED", "teacher-account"),
        ("ABANDONED", "teacher-account"),
        ("DELETE_PENDING", "teacher-account"),
        ("DELETED", "teacher-account"),
        ("SCRIPT_REVIEW", None),
    ],
)
def test_force_close_rejects_terminal_deletion_and_unlocked_runs(
    run_state: str, active_owner_teacher_id: str | None
) -> None:
    with pytest.raises(StoryRunForceCloseRuleError) as raised:
        force_close_transition(
            run_state=run_state,
            active_owner_teacher_id=active_owner_teacher_id,
            expected_revision=1,
            current_revision=1,
            current_version=1,
        )
    assert raised.value.code == "INVALID_STATE_TRANSITION"


def test_force_close_rejects_a_stale_revision_with_current_revision() -> None:
    with pytest.raises(StoryRunForceCloseRuleError) as raised:
        force_close_transition(
            run_state="SCRIPT_REVIEW",
            active_owner_teacher_id="teacher-account",
            expected_revision=6,
            current_revision=7,
            current_version=11,
        )
    assert raised.value.code == "STALE_REVISION"
    assert raised.value.current_version == 7


def test_force_close_rejects_non_ascii_or_non_string_idempotency_keys() -> None:
    for key in ("has space", "ümlaut", "", "x" * 129, None):
        with pytest.raises(StoryRunForceCloseRuleError) as raised:
            _identity(idempotency_key=key)
        assert raised.value.code == "INVALID_REQUEST"
