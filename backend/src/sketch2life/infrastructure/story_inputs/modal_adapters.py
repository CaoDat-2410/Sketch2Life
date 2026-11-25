"""Modal-backed Parent adapters for the current StoryRun input and story ports.

These adapters are composed only for the synthetic local Modal profile. They keep provider calls
behind the application ports and verify storage lineage before sending drawing bytes to Modal.
"""

from __future__ import annotations

import hashlib
import logging
import re
from collections.abc import Mapping
from typing import Any
from uuid import uuid4

from sketch2life.application.ports.object_storage import ObjectStorageFailure, ObjectStoragePort
from sketch2life.application.ports.parent_story_inputs import (
    DRAWING_ANALYSIS_FAILED,
    STORY_GENERATION_UNAVAILABLE,
    DrawingAnalysisFailure,
    DrawingAnalysisOutcomeUnknown,
    DrawingAnalysisRequest,
    DrawingAnalysisResult,
    StoryGenerationFailure,
    StoryGenerationOutcomeUnknown,
    StoryGenerationResult,
)
from sketch2life.application.story_staging import split_story_staging
from sketch2life.infrastructure.ai.modal_function_client import (
    MODEL_ID,
    MODEL_REVISION,
    STORY_MODEL_ID,
    STORY_MODEL_REVISION,
    ModalDrawingFunctionClient,
    ModalFunctionDispatchRejected,
    ModalFunctionExecutionFailed,
    ModalFunctionOutcomeUnknown,
    ModalStoryFunctionClient,
    prepare_drawing_input,
)

_LOGGER = logging.getLogger("sketch2life.api")
_MAX_DRAWING_BYTES = 5_000_000
_MAX_READ_CHUNK = 64 * 1024
_ERROR_CODE = re.compile(r"\A[A-Z][A-Z0-9_]{0,63}\Z")


class ModalParentDrawingAnalyzer:
    """Read and hash-check the attached normalized drawing, then invoke Qwen on Modal once."""

    def __init__(
        self,
        storage: ObjectStoragePort,
        *,
        client: ModalDrawingFunctionClient | None = None,
    ) -> None:
        self._storage = storage
        self._client = client or ModalDrawingFunctionClient()

    def analyze(self, request: DrawingAnalysisRequest) -> DrawingAnalysisResult:
        source_bytes = self._read_verified_asset(request)
        try:
            prepared = prepare_drawing_input(
                source_bytes=source_bytes,
                source_media_type="image/png",
                expected_source_sha256=request.derived_sha256,
                job_id=str(uuid4()),
                generation_id=str(uuid4()),
                attempt_id=str(uuid4()),
            )
        except ValueError:
            raise DrawingAnalysisFailure("DRAWING_INPUT_INVALID") from None

        try:
            response = self._client.invoke(prepared)
        except ModalFunctionDispatchRejected as exc:
            code = exc.code if _ERROR_CODE.fullmatch(exc.code) else "MODAL_RESOURCE_EXHAUSTED"
            _LOGGER.warning(
                "parent_drawing_analysis_dispatch_rejected",
                extra={
                    "run_id": request.run_id,
                    "input_revision": request.input_revision,
                    "error_code": code,
                    "modal_call_id": None,
                },
            )
            raise DrawingAnalysisFailure("MODAL_DISPATCH_REJECTED") from None
        except ModalFunctionOutcomeUnknown as exc:
            _LOGGER.warning(
                "parent_drawing_analysis_outcome_unknown",
                extra={
                    "run_id": request.run_id,
                    "input_revision": request.input_revision,
                    "modal_call_id": exc.call_id,
                },
            )
            raise DrawingAnalysisOutcomeUnknown() from None
        except ModalFunctionExecutionFailed as exc:
            code = exc.code if _ERROR_CODE.fullmatch(exc.code) else DRAWING_ANALYSIS_FAILED
            _LOGGER.warning(
                "parent_drawing_analysis_terminal_failure",
                extra={
                    "run_id": request.run_id,
                    "input_revision": request.input_revision,
                    "error_code": code,
                },
            )
            raise DrawingAnalysisFailure(code) from None

        output = response.output
        model = output.get("model")
        candidate = output.get("result")
        payload = prepared.payload
        if (
            output.get("schema_version") != "sketch2life.modal.worker-output.v1"
            or output.get("workload") != "drawing.analyze"
            or output.get("job_id") != payload.get("job_id")
            or output.get("generation_id") != payload.get("generation_id")
            or output.get("attempt_id") != payload.get("attempt_id")
            or output.get("input_sha256") != prepared.drawing_sha256
            or not isinstance(model, dict)
            or model.get("id") != MODEL_ID
            or model.get("revision") != MODEL_REVISION
            or not isinstance(candidate, dict)
            or candidate.get("adult_confirmation_required") is not True
        ):
            raise DrawingAnalysisFailure(DRAWING_ANALYSIS_FAILED)

        subject = candidate.get("candidate_subject")
        features = candidate.get("visible_features")
        confidence = candidate.get("confidence")
        if (
            not isinstance(subject, str)
            or not subject.strip()
            or not isinstance(features, list)
            or not features
            or any(not isinstance(item, str) or not item.strip() for item in features)
            or isinstance(confidence, bool)
            or not isinstance(confidence, (int, float))
        ):
            raise DrawingAnalysisFailure(DRAWING_ANALYSIS_FAILED)

        result = DrawingAnalysisResult(
            subject=subject.strip()[:160],
            visible_features=tuple(item.strip()[:160] for item in features[:4]),
            confidence=float(confidence),
            topic_compatible=(
                candidate.get("topic_compatible")
                if isinstance(candidate.get("topic_compatible"), bool)
                else None
            ),
            raw_candidate={
                key: candidate[key]
                for key in (
                    "understanding_schema",
                    "candidate_subject",
                    "visible_features",
                    "confidence",
                    "main_subject",
                    "secondary_subjects",
                )
                if key in candidate
            },
        )
        _LOGGER.info(
            "parent_drawing_analysis_completed",
            extra={
                "run_id": request.run_id,
                "input_revision": request.input_revision,
                "modal_call_id": response.call_id,
                "model_id": MODEL_ID,
                "model_revision": MODEL_REVISION,
                "elapsed_seconds": response.elapsed_seconds,
                "output_sha256": response.output_sha256,
            },
        )
        return result

    def _read_verified_asset(self, request: DrawingAnalysisRequest) -> bytes:
        if (
            not isinstance(request.derived_asset_ref, str)
            or not request.derived_asset_ref
            or not isinstance(request.derived_sha256, str)
            or len(request.derived_sha256) != 64
            or isinstance(request.derived_size_bytes, bool)
            or not 1 <= request.derived_size_bytes <= _MAX_DRAWING_BYTES
        ):
            raise DrawingAnalysisFailure("DRAWING_INPUT_INVALID")
        try:
            stored = self._storage.get_object(request.derived_asset_ref)
        except ObjectStorageFailure:
            raise DrawingAnalysisFailure("STORAGE_UNAVAILABLE") from None
        if stored is None:
            raise DrawingAnalysisFailure("DRAWING_ASSET_NOT_FOUND")
        try:
            media_type = stored.content_type.split(";", 1)[0].strip().lower()
            if (
                media_type != "image/png"
                or stored.content_length != request.derived_size_bytes
                or stored.content_length > _MAX_DRAWING_BYTES
            ):
                raise DrawingAnalysisFailure("DRAWING_INPUT_INVALID")
            chunks: list[bytes] = []
            digest = hashlib.sha256()
            total = 0
            while total <= request.derived_size_bytes:
                remaining = request.derived_size_bytes + 1 - total
                chunk = stored.body.read(min(_MAX_READ_CHUNK, remaining))
                if not chunk:
                    break
                if not isinstance(chunk, bytes):
                    raise DrawingAnalysisFailure("DRAWING_INPUT_INVALID")
                total += len(chunk)
                if total > request.derived_size_bytes:
                    break
                chunks.append(chunk)
                digest.update(chunk)
        except ObjectStorageFailure:
            raise DrawingAnalysisFailure("STORAGE_UNAVAILABLE") from None
        finally:
            stored.body.close()
        if total != request.derived_size_bytes or digest.hexdigest() != request.derived_sha256:
            raise DrawingAnalysisFailure("DRAWING_INPUT_INVALID")
        return b"".join(chunks)


class ModalParentStoryGenerator:
    """Invoke the pinned Qwen story worker and separate its validated video staging metadata."""

    def __init__(self, *, client: ModalStoryFunctionClient | None = None) -> None:
        self._client = client or ModalStoryFunctionClient()

    def generate(self, worker_input: Mapping[str, Any]) -> StoryGenerationResult:
        if not isinstance(worker_input, Mapping):
            raise StoryGenerationFailure("STORY_INPUT_CONTRACT_INVALID")
        try:
            raw_story, call_id = self._client.generate({"worker_input": dict(worker_input)})
        except ModalFunctionOutcomeUnknown:
            raise StoryGenerationOutcomeUnknown() from None
        except ModalFunctionExecutionFailed as exc:
            code = exc.code if _ERROR_CODE.fullmatch(exc.code) else STORY_GENERATION_UNAVAILABLE
            raise StoryGenerationFailure(code) from None
        except ValueError:
            # ModalStoryFunctionClient validates the request before dispatching.
            raise StoryGenerationFailure("STORY_INPUT_CONTRACT_INVALID") from None

        scenes = raw_story.get("scenes") if isinstance(raw_story, dict) else None
        scene_count = len(scenes) if isinstance(scenes, list) else 0
        story, staging, staging_issue = split_story_staging(
            raw_story, dict(worker_input), scene_count=scene_count
        )
        _LOGGER.info(
            "parent_story_generation_completed",
            extra={
                "modal_call_id": call_id,
                "model_id": STORY_MODEL_ID,
                "model_revision": STORY_MODEL_REVISION,
                "scene_count": scene_count,
                "staging_state": "VALID" if staging is not None else staging_issue,
            },
        )
        return StoryGenerationResult(
            story=story,
            call_id=call_id,
            model_id=STORY_MODEL_ID,
            model_revision=STORY_MODEL_REVISION,
            staging=staging,
            staging_issue=staging_issue,
        )


__all__ = ["ModalParentDrawingAnalyzer", "ModalParentStoryGenerator"]
