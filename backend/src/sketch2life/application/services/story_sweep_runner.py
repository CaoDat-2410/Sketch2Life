"""One pass of the periodic story sweep (FEAT-066 T-1d1-fix; SRS l.1799, l.2867 S12, FR-O-03 l.608).

``run_sweepers_once`` composes the three sweepers that were callable but unscheduled, in the order
that lets each one read what the one before it handed back to the adult: the lost-task reaper
(T-2d-fix), the admission reconciler (T-1a), then the adult-wait closeout and generation deadline
(T-1d1). The pass is a plain, idempotent callable over durable rows; every effect is a
compare-and-set inside the sweeper it calls, so a second pass, a second worker or a live adult
command can only make a row skip. The runner adds no state of its own, no quota, billing, provider
or notification logic, and logs counts only (BR-34 l.278).

A step that raises is counted by the exception class name and never stops the others (the class
name carries no id and no content). The wall clock is read once per pass so every step judges the
same instant.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

_LOG = logging.getLogger(__name__)
DEFAULT_BATCH_SIZE = 50
MAX_BATCH_SIZE = 200  # the smallest bound of the three sweepers (the reaper's)


@dataclass(frozen=True, slots=True)
class SweepStep:
    """One sweeper: ``run(now, batch_size)`` returns its counts (over a session of its own)."""

    name: str
    run: Callable[[datetime, int], Mapping[str, int]]


@dataclass(frozen=True, slots=True)
class SweepReport:
    """What one pass did: counts per step, the failed steps, and whether the lock was busy."""

    steps: tuple[tuple[str, Mapping[str, int]], ...] = ()
    failures: tuple[tuple[str, str], ...] = ()  # (step name, exception class name)
    lock_busy: bool = False

    @property
    def errors(self) -> int:
        return len(self.failures)


def run_sweepers_once(
    now: datetime | None = None,
    *,
    steps: Sequence[SweepStep],
    batch_size: int = DEFAULT_BATCH_SIZE,
    clock: Callable[[], datetime] | None = None,
) -> SweepReport:
    """Run every step once, in order. ``now`` is the test hook (an aware instant)."""

    if not 1 <= batch_size <= MAX_BATCH_SIZE:
        raise ValueError(f"batch_size must be between 1 and {MAX_BATCH_SIZE}")
    instant = now if now is not None else (clock or (lambda: datetime.now(UTC)))()
    if instant.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    results: list[tuple[str, Mapping[str, int]]] = []
    failures: list[tuple[str, str]] = []
    for step in steps:
        try:
            counts = dict(step.run(instant, batch_size))
        except Exception as exc:  # a failing step never stops the next one
            failures.append((step.name, type(exc).__name__))
            _LOG.warning("story_sweep_step_failed step=%s kind=%s", step.name, type(exc).__name__)
            continue
        results.append((step.name, counts))
    report = SweepReport(tuple(results), tuple(failures))
    log_report(report)
    return report


def log_report(report: SweepReport) -> None:
    """One INFO line, counts only: the per-pass heartbeat of the worker (SRS l.1988)."""

    parts = [
        f"{name}.{key}={value}" for name, counts in report.steps for key, value in counts.items()
    ]
    _LOG.info(
        "story_sweep_pass lock_busy=%d errors=%d%s",
        int(report.lock_busy),
        report.errors,
        "".join(f" {part}" for part in parts),
    )


__all__ = [
    "DEFAULT_BATCH_SIZE",
    "MAX_BATCH_SIZE",
    "SweepReport",
    "SweepStep",
    "log_report",
    "run_sweepers_once",
]
