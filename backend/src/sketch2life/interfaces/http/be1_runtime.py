"""Composition and request-scoped dependencies for the real BE1 API."""

# FastAPI dependency declarations intentionally use Depends in defaults.
# ruff: noqa: B008

from __future__ import annotations

import hashlib
import hmac
from collections.abc import Iterator
from dataclasses import dataclass
from uuid import uuid4

from fastapi import Depends, Header, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import Engine, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.domain.core_foundation import (
    ActiveChildTurn,
    CoreScope,
    MembershipState,
    PrincipalKind,
    PrincipalSource,
    SessionMembership,
)
from sketch2life.domain.core_foundation import (
    VerifiedPrincipal as CoreVerifiedPrincipal,
)
from sketch2life.infrastructure.config.settings import Settings, get_core_database_settings
from sketch2life.infrastructure.identity.firebase_token_verifier import (
    FirebaseTokenVerifier,
    IdentityVerificationUnavailable,
)
from sketch2life.infrastructure.persistence.be1_models import (
    ChildTurnModel,
    ClassroomSessionModel,
    ConsentRecordModel,
    DeviceGrantModel,
    SessionGroupModel,
    SessionMembershipModel,
)
from sketch2life.infrastructure.persistence.core_models import (
    CoreAggregateRevisionModel,
    CoreAuditEntryModel,
)
from sketch2life.infrastructure.persistence.database import (
    CoreDatabaseConfigurationError,
    create_core_engine,
    create_core_session_factory,
)
from sketch2life.infrastructure.storage.persistent_local_artifacts import LocalArtifactStore


@dataclass(slots=True)
class Be1Runtime:
    settings: Settings
    engine: Engine | None
    session_factory: sessionmaker[Session] | None
    database_error: str | None
    identity_verifier: FirebaseTokenVerifier
    artifact_store: LocalArtifactStore


@dataclass(frozen=True, slots=True)
class VerifiedDeviceContext:
    principal: CoreVerifiedPrincipal
    grant: DeviceGrantModel
    session: ClassroomSessionModel
    membership: SessionMembership
    turn: ActiveChildTurn
    scope: CoreScope


def build_be1_runtime(settings: Settings) -> Be1Runtime:
    configured = get_core_database_settings().database_url
    database_url = configured.get_secret_value() if configured else None
    engine: Engine | None = None
    session_factory: sessionmaker[Session] | None = None
    database_error: str | None = None
    try:
        engine = create_core_engine(database_url)
        session_factory = create_core_session_factory(engine)
    except CoreDatabaseConfigurationError:
        database_error = "database is not configured for BE1 runtime"
    return Be1Runtime(
        settings=settings,
        engine=engine,
        session_factory=session_factory,
        database_error=database_error,
        identity_verifier=FirebaseTokenVerifier(settings),
        artifact_store=LocalArtifactStore(settings.be1_artifact_root),
    )


def get_runtime(request: Request) -> Be1Runtime:
    runtime: Be1Runtime | None = getattr(request.app.state, "be1_runtime", None)
    if runtime is None:
        raise HTTPException(status_code=503, detail={"code": "BE1_RUNTIME_UNAVAILABLE"})
    if runtime.database_error or runtime.session_factory is None:
        raise HTTPException(
            status_code=503,
            detail={"code": "DATABASE_NOT_CONFIGURED", "message": runtime.database_error},
        )
    return runtime


def get_db(runtime: Be1Runtime = Depends(get_runtime)) -> Iterator[Session]:
    assert runtime.session_factory is not None
    session = runtime.session_factory()
    try:
        # Probe at request start so unavailable PostgreSQL fails closed before any route work.
        session.execute(text("SELECT 1"))
        yield session
    except SQLAlchemyError:
        session.rollback()
        raise HTTPException(status_code=503, detail={"code": "DATABASE_UNAVAILABLE"}) from None
    finally:
        session.close()


_bearer = HTTPBearer(auto_error=False)


async def get_verified_adult(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    runtime: Be1Runtime = Depends(get_runtime),
) -> VerifiedPrincipal:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail={"code": "AUTHENTICATION_REQUIRED"})
    try:
        return await runtime.identity_verifier.verify(credentials.credentials)
    except IdentityVerificationUnavailable as exc:
        if "not configured" in str(exc) or "SDK is required" in str(exc):
            raise HTTPException(
                status_code=503, detail={"code": "IDENTITY_PROVIDER_UNAVAILABLE"}
            ) from None
        raise HTTPException(status_code=401, detail={"code": "INVALID_IDENTITY_TOKEN"}) from None


def get_verified_device(
    grant_id: str | None = Header(default=None, alias="X-Be1-Grant"),
    device_key: str | None = Header(default=None, alias="X-Be1-Device-Key"),
    db: Session = Depends(get_db),
) -> VerifiedDeviceContext:
    if not grant_id or not device_key or len(device_key) < 24 or len(device_key) > 256:
        raise HTTPException(status_code=401, detail={"code": "DEVICE_AUTHENTICATION_REQUIRED"})
    grant = db.scalar(
        select(DeviceGrantModel).where(
            DeviceGrantModel.grant_id == grant_id,
            DeviceGrantModel.state == "admitted",
        )
    )
    digest = hashlib.sha256(device_key.encode("utf-8")).hexdigest()
    if grant is None or not hmac.compare_digest(grant.device_key_hash, digest):
        raise HTTPException(status_code=401, detail={"code": "INVALID_DEVICE_CREDENTIAL"})
    session = db.scalar(
        select(ClassroomSessionModel).where(
            ClassroomSessionModel.organization_id == grant.organization_id,
            ClassroomSessionModel.session_id == grant.session_id,
            ClassroomSessionModel.state == "active",
        )
    )
    if session is None or grant.admitted_child_id is None:
        raise HTTPException(status_code=403, detail={"code": "DEVICE_SCOPE_INACTIVE"})
    membership_row = db.scalar(
        select(SessionMembershipModel).where(
            SessionMembershipModel.organization_id == grant.organization_id,
            SessionMembershipModel.session_id == grant.session_id,
            SessionMembershipModel.child_id == grant.admitted_child_id,
            SessionMembershipModel.device_grant_id == grant.grant_id,
            SessionMembershipModel.state == "admitted",
        )
    )
    if membership_row is None or membership_row.group_id is None:
        raise HTTPException(status_code=403, detail={"code": "DEVICE_MEMBERSHIP_INACTIVE"})
    group = db.scalar(
        select(SessionGroupModel).where(
            SessionGroupModel.organization_id == grant.organization_id,
            SessionGroupModel.session_id == grant.session_id,
            SessionGroupModel.group_id == membership_row.group_id,
        )
    )
    if group is None or group.state != "active":
        raise HTTPException(status_code=403, detail={"code": "GROUP_NOT_WRITABLE"})
    turn_row = db.scalar(
        select(ChildTurnModel).where(
            ChildTurnModel.organization_id == grant.organization_id,
            ChildTurnModel.session_id == grant.session_id,
            ChildTurnModel.child_id == grant.admitted_child_id,
            ChildTurnModel.device_grant_id == grant.grant_id,
            ChildTurnModel.state == "active",
        )
    )
    if turn_row is None:
        raise HTTPException(status_code=403, detail={"code": "ACTIVE_TURN_REQUIRED"})
    consent_id = db.scalar(
        select(ConsentRecordModel.consent_id).where(
            ConsentRecordModel.organization_id == grant.organization_id,
            ConsentRecordModel.class_id == session.class_id,
            ConsentRecordModel.child_id == grant.admitted_child_id,
            ConsentRecordModel.purpose_ref == str(session.configuration.get("purpose_ref", "")),
            ConsentRecordModel.state == "effective",
        )
    )
    if consent_id is None:
        db.add(
            CoreAuditEntryModel(
                audit_id=str(uuid4()),
                organization_id=grant.organization_id,
                actor_ref=f"device:{grant.grant_id}",
                action="device.canvas_auth",
                resource_type="session",
                resource_id=grant.session_id,
                decision="denied_consent_pending",
            )
        )
        db.commit()
        raise HTTPException(
            status_code=409,
            detail={
                "code": "CONSENT_NOT_EFFECTIVE",
                "message": "Child data is blocked while consent verification is pending",
            },
        )
    canvas_revision = db.scalar(
        select(CoreAggregateRevisionModel.revision).where(
            CoreAggregateRevisionModel.aggregate_id == turn_row.canvas_id,
            CoreAggregateRevisionModel.organization_id == grant.organization_id,
        )
    )
    if canvas_revision is None:
        raise HTTPException(status_code=503, detail={"code": "CANVAS_UNAVAILABLE"})
    scope = CoreScope(
        organization_id=grant.organization_id,
        class_id=session.class_id,
        session_id=session.session_id,
        group_id=membership_row.group_id,
        child_id=grant.admitted_child_id,
        canvas_id=turn_row.canvas_id,
    )
    principal = CoreVerifiedPrincipal(
        principal_id=f"device:{grant.grant_id}",
        kind=PrincipalKind.ADMITTED_DEVICE,
        organization_id=grant.organization_id,
        source=PrincipalSource.IDENTITY_PORT,
        verified=True,
        role=None,
        capabilities=frozenset({"canvas.read", "canvas.write"}),
        authorized_scope=scope,
        device_id=grant.grant_id,
    )
    membership = SessionMembership(
        participant_id=grant.admitted_child_id,
        child_id=grant.admitted_child_id,
        organization_id=grant.organization_id,
        class_id=session.class_id,
        session_id=session.session_id,
        state=MembershipState.ADMITTED,
        group_id=membership_row.group_id,
        allowed_canvas_ids=frozenset({turn_row.canvas_id}),
    )
    turn = ActiveChildTurn(
        turn_id=turn_row.turn_id,
        device_id=grant.grant_id,
        organization_id=grant.organization_id,
        session_id=session.session_id,
        canvas_id=turn_row.canvas_id,
        participant_id=grant.admitted_child_id,
        state=turn_row.state,
        revision=canvas_revision,
        document_epoch=turn_row.document_epoch,
    )
    return VerifiedDeviceContext(principal, grant, session, membership, turn, scope)


__all__ = [
    "Be1Runtime",
    "VerifiedDeviceContext",
    "build_be1_runtime",
    "get_db",
    "get_runtime",
    "get_verified_adult",
    "get_verified_device",
]
