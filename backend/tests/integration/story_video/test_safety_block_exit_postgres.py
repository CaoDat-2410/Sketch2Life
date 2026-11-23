"""FEAT-066 goal v4 SAFETY_BLOCKED exit: a blocked video returns the adult to the script review.

SRS l.420 and l.2197 (a blocked output gets no playback token and the adult goes back to the
script), l.280 BR-36, l.408, l.1176 AT-03, l.578 FR-AI-12 (the blocked output is hidden and the
reason is a safe code), l.2120 item 6 and l.255 BR-11 (a blocked request counts toward the cap and
the run goes back to the script review), l.406 and l.1728 (keep the story and confirm it again, or
rewrite within the limit), l.394 (the idle clock). Owner decision C11 reverses T-1d1-fix DEC-3: the
run state ``SAFETY_BLOCKED`` is no longer written; rows written before stay valid (D6). Every adult
step is a real route; the block is made by the fixture runner. The app, the runner and the builders
are the T-1b module's, so the database name must contain ``be1_acceptance`` and ``frc08_v3_t1b``.
No provider, no sleep.
"""

# ruff: noqa: F811  (the imported fixtures are used as test arguments)

from __future__ import annotations

from datetime import timedelta
from typing import Any
from uuid import uuid4

from sketch2life.application.ports.story_video import ProgressEvent, VideoRenderResult
from sketch2life.application.services.story_run_video import StoryVideoProgressService
from sketch2life.infrastructure.story_video.fixture_runner import FixtureVideoRenderer
from sketch2life.infrastructure.story_video.repository import SqlStoryVideoRepository
from tests.integration.story_video.test_story_deadline_routes_postgres import (  # noqa: F401
    HOURS_168,
    accepted,
    idle_sweep,
)
from tests.integration.story_video.test_story_reconfirm_postgres import (  # noqa: F401
    add_generation,
    ask_and_render,
    detail,
    reconfirm,
    reviews,
)
from tests.integration.story_video.test_video_commands_postgres import (  # noqa: F401
    ScriptRun,
    VideoApi,
    _bind_api,
    api,
    cancel,
    code_of,
    complete,
    generations,
    headers,
    make_rewritable,
    new_script_run,
    rewrite_route,
    run_row,
    runner,
    snapshot,
    story_rows,
    unsuitable,
    video_request,
)


def unsafe_renderer(generation_id: str) -> FixtureVideoRenderer:
    renderer = FixtureVideoRenderer()
    renderer.results[generation_id] = VideoRenderResult(
        content=b"x", media_type="video/mp4", safety_passed=False, safety_finding_codes=("F-1",)
    )
    return renderer


def block(api: VideoApi, run: ScriptRun, *, reason: str | None = None) -> str:
    """One video request through the real route that the safety check blocks; returns its id."""

    response = video_request(api, run, reason=reason)
    assert response.status_code == 202, response.text
    generation_id = str(response.json()["video_generation"]["generation_id"])
    final = runner(api, unsafe_renderer(generation_id)).run_to_end(generation_id)
    assert final.record is not None and final.record.state == "SAFETY_BLOCKED", final
    return generation_id


def token(api: VideoApi, run: ScriptRun) -> Any:
    return api.client.post(
        f"/v1/story-runs/{run.run_id}/playback-token", headers=headers(run.owner)
    )


def lock_of(run_id: str) -> Any:
    return run_row(run_id)["active_owner_parent_account_id"]


# ============================================================================ the exit
def test_a_blocked_video_returns_the_run_to_the_script_review_and_keeps_the_lock(
    api: VideoApi,
) -> None:
    run = new_script_run(api)
    generation_id = block(api, run)
    row = run_row(run.run_id)
    assert row["run_state"] == "SCRIPT_REVIEW" and row["job_state"] == "FAILED"
    assert row["adult_wait_started_at"] is not None and row["error_code"] == "SAFETY_BLOCKED"
    assert lock_of(run.run_id) is not None and row["finished_at"] is None
    (stored,) = generations(run.run_id)
    assert stored["video_generation_id"] == generation_id and stored["state"] == "SAFETY_BLOCKED"
    assert stored["safety_validation_state"] == "FAILED" and stored["output_asset_ref"] is None
    assert stored["safe_failure_code"] == "SAFETY_BLOCKED" and stored["generation_no"] == 1
    body = detail(api, run)
    assert body["run_state"] == "SCRIPT_REVIEW" and body["story_confirmation_required"] is True
    assert body["error_code"] == "VIDEO_SAFETY_BLOCKED"
    video = body["video"]
    assert video["state"] == "SAFETY_BLOCKED" and video["playback"]["state"] == "UNAVAILABLE"
    assert video["job"]["error_code"] == "VIDEO_SAFETY_BLOCKED"
    assert video["video_requests_used"] == 1 and video["video_requests_remaining"] == 2
    assert "VIDEO_SAFETY_BLOCKED" in [item["event"] for item in video_timeline(api, run)]
    # no playback token for a blocked output; nothing else can be marked or completed
    refused = token(api, run)
    assert refused.status_code == 409 and code_of(refused) == "INVALID_STATE_TRANSITION"
    for response in (complete(api, run), unsuitable(api, run, generation_id)):
        assert response.status_code == 409 and code_of(response) == "INVALID_STATE_TRANSITION"


def video_timeline(api: VideoApi, run: ScriptRun) -> list[dict[str, Any]]:
    response = api.client.get(f"/v1/story-runs/{run.run_id}", headers=headers(run.owner))
    assert response.status_code == 200, response.text
    return list(response.json()["story_run"]["timeline"])


def test_the_adult_keeps_the_story_confirms_it_again_and_asks_again_after_a_block(
    api: VideoApi,
) -> None:
    run = new_script_run(api)
    block(api, run)
    # the blocked request spent its review: asking again needs a new confirmation first
    spent = video_request(api, run, reason="QUALITY_LOW")
    assert spent.status_code == 409 and code_of(spent) == "INVALID_STATE_TRANSITION"
    assert reconfirm(api, run).status_code == 200
    assert [r["review_epoch"] for r in reviews(run.run_id)] == [1, 2]
    assert detail(api, run)["story_confirmation_required"] is False
    again = video_request(api, run, reason="QUALITY_LOW")
    assert again.status_code == 202, again.text
    assert again.json()["video_generation"]["generation_no"] == 2
    assert again.json()["video_generation"]["kind"] == "QUALITY_REGEN"
    # the second request runs to the end like any other
    second = str(again.json()["video_generation"]["generation_id"])
    final = runner(api).run_to_end(second)
    assert final.record is not None and final.record.state == "READY"
    assert run_row(run.run_id)["run_state"] == "VIDEO_READY"
    assert token(api, run).status_code == 200  # the first playable video of this run


def test_the_adult_can_rewrite_after_a_block_and_confirm_the_new_story(api: VideoApi) -> None:
    run = new_script_run(api)
    make_rewritable(api, run)
    block(api, run)
    rewritten = rewrite_route(api, run)
    assert rewritten.status_code == 202, rewritten.text
    assert [r["status"] for r in story_rows(run.run_id)] == ["SUPERSEDED", "DRAFT"]
    assert run_row(run.run_id)["run_state"] == "SCRIPT_REVIEW"
    assert detail(api, run)["story_confirmation_required"] is True
    assert reconfirm(api, run).status_code == 200  # the new revision, epoch 1
    ready = ask_and_render(api, run)
    assert [(g["generation_no"], g["state"]) for g in generations(run.run_id)] == [
        (1, "SAFETY_BLOCKED"),
        (2, "READY"),
    ]
    assert generations(run.run_id)[-1]["video_generation_id"] == ready


def test_three_blocked_requests_leave_the_run_in_the_review_with_the_lock_at_the_cap(
    api: VideoApi,
) -> None:
    """D3 (SRS l.2120 item 6: the bounded cap, then the script review) and D3b: at the cap the
    envelope no longer asks for a confirmation that could lead to no video."""

    run = new_script_run(api)
    block(api, run)
    assert detail(api, run)["story_confirmation_required"] is True
    assert reconfirm(api, run).status_code == 200
    block(api, run, reason="QUALITY_LOW")
    assert detail(api, run)["story_confirmation_required"] is True  # two used, one request left
    assert reconfirm(api, run).status_code == 200
    block(api, run, reason="QUALITY_LOW")
    row = run_row(run.run_id)
    assert row["run_state"] == "SCRIPT_REVIEW" and lock_of(run.run_id) is not None
    assert row["finished_at"] is None and row["error_code"] == "SAFETY_BLOCKED"
    assert [(g["generation_no"], g["state"]) for g in generations(run.run_id)] == [
        (1, "SAFETY_BLOCKED"),
        (2, "SAFETY_BLOCKED"),
        (3, "SAFETY_BLOCKED"),
    ]
    body = detail(api, run)
    assert body["story_confirmation_required"] is False
    video = body["video"]
    assert video["video_requests_used"] == 3 and video["video_requests_remaining"] == 0
    before = snapshot(run.run_id)
    refused = reconfirm(api, run)
    assert refused.status_code == 409 and code_of(refused) == "VIDEO_REGENERATION_LIMIT_REACHED"
    assert video_request(api, run, reason="QUALITY_LOW").status_code == 409
    assert snapshot(run.run_id) == before and len(generations(run.run_id)) == 3
    # the way on is to stop the run: it frees the lock
    assert cancel(api, run).status_code == 202
    assert run_row(run.run_id)["run_state"] == "DELETE_PENDING" and lock_of(run.run_id) is None


def test_a_blocked_run_closes_abandoned_after_168_hours_like_any_wait(api: VideoApi) -> None:
    run = new_script_run(api)
    block(api, run)
    assert idle_sweep(api, run, after=HOURS_168 - timedelta(seconds=1)).errors == 0
    assert run_row(run.run_id)["run_state"] == "SCRIPT_REVIEW"
    assert idle_sweep(api, run, after=HOURS_168).errors == 0
    closed = run_row(run.run_id)
    assert closed["run_state"] == "ABANDONED" and lock_of(run.run_id) is None
    assert generations(run.run_id)[0]["state"] == "SAFETY_BLOCKED"  # the unit stays spent


def test_a_duplicate_or_late_block_callback_changes_nothing(api: VideoApi) -> None:
    run = new_script_run(api)
    generation_id = block(api, run)
    before = snapshot(run.run_id)
    session = api.sessions()()
    try:
        late = StoryVideoProgressService(SqlStoryVideoRepository(session), api.adapters).apply(
            generation_id,
            ProgressEvent(
                "SAFETY_VALIDATING", "SAFETY_BLOCKED", safe_failure_code="SAFETY_BLOCKED"
            ),
        )
    finally:
        session.close()
    assert late.applied is False and late.reason == "STALE"
    assert snapshot(run.run_id) == before


def test_a_block_event_without_a_code_stores_the_default_safety_code(api: VideoApi) -> None:
    run = new_script_run(api)
    generation_id = accepted(api, run)
    session = api.sessions()()
    try:
        service = StoryVideoProgressService(SqlStoryVideoRepository(session), api.adapters)
        previous = "ACCEPTED"
        for step in ("QUEUED", "GENERATING", "TECHNICAL_VALIDATING", "SAFETY_VALIDATING"):
            assert service.apply(generation_id, ProgressEvent(previous, step)).applied
            previous = step
        assert service.apply(
            generation_id,
            ProgressEvent("SAFETY_VALIDATING", "SAFETY_BLOCKED", safety_finding_codes=("F-2",)),
        ).applied
    finally:
        session.close()
    (stored,) = generations(run.run_id)
    assert stored["safe_failure_code"] == "SAFETY_BLOCKED"
    assert stored["safety_finding_codes"] == ["F-2"]
    assert run_row(run.run_id)["error_code"] == "SAFETY_BLOCKED"
    body = detail(api, run)
    assert body["run_state"] == "SCRIPT_REVIEW" and body["error_code"] == "VIDEO_SAFETY_BLOCKED"
    assert body["video"]["job"]["error_code"] == "VIDEO_SAFETY_BLOCKED"


# ============================================================================ legacy rows (D6)
def legacy_blocked_run(api: VideoApi) -> ScriptRun:
    """A row written before the exit: the run state ``SAFETY_BLOCKED`` with a blocked request."""

    run = new_script_run(api, run_state="SAFETY_BLOCKED")
    add_generation(api, run, "SAFETY_BLOCKED", 1)
    return run


def test_a_legacy_blocked_row_can_confirm_the_story_again_and_move_on(api: VideoApi) -> None:
    run = legacy_blocked_run(api)
    assert run_row(run.run_id)["run_state"] == "SAFETY_BLOCKED"
    assert detail(api, run)["story_confirmation_required"] is True  # widened in one place
    # the request is refused until the story is confirmed again (the review is spent)
    spent = video_request(api, run, reason="QUALITY_LOW")
    assert spent.status_code == 409 and code_of(spent) == "INVALID_STATE_TRANSITION"
    assert run_row(run.run_id)["run_state"] == "SAFETY_BLOCKED"
    assert reconfirm(api, run).status_code == 200
    after = run_row(run.run_id)
    assert after["run_state"] == "SCRIPT_REVIEW" and after["job_state"] == "SUCCEEDED"
    assert video_request(api, run, reason="QUALITY_LOW").status_code == 202


def test_a_legacy_blocked_row_can_be_rewritten(api: VideoApi) -> None:
    run = legacy_blocked_run(api)
    make_rewritable(api, run)
    rewritten = rewrite_route(api, run)
    assert rewritten.status_code == 202, rewritten.text
    assert run_row(run.run_id)["run_state"] == "SCRIPT_REVIEW"  # the generator ran
    assert [r["status"] for r in story_rows(run.run_id)] == ["SUPERSEDED", "DRAFT"]


def test_a_legacy_blocked_row_still_closes_abandoned_after_168_hours(api: VideoApi) -> None:
    run = legacy_blocked_run(api)
    assert idle_sweep(api, run, after=HOURS_168 - timedelta(seconds=1)).errors == 0
    assert run_row(run.run_id)["run_state"] == "SAFETY_BLOCKED"
    assert idle_sweep(api, run, after=HOURS_168).errors == 0
    closed = run_row(run.run_id)
    assert closed["run_state"] == "ABANDONED" and lock_of(run.run_id) is None


def test_a_stranger_still_gets_the_uniform_404_on_a_blocked_run(api: VideoApi) -> None:
    run = new_script_run(api)
    block(api, run)
    before = snapshot(run.run_id)
    stranger = api.client.post(
        f"/v1/story-runs/{run.run_id}/script-confirmation",
        json={"expected_revision": 1, "story_sha256": run.story_sha256},
        headers=headers(api.other_parent, uuid4().hex),
    )
    assert stranger.status_code == 404
    assert snapshot(run.run_id) == before
