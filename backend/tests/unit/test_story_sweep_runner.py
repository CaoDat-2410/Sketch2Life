"""FEAT-066 T-1d1-fix: the periodic story sweep runner and its worker, over a fake clock.

No test sleeps and none opens a database: the steps are fakes, the loop's wait is injected and the
lock connection is a stand-in. The PostgreSQL behaviour (lock, batches, two passes) is proved by
``tests/integration/story_video/test_story_sweep_runner_postgres.py``.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from sketch2life.application.services.story_sweep_runner import (
    MAX_BATCH_SIZE,
    SweepReport,
    SweepStep,
    run_sweepers_once,
)
from sketch2life.infrastructure.config.settings import Settings
from sketch2life.infrastructure.story_video import sweep_worker
from sketch2life.infrastructure.story_video.sweep_worker import (
    LOCK_NAME,
    STEP_ORDER,
    build_sweep_steps,
    run_loop,
    run_pass_locked,
)

NOW = datetime(2026, 12, 1, 12, 0, tzinfo=UTC)
PROBE_ID = "11111111-2222-3333-4444-555555555555"


class Recorder:
    def __init__(self) -> None:
        self.calls: list[tuple[str, datetime, int]] = []

    def step(
        self, name: str, counts: Mapping[str, int] | None = None, *, raises: Exception | None = None
    ) -> SweepStep:
        def run(now: datetime, batch: int) -> Mapping[str, int]:
            self.calls.append((name, now, batch))
            if raises is not None:
                raise raises
            return counts or {"done": 1}

        return SweepStep(name, run)


def test_the_steps_run_once_each_in_order_with_one_instant_and_the_batch() -> None:
    recorder = Recorder()
    ticks = iter([NOW, NOW + timedelta(hours=1)])
    report = run_sweepers_once(
        steps=[recorder.step("reaper"), recorder.step("reconciler"), recorder.step("closeout")],
        batch_size=7,
        clock=lambda: next(ticks),
    )
    assert [call[0] for call in recorder.calls] == ["reaper", "reconciler", "closeout"]
    assert {call[1] for call in recorder.calls} == {NOW}  # the clock is read once per pass
    assert {call[2] for call in recorder.calls} == {7}
    assert [name for name, _ in report.steps] == ["reaper", "reconciler", "closeout"]
    assert report.errors == 0 and report.lock_busy is False


def test_an_injected_now_wins_over_the_clock() -> None:
    recorder = Recorder()

    def clock() -> datetime:
        raise AssertionError("the clock must not be read")

    run_sweepers_once(NOW, steps=[recorder.step("a")], clock=clock)
    assert recorder.calls[0][1] == NOW


def test_a_failing_step_is_counted_by_class_name_and_never_stops_the_others() -> None:
    recorder = Recorder()
    report = run_sweepers_once(
        NOW,
        steps=[
            recorder.step("reaper", raises=RuntimeError(f"row {PROBE_ID} exploded")),
            recorder.step("reconciler"),
            recorder.step("closeout", raises=ValueError("boom")),
        ],
    )
    assert [call[0] for call in recorder.calls] == ["reaper", "reconciler", "closeout"]
    assert report.errors == 2
    assert report.failures == (("reaper", "RuntimeError"), ("closeout", "ValueError"))
    assert [name for name, _ in report.steps] == ["reconciler"]


@pytest.mark.parametrize("batch", [0, -1, MAX_BATCH_SIZE + 1, 500])
def test_the_batch_is_bounded(batch: int) -> None:
    with pytest.raises(ValueError, match="batch_size"):
        run_sweepers_once(NOW, steps=[], batch_size=batch)


@pytest.mark.parametrize("batch", [1, 50, MAX_BATCH_SIZE])
def test_the_batch_bounds_are_accepted(batch: int) -> None:
    assert run_sweepers_once(NOW, steps=[], batch_size=batch) == SweepReport()


def test_a_naive_now_is_refused_and_no_step_runs() -> None:
    recorder = Recorder()
    with pytest.raises(ValueError, match="timezone-aware"):
        run_sweepers_once(datetime(2026, 12, 1), steps=[recorder.step("a")])
    assert recorder.calls == []


def test_the_log_carries_counts_only(caplog: pytest.LogCaptureFixture) -> None:
    recorder = Recorder()
    with caplog.at_level(logging.INFO):
        run_sweepers_once(
            NOW,
            steps=[
                recorder.step("closeout", {"abandoned": 3, "errors": 0}),
                recorder.step("boom", raises=RuntimeError(f"run {PROBE_ID} secret detail")),
            ],
        )
    text = caplog.text
    assert "story_sweep_pass" in text and "closeout.abandoned=3" in text
    assert "story_sweep_step_failed step=boom kind=RuntimeError" in text
    assert PROBE_ID not in text and "secret detail" not in text
    for state in ("SCRIPT_REVIEW", "VIDEO_READY", "SAFETY_BLOCKED"):
        assert state not in text


# ------------------------------------------------------------------------------ the loop
class FakeWait:
    """A clock that never sleeps: every wait advances a fake time and says when to stop."""

    def __init__(self, stop_after: int | None = None) -> None:
        self.now = NOW
        self.waits: list[float] = []
        self._stop_after = stop_after

    def __call__(self, seconds: float) -> bool:
        self.waits.append(seconds)
        self.now += timedelta(seconds=seconds)
        return self._stop_after is not None and len(self.waits) >= self._stop_after


def test_the_loop_runs_a_pass_then_waits_the_interval_until_stopped() -> None:
    wait = FakeWait(stop_after=3)
    passes: list[datetime] = []

    def run_pass() -> SweepReport:
        passes.append(wait.now)
        return SweepReport()

    count = run_loop(run_pass, interval_seconds=300, wait=wait)
    assert count == 3 and wait.waits == [300, 300, 300]
    assert passes == [NOW, NOW + timedelta(seconds=300), NOW + timedelta(seconds=600)]


def test_a_failing_pass_waits_the_normal_interval_and_the_loop_goes_on() -> None:
    wait = FakeWait(stop_after=2)
    outcomes: list[str] = []
    beats: list[int] = []

    def run_pass() -> SweepReport:
        outcomes.append("run")
        if len(outcomes) == 1:
            raise ConnectionError("database down")
        return SweepReport()

    count = run_loop(
        run_pass, interval_seconds=60, wait=wait, on_success=lambda: beats.append(len(outcomes))
    )
    assert count == 2 and wait.waits == [60, 60]  # never spins, never a shorter wait
    assert beats == [2]  # only the pass that did not raise is a heartbeat


def test_max_passes_ends_the_loop_without_waiting_after_the_last_pass() -> None:
    wait = FakeWait()
    assert run_loop(SweepReport, interval_seconds=5, wait=wait, max_passes=2) == 2
    assert wait.waits == [5]


def test_the_heartbeat_needs_a_pass_without_a_failing_step_and_a_busy_lock_is_healthy() -> None:
    reports = iter(
        [
            SweepReport(failures=(("closeout", "OSError"),)),  # a step failed: no heartbeat
            SweepReport(lock_busy=True),  # another worker sweeps: healthy
            SweepReport(),
        ]
    )
    beats: list[int] = []
    wait = FakeWait(stop_after=3)
    count = run_loop(
        lambda: next(reports),
        interval_seconds=30,
        wait=wait,
        on_success=lambda: beats.append(len(beats) + 1),
    )
    assert count == 3 and beats == [1, 2]


def test_a_failing_heartbeat_never_stops_the_loop() -> None:
    wait = FakeWait(stop_after=1)

    def beat() -> None:
        raise OSError("read-only")

    assert run_loop(SweepReport, interval_seconds=5, wait=wait, on_success=beat) == 1


# ------------------------------------------------------------------------------ the lock
class FakeConnection:
    def __init__(self, *, acquired: bool, released: bool = True) -> None:
        self.acquired = acquired
        self.released = released
        self.statements: list[str] = []
        self.invalidated = False
        self.closed = False
        self.isolation: str | None = None

    def execution_options(self, **options: Any) -> FakeConnection:
        self.isolation = options.get("isolation_level")
        return self

    def scalar(self, statement: Any, parameters: Mapping[str, Any]) -> bool:
        text = str(statement)
        self.statements.append(text)
        assert parameters == {"name": LOCK_NAME}
        return self.acquired if "pg_try_advisory_lock" in text else self.released

    def invalidate(self) -> None:
        self.invalidated = True

    def close(self) -> None:
        self.closed = True


class FakeEngine:
    def __init__(self, connection: FakeConnection) -> None:
        self.connection = connection

    def connect(self) -> FakeConnection:
        return self.connection


def test_a_busy_lock_means_no_step_runs_and_the_report_says_so() -> None:
    connection = FakeConnection(acquired=False)
    recorder = Recorder()
    report = run_pass_locked(FakeEngine(connection), [recorder.step("a")], now=NOW)  # type: ignore[arg-type]
    assert report.lock_busy is True and report.steps == () and recorder.calls == []
    assert connection.isolation == "AUTOCOMMIT"
    assert connection.closed and not connection.invalidated
    assert len(connection.statements) == 1  # no unlock of a lock that was never taken


def test_the_lock_is_released_after_the_pass_even_when_a_step_fails() -> None:
    connection = FakeConnection(acquired=True)
    recorder = Recorder()
    report = run_pass_locked(
        FakeEngine(connection),  # type: ignore[arg-type]
        [recorder.step("a", raises=RuntimeError("x")), recorder.step("b")],
        now=NOW,
    )
    assert report.errors == 1 and [call[0] for call in recorder.calls] == ["a", "b"]
    assert "pg_advisory_unlock" in connection.statements[-1]
    assert connection.closed and not connection.invalidated


def test_a_lock_that_cannot_be_released_closes_the_physical_session() -> None:
    connection = FakeConnection(acquired=True, released=False)
    run_pass_locked(FakeEngine(connection), [], now=NOW)  # type: ignore[arg-type]
    assert (
        connection.invalidated and connection.closed
    )  # PostgreSQL drops the lock with the session


def test_a_programming_error_in_the_pass_still_releases_the_lock() -> None:
    connection = FakeConnection(acquired=True)
    with pytest.raises(ValueError, match="batch_size"):
        run_pass_locked(FakeEngine(connection), [], now=NOW, batch_size=0)  # type: ignore[arg-type]
    assert "pg_advisory_unlock" in connection.statements[-1] and connection.closed


# ------------------------------------------------------------------------------ steps and settings
def test_the_worker_composes_the_three_sweepers_in_the_srs_order() -> None:
    steps = build_sweep_steps(object(), None, lease=timedelta(hours=6))  # type: ignore[arg-type]
    assert [step.name for step in steps] == list(STEP_ORDER) == ["reaper", "reconciler", "closeout"]


def test_settings_defaults_are_safe_and_the_environment_overrides_them(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in (
        "ENABLED",
        "INTERVAL_SECONDS",
        "BATCH_SIZE",
        "TASK_LEASE_SECONDS",
    ):
        monkeypatch.delenv(f"SKETCH2LIFE_STORY_SWEEP_{name}", raising=False)
    defaults = Settings(_env_file=None)  # type: ignore[call-arg]
    assert defaults.story_sweep_enabled is True
    assert defaults.story_sweep_interval_seconds == 300
    assert defaults.story_sweep_batch_size == 50
    assert defaults.story_sweep_task_lease_seconds == 21_600  # the 6 h AI job deadline (l.615)
    monkeypatch.setenv("SKETCH2LIFE_STORY_SWEEP_ENABLED", "false")
    monkeypatch.setenv("SKETCH2LIFE_STORY_SWEEP_INTERVAL_SECONDS", "5")
    monkeypatch.setenv("SKETCH2LIFE_STORY_SWEEP_BATCH_SIZE", "10")
    monkeypatch.setenv("SKETCH2LIFE_STORY_SWEEP_TASK_LEASE_SECONDS", "600")
    shortened = Settings(_env_file=None)  # type: ignore[call-arg]
    assert shortened.story_sweep_enabled is False
    assert (shortened.story_sweep_interval_seconds, shortened.story_sweep_batch_size) == (5, 10)
    assert shortened.story_sweep_task_lease_seconds == 600


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("INTERVAL_SECONDS", "0"),
        ("INTERVAL_SECONDS", "3601"),
        ("BATCH_SIZE", "0"),
        ("BATCH_SIZE", "201"),
        ("TASK_LEASE_SECONDS", "59"),
        ("TASK_LEASE_SECONDS", "21601"),
    ],
)
def test_settings_refuse_values_outside_their_bounds(
    monkeypatch: pytest.MonkeyPatch, name: str, value: str
) -> None:
    monkeypatch.setenv(f"SKETCH2LIFE_STORY_SWEEP_{name}", value)
    with pytest.raises(ValueError, match="story_sweep"):
        Settings(_env_file=None)  # type: ignore[call-arg]


# ------------------------------------------------------------------------------ main
def _patch_main(
    monkeypatch: pytest.MonkeyPatch, settings: Settings, report: SweepReport | Exception
) -> list[str]:
    events: list[str] = []
    monkeypatch.setattr(sweep_worker, "get_settings", lambda: settings)

    class Engine:
        def dispose(self) -> None:
            events.append("dispose")

    def create_engine() -> Engine:
        events.append("connect")
        return Engine()

    def pass_once(engine: Any, steps: Any, *, batch_size: int) -> SweepReport:
        events.append(f"pass batch={batch_size}")
        if isinstance(report, Exception):
            raise report
        return report

    monkeypatch.setattr(sweep_worker, "create_core_engine", create_engine)
    monkeypatch.setattr(sweep_worker, "_steps_for", lambda *_: ())
    monkeypatch.setattr(sweep_worker, "run_pass_locked", pass_once)
    return events


def test_main_exits_at_once_without_connecting_when_the_sweep_is_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(_env_file=None, story_sweep_enabled=False)  # type: ignore[call-arg]
    events = _patch_main(monkeypatch, settings, SweepReport())
    assert sweep_worker.main(["--once"]) == 0
    assert events == []


def test_once_runs_one_pass_with_the_settings_batch_and_touches_the_heartbeat(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    settings = Settings(_env_file=None, story_sweep_batch_size=12)  # type: ignore[call-arg]
    events = _patch_main(monkeypatch, settings, SweepReport())
    beat = tmp_path / "beat"
    assert sweep_worker.main(["--once", "--heartbeat-file", str(beat)]) == 0
    assert events == ["connect", "pass batch=12", "dispose"] and beat.exists()


def test_once_returns_nonzero_only_when_a_step_raised(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    _patch_main(monkeypatch, settings, SweepReport(failures=(("closeout", "OSError"),)))
    assert sweep_worker.main(["--once"]) == 1
    beat = tmp_path / "beat"  # a failing step is not a heartbeat
    assert sweep_worker.main(["--once", "--heartbeat-file", str(beat)]) == 1 and not beat.exists()
    _patch_main(monkeypatch, settings, SweepReport(lock_busy=True))
    assert sweep_worker.main(["--once", "--batch-size", "3"]) == 0  # a busy lock is not an error
    _patch_main(monkeypatch, settings, ConnectionError("down"))
    assert sweep_worker.main(["--once"]) == 1


@pytest.mark.parametrize(
    "argument",
    [["--interval-seconds", "0"], ["--interval-seconds", "3601"], ["--batch-size", "201"]],
)
def test_main_refuses_arguments_outside_their_bounds(argument: list[str]) -> None:
    with pytest.raises(SystemExit) as stopped:
        sweep_worker.main(["--once", *argument])
    assert stopped.value.code == 2


def test_the_scheduled_pass_does_nothing_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings(_env_file=None, story_sweep_enabled=False)  # type: ignore[call-arg]
    events = _patch_main(monkeypatch, settings, SweepReport())
    assert sweep_worker.run_scheduled_pass() == SweepReport()
    assert events == []
