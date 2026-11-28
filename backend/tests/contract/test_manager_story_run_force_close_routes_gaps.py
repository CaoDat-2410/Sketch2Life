"""HTTP contract tests for T-6c (Manager emergency force-close; not built yet)."""

from __future__ import annotations

from collections.abc import Iterator
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.contracts.schemas.manager_story_run_force_close import (
    ManagerActiveStoryRunConflictV1,
    ManagerForceClosedStoryRunV1,
)
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    OrganizationAssignmentModel,
)
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.openapi_contract import MOUNTED_OPERATIONS

_ORG = "synthetic-t6c-org"
_TEACHER = "synthetic-t6c-teacher"
_RUN = "11111111-1111-4111-8111-111111111111"
_MANAGER = "synthetic-t6c-manager"
_ISSUER = "synthetic-t6c-issuer"
_GET_OP = (
    "get",
    "/api/be1/v1/organizations/{organization_id}/teachers/{teacher_ref}/active-story-run-conflict",
)
_POST_OP = (
    "post",
    "/api/be1/v1/organizations/{organization_id}/story-runs/{run_id}/force-close",
)


@pytest.fixture(autouse=True)
def _offline_settings(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv(
        "SKETCH2LIFE_DATABASE_URL",
        "postgresql+psycopg://sentinel_user:sentinel_pw@localhost:9/sentinel_db",
    )
    monkeypatch.setenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", "0")
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    try:
        yield
    finally:
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


class _FakeScopeDb:
    def get(self, model: type, key: str) -> object | None:
        if model is AdultIdentityModel:
            return SimpleNamespace(
                subject=key, issuer=_ISSUER, state="active", account_role="school_manager"
            )
        return SimpleNamespace(organization_id=key, state="active")

    def scalars(self, _statement: object) -> object:
        rows = [
            OrganizationAssignmentModel(
                assignment_id=str(uuid4()),
                organization_id=_ORG,
                subject=_MANAGER,
                class_id=None,
                role="school_admin",
                active=True,
            )
        ]
        return SimpleNamespace(all=lambda: rows)

    def rollback(self) -> None:
        return None


def test_openapi_catalog_and_app_publish_both_force_close_routes() -> None:
    """covers: D_T-6C_PROMPT.md §3 & §6"""
    assert _GET_OP in MOUNTED_OPERATIONS
    assert _POST_OP in MOUNTED_OPERATIONS
    spec = create_app(_composition_profile="classroom").openapi()
    assert _GET_OP[1] in spec["paths"]
    assert "get" in spec["paths"][_GET_OP[1]]
    assert _POST_OP[1] in spec["paths"]
    assert "post" in spec["paths"][_POST_OP[1]]


def test_conflict_projection_schema_and_force_closed_response_contracts() -> None:
    """covers: D_T-6C_PROMPT.md §2 D3 & §3"""
    conflict = ManagerActiveStoryRunConflictV1(
        contract="ManagerActiveStoryRunConflictV1",
        run_id=_RUN,
        run_state="SCRIPT_REVIEW",
        revision=4,
    )
    closed = ManagerForceClosedStoryRunV1(
        contract="ManagerForceClosedStoryRunV1",
        run_id=_RUN,
        run_state="ABANDONED",
        revision=5,
    )
    assert set(conflict.model_dump(mode="json")) == {"contract", "run_id", "run_state", "revision"}
    assert set(closed.model_dump(mode="json")) == {"contract", "run_id", "run_state", "revision"}


@pytest.mark.parametrize(
    ("method", "path", "headers", "body"),
    [
        ("get", f"/api/be1/v1/organizations/{_ORG}/teachers/{_TEACHER}/active-story-run-conflict", {}, None),
        (
            "post",
            f"/api/be1/v1/organizations/{_ORG}/story-runs/{_RUN}/force-close",
            {"Idempotency-Key": "t6c-unauth-key"},
            {"expected_revision": 1, "reason": "Teacher left mid-session."},
        ),
    ],
)
def test_force_close_routes_require_authentication(
    method: str, path: str, headers: dict[str, str], body: dict[str, object] | None
) -> None:
    """covers: D_T-6C_PROMPT.md §3"""
    with TestClient(create_app(), raise_server_exceptions=False) as client:
        response = client.request(method, path, headers=headers, json=body)
    assert response.status_code == 401
    assert response.json()["code"] == "AUTH_REQUIRED"


@pytest.mark.parametrize(
    ("headers", "body"),
    [
        ({}, {"expected_revision": 1, "reason": "Valid reason."}),
        ({"Idempotency-Key": "bad key"}, {"expected_revision": 1, "reason": "Valid reason."}),
        ({"Idempotency-Key": "valid-key"}, {"expected_revision": 0, "reason": "Valid reason."}),
        ({"Idempotency-Key": "valid-key"}, {"expected_revision": 1, "reason": "   "}),
        ({"Idempotency-Key": "valid-key"}, {"expected_revision": 1, "reason": "a" * 501}),
        ({"Idempotency-Key": "valid-key"}, {"expected_revision": 1, "reason": "bad\nreason"}),
        (
            {"Idempotency-Key": "valid-key"},
            {"expected_revision": 1, "reason": "Valid reason.", "extra": True},
        ),
    ],
)
def test_force_close_rejects_bad_keys_reasons_revisions_and_extra_fields(
    headers: dict[str, str], body: dict[str, object]
) -> None:
    """covers: D_T-6C_PROMPT.md §3 & §6"""
    application = create_app(_composition_profile="classroom")
    application.dependency_overrides[get_verified_adult] = lambda: VerifiedPrincipal(
        subject=_MANAGER, issuer=_ISSUER, roles=frozenset()
    )
    application.dependency_overrides[get_db] = lambda: _FakeScopeDb()
    with TestClient(application, raise_server_exceptions=False) as client:
        response = client.post(
            f"/api/be1/v1/organizations/{_ORG}/story-runs/{_RUN}/force-close",
            headers=headers,
            json=body,
        )
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"
