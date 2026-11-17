"""Safe, no-model-load readiness checks for the approved Lightning L4 setup."""

from __future__ import annotations

import importlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from importlib import metadata
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from sketch2life.contracts.schemas.vision_v2 import (
    VisionProfileIdV2,
    vision_profile_catalog_hash_v2,
    vision_profile_catalog_v2,
    vision_profile_config_hash_v2,
)
from sketch2life.infrastructure.ai.qwen_vision_runtime_config import (
    QwenVisionRuntimeConfig,
)


class QwenVisionEnvironmentStatus(StrEnum):
    READY = "READY"
    NOT_READY = "NOT_READY"


class QwenVisionDeviceClass(StrEnum):
    NVIDIA_L4 = "NVIDIA_L4"
    OTHER = "OTHER"
    NOT_AVAILABLE = "NOT_AVAILABLE"


class QwenVisionConfiguredDevice(StrEnum):
    CUDA = "CUDA"
    OTHER = "OTHER"


class QwenVisionRevisionState(StrEnum):
    VERIFIED = "VERIFIED"
    NOT_VERIFIABLE = "NOT_VERIFIABLE"
    MISMATCH = "MISMATCH"


class QwenVisionEnvironmentIssue(StrEnum):
    DEVICE_MUST_BE_CUDA = "DEVICE_MUST_BE_CUDA"
    MODEL_DIRECTORY_REQUIRED = "MODEL_DIRECTORY_REQUIRED"
    MODEL_SNAPSHOT_NOT_FOUND = "MODEL_SNAPSHOT_NOT_FOUND"
    MODEL_DOWNLOAD_MUST_BE_DISABLED = "MODEL_DOWNLOAD_MUST_BE_DISABLED"
    MODEL_REVISION_NOT_VERIFIABLE = "MODEL_REVISION_NOT_VERIFIABLE"
    MODEL_REVISION_MISMATCH = "MODEL_REVISION_MISMATCH"
    DEPENDENCY_NOT_INSTALLED = "DEPENDENCY_NOT_INSTALLED"
    DEPENDENCY_VERSION_MISMATCH = "DEPENDENCY_VERSION_MISMATCH"
    CUDA_NOT_AVAILABLE = "CUDA_NOT_AVAILABLE"
    DEVICE_INDEX_UNAVAILABLE = "DEVICE_INDEX_UNAVAILABLE"
    BF16_NOT_SUPPORTED = "BF16_NOT_SUPPORTED"
    DEVICE_CLASS_MISMATCH = "DEVICE_CLASS_MISMATCH"


class QwenVisionDependencyReadinessV1(BaseModel):
    """One safe exact-pin comparison; no install path is exposed."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    package: str
    expected_version: str
    installed_version: str | None
    matches: bool


class QwenVisionEnvironmentReadinessV1(BaseModel):
    """Sanitized setup result. This is not a real-model B2 preflight result."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_name: Literal["QwenVisionEnvironmentReadinessV1"] = (
        "QwenVisionEnvironmentReadinessV1"
    )
    contract_version: Literal["1.0"] = "1.0"
    status: QwenVisionEnvironmentStatus
    profile_id: VisionProfileIdV2
    config_hash: str
    profile_catalog_hash: str
    configured_device: QwenVisionConfiguredDevice
    device_index: int
    expected_device_class: QwenVisionDeviceClass
    observed_device_class: QwenVisionDeviceClass
    cuda_available: bool
    bf16_supported: bool
    model_directory_configured: bool
    model_snapshot_present: bool
    model_revision_state: QwenVisionRevisionState
    dependencies: tuple[QwenVisionDependencyReadinessV1, ...]
    issues: tuple[QwenVisionEnvironmentIssue, ...]
    model_load_performed: Literal[False] = False
    inference_performed: Literal[False] = False


@dataclass(frozen=True, slots=True)
class QwenVisionHardwareFacts:
    cuda_available: bool
    device_count: int
    device_name: str | None
    bf16_supported: bool


VersionLookup = Callable[[str], str | None]
HardwareProbe = Callable[[int], QwenVisionHardwareFacts]
RevisionVerifier = Callable[[Path, str], QwenVisionRevisionState]


_QWEN_LOAD_REQUIRED_FILENAMES = (
    "chat_template.json",
    "config.json",
    "generation_config.json",
    "merges.txt",
    "model.safetensors.index.json",
    "preprocessor_config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "video_preprocessor_config.json",
    "vocab.json",
)


def _installed_version(package: str) -> str | None:
    try:
        return metadata.version(package)
    except metadata.PackageNotFoundError:
        return None


def _probe_torch_hardware(device_index: int) -> QwenVisionHardwareFacts:
    try:
        torch_module = importlib.import_module("torch")
        cuda = torch_module.cuda
        cuda_available = bool(cuda.is_available())
        device_count = int(cuda.device_count()) if cuda_available else 0
        if not cuda_available or device_index >= device_count:
            return QwenVisionHardwareFacts(
                cuda_available=cuda_available,
                device_count=device_count,
                device_name=None,
                bf16_supported=False,
            )
        device_name = str(cuda.get_device_name(device_index))
        with cuda.device(device_index):
            bf16_supported = bool(cuda.is_bf16_supported())
        return QwenVisionHardwareFacts(
            cuda_available=True,
            device_count=device_count,
            device_name=device_name,
            bf16_supported=bf16_supported,
        )
    except Exception:  # noqa: BLE001 - readiness output contains only safe typed facts
        return QwenVisionHardwareFacts(
            cuda_available=False,
            device_count=0,
            device_name=None,
            bf16_supported=False,
        )


def _verify_local_snapshot_revision(
    model_dir: Path, expected_revision: str
) -> QwenVisionRevisionState:
    required_files = _required_local_snapshot_files(model_dir)
    if required_files is None:
        return QwenVisionRevisionState.NOT_VERIFIABLE

    metadata_root = model_dir / ".cache" / "huggingface" / "download"
    observed_revisions: set[str] = set()
    try:
        for required_file in required_files:
            relative_path = required_file.relative_to(model_dir)
            metadata_file = metadata_root / relative_path.with_name(
                f"{relative_path.name}.metadata"
            )
            lines = metadata_file.read_text(encoding="utf-8").splitlines()
            if not lines or not lines[0].strip():
                return QwenVisionRevisionState.NOT_VERIFIABLE
            observed_revisions.add(lines[0].strip())
    except (OSError, UnicodeError):
        return QwenVisionRevisionState.NOT_VERIFIABLE

    if observed_revisions == {expected_revision}:
        return QwenVisionRevisionState.VERIFIED
    return QwenVisionRevisionState.MISMATCH


def _required_local_snapshot_files(model_dir: Path) -> tuple[Path, ...] | None:
    required_files = tuple(model_dir / name for name in _QWEN_LOAD_REQUIRED_FILENAMES)
    if not all(path.is_file() for path in required_files):
        return None

    try:
        index_payload = json.loads(
            (model_dir / "model.safetensors.index.json").read_text(encoding="utf-8")
        )
        weight_map = index_payload.get("weight_map")
        if not isinstance(weight_map, dict) or not weight_map:
            return None
        shard_names = set(weight_map.values())
        if not shard_names or not all(isinstance(name, str) for name in shard_names):
            return None
        if any(
            Path(name).name != name or not name.endswith(".safetensors")
            for name in shard_names
        ):
            return None
        shard_files = tuple(model_dir / name for name in sorted(shard_names))
        if not all(path.is_file() for path in shard_files):
            return None
        return (*required_files, *shard_files)
    except (OSError, ValueError, TypeError, AttributeError):
        return None


def _has_complete_local_snapshot(model_dir: Path) -> bool:
    return _required_local_snapshot_files(model_dir) is not None


def _dependency_version_matches(package: str, installed: str | None, expected: str) -> bool:
    if installed is None:
        return False
    if package == "torch":
        return installed.split("+", maxsplit=1)[0] == expected
    return installed == expected


def _normalize_device_class(device_name: str | None) -> QwenVisionDeviceClass:
    if device_name is None:
        return QwenVisionDeviceClass.NOT_AVAILABLE
    normalized = "_".join(device_name.upper().split())
    if normalized in {"L4", "NVIDIA_L4"}:
        return QwenVisionDeviceClass.NVIDIA_L4
    return QwenVisionDeviceClass.OTHER


def inspect_qwen_vision_environment(
    runtime_config: QwenVisionRuntimeConfig,
    profile_id: VisionProfileIdV2,
    *,
    version_lookup: VersionLookup = _installed_version,
    hardware_probe: HardwareProbe = _probe_torch_hardware,
    revision_verifier: RevisionVerifier = _verify_local_snapshot_revision,
) -> QwenVisionEnvironmentReadinessV1:
    """Inspect setup readiness without importing Transformers or loading model weights."""

    if not isinstance(profile_id, VisionProfileIdV2):
        raise TypeError("inspect_qwen_vision_environment requires VisionProfileIdV2")
    catalog = vision_profile_catalog_v2()
    profile = catalog.resolve(profile_id)

    issues: list[QwenVisionEnvironmentIssue] = []
    if runtime_config.device != "cuda":
        issues.append(QwenVisionEnvironmentIssue.DEVICE_MUST_BE_CUDA)

    model_directory_configured = runtime_config.model_dir is not None
    model_snapshot_present = bool(
        runtime_config.model_dir is not None
        and runtime_config.model_dir.is_dir()
        and _has_complete_local_snapshot(runtime_config.model_dir)
    )
    if not model_directory_configured:
        issues.append(QwenVisionEnvironmentIssue.MODEL_DIRECTORY_REQUIRED)
    elif not model_snapshot_present:
        issues.append(QwenVisionEnvironmentIssue.MODEL_SNAPSHOT_NOT_FOUND)
    if runtime_config.allow_model_download:
        issues.append(QwenVisionEnvironmentIssue.MODEL_DOWNLOAD_MUST_BE_DISABLED)

    revision_state = QwenVisionRevisionState.NOT_VERIFIABLE
    if model_snapshot_present and runtime_config.model_dir is not None:
        revision_state = revision_verifier(
            runtime_config.model_dir,
            profile.model_provenance.model_revision,
        )
    if revision_state is QwenVisionRevisionState.NOT_VERIFIABLE:
        issues.append(QwenVisionEnvironmentIssue.MODEL_REVISION_NOT_VERIFIABLE)
    elif revision_state is QwenVisionRevisionState.MISMATCH:
        issues.append(QwenVisionEnvironmentIssue.MODEL_REVISION_MISMATCH)

    dependency_checks: list[QwenVisionDependencyReadinessV1] = []
    for pin in profile.model_provenance.dependency_pins:
        installed = version_lookup(pin.package)
        matches = _dependency_version_matches(pin.package, installed, pin.version)
        dependency_checks.append(
            QwenVisionDependencyReadinessV1(
                package=pin.package,
                expected_version=pin.version,
                installed_version=installed,
                matches=matches,
            )
        )
        if installed is None:
            issues.append(QwenVisionEnvironmentIssue.DEPENDENCY_NOT_INSTALLED)
        elif not matches:
            issues.append(QwenVisionEnvironmentIssue.DEPENDENCY_VERSION_MISMATCH)

    hardware = hardware_probe(runtime_config.device_index)
    observed_device_class = _normalize_device_class(hardware.device_name)
    expected_device_class = QwenVisionDeviceClass.NVIDIA_L4
    if not hardware.cuda_available:
        issues.append(QwenVisionEnvironmentIssue.CUDA_NOT_AVAILABLE)
    if runtime_config.device_index >= hardware.device_count:
        issues.append(QwenVisionEnvironmentIssue.DEVICE_INDEX_UNAVAILABLE)
    if not hardware.bf16_supported:
        issues.append(QwenVisionEnvironmentIssue.BF16_NOT_SUPPORTED)
    if observed_device_class is not expected_device_class:
        issues.append(QwenVisionEnvironmentIssue.DEVICE_CLASS_MISMATCH)

    unique_issues = tuple(dict.fromkeys(issues))
    status = (
        QwenVisionEnvironmentStatus.READY
        if not unique_issues
        else QwenVisionEnvironmentStatus.NOT_READY
    )
    configured_device = (
        QwenVisionConfiguredDevice.CUDA
        if runtime_config.device == "cuda"
        else QwenVisionConfiguredDevice.OTHER
    )
    return QwenVisionEnvironmentReadinessV1(
        status=status,
        profile_id=profile.profile_id,
        config_hash=vision_profile_config_hash_v2(profile),
        profile_catalog_hash=vision_profile_catalog_hash_v2(catalog),
        configured_device=configured_device,
        device_index=runtime_config.device_index,
        expected_device_class=expected_device_class,
        observed_device_class=observed_device_class,
        cuda_available=hardware.cuda_available,
        bf16_supported=hardware.bf16_supported,
        model_directory_configured=model_directory_configured,
        model_snapshot_present=model_snapshot_present,
        model_revision_state=revision_state,
        dependencies=tuple(dependency_checks),
        issues=unique_issues,
    )


def inspect_qwen_vision_environment_from_env_file(
    env_file: Path,
    profile_id: VisionProfileIdV2,
    *,
    version_lookup: VersionLookup = _installed_version,
    hardware_probe: HardwareProbe = _probe_torch_hardware,
    revision_verifier: RevisionVerifier = _verify_local_snapshot_revision,
) -> QwenVisionEnvironmentReadinessV1:
    """Load only the explicitly selected env file and inspect the explicit profile."""

    runtime_config = QwenVisionRuntimeConfig.from_env_file(env_file, environ={})
    return inspect_qwen_vision_environment(
        runtime_config,
        profile_id,
        version_lookup=version_lookup,
        hardware_probe=hardware_probe,
        revision_verifier=revision_verifier,
    )


__all__ = [
    "QwenVisionConfiguredDevice",
    "QwenVisionDeviceClass",
    "QwenVisionDependencyReadinessV1",
    "QwenVisionEnvironmentIssue",
    "QwenVisionEnvironmentReadinessV1",
    "QwenVisionEnvironmentStatus",
    "QwenVisionHardwareFacts",
    "QwenVisionRevisionState",
    "inspect_qwen_vision_environment",
    "inspect_qwen_vision_environment_from_env_file",
]
