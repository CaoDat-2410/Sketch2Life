"""Application service for the Parent support needs (T-12c).

Ownership and the active-Parent role are checked by the router before any call here; this service
validates the adult input, insists on a key source, and delegates to the repository. It never
logs, caches or returns a value other than the one decrypted for an authorized GET.
"""

from __future__ import annotations

from uuid import UUID

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.support_needs import (
    ParentSupportNeedsRepository,
    SupportNeedsCrypto,
)
from sketch2life.domain.parent_profiles import ParentProfileError, validate_idempotency_key
from sketch2life.domain.support_needs import SupportNeedsRuleViolation, validate_payload


class ParentSupportNeedsService:
    def __init__(
        self, repository: ParentSupportNeedsRepository, crypto: SupportNeedsCrypto | None
    ) -> None:
        self._repository = repository
        self._crypto = crypto

    def assert_profile_owned(self, *, principal: VerifiedPrincipal, profile_id: UUID) -> None:
        self._repository.assert_profile_owned(principal=principal, profile_id=profile_id)

    def require_available(self) -> SupportNeedsCrypto:
        """503 without a key source (gate O-SEED-KEY); checked after authorization."""
        if self._crypto is None:
            raise ParentProfileError(
                503, "SUPPORT_NEEDS_UNAVAILABLE", "Support needs are unavailable"
            )
        return self._crypto

    def get_support_needs(
        self, *, principal: VerifiedPrincipal, profile_id: UUID
    ) -> dict[str, object]:
        crypto = self.require_available()
        return self._repository.get_support_needs(
            principal=principal, profile_id=profile_id, crypto=crypto
        )

    def put_support_needs(
        self,
        *,
        principal: VerifiedPrincipal,
        profile_id: UUID,
        expected_revision: int,
        category: str | None,
        note: str | None,
        idempotency_key: str,
    ) -> dict[str, object]:
        crypto = self.require_available()
        validate_idempotency_key(idempotency_key)
        try:
            payload = validate_payload(category, note)
        except SupportNeedsRuleViolation as violation:
            raise ParentProfileError(
                400,
                "INVALID_REQUEST",
                "The request is invalid",
                field_errors=[{"field": violation.field, "code": violation.code}],
            ) from None
        return self._repository.put_support_needs(
            principal=principal,
            profile_id=profile_id,
            expected_revision=expected_revision,
            payload=payload,
            idempotency_key=idempotency_key,
            crypto=crypto,
        )
