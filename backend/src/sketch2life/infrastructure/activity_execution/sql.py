"""Scoped11 PostgreSQL rows/UoW/CAS and immutable exact ACK. No auto dispatcher."""

from collections.abc import Iterator
from contextlib import contextmanager, suppress
from dataclasses import replace
from typing import cast

from sqlalchemy import Connection, Engine, Table, insert, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.elements import ColumnElement

from sketch2life.application.ports.activity_execution import OutcomeAck, OutcomeEvent, Receipt
from sketch2life.domain.activity_execution.model import (
    TERMINAL,
    Action,
    Assignment,
    State,
    digest,
    fail,
)
from sketch2life.domain.knowledge_video.model import VideoError, require_id
from sketch2life.infrastructure.activity_execution.codec import decode, encode
from sketch2life.infrastructure.activity_execution.tables import ACK, EVENT, HEAD, HISTORY, RECEIPT


def validate_change(before: Assignment | None, after: Assignment) -> None:
    after = replace(after)
    if before is None:
        if after.revision != 1 or after.state is not State.SELECTED or after.proof is not None:
            fail("INVALID_TRANSITION")
        return
    before = replace(before)
    variants: list[Assignment] = []
    with suppress(VideoError):
        variants.append(
            before.reselect(
                before.revision,
                after.source,
                after.edits,
                after.audience,
                after.policy,
                after.updated_at,
            )
        )
    if after.invalidated is not None:
        with suppress(VideoError):
            variants.append(before.invalidate(before.revision, after.invalidated, after.updated_at))
    for action in (Action.CONFIRM, Action.START, Action.FINISH, Action.SKIP, Action.INTERRUPT):
        with suppress(VideoError):
            variants.append(
                before.transition(
                    action,
                    before.revision,
                    after.updated_at,
                    confirmation=after.confirmation
                    if action in {Action.CONFIRM, Action.START}
                    else None,
                    proof=after.proof if action in {Action.CONFIRM, Action.START} else None,
                    reason=after.reason,
                    evidence_refs=after.evidence_refs,
                )
            )
    if after not in variants:
        fail("INVALID_TRANSITION")


class ActivityRows:
    def __init__(self, conn: Connection, organization_id: str, session_id: str) -> None:
        if conn.dialect.name != "postgresql":
            fail("POSTGRESQL_REQUIRED")
        for value in (organization_id, session_id):
            require_id(value)
        self.conn, self.org, self.session = conn, organization_id, session_id

    def _tx(self) -> None:
        if not self.conn.in_transaction():
            fail("TRANSACTION_REQUIRED")

    def _scope(self, table: Table) -> tuple[ColumnElement[bool], ...]:
        return (table.c.organization_id == self.org, table.c.session_id == self.session)

    def _read(
        self, table: Table, kind: str, *, expected_revision: int | None = None, **keys: str
    ) -> object | None:
        self._tx()
        for identifier in keys.values():
            require_id(identifier)
        row = (
            self.conn.execute(
                select(table).where(
                    *self._scope(table), *(table.c[key] == value for key, value in keys.items())
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        value = decode(kind, row["payload"])
        if kind == "assignment":
            a = cast(Assignment, value)
        elif kind == "receipt":
            a = cast(Receipt, value).assignment
        elif kind == "event":
            a = cast(OutcomeEvent, value).assignment
        else:
            a = None
        if (
            (row["organization_id"], row["session_id"]) != (self.org, self.session)
            or (any(row[key] != expected for key, expected in keys.items()))
            or type(row["revision"]) is not int
        ):
            fail("STORAGE_CORRUPT")
        if a is not None and (a.organization_id, a.audience.session_id, a.revision) != (
            self.org,
            self.session,
            row["revision"],
        ):
            fail("STORAGE_CORRUPT")
        if expected_revision is not None and row["revision"] != expected_revision:
            fail("STORAGE_CORRUPT")
        if kind == "assignment" and cast(Assignment, value).assignment_id != keys["assignment_id"]:
            fail("STORAGE_CORRUPT")
        if kind == "receipt":
            r = cast(Receipt, value)
            if (r.actor.principal_id, r.actor.client_key) != (
                keys["principal_id"],
                keys["client_key"],
            ):
                fail("STORAGE_CORRUPT")
        if kind == "event" and cast(OutcomeEvent, value).event_id != keys["event_id"]:
            fail("STORAGE_CORRUPT")
        return value

    def load(self, assignment_id: str) -> Assignment | None:
        return cast(Assignment | None, self._read(HEAD, "assignment", assignment_id=assignment_id))

    def receipt(self, principal_id: str, client_key: str) -> Receipt | None:
        return cast(
            Receipt | None,
            self._read(RECEIPT, "receipt", principal_id=principal_id, client_key=client_key),
        )

    def write(
        self, before: Assignment | None, receipt: Receipt, event: OutcomeEvent | None
    ) -> None:
        self._tx()
        encode("receipt", receipt)
        after = receipt.assignment
        validate_change(before, after)
        if (after.organization_id, after.audience.session_id) != (self.org, self.session):
            fail("SCOPE_MISMATCH")
        if (after.state in TERMINAL) != (event is not None):
            fail("INVALID_EVENT")
        if event is not None:
            encode("event", event)
            if event.assignment != after or event.recorded_by != receipt.actor.principal_id:
                fail("INVALID_EVENT")
        if self.load(after.assignment_id) != before:
            fail("STALE_REVISION")
        values = {"revision": after.revision, "payload": encode("assignment", after)}
        try:
            if before is None:
                self.conn.execute(
                    insert(HEAD).values(
                        organization_id=self.org,
                        session_id=self.session,
                        assignment_id=after.assignment_id,
                        **values,
                    )
                )
            else:
                result = self.conn.execute(
                    update(HEAD)
                    .where(
                        *self._scope(HEAD),
                        HEAD.c.assignment_id == after.assignment_id,
                        HEAD.c.revision == before.revision,
                    )
                    .values(**values)
                )
                if result.rowcount != 1:
                    fail("STALE_REVISION")
            self.conn.execute(
                insert(HISTORY).values(
                    organization_id=self.org,
                    session_id=self.session,
                    assignment_id=after.assignment_id,
                    **values,
                )
            )
            self.conn.execute(
                insert(RECEIPT).values(
                    organization_id=self.org,
                    session_id=self.session,
                    principal_id=receipt.actor.principal_id,
                    client_key=receipt.actor.client_key,
                    revision=after.revision,
                    payload=encode("receipt", receipt),
                )
            )
            if event is not None:
                self.conn.execute(
                    insert(EVENT).values(
                        organization_id=self.org,
                        session_id=self.session,
                        event_id=event.event_id,
                        revision=after.revision,
                        payload=encode("event", event),
                    )
                )
        except IntegrityError:
            fail("WRITE_CONFLICT")  # Enclosing UoW must roll back, no per-row commit.

    def event(self, event_id: str) -> tuple[OutcomeEvent, OutcomeAck | None] | None:
        event = cast(OutcomeEvent | None, self._read(EVENT, "event", event_id=event_id))
        if event is None:
            return None
        ack = cast(
            OutcomeAck | None,
            self._read(ACK, "ack", event_id=event_id, expected_revision=event.assignment.revision),
        )
        if ack is not None and (ack.event_id, ack.event_digest) != (event_id, event.fingerprint()):
            fail("INVALID_ACK")
        return event, ack

    def acknowledge(self, event: OutcomeEvent, ack: OutcomeAck) -> None:
        self._tx()
        encode("event", event)
        encode("ack", ack)
        original = self.event(event.event_id)
        if (
            original is None
            or original[0] != event
            or (ack.event_id, ack.event_digest) != (event.event_id, event.fingerprint())
        ):
            fail("INVALID_ACK")
        if original[1] is not None:
            if original[1] != ack:
                fail("ACK_CONFLICT")
            return
        try:
            self.conn.execute(
                insert(ACK).values(
                    organization_id=self.org,
                    session_id=self.session,
                    event_id=event.event_id,
                    revision=event.assignment.revision,
                    payload=encode("ack", ack),
                )
            )
        except IntegrityError:
            fail("WRITE_CONFLICT")


class SqlActivityStore:
    def __init__(self, engine: Engine) -> None:
        if engine.dialect.name != "postgresql":
            fail("POSTGRESQL_REQUIRED")
        self.engine = engine

    @contextmanager
    def transaction(self, organization_id: str, session_id: str) -> Iterator[ActivityRows]:
        for value in (organization_id, session_id):
            require_id(value)
        with self.engine.begin() as conn:
            conn.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:scope,0))"),
                {"scope": digest(("BE2-11.Lock/1", organization_id, session_id))},
            )
            yield ActivityRows(conn, organization_id, session_id)
