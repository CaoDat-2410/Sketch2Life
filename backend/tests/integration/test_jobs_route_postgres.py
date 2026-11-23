"""FEAT-066 T0.4: ``GET /v1/jobs/{job_id}`` on PostgreSQL (SRS l.779, l.1675, l.865).

Runs only against a disposable database whose name contains ``be1_acceptance`` (migrated to
``heads``). Real identities, organizations, classrooms and assignments; jobs are inserted with the
SQL job repository. The test registry carries one explicit scope rule (the actor holds the class
named by the job target): the production registry has no job type yet, which the last test checks.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest
from fastapi import FastAPI, Header
from fastapi.testclient import TestClient
from sqlalchemy import Engine, func, select, update

from sketch2life.application.job_kinds import (
    ActorMembership,
    JobKindRegistry,
    JobKindSpec,
    JobStatusReader,
    JobTargetKind,
)
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.services.ai_jobs import FIXTURE_RETRY_POLICY
from sketch2life.domain.ai_jobs.model import AiJob, JobScope, create_job, start_attempt
from sketch2life.infrastructure.ai_jobs.harness import request_ref
from sketch2life.infrastructure.ai_jobs.read_only import (
    ReadOnlyFenceHold,
    build_read_only_job_repository,
)
from sketch2life.infrastructure.ai_jobs.sql import tables as t
from sketch2life.infrastructure.ai_jobs.sql.repository import SqlAiJobRepository
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    ClassroomModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult
from sketch2life.interfaces.http.routers.jobs import get_job_status_reader

ISSUER = "synthetic-t04-issuer"
JOB_TYPE = "t04_synthetic_job"
UNREGISTERED_TYPE = "vision_analysis"
KIND = JobTargetKind.LESSON_SKETCH_DECK_REVISION
NOW = datetime(2026, 11, 19, 12, 0, tzinfo=UTC)


def _hold_class(membership: ActorMembership, job: AiJob) -> bool:
    return job.scope.target_id in membership.class_ids


class _FixedClock:
    def now(self) -> datetime:
        return NOW + timedelta(seconds=1)


@dataclass
class T04Api:
    app: FastAPI
    client: TestClient
    engine: Engine
    repository: SqlAiJobRepository
    token: str
    subjects: dict[str, str]
    orgs: dict[str, str]
    classes: dict[str, str]
    jobs: dict[str, str]

    def get(self, who: str, job: str, **headers: str) -> Any:
        return self.client.get(
            f"/v1/jobs/{self.jobs.get(job, job)}",
            headers={"X-Test-Principal": self.subjects[who], **headers},
        )

    def job_state(self) -> list[Any]:
        with self.engine.connect() as connection:
            rows = connection.execute(
                select(t.job.c.job_id, t.job.c.job_revision, t.job.c.state, t.job.c.updated_at)
                .where(t.job.c.job_id.in_(list(self.jobs.values())))
                .order_by(t.job.c.job_id)
            ).all()
        return [tuple(row) for row in rows]

    def row_counts(self) -> dict[str, int]:
        with self.engine.connect() as connection:
            return {
                table.name: int(
                    connection.execute(select(func.count()).select_from(table)).scalar_one()
                )
                for table in (t.job, t.attempt, t.outbox, t.command_receipt)
            }


def _assign(
    db: Any, subject: str, org: str, role: str, class_id: str | None, *, active: bool = True
) -> None:
    db.add(
        OrganizationAssignmentModel(
            assignment_id=str(uuid4()),
            organization_id=org,
            subject=subject,
            class_id=class_id,
            role=role,
            active=active,
        )
    )


def _identity(db: Any, subject: str, role: str, *, state: str = "active") -> None:
    db.add(
        AdultIdentityModel(
            subject=subject,
            account_id=str(uuid4()),
            issuer=ISSUER,
            state=state,
            account_role=role,
            role_revision=1,
        )
    )


def _job(job_id: str, org: str, target: str, job_type: str = JOB_TYPE) -> AiJob:
    return create_job(
        job_id=job_id,
        attempt_id=f"att_{job_id}",
        job_type=job_type,
        scope=JobScope(org, None, (), "purpose_t04", target),
        request_ref=request_ref(f"req_{job_id}"),
        correlation_id=f"corr_{job_id}",
        retry_policy=FIXTURE_RETRY_POLICY,
        now=NOW,
    )


@pytest.fixture
def t04_api(monkeypatch: pytest.MonkeyPatch) -> Iterator[T04Api]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL to a disposable PostgreSQL database")
    if "be1_acceptance" not in database_url.rsplit("/", 1)[-1]:
        pytest.fail("BE1_TEST_DATABASE_URL must point to a disposable *be1_acceptance database")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", database_url)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "development")
    monkeypatch.setenv("SKETCH2LIFE_AI_PROVIDER", "disabled")
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    app = create_app()
    runtime = app.state.be1_runtime
    if runtime.engine is None or runtime.session_factory is None:
        pytest.fail("PostgreSQL runtime did not initialize")
    token = uuid4().hex[:8]
    orgs = {"a": f"t04-{token}-a", "b": f"t04-{token}-b"}
    classes = {
        "a1": f"{token}-a1",
        "a2": f"{token}-a2",
        "a_locked": f"{token}-a3",
        "b1": f"{token}-b1",
    }
    names = (
        "teacher1",
        "teacher2",
        "teacher_two_roles",
        "outsider",
        "manager",
        "observer",
        "inactive_teacher",
        "locked_class_teacher",
        "parent",
        "platform_admin",
        "disabled_teacher",
        "nobody",
    )
    subjects = {name: f"t04-{token}-{name}" for name in names}
    with runtime.session_factory.begin() as db:
        for key, org in orgs.items():
            db.add(OrganizationModel(organization_id=org, display_name=key, state="active"))
        for name, subject in subjects.items():
            if name == "nobody":
                continue
            role = {
                "manager": "school_manager",
                "parent": "parent",
                "platform_admin": "platform_admin",
            }.get(name, "teacher")
            state = "disabled" if name == "disabled_teacher" else "active"
            _identity(db, subject, role, state=state)
        db.flush()
        for key, class_id in classes.items():
            db.add(
                ClassroomModel(
                    class_id=class_id,
                    organization_id=orgs["b"] if key == "b1" else orgs["a"],
                    display_name=key,
                    state="locked" if key == "a_locked" else "active",
                    created_by="synthetic",
                )
            )
        db.flush()
        _assign(db, subjects["teacher1"], orgs["a"], "teacher", classes["a1"])
        _assign(db, subjects["teacher2"], orgs["a"], "teacher", classes["a2"])
        _assign(db, subjects["teacher_two_roles"], orgs["a"], "teacher", classes["a1"])
        _assign(db, subjects["teacher_two_roles"], orgs["a"], "school_admin", None)
        _assign(db, subjects["outsider"], orgs["b"], "teacher", classes["b1"])
        _assign(db, subjects["manager"], orgs["a"], "school_admin", None)
        _assign(db, subjects["observer"], orgs["a"], "observer", classes["a1"])
        _assign(db, subjects["inactive_teacher"], orgs["a"], "teacher", classes["a1"], active=False)
        _assign(db, subjects["locked_class_teacher"], orgs["a"], "teacher", classes["a_locked"])
        _assign(db, subjects["parent"], orgs["a"], "teacher", classes["a1"])  # stray row
        _assign(db, subjects["platform_admin"], orgs["a"], "school_admin", None)
        _assign(db, subjects["disabled_teacher"], orgs["a"], "teacher", classes["a1"])

    repository = SqlAiJobRepository(runtime.engine, lambda _connection: ReadOnlyFenceHold())
    jobs = {
        "a1": f"job_t04_{token}_a1",
        "a2": f"job_t04_{token}_a2",
        "b1": f"job_t04_{token}_b1",
        "a_locked": f"job_t04_{token}_a3",
        "unregistered": f"job_t04_{token}_unreg",
    }
    with repository.transaction() as tx:
        tx.insert_job(_job(jobs["a1"], orgs["a"], classes["a1"]))
        tx.insert_job(_job(jobs["a2"], orgs["a"], classes["a2"]))
        tx.insert_job(_job(jobs["b1"], orgs["b"], classes["b1"]))
        tx.insert_job(_job(jobs["a_locked"], orgs["a"], classes["a_locked"]))
        tx.insert_job(_job(jobs["unregistered"], orgs["a"], classes["a1"], UNREGISTERED_TYPE))

    registry = JobKindRegistry(
        [
            JobKindSpec(
                KIND, (JOB_TYPE,), scope_rule=_hold_class, eligibility=lambda _job: True
            )
        ]
    )
    reader = JobStatusReader(
        build_read_only_job_repository(runtime.engine), registry, _FixedClock()
    )

    async def verified(
        x_test_principal: str = Header(alias="X-Test-Principal"),
    ) -> VerifiedPrincipal:
        return VerifiedPrincipal(subject=x_test_principal, issuer=ISSUER, roles=frozenset())

    app.dependency_overrides[get_verified_adult] = verified
    app.dependency_overrides[get_job_status_reader] = lambda: reader
    try:
        with TestClient(app) as client:
            yield T04Api(
                app, client, runtime.engine, repository, token, subjects, orgs, classes, jobs
            )
    finally:
        app.dependency_overrides.clear()
        runtime.engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def test_teacher_of_the_class_reads_the_job_with_its_target_pair(t04_api: T04Api) -> None:
    api = t04_api
    response = api.get("teacher1", "a1")
    assert response.status_code == 200
    body = response.json()
    assert body["job_id"] == api.jobs["a1"]
    assert body["target_kind"] == "LESSON_SKETCH_DECK_REVISION"
    assert body["target_ref"] == api.classes["a1"]
    assert body["state"] == "queued" and body["poll_after_ms"] == 2000
    assert body["result_refs"] == [] and body["failure"] is None
    assert body["job_revision"] == 1 and body["attempt_number"] == 1
    for hidden in ("organization_id", "attempt_id", "job_type"):
        assert hidden not in body
    assert response.headers["Cache-Control"] == "private, no-cache"
    assert response.headers["ETag"].startswith(f'"job:{api.jobs["a1"]}:1:')


def test_teacher_with_two_roles_reads_through_the_class_rule(t04_api: T04Api) -> None:
    api = t04_api
    assert api.get("teacher_two_roles", "a1").status_code == 200
    assert api.get("teacher_two_roles", "a2").status_code == 404  # org-wide role grants no read


@pytest.mark.parametrize(
    ("who", "job"),
    [
        ("teacher1", "a2"),  # teacher of another class
        ("teacher2", "a1"),
        ("teacher1", "b1"),  # another organization
        ("outsider", "a1"),
        ("manager", "a1"),  # no organization-wide read (SRS l.1675)
        ("observer", "a1"),
        ("inactive_teacher", "a1"),
        ("locked_class_teacher", "a_locked"),  # the loader drops a locked class
        ("parent", "a1"),
        ("platform_admin", "a1"),
        ("disabled_teacher", "a1"),
        ("nobody", "a1"),  # no identity row at all
        ("teacher1", "unregistered"),  # job type that no product kind registered
        ("teacher1", "job_t04_missing"),
    ],
)
def test_denied_reads_share_one_404_shape(t04_api: T04Api, who: str, job: str) -> None:
    api = t04_api
    response = api.get(who, job)
    assert response.status_code == 404
    body = response.json()
    assert body["code"] == "RESOURCE_NOT_FOUND"
    assert body["field_errors"] is None and body["retryable"] is False
    assert "ETag" not in response.headers
    assert api.jobs.get(job, job) not in response.text
    reference = api.get("teacher1", "job_t04_missing").json()
    assert {k: v for k, v in body.items() if k not in {"request_id", "correlation_id"}} == {
        k: v for k, v in reference.items() if k not in {"request_id", "correlation_id"}
    }


def test_conditional_poll_follows_revision_and_current_assignment(t04_api: T04Api) -> None:
    api = t04_api
    first = api.get("teacher1", "a1")
    etag = first.headers["ETag"]
    cached = api.get("teacher1", "a1", **{"If-None-Match": etag})
    assert cached.status_code == 304 and cached.content == b""
    assert cached.headers["ETag"] == etag

    # The job moves (a worker starts it): the old validator no longer matches.
    with api.repository.transaction() as tx:
        job = tx.get_job(api.jobs["a1"])
        assert job is not None
        started = start_attempt(job, job.active_attempt.attempt_id, NOW + timedelta(seconds=1))
        tx.cas_job(expected_revision=job.job_revision, job=started)
    moved = api.get("teacher1", "a1", **{"If-None-Match": etag})
    assert moved.status_code == 200
    assert moved.json()["state"] == "running" and moved.json()["job_revision"] == 2
    assert moved.headers["ETag"] != etag

    # Authorisation first: the same validator after the assignment is switched off is a 404.
    fresh = moved.headers["ETag"]
    assert api.get("teacher1", "a1", **{"If-None-Match": fresh}).status_code == 304
    with api.app.state.be1_runtime.session_factory.begin() as db:
        db.execute(
            update(OrganizationAssignmentModel)
            .where(OrganizationAssignmentModel.subject == api.subjects["teacher1"])
            .values(active=False)
        )
    assert api.get("teacher1", "a1", **{"If-None-Match": fresh}).status_code == 404


def test_reads_never_write(t04_api: T04Api) -> None:
    api = t04_api
    before_state = api.job_state()
    before_counts = api.row_counts()
    for who, job in (
        ("teacher1", "a1"),
        ("teacher1", "a1"),
        ("teacher2", "a1"),
        ("manager", "a1"),
        ("teacher1", "job_t04_missing"),
    ):
        api.get(who, job)
    assert api.job_state() == before_state
    assert api.row_counts() == before_counts


def test_other_methods_do_not_exist(t04_api: T04Api) -> None:
    api = t04_api
    headers = {"X-Test-Principal": api.subjects["teacher1"]}
    for method in ("post", "put", "patch", "delete"):
        response = getattr(api.client, method)(f"/v1/jobs/{api.jobs['a1']}", headers=headers)
        assert response.status_code == 405


def test_production_registry_is_empty_so_the_default_reader_answers_404(
    t04_api: T04Api,
) -> None:
    """HEAD wiring: the lazily built reader uses the read-only SQL repository and the default
    registry, which has no job type; an existing job is still the uniform 404."""

    api = t04_api
    api.app.dependency_overrides.pop(get_job_status_reader)
    assert getattr(api.app.state, "job_status_reader", None) is None
    before = api.row_counts()
    response = api.get("teacher1", "a1")
    assert response.status_code == 404 and response.json()["code"] == "RESOURCE_NOT_FOUND"
    assert api.app.state.job_status_reader is not None  # built on first use, then reused
    assert api.get("teacher1", "a1").status_code == 404
    assert api.row_counts() == before
