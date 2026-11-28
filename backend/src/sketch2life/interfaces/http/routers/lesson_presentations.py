"""Teacher presentation commands and reads for one lesson occurrence (T-SLD1)."""

# FastAPI dependency declarations intentionally use Depends in defaults.
# ruff: noqa: B008

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable
from typing import Annotated, Any, NoReturn

from fastapi import APIRouter, Depends, Header, HTTPException, Path, Request, Response, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.contracts.schemas.lesson_presentations import (
    CreatePresentationRequestV1,
    CreatePresentationRevisionRequestV1,
    CreatePresentationSvgDraftRequestV1,
    DecidePresentationSvgDraftRequestV1,
    LessonPresentationRevisionV1,
    LessonPresentationV1,
    PresentationSvgDraftV1,
)
from sketch2life.domain.lesson_occurrences.presentation import etag as presentation_etag
from sketch2life.infrastructure.lesson_occurrences.presentations import (
    LessonPresentationService,
    PresentationCommandResult,
)
from sketch2life.infrastructure.lesson_occurrences.scope import LessonOccurrenceError
from sketch2life.interfaces.http.api_conventions import parse_idempotency_key
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult

router = APIRouter(prefix="/v1/lesson-occurrences", tags=["Lesson Occurrences"])

OccurrenceId = Annotated[str, Path(min_length=1, max_length=256, pattern=r"^[^\x00]+$")]
RevisionNo = Annotated[int, Path(ge=1, le=1_000_000)]
DraftId = Annotated[str, Path(min_length=1, max_length=36, pattern=r"^[A-Za-z0-9-]+$")]
AssetRef = Annotated[str, Path(min_length=5, max_length=64, pattern=r"^upl_[A-Za-z0-9._:-]+$")]
IdempotencyKeyHeader = Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)]
_READ_HEADERS = {"Cache-Control": "private, no-cache", "Vary": "Authorization"}
_IMAGE_HEADERS = {"Cache-Control": "private, no-store", "Vary": "Authorization"}
_ETAG = re.compile(r'^"([1-9][0-9]{0,8})"$')


def get_presentation_service(
    request: Request,
    db: Session = Depends(get_db),
) -> LessonPresentationService:
    state = request.app.state
    return LessonPresentationService(
        db,
        storage=getattr(state, "lesson_library_storage", None),
        svg_drafter=getattr(state, "presentation_svg_drafter", None),
    )


def _raise(exc: LessonOccurrenceError) -> NoReturn:
    detail: dict[str, Any] = {"code": exc.code}
    if exc.field_errors:
        detail["field_errors"] = exc.field_errors
    headers = None
    retry_after = getattr(exc, "retry_after", None)
    if retry_after is not None:
        headers = {"Retry-After": str(retry_after)}
    if exc.code == "STALE_REVISION" and exc.current_version is not None:
        detail["current_version"] = exc.current_version
        headers = {**(headers or {}), "ETag": presentation_etag(exc.current_version)}
    raise HTTPException(status_code=exc.status_code, detail=detail, headers=headers) from None


def _call[Result](function: Callable[[], Result]) -> Result:
    try:
        return function()
    except LessonOccurrenceError as exc:
        _raise(exc)


def _parse_if_match(value: str | None) -> tuple[int, str]:
    if value is None:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_REQUEST",
                "field_errors": [{"field": "If-Match", "code": "REQUIRED"}],
            },
        )
    match = _ETAG.fullmatch(value.strip())
    if match is None:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_REQUEST",
                "field_errors": [{"field": "If-Match", "code": "INVALID_FORMAT"}],
            },
        )
    return int(match.group(1)), value.strip()


def _if_none_match(value: str | None, current: str) -> bool:
    if value is None:
        return False
    current_opaque = current.removeprefix("W/")
    return any(
        item.strip() == "*" or item.strip().removeprefix("W/") == current_opaque
        for item in value.split(",")
    )


def _presentation_body_etag(body: dict[str, Any]) -> str:
    """Validate the complete read representation, including derived freshness and media state."""
    encoded = json.dumps(
        jsonable_encoder(body), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()[:12]
    return f'W/"{digest}"'


def _set_command_headers(response: Response, result: PresentationCommandResult) -> None:
    response.headers.update(_READ_HEADERS)
    response.headers["ETag"] = result.etag


@router.post(
    "/{occurrence_id}/presentation",
    response_model=LessonPresentationV1,
    status_code=status.HTTP_201_CREATED,
    summary="Create a presentation pinned to the occurrence's approved plan",
)
def create_presentation(
    occurrence_id: OccurrenceId,
    payload: CreatePresentationRequestV1,
    request: Request,
    response: Response,
    idempotency_key: IdempotencyKeyHeader,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    service: LessonPresentationService = Depends(get_presentation_service),
) -> dict[str, Any]:
    key = parse_idempotency_key(request)
    result = _call(
        lambda: service.create(
            principal=principal, occurrence_id=occurrence_id, seed=payload.seed, idempotency_key=key
        )
    )
    _set_command_headers(response, result)
    response.headers["Location"] = f"/v1/lesson-occurrences/{occurrence_id}/presentation"
    return result.body


@router.get(
    "/{occurrence_id}/presentation",
    response_model=LessonPresentationV1,
    summary="Read a presentation after occurrence authorization",
    responses={304: {"description": "Not modified after authorization"}},
)
def get_presentation(
    occurrence_id: OccurrenceId,
    request: Request,
    response: Response,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    service: LessonPresentationService = Depends(get_presentation_service),
) -> Any:
    body = _call(lambda: service.get_presentation(principal=principal, occurrence_id=occurrence_id))
    response.headers.update(_READ_HEADERS)
    current_etag = _presentation_body_etag(body)
    response.headers["ETag"] = current_etag
    if _if_none_match(request.headers.get("If-None-Match"), current_etag):
        return Response(status_code=304, headers={**_READ_HEADERS, "ETag": current_etag})
    return body


@router.post(
    "/{occurrence_id}/presentation/revisions",
    response_model=LessonPresentationV1,
    status_code=status.HTTP_201_CREATED,
    summary="Create a draft presentation revision",
)
def create_presentation_revision(
    occurrence_id: OccurrenceId,
    payload: CreatePresentationRevisionRequestV1,
    request: Request,
    response: Response,
    idempotency_key: IdempotencyKeyHeader,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    service: LessonPresentationService = Depends(get_presentation_service),
) -> dict[str, Any]:
    expected, token = _parse_if_match(if_match)
    key = parse_idempotency_key(request)
    operations = [operation.model_dump(mode="json") for operation in payload.operations]
    result = _call(
        lambda: service.create_revision(
            principal=principal, occurrence_id=occurrence_id, expected_revision=expected,
            if_match=token, idempotency_key=key,
            repin_to_current_plan=payload.repin_to_current_plan, operations=operations,
        )
    )
    _set_command_headers(response, result)
    response.headers["Content-Location"] = (
        f"/v1/lesson-occurrences/{occurrence_id}/presentation/revisions/"
        f"{result.body['head_revision_no']}"
    )
    return result.body


@router.get(
    "/{occurrence_id}/presentation/revisions/{revision_no}",
    response_model=LessonPresentationRevisionV1,
    summary="Read one immutable presentation revision",
    responses={304: {"description": "Not modified after authorization"}},
)
def get_presentation_revision(
    occurrence_id: OccurrenceId,
    revision_no: RevisionNo,
    request: Request,
    response: Response,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    service: LessonPresentationService = Depends(get_presentation_service),
) -> Any:
    body = _call(
        lambda: service.get_revision(
            principal=principal, occurrence_id=occurrence_id, revision_no=revision_no
        )
    )
    current_etag = _presentation_body_etag(body)
    response.headers.update({**_READ_HEADERS, "ETag": current_etag})
    if _if_none_match(request.headers.get("If-None-Match"), current_etag):
        return Response(status_code=304, headers={**_READ_HEADERS, "ETag": current_etag})
    return body


@router.post(
    "/{occurrence_id}/presentation/revisions/{revision_no}/ready",
    response_model=LessonPresentationV1,
    summary="Mark the current draft revision ready after source checks",
)
def mark_presentation_revision_ready(
    occurrence_id: OccurrenceId,
    revision_no: RevisionNo,
    request: Request,
    response: Response,
    idempotency_key: IdempotencyKeyHeader,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    service: LessonPresentationService = Depends(get_presentation_service),
) -> dict[str, Any]:
    expected, token = _parse_if_match(if_match)
    key = parse_idempotency_key(request)
    result = _call(
        lambda: service.mark_ready(
            principal=principal, occurrence_id=occurrence_id, revision_no=revision_no,
            expected_revision=expected, if_match=token, idempotency_key=key,
        )
    )
    _set_command_headers(response, result)
    return result.body


@router.get(
    "/{occurrence_id}/presentation/images/{asset_ref}",
    summary="Serve an original image only when a presentation revision references its handle",
    responses={
        200: {
            "description": "Original image bytes with an SHA-256 ETag",
            "content": {"image/*": {"schema": {"type": "string", "format": "binary"}}},
        }
    },
)
def get_presentation_image(
    occurrence_id: OccurrenceId,
    asset_ref: AssetRef,
    response: Response,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    service: LessonPresentationService = Depends(get_presentation_service),
) -> Response:
    result = _call(
        lambda: service.get_image(
            principal=principal,
            occurrence_id=occurrence_id,
            asset_ref=asset_ref,
        )
    )
    headers = {
        **_IMAGE_HEADERS,
        "ETag": f'"{result.sha256}"',
        "X-Content-Type-Options": "nosniff",
        "Content-Disposition": "inline",
    }
    response.headers.update(headers)
    return Response(content=result.body, media_type=result.media_type, headers=headers)


@router.post(
    "/{occurrence_id}/presentation/svg-drafts",
    response_model=PresentationSvgDraftV1,
    status_code=status.HTTP_201_CREATED,
    summary="Create a private SVG draft from one approved plan activity",
)
def create_presentation_svg_draft(
    occurrence_id: OccurrenceId,
    payload: CreatePresentationSvgDraftRequestV1,
    request: Request,
    response: Response,
    idempotency_key: IdempotencyKeyHeader,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    service: LessonPresentationService = Depends(get_presentation_service),
) -> dict[str, Any]:
    key = parse_idempotency_key(request)
    result = _call(
        lambda: service.create_svg_draft(
            principal=principal, occurrence_id=occurrence_id,
            plan_activity_id=payload.plan_activity_id, subject_text=payload.subject_text,
            idempotency_key=key,
        )
    )
    _set_command_headers(response, result)
    response.headers["Location"] = (
        f"/v1/lesson-occurrences/{occurrence_id}/presentation/svg-drafts/"
        f"{result.body['svg_draft_id']}"
    )
    return result.body


@router.get(
    "/{occurrence_id}/presentation/svg-drafts/{svg_draft_id}",
    response_model=PresentationSvgDraftV1,
    summary="Read one private presentation SVG draft",
)
def get_presentation_svg_draft(
    occurrence_id: OccurrenceId,
    svg_draft_id: DraftId,
    response: Response,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    service: LessonPresentationService = Depends(get_presentation_service),
) -> dict[str, Any]:
    body = _call(
        lambda: service.get_svg_draft(
            principal=principal, occurrence_id=occurrence_id, svg_draft_id=svg_draft_id
        )
    )
    response.headers.update({**_READ_HEADERS, "ETag": presentation_etag(int(body["revision"]))})
    return body


@router.post(
    "/{occurrence_id}/presentation/svg-drafts/{svg_draft_id}/decision",
    response_model=PresentationSvgDraftV1,
    summary="Accept or discard a pending SVG draft",
)
def decide_presentation_svg_draft(
    occurrence_id: OccurrenceId,
    svg_draft_id: DraftId,
    payload: DecidePresentationSvgDraftRequestV1,
    request: Request,
    response: Response,
    idempotency_key: IdempotencyKeyHeader,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    service: LessonPresentationService = Depends(get_presentation_service),
) -> dict[str, Any]:
    expected, token = _parse_if_match(if_match)
    key = parse_idempotency_key(request)
    result = _call(
        lambda: service.decide_svg_draft(
            principal=principal, occurrence_id=occurrence_id, svg_draft_id=svg_draft_id,
            expected_revision=expected, if_match=token, decision=payload.decision,
            idempotency_key=key,
        )
    )
    _set_command_headers(response, result)
    return result.body


__all__ = ["get_presentation_service", "router"]
