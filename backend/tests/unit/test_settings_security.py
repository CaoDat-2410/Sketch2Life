from pathlib import Path

import pytest
from pydantic import ValidationError

from sketch2life.infrastructure.config.settings import Settings


def test_production_rejects_development_identity() -> None:
    with pytest.raises(ValidationError, match="Firebase Authentication"):
        Settings(env="production", ai_provider="runpod")


def test_production_rejects_lightning_provider() -> None:
    with pytest.raises(ValidationError, match="Runpod AI provider"):
        Settings(
            env="production",
            auth_provider="firebase",
            firebase_project_id="fixture-project",
            ai_provider="lightning_dev",
        )


def test_production_accepts_firebase_and_runpod_runtime_references() -> None:
    settings = Settings(
        env="production",
        auth_provider="firebase",
        firebase_project_id="fixture-project",
        ai_provider="runpod",
        runpod_endpoint_id="fixture-endpoint",
        runpod_api_key_file=Path("/runtime/secrets/runpod-key"),
    )

    assert settings.auth_provider == "firebase"
    assert settings.ai_provider == "runpod"
