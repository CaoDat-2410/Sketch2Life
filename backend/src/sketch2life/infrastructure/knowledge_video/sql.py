"""Caller-transaction-bound owned08 row participant, NOT AtomicVideoSubmission.

Never opens/commits a transaction, creates a foundation job, or dispatches work.
Actual composition must bind this SAME connection to the adopted authorized
foundation bridge and owner guards. No durable create route/factory supplied.
"""

from __future__ import annotations

from dataclasses import replace

from sqlalchemy import Connection, insert, select, update
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import IntegrityError

from sketch2life.application.ports.knowledge_video import VideoCommandReceipt
from sketch2life.domain.ai_jobs.model import TERMINAL_STATES, JobState
from sketch2life.domain.knowledge_video.model import (
    VideoError,
    VideoRun,
    require_hash,
    require_id,
    require_revision,
)
from sketch2life.infrastructure.knowledge_video.codec import decode_run, encode_run
from sketch2life.infrastructure.knowledge_video.tables import RECEIPT, RUN


def _decode_row(row: RowMapping, organization_id: str) -> VideoRun:
    run = decode_run(row["run_json"])
    if ((row["organization_id"], row["video_id"], row["session_id"], row["job_id"],
         row["run_revision"], row["pin_digest"])
            != (organization_id, run.video_id, run.pin.session_id, run.job_id,
                run.run_revision, run.pin.digest())
            or run.pin.organization_id != organization_id):
        raise VideoError("VIDEO_STORAGE_CORRUPT")
    return run


def _values(run: VideoRun) -> dict[str, object]:
    return {"organization_id": run.pin.organization_id, "video_id": run.video_id,
            "session_id": run.pin.session_id, "job_id": run.job_id,
            "run_revision": run.run_revision, "pin_digest": run.pin.digest(),
            "run_json": encode_run(run)}


class VideoRunRows:
    def __init__(self, connection: Connection, organization_id: str) -> None:
        require_id(organization_id)
        if connection.dialect.name != "postgresql":
            raise VideoError("VIDEO_POSTGRESQL_REQUIRED")
        self._connection = connection
        self._organization_id = organization_id

    def _transaction(self) -> None:
        if not self._connection.in_transaction():
            raise VideoError("VIDEO_TRANSACTION_REQUIRED")

    def get(self, video_id: str, *, for_update: bool = False) -> VideoRun | None:
        self._transaction()
        require_id(video_id)
        query = select(RUN).where(RUN.c.organization_id == self._organization_id,
                                  RUN.c.video_id == video_id)
        if for_update:
            query = query.with_for_update()
        row = self._connection.execute(query).mappings().one_or_none()
        return None if row is None else _decode_row(row, self._organization_id)

    def find_semantic(self, session_id: str, pin_digest: str) -> VideoRun | None:
        self._transaction()
        require_id(session_id)
        require_hash(pin_digest)
        query = select(RUN).where(RUN.c.organization_id == self._organization_id,
                                  RUN.c.session_id == session_id, RUN.c.pin_digest == pin_digest)
        row = self._connection.execute(query).mappings().one_or_none()
        return None if row is None else _decode_row(row, self._organization_id)

    def insert(self, run: VideoRun) -> None:
        self._transaction()
        if (run.pin.organization_id != self._organization_id or run.run_revision != 1
                or run.generation_state is not JobState.QUEUED):
            raise VideoError("VIDEO_INVALID_INITIAL_RUN")
        try:
            self._connection.execute(insert(RUN).values(**_values(run)))
        except IntegrityError:
            # Caller MUST roll back the whole enclosing transaction before retry.
            raise VideoError("VIDEO_WRITE_CONFLICT") from None

    def save(self, run: VideoRun, *, expected_revision: int) -> None:
        self._transaction()
        require_revision(expected_revision)
        if (run.pin.organization_id != self._organization_id
                or run.run_revision != expected_revision + 1):
            raise VideoError("VIDEO_STALE_RUN")
        prior = self.get(run.video_id, for_update=True)
        if prior is None or prior.run_revision != expected_revision:
            raise VideoError("VIDEO_STALE_RUN")
        if ((run.pin.digest(), run.video_version, run.review_revision, run.job_id, run.created_at)
                != (prior.pin.digest(), prior.video_version, prior.review_revision,
                    prior.job_id, prior.created_at)):
            raise VideoError("VIDEO_IMMUTABLE_LINEAGE")
        if prior.artifact is not None and run.artifact != prior.artifact:
            raise VideoError("VIDEO_IMMUTABLE_ARTIFACT")
        if (prior.generation_state in TERMINAL_STATES
                and replace(run, run_revision=prior.run_revision) != prior):
            raise VideoError("VIDEO_TERMINAL_RUN")
        result = self._connection.execute(update(RUN).where(
            RUN.c.organization_id == self._organization_id, RUN.c.video_id == run.video_id,
            RUN.c.run_revision == expected_revision
        ).values(run_revision=run.run_revision, run_json=encode_run(run)))
        if result.rowcount != 1:
            raise VideoError("VIDEO_STALE_RUN")

    def get_receipt(self, session_id: str, principal_id: str,
                    key: str) -> VideoCommandReceipt | None:
        self._transaction()
        for value in (session_id, principal_id, key):
            require_id(value)
        query = select(RECEIPT).where(
            RECEIPT.c.organization_id == self._organization_id,
            RECEIPT.c.session_id == session_id, RECEIPT.c.principal_id == principal_id,
            RECEIPT.c.idempotency_key == key
        )
        row = self._connection.execute(query).mappings().one_or_none()
        return None if row is None else VideoCommandReceipt(**dict(row))

    def put_receipt(self, receipt: VideoCommandReceipt) -> None:
        self._transaction()
        run = self.get(receipt.video_id, for_update=True)
        if (receipt.organization_id != self._organization_id or run is None
                or run.pin.session_id != receipt.session_id
                or run.pin.digest() != receipt.pin_digest):
            raise VideoError("VIDEO_RECEIPT_MISMATCH")
        try:
            self._connection.execute(insert(RECEIPT).values(
                organization_id=receipt.organization_id, session_id=receipt.session_id,
                principal_id=receipt.principal_id, idempotency_key=receipt.idempotency_key,
                command_hash=receipt.command_hash, pin_digest=receipt.pin_digest,
                video_id=receipt.video_id, created_at=receipt.created_at
            ))
        except IntegrityError:
            raise VideoError("VIDEO_WRITE_CONFLICT") from None
