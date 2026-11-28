"""Additive response contracts for School Manager video quota labels."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class VideoQuotaContract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SchoolQuotaTeacherV1(VideoQuotaContract):
    teacher_ref: str
    label: str
    display_name: str | None = None
    email_masked: str | None = None


class SchoolQuotaTeacherPageV1(VideoQuotaContract):
    items: list[SchoolQuotaTeacherV1]


class SchoolQuotaAllocationV1(VideoQuotaContract):
    allocation_id: str
    teacher_ref: str
    available_units: int
    active: bool
    revision: int
    updated_at: str | None
    display_name: str | None = None
    email_masked: str | None = None


class SchoolQuotaAllocationPageV1(VideoQuotaContract):
    items: list[SchoolQuotaAllocationV1]
    total: int
