"""FEAT-066 T-1d1-fix: the way back after the generation deadline, through the real routes.

SRS l.395 (the six-hour deadline), l.2119-2120 and BR-11 l.255 (a failed accepted request counts
toward the cap and the run goes back to script review, or ends ``FAILED`` when no request is left),
FR-AI-07 l.573 (three requests), l.416 and BR-16 l.260 (a rewrite after a spent video makes a new
revision that needs a confirmation), FR-C-11 l.503 (the idle close frees the lock). Every step the
adult takes is a real route (``video-generations``, ``story-rewrites``, ``script-confirmation``,
``complete``, ``cancel``, the run detail); only the deadline itself is the sweep with an injected
clock. The app, the fixture runner and the builders are the T-1b module's, so the database name
must contain ``be1_acceptance`` and ``frc08_v3_t1b``. No provider, no sleep.
"""

# ruff: noqa: F811  (the imported fixtures are used as test arguments)

from __future__ import annotations

from datetime import timedelta
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from sketch2life.application.ports.story_video import ProgressEvent
from sketch2life.application.services.story_run_video import StoryVideoProgressService
from sketch2life.infrastructure.story_video.closeout_store import build_story_run_closeout
from sketch2life.infrastructure.story_video.repository import SqlStoryVideoRepository
from tests.integration.story_video.test_video_commands_postgres import (  # noqa: F401
    VG,
    ScriptRun,
    VideoApi,
    _bind_api,
    api,
    cancel,
    code_of,
    complete,
    confirm_route,
    generations,
    headers,
    make_rewritable,
    new_script_run,
    rewrite_and_confirm,
    rewrite_route,
    run_row,
    runner,
    story_rows,
    video_ready,
    video_request,
)

DEADLINE = timedelta(hours=6)
HOURS_168 = timedelta(hours=168)


def sweep(api: VideoApi, generation_id: str, *, extra: timedelta = timedelta(0)) -> Any:
    """One pass at the instant the generation is overdue (plus ``extra``): reaper-free, adapters
    composed as in the app, batch large enough for the whole database."""

    with api.sessions()() as session:
        accepted_at = session.scalar(
            select(VG.c.accepted_at).where(VG.c.video_generation_id == generation_id)
        )
    assert accepted_at is not None
    session = api.sessions()()
    try:
        return build_story_run_closeout(session, api.adapters).run_once(
            accepted_at + DEADLINE + extra, batch_size=200
        )
    finally:
        session.close()


def idle_sweep(api: VideoApi, run: ScriptRun, *, after: timedelta) -> Any:
    """A pass ``after`` the run's current wait clock."""

    row = run_row(run.run_id)
    clock = max(row["updated_at"], row["adult_wait_started_at"])
    session = api.sessions()()
    try:
        return build_story_run_closeout(session, api.adapters).run_once(
            clock + after, batch_size=200
        )
    finally:
        session.close()


def accepted(api: VideoApi, run: ScriptRun, *, reason: str | None = None) -> str:
    """One accepted request through the real route, left at ``ACCEPTED``; returns its id."""

    response = video_request(api, run, reason=reason)
    assert response.status_code == 202, response.text
    body = response.json()["video_generation"]
    assert body["state"] == "ACCEPTED"
    return str(body["generation_id"])


def detail_video(api: VideoApi, run: ScriptRun) -> dict[str, Any]:
    response = api.client.get(f"/v1/story-runs/{run.run_id}", headers=headers(run.owner))
    assert response.status_code == 200, response.text
    return dict(response.json()["story_run"]["video"])


def lock_of(run_id: str) -> Any:
    return run_row(run_id)["active_owner_parent_account_id"]


def owner_can_hold_a_lock_again(api: VideoApi, owner: str) -> None:
    """The unique index allows one active run per account: a new run takes the slot only when the
    old one released it."""

    fresh = new_script_run(api, owner)
    assert lock_of(fresh.run_id) is not None


def test_after_a_deadline_the_adult_rewrites_confirms_and_asks_again(api: VideoApi) -> None:
    run = new_script_run(api)
    generator = make_rewritable(api, run)
    first = accepted(api, run)
    report = sweep(api, first)
    assert report.deadline_failed >= 1 and report.errors == 0
    row = run_row(run.run_id)
    assert row["run_state"] == "SCRIPT_REVIEW" and lock_of(run.run_id) is not None
    assert [(g["generation_no"], g["state"]) for g in generations(run.run_id)] == [(1, "FAILED")]
    video = detail_video(api, run)
    assert video["video_requests_used"] == 1 and video["video_requests_remaining"] == 2
    # the same story cannot be asked for again (its review is spent, as after a rejection)
    same_story = video_request(api, run, reason="QUALITY_LOW")
    assert same_story.status_code == 409 and code_of(same_story) == "INVALID_STATE_TRANSITION"
    # the way back: a rewrite, then its confirmation (BR-16 l.260)
    rewritten = rewrite_route(api, run)
    assert rewritten.status_code == 202, rewritten.text
    assert generator.calls == 1 and rewritten.json()["story_revision_no"] == 2
    assert [r["status"] for r in story_rows(run.run_id)] == ["SUPERSEDED", "DRAFT"]
    unconfirmed = video_request(api, run, reason="QUALITY_LOW")
    assert unconfirmed.status_code == 409 and len(generations(run.run_id)) == 1
    assert confirm_route(api, run).status_code == 200
    assert [r["status"] for r in story_rows(run.run_id)] == ["SUPERSEDED", "CONFIRMED"]
    second = video_request(api, run, reason="QUALITY_LOW")
    assert second.status_code == 202, second.text
    body = second.json()["video_generation"]
    assert body["kind"] == "QUALITY_REGEN" and body["generation_no"] == 2
    assert [(g["generation_no"], g["state"]) for g in generations(run.run_id)] == [
        (1, "FAILED"),
        (2, "ACCEPTED"),
    ]
    final = runner(api).run_to_end(str(body["generation_id"]))
    assert final.record is not None and final.record.state == "READY"
    assert run_row(run.run_id)["run_state"] == "VIDEO_READY"
    video = detail_video(api, run)
    assert video["video_requests_used"] == 2 and video["video_requests_remaining"] == 1
    assert complete(api, run).status_code == 200
    done = run_row(run.run_id)
    assert done["run_state"] == "COMPLETED" and lock_of(run.run_id) is None
    owner_can_hold_a_lock_again(api, run.owner)


def test_a_second_deadline_leaves_one_request_and_the_third_one_ends_the_run(
    api: VideoApi,
) -> None:
    run = new_script_run(api)
    make_rewritable(api, run)
    sweep(api, accepted(api, run))
    rewrite_and_confirm(api, run)
    second = accepted(api, run, reason="QUALITY_LOW")
    assert sweep(api, second).deadline_failed >= 1
    assert run_row(run.run_id)["run_state"] == "SCRIPT_REVIEW"
    video = detail_video(api, run)
    assert video["video_requests_used"] == 2 and video["video_requests_remaining"] == 1
    rewrite_and_confirm(api, run)
    third = accepted(api, run, reason="CONTENT_CONCERN")
    assert [g["generation_no"] for g in generations(run.run_id)] == [1, 2, 3]
    assert sweep(api, third).deadline_failed >= 1
    # the cap is spent: no rewrite could lead to a request, so the run ends and frees the lock
    row = run_row(run.run_id)
    assert row["run_state"] == "FAILED" and lock_of(run.run_id) is None
    assert row["finished_at"] is not None and row["error_code"] == "VIDEO_DEADLINE_EXCEEDED"
    assert [g["state"] for g in generations(run.run_id)] == ["FAILED", "FAILED", "FAILED"]
    video = detail_video(api, run)
    assert video["video_requests_used"] == 3 and video["video_requests_remaining"] == 0
    refused = video_request(api, run, reason="QUALITY_LOW")
    assert refused.status_code == 409 and code_of(refused) == "INVALID_STATE_TRANSITION"
    assert rewrite_route(api, run).status_code == 409
    owner_can_hold_a_lock_again(api, run.owner)


def test_when_the_cap_was_already_two_the_third_deadline_ends_the_run_at_once(
    api: VideoApi,
) -> None:
    run = new_script_run(api, prior=2)  # requests 1 and 2 were accepted and failed earlier
    make_rewritable(api, run)
    third = accepted(api, run, reason="QUALITY_LOW")
    sweep(api, third)
    row = run_row(run.run_id)
    assert row["run_state"] == "FAILED" and lock_of(run.run_id) is None
    assert generations(run.run_id)[-1]["state"] == "FAILED"
    owner_can_hold_a_lock_again(api, run.owner)


def test_with_all_three_rewrites_spent_the_deadline_ends_the_run_instead_of_a_dead_end(
    api: VideoApi,
) -> None:
    """The revision-four corner (T-1b OPEN Q4): no rewrite is left, so a run returned to the
    script review could only wait for the idle close. It ends ``FAILED`` and frees the lock."""

    run, first = video_ready(api)
    make_rewritable(api, run)
    unmarked = api.client.post(
        f"/v1/story-runs/{run.run_id}/video-unsuitable",
        json={
            "expected_revision": int(run_row(run.run_id)["revision"]),
            "generation_id": first,
            "reason_code": "QUALITY_LOW",
        },
        headers=headers(run.owner, uuid4().hex),
    )
    assert unmarked.status_code == 200, unmarked.text
    for _ in range(3):  # revisions 2, 3 and 4
        assert rewrite_route(api, run).status_code == 202
    assert confirm_route(api, run).status_code == 200
    assert len(story_rows(run.run_id)) == 4
    second = accepted(api, run, reason="QUALITY_LOW")
    assert sweep(api, second).deadline_failed >= 1
    row = run_row(run.run_id)
    assert row["run_state"] == "FAILED" and lock_of(run.run_id) is None
    assert generations(run.run_id)[-1]["state"] == "FAILED"
    owner_can_hold_a_lock_again(api, run.owner)


def test_a_returned_run_does_not_hold_the_owner_lock_forever(api: VideoApi) -> None:
    run = new_script_run(api)
    make_rewritable(api, run)
    first = accepted(api, run)
    sweep(api, first)
    held = lock_of(run.run_id)
    assert held is not None
    # while the run waits, the same account cannot start another one (SRS l.383)
    with pytest.raises(IntegrityError):
        new_script_run(api, run.owner, hold_slot=True)
    # 168 h minus a second after the failure: still waiting for the adult
    assert idle_sweep(api, run, after=HOURS_168 - timedelta(seconds=1)).errors == 0
    assert run_row(run.run_id)["run_state"] == "SCRIPT_REVIEW"
    # 168 h after the failure: the idle close ends it and frees the lock (FR-C-11 l.503)
    assert idle_sweep(api, run, after=HOURS_168).errors == 0
    closed = run_row(run.run_id)
    assert closed["run_state"] == "ABANDONED" and lock_of(run.run_id) is None
    assert closed["job_state"] is None and closed["error_code"] is None
    assert generations(run.run_id)[0]["state"] == "FAILED"  # the attempt stays on its row
    refused = video_request(api, run, reason="QUALITY_LOW")
    assert refused.status_code == 409
    assert rewrite_route(api, run).status_code == 409
    owner_can_hold_a_lock_again(api, run.owner)


def test_the_adult_can_cancel_a_returned_run_at_any_time(api: VideoApi) -> None:
    run = new_script_run(api)
    make_rewritable(api, run)
    sweep(api, accepted(api, run))
    assert run_row(run.run_id)["run_state"] == "SCRIPT_REVIEW"
    assert cancel(api, run).status_code == 202
    assert run_row(run.run_id)["run_state"] in {"DELETE_PENDING", "DELETED"}
    assert lock_of(run.run_id) is None
    owner_can_hold_a_lock_again(api, run.owner)


def test_a_failed_generation_alone_never_opens_a_rewrite_on_a_run_that_is_not_waiting(
    api: VideoApi,
) -> None:
    """The gate reads ``SCRIPT_REVIEW`` first: a failed generation of a FAILED run (T-1a path,
    no return to the script review) stays refused, and a confirmed script with only an older
    failed request stays refused as in T-1b."""

    run = new_script_run(api)
    make_rewritable(api, run)
    generation_id = accepted(api, run)
    # the T-1a outcome (no flag): the generation fails and the run ends FAILED
    with api.sessions()() as session:
        progress = StoryVideoProgressService(SqlStoryVideoRepository(session), api.adapters)
        assert progress.apply(
            generation_id, ProgressEvent("ACCEPTED", "FAILED", safe_failure_code="OTHER")
        ).applied
    assert run_row(run.run_id)["run_state"] == "FAILED"
    refused = rewrite_route(api, run)
    assert refused.status_code == 409 and code_of(refused) == "INVALID_STATE_TRANSITION"
    assert [r["status"] for r in story_rows(run.run_id)] == ["CONFIRMED"]
