from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

MODAL_DIR = Path(__file__).resolve().parents[1]
MODULE_SPEC = importlib.util.spec_from_file_location(
    "sketch2life_modal_language_audio_app_parent_topic_subjects",
    MODAL_DIR / "language_audio_app.py",
)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
worker = importlib.util.module_from_spec(MODULE_SPEC)
sys.modules[MODULE_SPEC.name] = worker
MODULE_SPEC.loader.exec_module(worker)


def _suggestion(
    title: str, guide_subject: str, relation_to_topic_vi: str
) -> dict[str, str]:
    return {
        "title_vi": title,
        "guide_subject": guide_subject,
        "relation_to_topic_vi": relation_to_topic_vi,
    }


def _valid_output() -> dict[str, Any]:
    return {
        "subjects": [
            _suggestion("Khủng long cổ dài", "khủng long cổ dài", "Một loài khủng long ăn thực vật."),
            _suggestion("Khủng long ba sừng", "khủng long ba sừng", "Một loài khủng long có ba sừng."),
            _suggestion("Khủng long bạo chúa", "khủng long bạo chúa", "Một loài khủng long nổi tiếng."),
        ]
    }


def test_parent_topic_suggestion_worker_input_contains_only_generic_topic() -> None:
    worker._validate_parent_topic_subject_input(
        {
            "schema_version": "sketch2life.parent-topic-subject-input.v1",
            "topic": "Khủng long",
            "excluded_subjects": [],
        }
    )

    with pytest.raises(worker.WorkerContractError):
        worker._validate_parent_topic_subject_input(
            {
                "schema_version": "sketch2life.parent-topic-subject-input.v1",
                "topic": "Bé nhà tôi thích khủng long",
                "excluded_subjects": [],
            }
        )


def test_parent_topic_suggestion_worker_requires_three_unique_safe_items() -> None:
    parsed = worker._parse_parent_topic_subjects(json.dumps(_valid_output(), ensure_ascii=False))
    assert len(parsed["subjects"]) == 3

    duplicate = _valid_output()
    duplicate["subjects"][2] = duplicate["subjects"][0]
    with pytest.raises(ValueError, match="PARENT_TOPIC_SUBJECT_DUPLICATE"):
        worker._parse_parent_topic_subjects(json.dumps(duplicate, ensure_ascii=False))

    with pytest.raises(ValueError, match="PARENT_TOPIC_SUBJECT_REPEAT_FROM_PREVIOUS_SET"):
        worker._parse_parent_topic_subjects(
            json.dumps(_valid_output(), ensure_ascii=False),
            excluded_subjects=("Khủng long cổ dài",),
        )


def test_parent_topic_suggestion_parser_rejects_duplicate_json_keys() -> None:
    duplicate_root = '{"subjects": [], "subjects": []}'
    duplicate_nested = (
        '{"subjects":[{"title_vi":"Cá voi", "title_vi":"Cá voi",'
        '"guide_subject":"cá voi", "relation_to_topic_vi":"động vật biển"},'
        '{"title_vi":"Mèo", "guide_subject":"mèo", "relation_to_topic_vi":"động vật nuôi"},'
        '{"title_vi":"Chim", "guide_subject":"chim", "relation_to_topic_vi":"động vật bay"}]}'
    )

    for raw in (duplicate_root, duplicate_nested):
        with pytest.raises(ValueError, match="PARENT_TOPIC_SUBJECT_JSON_INVALID"):
            worker._parse_parent_topic_subjects(raw)


def test_parent_topic_suggestion_worker_rejects_non_vietnamese_cjk_and_private_data() -> None:
    cjk_output = _valid_output()
    cjk_output["subjects"][0]["relation_to_topic_vi"] = "這是一種恐龍。"
    with pytest.raises(ValueError, match="PARENT_TOPIC_SUBJECT_LANGUAGE_INVALID"):
        worker._parse_parent_topic_subjects(json.dumps(cjk_output, ensure_ascii=False))

    private_output = _valid_output()
    private_output["subjects"][0]["guide_subject"] = "khủng long person@example.test"
    with pytest.raises(ValueError, match="PARENT_TOPIC_SUBJECT_SAFETY_INVALID"):
        worker._parse_parent_topic_subjects(json.dumps(private_output, ensure_ascii=False))


def test_parent_topic_suggestion_worker_json_schema_is_exactly_three_items() -> None:
    schema = worker._parent_topic_subjects_json_schema()
    assert schema["properties"]["subjects"]["minItems"] == 3
    assert schema["properties"]["subjects"]["maxItems"] == 3
    assert schema["additionalProperties"] is False


def test_parent_topic_subject_validation_worker_is_generic_and_fail_closed() -> None:
    worker._validate_parent_topic_subject_validation_input(
        {
            "schema_version": "sketch2life.parent-topic-subject-validation-input.v1",
            "topic": "Khủng long",
            "subject": "Khủng long cổ dài",
        }
    )
    with pytest.raises(worker.WorkerContractError):
        worker._validate_parent_topic_subject_validation_input(
            {
                "schema_version": "sketch2life.parent-topic-subject-validation-input.v1",
                "topic": "Khủng long",
                "subject": "con tôi thích khủng long",
            }
        )

    assert "parent.topic-subjects.validate" in worker.parse_worker_input(
        {
            "schema_version": "sketch2life.modal.worker-input.v1",
            "environment": "dev",
            "workload": "parent.topic-subjects.validate",
            "job_id": "job-topic-test-01",
            "generation_id": "generation-topic-01",
            "attempt_id": "attempt-topic-01",
            "attempt_prefix": "sketch2life/dev/job-topic-test-01/generation-topic-01/attempt-topic-01/",
            "input_manifest_ref": "input/manifest.json",
            "input_manifest_sha256": "a" * 64,
            "input_bytes": 256,
        },
        execution_group="l4",
    ).workload

    assert worker._parse_parent_topic_subject_validation('{"decision":"ON_TOPIC"}') == {
        "decision": "ON_TOPIC"
    }
    for output in (
        '{"decision":"UNKNOWN"}',
        '{"decision":[]}',
        '{"decision":"ON_TOPIC","normalized_subject":"Other"}',
        "not-json",
    ):
        with pytest.raises(ValueError):
            worker._parse_parent_topic_subject_validation(output)

    with pytest.raises(ValueError, match="PARENT_TOPIC_SUBJECT_VALIDATION_JSON_INVALID"):
        worker._parse_parent_topic_subject_validation(
            '{"decision":"ON_TOPIC", "decision":"OUT_OF_TOPIC"}'
        )
