from __future__ import annotations

from uuid import UUID

import pytest

from sketch2life.contracts.schemas.modal_ai import ParentActivitySuggestionResponseV1


@pytest.mark.parametrize("source", ["QWEN3_5_MODAL", "QWEN3_8_MODAL"])
def test_backend_accepts_both_modal_source_literals(source: str) -> None:
    response = ParentActivitySuggestionResponseV1.model_validate(
        {
            "request_id": UUID("a0000000-0000-4000-8000-000000000001"),
            "story_run_id": UUID("b0000000-0000-4000-8000-000000000002"),
            "understanding_revision": 1,
            "source": source,
            "source_lesson_version_id": None,
            "review_required": True,
            "activities": [
                {
                    "title": "Observe a leaf",
                    "objective": "Notice its shape.",
                    "materials_text": "",
                    "preparation_text": "Stay with an adult.",
                    "instructions_text": "Look without picking it.",
                    "observation_notes": "",
                    "safety_notes": "Stay on the path.",
                    "activity_kind": "outdoor",
                }
            ],
        }
    )

    assert response.source == source
