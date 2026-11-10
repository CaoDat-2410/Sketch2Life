"""Authenticated Parent AI routes backed only by the pinned Modal dev workers."""

# ruff: noqa: B008

from __future__ import annotations

import base64
import binascii
import hashlib
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from structlog import get_logger

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.contracts.schemas.modal_ai import (
    ParentDrawingAnalysisRequestV1,
    ParentSketchGuideRequestV1,
    ParentStoryRequestV1,
)
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
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult

router = APIRouter(prefix="/api/parent/v1/ai", tags=["Parent AI v1"])
_LOGGER = get_logger(__name__)


def _require_parent(db: Session, principal: VerifiedPrincipal) -> None:
    identity = db.get(AdultIdentityModel, principal.subject)
    if (
        identity is None
        or identity.state != "active"
        or identity.account_role != "parent"
        or identity.issuer != principal.issuer
    ):
        raise HTTPException(status_code=403, detail={"code": "PARENT_ROLE_REQUIRED"})


def _require_modal_dev() -> None:
    settings = get_settings()
    if settings.ai_provider != "modal_dev" or settings.env not in {"local", "test"}:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
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


@router.post("/drawing-understandings", summary="Analyze a Parent drawing for adult confirmation")
def analyze_drawing(
    payload: ParentDrawingAnalysisRequestV1,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    _require_parent(db, principal)
    _require_modal_dev()
    request_id = str(uuid4())
    try:
        source_bytes = base64.b64decode(payload.image_base64, validate=True)
    except (ValueError, binascii.Error):
        raise HTTPException(status_code=422, detail={"code": "DRAWING_IMAGE_INVALID"}) from None
    if not source_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        raise HTTPException(status_code=415, detail={"code": "DRAWING_IMAGE_TYPE_NOT_ALLOWED"})
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    try:
        prepared = prepare_drawing_input(
            source_bytes=source_bytes,
            source_media_type="image/png",
            expected_source_sha256=source_hash,
            job_id=str(uuid4()),
            generation_id=str(uuid4()),
            attempt_id=str(uuid4()),
        )
        result = ModalDrawingFunctionClient().invoke(prepared)
    except ValueError:
        raise HTTPException(status_code=422, detail={"code": "DRAWING_IMAGE_INVALID"}) from None
    except (ModalFunctionOutcomeUnknown, ModalFunctionExecutionFailed) as exc:
        raise _provider_error(exc, request_id=request_id, workload="drawing.analyze") from None
    output = result.output
    candidate = output.get("result")
    if not isinstance(candidate, dict) or candidate.get("adult_confirmation_required") is not True:
        raise HTTPException(status_code=502, detail={"code": "MODAL_OUTPUT_CONTRACT_INVALID"})
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
        "drawing_sha256": output.get("input_sha256"),
        "model": output.get("model"),
        "candidate": candidate,
    }


@router.post("/storyboards", summary="Generate a Vietnamese Parent story and storyboard draft")
def generate_storyboard(
    payload: ParentStoryRequestV1,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    _require_parent(db, principal)
    _require_modal_dev()
    request_id = str(uuid4())
    worker_input: dict[str, object] = {
        "schema_version": "sketch2life.story-generation-input.v1",
        "role": "PARENT",
        "language": "vi",
        "confirmed_subject": payload.confirmed_subject,
        "understanding_revision": payload.understanding_revision,
        "drawing_sha256": payload.drawing_sha256,
        "visible_features": payload.visible_features,
        "child_age_months": payload.child_age_months,
        "context_revision": payload.context_revision,
        "adult_confirmed_idea": payload.adult_confirmed_idea,
        "rewrite_instruction": None,
        "lesson_direction": None,
    }
    try:
        result, modal_call_id = ModalStoryFunctionClient().generate(
            {"worker_input": worker_input}
        )
    except (ModalFunctionOutcomeUnknown, ModalFunctionExecutionFailed) as exc:
        raise _provider_error(exc, request_id=request_id, workload="story.generate") from None
    _LOGGER.info(
        "parent_modal_request_completed",
        request_id=request_id,
        modal_call_id=modal_call_id,
        workload="story.generate",
    )
    return {
        "request_id": request_id,
        "modal_call_id": modal_call_id,
        "model": {"id": STORY_MODEL_ID, "revision": STORY_MODEL_REVISION},
        "review_required": True,
        "story": result,
    }


__all__ = ["router"]
