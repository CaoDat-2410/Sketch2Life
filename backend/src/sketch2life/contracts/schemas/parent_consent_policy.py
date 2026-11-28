"""Parent consent-policy read contract (T-CONSENT1)."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ParentConsentPurposeV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    purpose_code: str
    text_key: str


class ParentConsentPolicyDetailsV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    purpose_code: str
    policy_version: str
    consent_text: str
    consent_text_sha256: str
    policy_state: Literal["PLACEHOLDER_NOT_APPROVED"]
    data_origin_scope: Literal["SYNTHETIC_TEST"]
    effective_from: date | None
    purposes: list[ParentConsentPurposeV1]
    links: list[str]
    acceptance_recording: Literal["NOT_AVAILABLE"]


class ParentConsentPolicyV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract: Literal["ParentConsentPolicyV1"] = "ParentConsentPolicyV1"
    request_id: str
    policy: ParentConsentPolicyDetailsV1
