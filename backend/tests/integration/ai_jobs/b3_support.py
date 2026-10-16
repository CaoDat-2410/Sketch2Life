"""Shared PostgreSQL wiring for the BE2-01 Phase B batch B3 tests (synthetic data only).

The service runs on ``SqlAiJobRepository`` with the ASSUMED_CONTRACT owner-fence fixture as
owner ports. Worker capability, clock, queue and audit sink stay fakes: B3 proves the SQL
unit of work and fences, not workers or delivery (batches B4/B5).
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
from alembic import command as alembic_command
from alembic.config import Config
from sketch2life.application.ports.ai_jobs import (
    ArtifactDescriptor,
    AuthorizationAction,
    AuthorizationDecision,
    EligibilityDecision,
    FenceResult,
    Principal,
)
from sketch2life.application.services.ai_jobs import (
    AiJobDependencies,
    AiJobService,
    CreateJobCommand,
)
from sketch2life.domain.ai_jobs.model import AiJob, JobScope, RequestRef
from sketch2life.infrastructure.ai_jobs.fakes import (
    FakeAudit,
    FakeClock,
    FakeQueue,
    FakeWorkerCapability,
)
from sketch2life.infrastructure.ai_jobs.harness import (
    FIXTURE_START,
    JOB_TYPE,
    ORG,
    SESSION,
    SUBJECT,
    TARGET,
    TEACHER,
    TEACHER_2,
    request_ref,
)
from sketch2life.infrastructure.ai_jobs.sql import owner_fence_fixture as fx
from sketch2life.infrastructure.ai_jobs.sql import tables as t
from sketch2life.infrastructure.ai_jobs.sql.repository import (
    SqlAiJobRepository,
    SqlAiJobUnitOfWork,
)
from sketch2life.infrastructure.config.settings import get_core_database_settings
from sqlalchemy import Engine, create_engine, func, select
from sqlalchemy.engine import URL
from sqlalchemy.pool import NullPool

BACKEND = Path(__file__).resolve().parents[3]
ALL_ACTIONS = [str(a) for a in AuthorizationAction]
REQUESTS = ("req_b3_1", "req_b3_2", "req_b3_3")


class UuidIds:
    """Process-safe ids: two processes never mint the same job/attempt id."""

    def new_id(self, prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex}"


class HookedEligibility:
    """Runs ``after(n)`` after the n-th decision is returned: an owner change that lands
    between the precheck and the write transaction."""

    def __init__(self, port: fx.FixtureEligibility, after: Callable[[int], None]) -> None:
        self._port = port
        self._after = after
        self.calls = 0

    def check(
        self, *, scope: JobScope, request_ref: RequestRef, job_type: str
    ) -> EligibilityDecision:
        decision = self._port.check(scope=scope, request_ref=request_ref, job_type=job_type)
        self.calls += 1
        self._after(self.calls)
        return decision


class HookedAuthorization:
    def __init__(
        self, port: fx.FixtureAuthorization, after: Callable[[AuthorizationAction, int], None]
    ) -> None:
        self._port = port
        self._after = after
        self.calls = 0

    def decide(
        self, principal: Principal, action: AuthorizationAction, scope: JobScope
    ) -> AuthorizationDecision:
        decision = self._port.decide(principal, action, scope)
        self.calls += 1
        self._after(action, self.calls)
        return decision


class HookedArtifacts:
    def __init__(self, port: fx.FixtureArtifacts, after: Callable[[str], None]) -> None:
        self._port = port
        self._after = after

    def describe(self, artifact_ref: str) -> ArtifactDescriptor | None:
        descriptor = self._port.describe(artifact_ref)
        self._after(artifact_ref)
        return descriptor

    def quarantine(self, artifact_refs: tuple[str, ...], reason_code: str) -> None:
        self._port.quarantine(artifact_refs, reason_code)


@dataclass
class SqlRig:
    engine: Engine
    owner: fx.OwnerFixture
    repository: SqlAiJobRepository
    service: AiJobService
    deps: AiJobDependencies
    clock: FakeClock
    capabilities: FakeWorkerCapability
    holds: list[FenceResult] = field(default_factory=list)

    def with_ports(self, **changes: Any) -> AiJobService:
        """Same repository/state with replaced owner ports (hooks)."""

        values = {name: getattr(self.deps, name) for name in self.deps.__dataclass_fields__}
        values.update(changes)
        return AiJobService(AiJobDependencies(**values))

    def job(self, job_id: str) -> AiJob:
        with self.repository.transaction() as tx:
            found = tx.get_job(job_id)
        assert found is not None
        return found


def engine_for(url: URL) -> Engine:
    return create_engine(url, poolclass=NullPool, hide_parameters=True)


def build_rig(
    url: URL,
    *,
    on_transaction: Callable[[int], None] | None = None,
    before_commit: Callable[[SqlAiJobUnitOfWork], None] | None = None,
    on_hold: Callable[[FenceResult], None] | None = None,
) -> SqlRig:
    engine = engine_for(url)
    owner = fx.OwnerFixture(engine)
    holds: list[FenceResult] = []

    def observe(result: FenceResult) -> None:
        holds.append(result)
        if on_hold is not None:
            on_hold(result)

    repository = SqlAiJobRepository(
        engine,
        lambda connection: fx.FixtureFenceHold(connection, observe),
        on_transaction=on_transaction,
        before_commit=before_commit,
    )
    clock = FakeClock(FIXTURE_START)
    capabilities = FakeWorkerCapability()
    deps = AiJobDependencies(
        repository=repository,
        authorization=fx.FixtureAuthorization(owner),
        eligibility=fx.FixtureEligibility(owner),
        worker_capability=capabilities,
        clock=clock,
        ids=UuidIds(),
        artifacts=fx.FixtureArtifacts(owner),
        audit=FakeAudit(),
        queue=FakeQueue(),
    )
    return SqlRig(engine, owner, repository, AiJobService(deps), deps, clock, capabilities, holds)


def prepare_database(monkeypatch: pytest.MonkeyPatch, url: URL) -> Iterator[URL]:
    """Disposable database at ``ai_jobs@head`` (the B2 migration, unchanged) plus the
    ASSUMED_CONTRACT fixture schema and synthetic owner decisions."""

    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", url.render_as_string(hide_password=False))
    get_core_database_settings.cache_clear()
    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND / "alembic"))
    alembic_command.upgrade(cfg, "ai_jobs@head")
    engine = engine_for(url)
    with engine.begin() as connection:
        fx.create_fixture_schema(connection)
    seed_owner(fx.OwnerFixture(engine))
    engine.dispose()
    try:
        yield url
    finally:
        get_core_database_settings.cache_clear()


def seed_owner(owner: fx.OwnerFixture) -> None:
    """Synthetic owner state: both teachers hold every action; requests are eligible."""

    for principal in (TEACHER, TEACHER_2):
        owner.set(fx.grant_scope(ORG, principal.principal_id), {"actions": ALL_ACTIONS})
    for request_id in REQUESTS:
        owner.set(fx.eligibility_scope(ORG, request_id), {"eligible": True})


def command(
    *,
    principal: Principal = TEACHER,
    key: str = "idem_b3_001",
    request: str = REQUESTS[0],
    target: str = TARGET,
    purpose: str = "purpose_fx_ai_assistance",
    session_id: str | None = SESSION,
    subjects: tuple[str, ...] = (SUBJECT,),
    job_type: str = JOB_TYPE,
    context: int = 1,
) -> CreateJobCommand:
    return CreateJobCommand(
        principal=principal,
        idempotency_key=key,
        job_type=job_type,
        target_id=target,
        purpose_code=purpose,
        session_id=session_id,
        subject_refs=subjects,
        request_ref=request_ref(request, context=context),
        correlation_id="corr_b3_001",
    )


def counts(engine: Engine) -> dict[str, int]:
    """Row counts per ai_jobs table, with outbox split by kind."""

    with engine.connect() as connection:
        result = {
            name: int(connection.execute(select(func.count()).select_from(table)).scalar_one())
            for name, table in (
                ("job", t.job),
                ("attempt", t.attempt),
                ("semantic_request", t.semantic_request),
                ("command_receipt", t.command_receipt),
                ("completion_receipt", t.completion_receipt),
            )
        }
        for kind in ("dispatch", "audit"):
            result[f"outbox_{kind}"] = int(
                connection.execute(
                    select(func.count()).select_from(t.outbox).where(t.outbox.c.kind == kind)
                ).scalar_one()
            )
    return result


def no_orphans(engine: Engine) -> bool:
    """Every job has exactly one attempt-1 row, one semantic row and one dispatch row, and no
    row of those tables points at a missing job (FKs) or a job without its siblings."""

    with engine.connect() as connection:
        jobs = set(connection.execute(select(t.job.c.job_id)).scalars())
        for table in (t.attempt, t.semantic_request):
            owners = list(connection.execute(select(table.c.job_id)).scalars())
            if sorted(owners) != sorted(jobs):
                return False
        dispatch = list(
            connection.execute(
                select(t.outbox.c.job_id).where(t.outbox.c.kind == "dispatch")
            ).scalars()
        )
        audit_jobs = set(
            connection.execute(
                select(t.outbox.c.job_id).where(t.outbox.c.kind == "audit")
            ).scalars()
        )
        return sorted(dispatch) == sorted(jobs) and audit_jobs <= jobs
