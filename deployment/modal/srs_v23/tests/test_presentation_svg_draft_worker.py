from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

MODAL_DIR = Path(__file__).resolve().parents[1]
for import_path in (str(MODAL_DIR),):
    if import_path not in sys.path:
        sys.path.insert(0, import_path)

from contracts import L4_WORKLOADS, WorkerContractError

MODULE_SPEC = importlib.util.spec_from_file_location(
    "sketch2life_modal_presentation_svg_draft_worker",
    MODAL_DIR / "language_audio_app.py",
)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
worker = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(worker)


def _valid_draft() -> dict[str, Any]:
    return {
        "schema_version": "sketch2life.presentation-svg-draft.v1",
        "review_required": True,
        "viewbox": [0, 0, 100, 100],
        "shapes": [
            {
                "kind": "circle",
                "cx": 15,
                "cy": 15,
                "r": 8,
                "stroke": "#1f2937",
                "stroke_width": 2,
            },
            {
                "kind": "rect",
                "x": 35,
                "y": 10,
                "w": 20,
                "h": 15,
                "stroke": "#2563eb",
                "stroke_width": 3,
            },
            {
                "kind": "line",
                "x1": 5,
                "y1": 40,
                "x2": 20,
                "y2": 45,
                "stroke": "#16a34a",
                "stroke_width": 1,
            },
            {
                "kind": "polyline",
                "points": [[10, 70], [20, 60], [30, 70]],
                "stroke": "#dc2626",
                "stroke_width": 2,
            },
            {
                "kind": "ellipse",
                "cx": 70,
                "cy": 70,
                "rx": 12,
                "ry": 8,
                "stroke": "#d97706",
                "stroke_width": 4,
            },
        ],
    }


def _worker_input() -> dict[str, str]:
    payload = {
        "schema_version": "sketch2life.presentation-svg-input.v1",
        "activity_title": "Draw a butterfly",
        "subject_text": "butterfly",
    }
    digest = hashlib.sha256(
        json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()
    return {**payload, "content_hash": digest}


def test_draft_parser_accepts_bounded_structured_geometry() -> None:
    draft = _valid_draft()
    parsed = worker._parse_presentation_svg_draft(json.dumps(draft))

    assert parsed == draft
    assert "presentation.svg-draft.generate" in L4_WORKLOADS
    schema = worker._presentation_svg_draft_json_schema()
    shape_schema = schema["properties"]["shapes"]["items"]
    assert shape_schema["additionalProperties"] is False
    assert "fill" not in shape_schema["properties"]
    assert len(shape_schema["properties"]["kind"]["enum"]) == 5
    assert "review_required" not in schema["properties"]


def test_draft_parser_adds_the_server_review_flag_when_the_decoder_omits_it() -> None:
    draft = _valid_draft()
    del draft["review_required"]

    parsed = worker._parse_presentation_svg_draft(json.dumps(draft))

    assert parsed["review_required"] is True


def test_draft_parser_repairs_what_the_decoder_cannot_forbid() -> None:
    draft = _valid_draft()
    expected = json.loads(json.dumps(draft))
    draft["viewbox"] = [0, 0, 0, 100]
    draft["shapes"][0]["x1"] = 5  # geometry of another kind
    draft["shapes"] += [
        {"kind": "circle", "cx": 5, "cy": 5, "r": 40, "stroke": "#1f2937", "stroke_width": 2},
        {"kind": "rect", "x": 10, "y": 10, "stroke": "#1f2937", "stroke_width": 2},
    ]

    assert worker._parse_presentation_svg_draft(json.dumps(draft)) == expected
    assert "viewbox" not in worker._presentation_svg_draft_json_schema()["properties"]


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value["shapes"][0].update(kind="text"),
        lambda value: value["shapes"][0].update(cx=101),
        lambda value: value["shapes"][0].update(cy=float("nan")),
        lambda value: value["shapes"][0].update(r=float("inf")),
        lambda value: value["shapes"][0].update(stroke="#000000"),
        lambda value: value["shapes"][0].update(text="unsafe"),
        lambda value: value["shapes"][0].update(href="https://example.invalid"),
        lambda value: value["shapes"][0].update(style="fill:red"),
        lambda value: value["shapes"].extend(value["shapes"] * 2),
        lambda value: value.update(shapes=value["shapes"][:3]),
    ],
    ids=[
        "unknown-kind",
        "out-of-range",
        "nan",
        "infinity",
        "bad-palette",
        "text-injection",
        "href-injection",
        "style-injection",
        "too-many-shapes",
        "too-few-shapes",
    ],
)
def test_draft_parser_rejects_invalid_geometry(mutate: Any) -> None:
    value = _valid_draft()
    mutate(value)

    with pytest.raises(RuntimeError, match="PRESENTATION_SVG_DRAFT_INVALID"):
        worker._parse_presentation_svg_draft(json.dumps(value))


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value.update(schema_version="wrong"),
        lambda value: value.update(subject_text="x" * 81),
        lambda value: value.update(child_id="must-not-be-present"),
        lambda value: value.update(content_hash="0" * 64),
    ],
    ids=["schema", "subject-bound", "extra-child-data", "content-hash"],
)
def test_worker_input_validation_rejects_bad_or_extra_fields(mutate: Any) -> None:
    value = _worker_input()
    mutate(value)

    with pytest.raises(WorkerContractError):
        worker._validate_presentation_svg_input(value)


def test_worker_input_validation_accepts_only_the_canonical_minimal_request() -> None:
    value = _worker_input()

    worker._validate_presentation_svg_input(value)

    assert set(value) == {
        "schema_version",
        "activity_title",
        "subject_text",
        "content_hash",
    }
    prompt = worker._presentation_svg_prompt(value)
    assert "child_id" not in prompt
    assert value["subject_text"] in prompt


def test_presentation_svg_coordinates_are_checked_without_a_name_error() -> None:
    """The dev merge lost ``import math``; every real draft then failed after the GPU ran."""

    assert worker._presentation_svg_number(50) == 50.0
    with pytest.raises(ValueError):
        worker._presentation_svg_number(float("nan"))
    with pytest.raises(ValueError):
        worker._presentation_svg_number(101)


def test_svg_prompt_asks_for_paired_parts_on_both_sides() -> None:
    prompt = worker._presentation_svg_prompt({"activity_title": "Vẽ con mèo", "subject_text": "con mèo"})

    assert "whiskers" in prompt
    assert "drawn on both sides, mirrored around the vertical centre line x=50" in prompt
    assert "same number on each side" in prompt
