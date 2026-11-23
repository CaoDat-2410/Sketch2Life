from __future__ import annotations

import logging

import pytest
from fastapi.testclient import TestClient

import sketch2life.interfaces.http.routers.parent_ai as parent_ai
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult


def _client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    application = create_app()
    application.dependency_overrides[get_verified_adult] = lambda: object()
    application.dependency_overrides[get_db] = lambda: object()
    monkeypatch.setattr(parent_ai, "_require_parent", lambda _db, _principal: None)
    return TestClient(application)


def test_sketch_guide_api_returns_correlated_curated_draft_for_sea_turtle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _client(monkeypatch)

    response = client.post(
        "/api/parent/v1/ai/sketch-guides",
        headers={"X-Request-ID": "svg-guide-sea-turtle-1"},
        json={
            "contract": "SvgTopicStrokeGuideRequestV1",
            "topic": "Đại dương",
            "intended_subject": "Rùa biển",
            "difficulty": "beginner",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["contract"] == "SvgTopicStrokeGuideSourceDraftV1"
    assert body["request_id"] == "svg-guide-sea-turtle-1"
    assert body["generation_source"] == "CURATED_SOURCE_DERIVATION"
    assert body["reference_source"]["dataset_name"] == "OpenMoji"
    assert 4 <= body["stage_count"] <= 8
    assert response.headers["X-Request-ID"] == "svg-guide-sea-turtle-1"


def test_sketch_guide_api_returns_correlated_non_sensitive_no_match_without_modal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _client(monkeypatch)
    monkeypatch.setattr(parent_ai, "build_parent_svg_guide", lambda **_kwargs: None)

    def fail_if_modal_is_used():
        raise AssertionError("missing curated guide must not dispatch a retired Modal workload")

    monkeypatch.setattr(parent_ai, "ModalJsonFunctionClient", fail_if_modal_is_used)
    response = client.post(
        "/api/parent/v1/ai/sketch-guides",
        headers={"X-Request-ID": "svg-guide-no-match-1"},
        json={
            "contract": "SvgTopicStrokeGuideRequestV1",
            "topic": "Đại dương",
            "intended_subject": "Sao biển",
            "difficulty": "beginner",
        },
    )

    assert response.status_code == 404
    detail = response.json()["detail"]
    assert detail["code"] == "CURATED_SVG_GUIDE_NOT_FOUND"
    assert detail["request_id"] == "svg-guide-no-match-1"
    assert "Sao biển" not in response.text
    assert response.headers["X-Request-ID"] == "svg-guide-no-match-1"


def test_sketch_guide_api_logs_only_safe_source_failure_diagnostics(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    client = _client(monkeypatch)
    monkeypatch.setattr(
        parent_ai,
        "build_parent_svg_guide",
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("private source path")),
    )
    caplog.set_level(logging.ERROR, logger=parent_ai.__name__)

    response = client.post(
        "/api/parent/v1/ai/sketch-guides",
        headers={"X-Request-ID": "svg-guide-source-error-1"},
        json={
            "contract": "SvgTopicStrokeGuideRequestV1",
            "topic": "Đại dương",
            "intended_subject": "Rùa biển",
            "difficulty": "beginner",
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "CURATED_SVG_GUIDE_UNAVAILABLE"
    assert response.json()["detail"]["request_id"] == "svg-guide-source-error-1"
    assert "private source path" not in response.text
    assert "private source path" not in caplog.text
    assert "svg-guide-source-error-1" in caplog.text
    assert "RuntimeError" in caplog.text
