"""Public, metadata-only contracts for the BE1 Teacher assignment transfer saga."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Be1TeacherAssignmentTransferAcceptedV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract: Literal["Be1TeacherAssignmentTransferAcceptedV1"] = (
        "Be1TeacherAssignmentTransferAcceptedV1"
    )
    transfer_id: UUID
    class_id: str = Field(min_length=1, max_length=128)
    action: Literal["REASSIGN", "OFFBOARD"]
    state: Literal["TRANSFER_PENDING"]
    assignment_revision: int = Field(ge=1)
    status_url: str = Field(min_length=1, max_length=512)


class Be1TeacherAssignmentTransferStatusV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract: Literal["Be1TeacherAssignmentTransferStatusV1"] = (
        "Be1TeacherAssignmentTransferStatusV1"
    )
    transfer_id: UUID
    class_id: str = Field(min_length=1, max_length=128)
    action: Literal["REASSIGN", "OFFBOARD"]
    state: Literal[
        "TRANSFER_PENDING",
        "RECONCILE_REQUIRED",
        "COMPLETED",
        "OFFBOARDED",
        "COMPENSATED_CONFLICT",
    ]
    assignment_revision: int = Field(ge=1)
    created_at: datetime
    updated_at: datetime
    last_failure_code: str | None = Field(default=None, max_length=64)
    status_url: str = Field(min_length=1, max_length=512)


__all__ = [
    "Be1TeacherAssignmentTransferAcceptedV1",
    "Be1TeacherAssignmentTransferStatusV1",
]
