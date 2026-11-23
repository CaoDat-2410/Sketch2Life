"""The periodic story sweep worker (FEAT-066 T-1d1-fix; SRS l.1799, l.1988, l.2867, FR-O-03 l.608).

A separate process that runs ``run_sweepers_once`` on an interval: ``python -m
sketch2life.infrastructure.story_video.sweep_worker`` (``--once`` runs one pass and exits).

Departure from the owner's wording "Redis/RQ dispatch" (OPEN Q1 of the plan): FR-O-03 l.608 gives
PostgreSQL the business and job state and Redis/RQ the dispatch, backpressure and rate limit; a
sweep dispatches nothing, it is a periodic idempotent pass over durable rows (l.1801: recovery after
losing Redis is a PostgreSQL scan), and a net that recovers lost background tasks should not depend
on Redis, one of the things it recovers from. ``run_scheduled_pass`` is a no-argument callable, so a
later ``rq.cron`` registration (rq 2.11 ships it) is one line and needs a Redis container and the
INTG-02 wiring, both outside this task.

The lock is a duplicate-work guard only: one pass runs at a time under a PostgreSQL session
advisory lock on a dedicated connection. Correctness stays with the compare-and-set of every row,
so a lost lock, a crash or two workers can only repeat work, never double an effect. Logs carry
counts only (BR-34); the per-pass count line is the heartbeat (l.1988), and ``--heartbeat-file``
touches a file after each pass that did not raise, for a container health check.
"""

from __future__ import annotations

import argparse
import logging
import signal
import sys
import threading
from collections.abc import Callable, Mapping, Sequence
from contextlib import suppress
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path
from types import FrameType
from typing import Any

from sqlalchemy import Engine, text
from sqlalchemy.orm import Session, sessionmaker

from sketch2life.application.ports.story_video import StoryVideoAdapters
from sketch2life.application.services.story_run_video import (
    DEFAULT_PORT_TIMEOUT_SECONDS,
    StoryVideoAdmissionService,
)
from sketch2life.application.services.story_sweep_runner import (
    DEFAULT_BATCH_SIZE,
    MAX_BATCH_SIZE,
    SweepReport,
    SweepStep,
    log_report,
    run_sweepers_once,
)
from sketch2life.infrastructure.config.settings import Settings, get_settings
from sketch2life.infrastructure.persistence.database import (
    create_core_engine,
    create_core_session_factory,
)
from sketch2life.infrastructure.persistence.story_task_reaper_store import build_story_task_reaper
from sketch2life.infrastructure.story_video.closeout_store import build_story_run_closeout
from sketch2life.infrastructure.story_video.composition import build_story_video_adapters
from sketch2life.infrastructure.story_video.repository import SqlStoryVideoRepository

_LOG = logging.getLogger(__name__)
LOCK_NAME = "sketch2life.story-sweep.v1"
STEP_ORDER = ("reaper", "reconciler", "closeout")


def build_sweep_steps(
    session_factory: sessionmaker[Session],
    adapters: StoryVideoAdapters | None,
    *,
    lease: timedelta,
    port_timeout_seconds: float = DEFAULT_PORT_TIMEOUT_SECONDS,
) -> tuple[SweepStep, ...]:
    """The three sweepers in the order of ``STEP_ORDER``, each over a session of its own."""

    def reaper(now: datetime, batch: int) -> Mapping[str, int]:
        with session_factory() as session:
            report = build_story_task_reaper(session).run_once(
                lease=lease, now=now, batch_size=batch
            )
        return asdict(report)

    def reconciler(now: datetime, batch: int) -> Mapping[str, int]:
        # The admission service takes no clock, so only the reaper and the closeout read ``now``.
        # With no adapters it still fails the in-flight generations of cancelled runs (database
        # only); a pending intent or a compute reservation waits for the adapters.
        with session_factory() as session:
            service = StoryVideoAdmissionService(
                SqlStoryVideoRepository(session),
                adapters,
                call_timeout_seconds=port_timeout_seconds,
            )
            report = service.reconcile_pending_admissions(limit=batch)
        return asdict(report)

    def closeout(now: datetime, batch: int) -> Mapping[str, int]:
        with session_factory() as session:
            service = build_story_run_closeout(
                session, adapters, call_timeout_seconds=port_timeout_seconds
            )
            report = service.run_once(now, batch_size=batch)
        return asdict(report)

    runners = {"reaper": reaper, "reconciler": reconciler, "closeout": closeout}
    return tuple(SweepStep(name, runners[name]) for name in STEP_ORDER)


def run_pass_locked(
    engine: Engine,
    steps: Sequence[SweepStep],
    *,
    now: datetime | None = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    clock: Callable[[], datetime] | None = None,
) -> SweepReport:
    """One pass under the advisory lock; a busy lock means another worker is sweeping: no work."""

    connection = engine.connect()
    try:
        connection = connection.execution_options(isolation_level="AUTOCOMMIT")
        acquired = connection.scalar(
            text("SELECT pg_try_advisory_lock(hashtextextended(:name, 0))"), {"name": LOCK_NAME}
        )
        if acquired is not True:
            report = SweepReport(lock_busy=True)
            log_report(report)
            return report
        try:
            return run_sweepers_once(now, steps=steps, batch_size=batch_size, clock=clock)
        finally:
            try:
                released = connection.scalar(
                    text("SELECT pg_advisory_unlock(hashtextextended(:name, 0))"),
                    {"name": LOCK_NAME},
                )
                if released is not True:
                    connection.invalidate()  # closing the session releases every lock it holds
            except Exception:
                with suppress(Exception):
                    connection.invalidate()
    finally:
        with suppress(Exception):
            connection.close()


def run_loop(
    run_pass: Callable[[], SweepReport],
    *,
    interval_seconds: float,
    wait: Callable[[float], bool],
    max_passes: int | None = None,
    on_success: Callable[[], None] | None = None,
) -> int:
    """Run passes until ``wait`` says stop (it returns True) or ``max_passes``; returns the count.

    A pass that raises is logged by class name and the loop waits the normal interval (it never
    spins); ``on_success`` (the heartbeat) runs after each pass that did not raise and had no
    failing step (a busy lock is healthy: another worker sweeps; a step that fails on every pass is
    not, so the container healthcheck sees it).
    """

    passes = 0
    while True:
        try:
            report = run_pass()
        except Exception as exc:
            _LOG.warning("story_sweep_pass_failed kind=%s", type(exc).__name__)
        else:
            if on_success is not None and report.errors == 0:
                with suppress(Exception):
                    on_success()
        passes += 1
        if max_passes is not None and passes >= max_passes:
            return passes
        if wait(interval_seconds):
            return passes


def _steps_for(settings: Settings, engine: Engine) -> tuple[SweepStep, ...]:
    return build_sweep_steps(
        create_core_session_factory(engine),
        build_story_video_adapters(settings),
        lease=timedelta(seconds=settings.story_sweep_task_lease_seconds),
        port_timeout_seconds=settings.story_video_port_timeout_seconds,
    )


def run_scheduled_pass() -> SweepReport:
    """One locked pass built from the settings: the one entry a scheduler (RQ cron) would call."""

    settings = get_settings()
    if not settings.story_sweep_enabled:
        return SweepReport()
    engine = create_core_engine()
    try:
        return run_pass_locked(
            engine, _steps_for(settings, engine), batch_size=settings.story_sweep_batch_size
        )
    finally:
        engine.dispose()


def _positive_int(low: int, high: int) -> Callable[[str], int]:
    def parse(raw: str) -> int:
        value = int(raw)
        if not low <= value <= high:
            raise argparse.ArgumentTypeError(f"must be between {low} and {high}")
        return value

    return parse


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the periodic Parent story sweep")
    parser.add_argument("--once", action="store_true", help="run one pass and exit")
    parser.add_argument("--interval-seconds", type=_positive_int(1, 3600), default=None)
    parser.add_argument("--batch-size", type=_positive_int(1, MAX_BATCH_SIZE), default=None)
    parser.add_argument("--heartbeat-file", type=Path, default=None)
    args = parser.parse_args(argv)
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level.upper(),
        stream=sys.stdout,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    if not settings.story_sweep_enabled:
        _LOG.info("story_sweep_disabled")
        return 0
    interval = args.interval_seconds or settings.story_sweep_interval_seconds
    batch = args.batch_size or settings.story_sweep_batch_size
    engine = create_core_engine()
    try:
        steps = _steps_for(settings, engine)

        def run_pass() -> SweepReport:
            return run_pass_locked(engine, steps, batch_size=batch)

        heartbeat = args.heartbeat_file

        def beat() -> None:
            if heartbeat is not None:
                heartbeat.touch()

        if args.once:
            try:
                report = run_pass()
            except Exception as exc:
                _LOG.warning("story_sweep_pass_failed kind=%s", type(exc).__name__)
                return 1
            if not report.errors:
                beat()
            return 1 if report.errors else 0
        stop = threading.Event()

        def request_stop(_signal: int, _frame: FrameType | None) -> Any:
            stop.set()

        signal.signal(signal.SIGTERM, request_stop)
        signal.signal(signal.SIGINT, request_stop)
        run_loop(run_pass, interval_seconds=interval, wait=stop.wait, on_success=beat)
        return 0
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
