"""One-command Lightning Studio entrypoint for the FEAT-020 backend workflow."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Sequence
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path

from sketch2life.application.services.backend_ai_workflow import (
    BackendAiWorkflow,
    BackendWorkflowRequest,
    WorkflowRuntimeError,
)
from sketch2life.contracts.schemas.asr import AsrProfileId
from sketch2life.contracts.schemas.vision_v2 import VisionProfileIdV2
from sketch2life.contracts.schemas.workflow_demo import (
    AgeBand,
    AgeMatrixSummaryV1,
    BackendWorkflowResultV1,
    WorkflowBandResultV1,
    WorkflowStageV1,
    finalize_workflow_result,
)
from sketch2life.infrastructure.ai.faster_whisper_asr import FasterWhisperAsrAdapter
from sketch2life.infrastructure.ai.faster_whisper_runtime_config import (
    FasterWhisperRuntimeConfig,
)
from sketch2life.infrastructure.ai.qwen_vision import QwenVisionAdapter
from sketch2life.infrastructure.ai.qwen_vision_environment_readiness import (
    QwenVisionEnvironmentStatus,
    inspect_qwen_vision_environment,
)
from sketch2life.infrastructure.ai.qwen_vision_runtime_config import QwenVisionRuntimeConfig
from sketch2life.infrastructure.ai.vision_lexical_policy import (
    LexicalRegressionContentPolicy,
    synthetic_prohibited_lexicon,
)
from sketch2life.infrastructure.ai.workflow_prompt import workflow_prompt_text


def build_real_workflow(repo_root: Path) -> BackendAiWorkflow:
    """Compose only real local model adapters; no fixture adapter is reachable here."""

    vision_config = QwenVisionRuntimeConfig.from_env(os.environ)
    asr_config = FasterWhisperRuntimeConfig.from_env(os.environ)
    vision = QwenVisionAdapter(
        vision_config,
        content_policy=LexicalRegressionContentPolicy(synthetic_prohibited_lexicon()),
        prompt=workflow_prompt_text(),
    )
    asr = FasterWhisperAsrAdapter(asr_config)
    return BackendAiWorkflow(asr=asr, vision=vision, repo_root=repo_root)


def inspect_real_runtime() -> tuple[bool, tuple[str, ...]]:
    """Run bounded setup checks without loading model weights or calling inference."""

    issues: list[str] = []
    try:
        vision_config = QwenVisionRuntimeConfig.from_env(os.environ)
        readiness = inspect_qwen_vision_environment(
            vision_config,
            VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1,
        )
        if readiness.status is not QwenVisionEnvironmentStatus.READY:
            issues.extend(f"VISION_{issue}" for issue in readiness.issues)
    except (RuntimeError, ValueError) as exc:
        issues.append(f"VISION_CONFIG_{type(exc).__name__}")
    try:
        asr_config = FasterWhisperRuntimeConfig.from_env(os.environ)
        if asr_config.model_dir is not None and not asr_config.model_dir.is_dir():
            issues.append("ASR_MODEL_DIRECTORY_NOT_FOUND")
        if asr_config.model_cache_dir is not None and not asr_config.model_cache_dir.is_dir():
            issues.append("ASR_MODEL_CACHE_DIRECTORY_NOT_FOUND")
        for package in ("faster-whisper", "ctranslate2"):
            if _installed_version(package) is None:
                issues.append(f"ASR_DEPENDENCY_NOT_INSTALLED:{package}")
    except (RuntimeError, ValueError) as exc:
        issues.append(f"ASR_CONFIG_{type(exc).__name__}")
    return not issues, tuple(dict.fromkeys(issues))


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    repo_root = Path(args.repo_root).resolve() if args.repo_root else Path.cwd().resolve()
    output = Path(args.output)
    age_bands: tuple[AgeBand, ...] = (
        ("0-3", "3-6", "6-9", "9-12")
        if args.age_band is None
        else (args.age_band,)
    )
    if not args.demo_autopilot:
        result = _error_manifest(
            repo_root, args.image, args.narration_audio, age_bands, "GATE_A_REQUIRED"
        )
        _write_result(output, result)
        return 5
    ready, issues = inspect_real_runtime()
    if not ready:
        result = _error_manifest(
            repo_root, args.image, args.narration_audio, age_bands, "RUNTIME_NOT_READY", issues
        )
        _write_result(output, result)
        print(json.dumps({"status": result.terminal_status, "issues": issues}, ensure_ascii=False))
        return 2
    try:
        workflow = build_real_workflow(repo_root)
        result = workflow.run(
            BackendWorkflowRequest(
                image_path=Path(args.image),
                narration_audio_path=Path(args.narration_audio),
                repo_root=repo_root,
                age_bands=age_bands,
                seed=args.seed,
                demo_autopilot=True,
                report_partial_test_only=args.report_partial_test_only,
                asr_profile_id=AsrProfileId(args.asr_profile),
            )
        )
    except (WorkflowRuntimeError, RuntimeError, ValueError) as exc:
        result = _error_manifest(
            repo_root,
            args.image,
            args.narration_audio,
            age_bands,
            "RUNTIME_NOT_READY",
            (type(exc).__name__,),
        )
    _write_result(output, result)
    print(
        json.dumps(
            {"status": result.terminal_status, "workflow_run_id": result.workflow_run_id},
            ensure_ascii=False,
        )
    )
    return _exit_code(result)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the backend-only Sketch2Life workflow demo")
    parser.add_argument("--image", required=True, help="replaceable image path")
    parser.add_argument("--narration-audio", required=True, help="replaceable Vietnamese WAV path")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--age-mode", choices=("all",), default="all")
    group.add_argument("--age-band", choices=("0-3", "3-6", "6-9", "9-12"))
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--demo-autopilot", action="store_true")
    parser.add_argument(
        "--report-partial-test-only",
        action="store_true",
        help="allow all-age test runs to return PARTIAL_SUCCESS; production remains fail-closed",
    )
    parser.add_argument("--asr-profile", default=AsrProfileId.WHISPER_TURBO_INT8_AUTO_V1.value)
    parser.add_argument("--output", default="runtime-output/workflow-result.json")
    parser.add_argument("--repo-root", default=None)
    return parser


def _installed_version(package: str) -> str | None:
    try:
        return metadata.version(package)
    except metadata.PackageNotFoundError:
        return None


def _write_result(path: Path, result: BackendWorkflowResultV1) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _error_manifest(
    repo_root: Path,
    image: str,
    audio: str,
    age_bands: tuple[AgeBand, ...],
    terminal_status: str,
    issues: tuple[str, ...] = (),
) -> BackendWorkflowResultV1:
    seed = 0
    bands = tuple(
        WorkflowBandResultV1(
            age_band=band,  # type: ignore[arg-type]
            age_months={"0-3": 24, "3-6": 54, "6-9": 84, "9-12": 132}[band],
            run_seed=seed,
            seed_fingerprint="5feceb66ffc86f38",
            status="FAILED",
            terminal_status=terminal_status,  # type: ignore[arg-type]
            stages=(
                WorkflowStageV1(
                    stage="PREFLIGHT",
                    status="FAILED",
                    reason_code=terminal_status,
                    details={"issue_count": len(issues)},
                ),
            ),
            warnings=issues,
        )
        for band in age_bands
    )
    return finalize_workflow_result(
        {
            "workflow_run_id": "workflow-preflight-failure",
            "status": "FAILED",
            "terminal_status": terminal_status,
            "input_mode": "MULTIMODAL",
            "image_artifact_ref": _safe_reference(image, repo_root),
            "image_sha256": _digest_or_empty(Path(image)),
            "audio_artifact_ref": _safe_reference(audio, repo_root),
            "audio_sha256": _digest_or_empty(Path(audio)),
            "run_seed": seed,
            "age_matrix_summary": AgeMatrixSummaryV1(
                matrix_policy=(
                    "REPORT_PARTIAL_TEST_ONLY"
                    if terminal_status == "BACKEND_CONTEXT_PARTIAL"
                    else "STRICT"
                ),
                requested_age_bands=age_bands,
                ready_age_bands=(),
                unavailable_age_bands=age_bands,
            ),
            "age_bands": [band.model_dump(mode="json") for band in bands],
            "stages": [
                WorkflowStageV1(
                    stage="PREFLIGHT",
                    status="FAILED",
                    reason_code=terminal_status,
                    details={"issue_count": len(issues)},
                )
            ],
            "warnings": issues,
            "created_at": datetime.now(UTC),
        }
    )


def _safe_reference(value: str, repo_root: Path) -> str:
    try:
        return Path(os.path.relpath(Path(value).resolve(), Path.cwd().resolve())).as_posix()
    except (OSError, ValueError):
        return "input:unresolved"


def _digest_or_empty(path: Path) -> str:
    import hashlib

    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return hashlib.sha256(b"").hexdigest()


def _exit_code(result: BackendWorkflowResultV1) -> int:
    if result.status == "PARTIAL_SUCCESS":
        return 0
    if result.terminal_status == "BACKEND_CONTEXT_READY":
        return 0
    if result.terminal_status == "RUNTIME_NOT_READY":
        return 2
    if result.terminal_status == "MEDIA_RECAPTURE":
        return 3
    if result.terminal_status in {"ASR_FAILED", "AI_FAILED"}:
        return 4
    if result.terminal_status == "NO_ELIGIBLE_ACTIVITY":
        return 5
    return 1


if __name__ == "__main__":  # pragma: no cover - exercised by Lightning operator
    raise SystemExit(main())


__all__ = ["build_real_workflow", "inspect_real_runtime", "main"]
