"""Session-volatile preference classification endpoint; raw text is never stored or logged."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse

from sketch2life.application.ports.child_preference_classifier import (
    ChildPreferenceClassifierPort,
)
from sketch2life.contracts.schemas.child_preference_classification import (
    ChildPreferenceClassificationFailureV1,
    ChildPreferenceClassificationRequestV1,
)
from sketch2life.infrastructure.ai.lightning_child_preference_classifier import (
    ChildPreferenceClassificationUnavailable,
)

router = APIRouter(prefix="/v1/profile", tags=["child-preferences"])
_LOGGER = logging.getLogger("sketch2life.child_preferences")


@router.post("/preferences/classify")
def classify_preferences(
    payload: ChildPreferenceClassificationRequestV1,
    request: Request,
    actor_ref: Annotated[str, Header(alias="X-Actor-Ref", min_length=1, max_length=160)],
) -> JSONResponse:
    if actor_ref != "demo:local":
        return _failure(
            request_id=payload.request_id,
            code="DEMO_ACTOR_INVALID",
            retryable=False,
            status_code=403,
            message="Không xác nhận được phiên người lớn. Hãy quay lại và thử lại.",
        )
    classifier: ChildPreferenceClassifierPort | None = getattr(
        request.app.state, "child_preference_classifier", None
    )
    if classifier is None:
        return _failure(
            request_id=payload.request_id,
            code="CLASSIFIER_UNAVAILABLE",
            retryable=False,
            status_code=503,
            message="Tạm thời chưa phân loại được sở thích. Bạn có thể bỏ qua bước này.",
        )
    try:
        result = classifier.classify(payload)
    except ChildPreferenceClassificationUnavailable as error:
        _LOGGER.warning(
            "preference_classification_failed request_id=%s code=%s retryable=%s",
            payload.request_id,
            error.code,
            error.retryable,
        )
        if error.code == "CLASSIFIER_ENDPOINT_UNAVAILABLE":
            status_code = 503
            message = (
                "Dịch vụ AI chưa có endpoint phân loại sở thích mới. "
                "Hãy cập nhật và khởi động lại dịch vụ AI, hoặc tiếp tục không cá nhân hóa."
            )
        elif error.code == "CLASSIFICATION_TIMEOUT":
            status_code = 504
            message = (
                "AI phân loại mất quá nhiều thời gian. "
                "Hãy thử lại hoặc tiếp tục không cá nhân hóa."
            )
        else:
            status_code = 502
            message = "Chưa phân loại được sở thích. Hãy thử lại hoặc tiếp tục không cá nhân hóa."
        return _failure(
            request_id=payload.request_id,
            code=error.code,
            retryable=error.retryable,
            status_code=status_code,
            message=message,
        )
    except Exception as error:
        # Provider/client failures must not escape as FastAPI's HTML 500 page.
        # Log only bounded metadata: exception messages may contain submitted
        # preference text or other provider details.
        _LOGGER.error(
            "preference_classification_failed request_id=%s "
            "code=CLASSIFIER_INTERNAL_ERROR error_type=%s",
            payload.request_id,
            type(error).__name__,
        )
        return _failure(
            request_id=payload.request_id,
            code="CLASSIFIER_INTERNAL_ERROR",
            retryable=False,
            status_code=500,
            message="Chưa thể xử lý sở thích lúc này. Bạn có thể bỏ qua và tiếp tục.",
        )
    _LOGGER.info("preference_classification_completed request_id=%s", payload.request_id)
    return JSONResponse(status_code=200, content=result.model_dump(mode="json"))


def _failure(
    *,
    request_id: str,
    code: str,
    retryable: bool,
    status_code: int,
    message: str,
) -> JSONResponse:
    result = ChildPreferenceClassificationFailureV1(
        request_id=request_id,
        failure={"code": code, "retryable": retryable, "safe_message": message},
    )
    return JSONResponse(status_code=status_code, content=result.model_dump(mode="json"))


__all__ = ["router"]
