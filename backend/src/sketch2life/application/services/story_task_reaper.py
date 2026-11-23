"""The lost-background-task reaper of the Parent story runs (FEAT-066 T-2d-fix; SRS l.394, l.615).

``StoryTaskReaperService.run_once`` is one bounded pass and nothing schedules it yet (the periodic
runner slice owns that, the same release as the T-1a reconciler and the T-1d1 closeout). It closes
the work a dead worker left behind, each row in its own transaction:

* a drawing analysis that never reported (K1 lost, K2 unknown outcome): the job fails with
  ``PROVIDER_TIMEOUT`` and the run goes back to ``INPUT_REVIEW``/``SUBJECT_REVIEW``;
* a speech transcription that never reported (K3): the transcript fails and the adult can type;
* a story generation that never reported (K4 lost, K5 unknown outcome): a rewrite returns to the
  previous story (``SCRIPT_REVIEW``, job ``FAILED``); a first story ends the run ``FAILED``.

Only the 6 h AI job deadline is licensed by the SRS (l.394, l.615). A shorter inactivity
lease for a QUEUED/RUNNING job has no SRS number, so ``lease`` is a required argument bounded by
that deadline; the future scheduler passes 6 h unless the owner sets less. Every effect is a
compare-and-set under the run lock, so a second pass, a second worker, a live adult command or a
late worker result can only make a row skip. Only counts are logged (BR-34).
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from sketch2life.application.ports.story_task_reaper import (
    AI_JOB_DEADLINE,
    ReapKind,
    ReapOutcome,
    ReapReport,
    StoryTaskReaperStore,
)

_LOG = logging.getLogger(__name__)
DEFAULT_BATCH_SIZE = 50
MAX_BATCH_SIZE = 200
_LEASE_KINDS = (ReapKind.DRAWING_LOST, ReapKind.TRANSCRIPT_LOST, ReapKind.STORY_LOST)
_UNKNOWN_KINDS = (ReapKind.DRAWING_UNKNOWN, ReapKind.STORY_UNKNOWN)


class StoryTaskReaperService:
    def __init__(
        self, store: StoryTaskReaperStore, *, clock: Callable[[], datetime] | None = None
    ) -> None:
        self._store = store
        self._clock = clock or (lambda: datetime.now(UTC))

    def run_once(
        self,
        *,
        lease: timedelta,
        now: datetime | None = None,
        unknown_deadline: timedelta = AI_JOB_DEADLINE,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> ReapReport:
        """One pass. ``now`` is the test hook (an aware instant); the default is the clock.

        ``lease`` is the inactivity time after which a QUEUED/RUNNING story job is lost
        (``0 < lease <= 6 h``); ``unknown_deadline`` is the time an unknown outcome waits for its
        reconciliation before the run is released (``0 < unknown_deadline <= 6 h``, default 6 h).
        ``batch_size`` (1..200) bounds the rows one pass touches, in the order of the kinds.
        """

        if not timedelta(0) < lease <= AI_JOB_DEADLINE:
            raise ValueError("lease must be positive and at most the 6 h AI job deadline")
        if not timedelta(0) < unknown_deadline <= AI_JOB_DEADLINE:
            raise ValueError("unknown_deadline must be positive and at most 6 h")
        if not 1 <= batch_size <= MAX_BATCH_SIZE:
            raise ValueError("batch_size must be between 1 and 200")
        instant = now if now is not None else self._clock()
        if instant.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        counts = {outcome: 0 for outcome in ReapOutcome}
        errors = 0
        remaining = batch_size
        for kind in (*_LEASE_KINDS, *_UNKNOWN_KINDS):
            if remaining <= 0:
                break
            cutoff = instant - (lease if kind in _LEASE_KINDS else unknown_deadline)
            try:
                candidates = self._store.list_candidates(kind, cutoff, remaining)
            except Exception as exc:  # a listing failed: the other kinds still run
                _LOG.warning("story_task_reaper_listing_failed kind=%s", type(exc).__name__)
                errors += 1
                continue
            for candidate in candidates:
                remaining -= 1
                try:
                    outcome = self._store.reap(candidate, instant, cutoff)
                except Exception as exc:  # one row never stops the batch
                    _LOG.warning("story_task_reaper_row_failed kind=%s", type(exc).__name__)
                    errors += 1
                    continue
                counts[outcome] += 1
        report = ReapReport(
            drawing_timed_out=counts[ReapOutcome.DRAWING_TIMED_OUT],
            transcript_timed_out=counts[ReapOutcome.TRANSCRIPT_TIMED_OUT],
            rewrite_recovered=counts[ReapOutcome.REWRITE_RECOVERED],
            story_failed=counts[ReapOutcome.STORY_FAILED],
            skipped=counts[ReapOutcome.SKIPPED],
            errors=errors,
        )
        _LOG.info(
            "story_task_reaper drawing=%d transcript=%d rewrite_recovered=%d story_failed=%d "
            "skipped=%d errors=%d",
            report.drawing_timed_out,
            report.transcript_timed_out,
            report.rewrite_recovered,
            report.story_failed,
            report.skipped,
            report.errors,
        )
        return report


__all__ = ["DEFAULT_BATCH_SIZE", "MAX_BATCH_SIZE", "StoryTaskReaperService"]
