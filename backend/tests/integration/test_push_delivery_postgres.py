"""PostgreSQL acceptance cases for T-NTF1; authored here and intentionally not run in-session.

The only target is ``NTF1_PUSH_DELIVERY_DATABASE_URL`` and it must identify a disposable database
whose name contains both ``ntf1_push_delivery`` and ``be1_acceptance``. The fixture rejects the
master databases and all protected ports before upgrading migrations.
"""

from __future__ import annotations

import hashlib
import importlib.util
import os
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Barrier
from types import ModuleType
from uuid import uuid4

import pytest
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import Engine, create_engine, delete, func, inspect, select, update
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from alembic import command
from sketch2life.application.ports.push_delivery import (
    PushDeliveryRecordResult,
    PushMessage,
    PushSendOutcome,
    PushSendResult,
)
from sketch2life.application.services.notification_templates import eligible_template_keys
from sketch2life.application.services.push_delivery import PushDeliveryWorker
from sketch2life.domain.push_delivery import ENROLL_WINDOW, PushDeliveryStatus, push_pointer
from sketch2life.domain.story_run_reminder import REMINDER_DELAY
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.notifications.push_delivery_fakes import LocalFakePushSender
from sketch2life.infrastructure.notifications.push_delivery_repository import SqlPushDeliveryStore
from sketch2life.infrastructure.notifications.tables import (
    INBOX_ITEMS,
    PUSH_DELIVERIES,
    PUSH_ENDPOINTS,
)
from sketch2life.infrastructure.story_run_lite import tables as story_tables
from sketch2life.infrastructure.story_video.reminder_store import build_story_run_reminder

BACKEND = Path(__file__).resolve().parents[2]
MIGRATION_FILE = BACKEND / "alembic" / "versions" / "20261125_nt_0003_push_deliveries.py"
FORBIDDEN_PORTS = {5432, 5433, 8000, 55439}
NOW = datetime.now(UTC)
RUNS = story_tables.story_runs


class Postgres:
    def __init__(self, engine: Engine, factory: sessionmaker[Session]) -> None:
        self.engine = engine
        self.factory = factory


def _open_postgres(monkeypatch: pytest.MonkeyPatch) -> Postgres:
    url = os.environ.get("NTF1_PUSH_DELIVERY_DATABASE_URL")
    if not url:
        pytest.skip(
            "set NTF1_PUSH_DELIVERY_DATABASE_URL to an isolated disposable PostgreSQL database"
        )
    parsed = make_url(url)
    database = parsed.database or ""
    if "ntf1_push_delivery" not in database or "be1_acceptance" not in database:
        pytest.fail(
            "NTF1_PUSH_DELIVERY_DATABASE_URL must name an isolated "
            "ntf1_push_delivery be1_acceptance database"
        )
    if parsed.port in FORBIDDEN_PORTS or database in {"sketch2life", "sketch2life_m2_s1a"}:
        pytest.fail("NTF1_PUSH_DELIVERY_DATABASE_URL points at a forbidden database or port")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", url)
    monkeypatch.setenv("S1A_P_ALEMBIC_DATABASE_URL", url)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "development")
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    config = Config(str(BACKEND / "alembic.ini"))
    command.upgrade(config, "heads")
    engine = create_engine(url, poolclass=NullPool, hide_parameters=True)
    with engine.begin() as connection:
        connection.execute(delete(PUSH_DELIVERIES))
        connection.execute(delete(INBOX_ITEMS))
    return Postgres(engine, sessionmaker(engine, expire_on_commit=False))


@pytest.fixture
def postgres(monkeypatch: pytest.MonkeyPatch) -> Iterator[Postgres]:
    database = _open_postgres(monkeypatch)
    try:
        yield database
    finally:
        database.engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def _endpoint(
    postgres: Postgres,
    *,
    recipient: str | None = None,
    now: datetime = NOW,
) -> str:
    endpoint_id = str(uuid4())
    recipient_id = recipient or str(uuid4())
    with postgres.factory.begin() as session:
        session.execute(
            PUSH_ENDPOINTS.insert().values(
                push_endpoint_id=endpoint_id,
                recipient_account_id=recipient_id,
                platform_kind="WEB",
                provider_kind="WEB_PUSH",
                endpoint_ciphertext=b"synthetic-ntf1-ciphertext",
                endpoint_fingerprint=hashlib.sha256(endpoint_id.encode()).hexdigest(),
                state="ACTIVE",
                version=1,
                registered_at=now,
                last_seen_at=now,
            )
        )
    return endpoint_id


def _inbox_item(
    postgres: Postgres,
    *,
    recipient: str,
    now: datetime = NOW,
    read_at: datetime | None = None,
    expires_at: datetime | None = None,
    notification_type: str = "RUN_WAIT_REMINDER",
    template_version: int = 1,
) -> str:
    inbox_item_id = str(uuid4())
    dedupe_key = f"ntf1.{uuid4().hex}"
    with postgres.factory.begin() as session:
        session.execute(
            INBOX_ITEMS.insert().values(
                inbox_item_id=inbox_item_id,
                recipient_account_id=recipient,
                recipient_role="parent",
                organization_ref=None,
                notification_type=notification_type,
                template_version=template_version,
                trigger_id=dedupe_key,
                trigger_dedupe_key=dedupe_key,
                command_sha256="0" * 64,
                safe_parameters={},
                created_at=now,
                read_at=read_at,
                expires_at=expires_at,
            )
        )
    return inbox_item_id


def _delivery(
    postgres: Postgres,
    *,
    inbox_item_id: str,
    endpoint_id: str,
    recipient: str,
    created_at: datetime = NOW,
    next_attempt_at: datetime = NOW,
    attempt_count: int = 0,
) -> str:
    delivery_id = str(uuid4())
    with postgres.factory.begin() as session:
        session.execute(
            PUSH_DELIVERIES.insert().values(
                delivery_id=delivery_id,
                inbox_item_id=inbox_item_id,
                push_endpoint_id=endpoint_id,
                recipient_account_id=recipient,
                status="PENDING",
                attempt_count=attempt_count,
                next_attempt_at=next_attempt_at,
                created_at=created_at,
            )
        )
    return delivery_id


def _migration() -> ModuleType:
    spec = importlib.util.spec_from_file_location("ntf1_delivery_migration", MIGRATION_FILE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _PointerCheckingFake(LocalFakePushSender):
    def __init__(self, inbox_item_id: str) -> None:
        super().__init__()
        self._expected_pointer = push_pointer(inbox_item_id)
        self.pointer_count = 0

    def send(self, message: PushMessage) -> PushSendResult:
        assert message.payload == self._expected_pointer
        assert set(message.payload) == {"v", "kind", "inbox_item_id"}
        self.pointer_count += 1
        return super().send(message)


def test_downgrade_refuses_rows_and_succeeds_when_empty_inside_rollback(postgres: Postgres) -> None:
    recipient = str(uuid4())
    endpoint_id = _endpoint(postgres, recipient=recipient)
    item_id = _inbox_item(postgres, recipient=recipient)
    _delivery(postgres, inbox_item_id=item_id, endpoint_id=endpoint_id, recipient=recipient)
    migration = _migration()
    with (
        postgres.engine.begin() as connection,
        Operations.context(MigrationContext.configure(connection)),
        pytest.raises(RuntimeError, match="push delivery downgrade refused"),
    ):
        migration.downgrade()

    with postgres.factory.begin() as session:
        session.execute(delete(PUSH_DELIVERIES))

    class _RollbackDdl(Exception):
        pass

    with (
        pytest.raises(_RollbackDdl),
        postgres.engine.begin() as connection,
        Operations.context(MigrationContext.configure(connection)),
    ):
        migration.downgrade()
        raise _RollbackDdl()

    assert "push_deliveries" in set(
        inspect(postgres.engine).get_table_names(schema="notifications")
    )


def test_enrollment_is_idempotent_and_bounded_to_24_hours(postgres: Postgres) -> None:
    recipient = str(uuid4())
    _endpoint(postgres, recipient=recipient)
    recent = _inbox_item(postgres, recipient=recipient, now=NOW - timedelta(hours=23, minutes=59))
    old = _inbox_item(postgres, recipient=recipient, now=NOW - timedelta(hours=24, minutes=1))
    with postgres.factory() as session:
        store = SqlPushDeliveryStore(session)
        first = store.enroll(
            now=NOW,
            limit=10,
            eligible_templates=eligible_template_keys(),
            window=ENROLL_WINDOW,
        )
        second = store.enroll(
            now=NOW,
            limit=10,
            eligible_templates=eligible_template_keys(),
            window=ENROLL_WINDOW,
        )
    with postgres.factory() as session:
        rows = (
            session.execute(
                select(PUSH_DELIVERIES.c.inbox_item_id).where(
                    PUSH_DELIVERIES.c.inbox_item_id.in_((recent, old))
                )
            )
            .scalars()
            .all()
        )
    assert first == 1 and second == 0
    assert rows == [recent]


def test_one_enroll_batch_preserves_inbox_order_per_endpoint(postgres: Postgres) -> None:
    recipient = str(uuid4())
    _endpoint(postgres, recipient=recipient)
    older = _inbox_item(postgres, recipient=recipient, now=NOW - timedelta(minutes=3))
    newer = _inbox_item(postgres, recipient=recipient, now=NOW - timedelta(minutes=1))
    with postgres.factory() as session:
        enrolled = SqlPushDeliveryStore(session).enroll(
            now=NOW,
            limit=10,
            eligible_templates=eligible_template_keys(),
            window=ENROLL_WINDOW,
        )
    with postgres.factory() as session:
        first = (
            SqlPushDeliveryStore(session)
            .claim_due(
                now=NOW,
                eligible_templates=eligible_template_keys(),
            )
            .claim
        )
    assert enrolled == 2
    assert first is not None and first.inbox_item_id == older
    assert newer != older


def test_skip_locked_claimers_take_distinct_rows(postgres: Postgres) -> None:
    claims_barrier = Barrier(2)
    endpoints = []
    for _ in range(2):
        recipient = str(uuid4())
        endpoint_id = _endpoint(postgres, recipient=recipient)
        item_id = _inbox_item(postgres, recipient=recipient)
        endpoints.append((endpoint_id, recipient, item_id))
    with postgres.factory() as session:
        SqlPushDeliveryStore(session).enroll(
            now=NOW,
            limit=2,
            eligible_templates=eligible_template_keys(),
            window=ENROLL_WINDOW,
        )

    def claim_one() -> str | None:
        with postgres.factory() as session:
            claims_barrier.wait()
            claim = (
                SqlPushDeliveryStore(session)
                .claim_due(
                    now=NOW,
                    eligible_templates=eligible_template_keys(),
                )
                .claim
            )
            return claim.delivery_id if claim is not None else None

    with ThreadPoolExecutor(max_workers=2) as executor:
        first, second = executor.map(lambda _index: claim_one(), range(2))
    assert first is not None and second is not None and first != second


def test_compare_and_set_ignores_late_finisher(postgres: Postgres) -> None:
    recipient = str(uuid4())
    endpoint_id = _endpoint(postgres, recipient=recipient)
    item_id = _inbox_item(postgres, recipient=recipient)
    delivery_id = _delivery(
        postgres,
        inbox_item_id=item_id,
        endpoint_id=endpoint_id,
        recipient=recipient,
    )
    with postgres.factory() as session:
        store = SqlPushDeliveryStore(session)
        first = store.claim_due(now=NOW, eligible_templates=eligible_template_keys()).claim
    assert first is not None
    with postgres.factory() as session:
        second = (
            SqlPushDeliveryStore(session)
            .claim_due(
                now=NOW + timedelta(seconds=120),
                eligible_templates=eligible_template_keys(),
            )
            .claim
        )
    assert second is not None and second.delivery_id == delivery_id
    with postgres.factory() as session:
        stale = SqlPushDeliveryStore(session).record_outcome(
            claim=first,
            result=PushSendResult(PushSendOutcome.SENT),
            now=NOW + timedelta(seconds=120),
        )
    with postgres.factory() as session:
        applied = SqlPushDeliveryStore(session).record_outcome(
            claim=second,
            result=PushSendResult(PushSendOutcome.SENT),
            now=NOW + timedelta(seconds=120),
        )
    assert stale is PushDeliveryRecordResult.STALE
    assert applied is PushDeliveryRecordResult.SENT


def test_dead_endpoint_revoke_bumps_version_and_later_pending_rows_skip(postgres: Postgres) -> None:
    recipient = str(uuid4())
    endpoint_id = _endpoint(postgres, recipient=recipient)
    first_item = _inbox_item(postgres, recipient=recipient)
    first_delivery = _delivery(
        postgres,
        inbox_item_id=first_item,
        endpoint_id=endpoint_id,
        recipient=recipient,
    )
    with postgres.factory() as session:
        claim = (
            SqlPushDeliveryStore(session)
            .claim_due(
                now=NOW,
                eligible_templates=eligible_template_keys(),
            )
            .claim
        )
    assert claim is not None and claim.delivery_id == first_delivery
    with postgres.factory() as session:
        result = SqlPushDeliveryStore(session).record_outcome(
            claim=claim,
            result=PushSendResult(PushSendOutcome.ENDPOINT_GONE),
            now=NOW,
        )
    assert result is PushDeliveryRecordResult.DEAD_ENDPOINT
    with postgres.factory() as session:
        endpoint = session.execute(
            select(PUSH_ENDPOINTS.c.state, PUSH_ENDPOINTS.c.version).where(
                PUSH_ENDPOINTS.c.push_endpoint_id == endpoint_id
            )
        ).one()
    assert endpoint.state == "REVOKED" and endpoint.version == 2

    later_item = _inbox_item(postgres, recipient=recipient)
    _delivery(postgres, inbox_item_id=later_item, endpoint_id=endpoint_id, recipient=recipient)
    with postgres.factory() as session:
        skipped = SqlPushDeliveryStore(session).claim_due(
            now=NOW,
            eligible_templates=eligible_template_keys(),
        )
    assert skipped.skipped is True


def test_read_item_is_skipped_at_claim(postgres: Postgres) -> None:
    recipient = str(uuid4())
    endpoint_id = _endpoint(postgres, recipient=recipient)
    item_id = _inbox_item(postgres, recipient=recipient)
    _delivery(postgres, inbox_item_id=item_id, endpoint_id=endpoint_id, recipient=recipient)
    with postgres.factory.begin() as session:
        session.execute(
            update(INBOX_ITEMS).where(INBOX_ITEMS.c.inbox_item_id == item_id).values(read_at=NOW)
        )
    with postgres.factory() as session:
        result = SqlPushDeliveryStore(session).claim_due(
            now=NOW,
            eligible_templates=eligible_template_keys(),
        )
    assert result.skipped is True


def test_per_endpoint_order_blocks_later_row_but_not_other_endpoint(postgres: Postgres) -> None:
    first_recipient = str(uuid4())
    first_endpoint = _endpoint(postgres, recipient=first_recipient)
    first_item = _inbox_item(postgres, recipient=first_recipient)
    later_item = _inbox_item(postgres, recipient=first_recipient)
    _delivery(
        postgres,
        inbox_item_id=first_item,
        endpoint_id=first_endpoint,
        recipient=first_recipient,
        created_at=NOW - timedelta(minutes=2),
        next_attempt_at=NOW + timedelta(minutes=1),
    )
    _delivery(
        postgres,
        inbox_item_id=later_item,
        endpoint_id=first_endpoint,
        recipient=first_recipient,
        created_at=NOW - timedelta(minutes=1),
        next_attempt_at=NOW,
    )
    second_recipient = str(uuid4())
    second_endpoint = _endpoint(postgres, recipient=second_recipient)
    second_item = _inbox_item(postgres, recipient=second_recipient)
    expected = _delivery(
        postgres,
        inbox_item_id=second_item,
        endpoint_id=second_endpoint,
        recipient=second_recipient,
        created_at=NOW - timedelta(minutes=1),
        next_attempt_at=NOW,
    )

    with postgres.factory() as session:
        claim = (
            SqlPushDeliveryStore(session)
            .claim_due(
                now=NOW,
                eligible_templates=eligible_template_keys(),
            )
            .claim
        )
    assert claim is not None and claim.delivery_id == expected


def test_reminder_to_push_end_to_end_uses_one_safe_inbox_pointer(
    postgres: Postgres,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    run_id = str(uuid4())
    recipient = str(uuid4())
    wait_since = NOW - REMINDER_DELAY
    with postgres.factory.begin() as session:
        session.execute(
            RUNS.insert().values(
                run_id=run_id,
                actor_scope_kind="PARENT_ACCOUNT",
                actor_scope_ref=str(uuid4()),
                profile_ref=str(uuid4()),
                run_state="SCRIPT_REVIEW",
                revision=1,
                version=1,
                job_state="SUCCEEDED",
                retryable=False,
                active_owner_parent_account_id=recipient,
                adult_wait_started_at=wait_since,
                last_meaningful_activity_at=wait_since,
                created_at=NOW - timedelta(days=60),
                updated_at=wait_since,
            )
        )
    with postgres.factory() as session:
        reminder = build_story_run_reminder(session).run_once(now=NOW, limit=10)
    assert reminder.created == 1
    endpoint_id = _endpoint(postgres, recipient=recipient)
    with postgres.factory() as session:
        inbox_item_id = session.scalar(
            select(INBOX_ITEMS.c.inbox_item_id).where(
                INBOX_ITEMS.c.recipient_account_id == recipient
            )
        )
    assert inbox_item_id is not None
    sender = _PointerCheckingFake(str(inbox_item_id))
    with postgres.factory() as session:
        report = PushDeliveryWorker(SqlPushDeliveryStore(session), sender).run_once(
            now=NOW,
            batch=10,
        )
    assert report.enrolled == 1 and report.sent == 1
    assert len(sender.records) == sender.pointer_count == 1
    with postgres.factory() as session:
        row = session.execute(
            select(PUSH_DELIVERIES.c.status, PUSH_DELIVERIES.c.push_endpoint_id).where(
                PUSH_DELIVERIES.c.push_endpoint_id == endpoint_id
            )
        ).one()
        inbox_count = session.scalar(
            select(func.count())
            .select_from(INBOX_ITEMS)
            .where(INBOX_ITEMS.c.recipient_account_id == recipient)
        )
    assert row.status == PushDeliveryStatus.SENT.value
    assert inbox_count == 1
