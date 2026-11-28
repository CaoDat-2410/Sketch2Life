"""T-7e PostgreSQL acceptance: Teacher class roster, synthetic-or-consented list with cursor paging.

D-066-100; SRS l.832 (consent for real data only), l.2586 (Profile row), l.864-865 (uniform 404),
l.1640 (cursor lists). Set BE1_TEST_DATABASE_URL to a disposable database whose name contains
``be1_acceptance``; every test builds its own organizations, so rows accumulate only in that
disposable database. Only the external token boundary is substituted: a test header names the
acting adult, and every route, scope query and transaction is real.

The database check ``ck_be1_consent_state`` allows only ``pending`` and ``revoked``, so no
``effective`` consent row can exist in the shared tables. The SQL of the ``REAL`` branch is
exercised in a private schema (four tables made from the models, the check dropped there only),
which is removed after the test; the shared tables are never altered.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    ClassroomModel,
    ConsentRecordModel,
    ManagedProfileModel,
    OrganizationAssignmentModel,
    OrganizationModel,
    ProfileRevisionModel,
)
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.interfaces.http.api_conventions import encode_cursor
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult
from sketch2life.interfaces.http.routers import be1_registry

ISSUER = "synthetic-test-issuer"
ACTOR_HEADER = "X-T7e-Actor"
BASE_TIME = datetime(2026, 3, 1, 8, 0, 0, tzinfo=UTC)
# (actor name, account role, assignment role, scope)
ACTORS = (
    ("manager", "school_manager", "school_admin", "org"),
    ("teacher", "teacher", "teacher", "class"),
    ("other_class_teacher", "teacher", "teacher", "other"),
    ("suspended_teacher", "teacher", "teacher", "suspended"),
    ("archived_teacher", "teacher", "teacher", "archived"),
    ("orgwide_teacher", "teacher", "teacher", "orgwide"),
    ("foreign_teacher", "teacher", "teacher", "foreign"),
)


@dataclass
class T7e:
    app: FastAPI
    client: TestClient
    run: str
    organization_id: str
    class_id: str
    other_class_id: str
    suspended_class_id: str
    archived_class_id: str
    subjects: dict[str, str] = field(default_factory=dict)

    def get(self, actor: str, class_id: str | None = None, **params: Any) -> Any:
        path = (
            f"/api/be1/v1/organizations/{self.organization_id}"
            f"/classes/{class_id or self.class_id}/profiles"
        )
        return self.client.get(path, params=params or None, headers={ACTOR_HEADER: actor})

    @property
    def factory(self) -> Any:
        return self.app.state.be1_runtime.session_factory


def _class(class_id: str, organization_id: str, state: str, created_at: datetime) -> ClassroomModel:
    return ClassroomModel(
        class_id=class_id,
        organization_id=organization_id,
        display_name=f"Synthetic {class_id}"[:200],
        state=state,
        created_by="synthetic-t7e-seed",
        created_at=created_at,
    )


@pytest.fixture
def t7e(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> Iterator[T7e]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL to run PostgreSQL-backed T-7e acceptance tests")
    if "be1_acceptance" not in database_url.rsplit("/", 1)[-1]:
        pytest.fail("BE1_TEST_DATABASE_URL must point to a disposable *be1_acceptance database")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", database_url)
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "development")
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED", "true")
    monkeypatch.setenv("SKETCH2LIFE_ROOM_CODE_HMAC_KEY", "synthetic-test-key-" + "x" * 40)
    monkeypatch.setenv("SKETCH2LIFE_BE1_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()

    app = create_app()
    runtime = app.state.be1_runtime
    if runtime.engine is None or runtime.session_factory is None:
        pytest.fail("BE1 PostgreSQL runtime did not initialize")

    run = uuid4().hex[:10]
    organization_id = f"synthetic-t7e-{run}-org"
    foreign_organization_id = f"synthetic-t7e-{run}-foreign"
    class_id = f"synthetic-t7e-{run}-class-a"
    other_class_id = f"synthetic-t7e-{run}-class-b"
    suspended_class_id = f"synthetic-t7e-{run}-class-s"
    archived_class_id = f"synthetic-t7e-{run}-class-x"
    foreign_class_id = f"synthetic-t7e-{run}-foreign-1"
    subjects = {name: f"synthetic-t7e-{run}-{name}" for name, *_rest in ACTORS}
    principals = {
        subject: VerifiedPrincipal(
            subject=subject, issuer=ISSUER, roles=frozenset(), token_id=f"synthetic-t7e-{n}"
        )
        for n, subject in enumerate(subjects.values())
    }

    with runtime.session_factory.begin() as db:
        db.add_all(
            [
                OrganizationModel(
                    organization_id=organization_id,
                    display_name="Synthetic T7e org",
                    state="active",
                ),
                OrganizationModel(
                    organization_id=foreign_organization_id,
                    display_name="Synthetic T7e foreign org",
                    state="active",
                ),
            ]
        )
        db.flush()
        db.add_all(
            [
                _class(class_id, organization_id, "active", BASE_TIME),
                _class(other_class_id, organization_id, "active", BASE_TIME),
                _class(suspended_class_id, organization_id, "suspended", BASE_TIME),
                _class(archived_class_id, organization_id, "archived", BASE_TIME),
                _class(foreign_class_id, foreign_organization_id, "active", BASE_TIME),
            ]
        )
        db.add_all(
            [
                AdultIdentityModel(
                    subject=subjects[name], issuer=ISSUER, state="active", account_role=account_role
                )
                for name, account_role, _role, _scope in ACTORS
            ]
        )
        db.flush()
        scope_to_row = {
            "org": (organization_id, None),
            "class": (organization_id, class_id),
            "other": (organization_id, other_class_id),
            "suspended": (organization_id, suspended_class_id),
            "archived": (organization_id, archived_class_id),
            "orgwide": (organization_id, None),
            "foreign": (foreign_organization_id, None),
        }
        db.add_all(
            [
                OrganizationAssignmentModel(
                    assignment_id=str(uuid4()),
                    organization_id=scope_to_row[scope][0],
                    subject=subjects[name],
                    class_id=scope_to_row[scope][1],
                    role=role,
                    active=True,
                )
                for name, _account_role, role, scope in ACTORS
            ]
        )

    async def verified_actor(request: Request) -> VerifiedPrincipal:
        return principals[subjects[request.headers[ACTOR_HEADER]]]

    app.dependency_overrides[get_verified_adult] = verified_actor
    with TestClient(app, client=("10.7.7.7", 12345)) as client:
        yield T7e(
            app=app,
            client=client,
            run=run,
            organization_id=organization_id,
            class_id=class_id,
            other_class_id=other_class_id,
            suspended_class_id=suspended_class_id,
            archived_class_id=archived_class_id,
            subjects=subjects,
        )
    app.dependency_overrides.clear()
    runtime.engine.dispose()
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()


def _profile(
    t: T7e,
    child_id: str,
    *,
    origin: str,
    created_at: datetime,
    class_id: str | None = None,
    state: str = "active",
    consent_state: str | None = None,
    name: str | None = None,
) -> str:
    """Seed one profile. `consent_state` adds a consent row of that state (REAL and legacy)."""
    target_class = class_id or t.class_id
    consent_id: str | None = None
    purpose_ref: str | None = None
    if origin == "REAL" or origin == "LEGACY_UNCLASSIFIED" and consent_state is not None:
        consent_id = str(uuid4())
        purpose_ref = f"synthetic-purpose-{uuid4().hex[:8]}"
    with t.factory.begin() as db:
        if consent_state is not None and consent_id is not None and purpose_ref is not None:
            db.add(
                ConsentRecordModel(
                    consent_id=consent_id,
                    organization_id=t.organization_id,
                    class_id=target_class,
                    child_id=child_id,
                    purpose_ref=purpose_ref,
                    state=consent_state,
                    recorded_by=t.subjects["manager"],
                )
            )
        db.add(
            ManagedProfileModel(
                child_id=child_id,
                organization_id=t.organization_id,
                class_id=target_class,
                display_name=name or f"Synthetic {child_id[-6:]}",
                age_months=72,
                age_revision=1,
                age_source="SYNTHETIC_FIXTURE" if origin == "SYNTHETIC_DEV" else "ADULT_DECLARED",
                consent_id=consent_id,
                consent_purpose_ref=purpose_ref,
                data_origin=origin,
                state=state,
                created_by=t.subjects["manager"],
                created_at=created_at,
            )
        )
    return child_id


def _synthetic(t: T7e, index: int, created_at: datetime | None = None, **kwargs: Any) -> str:
    return _profile(
        t,
        f"synthetic-t7e-{t.run}-{index:03d}",
        origin="SYNTHETIC_DEV",
        created_at=created_at or BASE_TIME + timedelta(minutes=index),
        **kwargs,
    )


def _audit_count(t: T7e, action: str) -> int:
    with t.factory() as db:
        return int(
            db.scalar(
                select(func.count())
                .select_from(CoreAuditEntryModel)
                .where(
                    CoreAuditEntryModel.organization_id == t.organization_id,
                    CoreAuditEntryModel.action == action,
                )
            )
            or 0
        )


def _walk(t: T7e, *, limit: int, class_id: str | None = None) -> tuple[list[str], int, set[int]]:
    seen: list[str] = []
    counts: set[int] = set()
    pages = 0
    cursor: str | None = None
    while True:
        params: dict[str, Any] = {"limit": limit}
        if cursor is not None:
            params["cursor"] = cursor
        page = t.get("teacher", class_id, **params)
        assert page.status_code == 200, page.text
        body = page.json()
        pages += 1
        assert len(body["items"]) <= limit
        seen.extend(item["child_id"] for item in body["items"])
        counts.add(body["active_profile_count"])
        cursor = body["next_cursor"]
        if cursor is None:
            return seen, pages, counts
        assert pages < 100


def _db_order(t: T7e, ids: list[str]) -> list[str]:
    with t.factory() as db:
        return list(
            db.scalars(
                select(ManagedProfileModel.child_id)
                .where(ManagedProfileModel.child_id.in_(ids))
                .order_by(ManagedProfileModel.created_at, ManagedProfileModel.child_id)
            )
        )


# --- the Teacher list --------------------------------------------------------------------------


def test_empty_class_is_200_with_the_new_empty_body(t7e: T7e) -> None:
    response = t7e.get("teacher")
    assert response.status_code == 200, response.text
    assert response.json() == {
        "contract": "Be1ManagedProfileListV1",
        "items": [],
        "next_cursor": None,
        "active_profile_count": 0,
    }
    assert _audit_count(t7e, "profile.list") == 0


def test_synthetic_profiles_are_listed_paged_and_counted(t7e: T7e) -> None:
    listed = [_synthetic(t7e, n) for n in range(5)]
    # Not listed, but counted (all are active): a REAL profile with a pending or a revoked
    # consent, and a legacy profile (with and without a consent row). An archived profile is
    # neither listed nor counted.
    _profile(
        t7e, f"real-pending-{t7e.run}", origin="REAL", created_at=BASE_TIME, consent_state="pending"
    )
    _profile(
        t7e, f"real-revoked-{t7e.run}", origin="REAL", created_at=BASE_TIME, consent_state="revoked"
    )
    _profile(t7e, f"legacy-bare-{t7e.run}", origin="LEGACY_UNCLASSIFIED", created_at=BASE_TIME)
    _profile(
        t7e,
        f"legacy-pending-{t7e.run}",
        origin="LEGACY_UNCLASSIFIED",
        created_at=BASE_TIME,
        consent_state="pending",
    )
    _synthetic(t7e, 90, state="archived")
    expected = _db_order(t7e, listed)

    first = t7e.get("teacher", limit=2)
    assert first.status_code == 200, first.text
    body = first.json()
    assert body["contract"] == "Be1ManagedProfileListV1"
    assert [item["child_id"] for item in body["items"]] == expected[:2]
    assert set(body["items"][0]) == {"child_id", "class_id", "display_name", "age_months"}
    assert body["next_cursor"] is not None
    assert body["active_profile_count"] == 9
    for unlisted in ("real-pending", "real-revoked", "legacy-bare", "legacy-pending"):
        assert unlisted not in first.text

    seen, pages, counts = _walk(t7e, limit=2)
    assert seen == expected and pages == 3
    assert counts == {9}  # the count is independent of the page
    seen_all, pages_all, _counts = _walk(t7e, limit=100)
    assert seen_all == expected and pages_all == 1
    assert _audit_count(t7e, "profile.list") == 0


def test_default_page_is_25_and_the_last_page_has_no_cursor(t7e: T7e) -> None:
    ids = [_synthetic(t7e, n) for n in range(27)]
    first = t7e.get("teacher").json()
    assert len(first["items"]) == 25 and first["next_cursor"] is not None
    second = t7e.get("teacher", cursor=first["next_cursor"]).json()
    assert len(second["items"]) == 2 and second["next_cursor"] is None
    assert [i["child_id"] for i in first["items"] + second["items"]] == _db_order(t7e, ids)
    assert first["active_profile_count"] == second["active_profile_count"] == 27


def test_equal_created_at_is_ordered_by_child_id_across_a_page_boundary(t7e: T7e) -> None:
    same = BASE_TIME + timedelta(minutes=3)
    ids = [_synthetic(t7e, n, same) for n in (4, 2, 5, 1, 3)]  # inserted out of order
    expected = sorted(ids)
    assert _db_order(t7e, ids) == expected
    for limit in (1, 2, 3):
        seen, _pages, _counts = _walk(t7e, limit=limit)
        assert seen == expected, limit


def test_exact_page_has_no_cursor_and_one_more_row_has_one(t7e: T7e) -> None:
    for n in range(3):
        _synthetic(t7e, n)
    assert t7e.get("teacher", limit=3).json()["next_cursor"] is None
    assert t7e.get("teacher", limit=2).json()["next_cursor"] is not None


def test_limit_bounds_are_400_for_both_audiences(t7e: T7e) -> None:
    _synthetic(t7e, 0)
    for actor in ("teacher", "manager"):
        for bad in (0, 101, -1):
            response = t7e.get(actor, limit=bad)
            assert response.status_code == 400, (actor, bad, response.text)
            assert response.json()["code"] == "INVALID_REQUEST"
        assert t7e.get(actor, limit="x").status_code == 400
        assert t7e.get(actor, limit=1).status_code == 200
        assert t7e.get(actor, limit=100).status_code == 200


def test_teacher_bad_cursors_are_400_and_scope_checks_come_first(t7e: T7e) -> None:
    _synthetic(t7e, 0)
    scopes = (
        f"be1.profiles:{t7e.organization_id}:{t7e.other_class_id}",
        f"be1.consents:{t7e.organization_id}:{t7e.class_id}",
        f"be1.classes:{t7e.organization_id}:active",
    )
    cursors = ["not-a-cursor", "e30"] + [
        encode_cursor(scope=scope, sort_key=BASE_TIME.isoformat(), item_id="x") for scope in scopes
    ]
    tampered = encode_cursor(
        scope=f"be1.profiles:{t7e.organization_id}:{t7e.class_id}",
        sort_key="not-a-time",
        item_id="x",
    )
    for cursor in [*cursors, tampered]:
        response = t7e.get("teacher", cursor=cursor)
        assert response.status_code == 400, (cursor, response.text)
        assert response.json()["code"] == "INVALID_REQUEST"
        assert response.json()["field_errors"] == [{"field": "cursor", "code": "INVALID_FORMAT"}]
    assert t7e.get("teacher", cursor="a" * 1025).status_code == 400
    assert t7e.get("teacher", cursor="").status_code == 400
    # Out-of-scope callers do not learn anything from the cursor.
    assert t7e.get("foreign_teacher", cursor="not-a-cursor").status_code == 404
    assert t7e.get("other_class_teacher", cursor="not-a-cursor").status_code == 404
    assert t7e.get("orgwide_teacher", cursor="not-a-cursor").status_code == 403


def test_a_cursor_of_another_class_cannot_be_replayed(t7e: T7e) -> None:
    for n in range(3):
        _synthetic(t7e, n)
    cursor = t7e.get("teacher", limit=1).json()["next_cursor"]
    replay = t7e.get("teacher", t7e.other_class_id, cursor=cursor)
    # The Teacher of class a has no row for class b: the uniform 404, the cursor never read.
    assert replay.status_code == 404, replay.text


def test_suspended_class_is_readable_and_archived_is_404_for_a_teacher(t7e: T7e) -> None:
    _synthetic(t7e, 1, class_id=t7e.suspended_class_id)
    _synthetic(t7e, 2, class_id=t7e.archived_class_id)
    suspended = t7e.get("suspended_teacher", t7e.suspended_class_id)
    assert suspended.status_code == 200, suspended.text
    assert len(suspended.json()["items"]) == 1 and suspended.json()["active_profile_count"] == 1
    archived = t7e.get("archived_teacher", t7e.archived_class_id)
    assert archived.status_code == 404, archived.text
    assert archived.json()["code"] == "RESOURCE_NOT_FOUND"
    # A Manager still reads the count of an archived class.
    summary = t7e.get("manager", t7e.archived_class_id)
    assert summary.status_code == 200 and summary.json()["active_profile_count"] == 1


def test_a_profile_moved_out_between_pages_disappears_from_the_next_page(t7e: T7e) -> None:
    ids = [_synthetic(t7e, n) for n in range(3)]
    first = t7e.get("teacher", limit=1).json()
    assert [item["child_id"] for item in first["items"]] == ids[:1]
    with t7e.factory.begin() as db:
        moved = db.get(ManagedProfileModel, ids[1])
        assert moved is not None
        moved.class_id = t7e.other_class_id
    rest = t7e.get("teacher", limit=5, cursor=first["next_cursor"]).json()
    assert [item["child_id"] for item in rest["items"]] == ids[2:]
    assert rest["active_profile_count"] == 2


def test_out_of_scope_callers_get_one_uniform_404_and_other_teacher_rows_403(t7e: T7e) -> None:
    _synthetic(t7e, 0)
    bodies = []
    for actor in ("foreign_teacher", "other_class_teacher"):
        response = t7e.get(actor)
        assert response.status_code == 404, (actor, response.text)
        body = response.json()
        bodies.append({"code": body["code"], "message": body["message"]})
    assert bodies[0] == bodies[1] and bodies[0]["code"] == "RESOURCE_NOT_FOUND"
    # An organization-wide Teacher row is a membership marker and sees no profile (403).
    orgwide = t7e.get("orgwide_teacher")
    assert orgwide.status_code == 403 and orgwide.json()["code"] == "ACTION_NOT_ALLOWED"
    assert t7e.get("teacher", f"missing-{uuid4().hex[:8]}").status_code == 404


# --- the Manager summary -----------------------------------------------------------------------


def test_manager_gets_the_summary_ignores_valid_paging_and_writes_no_audit_row(t7e: T7e) -> None:
    for n in range(3):
        _synthetic(t7e, n)
    _profile(
        t7e, f"real-pending-{t7e.run}", origin="REAL", created_at=BASE_TIME, consent_state="pending"
    )
    for params in ({}, {"limit": 1}, {"limit": 100, "cursor": "anything-valid-length"}):
        response = t7e.get("manager", **params)
        assert response.status_code == 200, (params, response.text)
        assert response.json() == {
            "contract": "Be1ClassRosterSummaryV1",
            "class_id": t7e.class_id,
            "active_profile_count": 4,
        }
        for forbidden in ("items", "next_cursor", "display_name", "child_id"):
            assert forbidden not in response.text
    # An overlong cursor is the framework 400 for a Manager too.
    assert t7e.get("manager", cursor="a" * 1025).status_code == 400
    assert _audit_count(t7e, "profile.list") == 0


# --- the REAL branch of the filter (SQL on PostgreSQL, in a private schema) ----------------------


@pytest.fixture
def private_schema() -> Iterator[Session]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL to run PostgreSQL-backed T-7e acceptance tests")
    if "be1_acceptance" not in database_url.rsplit("/", 1)[-1]:
        pytest.fail("BE1_TEST_DATABASE_URL must point to a disposable *be1_acceptance database")
    schema = f"t7e_{uuid4().hex[:12]}"
    engine = create_engine(database_url)
    tables = [
        OrganizationModel.__table__,
        ClassroomModel.__table__,
        ManagedProfileModel.__table__,
        # T-12b: every new profile gets its baseline revision in the same flush.
        ProfileRevisionModel.__table__,
        ConsentRecordModel.__table__,
    ]
    try:
        with engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        connection = engine.connect().execution_options(schema_translate_map={None: schema})
        transaction = connection.begin()
        try:
            # `create_all` orders the tables and adds the deferred head foreign key of the
            # profile table (a cycle with its revisions) after both exist.
            ManagedProfileModel.metadata.create_all(connection, tables=tables)
            # The shared tables stay as they are; only this private copy accepts `effective`.
            connection.execute(
                text(
                    f'ALTER TABLE "{schema}".be1_consent_records '
                    "DROP CONSTRAINT ck_be1_consent_state"
                )
            )
            with Session(connection) as session:
                yield session
        finally:
            transaction.rollback()
            connection.close()
    finally:
        with engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        engine.dispose()


def test_real_branch_lists_only_an_effective_consent_of_the_same_class_child_and_purpose(
    private_schema: Session,
) -> None:
    db = private_schema
    org, cls, other_cls = "org-p", "class-p", "class-q"
    db.add(OrganizationModel(organization_id=org, display_name="Private org", state="active"))
    db.flush()
    db.add_all(
        [
            _class("class-p", org, "active", BASE_TIME),
            _class("class-q", org, "active", BASE_TIME),
        ]
    )
    db.flush()

    def add(child: str, origin: str, *, consent: tuple[str, str, str] | None) -> None:
        """`consent` is (state, class, purpose) of the consent row; the profile has `p-<child>`."""
        purpose = f"p-{child}" if origin != "SYNTHETIC_DEV" else None
        db.add(
            ManagedProfileModel(
                child_id=child,
                organization_id=org,
                class_id=cls,
                display_name=child,
                age_months=72,
                age_revision=1,
                age_source="ADULT_DECLARED",
                consent_id=str(uuid4()) if origin == "REAL" else None,
                consent_purpose_ref=purpose,
                data_origin=origin,
                state="active",
                created_by="synthetic-t7e",
                created_at=BASE_TIME + timedelta(minutes=len(child)),
            )
        )
        if consent is not None:
            state, consent_class, consent_purpose = consent
            db.add(
                ConsentRecordModel(
                    consent_id=str(uuid4()),
                    organization_id=org,
                    class_id=consent_class,
                    child_id=child,
                    purpose_ref=consent_purpose or f"p-{child}",
                    state=state,
                    recorded_by="synthetic-t7e",
                )
            )

    add("syn", "SYNTHETIC_DEV", consent=None)
    add("real-effective", "REAL", consent=("effective", cls, ""))
    add("real-pending", "REAL", consent=("pending", cls, ""))
    add("real-revoked", "REAL", consent=("revoked", cls, ""))
    add("real-none", "REAL", consent=None)
    add("real-other-class", "REAL", consent=("effective", other_cls, ""))
    add("real-other-purpose", "REAL", consent=("effective", cls, "another-purpose"))
    add("legacy-effective", "LEGACY_UNCLASSIFIED", consent=("effective", cls, ""))
    db.flush()

    statement = be1_registry._roster_listed(org, cls).order_by(
        ManagedProfileModel.created_at, ManagedProfileModel.child_id
    )
    listed = {row.child_id for row in db.scalars(statement)}
    assert listed == {"syn", "real-effective"}
    assert be1_registry._active_profile_count(db, org, cls) == 8
