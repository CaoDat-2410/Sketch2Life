from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

import sketch2life.interfaces.http.app as app_module
import sketch2life.interfaces.http.be1_runtime as runtime_module
import sketch2life.interfaces.http.routers.parent_ai as parent_ai
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_activity_suggestion_sets import (
    ActivitySelectionOutcome,
    ActivitySuggestionSetReservation,
)
from sketch2life.application.ports.parent_story_runs import ParentActivityContext
from sketch2life.infrastructure.config.settings import Settings
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult

_ISSUER = "activity-contract-issuer"
_PRINCIPAL = VerifiedPrincipal("parent-subject", _ISSUER, frozenset())
_RUN_ID = "55555555-5555-4555-8555-555555555555"
_SET_ID = "66666666-6666-4666-8666-666666666666"
_SELECTION_ID = "77777777-7777-4777-8777-777777777777"


def _catalog_activity(title: str) -> dict[str, str]:
    return {
        "title": title,
        "objective": "Tre quan sat mau canh buom va so sanh voi hoa.",
        "materials_text": "Giay ve va but mau.",
        "preparation_text": "Nguoi lon chon san vuon va dat giay tren ban.",
        "instructions_text": (
            "Ngoai troi trong vuon, tre tu chon goc an toan de quan sat buom; "
            "nguoi lon ho tro va moi tre mo ta mau sac."
        ),
        "observation_notes": "Ghi nhan cach tre so sanh mau canh buom va hoa.",
        "safety_notes": "Khong bat buom; nguoi lon giam sat tre.",
        "activity_kind": "outdoor",
    }


def _drafts() -> list[dict[str, str]]:
    return [
        _catalog_activity("Quan sat canh buom"),
        {
            "title": "Ve duong bay cua buom",
            "objective": "Tre thu nghiem ve va so sanh cac huong bay.",
            "materials_text": "Bang giay nho va but mau.",
            "preparation_text": "Nguoi huong dan chuan bi bang giay tai san truong.",
            "instructions_text": (
                "Tai san truong ngoai troi, tre tu quyet dinh cach ve duong bay sau khi "
                "quan sat; nguoi huong dan ho tro khi can."
            ),
            "observation_notes": "Quan sat cach tre chon huong va net ve.",
            "safety_notes": "Tranh chay nhanh; nguoi lon nhac tre giu khoang cach.",
            "activity_kind": "outdoor",
        },
        {
            "title": "Phan loai mau hoa va buom",
            "objective": "Tre phan loai mau giay theo sac tren canh buom va hoa.",
            "materials_text": "Mau giay cat san va tam bia.",
            "preparation_text": "Nguoi cham soc dat giay tren hien nha sach se.",
            "instructions_text": (
                "Ngoai troi ben hien nha, tre tu chon mau giay de phan loai sac tren canh "
                "buom; nguoi cham soc khuyen khich tre thu nghiem cach xep."
            ),
            "observation_notes": "Ghi nhan cach tre doi nhom va giai thich lua chon.",
            "safety_notes": "Khong nem giay; nguoi lon giup thu gon sau hoat dong.",
            "activity_kind": "outdoor",
        },
    ]


def _worker_output() -> dict[str, Any]:
    return {
        "schema_version": "sketch2life.parent-activity-suggestions.v2",
        "decision": "NO_MATCH",
        "selected_candidates": [],
        "no_match_reason": "No suitable catalog activity was found.",
        "age_band_months": "72-107",
        "fallback_activities": _drafts(),
    }


class _Repository:
    def __init__(self) -> None:
        self.reservation = ActivitySuggestionSetReservation(
            receipt_id="receipt-1",
            suggestion_set_id=_SET_ID,
            set_revision=4,
            context=ParentActivityContext(
                run_id=_RUN_ID,
                run_revision=5,
                understanding_revision=2,
                context_snapshot={
                    "age_months": 84,
                    "topic": "buom",
                    "adult_confirmed_idea": "private adult idea",
                    "interests_summary": "private profile interests",
                },
                subject_label="private child name",
                visible_features=["private drawing feature"],
                lesson_pin_snapshot=None,
            ),
        )
        self.completed: list[dict[str, Any]] = []
        self.failed: list[dict[str, Any]] = []

    def reserve_activity_suggestion_set(self, **_kwargs: Any) -> ActivitySuggestionSetReservation:
        return self.reservation

    def complete_activity_suggestion_set(self, *, response: Any, **_kwargs: Any) -> dict[str, Any]:
        body = dict(response)
        self.completed.append(body)
        return body

    def fail_activity_suggestion_set(self, **kwargs: Any) -> None:
        self.failed.append(kwargs)


class _SelectionService:
    def __init__(self) -> None:
        self.candidates: tuple[Any, ...] = ()
        self.selection_outcome = ActivitySelectionOutcome(
            receipt_body={
                "contract": "ParentActivitySelectionReceiptV1",
                "request_id": "88888888-8888-4888-8888-888888888888",
                "story_run_id": _RUN_ID,
                "suggestion_set_id": _SET_ID,
                "activity_selection_id": _SELECTION_ID,
                "selection_revision": 1,
                "understanding_revision": 2,
                "activity_index": 1,
                "activity_snapshot_sha256": "a" * 64,
                "persisted_at": datetime(2026, 11, 25, tzinfo=UTC),
            }
        )
        self.selection_call: dict[str, Any] | None = None

    def prepare_suggestion_candidates(self, **_kwargs: Any) -> tuple[object, tuple[Any, ...]]:
        return object(), self.candidates

    def select_suggestion_set_activity(self, **kwargs: Any) -> ActivitySelectionOutcome:
        self.selection_call = kwargs
        return self.selection_outcome


class _Harness:
    def __init__(self) -> None:
        self.settings: Any = None
        self.repository = _Repository()
        self.selection = _SelectionService()


@pytest.fixture
def harness(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[TestClient, _Harness]]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    settings = Settings(
        env="test",
        auth_provider="firebase",
        firebase_project_id="activity-contract-project",
        ai_provider="modal_dev",
        parent_topic_subject_ai_enabled=False,
        _env_file=None,  # type: ignore[call-arg]
    )
    state = _Harness()
    state.settings = settings
    monkeypatch.setattr(app_module, "get_settings", lambda: settings)
    monkeypatch.setattr(parent_ai, "get_settings", lambda: settings)
    monkeypatch.setattr(
        runtime_module,
        "get_core_database_settings",
        lambda: SimpleNamespace(database_url=None),
    )
    monkeypatch.setattr(parent_ai, "_require_parent", lambda _db, _principal: None)
    monkeypatch.setattr(
        parent_ai,
        "SqlParentActivitySuggestionSetRepository",
        lambda _db: state.repository,
    )
    monkeypatch.setattr(
        parent_ai,
        "_activity_selection_service",
        lambda _request, _db, _repository: state.selection,
    )
    monkeypatch.setattr(parent_ai, "schedule_first_story", lambda *_args: None)
    application = app_module.create_app()
    application.dependency_overrides[get_verified_adult] = lambda: _PRINCIPAL
    application.dependency_overrides[get_db] = lambda: SimpleNamespace(commit=lambda: None)
    try:
        with TestClient(application, raise_server_exceptions=False) as client:
            yield client, state
    finally:
        application.dependency_overrides.clear()


def _post_suggestions(client: TestClient, *, key: str = "suggestions-key"):
    return client.post(
        f"/api/parent/v1/ai/story-runs/{_RUN_ID}/activity-suggestions",
        headers={"Idempotency-Key": key},
        json={"expected_understanding_revision": 2},
    )


def _candidate(index: int) -> Any:
    return SimpleNamespace(
        activity={
            "title": f"Catalog garden card {index}",
            "objective": "Observe shapes formed by stones near a walking path.",
            "materials_text": "A small observation card and colored pencils.",
            "preparation_text": "An adult chooses a clear route beside the garden.",
            "instructions_text": (
                "Outside, the child observes stones along the path with an adult nearby "
                "and chooses one shape to describe."
            ),
            "observation_notes": "Record which shapes the child notices.",
            "safety_notes": "Stay on the clear path with adult supervision.",
            "activity_kind": "outdoor",
        },
        source="PUBLIC",
        lesson_id=f"lesson-{index}",
        lesson_title=f"Lesson {index}",
        version_id=f"version-{index}",
        content_sha256=f"{index:064x}",
        activity_index=0,
    )


def test_catalog_candidates_are_returned_without_a_modal_call(
    harness: tuple[TestClient, _Harness], monkeypatch: pytest.MonkeyPatch
) -> None:
    client, state = harness
    state.selection.candidates = tuple(_candidate(index) for index in range(1, 4))

    class _NoModal:
        def __init__(self) -> None:
            raise AssertionError("catalog-first suggestions must not invoke Modal")

    monkeypatch.setattr(parent_ai, "ModalJsonFunctionClient", _NoModal)
    response = _post_suggestions(client)

    assert response.status_code == 200
    body = response.json()
    assert body["contract"] == "ParentActivitySuggestionSetV1"
    assert body["suggestion_set_id"] == _SET_ID
    assert body["set_revision"] == 4
    assert body["selection_mode"] == "CATALOG_SELECTION"
    assert body["catalog_candidate_count"] == 3
    assert body["modal_call_id"] is None
    assert len(body["activities"]) == 3
    assert {item["source"] for item in body["activities"]} == {"PUBLISHED_SHARED_LESSON"}
    assert len(state.repository.completed) == 1
    assert response.headers["Idempotency-Replayed"] == "false"


def test_sparse_catalog_uses_sanitized_fallback_worker_input_and_returns_gated_drafts(
    harness: tuple[TestClient, _Harness], monkeypatch: pytest.MonkeyPatch
) -> None:
    client, state = harness
    state.settings.parent_topic_subject_ai_enabled = True
    state.selection.candidates = tuple(_candidate(index) for index in range(1, 3))
    calls: list[tuple[str, dict[str, Any]]] = []

    class _Modal:
        def invoke(self, workload: str, request_data: dict[str, Any]) -> Any:
            calls.append((workload, request_data))
            return SimpleNamespace(
                output={"result": _worker_output()},
                call_id="fc-activity-contract",
                elapsed_seconds=0.1,
            )

    monkeypatch.setattr(parent_ai, "ModalJsonFunctionClient", _Modal)
    response = _post_suggestions(client, key="fallback-key")

    assert response.status_code == 200
    body = response.json()
    assert body["selection_mode"] == "AI_GENERATED_FALLBACK"
    assert body["catalog_candidate_count"] == 2
    assert body["modal_call_id"] == "fc-activity-contract"
    assert len(body["activities"]) == 5
    assert [item["source"] for item in body["activities"]].count(
        "PUBLISHED_SHARED_LESSON"
    ) == 2
    assert [item["source"] for item in body["activities"]].count("AI_GENERATED_DRAFT") == 3
    assert len(calls) == 1 and calls[0][0] == "parent.activity.suggest"
    worker_input = calls[0][1]
    assert worker_input["topic"] == "buom"
    assert worker_input["age_band_months"] == "72-107"
    assert worker_input["adult_confirmed_idea"] == ""
    assert worker_input["candidate_activities"] == []
    assert "private adult idea" not in str(worker_input)
    assert "private profile interests" not in str(worker_input)
    assert "private child name" not in str(worker_input)
    assert "private drawing feature" not in str(worker_input)


def test_sparse_catalog_without_ai_capability_returns_catalog_items_without_modal(
    harness: tuple[TestClient, _Harness], monkeypatch: pytest.MonkeyPatch
) -> None:
    client, state = harness
    state.selection.candidates = (_candidate(1), _candidate(2))

    class _NoModal:
        def __init__(self) -> None:
            raise AssertionError("the disabled AI path must not invoke Modal")

    monkeypatch.setattr(parent_ai, "ModalJsonFunctionClient", _NoModal)
    response = _post_suggestions(client, key="ai-disabled-key")

    assert response.status_code == 200
    body = response.json()
    assert body["selection_mode"] == "CATALOG_SELECTION"
    assert body["catalog_candidate_count"] == 2
    assert len(body["activities"]) == 2
    assert {item["source"] for item in body["activities"]} == {"PUBLISHED_SHARED_LESSON"}
    assert state.repository.failed == []


def test_no_catalog_and_disabled_ai_leaves_the_generation_receipt_retryable(
    harness: tuple[TestClient, _Harness], monkeypatch: pytest.MonkeyPatch
) -> None:
    client, state = harness

    class _NoModal:
        def __init__(self) -> None:
            raise AssertionError("the disabled AI path must not invoke Modal")

    monkeypatch.setattr(parent_ai, "ModalJsonFunctionClient", _NoModal)
    response = _post_suggestions(client, key="ai-disabled-empty-key")

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "MODAL_AI_NOT_ENABLED"
    assert len(state.repository.failed) == 1
    assert state.repository.failed[0]["error_code"] == "MODAL_AI_NOT_ENABLED"
    assert state.repository.failed[0]["response_status"] == 503
    assert state.repository.failed[0]["cache_failure"] is False


def test_deterministic_draft_gate_rejection_is_cached_as_502(
    harness: tuple[TestClient, _Harness], monkeypatch: pytest.MonkeyPatch
) -> None:
    client, state = harness
    state.settings.parent_topic_subject_ai_enabled = True
    unsafe_output = _worker_output()
    unsafe_output["fallback_activities"][0]["title"] = "Tre leo len hang rao"

    class _Modal:
        def invoke(self, _workload: str, _request_data: dict[str, Any]) -> Any:
            return SimpleNamespace(
                output={"result": unsafe_output},
                call_id="fc-unsafe-activity",
                elapsed_seconds=0.1,
            )

    monkeypatch.setattr(parent_ai, "ModalJsonFunctionClient", _Modal)
    response = _post_suggestions(client, key="unsafe-gate-key")

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "MODAL_OUTPUT_CONTRACT_INVALID"
    assert len(state.repository.failed) == 1
    assert state.repository.failed[0]["cache_failure"] is True
    assert state.repository.failed[0]["response_status"] == 502


def test_modal_timeout_leaves_the_generation_receipt_retryable(
    harness: tuple[TestClient, _Harness], monkeypatch: pytest.MonkeyPatch
) -> None:
    client, state = harness
    state.settings.parent_topic_subject_ai_enabled = True

    class _Modal:
        def invoke(self, _workload: str, _request_data: dict[str, Any]) -> Any:
            raise parent_ai.ModalFunctionOutcomeUnknown("fc-timeout")

    monkeypatch.setattr(parent_ai, "ModalJsonFunctionClient", _Modal)
    response = _post_suggestions(client, key="timeout-retry-key")

    assert response.status_code == 504
    assert response.json()["detail"]["code"] == "MODAL_OUTCOME_UNKNOWN"
    assert state.repository.failed[0]["cache_failure"] is False


def test_activity_selection_returns_the_persisted_receipt_and_uses_idempotency_key(
    harness: tuple[TestClient, _Harness]
) -> None:
    client, state = harness
    response = client.post(
        f"/api/parent/v1/ai/story-runs/{_RUN_ID}/activity-selection",
        headers={"Idempotency-Key": "selection-key"},
        json={
            "suggestion_set_id": _SET_ID,
            "expected_understanding_revision": 2,
            "activity_index": 1,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "contract": "ParentActivitySelectionReceiptV1",
        "request_id": "88888888-8888-4888-8888-888888888888",
        "story_run_id": _RUN_ID,
        "suggestion_set_id": _SET_ID,
        "activity_selection_id": _SELECTION_ID,
        "selection_revision": 1,
        "understanding_revision": 2,
        "activity_index": 1,
        "activity_snapshot_sha256": "a" * 64,
        "persisted_at": "2026-11-25T00:00:00Z",
    }
    assert state.selection.selection_call is not None
    assert state.selection.selection_call["idempotency_key"] == "selection-key"
    assert state.selection.selection_call["suggestion_set_id"] == _SET_ID


def test_openapi_publishes_the_versioned_activity_request_and_response_shapes(
    harness: tuple[TestClient, _Harness],
) -> None:
    client, _state = harness
    spec = client.app.openapi()  # type: ignore[attr-defined]
    schemas = spec["components"]["schemas"]
    suggestions = spec["paths"][
        "/api/parent/v1/ai/story-runs/{run_id}/activity-suggestions"
    ]["post"]
    selection = spec["paths"][
        "/api/parent/v1/ai/story-runs/{run_id}/activity-selection"
    ]["post"]

    assert set(schemas["ParentActivitySuggestionsRequestV1"]["properties"]) == {
        "expected_understanding_revision"
    }
    assert schemas["ParentActivitySuggestionSetV1"]["properties"]["activities"]["maxItems"] == 24
    selection_request_ref = selection["requestBody"]["content"]["application/json"]["schema"][
        "$ref"
    ]
    selection_request_name = selection_request_ref.rsplit("/", maxsplit=1)[-1]
    assert set(schemas[selection_request_name]["properties"]) == {
        "suggestion_set_id",
        "expected_understanding_revision",
        "activity_index",
    }
    assert set(schemas["ParentActivitySelectionReceiptV1"]["properties"]) >= {
        "suggestion_set_id",
        "activity_selection_id",
        "selection_revision",
    }
    for operation in (suggestions, selection):
        key = next(
            parameter
            for parameter in operation["parameters"]
            if parameter["name"] == "Idempotency-Key"
        )
        assert key["required"] is True and key["schema"]["maxLength"] == 200
