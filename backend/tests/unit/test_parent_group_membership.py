from __future__ import annotations

import importlib.util
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa
from fastapi import HTTPException
from pydantic import ValidationError
from starlette.requests import Request

from sketch2life.contracts.schemas.lesson_library import (
    ParentGroupMemberCountsV1,
    ParentGroupMembershipV1,
    ParentGroupMemberSummaryV1,
)
from sketch2life.domain.lesson_library.model import (
    LessonLibraryRuleError,
    decline_parent_group_invitation,
)
from sketch2life.infrastructure.lesson_library.service import (
    LessonLibraryError,
    LessonLibraryService,
    _decode_scoped_cursor,
    _encode_scoped_cursor,
)
from sketch2life.infrastructure.lesson_library.tables import PARENT_GROUP_MEMBERS
from sketch2life.interfaces.http.api_conventions import parse_idempotency_key
from sketch2life.interfaces.http.openapi_contract import MOUNTED_OPERATIONS, TAG_DESCRIPTIONS

_MIGRATION = (
    Path(__file__).resolve().parents[2]
    / "alembic"
    / "versions"
    / "20261121_pg_0001_declined_membership.py"
)


def _load_migration():
    spec = importlib.util.spec_from_file_location("pg_0001_migration", _MIGRATION)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_decline_transition_only_changes_a_live_invitation() -> None:
    assert decline_parent_group_invitation("invited", invitation_expired=False) == "declined"
    with pytest.raises(LessonLibraryRuleError, match="INVITATION_EXPIRED"):
        decline_parent_group_invitation("invited", invitation_expired=True)
    with pytest.raises(LessonLibraryRuleError, match="INVITATION_EXPIRED"):
        decline_parent_group_invitation("expired", invitation_expired=False)
    for state in ("active", "revoked", "declined"):
        with pytest.raises(LessonLibraryRuleError, match="INVALID_STATE_TRANSITION"):
            decline_parent_group_invitation(state, invitation_expired=False)


def test_membership_response_supports_declined_without_private_parent_identity_fields() -> None:
    membership = ParentGroupMembershipV1.model_validate(
        {
            "contract": "ParentGroupMembershipV1",
            "membership_id": "membership-1",
            "parent_group_id": "group-1",
            "organization_id": "organization-1",
            "state": "DECLINED",
            "invited_at": "2026-11-24T00:00:00Z",
            "expires_at": "2026-12-24T00:00:00Z",
            "accepted_at": None,
            "revision": 2,
        }
    )
    assert membership.state == "DECLINED"
    assert membership.organization_id == "organization-1"
    assert set(membership.model_dump()) == {
        "contract",
        "membership_id",
        "parent_group_id",
        "organization_id",
        "state",
        "invited_at",
        "expires_at",
        "accepted_at",
        "revision",
        "revision_source",
    }
    with pytest.raises(ValidationError):
        ParentGroupMembershipV1.model_validate(
            {
                **membership.model_dump(),
                "parent_principal_ref": "private-parent-ref",
            }
        )


def test_manager_summary_and_counts_match_the_member_read_contract() -> None:
    summary = ParentGroupMemberSummaryV1.model_validate(
        {
            "membership_id": "membership-1",
            "parent_group_id": "group-1",
            "state": "ACCEPTED",
            "invited_at": "2026-11-24T00:00:00Z",
            "expires_at": "2026-12-24T00:00:00Z",
            "accepted_at": "2026-11-24T01:00:00Z",
            "revision": 2,
        }
    )
    assert "contract" not in summary.model_dump()
    assert "revision_source" not in summary.model_dump()
    assert set(summary.model_dump()) == {
        "membership_id",
        "parent_group_id",
        "state",
        "invited_at",
        "expires_at",
        "accepted_at",
        "revision",
    }
    counts = ParentGroupMemberCountsV1.model_validate(
        {"invited": 0, "accepted": 1, "declined": 3, "revoked": 0, "expired": 2, "total": 6}
    )
    assert counts.model_dump() == {
        "invited": 0,
        "accepted": 1,
        "declined": 3,
        "revoked": 0,
        "expired": 2,
        "total": 6,
    }
    with pytest.raises(ValidationError):
        ParentGroupMemberCountsV1.model_validate(
            {"invited": 0, "accepted": -1, "declined": 0, "revoked": 0, "expired": 0, "total": 0}
        )


def test_membership_table_mirrors_declined_state_and_page_indexes() -> None:
    checks = {
        constraint.name: str(constraint.sqltext)
        for constraint in PARENT_GROUP_MEMBERS.constraints
        if isinstance(constraint, sa.CheckConstraint)
    }
    assert "'declined'" in checks["ck_be1_parent_group_member_state"]
    indexes = {index.name: index for index in PARENT_GROUP_MEMBERS.indexes}
    expected = {
        "ix_be1_parent_member_owner_page": (
            "parent_principal_ref", "state", "invited_at", "membership_id"
        ),
        "ix_be1_parent_member_group_page": (
            "parent_group_id", "state", "invited_at", "membership_id"
        ),
    }
    for name, expected_columns in expected.items():
        index = indexes[name]
        expressions = index.expressions
        assert tuple(
            (
                expression.element
                if isinstance(expression, sa.sql.elements.UnaryExpression)
                else expression
            ).name
            for expression in expressions
        ) == expected_columns
        assert all(
            isinstance(expression, sa.sql.elements.UnaryExpression)
            and expression.modifier.__name__ == "desc_op"
            for expression in expressions[-2:]
        )


def test_parent_group_receipt_scope_hash_stays_compact_for_long_resource_ids() -> None:
    service = object.__new__(LessonLibraryService)
    scope = service._parent_group_operation_scope(
        "DELETE /lesson-library/v1/organizations/parent-groups/members",
        "o" * 128,
        "g" * 36,
        "m" * 36,
    )
    assert len(scope) < 256
    assert "o" * 128 not in scope
    assert "g" * 36 not in scope
    assert "m" * 36 not in scope


def test_migration_is_chained_and_downgrade_checks_for_declined_rows(
    monkeypatch: Any,
) -> None:
    migration = _load_migration()
    assert migration.revision == "20261121_pg_0001"
    assert migration.down_revision == "20261121_ll_0001"
    calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

    class _OpSpy:
        def __getattr__(self, name: str):
            def record(*args: Any, **kwargs: Any) -> None:
                calls.append((name, args, kwargs))

            return record

    monkeypatch.setattr(migration, "op", _OpSpy())
    migration.upgrade()
    index_calls = [call for call in calls if call[0] == "create_index"]
    assert [call[1][0] for call in index_calls] == [
        "ix_be1_parent_member_owner_page",
        "ix_be1_parent_member_group_page",
    ]
    for _name, args, _kwargs in index_calls:
        assert args[1] == "be1_parent_group_members"
        assert args[2][1] == "state"
        assert str(args[2][2]) == "invited_at DESC"
        assert str(args[2][3]) == "membership_id DESC"
    calls.clear()
    migration.downgrade()
    assert calls[0][0] == "execute"
    guard_sql = str(calls[0][1][0])
    assert "state = 'declined'" in guard_sql
    assert "RAISE EXCEPTION" in guard_sql


def test_scoped_cursor_rejects_a_different_actor_route_org_group_or_filter() -> None:
    scope = {
        "actor": "synthetic-parent",
        "route": "GET /organizations/{organization_id}/parent-groups/{parent_group_id}/members",
        "organization_id": "synthetic-org-1",
        "parent_group_id": "synthetic-group-1",
        "state": "ACCEPTED",
    }
    cursor = _encode_scoped_cursor(
        scope=scope,
        sort_value=datetime(2026, 11, 24, tzinfo=UTC),
        row_id="synthetic-membership-1",
        value_kind="datetime",
    )
    assert _decode_scoped_cursor(cursor=cursor, scope=scope, value_kind="datetime") == (
        datetime(2026, 11, 24, tzinfo=UTC),
        "synthetic-membership-1",
    )
    for changed in (
        {**scope, "actor": "synthetic-other-parent"},
        {**scope, "route": "GET /another-route"},
        {**scope, "organization_id": "synthetic-org-2"},
        {**scope, "parent_group_id": "synthetic-group-2"},
        {**scope, "state": "DECLINED"},
    ):
        with pytest.raises(LessonLibraryError) as error:
            _decode_scoped_cursor(cursor=cursor, scope=changed, value_kind="datetime")
        assert error.value.code == "INVALID_REQUEST"


def test_revoke_fingerprint_binds_the_expected_if_match_revision() -> None:
    common = {
        "method": "DELETE",
        "organization_id": "synthetic-org-1",
        "group_id": "synthetic-group-1",
        "membership_id": "synthetic-membership-1",
    }
    revision_one = LessonLibraryService._parent_group_command_fingerprint(
        **common, expected_revision=1
    )
    revision_one_replay = LessonLibraryService._parent_group_command_fingerprint(
        **common, expected_revision=1
    )
    revision_two = LessonLibraryService._parent_group_command_fingerprint(
        **common, expected_revision=2
    )
    assert revision_one == revision_one_replay
    assert revision_one != revision_two


@pytest.mark.parametrize("value", [None, "", " ", "x" * 129, "key\x7fvalue"])
def test_idempotency_key_parser_rejects_values_outside_1_to_128_visible_ascii(
    value: str | None,
) -> None:
    headers = [] if value is None else [(b"idempotency-key", value.encode("latin-1"))]
    request = Request(
        {"type": "http", "method": "POST", "path": "/synthetic", "headers": headers}
    )
    with pytest.raises(HTTPException) as error:
        parse_idempotency_key(request)
    assert error.value.status_code == 400
    assert error.value.detail["code"] == "INVALID_REQUEST"


@pytest.mark.parametrize("value", ["a", "x" * 128])
def test_idempotency_key_parser_accepts_both_length_boundaries(value: str) -> None:
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/synthetic",
            "headers": [(b"idempotency-key", value.encode("ascii"))],
        }
    )
    assert parse_idempotency_key(request) == value


def test_all_mounted_catalog_tags_are_declared() -> None:
    assert all(operation["tag"] in TAG_DESCRIPTIONS for operation in MOUNTED_OPERATIONS.values())
