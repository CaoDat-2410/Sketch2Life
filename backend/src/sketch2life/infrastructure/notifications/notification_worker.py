"""Locally clocked reminder and fake push-delivery worker commands (T-NTF1)."""

from __future__ import annotations

import argparse
import logging
import os
import signal
import sys
import threading
from collections.abc import Callable, Mapping, Sequence
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import FrameType

from sqlalchemy import Engine, text
from sqlalchemy.orm import Session, sessionmaker

from sketch2life.application.ports.push_delivery import PushSenderPort, PushSenderUnavailable
from sketch2life.application.services.billing_notice import (
    DEFAULT_BATCH_SIZE as BILLING_DEFAULT_BATCH_SIZE,
)
from sketch2life.application.services.billing_notice import (
    MAX_BATCH_SIZE as BILLING_MAX_BATCH_SIZE,
)
from sketch2life.application.services.push_delivery import (
    DEFAULT_BATCH_SIZE,
    MAX_BATCH_SIZE,
    PushDeliveryReport,
    PushDeliveryWorker,
)
from sketch2life.domain.billing_notice import BillingNoticeSource
from sketch2life.domain.story_run_reminder import require_aware_utc
from sketch2life.infrastructure.notifications.billing_notice_store import (
    build_billing_notice_sweep,
)
from sketch2life.infrastructure.notifications.push_delivery_repository import SqlPushDeliveryStore
from sketch2life.infrastructure.persistence.database import (
    create_core_engine,
    create_core_session_factory,
)
from sketch2life.infrastructure.story_video.reminder_store import build_story_run_reminder

_LOG = logging.getLogger(__name__)
LOCK_NAMES: Mapping[str, str] = {
    "reminders": "sketch2life.reminder-sweep.v1",
    "billing-notices": "sketch2life.billing-notices.v1",
    "push-delivery": "sketch2life.push-delivery.v1",
}
DEFAULT_MAX_PAGES = 5
DEFAULT_INTERVAL_SECONDS = 30


@dataclass(frozen=True, slots=True)
class WorkerPassReport:
    mode: str
    counts: Mapping[str, int]
    lock_busy: bool = False
    errors: int = 0


def build_push_sender(env: str | None = None) -> PushSenderPort:
    """Build only the synthetic sender in local/test; no production adapter exists in this slice."""

    environment = (os.environ.get("SKETCH2LIFE_ENV", "") if env is None else env).lower()
    if environment not in {"local", "test"}:
        raise PushSenderUnavailable("push sender is unavailable outside local/test")
    from sketch2life.infrastructure.notifications.push_delivery_fakes import LocalFakePushSender

    return LocalFakePushSender(env=environment)


def parse_utc_now(value: str) -> datetime:
    """Parse an aware UTC ISO timestamp; naive and non-UTC clocks are refused."""

    raw = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError("now must be an aware UTC ISO timestamp") from exc
    return require_aware_utc(parsed, field="now")


def run_reminder_pages(
    session_factory: sessionmaker[Session],
    *,
    now: datetime,
    batch_size: int,
    max_pages: int,
) -> dict[str, int]:
    """Run bounded T-1d2 pages, opening a fresh database session for each page."""

    if type(max_pages) is not int or not 1 <= max_pages <= 20:
        raise ValueError("max_pages must be between 1 and 20")
    totals = {
        "scanned": 0,
        "created": 0,
        "already_present": 0,
        "skipped_stale": 0,
        "failed": 0,
    }
    cursor: str | None = None
    for _ in range(max_pages):
        with session_factory() as session:
            result = build_story_run_reminder(session).run_once(
                now=now,
                limit=batch_size,
                cursor=cursor,
            )
        totals["scanned"] += result.scanned
        totals["created"] += result.created
        totals["already_present"] += result.already_present
        totals["skipped_stale"] += result.skipped_stale
        totals["failed"] += result.failed
        cursor = result.next_cursor
        if cursor is None:
            break
    return totals


def run_billing_notice_pages(
    session_factory: sessionmaker[Session],
    *,
    now: datetime,
    batch_size: int,
    max_pages: int,
) -> dict[str, int]:
    """Run bounded pages per Billing source, opening a fresh session for each page."""

    if type(max_pages) is not int or not 1 <= max_pages <= 20:
        raise ValueError("max_pages must be between 1 and 20")
    totals = {
        "scanned": 0,
        "created": 0,
        "already_present": 0,
        "skipped_stale": 0,
        "no_recipient": 0,
        "failed": 0,
    }
    for source in BillingNoticeSource:
        cursor: str | None = None
        for _ in range(max_pages):
            with session_factory() as session:
                result = build_billing_notice_sweep(session).run_once(
                    now=now,
                    limit=batch_size,
                    cursor=cursor,
                    source=source,
                )
            totals["scanned"] += result.scanned
            totals["created"] += result.created
            totals["already_present"] += result.already_present
            totals["skipped_stale"] += result.skipped_stale
            totals["no_recipient"] += result.no_recipient
            totals["failed"] += result.failed
            cursor = result.next_cursor
            if cursor is None:
                break
    return totals


def run_push_delivery(
    session_factory: sessionmaker[Session],
    sender: PushSenderPort,
    *,
    now: datetime,
    batch_size: int,
) -> PushDeliveryReport:
    """Run one enrollment/delivery batch using the local fake sender composition."""

    with session_factory() as session:
        worker = PushDeliveryWorker(SqlPushDeliveryStore(session), sender)
        return worker.run_once(now=now, batch=batch_size)


def _empty_counts(mode: str) -> dict[str, int]:
    if mode == "reminders":
        return {
            "scanned": 0,
            "created": 0,
            "already_present": 0,
            "skipped_stale": 0,
            "failed": 0,
        }
    if mode == "billing-notices":
        return {
            "scanned": 0,
            "created": 0,
            "already_present": 0,
            "skipped_stale": 0,
            "no_recipient": 0,
            "failed": 0,
        }
    return {
        "enrolled": 0,
        "claimed": 0,
        "sent": 0,
        "retry": 0,
        "failed": 0,
        "dead_endpoint": 0,
        "skipped": 0,
    }


def run_pass_locked(
    engine: Engine,
    session_factory: sessionmaker[Session],
    *,
    mode: str,
    batch_size: int,
    max_pages: int = DEFAULT_MAX_PAGES,
    sender: PushSenderPort | None = None,
    now: datetime | None = None,
    clock: Callable[[], datetime] | None = None,
) -> WorkerPassReport:
    """Run one counts-only pass under the mode-specific advisory lock."""

    if mode not in LOCK_NAMES:
        raise ValueError("unknown notification worker mode")
    connection = engine.connect()
    try:
        connection = connection.execution_options(isolation_level="AUTOCOMMIT")
        acquired = connection.scalar(
            text("SELECT pg_try_advisory_lock(hashtextextended(:name, 0))"),
            {"name": LOCK_NAMES[mode]},
        )
        if acquired is not True:
            return WorkerPassReport(mode=mode, counts=_empty_counts(mode), lock_busy=True)
        try:
            instant = require_aware_utc(
                now if now is not None else (clock or (lambda: datetime.now(UTC)))(),
                field="now",
            )
            if mode == "reminders":
                counts = run_reminder_pages(
                    session_factory,
                    now=instant,
                    batch_size=batch_size,
                    max_pages=max_pages,
                )
            elif mode == "billing-notices":
                counts = run_billing_notice_pages(
                    session_factory,
                    now=instant,
                    batch_size=batch_size,
                    max_pages=max_pages,
                )
            else:
                if sender is None:
                    raise PushSenderUnavailable("push sender is unavailable")
                counts = run_push_delivery(
                    session_factory,
                    sender,
                    now=instant,
                    batch_size=batch_size,
                ).as_counts()
            errors = int(counts.get("failed", 0) > 0)
            return WorkerPassReport(mode=mode, counts=counts, errors=errors)
        finally:
            try:
                released = connection.scalar(
                    text("SELECT pg_advisory_unlock(hashtextextended(:name, 0))"),
                    {"name": LOCK_NAMES[mode]},
                )
                if released is not True:
                    connection.invalidate()
            except Exception:
                with suppress(Exception):
                    connection.invalidate()
    finally:
        with suppress(Exception):
            connection.close()


def _log_report(report: WorkerPassReport) -> None:
    counts = "".join(f" {key}={value}" for key, value in report.counts.items())
    _LOG.info(
        "notification_worker_pass mode=%s lock_busy=%d errors=%d%s",
        report.mode,
        int(report.lock_busy),
        report.errors,
        counts,
    )


def _positive_int(low: int, high: int) -> Callable[[str], int]:
    def parse(raw: str) -> int:
        try:
            value = int(raw)
        except ValueError as exc:
            raise argparse.ArgumentTypeError("must be an integer") from exc
        if not low <= value <= high:
            raise argparse.ArgumentTypeError(f"must be between {low} and {high}")
        return value

    return parse


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run local notification sweeps")
    subparsers = parser.add_subparsers(dest="mode", required=True)
    for mode in ("reminders", "billing-notices", "push-delivery"):
        subparser = subparsers.add_parser(mode)
        subparser.add_argument("--once", action="store_true", help="run one pass and exit")
        batch_max = BILLING_MAX_BATCH_SIZE if mode == "billing-notices" else MAX_BATCH_SIZE
        batch_default = (
            BILLING_DEFAULT_BATCH_SIZE if mode == "billing-notices" else DEFAULT_BATCH_SIZE
        )
        subparser.add_argument(
            "--batch-size", type=_positive_int(1, batch_max), default=batch_default
        )
        subparser.add_argument("--now", default=None, help="aware UTC ISO clock for local/test")
        subparser.add_argument("--heartbeat-file", type=Path, default=None)
        if mode in {"reminders", "billing-notices"}:
            subparser.add_argument(
                "--max-pages", type=_positive_int(1, 20), default=DEFAULT_MAX_PAGES
            )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    environment = os.environ.get("SKETCH2LIFE_ENV", "").lower()
    if environment not in {"local", "test"}:
        _LOG.error("notification_worker_refused mode=%s reason=local_test_only", args.mode)
        return 2
    try:
        now = None if args.now is None else parse_utc_now(args.now)
    except ValueError:
        _LOG.error("notification_worker_refused mode=%s reason=invalid_now", args.mode)
        return 2
    try:
        sender = build_push_sender(environment) if args.mode == "push-delivery" else None
    except PushSenderUnavailable:
        _LOG.error("notification_worker_refused mode=%s reason=sender_unavailable", args.mode)
        return 2

    try:
        engine = create_core_engine()
        session_factory = create_core_session_factory(engine)
    except Exception:
        _LOG.error("notification_worker_start_failed errors=1")
        return 1

    def beat() -> None:
        if args.heartbeat_file is not None:
            with suppress(Exception):
                args.heartbeat_file.touch()

    def run_pass() -> WorkerPassReport:
        return run_pass_locked(
            engine,
            session_factory,
            mode=args.mode,
            batch_size=args.batch_size,
            max_pages=getattr(args, "max_pages", DEFAULT_MAX_PAGES),
            sender=sender,
            now=now,
        )

    try:
        if args.once:
            try:
                report = run_pass()
            except Exception:
                _LOG.error("notification_worker_pass_failed mode=%s errors=1", args.mode)
                return 1
            _log_report(report)
            if report.errors == 0:
                beat()
            return 1 if report.errors else 0

        stop = threading.Event()

        def request_stop(_signal: int, _frame: FrameType | None) -> None:
            stop.set()

        signal.signal(signal.SIGTERM, request_stop)
        signal.signal(signal.SIGINT, request_stop)
        had_errors = False
        while not stop.is_set():
            try:
                report = run_pass()
            except Exception:
                _LOG.error("notification_worker_pass_failed mode=%s errors=1", args.mode)
                had_errors = True
            else:
                _log_report(report)
                had_errors = had_errors or report.errors > 0
                if report.errors == 0:
                    beat()
            if stop.wait(DEFAULT_INTERVAL_SECONDS):
                break
        return 1 if had_errors else 0
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
