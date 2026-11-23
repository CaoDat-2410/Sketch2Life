"""Billing-owned sandbox invoices and immutable video quota ledger."""

from datetime import datetime

from sqlalchemy import JSON, CheckConstraint, DateTime, Integer, String, UniqueConstraint, func
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
    owner_kind: Mapped[str] = mapped_column(String(24), nullable=False)
    units: Mapped[int] = mapped_column(Integer, nullable=False)
    amount_vnd: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BillingInvoiceModel(BillingBase):
    __tablename__ = "invoices"
    __table_args__ = (
        CheckConstraint("state IN ('PENDING','PAID','FAILED')", name="ck_billing_invoice_state"),
        {"schema": "billing"},
    )
    invoice_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    offer_id: Mapped[str] = mapped_column(String(36), nullable=False)
    owner_kind: Mapped[str] = mapped_column(String(24), nullable=False)
    owner_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    units: Mapped[int] = mapped_column(Integer, nullable=False)
    amount_vnd: Mapped[int] = mapped_column(Integer, nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING")
    provider: Mapped[str] = mapped_column(String(16), nullable=False, default="SANDBOX")
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BillingPaymentEventModel(BillingBase):
    __tablename__ = "payment_events"
    __table_args__ = ({"schema": "billing"},)
    event_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    invoice_id: Mapped[str] = mapped_column(String(36), nullable=False)
    amount_vnd: Mapped[int] = mapped_column(Integer, nullable=False)
    outcome: Mapped[str] = mapped_column(String(16), nullable=False)
    provider: Mapped[str] = mapped_column(String(16), nullable=False, default="SANDBOX")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class VideoQuotaGrantModel(BillingBase):
    __tablename__ = "video_quota_grants"
    __table_args__ = (
        CheckConstraint("units > 0", name="ck_quota_grant_units"),
        CheckConstraint("owner_kind IN ('ORGANIZATION','PARENT_ACCOUNT')", name="ck_quota_owner"),
        CheckConstraint("kind IN ('INCLUDED','TOP_UP')", name="ck_quota_kind"),
        UniqueConstraint("owner_kind", "owner_ref", "period", name="uq_quota_monthly_scope"),
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
