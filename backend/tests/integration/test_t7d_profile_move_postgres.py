"""FEAT-066 T-7d: the Manager/Teacher enrollment move within an organization on PostgreSQL.

SRS l.544 (one active enrollment, the earlier one is closed and kept), l.830 and l.1093 (the
enrollment is the source, the class projection moves in the same transaction), l.1425 (capacity
never blocks a change in an existing class: none is built), l.864-865 (uniform 404, 403 only
inside a known scope), l.1651 and l.1699 (expected class revision, STALE_REVISION), l.1697 (keyed
commands), l.2586 (no child data to the School Manager), REG l.102, l.248, l.273 (one active
enrollment per child in the database). Runs only against a disposable database whose name contains
``be1_acceptance``. Principals are injected through the ``X-Test-Principal`` header; every
identity, class and text is synthetic.

The migration round trip (downgrade to ``20261120_cls_0001`` and back) runs with alembic against a
separate fresh database (see the evidence note); here the index definitions, the one-active rule
and the two guard statements are exercised.
"""

from __future__ import annotations

import os
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
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError, IntegrityError

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    Be1CommandReceiptModel,
    ClassroomModel,
    ClassroomSessionModel,
    ConsentRecordModel,
    EnrollmentModel,
    ManagedProfileModel,
    OrganizationAssignmentModel,
    OrganizationModel,
    SessionMembershipModel,
    SyntheticEligibilityProofModel,
)
from sketch2life.infrastructure.persistence.core_models import (
    CoreAuditEntryModel,
    CoreOutboxEventModel,
)
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult

ISSUER = "synthetic-t7d-issuer"
PURPOSE = "classroom-learning-v1"
NAME = "Synthetic Moving Learner"


@dataclass
class Api:
    app: FastAPI
    client: TestClient
    token: str
    organization: str
    foreign_organization: str
    subjects: dict[str, str] = field(default_factory=dict)

    def factory(self) -> Any:
        return self.app.state.be1_runtime.session_factory


def _identity(db: Any, subject: str, role: str) -> None:
    db.add(AdultIdentityModel(subject=subject, issuer=ISSUER, state="active", account_role=role))
    db.flush()


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
    organization, foreign = f"synthetic-t7d-org-{token}", f"synthetic-t7d-foreign-{token}"
    d = Api(app, TestClient(app), token, organization, foreign)

    def label(value: str) -> str:
        return f"synthetic-t7d-{value}-{token}"

    with runtime.session_factory.begin() as db:
        for org in (organization, foreign):
            db.add(OrganizationModel(organization_id=org, display_name=org, state="active"))
        db.flush()
        people: tuple[tuple[str, str, str | None, str | None], ...] = (
            ("manager", "school_manager", organization, "school_admin"),
            ("foreign_manager", "school_manager", foreign, "school_admin"),
            ("orgt", "teacher", organization, "teacher"),  # an organization-wide Teacher row
            ("parent", "parent", None, None),
            ("platform", "platform_admin", None, None),
            ("fteacher", "teacher", foreign, "teacher"),  # a Teacher of another organization
        )
        for key, role, home, assignment_role in people:
            d.subjects[key] = label(key)
            _identity(db, label(key), role)
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
def new_class(d: Api, *, state: str = "active", organization: str | None = None) -> str:
    class_id = f"synthetic-t7d-class-{uuid4().hex[:12]}"
    with d.factory().begin() as db:
        db.add(
            ClassroomModel(
                class_id=class_id,
                organization_id=organization or d.organization,
                display_name=f"Synthetic {class_id}"[:200],
                state=state,
                created_by="synthetic-t7d-seed",
            )
        )
    return class_id


def add_adult(
    d: Api,
    key: str,
    class_ids: list[str],
    *,
    role: str = "teacher",
    organization: str | None = None,
) -> None:
    subject = f"synthetic-t7d-{key}-{d.token}"
    d.subjects[key] = subject
    with d.factory().begin() as db:
        _identity(db, subject, "teacher")
        for class_id in class_ids:
            _assign(db, organization or d.organization, subject, role, class_id)


def new_child(
    d: Api, class_id: str, *, enrolled: bool = True, organization: str | None = None
) -> str:
    child_id = f"synthetic-{uuid4().hex[:24]}"
    org = organization or d.organization
    with d.factory().begin() as db:
        db.add(
            ManagedProfileModel(
                child_id=child_id,
                organization_id=org,
                class_id=class_id,
                display_name=NAME,
                age_months=60,
                age_revision=1,
                age_source="SYNTHETIC_FIXTURE",
                consent_id=None,
                consent_purpose_ref=None,
                data_origin="SYNTHETIC_DEV",
                created_by="synthetic-t7d-seed",
            )
        )
        db.flush()
        if enrolled:
            db.add(
                EnrollmentModel(
                    enrollment_id=str(uuid4()),
                    organization_id=org,
                    class_id=class_id,
                    child_id=child_id,
                    created_by="synthetic-t7d-seed",
                )
            )
    return child_id


def new_real_child(d: Api, class_id: str) -> tuple[str, str]:
    child_id = f"synthetic-{uuid4().hex[:24]}"
    consent_id = str(uuid4())
    with d.factory().begin() as db:
        db.add(
            ManagedProfileModel(
                child_id=child_id,
                organization_id=d.organization,
                class_id=class_id,
                display_name=NAME,
                age_months=60,
                age_revision=1,
                age_source="ADULT_DECLARED",
                consent_id=consent_id,
                consent_purpose_ref=PURPOSE,
                data_origin="REAL",
                created_by="synthetic-t7d-seed",
            )
        )
        db.add(
            EnrollmentModel(
                enrollment_id=str(uuid4()),
                organization_id=d.organization,
                class_id=class_id,
                child_id=child_id,
                created_by="synthetic-t7d-seed",
            )
        )
        db.add(
            ConsentRecordModel(
                consent_id=consent_id,
                organization_id=d.organization,
                class_id=class_id,
                child_id=child_id,
                purpose_ref=PURPOSE,
                state="pending",
                recorded_by="synthetic-t7d-seed",
            )
        )
    return child_id, consent_id


def url(source: str, child_id: str) -> str:
    return f"/api/be1/v1/classes/{source}/profiles/{child_id}/move"


def move(
    d: Api,
    who: str,
    source: str,
    child_id: str,
    target: str,
    *,
    source_revision: str | None = '"1"',
    target_revision: int = 1,
    key: str | None = None,
    body: dict[str, Any] | None = None,
    **headers: str,
) -> Any:
    request_headers = {"X-Test-Principal": d.subjects[who]}
    request_headers["Idempotency-Key"] = uuid4().hex if key is None else key
    if source_revision is not None:
        request_headers["If-Match"] = source_revision
    request_headers.update(headers)
    return d.client.post(
        url(source, child_id),
        json={"target_class_id": target, "target_class_revision": target_revision}
        if body is None
        else body,
        headers=request_headers,
    )


def shape(response: Any) -> tuple[int, dict[str, Any]]:
    body = dict(response.json())
    body.pop("request_id", None)
    body.pop("correlation_id", None)
    return response.status_code, body


def class_revision(d: Api, class_id: str) -> int:
    with d.factory()() as db:
        return int(
            db.scalar(select(ClassroomModel.revision).where(ClassroomModel.class_id == class_id))
            or 0
        )


def set_class(d: Api, class_id: str, **values: Any) -> None:
    with d.factory().begin() as db:
        row = db.get(ClassroomModel, class_id)
        assert row is not None
        for name, value in values.items():
            setattr(row, name, value)


def count(d: Api, model: Any, *where: Any) -> int:
    with d.factory()() as db:
        return int(db.scalar(select(func.count()).select_from(model).where(*where)) or 0)


def enrollments(d: Api, child_id: str) -> list[tuple[str, str]]:
    with d.factory()() as db:
        rows = db.execute(
            select(EnrollmentModel.class_id, EnrollmentModel.state)
            .where(EnrollmentModel.child_id == child_id)
            .order_by(EnrollmentModel.created_at, EnrollmentModel.enrollment_id)
        ).all()
    return [(str(class_id), str(state)) for class_id, state in rows]


def profile_class(d: Api, child_id: str) -> str:
    with d.factory()() as db:
        row = db.get(ManagedProfileModel, child_id)
        assert row is not None
        return str(row.class_id)


def audit_count(d: Api, child_id: str) -> int:
    return count(
        d,
        CoreAuditEntryModel,
        CoreAuditEntryModel.organization_id == d.organization,
        CoreAuditEntryModel.action == "profile.move",
        CoreAuditEntryModel.resource_id == child_id,
    )


def add_session(d: Api, class_id: str, *, state: str) -> str:
    session_id = f"synthetic-t7d-session-{uuid4().hex[:12]}"
    with d.factory().begin() as db:
        db.add(
            ClassroomSessionModel(
                session_id=session_id,
                organization_id=d.organization,
                class_id=class_id,
                created_by="synthetic-t7d-seed",
                state=state,
                revision=1,
                configuration={},
                active_phase="lobby",
            )
        )
    return session_id


def add_membership(d: Api, session_id: str, class_id: str, child_id: str, state: str) -> None:
    with d.factory().begin() as db:
        db.add(
            SessionMembershipModel(
                membership_id=str(uuid4()),
                organization_id=d.organization,
                session_id=session_id,
                class_id=class_id,
                child_id=child_id,
                state=state,
            )
        )


def two_classes(d: Api, key: str = "t1") -> tuple[str, str]:
    source, target = new_class(d), new_class(d)
    add_adult(d, key, [source, target])
    return source, target


# --------------------------------------------------------------------------------- the move
def test_move_closes_and_keeps_the_old_enrollment_and_opens_a_new_one(api: Api) -> None:
    d = api
    source, target = two_classes(d)
    child = new_child(d, source)
    key = f"t7d-{uuid4().hex}"
    response = move(d, "t1", source, child, target, key=key)
    assert response.status_code == 200, response.text
    body = response.json()
    assert "ETag" not in response.headers  # two resources, no single ETag
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
    assert (body["child_id"], body["from_class_id"], body["to_class_id"]) == (child, source, target)
    assert (body["from_class_revision"], body["to_class_revision"]) == (2, 2)
    assert NAME not in response.text and "60" not in body.values()
    assert enrollments(d, child) == [(source, "withdrawn"), (target, "active")]
    with d.factory()() as db:
        new = db.get(EnrollmentModel, body["enrollment_id"])
        assert new is not None and (new.class_id, new.state) == (target, "active")
        receipts = db.scalars(
            select(Be1CommandReceiptModel).where(Be1CommandReceiptModel.idempotency_key == key)
        ).all()
        assert len(receipts) == 1 and receipts[0].response_json == body
        assert receipts[0].operation_scope == f"POST /classes/{source}/profiles/{child}/move"
        assert NAME not in str(receipts[0].response_json)
    assert profile_class(d, child) == target
    assert (class_revision(d, source), class_revision(d, target)) == (2, 2)
    assert audit_count(d, child) == 1
    assert (
        count(
            d,
            CoreOutboxEventModel,
            CoreOutboxEventModel.aggregate_id == child,
            CoreOutboxEventModel.event_type == "be1.profile.moved.v1",
        )
        == 1
    )


def test_the_child_can_return_to_a_class_it_left_and_the_history_is_kept(api: Api) -> None:
    d = api
    class_a, class_b = two_classes(d)
    child = new_child(d, class_a)
    assert move(d, "t1", class_a, child, class_b).status_code == 200
    back = move(d, "t1", class_b, child, class_a, source_revision='"2"', target_revision=2)
    assert back.status_code == 200, back.text
    assert back.json()["from_class_revision"] == 3 and back.json()["to_class_revision"] == 3
    history = enrollments(d, child)
    assert sorted(history) == sorted(
        [(class_a, "withdrawn"), (class_b, "withdrawn"), (class_a, "active")]
    )
    assert [state for _class, state in history].count("active") == 1
    assert profile_class(d, child) == class_a
    assert count(d, EnrollmentModel, EnrollmentModel.child_id == child) == 3


def test_a_move_does_not_touch_consents_proofs_or_session_history(api: Api) -> None:
    d = api
    source, target = two_classes(d)
    child = new_child(d, source)
    finished = add_session(d, source, state="finished")
    add_membership(d, finished, source, child, "admitted")
    consent_id = str(uuid4())
    now = datetime.now(UTC)
    with d.factory().begin() as db:
        db.add(
            ConsentRecordModel(
                consent_id=consent_id,
                organization_id=d.organization,
                class_id=source,
                child_id=child,
                purpose_ref=PURPOSE,
                state="pending",
                recorded_by="synthetic-t7d-seed",
            )
        )
        db.add(
            SyntheticEligibilityProofModel(
                evidence_id=f"synthetic-t7d-proof-{uuid4().hex[:10]}",
                schema_version="v1",
                organization_id=d.organization,
                class_id=source,
                child_profile_id=child,
                purpose_ref=PURPOSE,
                run_ref="synthetic-run",
                issued_by="synthetic-t7d-seed",
                issued_at=now,
                expires_at=now + timedelta(hours=1),
                policy_version="v1",
            )
        )
    assert move(d, "t1", source, child, target).status_code == 200
    with d.factory()() as db:
        consent = db.get(ConsentRecordModel, consent_id)
        assert consent is not None and consent.class_id == source
        proof_class = db.scalar(
            select(SyntheticEligibilityProofModel.class_id).where(
                SyntheticEligibilityProofModel.child_profile_id == child
            )
        )
        assert proof_class == source
        membership = db.scalar(
            select(SessionMembershipModel).where(SessionMembershipModel.child_id == child)
        )
        assert membership is not None and (membership.class_id, membership.state) == (
            source,
            "admitted",
        )


# --------------------------------------------------------------------------- idempotency
def test_the_same_key_and_request_replays_the_stored_answer(api: Api) -> None:
    d = api
    source, target = two_classes(d)
    child = new_child(d, source)
    key = f"t7d-{uuid4().hex}"
    first = move(d, "t1", source, child, target, key=key)
    assert first.status_code == 200
    # The revisions moved, the old ones are stale, yet the replay answers the stored body, also
    # after the target class was suspended (the receipt comes before the stale and state checks).
    set_class(d, target, state="suspended")
    again = move(d, "t1", source, child, target, key=key)
    assert again.status_code == 200
    assert shape(again) == shape(first)
    assert again.content == first.content
    assert enrollments(d, child) == [(source, "withdrawn"), (target, "active")]
    assert audit_count(d, child) == 1
    assert count(d, Be1CommandReceiptModel, Be1CommandReceiptModel.idempotency_key == key) == 1


def test_the_same_key_with_another_request_is_400_invalid_idempotency_key(api: Api) -> None:
    d = api
    class_a, class_b = two_classes(d)
    class_c = new_class(d)
    add_adult(d, "t1c", [class_a, class_b, class_c])
    child = new_child(d, class_a)
    key = f"t7d-{uuid4().hex}"
    assert move(d, "t1c", class_a, child, class_b, key=key).status_code == 200
    other_target = move(d, "t1c", class_a, child, class_c, key=key)
    assert other_target.status_code == 400
    assert other_target.json()["code"] == "INVALID_IDEMPOTENCY_KEY"
    other_revision = move(d, "t1c", class_a, child, class_b, key=key, target_revision=2)
    assert other_revision.status_code == 400
    assert other_revision.json()["code"] == "INVALID_IDEMPOTENCY_KEY"
    other_if_match = move(d, "t1c", class_a, child, class_b, key=key, source_revision='"2"')
    assert other_if_match.status_code == 400
    assert enrollments(d, child) == [(class_a, "withdrawn"), (class_b, "active")]


def test_the_same_key_for_another_child_is_a_new_command(api: Api) -> None:
    d = api
    source, target = two_classes(d)
    first_child, second_child = new_child(d, source), new_child(d, source)
    key = f"t7d-{uuid4().hex}"
    assert move(d, "t1", source, first_child, target, key=key).status_code == 200
    second = move(
        d, "t1", source, second_child, target, key=key, source_revision='"2"', target_revision=2
    )
    assert second.status_code == 200, second.text
    assert profile_class(d, second_child) == target


@pytest.mark.parametrize("bad", ["", "a b", "x" * 129])
def test_bad_idempotency_keys_are_400_invalid_request(api: Api, bad: str) -> None:
    d = api
    source, target = two_classes(d)
    child = new_child(d, source)
    response = move(d, "t1", source, child, target, key=bad) if bad else d.client.post(
        url(source, child),
        json={"target_class_id": target, "target_class_revision": 1},
        headers={"X-Test-Principal": d.subjects["t1"], "If-Match": '"1"'},
    )
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"
    assert enrollments(d, child) == [(source, "active")]


# ------------------------------------------------------------------------------ revisions
def test_a_stale_source_revision_is_409_with_the_current_version(api: Api) -> None:
    d = api
    source, target = two_classes(d)
    child = new_child(d, source)
    set_class(d, source, revision=3)
    response = move(d, "t1", source, child, target, source_revision='"1"')
    assert response.status_code == 409
    assert response.json()["code"] == "STALE_REVISION"
    assert response.json()["current_version"] == 3
    assert response.headers["ETag"] == '"3"'
    assert enrollments(d, child) == [(source, "active")]
    assert (class_revision(d, source), class_revision(d, target)) == (3, 1)


def test_a_stale_target_revision_is_409_with_the_target_version(api: Api) -> None:
    d = api
    source, target = two_classes(d)
    child = new_child(d, source)
    set_class(d, target, revision=4)
    response = move(d, "t1", source, child, target, target_revision=1)
    assert response.status_code == 409
    assert response.json()["code"] == "STALE_REVISION"
    assert response.json()["current_version"] == 4
    assert profile_class(d, child) == source
    assert (class_revision(d, source), class_revision(d, target)) == (1, 4)


def test_the_source_is_checked_first_when_both_are_stale(api: Api) -> None:
    d = api
    source, target = two_classes(d)
    child = new_child(d, source)
    set_class(d, source, revision=2)
    set_class(d, target, revision=5)
    response = move(d, "t1", source, child, target)
    assert response.json()["current_version"] == 2


def test_missing_and_malformed_if_match_and_bodies_are_400(api: Api) -> None:
    d = api
    source, target = two_classes(d)
    child = new_child(d, source)
    missing = move(d, "t1", source, child, target, source_revision=None)
    assert (missing.status_code, missing.json()["code"]) == (400, "INVALID_REQUEST")
    assert missing.json()["field_errors"] == [{"field": "If-Match", "code": "REQUIRED"}]
    for bad in ('1', 'W/"1"', '"0"', '"01"', '*'):
        response = move(d, "t1", source, child, target, source_revision=bad)
        assert (response.status_code, response.json()["code"]) == (400, "INVALID_REQUEST"), bad
    for body in (
        {"target_class_id": target},
        {"target_class_revision": 1},
        {"target_class_id": target, "target_class_revision": 0},
        {"target_class_id": target, "target_class_revision": 1, "child_id": child},
        {"target_class_id": target, "target_class_revision": 1, "capacity": 99},
    ):
        response = move(d, "t1", source, child, target, body=body)
        assert (response.status_code, response.json()["code"]) == (400, "INVALID_REQUEST"), body
    assert enrollments(d, child) == [(source, "active")]


def test_moving_into_the_same_class_is_400(api: Api) -> None:
    d = api
    source, _target = two_classes(d)
    child = new_child(d, source)
    response = move(d, "t1", source, child, source)
    assert response.status_code == 400
    assert response.json()["field_errors"] == [
        {"field": "target_class_id", "code": "INVALID_FORMAT"}
    ]
    assert enrollments(d, child) == [(source, "active")]


@pytest.mark.parametrize("state", ["suspended", "archived"])
@pytest.mark.parametrize("side", ["source", "target"])
def test_a_read_only_class_on_either_side_is_409_and_writes_nothing(
    api: Api, state: str, side: str
) -> None:
    d = api
    source, target = two_classes(d)
    child = new_child(d, source)
    set_class(d, source if side == "source" else target, state=state)
    response = move(d, "t1", source, child, target)
    assert response.status_code == 409
    assert response.json()["code"] == "INVALID_STATE_TRANSITION"
    assert enrollments(d, child) == [(source, "active")]
    assert profile_class(d, child) == source
    assert (class_revision(d, source), class_revision(d, target)) == (1, 1)
    assert audit_count(d, child) == 0


# ------------------------------------------------------------------------------ authorization
def test_the_school_manager_can_move_within_the_organization_without_profile_contents(
    api: Api,
) -> None:
    d = api
    source, target = two_classes(d)
    child = new_child(d, source)
    response = move(d, "manager", source, child, target)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["contract"] == "Be1ProfileMoveV1"
    assert body["child_id"] == child
    assert set(body) == {
        "contract",
        "child_id",
        "from_class_id",
        "to_class_id",
        "enrollment_id",
        "from_class_revision",
        "to_class_revision",
    }
    assert NAME not in response.text and "age_months" not in response.text
    assert enrollments(d, child) == [(source, "withdrawn"), (target, "active")]
    assert profile_class(d, child) == target
    assert (class_revision(d, source), class_revision(d, target)) == (2, 2)
    assert audit_count(d, child) == 1


def test_manager_move_does_not_copy_real_profile_consent_to_the_target_class(api: Api) -> None:
    d = api
    source, target = two_classes(d)
    child, consent_id = new_real_child(d, source)

    response = move(d, "manager", source, child, target)

    assert response.status_code == 200, response.text
    with d.factory()() as db:
        consent = db.get(ConsentRecordModel, consent_id)
        assert consent is not None and consent.class_id == source
        moved_profile = db.get(ManagedProfileModel, child)
        assert moved_profile is not None and moved_profile.class_id == target
    assert count(
        d,
        ConsentRecordModel,
        ConsentRecordModel.organization_id == d.organization,
        ConsentRecordModel.class_id == target,
        ConsentRecordModel.child_id == child,
    ) == 0

    target_roster = d.client.get(
        f"/api/be1/v1/organizations/{d.organization}/classes/{target}/profiles",
        headers={"X-Test-Principal": d.subjects["t1"]},
    )
    assert target_roster.status_code == 200, target_roster.text
    assert target_roster.json()["active_profile_count"] == 1
    assert target_roster.json()["items"] == []
    assert child not in target_roster.text and NAME not in target_roster.text


def test_everyone_outside_the_two_classes_gets_one_uniform_404(api: Api) -> None:
    d = api
    class_a, class_b = two_classes(d)
    only_a = new_class(d)
    add_adult(d, "only_a", [class_a])  # source taught, target not
    add_adult(d, "only_b", [class_b])  # target taught, source not
    add_adult(d, "other", [only_a])  # another class of the organization
    foreign_class = new_class(d, organization=d.foreign_organization)
    add_adult(d, "foreign_both", [foreign_class], organization=d.foreign_organization)
    child = new_child(d, class_a)
    attempts = [
        move(d, "only_a", class_a, child, class_b),
        move(d, "only_b", class_a, child, class_b),
        move(d, "other", class_a, child, class_b),
        move(d, "orgt", class_a, child, class_b),
        move(d, "fteacher", class_a, child, class_b),
        move(d, "foreign_manager", class_a, child, class_b),
        move(d, "foreign_both", class_a, child, class_b),
        move(d, "parent", class_a, child, class_b),
        move(d, "platform", class_a, child, class_b),
        move(d, "foreign_both", class_a, child, foreign_class),
        move(d, "manager", class_a, child, foreign_class),
        # a target of another organization, asked by a Teacher of the source
        move(d, "only_a", class_a, child, foreign_class),
        # unknown source class and unknown target class
        move(d, "only_a", "synthetic-t7d-missing", child, class_b),
        move(d, "only_a", class_a, child, "synthetic-t7d-missing"),
    ]
    shapes = [shape(item) for item in attempts]
    assert {status for status, _ in shapes} == {404}
    assert len({str(body) for _, body in shapes}) == 1, shapes
    assert shapes[0][1]["code"] == "RESOURCE_NOT_FOUND"
    assert enrollments(d, child) == [(class_a, "active")]
    assert (class_revision(d, class_a), class_revision(d, class_b)) == (1, 1)


def test_guide_and_observer_rows_are_403_on_the_source_and_404_on_the_target(api: Api) -> None:
    d = api
    class_a, class_b = new_class(d), new_class(d)
    add_adult(d, "guide_a", [class_a], role="guide")
    add_adult(d, "observer_a", [class_a], role="observer")
    child = new_child(d, class_a)
    for who in ("guide_a", "observer_a"):
        response = move(d, who, class_a, child, class_b)
        assert response.status_code == 403, who
        assert response.json()["code"] == "ACTION_NOT_ALLOWED"
    # A Teacher of the source whose only row on the target is a guide row: the uniform 404.
    add_adult(d, "mixed", [class_a])
    with d.factory().begin() as db:
        _assign(db, d.organization, d.subjects["mixed"], "guide", class_b)
    response = move(d, "mixed", class_a, child, class_b)
    assert response.status_code == 404
    assert response.json()["code"] == "RESOURCE_NOT_FOUND"
    assert enrollments(d, child) == [(class_a, "active")]


def test_a_replay_by_a_teacher_whose_target_row_was_revoked_is_404(api: Api) -> None:
    d = api
    source, target = two_classes(d)
    child = new_child(d, source)
    key = f"t7d-{uuid4().hex}"
    assert move(d, "t1", source, child, target, key=key).status_code == 200
    with d.factory().begin() as db:
        rows = db.scalars(
            select(OrganizationAssignmentModel).where(
                OrganizationAssignmentModel.subject == d.subjects["t1"],
                OrganizationAssignmentModel.class_id == target,
            )
        ).all()
        for row in rows:
            row.active = False
    replay = move(d, "t1", source, child, target, key=key)
    assert replay.status_code == 404
    assert replay.json()["code"] == "RESOURCE_NOT_FOUND"


# --------------------------------------------------------------------------- the child state
def test_an_unknown_child_and_a_child_of_another_class_are_the_same_404(api: Api) -> None:
    d = api
    source, target = two_classes(d)
    third = new_class(d)
    add_adult(d, "t1x", [source, target, third])
    elsewhere = new_child(d, third)
    unknown = move(d, "t1x", source, "synthetic-does-not-exist", target)
    other_class = move(d, "t1x", source, elsewhere, target)
    assert unknown.status_code == other_class.status_code == 404
    assert unknown.json()["code"] == "RESOURCE_NOT_FOUND"
    assert shape(unknown) == shape(other_class)
    assert enrollments(d, elsewhere) == [(third, "active")]


def test_a_withdrawn_profile_is_not_found(api: Api) -> None:
    d = api
    source, target = two_classes(d)
    child = new_child(d, source)
    with d.factory().begin() as db:
        row = db.get(ManagedProfileModel, child)
        assert row is not None
        row.state = "withdrawn"
    assert move(d, "t1", source, child, target).status_code == 404


def test_a_profile_without_an_active_enrollment_is_409_and_is_not_auto_enrolled(api: Api) -> None:
    d = api
    source, target = two_classes(d)
    child = new_child(d, source, enrolled=False)
    response = move(d, "t1", source, child, target)
    assert response.status_code == 409
    assert response.json()["code"] == "INVALID_STATE_TRANSITION"
    assert enrollments(d, child) == []
    assert profile_class(d, child) == source


@pytest.mark.parametrize("membership_state", ["join_pending", "admitted"])
@pytest.mark.parametrize("session_state", ["configured", "lobby", "active", "paused"])
def test_an_open_membership_in_an_unfinished_session_is_409(
    api: Api, membership_state: str, session_state: str
) -> None:
    d = api
    source, target = two_classes(d)
    child = new_child(d, source)
    session_id = add_session(d, source, state=session_state)
    add_membership(d, session_id, source, child, membership_state)
    response = move(d, "t1", source, child, target)
    assert response.status_code == 409
    assert response.json()["code"] == "INVALID_STATE_TRANSITION"
    assert enrollments(d, child) == [(source, "active")]
    assert (class_revision(d, source), class_revision(d, target)) == (1, 1)


def test_finished_sessions_and_closed_memberships_do_not_block_a_move(api: Api) -> None:
    d = api
    source, target = two_classes(d)
    child = new_child(d, source)
    finished = add_session(d, source, state="finished")
    add_membership(d, finished, source, child, "admitted")
    running = add_session(d, source, state="active")
    add_membership(d, running, source, child, "left")
    removed = add_session(d, source, state="lobby")
    add_membership(d, removed, source, child, "removed")
    response = move(d, "t1", source, child, target)
    assert response.status_code == 200, response.text


# -------------------------------------------------------------------------- concurrency
def test_two_moves_of_one_child_to_different_classes_make_one_move(api: Api) -> None:
    d = api
    class_a, class_b = two_classes(d)
    class_c = new_class(d)
    add_adult(d, "t1c", [class_a, class_b, class_c])
    child = new_child(d, class_a)
    barrier = Barrier(2)

    def run(target: str) -> Any:
        barrier.wait(timeout=30)
        return move(d, "t1c", class_a, child, target)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(run, class_b), executor.submit(run, class_c)]
        responses = [future.result(timeout=90) for future in futures]
    assert sorted(response.status_code for response in responses) == [200, 409]
    loser = next(response for response in responses if response.status_code == 409)
    assert loser.json()["code"] == "STALE_REVISION"
    history = enrollments(d, child)
    assert [state for _class, state in history].count("active") == 1
    assert len(history) == 2
    assert class_revision(d, class_a) == 2
    assert count(d, CoreAuditEntryModel, CoreAuditEntryModel.action == "profile.move",
                 CoreAuditEntryModel.resource_id == child) == 1


def _opposite_round(d: Api, who: str) -> None:
    class_a, class_b = two_classes(d, key=who)
    child_ab, child_ba = new_child(d, class_a), new_child(d, class_b)
    barrier = Barrier(2)

    def run(source: str, child: str, target: str) -> Any:
        barrier.wait(timeout=30)
        return move(d, who, source, child, target)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(run, class_a, child_ab, class_b),
            executor.submit(run, class_b, child_ba, class_a),
        ]
        responses = [future.result(timeout=60) for future in futures]
    statuses = sorted(response.status_code for response in responses)
    # Both end (no deadlock, no 500): the first commit makes the other side stale.
    assert statuses in ([200, 409], [200, 200]), statuses
    for response in responses:
        if response.status_code == 409:
            assert response.json()["code"] == "STALE_REVISION"
    for child in (child_ab, child_ba):
        assert [s for _c, s in enrollments(d, child)].count("active") == 1


def test_opposite_moves_of_two_children_finish_without_a_deadlock(api: Api) -> None:
    for round_index in range(4):
        _opposite_round(api, f"t1r{round_index}")


def test_concurrent_requests_with_the_same_key_make_one_move(api: Api) -> None:
    d = api
    source, target = two_classes(d)
    child = new_child(d, source)
    key = f"t7d-same-{uuid4().hex}"
    barrier = Barrier(5)

    def run() -> Any:
        barrier.wait(timeout=30)
        return move(d, "t1", source, child, target, key=key)

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(run) for _ in range(5)]
        responses = [future.result(timeout=60) for future in futures]
    assert [response.status_code for response in responses] == [200] * 5
    assert len({response.content for response in responses}) == 1
    assert enrollments(d, child) == [(source, "withdrawn"), (target, "active")]
    assert class_revision(d, source) == 2 and class_revision(d, target) == 2
    assert count(d, Be1CommandReceiptModel, Be1CommandReceiptModel.idempotency_key == key) == 1


# ------------------------------------------------------------------------ the database rule
def test_the_database_holds_one_active_enrollment_per_child(api: Api) -> None:
    d = api
    class_a, class_b = new_class(d), new_class(d)
    child = new_child(d, class_a)
    # A second active row for the same child, in any class, is refused by the partial index.
    for target in (class_a, class_b):
        with pytest.raises(IntegrityError), d.factory().begin() as db:
            db.add(
                EnrollmentModel(
                    enrollment_id=str(uuid4()),
                    organization_id=d.organization,
                    class_id=target,
                    child_id=child,
                    created_by="synthetic-t7d-seed",
                )
            )
    # Withdrawn rows are history: several in one class, plus one active row, are accepted.
    with d.factory().begin() as db:
        for _ in range(2):
            db.add(
                EnrollmentModel(
                    enrollment_id=str(uuid4()),
                    organization_id=d.organization,
                    class_id=class_a,
                    child_id=child,
                    state="withdrawn",
                    created_by="synthetic-t7d-seed",
                )
            )
    assert sorted(state for _c, state in enrollments(d, child)) == [
        "active",
        "withdrawn",
        "withdrawn",
    ]


def test_the_indexes_replace_the_old_unique_constraint(api: Api) -> None:
    d = api
    with d.factory()() as db:
        indexes = dict(
            db.execute(
                text(
                    "SELECT indexname, indexdef FROM pg_indexes "
                    "WHERE tablename = 'be1_enrollments'"
                )
            ).all()
        )
        constraints = {
            row[0]
            for row in db.execute(
                text(
                    "SELECT conname FROM pg_constraint "
                    "WHERE conrelid = 'be1_enrollments'::regclass"
                )
            ).all()
        }
    assert "uq_be1_enrollment" not in indexes and "uq_be1_enrollment" not in constraints
    active = indexes["uq_be1_enrollment_active"]
    assert "UNIQUE INDEX" in active and "(organization_id, child_id)" in active
    assert "WHERE" in active and "'active'" in active
    lookup = indexes["ix_be1_enrollment_class_child"]
    assert "UNIQUE" not in lookup and "(organization_id, class_id, child_id)" in lookup


def test_the_guard_statements_run_and_the_downgrade_guard_refuses_a_return_move(
    api: Api,
) -> None:
    import importlib.util
    from pathlib import Path

    path = (
        Path(__file__).resolve().parents[2]
        / "alembic"
        / "versions"
        / "20261120_cls_0002_enrollment_active_unique.py"
    )
    spec = importlib.util.spec_from_file_location("cls_0002_guard", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    d = api
    # The upgrade guard finds nothing: the partial index makes a second active row impossible.
    with d.factory()() as db:
        db.execute(text(module.UPGRADE_GUARD))
    class_a, class_b = two_classes(d)
    child = new_child(d, class_a)
    assert move(d, "t1", class_a, child, class_b).status_code == 200
    assert (
        move(d, "t1", class_b, child, class_a, source_revision='"2"', target_revision=2).status_code
        == 200
    )
    # A child returned to a class it left: the old unique constraint could not be rebuilt.
    with pytest.raises(DBAPIError, match="downgrade refused"), d.factory()() as db:
        db.execute(text(module.DOWNGRADE_GUARD))
