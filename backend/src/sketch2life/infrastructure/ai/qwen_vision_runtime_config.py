"""Constructor-injected configuration for the local Qwen vision runtime.

This configuration is intentionally separate from the shared application
``Settings`` object.  It contains no provider credentials and has no default
model or cache path; callers must select one explicitly for a real run.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

_MODEL_DIR_ENV_VAR = "SKETCH2LIFE_VISION_MODEL_DIR"
_MODEL_CACHE_DIR_ENV_VAR = "SKETCH2LIFE_VISION_MODEL_CACHE_DIR"
_DEVICE_ENV_VAR = "SKETCH2LIFE_VISION_DEVICE"
_DEVICE_INDEX_ENV_VAR = "SKETCH2LIFE_VISION_DEVICE_INDEX"
_ALLOW_DOWNLOAD_ENV_VAR = "SKETCH2LIFE_VISION_ALLOW_MODEL_DOWNLOAD"

VISION_MODEL_DIR_ENV_VAR = _MODEL_DIR_ENV_VAR
VISION_MODEL_CACHE_DIR_ENV_VAR = _MODEL_CACHE_DIR_ENV_VAR
VISION_DEVICE_ENV_VAR = _DEVICE_ENV_VAR
VISION_DEVICE_INDEX_ENV_VAR = _DEVICE_INDEX_ENV_VAR
VISION_ALLOW_DOWNLOAD_ENV_VAR = _ALLOW_DOWNLOAD_ENV_VAR


@dataclass(frozen=True, slots=True)
class QwenVisionRuntimeConfig:
    """Explicit local runtime paths and device selection for the Qwen adapter."""

    model_dir: Path | None = None
    model_cache_dir: Path | None = None
    device: str = "cuda"
    device_index: int = 0
    allow_model_download: bool = False

    def __post_init__(self) -> None:
        if self.model_dir is None and self.model_cache_dir is None:
            raise ValueError(
                "model_dir or model_cache_dir must be explicitly configured; "
                "there is no default Qwen model path"
            )
        if self.device_index < 0:
            raise ValueError("device_index must be non-negative")

    @classmethod
    def from_env(cls, environ: Mapping[str, str]) -> QwenVisionRuntimeConfig:
        """Build configuration from explicit environment names without path defaults."""

        raw_model_dir = environ.get(_MODEL_DIR_ENV_VAR, "").strip()
        raw_cache_dir = environ.get(_MODEL_CACHE_DIR_ENV_VAR, "").strip()
        if not raw_model_dir and not raw_cache_dir:
            raise RuntimeError(
                f"{_MODEL_DIR_ENV_VAR} or {_MODEL_CACHE_DIR_ENV_VAR} must be set; "
                "there is no default Qwen model path"
            )

        raw_device = environ.get(_DEVICE_ENV_VAR, "cuda").strip() or "cuda"
        raw_device_index = environ.get(_DEVICE_INDEX_ENV_VAR, "0").strip() or "0"
        try:
            device_index = int(raw_device_index)
        except ValueError as exc:
            raise RuntimeError(f"{_DEVICE_INDEX_ENV_VAR} must be a non-negative integer") from exc
        if device_index < 0:
            raise RuntimeError(f"{_DEVICE_INDEX_ENV_VAR} must be a non-negative integer")

        raw_allow_download = environ.get(_ALLOW_DOWNLOAD_ENV_VAR, "false").strip().lower()
        if raw_allow_download not in {"true", "false"}:
            raise RuntimeError(f"{_ALLOW_DOWNLOAD_ENV_VAR} must be true or false")

        return cls(
            model_dir=Path(raw_model_dir) if raw_model_dir else None,
            model_cache_dir=Path(raw_cache_dir) if raw_cache_dir else None,
            device=raw_device,
            device_index=device_index,
            allow_model_download=raw_allow_download == "true",
        )

    @classmethod
    def from_env_file(
        cls, env_file: Path, *, environ: Mapping[str, str] | None = None
    ) -> QwenVisionRuntimeConfig:
        """Read an explicitly selected local env file without mutating the process."""

        file_values = _read_env_file(env_file)
        merged = {**file_values, **(os.environ if environ is None else environ)}
        return cls.from_env(merged)

    def model_reference(self, model_identifier: str) -> str:
        """Return the explicit local snapshot or remote model identifier."""

        if self.model_dir is not None:
            return str(self.model_dir)
        return model_identifier


# Compatibility spelling for callers that use the shorter runtime name.
QwenRuntimeConfig = QwenVisionRuntimeConfig


def _read_env_file(env_file: Path) -> dict[str, str]:
    """Parse the small KEY=VALUE subset needed by the ignored local config file."""

    try:
        lines = env_file.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise RuntimeError("the selected Qwen runtime env file is unreadable") from exc

    values: dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("export "):
            stripped = stripped[7:].lstrip()
        key, separator, value = stripped.partition("=")
        if not separator or not key.strip():
            raise RuntimeError("the selected Qwen runtime env file contains an invalid entry")
        normalized_value = value.strip()
        if (
            len(normalized_value) >= 2
            and normalized_value[0] == normalized_value[-1]
            and normalized_value[0] in {"'", '"'}
        ):
            normalized_value = normalized_value[1:-1]
        values[key.strip()] = normalized_value
    return values


__all__ = [
    "QwenRuntimeConfig",
    "QwenVisionRuntimeConfig",
    "VISION_ALLOW_DOWNLOAD_ENV_VAR",
    "VISION_DEVICE_ENV_VAR",
    "VISION_DEVICE_INDEX_ENV_VAR",
    "VISION_MODEL_CACHE_DIR_ENV_VAR",
    "VISION_MODEL_DIR_ENV_VAR",
]
