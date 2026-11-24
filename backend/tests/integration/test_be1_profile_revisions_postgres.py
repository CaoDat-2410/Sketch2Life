"""T-12b PostgreSQL acceptance: Teacher profile revisions, history reads and the keyed edit.

SRS l.496-499 (FR-C-04 to FR-C-07), l.829 (head), l.832 (consent covers real data only), l.864-865
(uniform 404), l.1640 (cursor lists), l.1651 and l.1697 (expected revision, keyed commands). Set
``BE1_TEST_DATABASE_URL`` to a disposable database whose name contains ``be1_acceptance``; every
test builds its own organization. Only the external token boundary is substituted: a test header
names the acting adult, and every route, scope query and transaction is real. The migration round
trip needs its own empty database in ``T12B_ROUNDTRIP_DATABASE_URL`` naming a
``frc08_v4_t12b*roundtrip*be1_acceptance`` database.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from threading import Barrier
from typing import Any
from uuid import uuid4

import pytest
from alembic.config import Config
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, func, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import NullPool

from alembic import command
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.domain import be1_profile_revisions as rules
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    Be1CommandReceiptModel,
    Be1ProfileSupportNeedsModel,
    ClassroomModel,
    ConsentRecordModel,
    DataLifecycleRequestModel,
    ManagedProfileModel,
    OrganizationAssignmentModel,
    OrganizationModel,
    ProfileRevisionModel,
)
from sketch2life.infrastructure.persistence.be1_profile_purge import purge_managed_profile
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult
from sketch2life.interfaces.http.routers import be1_registry

BACKEND = Path(__file__).resolve().parents[2]
ISSUER = "synthetic-test-issuer"
ACTOR_HEADER = "X-T12b-Actor"
BASE_TIME = datetime(2026, 3, 1, 8, 0, 0, tzinfo=UTC)
# (actor name, account role, assignment role, scope)
ACTORS = (
    ("manager", "school_manager", "school_admin", "org"),
    ("teacher", "teacher", "teacher", "class"),
    ("other_teacher", "teacher", "teacher", "other"),
    ("suspended_teacher", "teacher", "teacher", "suspended"),
    ("archived_teacher", "teacher", "teacher", "archived"),
    ("orgwide_teacher", "teacher", "teacher", "orgwide"),
    ("foreign_teacher", "teacher", "teacher", "foreign"),
)
NAME = "Synthetic Mina Pham"
NEW_NAME = "Synthetic Linh Tran"
INTEREST = "xếp hình khủng long"


@dataclass
class T12b:
    app: FastAPI
    client: TestClient
    run: str
    organization_id: str
    class_id: str
    other_class_id: str
    suspended_class_id: str
    archived_class_id: str
    foreign_organization_id: str
    subjects: dict[str, str] = field(default_factory=dict)

    @property
    def factory(self) -> Any:
        return self.app.state.be1_runtime.session_factory

    def path(
        self, child_id: str, class_id: str | None = None, organization_id: str | None = None
    ) -> str:
        return (
            f"/api/be1/v1/organizations/{organization_id or self.organization_id}"
            f"/classes/{class_id or self.class_id}/profiles/{child_id}"
        )

    def history(self, actor: str, child_id: str, class_id: str | None = None, **params: Any) -> Any:
        return self.client.get(
            f"{self.path(child_id, class_id)}/revisions",
            params=params or None,
            headers={ACTOR_HEADER: actor},
        )

    def revision(
        self, actor: str, child_id: str, revision_id: str, class_id: str | None = None
    ) -> Any:
        return self.client.get(
            f"{self.path(child_id, class_id)}/revisions/{revision_id}",
            headers={ACTOR_HEADER: actor},
        )

    def edit(
        self,
        actor: str,
        child_id: str,
        body: dict[str, Any],
        *,
        key: str | None = None,
        class_id: str | None = None,
    ) -> Any:
        return self.client.patch(
            self.path(child_id, class_id),
            json=body,
            headers={ACTOR_HEADER: actor, "Idempotency-Key": key or f"k-{uuid4().hex[:12]}"},
        )


def _class(class_id: str, organization_id: str, state: str) -> ClassroomModel:
    return ClassroomModel(
        class_id=class_id,
        organization_id=organization_id,
        display_name=f"Synthetic {class_id}"[:200],
        state=state,
        created_by="synthetic-t12b-seed",
        created_at=BASE_TIME,
    )


@pytest.fixture
def t12b(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> Iterator[T12b]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL to run PostgreSQL-backed T-12b acceptance tests")
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
    organization_id = f"synthetic-t12b-{run}-org"
    foreign_organization_id = f"synthetic-t12b-{run}-foreign"
    class_id = f"synthetic-t12b-{run}-class-a"
    other_class_id = f"synthetic-t12b-{run}-class-b"
    suspended_class_id = f"synthetic-t12b-{run}-class-s"
    archived_class_id = f"synthetic-t12b-{run}-class-x"
    foreign_class_id = f"synthetic-t12b-{run}-foreign-1"
    subjects = {name: f"synthetic-t12b-{run}-{name}" for name, *_rest in ACTORS}
    principals = {
        subject: VerifiedPrincipal(
            subject=subject, issuer=ISSUER, roles=frozenset(), token_id=f"synthetic-t12b-{n}"
        )
        for n, subject in enumerate(subjects.values())
    }
    with runtime.session_factory.begin() as db:
        db.add_all(
            [
                OrganizationModel(
                    organization_id=organization_id,
                    display_name="Synthetic T12b org",
                    state="active",
                ),
                OrganizationModel(
                    organization_id=foreign_organization_id,
                    display_name="Synthetic T12b foreign org",
                    state="active",
                ),
            ]
        )
        db.flush()
        db.add_all(
            [
                _class(class_id, organization_id, "active"),
                _class(other_class_id, organization_id, "active"),
                _class(suspended_class_id, organization_id, "suspended"),
                _class(archived_class_id, organization_id, "archived"),
                _class(foreign_class_id, foreign_organization_id, "active"),
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
        yield T12b(
            app=app,
            client=client,
            run=run,
            organization_id=organization_id,
            class_id=class_id,
            other_class_id=other_class_id,
            suspended_class_id=suspended_class_id,
            archived_class_id=archived_class_id,
            foreign_organization_id=foreign_organization_id,
            subjects=subjects,
        )
    app.dependency_overrides.clear()
    runtime.engine.dispose()
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()


def _profile(
    t: T12b,
    suffix: str,
    *,
    origin: str = "SYNTHETIC_DEV",
    age: int = 60,
    class_id: str | None = None,
    state: str = "active",
    name: str = NAME,
) -> str:
    child_id = f"synthetic-t12b-{t.run}-{suffix}"
    real = origin == "REAL"
    with t.factory.begin() as db:
        db.add(
            ManagedProfileModel(
                child_id=child_id,
                organization_id=t.organization_id,
                class_id=class_id or t.class_id,
                display_name=name,
                age_months=age,
                age_revision=1,
                age_source="SYNTHETIC_FIXTURE" if origin == "SYNTHETIC_DEV" else "ADULT_DECLARED",
                consent_id=str(uuid4()) if real else None,
                consent_purpose_ref=f"synthetic-purpose-{suffix}" if real else None,
                data_origin=origin,
                state=state,
                created_by=t.subjects["manager"],
                created_at=BASE_TIME,
            )
        )
    return child_id


def _revisions(t: T12b, child_id: str) -> list[ProfileRevisionModel]:
    with t.factory() as db:
        return list(
            db.scalars(
                select(ProfileRevisionModel)
                .where(ProfileRevisionModel.child_id == child_id)
                .order_by(ProfileRevisionModel.revision_no)
            )
        )


def _profile_row(t: T12b, child_id: str) -> ManagedProfileModel:
    with t.factory() as db:
        row = db.get(ManagedProfileModel, child_id)
        assert row is not None
        db.expunge(row)
        return row


def _receipts(t: T12b) -> list[Be1CommandReceiptModel]:
    with t.factory() as db:
        return list(
            db.scalars(
                select(Be1CommandReceiptModel).where(
                    Be1CommandReceiptModel.organization_id == t.organization_id
                )
            )
        )


def _audits(t: T12b, action: str) -> list[CoreAuditEntryModel]:
    with t.factory() as db:
        return list(
            db.scalars(
                select(CoreAuditEntryModel).where(
                    CoreAuditEntryModel.organization_id == t.organization_id,
                    CoreAuditEntryModel.action == action,
                )
            )
        )


def _code(response: Any) -> str:
    return str(response.json().get("code"))


# --- the writers -------------------------------------------------------------------------------


def test_an_orm_insert_writes_revision_one_and_the_head_in_one_flush(t12b: T12b) -> None:
    child = _profile(t12b, "orm")
    revisions = _revisions(t12b, child)
    assert [r.revision_no for r in revisions] == [1]
    row = _profile_row(t12b, child)
    assert row.current_profile_revision_id == revisions[0].profile_revision_id
    assert row.profile_revision_no == 1
    assert revisions[0].authored_by == t12b.subjects["manager"]
    assert revisions[0].revision_hash == rules.revision_hash(
        child_id=child, revision_no=1, display_name=NAME, age_months=60, structured_interests=[]
    )
    assert (revisions[0].age_band_version, revisions[0].age_band_code) == (1, "AGE_36_71")


def test_the_create_route_writes_revision_one_and_the_head(t12b: T12b) -> None:
    created = t12b.client.post(
        f"/api/be1/v1/organizations/{t12b.organization_id}/classes/{t12b.class_id}/profiles",
        json={"display_name": "Synthetic Route Child", "age_months": 84},
        headers={ACTOR_HEADER: "teacher", "Idempotency-Key": "create-1", "If-Match": '"1"'},
    )
    assert created.status_code == 201, created.text
    child = created.json()["child_id"]
    revisions = _revisions(t12b, child)
    assert [(r.revision_no, r.display_name, r.age_months) for r in revisions] == [
        (1, "Synthetic Route Child", 84)
    ]
    assert revisions[0].authored_by == t12b.subjects["teacher"]
    assert (revisions[0].age_band_code) == "AGE_72_107"
    row = _profile_row(t12b, child)
    assert (row.current_profile_revision_id, row.profile_revision_no) == (
        revisions[0].profile_revision_id,
        1,
    )
    page = t12b.history("teacher", child)
    assert page.status_code == 200 and [i["revision_no"] for i in page.json()["items"]] == [1]


# --- the edit ----------------------------------------------------------------------------------


def test_an_edit_appends_one_revision_moves_the_head_and_the_projection(t12b: T12b) -> None:
    child = _profile(t12b, "edit")
    first = t12b.history("teacher", child).json()["items"][0]
    assert first["revision_no"] == 1
    response = t12b.edit(
        "teacher",
        child,
        {
            "expected_revision": 1,
            "display_name": NEW_NAME,
            "age_months": 75,
            "structured_interests": [INTEREST, "vẽ tranh"],
        },
    )
    assert response.status_code == 200, response.text
    assert response.headers["ETag"] == '"2"'
    body = response.json()
    assert set(body) == {
        "contract",
        "child_id",
        "profile_revision_id",
        "revision_no",
        "revision_hash",
    }
    assert body["contract"] == "Be1ProfileEditResultV1" and body["revision_no"] == 2
    revisions = _revisions(t12b, child)
    assert [r.revision_no for r in revisions] == [1, 2]
    new = revisions[1]
    assert new.profile_revision_id == body["profile_revision_id"]
    assert (new.display_name, new.age_months, new.structured_interests) == (
        NEW_NAME,
        75,
        [INTEREST, "vẽ tranh"],
    )
    assert (new.age_band_version, new.age_band_code) == (1, "AGE_72_107")
    assert new.authored_by == t12b.subjects["teacher"]
    assert (
        new.revision_hash
        == body["revision_hash"]
        == rules.revision_hash(
            child_id=child,
            revision_no=2,
            display_name=NEW_NAME,
            age_months=75,
            structured_interests=[INTEREST, "vẽ tranh"],
        )
    )
    row = _profile_row(t12b, child)
    assert (row.display_name, row.age_months, row.age_revision) == (NEW_NAME, 75, 2)
    assert (row.current_profile_revision_id, row.profile_revision_no) == (
        new.profile_revision_id,
        2,
    )
    assert len(_receipts(t12b)) == 1
    assert [a.resource_id for a in _audits(t12b, "profile.edit")] == [child]
    # the old revision is untouched
    assert (revisions[0].display_name, revisions[0].age_months) == (NAME, 60)


def test_the_age_revision_moves_only_when_the_age_changes(t12b: T12b) -> None:
    child = _profile(t12b, "agerev")
    assert (
        t12b.edit("teacher", child, {"expected_revision": 1, "display_name": NEW_NAME}).status_code
        == 200
    )
    assert _profile_row(t12b, child).age_revision == 1
    assert (
        t12b.edit("teacher", child, {"expected_revision": 2, "age_months": 60}).status_code == 200
    )
    assert _profile_row(t12b, child).age_revision == 1  # same age sent again: no age change
    assert (
        t12b.edit("teacher", child, {"expected_revision": 3, "age_months": 61}).status_code == 200
    )
    assert _profile_row(t12b, child).age_revision == 2
    assert (
        t12b.edit(
            "teacher", child, {"expected_revision": 4, "structured_interests": []}
        ).status_code
        == 200
    )
    row = _profile_row(t12b, child)
    assert (row.age_revision, row.profile_revision_no) == (2, 5)


def test_an_omitted_field_keeps_its_value_and_an_empty_list_clears_the_interests(
    t12b: T12b,
) -> None:
    child = _profile(t12b, "merge")
    assert (
        t12b.edit(
            "teacher", child, {"expected_revision": 1, "structured_interests": ["vẽ"]}
        ).status_code
        == 200
    )
    assert (
        t12b.edit("teacher", child, {"expected_revision": 2, "age_months": 70}).status_code == 200
    )
    revisions = _revisions(t12b, child)
    assert revisions[2].structured_interests == ["vẽ"] and revisions[2].display_name == NAME
    assert (
        t12b.edit(
            "teacher", child, {"expected_revision": 3, "structured_interests": []}
        ).status_code
        == 200
    )
    assert _revisions(t12b, child)[3].structured_interests == []


def test_a_stale_expected_revision_is_409_with_the_current_version_and_writes_nothing(
    t12b: T12b,
) -> None:
    child = _profile(t12b, "stale")
    assert (
        t12b.edit("teacher", child, {"expected_revision": 1, "age_months": 70}).status_code == 200
    )
    stale = t12b.edit("teacher", child, {"expected_revision": 1, "age_months": 80})
    assert stale.status_code == 409 and _code(stale) == "STALE_REVISION"
    assert stale.json()["current_version"] == 2 and stale.headers["ETag"] == '"2"'
    ahead = t12b.edit("teacher", child, {"expected_revision": 9, "age_months": 80})
    assert ahead.status_code == 409 and ahead.json()["current_version"] == 2
    assert [r.revision_no for r in _revisions(t12b, child)] == [1, 2]
    assert len(_receipts(t12b)) == 1  # only the first edit


def test_an_exact_replay_returns_the_first_answer_and_a_changed_request_is_400(
    t12b: T12b,
) -> None:
    child = _profile(t12b, "replay")
    body = {"expected_revision": 1, "display_name": NEW_NAME, "structured_interests": [INTEREST]}
    first = t12b.edit("teacher", child, body, key="same-key")
    replay = t12b.edit("teacher", child, body, key="same-key")
    assert first.status_code == replay.status_code == 200
    assert first.json() == replay.json() and replay.headers["ETag"] == '"2"'
    assert len(_revisions(t12b, child)) == 2 and len(_receipts(t12b)) == 1
    for changed in (
        {**body, "display_name": "Synthetic Other Name"},
        {**body, "structured_interests": []},
        {**body, "expected_revision": 2},
        {"expected_revision": 1, "display_name": NEW_NAME},
    ):
        mismatch = t12b.edit("teacher", child, changed, key="same-key")
        assert mismatch.status_code == 400 and _code(mismatch) == "INVALID_IDEMPOTENCY_KEY", changed
    assert len(_revisions(t12b, child)) == 2


def test_a_key_reused_on_another_profile_discloses_nothing_and_is_a_new_command(
    t12b: T12b,
) -> None:
    one, two = _profile(t12b, "key-a"), _profile(t12b, "key-b")
    first = t12b.edit("teacher", one, {"expected_revision": 1, "age_months": 70}, key="shared")
    second = t12b.edit("teacher", two, {"expected_revision": 1, "age_months": 70}, key="shared")
    assert first.status_code == second.status_code == 200
    assert first.json()["child_id"] == one and second.json()["child_id"] == two
    assert len(_receipts(t12b)) == 2


def test_the_receipt_and_the_audit_row_hold_no_child_value(t12b: T12b) -> None:
    child = _profile(t12b, "nodata")
    assert (
        t12b.edit(
            "teacher",
            child,
            {"expected_revision": 1, "display_name": NEW_NAME, "structured_interests": [INTEREST]},
        ).status_code
        == 200
    )
    (receipt,) = _receipts(t12b)
    assert set(receipt.response_json) == {"profile_revision_id", "fp_v", "fp_kid"}
    assert len(receipt.request_fingerprint) == 64
    dump = repr(receipt.__dict__) + repr(receipt.response_json)
    for secret in (NEW_NAME, "Linh", INTEREST, "khủng long"):
        assert secret not in dump
    for audit in _audits(t12b, "profile.edit"):
        assert NEW_NAME not in repr(audit.__dict__) and INTEREST not in repr(audit.__dict__)


def test_two_keys_on_one_head_one_wins_and_one_is_stale(t12b: T12b) -> None:
    child = _profile(t12b, "race")
    barrier = Barrier(2)

    def call(n: int) -> Any:
        barrier.wait()
        return t12b.edit(
            "teacher", child, {"expected_revision": 1, "age_months": 70 + n}, key=f"race-{n}"
        )

    with ThreadPoolExecutor(2) as pool:
        statuses = sorted(r.status_code for r in pool.map(call, range(2)))
    assert statuses == [200, 409]
    assert [r.revision_no for r in _revisions(t12b, child)] == [1, 2]


def test_the_same_key_concurrent_commits_one_revision_and_every_caller_gets_the_answer(
    t12b: T12b,
) -> None:
    child = _profile(t12b, "same")
    barrier = Barrier(4)

    def call(_: int) -> Any:
        barrier.wait()
        return t12b.edit(
            "teacher",
            child,
            {"expected_revision": 1, "structured_interests": [INTEREST]},
            key="concurrent-1",
        )

    with ThreadPoolExecutor(4) as pool:
        responses = list(pool.map(call, range(4)))
    assert [r.status_code for r in responses] == [200] * 4
    assert len({r.json()["profile_revision_id"] for r in responses}) == 1
    assert [r.revision_no for r in _revisions(t12b, child)] == [1, 2]
    assert len(_receipts(t12b)) == 1


def test_a_failure_in_the_transaction_rolls_back_the_revision_projection_and_receipt(
    t12b: T12b, monkeypatch: pytest.MonkeyPatch
) -> None:
    child = _profile(t12b, "rollback")

    def boom(*_a: Any, **_k: Any) -> None:
        raise RuntimeError("synthetic failure after the revision was staged")

    monkeypatch.setattr(be1_registry, "audit", boom)
    with pytest.raises(RuntimeError, match="synthetic failure"):
        t12b.edit(
            "teacher", child, {"expected_revision": 1, "display_name": NEW_NAME, "age_months": 90}
        )
    assert [r.revision_no for r in _revisions(t12b, child)] == [1]
    row = _profile_row(t12b, child)
    assert (row.display_name, row.age_months, row.age_revision, row.profile_revision_no) == (
        NAME,
        60,
        1,
        1,
    )
    assert _receipts(t12b) == []


def test_a_long_scope_is_hashed_to_fit_the_receipt_column(t12b: T12b) -> None:
    organization_id, class_id, child_id = (f"{c}{'o' * 120}" for c in ("a-", "b-", "c-"))
    with t12b.factory.begin() as db:
        db.add(
            OrganizationModel(
                organization_id=organization_id, display_name="Synthetic L", state="active"
            )
        )
        db.flush()
        db.add(_class(class_id, organization_id, "active"))
        db.flush()
        db.add(
            OrganizationAssignmentModel(
                assignment_id=str(uuid4()),
                organization_id=organization_id,
                subject=t12b.subjects["teacher"],
                class_id=class_id,
                role="teacher",
                active=True,
            )
        )
        db.add(
            ManagedProfileModel(
                child_id=child_id,
                organization_id=organization_id,
                class_id=class_id,
                display_name=NAME,
                age_months=60,
                age_source="SYNTHETIC_FIXTURE",
                data_origin="SYNTHETIC_DEV",
                created_by="synthetic-t12b-seed",
            )
        )
    response = t12b.client.patch(
        t12b.path(child_id, class_id, organization_id),
        json={"expected_revision": 1, "age_months": 61},
        headers={ACTOR_HEADER: "teacher", "Idempotency-Key": "long-1"},
    )
    assert response.status_code == 200, response.text
    with t12b.factory() as db:
        scopes = list(
            db.scalars(
                select(Be1CommandReceiptModel.operation_scope).where(
                    Be1CommandReceiptModel.organization_id == organization_id
                )
            )
        )
    assert len(scopes) == 1 and len(scopes[0]) <= 256 and "#" in scopes[0]
    replay = t12b.client.patch(
        t12b.path(child_id, class_id, organization_id),
        json={"expected_revision": 1, "age_months": 61},
        headers={ACTOR_HEADER: "teacher", "Idempotency-Key": "long-1"},
    )
    assert replay.status_code == 200 and replay.json() == response.json()


# --- the history -------------------------------------------------------------------------------


def test_the_history_pages_newest_first_and_the_cursor_is_bound_to_the_profile(
    t12b: T12b,
) -> None:
    child, other = _profile(t12b, "page-a"), _profile(t12b, "page-b")
    for revision in range(1, 6):
        assert (
            t12b.edit(
                "teacher", child, {"expected_revision": revision, "age_months": 60 + revision}
            ).status_code
            == 200
        )
    seen: list[int] = []
    cursor: str | None = None
    pages = 0
    while True:
        params: dict[str, Any] = {"limit": 2}
        if cursor is not None:
            params["cursor"] = cursor
        page = t12b.history("teacher", child, **params)
        assert page.status_code == 200, page.text
        body = page.json()
        assert body["contract"] == "Be1ProfileRevisionPageV1" and len(body["items"]) <= 2
        seen.extend(item["revision_no"] for item in body["items"])
        pages += 1
        cursor = body["next_cursor"]
        if cursor is None:
            break
        stolen = t12b.history("teacher", other, cursor=cursor)
        assert stolen.status_code == 400 and stolen.json()["field_errors"][0]["field"] == "cursor"
    assert seen == [6, 5, 4, 3, 2, 1] and pages == 3
    assert t12b.history("teacher", child, limit=101).status_code == 400
    assert t12b.history("teacher", child, limit=0).status_code == 400
    assert t12b.history("teacher", child, cursor="not-a-cursor").status_code == 400
    first_page = t12b.history("teacher", child, limit=2).json()
    assert (
        t12b.history("teacher", child, limit=2, cursor=first_page["next_cursor"] + "x").status_code
        == 400
    )
    default = t12b.history("teacher", child).json()
    assert len(default["items"]) == 6 and default["next_cursor"] is None


def test_one_revision_has_the_full_shape_and_no_author(t12b: T12b) -> None:
    child = _profile(t12b, "shape")
    assert (
        t12b.edit(
            "teacher", child, {"expected_revision": 1, "structured_interests": [INTEREST]}
        ).status_code
        == 200
    )
    items = t12b.history("teacher", child).json()["items"]
    head = items[0]
    assert set(head) == {
        "contract",
        "child_id",
        "profile_revision_id",
        "revision_no",
        "display_name",
        "age_months",
        "age_band",
        "structured_interests",
        "revision_hash",
        "created_at",
    }
    assert head["age_band"] == {"band_version": 1, "band_code": "AGE_36_71"}
    one = t12b.revision("teacher", child, head["profile_revision_id"])
    assert one.status_code == 200 and one.json() == head
    assert datetime.fromisoformat(head["created_at"]).tzinfo is not None
    missing = t12b.revision("teacher", child, str(uuid4()))
    assert missing.status_code == 404 and _code(missing) == "RESOURCE_NOT_FOUND"
    other = _profile(t12b, "shape-other")
    foreign = t12b.revision("teacher", other, head["profile_revision_id"])
    assert foreign.status_code == 404  # a revision of another profile


# --- scope and authorization -------------------------------------------------------------------


def test_scope_denials_are_the_uniform_404_and_a_manager_is_403(t12b: T12b) -> None:
    child = _profile(t12b, "scope")
    body = {"expected_revision": 1, "age_months": 70}
    for actor in ("other_teacher", "foreign_teacher", "orgwide_teacher"):
        assert t12b.history(actor, child).status_code == 404, actor
        assert t12b.revision(actor, child, str(uuid4())).status_code == 404, actor
        denied = t12b.edit(actor, child, body)
        assert denied.status_code == 404 and _code(denied) == "RESOURCE_NOT_FOUND", actor
    for call in (
        t12b.history("manager", child),
        t12b.revision("manager", child, str(uuid4())),
        t12b.edit("manager", child, body),
    ):
        assert call.status_code == 403 and _code(call) == "ACTION_NOT_ALLOWED"
    # an unknown class, a profile of another class of the organization, an unknown child
    assert t12b.history("teacher", child, class_id="synthetic-no-such-class").status_code == 404
    elsewhere = _profile(t12b, "elsewhere", class_id=t12b.other_class_id)
    assert t12b.history("teacher", elsewhere).status_code == 404
    assert t12b.edit("teacher", elsewhere, body).status_code == 404
    assert t12b.history("teacher", f"synthetic-t12b-{t12b.run}-ghost").status_code == 404
    assert t12b.edit("teacher", f"synthetic-t12b-{t12b.run}-ghost", body).status_code == 404
    assert [r.revision_no for r in _revisions(t12b, child)] == [1]
    assert _receipts(t12b) == []


def test_an_inactive_profile_is_the_uniform_404(t12b: T12b) -> None:
    child = _profile(t12b, "inactive", state="archived")
    assert t12b.history("teacher", child).status_code == 404
    assert (
        t12b.edit("teacher", child, {"expected_revision": 1, "age_months": 70}).status_code == 404
    )


def test_a_revoked_assignment_is_refused_and_a_replay_is_not_served(t12b: T12b) -> None:
    child = _profile(t12b, "revoked")
    body = {"expected_revision": 1, "age_months": 70}
    assert t12b.edit("teacher", child, body, key="before-revoke").status_code == 200
    with t12b.factory.begin() as db:
        db.execute(
            update(OrganizationAssignmentModel)
            .where(OrganizationAssignmentModel.subject == t12b.subjects["teacher"])
            .values(active=False)
        )
    for denied in (
        t12b.edit("teacher", child, body, key="before-revoke"),
        t12b.history("teacher", child),
        t12b.revision("teacher", child, str(uuid4())),
    ):
        assert denied.status_code == 404
    assert len(_revisions(t12b, child)) == 2


# --- the release predicate (option B of D-066-100) -----------------------------------------------


def test_a_legacy_unclassified_profile_is_refused_for_read_and_write_and_audited(
    t12b: T12b,
) -> None:
    child = _profile(t12b, "legacy", origin="LEGACY_UNCLASSIFIED")
    body = {"expected_revision": 1, "age_months": 70}
    for call in (
        t12b.history("teacher", child),
        t12b.revision("teacher", child, str(uuid4())),
        t12b.edit("teacher", child, body),
    ):
        assert call.status_code == 409 and _code(call) == "CONSENT_NOT_EFFECTIVE"
    assert len(_audits(t12b, "profile.revisions.read")) == 2
    assert len(_audits(t12b, "profile.edit")) == 1
    assert {a.decision for a in _audits(t12b, "profile.edit")} == {"denied_consent_pending"}
    assert len(_revisions(t12b, child)) == 1 and _receipts(t12b) == []


def test_a_real_profile_without_an_effective_consent_is_refused(t12b: T12b) -> None:
    child = _profile(t12b, "real-none", origin="REAL")
    assert t12b.history("teacher", child).status_code == 409
    refused = t12b.edit("teacher", child, {"expected_revision": 1, "age_months": 70})
    assert refused.status_code == 409 and _code(refused) == "CONSENT_NOT_EFFECTIVE"


def test_a_real_profile_with_an_effective_consent_is_readable_but_its_write_stays_blocked(
    t12b: T12b, monkeypatch: pytest.MonkeyPatch
) -> None:
    child = _profile(t12b, "real-eff", origin="REAL")
    monkeypatch.setattr(be1_registry, "consent_is_effective", lambda *a, **k: True)
    page = t12b.history("teacher", child)
    assert page.status_code == 200 and len(page.json()["items"]) == 1
    blocked = t12b.edit("teacher", child, {"expected_revision": 1, "age_months": 70})
    assert blocked.status_code == 409 and _code(blocked) == "CONSENT_NOT_EFFECTIVE"
    assert len(_revisions(t12b, child)) == 1 and _receipts(t12b) == []


def test_a_suspended_class_is_readable_but_read_only_and_an_archived_one_is_gone(
    t12b: T12b,
) -> None:
    child = _profile(t12b, "susp", class_id=t12b.suspended_class_id)
    assert (
        t12b.history("suspended_teacher", child, class_id=t12b.suspended_class_id).status_code
        == 200
    )
    refused = t12b.edit(
        "suspended_teacher",
        child,
        {"expected_revision": 1, "age_months": 70},
        class_id=t12b.suspended_class_id,
    )
    assert refused.status_code == 409 and _code(refused) == "INVALID_STATE_TRANSITION"
    gone = _profile(t12b, "arch", class_id=t12b.archived_class_id)
    assert (
        t12b.history("archived_teacher", gone, class_id=t12b.archived_class_id).status_code == 404
    )
    write = t12b.edit(
        "archived_teacher",
        gone,
        {"expected_revision": 1, "age_months": 70},
        class_id=t12b.archived_class_id,
    )
    assert write.status_code == 409 and _code(write) == "INVALID_STATE_TRANSITION"
    assert len(_revisions(t12b, child)) == 1 and len(_revisions(t12b, gone)) == 1


def test_a_legacy_over_age_profile_is_readable_with_no_band_and_refuses_an_edit(
    t12b: T12b,
) -> None:
    child = _profile(t12b, "over", age=130)
    page = t12b.history("teacher", child)
    assert page.status_code == 200
    item = page.json()["items"][0]
    assert item["age_months"] == 130 and item["age_band"] is None
    refused = t12b.edit("teacher", child, {"expected_revision": 1, "display_name": NEW_NAME})
    assert refused.status_code == 409 and _code(refused) == "INVALID_STATE_TRANSITION"
    assert len(_revisions(t12b, child)) == 1


def test_an_invalid_body_is_a_400_before_any_write(t12b: T12b) -> None:
    child = _profile(t12b, "bad")
    for body in (
        {"expected_revision": 1},
        {"age_months": 70},
        {"expected_revision": 1, "age_months": 121},
        {"expected_revision": 1, "display_name": "Mina Pham"},
        {"expected_revision": 1, "structured_interests": ["a", "a"]},
        {"expected_revision": 1, "age_months": 70, "child_id": "x"},
        {"expected_revision": 1, "age_months": None},
    ):
        response = t12b.edit("teacher", child, body)
        assert response.status_code == 400 and _code(response) == "INVALID_REQUEST", body
    missing_key = t12b.client.patch(
        t12b.path(child),
        json={"expected_revision": 1, "age_months": 70},
        headers={ACTOR_HEADER: "teacher"},
    )
    assert missing_key.status_code == 400
    assert len(_revisions(t12b, child)) == 1 and _receipts(t12b) == []


# --- the database guarantees -------------------------------------------------------------------


def test_a_revision_is_append_only(t12b: T12b) -> None:
    child = _profile(t12b, "append")
    with pytest.raises(IntegrityError), t12b.factory.begin() as db:
        db.execute(
            text(
                "UPDATE be1_profile_revisions SET display_name = 'Synthetic Z' WHERE child_id = :c"
            ),
            {"c": child},
        )
    with pytest.raises(IntegrityError), t12b.factory.begin() as db:
        db.execute(text("DELETE FROM be1_profile_revisions WHERE child_id = :c"), {"c": child})
    assert _revisions(t12b, child)[0].display_name == NAME


def test_the_profile_with_a_revision_cannot_be_deleted(t12b: T12b) -> None:
    child = _profile(t12b, "restrict")
    with pytest.raises(IntegrityError), t12b.factory.begin() as db:
        db.execute(text("DELETE FROM be1_managed_profiles WHERE child_id = :c"), {"c": child})


def test_the_head_cannot_point_at_another_childs_revision_or_a_wrong_number(t12b: T12b) -> None:
    one, two = _profile(t12b, "head-a"), _profile(t12b, "head-b")
    other_revision = _revisions(t12b, two)[0].profile_revision_id
    with pytest.raises(IntegrityError), t12b.factory.begin() as db:
        db.execute(
            text(
                "UPDATE be1_managed_profiles SET current_profile_revision_id = :r "
                "WHERE child_id = :c"
            ),
            {"r": other_revision, "c": one},
        )
    with pytest.raises(IntegrityError), t12b.factory.begin() as db:
        db.execute(
            text("UPDATE be1_managed_profiles SET profile_revision_no = 5 WHERE child_id = :c"),
            {"c": one},
        )
    with pytest.raises(IntegrityError), t12b.factory.begin() as db:
        db.execute(
            text("UPDATE be1_managed_profiles SET profile_revision_no = 0 WHERE child_id = :c"),
            {"c": one},
        )
    row = _profile_row(t12b, one)
    assert row.profile_revision_no == 1


def test_a_new_revision_without_a_head_move_is_refused_at_commit(t12b: T12b) -> None:
    child = _profile(t12b, "orphan")
    with pytest.raises(IntegrityError), t12b.factory.begin() as db:
        db.add(
            ProfileRevisionModel(
                profile_revision_id=str(uuid4()),
                child_id=child,
                revision_no=2,
                display_name=NAME,
                age_months=60,
                age_band_version=1,
                age_band_code="AGE_36_71",
                structured_interests=[],
                authored_by="synthetic-t12b-seed",
                revision_hash_version=1,
                revision_hash="0" * 64,
            )
        )
    assert [r.revision_no for r in _revisions(t12b, child)] == [1]


def test_the_database_checks_refuse_a_wrong_band_and_an_oversized_interest_list(
    t12b: T12b,
) -> None:
    child = _profile(t12b, "checks")
    with pytest.raises(IntegrityError), t12b.factory.begin() as db:
        db.add(
            ProfileRevisionModel(
                profile_revision_id=str(uuid4()),
                child_id=child,
                revision_no=2,
                display_name=NAME,
                age_months=60,
                age_band_version=1,
                age_band_code="AGE_72_107",  # the age says 36-71
                structured_interests=[],
                authored_by="x",
                revision_hash_version=1,
                revision_hash="0" * 64,
            )
        )
    with pytest.raises(IntegrityError), t12b.factory.begin() as db:
        db.add(
            ProfileRevisionModel(
                profile_revision_id=str(uuid4()),
                child_id=child,
                revision_no=2,
                display_name=NAME,
                age_months=60,
                age_band_version=1,
                age_band_code="AGE_36_71",
                structured_interests=["x" * 80] * 120,  # above 8192 octets
                authored_by="x",
                revision_hash_version=1,
                revision_hash="0" * 64,
            )
        )
    with pytest.raises(IntegrityError), t12b.factory.begin() as db:
        db.add(
            ProfileRevisionModel(
                profile_revision_id=str(uuid4()),
                child_id=child,
                revision_no=2,
                display_name=NAME,
                age_months=60,
                age_band_version=1,
                age_band_code="AGE_36_71",
                structured_interests=[],
                authored_by="x",
                revision_hash_version=1,
                revision_hash="NOT-A-HASH",
            )
        )
    assert [r.revision_no for r in _revisions(t12b, child)] == [1]


def test_the_profile_move_changes_no_revision(t12b: T12b) -> None:
    child = _profile(t12b, "move")
    with t12b.factory.begin() as db:
        profile = db.get(ManagedProfileModel, child)
        assert profile is not None
        profile.class_id = t12b.other_class_id
    assert [r.revision_no for r in _revisions(t12b, child)] == [1]
    assert _profile_row(t12b, child).profile_revision_no == 1


def test_the_count_of_revisions_equals_the_profiles_after_writers_ran(t12b: T12b) -> None:
    children = [_profile(t12b, f"count-{n}") for n in range(3)]
    with t12b.factory() as db:
        revisions = db.scalar(
            select(func.count())
            .select_from(ProfileRevisionModel)
            .where(ProfileRevisionModel.child_id.in_(children))
        )
        heads = db.scalar(
            select(func.count())
            .select_from(ManagedProfileModel)
            .where(
                ManagedProfileModel.child_id.in_(children),
                ManagedProfileModel.current_profile_revision_id.is_not(None),
            )
        )
    assert revisions == heads == 3


# ============================================================================= the round trip
@pytest.fixture
def roundtrip(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[Config, Engine]]:
    url = os.environ.get("T12B_ROUNDTRIP_DATABASE_URL")
    if not url:
        pytest.skip(
            "set T12B_ROUNDTRIP_DATABASE_URL to a disposable round-trip PostgreSQL database"
        )
    name = url.rsplit("/", 1)[-1]
    if not all(part in name for part in ("be1_acceptance", "frc08_v4_t12b", "roundtrip")):
        pytest.fail(
            "T12B_ROUNDTRIP_DATABASE_URL must name a frc08_v4_t12b*roundtrip*be1_acceptance db"
        )
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", url)
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    config = Config(str(BACKEND / "alembic.ini"))
    engine = create_engine(url, poolclass=NullPool)
    try:
        yield config, engine
    finally:
        engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def test_the_migration_backfills_refuses_an_unreconciled_baseline_and_guards_the_downgrade(
    roundtrip: tuple[Config, Engine],
) -> None:
    config, engine = roundtrip
    parent, head = "20261123_rv_0001", "20261121_bpr_0001"
    live = "20261123_ppg_0001"  # T-12c and the T-12b-fix purge sit on it; `upgrade heads` leaves it

    def versions() -> set[str]:
        with engine.connect() as connection:
            return {
                str(v) for v in connection.scalars(text("SELECT version_num FROM alembic_version"))
            }

    def has_table() -> bool:
        with engine.connect() as connection:
            return bool(
                connection.scalar(text("SELECT to_regclass('public.be1_profile_revisions')"))
            )

    def has_column() -> bool:
        with engine.connect() as connection:
            return bool(
                connection.scalar(
                    text(
                        "SELECT count(*) FROM information_schema.columns WHERE table_name = "
                        "'be1_managed_profiles' AND column_name = 'profile_revision_no'"
                    )
                )
            )

    command.upgrade(config, "heads")
    assert live in versions() and has_table() and has_column()
    command.downgrade(config, parent)  # empty database: the guard passes
    assert not has_table() and not has_column() and parent in versions()

    org, cls = "synthetic-t12b-rt-org", "synthetic-t12b-rt-class"
    rows = (
        ("synthetic-t12b-rt-1", 60, "SYNTHETIC_DEV", "Synthetic Một"),
        ("synthetic-t12b-rt-2", 100, "SYNTHETIC_DEV", "Synthetic Hai"),
        ("synthetic-t12b-rt-3", 130, "LEGACY_UNCLASSIFIED", "Old Legacy Three"),
    )
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO be1_organizations (organization_id, display_name, state) "
                "VALUES (:o, 'Synthetic RT', 'active')"
            ),
            {"o": org},
        )
        connection.execute(
            text(
                "INSERT INTO be1_classrooms (class_id, organization_id, display_name, state, "
                "created_by) VALUES (:c, :o, 'Synthetic RT class', 'active', 'x')"
            ),
            {"c": cls, "o": org},
        )
        for child, age, origin, name in rows:
            connection.execute(
                text(
                    "INSERT INTO be1_managed_profiles (child_id, organization_id, class_id, "
                    "display_name, age_months, age_revision, age_source, data_origin, state, "
                    "created_by) VALUES (:i, :o, :c, :n, :a, 1, 'LEGACY_UNKNOWN', :g, "
                    "'active', 'x')"
                ),
                {"i": child, "o": org, "c": cls, "n": name, "a": age, "g": origin},
            )
        # an unreconcilable row: an empty name cannot become a revision
        connection.execute(
            text(
                "INSERT INTO be1_managed_profiles (child_id, organization_id, class_id, "
                "display_name, age_months, age_revision, age_source, data_origin, state, "
                "created_by) VALUES ('synthetic-t12b-rt-bad', :o, :c, '', 60, 1, "
                "'LEGACY_UNKNOWN', 'LEGACY_UNCLASSIFIED', 'active', 'x')"
            ),
            {"o": org, "c": cls},
        )
    with pytest.raises(Exception):  # noqa: B017,PT011 - the CHECK of the revision table aborts it
        command.upgrade(config, head)
    assert not has_table() and not has_column() and parent in versions()  # DDL rolled back
    with engine.begin() as connection:
        connection.execute(
            text("DELETE FROM be1_managed_profiles WHERE child_id = 'synthetic-t12b-rt-bad'")
        )

    command.upgrade(config, head)
    assert head in versions() and has_table() and has_column()
    with engine.connect() as connection:
        revisions = connection.execute(
            text(
                "SELECT r.child_id, r.revision_no, r.display_name, r.age_months, "
                "r.age_band_code, r.structured_interests, r.authored_by, r.revision_hash, "
                "r.profile_revision_id, p.created_at = r.created_at AS same_time, "
                "p.current_profile_revision_id, p.profile_revision_no, p.display_name AS pname "
                "FROM be1_profile_revisions r JOIN be1_managed_profiles p USING (child_id) "
                "ORDER BY r.child_id"
            )
        ).all()
        nullable = connection.execute(
            text(
                "SELECT column_name, is_nullable FROM information_schema.columns WHERE "
                "table_name = 'be1_managed_profiles' AND column_name IN "
                "('current_profile_revision_id', 'profile_revision_no')"
            )
        ).all()
    assert len(revisions) == 3 and {r.is_nullable for r in nullable} == {"NO"}
    for row, (child, age, _origin, name) in zip(revisions, rows, strict=True):
        assert (row.child_id, row.revision_no, row.age_months, row.display_name) == (
            child,
            1,
            age,
            name,
        )
        assert row.pname == name and row.profile_revision_no == 1
        assert row.current_profile_revision_id == row.profile_revision_id
        assert row.profile_revision_id == rules.baseline_revision_id(child)
        assert row.structured_interests == [] and row.authored_by == rules.LEGACY_AUTHOR
        assert row.same_time is True
        assert row.revision_hash == rules.revision_hash(
            child_id=child,
            revision_no=1,
            display_name=name,
            age_months=age,
            structured_interests=[],
        )
    assert [r.age_band_code for r in revisions] == ["AGE_36_71", "AGE_72_107", None]

    # a baseline-only database goes down and comes back identical
    command.downgrade(config, parent)
    assert not has_table() and not has_column()
    command.upgrade(config, "heads")
    assert live in versions() and has_table()

    # a profile created after the migration (a real author) blocks the downgrade
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO be1_managed_profiles (child_id, organization_id, class_id, "
                "display_name, age_months, age_revision, age_source, data_origin, state, "
                "created_by, current_profile_revision_id, profile_revision_no) VALUES "
                "('synthetic-t12b-rt-api', :o, :c, 'Synthetic Api', 60, 1, "
                "'SYNTHETIC_FIXTURE', 'SYNTHETIC_DEV', 'active', 'teacher-1', :r, 1)"
            ),
            {"o": org, "c": cls, "r": rules.baseline_revision_id("synthetic-t12b-rt-api")},
        )
        connection.execute(
            text(
                "INSERT INTO be1_profile_revisions (profile_revision_id, child_id, "
                "revision_no, display_name, age_months, age_band_version, age_band_code, "
                "authored_by, revision_hash_version, revision_hash) VALUES (:r, "
                "'synthetic-t12b-rt-api', 1, 'Synthetic Api', 60, 1, 'AGE_36_71', "
                "'teacher-1', 1, repeat('b', 64))"
            ),
            {"r": rules.baseline_revision_id("synthetic-t12b-rt-api")},
        )
    with pytest.raises(Exception, match="downgrade refused"):
        command.downgrade(config, parent)
    assert has_table() and has_column() and live in versions()

    # an edit makes the downgrade refuse, and nothing is removed
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO be1_profile_revisions (profile_revision_id, child_id, revision_no, "
                "display_name, age_months, age_band_version, age_band_code, authored_by, "
                "revision_hash_version, revision_hash) VALUES (:r, 'synthetic-t12b-rt-1', 2, "
                "'Synthetic Mot', 61, 1, 'AGE_36_71', 'x', 1, repeat('a', 64))"
            ),
            {"r": str(uuid4())},
        )
        connection.execute(
            text(
                "UPDATE be1_managed_profiles SET current_profile_revision_id = "
                "(SELECT profile_revision_id FROM be1_profile_revisions WHERE child_id = "
                "'synthetic-t12b-rt-1' AND revision_no = 2), profile_revision_no = 2, "
                "display_name = 'Synthetic Mot', age_months = 61, age_revision = 2 "
                "WHERE child_id = 'synthetic-t12b-rt-1'"
            )
        )
    with pytest.raises(Exception, match="downgrade refused"):
        command.downgrade(config, parent)
    assert has_table() and has_column() and live in versions()


# --- V4-B T-12b-fix: withdrawn access is the uniform 404 (owner decision Q3, 2026-11-23) ---------


def _lifecycle_delete(t: T12b, target_ref: str, state: str = "requested") -> None:
    with t.factory.begin() as db:
        db.add(
            DataLifecycleRequestModel(
                request_id=str(uuid4()),
                organization_id=t.organization_id,
                request_type="delete",
                target_ref=target_ref,
                state=state,
                requested_by="synthetic-test",
            )
        )


def _consent(t: T12b, child_id: str, purpose_ref: str, state: str) -> None:
    with t.factory.begin() as db:
        db.add(
            ConsentRecordModel(
                consent_id=str(uuid4()),
                organization_id=t.organization_id,
                class_id=t.class_id,
                child_id=child_id,
                purpose_ref=purpose_ref,
                state=state,
                recorded_by=t.subjects["manager"],
            )
        )


def test_a_pending_deletion_request_is_the_uniform_404_even_for_a_synthetic_profile(
    t12b: T12b,
) -> None:
    child = _profile(t12b, "deleting")
    unknown = t12b.history("teacher", f"{child}-missing")
    assert t12b.history("teacher", child).status_code == 200
    _lifecycle_delete(t12b, child)
    first = _revisions(t12b, child)[0].profile_revision_id
    body = {"expected_revision": 1, "age_months": 70}
    for call in (
        t12b.history("teacher", child),
        t12b.revision("teacher", child, first),
        t12b.edit("teacher", child, body),
    ):
        assert call.status_code == 404 and _code(call) == "RESOURCE_NOT_FOUND"
        assert call.json()["message"] == unknown.json()["message"]
    assert _audits(t12b, "profile.edit") == []
    assert _audits(t12b, "profile.revisions.read") == []
    assert len(_revisions(t12b, child)) == 1 and _receipts(t12b) == []


def test_a_deletion_request_is_judged_by_its_target_and_its_state(t12b: T12b) -> None:
    child = _profile(t12b, "deleting-scope")
    _lifecycle_delete(t12b, child, state="completed")
    assert t12b.history("teacher", child).status_code == 200  # a completed request hides nothing
    _lifecycle_delete(t12b, t12b.class_id)
    assert t12b.history("teacher", child).status_code == 404  # the class target hides the child


def test_a_revoked_consent_is_404_where_a_pending_one_is_409(t12b: T12b) -> None:
    pending = _profile(t12b, "consent-pending", origin="REAL")
    _consent(t12b, pending, "synthetic-purpose-consent-pending", "pending")
    revoked = _profile(t12b, "consent-revoked", origin="REAL")
    _consent(t12b, revoked, "synthetic-purpose-consent-revoked", "revoked")
    body = {"expected_revision": 1, "age_months": 70}
    for call in (t12b.history("teacher", pending), t12b.edit("teacher", pending, body)):
        assert call.status_code == 409 and _code(call) == "CONSENT_NOT_EFFECTIVE"
    for call in (t12b.history("teacher", revoked), t12b.edit("teacher", revoked, body)):
        assert call.status_code == 404 and _code(call) == "RESOURCE_NOT_FOUND"
    assert len(_audits(t12b, "profile.edit")) == 1  # only the pending one is audited
    assert len(_audits(t12b, "profile.revisions.read")) == 1


def test_a_revoked_consent_does_not_hide_a_synthetic_profile(t12b: T12b) -> None:
    child = _profile(t12b, "synthetic-revoked")
    _consent(t12b, child, "synthetic-purpose-unused", "revoked")
    assert t12b.history("teacher", child).status_code == 200


# --- V4-B T-12b-fix: BR-20, an interest never names a diagnosis ---------------------------------


@pytest.mark.parametrize("interest", ["tự kỷ", "ADHD", "chẩn đoán trầm cảm", "autism"])
def test_an_interest_that_names_a_diagnosis_is_400_and_writes_nothing(
    t12b: T12b, interest: str
) -> None:
    child = _profile(t12b, "br20")
    refused = t12b.edit(
        "teacher", child, {"expected_revision": 1, "structured_interests": [interest]}
    )
    assert refused.status_code == 400
    assert {"field": "structured_interests", "code": "DIAGNOSIS_LIKE"} in refused.json()[
        "field_errors"
    ]
    assert interest not in refused.text
    assert len(_revisions(t12b, child)) == 1 and _receipts(t12b) == []


# --- V4-B T-12b-fix: the lifecycle purge (owner decision Q5, SRS FR-C-10, BR-35, UC-09) -----------


def _sql_scalar(t: T12b, statement: str, **params: Any) -> Any:
    with t.factory() as db:
        return db.execute(text(statement), params).scalar_one()


def _insert_support_needs(t: T12b, child_id: str) -> None:
    with t.factory.begin() as db:
        db.add(
            Be1ProfileSupportNeedsModel(
                child_id=child_id,
                revision=1,
                ciphertext=b"c" * 32,
                nonce=uuid4().bytes[:12],
                key_id="synthetic-purge-key",
                algorithm_version=1,
            )
        )


def test_ordinary_update_and_delete_of_a_revision_stay_refused(t12b: T12b) -> None:
    child = _profile(t12b, "purge-refuse")
    for statement in (
        "UPDATE be1_profile_revisions SET display_name = 'Synthetic X' WHERE child_id = :c",
        "DELETE FROM be1_profile_revisions WHERE child_id = :c",
        "DELETE FROM be1_managed_profiles WHERE child_id = :c",
    ):
        with pytest.raises(Exception) as caught, t12b.factory.begin() as db:
            db.execute(text(statement), {"c": child})
        assert "APPEND_ONLY" in str(caught.value) or "foreign key" in str(caught.value)
    assert len(_revisions(t12b, child)) == 1


def test_the_purge_function_removes_the_profile_its_revisions_receipts_and_support_needs(
    t12b: T12b,
) -> None:
    child = _profile(t12b, "purge-all")
    other = _profile(t12b, "purge-keep")
    for target in (child, other):
        edited = t12b.edit("teacher", target, {"expected_revision": 1, "age_months": 70})
        assert edited.status_code == 200, edited.text
        again = t12b.edit(
            "teacher", target, {"expected_revision": 2, "structured_interests": [INTEREST]}
        )
        assert again.status_code == 200, again.text
    _insert_support_needs(t12b, child)
    _insert_support_needs(t12b, other)
    assert len(_revisions(t12b, child)) == 3 and len(_receipts(t12b)) == 4
    with t12b.factory.begin() as db:
        counts = purge_managed_profile(db, organization_id=t12b.organization_id, child_id=child)
    assert (counts.profiles, counts.revisions, counts.support_needs, counts.receipts) == (
        1,
        3,
        1,
        2,
    )
    assert counts.purged
    # the profile and everything of it is gone; the other child is untouched
    profile_count = "SELECT count(*) FROM be1_managed_profiles WHERE child_id = :c"
    needs_count = "SELECT count(*) FROM be1_profile_support_needs WHERE child_id = :c"
    assert _sql_scalar(t12b, profile_count, c=child) == 0
    assert _revisions(t12b, child) == []
    assert _sql_scalar(t12b, needs_count, c=child) == 0
    assert len(_revisions(t12b, other)) == 3 and len(_receipts(t12b)) == 2
    assert _sql_scalar(t12b, needs_count, c=other) == 1
    # the guard is back: nothing leaks out of the purge transaction
    leaked = _sql_scalar(
        t12b, "SELECT coalesce(current_setting('sketch2life.profile_purge', true), '')"
    )
    assert leaked == ""
    with pytest.raises(Exception, match="APPEND_ONLY"), t12b.factory.begin() as db:
        db.execute(text("DELETE FROM be1_profile_revisions WHERE child_id = :c"), {"c": other})
    with t12b.factory.begin() as db:  # idempotent: an unknown profile answers zero counts
        again_counts = purge_managed_profile(
            db, organization_id=t12b.organization_id, child_id=child
        )
    assert not again_counts.purged and again_counts.revisions == 0


def test_a_purge_names_one_child_only_and_a_rollback_leaves_everything(t12b: T12b) -> None:
    child = _profile(t12b, "purge-one")
    other = _profile(t12b, "purge-two")
    with pytest.raises(Exception, match="APPEND_ONLY"), t12b.factory.begin() as db:
        # inside a purge of `child`, deleting the revision of `other` is still refused
        db.execute(text("SELECT set_config('sketch2life.profile_purge', :c, true)"), {"c": child})
        db.execute(text("DELETE FROM be1_profile_revisions WHERE child_id = :c"), {"c": other})
    with t12b.factory() as db:  # a rolled-back purge changes nothing
        purge_managed_profile(db, organization_id=t12b.organization_id, child_id=child)
        db.rollback()
    assert len(_revisions(t12b, child)) == 1 and len(_revisions(t12b, other)) == 1
    assert (
        _sql_scalar(
            t12b, "SELECT count(*) FROM be1_managed_profiles WHERE child_id = :c", c=child
        )
        == 1
    )


def test_a_purge_in_another_organization_finds_nothing(t12b: T12b) -> None:
    child = _profile(t12b, "purge-org")
    with t12b.factory.begin() as db:
        counts = purge_managed_profile(
            db, organization_id=t12b.foreign_organization_id, child_id=child
        )
    assert not counts.purged and len(_revisions(t12b, child)) == 1


def test_a_409_is_given_and_audited_only_to_a_verified_assigned_teacher(t12b: T12b) -> None:
    child = _profile(t12b, "pending-audience", origin="REAL")
    _consent(t12b, child, "synthetic-purpose-audience", "pending")
    body = {"expected_revision": 1, "age_months": 70}
    # an outsider (another class, another organization, an organization-wide grant) learns nothing
    for actor in ("other_teacher", "foreign_teacher", "orgwide_teacher"):
        for call in (t12b.history(actor, child), t12b.edit(actor, child, body)):
            assert call.status_code == 404 and _code(call) == "RESOURCE_NOT_FOUND", actor
    assert _audits(t12b, "profile.edit") == [] and _audits(t12b, "profile.revisions.read") == []
    # the assigned Teacher is told, and the denial is audited
    for call in (t12b.history("teacher", child), t12b.edit("teacher", child, body)):
        assert call.status_code == 409 and _code(call) == "CONSENT_NOT_EFFECTIVE"
    assert len(_audits(t12b, "profile.edit")) == 1
    assert len(_audits(t12b, "profile.revisions.read")) == 1
    # once the assignment is revoked the same calls are the uniform 404 and add no audit row
    with t12b.factory.begin() as db:
        db.execute(
            update(OrganizationAssignmentModel)
            .where(OrganizationAssignmentModel.subject == t12b.subjects["teacher"])
            .values(active=False)
        )
    for call in (t12b.history("teacher", child), t12b.edit("teacher", child, body)):
        assert call.status_code == 404 and _code(call) == "RESOURCE_NOT_FOUND"
    assert len(_audits(t12b, "profile.edit")) == 1
    assert len(_audits(t12b, "profile.revisions.read")) == 1
    assert _receipts(t12b) == [] and len(_revisions(t12b, child)) == 1


def test_only_the_newest_record_of_the_profiles_own_purpose_can_withdraw_it(t12b: T12b) -> None:
    body = {"expected_revision": 1, "age_months": 70}
    # a revoke of another purpose hides nothing: the profile stays at the audited 409
    other = _profile(t12b, "revoke-other-purpose", origin="REAL")
    _consent(t12b, other, "synthetic-purpose-unrelated", "revoked")
    assert t12b.history("teacher", other).status_code == 409
    # revoke, then a newer pending record of the same purpose (a re-grant under way): 409, not 404
    regrant = _profile(t12b, "revoke-then-regrant", origin="REAL")
    _consent(t12b, regrant, "synthetic-purpose-revoke-then-regrant", "revoked")
    assert t12b.history("teacher", regrant).status_code == 404
    _consent(t12b, regrant, "synthetic-purpose-revoke-then-regrant", "pending")
    for call in (t12b.history("teacher", regrant), t12b.edit("teacher", regrant, body)):
        assert call.status_code == 409 and _code(call) == "CONSENT_NOT_EFFECTIVE"
    # a newer revoke after a pending record withdraws it again
    _consent(t12b, regrant, "synthetic-purpose-revoke-then-regrant", "revoked")
    assert t12b.history("teacher", regrant).status_code == 404


def test_a_failed_deletion_request_keeps_hiding_the_profile_like_the_candidate_selection(
    t12b: T12b,
) -> None:
    child = _profile(t12b, "deleting-exception")
    _lifecycle_delete(t12b, child, state="exception")
    assert t12b.history("teacher", child).status_code == 404
