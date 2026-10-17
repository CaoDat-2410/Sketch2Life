"""Transactional content storage. No access to BE1 or ai_jobs tables."""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict
from typing import Any

from sqlalchemy import Connection, Engine, insert, select, update
from sqlalchemy.exc import IntegrityError

from sketch2life.application.ports.learning_content import (
    ContentEvent,
    ContentReceipt,
    ContentTransaction,
)
from sketch2life.domain.learning_content.model import (
    ContentError,
    ContentState,
    ContentVersion,
    ReviewProof,
    content_hash,
)
from sketch2life.infrastructure.learning_content.tables import (
    EVENT,
    OUTBOX,
    RECEIPT,
    RECORD,
    REVIEW,
    VERSION,
)


class SqlContentTransaction:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def load(self, organization_id: str, record_id: str, *, version: int | None = None,
             for_update: bool = False) -> ContentVersion | None:
        query = select(RECORD).where(
            RECORD.c.organization_id == organization_id, RECORD.c.record_id == record_id)
        # Shared readers retain the record boundary while loading its version/
        # reviews. Writers request UPDATE from the beginning, avoiding lock upgrades.
        query = query.with_for_update(read=not for_update)
        record = self.connection.execute(query).mappings().one_or_none()
        if record is None:
            return None
        row = self.connection.execute(select(VERSION).where(
            VERSION.c.organization_id == organization_id, VERSION.c.record_id == record_id,
            VERSION.c.version == (version if version is not None else record["current_version"])
        )).mappings().one_or_none()
        if row is None:
            return None
        proofs: list[dict[str, Any]] = list(self.connection.execute(select(REVIEW.c.proof).where(
            REVIEW.c.organization_id == organization_id, REVIEW.c.record_id == record_id,
            REVIEW.c.version == row["version"],
            REVIEW.c.context_revision == row["context_revision"],
        ).order_by(REVIEW.c.review_revision)).scalars())
        latest = {p["dimension"]: ReviewProof(**p) for p in proofs}
        return ContentVersion(
            record_id=record_id, organization_id=organization_id, version=row["version"],
            revision=record["revision"], body_json=row["body_json"], hash=row["hash"],
            state=ContentState(row["state"]), authored_by=row["authored_by"],
            created_at=row["created_at"], context_revision=row["context_revision"],
            review_revision=row["review_revision"], reviews=tuple(latest.values()),
            publication_review_ids=tuple(row["publication_review_ids"]),
            publication_policy_version=row["publication_policy_version"],
            recalled_at=row["recalled_at"], recall_reason=row["recall_reason"])

    def save(self, content: ContentVersion, *, expected_revision: int | None,
             event: ContentEvent) -> None:
        if content_hash(content.body_json) != content.hash:
            raise ContentError("CONTENT_HASH_MISMATCH")
        values: dict[str, Any] = asdict(content)
        values.pop("revision")
        values.pop("reviews")
        values["state"] = content.state.value
        values["publication_review_ids"] = list(content.publication_review_ids)
        where = (VERSION.c.organization_id == content.organization_id,
                 VERSION.c.record_id == content.record_id, VERSION.c.version == content.version)
        current_version = 0
        if expected_revision is None:
            if content.version != 1 or content.revision != 1:
                raise ContentError("CONTENT_INVALID_VERSION")
            self.connection.execute(insert(RECORD).values(
                organization_id=content.organization_id, record_id=content.record_id,
                current_version=1, revision=1))
        else:
            record = self.connection.execute(select(RECORD).where(
                RECORD.c.organization_id == content.organization_id,
                RECORD.c.record_id == content.record_id).with_for_update()
            ).mappings().one_or_none()
            if (record is None or record["revision"] != expected_revision
                    or content.revision != expected_revision + 1):
                raise ContentError("CONTENT_STALE_REVISION")
            if content.version > record["current_version"] + 1:
                raise ContentError("CONTENT_INVALID_VERSION")
            current_version = record["current_version"]
            self.connection.execute(update(RECORD).where(
                RECORD.c.organization_id == content.organization_id,
                RECORD.c.record_id == content.record_id,
                RECORD.c.revision == expected_revision).values(
                    revision=content.revision,
                    current_version=max(record["current_version"], content.version)))
        previous = self.connection.execute(select(VERSION).where(*where)).mappings().one_or_none()
        if previous is None:
            if expected_revision is not None and content.version != current_version + 1:
                raise ContentError("CONTENT_INVALID_VERSION")
            self.connection.execute(insert(VERSION).values(**values))
        else:
            for immutable in ("body_json", "hash", "authored_by", "created_at"):
                if previous[immutable] != values[immutable]:
                    raise ContentError("CONTENT_IMMUTABLE_VERSION")
            self.connection.execute(update(VERSION).where(*where).values(**values))
        for proof in content.reviews:
            existing = self.connection.execute(select(REVIEW.c.proof).where(
                REVIEW.c.organization_id == content.organization_id,
                REVIEW.c.review_id == proof.review_id)).scalar_one_or_none()
            if existing is not None:
                if existing != asdict(proof):
                    raise ContentError("CONTENT_REVIEW_ID_CONFLICT")
            else:
                self.connection.execute(insert(REVIEW).values(
                    organization_id=content.organization_id, review_id=proof.review_id,
                    record_id=content.record_id, version=content.version,
                    context_revision=content.context_revision,
                    review_revision=proof.review_revision,
                    dimension=proof.dimension, proof=asdict(proof)))
        if event.occurred_at.tzinfo is None:
            raise ContentError("CONTENT_INVALID_TIME")
        payload = {"record_id": content.record_id, "organization_id": content.organization_id,
                   "version": content.version, "revision": content.revision,
                   "hash": content.hash, "state": content.state.value, "kind": event.kind}
        self.connection.execute(insert(EVENT).values(
            event_id=event.event_id, organization_id=content.organization_id,
            record_id=content.record_id, version=content.version, revision=content.revision,
            kind=event.kind, principal_id=event.principal_id, occurred_at=event.occurred_at,
            payload=payload))
        self.connection.execute(insert(OUTBOX).values(
            event_id=event.event_id, organization_id=content.organization_id, payload=payload))

    def receipt(self, organization_id: str, principal_id: str,
                request_id: str) -> ContentReceipt | None:
        row = self.connection.execute(select(RECEIPT).where(
            RECEIPT.c.organization_id == organization_id, RECEIPT.c.principal_id == principal_id,
            RECEIPT.c.request_id == request_id)).mappings().one_or_none()
        return ContentReceipt(**row) if row is not None else None

    def add_receipt(self, receipt: ContentReceipt) -> None:
        # Validate JSON before writing; shared transaction makes the receipt
        # atomic with lifecycle/history/outbox and DB uniqueness handles races.
        json.loads(receipt.result_json)
        self.connection.execute(insert(RECEIPT).values(**asdict(receipt)))


class SqlContentStore:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    @contextmanager
    def transaction(self) -> Iterator[ContentTransaction]:
        try:
            with self.engine.begin() as connection:
                yield SqlContentTransaction(connection)
        except IntegrityError:
            # Roll back the whole candidate before the caller retries/reads
            # an idempotency winner in a fresh transaction.
            raise ContentError("CONTENT_WRITE_CONFLICT") from None
