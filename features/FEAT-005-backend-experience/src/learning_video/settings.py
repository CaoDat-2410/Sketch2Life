"""Typed YAML configuration for the standalone learning-media POC."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SettingsModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class WanSettings(SettingsModel):
    provider: str = Field(pattern=r"^(mock|wan2\.2)$")
    model_name: str = Field(min_length=1)
    python_binary: str = Field(min_length=1)
    inference_script: Path
    checkpoint_dir: Path
    output_dir: Path
    offload_model: bool = True
    convert_model_dtype: bool = True
    t5_cpu: bool = True


class VideoSettings(SettingsModel):
    min_duration_sec: int = Field(ge=1)
    max_duration_sec: int = Field(le=10)
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    fps: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_duration_range(self) -> VideoSettings:
        if self.min_duration_sec > self.max_duration_sec:
            raise ValueError("min_duration_sec must not exceed max_duration_sec")
        return self


class RuntimeSettings(SettingsModel):
    max_retries: int = Field(ge=0, le=1)


class AppSettings(SettingsModel):
    wan: WanSettings
    video: VideoSettings
    runtime: RuntimeSettings


def load_settings(path: Path) -> AppSettings:
    """Load and validate one YAML profile."""

    try:
        import yaml
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "PyYAML is required to load learning-video configuration; install PyYAML>=6,<7"
        ) from exc

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("settings file must contain a top-level mapping")
    return AppSettings.model_validate(data)
