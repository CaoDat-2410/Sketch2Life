from __future__ import annotations

import importlib.util
import inspect
import sys
from pathlib import Path

import pytest

MODAL_DIR = Path(__file__).resolve().parents[1]
if str(MODAL_DIR) not in sys.path:
    sys.path.insert(0, str(MODAL_DIR))


def _load_worker(module_name: str, filename: str):
    spec = importlib.util.spec_from_file_location(module_name, MODAL_DIR / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


language_worker = _load_worker("sketch2life_dev_language_pin_test", "language_audio_app.py")
drawing_worker = _load_worker("sketch2life_dev_drawing_pin_test", "drawing_vlm_app.py")

from contracts import L4_WORKLOADS, WorkerContractError, parse_worker_input


def _worker_input(workload: str = "story.generate", **extra: object) -> dict[str, object]:
    job_id = "job-dev-pin"
    generation_id = "generation-dev-pin"
    attempt_id = "attempt-dev-pin"
    return {
        "schema_version": "sketch2life.modal.worker-input.v1",
        "environment": "dev",
        "workload": workload,
        "job_id": job_id,
        "generation_id": generation_id,
        "attempt_id": attempt_id,
        "attempt_prefix": f"sketch2life/dev/{job_id}/{generation_id}/{attempt_id}/",
        "input_manifest_ref": "input/manifest.json",
        "input_manifest_sha256": "a" * 64,
        "input_bytes": 1,
        **extra,
    }


def test_worker_input_contract_has_no_unpinned_override_field() -> None:
    parsed = parse_worker_input(_worker_input(), execution_group="l4")
    assert parsed.workload == "story.generate"
    assert not hasattr(parsed, "qwen38_allow_unpinned_dev")


def test_worker_input_rejects_the_retired_unpinned_flag() -> None:
    with pytest.raises(WorkerContractError, match="MODAL_INPUT_INVALID"):
        parse_worker_input(
            _worker_input(qwen38_allow_unpinned_dev=True), execution_group="l4"
        )


def test_both_workers_use_the_pinned_dev_checkpoint() -> None:
    expected = ("Qwen/Qwen3.8-27B-FP8", "c3a462cc3d38cf351f3b26cbd763469eeb74ef81")
    assert (language_worker.TEXT_MODEL_ID, language_worker.TEXT_MODEL_REVISION) == expected
    assert (drawing_worker.MODEL_ID, drawing_worker.MODEL_REVISION) == expected


def test_checkpoint_directories_include_the_pinned_revision() -> None:
    assert language_worker.TEXT_MODEL_REVISION in language_worker.TEXT_MODEL_DIR
    assert drawing_worker.MODEL_REVISION in drawing_worker.MODEL_DIR


def test_both_workers_have_no_unpinned_kernel_loader_switch() -> None:
    for worker in (language_worker, drawing_worker):
        parameters = set(inspect.signature(worker._preload_qwen38_fp8_kernel).parameters)
        assert "allow_unpinned_dev" not in parameters
        assert not hasattr(worker, "_log_qwen38_unpinned_dev")


def test_story_worker_has_no_q38_manifest_override_api() -> None:
    assert not hasattr(language_worker, "STORY_Q38_CHECKPOINT_MANIFEST_SHA256")
    assert not hasattr(language_worker, "_verify_story_q38_checkpoint")
    assert not hasattr(language_worker, "_require_qwen38_text_pins")


def test_dev_story_workload_is_l4_and_old_dispatches_are_not() -> None:
    assert "story.generate" in L4_WORKLOADS
    assert "parent.topic-subjects.validate" in L4_WORKLOADS
    assert "parent.topic-subjects.suggest" not in L4_WORKLOADS
    assert "parent.sketch-guide.generate" not in L4_WORKLOADS


def test_shared_worker_routes_keep_dev_workloads_and_retire_old_suggest() -> None:
    routes = language_worker._shared_qwen_routes()
    assert "story.generate" in routes
    assert "parent.activity.suggest" in routes
    assert "parent.topic-subjects.validate" in routes
    assert "parent.topic-subjects.suggest" not in routes


def test_teacher_presentation_svg_uses_the_shared_dev_text_model() -> None:
    assert language_worker.TEXT_MODEL_ID == "Qwen/Qwen3.8-27B-FP8"
    source = inspect.getsource(language_worker)
    assert "presentation.svg-draft.generate" in source


def test_no_worker_source_has_an_unpinned_dev_override() -> None:
    for worker in (language_worker, drawing_worker):
        source = inspect.getsource(worker)
        assert "qwen38_allow_unpinned_dev" not in source
        assert "allow_unpinned_dev" not in source


def test_retired_profile_and_q38_workload_names_are_absent() -> None:
    source = inspect.getsource(language_worker)
    assert "story.generate.q38" not in source
    assert "STORY_Q38_PROFILE" not in source
    assert "STORY_V1_PROFILE" not in source
