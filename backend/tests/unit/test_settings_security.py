from pathlib import Path

import pytest
from pydantic import ValidationError

from sketch2life.infrastructure.config.settings import CoreDatabaseSettings, Settings


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


def test_default_pixi_planner_path_matches_adaptive_v4_contract() -> None:
    assert Settings().lightning_pixi_show_path == "/v4/pixi/show-plan"


def test_shared_environment_ignores_keys_owned_by_client_apps() -> None:
    settings = Settings(
        _env_file=None,
        auth_provider="firebase",
        firebase_project_id="synthetic-project",
        firebase_admin_json_base64="c3ludGhldGlj",
        vite_firebase_api_key="public-client-key",
    )
    database_settings = CoreDatabaseSettings(
        _env_file=None,
        vite_firebase_api_key="public-client-key",
    )

    assert settings.firebase_project_id == "synthetic-project"
    assert settings.firebase_admin_json_base64 is not None
    assert settings.firebase_admin_json_base64.get_secret_value() == "c3ludGhldGlj"
    assert database_settings.database_url is None


@pytest.mark.parametrize("env", ["local", "test"])
def test_pixi_sprite_dev_preview_requires_explicit_local_test_flag(env: str) -> None:
    assert Settings(env=env).pixi_sprite_cycle_dev_preview_allowed is False
    assert (
        Settings(
            env=env,
            pixi_sprite_cycle_dev_preview_enabled=True,
        ).pixi_sprite_cycle_dev_preview_allowed
        is True
    )


@pytest.mark.parametrize("env", ["staging", "production"])
def test_pixi_sprite_dev_preview_cannot_be_enabled_outside_local_test(env: str) -> None:
    settings = Settings(
        env=env,
        auth_provider="firebase",
        firebase_project_id="fixture-project",
        ai_provider="runpod" if env == "production" else "disabled",
        runpod_endpoint_id="fixture-endpoint" if env == "production" else "",
        runpod_api_key_file=Path("/runtime/secrets/runpod-key") if env == "production" else None,
        pixi_sprite_cycle_dev_preview_enabled=True,
    )

    assert settings.pixi_sprite_cycle_dev_preview_allowed is False
