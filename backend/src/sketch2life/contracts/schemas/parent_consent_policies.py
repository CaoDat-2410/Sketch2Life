"""Versioned HTTP contracts for Platform Admin consent-policy management."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ParentConsentPolicyCreateRequestV1(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    policy_version: str = Field(
        min_length=1,
        max_length=80,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$",
    )
    consent_text: str = Field(min_length=1, max_length=4000)


class ParentConsentPolicyAdminResponseV1(BaseModel):
    policy_id: str
    policy_version: str
    purpose_code: str
    consent_text: str
    consent_text_sha256: str
    state: Literal["DRAFT", "ACTIVE", "RETIRED"]
    created_by: str
    created_at: datetime
    activated_by: str | None
    activated_at: datetime | None


class ParentConsentPolicyAdminEnvelopeV1(BaseModel):
    request_id: str
    policy: ParentConsentPolicyAdminResponseV1


class ParentConsentPolicyAdminCollectionV1(BaseModel):
    request_id: str
    active_policy_id: str | None
    policies: list[ParentConsentPolicyAdminResponseV1]


__all__ = [
    "ParentConsentPolicyAdminCollectionV1",
    "ParentConsentPolicyAdminEnvelopeV1",
    "ParentConsentPolicyAdminResponseV1",
    "ParentConsentPolicyCreateRequestV1",
]
