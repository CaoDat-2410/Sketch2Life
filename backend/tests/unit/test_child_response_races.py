"""Local transaction races and honest cross-owner decision ordering (offline only)."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier, local

import pytest

from sketch2life.application.services.child_response import (
    ChildResponseError,
    ResponseCommand,
    ResponseResult,
)
from sketch2life.infrastructure.assistance.harness import CHILD_A, CHILD_B, DEVICE_GA
from sketch2life.infrastructure.child_response.harness import (
    ChildResponseHarness,
    build_child_response_harness,
)


@pytest.mark.parametrize("step", ["save_state", "append_history", "mark_terminal", "put_receipt",
                                  "add_audit", "add_event", "commit"])
def test_b6_r03_every_effect_rolls_back_then_retry_commits(step: str) -> None:
    h = build_child_response_harness()
    proposal_id = h.approved()
    command = h.command(proposal_id, "declined")
    before = h.store.snapshot()
    h.store.fail_next(step)
    with pytest.raises(RuntimeError, match="injected child response fault"):
        h.service.record_response(command)
    assert h.store.snapshot() == before and h.store.commits == 0
    result = h.service.record_response(command)
    assert result.data.applied and not result.replayed
    state = h.store.snapshot()
    assert len(state.history) == len(state.receipts) == len(state.audit) == len(state.events) == 1
    assert len(state.markers) == 1 and h.store.commits == 1


def _compete(h: ChildResponseHarness, commands: tuple[ResponseCommand, ResponseCommand]
             ) -> list[ResponseResult | str]:
    barrier, seen = Barrier(2), local()

    def prepared() -> None:
        seen.count = getattr(seen, "count", 0) + 1
        if seen.count == 2:  # initial receipt lookup is first; final local unit is second
            barrier.wait(timeout=8)

    def run(command: ResponseCommand) -> ResponseResult | str:
        try:
            return h.service.record_response(command)
        except ChildResponseError as exc:
            return exc.code

    h.store.before_transaction = prepared
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            return list(executor.map(run, commands))
    finally:
        h.store.before_transaction = None


@pytest.mark.parametrize("existing", [False, True])
def test_b6_r04_r05_same_etag_has_one_winner_including_initial_state(existing: bool) -> None:
    h = build_child_response_harness()
    proposal_id = h.approved()
    if existing:
        h.respond(proposal_id)
    commands = (h.command(proposal_id, "hidden"), h.command(proposal_id, "declined"))
    results = _compete(h, commands)
    assert results.count("STALE_AGGREGATE") == 1
    assert sum(isinstance(r, ResponseResult) and r.data.applied for r in results) == 1
    state = h.store.snapshot()
    assert len(state.history) == len(state.events) == 1 + int(existing)
    assert len(state.receipts) == len(state.audit) == 1 + int(existing)


def test_b6_r06_same_key_concurrent_commit_replays_without_second_event() -> None:
    h = build_child_response_harness()
    proposal_id = h.approved()
    command = h.command(proposal_id)
    results = _compete(h, (command, command))
    assert all(isinstance(r, ResponseResult) for r in results)
    actual = [r for r in results if isinstance(r, ResponseResult)]
    assert sorted(r.replayed for r in actual) == [False, True]
    assert actual[0].data == actual[1].data
    state = h.store.snapshot()
    assert len(state.receipts) == len(state.history) == len(state.events) == len(state.audit) == 1


@pytest.mark.parametrize("kind", ["review", "turn"])
def test_b6_r01_r02_change_completed_before_validation_denies(kind: str) -> None:
    h = build_child_response_harness()
    proposal_id = h.approved()
    command = h.command(proposal_id)
    if kind == "review":
        h.revoke_review(proposal_id)
    else:
        h.close_turn()
    with pytest.raises(ChildResponseError, match="^SKETCH_UNAVAILABLE$"):
        h.service.record_response(command)
    assert not h.store.snapshot().history and not h.store.snapshot().events


@pytest.mark.parametrize("kind", ["review", "turn"])
def test_b6_r01_r02_later_change_keeps_only_historical_response(kind: str) -> None:
    h = build_child_response_harness()
    proposal_id = h.approved()
    command = h.command(proposal_id)
    changed: list[str] = []

    def publication() -> None:
        if kind == "review":
            h.revoke_review(proposal_id)
        else:
            h.close_turn()
        changed.append(kind)
        # This unit has not published yet. There is no cross-owner atomic lock claim.
        assert h.store.snapshot().history == []

    h.store.before_commit = publication
    result = h.service.record_response(command)
    assert changed == [kind] and result.data.applied
    assert len(h.store.snapshot().history) == len(h.store.snapshot().events) == 1
    with pytest.raises(ChildResponseError, match="^SKETCH_UNAVAILABLE$"):
        h.read(proposal_id)
    if kind == "review":
        with pytest.raises(ChildResponseError, match="^SKETCH_UNAVAILABLE$"):
            h.service.record_response(command)
    else:
        replay = h.service.record_response(command)
        assert replay.replayed and replay.data == result.data


def test_failed_local_commit_after_turn_close_has_no_accepted_receipt_to_replay() -> None:
    h = build_child_response_harness()
    proposal_id = h.approved()
    command = h.command(proposal_id)
    h.store.before_commit = h.close_turn
    h.store.fail_next_commit = True
    with pytest.raises(RuntimeError, match="commit failure"):
        h.service.record_response(command)
    assert not h.store.snapshot().receipts and not h.store.snapshot().events
    with pytest.raises(ChildResponseError, match="^SKETCH_UNAVAILABLE$"):
        h.service.record_response(command)


def test_snapshot_mutation_cannot_change_committed_receipt() -> None:
    h = build_child_response_harness()
    proposal_id = h.approved()
    command = h.command(proposal_id)
    expected = h.service.record_response(command)
    copy = h.store.snapshot()
    copy.receipts.clear()
    copy.history.clear()
    copy.states.clear()
    assert h.service.record_response(replace(command, if_match='"old"')).data == expected.data
    assert len(h.store.snapshot().history) == 1


@pytest.mark.parametrize("after_decision", [False, True])
def test_b6_r02_rebinding_never_relabels_or_discloses_old_participant(
    after_decision: bool,
) -> None:
    h = build_child_response_harness()
    proposal_id = h.approved(group=True)
    command = h.command(proposal_id, principal=DEVICE_GA)

    def rebind() -> None:
        h.rebind(DEVICE_GA, CHILD_B, "turn_fx_new_b")

    if after_decision:
        h.store.before_commit = rebind
        result = h.service.record_response(command)
        assert result.data.participant_id == CHILD_A
        assert result.data.child_response.turn_id == "turn_fx_ga"
        assert h.store.snapshot().history[0].key.participant_id == CHILD_A
        with pytest.raises(ChildResponseError, match="^SKETCH_UNAVAILABLE$"):
            h.service.record_response(command)
    else:
        rebind()
        with pytest.raises(ChildResponseError, match="^SKETCH_UNAVAILABLE$"):
            h.service.record_response(command)
        assert not h.store.snapshot().history
    # The now-authorized B can read, but never inherits A's response or receipt.
    current = h.read(proposal_id, DEVICE_GA)
    assert current.projection.access.participant_id == CHILD_B
    assert current.projection.child_response is None
    assert current.projection.response_revision == 1


@pytest.mark.parametrize("existing", [False, True])
def test_nested_commit_preserves_accepted_decline_and_rejects_outer_stale_copy(
    existing: bool,
) -> None:
    h = build_child_response_harness()
    proposal_id = h.approved()
    if existing:
        h.respond(proposal_id)
    outer = h.command(proposal_id, "hidden")
    inner = h.command(proposal_id, "declined")
    accepted: list[ResponseResult] = []

    def nested() -> None:
        accepted.append(h.service.record_response(inner))

    h.store.before_commit = nested
    with pytest.raises(ChildResponseError, match="^STALE_AGGREGATE$"):
        h.service.record_response(outer)
    assert len(accepted) == 1 and accepted[0].data.applied
    state = h.store.snapshot()
    assert state.history[-1].action.value == "declined"
    assert len(state.markers) == 1
    assert len(state.receipts) == len(state.history) == len(state.events) == 1 + int(existing)
    assert all(k.idempotency_key != outer.idempotency_key for k in state.receipts)
    replay = h.service.record_response(inner)
    assert replay.replayed and replay.data == accepted[0].data
    assert h.store.snapshot() == state


def test_nested_identical_operation_returns_winning_receipt_after_rollback() -> None:
    h = build_child_response_harness()
    proposal_id = h.approved()
    command = h.command(proposal_id, "declined")
    accepted: list[ResponseResult] = []
    h.store.before_commit = lambda: accepted.append(h.service.record_response(command))
    outer = h.service.record_response(command)
    assert outer.replayed and outer.data == accepted[0].data
    state = h.store.snapshot()
    assert len(state.receipts) == len(state.history) == len(state.events) == len(state.audit) == 1
    assert len(state.markers) == 1 and h.store.commits == 1
