"""Durable BE1 session, admission, grouping and turn lifecycle endpoints."""

# FastAPI dependency declarations intentionally use Depends in defaults.
# ruff: noqa: B008

from __future__ import annotations

import hashlib
import hmac
import ipaddress
import json
import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.services.be1_runtime import (
    Be1PolicyError,
    Be1RuntimePolicy,
    SessionAction,
)
from sketch2life.application.services.classroom_stage_policy import (
    StageTransitionError,
    require_next_stage,
)
from sketch2life.contracts.schemas.be1_runtime import (
    AdmitDeviceRequest,
    AssignMemberRequest,
    CompleteSessionRequest,
    CreateGroupRequest,
    CreateSessionRequest,
    GroupControlRequest,
    JoinRequest,
    JoinRoomCodeRequest,
    ProgressRequest,
    SessionTransitionRequest,
    StageAdvanceRequest,
)
from sketch2life.infrastructure.persistence.be1_models import (
    Be1GroupDraftModel,
    Be1RoomCodeModel,
    Be1RoomCodeRateLimitModel,
    Be1SessionCommandReceiptModel,
    Be1SessionOutcomeModel,
    Be1SessionStageEventModel,
    Be1SessionStageModel,
    ChildTurnModel,
    ClassroomSessionModel,
    DeviceGrantModel,
    GallerySnapshotModel,
    ManagedProfileModel,
    SessionGroupModel,
    SessionMembershipModel,
)
from sketch2life.infrastructure.persistence.core_models import (
    CoreAggregateRevisionModel,
    CoreCanvasCheckpointModel,
    CoreCanvasOperationModel,
)
from sketch2life.interfaces.http.be1_runtime import (
    Be1Runtime,
    get_db,
    get_runtime,
    get_verified_adult,
)
from sketch2life.interfaces.http.routers.be1_common import (
    BE1_ERROR_RESPONSES,
    audit,
    commit,
    consent_is_effective,
    deny_pending_consent,
    event,
    failure,
    get_class,
    get_session,
    require_assignment,
    session_event,
    session_response,
)

router = APIRouter(prefix="/api/be1/v1", tags=["BE1 sessions"], responses=BE1_ERROR_RESPONSES)
_RETENTION_DAYS = 90
_ROOM_CODE_DIGITS = 6
_ROOM_CODE_RATE_LIMIT = 10
_ROOM_CODE_WINDOW = timedelta(minutes=15)


def _room_code_key(runtime: Be1Runtime) -> bytes:
    configured = runtime.settings.room_code_hmac_key
    if configured is None:
        raise failure(503, "ROOM_CODE_UNAVAILABLE", "Room-code service is not configured")
    key = configured.get_secret_value().encode("utf-8")
    if len(key) < 32:
        raise failure(503, "ROOM_CODE_UNAVAILABLE", "Room-code service is not configured")
    return key


def _room_code_hmac(runtime: Be1Runtime, value: str) -> str:
    return hmac.new(_room_code_key(runtime), value.encode("utf-8"), hashlib.sha256).hexdigest()


def _new_room_code() -> str:
    return f"{secrets.randbelow(10**_ROOM_CODE_DIGITS):0{_ROOM_CODE_DIGITS}d}"


def _fingerprint(payload: object) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _require_idempotency_key(value: str | None) -> str:
    if value is None or not value.strip() or len(value) > 128:
        raise failure(422, "IDEMPOTENCY_KEY_REQUIRED", "A valid Idempotency-Key is required")
    return value.strip()


def _room_code_source_hash(runtime: Be1Runtime, request: Request) -> str:
    client = request.client
    if client is None:
        raise failure(503, "ROOM_CODE_UNAVAILABLE", "Room-code service is not configured")
    try:
        source_ip = str(ipaddress.ip_address(client.host))
    except ValueError:
        raise failure(503, "ROOM_CODE_UNAVAILABLE", "Room-code service is not configured") from None
    return _room_code_hmac(runtime, f"source-ip:{source_ip}")


def _lock_room_code_source(db: Session, source_hash: str) -> None:
    # BE1 is PostgreSQL-only. Advisory transaction lock serializes guesses for this source,
    # including the first attempt when no rate-limit row exists yet.
    db.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:source_hash, 0))"),
        {"source_hash": source_hash},
    )


def _room_code_source_throttled(db: Session, source_hash: str, now: datetime) -> bool:
    row = db.get(Be1RoomCodeRateLimitModel, source_hash)
    if row is None:
        return False
    cutoff = now - _ROOM_CODE_WINDOW
    recent_attempts = [
        attempted_at
        for attempted_at in row.attempts
        if datetime.fromisoformat(attempted_at) > cutoff
    ]
    return len(recent_attempts) >= _ROOM_CODE_RATE_LIMIT


def _record_invalid_room_code(db: Session, source_hash: str, now: datetime) -> None:
    cutoff = now - _ROOM_CODE_WINDOW
    row = db.get(Be1RoomCodeRateLimitModel, source_hash)
    recent_attempts = (
        [
            attempted_at
            for attempted_at in row.attempts
            if datetime.fromisoformat(attempted_at) > cutoff
        ]
        if row is not None
        else []
    )
    recent_attempts.append(now.isoformat())
    if row is None:
        db.add(Be1RoomCodeRateLimitModel(source_hmac=source_hash, attempts=recent_attempts))
    else:
        row.attempts = recent_attempts


def _lock_session(db: Session, organization_id: str, session_id: str) -> ClassroomSessionModel:
    row = db.scalar(
        select(ClassroomSessionModel)
        .where(
            ClassroomSessionModel.organization_id == organization_id,
            ClassroomSessionModel.session_id == session_id,
        )
        .with_for_update()
    )
    if row is None:
        raise failure(404, "SESSION_NOT_FOUND", "Session was not found")
    return row


@router.post("/organizations/{organization_id}/sessions", status_code=status.HTTP_201_CREATED)
def create_session(
    organization_id: str,
    payload: CreateSessionRequest,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    require_assignment(
        db, principal, organization_id, roles={"school_admin", "teacher"}, class_id=payload.class_id
    )
    get_class(db, organization_id, payload.class_id)
    if {"purpose_ref", "join_code_sha256"}.intersection(payload.configuration):
        raise failure(
            422, "RESERVED_CONFIGURATION_KEY", "Session configuration contains a reserved key"
        )
    session_id = str(uuid4())
    join_code = secrets.token_urlsafe(12)
    configuration = {
        **payload.configuration,
        "purpose_ref": payload.purpose_ref,
        "join_code_sha256": hashlib.sha256(join_code.encode("utf-8")).hexdigest(),
    }
    record = ClassroomSessionModel(
        session_id=session_id,
        organization_id=organization_id,
        class_id=payload.class_id,
        created_by=principal.subject,
        state="configured",
        revision=1,
        configuration=configuration,
    )
    db.add(record)
    db.flush()
    db.add(
        Be1SessionStageModel(
            session_id=session_id,
            organization_id=organization_id,
            stage="preparation",
            stage_revision=1,
        )
    )
    audit(
        db,
        organization_id=organization_id,
        actor=principal.subject,
        action="session.configure",
        resource_type="session",
        resource_id=session_id,
    )
    event(
        db,
        organization_id=organization_id,
        aggregate_id=session_id,
        event_type="be1.session.configured.v1",
        payload={"class_id": payload.class_id, "session_id": session_id},
        revision=1,
    )
    commit(db)
    return {**session_response(record), "join_code": join_code}


@router.get("/organizations/{organization_id}/sessions/{session_id}")
def read_session(
    organization_id: str,
    session_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    record = get_session(db, organization_id, session_id)
    require_assignment(db, principal, organization_id, class_id=record.class_id)
    return session_response(record)


@router.get("/organizations/{organization_id}/sessions/{session_id}/learning-stage")
def read_learning_stage(
    organization_id: str,
    session_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    record = get_session(db, organization_id, session_id)
    require_assignment(
        db, principal, organization_id, roles={"school_admin", "teacher"}, class_id=record.class_id
    )
    stage = db.get(Be1SessionStageModel, session_id)
    if stage is None:
        raise failure(409, "LEARNING_STAGE_UNAVAILABLE", "Session stage was not initialized")
    return {
        "contract": "Be1SharedLearningStageV1",
        "session_id": session_id,
        "stage": stage.stage,
        "stage_revision": stage.stage_revision,
        "lifecycle_state": record.state,
        "entered_at": stage.entered_at,
        "last_command_id": stage.last_command_id,
    }


@router.get("/organizations/{organization_id}/sessions/{session_id}/roster")
def read_session_roster(
    organization_id: str,
    session_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    record = get_session(db, organization_id, session_id)
    require_assignment(
        db, principal, organization_id, roles={"school_admin", "teacher"}, class_id=record.class_id
    )
    memberships = db.scalars(
        select(SessionMembershipModel)
        .where(
            SessionMembershipModel.organization_id == organization_id,
            SessionMembershipModel.session_id == session_id,
            SessionMembershipModel.state == "admitted",
        )
        .order_by(SessionMembershipModel.admitted_at, SessionMembershipModel.child_id)
    ).all()
    profiles = {
        profile.child_id: profile
        for profile in db.scalars(
            select(ManagedProfileModel).where(
                ManagedProfileModel.organization_id == organization_id,
                ManagedProfileModel.class_id == record.class_id,
            )
        ).all()
    }
    groups = db.scalars(
        select(SessionGroupModel)
        .where(
            SessionGroupModel.organization_id == organization_id,
            SessionGroupModel.session_id == session_id,
        )
        .order_by(SessionGroupModel.created_at, SessionGroupModel.group_id)
    ).all()
    turns = db.scalars(
        select(ChildTurnModel)
        .where(
            ChildTurnModel.organization_id == organization_id,
            ChildTurnModel.session_id == session_id,
        )
        .order_by(ChildTurnModel.started_at, ChildTurnModel.turn_id)
    ).all()
    return {
        "contract": "Be1SessionRosterV1",
        "session_id": session_id,
        "session_revision": record.revision,
        "members": [
            {
                "membership_id": member.membership_id,
                "child_id": member.child_id,
                "display_name": profiles[member.child_id].display_name
                if member.child_id in profiles
                else "",
                "group_id": member.group_id,
                "progress": member.progress,
                "admitted_at": member.admitted_at,
                "device_grant_id": member.device_grant_id,
            }
            for member in memberships
        ],
        "groups": [
            {
                "group_id": group.group_id,
                "display_name": group.display_name,
                "state": group.state,
            }
            for group in groups
        ],
        "turns": [
            {
                "turn_id": turn.turn_id,
                "child_id": turn.child_id,
                "group_id": turn.group_id,
                "canvas_id": turn.canvas_id,
                "state": turn.state,
                "document_epoch": turn.document_epoch,
                "started_at": turn.started_at,
                "ended_at": turn.ended_at,
            }
            for turn in turns
        ],
    }


@router.get("/organizations/{organization_id}/sessions/{session_id}/outcome")
def read_session_outcome(
    organization_id: str,
    session_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    record = get_session(db, organization_id, session_id)
    require_assignment(
        db, principal, organization_id, roles={"school_admin", "teacher"}, class_id=record.class_id
    )
    outcome = db.get(Be1SessionOutcomeModel, session_id)
    return {
        "contract": "Be1SessionOutcomeReadV1",
        "session_id": session_id,
        "lifecycle_state": record.state,
        "outcome": None
        if outcome is None
        else {
            "value": outcome.outcome,
            "reason_category": outcome.reason_category,
            "teacher_note": outcome.teacher_note,
            "outcome_refs": outcome.outcome_refs,
            "stage_revision": outcome.stage_revision,
            "created_at": outcome.created_at,
        },
    }


def _load_stage_command_receipt(
    db: Session,
    *,
    organization_id: str,
    session_id: str,
    command_type: str,
    idempotency_key: str,
    request_fingerprint: str,
) -> dict[str, object] | None:
    receipt = db.get(
        Be1SessionCommandReceiptModel,
        (organization_id, session_id, command_type, idempotency_key),
    )
    if receipt is None:
        return None
    if not secrets.compare_digest(receipt.request_fingerprint, request_fingerprint):
        raise failure(
            409, "IDEMPOTENCY_KEY_REUSED", "Idempotency-Key was used with a different request"
        )
    return receipt.response_payload


def _draft_canvas_refs(
    db: Session, organization_id: str, session_id: str, group_id: str
) -> list[dict[str, object]]:
    turns = db.scalars(
        select(ChildTurnModel).where(
            ChildTurnModel.organization_id == organization_id,
            ChildTurnModel.session_id == session_id,
            ChildTurnModel.group_id == group_id,
        )
    ).all()
    refs: list[dict[str, object]] = []
    for turn in turns:
        accepted_revision = db.scalar(
            select(func.max(CoreCanvasOperationModel.resulting_revision)).where(
                CoreCanvasOperationModel.organization_id == organization_id,
                CoreCanvasOperationModel.session_id == session_id,
                CoreCanvasOperationModel.canvas_id == turn.canvas_id,
                CoreCanvasOperationModel.document_epoch == turn.document_epoch,
            )
        )
        checkpoint = db.scalar(
            select(CoreCanvasCheckpointModel)
            .where(
                CoreCanvasCheckpointModel.organization_id == organization_id,
                CoreCanvasCheckpointModel.session_id == session_id,
                CoreCanvasCheckpointModel.canvas_id == turn.canvas_id,
                CoreCanvasCheckpointModel.document_epoch == turn.document_epoch,
            )
            .order_by(CoreCanvasCheckpointModel.revision.desc())
            .limit(1)
        )
        refs.append(
            {
                "turn_id": turn.turn_id,
                "canvas_id": turn.canvas_id,
                "document_epoch": turn.document_epoch,
                "accepted_revision": accepted_revision or 0,
                "checkpoint_id": checkpoint.checkpoint_id if checkpoint is not None else None,
                "checkpoint_revision": checkpoint.revision if checkpoint is not None else None,
            }
        )
    return refs


@router.post("/organizations/{organization_id}/sessions/{session_id}/learning-stage/advance")
def advance_learning_stage(
    organization_id: str,
    session_id: str,
    payload: StageAdvanceRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    key = _require_idempotency_key(idempotency_key)
    record = _lock_session(db, organization_id, session_id)
    require_assignment(
        db, principal, organization_id, roles={"school_admin", "teacher"}, class_id=record.class_id
    )
    fingerprint = _fingerprint(payload.model_dump(mode="json"))
    replay = _load_stage_command_receipt(
        db,
        organization_id=organization_id,
        session_id=session_id,
        command_type="stage_advance",
        idempotency_key=key,
        request_fingerprint=fingerprint,
    )
    if replay is not None:
        return replay
    stage = db.scalar(
        select(Be1SessionStageModel)
        .where(
            Be1SessionStageModel.organization_id == organization_id,
            Be1SessionStageModel.session_id == session_id,
        )
        .with_for_update()
    )
    if stage is None:
        raise failure(409, "LEARNING_STAGE_UNAVAILABLE", "Session stage was not initialized")
    if stage.stage_revision != payload.expected_stage_revision:
        raise failure(409, "STALE_STAGE_REVISION", "Learning stage changed; reload before retrying")
    if record.state != "active":
        raise failure(
            409, "SESSION_NOT_ACTIVE", "Learning stage advances require an active session"
        )
    try:
        next_stage = require_next_stage(stage.stage, payload.target_stage)
    except StageTransitionError as exc:
        raise failure(409, "INVALID_STAGE_TRANSITION", str(exc)) from None

    if stage.stage == "assistance" and next_stage == "sharing":
        help_pending = db.scalar(
            select(SessionMembershipModel.membership_id).where(
                SessionMembershipModel.organization_id == organization_id,
                SessionMembershipModel.session_id == session_id,
                SessionMembershipModel.state == "admitted",
                SessionMembershipModel.help_requested.is_(True),
            )
        )
        if help_pending is not None:
            raise failure(
                409,
                "ASSISTANCE_REVIEW_PENDING",
                "Requested assistance has no approved completion contract",
            )
        if payload.assistance_disposition != "not_needed":
            raise failure(
                409,
                "ASSISTANCE_DISPOSITION_REQUIRED",
                "Record not_needed before leaving Assistance",
            )

    if stage.stage == "sharing" and next_stage == "knowledge":
        published_gallery = db.scalar(
            select(GallerySnapshotModel.gallery_id).where(
                GallerySnapshotModel.organization_id == organization_id,
                GallerySnapshotModel.session_id == session_id,
                GallerySnapshotModel.state == "published",
            )
        )
        if published_gallery is None:
            raise failure(
                409,
                "PUBLISHED_GALLERY_REQUIRED",
                "Publish a consent-checked class gallery before continuing",
            )
    if stage.stage in {"knowledge", "off_screen", "reflection"}:
        raise failure(
            409,
            "SRS_STAGE_CONTRACT_UNAVAILABLE",
            "This stage needs its approved media, activity or child-reflection contract "
            "before it can advance",
        )

    groups = db.scalars(
        select(SessionGroupModel).where(
            SessionGroupModel.organization_id == organization_id,
            SessionGroupModel.session_id == session_id,
            SessionGroupModel.state.in_(["active", "locked"]),
        )
    ).all()
    if stage.stage == "explore_draw" and next_stage == "assistance":
        for group in groups:
            turn = db.scalar(
                select(ChildTurnModel).where(
                    ChildTurnModel.organization_id == organization_id,
                    ChildTurnModel.session_id == session_id,
                    ChildTurnModel.group_id == group.group_id,
                ).limit(1)
            )
            if turn is None:
                raise failure(
                    409,
                    "DRAWING_RECEIPT_REQUIRED",
                    "Every active group needs a server-issued drawing turn before leaving "
                    "Explore & Draw",
                )
            saved_operation = db.scalar(
                select(CoreCanvasOperationModel.operation_id)
                .where(
                    CoreCanvasOperationModel.organization_id == organization_id,
                    CoreCanvasOperationModel.session_id == session_id,
                    CoreCanvasOperationModel.canvas_id == turn.canvas_id,
                    CoreCanvasOperationModel.document_epoch == turn.document_epoch,
                )
                .limit(1)
            )
            saved_checkpoint = db.scalar(
                select(CoreCanvasCheckpointModel.checkpoint_id)
                .where(
                    CoreCanvasCheckpointModel.organization_id == organization_id,
                    CoreCanvasCheckpointModel.session_id == session_id,
                    CoreCanvasCheckpointModel.canvas_id == turn.canvas_id,
                    CoreCanvasCheckpointModel.document_epoch == turn.document_epoch,
                )
                .limit(1)
            )
            if saved_operation is None and saved_checkpoint is None:
                raise failure(
                    409,
                    "DRAWING_RECEIPT_REQUIRED",
                    "A durable drawing operation or checkpoint is required before leaving "
                    "Explore & Draw",
                )
    unfinished_group_ids: set[str] = set()
    for group in groups:
        incomplete = db.scalar(
            select(SessionMembershipModel.membership_id).where(
                SessionMembershipModel.organization_id == organization_id,
                SessionMembershipModel.session_id == session_id,
                SessionMembershipModel.group_id == group.group_id,
                SessionMembershipModel.state == "admitted",
                SessionMembershipModel.progress != "completed",
            )
        )
        if incomplete is not None:
            unfinished_group_ids.add(group.group_id)
    declared = set(payload.unfinished_group_ids)
    if declared != unfinished_group_ids:
        raise failure(
            409,
            "UNFINISHED_GROUP_SET_MISMATCH",
            "Reload the group list and declare every unfinished group before advancing",
        )
    if unfinished_group_ids and payload.unfinished_group_disposition != "save_draft":
        raise failure(409, "GROUP_DRAFT_REQUIRED", "Save unfinished group work before advancing")

    now = datetime.now(UTC)
    new_revision = stage.stage_revision + 1
    draft_ids: list[str] = []
    for group_id in sorted(unfinished_group_ids):
        draft_id = str(uuid4())
        db.add(
            Be1GroupDraftModel(
                draft_id=draft_id,
                organization_id=organization_id,
                session_id=session_id,
                group_id=group_id,
                stage_revision=new_revision,
                disposition="save_draft",
                durable_canvas_refs=_draft_canvas_refs(db, organization_id, session_id, group_id),
                created_by=principal.subject,
            )
        )
        draft_ids.append(draft_id)
    previous_stage = stage.stage
    stage.stage = next_stage
    stage.stage_revision = new_revision
    stage.entered_at = now
    stage.last_command_id = key
    db.add(
        Be1SessionStageEventModel(
            event_id=str(uuid4()),
            organization_id=organization_id,
            session_id=session_id,
            from_stage=previous_stage,
            to_stage=next_stage,
            stage_revision=new_revision,
            command_id=key,
            actor=principal.subject,
            disposition={
                "assistance_disposition": payload.assistance_disposition or "",
                "unfinished_group_disposition": payload.unfinished_group_disposition or "",
                "draft_ids": draft_ids,
            },
        )
    )
    audit(
        db,
        organization_id=organization_id,
        actor=principal.subject,
        action="session.learning_stage.advance",
        resource_type="session",
        resource_id=session_id,
    )
    session_event(
        db,
        session=record,
        event_type="be1.session.learning_stage_advanced.v1",
        payload={"session_id": session_id, "from_stage": previous_stage, "to_stage": next_stage},
    )
    response: dict[str, object] = {
        "contract": "Be1SharedLearningStageReceiptV1",
        "session_id": session_id,
        "stage": next_stage,
        "stage_revision": new_revision,
        "session_revision": record.revision,
        "command_id": key,
        "saved_drafts": draft_ids,
        "assistance_disposition": payload.assistance_disposition,
    }
    db.add(
        Be1SessionCommandReceiptModel(
            organization_id=organization_id,
            session_id=session_id,
            command_type="stage_advance",
            idempotency_key=key,
            request_fingerprint=fingerprint,
            response_payload=response,
        )
    )
    commit(db)
    return response


def _transition(
    db: Session,
    record: ClassroomSessionModel,
    *,
    expected_revision: int,
    action: str,
    actor: str,
) -> dict[str, object]:
    record = _lock_session(db, record.organization_id, record.session_id)
    if record.revision != expected_revision:
        raise failure(409, "STALE_SESSION_REVISION", "Session changed; reload before retrying")
    now = datetime.now(UTC)
    stage: Be1SessionStageModel | None = None
    next_stage: str | None = None
    if action in {"lobby", "start"}:
        stage = db.scalar(
            select(Be1SessionStageModel)
            .where(
                Be1SessionStageModel.organization_id == record.organization_id,
                Be1SessionStageModel.session_id == record.session_id,
            )
            .with_for_update()
        )
        expected_stage = "preparation" if action == "lobby" else "join"
        next_stage = "join" if action == "lobby" else "explore_draw"
        if stage is None or stage.stage != expected_stage:
            raise failure(
                409, "LEARNING_STAGE_CONFLICT", "Reload the class learning stage before retrying"
            )
    consent_ready = True
    if action == "start":
        members = db.scalars(
            select(SessionMembershipModel).where(
                SessionMembershipModel.organization_id == record.organization_id,
                SessionMembershipModel.session_id == record.session_id,
                SessionMembershipModel.state == "admitted",
            )
        ).all()
        purpose_ref = str(record.configuration.get("purpose_ref", ""))
        consent_ready = bool(members) and not any(
            not consent_is_effective(
                db,
                organization_id=record.organization_id,
                class_id=record.class_id,
                child_id=member.child_id,
                purpose_ref=purpose_ref,
            )
            for member in members
        )
        if not consent_ready:
            deny_pending_consent(
                db,
                organization_id=record.organization_id,
                actor=actor,
                resource_type="session",
                resource_id=record.session_id,
                action="session.start",
            )

    try:
        next_state = Be1RuntimePolicy.next_session_state(
            record.state,
            SessionAction(action),
            consent_ready=consent_ready,
        )
    except (ValueError, Be1PolicyError) as exc:
        code = exc.code if isinstance(exc, Be1PolicyError) else "INVALID_SESSION_TRANSITION"
        raise failure(409, code, str(exc)) from None
    record.state = next_state
    if action == "start":
        record.started_at = now
        pending_grants = db.scalars(
            select(DeviceGrantModel)
            .where(
                DeviceGrantModel.organization_id == record.organization_id,
                DeviceGrantModel.session_id == record.session_id,
                DeviceGrantModel.state == "pending",
            )
            .with_for_update()
        ).all()
        for grant in pending_grants:
            grant.state = "revoked"
        audit(
            db,
            organization_id=record.organization_id,
            actor=actor,
            action="device.pending_requests.revoke_on_start",
            resource_type="session",
            resource_id=record.session_id,
        )
    elif action == "finish":
        record.ended_at = now
        record.retain_until = now + timedelta(days=_RETENTION_DAYS)
        turns = db.scalars(
            select(ChildTurnModel).where(
                ChildTurnModel.organization_id == record.organization_id,
                ChildTurnModel.session_id == record.session_id,
                ChildTurnModel.state == "active",
            )
        ).all()
        for turn in turns:
            turn.state = "closed"
            turn.ended_at = now
    record.revision += 1
    if stage is not None and next_stage is not None:
        previous_stage = stage.stage
        stage.stage = next_stage
        stage.stage_revision += 1
        stage.entered_at = now
        stage.last_command_id = f"session-{action}-{record.revision}"
        db.add(
            Be1SessionStageEventModel(
                event_id=str(uuid4()),
                organization_id=record.organization_id,
                session_id=record.session_id,
                from_stage=previous_stage,
                to_stage=next_stage,
                stage_revision=stage.stage_revision,
                command_id=stage.last_command_id,
                actor=actor,
                disposition={"source": f"session.{action}"},
            )
        )
    audit(
        db,
        organization_id=record.organization_id,
        actor=actor,
        action=f"session.{action}",
        resource_type="session",
        resource_id=record.session_id,
    )
    event(
        db,
        organization_id=record.organization_id,
        aggregate_id=record.session_id,
        event_type=f"be1.session.{action}.v1",
        payload={"session_id": record.session_id, "state": record.state},
        revision=record.revision,
    )
    commit(db)
    return session_response(record)


def _do_transition(
    organization_id: str,
    session_id: str,
    payload: SessionTransitionRequest,
    action: str,
    principal: VerifiedPrincipal,
    db: Session,
) -> dict[str, object]:
    record = _lock_session(db, organization_id, session_id)
    require_assignment(
        db, principal, organization_id, roles={"school_admin", "teacher"}, class_id=record.class_id
    )
    return _transition(
        db,
        record,
        expected_revision=payload.expected_revision,
        action=action,
        actor=principal.subject,
    )


@router.post("/organizations/{organization_id}/sessions/{session_id}/lobby")
def open_lobby(
    organization_id: str,
    session_id: str,
    payload: SessionTransitionRequest,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return _do_transition(organization_id, session_id, payload, "lobby", principal, db)


@router.post("/organizations/{organization_id}/sessions/{session_id}/start")
def start_session(
    organization_id: str,
    session_id: str,
    payload: SessionTransitionRequest,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return _do_transition(organization_id, session_id, payload, "start", principal, db)


@router.post("/organizations/{organization_id}/sessions/{session_id}/pause")
def pause_session(
    organization_id: str,
    session_id: str,
    payload: SessionTransitionRequest,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return _do_transition(organization_id, session_id, payload, "pause", principal, db)


@router.post("/organizations/{organization_id}/sessions/{session_id}/resume")
def resume_session(
    organization_id: str,
    session_id: str,
    payload: SessionTransitionRequest,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return _do_transition(organization_id, session_id, payload, "resume", principal, db)


@router.post("/organizations/{organization_id}/sessions/{session_id}/finish")
def finish_session(
    organization_id: str,
    session_id: str,
    payload: SessionTransitionRequest,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return _do_transition(organization_id, session_id, payload, "finish", principal, db)


@router.post("/organizations/{organization_id}/sessions/{session_id}/completion")
def complete_session(
    organization_id: str,
    session_id: str,
    payload: CompleteSessionRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    key = _require_idempotency_key(idempotency_key)
    record = _lock_session(db, organization_id, session_id)
    require_assignment(
        db, principal, organization_id, roles={"school_admin", "teacher"}, class_id=record.class_id
    )
    fingerprint = _fingerprint(payload.model_dump(mode="json"))
    replay = _load_stage_command_receipt(
        db,
        organization_id=organization_id,
        session_id=session_id,
        command_type="completion",
        idempotency_key=key,
        request_fingerprint=fingerprint,
    )
    if replay is not None:
        return replay
    stage = db.scalar(
        select(Be1SessionStageModel)
        .where(
            Be1SessionStageModel.organization_id == organization_id,
            Be1SessionStageModel.session_id == session_id,
        )
        .with_for_update()
    )
    if stage is None:
        raise failure(409, "LEARNING_STAGE_UNAVAILABLE", "Session stage was not initialized")
    if stage.stage_revision != payload.expected_stage_revision:
        raise failure(409, "STALE_STAGE_REVISION", "Learning stage changed; reload before retrying")
    if payload.outcome == "completed" and stage.stage != "completion":
        raise failure(409, "COMPLETION_STAGE_REQUIRED", "The final SRS stage must be reached first")
    if record.state not in {"active", "paused"}:
        raise failure(
            409, "SESSION_NOT_RUNNING", "Only a started session can be completed or ended early"
        )
    if db.get(Be1SessionOutcomeModel, session_id) is not None:
        raise failure(
            409, "SESSION_OUTCOME_ALREADY_RECORDED", "Session outcome has already been recorded"
        )
    try:
        next_state = Be1RuntimePolicy.next_session_state(
            record.state, SessionAction("finish"), consent_ready=True
        )
    except (ValueError, Be1PolicyError) as exc:
        code = exc.code if isinstance(exc, Be1PolicyError) else "INVALID_SESSION_TRANSITION"
        raise failure(409, code, str(exc)) from None

    now = datetime.now(UTC)
    record.state = next_state
    record.ended_at = now
    record.retain_until = now + timedelta(days=_RETENTION_DAYS)
    for turn in db.scalars(
        select(ChildTurnModel)
        .where(
            ChildTurnModel.organization_id == organization_id,
            ChildTurnModel.session_id == session_id,
            ChildTurnModel.state == "active",
        )
        .with_for_update()
    ).all():
        turn.state = "closed"
        turn.ended_at = now
    outcome = Be1SessionOutcomeModel(
        session_id=session_id,
        organization_id=organization_id,
        outcome=payload.outcome,
        reason_category=payload.reason_category,
        teacher_note=payload.teacher_note,
        outcome_refs=payload.outcome_refs,
        stage_revision=stage.stage_revision,
        command_id=key,
        created_by=principal.subject,
    )
    db.add(outcome)
    record.revision += 1
    event(
        db,
        organization_id=organization_id,
        aggregate_id=session_id,
        event_type=f"be1.session.{payload.outcome}.v1",
        payload={"session_id": session_id, "outcome": payload.outcome},
        revision=record.revision,
    )
    audit(
        db,
        organization_id=organization_id,
        actor=principal.subject,
        action=f"session.{payload.outcome}",
        resource_type="session",
        resource_id=session_id,
    )
    response: dict[str, object] = {
        "contract": "Be1SessionOutcomeReceiptV1",
        "session_id": session_id,
        "lifecycle_state": record.state,
        "outcome": payload.outcome,
        "reason_category": payload.reason_category,
        "teacher_note": payload.teacher_note,
        "stage_revision": stage.stage_revision,
        "session_revision": record.revision,
        "command_id": key,
    }
    db.add(
        Be1SessionCommandReceiptModel(
            organization_id=organization_id,
            session_id=session_id,
            command_type="completion",
            idempotency_key=key,
            request_fingerprint=fingerprint,
            response_payload=response,
        )
    )
    commit(db)
    return response


@router.post(
    "/organizations/{organization_id}/sessions/{session_id}/join",
    status_code=status.HTTP_202_ACCEPTED,
)
def request_device_join(
    organization_id: str, session_id: str, payload: JoinRequest, db: Session = Depends(get_db)
) -> dict[str, object]:
    record = _lock_session(db, organization_id, session_id)
    expected_hash = record.configuration.get("join_code_sha256")
    actual_hash = hashlib.sha256(payload.join_code.encode("utf-8")).hexdigest()
    if (
        record.state != "lobby"
        or not isinstance(expected_hash, str)
        or not secrets.compare_digest(actual_hash, expected_hash)
    ):
        raise failure(404, "JOIN_UNAVAILABLE", "Session is not accepting this join request")
    return _create_pending_device_grant(record, payload.device_key, db)


def _create_pending_device_grant(
    record: ClassroomSessionModel, device_key: str, db: Session
) -> dict[str, object]:
    organization_id = record.organization_id
    session_id = record.session_id
    device_hash = hashlib.sha256(device_key.encode("utf-8")).hexdigest()
    prior = db.scalar(
        select(DeviceGrantModel).where(
            DeviceGrantModel.organization_id == organization_id,
            DeviceGrantModel.session_id == session_id,
            DeviceGrantModel.device_key_hash == device_hash,
            DeviceGrantModel.state.in_(["pending", "admitted"]),
        )
    )
    if prior is not None:
        return {
            "contract": "Be1DeviceJoinV1",
            "grant_id": prior.grant_id,
            "state": prior.state,
            "session_revision": record.revision,
        }
    grant_id = str(uuid4())
    grant = DeviceGrantModel(
        grant_id=grant_id,
        organization_id=organization_id,
        session_id=session_id,
        device_key_hash=device_hash,
        state="pending",
        requested_by="device",
    )
    db.add(grant)
    db.flush()
    audit(
        db,
        organization_id=organization_id,
        actor=None,
        action="device.join_request",
        resource_type="device_grant",
        resource_id=grant_id,
    )
    session_event(
        db,
        session=record,
        event_type="be1.device.join_requested.v1",
        payload={"grant_id": grant_id, "session_id": session_id},
    )
    commit(db)
    return {
        "contract": "Be1DeviceJoinV1",
        "grant_id": grant_id,
        "state": "pending",
        "session_revision": record.revision,
    }


@router.post(
    "/organizations/{organization_id}/sessions/{session_id}/room-code/rotate",
    status_code=status.HTTP_200_OK,
)
def rotate_room_code(
    organization_id: str,
    session_id: str,
    runtime: Be1Runtime = Depends(get_runtime),
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    record = _lock_session(db, organization_id, session_id)
    require_assignment(
        db, principal, organization_id, roles={"school_admin", "teacher"}, class_id=record.class_id
    )
    if record.state != "lobby":
        raise failure(409, "ROOM_CODE_CLOSED", "Room code is unavailable outside the lobby")
    room_code = ""
    digest = ""
    for _ in range(128):
        room_code = _new_room_code()
        digest = _room_code_hmac(runtime, room_code)
        owner = db.scalar(
            select(Be1RoomCodeModel.session_id).where(Be1RoomCodeModel.room_code_hmac == digest)
        )
        if owner is None or owner == session_id:
            break
    else:
        raise failure(503, "ROOM_CODE_UNAVAILABLE", "Could not allocate a unique room code")

    room = db.get(Be1RoomCodeModel, session_id)
    if room is None:
        room = Be1RoomCodeModel(
            session_id=session_id,
            organization_id=organization_id,
            room_code_hmac=digest,
            key_version="v1",
        )
        db.add(room)
    else:
        room.organization_id = organization_id
        room.room_code_hmac = digest
        room.key_version = "v1"
        room.rotated_at = datetime.now(UTC)
    audit(
        db,
        organization_id=organization_id,
        actor=principal.subject,
        action="session.room_code.rotate",
        resource_type="session",
        resource_id=session_id,
    )
    commit(db)
    return {
        "contract": "Be1SharedRoomCodeV1",
        "session_id": session_id,
        "room_code": room_code,
        "state": "lobby",
    }


@router.post("/room-code/join", status_code=status.HTTP_202_ACCEPTED)
def request_room_code_join(
    payload: JoinRoomCodeRequest,
    request: Request,
    runtime: Be1Runtime = Depends(get_runtime),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    source_hash = _room_code_source_hash(runtime, request)
    _lock_room_code_source(db, source_hash)
    now = datetime.now(UTC)
    if _room_code_source_throttled(db, source_hash, now):
        raise failure(429, "ROOM_CODE_RATE_LIMITED", "Room-code attempts are temporarily limited")

    code_hash = _room_code_hmac(runtime, payload.room_code)
    room = db.scalar(select(Be1RoomCodeModel).where(Be1RoomCodeModel.room_code_hmac == code_hash))
    record = _lock_session(db, room.organization_id, room.session_id) if room is not None else None
    if record is None or record.state != "lobby":
        _record_invalid_room_code(db, source_hash, now)
        commit(db)
        raise failure(404, "JOIN_UNAVAILABLE", "Session is not accepting this join request")

    # Recheck after taking the session lock so a concurrent Teacher Start cannot admit after close.
    current_room = db.scalar(
        select(Be1RoomCodeModel)
        .where(Be1RoomCodeModel.session_id == record.session_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if current_room is None or not secrets.compare_digest(current_room.room_code_hmac, code_hash):
        _record_invalid_room_code(db, source_hash, now)
        commit(db)
        raise failure(404, "JOIN_UNAVAILABLE", "Session is not accepting this join request")
    return _create_pending_device_grant(record, payload.device_key, db)


@router.post("/device-grants/{grant_id}/join-status")
def read_join_status(
    grant_id: str,
    device_key: str | None = Header(default=None, alias="X-Be1-Device-Key"),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    if not device_key or len(device_key) < 24 or len(device_key) > 256:
        raise failure(401, "DEVICE_AUTHENTICATION_REQUIRED", "Current device proof is required")
    grant = db.get(DeviceGrantModel, grant_id)
    digest = hashlib.sha256(device_key.encode("utf-8")).hexdigest()
    if grant is None or not secrets.compare_digest(grant.device_key_hash, digest):
        raise failure(401, "INVALID_DEVICE_CREDENTIAL", "Current device proof was rejected")
    response: dict[str, object] = {
        "contract": "Be1DeviceJoinStatusV1",
        "grant_id": grant_id,
        "state": grant.state,
    }
    if grant.state == "admitted":
        response["organization_id"] = grant.organization_id
        response["session_id"] = grant.session_id
    return response


@router.get("/organizations/{organization_id}/sessions/{session_id}/join-requests")
def list_join_requests(
    organization_id: str,
    session_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    record = get_session(db, organization_id, session_id)
    require_assignment(
        db, principal, organization_id, roles={"school_admin", "teacher"}, class_id=record.class_id
    )
    rows = db.scalars(
        select(DeviceGrantModel)
        .where(
            DeviceGrantModel.organization_id == organization_id,
            DeviceGrantModel.session_id == session_id,
            DeviceGrantModel.state == "pending",
        )
        .order_by(DeviceGrantModel.created_at)
    ).all()
    return {
        "contract": "Be1PendingJoinListV1",
        "items": [{"grant_id": row.grant_id, "requested_at": row.created_at} for row in rows],
    }


@router.post(
    "/organizations/{organization_id}/sessions/{session_id}/join-requests/{grant_id}/admit"
)
def admit_device(
    organization_id: str,
    session_id: str,
    grant_id: str,
    payload: AdmitDeviceRequest,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    record = _lock_session(db, organization_id, session_id)
    require_assignment(
        db, principal, organization_id, roles={"school_admin", "teacher"}, class_id=record.class_id
    )
    if record.state != "lobby":
        raise failure(409, "JOIN_WINDOW_CLOSED", "New join requests are closed for this session")
    grant = db.scalar(
        select(DeviceGrantModel)
        .where(
            DeviceGrantModel.organization_id == organization_id,
            DeviceGrantModel.session_id == session_id,
            DeviceGrantModel.grant_id == grant_id,
            DeviceGrantModel.state == "pending",
        )
        .with_for_update()
    )
    if grant is None:
        raise failure(404, "JOIN_REQUEST_NOT_FOUND", "Pending join request was not found")
    profile = db.scalar(
        select(ManagedProfileModel).where(
            ManagedProfileModel.organization_id == organization_id,
            ManagedProfileModel.class_id == record.class_id,
            ManagedProfileModel.child_id == payload.child_id,
            ManagedProfileModel.state == "active",
        )
    )
    if profile is None:
        raise failure(404, "PROFILE_NOT_FOUND", "Profile was not found in this class")
    if not consent_is_effective(
        db,
        organization_id=organization_id,
        class_id=record.class_id,
        child_id=payload.child_id,
        purpose_ref=str(record.configuration.get("purpose_ref", "")),
    ):
        deny_pending_consent(
            db,
            organization_id=organization_id,
            actor=principal.subject,
            resource_type="device_grant",
            resource_id=grant_id,
            action="device.admit",
        )
    membership = db.scalar(
        select(SessionMembershipModel).where(
            SessionMembershipModel.organization_id == organization_id,
            SessionMembershipModel.session_id == session_id,
            SessionMembershipModel.child_id == payload.child_id,
        )
    )
    if membership is not None and membership.state == "admitted":
        raise failure(409, "MEMBER_ALREADY_ADMITTED", "Child already has an admitted device")
    now = datetime.now(UTC)
    if membership is None:
        membership = SessionMembershipModel(
            membership_id=str(uuid4()),
            organization_id=organization_id,
            session_id=session_id,
            class_id=record.class_id,
            child_id=payload.child_id,
            state="admitted",
            device_grant_id=grant_id,
            admitted_at=now,
        )
        db.add(membership)
    else:
        # Re-admission reuses the unique membership row but starts without the previous
        # group/turn binding. Teacher must explicitly assign and start a new turn.
        membership.state = "admitted"
        membership.group_id = None
        membership.device_grant_id = grant_id
        membership.progress = "not_started"
        membership.help_requested = False
        membership.admitted_at = now
    grant.state = "admitted"
    grant.admitted_child_id = payload.child_id
    grant.admitted_by = principal.subject
    db.add(membership)
    db.flush()
    audit(
        db,
        organization_id=organization_id,
        actor=principal.subject,
        action="device.admit",
        resource_type="device_grant",
        resource_id=grant_id,
    )
    session_event(
        db,
        session=record,
        event_type="be1.device.admitted.v1",
        payload={"grant_id": grant_id, "membership_id": membership.membership_id},
    )
    commit(db)
    return {
        "contract": "Be1AdmissionV1",
        "membership_id": membership.membership_id,
        "state": "admitted",
        "session_revision": record.revision,
    }


@router.post(
    "/organizations/{organization_id}/sessions/{session_id}/join-requests/{grant_id}/revoke"
)
def revoke_device_grant(
    organization_id: str,
    session_id: str,
    grant_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    record = get_session(db, organization_id, session_id)
    require_assignment(
        db, principal, organization_id, roles={"school_admin", "teacher"}, class_id=record.class_id
    )
    grant = db.scalar(
        select(DeviceGrantModel).where(
            DeviceGrantModel.organization_id == organization_id,
            DeviceGrantModel.session_id == session_id,
            DeviceGrantModel.grant_id == grant_id,
        )
    )
    if grant is None:
        raise failure(404, "DEVICE_GRANT_NOT_FOUND", "Device grant was not found")
    grant.state = "revoked"
    membership = db.scalar(
        select(SessionMembershipModel).where(
            SessionMembershipModel.organization_id == organization_id,
            SessionMembershipModel.session_id == session_id,
            SessionMembershipModel.device_grant_id == grant_id,
            SessionMembershipModel.state == "admitted",
        )
    )
    if membership is not None:
        membership.state = "removed"
    turns = db.scalars(
        select(ChildTurnModel).where(
            ChildTurnModel.organization_id == organization_id,
            ChildTurnModel.session_id == session_id,
            ChildTurnModel.device_grant_id == grant_id,
            ChildTurnModel.state == "active",
        )
    ).all()
    for turn in turns:
        turn.state = "revoked"
        turn.ended_at = datetime.now(UTC)
    audit(
        db,
        organization_id=organization_id,
        actor=principal.subject,
        action="device.revoke",
        resource_type="device_grant",
        resource_id=grant_id,
    )
    session_event(
        db, session=record, event_type="be1.device.revoked.v1", payload={"grant_id": grant_id}
    )
    commit(db)
    return {"contract": "Be1DeviceGrantV1", "grant_id": grant_id, "state": "revoked"}


@router.post(
    "/organizations/{organization_id}/sessions/{session_id}/device-grants/{grant_id}/refresh"
)
def refresh_device_grant(
    organization_id: str,
    session_id: str,
    grant_id: str,
    device_key: str | None = Header(default=None, alias="X-Be1-Device-Key"),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    if not device_key or len(device_key) < 24 or len(device_key) > 256:
        raise failure(401, "DEVICE_AUTHENTICATION_REQUIRED", "Current device proof is required")
    grant = db.scalar(
        select(DeviceGrantModel).where(
            DeviceGrantModel.organization_id == organization_id,
            DeviceGrantModel.session_id == session_id,
            DeviceGrantModel.grant_id == grant_id,
        )
    )
    previous_hash = hashlib.sha256(device_key.encode("utf-8")).hexdigest()
    if grant is None or not secrets.compare_digest(grant.device_key_hash, previous_hash):
        raise failure(401, "INVALID_DEVICE_CREDENTIAL", "Current device proof was rejected")
    if grant.state == "pending":
        return {"contract": "Be1DeviceGrantRefreshV1", "grant_id": grant_id, "state": "pending"}
    if grant.state == "revoked":
        return {"contract": "Be1DeviceGrantRefreshV1", "grant_id": grant_id, "state": "revoked"}
    if grant.state != "admitted":
        raise failure(401, "INVALID_DEVICE_CREDENTIAL", "Current device proof was rejected")
    record = get_session(db, organization_id, session_id)
    if record.state not in {"lobby", "active", "paused"}:
        raise failure(409, "DEVICE_GRANT_INACTIVE", "Session no longer accepts device refresh")
    replacement_key = secrets.token_urlsafe(32)
    grant.device_key_hash = hashlib.sha256(replacement_key.encode("utf-8")).hexdigest()
    audit(
        db,
        organization_id=organization_id,
        actor=f"device:{grant_id}",
        action="device.grant.refresh",
        resource_type="device_grant",
        resource_id=grant_id,
    )
    session_event(
        db,
        session=record,
        event_type="be1.device.grant_refreshed.v1",
        payload={"grant_id": grant_id, "session_id": session_id},
    )
    commit(db)
    return {
        "contract": "Be1DeviceGrantRefreshV1",
        "grant_id": grant_id,
        "device_key": replacement_key,
        "state": "admitted",
    }


@router.post(
    "/organizations/{organization_id}/sessions/{session_id}/groups",
    status_code=status.HTTP_201_CREATED,
)
def create_group(
    organization_id: str,
    session_id: str,
    payload: CreateGroupRequest,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    record = get_session(db, organization_id, session_id)
    require_assignment(
        db, principal, organization_id, roles={"school_admin", "teacher"}, class_id=record.class_id
    )
    if record.state not in {"lobby", "active", "paused"}:
        raise failure(409, "SESSION_NOT_OPEN", "Groups can only be configured in an open session")
    group_id = str(uuid4())
    group = SessionGroupModel(
        group_id=group_id,
        organization_id=organization_id,
        session_id=session_id,
        display_name=payload.display_name,
        created_by=principal.subject,
    )
    db.add(group)
    db.flush()
    audit(
        db,
        organization_id=organization_id,
        actor=principal.subject,
        action="group.create",
        resource_type="group",
        resource_id=group_id,
    )
    session_event(
        db,
        session=record,
        event_type="be1.group.created.v1",
        payload={"group_id": group_id, "session_id": session_id},
    )
    commit(db)
    return {
        "contract": "Be1SessionGroupV1",
        "group_id": group_id,
        "display_name": group.display_name,
        "state": group.state,
        "session_revision": record.revision,
    }


@router.put(
    "/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/members/{child_id}"
)
def assign_member_to_group(
    organization_id: str,
    session_id: str,
    group_id: str,
    child_id: str,
    payload: AssignMemberRequest,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    record = get_session(db, organization_id, session_id)
    require_assignment(
        db, principal, organization_id, roles={"school_admin", "teacher"}, class_id=record.class_id
    )
    membership = db.scalar(
        select(SessionMembershipModel).where(
            SessionMembershipModel.organization_id == organization_id,
            SessionMembershipModel.session_id == session_id,
            SessionMembershipModel.child_id == child_id,
            SessionMembershipModel.state == "admitted",
        )
    )
    if membership is None:
        raise failure(404, "ADMITTED_MEMBER_NOT_FOUND", "Admitted member was not found")
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
    if payload.expected_revision != record.revision:
        raise failure(409, "STALE_SESSION_REVISION", "Session changed; reload before retrying")
    if not consent_is_effective(
        db,
        organization_id=organization_id,
        class_id=record.class_id,
        child_id=child_id,
        purpose_ref=str(record.configuration.get("purpose_ref", "")),
    ):
        deny_pending_consent(
            db,
            organization_id=organization_id,
            actor=principal.subject,
            resource_type="membership",
            resource_id=membership.membership_id,
            action="group.assign_member",
        )
    if membership.group_id == group_id:
        return {
            "contract": "Be1GroupAssignmentV1",
            "membership_id": membership.membership_id,
            "group_id": group_id,
            "session_revision": record.revision,
        }
    active_turns = db.scalars(
        select(ChildTurnModel).where(
            ChildTurnModel.organization_id == organization_id,
            ChildTurnModel.session_id == session_id,
            ChildTurnModel.child_id == child_id,
            ChildTurnModel.state == "active",
        )
    ).all()
    now = datetime.now(UTC)
    for turn in active_turns:
        turn.state = "closed"
        turn.ended_at = now
    previous_group_id = membership.group_id
    membership.group_id = group_id
    audit(
        db,
        organization_id=organization_id,
        actor=principal.subject,
        action="group.assign_member",
        resource_type="membership",
        resource_id=membership.membership_id,
    )
    session_event(
        db,
        session=record,
        event_type="be1.group.member_assigned.v1",
        payload={
            "membership_id": membership.membership_id,
            "previous_group_id": previous_group_id or "",
            "group_id": group_id,
        },
    )
    commit(db)
    return {
        "contract": "Be1GroupAssignmentV1",
        "membership_id": membership.membership_id,
        "group_id": group_id,
        "session_revision": record.revision,
    }


@router.post("/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/control")
def control_group(
    organization_id: str,
    session_id: str,
    group_id: str,
    payload: GroupControlRequest,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    record = get_session(db, organization_id, session_id)
    require_assignment(
        db, principal, organization_id, roles={"school_admin", "teacher"}, class_id=record.class_id
    )
    if record.revision != payload.expected_revision:
        raise failure(409, "STALE_SESSION_REVISION", "Session changed; reload before retrying")
    if record.state not in {"lobby", "active", "paused"}:
        raise failure(409, "SESSION_NOT_OPEN", "Group control requires an open session")
    group = db.scalar(
        select(SessionGroupModel).where(
            SessionGroupModel.organization_id == organization_id,
            SessionGroupModel.session_id == session_id,
            SessionGroupModel.group_id == group_id,
        )
    )
    if group is None:
        raise failure(404, "GROUP_NOT_FOUND", "Group was not found")
    next_state = "locked" if payload.action == "lock" else "active"
    if group.state == next_state:
        return {
            "contract": "Be1GroupControlV1",
            "group_id": group_id,
            "state": group.state,
            "session_revision": record.revision,
        }
    if group.state not in {"active", "locked"}:
        raise failure(409, "INVALID_GROUP_TRANSITION", "Archived groups cannot be reopened")
    group.state = next_state
    if next_state == "locked":
        now = datetime.now(UTC)
        active_turns = db.scalars(
            select(ChildTurnModel).where(
                ChildTurnModel.organization_id == organization_id,
                ChildTurnModel.session_id == session_id,
                ChildTurnModel.group_id == group_id,
                ChildTurnModel.state == "active",
            )
        ).all()
        for turn in active_turns:
            turn.state = "closed"
            turn.ended_at = now
    audit(
        db,
        organization_id=organization_id,
        actor=principal.subject,
        action=f"group.{payload.action}",
        resource_type="group",
        resource_id=group_id,
    )
    session_event(
        db,
        session=record,
        event_type=("be1.group.locked.v1" if payload.action == "lock" else "be1.group.unlocked.v1"),
        payload={"group_id": group_id, "state": group.state},
    )
    commit(db)
    return {
        "contract": "Be1GroupControlV1",
        "group_id": group_id,
        "state": group.state,
        "session_revision": record.revision,
    }


@router.post(
    "/organizations/{organization_id}/sessions/{session_id}/memberships/{membership_id}/progress"
)
def update_progress(
    organization_id: str,
    session_id: str,
    membership_id: str,
    payload: ProgressRequest,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    record = get_session(db, organization_id, session_id)
    require_assignment(
        db,
        principal,
        organization_id,
        roles={"school_admin", "teacher", "guide"},
        class_id=record.class_id,
    )
    membership = db.scalar(
        select(SessionMembershipModel).where(
            SessionMembershipModel.organization_id == organization_id,
            SessionMembershipModel.session_id == session_id,
            SessionMembershipModel.membership_id == membership_id,
        )
    )
    if membership is None:
        raise failure(404, "MEMBERSHIP_NOT_FOUND", "Membership was not found")
    if not consent_is_effective(
        db,
        organization_id=organization_id,
        class_id=membership.class_id,
        child_id=membership.child_id,
        purpose_ref=str(record.configuration.get("purpose_ref", "")),
    ):
        deny_pending_consent(
            db,
            organization_id=organization_id,
            actor=principal.subject,
            resource_type="membership",
            resource_id=membership_id,
            action="membership.progress",
        )
    membership.progress = payload.progress
    audit(
        db,
        organization_id=organization_id,
        actor=principal.subject,
        action="membership.progress",
        resource_type="membership",
        resource_id=membership_id,
    )
    session_event(
        db,
        session=record,
        event_type="be1.membership.progress.v1",
        payload={"membership_id": membership_id, "progress": payload.progress},
    )
    commit(db)
    return {
        "contract": "Be1MemberProgressV1",
        "membership_id": membership_id,
        "progress": payload.progress,
    }


@router.post(
    "/organizations/{organization_id}/sessions/{session_id}/memberships/{membership_id}/help"
)
def request_help(
    organization_id: str,
    session_id: str,
    membership_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    record = get_session(db, organization_id, session_id)
    require_assignment(
        db,
        principal,
        organization_id,
        roles={"school_admin", "teacher", "guide"},
        class_id=record.class_id,
    )
    membership = db.scalar(
        select(SessionMembershipModel).where(
            SessionMembershipModel.organization_id == organization_id,
            SessionMembershipModel.session_id == session_id,
            SessionMembershipModel.membership_id == membership_id,
        )
    )
    if membership is None:
        raise failure(404, "MEMBERSHIP_NOT_FOUND", "Membership was not found")
    if not consent_is_effective(
        db,
        organization_id=organization_id,
        class_id=membership.class_id,
        child_id=membership.child_id,
        purpose_ref=str(record.configuration.get("purpose_ref", "")),
    ):
        deny_pending_consent(
            db,
            organization_id=organization_id,
            actor=principal.subject,
            resource_type="membership",
            resource_id=membership_id,
            action="membership.help_request",
        )
    membership.help_requested = True
    audit(
        db,
        organization_id=organization_id,
        actor=principal.subject,
        action="membership.help_request",
        resource_type="membership",
        resource_id=membership_id,
    )
    session_event(
        db,
        session=record,
        event_type="be1.membership.help_requested.v1",
        payload={"membership_id": membership_id},
    )
    commit(db)
    return {"contract": "Be1HelpRequestV1", "membership_id": membership_id, "state": "open"}


@router.post(
    "/organizations/{organization_id}/sessions/{session_id}/memberships/{membership_id}/leave"
)
def leave_session(
    organization_id: str,
    session_id: str,
    membership_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    record = get_session(db, organization_id, session_id)
    require_assignment(
        db, principal, organization_id, roles={"school_admin", "teacher"}, class_id=record.class_id
    )
    membership = db.scalar(
        select(SessionMembershipModel).where(
            SessionMembershipModel.organization_id == organization_id,
            SessionMembershipModel.session_id == session_id,
            SessionMembershipModel.membership_id == membership_id,
        )
    )
    if membership is None:
        raise failure(404, "MEMBERSHIP_NOT_FOUND", "Membership was not found")
    membership.state = "left"
    if membership.device_grant_id is not None:
        grant = db.get(DeviceGrantModel, membership.device_grant_id)
        if grant is not None and grant.organization_id == organization_id:
            grant.state = "revoked"
    turns = db.scalars(
        select(ChildTurnModel).where(
            ChildTurnModel.organization_id == organization_id,
            ChildTurnModel.session_id == session_id,
            ChildTurnModel.child_id == membership.child_id,
            ChildTurnModel.state == "active",
        )
    ).all()
    for turn in turns:
        turn.state = "closed"
        turn.ended_at = datetime.now(UTC)
    audit(
        db,
        organization_id=organization_id,
        actor=principal.subject,
        action="membership.leave",
        resource_type="membership",
        resource_id=membership_id,
    )
    session_event(
        db,
        session=record,
        event_type="be1.membership.left.v1",
        payload={"membership_id": membership_id},
    )
    commit(db)
    return {"contract": "Be1MembershipStateV1", "membership_id": membership_id, "state": "left"}


@router.post(
    "/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/turns/{child_id}"
)
def start_child_turn(
    organization_id: str,
    session_id: str,
    group_id: str,
    child_id: str,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    record = get_session(db, organization_id, session_id)
    require_assignment(
        db, principal, organization_id, roles={"school_admin", "teacher"}, class_id=record.class_id
    )
    if record.state != "active":
        raise failure(409, "SESSION_NOT_ACTIVE", "A turn requires an active session")
    group = db.scalar(
        select(SessionGroupModel).where(
            SessionGroupModel.organization_id == organization_id,
            SessionGroupModel.session_id == session_id,
            SessionGroupModel.group_id == group_id,
            SessionGroupModel.state == "active",
        )
    )
    if group is None:
        raise failure(409, "GROUP_NOT_WRITABLE", "A turn requires an active group")
    membership = db.scalar(
        select(SessionMembershipModel).where(
            SessionMembershipModel.organization_id == organization_id,
            SessionMembershipModel.session_id == session_id,
            SessionMembershipModel.child_id == child_id,
            SessionMembershipModel.state == "admitted",
            SessionMembershipModel.group_id == group_id,
        )
    )
    if membership is None or not membership.device_grant_id:
        raise failure(
            409, "ADMITTED_MEMBER_REQUIRED", "An admitted member with an assigned group is required"
        )
    if not consent_is_effective(
        db,
        organization_id=organization_id,
        class_id=record.class_id,
        child_id=child_id,
        purpose_ref=str(record.configuration.get("purpose_ref", "")),
    ):
        deny_pending_consent(
            db,
            organization_id=organization_id,
            actor=principal.subject,
            resource_type="child_turn",
            resource_id=child_id,
            action="turn.start",
        )
    open_turns = db.scalars(
        select(ChildTurnModel).where(
            ChildTurnModel.organization_id == organization_id,
            ChildTurnModel.session_id == session_id,
            ChildTurnModel.group_id == group_id,
            ChildTurnModel.state == "active",
        )
    ).all()
    for old_turn in open_turns:
        old_turn.state = "closed"
        old_turn.ended_at = datetime.now(UTC)
    canvas_id = group_id
    canvas_aggregate = db.get(CoreAggregateRevisionModel, canvas_id)
    if canvas_aggregate is None:
        db.add(
            CoreAggregateRevisionModel(
                aggregate_id=canvas_id,
                organization_id=organization_id,
                revision=1,
            )
        )
        db.flush()
    latest_checkpoint = db.scalar(
        select(CoreCanvasCheckpointModel)
        .where(
            CoreCanvasCheckpointModel.organization_id == organization_id,
            CoreCanvasCheckpointModel.canvas_id == canvas_id,
        )
        .order_by(
            CoreCanvasCheckpointModel.document_epoch.desc(),
            CoreCanvasCheckpointModel.revision.desc(),
        )
    )
    document_epoch = latest_checkpoint.document_epoch if latest_checkpoint is not None else 1
    turn_id = str(uuid4())
    db.add(
        ChildTurnModel(
            turn_id=turn_id,
            organization_id=organization_id,
            session_id=session_id,
            child_id=child_id,
            group_id=group_id,
            canvas_id=canvas_id,
            document_epoch=document_epoch,
            device_grant_id=membership.device_grant_id,
            state="active",
            created_by=principal.subject,
        )
    )
    audit(
        db,
        organization_id=organization_id,
        actor=principal.subject,
        action="turn.start",
        resource_type="child_turn",
        resource_id=turn_id,
    )
    session_event(
        db,
        session=record,
        event_type="be1.turn.started.v1",
        payload={"turn_id": turn_id, "group_id": group_id},
    )
    commit(db)
    return {
        "contract": "Be1ActiveTurnV1",
        "turn_id": turn_id,
        "child_id": child_id,
        "group_id": group_id,
        "state": "active",
    }


__all__ = ["router"]
