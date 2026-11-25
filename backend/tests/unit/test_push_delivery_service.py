from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest

from sketch2life.application.ports.push_delivery import (
    PushDeliveryClaim,
    PushDeliveryClaimResult,
    PushDeliveryRecordResult,
    PushMessage,
    PushSendOutcome,
    PushSendResult,
)
from sketch2life.application.services.notification_templates import eligible_template_keys
from sketch2life.application.services.push_delivery import PushDeliveryWorker
from sketch2life.domain.push_delivery import (
    CLAIM_LEASE,
    MAX_ATTEMPTS,
    PushDeliveryErrorCode,
    PushDeliveryStatus,
    push_pointer,
    retry_delay,
)
from sketch2life.domain.story_run_reminder import (
    REMINDER_NOTIFICATION_TYPE,
    REMINDER_TEMPLATE_VERSION,
)
from sketch2life.infrastructure.notifications.push_delivery_fakes import (
    LocalFakePushSender,
)

NOW = datetime(2026, 11, 25, 12, 0, tzinfo=UTC)


@dataclass
class FakeInboxItem:
    inbox_item_id: str
    recipient_account_id: str
    notification_type: str
    template_version: int
    created_at: datetime
    read_at: datetime | None = None
    expires_at: datetime | None = None


@dataclass
class FakeEndpoint:
    push_endpoint_id: str
    recipient_account_id: str
    endpoint_ciphertext: bytes
    active: bool = True
    version: int = 1
    revoke_calls: int = 0


@dataclass
class FakeDelivery:
    delivery_id: str
    inbox_item_id: str
    push_endpoint_id: str
    recipient_account_id: str
    status: PushDeliveryStatus
    attempt_count: int
    next_attempt_at: datetime
    created_at: datetime
    last_attempt_at: datetime | None = None
    last_error_code: str | None = None
    completed_at: datetime | None = None


class InMemoryPushDeliveryStore:
    """Test-only store fake with the same enrollment, lease, ordering and CAS rules."""

    def __init__(self) -> None:
        self.items: dict[str, FakeInboxItem] = {}
        self.endpoints: dict[str, FakeEndpoint] = {}
        self.deliveries: list[FakeDelivery] = []
        self._sequence = 0

    def add_item(
        self,
        inbox_item_id: str,
        recipient_account_id: str,
        *,
        created_at: datetime = NOW,
        notification_type: str = REMINDER_NOTIFICATION_TYPE,
        template_version: int = REMINDER_TEMPLATE_VERSION,
        read_at: datetime | None = None,
        expires_at: datetime | None = None,
    ) -> FakeInboxItem:
        item = FakeInboxItem(
            inbox_item_id,
            recipient_account_id,
            notification_type,
            template_version,
            created_at,
            read_at,
            expires_at,
        )
        self.items[item.inbox_item_id] = item
        return item

    def add_endpoint(
        self,
        push_endpoint_id: str,
        recipient_account_id: str,
        *,
        endpoint_ciphertext: bytes = b"synthetic-ciphertext",
    ) -> FakeEndpoint:
        endpoint = FakeEndpoint(push_endpoint_id, recipient_account_id, endpoint_ciphertext)
        self.endpoints[endpoint.push_endpoint_id] = endpoint
        return endpoint

    def add_delivery(
        self,
        item: FakeInboxItem,
        endpoint: FakeEndpoint,
        *,
        created_at: datetime,
        next_attempt_at: datetime,
        status: PushDeliveryStatus = PushDeliveryStatus.PENDING,
        attempt_count: int = 0,
        delivery_id: str | None = None,
    ) -> FakeDelivery:
        self._sequence += 1
        row = FakeDelivery(
            delivery_id or f"delivery-{self._sequence:04d}",
            item.inbox_item_id,
            endpoint.push_endpoint_id,
            item.recipient_account_id,
            status,
            attempt_count,
            next_attempt_at,
            created_at,
        )
        self.deliveries.append(row)
        return row

    def enroll(
        self,
        *,
        now: datetime,
        limit: int,
        eligible_templates: frozenset[tuple[str, int]],
        window: timedelta,
    ) -> int:
        enrolled_pairs = {(row.inbox_item_id, row.push_endpoint_id) for row in self.deliveries}
        candidates: list[tuple[FakeInboxItem, FakeEndpoint]] = []
        for item in self.items.values():
            if (
                item.read_at is not None
                or item.created_at < now - window
                or item.created_at > now
                or (item.expires_at is not None and item.expires_at <= now)
                or (item.notification_type, item.template_version) not in eligible_templates
            ):
                continue
            for endpoint in self.endpoints.values():
                if (
                    endpoint.active
                    and endpoint.recipient_account_id == item.recipient_account_id
                    and (item.inbox_item_id, endpoint.push_endpoint_id) not in enrolled_pairs
                ):
                    candidates.append((item, endpoint))
        candidates.sort(
            key=lambda pair: (pair[1].push_endpoint_id, pair[0].created_at, pair[0].inbox_item_id)
        )
        selected = candidates[:limit]
        for item, endpoint in selected:
            self.add_delivery(
                item,
                endpoint,
                created_at=now,
                next_attempt_at=now,
            )
        return len(selected)

    def claim_due(
        self, *, now: datetime, eligible_templates: frozenset[tuple[str, int]]
    ) -> PushDeliveryClaimResult:
        pending = [
            row
            for row in self.deliveries
            if row.status is PushDeliveryStatus.PENDING
            and row.next_attempt_at <= now
            and row.created_at <= now
        ]
        pending.sort(
            key=lambda row: (
                row.next_attempt_at,
                row.push_endpoint_id,
                row.created_at,
                row.delivery_id,
            )
        )
        for row in pending:
            earlier = any(
                other.status is PushDeliveryStatus.PENDING
                and other.push_endpoint_id == row.push_endpoint_id
                and (other.created_at, other.delivery_id) < (row.created_at, row.delivery_id)
                for other in self.deliveries
            )
            if earlier:
                continue
            item = self.items[row.inbox_item_id]
            endpoint = self.endpoints[row.push_endpoint_id]
            if (
                item.read_at is not None
                or (item.expires_at is not None and item.expires_at <= now)
                or (item.notification_type, item.template_version) not in eligible_templates
                or not endpoint.active
            ):
                row.status = PushDeliveryStatus.SKIPPED
                row.completed_at = now
                return PushDeliveryClaimResult(None, skipped=True)
            if row.attempt_count >= MAX_ATTEMPTS:
                row.status = PushDeliveryStatus.FAILED
                row.completed_at = now
                return PushDeliveryClaimResult(None, failed=True)
            row.attempt_count += 1
            row.last_attempt_at = now
            row.next_attempt_at = now + CLAIM_LEASE
            return PushDeliveryClaimResult(
                PushDeliveryClaim(
                    row.delivery_id,
                    row.inbox_item_id,
                    row.push_endpoint_id,
                    row.recipient_account_id,
                    endpoint.endpoint_ciphertext,
                    row.attempt_count,
                    row.created_at,
                )
            )
        return PushDeliveryClaimResult(None)

    def record_outcome(
        self,
        *,
        claim: PushDeliveryClaim,
        result: PushSendResult,
        now: datetime,
    ) -> PushDeliveryRecordResult:
        row = next(
            (item for item in self.deliveries if item.delivery_id == claim.delivery_id),
            None,
        )
        if (
            row is None
            or row.status is not PushDeliveryStatus.PENDING
            or row.attempt_count != claim.attempt_count
        ):
            return PushDeliveryRecordResult.STALE
        if result.outcome is PushSendOutcome.SENT:
            row.status = PushDeliveryStatus.SENT
            row.completed_at = now
            row.last_error_code = None
            return PushDeliveryRecordResult.SENT
        if result.outcome is PushSendOutcome.ENDPOINT_GONE:
            row.status = PushDeliveryStatus.DEAD_ENDPOINT
            row.completed_at = now
            row.last_error_code = PushDeliveryErrorCode.ENDPOINT_GONE.value
            endpoint = self.endpoints[row.push_endpoint_id]
            if endpoint.active:
                endpoint.active = False
                endpoint.version += 1
                endpoint.revoke_calls += 1
            return PushDeliveryRecordResult.DEAD_ENDPOINT
        row.last_error_code = result.outcome.value
        if claim.attempt_count >= MAX_ATTEMPTS:
            row.status = PushDeliveryStatus.FAILED
            row.completed_at = now
            return PushDeliveryRecordResult.FAILED
        row.next_attempt_at = now + retry_delay(claim.attempt_count)
        return PushDeliveryRecordResult.RETRY


class CapturePointerSender:
    def __init__(self) -> None:
        self.payloads: list[dict[str, object]] = []

    def send(self, message: PushMessage) -> PushSendResult:
        self.payloads.append(dict(message.payload))
        return PushSendResult(PushSendOutcome.SENT)


def _single_pending_store(
    *,
    item_id: str = "item-0001",
    endpoint_id: str = "endpoint-0001",
    ciphertext: bytes = b"opaque-envelope",
) -> tuple[InMemoryPushDeliveryStore, FakeInboxItem, FakeEndpoint, FakeDelivery]:
    store = InMemoryPushDeliveryStore()
    item = store.add_item(item_id, "recipient-1")
    endpoint = store.add_endpoint(
        endpoint_id,
        "recipient-1",
        endpoint_ciphertext=ciphertext,
    )
    row = store.add_delivery(item, endpoint, created_at=NOW, next_attempt_at=NOW)
    return store, item, endpoint, row


def test_in_memory_store_exposes_the_delivery_store_protocol_methods() -> None:
    assert callable(InMemoryPushDeliveryStore.enroll)
    assert callable(InMemoryPushDeliveryStore.claim_due)
    assert callable(InMemoryPushDeliveryStore.record_outcome)


def test_worker_reads_its_injected_clock_once() -> None:
    store = InMemoryPushDeliveryStore()
    clock_calls: list[int] = []

    def clock() -> datetime:
        clock_calls.append(1)
        return NOW

    report = PushDeliveryWorker(store, CapturePointerSender(), clock=clock).run_once(batch=1)

    assert report.enrolled == 0
    assert len(clock_calls) == 1


def test_enrollment_includes_23h59_items_and_excludes_24h01_items(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    store = InMemoryPushDeliveryStore()
    store.add_endpoint("endpoint-1", "recipient-1")
    store.add_item("recent-item", "recipient-1", created_at=NOW - timedelta(hours=23, minutes=59))
    store.add_item("old-item", "recipient-1", created_at=NOW - timedelta(hours=24, minutes=1))

    report = PushDeliveryWorker(store, LocalFakePushSender()).run_once(now=NOW, batch=10)

    assert report.enrolled == 1
    assert report.sent == 1
    assert {row.inbox_item_id for row in store.deliveries} == {"recent-item"}


def test_read_expired_and_no_longer_eligible_rows_are_skipped() -> None:
    store = InMemoryPushDeliveryStore()
    endpoint = store.add_endpoint("endpoint-1", "recipient-1")
    read = store.add_item("read-item", "recipient-1", read_at=NOW - timedelta(minutes=1))
    expired = store.add_item("expired-item", "recipient-1", expires_at=NOW)
    unknown = store.add_item("unknown-item", "recipient-1", notification_type="UNKNOWN_NOTICE")
    for item in (read, expired, unknown):
        store.add_delivery(
            item,
            endpoint,
            created_at=NOW - timedelta(minutes=2),
            next_attempt_at=NOW,
        )

    report = PushDeliveryWorker(store, CapturePointerSender()).run_once(now=NOW, batch=10)

    assert report.skipped == 3
    assert all(row.status is PushDeliveryStatus.SKIPPED for row in store.deliveries)


def test_success_sends_exact_content_free_pointer_and_marks_sent() -> None:
    store, _item, _endpoint, row = _single_pending_store()
    sender = CapturePointerSender()

    report = PushDeliveryWorker(store, sender).run_once(now=NOW, batch=1)

    assert report.sent == 1
    assert row.status is PushDeliveryStatus.SENT
    assert sender.payloads == [push_pointer(row.inbox_item_id)]
    assert set(sender.payloads[0]) == {"v", "kind", "inbox_item_id"}


def test_transient_failures_use_each_retry_delay_and_fail_on_attempt_five(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    store, _item, _endpoint, row = _single_pending_store()
    sender = LocalFakePushSender([PushSendOutcome.TRANSIENT] * MAX_ATTEMPTS)
    worker = PushDeliveryWorker(store, sender)
    instant = NOW

    for attempt in range(1, MAX_ATTEMPTS + 1):
        report = worker.run_once(now=instant, batch=1)
        assert row.attempt_count == attempt
        if attempt < MAX_ATTEMPTS:
            delay = retry_delay(attempt)
            assert report.retry == 1
            assert row.next_attempt_at == instant + delay
            instant = row.next_attempt_at
        else:
            assert report.failed == 1
            assert row.status is PushDeliveryStatus.FAILED
            assert row.completed_at == instant


def test_crashed_claim_is_reclaimed_after_its_lease() -> None:
    store, _item, _endpoint, _row = _single_pending_store()
    eligible = eligible_template_keys()

    first = store.claim_due(now=NOW, eligible_templates=eligible).claim
    assert first is not None and first.attempt_count == 1
    assert (
        store.claim_due(
            now=NOW + CLAIM_LEASE - timedelta(seconds=1), eligible_templates=eligible
        ).claim
        is None
    )
    reclaimed = store.claim_due(now=NOW + CLAIM_LEASE, eligible_templates=eligible).claim

    assert reclaimed is not None and reclaimed.attempt_count == 2


def test_only_endpoint_gone_marks_dead_and_revokes_endpoint() -> None:
    store, _item, endpoint, row = _single_pending_store()
    eligible = eligible_template_keys()
    claim = store.claim_due(now=NOW, eligible_templates=eligible).claim
    assert claim is not None

    result = store.record_outcome(
        claim=claim,
        result=PushSendResult(PushSendOutcome.ENDPOINT_GONE),
        now=NOW,
    )

    assert result is PushDeliveryRecordResult.DEAD_ENDPOINT
    assert row.status is PushDeliveryStatus.DEAD_ENDPOINT
    assert row.last_error_code == PushDeliveryErrorCode.ENDPOINT_GONE.value
    assert endpoint.active is False
    assert endpoint.version == 2
    assert endpoint.revoke_calls == 1


def test_transient_failure_never_revokes_endpoint() -> None:
    store, _item, endpoint, row = _single_pending_store()
    claim = store.claim_due(now=NOW, eligible_templates=eligible_template_keys()).claim
    assert claim is not None

    result = store.record_outcome(
        claim=claim,
        result=PushSendResult(PushSendOutcome.TRANSIENT),
        now=NOW,
    )

    assert result is PushDeliveryRecordResult.RETRY
    assert row.status is PushDeliveryStatus.PENDING
    assert endpoint.active is True
    assert endpoint.version == 1
    assert endpoint.revoke_calls == 0


def test_sender_exception_is_recorded_as_safe_code_without_message_leak(
    caplog: pytest.LogCaptureFixture,
) -> None:
    store, _item, _endpoint, row = _single_pending_store()

    class ExplodingSender:
        def send(self, _message: PushMessage) -> PushSendResult:
            raise RuntimeError("secret-token child-name run-id")

    report = PushDeliveryWorker(store, ExplodingSender()).run_once(now=NOW, batch=1)  # type: ignore[arg-type]

    assert report.retry == 1
    assert row.last_error_code == PushDeliveryErrorCode.SENDER_ERROR.value
    assert "secret-token" not in caplog.text
    assert "child-name" not in caplog.text
    assert "run-id" not in caplog.text


def test_head_of_line_wait_does_not_block_a_different_endpoint() -> None:
    store = InMemoryPushDeliveryStore()
    first = store.add_endpoint("endpoint-a", "recipient-a")
    second = store.add_endpoint("endpoint-b", "recipient-b")
    earlier_item = store.add_item("earlier", "recipient-a")
    later_item = store.add_item("later", "recipient-a")
    independent_item = store.add_item("independent", "recipient-b")
    store.add_delivery(
        earlier_item,
        first,
        created_at=NOW - timedelta(minutes=2),
        next_attempt_at=NOW + timedelta(minutes=1),
        delivery_id="a-1",
    )
    later = store.add_delivery(
        later_item,
        first,
        created_at=NOW - timedelta(minutes=1),
        next_attempt_at=NOW,
        delivery_id="a-2",
    )
    independent = store.add_delivery(
        independent_item,
        second,
        created_at=NOW - timedelta(minutes=1),
        next_attempt_at=NOW,
        delivery_id="b-1",
    )
    sender = CapturePointerSender()

    report = PushDeliveryWorker(store, sender).run_once(now=NOW, batch=5)

    assert report.sent == 1
    assert independent.status is PushDeliveryStatus.SENT
    assert later.status is PushDeliveryStatus.PENDING
    assert sender.payloads == [push_pointer("independent")]


def test_same_endpoint_deliveries_keep_created_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    store = InMemoryPushDeliveryStore()
    endpoint = store.add_endpoint("endpoint-a", "recipient-a")
    first_item = store.add_item("first", "recipient-a")
    second_item = store.add_item("second", "recipient-a")
    first = store.add_delivery(
        first_item,
        endpoint,
        created_at=NOW - timedelta(minutes=2),
        next_attempt_at=NOW,
        delivery_id="a-1",
    )
    second = store.add_delivery(
        second_item,
        endpoint,
        created_at=NOW - timedelta(minutes=1),
        next_attempt_at=NOW,
        delivery_id="a-2",
    )
    sender = LocalFakePushSender()

    report = PushDeliveryWorker(store, sender).run_once(now=NOW, batch=2)

    assert report.sent == 2
    assert [record.delivery_id for record in sender.records] == [
        first.delivery_id,
        second.delivery_id,
    ]


def test_late_finisher_cannot_overwrite_a_newer_attempt() -> None:
    store, _item, _endpoint, row = _single_pending_store()
    eligible = eligible_template_keys()
    first = store.claim_due(now=NOW, eligible_templates=eligible).claim
    assert first is not None
    second = store.claim_due(now=NOW + CLAIM_LEASE, eligible_templates=eligible).claim
    assert second is not None

    late = store.record_outcome(
        claim=first,
        result=PushSendResult(PushSendOutcome.SENT),
        now=NOW + CLAIM_LEASE,
    )
    current = store.record_outcome(
        claim=second,
        result=PushSendResult(PushSendOutcome.SENT),
        now=NOW + CLAIM_LEASE,
    )

    assert late is PushDeliveryRecordResult.STALE
    assert current is PushDeliveryRecordResult.SENT
    assert row.status is PushDeliveryStatus.SENT


def test_delivery_rows_and_fake_sender_records_never_retain_ciphertext_or_content(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    secret = b"opaque-secret-token-child-name-run-42"
    store, _item, _endpoint, _row = _single_pending_store(ciphertext=secret)
    sender = LocalFakePushSender()

    PushDeliveryWorker(store, sender).run_once(now=NOW, batch=1)

    assert secret.decode() not in repr(store.deliveries)
    assert "secret-token" not in repr(sender.records)
    assert "child-name" not in repr(sender.records)
    assert "run-42" not in repr(sender.records)
    assert secret.decode() not in caplog.text
    assert all(
        set(record.__dataclass_fields__) == {"delivery_id", "push_endpoint_id"}
        for record in sender.records
    )
