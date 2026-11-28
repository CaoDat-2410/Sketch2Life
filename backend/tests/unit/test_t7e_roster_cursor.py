"""T-7e unit tests: Teacher roster paging, filter statement and Manager audience (no database).

D-066-100; SRS l.832 (consent for real data only), l.1640 (cursor lists), l.1635 (additive fields),
l.2586 (Profile row). A fake session records the statement of each page and answers by the table.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any, cast

import pytest
from fastapi import HTTPException
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.interfaces.http.api_conventions import (
    CURSOR_MAX_LENGTH,
    decode_time_cursor,
    encode_cursor,
)
from sketch2life.interfaces.http.routers import be1_common, be1_registry

ISSUER = "https://issuer.example.test/synthetic"
PRINCIPAL = VerifiedPrincipal(subject="adult-1", issuer=ISSUER, roles=frozenset())
ORG = "org-1"
CLASS = "class-a"
SCOPE = f"be1.profiles:{ORG}:{CLASS}"
BASE_TIME = datetime(2026, 11, 23, 8, 0, 0, tzinfo=UTC)


class _Scalars:
    def __init__(self, rows: list[Any]) -> None:
        self._rows = rows

    def all(self) -> list[Any]:
        return self._rows


class _Session:
    def __init__(self, role: str, class_id: str | None, rows: list[Any], total: int = 0) -> None:
        self._assignment = SimpleNamespace(
            organization_id=ORG,
            subject=PRINCIPAL.subject,
            class_id=class_id,
            role=role,
            active=True,
            assignment_id="assignment-1",
        )
        self._account_role = "school_manager" if role == "school_admin" else "teacher"
        self._rows = rows
        self._total = total
        self.page_statements: list[Any] = []

    def get(self, _model: Any, _key: Any) -> Any:
        return SimpleNamespace(state="active", account_role=self._account_role, issuer=ISSUER)

    def scalars(self, statement: Any) -> _Scalars:
        text = str(statement)
        if "be1_organization_assignments" in text:
            return _Scalars([self._assignment])
        self.page_statements.append(statement)
        return _Scalars(self._rows)

    def scalar(self, statement: Any) -> Any:
        if "count(" in str(statement).lower():
            return self._total
        return SimpleNamespace(organization_id=ORG, class_id=CLASS, state="active")

    def commit(self) -> None:  # pragma: no cover - a read must not reach it
        raise AssertionError("a roster read must not commit")


def _row(index: int, created_at: datetime | None = None) -> Any:
    return SimpleNamespace(
        child_id=f"child-{index:03d}",
        class_id=CLASS,
        display_name=f"Synthetic Learner {index}",
        age_months=60,
        created_at=created_at or BASE_TIME + timedelta(minutes=index),
    )


def _teacher(rows: list[Any], total: int = 0) -> _Session:
    return _Session("teacher", CLASS, rows, total)


def _call(session: _Session, *, limit: int = 25, cursor: str | None = None) -> Any:
    return be1_registry.list_profiles(
        ORG,
        CLASS,
        limit=limit,
        cursor=cursor,
        principal=PRINCIPAL,
        db=cast(Session, session),
    )


def _sql(statement: Any) -> str:
    return str(
        statement.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})
    )


def _error(call: Any) -> HTTPException:
    with pytest.raises(HTTPException) as caught:
        call()
    return caught.value


def _cursor(scope: str, sort_key: str) -> str:
    return encode_cursor(scope=scope, sort_key=sort_key, item_id="x")


def test_next_cursor_is_built_from_the_last_returned_row_and_round_trips() -> None:
    rows = [_row(1), _row(2), _row(3)]
    body = _call(_teacher(rows, total=3), limit=2)
    assert [item["child_id"] for item in body["items"]] == ["child-001", "child-002"]
    assert body["active_profile_count"] == 3
    assert decode_time_cursor(body["next_cursor"], scope=SCOPE) == (
        rows[1].created_at,
        "child-002",
    )


def test_next_cursor_is_null_when_no_further_row_exists() -> None:
    exact = _call(_teacher([_row(1), _row(2)], total=2), limit=2)
    assert exact["next_cursor"] is None and len(exact["items"]) == 2
    empty = _call(_teacher([], total=5))
    assert empty == {
        "contract": "Be1ManagedProfileListV1",
        "items": [],
        "next_cursor": None,
        "active_profile_count": 5,
    }


def test_equal_timestamps_keep_the_child_id_in_the_cursor() -> None:
    rows = [_row(1, BASE_TIME), _row(2, BASE_TIME), _row(3, BASE_TIME)]
    body = _call(_teacher(rows, total=3), limit=1)
    assert decode_time_cursor(body["next_cursor"], scope=SCOPE) == (BASE_TIME, "child-001")


def test_page_statement_orders_by_created_at_then_child_id_and_fetches_one_extra() -> None:
    session = _teacher([_row(1)])
    _call(session, limit=7)
    sql = _sql(session.page_statements[0])
    assert "ORDER BY be1_managed_profiles.created_at, be1_managed_profiles.child_id" in sql
    assert "LIMIT 8" in sql
    assert len(session.page_statements) == 1  # one statement per page (D5)


def test_cursor_adds_a_strict_keyset_condition() -> None:
    cursor = encode_cursor(scope=SCOPE, sort_key=BASE_TIME.isoformat(), item_id="child-010")
    session = _teacher([])
    _call(session, cursor=cursor)
    sql = _sql(session.page_statements[0])
    assert "(be1_managed_profiles.created_at, be1_managed_profiles.child_id) >" in sql
    assert "child-010" in sql


def test_filter_lists_synthetic_or_consented_real_only() -> None:
    sql = _sql(be1_registry._roster_listed(ORG, CLASS))
    assert "be1_managed_profiles.state = 'active'" in sql
    assert "be1_managed_profiles.data_origin = 'SYNTHETIC_DEV'" in sql
    assert "be1_managed_profiles.data_origin = 'REAL'" in sql
    assert "be1_managed_profiles.consent_purpose_ref IS NOT NULL" in sql
    assert "EXISTS (SELECT *" in sql
    assert "be1_consent_records.state = 'effective'" in sql
    for column in ("organization_id", "class_id", "child_id"):
        assert f"be1_consent_records.{column} = be1_managed_profiles.{column}" in sql
    assert "be1_consent_records.purpose_ref = be1_managed_profiles.consent_purpose_ref" in sql
    # No branch for LEGACY_UNCLASSIFIED: such a profile is never listed (SRS l.832).
    assert "LEGACY_UNCLASSIFIED" not in sql


class _ConsentDb:
    """A session whose consent lookup answers one value: the plain `consent_is_effective` check."""

    def __init__(self, found: str | None) -> None:
        self.found = found
        self.statements: list[str] = []

    def scalar(self, statement: Any) -> Any:
        self.statements.append(_sql(statement))
        return self.found


def test_the_python_predicate_matches_the_sql_filter() -> None:
    kwargs: dict[str, Any] = {"organization_id": ORG, "class_id": CLASS, "child_id": "child-1"}
    no_purpose = _ConsentDb("consent-1")
    assert not be1_common.consent_is_effective(
        cast(Session, no_purpose), purpose_ref=None, **kwargs
    )
    assert no_purpose.statements == []
    effective = _ConsentDb("consent-1")
    assert be1_common.consent_is_effective(cast(Session, effective), purpose_ref="p-1", **kwargs)
    assert "be1_consent_records.state = 'effective'" in effective.statements[0]
    assert not be1_common.consent_is_effective(
        cast(Session, _ConsentDb(None)), purpose_ref="p-1", **kwargs
    )


@pytest.mark.parametrize(
    "cursor",
    [
        "%%%",
        "e30",
        _cursor("be1.consents:org-1:class-a", BASE_TIME.isoformat()),
        _cursor("be1.profiles:org-1:class-b", BASE_TIME.isoformat()),
        _cursor(SCOPE, "not-a-time"),
        _cursor(SCOPE, "2026-11-23T08:00:00"),
    ],
)
def test_teacher_bad_or_foreign_scope_cursor_is_400(cursor: str) -> None:
    error = _error(lambda: _call(_teacher([_row(1)]), cursor=cursor))
    assert error.status_code == 400
    assert error.detail == {
        "code": "INVALID_REQUEST",
        "field_errors": [{"field": "cursor", "code": "INVALID_FORMAT"}],
    }


def test_cursor_is_decoded_only_after_the_scope_checks() -> None:
    # An out-of-scope Teacher and an unassigned guide get their 404/403 whatever the cursor says.
    other_class = _Session("teacher", "class-b", [_row(1)])
    assert _error(lambda: _call(other_class, cursor="%%%")).status_code == 404
    guide = _Session("guide", None, [_row(1)])
    assert _error(lambda: _call(guide, cursor="%%%")).status_code == 403


def test_the_shared_query_types_carry_the_published_bounds() -> None:
    # The framework refuses an overlong cursor or an out-of-range limit, for both audiences,
    # before the handler runs; this pins the bounds the catalog publishes.
    assert CURSOR_MAX_LENGTH == 1024
    cursor_bounds = {
        name: getattr(item, name)
        for item in be1_registry.cursor_query().metadata
        for name in ("min_length", "max_length")
        if hasattr(item, name)
    }
    assert cursor_bounds == {"min_length": 1, "max_length": CURSOR_MAX_LENGTH}
    limit = be1_registry.limit_query()
    limit_bounds = {
        name: getattr(item, name)
        for item in limit.metadata
        for name in ("ge", "le")
        if hasattr(item, name)
    }
    assert (limit.default, limit_bounds) == (25, {"ge": 1, "le": 100})


def test_manager_gets_the_summary_and_never_decodes_the_cursor() -> None:
    manager = _Session("school_admin", None, [_row(1)], total=4)
    body = _call(manager, limit=1, cursor="%%%")  # a well-formed length, but not a real cursor
    assert body == {
        "contract": "Be1ClassRosterSummaryV1",
        "class_id": CLASS,
        "active_profile_count": 4,
    }
    assert manager.page_statements == []  # no page query for a Manager


def test_items_carry_only_the_four_item_fields() -> None:
    body = _call(_teacher([_row(1)], total=1))
    assert set(body["items"][0]) == {"child_id", "class_id", "display_name", "age_months"}
    assert set(body) == {"contract", "items", "next_cursor", "active_profile_count"}
