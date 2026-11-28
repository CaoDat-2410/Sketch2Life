from __future__ import annotations

import pytest

from sketch2life.infrastructure.config.settings import Settings
from sketch2life.infrastructure.identity.firebase_token_verifier import FirebaseTokenVerifier


@pytest.mark.parametrize("application_env", ["production", "staging"])
def test_emulator_host_is_refused_outside_local_test(
    monkeypatch: pytest.MonkeyPatch, application_env: str
) -> None:
    monkeypatch.setenv("FIREBASE_AUTH_EMULATOR_HOST", "firebase-auth:9099")
    settings = Settings.model_construct(env=application_env)

    with pytest.raises(
        ValueError,
        match="FIREBASE_AUTH_EMULATOR_HOST is permitted only when SKETCH2LIFE_ENV is local or test",
    ):
        FirebaseTokenVerifier(settings)


@pytest.mark.parametrize("application_env", ["local", "test"])
def test_emulator_host_is_allowed_in_local_test(
    monkeypatch: pytest.MonkeyPatch, application_env: str
) -> None:
    monkeypatch.setenv("FIREBASE_AUTH_EMULATOR_HOST", "firebase-auth:9099")
    settings = Settings.model_construct(env=application_env)

    assert isinstance(FirebaseTokenVerifier(settings), FirebaseTokenVerifier)


def test_missing_emulator_host_preserves_staging_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("FIREBASE_AUTH_EMULATOR_HOST", raising=False)
    settings = Settings.model_construct(env="staging")

    verifier = FirebaseTokenVerifier(settings)

    assert verifier._settings.env == "staging"
