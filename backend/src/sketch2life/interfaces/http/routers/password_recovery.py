"""Neutral password recovery; only the outbox owns email delivery."""

# ruff: noqa: B008
import hashlib
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import IdentityAccountProvisioningUnavailable
from sketch2life.contracts.schemas.platform_admin import PasswordRecoveryInput
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.infrastructure.persistence.platform_models import EmailDeliveryModel
from sketch2life.interfaces.http.be1_runtime import get_db
from sketch2life.interfaces.http.routers.auth_registration import RegistrationRateLimiter

router = APIRouter(prefix="/api/auth/v1", tags=["authentication"])
limiter = RegistrationRateLimiter()


@router.post("/password-recovery", status_code=202)
def recovery(payload: PasswordRecoveryInput, request: Request, db: Session = Depends(get_db)):
    address = request.client.host if request.client else "unknown"
    if not limiter.allow(hashlib.sha256(address.encode()).hexdigest()):
        raise HTTPException(
            429, detail={"code": "RATE_LIMITED", "message": "Please try again later"}
        )
    try:
        provider = request.app.state.identity_account_provisioner
        identity = provider.find_account_by_email(payload.email.lower())
        if identity is not None:
            account = db.get(AdultIdentityModel, identity.subject)
            if (
                account
                and account.state in {"active", "pending_verification"}
                and account.issuer == identity.issuer
            ):
                db.add(
                    EmailDeliveryModel(
                        delivery_id=str(uuid4()),
                        recipient_ref=identity.subject,
                        template="password_recovery",
                        state="pending",
                        attempts=0,
                    )
                )
                db.commit()
    except IdentityAccountProvisioningUnavailable:
        # Provider diagnostics are retained at the adapter boundary, never returned to a caller.
        pass
    return {"status": "RECOVERY_REQUESTED"}
