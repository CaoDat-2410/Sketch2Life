"""FEAT-066 T0.1: create class is a keyed command (C-D5/C-D6, SRS l.1649, l.1697) on PostgreSQL.

Runs only against a disposable database whose name contains ``be1_acceptance``. The identity
is a synthetic header principal; no network is used.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from threading import Barrier
from typing import Any
from uuid import uuid4

import pytest
from fastapi import FastAPI, Header
from fastapi.testclient import TestClient
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    Be1CommandReceiptModel,
    ClassroomModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.infrastructure.persistence.core_models import (
    CoreAuditEntryModel,
    CoreOutboxEventModel,
)
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult

ISSUER = "synthetic-t01-issuer"


@dataclass
class T01Api:
    app: FastAPI
    client: TestClient
    organization_id: str
    other_organization_id: str
    manager: str
    other_manager: str
    teacher: str
    parent: str

    def session(self) -> Any:
        return self.app.state.be1_runtime.session_factory


@pytest.fixture
def t01_api(monkeypatch: pytest.MonkeyPatch) -> Iterator[T01Api]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL to a disposable PostgreSQL database")
    if "be1_acceptance" not in database_url.rsplit("/", 1)[-1]:
        pytest.fail("BE1_TEST_DATABASE_URL must point to a disposable *be1_acceptance database")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", database_url)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "development")
    monkeypatch.setenv("SKETCH2LIFE_AI_PROVIDER", "disabled")
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    app = create_app()
    runtime = app.state.be1_runtime
    if runtime.engine is None or runtime.session_factory is None:
        pytest.fail("PostgreSQL runtime did not initialize")
    token = uuid4().hex[:8]
    organization_id = f"synthetic-t01-org-{token}"
    other_organization_id = f"synthetic-t01-other-{token}"
    manager = f"synthetic-t01-manager-{token}"
    other_manager = f"synthetic-t01-other-manager-{token}"
    teacher = f"synthetic-t01-teacher-{token}"
    parent = f"synthetic-t01-parent-{token}"
    with runtime.session_factory.begin() as db:
        for org in (organization_id, other_organization_id):
            db.add(
                OrganizationModel(
                    organization_id=org, display_name=f"Synthetic {org}", state="active"
                )
            )
        for subject, role in (
            (manager, "school_manager"),
            (other_manager, "school_manager"),
            (teacher, "teacher"),
            (parent, "parent"),
        ):
            db.add(
                AdultIdentityModel(
                    subject=subject, issuer=ISSUER, state="active", account_role=role
                )
            )
        db.flush()
        for subject, org, role in (
            (manager, organization_id, "school_admin"),
            (other_manager, other_organization_id, "school_admin"),
            (teacher, organization_id, "teacher"),
        ):
            db.add(
                OrganizationAssignmentModel(
                    assignment_id=str(uuid4()),
                    organization_id=org,
                    subject=subject,
                    class_id=None,
                    role=role,
                    active=True,
                )
            )

    async def verified(
        x_test_principal: str = Header(alias="X-Test-Principal"),
    ) -> VerifiedPrincipal:
        return VerifiedPrincipal(subject=x_test_principal, issuer=ISSUER, roles=frozenset())

    app.dependency_overrides[get_verified_adult] = verified
    try:
        with TestClient(app) as client:
            yield T01Api(
                app,
                client,
                organization_id,
                other_organization_id,
                manager,
                other_manager,
                teacher,
                parent,
            )
    finally:
        app.dependency_overrides.clear()
        runtime.engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def _post(
    api: T01Api,
    *,
    subject: str | None = None,
    organization_id: str | None = None,
    key: str | None,
    display_name: str = "Lớp Mầm",
) -> Any:
    headers = {"X-Test-Principal": subject or api.manager}
    if key is not None:
        headers["Idempotency-Key"] = key
    return api.client.post(
        f"/api/be1/v1/organizations/{organization_id or api.organization_id}/classes",
        json={"display_name": display_name},
        headers=headers,
    )


def _class_count(api: T01Api, organization_id: str | None = None) -> int:
    with api.session()() as db:
        return int(
            db.scalar(
                select(func.count())
                .select_from(ClassroomModel)
                .where(ClassroomModel.organization_id == (organization_id or api.organization_id))
            )
            or 0
        )


def _receipts(api: T01Api, key: str) -> list[Be1CommandReceiptModel]:
    with api.session()() as db:
        return list(
            db.scalars(
                select(Be1CommandReceiptModel).where(Be1CommandReceiptModel.idempotency_key == key)
            ).all()
        )


def test_t01_create_class_returns_201_with_state_and_assignment_revision(t01_api: T01Api) -> None:
    api = t01_api
    key = f"t01-{uuid4().hex}"
    created = _post(api, key=key)
    assert created.status_code == 201, created.text
    body = created.json()
    assert body == {
        "contract": "Be1ClassV1",
        "class_id": body["class_id"],
        "display_name": "Lớp Mầm",
        "state": "active",
        "assignment_revision": 1,
    }
    assert _class_count(api) == 1
    receipts = _receipts(api, key)
    assert len(receipts) == 1
    assert receipts[0].principal_ref == api.manager
    assert receipts[0].operation_scope == f"POST /organizations/{api.organization_id}/classes"
    assert receipts[0].organization_id == api.organization_id
    # The receipt keeps ids and revisions only, never the display name.
    assert receipts[0].response_json == {
        "class_id": body["class_id"],
        "state": "active",
        "assignment_revision": 1,
    }

    listing = api.client.get(
        f"/api/be1/v1/organizations/{api.organization_id}/classes",
        headers={"X-Test-Principal": api.manager},
    )
    item = next(row for row in listing.json()["items"] if row["class_id"] == body["class_id"])
    assert item["state"] == "active" and item["assignment_revision"] == 1


def test_t01_same_key_and_payload_replays_the_original_result(t01_api: T01Api) -> None:
    api = t01_api
    key = f"t01-{uuid4().hex}"
    first = _post(api, key=key)
    assert first.status_code == 201, first.text
    replay = _post(api, key=key)
    assert replay.status_code == 201, replay.text
    assert replay.json() == first.json()
    assert replay.content == first.content
    assert _class_count(api) == 1
    assert len(_receipts(api, key)) == 1
    # A later assignment-counter change does not alter the replayed original result.
    with api.session().begin() as db:
        db.add(
            OrganizationAssignmentModel(
                assignment_id=str(uuid4()),
                organization_id=api.organization_id,
                subject=api.teacher,
                class_id=first.json()["class_id"],
                role="teacher",
                active=False,
            )
        )
    live = api.client.get(
        f"/api/be1/v1/organizations/{api.organization_id}/classes",
        headers={"X-Test-Principal": api.manager},
    )
    item = next(row for row in live.json()["items"] if row["class_id"] == first.json()["class_id"])
    assert item["assignment_revision"] == 2  # the live counter moved ...
    again = _post(api, key=key)
    # ... and the replay still returns the stored original result.
    assert again.status_code == 201 and again.json() == first.json()


def test_t01_same_key_with_another_payload_is_invalid_idempotency_key(t01_api: T01Api) -> None:
    api = t01_api
    key = f"t01-{uuid4().hex}"
    assert _post(api, key=key).status_code == 201
    other = _post(api, key=key, display_name="Lớp Chồi")
    assert other.status_code == 400, other.text
    assert other.json()["code"] == "INVALID_IDEMPOTENCY_KEY"
    assert _class_count(api) == 1


@pytest.mark.parametrize(
    "key", (None, "", "k" * 129, "with space", "tab\tkey"), ids=lambda k: repr(k)[:16]
)
def test_t01_missing_or_invalid_key_is_invalid_request(t01_api: T01Api, key: str | None) -> None:
    api = t01_api
    response = _post(api, key=key)
    assert response.status_code == 400, response.text
    body = response.json()
    assert body["code"] == "INVALID_REQUEST"
    assert isinstance(body["field_errors"], list) and body["field_errors"]
    assert body["field_errors"][0]["field"] == "Idempotency-Key"
    assert _class_count(api) == 0


def test_t01_valid_key_boundary_lengths_are_accepted(t01_api: T01Api) -> None:
    api = t01_api
    for length in (1, 128):
        response = _post(api, key="k" * length, display_name=f"Lớp {length}")
        assert response.status_code == 201, response.text


def test_t01_the_same_key_in_another_organization_is_not_a_replay(t01_api: T01Api) -> None:
    api = t01_api
    key = f"t01-{uuid4().hex}"
    mine = _post(api, key=key)
    theirs = _post(
        api, subject=api.other_manager, organization_id=api.other_organization_id, key=key
    )
    assert mine.status_code == 201 and theirs.status_code == 201
    assert mine.json()["class_id"] != theirs.json()["class_id"]
    assert _class_count(api) == 1 and _class_count(api, api.other_organization_id) == 1


def test_t01_role_and_scope_refusals_keep_403_and_the_uniform_404(t01_api: T01Api) -> None:
    api = t01_api
    # An assigned non-admin of the organization is refused inside the scope: 403.
    forbidden = _post(api, subject=api.teacher, key=f"t01-{uuid4().hex}")
    assert forbidden.status_code == 403, forbidden.text
    assert forbidden.json()["code"] == "ACTION_NOT_ALLOWED"
    # A Parent, an unassigned outsider and a manager of another organization are all the
    # uniform 404 (SRS l.864-865), each with a valid key so the 400 does not hide them.
    uniform = []
    for subject in (api.parent, "synthetic-t01-outsider", api.other_manager):
        denied = _post(api, subject=subject, key=f"t01-{uuid4().hex}")
        assert denied.status_code == 404, (subject, denied.text)
        uniform.append(denied.json()["code"])
    assert set(uniform) == {"RESOURCE_NOT_FOUND"}
    assert _class_count(api) == 0


def test_t01_replay_is_refused_after_the_manager_is_deactivated(t01_api: T01Api) -> None:
    api = t01_api
    key = f"t01-{uuid4().hex}"
    assert _post(api, key=key).status_code == 201
    with api.session().begin() as db:
        db.execute(
            update(AdultIdentityModel)
            .where(AdultIdentityModel.subject == api.manager)
            .values(state="disabled")
        )
    refused = _post(api, key=key)
    assert refused.status_code == 404, refused.text
    assert refused.json()["code"] == "RESOURCE_NOT_FOUND"


def test_t01_two_concurrent_requests_with_one_key_create_one_class(t01_api: T01Api) -> None:
    api = t01_api
    gate = Barrier(2)

    def raced(key: str) -> Any:
        gate.wait(timeout=15)
        return _post(api, key=key)

    for round_no in range(3):
        key = f"t01-race-{round_no}-{uuid4().hex}"
        before = _class_count(api)
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(raced, key) for _ in range(2)]
            results = [future.result() for future in futures]
        assert [response.status_code for response in results] == [201, 201]
        assert results[0].json() == results[1].json()
        assert _class_count(api) == before + 1
        assert len(_receipts(api, key)) == 1
    # The loser rolled back with its audit and event rows: one of each per class, no orphans.
    with api.session()() as db:
        audits = db.scalar(
            select(func.count())
            .select_from(CoreAuditEntryModel)
            .where(
                CoreAuditEntryModel.organization_id == api.organization_id,
                CoreAuditEntryModel.action == "class.create",
            )
        )
        events = db.scalar(
            select(func.count())
            .select_from(CoreOutboxEventModel)
            .where(
                CoreOutboxEventModel.organization_id == api.organization_id,
                CoreOutboxEventModel.event_type == "be1.class.created.v1",
            )
        )
    assert audits == events == _class_count(api)


def _hide_receipt_lookup(monkeypatch: pytest.MonkeyPatch, *, times: int) -> list[int]:
    """Make the first `times` receipt lookups of create class miss, as a lost race would."""
    original = Session.get
    state = [0]

    def get(self: Session, entity: Any, ident: Any, *args: Any, **kwargs: Any) -> Any:
        if entity is Be1CommandReceiptModel and state[0] < times:
            state[0] += 1
            return None
        return original(self, entity, ident, *args, **kwargs)

    monkeypatch.setattr(Session, "get", get)
    return state


def test_t01_commit_conflict_branch_replays_and_rolls_back_the_loser(
    t01_api: T01Api, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Deterministic loser: the lookup misses, the receipt insert hits the primary key."""
    api = t01_api
    key = f"t01-{uuid4().hex}"
    first = _post(api, key=key)
    assert first.status_code == 201
    calls = _hide_receipt_lookup(monkeypatch, times=1)
    loser = _post(api, key=key)
    assert calls == [1]  # the first lookup was hidden, so the IntegrityError branch ran
    assert loser.status_code == 201, loser.text
    assert loser.content == first.content
    assert _class_count(api) == 1 and len(_receipts(api, key)) == 1
    with api.session()() as db:
        audits = db.scalar(
            select(func.count())
            .select_from(CoreAuditEntryModel)
            .where(
                CoreAuditEntryModel.organization_id == api.organization_id,
                CoreAuditEntryModel.action == "class.create",
            )
        )
        events = db.scalar(
            select(func.count())
            .select_from(CoreOutboxEventModel)
            .where(
                CoreOutboxEventModel.organization_id == api.organization_id,
                CoreOutboxEventModel.event_type == "be1.class.created.v1",
            )
        )
    assert audits == events == 1  # the loser's audit and event rows rolled back with it

    # Same lost race with another payload: still 400 INVALID_IDEMPOTENCY_KEY, no new class.
    _hide_receipt_lookup(monkeypatch, times=1)
    other = _post(api, key=key, display_name="Lớp Chồi")
    assert other.status_code == 400 and other.json()["code"] == "INVALID_IDEMPOTENCY_KEY"
    assert _class_count(api) == 1


def test_t01_commit_conflict_without_a_receipt_is_resource_conflict(
    t01_api: T01Api, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A commit conflict that leaves no receipt to replay answers 409 and leaves no class."""
    api = t01_api
    key = f"t01-{uuid4().hex}"
    assert _post(api, key=key).status_code == 201
    # The first lookup, the lookup after the capacity lock, and the re-read all miss.
    _hide_receipt_lookup(monkeypatch, times=3)
    conflict = _post(api, key=key)
    assert conflict.status_code == 409, conflict.text
    assert conflict.json()["code"] == "RESOURCE_CONFLICT"
    assert _class_count(api) == 1
