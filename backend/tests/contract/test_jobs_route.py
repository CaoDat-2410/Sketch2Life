"""FEAT-066 T0.4: ``GET /v1/jobs/{job_id}`` over the live app (SRS l.779, l.786, l.806, l.1675).

Offline: jobs live in the BE2 in-memory store, the identity row is served by a fake session and
the T0.2 scope loader is replaced by a table of scopes (its SQL is covered in
``tests/integration/test_jobs_route_postgres.py``). The production registry has no job type, so
the tests inject a registry with one explicit scope rule; nothing mutates the module default.
"""

from __future__ import annotations

import ast
import json
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field, replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from sketch2life.application.job_kinds import (
    DEFAULT_JOB_KIND_REGISTRY,
    SRS_JOB_POLL_POLICY,
    ActorMembership,
    JobActor,
    JobKindRegistry,
    JobKindSpec,
    JobStatusReader,
    JobTargetKind,
    NoParentJobs,
    deny_scope,
    withhold_results,
)
from sketch2life.application.ports.ai_jobs import OWNER_FENCE_CONTRACT, PrincipalRole
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.domain.ai_jobs.model import AiJob
from sketch2life.infrastructure.ai_jobs.harness import (
    JOB_TYPE,
    ORG,
    OTHER_ORG,
    FixtureHarness,
    build_fixture_harness,
)
from sketch2life.infrastructure.ai_jobs.read_only import (
    ReadOnlyFenceHold,
    build_read_only_job_repository,
)
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.interfaces.http import account_scope
from sketch2life.interfaces.http.account_scope import (
    GrantedClass,
    GrantedOrganization,
    GrantedScope,
    load_granted_scope,
)
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.routers import ai_jobs as candidate_router
from sketch2life.interfaces.http.routers import jobs as jobs_router
from sketch2life.interfaces.http.routers.jobs import (
    JOB_ID_PATTERN,
    AiJobStatusV1,
    get_job_status_reader,
)

ISSUER = "synthetic-t04-issuer"
SUBJECT = "synthetic-t04-subject-3f9a"
ACCOUNT_ID = "00000000-0000-4000-8000-0000000000a4"
BEARER = {"Authorization": "Bearer synthetic"}
CLASS_ID = "class_fx_001"
TEST_KIND = JobTargetKind.LESSON_SKETCH_DECK_REVISION
UNIFORM_NOT_FOUND = {"code": "RESOURCE_NOT_FOUND", "retryable": False, "field_errors": None}


def class_scope_rule(membership: ActorMembership, job: AiJob) -> bool:
    """Test-only rule (never production): the actor holds the class named by the job target."""

    return job.scope.target_id in membership.class_ids


@dataclass
class Ctx:
    """Mutable per-test state read by the module-wide dependency overrides."""

    harness: FixtureHarness = field(default_factory=build_fixture_harness)
    identity: AdultIdentityModel | None = None
    scopes: dict[str, GrantedScope] = field(default_factory=dict)
    loader_calls: list[str | None] = field(default_factory=list)
    eligible: bool = True
    parent_jobs: Any = field(default_factory=NoParentJobs)

    def reader(self) -> JobStatusReader:
        registry = JobKindRegistry(
            [
                JobKindSpec(
                    TEST_KIND,
                    (JOB_TYPE,),
                    scope_rule=class_scope_rule,
                    eligibility=lambda _job: self.eligible,
                )
            ]
        )
        return JobStatusReader(
            self.harness.store,
            registry,
            self.harness.clock,
            parent_jobs=self.parent_jobs,
        )


class _FakeSession:
    def __init__(self, identity: AdultIdentityModel | None) -> None:
        self._identity = identity

    def get(self, _model: object, _key: object) -> AdultIdentityModel | None:
        return self._identity


class _UnreachableSession:
    """``get_db`` probes with ``SELECT 1``; this session behaves like a database that is down."""

    def execute(self, *_args: object, **_kwargs: object) -> None:
        raise OperationalError("SELECT 1", {}, ConnectionError("down"))

    def rollback(self) -> None:
        return None

    def close(self) -> None:
        return None


def _identity(
    *,
    role: str | None = "teacher",
    state: str = "active",
    issuer: str = ISSUER,
) -> AdultIdentityModel:
    return AdultIdentityModel(
        subject=SUBJECT,
        account_id=ACCOUNT_ID,
        issuer=issuer,
        state=state,
        account_role=role,
        role_revision=1,
    )


def _scope(
    organization: str = ORG,
    roles: tuple[str, ...] = ("teacher",),
    classes: tuple[str, ...] = (CLASS_ID,),
) -> GrantedScope:
    return GrantedScope(
        account_id=ACCOUNT_ID,
        managed="NONE",
        organizations=(GrantedOrganization(organization, "School", roles),),
        classes=tuple(
            GrantedClass(organization, class_id, "Lop", "teacher", "active") for class_id in classes
        ),
    )


@pytest.fixture(autouse=True)
def _offline_settings(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", "0")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", "postgresql+psycopg://localhost:9/t04_closed")
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    yield
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()


@pytest.fixture
def ctx(monkeypatch: pytest.MonkeyPatch) -> Ctx:
    state = Ctx(identity=_identity(), scopes={ORG: _scope()})

    def fake_loader(
        _db: object, _identity: AdultIdentityModel, *, organization_id: str | None = None
    ) -> GrantedScope:
        state.loader_calls.append(organization_id)
        return state.scopes.get(
            organization_id or "", GrantedScope(account_id=ACCOUNT_ID, managed="NONE")
        )

    monkeypatch.setattr(jobs_router, "load_granted_scope", fake_loader)
    return state


def _app(state: Ctx, *, override_db: bool = True) -> FastAPI:
    application = create_app()
    application.dependency_overrides[get_verified_adult] = lambda: VerifiedPrincipal(
        subject=SUBJECT, issuer=ISSUER, roles=frozenset()
    )
    if override_db:
        application.dependency_overrides[get_db] = lambda: _FakeSession(state.identity)
    application.dependency_overrides[get_job_status_reader] = state.reader
    return application


@pytest.fixture
def client(ctx: Ctx) -> Iterator[TestClient]:
    with TestClient(_app(ctx)) as test_client:
        yield test_client


def _succeeded_job(state: Ctx, *, job_type: str = JOB_TYPE) -> str:
    harness = state.harness
    job_id = harness.service.create_job(harness.create(job_type=job_type, target=CLASS_ID)).job_id
    message = harness.start_next()
    harness.service.accept_completion(
        harness.capability(job_id), harness.success_claim(message)
    )
    return job_id


def _queued_job(state: Ctx, *, job_type: str = JOB_TYPE) -> str:
    command = state.harness.create(job_type=job_type, target=CLASS_ID)
    return state.harness.service.create_job(command).job_id


def _get(client: TestClient, job_id: str, **headers: str) -> Any:
    return client.get(f"/v1/jobs/{job_id}", headers={**BEARER, **headers})


def _assert_uniform_404(response: Any, job_id: str) -> dict[str, Any]:
    assert response.status_code == 404
    body = response.json()
    assert {key: body[key] for key in UNIFORM_NOT_FOUND} == UNIFORM_NOT_FOUND
    assert set(body) == {
        "code",
        "message",
        "correlation_id",
        "retryable",
        "retry_after_seconds",
        "field_errors",
        "request_id",
    }
    assert body["request_id"] == body["correlation_id"] == response.headers["X-Request-ID"]
    assert job_id not in response.text
    assert "ETag" not in response.headers
    ignored = {"request_id", "correlation_id"}
    return {key: value for key, value in body.items() if key not in ignored}


# ---------------------------------------------------------------- registry (unit level)
def test_default_registry_has_exactly_the_eight_srs_kinds_and_no_job_type() -> None:
    assert [spec.target_kind.value for spec in DEFAULT_JOB_KIND_REGISTRY.specs] == [
        "STORY_RUN",
        "VIDEO_GENERATION",
        "VIDEO_GENERATION_SCENE",
        "LESSON_SOURCE_DOCUMENT",
        "LESSON_LIBRARY_VERSION",
        "LESSON_VERSION_VISUAL_ASSET",
        "LESSON_SKETCH_DECK_REVISION",
        "PARENT_SKETCH_GUIDE",
    ]
    assert all(spec.job_types == () for spec in DEFAULT_JOB_KIND_REGISTRY.specs)
    assert all(spec.scope_rule is deny_scope for spec in DEFAULT_JOB_KIND_REGISTRY.specs)
    assert all(spec.eligibility is withhold_results for spec in DEFAULT_JOB_KIND_REGISTRY.specs)
    # BE2 pilot / fixture job types are not product kinds.
    for pilot in ("vision_analysis", "sketch_assistance", "sketch_generation"):
        assert DEFAULT_JOB_KIND_REGISTRY.for_job_type(pilot) is None


def test_spec_with_job_types_must_define_its_own_rule_and_eligibility() -> None:
    with pytest.raises(ValueError, match="scope_rule and eligibility"):
        JobKindSpec(TEST_KIND, ("a_type",))
    with pytest.raises(ValueError, match="scope_rule and eligibility"):
        JobKindSpec(TEST_KIND, ("a_type",), scope_rule=class_scope_rule)
    with pytest.raises(ValueError, match="scope_rule and eligibility"):
        JobKindSpec(TEST_KIND, ("a_type",), eligibility=lambda _job: True)
    explicit = JobKindSpec(
        TEST_KIND, ("a_type",), scope_rule=class_scope_rule, eligibility=lambda _job: True
    )
    assert explicit.job_types == ("a_type",)
    with pytest.raises(ValueError, match="distinct"):
        JobKindSpec(
            TEST_KIND, ("x", "x"), scope_rule=class_scope_rule, eligibility=lambda _job: True
        )


def test_registry_rejects_a_job_type_registered_under_two_kinds() -> None:
    def spec(kind: JobTargetKind) -> JobKindSpec:
        return JobKindSpec(
            kind, ("shared",), scope_rule=class_scope_rule, eligibility=lambda _job: True
        )

    with pytest.raises(ValueError, match="registered twice"):
        JobKindRegistry([spec(JobTargetKind.STORY_RUN), spec(JobTargetKind.VIDEO_GENERATION)])
    with pytest.raises(ValueError, match="duplicate spec"):
        JobKindRegistry(
            [JobKindSpec(JobTargetKind.STORY_RUN), JobKindSpec(JobTargetKind.STORY_RUN)]
        )


def test_injected_registry_does_not_touch_the_module_default(ctx: Ctx) -> None:
    ctx.reader()
    assert DEFAULT_JOB_KIND_REGISTRY.for_job_type(JOB_TYPE) is None


def test_poll_policy_is_the_srs_window() -> None:
    assert (SRS_JOB_POLL_POLICY.min_interval_ms, SRS_JOB_POLL_POLICY.max_interval_ms) == (
        2000,
        10000,
    )


def test_job_id_pattern_matches_the_candidate_route() -> None:
    assert candidate_router._ID.pattern == JOB_ID_PATTERN


# ----------------------------------------------------------------------- 401 / 400 / 503
def test_missing_token_is_401_even_with_a_malformed_id(ctx: Ctx) -> None:
    application = create_app()
    application.dependency_overrides[get_job_status_reader] = ctx.reader
    with TestClient(application) as test_client:
        for job_id in ("job_fx0001", "bad id!"):
            response = test_client.get(f"/v1/jobs/{job_id}")
            assert response.status_code == 401
            body = response.json()
            assert body["code"] == "AUTH_REQUIRED"
            assert body["request_id"] == body["correlation_id"]
            assert set(body) >= {"code", "message", "correlation_id", "retryable", "field_errors"}


def test_malformed_id_is_400_invalid_request_with_field_errors(client: TestClient) -> None:
    for job_id in ("bad%20id", "a" * 121, "job$fx"):
        response = _get(client, job_id)
        assert response.status_code == 400, job_id
        body = response.json()
        assert body["code"] == "INVALID_REQUEST"
        assert isinstance(body["field_errors"], list) and body["field_errors"]
        assert body["request_id"] == response.headers["X-Request-ID"]


def test_database_unavailable_is_503_after_authentication(ctx: Ctx) -> None:
    application = create_app()
    application.dependency_overrides[get_job_status_reader] = ctx.reader
    application.state.be1_runtime.session_factory = _UnreachableSession
    with TestClient(application) as test_client:
        denied = test_client.get("/v1/jobs/job_fx0001")
        assert denied.status_code == 401  # authentication wins over the database probe
        application.dependency_overrides[get_verified_adult] = lambda: VerifiedPrincipal(
            subject=SUBJECT, issuer=ISSUER, roles=frozenset()
        )
        response = test_client.get("/v1/jobs/job_fx0001", headers=BEARER)
    assert response.status_code == 503
    assert response.json()["code"] == "DATABASE_UNAVAILABLE"
    assert response.json()["retryable"] is True


# ------------------------------------------------------------------------ uniform 404
def test_missing_out_of_scope_and_unregistered_jobs_share_one_404(
    client: TestClient, ctx: Ctx
) -> None:
    visible = _succeeded_job(ctx)
    assert _get(client, visible).status_code == 200
    ctx.harness.clock.advance(seconds=1)
    unregistered = ctx.harness.service.create_job(
        ctx.harness.create(job_type="vision_analysis", key="idem_fx_002", target="other_target")
    ).job_id
    ctx.scopes[ORG] = _scope(classes=("someone_elses_class",))
    candidates = {
        "missing": "job_fx9999",
        "other_class": visible,
        "unregistered": unregistered,
    }
    bodies = {name: _assert_uniform_404(_get(client, job_id), job_id)
              for name, job_id in candidates.items()}
    assert len({json.dumps(body, sort_keys=True) for body in bodies.values()}) == 1


@pytest.mark.parametrize(
    "case",
    [
        "other_organization",
        "no_membership",
        "observer_role_only",
        "guide_role_only",
        "platform_admin",
        "parent_head_port",
        "no_account_role",
        "disabled_identity",
        "issuer_mismatch",
        "unknown_identity",
    ],
)
def test_every_denied_actor_gets_the_same_404(client: TestClient, ctx: Ctx, case: str) -> None:
    job_id = _succeeded_job(ctx)
    if case == "other_organization":
        ctx.scopes = {OTHER_ORG: _scope(OTHER_ORG)}
    elif case == "no_membership":
        ctx.scopes = {}
    elif case in {"observer_role_only", "guide_role_only"}:
        ctx.scopes[ORG] = _scope(roles=(case.split("_")[0],))
    elif case == "platform_admin":
        ctx.identity = _identity(role="platform_admin")
    elif case == "parent_head_port":
        ctx.identity = _identity(role="parent")
    elif case == "no_account_role":
        ctx.identity = _identity(role=None)
    elif case == "disabled_identity":
        ctx.identity = _identity(state="disabled")
    elif case == "issuer_mismatch":
        ctx.identity = _identity(issuer="another-issuer")
    else:
        ctx.identity = None
    missing = _assert_uniform_404(_get(client, "job_fx9999"), "job_fx9999")
    assert _assert_uniform_404(_get(client, job_id), job_id) == missing


def test_membership_is_read_for_the_organization_of_the_stored_job(
    client: TestClient, ctx: Ctx
) -> None:
    job_id = _succeeded_job(ctx)
    assert _get(client, job_id).status_code == 200
    assert ctx.loader_calls == [ORG]  # one narrow read, never the whole account scope
    ctx.loader_calls.clear()
    assert _get(client, "job_fx9999").status_code == 404
    assert ctx.loader_calls == []  # nothing about the actor is read for a missing job


def test_truncated_membership_fails_closed_with_the_uniform_404(
    client: TestClient, ctx: Ctx
) -> None:
    """Review R1 F-3: a capped class list may be incomplete, so the route does not guess."""

    job_id = _succeeded_job(ctx)
    assert _get(client, job_id).status_code == 200
    ctx.scopes[ORG] = GrantedScope(
        account_id=ACCOUNT_ID,
        managed="NONE",
        organizations=_scope().organizations,
        classes=_scope().classes,
        truncated=True,
    )
    _assert_uniform_404(_get(client, job_id), job_id)


def test_stored_value_outside_the_public_patterns_is_a_safe_500(
    ctx: Ctx, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Review R1 F-4: a row that breaks the public contract never becomes a bare traceback."""

    job_id = _succeeded_job(ctx)
    real_reader = ctx.reader()
    leak = "https://storage.example.invalid/bucket/object?sig=secret"

    class BadRefReader:
        def read(self, actor: Any, requested: str, if_none_match: str | None = None) -> Any:
            read = real_reader.read(actor, requested, if_none_match)
            view = dict(read.status.view or {})
            view["result_refs"] = [{"artifact_ref": leak, "sha256": "0" * 64}]
            return replace(read, status=replace(read.status, view=view))

    application = _app(ctx)
    application.dependency_overrides[get_job_status_reader] = BadRefReader
    with TestClient(application, raise_server_exceptions=False) as strict_client:
        response = _get(strict_client, job_id)
    assert response.status_code == 500
    body = response.json()
    assert body["code"] == "INTERNAL_SERVER_ERROR"
    assert set(body) >= {"code", "message", "correlation_id", "retryable", "field_errors"}
    assert leak not in response.text and "secret" not in response.text


def test_school_manager_has_no_organization_wide_read(client: TestClient, ctx: Ctx) -> None:
    """SRS l.1675 limits the read to the actor of the run; l.1602 gives no run-content read."""

    job_id = _succeeded_job(ctx)
    ctx.identity = _identity(role="school_manager")
    ctx.scopes[ORG] = _scope(roles=("school_admin",), classes=())
    _assert_uniform_404(_get(client, job_id), job_id)
    # Even the manager who also holds the class gets no result refs (ADMIN projection).
    ctx.scopes[ORG] = _scope(roles=("school_admin",))
    response = _get(client, job_id)
    assert response.status_code == 200
    assert response.json()["result_refs"] == []


# ---------------------------------------------------------------------------- 200 shape
def test_teacher_of_the_class_gets_the_status_with_target_pair_and_headers(
    client: TestClient, ctx: Ctx
) -> None:
    job_id = _succeeded_job(ctx)
    response = _get(client, job_id, **{"X-Request-ID": "req-t04-1"})
    assert response.status_code == 200
    body = response.json()
    model = AiJobStatusV1.model_validate(body)
    assert model.target_kind is TEST_KIND
    assert model.target_ref == CLASS_ID
    assert body["target_kind"] == "LESSON_SKETCH_DECK_REVISION"
    assert model.job_id == job_id and model.state == "succeeded"
    assert model.result_disposition == "accepted" and model.poll_after_ms is None
    assert model.job_revision >= 2 and model.attempt_number == 1
    assert len(model.result_refs) == 1
    assert set(body) == set(AiJobStatusV1.model_fields)
    for hidden in ("organization_id", "attempt_id", "job_type", "request_ref", "detail"):
        assert hidden not in body
    assert "://" not in response.text
    assert body["created_at"].endswith("Z") and body["updated_at"].endswith("Z")
    assert response.headers["ETag"].startswith(f'"job:{job_id}:{model.job_revision}:')
    assert response.headers["Cache-Control"] == "private, no-cache"
    assert "Authorization" in response.headers["Vary"]


def test_queued_job_reports_the_srs_poll_window(client: TestClient, ctx: Ctx) -> None:
    job_id = _queued_job(ctx)
    first = _get(client, job_id).json()
    assert first["state"] == "queued" and first["poll_after_ms"] == 2000
    assert first["progress"] == {"kind": "unknown", "value": None, "stage_label": None}
    ctx.harness.clock.advance(seconds=3600)
    assert _get(client, job_id).json()["poll_after_ms"] == 10000


def test_result_refs_follow_the_kind_eligibility(client: TestClient, ctx: Ctx) -> None:
    job_id = _succeeded_job(ctx)
    ctx.eligible = False
    withheld = _get(client, job_id)
    assert withheld.status_code == 200 and withheld.json()["result_refs"] == []
    ctx.eligible = True
    exposed = _get(client, job_id)
    assert len(exposed.json()["result_refs"]) == 1
    assert exposed.headers["ETag"] != withheld.headers["ETag"]


def test_failed_job_carries_a_safe_failure_only(client: TestClient, ctx: Ctx) -> None:
    harness = ctx.harness
    job_id = harness.service.create_job(harness.create(target=CLASS_ID)).job_id
    message = harness.start_next()
    harness.service.accept_completion(
        harness.capability(job_id),
        harness.failure_claim(message, code="PROVIDER_UNAVAILABLE", retryable=False,
                              diagnostic="Traceback at /srv/provider/secret.py line 3"),
    )
    body = _get(client, job_id).json()
    assert body["state"] == "failed_exhausted"
    assert set(body["failure"]) == {"code", "retryable", "public_message", "attempts_remaining"}
    assert "Traceback" not in json.dumps(body) and "/srv/" not in json.dumps(body)


# --------------------------------------------------------------------------- 304 / ETag
def test_conditional_poll_is_304_only_while_authorised_and_unchanged(
    client: TestClient, ctx: Ctx
) -> None:
    job_id = _succeeded_job(ctx)
    etag = _get(client, job_id).headers["ETag"]
    for header in (etag, f"W/{etag}", f'"other", {etag}', f'W/"other" , W/{etag}'):
        cached = _get(client, job_id, **{"If-None-Match": header})
        assert cached.status_code == 304, header
        assert cached.content == b""
        assert cached.headers["ETag"] == etag
        assert cached.headers["Cache-Control"] == "private, no-cache"
    stale = _get(client, job_id, **{"If-None-Match": '"job:other:1:abcd1234"'})
    assert stale.status_code == 200
    # Authorisation comes first: once the class is gone the same header is a 404, never a 304.
    ctx.scopes[ORG] = _scope(classes=())
    _assert_uniform_404(_get(client, job_id, **{"If-None-Match": etag}), job_id)
    ctx.scopes = {}
    _assert_uniform_404(_get(client, job_id, **{"If-None-Match": etag}), job_id)


def test_etag_moves_with_the_job_revision(client: TestClient, ctx: Ctx) -> None:
    job_id = _queued_job(ctx)
    queued = _get(client, job_id)
    ctx.harness.start_next()
    running = _get(client, job_id, **{"If-None-Match": queued.headers["ETag"]})
    assert running.status_code == 200 and running.json()["state"] == "running"
    assert running.headers["ETag"] != queued.headers["ETag"]
    assert running.json()["job_revision"] > queued.json()["job_revision"]


# ----------------------------------------------------------------------- read-only surface
@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_only_get_exists_on_the_job_path(client: TestClient, ctx: Ctx, method: str) -> None:
    job_id = _succeeded_job(ctx)
    response = getattr(client, method)(f"/v1/jobs/{job_id}", headers=BEARER)
    assert response.status_code == 405
    for suffix in ("completion", "cancel", "retry"):
        assert client.post(f"/v1/jobs/{job_id}/{suffix}", headers=BEARER).status_code == 404


def test_reading_does_not_change_the_job(client: TestClient, ctx: Ctx) -> None:
    job_id = _succeeded_job(ctx)
    before = ctx.harness.store.snapshot()
    for _ in range(3):
        assert _get(client, job_id).status_code == 200
    after = ctx.harness.store.snapshot()
    assert after.jobs[job_id] == before.jobs[job_id]
    assert len(after.jobs) == len(before.jobs)


# ------------------------------------------------------------------------- Parent seam
def test_parent_seam_is_closed_at_head_and_opens_only_through_the_port(
    client: TestClient, ctx: Ctx
) -> None:
    job_id = _succeeded_job(ctx)
    job = ctx.harness.store.snapshot().jobs[job_id]
    ctx.identity = _identity(role="parent")
    _assert_uniform_404(_get(client, job_id), job_id)  # HEAD port owns nothing

    class OwnsJob:
        def __init__(self) -> None:
            self.asked: list[tuple[str, str]] = []

        def owned_job(self, actor: JobActor, requested: str) -> AiJob | None:
            # T-1a: the port receives the actor (account id and the Parent story scope ref).
            assert actor.story_scope_ref is not None and len(actor.story_scope_ref) == 64
            self.asked.append((actor.account_id, requested))
            return job if requested == job_id else None

    port = OwnsJob()
    ctx.parent_jobs = port
    ctx.eligible = True
    response = _get(client, job_id)
    assert response.status_code == 200
    assert response.json()["target_ref"] == CLASS_ID
    assert port.asked == [(ACCOUNT_ID, job_id)]
    _assert_uniform_404(_get(client, "job_fx9999"), "job_fx9999")
    # The port decides ownership; the registry still decides the kind.
    ctx.parent_jobs = SimpleNamespace(owned_job=lambda _account, _job: job)
    registry_denied = JobStatusReader(
        ctx.harness.store, JobKindRegistry(), ctx.harness.clock, parent_jobs=ctx.parent_jobs
    )
    application = _app(ctx)
    application.dependency_overrides[get_job_status_reader] = lambda: registry_denied
    with TestClient(application) as strict_client:
        _assert_uniform_404(_get(strict_client, job_id), job_id)


def test_reader_picks_the_projection_role_from_the_assignment(ctx: Ctx) -> None:
    job_id = _succeeded_job(ctx)
    reader = ctx.reader()

    def actor(*roles: str) -> JobActor:
        membership = ActorMembership(ORG, frozenset(roles), frozenset({CLASS_ID}))
        return JobActor(ACCOUNT_ID, "teacher", lambda _org: membership)

    assert reader.read(actor("teacher"), job_id).status.role is PrincipalRole.TEACHER
    assert reader.read(actor("school_admin"), job_id).status.role is PrincipalRole.ADMIN
    both = reader.read(actor("school_admin", "teacher"), job_id)
    assert both.status.role is PrincipalRole.TEACHER


# --------------------------------------------------------------- composition and envelope
def _job_routes(application: FastAPI) -> list[str]:
    application.openapi()
    paths = application.state.runtime_openapi_schema["paths"]
    return [
        method.upper()
        for method in paths.get("/v1/jobs/{job_id}", {})
        if method in {"get", "post", "put", "patch", "delete"}
    ]


def test_route_is_mounted_exactly_once_per_profile() -> None:
    from sketch2life.interfaces.http.app import create_classroom_app, create_demo_app

    assert _job_routes(create_app()) == ["GET"]
    assert _job_routes(create_classroom_app()) == ["GET"]
    assert _job_routes(create_demo_app()) == []
    combined = create_app()
    operation_ids = [
        operation["operationId"]
        for path_item in combined.openapi(fe_projected=False)["paths"].values()
        for operation in path_item.values()
        if isinstance(operation, dict) and "operationId" in operation
    ]
    assert len([op for op in operation_ids if op.startswith("get_job_status_v1_jobs")]) == 1


def test_route_is_runtime_only_and_not_in_the_fe_projected_spec() -> None:
    application = create_app()
    assert "/v1/jobs/{job_id}" not in application.openapi()["paths"]
    application.openapi(fe_projected=False)
    assert "/v1/jobs/{job_id}" in application.state.runtime_openapi_schema["paths"]


def test_app_source_does_not_import_the_job_modules() -> None:
    """T0.5 owns app.py; the mount lives in router_composition (existing guard tests)."""

    app_source = Path(jobs_router.__file__).parents[1] / "app.py"
    tree = ast.parse(app_source.read_text(encoding="utf-8"))
    imported = {
        node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    }
    assert not {name for name in imported if "ai_jobs" in name or name.endswith("job_kinds")}


# ----------------------------------------------------------------- read-only repository
def test_read_only_fence_never_holds_and_declares_the_contract() -> None:
    fence = ReadOnlyFenceHold()
    assert fence.contract_version == OWNER_FENCE_CONTRACT
    with pytest.raises(RuntimeError, match="read-only"):
        fence.hold(())


def test_read_only_repository_factory_binds_the_refusing_fence(monkeypatch: Any) -> None:
    captured: dict[str, Any] = {}

    class Recorder:
        def __init__(self, engine: object, owner_fences: Callable[[object], object]) -> None:
            captured["engine"] = engine
            captured["fence"] = owner_fences(object())

    monkeypatch.setattr(
        "sketch2life.infrastructure.ai_jobs.read_only.SqlAiJobRepository", Recorder
    )
    sentinel = object()
    build_read_only_job_repository(sentinel)  # type: ignore[arg-type]
    assert captured["engine"] is sentinel
    assert isinstance(captured["fence"], ReadOnlyFenceHold)


# ---------------------------------------------------- the T0.2 scope loader extension
class _Result:
    def __init__(self, rows: list[Any]) -> None:
        self._rows = rows

    def all(self) -> list[Any]:
        return self._rows


class _Recording:
    def __init__(self, *results: list[Any]) -> None:
        self._results = list(results)
        self.statements: list[Any] = []

    def execute(self, statement: Any) -> _Result:
        self.statements.append(statement)
        return _Result(self._results.pop(0))


def test_loader_can_be_narrowed_to_one_organization_without_changing_the_rules() -> None:
    org = SimpleNamespace(organization_id="org-a", display_name="School A")
    roles = [SimpleNamespace(organization_id="org-a", role="teacher")]
    classes = [
        SimpleNamespace(
            organization_id="org-a", class_id="c1", display_name="C1", role="teacher",
            state="active",
        )
    ]
    narrow = _Recording([org], roles, classes)
    scope = load_granted_scope(narrow, _identity(), organization_id="org-a")  # type: ignore[arg-type]
    assert [item.organization_id for item in scope.organizations] == ["org-a"]
    assert [item.class_id for item in scope.classes] == ["c1"]
    assert len(narrow.statements) == 3
    first = narrow.statements[0].compile().params
    assert "org-a" in first.values()
    wide = _Recording([org], roles, classes)
    load_granted_scope(wide, _identity())  # type: ignore[arg-type]
    assert "org-a" not in wide.statements[0].compile().params.values()
    # Non-organization roles still read nothing, even when narrowed.
    silent = _Recording()
    load_granted_scope(silent, _identity(role="parent"), organization_id="org-a")  # type: ignore[arg-type]
    assert silent.statements == []
    assert account_scope.__all__.count("load_granted_scope") == 1
