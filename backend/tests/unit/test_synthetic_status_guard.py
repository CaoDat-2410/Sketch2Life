"""Dependency-level status guard checks without routes, network, or database I/O."""

from __future__ import annotations

import ast
import hashlib
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import operators
from sqlalchemy.sql.elements import BinaryExpression, BooleanClauseList, UnaryExpression
from starlette.requests import Request

from sketch2life.domain.eligibility import PROOF_VERSION
from sketch2life.infrastructure.persistence.be1_models import (
    ClassroomSessionModel,
    ConsentRecordModel,
    DeviceGrantModel,
    ManagedProfileModel,
    SessionMembershipModel,
    SyntheticEligibilityProofModel,
)
from sketch2life.interfaces.http import be1_runtime
from sketch2life.interfaces.http.be1_runtime import Be1Runtime, VerifiedDeviceStatusContext
from sketch2life.interfaces.http.routers.be1_common import consent_is_effective

_DEVICE_KEY = "synthetic-device-key-0123456789abcdef"
_RUNTIME_SOURCE = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "sketch2life"
    / "interfaces"
    / "http"
    / "be1_runtime.py"
)


class _Db:
    def __init__(self, grant: object, session: object, membership: object) -> None:
        self.rows = {
            DeviceGrantModel: grant,
            ClassroomSessionModel: session,
            SessionMembershipModel: membership,
        }
        self.queried: list[type[object]] = []
        self.added: list[object] = []
        self.commits = 0

    def scalar(self, statement: Any) -> object:
        model = statement.column_descriptions[0]["entity"]
        self.queried.append(model)
        return self.rows[model]

    def add(self, value: object) -> None:
        self.added.append(value)

    def commit(self) -> None:
        self.commits += 1


def _facts(
    *, session_state: str = "paused", membership_state: str = "admitted"
) -> tuple[SimpleNamespace, SimpleNamespace, SimpleNamespace]:
    grant = SimpleNamespace(
        grant_id="synthetic-grant",
        state="admitted",
        organization_id="synthetic-org",
        session_id="synthetic-session",
        admitted_child_id="synthetic-child",
        device_key_hash=hashlib.sha256(_DEVICE_KEY.encode("utf-8")).hexdigest(),
    )
    session = SimpleNamespace(
        organization_id="synthetic-org",
        session_id="synthetic-session",
        class_id="synthetic-class",
        state=session_state,
        configuration={
            "purpose_ref": "synthetic-purpose",
            "pilot_run_ref": "synthetic-run",
        },
    )
    membership = SimpleNamespace(
        organization_id="synthetic-org",
        session_id="synthetic-session",
        child_id="synthetic-child",
        device_grant_id="synthetic-grant",
        state=membership_state,
        group_id=None,
    )
    return grant, session, membership


def _request(**path_params: str) -> Request:
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/",
            "raw_path": b"/",
            "query_string": b"",
            "headers": [],
            "client": ("127.0.0.1", 1234),
            "server": ("test", 80),
            "path_params": path_params,
        }
    )


def _status_guard(
    db: _Db,
    *,
    settings: object,
    device_key: str = _DEVICE_KEY,
    path_params: dict[str, str] | None = None,
) -> VerifiedDeviceStatusContext:
    return be1_runtime.get_verified_device_status(
        _request(**(path_params or {})),
        grant_id="synthetic-grant",
        device_key=device_key,
        db=cast(Session, db),
        runtime=cast(Be1Runtime, SimpleNamespace(settings=settings)),
    )


def _detail_code(error: HTTPException) -> str:
    assert isinstance(error.detail, dict)
    code = error.detail.get("code")
    assert isinstance(code, str)
    return code


def _install_gate(monkeypatch: pytest.MonkeyPatch, *, allowed: bool) -> list[dict[str, object]]:
    calls: list[dict[str, object]] = []

    def gate(*args: object, **kwargs: object) -> bool:
        calls.append(kwargs)
        return allowed

    monkeypatch.setattr(be1_runtime, "eligibility_ready", gate)
    return calls


@pytest.mark.parametrize("state", ("active", "paused"))
def test_status_guard_allows_active_or_paused_without_group_or_turn(
    monkeypatch: pytest.MonkeyPatch, state: str
) -> None:
    grant, session, membership = _facts(session_state=state)
    db = _Db(grant, session, membership)
    settings = object()
    calls = _install_gate(monkeypatch, allowed=True)

    result = _status_guard(db, settings=settings)

    assert result.grant.grant_id == grant.grant_id
    assert result.session.session_id == session.session_id
    assert result.membership.child_id == membership.child_id
    assert db.queried == [DeviceGrantModel, ClassroomSessionModel, SessionMembershipModel]
    assert calls == [
        {
            "session": session,
            "child_id": "synthetic-child",
            "legal_effective": consent_is_effective,
            "settings": settings,
            "actor": "device:synthetic-grant",
        }
    ]
    assert not db.added
    assert db.commits == 0


@pytest.mark.parametrize("state", ("finished", "lobby"))
def test_status_guard_rejects_non_readable_session_states(state: str) -> None:
    grant, session, membership = _facts(session_state=state)
    db = _Db(grant, session, membership)

    with pytest.raises(HTTPException) as caught:
        _status_guard(db, settings=None)

    assert caught.value.status_code == 403
    assert _detail_code(caught.value) == "DEVICE_SCOPE_INACTIVE"
    assert db.queried == [DeviceGrantModel, ClassroomSessionModel]


def test_status_guard_rejects_revoked_grant() -> None:
    grant, session, membership = _facts()
    grant.state = "revoked"
    db = _Db(grant, session, membership)

    with pytest.raises(HTTPException) as caught:
        _status_guard(db, settings=None)

    assert caught.value.status_code == 401
    assert _detail_code(caught.value) == "INVALID_DEVICE_CREDENTIAL"
    assert db.queried == [DeviceGrantModel]


def test_status_guard_rejects_wrong_device_key() -> None:
    grant, session, membership = _facts()
    db = _Db(grant, session, membership)

    with pytest.raises(HTTPException) as caught:
        _status_guard(
            db,
            settings=None,
            device_key="another-synthetic-device-key-012345",
        )

    assert caught.value.status_code == 401
    assert _detail_code(caught.value) == "INVALID_DEVICE_CREDENTIAL"


@pytest.mark.parametrize(
    "path_params",
    (
        {"organization_id": "foreign-org"},
        {"session_id": "foreign-session"},
    ),
)
def test_status_guard_rejects_foreign_path_scope(path_params: dict[str, str]) -> None:
    grant, session, membership = _facts()
    db = _Db(grant, session, membership)

    with pytest.raises(HTTPException) as caught:
        _status_guard(db, settings=None, path_params=path_params)

    assert caught.value.status_code == 403
    assert _detail_code(caught.value) == "DEVICE_SCOPE_INACTIVE"
    assert db.queried == [DeviceGrantModel]


def test_status_guard_rejects_membership_not_bound_to_grant() -> None:
    grant, session, membership = _facts(membership_state="left")
    db = _Db(grant, session, membership)

    with pytest.raises(HTTPException) as caught:
        _status_guard(db, settings=None)

    assert caught.value.status_code == 403
    assert _detail_code(caught.value) == "DEVICE_MEMBERSHIP_INACTIVE"


def test_status_guard_rejects_membership_for_another_grant() -> None:
    grant, session, membership = _facts()
    membership.device_grant_id = "foreign-grant"
    db = _Db(grant, session, membership)

    with pytest.raises(HTTPException) as caught:
        _status_guard(db, settings=None)

    assert caught.value.status_code == 403
    assert _detail_code(caught.value) == "DEVICE_MEMBERSHIP_INACTIVE"


def test_status_guard_audits_denied_eligibility_without_success_audit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    grant, session, membership = _facts()
    db = _Db(grant, session, membership)
    calls = _install_gate(monkeypatch, allowed=False)

    with pytest.raises(HTTPException) as caught:
        _status_guard(db, settings=object())

    assert caught.value.status_code == 409
    assert _detail_code(caught.value) == "CONSENT_NOT_EFFECTIVE"
    assert len(calls) == 1
    assert "audit_action" not in calls[0]
    assert len(db.added) == 1
    assert getattr(db.added[0], "decision", None) == "denied_consent_pending"
    assert db.commits == 1


def _function(source: str, name: str) -> ast.FunctionDef:
    tree = ast.parse(source)
    functions = [
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    assert len(functions) == 1
    return functions[0]


def test_status_guard_is_separate_from_group_and_turn_write_authority() -> None:
    source = _RUNTIME_SOURCE.read_text(encoding="utf-8")
    read_guard = _function(source, "get_verified_device_status")
    write_guard = _function(source, "get_verified_device")
    read_names = {node.id for node in ast.walk(read_guard) if isinstance(node, ast.Name)}
    write_names = {node.id for node in ast.walk(write_guard) if isinstance(node, ast.Name)}

    assert "SessionGroupModel" not in read_names
    assert "ChildTurnModel" not in read_names
    assert "eligibility_ready" in read_names
    assert "SessionGroupModel" in write_names
    assert "ChildTurnModel" in write_names


# --------------------------------------------------------------------------------------
# Real eligibility gate (no monkeypatch) over a column-filtering in-memory fake.
#
# The fake applies the WHERE clauses, ORDER BY and LIMIT of the statements the guard and
# `eligibility_ready` really issue, so an expired, revoked, unbound or foreign proof is
# excluded or refused by the production code path and not by a canned return value.
# Covered offline here: the guard's own checks and the typed decision over fetched rows.
# Covered only by PostgreSQL (not run in this task): SQL dialect behavior, timestamptz
# round-trip and index/ordering semantics on real rows.
# --------------------------------------------------------------------------------------
_NOW = datetime.now(UTC)
_REAL_SETTINGS = SimpleNamespace(env="test", synthetic_pilot_enabled=True)


def _column_value(row: object, clause_side: Any) -> object:
    return getattr(row, clause_side.key)


def _matches(clause: Any, row: object) -> bool:
    if isinstance(clause, BooleanClauseList):
        results = (_matches(part, row) for part in clause.clauses)
        if clause.operator is operators.and_:
            return all(results)
        if clause.operator is operators.or_:
            return any(results)
        raise NotImplementedError(f"unsupported boolean operator {clause.operator}")
    if isinstance(clause, BinaryExpression):
        left = _column_value(row, clause.left)
        if clause.operator is operators.is_:
            return left is None
        right = clause.right.value
        if clause.operator is operators.eq:
            return bool(left == right)
        if clause.operator is operators.in_op:
            return left in tuple(right)
        raise NotImplementedError(f"unsupported operator {clause.operator}")
    raise NotImplementedError(f"unsupported clause {type(clause).__name__}")


def _sort_key(attribute: str) -> Callable[[object], Any]:
    def key(row: object) -> Any:
        return getattr(row, attribute)

    return key


class _FilteringDb:
    """Evaluates simple SELECTs over per-model row lists; unsupported SQL fails loudly."""

    def __init__(self, rows: dict[type[object], list[object]]) -> None:
        self.rows = rows
        self.queried: list[type[object]] = []
        self.added: list[object] = []
        self.commits = 0

    def scalar(self, statement: Any) -> object:
        description = statement.column_descriptions[0]
        model = description["entity"]
        self.queried.append(model)
        candidates = list(self.rows.get(model, []))
        if statement.whereclause is not None:
            candidates = [row for row in candidates if _matches(statement.whereclause, row)]
        for ordering in reversed(statement._order_by_clauses):
            assert isinstance(ordering, UnaryExpression)
            reverse = ordering.modifier is operators.desc_op
            column_name = ordering.element.key
            assert isinstance(column_name, str)
            candidates.sort(key=_sort_key(column_name), reverse=reverse)
        if not candidates:
            return None
        first = candidates[0]
        if isinstance(description["expr"], type):
            return first
        return getattr(first, description["name"])

    def add(self, value: object) -> None:
        self.added.append(value)

    def commit(self) -> None:
        self.commits += 1


def _proof_row(**changes: object) -> SimpleNamespace:
    values: dict[str, object] = {
        "evidence_id": "synthetic-proof",
        "schema_version": PROOF_VERSION,
        "organization_id": "synthetic-org",
        "class_id": "synthetic-class",
        "child_profile_id": "synthetic-child",
        "purpose_ref": "synthetic-purpose",
        "run_ref": "synthetic-run",
        "session_id": "synthetic-session",
        "issued_at": _NOW - timedelta(hours=1),
        "expires_at": _NOW + timedelta(hours=1),
        "revoked_at": None,
    }
    values.update(changes)
    return SimpleNamespace(**values)


def _profile_row(**changes: object) -> SimpleNamespace:
    values: dict[str, object] = {
        "organization_id": "synthetic-org",
        "class_id": "synthetic-class",
        "child_id": "synthetic-child",
        "state": "active",
        "data_origin": "SYNTHETIC_DEV",
    }
    values.update(changes)
    return SimpleNamespace(**values)


def _consent_row(**changes: object) -> SimpleNamespace:
    values: dict[str, object] = {
        "consent_id": "legal-consent",
        "organization_id": "synthetic-org",
        "class_id": "synthetic-class",
        "child_id": "synthetic-child",
        "purpose_ref": "synthetic-purpose",
        "state": "effective",
    }
    values.update(changes)
    return SimpleNamespace(**values)


def _real_db(
    *,
    session_state: str = "active",
    profile: SimpleNamespace | None = None,
    proofs: tuple[SimpleNamespace, ...] | None = None,
    consents: tuple[SimpleNamespace, ...] = (),
    grant_changes: dict[str, object] | None = None,
) -> _FilteringDb:
    grant, session, membership = _facts(session_state=session_state)
    for name, value in (grant_changes or {}).items():
        setattr(grant, name, value)
    return _FilteringDb(
        {
            DeviceGrantModel: [grant],
            ClassroomSessionModel: [session],
            SessionMembershipModel: [membership],
            ManagedProfileModel: [profile if profile is not None else _profile_row()],
            SyntheticEligibilityProofModel: list(
                proofs if proofs is not None else (_proof_row(),)
            ),
            ConsentRecordModel: list(consents),
        }
    )


def _real_guard(
    db: _FilteringDb,
    *,
    settings: object = _REAL_SETTINGS,
    path_params: dict[str, str] | None = None,
) -> VerifiedDeviceStatusContext:
    return be1_runtime.get_verified_device_status(
        _request(**(path_params or {})),
        grant_id="synthetic-grant",
        device_key=_DEVICE_KEY,
        db=cast(Session, db),
        runtime=cast(Be1Runtime, SimpleNamespace(settings=settings)),
    )


def _assert_refused(
    db: _FilteringDb, status: int, code: str, **guard_kwargs: Any
) -> HTTPException:
    with pytest.raises(HTTPException) as caught:
        _real_guard(db, **guard_kwargs)
    assert caught.value.status_code == status
    assert _detail_code(caught.value) == code
    return caught.value


def _assert_consent_denied_with_audit(db: _FilteringDb, **guard_kwargs: Any) -> None:
    _assert_refused(db, 409, "CONSENT_NOT_EFFECTIVE", **guard_kwargs)
    # The real typed gate ran: it read the profile before refusing.
    assert ManagedProfileModel in db.queried
    assert len(db.added) == 1
    assert getattr(db.added[0], "decision", None) == "denied_consent_pending"
    assert db.commits == 1


def test_filtering_fake_applies_where_order_and_limit_semantics() -> None:
    older = _proof_row(evidence_id="a", issued_at=_NOW - timedelta(hours=3))
    newer = _proof_row(evidence_id="b", issued_at=_NOW - timedelta(hours=2))
    foreign = _proof_row(evidence_id="c", child_profile_id="another-child")
    db = _real_db(proofs=(older, newer, foreign))

    from sketch2life.infrastructure.persistence.core_store import (
        load_profile_origin,
        load_synthetic_proof,
    )

    proof = load_synthetic_proof(
        cast(Session, db),
        organization_id="synthetic-org",
        class_id="synthetic-class",
        child_id="synthetic-child",
        purpose_ref="synthetic-purpose",
    )
    assert proof is not None and proof.evidence_id == "b"
    assert (
        load_synthetic_proof(
            cast(Session, db),
            organization_id="synthetic-org",
            class_id="synthetic-class",
            child_id="synthetic-child",
            purpose_ref="another-purpose",
        )
        is None
    )
    assert (
        load_profile_origin(
            cast(Session, db),
            organization_id="synthetic-org",
            class_id="synthetic-class",
            child_id="another-child",
        )
        is None
    )


def test_real_gate_allows_a_valid_synthetic_proof_without_audit() -> None:
    db = _real_db()

    result = _real_guard(db)

    assert result.membership.child_id == "synthetic-child"
    assert ManagedProfileModel in db.queried
    assert SyntheticEligibilityProofModel in db.queried
    assert not db.added
    assert db.commits == 0


def test_real_gate_allows_active_and_paused_sessions() -> None:
    for state in ("active", "paused"):
        assert _real_guard(_real_db(session_state=state)).session.state == state


def test_real_gate_keeps_the_legal_consent_path_working() -> None:
    legal = _real_db(
        profile=_profile_row(data_origin="REAL"), proofs=(), consents=(_consent_row(),)
    )
    assert _real_guard(legal).grant.grant_id == "synthetic-grant"

    pending = _real_db(
        profile=_profile_row(data_origin="REAL"),
        proofs=(),
        consents=(_consent_row(state="revoked"),),
    )
    _assert_consent_denied_with_audit(pending)

    other_purpose = _real_db(
        profile=_profile_row(data_origin="REAL"),
        proofs=(),
        consents=(_consent_row(purpose_ref="another-purpose"),),
    )
    _assert_consent_denied_with_audit(other_purpose)


@pytest.mark.parametrize(
    "proof_changes",
    (
        {"expires_at": _NOW - timedelta(minutes=1)},
        {"revoked_at": _NOW - timedelta(minutes=5)},
        {"session_id": None},
        {"session_id": "another-session"},
        {"run_ref": "another-run"},
        {"issued_at": _NOW + timedelta(hours=1), "expires_at": _NOW + timedelta(hours=2)},
        {"schema_version": "unknown-proof-version"},
        {"child_profile_id": "another-child"},
        {"purpose_ref": "another-purpose"},
        {"organization_id": "another-org"},
    ),
    ids=(
        "expired",
        "revoked",
        "unbound_session",
        "wrong_session",
        "wrong_run",
        "not_yet_valid",
        "unknown_schema",
        "other_child",
        "other_purpose",
        "other_org",
    ),
)
def test_real_gate_denies_unusable_synthetic_proofs(proof_changes: dict[str, object]) -> None:
    db = _real_db(proofs=(_proof_row(**proof_changes),))

    _assert_consent_denied_with_audit(db)


def test_real_gate_denies_when_no_proof_exists() -> None:
    _assert_consent_denied_with_audit(_real_db(proofs=()))


@pytest.mark.parametrize(
    "settings",
    (
        None,
        SimpleNamespace(env="test", synthetic_pilot_enabled=False),
        SimpleNamespace(env="production", synthetic_pilot_enabled=True),
    ),
    ids=("settings_missing", "pilot_disabled", "production_environment"),
)
def test_real_gate_denies_when_the_pilot_is_off_or_environment_is_not_dev(
    settings: object,
) -> None:
    _assert_consent_denied_with_audit(_real_db(), settings=settings)


def test_real_gate_denies_a_real_profile_that_only_has_a_synthetic_proof() -> None:
    _assert_consent_denied_with_audit(_real_db(profile=_profile_row(data_origin="REAL")))


def test_real_gate_rejects_a_grant_without_an_admitted_child() -> None:
    db = _real_db(grant_changes={"admitted_child_id": None})

    _assert_refused(db, 403, "DEVICE_SCOPE_INACTIVE")

    assert ManagedProfileModel not in db.queried
    assert not db.added


@pytest.mark.parametrize("name", ("organization_id", "org_id"))
def test_real_gate_rejects_foreign_organization_path_alias_before_any_other_read(
    name: str,
) -> None:
    db = _real_db()

    _assert_refused(db, 403, "DEVICE_SCOPE_INACTIVE", path_params={name: "foreign-org"})

    assert db.queried == [DeviceGrantModel]
    assert not db.added


@pytest.mark.parametrize("name", ("organization_id", "org_id"))
def test_real_gate_accepts_own_organization_path_alias(name: str) -> None:
    result = _real_guard(_real_db(), path_params={name: "synthetic-org"})

    assert result.grant.organization_id == "synthetic-org"


@pytest.mark.parametrize("state", ("finished", "lobby", "configured"))
def test_real_gate_rejects_sessions_that_cannot_be_read(state: str) -> None:
    db = _real_db(session_state=state)

    _assert_refused(db, 403, "DEVICE_SCOPE_INACTIVE")

    assert ManagedProfileModel not in db.queried
    assert not db.added


def test_real_gate_rejects_revoked_grant_through_the_query_filter() -> None:
    db = _real_db(grant_changes={"state": "revoked"})

    _assert_refused(db, 401, "INVALID_DEVICE_CREDENTIAL")

    assert db.queried == [DeviceGrantModel]


def test_real_gate_rejects_session_path_that_is_not_the_grant_session() -> None:
    db = _real_db()

    _assert_refused(db, 403, "DEVICE_SCOPE_INACTIVE", path_params={"session_id": "other"})

    assert db.queried == [DeviceGrantModel]
