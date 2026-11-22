"""FEAT-066 T-4b2: the pure rules and builders of the Teacher StoryRun create (offline).

SRS l.1445-1449 (one confirmed child, no array), l.1663, l.549 and l.354 (a minimal snapshot, no
name, no seed), R2 N-1 (the Teacher view of every stored shape round-trips, with a string profile
ref
and a canonical selection id) and the OD-14 window (``has_ready_output``).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from sketch2life.application.ports.parent_story_runs import TeacherStoryRunRecord
from sketch2life.contracts.schemas.teacher_story_runs import (
    TeacherRunContextSnapshotV1,
    TeacherRunPinSnapshotV1,
    TeacherStoryRunCreateRequestV1,
)
from sketch2life.domain.story_teacher import (
    CONTEXT_DIRECTION_CHARS,
    CONTEXT_MAX_BYTES,
    CONTEXT_OBJECTIVE_CHARS,
    CONTEXT_OBJECTIVES_MAX,
    LOCK_FREE_STATES,
    build_context_snapshot,
    build_pin_snapshot,
    canonical_json,
    create_fingerprint,
    has_lock_free_state,
    is_teacher_shaped,
    multi_child_requested,
    parse_json_object,
    sha256_json,
)
from sketch2life.domain.story_video.model import has_ready_output, is_playable
from sketch2life.interfaces.http.routers.story_run_create_dispatch import (
    teacher_envelope,
    teacher_story_run_response,
)

HASH = "b" * 64
SELECTION_ID = str(uuid4())
CHILD = "synthetic-0123456789abcdef01234567"
BODY: dict[str, Any] = {
    "profile_ref": {"kind": "MANAGED_PROFILE", "id": CHILD},
    "occurrence_id": str(uuid4()),
    "plan": {"revision_no": 3, "plan_hash": HASH},
    "activity_id": str(uuid4()),
    "selection_id": SELECTION_ID,
    "selection_sha256": HASH,
}


# ----------------------------------------------------------------------------- the dispatch shape
def test_a_json_object_with_a_teacher_key_or_a_multi_child_spelling_is_teacher_shaped() -> None:
    for key in (
        "profile_ref",
        "occurrence_id",
        "plan",
        "activity_id",
        "selection_id",
        "selection_sha256",
        "profile_refs",
        "child_ids",
        "children",
        "profiles",
    ):
        assert is_teacher_shaped({key: 1}), key
    assert is_teacher_shaped({"parent_profile_id": "x", "occurrence_id": "o"})


def test_everything_else_stays_with_the_parent_handler() -> None:
    assert not is_teacher_shaped({"parent_profile_id": "x"})
    assert not is_teacher_shaped({"parent_profile_id": "x", "topic": "t", "lesson_version": None})
    assert not is_teacher_shaped({})
    assert not is_teacher_shaped(None)
    for raw in (b"", b"{", b"[1]", b'"x"', b"1", b"null", b"\xff\xfe"):
        assert parse_json_object(raw) is None, raw
    assert parse_json_object(b'{"a": 1}') == {"a": 1}
    assert parse_json_object(b"[" * 100_000) is None  # no recursion error


def test_the_multi_child_pre_check_reads_the_raw_json() -> None:
    assert multi_child_requested({"profile_refs": []})
    assert multi_child_requested({"children": "x"})
    assert multi_child_requested({"profile_ref": [{"id": "a"}]})
    assert multi_child_requested({"profile_ref": {"kind": "MANAGED_PROFILE", "id": ["a", "b"]}})
    assert not multi_child_requested(BODY)
    assert not multi_child_requested({"profile_ref": {"kind": "MANAGED_PROFILE", "id": "a"}})
    assert not multi_child_requested({"profile_ref": "text"})


# ----------------------------------------------------------------------------- the request model
def test_the_teacher_body_is_closed_strict_and_names_one_child() -> None:
    body = TeacherStoryRunCreateRequestV1.model_validate(BODY)
    assert body.profile_ref.id == CHILD and body.plan.revision_no == 3
    for broken in (
        {**BODY, "child_name": "x"},
        {**BODY, "plan": {**BODY["plan"], "extra": 1}},
        {**BODY, "plan": {"revision_no": "3", "plan_hash": HASH}},
        {**BODY, "plan": {"revision_no": 0, "plan_hash": HASH}},
        {**BODY, "plan": {"revision_no": 1, "plan_hash": "A" * 64}},
        {**BODY, "selection_id": "11111111-1111-1111-1111-11111111111"},
        {**BODY, "selection_id": str(uuid4()).upper()},
        {**BODY, "selection_sha256": "x"},
        {**BODY, "profile_ref": {"kind": "PROFILE", "id": CHILD}},
        {**BODY, "profile_ref": {"kind": "MANAGED_PROFILE", "id": ""}},
        {**BODY, "profile_ref": {"kind": "MANAGED_PROFILE", "id": "x" * 129}},
        {**BODY, "activity_id": ""},
        {key: value for key, value in BODY.items() if key != "activity_id"},
    ):
        with pytest.raises(ValidationError):
            TeacherStoryRunCreateRequestV1.model_validate(broken)


def test_the_fingerprint_is_the_canonical_body() -> None:
    assert create_fingerprint(BODY) == create_fingerprint(dict(reversed(list(BODY.items()))))
    assert create_fingerprint(BODY) != create_fingerprint({**BODY, "activity_id": "other"})
    assert len(create_fingerprint(BODY)) == 64
    assert sha256_json({"b": 1, "a": 2}) == sha256_json({"a": 2, "b": 1})
    assert canonical_json({"é": "ệ"}) == '{"é":"ệ"}'


# ----------------------------------------------------------------------------- the snapshots
def _context(**override: object) -> dict[str, object]:
    values: dict[str, object] = {
        "selection_id": SELECTION_ID,
        "age_months": 60,
        "age_revision": 2,
        "objectives": ["Nhận biết hình tròn", "Kể chuyện chú mèo"],
        "teacher_direction": "Kể chuyện về chú mèo đi tìm bạn",
        "activity_title": "Vẽ theo mẫu",
        "activity_snapshot_hash": HASH,
    }
    values.update(override)
    return values


def test_the_context_snapshot_holds_no_name_no_media_no_seed_and_validates() -> None:
    snapshot = build_context_snapshot(**_context())  # type: ignore[arg-type]
    assert set(snapshot) == {
        "schema_version",
        "selection_id",
        "age_months",
        "age_revision",
        "objectives",
        "teacher_direction",
        "activity_title",
        "activity_snapshot_hash",
    }
    assert snapshot["schema_version"] == "sketch2life.teacher-context.v1"
    TeacherRunContextSnapshotV1.model_validate(snapshot)
    text = json.dumps(snapshot)
    for forbidden in ("name", "asset", "seed", "index", CHILD):
        assert forbidden not in text.replace("selection_id", "")


def test_the_context_is_bounded_by_clipping_and_by_a_size_guard() -> None:
    long_objective = "ệ" * 1000
    snapshot = build_context_snapshot(
        **_context(  # type: ignore[arg-type]
            objectives=[long_objective] * 20,
            teacher_direction="d" * 5000,
            activity_title="t" * 500,
        )
    )
    assert len(snapshot["objectives"]) == CONTEXT_OBJECTIVES_MAX
    assert all(len(item) == CONTEXT_OBJECTIVE_CHARS for item in snapshot["objectives"])
    assert len(snapshot["teacher_direction"]) == CONTEXT_DIRECTION_CHARS
    assert len(canonical_json(snapshot).encode("utf-8")) <= CONTEXT_MAX_BYTES
    TeacherRunContextSnapshotV1.model_validate(snapshot)
    no_title = build_context_snapshot(**_context(activity_title=None, activity_snapshot_hash=None))  # type: ignore[arg-type]
    assert no_title["activity_title"] is None
    TeacherRunContextSnapshotV1.model_validate(no_title)


def _pin(lesson: dict[str, object] | None = None) -> dict[str, object]:
    return build_pin_snapshot(
        occurrence_id=str(uuid4()),
        plan_revision_id=str(uuid4()),
        plan_revision_no=3,
        plan_hash=HASH,
        activity={
            "plan_activity_id": str(uuid4()),
            "kind": "CUSTOM",
            "catalog_activity_ref": None,
            "activity_version": None,
            "snapshot_hash": None,
        },
        lesson=lesson,
    )


def test_the_pin_snapshot_validates_with_and_without_a_lesson_lineage() -> None:
    TeacherRunPinSnapshotV1.model_validate(_pin())
    lineage = {
        "lesson_id": str(uuid4()),
        "version_id": str(uuid4()),
        "version_no": 4,
        "version_hash": HASH,
    }
    pin = _pin(lineage)
    TeacherRunPinSnapshotV1.model_validate(pin)
    assert pin["schema_version"] == "sketch2life.teacher-run-pin.v1"
    assert pin["lesson"] == lineage
    # the same dict is the stored JSONB and the hashed value
    assert sha256_json(pin) == sha256_json(json.loads(json.dumps(pin)))


# ------------------------------------------------------------------- the Teacher view (N-1)
def _record(**override: object) -> TeacherStoryRunRecord:
    context = build_context_snapshot(**_context())  # type: ignore[arg-type]
    pin = _pin()
    values: dict[str, object] = {
        "run_id": str(uuid4()),
        "run_state": "INPUT_PROCESSING",
        "run_revision": 1,
        "profile_ref": CHILD,
        "profile_revision_ref": SELECTION_ID,
        "occurrence_id": str(pin["occurrence_id"]),
        "plan": {"revision_no": 3, "plan_hash": HASH},
        "activity": {
            "plan_activity_id": pin["activity"]["plan_activity_id"],  # type: ignore[index]
            "kind": "CUSTOM",
            "snapshot_hash": None,
        },
        "context_revision": 1,
        "context_confirmed": False,
        "context_snapshot": context,
        "context_snapshot_sha256": sha256_json(context),
        "current_input_revision": 1,
        "understanding_revision": None,
        "subject_label": None,
        "candidate": None,
        "story_revision_id": None,
        "story_revision_no": None,
        "story_status": None,
        "story_sha256": None,
        "story_content": None,
        "job_state": None,
        "retryable": False,
        "error_code": None,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
        "lesson_pin_snapshot": pin,
    }
    values.update(override)
    return TeacherStoryRunRecord(**values)  # type: ignore[arg-type]


def test_a_built_teacher_record_round_trips_with_a_string_profile_ref() -> None:
    record = _record()
    view = teacher_story_run_response(record)
    assert view.profile_ref.id == CHILD and view.profile_ref.kind == "MANAGED_PROFILE"
    assert view.profile_revision_ref == SELECTION_ID
    UUID(view.profile_revision_ref)  # the selection id is a canonical uuid (T-4b1 N-9)
    assert view.plan is not None and view.plan.revision_no == 3
    assert view.activity is not None and view.activity.kind == "CUSTOM"
    assert view.context_snapshot.schema_version == "sketch2life.teacher-context.v1"
    assert view.lesson_pin_snapshot is not None
    assert view.lesson_pin_snapshot.schema_version == "sketch2life.teacher-run-pin.v1"
    body = teacher_envelope(record).model_dump(mode="json")
    assert "parent_profile_id" not in json.dumps(body)
    assert set(body["story_run"]) >= {"profile_ref", "occurrence_id", "plan", "activity"}
    assert CHILD not in json.dumps(body["story_run"]["context_snapshot"])


def test_a_fixture_run_with_parent_snapshots_and_no_occurrence_still_reads() -> None:
    """A row written by T-4a1 or T-13a (no occurrence pin, Parent-schema snapshots) must not 500."""

    parent_context = {
        "schema_version": "sketch2life.parent-context.v1",
        "profile_revision_ref": str(uuid4()),
        "age_months": 60,
        "interests_summary": "",
        "topic": "",
        "adult_confirmed_idea": "",
    }
    record = _record(
        occurrence_id=None,
        plan=None,
        activity=None,
        profile_revision_ref=parent_context["profile_revision_ref"],
        context_snapshot=parent_context,
        context_snapshot_sha256=sha256_json(parent_context),
        lesson_pin_snapshot=None,
    )
    view = teacher_story_run_response(record)
    assert view.occurrence_id is None and view.plan is None and view.activity is None
    assert view.context_snapshot.schema_version == "sketch2life.parent-context.v1"
    assert view.profile_ref.id == CHILD


def test_the_view_accepts_every_run_state_the_check_allows() -> None:
    for state in (
        "INPUT_PROCESSING",
        "INPUT_REVIEW",
        "SUBJECT_REVIEW",
        "SCRIPT_REVIEW",
        "VIDEO_READY",
        "SAFETY_BLOCKED",
        "COMPLETED",
        "ABANDONED",
    ):
        assert teacher_story_run_response(_record(run_state=state)).run_state == state


# -------------------------------------------------------------------- the slot and the lock
def test_has_ready_output_is_is_playable_without_the_run_state() -> None:
    ready: dict[str, Any] = {
        "generation_state": "READY",
        "technical": "PASSED",
        "consistency": "PASSED",
        "safety": "PASSED",
        "has_output": True,
    }
    assert has_ready_output(**ready)
    assert is_playable(run_state="VIDEO_READY", **ready)
    # a completed (unprojected) run holds the sample although it is no longer playable
    assert not is_playable(run_state="COMPLETED", **ready)
    assert has_ready_output(**ready)
    for change in (
        {"generation_state": "FAILED"},
        {"generation_state": "SAFETY_BLOCKED"},
        {"generation_state": None},
        {"technical": "FAILED"},
        {"consistency": "PENDING"},
        {"safety": "FAILED"},
        {"safety": None},
        {"has_output": False},
    ):
        assert not has_ready_output(**{**ready, **change}), change


def test_the_lock_free_states_are_the_five_terminal_ones() -> None:
    assert {"COMPLETED", "FAILED", "ABANDONED", "DELETE_PENDING", "DELETED"} == LOCK_FREE_STATES
    assert all(has_lock_free_state(state) for state in LOCK_FREE_STATES)
    assert not has_lock_free_state("SAFETY_BLOCKED")
    assert not has_lock_free_state("VIDEO_READY")
