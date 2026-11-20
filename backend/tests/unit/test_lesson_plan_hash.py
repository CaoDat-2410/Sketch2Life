"""FEAT-066 T-3d: plan content hash, request rules, fingerprints, cursor, ETag (no database).

SRS l.1660 ("expected plan hash"), l.1699 (hashes and stale fences), l.547-548 (activities and the
safety checklist). Technical limits equal the Lesson Library limits (T-3d-DEC-2).
"""

from __future__ import annotations

import hashlib
import inspect
import json
from typing import Any

import pytest

from sketch2life.contracts.schemas.lesson_occurrences import (
    CreatePlanRevisionRequestV1,
    LessonPlanRevisionV1,
)
from sketch2life.domain.lesson_library.model import canonical_content_hash
from sketch2life.domain.lesson_occurrences import plan as rules
from sketch2life.domain.lesson_occurrences.model import LessonOccurrenceRuleError
from sketch2life.domain.lesson_occurrences.plan import (
    ActivityInput,
    activity_hash_entry,
    canonical_hash,
    plan_content_hash,
    plan_request_problems,
)
from sketch2life.domain.lesson_occurrences.safety_checklist import ChecklistAnswer, ChecklistEntry

OCC = "11111111-1111-4111-8111-111111111111"
LESSON_REF = {
    "lesson_id": "les-1",
    "version_id": "ver-1",
    "version_no": 3,
    "content_hash": "c" * 64,
}


def custom(order: int = 1, title: str = "Vẽ bằng ngón tay", text: str = "Cho trẻ vẽ") -> Any:
    return activity_hash_entry(
        order=order,
        kind="CUSTOM",
        catalog_activity_ref=None,
        activity_version=None,
        title=title,
        description=text,
        snapshot_hash=None,
    )


def hash_of(**overrides: Any) -> str:
    values: dict[str, Any] = {
        "occurrence_id": OCC,
        "document": {"document_revision_id": "rev-1", "text_hash": "a" * 64},
        "objectives": ["Nhận biết hình tròn"],
        "teacher_direction": "Câu chuyện về chú mèo",
        "safety_notes": None,
        "lesson_ref": LESSON_REF,
        "activities": [custom()],
    }
    values.update(overrides)
    return plan_content_hash(**values)


# ----------------------------------------------------------------------------- the hash
def test_the_algorithm_is_the_library_content_hash() -> None:
    sample = {"b": [1, "đ"], "a": {"z": 1, "y": None}}
    assert canonical_hash(sample) == canonical_content_hash(sample)
    expected = hashlib.sha256(
        json.dumps(sample, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    assert canonical_hash(sample) == expected


def test_a_fixed_vector_pins_the_hash() -> None:
    # Any change of the hashed fields or of the encoding changes this value on purpose.
    assert hash_of() == hash_of()
    assert len(hash_of()) == 64 and hash_of() == hash_of().lower()
    assert hash_of(document=None, lesson_ref=None, activities=[]) == canonical_hash(
        {
            "occurrence_id": OCC,
            "document": None,
            "objectives": ["Nhận biết hình tròn"],
            "teacher_direction": "Câu chuyện về chú mèo",
            "safety_notes": None,
            "lesson_ref": None,
            "activities": [],
        }
    )


def test_key_order_of_the_inputs_does_not_change_the_hash() -> None:
    first = hash_of(document={"document_revision_id": "rev-1", "text_hash": "a" * 64})
    second = hash_of(document={"text_hash": "a" * 64, "document_revision_id": "rev-1"})
    assert first == second
    reversed_ref = dict(reversed(list(LESSON_REF.items())))
    assert hash_of(lesson_ref=reversed_ref) == hash_of()


@pytest.mark.parametrize(
    "change",
    [
        {"objectives": ["Nhận biết hình vuông"]},
        {"objectives": ["Nhận biết hình tròn", "Tô màu"]},
        {"teacher_direction": "Câu chuyện khác"},
        {"safety_notes": "Rửa tay"},
        {"document": None},
        {"document": {"document_revision_id": "rev-2", "text_hash": "a" * 64}},
        {"document": {"document_revision_id": "rev-1", "text_hash": "b" * 64}},
        {"lesson_ref": None},
        {"lesson_ref": {**LESSON_REF, "version_no": 4}},
        {"activities": []},
        {"activities": [custom(), custom(2)]},
        {"activities": [custom(title="Vẽ bằng bút")]},
        {"occurrence_id": "22222222-2222-4222-8222-222222222222"},
    ],
)
def test_every_approved_field_changes_the_hash(change: dict[str, Any]) -> None:
    assert hash_of(**change) != hash_of()


def test_adding_or_removing_a_custom_activity_changes_the_hash() -> None:
    assert (
        hash_of(activities=[])
        != hash_of(activities=[custom()])
        != hash_of(activities=[custom(), custom(2)])
    )


def test_unicode_is_hashed_as_utf8_text_not_as_escapes() -> None:
    vietnamese = hash_of(objectives=["Nhận biết hình tròn đỏ"])
    ascii_only = hash_of(objectives=["Nhan biet hinh tron do"])
    assert vietnamese != ascii_only
    # NFC and NFD forms are different texts and stay different (no normalisation)
    assert hash_of(objectives=["é"]) != hash_of(objectives=["é"])


def test_the_activity_order_is_part_of_the_content() -> None:
    first, second = custom(1, "A", "a"), custom(2, "B", "b")
    assert hash_of(activities=[first, second]) != hash_of(
        activities=[custom(1, "B", "b"), custom(2, "A", "a")]
    )


def test_revision_ids_numbers_timestamps_state_and_checklist_are_not_hash_inputs() -> None:
    parameters = set(inspect.signature(plan_content_hash).parameters)
    assert parameters == {
        "occurrence_id",
        "document",
        "objectives",
        "teacher_direction",
        "safety_notes",
        "lesson_ref",
        "activities",
    }
    entry = custom()
    assert set(entry) == {
        "order",
        "kind",
        "catalog_activity_ref",
        "activity_version",
        "title",
        "description",
        "snapshot_hash",
    }


# ----------------------------------------------------------------------------- request rules
def problems(**overrides: Any) -> list[dict[str, str]]:
    values: dict[str, Any] = {
        "objectives": ["Mục tiêu"],
        "teacher_direction": "Hướng truyện",
        "safety_notes": None,
        "activities": [],
        "custom_allowed": True,
    }
    values.update(overrides)
    return plan_request_problems(**values)


def test_a_clean_request_has_no_problem() -> None:
    assert problems() == []
    assert problems(safety_notes="Ghi chú an toàn") == []
    assert problems(activities=[ActivityInput("LESSON", lesson_activity_id="act-1")]) == []
    assert (
        problems(activities=[ActivityInput("CUSTOM", title="Tên", description="Mô tả\nnhiều dòng")])
        == []
    )


@pytest.mark.parametrize("bad", ["a\x00b", "lone\ud800surrogate", "x\udfffy"])
def test_nul_and_lone_surrogates_are_refused_in_every_text_field(bad: str) -> None:
    assert problems(objectives=["ok", bad]) == [
        {"field": "objectives[1]", "code": "INVALID_FORMAT"}
    ]
    assert problems(teacher_direction=bad) == [
        {"field": "teacher_direction", "code": "INVALID_FORMAT"}
    ]
    assert problems(safety_notes=bad) == [{"field": "safety_notes", "code": "INVALID_FORMAT"}]
    found = problems(activities=[ActivityInput("CUSTOM", title=bad, description=bad)])
    assert {"field": "activities[0].title", "code": "INVALID_FORMAT"} in found
    assert {"field": "activities[0].description", "code": "INVALID_FORMAT"} in found
    assert bad not in json.dumps(found, ensure_ascii=True)


def test_blank_required_text_is_empty_but_blank_notes_are_allowed() -> None:
    assert problems(objectives=["   "]) == [{"field": "objectives[0]", "code": "EMPTY"}]
    assert problems(teacher_direction="\n\t ") == [{"field": "teacher_direction", "code": "EMPTY"}]
    assert problems(safety_notes="   ") == []
    assert rules.normalize_safety_notes("   ") is None
    assert rules.normalize_safety_notes(None) is None
    assert rules.normalize_safety_notes("  giữ nguyên  ") == "  giữ nguyên  "


def test_a_custom_title_takes_no_control_character_but_a_description_may_have_newlines() -> None:
    found = problems(activities=[ActivityInput("CUSTOM", title="a\nb", description="x\ny")])
    assert found == [{"field": "activities[0].title", "code": "INVALID_FORMAT"}]


def test_lesson_and_custom_activities_have_their_own_fields() -> None:
    assert problems(activities=[ActivityInput("LESSON")]) == [
        {"field": "activities[0].lesson_activity_id", "code": "REQUIRED"}
    ]
    found = problems(
        activities=[ActivityInput("LESSON", lesson_activity_id="a", title="t", description="d")]
    )
    assert {"field": "activities[0].title", "code": "UNKNOWN_FIELD"} in found
    assert {"field": "activities[0].description", "code": "UNKNOWN_FIELD"} in found
    found = problems(activities=[ActivityInput("CUSTOM", lesson_activity_id="a")])
    assert {"field": "activities[0].lesson_activity_id", "code": "UNKNOWN_FIELD"} in found
    assert {"field": "activities[0].title", "code": "REQUIRED"} in found
    assert {"field": "activities[0].description", "code": "REQUIRED"} in found


def test_custom_is_refused_while_no_checklist_exists_and_catalog_always() -> None:
    refused = problems(
        activities=[
            ActivityInput("LESSON", lesson_activity_id="a"),
            ActivityInput("CUSTOM", title="t", description="d"),
            ActivityInput("CATALOG"),
        ],
        custom_allowed=False,
    )
    assert refused == [
        {"field": "activities[1].kind", "code": "NOT_SUPPORTED"},
        {"field": "activities[2].kind", "code": "NOT_SUPPORTED"},
    ]
    assert problems(activities=[ActivityInput("CATALOG")]) == [
        {"field": "activities[0].kind", "code": "NOT_SUPPORTED"}
    ]


# ----------------------------------------------------------------------------- the schema limits
def request(**overrides: Any) -> dict[str, Any]:
    values: dict[str, Any] = {
        "expected_head_revision_no": 0,
        "objectives": ["Mục tiêu"],
        "teacher_direction": "Hướng truyện",
    }
    values.update(overrides)
    return values


def test_the_schema_limits_are_the_library_limits() -> None:
    assert rules.OBJECTIVES_MAX == 12 and rules.OBJECTIVE_MAX_CHARS == 1000
    assert rules.ACTIVITIES_MAX == 24 and rules.CUSTOM_TITLE_MAX_CHARS == 160
    assert rules.DIRECTION_MAX_CHARS == 2000 and rules.SAFETY_NOTES_MAX_CHARS == 2000
    ok = CreatePlanRevisionRequestV1.model_validate(
        request(
            objectives=["x" * 1000] * 12,
            teacher_direction="d" * 2000,
            safety_notes="n" * 2000,
            activities=[{"kind": "LESSON", "lesson_activity_id": "a"}] * 24,
        )
    )
    assert len(ok.activities) == 24
    for bad in (
        request(objectives=[]),
        request(objectives=["x"] * 13),
        request(objectives=["x" * 1001]),
        request(teacher_direction=""),
        request(teacher_direction="d" * 2001),
        request(safety_notes="n" * 2001),
        request(activities=[{"kind": "LESSON", "lesson_activity_id": "a"}] * 25),
        request(activities=[{"kind": "CUSTOM", "title": "t" * 161, "description": "d"}]),
        request(activities=[{"kind": "CUSTOM", "title": "t", "description": "d" * 4001}]),
        request(expected_head_revision_no=-1),
        request(lesson_version_ref={"lesson_id": "x"}),  # no pin field: the plan copies the pin
        request(state="APPROVED"),
        request(content_hash="a" * 64),
    ):
        with pytest.raises(ValueError):
            CreatePlanRevisionRequestV1.model_validate(bad)


def test_free_text_is_not_stripped_by_the_schema() -> None:
    parsed = CreatePlanRevisionRequestV1.model_validate(
        request(teacher_direction="  hướng  ", objectives=["  mục tiêu  "])
    )
    assert parsed.teacher_direction == "  hướng  " and parsed.objectives == ["  mục tiêu  "]


def test_the_published_schema_states_the_limits() -> None:
    schema = CreatePlanRevisionRequestV1.model_json_schema()["properties"]
    assert schema["objectives"]["maxItems"] == 12 and schema["objectives"]["minItems"] == 1
    assert schema["objectives"]["items"]["maxLength"] == 1000
    assert schema["activities"]["maxItems"] == 24
    assert schema["teacher_direction"]["maxLength"] == 2000
    assert "lesson_version_ref" not in schema and "latest" not in json.dumps(schema)
    assert LessonPlanRevisionV1.model_fields["supersedes_revision_no"].default is None


# ----------------------------------------------------------------------------- fingerprints
def test_create_fingerprint_follows_the_request_not_the_server_derived_values() -> None:
    inputs = [ActivityInput("LESSON", lesson_activity_id="a")]
    base = {
        "expected_head_revision_no": 0,
        "document_ref": None,
        "objectives": ["x"],
        "teacher_direction": "d",
        "safety_notes": None,
        "activities": inputs,
    }
    first = rules.create_fingerprint(**base)
    assert first == rules.create_fingerprint(**base)
    assert first != rules.create_fingerprint(**{**base, "expected_head_revision_no": 1})
    assert first != rules.create_fingerprint(**{**base, "objectives": ["y"]})
    assert first != rules.create_fingerprint(
        **{**base, "document_ref": {"document_id": "d", "revision_no": 1}}
    )
    assert first != rules.create_fingerprint(
        **{**base, "activities": [ActivityInput("LESSON", lesson_activity_id="b")]}
    )


def test_confirm_fingerprint_ignores_the_order_of_entries_and_items() -> None:
    one = ChecklistEntry(1, "v1", (ChecklistAnswer("a", True), ChecklistAnswer("b", True)))
    two = ChecklistEntry(2, "v1", (ChecklistAnswer("a", True),))
    swapped = ChecklistEntry(1, "v1", (ChecklistAnswer("b", True), ChecklistAnswer("a", True)))
    assert rules.confirm_fingerprint(3, "h" * 64, [one, two]) == rules.confirm_fingerprint(
        3, "h" * 64, [two, swapped]
    )
    assert rules.confirm_fingerprint(3, "h" * 64, [one]) != rules.confirm_fingerprint(
        4, "h" * 64, [one]
    )
    assert rules.confirm_fingerprint(3, "h" * 64, [one]) != rules.confirm_fingerprint(
        3, "i" * 64, [one]
    )
    unchecked = ChecklistEntry(1, "v1", (ChecklistAnswer("a", False), ChecklistAnswer("b", True)))
    assert rules.confirm_fingerprint(3, "h" * 64, [one]) != rules.confirm_fingerprint(
        3, "h" * 64, [unchecked]
    )


# ----------------------------------------------------------------------------- etag and cursor
def test_the_etag_names_content_and_state() -> None:
    assert rules.plan_etag("a" * 64, "DRAFT") == f'"{"a" * 64}.DRAFT"'
    assert rules.plan_etag("a" * 64, "DRAFT") != rules.plan_etag("a" * 64, "APPROVED")
    assert rules.plan_etag_value("a" * 64, "APPROVED") == f"{'a' * 64}.APPROVED"
    etag = rules.plan_etag("a" * 64, "DRAFT")
    assert rules.etag_matches(etag, etag) and rules.etag_matches(f'"x", {etag}', etag)
    assert rules.etag_matches("*", etag) and not rules.etag_matches(None, etag)
    assert not rules.etag_matches('"other"', etag)


def test_the_cursor_round_trips_and_every_defect_is_a_cursor_error() -> None:
    assert rules.decode_plan_cursor(rules.encode_plan_cursor(7)) == 7
    for bad in ("", "!!!", "e30", rules.encode_plan_cursor(0), "x" * 600):
        with pytest.raises(LessonOccurrenceRuleError) as error:
            rules.decode_plan_cursor(bad)
        assert (error.value.field, error.value.code) == ("cursor", "INVALID_FORMAT")
