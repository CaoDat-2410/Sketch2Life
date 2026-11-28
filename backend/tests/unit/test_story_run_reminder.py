"""Pure rules and bounded sweep behavior for FEAT-066 T-1d2."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta, timezone

import pytest

from sketch2life.application.ports.story_run_reminder import (
    ReminderCandidate,
    ReminderCandidatePage,
    ReminderOutcome,
    ReminderScanCursor,
)
from sketch2life.application.services.story_run_reminder import (
    DEFAULT_BATCH_SIZE,
    MAX_BATCH_SIZE,
    ReminderSweep,
    decode_scan_cursor,
    encode_scan_cursor,
    reminder_command,
)
from sketch2life.domain.story_run_closeout import ACTIVE_JOB_STATES, ADULT_WAIT_STATES, idle_since
from sketch2life.domain.story_run_reminder import (
    REMINDER_DELAY,
    canonical_deadline,
    reminder_deadline,
    reminder_due,
    reminder_trigger_id,
    require_aware_utc,
)

NOW = datetime(2026, 11, 25, 12, 0, tzinfo=UTC)


@dataclass
class FakeSweepStore:
    page: ReminderCandidatePage = field(
        default_factory=lambda: ReminderCandidatePage(candidates=(), has_more=False)
    )
    outcomes: dict[str, ReminderOutcome | Exception] = field(default_factory=dict)
    scans: list[tuple[datetime, int, ReminderScanCursor | None]] = field(default_factory=list)
    processed: list[tuple[ReminderCandidate, datetime]] = field(default_factory=list)

    def scan_candidates(
        self, now: datetime, limit: int, cursor: ReminderScanCursor | None
    ) -> ReminderCandidatePage:
        self.scans.append((now, limit, cursor))
        return self.page

    def enqueue_if_due(self, candidate: ReminderCandidate, now: datetime) -> ReminderOutcome:
        self.processed.append((candidate, now))
        outcome = self.outcomes.get(candidate.run_id, ReminderOutcome.CREATED)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def candidate(run_id: str, index: int, *, since: datetime | None = None) -> ReminderCandidate:
    return ReminderCandidate(
        run_id=run_id,
        run_state="SCRIPT_REVIEW",
        revision=index + 1,
        owner_account_id=f"parent-{index}",
        wait_since=since or NOW - REMINDER_DELAY,
    )


def test_reminder_is_not_due_at_143h59m59s_and_is_due_at_144h() -> None:
    since = NOW - REMINDER_DELAY + timedelta(seconds=1)
    assert not reminder_due("SCRIPT_REVIEW", "SUCCEEDED", since, NOW)
    assert reminder_due("SCRIPT_REVIEW", "SUCCEEDED", NOW - REMINDER_DELAY, NOW)


def test_all_adult_wait_states_are_eligible_without_work() -> None:
    since = NOW - REMINDER_DELAY
    for state in ADULT_WAIT_STATES:
        assert reminder_due(state, None, since, NOW), state
        if state != "INPUT_PROCESSING":
            assert reminder_due(state, "FAILED", since, NOW), state
        for job_state in ACTIVE_JOB_STATES:
            assert not reminder_due(state, job_state, since, NOW), (state, job_state)
        assert not reminder_due(state, None, since, NOW, open_generation=True), state


def test_draft_like_input_processing_excludes_job_and_pending_transcript() -> None:
    since = NOW - REMINDER_DELAY
    assert reminder_due("INPUT_PROCESSING", None, since, NOW)
    assert not reminder_due("INPUT_PROCESSING", "SUCCEEDED", since, NOW)
    assert not reminder_due("INPUT_PROCESSING", None, since, NOW, transcript_pending=True)
    assert not reminder_due("VIDEO_ADMISSION_PENDING", None, since, NOW)


def test_latest_meaningful_marker_sets_the_deadline_and_polling_does_not() -> None:
    updated = NOW - timedelta(hours=300)
    wait_started = NOW - timedelta(hours=200)
    activity = NOW - timedelta(hours=143, minutes=59, seconds=1)
    since = idle_since(updated, wait_started, activity)
    assert since == activity
    assert not reminder_due("SCRIPT_REVIEW", "SUCCEEDED", since, NOW)
    assert reminder_due("SCRIPT_REVIEW", "SUCCEEDED", since, NOW + timedelta(seconds=59))
    # A poll/read has no marker to feed into idle_since, so its dedupe identity remains stable.
    assert reminder_trigger_id("run-1", "SCRIPT_REVIEW", since) == reminder_trigger_id(
        "run-1", "SCRIPT_REVIEW", idle_since(updated, wait_started, activity)
    )


def test_trigger_uses_compact_utc_microseconds_and_exact_state() -> None:
    since = datetime(2026, 1, 2, 3, 4, 5, 123456, tzinfo=UTC)
    deadline = reminder_deadline(since)
    canonical = json.dumps(
        ["run-1", "SCRIPT_REVIEW", "2026-01-08T03:04:05.123456Z"],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    expected = "run-reminder." + hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    assert canonical_deadline(deadline) == "2026-01-08T03:04:05.123456Z"
    assert reminder_trigger_id("run-1", "SCRIPT_REVIEW", since) == expected
    assert reminder_trigger_id("run-1", "VIDEO_READY", since) != expected
    assert (
        reminder_trigger_id("run-1", "SCRIPT_REVIEW", since + timedelta(microseconds=1))
        != expected
    )


def test_meaningful_activity_starts_a_new_key_but_a_poll_does_not() -> None:
    original = NOW - REMINDER_DELAY
    meaningful_command = original + timedelta(minutes=10)
    first = reminder_trigger_id("run-2", "SCRIPT_REVIEW", original)
    after_poll = reminder_trigger_id("run-2", "SCRIPT_REVIEW", original)
    after_command = reminder_trigger_id("run-2", "SCRIPT_REVIEW", meaningful_command)
    assert first == after_poll
    assert first != after_command


def test_same_run_state_and_timestamp_reuse_the_same_key_until_generation_exists() -> None:
    # This pins the current no-DDL identity and documents the production gate in the domain module.
    wait_since = NOW - REMINDER_DELAY
    assert reminder_trigger_id("run-3", "SCRIPT_REVIEW", wait_since) == reminder_trigger_id(
        "run-3", "SCRIPT_REVIEW", wait_since
    )


def test_command_has_empty_safe_parameters_and_no_display_content() -> None:
    command = reminder_command(
        recipient_account_id="12345678-1234-1234-1234-123456789abc",
        run_id="run-with-child-data-kept-private",
        run_state="SCRIPT_REVIEW",
        wait_since=NOW - REMINDER_DELAY,
    )
    assert command.recipient_role == "parent"
    assert command.notification_type == "RUN_WAIT_REMINDER"
    assert command.template_version == 1
    assert command.safe_parameters == {}
    assert command.organization_ref is None
    assert command.expires_at is None
    assert command.trigger_id == command.dedupe_key
    assert "run-with-child-data-kept-private" not in command.trigger_id


def test_internal_cursor_roundtrips_and_rejects_noncanonical_values() -> None:
    original = ReminderScanCursor(wait_since=NOW - REMINDER_DELAY, run_id="run-9")
    encoded = encode_scan_cursor(original)
    assert decode_scan_cursor(encoded) == original
    for invalid in ("", "%%%", "e30", "eyJ1bnN1cHBvcnRlZCI6dHJ1ZX0"):
        with pytest.raises(ValueError):
            decode_scan_cursor(invalid)


def test_sweep_advances_cursor_past_existing_rows_and_uses_one_injected_instant() -> None:
    rows = (candidate("a", 0), candidate("b", 1), candidate("c", 2))
    store = FakeSweepStore(
        page=ReminderCandidatePage(candidates=rows[:2], has_more=True),
        outcomes={"a": ReminderOutcome.ALREADY_PRESENT, "b": ReminderOutcome.CREATED},
    )
    report = ReminderSweep(store, store).run_once(NOW, limit=2)
    assert (report.scanned, report.created, report.already_present) == (2, 1, 1)
    assert report.skipped_stale == report.failed == 0
    assert decode_scan_cursor(report.next_cursor or "") == rows[1].cursor
    assert store.scans == [(NOW, 2, None)]
    assert all(instant == NOW for _, instant in store.processed)


def test_one_transaction_failure_does_not_stop_the_batch() -> None:
    rows = (candidate("broken", 0), candidate("good", 1))
    store = FakeSweepStore(
        page=ReminderCandidatePage(candidates=rows, has_more=False),
        outcomes={"broken": RuntimeError("synthetic storage failure")},
    )
    report = ReminderSweep(store, store).run_once(NOW)
    assert (report.scanned, report.created, report.failed) == (2, 1, 1)
    assert [row.run_id for row, _ in store.processed] == ["broken", "good"]


def test_sweep_counts_stale_rows_and_does_not_call_external_delivery() -> None:
    row = candidate("stale", 0)
    store = FakeSweepStore(
        page=ReminderCandidatePage(candidates=(row,), has_more=False),
        outcomes={"stale": ReminderOutcome.STALE},
    )
    report = ReminderSweep(store, store).run_once(NOW)
    assert report.skipped_stale == 1
    # The application sweep has only scan and transaction ports; delivery has no adapter here.
    assert not hasattr(ReminderSweep, "send_push")
    assert not hasattr(ReminderSweep, "send_email")


def test_clock_limit_and_result_boundaries_are_validated() -> None:
    store = FakeSweepStore()
    report = ReminderSweep(store, store, clock=lambda: NOW).run_once()
    assert report.scanned == 0 and store.scans[0][1] == DEFAULT_BATCH_SIZE
    for limit in (0, -1, MAX_BATCH_SIZE + 1, True):
        with pytest.raises(ValueError):
            ReminderSweep(store, store).run_once(NOW, limit=limit)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        ReminderSweep(store, store).run_once(datetime(2026, 11, 25, 12, 0))


def test_stored_non_utc_instants_normalize_to_the_same_identity_and_due_result() -> None:
    since_utc = datetime(2026, 11, 20, 3, 0, 0, 123456, tzinfo=UTC)
    since_local = since_utc.astimezone(timezone(timedelta(hours=7)))
    assert since_local.utcoffset() == timedelta(hours=7)
    assert reminder_trigger_id("run-1", "SCRIPT_REVIEW", since_local) == reminder_trigger_id(
        "run-1", "SCRIPT_REVIEW", since_utc
    )
    assert canonical_deadline(since_local) == canonical_deadline(since_utc)
    now = since_utc + REMINDER_DELAY
    assert reminder_due("SCRIPT_REVIEW", "SUCCEEDED", since_local, now)
    assert not reminder_due(
        "SCRIPT_REVIEW", "SUCCEEDED", since_local, now - timedelta(microseconds=1)
    )
    cursor = ReminderScanCursor(wait_since=since_local, run_id="run-1")
    assert decode_scan_cursor(encode_scan_cursor(cursor)).wait_since == since_utc


def test_the_injected_now_stays_strictly_aware_utc() -> None:
    since = datetime(2026, 11, 20, tzinfo=UTC)
    local_now = (since + REMINDER_DELAY).astimezone(timezone(timedelta(hours=7)))
    with pytest.raises(ValueError, match="UTC"):
        reminder_due("SCRIPT_REVIEW", "SUCCEEDED", since, local_now)
    with pytest.raises(ValueError, match="aware"):
        require_aware_utc(datetime(2026, 11, 20))
