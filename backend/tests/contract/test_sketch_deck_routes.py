from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

import sketch2life.interfaces.http.routers.lesson_occurrences as occurrence_routes
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.domain.lesson_occurrences.sketch_deck import (
    DrawingStepInput,
    SketchDeckDrawingInputs,
)
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.infrastructure.lesson_occurrences.documents import DocumentError
from sketch2life.infrastructure.lesson_occurrences.sketch_decks import (
    PreparedSketchDeck,
    SketchDeckCommandResult,
    SketchDeckGenerationStart,
)
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult
from sketch2life.interfaces.http.routers.lesson_occurrences import get_sketch_deck_service


@pytest.fixture(autouse=True)
def _disable_dotenv(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", "postgresql+psycopg://localhost:9/deck_contract")
    monkeypatch.setenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", "0")
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    try:
        yield
    finally:
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def _payload(
    *,
    review_confirmed: bool = True,
    step_count: int = 4,
    teacher_confirmed_age_band_ref: str | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "expected_plan_revision_id": "11234567-89ab-cdef-0123-456789abcdef",
        "expected_plan_hash": "a" * 64,
        "review_confirmed": review_confirmed,
        "topic": "Tree",
        "drawing_steps": [
            {"action": f"action {index}", "placement": f"placement {index}"}
            for index in range(1, step_count + 1)
        ],
        "subject_knowledge": ["Trees have trunks and leaves."],
    }
    if teacher_confirmed_age_band_ref is not None:
        payload["teacher_confirmed_age_band_ref"] = teacher_confirmed_age_band_ref
    return payload


def test_generate_uses_teacher_inputs_and_returns_them_on_the_revision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    verified = VerifiedPrincipal(subject="synthetic-teacher", issuer="test", roles=frozenset())
    occurrence_id = "01234567-89ab-cdef-0123-456789abcdef"
    plan_revision_id = "11234567-89ab-cdef-0123-456789abcdef"
    plan_hash = "a" * 64
    events: list[str] = []
    expected_inputs = SketchDeckDrawingInputs(
        review_confirmed=True,
        topic="Tree",
        drawing_steps=tuple(
            DrawingStepInput(f"action {index}", f"placement {index}")
            for index in range(1, 5)
        ),
        subject_knowledge=("Trees have trunks and leaves.",),
        teacher_confirmed_age_band_ref="36-71",
    )

    class ServiceStub:
        def replay_if_present(self, **kwargs: object) -> None:
            assert kwargs["drawing_inputs"] == expected_inputs
            events.append("replay_check")
            return None

        def verify_approved_plan(self, **_kwargs: object) -> None:
            events.append("verify_plan")

        def prepare_worker_input(self, **kwargs: object) -> PreparedSketchDeck:
            assert kwargs["drawing_inputs"] == expected_inputs
            events.append("prepare")
            return PreparedSketchDeck(
                occurrence_id=occurrence_id,
                plan_revision_id=plan_revision_id,
                plan_content_hash=plan_hash,
                plan_activity_ids=("activity-one",),
                target_age_band="36-71",
                drawing_inputs=expected_inputs,
                worker_input={
                    "schema_version": "sketch2life.teacher-deck-input.v1",
                    "topic": "Tree",
                    "drawing_subject": "Tree",
                    "target_age_months": 54,
                    "drawing_steps": [
                        {
                            "step_index": index,
                            "action": f"action {index}",
                            "placement": f"placement {index}",
                        }
                        for index in range(1, 5)
                    ],
                },
            )

        def begin_generation(self, **_kwargs: object) -> SketchDeckGenerationStart:
            return SketchDeckGenerationStart(
                sketch_deck_revision_id=str(uuid4()),
                revision_no=1,
                occurrence_id=occurrence_id,
                plan_revision_id=plan_revision_id,
                plan_content_hash=plan_hash,
                target_age_band="36-71",
                plan_activity_ids=("activity-one",),
            )

        def complete_generation(self, **kwargs: object) -> SketchDeckCommandResult:
            assert kwargs["deck"] == {}
            return SketchDeckCommandResult(
                body={
                    "contract": "SketchDeckRevisionV1",
                    "sketch_deck_revision_id": str(uuid4()),
                    "occurrence_id": occurrence_id,
                    "plan_revision_id": plan_revision_id,
                    "revision_no": 1,
                    "plan_content_hash": plan_hash,
                    "review_confirmed": True,
                    "topic": "Tree",
                    "drawing_steps": [
                        {"action": f"action {index}", "placement": f"placement {index}"}
                        for index in range(1, 5)
                    ],
                    "subject_knowledge": ["Trees have trunks and leaves."],
                    "target_age_band": "36-71",
                    "deck_schema_version": "sketch2life.teacher-sketch-deck.v1",
                    "state": "FAILED",
                    "content_hash": None,
                    "created_at": datetime.now(UTC).isoformat(),
                    "ready_at": None,
                    "superseded_at": None,
                },
                status_code=201,
                replayed=False,
            )

    def modal_gate() -> None:
        events.append("modal_gate")

    def worker(worker_input: dict[str, object], **_kwargs: str) -> dict[str, object]:
        assert worker_input["topic"] == "Tree"
        assert worker_input["drawing_subject"] == "Tree"
        assert worker_input["target_age_months"] == 54
        events.append("shared_worker_adapter")
        return {"deck": {}}

    monkeypatch.setattr(occurrence_routes, "_require_modal_dev", modal_gate)
    monkeypatch.setattr(occurrence_routes, "invoke_teacher_sketch_deck_worker", worker)
    application = create_app()
    application.dependency_overrides[get_verified_adult] = lambda: verified
    application.dependency_overrides[get_sketch_deck_service] = lambda: ServiceStub()

    with TestClient(application) as client:
        response = client.post(
            f"/v1/lesson-occurrences/{occurrence_id}/sketch-decks",
            headers={"Idempotency-Key": "synthetic-deck-command-2"},
            json=_payload(teacher_confirmed_age_band_ref="36-71"),
        )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["state"] == "FAILED"
    assert body["review_confirmed"] is True
    assert body["topic"] == "Tree"
    assert len(body["drawing_steps"]) == 4
    assert body["subject_knowledge"] == ["Trees have trunks and leaves."]
    assert events == [
        "replay_check",
        "verify_plan",
        "prepare",
        "modal_gate",
        "shared_worker_adapter",
    ]


@pytest.mark.parametrize(
    ("review_confirmed", "step_count"),
    [(False, 4), (True, 3), (True, 9)],
)
def test_generate_rejects_unconfirmed_review_or_invalid_step_count(
    monkeypatch: pytest.MonkeyPatch, review_confirmed: bool, step_count: int
) -> None:
    verified = VerifiedPrincipal(subject="synthetic-teacher", issuer="test", roles=frozenset())
    application = create_app()
    application.dependency_overrides[get_verified_adult] = lambda: verified

    class UnusedService:
        def __getattr__(self, _name: str) -> object:
            raise AssertionError("invalid request must be rejected before service calls")

    application.dependency_overrides[get_sketch_deck_service] = lambda: UnusedService()
    monkeypatch.setattr(
        occurrence_routes,
        "_require_modal_dev",
        lambda: (_ for _ in ()).throw(AssertionError("provider must not run")),
    )

    with TestClient(application) as client:
        response = client.post(
            "/v1/lesson-occurrences/01234567-89ab-cdef-0123-456789abcdef/sketch-decks",
            headers={"Idempotency-Key": "synthetic-invalid-deck-command"},
            json=_payload(review_confirmed=review_confirmed, step_count=step_count),
        )

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("topic", "x" * 121),
        ("action", "x" * 241),
        ("placement", "x" * 241),
        ("subject_knowledge", "x" * 241),
    ],
)
def test_generate_rejects_review_text_outside_teacher_field_limits(
    monkeypatch: pytest.MonkeyPatch, field: str, value: str
) -> None:
    verified = VerifiedPrincipal(subject="synthetic-teacher", issuer="test", roles=frozenset())
    application = create_app()
    application.dependency_overrides[get_verified_adult] = lambda: verified

    class UnusedService:
        def __getattr__(self, _name: str) -> object:
            raise AssertionError("invalid request must be rejected before service calls")

    application.dependency_overrides[get_sketch_deck_service] = lambda: UnusedService()
    payload = _payload()
    if field == "topic":
        payload[field] = value
    elif field == "subject_knowledge":
        payload[field] = [value]
    else:
        steps = payload["drawing_steps"]
        assert isinstance(steps, list)
        steps[0][field] = value
    monkeypatch.setattr(
        occurrence_routes,
        "_require_modal_dev",
        lambda: (_ for _ in ()).throw(AssertionError("provider must not run")),
    )

    with TestClient(application) as client:
        response = client.post(
            "/v1/lesson-occurrences/01234567-89ab-cdef-0123-456789abcdef/sketch-decks",
            headers={"Idempotency-Key": "synthetic-invalid-deck-text"},
            json=payload,
        )

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"


def test_generate_returns_the_stored_plan_field_error_before_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    verified = VerifiedPrincipal(subject="synthetic-teacher", issuer="test", roles=frozenset())

    class InvalidStoredPlanService:
        def replay_if_present(self, **_kwargs: object) -> None:
            return None

        def verify_approved_plan(self, **_kwargs: object) -> None:
            return None

        def prepare_worker_input(self, **_kwargs: object) -> PreparedSketchDeck:
            raise DocumentError(
                400,
                "INVALID_REQUEST",
                field_errors=[{"field": "objectives[0]", "code": "INVALID_FORMAT"}],
            )

    def provider_must_not_run(*_args: object, **_kwargs: object) -> object:
        pytest.fail("stored plan validation must run before the provider")

    monkeypatch.setattr(occurrence_routes, "_require_modal_dev", provider_must_not_run)
    monkeypatch.setattr(
        occurrence_routes, "invoke_teacher_sketch_deck_worker", provider_must_not_run
    )
    application = create_app()
    application.dependency_overrides[get_verified_adult] = lambda: verified
    application.dependency_overrides[get_sketch_deck_service] = (
        lambda: InvalidStoredPlanService()
    )

    with TestClient(application) as client:
        response = client.post(
            "/v1/lesson-occurrences/01234567-89ab-cdef-0123-456789abcdef/sketch-decks",
            headers={"Idempotency-Key": "stored-plan-field-limit"},
            json=_payload(teacher_confirmed_age_band_ref="36-71"),
        )

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"
    assert response.json()["field_errors"] == [
        {"field": "objectives[0]", "code": "INVALID_FORMAT"}
    ]
