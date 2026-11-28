"""Versioned HTTP contracts for Parent profile sharing and delivery history."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ShareFieldName = Literal["DISPLAY_NAME", "AGE_BAND", "INTERESTS_SUMMARY"]
ShareStateName = Literal["INVITED", "ACTIVE", "REVOKED", "EXPIRED"]


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateShareGrantRequestV1(_StrictModel):
    profile_id: UUID
    granted_fields: list[str] = Field(
        min_length=1,
        max_length=3,
        json_schema_extra={
            "items": {"enum": ["DISPLAY_NAME", "AGE_BAND", "INTERESTS_SUMMARY"]}
        },
    )


class AcceptParentShareRequestV1(_StrictModel):
    invitation_code: str = Field(min_length=16, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")


class ParentShareGrantV1(_StrictModel):
    contract: Literal["ParentShareGrantV1"] = "ParentShareGrantV1"
    share_grant_id: UUID
    profile_id: UUID
    state: ShareStateName
    granted_fields: list[ShareFieldName]
    created_at: datetime
    invitation_expires_at: datetime
    accepted_at: datetime | None
    expires_at: datetime | None
    revoked_at: datetime | None
    revision: int


class ParentShareGrantCreatedV1(ParentShareGrantV1):
    invitation_code: str | None


class ParentShareGrantListV1(_StrictModel):
    contract: Literal["ParentShareGrantListV1"] = "ParentShareGrantListV1"
    items: list[ParentShareGrantV1]
    next_cursor: str | None


class ParentShareDeliveryItemV1(_StrictModel):
    delivered_at: datetime
    title: str | None


class ParentShareDeliveryListV1(_StrictModel):
    contract: Literal["ParentShareDeliveryListV1"] = "ParentShareDeliveryListV1"
    share_grant_id: UUID
    content_access: Literal["AVAILABLE", "ENDED"]
    items: list[ParentShareDeliveryItemV1]
    next_cursor: str | None


class Be1ParentShareLinkV1(_StrictModel):
    contract: Literal["Be1ParentShareLinkV1"] = "Be1ParentShareLinkV1"
    share_grant_id: UUID
    child_id: str
    state: Literal["ACTIVE"]
    granted_fields: list[ShareFieldName]
    accepted_at: datetime
    expires_at: datetime
    revision: int


class Be1ParentSharedAgeBandV1(_StrictModel):
    band_ref: str
    band_version: str


class Be1ParentSharedFieldsV1(_StrictModel):
    display_name: str | None = None
    age_band: Be1ParentSharedAgeBandV1 | None = None
    interests_summary: str | None = None


class Be1ParentSharedProfileV1(_StrictModel):
    contract: Literal["Be1ParentSharedProfileV1"] = "Be1ParentSharedProfileV1"
    share_grant_id: UUID
    child_id: str
    granted_fields: list[ShareFieldName]
    expires_at: datetime
    fields: Be1ParentSharedFieldsV1


__all__ = [
    "AcceptParentShareRequestV1",
    "Be1ParentShareLinkV1",
    "Be1ParentSharedAgeBandV1",
    "Be1ParentSharedFieldsV1",
    "Be1ParentSharedProfileV1",
    "CreateShareGrantRequestV1",
    "ParentShareDeliveryItemV1",
    "ParentShareDeliveryListV1",
    "ParentShareGrantCreatedV1",
    "ParentShareGrantListV1",
    "ParentShareGrantV1",
]
