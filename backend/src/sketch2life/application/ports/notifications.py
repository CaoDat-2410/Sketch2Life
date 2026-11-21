"""Notification producer port (FEAT-066 goal v3, T-8a; SRS l.784, l.1681; FR-B-09).

A producer asks for one inbox notification with a typed ``NotificationCommandV1``: the recipient's
opaque account id and role, the template and its version, the trigger id, the dedupe key and a
small set of safe parameters. The command carries no child content (SRS l.784).

``safe_parameters`` are codes, counts and opaque references, never display text: a person's name,
a sentence, a URL or an e-mail address cannot be written (the rules are an allowlist, see
``application.services.notifications``). Display text belongs to the template version, which the
client resolves; the server stores only which template applies and its parameters.

The port is the only way a notification enters the inbox. A real producer (a class event, billing,
reminders) is not wired in T-8a (T-1d2, X-13, group invitation are deferred); tests act as the
producer through ``SqlNotificationProducer``, the one adapter.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

NotificationParameter = str | int | bool


class NotificationRejected(ValueError):  # noqa: N818 - a domain refusal, not a runtime error
    """The command breaks a rule: nothing was written. ``field`` names the offending part."""

    def __init__(self, field: str, code: str) -> None:
        self.field = field
        self.code = code
        super().__init__(f"{field}: {code}")


class NotificationDedupeConflict(RuntimeError):  # noqa: N818 - a domain refusal
    """The dedupe key already exists for the recipient with a different command."""


@dataclass(frozen=True, slots=True)
class NotificationCommandV1:
    """One notification request (SRS l.784): who, what template, which trigger, which dedupe key."""

    recipient_account_id: str
    recipient_role: str
    notification_type: str
    template_version: int
    trigger_id: str
    dedupe_key: str
    safe_parameters: dict[str, NotificationParameter]
    organization_ref: str | None = None
    expires_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class EnqueueResult:
    """``created`` is false when the same command (same dedupe key and hash) was seen before."""

    inbox_item_id: str
    created: bool


class NotificationProducerPort(Protocol):
    """Writes one inbox item inside the caller's transaction; never commits, never delivers."""

    def enqueue(self, command: NotificationCommandV1) -> EnqueueResult:
        """Validate and store the command, or return the existing item of the same command.

        Raises ``NotificationRejected`` for a rule breach and ``NotificationDedupeConflict`` when
        the dedupe key exists for the recipient with another command hash.
        """
        ...


__all__ = [
    "EnqueueResult",
    "NotificationCommandV1",
    "NotificationDedupeConflict",
    "NotificationParameter",
    "NotificationProducerPort",
    "NotificationRejected",
]
