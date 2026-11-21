"""FEAT-066 T-13a: cancel and delete of a Teacher run (FR-C-08), HTTP and repository on PostgreSQL.

SRS l.500 (cancel and delete, purge progress), l.1673-1674 ("Actor của run", "Chủ sở hữu Parent hoặc
Teacher được phân quyền"), UC-07 l.1465, UC-11 l.1513, l.553 (FR-T-14: the CURRENT assignment),
l.864-865 (one 404), l.364, l.593, l.1425 (a suspended or archived class is read-only). Runs only
against a disposable database whose name contains ``be1_acceptance`` and ``frc08_v3_t13a``;
synthetic rows only. The worker half (the purge of a Teacher run) is
``test_t13a_teacher_run_purge_worker_postgres.py``.

The Teacher runs are FIXTURES (the interim storage of T-4a1-DEC-2): ``ORGANIZATION`` + organization
id, ``profile_ref`` = the Managed Profile child id, no lock column. ABANDONED is insertable since
``20261120_vb_0002`` (the plan's note T13A-06 is stale), so it is tested here.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from typing import Any
from uuid import uuid4

import pytest
from fastapi import Header
from fastapi.testclient import TestClient
from sqlalchemy import select, text, update
from sqlalchemy.exc import DBAPIError

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.story_run_actor import RunActor, RunActorKind
from sketch2life.application.ports.story_run_lifecycle import (
    lifecycle_audit_id,
    lifecycle_event_id,
    lifecycle_request_id,
)
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    ClassroomModel,
    ManagedProfileModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
)
from sketch2life.infrastructure.persistence.teacher_run_access import SqlTeacherRunAccess
from sketch2life.infrastructure.story_run_lite import tables as story_tables
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult
from tests.integration.test_t4a1_teacher_run_guard_postgres import (
    ISSUER,
    VOLATILE,
    Api,
    Fixture,
    digest_of,
    run_row,
    seed_run,
    set_assignment,
    set_class_state,
)

CONTENT_WORDS = ("dragon", "synthetic-prompt", "wings")  # content of the seeded runs


@pytest.fixture
def api(monkeypatch: pytest.MonkeyPatch) -> Iterator[Api]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL to a disposable PostgreSQL database")
    database_name = database_url.rsplit("/", 1)[-1]
    if "be1_acceptance" not in database_name or "frc08_v3_t13a" not in database_name:
        pytest.fail("BE1_TEST_DATABASE_URL must be a disposable frc08_v3_t13a*be1_acceptance db")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", database_url)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "development")
    monkeypatch.setenv("SKETCH2LIFE_AI_PROVIDER", "disabled")
    monkeypatch.delenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", raising=False)
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    app = create_app()
    runtime = app.state.be1_runtime
    if runtime.engine is None or runtime.session_factory is None:
        pytest.fail("PostgreSQL runtime did not initialize")
    token = uuid4().hex[:8]
    org, foreign_org = f"org-t13a-{token}", f"org-t13a-foreign-{token}"
    class_a, class_b, class_c = (f"class-{letter}-{token}" for letter in "abc")
    foreign_class = f"class-foreign-{token}"
    child = str(uuid4())
    roles = {
        "parent": "parent",
        "other_parent": "parent",
        "t1": "teacher",  # class A
        "t2": "teacher",  # class B (reassigned to A in one test)
        "t3": "teacher",  # organization-wide teacher row
        "guide": "teacher",
        "observer": "teacher",
        "manager": "school_manager",
        "foreign": "teacher",
        "admin": "platform_admin",
        "idle": "teacher",  # suspended identity with a class A row
    }
    subjects = {name: f"synthetic-t13a-{name}-{token}" for name in roles}
    accounts: dict[str, str] = {}
    with runtime.session_factory.begin() as db:
        for name, role in roles.items():
            identity = AdultIdentityModel(
                subject=subjects[name],
                issuer=ISSUER,
                state="suspended" if name == "idle" else "active",
                account_role=role,
            )
            db.add(identity)
            accounts[name] = identity.account_id
        for organization in (org, foreign_org):
            db.add(OrganizationModel(organization_id=organization, display_name=organization))
        db.flush()
        for class_id, organization in (
            (class_a, org),
            (class_b, org),
            (class_c, org),
            (foreign_class, foreign_org),
        ):
            db.add(
                ClassroomModel(
                    class_id=class_id,
                    organization_id=organization,
                    display_name=class_id,
                    state="active",
                    created_by="fixture",
                )
            )
        db.flush()
        db.add(
            ManagedProfileModel(
                child_id=child,
                organization_id=org,
                class_id=class_a,
                display_name="Synthetic child",
                age_months=72,
                age_source="SYNTHETIC_FIXTURE",
                data_origin="SYNTHETIC_DEV",
                state="active",
                created_by="fixture",
            )
        )
        rows: tuple[tuple[str, str, str | None, str], ...] = (
            ("t1", org, class_a, "teacher"),
            ("t2", org, class_b, "teacher"),
            ("t3", org, None, "teacher"),
            ("guide", org, class_a, "guide"),
            ("observer", org, class_a, "observer"),
            ("manager", org, None, "school_admin"),
            ("foreign", foreign_org, foreign_class, "teacher"),
            ("idle", org, class_a, "teacher"),
        )
        for name, organization, assigned_class, role in rows:
            db.add(
                OrganizationAssignmentModel(
                    assignment_id=str(uuid4()),
                    organization_id=organization,
                    subject=subjects[name],
                    class_id=assigned_class,
                    role=role,
                    active=True,
                )
            )

    async def verified(
        x_test_principal: str = Header(alias="X-Test-Principal"),
    ) -> VerifiedPrincipal:
        return VerifiedPrincipal(subject=x_test_principal, issuer=ISSUER, roles=frozenset())

    app.dependency_overrides[get_verified_adult] = verified
    fixture = Fixture(org, foreign_org, class_a, class_b, class_c, child, child, subjects, accounts)
    try:
        with TestClient(app) as client:
            yield Api(app, client, fixture)
    finally:
        app.dependency_overrides.clear()
        runtime.engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


# ------------------------------------------------------------------------------- the routes
REVISION = 3  # the revision the fixture rows are seeded with


def cancel(
    api: Api,
    run_id: str,
    name: str,
    *,
    key: str | None = "default",
    revision: int = REVISION,
    subject: str | None = None,
) -> Any:
    headers = {"X-Test-Principal": subject or api.fx.subjects[name]}
    if key is not None:
        headers["Idempotency-Key"] = uuid4().hex if key == "default" else key
    return api.client.post(
        f"/v1/story-runs/{run_id}/cancel", json={"expected_revision": revision}, headers=headers
    )


def delete(
    api: Api, run_id: str, name: str, *, key: str | None = "default", subject: str | None = None
) -> Any:
    headers = {"X-Test-Principal": subject or api.fx.subjects[name]}
    if key is not None:
        headers["Idempotency-Key"] = uuid4().hex if key == "default" else key
    return api.client.delete(f"/v1/story-runs/{run_id}", headers=headers)


def wire(response: Any) -> tuple[int, dict[str, Any]]:
    body = response.json()
    return response.status_code, {k: v for k, v in body.items() if k not in VOLATILE}


def rows_of(api: Api, sql: str, **params: Any) -> list[Any]:
    with api.sessions()() as db:
        return list(db.execute(text(sql), params).mappings().all())


def footprint(api: Api, run_id: str) -> dict[str, Any]:
    """Everything a command may write for one run: the row, the receipts, the events, the audit."""

    row = run_row(api, run_id)
    return {
        "run": (row["run_state"], int(row["revision"]), int(row["version"])),
        "receipts": len(
            rows_of(api, "SELECT 1 FROM story.command_receipts WHERE resource_ref = :r", r=run_id)
        ),
        "outbox": len(
            rows_of(api, "SELECT 1 FROM core_outbox_events WHERE aggregate_id = :r", r=run_id)
        ),
        "audit": len(
            rows_of(api, "SELECT 1 FROM core_audit_entries WHERE resource_id = :r", r=run_id)
        ),
        "aggregate": len(
            rows_of(api, "SELECT 1 FROM core_aggregate_revisions WHERE aggregate_id = :r", r=run_id)
        ),
    }


def lesson_rows(api: Api) -> int:
    tables = rows_of(
        api,
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'lesson'",
    )
    return sum(
        int(rows_of(api, f'SELECT count(*) AS n FROM lesson."{t["table_name"]}"')[0]["n"])
        for t in tables
    )


WRONG_ACTORS = (
    "t2",  # a Teacher of another class
    "t3",  # an organization-wide teacher row
    "guide",
    "observer",
    "manager",
    "foreign",  # a Teacher of another organization
    "parent",  # a Parent that does not own a Teacher run
    "other_parent",
    "admin",
    "idle",  # an inactive identity with a class row
)


# ================================================================== the assigned Teacher cancels
def test_the_class_teacher_cancels_and_every_row_is_an_organization_row(api: Api) -> None:
    fx = api.fx
    run_id = seed_run(api, teacher=True, state="INPUT_PROCESSING", understanding=True)
    before = lesson_rows(api)
    response = cancel(api, run_id, "t1", key="t1-cancel")
    assert response.status_code == 202, response.text
    projection = response.json()["lifecycle"]
    assert projection["run_state"] == "DELETE_PENDING"
    assert projection["revision"] == REVISION + 1 and projection["version"] == 4
    assert projection["lifecycle_request_ref"] == lifecycle_request_id(run_id)
    assert projection["purge_state"] == "PENDING"
    row = run_row(api, run_id)
    assert (row["run_state"], int(row["revision"]), int(row["version"])) == (
        "DELETE_PENDING",
        REVISION + 1,
        4,
    )
    # the owner scope of the run and the lock columns are untouched
    assert (row["actor_scope_kind"], row["actor_scope_ref"]) == ("ORGANIZATION", fx.org)
    assert row["active_owner_parent_account_id"] is None
    request_id = lifecycle_request_id(run_id)
    (event,) = rows_of(api, "SELECT * FROM core_outbox_events WHERE aggregate_id = :r", r=run_id)
    assert event["event_id"] == lifecycle_event_id(request_id, "StoryRunCancellationRequestedV1")
    assert (event["organization_id"], event["owner_scope_kind"], event["owner_scope_ref"]) == (
        fx.org,
        "ORGANIZATION",
        fx.org,
    )
    assert event["payload"]["reason_code"] == "TEACHER_CANCEL_REQUESTED"
    assert event["payload"]["actor_ref"] == digest_of(fx.subjects["t1"])
    assert event["status"] == "pending" and int(event["aggregate_revision"]) == REVISION + 1
    (aggregate,) = rows_of(
        api, "SELECT * FROM core_aggregate_revisions WHERE aggregate_id = :r", r=run_id
    )
    assert (aggregate["organization_id"], aggregate["owner_scope_kind"]) == (
        fx.org,
        "ORGANIZATION",
    )
    assert aggregate["owner_scope_ref"] == fx.org and int(aggregate["revision"]) == REVISION + 1
    (audit,) = rows_of(api, "SELECT * FROM core_audit_entries WHERE resource_id = :r", r=run_id)
    assert audit["audit_id"] == lifecycle_audit_id(request_id, "lifecycle.cancel_accepted")
    assert (audit["organization_id"], audit["owner_scope_kind"]) == (fx.org, "ORGANIZATION")
    assert audit["owner_scope_ref"] == fx.org
    assert audit["actor_ref"] == digest_of(fx.subjects["t1"])
    assert audit["decision"] == "accepted:" + request_id
    (receipt,) = rows_of(
        api, "SELECT * FROM story.command_receipts WHERE resource_ref = :r", r=run_id
    )
    assert (receipt["actor_scope_kind"], receipt["actor_scope_ref"]) == (
        "ORGANIZATION",
        digest_of(fx.subjects["t1"]),
    )
    assert receipt["operation"] == "CANCEL_RUN" and receipt["response_status"] == 202
    # no child content in any lifecycle row, and no lesson.* write (D6)
    blob = " ".join(str(v) for r in (event, aggregate, audit, receipt) for v in r.values())
    assert not any(word in blob for word in CONTENT_WORDS)
    assert lesson_rows(api) == before


def test_a_stale_revision_is_409_with_the_current_version_and_writes_nothing(api: Api) -> None:
    run_id = seed_run(api, teacher=True)
    before = footprint(api, run_id)
    response = cancel(api, run_id, "t1", revision=REVISION - 1)
    assert response.status_code == 409
    assert response.json()["code"] == "STALE_REVISION"
    assert response.json()["current_version"] == REVISION
    assert footprint(api, run_id) == before


@pytest.mark.parametrize("state", ["COMPLETED", "FAILED", "ABANDONED"])
def test_the_class_teacher_deletes_a_finished_run(api: Api, state: str) -> None:
    run_id = seed_run(api, teacher=True, state=state)
    response = delete(api, run_id, "t1", key=f"t1-delete-{state}")
    assert response.status_code == 202, response.text
    projection = response.json()["lifecycle"]
    assert projection["run_state"] == "DELETE_PENDING" and projection["purge_state"] == "PENDING"
    (event,) = rows_of(api, "SELECT * FROM core_outbox_events WHERE aggregate_id = :r", r=run_id)
    assert event["event_type"] == "StoryRunDeletedV1"
    assert event["payload"]["reason_code"] == "TEACHER_DELETE_REQUESTED"
    assert event["organization_id"] == api.fx.org
    (receipt,) = rows_of(
        api, "SELECT * FROM story.command_receipts WHERE resource_ref = :r", r=run_id
    )
    assert receipt["operation"] == "DELETE_RUN"


def test_delete_of_a_live_run_and_cancel_of_a_closed_run_are_409(api: Api) -> None:
    live = seed_run(api, teacher=True, state="SCRIPT_REVIEW")
    before = footprint(api, live)
    refused = delete(api, live, "t1")
    assert (refused.status_code, refused.json()["code"]) == (409, "INVALID_STATE_TRANSITION")
    assert footprint(api, live) == before
    done = seed_run(api, teacher=True, state="COMPLETED")
    closed = cancel(api, done, "t1")
    assert (closed.status_code, closed.json()["code"]) == (409, "INVALID_STATE_TRANSITION")
    # a second cancel of a pending run is refused too
    accepted = cancel(api, live, "t1")
    assert accepted.status_code == 202
    again = cancel(api, live, "t1", revision=REVISION + 1)
    assert (again.status_code, again.json()["code"]) == (409, "INVALID_STATE_TRANSITION")


def test_replay_returns_the_stored_202_and_a_key_cannot_move_to_another_run(api: Api) -> None:
    run_id = seed_run(api, teacher=True)
    first = cancel(api, run_id, "t1", key="replay-key")
    second = cancel(api, run_id, "t1", key="replay-key")
    assert first.status_code == second.status_code == 202
    assert wire(first) == wire(second)
    assert footprint(api, run_id)["outbox"] == 1 and footprint(api, run_id)["audit"] == 1
    other = seed_run(api, teacher=True)
    moved = cancel(api, other, "t1", key="replay-key")
    assert (moved.status_code, moved.json()["code"]) == (400, "INVALID_IDEMPOTENCY_KEY")
    # one key under two actors never collides: the receipt carries the principal digest
    shared = seed_run(api, teacher=True)
    assert cancel(api, shared, "t1", key="one-key").status_code == 202


def test_the_key_errors_come_after_the_actor_check(api: Api) -> None:
    run_id = seed_run(api, teacher=True)
    missing = cancel(api, run_id, "t1", key=None)
    assert (missing.status_code, missing.json()["code"]) == (400, "INVALID_REQUEST")
    too_long = delete(api, run_id, "t1", key="k" * 129)
    assert (too_long.status_code, too_long.json()["code"]) == (400, "INVALID_REQUEST")
    # the 400 does not depend on the run (a Teacher of another class gets it too); a caller whose
    # role cannot act on a run at all gets the role guard's 404 first
    assert cancel(api, run_id, "t2", key=None).status_code == 400
    assert cancel(api, run_id, "manager", key=None).status_code == 404
    assert delete(api, run_id, "admin", key=None).status_code == 404


# ======================================================================== every other actor
@pytest.mark.parametrize("command", ["cancel", "delete"])
def test_every_other_actor_gets_the_one_404_and_no_write(api: Api, command: str) -> None:
    state = "SCRIPT_REVIEW" if command == "cancel" else "COMPLETED"
    run_id = seed_run(api, teacher=True, state=state)
    before = footprint(api, run_id)

    def attempt(
        name: str | None = None, *, target: str = run_id, subject: str | None = None
    ) -> Any:
        if command == "cancel":
            return cancel(api, target, name or "t1", subject=subject)
        return delete(api, target, name or "t1", subject=subject)

    unknown = attempt("t1", target=str(uuid4()))
    assert unknown.status_code == 404
    for name in WRONG_ACTORS:
        response = attempt(name)
        assert wire(response) == wire(unknown), name
    # an identity that does not exist at all
    assert wire(attempt(subject="no-such-subject")) == wire(unknown)
    assert footprint(api, run_id) == before
    # a Teacher on a Parent run, and a Parent on its own run (unchanged behaviour)
    parent_run = seed_run(api, teacher=False, state=state)
    parent_before = footprint(api, parent_run)
    assert wire(attempt("t1", target=parent_run)) == wire(unknown)
    assert footprint(api, parent_run) == parent_before
    owner = attempt("parent", target=parent_run)
    assert owner.status_code == 202, owner.text


def test_a_deleted_tombstone_is_404_for_the_teacher(api: Api) -> None:
    gone = seed_run(api, teacher=True, state="DELETED")
    assert cancel(api, gone, "t1").status_code == 404
    assert delete(api, gone, "t1").status_code == 404


# ===================================================================== the assignment is live
def test_a_revoked_teacher_gets_404_and_an_earlier_key_replay_is_404_too(api: Api) -> None:
    run_id = seed_run(api, teacher=True)
    assert cancel(api, run_id, "t1", key="before-revoke").status_code == 202
    other = seed_run(api, teacher=True)
    set_assignment(api, "t1", active=False)
    before = footprint(api, other)
    refused = cancel(api, other, "t1")
    assert refused.status_code == 404 and refused.json()["code"] == "RESOURCE_NOT_FOUND"
    replay = cancel(api, run_id, "t1", key="before-revoke")
    assert replay.status_code == 404  # UC-07 alternate flow: the former Teacher cannot act
    assert footprint(api, other) == before


def test_after_a_reassignment_the_new_teacher_acts_and_the_old_one_cannot(api: Api) -> None:
    run_id = seed_run(api, teacher=True)
    other = seed_run(api, teacher=True, state="COMPLETED")
    with api.sessions().begin() as db:
        db.execute(
            update(OrganizationAssignmentModel)
            .where(
                OrganizationAssignmentModel.subject == api.fx.subjects["t1"],
                OrganizationAssignmentModel.role == "teacher",
            )
            .values(active=False)
        )
        db.add(
            OrganizationAssignmentModel(
                assignment_id=str(uuid4()),
                organization_id=api.fx.org,
                subject=api.fx.subjects["t2"],
                class_id=api.fx.class_a,
                role="teacher",
                active=True,
            )
        )
    assert cancel(api, run_id, "t1").status_code == 404
    assert delete(api, other, "t1").status_code == 404
    accepted = cancel(api, run_id, "t2")
    assert accepted.status_code == 202, accepted.text
    (receipt,) = rows_of(
        api, "SELECT * FROM story.command_receipts WHERE resource_ref = :r", r=run_id
    )
    assert receipt["actor_scope_ref"] == digest_of(api.fx.subjects["t2"])
    assert delete(api, other, "t2").status_code == 202


# ===================================================================== the class state (D7)
@pytest.mark.parametrize("class_state", ["suspended", "archived"])
def test_a_read_only_class_refuses_the_teacher_but_not_the_parent(
    api: Api, class_state: str
) -> None:
    live = seed_run(api, teacher=True, state="SCRIPT_REVIEW")
    done = seed_run(api, teacher=True, state="COMPLETED")
    earlier = seed_run(api, teacher=True, state="SCRIPT_REVIEW")
    assert cancel(api, earlier, "t1", key="before-suspend").status_code == 202
    parent_run = seed_run(api, teacher=False, state="SCRIPT_REVIEW")
    set_class_state(api, api.fx.class_a, class_state)
    try:
        before = (footprint(api, live), footprint(api, done))
        for response in (cancel(api, live, "t1"), delete(api, done, "t1")):
            assert (response.status_code, response.json()["code"]) == (
                409,
                "INVALID_STATE_TRANSITION",
            )
        assert (footprint(api, live), footprint(api, done)) == before
        # the same-key replay of an earlier success is still the stored 202 (l.1697)
        replay = cancel(api, earlier, "t1", key="before-suspend")
        assert replay.status_code == 202
        # a Parent is unaffected: a Parent run is not bound to a class
        assert cancel(api, parent_run, "parent").status_code == 202
    finally:
        set_class_state(api, api.fx.class_a, "active")
    # the class is active again: the same command is accepted
    assert cancel(api, live, "t1").status_code == 202


# ==================================================================== concurrency and locks
def _parallel(count: int, work: Callable[[int], Any]) -> list[Any]:
    barrier = Barrier(count)

    def start(index: int) -> Any:
        barrier.wait()
        return work(index)

    with ThreadPoolExecutor(max_workers=count) as pool:
        return [future.result() for future in [pool.submit(start, i) for i in range(count)]]


def test_two_cancels_with_different_keys_give_one_202_and_one_409(api: Api) -> None:
    run_id = seed_run(api, teacher=True)
    responses = _parallel(2, lambda _i: cancel(api, run_id, "t1"))
    assert sorted(r.status_code for r in responses) == [202, 409]
    loser = next(r for r in responses if r.status_code == 409)
    # both sent the same expected revision, so the loser sees either a stale revision or the state
    assert loser.json()["code"] in {"STALE_REVISION", "INVALID_STATE_TRANSITION"}
    after = footprint(api, run_id)
    assert (after["outbox"], after["audit"], after["receipts"], after["aggregate"]) == (1, 1, 1, 1)
    assert after["run"] == ("DELETE_PENDING", REVISION + 1, 4)


def test_two_cancels_with_one_key_give_two_202_with_one_body(api: Api) -> None:
    run_id = seed_run(api, teacher=True)
    responses = _parallel(2, lambda _i: cancel(api, run_id, "t1", key="shared-key"))
    assert [r.status_code for r in responses] == [202, 202]
    assert wire(responses[0]) == wire(responses[1])
    after = footprint(api, run_id)
    assert (after["outbox"], after["audit"], after["receipts"]) == (1, 1, 1)


def test_a_revoke_waits_behind_a_cancel_that_holds_the_assignment_for_share(api: Api) -> None:
    """``FOR SHARE`` on the assignment row: a revoke cannot slip between the check and the write."""

    run_id = seed_run(api, teacher=True)
    principal = VerifiedPrincipal(api.fx.subjects["t1"], ISSUER, frozenset())
    holder = api.sessions()()
    try:
        repository = SqlParentStoryRunRepository(
            holder,
            actor=RunActor(RunActorKind.TEACHER, api.fx.accounts["t1"]),
            teacher_access=SqlTeacherRunAccess(holder),
        )
        # the first thing every cancel does: the run row FOR UPDATE and the assignment FOR SHARE
        row, access = repository._owned_run_access(
            principal, run_id, lock=True, teacher_capable=True
        )
        assert row["run_id"] == run_id and access is not None and access.writable
        with api.sessions()() as other:
            other.execute(text("SET LOCAL lock_timeout = '500ms'"))
            with pytest.raises(DBAPIError, match="lock"):
                other.execute(
                    update(OrganizationAssignmentModel)
                    .where(
                        OrganizationAssignmentModel.subject == api.fx.subjects["t1"],
                        OrganizationAssignmentModel.role == "teacher",
                    )
                    .values(active=False)
                )
            other.rollback()
    finally:
        holder.rollback()
        holder.close()
    # the transaction ended: the revoke goes through
    set_assignment(api, "t1", active=False)
    assert cancel(api, run_id, "t1").status_code == 404


def test_a_class_suspension_waits_behind_a_cancel_that_holds_the_class_for_share(
    api: Api,
) -> None:
    """``FOR SHARE`` on the class row: no cancel or delete lands after a suspension (T13A-I-01)."""

    run_id = seed_run(api, teacher=True)
    principal = VerifiedPrincipal(api.fx.subjects["t1"], ISSUER, frozenset())
    holder = api.sessions()()
    try:
        repository = SqlParentStoryRunRepository(
            holder,
            actor=RunActor(RunActorKind.TEACHER, api.fx.accounts["t1"]),
            teacher_access=SqlTeacherRunAccess(holder),
        )
        row, access = repository._owned_run_access(
            principal, run_id, lock=True, teacher_capable=True
        )
        assert row["run_id"] == run_id and access is not None and access.writable
        with api.sessions()() as other:
            other.execute(text("SET LOCAL lock_timeout = '500ms'"))
            with pytest.raises(DBAPIError, match="lock"):
                other.execute(
                    update(ClassroomModel)
                    .where(ClassroomModel.class_id == api.fx.class_a)
                    .values(state="suspended")
                )
            other.rollback()
    finally:
        holder.rollback()
        holder.close()
    # the transaction ended: the suspension goes through and the cancel is now refused (409)
    set_class_state(api, api.fx.class_a, "suspended")
    try:
        assert cancel(api, run_id, "t1").status_code == 409
    finally:
        set_class_state(api, api.fx.class_a, "active")
    assert cancel(api, run_id, "t1").status_code == 202


def test_the_run_columns_a_cancel_must_not_touch_stay_as_seeded(api: Api) -> None:
    run_id = seed_run(api, teacher=True, understanding=True, story=True)
    before = run_row(api, run_id)
    assert cancel(api, run_id, "t1").status_code == 202
    after = run_row(api, run_id)
    changed = {k for k in before if before[k] != after[k]}
    assert changed <= {"run_state", "revision", "version", "updated_at"}
    # the content stays until the worker purges it
    assert after["subject_label"] == before["subject_label"]
    assert after["profile_ref"] == before["profile_ref"]


# ============================================================ what a Teacher sees while pending
def test_the_teacher_sees_the_content_free_projection_while_the_purge_is_pending(
    api: Api,
) -> None:
    run_id = seed_run(api, teacher=True, understanding=True)
    assert cancel(api, run_id, "t1", key="pending-key").status_code == 202
    read = api.client.get(
        f"/v1/story-runs/{run_id}", headers={"X-Test-Principal": api.fx.subjects["t1"]}
    )
    assert read.status_code == 200
    projection = read.json()["lifecycle"]
    assert projection["run_state"] == "DELETE_PENDING" and projection["purge_state"] == "PENDING"
    assert not any(word in read.text for word in CONTENT_WORDS)
    assert cancel(api, run_id, "t1", key="pending-key").status_code == 202  # replay
    # a Teacher of another class still gets the 404 on the read
    assert (
        api.client.get(
            f"/v1/story-runs/{run_id}", headers={"X-Test-Principal": api.fx.subjects["t2"]}
        ).status_code
        == 404
    )


def test_the_story_tables_are_selectable_for_the_footprint_helper(api: Api) -> None:
    # guards the helper itself: the receipt table has the resource_ref column the footprint reads
    assert story_tables.story_command_receipts.c.resource_ref is not None
    assert select(story_tables.story_runs.c.run_id) is not None
