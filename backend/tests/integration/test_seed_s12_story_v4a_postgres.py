"""PostgreSQL acceptance checks for the S12 Story v4a seed stage."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from collections.abc import Iterator
from typing import TypedDict

import pytest
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from sketch2life.application.ports.story_video import PlaybackStatus
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
)
from sketch2life.infrastructure.story_run_lite import tables as story_tables
from sketch2life.infrastructure.story_video.repository import SqlStoryVideoRepository
from tools.seed import s12_story_v4a, s12_story_v4a_data
from tools.seed.guard import SEED_URL_VARIABLE, guarded_engine
from tools.seed.s1_core import run_s1
from tools.seed.s7a_runs import run_s7a
from tools.seed.s7b_story_states import run_s7b
from tools.seed.s8_lessons import run_s8
from tools.seed.s12_story_v4a_data import EXPECTED, PARENTS_BY_KEY
from tools.seed.stage_common import check_database_prefix, seed_principal

pytestmark = pytest.mark.skipif(
    not os.environ.get(SEED_URL_VARIABLE), reason=f"{SEED_URL_VARIABLE} is not set"
)


class SeededState(TypedDict):
    first_exit: int
    second_exit: int
    before_second: dict[str, int]
    totals: dict[str, int]


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
def seeded(seed_engine: Engine) -> SeededState:
    run_s1(seed_engine)
    run_s7a(seed_engine)
    run_s8(seed_engine)
    run_s7b(seed_engine)

    first = subprocess.run(
        [sys.executable, "-m", "tools.seed.s12_story_v4a"],
        check=False,
        capture_output=True,
        text=True,
    )
    with seed_engine.connect() as connection:
        before_second = s12_story_v4a.count_s12_rows(connection)
    second = subprocess.run(
        [sys.executable, "-m", "tools.seed.s12_story_v4a"],
        check=False,
        capture_output=True,
        text=True,
    )
    with seed_engine.connect() as connection:
        totals = s12_story_v4a.count_s12_rows(connection)
    return {
        "first_exit": first.returncode,
        "second_exit": second.returncode,
        "before_second": before_second,
        "totals": totals,
    }


def test_s12_module_twice_adds_zero_rows_and_matches_expected(seeded: SeededState) -> None:
    assert seeded["first_exit"] == 0
    assert seeded["second_exit"] == 0
    assert seeded["before_second"] == EXPECTED
    assert seeded["totals"] == EXPECTED


def test_phase_a_run_stays_ready_for_activity_review_and_other_story_states_replayable(
    seed_engine: Engine, seeded: SeededState
) -> None:
    del seeded
    with seed_engine.connect() as connection:
        started_selections = connection.execute(
            select(story_tables.activity_selections.c.selection_no)
            .where(story_tables.activity_selections.c.run_id == s12_story_v4a_data.RUN_STARTED_ID)
            .order_by(story_tables.activity_selections.c.selection_no)
        ).scalars().all()
        assert list(started_selections) == []

        completed_epochs = connection.execute(
            select(story_tables.story_revision_reviews.c.review_epoch)
            .where(
                story_tables.story_revision_reviews.c.run_id
                == s12_story_v4a_data.RUN_COMPLETED_ID
            )
            .order_by(story_tables.story_revision_reviews.c.review_epoch)
        ).scalars().all()
        assert list(completed_epochs) == [1, 2]

    p6_principal = seed_principal(PARENTS_BY_KEY["p6"].subject)
    p7_principal = seed_principal(PARENTS_BY_KEY["p7"].subject)
    p1_principal = seed_principal("seed-parent-p1")

    with Session(seed_engine) as session:
        repo = SqlParentStoryRunRepository(session)
        started_view = repo.get_run(
            principal=p6_principal, run_id=s12_story_v4a_data.RUN_STARTED_ID
        )
        assert started_view.run_state == "PREPARATION_REVIEW"

        sb_view = repo.get_run(
            principal=p7_principal, run_id=s12_story_v4a_data.RUN_SAFETY_BLOCKED_ID
        )
        assert sb_view.run_state == "SCRIPT_REVIEW"
        assert sb_view.story_confirmation_required is True
        assert sb_view.error_code == "VIDEO_SAFETY_BLOCKED"

        completed_view = repo.get_run(
            principal=p1_principal, run_id=s12_story_v4a_data.RUN_COMPLETED_ID
        )
        assert completed_view.run_state == "COMPLETED"

        playback = SqlStoryVideoRepository(session).resolve_playback(
            principal=p1_principal,
            run_id=s12_story_v4a_data.RUN_COMPLETED_ID,
            generation_id=s12_story_v4a_data.COMPLETED_VIDEO_READY_ID,
        )
        assert playback.status == PlaybackStatus.PLAYABLE


def test_parent_activity_suggestions_are_catalog_backed_and_hash_bound(
    seed_engine: Engine, seeded: SeededState
) -> None:
    del seeded
    with seed_engine.connect() as connection:
        suggestion = connection.execute(
            select(story_tables.parent_activity_suggestion_sets).where(
                story_tables.parent_activity_suggestion_sets.c.run_id
                == s12_story_v4a_data.RUN_STARTED_ID
            )
        ).mappings().one()
        activities = suggestion["activities_snapshot"]
        expected_hash = hashlib.sha256(
            json.dumps(
                activities,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        assert suggestion["selection_mode"] == "CATALOG_SELECTION"
        assert suggestion["provider_call_id"] is None
        assert suggestion["activities_snapshot_sha256"] == expected_hash
        assert len(activities) == 1
        assert all(item["source_lesson_title"] for item in activities)
        assert connection.execute(
            select(story_tables.parent_activity_selections.c.activity_selection_id).where(
                story_tables.parent_activity_selections.c.run_id
                == s12_story_v4a_data.RUN_STARTED_ID
            )
        ).first() is None
