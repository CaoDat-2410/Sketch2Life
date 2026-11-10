"""Versioned request and response contracts for Parent child profiles."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ParentProfileRequestV1(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    age_months: int = Field(ge=36, le=120)
    display_name: str = Field(min_length=1, max_length=120)
    interests_summary: str = Field(default="", max_length=800)


class ParentProfileCreateRequestV1(ParentProfileRequestV1):
    consent_accepted: Literal[True]
    consent_policy_version: str = Field(min_length=1, max_length=80)


class ParentProfileUpdateRequestV1(ParentProfileRequestV1):
    expected_revision: int = Field(ge=1)


class ParentDataAuthorizationRequestV1(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)

    consent_accepted: Literal[True]
    consent_policy_version: str = Field(min_length=1, max_length=80)


class ParentProfileRevisionResponseV1(BaseModel):
    profile_revision_id: str
    revision: int
    age_months: int
    display_name: str
    interests_summary: str
    revision_sha256: str
    created_at: datetime


class ParentProfileResponseV1(BaseModel):
    parent_profile_id: str
    state: Literal["ACTIVE", "ARCHIVED", "DELETED"]
    current_revision: ParentProfileRevisionResponseV1
    authorization_state: Literal["GRANTED", "REVOKED", "EXPIRED"] | None
    authorization_policy_version: str | None
    authorization_current: bool
    created_at: datetime
    updated_at: datetime


class ParentConsentPolicyResponseV1(BaseModel):
    purpose_code: str
    policy_version: str
    consent_text: str
    consent_text_sha256: str


class ParentProfileCollectionResponseV1(BaseModel):
    request_id: str
    profiles: list[ParentProfileResponseV1]


class ParentProfileEnvelopeV1(BaseModel):
    request_id: str
    profile: ParentProfileResponseV1


class ParentConsentPolicyEnvelopeV1(BaseModel):
    request_id: str
    policy: ParentConsentPolicyResponseV1


__all__ = [
    "ParentConsentPolicyEnvelopeV1",
    "ParentConsentPolicyResponseV1",
    "ParentDataAuthorizationRequestV1",
    "ParentProfileCollectionResponseV1",
    "ParentProfileCreateRequestV1",
    "ParentProfileEnvelopeV1",
    "ParentProfileRequestV1",
    "ParentProfileResponseV1",
    "ParentProfileRevisionResponseV1",
    "ParentProfileUpdateRequestV1",
]
