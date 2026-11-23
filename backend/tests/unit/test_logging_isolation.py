"""FEAT-066 T-1d1-fix: a test that runs an Alembic migration in process must not silence the logs of
the tests after it (``alembic/env.py`` calls ``logging.config.fileConfig``)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from logging.config import fileConfig
from pathlib import Path

import pytest

from sketch2life.application.services.story_sweep_runner import SweepStep, run_sweepers_once
from tests.conftest import restore_logging, snapshot_logging

ALEMBIC_INI = Path(__file__).resolve().parents[2] / "alembic.ini"
APP_LOGGER = "sketch2life.application.services.story_sweep_runner"


def _ours(name: str) -> logging.Logger:
    return logging.getLogger(name)


def test_the_helper_undoes_file_config_for_old_and_new_loggers() -> None:
    """Order-independent proof of the restore itself."""

    existing = _ours("t1d1fix.existing")
    existing.setLevel(logging.DEBUG)
    before = snapshot_logging()
    created_inside = _ours("t1d1fix.created_inside")  # first used after the snapshot
    fileConfig(ALEMBIC_INI)  # the default disable_existing_loggers=True, root level WARNING
    assert existing.disabled and created_inside.disabled
    assert logging.root.level == logging.WARNING
    restore_logging(before)
    assert not existing.disabled and existing.level == logging.DEBUG
    assert not created_inside.disabled and created_inside.level == logging.NOTSET
    assert created_inside.propagate
    assert logging.root.level == before[0]


def test_a_test_that_runs_file_config_pollutes_the_process_inside_its_own_body() -> None:
    fileConfig(ALEMBIC_INI)
    assert _ours(APP_LOGGER).disabled  # the failure mode this module guards against


def test_the_next_test_still_sees_the_application_logs(caplog: pytest.LogCaptureFixture) -> None:
    """Runs right after the polluter in file order; the autouse fixture restored the state."""

    assert not _ours(APP_LOGGER).disabled
    assert not _ours("sketch2life").disabled
    with caplog.at_level(logging.INFO):
        run_sweepers_once(
            steps=[SweepStep("probe", lambda now, batch: {"seen": 1})],
            clock=lambda: datetime(2026, 1, 1, tzinfo=UTC),
        )
    assert "story_sweep_pass" in caplog.text and "probe.seen=1" in caplog.text
