from __future__ import annotations

import pytest

from sketch2life.application.ports.parent_story_runs import ParentStoryRevisionReservation
from sketch2life.application.services.parent_story_runs import (
    ParentStoryRunService,
    ParentStoryRunServiceError,
)
from sketch2life.contracts.schemas.modal_ai import ParentStoryRequestV1
from sketch2life.infrastructure.config.settings import Settings

_ACTIVITY = {
    "activity_ref": "draft_00000000-0000-0000-0000-000000000001_001",
    "title": "Quan sát lá ngoài trời",
    "objective": "Quan sát hình dáng lá quanh chủ đề con gà.",
    "materials_text": "Lá đã rụng và giấy.",
    "preparation_text": "Người lớn chọn khu vực sân chơi an toàn.",
    "instructions_text": (
        "Ngoài trời ở sân chơi, trẻ tự chọn lá đã rụng để quan sát; người lớn đi cùng."
    ),
    "observation_notes": "Ghi nhận điều trẻ tự chọn quan sát.",
    "safety_notes": "Không nếm lá; người lớn luôn giám sát.",
    "activity_kind": "outdoor",
    "source": "AI_GENERATED_DRAFT",
    "source_lesson_id": None,
    "source_lesson_title": None,
    "source_lesson_version_id": None,
    "source_content_sha256": None,
    "source_activity_index": None,
    "match_reason": "Bản nháp AI cần người lớn xem lại.",
}


class _Repository:
    def __init__(self) -> None:
        self.received: dict[str, object] | None = None

    def reserve_story_revision(self, **kwargs):
        self.received = kwargs
        return ParentStoryRevisionReservation(
            run_id=kwargs["run_id"],
            story_revision_id=kwargs["story_revision_id"],
            revision_no=1,
            understanding_revision=kwargs["expected_understanding_revision"],
            context_revision=1,
            source_asset_sha256="a" * 64,
            worker_input={},
            request_sha256="b" * 64,
        )


def test_story_request_requires_exact_selected_activity_pair_for_first_revision() -> None:
    payload = ParentStoryRequestV1.model_validate(
        {
            "expected_understanding_revision": 1,
            "primary_activity_request_id": "00000000-0000-0000-0000-000000000002",
            "primary_activity_ref": _ACTIVITY["activity_ref"],
        }
    )
    assert payload.primary_activity_request_id is not None
    with pytest.raises(ValueError, match="initial story requires"):
        ParentStoryRequestV1.model_validate({"expected_understanding_revision": 1})


def test_soft_gate_bypass_defaults_to_strict_and_cannot_be_enabled_in_production() -> None:
    assert Settings().parent_activity_soft_quality_gate_enabled is True
    with pytest.raises(ValueError, match="available only in local/test"):
        Settings(
            env="production",
            auth_provider="firebase",
            firebase_project_id="sketch2life-test",
            parent_activity_soft_quality_gate_enabled=False,
        )


def test_story_service_passes_server_snapshot_and_rejects_malformed_snapshot() -> None:
    repository = _Repository()
    service = ParentStoryRunService(repository)  # type: ignore[arg-type]
    service.reserve_story_revision(
        owner_subject="parent-1",
        policy_version="consent-v1",
        run_id="run-1",
        expected_understanding_revision=1,
        primary_activity=_ACTIVITY,
        rewrite_instruction=None,
        model_id="Qwen/Qwen3.5-9B",
        model_revision="c202236235762e1c871ad0ccb60c8ee5ba337b9a",
        prompt_version="parent-story-v3-primary-activity.2026-11-13",
    )
    assert repository.received is not None
    assert repository.received["primary_activity"] == _ACTIVITY

    with pytest.raises(
        ParentStoryRunServiceError,
        match="PARENT_PRIMARY_ACTIVITY_SNAPSHOT_INVALID",
    ):
        service.reserve_story_revision(
            owner_subject="parent-1",
            policy_version="consent-v1",
            run_id="run-1",
            expected_understanding_revision=1,
            primary_activity={"activity_ref": "client-injected"},
            rewrite_instruction=None,
            model_id="Qwen/Qwen3.5-9B",
            model_revision="c202236235762e1c871ad0ccb60c8ee5ba337b9a",
            prompt_version="parent-story-v3-primary-activity.2026-11-13",
        )
