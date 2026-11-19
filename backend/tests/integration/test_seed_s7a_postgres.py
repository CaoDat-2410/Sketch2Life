"""Seed-database check of S7 item 2a (FEAT-066 SEED-7a, package Draft 3 test T5).

Skipped unless ``S2L_SEED_DATABASE_URL`` is set. The guards of package section 3.1 run in
the writer's own process: this test starts S1 and S7a as subprocesses (``python -m
tools.seed.s1_core`` and ``tools.seed.s7a_runs``), so the Modal-import check is isolated
from this pytest process. It then reads the result back through the product repository.
The seed database may already have been through S7a, so the first run adds either zero
rows or the full expected rows.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from collections.abc import Iterator
from dataclasses import fields
from pathlib import Path

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import ParentStoryRunRecord
from sketch2life.contracts.schemas.parent_story_runs import ParentStoryRunResponseV1
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
)
from tools.seed import data
from tools.seed.guard import SEED_URL_VARIABLE, guarded_engine
from tools.seed.s1_core import count_rows
from tools.seed.s7a_runs import count_s7a_rows

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
def runs(seed_engine: Engine) -> dict[str, tuple[int, dict[str, tuple[int, int, int, str]]]]:
    s1 = _run_module("tools.seed.s1_core")
    first = _run_module("tools.seed.s7a_runs")
    second = _run_module("tools.seed.s7a_runs")
    return {"s1": s1, "first": first, "second": second}


def test_s1_then_s7a_exit_cleanly(
    runs: dict[str, tuple[int, dict[str, tuple[int, int, int, str]]]],
) -> None:
    assert runs["s1"][0] == 0
    assert runs["first"][0] == 0
    assert runs["second"][0] == 0


def test_first_run_adds_zero_or_expected_and_second_adds_zero(
    runs: dict[str, tuple[int, dict[str, tuple[int, int, int, str]]]],
) -> None:
    first_rows = runs["first"][1]
    second_rows = runs["second"][1]
    assert set(first_rows) == set(data.EXPECTED_S7A_COUNTS)
    for name, expected in data.EXPECTED_S7A_COUNTS.items():
        assert first_rows[name][0] in {0, expected}, name
        assert first_rows[name][1] == expected, name
        assert second_rows[name][0] == 0, name
        assert second_rows[name][1] == expected, name


def test_counts_in_the_database(seed_engine: Engine, runs: object) -> None:
    with seed_engine.connect() as connection:
        assert count_s7a_rows(connection) == data.EXPECTED_S7A_COUNTS
        # S1-scoped counting still passes with the S7a rows present.
        assert count_rows(connection) == data.EXPECTED_COUNTS


def _response(record: ParentStoryRunRecord) -> ParentStoryRunResponseV1:
    values = {field.name: getattr(record, field.name) for field in fields(record)}
    values["story"] = values.pop("story_content")
    return ParentStoryRunResponseV1.model_validate(values)


@pytest.mark.parametrize("spec", data.S7A_RUN_SPECS, ids=lambda spec: spec[0])
def test_p4_and_p5_have_one_confirmed_active_run(
    seed_engine: Engine, runs: object, spec: tuple[str, str, str, str]
) -> None:
    parent_key, profile_key, topic, idea = spec
    principal = VerifiedPrincipal(
        subject=data.PARENT_SUBJECTS[parent_key], issuer=data.SEED_ISSUER, roles=frozenset()
    )
    session = Session(seed_engine)
    try:
        repository = SqlParentStoryRunRepository(session)
        record = repository.get_active_run(
            principal=principal, account_id=data.parent_account_id(parent_key)
        )
        assert isinstance(record, ParentStoryRunRecord)
        response = _response(record)
    finally:
        session.rollback()
        session.close()
    assert record.run_state == "INPUT_PROCESSING"
    assert record.context_confirmed is True
    assert str(record.parent_profile_id) == str(data.parent_profile_id(profile_key))
    assert response.context_snapshot.topic == topic
    assert response.context_snapshot.adult_confirmed_idea == idea


@pytest.mark.parametrize("spec", data.STORY_RUN_SPECS, ids=lambda spec: spec[0])
def test_s1_runs_are_unchanged(
    seed_engine: Engine, runs: object, spec: tuple[str, str, str, str, bool, str, str | None]
) -> None:
    key, parent_key, _profile_key, state, _active, _topic, _idea = spec
    principal = VerifiedPrincipal(
        subject=data.PARENT_SUBJECTS[parent_key],
        issuer=data.SEED_ISSUER,
        roles=frozenset({"parent"}),
    )
    session = Session(seed_engine)
    try:
        record = SqlParentStoryRunRepository(session).get_run(
            principal=principal, run_id=data.run_id(key)
        )
    finally:
        session.rollback()
        session.close()
    assert record.run_state == state
