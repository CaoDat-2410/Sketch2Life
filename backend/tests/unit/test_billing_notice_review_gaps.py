# ruff: noqa: E501, F811, SIM117, B023
"""Missing unit tests for E4 T-BILLN1 named in IMPL_REVIEW_E_E4_R1_20261125.md and E4_PROMPT.md."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
from typing import Any

import pytest

from sketch2life.application.ports.billing_notice import (
    BillingNoticeCandidate,
    BillingNoticeCandidatePage,
    BillingNoticeOutcome,
    BillingNoticeScanCursor,
    BillingNoticeSweepResult,
)
from sketch2life.application.services.billing_notice import (
    BillingNoticeSweep,
    decode_scan_cursor,
    encode_scan_cursor,
    payment_notice_command,
    subscription_notice_command,
)
from sketch2life.domain.billing_notice import (
    GRACE_PERIOD,
    NOTICE_LOOKBACK,
    RENEWAL_LEAD_7D,
    BillingNoticeKind,
    BillingNoticeSource,
    billing_notice_local_date,
    billing_notice_trigger_id,
    payment_notice_due,
    subscription_notice_kind,
)
from sketch2life.infrastructure.notifications import (
    billing_notice_store,
)
from sketch2life.infrastructure.notifications import (
    notification_worker as worker,
)

NOW = datetime(2026, 11, 25, 12, 0, tzinfo=UTC)
ORG_ID = "12345678-1234-1234-1234-123456789abc"
ACCOUNT_ID = "abcdef12-1234-1234-1234-123456789abc"


@pytest.mark.parametrize(
    ("state", "offset", "expected"),
    [
        ("ACTIVE", RENEWAL_LEAD_7D + timedelta(microseconds=1), None),
        ("ACTIVE", -(GRACE_PERIOD - timedelta(microseconds=1)), None),
        ("CANCEL_AT_PERIOD_END", -GRACE_PERIOD, None),
        ("CANCELED", -GRACE_PERIOD, None),
        ("PAYMENT_PENDING", -GRACE_PERIOD, None),
        ("GRACE", -GRACE_PERIOD, BillingNoticeKind.GRACE_EXPIRED),
    ],
)
def test_subscription_notice_edges_before_windows_and_non_active_after_grace(
    state: str,
    offset: timedelta,
    expected: BillingNoticeKind | None,
) -> None:
    """covers: IMPL_REVIEW_E_E4_R1_20261125.md Conformance (E4_PROMPT §5 subscription window & state edges)"""
    period_end = NOW + offset
    assert subscription_notice_kind(state, period_end, NOW) is expected


@pytest.mark.parametrize(
    ("kind", "outcome", "invoice_state", "age"),
    [
        (BillingNoticeKind.PAYMENT_SUCCEEDED, "CANCELED", "CANCELED", timedelta(0)),
        (BillingNoticeKind.PAYMENT_SUCCEEDED, "PAID", "PENDING", timedelta(0)),
        (BillingNoticeKind.PAYMENT_FAILED, "FAILED", "PAID", timedelta(0)),
        (BillingNoticeKind.PAYMENT_FAILED, "PAID", "PAID", timedelta(0)),
        (BillingNoticeKind.GRACE_EXPIRED, "PAID", "PAID", timedelta(0)),
        (BillingNoticeKind.PAYMENT_SUCCEEDED, "PAID", "PAID", NOTICE_LOOKBACK + timedelta(microseconds=1)),
    ],
)
def test_payment_notice_due_rejects_mismatched_states_canceled_and_expired_lookback(
    kind: BillingNoticeKind,
    outcome: str,
    invoice_state: str,
    age: timedelta,
) -> None:
    """covers: IMPL_REVIEW_E_E4_R1_20261125.md Conformance (E4_PROMPT §3 D2 payment due rules)"""
    assert not payment_notice_due(kind, outcome, invoice_state, NOW - age, NOW)


def test_payment_notice_due_rejects_non_utc_now() -> None:
    """covers: IMPL_REVIEW_E_E4_R1_20261125.md Conformance (E4_PROMPT §5 non-UTC clock refused)"""
    local_now = datetime(2026, 11, 25, 19, 0, tzinfo=timezone(timedelta(hours=7)))
    with pytest.raises(ValueError, match="UTC"):
        payment_notice_due(BillingNoticeKind.PAYMENT_SUCCEEDED, "PAID", "PAID", NOW, local_now)


def test_trigger_id_local_date_and_command_builders_reject_invalid_inputs() -> None:
    """covers: IMPL_REVIEW_E_E4_R1_20261125.md Conformance (E4_PROMPT §3 D3/D8 command & identity guards)"""
    with pytest.raises(ValueError):
        billing_notice_trigger_id(BillingNoticeKind.RENEWAL_7D, "", period_end=NOW)
    with pytest.raises(ValueError):
        billing_notice_trigger_id(BillingNoticeKind.PAYMENT_SUCCEEDED, "evt-1", period_end=NOW)
    with pytest.raises(ValueError):
        billing_notice_local_date(BillingNoticeKind.PAYMENT_SUCCEEDED, NOW)
    with pytest.raises(ValueError):
        subscription_notice_command(
            recipient_account_id=ACCOUNT_ID,
            organization_ref=ORG_ID,
            kind=BillingNoticeKind.PAYMENT_SUCCEEDED,
            subscription_id="sub-1",
            period_end=NOW,
        )
    with pytest.raises(ValueError):
        payment_notice_command(
            recipient_account_id=ACCOUNT_ID,
            owner_kind="UNKNOWN_OWNER",
            owner_ref=ORG_ID,
            kind=BillingNoticeKind.PAYMENT_SUCCEEDED,
            invoice_id="inv-1",
            payment_event_id="evt-1",
        )
    with pytest.raises(ValueError):
        payment_notice_command(
            recipient_account_id=ACCOUNT_ID,
            owner_kind="ORGANIZATION",
            owner_ref=ORG_ID,
            kind=BillingNoticeKind.RENEWAL_7D,
            invoice_id="inv-1",
            payment_event_id="evt-1",
        )


def _b64(payload: object) -> str:
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


@pytest.mark.parametrize(
    "token",
    [
        _b64({"source": "subscriptions"}),
        _b64(["subscriptions", "2026-11-25T12:00:00.000000Z"]),
        _b64(["subscriptions", "2026-11-25T12:00:00.000000Z", ""]),
        _b64(["subscriptions", "2026-11-25T12:00:00.000000+00:00", "sub-1"]),
        _b64(["subscriptions", "2026-11-25T19:00:00.000000+07:00", "sub-1"]),
        _b64(["subscriptions", "not-a-timestampZ", "sub-1"]),
        _b64(["invoices", "2026-11-25T12:00:00.000000Z", "inv-1"]),
        _b64(["subscriptions", "2026-11-25T12:00:00Z", "sub-1"]),
    ],
)
def test_decode_scan_cursor_rejects_malformed_and_noncanonical_variants(token: str) -> None:
    """covers: IMPL_REVIEW_E_E4_R1_20261125.md Conformance (E4_PROMPT §5 cursor canonical validation)"""
    with pytest.raises(ValueError):
        decode_scan_cursor(token)


@dataclass
class _ContractCheckingStore:
    page: BillingNoticeCandidatePage
    outcome: Any = BillingNoticeOutcome.CREATED

    def scan_candidates(
        self,
        _now: datetime,
        _source: BillingNoticeSource,
        _limit: int,
        _cursor: BillingNoticeScanCursor | None,
    ) -> BillingNoticeCandidatePage:
        return self.page

    def enqueue_if_due(
        self, _candidate: BillingNoticeCandidate, _now: datetime
    ) -> BillingNoticeOutcome:
        return self.outcome


def _sub_candidate(subject_id: str, source: BillingNoticeSource = BillingNoticeSource.SUBSCRIPTIONS) -> BillingNoticeCandidate:
    return BillingNoticeCandidate(
        source=source,
        kind=BillingNoticeKind.RENEWAL_7D,
        subject_id=subject_id,
        timestamp=NOW + timedelta(days=7),
        owner_kind="ORGANIZATION",
        owner_ref=ORG_ID,
        state="ACTIVE",
    )


def test_sweep_rejects_bad_source_non_utc_now_and_scanner_contract_violations() -> None:
    """covers: IMPL_REVIEW_E_E4_R1_20261125.md Conformance & P3-3 (sweep bounds & scanner invariants)"""
    good_cursor = BillingNoticeScanCursor(BillingNoticeSource.SUBSCRIPTIONS, NOW, "sub-1")
    wrong_cursor = BillingNoticeScanCursor(BillingNoticeSource.PAYMENTS, NOW, "evt-1")

    base_store = _ContractCheckingStore(BillingNoticeCandidatePage((), False))
    sweep = BillingNoticeSweep(base_store, base_store)
    with pytest.raises(ValueError):
        sweep.run_once(NOW, source="unknown-source")
    with pytest.raises(ValueError):
        sweep.run_once(datetime(2026, 11, 25, 12, 0), source=BillingNoticeSource.SUBSCRIPTIONS)

    for bad_page in (
        BillingNoticeCandidatePage((), False, failed_count=-1, last_cursor=good_cursor),
        BillingNoticeCandidatePage((_sub_candidate("sub-1"),), False, failed_count=1, last_cursor=good_cursor),
        BillingNoticeCandidatePage((_sub_candidate("sub-1"),), False, failed_count=0, last_cursor=wrong_cursor),
        BillingNoticeCandidatePage((), False, failed_count=1, last_cursor=None),
        BillingNoticeCandidatePage((_sub_candidate("sub-1", BillingNoticeSource.PAYMENTS),), False),
    ):
        bad_store = _ContractCheckingStore(bad_page)
        with pytest.raises(ValueError):
            BillingNoticeSweep(bad_store, bad_store).run_once(
                NOW, limit=1, source=BillingNoticeSource.SUBSCRIPTIONS
            )


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


def test_mixed_valid_and_domain_mismatch_rows_on_same_page_do_not_abort_page(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """covers: IMPL_REVIEW_E_E4_R1_20261125.md P3-3 (one mismatch skips only that row, keeps valid rows and keyset cursor)"""
    rows = [
        {
            "subject_id": "sub-mismatch",
            "owner_ref": ORG_ID,
            "state": "ACTIVE",
            "timestamp": NOW + timedelta(days=7),
        },
        {
            "subject_id": "sub-valid",
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
    seen: list[str] = []

    def fake_enqueue(self: Any, candidate: BillingNoticeCandidate, _now: datetime) -> BillingNoticeOutcome:
        seen.append(candidate.subject_id)
        return BillingNoticeOutcome.CREATED

    call_count = {"n": 0}
    real_kind = subscription_notice_kind

    def first_none_then_real(state: str, period_end: datetime, now: datetime) -> BillingNoticeKind | None:
        call_count["n"] += 1
        if call_count["n"] == 1:
            return None
        return real_kind(state, period_end, now)

    monkeypatch.setattr(billing_notice_store, "subscription_notice_kind", first_none_then_real)
    monkeypatch.setattr(billing_notice_store.SqlBillingNoticeStore, "enqueue_if_due", fake_enqueue)

    store = billing_notice_store.SqlBillingNoticeStore(session)  # type: ignore[arg-type]
    result = BillingNoticeSweep(store, store).run_once(
        NOW, limit=2, source=BillingNoticeSource.SUBSCRIPTIONS
    )

    assert session.rolled_back is True
    assert seen == ["sub-valid"]
    assert result.scanned == 2
    assert result.failed == 1
    assert result.created == 1
    assert result.next_cursor is not None
    assert decode_scan_cursor(result.next_cursor) == BillingNoticeScanCursor(
        BillingNoticeSource.SUBSCRIPTIONS,
        NOW + timedelta(days=7),
        "sub-valid",
    )


def test_run_billing_notice_pages_paginates_both_sources_and_enforces_max_pages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """covers: IMPL_REVIEW_E_E4_R1_20261125.md Conformance (E4_PROMPT §3 D9 run_billing_notice_pages)"""
    class _SessionCtx:
        def __init__(self, marker: int) -> None:
            self.marker = marker

        def __enter__(self) -> _SessionCtx:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

    created_sessions = 0

    def session_factory() -> _SessionCtx:
        nonlocal created_sessions
        created_sessions += 1
        return _SessionCtx(created_sessions)

    for bad_max in (0, 21, True):
        with pytest.raises(ValueError, match="max_pages"):
            worker.run_billing_notice_pages(
                session_factory,  # type: ignore[arg-type]
                now=NOW,
                batch_size=10,
                max_pages=bad_max,  # type: ignore[arg-type]
            )

    sub_cursor_1 = encode_scan_cursor(
        BillingNoticeScanCursor(BillingNoticeSource.SUBSCRIPTIONS, NOW, "sub-1")
    )
    sub_cursor_2 = encode_scan_cursor(
        BillingNoticeScanCursor(BillingNoticeSource.SUBSCRIPTIONS, NOW, "sub-2")
    )
    calls: list[tuple[BillingNoticeSource, str | None]] = []

    class _FakeSweep:
        def run_once(
            self, *, now: datetime, limit: int, cursor: str | None, source: BillingNoticeSource
        ) -> BillingNoticeSweepResult:
            assert now == NOW and limit == 10
            calls.append((source, cursor))
            if source is BillingNoticeSource.SUBSCRIPTIONS:
                if cursor is None:
                    return BillingNoticeSweepResult(2, 1, 1, 0, 0, 0, sub_cursor_1)
                return BillingNoticeSweepResult(1, 0, 0, 1, 0, 0, sub_cursor_2)
            return BillingNoticeSweepResult(2, 1, 0, 0, 1, 0, None)

    monkeypatch.setattr(worker, "build_billing_notice_sweep", lambda _session: _FakeSweep())

    totals = worker.run_billing_notice_pages(
        session_factory,  # type: ignore[arg-type]
        now=NOW,
        batch_size=10,
        max_pages=2,
    )

    assert created_sessions == 3
    assert calls == [
        (BillingNoticeSource.SUBSCRIPTIONS, None),
        (BillingNoticeSource.SUBSCRIPTIONS, sub_cursor_1),
        (BillingNoticeSource.PAYMENTS, None),
    ]
    assert totals == {
        "scanned": 5,
        "created": 2,
        "already_present": 1,
        "skipped_stale": 1,
        "no_recipient": 1,
        "failed": 0,
    }


@pytest.mark.parametrize(
    "argv",
    [
        ["billing-notices", "--once", "--batch-size", "0"],
        ["billing-notices", "--once", "--batch-size", "501"],
        ["billing-notices", "--once", "--max-pages", "0"],
        ["billing-notices", "--once", "--max-pages", "21"],
    ],
)
def test_billing_notice_cli_rejects_out_of_range_batch_and_page_limits(argv: list[str]) -> None:
    """covers: IMPL_REVIEW_E_E4_R1_20261125.md Conformance (E4_PROMPT §3 D9 CLI bounds)"""
    with pytest.raises(SystemExit) as exc_info:
        worker._parser().parse_args(argv)
    assert exc_info.value.code == 2


def test_billing_notice_worker_busy_lock_and_non_utc_now_refusal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """covers: IMPL_REVIEW_E_E4_R1_20261125.md Conformance (E4_PROMPT §3 D9 lock & UTC refusal)"""
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setattr(
        worker,
        "create_core_engine",
        lambda: (_ for _ in ()).throw(AssertionError("engine must not be created")),
    )
    assert worker.main(["billing-notices", "--once", "--now", "2026-11-25T19:00:00+07:00"]) == 2

    class _BusyConn:
        def __init__(self) -> None:
            self.closed = False

        def execution_options(self, **_kwargs: Any) -> _BusyConn:
            return self

        def scalar(self, *_args: Any, **_kwargs: Any) -> bool:
            return False

        def close(self) -> None:
            self.closed = True

    class _BusyEngine:
        def __init__(self) -> None:
            self.conn = _BusyConn()

        def connect(self) -> _BusyConn:
            return self.conn

    engine = _BusyEngine()
    monkeypatch.setattr(
        worker,
        "run_billing_notice_pages",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("busy lock ran pages")),
    )
    report = worker.run_pass_locked(
        engine,  # type: ignore[arg-type]
        object(),  # type: ignore[arg-type]
        mode="billing-notices",
        batch_size=50,
        now=NOW,
    )
    assert report.lock_busy is True
    assert report.counts == worker._empty_counts("billing-notices")
    assert engine.conn.closed is True
