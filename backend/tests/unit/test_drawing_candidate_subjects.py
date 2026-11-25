"""FEAT-093 M1: the stored drawing candidate keeps the worker's main and secondary subjects."""

from __future__ import annotations

from sketch2life.application.parent_subject_roles import present_candidate
from sketch2life.application.ports.parent_story_inputs import DrawingAnalysisResult
from sketch2life.infrastructure.story_inputs.runner import candidate_from_result

RAW = {
    "understanding_schema": "sketch2life.drawing-understanding.v2",
    "candidate_subject": "con gà con",
    "visible_features": ["lông vàng", "mào đỏ"],
    "confidence": 0.9,
    "main_subject": {
        "label": "con gà con",
        "visible_features": ["lông vàng", "mào đỏ"],
        "facing": "right",
        "box": [4, 3, 17, 18],
    },
    "secondary_subjects": [
        {"label": "mặt trời", "visible_features": ["tia cam"], "box": [0, 0, 5, 5]},
        {"label": "cỏ", "visible_features": [], "box": [0, 16, 20, 20]},
    ],
}


def _result(raw):
    return DrawingAnalysisResult(
        subject="con gà con",
        visible_features=("lông vàng", "mào đỏ"),
        confidence=0.9,
        raw_candidate=raw,
    )


def test_main_and_secondary_subjects_are_stored_with_stable_entity_ids() -> None:
    candidate, subject, confidence = candidate_from_result(_result(RAW))

    assert subject == "con gà con" and confidence == 0.9
    assert candidate["main_subject"]["entity_id"] == "main"
    assert candidate["main_subject"]["box"] == [4, 3, 17, 18]
    assert [item["entity_id"] for item in candidate["secondary_subjects"]] == ["sec-1", "sec-2"]
    assert candidate["decision"] == "REVIEW_REQUIRED"


def test_the_client_view_lists_entities_without_boxes() -> None:
    candidate, _subject, _confidence = candidate_from_result(_result(RAW))

    shown = present_candidate(candidate)

    assert [(item["entity_id"], item["suggested_role"]) for item in shown["entities"]] == [
        ("main", "main"),
        ("sec-1", "secondary"),
        ("sec-2", "secondary"),
    ]
    assert "main_subject" not in shown and "secondary_subjects" not in shown
    assert "box" not in repr(shown)


def test_an_analysis_without_subjects_keeps_the_legacy_single_subject_shape() -> None:
    candidate, _subject, _confidence = candidate_from_result(_result(None))

    assert "main_subject" not in candidate and "secondary_subjects" not in candidate
    assert present_candidate(candidate)["entities"] == []


def test_an_invalid_box_falls_back_to_the_single_subject_shape() -> None:
    raw = {**RAW, "main_subject": {**RAW["main_subject"], "box": [4, 3, 17]}}

    candidate, _subject, _confidence = candidate_from_result(_result(raw))

    assert "main_subject" not in candidate


def test_the_client_view_marks_scenery_unused_and_exposes_needs_choice() -> None:
    candidate, _subject, _confidence = candidate_from_result(_result(RAW))

    shown = present_candidate(candidate, intent_terms=["gà con ở nông trại"])

    by_id = {item["entity_id"]: item for item in shown["entities"]}
    assert by_id["main"]["suggested_role"] == "main" and by_id["main"]["suggested_included"] is True
    assert by_id["sec-1"]["suggested_included"] is False  # the sun
    assert by_id["sec-2"]["suggested_included"] is False  # the grass
    assert shown["needs_choice"] is False


def test_two_close_animals_set_needs_choice_in_the_client_view() -> None:
    raw = {
        **RAW,
        "main_subject": {**RAW["main_subject"], "label": "con mèo", "box": [1, 6, 10, 17]},
        "secondary_subjects": [
            {"label": "con chó", "visible_features": ["tai dài"], "box": [10, 6, 19, 17]}
        ],
    }
    candidate, _subject, _confidence = candidate_from_result(_result(raw))

    shown = present_candidate(candidate)

    assert shown["needs_choice"] is True
