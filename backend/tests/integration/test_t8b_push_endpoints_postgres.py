"""PostgreSQL acceptance cases for T-8b; requires an explicitly named disposable database.

This module is authored for the later authorized integration run. It was not run in the T-8b
implementation session. The main target is ``T8B_PUSH_ENDPOINTS_DATABASE_URL``; downgrade checks
use a separate empty target ``T8B_PUSH_DOWNGRADE_DATABASE_URL``.
"""

from __future__ import annotations

import importlib.util
import os
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, select, text, update
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from alembic import command
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.notifications import NotificationCommandV1
from sketch2life.application.services.push_endpoints import (
    PushEndpointCommandService,
    PushEndpointError,
    PushEndpointRegistration,
)
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.notifications.inbox_repository import SqlNotificationProducer
from sketch2life.infrastructure.notifications.push_endpoint_fakes import (
    SyntheticEndpointEncryptor,
    SyntheticEndpointFingerprinter,
    SyntheticReceiptFingerprinter,
    SyntheticRegistrationProofVerifier,
)
from sketch2life.infrastructure.notifications.push_endpoint_repository import SqlPushEndpointStore
from sketch2life.infrastructure.notifications.tables import INBOX_ITEMS, PUSH_ENDPOINTS
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    Be1CommandReceiptModel,
)

BACKEND = Path(__file__).resolve().parents[2]
MIGRATION_FILE = BACKEND / "alembic" / "versions" / "20261121_nt_0002_push_endpoints.py"
REVISION = "20261121_nt_0002"
PARENT = "20261121_pg_0001"
FORBIDDEN_PORTS = {5432, 5433, 8000, 55439}
ISSUER = "synthetic-t8b-issuer"
NOW = datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class Postgres:
    engine: Engine
    factory: sessionmaker[Session]
    url: str


def _open_postgres(monkeypatch: pytest.MonkeyPatch, env_name: str, name_fragment: str) -> Postgres:
    url = os.environ.get(env_name)
    if not url:
        pytest.skip(f"set {env_name} to an isolated disposable PostgreSQL database")
    from sqlalchemy.engine import make_url

    parsed = make_url(url)
    database = parsed.database or ""
    if name_fragment not in database or "be1_acceptance" not in database:
        pytest.fail(f"{env_name} must name an isolated {name_fragment} be1_acceptance database")
    if parsed.port in FORBIDDEN_PORTS or database in {"sketch2life", "sketch2life_m2_s1a"}:
        pytest.fail(f"{env_name} points at a forbidden database or port")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", url)
    monkeypatch.setenv("S1A_P_ALEMBIC_DATABASE_URL", url)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "development")
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    config = Config(str(BACKEND / "alembic.ini"))
    command.upgrade(config, "heads")
    engine = create_engine(url, poolclass=NullPool, hide_parameters=True)
    return Postgres(engine, sessionmaker(engine, expire_on_commit=False), url)


@pytest.fixture
def postgres(monkeypatch: pytest.MonkeyPatch) -> Iterator[Postgres]:
    pg = _open_postgres(monkeypatch, "T8B_PUSH_ENDPOINTS_DATABASE_URL", "t8b_push_endpoints")
    try:
        yield pg
    finally:
        pg.engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


@pytest.fixture
def downgrade_postgres(monkeypatch: pytest.MonkeyPatch) -> Iterator[Postgres]:
    pg = _open_postgres(
        monkeypatch,
        "T8B_PUSH_DOWNGRADE_DATABASE_URL",
        "t8b_push_downgrade",
    )
    try:
        yield pg
    finally:
        pg.engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def _identity(pg: Postgres, label: str, *, role: str = "parent") -> tuple[str, str]:
    subject = f"synthetic-t8b-{label}-{uuid4().hex}"
    with pg.factory.begin() as db:
        identity = AdultIdentityModel(
            subject=subject,
            issuer=ISSUER,
            state="active",
            account_role=role,
        )
        db.add(identity)
        db.flush()
        account_id = str(identity.account_id)
    return subject, account_id


def _service(
    db: Session,
    verifier: SyntheticRegistrationProofVerifier,
) -> PushEndpointCommandService:
    return PushEndpointCommandService(
        store=SqlPushEndpointStore(db),
        proof_verifier=verifier,
        encryptor=SyntheticEndpointEncryptor(b"e" * 32),
        endpoint_fingerprinter=SyntheticEndpointFingerprinter(b"f" * 32),
        receipt_fingerprinter=SyntheticReceiptFingerprinter(b"r" * 32),
    )


def _principal(subject: str) -> VerifiedPrincipal:
    return VerifiedPrincipal(subject=subject, issuer=ISSUER, roles=frozenset())


def _registration(
    verifier: SyntheticRegistrationProofVerifier,
    subject: str,
    endpoint: bytes,
) -> PushEndpointRegistration:
    proof = verifier.issue(
        actor_subject=subject,
        provider_kind="WEB_PUSH",
        endpoint=endpoint,
        consent_granted=True,
    )
    return PushEndpointRegistration(
        contract="PushEndpointRegistrationV1",
        platform_kind="WEB",
        provider_kind="WEB_PUSH",
        encrypted_registration_proof=proof,
        app_version="t8b-test",
    )


def _register(
    pg: Postgres,
    verifier: SyntheticRegistrationProofVerifier,
    subject: str,
    endpoint: bytes,
    key: str,
):
    with pg.factory() as db:
        return _service(db, verifier).register(
            principal=_principal(subject),
            command=_registration(verifier, subject, endpoint),
            idempotency_key=key,
        )


def _migration_module():
    spec = importlib.util.spec_from_file_location("t8b_push_endpoint_migration", MIGRATION_FILE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_push_migration_metadata_checks_indexes_and_trigger(postgres: Postgres) -> None:
    inspector = inspect(postgres.engine)
    checks = {
        item["name"]
        for item in inspector.get_check_constraints("push_endpoints", schema="notifications")
    }
    indexes = {
        item["name"] for item in inspector.get_indexes("push_endpoints", schema="notifications")
    }
    expected_checks = {
        "ck_push_endpoint_platform_provider",
        "ck_push_endpoint_ciphertext_size",
        "ck_push_endpoint_fingerprint",
        "ck_push_endpoint_state",
        "ck_push_endpoint_version",
        "ck_push_endpoint_times",
        "ck_push_endpoint_revoked_at",
        "ck_push_endpoint_app_version",
    }
    assert expected_checks <= checks
    assert {
        "uq_push_endpoint_active_provider_fingerprint",
        "ix_push_endpoint_recipient_state",
    } <= indexes
    with postgres.engine.connect() as connection:
        triggers = set(
            connection.execute(
                text(
                    "SELECT tgname FROM pg_trigger "
                    "WHERE tgrelid = 'notifications.push_endpoints'::regclass AND NOT tgisinternal"
                )
            ).scalars()
        )
    assert triggers == {"trg_push_endpoint_guard_update", "trg_push_endpoint_prevent_delete"}
    assert {column.name for column in PUSH_ENDPOINTS.columns} == {
        "push_endpoint_id", "recipient_account_id", "platform_kind", "provider_kind",
        "endpoint_ciphertext", "endpoint_fingerprint", "state", "version", "registered_at",
        "last_seen_at", "revoked_at", "app_version",
    }


def test_empty_downgrade_and_nonempty_refusal(downgrade_postgres: Postgres) -> None:
    migration = _migration_module()
    with downgrade_postgres.engine.connect() as connection:
        transaction = connection.begin()
        try:
            count = connection.execute(
                select(PUSH_ENDPOINTS.c.push_endpoint_id).limit(1)
            ).first()
            assert count is None, "downgrade target must be an empty dedicated database"
            # nt_0003 (T-NTF1) holds an FK to this table; its own downgrade runs first.
            connection.execute(text("DROP TABLE notifications.push_deliveries"))
            with Operations.context(MigrationContext.configure(connection)):
                migration.downgrade()
            transaction.rollback()
        finally:
            if transaction.is_active:
                transaction.rollback()

        transaction = connection.begin()
        try:
            now = datetime.now(UTC)
            connection.execute(
                PUSH_ENDPOINTS.insert().values(
                    push_endpoint_id=str(uuid4()),
                    recipient_account_id=str(uuid4()),
                    platform_kind="WEB",
                    provider_kind="WEB_PUSH",
                    endpoint_ciphertext=b"synthetic-ciphertext",
                    endpoint_fingerprint="a" * 64,
                    state="ACTIVE",
                    version=1,
                    registered_at=now,
                    last_seen_at=now,
                    revoked_at=None,
                    app_version=None,
                )
            )
            connection.execute(text("DROP TABLE notifications.push_deliveries"))
            with (
                Operations.context(MigrationContext.configure(connection)),
                pytest.raises(RuntimeError, match="rows exist"),
            ):
                migration.downgrade()
            transaction.rollback()
        finally:
            if transaction.is_active:
                transaction.rollback()


def test_two_concurrent_same_key_single_row_and_same_201(postgres: Postgres) -> None:
    subject, _ = _identity(postgres, "same-key")
    verifier = SyntheticRegistrationProofVerifier()
    endpoint = f"https://push.invalid/{uuid4().hex}".encode()
    request = _registration(verifier, subject, endpoint)
    principal = _principal(subject)

    def register_once():
        with postgres.factory() as db:
            try:
                result = _service(db, verifier).register(
                    principal=principal, command=request, idempotency_key="same-key"
                )
                return (201, result.endpoint_id, result.version)
            except PushEndpointError as exc:
                return (exc.status_code, exc.code, exc.current_version)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _index: register_once(), (1, 2)))
    assert results[0] == results[1] and results[0][0] == 201
    with postgres.factory() as db:
        rows = db.execute(
            select(PUSH_ENDPOINTS).where(
                PUSH_ENDPOINTS.c.recipient_account_id == _account(postgres, subject)
            )
        ).all()
        receipts = db.scalars(
            select(Be1CommandReceiptModel).where(
                Be1CommandReceiptModel.principal_ref == subject,
                Be1CommandReceiptModel.operation_scope == "POST /notifications/push-endpoints",
                Be1CommandReceiptModel.idempotency_key == "same-key",
            )
        ).all()
    assert len(rows) == 1 and len(receipts) == 1


def test_two_keys_same_owner_same_fingerprint_single_active_row(postgres: Postgres) -> None:
    subject, account_id = _identity(postgres, "same-owner")
    verifier = SyntheticRegistrationProofVerifier()
    endpoint = f"https://push.invalid/{uuid4().hex}".encode()
    first = _register(postgres, verifier, subject, endpoint, "owner-key-1")
    second = _register(postgres, verifier, subject, endpoint, "owner-key-2")
    assert first.endpoint_id == second.endpoint_id and first.version == second.version == 1
    with postgres.factory() as db:
        rows = db.execute(
            select(PUSH_ENDPOINTS).where(
                PUSH_ENDPOINTS.c.recipient_account_id == account_id,
                PUSH_ENDPOINTS.c.state == "ACTIVE",
            )
        ).all()
    assert len(rows) == 1


def test_cross_owner_fingerprint_race_no_transfer_or_disclosure(postgres: Postgres) -> None:
    first_subject, first_account = _identity(postgres, "race-a")
    second_subject, second_account = _identity(postgres, "race-b")
    verifier = SyntheticRegistrationProofVerifier()
    endpoint = f"https://push.invalid/{uuid4().hex}".encode()

    def register(subject: str, key: str):
        with postgres.factory() as db:
            try:
                result = _service(db, verifier).register(
                    principal=_principal(subject),
                    command=_registration(verifier, subject, endpoint),
                    idempotency_key=key,
                )
                return (201, result.endpoint_id)
            except PushEndpointError as exc:
                return (exc.status_code, exc.code)

    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = ((first_subject, "race-a"), (second_subject, "race-b"))
        results = list(pool.map(lambda args: register(*args), jobs))
    assert sorted(result[0] for result in results) == [201, 404]
    assert (404, "RESOURCE_NOT_FOUND") in results
    with postgres.factory() as db:
        rows = db.execute(
            select(PUSH_ENDPOINTS).where(
                PUSH_ENDPOINTS.c.endpoint_fingerprint
                == _endpoint_fingerprint(verifier, endpoint)
            )
        ).all()
        receipts = db.scalars(
            select(Be1CommandReceiptModel).where(
                Be1CommandReceiptModel.operation_scope == "POST /notifications/push-endpoints",
                Be1CommandReceiptModel.idempotency_key.in_(["race-a", "race-b"]),
            )
        ).all()
    assert len(rows) == 1
    assert rows[0].recipient_account_id in {first_account, second_account}
    assert len(receipts) == 1


def test_concurrent_revoke_one_winner_other_stale(postgres: Postgres) -> None:
    subject, _ = _identity(postgres, "revoke-race")
    verifier = SyntheticRegistrationProofVerifier()
    registered = _register(
        postgres, verifier, subject, f"https://push.invalid/{uuid4().hex}".encode(), "race-register"
    )

    def revoke(key: str):
        with postgres.factory() as db:
            try:
                _service(db, verifier).revoke(
                    principal=_principal(subject),
                    endpoint_id=registered.endpoint_id,
                    expected_version=1,
                    idempotency_key=key,
                )
                return (204, None)
            except PushEndpointError as exc:
                return (exc.status_code, exc.current_version)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(revoke, ("revoke-a", "revoke-b")))
    assert sorted(status for status, _version in results) == [204, 409]
    assert (409, 2) in results


def test_revoke_replay_after_version_increment(postgres: Postgres) -> None:
    subject, _ = _identity(postgres, "revoke-replay")
    verifier = SyntheticRegistrationProofVerifier()
    registered = _register(
        postgres, verifier, subject, f"https://push.invalid/{uuid4().hex}".encode(), "rr-register"
    )
    with postgres.factory() as db:
        service = _service(db, verifier)
        service.revoke(
            principal=_principal(subject), endpoint_id=registered.endpoint_id,
            expected_version=1, idempotency_key="rr-revoke",
        )
    with postgres.factory() as db:
        _service(db, verifier).revoke(
            principal=_principal(subject), endpoint_id=registered.endpoint_id,
            expected_version=1, idempotency_key="rr-revoke",
        )
    with postgres.factory() as db:
        row = db.execute(
            select(PUSH_ENDPOINTS).where(
                PUSH_ENDPOINTS.c.push_endpoint_id == registered.endpoint_id
            )
        ).mappings().one()
    assert (row["state"], row["version"]) == ("REVOKED", 2)


def test_register_rollback_leaves_no_receipt(postgres: Postgres) -> None:
    subject, account_id = _identity(postgres, "rollback")
    verifier = SyntheticRegistrationProofVerifier()

    class FailingEncryptor:
        def encrypt(self, *, plaintext: bytes, associated_data: bytes) -> bytes:
            raise RuntimeError("synthetic key unavailable")

    with postgres.factory() as db:
        service = PushEndpointCommandService(
            store=SqlPushEndpointStore(db),
            proof_verifier=verifier,
            encryptor=FailingEncryptor(),
            endpoint_fingerprinter=SyntheticEndpointFingerprinter(b"f" * 32),
            receipt_fingerprinter=SyntheticReceiptFingerprinter(b"r" * 32),
        )
        with pytest.raises(PushEndpointError) as failure:
            service.register(
                principal=_principal(subject),
                command=_registration(verifier, subject, b"https://push.invalid/rollback"),
                idempotency_key="rollback-key",
            )
    with postgres.factory() as db:
        receipt = db.get(
            Be1CommandReceiptModel,
            (subject, "POST /notifications/push-endpoints", "rollback-key"),
        )
        endpoint_count = db.scalar(
            select(PUSH_ENDPOINTS.c.push_endpoint_id).where(
                PUSH_ENDPOINTS.c.recipient_account_id == account_id
            ).limit(1)
        )
    assert failure.value.code == "PUSH_REGISTRATION_UNAVAILABLE"
    assert receipt is None and endpoint_count is None


def test_actor_disabled_before_replay_denied(postgres: Postgres) -> None:
    subject, _ = _identity(postgres, "disabled-replay")
    verifier = SyntheticRegistrationProofVerifier()
    command = _registration(verifier, subject, f"https://push.invalid/{uuid4().hex}".encode())
    with postgres.factory() as db:
        _service(db, verifier).register(
            principal=_principal(subject), command=command, idempotency_key="disabled-key"
        )
    with postgres.factory.begin() as db:
        db.execute(
            update(AdultIdentityModel)
            .where(AdultIdentityModel.subject == subject)
            .values(state="disabled")
        )
    with postgres.factory() as db, pytest.raises(PushEndpointError) as denied:
        _service(db, verifier).register(
            principal=_principal(subject), command=command, idempotency_key="disabled-key"
        )
    assert (denied.value.status_code, denied.value.code) == (404, "RESOURCE_NOT_FOUND")


def test_revoked_reregister_new_ref(postgres: Postgres) -> None:
    subject, account_id = _identity(postgres, "revoked-reregister")
    verifier = SyntheticRegistrationProofVerifier()
    endpoint = f"https://push.invalid/{uuid4().hex}".encode()
    first = _register(postgres, verifier, subject, endpoint, "revoked-r1")
    with postgres.factory() as db:
        _service(db, verifier).revoke(
            principal=_principal(subject), endpoint_id=first.endpoint_id,
            expected_version=1, idempotency_key="revoked-d1",
        )
    second = _register(postgres, verifier, subject, endpoint, "revoked-r2")
    assert second.endpoint_id != first.endpoint_id
    with postgres.factory() as db:
        rows = db.execute(
            select(PUSH_ENDPOINTS).where(PUSH_ENDPOINTS.c.recipient_account_id == account_id)
        ).mappings().all()
    assert {(row["state"], row["version"]) for row in rows} == {("REVOKED", 2), ("ACTIVE", 1)}


def test_receipts_and_table_never_contain_plaintext(postgres: Postgres) -> None:
    subject, account_id = _identity(postgres, "no-plaintext")
    verifier = SyntheticRegistrationProofVerifier()
    raw_endpoint = f"https://push.invalid/secret-{uuid4().hex}".encode()
    request = _registration(verifier, subject, raw_endpoint)
    with postgres.factory() as db:
        result = _service(db, verifier).register(
            principal=_principal(subject), command=request, idempotency_key="no-plaintext"
        )
    with postgres.factory() as db:
        row = db.execute(
            select(PUSH_ENDPOINTS).where(PUSH_ENDPOINTS.c.push_endpoint_id == result.endpoint_id)
        ).mappings().one()
        receipt = db.get(
            Be1CommandReceiptModel,
            (subject, "POST /notifications/push-endpoints", "no-plaintext"),
        )
    assert raw_endpoint not in bytes(row["endpoint_ciphertext"])
    assert request.encrypted_registration_proof not in str(receipt.response_json)
    assert set(receipt.response_json) == {"endpoint_id", "status", "version"}
    assert account_id == row["recipient_account_id"]


def test_inbox_survives_revoke(postgres: Postgres) -> None:
    subject, account_id = _identity(postgres, "inbox-survives")
    verifier = SyntheticRegistrationProofVerifier()
    registered = _register(
        postgres,
        verifier,
        subject,
        f"https://push.invalid/{uuid4().hex}".encode(),
        "inbox-register",
    )
    notice_id = str(uuid4())
    with postgres.factory.begin() as db:
        SqlNotificationProducer(db).enqueue(
            NotificationCommandV1(
                recipient_account_id=account_id,
                recipient_role="parent",
                notification_type="CLASS_ARCHIVED",
                template_version=1,
                trigger_id=f"t8b.{uuid4().hex}",
                dedupe_key=f"t8b.{uuid4().hex}",
                safe_parameters={"count": 1},
            )
        )
        notice_id = db.scalar(
            select(INBOX_ITEMS.c.inbox_item_id)
            .where(INBOX_ITEMS.c.recipient_account_id == account_id)
            .order_by(INBOX_ITEMS.c.created_at.desc())
            .limit(1)
        )
    with postgres.factory() as db:
        _service(db, verifier).revoke(
            principal=_principal(subject), endpoint_id=registered.endpoint_id,
            expected_version=1, idempotency_key="inbox-revoke",
        )
    with postgres.factory() as db:
        row = db.execute(
            select(INBOX_ITEMS.c.inbox_item_id).where(INBOX_ITEMS.c.inbox_item_id == notice_id)
        ).first()
    assert row is not None


def _account(pg: Postgres, subject: str) -> str:
    with pg.factory() as db:
        return str(db.get(AdultIdentityModel, subject).account_id)


def _endpoint_fingerprint(
    verifier: SyntheticRegistrationProofVerifier, endpoint: bytes
) -> str:
    del verifier
    return SyntheticEndpointFingerprinter(b"f" * 32).fingerprint(
        provider_kind="WEB_PUSH", endpoint=endpoint
    )
