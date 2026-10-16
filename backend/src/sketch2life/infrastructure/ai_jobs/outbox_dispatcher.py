"""Outbox dispatcher entry for BE2-01 Phase B batch B4 test processes (plan Δ6, accepted Q6).

A dispatcher instance has a stable owner id; each ``run_once`` leases a bounded batch and
publishes it through ``AiJobService.dispatch_outbox``. Not wired into the live app.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from sketch2life.application.services.ai_jobs import AiJobService


@dataclass
class OutboxDispatcher:
    service: AiJobService
    owner: str = field(default_factory=lambda: f"dispatcher_{uuid.uuid4().hex[:12]}")

    def run_once(self) -> int:
        return self.service.dispatch_outbox(owner=self.owner)


__all__ = ["OutboxDispatcher"]
