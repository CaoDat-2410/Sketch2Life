from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

MODAL_DIR = Path(__file__).resolve().parents[1]
if str(MODAL_DIR) not in sys.path:
    sys.path.insert(0, str(MODAL_DIR))

MODULE_SPEC = importlib.util.spec_from_file_location(
    "sketch2life_modal_language_audio_svg_illustration_contract",
    MODAL_DIR / "language_audio_app.py",
)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
worker = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(worker)


def _content() -> dict[str, Any]:
    return {
        "schema_version": "SvgIllustrationContentV1",
        "title_vi": "Con hươu",
        "alt_text_vi": "Hình minh họa con hươu màu nâu, có sừng và bốn chân.",
        "document": {
            "schema_version": "SvgDocumentV1",
            "view_box": "0 0 512 512",
            "paths": [
                {
                    "path_id": f"part-{index}",
                    "d": f"M {index} {index} L {index + 10} {index + 10} Z",
                    "fill": "#A06038",
                    "stroke": "#392719",
                    "stroke_width": 4,
                }
                for index in range(1, 5)
            ],
        },
    }


def test_teacher_svg_input_is_bounded_and_allowlisted() -> None:
    worker._validate_teacher_svg_illustration_input(
        {
            "schema_version": "sketch2life.teacher-svg-illustration-input.v1",
            "topic": "con hươu",
            "target_age_months": 60,
            "visual_style": "warm_storybook",
        }
    )
    with pytest.raises(worker.WorkerContractError):
        worker._validate_teacher_svg_illustration_input(
            {
                "schema_version": "sketch2life.teacher-svg-illustration-input.v1",
                "topic": "con hươu",
                "target_age_months": 121,
                "visual_style": "warm_storybook",
            }
        )


def test_svg_output_schema_has_bounded_independent_paths() -> None:
    schema = worker._teacher_svg_illustration_json_schema()
    document = schema["properties"]["document"]
    paths = document["properties"]["paths"]
    assert paths["minItems"] == 4
    assert paths["maxItems"] == 20
    assert document["properties"]["view_box"]["enum"] == ["0 0 512 512"]
    assert schema["additionalProperties"] is False


def test_worker_parses_only_structured_nonduplicate_svg_paths() -> None:
    result = worker._parse_teacher_svg_illustration(
        json.dumps(_content(), ensure_ascii=False)
    )
    assert result["document"]["schema_version"] == "SvgDocumentV1"
    assert len(result["document"]["paths"]) == 4

    duplicate_geometry = _content()
    duplicate_geometry["document"]["paths"][1]["d"] = duplicate_geometry["document"]["paths"][0]["d"]
    with pytest.raises(RuntimeError, match="MODAL_SVG_ILLUSTRATION_DUPLICATE_PATH"):
        worker._parse_teacher_svg_illustration(
            json.dumps(duplicate_geometry, ensure_ascii=False)
        )


def test_svg_workload_uses_pinned_qwen_and_remains_disabled() -> None:
    registry = json.loads((MODAL_DIR / "workloads.json").read_text(encoding="utf-8"))
    workload = next(
        item for item in registry["workloads"]
        if item["id"] == "teacher.svg-illustration.generate"
    )
    assert workload["enabled"] is False
    assert workload["candidate"].startswith("Qwen/Qwen3.5-9B@")
    assert workload["modal_function"] == "generate-teacher-svg-illustration-draft"
    assert workload["modal_function"] not in {
        item["function_name"]
        for app in registry["local_startup"]["apps"]
        for item in app["workers"]
    }
