from __future__ import annotations

import os
from pathlib import Path

import pytest

from sketch2life.infrastructure.ai.qwen_vision_runtime_config import (
    VISION_ALLOW_DOWNLOAD_ENV_VAR,
    VISION_DEVICE_ENV_VAR,
    VISION_DEVICE_INDEX_ENV_VAR,
    VISION_MODEL_CACHE_DIR_ENV_VAR,
    VISION_MODEL_DIR_ENV_VAR,
    QwenVisionRuntimeConfig,
)


def test_runtime_config_requires_an_explicit_model_or_cache_path() -> None:
    with pytest.raises(RuntimeError, match="no default Qwen model path"):
        QwenVisionRuntimeConfig.from_env({})
    with pytest.raises(ValueError, match="no default Qwen model path"):
        QwenVisionRuntimeConfig()


def test_runtime_config_is_constructor_injected_and_parses_only_vision_keys() -> None:
    config = QwenVisionRuntimeConfig.from_env(
        {
            VISION_MODEL_DIR_ENV_VAR: "models/qwen3-vl",
            VISION_MODEL_CACHE_DIR_ENV_VAR: "models/qwen-vl-cache",
            VISION_DEVICE_ENV_VAR: "cuda",
            VISION_DEVICE_INDEX_ENV_VAR: "1",
            VISION_ALLOW_DOWNLOAD_ENV_VAR: "false",
            "SKETCH2LIFE_S3_ENDPOINT": "must-not-be-read",
        }
    )
    assert config.model_dir == Path("models/qwen3-vl")
    assert config.model_cache_dir == Path("models/qwen-vl-cache")
    assert config.device == "cuda"
    assert config.device_index == 1
    assert config.allow_model_download is False
    assert config.model_reference("Qwen/Qwen3-VL-8B-Instruct") == str(Path("models/qwen3-vl"))


def test_runtime_config_uses_model_identifier_when_only_cache_is_selected() -> None:
    config = QwenVisionRuntimeConfig.from_env(
        {VISION_MODEL_CACHE_DIR_ENV_VAR: "models/qwen-vl-cache"}
    )
    assert config.model_dir is None
    assert config.model_reference("Qwen/Qwen3-VL-8B-Instruct") == "Qwen/Qwen3-VL-8B-Instruct"


def test_env_file_loading_does_not_mutate_process_environment(tmp_path: Path) -> None:
    env_file = tmp_path / ".vision.env"
    env_file.write_text(
        "\n".join(
            (
                "# local-only test values",
                "SKETCH2LIFE_VISION_MODEL_DIR=models/qwen3-vl",
                "SKETCH2LIFE_VISION_DEVICE=cuda",
                "SKETCH2LIFE_VISION_DEVICE_INDEX=0",
                "SKETCH2LIFE_VISION_ALLOW_MODEL_DOWNLOAD=false",
            )
        ),
        encoding="utf-8",
    )
    before = {key: os.environ.get(key) for key in (
        VISION_MODEL_DIR_ENV_VAR,
        VISION_DEVICE_ENV_VAR,
        VISION_DEVICE_INDEX_ENV_VAR,
        VISION_ALLOW_DOWNLOAD_ENV_VAR,
    )}

    config = QwenVisionRuntimeConfig.from_env_file(env_file, environ={})

    assert config.model_dir == Path("models/qwen3-vl")
    assert {key: os.environ.get(key) for key in before} == before


def test_process_environment_overrides_selected_env_file_values(tmp_path: Path) -> None:
    env_file = tmp_path / ".vision.env"
    env_file.write_text(
        "SKETCH2LIFE_VISION_MODEL_DIR=file-model\nSKETCH2LIFE_VISION_DEVICE=cpu\n",
        encoding="utf-8",
    )
    config = QwenVisionRuntimeConfig.from_env_file(
        env_file,
        environ={
            VISION_MODEL_CACHE_DIR_ENV_VAR: "env-cache",
            VISION_DEVICE_ENV_VAR: "cuda",
        },
    )
    assert config.model_dir == Path("file-model")
    assert config.model_cache_dir == Path("env-cache")
    assert config.device == "cuda"


@pytest.mark.parametrize(
    "environment",
    (
        {VISION_MODEL_DIR_ENV_VAR: "model", VISION_DEVICE_INDEX_ENV_VAR: "-1"},
        {VISION_MODEL_DIR_ENV_VAR: "model", VISION_DEVICE_INDEX_ENV_VAR: "not-an-int"},
        {VISION_MODEL_DIR_ENV_VAR: "model", VISION_ALLOW_DOWNLOAD_ENV_VAR: "sometimes"},
    ),
)
def test_runtime_config_rejects_invalid_device_or_download_values(
    environment: dict[str, str],
) -> None:
    with pytest.raises(RuntimeError):
        QwenVisionRuntimeConfig.from_env(environment)
