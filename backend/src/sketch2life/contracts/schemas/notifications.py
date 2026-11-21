"""Notification inbox contracts (FEAT-066 goal v3, T-8a; SRS l.812, l.1681, l.1697, FR-B-09).

The inbox is the source of truth of a notification. An item names its template and version and
carries the producer's safe parameters (codes, counts and opaque references, never display text, a
child name, media or a playback URL). The recipient, role, organization reference, trigger id,
dedupe key and command hash stay on the server. No push endpoint or delivery state is part of this
contract (T-8b is deferred).
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class NotificationV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract: Literal["NotificationV1"] = "NotificationV1"
    inbox_item_id: str
    notification_type: str = Field(
        description="Upper-case template family code, for example CLASS_ARCHIVED."
    )
    template_version: int = Field(ge=1, le=9999)
    safe_parameters: dict[str, bool | int | str] = Field(
        description=(
            "Codes, counts and opaque references for the template; never a name, sentence, URL "
            "or e-mail address. The client resolves the display text from the template version."
        )
    )
    created_at: datetime
    read_at: datetime | None = None
    expires_at: datetime | None = None


class NotificationPageV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract: Literal["NotificationPageV1"] = "NotificationPageV1"
    items: list[NotificationV1]
    next_cursor: str | None = None
    unread_count: int = Field(
        ge=0,
        le=100,
        description=(
            "Unread, unexpired items of the caller, exact up to 99; the value 100 means 100 or "
            "more, so a client shows '99+' (or '100+') and never the bare number 100."
        ),
    )


class NotificationReadAllV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract: Literal["NotificationReadAllV1"] = "NotificationReadAllV1"
    marked_count: int = Field(
        ge=0,
        description="Items that were unread and unexpired when the command first ran.",
    )


__all__ = ["NotificationPageV1", "NotificationReadAllV1", "NotificationV1"]
