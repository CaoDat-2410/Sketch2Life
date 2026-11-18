"""Owner-run Gate P2 for Parent-owned list, deletion, and receipt behavior only."""

from __future__ import annotations

import hashlib
import os
import re
from collections.abc import Iterator
from ipaddress import ip_address
from uuid import UUID

import pytest
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
from sketch2life.interfaces.http.parent_runtime import get_parent_role_reader

_EXPECTED_DATABASE = "sketch2life_m2_s1a"
_EXPECTED_REVISION = "20261109_m2_parent_profiles"
_EXPECTED_PORT = 5433
_EXPECTED_MAJOR = 17
_EXPECTED_ISSUER = "synthetic-parent-issuer"
_GATE_B_RUN_ID = "8b64744372454dadb5e3d75b14288853"
_GATE_B_OWNER_SUBJECT = f"s1a-p-{_GATE_B_RUN_ID}-owner"


class _GateP2TokenVerifier(FirebaseTokenVerifier):
    def __init__(self, run_id: str, settings: Settings) -> None:
        super().__init__(settings)
        self._run_id = run_id

    async def verify(self, encoded_token: str) -> VerifiedPrincipal:
        if encoded_token != "synthetic-owner":
            if encoded_token == "synthetic-other":
                return VerifiedPrincipal(
                    f"s1a-p2-other-{self._run_id}", _EXPECTED_ISSUER, frozenset()
                )
            raise IdentityVerificationUnavailable("Gate P2 token was not recognized")
        return VerifiedPrincipal(_GATE_B_OWNER_SUBJECT, _EXPECTED_ISSUER, frozenset())


class _ApplicationRoleStub:
    def __init__(self, run_id: str) -> None:
        self._other_subject = f"s1a-p2-other-{run_id}"

    def has_active_parent_role(self, *, principal: VerifiedPrincipal) -> bool:
        return (
            principal.issuer == _EXPECTED_ISSUER
            and principal.subject in {_GATE_B_OWNER_SUBJECT, self._other_subject}
        )


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
        connection.rollback()
    database, host_text, port, user, version_number = row
    return (
        str(database),
        str(host_text),
        int(port),
        str(user),
        int(version_number) // 10000,
    )


def _table_counts(engine: Engine) -> dict[str, int]:
    counts: dict[str, int] = {}
    with engine.connect() as connection:
        connection.execute(text("SET TRANSACTION READ ONLY"))
        inspector = inspect(connection)
        for schema in sorted(inspector.get_schema_names()):
            if (
                schema in {"information_schema", "pg_catalog"}
                or schema.startswith("pg_toast")
                or schema.startswith("pg_temp_")
            ):
                continue
            for name in sorted(inspector.get_table_names(schema=schema)):
                table = Table(name, MetaData(), schema=schema, autoload_with=connection)
                count = connection.scalar(select(func.count()).select_from(table))
                counts[f"{schema}.{name}"] = int(count or 0)
        connection.rollback()
    return counts


def _run_marker_counts(
    engine: Engine, issuer: str, subject: str, run_id: str
) -> dict[str, int]:
    profile_names = {f"Gate P2 {run_id}", f"Gate P2 updated {run_id}"}
    receipt_hashes = {
        hashlib.sha256(f"{run_id}-{operation}".encode("ascii")).digest()
        for operation in ("create", "patch", "delete")
    }
    with engine.connect() as connection:
        connection.execute(text("SET TRANSACTION READ ONLY"))
        profile_ids = list(
            connection.scalars(
                select(ParentChildProfileModel.parent_profile_id)
                .join(
                    ParentProfileRevisionModel.__table__,
                    ParentProfileRevisionModel.parent_profile_id
                    == ParentChildProfileModel.parent_profile_id,
                )
                .where(
                    ParentChildProfileModel.owner_issuer == issuer,
                    ParentChildProfileModel.owner_subject == subject,
                    ParentProfileRevisionModel.display_name.in_(profile_names),
                )
                .distinct()
            )
        )
        profiles = len(profile_ids)
        revisions = connection.scalar(
            select(func.count())
            .select_from(ParentProfileRevisionModel.__table__)
            .where(
                ParentProfileRevisionModel.parent_profile_id.in_(profile_ids),
                ParentProfileRevisionModel.authored_by_issuer == issuer,
                ParentProfileRevisionModel.authored_by_subject == subject,
            )
        )
        receipts = connection.scalar(
            select(func.count())
            .select_from(ParentCommandReceiptModel.__table__)
            .where(
                ParentCommandReceiptModel.principal_issuer == issuer,
                ParentCommandReceiptModel.principal_subject == subject,
                ParentCommandReceiptModel.key_hash.in_(receipt_hashes),
            )
        )
        connection.rollback()
    return {
        "parent.child_profiles": int(profiles or 0),
        "parent.profile_revisions": int(revisions or 0),
        "parent.command_receipts": int(receipts or 0),
    }


def _gate_b_owner_counts(engine: Engine) -> dict[str, int]:
    with engine.connect() as connection:
        connection.execute(text("SET TRANSACTION READ ONLY"))
        profiles = connection.scalar(
            select(func.count())
            .select_from(ParentChildProfileModel.__table__)
            .where(
                ParentChildProfileModel.owner_issuer == _EXPECTED_ISSUER,
                ParentChildProfileModel.owner_subject == _GATE_B_OWNER_SUBJECT,
            )
        )
        active_profiles = connection.scalar(
            select(func.count())
            .select_from(ParentChildProfileModel.__table__)
            .where(
                ParentChildProfileModel.owner_issuer == _EXPECTED_ISSUER,
                ParentChildProfileModel.owner_subject == _GATE_B_OWNER_SUBJECT,
                ParentChildProfileModel.state == "ACTIVE",
                ParentChildProfileModel.deleted_at.is_(None),
            )
        )
        revisions = connection.scalar(
            select(func.count())
            .select_from(ParentProfileRevisionModel.__table__)
            .join(
                ParentChildProfileModel.__table__,
                ParentChildProfileModel.parent_profile_id
                == ParentProfileRevisionModel.parent_profile_id,
            )
            .where(
                ParentChildProfileModel.owner_issuer == _EXPECTED_ISSUER,
                ParentChildProfileModel.owner_subject == _GATE_B_OWNER_SUBJECT,
                ParentProfileRevisionModel.authored_by_issuer == _EXPECTED_ISSUER,
                ParentProfileRevisionModel.authored_by_subject == _GATE_B_OWNER_SUBJECT,
            )
        )
        receipts = connection.scalar(
            select(func.count())
            .select_from(ParentCommandReceiptModel.__table__)
            .where(
                ParentCommandReceiptModel.principal_issuer == _EXPECTED_ISSUER,
                ParentCommandReceiptModel.principal_subject == _GATE_B_OWNER_SUBJECT,
            )
        )
        connection.rollback()
    return {
        "profiles": int(profiles or 0),
        "active_profiles": int(active_profiles or 0),
        "revisions": int(revisions or 0),
        "receipts": int(receipts or 0),
    }


def _require_database_identity(engine: Engine) -> None:
    database, host_text, port, user, major = _database_identity(engine)
    assert database == _EXPECTED_DATABASE
    assert ip_address(host_text).is_loopback
    assert port == _EXPECTED_PORT
    assert user == "postgres"
    assert major == _EXPECTED_MAJOR


@pytest.fixture
def gate_p2(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[TestClient, Engine, str, str, dict[str, int]]]:
    run_id = os.environ.get("S1A_P_GATE_P2_RUN_ID")
    if run_id is None or re.fullmatch(r"[0-9a-f]{32}", run_id) is None:
        pytest.fail("S1A_P_GATE_P2_RUN_ID is required from the reviewed owner runner")
    dedicated_url = os.environ.get("S1A_P_TEST_DATABASE_URL")
    if not dedicated_url:
        pytest.fail("The dedicated S1a-P test database is required; no write was attempted")

    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", dedicated_url)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "firebase")
    monkeypatch.setenv("SKETCH2LIFE_FIREBASE_PROJECT_ID", "synthetic-parent-gate-p2")
    monkeypatch.setenv("SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED", "1")
    monkeypatch.setenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", "0")
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()

    application = create_app()
    runtime = application.state.be1_runtime
    if runtime.engine is None or runtime.session_factory is None:
        pytest.fail("The configured application database engine is unavailable")
    engine: Engine = runtime.engine
    _require_database_identity(engine)
    before = _table_counts(engine)
    if len(before) != 120 or sum(before.values()) != 36:
        pytest.fail("The task database does not match the accepted Gate B inventory")
    if _run_marker_counts(engine, _EXPECTED_ISSUER, _GATE_B_OWNER_SUBJECT, run_id) != {
        "parent.child_profiles": 0,
        "parent.profile_revisions": 0,
        "parent.command_receipts": 0,
    }:
        pytest.fail("The Gate P2 run marker already exists")
    if _gate_b_owner_counts(engine) != {
        "profiles": 1,
        "active_profiles": 1,
        "revisions": 2,
        "receipts": 3,
    }:
        pytest.fail("The accepted Gate B profile marker is not the expected active baseline")
    with engine.connect() as connection:
        connection.execute(text("SET TRANSACTION READ ONLY"))
        versions = connection.execute(
            text("SELECT version_num FROM public.alembic_version ORDER BY version_num")
        ).scalars().all()
        connection.rollback()
    if versions != [_EXPECTED_REVISION]:
        pytest.fail("The task database Alembic state does not match the accepted baseline")

    subject = _GATE_B_OWNER_SUBJECT
    runtime.identity_verifier = _GateP2TokenVerifier(run_id, runtime.settings)
    application.dependency_overrides[get_parent_role_reader] = lambda: _ApplicationRoleStub(
        run_id
    )
    try:
        with TestClient(application) as client:
            yield client, engine, run_id, subject, before
    finally:
        application.dependency_overrides.clear()
        if runtime.engine is not None:
            runtime.engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def test_parent_owned_list_delete_and_receipts_add_only_six_marked_rows(
    gate_p2: tuple[TestClient, Engine, str, str, dict[str, int]],
) -> None:
    client, engine, run_id, subject, before = gate_p2
    headers = {"Authorization": "Bearer synthetic-owner"}
    profile_body = {"display_name": f"Gate P2 {run_id}", "age_months": 72}
    created = client.post(
        "/v1/parent/profiles",
        headers={**headers, "Idempotency-Key": f"{run_id}-create"},
        json=profile_body,
    )
    assert created.status_code == 201
    profile_id = UUID(created.json()["profile_id"])

    patched_body = {
        "expected_revision": 1,
        "display_name": f"Gate P2 updated {run_id}",
        "age_months": 73,
    }
    patched = client.patch(
        f"/v1/parent/profiles/{profile_id}",
        headers={**headers, "Idempotency-Key": f"{run_id}-patch"},
        json=patched_body,
    )
    assert patched.status_code == 200
    assert patched.json()["revision_no"] == 2
    mismatch = client.patch(
        f"/v1/parent/profiles/{profile_id}",
        headers={**headers, "Idempotency-Key": f"{run_id}-patch"},
        json={**patched_body, "display_name": "Different payload"},
    )
    assert mismatch.status_code == 400
    assert mismatch.json()["code"] == "INVALID_IDEMPOTENCY_KEY"

    first_page = client.get("/v1/parent/profiles?limit=1", headers=headers)
    assert first_page.status_code == 200
    assert len(first_page.json()["items"]) == 1
    next_cursor = first_page.json()["next_cursor"]
    assert isinstance(next_cursor, str)
    second_page = client.get(
        "/v1/parent/profiles",
        params={"limit": "1", "cursor": next_cursor},
        headers=headers,
    )
    assert second_page.status_code == 200
    assert len(second_page.json()["items"]) == 1
    assert second_page.json()["next_cursor"] is None
    paged_ids = [
        first_page.json()["items"][0]["profile_id"],
        second_page.json()["items"][0]["profile_id"],
    ]
    all_profiles = client.get("/v1/parent/profiles?limit=100", headers=headers)
    assert all_profiles.status_code == 200
    assert [item["profile_id"] for item in all_profiles.json()["items"]] == paged_ids
    assert len(set(paged_ids)) == 2
    assert str(profile_id) in paged_ids
    other_owner = client.get(
        "/v1/parent/profiles", headers={"Authorization": "Bearer synthetic-other"}
    )
    assert other_owner.status_code == 200
    assert other_owner.json()["items"] == []
    malformed_cursor = client.get(
        "/v1/parent/profiles?cursor=not-a-cursor", headers=headers
    )
    assert malformed_cursor.status_code == 400
    assert malformed_cursor.json()["field_errors"] == [
        {"field": "cursor", "code": "INVALID_FORMAT"}
    ]

    deletion_key = f"{run_id}-delete"
    deleted = client.delete(
        f"/v1/parent/profiles/{profile_id}",
        headers={**headers, "Idempotency-Key": deletion_key},
    )
    assert deleted.status_code == 202
    assert set(deleted.json()) == {"profile_id", "state", "request_id"}
    assert deleted.json()["state"] == "DELETE_PENDING"

    owner_read = client.get(f"/v1/parent/profiles/{profile_id}", headers=headers)
    assert owner_read.status_code == 200
    assert owner_read.json()["state"] == "DELETE_PENDING"
    assert set(owner_read.json()) == {"profile_id", "state", "request_id"}
    after_delete_list = client.get("/v1/parent/profiles?limit=100", headers=headers)
    assert after_delete_list.status_code == 200
    assert str(profile_id) not in {
        item["profile_id"] for item in after_delete_list.json()["items"]
    }
    malformed_cursor = client.get(
        "/v1/parent/profiles?cursor=not-a-cursor", headers=headers
    )
    assert malformed_cursor.status_code == 400
    assert malformed_cursor.json()["field_errors"] == [
        {"field": "cursor", "code": "INVALID_FORMAT"}
    ]

    patch_replay = client.patch(
        f"/v1/parent/profiles/{profile_id}",
        headers={**headers, "Idempotency-Key": f"{run_id}-patch"},
        json=patched_body,
    )
    assert patch_replay.status_code == 409
    assert patch_replay.json()["code"] == "INVALID_STATE_TRANSITION"
    second_delete = client.delete(
        f"/v1/parent/profiles/{profile_id}",
        headers={**headers, "Idempotency-Key": f"{run_id}-delete-again"},
    )
    assert second_delete.status_code == 409
    assert second_delete.json()["code"] == "INVALID_STATE_TRANSITION"
    deletion_replay = client.delete(
        f"/v1/parent/profiles/{profile_id}",
        headers={**headers, "Idempotency-Key": deletion_key},
    )
    assert deletion_replay.status_code == 202
    assert deletion_replay.json() == deleted.json()

    assert _run_marker_counts(engine, _EXPECTED_ISSUER, subject, run_id) == {
        "parent.child_profiles": 1,
        "parent.profile_revisions": 2,
        "parent.command_receipts": 3,
    }
    after = _table_counts(engine)
    expected = dict(before)
    expected["parent.child_profiles"] += 1
    expected["parent.profile_revisions"] += 2
    expected["parent.command_receipts"] += 3
    assert after == expected
    assert sum(after.values()) == sum(before.values()) + 6

    with engine.connect() as connection:
        connection.execute(text("SET TRANSACTION READ ONLY"))
        receipt_body = connection.scalar(
            select(ParentCommandReceiptModel.response_body).where(
                ParentCommandReceiptModel.principal_issuer == _EXPECTED_ISSUER,
                ParentCommandReceiptModel.principal_subject == subject,
                ParentCommandReceiptModel.operation_scope == "delete_profile",
                ParentCommandReceiptModel.resource_scope == str(profile_id),
                ParentCommandReceiptModel.response_status == 202,
            )
        )
        connection.rollback()
    assert receipt_body is not None
    assert set(receipt_body) == {"profile_id", "state", "request_id"}
