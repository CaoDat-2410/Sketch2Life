"""SQL reconciler entry for BE2-01 Phase B batch B4 test processes (plan Δ7, Δ11, Δ13).

One pass runs the three targeted, paged sweeps: unstarted dispatches (same-attempt republish up
to the publish bound, then dispatch loss), overdue running attempts (policy timeout) and due
retries. Each sweep re-reads under the job row lock before changing anything. Not a general
scheduler and not wired into the live app.
"""

from __future__ import annotations

from dataclasses import dataclass

from sketch2life.application.services.ai_jobs import AiJobService


@dataclass(frozen=True, slots=True)
class ReconcilerPass:
    unstarted: tuple[tuple[str, str], ...]
    overdue: tuple[str, ...]
    retried: tuple[str, ...]


@dataclass
class Reconciler:
    service: AiJobService

    def run_once(self) -> ReconcilerPass:
        return ReconcilerPass(
            unstarted=self.service.recover_unstarted_dispatches(),
            overdue=self.service.expire_overdue_attempts(),
            retried=self.service.run_due_retries(),
        )


__all__ = ["Reconciler", "ReconcilerPass"]
