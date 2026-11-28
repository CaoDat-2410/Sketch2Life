from __future__ import annotations

import inspect

from sketch2life.infrastructure.ai import modal_function_client as client_module
from sketch2life.infrastructure.ai.modal_function_client import (
    MODEL_ID,
    MODEL_REVISION,
    QWEN_MODEL_ID,
    QWEN_MODEL_REVISION,
    STORY_MODEL_ID,
    STORY_MODEL_REVISION,
    ModalDrawingFunctionClient,
    ModalJsonFunctionClient,
    ModalStoryFunctionClient,
)
from sketch2life.infrastructure.config.settings import Settings


def test_dev_model_identity_is_the_single_backend_identity() -> None:
    expected = ("Qwen/Qwen3.8-27B-FP8", "c3a462cc3d38cf351f3b26cbd763469eeb74ef81")
    assert (MODEL_ID, MODEL_REVISION) == expected
    assert (QWEN_MODEL_ID, QWEN_MODEL_REVISION) == expected
    assert (STORY_MODEL_ID, STORY_MODEL_REVISION) == expected
    assert (client_module.MODEL_ID, client_module.MODEL_REVISION) == expected


def test_settings_has_no_model_profile_or_unpinned_override_fields() -> None:
    fields = set(Settings.model_fields)
    assert "modal_qwen_profile" not in fields
    assert "story_generation_profile" not in fields
    assert "qwen38_allow_unpinned_dev" not in fields


def test_legacy_profile_environment_variables_cannot_switch_the_dev_pin(monkeypatch) -> None:
    monkeypatch.setenv("SKETCH2LIFE_MODAL_QWEN_PROFILE", "qwen35")
    monkeypatch.setenv("SKETCH2LIFE_STORY_GENERATION_PROFILE", "v1_qwen35")
    monkeypatch.setenv("SKETCH2LIFE_QWEN38_ALLOW_UNPINNED_DEV", "true")
    Settings(_env_file=None)

    assert (STORY_MODEL_ID, STORY_MODEL_REVISION) == (
        "Qwen/Qwen3.8-27B-FP8",
        "c3a462cc3d38cf351f3b26cbd763469eeb74ef81",
    )


def test_story_client_has_no_profile_or_settings_selector() -> None:
    parameters = set(inspect.signature(ModalStoryFunctionClient).parameters)
    assert {"volume", "function", "timeout_seconds"} <= parameters
    assert "profile" not in parameters and "settings" not in parameters


def test_drawing_client_has_no_qwen_profile_selector() -> None:
    parameters = set(inspect.signature(ModalDrawingFunctionClient).parameters)
    assert {"volume", "function", "timeout_seconds"} <= parameters
    assert "qwen_profile" not in parameters and "settings" not in parameters


def test_json_client_has_no_qwen_profile_selector() -> None:
    parameters = set(inspect.signature(ModalJsonFunctionClient).parameters)
    assert {"volume", "function_resolver", "timeout_seconds"} <= parameters
    assert "qwen_profile" not in parameters and "settings" not in parameters


def test_model_client_source_contains_no_retired_profile_api() -> None:
    source = inspect.getsource(client_module)
    for retired_name in (
        "STORY_Q38_PROFILE",
        "STORY_V1_PROFILE",
        "DEFAULT_STORY_PROFILE",
        "qwen38_allow_unpinned_dev",
    ):
        assert retired_name not in source
