"""Own10 PostgreSQL UoW/CAS/unique failed-lifecycle claim, not owner adoption."""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Connection, Engine, insert, select, text, update
from sqlalchemy.exc import IntegrityError

from sketch2life.domain.knowledge_video.model import VideoError, canonical_digest, require_id
from sketch2life.domain.video_failure.model import Intent
from sketch2life.infrastructure.video_failure.codec import decode, encode
from sketch2life.infrastructure.video_failure.tables import EVENT, HISTORY, INTENT


class FailureRows:
    def __init__(self, connection: Connection, organization_id: str, session_id: str) -> None:
        if connection.dialect.name != "postgresql":
            raise VideoError("VIDEO_DISPOSITION_POSTGRESQL_REQUIRED")
        for value in (organization_id, session_id):
            require_id(value)
        self.conn, self.org, self.session = connection, organization_id, session_id

    def _tx(self) -> None:
        if not self.conn.in_transaction():
            raise VideoError("VIDEO_DISPOSITION_TRANSACTION_REQUIRED")

    def _scope(self, intent: Intent) -> None:
        if (intent.context.organization_id, intent.context.session_id) != (self.org, self.session):
            raise VideoError("VIDEO_DISPOSITION_SCOPE_MISMATCH")

    def get(self, principal_id: str, client_key: str) -> Intent | None:
        self._tx()
        for value in (principal_id, client_key):
            require_id(value)
        row = (
            self.conn.execute(
                select(INTENT).where(
                    INTENT.c.organization_id == self.org,
                    INTENT.c.session_id == self.session,
                    INTENT.c.principal_id == principal_id,
                    INTENT.c.client_key == client_key,
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        intent = decode(row["payload"])
        c = intent.context
        if (
            (c.organization_id, c.session_id, c.principal_id, c.client_key)
            != (self.org, self.session, principal_id, client_key)
            or tuple(
                row[name]
                for name in ("organization_id", "session_id", "principal_id", "client_key")
            )
            != (self.org, self.session, principal_id, client_key)
            or type(row["revision"]) is not int
            or (row["revision"], row["claim_key"], row["disposition_id"])
            != (intent.revision, intent.target.claim_key(), intent.disposition_id)
        ):
            raise VideoError("VIDEO_DISPOSITION_STORAGE_CORRUPT")
        return intent

    def _append(self, intent: Intent) -> None:
        self.conn.execute(
            insert(HISTORY).values(
                organization_id=self.org,
                disposition_id=intent.disposition_id,
                revision=intent.revision,
                payload=encode(intent),
            )
        )
        # Minimal committed event intent, NOT a delivered external command.
        self.conn.execute(
            insert(EVENT).values(
                organization_id=self.org,
                disposition_id=intent.disposition_id,
                revision=intent.revision,
                operation_key=intent.context.operation_key(),
                target_digest=intent.target.digest(),
            )
        )

    def insert(self, intent: Intent) -> None:
        self._tx()
        payload = encode(intent)
        self._scope(intent)
        if intent.revision != 1 or intent.receipt is not None:
            raise VideoError("VIDEO_DISPOSITION_INVALID_INTENT")
        c = intent.context
        try:
            self.conn.execute(
                insert(INTENT).values(
                    organization_id=self.org,
                    session_id=self.session,
                    principal_id=c.principal_id,
                    client_key=c.client_key,
                    disposition_id=intent.disposition_id,
                    claim_key=intent.target.claim_key(),
                    revision=1,
                    payload=payload,
                )
            )
            self._append(intent)
        except IntegrityError:
            # Caller rolls back whole tx; do not query winner in aborted transaction.
            raise VideoError("VIDEO_DISPOSITION_CONFLICT") from None

    def save(self, intent: Intent, *, expected_revision: int) -> None:
        self._tx()
        payload = encode(intent)
        self._scope(intent)
        c = intent.context
        before = self.get(c.principal_id, c.client_key)
        if (
            type(expected_revision) is not int
            or expected_revision != 1
            or before is None
            or (
                before.revision != expected_revision
                or before.receipt is not None
                or intent.receipt is None
                or before.settle(intent.receipt) != intent
            )
        ):
            raise VideoError("VIDEO_DISPOSITION_STALE_INTENT")
        try:
            result = self.conn.execute(
                update(INTENT)
                .where(
                    INTENT.c.organization_id == self.org,
                    INTENT.c.session_id == self.session,
                    INTENT.c.principal_id == c.principal_id,
                    INTENT.c.client_key == c.client_key,
                    INTENT.c.revision == expected_revision,
                )
                .values(revision=2, payload=payload)
            )
            if result.rowcount != 1:
                raise VideoError("VIDEO_DISPOSITION_STALE_INTENT")
            self._append(intent)
        except IntegrityError:
            raise VideoError("VIDEO_DISPOSITION_CONFLICT") from None


class SqlFailureStore:
    def __init__(self, engine: Engine) -> None:
        if engine.dialect.name != "postgresql":
            raise VideoError("VIDEO_DISPOSITION_POSTGRESQL_REQUIRED")
        self.engine = engine

    @contextmanager
    def transaction(self, organization_id: str, session_id: str) -> Iterator[FailureRows]:
        for value in (organization_id, session_id):
            require_id(value)
        with self.engine.begin() as conn:
            key = canonical_digest(
                {"schema": "BE2-10.Lock/1", "org": organization_id, "session": session_id}
            )
            conn.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:scope, 0))"), {"scope": key}
            )
            yield FailureRows(conn, organization_id, session_id)
