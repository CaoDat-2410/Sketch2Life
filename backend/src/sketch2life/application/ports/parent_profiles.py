"""Persistence port for Parent profile commands and projections."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.domain.parent_profiles import ProfileSnapshot


@dataclass(frozen=True, slots=True)
class ParentCommandResult:
    status_code: int
    body: dict[str, object]


class ParentProfileRepository(Protocol):
    def create_profile(
        self,
        *,
        principal: VerifiedPrincipal,
        snapshot: ProfileSnapshot,
        idempotency_key: str,
        request_id: str,
    ) -> ParentCommandResult: ...

    def get_profile(
        self, *, principal: VerifiedPrincipal, profile_id: UUID
    ) -> dict[str, object]: ...

    def patch_profile(
        self,
        *,
        principal: VerifiedPrincipal,
        profile_id: UUID,
        expected_revision: int,
        snapshot: ProfileSnapshot,
        idempotency_key: str,
        request_id: str,
    ) -> ParentCommandResult: ...
