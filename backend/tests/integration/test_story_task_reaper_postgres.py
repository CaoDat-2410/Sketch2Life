"""FEAT-066 T-2d-fix: a failed rewrite does not end the run; the lost-task reaper (PostgreSQL).

SRS l.394 (``SCRIPT_GENERATING`` back to ``SCRIPT_REVIEW``, the adult wait starts when the AI job
fails), l.615 and l.988 (the 6 h AI job deadline, safe codes), l.866
(``STORY_REWRITE_LIMIT_REACHED``), l.1413 (a first story out of retries ends the run), l.278
(BR-34: metadata only). Runs only against a disposable database whose name contains
``be1_acceptance`` and ``frc08_v3_t2d`` (the fixture and the builders are the T-2d module's).
The runs are seeded straight into the Story tables or made through the real routes; no object
storage, no provider: the generators are test doubles. The reaper is called as a function with an
injected clock; nothing schedules it.
"""

# ruff: noqa: F811  (the imported T-2d ``api`` fixture is used as a test argument)

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from threading import Barrier
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import select, text, update

from sketch2life.application.ports.parent_story_inputs import (
    StoryGenerationFailure,
    StoryGenerationOutcomeUnknown,
    StoryGenerationResult,
)
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryRevisionReservation,
    ParentStoryRunError,
)
from sketch2life.application.ports.story_task_reaper import (
    REAPER_ACTOR_REF,
    ReapCandidate,
    ReapKind,
    ReapOutcome,
    ReapReport,
)
from sketch2life.application.services.story_output import normalize_story_output
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
)
from sketch2life.infrastructure.persistence.story_task_reaper_store import (
    SqlStoryTaskReaperStore,
    build_story_task_reaper,
)
from sketch2life.infrastructure.story_run_lite import tables as story_tables
from sketch2life.infrastructure.story_video.closeout_store import build_story_run_closeout
from sketch2life.infrastructure.uploads.resolvers import parent_scope_ref
from tests.integration.test_parent_story_rewrites_postgres import (  # noqa: F401
    RecordingGenerator,
    RewriteApi,
    api,
    cancel,
    code_of,
    compose_generator,
    headers,
    principal_of,
    receipt_rows,
    rewrite,
    run_row,
    seed_run,
    states,
    story_rows,
    story_run,
    subject_route,
    wire,
)
from tests.unit.test_story_output import valid_story

AUDIT = CoreAuditEntryModel.__table__
RUNS = story_tables.story_runs
LEASE = timedelta(minutes=30)
SECOND = timedelta(seconds=1)
# The injected clock sits in 2020, far before any real timestamp, so a row another test left
# behind (real timestamps) is never due, and a row this test ages to ``T0`` is.
T0 = datetime(2020, 6, 1, 8, 0, tzinfo=UTC)
TIMEOUT = "PROVIDER_TIMEOUT"


@pytest.fixture(autouse=True)
def _forget_aged_rows(api: RewriteApi) -> None:
    """Rows an earlier test aged to the injected clock are made current (out of reach)."""
    with api.sessions().begin() as db:
        db.execute(
            update(RUNS)
            .where(RUNS.c.updated_at < datetime(2021, 1, 1, tzinfo=UTC))
            .values(updated_at=datetime.now(UTC))
        )
        db.execute(
            update(story_tables.transcript_revisions)
            .where(
                story_tables.transcript_revisions.c.created_at < datetime(2021, 1, 1, tzinfo=UTC)
            )
            .values(created_at=datetime.now(UTC))
        )


# ----------------------------------------------------------------------------- doubles
class Scripted:
    """A story generator that answers with the next scripted behaviour, then with a draft."""

    def __init__(self, *behaviours: Exception | None) -> None:
        self.behaviours = list(behaviours)
        self.calls = 0

    def generate(self, worker_input: Any) -> StoryGenerationResult:
        self.calls += 1
        behaviour = self.behaviours.pop(0) if self.behaviours else None
        if behaviour is not None:
            raise behaviour
        story = valid_story()
        story["title"] = f"Rồng nhỏ lần {self.calls}"
        return StoryGenerationResult(story, f"call-{self.calls}", "fixture-model", "1")


FAIL = StoryGenerationFailure()
UNKNOWN = StoryGenerationOutcomeUnknown()


# ----------------------------------------------------------------------------- helpers
def reserve(
    api: RewriteApi, run_id: str, *, revision: int, key: str | None = None
) -> ParentStoryRevisionReservation:
    """The reservation the route makes, without the runner (a lost background task)."""
    with api.sessions()() as db:
        outcome = SqlParentStoryRunRepository(db).reserve_story_rewrite(
            principal=principal_of(api.parent),
            run_id=run_id,
            idempotency_key=key or uuid4().hex,
            expected_story_revision=revision,
            expected_story_sha256=None,
            hint=None,
            story_revision_id=str(uuid4()),
            model_id="story-generator-port",
            model_revision="unassigned",
            prompt_version="parent-story-rewrite.v1",
            instruction_version="rewrite-neutral.v1",
            instruction="synthetic instruction",
        )
    assert outcome.reservation is not None
    return outcome.reservation


def start(api: RewriteApi, run_id: str, reservation: ParentStoryRevisionReservation) -> None:
    with api.sessions()() as db:
        assert SqlParentStoryRunRepository(db).start_story_generation(
            principal=principal_of(api.parent),
            run_id=run_id,
            story_revision_id=reservation.story_revision_id,
        )


def set_clock(api: RewriteApi, run_id: str, when: datetime) -> None:
    with api.sessions().begin() as db:
        db.execute(update(RUNS).where(RUNS.c.run_id == run_id).values(updated_at=when))


def reap(api: RewriteApi, now: datetime, **kwargs: Any) -> ReapReport:
    lease = kwargs.pop("lease", LEASE)
    lock_timeout_ms = kwargs.pop("lock_timeout_ms", None)
    with api.sessions()() as db:
        if lock_timeout_ms is not None:
            # a regression to a plain ``FOR UPDATE`` then fails fast instead of waiting forever
            db.execute(text(f"SET lock_timeout = {int(lock_timeout_ms)}"))
        try:
            return build_story_task_reaper(db).run_once(lease=lease, now=now, **kwargs)
        finally:
            if lock_timeout_ms is not None:
                db.rollback()
                db.execute(text("RESET lock_timeout"))
                db.commit()


def audit_rows(api: RewriteApi, run_id: str) -> list[Any]:
    with api.sessions()() as db:
        return list(
            db.execute(
                select(AUDIT).where(AUDIT.c.resource_id == run_id).order_by(AUDIT.c.created_at)
            )
            .mappings()
            .all()
        )


def snapshot(api: RewriteApi, run_id: str) -> tuple[Any, ...]:
    """Everything a failed or late write could change: the run row, the stories, the receipts."""
    table = story_tables.story_command_receipts
    with api.sessions()() as db:
        receipts = db.execute(
            select(table.c.receipt_id, table.c.state, table.c.response_status).where(
                table.c.resource_ref == run_id
            )
        ).all()
    return (
        dict(run_row(api, run_id)),
        [
            (row["revision_no"], row["status"], row["story_revision_id"])
            for row in story_rows(api, run_id)
        ],
        sorted(tuple(row) for row in receipts),
    )


def fail_known(api: RewriteApi, reservation: ParentStoryRevisionReservation, **kw: Any) -> None:
    with api.sessions()() as db:
        SqlParentStoryRunRepository(db).fail_story_revision(
            principal=principal_of(api.parent),
            reservation=reservation,
            error_code="STORY_GENERATION_UNAVAILABLE",
            outcome_unknown=bool(kw.get("unknown", False)),
        )


def complete(api: RewriteApi, reservation: ParentStoryRevisionReservation) -> None:
    story, digest = normalize_story_output(valid_story(), confirmed_subject="dragon")
    with api.sessions()() as db:
        SqlParentStoryRunRepository(db).complete_story_revision(
            reservation=reservation,
            principal=principal_of(api.parent),
            story=story,
            story_sha256=digest,
            provider_call_id="late-call",
            model_id="m",
            model_revision="r",
        )


def refused(call: Any) -> str:
    try:
        call()
    except ParentStoryRunError as exc:
        assert exc.status_code == 409
        return exc.code
    raise AssertionError("the late write was accepted")


def confirm_story(api: RewriteApi, run_id: str) -> Any:
    latest = story_rows(api, run_id)[-1]
    return api.client.post(
        f"/v1/story-runs/{run_id}/script-confirmation",
        json={"expected_revision": latest["revision_no"], "story_sha256": latest["story_sha256"]},
        headers=headers(api.parent, uuid4().hex),
    )


def get_view(api: RewriteApi, run_id: str) -> Any:
    with api.sessions()() as db:
        return SqlParentStoryRunRepository(db).get_run(
            principal=principal_of(api.parent), run_id=run_id
        )


# ============================================================================ D1: the recovery
def test_a_failed_rewrite_returns_to_the_previous_story_and_the_retry_reuses_the_number(
    api: RewriteApi,
) -> None:
    run_id = story_run(api)
    first = story_rows(api, run_id)[0]
    api.app.state.story_generator = Scripted(FAIL)
    response = rewrite(api, api.parent, run_id, revision=1, key="failing-key")
    assert response.status_code == 202 and response.json()["story_revision_no"] == 2
    # the run is back in review with the previous story intact and a safe, retryable failure
    assert states(api, run_id) == ("SCRIPT_REVIEW", "FAILED")
    row = run_row(api, run_id)
    assert row["error_code"] == "STORY_GENERATION_UNAVAILABLE" and row["retryable"] is True
    assert row["active_owner_parent_account_id"] is not None and row["finished_at"] is None
    rows = story_rows(api, run_id)
    assert [(r["revision_no"], r["status"]) for r in rows] == [(1, "DRAFT")]
    assert rows[0]["story_revision_id"] == first["story_revision_id"]
    assert rows[0]["story_sha256"] == first["story_sha256"]
    view = get_view(api, run_id)
    assert (view.run_state, view.job_state, view.retryable, view.error_code) == (
        "SCRIPT_REVIEW",
        "FAILED",
        True,
        "STORY_GENERATION_UNAVAILABLE",
    )
    assert (view.story_revision_no, view.story_status) == (1, "DRAFT")
    assert view.story_content is not None
    detail = api.client.get(f"/v1/story-runs/{run_id}", headers=headers(api.parent))
    assert detail.status_code == 200
    # the stored 202 of the failed key replays as it was (its revision id is dangling by design)
    again = rewrite(api, api.parent, run_id, revision=1, key="failing-key")
    assert wire(again) == wire(response)
    assert story_rows(api, run_id)[0]["revision_no"] == 1 and len(story_rows(api, run_id)) == 1
    # the retry has a new key and is the same slot: number 2 again, then the story arrives
    retry = rewrite(api, api.parent, run_id, revision=1)
    assert retry.status_code == 202 and retry.json()["story_revision_no"] == 2
    assert states(api, run_id) == ("SCRIPT_REVIEW", "SUCCEEDED")
    row = run_row(api, run_id)
    assert row["error_code"] is None and row["retryable"] is False
    assert [(r["revision_no"], r["status"]) for r in story_rows(api, run_id)] == [
        (1, "SUPERSEDED"),
        (2, "DRAFT"),
    ]


def test_an_invalid_draft_and_an_unknown_outcome_take_the_documented_paths(
    api: RewriteApi,
) -> None:
    class Broken(Scripted):
        def generate(self, worker_input: Any) -> StoryGenerationResult:
            return StoryGenerationResult({"title": "x"}, "call-x", "fixture-model", "1")

    run_id = story_run(api)
    api.app.state.story_generator = Broken()
    assert rewrite(api, api.parent, run_id, revision=1).status_code == 202
    assert states(api, run_id) == ("SCRIPT_REVIEW", "FAILED")
    assert run_row(api, run_id)["error_code"] == "STORY_OUTPUT_INVALID"
    assert [r["status"] for r in story_rows(api, run_id)] == ["DRAFT"]
    # an unknown outcome keeps the attempt for reconciliation and the run does not return
    api.app.state.story_generator = Scripted(UNKNOWN)
    assert rewrite(api, api.parent, run_id, revision=1).status_code == 202
    assert states(api, run_id) == ("SCRIPT_GENERATION_UNKNOWN", "AWAITING_RECONCILIATION")
    assert [r["status"] for r in story_rows(api, run_id)] == ["DRAFT", "AWAITING_RECONCILIATION"]
    assert run_row(api, run_id)["active_owner_parent_account_id"] is not None


def test_three_failed_attempts_use_up_the_slot_and_the_fourth_is_the_limit(
    api: RewriteApi,
) -> None:
    run_id = story_run(api)
    generator = Scripted(FAIL, FAIL, FAIL)
    api.app.state.story_generator = generator
    for attempt, retryable in ((1, True), (2, True), (3, False)):
        response = rewrite(api, api.parent, run_id, revision=1)
        assert response.status_code == 202 and response.json()["story_revision_no"] == 2
        assert states(api, run_id) == ("SCRIPT_REVIEW", "FAILED")
        assert run_row(api, run_id)["retryable"] is retryable, attempt
        assert len(receipt_rows(api, run_id, "GENERATE_STORY_REVISION")) == attempt + 1
    fourth = rewrite(api, api.parent, run_id, revision=1)
    assert fourth.status_code == 409 and code_of(fourth) == "STORY_REWRITE_LIMIT_REACHED"
    assert generator.calls == 3 and [r["status"] for r in story_rows(api, run_id)] == ["DRAFT"]
    # the adult keeps the story: confirm it. The failure fields do not outlive the confirmation
    confirmed = confirm_story(api, run_id)
    assert confirmed.status_code == 200, confirmed.text
    row = run_row(api, run_id)
    assert (row["run_state"], row["job_state"]) == ("SCRIPT_REVIEW", "SUCCEEDED")
    assert row["retryable"] is False and row["error_code"] is None


def test_a_success_after_two_failures_leaves_the_other_rewrites_untouched(api: RewriteApi) -> None:
    run_id = story_run(api)
    generator = Scripted(FAIL, FAIL)
    api.app.state.story_generator = generator
    for expected, revision in (("FAILED", 1), ("FAILED", 1), ("SUCCEEDED", 1)):
        assert rewrite(api, api.parent, run_id, revision=revision).status_code == 202
        assert states(api, run_id)[1] == expected
    assert [(r["revision_no"], r["status"]) for r in story_rows(api, run_id)] == [
        (1, "SUPERSEDED"),
        (2, "DRAFT"),
    ]
    # slots 3 and 4 are fresh: the earlier failures belong to slot 2 only
    for revision in (2, 3):
        assert rewrite(api, api.parent, run_id, revision=revision).status_code == 202
        assert states(api, run_id) == ("SCRIPT_REVIEW", "SUCCEEDED")
    assert [r["status"] for r in story_rows(api, run_id)] == [
        "SUPERSEDED",
        "SUPERSEDED",
        "SUPERSEDED",
        "DRAFT",
    ]
    limit = rewrite(api, api.parent, run_id, revision=4)
    assert limit.status_code == 409 and code_of(limit) == "STORY_REWRITE_LIMIT_REACHED"
    assert generator.calls == 5


def test_a_failure_leaves_one_content_free_audit_row(api: RewriteApi) -> None:
    run_id = story_run(api)
    api.app.state.story_generator = Scripted(FAIL)
    response = rewrite(api, api.parent, run_id, revision=1, hint="HINT-SENTENCE secret")
    assert response.status_code == 202
    rows = audit_rows(api, run_id)
    assert len(rows) == 1
    row = rows[0]
    assert (row["action"], row["resource_type"], row["resource_id"]) == (
        "STORY_REWRITE_ATTEMPT_FAILED",
        "story_run",
        run_id,
    )
    assert row["decision"] == "STORY_GENERATION_UNAVAILABLE"
    assert row["owner_scope_kind"] == "PARENT_ACCOUNT" and row["organization_id"] is None
    assert row["actor_ref"] == row["owner_scope_ref"] == parent_scope_ref(principal_of(api.parent))
    flat = " ".join(str(value) for value in row.values())
    for forbidden in ("HINT-SENTENCE", "Rồng", "dragon"):
        assert forbidden not in flat


def test_a_first_story_failure_still_ends_the_run_with_the_lock_released(
    api: RewriteApi,
) -> None:
    seeded = seed_run(api, api.parent)
    assert subject_route(api, api.parent, seeded.run_id).status_code == 202
    with api.sessions()() as db:
        reservation = SqlParentStoryRunRepository(db).reserve_story_revision(
            principal=principal_of(api.parent),
            run_id=seeded.run_id,
            expected_understanding_revision=1,
            rewrite_instruction=None,
            idempotency_key=uuid4().hex,
            story_revision_id=str(uuid4()),
            model_id="synthetic-model",
            model_revision="1",
            prompt_version="synthetic-prompt",
        )
    fail_known(api, reservation)
    row = run_row(api, seeded.run_id)
    assert (row["run_state"], row["job_state"], row["retryable"]) == ("FAILED", "FAILED", False)
    assert row["active_owner_parent_account_id"] is None
    assert row["finished_at"] is not None and row["adult_wait_started_at"] is None
    assert [r["status"] for r in story_rows(api, seeded.run_id)] == ["FAILED"]
    legacy = receipt_rows(api, seeded.run_id, "GENERATE_STORY_REVISION")
    assert [(r["state"], r["response_status"]) for r in legacy] == [("FINAL", 502)]
    assert audit_rows(api, seeded.run_id) == []  # a terminal run needs no recovery trace here


def test_a_failed_legacy_rewrite_is_terminal_not_a_return(api: RewriteApi) -> None:
    run_id = story_run(api)
    with api.sessions()() as db:
        reservation = SqlParentStoryRunRepository(db).reserve_story_revision(
            principal=principal_of(api.parent),
            run_id=run_id,
            expected_understanding_revision=1,
            rewrite_instruction="rewrite",
            idempotency_key=uuid4().hex,
            story_revision_id=str(uuid4()),
            model_id="synthetic-model",
            model_revision="1",
            prompt_version="synthetic-prompt",
        )
    assert reservation.receipt_id is not None and reservation.revision_no == 2
    fail_known(api, reservation)
    assert states(api, run_id) == ("FAILED", "FAILED")
    assert [r["status"] for r in story_rows(api, run_id)] == ["SUPERSEDED", "FAILED"]


@pytest.mark.parametrize("unknown", [False, True], ids=["lost", "unknown-outcome"])
def test_a_lost_legacy_rewrite_is_ended_by_the_reaper_not_recovered(
    api: RewriteApi, unknown: bool
) -> None:
    """The reaper's route discriminator: only a ``story-rewrites`` receipt allows a recovery.

    The legacy route supersedes the previous draft when it reserves, so a "recovery" would leave
    ``SCRIPT_REVIEW`` with no reviewable story and a legacy receipt stuck ``PENDING``.
    """
    run_id = story_run(api)
    with api.sessions()() as db:
        reservation = SqlParentStoryRunRepository(db).reserve_story_revision(
            principal=principal_of(api.parent),
            run_id=run_id,
            expected_understanding_revision=1,
            rewrite_instruction="rewrite",
            idempotency_key=uuid4().hex,
            story_revision_id=str(uuid4()),
            model_id="synthetic-model",
            model_revision="1",
            prompt_version="synthetic-prompt",
        )
    assert reservation.receipt_id is not None and reservation.revision_no == 2
    assert [r["status"] for r in story_rows(api, run_id)] == ["SUPERSEDED", "GENERATING"]
    if unknown:
        fail_known(api, reservation, unknown=True)
        assert states(api, run_id) == ("SCRIPT_GENERATION_UNKNOWN", "AWAITING_RECONCILIATION")
        wait, expected_receipt = timedelta(hours=6), ("FINAL", 504)
    else:
        assert states(api, run_id) == ("SCRIPT_GENERATING", "RUNNING")
        wait, expected_receipt = LEASE, ("FINAL", 502)
    set_clock(api, run_id, T0)
    assert reap(api, T0 + wait - SECOND).story_failed == 0
    report = reap(api, T0 + wait)
    assert (report.story_failed, report.rewrite_recovered, report.errors) == (1, 0, 0)
    assert states(api, run_id) == ("FAILED", "FAILED")
    row = run_row(api, run_id)
    assert row["retryable"] is False and row["active_owner_parent_account_id"] is None
    assert [r["status"] for r in story_rows(api, run_id)] == ["SUPERSEDED", "FAILED"]
    legacy = [
        (r["state"], r["response_status"])
        for r in receipt_rows(api, run_id, "GENERATE_STORY_REVISION")
        if r["receipt_id"] == reservation.receipt_id
    ]
    assert legacy == [expected_receipt]
    assert not [
        r for r in receipt_rows(api, run_id, "GENERATE_STORY_REVISION") if r["state"] == "PENDING"
    ]
    assert [r["action"] for r in audit_rows(api, run_id)] == ["STORY_TASK_TIMED_OUT_STORY"]
    assert reap(api, T0 + wait * 2).story_failed == 0


# ============================================================================ late workers
def test_a_late_worker_after_the_reaper_changes_nothing(api: RewriteApi) -> None:
    run_id = story_run(api)
    reservation = reserve(api, run_id, revision=1)
    start(api, run_id, reservation)
    set_clock(api, run_id, T0)
    report = reap(api, T0 + LEASE + SECOND)
    assert report.rewrite_recovered == 1 and report.errors == 0
    assert states(api, run_id) == ("SCRIPT_REVIEW", "FAILED")
    row = run_row(api, run_id)
    assert row["error_code"] == TIMEOUT and row["retryable"] is True
    assert [r["status"] for r in story_rows(api, run_id)] == ["DRAFT"]
    assert row["updated_at"] == T0 + LEASE + SECOND  # the injected instant starts the adult wait
    before = snapshot(api, run_id)
    assert refused(lambda: fail_known(api, reservation)) == "INVALID_STATE_TRANSITION"
    assert refused(lambda: fail_known(api, reservation, unknown=True)) == "INVALID_STATE_TRANSITION"
    assert refused(lambda: complete(api, reservation)) == "INVALID_STATE_TRANSITION"
    with api.sessions()() as db:
        assert (
            SqlParentStoryRunRepository(db).start_story_generation(
                principal=principal_of(api.parent),
                run_id=run_id,
                story_revision_id=reservation.story_revision_id,
            )
            is False
        )
    assert snapshot(api, run_id) == before
    # one audit row, written by the system actor, with the safe code and no content
    rows = audit_rows(api, run_id)
    assert [(r["action"], r["actor_ref"], r["decision"]) for r in rows] == [
        ("STORY_REWRITE_ATTEMPT_FAILED", REAPER_ACTOR_REF, TIMEOUT)
    ]
    assert rows[0]["owner_scope_ref"] == parent_scope_ref(principal_of(api.parent))
    # a second pass finds nothing (idempotent)
    second = reap(api, T0 + LEASE + SECOND)
    assert (second.rewrite_recovered, second.skipped, second.errors) == (0, 0, 0)
    assert len(audit_rows(api, run_id)) == 1


def test_a_late_worker_after_the_unknown_deadline_changes_nothing(api: RewriteApi) -> None:
    run_id = story_run(api)
    reservation = reserve(api, run_id, revision=1)
    start(api, run_id, reservation)
    fail_known(api, reservation, unknown=True)
    assert states(api, run_id) == ("SCRIPT_GENERATION_UNKNOWN", "AWAITING_RECONCILIATION")
    deadline = timedelta(hours=6)
    set_clock(api, run_id, T0)
    # the lease does not apply to an unknown outcome; only the deadline does
    early = reap(api, T0 + deadline - SECOND, lease=LEASE, unknown_deadline=deadline)
    assert early.rewrite_recovered == 0 and states(api, run_id)[0] == "SCRIPT_GENERATION_UNKNOWN"
    assert reap(api, T0 + LEASE * 3, lease=LEASE).rewrite_recovered == 0
    late = reap(api, T0 + deadline + SECOND, lease=LEASE, unknown_deadline=deadline)
    assert late.rewrite_recovered == 1
    assert states(api, run_id) == ("SCRIPT_REVIEW", "FAILED")
    assert [r["status"] for r in story_rows(api, run_id)] == ["DRAFT"]
    before = snapshot(api, run_id)
    assert refused(lambda: fail_known(api, reservation)) == "INVALID_STATE_TRANSITION"
    assert refused(lambda: fail_known(api, reservation, unknown=True)) == "INVALID_STATE_TRANSITION"
    assert refused(lambda: complete(api, reservation)) == "INVALID_STATE_TRANSITION"
    assert snapshot(api, run_id) == before


def test_a_late_failure_of_an_earlier_attempt_does_not_touch_the_new_one(api: RewriteApi) -> None:
    run_id = story_run(api)
    old = reserve(api, run_id, revision=1)
    start(api, run_id, old)
    set_clock(api, run_id, T0)
    assert reap(api, T0 + LEASE + SECOND).rewrite_recovered == 1
    new = reserve(api, run_id, revision=1)  # the adult retries: the same number, a new id
    assert new.revision_no == old.revision_no and new.story_revision_id != old.story_revision_id
    before = snapshot(api, run_id)
    assert states(api, run_id) == ("SCRIPT_GENERATING", "QUEUED")
    assert refused(lambda: fail_known(api, old)) == "INVALID_STATE_TRANSITION"
    assert refused(lambda: fail_known(api, old, unknown=True)) == "INVALID_STATE_TRANSITION"
    # the old id has no row left: the completion is refused by the row guard of T-2d
    assert refused(lambda: complete(api, old)) == "PARENT_STORY_REVISION_NOT_GENERATING"
    assert snapshot(api, run_id) == before
    assert [r["status"] for r in story_rows(api, run_id)] == ["DRAFT", "GENERATING"]
    # the new attempt still completes normally
    complete(api, new)
    assert states(api, run_id) == ("SCRIPT_REVIEW", "SUCCEEDED")
    assert [r["status"] for r in story_rows(api, run_id)] == ["SUPERSEDED", "DRAFT"]


def test_a_first_story_lost_at_the_lease_ends_the_run_and_a_late_worker_cannot_revive_it(
    api: RewriteApi,
) -> None:
    seeded = seed_run(api, api.parent)
    assert subject_route(api, api.parent, seeded.run_id).status_code == 202
    with api.sessions()() as db:
        reservation = SqlParentStoryRunRepository(db).reserve_story_revision(
            principal=principal_of(api.parent),
            run_id=seeded.run_id,
            expected_understanding_revision=1,
            rewrite_instruction=None,
            idempotency_key=uuid4().hex,
            story_revision_id=str(uuid4()),
            model_id="synthetic-model",
            model_revision="1",
            prompt_version="synthetic-prompt",
        )
    run_id = seeded.run_id
    assert states(api, run_id) == ("SCRIPT_GENERATING", "RUNNING")
    pending = receipt_rows(api, run_id, "GENERATE_STORY_REVISION")
    assert [r["state"] for r in pending] == ["PENDING"]
    set_clock(api, run_id, T0)
    assert reap(api, T0 + LEASE - SECOND).story_failed == 0
    report = reap(api, T0 + LEASE)
    assert report.story_failed == 1 and report.rewrite_recovered == 0
    row = run_row(api, run_id)
    assert (row["run_state"], row["job_state"], row["retryable"]) == ("FAILED", "FAILED", False)
    assert row["error_code"] == TIMEOUT and row["active_owner_parent_account_id"] is None
    assert row["finished_at"] == T0 + LEASE and row["adult_wait_started_at"] is None
    assert [r["status"] for r in story_rows(api, run_id)] == ["FAILED"]
    finalised = receipt_rows(api, run_id, "GENERATE_STORY_REVISION")
    assert [(r["state"], r["response_status"]) for r in finalised] == [("FINAL", 502)]
    assert finalised[0]["response_body"] == {"error_code": TIMEOUT}
    assert [r["action"] for r in audit_rows(api, run_id)] == ["STORY_TASK_TIMED_OUT_STORY"]
    before = snapshot(api, run_id)
    assert refused(lambda: fail_known(api, reservation)) == "INVALID_STATE_TRANSITION"
    assert refused(lambda: fail_known(api, reservation, unknown=True)) == "INVALID_STATE_TRANSITION"
    assert refused(lambda: complete(api, reservation)) == "INVALID_STATE_TRANSITION"
    assert snapshot(api, run_id) == before
    assert reap(api, T0 + LEASE).story_failed == 0


def test_an_unknown_first_story_outcome_ends_the_run_at_the_deadline(api: RewriteApi) -> None:
    seeded = seed_run(api, api.parent)
    run_id = seeded.run_id
    assert subject_route(api, api.parent, run_id).status_code == 202
    with api.sessions()() as db:
        reservation = SqlParentStoryRunRepository(db).reserve_story_revision(
            principal=principal_of(api.parent),
            run_id=run_id,
            expected_understanding_revision=1,
            rewrite_instruction=None,
            idempotency_key=uuid4().hex,
            story_revision_id=str(uuid4()),
            model_id="synthetic-model",
            model_revision="1",
            prompt_version="synthetic-prompt",
        )
    fail_known(api, reservation, unknown=True)
    assert states(api, run_id) == ("SCRIPT_GENERATION_UNKNOWN", "AWAITING_RECONCILIATION")
    assert [r["status"] for r in story_rows(api, run_id)] == ["AWAITING_RECONCILIATION"]
    set_clock(api, run_id, T0)
    deadline = timedelta(hours=6)
    assert reap(api, T0 + deadline - SECOND).story_failed == 0
    report = reap(api, T0 + deadline)
    assert report.story_failed == 1 and report.rewrite_recovered == 0
    row = run_row(api, run_id)
    assert (row["run_state"], row["job_state"], row["error_code"]) == ("FAILED", "FAILED", TIMEOUT)
    assert row["active_owner_parent_account_id"] is None and row["finished_at"] == T0 + deadline
    assert [r["status"] for r in story_rows(api, run_id)] == ["FAILED"]
    # the legacy receipt was finalised 504 when the outcome became unknown and is left alone
    receipts = receipt_rows(api, run_id, "GENERATE_STORY_REVISION")
    assert [(r["state"], r["response_status"]) for r in receipts] == [("FINAL", 504)]
    assert [r["action"] for r in audit_rows(api, run_id)] == ["STORY_TASK_TIMED_OUT_STORY"]


# ============================================================================ K1 / K2 / K3
def drawing_run(
    api: RewriteApi,
    *,
    job_state: str,
    understood: bool,
    when: datetime = T0,
    hold_slot: bool = True,
) -> str:
    seeded = seed_run(
        api, api.parent, run_state="INPUT_PROCESSING", job_state=job_state, hold_slot=hold_slot
    )
    run_id = seeded.run_id
    with api.sessions().begin() as db:
        if not understood:
            db.execute(
                story_tables.understanding_revisions.delete().where(
                    story_tables.understanding_revisions.c.run_id == run_id
                )
            )
            db.execute(
                update(RUNS).where(RUNS.c.run_id == run_id).values(understanding_revision=None)
            )
        db.execute(update(RUNS).where(RUNS.c.run_id == run_id).values(updated_at=when))
    return run_id


def add_pending_transcript(api: RewriteApi, run_id: str, when: datetime) -> str:
    inputs = story_tables.run_inputs
    transcript_id = str(uuid4())
    with api.sessions().begin() as db:
        current = (
            db.execute(
                select(inputs).where(inputs.c.run_id == run_id, inputs.c.input_revision == 2)
            )
            .mappings()
            .one()
        )
        voice = f"synthetic/{run_id}/voice"
        db.execute(
            update(inputs)
            .where(inputs.c.run_input_id == current["run_input_id"])
            .values(
                voice_asset_ref=voice,
                voice_asset_version=1,
                voice_duration_ms=5000,
                idea_source="TEXT_AND_VOICE",
            )
        )
        db.execute(
            story_tables.transcript_revisions.insert().values(
                transcript_revision_id=transcript_id,
                run_id=run_id,
                run_input_id=current["run_input_id"],
                source_asset_ref=voice,
                revision_no=1,
                origin="ASR",
                state="PENDING",
                created_at=when,
            )
        )
    return transcript_id


def test_a_lost_first_drawing_analysis_goes_back_to_input_review_at_the_lease(
    api: RewriteApi,
) -> None:
    for job_state in ("QUEUED", "RUNNING"):
        run_id = drawing_run(api, job_state=job_state, understood=False)
        assert reap(api, T0 + LEASE - SECOND).drawing_timed_out == 0
        assert states(api, run_id) == ("INPUT_PROCESSING", job_state)
        report = reap(api, T0 + LEASE)
        assert report.drawing_timed_out == 1 and report.errors == 0
        assert states(api, run_id) == ("INPUT_REVIEW", "FAILED")
        row = run_row(api, run_id)
        assert row["error_code"] == TIMEOUT and row["retryable"] is True
        assert row["updated_at"] == T0 + LEASE and row["revision"] == 6 and row["version"] == 6
        assert row["active_owner_parent_account_id"] is not None and row["finished_at"] is None
        assert [r["action"] for r in audit_rows(api, run_id)] == ["STORY_TASK_TIMED_OUT_DRAWING"]
        # a second pass changes nothing
        assert reap(api, T0 + LEASE).drawing_timed_out == 0
        assert run_row(api, run_id)["revision"] == 6
        # the Parent slot is single: free it for the next loop
        with api.sessions().begin() as db:
            db.execute(
                update(RUNS)
                .where(RUNS.c.run_id == run_id)
                .values(active_owner_parent_account_id=None)
            )


def test_a_lost_rerun_goes_back_to_subject_review_and_keeps_the_earlier_understanding(
    api: RewriteApi,
) -> None:
    run_id = drawing_run(api, job_state="RUNNING", understood=True)
    assert reap(api, T0 + LEASE - SECOND).drawing_timed_out == 0
    assert reap(api, T0 + LEASE + SECOND).drawing_timed_out == 1
    assert states(api, run_id) == ("SUBJECT_REVIEW", "FAILED")
    assert run_row(api, run_id)["understanding_revision"] == 1
    assert get_view(api, run_id).candidate is not None


def test_an_unknown_drawing_outcome_waits_for_the_deadline_not_the_lease(api: RewriteApi) -> None:
    run_id = drawing_run(api, job_state="AWAITING_RECONCILIATION", understood=False)
    deadline = timedelta(hours=6)
    assert reap(api, T0 + deadline - SECOND, lease=LEASE).drawing_timed_out == 0
    assert states(api, run_id)[0] == "INPUT_PROCESSING"
    assert reap(api, T0 + deadline, lease=LEASE).drawing_timed_out == 1
    assert states(api, run_id) == ("INPUT_REVIEW", "FAILED")
    assert run_row(api, run_id)["error_code"] == TIMEOUT


def test_a_late_drawing_result_after_the_reaper_changes_nothing(api: RewriteApi) -> None:
    run_id = drawing_run(api, job_state="RUNNING", understood=False)
    assert reap(api, T0 + LEASE).drawing_timed_out == 1
    before = snapshot(api, run_id)
    principal = principal_of(api.parent)
    with api.sessions()() as db:
        repository = SqlParentStoryRunRepository(db)
        for unknown in (True, False):
            assert (
                refused(
                    lambda unknown=unknown: repository.fail_drawing_analysis(
                        principal=principal,
                        run_id=run_id,
                        error_code="DRAWING_OUTCOME_UNKNOWN",
                        outcome_unknown=unknown,
                        expected_input_revision=2,
                    )
                )
                == "INVALID_STATE_TRANSITION"
            )
        assert (
            repository.fail_drawing_analysis_recoverable(
                principal=principal,
                run_id=run_id,
                error_code="DRAWING_ANALYSIS_FAILED",
                expected_input_revision=2,
            )
            is False
        )
        assert (
            refused(
                lambda: repository.record_understanding(
                    principal=principal,
                    run_id=run_id,
                    result_snapshot={"result": {"candidate_subject": "x"}},
                    candidate_subject="x",
                    confidence=0.5,
                    expected_input_revision=2,
                )
            )
            == "PARENT_STORY_RUN_NOT_AWAITING_UNDERSTANDING"
        )
    assert snapshot(api, run_id) == before


def test_the_legacy_drawing_failure_without_an_input_revision_keeps_its_behaviour(
    api: RewriteApi,
) -> None:
    """The synchronous legacy route (and the G1 gate helper) call it with no fence."""
    principal = principal_of(api.parent)

    def plain_run(job_state: Any) -> str:
        return seed_run(
            api, api.parent, run_state="INPUT_PROCESSING", job_state=job_state, hold_slot=False
        ).run_id

    known = plain_run(None)
    with api.sessions()() as db:
        SqlParentStoryRunRepository(db).fail_drawing_analysis(
            principal=principal,
            run_id=known,
            error_code="MODAL_REQUEST_FAILED",
            outcome_unknown=False,
        )
    row = run_row(api, known)
    assert (row["run_state"], row["job_state"], row["retryable"]) == ("FAILED", "FAILED", False)
    assert row["active_owner_parent_account_id"] is None and row["finished_at"] is not None
    unknown = plain_run(None)
    with api.sessions()() as db:
        SqlParentStoryRunRepository(db).fail_drawing_analysis(
            principal=principal,
            run_id=unknown,
            error_code="MODAL_OUTCOME_UNKNOWN",
            outcome_unknown=True,
        )
    assert states(api, unknown) == ("INPUT_PROCESSING", "AWAITING_RECONCILIATION")
    assert run_row(api, unknown)["finished_at"] is None
    # with the fence, the same call on a run with no analysis in flight is refused
    fenced = plain_run("SUCCEEDED")
    with api.sessions()() as db:
        repository = SqlParentStoryRunRepository(db)
        assert (
            refused(
                lambda: repository.fail_drawing_analysis(
                    principal=principal,
                    run_id=fenced,
                    error_code="X",
                    outcome_unknown=True,
                    expected_input_revision=2,
                )
            )
            == "INVALID_STATE_TRANSITION"
        )


def test_a_late_failure_of_a_job_that_is_no_longer_in_flight_is_refused_too(
    api: RewriteApi,
) -> None:
    """The job-state guard of ``fail_drawing_analysis_recoverable`` and of the unknown writer.

    With a transcript still pending the run stays ``INPUT_PROCESSING`` after the reaper failed its
    drawing job, so the run state alone would not refuse a late worker; the job state does.
    """
    run_id = drawing_run(api, job_state="RUNNING", understood=False)
    add_pending_transcript(api, run_id, T0 + timedelta(hours=1))
    assert reap(api, T0 + LEASE).drawing_timed_out == 1
    assert states(api, run_id) == ("INPUT_PROCESSING", "FAILED")  # the transcript still waits
    before = snapshot(api, run_id)
    principal = principal_of(api.parent)
    with api.sessions()() as db:
        repository = SqlParentStoryRunRepository(db)
        assert (
            repository.fail_drawing_analysis_recoverable(
                principal=principal,
                run_id=run_id,
                error_code="DRAWING_ANALYSIS_FAILED",
                expected_input_revision=2,
            )
            is False
        )
        assert (
            refused(
                lambda: repository.fail_drawing_analysis(
                    principal=principal,
                    run_id=run_id,
                    error_code="DRAWING_OUTCOME_UNKNOWN",
                    outcome_unknown=True,
                    expected_input_revision=2,
                )
            )
            == "INVALID_STATE_TRANSITION"
        )
    assert snapshot(api, run_id) == before


def test_a_late_failure_of_a_replaced_drawing_is_refused_while_the_new_one_runs(
    api: RewriteApi,
) -> None:
    """The ``_drawing_unchanged`` fence of the fenced ``fail_drawing_analysis``.

    A retake (input revision 3, a different drawing) starts a new analysis; the late UNKNOWN
    outcome of the analysis of drawing 2 must not flip the run for the wrong drawing.
    """
    run_id = drawing_run(api, job_state="RUNNING", understood=False)
    inputs = story_tables.run_inputs
    with api.sessions().begin() as db:
        current = (
            db.execute(
                select(inputs).where(inputs.c.run_id == run_id, inputs.c.input_revision == 2)
            )
            .mappings()
            .one()
        )
        token = uuid4().hex
        retake = {key: value for key, value in current.items() if value is not None}
        retake.update(
            run_input_id=str(uuid4()),
            input_revision=3,
            original_asset_ref=f"parent/{run_id}/{token}/original",
            original_sha256="e" * 64,
            derived_asset_ref=f"parent/{run_id}/{token}/normalized.png",
            derived_sha256="f" * 64,
        )
        db.execute(inputs.insert().values(**retake))
        db.execute(update(RUNS).where(RUNS.c.run_id == run_id).values(current_input_revision=3))
    before = snapshot(api, run_id)
    principal = principal_of(api.parent)

    def late(revision: int, *, unknown: bool) -> Any:
        with api.sessions()() as db:
            return SqlParentStoryRunRepository(db).fail_drawing_analysis(
                principal=principal,
                run_id=run_id,
                error_code="DRAWING_OUTCOME_UNKNOWN",
                outcome_unknown=unknown,
                expected_input_revision=revision,
            )

    assert refused(lambda: late(2, unknown=True)) == "INVALID_STATE_TRANSITION"
    assert refused(lambda: late(2, unknown=False)) == "INVALID_STATE_TRANSITION"
    assert snapshot(api, run_id) == before
    # the same call for the current drawing is accepted (the fence refuses only the stale one)
    late(3, unknown=True)
    assert states(api, run_id) == ("INPUT_PROCESSING", "AWAITING_RECONCILIATION")


def test_a_late_understanding_while_a_transcript_waits_is_still_a_legitimate_result(
    api: RewriteApi,
) -> None:
    """Pinned: the run is still ``INPUT_PROCESSING``, so the worker's result is accepted."""
    run_id = drawing_run(api, job_state="RUNNING", understood=False)
    add_pending_transcript(api, run_id, T0 + timedelta(hours=1))
    assert reap(api, T0 + LEASE).drawing_timed_out == 1
    with api.sessions()() as db:
        revision = SqlParentStoryRunRepository(db).record_understanding(
            principal=principal_of(api.parent),
            run_id=run_id,
            result_snapshot={"result": {"candidate_subject": "dragon", "visible_features": ["a"]}},
            candidate_subject="dragon",
            confidence=0.9,
            expected_input_revision=2,
        )
    assert revision == 1 and states(api, run_id) == ("INPUT_PROCESSING", "SUCCEEDED")


def test_a_lost_transcription_fails_the_transcript_and_settles_the_run(api: RewriteApi) -> None:
    # the drawing is understood and its job is done; only the audio still waits for the ASR
    run_id = drawing_run(api, job_state="SUCCEEDED", understood=True, when=T0 + timedelta(hours=9))
    transcript_id = add_pending_transcript(api, run_id, T0)
    assert reap(api, T0 + LEASE - SECOND).transcript_timed_out == 0
    assert run_row(api, run_id)["run_state"] == "INPUT_PROCESSING"
    report = reap(api, T0 + LEASE)
    assert report.transcript_timed_out == 1 and report.errors == 0
    table = story_tables.transcript_revisions
    with api.sessions()() as db:
        transcript = (
            db.execute(select(table).where(table.c.transcript_revision_id == transcript_id))
            .mappings()
            .one()
        )
    assert (transcript["state"], transcript["error_code"]) == ("FAILED", TIMEOUT)
    row = run_row(api, run_id)
    assert row["run_state"] == "INPUT_REVIEW" and row["updated_at"] == T0 + LEASE
    assert [r["action"] for r in audit_rows(api, run_id)] == ["STORY_TASK_TIMED_OUT_TRANSCRIPT"]
    # a late ASR result is refused by the existing compare-and-set on PENDING
    before = snapshot(api, run_id)
    with api.sessions()() as db:
        repository = SqlParentStoryRunRepository(db)
        assert (
            repository.complete_transcript(
                principal=principal_of(api.parent),
                run_id=run_id,
                transcript_revision_id=transcript_id,
                text="late text",
                language="vi",
                model_revision="r",
                config_hash=None,
                asr_profile_ref=None,
                segment_timing=None,
            )
            is False
        )
        assert (
            repository.fail_transcript(
                principal=principal_of(api.parent),
                run_id=run_id,
                transcript_revision_id=transcript_id,
                error_code="ASR_FAILED",
            )
            is False
        )
    assert snapshot(api, run_id) == before
    assert reap(api, T0 + LEASE).transcript_timed_out == 0


# ============================================================================ the reaper's guards
def test_a_lost_rewrite_at_lease_minus_and_plus_one_second(api: RewriteApi) -> None:
    run_id = story_run(api)
    reserve(api, run_id, revision=1)  # QUEUED: no worker was ever composed
    assert states(api, run_id) == ("SCRIPT_GENERATING", "QUEUED")
    set_clock(api, run_id, T0)
    assert reap(api, T0 + LEASE - SECOND).rewrite_recovered == 0
    assert states(api, run_id) == ("SCRIPT_GENERATING", "QUEUED")
    assert reap(api, T0 + LEASE).rewrite_recovered == 1
    assert states(api, run_id) == ("SCRIPT_REVIEW", "FAILED")


def test_a_run_a_live_command_holds_is_skipped_and_picked_up_later(api: RewriteApi) -> None:
    run_id = story_run(api)
    reserve(api, run_id, revision=1)
    set_clock(api, run_id, T0)
    holder = api.sessions()()
    try:
        holder.execute(select(RUNS.c.run_id).where(RUNS.c.run_id == run_id).with_for_update())
        report = reap(api, T0 + LEASE, lock_timeout_ms=2000)
        assert (report.rewrite_recovered, report.skipped, report.errors) == (0, 1, 0)
        assert states(api, run_id) == ("SCRIPT_GENERATING", "QUEUED")
    finally:
        holder.rollback()
        holder.close()
    assert reap(api, T0 + LEASE).rewrite_recovered == 1


def test_a_completed_worker_is_never_reaped(api: RewriteApi) -> None:
    run_id = story_run(api)
    reservation = reserve(api, run_id, revision=1)
    start(api, run_id, reservation)
    set_clock(api, run_id, T0)
    complete(api, reservation)  # the worker wins the race
    report = reap(api, T0 + LEASE * 10)
    assert (report.rewrite_recovered, report.skipped, report.errors) == (0, 0, 0)
    assert states(api, run_id) == ("SCRIPT_REVIEW", "SUCCEEDED")
    assert audit_rows(api, run_id) == []
    # the listed candidate that changed before the lock is skipped, not failed
    with api.sessions()() as db:
        outcome = SqlStoryTaskReaperStore(db).reap(
            ReapCandidate(run_id, ReapKind.STORY_LOST), T0 + LEASE * 10, T0 + LEASE * 9
        )
    assert outcome is ReapOutcome.SKIPPED


@pytest.mark.parametrize(
    "kind",
    [
        ReapKind.DRAWING_LOST,
        ReapKind.DRAWING_UNKNOWN,
        ReapKind.TRANSCRIPT_LOST,
        ReapKind.STORY_LOST,
        ReapKind.STORY_UNKNOWN,
    ],
    ids=lambda kind: kind.name.lower(),
)
def test_a_candidate_that_is_no_longer_due_at_the_lock_is_skipped(
    api: RewriteApi, kind: ReapKind
) -> None:
    """Every clock is re-checked under the run lock: a run that moved after the listing is left."""
    if kind in (ReapKind.STORY_LOST, ReapKind.STORY_UNKNOWN):
        run_id = story_run(api)
        reservation = reserve(api, run_id, revision=1)
        if kind is ReapKind.STORY_UNKNOWN:
            start(api, run_id, reservation)
            fail_known(api, reservation, unknown=True)
        set_clock(api, run_id, T0)
    elif kind is ReapKind.TRANSCRIPT_LOST:
        run_id = drawing_run(api, job_state="SUCCEEDED", understood=True)
        add_pending_transcript(api, run_id, T0)
    else:
        job_state = "RUNNING" if kind is ReapKind.DRAWING_LOST else "AWAITING_RECONCILIATION"
        run_id = drawing_run(api, job_state=job_state, understood=False)
    before = snapshot(api, run_id)
    now = T0 + timedelta(hours=7)

    def reap_directly(cutoff: datetime) -> ReapOutcome:
        with api.sessions()() as db:
            return SqlStoryTaskReaperStore(db).reap(ReapCandidate(run_id, kind), now, cutoff)

    # the clock of the run (or of its transcript) is after the cutoff the caller computed
    assert reap_directly(T0 - SECOND) is ReapOutcome.SKIPPED
    assert snapshot(api, run_id) == before and audit_rows(api, run_id) == []
    if kind is ReapKind.TRANSCRIPT_LOST:
        # the run left ``INPUT_PROCESSING`` after the listing
        with api.sessions().begin() as db:
            db.execute(update(RUNS).where(RUNS.c.run_id == run_id).values(run_state="INPUT_REVIEW"))
        before = snapshot(api, run_id)
        assert reap_directly(T0) is ReapOutcome.SKIPPED
        assert snapshot(api, run_id) == before
        table = story_tables.transcript_revisions
        with api.sessions()() as db:
            assert db.scalar(select(table.c.state).where(table.c.run_id == run_id)) == "PENDING"
    else:
        assert reap_directly(T0) is not ReapOutcome.SKIPPED  # due at the cutoff: the control


def test_two_reapers_leave_one_winner_and_one_audit_row(api: RewriteApi) -> None:
    run_id = story_run(api)
    reserve(api, run_id, revision=1)
    set_clock(api, run_id, T0)
    barrier = Barrier(2)

    def work(_: int) -> ReapOutcome:
        with api.sessions()() as db:
            barrier.wait()
            return SqlStoryTaskReaperStore(db).reap(
                ReapCandidate(run_id, ReapKind.STORY_LOST), T0 + LEASE, T0
            )

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(work, range(2)))
    assert sorted(outcomes) == sorted([ReapOutcome.REWRITE_RECOVERED, ReapOutcome.SKIPPED])
    assert states(api, run_id) == ("SCRIPT_REVIEW", "FAILED")
    assert [r["status"] for r in story_rows(api, run_id)] == ["DRAFT"]
    assert len(audit_rows(api, run_id)) == 1


def test_a_cancelled_run_is_never_touched(api: RewriteApi) -> None:
    run_id = story_run(api)
    reserve(api, run_id, revision=1)
    set_clock(api, run_id, T0)
    assert cancel(api, api.parent, run_id).status_code == 202
    assert states(api, run_id)[0] == "DELETE_PENDING"
    set_clock(api, run_id, T0)
    before = snapshot(api, run_id)
    report = reap(api, T0 + LEASE * 10)
    assert (report.rewrite_recovered, report.skipped, report.errors) == (0, 0, 0)
    with api.sessions()() as db:
        assert (
            SqlStoryTaskReaperStore(db).reap(
                ReapCandidate(run_id, ReapKind.STORY_LOST), T0 + LEASE * 10, T0 + LEASE * 9
            )
            is ReapOutcome.SKIPPED
        )
    assert snapshot(api, run_id) == before
    # the cancel wrote its own lifecycle audit row; the reaper wrote none
    assert [r for r in audit_rows(api, run_id) if r["action"].startswith("STORY_")] == []


def test_a_demo_lane_run_is_never_touched(api: RewriteApi) -> None:
    """StoryRun-lite writes the same table but never sets ``current_input_revision`` (N-02)."""
    run_id = drawing_run(api, job_state="RUNNING", understood=True)
    with api.sessions().begin() as db:
        db.execute(update(RUNS).where(RUNS.c.run_id == run_id).values(current_input_revision=None))
    before = snapshot(api, run_id)
    report = reap(api, T0 + LEASE * 10)
    assert (report.drawing_timed_out, report.skipped, report.errors) == (0, 0, 0)
    with api.sessions()() as db:
        assert (
            SqlStoryTaskReaperStore(db).reap(
                ReapCandidate(run_id, ReapKind.DRAWING_LOST), T0 + LEASE * 10, T0 + LEASE * 9
            )
            is ReapOutcome.SKIPPED
        )
    assert snapshot(api, run_id) == before and audit_rows(api, run_id) == []


def test_an_organization_run_is_never_touched(api: RewriteApi) -> None:
    run_id = drawing_run(api, job_state="RUNNING", understood=False)
    with api.sessions().begin() as db:
        db.execute(
            update(RUNS).where(RUNS.c.run_id == run_id).values(actor_scope_kind="ORGANIZATION")
        )
    before = snapshot(api, run_id)
    assert reap(api, T0 + LEASE * 10).drawing_timed_out == 0
    assert snapshot(api, run_id) == before


def test_the_batch_bounds_one_pass_and_a_second_pass_finishes_the_rest(api: RewriteApi) -> None:
    run_ids = [
        drawing_run(api, job_state="RUNNING", understood=False, hold_slot=False) for _ in range(3)
    ]
    first = reap(api, T0 + LEASE, batch_size=2)
    assert (first.drawing_timed_out, first.errors) == (2, 0)
    second = reap(api, T0 + LEASE, batch_size=2)
    assert (second.drawing_timed_out, second.errors) == (1, 0)
    assert all(states(api, run_id) == ("INPUT_REVIEW", "FAILED") for run_id in run_ids)
    assert reap(api, T0 + LEASE).drawing_timed_out == 0


def test_the_report_and_the_logs_hold_counts_only(api: RewriteApi, caplog: Any) -> None:
    run_id = drawing_run(api, job_state="RUNNING", understood=False)
    with caplog.at_level(logging.DEBUG):
        reap(api, T0 + LEASE)
    text_out = " ".join(record.getMessage() for record in caplog.records)
    assert run_id not in text_out and "INPUT_REVIEW" not in text_out


def test_a_recovered_run_is_not_closed_before_168_hours_from_the_recovery(api: RewriteApi) -> None:
    run_id = story_run(api)
    reserve(api, run_id, revision=1)
    old = T0 - timedelta(hours=400)
    with api.sessions().begin() as db:
        db.execute(
            update(RUNS)
            .where(RUNS.c.run_id == run_id)
            .values(
                updated_at=T0,
                adult_wait_started_at=old,
                last_meaningful_activity_at=old,
            )
        )
    assert reap(api, T0 + LEASE).rewrite_recovered == 1
    recovered_at = T0 + LEASE

    def closeout(now: datetime) -> Any:
        with api.sessions()() as db:
            return build_story_run_closeout(db, None).run_once(now)

    assert closeout(recovered_at + timedelta(hours=167, minutes=59)).abandoned == 0
    assert states(api, run_id)[0] == "SCRIPT_REVIEW"
    assert closeout(recovered_at + timedelta(hours=168, seconds=1)).abandoned == 1
    assert states(api, run_id)[0] == "ABANDONED"


def test_no_text_of_the_story_or_the_hint_reaches_the_audit_or_the_receipts_of_a_recovery(
    api: RewriteApi,
) -> None:
    run_id = story_run(api)
    api.app.state.story_generator = Scripted(FAIL)
    hint = "HINT-SENTENCE zebra"
    assert rewrite(api, api.parent, run_id, revision=1, hint=hint).status_code == 202
    dump = " ".join(str(dict(row)) for row in audit_rows(api, run_id))
    assert hint not in dump and "zebra" not in dump
