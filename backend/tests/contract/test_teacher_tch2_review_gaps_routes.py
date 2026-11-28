# ruff: noqa: E501, F811, SIM117, B023
"""Offline contract tests for E2 (T-TCH2) review gaps across R1-R4 (R5 dropped)."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from sketch2life.application.ports.identity import IdentityAccountProfile, VerifiedPrincipal
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.infrastructure.lesson_occurrences.scope import LessonOccurrenceError
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.openapi_contract import (
    IDEMPOTENCY_MISMATCH_OPERATION_KEYS,
    MOUNTED_OPERATIONS,
)
from sketch2life.interfaces.http.openapi_contract_amendments import PORTFOLIO_OPERATION_KEY
from sketch2life.interfaces.http.routers.lesson_library import get_lesson_library_service
from sketch2life.interfaces.http.routers.lesson_occurrences import get_occurrence_service

TEACHER = VerifiedPrincipal(
    subject="teacher-subject",
    issuer="synthetic-issuer",
    roles=frozenset({"teacher"}),
)
NOW = datetime(2026, 11, 25, 12, 0, tzinfo=UTC)


class _FakeDatabase:
    def __init__(self, identity: Any = None, *, raise_sql: bool = False) -> None:
        self.identity = identity
        self.raise_sql = raise_sql
        self.rolled_back = False

    def get(self, model: Any, _key: Any) -> Any:
        if self.raise_sql:
            raise SQLAlchemyError("db down")
        if model is AdultIdentityModel:
            return self.identity
        return None

    def scalars(self, _statement: Any) -> Any:
        return SimpleNamespace(
            all=lambda: [
                SimpleNamespace(
                    organization_id="org-1",
                    subject="teacher-subject",
                    role="teacher",
                    class_id="class-1",
                    active=True,
                    assignment_id="assignment-1",
                )
            ]
        )

    def rollback(self) -> None:
        self.rolled_back = True


class _FakeIdentityProvider:
    def __init__(self, *, missing: bool = False, fail: bool = False) -> None:
        self.missing = missing
        self.fail = fail

    def get_account_profiles(self, subjects: list[str]) -> dict[str, IdentityAccountProfile]:
        if self.fail:
            raise RuntimeError("identity error")
        if self.missing:
            return {}
        return {
            subject: IdentityAccountProfile(
                subject=subject,
                email=None,
                display_name="Teacher One",
            )
            for subject in subjects
        }


class _FakeOccurrenceService:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.error: Exception | None = None

    def list_teacher_history(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return {
            "contract": "LessonOccurrencePageV1",
            "items": [],
            "next_cursor": None,
        }


class _FakeLessonLibraryService:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def list_teacher_activities(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        return {
            "contract": "TeacherActivityPageV1",
            "items": [],
            "next_cursor": None,
        }


@dataclass
class _Workspace:
    app: FastAPI
    client: TestClient
    db: _FakeDatabase = field(default_factory=_FakeDatabase)
    occurrences: _FakeOccurrenceService = field(default_factory=_FakeOccurrenceService)
    library: _FakeLessonLibraryService = field(default_factory=_FakeLessonLibraryService)


@pytest.fixture
def workspace(monkeypatch: pytest.MonkeyPatch) -> Iterator[_Workspace]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", "0")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", "postgresql+psycopg://localhost:9/s1at_closed")
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    app = create_app()
    state = _Workspace(app=app, client=TestClient(app))
    state.db.identity = SimpleNamespace(
        account_id="account-1",
        state="active",
        issuer=TEACHER.issuer,
        account_role="teacher",
    )
    app.dependency_overrides[get_verified_adult] = lambda: TEACHER
    app.dependency_overrides[get_db] = lambda: state.db
    app.dependency_overrides[get_occurrence_service] = lambda: state.occurrences
    app.dependency_overrides[get_lesson_library_service] = lambda: state.library
    app.state.identity_account_provisioner = _FakeIdentityProvider()
    try:
        with state.client:
            yield state
    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


@pytest.mark.parametrize(
    "identity",
    [
        None,
        SimpleNamespace(account_id="a1", state="disabled", issuer=TEACHER.issuer, account_role="teacher"),
        SimpleNamespace(account_id="a1", state="active", issuer="other-issuer", account_role="teacher"),
        SimpleNamespace(account_id="a1", state="active", issuer=TEACHER.issuer, account_role="school_manager"),
        SimpleNamespace(account_id="a1", state="active", issuer=TEACHER.issuer, account_role="parent"),
    ],
)
def test_teacher_profile_returns_403_for_inactive_mismatch_or_non_teacher_identity(
    workspace: _Workspace, identity: Any
) -> None:
    """covers: IMPL_REVIEW_E_E2_R1_20261125.md Checked-(b) & E2_PROMPT §5 (non-Teacher 403)"""
    workspace.db.identity = identity
    response = workspace.client.get("/api/teacher/v1/me/profile")
    assert response.status_code == 403
    assert response.json()["code"] == "ACTION_NOT_ALLOWED"


@pytest.mark.parametrize(
    "provisioner",
    [
        None,
        SimpleNamespace(),
        _FakeIdentityProvider(fail=True),
        _FakeIdentityProvider(missing=True),
    ],
)
def test_teacher_profile_returns_503_when_identity_provider_is_missing_or_fails(
    workspace: _Workspace, provisioner: Any
) -> None:
    """covers: IMPL_REVIEW_E_E2_R1_20261125.md Checked-(b) & E2_PROMPT §5 (provider failure 503)"""
    workspace.app.state.identity_account_provisioner = provisioner
    response = workspace.client.get("/api/teacher/v1/me/profile")
    assert response.status_code == 503
    assert response.json()["code"] == "IDENTITY_PROVIDER_UNAVAILABLE"


def test_teacher_profile_returns_503_and_rolls_back_on_database_error(
    workspace: _Workspace,
) -> None:
    """covers: IMPL_REVIEW_E_E2_R1_20261125.md Checked-(b) (DB error -> 503 + rollback)"""
    workspace.db.raise_sql = True
    response = workspace.client.get("/api/teacher/v1/me/profile")
    assert response.status_code == 503
    assert response.json()["code"] == "DATABASE_UNAVAILABLE"
    assert workspace.db.rolled_back is True


def test_teacher_profile_patch_is_not_mounted(workspace: _Workspace) -> None:
    """covers: E2_FIX1_PROMPT.md §1 (dropped R5 PATCH returns 405)"""
    response = workspace.client.patch(
        "/api/teacher/v1/me/profile",
        json={"display_name": "Updated"},
        headers={"Idempotency-Key": "dropped-r5"},
    )
    assert response.status_code == 405


def test_teacher_history_route_headers_query_validation_and_404_envelope(
    workspace: _Workspace,
) -> None:
    """covers: IMPL_REVIEW_E_E2_R1_20261125.md Checked-(b) (R3 headers, 400 not 422, 404 envelope)"""
    ok = workspace.client.get(
        "/api/teacher/v1/organizations/org-1/history?state=DRAFT&limit=10"
    )
    assert ok.status_code == 200
    assert ok.json()["contract"] == "LessonOccurrencePageV1"
    assert ok.headers["cache-control"] == "private, no-cache"
    assert ok.headers["vary"] == "Authorization"
    assert workspace.occurrences.calls[-1]["state"] == "DRAFT"
    assert workspace.occurrences.calls[-1]["limit"] == 10

    for bad_query in ("?limit=0", "?limit=101", "?state=NOT_A_STATE"):
        bad = workspace.client.get(
            f"/api/teacher/v1/organizations/org-1/history{bad_query}"
        )
        assert bad.status_code == 400
        assert bad.json()["code"] == "INVALID_REQUEST"

    workspace.occurrences.error = LessonOccurrenceError(404, "RESOURCE_NOT_FOUND")
    missing = workspace.client.get("/api/teacher/v1/organizations/org-1/history")
    assert missing.status_code == 404
    assert missing.json()["code"] == "RESOURCE_NOT_FOUND"


def test_teacher_activities_route_headers_query_validation_and_503_unconfigured(
    workspace: _Workspace,
) -> None:
    """covers: IMPL_REVIEW_E_E2_R1_20261125.md Checked-(a) (R2 headers, 400 not 422, 503 unconfigured)"""
    ok = workspace.client.get("/api/lesson-library/v1/organizations/org-1/activities?limit=5")
    assert ok.status_code == 200
    assert ok.json()["contract"] == "TeacherActivityPageV1"
    assert ok.headers["cache-control"] == "private, no-cache"
    assert ok.headers["vary"] == "Authorization"

    for bad_query in ("?limit=0", "?limit=101"):
        bad = workspace.client.get(
            f"/api/lesson-library/v1/organizations/org-1/activities{bad_query}"
        )
        assert bad.status_code == 400
        assert bad.json()["code"] == "INVALID_REQUEST"

    workspace.app.dependency_overrides.pop(get_lesson_library_service, None)
    workspace.app.state.lesson_library_storage = None
    unconfigured = workspace.client.get(
        "/api/lesson-library/v1/organizations/org-1/activities"
    )
    assert unconfigured.status_code == 503
    assert unconfigured.json()["code"] == "PROVIDER_UNAVAILABLE"


def test_openapi_catalog_and_portfolio_description_match_e2_decisions(
    workspace: _Workspace,
) -> None:
    """covers: IMPL_REVIEW_E_E2_R1_20261125.md P2-1 & P3-5 (catalog metadata and portfolio note)"""
    assert ("patch", "/api/teacher/v1/me/profile") not in MOUNTED_OPERATIONS
    assert ("patch", "/api/teacher/v1/me/profile") not in IDEMPOTENCY_MISMATCH_OPERATION_KEYS
    for key in (
        ("get", "/api/lesson-library/v1/organizations/{organization_id}/activities"),
        ("get", "/api/teacher/v1/organizations/{organization_id}/history"),
        ("get", "/api/teacher/v1/me/profile"),
    ):
        assert key in MOUNTED_OPERATIONS
    assert "X-Request-ID" not in MOUNTED_OPERATIONS[("get", "/api/teacher/v1/me/profile")]["request_inputs"]
    portfolio_statuses = {
        row["status"] for row in MOUNTED_OPERATIONS[PORTFOLIO_OPERATION_KEY]["responses"]
    }
    assert {"200", "409"}.issubset(portfolio_statuses)

    spec = workspace.client.get("/openapi.json").json()
    portfolio_desc = spec["paths"][PORTFOLIO_OPERATION_KEY[1]]["get"]["description"]
    assert "200 for synthetic profiles" in portfolio_desc
    assert "until a consent state `effective` exists" in portfolio_desc
