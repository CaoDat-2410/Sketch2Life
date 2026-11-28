"""FEAT-066 T-2d (P-12(c), OD-18b): the role guard of the dev-only Parent AI routes is a 404.

SRS l.864-865: a caller who is not an active Parent has no resource and no scope on these routes
(they act on ``story_run_id``), so the answer is the one uniform 404 of an unknown resource. The
guard runs before the provider gate (``_require_modal_dev``), so a caller learns nothing about the
provider configuration. ``PARENT_ROLE_REQUIRED`` is read by no client, test or contract.
"""

from __future__ import annotations

from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import sketch2life.interfaces.http.app as app_module
import sketch2life.interfaces.http.be1_runtime as runtime_module
import sketch2life.interfaces.http.routers.parent_ai as parent_ai
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult

ISSUER = "issuer-1"
PRINCIPAL = VerifiedPrincipal("adult-1", ISSUER, frozenset())
RUN_ID = "22222222-2222-4222-8222-222222222222"


class _Db:
    def __init__(self, role: str | None, *, state: str = "active", issuer: str = ISSUER) -> None:
        self._identity = (
            None
            if role is None
            else SimpleNamespace(
                account_id="account-1", issuer=issuer, account_role=role, state=state
            )
        )

    def get(self, _model: object, _key: object) -> Any:
        return self._identity


_WRONG_ROLE = [
    pytest.param(_Db(None), id="no-identity"),
    pytest.param(_Db("teacher"), id="teacher"),
    pytest.param(_Db("school_manager"), id="manager"),
    pytest.param(_Db("platform_admin"), id="platform-admin"),
    pytest.param(_Db("parent", state="suspended"), id="inactive"),
    pytest.param(_Db("parent", issuer="another-issuer"), id="other-issuer"),
]


@pytest.mark.parametrize("db", _WRONG_ROLE)
def test_the_guard_answers_a_uniform_404_for_every_caller_that_is_not_an_active_parent(
    db: _Db,
) -> None:
    with pytest.raises(HTTPException) as refused:
        parent_ai._require_parent(db, PRINCIPAL)  # type: ignore[arg-type]
    assert refused.value.status_code == 404
    assert dict(refused.value.detail) == {"code": "RESOURCE_NOT_FOUND"}  # type: ignore[arg-type]


def test_an_active_parent_of_the_issuer_passes_the_guard() -> None:
    identity = parent_ai._require_parent(_Db("parent"), PRINCIPAL)  # type: ignore[arg-type]
    assert identity.account_role == "parent"


def test_the_old_code_is_gone_from_the_module() -> None:
    from pathlib import Path

    source = Path(parent_ai.__file__).read_text(encoding="utf-8")
    assert "PARENT_ROLE_REQUIRED" not in source


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", "0")
    settings = Settings(env="test", _env_file=None)  # type: ignore[call-arg]
    monkeypatch.setattr(app_module, "get_settings", lambda: settings)
    monkeypatch.setattr(parent_ai, "get_settings", lambda: settings)
    monkeypatch.setattr(
        runtime_module, "get_core_database_settings", lambda: SimpleNamespace(database_url=None)
    )
    application = app_module.create_app()
    application.dependency_overrides[get_verified_adult] = lambda: PRINCIPAL
    application.dependency_overrides[get_db] = lambda: _Db("parent")
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    try:
        with TestClient(application, raise_server_exceptions=False) as test_client:
            yield test_client
    finally:
        application.dependency_overrides.clear()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def _use_db(client: TestClient, db: _Db) -> None:
    client.app.dependency_overrides[get_db] = lambda: db  # type: ignore[attr-defined]


def _calls(client: TestClient) -> dict[str, Any]:
    return {
        "sketch-guides": lambda: client.post(
            "/api/parent/v1/ai/sketch-guides", json={"topic": "a cat"}
        ),
        "drawing-understandings": lambda: client.post(
            "/api/parent/v1/ai/drawing-understandings",
            json={
                "story_run_id": RUN_ID,
                "media_type": "image/png",
                "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB",
            },
        ),
        "story-revisions": lambda: client.post(
            f"/api/parent/v1/ai/story-runs/{RUN_ID}/story-revisions",
            json={"expected_understanding_revision": 1},
            headers={"Idempotency-Key": "t2d-guard-key"},
        ),
    }


@pytest.mark.parametrize("db", _WRONG_ROLE)
def test_every_ai_route_answers_the_404_before_the_provider_gate(
    client: TestClient, db: _Db
) -> None:
    """Wrong-role callers get the uniform 404 before any AI or catalog capability is used.

    The curated SVG route is local and may return a catalog miss (404) for an active Parent;
    the drawing and story routes still reveal the disabled provider only after Parent auth.
    """
    calls = _calls(client)
    _use_db(client, _Db("parent"))
    for name, call in calls.items():
        response = call()
        if name == "sketch-guides":
            assert response.status_code == 404
            assert response.json()["detail"]["code"] == "CURATED_SVG_GUIDE_NOT_FOUND"
        else:
            assert response.status_code == 503, name
    _use_db(client, db)
    bodies = {name: call() for name, call in calls.items()}
    for name, response in bodies.items():
        assert response.status_code == 404, name
    # the two routes inside the Parent story envelope answer its 404 shape
    for name in ("drawing-understandings", "story-revisions"):
        body = bodies[name].json()
        assert body["code"] == "RESOURCE_NOT_FOUND"
        assert set(body) >= {"code", "message", "correlation_id", "retryable"}
    # the sketch guide keeps the raw FastAPI body (dev-only, unscheduled; CV-1)
    assert bodies["sketch-guides"].json() == {"detail": {"code": "RESOURCE_NOT_FOUND"}}
    assert (
        bodies["drawing-understandings"].json()["code"]
        == (bodies["story-revisions"].json()["code"])
    )
