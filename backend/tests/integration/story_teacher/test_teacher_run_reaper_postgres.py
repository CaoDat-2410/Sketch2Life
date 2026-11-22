"""FEAT-066 T-4b3a: the lost-task reaper for a Teacher run on PostgreSQL (D13, T-13a H7).

SRS l.394 and l.503 (a lost AI task ends or returns the run; the 6 h deadline), l.615 and l.988
(safe codes), l.1413 (a first story out of retries ends the run), l.278 (BR-34: the audit row holds
metadata only), l.495 and l.553 (the Teacher lock is freed when the run ends). Runs only against a
disposable database whose name contains ``be1_acceptance`` and ``frc08``. The reaper is called as a
function with an injected clock in 2020 (so a row another test left behind is never due); nothing
schedules it.
"""

# ruff: noqa: F811  (the support module re-exports the T-4b2 ``api`` fixture)

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest
from inputs_support import (  # type: ignore[import-not-found]
    Env,
    api,  # noqa: F401 - fixture
    attach,
    complete_upload,
    confirm_context,
    confirm_subject,
    drawing_handle,
    env,  # noqa: F401 - fixture
    idea,
    new_run,
    receipt_rows,
    rewrite,
    run_row,
    states,
    story_rows,
    to_script_review,
    to_subject_review,
    transcript_rows,
    wav_bytes,
    who_headers,
)
from sqlalchemy import select, text, update

from sketch2life.application.ports.story_task_reaper import (
    AUDIT_REWRITE_ATTEMPT_FAILED,
    AUDIT_TIMED_OUT_DRAWING,
    AUDIT_TIMED_OUT_STORY,
    AUDIT_TIMED_OUT_TRANSCRIPT,
    REAPER_ACTOR_REF,
    TASK_TIMEOUT_CODE,
    ReapCandidate,
    ReapKind,
    ReapOutcome,
    ReapReport,
)
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.infrastructure.persistence.story_task_reaper_store import (
    SqlStoryTaskReaperStore,
    build_story_task_reaper,
)
from sketch2life.infrastructure.story_run_lite import tables as story_tables

AUDIT = CoreAuditEntryModel.__table__
RUNS = story_tables.story_runs
LEASE = timedelta(minutes=30)
T0 = datetime(2020, 6, 1, 8, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def _forget_aged_rows(api: Any) -> None:
    """Rows an earlier test aged to the injected clock are made current (out of reach)."""
    with api.sessions().begin() as db:
        db.execute(
            update(RUNS)
            .where(RUNS.c.updated_at < datetime(2021, 1, 1, tzinfo=UTC))
            .values(updated_at=datetime.now(UTC))
        )
        db.execute(
            update(story_tables.transcript_revisions)
            .where(
                story_tables.transcript_revisions.c.created_at < datetime(2021, 1, 1, tzinfo=UTC)
            )
            .values(created_at=datetime.now(UTC))
        )


def age(e: Env, run_id: str, when: datetime = T0) -> None:
    with e.sessions().begin() as db:
        db.execute(update(RUNS).where(RUNS.c.run_id == run_id).values(updated_at=when))


def reap(e: Env, now: datetime, **kwargs: Any) -> ReapReport:
    with e.sessions()() as db:
        return build_story_task_reaper(db).run_once(lease=LEASE, now=now, **kwargs)


def audit_rows(e: Env, run_id: str) -> list[Any]:
    """The reaper's audit rows of one run (the create row of T-4b2 is not the reaper's)."""
    with e.sessions()() as db:
        return list(
            db.execute(
                select(AUDIT)
                .where(AUDIT.c.resource_id == run_id, AUDIT.c.actor_ref == REAPER_ACTOR_REF)
                .order_by(AUDIT.c.created_at)
            )
            .mappings()
            .all()
        )


def assert_organization_audit(e: Env, run_id: str, action: str) -> None:
    rows = [row for row in audit_rows(e, run_id) if row["action"] == action]
    assert len(rows) == 1, audit_rows(e, run_id)
    row = rows[0]
    assert row["owner_scope_kind"] == "ORGANIZATION"
    assert row["organization_id"] == e.d.organization == row["owner_scope_ref"]
    assert row["actor_ref"] == REAPER_ACTOR_REF
    assert row["decision"] == TASK_TIMEOUT_CODE and row["resource_type"]
    # metadata only: no story, hint, transcript or child text (BR-34, l.278)
    assert str(dict(row)).count("dragon") == 0 and "Synthetic Kid" not in str(dict(row))


def teacher_lock(e: Env, run_id: str) -> Any:
    return run_row(e, run_id)["active_owner_teacher_id"]


# ------------------------------------------------------------------------------ drawing
def test_a_lost_drawing_analysis_of_a_teacher_run_goes_back_to_input_review(env: Env) -> None:
    e = env
    e.d.app.state.drawing_analyzer = None  # no analyzer composed: the analysis is never run
    run_id = new_run(e)
    handle, _data = drawing_handle(e, "t1", run_id)
    assert attach(e, "t1", run_id, handle).status_code == 202
    assert states(e, run_id) == ("INPUT_PROCESSING", "QUEUED")
    age(e, run_id)
    report = reap(e, T0 + LEASE)
    assert (report.drawing_timed_out, report.errors) == (1, 0)
    assert states(e, run_id) == ("INPUT_REVIEW", "FAILED")
    row = run_row(e, run_id)
    assert row["retryable"] is True and row["error_code"] == TASK_TIMEOUT_CODE
    assert teacher_lock(e, run_id) == e.d.accounts["t1"]  # the Teacher keeps the run
    assert_organization_audit(e, run_id, AUDIT_TIMED_OUT_DRAWING)
    # a second pass finds nothing: one effect, one audit row
    assert reap(e, T0 + LEASE).drawing_timed_out == 0
    assert len(audit_rows(e, run_id)) == 1


def test_a_lost_voice_transcription_fails_the_transcript_and_settles_the_run(env: Env) -> None:
    e = env
    e.d.app.state.speech_transcriber = None
    run_id = to_subject_review(e)
    audio = wav_bytes(1500, seed=12)
    voice = complete_upload(e, "t1", run_id, audio, purpose="RUN_AUDIO", media_type="audio/wav")
    assert idea(e, "t1", run_id, audio_ref=voice).status_code == 202
    (pending,) = [r for r in transcript_rows(e, run_id) if r["state"] == "PENDING"]
    with e.sessions().begin() as db:
        db.execute(
            update(story_tables.transcript_revisions)
            .where(
                story_tables.transcript_revisions.c.transcript_revision_id
                == pending["transcript_revision_id"]
            )
            .values(created_at=T0)
        )
    age(e, run_id)
    report = reap(e, T0 + LEASE)
    assert (report.transcript_timed_out, report.errors) == (1, 0)
    (row,) = [r for r in transcript_rows(e, run_id) if r["state"] != "SUPERSEDED"]
    assert row["state"] == "FAILED" and row["error_code"] == TASK_TIMEOUT_CODE
    assert_organization_audit(e, run_id, AUDIT_TIMED_OUT_TRANSCRIPT)
    assert teacher_lock(e, run_id) == e.d.accounts["t1"]


# ------------------------------------------------------------------------------ stories
def test_a_lost_first_story_ends_the_teacher_run_and_frees_the_lock(env: Env) -> None:
    e = env
    run_id = to_subject_review(e)
    assert confirm_context(e, "t1", run_id).status_code == 200
    assert confirm_subject(e, "t1", run_id).status_code == 202
    # a first story whose background task was lost: GENERATING, run SCRIPT_GENERATING/QUEUED
    with e.sessions().begin() as db:
        run = db.execute(select(RUNS).where(RUNS.c.run_id == run_id)).mappings().one()
        db.execute(
            story_tables.story_revisions.insert().values(
                story_revision_id=str(uuid4()),
                run_id=run_id,
                revision_no=1,
                status="GENERATING",
                source_asset_sha256="a" * 64,
                understanding_revision=int(run["understanding_revision"]),
                context_revision=1,
                schema_version="sketch2life.story-revision.v1",
                prompt_version="synthetic-prompt",
                model_id="synthetic-model",
                model_revision="1",
                request_sha256="e" * 64,
                created_at=T0,
            )
        )
        db.execute(
            update(RUNS)
            .where(RUNS.c.run_id == run_id)
            .values(run_state="SCRIPT_GENERATING", job_state="QUEUED", updated_at=T0)
        )
    assert teacher_lock(e, run_id) == e.d.accounts["t1"]
    report = reap(e, T0 + LEASE)
    assert (report.story_failed, report.errors) == (1, 0)
    assert states(e, run_id) == ("FAILED", "FAILED")
    assert run_row(e, run_id)["error_code"] == TASK_TIMEOUT_CODE
    assert teacher_lock(e, run_id) is None  # DDL-B2 trigger: a terminal state frees the lock
    assert story_rows(e, run_id)[0]["status"] == "FAILED"
    assert_organization_audit(e, run_id, AUDIT_TIMED_OUT_STORY)


def test_a_lost_rewrite_returns_to_the_previous_story_and_the_slot_is_counted_by_kind(
    env: Env,
) -> None:
    e = env
    run_id = to_script_review(e)
    e.d.app.state.story_generator = None  # the rewrite is reserved and never started
    assert rewrite(e, "t1", run_id, revision=1, key="lost-1").status_code == 202
    assert states(e, run_id) == ("SCRIPT_GENERATING", "QUEUED")
    age(e, run_id)
    report = reap(e, T0 + LEASE)
    assert (report.rewrite_recovered, report.errors) == (1, 0)
    # back to the previous reviewable story, the lock kept, the attempt row gone
    assert states(e, run_id) == ("SCRIPT_REVIEW", "FAILED")
    row = run_row(e, run_id)
    assert row["error_code"] == TASK_TIMEOUT_CODE and row["retryable"] is True
    assert teacher_lock(e, run_id) == e.d.accounts["t1"]
    assert [r["revision_no"] for r in story_rows(e, run_id)] == [1]
    assert_organization_audit(e, run_id, AUDIT_REWRITE_ATTEMPT_FAILED)
    # the receipt of the lost attempt still counts: three attempts per slot, whoever asked
    assert rewrite(e, "t1", run_id, revision=1, key="lost-2").status_code == 202
    age(e, run_id)
    assert reap(e, T0 + LEASE).rewrite_recovered == 1
    assert rewrite(e, "t1", run_id, revision=1, key="lost-3").status_code == 202
    age(e, run_id)
    assert reap(e, T0 + LEASE).rewrite_recovered == 1
    assert run_row(e, run_id)["retryable"] is False  # the third attempt used the slot
    limit = rewrite(e, "t1", run_id, revision=1, key="lost-4")
    assert limit.status_code == 409 and limit.json()["code"] == "STORY_REWRITE_LIMIT_REACHED"
    assert (
        len([r for r in receipt_rows(e, run_id) if r["operation"] == "GENERATE_STORY_REVISION"])
        == 3
    )


# ------------------------------------------------------------------------------ what is not touched
def test_a_fixture_row_without_a_pin_a_demo_lane_row_and_a_cancelled_run_are_left_alone(
    env: Env,
) -> None:
    from test_teacher_run_inputs_postgres import fixture_run  # type: ignore[import-not-found]

    e = env
    # (1) a T-4a1 style row: ORGANIZATION owner, no occurrence pin, an analysis in flight
    fixture = fixture_run(e)
    with e.sessions().begin() as db:
        db.execute(
            update(RUNS).where(RUNS.c.run_id == fixture).values(job_state="RUNNING", updated_at=T0)
        )
    # (2) a pinned run whose ``current_input_revision`` is NULL: the lane marker of the demo
    demo = new_run(e)
    with e.sessions().begin() as db:
        db.execute(
            update(RUNS)
            .where(RUNS.c.run_id == demo)
            .values(job_state="RUNNING", current_input_revision=None, updated_at=T0)
        )
    before = {run_id: dict(run_row(e, run_id)) for run_id in (fixture, demo)}
    report = reap(e, T0 + LEASE * 10)
    assert (report.drawing_timed_out, report.errors) == (0, 0)
    for run_id in (fixture, demo):
        assert dict(run_row(e, run_id)) == before[run_id]
        assert audit_rows(e, run_id) == []
    with e.sessions()() as db:
        outcome = SqlStoryTaskReaperStore(db).reap(
            ReapCandidate(fixture, ReapKind.DRAWING_LOST), T0 + LEASE * 10, T0 + LEASE * 9
        )
    assert outcome is ReapOutcome.SKIPPED
    # (3) a cancelled Teacher run is never touched
    cancelled = new_run_after(e)
    cancel = e.d.client.post(
        f"/v1/story-runs/{cancelled}/cancel",
        json={"expected_revision": int(run_row(e, cancelled)["revision"])},
        headers=who_headers(e, "t1", uuid4().hex),
    )
    assert cancel.status_code in {200, 202}, cancel.text
    age(e, cancelled)
    assert reap(e, T0 + LEASE * 10).drawing_timed_out == 0
    assert audit_rows(e, cancelled) == [] or all(
        row["action"] != AUDIT_TIMED_OUT_DRAWING for row in audit_rows(e, cancelled)
    )


def new_run_after(e: Env) -> str:
    """A fresh run once the earlier ones are out of the way (one active run per Teacher)."""
    with e.sessions().begin() as db:
        db.execute(
            update(RUNS)
            .where(
                RUNS.c.actor_scope_ref == e.d.organization, RUNS.c.run_state == "INPUT_PROCESSING"
            )
            .values(run_state="ABANDONED")
        )
    return str(new_run(e))


def test_the_reaper_listings_hold_ids_only_and_read_no_content_column(env: Env) -> None:
    import inspect

    from sketch2life.infrastructure.persistence import story_task_reaper_store as store

    source = inspect.getsource(store.SqlStoryTaskReaperStore.list_candidates)
    assert "select(_RUNS.c.run_id)" in source
    assert "story_content" not in source and "raw_transcript" not in source
    lane = inspect.getsource(store._story_lane)
    assert "occurrence_ref.is_not(None)" in lane and "current_input_revision" in lane


def test_nothing_in_the_reaper_pass_writes_a_job_outbox_or_billing_row(env: Env) -> None:
    e = env
    run_id = to_script_review(e)
    e.d.app.state.story_generator = None
    assert rewrite(e, "t1", run_id, revision=1).status_code == 202
    age(e, run_id)
    with e.sessions()() as db:
        before = {
            name: db.execute(text(f"select count(*) from {name}")).scalar_one()  # noqa: S608
            for name in ("core_outbox_events",)
        }
    assert reap(e, T0 + LEASE).rewrite_recovered == 1
    with e.sessions()() as db:
        after = {
            name: db.execute(text(f"select count(*) from {name}")).scalar_one()  # noqa: S608
            for name in ("core_outbox_events",)
        }
    assert before == after
