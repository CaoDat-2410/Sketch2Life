"""PostgreSQL-only scoped CAS/history adapter. Own locks are NOT BE1 authority."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Connection, Engine, Table, insert, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.elements import ColumnElement

from sketch2life.application.ports.preset_automation import Decision, LocalReceipt, Rows, Stored
from sketch2life.application.preset_governance import receipt_key
from sketch2life.domain.preset_automation.model import (
    EffectReceipt,
    Intent,
    IntentState,
    Library,
    State,
    fail,
    identifier,
)
from sketch2life.infrastructure.preset_automation.codec import decode, encode
from sketch2life.infrastructure.preset_automation.tables import HEAD, HISTORY


def revision(value: Stored) -> int:
    return value.revision if isinstance(value, (Library, Intent)) else 1


def validate_change(before: Stored | None, after: Stored) -> None:
    after = decode(encode(after))
    if before is None:
        if isinstance(after, Library) and (
            after.revision != 1
            or len(after.versions) != 1
            or after.versions[0].state is not State.DRAFT
            or after.action != "create"
            or after.actor != after.versions[0].author
            or after.versions[0].reviews
            or after.versions[0].publication is not None
        ):
            fail("INVALID_TRANSITION")
        if isinstance(after, Intent) and (
            after.revision != 1 or after.state not in {IntentState.QUEUED, IntentState.DEFERRED}
        ):
            fail("INVALID_TRANSITION")
        return
    if type(before) is not type(after):
        fail("INVALID_TRANSITION")
    if isinstance(before, Intent) and isinstance(after, Intent):
        if before.transition(after.state, after.disposition) != after:
            fail("INVALID_TRANSITION")
        return
    if isinstance(before, Library) and isinstance(after, Library):
        changed = [
            v
            for v in after.versions
            if v.number > len(before.versions) or v != before.versions[v.number - 1]
        ]
        if len(changed) != 1:
            fail("INVALID_TRANSITION")
        version = changed[0]
        target = len(before.versions) if after.action == "edit" else version.number
        if target > len(before.versions):
            fail("INVALID_TRANSITION")
        old = before.versions[target - 1]
        new_reviews = [r for r in version.reviews if r not in old.reviews]
        reconstructed = before.change(
            after.action,
            before.revision,
            target,
            old.body.hash,
            after.actor,
            after.changed_at,
            body=version.body,
            review=new_reviews[0] if len(new_reviews) == 1 else None,
            publication=version.publication,
            why=after.reason,
        )
        if reconstructed != after:
            fail("INVALID_TRANSITION")
        return
    fail("IMMUTABLE_ROW")


class PresetRows:
    def __init__(self, conn: Connection, organization_id: str, scope: str) -> None:
        if conn.dialect.name != "postgresql":
            fail("POSTGRESQL_REQUIRED")
        identifier(organization_id)
        identifier(scope)
        self.conn, self.org, self.scope = conn, organization_id, scope

    def _bind(self, key: str, value: Stored) -> None:
        identifier(key)
        if isinstance(value, Library):
            if (
                value.organization_id != self.org
                or self.scope != "library"
                or key != value.record_id
            ):
                fail("STORAGE_CORRUPT")
        elif isinstance(value, (Intent, EffectReceipt)):
            expected = value.intent_id if isinstance(value, Intent) else "effect-" + value.intent_id
            if (value.organization_id, value.session_id, expected) != (self.org, self.scope, key):
                fail("STORAGE_CORRUPT")
        elif isinstance(value, Decision):
            if (value.organization_id, value.session_id, value.decision_id) != (
                self.org,
                self.scope,
                key,
            ):
                fail("STORAGE_CORRUPT")
        elif isinstance(value, LocalReceipt) and key != receipt_key(value.actor, value.client_key):
            fail("STORAGE_CORRUPT")

    def _where(self, key: str, table: Table = HEAD) -> tuple[ColumnElement[bool], ...]:
        if not self.conn.in_transaction():
            fail("TRANSACTION_REQUIRED")
        identifier(key)
        return (
            table.c.organization_id == self.org,
            table.c.scope == self.scope,
            table.c.object_key == key,
        )

    def _load(self, key: str, rev: int | None) -> Stored | None:
        table = HEAD if rev is None else HISTORY
        filters = self._where(key, table)
        if rev is not None:
            filters = (*filters, table.c.revision == rev)
        row = self.conn.execute(select(table).where(*filters)).mappings().one_or_none()
        if row is None:
            return None
        value = decode(row["payload"])
        self._bind(key, value)
        if revision(value) != row["revision"] or (rev is not None and row["revision"] != rev):
            fail("STORAGE_CORRUPT")
        return value

    def get(self, key: str) -> Stored | None:
        return self._load(key, None)

    def history(self, key: str, revision: int) -> Stored | None:
        return self._load(key, revision)

    def put(self, key: str, before: Stored | None, value: Stored) -> None:
        self._where(key)
        self._bind(key, value)
        validate_change(before, value)
        if self.get(key) != before:
            fail("STALE_REVISION")
        if isinstance(value, LocalReceipt):
            snapshot = self.history(value.object_key, value.applied_revision)
            if (
                snapshot is None
                or revision(snapshot) != value.applied_revision
                or isinstance(snapshot, (LocalReceipt, EffectReceipt, Decision))
            ):
                fail("STORAGE_CORRUPT")
            if isinstance(snapshot, Library) and value.target_version > len(snapshot.versions):
                fail("STORAGE_CORRUPT")
            if snapshot.actor != value.actor:
                fail("STORAGE_CORRUPT")
        if isinstance(value, EffectReceipt):
            intent = self.get(value.intent_id)
            if not isinstance(intent, Intent) or intent.state is not IntentState.SENDING:
                fail("INVALID_RECEIPT")
            value.validate_for(intent)
        if (
            isinstance(value, Intent)
            and value.state in {IntentState.APPLIED, IntentState.REJECTED}
            or (
                isinstance(value, Intent)
                and value.state is IntentState.STALE
                and isinstance(before, Intent)
                and before.state is IntentState.SENDING
            )
        ):
            effect = self.get("effect-" + value.intent_id)
            if not isinstance(effect, EffectReceipt) or effect.outcome != value.state.value:
                fail("INVALID_RECEIPT")
            effect.validate_for(value)
        if isinstance(value, Decision) and value.intent_id is not None:
            queued = self.get(value.intent_id)
            if (
                not isinstance(queued, Intent)
                or queued.source != value.source
                or queued.observed != value.observed
                or queued.actor != value.actor
                or queued.state.value != value.outcome
            ):
                fail("STORAGE_CORRUPT")
        data = dict(
            organization_id=self.org,
            scope=self.scope,
            object_key=key,
            revision=revision(value),
            payload=encode(value),
        )
        if before is None:
            self.conn.execute(insert(HEAD).values(**data))
        else:
            result = self.conn.execute(
                update(HEAD)
                .where(*self._where(key), HEAD.c.revision == revision(before))
                .values(revision=revision(value), payload=encode(value))
            )
            if result.rowcount != 1:
                fail("STALE_REVISION")
        self.conn.execute(insert(HISTORY).values(**data))


class SqlPresetStore:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    @contextmanager
    def transaction(self, organization_id: str, scope: str) -> Iterator[Rows]:
        identifier(organization_id)
        identifier(scope)
        try:
            with self.engine.begin() as conn:
                if conn.dialect.name != "postgresql":
                    fail("POSTGRESQL_REQUIRED")
                conn.execute(
                    text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
                    {"key": "be2-13:" + organization_id + ":" + scope},
                )
                yield PresetRows(conn, organization_id, scope)
        except IntegrityError:
            fail("STALE_REVISION")
