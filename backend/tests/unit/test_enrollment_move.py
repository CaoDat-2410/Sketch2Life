"""FEAT-066 T-7d unit tests: the Teacher enrollment move helpers and handler order.

No database: a fake session answers the handler's reads in order. SRS l.544 (one active
enrollment, the earlier one is closed and kept), l.830 and l.1093, l.1425 (no capacity rule),
l.1651 and l.1699 (expected class revision, STALE_REVISION), l.1697 (keyed commands). The School
Manager is refused by the role helper (403) and no cross-Teacher move exists (X-19).
"""

from __future__ import annotations

import inspect
from types import SimpleNamespace
from typing import Any, cast

import pytest
from fastapi import HTTPException, Request
from pydantic import ValidationError
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.contracts.schemas.be1_runtime import MoveProfileRequest
from sketch2life.infrastructure.persistence.be1_models import (
    Be1CommandReceiptModel,
    EnrollmentModel,
)
from sketch2life.infrastructure.persistence.core_models import (
    CoreAuditEntryModel,
    CoreOutboxEventModel,
)
from sketch2life.interfaces.http.routers import be1_registry
from sketch2life.interfaces.http.routers.be1_common import failure

ORG = "synthetic-org"
CHILD = "synthetic-0123456789abcdef01234567"
PRINCIPAL = VerifiedPrincipal(
    subject="synthetic-teacher", issuer="synthetic-issuer", roles=frozenset(), token_id="t"
)


def _payload(**overrides: Any) -> MoveProfileRequest:
    values: dict[str, Any] = {"target_class_id": "class-b", "target_class_revision": 1}
    values.update(overrides)
    return MoveProfileRequest(**values)


def _request(key: str = "synthetic-key") -> Request:
    return Request({"type": "http", "headers": [(b"idempotency-key", key.encode())]})


def _class(class_id: str, *, revision: int = 1, state: str = "active") -> SimpleNamespace:
    return SimpleNamespace(
        class_id=class_id, organization_id=ORG, state=state, revision=revision
    )


class FakeSession:
    """`scalar` answers lock statements by class id and the other reads in call order."""

    def __init__(
        self,
        ordered: list[object],
        classes: dict[str, SimpleNamespace | None],
        receipt: object | None = None,
    ) -> None:
        self._ordered = list(ordered)
        self._classes = classes
        self._receipt = receipt
        self.added: list[object] = []
        self.locks: list[str] = []
        self.log: list[str] = []
        self.commits = 0
        self.rollbacks = 0
        self.enrollment: SimpleNamespace | None = None

    def scalar(self, statement: object) -> object:
        if isinstance(statement, tuple) and statement[0] == "lock":
            self.locks.append(statement[1])
            return self._classes[statement[1]]
        return self._ordered.pop(0)

    def get(self, _model: object, _key: object) -> object | None:
        return self._receipt

    def add(self, row: object) -> None:
        self.added.append(row)

    def flush(self) -> None:
        added = [row for row in self.added if isinstance(row, EnrollmentModel)]
        state = None if self.enrollment is None else self.enrollment.state
        self.log.append(f"flush(old={state},new_rows={len(added)})")

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


@pytest.fixture(autouse=True)
def _wiring(monkeypatch: pytest.MonkeyPatch) -> None:
    row = SimpleNamespace(class_id="class-a", role="teacher")
    monkeypatch.setattr(be1_registry, "require_assignment", lambda *_a, **_k: (row,))
    monkeypatch.setattr(be1_registry, "class_lock_select", lambda cid: ("lock", cid))
    monkeypatch.setattr(be1_registry, "_teacher_of_class", lambda *_a, **_k: True)
    monkeypatch.setattr(
        be1_registry, "_holds_unfinished_session_membership", lambda *_a, **_k: False
    )


def _db(
    *,
    source: SimpleNamespace | None = None,
    target: SimpleNamespace | None = None,
    profile: object | None = "default",
    enrollment: object | None = "default",
    receipt: object | None = None,
    source_known: object | None = "default",
    target_known: object | None = "default",
) -> FakeSession:
    source = source or _class("class-a")
    target = target or _class("class-b")
    profile_row = SimpleNamespace(class_id="class-a") if profile == "default" else profile
    enrollment_row = (
        SimpleNamespace(state="active", class_id="class-a")
        if enrollment == "default"
        else enrollment
    )
    ordered: list[object] = [
        source if source_known == "default" else source_known,
        "class-b" if target_known == "default" else target_known,
        profile_row,
        enrollment_row,
    ]
    db = FakeSession(ordered, {"class-a": source, "class-b": target}, receipt)
    db.enrollment = cast("SimpleNamespace | None", enrollment_row)
    return db


def _move(
    db: FakeSession,
    payload: MoveProfileRequest | None = None,
    *,
    if_match: str | None = '"1"',
    key: str = "synthetic-key",
    child_id: str = CHILD,
    class_id: str = "class-a",
) -> dict[str, object]:
    return be1_registry.move_profile(
        class_id,
        child_id,
        payload or _payload(),
        _request(key),
        key,
        if_match,
        PRINCIPAL,
        cast(Session, db),
    )


def _error(db: FakeSession, **kwargs: Any) -> HTTPException:
    with pytest.raises(HTTPException) as caught:
        _move(db, **kwargs)
    return caught.value


def _code(error: HTTPException) -> object:
    detail = cast("dict[str, Any]", error.detail)
    return detail["code"]


def _wrote_nothing(db: FakeSession) -> None:
    assert db.added == [] and db.commits == 0 and db.log == []


# ------------------------------------------------------------------------------ the schema
def test_schema_is_the_target_and_its_revision_only() -> None:
    assert set(MoveProfileRequest.model_fields) == {"target_class_id", "target_class_revision"}
    assert _payload().target_class_revision == 1


@pytest.mark.parametrize("revision", [0, -1])
def test_schema_refuses_a_revision_below_one(revision: int) -> None:
    with pytest.raises(ValidationError):
        _payload(target_class_revision=revision)


@pytest.mark.parametrize(
    "extra", ["class_id", "child_id", "state", "consent_id", "capacity", "enrollment_id"]
)
def test_schema_refuses_every_other_field(extra: str) -> None:
    with pytest.raises(ValidationError):
        MoveProfileRequest(target_class_id="class-b", target_class_revision=1, **{extra: "x"})


def test_schema_refuses_an_empty_or_overlong_target() -> None:
    for target in ("", "x" * 129):
        with pytest.raises(ValidationError):
            _payload(target_class_id=target)


# ------------------------------------------------------------------- receipt helpers
def test_receipt_scope_is_plain_when_it_fits_and_hashed_when_it_cannot() -> None:
    plain = be1_registry._move_receipt_scope("class-a", CHILD)
    assert plain == f"POST /classes/class-a/profiles/{CHILD}/move"
    long_scope = be1_registry._move_receipt_scope("a" * 128, "c" * 128)
    assert len(long_scope) <= 256 and "#" in long_scope
    other = be1_registry._move_receipt_scope("a" * 128, "d" * 128)
    assert other != long_scope  # the digest keeps the child in the scope


def test_fingerprint_is_stable_and_separates_every_input() -> None:
    base = be1_registry._move_fingerprint(
        class_id="class-a", child_id=CHILD, payload=_payload(), expected_revision=1
    )
    assert base == be1_registry._move_fingerprint(
        class_id="class-a", child_id=CHILD, payload=_payload(), expected_revision=1
    )
    variants = {
        be1_registry._move_fingerprint(
            class_id="class-x", child_id=CHILD, payload=_payload(), expected_revision=1
        ),
        be1_registry._move_fingerprint(
            class_id="class-a", child_id="other", payload=_payload(), expected_revision=1
        ),
        be1_registry._move_fingerprint(
            class_id="class-a",
            child_id=CHILD,
            payload=_payload(target_class_id="class-c"),
            expected_revision=1,
        ),
        be1_registry._move_fingerprint(
            class_id="class-a",
            child_id=CHILD,
            payload=_payload(target_class_revision=2),
            expected_revision=1,
        ),
        be1_registry._move_fingerprint(
            class_id="class-a", child_id=CHILD, payload=_payload(), expected_revision=2
        ),
    }
    assert base not in variants and len(variants) == 5


def test_body_holds_references_and_two_revisions_only() -> None:
    body = be1_registry._move_body(
        child_id=CHILD,
        from_class_id="class-a",
        to_class_id="class-b",
        enrollment_id="e-1",
        from_class_revision=2,
        to_class_revision=3,
    )
    assert set(body) == {
        "contract",
        "child_id",
        "from_class_id",
        "to_class_id",
        "enrollment_id",
        "from_class_revision",
        "to_class_revision",
    }
    assert body["contract"] == "Be1ProfileMoveV1"


# ------------------------------------------------------------------------------ the success
def test_success_closes_then_opens_projects_bumps_both_and_stores_references() -> None:
    db = _db(source=_class("class-a", revision=4), target=_class("class-b", revision=7))
    body = _move(db, _payload(target_class_revision=7), if_match='"4"')
    assert db.locks == ["class-a", "class-b"]
    assert db.commits == 1
    assert db._ordered == []  # every planned read happened
    # the old enrollment is flushed as withdrawn BEFORE the new row is added
    assert db.log == ["flush(old=withdrawn,new_rows=0)"]
    enrollments = [row for row in db.added if isinstance(row, EnrollmentModel)]
    assert len(enrollments) == 1
    assert (enrollments[0].class_id, enrollments[0].child_id, enrollments[0].organization_id) == (
        "class-b",
        CHILD,
        ORG,
    )
    assert enrollments[0].created_by == PRINCIPAL.subject
    assert body == {
        "contract": "Be1ProfileMoveV1",
        "child_id": CHILD,
        "from_class_id": "class-a",
        "to_class_id": "class-b",
        "enrollment_id": enrollments[0].enrollment_id,
        "from_class_revision": 5,
        "to_class_revision": 8,
    }
    audit = [row for row in db.added if isinstance(row, CoreAuditEntryModel)]
    assert [(a.action, a.resource_type, a.resource_id, a.decision) for a in audit] == [
        ("profile.move", "child_profile", CHILD, "allowed")
    ]
    events = [row for row in db.added if isinstance(row, CoreOutboxEventModel)]
    assert len(events) == 1 and events[0].event_type == "be1.profile.moved.v1"
    assert events[0].aggregate_id == CHILD
    assert events[0].payload == {
        "child_id": CHILD,
        "from_class_id": "class-a",
        "to_class_id": "class-b",
    }
    receipts = [row for row in db.added if isinstance(row, Be1CommandReceiptModel)]
    assert len(receipts) == 1
    assert receipts[0].operation_scope == f"POST /classes/class-a/profiles/{CHILD}/move"
    assert receipts[0].response_json == body


def test_success_projects_the_target_class_on_the_profile_row() -> None:
    profile = SimpleNamespace(class_id="class-a")
    db = _db(profile=profile)
    _move(db)
    assert profile.class_id == "class-b"


def test_the_class_rows_are_locked_in_ascending_order_whichever_way_the_move_goes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # B -> A: the target id sorts first, so it is locked first.
    row = SimpleNamespace(class_id="class-b", role="teacher")
    monkeypatch.setattr(be1_registry, "require_assignment", lambda *_a, **_k: (row,))
    source, target = _class("class-b"), _class("class-a")
    db = FakeSession(
        [source, "class-a", SimpleNamespace(class_id="class-b"), SimpleNamespace(state="active")],
        {"class-a": target, "class-b": source},
    )
    be1_registry.move_profile(
        "class-b",
        CHILD,
        _payload(target_class_id="class-a"),
        _request(),
        "synthetic-key",
        '"1"',
        PRINCIPAL,
        cast(Session, db),
    )
    assert db.locks == ["class-a", "class-b"]


# ------------------------------------------------------------------------- order and failure
def test_a_missing_source_class_is_404_before_the_scope_guard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def never(*_a: object, **_k: object) -> None:
        raise AssertionError("the scope guard must come after the class lookup")

    monkeypatch.setattr(be1_registry, "require_assignment", never)
    error = _error(_db(source_known=None))
    assert error.status_code == 404 and _code(error) == "RESOURCE_NOT_FOUND"


def test_the_role_refusal_of_the_helper_passes_through_as_403(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def refuse(*_a: object, **_k: object) -> None:
        raise failure(403, "ACTION_NOT_ALLOWED", "no")

    monkeypatch.setattr(be1_registry, "require_assignment", refuse)
    db = _db()
    error = _error(db)
    assert error.status_code == 403 and _code(error) == "ACTION_NOT_ALLOWED"
    _wrote_nothing(db)


def test_a_teacher_row_of_another_class_is_the_uniform_404(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    other = SimpleNamespace(class_id="class-z", role="teacher")
    monkeypatch.setattr(be1_registry, "require_assignment", lambda *_a, **_k: (other,))
    error = _error(_db())
    assert error.status_code == 404 and _code(error) == "RESOURCE_NOT_FOUND"


def test_an_organization_wide_teacher_row_is_the_uniform_404(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    org_wide = SimpleNamespace(class_id=None, role="teacher")
    monkeypatch.setattr(be1_registry, "require_assignment", lambda *_a, **_k: (org_wide,))
    error = _error(_db())
    assert error.status_code == 404 and _code(error) == "RESOURCE_NOT_FOUND"


def test_moving_into_the_same_class_is_400_before_the_target_lookup() -> None:
    db = _db()
    error = _error(db, payload=_payload(target_class_id="class-a"))
    assert error.status_code == 400
    assert cast("dict[str, Any]", error.detail)["field_errors"] == [
        {"field": "target_class_id", "code": "INVALID_FORMAT"}
    ]
    assert len(db._ordered) == 3  # only the source class was read
    _wrote_nothing(db)


def test_an_unknown_or_foreign_target_class_is_the_same_404() -> None:
    db = _db(target_known=None)
    error = _error(db)
    assert error.status_code == 404 and _code(error) == "RESOURCE_NOT_FOUND"
    _wrote_nothing(db)


def test_a_target_class_the_teacher_does_not_teach_is_the_same_404(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(be1_registry, "_teacher_of_class", lambda *_a, **_k: False)
    db = _db()
    error = _error(db)
    assert error.status_code == 404 and _code(error) == "RESOURCE_NOT_FOUND"
    assert db.locks == []  # nothing is locked for a stranger
    _wrote_nothing(db)


def test_a_missing_or_malformed_if_match_is_400() -> None:
    cases = ((None, "REQUIRED"), ('"0"', "INVALID_FORMAT"), ('W/"1"', "INVALID_FORMAT"))
    for header, code in cases:
        error = _error(_db(), if_match=header)
        assert error.status_code == 400
        assert cast("dict[str, Any]", error.detail)["field_errors"] == [
            {"field": "If-Match", "code": code}
        ]


def test_replay_returns_the_stored_body_before_the_stale_checks() -> None:
    stored = be1_registry._move_body(
        child_id=CHILD,
        from_class_id="class-a",
        to_class_id="class-b",
        enrollment_id="e-1",
        from_class_revision=2,
        to_class_revision=3,
    )
    fingerprint = be1_registry._move_fingerprint(
        class_id="class-a", child_id=CHILD, payload=_payload(), expected_revision=1
    )
    receipt = SimpleNamespace(request_fingerprint=fingerprint, response_json=stored)
    # the classes carry other revisions now: a replay must not be stale
    db = _db(
        source=_class("class-a", revision=9), target=_class("class-b", revision=9), receipt=receipt
    )
    assert _move(db) == stored
    assert db.commits == 0 and db.rollbacks == 1


def test_the_same_key_with_another_request_is_400_invalid_idempotency_key() -> None:
    receipt = SimpleNamespace(request_fingerprint="0" * 64, response_json={})
    db = _db(receipt=receipt)
    error = _error(db)
    assert error.status_code == 400 and _code(error) == "INVALID_IDEMPOTENCY_KEY"
    _wrote_nothing(db)


def test_a_stale_source_is_409_with_the_current_version_and_writes_nothing() -> None:
    db = _db(source=_class("class-a", revision=3))
    error = _error(db)
    assert error.status_code == 409 and _code(error) == "STALE_REVISION"
    assert cast("dict[str, Any]", error.detail)["current_version"] == 3
    assert error.headers == {"ETag": '"3"'}
    _wrote_nothing(db)


def test_the_source_is_checked_before_the_target() -> None:
    db = _db(source=_class("class-a", revision=3), target=_class("class-b", revision=9))
    error = _error(db)
    assert cast("dict[str, Any]", error.detail)["current_version"] == 3


def test_a_stale_target_is_409_with_the_target_version() -> None:
    db = _db(target=_class("class-b", revision=5))
    error = _error(db)
    assert error.status_code == 409 and _code(error) == "STALE_REVISION"
    assert cast("dict[str, Any]", error.detail)["current_version"] == 5
    assert error.headers == {"ETag": '"5"'}
    _wrote_nothing(db)


@pytest.mark.parametrize("which", ["source", "target"])
@pytest.mark.parametrize("state", ["suspended", "archived"])
def test_a_read_only_class_on_either_side_is_409_after_the_stale_checks(
    which: str, state: str
) -> None:
    source = _class("class-a", state=state if which == "source" else "active")
    target = _class("class-b", state=state if which == "target" else "active")
    db = _db(source=source, target=target)
    error = _error(db)
    assert error.status_code == 409 and _code(error) == "INVALID_STATE_TRANSITION"
    _wrote_nothing(db)
    # stale revisions are reported before the state
    stale = _db(
        source=_class("class-a", revision=2, state=state), target=_class("class-b", state=state)
    )
    assert _code(_error(stale)) == "STALE_REVISION"


def test_an_unknown_child_or_a_child_of_another_class_is_404_profile_not_found() -> None:
    db = _db(profile=None)
    error = _error(db)
    assert error.status_code == 404 and _code(error) == "PROFILE_NOT_FOUND"
    _wrote_nothing(db)


def test_a_profile_without_an_active_enrollment_is_409_and_is_not_auto_enrolled() -> None:
    db = _db(enrollment=None)
    error = _error(db)
    assert error.status_code == 409 and _code(error) == "INVALID_STATE_TRANSITION"
    _wrote_nothing(db)


def test_a_child_in_an_unfinished_session_is_409(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        be1_registry, "_holds_unfinished_session_membership", lambda *_a, **_k: True
    )
    enrollment = SimpleNamespace(state="active", class_id="class-a")
    db = _db(enrollment=enrollment)
    error = _error(db)
    assert error.status_code == 409 and _code(error) == "INVALID_STATE_TRANSITION"
    assert enrollment.state == "active"  # nothing was closed
    _wrote_nothing(db)


def test_the_handler_has_no_capacity_quota_or_billing_code() -> None:
    source = inspect.getsource(be1_registry.move_profile).lower()
    for banned in ("capacity", "quota", "billing", "subscription", "payment"):
        assert banned not in source
