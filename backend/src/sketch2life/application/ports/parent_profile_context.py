"""Persistence port for Parent profile context entries (T-12a)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_profiles import ParentCommandResult
from sketch2life.domain.parent_profile_context import ContextEntryDraft


@dataclass(frozen=True, slots=True)
class ParentContextEntryPage:
    items: list[dict[str, object]]
    next_cursor: str | None


class ParentProfileContextRepository(Protocol):
    def assert_profile_owned(self, *, principal: VerifiedPrincipal, profile_id: UUID) -> None: ...

    def list_context_entries(
        self,
        *,
        principal: VerifiedPrincipal,
        profile_id: UUID,
        limit: int,
        cursor: str | None,
    ) -> ParentContextEntryPage: ...

    def create_context_entry(
        self,
        *,
        principal: VerifiedPrincipal,
        profile_id: UUID,
        entry: ContextEntryDraft,
        idempotency_key: str,
        request_id: str,
    ) -> ParentCommandResult: ...


__all__ = ["ParentContextEntryPage", "ParentProfileContextRepository"]
