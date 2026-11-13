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


@dataclass(frozen=True, slots=True)
class ParentProfileListResult:
    items: list[dict[str, object]]
    next_cursor: str | None


class ParentProfileRepository(Protocol):
    def assert_profile_owned(
        self, *, principal: VerifiedPrincipal, profile_id: UUID
    ) -> None: ...

    def create_profile(
        self,
        *,
        principal: VerifiedPrincipal,
        snapshot: ProfileSnapshot,
        idempotency_key: str,
        request_id: str,
    ) -> ParentCommandResult: ...

    def get_profile(
        self, *, principal: VerifiedPrincipal, profile_id: UUID, request_id: str
    ) -> dict[str, object]: ...

    def list_profiles(
        self,
        *,
        principal: VerifiedPrincipal,
        limit: int,
        cursor: str | None,
    ) -> ParentProfileListResult: ...

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

    def delete_profile(
        self,
        *,
        principal: VerifiedPrincipal,
        profile_id: UUID,
        idempotency_key: str,
        request_id: str,
    ) -> ParentCommandResult: ...
