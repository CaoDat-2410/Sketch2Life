"""PostgreSQL gate coverage for Modal-backed Teacher SVG drafts; not run in this task."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from sqlalchemy import func, select
from test_child_selection_postgres import Api, _build, headers, make_occurrence

from sketch2life.domain.lesson_occurrences.safety_checklist import (
    ChecklistDefinition,
    ChecklistItem,
    ChecklistRegistry,
)
from sketch2life.infrastructure.ai.modal_function_client import (
    MODEL_ID,
    MODEL_REVISION,
    ModalFunctionExecutionFailed,
    ModalJsonFunctionResult,
)
from sketch2life.infrastructure.lesson_occurrences.presentation_svg_fake import (
    DeterministicPresentationSvgDrafter,
)
from sketch2life.infrastructure.lesson_occurrences.presentation_svg_modal import (
    ModalPresentationSvgDrafter,
)
from sketch2life.infrastructure.lesson_occurrences.presentations import (
    SVG_CREATE_SCOPE,
    SVG_DRAFTS_PER_24H,
)
from sketch2life.infrastructure.lesson_occurrences.tables import (
    PRESENTATION_SVG_DRAFTS,
)
from sketch2life.infrastructure.persistence.be1_models import Be1CommandReceiptModel
from sketch2life.interfaces.http.routers.lesson_occurrences import get_checklist_registry

pytestmark = pytest.mark.integration


@pytest.fixture
def presentation_api(monkeypatch: pytest.MonkeyPatch) -> Iterator[Api]:
    yield from _build(monkeypatch, real_service=True, pilot=True)


class _FakeModalClient:
    def __init__(self, *responses: object) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def invoke(self, workload: str, request_data: dict[str, Any]) -> ModalJsonFunctionResult:
        self.calls.append((workload, dict(request_data)))
        if not self.responses:
            raise AssertionError("the adapter dispatched more than the supplied responses")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return ModalJsonFunctionResult(
            output={
                "model": {"id": MODEL_ID, "revision": MODEL_REVISION},
                "result": response,
            },
            call_id=f"fc-presentation-svg-{len(self.calls)}",
            elapsed_seconds=0.5,
        )


def _valid_worker_result() -> dict[str, Any]:
    return {
        "schema_version": "sketch2life.presentation-svg-draft.v1",
        "review_required": True,
        "viewbox": [0, 0, 100, 100],
        "shapes": [
            {
                "kind": "circle",
                "cx": 20,
                "cy": 20,
                "r": 8,
                "stroke": "#1f2937",
                "stroke_width": 2,
            },
            {
                "kind": "rect",
                "x": 40,
                "y": 12,
                "w": 24,
                "h": 18,
                "stroke": "#2563eb",
                "stroke_width": 3,
            },
            {
                "kind": "polyline",
                "points": [[12, 72], [22, 60], [32, 72]],
                "stroke": "#16a34a",
                "stroke_width": 2,
            },
            {
                "kind": "line",
                "x1": 5,
                "y1": 40,
                "x2": 20,
                "y2": 45,
                "stroke": "#dc2626",
                "stroke_width": 1,
            },
        ],
    }


def _approved_custom_activity(api: Api, occurrence_id: str) -> str:
    registry = ChecklistRegistry(
        (
            ChecklistDefinition(
                "synthetic-v1", (ChecklistItem("synthetic-item", "Synthetic safety item"),)
            ),
        )
    )
    api.app.dependency_overrides[get_checklist_registry] = lambda: registry
    base = f"/v1/lesson-occurrences/{occurrence_id}/plan-revisions"
    draft = api.client.post(
        base,
        json={
            "expected_head_revision_no": 1,
            "objectives": ["Synthetic objective"],
            "teacher_direction": "Synthetic direction",
            "activities": [
                {"kind": "CUSTOM", "title": "Synthetic activity", "description": "Synthetic"}
            ],
        },
        headers=headers(api.subjects["t1"], "presentation-modal-custom-plan-create"),
    )
    assert draft.status_code == 201, draft.text
    confirmed = api.client.post(
        f"{base}/{draft.json()['revision_no']}/confirm",
        json={
            "expected_plan_hash": draft.json()["content_hash"],
            "checklist": [
                {
                    "activity_order": 1,
                    "checklist_version": "synthetic-v1",
                    "items": [{"item_id": "synthetic-item", "checked": True}],
                }
            ],
        },
        headers=headers(api.subjects["t1"], "presentation-modal-custom-plan-confirm"),
    )
    assert confirmed.status_code == 200, confirmed.text
    return str(confirmed.json()["activities"][0]["plan_activity_id"])


def _create_presentation(api: Api, occurrence_id: str, key: str) -> Any:
    response = api.client.post(
        f"/v1/lesson-occurrences/{occurrence_id}/presentation",
        json={"seed": "BLANK"},
        headers=headers(api.subjects["t1"], key),
    )
    assert response.status_code == 201, response.text
    return response


def _create_svg_draft(api: Api, occurrence_id: str, activity_id: str, key: str) -> Any:
    return api.client.post(
        f"/v1/lesson-occurrences/{occurrence_id}/presentation/svg-drafts",
        json={"plan_activity_id": activity_id, "subject_text": "butterfly"},
        headers=headers(api.subjects["t1"], key),
    )


def _counts(api: Api, occurrence_id: str, presentation_id: str, key: str) -> tuple[int, int]:
    scope = SVG_CREATE_SCOPE.replace("{occurrence_id}", occurrence_id)
    with api.sessions()() as db:
        draft_count = db.scalar(
            select(func.count())
            .select_from(PRESENTATION_SVG_DRAFTS)
            .where(PRESENTATION_SVG_DRAFTS.c.presentation_id == presentation_id)
        )
        receipt_count = db.scalar(
            select(func.count())
            .select_from(Be1CommandReceiptModel)
            .where(
                Be1CommandReceiptModel.operation_scope == scope,
                Be1CommandReceiptModel.idempotency_key == key,
            )
        )
    return int(draft_count or 0), int(receipt_count or 0)


def test_modal_adapter_create_is_pending_and_idempotency_replays_without_dispatch(
    presentation_api: Api,
) -> None:
    api = presentation_api
    occurrence = make_occurrence(api)
    created_presentation = _create_presentation(
        api, occurrence.occurrence_id, "presentation-modal-create"
    )
    activity_id = _approved_custom_activity(api, occurrence.occurrence_id)
    client = _FakeModalClient(_valid_worker_result())
    api.app.state.presentation_svg_drafter = ModalPresentationSvgDrafter(client)
    key = "presentation-modal-svg-create"

    created = _create_svg_draft(api, occurrence.occurrence_id, activity_id, key)
    replay = _create_svg_draft(api, occurrence.occurrence_id, activity_id, key)

    assert created.status_code == replay.status_code == 201
    assert replay.json() == created.json()
    assert len(client.calls) == 1
    assert set(client.calls[0][1]) == {
        "schema_version",
        "activity_title",
        "subject_text",
        "content_hash",
    }
    assert created.json()["state"] == "PENDING_REVIEW"
    assert _counts(
        api,
        occurrence.occurrence_id,
        created_presentation.json()["presentation_id"],
        key,
    ) == (1, 1)


def test_provider_unavailable_leaves_no_receipt_and_same_key_can_retry(
    presentation_api: Api,
) -> None:
    api = presentation_api
    occurrence = make_occurrence(api)
    created_presentation = _create_presentation(
        api, occurrence.occurrence_id, "presentation-modal-unavailable"
    )
    activity_id = _approved_custom_activity(api, occurrence.occurrence_id)
    client = _FakeModalClient(
        ModalFunctionExecutionFailed("PROVIDER_UNAVAILABLE"), _valid_worker_result()
    )
    api.app.state.presentation_svg_drafter = ModalPresentationSvgDrafter(client)
    key = "presentation-modal-svg-unavailable-retry"

    unavailable = _create_svg_draft(api, occurrence.occurrence_id, activity_id, key)
    assert unavailable.status_code == 503
    assert unavailable.json()["code"] == "PROVIDER_UNAVAILABLE"
    assert _counts(
        api,
        occurrence.occurrence_id,
        created_presentation.json()["presentation_id"],
        key,
    ) == (0, 0)

    succeeded = _create_svg_draft(api, occurrence.occurrence_id, activity_id, key)
    assert succeeded.status_code == 201, succeeded.text
    assert succeeded.json()["state"] == "PENDING_REVIEW"
    assert len(client.calls) == 2
    assert _counts(
        api,
        occurrence.occurrence_id,
        created_presentation.json()["presentation_id"],
        key,
    ) == (1, 1)


def test_bad_provider_geometry_returns_502_without_row_or_receipt(
    presentation_api: Api,
) -> None:
    api = presentation_api
    occurrence = make_occurrence(api)
    created_presentation = _create_presentation(
        api, occurrence.occurrence_id, "presentation-modal-bad-output"
    )
    activity_id = _approved_custom_activity(api, occurrence.occurrence_id)
    bad_result = _valid_worker_result()
    bad_result["shapes"][0]["style"] = "fill:url(https://example.invalid)"
    client = _FakeModalClient(bad_result)
    api.app.state.presentation_svg_drafter = ModalPresentationSvgDrafter(client)
    key = "presentation-modal-svg-bad-output"

    response = _create_svg_draft(api, occurrence.occurrence_id, activity_id, key)

    assert response.status_code == 502
    assert response.json()["code"] == "PROVIDER_BAD_RESPONSE"
    assert len(client.calls) == 1
    assert _counts(
        api,
        occurrence.occurrence_id,
        created_presentation.json()["presentation_id"],
        key,
    ) == (0, 0)


def test_cap_is_checked_before_modal_dispatch(presentation_api: Api) -> None:
    api = presentation_api
    occurrence = make_occurrence(api)
    created_presentation = _create_presentation(
        api, occurrence.occurrence_id, "presentation-modal-cap"
    )
    activity_id = _approved_custom_activity(api, occurrence.occurrence_id)
    api.app.state.presentation_svg_drafter = DeterministicPresentationSvgDrafter()
    for index in range(SVG_DRAFTS_PER_24H):
        seeded = _create_svg_draft(
            api,
            occurrence.occurrence_id,
            activity_id,
            f"presentation-modal-cap-seed-{index}",
        )
        assert seeded.status_code == 201, seeded.text

    client = _FakeModalClient(_valid_worker_result())
    api.app.state.presentation_svg_drafter = ModalPresentationSvgDrafter(client)
    capped = _create_svg_draft(
        api, occurrence.occurrence_id, activity_id, "presentation-modal-cap-exhausted"
    )

    assert capped.status_code == 429
    assert capped.json()["code"] == "RATE_LIMITED"
    assert client.calls == []
    with api.sessions()() as db:
        presentation_id = created_presentation.json()["presentation_id"]
        states = (
            db.execute(
                select(PRESENTATION_SVG_DRAFTS.c.state).where(
                    PRESENTATION_SVG_DRAFTS.c.presentation_id == presentation_id
                )
            )
            .scalars()
            .all()
        )
    assert len(states) == SVG_DRAFTS_PER_24H
