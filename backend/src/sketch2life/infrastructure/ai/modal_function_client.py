"""Private Modal SDK adapter for the synthetic drawing-analysis pilot."""

from __future__ import annotations

import hashlib
import io
import re
import time
import uuid
from dataclasses import dataclass
from typing import Any

from structlog import get_logger

from sketch2life.domain.ai_jobs.completion import canonical_json

APP_NAME = "sketch2life-srs23-drawing-vlm-dev"
FUNCTION_NAME = "analyze-drawing"
ENVIRONMENT_NAME = "dev"
SCRATCH_VOLUME_NAME = "sketch2life-dev-job-scratch-v2"
DRAWING_INPUT_SCHEMA = "sketch2life.modal.drawing-input.v1"
STORY_INPUT_SCHEMA = "sketch2life.modal.ai-request.v1"
WORKER_INPUT_SCHEMA = "sketch2life.modal.worker-input.v1"
WORKER_OUTPUT_SCHEMA = "sketch2life.modal.worker-output.v1"
MODEL_ID = "Qwen/Qwen3.5-9B"
MODEL_REVISION = "c202236235762e1c871ad0ccb60c8ee5ba337b9a"
STORY_MODEL_ID = "Qwen/Qwen3.5-9B"
STORY_MODEL_REVISION = "c202236235762e1c871ad0ccb60c8ee5ba337b9a"
MAX_INPUT_BYTES = 48 * 1024 * 1024
MAX_MANIFEST_BYTES = 64 * 1024
MAX_IMAGE_PIXELS = 2_000_000
MAX_OUTPUT_BYTES = 256 * 1024
_OPAQUE_ID = re.compile(r"\A[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}\Z")
_SHA256 = re.compile(r"\A[0-9a-f]{64}\Z")

_LOGGER = get_logger(__name__)


class ModalFunctionOutcomeUnknown(RuntimeError):
    """The SDK call may have reached Modal; this run must not be dispatched again."""

    def __init__(self, call_id: str | None = None) -> None:
        self.call_id = call_id
        self.outcome_unknown = True
        super().__init__("MODAL_FUNCTION_OUTCOME_UNKNOWN")


class ModalFunctionExecutionFailed(RuntimeError):
    """The Modal function returned a terminal, classifiable failure."""

    def __init__(self, code: str) -> None:
        self.code = code
        self.outcome_unknown = False
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class PreparedDrawingInput:
    attempt_prefix: str
    drawing_png: bytes
    manifest: bytes
    manifest_sha256: str
    payload: dict[str, object]
    drawing_sha256: str


@dataclass(frozen=True, slots=True)
class ModalFunctionResult:
    output: dict[str, Any]
    call_id: str
    output_sha256: str
    elapsed_seconds: float


def _require_opaque_id(value: str) -> str:
    if not isinstance(value, str) or _OPAQUE_ID.fullmatch(value) is None:
        raise ValueError("Modal worker identity is invalid")
    return value


def prepare_drawing_input(
    *,
    source_bytes: bytes,
    source_media_type: str,
    expected_source_sha256: str,
    job_id: str,
    generation_id: str,
    attempt_id: str,
) -> PreparedDrawingInput:
    """Verify the admitted asset and create the exact PNG contract consumed by the worker."""

    job_id = _require_opaque_id(job_id)
    generation_id = _require_opaque_id(generation_id)
    attempt_id = _require_opaque_id(attempt_id)
    if (
        not isinstance(source_bytes, bytes)
        or not source_bytes
        or len(source_bytes) > 5_000_000
        or source_media_type not in {"image/jpeg", "image/png"}
        or not isinstance(expected_source_sha256, str)
        or _SHA256.fullmatch(expected_source_sha256) is None
        or hashlib.sha256(source_bytes).hexdigest() != expected_source_sha256
    ):
        raise ValueError("Modal drawing input is not admitted")

    try:
        from PIL import Image, UnidentifiedImageError

        with Image.open(io.BytesIO(source_bytes)) as opened:
            if (
                opened.format not in {"JPEG", "PNG"}
                or opened.width < 1
                or opened.height < 1
                or opened.width * opened.height > MAX_IMAGE_PIXELS
            ):
                raise ValueError("Modal drawing image is invalid")
            opened.verify()
        with Image.open(io.BytesIO(source_bytes)) as opened:
            drawing = opened.convert("RGB")
        output = io.BytesIO()
        drawing.save(output, format="PNG", optimize=True)
        drawing_png = output.getvalue()
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
        raise ValueError("Modal drawing image is invalid") from exc

    drawing_sha256 = hashlib.sha256(drawing_png).hexdigest()
    manifest = {
        "schema_version": DRAWING_INPUT_SCHEMA,
        "asset": {
            "path": "input/drawing.png",
            "content_type": "image/png",
            "size_bytes": len(drawing_png),
            "sha256": drawing_sha256,
        },
    }
    manifest_bytes = canonical_json(manifest).encode("utf-8")
    total_bytes = len(drawing_png) + len(manifest_bytes)
    if len(manifest_bytes) > MAX_MANIFEST_BYTES or total_bytes > MAX_INPUT_BYTES:
        raise ValueError("Modal drawing input exceeds the worker limit")

    attempt_prefix = f"sketch2life/{ENVIRONMENT_NAME}/{job_id}/{generation_id}/{attempt_id}/"
    payload: dict[str, object] = {
        "schema_version": WORKER_INPUT_SCHEMA,
        "environment": ENVIRONMENT_NAME,
        "workload": "drawing.analyze",
        "job_id": job_id,
        "generation_id": generation_id,
        "attempt_id": attempt_id,
        "attempt_prefix": attempt_prefix,
        "input_manifest_ref": "input/manifest.json",
        "input_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "input_bytes": total_bytes,
    }
    return PreparedDrawingInput(
        attempt_prefix=attempt_prefix,
        drawing_png=drawing_png,
        manifest=manifest_bytes,
        manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
        payload=payload,
        drawing_sha256=drawing_sha256,
    )


class ModalDrawingFunctionClient:
    """Stage one hash-bound PNG and invoke the private deployed drawing function once."""

    def __init__(
        self,
        *,
        volume: Any | None = None,
        function: Any | None = None,
        timeout_seconds: float = 1_800.0,
    ) -> None:
        if (volume is None) != (function is None):
            raise ValueError("Modal test doubles must supply both Volume and Function")
        if not 0 < timeout_seconds <= 1_800:
            raise ValueError("Modal function wait timeout is outside the approved bound")
        self._volume = volume
        self._function = function
        self._timeout = timeout_seconds

    def invoke(self, prepared: PreparedDrawingInput) -> ModalFunctionResult:
        volume = self._volume
        function = self._function
        if volume is None or function is None:
            import modal

            volume = modal.Volume.from_name(
                SCRATCH_VOLUME_NAME,
                environment_name=ENVIRONMENT_NAME,
                version=2,
            )
            function = modal.Function.from_name(
                APP_NAME,
                FUNCTION_NAME,
                environment_name=ENVIRONMENT_NAME,
            )

        call_id: str | None = None
        terminal = False
        started = time.perf_counter()
        try:
            with volume.batch_upload() as batch:
                batch.put_file(
                    io.BytesIO(prepared.drawing_png),
                    f"/{prepared.attempt_prefix}input/drawing.png",
                )
                batch.put_file(
                    io.BytesIO(prepared.manifest),
                    f"/{prepared.attempt_prefix}input/manifest.json",
                )

            call = function.spawn(prepared.payload)
            call_id = getattr(call, "object_id", None)
            if not isinstance(call_id, str) or not call_id.startswith("fc-"):
                raise ModalFunctionOutcomeUnknown()
            _LOGGER.info(
                "modal_drawing_function_started",
                modal_call_id=call_id,
                workload="drawing.analyze",
                drawing_sha256=prepared.drawing_sha256,
            )
            try:
                result = call.get(timeout=self._timeout)
            except TimeoutError as exc:
                raise ModalFunctionOutcomeUnknown(call_id) from exc
            terminal = True
            if not isinstance(result, dict):
                raise ModalFunctionOutcomeUnknown(call_id)
            try:
                output_bytes = canonical_json(result).encode("utf-8")
            except (TypeError, ValueError) as exc:
                raise ModalFunctionOutcomeUnknown(call_id) from exc
            if len(output_bytes) > MAX_OUTPUT_BYTES:
                raise ModalFunctionOutcomeUnknown(call_id)
            return ModalFunctionResult(
                output=result,
                call_id=call_id,
                output_sha256=hashlib.sha256(output_bytes).hexdigest(),
                elapsed_seconds=round(time.perf_counter() - started, 3),
            )
        except ModalFunctionOutcomeUnknown:
            raise
        except Exception as exc:
            # Do not surface SDK diagnostics; a failure after dispatch is treated as ambiguous.
            raise ModalFunctionOutcomeUnknown(call_id) from exc
        finally:
            if terminal:
                try:
                    volume.remove_file(
                        f"{prepared.attempt_prefix}input",
                        recursive=True,
                    )
                except Exception as exc:
                    raise ModalFunctionOutcomeUnknown(call_id) from exc


class ModalStoryFunctionClient:
    """Stage an allowlisted Parent story manifest and invoke the private Qwen worker once."""

    def __init__(
        self,
        *,
        volume: Any | None = None,
        function: Any | None = None,
        timeout_seconds: float = 1_800.0,
    ) -> None:
        if (volume is None) != (function is None):
            raise ValueError("Modal test doubles must supply both Volume and Function")
        if not 0 < timeout_seconds <= 1_800:
            raise ValueError("Modal story wait timeout is outside the approved bound")
        self._volume = volume
        self._function = function
        self._timeout = timeout_seconds

    def generate(self, context: dict[str, object]) -> tuple[dict[str, object], str]:
        worker_input = context.get("worker_input")
        expected = {
            "schema_version",
            "role",
            "language",
            "confirmed_subject",
            "understanding_revision",
            "drawing_sha256",
            "visible_features",
            "child_age_months",
            "context_revision",
            "adult_confirmed_idea",
            "rewrite_instruction",
            "lesson_direction",
        }
        if not isinstance(worker_input, dict) or set(worker_input) != expected:
            raise ValueError("Modal story request does not match the approved input contract")
        if (
            worker_input.get("schema_version") != "sketch2life.story-generation-input.v1"
            or worker_input.get("role") != "PARENT"
            or worker_input.get("language") != "vi"
            or worker_input.get("lesson_direction") is not None
            or not isinstance(worker_input.get("confirmed_subject"), str)
            or not isinstance(worker_input.get("visible_features"), list)
            or not 36 <= int(worker_input.get("child_age_months", 0)) <= 120
            or worker_input.get("activities") is not None
        ):
            raise ValueError("Modal story request violates Parent role or SRS limits")
        request_bytes = canonical_json(worker_input).encode("utf-8")
        if len(request_bytes) > MAX_MANIFEST_BYTES:
            raise ValueError("Modal story request exceeds the manifest limit")
        job_id, generation_id, attempt_id = (str(uuid.uuid4()) for _ in range(3))
        attempt_prefix = f"sketch2life/{ENVIRONMENT_NAME}/{job_id}/{generation_id}/{attempt_id}/"
        manifest = {
            "schema_version": STORY_INPUT_SCHEMA,
            "asset": {
                "path": "input/request.json",
                "content_type": "application/json",
                "size_bytes": len(request_bytes),
                "sha256": hashlib.sha256(request_bytes).hexdigest(),
            },
        }
        manifest_bytes = canonical_json(manifest).encode("utf-8")
        payload = {
            "schema_version": WORKER_INPUT_SCHEMA,
            "environment": ENVIRONMENT_NAME,
            "workload": "story.generate",
            "job_id": job_id,
            "generation_id": generation_id,
            "attempt_id": attempt_id,
            "attempt_prefix": attempt_prefix,
            "input_manifest_ref": "input/manifest.json",
            "input_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            "input_bytes": len(manifest_bytes) + len(request_bytes),
        }
        volume = self._volume
        function = self._function
        if volume is None:
            import modal

            volume = modal.Volume.from_name(
                SCRATCH_VOLUME_NAME, environment_name=ENVIRONMENT_NAME, version=2
            )
            function = modal.Function.from_name(
                "sketch2life-srs23-language-audio-dev",
                "generate-story-and-storyboard",
                environment_name=ENVIRONMENT_NAME,
            )
        assert function is not None
        call_id: str | None = None
        terminal = False
        started = time.perf_counter()
        try:
            with volume.batch_upload() as batch:
                batch.put_file(io.BytesIO(request_bytes), f"/{attempt_prefix}input/request.json")
                batch.put_file(io.BytesIO(manifest_bytes), f"/{attempt_prefix}input/manifest.json")
            call = function.spawn(payload)
            call_id = getattr(call, "object_id", None)
            if not isinstance(call_id, str) or not call_id.startswith("fc-"):
                raise ModalFunctionOutcomeUnknown()
            try:
                output = call.get(timeout=self._timeout)
            except TimeoutError as exc:
                raise ModalFunctionOutcomeUnknown(call_id) from exc
            except Exception as exc:
                terminal = True
                safe_text = str(exc)
                terminal_worker_errors = {
                    "MODAL_EDUCATIONAL_FACT_CHECK_FAILED": "EDUCATIONAL_FACT_CHECK_FAILED",
                    "MODAL_MODEL_OUTPUT_INVALID": "STORY_OUTPUT_INVALID",
                    "MODAL_SCHEMA_UNSUPPORTED": "STORY_INPUT_CONTRACT_INVALID",
                    "MODAL_INPUT_INVALID": "STORY_INPUT_CONTRACT_INVALID",
                    "MODAL_INPUT_MANIFEST_INVALID": "STORY_INPUT_CONTRACT_INVALID",
                    "MODAL_INPUT_TYPE_NOT_ALLOWED": "STORY_INPUT_CONTRACT_INVALID",
                    "MODAL_INPUT_HASH_MISMATCH": "STORY_INPUT_INTEGRITY_INVALID",
                    "MODAL_INPUT_LIMIT_EXCEEDED": "STORY_INPUT_LIMIT_EXCEEDED",
                    "MODAL_INPUT_MANIFEST_MISSING": "STORY_INPUT_MISSING",
                    "MODAL_INPUT_ASSET_MISSING": "STORY_INPUT_MISSING",
                    "MODAL_PATH_SCOPE_INVALID": "STORY_INPUT_CONTRACT_INVALID",
                    "MODAL_WORKLOAD_NOT_ALLOWED": "STORY_INPUT_CONTRACT_INVALID",
                    "MODAL_ENVIRONMENT_NOT_ALLOWED": "STORY_INPUT_CONTRACT_INVALID",
                }
                for marker, code in terminal_worker_errors.items():
                    if marker in safe_text:
                        raise ModalFunctionExecutionFailed(code) from None
                if type(exc).__name__ == "RemoteError" and type(exc).__module__.startswith(
                    "modal."
                ):
                    raise ModalFunctionExecutionFailed("STORY_WORKER_FAILED_TERMINAL") from None
                raise ModalFunctionOutcomeUnknown(call_id) from exc
            terminal = True
            if not isinstance(output, dict):
                raise ModalFunctionExecutionFailed("STORY_OUTPUT_INVALID")
            output_bytes = canonical_json(output).encode("utf-8")
            if len(output_bytes) > MAX_OUTPUT_BYTES:
                raise ModalFunctionExecutionFailed("STORY_OUTPUT_INVALID")
            if (
                output.get("schema_version") != WORKER_OUTPUT_SCHEMA
                or output.get("workload") != "story.generate"
                or output.get("job_id") != job_id
                or output.get("generation_id") != generation_id
                or output.get("attempt_id") != attempt_id
            ):
                raise ModalFunctionExecutionFailed("STORY_OUTPUT_INVALID")
            model = output.get("model")
            if not isinstance(model, dict) or set(model) != {"id", "revision"}:
                raise ModalFunctionExecutionFailed("STORY_OUTPUT_INVALID")
            if model.get("id") != STORY_MODEL_ID or model.get("revision") != STORY_MODEL_REVISION:
                raise ModalFunctionExecutionFailed("STORY_OUTPUT_INVALID")
            result = output.get("result")
            if not isinstance(result, dict):
                raise ModalFunctionExecutionFailed("STORY_OUTPUT_INVALID")
            _LOGGER.info(
                "modal_story_generation_completed",
                modal_call_id=call_id,
                output_sha256=hashlib.sha256(output_bytes).hexdigest(),
                elapsed_seconds=round(time.perf_counter() - started, 3),
            )
            return result, call_id
        except ModalFunctionOutcomeUnknown:
            raise
        except ModalFunctionExecutionFailed:
            raise
        except Exception as exc:
            raise ModalFunctionOutcomeUnknown(call_id) from exc
        finally:
            if terminal:
                try:
                    volume.remove_file(f"{attempt_prefix}input", recursive=True)
                except Exception as exc:
                    raise ModalFunctionOutcomeUnknown(call_id) from exc


__all__ = [
    "APP_NAME",
    "ENVIRONMENT_NAME",
    "FUNCTION_NAME",
    "MODEL_ID",
    "MODEL_REVISION",
    "ModalDrawingFunctionClient",
    "ModalStoryFunctionClient",
    "ModalFunctionOutcomeUnknown",
    "ModalFunctionExecutionFailed",
    "ModalFunctionResult",
    "PreparedDrawingInput",
    "prepare_drawing_input",
]
