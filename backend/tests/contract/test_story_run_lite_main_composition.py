from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest
from fastapi.testclient import TestClient

from sketch2life.application.ports.story_run_lite import CommandResult
from sketch2life.domain.story_run_lite import StoryRunLiteError
from sketch2life.infrastructure.config.settings import get_settings
from sketch2life.infrastructure.story_run_lite import composition
from sketch2life.interfaces.http.app import create_app, create_classroom_app


@pytest.fixture
def local_demo(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", "1")
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    get_settings.cache_clear()
    repository = Mock()
    service = Mock()
    service.get_run.return_value = CommandResult(200, {"run_ref": "synthetic"}, 1)
    runtime = SimpleNamespace(repository=repository, service=service, vision=None, engine=Mock())
    build = Mock(return_value=runtime)
    monkeypatch.setattr(composition, "build_runtime", build)
    yield runtime, build
    get_settings.cache_clear()


def test_disabled_preserves_default_surface_and_does_not_start_runtime(monkeypatch):
    monkeypatch.delenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", raising=False)
    build = Mock(side_effect=AssertionError("unexpected database startup"))
    monkeypatch.setattr(composition, "build_runtime", build)
    with TestClient(create_app()) as client:
        assert client.get("/v1/story-runs/synthetic").status_code == 404
    build.assert_not_called()


def test_main_demo_lifespan_routes_and_error_isolation(local_demo):
    runtime, build = local_demo
    app = create_app()
    with TestClient(app, base_url="http://127.0.0.1", client=("127.0.0.1", 54321)) as client:
        result = client.get("/v1/story-runs/synthetic")
        assert result.status_code == 200
        assert result.json()["run_ref"] == "synthetic"
        assert client.post("/v1/story-runs", json={}).json()["code"] == "INVALID_REQUEST"
        assert client.post("/v1/sessions", json={}).json() == {"detail": "request contract invalid"}
    build.assert_called_once_with(main_demo=True)
    runtime.repository.acquire_singleton_lock.assert_called_once()
    runtime.repository.recover_after_restart.assert_called_once()
    runtime.repository.release_singleton_lock.assert_called_once()
    runtime.engine.dispose.assert_called_once()


def test_main_demo_rejects_nonlocal_and_forwarded_requests(local_demo):
    app = create_app()
    with TestClient(app, base_url="http://127.0.0.1", client=("192.0.2.1", 54321)) as client:
        assert client.get("/v1/story-runs/synthetic").status_code == 403
    with TestClient(app, base_url="http://127.0.0.1", client=("127.0.0.1", 54321)) as client:
        assert client.get(
            "/v1/story-runs/synthetic", headers={"X-Forwarded-For": "127.0.0.1"}
        ).status_code == 403
        assert client.get(
            "/v1/story-runs/synthetic", headers={"Host": "attacker.example"}
        ).status_code == 403
    with TestClient(app, base_url="http://192.0.2.1", client=("127.0.0.1", 54321)) as client:
        assert client.get("/v1/story-runs/synthetic").status_code == 403


def test_main_demo_lock_failure_disposes_engine(local_demo):
    runtime, _build = local_demo
    runtime.repository.acquire_singleton_lock.side_effect = RuntimeError("lock unavailable")
    with pytest.raises(RuntimeError, match="lock unavailable"), TestClient(
        create_app(), base_url="http://127.0.0.1"
    ):
        pass
    runtime.repository.release_singleton_lock.assert_not_called()
    runtime.engine.dispose.assert_called_once()


def test_main_demo_recovery_failure_releases_lock_and_engine(local_demo):
    runtime, _build = local_demo
    runtime.repository.recover_after_restart.side_effect = RuntimeError("recovery unavailable")
    with pytest.raises(RuntimeError, match="recovery unavailable"), TestClient(
        create_app(), base_url="http://127.0.0.1"
    ):
        pass
    runtime.repository.release_singleton_lock.assert_called_once()
    runtime.engine.dispose.assert_called_once()


def test_main_demo_error_contract_does_not_replace_other_errors(local_demo):
    runtime, _build = local_demo
    app = create_app()
    with TestClient(
        app, base_url="http://127.0.0.1", client=("127.0.0.1", 54321),
        raise_server_exceptions=False,
    ) as client:
        runtime.service.get_run.side_effect = StoryRunLiteError(404, "RUN_NOT_FOUND", "Not found")
        response = client.get("/v1/story-runs/synthetic")
        assert response.status_code == 404
        assert response.json()["code"] == "RUN_NOT_FOUND"
        runtime.service.get_run.side_effect = RuntimeError("sensitive diagnostic")
        response = client.get("/v1/story-runs/synthetic")
        assert response.status_code == 500
        assert response.json()["code"] == "INTERNAL_ERROR"
        assert "sensitive diagnostic" not in response.text
        assert client.post("/v1/sessions", json={}).json() == {"detail": "request contract invalid"}


def test_main_demo_rejects_other_profiles_and_deployment_environments(local_demo, monkeypatch):
    with pytest.raises(ValueError, match="combined local/test"):
        create_classroom_app()
    monkeypatch.setenv("SKETCH2LIFE_ENV", "staging")
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "firebase")
    monkeypatch.setenv("SKETCH2LIFE_FIREBASE_PROJECT_ID", "synthetic")
    get_settings.cache_clear()
    with pytest.raises(ValueError, match="combined local/test"):
        create_app()


def test_main_demo_openapi_uses_pinned_route_contract(local_demo):
    root = Path(__file__).resolve().parents[3]
    expected = json.loads(
        (root / "features/FEAT-063-system-architecture-rearchitecture/artifacts/"
         "storyrun-lite/openapi.json").read_text(encoding="utf-8")
    )
    packaged = files("sketch2life.interfaces.http").joinpath("story_run_lite_openapi.json")
    assert json.loads(packaged.read_text(encoding="utf-8")) == expected
    schema = create_app().openapi()

    def restore_refs(value):
        if isinstance(value, list):
            return [restore_refs(item) for item in value]
        if isinstance(value, dict):
            return {key: restore_refs(item) for key, item in value.items()}
        if isinstance(value, str) and value.startswith("#/components/"):
            group, name = value.removeprefix("#/components/").split("/")
            assert name.startswith("StoryRunLite_")
            return f"#/components/{group}/{name.removeprefix('StoryRunLite_')}"
        return value

    for path, operations in expected["paths"].items():
        assert set(schema["paths"][path]) == set(operations)
        assert restore_refs(schema["paths"][path]) == operations
    for group, components in expected["components"].items():
        for name, value in components.items():
            assert restore_refs(schema["components"][group][f"StoryRunLite_{name}"]) == value


@pytest.mark.parametrize("url", [
    "postgresql://postgres@127.0.0.1:5433/sketch2life",
    "postgresql://postgres@127.0.0.1:5433/storyrun_lite_test",
])
def test_main_demo_accepts_only_explicit_local_database_targets(url):
    assert composition.goal_database_url(url, main_demo=True)[0] == url


@pytest.mark.parametrize("url", [
    "postgresql://postgres@127.0.0.1:5433/sketch2life_a2",
    "postgresql://postgres@127.0.0.1:5432/sketch2life",
    "postgresql://postgres@localhost:5433/sketch2life",
    "postgresql://postgres@192.0.2.1:5433/sketch2life",
    "postgresql://postgres@127.0.0.1:5433/sketch2life?host=192.0.2.1",
    "postgresql://postgres@127.0.0.1:5433/sketch2life?port=5432",
])
def test_main_demo_rejects_wrong_database_targets(url):
    with pytest.raises(ValueError):
        composition.goal_database_url(url, main_demo=True)


def test_standalone_guard_still_rejects_main_database():
    with pytest.raises(ValueError):
        composition.goal_database_url("postgresql://postgres@127.0.0.1:5433/sketch2life")


def test_main_demo_rejects_mismatched_database_before_connect(monkeypatch):
    monkeypatch.setenv(
        "STORYRUN_LITE_DATABASE_URL", "postgresql://postgres@127.0.0.1:5433/sketch2life"
    )
    monkeypatch.setenv(
        "SKETCH2LIFE_DATABASE_URL", "postgresql://postgres@127.0.0.1:5433/storyrun_lite_other"
    )
    create = Mock(side_effect=AssertionError("unexpected connection"))
    monkeypatch.setattr(composition, "create_engine", create)
    with pytest.raises(ValueError, match="targets differ"):
        composition.build_runtime(main_demo=True)
    create.assert_not_called()


def test_main_demo_rejects_postgres_target_override_before_connect(monkeypatch):
    url = "postgresql://postgres@127.0.0.1:5433/sketch2life"
    monkeypatch.setenv("STORYRUN_LITE_DATABASE_URL", url)
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", url)
    monkeypatch.setenv("PGHOSTADDR", "192.0.2.1")
    create = Mock(side_effect=AssertionError("unexpected connection"))
    monkeypatch.setattr(composition, "create_engine", create)
    with pytest.raises(ValueError, match="target overrides"):
        composition.build_runtime(main_demo=True)
    create.assert_not_called()


@pytest.mark.parametrize(
    ("changes", "valid"),
    [
        ({}, True),
        ({"database_name": "sketch2life_a2"}, False),
        ({"current_user": "not_owner"}, False),
        ({"server_address": "192.0.2.1/32"}, False),
        ({"server_port": 5432}, False),
    ],
)
def test_main_demo_verifies_connected_owner_and_network(changes, valid):
    row = {
        "database_name": "sketch2life",
        "current_user": "postgres",
        "database_owner": "postgres",
        "server_address": "127.0.0.1/32",
        "server_port": 5433,
        **changes,
    }
    engine = MagicMock()
    connection = engine.connect.return_value.__enter__.return_value
    connection.execute.return_value.mappings.return_value.one.return_value = row
    if valid:
        assert composition.verify_goal_database_owner(engine, "sketch2life", main_demo=True) == (
            "postgres"
        )
    else:
        with pytest.raises(RuntimeError):
            composition.verify_goal_database_owner(engine, "sketch2life", main_demo=True)
