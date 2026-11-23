"""FEAT-066 T-13a: the FR-C-08 purge of a Teacher run on PostgreSQL and the local S3Mock.

The worker half of T-13a (the HTTP half is ``test_t13a_teacher_run_lifecycle_postgres.py``). A
Teacher cancel or delete is accepted by the product code (the repository with a Teacher actor) and
the BE1 lifecycle consumer then drains the ``ORGANIZATION`` outbox event: upload, AI Jobs notice,
Core assets, Story content, ``DELETED``. SRS l.500, UC-07 l.1471, UC-11 l.1522-1525.

Owner-run style, like ``test_frc08_lifecycle_postgres.py``: it refuses to run unless the database
and the object store match the explicit ``FRC08_*`` allow-list of
``tools/run_be1_lifecycle_consumer.py`` AND carry the task tag (database ``frc08_v3_t13a``, bucket
``frc08-v3-t13a``). Without ``FRC08_DATABASE_URL`` the module is skipped (NOT_RUN, never PASS).
Synthetic rows only. The Teacher runs and their assets are FIXTURES (interim storage of
T-4a1-DEC-2); the asset keys must stay under ``parent/<run>/`` with version 1 and the scope
``(ORGANIZATION, organization)`` (decision D5, hand-off H3 to T-4b2).
"""

from __future__ import annotations

import os
import re
from collections.abc import Iterator
from dataclasses import dataclass
from io import BytesIO
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest

from tools.local_s3mock_target import check_s3mock_target
from tools.run_be1_lifecycle_consumer import TargetRefused, build_consumer, load_targets

if not os.environ.get("FRC08_DATABASE_URL"):
    pytest.skip("NOT_RUN: owner-run only (FRC08_DATABASE_URL is not set)", allow_module_level=True)

from sqlalchemy import text  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from sketch2life.application.ports.identity import VerifiedPrincipal  # noqa: E402
from sketch2life.application.ports.parent_story_runs import ParentStoryRunError  # noqa: E402
from sketch2life.application.ports.story_run_actor import RunActor, RunActorKind  # noqa: E402
from sketch2life.infrastructure.persistence.be1_models import (  # noqa: E402
    AdultIdentityModel,
    ClassroomModel,
    ManagedProfileModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.infrastructure.persistence.core_models import (  # noqa: E402
    CoreAssetMetadataModel,
)
from sketch2life.infrastructure.persistence.parent_story_repository import (  # noqa: E402
    SqlParentStoryRunRepository,
)
from sketch2life.infrastructure.persistence.story_lifecycle_store import (  # noqa: E402
    SqlStoryLifecycleStore,
)
from sketch2life.infrastructure.persistence.teacher_run_access import (  # noqa: E402
    SqlTeacherRunAccess,
)
from sketch2life.infrastructure.storage.s3_compatible import (  # noqa: E402
    Boto3S3CompatibleObjectStorage,
)
from tests.integration.test_t4a1_teacher_run_guard_postgres import seed_run  # noqa: E402

ISSUER = "synthetic-t13a-worker-issuer"
PNG = b"\x89PNG\r\n\x1a\n" + b"synthetic-t13a-artwork"
COMPLETED = re.compile(
    r"^lcr1;upload=v:[0-9]+:[0-9a-f]{16}@[0-9a-f]{8};ai=v:[0-9]+:[0-9a-f]{16}@[0-9a-f]{8};"
    r"asset=v:[0-9]+:[0-9a-f]{16}@[0-9a-f]{8};story=v:[0-9]+:[0-9a-f]{16}@[0-9a-f]{8};"
    r"sha256=[0-9a-f]{64}(;orph=[0-9]+)?$"
)


@dataclass
class Target:
    engine: Any
    sessions: sessionmaker[Session]
    storage: Boto3S3CompatibleObjectStorage
    consumer: Any
    story: SqlStoryLifecycleStore
    org: str
    class_id: str
    child: str
    teacher: VerifiedPrincipal
    teacher_account: str


@pytest.fixture(scope="module")
def target() -> Iterator[Target]:
    try:
        targets = load_targets(os.environ, require_storage=True)
        if "frc08_v3_t13a" not in targets.database_name:
            raise TargetRefused("DATABASE_TASK_TAG_MISSING")
        check_s3mock_target(
            str(targets.s3_endpoint), str(targets.s3_bucket), task_tag="v3-t13a", environ=os.environ
        )
    except TargetRefused as refused:
        pytest.fail(f"REFUSED code={refused.code}", pytrace=False)
    consumer, engine = build_consumer(targets, os.environ, worker_id="t13a-test-worker")
    sessions = sessionmaker(engine, expire_on_commit=False, autoflush=False)
    storage = Boto3S3CompatibleObjectStorage(
        bucket=str(targets.s3_bucket),
        endpoint_url=targets.s3_endpoint,
        region_name=os.environ.get("FRC08_S3_REGION", "us-east-1"),
        access_key=os.environ["FRC08_S3_ACCESS_KEY"],
        secret_key=os.environ["FRC08_S3_SECRET_KEY"],
    )
    token = uuid4().hex[:8]
    org, class_id, child = f"org-t13a-w-{token}", f"class-t13a-w-{token}", str(uuid4())
    subject = f"synthetic-t13a-w-teacher-{token}"
    with sessions.begin() as db:
        identity = AdultIdentityModel(
            subject=subject, issuer=ISSUER, state="active", account_role="teacher"
        )
        db.add(identity)
        db.add(OrganizationModel(organization_id=org, display_name=org))
        db.flush()
        db.add(
            ClassroomModel(
                class_id=class_id,
                organization_id=org,
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
                class_id=class_id,
                display_name="Synthetic child",
                age_months=72,
                age_source="SYNTHETIC_FIXTURE",
                data_origin="SYNTHETIC_DEV",
                state="active",
                created_by="fixture",
            )
        )
        db.add(
            OrganizationAssignmentModel(
                assignment_id=str(uuid4()),
                organization_id=org,
                subject=subject,
                class_id=class_id,
                role="teacher",
                active=True,
            )
        )
        account = identity.account_id
    try:
        yield Target(
            engine,
            sessions,
            storage,
            consumer,
            SqlStoryLifecycleStore(sessions),
            org,
            class_id,
            child,
            VerifiedPrincipal(subject, ISSUER, frozenset()),
            account,
        )
    finally:
        engine.dispose()


# ------------------------------------------------------------------------------- fixtures
def _seed(t: Target, **kwargs: Any) -> str:
    stub = SimpleNamespace(
        fx=SimpleNamespace(org=t.org, child=t.child, subjects={}), sessions=lambda: t.sessions
    )
    return seed_run(stub, teacher=True, **kwargs)  # type: ignore[arg-type]


def _asset(t: Target, run_id: str, *, key: str | None = None, version: int = 1) -> str:
    """One Teacher asset: an object and its Core row, scope ``(ORGANIZATION, org)``."""

    asset_key = key or f"parent/{run_id}/{uuid4().hex}/original"
    t.storage.put_object(
        asset_key, BytesIO(PNG), content_type="image/png", content_length=len(PNG), metadata={}
    )
    with t.sessions.begin() as db:
        db.add(
            CoreAssetMetadataModel(
                asset_ref=asset_key,
                asset_version=version,
                organization_id=t.org,
                owner_scope_kind="ORGANIZATION",
                owner_scope_ref=t.org,
                content_sha256="a" * 64,
                media_type="image/png",
                source_refs=[run_id],
                derived_from_ref=None,
            )
        )
    return asset_key


def _teacher_repository(t: Target, session: Session) -> SqlParentStoryRunRepository:
    return SqlParentStoryRunRepository(
        session,
        actor=RunActor(RunActorKind.TEACHER, t.teacher_account),
        teacher_access=SqlTeacherRunAccess(session),
    )


def _cancel(t: Target, run_id: str, *, revision: int = 3) -> None:
    with t.sessions() as session:
        record = _teacher_repository(t, session).cancel_run(
            principal=t.teacher,
            run_id=run_id,
            expected_revision=revision,
            idempotency_key=f"cancel-{uuid4().hex}",
        )
    assert record.run_state == "DELETE_PENDING"


def _delete(t: Target, run_id: str) -> None:
    with t.sessions() as session:
        record = _teacher_repository(t, session).delete_run(
            principal=t.teacher, run_id=run_id, idempotency_key=f"delete-{uuid4().hex}"
        )
    assert record.run_state == "DELETE_PENDING"


def _drain(t: Target) -> list[str]:
    outcomes = []
    for _ in range(40):
        outcome = t.consumer.run_once()
        if outcome is None:
            break
        outcomes.append(outcome)
    return outcomes


def _rows(t: Target, sql: str, **params: Any) -> list[Any]:
    with t.engine.connect() as connection:
        return list(connection.execute(text(sql), params).mappings().all())


def _objects(t: Target, run_id: str) -> list[str]:
    listing = t.storage._client.list_objects_v2(
        Bucket=os.environ["FRC08_S3_BUCKET"], Prefix=f"parent/{run_id}/"
    )
    return [item["Key"] for item in listing.get("Contents", [])]


def _request(t: Target, run_id: str) -> Any:
    request_id = _rows(
        t,
        "SELECT request_id FROM be1_data_lifecycle_requests WHERE target_ref = :target",
        target=f"story_run:{run_id}",
    )
    assert len(request_id) == 1
    return _rows(
        t,
        "SELECT * FROM be1_data_lifecycle_requests WHERE request_id = :r",
        r=request_id[0]["request_id"],
    )[0]


# ===================================================================== the purge to DELETED
@pytest.mark.parametrize("command", ["cancel", "delete"])
def test_a_teacher_command_is_purged_to_deleted_with_organization_rows(
    target: Target, command: str
) -> None:
    t = target
    state = "SCRIPT_REVIEW" if command == "cancel" else "COMPLETED"
    run_id = _seed(t, state=state, understanding=True, story=True, confirmed_context=True)
    keys = [_asset(t, run_id), _asset(t, run_id)]
    assert sorted(_objects(t, run_id)) == sorted(keys)
    _cancel(t, run_id) if command == "cancel" else _delete(t, run_id)
    (event,) = _rows(t, "SELECT * FROM core_outbox_events WHERE aggregate_id = :r", r=run_id)
    assert event["owner_scope_kind"] == "ORGANIZATION" and event["organization_id"] == t.org

    outcomes = _drain(t)
    assert "completed" in outcomes, outcomes
    run = _rows(t, "SELECT * FROM story.runs WHERE run_id = :r", r=run_id)[0]
    assert run["run_state"] == "DELETED" and run["profile_ref"] is None
    assert run["subject_label"] is None and run["current_input_revision"] is None
    assert (run["actor_scope_kind"], run["actor_scope_ref"]) == ("ORGANIZATION", t.org)
    for table in ("run_inputs", "story_revisions", "understanding_revisions", "review_decisions"):
        assert _rows(t, f"SELECT 1 FROM story.{table} WHERE run_id = :r", r=run_id) == [], table
    # the objects and the Core rows of the run are gone
    assert _objects(t, run_id) == []
    assert _rows(t, "SELECT 1 FROM core_asset_metadata WHERE asset_ref = ANY(:k)", k=keys) == []

    # the BE1 receipt: the assertions that replace the missing ORGANIZATION CHECK (T13A-09)
    request = _request(t, run_id)
    assert request["state"] == "completed" and request["unresolved_items"] == 0
    assert request["completed_at"] is not None
    assert COMPLETED.fullmatch(str(request["result_ref"])), request["result_ref"]
    assert (request["organization_id"], request["owner_scope_kind"]) == (t.org, "ORGANIZATION")
    assert request["owner_scope_ref"] == t.org and request["request_type"] == "delete"

    # the AI Jobs notice: organization scope, the run, applied_count 0, no job selector
    (notice,) = _rows(
        t,
        "SELECT * FROM ai_jobs.cancellation_notice WHERE notice_id = :n",
        n=f"lifecycle:{request['request_id']}",
    )
    assert (notice["organization_id"], notice["owner_scope_kind"]) == (t.org, "ORGANIZATION")
    assert notice["owner_scope_ref"] == t.org and notice["story_run_ref"] == run_id
    assert notice["applied_count"] == 0 and notice["status"] == "COMPLETE"
    assert notice["reason_code"] == "TEACHER_STORY_RUN_DELETED"
    assert (notice["session_id"], notice["job_type"], notice["subject_ref"]) == (None, None, None)

    # the audit trail and the aggregate carry the organization; no exception row
    audits = _rows(t, "SELECT * FROM core_audit_entries WHERE resource_id = :r", r=run_id)
    assert {a["action"] for a in audits} == {
        "lifecycle.cancel_accepted",
        "lifecycle.completed",
    } or {a["action"] for a in audits} == {"lifecycle.delete_accepted", "lifecycle.completed"}
    assert all(
        (a["organization_id"], a["owner_scope_kind"], a["owner_scope_ref"])
        == (t.org, "ORGANIZATION", t.org)
        for a in audits
    )
    (aggregate,) = _rows(
        t, "SELECT * FROM core_aggregate_revisions WHERE aggregate_id = :r", r=run_id
    )
    assert (aggregate["organization_id"], aggregate["owner_scope_kind"]) == (t.org, "ORGANIZATION")
    assert int(aggregate["revision"]) == int(run["revision"])
    (delivered,) = _rows(
        t, "SELECT status FROM core_outbox_events WHERE aggregate_id = :r", r=run_id
    )
    assert delivered["status"] == "delivered"
    # a second pass finds nothing
    assert _drain(t) == []


def test_a_teacher_asset_outside_the_run_prefix_is_retained_never_silently_deleted(
    target: Target,
) -> None:
    t = target
    run_id = _seed(t, state="SCRIPT_REVIEW", understanding=True)
    inside = _asset(t, run_id)
    outside = _asset(t, run_id, key=f"teacher/{run_id}/{uuid4().hex}/original")
    _cancel(t, run_id)
    outcomes = _drain(t)
    assert "completed" not in outcomes, outcomes
    request = _request(t, run_id)
    assert request["state"] == "exception"
    # all or nothing: no object and no row of the plan was removed
    assert _rows(
        t,
        "SELECT asset_ref FROM core_asset_metadata WHERE asset_ref = ANY(:k)",
        k=[inside, outside],
    )
    listing = t.storage._client.list_objects_v2(
        Bucket=os.environ["FRC08_S3_BUCKET"], Prefix=f"teacher/{run_id}/"
    )
    assert [item["Key"] for item in listing.get("Contents", [])] == [outside]
    assert inside in _objects(t, run_id)
    run = _rows(t, "SELECT run_state FROM story.runs WHERE run_id = :r", r=run_id)[0]
    assert run["run_state"] == "DELETE_PENDING"  # never DELETED while an asset is retained
    # the Story step already cleared the child link, so the Teacher (whose access follows the
    # child's class) gets the 404 here; only the BE1 receipt shows the exception (OWNER-VISIBLE)
    with t.sessions() as session, pytest.raises(ParentStoryRunError) as gone:
        _teacher_repository(t, session).get_run(principal=t.teacher, run_id=run_id)
    assert (gone.value.status_code, gone.value.code) == (404, "RESOURCE_NOT_FOUND")
    (audit,) = _rows(
        t,
        "SELECT * FROM core_audit_entries "
        "WHERE resource_id = :r AND action = 'lifecycle.exception'",
        r=run_id,
    )
    assert (audit["organization_id"], audit["owner_scope_kind"]) == (t.org, "ORGANIZATION")


def test_the_reconciler_gives_a_teacher_delete_pending_run_its_event_and_the_worker_purges_it(
    target: Target,
) -> None:
    t = target
    run_id = _seed(t, state="DELETE_PENDING", understanding=True)
    key = _asset(t, run_id)
    assert run_id in t.story.delete_pending_runs_without_event(limit=5000)
    assert t.story.insert_reconciliation_event(run_id) is True
    assert t.story.insert_reconciliation_event(run_id) is False  # insert-if-absent
    (event,) = _rows(t, "SELECT * FROM core_outbox_events WHERE aggregate_id = :r", r=run_id)
    assert (event["organization_id"], event["owner_scope_kind"], event["owner_scope_ref"]) == (
        t.org,
        "ORGANIZATION",
        t.org,
    )
    assert event["payload"]["reason_code"] == "PRE_EXISTING_DELETE_PENDING"
    assert "completed" in _drain(t)
    assert (
        _rows(t, "SELECT run_state FROM story.runs WHERE run_id = :r", r=run_id)[0]["run_state"]
        == "DELETED"
    )
    assert _rows(t, "SELECT 1 FROM core_asset_metadata WHERE asset_ref = :k", k=key) == []
    assert run_id not in t.story.delete_pending_runs_without_event(limit=5000)


def test_the_worker_state_read_covers_both_scopes_and_nothing_else(target: Target) -> None:
    t = target
    run_id = _seed(t, state="DELETE_PENDING")
    assert t.story.lifecycle_state(run_id) == "DELETE_PENDING"
    assert t.story.lifecycle_state(str(uuid4())) is None


# ------------------------------------------------- hand-offs to T-4b2 / T-4b3a / T-4b3b (H1-H3)
@pytest.mark.skip(
    reason="H1 is closed by T-4b2 (DDL-B2): the release trigger frees the Teacher lock on every "
    "terminal state; proved in test_teacher_run_create_postgres.py (the cancel included)"
)
def test_h1_the_teacher_lock_is_released_by_the_cancel() -> None:  # pragma: no cover
    ...


@pytest.mark.skip(
    reason="H2 is a verified no-op (T-4b3a): no Parent or Teacher producer of the input routes "
    "writes an ai_jobs row (the producers are background tasks of the Story tables), so the notice "
    "has nothing to match; proved in story_teacher/test_teacher_run_inputs_postgres.py (zero "
    "ai_jobs rows across the whole Teacher flow); the video producer is T-4b3b"
)
def test_h2_the_notice_cancels_the_jobs_whose_subject_is_the_run() -> None:  # pragma: no cover
    ...


@pytest.mark.skip(
    reason="H3 is closed for the inputs by T-4b3a: real Teacher run assets and upload sessions "
    "use (ORGANIZATION, org, org), parent/<run>/, v1; proved by the agent-runnable purge-closure "
    "test in story_teacher/test_teacher_run_inputs_postgres.py (plan review P2-2); this owner-run "
    "module keeps its own seeded-asset purge tests; the video output asset is T-4b3b"
)
def test_h3_real_teacher_run_assets_follow_the_purge_key_contract() -> None:  # pragma: no cover
    ...
