"""Unit tests for local-only faster-whisper runtime path configuration."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from sketch2life.infrastructure.ai import faster_whisper_runtime_config
from sketch2life.infrastructure.ai.faster_whisper_runtime_config import (
    FasterWhisperRuntimeConfig,
)


def test_from_env_reads_direct_model_and_native_library_paths(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    native_library_dir = tmp_path / "native-libraries"
    model_dir.mkdir()
    native_library_dir.mkdir()

    config = FasterWhisperRuntimeConfig.from_env(
        {
            "SKETCH2LIFE_ASR_MODEL_DIR": str(model_dir),
            "SKETCH2LIFE_ASR_NATIVE_LIBRARY_DIR": str(native_library_dir),
        }
    )

    assert config.model_dir == model_dir
    assert config.model_cache_dir is None
    assert config.native_library_dir == native_library_dir


def test_from_env_keeps_hugging_face_cache_fallback_for_nonlocal_runtime(tmp_path: Path) -> None:
    cache_dir = tmp_path / "hub-cache"

    config = FasterWhisperRuntimeConfig.from_env(
        {"SKETCH2LIFE_ASR_MODEL_CACHE_DIR": str(cache_dir)}
    )

    assert config.model_dir is None
    assert config.model_cache_dir == cache_dir
    assert config.native_library_dir is None


def test_from_env_rejects_missing_model_source() -> None:
    with pytest.raises(RuntimeError, match="MODEL_DIR.*MODEL_CACHE_DIR"):
        FasterWhisperRuntimeConfig.from_env({})


def test_from_env_file_prefers_actual_environment_over_local_file(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("SKETCH2LIFE_ASR_MODEL_DIR=file-model\n", encoding="utf-8")

    config = FasterWhisperRuntimeConfig.from_env_file(
        env_file, environ={"SKETCH2LIFE_ASR_MODEL_DIR": "process-model"}
    )

    assert config.model_dir == Path("process-model")


def test_native_library_directory_is_added_only_to_the_current_process(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    native_library_dir = tmp_path / "native-libraries"
    native_library_dir.mkdir()
    config = FasterWhisperRuntimeConfig(native_library_dir=native_library_dir)
    added_directories: list[str] = []
    faster_whisper_runtime_config._DLL_DIRECTORY_HANDLES.clear()  # noqa: SLF001
    monkeypatch.setenv("PATH", "existing-path")
    monkeypatch.setattr(
        faster_whisper_runtime_config.os,
        "add_dll_directory",
        lambda value: added_directories.append(value) or object(),
    )

    config.enable_native_libraries_for_current_process()
    config.enable_native_libraries_for_current_process()

    assert added_directories == [str(native_library_dir.resolve())]
    assert Path(os.environ["PATH"].split(os.pathsep)[0]) == native_library_dir.resolve()
