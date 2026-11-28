"""HTTP schemas for School Manager Teacher invitations."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TeacherInvitationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(
        min_length=3,
        max_length=254,
        pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$",
        description="Teacher's email address",
    )


class TeacherInvitationResponse(BaseModel):
    account_ref: str = Field(min_length=1, max_length=36)
    status: Literal["PENDING_VERIFICATION"]
