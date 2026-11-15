"""Authenticated Parent AI routes with server-owned StoryRun context and private assets."""

# ruff: noqa: B008

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
import unicodedata
from io import BytesIO
from math import isfinite
from uuid import UUID, uuid4
import xml.etree.ElementTree as ET

from fastapi import APIRouter, Depends, HTTPException, Request
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
from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
from sketch2life.application.ports.parent_activity_suggestion_store import (
    ParentActivitySuggestionStorePort,
)
from sketch2life.application.services.parent_activity_suggestions import (
    ParentActivitySuggestionError,
    ParentActivitySuggestionService,
)
from sketch2life.application.services.parent_story_runs import (
    ParentStoryRunService,
    ParentStoryRunServiceError,
)
from sketch2life.contracts.schemas.ai_story import (
    StoryRevisionDraftV1,
    validate_butterfly_lifecycle_v1,
)
from sketch2life.contracts.schemas.modal_ai import (
    ParentActivitySuggestionRequestV1,
    ParentActivitySuggestionResponseV2,
    ParentDrawingAnalysisRequestV1,
    ParentStoryRequestV1,
)
from sketch2life.contracts.schemas.parent_story_runs import ParentStoryRunResponseV1
from sketch2life.contracts.schemas.svg_engine import (
    SvgDocumentV1,
    SvgModelProvenanceV1,
    SvgReferenceIllustrationDocumentV1,
    SvgReferenceSourceProvenanceV1,
    SvgTopicStrokeGuideDerivationV1,
    SvgTopicStrokeGuideDraftResponseV1,
    SvgTopicStrokeGuideConstructionDraftResponseV1,
    SvgTopicStrokeGuideConstructionDerivationV1,
    SvgTopicStrokeGuideConstructionModelResultV1,
    SvgTopicStrokeGuideConstructionPathLineageV1,
    SvgTopicStrokeGuideModelResultV1,
    SvgTopicStrokeGuidePathLineageV1,
    SvgTopicStrokeGuideRequestV1,
    SvgTopicStrokeGuideSourceDraftResponseV1,
    SvgTopicStrokeGuideV1,
)
from sketch2life.domain.svg_engine import (
    ARCADIA_GALLUS_REFERENCE_SOURCE_V1,
    SvgRuleError,
    topic_uses_arcadia_gallus_reference,
    validate_construction_topic_stroke_guide_v1,
    validate_source_bound_topic_stroke_guide_v1,
    validate_topic_stroke_guide_v1,
)
from sketch2life.infrastructure.ai.modal_function_client import (
    MODEL_ID,
    MODEL_REVISION,
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
from sketch2life.infrastructure.lesson_library.parent_activity_catalog import (
    LessonLibraryParentActivityCatalogAdapter,
)
from sketch2life.infrastructure.lesson_library.service import LessonLibraryService
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
)
from sketch2life.infrastructure.svg.arcadia_gallus_guide import (
    ArcadiaDerivedGuideUnavailable,
    arcadia_source_pack_installed,
    build_arcadia_gallus_guide,
)
from sketch2life.infrastructure.svg.openclipart_guide import (
    OpenclipartGuideUnavailable,
    build_openclipart_guide,
)
from sketch2life.infrastructure.svg.openmoji_guide import (
    OpenMojiGuideUnavailable,
    build_openmoji_guide,
)
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.routers.lesson_library import get_lesson_library_service
from sketch2life.infrastructure.svg.sanitizer import (
    SvgInputRejected,
    canonical_json_bytes,
    sanitize_svg_source,
)

router = APIRouter(prefix="/api/parent/v1/ai", tags=["Parent AI v1"])
_LOGGER = get_logger(__name__)
_STORY_PROMPT_VERSION = "parent-story-v3-primary-activity.2026-11-13"


def _normalized_subject_terms(value: str) -> set[str]:
    folded = unicodedata.normalize("NFKD", value.casefold())
    plain = "".join(char for char in folded if not unicodedata.combining(char))
    ignored = {"con", "cai", "loai", "vong", "doi", "cua", "ve", "chu", "de", "tim", "hieu", "quan", "sat"}
    return {term for term in re.findall(r"[a-z0-9]+", plain) if term not in ignored}


def _subject_matches_context(candidate: str, context: str) -> bool:
    candidate_terms = _normalized_subject_terms(candidate)
    context_terms = _normalized_subject_terms(context)
    if not candidate_terms or not context_terms:
        return False
    overlap = len(candidate_terms & context_terms)
    return overlap / len(candidate_terms) >= 0.6 and overlap / len(context_terms) >= 0.45


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


@router.post(
    "/story-runs/{run_id}/activity-suggestions",
    response_model=ParentActivitySuggestionResponseV2,
    summary="Select Parent-accessible lesson activities or create quality-gated drafts",
)
def suggest_parent_activities(
    run_id: UUID,
    payload: ParentActivitySuggestionRequestV1,
    request: Request,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
    lesson_library: LessonLibraryService = Depends(get_lesson_library_service),
) -> ParentActivitySuggestionResponseV2:
    _require_parent(db, principal)
    request_id = str(uuid4())
    policy_version = _policy_version()
    try:
        run = _story_service(db).get_run(
            owner_subject=principal.subject,
            policy_version=policy_version,
            run_id=str(run_id),
        )
    except ParentStoryRunError as exc:
        raise HTTPException(status_code=exc.status_code, detail={"code": exc.code}) from None
    if (
        run.run_state != "PREPARATION_REVIEW"
        or run.understanding_revision != payload.expected_understanding_revision
        or not run.subject_label
        or run.candidate is None
    ):
        raise HTTPException(
            status_code=409,
            detail={"code": "PARENT_SUBJECT_CONFIRMATION_REQUIRED"},
        )

    _require_modal_dev()
    visible_features = run.candidate.get("visible_features")
    if not isinstance(visible_features, list) or not visible_features:
        raise HTTPException(
            status_code=409,
            detail={"code": "PARENT_VISIBLE_FEATURES_UNAVAILABLE"},
        )
    suggestion_service = ParentActivitySuggestionService(
        LessonLibraryParentActivityCatalogAdapter(lesson_library),
        soft_quality_gate_enabled=request.app.state.be1_runtime.settings.parent_activity_soft_quality_gate_enabled,
    )
    try:
        prepared = suggestion_service.prepare(
            parent_principal_ref=principal.subject,
            context_snapshot=run.context_snapshot,
            subject_label=run.subject_label,
            visible_features=visible_features,
            pinned_lesson_snapshot=run.lesson_pin_snapshot,
        )
    except ParentActivitySuggestionError as exc:
        status_code = 409 if exc.code.startswith("PARENT_") else 502
        raise HTTPException(status_code=status_code, detail={"code": exc.code}) from None
    try:
        result = ModalJsonFunctionClient().invoke(
            "parent.activity.suggest", prepared.worker_input
        )
    except (ModalFunctionOutcomeUnknown, ModalFunctionExecutionFailed) as exc:
        raise _provider_error(
            exc, request_id=request_id, workload="parent.activity.suggest"
        ) from None
    output = result.output
    if output.get("workload") != "parent.activity.suggest":
        raise HTTPException(status_code=502, detail={"code": "MODAL_OUTPUT_CONTRACT_INVALID"})
    raw_result = output.get("result")
    if (
        not isinstance(raw_result, dict)
        or raw_result.get("schema_version")
        != "sketch2life.parent-activity-suggestions.v2"
    ):
        raise HTTPException(status_code=502, detail={"code": "MODAL_OUTPUT_CONTRACT_INVALID"})
    try:
        response = suggestion_service.resolve(
            prepared=prepared,
            raw_result=raw_result,
            request_id=request_id,
            story_run_id=str(run_id),
            understanding_revision=payload.expected_understanding_revision,
            modal_call_id=result.call_id,
        )
        response_model = ParentActivitySuggestionResponseV2.model_validate(response)
    except (ParentActivitySuggestionError, TypeError, ValidationError) as exc:
        code = (
            exc.code
            if isinstance(exc, ParentActivitySuggestionError)
            else "MODAL_OUTPUT_CONTRACT_INVALID"
        )
        _LOGGER.warning(
            "parent_activity_output_rejected",
            request_id=request_id,
            error_code=code,
            quality_gate_reason=(
                exc.diagnostic_code
                if isinstance(exc, ParentActivitySuggestionError)
                else None
            ),
        )
        raise HTTPException(status_code=502, detail={"code": code}) from None
    store: ParentActivitySuggestionStorePort = request.app.state.parent_activity_suggestion_store
    try:
        store.record_response(
            owner_subject=principal.subject,
            story_run_id=str(run_id),
            understanding_revision=payload.expected_understanding_revision,
            request_id=str(response_model.request_id),
            activities=[activity.model_dump(mode="json") for activity in response_model.activities],
        )
    except (TypeError, ValueError):
        _LOGGER.exception(
            "parent_activity_snapshot_store_failed",
            request_id=request_id,
            story_run_id=str(run_id),
        )
        raise HTTPException(status_code=503, detail={"code": "PARENT_ACTIVITY_SNAPSHOT_UNAVAILABLE"}) from None
    _LOGGER.info(
        "parent_activity_suggestions_completed",
        request_id=request_id,
        modal_call_id=result.call_id,
        workload="parent.activity.suggest",
        elapsed_seconds=result.elapsed_seconds,
        selection_mode=response_model.selection_mode,
        catalog_candidate_count=response_model.catalog_candidate_count,
        activity_count=len(response_model.activities),
        soft_quality_gate_enabled=request.app.state.be1_runtime.settings.parent_activity_soft_quality_gate_enabled,
    )
    return response_model


@router.post(
    "/sketch-guides",
    summary="Generate an optional, private progressive SVG stroke-guide draft",
    response_model=(
        SvgTopicStrokeGuideDraftResponseV1
        | SvgTopicStrokeGuideSourceDraftResponseV1
        | SvgTopicStrokeGuideConstructionDraftResponseV1
    ),
)
def generate_sketch_guide(
    payload: SvgTopicStrokeGuideRequestV1,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> (
    SvgTopicStrokeGuideDraftResponseV1
    | SvgTopicStrokeGuideSourceDraftResponseV1
    | SvgTopicStrokeGuideConstructionDraftResponseV1
):
    _require_parent(db, principal)
    settings = get_settings()
    if not settings.svg_topic_stroke_guide_generation_enabled:
        raise HTTPException(
            status_code=503,
            detail={"code": "CAPABILITY_DISABLED"},
        )
    topic = payload.topic.strip()
    if any(
        pattern.search(topic)
        for pattern in (
            re.compile(r"\b[^\s@]+@[^\s@]+\.[A-Za-z]{2,}\b"),
            re.compile(r"\b(?:https?://|www\.)\S+", re.IGNORECASE),
            re.compile(r"(?<!\d)(?:\+?\d[\d .()\-]{7,}\d)(?!\d)"),
        )
    ):
        raise HTTPException(
            status_code=422,
            detail={"code": "PERSONAL_OR_REMOTE_REFERENCE_NOT_ALLOWED"},
        )
    request_id = str(uuid4())

    # Higher-detail, hash-pinned Openclipart pairs resolve before the simpler emoji pack.
    # The adapter receives the generic topic only; it never dispatches a Modal call.
    try:
        source_guide = build_openclipart_guide(topic)
    except (OpenclipartGuideUnavailable, ValidationError, SvgInputRejected, SvgRuleError, ValueError) as exc:
        reason_code = (
            exc.code
            if isinstance(exc, (SvgInputRejected, SvgRuleError))
            else str(exc)
            if str(exc).startswith("SVG_")
            else "SVG_OPENCLIPART_DERIVED_GUIDE_INVALID"
        )
        _LOGGER.error(
            "parent_svg_source_guide_rejected",
            request_id=request_id,
            workload="svg.topic-stroke-guide.derive.openclipart",
            reason_code=reason_code,
        )
        raise HTTPException(
            status_code=503,
            detail={"code": "CURATED_SVG_GUIDE_UNAVAILABLE", "reason_code": reason_code, "request_id": request_id},
        ) from None
    if source_guide is not None:
        try:
            generated = source_guide.generated
            document, document_sha256 = _canonicalize_openclipart_source_path_guide_svg(
                generated.document
            )
            guide = SvgTopicStrokeGuideV1(
                guide_id=request_id,
                title_vi=generated.title_vi,
                parts=generated.parts,
                stages=generated.stages,
            )
            derivation = SvgTopicStrokeGuideDerivationV1(
                engine_id=source_guide.engine_id,
                engine_revision=source_guide.engine_revision,
                source_guide_uri=source_guide.source_guide_uri,
                source_guide_sha256=source_guide.source_guide_sha256,
                method=source_guide.derivation_method,
                source_path_count=source_guide.source_path_count,
                path_lineage=[
                    SvgTopicStrokeGuidePathLineageV1.model_validate(item)
                    for item in source_guide.path_lineage
                ],
            )
        except (ValidationError, SvgInputRejected, SvgRuleError, ValueError) as exc:
            reason_code = (
                exc.code
                if isinstance(exc, (SvgInputRejected, SvgRuleError))
                else str(exc)
                if str(exc).startswith("SVG_")
                else "SVG_OPENCLIPART_DERIVED_GUIDE_INVALID"
            )
            _LOGGER.error(
                "parent_svg_source_guide_rejected",
                request_id=request_id,
                workload="svg.topic-stroke-guide.derive.openclipart",
                reason_code=reason_code,
            )
            raise HTTPException(
                status_code=503,
                detail={"code": "CURATED_SVG_GUIDE_UNAVAILABLE", "reason_code": reason_code, "request_id": request_id},
            ) from None
        _LOGGER.info(
            "parent_svg_source_guide_completed",
            request_id=request_id,
            workload="svg.topic-stroke-guide.derive.openclipart",
            source_sha256=source_guide.reference_source.source_sha256,
            asset_id=source_guide.reference_source.asset_id,
            path_count=len(document.paths),
            stage_count=len(guide.stages),
            document_sha256=document_sha256,
        )
        return SvgTopicStrokeGuideSourceDraftResponseV1(
            request_id=request_id,
            topic=topic,
            status="DRAFT",
            review_required=True,
            persisted=False,
            generation_source="CURATED_SOURCE_DERIVATION",
            derivation=derivation,
            reference_source=source_guide.reference_source,
            reference_illustration=source_guide.reference_illustration,
            document=document,
            document_sha256=document_sha256,
            guide=guide,
            path_count=len(document.paths),
            stage_count=len(guide.stages),
            quality_gates_passed=[
                "SVG_SANITIZER",
                "PINNED_SOURCE_PATH_SANITIZER",
                "LINE_ONLY_PATHS",
                "SOURCE_CONTOUR_SEQUENCE",
                "SOURCE_PATH_COVERAGE_EXACTLY_ONCE",
                "PROGRESSIVE_PATH_COVERAGE",
                "PINNED_OPENCLIPART_SOURCE_HASH",
                "MATCHED_COLOR_LINE_REFERENCE",
                "SOURCE_PATH_LINEAGE",
            ],
        )

    # Pinned, child-friendly OpenMoji drawings resolve locally before any AI fallback.
    # This path uses only the generic topic and never dispatches a Modal call.
    try:
        source_guide = build_openmoji_guide(topic)
    except (OpenMojiGuideUnavailable, ValidationError, SvgInputRejected, SvgRuleError, ValueError) as exc:
        reason_code = (
            exc.code
            if isinstance(exc, (SvgInputRejected, SvgRuleError))
            else str(exc)
            if str(exc).startswith("SVG_")
            else "SVG_OPENMOJI_DERIVED_GUIDE_INVALID"
        )
        _LOGGER.error(
            "parent_svg_source_guide_rejected",
            request_id=request_id,
            workload="svg.topic-stroke-guide.derive.openmoji",
            reason_code=reason_code,
        )
        raise HTTPException(
            status_code=503,
            detail={"code": "CURATED_SVG_GUIDE_UNAVAILABLE", "reason_code": reason_code, "request_id": request_id},
        ) from None
    if source_guide is not None:
        try:
            generated = source_guide.generated
            document, document_sha256 = _canonicalize_openmoji_source_path_guide_svg(
                generated.document
            )
            guide = SvgTopicStrokeGuideV1(
                guide_id=request_id,
                title_vi=generated.title_vi,
                parts=generated.parts,
                stages=generated.stages,
            )
            derivation = SvgTopicStrokeGuideDerivationV1(
                engine_id=source_guide.engine_id,
                engine_revision=source_guide.engine_revision,
                source_guide_uri=source_guide.source_guide_uri,
                source_guide_sha256=source_guide.source_guide_sha256,
                method=source_guide.derivation_method,
                source_path_count=source_guide.source_path_count,
                path_lineage=[
                    SvgTopicStrokeGuidePathLineageV1.model_validate(item)
                    for item in source_guide.path_lineage
                ],
            )
        except (ValidationError, SvgInputRejected, SvgRuleError, ValueError) as exc:
            reason_code = (
                exc.code
                if isinstance(exc, (SvgInputRejected, SvgRuleError))
                else str(exc)
                if str(exc).startswith("SVG_")
                else "SVG_OPENMOJI_DERIVED_GUIDE_INVALID"
            )
            _LOGGER.error(
                "parent_svg_source_guide_rejected",
                request_id=request_id,
                workload="svg.topic-stroke-guide.derive.openmoji",
                reason_code=reason_code,
            )
            raise HTTPException(
                status_code=503,
                detail={"code": "CURATED_SVG_GUIDE_UNAVAILABLE", "reason_code": reason_code, "request_id": request_id},
            ) from None
        _LOGGER.info(
            "parent_svg_source_guide_completed",
            request_id=request_id,
            workload="svg.topic-stroke-guide.derive.openmoji",
            source_sha256=source_guide.reference_source.source_sha256,
            asset_id=source_guide.reference_source.asset_id,
            path_count=len(document.paths),
            stage_count=len(guide.stages),
            document_sha256=document_sha256,
        )
        return SvgTopicStrokeGuideSourceDraftResponseV1(
            request_id=request_id,
            topic=topic,
            status="DRAFT",
            review_required=True,
            persisted=False,
            generation_source="CURATED_SOURCE_DERIVATION",
            derivation=derivation,
            reference_source=source_guide.reference_source,
            reference_illustration=source_guide.reference_illustration,
            document=document,
            document_sha256=document_sha256,
            guide=guide,
            path_count=len(document.paths),
            stage_count=len(guide.stages),
            quality_gates_passed=[
                "SVG_SANITIZER",
                "PINNED_SOURCE_PATH_SANITIZER",
                "LINE_ONLY_PATHS",
                "SOURCE_SHAPE_GEOMETRY_NORMALIZED",
                "SOURCE_PATH_COVERAGE_EXACTLY_ONCE",
                "PROGRESSIVE_PATH_COVERAGE",
                "PINNED_OPENMOJI_SOURCE_HASH",
                "PINNED_OPENMOJI_MANIFEST_HASH",
                "PAIRED_COLOR_LINE_GEOMETRY",
                "SOURCE_PATH_LINEAGE",
            ],
        )

    # A pinned Arcadia chicken source has a curated, deterministic derivation.
    # This branch must not call Modal or claim model/provider provenance.
    if topic_uses_arcadia_gallus_reference(topic) and arcadia_source_pack_installed():
        try:
            source_guide = build_arcadia_gallus_guide(topic)
            if source_guide is None:
                raise ArcadiaDerivedGuideUnavailable("SVG_ARCADIA_TOPIC_NOT_PINNED")
            generated = source_guide.generated
            document, document_sha256 = _canonicalize_arcadia_source_path_guide_svg(
                generated.document
            )
            guide = SvgTopicStrokeGuideV1(
                guide_id=request_id,
                title_vi=generated.title_vi,
                parts=generated.parts,
                stages=generated.stages,
            )
            derivation = SvgTopicStrokeGuideDerivationV1(
                engine_id=source_guide.engine_id,
                engine_revision=source_guide.engine_revision,
                method=source_guide.derivation_method,
                source_path_count=source_guide.source_path_count,
                path_lineage=[
                    SvgTopicStrokeGuidePathLineageV1.model_validate(item)
                    for item in source_guide.path_lineage
                ],
            )
        except (
            ArcadiaDerivedGuideUnavailable,
            ValidationError,
            SvgInputRejected,
            SvgRuleError,
            ValueError,
        ) as exc:
            reason_code = (
                str(exc)
                if isinstance(exc, (ArcadiaDerivedGuideUnavailable, ValueError))
                and str(exc).startswith("SVG_")
                else exc.code
                if isinstance(exc, (SvgInputRejected, SvgRuleError))
                else "SVG_ARCADIA_DERIVED_GUIDE_INVALID"
            )
            _LOGGER.error(
                "parent_svg_source_guide_rejected",
                request_id=request_id,
                workload="svg.topic-stroke-guide.derive.arcadia-gallus",
                reason_code=reason_code,
            )
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "CURATED_SVG_GUIDE_UNAVAILABLE",
                    "reason_code": reason_code,
                    "request_id": request_id,
                },
            ) from None

        _LOGGER.info(
            "parent_svg_source_guide_completed",
            request_id=request_id,
            workload="svg.topic-stroke-guide.derive.arcadia-gallus",
            source_sha256=source_guide.reference_source.source_sha256,
            path_count=len(document.paths),
            stage_count=len(guide.stages),
            document_sha256=document_sha256,
        )
        return SvgTopicStrokeGuideSourceDraftResponseV1(
            request_id=request_id,
            topic=topic,
            status="DRAFT",
            review_required=True,
            persisted=False,
            generation_source="CURATED_SOURCE_DERIVATION",
            derivation=derivation,
            reference_source=source_guide.reference_source,
            reference_illustration=source_guide.reference_illustration,
            document=document,
            document_sha256=document_sha256,
            guide=guide,
            path_count=len(document.paths),
            stage_count=len(guide.stages),
            quality_gates_passed=[
                "SVG_SANITIZER",
                "REFERENCE_ILLUSTRATION_SANITIZER",
                "LINE_ONLY_PATHS",
                "EXACT_SOURCE_PATH_GEOMETRY",
                "SOURCE_PATH_COVERAGE_EXACTLY_ONCE",
                "PROGRESSIVE_PATH_COVERAGE",
                "PINNED_ARCADIA_SOURCE_HASH",
                "PINNED_SEQUENCE_MANIFEST_HASH",
                "SOURCE_PATH_LINEAGE",
            ],
        )

    _require_modal_dev()
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
        raise HTTPException(status_code=502, detail={"code": "MODAL_MODEL_REVISION_MISMATCH", "request_id": request_id})
    reference_source = output.get("reference_source")
    if isinstance(reference_source, dict) and reference_source.get("dataset_name") == "Openclipart":
        try:
            source_provenance = SvgReferenceSourceProvenanceV1.model_validate(reference_source)
            if (
                source_provenance.license_id != "CC0-1.0"
                or source_provenance.license_uri != "https://creativecommons.org/publicdomain/zero/1.0/"
                or source_provenance.dataset_uri is None
                or re.match(r"^https://openclipart\.org/", str(source_provenance.dataset_uri)) is None
                or re.fullmatch(r"[0-9a-f]{40}", source_provenance.dataset_revision) is None
            ):
                raise ValueError("SVG_OPENCLIPART_SOURCE_PROVENANCE_INVALID")
            reference_illustration = _canonicalize_openclipart_reference_illustration(
                SvgReferenceIllustrationDocumentV1.model_validate(
                    output.get("reference_illustration")
                )
            )
            output_source_path_ids = output.get("source_path_ids")
            expected_source_path_ids = [path.path_id for path in reference_illustration.paths]
            if output_source_path_ids != expected_source_path_ids:
                raise ValueError("SVG_OPENCLIPART_SOURCE_PATH_IDS_MISMATCH")
            raw_generated = output.get("result")
            if (
                isinstance(raw_generated, dict)
                and raw_generated.get("schema_version")
                == "SvgTopicStrokeGuideConstructionContentV1"
            ):
                generated_construction = SvgTopicStrokeGuideConstructionModelResultV1.model_validate(
                    raw_generated
                )
                validated_construction = validate_construction_topic_stroke_guide_v1(
                    generated_construction.model_dump(mode="json"),
                    topic=topic,
                    source_path_ids=expected_source_path_ids,
                    source_path_geometries={
                        path.path_id: path.d for path in reference_illustration.paths
                    },
                )
                document, document_sha256 = _canonicalize_topic_stroke_guide_svg(
                    SvgDocumentV1.model_validate(validated_construction["document"])
                )
                guide = SvgTopicStrokeGuideV1(
                    guide_id=request_id,
                    title_vi=validated_construction["title_vi"],
                    parts=validated_construction["parts"],
                    stages=validated_construction["stages"],
                )
                derivation = SvgTopicStrokeGuideConstructionDerivationV1(
                    engine_id="qwen-reference-conditioned-construction",
                    engine_revision=f"{MODEL_ID}@{MODEL_REVISION}",
                    method="QWEN_REFERENCE_CONDITIONED_CONSTRUCTION_V1",
                    source_path_count=len(reference_illustration.paths),
                    path_lineage=[
                        SvgTopicStrokeGuideConstructionPathLineageV1.model_validate(item)
                        for item in validated_construction["path_lineage"]
                    ],
                )
                _LOGGER.info(
                    "parent_svg_construction_guide_completed",
                    request_id=request_id,
                    modal_call_id=result.call_id,
                    workload="svg.topic-stroke-guide.generate",
                    source_asset_id=source_provenance.asset_id,
                    source_sha256=source_provenance.source_sha256,
                    dataset_revision=source_provenance.dataset_revision,
                    elapsed_seconds=result.elapsed_seconds,
                    path_count=len(document.paths),
                    stage_count=len(guide.stages),
                    source_anchor_count=len({
                        source_id
                        for item in derivation.path_lineage
                        for source_id in item.source_path_ids
                    }),
                    document_sha256=document_sha256,
                )
                return SvgTopicStrokeGuideConstructionDraftResponseV1(
                    request_id=request_id,
                    topic=topic,
                    status="DRAFT",
                    review_required=True,
                    persisted=False,
                    generation_source="QWEN_REFERENCE_CONDITIONED_CONSTRUCTION",
                    model=SvgModelProvenanceV1(id=MODEL_ID, revision=MODEL_REVISION),
                    modal_call_id=result.call_id,
                    derivation=derivation,
                    reference_source=source_provenance,
                    reference_illustration=reference_illustration,
                    document=document,
                    document_sha256=document_sha256,
                    guide=guide,
                    path_count=len(document.paths),
                    stage_count=len(guide.stages),
                    quality_gates_passed=[
                        "OPENCLIPART_CC0_PROVENANCE",
                        "SAFE_REFERENCE_SVG_SANITIZER",
                        "SAFE_CONSTRUCTION_PATH_SUBSET",
                        "CONSTRUCTION_FIRST_STEP_ONLY",
                        "CONSTRUCTION_STROKES_ANCHORED_TO_SOURCE",
                        "PROGRESSIVE_STROKE_ASSIGNMENT_EXACTLY_ONCE",
                        "FINAL_RECOGNITION_FEATURE",
                        "SOURCE_COLOR_ARTWORK_SEPARATE",
                        "PRIVATE_ADULT_REVIEW_DRAFT",
                    ],
                )
            generated = SvgTopicStrokeGuideModelResultV1.model_validate(raw_generated)
            document, document_sha256 = _canonicalize_openclipart_source_path_guide_svg(
                generated.document
            )
            if (
                [path.path_id for path in document.paths]
                != [path.path_id for path in reference_illustration.paths]
                or [path.d for path in document.paths]
                != [path.d for path in reference_illustration.paths]
            ):
                raise ValueError("SVG_OPENCLIPART_SOURCE_GEOMETRY_MISMATCH")
            content = generated.model_dump(mode="json")
            content["document"] = document.model_dump(mode="json")
            validated = validate_source_bound_topic_stroke_guide_v1(content, topic=topic)
            guide = SvgTopicStrokeGuideV1(
                guide_id=request_id,
                title_vi=generated.title_vi,
                parts=validated["parts"],
                stages=validated["stages"],
            )
            feature_by_path = {
                path_id: part["label_vi"]
                for part in validated["parts"]
                for path_id in part["path_ids"]
            }
            path_lineage = [
                SvgTopicStrokeGuidePathLineageV1(
                    derived_path_id=path.path_id,
                    source_path_ids=[path.path_id],
                    feature_vi=feature_by_path[path.path_id],
                    operation="QWEN_OPENCLIPART_SOURCE_PATH_SEQUENCE_V1",
                )
                for path in document.paths
            ]
            derivation = SvgTopicStrokeGuideDerivationV1(
                engine_id="qwen-openclipart-source-path-order",
                engine_revision=f"{MODEL_ID}@{MODEL_REVISION}",
                source_guide_uri=source_provenance.dataset_uri,
                source_guide_sha256=source_provenance.source_sha256,
                method="QWEN_OPENCLIPART_SOURCE_PATH_SEQUENCE_V1",
                source_path_count=len(reference_illustration.paths),
                path_lineage=path_lineage,
            )
        except (ValidationError, SvgInputRejected, SvgRuleError, ValueError, KeyError, TypeError) as exc:
            reason_code = (
                exc.code
                if isinstance(exc, (SvgInputRejected, SvgRuleError))
                else str(exc)
                if isinstance(exc, ValueError) and str(exc).startswith("SVG_")
                else "MODAL_SVG_SOURCE_GUIDE_OUTPUT_INVALID"
            )
            _LOGGER.warning(
                "parent_svg_catalog_source_guide_rejected",
                request_id=request_id,
                modal_call_id=result.call_id,
                workload="svg.topic-stroke-guide.generate",
                source_sha256=reference_source.get("source_sha256"),
                reason_code=reason_code,
            )
            raise HTTPException(
                status_code=502,
                detail={"code": "MODAL_SVG_SOURCE_GUIDE_OUTPUT_REJECTED", "reason_code": reason_code, "request_id": request_id},
            ) from None
        _LOGGER.info(
            "parent_svg_catalog_source_guide_completed",
            request_id=request_id,
            modal_call_id=result.call_id,
            workload="svg.topic-stroke-guide.generate",
            source_asset_id=source_provenance.asset_id,
            source_sha256=source_provenance.source_sha256,
            dataset_revision=source_provenance.dataset_revision,
            elapsed_seconds=result.elapsed_seconds,
            path_count=len(document.paths),
            stage_count=len(guide.stages),
            document_sha256=document_sha256,
        )
        return SvgTopicStrokeGuideSourceDraftResponseV1(
            request_id=request_id,
            topic=topic,
            status="DRAFT",
            review_required=True,
            persisted=False,
            generation_source="QWEN_SOURCE_PATH_DERIVATION",
            model=SvgModelProvenanceV1(id=MODEL_ID, revision=MODEL_REVISION),
            modal_call_id=result.call_id,
            derivation=derivation,
            reference_source=source_provenance,
            reference_illustration=reference_illustration,
            document=document,
            document_sha256=document_sha256,
            guide=guide,
            path_count=len(document.paths),
            stage_count=len(guide.stages),
            quality_gates_passed=[
                "SVG_CATALOG_READ_ONLY_VOLUME",
                "OPENCLIPART_CC0_PROVENANCE",
                "SAFE_SVG_SOURCE_SUBSET",
                "EXACT_SOURCE_PATH_GEOMETRY",
                "SOURCE_PATH_IDS_COVERED_EXACTLY_ONCE",
                "ADAPTIVE_4_TO_8_STAGES",
                "MATCHING_COLOR_SOURCE_GEOMETRY",
                "PRIVATE_REVIEW_REQUIRED_DRAFT",
            ],
        )
    uses_curated_reference = topic_uses_arcadia_gallus_reference(topic)
    if (
        (uses_curated_reference and reference_source != ARCADIA_GALLUS_REFERENCE_SOURCE_V1)
        or (not uses_curated_reference and reference_source is not None)
    ):
        raise HTTPException(
            status_code=502,
            detail={"code": "MODAL_SVG_REFERENCE_PROVENANCE_MISMATCH", "request_id": request_id},
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
            "parent_svg_topic_guide_output_rejected",
            request_id=request_id,
            modal_call_id=result.call_id,
            workload="svg.topic-stroke-guide.generate",
            reason_code=reason_code,
        )
        raise HTTPException(
            status_code=502,
            detail={"code": "MODAL_SVG_TOPIC_GUIDE_OUTPUT_REJECTED", "reason_code": reason_code, "request_id": request_id},
        ) from None
    _LOGGER.info(
        "parent_svg_topic_guide_completed",
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


def _canonicalize_arcadia_source_path_guide_svg(
    document: SvgDocumentV1,
) -> tuple[SvgDocumentV1, str]:
    """Sanitize the exact pinned-source paths without applying AI geometry gates."""
    if document.view_box != "0 0 252 252" or len(document.paths) != 77:
        raise ValueError("SVG_ARCADIA_SOURCE_GUIDE_DOCUMENT_INVALID")
    root = ET.Element(
        "svg",
        {"xmlns": "http://www.w3.org/2000/svg", "viewBox": document.view_box},
    )
    for path in document.paths:
        if path.fill != "none" or path.stroke != "#221f1f":
            raise ValueError("SVG_ARCADIA_SOURCE_GUIDE_STYLE_INVALID")
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
    sanitized_paths = sanitized.document.get("paths")
    if (
        not isinstance(sanitized_paths, list)
        or len(sanitized_paths) != len(document.paths)
        or any(
            clean.get("path_id") != original.path_id
            or clean.get("d") != original.d
            or clean.get("fill") != "none"
            or clean.get("stroke") != "#221f1f"
            or clean.get("stroke_width") != original.stroke_width
            for clean, original in zip(sanitized_paths, document.paths, strict=True)
        )
    ):
        raise ValueError("SVG_ARCADIA_SOURCE_GUIDE_SANITIZER_MISMATCH")
    canonical = SvgDocumentV1.model_validate(sanitized.document)
    digest = hashlib.sha256(
        canonical_json_bytes(canonical.model_dump(mode="json"))
    ).hexdigest()
    return canonical, digest


def _canonicalize_openmoji_source_path_guide_svg(
    document: SvgDocumentV1,
) -> tuple[SvgDocumentV1, str]:
    """Re-run the safe SVG parser and preserve the pinned OpenMoji path inventory."""
    if document.view_box != "0 0 72 72" or not 4 <= len(document.paths) <= 32:
        raise ValueError("SVG_OPENMOJI_SOURCE_GUIDE_DOCUMENT_INVALID")
    root = ET.Element(
        "svg",
        {"xmlns": "http://www.w3.org/2000/svg", "viewBox": document.view_box},
    )
    for path in document.paths:
        if path.fill != "none" or path.stroke not in {"#000000", "#20293b"}:
            raise ValueError("SVG_OPENMOJI_SOURCE_GUIDE_STYLE_INVALID")
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
    sanitized_paths = sanitized.document.get("paths")
    if (
        not isinstance(sanitized_paths, list)
        or len(sanitized_paths) != len(document.paths)
        or any(
            clean.get("path_id") != original.path_id
            or clean.get("d") != original.d
            or clean.get("fill") != "none"
            or clean.get("stroke") != original.stroke
            or clean.get("stroke_width") != original.stroke_width
            for clean, original in zip(sanitized_paths, document.paths, strict=True)
        )
    ):
        raise ValueError("SVG_OPENMOJI_SOURCE_GUIDE_SANITIZER_MISMATCH")
    canonical = SvgDocumentV1.model_validate(sanitized.document)
    digest = hashlib.sha256(
        canonical_json_bytes(canonical.model_dump(mode="json"))
    ).hexdigest()
    return canonical, digest


def _canonicalize_openclipart_source_path_guide_svg(
    document: SvgDocumentV1,
) -> tuple[SvgDocumentV1, str]:
    """Sanitize and retain every path in a pinned Openclipart guide."""
    if not 4 <= len(document.paths) <= 32:
        raise ValueError("SVG_OPENCLIPART_SOURCE_GUIDE_DOCUMENT_INVALID")
    root = ET.Element(
        "svg",
        {"xmlns": "http://www.w3.org/2000/svg", "viewBox": document.view_box},
    )
    for path in document.paths:
        if path.fill != "none" or path.stroke != "#20293b":
            raise ValueError("SVG_OPENCLIPART_SOURCE_GUIDE_STYLE_INVALID")
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
    paths = sanitized.document.get("paths")
    if (
        not isinstance(paths, list)
        or len(paths) != len(document.paths)
        or any(
            clean.get("path_id") != original.path_id
            or clean.get("fill") != "none"
            or clean.get("stroke") != original.stroke
            or clean.get("stroke_width") != original.stroke_width
            for clean, original in zip(paths, document.paths, strict=True)
        )
    ):
        raise ValueError("SVG_OPENCLIPART_SOURCE_GUIDE_SANITIZER_MISMATCH")
    canonical = SvgDocumentV1.model_validate(sanitized.document)
    digest = hashlib.sha256(canonical_json_bytes(canonical.model_dump(mode="json"))).hexdigest()
    return canonical, digest


def _canonicalize_openclipart_reference_illustration(
    document: SvgReferenceIllustrationDocumentV1,
) -> SvgReferenceIllustrationDocumentV1:
    """Sanitize a path-only color source while preserving IDs and rendered geometry."""
    if not 4 <= len(document.paths) <= 32:
        raise ValueError("SVG_OPENCLIPART_REFERENCE_PATH_COUNT_INVALID")
    root = ET.Element(
        "svg",
        {"xmlns": "http://www.w3.org/2000/svg", "viewBox": document.view_box},
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
    sanitized_paths = sanitized.document.get("paths")
    if (
        not isinstance(sanitized_paths, list)
        or len(sanitized_paths) != len(document.paths)
        or any(
            cleaned.get("path_id") != original.path_id
            for cleaned, original in zip(sanitized_paths, document.paths, strict=True)
        )
    ):
        raise ValueError("SVG_OPENCLIPART_REFERENCE_SANITIZER_MISMATCH")
    paths = [
        {
            **cleaned,
            "stroke_linecap": original.stroke_linecap,
            "stroke_linejoin": original.stroke_linejoin,
            "stroke_miterlimit": original.stroke_miterlimit,
        }
        for cleaned, original in zip(sanitized_paths, document.paths, strict=True)
    ]
    return SvgReferenceIllustrationDocumentV1.model_validate(
        {
            "schema_version": "SvgReferenceIllustrationV1",
            "view_box": document.view_box,
            "paths": paths,
        }
    )


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
    try:
        run_context = repository.get_run(
            owner_subject=principal.subject,
            policy_version=policy_version,
            run_id=run_id,
        )
    except ParentStoryRunError as exc:
        raise HTTPException(status_code=exc.status_code, detail={"code": exc.code}) from None
    if current.input_revision != payload.expected_input_revision:
        raise HTTPException(status_code=409, detail={"code": "PARENT_STORY_INPUT_REVISION_STALE"})
    if payload.replace_existing:
        if current.original_asset_ref is None:
            raise HTTPException(status_code=409, detail={"code": "PARENT_STORY_RETAKE_NOT_ALLOWED"})
    elif current.original_asset_ref is not None:
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
            replace_existing=payload.replace_existing,
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
        "topic_match": (
            "NO_SELECTED_TOPIC"
            if not (run_context.lesson_pin_snapshot or {}).get("drawing_subject")
            and not str(run_context.context_snapshot.get("topic") or "").strip()
            else "MATCH"
            if _subject_matches_context(
                candidate_subject,
                str(
                    (run_context.lesson_pin_snapshot or {}).get("drawing_subject")
                    or run_context.context_snapshot.get("topic")
                    or ""
                ),
            )
            else "MISMATCH"
        ),
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
        "artwork_retake_available": current.input_revision + 1 == 2,
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
    request: Request,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    _require_parent(db, principal)
    _require_modal_dev()
    policy_version = _policy_version()
    request_id = str(uuid4())
    store: ParentActivitySuggestionStorePort = request.app.state.parent_activity_suggestion_store
    if payload.rewrite_instruction is None:
        primary_activity = store.select_primary(
            owner_subject=principal.subject,
            story_run_id=str(run_id),
            understanding_revision=payload.expected_understanding_revision,
            request_id=str(payload.primary_activity_request_id),
            activity_ref=str(payload.primary_activity_ref),
        )
    else:
        primary_activity = store.get_selected_primary(
            owner_subject=principal.subject,
            story_run_id=str(run_id),
            understanding_revision=payload.expected_understanding_revision,
        )
    if primary_activity is None:
        raise HTTPException(
            status_code=409,
            detail={"code": "PARENT_PRIMARY_ACTIVITY_SELECTION_STALE_OR_INVALID", "request_id": request_id},
        )
    repository = SqlParentStoryRunRepository(db)
    service = ParentStoryRunService(repository)
    try:
        reservation = service.reserve_story_revision(
            owner_subject=principal.subject,
            policy_version=policy_version,
            run_id=str(run_id),
            expected_understanding_revision=payload.expected_understanding_revision,
            primary_activity=primary_activity,
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
        primary_activity_ref=reservation.worker_input["primary_activity"]["activity_ref"],
        primary_activity_sha256=reservation.worker_input["primary_activity_sha256"],
    )
    return {
        "request_id": request_id,
        "modal_call_id": modal_call_id,
        "story_run": _story_response(record),
        "story": record.story_content,
        "story_sha256": record.story_sha256,
        "primary_activity_ref": reservation.worker_input["primary_activity"]["activity_ref"],
        "primary_activity_sha256": reservation.worker_input["primary_activity_sha256"],
        "review_required": True,
        "model": {"id": STORY_MODEL_ID, "revision": STORY_MODEL_REVISION},
    }


__all__ = ["router"]
