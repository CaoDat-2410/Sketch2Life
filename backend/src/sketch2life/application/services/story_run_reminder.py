"""Bounded application sweep for internal adult-wait inbox reminders (T-1d2).

This service has no scheduler, HTTP route, delivery adapter or child-facing copy. Production
composition stays empty until an approved client template and scheduler integration exist.
"""

from __future__ import annotations

import base64
import binascii
import json
import re
from collections.abc import Callable
from datetime import UTC, datetime

from sketch2life.application.ports.notifications import NotificationCommandV1
from sketch2life.application.ports.story_run_reminder import (
    ReminderOutcome,
    ReminderScanCursor,
    ReminderScanPort,
    ReminderSweepResult,
    ReminderTransactionPort,
)
from sketch2life.domain.story_run_reminder import (
    REMINDER_NOTIFICATION_TYPE,
    REMINDER_TEMPLATE_VERSION,
    canonical_deadline,
    reminder_trigger_id,
    require_aware_utc,
)

Clock = Callable[[], datetime]
DEFAULT_BATCH_SIZE = 50
MAX_BATCH_SIZE = 500
_CURSOR_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,1024}$", re.ASCII)


def utc_now() -> datetime:
    return datetime.now(UTC)


def encode_scan_cursor(cursor: ReminderScanCursor) -> str:
    """Encode the internal keyset as canonical, opaque base64url JSON."""

    if not cursor.run_id:
        raise ValueError("cursor run_id must not be empty")
    payload = json.dumps(
        [canonical_deadline(cursor.wait_since), cursor.run_id],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii").rstrip("=")


def decode_scan_cursor(token: str) -> ReminderScanCursor:
    """Validate and decode a cursor from the trusted in-process scheduler boundary."""

    if not isinstance(token, str) or _CURSOR_PATTERN.fullmatch(token) is None:
        raise ValueError("invalid reminder cursor")
    padded = token + "=" * (-len(token) % 4)
    try:
        raw = base64.b64decode(padded, altchars=b"-_", validate=True)
        payload = json.loads(raw.decode("utf-8"))
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid reminder cursor") from exc
    if (
        not isinstance(payload, list)
        or len(payload) != 2
        or not isinstance(payload[0], str)
        or not isinstance(payload[1], str)
        or not payload[1]
        or not payload[0].endswith("Z")
    ):
        raise ValueError("invalid reminder cursor")
    try:
        wait_since = datetime.fromisoformat(payload[0][:-1] + "+00:00")
        wait_since = require_aware_utc(wait_since, field="cursor wait_since")
    except ValueError as exc:
        raise ValueError("invalid reminder cursor") from exc
    cursor = ReminderScanCursor(wait_since=wait_since, run_id=payload[1])
    if encode_scan_cursor(cursor) != token:
        raise ValueError("noncanonical reminder cursor")
    return cursor


def reminder_command(
    *, recipient_account_id: str, run_id: str, run_state: str, wait_since: datetime
) -> NotificationCommandV1:
    """Build the safe T-8a inbox command; the trigger carries no plaintext run or child data."""

    trigger_id = reminder_trigger_id(run_id, run_state, wait_since)
    return NotificationCommandV1(
        recipient_account_id=recipient_account_id,
        recipient_role="parent",
        notification_type=REMINDER_NOTIFICATION_TYPE,
        template_version=REMINDER_TEMPLATE_VERSION,
        trigger_id=trigger_id,
        dedupe_key=trigger_id,
        safe_parameters={},
        organization_ref=None,
        expires_at=None,
    )


class ReminderSweep:
    """Run one bounded page and isolate each candidate's short transaction."""

    def __init__(
        self,
        scanner: ReminderScanPort,
        transactions: ReminderTransactionPort,
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
    ) -> ReminderSweepResult:
        """Process one page; callers resume ``next_cursor`` until a pass is exhausted."""

        if type(limit) is not int or not 1 <= limit <= MAX_BATCH_SIZE:
            raise ValueError(f"limit must be between 1 and {MAX_BATCH_SIZE}")
        instant = require_aware_utc(self._clock() if now is None else now, field="now")
        decoded_cursor = None if cursor is None else decode_scan_cursor(cursor)
        page = self._scanner.scan_candidates(instant, limit, decoded_cursor)
        if len(page.candidates) > limit:
            raise ValueError("reminder scanner exceeded the requested limit")
        if page.has_more and not page.candidates:
            raise ValueError("reminder scanner returned an empty nonterminal page")

        created = already_present = skipped_stale = failed = 0
        for candidate in page.candidates:
            try:
                outcome = self._transactions.enqueue_if_due(candidate, instant)
            except Exception:
                # Per-run rollback belongs to the transaction adapter. Do not log an exception:
                # storage errors and candidate details can include identifiers or content.
                failed += 1
                continue
            if outcome is ReminderOutcome.CREATED:
                created += 1
            elif outcome is ReminderOutcome.ALREADY_PRESENT:
                already_present += 1
            elif outcome is ReminderOutcome.STALE:
                skipped_stale += 1
            else:  # defensive for an adapter added without updating this contract
                failed += 1

        next_cursor = (
            encode_scan_cursor(page.candidates[-1].cursor)
            if page.has_more and page.candidates
            else None
        )
        return ReminderSweepResult(
            scanned=len(page.candidates),
            created=created,
            already_present=already_present,
            skipped_stale=skipped_stale,
            failed=failed,
            next_cursor=next_cursor,
        )


__all__ = [
    "DEFAULT_BATCH_SIZE",
    "MAX_BATCH_SIZE",
    "ReminderSweep",
    "decode_scan_cursor",
    "encode_scan_cursor",
    "reminder_command",
    "utc_now",
]
