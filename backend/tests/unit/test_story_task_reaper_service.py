"""FEAT-066 T-2d-fix: the lost-background-task reaper service and its store contract (no database).

The service is one bounded pass over five kinds of stuck work. These tests pin the argument rules
(the lease is required and bounded by the 6 h AI job deadline, SRS l.394), the bound of one pass,
that one failing row or listing never stops the batch, that the report is counts only and the log
carries no run id (BR-34 l.278), and, by compiling the store's listing statements, that no content
column is ever selected.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from sqlalchemy.dialects import postgresql

from sketch2life.application.ports.story_task_reaper import (
    AI_JOB_DEADLINE,
    ReapCandidate,
    ReapKind,
    ReapOutcome,
)
from sketch2life.application.services.story_task_reaper import (
    MAX_BATCH_SIZE,
    StoryTaskReaperService,
)
from sketch2life.infrastructure.persistence.story_task_reaper_store import (
    SqlStoryTaskReaperStore,
)

NOW = datetime(2026, 11, 21, 12, 0, tzinfo=UTC)
LEASE = timedelta(minutes=30)


class FakeStore:
    def __init__(self, listing: dict[ReapKind, list[str]] | None = None) -> None:
        self.listing = listing or {}
        self.listed: list[tuple[ReapKind, datetime, int]] = []
        self.reaped: list[tuple[str, ReapKind, datetime, datetime]] = []
        self.outcomes: dict[str, ReapOutcome | Exception] = {}
        self.listing_error: ReapKind | None = None

    def list_candidates(self, kind: ReapKind, cutoff: datetime, limit: int) -> list[ReapCandidate]:
        self.listed.append((kind, cutoff, limit))
        if kind is self.listing_error:
            raise RuntimeError("listing failed")
        return [ReapCandidate(run_id, kind) for run_id in self.listing.get(kind, [])][:limit]

    def reap(self, candidate: ReapCandidate, now: datetime, cutoff: datetime) -> ReapOutcome:
        self.reaped.append((candidate.run_id, candidate.kind, now, cutoff))
        outcome = self.outcomes.get(candidate.run_id, ReapOutcome.SKIPPED)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def service(store: FakeStore) -> StoryTaskReaperService:
    return StoryTaskReaperService(store)


# ------------------------------------------------------------------------------ arguments
def test_the_lease_is_required_and_bounded_by_the_ai_job_deadline() -> None:
    reaper = service(FakeStore())
    with pytest.raises(TypeError):
        reaper.run_once(now=NOW)  # type: ignore[call-arg]
    for lease in (timedelta(0), timedelta(seconds=-1), AI_JOB_DEADLINE + timedelta(seconds=1)):
        with pytest.raises(ValueError, match="lease"):
            reaper.run_once(lease=lease, now=NOW)
    assert reaper.run_once(lease=AI_JOB_DEADLINE, now=NOW).errors == 0
    assert reaper.run_once(lease=timedelta(seconds=1), now=NOW).errors == 0


def test_the_unknown_deadline_and_the_batch_size_are_bounded() -> None:
    reaper = service(FakeStore())
    for deadline in (timedelta(0), AI_JOB_DEADLINE + timedelta(seconds=1)):
        with pytest.raises(ValueError, match="unknown_deadline"):
            reaper.run_once(lease=LEASE, now=NOW, unknown_deadline=deadline)
    for size in (0, -1, MAX_BATCH_SIZE + 1):
        with pytest.raises(ValueError, match="batch_size"):
            reaper.run_once(lease=LEASE, now=NOW, batch_size=size)
    reaper.run_once(lease=LEASE, now=NOW, batch_size=1)
    reaper.run_once(lease=LEASE, now=NOW, batch_size=MAX_BATCH_SIZE)


def test_a_naive_instant_is_refused_and_the_default_clock_is_used() -> None:
    reaper = service(FakeStore())
    with pytest.raises(ValueError, match="timezone"):
        reaper.run_once(lease=LEASE, now=datetime(2026, 11, 21, 12, 0))  # noqa: DTZ001
    store = FakeStore()
    StoryTaskReaperService(store, clock=lambda: NOW).run_once(lease=LEASE)
    assert {cutoff for _kind, cutoff, _limit in store.listed} == {
        NOW - LEASE,
        NOW - AI_JOB_DEADLINE,
    }


def test_each_kind_gets_its_own_cutoff_the_lease_or_the_unknown_deadline() -> None:
    store = FakeStore()
    service(store).run_once(lease=LEASE, now=NOW, unknown_deadline=timedelta(hours=2))
    cutoffs = {kind: cutoff for kind, cutoff, _limit in store.listed}
    assert cutoffs == {
        ReapKind.DRAWING_LOST: NOW - LEASE,
        ReapKind.TRANSCRIPT_LOST: NOW - LEASE,
        ReapKind.STORY_LOST: NOW - LEASE,
        ReapKind.DRAWING_UNKNOWN: NOW - timedelta(hours=2),
        ReapKind.STORY_UNKNOWN: NOW - timedelta(hours=2),
    }


# ------------------------------------------------------------------------------ the pass
def test_the_report_counts_each_outcome_and_a_second_pass_finds_nothing() -> None:
    store = FakeStore(
        {
            ReapKind.DRAWING_LOST: ["a", "b"],
            ReapKind.TRANSCRIPT_LOST: ["c"],
            ReapKind.STORY_LOST: ["d", "e"],
            ReapKind.STORY_UNKNOWN: ["f"],
        }
    )
    store.outcomes = {
        "a": ReapOutcome.DRAWING_TIMED_OUT,
        "b": ReapOutcome.SKIPPED,
        "c": ReapOutcome.TRANSCRIPT_TIMED_OUT,
        "d": ReapOutcome.REWRITE_RECOVERED,
        "e": ReapOutcome.STORY_FAILED,
        "f": ReapOutcome.REWRITE_RECOVERED,
    }
    report = service(store).run_once(lease=LEASE, now=NOW)
    assert (
        report.drawing_timed_out,
        report.transcript_timed_out,
        report.rewrite_recovered,
        report.story_failed,
        report.skipped,
        report.errors,
    ) == (1, 1, 2, 1, 1, 0)
    # every row got the instant of the pass
    assert {now for _id, _kind, now, _cutoff in store.reaped} == {NOW}
    store.listing = {}
    again = service(store).run_once(lease=LEASE, now=NOW)
    assert (again.drawing_timed_out, again.rewrite_recovered, again.skipped) == (0, 0, 0)


def test_one_pass_touches_at_most_the_batch_in_the_order_of_the_kinds() -> None:
    store = FakeStore(
        {
            ReapKind.DRAWING_LOST: ["a", "b", "c"],
            ReapKind.STORY_LOST: ["d", "e"],
            ReapKind.STORY_UNKNOWN: ["f"],
        }
    )
    service(store).run_once(lease=LEASE, now=NOW, batch_size=4)
    assert [run_id for run_id, *_rest in store.reaped] == ["a", "b", "c", "d"]
    # the limit offered to a listing is what is left of the batch, and a spent batch lists no more
    assert [(kind, limit) for kind, _cutoff, limit in store.listed] == [
        (ReapKind.DRAWING_LOST, 4),
        (ReapKind.TRANSCRIPT_LOST, 1),
        (ReapKind.STORY_LOST, 1),
    ]


def test_a_failing_row_or_listing_does_not_stop_the_batch(
    caplog: pytest.LogCaptureFixture,
) -> None:
    store = FakeStore(
        {
            ReapKind.DRAWING_LOST: ["run-secret-1", "run-secret-2"],
            ReapKind.STORY_LOST: ["run-secret-3"],
        }
    )
    store.outcomes = {
        "run-secret-1": RuntimeError("database detail child-name"),
        "run-secret-2": ReapOutcome.DRAWING_TIMED_OUT,
        "run-secret-3": ReapOutcome.REWRITE_RECOVERED,
    }
    store.listing_error = ReapKind.TRANSCRIPT_LOST
    with caplog.at_level(logging.INFO):
        report = service(store).run_once(lease=LEASE, now=NOW)
    assert (report.drawing_timed_out, report.rewrite_recovered, report.errors) == (1, 1, 2)
    # counts and exception class names only: no run id, no message of the error (BR-34, l.278)
    text = " ".join(record.getMessage() for record in caplog.records)
    assert "run-secret" not in text and "child-name" not in text and "database detail" not in text
    assert "errors=2" in text


# ------------------------------------------------------------------------------ the store
def test_the_listings_select_ids_and_clocks_only_never_a_content_column() -> None:
    captured: list[Any] = []

    class Session:
        def execute(self, statement: Any) -> Any:
            captured.append(statement)
            return type("Result", (), {"all": staticmethod(lambda: [])})()

        def rollback(self) -> None:
            pass

    store = SqlStoryTaskReaperStore(Session())  # type: ignore[arg-type]
    for kind in ReapKind:
        assert store.list_candidates(kind, NOW, 5) == []
    assert len(captured) == len(ReapKind)
    for statement in captured:
        assert {str(column) for column in statement.selected_columns} == {"runs.run_id"}
        dialect: Any = postgresql.dialect
        text = str(statement.compile(dialect=dialect()))
        select_part = text.split("FROM", 1)[0]
        for forbidden in (
            "story_content",
            "raw_transcript",
            "adult_corrected_text",
            "typed_idea",
            "context_snapshot",
            "subject_label",
            "result_snapshot",
            "title",
        ):
            assert forbidden not in select_part
        # every listing is bounded and ordered, and is Parent-lane only (the demo lane never sets
        # ``current_input_revision``)
        assert "LIMIT" in text and "ORDER BY" in text
        assert "current_input_revision IS NOT NULL" in text
        assert "actor_scope_kind" in text and "run_state NOT IN" in text
