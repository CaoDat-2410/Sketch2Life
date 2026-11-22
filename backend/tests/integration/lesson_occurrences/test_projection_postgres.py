"""FEAT-066 T-5a: the class projection confirmation, the sample-slot claim and the projection token
on PostgreSQL.

SRS l.396 (the playable sample claims the slot; the claim survives a deleted run), l.552 (FR-T-13:
the slot never reopens), l.553 and l.864-865 (access follows the CURRENT responsible Teacher; one
uniform 404), l.555 (FR-T-16: only the responsible Teacher, a short-lived authorization, no
capability for class members), l.777, l.1449, l.1661-1662, l.1691-1693 (the confirmation, the token
and the header-borne stream, re-checked on every request), l.2697 (an old READY output stays pinned
to its old plan), l.364, l.593, l.1425 (a suspended class is read-only), BR-34 (no child name in a
stored value), OD-14 (the claim is the first projection confirmation). Runs only against a
disposable database whose name contains ``be1_acceptance`` and ``frc08``.

The READY sample is made through the real Teacher routes of T-4b2 and T-4b3a/b (the first story is
inserted by SQL, plan review P2-1) and the fixture video runner; the two admission ports are the
accept-all local pair; object storage is in memory; no provider, no network. The fixtures live in
``tests/integration/story_teacher`` and are reached through ``sys.path``.
"""

# ruff: noqa: E402, F811  (the path insert precedes the sibling imports; fixtures are test arguments)

from __future__ import annotations

import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from typing import Any
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "story_teacher"))

import pytest
from sqlalchemy import select, text, update
from test_teacher_run_create_postgres import (  # type: ignore[import-not-found]
    ISSUER,
    NAME_PREFIX,
    _approve_plan,
    counts,
    occurrence_row,
)
from video_support import (  # type: ignore[import-not-found]
    RUNS,
    STORAGE_WORDS,
    Env,
    VEnv,
    api,  # noqa: F401 - re-exported fixture
    cancel,
    complete,
    env,  # noqa: F401 - re-exported fixture
    mark_unsuitable,
    playback_token,
    regenerate_cycle,
    run_revision,
    run_row,
    runner,
    stream,
    to_ready,
    v,  # noqa: F401 - fixture
    who_headers,
    wire,
)

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.story_video import ProjectionClaims
from sketch2life.domain.lesson_occurrences.projection import confirmed_ms
from sketch2life.infrastructure.lesson_occurrences.tables import OCCURRENCES
from sketch2life.infrastructure.persistence.be1_models import (
    Be1CommandReceiptModel,
    ClassroomModel,
    OrganizationAssignmentModel,
)
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.infrastructure.uploads.resolvers import parent_scope_ref

SYNTHETIC_MP4_HEAD = b"\x00\x00\x00\x18ftypmp42"
CONFIRM_ACTION = "lesson.occurrence.projection.confirm"
CLAIM_ACTION = "lesson.occurrence.sample.claim"
# the callers that are not the responsible Teacher, with the answer the decision table gives them
NOT_FOUND_ACTORS = (
    "parent",
    "t2",
    "tother",
    "revoked",
    "inactive",
    "manager",
    "platform",
    "stranger",
)
FORBIDDEN_ACTORS = ("t4", "g1", "o1", "orgt")  # a covered caller who is not the assignee
ROUNDS = 30


# ----------------------------------------------------------------------------- helpers
def occurrence_of(e: Env, run_id: str) -> str:
    return str(run_row(e, run_id)["occurrence_ref"])


def revision_of(e: Env, occurrence_id: str) -> int:
    return int(occurrence_row(e.d, occurrence_id)["revision"])


def confirm(
    e: Env,
    who: str,
    occurrence_id: str,
    run_id: str,
    generation_id: str,
    *,
    key: str | None = None,
    revision: int | None = None,
    **body: Any,
) -> Any:
    payload: dict[str, Any] = {
        "run_id": run_id,
        "generation_id": generation_id,
        "audience": "CLASS",
        "use": "CLASS_PROJECTION",
        **body,
    }
    headers = who_headers(e, who, key or uuid4().hex)
    headers["If-Match"] = f'"{revision if revision is not None else revision_of(e, occurrence_id)}"'
    return e.d.client.post(
        f"/v1/lesson-occurrences/{occurrence_id}/projection-confirmation",
        json=payload,
        headers=headers,
    )


def projection_token(e: Env, who: str, occurrence_id: str) -> Any:
    return e.d.client.post(
        f"/v1/lesson-occurrences/{occurrence_id}/projection-playback-token",
        headers=who_headers(e, who),
    )


def ready_sample(v: VEnv, who: str = "t1") -> tuple[str, str, str]:
    """``(occurrence_id, run_id, generation_id)`` of a Teacher run at ``VIDEO_READY``."""

    run_id, _digest, generation_id = to_ready(v, who)
    return occurrence_of(v.e, run_id), run_id, generation_id


def confirmed_sample(v: VEnv, who: str = "t1") -> tuple[str, str, str, str]:
    """A ready sample, confirmed by ``who``, with a projection token: ``(occ, run, gen, token)``."""

    occurrence_id, run_id, generation_id = ready_sample(v, who)
    assert confirm(v.e, who, occurrence_id, run_id, generation_id).status_code == 200
    response = projection_token(v.e, who, occurrence_id)
    assert response.status_code == 200, response.text
    return occurrence_id, run_id, generation_id, str(response.json()["token"])


def release_all(e: Env) -> None:
    """Free the Teacher lock of every run a test made (the trigger clears it on ``ABANDONED``)."""

    for run_id in list(e.runs):
        if run_row(e, run_id)["run_state"] not in {"COMPLETED", "FAILED", "ABANDONED", "DELETED"}:
            with e.sessions().begin() as db:
                db.execute(
                    update(RUNS).where(RUNS.c.run_id == run_id).values(run_state="ABANDONED")
                )
        e.runs.pop(run_id)


def audit_rows(e: Env, occurrence_id: str) -> list[Any]:
    with e.sessions()() as db:
        return list(
            db.execute(
                select(CoreAuditEntryModel)
                .where(
                    CoreAuditEntryModel.resource_id == occurrence_id,
                    CoreAuditEntryModel.action.in_((CONFIRM_ACTION, CLAIM_ACTION)),
                )
                .order_by(CoreAuditEntryModel.created_at, CoreAuditEntryModel.action)
            )
            .scalars()
            .all()
        )


def principal_digest(e: Env, who: str) -> str:
    return parent_scope_ref(VerifiedPrincipal(e.d.subjects[who], ISSUER, frozenset()))


def forged_token(
    e: Env, who: str, run_id: str, generation_id: str, occurrence_id: str, milliseconds: int
) -> str:
    """A token signed by the app's own codec with claims the Lesson side did not issue."""

    codec = e.d.app.state.story_playback_tokens
    token, _ = codec.issue(
        run_id=run_id,
        generation_id=generation_id,
        actor_digest=codec.actor_binding(principal_digest(e, who)),
        projection=ProjectionClaims(occurrence_id, milliseconds),
    )
    return str(token)


def set_class_state(e: Env, state: str) -> None:
    with e.sessions().begin() as db:
        db.execute(
            update(ClassroomModel)
            .where(ClassroomModel.class_id == e.d.classes["a1"])
            .values(state=state)
        )


def update_occurrence(e: Env, occurrence_id: str, **values: Any) -> None:
    with e.sessions().begin() as db:
        db.execute(
            update(OCCURRENCES).where(OCCURRENCES.c.occurrence_id == occurrence_id).values(**values)
        )


def assert_untouched(before: dict[str, Any], e: Env, occurrence_id: str) -> None:
    assert occurrence_row(e.d, occurrence_id) == before


def streams(response: Any) -> bool:
    return bool(response.status_code == 200 and response.content.startswith(SYNTHETIC_MP4_HEAD))


# ----------------------------------------------------------------------------- the claim
def test_the_first_confirmation_claims_the_slot_and_writes_the_receipt_and_two_audit_rows(
    v: VEnv,
) -> None:
    e = v.e
    occurrence_id, run_id, generation_id = ready_sample(v)
    before = occurrence_row(e.d, occurrence_id)
    assert (before["sample_slot_state"], before["state"]) == ("AVAILABLE", "APPROVED")
    assert before["successful_sample_run_ref"] is None
    tables_before = counts(e.d)
    response = confirm(e, "t1", occurrence_id, run_id, generation_id)
    assert response.status_code == 200, response.text
    assert response.headers["Cache-Control"] == "private, no-store"
    after = occurrence_row(e.d, occurrence_id)
    assert response.headers["ETag"] == f'"{after["revision"]}"'
    body = response.json()
    assert body["contract"] == "ClassProjectionConfirmationV1"
    assert (body["occurrence_id"], body["run_id"], body["generation_id"]) == (
        occurrence_id,
        run_id,
        generation_id,
    )
    assert (body["audience"], body["use"]) == ("CLASS", "CLASS_PROJECTION")
    assert body["confirmed_by_ref"] == e.d.accounts["t1"]
    assert body["occurrence_revision"] == after["revision"] == before["revision"] + 1
    assert body["plan"]["is_current"] is True and body["plan"]["revision_no"] == 1
    with e.sessions()() as db:
        class_revision = db.scalar(
            select(ClassroomModel.revision).where(ClassroomModel.class_id == e.d.classes["a1"])
        )
    assert body["assignment"] == {"class_revision": class_revision}
    assert body["sample_video"]["slot_state"] == "CLAIMED"
    assert body["sample_video"]["run_ref"] == run_id
    # the occurrence row: one compare-and-set, the plan pointer untouched
    assert after["sample_slot_state"] == "CLAIMED" and after["state"] == "SAMPLE_USED"
    assert after["successful_sample_run_ref"] == run_id and after["sample_claimed_at"] is not None
    assert after["class_projection_confirmed_by_ref"] == e.d.accounts["t1"]
    assert after["class_projection_confirmed_at"] is not None
    assert after["approved_plan_revision_id"] == before["approved_plan_revision_id"]
    # two audit rows, refs and the literals only
    rows = audit_rows(e, occurrence_id)
    assert sorted((row.action, row.decision) for row in rows) == sorted(
        [(CLAIM_ACTION, "CLAIMED"), (CONFIRM_ACTION, "CLASS/CLASS_PROJECTION")]
    )
    assert {row.actor_ref for row in rows} == {e.d.accounts["t1"]}
    assert {row.organization_id for row in rows} == {e.d.organization}
    # no quota, billing, job, usage, capacity or outbox row moved
    assert counts(e.d) == tables_before
    # the stored receipt holds refs only
    with e.sessions()() as db:
        stored = db.execute(select(Be1CommandReceiptModel)).scalars().all()
    text_body = repr([item.response_json for item in stored])
    assert NAME_PREFIX not in text_body
    assert not any(name in text_body for name in e.d.children.values())


def test_a_replay_by_key_returns_the_stored_body_and_writes_nothing(v: VEnv) -> None:
    e = v.e
    occurrence_id, run_id, generation_id = ready_sample(v)
    revision = revision_of(e, occurrence_id)
    first = confirm(e, "t1", occurrence_id, run_id, generation_id, key="replay-key")
    assert first.status_code == 200
    after = occurrence_row(e.d, occurrence_id)
    rows = len(audit_rows(e, occurrence_id))
    again = confirm(
        e, "t1", occurrence_id, run_id, generation_id, key="replay-key", revision=revision
    )
    assert again.status_code == 200 and again.json() == first.json()
    assert again.headers["ETag"] == first.headers["ETag"]
    assert occurrence_row(e.d, occurrence_id) == after and len(audit_rows(e, occurrence_id)) == rows
    # another request under the same key is 400, whatever else is right
    other = confirm(
        e, "t1", occurrence_id, run_id, generation_id, key="replay-key", revision=revision + 5
    )
    assert other.status_code == 400 and other.json()["code"] == "INVALID_IDEMPOTENCY_KEY"
    assert occurrence_row(e.d, occurrence_id) == after


def test_a_second_key_by_the_same_teacher_writes_nothing_and_keeps_the_token_alive(
    v: VEnv,
) -> None:
    e = v.e
    occurrence_id, run_id, generation_id, token = confirmed_sample(v)
    after = occurrence_row(e.d, occurrence_id)
    rows = len(audit_rows(e, occurrence_id))
    again = confirm(e, "t1", occurrence_id, run_id, generation_id)  # a new key, the new revision
    assert again.status_code == 200, again.text
    assert (
        again.json()["confirmed_at"]
        == confirm(e, "t1", occurrence_id, run_id, generation_id).json()["confirmed_at"]
    )
    assert occurrence_row(e.d, occurrence_id) == after  # no revision bump, no new pair
    assert len(audit_rows(e, occurrence_id)) == rows
    assert streams(stream(e, "t1", run_id, token))  # a double click never ends a playing video


# ----------------------------------------------------------------------------- the token
def test_the_token_needs_a_confirmation_then_streams_whole_and_by_range(v: VEnv) -> None:
    e = v.e
    occurrence_id, run_id, generation_id = ready_sample(v)
    before = projection_token(e, "t1", occurrence_id)
    assert before.status_code == 409 and before.json()["code"] == "INVALID_STATE_TRANSITION"
    assert confirm(e, "t1", occurrence_id, run_id, generation_id).status_code == 200
    response = projection_token(e, "t1", occurrence_id)
    assert response.status_code == 200, response.text
    assert response.headers["Cache-Control"] == "no-store"
    grant = response.json()
    assert set(grant) == {"contract", "token", "expires_at", "stream_path", "media_type"}
    assert grant["stream_path"] == f"/v1/story-runs/{run_id}/playback"
    assert grant["media_type"] == "video/mp4"
    assert not any(word in response.text.lower() for word in STORAGE_WORDS)
    assert streams(stream(e, "t1", run_id, grant["token"]))
    part = stream(e, "t1", run_id, grant["token"], byte_range="bytes=0-3")
    assert part.status_code == 206 and part.content == SYNTHETIC_MP4_HEAD[:4]
    assert stream(e, "t1", run_id, grant["token"], byte_range="bytes=99999999-").status_code == 416
    # the stream needs the token: none, junk
    assert stream(e, "t1", run_id, None).status_code == 401
    assert stream(e, "t1", run_id, "junk").status_code == 401
    # the owner-view token of T-4b3b keeps working and is not a projection token
    owner = playback_token(e, "t1", run_id)
    assert owner.status_code == 200
    assert streams(stream(e, "t1", run_id, owner.json()["playback"]["token"]))


def test_a_projection_token_never_streams_for_another_caller_run_or_claim(v: VEnv) -> None:
    e = v.e
    occurrence_id, run_id, generation_id, token = confirmed_sample(v)
    confirmed = occurrence_row(e.d, occurrence_id)["class_projection_confirmed_at"]
    assert streams(stream(e, "t1", run_id, token))
    other_run = str(uuid4())
    assert stream(e, "t1", other_run, token).status_code == 404
    # a token signed by the app with a wrong claim: another confirmation time, another occurrence
    good_ms = confirmed_ms(confirmed)
    for forged in (
        forged_token(e, "t1", run_id, generation_id, occurrence_id, good_ms + 1),
        forged_token(e, "t1", run_id, generation_id, occurrence_id, good_ms - 1),
        forged_token(e, "t1", run_id, generation_id, str(uuid4()), good_ms),
        forged_token(e, "t1", run_id, str(uuid4()), occurrence_id, good_ms),
    ):
        assert stream(e, "t1", run_id, forged).status_code == 404
    # the same claims signed for the same Teacher stream
    assert streams(
        stream(
            e, "t1", run_id, forged_token(e, "t1", run_id, generation_id, occurrence_id, good_ms)
        )
    )
    # and for another Teacher of the same class the digest differs: the uniform 404
    other_teacher = forged_token(e, "t4", run_id, generation_id, occurrence_id, good_ms)
    assert stream(e, "t4", run_id, other_teacher).status_code == 404
    assert stream(e, "t4", run_id, token).status_code == 404  # t1's token in t4's hands
    assert stream(e, "parent", run_id, token).status_code == 404


# ------------------------------------------------------------------ refusals of the confirmation
def test_a_sample_that_is_not_playable_or_not_the_current_one_is_refused_and_nothing_is_written(
    v: VEnv,
) -> None:
    e = v.e
    occurrence_id, run_id, generation_id = ready_sample(v)
    before = occurrence_row(e.d, occurrence_id)
    revision = int(before["revision"])
    # another generation, an unknown run
    for pair in ((run_id, str(uuid4())), (str(uuid4()), generation_id)):
        response = confirm(e, "t1", occurrence_id, *pair)
        assert response.status_code == 409 and response.json()["code"] == "STALE_REVISION"
        assert response.json()["current_version"] == revision
    # a stale If-Match carries the current version
    stale = confirm(e, "t1", occurrence_id, run_id, generation_id, revision=revision + 7)
    assert stale.status_code == 409 and stale.json()["code"] == "STALE_REVISION"
    assert stale.json()["current_version"] == revision
    assert_untouched(before, e, occurrence_id)
    # not playable: the run left VIDEO_READY (the adult marked the video unsuitable)
    assert mark_unsuitable(e, "t1", run_id, generation_id).status_code == 200
    refused = confirm(e, "t1", occurrence_id, run_id, generation_id)
    assert refused.status_code == 409 and refused.json()["code"] == "INVALID_STATE_TRANSITION"
    assert_untouched(before, e, occurrence_id)
    assert not audit_rows(e, occurrence_id)


def test_a_completed_run_can_no_longer_be_projected_and_the_slot_stays_available_open_2(
    v: VEnv,
) -> None:
    """OPEN-2: a sample completed before projection is never claimed (the token needs VIDEO_READY,
    SRS l.1676); the slot stays AVAILABLE and the run still holds the sample (T-4b2 D6)."""

    e = v.e
    occurrence_id, run_id, generation_id = ready_sample(v)
    before = occurrence_row(e.d, occurrence_id)
    assert complete(e, "t1", run_id).status_code == 200
    assert_untouched(before, e, occurrence_id)  # Complete never touches the slot (FR-T-13)
    response = confirm(e, "t1", occurrence_id, run_id, generation_id)
    assert response.status_code == 409 and response.json()["code"] == "INVALID_STATE_TRANSITION"
    assert projection_token(e, "t1", occurrence_id).status_code == 409
    assert_untouched(before, e, occurrence_id)
    assert not audit_rows(e, occurrence_id)


def test_the_run_of_another_occurrence_is_a_stale_pair_and_writes_nothing(v: VEnv) -> None:
    e = v.e
    first_occurrence, first_run, first_generation = ready_sample(v)
    assert complete(e, "t1", first_run).status_code == 200  # frees the Teacher lock
    second_occurrence, second_run, second_generation = ready_sample(v)
    assert second_occurrence != first_occurrence
    before = occurrence_row(e.d, second_occurrence)
    other = occurrence_row(e.d, first_occurrence)
    response = confirm(e, "t1", second_occurrence, first_run, first_generation)
    assert response.status_code == 409 and response.json()["code"] == "STALE_REVISION"
    assert_untouched(before, e, second_occurrence)
    assert_untouched(other, e, first_occurrence)
    assert confirm(e, "t1", second_occurrence, second_run, second_generation).status_code == 200


def test_a_slot_claimed_by_another_run_or_with_an_emptied_pointer_refuses_every_confirmation(
    v: VEnv,
) -> None:
    e = v.e
    occurrence_id, run_id, generation_id, _token = confirmed_sample(v)
    for pointer in (str(uuid4()), None):  # another run; a deleted run clears the pointer (l.396)
        update_occurrence(e, occurrence_id, successful_sample_run_ref=pointer)
        before = occurrence_row(e.d, occurrence_id)
        response = confirm(e, "t1", occurrence_id, run_id, generation_id)
        assert response.status_code == 409
        assert response.json()["code"] == "SAMPLE_VIDEO_ALREADY_EXISTS"
        assert_untouched(before, e, occurrence_id)
        assert before["sample_slot_state"] == "CLAIMED"  # the claim is kept
        assert projection_token(e, "t1", occurrence_id).status_code == 409


def test_an_archived_occurrence_and_a_suspended_class_refuse_the_projection_only(
    v: VEnv,
) -> None:
    e = v.e
    occurrence_id, run_id, generation_id, token = confirmed_sample(v)
    owner_token = playback_token(e, "t1", run_id).json()["playback"]["token"]
    revision = revision_of(e, occurrence_id)
    set_class_state(e, "suspended")
    try:
        before = occurrence_row(e.d, occurrence_id)
        again = confirm(e, "t1", occurrence_id, run_id, generation_id)
        assert again.status_code == 409 and again.json()["code"] == "INVALID_STATE_TRANSITION"
        assert projection_token(e, "t1", occurrence_id).status_code == 409
        # the class projection needs an active class (R2 N-3); the owner view is a read
        assert stream(e, "t1", run_id, token).status_code == 404
        assert streams(stream(e, "t1", run_id, owner_token))
        assert_untouched(before, e, occurrence_id)
    finally:
        set_class_state(e, "active")
    assert streams(stream(e, "t1", run_id, token))  # the same token works again
    update_occurrence(e, occurrence_id, state="ARCHIVED")
    assert confirm(e, "t1", occurrence_id, run_id, generation_id).status_code == 409
    assert projection_token(e, "t1", occurrence_id).status_code == 409
    assert stream(e, "t1", run_id, token).status_code == 404
    assert revision_of(e, occurrence_id) == revision


def test_a_replay_answers_even_after_the_class_was_suspended(v: VEnv) -> None:
    e = v.e
    occurrence_id, run_id, generation_id = ready_sample(v)
    revision = revision_of(e, occurrence_id)
    first = confirm(e, "t1", occurrence_id, run_id, generation_id, key="before-suspend")
    assert first.status_code == 200
    set_class_state(e, "suspended")
    try:
        replay = confirm(
            e, "t1", occurrence_id, run_id, generation_id, key="before-suspend", revision=revision
        )
        assert replay.status_code == 200 and replay.json() == first.json()
    finally:
        set_class_state(e, "active")


# ----------------------------------------------------------------------------- authorization
def test_the_decision_table_on_both_routes_and_the_stream_is_uniform(v: VEnv) -> None:
    e = v.e
    occurrence_id, run_id, generation_id = ready_sample(v)
    before = occurrence_row(e.d, occurrence_id)
    tables_before = counts(e.d)
    unknown = f"/v1/lesson-occurrences/{uuid4()}"
    expected_404 = wire(
        e.d.client.post(
            unknown + "/projection-confirmation",
            json={
                "run_id": run_id,
                "generation_id": generation_id,
                "audience": "CLASS",
                "use": "CLASS_PROJECTION",
            },
            headers={**who_headers(e, "t1", uuid4().hex), "If-Match": '"1"'},
        )
    )
    assert expected_404[0] == 404
    confirm_answers: dict[str, Any] = {}
    token_answers: dict[str, Any] = {}
    for who in (*NOT_FOUND_ACTORS, *FORBIDDEN_ACTORS):
        confirm_answers[who] = wire(confirm(e, who, occurrence_id, run_id, generation_id))
        token_answers[who] = wire(projection_token(e, who, occurrence_id))
    for who in NOT_FOUND_ACTORS:
        assert confirm_answers[who] == expected_404, who  # the same bytes as an unknown id
        assert token_answers[who] == expected_404, who
    for who in FORBIDDEN_ACTORS:
        for answers in (confirm_answers, token_answers):
            assert answers[who][0] == 403 and answers[who][1]["code"] == "ACTION_NOT_ALLOWED", who
    assert_untouched(before, e, occurrence_id)
    assert counts(e.d) == tables_before
    assert not audit_rows(e, occurrence_id)
    # the responsible Teacher still confirms, and then every other caller is 404 at the stream
    assert confirm(e, "t1", occurrence_id, run_id, generation_id).status_code == 200
    token = str(projection_token(e, "t1", occurrence_id).json()["token"])
    answers = {
        who: wire(stream(e, who, run_id, token)) for who in (*NOT_FOUND_ACTORS, *FORBIDDEN_ACTORS)
    }
    assert {answer[0] for answer in answers.values()} == {404}
    assert len({repr(answer) for answer in answers.values()}) == 1  # one uniform body
    assert streams(stream(e, "t1", run_id, token))


def test_the_responsible_teacher_follows_the_current_assignment_not_the_creator(v: VEnv) -> None:
    e = v.e
    occurrence_id, run_id, generation_id, old_token = confirmed_sample(v)
    first = occurrence_row(e.d, occurrence_id)
    # a reassignment by SQL (T-6x is deferred): t4 holds an exact-class teacher row of the class
    update_occurrence(e, occurrence_id, responsible_teacher_ref=e.d.accounts["t4"])
    assert stream(e, "t1", run_id, old_token).status_code == 404  # the old token ends at once
    assert confirm(e, "t1", occurrence_id, run_id, generation_id).status_code == 403
    assert projection_token(e, "t1", occurrence_id).status_code == 403
    # the new Teacher has no confirmation of their own yet
    assert projection_token(e, "t4", occurrence_id).status_code == 409
    response = confirm(e, "t4", occurrence_id, run_id, generation_id)
    assert response.status_code == 200, response.text
    after = occurrence_row(e.d, occurrence_id)
    assert after["class_projection_confirmed_by_ref"] == e.d.accounts["t4"]
    assert after["revision"] == first["revision"] + 1
    # the claim is never changed: same run, same claim time, same slot, same state
    assert (after["sample_slot_state"], after["successful_sample_run_ref"], after["state"]) == (
        first["sample_slot_state"],
        first["successful_sample_run_ref"],
        first["state"],
    )
    assert after["sample_claimed_at"] == first["sample_claimed_at"]
    new_token = str(projection_token(e, "t4", occurrence_id).json()["token"])
    assert streams(stream(e, "t4", run_id, new_token))
    assert stream(e, "t1", run_id, old_token).status_code == 404
    assert stream(e, "t1", run_id, new_token).status_code == 404
    rows = [(row.action, row.actor_ref) for row in audit_rows(e, occurrence_id)]
    assert rows.count((CONFIRM_ACTION, e.d.accounts["t4"])) == 1
    assert rows.count((CLAIM_ACTION, e.d.accounts["t1"])) == 1


def test_a_revoked_assignment_ends_playback_at_the_next_request(v: VEnv) -> None:
    e = v.e
    occurrence_id, run_id, _generation_id, token = confirmed_sample(v)
    assert streams(stream(e, "t1", run_id, token))

    def set_active(active: bool) -> None:
        with e.sessions().begin() as db:
            db.execute(
                update(OrganizationAssignmentModel)
                .where(
                    OrganizationAssignmentModel.subject == e.d.subjects["t1"],
                    OrganizationAssignmentModel.role == "teacher",
                )
                .values(active=active)
            )

    set_active(False)
    try:
        assert stream(e, "t1", run_id, token).status_code == 404
        assert projection_token(e, "t1", occurrence_id).status_code == 404
    finally:
        set_active(True)
    assert streams(stream(e, "t1", run_id, token))


# ------------------------------------------------------------------ the lifecycle of the sample
def test_a_new_confirmation_after_a_regeneration_covers_the_new_generation_only(v: VEnv) -> None:
    e = v.e
    occurrence_id, run_id, generation_id, old_token = confirmed_sample(v)
    first = occurrence_row(e.d, occurrence_id)
    # the adult marks the sample unsuitable and regenerates: the slot keeps its claim (FR-T-13)
    new_generation = regenerate_cycle(v, run_id, generation_id, number=2)
    assert stream(e, "t1", run_id, old_token).status_code == 404  # unsuitable ended the old token
    assert occurrence_row(e.d, occurrence_id)["sample_slot_state"] == "CLAIMED"
    final = runner(v).run_to_end(new_generation)
    assert final.record is not None and final.record.state == "READY"
    # the stored confirmation predates the new generation: it covers nothing (SRS l.777)
    assert projection_token(e, "t1", occurrence_id).status_code == 409
    old = confirm(e, "t1", occurrence_id, run_id, generation_id)
    assert old.status_code == 409 and old.json()["code"] == "STALE_REVISION"
    response = confirm(e, "t1", occurrence_id, run_id, new_generation)
    assert response.status_code == 200, response.text
    after = occurrence_row(e.d, occurrence_id)
    assert after["revision"] == first["revision"] + 1
    assert after["class_projection_confirmed_at"] > first["class_projection_confirmed_at"]
    assert after["sample_claimed_at"] == first["sample_claimed_at"]  # never claimed twice
    assert after["successful_sample_run_ref"] == run_id
    assert sum(1 for row in audit_rows(e, occurrence_id) if row.action == CLAIM_ACTION) == 1
    new_token = str(projection_token(e, "t1", occurrence_id).json()["token"])
    assert streams(stream(e, "t1", run_id, new_token))
    assert stream(e, "t1", run_id, old_token).status_code == 404


def test_cancel_unsuitable_and_complete_end_playback_and_never_reopen_the_slot(v: VEnv) -> None:
    e = v.e
    for ending in ("cancel", "unsuitable", "complete"):
        release_all(e)
        occurrence_id, run_id, generation_id, token = confirmed_sample(v)
        claimed = occurrence_row(e.d, occurrence_id)
        assert streams(stream(e, "t1", run_id, token))
        if ending == "cancel":
            assert cancel(e, "t1", run_id).status_code == 202
        elif ending == "unsuitable":
            assert mark_unsuitable(e, "t1", run_id, generation_id).status_code == 200
        else:
            assert complete(e, "t1", run_id).status_code == 200
        assert stream(e, "t1", run_id, token).status_code == 404, ending
        assert projection_token(e, "t1", occurrence_id).status_code == 409, ending
        after = occurrence_row(e.d, occurrence_id)
        assert after["sample_slot_state"] == "CLAIMED" and after["state"] == "SAMPLE_USED", ending
        assert after["successful_sample_run_ref"] == run_id
        assert after["sample_claimed_at"] == claimed["sample_claimed_at"]
        confirmed = confirm(e, "t1", occurrence_id, run_id, generation_id)
        assert confirmed.status_code == 409, ending  # not playable any more


def test_a_run_pinned_to_a_superseded_plan_is_confirmed_claimed_and_projected_open_1(
    v: VEnv,
) -> None:
    """SRS l.2697: the READY output stays pinned to its old plan and "no implicit supersession
    hide". The receipt shows the pin and ``is_current false``; there is still exactly one claim."""

    e = v.e
    occurrence_id, run_id, generation_id = ready_sample(v)
    before = occurrence_row(e.d, occurrence_id)
    _pointer, _hash, number, _activity = _approve_plan(e.d, occurrence_id, 1, "t1")
    assert number == 2
    assert (
        occurrence_row(e.d, occurrence_id)["approved_plan_revision_id"]
        != (before["approved_plan_revision_id"])
    )
    response = confirm(e, "t1", occurrence_id, run_id, generation_id)
    assert response.status_code == 200, response.text
    plan = response.json()["plan"]
    assert plan["revision_no"] == 1 and plan["is_current"] is False
    after = occurrence_row(e.d, occurrence_id)
    assert after["sample_slot_state"] == "CLAIMED" and after["state"] == "SAMPLE_USED"
    token = str(projection_token(e, "t1", occurrence_id).json()["token"])
    assert streams(stream(e, "t1", run_id, token))
    # a later plan approval does not end the projection and does not reopen the slot
    _approve_plan(e.d, occurrence_id, 2, "t1")
    assert streams(stream(e, "t1", run_id, token))
    final = occurrence_row(e.d, occurrence_id)
    assert (final["sample_slot_state"], final["state"]) == ("CLAIMED", "SAMPLE_USED")
    assert final["successful_sample_run_ref"] == run_id


def test_a_pin_that_names_no_plan_of_this_occurrence_is_a_stale_pair(v: VEnv) -> None:
    e = v.e
    occurrence_id, run_id, generation_id = ready_sample(v)
    before = occurrence_row(e.d, occurrence_id)
    for change in (
        "jsonb_set(lesson_pin_snapshot, '{plan_revision_id}', to_jsonb(gen_random_uuid()::text))",
        "jsonb_set(lesson_pin_snapshot, '{plan_hash}', to_jsonb(repeat('b', 64)))",
        "lesson_pin_snapshot - 'plan_revision_no'",
    ):
        with e.sessions().begin() as db:
            originals = db.execute(
                text(
                    "select run_input_id, lesson_pin_snapshot::text from story.run_inputs "
                    "where run_id = :r"
                ),
                {"r": run_id},
            ).all()
            db.execute(text("set local session_replication_role = replica"))
            db.execute(
                text(
                    f"update story.run_inputs set lesson_pin_snapshot = {change} where run_id = :r"
                ),  # noqa: S608
                {"r": run_id},
            )
        try:
            response = confirm(e, "t1", occurrence_id, run_id, generation_id)
            assert response.status_code == 409 and response.json()["code"] == "STALE_REVISION"
            assert_untouched(before, e, occurrence_id)
        finally:
            with e.sessions().begin() as db:
                db.execute(text("set local session_replication_role = replica"))
                for input_id, original in originals:
                    db.execute(
                        text(
                            "update story.run_inputs set lesson_pin_snapshot = cast(:o as jsonb) "
                            "where run_input_id = :i"
                        ),
                        {"o": original, "i": input_id},
                    )
    assert confirm(e, "t1", occurrence_id, run_id, generation_id).status_code == 200


def test_no_child_name_reaches_a_stored_value_a_log_or_the_audit_trail(
    v: VEnv, caplog: pytest.LogCaptureFixture
) -> None:
    import logging

    caplog.set_level(logging.DEBUG)
    e = v.e
    occurrence_id, run_id, _generation_id, token = confirmed_sample(v)
    assert streams(stream(e, "t1", run_id, token))
    names = list(e.d.children.values())
    assert not any(name in caplog.text for name in names)
    assert token not in caplog.text  # the token is never logged
    with e.sessions()() as db:
        for table in ("core_audit_entries", "be1_command_receipts", "lesson.occurrences"):
            dumped = db.execute(text(f"select t::text from {table} t")).scalars().all()  # noqa: S608
            assert not any(name in row for row in dumped for name in names), table
    rows = audit_rows(e, occurrence_id)
    assert all(NAME_PREFIX not in repr(row.__dict__) for row in rows)


# ----------------------------------------------------------------------------- races (exact counts)
def test_eight_concurrent_first_confirmations_make_exactly_one_claim(v: VEnv) -> None:
    e = v.e
    for round_number in range(ROUNDS):
        release_all(e)
        occurrence_id, run_id, generation_id = ready_sample(v)
        revision = revision_of(e, occurrence_id)
        barrier = Barrier(8)

        def call(
            _index: int,
            occurrence_id: str = occurrence_id,
            run_id: str = run_id,
            generation_id: str = generation_id,
            revision: int = revision,
            barrier: Barrier = barrier,
        ) -> Any:
            barrier.wait(timeout=30)
            return confirm(
                e, "t1", occurrence_id, run_id, generation_id, key=uuid4().hex, revision=revision
            )

        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(call, range(8)))
        won = [r for r in results if r.status_code == 200]
        lost = [r for r in results if r.status_code != 200]
        # the occurrence lock serialises them: one writes, the seven see the new revision
        assert len(won) == 1, (round_number, [r.status_code for r in results])
        assert len(lost) == 7 and all(r.status_code == 409 for r in lost), [r.text for r in lost]
        assert {r.json()["code"] for r in lost} == {"STALE_REVISION"}
        after = occurrence_row(e.d, occurrence_id)
        assert after["revision"] == revision + 1 and after["sample_slot_state"] == "CLAIMED"
        rows = audit_rows(e, occurrence_id)
        assert [row.action for row in rows].count(CLAIM_ACTION) == 1
        assert [row.action for row in rows].count(CONFIRM_ACTION) == 1


def test_eight_concurrent_confirmations_with_one_key_make_one_write_and_seven_replays(
    v: VEnv,
) -> None:
    e = v.e
    for round_number in range(ROUNDS):
        release_all(e)
        occurrence_id, run_id, generation_id = ready_sample(v)
        revision = revision_of(e, occurrence_id)
        key = f"race-key-{round_number}-{uuid4().hex}"
        barrier = Barrier(8)

        def call(
            _index: int,
            occurrence_id: str = occurrence_id,
            run_id: str = run_id,
            generation_id: str = generation_id,
            revision: int = revision,
            key: str = key,
            barrier: Barrier = barrier,
        ) -> Any:
            barrier.wait(timeout=30)
            return confirm(
                e, "t1", occurrence_id, run_id, generation_id, key=key, revision=revision
            )

        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(call, range(8)))
        assert [r.status_code for r in results] == [200] * 8, (
            round_number,
            [r.text for r in results],
        )
        assert len({repr(r.json()) for r in results}) == 1  # one body for all eight
        assert occurrence_row(e.d, occurrence_id)["revision"] == revision + 1
        assert len(audit_rows(e, occurrence_id)) == 2


def test_a_confirmation_racing_a_cancel_is_ordered_by_the_run_lock(v: VEnv) -> None:
    e = v.e
    outcomes: set[tuple[int, int]] = set()
    for round_number in range(ROUNDS):
        release_all(e)
        occurrence_id, run_id, generation_id = ready_sample(v)
        revision = revision_of(e, occurrence_id)
        run_rev = run_revision(e, run_id)
        barrier = Barrier(2)

        def call(
            index: int,
            occurrence_id: str = occurrence_id,
            run_id: str = run_id,
            generation_id: str = generation_id,
            revision: int = revision,
            barrier: Barrier = barrier,
        ) -> Any:
            barrier.wait(timeout=30)
            if index == 0:
                return confirm(e, "t1", occurrence_id, run_id, generation_id, revision=revision)
            return cancel(e, "t1", run_id)

        with ThreadPoolExecutor(max_workers=2) as pool:
            confirm_result, cancel_result = list(pool.map(call, range(2)))
        assert cancel_result.status_code == 202, (round_number, cancel_result.text)
        assert confirm_result.status_code in {200, 409}, confirm_result.text
        after = occurrence_row(e.d, occurrence_id)
        if confirm_result.status_code == 200:
            # the confirmation took the run lock first: the claim is written and survives the cancel
            assert after["sample_slot_state"] == "CLAIMED" and after["revision"] == revision + 1
        else:
            # the cancel won: the run is no longer playable and the slot was never touched
            assert confirm_result.json()["code"] in {"INVALID_STATE_TRANSITION", "STALE_REVISION"}
            assert after["sample_slot_state"] == "AVAILABLE" and after["revision"] == revision
        outcomes.add((confirm_result.status_code, cancel_result.status_code))
        assert run_revision(e, run_id) >= run_rev
    assert outcomes <= {(200, 202), (409, 202)}
