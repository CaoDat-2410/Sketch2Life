"""Parent-local synthetic LTX candidate endpoints; never product video admission."""

# ruff: noqa: B008

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.object_storage import StoredObject
from sketch2life.application.ports.parent_video_candidates import ParentVideoCandidateError
from sketch2life.application.services.parent_video_candidate_service import (
    ParentVideoCandidateService,
)
from sketch2life.contracts.schemas.parent_video_candidates import (
    ParentCurrentVideoCandidateEnvelopeV1,
    ParentVideoCandidateEnvelopeV1,
    ParentVideoCandidateMetadataV1,
    ParentVideoCandidateRequestV1,
    ParentVideoCandidateV1,
)
from sketch2life.infrastructure.ai.modal_silent_story_video import ModalSilentStoryVideoWorker
from sketch2life.infrastructure.persistence.parent_story_profile_lookup import (
    SqlParentStoryProfileLookup,
)
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
)
from sketch2life.infrastructure.persistence.parent_video_candidate_repository import (
    SqlParentVideoCandidateRepository,
)
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.routers.parent_story_runs import _require_parent

router = APIRouter(prefix="/v1/story-runs", tags=["Parent Video Candidates"])


def _service(request: Request, db: Session) -> ParentVideoCandidateService:
    storage = getattr(request.app.state, "lesson_library_storage", None)
    runtime = getattr(request.app.state, "be1_runtime", None)
    if storage is None or runtime is None:
        raise HTTPException(status_code=503, detail={"code": "PARENT_VIDEO_CANDIDATE_DISABLED"})
    return ParentVideoCandidateService(
        settings=runtime.settings,
        story_repository=SqlParentStoryRunRepository(db),
        profile_lookup=SqlParentStoryProfileLookup(db),
        candidate_repository=SqlParentVideoCandidateRepository(db),
        storage=storage,
        worker=ModalSilentStoryVideoWorker(),
    )


def _invoke(callable_: Callable[..., Any], **kwargs: Any) -> Any:
    try:
        return callable_(**kwargs)
    except ParentVideoCandidateError as exc:
        raise HTTPException(status_code=exc.status_code, detail={"code": exc.code}) from None


def _candidate_response(record: Any) -> ParentVideoCandidateV1:
    persisted_metadata = record.output_metadata
    metadata = None
    if persisted_metadata is not None:
        public_fields = ParentVideoCandidateMetadataV1.model_fields
        public_metadata = {
            field_name: persisted_metadata[field_name]
            for field_name in public_fields
            if field_name in persisted_metadata
        }
        metadata = ParentVideoCandidateMetadataV1.model_validate(public_metadata)
    return ParentVideoCandidateV1(
        video_candidate_id=record.video_candidate_id,
        story_run_id=record.run_id,
        story_revision_id=record.story_revision_id,
        story_revision=record.story_revision_no,
        story_sha256=record.story_sha256,
        state=record.state,
        safe_failure_code=record.safe_failure_code,
        metadata=metadata,
        preview_available=record.state == "CANDIDATE_READY" and bool(record.output_asset_ref),
        product_playable=False,
        safety_validation="NOT_RUN",
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.post(
    "/{run_id}/video-generations",
    response_model=ParentVideoCandidateEnvelopeV1,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start one synthetic Parent LTX video candidate",
)
def request_parent_video_candidate(
    run_id: UUID,
    payload: ParentVideoCandidateRequestV1,
    request: Request,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)],
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentVideoCandidateEnvelopeV1:
    _require_parent(db, principal)
    record, _replayed = _invoke(
        _service(request, db).request,
        principal=principal,
        run_id=str(run_id),
        expected_story_revision=payload.expected_story_revision,
        expected_story_sha256=payload.expected_story_sha256,
        idempotency_key=idempotency_key,
    )
    return ParentVideoCandidateEnvelopeV1(
        request_id=uuid4(), video_candidate=_candidate_response(record)
    )


@router.get(
    "/{run_id}/video-generations/current",
    response_model=ParentCurrentVideoCandidateEnvelopeV1,
    summary="Read the current Parent video-candidate status",
)
def get_current_parent_video_candidate(
    run_id: UUID,
    request: Request,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentCurrentVideoCandidateEnvelopeV1:
    _require_parent(db, principal)
    record = _invoke(
        _service(request, db).get_current,
        principal=principal,
        run_id=str(run_id),
    )
    return ParentCurrentVideoCandidateEnvelopeV1(
        request_id=uuid4(),
        video_candidate=_candidate_response(record) if record is not None else None,
    )


@router.get(
    "/{run_id}/video-generations/{video_candidate_id}",
    response_model=ParentVideoCandidateEnvelopeV1,
    summary="Poll a Parent video-candidate job",
)
def get_parent_video_candidate(
    run_id: UUID,
    video_candidate_id: UUID,
    request: Request,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentVideoCandidateEnvelopeV1:
    _require_parent(db, principal)
    record = _invoke(
        _service(request, db).get,
        principal=principal,
        run_id=str(run_id),
        video_candidate_id=str(video_candidate_id),
    )
    return ParentVideoCandidateEnvelopeV1(
        request_id=uuid4(), video_candidate=_candidate_response(record)
    )


@router.get(
    "/{run_id}/video-generations/{video_candidate_id}/preview",
    summary="Stream an authenticated synthetic technical preview",
    responses={200: {"content": {"video/mp4": {"schema": {"type": "string", "format": "binary"}}}}},
)
def stream_parent_video_candidate_preview(
    run_id: UUID,
    video_candidate_id: UUID,
    request: Request,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    _require_parent(db, principal)
    service = _service(request, db)
    stored: StoredObject = _invoke(
        service.get_preview_object,
        principal=principal,
        run_id=str(run_id),
        video_candidate_id=str(video_candidate_id),
    )
    if stored.content_type != "video/mp4" or stored.content_length <= 0:
        stored.body.close()
        raise HTTPException(status_code=502, detail={"code": "VIDEO_CANDIDATE_OUTPUT_INVALID"})

    def chunks() -> Iterator[bytes]:
        try:
            while True:
                chunk = stored.body.read(128 * 1024)
                if not chunk:
                    break
                yield chunk
        finally:
            stored.body.close()

    return StreamingResponse(
        chunks(),
        media_type="video/mp4",
        headers={
            "Content-Length": str(stored.content_length),
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
            "Content-Disposition": f'inline; filename="{video_candidate_id}.mp4"',
        },
    )


__all__ = ["router"]
