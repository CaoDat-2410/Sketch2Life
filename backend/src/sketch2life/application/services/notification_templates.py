"""Server-side notification template metadata; client copy remains a separate product decision."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from sketch2life.domain.story_run_reminder import (
    REMINDER_NOTIFICATION_TYPE,
    REMINDER_TEMPLATE_VERSION,
)


@dataclass(frozen=True, slots=True)
class NotificationTemplateSpec:
    notification_type: str
    version: int
    kind: str
    recipient_role: str
    allowed_parameters: tuple[str, ...]
    push_eligible: bool


_REMINDER = NotificationTemplateSpec(
    notification_type=REMINDER_NOTIFICATION_TYPE,
    version=REMINDER_TEMPLATE_VERSION,
    kind="REMINDER",
    recipient_role="parent",
    allowed_parameters=(),
    push_eligible=True,
)

TEMPLATE_REGISTRY: Final[Mapping[tuple[str, int], NotificationTemplateSpec]] = MappingProxyType(
    {(_REMINDER.notification_type, _REMINDER.version): _REMINDER}
)


def lookup_template(notification_type: str, version: int) -> NotificationTemplateSpec | None:
    """Return a registered version, or ``None`` for an unknown notification type/version."""

    return TEMPLATE_REGISTRY.get((notification_type, version))


def is_push_eligible(notification_type: str, version: int) -> bool:
    spec = lookup_template(notification_type, version)
    return spec is not None and spec.push_eligible


def eligible_template_keys() -> frozenset[tuple[str, int]]:
    return frozenset(key for key, spec in TEMPLATE_REGISTRY.items() if spec.push_eligible)


__all__ = [
    "TEMPLATE_REGISTRY",
    "NotificationTemplateSpec",
    "eligible_template_keys",
    "is_push_eligible",
    "lookup_template",
]
