"""Pure assignment rules, not actual Teacher/source/age/preparation authority."""

from dataclasses import replace

import pytest

from sketch2life.domain.activity_execution.model import (
    PRESTART,
    Action,
    Adaptations,
    ChildAge,
    Confirmation,
    State,
    digest,
    effective,
)
from sketch2life.domain.knowledge_video.model import VideoError
from tests.activity_execution_fixtures import (
    NOW,
    assignment,
    audience,
    definition,
    prepared,
    proof,
    ref,
)


def row_in(state):
    if state in {State.READY, State.RUNNING, State.COMPLETED, State.INTERRUPTED}:
        return prepared(state)
    if state is State.SKIPPED:
        row = assignment()
        return row.transition(Action.SKIP, 1, NOW, reason="not performed")
    return assignment(state=state)


@pytest.mark.parametrize("state", list(State))
@pytest.mark.parametrize("action", list(Action))
def test_complete_six_action_state_matrix(state, action):
    row = row_in(state)
    allowed = (
        (action is Action.SELECT and state in PRESTART)
        or (action is Action.CONFIRM and state in PRESTART)
        or (action is Action.START and state is State.READY)
        or (action in {Action.FINISH, Action.INTERRUPT} and state is State.RUNNING)
        or (action is Action.SKIP and state in PRESTART)
    )

    def run():
        if action is Action.SELECT:
            return row.reselect(
                row.revision,
                row.source,
                Adaptations(instructions="Local steps"),
                row.audience,
                row.policy,
                NOW,
            )
        return row.transition(
            action,
            row.revision,
            NOW,
            confirmation=Confirmation(True, True)
            if action in {Action.CONFIRM, Action.START}
            else None,
            proof=proof(row) if action in {Action.CONFIRM, Action.START} else None,
            reason="not observed as success" if action in {Action.SKIP, Action.INTERRUPT} else None,
        )

    if allowed:
        after = run()
        assert after.revision == row.revision + 1 and after.source == row.source
    else:
        with pytest.raises(VideoError, match="INVALID_TRANSITION"):
            run()


def test_local_edits_immutable_master_and_ready_confirmation_reset():
    row = prepared()
    edits = Adaptations(instructions="Group B steps", materials=("safe local paper",))
    after = row.reselect(row.revision, row.source, edits, row.audience, row.policy, NOW)
    assert row.source == after.source == definition()
    assert effective(after.source, after.edits).instructions == "Group B steps"
    assert row.source.instructions == "Observe together"
    assert after.state is State.PREPARATION and after.proof is after.confirmation is None
    with pytest.raises(VideoError):
        after.transition(
            Action.START,
            after.revision,
            NOW,
            confirmation=Confirmation(True, True),
            proof=proof(after),
        )


@pytest.mark.parametrize(
    "changes",
    [
        {"confirmation": Confirmation(False, True)},
        {"confirmation": Confirmation(True, False)},
        {"proof": None},
        {"proof": replace(proof(assignment()), binding_digest="f" * 64)},
        {"proof": replace(proof(assignment()), child_ids=("child1",))},
        {"proof": replace(proof(assignment()), policy=ref("foreign.policy"))},
    ],
)
def test_true_checkboxes_not_sufficient_exact_preparation_required(changes):
    row = assignment()
    args = {"confirmation": Confirmation(True, True), "proof": proof(row)} | changes
    with pytest.raises(VideoError):
        row.transition(Action.CONFIRM, 1, NOW, **args)


@pytest.mark.parametrize(
    "field,value",
    [
        ("revision", True),
        ("created_at", NOW.replace(tzinfo=None)),
        ("started_at", NOW),
        ("finished_at", NOW),
        ("source", None),
        ("state", "ready"),
    ],
)
def test_forged_assignment_constructor_rejected(field, value):
    with pytest.raises(VideoError):
        assignment(**{field: value})


def test_invalidation_not_autostop_and_requires_new_review_before_start():
    ready = prepared()
    stale = ready.invalidate(ready.revision, "source_recalled", NOW)
    assert stale.state is State.PREPARATION and stale.proof is None
    with pytest.raises(VideoError):
        stale.transition(
            Action.CONFIRM,
            stale.revision,
            NOW,
            confirmation=Confirmation(True, True),
            proof=proof(stale),
        )
    running = prepared(State.RUNNING)
    notice = running.invalidate(running.revision, "audience_changed", NOW)
    assert notice.state is State.RUNNING and notice.finished_at is None
    assert notice.invalidated == "audience_changed"  # Actual owner chooses intervention.


def test_terminal_state_no_resurrection_or_fake_individual_achievement():
    row = prepared(State.COMPLETED)
    assert row.finished_at is not None and not hasattr(row, "child_achievements")
    assert not hasattr(row, "reflection") and not hasattr(row, "portfolio_saved")
    with pytest.raises(VideoError):
        row.invalidate(row.revision, "policy_changed", NOW)


def test_audience_normalizes_sets_and_binds_each_exact_age():
    a = audience(children=(ChildAge("child2", 90), ChildAge("child1", 40)))
    assert a == audience()
    assert digest(a) != digest(
        replace(a, children=(ChildAge("child1", 90), ChildAge("child2", 40)))
    )
    with pytest.raises(VideoError):
        audience(children=(ChildAge("child1", 40), ChildAge("child1", 90)))


@pytest.mark.parametrize(
    "field,value",
    [
        ("instructions", " "),
        ("materials", ("",)),
        ("safety_note", "x" * 2001),
        ("duration_note", True),
    ],
)
def test_strict_local_adaptation_fields(field, value):
    with pytest.raises(VideoError):
        Adaptations(**{field: value})
