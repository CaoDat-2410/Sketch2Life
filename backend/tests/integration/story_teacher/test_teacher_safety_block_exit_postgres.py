"""FEAT-066 goal v4 SAFETY_BLOCKED exit: a Teacher run returns to the script review (PostgreSQL).

SRS l.420 and l.2197 (a blocked output gets no playback token and the adult goes back to the
script), l.552 FR-T-13 and l.1792 (a failed video leaves the occurrence slot free; a replacement
run needs the blocked run stopped first), l.2120 item 6 (a blocked request counts and the run goes
back to the script review), l.406 and l.1728 (keep the story and confirm it again). The Teacher
route is the same guarded route as the Parent one (T-4b2). Runs only against a disposable database
whose name contains ``be1_acceptance`` and ``frc08``; the video adapters are the accept-all local
pair and the renderer is the fixture one; nothing calls a provider.
"""

# ruff: noqa: F811  (the imported fixtures are used as test arguments)

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from test_teacher_run_create_postgres import occurrence_row  # type: ignore[import-not-found]
from test_teacher_run_video_postgres import post_create_ok  # type: ignore[import-not-found]
from video_support import (  # type: ignore[import-not-found]
    Env,
    VEnv,
    accepted_generation,
    api,  # noqa: F401 - fixture
    cancel,
    complete,
    confirm_script,
    env,  # noqa: F401 - fixture
    generations,
    mark_unsuitable,
    playback_token,
    request_video,
    run_row,
    runner,
    v,  # noqa: F401 - fixture
    who_headers,
)

from sketch2life.application.ports.story_video import VideoRenderResult
from sketch2life.infrastructure.story_run_lite import tables as story_tables
from sketch2life.infrastructure.story_video.fixture_runner import FixtureVideoRenderer

REVIEWS = story_tables.story_revision_reviews


def reviews(e: Env, run_id: str) -> list[Any]:
    with e.sessions()() as db:
        return list(
            db.execute(
                select(REVIEWS).where(REVIEWS.c.run_id == run_id).order_by(REVIEWS.c.review_epoch)
            )
            .mappings()
            .all()
        )


def view(e: Env, run_id: str) -> dict[str, Any]:
    response = e.d.client.get(f"/v1/story-runs/{run_id}", headers=who_headers(e, "t1"))
    assert response.status_code == 200, response.text
    return dict(response.json()["story_run"])


def blocked_run(v: VEnv) -> tuple[str, str, str]:
    """An accepted request that the safety check blocks: ``(run_id, digest, generation_id)``."""

    run_id, digest, generation_id = accepted_generation(v)
    renderer = FixtureVideoRenderer()
    renderer.results[generation_id] = VideoRenderResult(
        content=b"x", media_type="video/mp4", safety_passed=False, safety_finding_codes=("F-1",)
    )
    final = runner(v, renderer).run_to_end(generation_id)
    assert final.record is not None and final.record.state == "SAFETY_BLOCKED", final
    return run_id, digest, generation_id


def test_a_blocked_teacher_run_returns_to_the_script_review_and_keeps_the_lock(v: VEnv) -> None:
    e = v.e
    run_id, _digest, generation_id = blocked_run(v)
    row = run_row(e, run_id)
    assert row["run_state"] == "SCRIPT_REVIEW" and row["job_state"] == "FAILED"
    assert row["error_code"] == "SAFETY_BLOCKED" and row["adult_wait_started_at"] is not None
    assert row["active_owner_teacher_id"] == e.d.accounts["t1"]  # the lock is held (D5)
    (stored,) = generations(e, run_id)
    assert stored["video_generation_id"] == generation_id and stored["state"] == "SAFETY_BLOCKED"
    occurrence = occurrence_row(e.d, row["occurrence_ref"])
    assert occurrence["sample_slot_state"] == "AVAILABLE"  # a failed video leaves the slot free
    body = view(e, run_id)
    assert body["run_state"] == "SCRIPT_REVIEW" and body["story_confirmation_required"] is True
    assert body["video"]["state"] == "SAFETY_BLOCKED"
    assert body["video"]["job"]["error_code"] == "VIDEO_SAFETY_BLOCKED"
    assert body["video"]["playback"]["state"] == "UNAVAILABLE"
    refused = playback_token(e, "t1", run_id)
    assert refused.status_code == 409 and refused.json()["code"] == "INVALID_STATE_TRANSITION"
    unsuitable = mark_unsuitable(e, "t1", run_id, generation_id)
    assert unsuitable.status_code == 409
    assert unsuitable.json()["code"] == "INVALID_STATE_TRANSITION"
    assert complete(e, "t1", run_id).status_code == 409
    # a replacement run needs the blocked run stopped first (the lock), then it is possible
    assert post_create_ok(e) is False
    assert cancel(e, "t1", run_id).status_code == 202
    assert run_row(e, run_id)["active_owner_teacher_id"] is None
    assert post_create_ok(e) is True


def test_a_teacher_keeps_the_story_after_a_block_and_asks_again(v: VEnv) -> None:
    e = v.e
    run_id, digest, _generation_id = blocked_run(v)
    spent = request_video(e, "t1", run_id, digest, reason="QUALITY_LOW")
    assert spent.status_code == 409 and spent.json()["code"] == "INVALID_STATE_TRANSITION"
    again = confirm_script(e, "t1", run_id, digest, number=1)
    assert again.status_code == 200, again.text
    assert again.json()["story_run"]["story_confirmation_required"] is False
    assert [r["review_epoch"] for r in reviews(e, run_id)] == [1, 2]
    second = request_video(e, "t1", run_id, digest, reason="QUALITY_LOW")
    assert second.status_code == 202, second.text
    assert second.json()["video_generation"]["generation_no"] == 2
