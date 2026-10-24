"""Shared organization-scoped transaction helpers for BE1 HTTP adapters."""

from __future__ import annotations

from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.services.be1_runtime import (
    AdultAssignment,
    Be1PolicyError,
    Be1RuntimePolicy,
)
from sketch2life.contracts.schemas.be1_runtime import Be1Error
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    ClassroomModel,
    ClassroomSessionModel,
    ConsentRecordModel,
    OrganizationAssignmentModel,
)
from sketch2life.infrastructure.persistence.core_models import (
    CoreAggregateRevisionModel,
    CoreAuditEntryModel,
    CoreOutboxEventModel,
)

BE1_ERROR_RESPONSES = {
    401: {"model": Be1Error, "description": "Authentication or device credential is required"},
    403: {"model": Be1Error, "description": "The caller is not authorized for this resource"},
    404: {"model": Be1Error, "description": "The scoped resource was not found"},
    409: {"model": Be1Error, "description": "The command conflicts with current state"},
    410: {"model": Be1Error, "description": "The requested artifact is no longer available"},
    413: {"model": Be1Error, "description": "The request exceeds a supported size limit"},
    415: {"model": Be1Error, "description": "The request media type is not supported"},
    422: {"model": Be1Error, "description": "The request does not match the API contract"},
    429: {"model": Be1Error, "description": "The request is temporarily rate limited"},
    503: {"model": Be1Error, "description": "A required backend dependency is unavailable"},
    500: {"model": Be1Error, "description": "An unexpected server error occurred"},
}


def failure(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})


def commit(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise failure(
            409, "RESOURCE_CONFLICT", "The command conflicts with current records"
        ) from None
    except StaleDataError:
        db.rollback()
        raise failure(
            409, "STALE_AGGREGATE", "Concurrent change detected; reload before retrying"
        ) from None


def require_assignment(
    db: Session,
    principal: VerifiedPrincipal,
    organization_id: str,
    *,
    roles: set[str] | frozenset[str] | None = None,
    class_id: str | None = None,
) -> tuple[OrganizationAssignmentModel, ...]:
    identity = db.get(AdultIdentityModel, principal.subject)
    statement = select(OrganizationAssignmentModel).where(
        OrganizationAssignmentModel.organization_id == organization_id,
        OrganizationAssignmentModel.subject == principal.subject,
        OrganizationAssignmentModel.active.is_(True),
    )
    rows = tuple(db.scalars(statement).all())
    assignments = tuple(
        AdultAssignment(
            organization_id=row.organization_id,
            subject=row.subject,
            class_id=row.class_id,
            role=row.role,
            active=row.active,
            assignment_id=row.assignment_id,
        )
        for row in rows
    )
    try:
        allowed = Be1RuntimePolicy.authorize_adult(
            principal=principal,
            identity_active=identity is not None and identity.state == "active",
            identity_issuer=identity.issuer if identity is not None else None,
            assignments=assignments,
            organization_id=organization_id,
            roles=roles,
            class_id=class_id,
        )
    except Be1PolicyError as exc:
        raise failure(403, exc.code, str(exc)) from None
    allowed_ids = {row.assignment_id for row in allowed}
    return tuple(row for row in rows if row.assignment_id in allowed_ids)


def get_class(db: Session, organization_id: str, class_id: str) -> ClassroomModel:
    row = db.scalar(
        select(ClassroomModel).where(
            ClassroomModel.organization_id == organization_id,
            ClassroomModel.class_id == class_id,
            ClassroomModel.state == "active",
        )
    )
    if row is None:
        raise failure(404, "CLASS_NOT_FOUND", "Class was not found")
    return row


def get_session(db: Session, organization_id: str, session_id: str) -> ClassroomSessionModel:
    row = db.scalar(
        select(ClassroomSessionModel).where(
            ClassroomSessionModel.organization_id == organization_id,
            ClassroomSessionModel.session_id == session_id,
        )
    )
    if row is None:
        raise failure(404, "SESSION_NOT_FOUND", "Session was not found")
    return row


def audit(
    db: Session,
    *,
    organization_id: str,
    actor: str | None,
    action: str,
    resource_type: str,
    resource_id: str,
    decision: str = "allowed",
) -> None:
    db.add(
        CoreAuditEntryModel(
            audit_id=str(uuid4()),
            organization_id=organization_id,
            actor_ref=actor,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            decision=decision,
        )
    )


def event(
    db: Session,
    *,
    organization_id: str,
    aggregate_id: str,
    event_type: str,
    payload: dict[str, str],
    revision: int | None = None,
) -> int:
    aggregate = db.get(CoreAggregateRevisionModel, aggregate_id)
    if aggregate is None:
        next_revision = revision or 1
        aggregate = CoreAggregateRevisionModel(
            aggregate_id=aggregate_id,
            organization_id=organization_id,
            revision=next_revision,
        )
        db.add(aggregate)
    else:
        if aggregate.organization_id != organization_id:
            raise failure(409, "AGGREGATE_SCOPE_CONFLICT", "Aggregate scope is inconsistent")
        next_revision = revision if revision is not None else aggregate.revision + 1
        aggregate.revision = next_revision
    db.add(
        CoreOutboxEventModel(
            event_id=str(uuid4()),
            event_type=event_type,
            organization_id=organization_id,
            aggregate_id=aggregate_id,
            aggregate_revision=next_revision,
            payload=payload,
            status="pending",
            attempt_count=0,
        )
    )
    return next_revision


def session_event(
    db: Session,
    *,
    session: ClassroomSessionModel,
    event_type: str,
    payload: dict[str, str],
) -> int:
    session.revision += 1
    return event(
        db,
        organization_id=session.organization_id,
        aggregate_id=session.session_id,
        event_type=event_type,
        payload=payload,
        revision=session.revision,
    )


def consent_is_effective(
    db: Session,
    *,
    organization_id: str,
    class_id: str,
    child_id: str,
    purpose_ref: str,
) -> bool:
    return (
        db.scalar(
            select(ConsentRecordModel.consent_id).where(
                ConsentRecordModel.organization_id == organization_id,
                ConsentRecordModel.class_id == class_id,
                ConsentRecordModel.child_id == child_id,
                ConsentRecordModel.purpose_ref == purpose_ref,
                ConsentRecordModel.state == "effective",
            )
        )
        is not None
    )


def deny_pending_consent(
    db: Session,
    *,
    organization_id: str,
    actor: str,
    resource_type: str,
    resource_id: str,
    action: str,
) -> None:
    audit(
        db,
        organization_id=organization_id,
        actor=actor,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        decision="denied_consent_pending",
    )
    commit(db)
    raise failure(
        409,
        "CONSENT_NOT_EFFECTIVE",
        "Consent verification and purpose approval are pending; child data is blocked",
    )


def session_response(row: ClassroomSessionModel) -> dict[str, object]:
    configuration = dict(row.configuration)
    configuration.pop("join_code_sha256", None)
    return {
        "contract": "Be1SessionV1",
        "session_id": row.session_id,
        "organization_id": row.organization_id,
        "class_id": row.class_id,
        "state": row.state,
        "revision": row.revision,
        "active_phase": row.active_phase,
        "configuration": configuration,
        "started_at": row.started_at,
        "ended_at": row.ended_at,
        "retain_until": row.retain_until,
    }


__all__ = [
    "audit",
    "commit",
    "consent_is_effective",
    "deny_pending_consent",
    "event",
    "failure",
    "get_class",
    "get_session",
    "require_assignment",
    "session_event",
    "session_response",
]
