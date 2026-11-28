from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import pytest

from sketch2life.application.ports.push_delivery import PushSenderUnavailable
from sketch2life.infrastructure.notifications import notification_worker as worker


class _BusyConnection:
    def __init__(self) -> None:
        self.closed = False

    def execution_options(self, **_kwargs: Any) -> _BusyConnection:
        return self

    def scalar(self, *_args: Any, **_kwargs: Any) -> bool:
        return False

    def invalidate(self) -> None:
        raise AssertionError("a busy lock connection should not be invalidated")

    def close(self) -> None:
        self.closed = True


class _BusyEngine:
    def __init__(self) -> None:
        self.connection = _BusyConnection()
        self.disposed = False

    def connect(self) -> _BusyConnection:
        return self.connection

    def dispose(self) -> None:
        self.disposed = True


class _AvailableConnection(_BusyConnection):
    def __init__(self) -> None:
        super().__init__()
        self.calls = 0

    def scalar(self, *_args: Any, **_kwargs: Any) -> bool:
        self.calls += 1
        return True


class _AvailableEngine:
    def __init__(self) -> None:
        self.connection = _AvailableConnection()

    def connect(self) -> _AvailableConnection:
        return self.connection


class _DummyEngine:
    def __init__(self) -> None:
        self.disposed = False

    def dispose(self) -> None:
        self.disposed = True


@pytest.mark.parametrize("environment", ("", "production", "staging"))
def test_push_sender_fails_closed_outside_local_test(
    monkeypatch: pytest.MonkeyPatch, environment: str
) -> None:
    if environment:
        monkeypatch.setenv("SKETCH2LIFE_ENV", environment)
    else:
        monkeypatch.delenv("SKETCH2LIFE_ENV", raising=False)

    with pytest.raises(PushSenderUnavailable):
        worker.build_push_sender()


@pytest.mark.parametrize("environment", ("local", "test"))
def test_push_sender_is_the_local_fake_for_local_test_environments(
    monkeypatch: pytest.MonkeyPatch, environment: str
) -> None:
    monkeypatch.setenv("SKETCH2LIFE_ENV", environment)

    sender = worker.build_push_sender()

    assert type(sender).__name__ == "LocalFakePushSender"
    assert sender.test_only is True


def test_command_refuses_outside_local_test_and_now_is_also_refused(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setenv("SKETCH2LIFE_ENV", "production")
    caplog.set_level(logging.ERROR)

    status = worker.main(["push-delivery", "--once", "--now", "2026-11-25T12:00:00Z"])

    assert status == 2
    assert "notification_worker_refused" in caplog.text
    assert "local_test_only" in caplog.text


def test_naive_now_is_rejected_before_engine_creation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setattr(
        worker,
        "create_core_engine",
        lambda: (_ for _ in ()).throw(AssertionError("engine must not be created")),
    )

    assert worker.main(["reminders", "--once", "--now", "2026-11-25T12:00:00"]) == 2


def test_parse_now_requires_aware_utc() -> None:
    assert worker.parse_utc_now("2026-11-25T12:00:00Z") == datetime(2026, 11, 25, 12, 0, tzinfo=UTC)
    with pytest.raises(ValueError):
        worker.parse_utc_now("2026-11-25T12:00:00")
    with pytest.raises(ValueError):
        worker.parse_utc_now("2026-11-25T12:00:00+07:00")


def test_once_logs_one_counts_line_and_returns_success(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    engine = _DummyEngine()
    monkeypatch.setattr(worker, "create_core_engine", lambda: engine)
    monkeypatch.setattr(worker, "create_core_session_factory", lambda _engine: object())
    monkeypatch.setattr(
        worker,
        "run_pass_locked",
        lambda *_args, **_kwargs: worker.WorkerPassReport(
            mode="reminders",
            counts={
                "scanned": 3,
                "created": 1,
                "already_present": 1,
                "skipped_stale": 1,
                "failed": 0,
            },
        ),
    )
    caplog.set_level(logging.INFO)

    status = worker.main(["reminders", "--once", "--now", "2026-11-25T12:00:00Z"])

    assert status == 0
    assert "notification_worker_pass mode=reminders" in caplog.text
    assert "scanned=3 created=1 already_present=1 skipped_stale=1 failed=0" in caplog.text
    assert engine.disposed is True


def test_busy_lock_returns_zero_counts_without_running_work(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = _BusyEngine()
    monkeypatch.setattr(
        worker,
        "run_reminder_pages",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("busy lock did work")),
    )

    report = worker.run_pass_locked(
        engine,  # type: ignore[arg-type]
        object(),  # type: ignore[arg-type]
        mode="reminders",
        batch_size=5,
        now=datetime(2026, 11, 25, 12, 0, tzinfo=UTC),
    )

    assert report.lock_busy is True
    assert report.counts["scanned"] == 0
    assert engine.connection.closed is True


def test_billing_notice_worker_mode_accepts_its_bounded_options() -> None:
    args = worker._parser().parse_args(
        [
            "billing-notices",
            "--once",
            "--batch-size",
            "500",
            "--max-pages",
            "20",
            "--now",
            "2026-11-25T12:00:00Z",
        ]
    )

    assert args.mode == "billing-notices"
    assert args.batch_size == 500
    assert args.max_pages == 20
    assert worker.LOCK_NAMES[args.mode] == "sketch2life.billing-notices.v1"
    assert worker._empty_counts(args.mode) == {
        "scanned": 0,
        "created": 0,
        "already_present": 0,
        "skipped_stale": 0,
        "no_recipient": 0,
        "failed": 0,
    }


def test_billing_notice_worker_dispatches_counts_under_its_lock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = {
        "scanned": 4,
        "created": 1,
        "already_present": 1,
        "skipped_stale": 0,
        "no_recipient": 1,
        "failed": 1,
    }
    monkeypatch.setattr(worker, "run_billing_notice_pages", lambda *_args, **_kwargs: expected)

    report = worker.run_pass_locked(
        _AvailableEngine(),  # type: ignore[arg-type]
        object(),  # type: ignore[arg-type]
        mode="billing-notices",
        batch_size=10,
        max_pages=3,
        now=datetime(2026, 11, 25, 12, 0, tzinfo=UTC),
    )

    assert report.counts == expected
    assert report.errors == 1
    assert report.lock_busy is False
