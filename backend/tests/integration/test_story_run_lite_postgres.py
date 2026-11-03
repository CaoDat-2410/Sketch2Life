from __future__ import annotations

import hashlib
import os
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta, tzinfo
from typing import Self, cast
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Table, create_engine, event, insert, select, text, update
from sqlalchemy.exc import IntegrityError

from sketch2life.application.ports.story_run_lite import (
    AdmittedAssetPair,
    AssetBinding,
    CoreAssetAdmissionPort,
    ImageNormalizerPort,
    ImageSafetyScannerPort,
    NormalizedImage,
    ScanVerdict,
    StoryRunLiteVisionPort,
    StoryRunReferencePort,
    ValidatedVisionResult,
    VisionAttemptResult,
)
from sketch2life.application.services.story_run_lite import StoryRunLiteService
from sketch2life.domain.story_run_lite import (
    OwnerScopeKind,
    StoryRunLiteError,
    UploadState,
    canonical_fingerprint,
    validate_idempotency_key,
)
from sketch2life.infrastructure.persistence.core_models import CoreAssetMetadataModel
from sketch2life.infrastructure.story_run_lite import repository as repository_module
from sketch2life.infrastructure.story_run_lite import tables
from sketch2life.infrastructure.story_run_lite.composition import (
    goal_database_url,
    verify_goal_database_owner,
)
from sketch2life.infrastructure.story_run_lite.quarantine import QuarantineStore
from sketch2life.infrastructure.story_run_lite.repository import SqlStoryRunLiteRepository
from sketch2life.interfaces.http.story_run_lite_app import create_app

_PARENT = OwnerScopeKind.PARENT_ACCOUNT


@pytest.fixture
def story_db(tmp_path):
    value = os.environ.get("STORYRUN_LITE_DATABASE_URL")
    if not value:
        pytest.skip("requires the verified goal-owned storyrun_lite_* loopback database")
    safe_url, database_name = goal_database_url(value)
    engine = create_engine(safe_url, pool_pre_ping=True, hide_parameters=True)
    assert verify_goal_database_owner(engine, database_name)
    repository = SqlStoryRunLiteRepository(
        engine=engine,
        quarantine=QuarantineStore(tmp_path / "quarantine"),
    )
    repository.acquire_singleton_lock()
    repository.recover_after_restart()
    try:
        yield engine, repository
    finally:
        repository.release_singleton_lock()
        engine.dispose()


def test_goal_database_owner_accepts_loopback_inet_prefix(story_db) -> None:
    engine, _repository = story_db
    value = os.environ["STORYRUN_LITE_DATABASE_URL"]
    _safe_url, database_name = goal_database_url(value)
    with engine.connect() as connection:
        current_user, database_owner = connection.execute(
            text(
                "SELECT current_user, pg_get_userbyid(datdba) "
                "FROM pg_database WHERE datname = current_database()"
            )
        ).one()
    assert verify_goal_database_owner(engine, database_name) == current_user == database_owner


def _hash(seed: str) -> str:
    return hashlib.sha256(seed.encode()).hexdigest()


def _is_story_run_lock(statement: str) -> bool:
    sql = statement.lower()
    return "from story.runs" in sql and "for update" in sql


def _create_run(repository: SqlStoryRunLiteRepository, owner: str) -> str:
    result = repository.create_run(
        actor_scope_kind=_PARENT,
        actor_scope_ref=owner,
        profile_ref="synthetic-parent-demo",
        key_sha256=_hash("create-run:" + owner),
        fingerprint_sha256=_hash("fingerprint-create-run:" + owner),
    )
    assert result.status_code == 201
    return str(result.body["run_ref"])


def _create_upload(
    repository: SqlStoryRunLiteRepository,
    *,
    owner: str,
    run_id: str,
    content: bytes,
    name: str,
) -> tuple[str, str]:
    digest = hashlib.sha256(content).hexdigest()
    created = repository.create_upload(
        actor_scope_kind=_PARENT,
        actor_scope_ref=owner,
        run_id=run_id,
        media_type="image/png",
        expected_size_bytes=len(content),
        expected_sha256=digest,
        key_sha256=_hash("create-upload:" + name),
        fingerprint_sha256=_hash("fingerprint-create-upload:" + name),
    )
    upload_id = str(created.body["upload_ref"])
    part = repository.put_part(
        actor_scope_kind=_PARENT,
        actor_scope_ref=owner,
        upload_id=upload_id,
        part_number=1,
        payload=content,
        declared_length=len(content),
        declared_sha256=digest,
    )
    assert part.status_code == 200
    return upload_id, digest


def _reserve_complete(
    repository: SqlStoryRunLiteRepository,
    *,
    owner: str,
    upload_id: str,
    digest: str,
    size: int,
    name: str,
    version: int = 1,
):
    return repository.reserve_complete_upload(
        actor_scope_kind=_PARENT,
        actor_scope_ref=owner,
        upload_id=upload_id,
        expected_size_bytes=size,
        expected_sha256=digest,
        expected_version=version,
        key_sha256=_hash("complete:" + name),
        fingerprint_sha256=_hash("fingerprint-complete:" + name),
    )


def _open_upload_for_admission(
    repository: SqlStoryRunLiteRepository,
    *,
    owner: str,
    upload_id: str,
    digest: str,
    size: int,
    name: str,
) -> int:
    reservation = _reserve_complete(
        repository,
        owner=owner,
        upload_id=upload_id,
        digest=digest,
        size=size,
        name=name,
    )
    assert reservation.command_result.status_code == 202
    assert reservation.claim_version is not None
    repository.finalize_complete_upload(reservation, key_sha256=_hash("complete:" + name))
    assert repository.open_upload_gate(upload_id=upload_id, claim_version=reservation.claim_version)
    return reservation.claim_version


def _normalized_upload(payload: bytes, digest: str) -> NormalizedImage:
    return NormalizedImage(
        "image/png",
        digest,
        len(payload),
        1,
        1,
        "image/jpeg",
        _hash("admission-derived:" + digest),
        1,
        b"x",
        1_073_741_824,
        25,
        120,
    )


def _asset_pair(run_id: str, owner: str, *, seed: str) -> AdmittedAssetPair:
    original_ref = str(uuid.uuid4())
    derived_ref = str(uuid.uuid4())
    sha = _hash(seed)
    original = AssetBinding(original_ref, 1, "image/png", sha, 256, _PARENT, owner)
    derived = AssetBinding(
        derived_ref, 1, "image/jpeg", _hash(seed + ":derived"), 192, _PARENT, owner
    )
    return AdmittedAssetPair(original, derived, str(uuid.uuid4()), run_id)


def _attach(
    repository: SqlStoryRunLiteRepository,
    *,
    owner: str,
    run_id: str,
    pair: AdmittedAssetPair,
    name: str,
):
    return repository.attach_asset(
        actor_scope_kind=_PARENT,
        actor_scope_ref=owner,
        run_id=run_id,
        pair=pair,
        expected_revision=1,
        expected_version=1,
        key_sha256=_hash("attach:" + name),
        fingerprint_sha256=_hash("fingerprint-attach:" + name),
    )


def test_legacy_owner_fence_receipts_recovery_confirm_and_cancel(story_db) -> None:
    engine, repository = story_db

    legacy_ref = os.environ.get("STORYRUN_LITE_LEGACY_ASSET_REF")
    assert legacy_ref, "migration setup must seed a pre-migration legacy Organization row"
    with engine.begin() as connection:
        legacy = (
            connection.execute(
                select(CoreAssetMetadataModel.__table__).where(
                    CoreAssetMetadataModel.asset_ref == legacy_ref
                )
            )
            .mappings()
            .one()
        )
        assert legacy["owner_scope_kind"] == "ORGANIZATION"
        assert legacy["owner_scope_ref"] is None
        connection.execute(
            update(cast(Table, CoreAssetMetadataModel.__table__))
            .where(CoreAssetMetadataModel.asset_ref == legacy_ref)
            .values(media_type="image/png")
        )

    invalid_owner_ref = str(uuid.uuid4())
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(
            insert(cast(Table, CoreAssetMetadataModel.__table__)).values(
                asset_ref=invalid_owner_ref,
                asset_version=1,
                organization_id="legacy-org",
                owner_scope_kind="ORGANIZATION",
                owner_scope_ref=None,
                content_sha256=_hash("invalid-owner"),
                media_type="image/png",
                source_refs=[],
                derived_from_ref=None,
                created_at=datetime.now(UTC),
            )
        )

    # Core complete crash after PENDING commit: recovery finalizes 409, keeps no asset, and
    # exact same-key replay returns that immutable receipt snapshot.
    owner = "parent-core-pending-" + str(uuid.uuid4())
    run_id = _create_run(repository, owner)
    raw = b"synthetic-core-pending"
    upload_id, digest = _create_upload(
        repository, owner=owner, run_id=run_id, content=raw, name="core-pending"
    )
    pending = _reserve_complete(
        repository,
        owner=owner,
        upload_id=upload_id,
        digest=digest,
        size=len(raw),
        name="core-pending",
    )
    assert pending.upload_id == upload_id
    repository.recover_after_restart()
    failed_upload = repository.get_upload(
        actor_scope_kind=_PARENT, actor_scope_ref=owner, upload_id=upload_id
    )
    assert failed_upload.body["state"] == "FAILED"
    replay = _reserve_complete(
        repository,
        owner=owner,
        upload_id=upload_id,
        digest=digest,
        size=len(raw),
        name="core-pending",
    )
    assert replay.command_result.status_code == 409
    assert replay.command_result.replayed is True
    normalized = NormalizedImage(
        "image/png",
        digest,
        len(raw),
        1,
        1,
        "image/jpeg",
        _hash("derived"),
        1,
        b"x",
        1_073_741_824,
        25,
        120,
    )
    assert not repository.finish_upload_admission(
        upload_id=upload_id,
        claim_version=int(pending.claim_version),
        original_asset_ref=str(uuid.uuid4()),
        derived_asset_ref=str(uuid.uuid4()),
        normalized=normalized,
        scanner=ScanVerdict("CLEAN", digest, "test-only", datetime.now(UTC)),
        actor_scope_ref=owner,
    )

    # Core crash after final 202 but before gate open: 202 remains exact while GET is FAILED.
    next_owner = "parent-core-final-owner-" + str(uuid.uuid4())
    run_two = _create_run(repository, next_owner)
    raw_two = b"synthetic-core-final"
    upload_two, digest_two = _create_upload(
        repository,
        owner=next_owner,
        run_id=run_two,
        content=raw_two,
        name="core-final",
    )
    pending_two = _reserve_complete(
        repository,
        owner=next_owner,
        upload_id=upload_two,
        digest=digest_two,
        size=len(raw_two),
        name="core-final",
    )
    accepted = repository.finalize_complete_upload(
        pending_two, key_sha256=_hash("complete:core-final")
    )
    assert accepted.status_code == 202
    repository.recover_after_restart()
    final_replay = _reserve_complete(
        repository,
        owner=next_owner,
        upload_id=upload_two,
        digest=digest_two,
        size=len(raw_two),
        name="core-final",
    )
    assert final_replay.command_result.status_code == 202
    assert final_replay.command_result.body == accepted.body
    assert (
        repository.get_upload(
            actor_scope_kind=_PARENT, actor_scope_ref=next_owner, upload_id=upload_two
        ).body["state"]
        == "FAILED"
    )
    assert not repository.open_upload_gate(
        upload_id=upload_two, claim_version=int(pending_two.claim_version)
    )

    # Story attach crash before and after receipt finalization. Neither window redispatches.
    owner_story_pending = "parent-story-pending-" + str(uuid.uuid4())
    run_story_pending = _create_run(repository, owner_story_pending)
    pair_pending = _asset_pair(run_story_pending, owner_story_pending, seed="story-pending")
    pending_attach, _job, claim = _attach(
        repository,
        owner=owner_story_pending,
        run_id=run_story_pending,
        pair=pair_pending,
        name="story-pending",
    )
    assert pending_attach.status_code == 202 and claim is not None
    repository.recover_after_restart()
    story_hold = repository.get_run(
        actor_scope_kind=_PARENT,
        actor_scope_ref=owner_story_pending,
        run_id=run_story_pending,
    )
    assert story_hold.body["job_state"] == "AWAITING_RECONCILIATION"
    duplicate_pending, no_job, no_claim = repository.attach_asset(
        actor_scope_kind=_PARENT,
        actor_scope_ref=owner_story_pending,
        run_id=run_story_pending,
        pair=pair_pending,
        expected_revision=1,
        expected_version=1,
        key_sha256=_hash("attach:story-pending"),
        fingerprint_sha256=_hash("fingerprint-attach:story-pending"),
    )
    assert duplicate_pending.status_code == 409
    assert duplicate_pending.replayed is True
    assert no_job is None and no_claim is None

    owner_story_final = "parent-story-final-" + str(uuid.uuid4())
    run_story_final = _create_run(repository, owner_story_final)
    pair_final = _asset_pair(run_story_final, owner_story_final, seed="story-final")
    reservation_final, _job_final, claim_final = _attach(
        repository,
        owner=owner_story_final,
        run_id=run_story_final,
        pair=pair_final,
        name="story-final",
    )
    assert claim_final is not None
    attach_accepted = repository.finalize_attach_command(
        run_id=run_story_final,
        key_sha256=_hash("attach:story-final"),
        claimed_version=claim_final,
    )
    assert attach_accepted.status_code == 202
    repository.recover_after_restart()
    attach_replay, no_job, no_claim = repository.attach_asset(
        actor_scope_kind=_PARENT,
        actor_scope_ref=owner_story_final,
        run_id=run_story_final,
        pair=pair_final,
        expected_revision=1,
        expected_version=1,
        key_sha256=_hash("attach:story-final"),
        fingerprint_sha256=_hash("fingerprint-attach:story-final"),
    )
    assert attach_replay.status_code == 202
    assert attach_replay.body == attach_accepted.body
    assert no_job is None and no_claim is None
    assert not repository.open_story_dispatch_gate(
        run_id=run_story_final, claimed_version=int(claim_final)
    )

    # Full confirmation UoW: one CONFIRM decision, exact replay, stale revision 409.
    owner_confirm = "parent-confirm-" + str(uuid.uuid4())
    run_confirm = _create_run(repository, owner_confirm)
    pair_confirm = _asset_pair(run_confirm, owner_confirm, seed="story-confirm")
    _reservation, _job, claim_confirm = _attach(
        repository,
        owner=owner_confirm,
        run_id=run_confirm,
        pair=pair_confirm,
        name="story-confirm",
    )
    assert claim_confirm is not None
    repository.finalize_attach_command(
        run_id=run_confirm,
        key_sha256=_hash("attach:story-confirm"),
        claimed_version=claim_confirm,
    )
    assert repository.open_story_dispatch_gate(run_id=run_confirm, claimed_version=claim_confirm)
    assert repository.commit_vision_success(
        run_id=run_confirm,
        claimed_version=claim_confirm,
        result_snapshot={"contract_name": "FakeStoryRunLiteResultV1", "is_fake": True},
        subject_label="Synthetic subject",
        confidence=0.75,
        canonical_result_sha256=_hash("canonical-result"),
        raw_body_sha256=None,
    )
    current = repository.get_run(
        actor_scope_kind=_PARENT, actor_scope_ref=owner_confirm, run_id=run_confirm
    )
    assert current.body["run_state"] == "SUBJECT_REVIEW"
    assert current.body["target_revision"] == 1
    confirmed = repository.confirm_subject(
        actor_scope_kind=_PARENT,
        actor_scope_ref=owner_confirm,
        run_id=run_confirm,
        expected_version=int(current.body["version"]),
        expected_understanding_revision=1,
        key_sha256=_hash("confirm"),
        fingerprint_sha256=_hash("fingerprint-confirm"),
    )
    assert confirmed.status_code == 202
    assert confirmed.body["run_state"] == "PREPARATION_REVIEW"
    replay_confirm = repository.confirm_subject(
        actor_scope_kind=_PARENT,
        actor_scope_ref=owner_confirm,
        run_id=run_confirm,
        expected_version=int(current.body["version"]),
        expected_understanding_revision=1,
        key_sha256=_hash("confirm"),
        fingerprint_sha256=_hash("fingerprint-confirm"),
    )
    assert replay_confirm.replayed is True
    assert replay_confirm.body == confirmed.body
    with engine.connect() as connection:
        decision_count = connection.execute(
            text("SELECT count(*) FROM story.review_decisions WHERE run_id = :run_id"),
            {"run_id": run_confirm},
        ).scalar_one()
    assert decision_count == 1
    stale = repository.confirm_subject(
        actor_scope_kind=_PARENT,
        actor_scope_ref=owner_confirm,
        run_id=run_confirm,
        expected_version=int(confirmed.body["version"]),
        expected_understanding_revision=2,
        key_sha256=_hash("confirm-stale"),
        fingerprint_sha256=_hash("fingerprint-confirm-stale"),
    )
    assert stale.status_code == 409
    assert stale.body["code"] == "STALE_REVISION"

    # Cancellation wins its CAS and a late result cannot advance the run head.
    owner_cancel = "parent-cancel-" + str(uuid.uuid4())
    run_cancel = _create_run(repository, owner_cancel)
    pair_cancel = _asset_pair(run_cancel, owner_cancel, seed="story-cancel")
    _reservation_cancel, _job_cancel, claim_cancel = _attach(
        repository,
        owner=owner_cancel,
        run_id=run_cancel,
        pair=pair_cancel,
        name="story-cancel",
    )
    assert claim_cancel is not None
    repository.finalize_attach_command(
        run_id=run_cancel,
        key_sha256=_hash("attach:story-cancel"),
        claimed_version=claim_cancel,
    )
    assert repository.open_story_dispatch_gate(run_id=run_cancel, claimed_version=claim_cancel)
    before_cancel = repository.get_run(
        actor_scope_kind=_PARENT, actor_scope_ref=owner_cancel, run_id=run_cancel
    )
    cancelled = repository.cancel_run(
        actor_scope_kind=_PARENT,
        actor_scope_ref=owner_cancel,
        run_id=run_cancel,
        expected_revision=int(before_cancel.body["revision"]),
        expected_version=int(before_cancel.body["version"]),
        key_sha256=_hash("cancel"),
        fingerprint_sha256=_hash("fingerprint-cancel"),
    )
    assert cancelled.status_code == 202
    assert cancelled.body["run_state"] == "DELETE_PENDING"
    assert not repository.commit_vision_success(
        run_id=run_cancel,
        claimed_version=claim_cancel,
        result_snapshot={"contract_name": "FakeStoryRunLiteResultV1"},
        subject_label="Late synthetic result",
        confidence=0.5,
        canonical_result_sha256=_hash("late-canonical-result"),
        raw_body_sha256=None,
    )


def test_pre_migration_fixture_row_is_only_read_or_non_scope_updated(story_db) -> None:
    engine, _repository = story_db
    legacy_ref = os.environ.get("STORYRUN_LITE_LEGACY_ASSET_REF")
    assert legacy_ref
    with engine.connect() as connection:
        row = connection.execute(
            select(
                CoreAssetMetadataModel.owner_scope_kind,
                CoreAssetMetadataModel.owner_scope_ref,
                CoreAssetMetadataModel.organization_id,
            ).where(CoreAssetMetadataModel.asset_ref == legacy_ref)
        ).one()
    assert row.owner_scope_kind == "ORGANIZATION"
    assert row.owner_scope_ref is None
    assert row.organization_id == "storyrun-lite-legacy-fixture-org"


def test_cancel_racing_complete_aborts_upload_before_admission_and_cleans_staging(
    story_db, monkeypatch
) -> None:
    engine, repository = story_db
    owner = "parent-cancel-upload-race-" + str(uuid.uuid4())
    run_id = _create_run(repository, owner)
    payload = b"synthetic-cancel-upload-race"
    upload_id, digest = _create_upload(
        repository,
        owner=owner,
        run_id=run_id,
        content=payload,
        name="cancel-upload-race",
    )
    quarantine = repository._quarantine
    _snapshot_path, _snapshot = quarantine.assemble_snapshot(
        upload_id,
        [{"part_number": 1, "sha256": digest, "byte_size": len(payload)}],
        expected_size=len(payload),
        expected_sha256=digest,
    )
    assemble_started = threading.Event()
    allow_assemble = threading.Event()
    original_assemble = quarantine.assemble_snapshot

    def block_assemble(*args, **kwargs):
        assemble_started.set()
        assert allow_assemble.wait(timeout=10)
        return original_assemble(*args, **kwargs)

    monkeypatch.setattr(quarantine, "assemble_snapshot", block_assemble)
    cancel_started = threading.Event()

    def cancel():
        cancel_started.set()
        return repository.cancel_run(
            actor_scope_kind=_PARENT,
            actor_scope_ref=owner,
            run_id=run_id,
            expected_revision=1,
            expected_version=1,
            key_sha256=_hash("cancel-upload-race"),
            fingerprint_sha256=_hash("fingerprint-cancel-upload-race"),
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        try:
            completion = pool.submit(
                _reserve_complete,
                repository,
                owner=owner,
                upload_id=upload_id,
                digest=digest,
                size=len(payload),
                name="cancel-upload-race",
            )
            assert assemble_started.wait(timeout=10)
            cancellation = pool.submit(cancel)
            assert cancel_started.wait(timeout=10)
            allow_assemble.set()
            reservation = completion.result(timeout=15)
            cancelled = cancellation.result(timeout=15)
        finally:
            allow_assemble.set()

    assert reservation.upload_id == upload_id
    assert cancelled.status_code == 202
    assert cancelled.body["run_state"] == "DELETE_PENDING"
    assert not repository.open_upload_gate(
        upload_id=upload_id, claim_version=int(reservation.claim_version)
    )

    normalized = NormalizedImage(
        "image/png",
        digest,
        len(payload),
        1,
        1,
        "image/jpeg",
        _hash("cancel-race-derived"),
        1,
        b"x",
        1_073_741_824,
        25,
        120,
    )
    original_ref = str(uuid.uuid4())
    derived_ref = str(uuid.uuid4())
    assert not repository.finish_upload_admission(
        upload_id=upload_id,
        claim_version=int(reservation.claim_version),
        original_asset_ref=original_ref,
        derived_asset_ref=derived_ref,
        normalized=normalized,
        scanner=ScanVerdict("CLEAN", digest, "test-only", datetime.now(UTC)),
        actor_scope_ref=owner,
    )
    replay = _reserve_complete(
        repository,
        owner=owner,
        upload_id=upload_id,
        digest=digest,
        size=len(payload),
        name="cancel-upload-race",
    )
    assert replay.command_result.status_code == 409
    assert replay.command_result.body["code"] == "UPLOAD_SESSION_STATE_CONFLICT"
    assert replay.command_result.replayed is True

    current = repository.get_upload(
        actor_scope_kind=_PARENT, actor_scope_ref=owner, upload_id=upload_id
    )
    assert current.body["state"] == UploadState.ABORTED.value
    with engine.connect() as connection:
        assets = connection.execute(
            select(CoreAssetMetadataModel.asset_ref).where(
                CoreAssetMetadataModel.asset_ref.in_([original_ref, derived_ref])
            )
        ).all()
        upload = (
            connection.execute(
                select(tables.upload_sessions).where(
                    tables.upload_sessions.c.upload_session_id == upload_id
                )
            )
            .mappings()
            .one()
        )
    assert assets == []
    assert upload["state"] == UploadState.ABORTED.value
    assert not (quarantine._parts / upload_id).exists()
    assert not (quarantine._snapshots / f"{upload_id}.bin").exists()

    with pytest.raises(StoryRunLiteError) as create_after_cancel:
        repository.create_upload(
            actor_scope_kind=_PARENT,
            actor_scope_ref=owner,
            run_id=run_id,
            media_type="image/png",
            expected_size_bytes=len(payload),
            expected_sha256=digest,
            key_sha256=_hash("create-after-cancel"),
            fingerprint_sha256=_hash("fingerprint-create-after-cancel"),
        )
    assert create_after_cancel.value.status_code == 404


@pytest.mark.parametrize("winner", ["cancel", "admission"])
def test_cancel_and_admission_finalizer_race_serializes_asset_commit(story_db, winner: str) -> None:
    engine, repository = story_db
    owner = "parent-cancel-admission-race-" + winner + "-" + str(uuid.uuid4())
    run_id = _create_run(repository, owner)
    payload = b"synthetic-cancel-admission-race"
    upload_id, digest = _create_upload(
        repository,
        owner=owner,
        run_id=run_id,
        content=payload,
        name="cancel-admission-race-" + winner,
    )
    claim_version = _open_upload_for_admission(
        repository,
        owner=owner,
        upload_id=upload_id,
        digest=digest,
        size=len(payload),
        name="cancel-admission-race-" + winner,
    )
    normalized = _normalized_upload(payload, digest)
    original_ref = str(uuid.uuid4())
    derived_ref = str(uuid.uuid4())
    cancel_holds_run_before_uploads = threading.Event()
    allow_cancel = threading.Event()
    admission_at_asset_insert = threading.Event()
    allow_admission = threading.Event()
    finalizer_waiting_for_run = threading.Event()
    cancellation_waiting_for_run = threading.Event()
    thread_role = threading.local()
    commit_order: list[str] = []

    def coordinate_sql(_connection, _cursor, statement, _parameters, _context, _many):
        sql = statement.lower()
        is_lock = "for update" in sql
        role = getattr(thread_role, "value", None)
        if winner == "cancel" and role == "cancel" and "upload_sessions" in sql and is_lock:
            cancel_holds_run_before_uploads.set()
            assert allow_cancel.wait(timeout=15)
        elif winner == "cancel" and role == "admission" and _is_story_run_lock(statement):
            finalizer_waiting_for_run.set()
        elif (
            winner == "admission"
            and role == "admission"
            and "insert into core_asset_metadata" in sql
        ):
            if not admission_at_asset_insert.is_set():
                admission_at_asset_insert.set()
                assert allow_admission.wait(timeout=15)
        elif winner == "admission" and role == "cancel" and _is_story_run_lock(statement):
            cancellation_waiting_for_run.set()

    event.listen(engine, "before_cursor_execute", coordinate_sql)

    def cancel():
        thread_role.value = "cancel"
        result = repository.cancel_run(
            actor_scope_kind=_PARENT,
            actor_scope_ref=owner,
            run_id=run_id,
            expected_revision=1,
            expected_version=1,
            key_sha256=_hash("cancel-admission-race:" + winner),
            fingerprint_sha256=_hash("fingerprint-cancel-admission-race:" + winner),
        )
        commit_order.append("cancel")
        return result

    def finalize_admission():
        thread_role.value = "admission"
        result = repository.finish_upload_admission(
            upload_id=upload_id,
            claim_version=claim_version,
            original_asset_ref=original_ref,
            derived_asset_ref=derived_ref,
            normalized=normalized,
            scanner=ScanVerdict("CLEAN", digest, "test-only", datetime.now(UTC)),
            actor_scope_ref=owner,
        )
        commit_order.append("admission")
        return result

    try:
        with ThreadPoolExecutor(
            max_workers=2, thread_name_prefix="storyrun-admission-race"
        ) as pool:
            try:
                if winner == "cancel":
                    cancellation = pool.submit(cancel)
                    assert cancel_holds_run_before_uploads.wait(timeout=10)
                    admission = pool.submit(finalize_admission)
                    assert finalizer_waiting_for_run.wait(timeout=10)
                    allow_cancel.set()
                    cancel_result = cancellation.result(timeout=15)
                    admission_result = admission.result(timeout=15)
                else:
                    admission = pool.submit(finalize_admission)
                    assert admission_at_asset_insert.wait(timeout=10)
                    cancellation = pool.submit(cancel)
                    assert cancellation_waiting_for_run.wait(timeout=10)
                    allow_admission.set()
                    admission_result = admission.result(timeout=15)
                    cancel_result = cancellation.result(timeout=15)
            finally:
                allow_cancel.set()
                allow_admission.set()
    finally:
        event.remove(engine, "before_cursor_execute", coordinate_sql)

    assert cancel_result.status_code == 202
    assert cancel_result.body["run_state"] == "DELETE_PENDING"
    with engine.connect() as connection:
        upload = (
            connection.execute(
                select(tables.upload_sessions).where(
                    tables.upload_sessions.c.upload_session_id == upload_id
                )
            )
            .mappings()
            .one()
        )
        assets = (
            connection.execute(
                select(CoreAssetMetadataModel.asset_ref).where(
                    CoreAssetMetadataModel.asset_ref.in_([original_ref, derived_ref])
                )
            )
            .scalars()
            .all()
        )
    if winner == "cancel":
        assert commit_order == ["cancel", "admission"]
        assert admission_result is False
        assert upload["state"] == UploadState.ABORTED.value
        assert assets == []
        assert not (repository._quarantine._parts / upload_id).exists()
        assert not (repository._quarantine._snapshots / f"{upload_id}.bin").exists()
    else:
        assert commit_order == ["admission", "cancel"]
        assert admission_result is True
        assert upload["state"] == UploadState.READY.value
        assert set(assets) == {original_ref, derived_ref}
        assert not (repository._quarantine._parts / upload_id).exists()
        assert not (repository._quarantine._snapshots / f"{upload_id}.bin").exists()


def test_expiry_is_enforced_at_utc_boundary_for_get_put_complete_and_versions(
    story_db, monkeypatch
) -> None:
    engine, repository = story_db
    owner = "parent-upload-expiry-boundary-" + str(uuid.uuid4())
    run_id = _create_run(repository, owner)
    payload = b"synthetic-expiry-boundary"
    upload_id, digest = _create_upload(
        repository,
        owner=owner,
        run_id=run_id,
        content=payload,
        name="expiry-boundary",
    )
    quarantine = repository._quarantine
    snapshot_path, _snapshot = quarantine.assemble_snapshot(
        upload_id,
        [{"part_number": 1, "sha256": digest, "byte_size": len(payload)}],
        expected_size=len(payload),
        expected_sha256=digest,
    )
    fixed_now = datetime(2030, 1, 2, 3, 4, 5, tzinfo=UTC)

    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            if tz is None:
                return fixed_now.replace(tzinfo=None)
            return fixed_now.astimezone(tz)

    monkeypatch.setattr(repository_module, "datetime", FrozenDateTime)
    with engine.begin() as connection:
        connection.execute(
            update(tables.upload_sessions)
            .where(tables.upload_sessions.c.upload_session_id == upload_id)
            .values(expires_at=fixed_now + timedelta(microseconds=1))
        )
    before = repository.get_upload(
        actor_scope_kind=_PARENT, actor_scope_ref=owner, upload_id=upload_id
    )
    assert before.status_code == 200
    assert before.body["state"] == UploadState.RECEIVING.value

    with engine.begin() as connection:
        connection.execute(
            update(tables.upload_sessions)
            .where(tables.upload_sessions.c.upload_session_id == upload_id)
            .values(expires_at=fixed_now)
        )
    with pytest.raises(StoryRunLiteError) as expired_get:
        repository.get_upload(actor_scope_kind=_PARENT, actor_scope_ref=owner, upload_id=upload_id)
    assert expired_get.value.status_code == 410
    assert expired_get.value.code == "UPLOAD_EXPIRED"
    assert not snapshot_path.exists()
    assert not (quarantine._parts / upload_id).exists()

    with engine.connect() as connection:
        row = (
            connection.execute(
                select(tables.upload_sessions).where(
                    tables.upload_sessions.c.upload_session_id == upload_id
                )
            )
            .mappings()
            .one()
        )
        part_count = connection.execute(
            select(tables.upload_parts.c.upload_part_id).where(
                tables.upload_parts.c.upload_session_id == upload_id
            )
        ).all()
    assert row["state"] == UploadState.EXPIRED.value
    assert row["state_version"] == 2
    assert row["admission_gate_open"] is False
    assert row["claim_version"] is None
    assert len(part_count) == 1

    new_part = b"must-not-be-staged"
    with pytest.raises(StoryRunLiteError) as expired_put:
        repository.put_part(
            actor_scope_kind=_PARENT,
            actor_scope_ref=owner,
            upload_id=upload_id,
            part_number=2,
            payload=new_part,
            declared_length=len(new_part),
            declared_sha256=hashlib.sha256(new_part).hexdigest(),
        )
    assert expired_put.value.status_code == 410
    assert expired_put.value.code == "UPLOAD_EXPIRED"

    completed = _reserve_complete(
        repository,
        owner=owner,
        upload_id=upload_id,
        digest=digest,
        size=len(payload),
        name="expiry-boundary",
        version=2,
    )
    assert completed.command_result.status_code == 410
    assert completed.command_result.body["code"] == "UPLOAD_EXPIRED"
    replay = _reserve_complete(
        repository,
        owner=owner,
        upload_id=upload_id,
        digest=digest,
        size=len(payload),
        name="expiry-boundary",
        version=2,
    )
    assert replay.command_result.status_code == 410
    assert replay.command_result.replayed is True
    assert replay.command_result.body == completed.command_result.body
    with engine.connect() as connection:
        row = (
            connection.execute(
                select(tables.upload_sessions).where(
                    tables.upload_sessions.c.upload_session_id == upload_id
                )
            )
            .mappings()
            .one()
        )
        receipt = (
            connection.execute(
                select(tables.upload_command_receipts).where(
                    tables.upload_command_receipts.c.resource_ref == upload_id,
                    tables.upload_command_receipts.c.operation == "COMPLETE_UPLOAD",
                )
            )
            .mappings()
            .one()
        )
    assert row["state"] == UploadState.EXPIRED.value
    assert row["state_version"] == 2
    assert row["admission_gate_open"] is False
    assert row["claim_version"] is None
    assert receipt["response_status"] == 410
    assert not snapshot_path.exists()


@pytest.mark.parametrize("operation", ["get", "put", "complete"])
def test_expiry_uses_utc_time_after_story_run_lock_wait(
    story_db, monkeypatch, operation: str
) -> None:
    engine, repository = story_db
    owner = "parent-upload-expiry-lock-wait-" + operation + "-" + str(uuid.uuid4())
    run_id = _create_run(repository, owner)
    payload = b"synthetic-expiry-lock-wait"
    upload_id, digest = _create_upload(
        repository,
        owner=owner,
        run_id=run_id,
        content=payload,
        name="expiry-lock-wait-" + operation,
    )
    deadline = datetime(2030, 2, 3, 4, 5, 6, tzinfo=UTC)
    clock = {"now": deadline - timedelta(microseconds=1)}

    class ControlledDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            value = clock["now"]
            return value.replace(tzinfo=None) if tz is None else value.astimezone(tz)

    monkeypatch.setattr(repository_module, "datetime", ControlledDateTime)
    with engine.begin() as connection:
        connection.execute(
            update(tables.upload_sessions)
            .where(tables.upload_sessions.c.upload_session_id == upload_id)
            .values(expires_at=deadline)
        )

    holder = engine.connect()
    holder_transaction = holder.begin()
    holder.execute(
        select(tables.story_runs.c.run_id)
        .where(tables.story_runs.c.run_id == run_id)
        .with_for_update()
    )
    lock_wait_started = threading.Event()

    def observe_run_lock(_connection, _cursor, statement, _parameters, _context, _many):
        if _is_story_run_lock(statement):
            lock_wait_started.set()

    event.listen(engine, "before_cursor_execute", observe_run_lock)

    def invoke():
        try:
            if operation == "get":
                return repository.get_upload(
                    actor_scope_kind=_PARENT,
                    actor_scope_ref=owner,
                    upload_id=upload_id,
                )
            if operation == "put":
                new_part = b"must-not-be-staged-after-lock-wait"
                return repository.put_part(
                    actor_scope_kind=_PARENT,
                    actor_scope_ref=owner,
                    upload_id=upload_id,
                    part_number=2,
                    payload=new_part,
                    declared_length=len(new_part),
                    declared_sha256=hashlib.sha256(new_part).hexdigest(),
                )
            return _reserve_complete(
                repository,
                owner=owner,
                upload_id=upload_id,
                digest=digest,
                size=len(payload),
                name="expiry-lock-wait-" + operation,
            )
        except StoryRunLiteError as exc:
            return exc

    try:
        with ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="storyrun-expiry-operation"
        ) as pool:
            try:
                pending = pool.submit(invoke)
                assert lock_wait_started.wait(timeout=10)
                clock["now"] = deadline + timedelta(microseconds=1)
                holder_transaction.commit()
                result = pending.result(timeout=15)
            finally:
                if holder_transaction.is_active:
                    holder_transaction.rollback()
    finally:
        event.remove(engine, "before_cursor_execute", observe_run_lock)
        if holder_transaction.is_active:
            holder_transaction.rollback()
        holder.close()

    if operation == "complete":
        assert result.command_result.status_code == 410
        assert result.command_result.body["code"] == "UPLOAD_EXPIRED"
        replay = _reserve_complete(
            repository,
            owner=owner,
            upload_id=upload_id,
            digest=digest,
            size=len(payload),
            name="expiry-lock-wait-" + operation,
        )
        assert replay.command_result.status_code == 410
        assert replay.command_result.replayed is True
    else:
        assert isinstance(result, StoryRunLiteError)
        assert result.status_code == 410
        assert result.code == "UPLOAD_EXPIRED"

    with engine.connect() as connection:
        upload = (
            connection.execute(
                select(tables.upload_sessions).where(
                    tables.upload_sessions.c.upload_session_id == upload_id
                )
            )
            .mappings()
            .one()
        )
        parts = connection.execute(
            select(tables.upload_parts.c.upload_part_id).where(
                tables.upload_parts.c.upload_session_id == upload_id
            )
        ).all()
        completion_receipts = (
            connection.execute(
                select(tables.upload_command_receipts).where(
                    tables.upload_command_receipts.c.resource_ref == upload_id,
                    tables.upload_command_receipts.c.operation == "COMPLETE_UPLOAD",
                )
            )
            .mappings()
            .all()
        )
    assert upload["state"] == UploadState.EXPIRED.value
    assert upload["state_version"] == 2
    assert upload["admission_gate_open"] is False
    assert upload["claim_version"] is None
    assert len(parts) == 1
    assert not (repository._quarantine._parts / upload_id).exists()
    assert not (repository._quarantine._snapshots / f"{upload_id}.bin").exists()
    if operation == "complete":
        assert len(completion_receipts) == 1
        assert completion_receipts[0]["response_status"] == 410


def test_recovery_rechecks_expiry_after_wait_on_unfinished_upload_lock(
    story_db, monkeypatch
) -> None:
    engine, repository = story_db
    owner = "parent-upload-expiry-recovery-lock-wait-" + str(uuid.uuid4())
    run_id = _create_run(repository, owner)
    payload = b"synthetic-expiry-recovery-lock-wait"
    upload_id, digest = _create_upload(
        repository,
        owner=owner,
        run_id=run_id,
        content=payload,
        name="expiry-recovery-lock-wait",
    )
    snapshot_path, _snapshot = repository._quarantine.assemble_snapshot(
        upload_id,
        [{"part_number": 1, "sha256": digest, "byte_size": len(payload)}],
        expected_size=len(payload),
        expected_sha256=digest,
    )
    deadline = datetime(2030, 3, 4, 5, 6, 7, tzinfo=UTC)
    clock = {"now": deadline - timedelta(microseconds=1)}

    class ControlledDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            value = clock["now"]
            return value.replace(tzinfo=None) if tz is None else value.astimezone(tz)

    monkeypatch.setattr(repository_module, "datetime", ControlledDateTime)
    with engine.begin() as connection:
        connection.execute(
            update(tables.upload_sessions)
            .where(tables.upload_sessions.c.upload_session_id == upload_id)
            .values(expires_at=deadline)
        )

    blocker_owner = "parent-expiry-recovery-blocker-" + str(uuid.uuid4())
    blocker_run_id = _create_run(repository, blocker_owner)
    blocker_payload = b"synthetic-recovery-pending-lock"
    blocker_upload_id, blocker_digest = _create_upload(
        repository,
        owner=blocker_owner,
        run_id=blocker_run_id,
        content=blocker_payload,
        name="expiry-recovery-lock-blocker",
    )
    pending = _reserve_complete(
        repository,
        owner=blocker_owner,
        upload_id=blocker_upload_id,
        digest=blocker_digest,
        size=len(blocker_payload),
        name="expiry-recovery-lock-blocker",
    )
    assert pending.command_result.status_code == 202

    recovery_time = deadline + timedelta(microseconds=1)
    with engine.connect() as connection:
        before = (
            connection.execute(
                select(
                    tables.upload_sessions.c.upload_session_id,
                    tables.upload_sessions.c.state,
                    tables.upload_sessions.c.expires_at,
                )
            )
            .mappings()
            .all()
        )
    expected_failed = {
        row["upload_session_id"]
        for row in before
        if row["state"] in (UploadState.PENDING.value, UploadState.PROCESSING.value)
    }
    expected_expiring = {
        row["upload_session_id"]
        for row in before
        if row["state"] == UploadState.RECEIVING.value and row["expires_at"] <= recovery_time
    }
    expected_cleanup = expected_expiring | {
        row["upload_session_id"] for row in before if row["state"] == UploadState.EXPIRED.value
    }
    assert blocker_upload_id in expected_failed
    assert upload_id in expected_expiring
    cleanup_calls: list[str] = []
    original_remove = repository._quarantine.remove_upload

    def record_cleanup(resource_id: str) -> None:
        cleanup_calls.append(resource_id)
        original_remove(resource_id)

    monkeypatch.setattr(repository._quarantine, "remove_upload", record_cleanup)

    holder = engine.connect()
    holder_transaction = holder.begin()
    holder.execute(
        select(tables.upload_sessions.c.upload_session_id)
        .where(tables.upload_sessions.c.upload_session_id == blocker_upload_id)
        .with_for_update()
    )
    recovery_lock_waiting = threading.Event()

    def observe_pending_lock(_connection, _cursor, statement, parameters, _context, _many):
        sql = statement.lower()
        values = repr(parameters).lower()
        if (
            "upload_sessions" in sql
            and "for update" in sql
            and "pending" in values
            and "processing" in values
        ):
            recovery_lock_waiting.set()

    event.listen(engine, "before_cursor_execute", observe_pending_lock)
    try:
        with ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="storyrun-expiry-recovery"
        ) as pool:
            try:
                pending = pool.submit(repository.recover_after_restart)
                assert recovery_lock_waiting.wait(timeout=10)
                clock["now"] = recovery_time
                holder_transaction.commit()
                counts = pending.result(timeout=15)
            finally:
                if holder_transaction.is_active:
                    holder_transaction.rollback()
    finally:
        event.remove(engine, "before_cursor_execute", observe_pending_lock)
        if holder_transaction.is_active:
            holder_transaction.rollback()
        holder.close()

    assert counts["core_sessions_failed"] == len(expected_failed)
    assert counts["core_sessions_expired"] == len(expected_expiring)
    assert counts["core_expired_cleanup_succeeded"] == len(expected_cleanup)
    assert counts["core_expired_cleanup_failed"] == 0
    assert sorted(cleanup_calls) == sorted(expected_cleanup)
    assert cleanup_calls.count(upload_id) == 1
    assert not (repository._quarantine._parts / upload_id).exists()
    assert not snapshot_path.exists()
    with engine.connect() as connection:
        row = (
            connection.execute(
                select(tables.upload_sessions).where(
                    tables.upload_sessions.c.upload_session_id == upload_id
                )
            )
            .mappings()
            .one()
        )
        blocker = (
            connection.execute(
                select(tables.upload_sessions).where(
                    tables.upload_sessions.c.upload_session_id == blocker_upload_id
                )
            )
            .mappings()
            .one()
        )
    assert row["state"] == UploadState.EXPIRED.value
    assert row["state_version"] == 2
    assert blocker["state"] == UploadState.FAILED.value


def test_startup_recovery_expires_receiving_and_retries_staging_cleanup(story_db, monkeypatch):
    engine, repository = story_db
    owner = "parent-upload-expiry-recovery-" + str(uuid.uuid4())
    run_id = _create_run(repository, owner)
    payload = b"synthetic-expiry-recovery"
    upload_id, digest = _create_upload(
        repository,
        owner=owner,
        run_id=run_id,
        content=payload,
        name="expiry-recovery",
    )
    quarantine = repository._quarantine
    snapshot_path, _snapshot = quarantine.assemble_snapshot(
        upload_id,
        [{"part_number": 1, "sha256": digest, "byte_size": len(payload)}],
        expected_size=len(payload),
        expected_sha256=digest,
    )
    parts_path = quarantine._parts / upload_id
    recovery_time = datetime.now(UTC)

    class ControlledDateTime(datetime):
        @classmethod
        def now(cls, tz: tzinfo | None = None) -> Self:
            value = cls.fromisoformat(recovery_time.isoformat())
            return value.replace(tzinfo=None) if tz is None else value.astimezone(tz)

    monkeypatch.setattr(repository_module, "datetime", ControlledDateTime)
    with engine.begin() as connection:
        connection.execute(
            update(tables.upload_sessions)
            .where(tables.upload_sessions.c.upload_session_id == upload_id)
            .values(expires_at=recovery_time - timedelta(seconds=1))
        )
    with engine.connect() as connection:
        before = (
            connection.execute(
                select(
                    tables.upload_sessions.c.upload_session_id,
                    tables.upload_sessions.c.state,
                    tables.upload_sessions.c.expires_at,
                )
            )
            .mappings()
            .all()
        )
    expected_expiring = {
        row["upload_session_id"]
        for row in before
        if row["state"] == UploadState.RECEIVING.value and row["expires_at"] <= recovery_time
    }
    expected_cleanup = expected_expiring | {
        row["upload_session_id"] for row in before if row["state"] == UploadState.EXPIRED.value
    }
    assert upload_id in expected_expiring

    original_remove = quarantine.remove_upload
    cleanup_calls: list[str] = []
    target_attempts = 0

    def fail_first_cleanup(resource_id: str) -> None:
        nonlocal target_attempts
        cleanup_calls.append(resource_id)
        if resource_id == upload_id:
            target_attempts += 1
            if target_attempts == 1:
                raise OSError("synthetic cleanup failure")
        original_remove(resource_id)

    monkeypatch.setattr(quarantine, "remove_upload", fail_first_cleanup)
    first = repository.recover_after_restart()
    assert first["core_sessions_expired"] == len(expected_expiring)
    assert first["core_expired_cleanup_failed"] == 1
    assert first["core_expired_cleanup_succeeded"] == len(expected_cleanup) - 1
    assert sorted(cleanup_calls) == sorted(expected_cleanup)
    assert target_attempts == 1
    assert parts_path.exists()
    assert snapshot_path.exists()
    with engine.connect() as connection:
        first_row = (
            connection.execute(
                select(tables.upload_sessions).where(
                    tables.upload_sessions.c.upload_session_id == upload_id
                )
            )
            .mappings()
            .one()
        )
    assert first_row["state"] == UploadState.EXPIRED.value
    assert first_row["state_version"] == 2

    cleanup_calls.clear()
    second = repository.recover_after_restart()
    assert second["core_sessions_expired"] == 0
    assert second["core_expired_cleanup_succeeded"] == len(expected_cleanup)
    assert second["core_expired_cleanup_failed"] == 0
    assert sorted(cleanup_calls) == sorted(expected_cleanup)
    assert target_attempts == 2
    assert not parts_path.exists()
    assert not snapshot_path.exists()
    with engine.connect() as connection:
        row = (
            connection.execute(
                select(tables.upload_sessions).where(
                    tables.upload_sessions.c.upload_session_id == upload_id
                )
            )
            .mappings()
            .one()
        )
    assert row["state"] == UploadState.EXPIRED.value
    assert row["state_version"] == 2


def test_review_two_http_flows_release_owner_and_replay_attach_without_resending(story_db) -> None:
    """Exercise real HTTP/service/storage with synthetic scanner, worker and Vision doubles."""
    engine, repository = story_db
    owner = "review-repeat-parent-" + str(uuid.uuid4())
    scanner, normalizer, vision = Mock(), Mock(), Mock()
    scanner.scan.side_effect = lambda _payload, digest: ScanVerdict(
        "CLEAN", digest, "synthetic-test-only", datetime.now(UTC)
    )

    def normalize(payload: bytes, *, original_media_type: str, sha256: str) -> NormalizedImage:
        derived = b"synthetic-derived:" + payload
        return NormalizedImage(
            original_media_type,
            sha256,
            len(payload),
            1,
            1,
            "image/jpeg",
            hashlib.sha256(derived).hexdigest(),
            len(derived),
            derived,
            128 * 1024 * 1024,
            25,
            120,
            1024,
            1,
            0,
            25,
            1,
        )

    normalizer.normalize.side_effect = normalize

    def analyze(*, run_id, binding, persist_success):
        committed = persist_success(
            ValidatedVisionResult(
                {"contract_name": "SyntheticReviewResult", "asset_ref": binding.asset_ref},
                "Synthetic subject",
                0.75,
                _hash("canonical:" + run_id),
                _hash("raw:" + run_id),
            )
        )
        assert committed
        return VisionAttemptResult("SUCCEEDED", provider_invoked=True, result_committed=True)

    vision.analyze.side_effect = analyze
    service = StoryRunLiteService(
        repository=repository,
        scanner=cast(ImageSafetyScannerPort, scanner),
        normalizer=cast(ImageNormalizerPort, normalizer),
        vision=cast(StoryRunLiteVisionPort, vision),
        story_references=cast(StoryRunReferencePort, repository),
        asset_admission=cast(CoreAssetAdmissionPort, repository),
        actor_scope_ref=owner,
    )
    previous_runs: list[tuple[str, str, bytes]] = []
    with TestClient(create_app(service=service)) as client:
        for turn in range(2):
            tag = str(uuid.uuid4())
            created = client.post(
                "/v1/story-runs",
                json={"profile_ref": "synthetic-parent-demo"},
                headers={"Idempotency-Key": "create-" + tag},
            )
            assert created.status_code == 201
            run_id = created.json()["run_ref"]
            payload = ("synthetic-chosen-photo-" + str(turn)).encode()
            digest = hashlib.sha256(payload).hexdigest()
            upload = client.post(
                "/v1/upload-sessions",
                json={
                    "target_ref": run_id,
                    "purpose": "RUN_ARTWORK",
                    "media_type": "image/png",
                    "expected_size_bytes": len(payload),
                    "expected_sha256": digest,
                },
                headers={"Idempotency-Key": "upload-" + tag},
            )
            assert upload.status_code == 201
            upload_id = upload.json()["upload_ref"]
            part = client.put(
                f"/v1/upload-sessions/{upload_id}/parts/1",
                content=payload,
                headers={
                    "Content-Type": "application/octet-stream",
                    "Content-Length": str(len(payload)),
                    "Content-SHA256": digest,
                },
            )
            assert part.status_code == 200
            completed = client.post(
                f"/v1/upload-sessions/{upload_id}/complete",
                json={"expected_size_bytes": len(payload), "expected_sha256": digest},
                headers={"Idempotency-Key": "complete-" + tag, "If-Match": upload.headers["etag"]},
            )
            assert completed.status_code == 202
            admitted = client.get(f"/v1/upload-sessions/{upload_id}")
            assert admitted.json()["state"] == "READY"
            asset_ref = admitted.json()["asset_ref"]
            attach_headers = {
                "Idempotency-Key": "attach-" + tag,
                "If-Match": created.headers["etag"],
            }
            attach_body = {"asset_ref": asset_ref, "expected_revision": 1}
            attached = client.post(
                f"/v1/story-runs/{run_id}/assets",
                json=attach_body,
                headers=attach_headers,
            )
            assert attached.status_code == 202
            subject = client.get(f"/v1/story-runs/{run_id}")
            assert subject.json()["run_state"] == "SUBJECT_REVIEW"
            replay = client.post(
                f"/v1/story-runs/{run_id}/assets",
                json=attach_body,
                headers=attach_headers,
            )
            assert (replay.status_code, replay.json(), replay.headers["etag"]) == (
                attached.status_code,
                attached.json(),
                attached.headers["etag"],
            )
            changed = client.post(
                f"/v1/story-runs/{run_id}/assets",
                json={**attach_body, "expected_revision": 2},
                headers=attach_headers,
            )
            assert changed.status_code == 400
            assert changed.json()["code"] == "INVALID_IDEMPOTENCY_KEY"
            with pytest.raises(StoryRunLiteError) as forbidden:
                repository.replay_attach_command(
                    actor_scope_kind=_PARENT,
                    actor_scope_ref=owner + "-foreign",
                    run_id=run_id,
                    key_sha256=validate_idempotency_key("attach-" + tag),
                    fingerprint_sha256=canonical_fingerprint(
                        method="POST",
                        path=f"/v1/story-runs/{run_id}/assets",
                        request=attach_body,
                        expected_version=1,
                    ),
                )
            assert forbidden.value.status_code == 404
            confirmed = client.post(
                f"/v1/story-runs/{run_id}/subject-confirmation",
                json={"decision": "CONFIRM", "expected_understanding_revision": 1},
                headers={"Idempotency-Key": "confirm-" + tag, "If-Match": subject.headers["etag"]},
            )
            assert confirmed.status_code == 202
            assert confirmed.json()["run_state"] == "PREPARATION_REVIEW"
            after_confirm = client.post(
                f"/v1/story-runs/{run_id}/assets",
                json=attach_body,
                headers=attach_headers,
            )
            assert after_confirm.status_code == 202 and after_confirm.json() == attached.json()
            canceled = client.post(
                f"/v1/story-runs/{run_id}/cancel",
                json={"expected_revision": confirmed.json()["revision"]},
                headers={"Idempotency-Key": "cancel-" + tag, "If-Match": confirmed.headers["etag"]},
            )
            assert canceled.status_code == 202
            assert canceled.json()["run_state"] == "DELETE_PENDING"
            after_cancel = client.post(
                f"/v1/story-runs/{run_id}/assets",
                json=attach_body,
                headers=attach_headers,
            )
            assert after_cancel.status_code == 202 and after_cancel.json() == attached.json()
            assert vision.analyze.call_count == turn + 1
            previous_runs.append((run_id, asset_ref, payload))
            with engine.connect() as connection:
                stored = (
                    connection.execute(
                        select(tables.story_runs).where(tables.story_runs.c.run_id == run_id)
                    )
                    .mappings()
                    .one()
                )
                assert stored["active_owner_parent_account_id"] is None
                assert (
                    connection.execute(
                        select(tables.understanding_revisions).where(
                            tables.understanding_revisions.c.run_id == run_id
                        )
                    )
                    .mappings()
                    .one()["result_snapshot"]["contract_name"]
                    == "SyntheticReviewResult"
                )
                assert (
                    connection.execute(
                        select(tables.review_decisions).where(
                            tables.review_decisions.c.run_id == run_id
                        )
                    )
                    .mappings()
                    .one()["decision"]
                    == "CONFIRM"
                )
            assert repository.read_asset(asset_ref) == payload
    assert len({run for run, _ref, _payload in previous_runs}) == 2
    for old_run, old_asset, old_payload in previous_runs:
        assert repository.read_asset(old_asset) == old_payload
        assert repository.get_run(actor_scope_kind=_PARENT, actor_scope_ref=owner, run_id=old_run)


def test_review_http_replays_final_attach_receipt_after_restart_recovery(story_db) -> None:
    _engine, repository = story_db
    owner = "review-recovered-replay-" + str(uuid.uuid4())
    run_id = _create_run(repository, owner)
    pair = _asset_pair(run_id, owner, seed="review-recovered")
    key = "attach-recovered-" + str(uuid.uuid4())
    body = {"asset_ref": pair.original.asset_ref, "expected_revision": 1}
    key_hash = validate_idempotency_key(key)
    fingerprint = canonical_fingerprint(
        method="POST",
        path=f"/v1/story-runs/{run_id}/assets",
        request=body,
        expected_version=1,
    )
    _reserved, _job, claim = repository.attach_asset(
        actor_scope_kind=_PARENT,
        actor_scope_ref=owner,
        run_id=run_id,
        pair=pair,
        expected_revision=1,
        expected_version=1,
        key_sha256=key_hash,
        fingerprint_sha256=fingerprint,
    )
    assert claim is not None
    initial = repository.finalize_attach_command(
        run_id=run_id,
        key_sha256=key_hash,
        claimed_version=claim,
    )
    repository.recover_after_restart()
    current = repository.get_run(actor_scope_kind=_PARENT, actor_scope_ref=owner, run_id=run_id)
    assert current.body["job_state"] == "AWAITING_RECONCILIATION"
    vision, admission = Mock(), Mock()
    service = StoryRunLiteService(
        repository=repository,
        scanner=cast(ImageSafetyScannerPort, object()),
        normalizer=cast(ImageNormalizerPort, object()),
        vision=cast(StoryRunLiteVisionPort, vision),
        story_references=repository,
        asset_admission=cast(CoreAssetAdmissionPort, admission),
        actor_scope_ref=owner,
    )
    with TestClient(create_app(service=service)) as client:
        replay = client.post(
            f"/v1/story-runs/{run_id}/assets",
            json=body,
            headers={"Idempotency-Key": key, "If-Match": '"v1"'},
        )
    assert replay.status_code == initial.status_code == 202
    assert replay.json() == initial.body
    vision.analyze.assert_not_called()
    admission.resolve_story_artwork.assert_not_called()


def _review_prepare_confirmed_run(repository: SqlStoryRunLiteRepository, owner: str):
    """Reach the real post-confirmation state before testing closeout authority."""
    run_id = _create_run(repository, owner)
    name = "review-confirmed-" + str(uuid.uuid4())
    pair = _asset_pair(run_id, owner, seed=name)
    _result, _job, claim = _attach(repository, owner=owner, run_id=run_id, pair=pair, name=name)
    assert claim is not None
    repository.finalize_attach_command(
        run_id=run_id, key_sha256=_hash("attach:" + name), claimed_version=claim
    )
    assert repository.open_story_dispatch_gate(run_id=run_id, claimed_version=claim)
    assert repository.commit_vision_success(
        run_id=run_id,
        claimed_version=claim,
        result_snapshot={"contract_name": "SyntheticCloseoutRace", "run_ref": run_id},
        subject_label="synthetic closeout subject",
        confidence=0.75,
        canonical_result_sha256=_hash("canonical:" + name),
        raw_body_sha256=_hash("raw:" + name),
    )
    subject = repository.get_run(actor_scope_kind=_PARENT, actor_scope_ref=owner, run_id=run_id)
    confirmed = repository.confirm_subject(
        actor_scope_kind=_PARENT,
        actor_scope_ref=owner,
        run_id=run_id,
        expected_version=int(subject.resource_version),
        expected_understanding_revision=1,
        key_sha256=_hash("confirm:" + name),
        fingerprint_sha256=_hash("confirm-fingerprint:" + name),
    )
    assert confirmed.status_code == 202
    assert confirmed.body["run_state"] == "PREPARATION_REVIEW"
    return run_id, confirmed


@pytest.mark.parametrize("winner", ["cancel", "create"])
def test_review_post_confirm_cancel_and_create_serialize_owner_release(story_db, winner) -> None:
    engine, repository = story_db
    owner = "review-closeout-race-" + str(uuid.uuid4())
    run_id, confirmed = _review_prepare_confirmed_run(repository, owner)
    cancel_holds = threading.Event()
    create_holds = threading.Event()
    create_waiting = threading.Event()
    cancel_waiting = threading.Event()
    allow_cancel = threading.Event()
    allow_create = threading.Event()
    role = threading.local()

    def before_sql(_connection, _cursor, statement, _params, _context, _many):
        sql = statement.lower()
        current_role = getattr(role, "value", None)
        if (
            winner == "cancel"
            and current_role == "cancel"
            and sql.lstrip().startswith("update story.runs")
        ):
            cancel_holds.set()
            assert allow_cancel.wait(timeout=15)
        elif winner == "cancel" and current_role == "create" and _is_story_run_lock(statement):
            create_waiting.set()
        elif winner == "create" and current_role == "cancel" and _is_story_run_lock(statement):
            cancel_waiting.set()

    def after_sql(_connection, _cursor, statement, _params, _context, _many):
        if (
            winner == "create"
            and getattr(role, "value", None) == "create"
            and _is_story_run_lock(statement)
        ):
            create_holds.set()
            assert allow_create.wait(timeout=15)

    create_key = _hash("review-create-race:" + owner)
    create_fingerprint = _hash("review-create-race-fingerprint:" + owner)
    cancel_key = _hash("review-cancel-race:" + owner)
    cancel_fingerprint = _hash("review-cancel-race-fingerprint:" + owner)

    def create():
        role.value = "create"
        return repository.create_run(
            actor_scope_kind=_PARENT,
            actor_scope_ref=owner,
            profile_ref="synthetic-parent-demo",
            key_sha256=create_key,
            fingerprint_sha256=create_fingerprint,
        )

    def cancel():
        role.value = "cancel"
        return repository.cancel_run(
            actor_scope_kind=_PARENT,
            actor_scope_ref=owner,
            run_id=run_id,
            expected_revision=int(confirmed.body["revision"]),
            expected_version=int(confirmed.resource_version),
            key_sha256=cancel_key,
            fingerprint_sha256=cancel_fingerprint,
        )

    event.listen(engine, "before_cursor_execute", before_sql)
    event.listen(engine, "after_cursor_execute", after_sql)
    try:
        with ThreadPoolExecutor(max_workers=2, thread_name_prefix="review-closeout-race") as pool:
            try:
                if winner == "cancel":
                    cancellation = pool.submit(cancel)
                    assert cancel_holds.wait(timeout=10)
                    creation = pool.submit(create)
                    assert create_waiting.wait(timeout=10)
                    allow_cancel.set()
                else:
                    creation = pool.submit(create)
                    assert create_holds.wait(timeout=10)
                    cancellation = pool.submit(cancel)
                    assert cancel_waiting.wait(timeout=10)
                    allow_create.set()
                canceled = cancellation.result(timeout=15)
                created = creation.result(timeout=15)
            finally:
                allow_cancel.set()
                allow_create.set()
    finally:
        event.remove(engine, "before_cursor_execute", before_sql)
        event.remove(engine, "after_cursor_execute", after_sql)

    assert canceled.status_code == 202
    assert canceled.body["run_state"] == "DELETE_PENDING"
    assert created.status_code == (201 if winner == "cancel" else 409)
    if winner == "create":
        assert created.body["code"] == "ACTIVE_RUN_EXISTS"
        replay_create = create()
        assert replay_create.replayed is True
        assert replay_create.status_code == 409
        assert replay_create.body == created.body
        next_run = repository.create_run(
            actor_scope_kind=_PARENT,
            actor_scope_ref=owner,
            profile_ref="synthetic-parent-demo",
            key_sha256=_hash("review-create-after-close:" + owner),
            fingerprint_sha256=_hash("review-create-after-close-fingerprint:" + owner),
        )
        assert next_run.status_code == 201
    with engine.connect() as connection:
        old = (
            connection.execute(
                select(tables.story_runs).where(tables.story_runs.c.run_id == run_id)
            )
            .mappings()
            .one()
        )
        active = connection.execute(
            select(tables.story_runs.c.run_id).where(
                tables.story_runs.c.active_owner_parent_account_id == owner
            )
        ).all()
        retained_result = connection.execute(
            select(tables.understanding_revisions.c.result_snapshot).where(
                tables.understanding_revisions.c.run_id == run_id
            )
        ).scalar_one()
        retained_decision = connection.execute(
            select(tables.review_decisions.c.decision).where(
                tables.review_decisions.c.run_id == run_id
            )
        ).scalar_one()
    assert old["active_owner_parent_account_id"] is None
    assert len(active) == 1
    assert retained_result["contract_name"] == "SyntheticCloseoutRace"
    assert retained_decision == "CONFIRM"


def test_review_post_confirm_duplicate_cancel_replays_original_receipt(story_db) -> None:
    engine, repository = story_db
    owner = "review-duplicate-close-" + str(uuid.uuid4())
    run_id, confirmed = _review_prepare_confirmed_run(repository, owner)
    values = {
        "actor_scope_kind": _PARENT,
        "actor_scope_ref": owner,
        "run_id": run_id,
        "expected_revision": int(confirmed.body["revision"]),
        "expected_version": int(confirmed.resource_version),
        "key_sha256": _hash("cancel-duplicate:" + owner),
        "fingerprint_sha256": _hash("cancel-duplicate-fingerprint:" + owner),
    }
    initial = repository.cancel_run(**values)
    replay = repository.cancel_run(**values)
    assert initial.status_code == replay.status_code == 202
    assert replay.body == initial.body
    assert replay.resource_version == initial.resource_version
    assert replay.replayed is True
    with engine.connect() as connection:
        current = (
            connection.execute(
                select(tables.story_runs).where(tables.story_runs.c.run_id == run_id)
            )
            .mappings()
            .one()
        )
        cancel_receipts = connection.execute(
            select(tables.story_command_receipts.c.receipt_id).where(
                tables.story_command_receipts.c.resource_ref == run_id,
                tables.story_command_receipts.c.operation == "CANCEL_RUN",
            )
        ).all()
    assert current["version"] == initial.resource_version
    assert current["revision"] == initial.body["revision"]
    assert current["active_owner_parent_account_id"] is None
    assert len(cancel_receipts) == 1


@pytest.mark.parametrize("stale", ["version", "revision"])
def test_review_post_confirm_stale_cancel_does_not_release_active_owner(story_db, stale) -> None:
    engine, repository = story_db
    owner = "review-stale-close-" + str(uuid.uuid4())
    run_id, confirmed = _review_prepare_confirmed_run(repository, owner)
    canceled = repository.cancel_run(
        actor_scope_kind=_PARENT,
        actor_scope_ref=owner,
        run_id=run_id,
        expected_revision=int(confirmed.body["revision"]) - (stale == "revision"),
        expected_version=int(confirmed.resource_version) - (stale == "version"),
        key_sha256=_hash("stale-close:" + owner),
        fingerprint_sha256=_hash("stale-close-fingerprint:" + owner),
    )
    assert canceled.status_code == 409
    assert canceled.body["code"] == "STALE_REVISION"
    with engine.connect() as connection:
        row = (
            connection.execute(
                select(tables.story_runs).where(tables.story_runs.c.run_id == run_id)
            )
            .mappings()
            .one()
        )
    assert row["run_state"] == "PREPARATION_REVIEW"
    assert row["version"] == confirmed.resource_version
    assert row["active_owner_parent_account_id"] == owner
    blocked = repository.create_run(
        actor_scope_kind=_PARENT,
        actor_scope_ref=owner,
        profile_ref="synthetic-parent-demo",
        key_sha256=_hash("new-while-active:" + owner),
        fingerprint_sha256=_hash("new-while-active-fingerprint:" + owner),
    )
    assert blocked.status_code == 409
    assert blocked.body["code"] == "ACTIVE_RUN_EXISTS"
