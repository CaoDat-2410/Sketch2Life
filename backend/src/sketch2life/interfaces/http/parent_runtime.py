"""Parent-only identity, database, and service dependencies."""

# FastAPI dependency declarations intentionally use Depends in defaults.
# ruff: noqa: B008

from __future__ import annotations

from collections.abc import Iterator

from fastapi import Depends, Header, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_roles import ParentRoleReader
from sketch2life.application.services.parent_profiles import ParentProfileService
from sketch2life.domain.parent_profiles import ParentProfileError
from sketch2life.infrastructure.identity.firebase_token_verifier import (
    IdentityVerificationUnavailable,
)
from sketch2life.infrastructure.persistence.be1_parent_role_adapter import (
    Be1ParentRoleAdapter,
)
from sketch2life.infrastructure.persistence.parent_profile_repository import (
    SqlParentProfileRepository,
)
from sketch2life.interfaces.http.be1_runtime import Be1Runtime, get_runtime

_bearer = HTTPBearer(auto_error=False)


def get_parent_runtime(request: Request) -> Be1Runtime:
    runtime: Be1Runtime | None = getattr(request.app.state, "be1_runtime", None)
    if runtime is None:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "IDENTITY_PROVIDER_UNAVAILABLE",
                "message": "Identity verification is unavailable",
            },
        )
    return runtime


async def get_parent_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    runtime: Be1Runtime = Depends(get_parent_runtime),
) -> VerifiedPrincipal:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail={"code": "AUTH_REQUIRED", "message": "A verified bearer token is required"},
        )
    if runtime.settings.auth_provider != "firebase" or not runtime.settings.firebase_project_id:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "IDENTITY_PROVIDER_UNAVAILABLE",
                "message": "Identity verification is unavailable",
            },
        )
    try:
        return await runtime.identity_verifier.verify(credentials.credentials)
    except IdentityVerificationUnavailable as exc:
        cause = exc.__cause__
        if isinstance(cause, ImportError):
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "IDENTITY_PROVIDER_UNAVAILABLE",
                    "message": "Identity verification is unavailable",
                },
            ) from None
        if cause is not None and _is_expired_firebase_token(cause):
            raise HTTPException(
                status_code=401,
                detail={"code": "TOKEN_EXPIRED", "message": "The bearer token has expired"},
            ) from None
        raise HTTPException(
            status_code=401,
            detail={"code": "INVALID_TOKEN", "message": "The bearer token could not be verified"},
        ) from None


def _is_expired_firebase_token(cause: BaseException) -> bool:
    try:
        from firebase_admin.auth import ExpiredIdTokenError
    except ImportError:
        return False
    return isinstance(cause, ExpiredIdTokenError)


def get_parent_db(runtime: Be1Runtime = Depends(get_runtime)) -> Iterator[Session]:
    assert runtime.session_factory is not None
    session = runtime.session_factory()
    try:
        yield session
    except SQLAlchemyError:
        session.rollback()
        raise HTTPException(
            status_code=503,
            detail={
                "code": "PARENT_STORE_UNAVAILABLE",
                "message": "The profile store is unavailable",
            },
        ) from None
    finally:
        session.close()


def get_parent_profile_service(
    db: Session = Depends(get_parent_db),
    runtime: Be1Runtime = Depends(get_runtime),
) -> ParentProfileService:
    enabled = runtime.settings.env in {"local", "test"} and runtime.settings.synthetic_pilot_enabled
    return ParentProfileService(SqlParentProfileRepository(db), synthetic_enabled=enabled)


def get_parent_role_reader(
    runtime: Be1Runtime = Depends(get_runtime),
) -> ParentRoleReader:
    if runtime.session_factory is None:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "PARENT_STORE_UNAVAILABLE",
                "message": "The profile store is unavailable",
            },
        )
    return Be1ParentRoleAdapter(runtime.session_factory)


def parent_request_id(request: Request) -> str:
    return getattr(request.state, "parent_request_id", "")


def parent_idempotency_key(
    value: str = Header(alias="Idempotency-Key"),
) -> str:
    return value


__all__ = [
    "get_parent_db",
    "get_parent_principal",
    "get_parent_profile_service",
    "get_parent_role_reader",
    "get_parent_runtime",
    "parent_idempotency_key",
    "parent_request_id",
    "ParentProfileError",
]
