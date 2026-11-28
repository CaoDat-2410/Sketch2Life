from __future__ import annotations

import logging
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import OperationalError

from sketch2life.interfaces.http.be1_runtime import get_db


class _DriverFailure(Exception):
    pass


class _FailedSession:
    def __init__(self, *, fail_rollback: bool = False) -> None:
        self.fail_rollback = fail_rollback
        self.rolled_back = False
        self.closed = False

    def execute(self, _statement: object) -> None:
        raise OperationalError("SELECT 1", {}, _DriverFailure("private child datum detail"))

    def rollback(self) -> None:
        self.rolled_back = True
        if self.fail_rollback:
            raise OperationalError("ROLLBACK", {}, _DriverFailure("private rollback detail"))

    def close(self) -> None:
        self.closed = True


def _run_failed_probe(session: _FailedSession) -> None:
    runtime = SimpleNamespace(session_factory=lambda: session)
    dependency = get_db(runtime=runtime)
    with pytest.raises(HTTPException) as raised:
        next(dependency)

    assert raised.value.status_code == 503
    assert raised.value.detail == {"code": "DATABASE_UNAVAILABLE"}
    assert session.rolled_back is True
    assert session.closed is True


def test_database_preflight_returns_safe_503_and_logs_only_code_and_type(caplog) -> None:
    session = _FailedSession()

    caplog.set_level(logging.ERROR, logger="sketch2life.interfaces.http.be1_runtime")
    _run_failed_probe(session)

    log_messages = [
        record.getMessage()
        for record in caplog.records
        if record.name == "sketch2life.interfaces.http.be1_runtime"
    ]
    assert log_messages == ["code=DATABASE_UNAVAILABLE error_type=OperationalError"]
    assert "private child datum detail" not in "\n".join(log_messages)
    assert "SELECT 1" not in "\n".join(log_messages)


def test_database_rollback_failure_uses_a_second_safe_typed_diagnostic(caplog) -> None:
    session = _FailedSession(fail_rollback=True)

    caplog.set_level(logging.ERROR, logger="sketch2life.interfaces.http.be1_runtime")
    _run_failed_probe(session)

    log_messages = [
        record.getMessage()
        for record in caplog.records
        if record.name == "sketch2life.interfaces.http.be1_runtime"
    ]
    assert log_messages == [
        "code=DATABASE_ROLLBACK_FAILED error_type=OperationalError",
        "code=DATABASE_UNAVAILABLE error_type=OperationalError",
    ]
    assert "private rollback detail" not in "\n".join(log_messages)
    # The failed statement text must not appear; the diagnostic code itself names the rollback.
    assert "ROLLBACK" not in "\n".join(log_messages).replace("DATABASE_ROLLBACK_FAILED", "")
