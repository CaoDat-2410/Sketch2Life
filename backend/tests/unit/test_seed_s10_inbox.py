"""Pure and fake-service checks for the S10 notification seed."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal
from uuid import NAMESPACE_URL, uuid5

import pytest

from sketch2life.application.ports.notifications import (
    EnqueueResult,
    NotificationCommandV1,
)
from sketch2life.application.services.notifications import validate_command
from tools.seed import data
from tools.seed.guard import SeedGuardError
from tools.seed.s10_inbox import (
    FixedClock,
    _command,
    _dedupe_key,
    _read_key,
    count_stage_rows,
    seed_inbox,
)
from tools.seed.s10_inbox_data import EXPECTED, ITEMS, REF
from tools.seed.stage_common import check_database_prefix, seed_principal


@dataclass
class _SessionContext:
    session: object

    def __enter__(self) -> object:
        return self.session

    def __exit__(self, *_exc: object) -> Literal[False]:
        return False


def _fake_resolver(_factory: object, spec: Any) -> dict[str, str | int | bool]:
    return {
        key: data.seed_uuid_text(f"test:{value}")
        if isinstance(value, str) and value.startswith(REF)
        else value
        for key, value in spec.safe_parameters.items()
    }


class _SessionFactory:
    def __init__(self) -> None:
        self.session = object()

    def begin(self) -> _SessionContext:
        return _SessionContext(self.session)

    def __call__(self) -> _SessionContext:
        return _SessionContext(self.session)


class _FakeProducer:
    rows: dict[str, tuple[str, NotificationCommandV1]] = {}
    created_count = 0

    def __init__(self, _session: object, clock: FixedClock) -> None:
        self.clock = clock

    def enqueue(self, command: NotificationCommandV1) -> EnqueueResult:
        assert self.clock() == next(
            item.created_at for item in ITEMS if _dedupe_key(item) == command.dedupe_key
        )
        previous = self.rows.get(command.dedupe_key)
        if previous is not None:
            assert previous[1] == command
            return EnqueueResult(inbox_item_id=previous[0], created=False)
        item_id = str(uuid5(NAMESPACE_URL, command.dedupe_key))
        self.rows[command.dedupe_key] = (item_id, command)
        type(self).created_count += 1
        return EnqueueResult(inbox_item_id=item_id, created=True)


class _FakeInbox:
    receipts: dict[tuple[str, str], dict[str, Any]] = {}
    read_at: dict[str, datetime] = {}
    calls = 0

    def __init__(self, _session: object, clock: FixedClock) -> None:
        self.clock = clock

    def mark_read(
        self, *, principal: Any, inbox_item_id: str, idempotency_key: str
    ) -> dict[str, Any]:
        type(self).calls += 1
        receipt_key = (principal.subject, idempotency_key)
        previous = self.receipts.get(receipt_key)
        if previous is not None:
            assert previous["inbox_item_id"] == inbox_item_id
            return previous
        spec = next(spec for spec in ITEMS if _read_key(spec) == idempotency_key)
        assert _dedupe_key(spec) in _FakeProducer.rows
        assert self.clock() > spec.created_at
        assert spec.expires_at is None or self.clock() < spec.expires_at
        read_at = self.clock()
        self.read_at.setdefault(inbox_item_id, read_at)
        body = {"inbox_item_id": inbox_item_id, "read_at": self.read_at[inbox_item_id]}
        self.receipts[receipt_key] = body
        return body


def _reset_fakes() -> None:
    _FakeProducer.rows = {}
    _FakeProducer.created_count = 0
    _FakeInbox.receipts = {}
    _FakeInbox.read_at = {}
    _FakeInbox.calls = 0


def test_specs_have_the_required_recipients_read_counts_and_allowlisted_commands() -> None:
    assert len(ITEMS) == EXPECTED["notifications_inbox_items"] == 15
    by_subject: dict[str, list[Any]] = {}
    for spec in ITEMS:
        by_subject.setdefault(spec.recipient_subject, []).append(spec)
        command = _command(spec, _fake_resolver(None, spec))
        assert command.recipient_account_id == data.seed_uuid_text(
            f"adult:{spec.recipient_subject}"
        )
        assert command.recipient_role == spec.recipient_role
        validate_command(command, created_at=spec.created_at)
        assert all(
            isinstance(value, (str, int, bool)) for value in command.safe_parameters.values()
        )
    assert [(len(rows), sum(row.read for row in rows)) for rows in by_subject.values()] == [
        (2, 1),
        (2, 1),
        (1, 0),
        (2, 0),
        (4, 1),
        (4, 2),
    ]
    assert all(item.organization_ref is None for item in ITEMS[:7])
    assert all(item.organization_ref == data.org_id("a") for item in ITEMS[7:])


def test_safe_parameters_have_no_display_text_or_child_content() -> None:
    for spec in ITEMS:
        for key, value in spec.safe_parameters.items():
            assert "child" not in key and "story" not in key and "name" not in key
            if isinstance(value, str):
                assert " " not in value and "@" not in value and "://" not in value


def test_seed_inbox_replay_adds_no_rows_and_keeps_read_receipts_once() -> None:
    _reset_fakes()
    factory = _SessionFactory()
    seed_inbox(
        factory,
        producer_factory=_FakeProducer,  # type: ignore[arg-type]
        inbox_factory=_FakeInbox,  # type: ignore[arg-type]
        resolver=_fake_resolver,
    )
    first_reads = dict(_FakeInbox.read_at)
    assert _FakeProducer.created_count == 15
    assert len(_FakeInbox.receipts) == EXPECTED["be1_command_receipts_s10"] == 5
    assert len(first_reads) == 5

    seed_inbox(
        factory,
        producer_factory=_FakeProducer,  # type: ignore[arg-type]
        inbox_factory=_FakeInbox,  # type: ignore[arg-type]
        resolver=_fake_resolver,
    )
    assert _FakeProducer.created_count == 15
    assert len(_FakeInbox.receipts) == 5
    assert _FakeInbox.read_at == first_reads
    assert _FakeInbox.calls == 10


def test_fixed_clock_is_repeatable() -> None:
    clock = FixedClock(ITEMS[0].created_at)
    assert clock() == ITEMS[0].created_at
    assert clock() == ITEMS[0].created_at


def test_s10_read_commands_use_the_recipient_principal() -> None:
    for spec in ITEMS:
        if spec.read:
            principal = seed_principal(spec.recipient_subject)
            assert principal.subject == spec.recipient_subject


@pytest.mark.parametrize(
    ("database", "refused"),
    [("seed_s10_fixture", True), ("frc08_seed_s10_fixture", False)],
)
def test_s10_guard_requires_the_frc08_database_prefix(database: str, refused: bool) -> None:
    environ = {
        "S2L_SEED_DATABASE_URL": (f"postgresql+psycopg://fixture:fixture@127.0.0.1:5435/{database}")
    }
    if refused:
        with pytest.raises(SeedGuardError):
            check_database_prefix(environ)
    else:
        check_database_prefix(environ)


def test_count_query_returns_only_s10_owned_totals() -> None:
    class Result:
        def __init__(self, value: int) -> None:
            self.value = value

        def scalar_one(self) -> int:
            return self.value

    class Connection:
        def __init__(self) -> None:
            self.queries: list[str] = []

        def execute(self, statement: Any) -> Result:
            self.queries.append(str(statement))
            return Result(15 if len(self.queries) == 1 else 5)

    connection = Connection()
    assert count_stage_rows(connection) == EXPECTED  # type: ignore[arg-type]
    assert len(connection.queries) == 2
    assert all(
        "notifications.inbox_items" in query or "be1_command_receipts" in query
        for query in connection.queries
    )
