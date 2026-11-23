"""PostgreSQL acceptance checks for S1, S7a and the Phase B StoryRun state seed."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
)
from tools.seed import data
from tools.seed.guard import SEED_URL_VARIABLE, guarded_engine
from tools.seed.s7a_runs import count_s7a_rows
from tools.seed.s7b_story_states import count_s7b_rows
from tools.seed.s7b_story_states_data import EXPECTED as EXPECTED_S7B_COUNTS
from tools.seed.stage_common import check_database_prefix

pytestmark = pytest.mark.skipif(
    not os.environ.get(SEED_URL_VARIABLE), reason=f"{SEED_URL_VARIABLE} is not set"
)

BACKEND = Path(__file__).resolve().parents[2]
ROW = re.compile(r"^(\S+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(yes|NO)$", re.MULTILINE)


def _run_module(module: str) -> tuple[int, dict[str, tuple[int, int, int, str]]]:
    env = {**os.environ, "PYTHONPATH": str(BACKEND / "src")}
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-m", module],
        cwd=BACKEND,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    rows = {
        name: (int(new), int(total), int(expected), ok)
        for name, new, total, expected, ok in ROW.findall(result.stdout)
    }
    return result.returncode, rows


@pytest.fixture(scope="module")
def seed_engine() -> Iterator[Engine]:
    from sketch2life.infrastructure.config.settings import (
        get_core_database_settings,
        get_settings,
    )

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
def acceptance_runs(
    seed_engine: Engine,
) -> dict[str, tuple[int, dict[str, tuple[int, int, int, str]]]]:
    s1_first = _run_module("tools.seed.s1_core")
    s1_second = _run_module("tools.seed.s1_core")
    s7a_first = _run_module("tools.seed.s7a_runs")
    s7a_second = _run_module("tools.seed.s7a_runs")
    s7b_first = _run_module("tools.seed.s7b_story_states")
    s7b_second = _run_module("tools.seed.s7b_story_states")
    s7a_after_s7b = _run_module("tools.seed.s7a_runs")
    return {
        "s1_first": s1_first,
        "s1_second": s1_second,
        "s7a_first": s7a_first,
        "s7a_second": s7a_second,
        "s7b_first": s7b_first,
        "s7b_second": s7b_second,
        "s7a_after_s7b": s7a_after_s7b,
    }


def test_seed_stages_are_idempotent_in_the_coordinator_order(
    acceptance_runs: dict[str, tuple[int, dict[str, tuple[int, int, int, str]]]],
) -> None:
    assert all(code == 0 for code, _rows in acceptance_runs.values())
    for name, expected in data.EXPECTED_COUNTS.items():
        assert acceptance_runs["s1_first"][1][name][1:3] == (expected, expected)
        assert acceptance_runs["s1_second"][1][name][0] == 0
    for run_key in ("s7a_first", "s7a_second", "s7a_after_s7b"):
        rows = acceptance_runs[run_key][1]
        assert set(rows) == set(data.EXPECTED_S7A_COUNTS)
        for name, expected in data.EXPECTED_S7A_COUNTS.items():
            assert rows[name][1:3] == (expected, expected)
            assert rows[name][3] == "yes"
    for run_key in ("s7b_first", "s7b_second"):
        rows = acceptance_runs[run_key][1]
        assert set(rows) == set(EXPECTED_S7B_COUNTS)
        for name, expected in EXPECTED_S7B_COUNTS.items():
            assert rows[name][1:3] == (expected, expected)
            assert rows[name][3] == "yes"
    for name, expected in EXPECTED_S7B_COUNTS.items():
        assert 0 <= acceptance_runs["s7b_first"][1][name][0] <= expected
        assert acceptance_runs["s7b_second"][1][name][0] == 0
    assert all(row[0] == 0 for row in acceptance_runs["s7a_after_s7b"][1].values())


def test_database_counts_are_scoped_to_each_seed_stage(
    seed_engine: Engine,
    acceptance_runs: dict[str, tuple[int, dict[str, tuple[int, int, int, str]]]],
) -> None:
    del acceptance_runs
    with seed_engine.connect() as connection:
        assert count_s7a_rows(connection) == data.EXPECTED_S7A_COUNTS
        assert count_s7b_rows(connection) == EXPECTED_S7B_COUNTS


def _run_states(engine: Engine, parent_key: str) -> list[str]:
    principal = VerifiedPrincipal(
        subject=data.PARENT_SUBJECTS[parent_key], issuer=data.SEED_ISSUER, roles=frozenset()
    )
    with Session(engine) as session:
        runs = SqlParentStoryRunRepository(session).list_runs(
            principal=principal, profile_id=None, limit=100, after=None
        )
        session.rollback()
    return [run.run_state for run in runs]


def test_parent_run_lists_expose_every_requested_phase_b_state(
    seed_engine: Engine,
    acceptance_runs: dict[str, tuple[int, dict[str, tuple[int, int, int, str]]]],
) -> None:
    del acceptance_runs
    expected = {
        "p1": {"COMPLETED", "FAILED", "DELETE_PENDING", "INPUT_PROCESSING", "ABANDONED"},
        "p2": {"COMPLETED", "PREPARATION_REVIEW"},
        "p3": {"COMPLETED", "INPUT_REVIEW"},
        "p4": {"SUBJECT_REVIEW"},
        "p5": {"VIDEO_READY"},
    }
    for parent_key, required_states in expected.items():
        assert required_states <= set(_run_states(seed_engine, parent_key)), parent_key
