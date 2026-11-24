from __future__ import annotations

import logging
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import OperationalError
from starlette.requests import Request

from sketch2life.interfaces.http.be1_runtime import get_db


def test_database_preflight_returns_safe_503_and_logs_typed_correlation(caplog) -> None:
    class DriverFailure(Exception):
        sqlstate = "08006"

    class FailedSession:
        rolled_back = False
        closed = False

        def execute(self, _statement):
            raise OperationalError("SELECT 1", {}, DriverFailure("private database detail"))

        def rollback(self):
            self.rolled_back = True

        def close(self):
            self.closed = True

    session = FailedSession()
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/auth/v1/registrations",
            "headers": [],
        }
    )
    request.state.be1_request_id = "rev51-request-001"
    runtime = SimpleNamespace(session_factory=lambda: session)

    caplog.set_level(logging.ERROR, logger="sketch2life.interfaces.http.be1_runtime")
    dependency = get_db(request=request, runtime=runtime)
    with pytest.raises(HTTPException) as raised:
        next(dependency)

    assert raised.value.status_code == 503
    assert raised.value.detail == {"code": "DATABASE_UNAVAILABLE"}
    assert session.rolled_back is True
    assert session.closed is True
    log_text = "\n".join(record.getMessage() for record in caplog.records)
    assert "be1_database_unavailable" in log_text
    assert "rev51-request-001" in log_text
    assert "OperationalError" in log_text
    assert "DriverFailure" in log_text
    assert "08006" in log_text
    assert "private database detail" not in log_text
