from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

import pytest

from sketch2life.application.ports.billing_notice import (
    BillingNoticeCandidate,
    BillingNoticeCandidatePage,
    BillingNoticeOutcome,
    BillingNoticeScanCursor,
    BillingNoticeSweepResult,
)
from sketch2life.application.services.billing_notice import (
    DEFAULT_BATCH_SIZE,
    MAX_BATCH_SIZE,
    BillingNoticeSweep,
    decode_scan_cursor,
    encode_scan_cursor,
    payment_notice_command,
    subscription_notice_command,
)
from sketch2life.application.services.notification_templates import lookup_template
from sketch2life.application.services.notifications import validate_command
from sketch2life.domain.billing_notice import BillingNoticeKind, BillingNoticeSource
from sketch2life.infrastructure.notifications import billing_notice_store

NOW = datetime(2026, 11, 25, 12, 0, tzinfo=UTC)
ORG_ID = "12345678-1234-1234-1234-123456789abc"
ACCOUNT_ID = "abcdef12-1234-1234-1234-123456789abc"


@dataclass
class FakeBillingNoticeStore:
    page: BillingNoticeCandidatePage = field(
        default_factory=lambda: BillingNoticeCandidatePage((), False)
    )
    outcomes: dict[str, BillingNoticeOutcome | Exception] = field(default_factory=dict)
    scans: list[tuple[datetime, BillingNoticeSource, int, BillingNoticeScanCursor | None]] = field(
        default_factory=list
    )
    processed: list[tuple[BillingNoticeCandidate, datetime]] = field(default_factory=list)

    def scan_candidates(
        self,
        now: datetime,
        source: BillingNoticeSource,
        limit: int,
        cursor: BillingNoticeScanCursor | None,
    ) -> BillingNoticeCandidatePage:
        self.scans.append((now, source, limit, cursor))
        return self.page

    def enqueue_if_due(
        self, candidate: BillingNoticeCandidate, now: datetime
    ) -> BillingNoticeOutcome:
        self.processed.append((candidate, now))
        outcome = self.outcomes.get(candidate.subject_id, BillingNoticeOutcome.CREATED)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def subscription_candidate(subject_id: str) -> BillingNoticeCandidate:
    return BillingNoticeCandidate(
        source=BillingNoticeSource.SUBSCRIPTIONS,
        kind=BillingNoticeKind.RENEWAL_7D,
        subject_id=subject_id,
        timestamp=NOW + timedelta(days=7),
        owner_kind="ORGANIZATION",
        owner_ref=ORG_ID,
        state="ACTIVE",
    )


def payment_candidate(subject_id: str) -> BillingNoticeCandidate:
    return BillingNoticeCandidate(
        source=BillingNoticeSource.PAYMENTS,
        kind=BillingNoticeKind.PAYMENT_SUCCEEDED,
        subject_id=subject_id,
        timestamp=NOW,
        owner_kind="PARENT_ACCOUNT",
        owner_ref=ACCOUNT_ID,
        state="PAID",
        invoice_id="invoice-123",
    )


def test_cursor_roundtrips_and_rejects_invalid_or_noncanonical_tokens() -> None:
    cursor = BillingNoticeScanCursor(
        BillingNoticeSource.PAYMENTS,
        NOW - timedelta(seconds=1),
        "event-123",
    )
    token = encode_scan_cursor(cursor)
    assert decode_scan_cursor(token) == cursor

    spaced = json.dumps(
        ["payments", "2026-11-25T11:59:59.000000Z", "event-123"]
    ).encode()
    noncanonical = base64.urlsafe_b64encode(spaced).decode().rstrip("=")
    for invalid in ("", "%%%", "e30", noncanonical):
        with pytest.raises(ValueError):
            decode_scan_cursor(invalid)


def test_sweep_uses_one_clock_and_advances_a_source_specific_cursor() -> None:
    rows = (subscription_candidate("sub-a"), subscription_candidate("sub-b"))
    store = FakeBillingNoticeStore(
        page=BillingNoticeCandidatePage(rows, has_more=True),
        outcomes={"sub-a": BillingNoticeOutcome.ALREADY_PRESENT},
    )

    result = BillingNoticeSweep(store, store, clock=lambda: NOW).run_once(
        limit=2,
        source=BillingNoticeSource.SUBSCRIPTIONS,
    )

    assert (result.scanned, result.created, result.already_present) == (2, 1, 1)
    assert result.skipped_stale == result.no_recipient == result.failed == 0
    assert decode_scan_cursor(result.next_cursor or "") == rows[-1].cursor
    assert store.scans == [(NOW, BillingNoticeSource.SUBSCRIPTIONS, 2, None)]
    assert all(instant == NOW for _, instant in store.processed)


def test_sweep_counts_no_recipient_stale_and_adapter_failure_without_logging(
    caplog: pytest.LogCaptureFixture,
) -> None:
    rows = (
        payment_candidate("no-manager"),
        payment_candidate("stale-event"),
        payment_candidate("broken-event"),
    )
    store = FakeBillingNoticeStore(
        page=BillingNoticeCandidatePage(rows, has_more=False),
        outcomes={
            "no-manager": BillingNoticeOutcome.NO_RECIPIENT,
            "stale-event": BillingNoticeOutcome.STALE,
            "broken-event": RuntimeError("private invoice detail"),
        },
    )

    result = BillingNoticeSweep(store, store).run_once(NOW, source="payments")

    assert result.scanned == 3
    assert result.no_recipient == result.skipped_stale == result.failed == 1
    assert result.created == result.already_present == 0
    assert "private invoice detail" not in caplog.text


def test_sweep_refuses_bad_limits_mismatched_cursor_source_and_invalid_pages() -> None:
    store = FakeBillingNoticeStore()
    sweep = BillingNoticeSweep(store, store)
    assert sweep.run_once(source=BillingNoticeSource.PAYMENTS).scanned == 0
    assert store.scans[0][2] == DEFAULT_BATCH_SIZE
    for limit in (0, -1, MAX_BATCH_SIZE + 1, True):
        with pytest.raises(ValueError):
            sweep.run_once(
                NOW,
                limit=limit,  # type: ignore[arg-type]
                source=BillingNoticeSource.PAYMENTS,
            )

    subscription_cursor = encode_scan_cursor(
        BillingNoticeScanCursor(BillingNoticeSource.SUBSCRIPTIONS, NOW, "sub-1")
    )
    with pytest.raises(ValueError):
        sweep.run_once(
            NOW,
            cursor=subscription_cursor,
            source=BillingNoticeSource.PAYMENTS,
        )

    store.page = BillingNoticeCandidatePage((), has_more=True)
    with pytest.raises(ValueError):
        sweep.run_once(NOW, source=BillingNoticeSource.PAYMENTS)


class _FakeMappingsResult:
    def __init__(self, rows: list[dict[str, object]]) -> None:
        self._rows = rows

    def mappings(self) -> _FakeMappingsResult:
        return self

    def all(self) -> list[dict[str, object]]:
        return self._rows


class _FakeScanSession:
    def __init__(self, rows: list[dict[str, object]]) -> None:
        self.rows = rows
        self.rolled_back = False

    def execute(self, _statement: object) -> _FakeMappingsResult:
        return _FakeMappingsResult(self.rows)

    def rollback(self) -> None:
        self.rolled_back = True


def test_scan_domain_mismatch_is_counted_failed_and_advances_keyset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [
        {
            "subject_id": "sub-mismatch",
            "owner_ref": ORG_ID,
            "state": "ACTIVE",
            "timestamp": NOW + timedelta(days=7),
        },
        {
            "subject_id": "sub-lookahead",
            "owner_ref": ORG_ID,
            "state": "ACTIVE",
            "timestamp": NOW + timedelta(days=7),
        },
    ]
    session = _FakeScanSession(rows)
    monkeypatch.setattr(billing_notice_store, "subscription_notice_kind", lambda *_args: None)
    store = billing_notice_store.SqlBillingNoticeStore(session)  # type: ignore[arg-type]

    result = BillingNoticeSweep(store, store).run_once(
        NOW,
        limit=1,
        source=BillingNoticeSource.SUBSCRIPTIONS,
    )

    assert session.rolled_back is True
    assert result.scanned == result.failed == 1
    assert result.created == result.already_present == result.skipped_stale == 0
    assert result.next_cursor is not None
    assert decode_scan_cursor(result.next_cursor) == BillingNoticeScanCursor(
        BillingNoticeSource.SUBSCRIPTIONS,
        NOW + timedelta(days=7),
        "sub-mismatch",
    )


def test_result_enforces_nonnegative_counts_and_outcome_sum() -> None:
    with pytest.raises(ValueError):
        BillingNoticeSweepResult(1, 1, 0, 0, 1, 0, None)
    with pytest.raises(ValueError):
        BillingNoticeSweepResult(-1, 0, 0, 0, 0, -1, None)


def test_each_billing_command_passes_producer_validation_and_template_allowlist() -> None:
    subscription_cases = (
        (BillingNoticeKind.RENEWAL_7D, "BILLING_RENEWAL_DUE_7D"),
        (BillingNoticeKind.RENEWAL_1D, "BILLING_RENEWAL_DUE_1D"),
        (BillingNoticeKind.GRACE_EXPIRED, "BILLING_GRACE_EXPIRED"),
    )
    for kind, notification_type in subscription_cases:
        command = subscription_notice_command(
            recipient_account_id=ACCOUNT_ID,
            organization_ref=ORG_ID,
            kind=kind,
            subscription_id="sub-123",
            period_end=NOW + timedelta(days=7),
        )
        spec = lookup_template(notification_type, 1)
        assert spec is not None
        assert command.recipient_role == spec.recipient_role
        assert set(command.safe_parameters) == set(spec.allowed_parameters)
        validate_command(command, created_at=NOW)

    payment_cases = (
        ("ORGANIZATION", "PAYMENT_SUCCEEDED", "BILLING_ORG_PAYMENT_SUCCEEDED", "school_manager"),
        ("ORGANIZATION", "PAYMENT_FAILED", "BILLING_ORG_PAYMENT_FAILED", "school_manager"),
        ("PARENT_ACCOUNT", "PAYMENT_SUCCEEDED", "BILLING_PARENT_PAYMENT_SUCCEEDED", "parent"),
        ("PARENT_ACCOUNT", "PAYMENT_FAILED", "BILLING_PARENT_PAYMENT_FAILED", "parent"),
    )
    for owner_kind, kind_name, notification_type, role in payment_cases:
        command = payment_notice_command(
            recipient_account_id=ACCOUNT_ID,
            owner_kind=owner_kind,
            owner_ref=ORG_ID if owner_kind == "ORGANIZATION" else ACCOUNT_ID,
            kind=BillingNoticeKind[kind_name],
            invoice_id="invoice-123",
            payment_event_id="event-123",
        )
        spec = lookup_template(notification_type, 1)
        assert spec is not None
        assert command.recipient_role == role == spec.recipient_role
        assert set(command.safe_parameters) == set(spec.allowed_parameters)
        validate_command(command, created_at=NOW)

    assert DEFAULT_BATCH_SIZE <= MAX_BATCH_SIZE
