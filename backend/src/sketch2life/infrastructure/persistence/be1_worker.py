"""Durable BE1 retention worker for local filesystem artifacts and session state."""

from __future__ import annotations

import argparse
import time
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from sketch2life.infrastructure.config.settings import get_settings
from sketch2life.infrastructure.persistence.be1_models import (
    ChildTurnModel,
    ClassroomSessionModel,
    DataLifecycleRequestModel,
    DeviceGrantModel,
    GallerySnapshotModel,
    ObservationModel,
    SessionGroupModel,
    SessionMembershipModel,
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
from sketch2life.infrastructure.persistence.database import (
    create_core_engine,
    create_core_session_factory,
)
from sketch2life.infrastructure.storage.persistent_local_artifacts import LocalArtifactStore


def _purge_session(
    db: Session,
    *,
    row: ClassroomSessionModel,
    artifacts: LocalArtifactStore,
    now: datetime,
) -> int:
    organization_id = row.organization_id
    session_id = row.session_id
    session_tag = f"be1-session:{session_id}"
    group_ids = list(
        db.scalars(
            select(SessionGroupModel.group_id).where(
                SessionGroupModel.organization_id == organization_id,
                SessionGroupModel.session_id == session_id,
            )
        ).all()
    )

    unresolved = 1  # Provider-copy receipts have no approved BE1 verifier yet.
    assets = db.scalars(
        select(CoreAssetMetadataModel).where(
            CoreAssetMetadataModel.organization_id == organization_id,
            CoreAssetMetadataModel.source_refs.contains([session_tag]),
        )
    ).all()
    for asset in assets:
        if asset.asset_ref.startswith("local-artifact:"):
            artifacts.delete(asset.asset_ref)
            db.delete(asset)
        else:
            unresolved += 1

    checkpoints = db.scalars(
        select(CoreCanvasCheckpointModel).where(
            CoreCanvasCheckpointModel.organization_id == organization_id,
            CoreCanvasCheckpointModel.canvas_id.in_(group_ids or [""]),
        )
    ).all()
    for checkpoint in checkpoints:
        if checkpoint.storage_ref.startswith("local-artifact:"):
            artifacts.delete(checkpoint.storage_ref)
            db.delete(checkpoint)
        else:
            unresolved += 1

    operation_ids = list(
        db.scalars(
            select(CoreCanvasOperationModel.operation_id).where(
                CoreCanvasOperationModel.organization_id == organization_id,
                CoreCanvasOperationModel.session_id == session_id,
            )
        ).all()
    )
    if operation_ids:
        db.execute(
            delete(CoreIdempotencyReceiptModel).where(
                CoreIdempotencyReceiptModel.organization_id == organization_id,
                CoreIdempotencyReceiptModel.operation_id.in_(operation_ids),
            )
        )
        db.execute(
            delete(CoreCanvasOperationModel).where(
                CoreCanvasOperationModel.organization_id == organization_id,
                CoreCanvasOperationModel.operation_id.in_(operation_ids),
            )
        )

    db.execute(
        delete(ObservationModel).where(
            ObservationModel.organization_id == organization_id,
            ObservationModel.session_id == session_id,
        )
    )
    db.execute(
        delete(GallerySnapshotModel).where(
            GallerySnapshotModel.organization_id == organization_id,
            GallerySnapshotModel.session_id == session_id,
        )
    )
    db.execute(
        delete(ChildTurnModel).where(
            ChildTurnModel.organization_id == organization_id,
            ChildTurnModel.session_id == session_id,
        )
    )
    db.execute(
        delete(SessionMembershipModel).where(
            SessionMembershipModel.organization_id == organization_id,
            SessionMembershipModel.session_id == session_id,
        )
    )
    db.execute(
        delete(DeviceGrantModel).where(
            DeviceGrantModel.organization_id == organization_id,
            DeviceGrantModel.session_id == session_id,
        )
    )
    db.execute(
        delete(SessionGroupModel).where(
            SessionGroupModel.organization_id == organization_id,
            SessionGroupModel.session_id == session_id,
        )
    )

    # Keep the session tombstone and operational audit trail; remove its join secret,
    # purpose value and configuration payload after the confirmed 90-day lifetime.
    row.configuration = {}
    row.retention_enqueued_at = now
    row.revision += 1
    request_id = str(uuid4())
    request = DataLifecycleRequestModel(
        request_id=request_id,
        organization_id=organization_id,
        request_type="delete",
        target_ref=f"session:{session_id}",
        state="awaiting_external_purge",
        unresolved_items=unresolved,
        requested_by="be1-retention-worker",
    )
    db.add(request)
    db.flush()

    aggregate = db.get(CoreAggregateRevisionModel, session_id)
    if aggregate is None:
        aggregate = CoreAggregateRevisionModel(
            aggregate_id=session_id,
            organization_id=organization_id,
            revision=row.revision,
        )
        db.add(aggregate)
    else:
        aggregate.revision = max(aggregate.revision + 1, row.revision)
    db.add(
        CoreAuditEntryModel(
            audit_id=str(uuid4()),
            organization_id=organization_id,
            actor_ref=None,
            action="retention.local_purge",
            resource_type="session",
            resource_id=session_id,
            decision="local_copy_purged_external_pending",
        )
    )
    db.add(
        CoreOutboxEventModel(
            event_id=str(uuid4()),
            event_type="be1.retention.local_purge_completed.v1",
            organization_id=organization_id,
            aggregate_id=session_id,
            aggregate_revision=aggregate.revision,
            payload={"request_id": request_id, "session_id": session_id},
            status="pending",
            attempt_count=0,
        )
    )
    return unresolved


def run_retention_once(
    sessions: sessionmaker[Session], artifacts: LocalArtifactStore, *, now: datetime | None = None
) -> int:
    cutoff = now or datetime.now(UTC)
    if cutoff.tzinfo is None:
        raise ValueError("retention clock must be timezone-aware")
    processed = 0
    with sessions.begin() as db:
        due = db.scalars(
            select(ClassroomSessionModel)
            .where(
                ClassroomSessionModel.state == "finished",
                ClassroomSessionModel.retain_until <= cutoff,
                ClassroomSessionModel.retention_enqueued_at.is_(None),
            )
            .order_by(ClassroomSessionModel.retain_until)
            .limit(50)
            .with_for_update(skip_locked=True)
        ).all()
        for row in due:
            _purge_session(db, row=row, artifacts=artifacts, now=cutoff)
            processed += 1
    return processed


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the BE1 local retention worker")
    parser.add_argument("--once", action="store_true", help="process one retention batch and exit")
    parser.add_argument("--interval-seconds", type=int, default=30)
    args = parser.parse_args()
    if args.interval_seconds < 1 or args.interval_seconds > 3600:
        parser.error("--interval-seconds must be between 1 and 3600")
    settings = get_settings()
    if settings.env not in {"local", "test"}:
        print("BE1 production retention worker requires a selected object-storage provider")
        return 2
    engine = create_core_engine()
    sessions = create_core_session_factory(engine)
    artifacts = LocalArtifactStore(settings.be1_artifact_root)
    try:
        while True:
            count = run_retention_once(sessions, artifacts)
            print(f"BE1 retention batch completed; sessions_purged_locally={count}")
            if args.once:
                return 0
            time.sleep(args.interval_seconds)
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
