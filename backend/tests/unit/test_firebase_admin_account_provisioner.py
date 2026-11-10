from __future__ import annotations

import pytest
from firebase_admin import auth

from sketch2life.application.ports.identity import (
    IdentityAccountConflict,
    IdentityAccountProvisioningUnavailable,
)
from sketch2life.infrastructure.config.settings import Settings
from sketch2life.infrastructure.identity import firebase_admin_account_provisioner as adapter


def settings() -> Settings:
    return Settings(
        env="local",
        auth_provider="firebase",
        firebase_project_id="synthetic-project",
    )


def test_creates_unverified_identity_without_role_claims(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(adapter, "get_firebase_admin_app", lambda _settings: "fake-app")
    monkeypatch.setattr(
        auth,
        "create_user",
        lambda **kwargs: calls.append(kwargs),
    )

    adapter.FirebaseAdminAccountProvisioner(settings()).create_password_account(
        email="parent@example.test",
        password="synthetic-password",
    )

    assert calls == [
        {
            "email": "parent@example.test",
            "password": "synthetic-password",
            "email_verified": False,
            "disabled": False,
            "app": "fake-app",
        }
    ]
    assert "custom_claims" not in calls[0]


def test_maps_existing_email_to_generic_identity_conflict(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(adapter, "get_firebase_admin_app", lambda _settings: "fake-app")

    def create_user(**_kwargs: object) -> None:
        raise auth.EmailAlreadyExistsError(
            "email already registered", cause=None, http_response=None
        )

    monkeypatch.setattr(auth, "create_user", create_user)

    with pytest.raises(IdentityAccountConflict) as error:
        adapter.FirebaseAdminAccountProvisioner(settings()).create_password_account(
            email="parent@example.test",
            password="synthetic-password",
        )

    assert str(error.value) == ""


def test_hides_firebase_provider_exception_details(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(adapter, "get_firebase_admin_app", lambda _settings: "fake-app")

    def create_user(**_kwargs: object) -> None:
        raise RuntimeError("private provider payload")

    monkeypatch.setattr(auth, "create_user", create_user)

    with pytest.raises(IdentityAccountProvisioningUnavailable) as error:
        adapter.FirebaseAdminAccountProvisioner(settings()).create_password_account(
            email="parent@example.test",
            password="synthetic-password",
        )

    assert "private provider payload" not in str(error.value)
