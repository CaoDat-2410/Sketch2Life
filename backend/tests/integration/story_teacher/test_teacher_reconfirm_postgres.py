"""FEAT-066 goal v4 T-1b-fix: a Teacher run keeps its story and confirms it again, on PostgreSQL.

SRS l.406 and l.1728 (keep the current story and confirm it again, or rewrite within the limit),
l.255 BR-11 and l.2120 (a failed request counts and the run returns to the script review), l.386
and l.2690-2699 (a replaced plan fences new requests; the fence is read-only and sits on the video
request). The Teacher route is the same guarded route as the Parent one (T-4b2). Runs only against
a disposable database whose name contains ``be1_acceptance`` and ``frc08``; the video adapters are
the accept-all local pair and the renderer is the fixture one; nothing calls a provider.
"""

# ruff: noqa: F811  (the imported fixtures are used as test arguments)

from __future__ import annotations

from datetime import timedelta
from typing import Any

from sqlalchemy import select
from test_teacher_plan_fence_postgres import _reapprove  # type: ignore[import-not-found]
from test_teacher_run_sweepers_postgres import (  # type: ignore[import-not-found]
    DEADLINE,
    accepted_at,
    step_to,
    sweep,
)
from video_support import (  # type: ignore[import-not-found]
    Env,
    VEnv,
    accepted_generation,
    api,  # noqa: F401 - fixture
    cancel,
    confirm_script,
    env,  # noqa: F401 - fixture
    generations,
    mark_unsuitable,
    request_video,
    rewrite,
    run_row,
    story_rows,
    to_ready,
    v,  # noqa: F401 - fixture
    who_headers,
)

from sketch2life.infrastructure.story_run_lite import tables as story_tables

REVIEWS = story_tables.story_revision_reviews


def reviews(e: Env, run_id: str) -> list[Any]:
    with e.sessions()() as db:
        return list(
            db.execute(
                select(REVIEWS)
                .join(
                    story_tables.story_revisions,
                    story_tables.story_revisions.c.story_revision_id == REVIEWS.c.story_revision_id,
                )
                .where(REVIEWS.c.run_id == run_id)
                .order_by(story_tables.story_revisions.c.revision_no, REVIEWS.c.review_epoch)
            )
            .mappings()
            .all()
        )


def view(e: Env, run_id: str) -> dict[str, Any]:
    response = e.d.client.get(f"/v1/story-runs/{run_id}", headers=who_headers(e, "t1"))
    assert response.status_code == 200, response.text
    return dict(response.json()["story_run"])


def test_a_teacher_keeps_the_story_and_asks_again_with_a_new_review_epoch(v: VEnv) -> None:
    e = v.e
    run_id, digest, first = to_ready(v)
    assert view(e, run_id)["story_confirmation_required"] is False
    assert mark_unsuitable(e, "t1", run_id, first).status_code == 200
    assert view(e, run_id)["story_confirmation_required"] is True
    # the spent review is not reusable
    spent = request_video(e, "t1", run_id, digest, reason="QUALITY_LOW")
    assert spent.status_code == 409 and spent.json()["code"] == "INVALID_STATE_TRANSITION"
    again = confirm_script(e, "t1", run_id, digest, number=1)
    assert again.status_code == 200, again.text
    assert again.json()["story_run"]["story_confirmation_required"] is False
    assert [r["review_epoch"] for r in reviews(e, run_id)] == [1, 2]
    (revision,) = story_rows(e, run_id)
    assert revision["status"] == "CONFIRMED" and revision["story_sha256"] == digest
    second = request_video(e, "t1", run_id, digest, reason="QUALITY_LOW")
    assert second.status_code == 202, second.text
    assert second.json()["video_generation"]["generation_no"] == 2
    # nothing to confirm while the request runs, and no second confirmation without a spent one
    again_too = confirm_script(e, "t1", run_id, digest, number=1)
    assert again_too.status_code == 409
    assert again_too.json()["code"] == "INVALID_STATE_TRANSITION"


def test_a_teacher_deadline_return_can_be_kept_and_confirmed_again(v: VEnv) -> None:
    e = v.e
    run_id, digest, generation_id = accepted_generation(v)
    step_to(v, generation_id, "GENERATING")
    sweep(v, accepted_at(e, generation_id) + DEADLINE + timedelta(seconds=1))
    row = run_row(e, run_id)
    assert row["run_state"] == "SCRIPT_REVIEW" and row["active_owner_teacher_id"] is not None
    assert view(e, run_id)["story_confirmation_required"] is True
    assert confirm_script(e, "t1", run_id, digest, number=1).status_code == 200
    assert [r["review_epoch"] for r in reviews(e, run_id)] == [1, 2]
    assert request_video(e, "t1", run_id, digest, reason="QUALITY_LOW").status_code == 202


def test_a_teacher_can_still_rewrite_after_confirming_the_spent_story_again(v: VEnv) -> None:
    e = v.e
    run_id, digest, first = to_ready(v)
    assert mark_unsuitable(e, "t1", run_id, first).status_code == 200
    assert confirm_script(e, "t1", run_id, digest, number=1).status_code == 200
    assert rewrite(e, "t1", run_id, revision=1).status_code == 202
    assert [r["status"] for r in story_rows(e, run_id)] == ["SUPERSEDED", "DRAFT"]
    assert view(e, run_id)["story_confirmation_required"] is True


def test_a_replaced_plan_is_not_fenced_at_the_confirmation_only_at_the_next_request(
    v: VEnv,
) -> None:
    """D13: the fence stays on the video request. The confirmation of a Teacher run whose plan was
    replaced is accepted (200); the next request is 409 ``STALE_REVISION`` with the plan number,
    and nothing the Teacher can confirm or rewrite changes that: the way out is to cancel."""

    e = v.e
    run_id, digest, first = to_ready(v)
    assert mark_unsuitable(e, "t1", run_id, first).status_code == 200
    number = _reapprove(e, run_id)
    confirmed = confirm_script(e, "t1", run_id, digest, number=1)
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["story_run"]["story_confirmation_required"] is False
    refused = request_video(e, "t1", run_id, digest, reason="QUALITY_LOW")
    assert refused.status_code == 409, refused.text
    assert (
        refused.json()["code"] == "STALE_REVISION" and refused.json()["current_version"] == number
    )
    assert len(generations(e, run_id)) == 1  # nothing was written
    assert cancel(e, "t1", run_id).status_code == 202
