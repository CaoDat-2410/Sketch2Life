"""Scoped quota commerce endpoints for Parents and School Managers."""

from typing import Any

# FastAPI dependency declarations intentionally use Depends in defaults.
# ruff: noqa: B008
from fastapi import APIRouter, Depends, Header, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.contracts.schemas.platform_admin import QuotaAllocationInput, QuotaCheckoutInput
from sketch2life.domain.platform_admin import AdminError
from sketch2life.infrastructure.billing.quota_commerce import QuotaCommerceService, scope_for_be1
from sketch2life.infrastructure.config.settings import get_settings
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    OrganizationAssignmentModel,
)
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.routers.be1_common import (
    BE1_ERROR_RESPONSES,
    failure,
    require_assignment,
)

router = APIRouter(responses=BE1_ERROR_RESPONSES)  # type: ignore[arg-type]


def _commerce(db: Session, principal: VerifiedPrincipal) -> QuotaCommerceService:
    return QuotaCommerceService(db, principal.subject, get_settings())


def _run(operation: Any) -> Any:
    try:
        return operation()
    except AdminError as exc:
        raise failure(exc.status, exc.code, exc.code) from None


def _payment_settings() -> dict[str, Any]:
    settings = get_settings()
    return {
        "real_payments_enabled": settings.billing_real_payments_enabled
        and (settings.momo_payment_configured or settings.vnpay_payment_configured),
        "momo_checkout_enabled": settings.billing_real_payments_enabled
        and settings.momo_payment_configured,
        "momo_sandbox_enabled": settings.momo_sandbox_enabled,
        "vnpay_checkout_enabled": settings.billing_real_payments_enabled
        and settings.vnpay_payment_configured,
        "vnpay_sandbox_enabled": settings.vnpay_sandbox_enabled,
        "monthly_auto_renew_enabled": False,
    }


@router.get("/api/be1/v1/billing/video-quota/payment-settings", tags=["BE1 quota"])
def personal_payment_settings(
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> Any:
    return _run(lambda: (scope_for_be1(db, principal), _payment_settings())[1])


@router.get("/api/be1/v1/billing/video-quota/products", tags=["BE1 quota"])
def personal_products(
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> Any:
    def execute() -> Any:
        owner_kind, _ = scope_for_be1(db, principal)
        return _commerce(db, principal).products(owner_kind)

    return _run(execute)


@router.get("/api/be1/v1/billing/video-quota", tags=["BE1 quota"])
def personal_quota(
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> Any:
    def execute() -> Any:
        kind, ref = scope_for_be1(db, principal)
        return _commerce(db, principal).quota_summary(kind, ref)

    return _run(execute)


@router.get("/api/be1/v1/billing/video-quota/invoices", tags=["BE1 quota"])
def personal_invoices(
    limit: int = Query(50, ge=1, le=100),
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> Any:
    def execute() -> Any:
        kind, ref = scope_for_be1(db, principal)
        return _commerce(db, principal).invoices(kind, ref, limit=limit)

    return _run(execute)


@router.post("/api/be1/v1/billing/video-quota/checkout", tags=["BE1 quota"], status_code=201)
def personal_checkout(
    payload: QuotaCheckoutInput,
    request: Request,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=128),
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> Any:
    def execute() -> Any:
        kind, ref = scope_for_be1(db, principal)
        return _commerce(db, principal).checkout(
            payload.product_id,
            kind,
            ref,
            payload.provider,
            payload.payment_mode,
            idempotency_key,
            request.client.host if request.client else "127.0.0.1",
        )

    return _run(execute)


@router.post(
    "/api/be1/v1/billing/video-quota/invoices/{invoice_id}/reconcile",
    tags=["BE1 quota"],
)
def reconcile_personal_invoice(
    invoice_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> Any:
    def execute() -> Any:
        kind, ref = scope_for_be1(db, principal)
        commerce = _commerce(db, principal)
        invoice = commerce.invoice(invoice_id)
        if invoice.owner_kind != kind or invoice.owner_ref != ref:
            raise AdminError("INVOICE_NOT_FOUND", 404)
        return commerce.reconcile_invoice(invoice_id)

    return _run(execute)


@router.post(
    "/api/be1/v1/billing/video-quota/invoices/{invoice_id}/cancel",
    tags=["BE1 quota"],
)
def cancel_personal_invoice(
    invoice_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> Any:
    def execute() -> Any:
        kind, ref = scope_for_be1(db, principal)
        commerce = _commerce(db, principal)
        invoice = commerce.invoice(invoice_id)
        if invoice.owner_kind != kind or invoice.owner_ref != ref:
            raise AdminError("INVOICE_NOT_FOUND", 404)
        return commerce.cancel_expired_vnpay_invoice(invoice_id)

    return _run(execute)


@router.get("/api/be1/v1/organizations/{organization_id}/video-quota", tags=["BE1 quota"])
def school_quota(
    organization_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> Any:
    def execute() -> Any:
        require_assignment(db, principal, organization_id, roles={"school_admin"})
        return _commerce(db, principal).quota_summary("ORGANIZATION", organization_id)

    return _run(execute)


@router.get("/api/be1/v1/organizations/{organization_id}/video-quota/products", tags=["BE1 quota"])
def school_products(
    organization_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> Any:
    def execute() -> Any:
        require_assignment(db, principal, organization_id, roles={"school_admin"})
        return _commerce(db, principal).products("ORGANIZATION")

    return _run(execute)


@router.get(
    "/api/be1/v1/organizations/{organization_id}/video-quota/payment-settings", tags=["BE1 quota"]
)
def school_payment_settings(
    organization_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> Any:
    def execute() -> Any:
        require_assignment(db, principal, organization_id, roles={"school_admin"})
        return _payment_settings()

    return _run(execute)


@router.get("/api/be1/v1/organizations/{organization_id}/video-quota/teachers", tags=["BE1 quota"])
def school_quota_teachers(
    organization_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> Any:
    def execute() -> Any:
        require_assignment(db, principal, organization_id, roles={"school_admin"})
        subjects = db.scalars(
            select(OrganizationAssignmentModel.subject)
            .join(
                AdultIdentityModel,
                AdultIdentityModel.subject == OrganizationAssignmentModel.subject,
            )
            .where(
                OrganizationAssignmentModel.organization_id == organization_id,
                OrganizationAssignmentModel.role == "teacher",
                OrganizationAssignmentModel.active.is_(True),
                AdultIdentityModel.account_role == "teacher",
                AdultIdentityModel.state == "active",
            )
            .distinct()
            .order_by(OrganizationAssignmentModel.subject)
        )
        return {
            "items": [
                {"teacher_ref": subject, "label": "Giáo viên · " + subject[-6:]}
                for subject in subjects
            ]
        }

    return _run(execute)


@router.get("/api/be1/v1/organizations/{organization_id}/video-quota/invoices", tags=["BE1 quota"])
def school_invoices(
    organization_id: str,
    limit: int = Query(50, ge=1, le=100),
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> Any:
    def execute() -> Any:
        require_assignment(db, principal, organization_id, roles={"school_admin"})
        return _commerce(db, principal).invoices("ORGANIZATION", organization_id, limit=limit)

    return _run(execute)


@router.post(
    "/api/be1/v1/organizations/{organization_id}/video-quota/invoices/{invoice_id}/reconcile",
    tags=["BE1 quota"],
)
def reconcile_school_invoice(
    organization_id: str,
    invoice_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> Any:
    def execute() -> Any:
        require_assignment(db, principal, organization_id, roles={"school_admin"})
        commerce = _commerce(db, principal)
        invoice = commerce.invoice(invoice_id)
        if invoice.owner_kind != "ORGANIZATION" or invoice.owner_ref != organization_id:
            raise AdminError("INVOICE_NOT_FOUND", 404)
        return commerce.reconcile_invoice(invoice_id)

    return _run(execute)


@router.post(
    "/api/be1/v1/organizations/{organization_id}/video-quota/invoices/{invoice_id}/cancel",
    tags=["BE1 quota"],
)
def cancel_school_invoice(
    organization_id: str,
    invoice_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> Any:
    def execute() -> Any:
        require_assignment(db, principal, organization_id, roles={"school_admin"})
        commerce = _commerce(db, principal)
        invoice = commerce.invoice(invoice_id)
        if invoice.owner_kind != "ORGANIZATION" or invoice.owner_ref != organization_id:
            raise AdminError("INVOICE_NOT_FOUND", 404)
        return commerce.cancel_expired_vnpay_invoice(invoice_id)

    return _run(execute)


@router.post(
    "/api/be1/v1/organizations/{organization_id}/video-quota/checkout",
    tags=["BE1 quota"],
    status_code=201,
)
def school_checkout(
    organization_id: str,
    payload: QuotaCheckoutInput,
    request: Request,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=128),
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> Any:
    def execute() -> Any:
        require_assignment(db, principal, organization_id, roles={"school_admin"})
        return _commerce(db, principal).checkout(
            payload.product_id,
            "ORGANIZATION",
            organization_id,
            payload.provider,
            payload.payment_mode,
            idempotency_key,
            request.client.host if request.client else "127.0.0.1",
        )

    return _run(execute)


@router.get(
    "/api/be1/v1/organizations/{organization_id}/video-quota/allocations", tags=["BE1 quota"]
)
def school_allocations(
    organization_id: str,
    include_inactive: bool = False,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> Any:
    def execute() -> Any:
        require_assignment(db, principal, organization_id, roles={"school_admin"})
        return _commerce(db, principal).allocations(organization_id, include_inactive)

    return _run(execute)


@router.post(
    "/api/be1/v1/organizations/{organization_id}/video-quota/allocations",
    tags=["BE1 quota"],
    status_code=201,
)
def allocate_teacher_quota(
    organization_id: str,
    payload: QuotaAllocationInput,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=128),
    if_match: str | None = Header(default=None, alias="If-Match"),
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> Any:
    def execute() -> Any:
        require_assignment(db, principal, organization_id, roles={"school_admin"})
        expected = None
        if if_match is not None:
            try:
                expected = int(if_match.strip('"'))
            except ValueError:
                raise failure(422, "INVALID_REVISION", "If-Match must contain a revision") from None
            if expected < 1:
                raise failure(422, "INVALID_REVISION", "If-Match must contain a revision")
        return _commerce(db, principal).allocate(
            organization_id, payload.teacher_ref, payload.units, idempotency_key, expected
        )

    return _run(execute)


@router.post(
    "/api/be1/v1/organizations/{organization_id}/video-quota/allocations/reclaim",
    tags=["BE1 quota"],
)
def reclaim_teacher_quota(
    organization_id: str,
    payload: QuotaAllocationInput,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=128),
    if_match: str = Header(alias="If-Match"),
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> Any:
    def execute() -> Any:
        require_assignment(db, principal, organization_id, roles={"school_admin"})
        try:
            expected = int(if_match.strip('"'))
        except ValueError:
            raise failure(422, "INVALID_REVISION", "If-Match must contain a revision") from None
        if expected < 1:
            raise failure(422, "INVALID_REVISION", "If-Match must contain a revision")
        return _commerce(db, principal).reclaim(
            organization_id, payload.teacher_ref, payload.units, expected, idempotency_key
        )

    return _run(execute)


@router.get("/api/be1/v1/organizations/{organization_id}/video-quota/me", tags=["BE1 quota"])
def teacher_quota_allocation(
    organization_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> Any:
    def execute() -> Any:
        require_assignment(db, principal, organization_id, roles={"teacher"})
        result = _commerce(db, principal).allocations(organization_id)
        own = next(
            (item for item in result["items"] if item["teacher_ref"] == principal.subject), None
        )
        return {"allocation": own, "organization_quota_owner": "ORGANIZATION"}

    return _run(execute)
