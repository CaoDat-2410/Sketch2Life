"""``GET /v1/jobs/{job_id}``: poll one AI job (FEAT-066 T0.4; SRS l.779, l.786, l.806, l.1675).

Live route for adults (Teacher, School Manager, later Parent) with a verified bearer token. The
job must belong to the actor's scope; a missing id, an unregistered job type, another
organization, a role without a read rule and a disabled account all answer one identical 404
``RESOURCE_NOT_FOUND`` (SRS l.865). The route is read-only: there is no completion, cancel or
create route here. It uses the strong ETag of the job revision and answers 304 only after the
actor has been authorised again.

The 200 body is the live ``AiJobStatusV1`` resource defined below. It is deliberately not the
BE2 ``AsyncJobEnvelopeV1`` candidate (strict, pinned to ``0.1-candidate``, no target fields).
Not exposed: organization id, attempt id, internal job type, provider detail and any URL.
"""

# FastAPI dependency declarations intentionally use Depends in defaults.
# ruff: noqa: B008

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from fastapi import Path as PathParam
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_serializer
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from sketch2life.application.job_kinds import (
    ActorMembership,
    JobActor,
    JobNotVisible,
    JobStatusRead,
    JobStatusReader,
    JobTargetKind,
    build_job_kind_registry,
)
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.ai_jobs.read_only import build_read_only_job_repository
from sketch2life.infrastructure.lesson_occurrences.job_lookup import SqlSourceDocumentClassLookup
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.interfaces.http.account_scope import load_granted_scope
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult

# Same opaque-id alphabet as the BE2 candidate route (``routers/ai_jobs.py``); a unit test pins
# the two patterns together.
JOB_ID_PATTERN = r"^[A-Za-z0-9_.:-]{1,120}$"
_OPAQUE_PATTERN = r"^[A-Za-z0-9_.:-]+$"
_CACHE_HEADERS = {"Cache-Control": "private, no-cache", "Vary": "Authorization"}

router = APIRouter(tags=["jobs"])
_LOG = logging.getLogger(__name__)


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class JobProgressStatus(_Strict):
    kind: Literal["unknown", "stages", "percentage"]
    value: float | None = Field(default=None, ge=0, le=100, allow_inf_nan=False)
    stage_label: str | None = Field(default=None, min_length=1, max_length=80)


class JobFailureStatus(_Strict):
    code: str = Field(pattern=r"^[A-Z][A-Z0-9_]{1,79}$")
    retryable: bool
    public_message: str = Field(min_length=1, max_length=200)
    attempts_remaining: int | None = Field(default=None, ge=0)


class JobResultRefStatus(_Strict):
    # The pattern has no "/" so a storage URL can never pass (SRS l.816).
    artifact_ref: str = Field(min_length=1, max_length=120, pattern=_OPAQUE_PATTERN)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


def _utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


class AiJobStatusV1(_Strict):
    """One job status with its version (SRS l.779, l.806). ``job_revision`` is the version."""

    job_id: str = Field(min_length=1, max_length=120, pattern=_OPAQUE_PATTERN)
    target_kind: JobTargetKind
    target_ref: str = Field(min_length=1, max_length=120, pattern=_OPAQUE_PATTERN)
    job_revision: int = Field(ge=1)
    attempt_number: int = Field(ge=1)
    target_revision: int = Field(ge=1)
    input_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    state: Literal[
        "queued",
        "running",
        "succeeded",
        "failed_retryable",
        "failed_exhausted",
        "blocked_unsafe",
        "cancelled",
    ]
    result_disposition: Literal["accepted", "stale", "rejected"] | None
    correlation_id: str = Field(min_length=1, max_length=120, pattern=_OPAQUE_PATTERN)
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    progress: JobProgressStatus
    failure: JobFailureStatus | None
    result_refs: list[JobResultRefStatus] = Field(max_length=32)
    poll_after_ms: int | None = Field(ge=0)

    @field_serializer("created_at", "updated_at", "started_at", "completed_at")
    def _serialize_time(self, value: datetime | None) -> str | None:
        return _utc(value)


class _SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


def get_job_status_reader(request: Request) -> JobStatusReader:
    """Reader over a read-only job repository, built lazily from the BE1 runtime engine."""

    state = request.app.state
    reader: JobStatusReader | None = getattr(state, "job_status_reader", None)
    if reader is None:
        runtime = getattr(state, "be1_runtime", None)
        engine = getattr(runtime, "engine", None)
        if engine is None:
            raise HTTPException(status_code=503, detail={"code": "DATABASE_NOT_CONFIGURED"})
        # T-3b: the kinds that have a producer (the occurrence document extraction) are registered
        # here; every other job type stays unregistered and answers the uniform 404.
        reader = JobStatusReader(
            build_read_only_job_repository(engine),
            build_job_kind_registry(SqlSourceDocumentClassLookup(engine)),
            _SystemClock(),
        )
        state.job_status_reader = reader
    return reader


def _not_found() -> HTTPException:
    return HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND"})


def _resolve_actor(db: Session, principal: VerifiedPrincipal) -> JobActor:
    """Active identity with a role and the matching issuer, else the uniform not-found."""

    identity = db.get(AdultIdentityModel, principal.subject)
    if (
        identity is None
        or identity.state != "active"
        or identity.account_role is None
        or identity.issuer != principal.issuer
    ):
        raise _not_found()

    def membership_for(organization_id: str) -> ActorMembership | None:
        # Extends the T0.2 scope loader (one organization, same rules) instead of re-querying.
        scope = load_granted_scope(db, identity, organization_id=organization_id)
        if scope.truncated:
            # The class list hit its cap, so the membership may be incomplete. A rule that
            # reads ``class_ids`` could wrongly allow or deny; fail closed with the uniform
            # not-found instead of guessing (review R1 F-3; the cap is 500 classes per
            # organization, far above a real Teacher's load).
            return None
        for organization in scope.organizations:
            if organization.organization_id == organization_id:
                class_roles: dict[str, set[str]] = {}
                for item in scope.classes:
                    if item.organization_id == organization_id:
                        class_roles.setdefault(item.class_id, set()).add(item.role)
                return ActorMembership(
                    organization_id=organization_id,
                    roles=frozenset(organization.roles),
                    class_ids=frozenset(class_roles),
                    class_roles={key: frozenset(value) for key, value in class_roles.items()},
                )
        return None

    return JobActor(
        account_id=identity.account_id,
        account_role=identity.account_role,
        membership_for=membership_for,
    )


def _status_body(read: JobStatusRead) -> AiJobStatusV1:
    view = read.status.view
    assert view is not None
    request_ref = view["request_ref"]
    assert isinstance(request_ref, dict)
    return AiJobStatusV1.model_validate(
        {
            "job_id": view["job_id"],
            "target_kind": read.target_kind,
            "target_ref": read.target_ref,
            "job_revision": view["job_revision"],
            "attempt_number": view["attempt_number"],
            "target_revision": request_ref["request_revision"],
            "input_hash": request_ref["input_hash"],
            "state": view["state"],
            "result_disposition": view["result_disposition"],
            "correlation_id": view["correlation_id"],
            "created_at": view["created_at"],
            "updated_at": view["updated_at"],
            "started_at": view["started_at"],
            "completed_at": view["completed_at"],
            "progress": view["progress"],
            "failure": view["failure"],
            "result_refs": view["result_refs"],
            "poll_after_ms": view["poll_after_ms"],
        }
    )


@router.get(
    "/v1/jobs/{job_id}",
    response_model=AiJobStatusV1,
    summary="Poll one AI job",
    description=(
        "Returns the status and version (`job_revision`) of one AI job that belongs to the "
        "scope of the signed-in actor (SRS l.1675). A missing id, a job outside the actor's "
        "scope and a job type that no product kind has registered yet answer one identical 404 "
        "`RESOURCE_NOT_FOUND`. `poll_after_ms` is 2 s to 10 s and absent once the job is "
        "terminal; send the `ETag` back in `If-None-Match` to get 304 while nothing changed "
        "(the actor is authorised again first). `result_refs` stay empty unless the owner of "
        "the job kind says the result is currently eligible. The response is "
        "`Cache-Control: private, no-cache`."
    ),
    responses={
        304: {"description": "Not modified (only after the actor was authorised)"},
        400: {"description": "Malformed job id"},
        401: {"description": "No valid bearer token"},
        404: {"description": "Not found, or outside the actor's scope (one shape)"},
        503: {"description": "Identity or database service is unavailable"},
    },
)
def get_job_status(
    job_id: Annotated[str, PathParam(pattern=JOB_ID_PATTERN)],
    response: Response,
    if_none_match: Annotated[str | None, Header()] = None,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    reader: JobStatusReader = Depends(get_job_status_reader),
) -> AiJobStatusV1 | Response:
    try:
        actor = _resolve_actor(db, principal)
        read = reader.read(actor, job_id, if_none_match)
    except JobNotVisible:
        raise _not_found() from None
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail={"code": "DATABASE_UNAVAILABLE"}) from None
    headers = {"ETag": read.status.etag, **_CACHE_HEADERS}
    if read.status.not_modified:
        return Response(status_code=304, headers=headers)
    try:
        body = _status_body(read)
    except ValidationError:
        # A stored value outside the public patterns (review R1 F-4): answer the envelope's
        # 500, log the job id only, never echo the value.
        _LOG.error("job status row violates the public contract: %s", read.status.etag)
        raise HTTPException(
            status_code=500, detail={"code": "INTERNAL_SERVER_ERROR"}
        ) from None
    response.headers.update(headers)
    return body


__all__ = [
    "JOB_ID_PATTERN",
    "AiJobStatusV1",
    "get_job_status_reader",
    "router",
]
