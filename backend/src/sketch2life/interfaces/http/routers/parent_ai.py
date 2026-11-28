"""Authenticated Parent AI routes with server-owned StoryRun context and private assets."""

# ruff: noqa: B008

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import logging
import re
from collections.abc import Sequence
from contextlib import suppress
from io import BytesIO
from math import isfinite
from typing import Annotated, Any, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request, Response
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from structlog import get_logger

from sketch2life.application.parent_subject_roles import normalize_worker_candidate
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.lesson_documents import (
    MalwareDetected,
    MalwareScannerUnavailable,
)
from sketch2life.application.ports.object_storage import ObjectStorageFailure
from sketch2life.application.ports.parent_activity_catalog import (
    ParentActivityCatalogPort,
    ParentActivityLesson,
)
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryLifecycleRecord,
    ParentStoryRunError,
    ParentStoryRunRecord,
)
from sketch2life.application.services.parent_activity_selection import (
    ParentActivitySelectionService,
)
from sketch2life.application.services.parent_activity_suggestions import (
    ParentActivitySuggestionError,
    ParentActivitySuggestionService,
    classify_parent_activity_worker_failure,
    generate_activity_suggestions,
)
from sketch2life.application.services.parent_story_runs import (
    ParentStoryRunService,
    ParentStoryRunServiceError,
)
from sketch2life.application.services.story_output import (
    StoryOutputInvalid,
    complete_generated_story,
)
from sketch2life.application.story_staging import split_story_staging
from sketch2life.contracts.schemas.modal_ai import (
    ParentDrawingAnalysisRequestV1,
    ParentStoryRequestV1,
    ParentSuggestedActivityV2,
)
from sketch2life.contracts.schemas.parent_activity_selection import (
    ParentActivitySelectionReceiptV1,
    ParentActivitySelectionRequestV1,
    ParentActivitySuggestionSetV1,
    ParentActivitySuggestionsRequestV1,
)
from sketch2life.contracts.schemas.parent_story_runs import (
    ParentStoryRunLifecycleEnvelopeV1,
)
from sketch2life.contracts.schemas.svg_engine import (
    SvgTopicStrokeGuideRequestV1,
    SvgTopicStrokeGuideSourceDraftResponseV1,
)
from sketch2life.infrastructure.ai.modal_function_client import (
    STORY_MODEL_ID,
    STORY_MODEL_REVISION,
    ModalDrawingFunctionClient,
    ModalFunctionExecutionFailed,
    ModalFunctionOutcomeUnknown,
    ModalJsonFunctionClient,  # noqa: F401 ? retained for the no-fallback contract test
    ModalStoryFunctionClient,
    prepare_drawing_input,
)
from sketch2life.infrastructure.ai.story_generator import to_dev_story_worker_input
from sketch2life.infrastructure.config.settings import get_settings
from sketch2life.infrastructure.lesson_library.parent_activity_catalog import (
    LessonLibraryParentActivityCatalogAdapter,
)
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.infrastructure.persistence.parent_activity_suggestion_set_repository import (
    SqlParentActivitySuggestionSetRepository,
)
from sketch2life.infrastructure.persistence.parent_story_profile_lookup import (
    SqlParentStoryProfileLookup,
)
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
)
from sketch2life.infrastructure.story_video.modal_video_warm_up import VideoWarmUp
from sketch2life.infrastructure.svg.parent_guide import (
    ParentSvgGuideUnavailable,
    build_parent_svg_guide,
)
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.routers.lesson_library import get_lesson_library_service
from sketch2life.interfaces.http.routers.parent_story_inputs import schedule_first_story
from sketch2life.interfaces.http.routers.parent_story_runs import story_run_response

router = APIRouter(prefix="/api/parent/v1/ai", tags=["Parent AI v1"])
_LOGGER = get_logger(__name__)
_SAFE_LOGGER = logging.getLogger(__name__)
_STORY_PROMPT_VERSION = "parent-story-v2.2026-11-10"
# A complete standalone catalog response needs three candidates; fewer may be paired with drafts.
MINIMUM_CATALOG_CANDIDATES_FOR_STANDALONE_SET = 3
_LEARNING_PROMPT_VERSION = "parent-learning-v2.2026-11-27"  # FEAT-098
_VIDEO_WARM_UP = VideoWarmUp()


def _warm_up_video_container(background: BackgroundTasks) -> None:
    settings = get_settings()
    if (
        settings.story_video_warm_up
        and settings.ai_provider == "modal_dev"
        and settings.story_video_adapters != "unconfigured"
    ):
        background.add_task(_VIDEO_WARM_UP.request)


def _start_video_early(
    request: Request, background: BackgroundTasks, run_id: str, story_revision_id: str
) -> None:
    """FEAT-098: prepare the video while the adult reads the script when that is composed, else only
    warm up the container."""

    ahead = getattr(request.app.state, "video_prepare_ahead", None)
    if ahead is None:
        _warm_up_video_container(background)
    else:
        background.add_task(ahead.request, run_id, story_revision_id)


def _require_parent(db: Session, principal: VerifiedPrincipal) -> AdultIdentityModel:
    identity = db.get(AdultIdentityModel, principal.subject)
    if (
        identity is None
        or identity.state != "active"
        or identity.account_role != "parent"
        or identity.issuer != principal.issuer
    ):
        # CONV-1 (SRS l.864-865, T-2d, OD-18b): not an active Parent means out of scope, so the
        # answer is the one uniform 404 of an unknown resource, before the provider gate.
        raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND"})
    return identity


def _require_modal_dev() -> None:
    settings = get_settings()
    if settings.ai_provider != "modal_dev" or settings.env not in {"local", "test"}:
        raise HTTPException(
            status_code=503,
            detail={"code": "MODAL_AI_NOT_ENABLED"},
        )


def _provider_error(exc: Exception, *, request_id: str, workload: str) -> HTTPException:
    if isinstance(exc, ModalFunctionOutcomeUnknown):
        _LOGGER.warning(
            "parent_modal_outcome_unknown",
            request_id=request_id,
            workload=workload,
            modal_call_id=exc.call_id,
        )
        return HTTPException(
            status_code=504,
            detail={"code": "MODAL_OUTCOME_UNKNOWN", "request_id": request_id},
        )
    code = exc.code if isinstance(exc, ModalFunctionExecutionFailed) else "MODAL_REQUEST_FAILED"
    _LOGGER.warning(
        "parent_modal_request_failed",
        request_id=request_id,
        workload=workload,
        error_code=code,
        exception_type=type(exc).__name__,
    )
    return HTTPException(
        status_code=502,
        detail={"code": code, "request_id": request_id},
    )


def _story_service(db: Session) -> ParentStoryRunService:
    return ParentStoryRunService(
        SqlParentStoryRunRepository(db),
        SqlParentStoryProfileLookup(db),
    )


class _ParentAiActivityCatalog(ParentActivityCatalogPort):
    """Resolve the Lesson Library catalog lazily for catalog suggestions and selections."""

    def __init__(self, request: Request, db: Session) -> None:
        self._request = request
        self._db = db

    def list_accessible_lessons(
        self, *, parent_principal_ref: str
    ) -> Sequence[ParentActivityLesson]:
        adapter = LessonLibraryParentActivityCatalogAdapter(
            get_lesson_library_service(self._request, self._db)
        )
        return adapter.list_accessible_lessons(parent_principal_ref=parent_principal_ref)


def _activity_selection_service(
    request: Request,
    db: Session,
    repository: SqlParentActivitySuggestionSetRepository,
) -> ParentActivitySelectionService:
    return ParentActivitySelectionService(
        SqlParentStoryRunRepository(db),
        _ParentAiActivityCatalog(request, db),
        suggestion_sets=repository,
    )


def _parent_activity_ai_enabled() -> bool:
    settings = get_settings()
    return (
        settings.env in {"local", "test"}
        and settings.ai_provider == "modal_dev"
        and settings.parent_topic_subject_ai_enabled
    )


def _require_parent_activity_ai() -> None:
    if not _parent_activity_ai_enabled():
        raise HTTPException(status_code=503, detail={"code": "MODAL_AI_NOT_ENABLED"})


def _activity_suggestion_set_model(payload: dict[str, Any]) -> ParentActivitySuggestionSetV1:
    return ParentActivitySuggestionSetV1.model_validate(payload)


def _catalog_suggested_activity(candidate: Any) -> dict[str, Any]:
    return ParentSuggestedActivityV2(
        **candidate.activity,
        source=(
            "PINNED_LESSON"
            if candidate.source == "PINNED_LESSON"
            else "PUBLISHED_SHARED_LESSON"
        ),
        source_lesson_id=candidate.lesson_id,
        source_lesson_title=candidate.lesson_title,
        source_lesson_version_id=candidate.version_id,
        source_content_sha256=candidate.content_sha256,
        source_activity_index=candidate.activity_index,
        match_reason=None,
    ).model_dump(mode="json")


def _activity_set_hash(activities: list[dict[str, Any]]) -> str:
    canonical = json.dumps(
        activities, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _finalize_activity_suggestion_error(
    repository: SqlParentActivitySuggestionSetRepository,
    *,
    principal: VerifiedPrincipal,
    reservation: Any,
    error_code: str,
    response_status: int,
    request_id: str,
    cache_failure: bool = False,
    current_version: int | None = None,
) -> None:
    try:
        repository.fail_activity_suggestion_set(
            principal=principal,
            reservation=reservation,
            error_code=error_code,
            response_status=response_status,
            request_id=request_id,
            cache_failure=cache_failure,
            current_version=current_version,
        )
    except ParentStoryRunError as exc:
        _LOGGER.warning(
            "parent_activity_suggestions_receipt_finalize_failed",
            request_id=request_id,
            error_code=exc.code,
        )


# One builder for the whole run model (T-1c): this legacy route family shows the same shape as
# ``/v1/story-runs`` (video, quota summary and timeline included).
_story_response = story_run_response


def _lifecycle_body(request_id: str, record: ParentStoryLifecycleRecord) -> dict[str, object]:
    return ParentStoryRunLifecycleEnvelopeV1.model_validate(
        {"request_id": request_id, "lifecycle": record.as_body()}
    ).model_dump(mode="json")


def _fail_story_run(
    repository: SqlParentStoryRunRepository,
    *,
    operation: Literal["drawing", "story"],
    **kwargs: Any,
) -> None:
    try:
        if operation == "drawing":
            repository.fail_drawing_analysis(**kwargs)
        else:
            repository.fail_story_revision(**kwargs)
    except ParentStoryRunError as exc:
        if exc.code == "INVALID_STATE_TRANSITION":
            raise HTTPException(status_code=exc.status_code, detail={"code": exc.code}) from None
        raise


@router.post(
    "/sketch-guides",
    response_model=SvgTopicStrokeGuideSourceDraftResponseV1,
    summary="Create an optional private SVG guide from a curated source",
)
def generate_sketch_guide(
    payload: SvgTopicStrokeGuideRequestV1,
    request: Request,
    response: Response,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    _require_parent(db, principal)
    request_id = getattr(request.state, "be1_request_id", str(uuid4()))
    response.headers["X-Request-ID"] = request_id
    try:
        result = build_parent_svg_guide(
            topic=payload.topic,
            intended_subject=payload.intended_subject,
            difficulty=payload.difficulty,
            request_id=request_id,
        )
    except ParentSvgGuideUnavailable as exc:
        code = str(exc)
        _SAFE_LOGGER.warning(
            "parent_svg_guide_source_rejected request_id=%s error_code=%s",
            request_id,
            code,
        )
        raise HTTPException(
            status_code=422,
            detail={"code": code, "request_id": request_id},
            headers={"X-Request-ID": request_id},
        ) from None
    except Exception as exc:
        reason_code = str(exc)
        if re.fullmatch(r"[A-Z][A-Z0-9_]{0,79}", reason_code) is None:
            reason_code = "UNCLASSIFIED_SOURCE_FAILURE"
        _SAFE_LOGGER.error(
            "parent_svg_guide_source_failed request_id=%s exception_type=%s reason_code=%s",
            request_id,
            type(exc).__name__,
            reason_code,
        )
        raise HTTPException(
            status_code=503,
            detail={"code": "CURATED_SVG_GUIDE_UNAVAILABLE", "request_id": request_id},
            headers={"X-Request-ID": request_id},
        ) from None
    if result is None:
        _SAFE_LOGGER.info(
            "parent_svg_guide_source_missing request_id=%s source=curated_svg_catalog",
            request_id,
        )
        raise HTTPException(
            status_code=404,
            detail={
                "code": "CURATED_SVG_GUIDE_NOT_FOUND",
                "request_id": request_id,
                "message": "No approved source drawing guide is available for this subject yet.",
            },
            headers={"X-Request-ID": request_id},
        )
    _SAFE_LOGGER.info(
        "parent_svg_guide_source_completed request_id=%s generation_source=%s "
        "path_count=%s stage_count=%s document_sha256=%s",
        result["request_id"],
        result["generation_source"],
        result["path_count"],
        result["stage_count"],
        result["document_sha256"],
    )
    return result


# Keep this legacy artwork-ingestion flow outside I2. It writes source and
# derived assets, mutates StoryRun state, and invokes ModalDrawingFunctionClient.
def _drawing_confidence(candidate: dict[str, object]) -> object:
    """Confidence the drawing worker reported, or 0.0 ("unknown") when it reports none.

    The drawing worker's contract has no confidence field (the adult always confirms the subject),
    so a missing value is not a contract error. A present value is still validated by the caller.
    """

    return candidate.get("confidence", 0.0)


@router.post(
    "/drawing-understandings",
    summary="Store and analyze Parent artwork for an authenticated StoryRun",
)
def analyze_drawing(
    payload: ParentDrawingAnalysisRequestV1,
    request: Request,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    _require_parent(db, principal)
    _require_modal_dev()
    settings = get_settings()
    request_id = str(uuid4())
    run_id = str(payload.story_run_id)
    repository = SqlParentStoryRunRepository(db)
    try:
        current = repository.read_current_input(
            principal=principal,
            run_id=run_id,
        )
    except ParentStoryRunError as exc:
        raise HTTPException(status_code=exc.status_code, detail={"code": exc.code}) from None
    if current.original_asset_ref is not None:
        raise HTTPException(
            status_code=409, detail={"code": "PARENT_STORY_ARTWORK_ALREADY_ATTACHED"}
        )

    try:
        source_bytes = base64.b64decode(payload.image_base64, validate=True)
    except (ValueError, binascii.Error):
        raise HTTPException(status_code=422, detail={"code": "DRAWING_IMAGE_INVALID"}) from None
    if (
        (payload.media_type == "image/png" and not source_bytes.startswith(b"\x89PNG\r\n\x1a\n"))
        or (payload.media_type == "image/jpeg" and not source_bytes.startswith(b"\xff\xd8\xff"))
    ):
        raise HTTPException(status_code=415, detail={"code": "DRAWING_IMAGE_TYPE_NOT_ALLOWED"})
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    scanner = getattr(request.app.state, "lesson_document_scanner", None)
    storage = getattr(request.app.state, "lesson_library_storage", None)
    if scanner is None or storage is None:
        raise HTTPException(status_code=503, detail={"code": "PARENT_ARTWORK_STORAGE_UNAVAILABLE"})
    try:
        scan = scanner.scan(BytesIO(source_bytes))
        if scan.verdict != "CLEAN":
            raise MalwareDetected("MALWARE_DETECTED")
    except MalwareDetected:
        raise HTTPException(status_code=422, detail={"code": "MALWARE_DETECTED"}) from None
    except MalwareScannerUnavailable:
        raise HTTPException(
            status_code=503, detail={"code": "PARENT_ARTWORK_SCAN_UNAVAILABLE"}
        ) from None
    try:
        prepared = prepare_drawing_input(
            source_bytes=source_bytes,
            source_media_type=payload.media_type,
            expected_source_sha256=source_hash,
            job_id=str(uuid4()),
            generation_id=str(uuid4()),
            attempt_id=str(uuid4()),
        )
    except ValueError:
        raise HTTPException(status_code=422, detail={"code": "DRAWING_IMAGE_INVALID"}) from None

    original_asset_ref = f"parent/{run_id}/{uuid4().hex}/original"
    derived_asset_ref = f"parent/{run_id}/{uuid4().hex}/normalized.png"
    try:
        # FR-C-08 (port design §7): re-check the run state immediately before the first
        # put_object, so no object is written for a run in DELETE_PENDING or DELETED.
        repository.ensure_accepting_artwork(principal=principal, run_id=run_id)
    except ParentStoryRunError as exc:
        raise HTTPException(status_code=exc.status_code, detail={"code": exc.code}) from None
    try:
        storage.put_object(
            original_asset_ref,
            BytesIO(source_bytes),
            content_type=payload.media_type,
            content_length=len(source_bytes),
            metadata={"sha256": source_hash, "run-ref": run_id, "scan-verdict": "CLEAN"},
        )
        storage.put_object(
            derived_asset_ref,
            BytesIO(prepared.drawing_png),
            content_type="image/png",
            content_length=len(prepared.drawing_png),
            metadata={"sha256": prepared.drawing_sha256, "source-ref": original_asset_ref},
        )
        repository.attach_artwork(
            principal=principal,
            run_id=run_id,
            original_asset_ref=original_asset_ref,
            original_sha256=source_hash,
            original_media_type=payload.media_type,
            original_size_bytes=len(source_bytes),
            derived_asset_ref=derived_asset_ref,
            derived_sha256=prepared.drawing_sha256,
            derived_size_bytes=len(prepared.drawing_png),
            scanner_name=scan.scanner_name,
            scanner_version=scan.scanner_version,
        )
    except ObjectStorageFailure:
        for object_key in (original_asset_ref, derived_asset_ref):
            with suppress(ObjectStorageFailure):
                storage.delete_object(object_key)
        raise HTTPException(
            status_code=503, detail={"code": "PARENT_ARTWORK_STORAGE_UNAVAILABLE"}
        ) from None
    except (ParentStoryRunError, SQLAlchemyError) as exc:
        for object_key in (original_asset_ref, derived_asset_ref):
            with suppress(ObjectStorageFailure):
                storage.delete_object(object_key)
        if isinstance(exc, ParentStoryRunError):
            raise HTTPException(status_code=exc.status_code, detail={"code": exc.code}) from None
        raise HTTPException(
            status_code=503, detail={"code": "PARENT_STORY_RUN_STORE_UNAVAILABLE"}
        ) from None

    try:
        result = ModalDrawingFunctionClient().invoke(prepared)
    except (ModalFunctionOutcomeUnknown, ModalFunctionExecutionFailed) as exc:
        code = (
            "DRAWING_OUTCOME_UNKNOWN"
            if isinstance(exc, ModalFunctionOutcomeUnknown)
            else exc.code
        )
        with suppress(ParentStoryRunError):
            _fail_story_run(
                repository,
                operation="drawing",
                principal=principal,
                run_id=run_id,
                error_code=code,
                outcome_unknown=isinstance(exc, ModalFunctionOutcomeUnknown),
            )
        raise _provider_error(exc, request_id=request_id, workload="drawing.analyze") from None
    except Exception as exc:
        _LOGGER.warning(
            "parent_modal_adapter_error",
            request_id=request_id,
            workload="drawing.analyze",
            exception_type=type(exc).__name__,
        )
        unknown = ModalFunctionOutcomeUnknown()
        with suppress(ParentStoryRunError):
            _fail_story_run(
                repository,
                operation="drawing",
                principal=principal,
                run_id=run_id,
                error_code="MODAL_ADAPTER_OUTCOME_UNKNOWN",
                outcome_unknown=True,
            )
        raise _provider_error(unknown, request_id=request_id, workload="drawing.analyze") from None

    raw_candidate = result.output.get("result")
    if (
        not isinstance(raw_candidate, dict)
        or raw_candidate.get("adult_confirmation_required") is not True
    ):
        _fail_story_run(
            repository,
            operation="drawing",
            principal=principal,
            run_id=run_id,
            error_code="MODAL_OUTPUT_CONTRACT_INVALID",
            outcome_unknown=False,
        )
        raise HTTPException(
            status_code=502,
            detail={"code": "MODAL_OUTPUT_CONTRACT_INVALID", "request_id": request_id},
        )
    raw_subject = raw_candidate.get("candidate_subject")
    candidate_subject = raw_subject.strip()[:160] if isinstance(raw_subject, str) else ""
    raw_features = raw_candidate.get("visible_features")
    if not isinstance(raw_features, list):
        raw_features = []
    visible_features = [
        value.strip()[:160]
        for value in raw_features[:4]
        if isinstance(value, str) and value.strip()
    ]
    confidence_value = _drawing_confidence(raw_candidate)
    if (
        not visible_features
        or isinstance(confidence_value, bool)
        or not isinstance(confidence_value, (int, float))
        or not isfinite(float(confidence_value))
        or not 0 <= float(confidence_value) <= 1
    ):
        _fail_story_run(
            repository,
            operation="drawing",
            principal=principal,
            run_id=run_id,
            error_code="MODAL_OUTPUT_CONTRACT_INVALID",
            outcome_unknown=False,
        )
        raise HTTPException(
            status_code=502,
            detail={"code": "MODAL_OUTPUT_CONTRACT_INVALID", "request_id": request_id},
        )
    candidate = normalize_worker_candidate(
        {
            **raw_candidate,
            "candidate_subject": candidate_subject or None,
            "visible_features": visible_features,
            "confidence": float(confidence_value),
        }
    )
    result_snapshot = {"result": candidate}
    try:
        understanding_revision = repository.record_understanding(
            principal=principal,
            run_id=run_id,
            result_snapshot=result_snapshot,
            candidate_subject=candidate_subject or "UNCONFIRMED",
            confidence=float(confidence_value),
        )
    except ParentStoryRunError as exc:
        raise HTTPException(status_code=exc.status_code, detail={"code": exc.code}) from None
    _LOGGER.info(
        "parent_modal_request_completed",
        request_id=request_id,
        modal_call_id=result.call_id,
        workload="drawing.analyze",
        elapsed_seconds=result.elapsed_seconds,
    )
    return {
        "request_id": request_id,
        "modal_call_id": result.call_id,
        "story_run_id": run_id,
        "run_input_revision": current.input_revision + 1,
        "understanding_revision": understanding_revision,
        "drawing_sha256": source_hash,
        "model": result.output.get("model"),
        "candidate": candidate,
        "review_required": True,
    }


@router.post(
    "/story-runs/{run_id}/activity-suggestions",
    response_model=ParentActivitySuggestionSetV1,
    summary="Suggest Parent activities from accessible lessons and persist the set",
)
def suggest_parent_activities(
    run_id: UUID,
    payload: ParentActivitySuggestionsRequestV1,
    request: Request,
    response: Response,
    idempotency_key: Annotated[
        str, Header(alias="Idempotency-Key", min_length=1, max_length=200)
    ],
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentActivitySuggestionSetV1:
    """Catalog-first Qwen selection; a pinned lesson stays within its exact saved revision."""
    _require_parent(db, principal)
    request_id = str(uuid4())
    repository = SqlParentStoryRunRepository(db)
    try:
        reservation = repository.reserve_activity_suggestion_set(
            principal=principal,
            run_id=str(run_id),
            expected_understanding_revision=payload.expected_understanding_revision,
            idempotency_key=idempotency_key,
            reuse_latest=payload.reuse_latest,
        )
    except ParentStoryRunError as exc:
        raise HTTPException(status_code=exc.status_code, detail={"code": exc.code}) from None

    response.headers["Idempotency-Replayed"] = str(reservation.replayed).lower()
    if reservation.replayed:
        try:
            return ParentActivitySuggestionSetV1.model_validate(reservation.replay_body)
        except ValidationError:
            raise HTTPException(
                status_code=503,
                detail={"code": "PARENT_ACTIVITY_RESPONSE_INVALID", "request_id": request_id},
            ) from None

    modal_result = None
    workload_started = False
    try:
        if reservation.lesson_pin_snapshot is not None:
            result = ParentActivitySuggestionService.pinned_lesson_response(
                pinned_lesson_snapshot=reservation.lesson_pin_snapshot,
                age_months=int(reservation.context_snapshot["age_months"]),
                request_id=request_id,
                story_run_id=str(run_id),
                understanding_revision=reservation.understanding_revision,
            )
        else:
            _require_modal_dev()
            lesson_library = get_lesson_library_service(request, db)
            service = ParentActivitySuggestionService(
                LessonLibraryParentActivityCatalogAdapter(lesson_library)
            )
            prepared = service.prepare(
                parent_principal_ref=principal.subject,
                context_snapshot=reservation.context_snapshot,
                subject_label=reservation.subject_label,
                visible_features=list(reservation.visible_features),
                pinned_lesson_snapshot=None,
                exclude_activity_keys=reservation.excluded_candidate_keys,
            )
            _LOGGER.info(
                "parent_activity_suggestions_catalog_prepared",
                request_id=request_id,
                accessible_lesson_count=prepared.accessible_lesson_count,
                age_access_eligible_lesson_count=prepared.age_access_eligible_lesson_count,
                age_access_eligible_activity_count=prepared.age_access_eligible_activity_count,
                relevance_matched_activity_count=prepared.relevance_matched_activity_count,
                candidate_count_sent=prepared.candidate_count,
                truncated_catalog_context_field_count=(
                    prepared.truncated_catalog_context_field_count
                ),
            )
            workload_started = True

            def resolve_answer(answer: Any) -> dict[str, Any]:
                raw_result = answer.output.get("result")
                if not isinstance(raw_result, dict):
                    raise ParentActivitySuggestionError("MODAL_OUTPUT_CONTRACT_INVALID")
                return service.resolve(
                    prepared=prepared,
                    raw_result=raw_result,
                    request_id=request_id,
                    story_run_id=str(run_id),
                    understanding_revision=reservation.understanding_revision,
                    modal_call_id=answer.call_id,
                    excluded_activities=reservation.excluded_activities,
                )

            modal_result, result = generate_activity_suggestions(
                lambda: ModalJsonFunctionClient().invoke(
                    "parent.activity.suggest", prepared.worker_input
                ),
                resolve_answer,
                on_rejected=lambda error: _LOGGER.warning(
                    "parent_activity_suggestions_answer_rejected",
                    request_id=request_id,
                    error_code=error.code,
                    diagnostic_code=error.diagnostic_code,
                ),
            )

        result["contract"] = "ParentActivitySuggestionSetV1"
        activities = result.get("activities")
        if not isinstance(activities, list) or not activities:
            raise ParentActivitySuggestionError("PARENT_ACTIVITY_RESPONSE_INVALID")
        result["activities_snapshot_sha256"] = hashlib.sha256(
            json.dumps(
                activities,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        result.update(
            {
                "request_id": request_id,
                "story_run_id": str(run_id),
                "understanding_revision": reservation.understanding_revision,
                "suggestion_set_id": reservation.suggestion_set_id,
                "set_revision": reservation.set_revision,
                "review_required": True,
            }
        )
        validated = ParentActivitySuggestionSetV1.model_validate(result)
        persisted = repository.complete_activity_suggestion_set(
            principal=principal,
            reservation=reservation,
            response=validated.model_dump(mode="json"),
            provider_call_id=modal_result.call_id if modal_result is not None else None,
        )
        _LOGGER.info(
            "parent_activity_suggestions_completed",
            request_id=request_id,
            story_run_id=str(run_id),
            suggestion_set_id=reservation.suggestion_set_id,
            set_revision=reservation.set_revision,
            understanding_revision=reservation.understanding_revision,
            selection_mode=persisted["selection_mode"],
            activity_count=len(activities),
            modal_call_id=modal_result.call_id if modal_result is not None else None,
            elapsed_seconds=modal_result.elapsed_seconds if modal_result is not None else 0,
        )
        return ParentActivitySuggestionSetV1.model_validate(persisted)
    except ParentActivitySuggestionError as exc:
        status_code = 502 if exc.code in {
            "MODAL_OUTPUT_CONTRACT_INVALID",
            "PARENT_ACTIVITY_QUALITY_GATE_REJECTED",
            "PARENT_ACTIVITY_RESPONSE_INVALID",
        } else 422
        repository.fail_activity_suggestion_set(
            principal=principal,
            reservation=reservation,
            error_code=exc.code,
            response_status=status_code,
        )
        _LOGGER.warning(
            "parent_activity_suggestions_rejected",
            request_id=request_id,
            story_run_id=str(run_id),
            error_code=exc.code,
            diagnostic_code=exc.diagnostic_code,
            modal_call_id=modal_result.call_id if modal_result is not None else None,
        )
        raise HTTPException(
            status_code=status_code,
            detail={"code": exc.code, "request_id": request_id},
        ) from None
    except (ModalFunctionOutcomeUnknown, ModalFunctionExecutionFailed) as exc:
        if isinstance(exc, ModalFunctionOutcomeUnknown):
            status_code, error_code, diagnostic_code = (
                504,
                "PARENT_ACTIVITY_OUTCOME_UNKNOWN",
                None,
            )
        else:
            status_code = 502
            error_code, diagnostic_code = classify_parent_activity_worker_failure(exc.code)
        repository.fail_activity_suggestion_set(
            principal=principal,
            reservation=reservation,
            error_code=error_code,
            response_status=status_code,
        )
        _LOGGER.warning(
            "parent_activity_modal_failed",
            request_id=request_id,
            story_run_id=str(run_id),
            error_code=error_code,
            diagnostic_code=diagnostic_code,
            worker_error_code=None if isinstance(exc, ModalFunctionOutcomeUnknown) else exc.code,
            modal_call_id=getattr(exc, "call_id", None),
            workload="parent.activity.suggest",
        )
        raise HTTPException(
            status_code=status_code,
            detail={"code": error_code, "request_id": request_id},
        ) from None
    except HTTPException as exc:
        status_code = exc.status_code if exc.status_code in {409, 422, 503} else 503
        detail = exc.detail if isinstance(exc.detail, dict) else {}
        error_code = str(detail.get("code", "PARENT_ACTIVITY_DEPENDENCY_UNAVAILABLE"))
        repository.fail_activity_suggestion_set(
            principal=principal,
            reservation=reservation,
            error_code=error_code,
            response_status=status_code,
        )
        raise
    except ParentStoryRunError as exc:
        status_code = exc.status_code if exc.status_code in {409, 422, 503} else 503
        repository.fail_activity_suggestion_set(
            principal=principal,
            reservation=reservation,
            error_code=exc.code,
            response_status=status_code,
        )
        raise HTTPException(status_code=exc.status_code, detail={"code": exc.code}) from None
    except Exception as exc:
        error_code = (
            "PARENT_ACTIVITY_OUTCOME_UNKNOWN"
            if workload_started
            else "PARENT_ACTIVITY_SERVICE_UNAVAILABLE"
        )
        status_code = 504 if workload_started else 503
        with suppress(ParentStoryRunError):
            repository.fail_activity_suggestion_set(
                principal=principal,
                reservation=reservation,
                error_code=error_code,
                response_status=status_code,
            )
        _LOGGER.exception(
            "parent_activity_suggestions_unhandled_failure",
            request_id=request_id,
            story_run_id=str(run_id),
            error_code=error_code,
            exception_type=type(exc).__name__,
            modal_call_id=modal_result.call_id if modal_result is not None else None,
        )
        raise HTTPException(
            status_code=status_code,
            detail={"code": error_code, "request_id": request_id},
        ) from None


@router.post(
    "/story-runs/{run_id}/activity-selection",
    response_model=ParentActivitySelectionReceiptV1,
    summary="Persist the Parent's choice from a stored activity suggestion set",
)
def select_parent_activity(
    run_id: UUID,
    payload: ParentActivitySelectionRequestV1,
    request: Request,
    background_tasks: BackgroundTasks,
    idempotency_key: Annotated[
        str, Header(alias="Idempotency-Key", min_length=1, max_length=200)
    ],
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentActivitySelectionReceiptV1:
    _require_parent(db, principal)
    repository = SqlParentActivitySuggestionSetRepository(db)
    service = _activity_selection_service(request, db, repository)
    try:
        outcome = service.select_suggestion_set_activity(
            principal=principal,
            run_id=str(run_id),
            suggestion_set_id=str(payload.suggestion_set_id),
            expected_understanding_revision=payload.expected_understanding_revision,
            activity_index=payload.activity_index,
            idempotency_key=idempotency_key,
        )
    except ParentStoryRunError as exc:
        detail: dict[str, str | int] = {"code": exc.code}
        if exc.current_version is not None:
            detail["current_version"] = exc.current_version
        raise HTTPException(status_code=exc.status_code, detail=detail) from None
    reservations = [outcome.story_reservation] if outcome.story_reservation is not None else []
    schedule_first_story(request, background_tasks, principal, None, reservations)
    return ParentActivitySelectionReceiptV1.model_validate(outcome.receipt_body)


@router.post(
    "/story-runs/{run_id}/story-revisions",
    summary="Generate a story draft from a server-owned Parent StoryRun",
)
def generate_story_revision(
    run_id: UUID,
    payload: ParentStoryRequestV1,
    response: Response,
    background: BackgroundTasks,
    request: Request,
    idempotency_key: Annotated[
        str, Header(alias="Idempotency-Key", min_length=1, max_length=200)
    ],
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    identity = _require_parent(db, principal)
    _require_modal_dev()
    settings = get_settings()
    request_id = str(uuid4())
    repository = SqlParentStoryRunRepository(db)
    service = _story_service(db)
    try:
        reservation = service.reserve_story_revision(
            principal=principal,
            account_id=identity.account_id,
            run_id=str(run_id),
            expected_understanding_revision=payload.expected_understanding_revision,
            rewrite_instruction=payload.rewrite_instruction,
            idempotency_key=idempotency_key,
            model_id=STORY_MODEL_ID,
            model_revision=STORY_MODEL_REVISION,
            prompt_version=(
                _LEARNING_PROMPT_VERSION if settings.story_learning else _STORY_PROMPT_VERSION
            ),
            # T-2e-a D9: the dev-only first-story route needs the adult's main activity first; the
            # refusal is 409 ``PARENT_ACTIVITY_SELECTION_REQUIRED`` (passed through as the code).
            require_activity_selection=True,
        )
    except (ParentStoryRunError, ParentStoryRunServiceError) as exc:
        raise HTTPException(status_code=exc.status_code, detail={"code": exc.code}) from None
    response.headers["Idempotency-Replayed"] = str(reservation.replayed).lower()
    if reservation.lifecycle is not None:
        # FR-C-08 (Contract §3.3, DTR §6.5): the replay of a purged run returns only the
        # lifecycle envelope, under the route's normal status.
        return _lifecycle_body(request_id, reservation.lifecycle)
    if reservation.replayed:
        replay_body = reservation.replay_body or {}
        record = repository.get_run(principal=principal, run_id=str(run_id))
        if isinstance(record, ParentStoryLifecycleRecord):
            return _lifecycle_body(request_id, record)
        if not isinstance(record, ParentStoryRunRecord):  # a Parent repository never yields one
            raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND"})
        return {
            "request_id": request_id,
            "modal_call_id": replay_body.get("modal_call_id"),
            "story_run": _story_response(record),
            "story": record.story_content,
            "story_sha256": replay_body.get("story_sha256"),
            "review_required": True,
            "model": {
                "id": replay_body.get("model_id"),
                "revision": replay_body.get("model_revision"),
            },
        }
    try:
        raw_story, modal_call_id = ModalStoryFunctionClient().generate(
            {"worker_input": to_dev_story_worker_input(reservation.worker_input)}
        )
    except (ModalFunctionOutcomeUnknown, ModalFunctionExecutionFailed) as exc:
        code = "STORY_OUTCOME_UNKNOWN" if isinstance(exc, ModalFunctionOutcomeUnknown) else exc.code
        _fail_story_run(
            repository,
            operation="story",
            principal=principal,
            reservation=reservation,
            error_code=code,
            outcome_unknown=isinstance(exc, ModalFunctionOutcomeUnknown),
        )
        raise _provider_error(exc, request_id=request_id, workload="story.generate") from None
    except ValueError:
        _fail_story_run(
            repository,
            operation="story",
            principal=principal,
            reservation=reservation,
            error_code="STORY_INPUT_CONTRACT_INVALID",
            outcome_unknown=False,
        )
        raise HTTPException(
            status_code=502,
            detail={"code": "STORY_INPUT_CONTRACT_INVALID", "request_id": request_id},
        ) from None
    except Exception as exc:
        _LOGGER.warning(
            "parent_modal_adapter_error",
            request_id=request_id,
            workload="story.generate",
            exception_type=type(exc).__name__,
        )
        _fail_story_run(
            repository,
            operation="story",
            principal=principal,
            reservation=reservation,
            error_code="STORY_OUTCOME_UNKNOWN",
            outcome_unknown=True,
        )
        raise _provider_error(
            ModalFunctionOutcomeUnknown(),
            request_id=request_id,
            workload="story.generate",
        ) from None
    raw_story, staging, staging_issue = split_story_staging(
        raw_story, reservation.worker_input, scene_count=5
    )
    try:
        # The validation, the fact check, the hash and the store live in the shared service
        # (T-2d), which the story-rewrites runner calls too.
        record = complete_generated_story(
            repository,
            principal=principal,
            reservation=reservation,
            raw_story=raw_story,
            provider_call_id=modal_call_id,
            model_id=STORY_MODEL_ID,
            model_revision=STORY_MODEL_REVISION,
            staging=staging,
            staging_issue=staging_issue,
        )
    except StoryOutputInvalid as invalid:
        raise HTTPException(
            status_code=502, detail={"code": invalid.code, "request_id": request_id}
        ) from None
    except ParentStoryRunError as exc:
        if exc.code != "INVALID_STATE_TRANSITION":
            raise
        raise HTTPException(status_code=exc.status_code, detail={"code": exc.code}) from None
    if not isinstance(record, ParentStoryRunRecord):  # a Parent repository never yields one
        raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND"})
    _LOGGER.info(
        "parent_modal_request_completed",
        request_id=request_id,
        modal_call_id=modal_call_id,
        workload="story.generate",
        revision_no=reservation.revision_no,
    )
    _start_video_early(request, background, str(run_id), reservation.story_revision_id)
    return {
        "request_id": request_id,
        "modal_call_id": modal_call_id,
        "story_run": _story_response(record),
        "story": record.story_content,
        "story_sha256": record.story_sha256,
        "review_required": True,
        "model": {"id": STORY_MODEL_ID, "revision": STORY_MODEL_REVISION},
    }




__all__ = ["router"]
