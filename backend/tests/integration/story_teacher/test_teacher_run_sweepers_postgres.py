"""FEAT-066 T-4b3b: the generation sweepers, the reconciler, the cancel saga, the output asset and
the job read of a Teacher run on PostgreSQL.

SRS l.395 and l.503 (a generation unsettled six hours after ``accepted_at`` ends ``FAILED`` and the
run settles), l.596-597 (an admitted unit stays consumed; a reservation is never lost), l.500 and
FR-C-08 (cancel meets the saga before the purge; the purge covers every row, the video asset
included), l.779 and l.1675 (the job read is the actor of the run's), l.864-865 (one uniform 404),
BR-34 (no storage key or child data in a job). T-13a hand-offs H3 (asset scope) and H6 (the saga).
Runs only against a disposable database whose name contains ``be1_acceptance`` and ``frc08``. The
two admission ports are the accept-all local pair (no quota, billing or capacity logic); object
storage is in memory; no provider, no network.

Fixture rows (a Teacher run without an occurrence pin and without the Teacher lock) are NOT closed
by the overdue sweep: the sweep reads Parent runs and runs that hold the Teacher lock.
"""

# ruff: noqa: F811  (the imported ``v`` and ``env`` fixtures are used as test arguments)

from __future__ import annotations

from datetime import timedelta
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import select, update
from test_teacher_run_create_postgres import (  # type: ignore[import-not-found]
    _seed_generation,
    counts,
)
from test_teacher_run_inputs_postgres import ACTORS  # type: ignore[import-not-found]
from video_support import (  # type: ignore[import-not-found]
    RUNS,
    STORAGE_WORDS,
    VG,
    Env,
    VEnv,
    accepted_generation,
    api,  # noqa: F401 - re-exported fixture
    cancel,
    complete,
    confirm_script,
    env,  # noqa: F401 - re-exported fixture
    generations,
    mark_unsuitable,
    receipt_rows,
    regenerate_cycle,
    request_video,
    rewrite,
    run_row,
    runner,
    scenes_of,
    story_rows,
    to_confirmed_script,
    to_ready,
    v,  # noqa: F401 - fixture
    who_headers,
    wire,
)

from sketch2life.application.ports.core_foundation import LifecycleScope
from sketch2life.application.ports.story_run_lifecycle import StoryLifecycleError
from sketch2life.application.ports.story_video import AckStatus, QuotaStatus
from sketch2life.application.services.story_run_video import StoryVideoAdmissionService
from sketch2life.domain.story_video.model import PUBLIC_JOB_STATE, GenerationState
from sketch2life.infrastructure.lesson_occurrences.tables import OCCURRENCES
from sketch2life.infrastructure.persistence.core_lifecycle_store import (
    SqlCoreRunAssetPurge,
    build_plan,
)
from sketch2life.infrastructure.persistence.story_lifecycle_store import SqlStoryLifecycleStore
from sketch2life.infrastructure.story_video.closeout_store import build_story_run_closeout
from sketch2life.infrastructure.story_video.repository import SqlStoryVideoRepository

DEADLINE = timedelta(hours=6)


def accepted_at(e: Env, generation_id: str) -> Any:
    with e.sessions()() as db:
        return db.execute(
            select(VG.c.accepted_at).where(VG.c.video_generation_id == generation_id)
        ).scalar_one()


def sweep(v: VEnv, now: Any) -> Any:
    """One closeout pass over one session, with the same adapters the routes use."""
    with v.e.sessions()() as session:
        return build_story_run_closeout(session, v.adapters).run_once(now)


def step_to(v: VEnv, generation_id: str, state: str) -> None:
    fixture = runner(v)
    while generations_state(v.e, generation_id) != state:
        assert fixture.step(generation_id).applied


def generations_state(e: Env, generation_id: str) -> str:
    with e.sessions()() as db:
        return str(
            db.execute(
                select(VG.c.state).where(VG.c.video_generation_id == generation_id)
            ).scalar_one()
        )


def generation_row(e: Env, generation_id: str) -> Any:
    with e.sessions()() as db:
        return (
            db.execute(select(VG).where(VG.c.video_generation_id == generation_id)).mappings().one()
        )


# ====================================================================== the overdue sweep (D12)
def test_a_teacher_generation_past_six_hours_fails_and_the_run_returns_to_review(v: VEnv) -> None:
    e = v.e
    run_id, digest, generation_id = accepted_generation(v)
    step_to(v, generation_id, "GENERATING")
    started = accepted_at(e, generation_id)
    before = run_row(e, run_id)
    # not yet: 6 hours less a second after accepted_at leaves it alone
    sweep(v, started + DEADLINE - timedelta(seconds=1))
    assert generation_row(e, generation_id)["state"] == "GENERATING"
    sweep(v, started + DEADLINE + timedelta(seconds=1))
    row = generation_row(e, generation_id)
    assert row["state"] == "FAILED" and row["safe_failure_code"] == "VIDEO_DEADLINE_EXCEEDED"
    assert row["generation_no"] == 1  # the failed request still counts toward the three
    assert row["compute_released_at"] is not None  # the reservation was settled (it had started)
    assert "settle:FAILED" in [call[0] for call in v.reservation.calls]
    run = run_row(e, run_id)
    assert run["run_state"] == "SCRIPT_REVIEW" and run["revision"] > before["revision"]
    assert run["adult_wait_started_at"] is not None
    assert run["active_owner_teacher_id"] == e.d.accounts["t1"]  # the Teacher keeps the run
    assert {s["state"] for s in scenes_of(e, generation_id)} <= {"FAILED", "READY"}
    # the run is settled: a late worker step is a recorded no-op and the Teacher can go on
    assert runner(v).step(generation_id).applied is False
    assert generation_row(e, generation_id)["state"] == "FAILED"
    # a second pass finds nothing left to do for this generation
    sweep(v, started + DEADLINE + timedelta(hours=1))
    assert generation_row(e, generation_id)["state"] == "FAILED"
    # the same script cannot be asked again (its review is consumed); the way forward is a rewrite
    consumed = request_video(e, "t1", run_id, digest, reason="QUALITY_LOW")
    assert consumed.status_code == 409 and consumed.json()["code"] == "INVALID_STATE_TRANSITION"
    assert rewrite(e, "t1", run_id, revision=1).status_code == 202
    newdigest = str(story_rows(e, run_id)[-1]["story_sha256"])
    assert confirm_script(e, "t1", run_id, newdigest, number=2).status_code == 200
    again = request_video(e, "t1", run_id, newdigest, reason="QUALITY_LOW")
    assert again.status_code == 202, again.text


def test_the_overdue_sweep_leaves_a_fixture_row_without_the_teacher_lock_untouched(
    v: VEnv,
) -> None:
    e = v.e
    # Seed the legacy unpinned shape directly. T-6b makes a persisted occurrence binding immutable.
    run_id = _seed_generation(
        e.d, None, run_state="VIDEO_GENERATING", generation_state="GENERATING"
    )
    generation_id = str(generations(e, run_id)[0]["video_generation_id"])
    started = accepted_at(e, generation_id)
    run_before = dict(run_row(e, run_id))
    generation_before = dict(generation_row(e, generation_id))
    sweep(v, started + DEADLINE + timedelta(hours=2))
    assert dict(run_row(e, run_id)) == run_before
    assert dict(generation_row(e, generation_id)) == generation_before
    assert generation_before["state"] == "GENERATING"


def test_the_deadline_with_the_cap_spent_ends_the_run_and_frees_the_teacher_lock(v: VEnv) -> None:
    e = v.e
    run_id, digest, first = accepted_generation(v)
    runner(v).run_to_end(first)
    second = regenerate_cycle(v, run_id, first, number=2)
    runner(v).run_to_end(second)
    third = regenerate_cycle(v, run_id, second, number=3)
    step_to(v, third, "GENERATING")
    sweep(v, accepted_at(e, third) + DEADLINE + timedelta(seconds=1))
    assert generation_row(e, third)["safe_failure_code"] == "VIDEO_DEADLINE_EXCEEDED"
    run = run_row(e, run_id)
    # three accepted requests are spent: the failed one cannot be asked again, so the run ends
    # FAILED and the DDL-B2 trigger frees the Teacher lock (SRS l.2119)
    assert run["run_state"] == "FAILED" and run["finished_at"] is not None
    assert run["active_owner_teacher_id"] is None


# =========================================== the reconciler (T-1a, owner-agnostic)
def test_the_reconciler_finishes_a_teacher_intent_and_finalizes_its_receipt(v: VEnv) -> None:
    e = v.e
    run_id, digest = to_confirmed_script(e)
    v.script.quotas.append(QuotaStatus.UNAVAILABLE)  # the answer cannot be read: the intent waits
    response = request_video(e, "t1", run_id, digest)
    assert response.status_code == 202
    assert response.json()["video_generation"]["state"] == "ADMISSION_PENDING"
    (row,) = generations(e, run_id)
    assert row["state"] == "ADMISSION_PENDING" and row["generation_no"] is None
    (pending,) = [r for r in receipt_rows(e, run_id) if r["operation"] == "CREATE_VIDEO_GENERATION"]
    assert pending["state"] == "PENDING" and pending["actor_scope_kind"] == "ORGANIZATION"
    assert run_row(e, run_id)["run_state"] == "VIDEO_ADMISSION_PENDING"
    with e.sessions()() as db:
        report = StoryVideoAdmissionService(
            SqlStoryVideoRepository(db), v.adapters
        ).reconcile_pending_admissions(run_id=run_id)
    assert report.resolved == 1
    (settled,) = generations(e, run_id)
    assert settled["state"] == "ACCEPTED" and settled["generation_no"] == 1
    assert settled["compute_reservation_ref"] and settled["billing_quota_usage_ref"]
    (final,) = [r for r in receipt_rows(e, run_id) if r["operation"] == "CREATE_VIDEO_GENERATION"]
    # the PENDING receipt of a Teacher request (stored under the command scope, a digest) is
    # found by its command kind and finalized: it never stays PENDING (T-4b3a-DEC-10)
    assert final["state"] == "FINAL" and final["response_status"] == 202
    assert final["actor_scope_ref"] == pending["actor_scope_ref"] != e.d.organization
    assert run_row(e, run_id)["run_state"] == "VIDEO_QUEUED"
    assert run_row(e, run_id)["active_owner_teacher_id"] == e.d.accounts["t1"]


def test_the_reconciler_closes_the_compute_reservation_of_a_refused_teacher_intent(
    v: VEnv,
) -> None:
    e = v.e
    run_id, digest = to_confirmed_script(e)
    v.script.quotas.append(QuotaStatus.QUOTA_EXCEEDED)
    v.script.releases.append(AckStatus.UNAVAILABLE)  # the release is not acknowledged
    refused = request_video(e, "t1", run_id, digest)
    assert refused.status_code == 409 and refused.json()["code"] == "VIDEO_QUOTA_EXCEEDED"
    (row,) = generations(e, run_id)
    assert row["state"] == "ADMISSION_REJECTED"
    assert row["compute_reservation_ref"] and row["compute_released_at"] is None  # kept, not lost
    with e.sessions()() as db:
        report = StoryVideoAdmissionService(
            SqlStoryVideoRepository(db), v.adapters
        ).reconcile_pending_admissions()
    assert report.compute_closed >= 1
    assert generations(e, run_id)[0]["compute_released_at"] is not None
    assert "release" in [call[0] for call in v.reservation.calls]


# ============================================================== the cancel saga (T-13a H6)
def test_the_cancel_of_a_teacher_run_with_a_generation_in_flight_meets_the_saga_first(
    v: VEnv,
) -> None:
    e = v.e
    run_id, digest, generation_id = accepted_generation(v)
    step_to(v, generation_id, "GENERATING")
    response = cancel(e, "t1", run_id)
    assert response.status_code == 202, response.text
    # the hook ran after the cancel commit: nothing is unsettled, the purge plan is available
    row = generation_row(e, generation_id)
    assert row["state"] == "FAILED" and row["safe_failure_code"] == "RUN_CANCELLED"
    assert row["generation_no"] == 1 and row["billing_quota_usage_ref"]  # consumed, no refund
    assert row["compute_released_at"] is not None
    assert "settle:FAILED" in [call[0] for call in v.reservation.calls]  # it had started
    assert run_row(e, run_id)["run_state"] == "DELETE_PENDING"
    assert run_row(e, run_id)["active_owner_teacher_id"] is None
    assert runner(v).step(generation_id).applied is False  # a late worker result is a no-op
    store = SqlStoryLifecycleStore(e.sessions())
    plan = store.plan_story_purge(run_id)
    assert "video_generations" in {item.split(":")[0] for item in plan.ids}


def test_the_cancel_with_an_unreadable_admission_blocks_the_purge_until_the_saga_settles(
    v: VEnv,
) -> None:
    e = v.e
    run_id, digest = to_confirmed_script(e)
    v.script.quotas.extend([QuotaStatus.UNAVAILABLE, QuotaStatus.UNAVAILABLE])
    assert request_video(e, "t1", run_id, digest).status_code == 202
    assert cancel(e, "t1", run_id).status_code == 202  # the hook asks again: still unreadable
    (row,) = generations(e, run_id)
    assert row["state"] == "ADMISSION_PENDING"
    store = SqlStoryLifecycleStore(e.sessions())
    with pytest.raises(StoryLifecycleError, match="VIDEO_GENERATION_UNSETTLED"):
        store.plan_story_purge(run_id)
    with e.sessions()() as db:
        report = StoryVideoAdmissionService(
            SqlStoryVideoRepository(db), v.adapters
        ).reconcile_pending_admissions(run_id=run_id)
    assert report.resolved == 1
    (settled,) = generations(e, run_id)
    assert settled["state"] == "FAILED" and settled["safe_failure_code"] == "RUN_CANCELLED"
    assert settled["generation_no"] == 1 and settled["compute_released_at"] is not None
    plan = store.plan_story_purge(run_id)  # no longer blocked
    store.purge_story_content(plan)
    assert generations(e, run_id) == []


def test_the_cancel_with_a_pending_intent_the_ports_refuse_is_a_rejected_intent(v: VEnv) -> None:
    e = v.e
    run_id, digest = to_confirmed_script(e)
    v.script.quotas.append(QuotaStatus.UNAVAILABLE)
    assert request_video(e, "t1", run_id, digest).status_code == 202
    v.script.quotas.append(QuotaStatus.QUOTA_EXCEEDED)
    assert cancel(e, "t1", run_id).status_code == 202
    (row,) = generations(e, run_id)
    assert row["state"] == "ADMISSION_REJECTED" and row["generation_no"] is None
    assert row["compute_released_at"] is not None
    assert run_row(e, run_id)["run_state"] == "DELETE_PENDING"  # not moved back to the review
    SqlStoryLifecycleStore(e.sessions()).plan_story_purge(run_id)


def test_the_cancel_of_a_teacher_run_after_ready_leaves_the_settled_video_to_the_purge(
    v: VEnv,
) -> None:
    e = v.e
    run_id, digest, generation_id = to_ready(v)
    assert cancel(e, "t1", run_id).status_code == 202
    assert generation_row(e, generation_id)["state"] == "READY"  # settled: nothing to resolve
    SqlStoryLifecycleStore(e.sessions()).plan_story_purge(run_id)


# ===================================================== the purge closure with the video (H3)
def test_the_purge_closure_covers_the_video_output_asset_of_a_teacher_run(v: VEnv) -> None:
    e = v.e
    run_id, digest, generation_id = to_ready(v)
    key = str(generation_row(e, generation_id)["output_asset_ref"])
    assert key == f"parent/{run_id}/video/{generation_id}/output.mp4"  # the prefix is the contract
    assert key in e.storage.inner.objects
    from sketch2life.infrastructure.persistence.core_models import CoreAssetMetadataModel

    with e.sessions()() as db:
        asset = db.execute(
            select(CoreAssetMetadataModel).where(CoreAssetMetadataModel.asset_ref == key)
        ).scalar_one()
        assert (asset.owner_scope_kind, asset.owner_scope_ref, asset.organization_id) == (
            "ORGANIZATION",
            e.d.organization,
            e.d.organization,
        )
        assert asset.source_refs == [run_id] and asset.asset_version == 1
    assert cancel(e, "t1", run_id).status_code == 202
    scope = LifecycleScope("ORGANIZATION", e.d.organization)
    purge = SqlCoreRunAssetPurge(e.sessions(), e.storage)
    candidates = purge.closure_candidates(scope, run_id)
    assert key in {item.asset_ref for item in candidates.assets}
    plan = build_plan(candidates, frozenset())
    # no SCOPE_MISMATCH, no retained row: the video is removable (a NULL ref would defeat this)
    assert plan.retained == ()
    assert key in {item.asset_ref for item in plan.removable}
    purge.purge_objects(plan)
    assert purge.sweep_run_prefix(scope, run_id).swept_count == 0
    purge.delete_rows(plan, frozenset())
    store = SqlStoryLifecycleStore(e.sessions())
    store.purge_story_content(store.plan_story_purge(run_id))
    assert generations(e, run_id) == [] and e.storage.list_keys(f"parent/{run_id}/") == ()


# ============================================================================ the job read (D14)
def job_get(e: Env, who: str, job_id: str, **extra: str) -> Any:
    return e.d.client.get(f"/v1/jobs/{job_id}", headers=who_headers(e, who, **extra))


def job_id_of(e: Env, generation_id: str) -> str:
    return str(generation_row(e, generation_id)["job_ref"])


def test_the_responsible_teacher_reads_the_job_at_every_state_with_no_result_refs(
    v: VEnv,
) -> None:
    e = v.e
    run_id, digest, generation_id = accepted_generation(v)
    job_id = job_id_of(e, generation_id)
    seen: list[str] = []
    for _ in range(12):
        row = generation_row(e, generation_id)
        response = job_get(e, "t1", job_id)
        assert response.status_code == 200, response.text
        body = response.json()
        expected = PUBLIC_JOB_STATE[GenerationState(row["state"])]
        assert body["state"] == expected and body["target_kind"] == "VIDEO_GENERATION"
        assert body["target_ref"] == generation_id and body["job_id"] == job_id
        assert body["result_refs"] == []  # playback is the playback route only (l.1692)
        assert response.headers["cache-control"] == "private, no-cache"
        blob = (response.text + str(dict(response.headers))).lower()
        for word in (*STORAGE_WORDS, "amazonaws"):
            assert word not in blob
        seen.append(str(body["state"]))
        if not runner(v).step(generation_id).applied:
            break
    assert seen[0] != "succeeded" and seen[-1] == "succeeded"
    # the closed run stays readable by its Teacher
    assert complete(e, "t1", run_id).status_code == 200
    assert job_get(e, "t1", job_id).status_code == 200


def test_every_other_actor_gets_the_same_404_as_for_an_unknown_job(v: VEnv) -> None:
    e = v.e
    _run_id, digest, generation_id = accepted_generation(v)
    job_id = job_id_of(e, generation_id)
    unknown = wire(job_get(e, "t1", "vjob_" + "9" * 32))
    assert unknown[0] == 404 and unknown[1]["code"] == "RESOURCE_NOT_FOUND"
    for who in ACTORS:
        assert wire(job_get(e, who, job_id)) == unknown, who
    # the Manager and the other roles are not read through an organization role either
    assert wire(job_get(e, "manager", job_id)) == unknown


def test_the_job_follows_the_current_responsible_teacher_not_the_creator(v: VEnv) -> None:
    e = v.e
    run_id, digest, generation_id = accepted_generation(v)
    job_id = job_id_of(e, generation_id)
    unknown = wire(job_get(e, "t1", "vjob_" + "8" * 32))
    occurrence = run_row(e, run_id)["occurrence_ref"]
    with e.sessions().begin() as db:
        db.execute(
            update(OCCURRENCES)
            .where(OCCURRENCES.c.occurrence_id == occurrence)
            .values(responsible_teacher_ref=e.d.accounts["t4"])
        )
    assert wire(job_get(e, "t1", job_id)) == unknown
    assert job_get(e, "t4", job_id).status_code == 200


def test_the_conditional_read_is_decided_after_the_actor_was_authorised(v: VEnv) -> None:
    e = v.e
    _run_id, digest, generation_id = accepted_generation(v)
    job_id = job_id_of(e, generation_id)
    first = job_get(e, "t1", job_id)
    etag = first.headers["etag"]
    cached = job_get(e, "t1", job_id, **{"If-None-Match": etag})
    assert cached.status_code == 304 and cached.content == b""
    # nobody else gets a 304, whatever tag they present
    for who in ("t2", "t4", "parent", "manager"):
        refused = job_get(e, who, job_id, **{"If-None-Match": etag})
        assert refused.status_code == 404, who
    # the job moves: the same tag no longer matches
    runner(v).step(generation_id)
    moved = job_get(e, "t1", job_id, **{"If-None-Match": etag})
    assert moved.status_code == 200 and moved.headers["etag"] != etag


def test_a_purged_run_and_a_run_without_a_pin_have_no_readable_job(v: VEnv) -> None:
    e = v.e
    run_id = _seed_generation(e.d, None, run_state="SCRIPT_REVIEW", generation_state="ACCEPTED")
    generation_id = str(generations(e, run_id)[0]["video_generation_id"])
    job_id = job_id_of(e, generation_id)
    unknown = wire(job_get(e, "t1", "vjob_" + "7" * 32))
    assert wire(job_get(e, "t1", job_id)) == unknown  # a fixture row is never read
    # a second run: cancelled, so DELETE_PENDING, so the job is gone
    with e.sessions().begin() as db:
        db.execute(update(RUNS).where(RUNS.c.run_id == run_id).values(run_state="ABANDONED"))
    e.runs.pop(run_id, None)
    second, _d2, second_generation = accepted_generation(v)
    second_job = job_id_of(e, second_generation)
    assert job_get(e, "t1", second_job).status_code == 200
    assert cancel(e, "t1", second).status_code == 202
    assert wire(job_get(e, "t1", second_job)) == unknown


def test_the_unsuitable_and_rewrite_cycle_keeps_each_job_with_its_own_generation(
    v: VEnv,
) -> None:
    e = v.e
    run_id, digest, first = accepted_generation(v)
    runner(v).run_to_end(first)
    assert mark_unsuitable(e, "t1", run_id, first).status_code == 200
    assert rewrite(e, "t1", run_id, revision=1).status_code == 202
    first_job = job_id_of(e, first)
    body = job_get(e, "t1", first_job).json()
    assert body["target_ref"] == first and body["state"] == "succeeded"
    assert all(g["job_ref"] for g in generations(e, run_id))


def test_no_billing_or_job_table_row_exists_after_the_video_flows(v: VEnv) -> None:
    e = v.e
    run_id, digest, generation_id = to_ready(v)
    assert complete(e, "t1", run_id).status_code == 200
    names = counts(e.d)
    forbidden = {
        name
        for name, size in names.items()
        if size and (name.startswith(("ai_jobs.", "billing.", "ai_policy.")) or "quota" in name)
    }
    # the local adapters hold their receipts in memory: nothing durable of quota or billing exists
    assert forbidden == set(), forbidden
    assert uuid4() and generation_id
