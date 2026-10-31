"""Real-PostgreSQL FEAT-064 synthetic eligibility pilot rehearsal.

Run only against an explicitly approved disposable ``be1_acceptance`` database. This test
uses synthetic identities, the real BE1 HTTP app and the real PostgreSQL repositories. It
does not call an AI provider or use child data.
"""

from __future__ import annotations

import importlib.util
import ipaddress
import os
import socket
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
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
from sqlalchemy import Engine, MetaData, Table, and_, delete, inspect, select
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

_PILOT_POLICY_VERSION = "feat064-synthetic-pilot-v1"


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


def _is_loopback_host(host: object) -> bool:
    if not isinstance(host, str) or not host:
        return False
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return host.lower() == "localhost"


def _is_safe_acceptance_database_url(database_url: str) -> bool:
    try:
        url = make_url(database_url)
    except Exception:
        return False
    if (
        url.get_backend_name() != "postgresql"
        or not url.database
        or "be1_acceptance" not in url.database
        or not _is_loopback_host(url.host)
        or "service" in url.query
    ):
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
        ("postgresql://127.0.0.1:5433/app_be1_acceptance", True),
        ("postgresql://[::1]:5433/be1_acceptance", True),
        ("postgresql://db.example.invalid/be1_acceptance", False),
        ("postgresql://localhost/be1_acceptance?hostaddr=203.0.113.9", False),
        ("postgresql://localhost/be1_acceptance?service=remote", False),
        ("postgresql://localhost/application", False),
    ],
)
def test_acceptance_database_url_requires_loopback_and_acceptance_name(
    database_url: str, expected: bool
) -> None:
    assert _is_safe_acceptance_database_url(database_url) is expected


@pytest.fixture
def pilot_harness(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[PilotHarness]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL to run the PostgreSQL synthetic pilot")
    if not _is_safe_acceptance_database_url(database_url):
        pytest.fail(
            "BE1_TEST_DATABASE_URL must target a loopback PostgreSQL be1_acceptance database"
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
            )
    finally:
        app.dependency_overrides.clear()
        _delete_test_organization_rows(engine, organization_id, {adult_subject})
        engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def _delete_test_organization_rows(
    engine: Engine, organization_id: str, adult_subjects: set[str]
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
    with engine.begin() as connection:
        for table in ordered:
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

        adults = tables.get(("public", "be1_adult_identities"))
        if adults is not None:
            for subject in adult_subjects:
                connection.execute(delete(adults).where(adults.c.subject == subject))


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
