"""Minimal, fail-closed Modal worker envelope for the SRS v2.3 scaffold.

This module carries references and integrity metadata only. It does not load
assets, call a model, access storage, or imply that a workload is implemented.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

WORKER_INPUT_SCHEMA = "sketch2life.modal.worker-input.v1"
WORKER_OUTPUT_SCHEMA = "sketch2life.modal.worker-output.v1"
MAX_STAGED_INPUT_BYTES = 48 * 1024 * 1024  # SRS synthetic-demo proposal; unbenchmarked.

L4_WORKLOADS = frozenset(
    {
        "asr.transcribe",
        "drawing.analyze",
        "story.generate",
        "storyboard.generate",
        "parent.sketch-guide.generate",
        "teacher.sketch-deck.generate",
        "lesson.plan.suggest",
        "lesson.visual.generate",
        "drawing.segment",
        "video.scene.validate",
        "tts.narration.generate",
        "video.final-safety.validate",
    }
)
L40S_WORKLOADS = frozenset({"video.scene.generate"})
_OPAQUE_ID = re.compile(r"\A[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}\Z")
_SHA256 = re.compile(r"\A[0-9a-f]{64}\Z")


class WorkerContractError(ValueError):
    """Safe contract failure; the caller must not log the raw payload."""


class WorkloadNotConfiguredError(RuntimeError):
    """Raised until a reviewed, pinned model handler exists for a workload."""

    def __init__(self, workload: str) -> None:
        self.code = "MODAL_WORKLOAD_NOT_CONFIGURED"
        self.workload = workload
        super().__init__(f"{self.code}:{workload}")


@dataclass(frozen=True, slots=True)
class ModalWorkerInputV1:
    schema_version: Literal["sketch2life.modal.worker-input.v1"]
    environment: Literal["dev"]
    workload: str
    job_id: str
    generation_id: str
    attempt_id: str
    attempt_prefix: str
    input_manifest_ref: Literal["input/manifest.json"]
    input_manifest_sha256: str
    input_bytes: int


def parse_worker_input(
    payload: Mapping[str, Any], *, execution_group: Literal["l4", "l40s-video"]
) -> ModalWorkerInputV1:
    """Validate the exact scaffold envelope without echoing any payload value."""

    expected_keys = {
        "schema_version",
        "environment",
        "workload",
        "job_id",
        "generation_id",
        "attempt_id",
        "attempt_prefix",
        "input_manifest_ref",
        "input_manifest_sha256",
        "input_bytes",
    }
    if not isinstance(payload, Mapping) or set(payload) != expected_keys:
        raise WorkerContractError("MODAL_INPUT_INVALID")
    if payload.get("schema_version") != WORKER_INPUT_SCHEMA:
        raise WorkerContractError("MODAL_SCHEMA_UNSUPPORTED")
    if payload.get("environment") != "dev":
        raise WorkerContractError("MODAL_ENVIRONMENT_NOT_ALLOWED")

    workload = payload.get("workload")
    allowed_workloads = L4_WORKLOADS if execution_group == "l4" else L40S_WORKLOADS
    if not isinstance(workload, str) or workload not in allowed_workloads:
        raise WorkerContractError("MODAL_WORKLOAD_NOT_ALLOWED")

    identifiers: dict[str, str] = {}
    for field in ("job_id", "generation_id", "attempt_id"):
        value = payload.get(field)
        if not isinstance(value, str) or _OPAQUE_ID.fullmatch(value) is None:
            raise WorkerContractError("MODAL_INPUT_INVALID")
        identifiers[field] = value

    expected_prefix = (
        "sketch2life/dev/"
        f"{identifiers['job_id']}/{identifiers['generation_id']}/{identifiers['attempt_id']}/"
    )
    if payload.get("attempt_prefix") != expected_prefix:
        raise WorkerContractError("MODAL_PATH_SCOPE_INVALID")
    if payload.get("input_manifest_ref") != "input/manifest.json":
        raise WorkerContractError("MODAL_PATH_SCOPE_INVALID")

    digest = payload.get("input_manifest_sha256")
    if not isinstance(digest, str) or _SHA256.fullmatch(digest) is None:
        raise WorkerContractError("MODAL_INPUT_INVALID")
    input_bytes = payload.get("input_bytes")
    if (
        isinstance(input_bytes, bool)
        or not isinstance(input_bytes, int)
        or input_bytes < 0
        or input_bytes > MAX_STAGED_INPUT_BYTES
    ):
        raise WorkerContractError("MODAL_INPUT_LIMIT_EXCEEDED")

    return ModalWorkerInputV1(
        schema_version=WORKER_INPUT_SCHEMA,
        environment="dev",
        workload=workload,
        job_id=identifiers["job_id"],
        generation_id=identifiers["generation_id"],
        attempt_id=identifiers["attempt_id"],
        attempt_prefix=expected_prefix,
        input_manifest_ref="input/manifest.json",
        input_manifest_sha256=digest,
        input_bytes=input_bytes,
    )


def not_configured(request: ModalWorkerInputV1) -> None:
    """Never turn a scaffold call into a false success or fabricated output."""

    raise WorkloadNotConfiguredError(request.workload)
