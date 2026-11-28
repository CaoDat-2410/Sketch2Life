from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from sketch2life.contracts.schemas.parent_story_runs import (
    ParentActivityV1,
    ParentMainActivityV1,
)
from sketch2life.infrastructure.persistence import parent_story_repository
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
)


def test_ai_draft_selection_projects_as_a_valid_parent_activity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected_at = datetime(2026, 11, 25, 8, 30, tzinfo=UTC)
    selection = {
        "source_kind": "AI_DRAFT",
        "activity_snapshot": {
            "schema": "sketch2life.parent-activity-suggestion.v2",
            "title": "Observe a rounded shape",
            "objective": "Notice one visible detail.",
            "materials_text": "Paper and pencils.",
            "preparation_text": "Prepare a clear space.",
            "instructions_text": "Observe the shape with an adult nearby.",
            "observation_notes": "Ask which detail stands out.",
            "safety_notes": "Stay with an adult.",
            "activity_kind": "outdoor",
            "source": "AI_GENERATED_DRAFT",
            "source_lesson_id": None,
            "source_lesson_title": None,
            "source_lesson_version_id": None,
            "source_content_sha256": None,
            "source_activity_index": None,
            "match_reason": None,
            "selected_at": selected_at.isoformat(),
        },
    }
    monkeypatch.setattr(
        parent_story_repository,
        "latest_selection_row",
        lambda _session, run_id, revision: selection
        if run_id == "run-draft" and revision == 4
        else None,
    )
    repository = object.__new__(SqlParentStoryRunRepository)
    repository._session = None

    main, post_video = repository._activity_view(
        {
            "run_id": "run-draft",
            "understanding_revision": 4,
            "run_state": "PREPARATION_REVIEW",
        },
        {},
    )

    response = ParentMainActivityV1.model_validate(main)
    selected = ParentActivityV1.model_validate(response.selected)
    assert selected.activity_ref is None
    assert selected.source == "AI_DRAFT"
    assert selected.title == "Observe a rounded shape"
    assert selected.lesson_title == ""
    assert selected.lesson_topic == ""
    assert response.selected_at == selected_at
    assert post_video is None
    with pytest.raises(ValidationError, match="Catalog activities require a lesson reference"):
        ParentActivityV1.model_validate({**selected.model_dump(), "source": "PUBLIC"})
