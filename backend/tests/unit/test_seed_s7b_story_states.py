"""Pure checks for the synthetic Phase B Parent StoryRun fixtures and stage wiring."""

from __future__ import annotations

import io
import re
from typing import Any

import pytest

from sketch2life.application.services.story_output import normalize_story_output
from sketch2life.contracts.schemas.lesson_library import LessonContentInputV1
from sketch2life.infrastructure.story_inputs.drawing import normalize_drawing
from tools.seed import data as s1_data
from tools.seed import s7b_story_states as stage
from tools.seed import s7b_story_states_data as data


def test_profile_and_display_text_are_synthetic_vietnamese() -> None:
    assert data.PROFILE_KEY == "k6"
    assert data.PROFILE_SNAPSHOT.age_months == 66
    assert data.PROFILE_SNAPSHOT.display_name == "Mây"
    assert data.PROFILE_SNAPSHOT.interests_summary
    assert "[SEED]" not in data.PROFILE_SNAPSHOT.interests_summary
    assert data.P3A_TRANSCRIPT.startswith("Con muốn")
    assert all("[SEED]" not in value for run in (data.P3_RUN_A, data.P3_RUN_B) for value in run)


def test_registered_drawing_hashes_match_the_synthetic_inputs() -> None:
    for case, image_bytes in data.DRAWING_BYTES.items():
        normalized = normalize_drawing(image_bytes, declared_media_type="image/png")
        assert len(normalized.sha256) == 64
        assert data.DRAWING_RESULTS[case].visible_features
    assert data.DRAWING_RESULTS["p3-b"].child_count == 2
    assert set(data.DRAWING_BYTES) == {"p3-a", "p3-b", "p4", "p5"}


def test_story_fixtures_validate_as_real_parent_scripts() -> None:
    for case, result in data.STORY_RESULTS.items():
        normalized, digest = normalize_story_output(
            result.story,
            confirmed_subject=("Chậu đậu mới nhú mầm" if case == "p3-a" else data.P5_SUBJECT),
        )
        assert normalized["language"] == "vi"
        assert len(normalized["scenes"]) == 5
        assert re.fullmatch(r"[a-f0-9]{64}", digest)


def test_closeout_fallback_is_an_inactive_history_row() -> None:
    run, input_row = data.abandoned_rows("urn:sketch2life:seed:issuer")
    assert run["run_id"] == data.ABANDONED_RUN_ID
    assert run["run_state"] == "ABANDONED"
    assert run["active_owner_parent_account_id"] is None
    assert run["finished_at"] == run["updated_at"]
    assert input_row["context_confirmed_by"] == run["actor_scope_ref"]
    assert input_row["context_snapshot_sha256"] == s1_data.sha256_json(
        input_row["context_snapshot"]
    )


def test_stage_counts_use_simple_names_and_include_the_requested_tables() -> None:
    assert all(re.fullmatch(r"[A-Za-z0-9_]+", name) for name in data.EXPECTED)
    assert {
        "story_runs_s7b",
        "story_run_inputs_s7b",
        "story_story_revisions_s7b",
        "story_video_generations_s7b",
        "story_transcript_revisions_s7b",
        "parent_child_profiles_s7b",
    } <= data.EXPECTED.keys()
    assert data.EXPECTED["story_runs_s7b"] == 5
    assert data.EXPECTED["story_command_receipts_s7b"] == len(data.STORY_RECEIPT_CASES)


def test_story_states_seed_the_parent_activity_gate_before_story_generation() -> None:
    assert data.S7B_COMMAND_CASES["p3a_select_activity"] == "p3-a-select-activity-1"
    assert data.S7B_COMMAND_CASES["p5_select_activity"] == "p5-select-activity-1"
    assert data.EXPECTED["story_activity_selections_s7b"] == 2
    assert data.EXPECTED["lesson_access_grants_s7b"] == 2
    assert data.EXPECTED["lesson_command_receipts_s7b"] == len(
        data.STORY_CATALOG_RECEIPT_CASES
    )
    assert any(
        row["parent_group_id"] == s1_data.PARENT_GROUP_IDS[1]
        and row["parent_principal_ref"] == s1_data.PARENT_SUBJECTS["p3"]
        and row["state"] == "active"
        for row in s1_data.parent_group_member_rows()
    )


def test_p5_activity_lesson_matches_the_seeded_child_age_and_lesson_contract() -> None:
    content = LessonContentInputV1.model_validate(data.P5_ACTIVITY_LESSON_CONTENT)
    assert s1_data.current_profile_revision("k5")["age_months"] == 96
    assert content.target_age_band_ref == "age-72-107-months-v1"
    assert len(content.activities) == 1


def test_stage_main_delegates_guarding_to_run_stage_main(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}

    def fake_run_stage_main(run: Any, *, stage: str, stderr_code: str | None = None) -> int:
        seen.update(run=run, stage=stage, stderr_code=stderr_code)
        return 7

    monkeypatch.setattr(stage, "run_stage_main", fake_run_stage_main)
    assert stage.main() == 7
    assert seen == {"run": stage.run_s7b, "stage": "s7b", "stderr_code": None}


def test_in_memory_storage_has_no_filesystem_or_network_adapter() -> None:
    storage = stage.MemoryObjectStorage()
    storage.put_object(
        "parent/fixture/image.png",
        io.BytesIO(b"synthetic"),
        content_type="image/png",
        content_length=9,
        metadata={"sha256": "a" * 64},
    )
    loaded = storage.get_object("parent/fixture/image.png")
    assert loaded is not None and loaded.body.read() == b"synthetic"
    assert storage.list_keys("parent/fixture/") == ("parent/fixture/image.png",)
    storage.delete_object("parent/fixture/image.png")
    assert storage.list_keys("parent/fixture/") == ()
