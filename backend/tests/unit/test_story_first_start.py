"""FEAT-066 goal v4 T-2e-a / OPEN-A: the implicit first-story start (``FirstStoryStarter``).

Offline, with a scripted session: the truth table of the Parent predicate P and of the Teacher
predicate P_T (V4-A OPEN-A D2), the v2 worker input of both roles, the reservation, one story under
two evaluations, the failure path, the generator capability flag and the non-raising probe. The
behaviour inside the real transactions is proven on PostgreSQL in
``tests/integration/test_parent_activity_selection_postgres.py`` and
``tests/integration/story_teacher/test_teacher_first_story_postgres.py``.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import Insert, Select, Update

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
from sketch2life.domain.story_teacher import TEACHER_PIN_SCHEMA, teacher_pin_ready
from sketch2life.infrastructure.persistence import story_first_start
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
    _live_run,
    _sha256_json,
)
from sketch2life.infrastructure.persistence.story_first_start import (
    FIRST_STORY_INPUT_SCHEMA,
    FIRST_STORY_MODEL_ID,
    FIRST_STORY_MODEL_REVISION,
    FIRST_STORY_PROMPT_VERSION,
    FirstStoryStarter,
)
from sketch2life.infrastructure.story_inputs.story_generation import (
    STORY_REWRITE_MODEL_ID,
    STORY_REWRITE_MODEL_REVISION,
    STORY_REWRITE_PROMPT_VERSION,
)

RUN_ID = "11111111-1111-4111-8111-111111111111"
PRINCIPAL = VerifiedPrincipal("parent-1", "issuer-1", frozenset())
NOW = datetime(2026, 11, 22, 10, tzinfo=UTC)
HASH = "b" * 64
WORKER_KEYS = {
    "schema_version",
    "role",
    "language",
    "confirmed_subject",
    "understanding_revision",
    "drawing_sha256",
    "visible_features",
    "child_age_months",
    "context_revision",
    "adult_confirmed_idea",
    "activity",
    "lesson_direction",
}
ACTIVITY_KEYS = {
    "title",
    "objective",
    "instructions_text",
    "safety_notes",
    "activity_kind",
    "source",
    "lesson_id",
    "version_id",
    "content_sha256",
}


def _run(**changes: Any) -> dict[str, Any]:
    run = {
        "run_id": RUN_ID,
        "occurrence_ref": None,
        "actor_scope_ref": "parent-account-1",
        "run_state": "PREPARATION_REVIEW",
        "understanding_revision": 2,
        "subject_label": " rong ",
        "version": 7,
        "revision": 9,
    }
    run.update(changes)
    return run


def _selection() -> dict[str, Any]:
    return {
        "lesson_id": "lesson-1",
        "version_id": "version-1",
        "content_sha256": HASH,
        "activity_index": 0,
        "activity_snapshot": {
            "schema": "sketch2life.parent-activity-pin.v1",
            "title": "Tim la cay",
            "objective": "Quan sat",
            "instructions_text": "Cung tre di tim",
            "safety_notes": "Di cung nguoi lon",
            "activity_kind": "outdoor",
            "source": "PUBLIC",
            "materials_text": "must not reach the worker",
        },
    }


OCCURRENCE = "occurrence-1"
ORGANIZATION = "organization-1"


def _pin(**changes: Any) -> dict[str, Any]:
    pin: dict[str, Any] = {
        "schema_version": TEACHER_PIN_SCHEMA,
        "occurrence_id": OCCURRENCE,
        "plan_revision_id": "plan-revision-1",
        "plan_revision_no": 2,
        "plan_hash": "c" * 64,
        "activity": {
            "plan_activity_id": "plan-activity-1",
            "kind": "CUSTOM",
            "catalog_activity_ref": None,
            "activity_version": None,
            "snapshot_hash": None,
        },
        "lesson": None,
    }
    pin.update(changes)
    return pin


def _basis(pin: Any = None) -> tuple[Any, Any, str, list[str]]:
    understanding = {"revision_no": 2}
    input_row = {
        "context_snapshot": {
            "age_months": 60,
            "teacher_direction": "Cau chuyen ve chu meo",
            "objectives": ["Nhan biet hinh tron"],
            "activity_title": "Ve bang ngon tay",
        },
        "context_revision": 3,
        "original_sha256": HASH,
        "lesson_pin_snapshot": pin,
    }
    return understanding, input_row, "adult idea", ["leaf", "stem"]


class _Result:
    def __init__(self, row: Any) -> None:
        self._row = row

    def mappings(self) -> _Result:
        return self

    def one(self) -> Any:
        return self._row

    def one_or_none(self) -> Any:
        return self._row


class _Session:
    def __init__(
        self,
        *,
        run: dict[str, Any] | None = None,
        has_revision: bool = False,
        selection: dict[str, Any] | None = None,
        fail_on_write: bool = False,
    ) -> None:
        self.run = run if run is not None else _run()
        self.has_revision = has_revision
        self.selection = selection if selection is not None else _selection()
        self.fail_on_write = fail_on_write
        self.writes: list[Insert | Update] = []
        self.rolled_back = False

    def execute(self, statement: Any) -> _Result:
        if isinstance(statement, Insert | Update):
            if self.fail_on_write:
                raise SQLAlchemyError("synthetic")
            self.writes.append(statement)
            if isinstance(statement, Insert):
                self.has_revision = True
                self.run = {**self.run, "run_state": "SCRIPT_GENERATING"}
            return _Result(None)
        assert isinstance(statement, Select)
        table = statement.get_final_froms()[0].name
        if table == "runs":
            return _Result(self.run)
        assert table == "activity_selections", table
        return _Result(self.selection)

    def scalar(self, _statement: Any) -> Any:
        return "story-revision" if self.has_revision else None

    def rollback(self) -> None:
        self.rolled_back = True


def _starter(
    session: _Session, *, enabled: bool = True, probe: Any = None, teacher: bool = False
) -> FirstStoryStarter:
    return FirstStoryStarter(
        session,  # type: ignore[arg-type]
        enabled=enabled,
        probe=probe if probe is not None else (lambda _p, _r, _u: _basis()),  # type: ignore[arg-type]
        live_run=_live_run,
        sha256_json=_sha256_json,
        teacher=teacher,
    )


def _teacher_session(**changes: Any) -> _Session:
    return _Session(
        run=_run(occurrence_ref=OCCURRENCE, actor_scope_ref=ORGANIZATION, **changes),
        selection=None,  # a Teacher run has no selection row and none is read
    )


def _teacher_starter(
    session: _Session, *, pin: Any = "valid", enabled: bool = True
) -> FirstStoryStarter:
    stored = _pin() if pin == "valid" else pin
    return _starter(
        session,
        enabled=enabled,
        probe=lambda _p, _r, _u: _basis(stored),
        teacher=True,
    )


# ------------------------------------------------------------------------- the truth table of P
@pytest.mark.parametrize(
    "case",
    [
        "job_side",
        "input_review_state",
        "script_review_state",
        "story_exists",
        "no_selection",
        "probe_not_ready",
    ],
)
def test_each_unmet_gate_starts_nothing_and_writes_nothing(case: str) -> None:
    session = _Session()
    probe = None
    enabled = True
    if case == "job_side":
        enabled = False
    elif case == "input_review_state":
        session.run = _run(run_state="SUBJECT_REVIEW")
    elif case == "script_review_state":
        session.run = _run(run_state="SCRIPT_REVIEW")
    elif case == "story_exists":
        session.has_revision = True
    elif case == "no_selection":
        session.selection = None  # type: ignore[assignment]
    else:
        probe = lambda _p, _r, _u: None  # noqa: E731
    assert (
        _starter(session, enabled=enabled, probe=probe).start_if_ready(RUN_ID, PRINCIPAL, NOW)
        is None
    )
    assert session.writes == [] and not session.rolled_back


def test_all_gates_met_reserves_revision_one_without_a_receipt() -> None:
    session = _Session()
    reservation = _starter(session).start_if_ready(RUN_ID, PRINCIPAL, NOW)
    assert reservation is not None
    assert (reservation.run_id, reservation.revision_no, reservation.receipt_id) == (
        RUN_ID,
        1,
        None,
    )
    assert reservation.understanding_revision == 2 and reservation.context_revision == 3
    assert reservation.source_asset_sha256 == HASH and not reservation.replayed
    insert, update = session.writes
    assert isinstance(insert, Insert) and isinstance(update, Update)
    values = insert.compile().params
    assert values["status"] == "GENERATING" and values["revision_no"] == 1
    assert values["model_id"] == FIRST_STORY_MODEL_ID
    assert values["model_revision"] == FIRST_STORY_MODEL_REVISION
    assert values["prompt_version"] == FIRST_STORY_PROMPT_VERSION
    assert values["story_revision_id"] == reservation.story_revision_id
    assert values["request_sha256"] == reservation.request_sha256
    run_values = update.compile().params
    assert run_values["run_state"] == "SCRIPT_GENERATING" and run_values["job_state"] == "QUEUED"
    assert run_values["version"] == 8 and run_values["revision"] == 10
    assert run_values["retryable"] is False and run_values["error_code"] is None


def test_the_parent_worker_input_is_the_v3_shape_with_the_primary_activity() -> None:
    """FEAT-092: the Modal story client and worker accept only input v3 for a Parent run."""

    reservation = _starter(_Session()).start_if_ready(RUN_ID, PRINCIPAL, NOW)
    assert reservation is not None
    worker = reservation.worker_input
    assert worker["schema_version"] == "sketch2life.story-generation-input.v3"
    assert FIRST_STORY_INPUT_SCHEMA == "sketch2life.story-generation-input.v2"  # Teacher keeps v2
    assert set(worker) == {
        "schema_version", "role", "language", "topic", "confirmed_subject",
        "understanding_revision", "drawing_sha256", "visible_features", "child_age_months",
        "context_revision", "adult_confirmed_idea", "rewrite_instruction",
        "lesson_subject_learning_notes", "lesson_direction", "primary_activity",
        "primary_activity_sha256",
    }
    assert worker["role"] == "PARENT" and worker["lesson_direction"] is None
    assert worker["confirmed_subject"] == "rong"  # trimmed
    assert worker["child_age_months"] == 60 and worker["visible_features"] == ["leaf", "stem"]
    assert worker["adult_confirmed_idea"] == "adult idea"
    assert set(worker["primary_activity"]) == {
        "title", "objective", "materials_text", "preparation_text", "instructions_text",
        "observation_notes", "safety_notes", "activity_kind",
    }
    primary = json.dumps(
        worker["primary_activity"], ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    assert worker["primary_activity_sha256"] == hashlib.sha256(primary.encode("utf-8")).hexdigest()
    assert "activity" not in worker and "adult_rewrite_hint" not in worker
    canonical = json.dumps(worker, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    assert reservation.request_sha256 == hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _learning_switched_on(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        story_first_start, "get_settings", lambda: SimpleNamespace(story_learning=True)
    )


def test_the_first_parent_story_asks_for_a_learning_script_when_it_is_on(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FEAT-098: the app's first story starts by itself, so it must ask for the script there."""

    _learning_switched_on(monkeypatch)

    reservation = _starter(_Session()).start_if_ready(RUN_ID, PRINCIPAL, NOW)

    assert reservation is not None
    worker = reservation.worker_input
    learning = worker["learning"]
    assert (learning["scene_count"], learning["fact_count"], learning["fact_source"]) == (
        5,
        5,
        "AI_DRAFT",
    )
    canonical = json.dumps(worker, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    assert reservation.request_sha256 == hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def test_a_pinned_lesson_is_the_source_of_the_first_learning_script(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _learning_switched_on(monkeypatch)
    pin = {"subject_learning_notes": "La cay quang hop.", "script_following_allowed": False}

    starter = _starter(_Session(), probe=lambda _p, _r, _u: _basis(pin))
    reservation = starter.start_if_ready(RUN_ID, PRINCIPAL, NOW)

    assert reservation is not None
    assert reservation.worker_input["learning"]["fact_source"] == "LESSON"


def test_a_teacher_first_story_asks_for_no_learning_script(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _learning_switched_on(monkeypatch)

    reservation = _teacher_starter(_teacher_session()).start_if_ready(RUN_ID, PRINCIPAL, NOW)

    assert reservation is not None and "learning" not in reservation.worker_input


def test_the_first_story_reuses_the_rewrite_identifiers() -> None:
    assert FIRST_STORY_MODEL_ID == STORY_REWRITE_MODEL_ID
    assert FIRST_STORY_MODEL_REVISION == STORY_REWRITE_MODEL_REVISION
    assert FIRST_STORY_PROMPT_VERSION == STORY_REWRITE_PROMPT_VERSION


def test_two_evaluations_give_one_story() -> None:
    session = _Session()
    starter = _starter(session)
    assert starter.start_if_ready(RUN_ID, PRINCIPAL, NOW) is not None
    # the second caller (the other trigger) meets the committed state of the first
    assert starter.start_if_ready(RUN_ID, PRINCIPAL, NOW) is None
    assert len(session.writes) == 2  # one insert and one update, not four


# ------------------------------------------------------------------------- failure and the probe
def test_a_database_failure_rolls_back_and_says_503_not_a_conflict() -> None:
    session = _Session(fail_on_write=True)
    with pytest.raises(ParentStoryRunError) as raised:
        _starter(session).start_if_ready(RUN_ID, PRINCIPAL, NOW)
    assert (raised.value.status_code, raised.value.code) == (
        503,
        "PARENT_STORY_RUN_STORE_UNAVAILABLE",
    )
    assert session.rolled_back


def test_a_probe_failure_above_499_propagates_and_an_unmet_gate_is_not_ready() -> None:
    repository = SqlParentStoryRunRepository(SimpleNamespace())  # type: ignore[arg-type]

    def basis(**_kwargs: Any) -> Any:
        raise error

    repository._story_generation_basis = basis  # type: ignore[method-assign]
    for status in (409, 422):
        error = ParentStoryRunError(status, "PROFILE_CONTEXT_NOT_CONFIRMED")
        assert repository._first_story_probe(PRINCIPAL, _run(), 2) is None
    for status in (500, 503):
        error = ParentStoryRunError(status, "PARENT_STORY_CONTEXT_UNAVAILABLE")
        with pytest.raises(ParentStoryRunError) as raised:
            repository._first_story_probe(PRINCIPAL, _run(), 2)
        assert raised.value is error


def test_the_repository_starter_is_on_for_a_parent_and_a_teacher_and_off_job_side() -> None:
    parent = SqlParentStoryRunRepository(SimpleNamespace())  # type: ignore[arg-type]
    assert parent._first_story_starter()._enabled is True
    assert parent._first_story_starter()._teacher is False
    teacher = SqlParentStoryRunRepository(
        SimpleNamespace(),  # type: ignore[arg-type]
        actor=SimpleNamespace(is_teacher=True),  # type: ignore[arg-type]
    )
    assert teacher._first_story_starter()._enabled is True
    assert teacher._first_story_starter()._teacher is True
    # the job-side repository of a background task never starts a story (T-4b3a D6)
    job_side = SqlParentStoryRunRepository(
        SimpleNamespace(),  # type: ignore[arg-type]
        actor=SimpleNamespace(is_teacher=True),  # type: ignore[arg-type]
        job_side=True,
    )
    assert job_side._first_story_starter()._enabled is False
    parent_job_side = SqlParentStoryRunRepository(
        SimpleNamespace(),  # type: ignore[arg-type]
        job_side=True,
    )
    assert parent_job_side._first_story_starter()._enabled is False


# ------------------------------------------------------------------------- the Teacher predicate
def test_a_teacher_run_with_a_complete_pin_reserves_revision_one_without_a_selection() -> None:
    session = _teacher_session()
    reservation = _teacher_starter(session).start_if_ready(RUN_ID, PRINCIPAL, NOW)
    assert reservation is not None
    assert (reservation.run_id, reservation.revision_no, reservation.receipt_id) == (
        RUN_ID,
        1,
        None,
    )
    assert reservation.organization_id == ORGANIZATION
    insert, update = session.writes
    assert isinstance(insert, Insert) and isinstance(update, Update)
    assert update.compile().params["run_state"] == "SCRIPT_GENERATING"


def test_the_teacher_worker_input_is_the_v2_shape_with_the_direction_and_no_activity() -> None:
    reservation = _teacher_starter(_teacher_session()).start_if_ready(RUN_ID, PRINCIPAL, NOW)
    assert reservation is not None
    worker = reservation.worker_input
    assert set(worker) == WORKER_KEYS
    assert worker["schema_version"] == FIRST_STORY_INPUT_SCHEMA
    assert worker["role"] == "TEACHER" and worker["activity"] is None
    assert worker["lesson_direction"] == {
        "teacher_direction": "Cau chuyen ve chu meo",
        "objectives": ["Nhan biet hinh tron"],
        "activity_title": "Ve bang ngon tay",
    }
    assert worker["child_age_months"] == 60 and worker["confirmed_subject"] == "rong"
    assert "plan-revision-1" not in json.dumps(worker)  # no pin id reaches the worker
    canonical = json.dumps(worker, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    assert reservation.request_sha256 == hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@pytest.mark.parametrize(
    "case",
    [
        "no_pin",
        "other_schema",
        "other_occurrence",
        "no_plan_revision_id",
        "no_plan_hash",
        "no_plan_number",
        "no_activity",
        "no_activity_id",
        "unknown_kind",
        "lesson_without_snapshot_hash",
        "no_occurrence_pin_on_the_run",
        "unsupported_generator",
        "input_review_state",
        "story_exists",
        "probe_not_ready",
    ],
)
def test_each_unmet_teacher_gate_starts_nothing_and_writes_nothing(case: str) -> None:
    session = _teacher_session()
    pin: Any = "valid"
    flag = True
    probe_fails = False
    if case == "no_pin":
        pin = None
    elif case == "other_schema":
        pin = _pin(schema_version="sketch2life.other.v1")
    elif case == "other_occurrence":
        pin = _pin(occurrence_id="another-occurrence")
    elif case == "no_plan_revision_id":
        pin = _pin(plan_revision_id="")
    elif case == "no_plan_hash":
        pin = _pin(plan_hash=None)
    elif case == "no_plan_number":
        pin = _pin(plan_revision_no=0)
    elif case == "no_activity":
        pin = _pin(activity=None)
    elif case == "no_activity_id":
        pin = _pin(activity={"plan_activity_id": "", "kind": "CUSTOM", "snapshot_hash": None})
    elif case == "unknown_kind":
        pin = _pin(activity={"plan_activity_id": "a", "kind": "OTHER", "snapshot_hash": None})
    elif case == "lesson_without_snapshot_hash":
        pin = _pin(activity={"plan_activity_id": "a", "kind": "LESSON", "snapshot_hash": None})
    elif case == "no_occurrence_pin_on_the_run":
        session.run = _run(occurrence_ref=None, actor_scope_ref=ORGANIZATION)
    elif case == "unsupported_generator":
        flag = False
    elif case == "input_review_state":
        session.run = _run(
            run_state="SUBJECT_REVIEW", occurrence_ref=OCCURRENCE, actor_scope_ref=ORGANIZATION
        )
    elif case == "story_exists":
        session.has_revision = True
    else:
        probe_fails = True
    starter = _teacher_starter(session, pin=pin)
    if probe_fails:
        starter = _starter(session, probe=lambda _p, _r, _u: None, teacher=True)
    assert starter.start_if_ready(RUN_ID, PRINCIPAL, NOW, generator_supports_role=flag) is None
    assert session.writes == [] and not session.rolled_back


@pytest.mark.parametrize("kind", ["CATALOG", "LESSON"])
def test_a_catalog_or_lesson_activity_with_a_snapshot_hash_is_accepted(kind: str) -> None:
    pin = _pin(
        activity={"plan_activity_id": "a", "kind": kind, "snapshot_hash": "d" * 64},
    )
    assert teacher_pin_ready(pin, OCCURRENCE) is True


def test_a_custom_activity_without_a_snapshot_hash_is_accepted() -> None:
    assert teacher_pin_ready(_pin(), OCCURRENCE) is True
    assert teacher_pin_ready(_pin(), None) is False


def test_the_capability_flag_blocks_a_run_only_when_it_is_false() -> None:
    session = _teacher_session()
    assert (
        _teacher_starter(session).start_if_ready(
            RUN_ID, PRINCIPAL, NOW, generator_supports_role=False
        )
        is None
    )
    assert session.writes == []
    assert _teacher_starter(session).start_if_ready(RUN_ID, PRINCIPAL, NOW) is not None


def test_a_database_failure_on_a_read_is_a_503_with_a_rollback_too() -> None:
    class _ReadFails(_Session):
        def execute(self, statement: Any) -> _Result:
            raise SQLAlchemyError("synthetic read")

    session = _ReadFails()
    with pytest.raises(ParentStoryRunError) as raised:
        _starter(session).start_if_ready(RUN_ID, PRINCIPAL, NOW)
    assert (raised.value.status_code, raised.value.code) == (
        503,
        "PARENT_STORY_RUN_STORE_UNAVAILABLE",
    )
    assert session.rolled_back


def test_a_teacher_context_with_no_direction_starts_with_neither_activity_nor_direction() -> None:
    """Documented result (review P3-5): ``teacher_lesson_direction`` is ``None`` when the snapshot
    holds no direction, objective or title, and a Teacher run has no activity, so the worker
    receives the confirmed subject and features only. The plan activity title is stored at create,
    so this is rare; the story is not refused."""

    def probe(_p: Any, _r: Any, _u: Any) -> Any:
        understanding, input_row, idea, features = _basis(_pin())
        input_row["context_snapshot"] = {"age_months": 60}
        return understanding, input_row, idea, features

    session = _teacher_session()
    reservation = _starter(session, probe=probe, teacher=True).start_if_ready(
        RUN_ID, PRINCIPAL, NOW
    )
    assert reservation is not None
    assert reservation.worker_input["activity"] is None
    assert reservation.worker_input["lesson_direction"] is None
