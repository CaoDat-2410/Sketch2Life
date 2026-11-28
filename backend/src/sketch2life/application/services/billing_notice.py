"""Bounded, provider-free billing notice sweep and inbox command builders (T-BILLN1)."""

from __future__ import annotations

import base64
import binascii
import json
import re
from collections.abc import Callable
from datetime import UTC, datetime

from sketch2life.application.ports.billing_notice import (
    BillingNoticeOutcome,
    BillingNoticeScanCursor,
    BillingNoticeScanPort,
    BillingNoticeSweepResult,
    BillingNoticeTransactionPort,
)
from sketch2life.application.ports.notifications import NotificationCommandV1
from sketch2life.domain.billing_notice import (
    BILLING_GRACE_EXPIRED,
    BILLING_ORG_PAYMENT_FAILED,
    BILLING_ORG_PAYMENT_SUCCEEDED,
    BILLING_PARENT_PAYMENT_FAILED,
    BILLING_PARENT_PAYMENT_SUCCEEDED,
    BILLING_RENEWAL_DUE_1D,
    BILLING_RENEWAL_DUE_7D,
    BILLING_TEMPLATE_VERSION,
    BillingNoticeKind,
    BillingNoticeSource,
    billing_notice_local_date,
    billing_notice_trigger_id,
    canonical_utc,
    require_aware_utc,
)

Clock = Callable[[], datetime]
DEFAULT_BATCH_SIZE = 50
MAX_BATCH_SIZE = 500
_CURSOR_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,1024}$", re.ASCII)


def utc_now() -> datetime:
    return datetime.now(UTC)


def encode_scan_cursor(cursor: BillingNoticeScanCursor) -> str:
    """Encode a source-specific keyset as canonical opaque base64url JSON."""

    if not cursor.candidate_id:
        raise ValueError("cursor candidate_id must not be empty")
    payload = json.dumps(
        [cursor.source.value, canonical_utc(cursor.timestamp), cursor.candidate_id],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii").rstrip("=")


def decode_scan_cursor(token: str) -> BillingNoticeScanCursor:
    """Validate and decode the trusted in-process scheduler cursor."""

    if not isinstance(token, str) or _CURSOR_PATTERN.fullmatch(token) is None:
        raise ValueError("invalid billing notice cursor")
    padded = token + "=" * (-len(token) % 4)
    try:
        raw = base64.b64decode(padded, altchars=b"-_", validate=True)
        payload = json.loads(raw.decode("utf-8"))
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid billing notice cursor") from exc
    if (
        not isinstance(payload, list)
        or len(payload) != 3
        or not isinstance(payload[0], str)
        or not isinstance(payload[1], str)
        or not isinstance(payload[2], str)
        or not payload[2]
        or not payload[1].endswith("Z")
    ):
        raise ValueError("invalid billing notice cursor")
    try:
        source = BillingNoticeSource(payload[0])
        timestamp = datetime.fromisoformat(payload[1][:-1] + "+00:00")
        timestamp = require_aware_utc(timestamp, field="cursor timestamp")
    except ValueError as exc:
        raise ValueError("invalid billing notice cursor") from exc
    cursor = BillingNoticeScanCursor(source, timestamp, payload[2])
    if encode_scan_cursor(cursor) != token:
        raise ValueError("noncanonical billing notice cursor")
    return cursor


def subscription_notice_command(
    *,
    recipient_account_id: str,
    organization_ref: str,
    kind: BillingNoticeKind,
    subscription_id: str,
    period_end: datetime,
) -> NotificationCommandV1:
    """Build a minimal school-manager command for one subscription period notice."""

    notification_type = {
        BillingNoticeKind.RENEWAL_7D: BILLING_RENEWAL_DUE_7D,
        BillingNoticeKind.RENEWAL_1D: BILLING_RENEWAL_DUE_1D,
        BillingNoticeKind.GRACE_EXPIRED: BILLING_GRACE_EXPIRED,
    }.get(kind)
    if notification_type is None:
        raise ValueError("subscription command requires a subscription notice kind")
    trigger_id = billing_notice_trigger_id(kind, subscription_id, period_end=period_end)
    return NotificationCommandV1(
        recipient_account_id=recipient_account_id,
        recipient_role="school_manager",
        notification_type=notification_type,
        template_version=BILLING_TEMPLATE_VERSION,
        trigger_id=trigger_id,
        dedupe_key=trigger_id,
        safe_parameters={
            "subscription_ref": subscription_id,
            "due_local_date": billing_notice_local_date(kind, period_end),
        },
        organization_ref=organization_ref,
        expires_at=None,
    )


def payment_notice_command(
    *,
    recipient_account_id: str,
    owner_kind: str,
    owner_ref: str,
    kind: BillingNoticeKind,
    invoice_id: str,
    payment_event_id: str,
) -> NotificationCommandV1:
    """Build a role-scoped, content-free command for one verified payment event."""

    if owner_kind == "ORGANIZATION":
        notification_type = {
            BillingNoticeKind.PAYMENT_SUCCEEDED: BILLING_ORG_PAYMENT_SUCCEEDED,
            BillingNoticeKind.PAYMENT_FAILED: BILLING_ORG_PAYMENT_FAILED,
        }.get(kind)
        recipient_role = "school_manager"
        organization_ref: str | None = owner_ref
    elif owner_kind == "PARENT_ACCOUNT":
        notification_type = {
            BillingNoticeKind.PAYMENT_SUCCEEDED: BILLING_PARENT_PAYMENT_SUCCEEDED,
            BillingNoticeKind.PAYMENT_FAILED: BILLING_PARENT_PAYMENT_FAILED,
        }.get(kind)
        recipient_role = "parent"
        organization_ref = None
    else:
        raise ValueError("unsupported payment owner kind")
    if notification_type is None:
        raise ValueError("payment command requires a payment notice kind")
    trigger_id = billing_notice_trigger_id(kind, payment_event_id)
    return NotificationCommandV1(
        recipient_account_id=recipient_account_id,
        recipient_role=recipient_role,
        notification_type=notification_type,
        template_version=BILLING_TEMPLATE_VERSION,
        trigger_id=trigger_id,
        dedupe_key=trigger_id,
        safe_parameters={"invoice_ref": invoice_id},
        organization_ref=organization_ref,
        expires_at=None,
    )


class BillingNoticeSweep:
    """Process one bounded source page and isolate each candidate transaction."""

    def __init__(
        self,
        scanner: BillingNoticeScanPort,
        transactions: BillingNoticeTransactionPort,
        *,
        clock: Clock = utc_now,
    ) -> None:
        self._scanner = scanner
        self._transactions = transactions
        self._clock = clock

    def run_once(
        self,
        now: datetime | None = None,
        limit: int = DEFAULT_BATCH_SIZE,
        cursor: str | None = None,
        *,
        source: BillingNoticeSource | str,
    ) -> BillingNoticeSweepResult:
        """Process a source page; callers resume ``next_cursor`` until it is exhausted."""

        if type(limit) is not int or not 1 <= limit <= MAX_BATCH_SIZE:
            raise ValueError(f"limit must be between 1 and {MAX_BATCH_SIZE}")
        instant = require_aware_utc(self._clock() if now is None else now, field="now")
        try:
            scan_source = BillingNoticeSource(source)
        except ValueError as exc:
            raise ValueError("invalid billing notice source") from exc
        decoded_cursor = None if cursor is None else decode_scan_cursor(cursor)
        if decoded_cursor is not None and decoded_cursor.source is not scan_source:
            raise ValueError("billing notice cursor source does not match the scan")
        page = self._scanner.scan_candidates(instant, scan_source, limit, decoded_cursor)
        if type(page.failed_count) is not int or page.failed_count < 0:
            raise ValueError("billing notice scanner returned an invalid failed count")
        scanned = len(page.candidates) + page.failed_count
        if scanned > limit:
            raise ValueError("billing notice scanner exceeded the requested limit")
        page_cursor = page.last_cursor
        if page_cursor is not None and page_cursor.source is not scan_source:
            raise ValueError("billing notice scanner returned a cursor for another source")
        if page_cursor is None and page.candidates and not page.failed_count:
            page_cursor = page.candidates[-1].cursor
        if page.failed_count and page_cursor is None:
            raise ValueError("billing notice scanner omitted the cursor for failed rows")
        if page.has_more and (scanned == 0 or page_cursor is None):
            raise ValueError("billing notice scanner returned an empty nonterminal page")
        if any(candidate.source is not scan_source for candidate in page.candidates):
            raise ValueError("billing notice scanner returned a candidate for another source")

        created = already_present = skipped_stale = no_recipient = 0
        failed = page.failed_count
        for candidate in page.candidates:
            try:
                outcome = self._transactions.enqueue_if_due(candidate, instant)
            except Exception:
                # Do not log storage exceptions or source/recipient identifiers.
                failed += 1
                continue
            if outcome is BillingNoticeOutcome.CREATED:
                created += 1
            elif outcome is BillingNoticeOutcome.ALREADY_PRESENT:
                already_present += 1
            elif outcome is BillingNoticeOutcome.STALE:
                skipped_stale += 1
            elif outcome is BillingNoticeOutcome.NO_RECIPIENT:
                no_recipient += 1
            else:
                failed += 1

        next_cursor = encode_scan_cursor(page_cursor) if page.has_more and page_cursor else None
        return BillingNoticeSweepResult(
            scanned=scanned,
            created=created,
            already_present=already_present,
            skipped_stale=skipped_stale,
            no_recipient=no_recipient,
            failed=failed,
            next_cursor=next_cursor,
        )


__all__ = [
    "DEFAULT_BATCH_SIZE",
    "MAX_BATCH_SIZE",
    "BillingNoticeSweep",
    "decode_scan_cursor",
    "encode_scan_cursor",
    "payment_notice_command",
    "subscription_notice_command",
    "utc_now",
]
