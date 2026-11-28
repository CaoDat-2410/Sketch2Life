from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException

from sketch2life.domain.teacher_assignment_transfer import (
    TransferAction,
    TransferEnvelope,
    TransferProgress,
    TransferState,
    TransferStateError,
    assert_same_envelope,
    replace_progress,
    transition,
)
from sketch2life.interfaces.http.routers import be1_common

_NOW = datetime(2026, 11, 25, tzinfo=UTC)


def _progress() -> TransferProgress:
    return TransferProgress(
        state=TransferState.TRANSFER_PENDING,
        state_revision=1,
        attempt_count=0,
        last_failure_code=None,
        story_receipt_ref=None,
        updated_at=_NOW,
        finalized_at=None,
    )


def _envelope() -> TransferEnvelope:
    return TransferEnvelope(
        transfer_id="11111111-1111-4111-8111-111111111111",
        organization_id="synthetic-org",
        class_id="synthetic-class",
        action=TransferAction.REASSIGN,
        principal_ref="synthetic-manager",
        old_subject="synthetic-old-subject",
        new_subject="synthetic-new-subject",
        old_assignment_id="22222222-2222-4222-8222-222222222222",
        new_assignment_id="33333333-3333-4333-8333-333333333333",
        expected_revision=1,
        fenced_revision=2,
        operation_scope="POST /classes/synthetic-class/assignments",
        idempotency_key="transfer-key-1",
        fingerprint="a" * 64,
        created_at=_NOW,
    )


def test_transfer_state_machine_allows_only_declared_transitions() -> None:
    pending = replace_progress(
        _progress(),
        target=TransferState.RECONCILE_REQUIRED,
        updated_at=_NOW + timedelta(seconds=1),
        failure_code="STORY_TRANSFER_UNCERTAIN",
    )
    completed = replace_progress(
        pending,
        target=TransferState.COMPLETED,
        updated_at=_NOW + timedelta(seconds=2),
        story_receipt_ref="44444444-4444-4444-8444-444444444444",
        finalized_at=_NOW + timedelta(seconds=2),
    )
    assert (pending.state, pending.state_revision, pending.attempt_count) == (
        TransferState.RECONCILE_REQUIRED,
        2,
        1,
    )
    assert (completed.state, completed.state_revision, completed.attempt_count) == (
        TransferState.COMPLETED,
        3,
        2,
    )
    assert completed.story_receipt_ref == "44444444-4444-4444-8444-444444444444"


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (TransferState.TRANSFER_PENDING, TransferState.TRANSFER_PENDING),
        (TransferState.COMPLETED, TransferState.RECONCILE_REQUIRED),
        (TransferState.OFFBOARDED, TransferState.COMPLETED),
        (TransferState.COMPENSATED_CONFLICT, TransferState.TRANSFER_PENDING),
    ],
)
def test_transfer_state_machine_rejects_undeclared_transitions(
    current: TransferState, target: TransferState
) -> None:
    with pytest.raises(TransferStateError):
        transition(
            current,
            target,
            state_revision=1,
            updated_at=_NOW,
            previous_updated_at=_NOW,
            attempt_count=1,
            previous_attempt_count=0,
        )


def test_transfer_progress_rejects_time_or_receipt_regression() -> None:
    progress = replace_progress(
        _progress(),
        target=TransferState.RECONCILE_REQUIRED,
        updated_at=_NOW + timedelta(seconds=1),
        story_receipt_ref="44444444-4444-4444-8444-444444444444",
    )
    with pytest.raises(TransferStateError):
        replace_progress(
            progress,
            target=TransferState.RECONCILE_REQUIRED,
            updated_at=_NOW,
        )
    with pytest.raises(TransferStateError):
        replace_progress(
            progress,
            target=TransferState.RECONCILE_REQUIRED,
            updated_at=_NOW + timedelta(seconds=2),
            story_receipt_ref="55555555-5555-4555-8555-555555555555",
        )


def test_transfer_envelope_key_immutable() -> None:
    before = _envelope()
    assert_same_envelope(before, _envelope())
    changed = replace(before, idempotency_key="other-key")
    with pytest.raises(TransferStateError):
        assert_same_envelope(before, changed)


def test_class_writes_are_refused_while_a_transfer_is_pending(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(be1_common, "class_transfer_is_pending", lambda *_args, **_kwargs: True)
    with pytest.raises(HTTPException) as exc:
        be1_common.require_no_pending_class_transfer(
            object(),  # type: ignore[arg-type]
            organization_id="synthetic-org",
            class_id="synthetic-class",
        )
    assert exc.value.status_code == 409
    assert exc.value.detail["code"] == "RESOURCE_CONFLICT"
