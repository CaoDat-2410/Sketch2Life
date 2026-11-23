"""Billing-owned sandbox invoices and immutable video quota ledger."""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class BillingBase(DeclarativeBase):
    pass


class BillingOfferModel(BillingBase):
    __tablename__ = "offer_versions"
    __table_args__ = (
        CheckConstraint("units > 0 AND amount_vnd > 0", name="ck_billing_offer_values"),
        {"schema": "billing"},
    )
    offer_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    product_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    display_name: Mapped[str] = mapped_column(
        String(120), nullable=False, default="Gói hạn mức cũ", server_default="Gói hạn mức cũ"
    )
    offer_kind: Mapped[str] = mapped_column(
        String(16), nullable=False, default="TOP_UP", server_default="TOP_UP"
    )
    cycle_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    owner_kind: Mapped[str] = mapped_column(String(24), nullable=False)
    units: Mapped[int] = mapped_column(Integer, nullable=False)
    amount_vnd: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BillingQuotaProductModel(BillingBase):
    __tablename__ = "video_quota_products"
    __table_args__ = (
        CheckConstraint("owner_kind IN ('ORGANIZATION','PARENT_ACCOUNT')", name="ck_quota_product_owner"),
        CheckConstraint("offer_kind IN ('MONTHLY','TOP_UP')", name="ck_quota_product_kind"),
        CheckConstraint(
            "(offer_kind = 'TOP_UP' AND cycle_months IS NULL) OR "
            "(offer_kind = 'MONTHLY' AND cycle_months > 0)",
            name="ck_quota_product_cycle",
        ),
        CheckConstraint("revision > 0", name="ck_quota_product_revision"),
        {"schema": "billing"},
    )
    product_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_kind: Mapped[str] = mapped_column(String(24), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    offer_kind: Mapped[str] = mapped_column(String(16), nullable=False)
    cycle_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_offer_id: Mapped[str] = mapped_column(String(36), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_by: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BillingProductAuditEventModel(BillingBase):
    __tablename__ = "video_quota_product_events"
    __table_args__ = ({"schema": "billing"},)
    event_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    product_id: Mapped[str] = mapped_column(String(36), nullable=False)
    offer_id: Mapped[str] = mapped_column(String(36), nullable=False)
    actor_ref: Mapped[str] = mapped_column(String(256), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    snapshot: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BillingInvoiceModel(BillingBase):
    __tablename__ = "invoices"
    __table_args__ = (
        CheckConstraint("state IN ('PENDING','PAID','FAILED','CANCELED')", name="ck_billing_invoice_state"),
        {"schema": "billing"},
    )
    invoice_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    offer_id: Mapped[str] = mapped_column(String(36), nullable=False)
    product_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    owner_kind: Mapped[str] = mapped_column(String(24), nullable=False)
    owner_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    units: Mapped[int] = mapped_column(Integer, nullable=False)
    amount_vnd: Mapped[int] = mapped_column(Integer, nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING")
    provider: Mapped[str] = mapped_column(String(16), nullable=False, default="SANDBOX")
    payment_mode: Mapped[str] = mapped_column(
        String(16), nullable=False, default="MANUAL", server_default="MANUAL"
    )
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BillingPaymentEventModel(BillingBase):
    __tablename__ = "payment_events"
    __table_args__ = (
        UniqueConstraint("provider", "provider_transaction_ref", name="uq_payment_provider_transaction"),
        {"schema": "billing"},
    )
    event_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    invoice_id: Mapped[str] = mapped_column(String(36), nullable=False)
    amount_vnd: Mapped[int] = mapped_column(Integer, nullable=False)
    outcome: Mapped[str] = mapped_column(String(16), nullable=False)
    provider: Mapped[str] = mapped_column(String(16), nullable=False, default="SANDBOX")
    provider_transaction_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    payload_digest: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BillingPaymentAttemptModel(BillingBase):
    __tablename__ = "payment_attempts"
    __table_args__ = (
        CheckConstraint(
            "provider IN ('MOMO','VNPAY') AND state IN ('REQUESTING','OPEN','UNKNOWN','FAILED','PAID','CANCELED')",
            name="ck_billing_payment_attempt_state",
        ),
        UniqueConstraint("provider", "provider_order_ref", name="uq_billing_provider_order"),
        {"schema": "billing"},
    )
    attempt_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    invoice_id: Mapped[str] = mapped_column(String(36), nullable=False)
    provider: Mapped[str] = mapped_column(String(16), nullable=False)
    provider_order_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    provider_request_ref: Mapped[str | None] = mapped_column(String(64), nullable=True)
    provider_transaction_date: Mapped[str | None] = mapped_column(String(14), nullable=True)
    provider_order_info: Mapped[str | None] = mapped_column(String(255), nullable=True)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="REQUESTING")
    checkout_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class VideoQuotaGrantModel(BillingBase):
    __tablename__ = "video_quota_grants"
    __table_args__ = (
        CheckConstraint("units > 0", name="ck_quota_grant_units"),
        CheckConstraint("owner_kind IN ('ORGANIZATION','PARENT_ACCOUNT')", name="ck_quota_owner"),
        CheckConstraint("kind IN ('INCLUDED','MONTHLY','TOP_UP')", name="ck_quota_kind"),
        Index(
            "uq_quota_monthly_scope",
            "owner_kind",
            "owner_ref",
            "period",
            unique=True,
            postgresql_where=text("kind = 'INCLUDED' AND period IS NOT NULL"),
            sqlite_where=text("kind = 'INCLUDED' AND period IS NOT NULL"),
        ),
        {"schema": "billing"},
    )
    grant_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_kind: Mapped[str] = mapped_column(String(24), nullable=False)
    owner_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    units: Mapped[int] = mapped_column(Integer, nullable=False)
    invoice_id: Mapped[str | None] = mapped_column(String(36), unique=True)
    period: Mapped[str | None] = mapped_column(String(7))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BillingQuotaAllocationModel(BillingBase):
    __tablename__ = "video_quota_allocations"
    __table_args__ = (
        UniqueConstraint("organization_ref", "teacher_ref", name="uq_quota_allocation_teacher"),
        CheckConstraint("revision > 0", name="ck_quota_allocation_revision"),
        {"schema": "billing"},
    )
    allocation_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    organization_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    teacher_ref: Mapped[str] = mapped_column(String(256), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BillingQuotaAllocationEventModel(BillingBase):
    __tablename__ = "video_quota_allocation_events"
    __table_args__ = (
        CheckConstraint("units > 0", name="ck_quota_allocation_event_units"),
        CheckConstraint(
            "event_kind IN ('ALLOCATED','RECLAIMED','RETURNED','CONSUMED')",
            name="ck_quota_allocation_event_kind",
        ),
        UniqueConstraint("allocation_id", "operation_key", name="uq_quota_allocation_operation"),
        {"schema": "billing"},
    )
    event_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    allocation_id: Mapped[str] = mapped_column(String(36), nullable=False)
    organization_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    teacher_ref: Mapped[str] = mapped_column(String(256), nullable=False)
    event_kind: Mapped[str] = mapped_column(String(16), nullable=False)
    units: Mapped[int] = mapped_column(Integer, nullable=False)
    actor_ref: Mapped[str] = mapped_column(String(256), nullable=False)
    operation_key: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class VideoQuotaUsageModel(BillingBase):
    __tablename__ = "video_quota_usage"
    __table_args__ = (
        UniqueConstraint(
            "owner_kind", "owner_ref", "admission_ref", name="uq_quota_admission_scope"
        ),
        {"schema": "billing"},
    )
    usage_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    grant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    owner_kind: Mapped[str] = mapped_column(String(24), nullable=False)
    owner_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    admission_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    allocation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    teacher_ref: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BillingReceiptModel(BillingBase):
    __tablename__ = "command_receipts"
    __table_args__ = ({"schema": "billing"},)
    actor_ref: Mapped[str] = mapped_column(String(256), primary_key=True)
    operation: Mapped[str] = mapped_column(String(100), primary_key=True)
    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    response_json: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CapacityPriceModel(BillingBase):
    __tablename__ = "capacity_price_versions"
    __table_args__ = (
        CheckConstraint(
            "cycle_months IN (1,12) AND base_amount_vnd > 0 AND slot_amount_vnd > 0",
            name="ck_capacity_price",
        ),
        {"schema": "billing"},
    )
    price_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    cycle_months: Mapped[int] = mapped_column(Integer, nullable=False)
    base_amount_vnd: Mapped[int] = mapped_column(Integer, nullable=False)
    slot_amount_vnd: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SubscriptionModel(BillingBase):
    __tablename__ = "organization_subscriptions"
    __table_args__ = (
        CheckConstraint("addon_slots >= 0 AND revision > 0", name="ck_subscription_values"),
        {"schema": "billing"},
    )
    subscription_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    organization_ref: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    price_id: Mapped[str] = mapped_column(String(36), nullable=False)
    addon_slots: Mapped[int] = mapped_column(Integer, nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)


class SubscriptionEventModel(BillingBase):
    __tablename__ = "subscription_events"
    __table_args__ = ({"schema": "billing"},)
    event_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    subscription_id: Mapped[str] = mapped_column(String(36), nullable=False)
    invoice_id: Mapped[str | None] = mapped_column(String(36))
    group_ref: Mapped[str | None] = mapped_column(String(36))
    class_ref: Mapped[str | None] = mapped_column(String(128))
    kind: Mapped[str] = mapped_column(String(48), nullable=False)
    payload: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=False
    )
    actor_ref: Mapped[str] = mapped_column(String(256), nullable=False)
    effective_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
