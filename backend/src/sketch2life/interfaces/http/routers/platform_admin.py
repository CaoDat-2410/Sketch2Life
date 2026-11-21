"""Admin metadata endpoints; no child profile or media access is provided."""
# FastAPI dependency defaults are intentional.
# ruff: noqa: B008

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.contracts.schemas.platform_admin import (
    AuditPurgeInput,
    AuditRetentionInput,
    BillingInvoiceInput,
    BillingOfferInput,
    CapacityPriceInput,
    CapacityQuoteInput,
    CatalogAction,
    CatalogWrite,
    FeedbackInput,
    IncludedQuotaInput,
    OrganizationInput,
    OrganizationUpdateInput,
    PermissionInput,
    PlatformLessonWrite,
    PreferenceInput,
    PublicationAction,
    SandboxConsumeInput,
    SandboxPaymentInput,
    SubscriptionConfigInput,
)
from sketch2life.domain.platform_admin import AdminError
from sketch2life.infrastructure.config.settings import get_settings
from sketch2life.infrastructure.learning_content.admin_catalog import AdminCatalogService
from sketch2life.infrastructure.lesson_library.feedback import LessonFeedbackService
from sketch2life.infrastructure.lesson_library.platform_publication import PlatformLessonService
from sketch2life.infrastructure.persistence.be1_models import ClassroomModel
from sketch2life.infrastructure.platform_admin.operations import OperationsReader
from sketch2life.infrastructure.platform_admin.pagination import (
    apply_reference_cursor,
    cursor_scope,
    next_reference_cursor,
)
from sketch2life.infrastructure.platform_admin.sandbox_billing import SandboxBillingService
from sketch2life.infrastructure.platform_admin.sandbox_capacity import SandboxCapacityService
from sketch2life.infrastructure.platform_admin.service import PlatformAdminService
from sketch2life.interfaces.http.admin_route import AdminRoute
from sketch2life.interfaces.http.api_conventions import parse_idempotency_key
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult

router = APIRouter(prefix="/api/platform-admin/v1", tags=["Platform Admin"], route_class=AdminRoute)


def idempotency_key(
    request: Request,
    idempotency_key_header: Annotated[
        str | None,
        Header(
            alias="Idempotency-Key", description="Required; 1–128 printable characters."
        ),
    ] = None,
) -> str:
    """Same Idempotency-Key rule as every FEAT-066 command (400 INVALID_REQUEST, 1-128 chars)."""
    return parse_idempotency_key(request)


Key = Annotated[str, Depends(idempotency_key)]


def service(
    db: Session = Depends(get_db), principal: VerifiedPrincipal = Depends(get_verified_adult)
):
    return PlatformAdminService(db, principal)


def revision(value: Annotated[str | None, Header(alias="If-Match")] = None):
    if value is None:
        raise HTTPException(428, detail={"code": "PRECONDITION_REQUIRED"})
    if (
        len(value) > 22
        or not value.startswith('"')
        or not value.endswith('"')
        or not value[1:-1].isascii()
        or not value[1:-1].isdigit()
        or int(value[1:-1]) < 1
    ):
        raise HTTPException(422, detail={"code": "INVALID_REVISION"})
    return int(value[1:-1])


def run(operation):
    try:
        return operation()
    except AdminError as exc:
        raise HTTPException(exc.status, detail={"code": exc.code, "message": exc.code}) from None


@router.get("/organizations")
def organizations(
    search: str | None = Query(None, max_length=120),
    state: str | None = Query(None, pattern="^(active|paused|disabled)$"),
    limit: int = Query(25, ge=1, le=100),
    cursor: str | None = Query(None, max_length=768),
    svc=Depends(service),
):
    return run(lambda: svc.list_organizations(search, state, limit, cursor))


@router.post("/organizations", status_code=201)
def create_organization(payload: OrganizationInput, key: Key, svc=Depends(service)):
    return run(lambda: svc.create_organization(payload.display_name, key))


@router.get("/organizations/summary")
def organization_summary(svc=Depends(service)):
    return run(svc.organization_summary)


@router.get("/organizations/{organization_id}")
def organization(organization_id: str, svc=Depends(service)):
    return run(lambda: svc.organization(organization_id))


@router.patch("/organizations/{organization_id}")
def update_organization(
    organization_id: str,
    payload: OrganizationUpdateInput,
    key: Key,
    expected: int = Depends(revision),
    svc=Depends(service),
):
    return run(
        lambda: svc.update_organization(
            organization_id, payload.model_dump(exclude_unset=True), expected, key
        )
    )


@router.get("/accounts/{account_id}/permissions")
def permissions(account_id: str, svc=Depends(service)):
    return run(lambda: svc.permissions(account_id))


@router.put("/accounts/{account_id}/permissions/content-admin")
def set_permission(account_id: str, payload: PermissionInput, key: Key, svc=Depends(service)):
    return run(lambda: svc.set_permission(account_id, payload.model_dump(), key))


@router.post("/accounts/{account_id}/setup-email", status_code=202)
def setup_email(account_id: str, key: Key, svc=Depends(service)):
    return run(lambda: svc.request_account_email(account_id, key))


@router.get("/audit")
def audit(
    action: str | None = Query(None, max_length=128),
    organization_id: str | None = Query(None, max_length=128),
    limit: int = Query(25, ge=1, le=100),
    cursor: str | None = Query(None, max_length=768),
    svc=Depends(service),
):
    return run(lambda: svc.audit_feed(action, organization_id, limit, cursor))


@router.get("/audit/retention")
def audit_retention(svc=Depends(service)):
    return run(svc.audit_retention)


@router.put("/audit/retention")
def update_audit_retention(
    payload: AuditRetentionInput,
    key: Key,
    expected: int = Depends(revision),
    svc=Depends(service),
):
    return run(lambda: svc.update_audit_retention(payload.retention_days, expected, key))


@router.get("/audit/retention/preview")
def audit_retention_preview(svc=Depends(service)):
    return run(svc.audit_retention_preview)


@router.post("/audit/retention/purge")
def purge_audit(
    payload: AuditPurgeInput,
    key: Key,
    expected: int = Depends(revision),
    svc=Depends(service),
):
    return run(
        lambda: svc.purge_audit(payload.cutoff, payload.expected_count, expected, key)
    )


@router.get("/inbox")
def inbox(
    limit: int = Query(25, ge=1, le=100),
    cursor: str | None = Query(None, max_length=768),
    svc=Depends(service),
):
    return run(lambda: svc.inbox(limit, cursor))


@router.post("/inbox/{item_id}/read")
def mark_read(item_id: str, key: Key, svc=Depends(service)):
    return run(lambda: svc.mark_read(item_id, key))


@router.get("/preferences")
def preferences(svc=Depends(service)):
    return run(svc.preferences)


@router.put("/preferences")
def update_preferences(payload: PreferenceInput, key: Key, svc=Depends(service)):
    return run(lambda: svc.update_preferences(payload.model_dump(), key))


@router.get("/lessons")
def platform_lessons(
    state: str | None = Query(None, pattern="^(DRAFT|PENDING_REVIEW|CHANGES_REQUESTED|APPROVED)$"),
    limit: int = Query(25, ge=1, le=100),
    cursor: str | None = Query(None, max_length=768),
    svc=Depends(service),
):
    return run(lambda: PlatformLessonService(svc).list(state, limit, cursor))


@router.get("/lessons/{lesson_id}")
def platform_lesson(lesson_id: str, svc=Depends(service)):
    return run(lambda: PlatformLessonService(svc).detail(lesson_id))


@router.post("/lessons", status_code=201)
def create_platform_lesson(payload: PlatformLessonWrite, key: Key, svc=Depends(service)):
    return run(
        lambda: PlatformLessonService(svc).write(payload.content.model_dump(mode="json"), key)
    )


@router.patch("/lessons/{lesson_id}")
def revise_platform_lesson(
    lesson_id: str,
    payload: PlatformLessonWrite,
    key: Key,
    expected: int = Depends(revision),
    svc=Depends(service),
):
    return run(
        lambda: PlatformLessonService(svc).write(
            payload.content.model_dump(mode="json"), key, lesson_id, expected
        )
    )


@router.post("/lessons/{lesson_id}/actions")
def platform_lesson_action(
    lesson_id: str,
    payload: PublicationAction,
    key: Key,
    expected: int = Depends(revision),
    svc=Depends(service),
):
    return run(
        lambda: PlatformLessonService(svc).action(lesson_id, payload.model_dump(), expected, key)
    )


@router.get("/catalog")
def catalog(
    state: str | None = Query(
        None, pattern="^(draft|submitted|changes_requested|published|recalled|archived)$"
    ),
    limit: int = Query(25, ge=1, le=100),
    cursor: str | None = Query(None, max_length=768),
    svc=Depends(service),
):
    return run(lambda: AdminCatalogService(svc).list(state, limit, cursor))


@router.get("/catalog/{record_id}")
def catalog_detail(record_id: str, svc=Depends(service)):
    return run(lambda: AdminCatalogService(svc).detail(record_id))


@router.post("/catalog", status_code=201)
def create_catalog(payload: CatalogWrite, key: Key, svc=Depends(service)):
    return run(lambda: AdminCatalogService(svc).write(payload.model_dump(mode="json"), key))


@router.patch("/catalog/{record_id}")
def revise_catalog(
    record_id: str,
    payload: CatalogWrite,
    key: Key,
    expected: int = Depends(revision),
    svc=Depends(service),
):
    return run(
        lambda: AdminCatalogService(svc).write(
            payload.model_dump(mode="json"), key, record_id, expected
        )
    )


@router.post("/catalog/{record_id}/actions")
def catalog_action(
    record_id: str,
    payload: CatalogAction,
    key: Key,
    expected: int = Depends(revision),
    svc=Depends(service),
):
    return run(
        lambda: AdminCatalogService(svc).action(record_id, payload.model_dump(), expected, key)
    )


def billing(svc):
    svc.identity()
    return SandboxBillingService(svc.db, svc.principal.subject, get_settings())


@router.get("/billing/sandbox/offers")
def billing_offers(
    limit: int = Query(25, ge=1, le=100),
    cursor: str | None = Query(None, max_length=768),
    svc=Depends(service),
):
    return run(lambda: billing(svc).offers(limit, cursor))


@router.post("/billing/sandbox/offers", status_code=201)
def create_billing_offer(payload: BillingOfferInput, key: Key, svc=Depends(service)):
    return run(lambda: billing(svc).create_offer(payload.model_dump(), key))


@router.get("/billing/sandbox/invoices")
def invoices(
    state: str | None = Query(None, pattern="^(PENDING|PAID|FAILED)$"),
    limit: int = Query(25, ge=1, le=100),
    cursor: str | None = Query(None, max_length=768),
    svc=Depends(service),
):
    return run(lambda: billing(svc).invoices(state, limit, cursor))


@router.post("/billing/sandbox/invoices", status_code=201)
def create_invoice(payload: BillingInvoiceInput, key: Key, svc=Depends(service)):
    def execute():
        svc.require_billing_scope(payload.owner_kind, payload.owner_ref)
        return billing(svc).create_invoice(payload.model_dump(), key)

    return run(execute)


@router.post("/billing/sandbox/invoices/{invoice_id}/settle")
def settle_invoice(
    invoice_id: str,
    payload: SandboxPaymentInput,
    key: Key,
    expected: int = Depends(revision),
    svc=Depends(service),
):
    return run(lambda: billing(svc).settle(invoice_id, payload.model_dump(), expected, key))


@router.post("/billing/sandbox/included-grants", status_code=201)
def included_grant(payload: IncludedQuotaInput, key: Key, svc=Depends(service)):
    def execute():
        svc.require_billing_scope(payload.owner_kind, payload.owner_ref)
        return billing(svc).included(payload.model_dump(), key)

    return run(execute)


@router.get("/billing/sandbox/quota")
def quota(
    owner_kind: str = Query(pattern="^(ORGANIZATION|PARENT_ACCOUNT)$"),
    owner_ref: str = Query(min_length=1, max_length=128),
    svc=Depends(service),
):
    def execute():
        svc.require_billing_scope(owner_kind, owner_ref)
        return billing(svc).summary(owner_kind, owner_ref)

    return run(execute)


@router.post("/billing/sandbox/consume")
def consume_quota(payload: SandboxConsumeInput, key: Key, svc=Depends(service)):
    def execute():
        svc.require_billing_scope(payload.owner_kind, payload.owner_ref)
        return billing(svc).consume(payload.model_dump(), key)

    return run(execute)


@router.get("/session")
def admin_session(svc=Depends(service)):
    def execute():
        account = svc.identity()
        return {
            "account_id": account.account_id,
            "role": account.account_role,
            "role_revision": account.role_revision,
            **svc.permissions(account.account_id),
        }

    return run(execute)


@router.get("/operations")
def operations(svc=Depends(service)):
    def execute():
        svc.identity()
        return OperationsReader(svc.db, get_settings()).summary()

    return run(execute)


@router.get("/lifecycle")
def lifecycle(
    state: str | None = Query(
        None, pattern="^(requested|running|awaiting_external_purge|completed|exception)$"
    ),
    organization_id: str | None = Query(None, max_length=128),
    limit: int = Query(25, ge=1, le=100),
    cursor: str | None = Query(None, max_length=768),
    svc=Depends(service),
):
    def execute():
        svc.identity()
        return OperationsReader(svc.db).lifecycle(state, organization_id, limit, cursor)

    return run(execute)


@router.get("/email-deliveries")
def email_deliveries(
    state: str | None = Query(None, pattern="^(pending|sending|sent|failed)$"),
    limit: int = Query(25, ge=1, le=100),
    cursor: str | None = Query(None, max_length=768),
    svc=Depends(service),
):
    def execute():
        svc.identity()
        return OperationsReader(svc.db).email_deliveries(state, limit, cursor)

    return run(execute)


@router.get("/settings")
def runtime_settings(svc=Depends(service)):
    def execute():
        svc.identity()
        settings = get_settings()
        return {
            "environment": settings.env,
            "real_payments_enabled": False,
            "billing_sandbox_enabled": settings.env in {"local", "test"}
            and settings.billing_sandbox_enabled,
            "smtp_configured": bool(settings.smtp_host),
            "preferences": svc.preferences(),
        }

    return run(execute)


@router.get("/organizations/{organization_id}/feedback")
def organization_feedback(
    organization_id: str,
    limit: int = Query(25, ge=1, le=100),
    cursor: str | None = Query(None, max_length=768),
    svc=Depends(service),
):
    def execute():
        svc.identity()
        return LessonFeedbackService(svc).list(organization_id, limit, cursor)

    return run(execute)


@router.get("/organizations/{organization_id}/feedback/{thread_id}")
def feedback_detail(
    organization_id: str,
    thread_id: str,
    limit: int = Query(25, ge=1, le=100),
    cursor: str | None = Query(None, max_length=768),
    svc=Depends(service),
):
    def execute():
        svc.identity()
        return LessonFeedbackService(svc).detail(organization_id, thread_id, limit, cursor)

    return run(execute)


@router.post("/organizations/{organization_id}/feedback/{thread_id}/replies")
def feedback_reply(
    organization_id: str,
    thread_id: str,
    payload: FeedbackInput,
    key: Key,
    expected: int = Depends(revision),
    svc=Depends(service),
):
    def execute():
        svc.identity()
        return LessonFeedbackService(svc).reply(
            organization_id, thread_id, payload.body, expected, key
        )

    return run(execute)


@router.post("/billing/sandbox/capacity-prices", status_code=201)
def capacity_price(payload: CapacityPriceInput, key: Key, svc=Depends(service)):
    return run(lambda: SandboxCapacityService(billing(svc)).price(payload.model_dump(), key))


@router.get("/billing/sandbox/subscriptions")
def subscriptions(
    limit: int = Query(25, ge=1, le=100),
    cursor: str | None = Query(None, max_length=768),
    svc=Depends(service),
):
    return run(lambda: SandboxCapacityService(billing(svc)).list(limit, cursor))


@router.post("/billing/sandbox/subscriptions/quote", status_code=201)
def subscription_quote(payload: CapacityQuoteInput, key: Key, svc=Depends(service)):
    def execute():
        svc.require_billing_scope("ORGANIZATION", payload.organization_ref or "")
        return SandboxCapacityService(billing(svc)).quote(payload.model_dump(), key)

    return run(execute)


@router.post("/billing/sandbox/subscriptions/{subscription_id}/quote", status_code=201)
def capacity_quote(
    subscription_id: str,
    payload: CapacityQuoteInput,
    key: Key,
    expected: int = Depends(revision),
    svc=Depends(service),
):
    return run(
        lambda: SandboxCapacityService(billing(svc)).quote(
            payload.model_dump(), key, subscription_id, expected
        )
    )


@router.patch("/billing/sandbox/subscriptions/{subscription_id}")
def configure_subscription(
    subscription_id: str,
    payload: SubscriptionConfigInput,
    key: Key,
    expected: int = Depends(revision),
    svc=Depends(service),
):
    def execute():
        capacity = SandboxCapacityService(billing(svc))
        row = capacity.load(subscription_id)
        classes = set(
            svc.db.scalars(
                select(ClassroomModel.class_id).where(
                    ClassroomModel.organization_id == row.organization_ref,
                    ClassroomModel.state == "active",
                )
            )
        )
        return capacity.configure(subscription_id, payload.model_dump(), expected, key, classes)

    return run(execute)


@router.get("/billing/sandbox/capacity-prices")
def capacity_prices(
    limit: int = Query(25, ge=1, le=100),
    cursor: str | None = Query(None, max_length=768),
    svc=Depends(service),
):
    return run(lambda: SandboxCapacityService(billing(svc)).prices(limit, cursor))


@router.get("/organizations/{organization_id}/capacity-classes")
def capacity_classes(
    organization_id: str,
    limit: int = Query(25, ge=1, le=100),
    cursor: str | None = Query(None, max_length=768),
    svc=Depends(service),
):
    def execute():
        svc.organization(organization_id)
        query = select(ClassroomModel).where(
            ClassroomModel.organization_id == organization_id,
            ClassroomModel.state == "active",
        )
        total = (
            svc.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        )
        scope = cursor_scope("capacity-classes", organization_id)
        query = apply_reference_cursor(
            query,
            reference_column=ClassroomModel.class_id,
            scope=scope,
            cursor=cursor,
        )
        rows = list(
            svc.db.scalars(
                query
                .order_by(ClassroomModel.class_id)
                .limit(limit + 1)
            )
        )
        next_cursor = next_reference_cursor(
            rows,
            limit,
            scope=scope,
            reference=lambda row: row.class_id,
        )
        return {
            "total": total,
            "limit": limit,
            "next_cursor": next_cursor,
            "items": [
                {"class_id": r.class_id, "display_name": r.display_name}
                for r in rows[:limit]
            ],
        }

    return run(execute)
