"""Durable attributed canvas operations, sync, checkpoints and recovery."""

# FastAPI dependency declarations intentionally use Depends in defaults.
# ruff: noqa: B008

from __future__ import annotations

import hashlib
import hmac
import json
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import and_, case, func, select, update
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal as AdultPrincipal
from sketch2life.application.services.core_foundation import (
    CoreFoundationApplication,
)
from sketch2life.contracts.schemas.be1_runtime import (
    CanvasCheckpointRequest,
    CanvasOperationRequest,
    CanvasReconnectResponse,
    CanvasRestoreRequest,
    CanvasSourceExportV1,
    CanvasSourceOperationV1,
)
from sketch2life.domain.core_foundation import (
    CANVAS_OPERATION_PROFILE_V1_ID,
    CanvasOperation,
    CoreErrorCode,
    CoreRuleViolation,
    bind_canvas_operation_profile_v1_payload,
    canvas_operation_profile_v1_configuration,
    is_idempotent_replay,
    require_expected_revision,
    validate_canvas_operation_profile_v1,
)
from sketch2life.infrastructure.canvas_render.limits import MAX_POINTS, MAX_STROKES
from sketch2life.infrastructure.config.settings import Settings
from sketch2life.infrastructure.persistence.be1_models import (
    ChildTurnModel,
    ClassroomSessionModel,
    ConsentRecordModel,
    SessionGroupModel,
    SessionMembershipModel,
)
from sketch2life.infrastructure.persistence.core_models import (
    CoreAggregateRevisionModel,
    CoreCanvasCheckpointModel,
    CoreCanvasOperationModel,
)
from sketch2life.infrastructure.persistence.core_store import PostgresCoreStore
from sketch2life.interfaces.http.be1_runtime import (
    Be1Runtime,
    VerifiedDeviceContext,
    VerifiedDeviceStatusContext,
    get_db,
    get_runtime,
    get_verified_adult,
    get_verified_device,
    get_verified_device_status,
)
from sketch2life.interfaces.http.routers.be1_common import (
    BE1_ERROR_RESPONSES,
    audit,
    commit,
    consent_is_effective,
    deny_pending_consent,
    eligibility_ready,
    event,
    failure,
    get_session,
    require_assignment,
    session_event,
)

router = APIRouter(prefix="/api/be1/v1", tags=["BE1 canvas"], responses=BE1_ERROR_RESPONSES)


def _canvas_source_unavailable() -> HTTPException:
    return failure(409, "CANVAS_SOURCE_UNAVAILABLE", "Canvas source is unavailable")


def _store(runtime: Be1Runtime) -> PostgresCoreStore:
    if runtime.session_factory is None:
        raise failure(
            503, "DATABASE_NOT_CONFIGURED", "PostgreSQL is required for canvas operations"
        )
    return PostgresCoreStore(runtime.session_factory)


def _require_device_path(
    device: VerifiedDeviceContext,
    organization_id: str,
    session_id: str,
) -> None:
    if device.grant.organization_id != organization_id or device.session.session_id != session_id:
        raise failure(404, "DEVICE_SCOPE_NOT_FOUND", "Device is not scoped to this session")


def _record_response(record) -> dict[str, object]:
    return {
        "operation_id": record.operation.operation_id,
        "session_id": record.operation.session_id,
        "canvas_id": record.operation.canvas_id,
        "turn_id": record.operation.turn_id,
        "participant_id": record.operation.participant_id,
        "document_epoch": record.operation.document_epoch,
        "resulting_revision": record.resulting_revision,
        "operation_payload": record.operation_payload,
        "accepted_at": record.accepted_at,
    }


def build_canvas_source_export(
    db: Session,
    *,
    organization_id: str,
    session_id: str,
    canvas_id: str,
    document_epoch: int,
) -> CanvasSourceExportV1:
    """Build a complete, server-accepted canvas source from one DB statement snapshot."""

    checkpoint_exists = (
        select(CoreCanvasCheckpointModel.checkpoint_id)
        .where(CoreCanvasCheckpointModel.canvas_id == canvas_id)
        .exists()
    )
    statement = (
        select(
            CoreAggregateRevisionModel,
            ClassroomSessionModel.session_id,
            ClassroomSessionModel.configuration,
            CoreCanvasOperationModel,
            checkpoint_exists.label("has_checkpoint"),
        )
        .select_from(CoreAggregateRevisionModel)
        .outerjoin(
            ClassroomSessionModel,
            and_(
                ClassroomSessionModel.organization_id == organization_id,
                ClassroomSessionModel.session_id == session_id,
            ),
        )
        .outerjoin(
            CoreCanvasOperationModel,
            CoreCanvasOperationModel.canvas_id == CoreAggregateRevisionModel.aggregate_id,
        )
        .where(
            CoreAggregateRevisionModel.organization_id == organization_id,
            CoreAggregateRevisionModel.aggregate_id == canvas_id,
        )
        .order_by(
            CoreCanvasOperationModel.resulting_revision,
            CoreCanvasOperationModel.operation_id,
        )
    )
    rows = db.execute(statement).all()
    if not rows:
        raise _canvas_source_unavailable()

    aggregate = rows[0][0]
    bound_session_id = rows[0][1]
    session_configuration = rows[0][2]
    if (
        aggregate.aggregate_id != canvas_id
        or aggregate.organization_id != organization_id
        or bound_session_id != session_id
        or not isinstance(session_configuration, dict)
        or session_configuration.get("canvas_operation_profile")
        != canvas_operation_profile_v1_configuration()
        or any(bool(row[4]) for row in rows)
    ):
        raise _canvas_source_unavailable()

    raw_operations = [row[3] for row in rows if row[3] is not None]
    point_count = sum(
        len(row.operation_payload.get("points", []))
        for row in raw_operations
        if isinstance(row.operation_payload, dict)
        and isinstance(row.operation_payload.get("points"), list)
    )
    if aggregate.revision - 1 > MAX_STROKES or point_count > MAX_POINTS:
        raise failure(409, "CANVAS_SOURCE_TOO_LARGE", "Canvas source exceeds pilot capacity")

    operations: list[CanvasSourceOperationV1] = []
    for row in rows:
        operation = row[3]
        if operation is None:
            raise _canvas_source_unavailable()
        if (
            operation.organization_id != organization_id
            or operation.session_id != session_id
            or operation.canvas_id != canvas_id
            or operation.document_epoch != document_epoch
            or not isinstance(operation.operation_payload, dict)
            or operation.operation_payload.get("canvas_operation_profile_id")
            != CANVAS_OPERATION_PROFILE_V1_ID
        ):
            raise _canvas_source_unavailable()
        accepted_payload = dict(operation.operation_payload)
        accepted_payload.pop("canvas_operation_profile_id", None)
        try:
            validated_payload = validate_canvas_operation_profile_v1(accepted_payload)
            if validated_payload != accepted_payload:
                raise _canvas_source_unavailable()
            operations.append(
                CanvasSourceOperationV1(
                    operation_id=operation.operation_id,
                    participant_id=operation.participant_id,
                    document_epoch=operation.document_epoch,
                    resulting_revision=operation.resulting_revision,
                    operation_payload=operation.operation_payload,
                    payload_sha256=hashlib.sha256(
                        json.dumps(
                            operation.operation_payload,
                            ensure_ascii=False,
                            sort_keys=True,
                            separators=(",", ":"),
                        ).encode("utf-8")
                    ).hexdigest(),
                )
            )
        except (CoreRuleViolation, TypeError, ValueError):
            raise _canvas_source_unavailable() from None

    expected_revisions = list(range(2, aggregate.revision + 1))
    if (
        document_epoch < 1
        or not operations
        or [operation.resulting_revision for operation in operations] != expected_revisions
    ):
        raise _canvas_source_unavailable()

    try:
        return CanvasSourceExportV1.from_operations(
            organization_id=organization_id,
            session_id=session_id,
            canvas_id=canvas_id,
            document_epoch=document_epoch,
            document_revision=aggregate.revision,
            operations=operations,
        )
    except (TypeError, ValueError):
        raise _canvas_source_unavailable() from None


@router.post("/organizations/{organization_id}/sessions/{session_id}/canvas/operations")
def append_canvas_operation(
    organization_id: str,
    session_id: str,
    payload: CanvasOperationRequest,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=256),
    device: VerifiedDeviceContext = Depends(get_verified_device),
    runtime: Be1Runtime = Depends(get_runtime),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    _require_device_path(device, organization_id, session_id)
    session = _require_group_eligibility(
        db,
        settings=runtime.settings,
        organization_id=organization_id,
        session_id=session_id,
        group_id=device.membership.group_id or "",
        actor=f"device:{device.grant.grant_id}",
        action="canvas.operation.append",
    )
    try:
        operation_payload = bind_canvas_operation_profile_v1_payload(
            session_configuration=session.configuration,
            profile_version=payload.profile_version,
            operation_payload=payload.operation_payload,
        )
    except CoreRuleViolation as exc:
        code = exc.code.value
        status_code = 422 if exc.code is CoreErrorCode.CANVAS_PROFILE_INVALID else 409
        raise failure(status_code, code, str(exc)) from None
    operation = CanvasOperation(
        operation_id=payload.operation_id,
        turn_id=payload.turn_id,
        participant_id=device.membership.child_id,
        session_id=session_id,
        canvas_id=device.turn.canvas_id,
        document_epoch=payload.document_epoch,
    )
    fingerprint_payload = {
        "operation_id": payload.operation_id,
        "turn_id": payload.turn_id,
        "document_epoch": payload.document_epoch,
        "expected_revision": payload.expected_revision,
        "operation_payload": operation_payload,
    }
    if payload.profile_version is not None:
        fingerprint_payload["profile_version"] = payload.profile_version
    request_fingerprint = hashlib.sha256(
        json.dumps(
            fingerprint_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    store = _store(runtime)
    try:
        previous = store.get_receipt(
            organization_id=organization_id,
            scope=f"canvas:{device.turn.canvas_id}",
            key=idempotency_key,
        )
        replay = is_idempotent_replay(
            previous, key=idempotency_key, request_fingerprint=request_fingerprint
        )
        if not replay:
            current_revision = store.current_revision(
                device.turn.canvas_id, organization_id=organization_id
            )
            if current_revision is None:
                raise CoreRuleViolation(CoreErrorCode.STALE_AGGREGATE, "canvas is unavailable")
            require_expected_revision(payload.expected_revision, current_revision)
            points_json = CoreCanvasOperationModel.operation_payload["points"]
            existing_points = db.scalar(
                select(
                    func.coalesce(
                        func.sum(
                            case(
                                (
                                    func.jsonb_typeof(points_json) == "array",
                                    func.jsonb_array_length(points_json),
                                ),
                                else_=0,
                            )
                        ),
                        0,
                    )
                ).where(
                    CoreCanvasOperationModel.organization_id == organization_id,
                    CoreCanvasOperationModel.session_id == session_id,
                    CoreCanvasOperationModel.canvas_id == device.turn.canvas_id,
                )
            )
            incoming_points = operation_payload.get("points")
            point_count = len(incoming_points) if isinstance(incoming_points, list) else 0
            if (
                current_revision - 1 >= MAX_STROKES
                or int(existing_points or 0) + point_count > MAX_POINTS
            ):
                raise failure(409, "CANVAS_CAPACITY_REACHED", "Canvas reached pilot capacity")
        outcome = CoreFoundationApplication.apply_canvas_operation(
            principal=device.principal,
            target=device.scope,
            membership=device.membership,
            turn=device.turn,
            operation=operation,
            expected_revision=payload.expected_revision,
            idempotency_scope=f"canvas:{device.turn.canvas_id}",
            idempotency_key=idempotency_key,
            request_fingerprint=request_fingerprint,
            revision_port=store,
            receipt_port=store,
            transaction_port=store,
            operation_payload=operation_payload,
        )
    except CoreRuleViolation as exc:
        code = exc.code.value
        if exc.code is CoreErrorCode.CANVAS_PROFILE_INVALID:
            status_code = 422
        elif code in {"FORBIDDEN_ROLE", "SCOPE_DENIED", "INVALID_TURN"}:
            status_code = 403
        else:
            status_code = 409
        raise failure(status_code, code, str(exc)) from None
    return {
        "contract": "Be1CanvasOperationReceiptV1",
        "status": outcome.status.value,
        "canvas_id": device.turn.canvas_id,
        "resulting_revision": outcome.resulting_revision,
        "operation_id": payload.operation_id,
    }


@router.get("/organizations/{organization_id}/sessions/{session_id}/canvas/operations")
def sync_canvas_operations(
    organization_id: str,
    session_id: str,
    after_revision: int = Query(default=0, ge=0),
    limit: int = Query(default=200, ge=1, le=500),
    device: VerifiedDeviceContext = Depends(get_verified_device),
    runtime: Be1Runtime = Depends(get_runtime),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    _require_device_path(device, organization_id, session_id)
    _require_group_consent(
        db,
        organization_id=organization_id,
        session_id=session_id,
        group_id=device.membership.group_id or "",
        actor=f"device:{device.grant.grant_id}",
        action="canvas.operation.sync",
    )
    store = _store(runtime)
    records = store.list_operations(
        organization_id=organization_id,
        canvas_id=device.turn.canvas_id,
        after_revision=after_revision,
        limit=limit,
    )
    revision = store.current_revision(device.turn.canvas_id, organization_id=organization_id)
    return {
        "contract": "Be1CanvasSyncV1",
        "canvas_id": device.turn.canvas_id,
        "document_epoch": device.turn.document_epoch,
        "current_revision": revision,
        "operations": [_record_response(record) for record in records],
        "next_after_revision": records[-1].resulting_revision if records else after_revision,
    }


def _require_group_consent(
    db: Session,
    *,
    organization_id: str,
    session_id: str,
    group_id: str,
    actor: str,
    action: str,
) -> ClassroomSessionModel:
    session = get_session(db, organization_id, session_id)
    group = db.scalar(
        select(SessionGroupModel.group_id).where(
            SessionGroupModel.organization_id == organization_id,
            SessionGroupModel.session_id == session_id,
            SessionGroupModel.group_id == group_id,
        )
    )
    if group is None:
        raise failure(404, "GROUP_NOT_FOUND", "Group was not found in this session")
    members = db.scalars(
        select(SessionMembershipModel).where(
            SessionMembershipModel.organization_id == organization_id,
            SessionMembershipModel.session_id == session_id,
            SessionMembershipModel.group_id == group_id,
        )
    ).all()
    child_ids = {member.child_id for member in members}
    child_ids.update(
        db.scalars(
            select(CoreCanvasOperationModel.participant_id).where(
                CoreCanvasOperationModel.organization_id == organization_id,
                CoreCanvasOperationModel.session_id == session_id,
                CoreCanvasOperationModel.canvas_id == group_id,
            )
        ).all()
    )
    purpose = str(session.configuration.get("purpose_ref", ""))
    for child_id in child_ids:
        consent = db.scalar(
            select(ConsentRecordModel.consent_id).where(
                ConsentRecordModel.organization_id == organization_id,
                ConsentRecordModel.class_id == session.class_id,
                ConsentRecordModel.child_id == child_id,
                ConsentRecordModel.purpose_ref == purpose,
                ConsentRecordModel.state == "effective",
            )
        )
        if consent is None:
            deny_pending_consent(
                db,
                organization_id=organization_id,
                actor=actor,
                resource_type="canvas_checkpoint",
                resource_id=group_id,
                action=action,
            )
    return session


def _require_group_eligibility(
    db: Session,
    *,
    settings: Settings,
    organization_id: str,
    session_id: str,
    group_id: str,
    actor: str,
    action: str,
) -> ClassroomSessionModel:
    """Require legal or valid synthetic eligibility for each group contributor.

    Stroke append and Child reconnect use this gate; other routes retain their existing guards.
    """
    session = get_session(db, organization_id, session_id)
    group = db.scalar(
        select(SessionGroupModel.group_id).where(
            SessionGroupModel.organization_id == organization_id,
            SessionGroupModel.session_id == session_id,
            SessionGroupModel.group_id == group_id,
        )
    )
    if group is None:
        raise failure(404, "GROUP_NOT_FOUND", "Group was not found in this session")
    child_ids = set(
        db.scalars(
            select(SessionMembershipModel.child_id).where(
                SessionMembershipModel.organization_id == organization_id,
                SessionMembershipModel.session_id == session_id,
                SessionMembershipModel.group_id == group_id,
            )
        ).all()
    )
    child_ids.update(
        db.scalars(
            select(CoreCanvasOperationModel.participant_id).where(
                CoreCanvasOperationModel.organization_id == organization_id,
                CoreCanvasOperationModel.session_id == session_id,
                CoreCanvasOperationModel.canvas_id == group_id,
            )
        ).all()
    )
    for child_id in sorted(child_ids):
        if not eligibility_ready(
            db,
            session=session,
            child_id=child_id,
            legal_effective=consent_is_effective,
            settings=settings,
            actor=actor,
        ):
            deny_pending_consent(
                db,
                organization_id=organization_id,
                actor=actor,
                resource_type="canvas_checkpoint",
                resource_id=group_id,
                action=action,
            )
    return session


@router.post("/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/checkpoints")
def save_checkpoint(
    organization_id: str,
    session_id: str,
    group_id: str,
    payload: CanvasCheckpointRequest,
    principal: AdultPrincipal = Depends(get_verified_adult),
    runtime: Be1Runtime = Depends(get_runtime),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    if runtime.settings.env not in {"local", "test"}:
        raise failure(
            503,
            "ARTIFACT_PROVIDER_UNCONFIGURED",
            "Production checkpoint storage has not been selected",
        )
    session = get_session(db, organization_id, session_id)
    require_assignment(
        db, principal, organization_id, roles={"school_admin", "teacher"}, class_id=session.class_id
    )
    session = _require_group_consent(
        db,
        organization_id=organization_id,
        session_id=session_id,
        group_id=group_id,
        actor=principal.subject,
        action="canvas.checkpoint.save",
    )
    group = db.scalar(
        select(SessionGroupModel).where(
            SessionGroupModel.organization_id == organization_id,
            SessionGroupModel.session_id == session_id,
            SessionGroupModel.group_id == group_id,
            SessionGroupModel.state == "active",
        )
    )
    if group is None:
        raise failure(404, "GROUP_NOT_FOUND", "Group was not found")
    canvas_id = group_id
    aggregate = db.scalar(
        select(CoreAggregateRevisionModel).where(
            CoreAggregateRevisionModel.organization_id == organization_id,
            CoreAggregateRevisionModel.aggregate_id == canvas_id,
        )
    )
    if aggregate is None or aggregate.revision != payload.document_revision:
        raise failure(409, "STALE_CANVAS_REVISION", "Canvas changed; reload before checkpointing")
    last_operation = db.scalar(
        select(CoreCanvasOperationModel).where(
            CoreCanvasOperationModel.organization_id == organization_id,
            CoreCanvasOperationModel.canvas_id == canvas_id,
            CoreCanvasOperationModel.document_epoch == payload.document_epoch,
            CoreCanvasOperationModel.resulting_revision == payload.document_revision,
        )
    )
    if last_operation is None:
        raise failure(
            409, "CHECKPOINT_OPERATION_REQUIRED", "Checkpoint must include an accepted operation"
        )
    snapshot_bytes = json.dumps(
        payload.snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    checksum = hashlib.sha256(snapshot_bytes).hexdigest()
    storage_ref, stored_hash = runtime.artifact_store.put(snapshot_bytes)
    if not hmac.compare_digest(checksum, stored_hash):
        runtime.artifact_store.delete(storage_ref)
        raise failure(
            500, "CHECKPOINT_STORAGE_INTEGRITY", "Checkpoint storage integrity check failed"
        )
    checkpoint_id = str(uuid4())
    try:
        db.add(
            CoreCanvasCheckpointModel(
                checkpoint_id=checkpoint_id,
                organization_id=organization_id,
                canvas_id=canvas_id,
                document_epoch=payload.document_epoch,
                revision=payload.document_revision,
                through_operation_id=last_operation.operation_id,
                checksum_sha256=checksum,
                storage_ref=storage_ref,
            )
        )
        audit(
            db,
            organization_id=organization_id,
            actor=principal.subject,
            action="canvas.checkpoint.save",
            resource_type="canvas",
            resource_id=canvas_id,
        )
        session_event(
            db,
            session=session,
            event_type="be1.canvas.checkpoint_saved.v1",
            payload={"checkpoint_id": checkpoint_id, "canvas_id": canvas_id},
        )
        commit(db)
    except Exception:
        runtime.artifact_store.delete(storage_ref)
        raise
    return {
        "contract": "Be1CanvasCheckpointV1",
        "checkpoint_id": checkpoint_id,
        "canvas_id": canvas_id,
        "document_epoch": payload.document_epoch,
        "document_revision": payload.document_revision,
        "checksum_sha256": checksum,
    }


def _checkpoint_snapshot(runtime: Be1Runtime, row: CoreCanvasCheckpointModel) -> dict[str, object]:
    content = runtime.artifact_store.get(row.storage_ref)
    if content is None or not hmac.compare_digest(
        hashlib.sha256(content).hexdigest(), row.checksum_sha256
    ):
        raise failure(
            410,
            "CHECKPOINT_UNAVAILABLE",
            "Checkpoint bytes are unavailable or failed integrity validation",
        )
    try:
        snapshot = json.loads(content)
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise failure(410, "CHECKPOINT_INVALID", "Checkpoint bytes are invalid") from None
    if not isinstance(snapshot, dict):
        raise failure(410, "CHECKPOINT_INVALID", "Checkpoint payload is invalid")
    return snapshot


@router.get(
    "/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/checkpoints/latest"
)
def read_latest_checkpoint(
    organization_id: str,
    session_id: str,
    group_id: str,
    principal: AdultPrincipal = Depends(get_verified_adult),
    runtime: Be1Runtime = Depends(get_runtime),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    session = get_session(db, organization_id, session_id)
    require_assignment(
        db,
        principal,
        organization_id,
        roles={"school_admin", "teacher", "guide"},
        class_id=session.class_id,
    )
    _require_group_consent(
        db,
        organization_id=organization_id,
        session_id=session_id,
        group_id=group_id,
        actor=principal.subject,
        action="canvas.checkpoint.read",
    )
    row = db.scalar(
        select(CoreCanvasCheckpointModel)
        .where(
            CoreCanvasCheckpointModel.organization_id == organization_id,
            CoreCanvasCheckpointModel.canvas_id == group_id,
        )
        .order_by(
            CoreCanvasCheckpointModel.document_epoch.desc(),
            CoreCanvasCheckpointModel.revision.desc(),
        )
    )
    if row is None:
        raise failure(404, "CHECKPOINT_NOT_FOUND", "No checkpoint exists for this canvas")
    return {
        "contract": "Be1CanvasCheckpointV1",
        "checkpoint_id": row.checkpoint_id,
        "canvas_id": row.canvas_id,
        "document_epoch": row.document_epoch,
        "document_revision": row.revision,
        "checksum_sha256": row.checksum_sha256,
        "snapshot": _checkpoint_snapshot(runtime, row),
    }


@router.post("/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/restore")
def restore_checkpoint(
    organization_id: str,
    session_id: str,
    group_id: str,
    payload: CanvasRestoreRequest,
    principal: AdultPrincipal = Depends(get_verified_adult),
    runtime: Be1Runtime = Depends(get_runtime),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    if runtime.settings.env not in {"local", "test"}:
        raise failure(
            503,
            "ARTIFACT_PROVIDER_UNCONFIGURED",
            "Production checkpoint storage has not been selected",
        )
    session = get_session(db, organization_id, session_id)
    require_assignment(
        db, principal, organization_id, roles={"school_admin", "teacher"}, class_id=session.class_id
    )
    session = _require_group_consent(
        db,
        organization_id=organization_id,
        session_id=session_id,
        group_id=group_id,
        actor=principal.subject,
        action="canvas.checkpoint.restore",
    )
    checkpoint = db.scalar(
        select(CoreCanvasCheckpointModel).where(
            CoreCanvasCheckpointModel.organization_id == organization_id,
            CoreCanvasCheckpointModel.canvas_id == group_id,
            CoreCanvasCheckpointModel.checkpoint_id == payload.checkpoint_id,
        )
    )
    if checkpoint is None:
        raise failure(404, "CHECKPOINT_NOT_FOUND", "Checkpoint was not found")
    snapshot = _checkpoint_snapshot(runtime, checkpoint)
    aggregate = db.scalar(
        select(CoreAggregateRevisionModel).where(
            CoreAggregateRevisionModel.organization_id == organization_id,
            CoreAggregateRevisionModel.aggregate_id == group_id,
        )
    )
    if aggregate is None or aggregate.revision != payload.expected_revision:
        raise failure(409, "STALE_CANVAS_REVISION", "Canvas changed; reload before restoring")
    next_revision = aggregate.revision + 1
    result = db.execute(
        update(CoreAggregateRevisionModel)
        .where(
            CoreAggregateRevisionModel.aggregate_id == group_id,
            CoreAggregateRevisionModel.organization_id == organization_id,
            CoreAggregateRevisionModel.revision == payload.expected_revision,
        )
        .values(revision=next_revision)
    )
    if result.rowcount != 1:
        raise failure(409, "STALE_CANVAS_REVISION", "Canvas changed; reload before restoring")
    latest_epoch = db.scalar(
        select(CoreCanvasCheckpointModel.document_epoch)
        .where(
            CoreCanvasCheckpointModel.organization_id == organization_id,
            CoreCanvasCheckpointModel.canvas_id == group_id,
        )
        .order_by(CoreCanvasCheckpointModel.document_epoch.desc())
        .limit(1)
    )
    active_turns = db.scalars(
        select(ChildTurnModel).where(
            ChildTurnModel.organization_id == organization_id,
            ChildTurnModel.session_id == session_id,
            ChildTurnModel.group_id == group_id,
            ChildTurnModel.state == "active",
        )
    ).all()
    current_epoch = max(
        [
            epoch
            for epoch in [latest_epoch, *(turn.document_epoch for turn in active_turns)]
            if epoch is not None
        ],
        default=checkpoint.document_epoch,
    )
    new_epoch = current_epoch + 1
    for turn in active_turns:
        turn.document_epoch = new_epoch
    db.add(
        CoreCanvasCheckpointModel(
            checkpoint_id=str(uuid4()),
            organization_id=organization_id,
            canvas_id=group_id,
            document_epoch=new_epoch,
            revision=next_revision,
            through_operation_id=checkpoint.through_operation_id,
            checksum_sha256=checkpoint.checksum_sha256,
            storage_ref=checkpoint.storage_ref,
        )
    )
    audit(
        db,
        organization_id=organization_id,
        actor=principal.subject,
        action="canvas.checkpoint.restore",
        resource_type="canvas",
        resource_id=group_id,
    )
    event(
        db,
        organization_id=organization_id,
        aggregate_id=group_id,
        event_type="be1.canvas.checkpoint_restored.v1",
        payload={
            "checkpoint_id": checkpoint.checkpoint_id,
            "document_epoch": str(new_epoch),
            "session_id": session_id,
        },
        revision=next_revision,
    )
    session_event(
        db,
        session=session,
        event_type="be1.canvas.restored.v1",
        payload={"canvas_id": group_id, "document_epoch": str(new_epoch)},
    )
    commit(db)
    return {
        "contract": "Be1CanvasRestoreV1",
        "canvas_id": group_id,
        "document_epoch": new_epoch,
        "document_revision": next_revision,
        "snapshot": snapshot,
    }


@router.get(
    "/organizations/{organization_id}/sessions/{session_id}/reconnect",
    response_model=CanvasReconnectResponse,
)
def reconnect_canvas(
    organization_id: str,
    session_id: str,
    after_revision: int = Query(default=0, ge=0),
    device: VerifiedDeviceStatusContext = Depends(get_verified_device_status),
    runtime: Be1Runtime = Depends(get_runtime),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    group_id = device.membership.group_id
    if group_id is None:
        raise failure(404, "GROUP_NOT_FOUND", "Group was not found in this session")
    session = _require_group_eligibility(
        db,
        settings=runtime.settings,
        organization_id=organization_id,
        session_id=session_id,
        group_id=group_id,
        actor=f"device:{device.grant.grant_id}",
        action="canvas.reconnect",
    )
    store = _store(runtime)
    row = db.scalar(
        select(CoreCanvasCheckpointModel)
        .where(
            CoreCanvasCheckpointModel.organization_id == organization_id,
            CoreCanvasCheckpointModel.canvas_id == group_id,
        )
        .order_by(
            CoreCanvasCheckpointModel.document_epoch.desc(),
            CoreCanvasCheckpointModel.revision.desc(),
        )
    )
    checkpoint = (
        {
            "checkpoint_id": row.checkpoint_id,
            "document_epoch": row.document_epoch,
            "document_revision": row.revision,
            "snapshot": _checkpoint_snapshot(runtime, row),
        }
        if row is not None
        else None
    )
    turn = db.scalar(
        select(ChildTurnModel)
        .where(
            ChildTurnModel.organization_id == organization_id,
            ChildTurnModel.session_id == session_id,
            ChildTurnModel.group_id == group_id,
            ChildTurnModel.child_id == device.membership.child_id,
            ChildTurnModel.device_grant_id == device.grant.grant_id,
            ChildTurnModel.state == "active",
        )
        .order_by(ChildTurnModel.started_at.desc())
        .limit(1)
    )
    document_epoch = (
        row.document_epoch if row is not None else turn.document_epoch if turn is not None else 1
    )
    records = store.list_operations(
        organization_id=organization_id,
        canvas_id=group_id,
        after_revision=after_revision,
        limit=500,
    )
    return {
        "contract": "Be1CanvasReconnectV1",
        "canvas_id": group_id,
        "turn_id": turn.turn_id if turn is not None else None,
        "profile_version": (
            profile.get("version")
            if isinstance((profile := session.configuration.get("canvas_operation_profile")), dict)
            and isinstance(profile.get("version"), str)
            else None
        ),
        "document_epoch": document_epoch,
        "current_revision": store.current_revision(group_id, organization_id=organization_id) or 0,
        "checkpoint": checkpoint,
        "operations": [_record_response(record) for record in records],
    }


__all__ = ["router"]
