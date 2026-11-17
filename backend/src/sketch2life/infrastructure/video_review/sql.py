"""Owned09 scoped PostgreSQL adapters; persistence is NOT authority/bridge adoption."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import replace
from typing import cast

from sqlalchemy import Connection, Engine, Table, insert, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.elements import ColumnElement

from sketch2life.application.ports.video_review_lifecycle import ReviewChangeReceipt
from sketch2life.application.ports.video_review_write import ReviewWriteReceipt
from sketch2life.domain.knowledge_video.model import (
    VideoError,
    canonical_digest,
    require_id,
    require_revision,
)
from sketch2life.domain.video_review.model import ReviewHead
from sketch2life.domain.video_review.playback import PlaybackIntent, PlaybackState
from sketch2life.infrastructure.video_review.codec import decode, encode
from sketch2life.infrastructure.video_review.tables import (
    EVENT,
    HEAD,
    HISTORY,
    PLAYBACK,
    PLAYBACK_HISTORY,
    RECEIPT,
)


class _Rows:
    def __init__(self, connection: Connection, org: str, session: str) -> None:
        for value in (org, session):
            require_id(value)
        if connection.dialect.name != "postgresql":
            raise VideoError("VIDEO_REVIEW_POSTGRESQL_REQUIRED")
        self.conn, self.org, self.session = connection, org, session

    def _tx(self) -> None:
        if not self.conn.in_transaction():
            raise VideoError("VIDEO_REVIEW_TRANSACTION_REQUIRED")

    def _scope(self, table: Table) -> tuple[ColumnElement[bool], ...]:
        return (table.c.organization_id == self.org, table.c.session_id == self.session)

    def _event(self, event_id: str, video_id: str, kind: str, revision: int, digest: str) -> None:
        # Minimal committed audit/outbox INTENT. No raw reason, script, audience,
        # credentials/URL. Relay/ack/delivery authority belongs to later adoption.
        self.conn.execute(
            insert(EVENT).values(
                organization_id=self.org,
                session_id=self.session,
                video_id=video_id,
                event_id=event_id,
                kind=kind,
                revision=revision,
                subject_digest=digest,
            )
        )


class ReviewRows(_Rows):
    """Caller holds current authority then session advisory lock through transaction."""

    def __init__(self, connection: Connection, org: str, session: str, video: str) -> None:
        super().__init__(connection, org, session)
        require_id(video)
        self.video = video

    def _scope(self, table: Table) -> tuple[ColumnElement[bool], ...]:
        return (*super()._scope(table), table.c.video_id == self.video)

    def head(self) -> ReviewHead | None:
        self._tx()
        row = self.conn.execute(select(HEAD).where(*self._scope(HEAD))).mappings().one_or_none()
        if row is None:
            return None
        head = cast(ReviewHead, decode("head", row["payload"]))
        if type(row["revision"]) is not int:
            raise VideoError("VIDEO_REVIEW_STORAGE_CORRUPT")
        subject = head.subject
        if (
            row["organization_id"],
            row["session_id"],
            row["video_id"],
            row["revision"],
            row["subject_digest"],
        ) != (self.org, self.session, self.video, head.revision, subject.digest()) or (
            subject.organization_id,
            subject.audience.session_id,
            subject.video_id,
        ) != (self.org, self.session, self.video):
            raise VideoError("VIDEO_REVIEW_STORAGE_CORRUPT")
        return head

    def _receipt(
        self, kind: str, principal: str, key: str
    ) -> ReviewWriteReceipt | ReviewChangeReceipt | None:
        self._tx()
        for value in (principal, key):
            require_id(value)
        row = (
            self.conn.execute(
                select(RECEIPT).where(
                    *self._scope(RECEIPT),
                    RECEIPT.c.principal_id == principal,
                    RECEIPT.c.client_key == key,
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        if row["kind"] not in {"write", "change"}:
            raise VideoError("VIDEO_REVIEW_STORAGE_CORRUPT")
        if row["kind"] != kind:
            raise VideoError("VIDEO_REVIEW_IDEMPOTENCY_CONFLICT")
        receipt = cast(ReviewWriteReceipt | ReviewChangeReceipt, decode(kind, row["payload"]))
        ctx = receipt.context
        revision = (
            receipt.entry.revision
            if isinstance(receipt, ReviewWriteReceipt)
            else receipt.change.after.revision
        )
        if (
            (ctx.organization_id, ctx.session_id, ctx.video_id, ctx.principal_id, ctx.client_key)
            != (self.org, self.session, self.video, principal, key)
            or tuple(
                row[name]
                for name in (
                    "organization_id",
                    "session_id",
                    "video_id",
                    "principal_id",
                    "client_key",
                )
            )
            != (self.org, self.session, self.video, principal, key)
            or type(row["revision"]) is not int
            or row["revision"] != revision
        ):
            raise VideoError("VIDEO_REVIEW_STORAGE_CORRUPT")
        return receipt

    def receipt(self, principal_id: str, client_key: str) -> ReviewWriteReceipt | None:
        return cast(ReviewWriteReceipt | None, self._receipt("write", principal_id, client_key))

    def change_receipt(self, principal_id: str, client_key: str) -> ReviewChangeReceipt | None:
        return cast(ReviewChangeReceipt | None, self._receipt("change", principal_id, client_key))

    def _save(self, before: ReviewHead | None, after: ReviewHead) -> None:
        if self.head() != before:
            raise VideoError("VIDEO_REVIEW_STALE_REVISION")
        if (
            after.subject.organization_id,
            after.subject.audience.session_id,
            after.subject.video_id,
        ) != (self.org, self.session, self.video):
            raise VideoError("VIDEO_REVIEW_SCOPE_MISMATCH")
        values = dict(
            revision=after.revision,
            subject_digest=after.subject.digest(),
            payload=encode("head", after),
        )
        if before is None:
            self.conn.execute(
                insert(HEAD).values(
                    organization_id=self.org, session_id=self.session, video_id=self.video, **values
                )
            )
        else:
            if after.revision != before.revision + 1:
                raise VideoError("VIDEO_REVIEW_STALE_REVISION")
            result = self.conn.execute(
                update(HEAD)
                .where(*self._scope(HEAD), HEAD.c.revision == before.revision)
                .values(**values)
            )
            if result.rowcount != 1:
                raise VideoError("VIDEO_REVIEW_STALE_REVISION")

    def _append(
        self,
        kind: str,
        receipt: ReviewWriteReceipt | ReviewChangeReceipt,
        after: ReviewHead,
        event_id: str,
    ) -> None:
        self.conn.execute(
            insert(RECEIPT).values(
                organization_id=self.org,
                session_id=self.session,
                video_id=self.video,
                principal_id=receipt.context.principal_id,
                client_key=receipt.context.client_key,
                kind=kind,
                revision=after.revision,
                payload=encode(kind, receipt),
            )
        )
        self.conn.execute(
            insert(HISTORY).values(
                organization_id=self.org,
                session_id=self.session,
                video_id=self.video,
                revision=after.revision,
                payload=encode("head", after),
            )
        )
        self._event(event_id, self.video, "review." + kind, after.revision, after.subject.digest())

    def write(
        self, before: ReviewHead | None, after: ReviewHead, receipt: ReviewWriteReceipt
    ) -> None:
        self._tx()
        receipt, after = replace(receipt), replace(after)
        encode("write", receipt)
        initial = before or ReviewHead(after.subject, receipt.context.expected_review_revision)
        expected = initial.record(
            receipt.context.expected_review_revision,
            receipt.entry.review_id,
            receipt.entry.reviewer_id,
            receipt.entry.decision,
            receipt.entry.reason,
            receipt.entry.recorded_at,
        )
        if expected != after or after.entry != receipt.entry:
            raise VideoError("VIDEO_REVIEW_INVALID_RECORD")
        if (
            receipt.context.organization_id,
            receipt.context.session_id,
            receipt.context.video_id,
        ) != (self.org, self.session, self.video):
            raise VideoError("VIDEO_REVIEW_SCOPE_MISMATCH")
        try:
            self._save(before, after)
            self._append("write", receipt, after, "review:" + receipt.entry.review_id)
        except IntegrityError:
            raise VideoError("VIDEO_REVIEW_WRITE_CONFLICT") from None

    def change(self, receipt: ReviewChangeReceipt) -> None:
        self._tx()
        receipt = replace(receipt)
        encode("change", receipt)
        event = receipt.change
        if (
            receipt.context.organization_id,
            receipt.context.session_id,
            receipt.context.video_id,
        ) != (self.org, self.session, self.video):
            raise VideoError("VIDEO_REVIEW_SCOPE_MISMATCH")
        try:
            self._save(event.before, event.after)
            # Receipt retains immutable before+archived+after, not only current head.
            self._append("change", receipt, event.after, "change:" + event.event_id)
        except IntegrityError:
            raise VideoError("VIDEO_REVIEW_WRITE_CONFLICT") from None


class PlaybackRows(_Rows):
    def get(self, principal_id: str, client_key: str) -> PlaybackIntent | None:
        self._tx()
        for value in (principal_id, client_key):
            require_id(value)
        row = (
            self.conn.execute(
                select(PLAYBACK).where(
                    *self._scope(PLAYBACK),
                    PLAYBACK.c.principal_id == principal_id,
                    PLAYBACK.c.client_key == client_key,
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        intent = cast(PlaybackIntent, decode("playback", row["payload"]))
        subject = intent.request.subject
        if (
            (
                subject.organization_id,
                subject.audience.session_id,
                intent.principal_id,
                intent.client_key,
            )
            != (self.org, self.session, principal_id, client_key)
            or tuple(
                row[name]
                for name in ("organization_id", "session_id", "principal_id", "client_key")
            )
            != (self.org, self.session, principal_id, client_key)
            or (row["video_id"], row["revision"], row["state"])
            != (subject.video_id, intent.revision, intent.state.value)
            or type(row["revision"]) is not int
        ):
            raise VideoError("VIDEO_REVIEW_STORAGE_CORRUPT")
        return intent

    def _append(self, intent: PlaybackIntent) -> None:
        self.conn.execute(
            insert(PLAYBACK_HISTORY).values(
                organization_id=self.org,
                session_id=self.session,
                principal_id=intent.principal_id,
                client_key=intent.client_key,
                revision=intent.revision,
                payload=encode("playback", intent),
            )
        )
        self._event(
            "playback:" + intent.operation_key() + ":" + str(intent.revision),
            intent.request.subject.video_id,
            "playback." + intent.state.value,
            intent.revision,
            intent.request.subject.digest(),
        )

    def insert(self, intent: PlaybackIntent) -> None:
        self._tx()
        intent = replace(intent)
        payload = encode("playback", intent)
        subject = intent.request.subject
        if (
            (subject.organization_id, subject.audience.session_id) != (self.org, self.session)
            or intent.state is not PlaybackState.PENDING
            or intent.revision != 1
        ):
            raise VideoError("VIDEO_PLAYBACK_INVALID_STATE")
        try:
            self.conn.execute(
                insert(PLAYBACK).values(
                    organization_id=self.org,
                    session_id=self.session,
                    principal_id=intent.principal_id,
                    client_key=intent.client_key,
                    video_id=subject.video_id,
                    revision=1,
                    state=intent.state.value,
                    payload=payload,
                )
            )
            self._append(intent)
        except IntegrityError:
            raise VideoError("VIDEO_REVIEW_WRITE_CONFLICT") from None

    def save(self, intent: PlaybackIntent, *, expected_revision: int) -> None:
        self._tx()
        require_revision(expected_revision)
        intent = replace(intent)
        payload = encode("playback", intent)
        before = self.get(intent.principal_id, intent.client_key)
        if (
            before is None
            or before.revision != expected_revision
            or before.receipt is not None
            or intent.receipt is None
            or before.settle(intent.receipt) != intent
        ):
            raise VideoError("VIDEO_PLAYBACK_STALE_INTENT")
        try:
            result = self.conn.execute(
                update(PLAYBACK)
                .where(
                    *self._scope(PLAYBACK),
                    PLAYBACK.c.principal_id == intent.principal_id,
                    PLAYBACK.c.client_key == intent.client_key,
                    PLAYBACK.c.revision == expected_revision,
                )
                .values(revision=intent.revision, state=intent.state.value, payload=payload)
            )
            if result.rowcount != 1:
                raise VideoError("VIDEO_PLAYBACK_STALE_INTENT")
            self._append(intent)
        except IntegrityError:
            raise VideoError("VIDEO_REVIEW_WRITE_CONFLICT") from None


class _Store:
    def __init__(self, engine: Engine) -> None:
        if engine.dialect.name != "postgresql":
            raise VideoError("VIDEO_REVIEW_POSTGRESQL_REQUIRED")
        self.engine = engine

    def _lock(self, conn: Connection, org: str, session: str) -> None:
        for value in (org, session):
            require_id(value)
        # Serialize own mutations before first head exists, consistently across
        # review/change/playback. This is NOT a cross-owner revocation fence.
        scope = canonical_digest({"schema": "BE2-09.Lock/1", "org": org, "session": session})
        conn.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:scope, 0))"), {"scope": scope}
        )


class SqlVideoReviewStore(_Store):
    @contextmanager
    def transaction(
        self, organization_id: str, session_id: str, video_id: str
    ) -> Iterator[ReviewRows]:
        require_id(video_id)
        with self.engine.begin() as conn:
            self._lock(conn, organization_id, session_id)
            yield ReviewRows(conn, organization_id, session_id, video_id)


class SqlVideoPlaybackStore(_Store):
    @contextmanager
    def transaction(self, organization_id: str, session_id: str) -> Iterator[PlaybackRows]:
        with self.engine.begin() as conn:
            self._lock(conn, organization_id, session_id)
            yield PlaybackRows(conn, organization_id, session_id)
