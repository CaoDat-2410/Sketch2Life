"""The Parent video routes: ``video-generations`` (FEAT-066 T-1a; SRS l.395, l.1670) and the two
decisions on a ready video, ``video-unsuitable`` and ``complete`` (T-1b; SRS l.1671-1672).

The Parent owner asks for a video of the confirmed script. The response is 202: the saga stores an
intent first, then asks the compute reservation and the quota admission (both behind ports, never
inside a transaction) and answers ``ADMISSION_PENDING`` until both are clear, ``ACCEPTED`` with a
``job_id`` once they are. A refused request is a stable error (409 ``VIDEO_QUOTA_EXCEEDED`` or
``SUBSCRIPTION_RESTRICTED``, 503 ``AI_COST_LIMIT_REACHED``) and makes no usage, job or cap.

Check order: role, key syntax (400), owner-scoped locked lookup (404), replay, purge states, run
state, revision and hash (409), cap (409), then adapter availability (503 ``PROVIDER_UNAVAILABLE``):
a foreign actor never sees 503 first. Same literal prefix as ``parent_story_runs``; mounted and
unmounted together with it while the StoryRun-lite demo is on or off
(``story_demo_replaced_routers``).

T-1b: ``video-unsuitable`` and ``complete`` answer 200 with the run envelope (the lifecycle
envelope for a replay on a run already being deleted). Check order, in one locked transaction:
role, key syntax (400), owner-scoped lookup (404), replay, run state (409
``INVALID_STATE_TRANSITION``), run revision (409 ``STALE_REVISION`` with ``current_version``), then
for ``video-unsuitable`` the current generation (409 ``STALE_REVISION``) and the regeneration cap
(409 ``VIDEO_REGENERATION_LIMIT_REACHED``). No port is called and no storage reference is shown.

T-1c: ``playback-token`` (a grant, no database write: 404 for a foreign or deleted run, 409 when
the run is not at ``VIDEO_READY`` with a ``READY`` generation, 503 with no signing secret) and the
stream route ``playback`` (the bearer is required AND the ``X-Playback-Token`` header must name the
same actor; every request rechecks owner, run state and generation; the database session is
released before the first byte). Neither route shows a bucket, key or URL (SRS l.1692).
"""

# FastAPI dependency declarations intentionally use Depends in defaults.
# ruff: noqa: B008

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.background import BackgroundTask

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.object_storage import (
    ObjectStorageFailure,
    ObjectStoragePort,
    ReadableObjectBody,
)
from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
from sketch2life.application.ports.story_video import PLAYBACK_MEDIA_TYPE, RunCommandResult
from sketch2life.application.services.story_run_detail import video_asset_handle
from sketch2life.application.services.story_run_playback import (
    RangeNotSatisfiable,
    StoryPlaybackService,
    check_playback_token,
    parse_byte_range,
)
from sketch2life.application.services.story_run_video import (
    DEFAULT_PORT_TIMEOUT_SECONDS,
    StoryVideoAdmissionService,
    StoryVideoCommandService,
)
from sketch2life.contracts.schemas.parent_story_runs import (
    ParentStoryCancelErrorEnvelopeV1,
    ParentStoryRunLifecycleEnvelopeV1,
)
from sketch2life.contracts.schemas.story_run_video import (
    ParentPlaybackGrantV1,
    ParentPlaybackTokenResponseV1,
    ParentStoryRunCompleteRequestV1,
    ParentVideoGenerationAcceptedV1,
    ParentVideoGenerationRequestV1,
    ParentVideoGenerationV1,
    ParentVideoUnsuitableRequestV1,
)
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
)
from sketch2life.infrastructure.story_video.repository import SqlStoryVideoRepository
from sketch2life.interfaces.http.api_conventions import parse_idempotency_key
from sketch2life.interfaces.http.be1_runtime import (
    Be1Runtime,
    get_db,
    get_runtime,
    get_verified_adult,
)
from sketch2life.interfaces.http.routers.parent_story_inputs import _http_error
from sketch2life.interfaces.http.routers.parent_story_runs import (
    ParentStoryRunResult,
    _envelope,
    _lifecycle_envelope,
    _require_parent,
)

router = APIRouter(prefix="/v1/story-runs", tags=["Parent StoryRuns"])

_VIDEO_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {
        "model": ParentStoryCancelErrorEnvelopeV1,
        "description": "The request or the idempotency key is invalid.",
    },
    401: {
        "model": ParentStoryCancelErrorEnvelopeV1,
        "description": "Authentication is required.",
    },
    404: {
        "model": ParentStoryCancelErrorEnvelopeV1,
        "description": "The run was not found, or the caller is not the active Parent owner.",
    },
    409: {
        "model": ParentStoryCancelErrorEnvelopeV1,
        "description": (
            "The run state, the revision or the script does not allow a video request, the "
            "regeneration limit was reached, or the quota or the subscription refused it."
        ),
    },
    422: {
        "model": ParentStoryCancelErrorEnvelopeV1,
        "description": "The subject or the context of the run was not confirmed.",
    },
    503: {
        "model": ParentStoryCancelErrorEnvelopeV1,
        "description": (
            "The compute budget refused the request or a required service is unavailable."
        ),
    },
    500: {
        "model": ParentStoryCancelErrorEnvelopeV1,
        "description": "An unexpected error occurred.",
    },
}


@router.post(
    "/{run_id}/video-generations",
    response_model=ParentVideoGenerationAcceptedV1 | ParentStoryRunLifecycleEnvelopeV1,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ask for a video of the confirmed script of a Parent StoryRun",
    responses=_VIDEO_ERROR_RESPONSES,
)
def create_parent_video_generation(
    run_id: UUID,
    payload: ParentVideoGenerationRequestV1,
    request: Request,
    response: Response,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)],
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentVideoGenerationAcceptedV1 | ParentStoryRunLifecycleEnvelopeV1:
    # The declaration above publishes the header as required; parse_idempotency_key (1-128 visible
    # ASCII) is the authority and runs after the role check, before the run lookup.
    del idempotency_key
    _require_parent(db, principal)
    key = parse_idempotency_key(request)
    state = request.app.state
    service = StoryVideoAdmissionService(
        SqlStoryVideoRepository(db),
        getattr(state, "story_video_ports", None),
        call_timeout_seconds=getattr(
            state, "story_video_port_timeout_seconds", DEFAULT_PORT_TIMEOUT_SECONDS
        ),
    )
    try:
        outcome = service.request(
            principal=principal,
            run_id=str(run_id),
            expected_revision=payload.expected_revision,
            story_sha256=payload.story_sha256,
            quality_reason_code=payload.quality_reason_code,
            idempotency_key=key,
        )
    except ParentStoryRunError as exc:
        raise _http_error(exc) from None
    response.headers["Content-Location"] = f"/v1/story-runs/{run_id}"
    if outcome.projection is not None or outcome.record is None:
        assert outcome.projection is not None
        return ParentStoryRunLifecycleEnvelopeV1.model_validate(
            {"request_id": uuid4(), "lifecycle": outcome.projection.as_body()}
        )
    record = outcome.record
    return ParentVideoGenerationAcceptedV1(
        request_id=uuid4(),
        video_generation=ParentVideoGenerationV1.model_validate(
            {
                "generation_id": record.generation_id,
                "state": record.state,
                "generation_no": record.generation_no,
                "kind": record.kind,
                "job_id": record.job_ref,
                "run_state": record.run_state,
                "run_revision": record.run_revision,
            }
        ),
    )


_RUN_COMMAND_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: _VIDEO_ERROR_RESPONSES[400],
    401: _VIDEO_ERROR_RESPONSES[401],
    404: _VIDEO_ERROR_RESPONSES[404],
    409: {
        "model": ParentStoryCancelErrorEnvelopeV1,
        "description": (
            "The run is not at VIDEO_READY, the revision or the generation is stale, or the "
            "regeneration limit was reached."
        ),
    },
    422: {
        "model": ParentStoryCancelErrorEnvelopeV1,
        "description": "Validation uses the standard error envelope.",
    },
    503: {
        "model": ParentStoryCancelErrorEnvelopeV1,
        "description": "A required service is unavailable.",
    },
    500: _VIDEO_ERROR_RESPONSES[500],
}


def _run_command_response(
    response: Response,
    db: Session,
    principal: VerifiedPrincipal,
    run_id: UUID,
    result: RunCommandResult,
) -> ParentStoryRunResult:
    """200 with the run read after the commit, or the content-free projection of a purged replay."""

    response.headers["Content-Location"] = f"/v1/story-runs/{run_id}"
    if result.projection is not None:
        return _lifecycle_envelope(result.projection)
    try:
        view = SqlParentStoryRunRepository(db).get_run(principal=principal, run_id=str(run_id))
    except ParentStoryRunError as exc:
        raise _http_error(exc) from None
    return _envelope(view)


@router.post(
    "/{run_id}/video-unsuitable",
    response_model=ParentStoryRunResult,
    status_code=status.HTTP_200_OK,
    summary="Mark the current ready video unsuitable and return the run to the script review",
    responses=_RUN_COMMAND_ERROR_RESPONSES,
)
def mark_parent_video_unsuitable(
    run_id: UUID,
    payload: ParentVideoUnsuitableRequestV1,
    request: Request,
    response: Response,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)],
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentStoryRunResult:
    del idempotency_key  # parse_idempotency_key is the authority (see the video-generations route)
    _require_parent(db, principal)
    key = parse_idempotency_key(request)
    try:
        result = StoryVideoCommandService(SqlStoryVideoRepository(db)).mark_unsuitable(
            principal=principal,
            run_id=str(run_id),
            expected_revision=payload.expected_revision,
            generation_id=str(payload.generation_id),
            reason_code=payload.reason_code,
            idempotency_key=key,
        )
    except ParentStoryRunError as exc:
        raise _http_error(exc) from None
    return _run_command_response(response, db, principal, run_id, result)


@router.post(
    "/{run_id}/complete",
    response_model=ParentStoryRunResult,
    status_code=status.HTTP_200_OK,
    summary="Complete the Parent StoryRun at VIDEO_READY and release the active lock",
    responses=_RUN_COMMAND_ERROR_RESPONSES,
)
def complete_parent_story_run(
    run_id: UUID,
    payload: ParentStoryRunCompleteRequestV1,
    request: Request,
    response: Response,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)],
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentStoryRunResult:
    del idempotency_key  # parse_idempotency_key is the authority (see the video-generations route)
    _require_parent(db, principal)
    key = parse_idempotency_key(request)
    try:
        result = StoryVideoCommandService(SqlStoryVideoRepository(db)).complete(
            principal=principal,
            run_id=str(run_id),
            expected_revision=payload.expected_revision,
            idempotency_key=key,
        )
    except ParentStoryRunError as exc:
        raise _http_error(exc) from None
    return _run_command_response(response, db, principal, run_id, result)


# ---------------------------------------------------------------------------- playback (T-1c)
_PLAYBACK_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    401: {
        "model": ParentStoryCancelErrorEnvelopeV1,
        "description": "Authentication is required, or the playback token is invalid or expired.",
    },
    404: _VIDEO_ERROR_RESPONSES[404],
    422: {
        "model": ParentStoryCancelErrorEnvelopeV1,
        "description": "Validation uses the standard error envelope.",
    },
    503: {
        "model": ParentStoryCancelErrorEnvelopeV1,
        "description": "Playback or the object store is unavailable.",
    },
    500: _VIDEO_ERROR_RESPONSES[500],
}
_STREAM_CHUNK_BYTES = 64 * 1024
DEFAULT_MAX_STREAM_BYTES = 100 * 1024 * 1024
_BINARY_VIDEO: dict[str, Any] = {
    PLAYBACK_MEDIA_TYPE: {"schema": {"type": "string", "format": "binary"}}
}


@router.post(
    "/{run_id}/playback-token",
    response_model=ParentPlaybackTokenResponseV1,
    status_code=status.HTTP_200_OK,
    summary="Issue a short-lived playback grant for the ready video of the Parent StoryRun",
    responses={
        **_PLAYBACK_ERROR_RESPONSES,
        401: _VIDEO_ERROR_RESPONSES[401],
        409: {
            "model": ParentStoryCancelErrorEnvelopeV1,
            "description": "The run has no video that can be played now.",
        },
    },
)
def issue_parent_playback_token(
    run_id: UUID,
    request: Request,
    response: Response,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentPlaybackTokenResponseV1:
    """SRS l.1676: no body and no idempotency key (a grant, not a state change; no database
    write). Ownership and the video state are read now; the stream rechecks them on every use."""

    _require_parent(db, principal)
    service = StoryPlaybackService(
        SqlStoryVideoRepository(db), getattr(request.app.state, "story_playback_tokens", None)
    )
    try:
        issued = service.issue(principal=principal, run_id=str(run_id))
    except ParentStoryRunError as exc:
        raise _http_error(exc) from None
    response.headers["Cache-Control"] = "no-store"
    return ParentPlaybackTokenResponseV1(
        request_id=uuid4(),
        playback=ParentPlaybackGrantV1(
            token=issued.token,
            expires_at=datetime.fromtimestamp(issued.expires_at, UTC),
            stream_path=f"/v1/story-runs/{run_id}/playback",
            media_type=PLAYBACK_MEDIA_TYPE,
            asset_ref=video_asset_handle(issued.generation_id),
        ),
    )


async def _stream_chunks(body: ReadableObjectBody, first: int, last: int) -> AsyncIterator[bytes]:
    """Bytes ``first..last`` of the object in 64 KiB chunks; the body is always closed, also when
    the client leaves (the generator is closed) and when the object ends early."""

    try:
        skipped = 0
        while skipped < first:
            chunk = await run_in_threadpool(body.read, min(_STREAM_CHUNK_BYTES, first - skipped))
            if not chunk:
                return
            skipped += len(chunk)
        remaining = last - first + 1
        while remaining > 0:
            chunk = await run_in_threadpool(body.read, min(_STREAM_CHUNK_BYTES, remaining))
            if not chunk:
                return
            remaining -= len(chunk)
            yield chunk
    finally:
        body.close()


def _unavailable(code: str) -> HTTPException:
    return HTTPException(status_code=503, detail={"code": code})


@router.get(
    "/{run_id}/playback",
    response_model=None,
    response_class=Response,
    status_code=status.HTTP_200_OK,
    summary="Stream the ready video of the Parent StoryRun to the playback token holder",
    responses={
        200: {"description": "The whole video, streamed.", "content": _BINARY_VIDEO},
        206: {"description": "One byte range of the video.", "content": _BINARY_VIDEO},
        416: {
            "model": ParentStoryCancelErrorEnvelopeV1,
            "description": "The requested range cannot be served.",
        },
        **_PLAYBACK_ERROR_RESPONSES,
    },
)
def stream_parent_playback(
    run_id: UUID,
    request: Request,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    runtime: Be1Runtime = Depends(get_runtime),
    playback_token: Annotated[str | None, Header(alias="X-Playback-Token")] = None,
    byte_range: Annotated[str | None, Header(alias="Range")] = None,
) -> Response:
    """SRS l.1691-1693: the bearer is required and must be the token's actor; the token is read from
    a header only. Order: token shape, signature and expiry (401), then in one short database
    scope the parent role, the run, the current generation and the owner binding (uniform 404),
    then the object (404 when absent, 503 when the store fails). The session is closed before
    the first byte, so a slow download holds no database connection."""

    state = request.app.state
    tokens = getattr(state, "story_playback_tokens", None)
    try:
        grant = check_playback_token(tokens, playback_token)
    except ParentStoryRunError as exc:
        raise _http_error(exc) from None
    assert runtime.session_factory is not None
    try:
        with runtime.session_factory() as db:
            _require_parent(db, principal)
            target = StoryPlaybackService(SqlStoryVideoRepository(db), tokens).authorize(
                principal=principal, run_id=str(run_id), grant=grant
            )
    except ParentStoryRunError as exc:
        raise _http_error(exc) from None
    except SQLAlchemyError:
        raise _unavailable("DATABASE_UNAVAILABLE") from None
    # The database scope is closed here; nothing below holds a connection.
    storage: ObjectStoragePort | None = getattr(state, "lesson_library_storage", None)
    if storage is None:
        raise _unavailable("STORAGE_UNAVAILABLE")
    try:
        stored = storage.get_object(target.storage_key)
    except ObjectStorageFailure:
        raise _unavailable("STORAGE_UNAVAILABLE") from None
    if stored is None:
        raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND"})
    size = int(stored.content_length)
    ceiling = int(getattr(state, "story_playback_max_object_bytes", DEFAULT_MAX_STREAM_BYTES))
    try:
        if size > ceiling:
            raise _unavailable("STORAGE_UNAVAILABLE")
        try:
            selected = parse_byte_range(byte_range, size)
        except RangeNotSatisfiable:
            raise HTTPException(
                status_code=416,
                detail={"code": "RANGE_NOT_SATISFIABLE"},
                headers={"Content-Range": f"bytes */{size}"},
            ) from None
    except HTTPException:
        stored.body.close()
        raise
    first, last = (0, size - 1) if selected is None else selected
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(last - first + 1),
        "Content-Disposition": "inline",
        "Cache-Control": "private, no-store",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
    }
    if selected is not None:
        headers["Content-Range"] = f"bytes {first}-{last}/{size}"
    return StreamingResponse(
        _stream_chunks(stored.body, first, last),
        status_code=200 if selected is None else 206,
        media_type=PLAYBACK_MEDIA_TYPE,
        headers=headers,
        # A generator that was never started never runs its ``finally``; closing again is harmless.
        background=BackgroundTask(stored.body.close),
    )


__all__ = ["router"]
