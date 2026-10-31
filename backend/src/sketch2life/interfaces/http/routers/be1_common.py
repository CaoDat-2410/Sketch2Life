"""Shared organization-scoped transaction helpers for BE1 HTTP adapters."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
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
from sketch2life.domain.eligibility import (
    EligibilityBasis,
    EligibilityDecision,
    EligibilityFacts,
    EligibilityScope,
    ProvisionalDataOrigin,
    SyntheticEligibilityProof,
    evaluate_eligibility,
)
from sketch2life.infrastructure.config.settings import Settings
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
from sketch2life.infrastructure.persistence.core_store import (
    load_profile_origin,
    load_synthetic_proof,
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
    purpose_ref: str | None,
) -> bool:
    if purpose_ref is None:
        # A profile without a consent purpose (SYNTHETIC_DEV) has no legal consent to look up.
        return False
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


def eligibility_decision(
    db: Session,
    *,
    session: ClassroomSessionModel,
    child_id: str,
    legal_effective: Callable[..., bool],
    settings: Settings | None,
    now: datetime | None = None,
) -> EligibilityDecision:
    """Fetch current server-side facts and apply the pure typed decision.

    ``legal_effective`` is the existing effective-consent lookup, passed in by the caller so a
    caller-module monkeypatch of ``consent_is_effective`` keeps its effect. Missing settings
    mean the pilot is off, so only the legal basis can be granted.
    """
    organization_id = session.organization_id
    class_id = session.class_id
    purpose_ref = str(session.configuration.get("purpose_ref", ""))
    run_ref = session.configuration.get("pilot_run_ref")
    stored_origin = load_profile_origin(
        db, organization_id=organization_id, class_id=class_id, child_id=child_id
    )
    # Before this feature the legal gate never looked at the profile row, only at an effective
    # consent record. A Child with no active profile row (for example one archived after being
    # admitted) therefore keeps that legal-only behavior; it can never be synthetic, because a
    # synthetic decision needs a SYNTHETIC_DEV profile row and a proof that references it.
    profile_origin = (
        stored_origin if stored_origin is not None else ProvisionalDataOrigin.LEGACY_UNCLASSIFIED
    )
    proof: SyntheticEligibilityProof | None = None
    if profile_origin == ProvisionalDataOrigin.SYNTHETIC_DEV:
        # Only a synthetic profile consults the proof table, so the legal path never depends on
        # it. A proof cannot exist for another origin: it references the profile row, the
        # operator store refuses to issue one for a non-synthetic profile, and the origin has
        # no update path. (The pure evaluator still denies a stray proof on a legal profile.)
        proof = load_synthetic_proof(
            db,
            organization_id=organization_id,
            class_id=class_id,
            child_id=child_id,
            purpose_ref=purpose_ref,
        )
        if proof is not None and proof.session_id is None:
            # `pilot_run_ref` is written into the session configuration by whoever creates the
            # session, so the run alone does not identify the operator's intended session. A
            # synthetic proof therefore has to be bound to one session id to count.
            proof = None
    facts = EligibilityFacts(
        profile_origin=profile_origin,
        scope=EligibilityScope(organization_id, class_id, child_id, purpose_ref),
        legal_consent_effective=legal_effective(
            db,
            organization_id=organization_id,
            class_id=class_id,
            child_id=child_id,
            purpose_ref=purpose_ref,
        ),
        proof=proof,
        session_run_ref=run_ref if isinstance(run_ref, str) else None,
        session_id=session.session_id,
        environment=settings.env if settings is not None else None,
        pilot_enabled=settings.synthetic_pilot_enabled if settings is not None else False,
        evaluated_at=now if now is not None else datetime.now(UTC),
    )
    return evaluate_eligibility(facts)


def eligibility_ready(
    db: Session,
    *,
    session: ClassroomSessionModel,
    child_id: str,
    legal_effective: Callable[..., bool],
    settings: Settings | None,
    actor: str,
    audit_action: str | None = None,
) -> bool:
    """True for LEGAL_CONSENT or SYNTHETIC_DEV; the decision never becomes a consent value.

    An accepted synthetic decision is audited (proof id, basis, basis version) only when the
    caller names a state-changing ``audit_action``; per-request device and stroke checks pass
    none. Denials are audited by the caller's existing ``deny_pending_consent``.
    """
    decision = eligibility_decision(
        db, session=session, child_id=child_id, legal_effective=legal_effective, settings=settings
    )
    if decision.basis is EligibilityBasis.SYNTHETIC_DEV and audit_action is not None:
        audit(
            db,
            organization_id=session.organization_id,
            actor=actor,
            action=audit_action,
            resource_type="synthetic_eligibility_proof",
            resource_id=decision.evidence_id or "",
            decision=f"allowed_synthetic_dev:{decision.basis_version}",
        )
    return decision.basis is not EligibilityBasis.DENIED


def eligibility_all_ready(
    db: Session,
    *,
    session: ClassroomSessionModel,
    child_ids: list[str],
    legal_effective: Callable[..., bool],
    settings: Settings | None,
    actor: str,
    audit_action: str,
) -> bool:
    """All Children must be eligible; accepted synthetic decisions are audited only then.

    Every decision is computed before any audit row is added, so a later denial cannot leave
    "allowed" audit rows behind in the transaction that ``deny_pending_consent`` commits.
    """
    decisions = [
        eligibility_decision(
            db,
            session=session,
            child_id=child_id,
            legal_effective=legal_effective,
            settings=settings,
        )
        for child_id in child_ids
    ]
    if not all(decision.basis is not EligibilityBasis.DENIED for decision in decisions):
        return False
    for decision in decisions:
        if decision.basis is EligibilityBasis.SYNTHETIC_DEV:
            audit(
                db,
                organization_id=session.organization_id,
                actor=actor,
                action=audit_action,
                resource_type="synthetic_eligibility_proof",
                resource_id=decision.evidence_id or "",
                decision=f"allowed_synthetic_dev:{decision.basis_version}",
            )
    return True


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
    "eligibility_all_ready",
    "eligibility_decision",
    "eligibility_ready",
    "event",
    "failure",
    "get_class",
    "get_session",
    "require_assignment",
    "session_event",
    "session_response",
]
