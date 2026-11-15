"""Authenticated, read-only local Parent quota display."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.services.local_parent_video_quota import (
    LocalParentVideoQuotaService,
    LocalParentVideoQuotaUnavailable,
)
from sketch2life.contracts.schemas.parent_video_quota import ParentVideoQuotaSummaryV1
from sketch2life.infrastructure.config.settings import get_settings
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult

router = APIRouter(prefix="/api/billing/v1", tags=["Parent quota v1"])


@router.get(
    "/video-quota",
    response_model=ParentVideoQuotaSummaryV1,
    summary="Read the local demo Parent video-quota display",
)
def get_parent_video_quota(
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentVideoQuotaSummaryV1:
    identity = db.get(AdultIdentityModel, principal.subject)
    if (
        identity is None
        or identity.state != "active"
        or identity.account_role != "parent"
        or identity.issuer != principal.issuer
    ):
        raise HTTPException(status_code=403, detail={"code": "PARENT_ROLE_REQUIRED"})

    try:
        settings = get_settings()
        if settings.env != "local":
            raise LocalParentVideoQuotaUnavailable
        return LocalParentVideoQuotaService().get_summary(
            granted=settings.local_demo_parent_video_quota_granted,
            used=settings.local_demo_parent_video_quota_used,
        )
    except LocalParentVideoQuotaUnavailable:
        raise HTTPException(
            status_code=503,
            detail={"code": "LOCAL_DEMO_QUOTA_UNAVAILABLE"},
        ) from None


__all__ = ["router"]
