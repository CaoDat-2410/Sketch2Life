"""FEAT-087 M2: subject role normalisation, validation and approved-role projection."""

from __future__ import annotations

import pytest

from sketch2life.application.parent_subject_roles import (
    SubjectRoleError,
    apply_subject_roles,
    approved_subjects,
    normalize_worker_candidate,
    present_candidate,
)


def _worker_result() -> dict:
    return {
        "understanding_schema": "sketch2life.drawing-understanding.v2",
        "main_subject": {
            "label": "con rùa",
            "visible_features": ["mai ba ô tròn"],
            "facing": "right",
            "box": [2, 6, 12, 16],
        },
        "secondary_subjects": [
            {"label": "chiếc lá", "visible_features": ["gân giữa"], "box": [14, 9, 19, 15]},
            {"label": "bông hoa", "visible_features": [], "box": [1, 1, 5, 5]},
        ],
        "confidence": 0.8,
        "candidate_subject": "con rùa",
        "visible_features": ["mai ba ô tròn"],
        "decision": "NEEDS_ADULT_CONFIRMATION",
        "adult_confirmation_required": True,
    }


def _candidate() -> dict:
    return normalize_worker_candidate(_worker_result())


def _roles(**roles: str) -> list[dict]:
    labels = {"main": "con rùa", "sec-1": "chiếc lá", "sec-2": "bông hoa"}
    return [
        {"entity_id": key, "label": labels[key], "role": roles.get(key.replace("-", "_"), default)}
        for key, default in (("main", "main"), ("sec-1", "secondary"), ("sec-2", "excluded"))
    ]


def test_normalize_assigns_stable_entity_ids_and_review_decision() -> None:
    candidate = _candidate()
    assert candidate["decision"] == "REVIEW_REQUIRED"
    assert candidate["adult_confirmation_required"] is True
    assert candidate["main_subject"]["entity_id"] == "main"
    assert [s["entity_id"] for s in candidate["secondary_subjects"]] == ["sec-1", "sec-2"]
    assert candidate["candidate_subject"] == "con rùa"
    assert candidate["visible_features"] == ["mai ba ô tròn"]


def test_normalize_accepts_a_v1_worker_result_without_entities() -> None:
    candidate = normalize_worker_candidate(
        {
            "candidate_subject": "con rùa",
            "visible_features": ["mai"],
            "confidence": 0.7,
            "decision": "NEEDS_ADULT_CONFIRMATION",
            "adult_confirmation_required": True,
        }
    )
    assert "main_subject" not in candidate
    assert candidate["candidate_subject"] == "con rùa"


def test_apply_roles_records_approved_roles_and_relabels() -> None:
    roles = _roles()
    roles[1]["label"] = "lá xanh"
    updated = apply_subject_roles(_candidate(), roles)
    assert updated["approved_roles"] == [
        {"entity_id": "main", "label": "con rùa", "role": "main"},
        {"entity_id": "sec-1", "label": "lá xanh", "role": "secondary"},
        {"entity_id": "sec-2", "label": "bông hoa", "role": "excluded"},
    ]
    assert updated["decision"] == "CORRECTED_BY_ADULT"


def test_promoting_a_secondary_swaps_the_main_subject() -> None:
    roles = [
        {"entity_id": "main", "label": "con rùa", "role": "secondary"},
        {"entity_id": "sec-1", "label": "chiếc lá", "role": "main"},
        {"entity_id": "sec-2", "label": "bông hoa", "role": "excluded"},
    ]
    updated = apply_subject_roles(_candidate(), roles)
    assert updated["candidate_subject"] == "chiếc lá"
    assert updated["main_subject"]["entity_id"] == "sec-1"
    assert updated["main_subject"]["facing"] == "front"
    assert updated["main_subject"]["box"] == [14, 9, 19, 15]
    assert updated["visible_features"] == ["gân giữa"]


@pytest.mark.parametrize(
    "roles",
    [
        [],  # no main
        [  # two mains
            {"entity_id": "main", "label": "con rùa", "role": "main"},
            {"entity_id": "sec-1", "label": "chiếc lá", "role": "main"},
            {"entity_id": "sec-2", "label": "bông hoa", "role": "excluded"},
        ],
        [  # unknown entity
            {"entity_id": "main", "label": "con rùa", "role": "main"},
            {"entity_id": "sec-3", "label": "x", "role": "secondary"},
            {"entity_id": "sec-1", "label": "chiếc lá", "role": "excluded"},
            {"entity_id": "sec-2", "label": "bông hoa", "role": "excluded"},
        ],
        [  # missing an entity
            {"entity_id": "main", "label": "con rùa", "role": "main"},
            {"entity_id": "sec-1", "label": "chiếc lá", "role": "secondary"},
        ],
        [  # duplicate entity
            {"entity_id": "main", "label": "con rùa", "role": "main"},
            {"entity_id": "main", "label": "con rùa", "role": "secondary"},
            {"entity_id": "sec-1", "label": "chiếc lá", "role": "secondary"},
            {"entity_id": "sec-2", "label": "bông hoa", "role": "excluded"},
        ],
        [  # empty label
            {"entity_id": "main", "label": "  ", "role": "main"},
            {"entity_id": "sec-1", "label": "chiếc lá", "role": "secondary"},
            {"entity_id": "sec-2", "label": "bông hoa", "role": "excluded"},
        ],
        [  # label too long
            {"entity_id": "main", "label": "a" * 101, "role": "main"},
            {"entity_id": "sec-1", "label": "chiếc lá", "role": "secondary"},
            {"entity_id": "sec-2", "label": "bông hoa", "role": "excluded"},
        ],
        [  # bad role
            {"entity_id": "main", "label": "con rùa", "role": "boss"},
            {"entity_id": "sec-1", "label": "chiếc lá", "role": "secondary"},
            {"entity_id": "sec-2", "label": "bông hoa", "role": "excluded"},
        ],
        [  # duplicate labels among used entities
            {"entity_id": "main", "label": "Con  Rùa", "role": "main"},
            {"entity_id": "sec-1", "label": "con rùa", "role": "secondary"},
            {"entity_id": "sec-2", "label": "bông hoa", "role": "excluded"},
        ],
    ],
)
def test_invalid_roles_are_rejected_with_a_content_free_code(roles) -> None:
    with pytest.raises(SubjectRoleError) as refused:
        apply_subject_roles(_candidate(), roles)
    assert refused.value.code == "PARENT_SUBJECT_ROLES_INVALID"


def test_roles_cannot_be_applied_to_a_v1_candidate() -> None:
    legacy = normalize_worker_candidate(
        {
            "candidate_subject": "con rùa",
            "visible_features": ["mai"],
            "confidence": 0.7,
            "decision": "NEEDS_ADULT_CONFIRMATION",
            "adult_confirmation_required": True,
        }
    )
    with pytest.raises(SubjectRoleError):
        apply_subject_roles(legacy, _roles())


def test_approved_subjects_defaults_every_secondary_to_excluded() -> None:
    main, secondaries = approved_subjects(_candidate())
    assert main["entity_id"] == "main"
    assert secondaries == []  # nothing was approved by an adult


def test_approved_subjects_returns_only_secondary_role_entities() -> None:
    updated = apply_subject_roles(_candidate(), _roles())
    main, secondaries = approved_subjects(updated)
    assert main["label"] == "con rùa"
    assert [(s["entity_id"], s["label"], s["box"]) for s in secondaries] == [
        ("sec-1", "chiếc lá", [14, 9, 19, 15])
    ]


def test_approved_subjects_of_a_v1_candidate_is_main_only() -> None:
    legacy = {"candidate_subject": "con rùa", "visible_features": ["mai"]}
    main, secondaries = approved_subjects(legacy)
    assert main == {"entity_id": "main", "label": "con rùa", "visible_features": ["mai"]}
    assert secondaries == []


def test_present_candidate_strips_boxes_and_exposes_entities_and_roles() -> None:
    shown = present_candidate(_candidate())
    assert "main_subject" not in shown and "secondary_subjects" not in shown
    assert shown["entities"] == [
        {"entity_id": "main", "label": "con rùa", "suggested_role": "main", "suggested_included": True},
        {"entity_id": "sec-1", "label": "chiếc lá", "suggested_role": "secondary", "suggested_included": True},
        {"entity_id": "sec-2", "label": "bông hoa", "suggested_role": "secondary", "suggested_included": True},
    ]
    assert shown["needs_choice"] is False
    assert shown["subject_roles"] is None
    approved = present_candidate(apply_subject_roles(_candidate(), _roles()))
    assert approved["subject_roles"][2]["role"] == "excluded"
    assert "box" not in repr(approved)


def test_present_candidate_of_a_v1_candidate_has_no_entities() -> None:
    shown = present_candidate({"candidate_subject": "con rùa", "visible_features": ["mai"]})
    assert shown["entities"] == [] and shown["subject_roles"] is None


def test_malformed_v2_data_from_the_worker_is_dropped_not_trusted() -> None:
    raw = _worker_result()
    raw["main_subject"]["box"] = [9, 9, 3, 3]
    candidate = normalize_worker_candidate(raw)
    assert "main_subject" not in candidate and "secondary_subjects" not in candidate
    raw = _worker_result()
    raw["secondary_subjects"] = raw["secondary_subjects"] * 2  # four secondaries
    assert "main_subject" not in normalize_worker_candidate(raw)


def test_relabel_keeps_v2_main_subject_coherent() -> None:
    from sketch2life.application.parent_subject_roles import relabel_main_subject

    updated = relabel_main_subject(_candidate(), "rùa nhỏ")
    assert updated["candidate_subject"] == "rùa nhỏ"
    assert updated["main_subject"]["label"] == "rùa nhỏ"
    assert updated["decision"] == "CORRECTED_BY_ADULT"
    assert _candidate()["main_subject"]["label"] == "con rùa"  # input is not mutated
