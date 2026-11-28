from types import SimpleNamespace
from typing import cast

import pytest
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.persistence.be1_models import ConsentRecordModel, EnrollmentModel
from sketch2life.interfaces.http.routers import be1_registry as routes

PRINCIPAL = VerifiedPrincipal(subject="manager", issuer="test", roles=frozenset(), token_id="t")


class FakeDB:
    def __init__(self, values, receipt=None):
        self.values = iter(values)
        self.receipt = receipt
        self.added = []
        self.commits = 0

    def scalar(self, statement):
        return next(self.values)

    def get(self, model, key):
        return self.receipt

    def add(self, row):
        self.added.append(row)

    def rollback(self):
        pass

    def commit(self):
        self.commits += 1


@pytest.fixture(autouse=True)
def wiring(monkeypatch):
    monkeypatch.setattr(routes, "_require_m2_assignment", lambda *a, **k: ())
    monkeypatch.setattr(routes, "settle_due_class_suspensions", lambda *a, **k: None)
    monkeypatch.setattr(routes, "require_no_pending_class_transfer", lambda *a, **k: None)
    monkeypatch.setattr(routes, "class_lock_select", lambda cid: cid)


def call(db, revision='"1"'):
    request = Request({"type": "http", "headers": [(b"idempotency-key", b"key")]})
    return routes.place_profile(
        "class", "child", request, "key", revision, PRINCIPAL, cast(Session, db)
    )


def setup(profile=True, enrollment=None, pending=False, revision=1):
    classroom = SimpleNamespace(organization_id="org", revision=revision, state="active")
    child = (
        SimpleNamespace(child_id="child", class_id="old", organization_id="org")
        if profile
        else None
    )
    return FakeDB([classroom, classroom, child, enrollment, pending]), classroom, child


def test_place_creates_enrollment_and_no_consent():
    db, classroom, child = setup()
    body = call(db)
    assert body["contract"] == "Be1ProfilePlacementV1"
    assert body["class_revision"] == 2 and child.class_id == "class"
    assert sum(isinstance(row, EnrollmentModel) for row in db.added) == 1
    assert not any(isinstance(row, ConsentRecordModel) for row in db.added)
    assert db.commits == 1


@pytest.mark.parametrize(
    "kwargs,status,code",
    [
        ({"profile": False}, 404, "PROFILE_NOT_FOUND"),
        ({"enrollment": object()}, 409, "INVALID_STATE_TRANSITION"),
        ({"pending": True}, 409, "INVALID_STATE_TRANSITION"),
        ({"revision": 2}, 409, "STALE_REVISION"),
    ],
)
def test_refusals(kwargs, status, code):
    db, _, _ = setup(**kwargs)
    with pytest.raises(HTTPException) as caught:
        call(db)
    assert caught.value.status_code == status
    assert caught.value.detail["code"] == code
    assert not db.added and not db.commits


def test_replay_precedes_revision_check():
    db, _, _ = setup(revision=2)
    body = {
        "contract": "Be1ProfilePlacementV1",
        "child_id": "child",
        "class_id": "class",
        "enrollment_id": "enrollment",
        "class_revision": 2,
    }
    db.receipt = SimpleNamespace(
        request_fingerprint=routes._place_fingerprint("class", "child", 1), response_json=body
    )
    assert call(db) == body
    assert not db.added


def test_list_query_quarantines_pending_and_active_enrollments():
    from unittest.mock import Mock

    from sqlalchemy.dialects import postgresql

    db = Mock()
    db.execute.return_value.all.return_value = []
    assert routes.list_unplaced_profile_refs("org", 10, None, PRINCIPAL, cast(Session, db)) == {
        "contract": "Be1UnplacedProfileRefListV1",
        "items": [],
        "next_cursor": None,
    }
    sql = str(db.execute.call_args.args[0].compile(dialect=postgresql.dialect())).lower()
    assert sql.count("not (exists") == 2
    assert "request_type" in sql and "target_ref" in sql and "be1_enrollments" in sql


def test_list_returns_only_opaque_refs_and_binds_cursor(monkeypatch):
    from datetime import UTC, datetime
    from unittest.mock import Mock

    db = Mock()
    db.execute.return_value.all.return_value = [
        SimpleNamespace(child_id="opaque", created_at=datetime(2026, 1, 1, tzinfo=UTC))
    ]
    scopes = []
    monkeypatch.setattr(
        routes,
        "decode_time_cursor",
        lambda cursor, *, scope: (
            scopes.append(scope) or datetime(2025, 1, 1, tzinfo=UTC),
            "previous",
        ),
    )
    body = routes.list_unplaced_profile_refs("org", 10, "cursor", PRINCIPAL, cast(Session, db))
    assert body["items"] == [{"child_id": "opaque"}]
    assert scopes == ["be1.unplaced-profile-refs:org"]


def test_concurrent_unique_conflict_is_rolled_back():
    from sqlalchemy.exc import IntegrityError

    db, _, _ = setup()

    def fail_commit():
        raise IntegrityError("insert", {}, Exception("unique"))

    db.commit = fail_commit
    with pytest.raises(HTTPException) as caught:
        call(db)
    assert caught.value.status_code == 409
    assert caught.value.detail["code"] == "RESOURCE_CONFLICT"
