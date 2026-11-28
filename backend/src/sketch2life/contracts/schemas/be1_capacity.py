"""BE1 School Manager capacity API contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

ClassRef = Annotated[str, StringConstraints(min_length=1, max_length=128)]


class Be1CapacityConfigureRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    action: Literal["cancel_renewal", "resume_renewal", "downgrade"]
    addon_slots: int | None = Field(default=None, ge=0, le=1000)
    suspend_class_refs: list[ClassRef] | None = Field(default=None, max_length=1010)

    @model_validator(mode="after")
    def validate_action_fields(self) -> Be1CapacityConfigureRequest:
        supplied = self.model_fields_set
        if self.action == "downgrade":
            if self.addon_slots is None or self.suspend_class_refs is None:
                raise ValueError("A downgrade requires addon_slots and suspend_class_refs")
        elif "addon_slots" in supplied or "suspend_class_refs" in supplied:
            raise ValueError("Renewal actions do not accept capacity downgrade fields")
        return self


class Be1ScheduledCapacityChangeV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    addon_slots: int = Field(ge=0, le=1000)
    capacity: int = Field(ge=10, le=1010)
    effective_at: datetime
    suspend_class_refs: list[ClassRef]


class Be1OrganizationCapacityV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract: Literal["Be1OrganizationCapacityV1"] = "Be1OrganizationCapacityV1"
    organization_id: str
    subscription_id: str | None = None
    capacity: int = Field(ge=10, le=1010)
    active_class_count: int = Field(ge=0)
    available_slots: int = Field(ge=0)
    subscription_state: str
    revision: int = Field(ge=0)
    period_start: datetime | None = None
    period_end: datetime | None = None
    scheduled_change: Be1ScheduledCapacityChangeV1 | None = None
