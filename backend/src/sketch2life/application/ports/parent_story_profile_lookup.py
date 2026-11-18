"""Read-only profile snapshot contract for Parent StoryRun creation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from sketch2life.application.ports.identity import VerifiedPrincipal


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


__all__ = [
    "ParentStoryProfileLookupPort",
    "ParentStoryProfileLookupUnavailable",
    "ParentStoryProfileReference",
]
