"""The adult-wait closeout and the generation deadline sweep (FEAT-066 T-1d1; SRS l.394-395, l.503).

``StoryRunCloseoutService.run_once`` is one bounded pass; the periodic runner
(``infrastructure/story_video/sweep_worker``) calls it. It does two independent things, each row in
its own transaction:

* a generation accepted more than six hours ago and not settled ends ``FAILED`` with
  ``VIDEO_DEADLINE_EXCEEDED`` through the T-1a progress step (the compute reservation settled or
  released, the quota unit never refunded: l.395, l.573). The failed request still counts toward
  the three-request cap, so the run returns to ``SCRIPT_REVIEW`` with a new adult wait (l.2120,
  BR-11 l.255, the same path as a refused admission, l.503); when the cap is spent the run ends
  ``FAILED`` and the lock is released (l.2119);
* a run idle for 168 hours is closed: ``VIDEO_READY`` to ``COMPLETED``, every other adult-wait state
  to ``ABANDONED``; the owner lock is released and the content is kept (l.503).

Both are compare-and-set, so a second pass, a second worker or a live adult command can only make a
row skip. A refused video admission is not special here: it put the run back in ``SCRIPT_REVIEW``
with a new wait clock when it happened. Nothing is written to the audit log, the outbox or any
notification channel (FR-C-11 asks for none of them), and only counts are logged (BR-34).
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime

from sketch2life.application.ports.story_run_closeout import (
    CloseoutOutcome,
    CloseoutReport,
    GenerationProgress,
    StoryRunCloseoutStore,
)
from sketch2life.application.ports.story_video import ProgressEvent
from sketch2life.domain.story_run_closeout import VIDEO_DEADLINE_EXCEEDED
from sketch2life.domain.story_video.model import GenerationState

_LOG = logging.getLogger(__name__)
DEFAULT_BATCH_SIZE = 50
MAX_BATCH_SIZE = 500


class StoryRunCloseoutService:
    def __init__(
        self,
        store: StoryRunCloseoutStore,
        progress: GenerationProgress | None,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._store = store
        self._progress = progress
        self._clock = clock or (lambda: datetime.now(UTC))

    def run_once(
        self, now: datetime | None = None, *, batch_size: int = DEFAULT_BATCH_SIZE
    ) -> CloseoutReport:
        """One pass. ``now`` is the test hook (an aware instant); the default is the clock."""

        if not 1 <= batch_size <= MAX_BATCH_SIZE:
            raise ValueError("batch_size must be between 1 and 500")
        instant = now if now is not None else self._clock()
        if instant.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        completed = abandoned = failed = skipped = errors = 0
        if self._progress is not None:
            try:
                overdue = self._store.overdue_generations(instant, batch_size)
            except Exception as exc:  # the listing failed: the idle pass still runs
                _LOG.warning("story_run_closeout_listing_failed kind=%s", type(exc).__name__)
                overdue = []
                errors += 1
            for generation in overdue:
                try:
                    result = self._progress.apply(
                        generation.generation_id,
                        ProgressEvent(
                            expected_state=generation.state,
                            target_state=str(GenerationState.FAILED),
                            safe_failure_code=VIDEO_DEADLINE_EXCEEDED,
                            return_to_script_review=True,
                        ),
                    )
                except Exception as exc:  # one row never stops the batch
                    _LOG.warning("story_run_closeout_row_failed kind=%s", type(exc).__name__)
                    errors += 1
                    continue
                if result.applied:
                    failed += 1
                else:
                    skipped += 1
        try:
            candidates = self._store.idle_candidates(instant, batch_size)
        except Exception as exc:
            _LOG.warning("story_run_closeout_listing_failed kind=%s", type(exc).__name__)
            candidates = []
            errors += 1
        for candidate in candidates:
            try:
                outcome = self._store.close_idle(candidate.run_id, instant)
            except Exception as exc:
                _LOG.warning("story_run_closeout_row_failed kind=%s", type(exc).__name__)
                errors += 1
                continue
            if outcome is CloseoutOutcome.COMPLETED:
                completed += 1
            elif outcome is CloseoutOutcome.ABANDONED:
                abandoned += 1
            else:
                skipped += 1
        report = CloseoutReport(completed, abandoned, failed, skipped, errors)
        _LOG.info(
            "story_run_closeout completed=%d abandoned=%d deadline_failed=%d skipped=%d errors=%d",
            report.completed,
            report.abandoned,
            report.deadline_failed,
            report.skipped,
            report.errors,
        )
        return report


__all__ = ["DEFAULT_BATCH_SIZE", "MAX_BATCH_SIZE", "StoryRunCloseoutService"]
