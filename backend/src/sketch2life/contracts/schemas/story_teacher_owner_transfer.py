"""Versioned BE1-to-Story contract for transferring Teacher-owned active runs."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def story_teacher_owner_transfer_key_sha256(
    *, organization_ref: str, class_ref: str, transfer_id: str
) -> str:
    """Hash the scoped BE1 transfer identity; the caller key is scoped at BE1."""
    material = json.dumps(
        [organization_ref, class_ref, transfer_id], separators=(",", ":")
    ).encode("ascii")
    return hashlib.sha256(
        b"story.teacher-owner-transfer.receipt-key.v1\0" + material
    ).hexdigest()


class StoryTeacherOwnerTransferCommandV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract: Literal["StoryTeacherOwnerTransferCommandV1"] = "StoryTeacherOwnerTransferCommandV1"
    transfer_id: str = Field(min_length=36, max_length=36)
    organization_ref: str = Field(min_length=1, max_length=128)
    class_ref: str = Field(min_length=1, max_length=128)
    action: Literal["REASSIGN", "OFFBOARD"]
    old_owner_teacher_ref: str = Field(min_length=1, max_length=36)
    new_owner_teacher_ref: str | None = Field(default=None, max_length=36)
    assignment_revision: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=128)
    request_fingerprint_sha256: str = Field(min_length=64, max_length=64)

    @field_validator("idempotency_key")
    @classmethod
    def visible_ascii_key(cls, value: str) -> str:
        if not value.isascii() or any(ord(char) < 33 or ord(char) > 126 for char in value):
            raise ValueError("idempotency key must use visible ASCII")
        return value

    @field_validator("request_fingerprint_sha256")
    @classmethod
    def fingerprint_is_sha256(cls, value: str) -> str:
        if _SHA256.fullmatch(value) is None:
            raise ValueError("fingerprint must be lowercase SHA-256")
        return value

    @model_validator(mode="after")
    def action_matches_new_owner(self) -> StoryTeacherOwnerTransferCommandV1:
        has_new_owner = self.new_owner_teacher_ref is not None
        if (self.action == "REASSIGN") != has_new_owner:
            raise ValueError("action and new owner reference do not match")
        if has_new_owner and self.new_owner_teacher_ref == self.old_owner_teacher_ref:
            raise ValueError("the new owner must differ from the old owner")
        return self


class StoryTeacherOwnerTransferReceiptV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract: Literal["StoryTeacherOwnerTransferReceiptV1"] = "StoryTeacherOwnerTransferReceiptV1"
    transfer_id: str = Field(min_length=36, max_length=36)
    organization_ref: str = Field(min_length=1, max_length=128)
    class_ref: str = Field(min_length=1, max_length=128)
    action: Literal["REASSIGN", "OFFBOARD"]
    old_owner_teacher_ref: str = Field(min_length=1, max_length=36)
    new_owner_teacher_ref: str | None = Field(default=None, max_length=36)
    assignment_revision: int = Field(ge=1)
    idempotency_key_sha256: str = Field(min_length=64, max_length=64)
    request_fingerprint_sha256: str = Field(min_length=64, max_length=64)
    outcome: Literal["TRANSFERRED", "CONFLICT"]
    owner_epoch: int = Field(ge=0)

    @field_validator("idempotency_key_sha256", "request_fingerprint_sha256")
    @classmethod
    def hashes_are_sha256(cls, value: str) -> str:
        if _SHA256.fullmatch(value) is None:
            raise ValueError("receipt hashes must be lowercase SHA-256")
        return value

    @model_validator(mode="after")
    def action_matches_new_owner(self) -> StoryTeacherOwnerTransferReceiptV1:
        has_new_owner = self.new_owner_teacher_ref is not None
        if (self.action == "REASSIGN") != has_new_owner:
            raise ValueError("action and new owner reference do not match")
        if has_new_owner and self.new_owner_teacher_ref == self.old_owner_teacher_ref:
            raise ValueError("the new owner must differ from the old owner")
        return self


__all__ = [
    "StoryTeacherOwnerTransferCommandV1",
    "StoryTeacherOwnerTransferReceiptV1",
    "story_teacher_owner_transfer_key_sha256",
]
