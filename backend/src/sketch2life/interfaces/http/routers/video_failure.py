"""Injected CMD-43 candidate only; no production mounting/default authority."""

from collections.abc import Callable
from dataclasses import replace
from uuid import uuid4

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from sketch2life.application.video_failure import VideoFailureService
from sketch2life.contracts.schemas.knowledge_video import VideoExactRef
from sketch2life.contracts.schemas.video_failure import (
    ConfirmedDisposition,
    FailureDispositionCommand,
    PendingDisposition,
)
from sketch2life.domain.knowledge_video.model import VideoError, require_id
from sketch2life.domain.video_failure.model import Action, Choice, Context, Intent
from sketch2life.interfaces.http.routers.knowledge_video import VideoIdentity
from sketch2life.interfaces.http.routers.video_review import (
    _body,
    _error,
    _InputError,
    _key,
    _revision,
)

# Same strict transport primitives as09; translate its internal transport codes to
# CMD-43 names. No authority/service dependencies on09, no copied permissive binder.
_CODES = {
    "VIDEO_NOT_EXHAUSTED": 409,
    "VIDEO_DISPOSITION_FORBIDDEN": 403,
    "VIDEO_DISPOSITION_SCOPE_MISMATCH": 403,
    "VIDEO_DISPOSITION_STALE_TARGET": 409,
    "VIDEO_DISPOSITION_STALE_SESSION": 409,
    "VIDEO_DISPOSITION_IDEMPOTENCY_CONFLICT": 409,
    "VIDEO_DISPOSITION_CONFLICT": 409,
    "VIDEO_RETRY_NOT_AUTHORIZED": 409,
    "VIDEO_DISPOSITION_DEPENDENCY_UNAVAILABLE": 503,
}
_HEADERS = {"Cache-Control": "no-store", "Vary": "Authorization"}


def build_video_failure_router(
    service: VideoFailureService | None,
    resolve_identity: Callable[[Request], VideoIdentity | None],
    *,
    max_body_bytes: int,
    prefix: str = "/api/collaboration/v1",
) -> APIRouter:
    if type(max_body_bytes) is not int or max_body_bytes < 1:
        raise ValueError("explicit positive max_body_bytes required")
    router = APIRouter(prefix=prefix, tags=["video-failure-candidate"])

    @router.post("/knowledge-videos/{video_id}/failure-dispositions", response_model=None)
    async def disposition(video_id: str, request: Request) -> Response:
        correlation = "corr_" + uuid4().hex
        try:
            if len(request.headers.getlist("authorization")) > 1:
                raise _InputError(401, "UNAUTHENTICATED")
            actor = await run_in_threadpool(resolve_identity, request)
            if actor is None:
                raise _InputError(401, "UNAUTHENTICATED")
            if type(actor) is not VideoIdentity:
                raise RuntimeError("invalid identity adapter")
            actor = replace(actor)
            try:
                require_id(video_id)
            except VideoError:
                raise _InputError(400, "VIDEO_DISPOSITION_INVALID_TARGET") from None
            key, revision = _key(request), _revision(request)
            raw = await _body(request, max_body_bytes)
            try:
                cmd = FailureDispositionCommand.model_validate_json(raw, strict=True)
            except ValueError:
                raise _InputError(422, "VIDEO_DISPOSITION_INVALID_COMMAND") from None
            c = Context(actor.principal_id, actor.organization_id, actor.session_id, video_id, key)
            choice = Choice(
                Action(cmd.action),
                cmd.reason,
                cmd.expected_video_version,
                revision,
                cmd.expected_job_revision,
                cmd.expected_session_revision,
                cmd.retry_authorization_note,
            )
            if service is None:
                raise RuntimeError("unconfigured owner adoption")
            result = await run_in_threadpool(service.decide, c, choice)
            if type(result) is not Intent:
                raise RuntimeError("invalid projection")
            try:
                result = replace(result)
            except ValueError:
                raise RuntimeError("invalid service projection") from None
            if result.context != c or result.choice != choice:
                raise RuntimeError("foreign projection")
            if result.receipt is None:
                view: PendingDisposition | ConfirmedDisposition = PendingDisposition(
                    disposition_id=result.disposition_id, operation_key=c.operation_key()
                )
                status = 202
            else:
                r = result.receipt
                outcome = {
                    Action.RETRY: "retry_pending",
                    Action.SKIP: "skipped_by_teacher",
                    Action.END: "session_ended_early",
                }[choice.action]
                view = ConfirmedDisposition.model_validate(
                    {
                        "disposition_id": result.disposition_id,
                        "recorded_by": c.principal_id,
                        "recorded_at": r.recorded_at,
                        "action": choice.action.value,
                        "reason": choice.reason,
                        "prior_failure_ref": VideoExactRef(
                            ref=result.target.failure_ref.ref,
                            version=result.target.failure_ref.version,
                            hash=result.target.failure_ref.hash,
                        ),
                        "session_revision": r.session_revision_after,
                        "video_run_revision": r.video_run_revision,
                        "outcome": outcome,
                        "new_job_id": None if r.new_lifecycle is None else r.new_lifecycle.job_id,
                    },
                    strict=True,
                )
                status = 200
            return JSONResponse(
                {"correlation_id": correlation, "data": view.model_dump(mode="json")},
                status_code=status,
                headers=_HEADERS,
            )
        except _InputError as exc:
            return _error(
                correlation, exc.status, exc.code.replace("VIDEO_REVIEW_", "VIDEO_DISPOSITION_")
            )
        except VideoError as exc:
            code = str(exc) if str(exc) in _CODES else "VIDEO_DISPOSITION_DEPENDENCY_UNAVAILABLE"
            return _error(correlation, _CODES[code], code)
        except Exception:
            return _error(correlation, 503, "VIDEO_DISPOSITION_DEPENDENCY_UNAVAILABLE")

    return router
