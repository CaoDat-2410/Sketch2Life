"""FEAT-066 T-2d-fix: a failed rewrite after a video was marked unsuitable (PostgreSQL).

SRS l.416 and BR-16 l.260 (a rewrite is the adult's way back after an unsuitable video) with
SRS l.394 (a failed AI job returns the run to ``SCRIPT_REVIEW``): the failed attempt must leave the
``CONFIRMED`` story with its ``REJECTED_BY_ADULT`` video exactly as it was, and the retry must work
(the previous revision is superseded only when a later attempt completes). Runs only against a
disposable database whose name contains ``be1_acceptance``, ``frc08_v3_t1b`` and ``t2dfix`` (the
fixture and the builders are the T-1b module's); no provider is called.
"""

# ruff: noqa: F811  (the imported T-1b ``api`` fixture is used as a test argument)

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from sqlalchemy import select

from sketch2life.application.ports.parent_story_inputs import (
    StoryGenerationFailure,
    StoryGenerationResult,
)
from sketch2life.application.ports.story_task_reaper import REAPER_ACTOR_REF
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.infrastructure.persistence.story_task_reaper_store import build_story_task_reaper
from sketch2life.infrastructure.story_run_lite import tables as story_tables
from tests.integration.story_video.test_video_commands_postgres import (  # noqa: F401
    VideoApi,
    _bind_api,
    api,
    code_of,
    confirm_route,
    generations,
    make_rewritable,
    rewrite_route,
    run_row,
    story_rows,
    unsuitable,
    video_ready,
    video_request,
)
from tests.unit.test_story_output import valid_story

AUDIT = CoreAuditEntryModel.__table__
RUNS = story_tables.story_runs


@pytest.fixture(autouse=True)
def _task_database_name() -> None:
    name = os.environ.get("BE1_TEST_DATABASE_URL", "").rsplit("/", 1)[-1]
    if name and "t2dfix" not in name:
        pytest.skip("run on the t2dfix database (the T-1b guard also needs frc08_v3_t1b)")


class FailingThenWorking:
    """A story generator that fails technically ``failures`` times, then answers with a draft."""

    def __init__(self, failures: int) -> None:
        self.failures = failures
        self.calls = 0

    def generate(self, worker_input: Any) -> Any:
        self.calls += 1
        if self.calls <= self.failures:
            raise StoryGenerationFailure()
        story = valid_story()
        story["title"] = f"Rong nho lan {self.calls}"
        return StoryGenerationResult(story, f"call-{self.calls}", "fixture-model", "1")


def test_a_failed_rewrite_after_unsuitable_keeps_the_confirmed_story_and_the_retry_works(
    api: VideoApi,
) -> None:
    run, gid = video_ready(api)
    make_rewritable(api, run)
    api.app.state.story_generator = generator = FailingThenWorking(failures=1)
    assert unsuitable(api, run, gid).status_code == 200
    before = [(r["revision_no"], r["status"], r["story_sha256"]) for r in story_rows(run.run_id)]
    assert [status for _no, status, _sha in before] == ["CONFIRMED"]
    generation_before = [(g["generation_no"], g["state"]) for g in generations(run.run_id)]
    assert generation_before == [(1, "REJECTED_BY_ADULT")]

    failed = rewrite_route(api, run)
    assert failed.status_code == 202, failed.text
    # the run is back in review with the confirmed story and its rejected video untouched
    row = run_row(run.run_id)
    assert (row["run_state"], row["job_state"], row["retryable"]) == (
        "SCRIPT_REVIEW",
        "FAILED",
        True,
    )
    assert [(r["revision_no"], r["status"], r["story_sha256"]) for r in story_rows(run.run_id)] == (
        before
    )
    assert [(g["generation_no"], g["state"]) for g in generations(run.run_id)] == generation_before
    # the same video request is still refused (the review is consumed), a rewrite is the way back
    blocked = video_request(api, run, reason="QUALITY_LOW")
    assert blocked.status_code == 409 and code_of(blocked) == "INVALID_STATE_TRANSITION"

    retried = rewrite_route(api, run)
    assert retried.status_code == 202 and retried.json()["story_revision_no"] == 2
    assert generator.calls == 2
    assert [r["status"] for r in story_rows(run.run_id)] == ["SUPERSEDED", "DRAFT"]
    row = run_row(run.run_id)
    assert (row["run_state"], row["job_state"], row["retryable"], row["error_code"]) == (
        "SCRIPT_REVIEW",
        "SUCCEEDED",
        False,
        None,
    )
    # the rest of the way back is unchanged: confirm, then the next video is regeneration 2
    assert confirm_route(api, run).status_code == 200
    second = video_request(api, run, reason="NOT_MATCHING_STORY")
    assert second.status_code == 202, second.text
    assert second.json()["video_generation"]["kind"] == "QUALITY_REGEN"


def test_a_lost_rewrite_after_unsuitable_is_recovered_by_the_reaper(api: VideoApi) -> None:
    run, gid = video_ready(api)
    make_rewritable(api, run)
    api.app.state.story_generator = None  # no worker composed: the generation is lost (QUEUED)
    assert unsuitable(api, run, gid).status_code == 200
    assert rewrite_route(api, run).status_code == 202
    row = run_row(run.run_id)
    assert (row["run_state"], row["job_state"]) == ("SCRIPT_GENERATING", "QUEUED")
    assert [r["status"] for r in story_rows(run.run_id)] == ["CONFIRMED", "GENERATING"]
    with api.sessions().begin() as db:
        db.execute(
            RUNS.update()
            .where(RUNS.c.run_id == run.run_id)
            .values(updated_at=datetime(2020, 6, 1, 8, 0, tzinfo=UTC))
        )
    now = datetime(2020, 6, 1, 8, 0, tzinfo=UTC) + timedelta(minutes=30)
    with api.sessions()() as db:
        report = build_story_task_reaper(db).run_once(lease=timedelta(minutes=30), now=now)
    assert report.rewrite_recovered == 1 and report.errors == 0
    row = run_row(run.run_id)
    assert (row["run_state"], row["job_state"], row["error_code"]) == (
        "SCRIPT_REVIEW",
        "FAILED",
        "PROVIDER_TIMEOUT",
    )
    assert [r["status"] for r in story_rows(run.run_id)] == ["CONFIRMED"]
    assert [(g["generation_no"], g["state"]) for g in generations(run.run_id)] == [
        (1, "REJECTED_BY_ADULT")
    ]
    with api.sessions()() as db:
        actors = (
            db.execute(select(AUDIT.c.actor_ref).where(AUDIT.c.resource_id == run.run_id))
            .scalars()
            .all()
        )
    assert REAPER_ACTOR_REF in actors
    # the adult can ask again: the same T-1b rule accepts a rewrite from the confirmed story
    api.app.state.story_generator = FailingThenWorking(failures=0)
    again = rewrite_route(api, run)
    assert again.status_code == 202 and again.json()["story_revision_no"] == 2
    assert [r["status"] for r in story_rows(run.run_id)] == ["SUPERSEDED", "DRAFT"]
