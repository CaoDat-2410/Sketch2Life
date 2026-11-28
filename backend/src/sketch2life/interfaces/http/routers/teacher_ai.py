"""Teacher AI draft routes; only reviewed, structured lesson fields reach Modal."""

# ruff: noqa: B008

from __future__ import annotations

import base64
import hashlib
import json
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from structlog import get_logger

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.contracts.schemas.modal_ai import (
    TeacherLessonSuggestionRequestV1,
    TeacherReviewedPlanRequestV1,
)
from sketch2life.domain.age_bands import age_band_for_months
from sketch2life.infrastructure.ai.modal_function_client import (
    QWEN_TEXT_MODEL_ID,
    QWEN_TEXT_MODEL_REVISION,
    ModalFunctionExecutionFailed,
    ModalFunctionOutcomeUnknown,
    ModalJsonFunctionClient,
)
from sketch2life.infrastructure.config.settings import get_settings
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.routers.be1_common import require_assignment

MODEL_ID = QWEN_TEXT_MODEL_ID
MODEL_REVISION = QWEN_TEXT_MODEL_REVISION
_LESSON_VISUAL_MODEL_PROVENANCE = {
    "image_generator": {
        "id": "black-forest-labs/flux-3-image-klein",
        "revision": "09561231f44e41381c461caf53d5452005a60ac9",
    },
    "prompt_upsampler": {
        "id": "black-forest-labs/flux-3-image-klein-pup",
        "revision": "a57899549f8f6f64c6c4d88db30827d496ff76d0",
    },
}

router = APIRouter(
    prefix="/api/teacher/v1/organizations/{organization_id}/ai",
    tags=["Teacher AI v1"],
)
_LOGGER = get_logger(__name__)


def _bounded_text_segments(value: str, *, maximum: int = 240) -> list[str]:
    words = value.split()
    segments: list[str] = []
    current = ""
    for word in words:
        while len(word) > maximum:
            if current:
                segments.append(current)
                current = ""
            segments.append(word[:maximum])
            word = word[maximum:]
        candidate = f"{current} {word}".strip()
        if len(candidate) > maximum:
            segments.append(current)
            current = word
        else:
            current = candidate
    if current:
        segments.append(current)
    if not 1 <= len(segments) <= 8:
        raise HTTPException(status_code=422, detail={"code": "TEACHER_PLAN_FIELD_LIMIT_EXCEEDED"})
    return segments


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
            "teacher_modal_outcome_unknown",
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
        "teacher_modal_request_failed",
        request_id=request_id,
        workload=workload,
        error_code=code,
        exception_type=type(exc).__name__,
    )
    return HTTPException(status_code=502, detail={"code": code, "request_id": request_id})


def invoke_teacher_sketch_deck_worker(
    worker_input: dict[str, object], *, request_id: str
) -> dict[str, object]:
    """Invoke the existing allowlisted deck workload; logs contain metadata only."""
    try:
        result = ModalJsonFunctionClient().invoke("teacher.sketch-deck.generate", worker_input)
    except (ModalFunctionOutcomeUnknown, ModalFunctionExecutionFailed) as exc:
        raise _provider_error(
            exc, request_id=request_id, workload="teacher.sketch-deck.generate"
        ) from None
    deck = result.output.get("result")
    if (
        result.output.get("model")
        != {"id": QWEN_TEXT_MODEL_ID, "revision": QWEN_TEXT_MODEL_REVISION}
        or not isinstance(deck, dict)
        or deck.get("review_required") is not True
    ):
        raise HTTPException(status_code=502, detail={"code": "MODAL_OUTPUT_CONTRACT_INVALID"})
    _LOGGER.info(
        "teacher_modal_request_completed",
        request_id=request_id,
        modal_call_id=result.call_id,
        workload="teacher.sketch-deck.generate",
        elapsed_seconds=result.elapsed_seconds,
    )
    return {
        "request_id": request_id,
        "modal_call_id": result.call_id,
        "model": {"id": QWEN_TEXT_MODEL_ID, "revision": QWEN_TEXT_MODEL_REVISION},
        "deck": deck,
        "elapsed_seconds": result.elapsed_seconds,
    }


@router.post("/lesson-plan-suggestions", summary="Suggest a structured lesson-plan draft")
def suggest_lesson_plan(
    organization_id: str,
    payload: TeacherLessonSuggestionRequestV1,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    require_assignment(db, principal, organization_id, roles={"teacher"})
    _require_modal_dev()
    request_id = str(uuid4())
    age_band = age_band_for_months(payload.target_age_months)
    if age_band is None:
        raise HTTPException(status_code=422, detail={"code": "INVALID_REQUEST"})
    worker_input = {
        "schema_version": "sketch2life.lesson-plan-suggest-input.v1",
        "topic": payload.topic,
        "target_age_band_ref": age_band[1],
        "target_age_band_version": 1,
        "target_age_months": payload.target_age_months,
        "objectives": payload.objectives,
        "drawing_subject": payload.drawing_subject,
        "activity_count": payload.activity_count,
        "activity_kind": payload.activity_kind,
        "script_following_allowed": payload.script_following_allowed,
        "script_direction": payload.script_direction,
    }
    try:
        result = ModalJsonFunctionClient().invoke("lesson.plan.suggest", worker_input)
    except (ModalFunctionOutcomeUnknown, ModalFunctionExecutionFailed) as exc:
        raise _provider_error(exc, request_id=request_id, workload="lesson.plan.suggest") from None
    output = result.output
    if output.get("model") != {
        "id": QWEN_TEXT_MODEL_ID,
        "revision": QWEN_TEXT_MODEL_REVISION,
    }:
        raise HTTPException(status_code=502, detail={"code": "MODAL_MODEL_REVISION_MISMATCH"})
    model_result = output.get("result")
    content = model_result.get("content") if isinstance(model_result, dict) else None
    if not isinstance(content, dict):
        raise HTTPException(status_code=502, detail={"code": "MODAL_OUTPUT_CONTRACT_INVALID"})
    _LOGGER.info(
        "teacher_modal_request_completed",
        request_id=request_id,
        modal_call_id=result.call_id,
        workload="lesson.plan.suggest",
        elapsed_seconds=result.elapsed_seconds,
    )
    return {
        "request_id": request_id,
        "modal_call_id": result.call_id,
        "model": {
            "id": QWEN_TEXT_MODEL_ID,
            "revision": QWEN_TEXT_MODEL_REVISION,
        },
        "status": "DRAFT",
        "review_required": True,
        "suggestion": content,
    }


@router.post("/sketch-decks", summary="Generate a sketch deck from Teacher-reviewed fields")
def generate_sketch_deck(
    organization_id: str,
    payload: TeacherReviewedPlanRequestV1,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    require_assignment(db, principal, organization_id, roles={"teacher"})
    _require_modal_dev()
    request_id = str(uuid4())
    plan_without_hash: dict[str, object] = {
        "schema_version": "sketch2life.teacher-deck-input.v1",
        "plan_revision_ref": payload.plan_revision_ref,
        "topic": payload.topic,
        "target_age_months": payload.target_age_months,
        "objectives": payload.objectives,
        "drawing_steps": [
            {
                "step_index": index,
                "action": step.action,
                "placement": step.placement,
            }
            for index, step in enumerate(payload.drawing_steps, start=1)
        ],
        "subject_knowledge": payload.subject_knowledge,
        "activities": [
            {
                "activity_ref": activity.activity_ref,
                "title": activity.title,
                "goal": _bounded_text_segments(activity.goal),
                "materials": _bounded_text_segments(activity.materials),
                "preparation": _bounded_text_segments(activity.preparation),
                "instructions": _bounded_text_segments(activity.instructions),
                "safety_notes": _bounded_text_segments(activity.safety_notes),
            }
            for activity in payload.activities
        ],
    }
    worker_input = {
        **plan_without_hash,
        "content_hash": hashlib.sha256(
            json.dumps(
                plan_without_hash,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest(),
    }
    try:
        result = ModalJsonFunctionClient().invoke("teacher.sketch-deck.generate", worker_input)
    except (ModalFunctionOutcomeUnknown, ModalFunctionExecutionFailed) as exc:
        raise _provider_error(
            exc, request_id=request_id, workload="teacher.sketch-deck.generate"
        ) from None
    deck = result.output.get("result")
    if (
        result.output.get("model")
        != {"id": QWEN_TEXT_MODEL_ID, "revision": QWEN_TEXT_MODEL_REVISION}
        or not isinstance(deck, dict)
        or deck.get("review_required") is not True
    ):
        raise HTTPException(status_code=502, detail={"code": "MODAL_OUTPUT_CONTRACT_INVALID"})
    _LOGGER.info(
        "teacher_modal_request_completed",
        request_id=request_id,
        modal_call_id=result.call_id,
        workload="teacher.sketch-deck.generate",
        elapsed_seconds=result.elapsed_seconds,
    )
    return {
        "request_id": request_id,
        "modal_call_id": result.call_id,
        "model": {
            "id": QWEN_TEXT_MODEL_ID,
            "revision": QWEN_TEXT_MODEL_REVISION,
        },
        "status": "DRAFT",
        "deck": deck,
    }


@router.post("/lesson-visuals", summary="Generate a visual candidate from a reviewed lesson plan")
def generate_lesson_visual(
    organization_id: str,
    payload: TeacherReviewedPlanRequestV1,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    require_assignment(db, principal, organization_id, roles={"teacher"})
    _require_modal_dev()
    request_id = str(uuid4())
    visual_without_hash: dict[str, object] = {
        "schema_version": "sketch2life.lesson-visual-input.v1",
        "plan_revision_ref": payload.plan_revision_ref,
        "topic": payload.topic,
        "steps": [
            {
                "step_index": index,
                "instruction": step.action,
                "placement": step.placement,
            }
            for index, step in enumerate(payload.drawing_steps, start=1)
        ],
    }
    worker_input = {
        **visual_without_hash,
        "content_hash": hashlib.sha256(
            json.dumps(
                visual_without_hash,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest(),
    }
    try:
        result = ModalJsonFunctionClient().invoke("lesson.visual.generate", worker_input)
    except (ModalFunctionOutcomeUnknown, ModalFunctionExecutionFailed) as exc:
        raise _provider_error(
            exc, request_id=request_id, workload="lesson.visual.generate"
        ) from None
    output = result.output
    if output.get("model") != _LESSON_VISUAL_MODEL_PROVENANCE:
        raise HTTPException(status_code=502, detail={"code": "MODAL_MODEL_REVISION_MISMATCH"})
    asset = output.get("asset")
    if not isinstance(asset, dict) or not isinstance(asset.get("bytes"), bytes):
        raise HTTPException(status_code=502, detail={"code": "MODAL_OUTPUT_CONTRACT_INVALID"})
    asset_bytes = asset["bytes"]
    asset_metadata = {key: value for key, value in asset.items() if key != "bytes"}
    _LOGGER.info(
        "teacher_modal_request_completed",
        request_id=request_id,
        modal_call_id=result.call_id,
        workload="lesson.visual.generate",
        elapsed_seconds=result.elapsed_seconds,
    )
    return {
        "request_id": request_id,
        "modal_call_id": result.call_id,
        "model": output.get("model"),
        "status": "DRAFT",
        "review_required": True,
        "asset": asset_metadata,
        "image_base64": base64.b64encode(asset_bytes).decode("ascii"),
    }


__all__ = ["router"]
