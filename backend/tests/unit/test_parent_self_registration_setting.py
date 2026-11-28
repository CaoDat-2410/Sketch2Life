from __future__ import annotations

import pytest
from pydantic import ValidationError

from sketch2life.infrastructure.config.settings import Settings


def test_parent_self_registration_setting_defaults_to_false(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SKETCH2LIFE_PARENT_SELF_REGISTRATION_ENABLED", raising=False)

    settings = Settings(_env_file=None, env="test")

    assert settings.parent_self_registration_enabled is False


@pytest.mark.parametrize("environment", ["local", "test"])
def test_parent_self_registration_can_be_enabled_in_local_and_test(
    environment: str,
) -> None:
    settings = Settings(
        _env_file=None,
        env=environment,
        parent_self_registration_enabled=True,
    )

    assert settings.parent_self_registration_enabled is True


@pytest.mark.parametrize("environment", ["staging", "production"])
def test_parent_self_registration_true_is_rejected_outside_local_and_test(
    environment: str,
) -> None:
    with pytest.raises(
        ValidationError,
        match="Parent self-registration is available only in local/test",
    ):
        Settings(
            _env_file=None,
            env=environment,
            parent_self_registration_enabled=True,
        )


def test_parent_self_registration_setting_reads_its_named_environment_variable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SKETCH2LIFE_PARENT_SELF_REGISTRATION_ENABLED", "true")

    settings = Settings(_env_file=None, env="test")

    assert settings.parent_self_registration_enabled is True
