"""HTTP boundary for reading the active system-managed Parent policy."""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from sketch2life.application.ports.parent_consent_policies import (
    ParentConsentPolicyRecord,
    ParentConsentPolicyRepositoryError,
)
from sketch2life.infrastructure.persistence.parent_consent_policy_repository import (
    SqlParentConsentPolicyRepository,
)


def find_active_parent_consent_policy(
    db: Session,
) -> ParentConsentPolicyRecord | None:
    try:
        return SqlParentConsentPolicyRepository(db).get_active_policy()
    except ParentConsentPolicyRepositoryError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"code": exc.code},
        ) from None


def require_active_parent_consent_policy(db: Session) -> ParentConsentPolicyRecord:
    policy = find_active_parent_consent_policy(db)
    if policy is None:
        raise HTTPException(
            status_code=503,
            detail={"code": "PARENT_CONSENT_POLICY_UNAVAILABLE"},
        )
    return policy


__all__ = [
    "find_active_parent_consent_policy",
    "require_active_parent_consent_policy",
]
