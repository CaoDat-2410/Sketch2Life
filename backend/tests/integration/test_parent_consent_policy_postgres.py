"""PostgreSQL role checks for the read-only Parent consent-policy route (T-CONSENT1)."""

from __future__ import annotations

import os
from collections.abc import Iterator
from typing import Any
from uuid import uuid4

import pytest
from fastapi import Header
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.engine import make_url

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    Be1CommandReceiptModel,
)
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult

PATH = "/v1/parent/consent-policy"
ISSUER = "synthetic-t-consent1-issuer"
FORBIDDEN_DATABASES = {"sketch2life", "sketch2life_m2_s1a"}
FORBIDDEN_PORTS = {5432, 5433, 8000, 55439}


def _add_identity(
    db: Any,
    subject: str,
    role: str,
    *,
    state: str = "active",
    issuer: str = ISSUER,
) -> None:
    db.add(
        AdultIdentityModel(
            subject=subject,
            issuer=issuer,
            state=state,
            account_role=role,
        )
    )
    db.flush()


def _row_counts(session_factory: Any) -> tuple[int | None, int | None]:
    with session_factory() as db:
        return (
            db.scalar(select(func.count()).select_from(AdultIdentityModel)),
            db.scalar(select(func.count()).select_from(Be1CommandReceiptModel)),
        )


@pytest.fixture
def consent_directory(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[TestClient, Any, dict[str, str]]]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL to a disposable PostgreSQL database")
    parsed_url = make_url(database_url)
    database_name = (parsed_url.database or "").lower()
    if database_name in FORBIDDEN_DATABASES:
        pytest.fail("BE1_TEST_DATABASE_URL must not point to a protected database")
    if "be1_acceptance" not in database_name or "frc08" not in database_name:
        pytest.fail("BE1_TEST_DATABASE_URL must be a disposable frc08*be1_acceptance db")
    if (parsed_url.port or 5432) in FORBIDDEN_PORTS:
        pytest.fail("BE1_TEST_DATABASE_URL must not use a protected port")

    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", database_url)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "development")
    monkeypatch.setenv("SKETCH2LIFE_AI_PROVIDER", "disabled")
    monkeypatch.delenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", raising=False)
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()

    application = create_app()
    runtime = application.state.be1_runtime
    if runtime.engine is None or runtime.session_factory is None:
        pytest.fail("PostgreSQL runtime did not initialize")

    token = uuid4().hex[:8]
    subjects = {
        "parent": f"synthetic-t-consent1-parent-{token}",
        "teacher": f"synthetic-t-consent1-teacher-{token}",
        "disabled": f"synthetic-t-consent1-disabled-{token}",
    }
    with runtime.session_factory.begin() as db:
        _add_identity(db, subjects["parent"], "parent")
        _add_identity(db, subjects["teacher"], "teacher")
        _add_identity(db, subjects["disabled"], "parent", state="disabled")

    async def verified_adult(
        x_test_principal: str = Header(alias="X-Test-Principal"),
        x_test_issuer: str = Header(default=ISSUER, alias="X-Test-Issuer"),
    ) -> VerifiedPrincipal:
        return VerifiedPrincipal(
            subject=x_test_principal,
            issuer=x_test_issuer,
            roles=frozenset(),
        )

    application.dependency_overrides[get_verified_adult] = verified_adult
    try:
        with TestClient(application) as client:
            yield client, runtime.session_factory, subjects
    finally:
        application.dependency_overrides.clear()
        runtime.engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def _headers(subject: str) -> dict[str, str]:
    return {
        "X-Test-Principal": subject,
        "X-Test-Issuer": ISSUER,
    }


def test_parent_consent_policy_checks_real_parent_role_without_writes(
    consent_directory: tuple[TestClient, Any, dict[str, str]],
) -> None:
    client, session_factory, subjects = consent_directory
    before = _row_counts(session_factory)

    parent = client.get(PATH, headers=_headers(subjects["parent"]))
    teacher = client.get(PATH, headers=_headers(subjects["teacher"]))
    disabled = client.get(PATH, headers=_headers(subjects["disabled"]))

    assert parent.status_code == 200
    assert parent.json()["policy"]["purpose_code"] == "SYNTHETIC_TEST_ONLY"
    assert teacher.status_code == 403
    assert teacher.json()["code"] == "ACTION_NOT_ALLOWED"
    assert disabled.status_code == 403
    assert disabled.json()["code"] == "ACTION_NOT_ALLOWED"
    assert _row_counts(session_factory) == before
