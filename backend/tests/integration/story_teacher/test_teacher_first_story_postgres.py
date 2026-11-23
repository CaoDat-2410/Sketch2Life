"""FEAT-066 goal v4 OPEN-A: the Teacher first story starts by itself, on PostgreSQL.

SRS l.394, l.1412 (the first story follows the confirmations; there is no "generate" command),
l.1448 (a run is bound to one approved plan and one pinned activity), l.1666 and l.1668 ("Actor của
run"), l.553 (FR-T-14), l.364, l.593, l.1425 (a suspended class is read-only), l.1413 (a failed
first story), BR-34 (no child name in a stored value). Runs only against a disposable database whose
name contains ``be1_acceptance`` and ``frc08``.

The Teacher run is created through the real T-4b2 route and every step goes through the real
routes; the start is the one ``FirstStoryStarter`` of T-2e-a with its Teacher predicate. The story
generator is a recording double; no provider, no network.
"""

# ruff: noqa: F811  (the imported ``env`` fixture is used as a test argument)

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from typing import Any

from inputs_support import (  # type: ignore[import-not-found]
    Env,
    api,  # noqa: F401 - the T-4b2 fixture, re-exported by the support module
    confirm_context,
    confirm_subject,
    decision_rows,
    env,  # noqa: F401 - fixture
    receipt_rows,
    rewrite,
    run_row,
    states,
    story_rows,
    to_script_review,
    to_subject_review,
    wire,
)
from sqlalchemy import update

from sketch2life.application.ports.parent_story_inputs import StoryGenerationFailure
from sketch2life.infrastructure.lesson_occurrences.tables import OCCURRENCES
from sketch2life.infrastructure.persistence.be1_models import ClassroomModel

SCHEMA_V2 = "sketch2life.story-generation-input.v2"


def _no_child_name(e: Env, text_body: str) -> None:
    assert not any(name in text_body for name in e.d.children.values())


class RefusingGenerator:
    """A composed generator that declares it cannot take a Teacher story (D4)."""

    def __init__(self) -> None:
        self.inputs: list[dict[str, Any]] = []

    def supports_role(self, role: str) -> bool:
        return role != "TEACHER"

    def generate(self, worker_input: Any) -> Any:  # pragma: no cover - must never be called
        self.inputs.append(dict(worker_input))
        raise AssertionError("a Teacher story reached a generator that refuses the role")


# ------------------------------------------------------------------------ the two orders
def test_context_then_subject_starts_the_first_story_exactly_once_with_no_seed(env: Env) -> None:
    e = env
    run_id = to_subject_review(e)
    assert confirm_context(e, "t1", run_id).status_code == 200
    # the context alone is not the last gate: the subject is still to be confirmed
    assert states(e, run_id)[0] == "SUBJECT_REVIEW" and story_rows(e, run_id) == []
    response = confirm_subject(e, "t1", run_id)
    assert response.status_code == 202, response.text
    # the generator answered after the response, job-side: the draft waits for the Teacher
    assert states(e, run_id) == ("SCRIPT_REVIEW", "SUCCEEDED")
    (story,) = story_rows(e, run_id)
    assert story["revision_no"] == 1 and story["status"] == "DRAFT"
    assert len(e.generator.inputs) == 1
    worker = e.generator.inputs[0]
    assert worker["schema_version"] == SCHEMA_V2
    assert worker["role"] == "TEACHER" and worker["activity"] is None
    assert set(worker["lesson_direction"]) == {"teacher_direction", "objectives", "activity_title"}
    assert worker["lesson_direction"]["activity_title"] == "Vẽ bằng ngón tay"
    _no_child_name(e, str(e.generator.inputs))
    # no receipt of its own: the confirmation's receipt is the only one, and no rewrite receipt
    operations = [r["operation"] for r in receipt_rows(e, run_id)]
    assert "GENERATE_STORY_REVISION" not in operations
    assert operations.count("CONFIRM_SUBJECT") == 1 and operations.count("CONFIRM_CONTEXT") == 1


def test_subject_then_context_starts_the_first_story_exactly_once(env: Env) -> None:
    e = env
    run_id = to_subject_review(e)
    assert confirm_subject(e, "t1", run_id).status_code == 202
    # the subject alone is not the last gate: the context is still to be confirmed
    assert states(e, run_id)[0] == "PREPARATION_REVIEW" and story_rows(e, run_id) == []
    assert e.generator.inputs == []
    assert confirm_context(e, "t1", run_id).status_code == 200
    assert states(e, run_id) == ("SCRIPT_REVIEW", "SUCCEEDED")
    assert [r["revision_no"] for r in story_rows(e, run_id)] == [1]
    assert len(e.generator.inputs) == 1 and e.generator.inputs[0]["role"] == "TEACHER"


def test_the_subject_replay_answers_the_same_run_revision_and_starts_nothing_twice(
    env: Env,
) -> None:
    e = env
    run_id = to_subject_review(e)
    assert confirm_context(e, "t1", run_id).status_code == 200
    first = confirm_subject(e, "t1", run_id, key="subject-key-1")
    assert first.status_code == 202
    again = confirm_subject(e, "t1", run_id, key="subject-key-1")
    assert again.status_code == 202 and wire(again)[1] == wire(first)[1]
    assert len(story_rows(e, run_id)) == 1 and len(e.generator.inputs) == 1
    # the 202 and every replay report the command's own run revision (D1), which the stored
    # receipt holds; the run itself has moved on (the start and the generation bumped it)
    (receipt,) = [r for r in receipt_rows(e, run_id) if r["operation"] == "CONFIRM_SUBJECT"]
    assert receipt["response_body"]["run_revision"] == first.json()["run_revision"]
    assert first.json()["run_revision"] < int(run_row(e, run_id)["revision"])


# ------------------------------------------------------------------------ who can start it
def test_a_successor_teacher_after_a_move_can_confirm_and_the_story_starts(env: Env) -> None:
    e = env
    run_id = to_subject_review(e, "t1")
    assert confirm_context(e, "t1", run_id).status_code == 200
    occurrence = run_row(e, run_id)["occurrence_ref"]
    with e.sessions().begin() as db:
        db.execute(
            update(OCCURRENCES)
            .where(OCCURRENCES.c.occurrence_id == occurrence)
            .values(responsible_teacher_ref=e.d.accounts["t4"])
        )
    # the creator is out; the successor gives the last confirmation and the story starts
    assert confirm_subject(e, "t1", run_id).status_code == 404
    assert story_rows(e, run_id) == []
    response = confirm_subject(e, "t4", run_id)
    assert response.status_code == 202, response.text
    assert states(e, run_id) == ("SCRIPT_REVIEW", "SUCCEEDED")
    assert [d["actor_scope_kind"] for d in decision_rows(e, run_id)] == ["ORGANIZATION"]
    assert len(story_rows(e, run_id)) == 1
    # a rewrite by the successor works on the generated first story
    assert rewrite(e, "t4", run_id, revision=1).status_code == 202


def test_a_suspended_class_refuses_the_confirmation_and_starts_nothing(env: Env) -> None:
    e = env
    run_id = to_subject_review(e)
    assert confirm_context(e, "t1", run_id).status_code == 200
    with e.sessions().begin() as db:
        db.execute(
            update(ClassroomModel)
            .where(ClassroomModel.class_id == e.d.classes["a1"])
            .values(state="suspended")
        )
    refused = confirm_subject(e, "t1", run_id)
    assert refused.status_code == 409 and refused.json()["code"] == "INVALID_STATE_TRANSITION"
    assert states(e, run_id)[0] == "SUBJECT_REVIEW"
    assert story_rows(e, run_id) == [] and decision_rows(e, run_id) == []
    assert e.generator.inputs == []


# ------------------------------------------------------------------------ the generator
def test_a_composed_generator_that_refuses_teacher_leaves_the_run_in_review_until_it_changes(
    env: Env,
) -> None:
    e = env
    refusing = RefusingGenerator()
    e.d.app.state.story_generator = refusing
    run_id = to_subject_review(e)
    assert confirm_context(e, "t1", run_id).status_code == 200
    assert confirm_subject(e, "t1", run_id).status_code == 202
    # nothing started: the subject is confirmed, the context is confirmed, no story, no call
    assert states(e, run_id)[0] == "PREPARATION_REVIEW"
    assert story_rows(e, run_id) == [] and refusing.inputs == []
    # the generator is replaced by one that takes the role; a new context-confirmation starts it
    e.d.app.state.story_generator = e.generator
    assert confirm_context(e, "t1", run_id).status_code == 200
    assert states(e, run_id) == ("SCRIPT_REVIEW", "SUCCEEDED")
    assert [r["revision_no"] for r in story_rows(e, run_id)] == [1]
    assert len(e.generator.inputs) == 1


def test_with_no_generator_composed_the_run_waits_in_script_generating(env: Env) -> None:
    e = env
    e.d.app.state.story_generator = None
    run_id = to_subject_review(e)
    assert confirm_context(e, "t1", run_id).status_code == 200
    assert confirm_subject(e, "t1", run_id).status_code == 202
    assert states(e, run_id) == ("SCRIPT_GENERATING", "QUEUED")
    (story,) = story_rows(e, run_id)
    assert story["status"] == "GENERATING" and story["revision_no"] == 1
    assert e.generator.inputs == []


def test_a_known_failure_of_the_first_story_ends_the_run_and_frees_the_teacher_lock(
    env: Env,
) -> None:
    e = env
    e.generator.error = StoryGenerationFailure("PROVIDER_DOWN")
    run_id = to_subject_review(e)
    assert confirm_context(e, "t1", run_id).status_code == 200
    assert confirm_subject(e, "t1", run_id).status_code == 202
    assert states(e, run_id)[0] == "FAILED"
    row = run_row(e, run_id)
    assert row["active_owner_teacher_id"] is None  # the DDL-B2 trigger released the lock
    e.generator.error = None


# ------------------------------------------------------------------------ races and fixtures
def test_two_parallel_last_confirmations_make_exactly_one_story(env: Env) -> None:
    e = env
    run_id = to_subject_review(e)
    barrier = Barrier(2)

    def work(index: int) -> int:
        barrier.wait()
        if index == 0:
            return int(confirm_context(e, "t1", run_id).status_code)
        return int(confirm_subject(e, "t1", run_id).status_code)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(work, range(2)))
    assert sorted(results) == [200, 202], results
    assert [r["revision_no"] for r in story_rows(e, run_id)] == [1]
    assert len(e.generator.inputs) == 1
    assert states(e, run_id) == ("SCRIPT_REVIEW", "SUCCEEDED")


def test_a_generated_first_story_is_a_normal_script_review_run(env: Env) -> None:
    e = env
    run_id = to_script_review(e)
    (story,) = story_rows(e, run_id)
    assert story["status"] == "DRAFT" and story["story_sha256"]
    first = rewrite(e, "t1", run_id, revision=1)
    assert first.status_code == 202
    assert [r["revision_no"] for r in story_rows(e, run_id)] == [1, 2]
