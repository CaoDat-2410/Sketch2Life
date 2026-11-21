"""The in-memory producer keeps the port's rules for later producers' unit tests (T8A-I5)."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from sketch2life.application.ports.notifications import (
    NotificationCommandV1,
    NotificationDedupeConflict,
    NotificationProducerPort,
    NotificationRejected,
)
from sketch2life.application.services.notifications_in_memory import (
    InMemoryNotificationProducer,
)

NOW = datetime(2026, 11, 21, 7, 0, tzinfo=UTC)


def _command(**overrides: object) -> NotificationCommandV1:
    base = NotificationCommandV1(
        recipient_account_id="11111111-1111-4111-8111-111111111111",
        recipient_role="parent",
        notification_type="CLASS_ARCHIVED",
        template_version=1,
        trigger_id="trg:class.archived:1",
        dedupe_key="class.archived:1:parent",
        safe_parameters={"class_ref": "cls_1", "count": 3},
    )
    return replace(base, **overrides)  # type: ignore[arg-type]


def _producer() -> InMemoryNotificationProducer:
    return InMemoryNotificationProducer(clock=lambda: NOW)


def test_it_satisfies_the_port() -> None:
    port: NotificationProducerPort = _producer()
    assert port.enqueue(_command()).created is True


def test_the_same_command_returns_the_stored_item() -> None:
    producer = _producer()
    first = producer.enqueue(_command())
    again = producer.enqueue(_command(expires_at=NOW + timedelta(hours=1)))
    assert (first.created, again.created) == (True, False)
    assert again.inbox_item_id == first.inbox_item_id
    assert len(producer.items) == 1


def test_another_command_on_the_same_key_is_a_conflict() -> None:
    producer = _producer()
    producer.enqueue(_command())
    with pytest.raises(NotificationDedupeConflict):
        producer.enqueue(_command(safe_parameters={"count": 4}))
    assert len(producer.items) == 1


def test_the_dedupe_key_is_per_recipient() -> None:
    producer = _producer()
    producer.enqueue(_command())
    other = producer.enqueue(_command(recipient_account_id="22222222-2222-4222-8222-222222222222"))
    assert other.created is True
    assert len(producer.items) == 2


def test_a_rejected_command_stores_nothing() -> None:
    producer = _producer()
    with pytest.raises(NotificationRejected):
        producer.enqueue(_command(safe_parameters={"label": "Nguyen Be Lan"}))
    with pytest.raises(NotificationRejected):
        producer.enqueue(_command(expires_at=NOW))
    assert producer.items == []
