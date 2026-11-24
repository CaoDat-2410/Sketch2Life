"""Read-only profile snapshot contract for Parent StoryRun creation."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.domain.parent_profile_context import SelectedContextEntry


@dataclass(frozen=True, slots=True)
class ParentStoryProfileReference:
    profile_id: UUID
    profile_revision_id: UUID
    state: str
    data_origin: str
    age_months: int
    interests_summary: str | None


class ParentStoryProfileLookupUnavailable(RuntimeError):
    """The current Parent profile revision could not be read consistently."""


class ParentStoryProfileLookupPort(Protocol):
    def get_owned_profile_current_revision(
        self, *, principal: VerifiedPrincipal, profile_id: UUID
    ) -> ParentStoryProfileReference | None: ...

    def is_owned_profile(self, *, principal: VerifiedPrincipal, profile_id: UUID) -> bool:
        """FEAT-081 C3b: ownership only, any profile state, no revision read."""
        ...

    def resolve_selected_context_entries(
        self,
        *,
        principal: VerifiedPrincipal,
        profile_id: UUID,
        entry_ids: Sequence[UUID],
    ) -> list[SelectedContextEntry] | None:
        """T-12a: the ``{kind, text}`` of the named entries in ``(created_at, id)`` order, or
        ``None`` when any id is not an entry of this ACTIVE profile of the caller (a profile in
        ``DELETE_PENDING`` resolves nothing). The profile row is share-locked."""
        ...


__all__ = [
    "ParentStoryProfileLookupPort",
    "ParentStoryProfileLookupUnavailable",
    "ParentStoryProfileReference",
]
