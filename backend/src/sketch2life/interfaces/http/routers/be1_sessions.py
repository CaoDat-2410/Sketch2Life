"""Durable BE1 session, admission, grouping and turn lifecycle endpoints."""

# FastAPI dependency declarations intentionally use Depends in defaults.
# ruff: noqa: B008

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.services.be1_runtime import (
    Be1PolicyError,
    Be1RuntimePolicy,
    SessionAction,
)
from sketch2life.contracts.schemas.be1_runtime import (
    AdmitDeviceRequest,
    AssignMemberRequest,
    CreateGroupRequest,
    CreateSessionRequest,
    GroupControlRequest,
    JoinRequest,
    ProgressRequest,
    SessionTransitionRequest,
)
from sketch2life.infrastructure.persistence.be1_models import (
    ChildTurnModel,
    ClassroomSessionModel,
    DeviceGrantModel,
    ManagedProfileModel,
    SessionGroupModel,
    SessionMembershipModel,
)
from sketch2life.infrastructure.persistence.core_models import (
    CoreAggregateRevisionModel,
    CoreCanvasCheckpointModel,
)
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
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

router = APIRouter(
    prefix="/api/be1/v1", tags=["BE1 sessions"], responses=BE1_ERROR_RESPONSES
)
_RETENTION_DAYS = 90


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


def _transition(
    db: Session,
    record: ClassroomSessionModel,
    *,
    expected_revision: int,
    action: str,
    actor: str,
) -> dict[str, object]:
    if record.revision != expected_revision:
        raise failure(409, "STALE_SESSION_REVISION", "Session changed; reload before retrying")
    now = datetime.now(UTC)
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
    record = get_session(db, organization_id, session_id)
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


@router.post(
    "/organizations/{organization_id}/sessions/{session_id}/join",
    status_code=status.HTTP_202_ACCEPTED,
)
def request_device_join(
    organization_id: str, session_id: str, payload: JoinRequest, db: Session = Depends(get_db)
) -> dict[str, object]:
    record = get_session(db, organization_id, session_id)
    expected_hash = record.configuration.get("join_code_sha256")
    actual_hash = hashlib.sha256(payload.join_code.encode("utf-8")).hexdigest()
    if (
        record.state != "lobby"
        or not isinstance(expected_hash, str)
        or not secrets.compare_digest(actual_hash, expected_hash)
    ):
        raise failure(404, "JOIN_UNAVAILABLE", "Session is not accepting this join request")
    device_hash = hashlib.sha256(payload.device_key.encode("utf-8")).hexdigest()
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
    record = get_session(db, organization_id, session_id)
    require_assignment(
        db, principal, organization_id, roles={"school_admin", "teacher"}, class_id=record.class_id
    )
    grant = db.scalar(
        select(DeviceGrantModel).where(
            DeviceGrantModel.organization_id == organization_id,
            DeviceGrantModel.session_id == session_id,
            DeviceGrantModel.grant_id == grant_id,
            DeviceGrantModel.state == "pending",
        )
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
            DeviceGrantModel.state == "admitted",
        )
    )
    previous_hash = hashlib.sha256(device_key.encode("utf-8")).hexdigest()
    if grant is None or not secrets.compare_digest(grant.device_key_hash, previous_hash):
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
        event_type=(
            "be1.group.locked.v1" if payload.action == "lock" else "be1.group.unlocked.v1"
        ),
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
