"""Platform Admin APIs for versioned Parent consent policies."""

# ruff: noqa: B008

from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_consent_policies import (
    ParentConsentPolicyRepositoryError,
)
from sketch2life.application.services.parent_consent_policies import (
    ParentConsentPolicyService,
    ParentConsentPolicyServiceError,
)
from sketch2life.contracts.schemas.parent_consent_policies import (
    ParentConsentPolicyAdminCollectionV1,
    ParentConsentPolicyAdminEnvelopeV1,
    ParentConsentPolicyAdminResponseV1,
    ParentConsentPolicyCreateRequestV1,
)
from sketch2life.infrastructure.persistence.parent_consent_policy_repository import (
    SqlParentConsentPolicyRepository,
)
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.platform_admin_access import require_platform_admin

router = APIRouter(
    prefix="/api/platform-admin/v1/parent-consent-policies",
    tags=["Platform Admin Parent consent policies v1"],
)


def _service(db: Session) -> ParentConsentPolicyService:
    return ParentConsentPolicyService(SqlParentConsentPolicyRepository(db))


def _invoke(callable_, **kwargs):
    try:
        return callable_(**kwargs)
    except (ParentConsentPolicyRepositoryError, ParentConsentPolicyServiceError) as exc:
        raise HTTPException(status_code=exc.status_code, detail={"code": exc.code}) from None


def _response(policy) -> ParentConsentPolicyAdminResponseV1:
    return ParentConsentPolicyAdminResponseV1(
        policy_id=policy.policy_id,
        policy_version=policy.version,
        purpose_code=policy.purpose_code,
        consent_text=policy.text,
        consent_text_sha256=policy.text_sha256,
        state=policy.state,
        created_by=policy.created_by,
        created_at=policy.created_at,
        activated_by=policy.activated_by,
        activated_at=policy.activated_at,
    )


@router.get("", response_model=ParentConsentPolicyAdminCollectionV1)
def list_parent_consent_policies(
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentConsentPolicyAdminCollectionV1:
    require_platform_admin(db, principal)
    policies = _invoke(_service(db).list_policies)
    active_policy_id = next((item.policy_id for item in policies if item.state == "ACTIVE"), None)
    return ParentConsentPolicyAdminCollectionV1(
        request_id=str(uuid4()),
        active_policy_id=active_policy_id,
        policies=[_response(item) for item in policies],
    )


@router.post(
    "",
    response_model=ParentConsentPolicyAdminEnvelopeV1,
    status_code=status.HTTP_201_CREATED,
)
def create_parent_consent_policy_draft(
    payload: ParentConsentPolicyCreateRequestV1,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentConsentPolicyAdminEnvelopeV1:
    require_platform_admin(db, principal)
    policy = _invoke(
        _service(db).create_draft,
        version=payload.policy_version,
        text=payload.consent_text,
        actor_subject=principal.subject,
    )
    return ParentConsentPolicyAdminEnvelopeV1(
        request_id=str(uuid4()), policy=_response(policy)
    )


@router.post(
    "/{policy_id}/activate",
    response_model=ParentConsentPolicyAdminEnvelopeV1,
)
def activate_parent_consent_policy(
    policy_id: UUID,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentConsentPolicyAdminEnvelopeV1:
    require_platform_admin(db, principal)
    policy = _invoke(
        _service(db).activate,
        policy_id=str(policy_id),
        actor_subject=principal.subject,
    )
    return ParentConsentPolicyAdminEnvelopeV1(
        request_id=str(uuid4()), policy=_response(policy)
    )


__all__ = ["router"]
