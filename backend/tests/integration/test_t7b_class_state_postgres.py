"""FEAT-066 T-7b: class archive, manual suspend, state filter and class revision on PostgreSQL.

SRS l.593 and l.1425 and l.1461 (a suspended class is read-only), l.1709 (the School Manager
archives and suspends a class), l.1651 and l.1699 (expected class revision, STALE_REVISION),
l.1697 (keyed commands), l.864-865 (403 only inside a known scope), l.1640 (cursor lists), l.1708
(a Teacher lists only assigned classes). Runs only against a disposable database whose name
contains ``be1_acceptance``. Principals are injected through the ``X-Test-Principal`` header; every
identity, class and text is synthetic. The database-level checks of the migration
``20261120_cls_0001`` (column, default, CHECK) are here too; the downgrade guard and the round trip
are run with alembic against separate databases (see the evidence note).
"""

from __future__ import annotations

import hashlib
import os
import time
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from threading import Barrier
from typing import Any
from uuid import uuid4

import pytest
from fastapi import FastAPI, Header
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text, update
from sqlalchemy.exc import IntegrityError

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.lesson_occurrences.tables import (
    DOCUMENT_REVISIONS,
    PLAN_REVISIONS,
    SOURCE_DOCUMENTS,
)
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    Be1CommandReceiptModel,
    ClassroomModel,
    ClassroomSessionModel,
    ConsentRecordModel,
    ManagedProfileModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.infrastructure.persistence.core_models import (
    CoreAuditEntryModel,
    CoreOutboxEventModel,
)
from sketch2life.interfaces.http.api_conventions import encode_cursor
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult

ISSUER = "synthetic-t7b-issuer"
BASE_TIME = datetime(2026, 3, 1, 8, 0, 0, tzinfo=UTC)
FIRST_TEXT = "Tiêu đề: Vẽ con mèo\nMục tiêu: Nhận biết hình dạng con mèo"
PURPOSE = "classroom-learning-v1"


@dataclass
class Api:
    app: FastAPI
    client: TestClient
    token: str
    organization: str
    foreign_organization: str
    subjects: dict[str, str] = field(default_factory=dict)
    accounts: dict[str, str] = field(default_factory=dict)
    clock: int = 0

    def factory(self) -> Any:
        return self.app.state.be1_runtime.session_factory

    def base(self, suffix: str = "") -> str:
        return f"/api/be1/v1/organizations/{self.organization}{suffix}"


def _identity(db: Any, subject: str, role: str) -> str:
    row = AdultIdentityModel(subject=subject, issuer=ISSUER, state="active", account_role=role)
    db.add(row)
    db.flush()
    return row.account_id


def _assign(db: Any, organization: str, subject: str, role: str, class_id: str | None) -> None:
    db.add(
        OrganizationAssignmentModel(
            assignment_id=str(uuid4()),
            organization_id=organization,
            subject=subject,
            class_id=class_id,
            role=role,
            active=True,
        )
    )


@pytest.fixture
def api(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> Iterator[Api]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL to a disposable PostgreSQL database")
    if "be1_acceptance" not in database_url.rsplit("/", 1)[-1]:
        pytest.fail("BE1_TEST_DATABASE_URL must point to a disposable *be1_acceptance database")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", database_url)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "development")
    monkeypatch.setenv("SKETCH2LIFE_AI_PROVIDER", "disabled")
    monkeypatch.setenv("SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED", "true")
    monkeypatch.setenv("SKETCH2LIFE_ROOM_CODE_HMAC_KEY", "synthetic-test-key-" + "x" * 40)
    monkeypatch.setenv("SKETCH2LIFE_BE1_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.delenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", raising=False)
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    app = create_app()
    runtime = app.state.be1_runtime
    if runtime.engine is None or runtime.session_factory is None:
        pytest.fail("PostgreSQL runtime did not initialize")
    token = uuid4().hex[:8]
    organization, foreign = f"synthetic-t7b-org-{token}", f"synthetic-t7b-foreign-{token}"
    d = Api(app, TestClient(app), token, organization, foreign)

    def label(value: str) -> str:
        return f"synthetic-t7b-{value}-{token}"

    with runtime.session_factory.begin() as db:
        for org in (organization, foreign):
            db.add(OrganizationModel(organization_id=org, display_name=org, state="active"))
        db.flush()
        people: tuple[tuple[str, str, str | None, str | None], ...] = (
            # label, account role, organization, assignment role (None = no row)
            ("manager", "school_manager", organization, "school_admin"),
            ("manager2", "school_manager", organization, "school_admin"),
            ("fmanager", "school_manager", foreign, "school_admin"),
            ("orgt", "teacher", organization, "teacher"),  # an organization-wide Teacher row
            ("cand", "teacher", organization, "teacher"),  # the assignment candidate
            ("parent", "parent", None, None),
            ("platform", "platform_admin", None, None),
        )
        for key, role, home, assignment_role in people:
            d.subjects[key] = label(key)
            d.accounts[key] = _identity(db, label(key), role)
            if home is not None and assignment_role is not None:
                _assign(db, home, label(key), assignment_role, None)

    async def verified(
        x_test_principal: str = Header(alias="X-Test-Principal"),
    ) -> VerifiedPrincipal:
        return VerifiedPrincipal(subject=x_test_principal, issuer=ISSUER, roles=frozenset())

    app.dependency_overrides[get_verified_adult] = verified
    try:
        with d.client:
            yield d
    finally:
        app.dependency_overrides.clear()
        runtime.engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


# ----------------------------------------------------------------------------- helpers
def hdr(d: Api, who: str, key: str | None = None, **extra: str) -> dict[str, str]:
    result = {"X-Test-Principal": d.subjects[who]}
    if key is not None:
        result["Idempotency-Key"] = key
    result.update(extra)
    return result


def shape(response: Any) -> tuple[int, dict[str, Any]]:
    body = dict(response.json())
    body.pop("request_id", None)
    body.pop("correlation_id", None)
    return response.status_code, body


def new_class(
    d: Api,
    *,
    state: str = "active",
    teachers: tuple[str, ...] = (),
    guides: tuple[str, ...] = (),
    organization: str | None = None,
) -> str:
    """A class row in ``state`` with a distinct, increasing ``created_at``."""
    d.clock += 1
    class_id = f"synthetic-t7b-class-{uuid4().hex[:12]}"
    with d.factory().begin() as db:
        db.add(
            ClassroomModel(
                class_id=class_id,
                organization_id=organization or d.organization,
                display_name=f"Synthetic {class_id}"[:200],
                state=state,
                created_by="synthetic-t7b-seed",
                created_at=BASE_TIME + timedelta(seconds=d.clock),
            )
        )
        db.flush()
        for who in teachers:
            _assign(db, d.organization, d.subjects[who], "teacher", class_id)
        for who in guides:
            _assign(db, d.organization, d.subjects[who], "guide", class_id)
    return class_id


def add_teacher(d: Api, key: str, class_id: str, *, role: str = "teacher") -> None:
    subject = f"synthetic-t7b-{key}-{d.token}"
    d.subjects[key] = subject
    with d.factory().begin() as db:
        d.accounts[key] = _identity(db, subject, "teacher")
        _assign(db, d.organization, subject, role, class_id)


def command(
    d: Api,
    who: str,
    class_id: str,
    name: str,
    *,
    if_match: str | None = '"1"',
    key: str | None = None,
) -> Any:
    extra = {} if if_match is None else {"If-Match": if_match}
    return d.client.post(
        f"/api/be1/v1/classes/{class_id}/{name}",
        headers=hdr(d, who, uuid4().hex if key is None else key, **extra),
    )


def class_row(d: Api, class_id: str) -> tuple[str, int]:
    with d.factory()() as db:
        row = db.execute(
            select(ClassroomModel.state, ClassroomModel.revision).where(
                ClassroomModel.class_id == class_id
            )
        ).one()
    return str(row[0]), int(row[1])


def audits(d: Api, class_id: str, action: str) -> int:
    with d.factory()() as db:
        return int(
            db.scalar(
                select(func.count())
                .select_from(CoreAuditEntryModel)
                .where(
                    CoreAuditEntryModel.resource_id == class_id,
                    CoreAuditEntryModel.action == action,
                )
            )
            or 0
        )


def outbox(d: Api, class_id: str, event_type: str | None = None) -> list[Any]:
    with d.factory()() as db:
        statement = select(CoreOutboxEventModel).where(
            CoreOutboxEventModel.aggregate_id == class_id
        )
        if event_type is not None:
            statement = statement.where(CoreOutboxEventModel.event_type == event_type)
        return list(db.scalars(statement.order_by(CoreOutboxEventModel.aggregate_revision)))


def receipts(d: Api, class_id: str, name: str) -> list[Any]:
    with d.factory()() as db:
        return list(
            db.scalars(
                select(Be1CommandReceiptModel).where(
                    Be1CommandReceiptModel.operation_scope == f"POST /classes/{class_id}/{name}"
                )
            )
        )


def listing(d: Api, who: str, **params: Any) -> Any:
    return d.client.get(d.base("/classes"), params=params or None, headers=hdr(d, who))


def listed(d: Api, who: str, **params: Any) -> dict[str, dict[str, Any]]:
    response = listing(d, who, **params)
    assert response.status_code == 200, response.text
    return {item["class_id"]: item for item in response.json()["items"]}


# ----------------------------------------------------------------------------- the two commands
def test_suspend_then_archive_move_the_state_and_the_revision_with_etags(api: Api) -> None:
    d = api
    class_id = new_class(d)
    suspended = command(d, "manager", class_id, "suspend", if_match='"1"')
    assert suspended.status_code == 200, suspended.text
    assert suspended.json() == {
        "contract": "Be1ClassStateV1",
        "class_id": class_id,
        "state": "suspended",
        "class_revision": 2,
    }
    assert suspended.headers["ETag"] == '"2"'
    assert class_row(d, class_id) == ("suspended", 2)

    archived = command(d, "manager2", class_id, "archive", if_match='"2"')
    assert archived.status_code == 200, archived.text
    assert archived.json()["state"] == "archived" and archived.json()["class_revision"] == 3
    assert archived.headers["ETag"] == '"3"'
    assert class_row(d, class_id) == ("archived", 3)

    # An active class can be archived directly.
    direct = new_class(d)
    done = command(d, "manager", direct, "archive", if_match='"1"')
    assert done.status_code == 200 and done.json()["state"] == "archived"


def test_each_command_writes_one_audit_row_one_event_and_one_receipt(api: Api) -> None:
    d = api
    class_id = new_class(d)
    assert command(d, "manager", class_id, "suspend", if_match='"1"').status_code == 200
    assert command(d, "manager", class_id, "archive", if_match='"2"').status_code == 200
    assert audits(d, class_id, "class.suspend") == 1 and audits(d, class_id, "class.archive") == 1
    events = outbox(d, class_id)
    assert [e.event_type for e in events] == ["be1.class.suspended.v1", "be1.class.archived.v1"]
    assert [e.aggregate_revision for e in events] == [2, 3]
    assert events[0].payload == {
        "class_id": class_id,
        "from_state": "active",
        "to_state": "suspended",
    }
    assert events[1].payload["from_state"] == "suspended"
    for name in ("suspend", "archive"):
        (receipt,) = receipts(d, class_id, name)
        assert receipt.organization_id == d.organization
        # The receipt holds the class id, the state and the revision only (receipt rule).
        assert set(receipt.response_json) == {"contract", "class_id", "state", "class_revision"}


def test_a_replay_returns_the_first_answer_and_writes_nothing_more(api: Api) -> None:
    d = api
    class_id = new_class(d)
    first = command(d, "manager", class_id, "suspend", if_match='"1"', key="k-replay")
    again = command(d, "manager", class_id, "suspend", if_match='"1"', key="k-replay")
    assert first.status_code == again.status_code == 200
    assert shape(first) == shape(again)
    assert again.headers["ETag"] == '"2"'
    assert class_row(d, class_id) == ("suspended", 2)
    assert audits(d, class_id, "class.suspend") == 1
    assert len(outbox(d, class_id, "be1.class.suspended.v1")) == 1
    assert len(receipts(d, class_id, "suspend")) == 1
    # The key is per operation: the same key on the archive command is a new command.
    other = command(d, "manager", class_id, "archive", if_match='"2"', key="k-replay")
    assert other.status_code == 200 and other.json()["state"] == "archived"
    # A replay of the first command still answers its first body after the class moved on.
    late = command(d, "manager", class_id, "suspend", if_match='"1"', key="k-replay")
    assert shape(late) == shape(first)


def test_the_same_key_with_another_if_match_is_a_400_and_writes_nothing(api: Api) -> None:
    d = api
    class_id = new_class(d)
    first = command(d, "manager", class_id, "suspend", if_match='"1"', key="k-one")
    assert first.status_code == 200
    clash = command(d, "manager", class_id, "suspend", if_match='"2"', key="k-one")
    assert clash.status_code == 400 and clash.json()["code"] == "INVALID_IDEMPOTENCY_KEY"
    assert class_row(d, class_id) == ("suspended", 2)


def test_two_requests_with_one_key_make_one_transition(api: Api) -> None:
    d = api
    class_id = new_class(d)
    barrier = Barrier(2)

    def attempt(_: int) -> tuple[int, dict[str, Any]]:
        barrier.wait()
        return shape(command(d, "manager", class_id, "suspend", if_match='"1"', key="k-twin"))

    with ThreadPoolExecutor(max_workers=2) as pool:
        first, second = list(pool.map(attempt, range(2)))
    assert first == second and first[0] == 200
    assert class_row(d, class_id) == ("suspended", 2)
    assert audits(d, class_id, "class.suspend") == 1 and len(receipts(d, class_id, "suspend")) == 1


def test_two_keys_at_one_revision_make_one_200_and_one_stale_409(api: Api) -> None:
    d = api
    class_id = new_class(d)
    barrier = Barrier(2)

    def attempt(index: int) -> tuple[int, dict[str, Any]]:
        barrier.wait()
        return shape(
            command(d, "manager", class_id, "suspend", if_match='"1"', key=f"k-{index}")
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt, (1, 2)))
    assert sorted(status for status, _ in results) == [200, 409], results
    loser = next(body for status, body in results if status == 409)
    assert loser["code"] == "STALE_REVISION" and loser["current_version"] == 2
    assert class_row(d, class_id) == ("suspended", 2)
    assert audits(d, class_id, "class.suspend") == 1


def test_a_stale_revision_is_409_with_the_current_version_and_etag(api: Api) -> None:
    d = api
    class_id = new_class(d)
    stale = command(d, "manager", class_id, "suspend", if_match='"7"')
    assert stale.status_code == 409 and stale.json()["code"] == "STALE_REVISION"
    assert stale.json()["current_version"] == 1 and stale.headers["ETag"] == '"1"'
    assert class_row(d, class_id) == ("active", 1)
    for bad in (None, "1", 'W/"1"', '"0"', '"x"'):
        response = command(d, "manager", class_id, "suspend", if_match=bad)
        assert response.status_code == 400, (bad, response.text)
    missing_key = d.client.post(
        f"/api/be1/v1/classes/{class_id}/suspend",
        headers={"X-Test-Principal": d.subjects["manager"], "If-Match": '"1"'},
    )
    assert missing_key.status_code == 400
    assert class_row(d, class_id) == ("active", 1)


@pytest.mark.parametrize(
    ("name", "state"),
    [("suspend", "suspended"), ("suspend", "archived"), ("archive", "archived")],
)
def test_every_refused_pair_is_409_and_changes_nothing(api: Api, name: str, state: str) -> None:
    d = api
    class_id = new_class(d, state=state)
    refused = command(d, "manager", class_id, name, if_match='"1"')
    assert refused.status_code == 409 and refused.json()["code"] == "INVALID_STATE_TRANSITION"
    assert class_row(d, class_id) == (state, 1)
    assert audits(d, class_id, f"class.{name}") == 0 and receipts(d, class_id, name) == []


def test_stale_is_decided_before_the_transition(api: Api) -> None:
    d = api
    class_id = new_class(d, state="archived")
    response = command(d, "manager", class_id, "suspend", if_match='"5"')
    assert response.status_code == 409 and response.json()["code"] == "STALE_REVISION"


def test_there_is_no_route_back_from_suspended_or_archived(api: Api) -> None:
    d = api
    class_id = new_class(d, state="suspended")
    for name in ("reactivate", "activate", "unarchive", "unsuspend", "restore"):
        response = d.client.post(
            f"/api/be1/v1/classes/{class_id}/{name}",
            headers=hdr(d, "manager", uuid4().hex, **{"If-Match": '"1"'}),
        )
        assert response.status_code in (404, 405), name
    assert class_row(d, class_id) == ("suspended", 1)


# ----------------------------------------------------------------------------- who may do it
def test_scope_answers_404_before_403_and_with_one_body(api: Api) -> None:
    d = api
    class_id = new_class(d, teachers=("orgt",))  # orgt also holds an organization-wide row
    add_teacher(d, "t1", class_id)
    add_teacher(d, "g1", class_id, role="guide")
    other = new_class(d)
    add_teacher(d, "tb", other)
    unknown = command(d, "manager", f"synthetic-t7b-missing-{uuid4().hex[:8]}", "suspend")
    assert unknown.status_code == 404 and unknown.json()["code"] == "RESOURCE_NOT_FOUND"
    # Teacher of another class, Parent, Platform Admin, a Manager of another organization and a
    # Teacher asking for an unknown class all look exactly like an unknown class.
    for who in ("tb", "parent", "platform", "fmanager"):
        assert shape(command(d, who, class_id, "suspend")) == shape(unknown), who
    assert shape(command(d, "t1", f"synthetic-t7b-missing-{uuid4().hex[:8]}", "suspend")) == shape(
        unknown
    )
    # A Teacher account assigned in this organization (class row, organization-wide row, guide) is
    # told the action is not allowed: the resource is known (SRS l.864-865).
    for who in ("t1", "orgt", "g1"):
        refused = command(d, who, class_id, "archive")
        assert refused.status_code == 403, (who, refused.text)
        assert refused.json()["code"] == "ACTION_NOT_ALLOWED"
    assert class_row(d, class_id) == ("active", 1)
    # Neither command leaks a name, an age, a child reference or a count.
    ok = command(d, "manager", class_id, "suspend")
    assert set(ok.json()) == {"contract", "class_id", "state", "class_revision"}


# ----------------------------------------------------------------------------- list and filter
def test_the_manager_filters_by_state_and_the_default_is_active(api: Api) -> None:
    d = api
    active = new_class(d)
    suspended = new_class(d, state="suspended")
    archived = new_class(d, state="archived")
    assert set(listed(d, "manager")) == {active}
    assert set(listed(d, "manager", state="active")) == {active}
    assert set(listed(d, "manager", state="suspended")) == {suspended}
    assert set(listed(d, "manager", state="archived")) == {archived}
    everything = listed(d, "manager", state="all")
    assert set(everything) == {active, suspended, archived}
    assert everything[suspended]["state"] == "suspended"
    assert everything[active]["class_revision"] == 1
    assert {"class_revision", "assignment_revision", "has_active_teacher"} <= set(
        everything[active]
    )
    bad = listing(d, "manager", state="deleted")
    assert bad.status_code == 400 and bad.json()["code"] == "INVALID_REQUEST"
    assert listing(d, "manager", state="ACTIVE").status_code == 400


def test_the_list_reports_the_class_revision_after_each_change(api: Api) -> None:
    d = api
    class_id = new_class(d)
    assert listed(d, "manager")[class_id]["class_revision"] == 1
    command(d, "manager", class_id, "suspend", if_match='"1"')
    assert listed(d, "manager", state="suspended")[class_id]["class_revision"] == 2
    command(d, "manager", class_id, "archive", if_match='"2"')
    assert listed(d, "manager", state="archived")[class_id]["class_revision"] == 3


def test_a_teacher_lists_assigned_classes_in_active_and_suspended_only(api: Api) -> None:
    d = api
    active = new_class(d)
    suspended = new_class(d, state="suspended")
    archived = new_class(d, state="archived")
    unassigned = new_class(d)
    add_teacher(d, "t1", active)
    with d.factory().begin() as db:
        for class_id in (suspended, archived):
            _assign(db, d.organization, d.subjects["t1"], "teacher", class_id)
    assert set(listed(d, "t1")) == {active}
    assert set(listed(d, "t1", state="suspended")) == {suspended}
    # `archived` alone is an empty page; `all` means the two states a Teacher can see.
    assert listed(d, "t1", state="archived") == {}
    assert set(listed(d, "t1", state="all")) == {active, suspended}
    assert unassigned not in listed(d, "t1", state="all")


def test_an_organization_wide_teacher_row_no_longer_lists_every_class(api: Api) -> None:
    d = api
    new_class(d)
    new_class(d, state="suspended")
    page = listing(d, "orgt", state="all")
    assert page.status_code == 200, page.text
    assert page.json()["items"] == [] and page.json()["next_cursor"] is None
    # A class-scoped guide row lists exactly its class.
    mine = new_class(d)
    add_teacher(d, "g2", mine, role="guide")
    assert set(listed(d, "g2")) == {mine}
    assert listing(d, "fmanager").status_code == 404
    assert listing(d, "parent").status_code == 404


def test_a_cursor_belongs_to_one_state_filter(api: Api) -> None:
    d = api
    for _ in range(3):
        new_class(d)
        new_class(d, state="suspended")
    first = listing(d, "manager", state="all", limit=2).json()
    assert first["next_cursor"] is not None
    follow = listing(d, "manager", state="all", limit=2, cursor=first["next_cursor"])
    assert follow.status_code == 200, follow.text
    for other in ("active", "suspended", "archived"):
        moved = listing(d, "manager", state=other, cursor=first["next_cursor"])
        assert moved.status_code == 400, other
        assert moved.json()["field_errors"] == [{"field": "cursor", "code": "INVALID_FORMAT"}]
    # A cursor of the pre-T-7b shape (no state in the scope) is refused too.
    old_scope = f"be1.classes:{d.organization}"
    crafted = encode_cursor(
        scope=old_scope, sort_key=BASE_TIME.isoformat(), item_id="synthetic-t7b-x"
    )
    assert listing(d, "manager", cursor=crafted).status_code == 400
    # Walking one filter to its end sees every class once.
    seen: list[str] = []
    cursor: str | None = None
    while True:
        params: dict[str, Any] = {"state": "all", "limit": 2}
        if cursor is not None:
            params["cursor"] = cursor
        page = listing(d, "manager", **params).json()
        seen.extend(item["class_id"] for item in page["items"])
        cursor = page["next_cursor"]
        if cursor is None:
            break
    assert len(seen) == len(set(seen)) == 6


# ----------------------------------------------------------------------------- the class revision
def _candidate(d: Api) -> str:
    return d.accounts["cand"]


def assign(d: Api, class_id: str, *, if_match: str = '"1"', key: str | None = None) -> Any:
    return d.client.post(
        f"/api/be1/v1/classes/{class_id}/assignments",
        json={"candidate_ref": _candidate(d)},
        headers=hdr(d, "manager", uuid4().hex if key is None else key, **{"If-Match": if_match}),
    )


def test_an_assignment_moves_the_class_revision_and_not_the_assignment_token(api: Api) -> None:
    d = api
    class_id = new_class(d)
    done = assign(d, class_id)
    assert done.status_code == 200, done.text
    assert done.json()["assignment_revision"] == 2
    assert class_row(d, class_id) == ("active", 2)
    item = listed(d, "manager")[class_id]
    assert item["class_revision"] == 2 and item["assignment_revision"] == 2
    # A suspend that read the revision before the assignment is stale.
    stale = command(d, "manager", class_id, "suspend", if_match='"1"')
    assert stale.status_code == 409 and stale.json()["code"] == "STALE_REVISION"
    assert stale.json()["current_version"] == 2
    assert command(d, "manager", class_id, "suspend", if_match='"2"').status_code == 200


def test_an_assignment_replay_does_not_bump_the_class_revision_twice(api: Api) -> None:
    d = api
    class_id = new_class(d)
    first = assign(d, class_id, key="k-assign-replay")
    again = assign(d, class_id, key="k-assign-replay")
    assert first.status_code == again.status_code == 200
    assert shape(first) == shape(again)
    assert class_row(d, class_id) == ("active", 2)


@pytest.mark.parametrize("state", ["suspended", "archived"])
def test_assigning_a_teacher_to_a_read_only_class_is_409_not_404(api: Api, state: str) -> None:
    d = api
    class_id = new_class(d, state=state)
    refused = assign(d, class_id)
    assert refused.status_code == 409, refused.text
    assert refused.json()["code"] == "INVALID_STATE_TRANSITION"
    assert class_row(d, class_id) == (state, 1)
    with d.factory()() as db:
        rows = db.scalar(
            select(func.count())
            .select_from(OrganizationAssignmentModel)
            .where(OrganizationAssignmentModel.class_id == class_id)
        )
    assert rows == 0


def _hold_class_lock_then(d: Api, class_id: str, change: Any, request: Any) -> Any:
    """Lock the class row, start ``request`` (it blocks on the lock), then apply ``change``."""
    with d.factory()() as holder:
        holder.execute(
            select(ClassroomModel).where(ClassroomModel.class_id == class_id).with_for_update()
        )
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(request)
            time.sleep(1.5)
            assert not future.done(), "the request did not wait for the class row lock"
            change(holder)
            holder.commit()
            return future.result(timeout=30)


def test_an_assignment_that_lost_to_a_suspension_is_409_state_not_404(api: Api) -> None:
    d = api
    class_id = new_class(d)

    def suspend_like_the_command(holder: Any) -> None:
        holder.execute(
            update(ClassroomModel)
            .where(ClassroomModel.class_id == class_id)
            .values(state="suspended", revision=ClassroomModel.revision + 1)
        )

    response = _hold_class_lock_then(
        d, class_id, suspend_like_the_command, lambda: assign(d, class_id)
    )
    assert response.status_code == 409, response.text
    assert response.json()["code"] == "INVALID_STATE_TRANSITION"
    assert class_row(d, class_id) == ("suspended", 2)


def test_a_suspend_that_lost_to_an_assignment_is_stale_409(api: Api) -> None:
    d = api
    class_id = new_class(d)

    def assign_like_the_command(holder: Any) -> None:
        holder.execute(
            update(ClassroomModel)
            .where(ClassroomModel.class_id == class_id)
            .values(revision=ClassroomModel.revision + 1)
        )

    response = _hold_class_lock_then(
        d,
        class_id,
        assign_like_the_command,
        lambda: command(d, "manager", class_id, "suspend", if_match='"1"'),
    )
    assert response.status_code == 409 and response.json()["code"] == "STALE_REVISION"
    assert response.json()["current_version"] == 2
    assert class_row(d, class_id) == ("active", 2)


def _race_suspend_and_assign(d: Api, class_id: str) -> tuple[Any, Any]:
    barrier = Barrier(2)

    def do_suspend() -> Any:
        barrier.wait()
        return command(d, "manager", class_id, "suspend", if_match='"1"')

    def do_assign() -> Any:
        barrier.wait()
        return assign(d, class_id)

    with ThreadPoolExecutor(max_workers=2) as pool:
        suspend_future, assign_future = pool.submit(do_suspend), pool.submit(do_assign)
        return suspend_future.result(30), assign_future.result(30)


def test_a_suspend_racing_an_assignment_serialises_and_never_answers_404(api: Api) -> None:
    d = api
    for round_number in range(4):
        class_id = new_class(d)
        suspended, assigned = _race_suspend_and_assign(d, class_id)
        outcomes = (suspended.status_code, assigned.status_code)
        if outcomes == (200, 409):  # the suspension won: the assignment sees a read-only class
            assert assigned.json()["code"] == "INVALID_STATE_TRANSITION", round_number
            assert class_row(d, class_id) == ("suspended", 2)
        else:  # the assignment won: the suspension carries the old revision
            assert outcomes == (409, 200), (round_number, outcomes)
            assert suspended.json()["code"] == "STALE_REVISION", round_number
            assert class_row(d, class_id) == ("active", 2)


# ----------------------------------------------------------------------------- read-only class
def _profile_and_consent(d: Api, class_id: str, *, state: str = "pending") -> tuple[str, str]:
    child_id, consent_id = f"synthetic-{uuid4().hex[:24]}", str(uuid4())
    purpose = f"synthetic-purpose-{uuid4().hex[:8]}"
    with d.factory().begin() as db:
        db.add(
            ConsentRecordModel(
                consent_id=consent_id,
                organization_id=d.organization,
                class_id=class_id,
                child_id=child_id,
                purpose_ref=purpose,
                state=state,
                recorded_by=d.subjects["manager"],
            )
        )
        db.add(
            ManagedProfileModel(
                child_id=child_id,
                organization_id=d.organization,
                class_id=class_id,
                display_name="Synthetic child",
                age_months=72,
                age_revision=1,
                age_source="ADULT_DECLARED",
                consent_id=consent_id,
                consent_purpose_ref=purpose,
                state="active",
                created_by=d.subjects["manager"],
            )
        )
    return child_id, consent_id


def test_a_suspended_class_stays_readable_and_refuses_class_writes(api: Api) -> None:
    d = api
    class_id = new_class(d)
    add_teacher(d, "t1", class_id)
    child_id, consent_id = _profile_and_consent(d, class_id)
    # Sanity on the active class: a session can be configured and a profile created.
    assert (
        d.client.post(
            d.base("/sessions"),
            json={"class_id": class_id, "purpose_ref": PURPOSE, "configuration": {}},
            headers=hdr(d, "t1"),
        ).status_code
        == 201
    )
    assert command(d, "manager", class_id, "suspend", if_match='"1"').status_code == 200

    # Reads stay: the Manager roster summary and consent list, the Teacher's lists, the portfolio
    # route reaches its own gate (409 CONSENT_NOT_EFFECTIVE) and not a class refusal.
    summary = d.client.get(d.base(f"/classes/{class_id}/profiles"), headers=hdr(d, "manager"))
    assert summary.status_code == 200 and summary.json()["active_profile_count"] == 1
    consents = d.client.get(d.base(f"/classes/{class_id}/consents"), headers=hdr(d, "manager"))
    assert consents.status_code == 200 and len(consents.json()["items"]) == 1
    teacher_consents = d.client.get(
        d.base(f"/classes/{class_id}/consents"), headers=hdr(d, "t1")
    )
    assert teacher_consents.status_code == 200
    portfolio = d.client.get(
        d.base(f"/classes/{class_id}/profiles/{child_id}/portfolio"), headers=hdr(d, "t1")
    )
    assert portfolio.status_code == 409 and portfolio.json()["code"] == "CONSENT_NOT_EFFECTIVE"

    # Writes are refused with 409 INVALID_STATE_TRANSITION and nothing is written.
    def refused(response: Any) -> None:
        assert response.status_code == 409, response.text
        assert response.json()["code"] == "INVALID_STATE_TRANSITION"

    for who in ("manager", "t1"):
        refused(
            d.client.post(
                d.base("/sessions"),
                json={"class_id": class_id, "purpose_ref": PURPOSE, "configuration": {}},
                headers=hdr(d, who),
            )
        )
        refused(
            d.client.post(
                d.base(f"/classes/{class_id}/consents"),
                json={"class_id": class_id, "child_id": child_id, "purpose_ref": PURPOSE},
                headers=hdr(d, who),
            )
        )
    refused(
        d.client.post(
            d.base(f"/classes/{class_id}/observations"),
            json={
                "session_id": "synthetic-session",
                "child_id": child_id,
                "kind": "observation",
                "content": {},
            },
            headers=hdr(d, "t1"),
        )
    )
    refused(
        d.client.post(
            d.base(f"/classes/{class_id}/profiles"),
            json={"display_name": "Synthetic learner", "age_months": 60},
            # T-7c: the key and the current class revision (2 after the suspension), so the
            # state check is reached.
            headers=hdr(d, "t1", uuid4().hex, **{"If-Match": '"2"'}),
        )
    )
    refused(
        d.client.post(
            "/v1/lesson-occurrences",
            json={"class_id": class_id, "title": "Bài học vẽ"},
            headers=hdr(d, "t1", uuid4().hex),
        )
    )
    with d.factory()() as db:
        assert (
            db.scalar(
                select(func.count())
                .select_from(ConsentRecordModel)
                .where(ConsentRecordModel.class_id == class_id)
            )
            == 1
        )

    # A consent can still be withdrawn from a read-only class (the SRS is silent: kept allowed).
    revoked = d.client.post(
        d.base(f"/classes/{class_id}/consents/{consent_id}/revoke"), headers=hdr(d, "manager")
    )
    assert revoked.status_code == 200 and revoked.json()["state"] == "revoked"


def _new_session(d: Api, class_id: str, state: str) -> tuple[str, int]:
    created = d.client.post(
        d.base("/sessions"),
        json={"class_id": class_id, "purpose_ref": PURPOSE, "configuration": {}},
        headers=hdr(d, "t1"),
    )
    assert created.status_code == 201, created.text
    session_id = created.json()["session_id"]
    if state != "configured":
        with d.factory().begin() as db:
            db.execute(
                update(ClassroomSessionModel)
                .where(ClassroomSessionModel.session_id == session_id)
                .values(state=state)
            )
    return session_id, int(created.json()["revision"])


def _session_state(d: Api, session_id: str) -> tuple[str, int]:
    with d.factory()() as db:
        row = db.execute(
            select(ClassroomSessionModel.state, ClassroomSessionModel.revision).where(
                ClassroomSessionModel.session_id == session_id
            )
        ).one()
    return str(row[0]), int(row[1])


@pytest.mark.parametrize("final_state", ["suspended", "archived"])
def test_a_read_only_class_starts_no_run_but_a_running_session_can_still_be_closed(
    api: Api, final_state: str
) -> None:
    """T-7b review F-01: lobby, start and resume are class writes; pause and finish are not."""
    d = api
    class_id = new_class(d)
    add_teacher(d, "t1", class_id)
    configured, rev_configured = _new_session(d, class_id, "configured")
    in_lobby, rev_lobby = _new_session(d, class_id, "lobby")
    running, rev_running = _new_session(d, class_id, "active")
    paused, rev_paused = _new_session(d, class_id, "paused")
    assert command(d, "manager", class_id, "suspend", if_match='"1"').status_code == 200
    if final_state == "archived":
        assert command(d, "manager", class_id, "archive", if_match='"2"').status_code == 200

    def post(session_id: str, action: str, revision: int, who: str = "t1") -> Any:
        return d.client.post(
            d.base(f"/sessions/{session_id}/{action}"),
            json={"expected_revision": revision},
            headers=hdr(d, who),
        )

    # Run-starting or continuing transitions are refused with 409 and change nothing, whoever asks.
    for session_id, action, revision, before in (
        (configured, "lobby", rev_configured, "configured"),
        (in_lobby, "start", rev_lobby, "lobby"),
        (paused, "resume", rev_paused, "paused"),
    ):
        for who in ("t1", "manager"):
            response = post(session_id, action, revision, who)
            assert response.status_code == 409, (action, who, response.text)
            assert response.json()["code"] == "INVALID_STATE_TRANSITION"
        assert _session_state(d, session_id) == (before, revision)

    # Stopping a run stays allowed: a running session can be paused, and a paused, running or
    # lobby session can be finished (Q-3: nothing is closed by the class change itself).
    assert post(running, "pause", rev_running).status_code == 200
    assert _session_state(d, running)[0] == "paused"
    assert post(paused, "finish", rev_paused).status_code == 200
    assert _session_state(d, paused)[0] == "finished"
    assert post(in_lobby, "finish", rev_lobby).status_code == 200
    assert _session_state(d, in_lobby)[0] == "finished"
    # Reads stay open.
    assert d.client.get(d.base(f"/sessions/{configured}"), headers=hdr(d, "t1")).status_code == 200

    # A stranger is told nothing about the class state: still the uniform scope answer.
    other = post(configured, "lobby", rev_configured, "parent")
    assert other.status_code in (403, 404) and other.json()["code"] != "INVALID_STATE_TRANSITION"


def test_a_session_transition_waits_for_a_concurrent_suspension_and_is_then_refused(
    api: Api,
) -> None:
    """The class row is read FOR SHARE, so a suspension holding it forces the start to wait."""
    d = api
    class_id = new_class(d)
    add_teacher(d, "t1", class_id)
    session_id, revision = _new_session(d, class_id, "configured")
    with d.factory()() as holder:
        holder.execute(
            select(ClassroomModel.state)
            .where(ClassroomModel.class_id == class_id)
            .with_for_update()
        )
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(
                d.client.post,
                d.base(f"/sessions/{session_id}/lobby"),
                json={"expected_revision": revision},
                headers=hdr(d, "t1"),
            )
            time.sleep(1.5)
            assert not future.done(), "the lobby request did not wait for the class row lock"
            holder.execute(
                update(ClassroomModel)
                .where(ClassroomModel.class_id == class_id)
                .values(state="suspended", revision=2)
            )
            holder.commit()
            response = future.result(timeout=30)
    assert response.status_code == 409, response.text
    assert response.json()["code"] == "INVALID_STATE_TRANSITION"
    assert _session_state(d, session_id) == ("configured", revision)


def test_an_unknown_class_is_still_404_for_writes_and_reads(api: Api) -> None:
    d = api
    missing = f"synthetic-t7b-missing-{uuid4().hex[:8]}"
    response = d.client.post(
        d.base("/sessions"),
        json={"class_id": missing, "purpose_ref": PURPOSE, "configuration": {}},
        headers=hdr(d, "manager"),
    )
    assert response.status_code == 404
    response = d.client.get(d.base(f"/classes/{missing}/profiles"), headers=hdr(d, "manager"))
    assert response.status_code == 404


def test_an_archived_class_is_visible_to_the_manager_and_hidden_from_a_teacher(api: Api) -> None:
    d = api
    class_id = new_class(d, state="archived")
    add_teacher(d, "t1", class_id)
    child_id, _ = _profile_and_consent(d, class_id)
    assert d.client.get(
        d.base(f"/classes/{class_id}/profiles"), headers=hdr(d, "manager")
    ).status_code == 200
    assert d.client.get(
        d.base(f"/classes/{class_id}/consents"), headers=hdr(d, "manager")
    ).status_code == 200
    portfolio_path = d.base(f"/classes/{class_id}/profiles/{child_id}/portfolio")
    # T-7a2: the Manager sees the archived class (not 404) but has no profile access (403).
    assert d.client.get(portfolio_path, headers=hdr(d, "manager")).status_code == 403
    for path in (
        d.base(f"/classes/{class_id}/profiles"),
        d.base(f"/classes/{class_id}/consents"),
        portfolio_path,
    ):
        hidden = d.client.get(path, headers=hdr(d, "t1"))
        assert hidden.status_code == 404, path
        assert hidden.json()["code"] == "RESOURCE_NOT_FOUND"
    assert class_id in listed(d, "manager", state="all")
    assert listed(d, "t1", state="all") == {}


# ----------------------------------------------------------------------------- occurrence writes
def make_occurrence(d: Api, who: str, class_id: str) -> str:
    response = d.client.post(
        "/v1/lesson-occurrences",
        json={"class_id": class_id, "title": "Bài học vẽ"},
        headers=hdr(d, who, uuid4().hex),
    )
    assert response.status_code == 201, response.text
    return str(response.json()["occurrence_id"])


def make_document(d: Api, who: str, occurrence_id: str) -> str:
    document_id, revision_id = str(uuid4()), str(uuid4())
    account = d.accounts[who]
    with d.factory().begin() as db:
        db.execute(
            SOURCE_DOCUMENTS.insert().values(
                source_document_id=document_id,
                occurrence_id=occurrence_id,
                asset_ref=f"synthetic-asset-{uuid4()}",
                upload_session_ref=str(uuid4()),
                extraction_job_ref=f"lsd-{uuid4().hex}",
                safe_file_name="giao-an.pdf",
                file_extension=".pdf",
                page_or_slide_count=3,
                uploaded_by=account,
            )
        )
        db.execute(
            DOCUMENT_REVISIONS.insert().values(
                document_revision_id=revision_id,
                source_document_id=document_id,
                revision_no=1,
                origin="EXTRACTION",
                extracted_text=FIRST_TEXT,
                extracted_text_hash=hashlib.sha256(FIRST_TEXT.encode("utf-8")).hexdigest(),
                parser_name="t7b-synthetic",
                parser_version="1",
                extraction_warnings=[],
                page_coverage=[1, 2, 3],
                created_by=account,
            )
        )
    return document_id


def plan_count(d: Api, occurrence_id: str) -> int:
    with d.factory()() as db:
        return int(
            db.scalar(
                select(func.count())
                .select_from(PLAN_REVISIONS)
                .where(PLAN_REVISIONS.c.occurrence_id == occurrence_id)
            )
            or 0
        )


@pytest.mark.parametrize("final_state", ["suspended", "archived"])
def test_occurrence_documents_and_plans_are_read_only_on_a_read_only_class(
    api: Api, final_state: str
) -> None:
    d = api
    class_id = new_class(d)
    add_teacher(d, "t1", class_id)
    occurrence_id = make_occurrence(d, "t1", class_id)
    document_id = make_document(d, "t1", occurrence_id)
    plan_key = "k-plan-before"
    plan_body = {
        "expected_head_revision_no": 0,
        "objectives": ["Nhận biết hình tròn"],
        "teacher_direction": "Câu chuyện về chú mèo đi tìm bạn",
    }
    plan_url = f"/v1/lesson-occurrences/{occurrence_id}/plan-revisions"
    created = d.client.post(plan_url, json=plan_body, headers=hdr(d, "t1", plan_key))
    assert created.status_code == 201, created.text
    plan_hash = created.json()["content_hash"]

    assert command(d, "manager", class_id, "suspend", if_match='"1"').status_code == 200
    if final_state == "archived":
        assert command(d, "manager", class_id, "archive", if_match='"2"').status_code == 200

    def refused(response: Any) -> None:
        assert response.status_code == 409, response.text
        assert response.json()["code"] == "INVALID_STATE_TRANSITION"

    refused(
        d.client.post(
            plan_url,
            json={**plan_body, "expected_head_revision_no": 1},
            headers=hdr(d, "t1", "k-plan-after"),
        )
    )
    refused(
        d.client.post(
            f"{plan_url}/1/confirm",
            json={"expected_plan_hash": plan_hash},
            headers=hdr(d, "t1", "k-confirm"),
        )
    )
    refused(
        d.client.post(
            f"/v1/lesson-occurrences/{occurrence_id}/documents/{document_id}/revisions",
            json={"extracted_text": "Nội dung đã sửa", "expected_head_revision_no": 1},
            headers=hdr(d, "t1", "k-edit"),
        )
    )
    refused(
        d.client.post(
            f"/v1/lesson-occurrences/{occurrence_id}/documents",
            json={"asset_ref": "upl_synthetic"},
            headers=hdr(d, "t1", "k-attach"),
        )
    )
    data = b"%PDF-1.4 synthetic"
    refused(
        d.client.post(
            "/v1/upload-sessions",
            json={
                "purpose": "OCCURRENCE_DOCUMENT",
                "target_ref": occurrence_id,
                "media_type": "application/pdf",
                "expected_size_bytes": len(data),
                "expected_sha256": hashlib.sha256(data).hexdigest(),
                "file_name": "giao-an.pdf",
            },
            headers=hdr(d, "t1", uuid4().hex),
        )
    )
    refused(
        d.client.post(
            "/v1/lesson-occurrences",
            json={"class_id": class_id, "title": "Bài học khác"},
            headers=hdr(d, "t1", uuid4().hex),
        )
    )
    assert plan_count(d, occurrence_id) == 1

    # A replay of a command that succeeded before the change still answers its first body, and
    # every read stays open.
    replay = d.client.post(plan_url, json=plan_body, headers=hdr(d, "t1", plan_key))
    assert replay.status_code == 201 and replay.json()["content_hash"] == plan_hash
    assert plan_count(d, occurrence_id) == 1
    for path in (
        f"/v1/lesson-occurrences/{occurrence_id}",
        plan_url,
        f"{plan_url}/1",
        f"/v1/lesson-occurrences/{occurrence_id}/documents",
        f"/v1/lesson-occurrences/{occurrence_id}/documents/{document_id}",
    ):
        assert d.client.get(path, headers=hdr(d, "t1")).status_code == 200, path


def test_a_suspension_waits_for_an_occurrence_write_holding_the_class_share_lock(
    api: Api,
) -> None:
    d = api
    class_id = new_class(d)
    add_teacher(d, "t1", class_id)
    occurrence_id = make_occurrence(d, "t1", class_id)
    plan_url = f"/v1/lesson-occurrences/{occurrence_id}/plan-revisions"
    body = {
        "expected_head_revision_no": 0,
        "objectives": ["Nhận biết hình tròn"],
        "teacher_direction": "Câu chuyện về chú mèo",
    }
    # Hold FOR SHARE on the class row the way a plan write does; the suspension must wait for it.
    with d.factory()() as holder:
        holder.execute(
            select(ClassroomModel.state)
            .where(ClassroomModel.class_id == class_id)
            .with_for_update(read=True)
        )
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(command, d, "manager", class_id, "suspend", if_match='"1"')
            time.sleep(1.5)
            assert not future.done(), "the suspension did not wait for the share lock"
            holder.rollback()
            assert future.result(timeout=30).status_code == 200
    refused = d.client.post(plan_url, json=body, headers=hdr(d, "t1", uuid4().hex))
    assert refused.status_code == 409 and refused.json()["code"] == "INVALID_STATE_TRANSITION"


def test_create_profile_on_an_active_class_still_works_and_keeps_the_revision(api: Api) -> None:
    d = api
    class_id = new_class(d)
    add_teacher(d, "t1", class_id)
    created = d.client.post(
        d.base(f"/classes/{class_id}/profiles"),
        json={"display_name": "Synthetic learner", "age_months": 60},
        headers=hdr(d, "t1", uuid4().hex, **{"If-Match": '"1"'}),
    )
    assert created.status_code == 201, created.text
    assert class_row(d, class_id) == ("active", 1)  # profile create does not bump (T-7c-DEC-2)
    consent = d.client.post(
        d.base(f"/classes/{class_id}/consents"),
        json={
            "class_id": class_id,
            "child_id": created.json()["child_id"],
            "purpose_ref": PURPOSE,
        },
        headers=hdr(d, "manager"),
    )
    assert consent.status_code == 201, consent.text


# ----------------------------------------------------------------------------- DDL-H on the live db
def test_the_class_revision_column_default_and_check_are_in_the_database(api: Api) -> None:
    d = api
    with d.factory()() as db:
        column = db.execute(
            text(
                "SELECT data_type, is_nullable, column_default FROM information_schema.columns "
                "WHERE table_name = 'be1_classrooms' AND column_name = 'revision'"
            )
        ).one()
        assert (column[0], column[1], str(column[2])) == ("integer", "NO", "1")
        check = db.scalar(
            text(
                "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                "WHERE conname = 'ck_be1_class_revision' AND conrelid = 'be1_classrooms'::regclass"
            )
        )
        assert check is not None and "revision > 0" in str(check)
        db.execute(
            text(
                "INSERT INTO be1_classrooms (class_id, organization_id, display_name, created_by) "
                "VALUES (:c, :o, 'Synthetic default', 'synthetic')"
            ),
            {"c": f"synthetic-t7b-default-{d.token}", "o": d.organization},
        )
        stored = db.scalar(
            select(ClassroomModel.revision).where(
                ClassroomModel.class_id == f"synthetic-t7b-default-{d.token}"
            )
        )
        assert stored == 1
        db.rollback()
    class_id = new_class(d)
    with d.factory()() as db, pytest.raises(IntegrityError):
        db.execute(
            update(ClassroomModel).where(ClassroomModel.class_id == class_id).values(revision=0)
        )
        db.commit()
