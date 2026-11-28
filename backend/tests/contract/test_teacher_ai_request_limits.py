from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

import sketch2life.interfaces.http.routers.teacher_ai as teacher_ai
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult


@pytest.fixture(autouse=True)
def _disable_dotenv(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv(
        "SKETCH2LIFE_DATABASE_URL", "postgresql+psycopg://localhost:9/teacher_ai_limits"
    )
    monkeypatch.setenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", "0")
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    try:
        yield
    finally:
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def _reviewed_plan() -> dict[str, Any]:
    return {
        "review_confirmed": True,
        "plan_revision_ref": "plan-rev-1",
        "topic": "Tree",
        "target_age_months": 60,
        "objectives": ["Notice parts of a tree."],
        "drawing_steps": [
            {"action": f"Draw part {index}.", "placement": f"Place part {index}."}
            for index in range(1, 5)
        ],
        "subject_knowledge": ["Trees have trunks and leaves."],
        "activities": [
            {
                "activity_ref": "activity-1",
                "title": "Observe a tree",
                "goal": "Notice the trunk and leaves.",
                "materials": "Paper and pencils.",
                "preparation": "Prepare a clear workspace.",
                "instructions": "Observe the tree, then draw it.",
                "safety_notes": "Use pencils safely.",
            }
        ],
    }


def _set_field_path(payload: dict[str, Any], field_path: str, value: Any) -> None:
    parts = field_path.replace("[", ".").replace("]", "").split(".")
    target: Any = payload
    for part in parts[:-1]:
        target = target[int(part)] if isinstance(target, list) else target[part]
    last_part = parts[-1]
    if isinstance(target, list):
        target[int(last_part)] = value
    else:
        target[last_part] = value


def _app(monkeypatch: pytest.MonkeyPatch) -> Any:
    verified = VerifiedPrincipal(
        subject="synthetic-teacher", issuer="test", roles=frozenset()
    )
    application = create_app()
    application.dependency_overrides[get_verified_adult] = lambda: verified
    application.dependency_overrides[teacher_ai.get_db] = lambda: object()
    monkeypatch.setattr(teacher_ai, "require_assignment", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        teacher_ai,
        "_require_modal_dev",
        lambda: pytest.fail("invalid request reached the provider gate"),
    )

    class UnusedProvider:
        def invoke(self, *_args: object, **_kwargs: object) -> object:
            pytest.fail("invalid request invoked the provider")

    monkeypatch.setattr(teacher_ai, "ModalJsonFunctionClient", UnusedProvider)
    return application


@pytest.mark.parametrize(
    ("path", "field_path", "maximum"),
    [
        ("sketch-decks", "objectives[0]", 200),
        ("sketch-decks", "subject_knowledge[0]", 240),
        ("sketch-decks", "drawing_steps[0].action", 240),
        ("sketch-decks", "drawing_steps[0].placement", 240),
        ("sketch-decks", "activities[0].title", 120),
        ("sketch-decks", "activities[0].goal", 200),
        ("sketch-decks", "activities[0].materials", 500),
        ("sketch-decks", "activities[0].preparation", 500),
        ("sketch-decks", "activities[0].instructions", 1_200),
        ("sketch-decks", "activities[0].safety_notes", 500),
    ],
)
def test_teacher_sketch_deck_returns_422_for_each_worker_field_limit(
    monkeypatch: pytest.MonkeyPatch, path: str, field_path: str, maximum: int
) -> None:
    payload = _reviewed_plan()
    value = "x" * (maximum + 1)
    parts = field_path.replace("[", ".").replace("]", "").split(".")
    _set_field_path(payload, field_path, value)

    application = _app(monkeypatch)
    try:
        with TestClient(application) as client:
            response = client.post(
                f"/api/teacher/v1/organizations/org-1/ai/{path}", json=payload
            )
        assert response.status_code == 422, response.text
        locations = [error.get("loc", []) for error in response.json().get("detail", [])]
        assert any(parts[0] in location for location in locations)
    finally:
        runtime = getattr(application.state, "be1_runtime", None)
        if runtime is not None and runtime.engine is not None:
            runtime.engine.dispose()


@pytest.mark.parametrize(
    ("field_path", "value"),
    [
        ("objectives", []),
        ("objectives", ["Tree objective."] * 5),
        ("drawing_steps", _reviewed_plan()["drawing_steps"][:3]),
        (
            "drawing_steps",
            _reviewed_plan()["drawing_steps"]
            + [{"action": "extra", "placement": "extra"}] * 5,
        ),
        ("subject_knowledge", []),
        ("subject_knowledge", ["Tree note."] * 9),
        ("activities", []),
        ("activities", _reviewed_plan()["activities"] * 7),
        ("plan_revision_ref", "plan/ref"),
        ("activities[0].activity_ref", "activity/ref"),
        ("objectives[0]", "   "),
        ("drawing_steps[0].action", "   "),
        ("drawing_steps[0].placement", "   "),
        ("subject_knowledge[0]", "   "),
        ("activities[0].title", "   "),
        ("activities[0].goal", "   "),
        ("activities[0].materials", "   "),
        ("activities[0].preparation", "   "),
        ("activities[0].instructions", "   "),
        ("activities[0].safety_notes", "   "),
        ("topic", "   "),
        ("target_age_months", 35),
        ("target_age_months", 121),
    ],
)
def test_teacher_sketch_deck_returns_422_for_worker_counts_patterns_and_blanks(
    monkeypatch: pytest.MonkeyPatch, field_path: str, value: Any
) -> None:
    payload = _reviewed_plan()
    _set_field_path(payload, field_path, value)
    expected_location = [
        int(part) if part.isdigit() else part
        for part in field_path.replace("[", ".").replace("]", "").split(".")
    ]
    application = _app(monkeypatch)
    try:
        with TestClient(application) as client:
            response = client.post(
                "/api/teacher/v1/organizations/org-1/ai/sketch-decks", json=payload
            )
        assert response.status_code == 422, response.text
        locations = [error.get("loc", []) for error in response.json().get("detail", [])]
        assert any(
            location[0] == "body" and location[1:] == expected_location
            for location in locations
        )
    finally:
        runtime = getattr(application.state, "be1_runtime", None)
        if runtime is not None and runtime.engine is not None:
            runtime.engine.dispose()


def test_teacher_sketch_deck_returns_422_for_duplicate_activity_refs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _reviewed_plan()
    payload["activities"].append(dict(payload["activities"][0]))
    application = _app(monkeypatch)
    try:
        with TestClient(application) as client:
            response = client.post(
                "/api/teacher/v1/organizations/org-1/ai/sketch-decks", json=payload
            )
        assert response.status_code == 422, response.text
        assert any(
            error.get("loc") == ["body", "activities"]
            for error in response.json().get("detail", [])
        )
    finally:
        runtime = getattr(application.state, "be1_runtime", None)
        if runtime is not None and runtime.engine is not None:
            runtime.engine.dispose()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("objectives", ["   "]),
        ("subject_knowledge", ["   "]),
    ],
)
def test_teacher_sketch_deck_returns_422_for_blank_worker_text(
    monkeypatch: pytest.MonkeyPatch, field: str, value: list[str]
) -> None:
    payload = _reviewed_plan()
    payload[field] = value
    application = _app(monkeypatch)
    try:
        with TestClient(application) as client:
            response = client.post(
                "/api/teacher/v1/organizations/org-1/ai/sketch-decks", json=payload
            )
        assert response.status_code == 422, response.text
        assert any(
            field in error.get("loc", []) for error in response.json().get("detail", [])
        )
    finally:
        runtime = getattr(application.state, "be1_runtime", None)
        if runtime is not None and runtime.engine is not None:
            runtime.engine.dispose()


def test_teacher_lesson_suggestion_objectives_use_the_deck_limit_before_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {
        "topic": "Tree",
        "target_age_months": 60,
        "objectives": ["x" * 201],
        "drawing_subject": "tree",
        "activity_count": 1,
        "activity_kind": "outdoor",
    }
    application = _app(monkeypatch)
    try:
        with TestClient(application) as client:
            response = client.post(
                "/api/teacher/v1/organizations/org-1/ai/lesson-plan-suggestions",
                json=payload,
            )
        assert response.status_code == 422, response.text
        assert any(
            "objectives" in error.get("loc", [])
            for error in response.json().get("detail", [])
        )
    finally:
        runtime = getattr(application.state, "be1_runtime", None)
        if runtime is not None and runtime.engine is not None:
            runtime.engine.dispose()
