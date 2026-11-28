"""Modal-backed structured vector drafter for Teacher presentation SVG drafts."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Protocol

from structlog import get_logger

from sketch2life.application.ports.presentation_svg import (
    PresentationSvgDrafterUnavailable,
    PresentationSvgDraftInput,
    PresentationSvgDraftOutput,
)
from sketch2life.domain.lesson_occurrences.presentation import validate_subject_text
from sketch2life.domain.lesson_occurrences.presentation_svg_shapes import (
    build_presentation_svg_source,
)
from sketch2life.infrastructure.ai.modal_function_client import (
    MODEL_ID,
    MODEL_REVISION,
    ModalFunctionExecutionFailed,
    ModalFunctionOutcomeUnknown,
    ModalJsonFunctionClient,
    ModalJsonFunctionResult,
)
from sketch2life.infrastructure.config.settings import Settings

WORKLOAD = "presentation.svg-draft.generate"
INPUT_SCHEMA = "sketch2life.presentation-svg-input.v1"
# A cold Qwen3.8 container needs about three minutes before it generates, so a 180 s wait answered
# PROVIDER_UNAVAILABLE while the worker was still generating. Other text workloads wait up to
# 1800 s.
SVG_DRAFT_WAIT_SECONDS = 900
_LOGGER = get_logger(__name__)


class _ModalJsonInvoker(Protocol):
    def invoke(self, workload: str, request_data: dict[str, Any]) -> ModalJsonFunctionResult: ...


class ModalPresentationSvgDrafter:
    """Invoke the L4 Qwen worker once and serialize only validated geometry."""

    def __init__(self, client: _ModalJsonInvoker | None = None) -> None:
        self._client = client

    def draft(self, request: PresentationSvgDraftInput) -> PresentationSvgDraftOutput:
        worker_input, input_hash = _worker_input(request)
        client = (
            self._client
            if self._client is not None
            else ModalJsonFunctionClient(timeout_seconds=SVG_DRAFT_WAIT_SECONDS)
        )
        try:
            result = client.invoke(WORKLOAD, worker_input)
        except (ModalFunctionOutcomeUnknown, TimeoutError):
            raise PresentationSvgDrafterUnavailable() from None
        except ModalFunctionExecutionFailed as exc:
            if exc.code == "PROVIDER_UNAVAILABLE":
                raise PresentationSvgDrafterUnavailable() from None
            raise

        expected_model = {"id": MODEL_ID, "revision": MODEL_REVISION}
        if not isinstance(result.output, dict) or result.output.get("model") != expected_model:
            raise ValueError("Modal model identity does not match the configured Qwen pin")
        draft = result.output.get("result")
        source = build_presentation_svg_source(draft)
        _LOGGER.info(
            "presentation_svg_modal_request_completed",
            modal_call_id=result.call_id,
            workload=WORKLOAD,
            input_hash=input_hash,
            elapsed_seconds=result.elapsed_seconds,
        )
        return PresentationSvgDraftOutput(
            source=source,
            generator_name="qwen3.8-27b-fp8-modal",
            generator_version=MODEL_REVISION,
            license_id="CC0-1.0",
        )


def build_presentation_svg_drafter(settings: Settings) -> ModalPresentationSvgDrafter | None:
    # getattr keeps the gate fail-closed for partial settings objects used by composition tests.
    provider = getattr(settings, "ai_provider", None)
    env = getattr(settings, "env", None)
    if provider != "modal_dev" or env not in {"local", "test"}:
        return None
    return ModalPresentationSvgDrafter()


def _worker_input(request: PresentationSvgDraftInput) -> tuple[dict[str, Any], str]:
    if request.schema_version != INPUT_SCHEMA:
        raise ValueError("presentation SVG input schema is unsupported")
    if not isinstance(request.activity_title, str) or not 1 <= len(request.activity_title) <= 160:
        raise ValueError("presentation SVG activity title is invalid")
    validate_subject_text(request.subject_text)
    data: dict[str, Any] = {
        "schema_version": INPUT_SCHEMA,
        "activity_title": request.activity_title,
        "subject_text": request.subject_text,
    }
    content_hash = hashlib.sha256(
        json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {**data, "content_hash": content_hash}, content_hash


__all__ = ["ModalPresentationSvgDrafter", "build_presentation_svg_drafter"]
