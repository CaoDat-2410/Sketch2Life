"""FEAT-066 T-4b3a: the Teacher side of the StoryRun input routes on PostgreSQL.

SRS l.1664-1668 and l.1676 ("Actor của run"), l.553 (FR-T-14: access follows the CURRENT
assignment), l.394, l.1413 (a subject edit reruns the VLM), l.516, l.551 (the first story plus
three rewrites), l.864-865 (one uniform 404), l.1697-1699 (keys, replay, ``STALE_REVISION``), l.364,
l.593, l.1425 (a suspended or archived class is read-only), BR-34 (no child name in a stored value).
Runs only against a disposable database whose name contains ``be1_acceptance`` and ``frc08``.

The Teacher run is created through the real T-4b2 route; uploads, drawing, idea, transcript,
context, subject and rewrites go through the real routes. The first story starts by itself at the
last confirmation (V4-A OPEN-A D1); ``seed_first_story`` is kept for the one test that needs a story
over a run that never met the gates. Object storage is in memory; the analyzer, the
transcriber and the story generator are deterministic doubles; no provider, no network.
"""

# ruff: noqa: F811  (the imported ``env`` fixture is used as a test argument)

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from typing import Any
from uuid import uuid4

import pytest
from inputs_support import (  # type: ignore[import-not-found]
    SPEECH,
    SUBJECT,
    Env,
    api,  # noqa: F401 - the T-4b2 fixture, re-exported by the support module
    asset_rows,
    attach,
    complete_upload,
    confirm_context,
    confirm_subject,
    confirm_transcript,
    decision_rows,
    drawing_handle,
    env,  # noqa: F401 - fixture
    idea,
    input_rows,
    mask,
    new_run,
    read_transcript,
    receipt_rows,
    register_analysis,
    rewrite,
    run_revision,
    run_row,
    seed_first_story,
    sha,
    states,
    story_rows,
    to_script_review,
    to_subject_review,
    transcript_rows,
    understanding_rows,
    upload,
    upload_session_rows,
    wav_bytes,
    who_headers,
    wire,
)
from sqlalchemy import insert, null, select, text, update
from test_teacher_run_create_postgres import (  # type: ignore[import-not-found]
    NAME_PREFIX,
    counts,
)

from sketch2life.application.ports.parent_story_inputs import StoryGenerationFailure
from sketch2life.application.ports.story_task_reaper import AUDIT_REWRITE_ATTEMPT_FAILED
from sketch2life.infrastructure.lesson_occurrences.tables import OCCURRENCES
from sketch2life.infrastructure.persistence.be1_models import (
    ClassroomModel,
    OrganizationAssignmentModel,
)
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.infrastructure.story_run_lite import tables as story_tables

RUNS = story_tables.story_runs


def text_sha(value: str) -> str:
    return str(sha(value.encode("utf-8")))


def all_story_text(e: Env, run_id: str) -> str:
    """Every stored text column of one run, for the no-child-name checks."""
    parts: list[str] = []
    for rows in (
        input_rows(e, run_id),
        understanding_rows(e, run_id),
        transcript_rows(e, run_id),
        story_rows(e, run_id),
        receipt_rows(e, run_id),
        decision_rows(e, run_id),
    ):
        parts.extend(str(dict(row)) for row in rows)
    parts.append(str(dict(run_row(e, run_id))))
    return " ".join(parts)


def assert_no_child_name(e: Env, text_body: str) -> None:
    assert NAME_PREFIX not in text_body
    assert not any(name in text_body for name in e.d.children.values())


# ================================================================================== the happy path
def test_a_teacher_attaches_the_drawing_with_organization_scope_rows(env: Env) -> None:
    e = env
    run_id = new_run(e)
    handle, data = drawing_handle(e, "t1", run_id)
    register_analysis(e, data)
    org = e.d.organization
    # the upload session of a Teacher is bound to the organization, never to NULL (P2-2)
    sessions = upload_session_rows(e, run_id)
    assert len(sessions) == 1
    assert sessions[0]["owner_scope_kind"] == "ORGANIZATION"
    assert sessions[0]["owner_scope_ref"] == org and sessions[0]["organization_id"] == org
    assert sessions[0]["owner_principal_ref"] == e.d.subjects["t1"]
    before = counts(e.d)

    response = attach(e, "t1", run_id, handle)
    assert response.status_code == 202, response.text
    body = response.json()
    assert body["asset_ref"] == handle and body["asset_state"] == "READY"
    assert body["run_state"] == "INPUT_PROCESSING" and body["analysis_state"] == "QUEUED"
    assert response.headers["Content-Location"] == f"/v1/story-runs/{run_id}"
    # the analysis ran after the response, job-side, on the Teacher run
    assert states(e, run_id) == ("SUBJECT_REVIEW", "SUCCEEDED")
    assert len(e.analyzer.calls) == 1
    (understanding,) = understanding_rows(e, run_id)
    assert understanding["subject_label"] == SUBJECT

    rows = asset_rows(e, run_id)
    assert len(rows) == 2  # the upload original and the normalized copy
    for row in rows:
        assert row.owner_scope_kind == "ORGANIZATION"
        assert row.owner_scope_ref == org and row.organization_id == org
        assert row.asset_ref.startswith(f"parent/{run_id}/") and row.asset_version == 1
        assert row.source_refs == [run_id]
    derived = next(row for row in rows if row.derived_from_ref is not None)
    assert derived.asset_ref.endswith("/normalized.png")
    inputs = input_rows(e, run_id)
    assert [row["input_revision"] for row in inputs] == [1, 2]
    assert inputs[1]["derived_asset_ref"] == derived.asset_ref
    # the receipt carries the T-4a1 command scope: ORGANIZATION plus a digest, never the account
    receipt = next(r for r in receipt_rows(e, run_id) if r["operation"] == "ATTACH_ASSET")
    assert receipt["actor_scope_kind"] == "ORGANIZATION"
    assert receipt["actor_scope_ref"] not in {org, e.d.accounts["t1"], e.d.subjects["t1"]}
    # nothing but the Story and Core rows moved: no job, outbox, quota, usage or capacity row
    after = counts(e.d)
    moved = {name for name in after if after[name] != before[name]}
    assert moved <= {
        "story.runs",
        "story.run_inputs",
        "story.command_receipts",
        "story.understanding_revisions",
    }, moved
    assert_no_child_name(e, all_story_text(e, run_id) + response.text)
    for key in ("bucket", "object_key", "presigned", "amazonaws", "parent/"):
        assert key not in response.text


def test_the_idea_by_text_and_by_voice_runs_the_asr_job_side(env: Env) -> None:
    e = env
    run_id = to_subject_review(e)
    typed = idea(e, "t1", run_id, text="Con rồng nhỏ")
    assert typed.status_code == 202, typed.text
    assert typed.json()["idea_source"] == "TEXT" and typed.json()["transcript"] is None
    audio = wav_bytes(2000, seed=3)
    e.transcriber.register(sha(audio), SPEECH)
    voice_handle = complete_upload(
        e, "t1", run_id, audio, purpose="RUN_AUDIO", media_type="audio/wav"
    )
    voice = idea(e, "t1", run_id, audio_ref=voice_handle)
    assert voice.status_code == 202, voice.text
    body = voice.json()
    assert body["idea_source"] == "TEXT_AND_VOICE"
    assert body["transcript"] == {"transcript_revision": 1, "state": "PENDING"}
    # the ASR task ran after the response, job-side
    (row,) = [r for r in transcript_rows(e, run_id) if r["state"] != "SUPERSEDED"]
    assert (row["origin"], row["state"], row["raw_transcript"]) == (
        "ASR",
        "NEEDS_CONFIRMATION",
        SPEECH,
    )
    assert len(e.transcriber.calls) == 1
    voice_row = input_rows(e, run_id)[-1]
    assert voice_row["voice_asset_ref"].startswith(f"parent/{run_id}/")
    # the voice upload and its asset rows are organization scoped like the drawing's
    for asset in asset_rows(e, run_id):
        assert (
            asset.owner_scope_kind == "ORGANIZATION" and asset.owner_scope_ref == e.d.organization
        )
        assert asset.organization_id == e.d.organization

    # the Teacher reads the transcript: no-store, the exact text and hash
    read = read_transcript(e, "t1", run_id)
    assert read.status_code == 200 and read.headers["Cache-Control"] == "private, no-store"
    assert read.json()["text"] == SPEECH and read.json()["transcript_sha256"] == text_sha(SPEECH)
    # a correction is a new revision; the stale confirmation is 409 with the current version
    corrected = "Con rồng nhỏ chia kẹo"
    fixed = idea(e, "t1", run_id, transcript_correction={"base_revision": 1, "text": corrected})
    assert fixed.status_code == 202 and fixed.json()["transcript"]["transcript_revision"] == 2
    stale = confirm_transcript(e, "t1", run_id, 1, text_sha(SPEECH))
    assert stale.status_code == 409 and stale.json()["code"] == "STALE_REVISION"
    assert stale.json()["current_version"] == 2
    wrong_hash = confirm_transcript(e, "t1", run_id, 2, "0" * 64)
    assert wrong_hash.status_code == 409
    confirmed = confirm_transcript(e, "t1", run_id, 2, text_sha(corrected), key="tr-key-1")
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["state"] == "CONFIRMED"
    assert confirmed.headers["Cache-Control"] == "private, no-store"
    again = confirm_transcript(e, "t1", run_id, 2, text_sha(corrected), key="tr-key-1")
    assert (
        again.status_code == 200
        and wire(again)[1]["run_revision"] == wire(confirmed)[1]["run_revision"]
    )
    other = confirm_transcript(e, "t1", run_id, 2, "1" * 64, key="tr-key-1")
    assert other.status_code == 400 and other.json()["code"] == "INVALID_IDEMPOTENCY_KEY"
    assert_no_child_name(e, all_story_text(e, run_id))


def test_context_and_subject_then_the_edit_reruns_the_vlm_for_a_teacher(env: Env) -> None:
    e = env
    run_id = new_run(e)
    handle, data = drawing_handle(e, "t1", run_id)
    register_analysis(e, data)
    register_analysis(e, data, subject="little green dragon", hint="little green dragon")
    assert attach(e, "t1", run_id, handle).status_code == 202
    assert states(e, run_id) == ("SUBJECT_REVIEW", "SUCCEEDED")
    assert confirm_context(e, "t1", run_id).status_code == 200
    # T-4b3a D7e (T4A1-I-05): the edited subject now reruns the VLM for a Teacher
    edited = confirm_subject(e, "t1", run_id, subject="little green dragon")
    assert edited.status_code == 202, edited.text
    assert edited.json()["decision"] == "RERUN_REQUESTED"
    assert edited.json()["understanding_revision"] == 1
    # the rerun ran job-side with the adult's subject as data; revision 2 waits for the adult
    assert [c.subject_hint for c in e.analyzer.calls] == [None, "little green dragon"]
    assert states(e, run_id) == ("SUBJECT_REVIEW", "SUCCEEDED")
    assert [r["revision_no"] for r in understanding_rows(e, run_id)] == [1, 2]
    assert decision_rows(e, run_id) == []  # no decision until the Teacher confirms revision 2
    done = confirm_subject(e, "t1", run_id, subject="little green dragon", revision=2)
    assert done.status_code == 202 and done.json()["decision"] == "CONFIRMED"
    (decision,) = decision_rows(e, run_id)
    assert decision["actor_scope_kind"] == "ORGANIZATION" and decision["stage"] == "SUBJECT"
    assert decision["target_understanding_revision"] == 2
    # the context was confirmed first, so this subject confirmation is the last gate: the first
    # story started by itself (V4-A OPEN-A D1) and the composed generator answered
    assert states(e, run_id) == ("SCRIPT_REVIEW", "SUCCEEDED")
    assert [r["revision_no"] for r in story_rows(e, run_id)] == [1]
    assert e.generator.inputs[0]["understanding_revision"] == 2


def test_the_first_story_starts_by_itself_and_three_rewrites_then_the_limit(env: Env) -> None:
    e = env
    run_id = to_script_review(e)
    for number in (2, 3, 4):
        response = rewrite(e, "t1", run_id, revision=number - 1)
        assert response.status_code == 202, response.text
        body = response.json()
        assert body["story_revision_no"] == number and body["run_state"] == "SCRIPT_GENERATING"
        assert response.headers["Content-Location"] == f"/v1/story-runs/{run_id}"
        # the generator ran after the response, job-side: the new draft waits for the Teacher
        assert states(e, run_id) == ("SCRIPT_REVIEW", "SUCCEEDED")
        assert story_rows(e, run_id)[-1]["status"] == "DRAFT"
    assert [r["revision_no"] for r in story_rows(e, run_id)] == [1, 2, 3, 4]
    assert len(e.generator.inputs) == 4  # the first story and the three rewrites
    refused = rewrite(e, "t1", run_id, revision=4)
    assert refused.status_code == 409 and refused.json()["code"] == "STORY_REWRITE_LIMIT_REACHED"
    assert len(e.generator.inputs) == 4
    # the worker input of a Teacher run: role, bounded direction, no child name
    first = e.generator.inputs[0]
    assert first["schema_version"] == "sketch2life.story-generation-input.v3"
    assert first["context_entries"] == []  # a Teacher run never holds Parent entries
    assert first["role"] == "TEACHER" and first["activity"] is None
    direction = first["lesson_direction"]
    assert set(direction) == {"teacher_direction", "objectives", "activity_title"}
    assert direction["teacher_direction"] == "Câu chuyện về chú mèo đi tìm bạn"
    assert direction["activity_title"] == "Vẽ bằng ngón tay"
    assert direction["objectives"] == ["Nhận biết hình tròn", "Kể chuyện chú mèo"]
    assert first["confirmed_subject"] == SUBJECT and first["child_age_months"] == 60
    assert_no_child_name(e, str(e.generator.inputs) + all_story_text(e, run_id))
    # the rewrite input is the rewrite schema, the first story the generation schema
    assert e.generator.inputs[1]["schema_version"] == "sketch2life.story-rewrite-input.v2"
    assert e.generator.inputs[1]["context_entries"] == []
    # the receipts of the rewrites carry the organization command scope (the first story has none)
    rewrites = [r for r in receipt_rows(e, run_id) if r["operation"] == "GENERATE_STORY_REVISION"]
    assert len(rewrites) == 3
    assert {r["actor_scope_kind"] for r in rewrites} == {"ORGANIZATION"}


def test_a_replay_a_changed_body_and_a_stale_revision_on_a_rewrite(env: Env) -> None:
    e = env
    run_id = to_script_review(e)
    digest = story_rows(e, run_id)[0]["story_sha256"]
    first = rewrite(e, "t1", run_id, revision=1, key="rw-key-1", expected_story_sha256=digest)
    assert first.status_code == 202
    generated = len(e.generator.inputs)
    again = rewrite(e, "t1", run_id, revision=1, key="rw-key-1", expected_story_sha256=digest)
    assert again.status_code == 202 and wire(again)[1] == wire(first)[1]
    assert len(e.generator.inputs) == generated  # a replay never runs the generator twice
    assert len(story_rows(e, run_id)) == 2
    other = rewrite(e, "t1", run_id, revision=1, key="rw-key-1", hint="another hint")
    assert other.status_code == 400 and other.json()["code"] == "INVALID_IDEMPOTENCY_KEY"
    stale = rewrite(e, "t1", run_id, revision=1, key="rw-key-2")
    assert stale.status_code == 409 and stale.json()["code"] == "STALE_REVISION"
    assert stale.json()["current_version"] == 2
    bad_hash = rewrite(e, "t1", run_id, revision=2, key="rw-key-3", expected_story_sha256="a" * 64)
    assert bad_hash.status_code == 409 and bad_hash.json()["code"] == "STALE_REVISION"


def test_a_technically_failed_attempt_returns_its_slot(env: Env) -> None:
    e = env
    run_id = to_script_review(e)
    e.generator.error = StoryGenerationFailure("PROVIDER_DOWN")
    for _ in range(3):
        response = rewrite(e, "t1", run_id, revision=1)
        assert response.status_code == 202, response.text
        # a known failure of a rewrite goes back to the previous reviewable story
        assert states(e, run_id) == ("SCRIPT_REVIEW", "FAILED")
        assert [r["revision_no"] for r in story_rows(e, run_id)] == [1]
    # the fourth attempt of the same slot is the limit: three attempts per slot
    refused = rewrite(e, "t1", run_id, revision=1)
    assert refused.status_code == 409 and refused.json()["code"] == "STORY_REWRITE_LIMIT_REACHED"
    row = run_row(e, run_id)
    assert row["retryable"] is False
    with e.sessions()() as db:
        audits = db.execute(
            select(CoreAuditEntryModel.owner_scope_kind, CoreAuditEntryModel.organization_id).where(
                CoreAuditEntryModel.resource_id == run_id,
                CoreAuditEntryModel.action == AUDIT_REWRITE_ATTEMPT_FAILED,
            )
        ).all()
    assert audits and {tuple(a) for a in audits} == {("ORGANIZATION", e.d.organization)}
    # the generator is back to normal: a new slot is not needed, the run is still reviewable
    e.generator.error = None


# ======================================================================== the SUBJECT rule (D7c)
def test_the_subject_decision_of_the_run_counts_for_the_successor_after_a_move(env: Env) -> None:
    e = env
    run_id = to_script_review(e, "t1")
    # the occurrence is handed to t4 (SQL; the saga is T-6b): access follows the pin
    occurrence = run_row(e, run_id)["occurrence_ref"]
    with e.sessions().begin() as db:
        db.execute(
            update(OCCURRENCES)
            .where(OCCURRENCES.c.occurrence_id == occurrence)
            .values(responsible_teacher_ref=e.d.accounts["t4"])
        )
    creator = rewrite(e, "t1", run_id, revision=1)
    assert creator.status_code == 404 and creator.json()["code"] == "RESOURCE_NOT_FOUND"
    assert len(story_rows(e, run_id)) == 1
    # the successor never confirmed the subject, the predecessor did: the run is not stranded
    assert [d["actor_scope_kind"] for d in decision_rows(e, run_id)] == ["ORGANIZATION"]
    successor = rewrite(e, "t4", run_id, revision=1)
    assert successor.status_code == 202, successor.text
    assert len(story_rows(e, run_id)) == 2
    # the slot limit follows the run, not the person
    assert rewrite(e, "t4", run_id, revision=2).status_code == 202
    assert rewrite(e, "t4", run_id, revision=3).status_code == 202
    limit = rewrite(e, "t4", run_id, revision=4)
    assert limit.status_code == 409 and limit.json()["code"] == "STORY_REWRITE_LIMIT_REACHED"


def test_the_failed_attempts_of_a_slot_are_counted_across_teachers_of_the_run(env: Env) -> None:
    e = env
    run_id = to_script_review(e, "t1")
    e.generator.error = StoryGenerationFailure("PROVIDER_DOWN")
    assert rewrite(e, "t1", run_id, revision=1).status_code == 202  # attempt 1 of the slot
    occurrence = run_row(e, run_id)["occurrence_ref"]
    with e.sessions().begin() as db:
        db.execute(
            update(OCCURRENCES)
            .where(OCCURRENCES.c.occurrence_id == occurrence)
            .values(responsible_teacher_ref=e.d.accounts["t4"])
        )
    # the slot limit follows the run, not the person (D7d): the successor has two attempts left
    assert rewrite(e, "t4", run_id, revision=1).status_code == 202
    assert rewrite(e, "t4", run_id, revision=1).status_code == 202
    refused = rewrite(e, "t4", run_id, revision=1)
    assert refused.status_code == 409 and refused.json()["code"] == "STORY_REWRITE_LIMIT_REACHED"
    attempts = [r for r in receipt_rows(e, run_id) if r["operation"] == "GENERATE_STORY_REVISION"]
    assert len(attempts) == 3
    e.generator.error = None


def test_a_rewrite_without_the_subject_or_the_context_gate_is_422(env: Env) -> None:
    e = env
    run_id = to_subject_review(e)
    assert confirm_context(e, "t1", run_id).status_code == 200
    seed_first_story_unconfirmed(e, run_id)
    missing = rewrite(e, "t1", run_id, revision=1)
    assert missing.status_code == 422 and missing.json()["code"] == "SUBJECT_NOT_CONFIRMED"


def seed_first_story_unconfirmed(e: Env, run_id: str) -> None:
    """A story over a run whose subject was never confirmed (the gate is what is tested)."""
    with e.sessions().begin() as db:
        db.execute(
            update(RUNS).where(RUNS.c.run_id == run_id).values(run_state="PREPARATION_REVIEW")
        )
    seed_first_story(e, run_id)


# =================================================================== job-side (D6), late results
def test_a_late_result_after_the_assignment_was_revoked_lands_and_is_invisible(env: Env) -> None:
    e = env
    run_id = to_script_review(e, "t1")

    def revoke_the_assignment() -> None:
        with e.sessions().begin() as db:
            db.execute(
                update(OrganizationAssignmentModel)
                .where(OrganizationAssignmentModel.subject == e.d.subjects["t1"])
                .values(active=False)
            )

    e.generator.before = revoke_the_assignment
    response = rewrite(e, "t1", run_id, revision=1)
    assert response.status_code == 202, response.text
    # FR-T-14 (l.553): a valid AI job is not cancelled because an assignment changed; the result
    # lands on the run (state and revision checks pass) ...
    assert states(e, run_id) == ("SCRIPT_REVIEW", "SUCCEEDED")
    assert [r["revision_no"] for r in story_rows(e, run_id)] == [1, 2]
    # ... and the old Teacher can no longer see it
    read = e.d.client.get(f"/v1/story-runs/{run_id}", headers=who_headers(e, "t1"))
    assert read.status_code == 404
    assert read_transcript(e, "t1", run_id).status_code == 404


def test_a_job_side_call_with_another_organization_or_a_non_job_method_is_404(env: Env) -> None:
    from test_teacher_run_create_postgres import ISSUER

    from sketch2life.application.ports.identity import VerifiedPrincipal
    from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
    from sketch2life.application.ports.story_run_actor import RunActor, RunActorKind
    from sketch2life.infrastructure.persistence.parent_story_repository import (
        SqlParentStoryRunRepository,
    )

    e = env
    run_id = to_subject_review(e)
    principal = VerifiedPrincipal(e.d.subjects["t1"], ISSUER, frozenset())
    actor = RunActor(RunActorKind.TEACHER, e.d.accounts["t1"])
    right = e.d.organization
    for organization in (e.d.other_organization, None, ""):
        with e.sessions()() as db:
            repository = SqlParentStoryRunRepository(
                db, actor=actor, job_side=True, job_side_organization=organization
            )
            with pytest.raises(ParentStoryRunError) as caught:
                repository.read_current_input(principal=principal, run_id=run_id)
            assert (caught.value.status_code, caught.value.code) == (404, "RESOURCE_NOT_FOUND")
    with e.sessions()() as db:
        repository = SqlParentStoryRunRepository(
            db, actor=actor, job_side=True, job_side_organization=right
        )
        assert repository.read_current_input(principal=principal, run_id=run_id).input_revision == 2
        # a method that is not job-side is the uniform 404 even with the right organization
        for call in (
            lambda: repository.get_run(principal=principal, run_id=run_id),
            lambda: repository.get_transcript(principal=principal, run_id=run_id),
            lambda: repository.confirm_transcript(
                principal=principal,
                run_id=run_id,
                idempotency_key="k",
                expected_transcript_revision=1,
                transcript_sha256="a" * 64,
            ),
        ):
            with pytest.raises(ParentStoryRunError) as caught:
                call()
            assert caught.value.status_code == 404
    # a fixture run (no occurrence pin) is not a job-side target either
    fixture = fixture_run(e)
    with e.sessions()() as db:
        repository = SqlParentStoryRunRepository(
            db, actor=actor, job_side=True, job_side_organization=right
        )
        with pytest.raises(ParentStoryRunError) as caught:
            repository.read_current_input(principal=principal, run_id=fixture)
        assert caught.value.status_code == 404


def fixture_run(e: Env) -> str:
    """A T-4a1 style row: ``ORGANIZATION`` owner, no occurrence pin, the child-class rule."""
    import hashlib
    import json
    from datetime import UTC, datetime

    from test_teacher_run_create_postgres import add_child

    child = add_child(e.d)
    run_id, now = str(uuid4()), datetime.now(UTC)
    context = {
        "schema_version": "sketch2life.parent-context.v1",
        "profile_revision_ref": str(uuid4()),
        "age_months": 60,
        "interests_summary": "",
        "topic": "",
        "adult_confirmed_idea": "",
    }
    with e.sessions().begin() as db:
        db.execute(
            RUNS.insert().values(
                run_id=run_id,
                actor_scope_kind="ORGANIZATION",
                actor_scope_ref=e.d.organization,
                profile_ref=child,
                child_age_months=60,
                run_state="INPUT_PROCESSING",
                revision=1,
                version=1,
                retryable=False,
                current_input_revision=1,
                created_at=now,
                updated_at=now,
            )
        )
        db.execute(
            story_tables.run_inputs.insert().values(
                run_input_id=str(uuid4()),
                run_id=run_id,
                input_revision=1,
                source_profile_revision_ref=context["profile_revision_ref"],
                context_revision=1,
                context_snapshot=context,
                context_snapshot_sha256=hashlib.sha256(
                    json.dumps(context, sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest(),
                created_at=now,
            )
        )
    return run_id


# ============================================================================= read-only classes
@pytest.mark.parametrize("class_state", ["suspended", "archived"])
def test_a_read_only_class_refuses_writes_after_the_replay_and_allows_reads(
    env: Env, class_state: str
) -> None:
    e = env
    run_id = to_subject_review(e)
    # two uploads prepared while the class was active: a retake drawing and a voice idea
    spare, _ = drawing_handle(e, "t1", run_id, seed=5)
    audio = wav_bytes(1500, seed=9)
    e.transcriber.register(sha(audio), SPEECH)
    voice = complete_upload(e, "t1", run_id, audio, purpose="RUN_AUDIO", media_type="audio/wav")
    idea_revision = run_revision(e, run_id)
    first_idea = idea(e, "t1", run_id, revision=idea_revision, text="before", key="ro-idea")
    assert first_idea.status_code == 202
    assert confirm_context(e, "t1", run_id).status_code == 200
    assert confirm_subject(e, "t1", run_id).status_code == 202  # starts the first story
    first = rewrite(e, "t1", run_id, revision=1, key="ro-key")
    assert first.status_code == 202
    with e.sessions().begin() as db:
        db.execute(
            update(ClassroomModel)
            .where(ClassroomModel.class_id == e.d.classes["a1"])
            .values(state=class_state)
        )
    # the earlier success is still replayed (SRS l.1697) ...
    again = rewrite(e, "t1", run_id, revision=1, key="ro-key")
    assert again.status_code == 202
    replayed_idea = idea(e, "t1", run_id, revision=idea_revision, key="ro-idea", text="before")
    assert replayed_idea.status_code == 202 and wire(replayed_idea) == wire(first_idea)
    # ... a new write is 409 INVALID_STATE_TRANSITION, nothing written
    before = (run_revision(e, run_id), len(receipt_rows(e, run_id)), len(story_rows(e, run_id)))
    refused = rewrite(e, "t1", run_id, revision=2, key="ro-key-2")
    assert refused.status_code == 409 and refused.json()["code"] == "INVALID_STATE_TRANSITION"
    for response in (
        attach(e, "t1", run_id, spare),
        idea(e, "t1", run_id, text="late text"),
        idea(e, "t1", run_id, audio_ref=voice),
        confirm_transcript(e, "t1", run_id, 1, "a" * 64),
    ):
        assert response.status_code == 409, response.text
        assert response.json()["code"] == "INVALID_STATE_TRANSITION"
    assert before == (
        run_revision(e, run_id),
        len(receipt_rows(e, run_id)),
        len(story_rows(e, run_id)),
    )
    # reads stay allowed
    assert read_transcript(e, "t1", run_id).status_code == 200
    assert (
        e.d.client.get(f"/v1/story-runs/{run_id}", headers=who_headers(e, "t1")).status_code == 200
    )


@pytest.mark.parametrize("class_state", ["suspended", "archived"])
def test_a_read_only_class_opens_no_new_upload_session(env: Env, class_state: str) -> None:
    e = env
    run_id = new_run(e)
    assert (
        upload(
            e, "t1", run_id, png_for(7), purpose="RUN_ARTWORK", media_type="image/png"
        ).status_code
        == 201
    )
    with e.sessions().begin() as db:
        db.execute(
            update(ClassroomModel)
            .where(ClassroomModel.class_id == e.d.classes["a1"])
            .values(state=class_state)
        )
    for purpose, data, media_type in (
        ("RUN_ARTWORK", png_for(8), "image/png"),
        ("RUN_AUDIO", wav_bytes(1000, seed=1), "audio/wav"),
    ):
        blocked = upload(e, "t1", run_id, data, purpose=purpose, media_type=media_type)
        assert blocked.status_code == 409 and blocked.json()["code"] == "INVALID_STATE_TRANSITION"


def png_for(seed: int) -> bytes:
    from inputs_support import png_bytes

    return bytes(png_bytes(seed=seed))


# ================================================================ the uniform 404 and who may act
ACTORS = (
    "parent",
    "t2",  # a Teacher of another class
    "t4",  # a Teacher of the class who is not the responsible one
    "g1",  # a guide
    "o1",  # an observer
    "orgt",  # an org-wide Teacher row
    "tother",  # a Teacher of another organization
    "revoked",
    "inactive",
    "manager",
    "platform",
    "stranger",
)


def probes(e: Env, run_id: str, who: str) -> dict[str, Any]:
    """One request per input route, as ``who``."""

    def h(key: str | None = None) -> dict[str, str]:
        return dict(who_headers(e, who, key))

    base = f"/v1/story-runs/{run_id}"
    c = e.d.client
    return {
        "assets": c.post(
            f"{base}/assets",
            json={"asset_ref": "upl_" + str(uuid4())},
            headers=h(uuid4().hex),
        ),
        "idea": c.post(
            f"{base}/idea", json={"expected_run_revision": 1, "text": "x"}, headers=h(uuid4().hex)
        ),
        "transcript": c.get(f"{base}/transcript", headers=h()),
        "transcript_confirmation": c.post(
            f"{base}/transcript-confirmation",
            json={
                "expected_transcript_revision": 1,
                "transcript_sha256": "a" * 64,
                "confirmed": True,
            },
            headers=h(uuid4().hex),
        ),
        "story_rewrites": c.post(
            f"{base}/story-rewrites", json={"expected_story_revision": 1}, headers=h(uuid4().hex)
        ),
    }


def test_the_ten_actor_matrix_is_one_uniform_404_with_no_write(env: Env) -> None:
    e = env
    run_id = to_script_review(e)
    unknown = probes(e, str(uuid4()), "t1")
    reference = {name: wire(response) for name, response in unknown.items()}
    for status, body in reference.values():
        assert status == 404 and body["code"] == "RESOURCE_NOT_FOUND"
    snapshot = (
        dict(run_row(e, run_id)),
        len(receipt_rows(e, run_id)),
        len(input_rows(e, run_id)),
        len(story_rows(e, run_id)),
        counts_of(e),
    )
    for who in ACTORS:
        result = probes(e, run_id, who)
        for name, response in result.items():
            assert wire(response) == reference[name], (who, name)
            assert mask(response.text) == mask(unknown[name].text), (who, name)
    assert snapshot == (
        dict(run_row(e, run_id)),
        len(receipt_rows(e, run_id)),
        len(input_rows(e, run_id)),
        len(story_rows(e, run_id)),
        counts_of(e),
    )


def counts_of(e: Env) -> dict[str, int]:
    from test_teacher_run_create_postgres import counts

    return dict(counts(e.d))


def test_the_creating_teacher_after_a_move_and_a_revoked_one_get_the_same_404(env: Env) -> None:
    e = env
    run_id = to_script_review(e)
    occurrence = run_row(e, run_id)["occurrence_ref"]
    with e.sessions().begin() as db:
        db.execute(
            update(OCCURRENCES)
            .where(OCCURRENCES.c.occurrence_id == occurrence)
            .values(responsible_teacher_ref=e.d.accounts["t4"])
        )
    unknown = {n: wire(r) for n, r in probes(e, str(uuid4()), "t1").items()}
    for name, response in probes(e, run_id, "t1").items():
        assert wire(response) == unknown[name], name
    # the new responsible Teacher reaches every route (a 404 here would mean a guard bug)
    for name, response in probes(e, run_id, "t4").items():
        assert response.status_code != 404 or name == "assets", name


def test_a_fixture_run_without_an_occurrence_pin_stays_the_uniform_404_on_every_step(
    env: Env,
) -> None:
    e = env
    run_id = fixture_run(e)
    unknown = {n: wire(r) for n, r in probes(e, str(uuid4()), "t1").items()}
    for name, response in probes(e, run_id, "t1").items():
        assert wire(response) == unknown[name], name
    # and the run read of T-4a1 still works for it (the child-class rule)
    read = e.d.client.get(f"/v1/story-runs/{run_id}", headers=who_headers(e, "t1"))
    assert read.status_code == 200
    created = upload(e, "t1", run_id, png_for(11), purpose="RUN_ARTWORK", media_type="image/png")
    assert created.status_code == 404
    audio = upload(
        e, "t1", run_id, wav_bytes(1000, seed=4), purpose="RUN_AUDIO", media_type="audio/wav"
    )
    assert audio.status_code == 404


def test_the_key_is_required_after_the_role_check_and_bad_bodies_are_400(env: Env) -> None:
    e = env
    run_id = to_script_review(e)
    base = f"/v1/story-runs/{run_id}"
    c = e.d.client
    no_key = c.post(
        f"{base}/story-rewrites", json={"expected_story_revision": 1}, headers=who_headers(e, "t1")
    )
    assert no_key.status_code == 400
    bad_key = c.post(
        f"{base}/story-rewrites",
        json={"expected_story_revision": 1},
        headers=who_headers(e, "t1", "bad key"),
    )
    assert bad_key.status_code == 400
    # the role check comes first: a caller that is neither Parent nor Teacher gets the 404 of
    # everyone else, whatever the key (a Teacher of another class passes the role guard and is
    # stopped by the repository after the key has been parsed, as for every T-4a1 step)
    wrong = c.post(
        f"{base}/story-rewrites",
        json={"expected_story_revision": 1},
        headers=who_headers(e, "manager", "bad key"),
    )
    assert wrong.status_code == 404
    invalid = c.post(
        f"{base}/story-rewrites",
        json={"expected_story_revision": 0},
        headers=who_headers(e, "t1", uuid4().hex),
    )
    assert invalid.status_code == 400
    assert len(story_rows(e, run_id)) == 1 and len(e.generator.inputs) == 1  # the first story only


# ====================================================================== uploads and the policy
def test_a_parent_and_other_teachers_cannot_open_an_upload_for_a_teacher_run(env: Env) -> None:
    e = env
    run_id = new_run(e)
    data = png_for(21)
    for who in ("parent", "t2", "t4", "tother", "g1", "manager", "revoked"):
        created = upload(e, who, run_id, data, purpose="RUN_ARTWORK", media_type="image/png")
        assert created.status_code == 404, who
    ok = upload(e, "t1", run_id, data, purpose="RUN_ARTWORK", media_type="image/png")
    assert ok.status_code == 201
    # the responsible Teacher's session is not usable by another Teacher (owner principal binding)
    upload_id = ok.json()["upload_id"]
    other = e.d.client.put(
        f"/v1/upload-sessions/{upload_id}/parts/1",
        content=data,
        headers={
            **who_headers(e, "t4"),
            "X-Part-SHA256": sha(data),
            "Content-Type": "application/octet-stream",
        },
    )
    assert other.status_code == 404
    # no Parent upload target is open to a Teacher
    assert (
        upload(
            e, "t1", str(uuid4()), data, purpose="RUN_ARTWORK", media_type="image/png"
        ).status_code
        == 404
    )


def test_a_wrong_type_handle_is_415_and_an_unknown_handle_is_404(env: Env) -> None:
    e = env
    run_id = new_run(e)
    audio = wav_bytes(1000, seed=2)
    voice = complete_upload(e, "t1", run_id, audio, purpose="RUN_AUDIO", media_type="audio/wav")
    # a RUN_AUDIO session offered to the drawing route answers 415, like for a Parent
    wrong_type = attach(e, "t1", run_id, voice)
    assert wrong_type.status_code == 415
    unknown = attach(e, "t1", run_id, "upl_" + str(uuid4()))
    assert unknown.status_code == 404


# ========================================================================== purge closure (P2-2)
def test_the_purge_closure_covers_every_row_a_teacher_run_wrote(env: Env) -> None:
    from sketch2life.application.ports.core_foundation import LifecycleScope
    from sketch2life.infrastructure.persistence.core_lifecycle_store import (
        SqlCoreRunAssetPurge,
        SqlCoreRunUploadClose,
        build_plan,
    )

    e = env
    run_id = new_run(e)
    handle, data = drawing_handle(e, "t1", run_id)
    register_analysis(e, data)
    assert attach(e, "t1", run_id, handle).status_code == 202
    audio = wav_bytes(1500, seed=6)
    e.transcriber.register(sha(audio), SPEECH)
    voice = complete_upload(e, "t1", run_id, audio, purpose="RUN_AUDIO", media_type="audio/wav")
    assert idea(e, "t1", run_id, audio_ref=voice).status_code == 202
    # one more session of each purpose stays OPEN (nothing uploaded)
    assert (
        upload(
            e, "t1", run_id, png_for(31), purpose="RUN_ARTWORK", media_type="image/png"
        ).status_code
        == 201
    )
    assert (
        upload(
            e, "t1", run_id, wav_bytes(1000, seed=8), purpose="RUN_AUDIO", media_type="audio/wav"
        ).status_code
        == 201
    )
    scope = LifecycleScope("ORGANIZATION", e.d.organization)
    purge = SqlCoreRunAssetPurge(e.sessions(), e.storage)
    candidates = purge.closure_candidates(scope, run_id)
    assert len(candidates.assets) == len(asset_rows(e, run_id)) == 3
    plan = build_plan(candidates, frozenset())
    # nothing is SCOPE_MISMATCH or KEY_UNKNOWN: every original, copy and voice is removable
    assert plan.retained == ()
    assert sorted(key.asset_ref for key in plan.removable) == sorted(
        row.asset_ref for row in asset_rows(e, run_id)
    )
    closer = SqlCoreRunUploadClose(e.sessions())
    planned = closer.plan_close_run_uploads(scope, run_id)
    assert len(planned) == 2  # exactly the two open sessions
    assert closer.close_run_uploads(scope, run_id) == 2
    assert closer.plan_close_run_uploads(scope, run_id) == ()
    purge.purge_objects(plan)
    assert purge.sweep_run_prefix(scope, run_id).swept_count == 0
    assert e.storage.list_keys(f"parent/{run_id}/") == ()
    purge.delete_rows(plan, frozenset())
    assert asset_rows(e, run_id) == []


def test_a_null_scope_ref_would_defeat_the_closure_and_the_asset_trigger(env: Env) -> None:
    """The mutation the plan review (P2-2) asked to be caught: a Teacher row stored with a NULL
    ref is refused by the asset trigger, and a session with a NULL ref is never closed."""
    from sqlalchemy.exc import DBAPIError

    from sketch2life.application.ports.core_foundation import LifecycleScope
    from sketch2life.infrastructure.lesson_library.tables import UPLOAD_SESSIONS
    from sketch2life.infrastructure.persistence.core_lifecycle_store import SqlCoreRunUploadClose
    from sketch2life.infrastructure.persistence.core_models import CoreAssetMetadataModel

    e = env
    run_id = new_run(e)
    assert (
        upload(
            e, "t1", run_id, png_for(41), purpose="RUN_ARTWORK", media_type="image/png"
        ).status_code
        == 201
    )
    scope = LifecycleScope("ORGANIZATION", e.d.organization)
    closer = SqlCoreRunUploadClose(e.sessions())
    assert len(closer.plan_close_run_uploads(scope, run_id)) == 1
    # mutate: the session as the occurrence precedent stores it (NULL ref): not matched
    with e.sessions().begin() as db:
        db.execute(
            update(UPLOAD_SESSIONS)
            .where(UPLOAD_SESSIONS.c.target_ref == run_id)
            .values(owner_scope_ref=None)
        )
    assert closer.plan_close_run_uploads(scope, run_id) == ()
    # the asset trigger refuses a NEW organization asset row with a NULL ref
    with pytest.raises(DBAPIError), e.sessions().begin() as db:
        db.execute(
            insert(CoreAssetMetadataModel.__table__).values(  # type: ignore[arg-type]
                asset_ref=f"parent/{run_id}/null-ref",
                asset_version=1,
                organization_id=e.d.organization,
                owner_scope_kind="ORGANIZATION",
                owner_scope_ref=None,
                content_sha256="a" * 64,
                media_type="image/png",
                source_refs=[run_id],
                derived_from_ref=None,
            )
        )


# ====================================================================== nothing else is written
def test_no_job_outbox_quota_billing_or_capacity_row_across_the_whole_flow(
    env: Env, caplog: pytest.LogCaptureFixture
) -> None:
    e = env
    caplog.set_level(logging.DEBUG)
    names = counts_of(e)
    run_id = new_run(e)
    handle, data = drawing_handle(e, "t1", run_id)
    register_analysis(e, data)
    assert attach(e, "t1", run_id, handle).status_code == 202
    assert idea(e, "t1", run_id, text="Con rồng nhỏ").status_code == 202
    audio = wav_bytes(1500, seed=14)
    e.transcriber.register(sha(audio), SPEECH)
    voice = complete_upload(e, "t1", run_id, audio, purpose="RUN_AUDIO", media_type="audio/wav")
    assert idea(e, "t1", run_id, audio_ref=voice).status_code == 202
    assert read_transcript(e, "t1", run_id).status_code == 200
    assert confirm_transcript(e, "t1", run_id, 1, text_sha(SPEECH)).status_code == 200
    assert confirm_context(e, "t1", run_id).status_code == 200
    assert confirm_subject(e, "t1", run_id).status_code == 202  # starts the first story
    assert rewrite(e, "t1", run_id, revision=1, hint="HINT-SENTENCE shorter").status_code == 202
    # nothing the Teacher or the child said reaches a log record (l.942, BR-34)
    logged = " ".join(record.getMessage() for record in caplog.records)
    for secret in (SPEECH, "HINT-SENTENCE", "Con rồng nhỏ", NAME_PREFIX, *e.d.children.values()):
        assert secret not in logged
    after = counts_of(e)
    moved = {name for name in after if after[name] != names[name]}
    forbidden = {
        name
        for name in moved
        if name.startswith(("ai_jobs.", "billing.", "ai_policy."))
        or "outbox" in name
        or "quota" in name
        or "usage" in name
        or "capacity" in name
    }
    assert forbidden == set(), forbidden
    with e.sessions()() as db:
        tables = db.execute(
            text(
                "select table_schema || '.' || table_name from information_schema.tables "
                "where table_schema in ('billing', 'ai_policy')"
            )
        ).scalars()
        for table in list(tables):
            assert db.execute(text(f"select count(*) from {table}")).scalar_one() == 0  # noqa: S608
    assert_no_child_name(e, all_story_text(e, run_id))


# ========================================================================== concurrency (race)
def test_concurrent_rewrites_with_one_key_make_one_reservation_and_the_rest_replay(
    env: Env,
) -> None:
    e = env
    for round_number in range(30):
        run_id = to_script_review(e) if round_number == 0 else fresh_script_review(e)
        key = f"race-key-{round_number}"
        barrier = Barrier(6)

        def call(
            _index: int, run_id: str = run_id, key: str = key, barrier: Barrier = barrier
        ) -> Any:
            barrier.wait(timeout=30)
            return rewrite(e, "t1", run_id, revision=1, key=key)

        with ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(call, range(6)))
        statuses = sorted(r.status_code for r in results)
        assert statuses == [202] * 6, (round_number, statuses, [r.text for r in results])
        assert len({wire(r)[1]["story_revision_no"] for r in results}) == 1
        assert [r["revision_no"] for r in story_rows(e, run_id)] == [1, 2]
        assert (
            len([x for x in receipt_rows(e, run_id) if x["operation"] == "GENERATE_STORY_REVISION"])
            == 1
        )


def test_concurrent_rewrites_with_different_keys_make_one_winner(env: Env) -> None:
    e = env
    for round_number in range(30):
        run_id = fresh_script_review(e)
        barrier = Barrier(6)

        def call(_index: int, run_id: str = run_id, barrier: Barrier = barrier) -> Any:
            barrier.wait(timeout=30)
            return rewrite(e, "t1", run_id, revision=1, key=uuid4().hex)

        with ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(call, range(6)))
        won = [r for r in results if r.status_code == 202]
        # the run state is the fence: one request reserves; the others see a run that moved on
        assert len(won) == 1, (round_number, [r.status_code for r in results])
        assert all(r.status_code in {202, 409} for r in results), [r.text for r in results]
        assert [r["revision_no"] for r in story_rows(e, run_id)] == [1, 2]
        reservations = [
            x for x in receipt_rows(e, run_id) if x["operation"] == "GENERATE_STORY_REVISION"
        ]
        assert len(reservations) == 1


def fresh_script_review(e: Env) -> str:
    """A new Teacher run at ``SCRIPT_REVIEW``: a new occurrence, child and run on class a1.

    Teacher t1 may hold one active run at a time; the previous run is cancelled first."""
    for run_id in list(e.runs):
        row = run_row(e, run_id)
        if row["run_state"] not in {"COMPLETED", "FAILED", "ABANDONED", "DELETED"}:
            with e.sessions().begin() as db:
                db.execute(
                    update(RUNS).where(RUNS.c.run_id == run_id).values(run_state="ABANDONED")
                )
        e.runs.pop(run_id)
    return str(to_script_review(e))


# ============================================== the receipt finalizer of the video family (F7)
@pytest.mark.parametrize("kind", ["ORGANIZATION", "PARENT_ACCOUNT"])
def test_finalize_receipt_finds_the_pending_receipt_of_either_kind_and_no_other_run(
    env: Env, kind: str
) -> None:
    """``_finalize_receipt`` of the video repository (T-4b2 hand-over F7), exercised on rows: a
    PENDING receipt whose scope is the COMMAND scope (a digest, not the organization id) is
    finalized, a PENDING receipt of another run with the same key is not. The Teacher admission
    that creates such a receipt is T-4b3b."""
    from datetime import UTC, datetime

    from sketch2life.infrastructure.story_video.repository import OPERATION, SqlStoryVideoRepository

    e = env
    run_id = new_run(e)
    other_run = fixture_run(e)  # another run of the same organization
    key_hash = "k" * 64
    table = story_tables.story_command_receipts
    now = datetime.now(UTC)

    def pending(run: str, ref: str) -> str:
        receipt_id = str(uuid4())
        with e.sessions().begin() as db:
            db.execute(
                insert(table).values(
                    receipt_id=receipt_id,
                    actor_scope_kind=kind,
                    actor_scope_ref=ref,
                    operation=OPERATION,
                    idempotency_scope_kind="STORY_RUN",
                    idempotency_scope_ref=run,
                    idempotency_key_sha256=key_hash,
                    request_fingerprint_sha256="f" * 64,
                    state="PENDING",
                    response_status=None,
                    response_resource_version=None,
                    response_body=null(),  # SQL NULL: the receipt shape check wants IS NULL
                    resource_ref=run,
                    resource_version=2,
                    state_version=1,
                    created_at=now,
                    finalized_at=None,
                )
            )
        return receipt_id

    target = pending(run_id, "d" * 64)  # a principal digest, never the organization id
    other = pending(other_run, "e" * 64)
    row = dict(run_row(e, run_id))
    row["actor_scope_kind"] = kind
    with e.sessions().begin() as db:
        SqlStoryVideoRepository(db)._finalize_receipt(
            row,  # type: ignore[arg-type]
            {"request_idempotency_key_hash": key_hash},  # type: ignore[arg-type]
            status=202,
            body={"ok": True},
            now=now,
        )
    with e.sessions()() as db:
        states_after = dict(
            db.execute(
                select(table.c.receipt_id, table.c.state).where(
                    table.c.receipt_id.in_([target, other])
                )
            ).all()
        )
    assert states_after == {target: "FINAL", other: "PENDING"}
