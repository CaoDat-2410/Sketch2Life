"""T-7a PostgreSQL acceptance: School Manager roster summary, Teacher rule and cursor paging.

SRS l.2586 (Profile row), l.864-865 (403 only inside a known scope), l.1640 (cursor lists);
D-066-75 CM-2 to CM-5, CM-7, CM-11. Set BE1_TEST_DATABASE_URL to a disposable database whose
name contains ``be1_acceptance``; every test builds its own organizations, so rows accumulate
only in that disposable database. Only the external token boundary is substituted: a test
header names the acting adult, and every route, scope query and transaction is real.
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
from sqlalchemy import func, select

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    ClassroomModel,
    ConsentRecordModel,
    ManagedProfileModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.interfaces.http.api_conventions import encode_cursor
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult

ISSUER = "synthetic-test-issuer"
ACTOR_HEADER = "X-T7a-Actor"
BASE_TIME = datetime(2026, 2, 1, 8, 0, 0, tzinfo=UTC)
# (actor name, account role, assignment role, scope: "org", "class", "other", "foreign")
ACTORS = (
    ("manager", "school_manager", "school_admin", "org"),
    ("orgwide_teacher", "teacher", "teacher", "org"),
    ("scoped_teacher", "teacher", "teacher", "class"),
    ("other_class_teacher", "teacher", "teacher", "other"),
    ("orgwide_guide", "teacher", "guide", "org"),
    ("class_guide", "teacher", "guide", "class"),
    ("orgwide_observer", "teacher", "observer", "org"),
    ("class_observer", "teacher", "observer", "class"),
    ("foreign_teacher", "teacher", "teacher", "foreign"),
    ("foreign_manager", "school_manager", "school_admin", "foreign"),
)


@dataclass
class T7a:
    app: FastAPI
    client: TestClient
    run: str
    organization_id: str
    foreign_organization_id: str
    class_id: str
    other_class_id: str
    foreign_class_ids: list[str]
    subjects: dict[str, str] = field(default_factory=dict)

    def get(self, actor: str, path: str, **params: Any) -> Any:
        return self.client.get(path, params=params or None, headers={ACTOR_HEADER: actor})

    def post(self, actor: str, path: str, body: dict[str, Any]) -> Any:
        return self.client.post(path, json=body, headers={ACTOR_HEADER: actor})

    @property
    def factory(self) -> Any:
        return self.app.state.be1_runtime.session_factory

    def org(self, suffix: str = "", organization_id: str | None = None) -> str:
        return f"/api/be1/v1/organizations/{organization_id or self.organization_id}{suffix}"

    def class_path(self, suffix: str, class_id: str | None = None) -> str:
        return self.org(f"/classes/{class_id or self.class_id}{suffix}")


def _class_row(class_id: str, organization_id: str, created_at: datetime) -> ClassroomModel:
    return ClassroomModel(
        class_id=class_id,
        organization_id=organization_id,
        display_name=f"Synthetic {class_id}"[:200],
        state="active",
        created_by="synthetic-t7a-seed",
        created_at=created_at,
    )


@pytest.fixture
def t7a(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> Iterator[T7a]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL to run PostgreSQL-backed T-7a acceptance tests")
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
    organization_id = f"synthetic-t7a-{run}-org"
    foreign_organization_id = f"synthetic-t7a-{run}-foreign"
    class_id = f"synthetic-t7a-{run}-class-a"
    other_class_id = f"synthetic-t7a-{run}-class-b"
    foreign_class_ids = [f"synthetic-t7a-{run}-foreign-{n}" for n in (1, 2)]
    subjects = {name: f"synthetic-t7a-{run}-{name}" for name, *_rest in ACTORS}
    principals = {
        subject: VerifiedPrincipal(
            subject=subject, issuer=ISSUER, roles=frozenset(), token_id=f"synthetic-t7a-{n}"
        )
        for n, subject in enumerate(subjects.values())
    }

    with runtime.session_factory.begin() as db:
        db.add_all(
            [
                OrganizationModel(
                    organization_id=organization_id,
                    display_name="Synthetic T7a org",
                    state="active",
                ),
                OrganizationModel(
                    organization_id=foreign_organization_id,
                    display_name="Synthetic T7a foreign org",
                    state="active",
                ),
            ]
        )
        db.flush()
        db.add_all(
            [
                _class_row(class_id, organization_id, BASE_TIME),
                _class_row(other_class_id, organization_id, BASE_TIME + timedelta(seconds=1)),
                _class_row(foreign_class_ids[0], foreign_organization_id, BASE_TIME),
                _class_row(
                    foreign_class_ids[1], foreign_organization_id, BASE_TIME + timedelta(seconds=1)
                ),
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
        scope_org = {
            "org": (organization_id, None),
            "class": (organization_id, class_id),
            "other": (organization_id, other_class_id),
            "foreign": (foreign_organization_id, None),
        }
        db.add_all(
            [
                OrganizationAssignmentModel(
                    assignment_id=str(uuid4()),
                    organization_id=scope_org[scope][0],
                    subject=subjects[name],
                    class_id=scope_org[scope][1],
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
        yield T7a(
            app=app,
            client=client,
            run=run,
            organization_id=organization_id,
            foreign_organization_id=foreign_organization_id,
            class_id=class_id,
            other_class_id=other_class_id,
            foreign_class_ids=foreign_class_ids,
            subjects=subjects,
        )
    app.dependency_overrides.clear()
    runtime.engine.dispose()
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()


def _add_profile(
    t: T7a, *, name: str, state: str = "active", class_id: str | None = None
) -> str:
    child_id = f"synthetic-{uuid4().hex[:24]}"
    consent_id = str(uuid4())
    purpose_ref = f"synthetic-purpose-{uuid4().hex[:8]}"
    with t.factory.begin() as db:
        db.add(
            ConsentRecordModel(
                consent_id=consent_id,
                organization_id=t.organization_id,
                class_id=class_id or t.class_id,
                child_id=child_id,
                purpose_ref=purpose_ref,
                state="pending",
                recorded_by=t.subjects["manager"],
            )
        )
        db.add(
            ManagedProfileModel(
                child_id=child_id,
                organization_id=t.organization_id,
                class_id=class_id or t.class_id,
                display_name=name,
                age_months=72,
                age_revision=1,
                age_source="ADULT_DECLARED",
                consent_id=consent_id,
                consent_purpose_ref=purpose_ref,
                state=state,
                created_by=t.subjects["manager"],
            )
        )
    return child_id


def _audit_count(t: T7a, action: str, *, decision: str | None = None) -> int:
    with t.factory() as db:
        statement = (
            select(func.count())
            .select_from(CoreAuditEntryModel)
            .where(
                CoreAuditEntryModel.organization_id == t.organization_id,
                CoreAuditEntryModel.action == action,
            )
        )
        if decision is not None:
            statement = statement.where(CoreAuditEntryModel.decision == decision)
        return int(db.scalar(statement) or 0)


def _error_core(response: Any) -> dict[str, Any]:
    body = response.json()
    return {"code": body["code"], "message": body["message"]}


# --- A09 -----------------------------------------------------------------------------------


def test_manager_a09_returns_the_count_summary_without_child_fields_or_audit(t7a: T7a) -> None:
    _add_profile(t7a, name="Synthetic Active One")
    _add_profile(t7a, name="Synthetic Active Two")
    _add_profile(t7a, name="Synthetic Inactive", state="archived")
    response = t7a.get("manager", t7a.class_path("/profiles"))
    assert response.status_code == 200, response.text
    assert response.json() == {
        "contract": "Be1ClassRosterSummaryV1",
        "class_id": t7a.class_id,
        "active_profile_count": 2,
    }
    for forbidden in ("display_name", "age_months", "child_id", "Synthetic Active", "items"):
        assert forbidden not in response.text
    # No consent gate and no audit row for the Manager (CM-5); the pending consents did not matter.
    assert _audit_count(t7a, "profile.list") == 0
    empty = t7a.get("manager", t7a.class_path("/profiles", t7a.other_class_id))
    assert empty.json()["active_profile_count"] == 0


def test_class_scoped_teacher_a09_keeps_the_gate_and_its_audit_row(t7a: T7a) -> None:
    empty = t7a.get("scoped_teacher", t7a.class_path("/profiles"))
    assert empty.status_code == 200, empty.text
    assert empty.json() == {"contract": "Be1ManagedProfileListV1", "items": []}
    _add_profile(t7a, name="Synthetic Gated Child")
    gated = t7a.get("scoped_teacher", t7a.class_path("/profiles"))
    # The consent gate cannot pass today (no `effective` state exists): a non-empty class is 409.
    assert gated.status_code == 409, gated.text
    assert gated.json()["code"] == "CONSENT_NOT_EFFECTIVE"
    assert "Synthetic Gated Child" not in gated.text
    assert _audit_count(t7a, "profile.list", decision="denied_consent_pending") == 1


@pytest.mark.parametrize(
    "actor",
    ["orgwide_teacher", "orgwide_guide", "class_guide", "orgwide_observer", "class_observer"],
)
def test_other_teacher_side_rows_are_403_on_a09_and_a10(t7a: T7a, actor: str) -> None:
    _add_profile(t7a, name="Synthetic Hidden Child")
    for suffix in ("/profiles", "/consents"):
        response = t7a.get(actor, t7a.class_path(suffix))
        assert response.status_code == 403, (suffix, response.text)
        assert response.json()["code"] == "ACTION_NOT_ALLOWED"
        assert "Synthetic Hidden Child" not in response.text
        assert "items" not in response.json()
    assert _audit_count(t7a, "profile.list") == 0


def test_out_of_scope_callers_get_one_uniform_404_and_unknown_class_is_404(t7a: T7a) -> None:
    _add_profile(t7a, name="Synthetic Scoped Child")
    for suffix in ("/profiles", "/consents"):
        bodies = [
            _error_core(t7a.get(actor, t7a.class_path(suffix)))
            for actor in ("foreign_teacher", "foreign_manager", "other_class_teacher")
        ]
        unknown_org = _error_core(
            t7a.get("foreign_teacher", t7a.org(f"-missing/classes/{t7a.class_id}{suffix}"))
        )
        assert bodies[0]["code"] == "RESOURCE_NOT_FOUND"
        assert all(body == bodies[0] for body in bodies + [unknown_org])
        for actor in ("foreign_teacher", "foreign_manager", "other_class_teacher"):
            assert t7a.get(actor, t7a.class_path(suffix)).status_code == 404
        # An unknown class is 404 for every adult, also for the rows that would be 403 on a known
        # class (the class is looked up before the role rule).
        for actor in ("manager", "scoped_teacher", "orgwide_teacher", "class_guide"):
            missing = t7a.get(actor, t7a.class_path(suffix, f"missing-{uuid4().hex[:8]}"))
            assert missing.status_code == 404, (actor, suffix, missing.text)


# --- A10 -----------------------------------------------------------------------------------


def test_manager_a10_has_no_child_id_or_purpose_ref_and_teacher_keeps_them(t7a: T7a) -> None:
    child_id = _add_profile(t7a, name="Synthetic Consent Child")
    manager = t7a.get("manager", t7a.class_path("/consents"))
    assert manager.status_code == 200, manager.text
    body = manager.json()
    assert body["contract"] == "Be1ConsentListManagerV1"
    assert body["next_cursor"] is None
    assert len(body["items"]) == 1
    assert set(body["items"][0]) == {"consent_id", "state", "effective"}
    assert body["items"][0]["state"] == "pending" and body["items"][0]["effective"] is False
    assert child_id not in manager.text and "synthetic-purpose" not in manager.text

    teacher = t7a.get("scoped_teacher", t7a.class_path("/consents"))
    assert teacher.status_code == 200, teacher.text
    teacher_body = teacher.json()
    assert teacher_body["contract"] == "Be1ConsentListV1"
    assert teacher_body["next_cursor"] is None
    assert set(teacher_body["items"][0]) == {
        "consent_id",
        "child_id",
        "purpose_ref",
        "state",
        "effective",
    }
    assert teacher_body["items"][0]["child_id"] == child_id


def _seed_consents(
    t: T7a, times: list[datetime], *, class_id: str | None = None
) -> list[tuple[datetime, str]]:
    created: list[tuple[datetime, str]] = []
    with t.factory.begin() as db:
        for index, moment in enumerate(times):
            consent_id = f"cons{t.run}{index:04d}"
            db.add(
                ConsentRecordModel(
                    consent_id=consent_id,
                    organization_id=t.organization_id,
                    class_id=class_id or t.class_id,
                    child_id=f"synthetic-child-{index}",
                    purpose_ref="synthetic-purpose-page",
                    state="pending",
                    recorded_by=t.subjects["manager"],
                    recorded_at=moment,
                )
            )
            created.append((moment, consent_id))
    return created


def _walk(t: T7a, actor: str, path: str, *, limit: int) -> tuple[list[str], int]:
    seen: list[str] = []
    pages = 0
    cursor: str | None = None
    while True:
        params: dict[str, Any] = {"limit": limit}
        if cursor is not None:
            params["cursor"] = cursor
        page = t.get(actor, path, **params)
        assert page.status_code == 200, page.text
        body = page.json()
        pages += 1
        assert len(body["items"]) <= limit
        key = "consent_id" if "consent_id" in (body["items"][:1] or [{}])[0] else "class_id"
        seen.extend(item[key] for item in body["items"])
        assert "next_cursor" in body
        cursor = body["next_cursor"]
        if cursor is None:
            return seen, pages
        assert pages < 100


def test_a10_pages_newest_first_and_stay_stable_for_equal_timestamps(t7a: T7a) -> None:
    same = BASE_TIME + timedelta(minutes=5)
    created = _seed_consents(
        t7a,
        [
            BASE_TIME,
            BASE_TIME + timedelta(minutes=1),
            same,
            same,
            BASE_TIME + timedelta(minutes=9),
        ],
    )
    expected = [consent_id for _moment, consent_id in sorted(created, reverse=True)]
    # The two equal timestamps order by consent_id descending (same order the database sorts).
    with t7a.factory() as db:
        in_db = list(
            db.scalars(
                select(ConsentRecordModel.consent_id)
                .where(ConsentRecordModel.class_id == t7a.class_id)
                .order_by(
                    ConsentRecordModel.recorded_at.desc(), ConsentRecordModel.consent_id.desc()
                )
            )
        )
    assert in_db == expected
    for actor in ("manager", "scoped_teacher"):
        seen, pages = _walk(t7a, actor, t7a.class_path("/consents"), limit=1)
        assert seen == expected and pages == 5
        seen_two, pages_two = _walk(t7a, actor, t7a.class_path("/consents"), limit=2)
        assert seen_two == expected and pages_two == 3
    assert t7a.get("manager", t7a.class_path("/consents"), limit=0).status_code == 400
    assert t7a.get("manager", t7a.class_path("/consents"), limit=101).status_code == 400


def test_a10_bad_cursors_are_400_and_scope_checks_come_first(t7a: T7a) -> None:
    path = t7a.class_path("/consents")
    wrong_scope = encode_cursor(
        scope=f"be1.classes:{t7a.organization_id}", sort_key=BASE_TIME.isoformat(), item_id="x"
    )
    for cursor in ("not-a-cursor", wrong_scope):
        response = t7a.get("manager", path, cursor=cursor)
        assert response.status_code == 400, response.text
        assert response.json()["code"] == "INVALID_REQUEST"
        assert response.json()["field_errors"] == [{"field": "cursor", "code": "INVALID_FORMAT"}]
    # A cursor made for another class of the same organization is rejected too.
    other_scope = encode_cursor(
        scope=f"be1.consents:{t7a.organization_id}:{t7a.other_class_id}",
        sort_key=BASE_TIME.isoformat(),
        item_id="x",
    )
    assert t7a.get("manager", path, cursor=other_scope).status_code == 400
    # Out-of-scope and role-refused callers do not learn anything from the cursor.
    assert t7a.get("foreign_teacher", path, cursor="not-a-cursor").status_code == 404
    assert t7a.get("orgwide_teacher", path, cursor="not-a-cursor").status_code == 403


# --- A07 -----------------------------------------------------------------------------------


def _seed_classes(t: T7a, moments: list[datetime], *, organization_id: str | None = None) -> None:
    with t.factory.begin() as db:
        for index, moment in enumerate(moments):
            db.add(
                _class_row(
                    f"synthetic-t7a-{t.run}-pg-{moment.timestamp():.0f}-{index:02d}",
                    organization_id or t.organization_id,
                    moment,
                )
            )


def _db_class_order(t: T7a) -> list[str]:
    with t.factory() as db:
        return list(
            db.scalars(
                select(ClassroomModel.class_id)
                .where(ClassroomModel.organization_id == t.organization_id)
                .order_by(ClassroomModel.created_at, ClassroomModel.class_id)
            )
        )


def test_a07_pages_in_created_at_then_class_id_order_without_duplicates(t7a: T7a) -> None:
    tie = BASE_TIME + timedelta(minutes=3)
    _seed_classes(t7a, [tie, tie, tie, BASE_TIME + timedelta(minutes=2)])
    expected = _db_class_order(t7a)
    assert len(expected) == 6
    seen, pages = _walk(t7a, "manager", t7a.org("/classes"), limit=1)
    assert seen == expected and pages == 6
    seen_two, pages_two = _walk(t7a, "manager", t7a.org("/classes"), limit=4)
    assert seen_two == expected and pages_two == 2

    # A class inserted between two pages is neither duplicated nor skipped when it sorts after
    # the cursor; the walk ends with it exactly once.
    first = t7a.get("manager", t7a.org("/classes"), limit=2).json()
    assert first["next_cursor"] is not None
    late = BASE_TIME + timedelta(minutes=30)
    _seed_classes(t7a, [late])
    collected = [item["class_id"] for item in first["items"]]
    cursor = first["next_cursor"]
    while cursor is not None:
        page = t7a.get("manager", t7a.org("/classes"), limit=2, cursor=cursor).json()
        collected.extend(item["class_id"] for item in page["items"])
        cursor = page["next_cursor"]
    assert collected == _db_class_order(t7a)
    assert len(collected) == len(set(collected)) == 7


def test_a07_default_page_is_25_and_the_limit_bounds_are_400(t7a: T7a) -> None:
    _seed_classes(t7a, [BASE_TIME + timedelta(minutes=10 + n) for n in range(24)])
    default = t7a.get("manager", t7a.org("/classes"))
    assert default.status_code == 200, default.text
    body = default.json()
    assert body["contract"] == "Be1ClassListV1"
    assert len(body["items"]) == 25
    assert body["next_cursor"] is not None
    assert set(body["items"][0]) == {
        "class_id",
        "display_name",
        "state",
        "class_revision",
        "assignment_revision",
        "has_active_teacher",
    }
    rest = t7a.get("manager", t7a.org("/classes"), cursor=body["next_cursor"])
    assert len(rest.json()["items"]) == 1
    assert rest.json()["next_cursor"] is None
    assert t7a.get("manager", t7a.org("/classes"), limit=100).status_code == 200
    for bad in (0, 101, -1):
        assert t7a.get("manager", t7a.org("/classes"), limit=bad).status_code == 400
    assert t7a.get("manager", t7a.org("/classes"), cursor="").status_code == 400


def test_a07_rejects_foreign_organization_and_consent_cursors(t7a: T7a) -> None:
    foreign = t7a.get("foreign_manager", t7a.org("/classes", t7a.foreign_organization_id), limit=1)
    assert foreign.status_code == 200, foreign.text
    foreign_cursor = foreign.json()["next_cursor"]
    assert foreign_cursor is not None
    replay = t7a.get("manager", t7a.org("/classes"), cursor=foreign_cursor)
    assert replay.status_code == 400, replay.text
    assert replay.json()["field_errors"] == [{"field": "cursor", "code": "INVALID_FORMAT"}]
    # A cursor of the consents route does not open the class list, nor the other way round.
    _seed_consents(t7a, [BASE_TIME, BASE_TIME + timedelta(minutes=1)])
    consent_page = t7a.get("manager", t7a.class_path("/consents"), limit=1).json()
    assert consent_page["next_cursor"] is not None
    assert (
        t7a.get("manager", t7a.org("/classes"), cursor=consent_page["next_cursor"]).status_code
        == 400
    )
    class_page = t7a.get("manager", t7a.org("/classes"), limit=1).json()
    assert (
        t7a.get(
            "manager", t7a.class_path("/consents"), cursor=class_page["next_cursor"]
        ).status_code
        == 400
    )


def test_crafted_cursors_with_nul_or_noncanonical_form_are_400_not_503(t7a: T7a) -> None:
    # A cursor with the right scope but a NUL in the id or the sort key must be a client error
    # (400), never reach the database (which would answer 503), and the padded or re-spelled
    # form of a genuine cursor is refused too.
    # T-7b: the class cursor scope carries the state filter (default `active`).
    class_scope = f"be1.classes:{t7a.organization_id}:active"
    consent_scope = f"be1.consents:{t7a.organization_id}:{t7a.class_id}"
    targets = (
        (t7a.org("/classes"), class_scope),
        (t7a.class_path("/consents"), consent_scope),
    )
    stamp = BASE_TIME.isoformat()
    for path, scope in targets:
        crafted = (
            encode_cursor(scope=scope, sort_key=stamp, item_id="a\u0000b"),
            encode_cursor(scope=scope, sort_key=stamp + "\u0000", item_id="x"),
            encode_cursor(scope=scope, sort_key=stamp, item_id="café"),
            encode_cursor(scope=scope, sort_key=stamp.replace("+00:00", "Z"), item_id="x"),
        )
        for cursor in crafted:
            response = t7a.get("manager", path, cursor=cursor)
            assert response.status_code == 400, response.text
            assert response.json()["code"] == "INVALID_REQUEST"
            assert response.json()["field_errors"] == [
                {"field": "cursor", "code": "INVALID_FORMAT"}
            ]
    _seed_classes(t7a, [BASE_TIME + timedelta(minutes=n) for n in range(3)])
    genuine = t7a.get("manager", t7a.org("/classes"), limit=1).json()["next_cursor"]
    assert genuine is not None
    assert t7a.get("manager", t7a.org("/classes"), cursor=genuine).status_code == 200
    padded = genuine + "=" * (-len(genuine) % 4 or 1)
    assert t7a.get("manager", t7a.org("/classes"), cursor=padded).status_code == 400


def test_a07_teacher_scope_filter_runs_before_paging(t7a: T7a) -> None:
    page = t7a.get("scoped_teacher", t7a.org("/classes"), limit=1)
    assert page.status_code == 200, page.text
    assert [item["class_id"] for item in page.json()["items"]] == [t7a.class_id]
    assert page.json()["next_cursor"] is None
    assert t7a.get("foreign_teacher", t7a.org("/classes")).status_code == 404


# --- Session roster (T0.11 review P2-1, CM-2) -----------------------------------------------


def test_session_roster_is_403_for_the_manager_and_unchanged_for_the_teacher(t7a: T7a) -> None:
    created = t7a.post(
        "manager",
        t7a.org("/sessions"),
        {"class_id": t7a.class_id, "purpose_ref": "synthetic-roster-purpose", "configuration": {}},
    )
    assert created.status_code == 201, created.text
    session_id = created.json()["session_id"]
    path = t7a.org(f"/sessions/{session_id}/roster")

    manager = t7a.get("manager", path)
    assert manager.status_code == 403, manager.text
    assert manager.json()["code"] == "ACTION_NOT_ALLOWED"
    assert "members" not in manager.json()

    teacher = t7a.get("scoped_teacher", path)
    assert teacher.status_code == 200, teacher.text
    assert set(teacher.json()) == {
        "contract",
        "session_id",
        "session_revision",
        "members",
        "groups",
        "turns",
    }
    assert teacher.json()["contract"] == "Be1SessionRosterV1"
    assert teacher.json()["session_id"] == session_id

    for actor in ("foreign_teacher", "foreign_manager", "other_class_teacher"):
        assert t7a.get(actor, path).status_code == 404, actor
    # guide and observer were refused before this task and stay refused
    assert t7a.get("class_guide", path).status_code == 403
    # T-7a2: an org-wide `teacher` row covers the class but is not the class assignment.
    orgwide = t7a.get("orgwide_teacher", path)
    assert orgwide.status_code == 403, orgwide.text
    assert orgwide.json()["code"] == "ACTION_NOT_ALLOWED"
    assert "members" not in orgwide.json()
