from __future__ import annotations

import inspect

import pytest

from sketch2life.infrastructure.ai import modal_function_client
from sketch2life.infrastructure.ai.modal_function_client import (
    STORY_MODEL_ID,
    STORY_MODEL_REVISION,
    ModalDrawingFunctionClient,
    ModalJsonFunctionClient,
    ModalStoryFunctionClient,
)
from sketch2life.infrastructure.config.settings import Settings


def test_unpinned_override_setting_is_retired() -> None:
    settings = Settings(_env_file=None)
    assert "qwen38_allow_unpinned_dev" not in Settings.model_fields
    assert not hasattr(settings, "qwen38_allow_unpinned_dev")


@pytest.mark.parametrize("env", ["staging", "production"])
def test_legacy_unpinned_environment_variable_cannot_unlock_dispatch(
    env: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SKETCH2LIFE_QWEN38_ALLOW_UNPINNED_DEV", "true")
    settings = Settings(_env_file=None, env=env)
    assert not hasattr(settings, "qwen38_allow_unpinned_dev")


@pytest.mark.parametrize("kind", ["drawing", "json", "story"])
def test_clients_have_no_unpinned_profile_override(kind: str) -> None:
    constructors = {
        "drawing": ModalDrawingFunctionClient,
        "json": ModalJsonFunctionClient,
        "story": ModalStoryFunctionClient,
    }
    parameters = set(inspect.signature(constructors[kind]).parameters)
    assert "qwen_profile" not in parameters
    assert "profile" not in parameters
    assert "settings" not in parameters


@pytest.mark.parametrize("kind", ["drawing", "json", "story"])
def test_default_profile_behavior_is_the_dev_pin(kind: str) -> None:
    del kind  # all three adapters share the source-level model identity
    assert (STORY_MODEL_ID, STORY_MODEL_REVISION) == (
        "Qwen/Qwen3.8-27B-FP8",
        "c3a462cc3d38cf351f3b26cbd763469eeb74ef81",
    )
    assert modal_function_client.MODEL_ID == STORY_MODEL_ID
    assert modal_function_client.MODEL_REVISION == STORY_MODEL_REVISION


def test_backend_source_has_no_unpinned_dispatch_flag() -> None:
    source = inspect.getsource(modal_function_client)
    assert "qwen38_allow_unpinned_dev" not in source
    assert "STORY_Q38_CHECKPOINT_MANIFEST_SHA256" not in source


def test_story_worker_input_profile_is_v3_only() -> None:
    source = inspect.getsource(ModalStoryFunctionClient.generate)
    assert '"sketch2life.story-generation-input.v3"' in source
    assert '"sketch2life.story-generation-input.v4"' not in source
    assert '"sketch2life.story-generation-input.v1"' not in source


def test_story_client_wait_bound_remains_capped_at_thirty_minutes() -> None:
    with pytest.raises(ValueError, match="timeout"):
        ModalStoryFunctionClient(volume=object(), function=object(), timeout_seconds=1_801)
