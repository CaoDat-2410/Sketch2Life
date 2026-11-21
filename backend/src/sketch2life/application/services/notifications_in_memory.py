"""In-memory ``NotificationProducerPort`` for unit tests of later producers (T-8a review T8A-I5).

Same validation (``validate_command``), same canonical hash and same dedupe semantics as
``SqlNotificationProducer``: one item per ``(recipient_account_id, dedupe_key)``; the same command
returns the stored id with ``created=False``; another command on the same key raises
``NotificationDedupeConflict``. A rejected command stores nothing. Nothing is delivered and nothing
is persisted; ``items`` exposes the recorded commands for assertions.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import uuid4

from sketch2life.application.ports.notifications import (
    EnqueueResult,
    NotificationCommandV1,
    NotificationDedupeConflict,
)
from sketch2life.application.services.notifications import command_sha256, validate_command


def _utc_now() -> datetime:
    return datetime.now(UTC)


class InMemoryNotificationProducer:
    """Records the accepted commands in the order they were first enqueued."""

    def __init__(self, clock: Callable[[], datetime] = _utc_now) -> None:
        self._clock = clock
        self._by_key: dict[tuple[str, str], tuple[str, str, NotificationCommandV1]] = {}

    @property
    def items(self) -> list[NotificationCommandV1]:
        return [command for _, _, command in self._by_key.values()]

    def enqueue(self, command: NotificationCommandV1) -> EnqueueResult:
        validate_command(command, created_at=self._clock())
        digest = command_sha256(command)
        key = (command.recipient_account_id, command.dedupe_key)
        stored = self._by_key.get(key)
        if stored is None:
            item_id = str(uuid4())
            self._by_key[key] = (item_id, digest, command)
            return EnqueueResult(inbox_item_id=item_id, created=True)
        if stored[1] != digest:
            raise NotificationDedupeConflict(command.dedupe_key)
        return EnqueueResult(inbox_item_id=stored[0], created=False)


__all__ = ["InMemoryNotificationProducer"]
