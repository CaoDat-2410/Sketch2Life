"""Parent profile, lesson feedback, quota and school-capacity rows for S13."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any
from typing import cast as typing_cast
from uuid import UUID

from sqlalchemy import Connection, Engine, String, and_, cast, func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from sketch2life.application.services.parent_consent_policies import (
    ParentConsentPolicyService,
)
from sketch2life.application.services.parent_profile_context import ParentProfileContextService
from sketch2life.domain.billing_capacity import quota_month
from sketch2life.domain.parent_profile_context import ContextEntryDraft
from sketch2life.domain.platform_admin import AdminError
from sketch2life.infrastructure.billing.quota_commerce import QuotaCommerceService
from sketch2life.infrastructure.lesson_library.feedback import ParentLessonFeedbackService
from sketch2life.infrastructure.lesson_library.feedback_tables import (
    FEEDBACK_MESSAGES,
    FEEDBACK_THREADS,
)
from sketch2life.infrastructure.lesson_library.service import LessonLibraryService
from sketch2life.infrastructure.persistence.be1_models import Be1CommandReceiptModel
from sketch2life.infrastructure.persistence.billing_models import (
    BillingInvoiceModel,
    BillingOfferModel,
    BillingPaymentAttemptModel,
    BillingPaymentEventModel,
    BillingProductAuditEventModel,
    BillingQuotaAllocationEventModel,
    BillingQuotaAllocationModel,
    BillingQuotaProductModel,
    BillingReceiptModel,
    CapacityPriceModel,
    SubscriptionEventModel,
    SubscriptionModel,
    VideoQuotaGrantModel,
    VideoQuotaUsageModel,
)
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.infrastructure.persistence.database import create_core_session_factory
from sketch2life.infrastructure.persistence.parent_consent_policy_repository import (
    SqlParentConsentPolicyRepository,
)
from sketch2life.infrastructure.persistence.parent_models import (
    ParentCommandReceiptModel,
    ParentConsentPolicyModel,
    ParentProfileContextEntryModel,
)
from sketch2life.infrastructure.persistence.parent_profile_repository import (
    SqlParentProfileContextRepository,
)
from sketch2life.infrastructure.persistence.platform_models import InboxItemModel
from sketch2life.infrastructure.platform_admin.sandbox_billing import SandboxBillingService
from sketch2life.infrastructure.platform_admin.sandbox_capacity import SandboxCapacityService
from sketch2life.infrastructure.platform_admin.service import PlatformAdminService
from sketch2life.infrastructure.profile_sharing.service import create_grant
from sketch2life.infrastructure.profile_sharing.tables import PROFILE_SHARE_GRANTS
from tools.seed import data, s13_system_demo_data
from tools.seed.stage_common import StageError, StageResult, run_stage_main, seed_principal

EXPECTED = s13_system_demo_data.EXPECTED
_SANDBOX_SETTINGS = SimpleNamespace(
    env="test",
    billing_sandbox_enabled=True,
    billing_real_payments_enabled=False,
    momo_payment_configured=False,
    vnpay_payment_configured=False,
    video_quota_included_units_parent=s13_system_demo_data.PARENT_QUOTA_UNITS,
    video_quota_included_units_organization=s13_system_demo_data.ORGANIZATION_QUOTA_UNITS,
)


class _UnusedLessonIO:
    """Feedback authorization reads lesson metadata; asset I/O is not used."""


def _count(connection: Connection, model: Any, predicate: Any) -> int:
    return int(
        connection.execute(select(func.count()).select_from(model).where(predicate)).scalar_one()
    )


def _parent_profile_id() -> UUID:
    return data.parent_profile_id(s13_system_demo_data.PARENT_PROFILE_KEY)


def _parent_account_id() -> str:
    return data.parent_account_id(s13_system_demo_data.PARENT_KEY)


def _product_predicate() -> Any:
    return or_(
        *(
            and_(
                BillingQuotaProductModel.owner_kind == product["owner_kind"],
                BillingQuotaProductModel.display_name == product["display_name"],
            )
            for product in s13_system_demo_data.QUOTA_PRODUCTS
        )
    )


def count_s13_rows(connection: Connection, now: datetime) -> dict[str, int]:
    period = quota_month(now)[0]
    profile_id = _parent_profile_id()
    account_id = _parent_account_id()
    organization_id = data.org_id("a")
    teacher_subject = data.ORG_A_TEACHERS[0]
    product_ids = select(BillingQuotaProductModel.product_id).where(_product_predicate())
    capacity_price_ids = select(CapacityPriceModel.price_id).where(
        CapacityPriceModel.created_by == data.PLATFORM_ADMIN_SUBJECT,
        CapacityPriceModel.cycle_months == s13_system_demo_data.CAPACITY_PRICE["cycle_months"],
        CapacityPriceModel.base_amount_vnd
        == s13_system_demo_data.CAPACITY_PRICE["base_amount_vnd"],
        CapacityPriceModel.slot_amount_vnd
        == s13_system_demo_data.CAPACITY_PRICE["slot_amount_vnd"],
    )
    subscription_ids = select(SubscriptionModel.subscription_id).where(
        SubscriptionModel.organization_ref == organization_id
    )
    policy_ids = select(ParentConsentPolicyModel.policy_id).where(
        ParentConsentPolicyModel.policy_version == s13_system_demo_data.CONSENT_POLICY_VERSION
    )
    share_ids = select(cast(PROFILE_SHARE_GRANTS.c.share_grant_id, String)).where(
        PROFILE_SHARE_GRANTS.c.parent_profile_id == profile_id
    )
    feedback_threads = FEEDBACK_THREADS.c
    feedback_messages = FEEDBACK_MESSAGES.c
    feedback_thread_ids = select(feedback_threads.thread_id).where(
        feedback_threads.lesson_id == s13_system_demo_data.PARENT_FEEDBACK_LESSON_ID,
        feedback_threads.created_by == s13_system_demo_data.PARENT_FEEDBACK_SUBJECT,
    )
    fixed_command_clauses = [
        and_(
            BillingReceiptModel.actor_ref == data.PLATFORM_ADMIN_SUBJECT,
            BillingReceiptModel.operation == operation,
            BillingReceiptModel.key == key,
        )
        for operation, key in s13_system_demo_data.BILLING_COMMAND_KEYS
    ]
    fixed_command_clauses.append(
        and_(
            BillingReceiptModel.actor_ref == data.PLATFORM_ADMIN_SUBJECT,
            BillingReceiptModel.operation.like("invoice.settle:%"),
            BillingReceiptModel.key == s13_system_demo_data.CAPACITY_SETTLE_KEY,
        )
    )
    audit_scope = or_(
        and_(
            CoreAuditEntryModel.action == "PARENT_CONSENT_POLICY_DRAFT_CREATED",
            CoreAuditEntryModel.resource_type == "parent_consent_policy",
            CoreAuditEntryModel.resource_id.in_(policy_ids),
        ),
        and_(
            CoreAuditEntryModel.action == "parent_share.grant.invite",
            CoreAuditEntryModel.resource_type == "profile_share_grant",
            CoreAuditEntryModel.resource_id.in_(share_ids),
        ),
        and_(
            CoreAuditEntryModel.action == "LESSON_FEEDBACK_CREATED",
            CoreAuditEntryModel.resource_type == "lesson_feedback",
            CoreAuditEntryModel.resource_id.in_(feedback_thread_ids),
        ),
    )
    return {
        "parent_consent_policies": _count(
            connection,
            ParentConsentPolicyModel,
            ParentConsentPolicyModel.policy_version
            == s13_system_demo_data.CONSENT_POLICY_VERSION,
        ),
        "parent_profile_context_entries": _count(
            connection,
            ParentProfileContextEntryModel,
            and_(
                ParentProfileContextEntryModel.parent_profile_id == profile_id,
                ParentProfileContextEntryModel.short_text
                == s13_system_demo_data.PARENT_CONTEXT_ENTRY_TEXT,
                ParentProfileContextEntryModel.source_kind
                == s13_system_demo_data.PARENT_CONTEXT_ENTRY_SOURCE_KIND,
            ),
        ),
        "parent_context_command_receipts": _count(
            connection,
            ParentCommandReceiptModel,
            and_(
                ParentCommandReceiptModel.principal_issuer == data.SEED_ISSUER,
                ParentCommandReceiptModel.principal_subject
                == data.PARENT_SUBJECTS[s13_system_demo_data.PARENT_KEY],
                ParentCommandReceiptModel.operation_scope == "create_context_entry",
                ParentCommandReceiptModel.resource_scope == str(profile_id),
            ),
        ),
        "parent_profile_share_grants": _count(
            connection,
            PROFILE_SHARE_GRANTS,
            PROFILE_SHARE_GRANTS.c.parent_profile_id == profile_id,
        ),
        "parent_share_command_receipts": _count(
            connection,
            Be1CommandReceiptModel,
            and_(
                Be1CommandReceiptModel.operation_scope == "POST /v1/parent/share-grants",
                Be1CommandReceiptModel.idempotency_key
                == s13_system_demo_data.PARENT_SHARE_IDEMPOTENCY_KEY,
            ),
        ),
        "lesson_feedback_threads_s13": _count(
            connection,
            FEEDBACK_THREADS,
            and_(
                feedback_threads.lesson_id
                == s13_system_demo_data.PARENT_FEEDBACK_LESSON_ID,
                feedback_threads.created_by == s13_system_demo_data.PARENT_FEEDBACK_SUBJECT,
            ),
        ),
        "lesson_feedback_messages_s13": _count(
            connection,
            FEEDBACK_MESSAGES,
            and_(
                feedback_messages.thread_id.in_(feedback_thread_ids),
                feedback_messages.actor_ref == s13_system_demo_data.PARENT_FEEDBACK_SUBJECT,
                feedback_messages.body == s13_system_demo_data.PARENT_FEEDBACK_TEXT,
            ),
        ),
        "lesson_feedback_receipts_s13": _count(
            connection,
            Be1CommandReceiptModel,
            and_(
                Be1CommandReceiptModel.principal_ref
                == s13_system_demo_data.PARENT_FEEDBACK_SUBJECT,
                Be1CommandReceiptModel.operation_scope
                == ParentLessonFeedbackService.operation_scope(
                    s13_system_demo_data.PARENT_FEEDBACK_LESSON_ID
                ),
                Be1CommandReceiptModel.idempotency_key
                == s13_system_demo_data.PARENT_FEEDBACK_IDEMPOTENCY_KEY,
            ),
        ),
        "notification_inbox_items_s13": _count(
            connection,
            InboxItemModel,
            and_(
                InboxItemModel.recipient_ref == data.ORG_A_TEACHERS[0],
                InboxItemModel.kind == "LESSON_FEEDBACK_CREATED",
                InboxItemModel.resource_ref.in_(feedback_thread_ids),
            ),
        ),
        "core_audit_entries_s13": _count(connection, CoreAuditEntryModel, audit_scope),
        "billing_video_quota_products": _count(
            connection, BillingQuotaProductModel, _product_predicate()
        ),
        "billing_offer_versions": _count(
            connection, BillingOfferModel, BillingOfferModel.product_id.in_(product_ids)
        ),
        "billing_video_quota_product_events": _count(
            connection,
            BillingProductAuditEventModel,
            BillingProductAuditEventModel.product_id.in_(product_ids),
        ),
        "billing_video_quota_grants_current_period": _count(
            connection,
            VideoQuotaGrantModel,
            and_(
                VideoQuotaGrantModel.kind == "INCLUDED",
                VideoQuotaGrantModel.period == period,
                or_(
                    and_(
                        VideoQuotaGrantModel.owner_kind == "PARENT_ACCOUNT",
                        VideoQuotaGrantModel.owner_ref == account_id,
                    ),
                    and_(
                        VideoQuotaGrantModel.owner_kind == "ORGANIZATION",
                        VideoQuotaGrantModel.owner_ref == organization_id,
                    ),
                ),
            ),
        ),
        "billing_video_quota_allocations": _count(
            connection,
            BillingQuotaAllocationModel,
            and_(
                BillingQuotaAllocationModel.organization_ref == organization_id,
                BillingQuotaAllocationModel.teacher_ref == teacher_subject,
            ),
        ),
        "billing_video_quota_allocation_events": _count(
            connection,
            BillingQuotaAllocationEventModel,
            and_(
                BillingQuotaAllocationEventModel.organization_ref == organization_id,
                BillingQuotaAllocationEventModel.teacher_ref == teacher_subject,
                BillingQuotaAllocationEventModel.operation_key
                == s13_system_demo_data.TEACHER_ALLOCATION_KEY,
            ),
        ),
        "billing_capacity_price_versions": _count(
            connection,
            CapacityPriceModel,
            and_(
                CapacityPriceModel.created_by == data.PLATFORM_ADMIN_SUBJECT,
                CapacityPriceModel.cycle_months
                == s13_system_demo_data.CAPACITY_PRICE["cycle_months"],
                CapacityPriceModel.base_amount_vnd
                == s13_system_demo_data.CAPACITY_PRICE["base_amount_vnd"],
                CapacityPriceModel.slot_amount_vnd
                == s13_system_demo_data.CAPACITY_PRICE["slot_amount_vnd"],
            ),
        ),
        "billing_invoices": _count(
            connection,
            BillingInvoiceModel,
            and_(
                BillingInvoiceModel.owner_kind == "ORGANIZATION",
                BillingInvoiceModel.owner_ref == organization_id,
                BillingInvoiceModel.offer_id.in_(capacity_price_ids),
                BillingInvoiceModel.provider == "SANDBOX",
                BillingInvoiceModel.state == "PAID",
            ),
        ),
        "billing_payment_events_sandbox": _count(
            connection,
            BillingPaymentEventModel,
            and_(
                BillingPaymentEventModel.event_id
                == s13_system_demo_data.CAPACITY_PAYMENT_EVENT_ID,
                BillingPaymentEventModel.provider == "SANDBOX",
            ),
        ),
        "billing_organization_subscriptions": _count(
            connection,
            SubscriptionModel,
            SubscriptionModel.organization_ref == organization_id,
        ),
        "billing_subscription_events": _count(
            connection,
            SubscriptionEventModel,
            SubscriptionEventModel.subscription_id.in_(subscription_ids),
        ),
        "billing_command_receipts_s13": _count(
            connection, BillingReceiptModel, or_(*fixed_command_clauses)
        ),
        "billing_payment_attempts": _count(
            connection,
            BillingPaymentAttemptModel,
            BillingPaymentAttemptModel.invoice_id.in_(
                select(BillingInvoiceModel.invoice_id).where(
                    or_(
                        BillingInvoiceModel.owner_ref == account_id,
                        BillingInvoiceModel.owner_ref == organization_id,
                    )
                )
            ),
        ),
        "billing_video_quota_usage": _count(
            connection,
            VideoQuotaUsageModel,
            and_(
                VideoQuotaUsageModel.owner_ref.in_((account_id, organization_id)),
                VideoQuotaUsageModel.owner_kind.in_(
                    ("PARENT_ACCOUNT", "ORGANIZATION")
                ),
            ),
        ),
    }


def _seed_consent_policy(session_factory: Callable[[], Session]) -> None:
    with session_factory() as session:
        version = s13_system_demo_data.CONSENT_POLICY_VERSION
        existing = session.scalar(
            select(ParentConsentPolicyModel).where(
                ParentConsentPolicyModel.policy_version == version
            )
        )
        if existing is not None:
            if (
                existing.state != "DRAFT"
                or existing.consent_text != s13_system_demo_data.CONSENT_POLICY_TEXT
            ):
                raise StageError("S13_CONSENT_POLICY_CONFLICT")
            return
        try:
            ParentConsentPolicyService(SqlParentConsentPolicyRepository(session)).create_draft(
                version=version,
                text=s13_system_demo_data.CONSENT_POLICY_TEXT,
                actor_subject=data.PLATFORM_ADMIN_SUBJECT,
            )
        except Exception:
            session.rollback()
            raise StageError("S13_CONSENT_POLICY_FAILED") from None


def _seed_parent_context(session_factory: Callable[[], Session]) -> None:
    principal = seed_principal(data.PARENT_SUBJECTS[s13_system_demo_data.PARENT_KEY])
    profile_id = _parent_profile_id()
    entry = ContextEntryDraft(
        entry_kind="OBSERVATION",
        short_text=s13_system_demo_data.PARENT_CONTEXT_ENTRY_TEXT,
        source_kind=s13_system_demo_data.PARENT_CONTEXT_ENTRY_SOURCE_KIND,
        source_ref=None,
        approximate_date=data.SEED_TIME.date(),
    )
    with session_factory() as session:
        try:
            result = ParentProfileContextService(
                SqlParentProfileContextRepository(session)
            ).create_context_entry(
                principal=principal,
                profile_id=profile_id,
                entry=entry,
                idempotency_key=s13_system_demo_data.PARENT_CONTEXT_ENTRY_IDEMPOTENCY_KEY,
                request_id=s13_system_demo_data.PARENT_CONTEXT_REQUEST_ID,
            )
        except Exception:
            session.rollback()
            raise StageError("S13_PARENT_CONTEXT_ENTRY_FAILED") from None
        if result.body.get("context_entry", {}).get("short_text") != entry.short_text:
            raise StageError("S13_PARENT_CONTEXT_ENTRY_UNEXPECTED")


def _seed_parent_share(session_factory: Callable[[], Session], now: datetime) -> None:
    principal = seed_principal(data.PARENT_SUBJECTS[s13_system_demo_data.PARENT_KEY])
    with session_factory() as session:
        try:
            body, _etag = create_grant(
                session,
                principal,
                profile_id=_parent_profile_id(),
                granted_fields=s13_system_demo_data.PARENT_SHARE_GRANTED_FIELDS,
                idempotency_key=s13_system_demo_data.PARENT_SHARE_IDEMPOTENCY_KEY,
                now=now,
            )
        except Exception:
            session.rollback()
            raise StageError("S13_PARENT_SHARE_INVITATION_FAILED") from None
        if body.get("state") != "INVITED":
            raise StageError("S13_PARENT_SHARE_INVITATION_UNEXPECTED")
        # The one-time invitation code is intentionally not written to a fixture or log.


def _seed_parent_lesson_feedback(session_factory: Callable[[], Session]) -> None:
    principal = seed_principal(s13_system_demo_data.PARENT_FEEDBACK_SUBJECT)
    with session_factory() as session:
        lesson_service = LessonLibraryService(
            session,
            storage=typing_cast(Any, _UnusedLessonIO()),
            parser=typing_cast(Any, _UnusedLessonIO()),
            scanner=typing_cast(Any, _UnusedLessonIO()),
        )
        service = ParentLessonFeedbackService(
            PlatformAdminService(session, principal),
            parent_lesson=lambda lesson_id: lesson_service.get_parent_lesson(
                parent_principal_ref=principal.subject,
                lesson_id=lesson_id,
            ),
        )
        try:
            result = service.submit(
                lesson_id=s13_system_demo_data.PARENT_FEEDBACK_LESSON_ID,
                feedback_text=s13_system_demo_data.PARENT_FEEDBACK_TEXT,
                idempotency_key=s13_system_demo_data.PARENT_FEEDBACK_IDEMPOTENCY_KEY,
            )
        except Exception:
            session.rollback()
            raise StageError("S13_PARENT_LESSON_FEEDBACK_FAILED") from None
        if result.get("feedback_text") != s13_system_demo_data.PARENT_FEEDBACK_TEXT:
            raise StageError("S13_PARENT_LESSON_FEEDBACK_UNEXPECTED")


def _seed_products_and_quota(session_factory: Callable[[], Session], now: datetime) -> None:
    with session_factory() as session:
        commerce = QuotaCommerceService(
            session,
            actor=data.PLATFORM_ADMIN_SUBJECT,
            settings=_SANDBOX_SETTINGS,
            clock=lambda: now,
        )
        try:
            for index, product in enumerate(s13_system_demo_data.QUOTA_PRODUCTS):
                commerce.save_product(
                    dict(product),
                    key=(
                        "seed:s13:quota-product-parent"
                        if index == 0
                        else "seed:s13:quota-product-organization"
                    ),
                )
            parent_grant = commerce.ensure_monthly_included_grant(
                ("PARENT_ACCOUNT", _parent_account_id()), quota_month(now)[0]
            )
            organization_grant = commerce.ensure_monthly_included_grant(
                ("ORGANIZATION", data.org_id("a")), quota_month(now)[0]
            )
            if (
                parent_grant.get("units") != s13_system_demo_data.PARENT_QUOTA_UNITS
                or organization_grant.get("units")
                != s13_system_demo_data.ORGANIZATION_QUOTA_UNITS
            ):
                raise StageError("S13_INCLUDED_QUOTA_UNEXPECTED")
            commerce.allocate(
                organization_ref=data.org_id("a"),
                teacher_ref=data.ORG_A_TEACHERS[0],
                units=s13_system_demo_data.TEACHER_QUOTA_UNITS,
                key=s13_system_demo_data.TEACHER_ALLOCATION_KEY,
            )
        except StageError:
            session.rollback()
            raise
        except Exception:
            session.rollback()
            raise StageError("S13_QUOTA_SETUP_FAILED") from None


def _seed_capacity(session_factory: Callable[[], Session], now: datetime) -> None:
    with session_factory() as session:
        billing = SandboxBillingService(
            session,
            actor=data.PLATFORM_ADMIN_SUBJECT,
            settings=_SANDBOX_SETTINGS,
            clock=lambda: now,
        )
        capacity = SandboxCapacityService(billing)
        try:
            price = capacity.price(
                dict(s13_system_demo_data.CAPACITY_PRICE),
                s13_system_demo_data.CAPACITY_PRICE_KEY,
            )
            quote = capacity.quote(
                {
                    "mode": "START",
                    "organization_ref": data.org_id("a"),
                    "price_id": price["price_id"],
                    "addon_slots": 0,
                },
                s13_system_demo_data.CAPACITY_QUOTE_KEY,
            )
            settled = billing.settle(
                quote["invoice_id"],
                {
                    "event_id": s13_system_demo_data.CAPACITY_PAYMENT_EVENT_ID,
                    "paid": True,
                    "amount_vnd": quote["amount_vnd"],
                },
                expected=1,
                key=s13_system_demo_data.CAPACITY_SETTLE_KEY,
            )
        except (AdminError, SQLAlchemyError, ValueError, TypeError):
            session.rollback()
            raise StageError("S13_SANDBOX_CAPACITY_SETUP_FAILED") from None
        if settled.get("state") != "PAID" or settled.get("provider") != "SANDBOX":
            raise StageError("S13_SANDBOX_CAPACITY_SETUP_UNEXPECTED")


def run_s13(engine: Engine) -> StageResult:
    """Seed product-backed Parent and capacity data without a real payment provider."""

    now = datetime.now(UTC)
    try:
        with engine.connect() as connection:
            before = count_s13_rows(connection, now)
        session_factory = create_core_session_factory(engine)
        _seed_consent_policy(session_factory)
        _seed_parent_context(session_factory)
        _seed_parent_share(session_factory, now)
        _seed_parent_lesson_feedback(session_factory)
        _seed_products_and_quota(session_factory, now)
        _seed_capacity(session_factory, now)
        with engine.connect() as connection:
            after = count_s13_rows(connection, now)
        return StageResult("s13_system_demo", before, after, EXPECTED)
    except StageError:
        raise
    except SQLAlchemyError:
        raise StageError("S13_DATABASE_ERROR") from None


def main() -> int:
    return run_stage_main(run_s13, stage="s13")


if __name__ == "__main__":
    raise SystemExit(main())
