"""Authenticated Parent-owned child profile and data-authorization APIs."""

# ruff: noqa: B008

from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_profiles import ParentProfileRepositoryError
from sketch2life.application.services.parent_profiles import (
    ParentConsentPolicy,
    ParentProfileService,
    ParentProfileServiceError,
)
from sketch2life.contracts.schemas.parent_profiles import (
    ParentConsentPolicyEnvelopeV1,
    ParentConsentPolicyResponseV1,
    ParentDataAuthorizationRequestV1,
    ParentProfileCollectionResponseV1,
    ParentProfileCreateRequestV1,
    ParentProfileEnvelopeV1,
    ParentProfileResponseV1,
    ParentProfileRevisionResponseV1,
    ParentProfileUpdateRequestV1,
)
from sketch2life.infrastructure.config.settings import get_settings
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.infrastructure.persistence.parent_profile_repository import (
    SqlParentProfileRepository,
)
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult

router = APIRouter(prefix="/api/parent/v1", tags=["Parent profiles v1"])


def _service(db: Session) -> tuple[ParentProfileService, str]:
    settings = get_settings()
    policy = ParentConsentPolicy(
        version=settings.parent_consent_policy_version,
        text=settings.parent_consent_policy_text,
    )
    return ParentProfileService(SqlParentProfileRepository(db), policy), policy.version.strip()


def _require_parent(db: Session, principal: VerifiedPrincipal) -> AdultIdentityModel:
    identity = db.get(AdultIdentityModel, principal.subject)
    if (
        identity is None
        or identity.state != "active"
        or identity.account_role != "parent"
        or identity.issuer != principal.issuer
    ):
        raise HTTPException(status_code=403, detail={"code": "PARENT_ROLE_REQUIRED"})
    return identity


def _invoke(callable_, **kwargs):
    try:
        return callable_(**kwargs)
    except (ParentProfileServiceError, ParentProfileRepositoryError) as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"code": exc.code},
        ) from None


def _response(profile, current_policy_version: str) -> ParentProfileResponseV1:
    revision = profile.current_revision
    current_authorization = (
        profile.authorization_state == "GRANTED"
        and profile.authorization_policy_version == current_policy_version
        and bool(current_policy_version)
    )
    return ParentProfileResponseV1(
        parent_profile_id=profile.parent_profile_id,
        state=profile.state,
        current_revision=ParentProfileRevisionResponseV1(
            profile_revision_id=revision.profile_revision_id,
            revision=revision.revision_no,
            age_months=revision.age_months,
            display_name=revision.display_name,
            interests_summary=revision.interests_summary,
            revision_sha256=revision.revision_hash,
            created_at=revision.created_at,
        ),
        authorization_state=profile.authorization_state,
        authorization_policy_version=profile.authorization_policy_version,
        authorization_current=current_authorization,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.get(
    "/consent-policy",
    response_model=ParentConsentPolicyEnvelopeV1,
    summary="Read the active Parent data-authorization policy",
)
def get_parent_consent_policy(
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentConsentPolicyEnvelopeV1:
    _require_parent(db, principal)
    service, _ = _service(db)
    policy = _invoke(service.consent_policy)
    return ParentConsentPolicyEnvelopeV1(
        request_id=str(uuid4()), policy=ParentConsentPolicyResponseV1(**policy)
    )


@router.get(
    "/child-profiles",
    response_model=ParentProfileCollectionResponseV1,
    summary="List child profiles owned by the authenticated Parent",
)
def list_parent_child_profiles(
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentProfileCollectionResponseV1:
    _require_parent(db, principal)
    service, policy_version = _service(db)
    profiles = _invoke(service.list_profiles, owner_subject=principal.subject)
    return ParentProfileCollectionResponseV1(
        request_id=str(uuid4()),
        profiles=[_response(profile, policy_version) for profile in profiles],
    )


@router.post(
    "/child-profiles",
    response_model=ParentProfileEnvelopeV1,
    status_code=status.HTTP_201_CREATED,
    summary="Create a child profile and record explicit data authorization",
)
def create_parent_child_profile(
    payload: ParentProfileCreateRequestV1,
    response: Response,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentProfileEnvelopeV1:
    _require_parent(db, principal)
    service, policy_version = _service(db)
    profile = _invoke(
        service.create_profile,
        owner_subject=principal.subject,
        age_months=payload.age_months,
        display_name=payload.display_name,
        interests_summary=payload.interests_summary,
        consent_accepted=payload.consent_accepted,
        policy_version=payload.consent_policy_version,
    )
    response.headers["ETag"] = f'"{profile.current_revision.revision_no}"'
    return ParentProfileEnvelopeV1(
        request_id=str(uuid4()), profile=_response(profile, policy_version)
    )


@router.get(
    "/child-profiles/{parent_profile_id}",
    response_model=ParentProfileEnvelopeV1,
    summary="Read an owned child profile",
)
def get_parent_child_profile(
    parent_profile_id: UUID,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentProfileEnvelopeV1:
    _require_parent(db, principal)
    service, policy_version = _service(db)
    profile = _invoke(
        service.get_profile,
        owner_subject=principal.subject,
        parent_profile_id=str(parent_profile_id),
    )
    return ParentProfileEnvelopeV1(
        request_id=str(uuid4()), profile=_response(profile, policy_version)
    )


@router.patch(
    "/child-profiles/{parent_profile_id}",
    response_model=ParentProfileEnvelopeV1,
    summary="Create an immutable revision of an owned child profile",
)
def update_parent_child_profile(
    parent_profile_id: UUID,
    payload: ParentProfileUpdateRequestV1,
    response: Response,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentProfileEnvelopeV1:
    _require_parent(db, principal)
    service, policy_version = _service(db)
    profile = _invoke(
        service.revise_profile,
        owner_subject=principal.subject,
        parent_profile_id=str(parent_profile_id),
        expected_revision=payload.expected_revision,
        age_months=payload.age_months,
        display_name=payload.display_name,
        interests_summary=payload.interests_summary,
    )
    response.headers["ETag"] = f'"{profile.current_revision.revision_no}"'
    return ParentProfileEnvelopeV1(
        request_id=str(uuid4()), profile=_response(profile, policy_version)
    )


@router.post(
    "/child-profiles/{parent_profile_id}/data-authorizations",
    response_model=ParentProfileEnvelopeV1,
    summary="Grant the current versioned Parent data authorization",
)
def grant_parent_data_authorization(
    parent_profile_id: UUID,
    payload: ParentDataAuthorizationRequestV1,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentProfileEnvelopeV1:
    _require_parent(db, principal)
    service, policy_version = _service(db)
    profile = _invoke(
        service.grant_authorization,
        owner_subject=principal.subject,
        parent_profile_id=str(parent_profile_id),
        consent_accepted=payload.consent_accepted,
        policy_version=payload.consent_policy_version,
    )
    return ParentProfileEnvelopeV1(
        request_id=str(uuid4()), profile=_response(profile, policy_version)
    )


@router.delete(
    "/child-profiles/{parent_profile_id}/data-authorizations",
    response_model=ParentProfileEnvelopeV1,
    summary="Revoke active Parent data authorizations for an owned profile",
)
def revoke_parent_data_authorization(
    parent_profile_id: UUID,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentProfileEnvelopeV1:
    _require_parent(db, principal)
    service, policy_version = _service(db)
    profile = _invoke(
        service.revoke_authorization,
        owner_subject=principal.subject,
        parent_profile_id=str(parent_profile_id),
    )
    return ParentProfileEnvelopeV1(
        request_id=str(uuid4()), profile=_response(profile, policy_version)
    )


@router.delete(
    "/child-profiles/{parent_profile_id}",
    response_model=ParentProfileEnvelopeV1,
    summary="Archive an owned child profile and revoke its active authorizations",
)
def archive_parent_child_profile(
    parent_profile_id: UUID,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentProfileEnvelopeV1:
    _require_parent(db, principal)
    service, policy_version = _service(db)
    profile = _invoke(
        service.archive_profile,
        owner_subject=principal.subject,
        parent_profile_id=str(parent_profile_id),
    )
    return ParentProfileEnvelopeV1(
        request_id=str(uuid4()), profile=_response(profile, policy_version)
    )


__all__ = ["router"]
