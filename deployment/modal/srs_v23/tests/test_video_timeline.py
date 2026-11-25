"""FEAT-093: the video.timeline.generate workload (prompt, schema, structural parser, registry, age parity)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

MODAL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODAL_DIR))
import video_timeline as timeline  # noqa: E402

ROOT = Path(__file__).resolve().parents[4]


def _request(scene_count: int = 5) -> dict:
    return {
        "schema_version": timeline.REQUEST_SCHEMA,
        "age_band": {
            "band": "36-71", "scene_count": scene_count, "scene_seconds": 6, "narration_max_words": 9,
            "dialogue_max_lines": 1, "dialogue_max_words": 5, "secondary_max": 1,
        },
        "topic": "Động vật",
        "story": {"title": "Rùa con", "scenes": []},
        "subjects": [
            {"entity_id": "main", "label": "con rùa", "role": "main"},
            {"entity_id": "sec-1", "label": "chiếc lá", "role": "secondary"},
        ],
        "activity": {"title": "Tìm lá", "objective": "Quan sát lá"},
        "previous_error": None,
    }


def _scene() -> dict:
    return {
        "title": "Rùa đi", "action": "Rùa bò.", "visual_prompt": "A small turtle crawls on grass.",
        "background_prompt": "A sunny garden, crayon texture.", "narration": "Rùa con bò đi.",
        "dialogue": [], "subjects": ["main"], "interactions": [],
    }


def test_the_request_gate_accepts_the_contract_and_rejects_the_rest() -> None:
    timeline.validate_request(_request())
    bad = _request()
    bad["subjects"][1]["role"] = "main"
    with pytest.raises(timeline.TimelineRequestError):
        timeline.validate_request(bad)
    with pytest.raises(timeline.TimelineRequestError):
        timeline.validate_request({**_request(), "schema_version": "x"})
    too_many = _request(scene_count=20)
    with pytest.raises(timeline.TimelineRequestError):
        timeline.validate_request(too_many)


def test_the_schema_fixes_the_scene_count_and_closes_the_enums() -> None:
    schema = timeline.json_schema(_request(7))

    scenes = schema["properties"]["scenes"]
    assert scenes["minItems"] == scenes["maxItems"] == 7
    scene = scenes["items"]["properties"]
    assert scene["subjects"]["items"]["enum"] == ["main", "sec-1"]
    assert scene["dialogue"]["maxItems"] == 1
    assert scene["interactions"]["items"]["properties"]["kind"]["enum"] == list(timeline.INTERACTION_KINDS)
    assert schema["additionalProperties"] is False


def test_the_prompt_states_the_age_numbers_and_the_format_rules() -> None:
    prompt = timeline.system_prompt(_request())

    assert "đúng 5 cảnh" in prompt and "tối đa 9 từ" in prompt and "tối đa 1 lời thoại" in prompt
    assert "KHÔNG nhắc tên nhân vật" in prompt and "consume" in prompt
    assert "\n" not in prompt  # real newlines, not escaped ones
    assert "Chú thỏ và củ cà rốt" in prompt  # the format example


def test_the_user_prompt_carries_the_previous_error_code_only() -> None:
    data = _request()
    data["previous_error"] = "LINE_TEXT_DANGLING_WORD"

    text = timeline.user_prompt(data)

    assert "LINE_TEXT_DANGLING_WORD" in text and "con rùa" in text


def test_the_structural_parser_checks_counts_and_shapes() -> None:
    data = _request()
    good = json.dumps({"title": "Rùa con", "scenes": [_scene() for _ in range(5)]}, ensure_ascii=False)
    assert len(timeline.parse_output(good, data)["scenes"]) == 5

    for text, code in [
        ("not json", "TIMELINE_DRAFT_JSON_INVALID"),
        (json.dumps({"title": "x"}), "TIMELINE_DRAFT_SHAPE_INVALID"),
        (json.dumps({"title": "Rùa", "scenes": [_scene()]}), "TIMELINE_DRAFT_SCENE_COUNT"),
        (json.dumps({"title": "Rùa", "scenes": [{**_scene(), "x": 1} for _ in range(5)]}), "TIMELINE_DRAFT_SCENE_SHAPE"),
        ('{"title":"a","title":"b","scenes":[]}', "TIMELINE_DRAFT_DUPLICATE_KEY"),
    ]:
        with pytest.raises(timeline.TimelineOutputError) as error:
            timeline.parse_output(text, data)
        assert error.value.code == code


def test_the_token_budget_grows_with_the_scene_count() -> None:
    assert timeline.output_token_budget(5) == 1_650 and timeline.output_token_budget(9) == 2_570


def test_the_workload_is_registered_everywhere() -> None:
    registry = json.loads((MODAL_DIR / "workloads.json").read_text(encoding="utf-8"))
    entry = next(item for item in registry["workloads"] if item["id"] == "video.timeline.generate")
    assert entry["enabled"] is False and entry["execution_group"] == "l4"
    assert '"video.timeline.generate"' in (MODAL_DIR / "contracts.py").read_text(encoding="utf-8")
    app = (MODAL_DIR / "language_audio_app.py").read_text(encoding="utf-8")
    assert '"video.timeline.generate": generate_video_timeline.local' in app
    assert 'name="generate-video-timeline"' in app and "video_timeline.py" in app


def test_the_worker_age_keys_match_the_backend_table() -> None:
    spec = importlib.util.spec_from_file_location(
        "age_profile_backend", ROOT / "backend/src/sketch2life/application/video_pipeline/age_profile.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["age_profile_backend"] = module
    spec.loader.exec_module(module)
    for profile in module.AGE_BANDS:
        sent = {
            "band": profile.band, "scene_count": profile.scene_count, "scene_seconds": profile.scene_seconds,
            "narration_max_words": profile.narration_max_words, "dialogue_max_lines": profile.dialogue_max_lines,
            "dialogue_max_words": profile.dialogue_max_words, "secondary_max": profile.secondary_max,
        }
        assert set(sent) == set(timeline.AGE_BAND_KEYS)
        request = _request(profile.scene_count)
        request["age_band"] = sent
        timeline.validate_request(request)
