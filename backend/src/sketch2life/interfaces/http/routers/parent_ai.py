"""Authenticated Parent AI routes with server-owned StoryRun context and private assets."""

# ruff: noqa: B008

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import logging
import re
from io import BytesIO
from math import isfinite
from typing import Annotated, Any, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from structlog import get_logger

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.lesson_documents import (
    MalwareDetected,
    MalwareScannerUnavailable,
)
from sketch2life.application.ports.object_storage import ObjectStorageFailure
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryLifecycleRecord,
    ParentStoryRunError,
    ParentStoryRunRecord,
)
from sketch2life.application.services.parent_story_runs import (
    ParentStoryRunService,
    ParentStoryRunServiceError,
)
from sketch2life.application.services.parent_svg_guide import (
    ParentSvgGuideUnavailable,
    build_parent_svg_guide,
)
from sketch2life.application.services.parent_activity_suggestions import (
    ParentActivitySuggestionError,
    ParentActivitySuggestionService,
    classify_parent_activity_worker_failure,
)
from sketch2life.contracts.schemas.ai_story import (
    StoryRevisionDraftV1,
    validate_butterfly_lifecycle_v1,
)
from sketch2life.contracts.schemas.modal_ai import (
    ParentDrawingAnalysisRequestV1,
    ParentStoryRequestV1,
)
from sketch2life.contracts.schemas.parent_story_runs import (
    ParentStoryRunLifecycleEnvelopeV1,
    ParentStoryRunResponseV1,
)
from sketch2life.contracts.schemas.svg_engine import (
    SvgTopicStrokeGuideRequestV1,
    SvgTopicStrokeGuideSourceDraftResponseV1,
)
from sketch2life.contracts.schemas.parent_activity_selection import (
    ParentActivitySelectionReceiptV1,
    ParentActivitySelectionRequestV1,
    ParentActivitySuggestionSetV1,
    ParentActivitySuggestionsRequestV1,
)
from sketch2life.infrastructure.ai.modal_function_client import (
    STORY_MODEL_ID,
    STORY_MODEL_REVISION,
    ModalDrawingFunctionClient,
    ModalFunctionExecutionFailed,
    ModalFunctionOutcomeUnknown,
    ModalJsonFunctionClient,
    ModalStoryFunctionClient,
    prepare_drawing_input,
)
from sketch2life.infrastructure.config.settings import get_settings
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.infrastructure.persistence.parent_story_profile_lookup import (
    SqlParentStoryProfileLookup,
)
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
)
from sketch2life.infrastructure.lesson_library.parent_activity_catalog import (
    LessonLibraryParentActivityCatalogAdapter,
)
from sketch2life.interfaces.http.routers.lesson_library import get_lesson_library_service
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult

router = APIRouter(prefix="/api/parent/v1/ai", tags=["Parent AI v1"])
_LOGGER = get_logger(__name__)
_SAFE_LOGGER = logging.getLogger(__name__)
_STORY_PROMPT_VERSION = "parent-story-qwen38-v3.2026-11-22"


def _require_parent(db: Session, principal: VerifiedPrincipal) -> AdultIdentityModel:
    identity = db.get(AdultIdentityModel, principal.subject)
    if (
        identity is None
        or identity.state != "active"
        or identity.account_role != "parent"
        or identity.issuer != principal.issuer
    ):
        raise HTTPException(status_code=403, detail={"code": "PARENT_ROLE_REQUIRED"})
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


def _drawing_pre_dispatch_error(
    *,
    request_id: str,
    status_code: int,
    code: str,
    stage: str,
    exception: Exception | None = None,
) -> HTTPException:
    """Return a typed drawing error known to happen before Modal dispatch.

    Only fixed stage/code values and the exception class are logged. Request data,
    identity, object keys, provider messages, and exception text stay out of logs.
    """
    _SAFE_LOGGER.warning(
        "parent_drawing_pre_dispatch_failure request_id=%s stage=%s error_code=%s exception_type=%s",
        request_id,
        stage,
        code,
        type(exception).__name__ if exception is not None else "none",
    )
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "request_id": request_id},
    )


def _cleanup_drawing_objects(storage: Any, object_keys: tuple[str, ...], request_id: str) -> None:
    for object_key in object_keys:
        try:
            storage.delete_object(object_key)
        except Exception as exc:
            _SAFE_LOGGER.warning(
                "parent_drawing_pre_dispatch_failure request_id=%s stage=artifact_cleanup error_code=PARENT_ARTWORK_CLEANUP_FAILED exception_type=%s",
                request_id,
                type(exc).__name__,
            )


def _story_service(db: Session) -> ParentStoryRunService:
    return ParentStoryRunService(
        SqlParentStoryRunRepository(db),
        SqlParentStoryProfileLookup(db),
    )


def _story_response(record: ParentStoryRunRecord) -> ParentStoryRunResponseV1:
    return ParentStoryRunResponseV1(
        run_id=record.run_id,
        run_revision=record.run_revision,
        run_state=record.run_state,
        parent_profile_id=record.parent_profile_id,
        profile_revision_ref=record.profile_revision_ref,
        context_revision=record.context_revision,
        context_confirmed=record.context_confirmed,
        context_snapshot=record.context_snapshot,
        context_snapshot_sha256=record.context_snapshot_sha256,
        lesson_pin_snapshot=record.lesson_pin_snapshot,
        current_input_revision=record.current_input_revision,
        understanding_revision=record.understanding_revision,
        subject_label=record.subject_label,
        candidate=record.candidate,
        story_revision_id=record.story_revision_id,
        story_revision_no=record.story_revision_no,
        story_status=record.story_status,
        story_sha256=record.story_sha256,
        story=record.story_content,
        job_state=record.job_state,
        retryable=record.retryable,
        error_code=record.error_code,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


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
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    identity = _require_parent(db, principal)
    request_id = getattr(request.state, "be1_request_id", str(uuid4()))
    try:
        result = build_parent_svg_guide(
            topic=payload.topic,
            intended_subject=payload.intended_subject,
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
        )
    _SAFE_LOGGER.info(
        "parent_svg_guide_source_completed request_id=%s generation_source=%s path_count=%s stage_count=%s document_sha256=%s",
        result["request_id"],
        result["generation_source"],
        result["path_count"],
        result["stage_count"],
        result["document_sha256"],
    )
    return result


# Keep this legacy artwork-ingestion flow outside I2. It writes source and
# derived assets, mutates StoryRun state, and invokes ModalDrawingFunctionClient.
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
    request_id = getattr(request.state, "story_request_id", str(uuid4()))
    _require_parent(db, principal)
    try:
        _require_modal_dev()
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, dict) else {}
        if exc.status_code == 503 and detail.get("code") == "MODAL_AI_NOT_ENABLED":
            raise _drawing_pre_dispatch_error(
                request_id=request_id,
                status_code=503,
                code="MODAL_AI_NOT_ENABLED",
                stage="modal_configuration",
            ) from None
        raise
    run_id = str(payload.story_run_id)
    repository = SqlParentStoryRunRepository(db)
    try:
        current = repository.read_current_input(
            principal=principal,
            run_id=run_id,
        )
    except ParentStoryRunError as exc:
        if exc.code == "PARENT_STORY_RUN_STORE_UNAVAILABLE":
            raise _drawing_pre_dispatch_error(
                request_id=request_id,
                status_code=503,
                code=exc.code,
                stage="story_run_read",
                exception=exc,
            ) from None
        raise HTTPException(
            status_code=exc.status_code,
            detail={"code": exc.code, "request_id": request_id},
        ) from None
    except SQLAlchemyError as exc:
        raise _drawing_pre_dispatch_error(
            request_id=request_id,
            status_code=503,
            code="PARENT_STORY_RUN_STORE_UNAVAILABLE",
            stage="story_run_read",
            exception=exc,
        ) from None
    if current.original_asset_ref is not None:
        raise HTTPException(
            status_code=409,
            detail={"code": "PARENT_STORY_ARTWORK_ALREADY_ATTACHED", "request_id": request_id},
        )

    try:
        source_bytes = base64.b64decode(payload.image_base64, validate=True)
    except (ValueError, binascii.Error):
        raise HTTPException(
            status_code=422,
            detail={"code": "DRAWING_IMAGE_INVALID", "request_id": request_id},
        ) from None
    if (
        (payload.media_type == "image/png" and not source_bytes.startswith(b"\x89PNG\r\n\x1a\n"))
        or (payload.media_type == "image/jpeg" and not source_bytes.startswith(b"\xff\xd8\xff"))
    ):
        raise HTTPException(
            status_code=415,
            detail={"code": "DRAWING_IMAGE_TYPE_NOT_ALLOWED", "request_id": request_id},
        )
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    scanner = getattr(request.app.state, "lesson_document_scanner", None)
    storage = getattr(request.app.state, "lesson_library_storage", None)
    if scanner is None:
        raise _drawing_pre_dispatch_error(
            request_id=request_id,
            status_code=503,
            code="PARENT_ARTWORK_SCAN_UNAVAILABLE",
            stage="scanner_configuration",
        )
    if storage is None:
        raise _drawing_pre_dispatch_error(
            request_id=request_id,
            status_code=503,
            code="PARENT_ARTWORK_STORAGE_UNAVAILABLE",
            stage="object_storage_configuration",
        )
    try:
        scan = scanner.scan(BytesIO(source_bytes))
        if scan.verdict != "CLEAN":
            raise MalwareDetected("MALWARE_DETECTED")
    except MalwareDetected:
        raise HTTPException(
            status_code=422,
            detail={"code": "MALWARE_DETECTED", "request_id": request_id},
        ) from None
    except MalwareScannerUnavailable as exc:
        raise _drawing_pre_dispatch_error(
            request_id=request_id,
            status_code=503,
            code="PARENT_ARTWORK_SCAN_UNAVAILABLE",
            stage="malware_scan",
            exception=exc,
        ) from None
    except Exception as exc:
        raise _drawing_pre_dispatch_error(
            request_id=request_id,
            status_code=503,
            code="PARENT_ARTWORK_SCAN_UNAVAILABLE",
            stage="malware_scan",
            exception=exc,
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
        raise HTTPException(
            status_code=422,
            detail={"code": "DRAWING_IMAGE_INVALID", "request_id": request_id},
        ) from None

    original_asset_ref = f"parent/{run_id}/{uuid4().hex}/original"
    derived_asset_ref = f"parent/{run_id}/{uuid4().hex}/normalized.png"
    try:
        # FR-C-08 (port design §7): re-check the run state immediately before the first
        # put_object, so no object is written for a run in DELETE_PENDING or DELETED.
        repository.ensure_accepting_artwork(principal=principal, run_id=run_id)
    except ParentStoryRunError as exc:
        if exc.code == "PARENT_STORY_RUN_STORE_UNAVAILABLE":
            raise _drawing_pre_dispatch_error(
                request_id=request_id,
                status_code=503,
                code=exc.code,
                stage="artwork_state_check",
                exception=exc,
            ) from None
        raise HTTPException(
            status_code=exc.status_code,
            detail={"code": exc.code, "request_id": request_id},
        ) from None
    except SQLAlchemyError as exc:
        raise _drawing_pre_dispatch_error(
            request_id=request_id,
            status_code=503,
            code="PARENT_STORY_RUN_STORE_UNAVAILABLE",
            stage="artwork_state_check",
            exception=exc,
        ) from None
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
    except ObjectStorageFailure as exc:
        _cleanup_drawing_objects(storage, (original_asset_ref, derived_asset_ref), request_id)
        raise _drawing_pre_dispatch_error(
            request_id=request_id,
            status_code=503,
            code="PARENT_ARTWORK_STORAGE_UNAVAILABLE",
            stage="artifact_write",
            exception=exc,
        ) from None
    except (ParentStoryRunError, SQLAlchemyError) as exc:
        _cleanup_drawing_objects(storage, (original_asset_ref, derived_asset_ref), request_id)
        if isinstance(exc, ParentStoryRunError):
            if exc.code != "PARENT_STORY_RUN_STORE_UNAVAILABLE":
                raise HTTPException(
                    status_code=exc.status_code,
                    detail={"code": exc.code, "request_id": request_id},
                ) from None
        raise _drawing_pre_dispatch_error(
            request_id=request_id,
            status_code=503,
            code="PARENT_STORY_RUN_STORE_UNAVAILABLE",
            stage="artwork_attach",
            exception=exc,
        ) from None
    except Exception as exc:
        _cleanup_drawing_objects(storage, (original_asset_ref, derived_asset_ref), request_id)
        raise _drawing_pre_dispatch_error(
            request_id=request_id,
            status_code=503,
            code="PARENT_ARTWORK_STORAGE_UNAVAILABLE",
            stage="artifact_persistence",
            exception=exc,
        ) from None

    try:
        result = ModalDrawingFunctionClient().invoke(prepared)
    except (ModalFunctionOutcomeUnknown, ModalFunctionExecutionFailed) as exc:
        code = "DRAWING_OUTCOME_UNKNOWN" if isinstance(exc, ModalFunctionOutcomeUnknown) else exc.code
        try:
            _fail_story_run(
                repository,
                operation="drawing",
                principal=principal,
                run_id=run_id,
                error_code=code,
                outcome_unknown=isinstance(exc, ModalFunctionOutcomeUnknown),
            )
        except ParentStoryRunError:
            pass
        raise _provider_error(exc, request_id=request_id, workload="drawing.analyze") from None
    except Exception as exc:
        _LOGGER.warning(
            "parent_modal_adapter_error",
            request_id=request_id,
            workload="drawing.analyze",
            exception_type=type(exc).__name__,
        )
        unknown = ModalFunctionOutcomeUnknown()
        try:
            _fail_story_run(
                repository,
                operation="drawing",
                principal=principal,
                run_id=run_id,
                error_code="MODAL_ADAPTER_OUTCOME_UNKNOWN",
                outcome_unknown=True,
            )
        except ParentStoryRunError:
            pass
        raise _provider_error(unknown, request_id=request_id, workload="drawing.analyze") from None

    raw_candidate = result.output.get("result")
    if not isinstance(raw_candidate, dict) or raw_candidate.get("adult_confirmation_required") is not True:
        _fail_story_run(
            repository,
            operation="drawing",
            principal=principal,
            run_id=run_id,
            error_code="MODAL_OUTPUT_CONTRACT_INVALID",
            outcome_unknown=False,
        )
        raise HTTPException(status_code=502, detail={"code": "MODAL_OUTPUT_CONTRACT_INVALID", "request_id": request_id})
    raw_subject = raw_candidate.get("candidate_subject")
    candidate_subject = raw_subject.strip()[:160] if isinstance(raw_subject, str) else ""
    raw_features = raw_candidate.get("visible_features")
    if not isinstance(raw_features, list):
        raw_features = []
    visible_features = [value.strip()[:160] for value in raw_features[:4] if isinstance(value, str) and value.strip()]
    confidence_value = raw_candidate.get("confidence")
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
        raise HTTPException(status_code=502, detail={"code": "MODAL_OUTPUT_CONTRACT_INVALID", "request_id": request_id})
    candidate = {
        "candidate_subject": candidate_subject or None,
        "visible_features": visible_features,
        "confidence": float(confidence_value),
        "adult_confirmation_required": True,
        "decision": "REVIEW_REQUIRED",
    }
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
        _SAFE_LOGGER.warning(
            "parent_drawing_post_dispatch_failure request_id=%s stage=result_persist error_code=PARENT_DRAWING_RESULT_STORE_UNAVAILABLE exception_type=%s",
            request_id,
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=503,
            detail={"code": "PARENT_DRAWING_RESULT_STORE_UNAVAILABLE", "request_id": request_id},
        ) from None
    except SQLAlchemyError as exc:
        _SAFE_LOGGER.warning(
            "parent_drawing_post_dispatch_failure request_id=%s stage=result_persist error_code=PARENT_DRAWING_RESULT_STORE_UNAVAILABLE exception_type=%s",
            request_id,
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=503,
            detail={"code": "PARENT_DRAWING_RESULT_STORE_UNAVAILABLE", "request_id": request_id},
        ) from None
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
    summary="Suggest Parent activities from authorized lesson versions and persist the set",
)
def suggest_parent_activities(
    run_id: UUID,
    payload: ParentActivitySuggestionsRequestV1,
    request: Request,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=200)],
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentActivitySuggestionSetV1:
    _require_parent(db, principal)
    request_id = str(uuid4())
    repository = SqlParentStoryRunRepository(db)
    try:
        reservation = repository.reserve_activity_suggestion_set(
            principal=principal,
            run_id=str(run_id),
            expected_understanding_revision=payload.expected_understanding_revision,
            idempotency_key=idempotency_key,
        )
    except ParentStoryRunError as exc:
        raise HTTPException(status_code=exc.status_code, detail={"code": exc.code}) from None

    if reservation.replayed:
        try:
            return _activity_suggestion_set_model(reservation.replay_body)
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
            lesson_service = get_lesson_library_service(request, db)
            service = ParentActivitySuggestionService(
                LessonLibraryParentActivityCatalogAdapter(lesson_service)
            )
            prepared = service.prepare(
                parent_principal_ref=principal.subject,
                context_snapshot=reservation.context_snapshot,
                subject_label=reservation.subject_label,
                visible_features=reservation.visible_features,
                pinned_lesson_snapshot=None,
                exclude_activity_keys=reservation.excluded_candidate_keys,
            )
            _LOGGER.info(
                "parent_activity_suggestions_catalog_prepared",
                request_id=request_id,
                accessible_lesson_count=prepared.accessible_lesson_count,
                age_access_eligible_lesson_count=(
                    prepared.age_access_eligible_lesson_count
                ),
                age_access_eligible_activity_count=(
                    prepared.age_access_eligible_activity_count
                ),
                relevance_matched_activity_count=(
                    prepared.relevance_matched_activity_count
                ),
                candidate_count_sent=prepared.candidate_count,
                truncated_catalog_context_field_count=(
                    prepared.truncated_catalog_context_field_count
                ),
            )
            workload_started = True
            modal_result = ModalJsonFunctionClient().invoke(
                "parent.activity.suggest", prepared.worker_input
            )
            raw_result = modal_result.output.get("result")
            if not isinstance(raw_result, dict):
                raise ParentActivitySuggestionError("MODAL_OUTPUT_CONTRACT_INVALID")
            result = service.resolve(
                prepared=prepared,
                raw_result=raw_result,
                request_id=request_id,
                story_run_id=str(run_id),
                understanding_revision=reservation.understanding_revision,
                modal_call_id=modal_result.call_id,
                excluded_activities=reservation.excluded_activities,
            )

        result["contract"] = "ParentActivitySuggestionSetV1"
        activities = result.get("activities")
        if not isinstance(activities, list) or not activities:
            raise ParentActivitySuggestionError("PARENT_ACTIVITY_RESPONSE_INVALID")
        activities_hash = hashlib.sha256(
            json.dumps(
                activities,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        result.update(
            {
                "suggestion_set_id": reservation.suggestion_set_id,
                "set_revision": reservation.set_revision,
                "activities_snapshot_sha256": activities_hash,
            }
        )
        validated = _activity_suggestion_set_model(result)
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
                generation_source="PINNED_LESSON" if reservation.lesson_pin_snapshot else "QWEN3_8_MODAL",
        )
        return _activity_suggestion_set_model(persisted)
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
        raise HTTPException(status_code=status_code, detail={"code": exc.code, "request_id": request_id}) from None
    except (ModalFunctionOutcomeUnknown, ModalFunctionExecutionFailed) as exc:
        worker_error_code = None if isinstance(exc, ModalFunctionOutcomeUnknown) else exc.code
        if isinstance(exc, ModalFunctionOutcomeUnknown):
            status_code = 504
            error_code = "PARENT_ACTIVITY_OUTCOME_UNKNOWN"
            diagnostic_code = None
        else:
            status_code = 502
            error_code, diagnostic_code = classify_parent_activity_worker_failure(
                exc.code
            )
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
            worker_error_code=worker_error_code,
            modal_call_id=getattr(exc, "call_id", None),
            workload="parent.activity.suggest",
        )
        raise HTTPException(status_code=status_code, detail={"code": error_code, "request_id": request_id}) from None
    except HTTPException as exc:
        if reservation.receipt_id is not None:
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
        if reservation.receipt_id is not None:
            status_code = exc.status_code if exc.status_code in {409, 422, 503} else 503
            repository.fail_activity_suggestion_set(
                principal=principal,
                reservation=reservation,
                error_code=exc.code,
                response_status=status_code,
            )
        raise HTTPException(status_code=exc.status_code, detail={"code": exc.code}) from None
    except Exception as exc:
        error_code = "PARENT_ACTIVITY_OUTCOME_UNKNOWN" if workload_started else "PARENT_ACTIVITY_SERVICE_UNAVAILABLE"
        status_code = 504 if workload_started else 503
        try:
            repository.fail_activity_suggestion_set(
                principal=principal,
                reservation=reservation,
                error_code=error_code,
                response_status=status_code,
            )
        except ParentStoryRunError:
            pass
        _LOGGER.exception(
            "parent_activity_suggestions_unhandled_failure",
            request_id=request_id,
            story_run_id=str(run_id),
            error_code=error_code,
            exception_type=type(exc).__name__,
            modal_call_id=modal_result.call_id if modal_result is not None else None,
        )
        raise HTTPException(status_code=status_code, detail={"code": error_code, "request_id": request_id}) from None
@router.post(
    "/story-runs/{run_id}/activity-selection",
    response_model=ParentActivitySelectionReceiptV1,
    summary="Persist the Parent's primary activity from the latest suggestion set",
)
def select_parent_activity(
    run_id: UUID,
    payload: ParentActivitySelectionRequestV1,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=200)],
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentActivitySelectionReceiptV1:
    _require_parent(db, principal)
    try:
        selection = SqlParentStoryRunRepository(db).select_activity(
            principal=principal,
            run_id=str(run_id),
            suggestion_set_id=str(payload.suggestion_set_id),
            expected_understanding_revision=payload.expected_understanding_revision,
            activity_index=payload.activity_index,
            idempotency_key=idempotency_key,
            activity_selection_id=str(uuid4()),
        )
    except ParentStoryRunError as exc:
        raise HTTPException(status_code=exc.status_code, detail={"code": exc.code}) from None
    return ParentActivitySelectionReceiptV1(
        contract="ParentActivitySelectionReceiptV1",
        request_id=uuid4(),
        story_run_id=run_id,
        suggestion_set_id=UUID(selection.suggestion_set_id),
        activity_selection_id=UUID(selection.activity_selection_id),
        selection_revision=selection.selection_revision,
        understanding_revision=selection.understanding_revision,
        activity_index=selection.activity_index,
        activity_snapshot_sha256=selection.activity_snapshot_sha256,
        persisted_at=selection.created_at,
    )


@router.post(
    "/story-runs/{run_id}/story-revisions",
    summary="Generate a story draft from a server-owned Parent StoryRun",
)
def generate_story_revision(
    run_id: UUID,
    payload: ParentStoryRequestV1,
    response: Response,
    idempotency_key: Annotated[
        str, Header(alias="Idempotency-Key", min_length=1, max_length=200)
    ],
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    identity = _require_parent(db, principal)
    _require_modal_dev()
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
            prompt_version=_STORY_PROMPT_VERSION,
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
            {"worker_input": reservation.worker_input}
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
    try:
        story = StoryRevisionDraftV1.model_validate(raw_story)
        validate_butterfly_lifecycle_v1(
            story,
            confirmed_subject=str(reservation.worker_input["confirmed_subject"]),
        )
    except (ValidationError, ValueError) as exc:
        code = (
            "EDUCATIONAL_FACT_CHECK_FAILED"
            if str(exc) in {
                "EDUCATIONAL_FACT_FORBIDDEN_CLAIM",
                "EDUCATIONAL_FACT_STAGE_MISSING",
                "EDUCATIONAL_FACT_ORDER_INVALID",
            }
            else "STORY_OUTPUT_INVALID"
        )
        _fail_story_run(
            repository,
            operation="story",
            principal=principal,
            reservation=reservation,
            error_code=code,
            outcome_unknown=False,
        )
        raise HTTPException(status_code=502, detail={"code": code, "request_id": request_id}) from None
    normalized_story = story.model_dump(mode="json")
    story_hash = hashlib.sha256(
        json.dumps(
            normalized_story,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    try:
        record = repository.complete_story_revision(
            reservation=reservation,
            principal=principal,
            story=normalized_story,
            story_sha256=story_hash,
            provider_call_id=modal_call_id,
            model_id=STORY_MODEL_ID,
            model_revision=STORY_MODEL_REVISION,
        )
    except ParentStoryRunError as exc:
        if exc.code != "INVALID_STATE_TRANSITION":
            raise
        raise HTTPException(status_code=exc.status_code, detail={"code": exc.code}) from None
    if isinstance(record, ParentStoryLifecycleRecord):
        # complete_story_revision refuses a purged run; a projection here is never served.
        raise HTTPException(status_code=409, detail={"code": "INVALID_STATE_TRANSITION"})
    _LOGGER.info(
        "parent_modal_request_completed",
        request_id=request_id,
        modal_call_id=modal_call_id,
        workload="story.generate",
        revision_no=reservation.revision_no,
    )
    return {
        "request_id": request_id,
        "modal_call_id": modal_call_id,
        "story_run": _story_response(record),
        "story": record.story_content,
        "story_sha256": record.story_sha256,
        "review_required": True,
        "model": {"id": STORY_MODEL_ID, "revision": STORY_MODEL_REVISION},
    }


def _activity_suggestion_set_model(payload: dict[str, Any]) -> ParentActivitySuggestionSetV1:
    return ParentActivitySuggestionSetV1.model_validate_json(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    )


__all__ = ["router"]
