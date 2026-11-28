from __future__ import annotations

import importlib.util
import inspect
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
MODAL_DIR = Path(__file__).resolve().parents[1]
BACKEND_SRC = REPO_ROOT / "backend" / "src"
for import_path in (str(MODAL_DIR), str(BACKEND_SRC)):
    if import_path not in sys.path:
        sys.path.insert(0, import_path)

from contracts import L4_WORKLOADS


def _load_worker(module_name: str, filename: str):
    spec = importlib.util.spec_from_file_location(module_name, MODAL_DIR / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


worker = _load_worker("sketch2life_dev_story_registry", "language_audio_app.py")
drawing_worker = _load_worker("sketch2life_dev_drawing_registry", "drawing_vlm_app.py")


def _registry() -> dict[str, object]:
    return json.loads((MODAL_DIR / "workloads.json").read_text(encoding="utf-8"))


def _entry(workload_id: str) -> dict[str, object]:
    entries = _registry()["workloads"]
    return next(item for item in entries if item["id"] == workload_id)


def _parent_input(**changes: object) -> dict[str, object]:
    return {
        "schema_version": "sketch2life.story-generation-input.v3",
        "role": "PARENT",
        "language": "vi",
        "topic": "animals",
        "confirmed_subject": "butterfly",
        "understanding_revision": 1,
        "drawing_sha256": "a" * 64,
        "visible_features": ["two wings"],
        "child_age_months": 60,
        "context_revision": 1,
        "adult_confirmed_idea": "A safe story.",
        "rewrite_instruction": None,
        "lesson_subject_learning_notes": None,
        "lesson_direction": None,
        "primary_activity": {
            "title": "Observe a garden",
            "objective": "Notice colors.",
            "materials_text": "",
            "preparation_text": "",
            "instructions_text": "Observe with an adult.",
            "observation_notes": "",
            "safety_notes": "Stay with an adult.",
            "activity_kind": "outdoor",
        },
        "primary_activity_sha256": "b" * 64,
        **changes,
    }


def test_story_workload_is_disabled_and_admitted_in_l4() -> None:
    entry = _entry("story.generate")
    assert entry["execution_group"] == "l4"
    assert entry["enabled"] is False
    assert "story.generate" in L4_WORKLOADS
    assert "story.generate.q38" not in L4_WORKLOADS


def test_story_registry_uses_the_dev_qwen38_candidate() -> None:
    entry = _entry("story.generate")
    assert entry["candidate"] == (
        "Qwen/Qwen3.8-27B-FP8@c3a462cc3d38cf351f3b26cbd763469eeb74ef81"
    )
    assert worker.TEXT_MODEL_ID == "Qwen/Qwen3.8-27B-FP8"
    assert worker.TEXT_MODEL_REVISION == "c3a462cc3d38cf351f3b26cbd763469eeb74ef81"


def test_drawing_worker_uses_the_shared_dev_model_revision() -> None:
    assert drawing_worker.MODEL_ID == worker.TEXT_MODEL_ID
    assert drawing_worker.MODEL_REVISION == worker.TEXT_MODEL_REVISION


def test_story_registry_has_no_qwen35_fallback_selector() -> None:
    entry = _entry("story.generate")
    assert "fallback_candidate" not in entry
    assert "qwen35" not in json.dumps(entry).casefold()


def test_retired_topic_suggest_and_sketch_guide_are_not_dispatchable() -> None:
    assert "parent.topic-subjects.suggest" not in L4_WORKLOADS
    assert "parent.sketch-guide.generate" not in L4_WORKLOADS
    assert _entry("parent.topic-subjects.suggest")["enabled"] is False
    assert _entry("parent.sketch-guide.generate")["enabled"] is False


def test_shared_worker_router_omits_retired_dispatches() -> None:
    routes = worker._shared_qwen_routes()
    assert "parent.topic-subjects.suggest" not in routes
    assert "parent.sketch-guide.generate" not in routes
    assert "parent.topic-subjects.validate" in routes


def test_dev_story_handler_validates_v3_parent_schema() -> None:
    source = inspect.getsource(worker.generate_story_and_storyboard)
    assert '"sketch2life.story-generation-input.v3"' in source
    assert 'data.get("role") != "PARENT"' in source
    assert '"primary_activity_sha256"' in source


def test_story_handler_requires_bounded_activity_text_and_hash() -> None:
    source = inspect.getsource(worker.generate_story_and_storyboard)
    assert '"primary_activity"' in source
    assert '"instructions_text"' in source
    assert "primary_activity_sha256" in source
    assert "hashlib.sha256" in source


def test_q38_profile_specific_worker_validator_is_absent() -> None:
    source = inspect.getsource(worker)
    assert "_validate_story_q38_input" not in source
    assert "STORY_Q38_PROFILE" not in source
    assert "qwen38_allow_unpinned_dev" not in source


def test_story_prompt_uses_only_the_selected_activity_content() -> None:
    data = _parent_input()
    prompt = worker._parent_story_prompt(data)
    assert "Observe a garden" in prompt
    assert "Observe with an adult" in prompt
    assert "primary_activity_sha256" not in prompt


def test_story_prompt_omits_selection_ids_and_unapproved_context() -> None:
    data = _parent_input(
        context_entries=[{"kind": "INTEREST", "text": "private-context-sentinel"}],
        activity_selection_sha256="selection-hash-sentinel",
        adult_rewrite_hint="rewrite-hint-sentinel",
    )
    prompt = worker._parent_story_prompt(data)
    assert "private-context-sentinel" not in prompt
    assert "selection-hash-sentinel" not in prompt
    assert "rewrite-hint-sentinel" not in prompt


def test_story_prompt_includes_only_the_adult_reviewed_rewrite_instruction() -> None:
    prompt = worker._parent_story_prompt(
        _parent_input(rewrite_instruction="Keep the ending gentle.")
    )
    assert "Keep the ending gentle." in prompt


def test_current_teacher_visual_workloads_remain_registered() -> None:
    ids = {item["id"] for item in _registry()["workloads"]}
    assert "presentation.svg-draft.generate" in ids
    assert "lesson.visual.generate" in ids


def test_teacher_visual_workloads_remain_disabled_until_review() -> None:
    # Owner decision 2026-11-27: the AI vector draft is on; it stays a teacher-reviewed draft.
    assert _entry("presentation.svg-draft.generate")["enabled"] is True
    assert _entry("lesson.visual.generate")["enabled"] is False


def test_flux_lesson_visual_contract_uses_a_reviewed_plan() -> None:
    source = (MODAL_DIR / "flux_image_app.py").read_text(encoding="utf-8")
    assert "reviewed_plan_sha256" in source
    assert "min_steps=3" in source or "MIN_STEPS = 3" in source
    assert "max_steps=5" in source or "MAX_STEPS = 5" in source


def test_video_and_storyboard_registry_entries_remain_present() -> None:
    ids = {item["id"] for item in _registry()["workloads"]}
    assert {"storyboard.generate", "video.timeline.generate", "video.scene.validate"} <= ids


def test_story_output_parser_is_the_dev_content_parser() -> None:
    assert callable(worker._parse_story_content_output)
    source = inspect.getsource(worker._parse_story_content_output)
    assert "StoryOutputValidationError" in source
    assert "story" in source


def test_story_model_revision_is_not_selected_from_settings() -> None:
    settings_source = (BACKEND_SRC / "sketch2life" / "infrastructure" / "config" / "settings.py").read_text(
        encoding="utf-8"
    )
    assert "story_generation_profile" not in settings_source
    assert "modal_qwen_profile" not in settings_source
