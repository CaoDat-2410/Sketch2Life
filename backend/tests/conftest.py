"""Shared backend test fixtures."""

from __future__ import annotations

import logging
from collections.abc import Iterator

import pytest

_LoggerState = tuple[bool, int, bool]  # disabled, level, propagate


def snapshot_logging() -> tuple[int, dict[str, _LoggerState]]:
    """The root level and the ``disabled``, ``level`` and ``propagate`` of every named logger."""

    states: dict[str, _LoggerState] = {}
    for name, candidate in list(logging.root.manager.loggerDict.items()):
        if isinstance(candidate, logging.Logger):
            states[name] = (candidate.disabled, candidate.level, candidate.propagate)
    return logging.root.level, states


def restore_logging(snapshot: tuple[int, dict[str, _LoggerState]]) -> None:
    """Undo what a test did to the process-wide logging state.

    Alembic's ``env.py`` calls ``logging.config.fileConfig`` when a test runs a migration in
    process; with the default ``disable_existing_loggers`` that disables every logger that already
    exists and sets the root level to WARNING for the rest of the process, so a later ``caplog``
    test sees nothing. Loggers the test created itself (a lazy import) are disabled by the same
    call, so they are reset to the defaults of a new logger. Handlers are not touched: pytest owns
    the capture handlers.
    """

    root_level, states = snapshot
    logging.root.setLevel(root_level)
    for name, candidate in list(logging.root.manager.loggerDict.items()):
        if not isinstance(candidate, logging.Logger):
            continue
        disabled, level, propagate = states.get(name, (False, logging.NOTSET, True))
        candidate.disabled = disabled
        candidate.setLevel(level)
        candidate.propagate = propagate


@pytest.fixture(autouse=True)
def _restore_logging_state() -> Iterator[None]:
    """Function-scoped. It cannot repair state left by a module or session fixture that runs a
    migration in process; the unit and contract tests that read logs do not use such a fixture.

    A logger first created inside a test and configured by application code at import (a level,
    ``propagate = False``) is reset to the defaults of a new logger afterwards, so later tests see
    it differently from a fresh import. No such logger exists in the repository today."""

    snapshot = snapshot_logging()
    try:
        yield
    finally:
        restore_logging(snapshot)
