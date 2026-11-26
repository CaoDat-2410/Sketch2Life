"""One warm Qwen3.8 container: the client and the Modal app must agree on the shared worker."""

from __future__ import annotations

from pathlib import Path

from sketch2life.infrastructure.ai import modal_function_client as client

MODAL_APP = Path(__file__).resolve().parents[3] / "deployment/modal/srs_v23/language_audio_app.py"
ROUTED_WORKLOADS = (
    "drawing.analyze",
    "story.generate",
    "parent.activity.suggest",
    "parent.topic-subjects.suggest",
    "parent.topic-subjects.validate",
)


def test_drawing_and_json_workloads_call_the_shared_function() -> None:
    assert client.APP_NAME == "sketch2life-srs23-language-audio-dev"
    assert client.FUNCTION_NAME == "qwen-worker"
    for workload in ("parent.activity.suggest", "parent.topic-subjects.validate"):
        app_name, function_name, _timeout = client._JSON_WORKERS[workload]
        assert (app_name, function_name) == (client.APP_NAME, client.FUNCTION_NAME)


def test_modal_app_routes_every_workload_the_backend_sends_to_the_shared_worker() -> None:
    source = MODAL_APP.read_text(encoding="utf-8")
    assert 'name="qwen-worker"' in source
    assert "SHARED_QWEN_SCALEDOWN_SECONDS = 600" in source  # owner's request of 2026-11-26: ten warm minutes
    assert "scaledown_window=SHARED_QWEN_SCALEDOWN_SECONDS" in source
    for workload in ROUTED_WORKLOADS:
        assert f'"{workload}":' in source


def test_drawing_handler_reuses_the_text_model_instead_of_loading_a_second_copy() -> None:
    source = MODAL_APP.read_text(encoding="utf-8")
    assert "_drawing_worker._load_model = _shared_drawing_model" in source


def test_shared_worker_routes_use_the_public_local_api_not_get_raw_f() -> None:
    """FEAT-092: ``Function.get_raw_f`` does not exist; every route crashed with AttributeError."""
    source = MODAL_APP.read_text(encoding="utf-8")
    assert "get_raw_f" not in source.replace("``get_raw_f``", "")
    for handler in (
        "_drawing_worker.analyze_drawing.local",
        "generate_story_and_storyboard.local",
        "suggest_parent_activities.local",
        "suggest_parent_topic_subjects.local",
        "validate_parent_topic_subject.local",
    ):
        assert f": {handler}," in source
