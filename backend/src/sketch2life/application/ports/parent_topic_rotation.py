"""Account-scoped durable rotation for Parent topic and subject cards."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True)
class ParentTopicRotationAllocation:
    request_id: UUID
    draft_id: UUID
    catalog_revision: str
    cycle_number: int
    set_id: str
    selected_ids: tuple[str, ...]
    replayed: bool


class ParentTopicRotationPort(Protocol):
    def allocate(
        self,
        *,
        account_id: str,
        request_id: UUID,
        draft_id: UUID,
        rotation_kind: str,
        scope_id: str,
        catalog_revision: str,
        candidate_ids: tuple[str, ...],
        request_fingerprint: str,
        batch_size: int = 3,
    ) -> ParentTopicRotationAllocation:
        """Allocate an unseen batch atomically; replay the same request unchanged."""


__all__ = ["ParentTopicRotationAllocation", "ParentTopicRotationPort"]
