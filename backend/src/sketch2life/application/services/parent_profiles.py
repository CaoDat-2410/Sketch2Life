"""Application services for the synthetic Parent profile foundation."""

from __future__ import annotations

from uuid import UUID

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_profiles import (
    ParentCommandResult,
    ParentProfileListResult,
    ParentProfileRepository,
)
from sketch2life.domain.parent_profiles import (
    ParentProfileError,
    ProfileSnapshot,
    validate_snapshot,
)


class ParentProfileService:
    def __init__(self, repository: ParentProfileRepository, *, synthetic_enabled: bool) -> None:
        self._repository = repository
        self._synthetic_enabled = synthetic_enabled

    def create_profile(
        self,
        *,
        principal: VerifiedPrincipal,
        snapshot: ProfileSnapshot,
        idempotency_key: str,
        request_id: str,
    ) -> ParentCommandResult:
        self._validate_key(idempotency_key)
        validate_snapshot(snapshot)
        if not self._synthetic_enabled:
            raise ParentProfileError(
                409,
                "SYNTHETIC_PROFILE_CREATION_UNAVAILABLE",
                "Synthetic Parent profile creation is unavailable",
            )
        return self._repository.create_profile(
            principal=principal,
            snapshot=snapshot,
            idempotency_key=idempotency_key,
            request_id=request_id,
        )

    def assert_profile_owned(
        self, *, principal: VerifiedPrincipal, profile_id: UUID
    ) -> None:
        self._repository.assert_profile_owned(principal=principal, profile_id=profile_id)

    def get_profile(
        self, *, principal: VerifiedPrincipal, profile_id: UUID, request_id: str
    ) -> dict[str, object]:
        return self._repository.get_profile(
            principal=principal, profile_id=profile_id, request_id=request_id
        )

    def list_profiles(
        self,
        *,
        principal: VerifiedPrincipal,
        limit: int,
        cursor: str | None,
    ) -> ParentProfileListResult:
        return self._repository.list_profiles(
            principal=principal, limit=limit, cursor=cursor
        )

    def patch_profile(
        self,
        *,
        principal: VerifiedPrincipal,
        profile_id: UUID,
        expected_revision: int,
        snapshot: ProfileSnapshot,
        idempotency_key: str,
        request_id: str,
    ) -> ParentCommandResult:
        self._validate_key(idempotency_key)
        validate_snapshot(snapshot)
        return self._repository.patch_profile(
            principal=principal,
            profile_id=profile_id,
            expected_revision=expected_revision,
            snapshot=snapshot,
            idempotency_key=idempotency_key,
            request_id=request_id,
        )

    def delete_profile(
        self,
        *,
        principal: VerifiedPrincipal,
        profile_id: UUID,
        idempotency_key: str,
        request_id: str,
    ) -> ParentCommandResult:
        self._validate_key(idempotency_key)
        return self._repository.delete_profile(
            principal=principal,
            profile_id=profile_id,
            idempotency_key=idempotency_key,
            request_id=request_id,
        )

    @staticmethod
    def _validate_key(value: str) -> None:
        if not 1 <= len(value) <= 128 or any(
            ord(char) < 33 or ord(char) > 126 for char in value
        ):
            raise ParentProfileError(
                400,
                "INVALID_REQUEST",
                "The idempotency key is invalid",
                field_errors=[{"field": "Idempotency-Key", "code": "INVALID_FORMAT"}],
            )
