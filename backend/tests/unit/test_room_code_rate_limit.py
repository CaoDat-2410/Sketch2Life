from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock

from sketch2life.interfaces.http.routers.be1_sessions import (
    _record_invalid_room_code,
    _room_code_source_throttled,
)


def test_room_code_limit_counts_recent_attempts_in_a_sliding_window() -> None:
    now = datetime(2026, 10, 24, 12, tzinfo=UTC)
    row = SimpleNamespace(
        attempts=[(now - timedelta(minutes=14)).isoformat()] * 10,
    )
    db = Mock()
    db.get.return_value = row

    assert _room_code_source_throttled(db, "source-hmac", now)


def test_room_code_limit_expires_each_attempt_individually() -> None:
    now = datetime(2026, 10, 24, 12, tzinfo=UTC)
    recent = (now - timedelta(minutes=14)).isoformat()
    expired = (now - timedelta(minutes=16)).isoformat()
    row = SimpleNamespace(attempts=[recent] * 9 + [expired])
    db = Mock()
    db.get.return_value = row

    assert not _room_code_source_throttled(db, "source-hmac", now)
    _record_invalid_room_code(db, "source-hmac", now)

    assert len(row.attempts) == 10
    cutoff = now - timedelta(minutes=15)
    assert all(datetime.fromisoformat(value) > cutoff for value in row.attempts)
    assert row.attempts[-1] == now.isoformat()


def test_room_code_limit_creates_a_source_record_on_first_invalid_attempt() -> None:
    now = datetime(2026, 10, 24, 12, tzinfo=UTC)
    db = Mock()
    db.get.return_value = None

    assert not _room_code_source_throttled(db, "source-hmac", now)
    _record_invalid_room_code(db, "source-hmac", now)

    created = db.add.call_args.args[0]
    assert created.source_hmac == "source-hmac"
    assert created.attempts == [now.isoformat()]
