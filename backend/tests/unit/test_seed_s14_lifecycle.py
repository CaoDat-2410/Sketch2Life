"""Tests for replay and failure handling of the lifecycle stage."""

from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest

from tools.seed import s14_lifecycle as stage
from tools.seed.stage_common import StageError


def test_creates_once_and_replays(monkeypatch):
    session = MagicMock()
    session.scalar.side_effect = [0, 1, 1, 1]

    @contextmanager
    def factory():
        yield session

    monkeypatch.setattr(stage, "create_core_session_factory", lambda _engine: factory)
    create = MagicMock(return_value={"state": "requested"})
    monkeypatch.setattr(stage, "create_data_request", create)
    first = stage.run_s14_lifecycle(MagicMock())
    second = stage.run_s14_lifecycle(MagicMock())
    assert first.ok and second.ok
    assert create.call_count == 1
    assert create.call_args.args[1].target_ref == stage.KEY
    assert create.call_args.args[1].request_type == "export"


def test_refuses_duplicate(monkeypatch):
    session = MagicMock()
    session.scalar.return_value = 2

    @contextmanager
    def factory():
        yield session

    monkeypatch.setattr(stage, "create_core_session_factory", lambda _engine: factory)
    with pytest.raises(StageError, match="^S14_LIFECYCLE_DUPLICATE$"):
        stage.run_s14_lifecycle(MagicMock())
