"""Application service for Parent profile context entries (T-12a)."""

from __future__ import annotations

from uuid import UUID

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_profile_context import (
    ParentContextEntryPage,
    ParentProfileContextRepository,
)
from sketch2life.application.ports.parent_profiles import ParentCommandResult
from sketch2life.domain.parent_profile_context import ContextEntryDraft, validate_entry
from sketch2life.domain.parent_profiles import validate_idempotency_key


class ParentProfileContextService:
    def __init__(self, repository: ParentProfileContextRepository) -> None:
        self._repository = repository

    def assert_profile_owned(self, *, principal: VerifiedPrincipal, profile_id: UUID) -> None:
        self._repository.assert_profile_owned(principal=principal, profile_id=profile_id)

    def list_context_entries(
        self,
        *,
        principal: VerifiedPrincipal,
        profile_id: UUID,
        limit: int,
        cursor: str | None,
    ) -> ParentContextEntryPage:
        return self._repository.list_context_entries(
            principal=principal, profile_id=profile_id, limit=limit, cursor=cursor
        )

    def create_context_entry(
        self,
        *,
        principal: VerifiedPrincipal,
        profile_id: UUID,
        entry: ContextEntryDraft,
        idempotency_key: str,
        request_id: str,
    ) -> ParentCommandResult:
        validate_idempotency_key(idempotency_key)
        normalized = validate_entry(entry)
        return self._repository.create_context_entry(
            principal=principal,
            profile_id=profile_id,
            entry=normalized,
            idempotency_key=idempotency_key,
            request_id=request_id,
        )
