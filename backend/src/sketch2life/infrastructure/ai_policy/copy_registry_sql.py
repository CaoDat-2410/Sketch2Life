"""Own PostgreSQL inventory UoW. Current authority/discovery/deletion is NOT inferred."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import TypeAdapter
from sqlalchemy import Connection, Engine, insert, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import DBAPIError, IntegrityError

from sketch2life.application.ai_policy_commands import _digest
from sketch2life.application.ports.ai_policy_copy_registry import (
    CopyRegistryPage,
    ProviderCopyRegistryTransaction,
    RegisteredProviderCopy,
)
from sketch2life.contracts.schemas.ai_contract_candidates import OpaqueId
from sketch2life.contracts.schemas.ai_policy_copy_history import CopyInventoryEvidence
from sketch2life.contracts.schemas.ai_policy_copy_registry import (
    CopyCoverageObservation,
    CopyRegistryRegistration,
)
from sketch2life.domain.ai_policy.model import PolicyError
from sketch2life.infrastructure.ai_policy.copy_registry_tables import (
    COPY_COVERAGE,
    COPY_EVENT,
    COPY_EVIDENCE,
    COPY_REGISTRATION,
    COPY_SCOPE,
)

_ID = TypeAdapter(OpaqueId)


def _id(value: str) -> None:
    try:
        _ID.validate_python(value, strict=True)
    except (ValueError, TypeError):
        raise PolicyError("AI_POLICY_INVALID_COPY_REGISTRY_REQUEST") from None


def decode_registration(row: Mapping[Any, Any]) -> RegisteredProviderCopy:
    try:
        item = CopyRegistryRegistration.model_validate(
            {name: row[name] for name in CopyRegistryRegistration.model_fields}, strict=True
        )
        quarantine = row["initially_quarantined"]
        if type(quarantine) is not bool:
            raise ValueError("invalid registration quarantine")
        return RegisteredProviderCopy(item, quarantine)
    except (ValueError, TypeError, KeyError):
        raise PolicyError("AI_POLICY_INVALID_COPY_REGISTRY_STORAGE") from None


def validate_page(*, limit: int, after: str | None, expected_revision: int | None) -> None:
    if (
        type(limit) is not int
        or not 1 <= limit <= 256
        or (
            expected_revision is not None
            and (type(expected_revision) is not int or expected_revision < 0)
        )
        or (after is not None and expected_revision is None)
    ):
        raise PolicyError("AI_POLICY_INVALID_COPY_REGISTRY_PAGE")
    if after is not None:
        _id(after)


def decode_inventory_evidence(row: Mapping[Any, Any]) -> CopyInventoryEvidence:
    """Strict historical decode only; callers still need current read authority."""
    try:
        value = CopyInventoryEvidence.model_validate_json(json.dumps(row["record"]), strict=True)
        if (
            value.command_digest != _digest(value.command_binding())
            or (
                value.organization_id,
                value.context.scope_ref,
                value.principal_id,
                value.observed_at,
            )
            != (row["organization_id"], row["scope_ref"], row["principal_id"], row["observed_at"])
            or type(row["inventory_revision"]) is not int
            or row["inventory_revision"] < 0
        ):
            raise ValueError("invalid historical binding")
        _id(row["evidence_id"])
        return value
    except (ValueError, TypeError, KeyError):
        raise PolicyError("AI_POLICY_INVALID_COPY_EVIDENCE_STORAGE") from None


class SqlProviderCopyRegistryTransaction:
    def __init__(
        self,
        connection: Connection,
        organization_id: str,
        scope_ref: str,
        *,
        principal_id: str,
        for_update: bool,
        clock: Callable[[], datetime],
    ) -> None:
        for value in (organization_id, scope_ref, principal_id):
            _id(value)
        if type(for_update) is not bool:
            raise PolicyError("AI_POLICY_INVALID_COPY_REGISTRY_REQUEST")
        self.connection, self.organization_id, self.scope_ref = (
            connection,
            organization_id,
            scope_ref,
        )
        self.principal_id, self.writable, self.clock = principal_id, for_update, clock
        self.scope_filter = (COPY_SCOPE.c.organization_id == organization_id) & (
            COPY_SCOPE.c.scope_ref == scope_ref
        )
        if for_update:
            connection.execute(
                pg_insert(COPY_SCOPE)
                .values(
                    organization_id=organization_id,
                    scope_ref=scope_ref,
                    revision=0,
                    purging=False,
                )
                .on_conflict_do_nothing()
            )
        row = (
            connection.execute(
                select(COPY_SCOPE).where(self.scope_filter).with_for_update(read=not for_update)
            )
            .mappings()
            .one_or_none()
        )
        self.exists = row is not None
        self.revision: int = 0 if row is None else row["revision"]
        self.purging: bool = False if row is None else row["purging"]

    def _write(self) -> None:
        if not self.writable:
            raise PolicyError("AI_POLICY_COPY_REGISTRY_READ_ONLY")

    def _advance(self, kind: str, detail: dict[str, Any], *, purging: bool | None = None) -> int:
        self._write()
        now = self.clock()
        if now.utcoffset() is None:
            raise PolicyError("AI_POLICY_INVALID_TIME")
        next_revision = self.revision + 1
        next_purging = self.purging if purging is None else purging
        result = self.connection.execute(
            update(COPY_SCOPE)
            .where(
                self.scope_filter,
                COPY_SCOPE.c.revision == self.revision,
            )
            .values(revision=next_revision, purging=next_purging)
        )
        if result.rowcount != 1:
            raise PolicyError("AI_POLICY_COPY_REGISTRY_STALE")
        self.connection.execute(
            insert(COPY_EVENT).values(
                organization_id=self.organization_id,
                event_id="copy." + uuid4().hex,
                scope_ref=self.scope_ref,
                revision=next_revision,
                principal_id=self.principal_id,
                occurred_at=now,
                payload={"kind": kind} | detail,
            )
        )
        self.revision, self.purging = next_revision, next_purging
        return next_revision

    def get(self, copy_id: str) -> RegisteredProviderCopy | None:
        _id(copy_id)
        if not self.exists:
            return None
        row = (
            self.connection.execute(
                select(COPY_REGISTRATION).where(
                    COPY_REGISTRATION.c.organization_id == self.organization_id,
                    COPY_REGISTRATION.c.scope_ref == self.scope_ref,
                    COPY_REGISTRATION.c.copy_id == copy_id,
                )
            )
            .mappings()
            .one_or_none()
        )
        return None if row is None else decode_registration(row)

    def record_evidence(self, evidence: CopyInventoryEvidence) -> None:
        self._write()
        try:
            evidence = CopyInventoryEvidence.model_validate(
                evidence.model_dump(mode="python"), strict=True
            )
            if evidence.command_digest != _digest(evidence.command_binding()):
                raise ValueError("evidence command digest mismatch")
        except (TypeError, ValueError, AttributeError):
            raise PolicyError("AI_POLICY_INVALID_COPY_EVIDENCE") from None
        if (evidence.organization_id, evidence.context.scope_ref, evidence.principal_id) != (
            self.organization_id,
            self.scope_ref,
            self.principal_id,
        ):
            raise PolicyError("AI_POLICY_COPY_SCOPE_MISMATCH")
        self.connection.execute(
            insert(COPY_EVIDENCE).values(
                organization_id=self.organization_id,
                evidence_id="copy-proof." + uuid4().hex,
                scope_ref=self.scope_ref,
                principal_id=self.principal_id,
                inventory_revision=self.revision,
                observed_at=evidence.observed_at,
                record=evidence.model_dump(mode="json"),
            )
        )

    def register(self, registration: CopyRegistryRegistration) -> RegisteredProviderCopy:
        self._write()
        try:
            registration = CopyRegistryRegistration.model_validate(
                registration.model_dump(mode="python"),
                strict=True,
            )
        except (ValueError, TypeError, AttributeError):
            raise PolicyError("AI_POLICY_INVALID_COPY_REGISTRY_REQUEST") from None
        if (registration.organization_id, registration.scope_ref) != (
            self.organization_id,
            self.scope_ref,
        ):
            raise PolicyError("AI_POLICY_COPY_SCOPE_MISMATCH")
        row = (
            self.connection.execute(
                select(COPY_REGISTRATION).where(
                    COPY_REGISTRATION.c.organization_id == self.organization_id,
                    COPY_REGISTRATION.c.scope_ref == self.scope_ref,
                    COPY_REGISTRATION.c.copy_id == registration.copy_id,
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is not None:
            original = decode_registration(row)
            if original.registration != registration:
                raise PolicyError("AI_POLICY_COPY_REGISTRATION_CONFLICT")
            return original
        value = RegisteredProviderCopy(registration, self.purging)
        self._advance(
            "ai_policy.copy_registered",
            {
                "copy_id": registration.copy_id,
                "initially_quarantined": self.purging,
            },
        )
        self.connection.execute(
            insert(COPY_REGISTRATION).values(
                **registration.model_dump(mode="json"),
                initially_quarantined=self.purging,
            )
        )
        return value

    def mark_purging(self) -> int:
        self._write()
        if not self.purging:
            return self._advance("ai_policy.copy_scope_fenced", {}, purging=True)
        return self.revision

    def record_coverage(self, observation: CopyCoverageObservation) -> int:
        self._write()
        try:
            observation = CopyCoverageObservation.model_validate(
                observation.model_dump(mode="python"),
                strict=True,
            )
        except (ValueError, TypeError, AttributeError):
            raise PolicyError("AI_POLICY_INVALID_COPY_COVERAGE") from None
        if (observation.organization_id, observation.scope_ref) != (
            self.organization_id,
            self.scope_ref,
        ):
            raise PolicyError("AI_POLICY_COPY_SCOPE_MISMATCH")
        if observation.expected_revision != self.revision:
            raise PolicyError("AI_POLICY_COPY_REGISTRY_STALE")
        revision = self._advance(
            "ai_policy.copy_coverage_reported",
            {
                "attestation_ref": observation.attestation_ref.model_dump(mode="json"),
            },
        )
        self.connection.execute(
            insert(COPY_COVERAGE).values(
                organization_id=self.organization_id,
                scope_ref=self.scope_ref,
                applied_revision=revision,
                observation=observation.model_dump(mode="json"),
            )
        )
        return revision

    def page(
        self, *, limit: int, after: str | None = None, expected_revision: int | None = None
    ) -> CopyRegistryPage:
        validate_page(limit=limit, after=after, expected_revision=expected_revision)
        if expected_revision is not None and expected_revision != self.revision:
            raise PolicyError("AI_POLICY_COPY_REGISTRY_STALE")
        if not self.exists:
            # Missing-row SHARE cannot lock a future insert. Linearize this read
            # at the absence observation, never mix later inserts into revision0.
            return CopyRegistryPage(0, False, (), None, None)
        query = select(COPY_REGISTRATION).where(
            COPY_REGISTRATION.c.organization_id == self.organization_id,
            COPY_REGISTRATION.c.scope_ref == self.scope_ref,
        )
        if after is not None:
            query = query.where(COPY_REGISTRATION.c.copy_id > after)
        rows = (
            self.connection.execute(query.order_by(COPY_REGISTRATION.c.copy_id).limit(limit + 1))
            .mappings()
            .all()
        )
        records = tuple(decode_registration(row) for row in rows[:limit])
        observed = self.connection.execute(
            select(COPY_COVERAGE.c.observation).where(
                COPY_COVERAGE.c.organization_id == self.organization_id,
                COPY_COVERAGE.c.scope_ref == self.scope_ref,
                COPY_COVERAGE.c.applied_revision == self.revision,
            )
        ).scalar_one_or_none()
        coverage = None
        if observed is not None:
            try:
                coverage = CopyCoverageObservation.model_validate_json(
                    json.dumps(observed), strict=True
                )
            except (ValueError, TypeError):
                raise PolicyError("AI_POLICY_INVALID_COPY_REGISTRY_STORAGE") from None
            if coverage.expected_revision + 1 != self.revision or (
                coverage.organization_id,
                coverage.scope_ref,
            ) != (self.organization_id, self.scope_ref):
                raise PolicyError("AI_POLICY_INVALID_COPY_REGISTRY_STORAGE")
        return CopyRegistryPage(
            self.revision,
            self.purging,
            records,
            records[-1].registration.copy_id if len(rows) > limit else None,
            coverage,
        )


class SqlProviderCopyInventoryStore:
    def __init__(self, engine: Engine, *, clock: Callable[[], datetime] | None = None) -> None:
        self.engine = engine
        self.clock = clock or (lambda: datetime.now(UTC))

    @contextmanager
    def transaction(
        self, organization_id: str, scope_ref: str, *, principal_id: str, for_update: bool = False
    ) -> Iterator[ProviderCopyRegistryTransaction]:
        try:
            with self.engine.begin() as connection:
                yield SqlProviderCopyRegistryTransaction(
                    connection,
                    organization_id,
                    scope_ref,
                    principal_id=principal_id,
                    for_update=for_update,
                    clock=self.clock,
                )
        except IntegrityError:
            raise PolicyError("AI_POLICY_COPY_REGISTRY_WRITE_CONFLICT") from None
        except DBAPIError:
            raise PolicyError("AI_POLICY_COPY_REGISTRY_STORAGE_UNAVAILABLE") from None
