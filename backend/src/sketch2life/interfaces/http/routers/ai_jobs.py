"""CMD-44 ``GET /jobs/{job_id}`` thin adapter (BE2-01 Phase A candidate).

The router owns transport only: principal resolution is injected, the application service
rechecks authorization/eligibility before any ETag/304 decision, and the role projection is
validated against the DATA-25 candidate schemas. No completion route is exposed here.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from uuid import uuid4

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from sketch2life.application.ports.ai_jobs import Principal, PrincipalRole
from sketch2life.application.services.ai_jobs import AiJobError, AiJobService
from sketch2life.contracts.schemas.ai_jobs import (
    AsyncJobChildEnvelopeV1,
    AsyncJobChildViewV1,
    AsyncJobEnvelopeV1,
    AsyncJobViewV1,
    CollaborationErrorV1,
    ErrorBodyV1,
    JobStatusMetaV1,
)

CANDIDATE_PREFIX = "/api/collaboration/v1"
_ID = re.compile(r"^[A-Za-z0-9_.:-]{1,120}$")
_CACHE_HEADERS = {"Cache-Control": "private, no-cache", "Vary": "Authorization"}

PrincipalResolver = Callable[[Request], Principal | None]


def build_ai_jobs_router(
    service: AiJobService,
    resolve_principal: PrincipalResolver,
    *,
    prefix: str = CANDIDATE_PREFIX,
) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=["ai-jobs-candidate"])

    @router.get("/jobs/{job_id}", response_model=None)
    def get_job(job_id: str, request: Request) -> Response:
        correlation_id = _correlation_id(request)
        principal = resolve_principal(request)
        if principal is None:
            return _error(correlation_id, 401, "UNAUTHENTICATED", "Authentication required.")
        if not _ID.match(job_id):
            return _error(correlation_id, 400, "MALFORMED_REQUEST", "Malformed job id.")
        try:
            result = service.get_job_status(
                principal, job_id, request.headers.get("if-none-match")
            )
        except AiJobError as exc:
            return _error(correlation_id, exc.http_status, exc.code, exc.public_message,
                          retryable=exc.retryable)
        headers = {"ETag": result.etag, **_CACHE_HEADERS}
        if result.not_modified or result.view is None:
            return Response(status_code=304, headers=headers)
        view = result.view
        meta = JobStatusMetaV1(
            resource_revision=int(str(view["job_revision"])),
            poll_after_ms=view["poll_after_ms"],  # type: ignore[arg-type]
            projection=str(result.role),  # type: ignore[arg-type]
        )
        body: AsyncJobEnvelopeV1 | AsyncJobChildEnvelopeV1
        if result.role is PrincipalRole.DEVICE:
            body = AsyncJobChildEnvelopeV1(
                correlation_id=correlation_id,
                data=AsyncJobChildViewV1.model_validate(view, strict=False),
                meta=meta,
            )
        else:
            body = AsyncJobEnvelopeV1(
                correlation_id=correlation_id,
                data=AsyncJobViewV1.model_validate(view, strict=False),
                meta=meta,
            )
        return JSONResponse(body.model_dump(mode="json"), headers=headers)

    return router


def _correlation_id(request: Request) -> str:
    supplied = request.headers.get("x-correlation-id")
    if supplied and _ID.match(supplied):
        return supplied
    return f"corr_{uuid4().hex}"


def _error(
    correlation_id: str, status: int, code: str, message: str, *, retryable: bool = False
) -> JSONResponse:
    body = CollaborationErrorV1(
        correlation_id=correlation_id,
        error=ErrorBodyV1(code=code, message=message, retryable=retryable),
    )
    return JSONResponse(body.model_dump(mode="json"), status_code=status, headers=_CACHE_HEADERS)


__all__ = ["CANDIDATE_PREFIX", "PrincipalResolver", "build_ai_jobs_router"]
