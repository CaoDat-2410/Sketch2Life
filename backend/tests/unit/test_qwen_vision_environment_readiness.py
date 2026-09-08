from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from sketch2life.contracts.schemas.vision_v2 import (
    VisionProfileIdV2,
    vision_profile_catalog_v2,
)
from sketch2life.infrastructure.ai.qwen_vision_environment_readiness import (
    QwenVisionEnvironmentIssue,
    QwenVisionEnvironmentStatus,
    QwenVisionHardwareFacts,
    QwenVisionRevisionState,
    inspect_qwen_vision_environment,
    inspect_qwen_vision_environment_from_env_file,
)
from sketch2life.infrastructure.ai.qwen_vision_runtime_config import (
    QwenVisionRuntimeConfig,
)

_PROFILE = vision_profile_catalog_v2().resolve(
    VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1
)
_PINNED_VERSIONS = {
    pin.package: pin.version for pin in _PROFILE.model_provenance.dependency_pins
}
_LOAD_REQUIRED_FILENAMES = (
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
_SYNTHETIC_SHARD_FILENAME = "model-00001-of-00001.safetensors"


def _write_complete_snapshot(model_dir: Path) -> None:
    model_dir.mkdir()
    for filename in _LOAD_REQUIRED_FILENAMES:
        if filename == "model.safetensors.index.json":
            continue
        (model_dir / filename).write_text("{}", encoding="utf-8")
    (model_dir / _SYNTHETIC_SHARD_FILENAME).write_bytes(b"synthetic")
    (model_dir / "model.safetensors.index.json").write_text(
        f'{{"weight_map":{{"weight":"{_SYNTHETIC_SHARD_FILENAME}"}}}}',
        encoding="utf-8",
    )


def _write_revision_metadata(model_dir: Path, revision: str) -> None:
    metadata_dir = model_dir / ".cache" / "huggingface" / "download"
    metadata_dir.mkdir(parents=True)
    for filename in (*_LOAD_REQUIRED_FILENAMES, _SYNTHETIC_SHARD_FILENAME):
        (metadata_dir / f"{filename}.metadata").write_text(
            f"{revision}\netag\n",
            encoding="utf-8",
        )


def _l4_hardware(_device_index: int) -> QwenVisionHardwareFacts:
    return QwenVisionHardwareFacts(
        cuda_available=True,
        device_count=1,
        device_name="NVIDIA L4",
        bf16_supported=True,
    )


def _verified_revision(_model_dir: Path, _revision: str) -> QwenVisionRevisionState:
    return QwenVisionRevisionState.VERIFIED


def _runtime(model_dir: Path, **overrides: object) -> QwenVisionRuntimeConfig:
    values: dict[str, object] = {
        "model_dir": model_dir,
        "device": "cuda",
        "device_index": 0,
        "allow_model_download": False,
    }
    values.update(overrides)
    return QwenVisionRuntimeConfig(**values)  # type: ignore[arg-type]


def test_ready_environment_uses_profile_pins_without_loading_a_model(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    _write_complete_snapshot(model_dir)

    result = inspect_qwen_vision_environment(
        _runtime(model_dir),
        VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1,
        version_lookup=_PINNED_VERSIONS.get,
        hardware_probe=_l4_hardware,
        revision_verifier=_verified_revision,
    )

    assert result.status is QwenVisionEnvironmentStatus.READY
    assert result.issues == ()
    assert result.model_revision_state is QwenVisionRevisionState.VERIFIED
    assert result.model_load_performed is False
    assert result.inference_performed is False
    assert all(item.matches for item in result.dependencies)
    assert str(tmp_path) not in result.model_dump_json()

    with pytest.raises(ValidationError):
        type(result)(**{**result.model_dump(), "model_load_performed": True})
    with pytest.raises(ValidationError):
        type(result)(**{**result.model_dump(), "inference_performed": True})


def test_incomplete_local_snapshot_is_not_ready(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    (model_dir / "config.json").write_text("{}", encoding="utf-8")

    result = inspect_qwen_vision_environment(
        _runtime(model_dir),
        VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1,
        version_lookup=_PINNED_VERSIONS.get,
        hardware_probe=_l4_hardware,
        revision_verifier=_verified_revision,
    )

    assert result.status is QwenVisionEnvironmentStatus.NOT_READY
    assert QwenVisionEnvironmentIssue.MODEL_SNAPSHOT_NOT_FOUND in result.issues


def test_weight_index_cannot_reference_a_shard_outside_the_model_directory(
    tmp_path: Path,
) -> None:
    model_dir = tmp_path / "model"
    _write_complete_snapshot(model_dir)
    (tmp_path / "outside.safetensors").write_bytes(b"synthetic")
    (model_dir / "model.safetensors.index.json").write_text(
        '{"weight_map":{"weight":"../outside.safetensors"}}',
        encoding="utf-8",
    )

    result = inspect_qwen_vision_environment(
        _runtime(model_dir),
        VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1,
        version_lookup=_PINNED_VERSIONS.get,
        hardware_probe=_l4_hardware,
        revision_verifier=_verified_revision,
    )

    assert result.status is QwenVisionEnvironmentStatus.NOT_READY
    assert QwenVisionEnvironmentIssue.MODEL_SNAPSHOT_NOT_FOUND in result.issues


@pytest.mark.parametrize(
    ("package", "installed", "issue"),
    (
        ("accelerate", None, QwenVisionEnvironmentIssue.DEPENDENCY_NOT_INSTALLED),
        (
            "transformers",
            "0.0.0",
            QwenVisionEnvironmentIssue.DEPENDENCY_VERSION_MISMATCH,
        ),
    ),
)
def test_missing_or_mismatched_dependency_is_not_ready(
    package: str,
    installed: str | None,
    issue: QwenVisionEnvironmentIssue,
    tmp_path: Path,
) -> None:
    model_dir = tmp_path / "model"
    _write_complete_snapshot(model_dir)
    versions = {**_PINNED_VERSIONS, package: installed}

    result = inspect_qwen_vision_environment(
        _runtime(model_dir),
        VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1,
        version_lookup=versions.get,
        hardware_probe=_l4_hardware,
        revision_verifier=_verified_revision,
    )

    assert result.status is QwenVisionEnvironmentStatus.NOT_READY
    assert issue in result.issues


def test_torch_cuda_local_version_suffix_matches_the_exact_base_pin(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    _write_complete_snapshot(model_dir)
    versions = {**_PINNED_VERSIONS, "torch": "2.8.0+cu128"}

    result = inspect_qwen_vision_environment(
        _runtime(model_dir),
        VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1,
        version_lookup=versions.get,
        hardware_probe=_l4_hardware,
        revision_verifier=_verified_revision,
    )

    assert result.status is QwenVisionEnvironmentStatus.READY
    assert next(item for item in result.dependencies if item.package == "torch").matches


@pytest.mark.parametrize(
    ("hardware", "issue"),
    (
        (
            QwenVisionHardwareFacts(False, 0, None, False),
            QwenVisionEnvironmentIssue.CUDA_NOT_AVAILABLE,
        ),
        (
            QwenVisionHardwareFacts(True, 0, None, False),
            QwenVisionEnvironmentIssue.DEVICE_INDEX_UNAVAILABLE,
        ),
        (
            QwenVisionHardwareFacts(True, 1, "NVIDIA L4", False),
            QwenVisionEnvironmentIssue.BF16_NOT_SUPPORTED,
        ),
        (
            QwenVisionHardwareFacts(True, 1, "NVIDIA T4", True),
            QwenVisionEnvironmentIssue.DEVICE_CLASS_MISMATCH,
        ),
    ),
)
def test_hardware_readiness_failures_are_typed(
    hardware: QwenVisionHardwareFacts,
    issue: QwenVisionEnvironmentIssue,
    tmp_path: Path,
) -> None:
    model_dir = tmp_path / "model"
    _write_complete_snapshot(model_dir)

    result = inspect_qwen_vision_environment(
        _runtime(model_dir),
        VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1,
        version_lookup=_PINNED_VERSIONS.get,
        hardware_probe=lambda _index: hardware,
        revision_verifier=_verified_revision,
    )

    assert result.status is QwenVisionEnvironmentStatus.NOT_READY
    assert issue in result.issues


@pytest.mark.parametrize(
    ("revision_state", "issue"),
    (
        (
            QwenVisionRevisionState.NOT_VERIFIABLE,
            QwenVisionEnvironmentIssue.MODEL_REVISION_NOT_VERIFIABLE,
        ),
        (
            QwenVisionRevisionState.MISMATCH,
            QwenVisionEnvironmentIssue.MODEL_REVISION_MISMATCH,
        ),
    ),
)
def test_snapshot_revision_must_be_verified(
    revision_state: QwenVisionRevisionState,
    issue: QwenVisionEnvironmentIssue,
    tmp_path: Path,
) -> None:
    model_dir = tmp_path / "model"
    _write_complete_snapshot(model_dir)

    result = inspect_qwen_vision_environment(
        _runtime(model_dir),
        VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1,
        version_lookup=_PINNED_VERSIONS.get,
        hardware_probe=_l4_hardware,
        revision_verifier=lambda _path, _revision: revision_state,
    )

    assert result.status is QwenVisionEnvironmentStatus.NOT_READY
    assert issue in result.issues


def test_default_revision_verifier_reads_hugging_face_local_metadata(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    _write_complete_snapshot(model_dir)
    _write_revision_metadata(model_dir, _PROFILE.model_provenance.model_revision)

    result = inspect_qwen_vision_environment(
        _runtime(model_dir),
        VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1,
        version_lookup=_PINNED_VERSIONS.get,
        hardware_probe=_l4_hardware,
    )

    assert result.model_revision_state is QwenVisionRevisionState.VERIFIED
    assert result.status is QwenVisionEnvironmentStatus.READY


def test_env_file_entrypoint_uses_only_the_explicit_file(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    _write_complete_snapshot(model_dir)
    env_file = tmp_path / ".vision.env"
    env_file.write_text(
        "\n".join(
            (
                f"SKETCH2LIFE_VISION_MODEL_DIR={model_dir}",
                "SKETCH2LIFE_VISION_DEVICE=cuda",
                "SKETCH2LIFE_VISION_DEVICE_INDEX=0",
                "SKETCH2LIFE_VISION_ALLOW_MODEL_DOWNLOAD=false",
            )
        ),
        encoding="utf-8",
    )

    result = inspect_qwen_vision_environment_from_env_file(
        env_file,
        VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1,
        version_lookup=_PINNED_VERSIONS.get,
        hardware_probe=_l4_hardware,
        revision_verifier=_verified_revision,
    )

    assert result.status is QwenVisionEnvironmentStatus.READY
    assert str(model_dir) not in result.model_dump_json()


def test_cache_only_or_download_enabled_configuration_is_not_ready(tmp_path: Path) -> None:
    result = inspect_qwen_vision_environment(
        QwenVisionRuntimeConfig(
            model_cache_dir=tmp_path / "cache",
            allow_model_download=True,
        ),
        VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1,
        version_lookup=_PINNED_VERSIONS.get,
        hardware_probe=_l4_hardware,
        revision_verifier=_verified_revision,
    )

    assert result.status is QwenVisionEnvironmentStatus.NOT_READY
    assert QwenVisionEnvironmentIssue.MODEL_DIRECTORY_REQUIRED in result.issues
    assert QwenVisionEnvironmentIssue.MODEL_DOWNLOAD_MUST_BE_DISABLED in result.issues


def test_non_cuda_runtime_is_not_ready(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    _write_complete_snapshot(model_dir)

    result = inspect_qwen_vision_environment(
        _runtime(model_dir, device="private-device-marker"),
        VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1,
        version_lookup=_PINNED_VERSIONS.get,
        hardware_probe=_l4_hardware,
        revision_verifier=_verified_revision,
    )

    assert result.status is QwenVisionEnvironmentStatus.NOT_READY
    assert QwenVisionEnvironmentIssue.DEVICE_MUST_BE_CUDA in result.issues
    assert "private-device-marker" not in result.model_dump_json()


def test_environment_inspection_rejects_a_constructed_profile_object(
    tmp_path: Path,
) -> None:
    model_dir = tmp_path / "model"
    _write_complete_snapshot(model_dir)

    with pytest.raises(TypeError, match="VisionProfileIdV2"):
        inspect_qwen_vision_environment(
            _runtime(model_dir),
            _PROFILE,  # type: ignore[arg-type]
            version_lookup=_PINNED_VERSIONS.get,
            hardware_probe=_l4_hardware,
            revision_verifier=_verified_revision,
        )


@pytest.mark.parametrize("missing_filename", _LOAD_REQUIRED_FILENAMES)
def test_load_critical_snapshot_assets_are_required(
    missing_filename: str,
    tmp_path: Path,
) -> None:
    model_dir = tmp_path / "model"
    _write_complete_snapshot(model_dir)
    (model_dir / missing_filename).unlink()

    result = inspect_qwen_vision_environment(
        _runtime(model_dir),
        VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1,
        version_lookup=_PINNED_VERSIONS.get,
        hardware_probe=_l4_hardware,
        revision_verifier=_verified_revision,
    )

    assert result.status is QwenVisionEnvironmentStatus.NOT_READY
    assert QwenVisionEnvironmentIssue.MODEL_SNAPSHOT_NOT_FOUND in result.issues


def test_every_load_critical_file_and_shard_requires_matching_revision_metadata(
    tmp_path: Path,
) -> None:
    model_dir = tmp_path / "model"
    _write_complete_snapshot(model_dir)
    _write_revision_metadata(model_dir, _PROFILE.model_provenance.model_revision)
    metadata_dir = model_dir / ".cache" / "huggingface" / "download"
    (metadata_dir / f"{_SYNTHETIC_SHARD_FILENAME}.metadata").write_text(
        "0" * 40 + "\netag\n",
        encoding="utf-8",
    )

    result = inspect_qwen_vision_environment(
        _runtime(model_dir),
        VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1,
        version_lookup=_PINNED_VERSIONS.get,
        hardware_probe=_l4_hardware,
    )

    assert result.status is QwenVisionEnvironmentStatus.NOT_READY
    assert result.model_revision_state is QwenVisionRevisionState.MISMATCH


def test_missing_required_revision_metadata_is_not_verifiable(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    _write_complete_snapshot(model_dir)
    _write_revision_metadata(model_dir, _PROFILE.model_provenance.model_revision)
    metadata_dir = model_dir / ".cache" / "huggingface" / "download"
    (metadata_dir / "tokenizer.json.metadata").unlink()

    result = inspect_qwen_vision_environment(
        _runtime(model_dir),
        VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1,
        version_lookup=_PINNED_VERSIONS.get,
        hardware_probe=_l4_hardware,
    )

    assert result.status is QwenVisionEnvironmentStatus.NOT_READY
    assert result.model_revision_state is QwenVisionRevisionState.NOT_VERIFIABLE
    assert QwenVisionEnvironmentIssue.MODEL_REVISION_NOT_VERIFIABLE in result.issues


def test_corrupt_revision_metadata_returns_sanitized_not_ready(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    _write_complete_snapshot(model_dir)
    _write_revision_metadata(model_dir, _PROFILE.model_provenance.model_revision)
    metadata_dir = model_dir / ".cache" / "huggingface" / "download"
    (metadata_dir / "config.json.metadata").write_bytes(b"\xff\xfe")

    result = inspect_qwen_vision_environment(
        _runtime(model_dir),
        VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1,
        version_lookup=_PINNED_VERSIONS.get,
        hardware_probe=_l4_hardware,
    )

    assert result.status is QwenVisionEnvironmentStatus.NOT_READY
    assert result.model_revision_state is QwenVisionRevisionState.NOT_VERIFIABLE
    assert QwenVisionEnvironmentIssue.MODEL_REVISION_NOT_VERIFIABLE in result.issues
