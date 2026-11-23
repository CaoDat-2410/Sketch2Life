"""FEAT-066 goal v4 OPEN-A D8: a plan re-approval and a running Teacher run, on PostgreSQL.

SRS l.386 (an async result must match the Teacher activity and plan reference), l.2690-2699 (plan
re-approval: queued work is cancelled, running work is not built here, the READY output of the old
plan stays), l.1697-1699 (``STALE_REVISION`` and its ``current_version``). The fences are read-only:
Story asks which plan is approved and writes nothing to Lesson. Runs only against a disposable
database whose name contains ``be1_acceptance`` and ``frc08``; the video adapters are the accept-all
local pair and the renderer is the fixture one; nothing calls a provider.
"""

# ruff: noqa: F811  (the imported fixtures are used as test arguments)

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from test_teacher_run_create_postgres import _approve_plan  # type: ignore[import-not-found]
from video_support import (  # type: ignore[import-not-found]
    Env,
    VEnv,
    accepted_generation,
    api,  # noqa: F401 - fixture
    env,  # noqa: F401 - fixture
    generations,
    playback_token,
    request_video,
    run_row,
    runner,
    to_confirmed_script,
    to_ready,
    v,  # noqa: F401 - fixture
)

from sketch2life.domain.story_video.model import public_failure_code
from sketch2life.infrastructure.lesson_occurrences.tables import OCCURRENCES, PLAN_REVISIONS
from sketch2life.infrastructure.story_run_lite import tables as story_tables


def _reapprove(e: Env, run_id: str) -> int:
    """Approve a NEW plan revision of the run's occurrence; return its revision number."""
    occurrence = str(run_row(e, run_id)["occurrence_ref"])
    with e.sessions()() as db:
        head = int(
            db.execute(
                select(PLAN_REVISIONS.c.revision_no)
                .where(PLAN_REVISIONS.c.occurrence_id == occurrence)
                .order_by(PLAN_REVISIONS.c.revision_no.desc())
                .limit(1)
            ).scalar_one()
        )
    _, _, number, _ = _approve_plan(e.d, occurrence, head, "t1")
    assert number == head + 1
    return number


def _pin(e: Env, run_id: str) -> dict[str, Any]:
    inputs = story_tables.run_inputs
    with e.sessions()() as db:
        pin = db.execute(
            select(inputs.c.lesson_pin_snapshot)
            .where(inputs.c.run_id == run_id)
            .order_by(inputs.c.input_revision.desc())
            .limit(1)
        ).scalar_one()
    return dict(pin)


def _approved_pointer(e: Env, run_id: str) -> str:
    occurrence = str(run_row(e, run_id)["occurrence_ref"])
    with e.sessions()() as db:
        return str(
            db.execute(
                select(OCCURRENCES.c.approved_plan_revision_id).where(
                    OCCURRENCES.c.occurrence_id == occurrence
                )
            ).scalar_one()
        )


# ------------------------------------------------------------------ fence 1: the admission
def test_a_request_for_a_superseded_plan_is_409_with_the_approved_plan_number(v: VEnv) -> None:
    e = v.e
    run_id, digest = to_confirmed_script(e)
    pinned = _pin(e, run_id)["plan_revision_id"]
    number = _reapprove(e, run_id)
    assert _approved_pointer(e, run_id) != pinned
    refused = request_video(e, "t1", run_id, digest)
    assert refused.status_code == 409, refused.text
    body = refused.json()
    assert body["code"] == "STALE_REVISION" and body["current_version"] == number
    # nothing was written: no intent, the run is still reviewable
    assert generations(e, run_id) == []
    assert run_row(e, run_id)["run_state"] == "SCRIPT_REVIEW"


def test_a_request_for_the_current_plan_is_still_accepted(v: VEnv) -> None:
    e = v.e
    run_id, digest = to_confirmed_script(e)
    accepted = request_video(e, "t1", run_id, digest)
    assert accepted.status_code == 202, accepted.text


# ------------------------------------------------------------ fence 2: the worker-start steps
def test_an_accepted_generation_of_a_superseded_plan_is_failed_before_dispatch(v: VEnv) -> None:
    e = v.e
    run_id, _, generation_id = accepted_generation(v)
    _reapprove(e, run_id)
    result = runner(v).step(generation_id)
    assert result.applied is True and result.record is not None
    assert result.record.state == "FAILED" and result.record.safe_failure_code == "PLAN_SUPERSEDED"
    assert public_failure_code(result.record.safe_failure_code) == "VIDEO_TECHNICAL_FAILURE"
    (generation,) = generations(e, run_id)
    assert generation["state"] == "FAILED" and generation["started_at"] is None
    assert generation["generation_no"] == 1  # the accepted request still counts (no refund)
    # nothing had started: the compute reservation was RELEASED (not settled), and the accepted
    # quota receipt is kept: one admission, no second call, the reference still on the row
    assert [name for name, _ in v.reservation.calls] == ["reserve", "release"]
    assert generation["compute_released_at"] is not None
    assert len(v.quota.calls) == 1 and generation["billing_quota_usage_ref"] is not None
    row = run_row(e, run_id)
    assert row["run_state"] == "FAILED" and row["active_owner_teacher_id"] is None
    # the next step meets a settled generation: nothing is dispatched
    again = runner(v).step(generation_id)
    assert again.applied is False and again.reason == "SETTLED"


def test_a_queued_generation_of_a_superseded_plan_is_failed_at_the_next_start_step(
    v: VEnv,
) -> None:
    e = v.e
    run_id, _, generation_id = accepted_generation(v)
    queued = runner(v).step(generation_id)
    assert queued.applied and queued.record is not None and queued.record.state == "QUEUED"
    _reapprove(e, run_id)
    result = runner(v).step(generation_id)
    assert result.applied and result.record is not None and result.record.state == "FAILED"
    assert result.record.safe_failure_code == "PLAN_SUPERSEDED"
    assert run_row(e, run_id)["run_state"] == "FAILED"


def test_a_generation_that_is_already_running_finishes_with_its_old_pin(v: VEnv) -> None:
    e = v.e
    run_id, _, generation_id = accepted_generation(v)
    pinned = _pin(e, run_id)
    for _ in range(2):  # ACCEPTED -> QUEUED -> GENERATING
        assert runner(v).step(generation_id).applied
    assert generations(e, run_id)[0]["state"] == "GENERATING"
    _reapprove(e, run_id)
    final = runner(v).run_to_end(generation_id)
    assert final.record is not None and final.record.state == "READY", final
    assert run_row(e, run_id)["run_state"] == "VIDEO_READY"
    assert _pin(e, run_id) == pinned  # the run keeps its old pin (DEV-4: no cancellation built)


def test_the_ready_output_of_the_old_plan_is_not_hidden_and_a_current_run_is_not_fenced(
    v: VEnv,
) -> None:
    e = v.e
    run_id, _, _ = to_ready(v)
    _reapprove(e, run_id)
    assert run_row(e, run_id)["run_state"] == "VIDEO_READY"
    token = playback_token(e, "t1", run_id)
    assert token.status_code == 200, token.text
    assert len(generations(e, run_id)) == 1  # no second generation, no claim written here


def test_a_fixture_run_walks_to_ready_when_the_plan_never_changed(v: VEnv) -> None:
    e = v.e
    run_id, _, generation_id = accepted_generation(v)
    final = runner(v).run_to_end(generation_id)
    assert final.record is not None and final.record.state == "READY"
    assert run_row(e, run_id)["run_state"] == "VIDEO_READY"
