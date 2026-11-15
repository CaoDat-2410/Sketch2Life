"""Teacher AI draft routes; only reviewed, structured lesson fields reach Modal."""

# ruff: noqa: B008

from __future__ import annotations

import base64
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session
from structlog import get_logger

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.contracts.schemas.modal_ai import (
    ProgressiveGuideLayoutV1,
    TeacherLessonSuggestionRequestV1,
    TeacherReviewedPlanRequestV1,
)
from sketch2life.contracts.schemas.svg_engine import (
    SvgDocumentV1,
    SvgIllustrationModelResultV1,
    TeacherSvgIllustrationDraftRequestV1,
    TeacherSvgIllustrationDraftResponseV1,
    SvgModelProvenanceV1,
    SvgReferenceSourceProvenanceV1,
    SvgTopicStrokeGuideDraftResponseV1,
    SvgTopicStrokeGuideModelResultV1,
    SvgTopicStrokeGuideRequestV1,
    SvgTopicStrokeGuideV1,
)
from sketch2life.domain.svg_engine import (
    ARCADIA_GALLUS_REFERENCE_SOURCE_V1,
    SvgRuleError,
    topic_uses_arcadia_gallus_reference,
    validate_topic_stroke_guide_v1,
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
from sketch2life.infrastructure.svg.sanitizer import (
    SvgInputRejected,
    canonical_json_bytes,
    sanitize_svg_source,
)
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
_TOPIC_EMAIL = re.compile(r"\b[^\s@]+@[^\s@]+\.[A-Za-z]{2,}\b")
_TOPIC_URL = re.compile(r"\b(?:https?://|www\.)\S+", re.IGNORECASE)
_TOPIC_PHONE = re.compile(r"(?<!\d)(?:\+?\d[\d .()\-]{7,}\d)(?!\d)")


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


def _canonicalize_generated_svg(document: SvgDocumentV1) -> tuple[SvgDocumentV1, str]:
    if not 4 <= len(document.paths) <= 20:
        raise ValueError("SVG_ILLUSTRATION_PATH_COUNT_INVALID")
    root = ET.Element(
        "svg",
        {
            "xmlns": "http://www.w3.org/2000/svg",
            "viewBox": document.view_box,
        },
    )
    for path in document.paths:
        ET.SubElement(
            root,
            "path",
            {
                "id": path.path_id,
                "d": path.d,
                "fill": path.fill,
                "stroke": path.stroke,
                "stroke-width": format(path.stroke_width, ".6g"),
            },
        )
    sanitized = sanitize_svg_source(ET.tostring(root, encoding="utf-8"))
    canonical_document = SvgDocumentV1.model_validate(sanitized.document)
    if not 4 <= len(canonical_document.paths) <= 20:
        raise ValueError("SVG_ILLUSTRATION_PATH_COUNT_INVALID")
    digest = hashlib.sha256(canonical_json_bytes(canonical_document.model_dump(mode="json"))).hexdigest()
    return canonical_document, digest


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
    try:
        panel_layout = ProgressiveGuideLayoutV1.model_validate(output.get("panel_layout"))
        if panel_layout.step_count != len(payload.drawing_steps):
            raise ValueError("step count mismatch")
    except (ValidationError, ValueError):
        raise HTTPException(status_code=502, detail={"code": "MODAL_PROGRESSIVE_GUIDE_CONTRACT_INVALID"}) from None
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
        "panel_layout": panel_layout.model_dump(mode="json"),
        "image_base64": base64.b64encode(asset_bytes).decode("ascii"),
    }


@router.post(
    "/svg-illustrations",
    summary="Generate a validated, non-persisted Teacher SVG illustration draft",
    response_model=TeacherSvgIllustrationDraftResponseV1,
)
def generate_svg_illustration_draft(
    organization_id: str,
    payload: TeacherSvgIllustrationDraftRequestV1,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> TeacherSvgIllustrationDraftResponseV1:
    _require_teacher(db, principal, organization_id)
    _require_modal_dev()
    settings = get_settings()
    if not settings.svg_illustration_generation_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "CAPABILITY_DISABLED"},
        )
    if any(
        pattern.search(payload.topic)
        for pattern in (_TOPIC_EMAIL, _TOPIC_URL, _TOPIC_PHONE)
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "PERSONAL_OR_REMOTE_REFERENCE_NOT_ALLOWED"},
        )

    request_id = str(uuid4())
    worker_input = {
        "schema_version": "sketch2life.teacher-svg-illustration-input.v1",
        "topic": payload.topic.strip(),
        "target_age_months": payload.target_age_months,
        "visual_style": payload.visual_style,
    }
    try:
        result = ModalJsonFunctionClient().invoke(
            "teacher.svg-illustration.generate", worker_input
        )
    except (ModalFunctionOutcomeUnknown, ModalFunctionExecutionFailed) as exc:
        raise _provider_error(
            exc, request_id=request_id, workload="teacher.svg-illustration.generate"
        ) from None

    output = result.output
    if output.get("model") != {"id": MODEL_ID, "revision": MODEL_REVISION}:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "MODAL_MODEL_REVISION_MISMATCH", "request_id": request_id},
        )
    reference_source = output.get("reference_source")
    uses_curated_reference = topic_uses_arcadia_gallus_reference(topic)
    if (
        (uses_curated_reference and reference_source != ARCADIA_GALLUS_REFERENCE_SOURCE_V1)
        or (not uses_curated_reference and reference_source is not None)
    ):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": "MODAL_SVG_REFERENCE_PROVENANCE_MISMATCH",
                "request_id": request_id,
            },
        )
    try:
        generated = SvgIllustrationModelResultV1.model_validate(output.get("result"))
        document, document_sha256 = _canonicalize_generated_svg(generated.document)
    except (ValidationError, SvgInputRejected, ValueError) as exc:
        reason_code = (
            exc.code
            if isinstance(exc, SvgInputRejected)
            else str(exc)
            if isinstance(exc, ValueError) and str(exc).startswith("SVG_")
            else "MODAL_SVG_OUTPUT_INVALID"
        )
        _LOGGER.warning(
            "teacher_svg_illustration_output_rejected",
            request_id=request_id,
            modal_call_id=result.call_id,
            workload="teacher.svg-illustration.generate",
            reason_code=reason_code,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "MODAL_SVG_OUTPUT_REJECTED", "reason_code": reason_code, "request_id": request_id},
        ) from None

    _LOGGER.info(
        "teacher_modal_request_completed",
        request_id=request_id,
        modal_call_id=result.call_id,
        workload="teacher.svg-illustration.generate",
        elapsed_seconds=result.elapsed_seconds,
        path_count=len(document.paths),
        document_sha256=document_sha256,
    )
    return TeacherSvgIllustrationDraftResponseV1(
        request_id=request_id,
        modal_call_id=result.call_id,
        status="DRAFT",
        review_required=True,
        persisted=False,
        model={"id": MODEL_ID, "revision": MODEL_REVISION},
        title_vi=generated.title_vi,
        alt_text_vi=generated.alt_text_vi,
        document=document,
        document_sha256=document_sha256,
        path_count=len(document.paths),
    )


@router.post(
    "/svg-stroke-guides",
    summary="Generate a validated, non-persisted Teacher SVG stroke-guide draft",
    response_model=SvgTopicStrokeGuideDraftResponseV1,
)
def generate_svg_stroke_guide_draft(
    organization_id: str,
    payload: SvgTopicStrokeGuideRequestV1,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> SvgTopicStrokeGuideDraftResponseV1:
    _require_teacher(db, principal, organization_id)
    _require_modal_dev()
    settings = get_settings()
    if not settings.svg_topic_stroke_guide_generation_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "CAPABILITY_DISABLED"},
        )
    topic = payload.topic.strip()
    if any(pattern.search(topic) for pattern in (_TOPIC_EMAIL, _TOPIC_URL, _TOPIC_PHONE)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "PERSONAL_OR_REMOTE_REFERENCE_NOT_ALLOWED"},
        )
    request_id = str(uuid4())
    try:
        result = ModalJsonFunctionClient().invoke(
            "svg.topic-stroke-guide.generate",
            {
                "schema_version": "sketch2life.svg-topic-stroke-guide-input.v1",
                "topic": topic,
                "difficulty": payload.difficulty,
            },
        )
    except (ModalFunctionOutcomeUnknown, ModalFunctionExecutionFailed) as exc:
        raise _provider_error(
            exc, request_id=request_id, workload="svg.topic-stroke-guide.generate"
        ) from None

    output = result.output
    if output.get("model") != {"id": MODEL_ID, "revision": MODEL_REVISION}:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "MODAL_MODEL_REVISION_MISMATCH", "request_id": request_id},
        )
    try:
        generated = SvgTopicStrokeGuideModelResultV1.model_validate(output.get("result"))
        document, document_sha256 = _canonicalize_topic_stroke_guide_svg(generated.document)
        content = generated.model_dump(mode="json")
        content["document"] = document.model_dump(mode="json")
        validated = validate_topic_stroke_guide_v1(content, topic=topic)
        guide = SvgTopicStrokeGuideV1(
            guide_id=request_id,
            title_vi=generated.title_vi,
            parts=validated["parts"],
            stages=validated["stages"],
        )
    except (ValidationError, SvgInputRejected, SvgRuleError, ValueError) as exc:
        reason_code = (
            exc.code
            if isinstance(exc, (SvgInputRejected, SvgRuleError))
            else str(exc)
            if isinstance(exc, ValueError) and str(exc).startswith("SVG_")
            else "MODAL_SVG_TOPIC_GUIDE_OUTPUT_INVALID"
        )
        _LOGGER.warning(
            "teacher_svg_topic_guide_output_rejected",
            request_id=request_id,
            modal_call_id=result.call_id,
            workload="svg.topic-stroke-guide.generate",
            reason_code=reason_code,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": "MODAL_SVG_TOPIC_GUIDE_OUTPUT_REJECTED",
                "reason_code": reason_code,
                "request_id": request_id,
            },
        ) from None

    _LOGGER.info(
        "teacher_svg_topic_guide_completed",
        request_id=request_id,
        modal_call_id=result.call_id,
        workload="svg.topic-stroke-guide.generate",
        elapsed_seconds=result.elapsed_seconds,
        path_count=len(document.paths),
        stage_count=len(guide.stages),
        document_sha256=document_sha256,
    )
    return SvgTopicStrokeGuideDraftResponseV1(
        request_id=request_id,
        modal_call_id=result.call_id,
        topic=topic,
        status="DRAFT",
        review_required=True,
        persisted=False,
        model=SvgModelProvenanceV1(id=MODEL_ID, revision=MODEL_REVISION),
        reference_source=(
            SvgReferenceSourceProvenanceV1.model_validate(reference_source)
            if reference_source is not None
            else None
        ),
        document=document,
        document_sha256=document_sha256,
        guide=guide,
        path_count=len(document.paths),
        stage_count=len(guide.stages),
        quality_gates_passed=[
            "SVG_SANITIZER",
            "LINE_ONLY_PATHS",
            "PROGRESSIVE_PATH_COVERAGE",
            "TOPIC_ANATOMY_TOPOLOGY",
            "CURATED_SVG_REFERENCE",
            "CHICKEN_ANATOMY_TOPOLOGY",
        ],
    )


def _canonicalize_topic_stroke_guide_svg(document: SvgDocumentV1) -> tuple[SvgDocumentV1, str]:
    if document.view_box != "0 0 512 512" or not 8 <= len(document.paths) <= 64:
        raise ValueError("SVG_TOPIC_GUIDE_DOCUMENT_INVALID")
    root = ET.Element("svg", {"xmlns": "http://www.w3.org/2000/svg", "viewBox": document.view_box})
    for path in document.paths:
        ET.SubElement(
            root,
            "path",
            {
                "id": path.path_id,
                "d": path.d,
                "fill": path.fill,
                "stroke": path.stroke,
                "stroke-width": format(path.stroke_width, ".6g"),
            },
        )
    sanitized = sanitize_svg_source(ET.tostring(root, encoding="utf-8"))
    canonical = SvgDocumentV1.model_validate(sanitized.document)
    digest = hashlib.sha256(canonical_json_bytes(canonical.model_dump(mode="json"))).hexdigest()
    return canonical, digest


__all__ = ["router"]
