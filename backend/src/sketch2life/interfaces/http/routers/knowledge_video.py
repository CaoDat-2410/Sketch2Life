"""Candidate CMD-40 thin adapter; no default auth, session or submission binding.

The production app does not register this router. max_body_bytes is an explicit
deployment decision, not a hardcoded production policy. Invalid input/dependency
details are never reflected in errors.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from uuid import uuid4

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from sketch2life.application.knowledge_video_create import VideoCreateService
from sketch2life.application.ports.knowledge_video import VideoRequestContext
from sketch2life.contracts.schemas.knowledge_video import CreateKnowledgeVideo
from sketch2life.domain.knowledge_video.model import VideoError, require_id

_HEADERS = {"Cache-Control": "no-store", "Vary": "Authorization"}
_STATUS = {
    "VIDEO_FORBIDDEN": 403,
    "VIDEO_STALE_CONTEXT": 409,
    "VIDEO_IDEMPOTENCY_CONFLICT": 409,
    "VIDEO_PROFILE_UNAVAILABLE": 409,
    "VIDEO_STRATEGY_UNSUPPORTED": 409,
    "VIDEO_SOURCE_INELIGIBLE": 409,
    "VIDEO_DEPENDENCY_UNAVAILABLE": 503,
}


@dataclass(frozen=True, slots=True)
class VideoIdentity:
    """Verified principal and authorized target session from BE1/server context.

    No child/device/admin role is implicitly allowed: owner resolver/application
    guard must authorize the specific teaching action. Not parsed from body.
    """

    principal_id: str
    organization_id: str
    session_id: str

    def __post_init__(self) -> None:
        for value in (self.principal_id, self.organization_id, self.session_id):
            require_id(value)


def _error(correlation: str, status: int, code: str) -> JSONResponse:
    # Closed fixed message. Do not use str(dependency), Pydantic errors or request bytes.
    return JSONResponse({"correlation_id": correlation,
                         "error": {"code": code, "message": "Request could not be completed.",
                                   "retryable": status == 503}},
                        status_code=status, headers=_HEADERS)


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _no_constant(value: str) -> object:
    raise ValueError("nonfinite JSON constant")


def build_knowledge_video_router(
    service: VideoCreateService,
    resolve_identity: Callable[[Request], VideoIdentity | None],
    *,
    max_body_bytes: int,
    prefix: str = "/api/collaboration/v1",
) -> APIRouter:
    if type(max_body_bytes) is not int or max_body_bytes < 1:
        raise ValueError("positive explicit max_body_bytes required")
    router = APIRouter(prefix=prefix, tags=["knowledge-video-candidate"])

    @router.post("/knowledge-videos", response_model=None)
    async def create(request: Request) -> Response:
        correlation = "corr_" + uuid4().hex
        try:
            identity = await run_in_threadpool(resolve_identity, request)
            if identity is None:
                return _error(correlation, 401, "UNAUTHENTICATED")
            key = request.headers.get("idempotency-key", "")
            if len(request.headers.getlist("idempotency-key")) != 1:
                return _error(correlation, 400, "VIDEO_INVALID_IDEMPOTENCY_KEY")
            try:
                require_id(key)
            except VideoError:
                return _error(correlation, 400, "VIDEO_INVALID_IDEMPOTENCY_KEY")
            if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() \
                    != "application/json":
                return _error(correlation, 415, "UNSUPPORTED_MEDIA_TYPE")
            body = bytearray()
            async for chunk in request.stream():
                if len(body) + len(chunk) > max_body_bytes:
                    return _error(correlation, 413, "VIDEO_BODY_TOO_LARGE")
                body.extend(chunk)
            try:
                raw = json.loads(body.decode("utf-8"), object_pairs_hook=_unique_object,
                                 parse_constant=_no_constant)
                command = CreateKnowledgeVideo.model_validate(raw)
            except (ValueError, UnicodeError, RecursionError, ValidationError):
                return _error(correlation, 422, "VIDEO_INVALID_COMMAND")
            context = VideoRequestContext(identity.principal_id, identity.organization_id,
                                          identity.session_id, key, correlation)
            result = await run_in_threadpool(service.create, context, command)
            if result.view is None:
                return _error(correlation, 503, "VIDEO_DEPENDENCY_UNAVAILABLE")
            return JSONResponse({"correlation_id": correlation,
                                 "data": result.view.model_dump(mode="json"),
                                 "meta": {"outcome": result.outcome}},
                                status_code=202, headers=_HEADERS)
        except VideoError as error:
            code = str(error)
            if code not in _STATUS:
                code = "VIDEO_DEPENDENCY_UNAVAILABLE"
            return _error(correlation, _STATUS[code], code)
        except Exception:
            return _error(correlation, 503, "VIDEO_DEPENDENCY_UNAVAILABLE")

    return router
