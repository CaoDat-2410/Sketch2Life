"""PostgreSQL acceptance for manager profile placement; all fixture data is synthetic.

Rows are isolated by unique organizations in the disposable acceptance database, as in T-7d.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from threading import Barrier
from typing import Any
from uuid import uuid4

import pytest
from fastapi import FastAPI, Header
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    Be1CommandReceiptModel,
    ClassroomModel,
    ConsentRecordModel,
    DataLifecycleRequestModel,
    EnrollmentModel,
    ManagedProfileModel,
    OrganizationAssignmentModel,
    OrganizationModel,
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
def api(monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest) -> Iterator[Api]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL to a disposable PostgreSQL database")
    if "be1_acceptance" not in database_url.rsplit("/", 1)[-1]:
        pytest.fail("BE1_TEST_DATABASE_URL must point to a disposable *be1_acceptance database")
    tmp_path = request.getfixturevalue("tmp_path")
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
    d: Api, class_id: str, *, enrolled: bool = False, organization: str | None = None
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


def place(
    d: Api,
    target: str,
    child: str,
    *,
    who: str = "manager",
    revision: int = 1,
    key: str | None = None,
) -> Any:
    return d.client.post(
        f"/api/be1/v1/classes/{target}/profiles/{child}/place",
        headers={
            "X-Test-Principal": d.subjects[who],
            "Idempotency-Key": key or uuid4().hex,
            "If-Match": f'"{revision}"',
        },
    )


def refs(d: Api, **params: Any) -> Any:
    return d.client.get(
        f"/api/be1/v1/organizations/{d.organization}/unplaced-profile-refs",
        headers={"X-Test-Principal": d.subjects["manager"]},
        params=params,
    )


def pending(d: Api, target: str) -> None:
    with d.factory().begin() as db:
        db.add(
            DataLifecycleRequestModel(
                request_id=str(uuid4()),
                organization_id=d.organization,
                request_type="delete",
                target_ref=target,
                state="requested",
                requested_by="synthetic-test",
            )
        )


def snapshot(d: Api, child: str, classes: list[str]) -> tuple[Any, ...]:
    with d.factory()() as db:
        profile = db.get(ManagedProfileModel, child)
        assert profile is not None
        enrollment = list(
            db.execute(
                select(EnrollmentModel.class_id, EnrollmentModel.state).where(
                    EnrollmentModel.child_id == child
                )
            ).all()
        )
        revisions = [db.get(ClassroomModel, c).revision for c in classes]
        audit = db.scalar(
            select(func.count())
            .select_from(CoreAuditEntryModel)
            .where(
                CoreAuditEntryModel.action == "profile.place",
                CoreAuditEntryModel.resource_id == child,
            )
        )
        outbox = db.scalar(
            select(func.count())
            .select_from(CoreOutboxEventModel)
            .where(
                CoreOutboxEventModel.event_type == "be1.profile.placed.v1",
                CoreOutboxEventModel.aggregate_id == child,
            )
        )
        consent = db.scalar(
            select(func.count())
            .select_from(ConsentRecordModel)
            .where(ConsentRecordModel.child_id == child)
        )
        receipts = db.scalar(
            select(func.count())
            .select_from(Be1CommandReceiptModel)
            .where(
                Be1CommandReceiptModel.organization_id == d.organization,
                Be1CommandReceiptModel.operation_scope.like(f"%/profiles/{child}/place"),
            )
        )
        return (profile.class_id, enrollment, revisions, audit, outbox, consent, receipts)


def test_list_filters_and_pages_opaque_refs(api: Api) -> None:
    source = new_class(api)
    good = [new_child(api, source) for _ in range(2)]
    new_child(api, source, enrolled=True)
    inactive = new_child(api, source)
    with api.factory().begin() as db:
        db.get(ManagedProfileModel, inactive).state = "inactive"
    deleted = new_child(api, source)
    pending(api, deleted)
    deleted_class = new_class(api)
    new_child(api, deleted_class)
    pending(api, deleted_class)
    foreign_class = new_class(api, organization=api.foreign_organization)
    new_child(api, foreign_class, organization=api.foreign_organization)
    first = refs(api, limit=1)
    assert first.status_code == 200, first.text
    a = first.json()
    assert a["contract"] == "Be1UnplacedProfileRefListV1"
    assert len(a["items"]) == 1 and a["next_cursor"] is not None
    second = refs(api, limit=1, cursor=a["next_cursor"])
    assert second.status_code == 200, second.text
    b = second.json()
    assert len(b["items"]) == 1 and b["next_cursor"] is None
    items = a["items"] + b["items"]
    assert all(set(item) == {"child_id"} for item in items)
    assert {item["child_id"] for item in items} == set(good)
    pending(api, api.organization)
    result = refs(api)
    assert result.status_code == 200 and result.json()["items"] == []


def test_place_replay_and_already_enrolled(api: Api) -> None:
    source, target = new_class(api), new_class(api)
    child = new_child(api, source)
    key = uuid4().hex
    response = place(api, target, child, key=key)
    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == {"contract", "child_id", "class_id", "enrollment_id", "class_revision"}
    assert (body["contract"], body["child_id"], body["class_id"], body["class_revision"]) == (
        "Be1ProfilePlacementV1",
        child,
        target,
        2,
    )
    assert snapshot(api, child, [source, target]) == (
        target,
        [(target, "active")],
        [1, 2],
        1,
        1,
        0,
        1,
    )
    with api.factory()() as db:
        event = db.scalar(
            select(CoreOutboxEventModel).where(
                CoreOutboxEventModel.aggregate_id == child,
                CoreOutboxEventModel.event_type == "be1.profile.placed.v1",
            )
        )
        assert event is not None and event.payload == {"child_id": child, "class_id": target}
        receipt = db.scalar(
            select(Be1CommandReceiptModel).where(Be1CommandReceiptModel.idempotency_key == key)
        )
        assert receipt is not None and receipt.response_json == body
    before = snapshot(api, child, [source, target])
    replay = place(api, target, child, key=key)
    assert replay.status_code == 200 and replay.json() == body
    mismatch = place(api, target, child, key=key, revision=2)
    assert mismatch.status_code == 400 and mismatch.json()["code"] == "INVALID_IDEMPOTENCY_KEY"
    again = place(api, target, child, revision=2)
    assert again.status_code == 409 and again.json()["code"] == "INVALID_STATE_TRANSITION"
    assert snapshot(api, child, [source, target]) == before


@pytest.mark.parametrize(
    "case",
    [
        "stale",
        "suspended",
        "archived",
        "child_delete",
        "source_delete",
        "target_delete",
        "org_delete",
    ],
)
def test_refusals_do_not_write(api: Api, case: str) -> None:
    source = new_class(api)
    target = new_class(api, state=case if case in {"suspended", "archived"} else "active")
    child = new_child(api, source)
    deletion_targets = {
        "child_delete": child,
        "source_delete": source,
        "target_delete": target,
        "org_delete": api.organization,
    }
    if case in deletion_targets:
        pending(api, deletion_targets[case])
    before = snapshot(api, child, [source, target])
    response = place(api, target, child, revision=2 if case == "stale" else 1)
    assert response.status_code == 409, response.text
    if case == "stale":
        assert response.json()["code"] == "STALE_REVISION"
    assert snapshot(api, child, [source, target]) == before


def test_role_and_organization_boundaries(api: Api) -> None:
    source, target = new_class(api), new_class(api)
    child = new_child(api, source)
    foreign_class = new_class(api, organization=api.foreign_organization)
    foreign_child = new_child(api, foreign_class, organization=api.foreign_organization)
    add_adult(api, "scoped", [target])
    before = snapshot(api, child, [source, target])
    teacher = place(api, target, child, who="scoped")
    foreign = place(api, target, child, who="foreign_manager")
    foreign_profile = place(api, target, foreign_child)
    assert teacher.status_code == 403, teacher.text
    assert foreign.status_code == 404, foreign.text
    assert foreign_profile.status_code == 404, foreign_profile.text
    assert snapshot(api, child, [source, target]) == before


@pytest.mark.parametrize("round_number", range(5))
def test_two_targets_race_for_one_child(api: Api, round_number: int) -> None:
    source, a, b = new_class(api), new_class(api), new_class(api)
    child = new_child(api, source)
    barrier = Barrier(2)

    def run(target: str) -> Any:
        barrier.wait(timeout=30)
        return place(api, target, child)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(run, target) for target in (a, b)]
        responses = [future.result(timeout=90) for future in futures]
    winners = [response for response in responses if response.status_code == 200]
    losers = [response for response in responses if 400 <= response.status_code < 500]
    assert len(winners) == len(losers) == 1, [r.status_code for r in responses]
    winner = winners[0].json()["class_id"]
    assert winner in (a, b)
    assert snapshot(api, child, [source, a, b]) == (
        winner,
        [(winner, "active")],
        [1, 2 if winner == a else 1, 2 if winner == b else 1],
        1,
        1,
        0,
        1,
    )


def test_real_profile_without_target_consent_is_counted_but_hidden(api: Api) -> None:
    source, target = new_class(api), new_class(api)
    add_adult(api, "scoped", [target])
    child, consent_id = f"synthetic-{uuid4().hex[:24]}", str(uuid4())
    purpose = "synthetic-purpose-placement"
    with api.factory().begin() as db:
        db.add(
            ConsentRecordModel(
                consent_id=consent_id,
                organization_id=api.organization,
                class_id=source,
                child_id=child,
                purpose_ref=purpose,
                state="pending",
                recorded_by=api.subjects["manager"],
            )
        )
        db.add(
            ManagedProfileModel(
                child_id=child,
                organization_id=api.organization,
                class_id=source,
                display_name=NAME,
                age_months=60,
                age_revision=1,
                age_source="ADULT_DECLARED",
                consent_id=consent_id,
                consent_purpose_ref=purpose,
                data_origin="REAL",
                created_by="synthetic-seed",
            )
        )
    response = place(api, target, child)
    assert response.status_code == 200, response.text
    roster = api.client.get(
        f"/api/be1/v1/organizations/{api.organization}/classes/{target}/profiles",
        headers={"X-Test-Principal": api.subjects["scoped"]},
    )
    assert roster.status_code == 200, roster.text
    assert roster.json()["active_profile_count"] == 1
    assert roster.json()["items"] == []
    assert snapshot(api, child, [source, target])[5] == 1
