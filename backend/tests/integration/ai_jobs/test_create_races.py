"""BE2-01 Phase B batch B3: create races on real PostgreSQL (plan rev3 §7.2, B-03a–f, B-07).

Two OS processes run ``AiJobService.create_job`` against the same disposable database. A
barrier right after each process's first owner-fence hold (inside its first write
transaction, after the receipt/semantic re-reads, before any INSERT) guarantees both saw
"nothing exists" before either inserts, so the plain-INSERT unique violation, the whole
rollback and the fresh re-read round are exercised for real. Owner decisions come from
the ASSUMED_CONTRACT fixture. ``requires_postgres``; skipped means NOT_RUN.
"""

from __future__ import annotations

import multiprocessing
import os
import time
from collections.abc import Iterator
from typing import Any

import b3_support as s
import pytest
from sketch2life.application.ports.ai_jobs import FenceResult
from sketch2life.application.services.ai_jobs import AiJobError
from sketch2life.infrastructure.ai_jobs.harness import TEACHER, TEACHER_2
from sqlalchemy.engine import URL

pytestmark = pytest.mark.requires_postgres

SPAWN = multiprocessing.get_context("spawn")
TIMEOUT = 60


@pytest.fixture
def db(monkeypatch: pytest.MonkeyPatch, disposable_database_url: URL) -> Iterator[URL]:
    yield from s.prepare_database(monkeypatch, disposable_database_url)


def _create_in_process(
    url: URL,
    arguments: dict[str, Any],
    barrier: Any,
    results: Any,
    exit_at_transaction: int | None,
    delay_after_barrier: float = 0.0,
) -> None:
    """Child process: one create. Waits at the barrier after its first fence hold; optionally
    dies when a later transaction begins."""

    waited: list[bool] = []

    def on_hold(_: FenceResult) -> None:
        if barrier is not None and not waited:
            waited.append(True)
            barrier.wait(TIMEOUT)
            time.sleep(delay_after_barrier)

    def on_transaction(number: int) -> None:
        if exit_at_transaction is not None and number == exit_at_transaction:
            os._exit(17)

    principal = TEACHER_2 if arguments.pop("second_teacher", False) else TEACHER
    rig = s.build_rig(url, on_transaction=on_transaction, on_hold=on_hold)
    try:
        result = rig.service.create_job(s.command(principal=principal, **arguments))
        results.put(
            ("ok", result.outcome, result.replayed, result.job_id, rig.repository.transactions)
        )
    except AiJobError as error:
        results.put(("error", error.code, None, None, rig.repository.transactions))


def _race(
    url: URL,
    first: dict[str, Any],
    second: dict[str, Any],
    *,
    exit_second_at: int | None = None,
) -> list[tuple[Any, ...]]:
    barrier = SPAWN.Barrier(2)
    results = SPAWN.Queue()
    processes = [
        SPAWN.Process(target=_create_in_process, args=(url, first, barrier, results, None)),
        # When the second process must lose (restart case) it inserts after a short delay;
        # its INSERT then waits on or sees the winner's key either way.
        SPAWN.Process(
            target=_create_in_process,
            args=(
                url,
                second,
                barrier,
                results,
                exit_second_at,
                0.5 if exit_second_at is not None else 0.0,
            ),
        ),
    ]
    for process in processes:
        process.start()
    expected = 1 if exit_second_at is not None else 2
    try:
        # Drain results before joining so a child never blocks on a full queue pipe.
        collected = [results.get(timeout=TIMEOUT) for _ in range(expected)]
        for process in processes:
            process.join(TIMEOUT)
            assert process.exitcode is not None, "race process did not finish"
    finally:
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(5)
    if exit_second_at is not None:
        assert processes[1].exitcode == 17
    return collected


def test_b03a_same_key_same_payload_two_processes_one_job_both_replay_it(db: URL) -> None:
    outcomes = _race(db, {"key": "race_a"}, {"key": "race_a"})
    assert {o[3] for o in outcomes} == {outcomes[0][3]}  # both callers get the same job
    assert sorted((o[1], o[2]) for o in outcomes) == [("created", False), ("created", True)]
    # The loser needed the second round: its first write hit the unique key and rolled back.
    assert max(o[4] for o in outcomes) == 3
    engine = s.engine_for(db)
    assert s.counts(engine) == {
        "job": 1,
        "attempt": 1,
        "semantic_request": 1,
        "command_receipt": 1,
        "completion_receipt": 0,
        "outbox_dispatch": 1,
        "outbox_audit": 1,
    }
    assert s.no_orphans(engine)


def test_b03b_different_keys_same_semantic_one_job_attempt_dispatch_two_receipts(
    db: URL,
) -> None:
    outcomes = _race(db, {"key": "race_b1"}, {"key": "race_b2", "second_teacher": True})
    assert len({o[3] for o in outcomes}) == 1
    assert sorted(o[1] for o in outcomes) == ["created", "deduplicated"]
    # The loser's first write rolled back; its second round wrote only its own receipt.
    assert next(o[4] for o in outcomes if o[1] == "deduplicated") == 4
    engine = s.engine_for(db)
    assert s.counts(engine) == {
        "job": 1,
        "attempt": 1,
        "semantic_request": 1,
        "command_receipt": 2,
        "completion_receipt": 0,
        "outbox_dispatch": 1,
        "outbox_audit": 2,
    }
    assert s.no_orphans(engine)


def test_b03c_same_key_different_payload_is_a_mismatch_without_orphans(db: URL) -> None:
    outcomes = _race(db, {"key": "race_c"}, {"key": "race_c", "request": s.REQUESTS[1]})
    assert sorted(o[0] for o in outcomes) == ["error", "ok"]
    error = next(o for o in outcomes if o[0] == "error")
    assert error[1] == "IDEMPOTENCY_PAYLOAD_MISMATCH"
    engine = s.engine_for(db)
    assert s.counts(engine)["job"] == 1 and s.counts(engine)["command_receipt"] == 1
    assert s.no_orphans(engine)


def test_b03d_null_session_is_distinct_from_populated_and_deduplicates_with_null(
    db: URL,
) -> None:
    distinct = _race(
        db,
        {"key": "race_d1", "session_id": None},
        {"key": "race_d2", "session_id": "session_fx_001"},
    )
    assert len({o[3] for o in distinct}) == 2
    assert all(o[1] == "created" for o in distinct)
    same = _race(
        db,
        {"key": "race_d3", "session_id": None},
        {"key": "race_d4", "session_id": None, "second_teacher": True},
    )
    assert len({o[3] for o in same}) == 1
    assert {o[3] for o in same} <= {o[3] for o in distinct}
    engine = s.engine_for(db)
    assert s.counts(engine)["job"] == 2 and s.no_orphans(engine)


def test_b03e_permuted_and_unicode_equivalent_subjects_deduplicate(db: URL) -> None:
    composed = "child_é"  # é as one code point
    decomposed = "child_é"  # e + combining acute: same NFC text
    outcomes = _race(
        db,
        {"key": "race_e1", "subjects": (composed, "child_fx_001")},
        {"key": "race_e2", "subjects": ("child_fx_001", decomposed), "second_teacher": True},
    )
    assert len({o[3] for o in outcomes}) == 1
    assert sorted(o[1] for o in outcomes) == ["created", "deduplicated"]
    engine = s.engine_for(db)
    assert s.counts(engine)["job"] == 1 and s.no_orphans(engine)


def test_b03f_restart_between_rounds_converges_without_orphans(db: URL) -> None:
    # The second process dies right after its first round rolled back (transaction 3 would be
    # its fresh re-read). A restarted process then repeats the same command.
    outcomes = _race(
        db, {"key": "race_f1"}, {"key": "race_f2", "second_teacher": True}, exit_second_at=3
    )
    assert len(outcomes) == 1 and outcomes[0][1] == "created"
    engine = s.engine_for(db)
    assert s.counts(engine)["job"] == 1 and s.counts(engine)["command_receipt"] == 1
    results = SPAWN.Queue()
    restarted = SPAWN.Process(
        target=_create_in_process,
        args=(db, {"key": "race_f2", "second_teacher": True}, None, results, None),
    )
    restarted.start()
    try:
        status, outcome, replayed, job_id, _ = results.get(timeout=TIMEOUT)
        restarted.join(TIMEOUT)
        assert restarted.exitcode == 0
    finally:
        if restarted.is_alive():
            restarted.terminate()
            restarted.join(5)
    assert (status, outcome, replayed, job_id) == ("ok", "deduplicated", False, outcomes[0][3])
    assert s.counts(engine) == {
        "job": 1,
        "attempt": 1,
        "semantic_request": 1,
        "command_receipt": 2,
        "completion_receipt": 0,
        "outbox_dispatch": 1,
        "outbox_audit": 2,
    }
    assert s.no_orphans(engine)
