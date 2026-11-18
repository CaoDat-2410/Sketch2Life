"""Owner-run S1a-P PostgreSQL acceptance; this test is never run by the coordinator."""

from __future__ import annotations

import os
import re
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from ipaddress import ip_address
from typing import Any, cast
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import MetaData, Table, func, inspect, select, text
from sqlalchemy.engine import Engine

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.infrastructure.identity.firebase_token_verifier import (
    FirebaseTokenVerifier,
    IdentityVerificationUnavailable,
)
from sketch2life.infrastructure.persistence.parent_models import (
    ParentChildProfileModel,
    ParentCommandReceiptModel,
    ParentProfileRevisionModel,
)
from sketch2life.interfaces.http.app import create_app

_EXPECTED_DATABASE = "sketch2life_m2_s1a"
_EXPECTED_REVISION = "20261109_m2_parent_profiles"
_EXPECTED_PORT = 5433
_EXPECTED_MAJOR = 17


class _GateBTokenVerifier(FirebaseTokenVerifier):
    def __init__(self, run_id: str, settings: Settings) -> None:
        super().__init__(settings)
        self._run_id = run_id

    async def verify(self, encoded_token: str) -> VerifiedPrincipal:
        if encoded_token == "synthetic-owner":
            return VerifiedPrincipal(
                f"s1a-p-{self._run_id}-owner",
                "synthetic-parent-issuer",
                frozenset(),
            )
        if encoded_token == "synthetic-other":
            return VerifiedPrincipal(
                f"s1a-p-{self._run_id}-other",
                "synthetic-parent-issuer",
                frozenset(),
            )
        if encoded_token == "synthetic-same-subject-other-issuer":
            return VerifiedPrincipal(
                f"s1a-p-{self._run_id}-owner",
                "synthetic-other-issuer",
                frozenset(),
            )
        raise IdentityVerificationUnavailable("Synthetic Gate B token was not recognized")


@dataclass(frozen=True, slots=True)
class _GateBHarness:
    client: TestClient
    engine: Engine
    run_id: str
    owner_subject: str


def _database_identity(engine: Engine) -> tuple[str, str, int, str, int]:
    with engine.connect() as connection:
        connection.execute(text("SET TRANSACTION READ ONLY"))
        row = connection.execute(
            text(
                "SELECT current_database(), host(inet_server_addr()), "
                "inet_server_port(), current_user, "
                "current_setting('server_version_num')::integer"
            )
        ).one()
    database, host_text, port, user, version_number = row
    return (
        str(database),
        str(host_text),
        int(port),
        str(user),
        int(version_number) // 10000,
    )


def _all_table_counts(engine: Engine) -> dict[str, int]:
    counts: dict[str, int] = {}
    with engine.connect() as connection:
        connection.execute(text("SET TRANSACTION READ ONLY"))
        inspector = inspect(connection)
        for schema in sorted(inspector.get_schema_names()):
            if schema in {"information_schema", "pg_catalog"} or schema.startswith("pg_toast"):
                continue
            for name in sorted(inspector.get_table_names(schema=schema)):
                table = Table(name, MetaData(), schema=schema, autoload_with=connection)
                count = connection.scalar(select(func.count()).select_from(table))
                counts[f"{schema}.{name}"] = int(count or 0)
    return counts


def _parent_marker_counts(engine: Engine, issuer: str, subject: str) -> dict[str, int]:
    with engine.connect() as connection:
        connection.execute(text("SET TRANSACTION READ ONLY"))
        profiles = connection.scalar(
            select(func.count()).select_from(ParentChildProfileModel.__table__).where(
                ParentChildProfileModel.owner_issuer == issuer,
                ParentChildProfileModel.owner_subject == subject,
            )
        )
        revisions = connection.scalar(
            select(func.count())
            .select_from(ParentProfileRevisionModel.__table__)
            .join(
                ParentChildProfileModel.__table__,
                ParentProfileRevisionModel.parent_profile_id
                == ParentChildProfileModel.parent_profile_id,
            )
            .where(
                ParentChildProfileModel.owner_issuer == issuer,
                ParentChildProfileModel.owner_subject == subject,
                ParentProfileRevisionModel.authored_by_issuer == issuer,
                ParentProfileRevisionModel.authored_by_subject == subject,
            )
        )
        receipts = connection.scalar(
            select(func.count()).select_from(ParentCommandReceiptModel.__table__).where(
                ParentCommandReceiptModel.principal_issuer == issuer,
                ParentCommandReceiptModel.principal_subject == subject,
            )
        )
    return {
        "parent.child_profiles": int(profiles or 0),
        "parent.profile_revisions": int(revisions or 0),
        "parent.command_receipts": int(receipts or 0),
    }


def _require_gate_b_identity(engine: Engine) -> None:
    database, host_text, port, user, major = _database_identity(engine)
    assert database == _EXPECTED_DATABASE
    assert ip_address(host_text).is_loopback
    assert port == _EXPECTED_PORT
    assert user == "postgres"
    assert major == _EXPECTED_MAJOR


@pytest.fixture
def gate_b(monkeypatch: pytest.MonkeyPatch) -> Iterator[_GateBHarness]:
    run_id = os.environ.get("S1A_P_GATE_B_RUN_ID")
    if run_id is None or re.fullmatch(r"[0-9a-f]{32}", run_id) is None:
        pytest.fail("S1A_P_GATE_B_RUN_ID is required from the reviewed launcher")

    dedicated_url = os.environ.get("S1A_P_TEST_DATABASE_URL")
    if not dedicated_url:
        pytest.fail("S1A_P_TEST_DATABASE_URL is required; no database write was attempted")

    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", dedicated_url)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "firebase")
    monkeypatch.setenv("SKETCH2LIFE_FIREBASE_PROJECT_ID", "synthetic-parent-gate-b")
    monkeypatch.setenv("SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED", "1")
    monkeypatch.setenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", "0")
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()

    application = create_app()
    runtime = application.state.be1_runtime
    if runtime.engine is None or runtime.session_factory is None:
        pytest.fail("The configured application database engine is unavailable")
    engine: Engine = runtime.engine
    _require_gate_b_identity(engine)

    before = _all_table_counts(engine)
    assert len(before) == 120
    assert sum(before.values()) == 30
    assert before.get("parent.child_profiles") == 0
    assert before.get("parent.profile_revisions") == 0
    assert before.get("parent.command_receipts") == 0
    with engine.connect() as connection:
        connection.execute(text("SET TRANSACTION READ ONLY"))
        versions = connection.execute(
            text("SELECT version_num FROM public.alembic_version ORDER BY version_num")
        ).scalars().all()
    assert versions == [_EXPECTED_REVISION]

    owner_subject = f"s1a-p-{run_id}-owner"
    runtime.identity_verifier = _GateBTokenVerifier(run_id, runtime.settings)
    try:
        with TestClient(application) as client:
            yield _GateBHarness(client, engine, run_id, owner_subject)
    finally:
        application.dependency_overrides.clear()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def test_parent_postgresql_routes_preserve_exact_state_and_markers(
    gate_b: _GateBHarness,
) -> None:
    client = gate_b.client
    engine = gate_b.engine
    run_id = gate_b.run_id
    owner_subject = gate_b.owner_subject
    issuer = "synthetic-parent-issuer"
    baseline = _all_table_counts(engine)
    assert sum(baseline.values()) == 30

    owner_headers = {"Authorization": "Bearer synthetic-owner"}
    other_headers = {"Authorization": "Bearer synthetic-other"}
    different_issuer_headers = {
        "Authorization": "Bearer synthetic-same-subject-other-issuer"
    }
    create_body = {"display_name": "S1a-P synthetic", "age_months": 72}

    # The disabled control reaches the real Parent service but creates no rows.
    app = cast(FastAPI, client.app)
    app.state.be1_runtime.settings.synthetic_pilot_enabled = False
    disabled = client.post(
        "/v1/parent/profiles",
        headers={**owner_headers, "Idempotency-Key": f"{run_id}-disabled"},
        json=create_body,
    )
    assert disabled.status_code == 409
    assert disabled.json()["code"] == "SYNTHETIC_PROFILE_CREATION_UNAVAILABLE"
    assert _all_table_counts(engine) == baseline
    app.state.be1_runtime.settings.synthetic_pilot_enabled = True

    def create_once() -> Any:
        return client.post(
            "/v1/parent/profiles",
            headers={**owner_headers, "Idempotency-Key": f"{run_id}-create"},
            json=create_body,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        first_future = executor.submit(create_once)
        replay_future = executor.submit(create_once)
        first = first_future.result()
        replay = replay_future.result()
    assert first.status_code == 201
    assert replay.status_code == 201
    assert first.json() == replay.json()
    assert _parent_marker_counts(engine, issuer, owner_subject) == {
        "parent.child_profiles": 1,
        "parent.profile_revisions": 1,
        "parent.command_receipts": 1,
    }
    profile_id = UUID(first.json()["profile_id"])

    mismatched = client.post(
        "/v1/parent/profiles",
        headers={**owner_headers, "Idempotency-Key": f"{run_id}-create"},
        json={"display_name": "Different", "age_months": 72},
    )
    assert mismatched.status_code == 400
    assert mismatched.json()["code"] == "INVALID_IDEMPOTENCY_KEY"

    read = client.get(f"/v1/parent/profiles/{profile_id}", headers=owner_headers)
    assert read.status_code == 200
    assert read.json()["data_origin"] == "SYNTHETIC_DEV"

    before_denials = _all_table_counts(engine)
    missing_id = uuid4()
    denied = []
    for url, headers in (
        (f"/v1/parent/profiles/{missing_id}", owner_headers),
        (f"/v1/parent/profiles/{profile_id}", other_headers),
        (f"/v1/parent/profiles/{profile_id}", different_issuer_headers),
    ):
        denied.append(client.get(url, headers=headers))
        denied.append(
            client.patch(
                url,
                headers={**headers, "Idempotency-Key": f"{run_id}-denied-{len(denied)}"},
                json={"expected_revision": 1, "display_name": "Mina", "age_months": 72},
            )
        )
    for response in denied:
        assert response.status_code == 404
        assert response.json()["code"] == "PROFILE_NOT_FOUND"
        assert response.json()["message"] == "Profile was not found"
    assert _all_table_counts(engine) == before_denials

    patch_body = {"expected_revision": 1, "display_name": "S1a-P revised", "age_months": 84}
    patch_headers = {**owner_headers, "Idempotency-Key": f"{run_id}-patch"}
    patched = client.patch(
        f"/v1/parent/profiles/{profile_id}", headers=patch_headers, json=patch_body
    )
    patch_replay = client.patch(
        f"/v1/parent/profiles/{profile_id}", headers=patch_headers, json=patch_body
    )
    assert patched.status_code == 200
    assert patch_replay.status_code == 200
    assert patch_replay.json() == patched.json()
    patched_body = patched.json()
    assert set(patched_body) == {
        "profile_id",
        "revision_no",
        "revision_hash",
        "display_name",
        "age_months",
        "age_band_ref",
        "age_band_version",
        "interests_summary",
        "state",
        "data_origin",
    }
    assert patched_body["profile_id"] == str(profile_id)
    assert patched_body["revision_no"] == 2
    revision_hash = patched_body["revision_hash"]
    assert isinstance(revision_hash, str)
    assert len(revision_hash) == 64
    assert all(character in "0123456789abcdef" for character in revision_hash)
    assert patched_body["display_name"] == "S1a-P revised"
    assert patched_body["age_months"] == 84
    assert patched_body["age_band_ref"] is None
    assert patched_body["age_band_version"] is None
    assert patched_body["interests_summary"] is None
    assert patched_body["state"] == "ACTIVE"
    assert patched_body["data_origin"] == "SYNTHETIC_DEV"

    stale_body = {"expected_revision": 1, "display_name": "Stale", "age_months": 72}
    stale_headers = {
        **owner_headers,
        "Idempotency-Key": f"{run_id}-stale",
        "X-Request-ID": f"{run_id}-stale-first",
    }
    stale = client.patch(
        f"/v1/parent/profiles/{profile_id}", headers=stale_headers, json=stale_body
    )
    stale_replay = client.patch(
        f"/v1/parent/profiles/{profile_id}",
        headers={**stale_headers, "X-Request-ID": f"{run_id}-stale-replay"},
        json=stale_body,
    )
    assert stale.status_code == 409
    assert stale.json()["code"] == "STALE_REVISION"
    assert stale.json()["current_version"] == 2
    assert stale_replay.status_code == 409
    assert stale_replay.json() == stale.json()
    assert stale.json()["request_id"] == f"{run_id}-stale-first"
    assert stale.headers["X-Request-ID"] == stale.json()["request_id"]
    assert stale_replay.headers["X-Request-ID"] == stale_replay.json()["request_id"]

    final_counts = _all_table_counts(engine)
    assert len(final_counts) == 120
    assert sum(final_counts.values()) == 36
    assert {
        key: final_counts[key]
        for key in final_counts
        if not key.startswith("parent.")
    } == {
        key: baseline[key]
        for key in baseline
        if not key.startswith("parent.")
    }
    assert _parent_marker_counts(engine, issuer, owner_subject) == {
        "parent.child_profiles": 1,
        "parent.profile_revisions": 2,
        "parent.command_receipts": 3,
    }
