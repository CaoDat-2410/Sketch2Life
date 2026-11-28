"""Modal-backed ``DrawingAnalyzerPort`` for Parent StoryRun drawings."""

from __future__ import annotations

import hashlib
import re
from math import isfinite
from typing import Any, NoReturn
from uuid import uuid4

from structlog import get_logger

from sketch2life.application.ports.object_storage import ObjectStoragePort
from sketch2life.application.ports.parent_story_inputs import (
    DRAWING_ANALYSIS_FAILED,
    DRAWING_ANALYSIS_UNAVAILABLE,
    DrawingAnalysisFailure,
    DrawingAnalysisOutcomeUnknown,
    DrawingAnalysisRequest,
    DrawingAnalysisResult,
)
from sketch2life.infrastructure.ai.modal_function_client import (
    ModalDrawingFunctionClient,
    ModalFunctionExecutionFailed,
    ModalFunctionOutcomeUnknown,
    prepare_drawing_input,
)

_LOGGER = get_logger(__name__)
_MAX_DRAWING_BYTES = 5_000_000
_READ_CHUNK_BYTES = 1024 * 1024
_SHA256 = re.compile(r"\A[0-9a-f]{64}\Z")


class ModalDrawingAnalyzer:
    def __init__(self, storage: ObjectStoragePort, client: ModalDrawingFunctionClient) -> None:
        self._storage = storage
        self._client = client

    def analyze(self, request: DrawingAnalysisRequest) -> DrawingAnalysisResult:
        source_bytes = self._read_drawing(request)
        try:
            prepared = prepare_drawing_input(
                source_bytes=source_bytes,
                source_media_type="image/png",
                expected_source_sha256=request.derived_sha256,
                job_id=str(uuid4()),
                generation_id=str(uuid4()),
                attempt_id=str(uuid4()),
            )
        except Exception as exc:  # noqa: BLE001 - invalid drawing input is recoverable
            self._raise_failure(DRAWING_ANALYSIS_FAILED, type(exc).__name__)

        try:
            worker_result = self._client.invoke(prepared)
        except ModalFunctionOutcomeUnknown as exc:
            _LOGGER.warning(
                "parent_drawing_modal_outcome_unknown",
                exception_type=type(exc).__name__,
                error_code="DRAWING_OUTCOME_UNKNOWN",
            )
            raise DrawingAnalysisOutcomeUnknown() from None
        except ModalFunctionExecutionFailed as exc:
            code = (
                DRAWING_ANALYSIS_UNAVAILABLE
                if exc.code == "PROVIDER_UNAVAILABLE"
                else DRAWING_ANALYSIS_FAILED
            )
            self._raise_failure(code, type(exc).__name__)
        except Exception as exc:  # noqa: BLE001 - client setup faults are recoverable
            self._raise_failure(DRAWING_ANALYSIS_UNAVAILABLE, type(exc).__name__)

        return self._map_answer(worker_result)

    def _read_drawing(self, request: DrawingAnalysisRequest) -> bytes:
        if (
            not isinstance(request.derived_asset_ref, str)
            or not request.derived_asset_ref
            or isinstance(request.derived_size_bytes, bool)
            or not isinstance(request.derived_size_bytes, int)
            or not 0 < request.derived_size_bytes <= _MAX_DRAWING_BYTES
            or not isinstance(request.derived_sha256, str)
            or _SHA256.fullmatch(request.derived_sha256) is None
        ):
            self._raise_failure(DRAWING_ANALYSIS_FAILED)

        try:
            stored = self._storage.get_object(request.derived_asset_ref)
        except Exception as exc:  # noqa: BLE001 - storage faults are recoverable
            self._raise_failure(DRAWING_ANALYSIS_UNAVAILABLE, type(exc).__name__)

        if (
            stored is None
            or isinstance(stored.content_length, bool)
            or stored.content_length != request.derived_size_bytes
            or not 0 < stored.content_length <= _MAX_DRAWING_BYTES
            or stored.content_type != "image/png"
        ):
            self._raise_failure(DRAWING_ANALYSIS_FAILED)

        chunks: list[bytes] = []
        total = 0
        try:
            while True:
                read_limit = min(_READ_CHUNK_BYTES, _MAX_DRAWING_BYTES + 1 - total)
                chunk = stored.body.read(read_limit)
                if not isinstance(chunk, bytes):
                    self._raise_failure(DRAWING_ANALYSIS_FAILED)
                if not chunk:
                    break
                total += len(chunk)
                if total > _MAX_DRAWING_BYTES:
                    self._raise_failure(DRAWING_ANALYSIS_FAILED)
                chunks.append(chunk)
        except DrawingAnalysisFailure:
            raise
        except Exception as exc:  # noqa: BLE001 - read faults are recoverable
            self._raise_failure(DRAWING_ANALYSIS_UNAVAILABLE, type(exc).__name__)
        finally:
            try:
                stored.body.close()
            except Exception as exc:  # noqa: BLE001 - close faults do not expose asset data
                _LOGGER.warning(
                    "parent_drawing_storage_close_failed",
                    exception_type=type(exc).__name__,
                    error_code=DRAWING_ANALYSIS_UNAVAILABLE,
                )

        source_bytes = b"".join(chunks)
        if (
            len(source_bytes) != request.derived_size_bytes
            or hashlib.sha256(source_bytes).hexdigest() != request.derived_sha256
        ):
            self._raise_failure(DRAWING_ANALYSIS_FAILED)
        return source_bytes

    def _map_answer(self, worker_result: Any) -> DrawingAnalysisResult:
        try:
            output = worker_result.output
        except Exception as exc:  # noqa: BLE001 - malformed client answers are recoverable
            self._raise_failure(DRAWING_ANALYSIS_FAILED, type(exc).__name__)

        candidate = output.get("result") if isinstance(output, dict) else None
        if (
            not isinstance(candidate, dict)
            or candidate.get("adult_confirmation_required") is not True
        ):
            self._raise_failure(DRAWING_ANALYSIS_FAILED)

        raw_subject = candidate.get("candidate_subject")
        subject = raw_subject.strip()[:160] if isinstance(raw_subject, str) else ""
        raw_features = candidate.get("visible_features")
        if not isinstance(raw_features, list):
            raw_features = []
        features = tuple(
            value.strip()[:160]
            for value in raw_features[:4]
            if isinstance(value, str) and value.strip()
        )
        confidence = candidate.get("confidence", 0.0)
        if (
            not features
            or isinstance(confidence, bool)
            or not isinstance(confidence, int | float)
            or not isfinite(float(confidence))
            or not 0 <= float(confidence) <= 1
        ):
            self._raise_failure(DRAWING_ANALYSIS_FAILED)

        # The worker cannot count children; this adapter reports the supported single-child case.
        return DrawingAnalysisResult(
            subject=subject,
            visible_features=features,
            confidence=float(confidence),
            child_count=1,
        )

    @staticmethod
    def _raise_failure(code: str, exception_type: str | None = None) -> NoReturn:
        fields: dict[str, str] = {"error_code": code}
        if exception_type is not None:
            fields["exception_type"] = exception_type
        _LOGGER.warning("parent_drawing_analysis_failed", **fields)
        raise DrawingAnalysisFailure(code) from None


__all__ = ["ModalDrawingAnalyzer"]
