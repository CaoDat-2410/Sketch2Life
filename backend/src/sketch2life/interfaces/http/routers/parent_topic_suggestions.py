"""Authenticated catalog-first Parent topic and drawing-subject APIs."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, Query
from structlog import get_logger
from sqlalchemy.orm import Session

from sketch2life.application.services.parent_topic_suggestions import ParentTopicSuggestionService
from sketch2life.contracts.schemas.parent_topic_suggestions import (
    ParentCustomSubjectValidationRequestV1,
    ParentCustomSubjectValidationV1,
    ParentDrawingSubjectSuggestionSetV1,
    ParentTopicSuggestionSetV1,
)
from sketch2life.resources.parent_topic_catalog_vi_v2 import CATALOG_REVISION, TOPICS
from sketch2life.infrastructure.ai.modal_function_client import (
    MODEL_ID,
    MODEL_REVISION,
    ModalFunctionExecutionFailed,
    ModalFunctionOutcomeUnknown,
    ModalJsonFunctionClient,
)
from sketch2life.infrastructure.ai.modal_qwen_warm_up import QwenWarmUp
from sketch2life.infrastructure.config.settings import get_settings
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.infrastructure.persistence.parent_topic_rotation_repository import (
    SqlParentTopicRotationRepository,
)
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.application.ports.identity import VerifiedPrincipal

router = APIRouter(prefix="/api/parent/v1", tags=["Parent topic suggestions v1"])
_LOGGER = get_logger(__name__)
_QWEN_WARM_UP = QwenWarmUp()
_PRIVATE_TOPIC_PATTERNS = (
    re.compile(r"\b[^\s@]+@[^\s@]+\.[A-Za-z]{2,}\b"),
    re.compile(r"(?<!\d)(?:\+?\d[\d .()\-]{7,}\d)(?!\d)"),
    re.compile(r"\b(?:https?://|www\.)\S+", re.IGNORECASE),
    re.compile(r"\b(?:con tôi|bé nhà tôi|tên của bé|tên con tôi|my child|my daughter|my son)\b", re.IGNORECASE),
)


def _require_parent(db: Session, principal: VerifiedPrincipal) -> str:
    identity = db.get(AdultIdentityModel, principal.subject)
    if (
        identity is None
        or identity.state != "active"
        or identity.account_role != "parent"
        or identity.issuer != principal.issuer
    ):
        raise HTTPException(status_code=403, detail={"code": "PARENT_ROLE_REQUIRED"})
    try:
        return str(UUID(identity.account_id))
    except (ValueError, TypeError):
        raise HTTPException(status_code=403, detail={"code": "PARENT_ACCOUNT_REFERENCE_INVALID"}) from None


def _rotation_fingerprint(
    *,
    draft_id: UUID,
    rotation_kind: str,
    scope_id: str,
    catalog_revision: str,
    excluded_set_ids: list[str],
    excluded_subjects: tuple[str, ...] = (),
) -> str:
    def canonical_labels(values: tuple[str, ...] | list[str]) -> list[str]:
        normalized = {
            " ".join(unicodedata.normalize("NFKC", value).split()).casefold()
            for value in values
        }
        return sorted(normalized)

    body = {
        "draft_id": str(draft_id),
        "rotation_kind": rotation_kind,
        "scope_id": scope_id,
        "catalog_revision": catalog_revision,
        "excluded_set_ids": canonical_labels(excluded_set_ids),
        "excluded_subjects": canonical_labels(excluded_subjects),
    }
    canonical = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_excluded_set_ids(values: list[str], *, prefix: str) -> None:
    pattern = re.compile(rf"^{re.escape(prefix)}_[0-9a-f]{{24}}$")
    if any(pattern.fullmatch(value) is None for value in values):
        raise HTTPException(
            status_code=422,
            detail={"code": "PARENT_TOPIC_EXCLUDED_SET_INVALID"},
        )


def _translate_error(exc: ValueError) -> HTTPException:
    code = str(exc)
    status_code = (
        409
        if code in {
            "SUGGESTION_SET_UNAVAILABLE",
            "PARENT_TOPIC_ROTATION_IDEMPOTENCY_CONFLICT",
        }
        else 422
    )
    return HTTPException(status_code=status_code, detail={"code": code})


def _require_topic_ai() -> None:
    settings = get_settings()
    if (
        settings.env not in {"local", "test"}
        or settings.ai_provider != "modal_dev"
        or not settings.parent_topic_subject_ai_enabled
    ):
        raise HTTPException(
            status_code=503,
            detail={
                "code": "PARENT_TOPIC_SUBJECT_AI_NOT_ENABLED",
                "message": "Chủ đề riêng cần có tên đối tượng do người lớn nhập rồi mới kiểm tra được.",
            },
        )


def _validate_topic_for_ai(topic: str, excluded_subjects: list[str]) -> None:
    if any(
        pattern.search(value)
        for value in (topic, *excluded_subjects)
        for pattern in _PRIVATE_TOPIC_PATTERNS
    ):
        raise HTTPException(
            status_code=422,
            detail={
                "code": "PARENT_TOPIC_TEXT_NOT_ALLOWED",
                "message": "Chỉ nhập tên chủ đề hoặc đồ vật chung; không nhập tên, thông tin liên hệ hay dữ liệu riêng của trẻ.",
            },
        )


def _invoke_topic_subject_worker(
    *, workload: str, request_data: dict[str, Any], request_id: str
) -> dict[str, object]:
    try:
        result = ModalJsonFunctionClient().invoke(workload, request_data)
    except (ModalFunctionOutcomeUnknown, ModalFunctionExecutionFailed) as exc:
        if isinstance(exc, ModalFunctionOutcomeUnknown):
            _LOGGER.warning(
                "parent_topic_subject_modal_outcome_unknown",
                request_id=request_id,
                workload=workload,
                modal_call_id=exc.call_id,
            )
            raise HTTPException(
                status_code=504,
                detail={"code": "PARENT_TOPIC_SUBJECT_AI_OUTCOME_UNKNOWN", "request_id": request_id},
            ) from None
        _LOGGER.warning(
            "parent_topic_subject_modal_failed",
            request_id=request_id,
            workload=workload,
            error_code=exc.code,
        )
        raise HTTPException(
            status_code=502,
            detail={"code": exc.code, "request_id": request_id},
        ) from None
    output = result.output
    model = output.get("model")
    payload = output.get("result")
    if (
        model != {"id": MODEL_ID, "revision": MODEL_REVISION}
        or not isinstance(payload, dict)
    ):
        _LOGGER.warning(
            "parent_topic_subject_modal_contract_invalid",
            request_id=request_id,
            workload=workload,
            modal_call_id=result.call_id,
            elapsed_seconds=result.elapsed_seconds,
        )
        raise HTTPException(
            status_code=502,
            detail={"code": "PARENT_TOPIC_SUBJECT_AI_OUTPUT_INVALID", "request_id": request_id},
        )
    _LOGGER.info(
        "parent_topic_subject_modal_completed",
        request_id=request_id,
        workload=workload,
        modal_call_id=result.call_id,
        elapsed_seconds=result.elapsed_seconds,
    )
    return payload


@router.get(
    "/topics/suggestions",
    response_model=ParentTopicSuggestionSetV1,
    summary="Return three stable topic cards for a Parent drawing draft",
)
def get_topic_suggestions(
    draft_id: UUID,
    request_id: UUID,
    background: BackgroundTasks,
    exclude_set_ids: Annotated[list[str], Query(max_length=16)] = [],
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    account_id = _require_parent(db, principal)
    if get_settings().ai_provider == "modal_dev":
        # The drawing is analysed a minute or two from now; start the model while the parent chooses.
        background.add_task(_QWEN_WARM_UP.request)
    _validate_excluded_set_ids(exclude_set_ids, prefix="pts")
    try:
        service = ParentTopicSuggestionService()
        allocation = SqlParentTopicRotationRepository(db).allocate(
            account_id=account_id,
            request_id=request_id,
            draft_id=draft_id,
            rotation_kind="TOPIC",
            scope_id="all-topics",
            catalog_revision=CATALOG_REVISION,
            candidate_ids=tuple(row["topic_id"] for row in TOPICS),
            request_fingerprint=_rotation_fingerprint(
                draft_id=draft_id,
                rotation_kind="TOPIC",
                scope_id="all-topics",
                catalog_revision=CATALOG_REVISION,
                excluded_set_ids=exclude_set_ids,
            ),
        )
        result = service.topic_set(
            draft_id=draft_id,
            request_id=request_id,
            selected_topic_ids=allocation.selected_ids,
            set_id=allocation.set_id,
            excluded_set_ids=tuple(exclude_set_ids),
        )
        db.commit()
        return result
    except ValueError as exc:
        raise _translate_error(exc) from None


@router.get(
    "/topics/{topic_id}/drawing-subject-suggestions",
    response_model=ParentDrawingSubjectSuggestionSetV1,
    summary="Return three drawable subjects from the selected topic catalog",
)
def get_drawing_subject_suggestions(
    topic_id: Annotated[str, Path(min_length=2, max_length=48, pattern=r"^[a-z0-9-]+$")],
    draft_id: UUID,
    request_id: UUID,
    topic: Annotated[str, Query(min_length=2, max_length=120)],
    exclude_set_ids: Annotated[list[str], Query(max_length=16)] = [],
    exclude_subjects: Annotated[list[str], Query(max_length=24)] = [],
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    account_id = _require_parent(db, principal)
    _validate_excluded_set_ids(exclude_set_ids, prefix="pds")
    service = ParentTopicSuggestionService()
    try:
        category_id = service.resolve_topic(topic_id=topic_id, topic=topic)
        if category_id is None and service.is_catalog_topic_id(topic_id):
            raise HTTPException(
                status_code=422,
                detail={"code": "PARENT_TOPIC_ID_LABEL_MISMATCH"},
            )
        if any(not 2 <= len(subject.strip()) <= 80 for subject in exclude_subjects):
            raise HTTPException(
                status_code=422,
                detail={"code": "PARENT_TOPIC_EXCLUDED_SUBJECT_INVALID"},
            )
        if category_id is None:
            result = service.drawing_subject_set(
                draft_id=draft_id,
                request_id=request_id,
                topic_id=topic_id,
                topic=topic,
                excluded_set_ids=tuple(exclude_set_ids),
            )
            return result
        subject_ids = service.catalog_subject_ids(category_id)
        allocation = SqlParentTopicRotationRepository(db).allocate(
            account_id=account_id,
            request_id=request_id,
            draft_id=draft_id,
            rotation_kind="SUBJECT",
            scope_id=category_id,
            catalog_revision=CATALOG_REVISION,
            candidate_ids=subject_ids,
            request_fingerprint=_rotation_fingerprint(
                draft_id=draft_id,
                rotation_kind="SUBJECT",
                scope_id=category_id,
                catalog_revision=CATALOG_REVISION,
                excluded_set_ids=exclude_set_ids,
                excluded_subjects=tuple(exclude_subjects),
            ),
        )
        result = service.drawing_subject_set(
            draft_id=draft_id,
            request_id=request_id,
            topic_id=topic_id,
            topic=topic,
            selected_subject_ids=allocation.selected_ids,
            set_id=allocation.set_id,
            excluded_set_ids=tuple(exclude_set_ids),
        )
        db.commit()
        return result
    except HTTPException:
        raise
    except ValueError as exc:
        raise _translate_error(exc) from None


@router.post(
    "/topics/custom-subject-validation",
    response_model=ParentCustomSubjectValidationV1,
    summary="Check whether an adult-entered drawing subject fits the selected topic",
)
def validate_custom_subject(
    payload: ParentCustomSubjectValidationRequestV1,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    _require_parent(db, principal)
    service = ParentTopicSuggestionService()
    category_id = service.resolve_topic(topic_id=payload.topic_id, topic=payload.topic)
    if category_id is None and service.is_catalog_topic_id(payload.topic_id):
        raise HTTPException(status_code=422, detail={"code": "PARENT_TOPIC_ID_LABEL_MISMATCH"})
    if category_id is not None:
        deterministic = service.validate_custom_subject(
            topic_id=payload.topic_id,
            topic=payload.topic,
            subject=payload.subject,
        )
        if deterministic["decision"] != "NEEDS_CLARIFICATION":
            return deterministic

    _require_topic_ai()
    _validate_topic_for_ai(payload.topic, [payload.subject])
    request_id = str(uuid4())
    worker_result = _invoke_topic_subject_worker(
        workload="parent.topic-subjects.validate",
        request_data={
            "schema_version": "sketch2life.parent-topic-subject-validation-input.v1",
            "topic": payload.topic,
            "subject": payload.subject,
        },
        request_id=request_id,
    )
    if (
        set(worker_result) != {"schema_version", "decision"}
        or worker_result.get("schema_version") != "sketch2life.parent-topic-subject-validation.v1"
        or not isinstance(worker_result.get("decision"), str)
        or worker_result.get("decision") not in {"ON_TOPIC", "OUT_OF_TOPIC", "NEEDS_CLARIFICATION"}
    ):
        _LOGGER.warning(
            "parent_topic_subject_validation_modal_output_rejected",
            request_id=request_id,
            workload="parent.topic-subjects.validate",
        )
        raise HTTPException(
            status_code=502,
            detail={"code": "PARENT_TOPIC_SUBJECT_AI_OUTPUT_INVALID", "request_id": request_id},
        )
    decision = worker_result["decision"]
    messages = {
        "ON_TOPIC": "Đối tượng có vẻ phù hợp với chủ đề đã nhập.",
        "OUT_OF_TOPIC": "Đối tượng chưa khớp với chủ đề. Hãy chọn một trong ba gợi ý hoặc sửa chủ đề/đối tượng.",
        "NEEDS_CLARIFICATION": "Chưa xác định chắc đối tượng có thuộc chủ đề không. Hãy chọn một trong ba thẻ hoặc sửa nội dung nhập.",
    }
    return ParentCustomSubjectValidationV1(
        contract="ParentCustomSubjectValidationV1",
        decision=decision,
        normalized_subject=payload.subject if decision == "ON_TOPIC" else None,
        message_vi=messages[decision],
    ).model_dump(mode="json")


__all__ = ["router"]
