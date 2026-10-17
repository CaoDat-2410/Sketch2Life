"""Owned PostgreSQL lifecycle UoW; current policy/authority guards belong outside it."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict
from typing import Any

from sqlalchemy import Connection, Engine, insert, select, update
from sqlalchemy.exc import DBAPIError, IntegrityError

from sketch2life.application.ports.ai_policy import PolicyEvent, PolicyReceipt, PolicyTransaction
from sketch2life.domain.ai_policy.model import PolicyError, PolicyVersion, Review, State
from sketch2life.infrastructure.ai_policy.activation_sql import SqlActivationQueries
from sketch2life.infrastructure.ai_policy.tables import (
    EVENT,
    OUTBOX,
    RECEIPT,
    RECORD,
    REVIEW,
    VERSION,
)

ACTION_STATES = {
    "create": {State.DRAFT}, "edit": {State.DRAFT}, "submit_review": {State.SUBMITTED},
    "record_review": {State.SUBMITTED, State.CHANGES_REQUESTED},
    "request_changes": {State.CHANGES_REQUESTED}, "publish": {State.PUBLISHED},
    "recall": {State.RECALLED}, "archive": {State.ARCHIVED},
}


def validate_write(policy: PolicyVersion, event: PolicyEvent) -> None:
    if hashlib.sha256(policy.body_json.encode("utf-8")).hexdigest() != policy.hash:
        raise PolicyError("AI_POLICY_HASH_MISMATCH")
    action = event.kind.removeprefix("ai_policy.")
    if (not event.kind.startswith("ai_policy.") or action not in ACTION_STATES
            or policy.state not in ACTION_STATES[action]):
        raise PolicyError("AI_POLICY_INVALID_EVENT")
    if event.occurred_at.utcoffset() is None or policy.created_at.utcoffset() is None:
        raise PolicyError("AI_POLICY_INVALID_TIME")
    for proof in policy.reviews:
        if (proof.target_id, proof.target_version, proof.target_hash, proof.context_revision) != (
                policy.record_id, policy.version, policy.hash, policy.context_revision):
            raise PolicyError("AI_POLICY_REVIEW_MISMATCH")


def validate_fresh(policy: PolicyVersion) -> None:
    if (policy.state != State.DRAFT or policy.context_revision != 0 or policy.review_revision != 0
            or policy.reviews or policy.publication_review_ids
            or policy.publication_policy_version is not None or policy.recalled_at is not None
            or policy.recall_reason is not None):
        raise PolicyError("AI_POLICY_FRESH_VERSION_REQUIRED")


class SqlPolicyTransaction(SqlActivationQueries):
    def __init__(self, connection: Connection) -> None:
        self.connection = connection
        self._scope_locks: set[tuple[str, str]] = set()

    def load(self, organization_id: str, record_id: str, *, version: int | None = None,
             for_update: bool = False) -> PolicyVersion | None:
        parent = self.connection.execute(select(RECORD).where(
            RECORD.c.organization_id == organization_id, RECORD.c.record_id == record_id,
        ).with_for_update(read=not for_update)).mappings().one_or_none()
        if parent is None:
            return None
        row = self.connection.execute(select(VERSION).where(
            VERSION.c.organization_id == organization_id, VERSION.c.record_id == record_id,
            VERSION.c.version == (parent["current_version"] if version is None else version),
        )).mappings().one_or_none()
        if row is None:
            return None
        proofs: list[dict[str, Any]] = list(self.connection.execute(select(REVIEW.c.proof).where(
            REVIEW.c.organization_id == organization_id, REVIEW.c.record_id == record_id,
            REVIEW.c.version == row["version"],
            REVIEW.c.context_revision == row["context_revision"],
        ).order_by(REVIEW.c.review_revision)).scalars())
        latest = {item["dimension"]: Review(**item) for item in proofs}
        return PolicyVersion(
            record_id=record_id, organization_id=organization_id, version=row["version"],
            revision=parent["revision"], body_json=row["body_json"], hash=row["hash"],
            state=State(row["state"]), authored_by=row["authored_by"], created_at=row["created_at"],
            context_revision=row["context_revision"], review_revision=row["review_revision"],
            reviews=tuple(sorted(latest.values(), key=lambda proof: proof.review_revision)),
            publication_review_ids=tuple(row["publication_review_ids"]),
            publication_policy_version=row["publication_policy_version"],
            recalled_at=row["recalled_at"], recall_reason=row["recall_reason"])

    def review_history(self, organization_id: str, record_id: str, *, version: int,
                       after_revision: int, limit: int) -> tuple[Review, ...]:
        if (type(limit) is not int or not 1 <= limit <= 100
                or type(after_revision) is not int or after_revision < 0):
            raise PolicyError("AI_POLICY_INVALID_PAGE")
        if self.load(organization_id, record_id, version=version) is None:
            return ()
        rows: list[dict[str, Any]] = list(self.connection.execute(select(REVIEW.c.proof).where(
            REVIEW.c.organization_id == organization_id, REVIEW.c.record_id == record_id,
            REVIEW.c.version == version, REVIEW.c.review_revision > after_revision,
        ).order_by(REVIEW.c.review_revision).limit(limit)).scalars())
        return tuple(Review(**row) for row in rows)

    def save(self, policy: PolicyVersion, *, expected_revision: int | None,
             event: PolicyEvent) -> None:
        validate_write(policy, event)
        if expected_revision is not None and type(expected_revision) is not int:
            raise PolicyError("AI_POLICY_STALE_REVISION")
        values: dict[str, Any] = asdict(policy)
        values.pop("revision")
        values.pop("reviews")
        values["state"] = policy.state.value
        values["publication_review_ids"] = list(policy.publication_review_ids)
        where = (VERSION.c.organization_id == policy.organization_id,
                 VERSION.c.record_id == policy.record_id, VERSION.c.version == policy.version)
        head = 0
        if expected_revision is None:
            if policy.version != 1 or policy.revision != 1 or event.kind != "ai_policy.create":
                raise PolicyError("AI_POLICY_INVALID_VERSION")
            validate_fresh(policy)
            self.connection.execute(insert(RECORD).values(
                organization_id=policy.organization_id, record_id=policy.record_id,
                current_version=1, revision=1))
        else:
            parent = self.connection.execute(select(RECORD).where(
                RECORD.c.organization_id == policy.organization_id,
                RECORD.c.record_id == policy.record_id).with_for_update()
            ).mappings().one_or_none()
            if (parent is None or parent["revision"] != expected_revision
                    or policy.revision != expected_revision + 1):
                raise PolicyError("AI_POLICY_STALE_REVISION")
            head = parent["current_version"]
            if policy.version > head + 1:
                raise PolicyError("AI_POLICY_INVALID_VERSION")
        previous = self.connection.execute(select(VERSION).where(*where)).mappings().one_or_none()
        if previous is None:
            if policy.version != head + 1:
                raise PolicyError("AI_POLICY_INVALID_VERSION")
            validate_fresh(policy)
            if expected_revision is not None and event.kind != "ai_policy.edit":
                raise PolicyError("AI_POLICY_INVALID_EVENT")
            self.connection.execute(insert(VERSION).values(**values))
        else:
            if any(previous[name] != values[name] for name in (
                    "body_json", "hash", "authored_by", "created_at")):
                raise PolicyError("AI_POLICY_IMMUTABLE_VERSION")
            if (policy.version != head
                    and event.kind not in {"ai_policy.recall", "ai_policy.archive"}):
                raise PolicyError("AI_POLICY_SUPERSEDED_VERSION")
            self.connection.execute(update(VERSION).where(*where).values(**values))
        if expected_revision is not None:
            result = self.connection.execute(update(RECORD).where(
                RECORD.c.organization_id == policy.organization_id,
                RECORD.c.record_id == policy.record_id, RECORD.c.revision == expected_revision,
            ).values(revision=policy.revision, current_version=max(head, policy.version)))
            if result.rowcount != 1:
                raise PolicyError("AI_POLICY_STALE_REVISION")
        for proof in policy.reviews:
            existing = self.connection.execute(select(REVIEW).where(
                REVIEW.c.organization_id == policy.organization_id,
                REVIEW.c.review_id == proof.review_id)).mappings().one_or_none()
            if existing is not None:
                if (existing["record_id"], existing["version"], existing["proof"]) != (
                        policy.record_id, policy.version, asdict(proof)):
                    raise PolicyError("AI_POLICY_REVIEW_ID_CONFLICT")
            else:
                self.connection.execute(insert(REVIEW).values(
                    organization_id=policy.organization_id, review_id=proof.review_id,
                    record_id=policy.record_id, version=policy.version,
                    context_revision=proof.context_revision, review_revision=proof.review_revision,
                    dimension=proof.dimension, proof=asdict(proof)))
        payload = dict(organization_id=policy.organization_id, record_id=policy.record_id,
                       version=policy.version, revision=policy.revision, hash=policy.hash,
                       state=policy.state.value, kind=event.kind)
        self.connection.execute(insert(EVENT).values(
            organization_id=policy.organization_id, event_id=event.event_id,
            record_id=policy.record_id, version=policy.version, revision=policy.revision,
            kind=event.kind, principal_id=event.principal_id, occurred_at=event.occurred_at,
            payload=payload))
        self.connection.execute(insert(OUTBOX).values(
            organization_id=policy.organization_id, event_id=event.event_id, payload=payload))

    def receipt(self, organization_id: str, principal_id: str,
                request_id: str) -> PolicyReceipt | None:
        row = self.connection.execute(select(RECEIPT).where(
            RECEIPT.c.organization_id == organization_id, RECEIPT.c.principal_id == principal_id,
            RECEIPT.c.request_id == request_id)).mappings().one_or_none()
        return PolicyReceipt(**row) if row is not None else None

    def add_receipt(self, receipt: PolicyReceipt) -> None:
        try:
            json.loads(receipt.result_json)
        except ValueError:
            raise PolicyError("AI_POLICY_INVALID_RECEIPT") from None
        self.connection.execute(insert(RECEIPT).values(**asdict(receipt)))


class SqlPolicyStore:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    @contextmanager
    def transaction(self) -> Iterator[PolicyTransaction]:
        try:
            with self.engine.begin() as connection:
                yield SqlPolicyTransaction(connection)
        except IntegrityError:
            raise PolicyError("AI_POLICY_WRITE_CONFLICT") from None
        except DBAPIError:
            raise PolicyError("AI_POLICY_STORAGE_UNAVAILABLE") from None
