"""Real-PostgreSQL FEAT-064 synthetic eligibility pilot rehearsal.

Run only against an explicitly approved loopback PostgreSQL target: a disposable
``be1_acceptance`` database, a task-owned ``s2l_b1_review_`` database, or the exact existing
``sketch2life`` database under the separately approved A2 scope. This test uses synthetic
identities, the real BE1 HTTP app and PostgreSQL repositories. It does not call a live AI
provider or use child data.
"""

from __future__ import annotations

import importlib.util
import ipaddress
import json
import os
import re
import socket
from collections.abc import Callable, Iterator, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager, suppress
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Barrier, Event, Lock, Thread
from typing import Any, Protocol, cast
from uuid import uuid4

import pytest
import sketch2life.interfaces.http.app as app_module
import sketch2life.interfaces.http.be1_runtime as runtime_module
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.domain.eligibility import ProvisionalDataOrigin
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    ChildTurnModel,
    ClassroomSessionModel,
    ConsentRecordModel,
    DeviceGrantModel,
    ManagedProfileModel,
    OrganizationAssignmentModel,
    OrganizationModel,
    SessionMembershipModel,
    SyntheticEligibilityProofModel,
)
from sketch2life.infrastructure.persistence.core_models import CoreCanvasOperationModel
from sketch2life.infrastructure.persistence.core_store import PostgresCoreStore
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import (
    Be1Runtime,
    get_verified_adult,
    get_verified_device_status,
)
from sqlalchemy import (
    Connection,
    Engine,
    MetaData,
    Table,
    and_,
    delete,
    func,
    inspect,
    select,
    update,
)
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

_LIBPQ_ROUTING_ENVIRONMENT_KEYS = (
    "PGHOST",
    "PGHOSTADDR",
    "PGPORT",
    "PGDATABASE",
    "PGUSER",
    "PGSERVICE",
    "PGSERVICEFILE",
)

_PILOT_POLICY_VERSION = "feat064-synthetic-pilot-v1"
_TASK_OWNED_DATABASE_NAME = re.compile(
    r"(?:s2l_b1_review_[0-9]{8}T[0-9]{6}Z_[0-9a-f]{8}|"
    r"s2l_b1_review_20261104_6a1af65b)\Z"
)


class _JsonResponse(Protocol):
    status_code: int

    @property
    def text(self) -> str: ...

    def json(self) -> Any: ...


@pytest.fixture(autouse=True)
def block_non_loopback_sockets(monkeypatch: pytest.MonkeyPatch) -> None:
    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex

    def assert_local(address: Any) -> None:
        if not isinstance(address, tuple) or not address or not isinstance(address[0], str):
            return
        host = address[0]
        try:
            is_loopback = ipaddress.ip_address(host).is_loopback
        except ValueError:
            is_loopback = host.lower() == "localhost"
        if not is_loopback:
            raise AssertionError("non-loopback network access is disabled in this test module")

    def guarded_connect(sock: socket.socket, address: Any) -> None:
        assert_local(address)
        original_connect(sock, address)

    def guarded_connect_ex(sock: socket.socket, address: Any) -> int:
        assert_local(address)
        return original_connect_ex(sock, address)

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", guarded_connect_ex)


def _synthetic_uuid_token() -> str:
    """Return a lowercase Base36 encoding of a random UUID's 128 bits."""
    alphabet = "0123456789abcdefghijklmnopqrstuvwxyz"
    value = uuid4().int
    digits = ""
    while value:
        value, remainder = divmod(value, len(alphabet))
        digits = alphabet[remainder] + digits
    return digits.rjust(25, "0")


def _synthetic_id() -> str:
    """Prefix a compact UUID with synthetic- and fit BE1's varchar(36) IDs."""
    identifier = f"synthetic-{_synthetic_uuid_token()}"
    assert len(identifier) <= 36
    return identifier


@dataclass(slots=True)
class PilotHarness:
    app: FastAPI
    client: TestClient
    organization_id: str
    class_id: str
    adult_subject: str
    runtime: Be1Runtime
    session_factory: sessionmaker[Session]
    database_url: str = field(repr=False)
    created_ai_jobs: list[tuple[str, tuple[str, ...]]] = field(default_factory=list, repr=False)


def _is_loopback_host(host: object) -> bool:
    if not isinstance(host, str) or not host:
        return False
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return host.lower() == "localhost"


def _libpq_routing_environment_overrides(
    environ: Mapping[str, str],
) -> tuple[str, ...]:
    """Return connection-target environment keys without exposing their values."""

    return tuple(key for key in _LIBPQ_ROUTING_ENVIRONMENT_KEYS if key in environ)


def _is_safe_acceptance_database_url(database_url: str) -> bool:
    try:
        url = make_url(database_url)
    except Exception:
        return False
    database_name = url.database
    task_owned_database = bool(
        database_name and _TASK_OWNED_DATABASE_NAME.fullmatch(database_name)
    )
    if (
        url.get_backend_name() != "postgresql"
        or not url.database
        or (
            not task_owned_database
            and url.database != "sketch2life"
            and "be1_acceptance" not in url.database
        )
        or not _is_loopback_host(url.host)
        or "service" in url.query
    ):
        return False
    if task_owned_database:
        if url.host != "127.0.0.1" or url.port != 5433 or url.username != "postgres":
            return False
        for key, expected in (
            ("host", "127.0.0.1"),
            ("hostaddr", "127.0.0.1"),
            ("port", "5433"),
            ("user", "postgres"),
            ("dbname", database_name),
            ("database", database_name),
        ):
            value = url.query.get(key)
            if value is None:
                continue
            values = value if isinstance(value, tuple) else (value,)
            if not values or any(item != expected for item in values):
                return False
    for key in ("dbname", "database"):
        value = url.query.get(key)
        if value is None:
            continue
        values = value if isinstance(value, tuple) else (value,)
        if not values or any(item != url.database for item in values):
            return False
    if url.database == "sketch2life":
        if url.port != 5433 or url.username != "postgres":
            return False
        for key, expected in (
            ("port", "5433"),
            ("user", "postgres"),
        ):
            value = url.query.get(key)
            if value is None:
                continue
            values = value if isinstance(value, tuple) else (value,)
            if not values or any(item != expected for item in values):
                return False
    # libpq's hostaddr and URL query targets can override name resolution.
    for key in ("host", "hostaddr"):
        value = url.query.get(key)
        if value is None:
            continue
        values = value if isinstance(value, tuple) else (value,)
        if not values or any(not _is_loopback_host(item) for item in values):
            return False
    return True


@pytest.mark.parametrize(
    ("database_url", "expected"),
    [
        ("postgresql://localhost:5433/be1_acceptance", True),
        ("postgresql://postgres@127.0.0.1:5433/be1_acceptance?dbname=be1_acceptance", True),
        ("postgresql://postgres@127.0.0.1:5433/be1_acceptance?database=be1_acceptance", True),
        ("postgresql://127.0.0.1:5433/app_be1_acceptance", True),
        ("postgresql://[::1]:5433/be1_acceptance", True),
        (
            "postgresql+psycopg://other@127.0.0.1:5432/be1_acceptance?dbname=sketch2life",
            False,
        ),
        (
            "postgresql+psycopg://postgres@127.0.0.1:5433/be1_acceptance?database=sketch2life",
            False,
        ),
        ("postgresql://localhost:5433/be1_acceptance?dbname=other_database", False),
        (
            "postgresql://localhost:5433/be1_acceptance?dbname=be1_acceptance&dbname=sketch2life",
            False,
        ),
        ("postgresql://postgres@127.0.0.1:5433/sketch2life", True),
        ("postgresql://postgres@127.0.0.1:5432/sketch2life", False),
        ("postgresql://postgres@127.0.0.1/sketch2life", False),
        ("postgresql://other@127.0.0.1:5433/sketch2life", False),
        ("postgresql://127.0.0.1:5433/sketch2life", False),
        ("postgresql://postgres@127.0.0.1:5433/sketch2life?port=5432", False),
        ("postgresql://postgres@127.0.0.1:5433/sketch2life?user=other", False),
        ("postgresql://postgres@127.0.0.1:5433/sketch2life?dbname=other", False),
        ("postgresql://postgres@127.0.0.1:5433/sketch2life?database=other", False),
        (
            "postgresql+psycopg://postgres@127.0.0.1:5433/"
            "s2l_b1_review_20261104T120000Z_0123abcd",
            True,
        ),
        (
            "postgresql+psycopg://postgres@127.0.0.1:5433/"
            "s2l_b1_review_20261104_6a1af65b",
            True,
        ),
        (
            "postgresql+psycopg://postgres@127.0.0.1:5433/"
            "s2l_b1_review_20261104_6a1af65c",
            False,
        ),
        (
            "postgresql+psycopg://other@127.0.0.1:5433/"
            "s2l_b1_review_20261104_6a1af65b",
            False,
        ),
        (
            "postgresql+psycopg://postgres@127.0.0.1:5432/"
            "s2l_b1_review_20261104_6a1af65b",
            False,
        ),
        (
            "postgresql+psycopg://postgres@127.0.0.1:5432/"
            "s2l_b1_review_20261104T120000Z_0123abcd",
            False,
        ),
        (
            "postgresql+psycopg://postgres@127.0.0.1/"
            "s2l_b1_review_20261104T120000Z_0123abcd",
            False,
        ),
        (
            "postgresql+psycopg://other@127.0.0.1:5433/"
            "s2l_b1_review_20261104T120000Z_0123abcd",
            False,
        ),
        (
            "postgresql+psycopg://127.0.0.1:5433/"
            "s2l_b1_review_20261104T120000Z_0123abcd",
            False,
        ),
        (
            "postgresql+psycopg://postgres@127.0.0.1:5433/"
            "s2l_b1_review_20261104T120000Z_0123abcd?hostaddr=::1",
            False,
        ),
        (
            "postgresql+psycopg://postgres@127.0.0.1:5433/"
            "s2l_b1_review_20261104T120000Z_wrongbad",
            False,
        ),
        ("postgresql://127.0.0.1:5433/sketch2life_test", False),
        ("postgresql://db.example.invalid/sketch2life", False),
        ("postgresql://localhost/sketch2life?hostaddr=203.0.113.9", False),
        ("postgresql://localhost/sketch2life?service=remote", False),
        ("postgresql://db.example.invalid/be1_acceptance", False),
        ("postgresql://localhost/be1_acceptance?hostaddr=203.0.113.9", False),
        ("postgresql://localhost/be1_acceptance?service=remote", False),
        ("postgresql://localhost/application", False),
    ],
)
def test_database_url_requires_loopback_and_approved_name(
    database_url: str, expected: bool
) -> None:
    assert _is_safe_acceptance_database_url(database_url) is expected


@pytest.mark.parametrize("key", _LIBPQ_ROUTING_ENVIRONMENT_KEYS)
def test_libpq_routing_environment_overrides_are_detected(key: str) -> None:
    assert _libpq_routing_environment_overrides({key: "synthetic-value"}) == (key,)


def test_libpq_routing_environment_guard_allows_clean_environment() -> None:
    assert _libpq_routing_environment_overrides({}) == ()


def test_libpq_routing_environment_guard_reports_all_keys_without_values() -> None:
    environment = {
        "PGHOSTADDR": "203.0.113.9",
        "PGSERVICE": "synthetic-remote-service",
        "PGPASSWORD": "must-not-be-reported",
    }
    assert _libpq_routing_environment_overrides(environment) == (
        "PGHOSTADDR",
        "PGSERVICE",
    )


@pytest.fixture
def pilot_harness(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[PilotHarness]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL to run the PostgreSQL synthetic pilot")
    if not _is_safe_acceptance_database_url(database_url):
        pytest.fail(
            "BE1_TEST_DATABASE_URL must target an approved loopback PostgreSQL acceptance database"
        )
    routing_overrides = _libpq_routing_environment_overrides(os.environ)
    if routing_overrides:
        pytest.fail(
            "unset libpq connection-target environment variables before database tests: "
            + ", ".join(routing_overrides)
        )

    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", database_url)
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "development")
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED", "true")
    monkeypatch.setenv("SKETCH2LIFE_BE1_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    settings_factory = cast(Any, Settings)
    core_settings_factory = cast(Any, CoreDatabaseSettings)
    monkeypatch.setattr(app_module, "get_settings", lambda: settings_factory(_env_file=None))
    monkeypatch.setattr(
        runtime_module,
        "get_core_database_settings",
        lambda: core_settings_factory(_env_file=None),
    )

    # This BE1 suite does not exercise lesson-library storage; keep boto3 offline.
    def build_unused_storage(**_settings: object) -> object:
        return object()

    monkeypatch.setattr(app_module, "Boto3S3CompatibleObjectStorage", build_unused_storage)
    app = create_app()
    runtime = app.state.be1_runtime
    engine = runtime.engine
    session_factory = runtime.session_factory
    if engine is None or session_factory is None:
        pytest.fail("BE1 PostgreSQL runtime did not initialize")

    organization_id = _synthetic_id()
    adult_subject = _synthetic_id()
    with session_factory.begin() as db:
        db.add(
            OrganizationModel(
                organization_id=organization_id,
                display_name="Synthetic T12 Organization",
                state="active",
            )
        )
        db.add(AdultIdentityModel(subject=adult_subject, issuer="synthetic-t12", state="active"))
        db.flush()
        db.add(
            OrganizationAssignmentModel(
                assignment_id=_synthetic_id(),
                organization_id=organization_id,
                subject=adult_subject,
                class_id=None,
                role="school_admin",
                active=True,
            )
        )

    principal = VerifiedPrincipal(
        subject=adult_subject,
        issuer="synthetic-t12",
        roles=frozenset(),
        token_id=_synthetic_id(),
    )

    async def verified_test_adult() -> VerifiedPrincipal:
        return principal

    app.dependency_overrides[get_verified_adult] = verified_test_adult
    created_ai_jobs: list[tuple[str, tuple[str, ...]]] = []
    try:
        with TestClient(app) as client:
            class_response = client.post(
                f"/api/be1/v1/organizations/{organization_id}/classes",
                json={"display_name": "Synthetic T12 Class"},
            )
            assert class_response.status_code == 201, class_response.text
            yield PilotHarness(
                app=app,
                client=client,
                organization_id=organization_id,
                class_id=class_response.json()["class_id"],
                adult_subject=adult_subject,
                runtime=runtime,
                session_factory=session_factory,
                database_url=database_url,
                created_ai_jobs=created_ai_jobs,
            )
    finally:
        app.dependency_overrides.clear()
        _delete_test_organization_rows(
            engine, organization_id, {adult_subject}, created_ai_jobs=created_ai_jobs
        )
        engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def _delete_test_organization_rows(
    engine: Engine,
    organization_id: str,
    adult_subjects: set[str],
    *,
    created_ai_jobs: Sequence[tuple[str, Sequence[str]]] = (),
) -> None:
    """Delete rows scoped to this fixture's unique org, never rows from another run."""
    inspector = inspect(engine)
    metadata = MetaData()
    tables: dict[tuple[str, str], Table] = {}
    for schema in inspector.get_schema_names():
        if schema == "information_schema" or schema.startswith("pg_"):
            continue
        for name in inspector.get_table_names(schema=schema):
            table = Table(name, metadata, schema=schema, autoload_with=engine)
            tables[(schema, name)] = table

    ordered = [
        table
        for table in reversed(metadata.sorted_tables)
        if (table.schema or "public", table.name) in tables
        and (table.schema or "public", table.name) != ("public", "alembic_version")
    ]
    jobs = tables.get(("ai_jobs", "job"))
    attempts = tables.get(("ai_jobs", "attempt"))
    completion_receipts = tables.get(("ai_jobs", "completion_receipt"))
    deleted_attempts = 0
    deleted_jobs = 0
    if created_ai_jobs and (jobs is None or attempts is None or completion_receipts is None):
        raise AssertionError("AI job cleanup tables are unavailable")
    with engine.begin() as connection:
        for job_id, attempt_ids in created_ai_jobs:
            assert attempts is not None
            assert completion_receipts is not None
            for attempt_id in attempt_ids:
                receipt = connection.execute(
                    delete(completion_receipts).where(
                        and_(
                            completion_receipts.c.job_id == job_id,
                            completion_receipts.c.attempt_id == attempt_id,
                        )
                    )
                )
                if receipt.rowcount not in {0, 1}:
                    raise AssertionError("test-created AI job receipt cleanup was not exact")
                result = connection.execute(
                    delete(attempts).where(
                        and_(
                            attempts.c.attempt_id == attempt_id,
                            attempts.c.job_id == job_id,
                        )
                    )
                )
                if result.rowcount != 1:
                    raise AssertionError("test-created AI job attempt cleanup was not exact")
                deleted_attempts += 1
        for table in ordered:
            if table.schema == "ai_jobs" and table.name == "job":
                continue
            if "organization_id" not in table.c:
                continue
            primary_key = list(table.primary_key.columns)
            if not primary_key:
                raise AssertionError(f"test-owned table has no primary key: {table.fullname}")
            rows = connection.execute(
                select(*primary_key).where(table.c.organization_id == organization_id)
            ).all()
            for row in rows:
                connection.execute(
                    delete(table).where(
                        and_(
                            *(
                                column == value
                                for column, value in zip(primary_key, row, strict=True)
                            )
                        )
                    )
                )

        for job_id, _attempt_ids in created_ai_jobs:
            assert jobs is not None
            result = connection.execute(delete(jobs).where(jobs.c.job_id == job_id))
            if result.rowcount != 1:
                raise AssertionError("test-created AI job cleanup was not exact")
            deleted_jobs += 1

        adults = tables.get(("public", "be1_adult_identities"))
        if adults is not None:
            for subject in adult_subjects:
                connection.execute(delete(adults).where(adults.c.subject == subject))
    assert deleted_attempts == sum(len(attempt_ids) for _, attempt_ids in created_ai_jobs)
    assert deleted_jobs == len(created_ai_jobs)


def _session_path(harness: PilotHarness, session_id: str, suffix: str = "") -> str:
    return f"/api/be1/v1/organizations/{harness.organization_id}/sessions/{session_id}{suffix}"


def _new_lobby_session(
    harness: PilotHarness, *, purpose_ref: str | None = None, run_ref: str | None = None
) -> tuple[str, str, str, str]:
    purpose = purpose_ref or f"synthetic-purpose-{_synthetic_uuid_token()}"
    run = run_ref or f"synthetic-run-{_synthetic_uuid_token()}"
    created = harness.client.post(
        f"/api/be1/v1/organizations/{harness.organization_id}/sessions",
        json={
            "class_id": harness.class_id,
            "purpose_ref": purpose,
            "configuration": {"pilot_run_ref": run},
        },
    )
    assert created.status_code == 201, created.text
    session_id = created.json()["session_id"]
    lobby = harness.client.post(
        _session_path(harness, session_id, "/lobby"),
        json={"expected_revision": created.json()["revision"]},
    )
    assert lobby.status_code == 200, lobby.text
    return session_id, created.json()["join_code"], purpose, run


def _join_child(harness: PilotHarness, session_id: str, join_code: str) -> tuple[str, str]:
    device_key = f"synthetic-device-{_synthetic_uuid_token()}"
    response = harness.client.post(
        _session_path(harness, session_id, "/join"),
        json={"join_code": join_code, "device_key": device_key},
    )
    assert response.status_code == 202, response.text
    assert response.json()["state"] == "pending"
    return response.json()["grant_id"], device_key


def _operator_run(harness: PilotHarness, args: Sequence[str]) -> list[str]:
    tool_path = Path(__file__).resolve().parents[3] / "tools" / "synthetic_eligibility.py"
    spec = importlib.util.spec_from_file_location("synthetic_eligibility_operator", tool_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    emitted: list[str] = []
    result = module.run(
        args,
        settings_loader=lambda: harness.runtime.settings,
        database_url_loader=lambda: harness.database_url,
        store_factory=lambda _url: PostgresCoreStore(harness.session_factory),
        emit=emitted.append,
    )
    assert result == 0, "; ".join(emitted)
    assert emitted and emitted[-1].startswith("APPLIED:")
    return emitted


def _create_synthetic_profile(
    harness: PilotHarness, *, child_id: str, purpose_ref: str, session_id: str, run_ref: str
) -> str:
    evidence_id = _synthetic_id()
    _operator_run(
        harness,
        [
            "create-profile",
            "--pilot",
            "--apply",
            "--operator",
            f"synthetic-operator-{_synthetic_uuid_token()}",
            "--organization-id",
            harness.organization_id,
            "--class-id",
            harness.class_id,
            "--child-id",
            child_id,
            "--age-months",
            "72",
        ],
    )
    _operator_run(
        harness,
        [
            "issue",
            "--pilot",
            "--apply",
            "--operator",
            f"synthetic-operator-{_synthetic_uuid_token()}",
            "--organization-id",
            harness.organization_id,
            "--class-id",
            harness.class_id,
            "--child-id",
            child_id,
            "--purpose-ref",
            purpose_ref,
            "--run-ref",
            run_ref,
            "--session-id",
            session_id,
            "--evidence-id",
            evidence_id,
        ],
    )
    return evidence_id


def _issue_nonstandard_proof(
    harness: PilotHarness,
    *,
    child_id: str,
    purpose_ref: str,
    run_ref: str,
    session_id: str | None,
    expired: bool = False,
) -> str:
    now = datetime.now(UTC)
    issued_at = now - timedelta(minutes=2) if expired else now
    expires_at = now - timedelta(minutes=1) if expired else now + timedelta(minutes=30)
    evidence_id = _synthetic_id()
    store = PostgresCoreStore(harness.session_factory)
    assert store.issue_synthetic_proof(
        evidence_id=evidence_id,
        organization_id=harness.organization_id,
        class_id=harness.class_id,
        child_id=child_id,
        purpose_ref=purpose_ref,
        run_ref=run_ref,
        session_id=session_id,
        issued_by=f"synthetic-operator-{_synthetic_uuid_token()}",
        issued_at=issued_at,
        expires_at=expires_at,
        policy_version=_PILOT_POLICY_VERSION,
    )
    return evidence_id


def _admit(harness: PilotHarness, session_id: str, grant_id: str, child_id: str) -> _JsonResponse:
    return harness.client.post(
        _session_path(harness, session_id, f"/join-requests/{grant_id}/admit"),
        json={"child_id": child_id},
    )


def _current_revision(harness: PilotHarness, session_id: str) -> int:
    response = harness.client.get(_session_path(harness, session_id))
    assert response.status_code == 200, response.text
    revision = response.json().get("revision")
    assert isinstance(revision, int)
    return revision


def _prepare_synthetic_group(
    harness: PilotHarness,
) -> tuple[str, str, str, str, str]:
    session_id, join_code, purpose_ref, run_ref = _new_lobby_session(harness)
    child_id = _synthetic_id()
    _create_synthetic_profile(
        harness,
        child_id=child_id,
        purpose_ref=purpose_ref,
        session_id=session_id,
        run_ref=run_ref,
    )
    grant_id, device_key = _join_child(harness, session_id, join_code)
    admitted = _admit(harness, session_id, grant_id, child_id)
    assert admitted.status_code == 200, admitted.text
    group = harness.client.post(
        _session_path(harness, session_id, "/groups"), json={"display_name": "Synthetic Group"}
    )
    assert group.status_code == 201, group.text
    group_id = group.json()["group_id"]
    assigned = harness.client.put(
        _session_path(harness, session_id, f"/groups/{group_id}/members/{child_id}"),
        json={"child_id": child_id, "expected_revision": _current_revision(harness, session_id)},
    )
    assert assigned.status_code == 200, assigned.text
    started = harness.client.post(
        _session_path(harness, session_id, "/start"),
        json={"expected_revision": _current_revision(harness, session_id)},
    )
    assert started.status_code == 200, started.text
    return session_id, child_id, group_id, grant_id, device_key


def _prepare_synthetic_lobby(harness: PilotHarness) -> tuple[str, str]:
    session_id, _join_code, purpose_ref, run_ref = _new_lobby_session(harness)
    child_id = _synthetic_id()
    _create_synthetic_profile(
        harness,
        child_id=child_id,
        purpose_ref=purpose_ref,
        session_id=session_id,
        run_ref=run_ref,
    )
    return session_id, child_id


def _status_request(harness: PilotHarness, session_id: str) -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": _session_path(harness, session_id, "/requests/synthetic-request/status"),
            "headers": [],
            "path_params": {
                "organization_id": harness.organization_id,
                "session_id": session_id,
            },
        }
    )


def test_t12_synthetic_profile_to_accepted_canvas_stroke_without_consent(
    pilot_harness: PilotHarness,
) -> None:
    harness = pilot_harness
    session_id, join_code, purpose_ref, run_ref = _new_lobby_session(harness)
    session_response = harness.client.get(_session_path(harness, session_id))
    assert session_response.status_code == 200, session_response.text
    configuration = session_response.json()["configuration"]
    assert configuration["canvas_operation_profile"]["profile_id"] == "canvas-operation-profile-v1"
    assert configuration["canvas_operation_profile"]["version"] == "CanvasOperationProfileV1"
    child_id = _synthetic_id()
    _create_synthetic_profile(
        harness,
        child_id=child_id,
        purpose_ref=purpose_ref,
        session_id=session_id,
        run_ref=run_ref,
    )
    grant_id, device_key = _join_child(harness, session_id, join_code)

    admitted = _admit(harness, session_id, grant_id, child_id)
    assert admitted.status_code == 200, admitted.text
    group = harness.client.post(
        _session_path(harness, session_id, "/groups"), json={"display_name": "Synthetic Group"}
    )
    assert group.status_code == 201, group.text
    group_id = group.json()["group_id"]
    assigned = harness.client.put(
        _session_path(harness, session_id, f"/groups/{group_id}/members/{child_id}"),
        json={"child_id": child_id, "expected_revision": _current_revision(harness, session_id)},
    )
    assert assigned.status_code == 200, assigned.text
    started = harness.client.post(
        _session_path(harness, session_id, "/start"),
        json={"expected_revision": _current_revision(harness, session_id)},
    )
    assert started.status_code == 200, started.text
    turn = harness.client.post(
        _session_path(harness, session_id, f"/groups/{group_id}/turns/{child_id}")
    )
    assert turn.status_code == 200, turn.text

    operation_id = _synthetic_id()
    profile_mismatch_id = _synthetic_id()
    mismatch = harness.client.post(
        _session_path(harness, session_id, "/canvas/operations"),
        headers={
            "X-Be1-Grant": grant_id,
            "X-Be1-Device-Key": device_key,
            "Idempotency-Key": profile_mismatch_id,
        },
        json={
            "operation_id": profile_mismatch_id,
            "turn_id": turn.json()["turn_id"],
            "document_epoch": 1,
            "expected_revision": 1,
            "operation_payload": {
                "kind": "stroke",
                "points": [{"x": 0.1, "y": 0.2}, {"x": 0.3, "y": 0.4}],
                "color": "#FFD21F",
                "size": 5,
            },
        },
    )
    assert mismatch.status_code == 409, mismatch.text
    assert mismatch.json()["code"] == "CANVAS_PROFILE_MISMATCH"

    invalid_operation_id = _synthetic_id()
    invalid = harness.client.post(
        _session_path(harness, session_id, "/canvas/operations"),
        headers={
            "X-Be1-Grant": grant_id,
            "X-Be1-Device-Key": device_key,
            "Idempotency-Key": invalid_operation_id,
        },
        json={
            "operation_id": invalid_operation_id,
            "turn_id": turn.json()["turn_id"],
            "document_epoch": 1,
            "expected_revision": 1,
            "profile_version": "CanvasOperationProfileV1",
            "operation_payload": {
                "kind": "stroke",
                "points": [{"x": 0.1, "y": 0.2}],
                "color": "#FFD21F",
                "size": 5,
            },
        },
    )
    assert invalid.status_code == 422, invalid.text
    assert invalid.json()["code"] == "CANVAS_PROFILE_INVALID"

    stroke = harness.client.post(
        _session_path(harness, session_id, "/canvas/operations"),
        headers={
            "X-Be1-Grant": grant_id,
            "X-Be1-Device-Key": device_key,
            "Idempotency-Key": operation_id,
        },
        json={
            "operation_id": operation_id,
            "turn_id": turn.json()["turn_id"],
            "document_epoch": 1,
            "expected_revision": 1,
            "profile_version": "CanvasOperationProfileV1",
            "operation_payload": {
                "kind": "stroke",
                "points": [{"x": 0.1, "y": 0.1}, {"x": 0.3, "y": 0.35}],
                "color": "#FFD21F",
                "size": 5,
            },
        },
    )
    assert stroke.status_code == 200, stroke.text
    assert stroke.json()["status"] == "accepted"

    with harness.session_factory() as db:
        profile = db.get(ManagedProfileModel, child_id)
        assert profile is not None
        assert profile.data_origin == ProvisionalDataOrigin.SYNTHETIC_DEV.value
        assert profile.consent_id is None
        assert profile.consent_purpose_ref is None
        assert (
            db.scalar(
                select(ConsentRecordModel.consent_id).where(
                    ConsentRecordModel.organization_id == harness.organization_id,
                    ConsentRecordModel.child_id == child_id,
                )
            )
            is None
        )
        proof = db.scalar(
            select(SyntheticEligibilityProofModel).where(
                SyntheticEligibilityProofModel.organization_id == harness.organization_id,
                SyntheticEligibilityProofModel.child_profile_id == child_id,
                SyntheticEligibilityProofModel.session_id == session_id,
            )
        )
        assert proof is not None
        assert proof.run_ref == run_ref
        operation = db.get(CoreCanvasOperationModel, operation_id)
        assert operation is not None
        assert operation.participant_id == child_id
        assert (
            operation.operation_payload["canvas_operation_profile_id"]
            == "canvas-operation-profile-v1"
        )
        assert db.get(CoreCanvasOperationModel, profile_mismatch_id) is None
        assert db.get(CoreCanvasOperationModel, invalid_operation_id) is None

    reconnect = harness.client.get(
        _session_path(harness, session_id, "/reconnect"),
        headers={"X-Be1-Grant": grant_id, "X-Be1-Device-Key": device_key},
    )
    assert reconnect.status_code == 200, reconnect.text
    assert (
        reconnect.json()["operations"][-1]["operation_payload"]["canvas_operation_profile_id"]
        == "canvas-operation-profile-v1"
    )


@pytest.mark.parametrize("bad_color", [["#FFD21F"], {"a": 1}])
def test_t3_unhashable_color_returns_safe_422_without_persisting_operation(
    pilot_harness: PilotHarness, bad_color: object
) -> None:
    harness = pilot_harness
    session_id, child_id, group_id, grant_id, device_key = _prepare_synthetic_group(harness)
    turn = harness.client.post(
        _session_path(harness, session_id, f"/groups/{group_id}/turns/{child_id}")
    )
    assert turn.status_code == 200, turn.text
    operation_id = _synthetic_id()
    store = PostgresCoreStore(harness.session_factory)
    before_revision = store.current_revision(group_id, organization_id=harness.organization_id)

    response = harness.client.post(
        _session_path(harness, session_id, "/canvas/operations"),
        headers={
            "X-Be1-Grant": grant_id,
            "X-Be1-Device-Key": device_key,
            "Idempotency-Key": operation_id,
        },
        json={
            "operation_id": operation_id,
            "turn_id": turn.json()["turn_id"],
            "document_epoch": 1,
            "expected_revision": 1,
            "profile_version": "CanvasOperationProfileV1",
            "operation_payload": {
                "kind": "stroke",
                "points": [{"x": 0.1, "y": 0.2}, {"x": 0.3, "y": 0.4}],
                "color": bad_color,
                "size": 5,
            },
        },
    )
    assert response.status_code == 422, response.text
    body = response.json()
    assert body["code"] == "CANVAS_PROFILE_INVALID"
    assert set(body) == {"code", "message", "request_id"}
    assert "Traceback" not in response.text and "TypeError" not in response.text
    with harness.session_factory() as db:
        assert db.get(CoreCanvasOperationModel, operation_id) is None
    assert (
        store.current_revision(group_id, organization_id=harness.organization_id) == before_revision
    )


@pytest.mark.parametrize(
    "reserved_key",
    ["canvas_operation_profile", "canvas_operation_profile_id", "canvas_operation_profile_version"],
)
def test_t3_session_profile_configuration_is_server_owned(
    pilot_harness: PilotHarness, reserved_key: str
) -> None:
    harness = pilot_harness
    response = harness.client.post(
        f"/api/be1/v1/organizations/{harness.organization_id}/sessions",
        json={
            "class_id": harness.class_id,
            "purpose_ref": f"synthetic-purpose-{_synthetic_uuid_token()}",
            "configuration": {reserved_key: {"profile_id": "client-selected"}},
        },
    )
    assert response.status_code == 422, response.text
    assert response.json()["code"] == "RESERVED_CONFIGURATION_KEY"


def test_t3_profile_is_not_attached_when_synthetic_pilot_is_disabled(
    pilot_harness: PilotHarness, monkeypatch: pytest.MonkeyPatch
) -> None:
    harness = pilot_harness
    monkeypatch.setattr(harness.runtime.settings, "synthetic_pilot_enabled", False)
    response = harness.client.post(
        f"/api/be1/v1/organizations/{harness.organization_id}/sessions",
        json={
            "class_id": harness.class_id,
            "purpose_ref": f"synthetic-purpose-{_synthetic_uuid_token()}",
            "configuration": {"pilot_run_ref": f"synthetic-run-{_synthetic_uuid_token()}"},
        },
    )
    assert response.status_code == 201, response.text
    assert "canvas_operation_profile" not in response.json()["configuration"]


@pytest.mark.parametrize(
    ("target_state", "start_turn"),
    [("active", False), ("paused", False), ("active", True)],
)
def test_t2_child_reconnect_is_scoped_and_does_not_require_a_turn(
    pilot_harness: PilotHarness, target_state: str, start_turn: bool
) -> None:
    harness = pilot_harness
    session_id, child_id, group_id, grant_id, device_key = _prepare_synthetic_group(harness)
    turn_id = None
    if start_turn:
        turn = harness.client.post(
            _session_path(harness, session_id, f"/groups/{group_id}/turns/{child_id}")
        )
        assert turn.status_code == 200, turn.text
        turn_id = turn.json()["turn_id"]
    if target_state == "paused":
        paused = harness.client.post(
            _session_path(harness, session_id, "/pause"),
            json={"expected_revision": _current_revision(harness, session_id)},
        )
        assert paused.status_code == 200, paused.text

    response = harness.client.get(
        _session_path(harness, session_id, "/reconnect"),
        headers={"X-Be1-Grant": grant_id, "X-Be1-Device-Key": device_key},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["contract"] == "Be1CanvasReconnectV1"
    assert body["canvas_id"] == group_id
    assert body["turn_id"] == turn_id
    assert body["profile_version"] == "CanvasOperationProfileV1"
    assert body["document_epoch"] == 1
    assert body["current_revision"] == (1 if start_turn else 0)
    assert body["checkpoint"] is None
    assert body["operations"] == []


def test_t3_profiled_reconnect_version_can_be_echoed_by_append(
    pilot_harness: PilotHarness,
) -> None:
    harness = pilot_harness
    session_id, child_id, group_id, grant_id, device_key = _prepare_synthetic_group(harness)
    reconnect = harness.client.get(
        _session_path(harness, session_id, "/reconnect"),
        headers={"X-Be1-Grant": grant_id, "X-Be1-Device-Key": device_key},
    )
    assert reconnect.status_code == 200, reconnect.text
    profile_version = reconnect.json()["profile_version"]
    assert profile_version == "CanvasOperationProfileV1"

    turn = harness.client.post(
        _session_path(harness, session_id, f"/groups/{group_id}/turns/{child_id}")
    )
    assert turn.status_code == 200, turn.text
    operation_id = _synthetic_id()
    appended = harness.client.post(
        _session_path(harness, session_id, "/canvas/operations"),
        headers={
            "X-Be1-Grant": grant_id,
            "X-Be1-Device-Key": device_key,
            "Idempotency-Key": operation_id,
        },
        json={
            "operation_id": operation_id,
            "turn_id": turn.json()["turn_id"],
            "document_epoch": 1,
            "expected_revision": 1,
            "profile_version": profile_version,
            "operation_payload": {
                "kind": "stroke",
                "points": [{"x": 0.1, "y": 0.2}, {"x": 0.3, "y": 0.4}],
                "color": "#FFD21F",
                "size": 5,
            },
        },
    )
    assert appended.status_code == 200, appended.text


def test_t3_legacy_reconnect_returns_null_version_and_keeps_legacy_append(
    pilot_harness: PilotHarness,
) -> None:
    harness = pilot_harness
    session_id, child_id, group_id, grant_id, device_key = _prepare_synthetic_group(harness)
    with harness.session_factory.begin() as db:
        session = db.get(ClassroomSessionModel, session_id)
        assert session is not None
        session.configuration = dict(session.configuration)
        session.configuration.pop("canvas_operation_profile", None)

    turn = harness.client.post(
        _session_path(harness, session_id, f"/groups/{group_id}/turns/{child_id}")
    )
    assert turn.status_code == 200, turn.text
    reconnect = harness.client.get(
        _session_path(harness, session_id, "/reconnect"),
        headers={"X-Be1-Grant": grant_id, "X-Be1-Device-Key": device_key},
    )
    assert reconnect.status_code == 200, reconnect.text
    assert reconnect.json()["profile_version"] is None

    operation_id = _synthetic_id()
    legacy_payload = {"legacy_operation": "opaque"}
    appended = harness.client.post(
        _session_path(harness, session_id, "/canvas/operations"),
        headers={
            "X-Be1-Grant": grant_id,
            "X-Be1-Device-Key": device_key,
            "Idempotency-Key": operation_id,
        },
        json={
            "operation_id": operation_id,
            "turn_id": turn.json()["turn_id"],
            "document_epoch": 1,
            "expected_revision": 1,
            "operation_payload": legacy_payload,
        },
    )
    assert appended.status_code == 200, appended.text
    replay = harness.client.get(
        _session_path(harness, session_id, "/reconnect"),
        headers={"X-Be1-Grant": grant_id, "X-Be1-Device-Key": device_key},
    )
    assert replay.status_code == 200, replay.text
    assert replay.json()["profile_version"] is None
    assert replay.json()["operations"][-1]["operation_payload"] == legacy_payload


@pytest.mark.parametrize(
    ("denial_case", "expected_status", "expected_code"),
    [
        ("foreign_session", 403, "DEVICE_SCOPE_INACTIVE"),
        ("wrong_key", 401, "INVALID_DEVICE_CREDENTIAL"),
        ("revoked_grant", 401, "INVALID_DEVICE_CREDENTIAL"),
        ("finished_session", 403, "DEVICE_SCOPE_INACTIVE"),
        ("lobby_session", 403, "DEVICE_SCOPE_INACTIVE"),
        ("membership_not_admitted", 403, "DEVICE_MEMBERSHIP_INACTIVE"),
        ("missing_group", 404, "GROUP_NOT_FOUND"),
        ("other_group_member_not_eligible", 409, "CONSENT_NOT_EFFECTIVE"),
        ("revoked_proof", 409, "CONSENT_NOT_EFFECTIVE"),
        ("expired_proof", 409, "CONSENT_NOT_EFFECTIVE"),
    ],
)
def test_t2_reconnect_denials_do_not_disclose_canvas(
    pilot_harness: PilotHarness,
    denial_case: str,
    expected_status: int,
    expected_code: str,
) -> None:
    harness = pilot_harness
    session_id, child_id, group_id, grant_id, device_key = _prepare_synthetic_group(harness)
    path_session_id = session_id
    supplied_key = device_key
    with harness.session_factory.begin() as db:
        grant = db.get(DeviceGrantModel, grant_id)
        assert grant is not None
        if denial_case == "wrong_key":
            supplied_key = f"synthetic-wrong-device-{_synthetic_uuid_token()}"
        elif denial_case == "revoked_grant":
            grant.state = "revoked"
        elif denial_case == "finished_session":
            session = db.get(ClassroomSessionModel, session_id)
            assert session is not None
            session.state = "finished"
        elif denial_case == "lobby_session":
            session = db.get(ClassroomSessionModel, session_id)
            assert session is not None
            session.state = "lobby"
        elif denial_case in {"membership_not_admitted", "missing_group"}:
            membership = db.scalar(
                select(SessionMembershipModel).where(
                    SessionMembershipModel.organization_id == harness.organization_id,
                    SessionMembershipModel.session_id == session_id,
                    SessionMembershipModel.child_id == child_id,
                )
            )
            assert membership is not None
            if denial_case == "membership_not_admitted":
                membership.state = "left"
            else:
                membership.group_id = None
        elif denial_case == "other_group_member_not_eligible":
            db.add(
                SessionMembershipModel(
                    membership_id=_synthetic_id(),
                    organization_id=harness.organization_id,
                    session_id=session_id,
                    class_id=harness.class_id,
                    child_id=_synthetic_id(),
                    state="admitted",
                    group_id=group_id,
                    device_grant_id=None,
                    progress="not_started",
                    help_requested=False,
                )
            )
        elif denial_case in {"revoked_proof", "expired_proof"}:
            proof = db.scalar(
                select(SyntheticEligibilityProofModel).where(
                    SyntheticEligibilityProofModel.organization_id == harness.organization_id,
                    SyntheticEligibilityProofModel.child_profile_id == child_id,
                    SyntheticEligibilityProofModel.session_id == session_id,
                )
            )
            assert proof is not None
            if denial_case == "revoked_proof":
                proof.revoked_at = datetime.now(UTC)
                proof.revocation_revision = 1
            else:
                now = datetime.now(UTC)
                proof.issued_at = now - timedelta(minutes=1)
                proof.expires_at = now - timedelta(seconds=1)
        elif denial_case == "foreign_session":
            path_session_id = _synthetic_id()

    response = harness.client.get(
        _session_path(harness, path_session_id, "/reconnect"),
        headers={"X-Be1-Grant": grant_id, "X-Be1-Device-Key": supplied_key},
    )
    assert response.status_code == expected_status, response.text
    assert response.json()["code"] == expected_code
    assert "canvas_id" not in response.json()


def test_t2_legal_origin_reconnect_preserves_pre_g1_pending_consent_denial(
    pilot_harness: PilotHarness,
) -> None:
    harness = pilot_harness
    session_id, child_id, _group_id, grant_id, device_key = _prepare_synthetic_group(harness)
    consent_id = _synthetic_id()
    with harness.session_factory.begin() as db:
        profile = db.get(ManagedProfileModel, child_id)
        session = db.get(ClassroomSessionModel, session_id)
        assert profile is not None and session is not None
        purpose_ref = str(session.configuration["purpose_ref"])
        profile.data_origin = ProvisionalDataOrigin.REAL.value
        profile.consent_id = consent_id
        profile.consent_purpose_ref = purpose_ref
        proof = db.scalar(
            select(SyntheticEligibilityProofModel).where(
                SyntheticEligibilityProofModel.organization_id == harness.organization_id,
                SyntheticEligibilityProofModel.child_profile_id == child_id,
                SyntheticEligibilityProofModel.session_id == session_id,
            )
        )
        assert proof is not None
        db.delete(proof)
        db.add(
            ConsentRecordModel(
                consent_id=consent_id,
                organization_id=harness.organization_id,
                class_id=harness.class_id,
                child_id=child_id,
                purpose_ref=purpose_ref,
                state="pending",
                recorded_by=harness.adult_subject,
            )
        )

    response = harness.client.get(
        _session_path(harness, session_id, "/reconnect"),
        headers={"X-Be1-Grant": grant_id, "X-Be1-Device-Key": device_key},
    )
    assert response.status_code == 409, response.text
    assert response.json()["code"] == "CONSENT_NOT_EFFECTIVE"
    assert "canvas_id" not in response.json()


def test_t9_teacher_pilot_profile_route_returns_only_the_scoped_candidate_fields(
    pilot_harness: PilotHarness,
) -> None:
    harness = pilot_harness
    session_id, child_id = _prepare_synthetic_lobby(harness)
    with harness.session_factory() as db:
        profile = db.get(ManagedProfileModel, child_id)
        assert profile is not None
        expected_display_name = profile.display_name
    response = harness.client.get(_session_path(harness, session_id, "/pilot-profiles"))
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["contract"] == "Be1PilotProfileListV1"
    assert body["items"] == [{"child_id": child_id, "display_name": expected_display_name}]
    assert set(body["items"][0]) == {"child_id", "display_name"}


@pytest.mark.parametrize(
    "invalid_fact",
    [
        "unbound_session",
        "wrong_session",
        "expired",
        "not_yet_valid",
        "revoked",
        "wrong_schema",
        "wrong_purpose",
        "wrong_class",
        "inactive_profile",
    ],
)
def test_t9_invalid_proof_or_profile_is_not_a_candidate(
    pilot_harness: PilotHarness, invalid_fact: str
) -> None:
    harness = pilot_harness
    session_id, child_id = _prepare_synthetic_lobby(harness)
    with harness.session_factory.begin() as db:
        proof = db.scalar(
            select(SyntheticEligibilityProofModel).where(
                SyntheticEligibilityProofModel.organization_id == harness.organization_id,
                SyntheticEligibilityProofModel.child_profile_id == child_id,
                SyntheticEligibilityProofModel.session_id == session_id,
            )
        )
        assert proof is not None
        now = datetime.now(UTC)
        if invalid_fact == "unbound_session":
            proof.session_id = None
        elif invalid_fact == "wrong_session":
            proof.session_id = _synthetic_id()
        elif invalid_fact == "expired":
            proof.issued_at = now - timedelta(minutes=2)
            proof.expires_at = now - timedelta(minutes=1)
        elif invalid_fact == "not_yet_valid":
            proof.issued_at = now + timedelta(minutes=1)
            proof.expires_at = now + timedelta(minutes=2)
        elif invalid_fact == "revoked":
            proof.revoked_at = now
            proof.revocation_revision = 1
        elif invalid_fact == "wrong_schema":
            proof.schema_version = "synthetic-dev-eligibility-v0"
        elif invalid_fact == "wrong_purpose":
            proof.purpose_ref = _synthetic_id()
        elif invalid_fact == "wrong_class":
            proof.class_id = _synthetic_id()
        elif invalid_fact == "inactive_profile":
            profile = db.get(ManagedProfileModel, child_id)
            assert profile is not None
            profile.state = "inactive"

    response = harness.client.get(_session_path(harness, session_id, "/pilot-profiles"))
    assert response.status_code == 200, response.text
    assert response.json()["items"] == []


@pytest.mark.parametrize(
    ("setting", "value"), [("synthetic_pilot_enabled", False), ("env", "staging")]
)
def test_t9_profile_route_is_disabled_outside_local_pilot(
    pilot_harness: PilotHarness, monkeypatch: pytest.MonkeyPatch, setting: str, value: object
) -> None:
    harness = pilot_harness
    session_id, _child_id = _prepare_synthetic_lobby(harness)
    monkeypatch.setattr(harness.runtime.settings, setting, value)
    response = harness.client.get(_session_path(harness, session_id, "/pilot-profiles"))
    assert response.status_code == 409, response.text
    assert response.json()["code"] == "PILOT_PROFILE_LOOKUP_UNAVAILABLE"
    assert "items" not in response.json()


def test_t9_profile_route_requires_lobby_state_and_assignment(
    pilot_harness: PilotHarness,
) -> None:
    harness = pilot_harness
    session_id, _child_id, _group_id, _grant_id, _device_key = _prepare_synthetic_group(harness)
    not_lobby = harness.client.get(_session_path(harness, session_id, "/pilot-profiles"))
    assert not_lobby.status_code == 409
    assert not_lobby.json()["code"] == "SESSION_NOT_IN_LOBBY"
    with harness.session_factory.begin() as db:
        assignment = db.scalar(
            select(OrganizationAssignmentModel).where(
                OrganizationAssignmentModel.organization_id == harness.organization_id,
                OrganizationAssignmentModel.subject == harness.adult_subject,
                OrganizationAssignmentModel.active.is_(True),
            )
        )
        assert assignment is not None
        assignment.active = False
    unassigned = harness.client.get(_session_path(harness, session_id, "/pilot-profiles"))
    assert unassigned.status_code == 403
    assert "items" not in unassigned.json()


def test_t9_foreign_organization_session_route_does_not_disclose_candidates(
    pilot_harness: PilotHarness,
) -> None:
    harness = pilot_harness
    session_id, _child_id = _prepare_synthetic_lobby(harness)
    response = harness.client.get(
        f"/api/be1/v1/organizations/{_synthetic_id()}/sessions/{session_id}/pilot-profiles"
    )
    assert response.status_code == 404
    assert "items" not in response.json()


def test_t9_teacher_assigned_to_a_different_class_is_denied(
    pilot_harness: PilotHarness,
) -> None:
    harness = pilot_harness
    session_id, _child_id = _prepare_synthetic_lobby(harness)
    other_class = harness.client.post(
        f"/api/be1/v1/organizations/{harness.organization_id}/classes",
        json={"display_name": "Synthetic Other Class"},
    )
    assert other_class.status_code == 201, other_class.text
    with harness.session_factory.begin() as db:
        global_assignment = db.scalar(
            select(OrganizationAssignmentModel).where(
                OrganizationAssignmentModel.organization_id == harness.organization_id,
                OrganizationAssignmentModel.subject == harness.adult_subject,
                OrganizationAssignmentModel.class_id.is_(None),
                OrganizationAssignmentModel.active.is_(True),
            )
        )
        assert global_assignment is not None
        global_assignment.active = False
        db.add(
            OrganizationAssignmentModel(
                assignment_id=_synthetic_id(),
                organization_id=harness.organization_id,
                subject=harness.adult_subject,
                class_id=other_class.json()["class_id"],
                role="teacher",
                active=True,
            )
        )
    response = harness.client.get(_session_path(harness, session_id, "/pilot-profiles"))
    assert response.status_code == 403, response.text
    assert "items" not in response.json()


def test_t12_http_admission_rejects_invalid_pilot_basis_and_pending_real_consent(
    pilot_harness: PilotHarness,
) -> None:
    harness = pilot_harness
    cases = (
        "pilot_disabled",
        "expired",
        "revoked",
        "session_unbound",
        "wrong_session",
        "real_pending",
    )
    for case in cases:
        session_id, join_code, purpose_ref, run_ref = _new_lobby_session(harness)
        child_id = _synthetic_id()
        grant_id, _device_key = _join_child(harness, session_id, join_code)

        if case == "real_pending":
            consent_id = _synthetic_id()
            with harness.session_factory.begin() as db:
                db.add(
                    ConsentRecordModel(
                        consent_id=consent_id,
                        organization_id=harness.organization_id,
                        class_id=harness.class_id,
                        child_id=child_id,
                        purpose_ref=purpose_ref,
                        state="pending",
                        recorded_by=harness.adult_subject,
                    )
                )
                db.add(
                    ManagedProfileModel(
                        child_id=child_id,
                        organization_id=harness.organization_id,
                        class_id=harness.class_id,
                        display_name="Synthetic Pending Consent Profile",
                        age_months=72,
                        age_revision=1,
                        age_source="ADULT_DECLARED",
                        consent_id=consent_id,
                        consent_purpose_ref=purpose_ref,
                        created_by=harness.adult_subject,
                    )
                )
        else:
            evidence_id = _create_synthetic_profile(
                harness,
                child_id=child_id,
                purpose_ref=purpose_ref,
                session_id=session_id,
                run_ref=run_ref,
            )
            if case in {"expired", "session_unbound"}:
                with harness.session_factory.begin() as db:
                    db.delete(db.get(SyntheticEligibilityProofModel, evidence_id))
                _issue_nonstandard_proof(
                    harness,
                    child_id=child_id,
                    purpose_ref=purpose_ref,
                    run_ref=run_ref,
                    session_id=None if case == "session_unbound" else session_id,
                    expired=case == "expired",
                )
            elif case == "wrong_session":
                with harness.session_factory.begin() as db:
                    db.delete(db.get(SyntheticEligibilityProofModel, evidence_id))
                _issue_nonstandard_proof(
                    harness,
                    child_id=child_id,
                    purpose_ref=purpose_ref,
                    run_ref=run_ref,
                    session_id=_synthetic_id(),
                )
            elif case == "revoked":
                _operator_run(
                    harness,
                    [
                        "revoke",
                        "--pilot",
                        "--apply",
                        "--operator",
                        f"synthetic-operator-{_synthetic_uuid_token()}",
                        "--organization-id",
                        harness.organization_id,
                        "--evidence-id",
                        evidence_id,
                    ],
                )

        original_settings = harness.runtime.settings
        if case == "pilot_disabled":
            harness.runtime.settings = original_settings.model_copy(
                update={"synthetic_pilot_enabled": False}
            )
        try:
            denied = _admit(harness, session_id, grant_id, child_id)
        finally:
            harness.runtime.settings = original_settings
        assert denied.status_code == 409, f"{case}: {denied.status_code} {denied.text}"
        assert denied.json()["code"] == "CONSENT_NOT_EFFECTIVE", f"{case}: {denied.text}"


def test_t12_status_guard_reads_active_and_paused_without_turn_and_denies_lobby_finished(
    pilot_harness: PilotHarness,
) -> None:
    harness = pilot_harness
    session_id, join_code, purpose_ref, run_ref = _new_lobby_session(harness)
    child_id = _synthetic_id()
    _create_synthetic_profile(
        harness,
        child_id=child_id,
        purpose_ref=purpose_ref,
        session_id=session_id,
        run_ref=run_ref,
    )
    grant_id, device_key = _join_child(harness, session_id, join_code)
    admitted = _admit(harness, session_id, grant_id, child_id)
    assert admitted.status_code == 200, admitted.text

    request = _status_request(harness, session_id)
    with harness.session_factory() as db:
        assert (
            db.scalar(
                select(ChildTurnModel.turn_id).where(
                    ChildTurnModel.organization_id == harness.organization_id,
                    ChildTurnModel.session_id == session_id,
                )
            )
            is None
        )

    started = harness.client.post(
        _session_path(harness, session_id, "/start"),
        json={"expected_revision": _current_revision(harness, session_id)},
    )
    assert started.status_code == 200, started.text
    with harness.session_factory() as db:
        active_context = get_verified_device_status(
            request, grant_id=grant_id, device_key=device_key, db=db, runtime=harness.runtime
        )
        assert active_context.session.state == "active"

    paused = harness.client.post(
        _session_path(harness, session_id, "/pause"),
        json={"expected_revision": _current_revision(harness, session_id)},
    )
    assert paused.status_code == 200, paused.text
    with harness.session_factory() as db:
        paused_context = get_verified_device_status(
            request, grant_id=grant_id, device_key=device_key, db=db, runtime=harness.runtime
        )
        assert paused_context.session.state == "paused"

    resumed = harness.client.post(
        _session_path(harness, session_id, "/resume"),
        json={"expected_revision": _current_revision(harness, session_id)},
    )
    assert resumed.status_code == 200, resumed.text
    finished = harness.client.post(
        _session_path(harness, session_id, "/finish"),
        json={"expected_revision": _current_revision(harness, session_id)},
    )
    assert finished.status_code == 200, finished.text
    with harness.session_factory() as db:
        with pytest.raises(HTTPException) as denied_finished:
            get_verified_device_status(
                request, grant_id=grant_id, device_key=device_key, db=db, runtime=harness.runtime
            )
        assert denied_finished.value.status_code == 403
        assert isinstance(denied_finished.value.detail, dict)
        assert denied_finished.value.detail["code"] == "DEVICE_SCOPE_INACTIVE"

    lobby_id, lobby_code, lobby_purpose, lobby_run = _new_lobby_session(harness)
    lobby_child = _synthetic_id()
    _create_synthetic_profile(
        harness,
        child_id=lobby_child,
        purpose_ref=lobby_purpose,
        session_id=lobby_id,
        run_ref=lobby_run,
    )
    lobby_grant, lobby_device_key = _join_child(harness, lobby_id, lobby_code)
    lobby_admitted = _admit(harness, lobby_id, lobby_grant, lobby_child)
    assert lobby_admitted.status_code == 200, lobby_admitted.text
    with harness.session_factory() as db:
        with pytest.raises(HTTPException) as denied_lobby:
            get_verified_device_status(
                _status_request(harness, lobby_id),
                grant_id=lobby_grant,
                device_key=lobby_device_key,
                db=db,
                runtime=harness.runtime,
            )
        assert denied_lobby.value.status_code == 403
        assert isinstance(denied_lobby.value.detail, dict)
        assert denied_lobby.value.detail["code"] == "DEVICE_SCOPE_INACTIVE"


def test_t12_postgres_checks_reject_invalid_profile_origin_and_effective_consent_state(
    pilot_harness: PilotHarness,
) -> None:
    harness = pilot_harness
    profile_id = _synthetic_id()
    consent_id = _synthetic_id()

    with harness.session_factory.begin() as db:
        with pytest.raises(IntegrityError) as bad_origin, db.begin_nested():
            db.add(
                ManagedProfileModel(
                    child_id=profile_id,
                    organization_id=harness.organization_id,
                    class_id=harness.class_id,
                    display_name="Synthetic Invalid Origin",
                    age_months=72,
                    age_revision=1,
                    age_source="ADULT_DECLARED",
                    consent_id=None,
                    consent_purpose_ref=None,
                    data_origin="NOT_A_VALID_ORIGIN",
                    created_by=harness.adult_subject,
                )
            )
            db.flush()
        assert getattr(getattr(bad_origin.value.orig, "diag", None), "constraint_name", None) == (
            "ck_be1_profile_data_origin"
        )

        with pytest.raises(IntegrityError) as bad_consent_state, db.begin_nested():
            db.add(
                ConsentRecordModel(
                    consent_id=consent_id,
                    organization_id=harness.organization_id,
                    class_id=harness.class_id,
                    child_id=profile_id,
                    purpose_ref=f"synthetic-purpose-{_synthetic_uuid_token()}",
                    state="effective",
                    recorded_by=harness.adult_subject,
                )
            )
            db.flush()
        assert (
            getattr(getattr(bad_consent_state.value.orig, "diag", None), "constraint_name", None)
            == "ck_be1_consent_state"
        )


def _t4_append_two_strokes(
    harness: PilotHarness,
) -> tuple[str, str, str, str, str, list[str]]:
    session_id, child_id, group_id, grant_id, device_key = _prepare_synthetic_group(harness)
    turn = harness.client.post(
        _session_path(harness, session_id, f"/groups/{group_id}/turns/{child_id}")
    )
    assert turn.status_code == 200, turn.text
    operation_ids: list[str] = []
    for expected_revision in (1, 2):
        operation_id = _synthetic_id()
        operation_ids.append(operation_id)
        response = harness.client.post(
            _session_path(harness, session_id, "/canvas/operations"),
            headers={
                "X-Be1-Grant": grant_id,
                "X-Be1-Device-Key": device_key,
                "Idempotency-Key": operation_id,
            },
            json={
                "operation_id": operation_id,
                "turn_id": turn.json()["turn_id"],
                "document_epoch": 1,
                "expected_revision": expected_revision,
                "profile_version": "CanvasOperationProfileV1",
                "operation_payload": {
                    "kind": "stroke",
                    "points": [
                        {"x": 0.1, "y": 0.2},
                        {"x": 0.3 + expected_revision / 10, "y": 0.4},
                    ],
                    "color": "#FFD21F",
                    "size": 5,
                },
            },
        )
        assert response.status_code == 200, response.text
    return session_id, child_id, group_id, grant_id, device_key, operation_ids


def _ga2_prepare(harness: PilotHarness):
    """T4/T5 synthetic data with the approved fixed pilot purpose, no consent row."""
    from sketch2life.infrastructure.assistance.pilot_policy import PILOT_SYNTHETIC_POLICY_V1
    from sketch2life.interfaces.http.be1_runtime import get_verified_device
    from sketch2life.interfaces.http.routers.be1_artifacts import create_canvas_render_handoff

    session_id, child_id, canvas_id, grant_id, key, _ = _t4_append_two_strokes(harness)
    with harness.session_factory.begin() as db:
        session = db.get(ClassroomSessionModel, session_id)
        proof = db.scalar(
            select(SyntheticEligibilityProofModel).where(
                SyntheticEligibilityProofModel.child_profile_id == child_id,
                SyntheticEligibilityProofModel.session_id == session_id,
            )
        )
        assert session is not None and proof is not None
        purpose = PILOT_SYNTHETIC_POLICY_V1.purpose_code
        session.configuration = {**session.configuration, "purpose_ref": purpose}
        proof.purpose_ref = purpose
    with harness.session_factory() as db:
        device = get_verified_device(
            grant_id=grant_id, device_key=key, db=db, runtime=harness.runtime
        )
        handoff = create_canvas_render_handoff(db, harness.runtime, device)
    return session_id, child_id, canvas_id, handoff


def _ga2_ports(harness: PilotHarness, connection: Connection, session_id: str):
    from sketch2life.infrastructure.assistance.be1_canvas_source_adapter import (
        PostgresCanvasSourceAdapter,
    )
    from sketch2life.infrastructure.assistance.be1_owner_adapter import (
        PostgresAssistanceOwnerAdapter,
    )
    from sketch2life.interfaces.http.routers.be1_canvas import build_canvas_source_export

    def export(organization_id: str, canvas_id: str):
        with Session(bind=connection) as db:
            return build_canvas_source_export(
                db,
                organization_id=organization_id,
                session_id=session_id,
                canvas_id=canvas_id,
                document_epoch=1,
            )

    owner = PostgresAssistanceOwnerAdapter(
        connection,
        organization_id=harness.organization_id,
        class_id=harness.class_id,
        session_id=session_id,
        environment="test",
        pilot_enabled=True,
        export_source=export,
    )
    sources = PostgresCanvasSourceAdapter(
        connection,
        session_id=session_id,
        export_source=export,
        load_artifact=harness.runtime.artifact_store.get,
        environment="test",
        pilot_enabled=True,
    )
    return owner, sources


def _ga2_request(
    harness: PilotHarness,
    connection: Connection,
    session_id,
    child_id,
    canvas_id,
    handoff,
    *,
    repository=None,
):
    from dataclasses import replace

    from sketch2life.application.ports.ai_jobs import Principal, PrincipalRole
    from sketch2life.application.services.assistance import AssistanceService, SubmitCommand
    from sketch2life.domain.assistance import (
        ActorKind,
        CheckpointRef,
        RequestReason,
        TargetKind,
        TargetScope,
    )
    from sketch2life.infrastructure.assistance.fakes import TeacherScope
    from sketch2life.infrastructure.assistance.harness import build_assistance_harness
    from sketch2life.infrastructure.assistance.pilot_policy import PilotSyntheticPolicy

    owner, sources = _ga2_ports(harness, connection, session_id)
    canvas = owner.canvas(harness.organization_id, canvas_id)
    assert canvas is not None
    assert owner.current_turn(canvas_id) is not None
    fake = build_assistance_harness(auto_schedule=False)
    principal = Principal(harness.adult_subject, harness.organization_id, PrincipalRole.TEACHER)
    fake.authority.teachers[principal.principal_id] = TeacherScope(
        harness.organization_id, frozenset({harness.class_id})
    )
    service = AssistanceService(
        replace(
            fake.service._d,
            owner=owner,
            sources=sources,
            policy=PilotSyntheticPolicy(environment="test", pilot_enabled=True),
            repository=repository if repository is not None else fake.service._d.repository,
        )
    )
    command = SubmitCommand(
        principal=principal,
        idempotency_key="synthetic-ga2",
        canvas_id=canvas_id,
        checkpoint_ref=CheckpointRef(handoff.source_ref, 1, 3, handoff.source_sha256),
        target=TargetScope(TargetKind.INDIVIDUAL, child_id),
        region_id=None,
        requested_level="level_fx_1",
        child_intent=None,
        request_reason=RequestReason.TEACHER_REQUEST,
        context_revision=canvas.context_revision,
        client_request_id="synthetic-ga2-client",
    )
    if repository is not None:
        # The SQL pilot intentionally does not implement cache reads. Build the request
        # through the real owner/source/policy resolution and persist it through the real
        # SQL repository, without substituting a fake repository or changing product code.
        resolution = service._resolve_for(command, ActorKind.TEACHER)
        request = service._new_request(
            command,
            ActorKind.TEACHER,
            resolution,
            service._d.clock.now(),
            cache=None,
        )
        with repository.transaction() as unit:
            unit.insert(request)
        return service, request
    return service, service.submit(command).request


def _ga2_real_job_acceptance(
    harness: PilotHarness,
    session_id: str,
    child_id: str,
    canvas_id: str,
    handoff,
    *,
    before_hold=None,
    before_commit=None,
    lock_timeout_ms: int = 1000,
):
    """Build a test-only real-SQL acceptance path over this fixture's real BE1 facts."""
    import json
    from contextlib import contextmanager
    from dataclasses import replace
    from uuid import uuid4

    from sketch2life.application.ports.ai_jobs import (
        OWNER_FENCE_CONTRACT,
        AuthorizationAction,
        AuthorizationDecision,
        EligibilityDecision,
        FenceResult,
        OwnerFence,
        Principal,
        PrincipalRole,
    )
    from sketch2life.application.services.ai_jobs import AiJobService, CreateJobCommand
    from sketch2life.domain.ai_jobs.model import RequestRef
    from sketch2life.infrastructure.ai_jobs.harness import build_fixture_harness
    from sketch2life.infrastructure.ai_jobs.sql import tables as job_tables
    from sketch2life.infrastructure.ai_jobs.sql.repository import SqlAiJobRepository
    from sketch2life.infrastructure.assistance.owner_fence import (
        build_owner_fence,
        owner_fence_factory,
    )
    from sketch2life.infrastructure.assistance.sql_repository import SqlAssistanceRepository
    from sqlalchemy import select

    engine = harness.runtime.engine
    assert engine is not None

    class TrackedSqlAssistanceRepository(SqlAssistanceRepository):
        def __init__(self, db_engine: Engine, organization_id: str) -> None:
            super().__init__(db_engine, organization_id)
            self.transaction_count = 0

        @contextmanager
        def transaction(self):
            self.transaction_count += 1
            with super().transaction() as unit:
                yield unit

    assistance_repository = TrackedSqlAssistanceRepository(engine, harness.organization_id)
    with engine.connect() as connection:
        assistance_service, request = _ga2_request(
            harness,
            connection,
            session_id,
            child_id,
            canvas_id,
            handoff,
            repository=assistance_repository,
        )

    principal = Principal(harness.adult_subject, harness.organization_id, PrincipalRole.ADMIN)
    from sketch2life.infrastructure.assistance.be1_owner_adapter import (
        PostgresAssistanceOwnerAdapter,
    )

    assert isinstance(assistance_service._d.owner, PostgresAssistanceOwnerAdapter)
    assert assistance_service._d.repository is assistance_repository
    probe: dict[str, Any] = {
        "hold_connections": [],
        "resolver_connections": [],
        "resolver_transaction_counts": [],
        "held_batches": [],
    }

    def _auth_payload(fence: OwnerFence) -> dict[str, Any] | None:
        prefix = "ga2-test-auth-v1:"
        if not fence.fence_scope.startswith(prefix) or fence.epoch != 1:
            return None
        try:
            payload = json.loads(fence.fence_scope[len(prefix) :])
        except (TypeError, ValueError):
            return None
        if not isinstance(payload, dict) or payload.get("version") != "ga2-test-auth-v1":
            return None
        return payload

    def _auth_rows_current(connection: Connection, fence: OwnerFence) -> bool:
        payload = _auth_payload(fence)
        if payload is None:
            return False
        if (
            payload.get("organization_id") != harness.organization_id
            or payload.get("subject") != harness.adult_subject
            or payload.get("role") != PrincipalRole.ADMIN.value
        ):
            return False
        identity = connection.execute(
            select(AdultIdentityModel.subject)
            .where(
                AdultIdentityModel.subject == payload["subject"],
                AdultIdentityModel.state == "active",
            )
            .with_for_update(read=True)
        ).scalar_one_or_none()
        assignment = connection.execute(
            select(OrganizationAssignmentModel.assignment_id)
            .where(
                OrganizationAssignmentModel.assignment_id == payload["assignment_id"],
                OrganizationAssignmentModel.organization_id == payload["organization_id"],
                OrganizationAssignmentModel.subject == payload["subject"],
                OrganizationAssignmentModel.class_id.is_(None),
                OrganizationAssignmentModel.role == "school_admin",
                OrganizationAssignmentModel.active.is_(True),
            )
            .with_for_update(read=True)
        ).scalar_one_or_none()
        return identity == payload["subject"] and assignment == payload["assignment_id"]

    class PgAuthorization:
        def decide(self, decision_principal, action, scope):
            if (
                action is not AuthorizationAction.CREATE_JOB
                or decision_principal != principal
                or scope.organization_id != harness.organization_id
                or scope.session_id != session_id
                or scope.subject_refs != (child_id,)
            ):
                return AuthorizationDecision(False, "FORBIDDEN_SCOPE")
            with engine.connect() as connection:
                identity = connection.execute(
                    select(AdultIdentityModel.subject).where(
                        AdultIdentityModel.subject == harness.adult_subject,
                        AdultIdentityModel.state == "active",
                    )
                ).scalar_one_or_none()
                assignment = connection.execute(
                    select(OrganizationAssignmentModel.assignment_id)
                    .where(
                        OrganizationAssignmentModel.organization_id == harness.organization_id,
                        OrganizationAssignmentModel.subject == harness.adult_subject,
                        OrganizationAssignmentModel.class_id.is_(None),
                        OrganizationAssignmentModel.role == "school_admin",
                        OrganizationAssignmentModel.active.is_(True),
                    )
                    .order_by(OrganizationAssignmentModel.assignment_id)
                    .limit(1)
                ).scalar_one_or_none()
            if identity != harness.adult_subject or assignment is None:
                return AuthorizationDecision(False, "FORBIDDEN_SCOPE")
            payload = {
                "version": "ga2-test-auth-v1",
                "organization_id": harness.organization_id,
                "subject": harness.adult_subject,
                "assignment_id": assignment,
                "role": PrincipalRole.ADMIN.value,
                "action": str(action),
                "session_id": scope.session_id,
                "target_id": scope.target_id,
                "purpose_code": scope.purpose_code,
                "subject_refs": list(scope.subject_refs),
            }
            encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
            return AuthorizationDecision(
                True,
                fence=OwnerFence("ga2-test-auth-v1:" + encoded, 1),
            )

    class PgEligibility:
        def check(self, *, scope, request_ref, job_type):
            if job_type != "sketch_assistance":
                return EligibilityDecision(False, "STALE_CONTEXT", 0)
            with assistance_repository.transaction() as unit:
                current_request = unit.get(request_ref.request_id)
            if current_request is None:
                return EligibilityDecision(False, "STALE_CONTEXT", 0)
            if (
                current_request.facts.organization_id != scope.organization_id
                or current_request.facts.session_id != scope.session_id
                or current_request.facts.audience != scope.subject_refs
                or current_request.facts.purpose_code != scope.purpose_code
                or current_request.request_revision != request_ref.request_revision
                or current_request.facts.source.input_hash != request_ref.input_hash
                or current_request.facts.context_revision != request_ref.context_revision
            ):
                return EligibilityDecision(False, "STALE_CONTEXT", 0)
            with engine.connect() as connection:
                owner, sources = _ga2_ports(harness, connection, session_id)
                facts = assistance_service.current_resolved_facts(
                    current_request.assistance_id,
                    request=current_request,
                    owner=owner,
                    sources=sources,
                )
            if facts is None or facts.digest() != current_request.assistance_context_digest:
                return EligibilityDecision(False, "STALE_CONTEXT", 0)
            return EligibilityDecision(
                True,
                None,
                facts.context_revision,
                build_owner_fence(facts),
            )

    def resolver(connection: Connection, fence_scope):
        before_count = assistance_repository.transaction_count
        probe["resolver_connections"].append(connection)
        owner, sources = _ga2_ports(harness, connection, fence_scope.session_id)
        current_facts = assistance_service.current_resolved_facts(
            request.assistance_id,
            request=request,
            owner=owner,
            sources=sources,
        )
        probe["resolver_transaction_counts"].append(
            (before_count, assistance_repository.transaction_count)
        )
        assert assistance_repository.transaction_count == before_count
        return current_facts

    def owner_fences(connection: Connection):
        class CombinedOwnerFence:
            contract_version = OWNER_FENCE_CONTRACT

            def __init__(self) -> None:
                self.connection = connection
                self.be1_fence = owner_fence_factory(resolver, lock_timeout_ms=lock_timeout_ms)(
                    connection
                )

            def hold(self, fences):
                probe["hold_connections"].append(self.connection)
                probe["held_batches"].append(fences)
                if before_hold is not None:
                    before_hold(self.connection)
                auth_fences = tuple(
                    fence for fence in fences if fence.fence_scope.startswith("ga2-test-auth-v1:")
                )
                fact_fences = tuple(fence for fence in fences if fence not in auth_fences)
                if (
                    len(auth_fences) != 1
                    or len(fact_fences) != 1
                    or not _auth_rows_current(self.connection, auth_fences[0])
                ):
                    return FenceResult(False, fences)
                return self.be1_fence.hold(fact_fences)

        return CombinedOwnerFence()

    job_harness = build_fixture_harness()
    ai_repository = SqlAiJobRepository(
        engine,
        owner_fences,
        before_commit=before_commit,
    )

    class SyntheticIds:
        def new_id(self, prefix: str) -> str:
            return f"synthetic-{prefix}-{uuid4().hex}"

    ai_service = AiJobService(
        replace(
            job_harness.service._d,
            repository=ai_repository,
            authorization=PgAuthorization(),
            eligibility=PgEligibility(),
            ids=SyntheticIds(),
        )
    )
    command = CreateJobCommand(
        principal=principal,
        idempotency_key=f"synthetic-create-{uuid4().hex}",
        job_type="sketch_assistance",
        target_id=request.assistance_id,
        purpose_code=request.facts.purpose_code,
        session_id=request.facts.session_id,
        subject_refs=request.facts.audience,
        request_ref=RequestRef(
            request.assistance_id,
            request.request_revision,
            request.facts.source.input_hash,
            request.facts.context_revision,
        ),
        correlation_id=f"synthetic-correlation-{uuid4().hex}",
    )
    return ai_service, command, request, assistance_repository, probe, job_tables


def _ga2_assert_no_accepted_job(engine: Engine, organization_id: str) -> None:
    from sketch2life.infrastructure.ai_jobs.sql import tables as t
    from sqlalchemy import func, select

    with engine.connect() as connection:
        counts = {
            "jobs": connection.scalar(
                select(func.count())
                .select_from(t.job)
                .where(t.job.c.organization_id == organization_id)
            ),
            "receipts": connection.scalar(
                select(func.count())
                .select_from(t.command_receipt)
                .where(t.command_receipt.c.organization_id == organization_id)
            ),
            "semantics": connection.scalar(
                select(func.count())
                .select_from(t.semantic_request)
                .where(t.semantic_request.c.organization_id == organization_id)
            ),
            "outbox": connection.scalar(
                select(func.count())
                .select_from(t.outbox)
                .where(t.outbox.c.organization_id == organization_id)
            ),
        }
    assert counts == {"jobs": 0, "receipts": 0, "semantics": 0, "outbox": 0}


def test_ga2_real_ai_job_acceptance_holds_both_fences_on_one_connection(pilot_harness):
    from sketch2life.infrastructure.assistance.owner_fence import decode_owner_fence_scope
    from sqlalchemy import select

    h = pilot_harness
    session_id, child_id, canvas_id, handoff = _ga2_prepare(h)
    service, command, request, _assistance_repository, probe, job_tables = _ga2_real_job_acceptance(
        h, session_id, child_id, canvas_id, handoff
    )

    result = service.create_job(command)
    engine = h.runtime.engine
    assert engine is not None
    with engine.connect() as connection:
        attempt_ids = connection.execute(
            select(job_tables.attempt.c.attempt_id).where(
                job_tables.attempt.c.job_id == result.job_id
            )
        ).scalars().all()
    h.created_ai_jobs.append((result.job_id, tuple(attempt_ids)))
    assert len(attempt_ids) == 1
    assert result.outcome == "created"
    assert len(probe["held_batches"]) == 1
    assert len(probe["held_batches"][0]) == 2
    assert len(probe["resolver_connections"]) == 1
    assert probe["resolver_connections"][0] is probe["hold_connections"][0]
    assert probe["resolver_transaction_counts"]
    assert all(before == after for before, after in probe["resolver_transaction_counts"])

    with engine.connect() as connection:
        row = connection.execute(
            select(job_tables.job.c.accepted_fences).where(
                job_tables.job.c.job_id == result.job_id,
                job_tables.job.c.organization_id == h.organization_id,
            )
        ).scalar_one()
        accepted_fences = row
        assert len(accepted_fences) == 2
        auth_keys = [key for key in accepted_fences if key.startswith("ga2-test-auth-v1:")]
        owner_keys = [key for key in accepted_fences if decode_owner_fence_scope(key) is not None]
        assert len(auth_keys) == 1 and len(owner_keys) == 1
        assert (
            connection.execute(
                select(job_tables.command_receipt.c.job_id).where(
                    job_tables.command_receipt.c.organization_id == h.organization_id,
                    job_tables.command_receipt.c.target_id == request.assistance_id,
                )
            ).scalar_one()
            == result.job_id
        )


def test_ga2_real_ai_job_stale_owner_change_fails_closed_before_acceptance(pilot_harness):
    from sketch2life.application.services.ai_jobs import AiJobError
    from sqlalchemy import update

    h = pilot_harness
    session_id, child_id, canvas_id, handoff = _ga2_prepare(h)
    engine = h.runtime.engine
    assert engine is not None
    changed = False

    def change_facts_before_owner_hold(_connection: Connection) -> None:
        nonlocal changed
        if changed:
            return
        with engine.begin() as writer:
            writer.execute(
                update(ManagedProfileModel)
                .where(ManagedProfileModel.child_id == child_id)
                .values(age_revision=ManagedProfileModel.age_revision + 1)
            )
        changed = True

    service, command, _request, _assistance_repository, probe, _job_tables = (
        _ga2_real_job_acceptance(
            h,
            session_id,
            child_id,
            canvas_id,
            handoff,
            before_hold=change_facts_before_owner_hold,
        )
    )
    with pytest.raises(AiJobError):
        service.create_job(command)
    assert changed
    assert probe["resolver_connections"]
    assert probe["resolver_connections"][0] is probe["hold_connections"][0]
    _ga2_assert_no_accepted_job(engine, h.organization_id)


def test_ga2_real_ai_job_owner_lock_timeout_fails_closed(pilot_harness):
    from concurrent.futures import ThreadPoolExecutor

    from sketch2life.application.services.ai_jobs import AiJobError
    from sqlalchemy import select

    h = pilot_harness
    session_id, child_id, canvas_id, handoff = _ga2_prepare(h)
    engine = h.runtime.engine
    assert engine is not None
    service, command, _request, _assistance_repository, _probe, _job_tables = (
        _ga2_real_job_acceptance(
            h,
            session_id,
            child_id,
            canvas_id,
            handoff,
            lock_timeout_ms=100,
        )
    )

    with ThreadPoolExecutor(max_workers=1) as pool, engine.begin() as blocker:
        blocker.execute(
            select(ManagedProfileModel.child_id)
            .where(ManagedProfileModel.child_id == child_id)
            .with_for_update()
        ).scalar_one()
        future = pool.submit(service.create_job, command)
        with pytest.raises(AiJobError):
            future.result(timeout=15)
    _ga2_assert_no_accepted_job(engine, h.organization_id)


def test_ga2_real_ai_job_acceptance_transaction_failure_rolls_back_all_rows(pilot_harness):
    h = pilot_harness
    session_id, child_id, canvas_id, handoff = _ga2_prepare(h)
    engine = h.runtime.engine
    assert engine is not None
    injected = False

    def fail_before_commit(unit) -> None:
        nonlocal injected
        if unit.writes and not injected:
            injected = True
            raise RuntimeError("synthetic acceptance rollback")

    service, command, _request, _assistance_repository, _probe, _job_tables = (
        _ga2_real_job_acceptance(
            h,
            session_id,
            child_id,
            canvas_id,
            handoff,
            before_commit=fail_before_commit,
        )
    )
    with pytest.raises(RuntimeError, match="synthetic acceptance rollback"):
        service.create_job(command)
    assert injected
    _ga2_assert_no_accepted_job(engine, h.organization_id)


def test_ga2_t2c_source_and_context_use_real_scoped_facts(pilot_harness):
    from sketch2life.domain.eligibility import EligibilityBasis, EligibilityScope
    from sketch2life.domain.vision_analysis import ProviderContextMode
    from sketch2life.infrastructure.assistance.be1_fact_reader import BE1FactReader, BE1FactRequest
    from sketch2life.infrastructure.assistance.postgres_fact_source import PostgresBE1FactSource
    from sketch2life.infrastructure.vision_analysis.resolved_facts_context import (
        ResolvedFactsAnalysisContext,
    )

    h = pilot_harness
    session_id, child_id, canvas_id, handoff = _ga2_prepare(h)
    assert h.runtime.engine is not None
    with h.runtime.engine.begin() as connection:
        from sqlalchemy import insert

        proof_table = SyntheticEligibilityProofModel.__table__
        historical = dict(
            connection.execute(
                select(proof_table).where(
                    proof_table.c.child_profile_id == child_id,
                    proof_table.c.session_id == session_id,
                )
            )
            .mappings()
            .one()
        )
        historical.update(
            evidence_id=_synthetic_id(),
            session_id=_synthetic_id(),
            run_ref="synthetic-historical-run",
        )
        connection.execute(insert(proof_table).values(**historical))
        source = PostgresBE1FactSource(connection, environment="test", pilot_enabled=True)
        purpose = "ai_drawing_assistance"
        read = BE1FactReader(source).read(
            BE1FactRequest(
                h.organization_id,
                h.class_id,
                session_id,
                child_id,
                purpose,
                (child_id,),
                ProviderContextMode.IMAGE_ONLY,
            )
        )
        assert source.statements == 1 and read.member is not None
        assert read.member.eligibility_basis == EligibilityBasis.SYNTHETIC_DEV
        assert not read.member.consent_effective and read.member.consent_record_ref is None
        owner, _ = _ga2_ports(h, connection, session_id)
        assert owner.members(h.organization_id, (child_id,), purpose) == ()
        assert owner.members(
            h.organization_id,
            (child_id,),
            purpose,
            scope=EligibilityScope(h.organization_id, h.class_id, child_id, purpose),
        )
        service, request = _ga2_request(h, connection, session_id, child_id, canvas_id, handoff)
        pin = service.pin(request.assistance_id)
        assert pin is not None and pin.context_digest == "sha256:" + request.facts.digest()
        context = ResolvedFactsAnalysisContext(service.current_resolved_facts).current_for_pin(pin)
        assert context.context_digest == pin.context_digest
        assert context.context_revision == pin.context_revision
        assert read.context is not None and read.context.context_digest != context.context_digest
        assert not context.consent_effective and not context.purpose_granted


@pytest.mark.parametrize(
    "changed", ["purpose", "run", "expired", "revoked", "profile", "membership", "group", "origin"]
)
def test_ga2_t2c_invalid_current_facts_fail_closed(pilot_harness, changed):
    from sketch2life.domain.vision_analysis import ProviderContextMode
    from sketch2life.infrastructure.assistance.be1_fact_reader import BE1FactReader, BE1FactRequest
    from sketch2life.infrastructure.assistance.postgres_fact_source import PostgresBE1FactSource
    from sketch2life.infrastructure.persistence.be1_models import SessionGroupModel

    h = pilot_harness
    session_id, child_id, canvas_id, _ = _ga2_prepare(h)
    with h.session_factory.begin() as db:
        session = db.get(ClassroomSessionModel, session_id)
        profile = db.get(ManagedProfileModel, child_id)
        proof = db.scalar(
            select(SyntheticEligibilityProofModel).where(
                SyntheticEligibilityProofModel.child_profile_id == child_id
            )
        )
        membership = db.scalar(
            select(SessionMembershipModel).where(SessionMembershipModel.child_id == child_id)
        )
        assert session and profile and proof and membership
        if changed == "purpose":
            session.configuration = {**session.configuration, "purpose_ref": "wrong-purpose"}
        elif changed == "run":
            session.configuration = {**session.configuration, "pilot_run_ref": "wrong-run"}
        elif changed == "expired":
            proof.issued_at = datetime.now(UTC) - timedelta(hours=2)
            proof.expires_at = datetime.now(UTC) - timedelta(hours=1)
        elif changed == "revoked":
            proof.revoked_at = datetime.now(UTC)
            proof.revocation_revision = 1
        elif changed == "profile":
            profile.state = "inactive"
        elif changed == "membership":
            membership.state = "left"
        elif changed == "origin":
            profile.data_origin = "LEGACY_UNCLASSIFIED"
        else:
            group = db.get(SessionGroupModel, canvas_id)
            assert group
            group.state = "archived"
    assert h.runtime.engine is not None
    with h.runtime.engine.begin() as connection:
        source = PostgresBE1FactSource(connection, environment="test", pilot_enabled=True)
        result = BE1FactReader(source).read(
            BE1FactRequest(
                h.organization_id,
                h.class_id,
                session_id,
                child_id,
                "ai_drawing_assistance",
                (child_id,),
                ProviderContextMode.IMAGE_ONLY,
            )
        )
        assert result.member is None and source.statements == 1


def test_ga2_t7b_share_fence_blocks_be1_update_until_transaction_ends(pilot_harness):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from time import monotonic

    from sketch2life.infrastructure.assistance.owner_fence import (
        build_owner_fence,
        owner_fence_factory,
    )
    from sqlalchemy import text, update

    h = pilot_harness
    session_id, child_id, canvas_id, handoff = _ga2_prepare(h)
    engine = h.runtime.engine
    assert engine is not None
    with engine.begin() as connection:
        service, request = _ga2_request(h, connection, session_id, child_id, canvas_id, handoff)

        def resolve(same_connection, scope):
            assert same_connection is connection
            owner, sources = _ga2_ports(h, same_connection, scope.session_id)
            return service.current_resolved_facts(
                request.assistance_id, request=request, owner=owner, sources=sources
            )

        fence = build_owner_fence(request.facts)
        held = owner_fence_factory(resolve)(connection).hold((fence,))
        assert held.current and not held.stale
    ready = Event()
    pid = []

    def writer():
        with engine.begin() as other:
            other.execute(text("SET LOCAL lock_timeout = '4000ms'"))
            pid.append(other.scalar(text("SELECT pg_backend_pid()")))
            ready.set()
            other.execute(
                update(ManagedProfileModel)
                .where(ManagedProfileModel.child_id == child_id)
                .values(age_revision=2)
            )

    with ThreadPoolExecutor(max_workers=1) as pool:
        with engine.begin() as connection:
            owner, sources = _ga2_ports(h, connection, session_id)

            def resolve(conn, scope):
                owner, sources = _ga2_ports(h, conn, scope.session_id)
                return service.current_resolved_facts(
                    request.assistance_id, request=request, owner=owner, sources=sources
                )

            assert owner_fence_factory(resolve)(connection).hold((fence,)).current
            future = pool.submit(writer)
            assert ready.wait(2)
            blocked = False
            deadline = monotonic() + 2
            with engine.connect() as observer:
                while monotonic() < deadline:
                    if observer.scalar(
                        text("SELECT cardinality(pg_blocking_pids(:pid))"), {"pid": pid[0]}
                    ):
                        blocked = True
                        break
            assert blocked and not future.done()
        future.result(timeout=3)
    with engine.begin() as connection:
        assert not owner_fence_factory(resolve)(connection).hold((fence,)).current


def test_ga2_t7b_new_membership_insert_is_not_blocked_and_digest_becomes_stale(pilot_harness):
    from sketch2life.infrastructure.assistance.owner_fence import (
        build_owner_fence,
        owner_fence_factory,
    )
    from sqlalchemy import insert, text

    h = pilot_harness
    session_id, child_id, canvas_id, handoff = _ga2_prepare(h)
    engine = h.runtime.engine
    assert engine is not None
    with engine.begin() as connection:
        service, request = _ga2_request(h, connection, session_id, child_id, canvas_id, handoff)

        def resolve(conn, scope):
            owner, sources = _ga2_ports(h, conn, scope.session_id)
            return service.current_resolved_facts(
                request.assistance_id, request=request, owner=owner, sources=sources
            )

        fence = build_owner_fence(request.facts)
        guard = owner_fence_factory(resolve)(connection)
        assert guard.hold((fence,)).current
        with engine.begin() as other:
            other.execute(text("SET LOCAL lock_timeout = '500ms'"))
            other.execute(
                insert(SessionMembershipModel).values(
                    membership_id=_synthetic_id(),
                    organization_id=h.organization_id,
                    class_id=h.class_id,
                    session_id=session_id,
                    child_id=_synthetic_id(),
                    group_id=canvas_id,
                    state="admitted",
                )
            )
        result = guard.hold((fence,))
        assert not result.current and result.stale == (fence,)


def test_ga2_t7b_database_lock_timeout_returns_stale(pilot_harness):
    from sketch2life.infrastructure.assistance.owner_fence import (
        build_owner_fence,
        owner_fence_factory,
    )

    h = pilot_harness
    session_id, child_id, canvas_id, handoff = _ga2_prepare(h)
    engine = h.runtime.engine
    assert engine is not None
    with engine.begin() as connection:
        service, request = _ga2_request(h, connection, session_id, child_id, canvas_id, handoff)
        fence = build_owner_fence(request.facts)

    def resolve(conn, scope):
        owner, sources = _ga2_ports(h, conn, scope.session_id)
        return service.current_resolved_facts(
            request.assistance_id, request=request, owner=owner, sources=sources
        )

    with engine.begin() as writer:
        writer.execute(
            select(ManagedProfileModel.child_id)
            .where(ManagedProfileModel.child_id == child_id)
            .with_for_update()
        )
        with engine.begin() as accepting:
            result = owner_fence_factory(resolve, lock_timeout_ms=100)(accepting).hold((fence,))
            assert not result.current and result.stale == (fence,)


def test_t4_authoritative_export_binds_complete_ordered_operations_and_hashes(
    pilot_harness: PilotHarness,
) -> None:
    import hashlib
    import json

    from sketch2life.interfaces.http.routers.be1_canvas import build_canvas_source_export

    harness = pilot_harness
    session_id, _child_id, group_id, _grant_id, _device_key, operation_ids = _t4_append_two_strokes(
        harness
    )
    with harness.session_factory() as db:
        exported = build_canvas_source_export(
            db,
            organization_id=harness.organization_id,
            session_id=session_id,
            canvas_id=group_id,
            document_epoch=1,
        )
        repeated = build_canvas_source_export(
            db,
            organization_id=harness.organization_id,
            session_id=session_id,
            canvas_id=group_id,
            document_epoch=1,
        )

    assert exported.document_revision == 3
    assert [item.resulting_revision for item in exported.operations] == [2, 3]
    assert [item.operation_id for item in exported.operations] == operation_ids
    assert [item.operation_id for item in exported.operation_manifest] == operation_ids
    assert all(item.document_epoch == 1 for item in exported.operations)
    expected_operations = [
        {
            "operation_id": item.operation_id,
            "participant_id": item.participant_id,
            "document_epoch": item.document_epoch,
            "resulting_revision": item.resulting_revision,
            "operation_payload": item.operation_payload,
        }
        for item in exported.operations
    ]

    def canonical_json(value: Any) -> bytes:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )

    expected_manifest = [item.model_dump(mode="json") for item in exported.operation_manifest]
    manifest_sha256 = hashlib.sha256(canonical_json(expected_manifest)).hexdigest()
    document_sha256 = hashlib.sha256(
        canonical_json(
            {
                "canvas_id": group_id,
                "document_epoch": 1,
                "document_revision": 3,
                "operations": expected_operations,
            }
        )
    ).hexdigest()
    source_sha256 = hashlib.sha256(
        canonical_json(
            {
                "contract": "CanvasSourceExportV1",
                "organization_id": harness.organization_id,
                "session_id": session_id,
                "canvas_id": group_id,
                "profile_id": "canvas-operation-profile-v1",
                "profile_version": "CanvasOperationProfileV1",
                "document_epoch": 1,
                "document_revision": 3,
                "canonical_document_sha256": document_sha256,
                "operation_manifest_sha256": manifest_sha256,
            }
        )
    ).hexdigest()
    assert [
        hashlib.sha256(canonical_json(item.operation_payload)).hexdigest()
        for item in exported.operations
    ] == [item.payload_sha256 for item in exported.operations]
    assert manifest_sha256 == exported.operation_manifest_sha256
    assert document_sha256 == exported.canonical_document_sha256
    assert source_sha256 == exported.source_sha256
    assert exported.source_ref == f"be1-canvas-source-v1:{exported.source_sha256}"
    assert repeated == exported


@pytest.mark.parametrize(
    "history_problem", ["revision_gap", "mixed_epoch", "bad_profile", "checkpoint"]
)
def test_t4_unprovable_history_fails_closed_without_partial_export(
    pilot_harness: PilotHarness, history_problem: str
) -> None:
    from fastapi import HTTPException
    from sketch2life.infrastructure.persistence.core_models import (
        CoreCanvasCheckpointModel,
        CoreCanvasOperationModel,
    )
    from sketch2life.interfaces.http.routers.be1_canvas import build_canvas_source_export
    from sqlalchemy import update

    harness = pilot_harness
    session_id, _child_id, group_id, _grant_id, _device_key, operation_ids = _t4_append_two_strokes(
        harness
    )
    with harness.session_factory.begin() as db:
        if history_problem == "revision_gap":
            db.execute(
                update(CoreCanvasOperationModel)
                .where(CoreCanvasOperationModel.operation_id == operation_ids[0])
                .values(resulting_revision=4)
            )
        elif history_problem == "mixed_epoch":
            row = db.get(CoreCanvasOperationModel, operation_ids[0])
            assert row is not None
            row.document_epoch = 2
        elif history_problem == "bad_profile":
            row = db.get(CoreCanvasOperationModel, operation_ids[0])
            assert row is not None
            row.operation_payload = {
                **row.operation_payload,
                "canvas_operation_profile_id": "synthetic-unrecognized-profile",
            }
        else:
            db.add(
                CoreCanvasCheckpointModel(
                    checkpoint_id=_synthetic_id(),
                    organization_id=harness.organization_id,
                    canvas_id=group_id,
                    document_epoch=1,
                    revision=3,
                    through_operation_id=operation_ids[-1],
                    checksum_sha256="e" * 64,
                    storage_ref=f"synthetic-checkpoint-{_synthetic_uuid_token()}",
                )
            )

    with harness.session_factory() as db, pytest.raises(HTTPException) as refused:
        build_canvas_source_export(
            db,
            organization_id=harness.organization_id,
            session_id=session_id,
            canvas_id=group_id,
            document_epoch=1,
        )
    assert refused.value.status_code == 409
    assert "CANVAS_SOURCE_UNAVAILABLE" in str(refused.value.detail)


def test_t5_render_handoff_persists_private_png_and_admission_receipt(
    pilot_harness: PilotHarness,
) -> None:
    import hashlib
    import json

    from sketch2life.infrastructure.persistence.core_models import CoreAssetMetadataModel
    from sketch2life.interfaces.http.be1_runtime import get_verified_device
    from sketch2life.interfaces.http.routers.be1_artifacts import create_canvas_render_handoff
    from sqlalchemy import select

    harness = pilot_harness
    session_id, _child_id, _group_id, grant_id, device_key, _operation_ids = _t4_append_two_strokes(
        harness
    )
    with harness.session_factory() as db:
        device = get_verified_device(
            grant_id=grant_id,
            device_key=device_key,
            db=db,
            runtime=harness.runtime,
        )
        handoff = create_canvas_render_handoff(db, harness.runtime, device)

    png_bytes = harness.runtime.artifact_store.get(handoff.render_artifact_ref)
    receipt_bytes = harness.runtime.artifact_store.get(handoff.receipt_artifact_ref)
    assert png_bytes is not None and receipt_bytes is not None
    assert hashlib.sha256(png_bytes).hexdigest() == handoff.render_sha256
    receipt = json.loads(receipt_bytes)
    assert receipt["outcome"] == "ADMITTED"
    assert receipt["source_ref"] == handoff.source_ref
    assert receipt["source_sha256"] == handoff.source_sha256
    assert receipt["render_artifact_ref"] == handoff.render_artifact_ref
    assert receipt["render_sha256"] == handoff.render_sha256
    assert receipt["render_source_binding_sha256"] == handoff.render_source_binding_sha256
    assert (receipt["width"], receipt["height"], receipt["mode"]) == (1024, 1024, "RGB")
    assert receipt["decoder_pixel_format"]
    receipt_hash = receipt.pop("receipt_binding_sha256")
    assert (
        hashlib.sha256(
            json.dumps(receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
                "utf-8"
            )
        ).hexdigest()
        == receipt_hash
    )
    assert hashlib.sha256(receipt_bytes).hexdigest() == handoff.receipt_sha256

    with harness.session_factory() as db:
        image_metadata = db.scalar(
            select(CoreAssetMetadataModel).where(
                CoreAssetMetadataModel.organization_id == harness.organization_id,
                CoreAssetMetadataModel.asset_ref == handoff.render_artifact_ref,
            )
        )
        receipt_metadata = db.scalar(
            select(CoreAssetMetadataModel).where(
                CoreAssetMetadataModel.organization_id == harness.organization_id,
                CoreAssetMetadataModel.asset_ref == handoff.receipt_artifact_ref,
            )
        )
    assert image_metadata is not None and receipt_metadata is not None
    assert f"be1-session:{session_id}" in image_metadata.source_refs
    assert image_metadata.content_sha256 == handoff.render_sha256
    assert image_metadata.derived_from_ref == handoff.source_ref
    assert receipt_metadata.content_sha256 == handoff.receipt_sha256
    assert receipt_metadata.derived_from_ref == handoff.render_artifact_ref


def test_t5_render_handoff_removes_only_new_artifacts_on_metadata_commit_failure(
    pilot_harness: PilotHarness,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import sketch2life.interfaces.http.routers.be1_artifacts as artifact_routes
    from sketch2life.interfaces.http.be1_runtime import get_verified_device
    from sketch2life.interfaces.http.routers.be1_artifacts import create_canvas_render_handoff

    harness = pilot_harness
    _session_id, _child_id, _group_id, grant_id, device_key, _operation_ids = (
        _t4_append_two_strokes(harness)
    )
    from sketch2life.infrastructure.storage.persistent_local_artifacts import LocalArtifactStore

    created_refs: list[str] = []
    store = harness.runtime.artifact_store
    store_type = type(store)
    original_put = store_type.put

    def capture_put(instance: LocalArtifactStore, content: bytes) -> tuple[str, str]:
        ref, digest = original_put(instance, content)
        if instance is store:
            created_refs.append(ref)
        return ref, digest

    def fail_commit(_db: Session) -> None:
        raise RuntimeError("synthetic metadata commit failure")

    monkeypatch.setattr(store_type, "put", capture_put)
    monkeypatch.setattr(artifact_routes, "commit", fail_commit)
    with harness.session_factory() as db:
        device = get_verified_device(
            grant_id=grant_id,
            device_key=device_key,
            db=db,
            runtime=harness.runtime,
        )
        with pytest.raises(RuntimeError, match="synthetic metadata commit failure"):
            create_canvas_render_handoff(db, harness.runtime, device)

    assert len(created_refs) == 2
    assert all(store.get(ref) is None for ref in created_refs)


def test_t5_non_admitted_png_creates_no_receipt_or_persisted_artifacts(
    pilot_harness: PilotHarness,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from sketch2life.application.services.image_admission import (
        Feat018AdmissionResult,
        Feat018ImageAdmission,
    )
    from sketch2life.domain.understanding.image_admission import (
        AdmissionDecision,
        AdmissionOutcome,
        AdmissionReason,
    )
    from sketch2life.infrastructure.storage.persistent_local_artifacts import LocalArtifactStore
    from sketch2life.interfaces.http.be1_runtime import get_verified_device
    from sketch2life.interfaces.http.routers.be1_artifacts import create_canvas_render_handoff

    harness = pilot_harness
    _session_id, _child_id, _group_id, grant_id, device_key, _operation_ids = (
        _t4_append_two_strokes(harness)
    )
    created_refs: list[str] = []
    store = harness.runtime.artifact_store
    store_type = type(store)
    original_put = store_type.put

    def capture_put(instance: LocalArtifactStore, content: bytes) -> tuple[str, str]:
        ref, digest = original_put(instance, content)
        if instance is store:
            created_refs.append(ref)
        return ref, digest

    def reject_admission(
        _admission: Feat018ImageAdmission, _request: object
    ) -> Feat018AdmissionResult:
        return Feat018AdmissionResult(
            decision=AdmissionDecision(
                outcome=AdmissionOutcome.PROCESSING_FAILURE,
                reason=AdmissionReason.INTERNAL_ERROR,
                digest=None,
                metadata=None,
            ),
            source=None,
        )

    monkeypatch.setattr(store_type, "put", capture_put)
    monkeypatch.setattr(Feat018ImageAdmission, "admit", reject_admission)
    with harness.session_factory() as db:
        device = get_verified_device(
            grant_id=grant_id,
            device_key=device_key,
            db=db,
            runtime=harness.runtime,
        )
        with pytest.raises(HTTPException) as refused:
            create_canvas_render_handoff(db, harness.runtime, device)

    assert refused.value.status_code == 422
    assert isinstance(refused.value.detail, dict)
    assert refused.value.detail["code"] == "CANVAS_IMAGE_NOT_ADMITTED"
    assert len(created_refs) == 1
    assert store.get(created_refs[0]) is None


@dataclass(slots=True)
class _B1LoopbackVisionState:
    base_url: str
    disconnect: bool = False
    hold_response: bool = False
    before_response: Callable[[], None] | None = None
    calls: int = 0
    entered: Event = field(default_factory=Event)
    release: Event = field(default_factory=Event)
    lock: Lock = field(default_factory=Lock)


@contextmanager
def _b1_loopback_vision_stub(
    *,
    disconnect: bool = False,
    hold_response: bool = False,
    before_response: Callable[[], None] | None = None,
) -> Iterator[_B1LoopbackVisionState]:
    """A deterministic, loopback-only provider boundary for the composed B1 worker."""

    state = _B1LoopbackVisionState(
        base_url="",
        disconnect=disconnect,
        hold_response=hold_response,
        before_response=before_response,
    )

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, _format: str, *_args: object) -> None:
            return

        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length))
            with state.lock:
                state.calls += 1
            state.entered.set()
            if state.disconnect:
                with suppress(OSError):
                    self.connection.shutdown(socket.SHUT_RDWR)
                self.connection.close()
                return
            response = _b1_success_response(payload)
            if state.before_response is not None:
                state.before_response()
            if state.hold_response and not state.release.wait(15):
                return
            body = json.dumps(response, separators=(",", ":")).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    state.base_url = f"http://127.0.0.1:{server.server_port}"
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield state
    finally:
        state.release.set()
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def _b1_success_response(payload: Mapping[str, object]) -> dict[str, object]:
    from sketch2life.contracts.schemas.vision_v2 import (
        VisionUnderstandingRequestV2,
        VisionUnderstandingSuccessV2,
        vision_profile_catalog_hash_v2,
        vision_profile_catalog_v2,
        vision_profile_config_hash_v2,
    )
    from sketch2life.infrastructure.ai.vision_lexical_policy import (
        LexicalRegressionContentPolicy,
        synthetic_prohibited_lexicon,
    )

    request_value = payload.get("request")
    assert isinstance(request_value, dict)
    request = VisionUnderstandingRequestV2.model_validate(request_value)
    catalog = vision_profile_catalog_v2()
    profile = catalog.resolve(request.requested_profile_id)
    policy = LexicalRegressionContentPolicy(synthetic_prohibited_lexicon())
    result = VisionUnderstandingSuccessV2(
        correlation_id=request.correlation_id,
        executed_at=datetime.now(UTC),
        source_image_ref=request.source_image_ref,
        profile_id=request.requested_profile_id,
        profile_catalog_hash=vision_profile_catalog_hash_v2(catalog),
        attempt_number=1,
        repair_attempted=False,
        content_policy_version=policy.content_policy_version,
        policy_match_view_version=policy.policy_match_view_version,
        policy_execution_state="PASSED",
        entities=(),
        actions=(),
        relations=(),
        themes=(),
        ambiguous_regions=(),
        adapter_version=profile.adapter_version,
        config_hash=vision_profile_config_hash_v2(profile),
        model_provenance=profile.model_provenance,
    )
    return result.model_dump(mode="json")


def _b1_create_composed_job(
    harness: PilotHarness,
    *,
    base_url: str,
    token_file: Path,
):
    from sketch2life.application.ports.ai_jobs import Principal, PrincipalRole
    from sketch2life.application.services.ai_jobs import CreateJobCommand
    from sketch2life.domain.ai_jobs.model import RequestRef
    from sketch2life.domain.vision_analysis import VISION_ANALYSIS_JOB_TYPE
    from sketch2life.infrastructure.assistance.sql_repository import SqlAssistanceRepository
    from sketch2life.infrastructure.vision_analysis.pilot_composition import (
        PilotVisionComposition,
        build_default_pilot_vision,
    )

    session_id, child_id, canvas_id, handoff = _ga2_prepare(harness)
    engine = harness.runtime.engine
    assert engine is not None
    assistance_repository = SqlAssistanceRepository(engine, harness.organization_id)
    with engine.connect() as connection:
        _assistance_service, request = _ga2_request(
            harness,
            connection,
            session_id,
            child_id,
            canvas_id,
            handoff,
            repository=assistance_repository,
        )

    token_file.write_text("synthetic-loopback-token", encoding="utf-8")
    settings = harness.runtime.settings.model_copy(
        update={
            "env": "local",
            "synthetic_pilot_enabled": True,
            "ai_provider": "lightning_dev",
            "lightning_ai_base_url": base_url,
            "lightning_ai_token_file": token_file,
            "ai_request_timeout_seconds": 10.0,
        }
    )
    composition = build_default_pilot_vision(settings, engine)
    assert isinstance(composition, PilotVisionComposition)

    principal = Principal(
        harness.adult_subject, harness.organization_id, PrincipalRole.ADMIN
    )
    command = CreateJobCommand(
        principal=principal,
        idempotency_key=f"synthetic-b1-{uuid4().hex}",
        job_type=VISION_ANALYSIS_JOB_TYPE,
        target_id=request.assistance_id,
        purpose_code=request.facts.purpose_code,
        session_id=request.facts.session_id,
        subject_refs=request.facts.audience,
        request_ref=RequestRef(
            request.assistance_id,
            request.request_revision,
            request.facts.source.input_hash,
            request.facts.context_revision,
        ),
        correlation_id=f"synthetic-b1-correlation-{uuid4().hex}",
    )
    created = composition.jobs.create_job(command)
    from sketch2life.infrastructure.ai_jobs.sql import tables as job_tables

    with engine.connect() as connection:
        attempt_ids = tuple(
            connection.execute(
                select(job_tables.attempt.c.attempt_id).where(
                    job_tables.attempt.c.job_id == created.job_id
                )
            ).scalars()
        )
    assert len(attempt_ids) == 1
    harness.created_ai_jobs.append((created.job_id, attempt_ids))
    return composition, created.job_id, child_id, attempt_ids[0]


def _b1_persisted_state(engine: Engine, organization_id: str, job_id: str) -> dict[str, object]:
    from sketch2life.infrastructure.ai_jobs.sql import tables as job_tables
    from sketch2life.infrastructure.vision_analysis import tables as vision_tables

    with engine.connect() as connection:
        job = (
            connection.execute(
                select(
                    job_tables.job.c.state,
                    job_tables.job.c.job_revision,
                    job_tables.job.c.result_disposition,
                    func.jsonb_array_length(job_tables.job.c.result_refs).label("result_ref_count"),
                ).where(
                    job_tables.job.c.organization_id == organization_id,
                    job_tables.job.c.job_id == job_id,
                )
            )
            .mappings()
            .one()
        )
        attempt_rows = tuple(
            connection.execute(
                select(job_tables.attempt.c.attempt_id, job_tables.attempt.c.outcome).where(
                    job_tables.attempt.c.job_id == job_id
                )
            ).mappings()
        )
        attempt_ids = tuple(row["attempt_id"] for row in attempt_rows)
        attempts = tuple(row["outcome"] for row in attempt_rows)
        outbox_rows = tuple(
            connection.execute(
                select(
                    job_tables.outbox.c.kind,
                    job_tables.outbox.c.delivered_at,
                    job_tables.outbox.c.publish_attempts,
                    job_tables.outbox.c.last_error_code,
                ).where(
                    job_tables.outbox.c.job_id == job_id,
                    job_tables.outbox.c.attempt_id.in_(attempt_ids),
                )
            ).mappings()
        )
        completion_receipts = tuple(
            connection.execute(
                select(
                    job_tables.completion_receipt.c.disposition,
                    job_tables.completion_receipt.c.reason_code,
                    job_tables.completion_receipt.c.job_revision_after,
                ).where(
                    job_tables.completion_receipt.c.job_id == job_id,
                    job_tables.completion_receipt.c.attempt_id.in_(attempt_ids),
                )
            ).mappings()
        )
        invocation_states = tuple(
            connection.execute(
                select(vision_tables.invocations.c.state).where(
                    vision_tables.invocations.c.job_id == job_id,
                    vision_tables.invocations.c.organization_id == organization_id,
                )
            ).scalars()
        )
        analysis_count = connection.execute(
            select(func.count())
            .select_from(vision_tables.analysis_heads)
            .where(
                vision_tables.analysis_heads.c.organization_id == organization_id,
                vision_tables.analysis_heads.c.job_id == job_id,
            )
        ).scalar_one()
    return {
        "job_state": job["state"],
        "job_revision": job["job_revision"],
        "result_disposition": job["result_disposition"],
        "result_refs": tuple("present" for _ in range(job["result_ref_count"])),
        "attempt_outcomes": attempts,
        "invocation_states": invocation_states,
        "analysis_ids": tuple("present" for _ in range(analysis_count or 0)),
        "outbox": tuple(
            {
                "kind": row["kind"],
                "delivered": row["delivered_at"] is not None,
                "publish_attempts": row["publish_attempts"],
                "last_error_code": row["last_error_code"],
            }
            for row in outbox_rows
        ),
        "completion_receipts": tuple(
            {
                "disposition": row["disposition"],
                "reason_code": row["reason_code"],
                "job_revision_after": row["job_revision_after"],
            }
            for row in completion_receipts
        ),
    }


def _b1_dispatch_capture(composition, monkeypatch: pytest.MonkeyPatch):
    captured = []
    worker = composition.worker
    original_handle = worker.handle

    def capture(envelope):
        captured.append(envelope)
        return original_handle(envelope)

    monkeypatch.setattr(worker, "handle", capture)
    outcome = composition.dispatch_one()
    assert len(captured) == 1
    return outcome, captured[0]


def _b1_order_enforcing_repository_factory(real_factory, calls, violations):
    class OrderedTransaction:
        def __init__(self, transaction):
            self._transaction = transaction
            self._head_inserted = False
            self._observation_inserted = False

        def __getattr__(self, name):
            return getattr(self._transaction, name)

        def insert_head(self, record):
            if self._head_inserted:
                violations.append("duplicate analysis head insert")
                raise AssertionError(violations[-1])
            calls.append("head")
            self._head_inserted = True
            return self._transaction.insert_head(record)

        def insert_observation(self, record):
            if not self._head_inserted:
                violations.append("observation inserted before analysis head")
                raise AssertionError(violations[-1])
            calls.append("observation")
            self._observation_inserted = True
            return self._transaction.insert_observation(record)

        def insert_provider_result(self, record):
            if not self._observation_inserted:
                violations.append("provider result inserted before observation")
                raise AssertionError(violations[-1])
            calls.append("provider_result")
            return self._transaction.insert_provider_result(record)

    class OrderedRepository:
        def __init__(self, *args, **kwargs):
            self._inner = real_factory(*args, **kwargs)

        @contextmanager
        def transaction(self):
            with self._inner.transaction() as transaction:
                yield OrderedTransaction(transaction)

    return OrderedRepository


def test_b1_succeeded_is_durable_before_real_app_result_acceptance(
    pilot_harness: PilotHarness,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from sketch2life.infrastructure.vision_analysis import pilot_composition
    from sketch2life.infrastructure.vision_analysis import tables as vision_tables

    harness = pilot_harness
    engine = harness.runtime.engine
    assert engine is not None
    insert_order: list[str] = []
    order_violations: list[str] = []
    real_repository_factory = pilot_composition.SqlAnalysisRepository
    monkeypatch.setattr(
        pilot_composition,
        "SqlAnalysisRepository",
        _b1_order_enforcing_repository_factory(
            real_repository_factory, insert_order, order_violations
        ),
    )
    with _b1_loopback_vision_stub() as stub:
        composition, job_id, _child_id, _attempt_id = _b1_create_composed_job(
            harness, base_url=stub.base_url, token_file=tmp_path / "synthetic-token"
        )
        committed_observations: list[tuple[str | None, int]] = []
        original_complete = composition.invocation_ledger.complete

        def check_commit_before_acceptance(**values):
            completed = original_complete(**values)
            if values["state"] == "SUCCEEDED":
                with engine.connect() as connection:
                    persisted_state = connection.execute(
                        select(vision_tables.invocations.c.state).where(
                            vision_tables.invocations.c.run_id == values["run_id"],
                            vision_tables.invocations.c.job_id == job_id,
                        )
                    ).scalar_one_or_none()
                    head_count = connection.scalar(
                        select(func.count()).select_from(vision_tables.analysis_heads).where(
                            vision_tables.analysis_heads.c.organization_id
                            == harness.organization_id,
                            vision_tables.analysis_heads.c.job_id == job_id,
                        )
                    )
                committed_observations.append((persisted_state, head_count or 0))
            return completed

        monkeypatch.setattr(
            composition.invocation_ledger, "complete", check_commit_before_acceptance
        )
        outcome, envelope = _b1_dispatch_capture(composition, monkeypatch)
        state = _b1_persisted_state(engine, harness.organization_id, job_id)
        assert order_violations == []
        assert insert_order == ["head", "observation", "provider_result"]
        assert outcome is not None and outcome.status == "completed", (
            f"reason={None if outcome is None else outcome.reason_code}; "
            f"state={state}; stub_calls={stub.calls}"
        )
        assert outcome.receipt is not None and outcome.receipt.authoritative
        assert committed_observations == [("SUCCEEDED", 0)]
        assert state["job_state"] == "succeeded"
        assert state["result_disposition"] == "accepted"
        receipts = state["completion_receipts"]
        assert isinstance(receipts, tuple)
        assert len(receipts) == 1
        receipt = receipts[0]
        assert receipt["disposition"] == "accepted"
        assert receipt["reason_code"] is None
        assert receipt["job_revision_after"] == state["job_revision"]
        assert outcome.receipt.job_revision_after == receipt["job_revision_after"]
        assert len(state["result_refs"]) == 1
        assert state["invocation_states"] == ("SUCCEEDED",)
        assert len(state["analysis_ids"]) == 1
        assert len(state["attempt_outcomes"]) == 1
        assert stub.calls == 1

        replay = composition.worker.handle(envelope)
        assert replay.status in {"not_started", "rejected"}
        assert stub.calls == 1
        assert len(_b1_persisted_state(engine, harness.organization_id, job_id)["result_refs"]) == 1


def test_b1_sent_invocation_survives_process_rebuild_without_second_provider_call(
    pilot_harness: PilotHarness,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from sketch2life.application.ports.ai_jobs import DispatchMessage, WorkerDispatchEnvelope
    from sketch2life.infrastructure.vision_analysis.invocation_guard import (
        InvocationLedgerGuard,
    )
    from sketch2life.infrastructure.vision_analysis.pilot_composition import (
        PilotVisionComposition,
        build_default_pilot_vision,
    )

    harness = pilot_harness
    engine = harness.runtime.engine
    assert engine is not None
    with _b1_loopback_vision_stub() as stub:
        composition, job_id, _child_id, attempt_id = _b1_create_composed_job(
            harness, base_url=stub.base_url, token_file=tmp_path / "synthetic-token"
        )
        original_finalize = InvocationLedgerGuard.finalize

        class SimulatedProcessCrash(BaseException):
            pass

        def crash_after_provider_response(
            guard: InvocationLedgerGuard, state: Any, result_sha256: str | None = None
        ) -> bool:
            if getattr(state, "value", None) == "SUCCEEDED":
                raise SimulatedProcessCrash
            return original_finalize(guard, state, result_sha256)

        with monkeypatch.context() as process_context:
            process_context.setattr(
                InvocationLedgerGuard, "finalize", crash_after_provider_response
            )
            captured: list[Any] = []
            original_handle = composition.worker.handle

            def capture(envelope: Any) -> Any:
                captured.append(envelope)
                return original_handle(envelope)

            process_context.setattr(composition.worker, "handle", capture)
            with pytest.raises(SimulatedProcessCrash):
                composition.dispatch_one()

        assert len(captured) == 1
        original_envelope = captured[0]
        original_message = original_envelope.message
        assert stub.calls == 1
        state_after_crash = _b1_persisted_state(engine, harness.organization_id, job_id)
        assert state_after_crash["job_state"] == "running"
        assert state_after_crash["result_disposition"] is None
        assert state_after_crash["result_refs"] == ()
        assert state_after_crash["completion_receipts"] == ()
        assert state_after_crash["analysis_ids"] == ()
        assert state_after_crash["invocation_states"] == ("SENT",)
        assert state_after_crash["attempt_outcomes"] == (None,)

        token_file = tmp_path / "synthetic-token-after-restart"
        token_file.write_text("synthetic-loopback-token", encoding="utf-8")
        settings = harness.runtime.settings.model_copy(
            update={
                "env": "local",
                "synthetic_pilot_enabled": True,
                "ai_provider": "lightning_dev",
                "lightning_ai_base_url": stub.base_url,
                "lightning_ai_token_file": token_file,
                "ai_request_timeout_seconds": 10.0,
            }
        )
        restarted = build_default_pilot_vision(settings, engine)
        assert isinstance(restarted, PilotVisionComposition)
        assert restarted is not composition
        assert restarted.worker is not composition.worker
        assert restarted.invocation_ledger is not composition.invocation_ledger

        message = DispatchMessage(
            message_id=f"synthetic-restarted-{uuid4().hex}",
            job_id=original_message.job_id,
            attempt_id=original_message.attempt_id,
            attempt_number=original_message.attempt_number,
            job_type=original_message.job_type,
            request_ref=original_message.request_ref,
        )
        capability = restarted.jobs._d.capability_issuer.issue(
            job_id=job_id,
            attempt_id=attempt_id,
            now=restarted.jobs._d.clock.now(),
        )
        new_envelope = WorkerDispatchEnvelope(message, capability)
        assert new_envelope is not original_envelope
        assert new_envelope.message is not original_message

        redelivery = restarted.worker.handle(new_envelope)
        assert redelivery.status == "not_started"
        assert stub.calls == 1

        # Exercise the reconstructed provider guard too: the durable (job, attempt) SENT
        # claim must refuse a second HTTP call even after the worker object is rebuilt.
        claim = restarted.provider.run(message)
        assert claim.kind.value == "failure"
        assert stub.calls == 1
        final_state = _b1_persisted_state(engine, harness.organization_id, job_id)
        assert final_state["job_state"] == "running"
        assert final_state["result_disposition"] is None
        assert final_state["result_refs"] == ()
        assert final_state["completion_receipts"] == ()
        assert final_state["invocation_states"] == ("SENT",)


def test_b1_unknown_after_sent_is_not_accepted_or_replayed(
    pilot_harness: PilotHarness,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    harness = pilot_harness
    engine = harness.runtime.engine
    assert engine is not None
    with _b1_loopback_vision_stub(disconnect=True) as stub:
        composition, job_id, _child_id, _attempt_id = _b1_create_composed_job(
            harness, base_url=stub.base_url, token_file=tmp_path / "synthetic-token"
        )
        _outcome, envelope = _b1_dispatch_capture(composition, monkeypatch)
        replay = composition.worker.handle(envelope)
        state = _b1_persisted_state(engine, harness.organization_id, job_id)
        assert replay.status in {"not_started", "rejected"}
        assert stub.calls == 1
        assert state["job_state"] != "succeeded"
        assert state["result_refs"] == ()
        assert state["analysis_ids"] == ()
        assert state["invocation_states"] == ("UNKNOWN",)
        assert len(state["attempt_outcomes"]) == 1


def test_b1_hold_before_send_creates_no_result_or_invocation(
    pilot_harness: PilotHarness,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from sketch2life.infrastructure.persistence.be1_models import SyntheticEligibilityProofModel

    harness = pilot_harness
    engine = harness.runtime.engine
    assert engine is not None
    with _b1_loopback_vision_stub() as stub:
        composition, job_id, child_id, _attempt_id = _b1_create_composed_job(
            harness, base_url=stub.base_url, token_file=tmp_path / "synthetic-token"
        )
        with harness.session_factory.begin() as db:
            proof = db.scalar(
                select(SyntheticEligibilityProofModel).where(
                    SyntheticEligibilityProofModel.child_profile_id == child_id
                )
            )
            assert proof is not None and proof.revoked_at is None
            proof.revoked_at = datetime.now(UTC)
            proof.revocation_revision = 1

        worker_calls = []
        original_handle = composition.worker.handle

        def capture_worker(envelope: Any) -> Any:
            worker_calls.append(envelope)
            return original_handle(envelope)

        monkeypatch.setattr(composition.worker, "handle", capture_worker)
        outcome = composition.dispatch_one()
        state = _b1_persisted_state(engine, harness.organization_id, job_id)
        assert outcome is None
        assert worker_calls == []
        assert stub.calls == 0
        assert state["job_state"] != "succeeded"
        assert state["result_refs"] == ()
        assert state["analysis_ids"] == ()
        assert state["invocation_states"] == ()
        assert isinstance(state["attempt_outcomes"], tuple)
        assert len(state["attempt_outcomes"]) == 1


def test_b1_stale_owner_fence_rejects_result_after_provider_success(
    pilot_harness: PilotHarness,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from sketch2life.infrastructure.persistence.be1_models import ManagedProfileModel

    harness = pilot_harness
    engine = harness.runtime.engine
    assert engine is not None
    changed = Event()
    with _b1_loopback_vision_stub() as stub:
        composition, job_id, child_id, _attempt_id = _b1_create_composed_job(
            harness, base_url=stub.base_url, token_file=tmp_path / "synthetic-token"
        )
        original_decide = composition.jobs._decide_completion

        def change_facts_before_completion_fence(
            job: Any,
            claim: Any,
            eligibility: Any,
            descriptors: Any,
            effects: Any,
        ) -> Any:
            if not changed.is_set():
                with engine.begin() as writer:
                    writer.execute(
                        update(ManagedProfileModel)
                        .where(ManagedProfileModel.child_id == child_id)
                        .values(age_revision=ManagedProfileModel.age_revision + 1)
                    )
                changed.set()
            return original_decide(job, claim, eligibility, descriptors, effects)

        monkeypatch.setattr(
            composition.jobs, "_decide_completion", change_facts_before_completion_fence
        )
        outcome, _envelope = _b1_dispatch_capture(composition, monkeypatch)
        state = _b1_persisted_state(engine, harness.organization_id, job_id)
        assert changed.is_set()
        assert stub.calls == 1
        assert outcome is not None and outcome.status == "rejected"
        assert outcome.reason_code == "STALE_CONTEXT"
        # Owner decision (d): pin today's stale-fence outcome; do not invent a terminal state.
        assert state["job_state"] == "running"
        assert state["result_disposition"] is None
        assert state["result_refs"] == ()
        assert state["completion_receipts"] == ()
        assert state["invocation_states"] == ("SUCCEEDED",)
        assert isinstance(state["analysis_ids"], tuple)
        assert len(state["analysis_ids"]) == 1
        assert isinstance(state["attempt_outcomes"], tuple)
        assert state["attempt_outcomes"] == (None,)


def test_b1_stale_artifact_fence_rejects_result_after_provider_success(
    pilot_harness: PilotHarness,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from sketch2life.application.ports.ai_jobs import QuarantineIntent

    harness = pilot_harness
    engine = harness.runtime.engine
    assert engine is not None
    with _b1_loopback_vision_stub() as stub:
        composition, job_id, _child_id, _attempt_id = _b1_create_composed_job(
            harness, base_url=stub.base_url, token_file=tmp_path / "synthetic-token"
        )
        original_decide = composition.jobs._decide_completion
        quarantined_refs: list[str] = []

        def quarantine_after_descriptor_read(
            job: Any,
            claim: Any,
            eligibility: Any,
            descriptors: Any,
            effects: Any,
        ) -> Any:
            if not quarantined_refs:
                assert len(claim.outputs) == 1
                output = claim.outputs[0]
                descriptor = descriptors[output.artifact_ref]
                assert descriptor is not None
                assert descriptor.fence is not None
                assert descriptor.quarantine_reason is None
                composition.fake_artifacts.quarantine(
                    QuarantineIntent(
                        event_id=f"synthetic-artifact-fence-{uuid4().hex}",
                        organization_id=harness.organization_id,
                        job_id=job_id,
                        attempt_id=claim.attempt_id,
                        artifact_refs=(output.artifact_ref,),
                        reason_code="SYNTHETIC_TEST_QUARANTINE",
                    )
                )
                quarantined_refs.append(output.artifact_ref)
            return original_decide(job, claim, eligibility, descriptors, effects)

        monkeypatch.setattr(
            composition.jobs, "_decide_completion", quarantine_after_descriptor_read
        )
        outcome, _envelope = _b1_dispatch_capture(composition, monkeypatch)
        state = _b1_persisted_state(engine, harness.organization_id, job_id)

        assert len(quarantined_refs) == 1
        descriptor = composition.fake_artifacts.describe(quarantined_refs[0])
        assert descriptor is not None
        assert descriptor.quarantine_reason == "SYNTHETIC_TEST_QUARANTINE"
        assert stub.calls == 1
        assert state["job_state"] != "succeeded"
        assert state["result_refs"] == ()
        assert state["invocation_states"] == ("SUCCEEDED",)
        assert isinstance(state["attempt_outcomes"], tuple)
        assert len(state["attempt_outcomes"]) == 1
        assert outcome is not None


def test_b1_concurrent_duplicate_delivery_uses_one_attempt_and_one_send(
    pilot_harness: PilotHarness,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    harness = pilot_harness
    engine = harness.runtime.engine
    assert engine is not None
    with _b1_loopback_vision_stub(hold_response=True) as stub:
        composition, job_id, _child_id, _attempt_id = _b1_create_composed_job(
            harness, base_url=stub.base_url, token_file=tmp_path / "synthetic-token"
        )
        assert composition.jobs.dispatch_outbox() == 1
        barrier = Barrier(2)
        original_start = composition.jobs.start_attempt

        def simultaneous_claim(capability, requested_job_id, attempt_id):
            barrier.wait(timeout=5)
            return original_start(capability, requested_job_id, attempt_id)

        monkeypatch.setattr(composition.jobs, "start_attempt", simultaneous_claim)
        original_handle = composition.worker.handle
        concurrent_outcomes = []
        non_sender_finished = Event()

        class DuplicateDelivery:
            def handle(self, envelope):
                def run_one() -> object:
                    outcome = original_handle(envelope)
                    if outcome.status != "completed":
                        non_sender_finished.set()
                    return outcome

                with ThreadPoolExecutor(max_workers=2) as pool:
                    futures = (pool.submit(run_one), pool.submit(run_one))
                    concurrent_outcomes.extend(future.result(timeout=20) for future in futures)
                return None

        with ThreadPoolExecutor(max_workers=1) as pool:
            dispatch = pool.submit(composition.queue.run_one, DuplicateDelivery())
            assert stub.entered.wait(10)
            state_while_sent = _b1_persisted_state(engine, harness.organization_id, job_id)
            assert state_while_sent["invocation_states"] == ("SENT",)
            assert state_while_sent["analysis_ids"] == ()
            assert non_sender_finished.wait(10)
            assert stub.calls == 1
            stub.release.set()
            dispatch.result(timeout=20)

        assert len(concurrent_outcomes) == 2
        assert sum(outcome.status == "completed" for outcome in concurrent_outcomes) == 1
        assert stub.calls == 1
        state = _b1_persisted_state(engine, harness.organization_id, job_id)
        assert state["job_state"] == "succeeded"
        assert state["result_disposition"] == "accepted"
        assert len(state["result_refs"]) == 1
        assert state["invocation_states"] == ("SUCCEEDED",)
        assert len(state["analysis_ids"]) == 1
        assert len(state["attempt_outcomes"]) == 1
