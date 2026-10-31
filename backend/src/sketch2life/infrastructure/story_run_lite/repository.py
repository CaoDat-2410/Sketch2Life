"""PostgreSQL repositories for Story and Core-owned StoryRun-lite records."""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import uuid4

from sqlalchemy import Engine, Table, insert, select, text, update
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError

from sketch2life.application.ports.story_run_lite import (
    AdmittedAssetPair,
    AssetBinding,
    CommandResult,
    NormalizedImage,
    ScanVerdict,
    UploadReservation,
)
from sketch2life.domain.story_run_lite import (
    MAX_PART_BYTES,
    MAX_PARTS,
    MAX_UPLOAD_BYTES,
    OwnerScopeKind,
    ReceiptState,
    RunState,
    StoryRunLiteError,
    UploadState,
)
from sketch2life.infrastructure.persistence.core_models import CoreAssetMetadataModel
from sketch2life.infrastructure.story_run_lite import tables
from sketch2life.infrastructure.story_run_lite.quarantine import QuarantineError, QuarantineStore

_asset_metadata = cast(Table, CoreAssetMetadataModel.__table__)
_TECHNICAL_ORGANIZATION = "storyrun-lite-photo-bridge-v1"
_logger = logging.getLogger(__name__)


class SqlStoryRunLiteRepository:
    """Own Core upload records, Story run records, and receipt transactions separately."""

    def __init__(self, *, engine: Engine, quarantine: QuarantineStore) -> None:
        self._engine = engine
        self._quarantine = quarantine
        self._singleton_connection: Connection | None = None

    def acquire_singleton_lock(self) -> None:
        """Hold a process-scoped PostgreSQL advisory lock for the local one-instance demo."""

        if self._singleton_connection is not None:
            return
        connection = self._engine.connect()
        if connection.dialect.name != "postgresql":
            connection.close()
            raise RuntimeError(
                "StoryRun-lite requires PostgreSQL and a goal-owned disposable database"
            )
        connection.execute(
            text("SELECT pg_advisory_lock(hashtextextended(:scope, 0))"),
            {"scope": "storyrun-lite-singleton-v1"},
        )
        self._singleton_connection = connection

    def release_singleton_lock(self) -> None:
        connection = self._singleton_connection
        self._singleton_connection = None
        if connection is None:
            return
        try:
            connection.execute(
                text("SELECT pg_advisory_unlock(hashtextextended(:scope, 0))"),
                {"scope": "storyrun-lite-singleton-v1"},
            )
        finally:
            connection.close()

    def recover_after_restart(self) -> dict[str, int]:
        """Fence unfinished Core/Story dispatches after this process owns the singleton lock."""

        if self._singleton_connection is None:
            raise RuntimeError("singleton advisory lock must be acquired before recovery")
        counts = {
            "core_sessions_failed": 0,
            "core_receipts_finalized": 0,
            "core_sessions_expired": 0,
            "core_expired_cleanup_succeeded": 0,
            "core_expired_cleanup_failed": 0,
            "story_runs_held": 0,
            "story_receipts_finalized": 0,
        }
        now = datetime.now(UTC)
        expired_upload_ids: list[str] = []
        with self._engine.begin() as connection:
            core_rows = (
                connection.execute(
                    select(tables.upload_sessions)
                    .where(
                        tables.upload_sessions.c.state.in_(
                            [UploadState.PENDING.value, UploadState.PROCESSING.value]
                        )
                    )
                    .with_for_update()
                )
                .mappings()
                .all()
            )
            for row in core_rows:
                new_version = int(row["state_version"]) + 1
                connection.execute(
                    update(tables.upload_sessions)
                    .where(tables.upload_sessions.c.upload_session_id == row["upload_session_id"])
                    .values(
                        state=UploadState.FAILED.value,
                        state_version=new_version,
                        admission_gate_open=False,
                        claim_version=None,
                        error_code="UPLOAD_SESSION_STATE_CONFLICT",
                        updated_at=now,
                    )
                )
                counts["core_sessions_failed"] += 1
                receipts = (
                    connection.execute(
                        select(tables.upload_command_receipts)
                        .where(
                            tables.upload_command_receipts.c.resource_ref
                            == row["upload_session_id"],
                            tables.upload_command_receipts.c.operation == "COMPLETE_UPLOAD",
                            tables.upload_command_receipts.c.state == ReceiptState.PENDING.value,
                        )
                        .with_for_update()
                    )
                    .mappings()
                    .all()
                )
                for receipt in receipts:
                    body = _error_body(
                        "UPLOAD_SESSION_STATE_CONFLICT",
                        "The interrupted upload was failed; create a new upload session.",
                        retryable=False,
                    )
                    _finalize_receipt(
                        connection,
                        tables.upload_command_receipts,
                        receipt["receipt_id"],
                        409,
                        body,
                        new_version,
                        row["upload_session_id"],
                        new_version,
                        now,
                    )
                    counts["core_receipts_finalized"] += 1

            receiving_rows = (
                connection.execute(
                    select(tables.upload_sessions)
                    .where(tables.upload_sessions.c.state == UploadState.RECEIVING.value)
                    .order_by(tables.upload_sessions.c.upload_session_id)
                    .with_for_update()
                )
                .mappings()
                .all()
            )
            expiry_now = datetime.now(UTC)
            for row in receiving_rows:
                if not _is_expired(row, expiry_now):
                    continue
                new_version = int(row["state_version"]) + 1
                connection.execute(
                    update(tables.upload_sessions)
                    .where(
                        tables.upload_sessions.c.upload_session_id == row["upload_session_id"],
                        tables.upload_sessions.c.state == UploadState.RECEIVING.value,
                    )
                    .values(
                        state=UploadState.EXPIRED.value,
                        state_version=new_version,
                        admission_gate_open=False,
                        claim_version=None,
                        error_code="UPLOAD_EXPIRED",
                        updated_at=expiry_now,
                    )
                )
                counts["core_sessions_expired"] += 1

            expired_rows = (
                connection.execute(
                    select(tables.upload_sessions.c.upload_session_id)
                    .where(tables.upload_sessions.c.state == UploadState.EXPIRED.value)
                    .order_by(tables.upload_sessions.c.upload_session_id)
                    .with_for_update()
                )
                .all()
            )
            expired_upload_ids = [str(row[0]) for row in expired_rows]

            queued_runs = (
                connection.execute(
                    select(tables.story_runs)
                    .where(
                        tables.story_runs.c.job_state == "QUEUED",
                        tables.story_runs.c.run_state == RunState.INPUT_PROCESSING.value,
                    )
                    .with_for_update()
                )
                .mappings()
                .all()
            )
            for row in queued_runs:
                new_version = int(row["version"]) + 1
                connection.execute(
                    update(tables.story_runs)
                    .where(tables.story_runs.c.run_id == row["run_id"])
                    .values(
                        job_state="AWAITING_RECONCILIATION",
                        retryable=False,
                        action_required="OPERATOR_REVIEW",
                        error_code="VISION_ATTEMPT_HOLD",
                        dispatch_gate_open=False,
                        dispatch_claimed_version=None,
                        version=new_version,
                        updated_at=now,
                    )
                )
                counts["story_runs_held"] += 1
                pending_receipts = (
                    connection.execute(
                        select(tables.story_command_receipts)
                        .where(
                            tables.story_command_receipts.c.resource_ref == row["run_id"],
                            tables.story_command_receipts.c.operation == "ATTACH_ASSET",
                            tables.story_command_receipts.c.state == ReceiptState.PENDING.value,
                        )
                        .with_for_update()
                    )
                    .mappings()
                    .all()
                )
                for receipt in pending_receipts:
                    body = _error_body(
                        "VISION_ATTEMPT_HOLD",
                        "The interrupted attempt will not be redispatched; "
                        "cancel or request operator review.",
                        retryable=False,
                    )
                    _finalize_receipt(
                        connection,
                        tables.story_command_receipts,
                        receipt["receipt_id"],
                        409,
                        body,
                        new_version,
                        row["run_id"],
                        new_version,
                        now,
                    )
                    counts["story_receipts_finalized"] += 1
        for upload_id in expired_upload_ids:
            if self.remove_upload_quarantine(upload_id):
                counts["core_expired_cleanup_succeeded"] += 1
            else:
                counts["core_expired_cleanup_failed"] += 1
        return counts

    def authorize_upload_target(
        self, *, actor_scope_kind: OwnerScopeKind, actor_scope_ref: str, run_id: str
    ) -> bool:
        with self._engine.connect() as connection:
            row = connection.execute(
                select(tables.story_runs.c.run_id).where(
                    tables.story_runs.c.run_id == run_id,
                    tables.story_runs.c.actor_scope_kind == actor_scope_kind.value,
                    tables.story_runs.c.actor_scope_ref == actor_scope_ref,
                    tables.story_runs.c.run_state == RunState.INPUT_PROCESSING.value,
                )
            ).first()
        return row is not None

    def create_run(
        self,
        *,
        actor_scope_kind: OwnerScopeKind,
        actor_scope_ref: str,
        profile_ref: str,
        key_sha256: str,
        fingerprint_sha256: str,
    ) -> CommandResult:
        now = datetime.now(UTC)
        receipt_id = str(uuid4())
        run_id = str(uuid4())
        identity = _identity(
            actor_scope_kind,
            actor_scope_ref,
            "CREATE_RUN",
            "COLLECTION",
            "/v1/story-runs",
            key_sha256,
        )
        try:
            with self._engine.begin() as connection:
                _lock_identity(
                    connection, f"story:active:{actor_scope_kind.value}:{actor_scope_ref}"
                )
                _lock_identity(connection, "story:" + ":".join(identity.values()))
                existing = _existing_receipt(
                    connection, tables.story_command_receipts, identity, fingerprint_sha256
                )
                if existing is not None:
                    return existing
                connection.execute(
                    insert(tables.story_command_receipts).values(
                        receipt_id=receipt_id,
                        **identity,
                        request_fingerprint_sha256=fingerprint_sha256,
                        state=ReceiptState.PENDING.value,
                        state_version=1,
                        created_at=now,
                    )
                )
                if actor_scope_kind is OwnerScopeKind.PARENT_ACCOUNT:
                    active = connection.execute(
                        select(tables.story_runs.c.run_id)
                        .where(
                            tables.story_runs.c.active_owner_parent_account_id == actor_scope_ref
                        )
                        .with_for_update()
                    ).first()
                else:
                    active = connection.execute(
                        select(tables.story_runs.c.run_id)
                        .where(
                            tables.story_runs.c.actor_scope_kind == actor_scope_kind.value,
                            tables.story_runs.c.actor_scope_ref == actor_scope_ref,
                            tables.story_runs.c.active_owner_parent_account_id.is_not(None),
                        )
                        .with_for_update()
                    ).first()
                if active is not None:
                    body = _error_body(
                        "ACTIVE_RUN_EXISTS",
                        "This owner already has an unfinished StoryRun.",
                        retryable=False,
                    )
                    _finalize_receipt(
                        connection,
                        tables.story_command_receipts,
                        receipt_id,
                        409,
                        body,
                        None,
                        None,
                        None,
                        now,
                    )
                    return CommandResult(409, body, replayed=False)
                connection.execute(
                    insert(tables.story_runs).values(
                        run_id=run_id,
                        actor_scope_kind=actor_scope_kind.value,
                        actor_scope_ref=actor_scope_ref,
                        profile_ref=profile_ref,
                        run_state=RunState.INPUT_PROCESSING.value,
                        revision=1,
                        version=1,
                        retryable=False,
                        active_owner_parent_account_id=actor_scope_ref
                        if actor_scope_kind is OwnerScopeKind.PARENT_ACCOUNT
                        else None,
                        created_at=now,
                        updated_at=now,
                    )
                )
                row = (
                    connection.execute(
                        select(tables.story_runs).where(tables.story_runs.c.run_id == run_id)
                    )
                    .mappings()
                    .one()
                )
                body = _run_body(row)
                _finalize_receipt(
                    connection,
                    tables.story_command_receipts,
                    receipt_id,
                    201,
                    body,
                    1,
                    run_id,
                    1,
                    now,
                )
                return CommandResult(201, body, resource_version=1)
        except IntegrityError:
            # A competing run won the partial active-owner index. This transaction rolls back;
            # the stable owner lock normally prevents reaching this branch.
            raise StoryRunLiteError(
                409, "ACTIVE_RUN_EXISTS", "This owner already has an unfinished StoryRun."
            ) from None

    def create_upload(
        self,
        *,
        actor_scope_kind: OwnerScopeKind,
        actor_scope_ref: str,
        run_id: str,
        media_type: str,
        expected_size_bytes: int,
        expected_sha256: str,
        key_sha256: str,
        fingerprint_sha256: str,
    ) -> CommandResult:
        now = datetime.now(UTC)
        upload_id = str(uuid4())
        receipt_id = str(uuid4())
        identity = _identity(
            actor_scope_kind,
            actor_scope_ref,
            "CREATE_UPLOAD_SESSION",
            "COLLECTION",
            "/v1/upload-sessions",
            key_sha256,
        )
        with self._engine.begin() as connection:
            _lock_identity(connection, "core:" + ":".join(identity.values()))
            existing = _existing_receipt(
                connection, tables.upload_command_receipts, identity, fingerprint_sha256
            )
            if existing is not None:
                return existing
            run = self._owned_run(
                connection, actor_scope_kind, actor_scope_ref, run_id, lock=True
            )
            if run["run_state"] != RunState.INPUT_PROCESSING.value:
                raise StoryRunLiteError(404, "NOT_FOUND", "StoryRun is not accepting uploads.")
            connection.execute(
                insert(tables.upload_command_receipts).values(
                    receipt_id=receipt_id,
                    **identity,
                    request_fingerprint_sha256=fingerprint_sha256,
                    state=ReceiptState.PENDING.value,
                    state_version=1,
                    created_at=now,
                )
            )
            connection.execute(
                insert(tables.upload_sessions).values(
                    upload_session_id=upload_id,
                    actor_scope_kind=actor_scope_kind.value,
                    actor_scope_ref=actor_scope_ref,
                    target_kind="STORY_RUN",
                    target_ref=run_id,
                    purpose="RUN_ARTWORK",
                    expected_media_type=media_type,
                    expected_size_bytes=expected_size_bytes,
                    expected_sha256=expected_sha256,
                    part_size_bytes=MAX_PART_BYTES,
                    max_total_bytes=MAX_UPLOAD_BYTES,
                    max_parts=MAX_PARTS,
                    state=UploadState.RECEIVING.value,
                    state_version=1,
                    staging_key=upload_id,
                    admission_gate_open=False,
                    expires_at=now + timedelta(hours=2),
                    created_at=now,
                    updated_at=now,
                )
            )
            body = self._upload_body(connection, upload_id)
            _finalize_receipt(
                connection,
                tables.upload_command_receipts,
                receipt_id,
                201,
                body,
                1,
                upload_id,
                1,
                now,
            )
            return CommandResult(201, body, resource_version=1)

    def put_part(
        self,
        *,
        actor_scope_kind: OwnerScopeKind,
        actor_scope_ref: str,
        upload_id: str,
        part_number: int,
        payload: bytes,
        declared_length: int,
        declared_sha256: str,
    ) -> CommandResult:
        if declared_length != len(payload):
            raise StoryRunLiteError(
                400, "CONTENT_LENGTH_MISMATCH", "Content-Length must match the raw part bytes."
            )
        if not payload or len(payload) > MAX_PART_BYTES:
            raise StoryRunLiteError(413, "PART_TOO_LARGE", "The part exceeds part_size_bytes.")
        actual_sha256 = hashlib.sha256(payload).hexdigest()
        if actual_sha256 != declared_sha256.lower():
            raise StoryRunLiteError(
                422, "PART_HASH_MISMATCH", "Content-SHA256 does not match the part bytes."
            )
        if not 1 <= part_number <= MAX_PARTS:
            raise StoryRunLiteError(
                422, "INVALID_PART_NUMBER", "Part number must be within the advertised range."
            )
        expired = False
        replay: CommandResult | None = None
        result: CommandResult | None = None
        with self._engine.begin() as connection:
            run, row = self._owned_upload_with_run(
                connection, actor_scope_kind, actor_scope_ref, upload_id
            )
            now = datetime.now(UTC)
            if row["state"] == UploadState.EXPIRED.value or (
                row["state"] == UploadState.RECEIVING.value and _is_expired(row, now)
            ):
                if row["state"] == UploadState.RECEIVING.value:
                    new_version = int(row["state_version"]) + 1
                    connection.execute(
                        update(tables.upload_sessions)
                        .where(
                            tables.upload_sessions.c.upload_session_id == upload_id,
                            tables.upload_sessions.c.state == UploadState.RECEIVING.value,
                        )
                        .values(
                            state=UploadState.EXPIRED.value,
                            state_version=new_version,
                            admission_gate_open=False,
                            claim_version=None,
                            error_code="UPLOAD_EXPIRED",
                            updated_at=now,
                        )
                    )
                expired = True
            else:
                if row["state"] != UploadState.RECEIVING.value:
                    raise StoryRunLiteError(
                        409, "INVALID_STATE", "Upload session is not open for new parts."
                    )
                if run["run_state"] != RunState.INPUT_PROCESSING.value:
                    raise StoryRunLiteError(
                        409, "INVALID_STATE", "StoryRun is not accepting upload parts."
                    )
                existing = (
                    connection.execute(
                        select(tables.upload_parts)
                        .where(
                            tables.upload_parts.c.upload_session_id == upload_id,
                            tables.upload_parts.c.part_number == part_number,
                        )
                        .with_for_update()
                    )
                    .mappings()
                    .one_or_none()
                )
                if existing is not None:
                    if existing["sha256"] != actual_sha256 or int(existing["byte_size"]) != len(
                        payload
                    ):
                        raise StoryRunLiteError(
                            409,
                            "PART_CONFLICT",
                            "This part number already contains different bytes.",
                        )
                    replay = CommandResult(
                        200,
                        _part_body(part_number, len(payload), actual_sha256),
                        int(row["state_version"]),
                        True,
                    )
                else:
                    part_rows = connection.execute(
                        select(tables.upload_parts.c.part_number, tables.upload_parts.c.byte_size)
                        .where(tables.upload_parts.c.upload_session_id == upload_id)
                        .order_by(tables.upload_parts.c.part_number)
                    ).all()
                    expected_number = len(part_rows) + 1
                    if part_number != expected_number:
                        raise StoryRunLiteError(
                            422,
                            "UPLOAD_PART_GAP",
                            "Parts must be uploaded contiguously beginning at part one.",
                        )
                    already_received = sum(int(part.byte_size) for part in part_rows)
                    if already_received + len(payload) > int(row["expected_size_bytes"]):
                        raise StoryRunLiteError(
                            413, "IMAGE_TOO_LARGE", "Received parts exceed expected_size_bytes."
                        )
                    try:
                        storage_ref = self._quarantine.write_part(upload_id, part_number, payload)[
                            0
                        ]
                    except (OSError, QuarantineError):
                        raise StoryRunLiteError(
                            503,
                            "STAGING_UNAVAILABLE",
                            "The local quarantine could not store this part.",
                            retryable=True,
                        ) from None
                    connection.execute(
                        insert(tables.upload_parts).values(
                            upload_part_id=str(uuid4()),
                            upload_session_id=upload_id,
                            part_number=part_number,
                            byte_size=len(payload),
                            sha256=actual_sha256,
                            storage_object_ref=f"{upload_id}:{part_number}:{storage_ref}",
                            received_at=now,
                        )
                    )
                    result = CommandResult(
                        200,
                        _part_body(part_number, len(payload), actual_sha256),
                        int(row["state_version"]),
                    )
        if expired:
            self.remove_upload_quarantine(upload_id)
            raise StoryRunLiteError(410, "UPLOAD_EXPIRED", "Upload session has expired.")
        if replay is not None:
            return replay
        assert result is not None
        return result

    def reserve_complete_upload(
        self,
        *,
        actor_scope_kind: OwnerScopeKind,
        actor_scope_ref: str,
        upload_id: str,
        expected_size_bytes: int,
        expected_sha256: str,
        expected_version: int,
        key_sha256: str,
        fingerprint_sha256: str,
    ) -> UploadReservation:
        receipt_id = str(uuid4())
        expired_result: UploadReservation | None = None
        identity = _identity(
            actor_scope_kind,
            actor_scope_ref,
            "COMPLETE_UPLOAD",
            "UPLOAD_SESSION",
            upload_id,
            key_sha256,
        )
        with self._engine.begin() as connection:
            _lock_identity(connection, "core:" + ":".join(identity.values()))
            existing = _existing_receipt(
                connection, tables.upload_command_receipts, identity, fingerprint_sha256
            )
            if existing is not None:
                return UploadReservation(existing)
            run, row = self._owned_upload_with_run(
                connection, actor_scope_kind, actor_scope_ref, upload_id
            )
            now = datetime.now(UTC)
            connection.execute(
                insert(tables.upload_command_receipts).values(
                    receipt_id=receipt_id,
                    **identity,
                    request_fingerprint_sha256=fingerprint_sha256,
                    state=ReceiptState.PENDING.value,
                    state_version=1,
                    created_at=now,
                )
            )
            expired = row["state"] == UploadState.EXPIRED.value or (
                row["state"] == UploadState.RECEIVING.value and _is_expired(row, now)
            )
            if expired:
                expired_version = int(row["state_version"])
                if row["state"] == UploadState.RECEIVING.value:
                    expired_version += 1
                    connection.execute(
                        update(tables.upload_sessions)
                        .where(
                            tables.upload_sessions.c.upload_session_id == upload_id,
                            tables.upload_sessions.c.state == UploadState.RECEIVING.value,
                        )
                        .values(
                            state=UploadState.EXPIRED.value,
                            state_version=expired_version,
                            admission_gate_open=False,
                            claim_version=None,
                            error_code="UPLOAD_EXPIRED",
                            updated_at=now,
                        )
                    )
                body = _error_body(
                    "UPLOAD_EXPIRED", "Upload session has expired.", retryable=False
                )
                _finalize_receipt(
                    connection,
                    tables.upload_command_receipts,
                    receipt_id,
                    410,
                    body,
                    expired_version,
                    upload_id,
                    expired_version,
                    now,
                )
                expired_result = UploadReservation(
                    CommandResult(410, body, expired_version)
                )
            elif int(row["state_version"]) != expected_version:
                body = _error_body(
                    "STALE_REVISION",
                    "Upload resource changed; reload it and use the current ETag.",
                    retryable=False,
                )
                _finalize_receipt(
                    connection,
                    tables.upload_command_receipts,
                    receipt_id,
                    409,
                    body,
                    int(row["state_version"]),
                    upload_id,
                    int(row["state_version"]),
                    now,
                )
                return UploadReservation(CommandResult(409, body, int(row["state_version"])))
            elif run["run_state"] != RunState.INPUT_PROCESSING.value:
                body = _error_body(
                    "INVALID_STATE", "StoryRun is not accepting upload completion.", retryable=False
                )
                _finalize_receipt(
                    connection,
                    tables.upload_command_receipts,
                    receipt_id,
                    409,
                    body,
                    int(row["state_version"]),
                    upload_id,
                    int(row["state_version"]),
                    now,
                )
                return UploadReservation(CommandResult(409, body, int(row["state_version"])))
            elif row["state"] != UploadState.RECEIVING.value:
                body = _error_body(
                    "INVALID_STATE", "Upload session is not receiving parts.", retryable=False
                )
                _finalize_receipt(
                    connection,
                    tables.upload_command_receipts,
                    receipt_id,
                    409,
                    body,
                    int(row["state_version"]),
                    upload_id,
                    int(row["state_version"]),
                    now,
                )
                return UploadReservation(CommandResult(409, body, int(row["state_version"])))
            else:
                parts = (
                    connection.execute(
                        select(tables.upload_parts)
                        .where(tables.upload_parts.c.upload_session_id == upload_id)
                        .order_by(tables.upload_parts.c.part_number)
                    )
                    .mappings()
                    .all()
                )
                if not 1 <= len(parts) <= MAX_PARTS or [
                    int(part["part_number"]) for part in parts
                ] != list(range(1, len(parts) + 1)):
                    # The contract explicitly does not consume the key for an incomplete upload.
                    connection.execute(
                        tables.upload_command_receipts.delete().where(
                            tables.upload_command_receipts.c.receipt_id == receipt_id
                        )
                    )
                    raise StoryRunLiteError(
                        422,
                        "UPLOAD_INCOMPLETE",
                        "Upload parts must be contiguous and complete before admission.",
                    )
                if (
                    expected_size_bytes != int(row["expected_size_bytes"])
                    or expected_sha256 != row["expected_sha256"]
                ):
                    body = _error_body(
                        "UPLOAD_METADATA_MISMATCH",
                        "Complete metadata must match the upload session.",
                        retryable=False,
                    )
                    _finalize_receipt(
                        connection,
                        tables.upload_command_receipts,
                        receipt_id,
                        422,
                        body,
                        int(row["state_version"]),
                        upload_id,
                        int(row["state_version"]),
                        now,
                    )
                    return UploadReservation(CommandResult(422, body, int(row["state_version"])))
                next_version = int(row["state_version"]) + 1
                try:
                    _snapshot_path, snapshot = self._quarantine.assemble_snapshot(
                        upload_id,
                        [dict(part) for part in parts],
                        expected_size=expected_size_bytes,
                        expected_sha256=expected_sha256,
                    )
                except QuarantineError:
                    body = _error_body(
                        "UPLOAD_INCOMPLETE",
                        "Part bytes do not match the expected aggregate size and SHA-256.",
                        retryable=False,
                    )
                    _finalize_receipt(
                        connection,
                        tables.upload_command_receipts,
                        receipt_id,
                        422,
                        body,
                        int(row["state_version"]),
                        upload_id,
                        int(row["state_version"]),
                        now,
                    )
                    return UploadReservation(CommandResult(422, body, int(row["state_version"])))
                connection.execute(
                    update(tables.upload_sessions)
                    .where(
                        tables.upload_sessions.c.upload_session_id == upload_id,
                        tables.upload_sessions.c.state_version == expected_version,
                    )
                    .values(
                        state=UploadState.PENDING.value,
                        state_version=next_version,
                        claim_version=next_version,
                        aggregate_sha256=expected_sha256,
                        actual_size_bytes=expected_size_bytes,
                        updated_at=now,
                    )
                )
                connection.execute(
                    update(tables.upload_command_receipts)
                    .where(tables.upload_command_receipts.c.receipt_id == receipt_id)
                    .values(resource_ref=upload_id, resource_version=next_version)
                )
                return UploadReservation(
                    CommandResult(202, {}, next_version),
                    upload_id=upload_id,
                    claim_version=next_version,
                    snapshot=snapshot,
                    expected_sha256=expected_sha256,
                    original_media_type=str(row["expected_media_type"]),
                    actor_scope_ref=actor_scope_ref,
                )
        if expired_result is not None:
            self.remove_upload_quarantine(upload_id)
            return expired_result
        raise RuntimeError("complete upload reservation did not produce a result")

    def finalize_complete_upload(
        self, reservation: UploadReservation, *, key_sha256: str
    ) -> CommandResult:
        if reservation.upload_id is None or reservation.claim_version is None:
            return reservation.command_result
        now = datetime.now(UTC)
        with self._engine.begin() as connection:
            identity = (
                connection.execute(
                    select(
                        tables.upload_sessions.c.actor_scope_kind,
                        tables.upload_sessions.c.actor_scope_ref,
                    ).where(tables.upload_sessions.c.upload_session_id == reservation.upload_id)
                )
                .mappings()
                .one_or_none()
            )
            if identity is None:
                raise StoryRunLiteError(
                    409, "UPLOAD_SESSION_STATE_CONFLICT", "Upload session no longer exists."
                )
            run, row = self._owned_upload_with_run(
                connection,
                OwnerScopeKind(str(identity["actor_scope_kind"])),
                str(identity["actor_scope_ref"]),
                reservation.upload_id,
            )
            if (
                run["run_state"] != RunState.INPUT_PROCESSING.value
                or row["state"] != UploadState.PENDING.value
                or int(row["state_version"]) != reservation.claim_version
            ):
                raise StoryRunLiteError(
                    409,
                    "UPLOAD_SESSION_STATE_CONFLICT",
                    "Upload state changed before the completion receipt finalized.",
                )
            receipt = (
                connection.execute(
                    select(tables.upload_command_receipts)
                    .where(
                        tables.upload_command_receipts.c.resource_ref == reservation.upload_id,
                        tables.upload_command_receipts.c.operation == "COMPLETE_UPLOAD",
                        tables.upload_command_receipts.c.idempotency_key_sha256 == key_sha256,
                    )
                    .with_for_update()
                )
                .mappings()
                .one()
            )
            body = self._upload_body(connection, reservation.upload_id)
            _finalize_receipt(
                connection,
                tables.upload_command_receipts,
                receipt["receipt_id"],
                202,
                body,
                reservation.claim_version,
                reservation.upload_id,
                reservation.claim_version,
                now,
            )
            return CommandResult(202, body, reservation.claim_version)

    def open_upload_gate(self, *, upload_id: str, claim_version: int) -> bool:
        now = datetime.now(UTC)
        with self._engine.begin() as connection:
            identity = (
                connection.execute(
                    select(
                        tables.upload_sessions.c.actor_scope_kind,
                        tables.upload_sessions.c.actor_scope_ref,
                    ).where(tables.upload_sessions.c.upload_session_id == upload_id)
                )
                .mappings()
                .one_or_none()
            )
            if identity is None:
                return False
            run, row = self._owned_upload_with_run(
                connection,
                OwnerScopeKind(str(identity["actor_scope_kind"])),
                str(identity["actor_scope_ref"]),
                upload_id,
            )
            if (
                run["run_state"] != RunState.INPUT_PROCESSING.value
                or row["state"] != UploadState.PENDING.value
                or int(row["state_version"]) != claim_version
                or row["admission_gate_open"]
            ):
                return False
            receipt = connection.execute(
                select(tables.upload_command_receipts.c.receipt_id)
                .where(
                    tables.upload_command_receipts.c.resource_ref == upload_id,
                    tables.upload_command_receipts.c.operation == "COMPLETE_UPLOAD",
                    tables.upload_command_receipts.c.state == ReceiptState.FINAL.value,
                    tables.upload_command_receipts.c.response_status == 202,
                )
                .with_for_update()
            ).first()
            if receipt is None:
                return False
            changed = connection.execute(
                update(tables.upload_sessions)
                .where(
                    tables.upload_sessions.c.upload_session_id == upload_id,
                    tables.upload_sessions.c.state == UploadState.PENDING.value,
                    tables.upload_sessions.c.state_version == claim_version,
                    tables.upload_sessions.c.admission_gate_open.is_(False),
                )
                .values(
                    state=UploadState.PROCESSING.value,
                    state_version=claim_version + 1,
                    admission_gate_open=True,
                    updated_at=now,
                )
            )
            return changed.rowcount == 1

    def finish_upload_admission(
        self,
        *,
        upload_id: str,
        claim_version: int,
        original_asset_ref: str,
        derived_asset_ref: str,
        normalized: NormalizedImage,
        scanner: ScanVerdict,
        actor_scope_ref: str,
    ) -> bool:
        now = datetime.now(UTC)
        original_asset = {
            "asset_ref": original_asset_ref,
            "asset_version": 1,
            "organization_id": None,
            "owner_scope_kind": OwnerScopeKind.PARENT_ACCOUNT.value,
            "owner_scope_ref": actor_scope_ref,
            "content_sha256": normalized.original_sha256,
            "media_type": normalized.original_media_type,
            "source_refs": [],
            "derived_from_ref": None,
            "created_at": now,
        }
        derived_asset = {
            "asset_ref": derived_asset_ref,
            "asset_version": 1,
            "organization_id": None,
            "owner_scope_kind": OwnerScopeKind.PARENT_ACCOUNT.value,
            "owner_scope_ref": actor_scope_ref,
            "content_sha256": normalized.derived_sha256,
            "media_type": normalized.derived_media_type,
            "source_refs": [],
            "derived_from_ref": original_asset_ref,
            "created_at": now,
        }
        with self._engine.begin() as connection:
            identity = (
                connection.execute(
                    select(
                        tables.upload_sessions.c.actor_scope_kind,
                        tables.upload_sessions.c.actor_scope_ref,
                    ).where(tables.upload_sessions.c.upload_session_id == upload_id)
                )
                .mappings()
                .one_or_none()
            )
            if identity is None:
                return False
            run, row = self._owned_upload_with_run(
                connection,
                OwnerScopeKind(str(identity["actor_scope_kind"])),
                str(actor_scope_ref),
                upload_id,
            )
            if (
                identity["actor_scope_ref"] != actor_scope_ref
                or run["run_state"] != RunState.INPUT_PROCESSING.value
                or row["state"] != UploadState.PROCESSING.value
                or not row["admission_gate_open"]
                or row["claim_version"] != claim_version
            ):
                return False
            connection.execute(insert(_asset_metadata).values(**original_asset))
            connection.execute(insert(_asset_metadata).values(**derived_asset))
            connection.execute(
                insert(tables.asset_lineage).values(
                    lineage_id=str(uuid4()),
                    source_asset_ref=original_asset_ref,
                    source_asset_version=1,
                    derived_asset_ref=derived_asset_ref,
                    derived_asset_version=1,
                    source_sha256=normalized.original_sha256,
                    derived_sha256=normalized.derived_sha256,
                    source_size_bytes=normalized.original_size_bytes,
                    derived_size_bytes=normalized.derived_size_bytes,
                    transform_kind="STORYRUN_V2_JPEG_NORMALIZE",
                    transform_version="1",
                    scanner_name="ClamAV",
                    scanner_version=scanner.scanner_version or "unknown",
                    scanner_sha256=scanner.sha256,
                    created_at=now,
                )
            )
            changed = connection.execute(
                update(tables.upload_sessions)
                .where(
                    tables.upload_sessions.c.upload_session_id == upload_id,
                    tables.upload_sessions.c.state == UploadState.PROCESSING.value,
                    tables.upload_sessions.c.claim_version == claim_version,
                    tables.upload_sessions.c.admission_gate_open.is_(True),
                )
                .values(
                    state=UploadState.READY.value,
                    state_version=int(row["state_version"]) + 1,
                    asset_ref=original_asset_ref,
                    asset_version=1,
                    derived_asset_ref=derived_asset_ref,
                    derived_asset_version=1,
                    updated_at=now,
                )
            )
            if changed.rowcount != 1:
                raise RuntimeError("upload admission lost its locked state before commit")
            return True

    def fail_upload_admission(self, *, upload_id: str, claim_version: int, error_code: str) -> bool:
        with self._engine.begin() as connection:
            row = (
                connection.execute(
                    select(tables.upload_sessions)
                    .where(tables.upload_sessions.c.upload_session_id == upload_id)
                    .with_for_update()
                )
                .mappings()
                .one_or_none()
            )
            if (
                row is None
                or row["claim_version"] != claim_version
                or row["state"] not in {UploadState.PENDING.value, UploadState.PROCESSING.value}
            ):
                return False
            changed = connection.execute(
                update(tables.upload_sessions)
                .where(
                    tables.upload_sessions.c.upload_session_id == upload_id,
                    tables.upload_sessions.c.claim_version == claim_version,
                )
                .values(
                    state=UploadState.FAILED.value,
                    state_version=int(row["state_version"]) + 1,
                    error_code=error_code,
                    admission_gate_open=False,
                    updated_at=datetime.now(UTC),
                )
            )
            return changed.rowcount == 1

    def get_upload(
        self, *, actor_scope_kind: OwnerScopeKind, actor_scope_ref: str, upload_id: str
    ) -> CommandResult:
        expired = False
        result: CommandResult | None = None
        with self._engine.begin() as connection:
            _run, row = self._owned_upload_with_run(
                connection, actor_scope_kind, actor_scope_ref, upload_id
            )
            now = datetime.now(UTC)
            if row["state"] == UploadState.EXPIRED.value:
                expired = True
            elif row["state"] == UploadState.RECEIVING.value and _is_expired(row, now):
                new_version = int(row["state_version"]) + 1
                connection.execute(
                    update(tables.upload_sessions)
                    .where(
                        tables.upload_sessions.c.upload_session_id == upload_id,
                        tables.upload_sessions.c.state == UploadState.RECEIVING.value,
                    )
                    .values(
                        state=UploadState.EXPIRED.value,
                        state_version=new_version,
                        admission_gate_open=False,
                        claim_version=None,
                        error_code="UPLOAD_EXPIRED",
                        updated_at=now,
                    )
                )
                expired = True
            else:
                body = self._upload_body(connection, upload_id, row=row)
                result = CommandResult(200, body, int(row["state_version"]))
        if expired:
            self.remove_upload_quarantine(upload_id)
            raise StoryRunLiteError(410, "UPLOAD_EXPIRED", "Upload session has expired.")
        assert result is not None
        return result

    def abort_upload(
        self,
        *,
        actor_scope_kind: OwnerScopeKind,
        actor_scope_ref: str,
        upload_id: str,
        expected_version: int,
        key_sha256: str,
        fingerprint_sha256: str,
    ) -> CommandResult:
        now = datetime.now(UTC)
        receipt_id = str(uuid4())
        identity = _identity(
            actor_scope_kind,
            actor_scope_ref,
            "ABORT_UPLOAD",
            "UPLOAD_SESSION",
            upload_id,
            key_sha256,
        )
        with self._engine.begin() as connection:
            _lock_identity(connection, "core:" + ":".join(identity.values()))
            existing = _existing_receipt(
                connection, tables.upload_command_receipts, identity, fingerprint_sha256
            )
            if existing is not None:
                return existing
            _run, row = self._owned_upload_with_run(
                connection, actor_scope_kind, actor_scope_ref, upload_id
            )
            connection.execute(
                insert(tables.upload_command_receipts).values(
                    receipt_id=receipt_id,
                    **identity,
                    request_fingerprint_sha256=fingerprint_sha256,
                    state=ReceiptState.PENDING.value,
                    state_version=1,
                    created_at=now,
                )
            )
            if int(row["state_version"]) != expected_version:
                body = _error_body(
                    "STALE_REVISION",
                    "Upload resource changed; reload it and use the current ETag.",
                    retryable=False,
                )
                _finalize_receipt(
                    connection,
                    tables.upload_command_receipts,
                    receipt_id,
                    409,
                    body,
                    int(row["state_version"]),
                    upload_id,
                    int(row["state_version"]),
                    now,
                )
                return CommandResult(409, body, int(row["state_version"]))
            if row["state"] != UploadState.RECEIVING.value:
                body = _error_body(
                    "INVALID_STATE", "Only a receiving upload can be aborted.", retryable=False
                )
                _finalize_receipt(
                    connection,
                    tables.upload_command_receipts,
                    receipt_id,
                    409,
                    body,
                    int(row["state_version"]),
                    upload_id,
                    int(row["state_version"]),
                    now,
                )
                return CommandResult(409, body, int(row["state_version"]))
            new_version = int(row["state_version"]) + 1
            connection.execute(
                update(tables.upload_sessions)
                .where(tables.upload_sessions.c.upload_session_id == upload_id)
                .values(
                    state=UploadState.ABORTED.value,
                    state_version=new_version,
                    admission_gate_open=False,
                    claim_version=None,
                    updated_at=now,
                )
            )
            body = self._upload_body(connection, upload_id)
            _finalize_receipt(
                connection,
                tables.upload_command_receipts,
                receipt_id,
                202,
                body,
                new_version,
                upload_id,
                new_version,
                now,
            )
        self.remove_upload_quarantine(upload_id)
        return CommandResult(202, body, new_version)

    def resolve_story_artwork(
        self,
        *,
        actor_scope_kind: OwnerScopeKind,
        actor_scope_ref: str,
        asset_ref: str,
        run_id: str,
    ) -> AdmittedAssetPair:
        with self._engine.connect() as connection:
            upload = (
                connection.execute(
                    select(tables.upload_sessions).where(
                        tables.upload_sessions.c.asset_ref == asset_ref,
                        tables.upload_sessions.c.target_ref == run_id,
                        tables.upload_sessions.c.actor_scope_kind == actor_scope_kind.value,
                        tables.upload_sessions.c.actor_scope_ref == actor_scope_ref,
                        tables.upload_sessions.c.state == UploadState.READY.value,
                    )
                )
                .mappings()
                .one_or_none()
            )
            if upload is None or not upload["derived_asset_ref"]:
                raise StoryRunLiteError(
                    404, "NOT_FOUND", "Admitted artwork was not found in this Parent scope."
                )
            original = self._asset_binding(
                connection,
                asset_ref,
                int(upload["asset_version"]),
                actor_scope_kind,
                actor_scope_ref,
            )
            derived = self._asset_binding(
                connection,
                str(upload["derived_asset_ref"]),
                int(upload["derived_asset_version"]),
                actor_scope_kind,
                actor_scope_ref,
            )
        return AdmittedAssetPair(
            original, derived, str(upload["upload_session_id"]), str(upload["target_ref"])
        )

    def attach_asset(
        self,
        *,
        actor_scope_kind: OwnerScopeKind,
        actor_scope_ref: str,
        run_id: str,
        pair: AdmittedAssetPair,
        expected_revision: int,
        expected_version: int,
        key_sha256: str,
        fingerprint_sha256: str,
    ) -> tuple[CommandResult, str | None, int | None]:
        now = datetime.now(UTC)
        receipt_id = str(uuid4())
        identity = _identity(
            actor_scope_kind, actor_scope_ref, "ATTACH_ASSET", "STORY_RUN", run_id, key_sha256
        )
        with self._engine.begin() as connection:
            _lock_identity(connection, "story:" + ":".join(identity.values()))
            existing = _existing_receipt(
                connection, tables.story_command_receipts, identity, fingerprint_sha256
            )
            if existing is not None:
                return existing, None, None
            row = self._owned_run(connection, actor_scope_kind, actor_scope_ref, run_id, lock=True)
            connection.execute(
                insert(tables.story_command_receipts).values(
                    receipt_id=receipt_id,
                    **identity,
                    request_fingerprint_sha256=fingerprint_sha256,
                    state=ReceiptState.PENDING.value,
                    state_version=1,
                    created_at=now,
                )
            )
            if int(row["version"]) != expected_version or int(row["revision"]) != expected_revision:
                body = _error_body(
                    "STALE_REVISION",
                    "StoryRun changed; reload it and use the current revision and ETag.",
                    retryable=False,
                )
                _finalize_receipt(
                    connection,
                    tables.story_command_receipts,
                    receipt_id,
                    409,
                    body,
                    int(row["version"]),
                    run_id,
                    int(row["version"]),
                    now,
                )
                return CommandResult(409, body, int(row["version"])), None, None
            if row["run_state"] != RunState.INPUT_PROCESSING.value or row["asset_ref"] is not None:
                body = _error_body(
                    "INVALID_STATE",
                    "StoryRun is not ready for an artwork attachment.",
                    retryable=False,
                )
                _finalize_receipt(
                    connection,
                    tables.story_command_receipts,
                    receipt_id,
                    409,
                    body,
                    int(row["version"]),
                    run_id,
                    int(row["version"]),
                    now,
                )
                return CommandResult(409, body, int(row["version"])), None, None
            if (
                pair.target_run_id != run_id
                or pair.original.owner_scope_ref != actor_scope_ref
                or pair.derived.owner_scope_ref != actor_scope_ref
            ):
                body = _error_body(
                    "ASSET_SCOPE_MISMATCH",
                    "Artwork ownership or StoryRun binding does not match.",
                    retryable=False,
                )
                _finalize_receipt(
                    connection,
                    tables.story_command_receipts,
                    receipt_id,
                    409,
                    body,
                    int(row["version"]),
                    run_id,
                    int(row["version"]),
                    now,
                )
                return CommandResult(409, body, int(row["version"])), None, None
            input_id = str(uuid4())
            next_revision = int(row["revision"]) + 1
            next_version = int(row["version"]) + 1
            claimed_version = next_version
            connection.execute(
                insert(tables.run_inputs).values(
                    run_input_id=input_id,
                    run_id=run_id,
                    input_revision=1,
                    original_asset_ref=pair.original.asset_ref,
                    original_asset_version=pair.original.asset_version,
                    original_sha256=pair.original.sha256,
                    original_media_type=pair.original.media_type,
                    original_size_bytes=pair.original.byte_size,
                    derived_asset_ref=pair.derived.asset_ref,
                    derived_asset_version=pair.derived.asset_version,
                    derived_sha256=pair.derived.sha256,
                    derived_media_type=pair.derived.media_type,
                    derived_size_bytes=pair.derived.byte_size,
                    created_at=now,
                )
            )
            connection.execute(
                update(tables.story_runs)
                .where(
                    tables.story_runs.c.run_id == run_id,
                    tables.story_runs.c.version == expected_version,
                )
                .values(
                    asset_ref=pair.original.asset_ref,
                    derived_asset_ref=pair.derived.asset_ref,
                    run_state=RunState.INPUT_PROCESSING.value,
                    revision=next_revision,
                    version=next_version,
                    job_state="QUEUED",
                    retryable=False,
                    action_required=None,
                    dispatch_gate_open=False,
                    dispatch_claimed_version=claimed_version,
                    provider_job_id=str(uuid4()),
                    provider_attempt_id=str(uuid4()),
                    updated_at=now,
                )
            )
            connection.execute(
                update(tables.story_command_receipts)
                .where(tables.story_command_receipts.c.receipt_id == receipt_id)
                .values(resource_ref=run_id, resource_version=next_version)
            )
            updated = (
                connection.execute(
                    select(tables.story_runs).where(tables.story_runs.c.run_id == run_id)
                )
                .mappings()
                .one()
            )
            body = _run_body(updated)
            return (
                CommandResult(202, body, next_version),
                str(updated["provider_job_id"]),
                claimed_version,
            )

    def finalize_attach_command(
        self, *, run_id: str, key_sha256: str, claimed_version: int
    ) -> CommandResult:
        """Commit the attach 202 snapshot before opening its separate dispatch gate."""

        now = datetime.now(UTC)
        with self._engine.begin() as connection:
            row = (
                connection.execute(
                    select(tables.story_runs)
                    .where(
                        tables.story_runs.c.run_id == run_id,
                        tables.story_runs.c.dispatch_claimed_version == claimed_version,
                        tables.story_runs.c.job_state == "QUEUED",
                    )
                    .with_for_update()
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                raise StoryRunLiteError(
                    409,
                    "VISION_ATTEMPT_HOLD",
                    "The attach reservation changed before its receipt finalized.",
                )
            receipt = (
                connection.execute(
                    select(tables.story_command_receipts)
                    .where(
                        tables.story_command_receipts.c.resource_ref == run_id,
                        tables.story_command_receipts.c.operation == "ATTACH_ASSET",
                        tables.story_command_receipts.c.idempotency_key_sha256 == key_sha256,
                        tables.story_command_receipts.c.state == ReceiptState.PENDING.value,
                    )
                    .with_for_update()
                )
                .mappings()
                .one()
            )
            body = _run_body(row)
            version = int(row["version"])
            _finalize_receipt(
                connection,
                tables.story_command_receipts,
                receipt["receipt_id"],
                202,
                body,
                version,
                run_id,
                version,
                now,
            )
            return CommandResult(202, body, version)

    def open_story_dispatch_gate(self, *, run_id: str, claimed_version: int) -> bool:
        with self._engine.begin() as connection:
            receipt = connection.execute(
                select(tables.story_command_receipts.c.receipt_id)
                .where(
                    tables.story_command_receipts.c.resource_ref == run_id,
                    tables.story_command_receipts.c.operation == "ATTACH_ASSET",
                    tables.story_command_receipts.c.state == ReceiptState.FINAL.value,
                    tables.story_command_receipts.c.response_status == 202,
                )
                .with_for_update()
            ).first()
            if receipt is None:
                return False
            result = connection.execute(
                update(tables.story_runs)
                .where(
                    tables.story_runs.c.run_id == run_id,
                    tables.story_runs.c.dispatch_claimed_version == claimed_version,
                    tables.story_runs.c.dispatch_gate_open.is_(False),
                    tables.story_runs.c.job_state == "QUEUED",
                    tables.story_runs.c.run_state == RunState.INPUT_PROCESSING.value,
                )
                .values(
                    dispatch_gate_open=True,
                    version=tables.story_runs.c.version + 1,
                    updated_at=datetime.now(UTC),
                )
            )
            return result.rowcount == 1

    def get_dispatch_context(self, *, run_id: str) -> dict[str, object]:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(tables.story_runs).where(tables.story_runs.c.run_id == run_id)
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                raise StoryRunLiteError(404, "NOT_FOUND", "StoryRun not found.")
            input_row = (
                connection.execute(
                    select(tables.run_inputs)
                    .where(tables.run_inputs.c.run_id == run_id)
                    .order_by(tables.run_inputs.c.input_revision.desc())
                    .limit(1)
                )
                .mappings()
                .one_or_none()
            )
        if input_row is None:
            raise StoryRunLiteError(409, "INVALID_STATE", "StoryRun has no admitted artwork.")
        return {
            "run_id": str(row["run_id"]),
            "actor_scope_kind": str(row["actor_scope_kind"]),
            "actor_scope_ref": str(row["actor_scope_ref"]),
            "provider_job_id": str(row["provider_job_id"]),
            "provider_attempt_id": str(row["provider_attempt_id"]),
            "dispatch_claimed_version": int(row["dispatch_claimed_version"]),
            "original_asset_ref": str(input_row["original_asset_ref"]),
            "original_sha256": str(input_row["original_sha256"]),
            "derived_asset_ref": str(input_row["derived_asset_ref"]),
            "derived_sha256": str(input_row["derived_sha256"]),
            "derived_media_type": str(input_row["derived_media_type"]),
        }

    def pending_vision_ledger_reconciliation(self) -> list[dict[str, object]]:
        """Return only already-committed Story results that may need A1 terminalization."""

        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    select(
                        tables.story_runs.c.run_id,
                        tables.story_runs.c.provider_job_id,
                        tables.story_runs.c.provider_attempt_id,
                        tables.story_runs.c.raw_body_sha256,
                    ).where(
                        tables.story_runs.c.run_state == RunState.SUBJECT_REVIEW.value,
                        tables.story_runs.c.raw_body_sha256.is_not(None),
                        tables.story_runs.c.provider_job_id.is_not(None),
                        tables.story_runs.c.provider_attempt_id.is_not(None),
                    )
                )
                .mappings()
                .all()
            )
        return [dict(row) for row in rows]

    def commit_vision_success(
        self,
        *,
        run_id: str,
        claimed_version: int,
        result_snapshot: dict[str, object],
        subject_label: str,
        confidence: float,
        canonical_result_sha256: str,
        raw_body_sha256: str | None,
    ) -> bool:
        now = datetime.now(UTC)
        with self._engine.begin() as connection:
            row = (
                connection.execute(
                    select(tables.story_runs)
                    .where(tables.story_runs.c.run_id == run_id)
                    .with_for_update()
                )
                .mappings()
                .one_or_none()
            )
            if (
                row is None
                or row["run_state"] != RunState.INPUT_PROCESSING.value
                or row["job_state"] != "QUEUED"
                or not row["dispatch_gate_open"]
                or int(row["dispatch_claimed_version"] or 0) != claimed_version
            ):
                return False
            input_row = (
                connection.execute(
                    select(tables.run_inputs)
                    .where(tables.run_inputs.c.run_id == run_id)
                    .order_by(tables.run_inputs.c.input_revision.desc())
                    .limit(1)
                )
                .mappings()
                .one()
            )
            revision = 1
            connection.execute(
                insert(tables.understanding_revisions).values(
                    understanding_revision_id=str(uuid4()),
                    run_id=run_id,
                    run_input_id=input_row["run_input_id"],
                    revision_no=revision,
                    subject_label=subject_label[:256],
                    confidence=confidence,
                    canonical_result_sha256=canonical_result_sha256,
                    raw_body_sha256=raw_body_sha256,
                    result_snapshot=result_snapshot,
                    created_at=now,
                )
            )
            changed = connection.execute(
                update(tables.story_runs)
                .where(
                    tables.story_runs.c.run_id == run_id,
                    tables.story_runs.c.dispatch_claimed_version == claimed_version,
                    tables.story_runs.c.dispatch_gate_open.is_(True),
                )
                .values(
                    run_state=RunState.SUBJECT_REVIEW.value,
                    revision=tables.story_runs.c.revision + 1,
                    version=tables.story_runs.c.version + 1,
                    job_state="SUCCEEDED",
                    retryable=False,
                    action_required=None,
                    dispatch_gate_open=False,
                    dispatch_claimed_version=None,
                    understanding_revision=revision,
                    subject_label=subject_label[:256],
                    confidence=confidence,
                    result_sha256=canonical_result_sha256,
                    raw_body_sha256=raw_body_sha256,
                    error_code=None,
                    updated_at=now,
                )
            )
            if changed.rowcount != 1:
                raise RuntimeError("StoryRun result lost its locked dispatch claim before commit")
            return True

    def mark_vision_unknown(self, *, run_id: str, claimed_version: int, error_code: str) -> bool:
        now = datetime.now(UTC)
        with self._engine.begin() as connection:
            row = (
                connection.execute(
                    select(tables.story_runs)
                    .where(tables.story_runs.c.run_id == run_id)
                    .with_for_update()
                )
                .mappings()
                .one_or_none()
            )
            if (
                row is None
                or row["run_state"] == RunState.DELETE_PENDING.value
                or int(row["dispatch_claimed_version"] or 0) != claimed_version
            ):
                return False
            result = connection.execute(
                update(tables.story_runs)
                .where(
                    tables.story_runs.c.run_id == run_id,
                    tables.story_runs.c.dispatch_claimed_version == claimed_version,
                )
                .values(
                    job_state="AWAITING_RECONCILIATION",
                    retryable=False,
                    action_required="OPERATOR_REVIEW",
                    error_code=error_code,
                    dispatch_gate_open=False,
                    version=tables.story_runs.c.version + 1,
                    updated_at=now,
                )
            )
            return result.rowcount == 1

    def mark_vision_failed_before_send(
        self, *, run_id: str, claimed_version: int, error_code: str
    ) -> bool:
        now = datetime.now(UTC)
        with self._engine.begin() as connection:
            row = (
                connection.execute(
                    select(tables.story_runs)
                    .where(tables.story_runs.c.run_id == run_id)
                    .with_for_update()
                )
                .mappings()
                .one_or_none()
            )
            if (
                row is None
                or row["run_state"] == RunState.DELETE_PENDING.value
                or int(row["dispatch_claimed_version"] or 0) != claimed_version
            ):
                return False
            result = connection.execute(
                update(tables.story_runs)
                .where(
                    tables.story_runs.c.run_id == run_id,
                    tables.story_runs.c.dispatch_claimed_version == claimed_version,
                )
                .values(
                    run_state=RunState.FAILED.value,
                    job_state="FAILED",
                    retryable=False,
                    action_required=None,
                    error_code=error_code,
                    active_owner_parent_account_id=None,
                    dispatch_gate_open=False,
                    version=tables.story_runs.c.version + 1,
                    revision=tables.story_runs.c.revision + 1,
                    updated_at=now,
                )
            )
            return result.rowcount == 1

    def get_run(
        self, *, actor_scope_kind: OwnerScopeKind, actor_scope_ref: str, run_id: str
    ) -> CommandResult:
        with self._engine.connect() as connection:
            row = self._owned_run(connection, actor_scope_kind, actor_scope_ref, run_id)
        return CommandResult(200, _run_body(row), int(row["version"]))

    def confirm_subject(
        self,
        *,
        actor_scope_kind: OwnerScopeKind,
        actor_scope_ref: str,
        run_id: str,
        expected_version: int,
        expected_understanding_revision: int,
        key_sha256: str,
        fingerprint_sha256: str,
    ) -> CommandResult:
        now = datetime.now(UTC)
        receipt_id = str(uuid4())
        identity = _identity(
            actor_scope_kind, actor_scope_ref, "CONFIRM_SUBJECT", "STORY_RUN", run_id, key_sha256
        )
        with self._engine.begin() as connection:
            _lock_identity(connection, "story:" + ":".join(identity.values()))
            existing = _existing_receipt(
                connection, tables.story_command_receipts, identity, fingerprint_sha256
            )
            if existing is not None:
                return existing
            row = self._owned_run(connection, actor_scope_kind, actor_scope_ref, run_id, lock=True)
            connection.execute(
                insert(tables.story_command_receipts).values(
                    receipt_id=receipt_id,
                    **identity,
                    request_fingerprint_sha256=fingerprint_sha256,
                    state=ReceiptState.PENDING.value,
                    state_version=1,
                    created_at=now,
                )
            )
            if (
                row["run_state"] != RunState.SUBJECT_REVIEW.value
                or int(row["version"]) != expected_version
                or int(row["understanding_revision"] or 0) != expected_understanding_revision
            ):
                body = _error_body(
                    "STALE_REVISION",
                    "The current subject understanding changed; reload it before confirming.",
                    retryable=False,
                )
                _finalize_receipt(
                    connection,
                    tables.story_command_receipts,
                    receipt_id,
                    409,
                    body,
                    int(row["version"]),
                    run_id,
                    int(row["version"]),
                    now,
                )
                return CommandResult(409, body, int(row["version"]))
            new_revision = int(row["revision"]) + 1
            new_version = int(row["version"]) + 1
            connection.execute(
                update(tables.story_runs)
                .where(
                    tables.story_runs.c.run_id == run_id,
                    tables.story_runs.c.understanding_revision == expected_understanding_revision,
                )
                .values(
                    run_state=RunState.PREPARATION_REVIEW.value,
                    revision=new_revision,
                    version=new_version,
                    updated_at=now,
                )
            )
            connection.execute(
                insert(tables.review_decisions).values(
                    decision_id=str(uuid4()),
                    run_id=run_id,
                    command_receipt_id=receipt_id,
                    stage="SUBJECT",
                    decision="CONFIRM",
                    actor_scope_kind=actor_scope_kind.value,
                    actor_scope_ref=actor_scope_ref,
                    target_understanding_revision=expected_understanding_revision,
                    created_at=now,
                )
            )
            body = _run_body(
                connection.execute(
                    select(tables.story_runs).where(tables.story_runs.c.run_id == run_id)
                )
                .mappings()
                .one()
            )
            _finalize_receipt(
                connection,
                tables.story_command_receipts,
                receipt_id,
                202,
                body,
                new_version,
                run_id,
                new_version,
                now,
            )
            return CommandResult(202, body, new_version)

    def cancel_run(
        self,
        *,
        actor_scope_kind: OwnerScopeKind,
        actor_scope_ref: str,
        run_id: str,
        expected_revision: int,
        expected_version: int,
        key_sha256: str,
        fingerprint_sha256: str,
    ) -> CommandResult:
        now = datetime.now(UTC)
        cleanup_upload_ids: list[str] = []
        result: CommandResult | None = None
        receipt_id = str(uuid4())
        identity = _identity(
            actor_scope_kind, actor_scope_ref, "CANCEL_RUN", "STORY_RUN", run_id, key_sha256
        )
        with self._engine.begin() as connection:
            _lock_identity(connection, "story:" + ":".join(identity.values()))
            existing = _existing_receipt(
                connection, tables.story_command_receipts, identity, fingerprint_sha256
            )
            if existing is not None:
                return existing
            row = self._owned_run(connection, actor_scope_kind, actor_scope_ref, run_id, lock=True)
            connection.execute(
                insert(tables.story_command_receipts).values(
                    receipt_id=receipt_id,
                    **identity,
                    request_fingerprint_sha256=fingerprint_sha256,
                    state=ReceiptState.PENDING.value,
                    state_version=1,
                    created_at=now,
                )
            )
            if int(row["version"]) != expected_version or int(row["revision"]) != expected_revision:
                body = _error_body(
                    "STALE_REVISION",
                    "StoryRun changed; reload it and use the current revision and ETag.",
                    retryable=False,
                )
                _finalize_receipt(
                    connection,
                    tables.story_command_receipts,
                    receipt_id,
                    409,
                    body,
                    int(row["version"]),
                    run_id,
                    int(row["version"]),
                    now,
                )
                return CommandResult(409, body, int(row["version"]))
            if row["run_state"] in {
                RunState.PREPARATION_REVIEW.value,
                RunState.DELETE_PENDING.value,
                RunState.FAILED.value,
            }:
                body = _error_body(
                    "INVALID_STATE",
                    "This StoryRun cannot be canceled in its current state.",
                    retryable=False,
                )
                _finalize_receipt(
                    connection,
                    tables.story_command_receipts,
                    receipt_id,
                    409,
                    body,
                    int(row["version"]),
                    run_id,
                    int(row["version"]),
                    now,
                )
                return CommandResult(409, body, int(row["version"]))
            upload_rows = (
                connection.execute(
                    select(
                        tables.upload_sessions.c.upload_session_id,
                        tables.upload_sessions.c.state,
                        tables.upload_sessions.c.state_version,
                    )
                    .where(
                        tables.upload_sessions.c.target_kind == "STORY_RUN",
                        tables.upload_sessions.c.target_ref == run_id,
                        tables.upload_sessions.c.actor_scope_kind == actor_scope_kind.value,
                        tables.upload_sessions.c.actor_scope_ref == actor_scope_ref,
                    )
                    .order_by(tables.upload_sessions.c.upload_session_id)
                    .with_for_update()
                )
                .mappings()
                .all()
            )
            new_revision = int(row["revision"]) + 1
            new_version = int(row["version"]) + 1
            connection.execute(
                update(tables.story_runs)
                .where(
                    tables.story_runs.c.run_id == run_id,
                    tables.story_runs.c.version == expected_version,
                )
                .values(
                    run_state=RunState.DELETE_PENDING.value,
                    revision=new_revision,
                    version=new_version,
                    active_owner_parent_account_id=None,
                    dispatch_gate_open=False,
                    dispatch_claimed_version=None,
                    updated_at=now,
                )
            )
            for upload in upload_rows:
                upload_id = str(upload["upload_session_id"])
                cleanup_upload_ids.append(upload_id)
                if upload["state"] not in {
                    UploadState.RECEIVING.value,
                    UploadState.PENDING.value,
                    UploadState.PROCESSING.value,
                }:
                    continue
                upload_version = int(upload["state_version"]) + 1
                connection.execute(
                    update(tables.upload_sessions)
                    .where(
                        tables.upload_sessions.c.upload_session_id == upload_id,
                        tables.upload_sessions.c.state == upload["state"],
                    )
                    .values(
                        state=UploadState.ABORTED.value,
                        state_version=upload_version,
                        admission_gate_open=False,
                        claim_version=None,
                        error_code=(
                            "UPLOAD_SESSION_STATE_CONFLICT"
                            if upload["state"]
                            in {UploadState.PENDING.value, UploadState.PROCESSING.value}
                            else None
                        ),
                        updated_at=now,
                    )
                )
                if upload["state"] in {UploadState.PENDING.value, UploadState.PROCESSING.value}:
                    pending_receipts = (
                        connection.execute(
                            select(tables.upload_command_receipts.c.receipt_id)
                            .where(
                                tables.upload_command_receipts.c.resource_ref == upload_id,
                                tables.upload_command_receipts.c.operation == "COMPLETE_UPLOAD",
                                tables.upload_command_receipts.c.state
                                == ReceiptState.PENDING.value,
                            )
                            .order_by(tables.upload_command_receipts.c.receipt_id)
                            .with_for_update()
                        )
                        .scalars()
                        .all()
                    )
                    for pending_receipt_id in pending_receipts:
                        _finalize_receipt(
                            connection,
                            tables.upload_command_receipts,
                            str(pending_receipt_id),
                            409,
                            _error_body(
                                "UPLOAD_SESSION_STATE_CONFLICT",
                                "The StoryRun was canceled before upload admission completed.",
                                retryable=False,
                            ),
                            upload_version,
                            upload_id,
                            upload_version,
                            now,
                        )
            body = _run_body(
                connection.execute(
                    select(tables.story_runs).where(tables.story_runs.c.run_id == run_id)
                )
                .mappings()
                .one()
            )
            _finalize_receipt(
                connection,
                tables.story_command_receipts,
                receipt_id,
                202,
                body,
                new_version,
                run_id,
                new_version,
                now,
            )
            result = CommandResult(202, body, new_version)
        for upload_id in cleanup_upload_ids:
            self.remove_upload_quarantine(upload_id)
        assert result is not None
        return result

    def read_asset(self, asset_ref: str) -> bytes:
        try:
            return self._quarantine.read_asset(asset_ref, max_bytes=MAX_UPLOAD_BYTES)
        except QuarantineError:
            raise KeyError(asset_ref) from None

    def store_asset(self, asset_ref: str, payload: bytes) -> str:
        try:
            return self._quarantine.store_asset(asset_ref, payload)
        except QuarantineError:
            raise

    def delete_asset(self, asset_ref: str) -> None:
        self._quarantine.delete_asset(asset_ref)

    def remove_upload_quarantine(self, upload_id: str) -> bool:
        try:
            self._quarantine.remove_upload(upload_id)
        except (OSError, QuarantineError):
            _logger.warning("StoryRun-lite upload staging cleanup failed")
            return False
        return True

    def get_run_provider_identity(self, run_id: str) -> tuple[str, str, str]:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(tables.story_runs).where(tables.story_runs.c.run_id == run_id)
                )
                .mappings()
                .one_or_none()
            )
        if row is None or not row["provider_job_id"] or not row["provider_attempt_id"]:
            raise StoryRunLiteError(404, "NOT_FOUND", "StoryRun invocation identity not found.")
        return (
            str(row["provider_job_id"]),
            str(row["provider_attempt_id"]),
            str(row["actor_scope_ref"]),
        )

    def _owned_upload(
        self,
        connection: Connection,
        actor_scope_kind: OwnerScopeKind,
        actor_scope_ref: str,
        upload_id: str,
        *,
        lock: bool = False,
    ) -> Any:
        query = select(tables.upload_sessions).where(
            tables.upload_sessions.c.upload_session_id == upload_id,
            tables.upload_sessions.c.actor_scope_kind == actor_scope_kind.value,
            tables.upload_sessions.c.actor_scope_ref == actor_scope_ref,
        )
        if lock:
            query = query.with_for_update()
        row = connection.execute(query).mappings().one_or_none()
        if row is None:
            raise StoryRunLiteError(
                404, "NOT_FOUND", "Upload session not found in this actor scope."
            )
        return row

    def _owned_upload_with_run(
        self,
        connection: Connection,
        actor_scope_kind: OwnerScopeKind,
        actor_scope_ref: str,
        upload_id: str,
    ) -> tuple[Any, Any]:
        target = connection.execute(
            select(
                tables.upload_sessions.c.target_kind,
                tables.upload_sessions.c.target_ref,
            ).where(
                tables.upload_sessions.c.upload_session_id == upload_id,
                tables.upload_sessions.c.actor_scope_kind == actor_scope_kind.value,
                tables.upload_sessions.c.actor_scope_ref == actor_scope_ref,
            )
        ).first()
        if target is None or target.target_kind != "STORY_RUN":
            raise StoryRunLiteError(
                404, "NOT_FOUND", "Upload session not found in this actor scope."
            )
        run = self._owned_run(
            connection,
            actor_scope_kind,
            actor_scope_ref,
            str(target.target_ref),
            lock=True,
        )
        upload = self._owned_upload(
            connection, actor_scope_kind, actor_scope_ref, upload_id, lock=True
        )
        if upload["target_kind"] != "STORY_RUN" or upload["target_ref"] != target.target_ref:
            raise StoryRunLiteError(
                404, "NOT_FOUND", "Upload session not found in this actor scope."
            )
        return run, upload

    def _owned_run(
        self,
        connection: Connection,
        actor_scope_kind: OwnerScopeKind,
        actor_scope_ref: str,
        run_id: str,
        *,
        lock: bool = False,
    ) -> Any:
        query = select(tables.story_runs).where(
            tables.story_runs.c.run_id == run_id,
            tables.story_runs.c.actor_scope_kind == actor_scope_kind.value,
            tables.story_runs.c.actor_scope_ref == actor_scope_ref,
        )
        if lock:
            query = query.with_for_update()
        row = connection.execute(query).mappings().one_or_none()
        if row is None:
            raise StoryRunLiteError(404, "NOT_FOUND", "StoryRun not found in this actor scope.")
        return row

    def _asset_binding(
        self,
        connection: Connection,
        asset_ref: str,
        version: int,
        actor_scope_kind: OwnerScopeKind,
        actor_scope_ref: str,
    ) -> AssetBinding:
        row = (
            connection.execute(
                select(_asset_metadata).where(
                    _asset_metadata.c.asset_ref == asset_ref,
                    _asset_metadata.c.asset_version == version,
                )
            )
            .mappings()
            .one_or_none()
        )
        if (
            row is None
            or row["owner_scope_kind"] != actor_scope_kind.value
            or row["owner_scope_ref"] != actor_scope_ref
        ):
            raise StoryRunLiteError(404, "NOT_FOUND", "Asset is not available in this owner scope.")
        if not row["content_sha256"] or len(str(row["content_sha256"])) != 64:
            raise StoryRunLiteError(422, "ASSET_INVALID", "Asset metadata is incomplete.")
        upload = (
            connection.execute(
                select(
                    tables.upload_sessions.c.actual_size_bytes,
                    tables.upload_sessions.c.expected_size_bytes,
                ).where(
                    tables.upload_sessions.c.asset_ref == asset_ref,
                    tables.upload_sessions.c.state == UploadState.READY.value,
                )
            )
            .mappings()
            .one_or_none()
        )
        if upload is not None:
            byte_size = int(upload["actual_size_bytes"] or upload["expected_size_bytes"])
        else:
            lineage_size = connection.execute(
                select(tables.asset_lineage.c.derived_size_bytes).where(
                    tables.asset_lineage.c.derived_asset_ref == asset_ref,
                    tables.asset_lineage.c.derived_asset_version == version,
                )
            ).scalar_one_or_none()
            byte_size = int(lineage_size or 0)
        if byte_size < 1:
            raise StoryRunLiteError(422, "ASSET_INVALID", "Asset size metadata is unavailable.")
        return AssetBinding(
            asset_ref,
            version,
            str(row["media_type"]),
            str(row["content_sha256"]),
            byte_size,
            actor_scope_kind,
            actor_scope_ref,
        )

    def _upload_body(
        self, connection: Connection, upload_id: str, *, row: Any | None = None
    ) -> dict[str, object]:
        selected = (
            row
            or connection.execute(
                select(tables.upload_sessions).where(
                    tables.upload_sessions.c.upload_session_id == upload_id
                )
            )
            .mappings()
            .one()
        )
        parts = (
            connection.execute(
                select(tables.upload_parts)
                .where(tables.upload_parts.c.upload_session_id == upload_id)
                .order_by(tables.upload_parts.c.part_number)
            )
            .mappings()
            .all()
        )
        result: dict[str, object] = {
            "upload_ref": str(selected["upload_session_id"]),
            "state": str(selected["state"]),
            "version": int(selected["state_version"]),
            "part_size_bytes": int(selected["part_size_bytes"]),
            "max_total_bytes": int(selected["max_total_bytes"]),
            "max_parts": int(selected["max_parts"]),
            "parts": [
                _part_body(int(part["part_number"]), int(part["byte_size"]), str(part["sha256"]))
                for part in parts
            ],
            "asset_ref": selected["asset_ref"],
            "derived_asset_ref": selected["derived_asset_ref"],
            "expires_at": _iso(selected["expires_at"]),
            "error": _error_for_code(str(selected["error_code"]))
            if selected["error_code"]
            else None,
        }
        return result


def _identity(
    actor_scope_kind: OwnerScopeKind,
    actor_scope_ref: str,
    operation: str,
    scope_kind: str,
    scope_ref: str,
    key_sha256: str,
) -> dict[str, str]:
    return {
        "actor_scope_kind": actor_scope_kind.value,
        "actor_scope_ref": actor_scope_ref,
        "operation": operation,
        "idempotency_scope_kind": scope_kind,
        "idempotency_scope_ref": scope_ref,
        "idempotency_key_sha256": key_sha256,
    }


def _lock_identity(connection: Connection, identity: str) -> None:
    connection.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:identity, 0))"), {"identity": identity}
    )


def _existing_receipt(
    connection: Connection, table: Any, identity: dict[str, str], fingerprint_sha256: str
) -> CommandResult | None:
    row = (
        connection.execute(select(table).filter_by(**identity).with_for_update())
        .mappings()
        .one_or_none()
    )
    if row is None:
        return None
    if row["request_fingerprint_sha256"] != fingerprint_sha256:
        raise StoryRunLiteError(
            400,
            "INVALID_IDEMPOTENCY_KEY",
            "This Idempotency-Key was already used with a different request.",
        )
    if row["state"] != ReceiptState.FINAL.value:
        raise StoryRunLiteError(
            409,
            "COMMAND_RECOVERY_HOLD",
            "This command is still pending recovery; do not submit a new key.",
            retryable=False,
        )
    return CommandResult(
        int(row["response_status"]),
        dict(row["response_body"]),
        int(row["response_resource_version"])
        if row["response_resource_version"] is not None
        else None,
        True,
    )


def _finalize_receipt(
    connection: Connection,
    table: Any,
    receipt_id: str,
    status_code: int,
    body: dict[str, object],
    response_resource_version: int | None,
    resource_ref: str | None,
    resource_version: int | None,
    finalized_at: datetime,
) -> None:
    result = connection.execute(
        update(table)
        .where(table.c.receipt_id == receipt_id, table.c.state == ReceiptState.PENDING.value)
        .values(
            state=ReceiptState.FINAL.value,
            response_status=status_code,
            response_resource_version=response_resource_version,
            response_body=body,
            resource_ref=resource_ref,
            resource_version=resource_version,
            state_version=table.c.state_version + 1,
            finalized_at=finalized_at,
        )
    )
    if result.rowcount != 1:
        raise RuntimeError("command receipt did not finalize from PENDING")


def _run_body(row: Any) -> dict[str, object]:
    result: dict[str, object] = {
        "run_ref": str(row["run_id"]),
        "run_state": str(row["run_state"]),
        "revision": int(row["revision"]),
        "version": int(row["version"]),
        "target_revision": int(row["understanding_revision"])
        if row["understanding_revision"] is not None
        else None,
        "created_at": _iso(row["created_at"]),
        "updated_at": _iso(row["updated_at"]),
        "job_state": row["job_state"],
        "retryable": bool(row["retryable"]),
        "action_required": row["action_required"],
        "error": _error_for_code(str(row["error_code"])) if row["error_code"] else None,
        "result": None,
    }
    if row["run_state"] == RunState.SUBJECT_REVIEW.value:
        result["result"] = {
            "understanding_revision": int(row["understanding_revision"]),
            "subject_label": str(row["subject_label"]),
            "confidence": float(row["confidence"]),
        }
    return result


def _part_body(part_number: int, size: int, sha256: str) -> dict[str, object]:
    return {"part_no": part_number, "size_bytes": size, "sha256": sha256}


def _error_body(code: str, message: str, *, retryable: bool) -> dict[str, object]:
    return {
        "code": code,
        "message": message,
        "correlation_id": str(uuid4()),
        "retryable": retryable,
        "retry_after_seconds": None,
        "field_errors": None,
    }


def _error_for_code(code: str) -> dict[str, object]:
    messages = {
        "UPLOAD_EXPIRED": "Upload session has expired.",
        "UPLOAD_SESSION_STATE_CONFLICT": "Upload did not finish safely; create a new session.",
        "VISION_ATTEMPT_HOLD": "Vision outcome is held for operator review; it will not be resent.",
        "VISION_OUTCOME_UNKNOWN": "Vision outcome is unknown; do not retry automatically.",
        "SCANNER_UNAVAILABLE": "ClamAV did not return a CLEAN verdict for this snapshot.",
        "SCANNER_REJECTED": "ClamAV rejected this snapshot.",
        "IMAGE_INVALID": "Image format or content is invalid.",
        "WORKER_LIMITS_UNAVAILABLE": "The OS-enforced image worker limits are unavailable.",
    }
    return _error_body(
        code, messages.get(code, "The request could not be completed."), retryable=False
    )


def _iso(value: datetime | None) -> str:
    if value is None:
        return datetime.now(UTC).isoformat()
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat()


def _is_expired(row: Any, now: datetime) -> bool:
    expires_at = row["expires_at"]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    return bool(expires_at <= now)


__all__ = ["SqlStoryRunLiteRepository"]
