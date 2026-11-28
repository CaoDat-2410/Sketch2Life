# ruff: noqa: E501, F811, SIM117, B023
"""Missing contract tests for E5 T-CONSENT1 named in IMPL_REVIEW_E_E5_R1_20261125.md and E5_PROMPT.md."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError
from test_parent_consent_policy_route import (  # noqa: F401
    PATH,
    _assert_error,
    _headers,
    consent_client,
)

import sketch2life.interfaces.http.app as app_module
from sketch2life.infrastructure.persistence.be1_parent_role_adapter import Be1ParentRoleAdapter
from sketch2life.interfaces.http.be1_runtime import get_runtime
from sketch2life.interfaces.http.openapi_contract import MOUNTED_OPERATIONS
from sketch2life.interfaces.http.openapi_srs_v22 import (
    SRS_V22_INCLUDED_OPERATIONS,
    SRS_V22_OPERATION_TAGS,
)
from sketch2life.interfaces.http.routers.parent_consent_policy import get_consent_role_reader


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_non_get_methods_are_rejected_with_405_action_not_allowed(
    consent_client: tuple[TestClient, FastAPI, dict[str, bool]],
    method: str,
) -> None:
    """covers: IMPL_REVIEW_E_E5_R1_20261125.md Not verified (405 ACTION_NOT_ALLOWED across non-GET methods)"""
    client, _application, _state = consent_client

    response = getattr(client, method)(PATH, headers=_headers())

    _assert_error(response, status=405, code="ACTION_NOT_ALLOWED", retryable=False)


def test_get_consent_role_reader_returns_503_database_not_configured_without_session_factory(
    consent_client: tuple[TestClient, FastAPI, dict[str, bool]],
) -> None:
    """covers: IMPL_REVIEW_E_E5_R1_20261125.md Conformance (E5_PROMPT §3 503 DATABASE_NOT_CONFIGURED)"""
    client, application, _state = consent_client
    application.dependency_overrides.pop(get_consent_role_reader)

    response = client.get(PATH, headers=_headers())

    _assert_error(response, status=503, code="DATABASE_NOT_CONFIGURED", retryable=True)


def test_get_consent_role_reader_wraps_session_factory_and_maps_sqlalchemy_error_to_503(
    consent_client: tuple[TestClient, FastAPI, dict[str, bool]],
) -> None:
    """covers: IMPL_REVIEW_E_E5_R1_20261125.md Conformance (real get_consent_role_reader + Be1ParentRoleAdapter 503)"""
    client, application, _state = consent_client
    application.dependency_overrides.pop(get_consent_role_reader)

    class _FailingSession:
        def __enter__(self) -> _FailingSession:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def execute(self, *_args: object, **_kwargs: object) -> Any:
            raise SQLAlchemyError("simulated database outage")

    runtime = SimpleNamespace(session_factory=lambda: _FailingSession(), database_error=None)
    assert isinstance(get_consent_role_reader(runtime=runtime), Be1ParentRoleAdapter)  # type: ignore[arg-type]

    application.dependency_overrides[get_runtime] = lambda: runtime
    response = client.get(PATH, headers=_headers())

    _assert_error(response, status=503, code="DATABASE_UNAVAILABLE", retryable=True)


def test_banned_mobile_path_and_other_app_profiles_do_not_expose_consent_policy(
    consent_client: tuple[TestClient, FastAPI, dict[str, bool]],
) -> None:
    """covers: IMPL_REVIEW_E_E5_R1_20261125.md Conformance & E5_PROMPT §6 R2 (banned path & classroom/demo isolation)"""
    client, _application, _state = consent_client

    banned = client.get("/api/parent/v1/consent-policy", headers=_headers())
    assert banned.status_code == 404

    for other_app in (app_module.create_classroom_app(), app_module.create_demo_app()):
        assert PATH not in other_app.openapi()["paths"]


def test_openapi_catalog_entry_and_srs_v22_projection_match_e5_contract() -> None:
    """covers: IMPL_REVIEW_E_E5_R1_20261125.md P3-1 (E5 catalog entry and SRS v2.2 metadata verified directly)"""
    key = ("get", PATH)
    assert key in MOUNTED_OPERATIONS
    entry = MOUNTED_OPERATIONS[key]
    assert entry["handler"] == "parent_consent_policy.py::get_parent_consent_policy"
    assert entry["tag"] == "Parent Profiles"
    responses = {item["status"]: item["schema_name"] for item in entry["responses"]}
    assert responses == {
        "200": "ParentConsentPolicyV1",
        "401": "Be1Error",
        "403": "Be1Error",
        "503": "Be1Error",
    }
    assert key in SRS_V22_INCLUDED_OPERATIONS
    assert SRS_V22_OPERATION_TAGS[key] == "Parent Profiles"
