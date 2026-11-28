"""FEAT-066 T-8a: notification rules, producer, serializer and migration text (no database).

The behaviour against PostgreSQL (CHECKs, dedupe, paging, recipient scope, receipts) is in
``tests/integration/test_t8a_notifications_postgres.py``. This module pins the allowlist of the
producer, the canonical hash and fingerprints, the producer's use of the session, what an item
body hides, and the text of migration ``20261120_nt_0001`` and its place in the revision graph.
"""

from __future__ import annotations

import ast
import importlib.util
import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import pytest
from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.dialects import postgresql

from sketch2life.application.ports.notifications import (
    NotificationCommandV1,
    NotificationDedupeConflict,
    NotificationRejected,
)
from sketch2life.application.services.notifications import (
    MAX_PARAMETERS,
    READ_ALL_SCOPE,
    READ_ONE_SCOPE,
    command_sha256,
    pg_text_size,
    read_fingerprint,
    utc_iso,
    validate_command,
    validate_parameters,
)
from sketch2life.infrastructure.notifications.inbox_repository import (
    SqlNotificationProducer,
    item_body,
)
from sketch2life.infrastructure.notifications.tables import INBOX_ITEMS
from sketch2life.interfaces.http.api_conventions import decode_time_cursor, encode_cursor

NOW = datetime(2026, 11, 21, 7, 0, tzinfo=UTC)
ACCOUNT = "11111111-1111-4111-8111-111111111111"
_VERSIONS = Path(__file__).resolve().parents[2] / "alembic" / "versions"
_MIGRATION = _VERSIONS / "20261120_nt_0001_notifications_inbox.py"


def command(**overrides: Any) -> NotificationCommandV1:
    base = NotificationCommandV1(
        recipient_account_id=ACCOUNT,
        recipient_role="parent",
        notification_type="CLASS_ARCHIVED",
        template_version=1,
        trigger_id="trg:class.archived:1",
        dedupe_key="class.archived:1:parent",
        safe_parameters={"class_ref": "cls_1", "count": 3, "urgent": False},
    )
    return replace(base, **overrides)


# ------------------------------------------------------------------ the allowlist (T8A-02)
@pytest.mark.parametrize(
    "parameters",
    [
        {},
        {"count": 0},
        {"count": -5, "flag": True},
        {"class_ref": "cls_1", "week": "2026-W47"},
        {"code": "A.b:c-d_9"},
        {f"k{index}": index for index in range(MAX_PARAMETERS)},
    ],
)
def test_the_allowlist_accepts_codes_counts_and_opaque_refs(parameters: dict[str, Any]) -> None:
    assert validate_parameters(parameters) == parameters


@pytest.mark.parametrize(
    ("parameters", "field", "code"),
    [
        # A Vietnamese display name, spaced values, diacritics, a sentence, a URL, an e-mail.
        ({"label": "Nguyen Be Lan"}, "safe_parameters.label", "INVALID_FORMAT"),
        ({"label": "Nguyễn_Bé_Lan"}, "safe_parameters.label", "INVALID_FORMAT"),
        ({"label": "Bé Lan"}, "safe_parameters.label", "INVALID_FORMAT"),
        ({"label": "Be Lan drew a cat today."}, "safe_parameters.label", "INVALID_FORMAT"),
        ({"label": "https://x.example/v/1"}, "safe_parameters.label", "INVALID_FORMAT"),
        ({"label": "parent@example.com"}, "safe_parameters.label", "INVALID_FORMAT"),
        ({"label": ""}, "safe_parameters.label", "INVALID_FORMAT"),
        ({"label": "x" * 65}, "safe_parameters.label", "INVALID_FORMAT"),
        # Types: no float, none, list or nested object.
        ({"ratio": 0.5}, "safe_parameters.ratio", "INVALID_TYPE"),
        ({"value": None}, "safe_parameters.value", "INVALID_TYPE"),
        ({"items": ["a"]}, "safe_parameters.items", "INVALID_TYPE"),
        ({"nested": {"a": 1}}, "safe_parameters.nested", "INVALID_TYPE"),
        ({"big": 2**53}, "safe_parameters.big", "OUT_OF_RANGE"),
        ({"small": -(2**53)}, "safe_parameters.small", "OUT_OF_RANGE"),
        # Key shape and the denylist kept as defence in depth.
        ({"Label": "x"}, "safe_parameters", "INVALID_FORMAT"),
        ({"1label": "x"}, "safe_parameters", "INVALID_FORMAT"),
        ({"a" * 33: "x"}, "safe_parameters", "INVALID_FORMAT"),
        ({"child_name": "x"}, "safe_parameters.child_name", "NOT_SUPPORTED"),
        ({"story_ref": "x"}, "safe_parameters.story_ref", "NOT_SUPPORTED"),
        ({"playback_url": "x"}, "safe_parameters.playback_url", "NOT_SUPPORTED"),
        ({"contact_email": "x"}, "safe_parameters.contact_email", "NOT_SUPPORTED"),
        ({"push_token": "x"}, "safe_parameters.push_token", "NOT_SUPPORTED"),
        ({"endpoint_ref": "x"}, "safe_parameters.endpoint_ref", "NOT_SUPPORTED"),
        ({"media_ref": "x"}, "safe_parameters.media_ref", "NOT_SUPPORTED"),
        ({"transcript_id": "x"}, "safe_parameters.transcript_id", "NOT_SUPPORTED"),
        ({"home_address": "x"}, "safe_parameters.home_address", "NOT_SUPPORTED"),
        # Count.
        ({f"k{index}": 1 for index in range(MAX_PARAMETERS + 1)}, "safe_parameters", "TOO_LONG"),
    ],
)
def test_the_allowlist_refuses_names_sentences_urls_and_forbidden_keys(
    parameters: dict[str, Any], field: str, code: str
) -> None:
    with pytest.raises(NotificationRejected) as caught:
        validate_parameters(parameters)
    assert (caught.value.field, caught.value.code) == (field, code)


def test_a_non_object_or_non_string_key_is_refused() -> None:
    for value in ("text", ["a"], 3, None):
        with pytest.raises(NotificationRejected):
            validate_parameters(value)
    with pytest.raises(NotificationRejected):
        validate_parameters({1: "x"})


def test_the_largest_valid_parameters_stay_below_the_database_check() -> None:
    largest: dict[str, str | int | bool] = {
        f"{'k' * 31}{index}": "v" * 64 for index in range(MAX_PARAMETERS)
    }
    assert validate_parameters(largest) == largest
    # The producer cap is below the CHECK (2,048) and measured in the PostgreSQL text form.
    assert pg_text_size(largest) < 1536 < 2048
    assert pg_text_size({"a": "x", "b": 1}) == len('{"a": "x", "b": 1}')


def test_the_bool_stays_a_bool_and_an_int_stays_an_int() -> None:
    checked = validate_parameters({"flag": True, "count": 1})
    assert checked["flag"] is True and type(checked["count"]) is int


# ------------------------------------------------------------------ the command (D6)
def test_a_valid_command_passes() -> None:
    validate_command(command(), created_at=NOW)
    validate_command(
        command(
            organization_ref="org-1",
            expires_at=NOW + timedelta(days=1),
            recipient_role="platform_admin",
        ),
        created_at=NOW,
    )


@pytest.mark.parametrize(
    ("overrides", "field"),
    [
        ({"recipient_account_id": ""}, "recipient_account_id"),
        ({"recipient_account_id": "a b"}, "recipient_account_id"),
        ({"recipient_account_id": "x" * 37}, "recipient_account_id"),
        ({"recipient_role": "child"}, "recipient_role"),
        ({"recipient_role": "Parent"}, "recipient_role"),
        ({"notification_type": "class_archived"}, "notification_type"),
        ({"notification_type": "AB"}, "notification_type"),
        ({"notification_type": "A" * 65}, "notification_type"),
        ({"template_version": 0}, "template_version"),
        ({"template_version": 10000}, "template_version"),
        ({"template_version": True}, "template_version"),
        ({"trigger_id": ""}, "trigger_id"),
        ({"trigger_id": "has space"}, "trigger_id"),
        ({"trigger_id": "x" * 129}, "trigger_id"),
        ({"trigger_id": "run/1"}, "trigger_id"),
        ({"dedupe_key": "Nguyễn"}, "dedupe_key"),
        ({"dedupe_key": "a@b"}, "dedupe_key"),
        ({"organization_ref": "has space"}, "organization_ref"),
        ({"expires_at": NOW}, "expires_at"),
        ({"expires_at": NOW - timedelta(seconds=1)}, "expires_at"),
        ({"expires_at": datetime(2026, 12, 1)}, "expires_at"),  # naive
    ],
)
def test_a_command_with_a_bad_part_is_refused(overrides: dict[str, Any], field: str) -> None:
    with pytest.raises(NotificationRejected) as caught:
        validate_command(command(**overrides), created_at=NOW)
    assert caught.value.field == field


def test_the_command_hash_is_canonical_and_ignores_the_expiry() -> None:
    first = command(safe_parameters={"a": 1, "b": "x"})
    reordered = command(safe_parameters={"b": "x", "a": 1})
    assert command_sha256(first) == command_sha256(reordered)
    assert len(command_sha256(first)) == 64
    assert command_sha256(first) == command_sha256(replace(first, expires_at=NOW))
    for changed in (
        command(safe_parameters={"a": 2, "b": "x"}),
        command(trigger_id="trg:other"),
        command(dedupe_key="other"),
        command(recipient_role="teacher"),
        command(template_version=2),
        command(notification_type="CLASS_SUSPENDED"),
        command(organization_ref="org-1"),
        command(recipient_account_id="22222222-2222-4222-8222-222222222222"),
    ):
        assert command_sha256(changed) != command_sha256(first)
    # int 1 and bool True are different values.
    assert command_sha256(command(safe_parameters={"a": 1})) != command_sha256(
        command(safe_parameters={"a": True})
    )


def test_the_read_fingerprints_hold_the_item_but_the_scopes_are_constants() -> None:
    one = read_fingerprint("read", "item-1")
    other = read_fingerprint("read", "item-2")
    all_items = read_fingerprint("read-all", None)
    assert len({one, other, all_items}) == 3
    assert read_fingerprint("read", "item-1") == one
    assert all(len(value) == 64 for value in (one, other, all_items))
    # The item id is inside the fingerprint, never in the scope string (the same key on another
    # item is a different request).
    assert READ_ONE_SCOPE == "POST /notifications/read"
    assert READ_ALL_SCOPE == "POST /notifications/read-all"
    assert "item" not in READ_ONE_SCOPE and "{" not in READ_ONE_SCOPE


# ------------------------------------------------------------------ the producer on a fake session
class _Result:
    def __init__(self, scalar: Any = None, mapping: dict[str, Any] | None = None) -> None:
        self._scalar = scalar
        self._mapping = mapping

    def scalar_one_or_none(self) -> Any:
        return self._scalar

    def mappings(self) -> _Result:
        return self

    def one(self) -> dict[str, Any]:
        assert self._mapping is not None
        return self._mapping


class _FakeSession:
    def __init__(self, *results: _Result) -> None:
        self.results = list(results)
        self.statements: list[Any] = []
        self.commits = 0

    def execute(self, statement: Any) -> _Result:
        self.statements.append(statement)
        return self.results.pop(0)

    def commit(self) -> None:  # pragma: no cover - the producer must never call this
        self.commits += 1


def _producer(session: _FakeSession) -> SqlNotificationProducer:
    return SqlNotificationProducer(cast(Any, session), clock=lambda: NOW)


def test_the_producer_inserts_with_its_own_clock_and_never_commits() -> None:
    session = _FakeSession(_Result(scalar="item-1"))
    result = _producer(session).enqueue(command(expires_at=NOW + timedelta(hours=1)))
    assert (result.inbox_item_id, result.created) == ("item-1", True)
    assert session.commits == 0 and len(session.statements) == 1
    compiled = session.statements[0].compile(dialect=postgresql.dialect())  # type: ignore[no-untyped-call]
    assert "ON CONFLICT (recipient_account_id, trigger_dedupe_key) DO NOTHING" in str(compiled)
    assert compiled.params["created_at"] == NOW
    assert compiled.params["recipient_account_id"] == ACCOUNT
    assert compiled.params["command_sha256"] == command_sha256(
        command(expires_at=NOW + timedelta(hours=1))
    )


def test_a_duplicate_with_the_same_hash_returns_the_stored_item() -> None:
    digest = command_sha256(command())
    session = _FakeSession(
        _Result(scalar=None), _Result(mapping={"inbox_item_id": "item-1", "command_sha256": digest})
    )
    result = _producer(session).enqueue(command())
    assert (result.inbox_item_id, result.created) == ("item-1", False)


def test_a_duplicate_with_another_hash_raises() -> None:
    session = _FakeSession(
        _Result(scalar=None),
        _Result(mapping={"inbox_item_id": "item-1", "command_sha256": "0" * 64}),
    )
    with pytest.raises(NotificationDedupeConflict):
        _producer(session).enqueue(command())


def test_a_rejected_command_writes_nothing() -> None:
    session = _FakeSession()
    for bad in (
        command(safe_parameters={"label": "Nguyen Be Lan"}),
        command(expires_at=NOW),
        command(expires_at=NOW - timedelta(minutes=1)),
    ):
        with pytest.raises(NotificationRejected):
            _producer(session).enqueue(bad)
    assert session.statements == []


# ------------------------------------------------------------------ what a body hides
def test_the_item_body_hides_the_recipient_the_trigger_and_the_hash() -> None:
    row = {
        "inbox_item_id": "item-1",
        "recipient_account_id": ACCOUNT,
        "recipient_role": "parent",
        "organization_ref": "org-1",
        "notification_type": "CLASS_ARCHIVED",
        "template_version": 2,
        "trigger_id": "trg-1",
        "trigger_dedupe_key": "key-1",
        "command_sha256": "a" * 64,
        "safe_parameters": {"count": 3},
        "created_at": NOW,
        "read_at": None,
        "expires_at": None,
    }
    body = item_body(cast(Any, row))
    assert set(body) == {
        "contract",
        "inbox_item_id",
        "notification_type",
        "template_version",
        "safe_parameters",
        "created_at",
        "read_at",
        "expires_at",
    }
    text = json.dumps(body, default=str)
    for hidden in (ACCOUNT, "org-1", "trg-1", "key-1", "a" * 64, "recipient"):
        assert hidden not in text


# ------------------------------------------------------------------ cursor
def test_the_cursor_round_trips_and_rejects_another_scope_or_a_naive_time() -> None:
    moment = datetime(2026, 11, 21, 7, 0, 0, 123456, tzinfo=UTC)
    cursor = encode_cursor(scope="notifications", sort_key=utc_iso(moment), item_id="item-9")
    assert decode_time_cursor(cursor, scope="notifications") == (moment, "item-9")
    with pytest.raises(Exception) as other_scope:
        decode_time_cursor(cursor, scope="lesson-occurrences")
    assert getattr(other_scope.value, "status_code", None) == 400
    naive = encode_cursor(scope="notifications", sort_key="2026-11-21T07:00:00", item_id="i")
    with pytest.raises(Exception) as bad_time:
        decode_time_cursor(naive, scope="notifications")
    assert getattr(bad_time.value, "status_code", None) == 400
    with pytest.raises(Exception) as garbage:
        decode_time_cursor("not-a-cursor", scope="notifications")
    assert getattr(garbage.value, "status_code", None) == 400


def test_utc_iso_normalises_the_offset() -> None:
    local = datetime(2026, 11, 21, 14, 0, tzinfo=UTC).astimezone(timezone(timedelta(hours=7)))
    assert local.isoformat() == "2026-11-21T21:00:00+07:00"
    assert utc_iso(local) == "2026-11-21T14:00:00+00:00"


# ------------------------------------------------------------------ migration text and graph
def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("nt_0001_migration", _MIGRATION)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _constants(path: Path) -> dict[str, Any]:
    found: dict[str, Any] = {}
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in {
                "revision",
                "down_revision",
                "branch_labels",
                "depends_on",
            }:
                found[target.id] = ast.literal_eval(node.value)
    return found


def test_revision_is_the_only_child_of_cls_0002_and_includes_sketch_deck_head() -> None:
    constants = _constants(_MIGRATION)
    assert constants["revision"] == "20261120_nt_0001" and len(constants["revision"]) <= 32
    assert constants["down_revision"] == "20261120_cls_0002"
    assert constants["branch_labels"] is None and constants["depends_on"] is None
    graph: dict[str, tuple[str, ...]] = {}
    for path in sorted(_VERSIONS.glob("*.py")):
        found = _constants(path)
        down = found.get("down_revision")
        graph[str(found["revision"])] = (
            () if down is None else (down,) if isinstance(down, str) else tuple(down)
        )
    children: dict[str, set[str]] = {}
    for revision, downs in graph.items():
        for down in downs:
            children.setdefault(down, set()).add(revision)
    assert children["20261120_cls_0002"] == {"20261120_nt_0001"}
    # FEAT-066 T-4b1: 20261120_sel_0001 (the child-selection table) follows the inbox migration.
    assert children["20261120_nt_0001"] == {"20261120_sel_0001"}
    # FEAT-066 T-10b: 20261121_ll_0001 (remix lineage) is the single child of the selection table.
    assert children["20261120_sel_0001"] == {"20261121_ll_0001"}
    assert children["20261121_ll_0001"] == {"20261121_pg_0001"}
    assert children["20261121_pg_0001"] == {"20261121_nt_0002"}
    # T-SLD1 extends the notification delivery leaf with the presentation migration.
    assert children["20261121_nt_0002"] == {"20261125_nt_0003"}
    assert children["20261125_nt_0003"] == {
        "20261122_t6b_0001",
        "20261126_sl_0001",
    }
    assert children["20261126_sl_0001"] == {"20261126_sh_0001"}
    assert children["20261126_sh_0001"] == {"20261126_dc_0001"}
    assert "20261126_dc_0001" not in children


def test_orm_matches_the_migration_columns_checks_unique_and_indexes() -> None:
    module = _load()
    table = INBOX_ITEMS
    assert table.schema == module.SCHEMA == "notifications" and table.name == module.TABLE
    checks = {
        str(constraint.name): " ".join(str(constraint.sqltext).split())
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    }
    expected = {
        "ck_notif_inbox_role": module.ROLE_CHECK,
        "ck_notif_inbox_type": module.TYPE_CHECK,
        "ck_notif_inbox_template": module.TEMPLATE_CHECK,
        "ck_notif_inbox_keys": module.KEYS_CHECK,
        "ck_notif_inbox_hash": module.HASH_CHECK,
        "ck_notif_inbox_params": module.PARAMS_CHECK,
        "ck_notif_inbox_times": module.TIMES_CHECK,
    }
    assert checks == {name: " ".join(text.split()) for name, text in expected.items()}
    uniques = [c for c in table.constraints if isinstance(c, UniqueConstraint)]
    assert [(u.name, [col.name for col in u.columns]) for u in uniques] == [
        (module.DEDUPE_CONSTRAINT, ["recipient_account_id", "trigger_dedupe_key"])
    ]
    indexes = {index.name: index for index in table.indexes}
    assert set(indexes) == {module.PAGE_INDEX, module.UNREAD_INDEX}
    where = indexes[module.UNREAD_INDEX].dialect_options["postgresql"]["where"]
    assert str(where) == module.UNREAD_WHERE


def test_the_migration_creates_one_table_and_nothing_for_t8b() -> None:
    text = _MIGRATION.read_text(encoding="utf-8")
    assert text.count("op.create_table(") == 1 and text.count("op.drop_table(") == 1
    for deferred in ("push_endpoints", "delivery_attempts", "endpoint", "device_token"):
        assert deferred not in text.split('"""', 2)[2], deferred
    assert "alembic downgrade 20261120_cls_0002" in text and "downgrade -1" not in text
    upgrade_body = text.split("def upgrade", 1)[1].split("def downgrade", 1)[0]
    assert "DELETE" not in upgrade_body.upper() and "UPDATE" not in upgrade_body.upper()
    downgrade_body = text.split("def downgrade", 1)[1]
    assert downgrade_body.index("DOWNGRADE_GUARD") < downgrade_body.index("drop_table")
    assert "DELETE FROM" not in downgrade_body.upper()


def test_no_inbox_column_can_hold_child_content_or_a_contact() -> None:
    names = {column.name for column in INBOX_ITEMS.columns}
    for word in ("name", "child", "story", "media", "url", "email", "endpoint", "token", "address"):
        assert not [name for name in names if word in name], word
