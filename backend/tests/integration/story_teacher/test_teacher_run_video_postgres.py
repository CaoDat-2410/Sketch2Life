"""FEAT-066 T-4b3b: the Teacher side of the StoryRun video routes on PostgreSQL.

SRS l.395 (a generation is an intent first, accepted only after both receipts), l.500 and FR-C-08,
l.552 (Complete never touches the sample slot), l.553 (access follows the CURRENT Teacher),
l.573 (three requests), l.596-597 (the ports), l.864-865 (one uniform 404), l.1670-1672 (the three
video routes), l.1676 and l.1691-1693 (the owner-view token and stream), l.1697-1699 (keys, replay,
``STALE_REVISION``), l.364, l.593, l.1425 (a suspended or archived class is read-only), BR-34 (no
child name or storage key in a body). Runs only against a disposable database whose name contains
``be1_acceptance`` and ``frc08``.

The Teacher run is created through the real T-4b2 route; the first story is inserted by SQL (no HTTP
route starts it, plan review P2-1, OPEN-A) and confirmed through the real ``script-confirmation``
route; the video request, the two decisions, the token and the stream are the real routes. The two
admission ports are the accept-all local pair (no quota, billing or capacity logic); object storage
is in memory; no provider, no network.
"""

# ruff: noqa: F811  (the imported ``v`` and ``env`` fixtures are used as test arguments)

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import select, text, update
from test_teacher_run_create_postgres import (  # type: ignore[import-not-found]
    ISSUER,
    NAME_PREFIX,
    _assign,
    _identity,
    _seed_generation,
    counts,
    headers,
    occurrence_row,
    post_create,
)
from test_teacher_run_inputs_postgres import ACTORS  # type: ignore[import-not-found]
from video_support import (  # type: ignore[import-not-found]
    RUNS,
    STORAGE_WORDS,
    Env,
    VEnv,
    accepted_generation,
    api,  # noqa: F401 - re-exported fixture
    complete,
    confirm_script,
    env,  # noqa: F401 - re-exported fixture
    generations,
    mark_unsuitable,
    playback_token,
    receipt_rows,
    regenerate_cycle,
    request_video,
    rewrite,
    run_revision,
    run_row,
    runner,
    scenes_of,
    story_rows,
    stream,
    to_confirmed_script,
    to_ready,
    v,  # noqa: F401 - fixture
    who_headers,
    wire,
)

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.story_video import QuotaStatus, VideoRequestScope
from sketch2life.infrastructure.lesson_occurrences.tables import CHILD_SELECTIONS, OCCURRENCES
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    ClassroomModel,
    ManagedProfileModel,
    OrganizationAssignmentModel,
)
from sketch2life.infrastructure.uploads.resolvers import parent_scope_ref

VIDEO_OPERATION = "CREATE_VIDEO_GENERATION"
SYNTHETIC_MP4_HEAD = b"\x00\x00\x00\x18ftypmp42"


def field_errors(response: Any) -> list[tuple[str, str]]:
    return [(item["field"], item["code"]) for item in response.json()["field_errors"]]


def digest_of(e: Env, who: str) -> str:
    """The command scope ref of a Teacher: the digest of the principal, never the organization."""
    return parent_scope_ref(VerifiedPrincipal(e.d.subjects[who], ISSUER, frozenset()))


def snapshot_of_slot(e: Env) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Every occurrence and child-selection row: the sample slot lives there (OD-14, l.351)."""
    with e.sessions()() as db:
        occurrences = [dict(r) for r in db.execute(select(OCCURRENCES)).mappings().all()]
        selections = [dict(r) for r in db.execute(select(CHILD_SELECTIONS)).mappings().all()]
    key = lambda row: sorted(str(item) for item in row.items())  # noqa: E731
    return sorted(occurrences, key=key), sorted(selections, key=key)


def set_class_state(e: Env, state: str) -> None:
    with e.sessions().begin() as db:
        db.execute(
            update(ClassroomModel)
            .where(ClassroomModel.class_id == e.d.classes["a1"])
            .values(state=state)
        )


def complete_teacher_transfer(e: Env, run_id: str) -> str:
    """Run the T-6b BE1/Story reassignment saga and return its new Teacher actor key."""
    run = run_row(e, run_id)
    organization_id = str(run["organization_ref"])
    class_id = str(run["class_ref"])
    old_owner = str(run["active_owner_teacher_id"])
    manager_subject = e.d.subjects["manager"]
    new_subject = f"synthetic-t6b-video-successor-{uuid4().hex}"
    actor_key = f"successor-{uuid4().hex[:8]}"
    idempotency_key = f"t6b-video-transfer-{uuid4()}"

    with e.sessions().begin() as db:
        old_identity = db.scalar(
            select(AdultIdentityModel).where(AdultIdentityModel.account_id == old_owner)
        )
        assert old_identity is not None
        # The older route fixture can contain a second active Teacher row. T-6b's saga requires
        # exactly one current class assignment; keep the run owner and retire only the extra row.
        db.execute(
            update(OrganizationAssignmentModel)
            .where(
                OrganizationAssignmentModel.organization_id == organization_id,
                OrganizationAssignmentModel.class_id == class_id,
                OrganizationAssignmentModel.role == "teacher",
                OrganizationAssignmentModel.active.is_(True),
                OrganizationAssignmentModel.subject != old_identity.subject,
            )
            .values(active=False)
        )
        new_account = _identity(db, new_subject, "teacher")
        _assign(db, organization_id, new_subject, "teacher", None)
        classroom = db.scalar(
            select(ClassroomModel).where(
                ClassroomModel.organization_id == organization_id,
                ClassroomModel.class_id == class_id,
            )
        )
        assert classroom is not None
        assignment_revision = int(classroom.assignment_revision)

    accepted = e.d.client.post(
        f"/api/be1/v1/classes/{class_id}/assignments",
        json={"candidate_ref": new_account},
        headers=headers(
            manager_subject,
            idempotency_key,
            **{"If-Match": f'"{assignment_revision}"'},
        ),
    )
    assert accepted.status_code == 202, accepted.text
    completed = e.d.client.get(
        accepted.json()["status_url"], headers=headers(manager_subject)
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["state"] == "COMPLETED"

    e.d.subjects[actor_key] = new_subject
    e.d.accounts[actor_key] = new_account
    transferred = run_row(e, run_id)
    assert transferred["active_owner_teacher_id"] == new_account
    assert transferred["created_by_actor_ref"] == old_owner
    assert transferred["owner_epoch"] == int(run["owner_epoch"]) + 1
    return actor_key


# ======================================================================== the video request (D8)
def test_a_teacher_requests_a_video_with_the_organization_scope_and_no_billing_row(
    v: VEnv,
) -> None:
    e = v.e
    run_id, digest = to_confirmed_script(e)
    slot_before = snapshot_of_slot(e)
    names = counts(e.d)
    first_revision = run_revision(e, run_id)
    response = request_video(e, "t1", run_id, digest, key="teacher-key-1")
    assert response.status_code == 202, response.text
    body = response.json()["video_generation"]
    assert body["state"] == "ACCEPTED" and body["generation_no"] == 1 and body["kind"] == "INITIAL"
    assert body["run_state"] == "VIDEO_QUEUED" and body["job_id"].startswith("vjob_")
    assert response.headers["Content-Location"] == f"/v1/story-runs/{run_id}"
    (row,) = generations(e, run_id)
    assert row["state"] == "ACCEPTED" and row["generation_no"] == 1
    # the local adapter's opaque references satisfy ``ck_vg_shape``; nothing else is stored (OPEN-2)
    assert row["compute_reservation_ref"] and row["billing_quota_usage_ref"]
    assert row["compute_reservation_ref"].startswith("lres_")
    assert row["billing_quota_usage_ref"].startswith("lusg_")
    # Compute stays organization-scoped; Billing also receives the active account id and resolves
    # it to the sign-in subject used by Manager allocation writes.
    expected_compute = VideoRequestScope("ORGANIZATION", e.d.organization)
    expected_quota = VideoRequestScope(
        "ORGANIZATION", e.d.organization, e.d.accounts["t1"]
    )
    assert v.reservation.scopes == [expected_compute]
    assert v.quota.scopes == [expected_quota]
    run = run_row(e, run_id)
    assert run["run_state"] == "VIDEO_QUEUED" and run["job_state"] == "QUEUED"
    assert run["actor_scope_kind"] == "ORGANIZATION" and run["actor_scope_ref"] == e.d.organization
    assert run["active_owner_teacher_id"] == e.d.accounts["t1"]  # the lock is held
    # the receipt is the command scope of the calling Teacher, final, with the 202
    (receipt,) = [r for r in receipt_rows(e, run_id) if r["operation"] == VIDEO_OPERATION]
    assert receipt["actor_scope_kind"] == "ORGANIZATION"
    assert receipt["actor_scope_ref"] == digest_of(e, "t1") != e.d.organization
    assert receipt["state"] == "FINAL" and receipt["response_status"] == 202
    # a replay returns the same generation and writes nothing
    again = request_video(e, "t1", run_id, digest, key="teacher-key-1", revision=first_revision)
    assert (
        again.status_code == 202
        and again.json()["video_generation"]["generation_id"] == (body["generation_id"])
    )
    assert len(generations(e, run_id)) == 1
    # another body under the same key is a key error
    other = request_video(e, "t1", run_id, "b" * 64, key="teacher-key-1", revision=first_revision)
    assert other.status_code == 400 and other.json()["code"] == "INVALID_IDEMPOTENCY_KEY"
    # the sample slot and every Lesson row are untouched; no quota, billing or job row exists
    assert snapshot_of_slot(e) == slot_before
    moved = {name for name, size in counts(e.d).items() if size != names.get(name)}
    assert not {name for name in moved if name.startswith(("ai_jobs.", "billing.", "ai_policy."))}
    with e.sessions()() as db:
        for schema in ("billing", "ai_policy", "ai_jobs"):
            tables = db.execute(
                text(
                    "select table_schema || '.' || table_name from information_schema.tables "
                    "where table_schema = :schema"
                ),
                {"schema": schema},
            ).scalars()
            for table in list(tables):
                assert db.execute(text(f"select count(*) from {table}")).scalar_one() == 0  # noqa: S608
    text_body = response.text.lower()
    for word in (*STORAGE_WORDS, "organization", NAME_PREFIX.lower()):
        assert word not in text_body


@pytest.mark.parametrize(
    ("quota_status", "error_code"),
    [
        (QuotaStatus.QUOTA_EXCEEDED, "VIDEO_QUOTA_EXCEEDED"),
        (QuotaStatus.QUOTA_ALLOCATION_NOT_FOUND, "QUOTA_ALLOCATION_NOT_FOUND"),
        (QuotaStatus.TEACHER_QUOTA_INSUFFICIENT, "TEACHER_QUOTA_INSUFFICIENT"),
        (QuotaStatus.SCHOOL_QUOTA_INSUFFICIENT, "SCHOOL_QUOTA_INSUFFICIENT"),
    ],
)
def test_a_refused_admission_is_finalized_and_keeps_the_teacher_lock(
    v: VEnv, quota_status: QuotaStatus, error_code: str
) -> None:
    e = v.e
    run_id, digest = to_confirmed_script(e)
    v.script.quotas.append(quota_status)
    first_revision = run_revision(e, run_id)
    refused = request_video(e, "t1", run_id, digest, key="refused-1")
    assert refused.status_code == 409 and refused.json()["code"] == error_code
    (row,) = generations(e, run_id)
    assert row["state"] == "ADMISSION_REJECTED" and row["generation_no"] is None
    assert row["compute_released_at"] is not None  # the reservation was released
    (receipt,) = [r for r in receipt_rows(e, run_id) if r["operation"] == VIDEO_OPERATION]
    assert receipt["state"] == "FINAL" and receipt["response_status"] == 409  # never left PENDING
    run = run_row(e, run_id)
    assert run["run_state"] == "SCRIPT_REVIEW"
    assert run["active_owner_teacher_id"] == e.d.accounts["t1"]
    # the same key again replays the same refusal; a new key may try again and is accepted
    replayed = request_video(e, "t1", run_id, digest, key="refused-1", revision=first_revision)
    assert replayed.status_code == 409 and replayed.json()["code"] == error_code
    again = request_video(e, "t1", run_id, digest)
    assert again.status_code == 202, again.text


def test_the_successor_teacher_reusing_the_predecessors_key_gets_the_same_generation(
    v: VEnv,
) -> None:
    e = v.e
    run_id, digest = to_confirmed_script(e)
    first_revision = run_revision(e, run_id)
    first = request_video(e, "t1", run_id, digest, key="shared-key")
    assert first.status_code == 202
    generation_id = first.json()["video_generation"]["generation_id"]
    successor = complete_teacher_transfer(e, run_id)
    same = request_video(
        e, successor, run_id, digest, key="shared-key", revision=first_revision
    )
    # After the completed saga, the successor is authorized and replays the run-scoped receipt.
    assert same.status_code == 202
    assert same.json()["video_generation"]["generation_id"] == generation_id
    assert len(generations(e, run_id)) == 1
    other = request_video(
        e, successor, run_id, "c" * 64, key="shared-key", revision=first_revision
    )
    assert other.status_code == 400 and other.json()["code"] == "INVALID_IDEMPOTENCY_KEY"
    # the predecessor lost the run: the uniform 404 whatever the key
    gone = request_video(e, "t1", run_id, digest, key="shared-key", revision=first_revision)
    assert gone.status_code == 404 and gone.json()["code"] == "RESOURCE_NOT_FOUND"


def test_the_second_request_needs_a_reason_and_three_accepted_requests_close_the_door(
    v: VEnv,
) -> None:
    e = v.e
    run_id, digest = to_confirmed_script(e)
    refused = request_video(e, "t1", run_id, digest, reason="QUALITY_LOW")
    assert refused.status_code == 400  # the first request refuses a reason
    assert field_errors(refused) == [("quality_reason_code", "NOT_ALLOWED")]
    accepted = request_video(e, "t1", run_id, digest)
    assert accepted.status_code == 202
    first = accepted.json()["video_generation"]["generation_id"]
    runner(v).run_to_end(first)
    second = regenerate_cycle(v, run_id, first, number=2)
    row = generations(e, run_id)[-1]
    assert row["generation_kind"] == "QUALITY_REGEN" and row["generation_no"] == 2
    runner(v).run_to_end(second)
    third = regenerate_cycle(v, run_id, second, number=3)
    assert generations(e, run_id)[-1]["generation_no"] == 3
    runner(v).run_to_end(third)
    # three accepted requests: the adult can no longer reject the video, the video stays
    blocked = mark_unsuitable(e, "t1", run_id, third)
    assert blocked.status_code == 409
    assert blocked.json()["code"] == "VIDEO_REGENERATION_LIMIT_REACHED"
    assert run_row(e, run_id)["run_state"] == "VIDEO_READY"
    assert complete(e, "t1", run_id).status_code == 200  # the way out is Complete
    assert len(generations(e, run_id)) == 3


def test_the_regeneration_reason_is_required_after_the_first_accepted_request(v: VEnv) -> None:
    e = v.e
    run_id, digest, first = accepted_generation(v)
    runner(v).run_to_end(first)
    assert mark_unsuitable(e, "t1", run_id, first).status_code == 200
    assert rewrite(e, "t1", run_id, revision=1).status_code == 202
    new_digest = str(story_rows(e, run_id)[-1]["story_sha256"])
    assert confirm_script(e, "t1", run_id, new_digest, number=2).status_code == 200
    missing = request_video(e, "t1", run_id, new_digest)
    assert missing.status_code == 400
    assert field_errors(missing) == [("quality_reason_code", "REQUIRED")]
    assert request_video(e, "t1", run_id, new_digest, reason="OTHER").status_code == 202


def test_without_the_admission_ports_the_answer_is_503_after_the_404_and_409_rules(
    v: VEnv,
) -> None:
    e = v.e
    run_id, digest = to_confirmed_script(e)
    v.use_adapters(None)
    unavailable = request_video(e, "t1", run_id, digest)
    assert unavailable.status_code == 503 and unavailable.json()["code"] == "PROVIDER_UNAVAILABLE"
    assert generations(e, run_id) == []
    # a foreign actor never sees the 503 first; a stale revision is a 409 before it
    foreign = request_video(e, "t2", run_id, digest)
    assert foreign.status_code == 404 and foreign.json()["code"] == "RESOURCE_NOT_FOUND"
    stale = request_video(e, "t1", run_id, digest, revision=1)
    assert stale.status_code == 409 and stale.json()["code"] == "STALE_REVISION"
    assert stale.json()["current_version"] == run_revision(e, run_id)
    v.use_adapters(v.adapters)
    assert request_video(e, "t1", run_id, digest).status_code == 202


def test_the_request_checks_state_revision_script_and_the_unconfirmed_gate(v: VEnv) -> None:
    e = v.e
    run_id, digest = to_confirmed_script(e)
    assert request_video(e, "t1", run_id, "d" * 64).status_code == 409  # another script hash
    assert request_video(e, "t1", run_id, digest, revision=1).status_code == 409
    ok = request_video(e, "t1", run_id, digest)
    assert ok.status_code == 202
    busy = request_video(e, "t1", run_id, digest)  # a second request while one is in flight
    assert busy.status_code == 409 and busy.json()["code"] == "INVALID_STATE_TRANSITION"
    assert len(generations(e, run_id)) == 1


# ===================================================== unsuitable and complete (D9, D11)
def test_unsuitable_returns_the_teacher_view_keeps_the_lock_and_replays(v: VEnv) -> None:
    e = v.e
    run_id, _digest, generation_id = to_ready(v)
    slot_before = snapshot_of_slot(e)
    first_revision = run_revision(e, run_id)
    response = mark_unsuitable(e, "t1", run_id, generation_id, key="unsuitable-1")
    assert response.status_code == 200, response.text
    view = response.json()["story_run"]
    assert view["run_state"] == "SCRIPT_REVIEW"
    assert view["profile_ref"]["kind"] == "MANAGED_PROFILE"  # the Teacher view
    assert "parent_profile_id" not in view
    assert response.headers["Content-Location"] == f"/v1/story-runs/{run_id}"
    row = run_row(e, run_id)
    assert row["active_owner_teacher_id"] == e.d.accounts["t1"]  # the lock stays
    (generation,) = generations(e, run_id)
    assert generation["state"] == "REJECTED_BY_ADULT"
    (receipt,) = [r for r in receipt_rows(e, run_id) if r["operation"] == "MARK_VIDEO_UNSUITABLE"]
    assert receipt["actor_scope_kind"] == "ORGANIZATION"
    assert receipt["actor_scope_ref"] == digest_of(e, "t1") and receipt["state"] == "FINAL"
    # the same key and body again is the stored result: the current run, nothing written
    receipts_before = len(receipt_rows(e, run_id))
    again = mark_unsuitable(
        e, "t1", run_id, generation_id, key="unsuitable-1", revision=first_revision
    )
    assert again.status_code == 200 and again.json()["story_run"]["run_state"] == "SCRIPT_REVIEW"
    assert len(receipt_rows(e, run_id)) == receipts_before  # a replay writes nothing
    other = mark_unsuitable(
        e, "t1", run_id, generation_id, key="unsuitable-1", revision=first_revision, reason="OTHER"
    )
    assert other.status_code == 400 and other.json()["code"] == "INVALID_IDEMPOTENCY_KEY"
    assert snapshot_of_slot(e) == slot_before


def test_complete_frees_the_teacher_lock_and_never_touches_the_occurrence_or_the_slot(
    v: VEnv,
) -> None:
    e = v.e
    run_id, _digest, generation_id = to_ready(v)
    assert run_row(e, run_id)["active_owner_teacher_id"] == e.d.accounts["t1"]  # the lock is held
    slot_before = snapshot_of_slot(e)
    occurrence = run_row(e, run_id)["occurrence_ref"]
    first_revision = run_revision(e, run_id)
    response = complete(e, "t1", run_id, key="complete-1")
    assert response.status_code == 200, response.text
    view = response.json()["story_run"]
    assert view["run_state"] == "COMPLETED" and view["profile_ref"]["kind"] == "MANAGED_PROFILE"
    row = run_row(e, run_id)
    assert row["run_state"] == "COMPLETED" and row["finished_at"] is not None
    assert row["active_owner_teacher_id"] is None  # the DDL-B2 trigger freed the lock
    (generation,) = generations(e, run_id)
    assert generation["state"] == "READY"  # the run is not a video approval
    assert snapshot_of_slot(e) == slot_before  # no sample claimed, no occurrence written
    assert occurrence_row(e.d, occurrence)["responsible_teacher_ref"] == e.d.accounts["t1"]
    (receipt,) = [r for r in receipt_rows(e, run_id) if r["operation"] == "COMPLETE_RUN"]
    assert receipt["actor_scope_ref"] == digest_of(e, "t1") and receipt["state"] == "FINAL"
    # replay is the stored 200 (the run read now), a stale revision after it is the 409 rule
    again = complete(e, "t1", run_id, key="complete-1", revision=first_revision)
    assert again.status_code == 200 and again.json()["story_run"]["run_state"] == "COMPLETED"
    # a new run is possible now (the lock is free)
    assert post_create_ok(e)


def post_create_ok(e: Env) -> bool:
    from test_teacher_run_create_postgres import flow  # noqa: PLC0415

    _occ, _offer, body = flow(e.d)
    response = post_create(e.d, "t1", body)
    return bool(response.status_code == 201)


def test_complete_and_unsuitable_need_a_ready_video_and_the_current_revision(v: VEnv) -> None:
    e = v.e
    run_id, digest, generation_id = accepted_generation(v)
    early = complete(e, "t1", run_id)
    assert early.status_code == 409 and early.json()["code"] == "INVALID_STATE_TRANSITION"
    early_unsuitable = mark_unsuitable(e, "t1", run_id, generation_id)
    assert early_unsuitable.status_code == 409
    runner(v).run_to_end(generation_id)
    stale = complete(e, "t1", run_id, revision=1)
    assert stale.status_code == 409 and stale.json()["code"] == "STALE_REVISION"
    assert stale.json()["current_version"] == run_revision(e, run_id)
    wrong_generation = mark_unsuitable(e, "t1", run_id, str(uuid4()))
    assert (
        wrong_generation.status_code == 409 and wrong_generation.json()["code"] == "STALE_REVISION"
    )
    assert complete(e, "t1", run_id).status_code == 200


# ============================================================ the owner-view playback (D10)
def test_the_owner_view_token_and_stream_serve_the_ready_video(v: VEnv) -> None:
    e = v.e
    run_id, _digest, generation_id = to_ready(v)
    issued = playback_token(e, "t1", run_id)
    assert issued.status_code == 200, issued.text
    assert issued.headers["cache-control"] == "no-store"
    grant = issued.json()["playback"]
    assert grant["stream_path"] == f"/v1/story-runs/{run_id}/playback"
    assert set(grant) == {"token", "expires_at", "stream_path", "media_type", "asset_ref"}
    token = grant["token"]
    # no storage location, key, bucket or URL reaches a body
    blob = (issued.text + str(dict(issued.headers))).lower()
    for word in (*STORAGE_WORDS, "amazonaws"):
        assert word not in blob
    whole = stream(e, "t1", run_id, token)
    assert whole.status_code == 200 and whole.content.startswith(SYNTHETIC_MP4_HEAD)
    assert whole.headers["content-type"].startswith("video/mp4")
    assert whole.headers["cache-control"] == "private, no-store"
    size = len(whole.content)
    partial = stream(e, "t1", run_id, token, byte_range="bytes=0-3")
    assert partial.status_code == 206 and partial.content == whole.content[:4]
    assert partial.headers["content-range"] == f"bytes 0-3/{size}"
    outside = stream(e, "t1", run_id, token, byte_range=f"bytes={size + 5}-")
    assert outside.status_code == 416 and outside.headers["content-range"] == f"bytes */{size}"
    # the token header is required; a malformed one is a 401, never a lookup
    assert stream(e, "t1", run_id, None).status_code == 401
    assert stream(e, "t1", run_id, "not-a-token").status_code == 401
    # the playback never wrote anything: the generation and the run are as they were
    assert generations(e, run_id)[0]["video_generation_id"] == generation_id
    assert run_row(e, run_id)["run_state"] == "VIDEO_READY"


def test_the_token_names_one_teacher_and_the_current_assignment_decides_every_request(
    v: VEnv,
) -> None:
    e = v.e
    run_id, _digest, _gid = to_ready(v)
    token = playback_token(e, "t1", run_id).json()["playback"]["token"]
    unknown = wire(stream(e, "t1", str(uuid4()), token))
    assert unknown[0] == 404
    # another Teacher, a Parent and a Manager with the stolen token: the same uniform 404
    for who in ("t2", "t4", "parent", "manager", "revoked", "inactive", "stranger"):
        assert wire(stream(e, who, run_id, token)) == unknown, who
    # A completed T-6b transfer fences the old owner and advances the token's owner epoch.
    successor = complete_teacher_transfer(e, run_id)
    assert wire(stream(e, "t1", run_id, token)) == unknown
    assert wire(playback_token(e, "t1", run_id)) == unknown
    assert wire(stream(e, successor, run_id, token)) == unknown  # token is bound to the old actor
    own = playback_token(e, successor, run_id)
    assert own.status_code == 200
    assert stream(e, successor, run_id, own.json()["playback"]["token"]).status_code == 200


def test_a_revoked_assignment_ends_the_stream_at_the_next_request(v: VEnv) -> None:
    e = v.e
    run_id, _digest, _gid = to_ready(v)
    token = playback_token(e, "t1", run_id).json()["playback"]["token"]
    assert stream(e, "t1", run_id, token).status_code == 200
    with e.sessions().begin() as db:
        db.execute(
            update(OrganizationAssignmentModel)
            .where(OrganizationAssignmentModel.subject == e.d.subjects["t1"])
            .values(active=False)
        )
    gone = stream(e, "t1", run_id, token)
    assert gone.status_code == 404 and gone.json()["code"] == "RESOURCE_NOT_FOUND"
    assert playback_token(e, "t1", run_id).status_code == 404


def test_a_rejected_run_gets_no_token_and_a_completed_run_keeps_playing(
    v: VEnv,
) -> None:
    e = v.e
    run_id, _digest, generation_id = to_ready(v)
    token = playback_token(e, "t1", run_id).json()["playback"]["token"]
    assert mark_unsuitable(e, "t1", run_id, generation_id).status_code == 200
    assert stream(e, "t1", run_id, token).status_code == 404  # a rejected video is hidden
    refused = playback_token(e, "t1", run_id)
    assert refused.status_code == 409 and refused.json()["code"] == "INVALID_STATE_TRANSITION"
    # a second run to the end: Complete ends the run, not the viewing (V4-A T-1c-fix, owner C1(a));
    # a class projection confirmed before Complete ends in the Lesson check (test_projection_*)
    second_id, _d, _g = _second_ready(v)
    second_token = playback_token(e, "t1", second_id).json()["playback"]["token"]
    assert complete(e, "t1", second_id).status_code == 200
    assert stream(e, "t1", second_id, second_token).status_code == 200
    again = playback_token(e, "t1", second_id)
    assert again.status_code == 200
    assert stream(e, "t1", second_id, again.json()["playback"]["token"]).status_code == 200


def test_a_withdrawn_managed_profile_does_not_end_a_teacher_playback_t4a1_dec_3(v: VEnv) -> None:
    """The Teacher access is the occurrence pin; the managed profile state is not a condition
    (T-4a1-DEC-3: a withdrawn child's run stays reachable for the class Teacher). V4-A T-1c-fix
    pins the consequence: neither a ``VIDEO_READY`` nor a ``COMPLETED`` Teacher run is revoked by
    a non-active profile (the Parent branch is, test_replay_after_complete_postgres.py)."""

    e = v.e
    run_id, _digest, _generation_id = to_ready(v)
    profile_ref = str(run_row(e, run_id)["profile_ref"])
    token = playback_token(e, "t1", run_id).json()["playback"]["token"]

    def set_state(state: str) -> None:
        with e.sessions().begin() as db:
            db.execute(
                update(ManagedProfileModel)
                .where(ManagedProfileModel.child_id == profile_ref)
                .values(state=state)
            )

    set_state("deleted")
    try:
        assert stream(e, "t1", run_id, token).status_code == 200
        assert complete(e, "t1", run_id).status_code == 200
        again = playback_token(e, "t1", run_id)
        assert again.status_code == 200
        assert stream(e, "t1", run_id, again.json()["playback"]["token"]).status_code == 200
    finally:
        set_state("active")


def _second_ready(v: VEnv) -> tuple[str, str, str]:
    """Abandon whatever t1 still holds (the lock) and walk a new run to READY."""
    e = v.e
    for run_id in list(e.runs):
        if run_row(e, run_id)["run_state"] not in {"COMPLETED", "FAILED", "ABANDONED", "DELETED"}:
            with e.sessions().begin() as db:
                db.execute(
                    update(RUNS).where(RUNS.c.run_id == run_id).values(run_state="ABANDONED")
                )
        e.runs.pop(run_id)
    ready: tuple[str, str, str] = to_ready(v)
    return ready


# ==================================================================== read-only classes (l.364)
@pytest.mark.parametrize("class_state", ["suspended", "archived"])
def test_a_read_only_class_refuses_new_writes_after_the_replay_and_still_plays(
    v: VEnv, class_state: str
) -> None:
    e = v.e
    run_id, digest = to_confirmed_script(e)
    first_revision = run_revision(e, run_id)
    first = request_video(e, "t1", run_id, digest, key="ro-request")
    assert first.status_code == 202
    generation_id = first.json()["video_generation"]["generation_id"]
    runner(v).run_to_end(generation_id)
    token = playback_token(e, "t1", run_id).json()["playback"]["token"]
    set_class_state(e, class_state)
    # the earlier success is still replayed (SRS l.1697) ...
    again = request_video(e, "t1", run_id, digest, key="ro-request", revision=first_revision)
    assert again.status_code == 202
    assert again.json()["video_generation"]["generation_id"] == generation_id
    # ... a new write is 409 INVALID_STATE_TRANSITION and writes nothing
    before = (run_revision(e, run_id), len(receipt_rows(e, run_id)), len(generations(e, run_id)))
    for response in (
        request_video(e, "t1", run_id, digest, reason="OTHER"),
        mark_unsuitable(e, "t1", run_id, generation_id),
        complete(e, "t1", run_id),
    ):
        assert response.status_code == 409, response.text
        assert response.json()["code"] == "INVALID_STATE_TRANSITION"
    assert before == (
        run_revision(e, run_id),
        len(receipt_rows(e, run_id)),
        len(generations(e, run_id)),
    )
    # reads stay allowed: a fresh token and the stream
    assert playback_token(e, "t1", run_id).status_code == 200
    assert stream(e, "t1", run_id, token).status_code == 200
    set_class_state(e, "active")
    assert complete(e, "t1", run_id).status_code == 200


# =================================================================== who may act (l.864-865)
def probes(e: Env, run_id: str, who: str, token: str | None, generation_id: str) -> dict[str, Any]:
    c = e.d.client
    base = f"/v1/story-runs/{run_id}"
    key = uuid4().hex

    def h(with_key: bool = True) -> dict[str, str]:
        return dict(who_headers(e, who, key if with_key else None))

    return {
        "video_generations": c.post(
            f"{base}/video-generations",
            json={"expected_revision": 5, "story_sha256": "a" * 64},
            headers=h(),
        ),
        "video_unsuitable": c.post(
            f"{base}/video-unsuitable",
            json={"expected_revision": 5, "generation_id": generation_id, "reason_code": "OTHER"},
            headers=h(),
        ),
        "complete": c.post(f"{base}/complete", json={"expected_revision": 5}, headers=h()),
        "playback_token": c.post(f"{base}/playback-token", headers=h(False)),
        "playback": c.get(
            f"{base}/playback",
            headers={**h(False), **({"X-Playback-Token": token} if token else {})},
        ),
    }


def counts_of(e: Env) -> dict[str, int]:
    return dict(counts(e.d))


def test_the_twelve_actor_matrix_is_one_uniform_404_with_no_write(v: VEnv) -> None:
    e = v.e
    run_id, _digest, generation_id = to_ready(v)
    token = str(playback_token(e, "t1", run_id).json()["playback"]["token"])
    unknown = probes(e, str(uuid4()), "t1", token, generation_id)
    reference = {name: wire(response) for name, response in unknown.items()}
    for name, (status, body) in reference.items():
        assert status == 404 and body["code"] == "RESOURCE_NOT_FOUND", name
    snapshot = (
        dict(run_row(e, run_id)),
        [dict(r) for r in generations(e, run_id)],
        len(receipt_rows(e, run_id)),
        counts_of(e),
    )
    for who in ACTORS:
        result = probes(e, run_id, who, token, generation_id)
        for name, response in result.items():
            assert wire(response) == reference[name], (who, name)
    assert snapshot == (
        dict(run_row(e, run_id)),
        [dict(r) for r in generations(e, run_id)],
        len(receipt_rows(e, run_id)),
        counts_of(e),
    )


def test_a_run_without_an_occurrence_pin_is_the_uniform_404_on_every_video_route(v: VEnv) -> None:
    e = v.e
    run_id = _seed_generation(
        e.d, None, run_state="VIDEO_READY", generation_state="READY", output=True
    )
    generation_id = str(generations(e, run_id)[0]["video_generation_id"])
    # The unpinned legacy fixture cannot mint a Teacher playback token; malformed and unknown
    # routes still share the uniform not-found envelope.
    token = f"synthetic-token-{uuid4().hex}"
    unknown = {
        name: wire(response)
        for name, response in probes(e, str(uuid4()), "t1", token, generation_id).items()
    }
    for name, response in probes(e, run_id, "t1", token, generation_id).items():
        assert wire(response) == unknown[name], name
    assert generations(e, run_id)[0]["state"] == "READY"  # nothing moved


def test_the_creating_teacher_is_fenced_until_the_transfer_saga_completes(v: VEnv) -> None:
    e = v.e
    run_id, digest = to_confirmed_script(e)
    successor = complete_teacher_transfer(e, run_id)
    unknown = {n: wire(r) for n, r in probes(e, str(uuid4()), "t1", None, str(uuid4())).items()}
    for name, response in probes(e, run_id, "t1", None, str(uuid4())).items():
        assert wire(response) == unknown[name], name
    fresh = request_video(e, successor, run_id, digest)
    assert fresh.status_code == 202, fresh.text
    (generation,) = generations(e, run_id)
    assert generation["state"] == "ACCEPTED"
    (receipt,) = [r for r in receipt_rows(e, run_id) if r["operation"] == VIDEO_OPERATION]
    assert receipt["actor_scope_ref"] == digest_of(e, successor)


def test_a_parent_cannot_act_on_a_teacher_run(v: VEnv) -> None:
    e = v.e
    run_id, digest = to_confirmed_script(e)
    unknown = wire(request_video(e, "parent", str(uuid4()), digest, revision=3))
    assert unknown[0] == 404
    assert wire(request_video(e, "parent", run_id, digest, revision=3)) == unknown
    assert generations(e, run_id) == []


# ================================================================ the key and body rules (D3)
def test_the_key_is_checked_after_the_role_check_and_bad_bodies_are_400(v: VEnv) -> None:
    e = v.e
    run_id, digest = to_confirmed_script(e)
    base = f"/v1/story-runs/{run_id}"
    c = e.d.client
    body = {"expected_revision": 1, "story_sha256": digest}
    # a header-less request is the framework's 400 for everyone; a malformed key is the handler's
    missing = c.post(f"{base}/video-generations", json=body, headers=who_headers(e, "t1"))
    assert missing.status_code == 400
    bad_key = c.post(
        f"{base}/video-generations", json=body, headers=who_headers(e, "t1", "bad key")
    )
    assert bad_key.status_code == 400
    # the role check comes first: a stranger and a Manager with a malformed key get the 404
    for who in ("stranger", "manager", "platform"):
        refused = c.post(
            f"{base}/video-generations", json=body, headers=who_headers(e, who, "bad key")
        )
        assert refused.status_code == 404, who
    bad_body = c.post(
        f"{base}/video-generations",
        json={"expected_revision": 0, "story_sha256": "x"},
        headers=who_headers(e, "t1", uuid4().hex),
    )
    assert bad_body.status_code == 400
    assert generations(e, run_id) == []


# ===================================================================== no content in a body
def test_no_body_or_header_of_the_video_family_carries_a_child_name_or_a_storage_key(
    v: VEnv,
) -> None:
    e = v.e
    run_id, digest = to_confirmed_script(e)
    seen: list[str] = []
    request = request_video(e, "t1", run_id, digest)
    seen.append(request.text + str(dict(request.headers)))
    generation_id = request.json()["video_generation"]["generation_id"]
    runner(v).run_to_end(generation_id)
    token_response = playback_token(e, "t1", run_id)
    seen.append(token_response.text + str(dict(token_response.headers)))
    token = token_response.json()["playback"]["token"]
    played = stream(e, "t1", run_id, token, byte_range="bytes=0-9")
    seen.append(str(dict(played.headers)))
    # the run read of the Teacher shows the video state, never the object key
    view = e.d.client.get(f"/v1/story-runs/{run_id}", headers=who_headers(e, "t1"))
    assert view.status_code == 200, view.text
    video = view.json()["story_run"]["video"]
    assert video is not None and video["current_generation_id"] == generation_id
    seen.append(view.text + str(dict(view.headers)))
    decided = mark_unsuitable(e, "t1", run_id, generation_id)
    seen.append(decided.text + str(dict(decided.headers)))
    blob = " ".join(seen).lower()
    for word in (*STORAGE_WORDS, "amazonaws", NAME_PREFIX.lower()):
        assert word not in blob
    assert not any(name.lower() in blob for name in e.d.children.values())
    # the generation scenes exist for the Teacher run too (the video is its own run's)
    assert scenes_of(e, generation_id)


# ================================================================= concurrency (race tests)
def fresh_confirmed_script(e: Env) -> tuple[str, str]:
    """A new confirmed script on class a1: the previous run is abandoned first (one run each)."""
    for run_id in list(e.runs):
        if run_row(e, run_id)["run_state"] not in {"COMPLETED", "FAILED", "ABANDONED", "DELETED"}:
            with e.sessions().begin() as db:
                db.execute(
                    update(RUNS).where(RUNS.c.run_id == run_id).values(run_state="ABANDONED")
                )
        e.runs.pop(run_id)
    confirmed: tuple[str, str] = to_confirmed_script(e)
    return confirmed


def test_concurrent_requests_with_one_key_make_one_generation_and_the_rest_replay(
    v: VEnv,
) -> None:
    e = v.e
    for round_number in range(30):
        run_id, digest = fresh_confirmed_script(e)
        revision = run_revision(e, run_id)
        key = f"race-key-{round_number}"
        barrier = Barrier(6)

        def call(
            _index: int,
            run_id: str = run_id,
            digest: str = digest,
            revision: int = revision,
            key: str = key,
            barrier: Barrier = barrier,
        ) -> Any:
            barrier.wait(timeout=30)
            return request_video(e, "t1", run_id, digest, key=key, revision=revision)

        with ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(call, range(6)))
        statuses = sorted(r.status_code for r in results)
        assert statuses == [202] * 6, (round_number, statuses, [r.text for r in results])
        assert len({r.json()["video_generation"]["generation_id"] for r in results}) == 1
        assert len(generations(e, run_id)) == 1
        requests = [r for r in receipt_rows(e, run_id) if r["operation"] == VIDEO_OPERATION]
        assert len(requests) == 1 and requests[0]["state"] == "FINAL"


def test_concurrent_requests_with_different_keys_make_exactly_one_winner(v: VEnv) -> None:
    e = v.e
    for round_number in range(30):
        run_id, digest = fresh_confirmed_script(e)
        revision = run_revision(e, run_id)
        barrier = Barrier(6)

        def call(
            _index: int,
            run_id: str = run_id,
            digest: str = digest,
            revision: int = revision,
            barrier: Barrier = barrier,
        ) -> Any:
            barrier.wait(timeout=30)
            return request_video(e, "t1", run_id, digest, key=uuid4().hex, revision=revision)

        with ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(call, range(6)))
        won = [r for r in results if r.status_code == 202]
        lost = [r for r in results if r.status_code != 202]
        # the run row lock is the fence: one request moves the run, the others see a run that moved
        assert len(won) == 1, (round_number, [r.status_code for r in results])
        assert len(lost) == 5 and all(r.status_code == 409 for r in lost), [r.text for r in lost]
        assert len(generations(e, run_id)) == 1
        requests = [r for r in receipt_rows(e, run_id) if r["operation"] == VIDEO_OPERATION]
        assert len(requests) == 1 and requests[0]["state"] == "FINAL"


def test_complete_and_unsuitable_race_for_the_ready_run_with_exactly_one_winner(v: VEnv) -> None:
    e = v.e
    for round_number in range(30):
        for run_id in list(e.runs):
            if run_row(e, run_id)["run_state"] not in {"COMPLETED", "FAILED", "ABANDONED"}:
                with e.sessions().begin() as db:
                    db.execute(
                        update(RUNS).where(RUNS.c.run_id == run_id).values(run_state="ABANDONED")
                    )
            e.runs.pop(run_id)
        run_id, _digest, generation_id = to_ready(v)
        revision = run_revision(e, run_id)
        barrier = Barrier(2)

        def decide(
            index: int,
            run_id: str = run_id,
            generation_id: str = generation_id,
            revision: int = revision,
            barrier: Barrier = barrier,
        ) -> Any:
            barrier.wait(timeout=30)
            if index == 0:
                return complete(e, "t1", run_id, revision=revision)
            return mark_unsuitable(e, "t1", run_id, generation_id, revision=revision)

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(decide, range(2)))
        statuses = sorted(r.status_code for r in results)
        assert statuses == [200, 409], (round_number, statuses, [r.text for r in results])
        final = run_row(e, run_id)["run_state"]
        assert final in {"COMPLETED", "SCRIPT_REVIEW"}
        loser = next(r for r in results if r.status_code == 409)
        assert loser.json()["code"] in {"INVALID_STATE_TRANSITION", "STALE_REVISION"}
