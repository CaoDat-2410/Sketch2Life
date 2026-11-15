"""Local-only Parent video-quota display contract."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ParentVideoQuotaSummaryV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract: Literal["ParentVideoQuotaSummaryV1"] = "ParentVideoQuotaSummaryV1"
    mode: Literal["LOCAL_DEMO"]
    configuration_state: Literal["CONFIGURED", "NOT_CONFIGURED"]
    period_start: datetime
    period_end: datetime
    granted: int | None
    used: int | None
    available: int | None
    notice: str


__all__ = ["ParentVideoQuotaSummaryV1"]
