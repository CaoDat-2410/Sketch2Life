"""FEAT-066 T-3a: pure rules, contracts and envelope bookkeeping of the lesson occurrence."""

from __future__ import annotations

import ast
import json
from datetime import UTC, date, datetime, timedelta, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from sketch2life.contracts.schemas.lesson_occurrences import (
    CreateLessonOccurrenceRequestV1,
    LessonOccurrenceV1,
    LessonVersionRefV1,
)
from sketch2life.contracts.schemas.parent_story_runs import ParentLessonVersionRefV1
from sketch2life.domain.lesson_occurrences.model import (
    OCCURRENCE_STATES,
    AccessOutcome,
    AssignmentFact,
    LessonOccurrenceRuleError,
    decide_create,
    decide_read,
    decide_write,
    decode_cursor,
    encode_cursor,
    etag_for_revision,
    has_forbidden_characters,
    if_none_match_matches,
    normalize_title,
    parse_scheduled_date,
)
from sketch2life.infrastructure.lesson_occurrences.service import (
    create_fingerprint,
    occurrence_body,
)
from sketch2life.interfaces.http import error_envelope as envelope

SRC = Path(__file__).resolve().parents[2] / "src" / "sketch2life"
HASH = "a" * 64


def _request(**overrides: object) -> CreateLessonOccurrenceRequestV1:
    body: dict[str, object] = {"class_id": "class-1", "title": "Bài học vẽ con mèo"}
    body.update(overrides)
    return CreateLessonOccurrenceRequestV1.model_validate(body)


# ----------------------------------------------------------------------------- title and date
def test_title_is_trimmed_and_bounded() -> None:
    assert normalize_title("  Bài học 1  ") == "Bài học 1"
    assert normalize_title("a" * 200) == "a" * 200
    for raw, code in (
        ("   ", "EMPTY"),
        ("", "EMPTY"),
        ("a" * 201, "TOO_LONG"),
        ("a\u0000b", "INVALID_FORMAT"),
    ):
        with pytest.raises(LessonOccurrenceRuleError) as caught:
            normalize_title(raw)
        assert (caught.value.field, caught.value.code) == ("title", code)
    assert has_forbidden_characters("x\ud800y") and has_forbidden_characters("a\nb")
    assert not has_forbidden_characters("Tiếng Việt có dấu 🙂")


def test_scheduled_date_is_an_iso_calendar_date_only() -> None:
    assert parse_scheduled_date("2026-11-20") == date(2026, 11, 20)
    for raw in ("2026-13-01", "20-11-2026", "2026-11-20T00:00:00", 20261120, None, "2026-1-2 "):
        with pytest.raises(LessonOccurrenceRuleError) as caught:
            parse_scheduled_date(raw)
        assert (caught.value.field, caught.value.code) == ("scheduled_date", "INVALID_FORMAT")


def test_request_schema_is_strict_and_closed() -> None:
    ok = _request(scheduled_date="2026-11-20", title="  Bài  ")
    assert ok.title == "Bài" and ok.scheduled_date == date(2026, 11, 20)
    assert ok.lesson_version_ref is None
    for bad in (
        {"extra": 1},
        {"organization_id": "org"},
        {"responsible_teacher_ref": "x"},
        {"title": "   "},
        {"title": "x" * 201},
        {"title": "a\u0000"},
        {"class_id": ""},
        {"class_id": "c" * 129},
        {"scheduled_date": "20/11/2026"},
        {"scheduled_date": 5},
        {"lesson_version_ref": {"lesson_id": "l", "version_id": "v"}},
        {"lesson_version_ref": {"lesson_id": "l", "version_id": "v", "content_sha256": "A" * 64}},
        {
            "lesson_version_ref": {
                "lesson_id": "l",
                "version_id": "v",
                "content_sha256": HASH,
                "version_no": 1,
            }
        },
    ):
        with pytest.raises(ValidationError):
            _request(**bad)
    pinned = _request(
        lesson_version_ref={"lesson_id": "l", "version_id": "v", "content_sha256": HASH}
    )
    assert pinned.lesson_version_ref == LessonVersionRefV1(
        lesson_id="l", version_id="v", content_sha256=HASH
    )


def test_the_lesson_pin_has_the_shape_of_the_parent_typed_reference() -> None:
    """SRS l.547 and l.2563: one typed reference for occurrence, plan revision and StoryRun."""
    mine = LessonVersionRefV1.model_json_schema()
    parent = ParentLessonVersionRefV1.model_json_schema()
    for key in ("properties", "required", "additionalProperties", "type"):
        assert mine[key] == parent[key]
    values = {"lesson_id": "lesson-1", "version_id": "version-1", "content_sha256": HASH}
    assert json.dumps(LessonVersionRefV1(**values).model_dump(mode="json"), sort_keys=True) == (
        json.dumps(ParentLessonVersionRefV1(**values).model_dump(mode="json"), sort_keys=True)
    )
    assert LessonVersionRefV1.model_config == ParentLessonVersionRefV1.model_config


def test_the_fingerprint_follows_the_canonical_request() -> None:
    first = create_fingerprint(_request(scheduled_date="2026-11-20"))
    assert first == create_fingerprint(
        _request(scheduled_date="2026-11-20", title="  Bài học vẽ con mèo ")
    )
    assert len(first) == 64
    for other in (
        _request(scheduled_date="2026-11-21"),
        _request(),
        _request(class_id="class-2", scheduled_date="2026-11-20"),
        _request(title="Khác", scheduled_date="2026-11-20"),
        _request(
            scheduled_date="2026-11-20",
            lesson_version_ref={"lesson_id": "l", "version_id": "v", "content_sha256": HASH},
        ),
    ):
        assert create_fingerprint(other) != first


# ----------------------------------------------------------------------------- decision table
def _rows(*pairs: tuple[str, str | None]) -> list[AssignmentFact]:
    return [AssignmentFact(role=role, class_id=class_id) for role, class_id in pairs]


@pytest.mark.parametrize(
    ("rows", "expected"),
    [
        ([], AccessOutcome.NOT_FOUND),
        (_rows(("teacher", "A")), AccessOutcome.PROCEED),
        (_rows(("teacher", "B")), AccessOutcome.ASSIGNMENT_REQUIRED),
        (_rows(("teacher", None)), AccessOutcome.ASSIGNMENT_REQUIRED),
        (_rows(("guide", "A")), AccessOutcome.FORBIDDEN),
        (_rows(("observer", "A")), AccessOutcome.FORBIDDEN),
        (_rows(("guide", "A"), ("teacher", "B")), AccessOutcome.FORBIDDEN),
        (_rows(("guide", "A"), ("teacher", "A")), AccessOutcome.PROCEED),
        (_rows(("guide", None)), AccessOutcome.ASSIGNMENT_REQUIRED),
        (_rows(("teacher", "B"), ("teacher", None)), AccessOutcome.ASSIGNMENT_REQUIRED),
    ],
)
def test_create_decision_table(rows: list[AssignmentFact], expected: AccessOutcome) -> None:
    assert decide_create(rows, "A") is expected


def test_the_conflict_branch_is_reachable_only_after_the_organization_check() -> None:
    # A caller with no rows in the organization (stranger, other organization) never reaches 409.
    assert decide_create([], "A") is AccessOutcome.NOT_FOUND
    assert decide_create(_rows(("teacher", "B")), "A") is AccessOutcome.ASSIGNMENT_REQUIRED


@pytest.mark.parametrize(
    ("rows", "expected"),
    [
        ([], AccessOutcome.NOT_FOUND),
        (_rows(("teacher", "B")), AccessOutcome.NOT_FOUND),
        (_rows(("teacher", "A")), AccessOutcome.PROCEED),
        (_rows(("guide", "A")), AccessOutcome.PROCEED),
        (_rows(("observer", None)), AccessOutcome.PROCEED),
        (_rows(("teacher", None)), AccessOutcome.PROCEED),
    ],
)
def test_read_decision_table(rows: list[AssignmentFact], expected: AccessOutcome) -> None:
    assert decide_read(rows, "A") is expected


@pytest.mark.parametrize(
    ("rows", "caller", "expected"),
    [
        ([], "me", AccessOutcome.NOT_FOUND),
        (_rows(("teacher", "B")), "me", AccessOutcome.NOT_FOUND),
        (_rows(("guide", "A")), "me", AccessOutcome.FORBIDDEN),
        (_rows(("teacher", "A")), "me", AccessOutcome.PROCEED),
        (_rows(("teacher", "A")), "other", AccessOutcome.FORBIDDEN),
        (_rows(("teacher", None)), "me", AccessOutcome.PROCEED),
    ],
)
def test_write_decision_table(
    rows: list[AssignmentFact], caller: str, expected: AccessOutcome
) -> None:
    outcome = decide_write(rows, "A", caller_account_ref=caller, responsible_teacher_ref="me")
    assert outcome is expected


# ----------------------------------------------------------------------------- cursor and ETag
def test_cursor_round_trips_and_rejects_every_defect() -> None:
    moment = datetime(2026, 11, 20, 10, 30, 15, 123456, tzinfo=UTC)
    cursor = encode_cursor(moment, "occ-1")
    assert decode_cursor(cursor) == (moment, "occ-1")
    other_zone = datetime(2026, 11, 20, 17, 30, 15, 123456, tzinfo=timezone(timedelta(hours=7)))
    assert decode_cursor(encode_cursor(other_zone, "occ-2"))[0] == moment
    for bad in ("", "@@@", "e30", "x" * 600, encode_cursor(moment, "o")[:-3] + "!!!"):
        with pytest.raises(LessonOccurrenceRuleError) as caught:
            decode_cursor(bad)
        assert (caught.value.field, caught.value.code) == ("cursor", "INVALID_FORMAT")
    naive = encode_cursor(datetime(2026, 1, 1), "occ-1")
    with pytest.raises(LessonOccurrenceRuleError):
        decode_cursor(naive)


def test_etag_is_the_strong_quoted_revision() -> None:
    assert etag_for_revision(3) == '"3"'
    assert if_none_match_matches('"3"', 3)
    assert if_none_match_matches('"1", "3"', 3)
    assert if_none_match_matches("*", 3)
    assert not if_none_match_matches('"2"', 3)
    assert not if_none_match_matches('W/"3"', 3)
    assert not if_none_match_matches(None, 3)


def test_the_occurrence_body_has_no_organization_storage_or_child_field() -> None:
    row = {
        "occurrence_id": "o1",
        "class_ref": "c1",
        "title": "T",
        "scheduled_date": None,
        "state": "DRAFT",
        "revision": 1,
        "responsible_teacher_ref": "acct",
        "source_lesson_id": None,
        "source_lesson_version_id": None,
        "source_lesson_version_no": None,
        "source_lesson_version_hash": None,
        "sample_slot_state": "AVAILABLE",
        "sample_claimed_at": None,
        "successful_sample_run_ref": None,
        "created_at": datetime(2026, 11, 20, tzinfo=UTC),
        "organization_ref": "org",
        "approved_plan_revision_id": None,
    }
    body = occurrence_body(row, None)  # type: ignore[arg-type]
    model = LessonOccurrenceV1.model_validate(body)
    assert set(model.model_dump()) == {
        "contract",
        "occurrence_id",
        "class_id",
        "title",
        "scheduled_date",
        "state",
        "revision",
        "responsible_teacher_ref",
        "lesson_version_ref",
        "lesson_version_no",
        "approved_plan",
        "sample_video",
        "created_at",
    }
    text = json.dumps(body, default=str)
    assert "org" not in body and "organization" not in text
    assert body["sample_video"] == {"slot_state": "AVAILABLE", "claimed_at": None, "run_ref": None}
    assert body["state"] in OCCURRENCE_STATES


# ----------------------------------------------------------------------------- envelope
def _service_codes() -> set[str]:
    codes: set[str] = set()
    for relative in (
        "infrastructure/lesson_occurrences/scope.py",
        "infrastructure/lesson_occurrences/service.py",
        "interfaces/http/routers/lesson_occurrences.py",
    ):
        tree = ast.parse((SRC / relative).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "LessonOccurrenceError"
                and len(node.args) >= 2
                and isinstance(node.args[1], ast.Constant)
            ):
                codes.add(str(node.args[1].value))
    return codes


def test_every_code_the_occurrence_code_raises_has_a_message_or_status_message() -> None:
    codes = _service_codes()
    assert {
        "RESOURCE_NOT_FOUND",
        "ACTION_NOT_ALLOWED",
        "TEACHER_ASSIGNMENT_REQUIRED",
        "INVALID_STATE_TRANSITION",
        "STALE_REVISION",
        "INVALID_IDEMPOTENCY_KEY",
        "RESOURCE_CONFLICT",
        "INVALID_REQUEST",
        "PROVIDER_UNAVAILABLE",
    } <= codes
    for code in codes:
        assert code in envelope.MESSAGES or code in envelope.STATUS_MESSAGE_ONLY, code
    assert "LESSON_PLAN_NOT_APPROVED" not in codes  # belongs to the run task (SRS l.871)
    assert "CLASS_CAPACITY_REACHED" not in codes  # capacity is X-13 (T-3a-DEC-5)
    assert envelope.message_for(409, "TEACHER_ASSIGNMENT_REQUIRED").startswith("Giáo viên")


def test_occurrence_states_are_the_srs_set_and_the_public_enum_matches() -> None:
    """SRS §6.1.1 (l.396)."""
    expected = (
        "DRAFT",
        "DOCUMENT_REVIEW",
        "PLAN_REVIEW",
        "APPROVED",
        "SAMPLE_AVAILABLE",
        "SAMPLE_USED",
        "ARCHIVED",
    )
    assert expected == OCCURRENCE_STATES
    schema = LessonOccurrenceV1.model_json_schema()["properties"]["state"]
    assert tuple(schema["enum"]) == expected
    assert all(len(state) <= 16 for state in expected)
