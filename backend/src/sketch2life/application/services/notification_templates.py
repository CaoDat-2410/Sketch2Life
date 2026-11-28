"""Server-side notification template metadata; client copy remains a separate product decision."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from sketch2life.domain.billing_notice import (
    BILLING_GRACE_EXPIRED,
    BILLING_ORG_PAYMENT_FAILED,
    BILLING_ORG_PAYMENT_SUCCEEDED,
    BILLING_PARENT_PAYMENT_FAILED,
    BILLING_PARENT_PAYMENT_SUCCEEDED,
    BILLING_RENEWAL_DUE_1D,
    BILLING_RENEWAL_DUE_7D,
    BILLING_TEMPLATE_KIND,
    BILLING_TEMPLATE_VERSION,
)
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

_BILLING_TEMPLATES = (
    NotificationTemplateSpec(
        notification_type=BILLING_RENEWAL_DUE_7D,
        version=BILLING_TEMPLATE_VERSION,
        kind=BILLING_TEMPLATE_KIND,
        recipient_role="school_manager",
        allowed_parameters=("subscription_ref", "due_local_date"),
        push_eligible=True,
    ),
    NotificationTemplateSpec(
        notification_type=BILLING_RENEWAL_DUE_1D,
        version=BILLING_TEMPLATE_VERSION,
        kind=BILLING_TEMPLATE_KIND,
        recipient_role="school_manager",
        allowed_parameters=("subscription_ref", "due_local_date"),
        push_eligible=True,
    ),
    NotificationTemplateSpec(
        notification_type=BILLING_GRACE_EXPIRED,
        version=BILLING_TEMPLATE_VERSION,
        kind=BILLING_TEMPLATE_KIND,
        recipient_role="school_manager",
        allowed_parameters=("subscription_ref", "due_local_date"),
        push_eligible=True,
    ),
    NotificationTemplateSpec(
        notification_type=BILLING_ORG_PAYMENT_SUCCEEDED,
        version=BILLING_TEMPLATE_VERSION,
        kind=BILLING_TEMPLATE_KIND,
        recipient_role="school_manager",
        allowed_parameters=("invoice_ref",),
        push_eligible=True,
    ),
    NotificationTemplateSpec(
        notification_type=BILLING_ORG_PAYMENT_FAILED,
        version=BILLING_TEMPLATE_VERSION,
        kind=BILLING_TEMPLATE_KIND,
        recipient_role="school_manager",
        allowed_parameters=("invoice_ref",),
        push_eligible=True,
    ),
    NotificationTemplateSpec(
        notification_type=BILLING_PARENT_PAYMENT_SUCCEEDED,
        version=BILLING_TEMPLATE_VERSION,
        kind=BILLING_TEMPLATE_KIND,
        recipient_role="parent",
        allowed_parameters=("invoice_ref",),
        push_eligible=True,
    ),
    NotificationTemplateSpec(
        notification_type=BILLING_PARENT_PAYMENT_FAILED,
        version=BILLING_TEMPLATE_VERSION,
        kind=BILLING_TEMPLATE_KIND,
        recipient_role="parent",
        allowed_parameters=("invoice_ref",),
        push_eligible=True,
    ),
)

TEMPLATE_REGISTRY: Final[Mapping[tuple[str, int], NotificationTemplateSpec]] = MappingProxyType(
    {
        (_REMINDER.notification_type, _REMINDER.version): _REMINDER,
        **{
            (spec.notification_type, spec.version): spec
            for spec in _BILLING_TEMPLATES
        },
    }
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
