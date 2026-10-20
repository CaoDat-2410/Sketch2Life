"""MEMORY/ASSUMED lifecycle/current gates/result ACK; not actual BE1/12 integration."""

from contextlib import contextmanager
from dataclasses import replace

import pytest

from sketch2life.application.activity_execution import Command, event_id
from sketch2life.domain.activity_execution.model import (
    Action,
    Adaptations,
    ChildAge,
    Confirmation,
    State,
)
from sketch2life.domain.knowledge_video.model import VideoError
from tests.activity_execution_fixtures import actor, execute, harness, ref, select


def ready(h):
    execute(h)
    return execute(h, Action.CONFIRM).assignment


def terminal(h, action=Action.FINISH):
    ready(h)
    if action is not Action.SKIP:
        execute(h, Action.START)
    return execute(h, action).assignment


def test_select_local_edit_prepare_each_child_start_finish_outcome_separate():
    h = harness()
    first = execute(h, edits=Adaptations(instructions="Group B local steps"))
    assert first.assignment.state is State.SELECTED and first.outcome_delivery == "not_required"
    confirmed = execute(h, Action.CONFIRM)
    assert confirmed.assignment.state is State.READY
    assert h.boundary.checked_children == ["child1", "child2"]
    execute(h, Action.START)
    result = execute(h, Action.FINISH)
    assert result.assignment.state is State.COMPLETED and result.outcome_delivery == "pending"
    assert h.boundary.checked_children == ["child1", "child2", "child1", "child2"]
    h.consumer.send.assert_not_called()
    assert len(h.store.history) == len(h.store.receipts) == 4 and len(h.store.events) == 1
    assert h.delivery.deliver(actor(), event_id(result.assignment)) == "acknowledged"
    assert len(h.accepted) == 1  # Synthetic result-reference consumer, not observation/portfolio.
    assert h.delivery.deliver(actor(), event_id(result.assignment)) == "acknowledged"
    assert h.consumer.send.call_count == 1


def test_replay_returns_current_not_stale_ready_or_reapplied_edit():
    h = harness()
    original = h.service.execute(actor(), select())
    execute(h, Action.CONFIRM)
    replay = h.service.execute(actor(), select())
    assert replay.replayed and replay.applied_revision == original.applied_revision == 1
    assert replay.assignment.state is State.READY and replay.assignment.revision == 2
    assert len(h.store.history) == 2
    h.boundary.denied = "replay"
    with pytest.raises(VideoError, match="FORBIDDEN"):
        h.service.execute(actor(), select())


@pytest.mark.parametrize("action", [Action.SKIP, Action.INTERRUPT])
def test_skip_interrupt_truthful_reason_outcome_not_completed(action):
    h = harness()
    row = terminal(h, action)
    assert row.state is (State.SKIPPED if action is Action.SKIP else State.INTERRUPTED)
    assert row.reason == "fixture reason" and len(h.store.events) == 1


@pytest.mark.parametrize("principal", ["child", "admin", "device"])
def test_no_implicit_teacher_action(principal):
    h = harness()
    with pytest.raises(VideoError, match="FORBIDDEN"):
        h.service.execute(actor(principal_id=principal), select())
    assert not h.store.rows


@pytest.mark.parametrize("phase", ["select", "prepare", "commit"])
def test_current_authority_denial_and_atomic_rollback(phase):
    h = harness()
    if phase == "prepare":
        execute(h)
    h.boundary.denied = phase
    with pytest.raises(VideoError, match="FORBIDDEN"):
        execute(h, Action.CONFIRM if phase == "prepare" else Action.SELECT)
    assert len(h.store.history) == (1 if phase == "prepare" else 0)


@pytest.mark.parametrize("bad_child", ["child1", "child2"])
def test_all_children_checked_no_average_or_first_only(bad_child):
    h = harness()
    execute(h)
    h.boundary.denied_children.add(bad_child)
    with pytest.raises(VideoError, match="POLICY_DENIED"):
        execute(h, Action.CONFIRM)
    assert next(iter(h.store.rows.values())).state is State.SELECTED


def test_mixed_age_outside_policy_cannot_confirm_even_group_average_valid():
    h = harness()
    h.boundary.audience = replace(
        h.boundary.audience, children=(ChildAge("child1", 36), ChildAge("child2", 120))
    )
    execute(h)
    with pytest.raises(VideoError, match="POLICY_DENIED"):
        execute(h, Action.CONFIRM)


@pytest.mark.parametrize("confirmation", [Confirmation(False, True), Confirmation(True, False)])
def test_unprepared_cannot_confirm_despite_policy_shape(confirmation):
    h = harness()
    execute(h)
    with pytest.raises(VideoError, match="NOT_READY"):
        execute(h, Action.CONFIRM, confirmation=confirmation)


def test_adaptation_hazard_not_self_approved_by_checkbox_and_start_rechecks():
    h = harness()
    execute(h, edits=Adaptations(materials=("hazard",)))
    with pytest.raises(VideoError, match="POLICY_DENIED"):
        execute(h, Action.CONFIRM)
    h = harness()
    ready(h)
    h.boundary.hazard = True
    with pytest.raises(VideoError, match="POLICY_DENIED"):
        execute(h, Action.START)


def test_reselection_resets_preparation_and_cas_one_winner():
    h = harness()
    before = ready(h)
    result = execute(
        h,
        Action.SELECT,
        assignment_id=before.assignment_id,
        expected_revision=before.revision,
        source_ref=before.source.source_ref,
        group_ids=before.audience.group_ids,
        edits=Adaptations(instructions="different"),
    )
    assert result.assignment.proof is None and result.assignment.state is State.PREPARATION
    with pytest.raises(VideoError, match="STALE_REVISION"):
        h.service.execute(
            actor(client_key="competing"),
            Command(
                Action.SKIP, before.assignment_id, before.revision, reason="second actor command"
            ),
        )


def test_changed_body_same_key_and_scope_denied():
    h = harness()
    h.service.execute(actor(), select())
    with pytest.raises(VideoError, match="IDEMPOTENCY_CONFLICT"):
        h.service.execute(actor(), select(edits=Adaptations(instructions="changed")))
    with pytest.raises(VideoError, match="FORBIDDEN"):
        h.service.execute(actor(organization_id="foreign"), select())


@pytest.mark.parametrize("stage", ["write", "commit"])
def test_receipt_history_event_uow_failure_does_not_partially_write(stage):
    h = harness()
    if stage == "commit":
        h.boundary.on_check = lambda a, r, p: (
            setattr(h.store, "fail", "commit") if p == "commit" else None
        )
    else:
        h.store.fail = stage
    with pytest.raises(VideoError, match="DEPENDENCY_UNAVAILABLE"):
        execute(h)
    assert not h.store.rows and not h.store.history and not h.store.receipts


def test_lost_committed_ack_original_key_recovers_no_duplicate_assignment():
    h = harness()
    original, lost = h.store.transaction, []

    @contextmanager
    def transaction(org, session):
        had = bool(h.store.rows)
        with original(org, session) as tx:
            yield tx
        if not had and h.store.rows and not lost:
            lost.append(True)
            raise RuntimeError("lost commit ACK")

    h.store.transaction = transaction
    with pytest.raises(VideoError, match="DEPENDENCY_UNAVAILABLE"):
        h.service.execute(actor(), select())
    replay = h.service.execute(actor(), select())
    assert replay.replayed and len(h.store.rows) == 1


def test_current_recall_policy_change_cannot_start_and_notice_no_public_permission():
    h = harness()
    row = ready(h)
    h.boundary.definition = replace(h.boundary.definition, definition_ref=ref("changed"))
    with pytest.raises(VideoError, match="SOURCE_INELIGIBLE"):
        execute(h, Action.START)
    with pytest.raises(VideoError, match="FORBIDDEN"):
        h.service.invalidate(actor(), row.assignment_id, row.revision, "source_recalled")
    noticed = h.service.invalidate(
        actor(principal_id="owner.notice"), row.assignment_id, row.revision, "source_recalled"
    )
    assert noticed.assignment.state is State.PREPARATION
    assert noticed.assignment.invalidated == "source_recalled"
    assert h.service.invalidate(
        actor(principal_id="owner.notice"), row.assignment_id, row.revision, "source_recalled"
    ).replayed


@pytest.mark.parametrize("mode", ["outage", "foreign", "ack-save", "lost-send-ack"])
def test_delivery_original_event_no_false_save_or_duplicate_outcome(mode):
    h = harness()
    row = terminal(h)
    original = h.consumer.send.side_effect
    if mode == "outage":
        h.consumer.send.side_effect = TimeoutError("synthetic_sensitive")
    elif mode == "foreign":
        h.consumer.send.side_effect = lambda event: replace(original(event), event_digest="f" * 64)
    elif mode == "ack-save":
        h.store.fail = "ack"
    else:

        def lost(event):
            original(event)
            raise TimeoutError("lost ACK after actual synthetic receive")

        h.consumer.send.side_effect = lost
    assert h.delivery.deliver(actor(), event_id(row)) == "pending"
    assert not h.store.acks
    h.consumer.send.side_effect, h.store.fail = original, None
    assert h.delivery.deliver(actor(), event_id(row)) == "acknowledged"
    assert len(h.accepted) == 1


def test_guard_exit_failure_not_rollback_claim_and_current_delivery_denial():
    h = harness()
    h.boundary.fail_exit = True
    with pytest.raises(VideoError, match="DEPENDENCY_UNAVAILABLE"):
        h.service.execute(actor(), select())
    assert len(h.store.rows) == 1
    h.boundary.fail_exit = False
    row = terminal(h)
    h.boundary.denied = "deliver"
    with pytest.raises(VideoError, match="FORBIDDEN"):
        h.delivery.deliver(actor(), event_id(row))
    h.consumer.send.assert_not_called()


def test_finishing_teacher_attribution_not_copied_from_original_selector():
    h = harness()
    ready(h)
    row = execute(h, Action.START).assignment
    result = h.service.execute(
        actor(principal_id="teacher2", client_key="finish.by.teacher2"),
        Command(Action.FINISH, row.assignment_id, row.revision),
    )
    event = next(iter(h.store.events.values()))
    assert result.assignment.selected_by == "teacher"
    assert event.recorded_by == "teacher2"
    assert event.fingerprint() != replace(event, recorded_by="teacher").fingerprint()


def test_old_notice_replay_after_newer_completion_keeps_actual_outcome_delivery_axis():
    h = harness()
    row = ready(h)
    notice_actor = actor(principal_id="owner.notice")
    notice = h.service.invalidate(notice_actor, row.assignment_id, row.revision, "context_refresh")
    execute(
        h,
        Action.SELECT,
        assignment_id=row.assignment_id,
        expected_revision=notice.assignment.revision,
        source_ref=row.source.source_ref,
        group_ids=row.audience.group_ids,
    )
    execute(h, Action.CONFIRM)
    execute(h, Action.START)
    done = execute(h, Action.FINISH)
    replay = h.service.invalidate(notice_actor, row.assignment_id, row.revision, "context_refresh")
    assert replay.replayed and replay.applied_revision == notice.applied_revision
    assert replay.assignment == done.assignment and replay.outcome_delivery == "pending"
