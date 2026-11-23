"""V4-A T-1c-fix: a finished video can be watched again after Complete or the idle closeout
(PostgreSQL; owner decisions O-3 and C1(a)).

SRS l.283 BR-39, l.408, l.656 (content stays until the user deletes the run), l.1414, l.1676 (the
token), l.1672 (Complete is valid only at ``VIDEO_READY``, so a completed run can no longer be
marked unsuitable), l.500, l.502, l.1736 (deleting a run or a child profile ends playback at once),
l.394 (polling does not reset the idle clock). It reverses T-1c Q5, DEC-3 and DEC-4.

The ``api`` fixture and the database-name guard are the T-1c module's, so the database name must
contain ``be1_acceptance`` and ``frc08_v3_t1c``. Runs are built by the T-1b helpers (direct inserts
for the confirmed script, the real ``video-generations`` route and the fixture runner for the
video); object storage is in memory and no provider is called.
"""

# ruff: noqa: F401, F811  (the fixtures are imported for pytest and used as test arguments)

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import update

from sketch2life.application.ports.story_run_closeout import CloseoutOutcome
from sketch2life.application.ports.story_video import VideoRenderResult
from sketch2life.infrastructure.persistence.parent_models import (
    ParentChildProfileModel,
    ParentProfileRevisionModel,
)
from sketch2life.infrastructure.story_video.closeout_store import SqlStoryRunCloseoutStore
from sketch2life.infrastructure.story_video.fixture_runner import FixtureVideoRenderer
from tests.integration.story_video import test_video_commands_postgres as t1b
from tests.integration.story_video.test_playback_and_detail_postgres import (
    Api,
    _bind_api,
    api,
    assert_clean,
    content_of,
    detail,
    issue,
    ready_with_token,
    stream,
    token_of,
)

RUNS = t1b.RUNS


def _profile(api: Api, run: Any, state: str = "ACTIVE") -> str:
    """A profile row of the run's owner, bound to the run through ``profile_ref``."""

    profile_id = uuid4()
    with api.sessions().begin() as db:
        db.add(
            ParentChildProfileModel(
                parent_profile_id=profile_id,
                owner_issuer=t1b.ISSUER,
                owner_subject=run.owner,
                state=state,
                current_revision_no=1,
            )
        )
        db.add(
            ParentProfileRevisionModel(
                profile_revision_id=uuid4(),
                parent_profile_id=profile_id,
                revision_no=1,
                age_months=72,
                display_name="Synthetic child",
                authored_by_issuer=t1b.ISSUER,
                authored_by_subject=run.owner,
                revision_hash="a" * 64,
            )
        )
        db.execute(
            update(RUNS).where(RUNS.c.run_id == run.run_id).values(profile_ref=str(profile_id))
        )
    return str(profile_id)


def _set_profile(api: Api, profile_id: str, **values: Any) -> None:
    with api.sessions().begin() as db:
        db.execute(
            update(ParentChildProfileModel)
            .where(ParentChildProfileModel.parent_profile_id == profile_id)
            .values(**values)
        )


# ===================================================================== replay after Complete
def test_after_complete_a_new_token_streams_the_whole_video_and_a_byte_range(api: Api) -> None:
    run, _generation_id, old = ready_with_token(api)
    content = content_of(api, run)
    assert t1b.complete(api, run).status_code == 200
    assert t1b.run_row(run.run_id)["run_state"] == "COMPLETED"
    token = token_of(issue(api, run))
    whole = stream(api, run, token)
    assert whole.status_code == 200 and whole.content == content
    part = stream(api, run, token, Range="bytes=0-9")
    assert part.status_code == 206 and part.content == content[:10]
    # the token given before Complete is the same kind of grant and still works
    assert stream(api, run, old).status_code == 200
    # the generation stays READY: Complete is not a video approval
    assert t1b.generations(run.run_id)[0]["state"] == "READY"
    assert_clean(str(dict(whole.headers)))


def test_the_idle_closeout_keeps_the_video_playable(api: Api) -> None:
    run, _generation_id, token = ready_with_token(api)
    content = content_of(api, run)
    later = datetime.now(UTC) + timedelta(days=8)  # past the 168 h adult wait of a ready video
    with api.sessions()() as session:
        outcome = SqlStoryRunCloseoutStore(session).close_idle(run.run_id, later)
    assert outcome is CloseoutOutcome.COMPLETED
    row = t1b.run_row(run.run_id)
    assert row["run_state"] == "COMPLETED" and row["finished_at"] is not None
    assert row["active_owner_parent_account_id"] is None
    fresh = token_of(issue(api, run))
    assert stream(api, run, fresh).content == content
    assert stream(api, run, token).status_code == 200
    video = detail(api, run).json()["story_run"]["video"]
    assert video["playback"]["state"] == "AVAILABLE"


def test_the_detail_shows_available_after_complete_and_hidden_for_a_rejected_video(
    api: Api,
) -> None:
    run, generation_id = t1b.video_ready(api)
    assert t1b.complete(api, run).status_code == 200
    playback = detail(api, run).json()["story_run"]["video"]["playback"]
    assert playback["state"] == "AVAILABLE" and playback["asset_ref"] == f"vid_{generation_id}"
    assert playback["token_route"] == f"/v1/story-runs/{run.run_id}/playback-token"
    other, other_generation = t1b.video_ready(api, t1b.new_script_run(api, api.other_parent))
    assert t1b.unsuitable(api, other, other_generation).status_code == 200
    assert detail(api, other).json()["story_run"]["video"]["playback"]["state"] == "HIDDEN"


# ============================================================================== what still ends it
def test_a_completed_run_cannot_be_marked_unsuitable_and_keeps_playing(api: Api) -> None:
    run, generation_id = t1b.video_ready(api)
    assert t1b.complete(api, run).status_code == 200
    refused = t1b.unsuitable(api, run, generation_id)
    assert refused.status_code == 409 and t1b.code_of(refused) == "INVALID_STATE_TRANSITION"
    assert t1b.generations(run.run_id)[0]["state"] == "READY"
    assert issue(api, run).status_code == 200


def test_deleting_a_completed_run_ends_playback_for_every_token(api: Api) -> None:
    run, _generation_id, token = ready_with_token(api)
    assert t1b.complete(api, run).status_code == 200
    fresh = token_of(issue(api, run))
    deleted = api.client.delete(
        f"/v1/story-runs/{run.run_id}", headers=t1b.headers(run.owner, uuid4().hex)
    )
    assert deleted.status_code == 202, deleted.text
    for old in (token, fresh):
        gone = stream(api, run, old)
        assert gone.status_code == 404 and gone.json()["code"] == "RESOURCE_NOT_FOUND"
    assert issue(api, run).status_code == 404


@pytest.mark.parametrize("state", ["FAILED", "ABANDONED"])
def test_a_failed_or_abandoned_run_is_never_playable(api: Api, state: str) -> None:
    run, _generation_id, token = ready_with_token(api)
    with api.sessions().begin() as db:
        db.execute(update(RUNS).where(RUNS.c.run_id == run.run_id).values(run_state=state))
    refused = issue(api, run)
    assert refused.status_code == 409 and t1b.code_of(refused) == "INVALID_STATE_TRANSITION"
    assert stream(api, run, token).status_code == 404
    assert detail(api, run).json()["story_run"]["video"]["playback"]["state"] == "UNAVAILABLE"


def test_a_blocked_generation_and_a_rejected_video_are_never_playable_after_the_run_closes(
    api: Api,
) -> None:
    blocked_run = t1b.new_script_run(api)
    requested = t1b.video_request(api, blocked_run).json()
    blocked_id = str(requested["video_generation"]["generation_id"])
    renderer = FixtureVideoRenderer()
    renderer.results[blocked_id] = VideoRenderResult(
        content=b"x", media_type="video/mp4", safety_passed=False
    )
    t1b.runner(api, renderer).run_to_end(blocked_id)
    assert t1b.run_row(blocked_run.run_id)["run_state"] == "SCRIPT_REVIEW"  # V4-A exit (C11)
    with api.sessions().begin() as db:
        db.execute(
            update(RUNS).where(RUNS.c.run_id == blocked_run.run_id).values(run_state="COMPLETED")
        )
    assert issue(api, blocked_run).status_code == 409
    rejected, generation_id = t1b.video_ready(api, t1b.new_script_run(api, api.other_parent))
    assert t1b.unsuitable(api, rejected, generation_id).status_code == 200
    with api.sessions().begin() as db:
        db.execute(
            update(RUNS).where(RUNS.c.run_id == rejected.run_id).values(run_state="COMPLETED")
        )
    assert issue(api, rejected).status_code == 409


# ============================================================ the child profile (D5, SRS l.502)
@pytest.mark.parametrize("completed", [False, True])
def test_deleting_the_child_profile_ends_playback_at_the_next_request(
    api: Api, completed: bool
) -> None:
    run, _generation_id, token = ready_with_token(api)
    profile_id = _profile(api, run)
    if completed:
        assert t1b.complete(api, run).status_code == 200
    assert issue(api, run).status_code == 200  # an active profile: nothing changes
    assert stream(api, run, token).status_code == 200
    _set_profile(api, profile_id, state="DELETE_PENDING")
    gone = stream(api, run, token)
    assert gone.status_code == 404 and gone.json()["code"] == "RESOURCE_NOT_FOUND"
    assert issue(api, run).status_code == 404
    # the profile comes back (a test device only): playback follows the profile again
    _set_profile(api, profile_id, state="ACTIVE")
    assert stream(api, run, token).status_code == 200
    _set_profile(api, profile_id, deleted_at=datetime.now(UTC))
    assert stream(api, run, token).status_code == 404


def test_a_run_whose_profile_row_does_not_exist_is_not_revoked(api: Api) -> None:
    run, _generation_id, token = ready_with_token(api)  # the T-1b builders use a bare reference
    assert t1b.complete(api, run).status_code == 200
    assert stream(api, run, token).status_code == 200


# ================================================================ owner scope, idle clock, logs
def test_another_parent_cannot_use_the_token_of_a_completed_run(api: Api) -> None:
    run, _generation_id, token = ready_with_token(api)
    assert t1b.complete(api, run).status_code == 200
    stolen = stream(api, run, token, owner=api.other_parent)
    assert stolen.status_code == 404
    assert issue(api, run, api.other_parent).status_code == 404
    for subject in (api.teacher, api.manager, api.admin):
        assert issue(api, run, subject).status_code == 404


def test_asking_for_a_token_changes_nothing_on_the_run_and_resets_no_clock(api: Api) -> None:
    run, _generation_id = t1b.video_ready(api)
    assert t1b.complete(api, run).status_code == 200
    before = t1b.run_row(run.run_id)
    receipts_before = len(t1b.receipts(run.run_id, "COMPLETE_RUN"))
    assert issue(api, run).status_code == 200 and issue(api, run).status_code == 200
    after = t1b.run_row(run.run_id)
    for column in (
        "revision",
        "version",
        "updated_at",
        "adult_wait_started_at",
        "last_meaningful_activity_at",
        "finished_at",
        "run_state",
    ):
        assert after[column] == before[column], column
    assert len(t1b.receipts(run.run_id, "COMPLETE_RUN")) == receipts_before


def test_the_token_never_reaches_a_log_line_a_url_or_an_error_body_after_complete(
    api: Api, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    run, _generation_id = t1b.video_ready(api)
    assert t1b.complete(api, run).status_code == 200
    token = token_of(issue(api, run))
    streamed = stream(api, run, token)
    refused = stream(api, run, token, owner=api.other_parent)
    assert streamed.status_code == 200 and refused.status_code == 404
    assert token not in caplog.text and token not in refused.text
    assert token not in str(streamed.url) and token not in str(dict(streamed.headers))
