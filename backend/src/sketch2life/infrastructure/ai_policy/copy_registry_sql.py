"""Own PostgreSQL inventory UoW. Current authority/discovery/deletion is NOT inferred."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import TypeAdapter
from sqlalchemy import Connection, DateTime, Engine, and_, insert, or_, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import DBAPIError, IntegrityError

from sketch2life.application.ai_policy_commands import _digest
from sketch2life.application.ai_policy_copy_delivery_evidence import validate_delivery_evidence
from sketch2life.application.ai_policy_copy_operations import (
    validate_operation,
    validate_operation_authorization,
)
from sketch2life.application.ai_policy_copy_resolution import resolution_key, validate_resolution
from sketch2life.application.ports.ai_policy_copy_registry import (
    CopyCandidatePage,
    CopyOperationPage,
    CopyRegistryPage,
    ProviderCopyRegistryTransaction,
    RegisteredProviderCopy,
)
from sketch2life.contracts.schemas.ai_contract_candidates import OpaqueId
from sketch2life.contracts.schemas.ai_policy_copy_candidates import (
    CopyCandidateCursor,
    CopyCandidateRequest,
)
from sketch2life.contracts.schemas.ai_policy_copy_delivery import CopyDeliveryAuthorityEvidence
from sketch2life.contracts.schemas.ai_policy_copy_history import CopyInventoryEvidence
from sketch2life.contracts.schemas.ai_policy_copy_lifecycle import (
    CopyLifecycleRecord,
    CopyResolutionObservation,
)
from sketch2life.contracts.schemas.ai_policy_copy_operation import (
    CopyOperationAuthorization,
    CopyOperationEnvelope,
)
from sketch2life.contracts.schemas.ai_policy_copy_registry import (
    CopyCoverageObservation,
    CopyRegistryRegistration,
)
from sketch2life.domain.ai_policy.copy_delivery import (
    DeliveryResponse,
    DeliveryState,
    claim_delivery,
    finish_delivery,
)
from sketch2life.domain.ai_policy.model import PolicyError
from sketch2life.infrastructure.ai_policy.copy_delivery_codec import (
    decode_delivery,
    encode_delivery,
)
from sketch2life.infrastructure.ai_policy.copy_registry_tables import (
    COPY_COVERAGE,
    COPY_DELIVERY,
    COPY_DELIVERY_AUTHORITY,
    COPY_DELIVERY_HISTORY,
    COPY_EVENT,
    COPY_EVIDENCE,
    COPY_LIFECYCLE,
    COPY_OPERATION,
    COPY_OPERATION_AUTHORITY,
    COPY_REGISTRATION,
    COPY_RESOLUTION,
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

    def get_copy_lifecycle(self, copy_id: str) -> CopyLifecycleRecord:
        original = self.get(copy_id)
        if original is None:
            raise PolicyError("AI_POLICY_COPY_NOT_FOUND")
        row = (
            self.connection.execute(
                select(COPY_LIFECYCLE).where(
                    COPY_LIFECYCLE.c.organization_id == self.organization_id,
                    COPY_LIFECYCLE.c.scope_ref == self.scope_ref,
                    COPY_LIFECYCLE.c.copy_id == copy_id,
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return CopyLifecycleRecord(
                registration=original.registration,
                revision=0,
                status="purge_requested"
                if self.purging or original.initially_quarantined
                else "discovered",
            )
        try:
            record = CopyLifecycleRecord.model_validate_json(
                json.dumps(row["snapshot"]), strict=True
            )
            if (
                record.registration != original.registration
                or record.revision != row["revision"]
                or record.revision == 0
            ):
                raise ValueError("lifecycle storage mismatch")
            history = (
                self.connection.execute(
                    select(COPY_RESOLUTION.c.resolution_key, COPY_RESOLUTION.c.after_state).where(
                        COPY_RESOLUTION.c.organization_id == self.organization_id,
                        COPY_RESOLUTION.c.scope_ref == self.scope_ref,
                        COPY_RESOLUTION.c.copy_id == copy_id,
                        COPY_RESOLUTION.c.revision == record.revision,
                    )
                )
                .mappings()
                .one_or_none()
            )
            if history is None or history["after_state"] != record.model_dump(mode="json"):
                raise ValueError("lifecycle lacks matching immutable history")
            if self.get_resolution(history["resolution_key"]) is None:
                raise ValueError("missing validated resolution")
            return record
        except (TypeError, ValueError):
            raise PolicyError("AI_POLICY_INVALID_COPY_LIFECYCLE_STORAGE") from None

    def get_resolution(self, key: str) -> CopyResolutionObservation | None:
        if (
            not isinstance(key, str)
            or len(key) != 64
            or any(c not in "0123456789abcdef" for c in key)
        ):
            raise PolicyError("AI_POLICY_INVALID_COPY_RESOLUTION")
        row = (
            self.connection.execute(
                select(COPY_RESOLUTION).where(
                    COPY_RESOLUTION.c.organization_id == self.organization_id,
                    COPY_RESOLUTION.c.scope_ref == self.scope_ref,
                    COPY_RESOLUTION.c.resolution_key == key,
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        try:
            before = CopyLifecycleRecord.model_validate_json(
                json.dumps(row["before_state"]), strict=True
            )
            after = CopyLifecycleRecord.model_validate_json(
                json.dumps(row["after_state"]), strict=True
            )
            observation = CopyResolutionObservation.model_validate_json(
                json.dumps(row["observation"]), strict=True
            )
            validate_resolution(before, after, observation)
            if (
                self.get_operation(observation.binding.envelope.operation_key)
                != observation.binding.envelope
            ):
                raise ValueError("resolution differs from original operation")
            if resolution_key(observation) != key or (
                after.registration.organization_id,
                after.registration.scope_ref,
                after.registration.copy_id,
                after.revision,
                observation.binding.envelope.operation_key,
            ) != (
                self.organization_id,
                self.scope_ref,
                row["copy_id"],
                row["revision"],
                row["operation_key"],
            ):
                raise ValueError("resolution storage mismatch")
            return observation
        except (TypeError, ValueError, PolicyError):
            raise PolicyError("AI_POLICY_INVALID_COPY_RESOLUTION_STORAGE") from None

    def save_resolution(
        self,
        before: CopyLifecycleRecord,
        after: CopyLifecycleRecord,
        observation: CopyResolutionObservation,
    ) -> None:
        self._write()
        observation = validate_resolution(before, after, observation)
        envelope = observation.binding.envelope
        item = after.registration
        if (item.organization_id, item.scope_ref, envelope.principal_id) != (
            self.organization_id,
            self.scope_ref,
            self.principal_id,
        ):
            raise PolicyError("AI_POLICY_COPY_SCOPE_MISMATCH")
        if (
            self.get_operation(envelope.operation_key) != envelope
            or self.get_copy_lifecycle(item.copy_id) != before
        ):
            raise PolicyError("AI_POLICY_COPY_LIFECYCLE_STALE")
        delivery = self.get_delivery(envelope.operation_key)
        if (
            delivery.revision != observation.binding.delivery_revision
            or delivery.last_response is None
            or (
                delivery.status.value != "receipt_available"
                or delivery.last_response.reference != observation.binding.reference.ref
                or delivery.last_response.reference_hash != observation.binding.reference.hash
            )
        ):
            raise PolicyError("AI_POLICY_COPY_DELIVERY_STALE")
        scope = dict(
            organization_id=self.organization_id, scope_ref=self.scope_ref, copy_id=item.copy_id
        )
        if before.revision == 0:
            self.connection.execute(
                insert(COPY_LIFECYCLE).values(
                    **scope, revision=after.revision, snapshot=after.model_dump(mode="json")
                )
            )
        else:
            result = self.connection.execute(
                update(COPY_LIFECYCLE)
                .where(
                    COPY_LIFECYCLE.c.organization_id == self.organization_id,
                    COPY_LIFECYCLE.c.scope_ref == self.scope_ref,
                    COPY_LIFECYCLE.c.copy_id == item.copy_id,
                    COPY_LIFECYCLE.c.revision == before.revision,
                )
                .values(revision=after.revision, snapshot=after.model_dump(mode="json"))
            )
            if result.rowcount != 1:
                raise PolicyError("AI_POLICY_COPY_LIFECYCLE_STALE")
        self.connection.execute(
            insert(COPY_RESOLUTION).values(
                **scope,
                resolution_key=resolution_key(observation),
                operation_key=envelope.operation_key,
                revision=after.revision,
                before_state=before.model_dump(mode="json"),
                after_state=after.model_dump(mode="json"),
                observation=observation.model_dump(mode="json"),
            )
        )
        self._advance(
            "ai_policy.copy_receipt_resolved",
            {
                "copy_id": item.copy_id,
                "operation_key": envelope.operation_key,
                "copy_revision": after.revision,
            },
        )

    def record_delivery_authority(self, evidence: CopyDeliveryAuthorityEvidence) -> None:
        self._write()
        try:
            evidence = CopyDeliveryAuthorityEvidence.model_validate(
                evidence.model_dump(mode="python"), strict=True
            )
        except (ValueError, TypeError, AttributeError):
            raise PolicyError("AI_POLICY_INVALID_DELIVERY_AUTHORITY_EVIDENCE") from None
        if (evidence.organization_id, evidence.scope_ref, evidence.principal_id) != (
            self.organization_id,
            self.scope_ref,
            self.principal_id,
        ):
            raise PolicyError("AI_POLICY_COPY_SCOPE_MISMATCH")
        envelope = self.get_operation(evidence.operation_key)
        if envelope is None:
            raise PolicyError("AI_POLICY_COPY_OPERATION_NOT_FOUND")
        if evidence.state_revision == 0:
            before = DeliveryState(envelope.operation_key, envelope.binding_digest)
        else:
            snapshot = self.connection.execute(
                select(COPY_DELIVERY_HISTORY.c.snapshot).where(
                    COPY_DELIVERY_HISTORY.c.organization_id == self.organization_id,
                    COPY_DELIVERY_HISTORY.c.scope_ref == self.scope_ref,
                    COPY_DELIVERY_HISTORY.c.operation_key == evidence.operation_key,
                    COPY_DELIVERY_HISTORY.c.revision == evidence.state_revision,
                )
            ).scalar_one_or_none()
            if snapshot is None:
                raise PolicyError("AI_POLICY_INVALID_DELIVERY_AUTHORITY_EVIDENCE")
            before = decode_delivery(snapshot)
        evidence = validate_delivery_evidence(
            evidence, envelope, before, self.get_delivery(evidence.operation_key)
        )
        self.connection.execute(
            insert(COPY_DELIVERY_AUTHORITY).values(
                organization_id=self.organization_id,
                scope_ref=self.scope_ref,
                operation_key=evidence.operation_key,
                evidence_id="delivery-proof." + uuid4().hex,
                evidence=evidence.model_dump(mode="json"),
            )
        )
        self._advance(
            "ai_policy.copy_delivery_authorized",
            {
                "operation_key": evidence.operation_key,
                "phase": evidence.phase,
                "delivery_revision": self.get_delivery(evidence.operation_key).revision,
            },
        )

    def get_delivery(self, operation_key: str) -> DeliveryState:
        operation = self.get_operation(operation_key)
        if operation is None:
            raise PolicyError("AI_POLICY_COPY_OPERATION_NOT_FOUND")
        row = (
            self.connection.execute(
                select(COPY_DELIVERY).where(
                    COPY_DELIVERY.c.organization_id == self.organization_id,
                    COPY_DELIVERY.c.scope_ref == self.scope_ref,
                    COPY_DELIVERY.c.operation_key == operation_key,
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return DeliveryState(operation_key, operation.binding_digest)
        state = decode_delivery(row["snapshot"])
        if (state.operation_key, state.binding_digest, state.revision, state.status.value) != (
            operation_key,
            operation.binding_digest,
            row["revision"],
            row["status"],
        ) or state.revision == 0:
            raise PolicyError("AI_POLICY_INVALID_COPY_DELIVERY_STORAGE")
        return state

    def _store_delivery(self, old: DeliveryState, new: DeliveryState) -> DeliveryState:
        self._write()
        if old == new:
            return old
        values = dict(revision=new.revision, status=new.status.value, snapshot=encode_delivery(new))
        scope = dict(
            organization_id=self.organization_id,
            scope_ref=self.scope_ref,
            operation_key=new.operation_key,
        )
        if old.revision == 0:
            self.connection.execute(insert(COPY_DELIVERY).values(**scope, **values))
        else:
            result = self.connection.execute(
                update(COPY_DELIVERY)
                .where(
                    COPY_DELIVERY.c.organization_id == self.organization_id,
                    COPY_DELIVERY.c.scope_ref == self.scope_ref,
                    COPY_DELIVERY.c.operation_key == new.operation_key,
                    COPY_DELIVERY.c.revision == old.revision,
                )
                .values(**values)
            )
            if result.rowcount != 1:
                raise PolicyError("AI_POLICY_COPY_DELIVERY_STALE")
        self.connection.execute(
            insert(COPY_DELIVERY_HISTORY).values(
                **scope, revision=new.revision, snapshot=values["snapshot"]
            )
        )
        self._advance(
            "ai_policy.copy_delivery_changed",
            {
                "operation_key": new.operation_key,
                "delivery_revision": new.revision,
                "delivery_status": new.status.value,
            },
        )
        return new

    def claim_delivery(
        self, operation_key: str, *, expected_revision: int, token: str, expires_at: datetime
    ) -> DeliveryState:
        self._write()
        old = self.get_delivery(operation_key)
        new = claim_delivery(
            old,
            expected_revision=expected_revision,
            token=token,
            now=self.clock(),
            expires_at=expires_at,
        )
        return self._store_delivery(old, new)

    def finish_delivery(
        self, response: DeliveryResponse, *, expected_revision: int, token: str
    ) -> DeliveryState:
        self._write()
        if not isinstance(response, DeliveryResponse):
            raise PolicyError("AI_POLICY_INVALID_COPY_DELIVERY")
        old = self.get_delivery(response.operation_key)
        new = finish_delivery(
            old, response, expected_revision=expected_revision, token=token, now=self.clock()
        )
        return self._store_delivery(old, new)

    def operation_page(
        self, *, limit: int, after: str | None = None, expected_revision: int | None = None
    ) -> CopyOperationPage:
        validate_page(limit=limit, after=after, expected_revision=expected_revision)
        if after is not None and (
            len(after) != 64 or any(char not in "0123456789abcdef" for char in after)
        ):
            raise PolicyError("AI_POLICY_INVALID_COPY_OPERATION")
        if expected_revision is not None and expected_revision != self.revision:
            raise PolicyError("AI_POLICY_COPY_REGISTRY_STALE")
        if not self.exists:
            return CopyOperationPage(0, (), None)
        query = select(COPY_OPERATION.c.operation_key).where(
            COPY_OPERATION.c.organization_id == self.organization_id,
            COPY_OPERATION.c.scope_ref == self.scope_ref,
        )
        if after is not None:
            query = query.where(COPY_OPERATION.c.operation_key > after)
        keys: tuple[str, ...] = tuple(
            self.connection.execute(
                query.order_by(COPY_OPERATION.c.operation_key).limit(limit + 1)
            ).scalars()
        )
        if any(
            not isinstance(key, str)
            or len(key) != 64
            or any(char not in "0123456789abcdef" for char in key)
            for key in keys
        ) or keys != tuple(sorted(set(keys))):
            raise PolicyError("AI_POLICY_INVALID_COPY_OPERATION_STORAGE")
        if after is not None and any(key <= after for key in keys):
            raise PolicyError("AI_POLICY_INVALID_COPY_OPERATION_STORAGE")
        return CopyOperationPage(
            self.revision, keys[:limit], keys[limit - 1] if len(keys) > limit else None
        )

    def delivery_candidates(self, request: CopyCandidateRequest) -> CopyCandidatePage:
        try:
            request = CopyCandidateRequest.model_validate(
                request.model_dump(mode="python"), strict=True
            )
        except (ValueError, TypeError, AttributeError):
            raise PolicyError("AI_POLICY_INVALID_COPY_CANDIDATE_REQUEST") from None
        cursor = request.cursor
        if cursor is not None and (cursor.organization_id, cursor.scope_ref) != (
            self.organization_id,
            self.scope_ref,
        ):
            raise PolicyError("AI_POLICY_COPY_SCOPE_MISMATCH")
        if cursor is not None and cursor.revision != self.revision:
            raise PolicyError("AI_POLICY_COPY_REGISTRY_STALE")
        as_of = cursor.as_of if cursor is not None else request.as_of
        assert as_of is not None
        after = cursor.after if cursor is not None else None
        if not self.exists:
            return CopyCandidatePage(0, as_of, (), None)
        join = COPY_OPERATION.outerjoin(
            COPY_DELIVERY,
            and_(
                COPY_OPERATION.c.organization_id == COPY_DELIVERY.c.organization_id,
                COPY_OPERATION.c.scope_ref == COPY_DELIVERY.c.scope_ref,
                COPY_OPERATION.c.operation_key == COPY_DELIVERY.c.operation_key,
            ),
        )
        query = (
            select(COPY_OPERATION.c.operation_key)
            .select_from(join)
            .where(
                COPY_OPERATION.c.organization_id == self.organization_id,
                COPY_OPERATION.c.scope_ref == self.scope_ref,
                or_(
                    COPY_DELIVERY.c.operation_key.is_(None),
                    COPY_DELIVERY.c.status.in_(("pending", "exception")),
                    and_(
                        COPY_DELIVERY.c.status == "in_flight",
                        COPY_DELIVERY.c.snapshot["claim_expires_at"].astext.cast(
                            DateTime(timezone=True)
                        )
                        <= as_of,
                    ),
                ),
            )
        )
        if after is not None:
            query = query.where(COPY_OPERATION.c.operation_key > after)
        keys: tuple[str, ...] = tuple(
            self.connection.execute(
                query.order_by(COPY_OPERATION.c.operation_key).limit(request.limit + 1)
            ).scalars()
        )
        if (
            any(
                not isinstance(key, str)
                or len(key) != 64
                or any(char not in "0123456789abcdef" for char in key)
                for key in keys
            )
            or keys != tuple(sorted(set(keys)))
            or (after is not None and any(k <= after for k in keys))
        ):
            raise PolicyError("AI_POLICY_INVALID_COPY_OPERATION_STORAGE")
        continuation = (
            CopyCandidateCursor(
                organization_id=self.organization_id,
                scope_ref=self.scope_ref,
                revision=self.revision,
                as_of=as_of,
                after=keys[request.limit - 1],
            )
            if len(keys) > request.limit
            else None
        )
        return CopyCandidatePage(self.revision, as_of, keys[: request.limit], continuation)

    def get_operation(self, operation_key: str) -> CopyOperationEnvelope | None:
        # Digest syntax, not an arbitrary DB selector or provider operation alias.
        if (
            not isinstance(operation_key, str)
            or len(operation_key) != 64
            or any(char not in "0123456789abcdef" for char in operation_key)
        ):
            raise PolicyError("AI_POLICY_INVALID_COPY_OPERATION")
        if not self.exists:
            return None
        row = (
            self.connection.execute(
                select(COPY_OPERATION).where(
                    COPY_OPERATION.c.organization_id == self.organization_id,
                    COPY_OPERATION.c.scope_ref == self.scope_ref,
                    COPY_OPERATION.c.operation_key == operation_key,
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        try:
            envelope = validate_operation(
                CopyOperationEnvelope.model_validate_json(json.dumps(row["envelope"]), strict=True)
            )
            if (
                envelope.organization_id,
                envelope.command.scope_ref,
                envelope.operation_key,
                envelope.target.copy_id,
            ) != (row["organization_id"], row["scope_ref"], row["operation_key"], row["copy_id"]):
                raise ValueError("stored operation binding mismatch")
            return envelope
        except (ValueError, TypeError, KeyError, PolicyError):
            raise PolicyError("AI_POLICY_INVALID_COPY_OPERATION_STORAGE") from None

    def enqueue_operation(
        self, envelope: CopyOperationEnvelope, authorization: CopyOperationAuthorization
    ) -> CopyOperationEnvelope:
        self._write()
        envelope = validate_operation(envelope)
        authorization = validate_operation_authorization(envelope, authorization)
        if (envelope.organization_id, envelope.command.scope_ref, envelope.principal_id) != (
            self.organization_id,
            self.scope_ref,
            self.principal_id,
        ):
            raise PolicyError("AI_POLICY_COPY_SCOPE_MISMATCH")
        original_copy = self.get(envelope.target.copy_id)
        if original_copy is None or original_copy.registration != envelope.target:
            raise PolicyError("AI_POLICY_COPY_REGISTRATION_CONFLICT")
        original = self.get_operation(envelope.operation_key)
        if original is not None and original.binding_digest != envelope.binding_digest:
            raise PolicyError("AI_POLICY_COPY_OPERATION_CONFLICT")
        if original is None:
            if envelope.command.operation == "purge":
                self.mark_purging()
            self._advance(
                "ai_policy.copy_operation_queued",
                {
                    "operation_key": envelope.operation_key,
                    "copy_id": envelope.target.copy_id,
                    "operation": envelope.command.operation,
                },
            )
            self.connection.execute(
                insert(COPY_OPERATION).values(
                    organization_id=self.organization_id,
                    scope_ref=self.scope_ref,
                    operation_key=envelope.operation_key,
                    copy_id=envelope.target.copy_id,
                    envelope=envelope.model_dump(mode="json"),
                )
            )
        self.connection.execute(
            insert(COPY_OPERATION_AUTHORITY).values(
                organization_id=self.organization_id,
                observation_id="copy-op-proof." + uuid4().hex,
                scope_ref=self.scope_ref,
                operation_key=envelope.operation_key,
                observation=authorization.model_dump(mode="json"),
            )
        )
        return original or envelope

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
