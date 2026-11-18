from __future__ import annotations

import asyncio
from typing import Any

import pytest
from fastapi import HTTPException
from starlette.requests import Request
from starlette.exceptions import HTTPException as StarletteHTTPException

from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
import sketch2life.interfaces.http.app as app_module
import sketch2life.interfaces.http.be1_runtime as runtime_module
import sketch2life.interfaces.http.routers.parent_ai as parent_ai


@pytest.mark.parametrize("operation", ("drawing", "story"))
def test_delete_pending_failure_guard_is_forwarded_as_http_409(operation: str) -> None:
    class _Repository:
        def fail_drawing_analysis(self, **_kwargs: Any) -> None:
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")

        def fail_story_revision(self, **_kwargs: Any) -> None:
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")

    with pytest.raises(HTTPException) as blocked:
        parent_ai._fail_story_run(
            _Repository(), operation=operation, principal=object(), run_id="run"
        )
    assert blocked.value.status_code == 409
    assert blocked.value.detail == {"code": "INVALID_STATE_TRANSITION"}


def test_artwork_guard_uses_parent_error_envelope_only_on_its_route(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setattr(
        app_module,
        "get_settings",
        lambda: Settings(env="test", _env_file=None),
    )
    monkeypatch.setattr(
        runtime_module,
        "get_core_database_settings",
        lambda: type("DatabaseSettings", (), {"database_url": None})(),
    )
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    try:
        application = app_module.create_app()
        handler = application.exception_handlers[StarletteHTTPException]

        def response_for(path: str):
            request = Request(
                {
                    "type": "http",
                    "method": "POST",
                    "path": path,
                    "headers": [],
                    "query_string": b"",
                    "server": ("testserver", 80),
                    "client": ("testclient", 50000),
                    "scheme": "http",
                    "http_version": "1.1",
                }
            )
            request.state.story_request_id = "guard-request"
            return asyncio.run(
                handler(
                    request,
                    HTTPException(status_code=409, detail={"code": "INVALID_STATE_TRANSITION"}),
                )
            )

        artwork = response_for("/api/parent/v1/ai/drawing-understandings")
        body = artwork.body
        assert artwork.status_code == 409
        assert b'"code":"INVALID_STATE_TRANSITION"' in body
        assert b'"correlation_id":"guard-request"' in body
        assert b'"detail"' not in body

        unrelated = response_for("/api/parent/v1/ai/sketch-guides")
        assert unrelated.status_code == 409
        assert b'"detail"' in unrelated.body
    finally:
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()
