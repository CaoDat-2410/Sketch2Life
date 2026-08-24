"""Typed runtime settings; secrets come from environment variables."""

from functools import lru_cache
from pathlib import Path
from typing import Literal, Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SKETCH2LIFE_", env_file=".env")

    env: Literal["local", "test", "staging", "production"] = "local"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"

    auth_provider: Literal["development", "firebase"] = "development"
    firebase_project_id: str = ""
    firebase_credentials_file: Path | None = None
    firebase_check_revoked_tokens: bool = True

    # Backend-only AI connectivity. Lightning is fixture/dev; Runpod is production.
    # The mobile application never receives provider endpoints or credentials.
    ai_provider: Literal["disabled", "lightning_dev", "runpod"] = "disabled"
    lightning_ai_base_url: str = ""
    lightning_ai_token_file: Path | None = None
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
