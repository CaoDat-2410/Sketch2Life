"""FEAT-066 goal v4 T-1b-fix: keep the current story and confirm it again, through the real routes.

SRS l.406 and l.1728 (after an unsuitable video the adult keeps the current story and confirms it
again, or asks for a rewrite within the limit), l.379 and l.382 (each video request needs its own
confirmation), l.255 BR-11 and l.2120 (a failed request counts toward the cap), l.258 BR-14 (a
revision is immutable: a confirmation is a new review row with the next epoch), l.405 and l.573
(three requests), l.1669 and l.1697-1699 (stale protection, idempotency). Every adult step is a
real route; only the deadline is the sweep with an injected clock. The app, the fixture runner and
the builders are the T-1b module's, so the database name must contain ``be1_acceptance`` and
``frc08_v3_t1b``. No provider, no sleep.
"""

# ruff: noqa: F811  (the imported fixtures are used as test arguments)

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import select

from sketch2life.infrastructure.story_run_lite import tables as story_tables
from tests.integration.story_video.test_story_deadline_routes_postgres import (  # noqa: F401
    accepted,
    sweep,
)
from tests.integration.story_video.test_video_commands_postgres import (  # noqa: F401
    VG,
    ScriptRun,
    VideoApi,
    _bind_api,
    _parallel,
    api,
    cancel,
    code_of,
    generations,
    headers,
    make_rewritable,
    new_script_run,
    rewrite_route,
    run_row,
    runner,
    sha,
    snapshot,
    story_rows,
    unsuitable,
    video_ready,
    video_request,
)

REVIEWS = story_tables.story_revision_reviews


def reviews(run_id: str) -> list[Any]:
    from tests.integration.story_video import test_video_commands_postgres as base

    assert base._API is not None
    with base._API.sessions()() as db:
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


def reconfirm(
    api: VideoApi,
    run: ScriptRun,
    *,
    key: str | None = None,
    number: int | None = None,
    digest: str | None = None,
) -> Any:
    """``script-confirmation`` of the latest story revision (a fresh key unless one is given)."""

    latest = story_rows(run.run_id)[-1]
    run.story_sha256 = str(latest["story_sha256"])
    return api.client.post(
        f"/v1/story-runs/{run.run_id}/script-confirmation",
        json={
            "expected_revision": number if number is not None else int(latest["revision_no"]),
            "story_sha256": digest if digest is not None else latest["story_sha256"],
        },
        headers=headers(run.owner, key or uuid4().hex),
    )


def detail(api: VideoApi, run: ScriptRun) -> dict[str, Any]:
    response = api.client.get(f"/v1/story-runs/{run.run_id}", headers=headers(run.owner))
    assert response.status_code == 200, response.text
    return dict(response.json()["story_run"])


def ask_and_render(api: VideoApi, run: ScriptRun, *, reason: str = "QUALITY_LOW") -> str:
    response = video_request(api, run, reason=reason)
    assert response.status_code == 202, response.text
    generation_id = str(response.json()["video_generation"]["generation_id"])
    final = runner(api).run_to_end(generation_id)
    assert final.record is not None and final.record.state == "READY"
    return generation_id


def keep_and_ask_again(api: VideoApi, run: ScriptRun, generation_id: str) -> str:
    """The adult marks the video unsuitable, keeps the story, confirms it and asks again."""

    marked = unsuitable(api, run, generation_id)
    assert marked.status_code == 200, marked.text
    assert detail(api, run)["story_confirmation_required"] is True
    confirmed = reconfirm(api, run)
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["story_run"]["story_confirmation_required"] is False
    return ask_and_render(api, run)


def add_generation(api: VideoApi, run: ScriptRun, state: str, number: int) -> str:
    """A direct row: an accepted request of ``state`` on the latest review of the latest story."""

    now = datetime.now(UTC)
    generation_id = str(uuid4())
    latest_review = reviews(run.run_id)[-1]
    with api.sessions().begin() as db:
        db.execute(
            VG.insert().values(
                video_generation_id=generation_id,
                story_run_id=run.run_id,
                story_revision_id=latest_review["story_revision_id"],
                story_review_id=latest_review["review_id"],
                generation_no=number,
                generation_kind="INITIAL" if number == 1 else "QUALITY_REGEN",
                state=state,
                request_idempotency_key_hash=sha(f"seed-{generation_id}"),
                request_fingerprint_sha256=sha(f"fp-{generation_id}"),
                target_script_hash=latest_review["target_story_sha256"],
                quality_reason_code=None if number == 1 else "QUALITY_LOW",
                compute_reservation_ref=f"res-{number}-{generation_id}",
                compute_released_at=now,
                billing_quota_usage_ref=f"usage-{number}-{generation_id}",
                job_ref=f"vjob_{uuid4().hex}",
                admission_started_at=now,
                accepted_at=now,
                completed_at=now,
                safe_failure_code="VIDEO_GENERATION_FAILED" if state == "FAILED" else None,
                generation_revision=3,
                created_at=now,
                updated_at=now,
            )
        )
    return generation_id


# ============================================================================ the way back
@pytest.mark.parametrize("rewrites", [0, 1, 3], ids=["revision-1", "revision-2", "revision-4"])
def test_the_adult_keeps_the_story_and_asks_again_until_the_cap(
    api: VideoApi, rewrites: int
) -> None:
    run, first = video_ready(api)
    make_rewritable(api, run)
    current = first
    if rewrites:
        assert unsuitable(api, run, first).status_code == 200
        for _ in range(rewrites):
            assert rewrite_route(api, run).status_code == 202
        assert len(story_rows(run.run_id)) == rewrites + 1
        assert reconfirm(api, run).status_code == 200
        current = ask_and_render(api, run)
    requests_so_far = 1 if not rewrites else 2
    story_ids = {str(row["story_revision_id"]) for row in story_rows(run.run_id)}
    latest_story = story_rows(run.run_id)[-1]
    revisions_before = [
        (r["revision_no"], r["status"], r["story_sha256"]) for r in story_rows(run.run_id)
    ]
    while requests_so_far < 3:
        current = keep_and_ask_again(api, run, current)
        requests_so_far += 1
    # the cap is spent: the mark that would need a fourth request is refused and the video stays
    refused = unsuitable(api, run, current)
    assert refused.status_code == 409 and code_of(refused) == "VIDEO_REGENERATION_LIMIT_REACHED"
    assert run_row(run.run_id)["run_state"] == "VIDEO_READY"
    # revisions are untouched (BR-14); the reviews of the latest revision are epochs 1..n
    assert [(r["revision_no"], r["status"], r["story_sha256"]) for r in story_rows(run.run_id)] == (
        revisions_before
    )
    assert {str(row["story_revision_id"]) for row in story_rows(run.run_id)} == story_ids
    on_latest = [
        r
        for r in reviews(run.run_id)
        if r["story_revision_id"] == latest_story["story_revision_id"]
    ]
    assert [r["review_epoch"] for r in on_latest] == list(range(1, len(on_latest) + 1))
    assert len(on_latest) == (3 if not rewrites else 2)
    # each accepted request consumed its own review
    consumed = [
        g["story_review_id"]
        for g in generations(run.run_id)
        if g["story_revision_id"] == latest_story["story_revision_id"]
    ]
    assert consumed == [r["review_id"] for r in on_latest]
    assert [g["generation_no"] for g in generations(run.run_id)] == [1, 2, 3]


def test_a_deadline_failure_can_be_kept_and_confirmed_again_at_any_revision(
    api: VideoApi,
) -> None:
    run = new_script_run(api)
    make_rewritable(api, run)
    first = accepted(api, run)
    assert sweep(api, first).deadline_failed >= 1
    row = run_row(run.run_id)
    assert row["run_state"] == "SCRIPT_REVIEW" and row["active_owner_parent_account_id"] is not None
    assert detail(api, run)["story_confirmation_required"] is True
    # the spent review is not reusable
    spent = video_request(api, run, reason="QUALITY_LOW")
    assert spent.status_code == 409 and code_of(spent) == "INVALID_STATE_TRANSITION"
    assert reconfirm(api, run).status_code == 200
    again = video_request(api, run, reason="QUALITY_LOW")
    assert again.status_code == 202, again.text
    assert [(g["generation_no"], g["state"]) for g in generations(run.run_id)] == [
        (1, "FAILED"),
        (2, "ACCEPTED"),
    ]


def test_a_safety_blocked_request_spends_its_review_like_a_failed_one(api: VideoApi) -> None:
    """The state the SAFETY_BLOCKED exit task will leave a run in: the run is back at the script
    review and the only request ended ``SAFETY_BLOCKED``."""

    run = new_script_run(api)
    add_generation(api, run, "SAFETY_BLOCKED", 1)
    assert detail(api, run)["story_confirmation_required"] is True
    assert reconfirm(api, run).status_code == 200
    assert [r["review_epoch"] for r in reviews(run.run_id)] == [1, 2]
    assert video_request(api, run, reason="QUALITY_LOW").status_code == 202


# ============================================================================ the refusals
def test_a_confirmed_story_with_an_unspent_review_is_not_confirmed_again(api: VideoApi) -> None:
    run = new_script_run(api)
    make_rewritable(api, run)
    before = snapshot(run.run_id)
    assert detail(api, run)["story_confirmation_required"] is False
    refused = reconfirm(api, run)
    assert refused.status_code == 409 and code_of(refused) == "INVALID_STATE_TRANSITION"
    assert snapshot(run.run_id) == before and len(reviews(run.run_id)) == 1


def test_a_second_confirmation_on_the_unspent_epoch_is_refused_and_the_rewrite_stays_open(
    api: VideoApi,
) -> None:
    run, first = video_ready(api)
    make_rewritable(api, run)
    assert unsuitable(api, run, first).status_code == 200
    assert reconfirm(api, run).status_code == 200  # epoch 2, nothing requested yet
    before = snapshot(run.run_id)
    again = reconfirm(api, run)
    assert again.status_code == 409 and code_of(again) == "INVALID_STATE_TRANSITION"
    assert snapshot(run.run_id) == before and [r["review_epoch"] for r in reviews(run.run_id)] == [
        1,
        2,
    ]
    assert detail(api, run)["story_confirmation_required"] is False
    # the per-revision question: the video of epoch 1 is spent, so the rewrite door is open
    rewritten = rewrite_route(api, run)
    assert rewritten.status_code == 202, rewritten.text
    assert [r["status"] for r in story_rows(run.run_id)] == ["SUPERSEDED", "DRAFT"]
    assert detail(api, run)["story_confirmation_required"] is True
    assert reconfirm(api, run).status_code == 200  # the new revision, epoch 1
    assert [(r["review_epoch"]) for r in reviews(run.run_id)][-1] == 1


def test_a_confirmation_at_three_accepted_requests_is_refused_with_the_limit(
    api: VideoApi,
) -> None:
    run = new_script_run(api, prior=2)  # requests 1 and 2 failed on earlier revisions
    add_generation(api, run, "FAILED", 3)
    before = snapshot(run.run_id)
    refused = reconfirm(api, run)
    assert refused.status_code == 409 and code_of(refused) == "VIDEO_REGENERATION_LIMIT_REACHED"
    assert snapshot(run.run_id) == before and len(reviews(run.run_id)) == 3


def test_a_hash_or_story_revision_mismatch_is_stale_with_the_latest_revision(
    api: VideoApi,
) -> None:
    run, first = video_ready(api)
    make_rewritable(api, run)
    assert unsuitable(api, run, first).status_code == 200
    before = snapshot(run.run_id)
    wrong_hash = reconfirm(api, run, digest="f" * 64)
    assert wrong_hash.status_code == 409 and code_of(wrong_hash) == "STALE_REVISION"
    assert wrong_hash.json()["current_version"] == 1
    assert snapshot(run.run_id) == before
    assert rewrite_route(api, run).status_code == 202  # revision 2 is the latest now
    old = reconfirm(api, run, number=1, digest=story_rows(run.run_id)[0]["story_sha256"])
    assert old.status_code == 409 and code_of(old) == "STALE_REVISION"
    assert old.json()["current_version"] == 2
    missing = reconfirm(api, run, number=4)
    assert missing.status_code == 409 and code_of(missing) == "STALE_REVISION"
    assert missing.json()["current_version"] == 2


def test_the_run_state_decides_before_anything_else(api: VideoApi) -> None:
    run, _first = video_ready(api)  # VIDEO_READY: not in the script review
    refused = reconfirm(api, run)
    assert refused.status_code == 409 and code_of(refused) == "INVALID_STATE_TRANSITION"
    assert len(reviews(run.run_id)) == 1
    stranger = api.client.post(
        f"/v1/story-runs/{run.run_id}/script-confirmation",
        json={"expected_revision": 1, "story_sha256": run.story_sha256},
        headers=headers(api.other_parent, uuid4().hex),
    )
    assert stranger.status_code == 404


# ============================================================================ idempotency
def test_a_replay_returns_the_stored_answer_and_a_reused_key_never_makes_a_new_epoch(
    api: VideoApi,
) -> None:
    run, first = video_ready(api)
    assert unsuitable(api, run, first).status_code == 200
    key = uuid4().hex
    confirmed = reconfirm(api, run, key=key)
    assert confirmed.status_code == 200, confirmed.text
    assert [r["review_epoch"] for r in reviews(run.run_id)] == [1, 2]
    before = snapshot(run.run_id)
    replay = reconfirm(api, run, key=key)
    assert replay.status_code == 200 and replay.json()["story_run"]["run_id"] == run.run_id
    assert snapshot(run.run_id) == before and [r["review_epoch"] for r in reviews(run.run_id)] == [
        1,
        2,
    ]
    # the same key with another payload is a conflict of intent, not a new epoch
    other = reconfirm(api, run, key=key, digest="e" * 64)
    assert other.status_code == 400 and code_of(other) == "INVALID_IDEMPOTENCY_KEY"
    assert snapshot(run.run_id) == before


def test_a_key_used_after_the_second_unsuitable_video_replays_the_old_answer(
    api: VideoApi,
) -> None:
    """The client rule: a fresh key for every confirmation. Reusing the first key after the next
    unsuitable video replays the old answer and writes no epoch (the review stays spent)."""

    run, first = video_ready(api)
    assert unsuitable(api, run, first).status_code == 200
    key = uuid4().hex
    assert reconfirm(api, run, key=key).status_code == 200
    second = ask_and_render(api, run)
    assert unsuitable(api, run, second).status_code == 200
    replay = reconfirm(api, run, key=key)
    assert replay.status_code == 200
    assert [r["review_epoch"] for r in reviews(run.run_id)] == [1, 2]
    assert detail(api, run)["story_confirmation_required"] is True
    assert reconfirm(api, run).status_code == 200  # a fresh key gives epoch 3
    assert [r["review_epoch"] for r in reviews(run.run_id)] == [1, 2, 3]


def test_two_parallel_confirmations_give_exactly_one_new_epoch(api: VideoApi) -> None:
    run, first = video_ready(api)
    assert unsuitable(api, run, first).status_code == 200
    results = _parallel(2, lambda _index: reconfirm(api, run))
    statuses = sorted(response.status_code for response in results)
    assert statuses == [200, 409], [r.text for r in results]
    refused = next(r for r in results if r.status_code == 409)
    assert code_of(refused) == "INVALID_STATE_TRANSITION"
    assert [r["review_epoch"] for r in reviews(run.run_id)] == [1, 2]


def test_the_confirmation_bumps_the_run_revision_and_the_idle_clock(api: VideoApi) -> None:
    run, first = video_ready(api)
    assert unsuitable(api, run, first).status_code == 200
    before = run_row(run.run_id)
    assert reconfirm(api, run).status_code == 200
    after = run_row(run.run_id)
    assert after["run_state"] == "SCRIPT_REVIEW" and after["job_state"] == "SUCCEEDED"
    assert after["revision"] == before["revision"] + 1 and after["version"] == before["version"] + 1
    assert after["updated_at"] > before["updated_at"]
    # a video request that still names the old run revision is stale
    stale = api.client.post(
        f"/v1/story-runs/{run.run_id}/video-generations",
        json={
            "expected_revision": int(before["revision"]),
            "story_sha256": run.story_sha256,
            "quality_reason_code": "QUALITY_LOW",
        },
        headers=headers(run.owner, uuid4().hex),
    )
    assert stale.status_code == 409 and code_of(stale) == "STALE_REVISION"
    assert stale.json()["current_version"] == after["revision"]
