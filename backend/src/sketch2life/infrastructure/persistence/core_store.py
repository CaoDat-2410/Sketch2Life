"""PostgreSQL repositories and the atomic BE1-02 mutation unit-of-work."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, cast
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from sketch2life.application.ports.core_foundation import (
    CanvasCheckpointMetadata,
    CanvasMutationCommit,
    CanvasOperationRecord,
    CoreAssetMetadata,
    CoreAuditRecord,
)
from sketch2life.domain.core_foundation import CanvasOperation, IdempotencyReceipt
from sketch2life.domain.eligibility import (
    PROOF_VERSION,
    EligibilityScope,
    ProvisionalDataOrigin,
    SyntheticEligibilityProof,
)
from sketch2life.infrastructure.persistence.be1_models import (
    ManagedProfileModel,
    SyntheticEligibilityProofModel,
)
from sketch2life.infrastructure.persistence.core_models import (
    CoreAggregateRevisionModel,
    CoreAssetMetadataModel,
    CoreAuditEntryModel,
    CoreCanvasCheckpointModel,
    CoreCanvasOperationModel,
    CoreIdempotencyReceiptModel,
    CoreOutboxEventModel,
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def load_profile_origin(
    db: Session, *, organization_id: str, class_id: str, child_id: str
) -> str | None:
    """Return the stored origin of an active profile, or None when it is not found."""
    return db.scalar(
        select(ManagedProfileModel.data_origin).where(
            ManagedProfileModel.organization_id == organization_id,
            ManagedProfileModel.class_id == class_id,
            ManagedProfileModel.child_id == child_id,
            ManagedProfileModel.state == "active",
        )
    )


def load_synthetic_proof(
    db: Session, *, organization_id: str, class_id: str, child_id: str, purpose_ref: str
) -> SyntheticEligibilityProof | None:
    """Return the most recently issued proof for the exact scope; absence means no proof."""
    row = db.scalar(
        select(SyntheticEligibilityProofModel)
        .where(
            SyntheticEligibilityProofModel.organization_id == organization_id,
            SyntheticEligibilityProofModel.class_id == class_id,
            SyntheticEligibilityProofModel.child_profile_id == child_id,
            SyntheticEligibilityProofModel.purpose_ref == purpose_ref,
        )
        .order_by(
            SyntheticEligibilityProofModel.issued_at.desc(),
            SyntheticEligibilityProofModel.evidence_id.desc(),
        )
        .limit(1)
    )
    if row is None:
        return None
    return SyntheticEligibilityProof(
        evidence_id=row.evidence_id,
        scope=EligibilityScope(
            organization_id=row.organization_id,
            class_id=row.class_id,
            child_id=row.child_profile_id,
            purpose_ref=row.purpose_ref,
        ),
        run_ref=row.run_ref,
        issued_at=row.issued_at,
        expires_at=row.expires_at,
        revoked_at=row.revoked_at,
        session_id=row.session_id,
        schema_version=row.schema_version,
    )


class PostgresCoreStore:
    """Concrete repositories backed by PostgreSQL transactions."""

    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def initialize_aggregate(
        self, *, aggregate_id: str, organization_id: str, revision: int = 1
    ) -> bool:
        if revision < 1:
            raise ValueError("aggregate revision must be positive")
        try:
            with self._sessions.begin() as session:
                session.add(
                    CoreAggregateRevisionModel(
                        aggregate_id=aggregate_id,
                        organization_id=organization_id,
                        revision=revision,
                    )
                )
                session.flush()
            return True
        except IntegrityError:
            return False

    def current_revision(self, aggregate_id: str, *, organization_id: str) -> int | None:
        with self._sessions() as session:
            return session.scalar(
                select(CoreAggregateRevisionModel.revision).where(
                    CoreAggregateRevisionModel.aggregate_id == aggregate_id,
                    CoreAggregateRevisionModel.organization_id == organization_id,
                )
            )

    def get_operation(
        self, *, organization_id: str, operation_id: str
    ) -> CanvasOperationRecord | None:
        with self._sessions() as session:
            row = session.scalar(
                select(CoreCanvasOperationModel).where(
                    CoreCanvasOperationModel.organization_id == organization_id,
                    CoreCanvasOperationModel.operation_id == operation_id,
                )
            )
            if row is None:
                return None
            return CanvasOperationRecord(
                organization_id=row.organization_id,
                operation=CanvasOperation(
                    operation_id=row.operation_id,
                    turn_id=row.turn_id,
                    participant_id=row.participant_id,
                    session_id=row.session_id,
                    canvas_id=row.canvas_id,
                    document_epoch=row.document_epoch,
                ),
                resulting_revision=row.resulting_revision,
                request_fingerprint=row.request_fingerprint,
                operation_payload=row.operation_payload,
                accepted_at=row.accepted_at,
            )

    def list_operations(
        self,
        *,
        organization_id: str,
        canvas_id: str,
        after_revision: int,
        limit: int = 200,
    ) -> tuple[CanvasOperationRecord, ...]:
        if after_revision < 0 or not 1 <= limit <= 500:
            raise ValueError("operation sync cursor or limit is invalid")
        with self._sessions() as session:
            rows = session.scalars(
                select(CoreCanvasOperationModel)
                .where(
                    CoreCanvasOperationModel.organization_id == organization_id,
                    CoreCanvasOperationModel.canvas_id == canvas_id,
                    CoreCanvasOperationModel.resulting_revision > after_revision,
                )
                .order_by(CoreCanvasOperationModel.resulting_revision)
                .limit(limit)
            ).all()
            return tuple(
                CanvasOperationRecord(
                    organization_id=row.organization_id,
                    operation=CanvasOperation(
                        operation_id=row.operation_id,
                        turn_id=row.turn_id,
                        participant_id=row.participant_id,
                        session_id=row.session_id,
                        canvas_id=row.canvas_id,
                        document_epoch=row.document_epoch,
                    ),
                    resulting_revision=row.resulting_revision,
                    request_fingerprint=row.request_fingerprint,
                    operation_payload=row.operation_payload,
                    accepted_at=row.accepted_at,
                )
                for row in rows
            )

    def get_receipt(
        self, *, organization_id: str, scope: str, key: str
    ) -> IdempotencyReceipt | None:
        with self._sessions() as session:
            row = session.get(CoreIdempotencyReceiptModel, (organization_id, scope, key))
            if row is None:
                return None
            return IdempotencyReceipt(
                scope=row.scope,
                key=row.key,
                request_fingerprint=row.request_fingerprint,
                resulting_revision=row.resulting_revision,
                operation_id=row.operation_id,
            )

    def commit_canvas_mutation(self, mutation: CanvasMutationCommit) -> bool:
        operation = mutation.operation
        receipt = mutation.receipt
        if (
            operation.canvas_id != mutation.aggregate_id
            or receipt.operation_id != operation.operation_id
            or receipt.resulting_revision != mutation.next_revision
            or mutation.next_revision != mutation.expected_revision + 1
            or operation.document_epoch < 1
            or not _SHA256_RE.fullmatch(receipt.request_fingerprint)
            or receipt.scope == ""
            or receipt.key == ""
        ):
            raise ValueError("canvas mutation and receipt metadata are inconsistent")

        try:
            with self._sessions.begin() as session:
                result = cast(
                    CursorResult[Any],
                    session.execute(
                        update(CoreAggregateRevisionModel)
                        .where(
                            CoreAggregateRevisionModel.aggregate_id == mutation.aggregate_id,
                            CoreAggregateRevisionModel.organization_id == mutation.organization_id,
                            CoreAggregateRevisionModel.revision == mutation.expected_revision,
                        )
                        .values(revision=mutation.next_revision)
                    ),
                )
                if result.rowcount != 1:
                    return False

                session.add(
                    CoreCanvasOperationModel(
                        operation_id=operation.operation_id,
                        organization_id=mutation.organization_id,
                        canvas_id=operation.canvas_id,
                        session_id=operation.session_id,
                        turn_id=operation.turn_id,
                        participant_id=operation.participant_id,
                        document_epoch=operation.document_epoch,
                        resulting_revision=mutation.next_revision,
                        request_fingerprint=receipt.request_fingerprint,
                        operation_payload=mutation.operation_payload,
                    )
                )
                session.add(
                    CoreIdempotencyReceiptModel(
                        organization_id=mutation.organization_id,
                        scope=receipt.scope,
                        key=receipt.key,
                        request_fingerprint=receipt.request_fingerprint,
                        resulting_revision=receipt.resulting_revision,
                        operation_id=receipt.operation_id,
                    )
                )
                session.add(
                    CoreAuditEntryModel(
                        audit_id=str(uuid4()),
                        organization_id=mutation.organization_id,
                        actor_ref=mutation.actor_id,
                        action="canvas.operation.accept",
                        resource_type="canvas",
                        resource_id=operation.canvas_id,
                        decision="accepted_durable",
                    )
                )
                session.add(
                    CoreOutboxEventModel(
                        event_id=mutation.outbox_event_id,
                        event_type="canvas.operation.accepted.v1",
                        organization_id=mutation.organization_id,
                        aggregate_id=mutation.aggregate_id,
                        aggregate_revision=mutation.next_revision,
                        payload={
                            "operation_id": operation.operation_id,
                            "document_epoch": str(operation.document_epoch),
                        },
                    )
                )
                session.flush()
            return True
        except IntegrityError:
            # The transaction context rolls back the revision and every dependent row.
            return False

    def append(
        self,
        *,
        organization_id: str,
        action: str,
        resource_id: str,
        decision: str,
    ) -> None:
        with self._sessions.begin() as session:
            session.add(
                CoreAuditEntryModel(
                    audit_id=str(uuid4()),
                    organization_id=organization_id,
                    actor_ref=None,
                    action=action,
                    resource_type="core_resource",
                    resource_id=resource_id,
                    decision=decision,
                )
            )

    def list_for_resource(
        self, *, organization_id: str, resource_id: str, limit: int = 100
    ) -> tuple[CoreAuditRecord, ...]:
        if not 1 <= limit <= 500:
            raise ValueError("audit page size must be between 1 and 500")
        with self._sessions() as session:
            rows = session.scalars(
                select(CoreAuditEntryModel)
                .where(
                    CoreAuditEntryModel.organization_id == organization_id,
                    CoreAuditEntryModel.resource_id == resource_id,
                )
                .order_by(
                    CoreAuditEntryModel.created_at.desc(), CoreAuditEntryModel.audit_id.desc()
                )
                .limit(limit)
            )
            return tuple(
                CoreAuditRecord(
                    audit_id=row.audit_id,
                    organization_id=row.organization_id,
                    actor_ref=row.actor_ref,
                    action=row.action,
                    resource_type=row.resource_type,
                    resource_id=row.resource_id,
                    decision=row.decision,
                    created_at=row.created_at,
                )
                for row in rows
            )

    def save_checkpoint(self, checkpoint: CanvasCheckpointMetadata) -> bool:
        self._validate_sha256(checkpoint.checksum_sha256, "checkpoint checksum")
        try:
            with self._sessions.begin() as session:
                existing = session.scalar(
                    select(CoreCanvasCheckpointModel).where(
                        CoreCanvasCheckpointModel.checkpoint_id == checkpoint.checkpoint_id,
                        CoreCanvasCheckpointModel.organization_id == checkpoint.organization_id,
                    )
                )
                if existing is not None:
                    return self._checkpoint_from_row(existing) == checkpoint
                aggregate = session.get(CoreAggregateRevisionModel, checkpoint.canvas_id)
                operation = session.get(CoreCanvasOperationModel, checkpoint.through_operation_id)
                if (
                    aggregate is None
                    or aggregate.organization_id != checkpoint.organization_id
                    or operation is None
                    or operation.organization_id != checkpoint.organization_id
                    or operation.canvas_id != checkpoint.canvas_id
                    or operation.document_epoch != checkpoint.document_epoch
                    or operation.resulting_revision > checkpoint.revision
                    or checkpoint.revision > aggregate.revision
                ):
                    return False
                session.add(
                    CoreCanvasCheckpointModel(
                        checkpoint_id=checkpoint.checkpoint_id,
                        organization_id=checkpoint.organization_id,
                        canvas_id=checkpoint.canvas_id,
                        document_epoch=checkpoint.document_epoch,
                        revision=checkpoint.revision,
                        through_operation_id=checkpoint.through_operation_id,
                        checksum_sha256=checkpoint.checksum_sha256,
                        storage_ref=checkpoint.storage_ref,
                    )
                )
                session.flush()
            return True
        except IntegrityError:
            return (
                self.get_checkpoint(
                    checkpoint.checkpoint_id, organization_id=checkpoint.organization_id
                )
                == checkpoint
            )

    def get_checkpoint(
        self, checkpoint_id: str, *, organization_id: str
    ) -> CanvasCheckpointMetadata | None:
        with self._sessions() as session:
            row = session.scalar(
                select(CoreCanvasCheckpointModel).where(
                    CoreCanvasCheckpointModel.checkpoint_id == checkpoint_id,
                    CoreCanvasCheckpointModel.organization_id == organization_id,
                )
            )
            if row is None:
                return None
            return self._checkpoint_from_row(row)

    def save_asset_metadata(self, asset: CoreAssetMetadata) -> bool:
        self._validate_sha256(asset.content_sha256, "asset content hash")
        existing = self.get_asset_metadata(
            asset.asset_ref, asset.version, organization_id=asset.organization_id
        )
        if existing is not None:
            return existing == asset
        try:
            with self._sessions.begin() as session:
                session.add(
                    CoreAssetMetadataModel(
                        asset_ref=asset.asset_ref,
                        asset_version=asset.version,
                        organization_id=asset.organization_id,
                        content_sha256=asset.content_sha256,
                        media_type=asset.media_type,
                        source_refs=list(asset.source_refs),
                        derived_from_ref=asset.derived_from_ref,
                    )
                )
                session.flush()
            return True
        except IntegrityError:
            return (
                self.get_asset_metadata(
                    asset.asset_ref, asset.version, organization_id=asset.organization_id
                )
                == asset
            )

    def get_asset_metadata(
        self, asset_ref: str, version: int, *, organization_id: str
    ) -> CoreAssetMetadata | None:
        with self._sessions() as session:
            row = session.scalar(
                select(CoreAssetMetadataModel).where(
                    CoreAssetMetadataModel.asset_ref == asset_ref,
                    CoreAssetMetadataModel.asset_version == version,
                    CoreAssetMetadataModel.organization_id == organization_id,
                )
            )
            if row is None:
                return None
            return CoreAssetMetadata(
                asset_ref=row.asset_ref,
                version=row.asset_version,
                organization_id=row.organization_id,
                content_sha256=row.content_sha256,
                media_type=row.media_type,
                source_refs=tuple(row.source_refs),
                derived_from_ref=row.derived_from_ref,
            )

    def get_profile_origin(
        self, *, organization_id: str, class_id: str, child_id: str
    ) -> str | None:
        with self._sessions() as session:
            return load_profile_origin(
                session, organization_id=organization_id, class_id=class_id, child_id=child_id
            )

    def get_synthetic_proof(
        self, *, organization_id: str, class_id: str, child_id: str, purpose_ref: str
    ) -> SyntheticEligibilityProof | None:
        with self._sessions() as session:
            return load_synthetic_proof(
                session,
                organization_id=organization_id,
                class_id=class_id,
                child_id=child_id,
                purpose_ref=purpose_ref,
            )

    def create_synthetic_profile(
        self,
        *,
        organization_id: str,
        class_id: str,
        child_id: str,
        display_name: str,
        age_months: int,
        created_by: str,
    ) -> bool:
        """Operator-only: creates a SYNTHETIC_DEV profile with no legal consent references."""
        if not child_id.startswith("synthetic-") or not display_name.startswith("Synthetic "):
            # Second line of defense behind the operator tool: never store a real-looking identity.
            raise ValueError("a SYNTHETIC_DEV profile needs a synthetic- id and a Synthetic name")
        try:
            with self._sessions.begin() as session:
                session.add(
                    ManagedProfileModel(
                        child_id=child_id,
                        organization_id=organization_id,
                        class_id=class_id,
                        display_name=display_name,
                        age_months=age_months,
                        consent_id=None,
                        consent_purpose_ref=None,
                        data_origin=ProvisionalDataOrigin.SYNTHETIC_DEV.value,
                        created_by=created_by,
                    )
                )
                session.flush()
            return True
        except IntegrityError:
            return False

    def issue_synthetic_proof(
        self,
        *,
        evidence_id: str,
        organization_id: str,
        class_id: str,
        child_id: str,
        purpose_ref: str,
        run_ref: str,
        session_id: str | None,
        issued_by: str,
        issued_at: datetime,
        expires_at: datetime,
        policy_version: str,
    ) -> bool:
        """Operator-only: append one proof for a SYNTHETIC_DEV profile; never edits history."""
        try:
            with self._sessions.begin() as session:
                origin = load_profile_origin(
                    session, organization_id=organization_id, class_id=class_id, child_id=child_id
                )
                if origin != ProvisionalDataOrigin.SYNTHETIC_DEV.value:
                    raise ValueError("a proof can only be issued for a SYNTHETIC_DEV profile")
                session.add(
                    SyntheticEligibilityProofModel(
                        evidence_id=evidence_id,
                        schema_version=PROOF_VERSION,
                        data_origin=ProvisionalDataOrigin.SYNTHETIC_DEV.value,
                        organization_id=organization_id,
                        class_id=class_id,
                        child_profile_id=child_id,
                        purpose_ref=purpose_ref,
                        run_ref=run_ref,
                        session_id=session_id,
                        issued_by=issued_by,
                        issued_at=issued_at,
                        expires_at=expires_at,
                        revocation_revision=0,
                        policy_version=policy_version,
                    )
                )
                session.flush()
            return True
        except IntegrityError:
            return False

    def revoke_synthetic_proof(
        self, *, evidence_id: str, organization_id: str, revoked_at: datetime
    ) -> bool:
        """Operator-only: set the one-time revocation; a second call changes nothing."""
        with self._sessions.begin() as session:
            result = cast(
                CursorResult[Any],
                session.execute(
                    update(SyntheticEligibilityProofModel)
                    .where(
                        SyntheticEligibilityProofModel.evidence_id == evidence_id,
                        SyntheticEligibilityProofModel.organization_id == organization_id,
                        SyntheticEligibilityProofModel.revoked_at.is_(None),
                    )
                    .values(revoked_at=revoked_at, revocation_revision=1)
                ),
            )
            return result.rowcount == 1

    @staticmethod
    def _validate_sha256(value: str, label: str) -> None:
        if not _SHA256_RE.fullmatch(value):
            raise ValueError(f"{label} must be lowercase SHA-256 hex")

    @staticmethod
    def _checkpoint_from_row(row: CoreCanvasCheckpointModel) -> CanvasCheckpointMetadata:
        return CanvasCheckpointMetadata(
            checkpoint_id=row.checkpoint_id,
            organization_id=row.organization_id,
            canvas_id=row.canvas_id,
            document_epoch=row.document_epoch,
            revision=row.revision,
            through_operation_id=row.through_operation_id,
            checksum_sha256=row.checksum_sha256,
            storage_ref=row.storage_ref,
        )


__all__ = ["PostgresCoreStore", "load_profile_origin", "load_synthetic_proof"]
