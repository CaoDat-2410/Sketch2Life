"""Contract tests for the new Teacher workspace routes; all identity and database ports are fake."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from sketch2life.application.ports.identity import (
    IdentityAccountProfile,
    VerifiedPrincipal,
)
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult

TEACHER = VerifiedPrincipal(
    subject="teacher-subject",
    issuer="synthetic-issuer",
    roles=frozenset({"teacher"}),
)


class _FakeDatabase:
    def __init__(self) -> None:
        self.identity: Any = type(
            "Identity",
            (),
            {
                "account_id": "account-1",
                "state": "active",
                "issuer": TEACHER.issuer,
                "account_role": "teacher",
            },
        )()

    def get(self, model: Any, key: Any) -> Any:
        if model is AdultIdentityModel:
            return self.identity
        return None


class _FakeIdentityProvider:
    def __init__(self) -> None:
        self.display_name = "Teacher One"
        self.email = "teacher@example.test"

    def get_account_profiles(self, subjects: list[str]) -> dict[str, IdentityAccountProfile]:
        return {
            subject: IdentityAccountProfile(
                subject=subject,
                email=self.email,
                display_name=self.display_name,
            )
            for subject in subjects
        }


@dataclass
class _Workspace:
    app: FastAPI
    client: TestClient | None
    db: _FakeDatabase = field(default_factory=_FakeDatabase)
    provider: _FakeIdentityProvider = field(default_factory=_FakeIdentityProvider)
    principal: VerifiedPrincipal = TEACHER


@pytest.fixture
def workspace() -> Iterator[_Workspace]:
    app = create_app()
    state = _Workspace(app=app, client=None)
    app.dependency_overrides[get_verified_adult] = lambda: state.principal
    app.dependency_overrides[get_db] = lambda: state.db
    app.state.identity_account_provisioner = state.provider
    with TestClient(app) as client:
        state.client = client
        yield state
    app.dependency_overrides.clear()


def _client(workspace: _Workspace) -> TestClient:
    assert workspace.client is not None
    return workspace.client


def test_teacher_profile_reads_identity_provider_fields(workspace: _Workspace) -> None:
    response = _client(workspace).get("/api/teacher/v1/me/profile")
    assert response.status_code == 200, response.text
    assert response.json() == {
        "contract": "TeacherProfileV1",
        "account_ref": "account-1",
        "display_name": "Teacher One",
        "email": "teacher@example.test",
    }
    assert response.headers["cache-control"] == "private, no-store"


def test_openapi_publishes_tch2_operations_and_read_only_profile(
    workspace: _Workspace,
) -> None:
    response = _client(workspace).get("/openapi.json")
    assert response.status_code == 200
    spec = response.json()
    portfolio = spec["paths"][
        "/api/be1/v1/organizations/{organization_id}/classes/{class_id}"
        "/profiles/{child_id}/portfolio"
    ]["get"]
    activities = spec["paths"][
        "/api/lesson-library/v1/organizations/{organization_id}/activities"
    ]["get"]
    history = spec["paths"][
        "/api/teacher/v1/organizations/{organization_id}/history"
    ]["get"]
    profile = spec["paths"]["/api/teacher/v1/me/profile"]
    assert "200" in portfolio["responses"] and "409" in portfolio["responses"]
    assert "200" in activities["responses"]
    assert "200" in history["responses"]
    assert set(profile) == {"get"}
    assert all(
        parameter.get("name") != "X-Request-ID"
        for parameter in profile["get"].get("parameters", [])
    )
