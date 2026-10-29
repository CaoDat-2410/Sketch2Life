"""Injected CMD-41/42 candidate. Not mounted by production; no default authority.

Resolver must authenticate original-scope historical subjects on recovery,
not replace them with today's version. Current gates are held/rechecked by the
application boundary. Nothing here serves media or authorizes fetch/range/resume.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import replace
from uuid import uuid4

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from sketch2life.application.ports.video_review_write import ReviewWriteContext
from sketch2life.application.video_playback import PlaybackOutcome, VideoPlaybackService
from sketch2life.application.video_review_write import ReviewWriteOutcome, VideoReviewWriteService
from sketch2life.contracts.schemas.ai_contract_candidates import (
    ExactContentReviewCommandV1,
    ExactContentReviewRecordV1,
)
from sketch2life.contracts.schemas.video_review import (
    StartVideoPlayback,
    VideoPlaybackResult,
    VideoReviewRecorded,
)
from sketch2life.domain.knowledge_video.model import VideoError, require_id
from sketch2life.domain.video_review.model import ReviewSubject
from sketch2life.domain.video_review.playback import PlaybackRequest, playback_operation_key
from sketch2life.interfaces.http.routers.knowledge_video import VideoIdentity

_HEADERS = {"Cache-Control": "no-store", "Vary": "Authorization"}
_ETAG = re.compile(r'"([1-9][0-9]{0,18})"\Z')
_STATUS = {
    "VIDEO_REVIEW_FORBIDDEN": 403,
    "VIDEO_PLAYBACK_FORBIDDEN": 403,
    "VIDEO_REVIEW_SCOPE_MISMATCH": 403,
    "VIDEO_REVIEW_STALE_REVISION": 409,
    "VIDEO_REVIEW_HEAD_NOT_CURRENT": 409,
    "VIDEO_REVIEW_TARGET_NOT_CURRENT": 409,
    "VIDEO_REVIEW_TARGET_MISMATCH": 409,
    "VIDEO_REVIEW_IDEMPOTENCY_CONFLICT": 409,
    "VIDEO_REVIEW_WRITE_CONFLICT": 409,
    "VIDEO_PLAYBACK_IDEMPOTENCY_CONFLICT": 409,
    "VIDEO_PLAYBACK_REVIEW_NOT_EFFECTIVE": 409,
    "VIDEO_PLAYBACK_STALE_SESSION": 409,
    "VIDEO_REVIEW_INVALID_CONTEXT": 422,
    "VIDEO_REVIEW_REASON_REQUIRED": 422,
    "VIDEO_REVIEW_INVALID_COMMAND": 422,
    "VIDEO_REVIEW_DEPENDENCY_UNAVAILABLE": 503,
    "VIDEO_PLAYBACK_DEPENDENCY_UNAVAILABLE": 503,
}


class _InputError(Exception):
    def __init__(self, status: int, code: str) -> None:
        self.status, self.code = status, code


def _error(correlation: str, status: int, code: str) -> JSONResponse:
    return JSONResponse(
        {
            "correlation_id": correlation,
            "error": {
                "code": code,
                "message": "Request could not be completed.",
                "retryable": status == 503,
            },
        },
        status_code=status,
        headers=_HEADERS,
    )


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _constant(value: str) -> object:
    raise ValueError("nonfinite JSON")


async def _body(request: Request, limit: int) -> bytes:
    if (
        len(request.headers.getlist("content-type")) != 1
        or (
            request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
            != "application/json"
        )
        or request.headers.getlist("content-encoding")
    ):
        raise _InputError(415, "UNSUPPORTED_MEDIA_TYPE")
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > limit:
            raise _InputError(413, "VIDEO_REVIEW_BODY_TOO_LARGE")
        body.extend(chunk)
    try:
        # Parse once to reject duplicate keys/nonfinite tokens, then validate JSON
        # (not Python) so strict shared tuple fields accept genuine JSON arrays.
        raw = bytes(body)
        parsed = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_unique, parse_constant=_constant
        )
        if type(parsed) is not dict:
            raise ValueError("JSON object required")
        return raw
    except (ValueError, UnicodeError, RecursionError):
        raise _InputError(422, "VIDEO_REVIEW_INVALID_COMMAND") from None


def _key(request: Request) -> str:
    values = request.headers.getlist("idempotency-key")
    try:
        if len(values) != 1:
            raise ValueError("one key")
        require_id(values[0])
        return values[0]
    except ValueError:
        raise _InputError(400, "VIDEO_REVIEW_INVALID_IDEMPOTENCY_KEY") from None


def _revision(request: Request) -> int:
    values = request.headers.getlist("if-match")
    if not values:
        raise _InputError(428, "VIDEO_REVIEW_PRECONDITION_REQUIRED")
    matched = _ETAG.fullmatch(values[0]) if len(values) == 1 else None
    if matched is None or int(matched[1]) > 2**63 - 1:
        raise _InputError(400, "VIDEO_REVIEW_INVALID_PRECONDITION")
    return int(matched[1])


def build_video_review_router(
    review_service: VideoReviewWriteService | None,
    playback_service: VideoPlaybackService | None,
    resolve_identity: Callable[[Request], VideoIdentity | None],
    resolve_playback_subject: Callable[[VideoIdentity, str, StartVideoPlayback], ReviewSubject]
    | None,
    *,
    max_body_bytes: int,
    prefix: str = "/api/collaboration/v1",
) -> APIRouter:
    if type(max_body_bytes) is not int or max_body_bytes < 1:
        raise ValueError("explicit positive max_body_bytes required")
    router = APIRouter(prefix=prefix, tags=["video-review-playback-candidate"])

    async def identity(request: Request, video_id: str) -> VideoIdentity:
        if len(request.headers.getlist("authorization")) > 1:
            raise _InputError(401, "UNAUTHENTICATED")
        verified = await run_in_threadpool(resolve_identity, request)
        if verified is None:
            raise _InputError(401, "UNAUTHENTICATED")
        if type(verified) is not VideoIdentity:
            raise RuntimeError("invalid identity adapter")
        verified = replace(verified)
        try:
            require_id(video_id)
        except VideoError:
            raise _InputError(400, "VIDEO_REVIEW_INVALID_TARGET") from None
        return verified

    @router.post("/knowledge-videos/{video_id}/reviews", response_model=None)
    async def review(video_id: str, request: Request) -> Response:
        correlation = "corr_" + uuid4().hex
        try:
            actor = await identity(request, video_id)
            key, revision = _key(request), _revision(request)
            raw = await _body(request, max_body_bytes)
            try:
                command = ExactContentReviewCommandV1.model_validate_json(raw, strict=True)
            except ValueError:
                raise _InputError(422, "VIDEO_REVIEW_INVALID_COMMAND") from None
            if command.target_id != video_id:
                raise _InputError(409, "VIDEO_REVIEW_TARGET_MISMATCH")
            if review_service is None:
                raise RuntimeError("unconfigured service")
            context = ReviewWriteContext(
                actor.principal_id, actor.organization_id, actor.session_id, video_id, key, revision
            )
            result = await run_in_threadpool(review_service.record, context, command)
            if type(result) is not ReviewWriteOutcome:
                raise RuntimeError("invalid result")
            record = ExactContentReviewRecordV1.model_validate(
                result.record.model_dump(mode="python"), strict=True
            )
            if record.reviewer_principal_id != actor.principal_id or (
                record.review_revision != revision + 1
            ):
                raise RuntimeError("mismatched review receipt")
            view = VideoReviewRecorded(
                video_id=video_id,
                target_version=command.target_version,
                target_hash=command.target_hash,
                record=record,
                current_review_revision=result.current_review_revision,
                replayed=result.replayed,
            )
            return JSONResponse(
                {"correlation_id": correlation, "data": view.model_dump(mode="json")},
                status_code=200,
                headers=_HEADERS,
            )
        except _InputError as exc:
            return _error(correlation, exc.status, exc.code)
        except VideoError as exc:
            code = str(exc) if str(exc) in _STATUS else "VIDEO_REVIEW_DEPENDENCY_UNAVAILABLE"
            return _error(correlation, _STATUS[code], code)
        except Exception:
            return _error(correlation, 503, "VIDEO_REVIEW_DEPENDENCY_UNAVAILABLE")

    @router.post("/knowledge-videos/{video_id}/playback", response_model=None)
    async def playback(video_id: str, request: Request) -> Response:
        correlation = "corr_" + uuid4().hex
        try:
            actor = await identity(request, video_id)
            key = _key(request)
            # Do not silently interpret a review/run/job ETag as a session CAS.
            if request.headers.getlist("if-match"):
                raise _InputError(400, "VIDEO_PLAYBACK_UNSUPPORTED_PRECONDITION")
            raw = await _body(request, max_body_bytes)
            try:
                command = StartVideoPlayback.model_validate_json(raw, strict=True)
            except ValueError:
                raise _InputError(422, "VIDEO_REVIEW_INVALID_COMMAND") from None
            if playback_service is None or resolve_playback_subject is None:
                raise RuntimeError("unconfigured adoption")
            subject = await run_in_threadpool(resolve_playback_subject, actor, video_id, command)
            if type(subject) is not ReviewSubject:
                raise RuntimeError("invalid subject adapter")
            subject = replace(subject)
            if (subject.organization_id, subject.audience.session_id, subject.video_id) != (
                actor.organization_id,
                actor.session_id,
                video_id,
            ):
                raise VideoError("VIDEO_REVIEW_SCOPE_MISMATCH")
            if (subject.video_version, subject.artifact.hash, subject.digest()) != (
                command.target_version,
                command.target_hash,
                command.subject_digest,
            ):
                raise VideoError("VIDEO_REVIEW_TARGET_MISMATCH")
            resolved = PlaybackRequest(
                subject,
                command.review_id,
                command.review_revision,
                command.expected_session_revision,
            )
            result = await run_in_threadpool(
                playback_service.start, actor.principal_id, key, resolved
            )
            if type(
                result
            ) is not PlaybackOutcome or result.operation_key != playback_operation_key(
                actor.principal_id, key, subject
            ):
                raise RuntimeError("invalid playback result")
            view = VideoPlaybackResult(
                status=result.status,
                operation_key=result.operation_key,
                reason_code=result.reason_code,
                receipt_id=result.receipt_id,
            )
            return JSONResponse(
                {"correlation_id": correlation, "data": view.model_dump(mode="json")},
                status_code=202 if view.status == "pending" else 200,
                headers=_HEADERS,
            )
        except _InputError as exc:
            return _error(correlation, exc.status, exc.code)
        except VideoError as exc:
            code = str(exc) if str(exc) in _STATUS else "VIDEO_PLAYBACK_DEPENDENCY_UNAVAILABLE"
            return _error(correlation, _STATUS[code], code)
        except Exception:
            return _error(correlation, 503, "VIDEO_PLAYBACK_DEPENDENCY_UNAVAILABLE")

    return router
