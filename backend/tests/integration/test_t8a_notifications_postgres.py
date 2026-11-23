"""FEAT-066 T-8a: the notification inbox on PostgreSQL (SRS l.784, l.812, l.1681, l.1697).

Runs only against a disposable database whose name contains ``be1_acceptance`` and ``frc08``.
Principals are injected through the ``X-Test-Principal`` header (the verified adult dependency is
overridden); every identity and parameter is synthetic. Producers act through
``SqlNotificationProducer`` with a controlled clock, so created and expiry times are exact.

The migration round trip (downgrade to ``20261120_cls_0002`` by explicit revision and back) runs
with alembic against a separate fresh database (see the evidence note); here the constraint, index
and schema definitions, the downgrade guard statement and the behaviour of the three routes and
the producer are exercised.
"""

from __future__ import annotations

import importlib.util
import json
import os
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Barrier
from typing import Any
from uuid import uuid4

import pytest
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from fastapi import FastAPI, Header
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError, IntegrityError

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.notifications import (
    EnqueueResult,
    NotificationCommandV1,
    NotificationDedupeConflict,
    NotificationRejected,
)
from sketch2life.application.services.notifications import READ_ALL_SCOPE, READ_ONE_SCOPE
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.notifications.inbox_repository import SqlNotificationProducer
from sketch2life.infrastructure.notifications.tables import INBOX_ITEMS, METADATA
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    Be1CommandReceiptModel,
)
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult

ISSUER = "synthetic-t8a-issuer"
MIGRATION = (
    Path(__file__).resolve().parents[2]
    / "alembic"
    / "versions"
    / "20261120_nt_0001_notifications_inbox.py"
)
ROLES = ("parent", "teacher", "school_manager", "platform_admin")


class Clock:
    """A settable clock for the producer and nothing else (the service uses the real one)."""

    def __init__(self, moment: datetime) -> None:
        self.moment = moment

    def __call__(self) -> datetime:
        return self.moment


@dataclass
class Directory:
    app: FastAPI
    client: TestClient
    token: str
    subjects: dict[str, str] = field(default_factory=dict)
    accounts: dict[str, str] = field(default_factory=dict)
    roles: dict[str, str] = field(default_factory=dict)
    counter: int = 0

    def factory(self) -> Any:
        return self.app.state.be1_runtime.session_factory

    def header(self, who: str, **extra: str) -> dict[str, str]:
        headers = {"X-Test-Principal": self.subjects[who]}
        headers.update(extra)
        return headers

    def command(self, who: str, **overrides: Any) -> NotificationCommandV1:
        self.counter += 1
        base = NotificationCommandV1(
            recipient_account_id=self.accounts[who],
            recipient_role=self.roles[who],
            notification_type="CLASS_ARCHIVED",
            template_version=1,
            trigger_id=f"trg.{self.token}.{self.counter}",
            dedupe_key=f"dk.{self.token}.{self.counter}",
            safe_parameters={"count": self.counter, "class_ref": f"cls_{self.counter}"},
        )
        return replace(base, **overrides)

    def produce(self, who: str, *, at: datetime | None = None, **overrides: Any) -> EnqueueResult:
        clock = Clock(at or datetime.now(UTC) - timedelta(minutes=5))
        with self.factory().begin() as db:
            return SqlNotificationProducer(db, clock).enqueue(self.command(who, **overrides))

    def list_page(self, who: str, query: str = "") -> Any:
        return self.client.get(f"/v1/notifications?{query}", headers=self.header(who))

    def read(self, who: str, item_id: str, key: str | None = None, **extra: str) -> Any:
        return self.client.post(
            f"/v1/notifications/{item_id}/read",
            headers=self.header(who, **{"Idempotency-Key": key or uuid4().hex}, **extra),
        )

    def read_all(self, who: str, key: str | None = None) -> Any:
        return self.client.post(
            "/v1/notifications/read-all",
            headers=self.header(who, **{"Idempotency-Key": key or uuid4().hex}),
        )

    def row(self, item_id: str) -> Any:
        with self.factory()() as db:
            return (
                db.execute(select(INBOX_ITEMS).where(INBOX_ITEMS.c.inbox_item_id == item_id))
                .mappings()
                .one()
            )

    def receipts(self, who: str, scope: str | None = None) -> list[Be1CommandReceiptModel]:
        with self.factory()() as db:
            statement = select(Be1CommandReceiptModel).where(
                Be1CommandReceiptModel.principal_ref == self.subjects[who]
            )
            if scope is not None:
                statement = statement.where(Be1CommandReceiptModel.operation_scope == scope)
            return list(db.scalars(statement))


def _add_identity(
    db: Any, subject: str, role: str | None, *, state: str = "active", issuer: str = ISSUER
) -> str:
    row = AdultIdentityModel(subject=subject, issuer=issuer, state=state, account_role=role)
    db.add(row)
    db.flush()
    return str(row.account_id)


@pytest.fixture
def directory(monkeypatch: pytest.MonkeyPatch) -> Iterator[Directory]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL to a disposable PostgreSQL database")
    name = database_url.rsplit("/", 1)[-1]
    if "be1_acceptance" not in name or "frc08" not in name:
        pytest.fail("BE1_TEST_DATABASE_URL must be a disposable frc08*be1_acceptance db")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", database_url)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "development")
    monkeypatch.setenv("SKETCH2LIFE_AI_PROVIDER", "disabled")
    monkeypatch.delenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", raising=False)
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    app = create_app()
    runtime = app.state.be1_runtime
    if runtime.engine is None or runtime.session_factory is None:
        pytest.fail("PostgreSQL runtime did not initialize")
    token = uuid4().hex[:8]
    d = Directory(app, TestClient(app), token)
    with runtime.session_factory.begin() as db:
        people: tuple[tuple[str, str | None, str, str], ...] = (
            ("p1", "parent", "active", ISSUER),
            ("p2", "parent", "active", ISSUER),
            ("t1", "teacher", "active", ISSUER),
            ("m1", "school_manager", "active", ISSUER),
            ("a1", "platform_admin", "active", ISSUER),
            ("inactive", "parent", "disabled", ISSUER),
            ("foreign", "parent", "active", "synthetic-other-issuer"),
            ("norole", None, "active", ISSUER),
        )
        for label, role, state, issuer in people:
            subject = f"synthetic-t8a-{label}-{token}"
            d.subjects[label] = subject
            d.accounts[label] = _add_identity(db, subject, role, state=state, issuer=issuer)
            d.roles[label] = role or "parent"
        # A verified bearer that has no identity row at all.
        d.subjects["stranger"] = f"synthetic-t8a-stranger-{token}"
        d.accounts["stranger"] = str(uuid4())
        d.roles["stranger"] = "parent"

    async def verified(
        x_test_principal: str = Header(alias="X-Test-Principal"),
        x_test_issuer: str = Header(default=ISSUER, alias="X-Test-Issuer"),
    ) -> VerifiedPrincipal:
        return VerifiedPrincipal(subject=x_test_principal, issuer=x_test_issuer, roles=frozenset())

    app.dependency_overrides[get_verified_adult] = verified
    try:
        with d.client:
            yield d
    finally:
        app.dependency_overrides.clear()
        runtime.engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def shape(response: Any) -> tuple[int, dict[str, Any]]:
    """Status and envelope without the per-request ids: what a caller can compare."""
    body = dict(response.json())
    body.pop("request_id", None)
    body.pop("correlation_id", None)
    return response.status_code, body


def _ids(response: Any) -> list[str]:
    return [item["inbox_item_id"] for item in response.json()["items"]]


# ----------------------------------------------------------------------------- the database
def test_the_schema_holds_one_table_with_the_planned_indexes_and_checks(
    directory: Directory,
) -> None:
    with directory.factory()() as db:
        tables = set(
            db.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'notifications'"
                )
            ).scalars()
        )
        # DDL-C part 1 only: no push endpoint and no delivery attempt table (T-8b is deferred).
        assert tables == {"inbox_items"}
        indexes = {
            row[0]: row[1]
            for row in db.execute(
                text(
                    "SELECT indexname, indexdef FROM pg_indexes "
                    "WHERE schemaname = 'notifications' AND tablename = 'inbox_items'"
                )
            )
        }
        assert set(indexes) == {
            "inbox_items_pkey",
            "uq_notif_inbox_dedupe",
            "ix_notif_inbox_page",
            "ix_notif_inbox_unread",
        }
        assert "created_at DESC" in indexes["ix_notif_inbox_page"]
        assert "inbox_item_id DESC" in indexes["ix_notif_inbox_page"]
        assert "WHERE (read_at IS NULL)" in indexes["ix_notif_inbox_unread"]
        checks = set(
            db.execute(
                text(
                    "SELECT conname FROM pg_constraint WHERE contype = 'c' "
                    "AND connamespace = 'notifications'::regnamespace"
                )
            ).scalars()
        )
        assert checks == {
            "ck_notif_inbox_role",
            "ck_notif_inbox_type",
            "ck_notif_inbox_template",
            "ck_notif_inbox_keys",
            "ck_notif_inbox_hash",
            "ck_notif_inbox_params",
            "ck_notif_inbox_times",
        }
    engine = directory.app.state.be1_runtime.engine
    with engine.connect() as connection:
        context = MigrationContext.configure(
            connection,
            opts={
                "compare_type": True,
                "include_schemas": True,
                "include_name": lambda name, type_, _parents: (
                    type_ != "schema" or name == "notifications"
                ),
            },
        )
        assert compare_metadata(context, METADATA) == []


def _raw_row(**overrides: Any) -> dict[str, Any]:
    now = datetime.now(UTC)
    row: dict[str, Any] = {
        "inbox_item_id": str(uuid4()),
        "recipient_account_id": str(uuid4()),
        "recipient_role": "parent",
        "organization_ref": None,
        "notification_type": "CLASS_ARCHIVED",
        "template_version": 1,
        "trigger_id": "trg-1",
        "trigger_dedupe_key": f"dk-{uuid4().hex}",
        "command_sha256": "a" * 64,
        "safe_parameters": {"count": 1},
        "created_at": now - timedelta(minutes=1),
        "read_at": None,
        "expires_at": None,
    }
    row.update(overrides)
    return row


@pytest.mark.parametrize(
    ("overrides", "check"),
    [
        ({"recipient_role": "child"}, "ck_notif_inbox_role"),
        ({"recipient_role": "Parent"}, "ck_notif_inbox_role"),
        ({"notification_type": "class_archived"}, "ck_notif_inbox_type"),
        ({"notification_type": "AB"}, "ck_notif_inbox_type"),
        ({"template_version": 0}, "ck_notif_inbox_template"),
        ({"template_version": 10000}, "ck_notif_inbox_template"),
        ({"trigger_id": "has space"}, "ck_notif_inbox_keys"),
        ({"trigger_id": ""}, "ck_notif_inbox_keys"),
        ({"trigger_dedupe_key": "Nguyễn"}, "ck_notif_inbox_keys"),
        ({"trigger_dedupe_key": "a@b"}, "ck_notif_inbox_keys"),
        ({"command_sha256": "A" * 64}, "ck_notif_inbox_hash"),
        ({"command_sha256": "a" * 63}, "ck_notif_inbox_hash"),
        ({"safe_parameters": ["a"]}, "ck_notif_inbox_params"),
        ({"safe_parameters": {"k": "x" * 2100}}, "ck_notif_inbox_params"),
        (
            {"read_at": datetime.now(UTC) - timedelta(days=1)},
            "ck_notif_inbox_times",
        ),
        (
            {"expires_at": datetime.now(UTC) - timedelta(days=1)},
            "ck_notif_inbox_times",
        ),
    ],
)
def test_each_check_constraint_rejects_a_bad_row(
    directory: Directory, overrides: dict[str, Any], check: str
) -> None:
    with pytest.raises(IntegrityError) as caught, directory.factory().begin() as db:
        db.execute(INBOX_ITEMS.insert().values(**_raw_row(**overrides)))
    assert check in str(caught.value.orig)


def test_the_dedupe_constraint_is_per_recipient(directory: Directory) -> None:
    first = _raw_row(trigger_dedupe_key="same-key")
    other_recipient = _raw_row(trigger_dedupe_key="same-key")
    with directory.factory().begin() as db:
        db.execute(INBOX_ITEMS.insert().values(**first))
        db.execute(INBOX_ITEMS.insert().values(**other_recipient))  # another recipient: allowed
    clash = _raw_row(
        recipient_account_id=first["recipient_account_id"], trigger_dedupe_key="same-key"
    )
    with pytest.raises(IntegrityError) as caught, directory.factory().begin() as db:
        db.execute(INBOX_ITEMS.insert().values(**clash))
    assert "uq_notif_inbox_dedupe" in str(caught.value.orig)


def test_a_valid_row_with_every_optional_column_is_accepted(directory: Directory) -> None:
    now = datetime.now(UTC)
    row = _raw_row(
        organization_ref="org-1",
        read_at=now,
        created_at=now - timedelta(minutes=1),
        expires_at=now + timedelta(days=1),
        safe_parameters={},
    )
    with directory.factory().begin() as db:
        db.execute(INBOX_ITEMS.insert().values(**row))
    assert directory.row(row["inbox_item_id"])["organization_ref"] == "org-1"


def test_the_downgrade_guard_statement_refuses_while_a_row_exists(directory: Directory) -> None:
    spec = importlib.util.spec_from_file_location("nt_0001_migration_pg", MIGRATION)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with directory.factory().begin() as db:
        db.execute(INBOX_ITEMS.insert().values(**_raw_row()))
    with pytest.raises(DBAPIError, match="downgrade refused"), directory.factory().begin() as db:
        db.execute(text(module.DOWNGRADE_GUARD))
    with directory.factory().begin() as db:
        assert db.scalar(select(func.count()).select_from(INBOX_ITEMS)) >= 1


# ----------------------------------------------------------------------------- the producer
def test_the_producer_stores_one_row_in_the_callers_transaction(directory: Directory) -> None:
    d = directory
    moment = datetime.now(UTC) - timedelta(minutes=3)
    command = d.command("p1", organization_ref="org-9", expires_at=moment + timedelta(days=2))
    with d.factory()() as db:
        result = SqlNotificationProducer(db, Clock(moment)).enqueue(command)
        assert result.created is True
        db.rollback()  # the producer never commits: the caller's rollback removes the row
    with d.factory()() as db:
        assert (
            db.scalar(
                select(func.count()).where(INBOX_ITEMS.c.inbox_item_id == result.inbox_item_id)
            )
            == 0
        )
    stored = d.produce("p1", at=moment, expires_at=moment + timedelta(days=2))
    row = d.row(stored.inbox_item_id)
    assert row["created_at"] == moment and row["read_at"] is None
    assert row["recipient_account_id"] == d.accounts["p1"] and row["recipient_role"] == "parent"
    assert len(row["command_sha256"]) == 64 and row["safe_parameters"]["count"] >= 1


def test_a_duplicate_command_returns_the_stored_item_and_another_hash_raises(
    directory: Directory,
) -> None:
    d = directory
    command = d.command("p1", safe_parameters={"count": 7})
    first = d.produce("p1", **_fields(command))
    again = d.produce("p1", **_fields(command), expires_at=datetime.now(UTC) + timedelta(days=1))
    assert (first.created, again.created) == (True, False)
    assert again.inbox_item_id == first.inbox_item_id
    with pytest.raises(NotificationDedupeConflict):
        d.produce("p1", **_fields(replace(command, safe_parameters={"count": 8})))
    with d.factory()() as db:
        count = db.scalar(
            select(func.count()).where(
                INBOX_ITEMS.c.recipient_account_id == d.accounts["p1"],
                INBOX_ITEMS.c.trigger_dedupe_key == command.dedupe_key,
            )
        )
    assert count == 1
    # The same dedupe key for another recipient is its own notification.
    other = d.produce("p2", **{**_fields(command), "recipient_account_id": d.accounts["p2"]})
    assert other.created is True and other.inbox_item_id != first.inbox_item_id


def _fields(command: NotificationCommandV1) -> dict[str, Any]:
    return {
        "notification_type": command.notification_type,
        "template_version": command.template_version,
        "trigger_id": command.trigger_id,
        "dedupe_key": command.dedupe_key,
        "safe_parameters": dict(command.safe_parameters),
    }


def test_two_concurrent_producers_of_one_command_make_one_row(directory: Directory) -> None:
    d = directory
    command = d.command("p1", safe_parameters={"count": 99})
    barrier = Barrier(2)

    def work(_index: int) -> EnqueueResult:
        barrier.wait()
        with d.factory().begin() as db:
            return SqlNotificationProducer(db, Clock(datetime.now(UTC))).enqueue(command)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(work, range(2)))
    assert sorted(result.created for result in results) == [False, True]
    assert len({result.inbox_item_id for result in results}) == 1


def test_two_concurrent_producers_with_clashing_commands_make_one_row_and_one_error(
    directory: Directory,
) -> None:
    d = directory
    first = d.command("p1", safe_parameters={"count": 1})
    second = replace(first, safe_parameters={"count": 2})
    barrier = Barrier(2)

    def work(command: NotificationCommandV1) -> str:
        barrier.wait()
        try:
            with d.factory().begin() as db:
                SqlNotificationProducer(db, Clock(datetime.now(UTC))).enqueue(command)
        except NotificationDedupeConflict:
            return "conflict"
        return "stored"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = sorted(pool.map(work, (first, second)))
    assert outcomes == ["conflict", "stored"]


def test_a_rejected_command_writes_no_row(directory: Directory) -> None:
    d = directory
    before = _count(d)
    for bad in (
        d.command("p1", safe_parameters={"label": "Nguyen Be Lan"}),
        d.command("p1", safe_parameters={"child_name": "x"}),
        d.command("p1", safe_parameters={"link": "https://x.example/a"}),
        d.command("p1", recipient_role="child"),
    ):
        with pytest.raises(NotificationRejected), d.factory().begin() as db:
            SqlNotificationProducer(db, Clock(datetime.now(UTC))).enqueue(bad)
    now = datetime.now(UTC)
    with pytest.raises(NotificationRejected), d.factory().begin() as db:
        SqlNotificationProducer(db, Clock(now)).enqueue(d.command("p1", expires_at=now))
    assert _count(d) == before


def _count(d: Directory) -> int:
    with d.factory()() as db:
        return int(db.scalar(select(func.count()).select_from(INBOX_ITEMS)) or 0)


# ----------------------------------------------------------------------------- reads
def test_each_of_the_four_roles_reads_only_its_own_inbox(directory: Directory) -> None:
    d = directory
    own = {who: d.produce(who) for who in ("p1", "p2", "t1", "m1", "a1")}
    for who, produced in own.items():
        response = d.list_page(who)
        assert response.status_code == 200, who
        assert _ids(response) == [produced.inbox_item_id], who
        assert response.json()["unread_count"] == 1
        assert response.headers["Cache-Control"] == "private, no-cache"
        assert response.headers["Vary"] == "Authorization"
    assert {d.roles[who] for who in own} == set(ROLES)


def test_the_body_holds_no_recipient_trigger_hash_or_child_content(directory: Directory) -> None:
    d = directory
    produced = d.produce(
        "p1", organization_ref="org-1", safe_parameters={"count": 2, "week": "2026-W47"}
    )
    body = d.list_page("p1").json()
    item = body["items"][0]
    assert set(item) == {
        "contract",
        "inbox_item_id",
        "notification_type",
        "template_version",
        "safe_parameters",
        "created_at",
        "read_at",
        "expires_at",
    }
    assert item["inbox_item_id"] == produced.inbox_item_id
    assert item["safe_parameters"] == {"count": 2, "week": "2026-W47"}
    text_body = json.dumps(body)
    row = d.row(produced.inbox_item_id)
    for hidden in (
        d.accounts["p1"],
        row["trigger_id"],
        row["trigger_dedupe_key"],
        row["command_sha256"],
        "org-1",
    ):
        assert hidden not in text_body


def test_identity_guards_are_one_uniform_404(directory: Directory) -> None:
    d = directory
    d.produce("p1")
    unknown = shape(d.client.get("/v1/notifications", headers={"X-Test-Principal": "nobody"}))
    assert unknown[0] == 404 and unknown[1]["code"] == "RESOURCE_NOT_FOUND"
    # No identity row, an inactive identity, another issuer and no role: the same answer.
    for who in ("stranger", "inactive", "norole"):
        assert shape(d.list_page(who)) == unknown, who
    foreign = d.client.get(
        "/v1/notifications",
        headers={"X-Test-Principal": d.subjects["foreign"], "X-Test-Issuer": ISSUER},
    )
    assert shape(foreign) == unknown
    mismatch = d.client.get(
        "/v1/notifications",
        headers={"X-Test-Principal": d.subjects["p1"], "X-Test-Issuer": "someone-else"},
    )
    assert shape(mismatch) == unknown
    # The writes answer the same way and write nothing.
    before = len(d.receipts("stranger"))
    assert shape(d.read("stranger", str(uuid4()))) == unknown
    assert shape(d.read_all("stranger")) == unknown
    assert len(d.receipts("stranger")) == before == 0


def test_paging_is_25_by_default_100_at_most_and_101_is_400(directory: Directory) -> None:
    d = directory
    base = datetime.now(UTC) - timedelta(hours=2)
    produced = [d.produce("p1", at=base + timedelta(seconds=index)) for index in range(60)]
    newest_first = [item.inbox_item_id for item in reversed(produced)]
    first = d.list_page("p1")
    assert first.status_code == 200 and len(first.json()["items"]) == 25
    assert _ids(first) == newest_first[:25]
    second = d.list_page("p1", f"cursor={first.json()['next_cursor']}")
    assert _ids(second) == newest_first[25:50]
    third = d.list_page("p1", f"cursor={second.json()['next_cursor']}")
    assert _ids(third) == newest_first[50:] and third.json()["next_cursor"] is None
    assert len(d.list_page("p1", "limit=100").json()["items"]) == 60
    assert len(d.list_page("p1", "limit=7").json()["items"]) == 7
    assert d.list_page("p1", "limit=101").status_code == 400
    assert d.list_page("p1", "limit=0").status_code == 400
    assert d.list_page("p1", "cursor=garbage").status_code == 400


def test_paging_has_no_duplicate_or_gap_under_concurrent_inserts(directory: Directory) -> None:
    d = directory
    base = datetime.now(UTC) - timedelta(hours=2)
    tie = base + timedelta(minutes=30)
    # 30 items share one timestamp (the id breaks the tie) and 30 more are spread over time.
    produced = [d.produce("p1", at=base + timedelta(seconds=index)) for index in range(30)]
    produced += [d.produce("p1", at=tie) for _ in range(30)]
    original = {item.inbox_item_id for item in produced}
    seen: list[str] = []
    page = d.list_page("p1")
    seen += _ids(page)
    # Between pages: newer items arrive, and an older one lands late (a long producer transaction).
    newer = [d.produce("p1", at=datetime.now(UTC) - timedelta(seconds=index)) for index in range(5)]
    late = d.produce("p1", at=base - timedelta(hours=1))
    while page.json()["next_cursor"] is not None:
        page = d.list_page("p1", f"cursor={page.json()['next_cursor']}")
        seen += _ids(page)
    assert len(seen) == len(set(seen)), "a duplicate across pages"
    assert original <= set(seen), "a gap: an item present before the first page was skipped"
    # The newer items stay out of the pages already behind the cursor and show on a fresh read.
    assert not {item.inbox_item_id for item in newer} & set(seen)
    assert late.inbox_item_id in seen
    fresh = _ids(d.list_page("p1", "limit=100"))
    assert {item.inbox_item_id for item in newer} <= set(fresh)
    by_time = sorted(newer, key=lambda item: d.row(item.inbox_item_id)["created_at"], reverse=True)
    assert fresh[:5] == [item.inbox_item_id for item in by_time]


def test_a_cursor_of_one_user_never_shows_another_users_items(directory: Directory) -> None:
    d = directory
    base = datetime.now(UTC) - timedelta(hours=1)
    mine = [d.produce("p1", at=base + timedelta(seconds=i)).inbox_item_id for i in range(30)]
    theirs = [d.produce("p2", at=base + timedelta(seconds=i)).inbox_item_id for i in range(30)]
    cursor = d.list_page("p1").json()["next_cursor"]
    leaked = d.list_page("p2", f"cursor={cursor}")
    assert leaked.status_code == 200
    assert set(_ids(leaked)) <= set(theirs) and not set(_ids(leaked)) & set(mine)


def test_the_unread_badge_is_exact_up_to_99_and_capped_at_100(directory: Directory) -> None:
    d = directory
    base = datetime.now(UTC) - timedelta(hours=3)
    for index in range(3):
        d.produce("p1", at=base + timedelta(seconds=index))
    assert d.list_page("p1").json()["unread_count"] == 3
    for index in range(3, 105):
        d.produce("p1", at=base + timedelta(seconds=index))
    page = d.list_page("p1", "limit=1").json()
    assert page["unread_count"] == 100 and len(page["items"]) == 1
    assert d.read_all("p1").json()["marked_count"] == 105
    assert d.list_page("p1").json()["unread_count"] == 0


def test_an_expired_item_is_hidden_and_cannot_be_marked(directory: Directory) -> None:
    d = directory
    past = datetime.now(UTC) - timedelta(hours=2)
    expired = d.produce("p1", at=past, expires_at=past + timedelta(hours=1))
    live = d.produce("p1", at=past, expires_at=datetime.now(UTC) + timedelta(hours=1))
    page = d.list_page("p1")
    assert _ids(page) == [live.inbox_item_id] and page.json()["unread_count"] == 1
    response = d.read("p1", expired.inbox_item_id)
    assert response.status_code == 404 and response.json()["code"] == "RESOURCE_NOT_FOUND"
    assert d.row(expired.inbox_item_id)["read_at"] is None
    assert d.read_all("p1").json()["marked_count"] == 1
    assert d.row(expired.inbox_item_id)["read_at"] is None


# ----------------------------------------------------------------------------- mark read
def test_another_users_item_and_an_unknown_item_are_the_same_404(directory: Directory) -> None:
    d = directory
    theirs = d.produce("p2")
    foreign = d.read("p1", theirs.inbox_item_id)
    unknown = d.read("p1", str(uuid4()))
    too_long = d.read("p1", "x" * 40)
    assert foreign.status_code == 404
    assert shape(foreign) == shape(unknown) == shape(too_long)
    assert d.row(theirs.inbox_item_id)["read_at"] is None
    assert d.receipts("p1", READ_ONE_SCOPE) == []  # receipts are success-only
    # The owner's own list still shows the item unread.
    assert d.list_page("p2").json()["items"][0]["read_at"] is None


def test_mark_read_sets_read_at_once_and_keeps_the_first(directory: Directory) -> None:
    d = directory
    item = d.produce("p1")
    first = d.read("p1", item.inbox_item_id)
    assert first.status_code == 200 and first.json()["contract"] == "NotificationV1"
    first_read_at = first.json()["read_at"]
    assert first_read_at is not None
    second = d.read("p1", item.inbox_item_id)  # another key
    assert second.status_code == 200 and second.json()["read_at"] == first_read_at
    stored = d.row(item.inbox_item_id)
    assert stored["read_at"] >= stored["created_at"]
    assert d.list_page("p1").json()["unread_count"] == 0
    assert d.list_page("p1").json()["items"][0]["read_at"] == first_read_at


def test_an_item_created_in_the_future_is_read_at_its_creation_time(directory: Directory) -> None:
    d = directory
    future = datetime.now(UTC) + timedelta(hours=1)
    item = d.produce("p1", at=future)
    response = d.read("p1", item.inbox_item_id)
    assert response.status_code == 200  # read_at = max(now, created_at) satisfies the CHECK
    row = d.row(item.inbox_item_id)
    assert row["read_at"] == row["created_at"] == future


def test_the_same_key_replays_the_first_answer_with_one_receipt(directory: Directory) -> None:
    d = directory
    item = d.produce("p1")
    first = d.read("p1", item.inbox_item_id, key="key-replay")
    again = d.read("p1", item.inbox_item_id, key="key-replay")
    assert first.status_code == again.status_code == 200
    assert first.json() == again.json()
    receipts = d.receipts("p1", READ_ONE_SCOPE)
    assert len(receipts) == 1
    (receipt,) = receipts
    assert receipt.principal_ref == d.subjects["p1"] and receipt.idempotency_key == "key-replay"
    assert receipt.organization_id is None and len(receipt.request_fingerprint) == 64
    assert item.inbox_item_id not in receipt.operation_scope  # a constant scope
    stored = json.dumps(receipt.response_json)
    assert d.accounts["p1"] not in stored and "recipient" not in stored


def test_the_same_key_on_another_item_is_400_invalid_idempotency_key(directory: Directory) -> None:
    d = directory
    first_item, second_item = d.produce("p1"), d.produce("p1")
    assert d.read("p1", first_item.inbox_item_id, key="shared").status_code == 200
    refused = d.read("p1", second_item.inbox_item_id, key="shared")
    assert refused.status_code == 400 and refused.json()["code"] == "INVALID_IDEMPOTENCY_KEY"
    assert d.row(second_item.inbox_item_id)["read_at"] is None
    assert len(d.receipts("p1", READ_ONE_SCOPE)) == 1


def test_a_key_is_scoped_to_the_principal_and_the_operation(directory: Directory) -> None:
    d = directory
    mine, theirs = d.produce("p1"), d.produce("p2")
    assert d.read("p1", mine.inbox_item_id, key="same").status_code == 200
    assert d.read("p2", theirs.inbox_item_id, key="same").status_code == 200  # another principal
    assert d.read_all("p1", key="same").status_code == 200  # another operation
    assert len(d.receipts("p1")) == 2


def test_read_all_replay_keeps_the_original_count_and_leaves_new_items_unread(
    directory: Directory,
) -> None:
    d = directory
    base = datetime.now(UTC) - timedelta(hours=1)
    for index in range(4):
        d.produce("p1", at=base + timedelta(seconds=index))
    first = d.read_all("p1", key="all-1")
    assert first.status_code == 200
    assert first.json() == {"contract": "NotificationReadAllV1", "marked_count": 4}
    arrived = d.produce("p1")
    replay = d.read_all("p1", key="all-1")
    assert replay.status_code == 200 and replay.json() == first.json()
    assert d.row(arrived.inbox_item_id)["read_at"] is None
    assert d.list_page("p1").json()["unread_count"] == 1
    # A new key marks the new arrival.
    assert d.read_all("p1", key="all-2").json()["marked_count"] == 1
    assert d.read_all("p1", key="all-3").json()["marked_count"] == 0
    assert len(d.receipts("p1", READ_ALL_SCOPE)) == 3


def test_read_all_touches_only_the_callers_items(directory: Directory) -> None:
    d = directory
    mine, theirs = d.produce("p1"), d.produce("p2")
    assert d.read_all("p1").json()["marked_count"] == 1
    assert d.row(mine.inbox_item_id)["read_at"] is not None
    assert d.row(theirs.inbox_item_id)["read_at"] is None


def test_concurrent_requests_with_the_same_key_make_one_receipt(directory: Directory) -> None:
    d = directory
    item = d.produce("p1")
    barrier = Barrier(2)

    def work(_index: int) -> Any:
        barrier.wait()
        return d.read("p1", item.inbox_item_id, key="race")

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(work, range(2)))
    assert [response.status_code for response in responses] == [200, 200]
    assert responses[0].json() == responses[1].json()
    assert len(d.receipts("p1", READ_ONE_SCOPE)) == 1


def test_concurrent_read_all_with_the_same_key_make_one_receipt(directory: Directory) -> None:
    d = directory
    for _ in range(3):
        d.produce("p1")
    barrier = Barrier(2)

    def work(_index: int) -> Any:
        barrier.wait()
        return d.read_all("p1", key="race-all")

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(work, range(2)))
    assert [response.status_code for response in responses] == [200, 200]
    assert (
        responses[0].json()
        == responses[1].json()
        == {
            "contract": "NotificationReadAllV1",
            "marked_count": 3,
        }
    )
    assert len(d.receipts("p1", READ_ALL_SCOPE)) == 1


def test_missing_and_malformed_keys_are_400_and_write_nothing(directory: Directory) -> None:
    d = directory
    item = d.produce("p1")
    missing = d.client.post(f"/v1/notifications/{item.inbox_item_id}/read", headers=d.header("p1"))
    assert missing.status_code == 400
    assert {"field": "Idempotency-Key", "code": "REQUIRED"} in missing.json()["field_errors"]
    for bad in ("has space", "x" * 129):
        response = d.client.post(
            "/v1/notifications/read-all", headers=d.header("p1", **{"Idempotency-Key": bad})
        )
        assert response.status_code == 400
    assert d.row(item.inbox_item_id)["read_at"] is None
    assert d.receipts("p1") == []


def test_no_inbox_row_or_response_holds_an_e_mail_a_url_or_a_name(directory: Directory) -> None:
    d = directory
    for who in ("p1", "t1", "m1", "a1"):
        d.produce(who, safe_parameters={"count": 1, "week": "2026-W47", "urgent": True})
    for who in ("p1", "t1", "m1", "a1"):
        assert "@" not in d.list_page(who).text and "://" not in d.list_page(who).text
    with d.factory()() as db:
        rows = db.execute(select(INBOX_ITEMS)).mappings().all()
    assert rows
    for row in rows:
        blob = json.dumps({key: str(value) for key, value in row.items()})
        assert "@" not in blob and "://" not in blob, row["inbox_item_id"]
    assert not {"email", "display_name", "endpoint", "token", "url"} & {
        column.name for column in INBOX_ITEMS.columns
    }


def test_no_push_endpoint_route_exists_on_the_live_app(directory: Directory) -> None:
    d = directory
    for method, path in (
        ("post", "/v1/notifications/push-endpoints"),
        ("get", "/v1/notifications/push-endpoints"),
    ):
        response = d.client.request(
            method, path, headers=d.header("p1", **{"Idempotency-Key": "k"})
        )
        assert response.status_code in {404, 405}, (method, path)


def test_a_failed_producer_transaction_leaves_the_inbox_unchanged(directory: Directory) -> None:
    d = directory
    before = len(_ids(d.list_page("p1", "limit=100")))
    with pytest.raises(RuntimeError), d.factory().begin() as db:
        SqlNotificationProducer(db, Clock(datetime.now(UTC))).enqueue(d.command("p1"))
        raise RuntimeError("the caller's transaction fails after the enqueue")
    assert len(_ids(d.list_page("p1", "limit=100"))) == before


def test_the_recipient_ids_in_the_database_are_account_ids_never_subjects(
    directory: Directory,
) -> None:
    d = directory
    produced = d.produce("p1")
    row = d.row(produced.inbox_item_id)
    with d.factory()() as db:
        accounts = set(db.scalars(select(AdultIdentityModel.account_id)))
        subjects = set(db.scalars(select(AdultIdentityModel.subject)))
    assert row["recipient_account_id"] == d.accounts["p1"]
    assert row["recipient_account_id"] in accounts
    assert row["recipient_account_id"] not in subjects
    assert d.subjects["p1"] not in json.dumps({k: str(v) for k, v in row.items()})
