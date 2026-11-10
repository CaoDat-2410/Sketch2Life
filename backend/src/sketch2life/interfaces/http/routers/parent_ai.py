"""Authenticated Parent AI routes with server-owned StoryRun context and private assets."""

# ruff: noqa: B008

from __future__ import annotations

import base64
import binascii
import hashlib
import json
from io import BytesIO
from math import isfinite
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from structlog import get_logger

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.lesson_documents import MalwareDetected, MalwareScannerUnavailable
from sketch2life.application.ports.object_storage import ObjectStorageFailure
from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
from sketch2life.application.services.parent_story_runs import (
    ParentStoryRunService,
    ParentStoryRunServiceError,
)
from sketch2life.contracts.schemas.ai_story import (
    StoryRevisionDraftV1,
    validate_butterfly_lifecycle_v1,
)
from sketch2life.contracts.schemas.modal_ai import (
    ParentDrawingAnalysisRequestV1,
    ParentSketchGuideRequestV1,
    ParentStoryRequestV1,
)
from sketch2life.contracts.schemas.parent_story_runs import ParentStoryRunResponseV1
from sketch2life.infrastructure.ai.modal_function_client import (
    FLUX_MODEL_PROVENANCE,
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
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
)
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult

router = APIRouter(prefix="/api/parent/v1/ai", tags=["Parent AI v1"])
_LOGGER = get_logger(__name__)
_STORY_PROMPT_VERSION = "parent-story-v2.2026-11-10"


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


def _policy_version() -> str:
    value = get_settings().parent_consent_policy_version.strip()
    if not value or not get_settings().parent_consent_policy_text.strip():
        raise HTTPException(status_code=503, detail={"code": "PARENT_CONSENT_POLICY_UNAVAILABLE"})
    return value


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
    return ParentStoryRunService(SqlParentStoryRunRepository(db))


def _story_response(record) -> ParentStoryRunResponseV1:
    return ParentStoryRunResponseV1(
        run_id=record.run_id,
        run_state=record.run_state,
        parent_profile_id=record.parent_profile_id,
        profile_revision_ref=record.profile_revision_ref,
        context_revision=record.context_revision,
        context_snapshot=record.context_snapshot,
        context_snapshot_sha256=record.context_snapshot_sha256,
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


@router.post("/sketch-guides", summary="Generate an optional generic line-sketch guide")
def generate_sketch_guide(
    payload: ParentSketchGuideRequestV1,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    _require_parent(db, principal)
    _require_modal_dev()
    request_id = str(uuid4())
    try:
        result = ModalJsonFunctionClient().invoke(
            "parent.sketch-guide.generate",
            {
                "topic": payload.topic,
                "difficulty": payload.difficulty,
                "step_count": payload.step_count,
            },
        )
    except (ModalFunctionOutcomeUnknown, ModalFunctionExecutionFailed) as exc:
        raise _provider_error(
            exc, request_id=request_id, workload="parent.sketch-guide.generate"
        ) from None
    output = result.output
    if output.get("model") != FLUX_MODEL_PROVENANCE:
        raise HTTPException(status_code=502, detail={"code": "MODAL_MODEL_REVISION_MISMATCH"})
    asset = output.get("asset")
    if not isinstance(asset, dict) or not isinstance(asset.get("bytes"), bytes):
        raise HTTPException(status_code=502, detail={"code": "MODAL_OUTPUT_CONTRACT_INVALID"})
    image_bytes = asset["bytes"]
    response_asset = {key: value for key, value in asset.items() if key != "bytes"}
    _LOGGER.info(
        "parent_modal_request_completed",
        request_id=request_id,
        modal_call_id=result.call_id,
        workload="parent.sketch-guide.generate",
        elapsed_seconds=result.elapsed_seconds,
    )
    return {
        "request_id": request_id,
        "modal_call_id": result.call_id,
        "status": "DRAFT",
        "review_required": True,
        "model": output.get("model"),
        "asset": response_asset,
        "image_base64": base64.b64encode(image_bytes).decode("ascii"),
    }


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
    policy_version = _policy_version()
    request_id = str(uuid4())
    run_id = str(payload.story_run_id)
    repository = SqlParentStoryRunRepository(db)
    try:
        current = repository.read_current_input(
            owner_subject=principal.subject,
            policy_version=policy_version,
            run_id=run_id,
        )
    except ParentStoryRunError as exc:
        raise HTTPException(status_code=exc.status_code, detail={"code": exc.code}) from None
    if current.original_asset_ref is not None:
        raise HTTPException(status_code=409, detail={"code": "PARENT_STORY_ARTWORK_ALREADY_ATTACHED"})

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
        raise HTTPException(status_code=503, detail={"code": "PARENT_ARTWORK_SCAN_UNAVAILABLE"}) from None
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
            owner_subject=principal.subject,
            policy_version=policy_version,
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
            try:
                storage.delete_object(object_key)
            except ObjectStorageFailure:
                pass
        raise HTTPException(status_code=503, detail={"code": "PARENT_ARTWORK_STORAGE_UNAVAILABLE"}) from None
    except (ParentStoryRunError, SQLAlchemyError) as exc:
        for object_key in (original_asset_ref, derived_asset_ref):
            try:
                storage.delete_object(object_key)
            except ObjectStorageFailure:
                pass
        if isinstance(exc, ParentStoryRunError):
            raise HTTPException(status_code=exc.status_code, detail={"code": exc.code}) from None
        raise HTTPException(status_code=503, detail={"code": "PARENT_STORY_RUN_STORE_UNAVAILABLE"}) from None

    try:
        result = ModalDrawingFunctionClient().invoke(prepared)
    except (ModalFunctionOutcomeUnknown, ModalFunctionExecutionFailed) as exc:
        code = "DRAWING_OUTCOME_UNKNOWN" if isinstance(exc, ModalFunctionOutcomeUnknown) else exc.code
        try:
            repository.fail_drawing_analysis(
                owner_subject=principal.subject,
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
            repository.fail_drawing_analysis(
                owner_subject=principal.subject,
                run_id=run_id,
                error_code="MODAL_ADAPTER_OUTCOME_UNKNOWN",
                outcome_unknown=True,
            )
        except ParentStoryRunError:
            pass
        raise _provider_error(unknown, request_id=request_id, workload="drawing.analyze") from None

    raw_candidate = result.output.get("result")
    if not isinstance(raw_candidate, dict) or raw_candidate.get("adult_confirmation_required") is not True:
        repository.fail_drawing_analysis(
            owner_subject=principal.subject,
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
        repository.fail_drawing_analysis(
            owner_subject=principal.subject,
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
            owner_subject=principal.subject,
            policy_version=policy_version,
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
    "/story-runs/{run_id}/story-revisions",
    summary="Generate a story draft from a server-owned Parent StoryRun",
)
def generate_story_revision(
    run_id: UUID,
    payload: ParentStoryRequestV1,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    _require_parent(db, principal)
    _require_modal_dev()
    policy_version = _policy_version()
    request_id = str(uuid4())
    repository = SqlParentStoryRunRepository(db)
    service = ParentStoryRunService(repository)
    try:
        reservation = service.reserve_story_revision(
            owner_subject=principal.subject,
            policy_version=policy_version,
            run_id=str(run_id),
            expected_understanding_revision=payload.expected_understanding_revision,
            rewrite_instruction=payload.rewrite_instruction,
            model_id=STORY_MODEL_ID,
            model_revision=STORY_MODEL_REVISION,
            prompt_version=_STORY_PROMPT_VERSION,
        )
    except (ParentStoryRunError, ParentStoryRunServiceError) as exc:
        raise HTTPException(status_code=exc.status_code, detail={"code": exc.code}) from None
    try:
        raw_story, modal_call_id = ModalStoryFunctionClient().generate(
            {"worker_input": reservation.worker_input}
        )
    except (ModalFunctionOutcomeUnknown, ModalFunctionExecutionFailed) as exc:
        code = "STORY_OUTCOME_UNKNOWN" if isinstance(exc, ModalFunctionOutcomeUnknown) else exc.code
        repository.fail_story_revision(
            owner_subject=principal.subject,
            policy_version=policy_version,
            reservation=reservation,
            error_code=code,
            outcome_unknown=isinstance(exc, ModalFunctionOutcomeUnknown),
        )
        raise _provider_error(exc, request_id=request_id, workload="story.generate") from None
    except ValueError:
        repository.fail_story_revision(
            owner_subject=principal.subject,
            policy_version=policy_version,
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
        repository.fail_story_revision(
            owner_subject=principal.subject,
            policy_version=policy_version,
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
        repository.fail_story_revision(
            owner_subject=principal.subject,
            policy_version=policy_version,
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
    record = repository.complete_story_revision(
        reservation=reservation,
        owner_subject=principal.subject,
        policy_version=policy_version,
        story=normalized_story,
        story_sha256=story_hash,
        provider_call_id=modal_call_id,
        model_id=STORY_MODEL_ID,
        model_revision=STORY_MODEL_REVISION,
    )
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


__all__ = ["router"]
