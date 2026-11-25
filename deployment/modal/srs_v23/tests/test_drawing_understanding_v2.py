"""FEAT-087 M1: drawing understanding v2 (main + secondary subjects with boxes).

Pure contract tests; no model, network or GPU.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

MODAL_DIR = Path(__file__).resolve().parents[1]
if str(MODAL_DIR) not in sys.path:
    sys.path.insert(0, str(MODAL_DIR))
SPEC = importlib.util.spec_from_file_location(
    "sketch2life_modal_drawing_understanding_v2", MODAL_DIR / "drawing_vlm_app.py"
)
assert SPEC is not None and SPEC.loader is not None
worker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(worker)


def _valid() -> dict:
    return {
        "main_subject": {
            "label": "con rùa",
            "visible_features": ["mai có ba ô tròn", "bốn chân ngắn"],
            "facing": "right",
            "box": [2, 6, 12, 16],
        },
        "secondary_subjects": [
            {
                "label": "chiếc lá",
                "visible_features": ["lá có gân giữa"],
                "box": [14, 9, 19, 15],
            }
        ],
        "confidence": 0.8,
    }


def _dump(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False)


def test_schema_constant_and_result_shape() -> None:
    assert worker.UNDERSTANDING_SCHEMA_V2 == "sketch2life.drawing-understanding.v2"
    parsed = worker._parse_candidate(_dump(_valid()))
    assert parsed["understanding_schema"] == worker.UNDERSTANDING_SCHEMA_V2
    assert parsed["main_subject"] == {
        "label": "con rùa",
        "visible_features": ["mai có ba ô tròn", "bốn chân ngắn"],
        "facing": "right",
        "box": [2, 6, 12, 16],
    }
    assert parsed["secondary_subjects"] == [
        {"label": "chiếc lá", "visible_features": ["lá có gân giữa"], "box": [14, 9, 19, 15]}
    ]
    assert parsed["confidence"] == 0.8


def test_legacy_keys_are_derived_from_the_main_subject() -> None:
    parsed = worker._parse_candidate(_dump(_valid()))
    assert parsed["candidate_subject"] == "con rùa"
    assert parsed["visible_features"] == ["mai có ba ô tròn", "bốn chân ngắn"]


def test_single_object_drawing_has_no_secondaries() -> None:
    payload = _valid()
    payload["secondary_subjects"] = []
    assert worker._parse_candidate(_dump(payload))["secondary_subjects"] == []


def test_output_json_schema_is_closed_enum_grid() -> None:
    schema = worker._drawing_output_json_schema()
    assert set(schema["required"]) == {"main_subject", "secondary_subjects", "confidence"}
    assert schema["additionalProperties"] is False
    secondaries = schema["properties"]["secondary_subjects"]
    assert secondaries["minItems"] == 0 and secondaries["maxItems"] == 3
    main = schema["properties"]["main_subject"]
    assert main["properties"]["facing"]["enum"] == ["left", "right", "front"]
    for box in (main["properties"]["box"], secondaries["items"]["properties"]["box"]):
        assert box["type"] == "object"
        assert box["required"] == ["left", "top", "right", "bottom"]
        assert box["additionalProperties"] is False
        assert all(box["properties"][k]["enum"] == list(range(21)) for k in box["required"])
    assert secondaries["items"]["properties"]["visible_features"]["maxItems"] == 2
    assert "facing" not in secondaries["items"]["properties"]


@pytest.mark.parametrize(
    "mutate, code",
    [
        (lambda p: p["main_subject"].__setitem__("box", [12, 6, 2, 16]), "BOX_ORDER_INVALID"),
        (lambda p: p["main_subject"].__setitem__("box", [2, 16, 12, 6]), "BOX_ORDER_INVALID"),
        (lambda p: p["main_subject"].__setitem__("box", [2, 2, 3, 3]), "BOX_AREA_TOO_SMALL"),
        (lambda p: p["main_subject"].__setitem__("box", [2, 6, 21, 16]), "BOX_RANGE_INVALID"),
        (lambda p: p["main_subject"].__setitem__("box", [2, 6, 12]), "BOX_SHAPE_INVALID"),
        (lambda p: p["main_subject"].__setitem__("box", [2, 6, 12.5, 16]), "BOX_TYPE_INVALID"),
        (lambda p: p["main_subject"].__setitem__("facing", "up"), "FACING_INVALID"),
        (lambda p: p["secondary_subjects"][0].__setitem__("label", "Con  Rùa"), "LABEL_DUPLICATE"),
        (
            lambda p: p["secondary_subjects"][0].__setitem__("visible_features", ["a", "b", "c"]),
            "FEATURES_COUNT_INVALID",
        ),
        (lambda p: p["main_subject"].__setitem__("visible_features", []), "FEATURES_COUNT_INVALID"),
        (lambda p: p.__setitem__("secondary_subjects", [p["secondary_subjects"][0]] * 4), "SECONDARY_COUNT_INVALID"),
        (lambda p: p.pop("secondary_subjects"), "MISSING_KEYS"),
        (lambda p: p.__setitem__("extra", 1), "UNEXPECTED_KEYS"),
        (lambda p: p.__setitem__("confidence", 1.5), "CONFIDENCE_OUT_OF_RANGE"),
    ],
)
def test_contract_violations_have_content_free_codes(mutate, code) -> None:
    payload = _valid()
    mutate(payload)
    assert worker._drawing_contract_violation(payload) == code
    with pytest.raises(RuntimeError, match="MODAL_MODEL_OUTPUT_INVALID"):
        worker._parse_candidate(_dump(payload))


def test_secondary_labels_must_be_unique_after_normalisation() -> None:
    payload = _valid()
    leaf = payload["secondary_subjects"][0]
    payload["secondary_subjects"] = [leaf, {**leaf, "label": "CHIẾC  LÁ"}]
    assert worker._drawing_contract_violation(payload) == "LABEL_DUPLICATE"


def test_valid_payload_has_no_violation() -> None:
    assert worker._drawing_contract_violation(_valid()) == "NONE"


def test_legacy_v1_payload_is_not_accepted_from_the_worker() -> None:
    legacy = {"candidate_subject": "bướm", "visible_features": ["hai cánh"], "confidence": 0.9}
    with pytest.raises(RuntimeError, match="MODAL_MODEL_OUTPUT_INVALID"):
        worker._parse_candidate(_dump(legacy))
    assert worker._drawing_contract_violation(legacy) == "UNEXPECTED_KEYS"


def test_diagnostics_report_violation_code_without_content() -> None:
    payload = _valid()
    payload["main_subject"]["box"] = [12, 6, 2, 16]
    text = _dump(payload)
    diagnostics = worker._drawing_json_diagnostics(text)
    assert diagnostics["contract_violation"] == "BOX_ORDER_INVALID"
    assert "con rùa" not in repr(diagnostics)


def test_prompt_defines_roles_and_forbids_background_and_invention() -> None:
    prompt = worker._drawing_prompt()
    for needle in ("main_subject", "secondary_subjects", "box", "0 đến 20", "facing"):
        assert needle in prompt
    assert "nền" in prompt and "không bịa" in prompt.lower()
    for key in ("left (trái)", "top (trên)", "right (phải)", "bottom (dưới)"):
        assert key in prompt
    assert "không được bỏ khóa nào" in prompt
    assert "trái < phải" in prompt and "trên < dưới" in prompt
    assert "tự kiểm tra trước khi trả json" in prompt.lower()
    assert "(phải - trái) nhân (dưới - trên)" in prompt
    assert "ít nhất 4 ô lưới" in prompt
    assert "candidate_subject" not in prompt


def test_box_to_pixels_maps_grid_to_image() -> None:
    assert worker.box_grid_to_pixels([0, 0, 20, 20], width=1000, height=600) == (0, 0, 1000, 600)
    assert worker.box_grid_to_pixels([10, 5, 20, 15], width=1000, height=600) == (500, 150, 1000, 450)


def test_prompt_requires_vietnamese_labels_and_features() -> None:
    """The adult-facing subject name must come back in Vietnamese, not English."""

    prompt = worker._drawing_prompt()
    assert "tiếng Việt" in prompt
    assert "label" in prompt and "visible_features" in prompt


def test_named_box_objects_normalize_to_the_four_number_list() -> None:
    parsed = {
        "main_subject": {"label": "gà", "visible_features": ["mào đỏ"], "facing": "right",
                         "box": {"left": 4, "top": 3, "right": 17, "bottom": 18}},
        "secondary_subjects": [
            {"label": "mặt trời", "visible_features": [], "box": {"left": 0, "top": 0, "right": 5, "bottom": 5}}
        ],
        "confidence": 0.9,
    }
    candidate = worker._parse_candidate(json.dumps(parsed))
    assert candidate["main_subject"]["box"] == [4, 3, 17, 18]
    assert candidate["secondary_subjects"][0]["box"] == [0, 0, 5, 5]


def test_box_object_missing_an_edge_is_still_a_contract_violation() -> None:
    bad = {
        "main_subject": {"label": "gà", "visible_features": ["mào đỏ"], "facing": "right",
                         "box": {"left": 4, "top": 3, "right": 17}},
        "secondary_subjects": [],
        "confidence": 0.9,
    }
    with pytest.raises(RuntimeError, match="MODAL_MODEL_OUTPUT_INVALID"):
        worker._parse_candidate(json.dumps(bad))
