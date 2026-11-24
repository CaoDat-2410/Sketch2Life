from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Any

import pytest
from sqlalchemy.dialects import postgresql

from sketch2life.infrastructure.persistence.outbox import PostgresOutbox


class _CaptureSession(AbstractContextManager["_CaptureSession"]):
    statement: Any = None

    def __enter__(self) -> _CaptureSession:
        return self

    def __exit__(self, *_exc: object) -> None:
        return None

    def scalars(self, statement: Any) -> tuple[()]:
        self.statement = statement
        return ()


class _SessionFactory:
    def __init__(self) -> None:
        self.session = _CaptureSession()

    def begin(self) -> _CaptureSession:
        return self.session


def test_claim_ready_compiles_an_exact_aggregate_filter() -> None:
    sessions = _SessionFactory()
    target = "08657e31-ebd7-4a07-8f9b-5929b4dff23b"

    assert PostgresOutbox(sessions).claim_ready(
        worker_id="one-shot-test",
        limit=1,
        event_types=("StoryRunCancellationRequestedV1",),
        aggregate_ids=(target,),
    ) == ()

    compiled = sessions.session.statement.compile(dialect=postgresql.dialect())
    assert "core_outbox_events.aggregate_id IN" in str(compiled)
    assert any(
        target in value if isinstance(value, list) else value == target
        for value in compiled.params.values()
    )


def test_claim_ready_refuses_an_empty_aggregate_allowlist() -> None:
    sessions = _SessionFactory()

    with pytest.raises(ValueError, match="aggregate filter must not be empty"):
        PostgresOutbox(sessions).claim_ready(
            worker_id="one-shot-test",
            aggregate_ids=(),
        )

    assert sessions.session.statement is None


def test_claim_ready_refuses_more_than_500_distinct_aggregates() -> None:
    sessions = _SessionFactory()

    with pytest.raises(ValueError, match="aggregate filter exceeds its bound"):
        PostgresOutbox(sessions).claim_ready(
            worker_id="one-shot-test",
            aggregate_ids=tuple(f"run-{index}" for index in range(501)),
        )

    assert sessions.session.statement is None
