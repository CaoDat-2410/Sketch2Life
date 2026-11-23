"""FEAT-066 T-1d1: the closeout service over a fake store (counts, order, isolation of one row).

The SQL behaviour (the lock, the compare-and-set, the clock, the matrix of states) is in
``tests/integration/story_video/test_story_run_closeout_postgres.py``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

import pytest

from sketch2life.application.ports.story_run_closeout import (
    CloseoutOutcome,
    IdleCandidate,
    OverdueGeneration,
)
from sketch2life.application.ports.story_video import ProgressEvent, ProgressResult
from sketch2life.application.services.story_run_closeout import (
    MAX_BATCH_SIZE,
    StoryRunCloseoutService,
)

NOW = datetime(2026, 11, 19, 12, 0, tzinfo=UTC)


@dataclass
class FakeStore:
    overdue: list[OverdueGeneration] = field(default_factory=list)
    idle: list[IdleCandidate] = field(default_factory=list)
    outcomes: dict[str, CloseoutOutcome | Exception] = field(default_factory=dict)
    seen_now: list[datetime] = field(default_factory=list)
    limits: list[int] = field(default_factory=list)
    fail_listing: bool = False

    def overdue_generations(self, now: datetime, limit: int) -> list[OverdueGeneration]:
        self.seen_now.append(now)
        self.limits.append(limit)
        if self.fail_listing:
            raise RuntimeError("listing down")
        return self.overdue

    def idle_candidates(self, now: datetime, limit: int) -> list[IdleCandidate]:
        self.seen_now.append(now)
        self.limits.append(limit)
        if self.fail_listing:
            raise RuntimeError("listing down")
        return self.idle

    def close_idle(self, run_id: str, now: datetime) -> CloseoutOutcome:
        self.seen_now.append(now)
        outcome = self.outcomes.get(run_id, CloseoutOutcome.ABANDONED)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


@dataclass
class FakeProgress:
    applied: dict[str, bool] = field(default_factory=dict)
    raises: set[str] = field(default_factory=set)
    events: list[tuple[str, ProgressEvent]] = field(default_factory=list)

    def apply(self, generation_id: str, event: ProgressEvent) -> ProgressResult:
        self.events.append((generation_id, event))
        if generation_id in self.raises:
            raise RuntimeError("store down")
        return ProgressResult(self.applied.get(generation_id, True), None)


def test_the_idle_pass_counts_each_outcome_and_uses_the_injected_instant() -> None:
    store = FakeStore(
        idle=[IdleCandidate(f"run-{i}", "SCRIPT_REVIEW") for i in range(4)],
        outcomes={
            "run-0": CloseoutOutcome.COMPLETED,
            "run-1": CloseoutOutcome.ABANDONED,
            "run-2": CloseoutOutcome.SKIPPED,
        },
    )
    report = StoryRunCloseoutService(store, FakeProgress()).run_once(NOW)
    assert (report.completed, report.abandoned, report.skipped, report.errors) == (1, 2, 1, 0)
    assert report.deadline_failed == 0
    assert set(store.seen_now) == {NOW}


def test_the_default_clock_is_used_when_no_instant_is_given() -> None:
    store = FakeStore(idle=[IdleCandidate("run-0", "VIDEO_READY")])
    service = StoryRunCloseoutService(store, None, clock=lambda: NOW + timedelta(hours=1))
    service.run_once()
    assert set(store.seen_now) == {NOW + timedelta(hours=1)}


def test_a_failing_row_does_not_stop_the_batch_and_is_counted() -> None:
    store = FakeStore(
        idle=[IdleCandidate("a", "SCRIPT_REVIEW"), IdleCandidate("b", "SCRIPT_REVIEW")],
        outcomes={"a": RuntimeError("boom"), "b": CloseoutOutcome.ABANDONED},
    )
    report = StoryRunCloseoutService(store, None).run_once(NOW)
    assert (report.abandoned, report.errors) == (1, 1)


def test_the_deadline_pass_fails_each_overdue_generation_with_its_own_state() -> None:
    progress = FakeProgress(applied={"g-2": False})
    store = FakeStore(
        overdue=[
            OverdueGeneration("g-1", "QUEUED"),
            OverdueGeneration("g-2", "GENERATING"),
            OverdueGeneration("g-3", "SAFETY_VALIDATING"),
        ]
    )
    report = StoryRunCloseoutService(store, progress).run_once(NOW)
    assert (report.deadline_failed, report.skipped) == (2, 1)
    events = {generation: event for generation, event in progress.events}
    assert events["g-1"].expected_state == "QUEUED"
    assert events["g-3"].expected_state == "SAFETY_VALIDATING"
    assert {event.target_state for event in events.values()} == {"FAILED"}
    assert {event.safe_failure_code for event in events.values()} == {"VIDEO_DEADLINE_EXCEEDED"}


def test_a_progress_failure_is_counted_and_the_idle_pass_still_runs() -> None:
    progress = FakeProgress(raises={"g-1"})
    store = FakeStore(
        overdue=[OverdueGeneration("g-1", "QUEUED")], idle=[IdleCandidate("r", "SCRIPT_REVIEW")]
    )
    report = StoryRunCloseoutService(store, progress).run_once(NOW)
    assert (report.deadline_failed, report.abandoned, report.errors) == (0, 1, 1)


def test_without_a_progress_service_the_deadline_pass_is_off() -> None:
    store = FakeStore(overdue=[OverdueGeneration("g-1", "QUEUED")])
    report = StoryRunCloseoutService(store, None).run_once(NOW)
    assert report.deadline_failed == 0
    assert len(store.limits) == 1  # only the idle listing was read


def test_a_listing_failure_is_counted_and_not_raised() -> None:
    report = StoryRunCloseoutService(FakeStore(fail_listing=True), FakeProgress()).run_once(NOW)
    assert report.errors == 2
    assert report.completed == report.abandoned == report.deadline_failed == 0


def test_the_batch_size_is_bounded_and_passed_to_both_listings() -> None:
    store = FakeStore()
    StoryRunCloseoutService(store, FakeProgress()).run_once(NOW, batch_size=7)
    assert store.limits == [7, 7]
    for bad in (0, -1, MAX_BATCH_SIZE + 1):
        with pytest.raises(ValueError):
            StoryRunCloseoutService(store, None).run_once(NOW, batch_size=bad)


def test_a_naive_instant_is_refused() -> None:
    with pytest.raises(ValueError):
        StoryRunCloseoutService(FakeStore(), None).run_once(datetime(2026, 11, 19, 12, 0))


def test_the_log_carries_counts_only(caplog: pytest.LogCaptureFixture) -> None:
    store = FakeStore(idle=[IdleCandidate("secret-run-id", "SCRIPT_REVIEW")])
    with caplog.at_level(logging.INFO):
        StoryRunCloseoutService(store, None).run_once(NOW)
    text = " ".join(record.getMessage() for record in caplog.records)
    assert "abandoned=1" in text
    assert "secret-run-id" not in text
    assert "SCRIPT_REVIEW" not in text
