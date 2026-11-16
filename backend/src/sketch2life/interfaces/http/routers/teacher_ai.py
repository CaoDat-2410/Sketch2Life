"""Teacher AI draft routes; only reviewed, structured lesson fields reach Modal."""

# ruff: noqa: B008

from __future__ import annotations

import base64
import hashlib
import json
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from structlog import get_logger

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.contracts.schemas.modal_ai import (
    TeacherLessonSuggestionRequestV1,
    TeacherReviewedPlanRequestV1,
)
from sketch2life.infrastructure.ai.modal_function_client import (
    FLUX_MODEL_PROVENANCE,
    MODEL_ID,
    MODEL_REVISION,
    ModalFunctionExecutionFailed,
    ModalFunctionOutcomeUnknown,
    ModalJsonFunctionClient,
)
from sketch2life.infrastructure.config.settings import get_settings
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    OrganizationAssignmentModel,
)
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult

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


def _require_teacher(
    db: Session, principal: VerifiedPrincipal, organization_id: str
) -> None:
    identity = db.get(AdultIdentityModel, principal.subject)
    assignment = db.scalar(
        select(OrganizationAssignmentModel.assignment_id).where(
            OrganizationAssignmentModel.subject == principal.subject,
            OrganizationAssignmentModel.organization_id == organization_id,
            OrganizationAssignmentModel.role == "teacher",
            OrganizationAssignmentModel.active.is_(True),
        )
    )
    if (
        identity is None
        or identity.state != "active"
        or identity.account_role != "teacher"
        or identity.issuer != principal.issuer
        or assignment is None
    ):
        raise HTTPException(
            status_code=403,
            detail={"code": "TEACHER_ORGANIZATION_ACCESS_REQUIRED"},
        )


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


@router.post("/lesson-plan-suggestions", summary="Suggest a structured lesson-plan draft")
def suggest_lesson_plan(
    organization_id: str,
    payload: TeacherLessonSuggestionRequestV1,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    _require_teacher(db, principal, organization_id)
    _require_modal_dev()
    request_id = str(uuid4())
    worker_input = {
        "schema_version": "sketch2life.lesson-plan-suggest-input.v1",
        "topic": payload.topic,
        "target_age_band_ref": "age-36-120-months-v1",
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
        raise _provider_error(
            exc, request_id=request_id, workload="lesson.plan.suggest"
        ) from None
    output = result.output
    if output.get("model") != {"id": MODEL_ID, "revision": MODEL_REVISION}:
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
        "model": {"id": MODEL_ID, "revision": MODEL_REVISION},
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
    _require_teacher(db, principal, organization_id)
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
        result.output.get("model") != {"id": MODEL_ID, "revision": MODEL_REVISION}
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
        "model": {"id": MODEL_ID, "revision": MODEL_REVISION},
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
    _require_teacher(db, principal, organization_id)
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
    if output.get("model") != FLUX_MODEL_PROVENANCE:
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
