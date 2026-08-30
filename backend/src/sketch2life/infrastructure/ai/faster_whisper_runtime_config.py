"""Standalone runtime configuration for the real faster-whisper adapter.

Constructor-injected only. Never added to `sketch2life.infrastructure.config.settings.Settings`
(the shared backend settings class) — Phase B introduces no HTTP/API/provider wiring and no
coupling to that class's production-deployment validator, per the approved Phase B scope.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import dotenv_values

_MODEL_CACHE_DIR_ENV_VAR = "SKETCH2LIFE_ASR_MODEL_CACHE_DIR"
_MODEL_DIR_ENV_VAR = "SKETCH2LIFE_ASR_MODEL_DIR"
_NATIVE_LIBRARY_DIR_ENV_VAR = "SKETCH2LIFE_ASR_NATIVE_LIBRARY_DIR"

# `os.add_dll_directory()` returns a handle whose lifetime controls the DLL search path.
# Retain one handle per directory for the process lifetime; this never changes the user's
# global Windows PATH and is a no-op on Linux cloud runtimes.
_DLL_DIRECTORY_HANDLES: dict[Path, Any] = {}


@dataclass(frozen=True, slots=True)
class FasterWhisperRuntimeConfig:
    """Environment-level runtime settings; per-profile decode settings live on `AsrProfileV1`."""

    model_dir: Path | None = None
    model_cache_dir: Path | None = None
    native_library_dir: Path | None = None
    device: str = "cuda"
    device_index: int = 0

    @classmethod
    def from_env(cls, environ: Mapping[str, str]) -> FasterWhisperRuntimeConfig:
        """Read explicit local model/runtime paths from the given environment mapping.

        A local snapshot (`SKETCH2LIFE_ASR_MODEL_DIR`) or a Hugging Face cache directory
        (`SKETCH2LIFE_ASR_MODEL_CACHE_DIR`) is required. `SKETCH2LIFE_ASR_NATIVE_LIBRARY_DIR`
        is optional because Linux cloud images provide CUDA libraries themselves. No default
        path exists anywhere in this class. Callers pass a mapping explicitly so this stays
        testable without real process environment.
        """

        raw_model_dir = environ.get(_MODEL_DIR_ENV_VAR, "").strip()
        raw_cache_dir = environ.get(_MODEL_CACHE_DIR_ENV_VAR, "").strip()
        raw_native_library_dir = environ.get(_NATIVE_LIBRARY_DIR_ENV_VAR, "").strip()
        if not raw_model_dir and not raw_cache_dir:
            raise RuntimeError(
                f"{_MODEL_DIR_ENV_VAR} or {_MODEL_CACHE_DIR_ENV_VAR} must be set; "
                "there is no default model path"
            )
        return cls(
            model_dir=Path(raw_model_dir) if raw_model_dir else None,
            model_cache_dir=Path(raw_cache_dir) if raw_cache_dir else None,
            native_library_dir=(
                Path(raw_native_library_dir) if raw_native_library_dir else None
            ),
        )

    @classmethod
    def from_env_file(
        cls, env_file: Path, *, environ: Mapping[str, str] | None = None
    ) -> FasterWhisperRuntimeConfig:
        """Read an explicitly selected ignored ASR env file without mutating `os.environ`.

        Process environment values win over file values, matching normal deployment behavior.
        This is deliberately separate from shared application `Settings`; local Windows callers
        pass `backend/.asr.env`, not the shared backend `.env` file.
        """

        file_values = {
            key: value
            for key, value in dotenv_values(env_file).items()
            if value is not None
        }
        merged = {**file_values, **(os.environ if environ is None else environ)}
        return cls.from_env(merged)

    def enable_native_libraries_for_current_process(self) -> None:
        """Expose configured Windows DLLs to this process only, if supplied.

        CTranslate2's native loader resolves its transitive CUDA dependencies through the
        process PATH on Windows. `add_dll_directory` is retained as the modern DLL search
        registration, while prepending the same directory to this Python process's PATH keeps
        CTranslate2's loader compatible. Neither operation modifies the global user/system
        PATH or survives process exit.
        """

        if self.native_library_dir is None or os.name != "nt":
            return
        resolved_dir = self.native_library_dir.resolve()
        if not resolved_dir.is_dir():
            raise RuntimeError(
                f"{_NATIVE_LIBRARY_DIR_ENV_VAR} does not name an existing directory"
            )
        directory_text = str(resolved_dir)
        current_path = os.environ.get("PATH", "")
        current_entries = current_path.split(os.pathsep) if current_path else []
        if directory_text not in current_entries:
            os.environ["PATH"] = (
                directory_text
                if not current_path
                else f"{directory_text}{os.pathsep}{current_path}"
            )
        if resolved_dir not in _DLL_DIRECTORY_HANDLES:
            add_dll_directory = getattr(os, "add_dll_directory", None)
            if add_dll_directory is None:
                raise RuntimeError("Windows DLL directory support is unavailable in this Python")
            _DLL_DIRECTORY_HANDLES[resolved_dir] = add_dll_directory(directory_text)
