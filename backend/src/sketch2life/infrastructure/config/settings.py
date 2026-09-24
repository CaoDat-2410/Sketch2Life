"""Settings for the backend-only live Lightning development adapter."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal, Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    _BACKEND_ROOT = Path(__file__).resolve().parents[4]
    model_config = SettingsConfigDict(
        env_prefix="SKETCH2LIFE_",
        # Keep local startup deterministic when uvicorn is launched from the repo root.
        # The process environment still wins over both files.
        env_file=(_BACKEND_ROOT / ".env", ".env"),
    )

    env: Literal["local", "test", "staging", "production"] = "local"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"
    session_idle_ttl_seconds: int = Field(default=1800, ge=60, le=86_400)

    auth_provider: Literal["development", "firebase"] = "development"
    firebase_project_id: str = ""
    firebase_credentials_file: Path | None = None
    firebase_check_revoked_tokens: bool = True

    # Backend-only AI connectivity. Lightning is development; Runpod is production.
    ai_provider: Literal["disabled", "lightning_dev", "runpod"] = "disabled"
    lightning_ai_base_url: str = ""
    lightning_ai_token_file: Path | None = None
    lightning_model_profile: str = "live-p2-understanding-v1"
    lightning_asr_profile: str = "WHISPER_TURBO_FP16_AUTO_V1"
    lightning_asr_path: str = "/v1/asr"
    lightning_vision_path: str = "/v1/vision"
    lightning_vision_v2_path: str = "/v2/vision"
    lightning_whiteboard_localization_path: str = "/v1/whiteboard/localize"
    lightning_whiteboard_segmentation_path: str = "/v1/whiteboard/segment"
    whiteboard_video_enabled: bool = False
    whiteboard_video_auto_run: bool = False
    whiteboard_video_artifact_root: Path = Path(".runtime/whiteboard")
    whiteboard_video_max_size_bytes: int = Field(default=12 * 1024 * 1024, ge=1)
    whiteboard_learning_thread_fixture: Path | None = None
    whiteboard_tts_executable: str = "espeak-ng"
    whiteboard_ffmpeg_executable: str = "ffmpeg"
    live_fixture_root: Path | None = None
    runpod_endpoint_id: str = ""
    runpod_api_key_file: Path | None = None
    ai_connect_timeout_seconds: float = 5.0
    ai_request_timeout_seconds: float = 120.0

    @model_validator(mode="after")
    def enforce_deployment_provider_policy(self) -> Self:
        if self.env in {"staging", "production"} and (
            self.auth_provider != "firebase" or not self.firebase_project_id
        ):
            raise ValueError("staging/production requires configured Firebase Authentication")

        if self.env == "production":
            if self.ai_provider != "runpod":
                raise ValueError("production requires the approved Runpod AI provider")
            if not self.runpod_endpoint_id or self.runpod_api_key_file is None:
                raise ValueError("production Runpod endpoint and key file are required")

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
