"""PostgreSQL acceptance coverage for the S10 notification inbox seed."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import Engine

from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.notifications.inbox_repository import NotificationInboxService
from sketch2life.infrastructure.persistence.database import create_core_session_factory
from tools.seed import data
from tools.seed.guard import SEED_URL_VARIABLE, guarded_engine
from tools.seed.s10_inbox import count_stage_rows
from tools.seed.s10_inbox_data import EXPECTED, ITEMS
from tools.seed.stage_common import check_database_prefix, seed_principal

pytestmark = pytest.mark.skipif(
    not os.environ.get(SEED_URL_VARIABLE), reason=f"{SEED_URL_VARIABLE} is not set"
)

BACKEND = Path(__file__).resolve().parents[2]
ROW = re.compile(r"^(\S+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(yes|NO)$", re.MULTILINE)
PAGE_CLOCK = datetime(2026, 12, 1, 0, 0, tzinfo=UTC)
StageRun = tuple[int, dict[str, tuple[int, int, int, str]], str]


def _run_module(module: str) -> StageRun:
    environment = {
        **os.environ,
        "PYTHONPATH": os.pathsep.join((str(BACKEND / "src"), str(BACKEND))),
    }
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-m", module],
        cwd=BACKEND,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    rows = {
        name: (int(new), int(total), int(expected), ok)
        for name, new, total, expected, ok in ROW.findall(result.stdout)
    }
    return result.returncode, rows, result.stdout + result.stderr


@pytest.fixture(scope="module")
def seed_engine() -> Iterator[Engine]:
    previous = os.environ.get("SKETCH2LIFE_DATABASE_URL")
    try:
        check_database_prefix()
        engine, _target = guarded_engine()
        try:
            yield engine
        finally:
            engine.dispose()
    finally:
        if previous is None:
            os.environ.pop("SKETCH2LIFE_DATABASE_URL", None)
        else:
            os.environ["SKETCH2LIFE_DATABASE_URL"] = previous
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


@pytest.fixture(scope="module")
def stage_runs() -> tuple[StageRun, ...]:
    core = _run_module("tools.seed.s1_core")
    s7a = _run_module("tools.seed.s7a_runs")
    # S10 points its items at rows of the lesson, class and Parent-run stages.
    for module in ("tools.seed.s8_lessons", "tools.seed.s7b_story_states"):
        assert _run_module(module)[0] == 0, module
    first = _run_module("tools.seed.s10_inbox")
    second = _run_module("tools.seed.s10_inbox")
    assert core[0] == 0 and s7a[0] == 0, (core[2], s7a[2])
    return core, s7a, first, second


def test_s10_is_idempotent_and_reports_all_expected_counts(
    stage_runs: tuple[StageRun, ...],
) -> None:
    first, second = stage_runs[2:]
    assert first[0] == second[0] == 0, (first[2], second[2])
    assert set(second[1]) == set(EXPECTED)
    for table, expected in EXPECTED.items():
        assert second[1][table] == (0, expected, expected, "yes")


def test_inbox_pages_are_newest_first_and_have_the_expected_read_states(
    seed_engine: Engine,
    stage_runs: tuple[StageRun, ...],
) -> None:
    factory = create_core_session_factory(seed_engine)
    subjects = (
        data.PARENT_SUBJECTS["p1"],
        data.PARENT_SUBJECTS["p3"],
        data.PARENT_SUBJECTS["p4"],
        data.PARENT_SUBJECTS["p5"],
        data.ORG_A_TEACHERS[0],
        data.manager_subject("a"),
    )
    expected = dict(zip(subjects, ((2, 1), (2, 1), (1, 0), (2, 0), (4, 1), (4, 2)), strict=True))
    for subject in subjects:
        with factory() as session:
            page = NotificationInboxService(session, lambda: PAGE_CLOCK).list_page(
                principal=seed_principal(subject), limit=100, after=None
            )
        wanted_count, wanted_read = expected[subject]
        assert len(page.items) == wanted_count
        created = [item["created_at"] for item in page.items]
        assert created == sorted(created, reverse=True)
        assert sum(item["read_at"] is not None for item in page.items) == wanted_read
        assert page.unread_count == wanted_count - wanted_read


def test_seed_specs_only_use_the_seeded_principals_and_future_expiries() -> None:
    assert len(ITEMS) == EXPECTED["notifications_inbox_items"]
    assert all(item.expires_at is None or item.expires_at > PAGE_CLOCK for item in ITEMS)


def test_database_counts_match_the_s10_contract(
    seed_engine: Engine,
    stage_runs: tuple[StageRun, ...],
) -> None:
    with seed_engine.connect() as connection:
        assert count_stage_rows(connection) == EXPECTED
