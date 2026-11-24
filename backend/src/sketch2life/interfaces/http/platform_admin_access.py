"""Shared HTTP authorization rule for Platform Admin-only operations."""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel


def require_platform_admin(
    db: Session, principal: VerifiedPrincipal
) -> AdultIdentityModel:
    identity = db.get(AdultIdentityModel, principal.subject)
    if (
        identity is None
        or identity.state != "active"
        or identity.account_role != "platform_admin"
        or identity.issuer != principal.issuer
    ):
        raise HTTPException(
            status_code=403,
            detail={
                "code": "FORBIDDEN",
                "message": "Platform Admin authority is required",
            },
        )
    return identity


__all__ = ["require_platform_admin"]
