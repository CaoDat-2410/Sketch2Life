"""Strict, bounded commands for the platform administration API."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sketch2life.contracts.schemas.lesson_library import LessonActivityInputV1, LessonContentInputV1


class AdminInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class OrganizationInput(AdminInput):
    display_name: str = Field(min_length=1, max_length=200)


class OrganizationUpdateInput(AdminInput):
    display_name: str | None = Field(None, min_length=1, max_length=200)
    state: Literal["active", "paused", "disabled"] | None = None

    @model_validator(mode="after")
    def require_a_change(self):
        if self.display_name is None and self.state is None:
            raise ValueError("At least one organization field must be provided")
        return self


class AuditRetentionInput(AdminInput):
    retention_days: int | None = Field(..., ge=1, le=36500)


class AuditPurgeInput(AdminInput):
    cutoff: datetime
    expected_count: int = Field(ge=1, le=500)

    @model_validator(mode="after")
    def require_timezone(self):
        if self.cutoff.tzinfo is None or self.cutoff.utcoffset() is None:
            raise ValueError("cutoff must include a timezone")
        return self


class PermissionInput(AdminInput):
    active: bool
    expected_revision: int = Field(ge=0)
    reason: str = Field(min_length=1, max_length=500)


class PreferenceInput(AdminInput):
    locale: Literal["vi-VN", "en-US"] = "vi-VN"
    email_notifications: bool
    expected_revision: int = Field(ge=0)


class PasswordRecoveryInput(AdminInput):
    email: str = Field(min_length=3, max_length=254, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class PlatformLessonWrite(AdminInput):
    content: LessonContentInputV1


class PublicationAction(AdminInput):
    action: Literal["submit", "approve", "request_changes", "publish", "hide", "unpublish"]
    version_id: str = Field(min_length=1, max_length=36)
    content_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    review_id: str | None = Field(None, max_length=36)
    reason: str | None = Field(None, min_length=1, max_length=1000)


class CatalogWrite(AdminInput):
    activity: LessonActivityInputV1
    age_band: Literal["36-71", "72-107", "108-120"]
    age_band_version: int = Field(ge=1)
    provenance: Literal["HUMAN_AUTHORED"] = "HUMAN_AUTHORED"


class CatalogAction(AdminInput):
    action: Literal["submit", "review", "publish", "hide", "archive"]
    version: int = Field(ge=1)
    content_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    dimension: Literal["safety", "pedagogical"] | None = None
    decision: Literal["approve", "request_changes"] | None = None
    reason: str | None = Field(None, min_length=1, max_length=200)


class BillingOfferInput(AdminInput):
    owner_kind: Literal["ORGANIZATION", "PARENT_ACCOUNT"]
    units: int = Field(ge=1, le=100000)
    amount_vnd: int = Field(ge=1, le=2000000000)


class BillingScopeInput(AdminInput):
    owner_kind: Literal["ORGANIZATION", "PARENT_ACCOUNT"]
    owner_ref: str = Field(min_length=1, max_length=128)


class BillingInvoiceInput(BillingScopeInput):
    offer_id: str = Field(min_length=1, max_length=36)


class SandboxPaymentInput(AdminInput):
    event_id: str = Field(min_length=1, max_length=128)
    paid: bool
    amount_vnd: int = Field(ge=1, le=2000000000)


class IncludedQuotaInput(BillingScopeInput):
    units: int = Field(ge=1, le=100000)


class SandboxConsumeInput(BillingScopeInput):
    admission_ref: str = Field(min_length=1, max_length=128)


class FeedbackInput(AdminInput):
    body: str = Field(min_length=1, max_length=2000)


class CapacityPriceInput(AdminInput):
    cycle_months: Literal[1, 12]
    base_amount_vnd: int = Field(ge=1, le=2000000000)
    slot_amount_vnd: int = Field(ge=1, le=2000000000)


class CapacityQuoteInput(AdminInput):
    mode: Literal["START", "ADDON", "RENEW"]
    organization_ref: str | None = Field(None, min_length=1, max_length=128)
    price_id: str | None = Field(None, min_length=1, max_length=36)
    addon_slots: int = Field(0, ge=0, le=1000)

    @model_validator(mode="after")
    def initial_quote_fields(self):
        if self.mode == "START" and (not self.organization_ref or not self.price_id):
            raise ValueError("Initial quote requires organization_ref and price_id")
        return self


class SubscriptionConfigInput(AdminInput):
    action: Literal["cancel_renewal", "resume_renewal", "downgrade"]
    addon_slots: int | None = Field(None, ge=0, le=1000)
    suspend_class_refs: list[str] = Field(default_factory=list, max_length=1010)
