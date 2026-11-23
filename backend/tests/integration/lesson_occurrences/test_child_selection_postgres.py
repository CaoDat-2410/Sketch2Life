"""FEAT-066 T-4b1: the Teacher random-child selection on PostgreSQL.

SRS l.341-352 (candidates, equal-probability pick, one stale reselect, empty stops, every read
revalidates, confirm before a run exists), l.354 and BR-34 (metadata-only evidence), l.549-554,
l.1441, l.1447-1448, l.1697-1699, AC-56. Runs only against a disposable database whose name
contains ``be1_acceptance`` and ``frc08``. Principals are injected through the ``X-Test-Principal``
header; every identity, class, child and plan is synthetic. The selection service is built with an
injected clock, generator and gate (a dependency override), except in the two settings tests that
use the shipped dependency and the real runtime settings.
"""

from __future__ import annotations

import importlib.util
import json
import logging
import os
import secrets
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Barrier
from typing import Any
from uuid import uuid4

import pytest
from fastapi import Depends, FastAPI, Header
from fastapi.testclient import TestClient
from sqlalchemy import func, insert, select, text, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.domain.lesson_occurrences.child_selection import (
    POLICY_VERSION,
    SelectionPolicy,
    selection_sha256,
)
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.lesson_occurrences.child_selection import (
    ChildSelectionService,
    SyntheticGate,
    candidate_statement,
    purge_child_selections,
)
from sketch2life.infrastructure.lesson_occurrences.tables import CHILD_SELECTIONS, OCCURRENCES
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    Be1CommandReceiptModel,
    ClassroomModel,
    DataLifecycleRequestModel,
    EnrollmentModel,
    ManagedProfileModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.routers.lesson_occurrences import get_child_selection_service

ISSUER = "synthetic-t4b1-issuer"
MIGRATION = (
    Path(__file__).resolve().parents[3]
    / "alembic"
    / "versions"
    / "20261120_sel_0001_child_selection.py"
)
NAME_PREFIX = "Synthetic Kid"
SELECTION_FIELDS = {
    "contract",
    "selection_id",
    "occurrence_id",
    "outcome",
    "state",
    "revision",
    "draw_no",
    "reselect_available",
    "issued_at",
    "expires_at",
    "confirmation_expires_at",
    "selection_sha256",
    "plan",
    "consumed_run_ref",
    "child",
}


class Clock:
    """A settable clock for the service and nothing else (the database keeps its own now())."""

    def __init__(self) -> None:
        self.moment = datetime.now(UTC)

    def __call__(self) -> datetime:
        return self.moment

    def advance(self, seconds: float) -> None:
        self.moment += timedelta(seconds=seconds)


@dataclass
class Api:
    app: FastAPI
    client: TestClient
    token: str
    organization: str
    other_organization: str
    clock: Clock = field(default_factory=Clock)
    gate_on: bool = True
    policy: SelectionPolicy = field(default_factory=SelectionPolicy)
    forced: list[int] = field(default_factory=list)
    classes: dict[str, str] = field(default_factory=dict)
    subjects: dict[str, str] = field(default_factory=dict)
    accounts: dict[str, str] = field(default_factory=dict)
    children: dict[str, str] = field(default_factory=dict)  # child id -> display name
    counter: int = 0

    def sessions(self) -> Any:
        return self.app.state.be1_runtime.session_factory

    @property
    def engine(self) -> Any:
        return self.app.state.be1_runtime.engine

    def randbelow(self, bound: int) -> int:
        if self.forced:
            return self.forced.pop(0) % bound
        return secrets.randbelow(bound)


def _identity(db: Any, subject: str, role: str, *, state: str = "active") -> str:
    row = AdultIdentityModel(subject=subject, issuer=ISSUER, state=state, account_role=role)
    db.add(row)
    db.flush()
    return row.account_id


def _assign(
    db: Any,
    organization: str,
    subject: str,
    role: str,
    class_id: str | None,
    *,
    active: bool = True,
) -> None:
    db.add(
        OrganizationAssignmentModel(
            assignment_id=str(uuid4()),
            organization_id=organization,
            subject=subject,
            class_id=class_id,
            role=role,
            active=active,
        )
    )


def _build(monkeypatch: pytest.MonkeyPatch, *, real_service: bool, pilot: bool) -> Iterator[Api]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL to a disposable PostgreSQL database")
    name = database_url.rsplit("/", 1)[-1]
    if "be1_acceptance" not in name or "frc08" not in name:
        pytest.fail("BE1_TEST_DATABASE_URL must be a disposable frc08*be1_acceptance db")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", database_url)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "development")
    monkeypatch.setenv("SKETCH2LIFE_AI_PROVIDER", "disabled")
    monkeypatch.setenv("SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED", "true" if pilot else "false")
    monkeypatch.delenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", raising=False)
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    app = create_app()
    runtime = app.state.be1_runtime
    if runtime.engine is None or runtime.session_factory is None:
        pytest.fail("PostgreSQL runtime did not initialize")
    token = uuid4().hex[:8]
    organization, other = f"synthetic-t4b1-org-{token}", f"synthetic-t4b1-other-{token}"
    d = Api(app, TestClient(app), token, organization, other)

    def label(value: str) -> str:
        return f"synthetic-t4b1-{value}-{token}"

    with runtime.session_factory.begin() as db:
        for org in (organization, other):
            db.add(OrganizationModel(organization_id=org, display_name=org, state="active"))
        db.flush()
        for key, org in (("a1", organization), ("a2", organization), ("b1", other)):
            class_id = f"class-{key}-{token}"
            d.classes[key] = class_id
            db.add(
                ClassroomModel(
                    class_id=class_id,
                    organization_id=org,
                    display_name=key,
                    state="active",
                    created_by="synthetic",
                )
            )
        db.flush()
        people = (
            ("t1", "teacher", organization, "a1", "teacher"),  # the responsible Teacher
            ("t4", "teacher", organization, "a1", "teacher"),  # a second teacher row on a1
            ("t2", "teacher", organization, "a2", "teacher"),
            ("g1", "teacher", organization, "a1", "guide"),
            ("o1", "teacher", organization, "a1", "observer"),
            ("tother", "teacher", other, "b1", "teacher"),
            ("orgt", "teacher", organization, None, "teacher"),
            ("manager", "school_manager", organization, None, "school_admin"),
        )
        for key, role, org, class_key, assignment_role in people:
            subject = label(key)
            d.subjects[key] = subject
            d.accounts[key] = _identity(db, subject, role)
            _assign(db, org, subject, assignment_role, d.classes[class_key] if class_key else None)
        d.subjects["revoked"] = label("revoked")
        d.accounts["revoked"] = _identity(db, label("revoked"), "teacher")
        _assign(db, organization, label("revoked"), "teacher", d.classes["a1"], active=False)
        d.subjects["inactive"] = label("inactive")
        d.accounts["inactive"] = _identity(db, label("inactive"), "teacher", state="disabled")
        _assign(db, organization, label("inactive"), "teacher", d.classes["a1"])
        d.subjects["parent"] = label("parent")
        d.accounts["parent"] = _identity(db, label("parent"), "parent")
        d.subjects["platform"] = label("platform")
        d.accounts["platform"] = _identity(db, label("platform"), "platform_admin")
        d.subjects["stranger"] = label("stranger")  # no identity row at all

    async def verified(
        x_test_principal: str = Header(alias="X-Test-Principal"),
    ) -> VerifiedPrincipal:
        return VerifiedPrincipal(subject=x_test_principal, issuer=ISSUER, roles=frozenset())

    app.dependency_overrides[get_verified_adult] = verified
    if not real_service:

        def service(db: Session = Depends(get_db)) -> ChildSelectionService:  # noqa: B008
            return ChildSelectionService(
                db,
                gate=SyntheticGate(d.gate_on),
                policy=d.policy,
                clock=d.clock,
                randbelow=d.randbelow,
            )

        app.dependency_overrides[get_child_selection_service] = service
    try:
        with d.client:
            yield d
    finally:
        app.dependency_overrides.clear()
        runtime.engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


@pytest.fixture
def api(monkeypatch: pytest.MonkeyPatch) -> Iterator[Api]:
    yield from _build(monkeypatch, real_service=False, pilot=True)


@pytest.fixture
def api_pilot_on(monkeypatch: pytest.MonkeyPatch) -> Iterator[Api]:
    yield from _build(monkeypatch, real_service=True, pilot=True)


@pytest.fixture
def api_pilot_off(monkeypatch: pytest.MonkeyPatch) -> Iterator[Api]:
    yield from _build(monkeypatch, real_service=True, pilot=False)


# ----------------------------------------------------------------------------- helpers
def headers(subject: str, key: str | None = None, **extra: str) -> dict[str, str]:
    result = {"X-Test-Principal": subject}
    if key is not None:
        result["Idempotency-Key"] = key
    result.update(extra)
    return result


@dataclass
class Occurrence:
    occurrence_id: str
    plan_revision_id: str
    plan_hash: str
    class_key: str = "a1"
    plans: int = 1


def _plan(d: Api, occurrence_id: str, head: int, who: str = "t1") -> tuple[str, str]:
    created = d.client.post(
        f"/v1/lesson-occurrences/{occurrence_id}/plan-revisions",
        json={
            "expected_head_revision_no": head,
            "objectives": ["Nhận biết hình tròn"],
            "teacher_direction": "Câu chuyện về chú mèo đi tìm bạn",
        },
        headers=headers(d.subjects[who], uuid4().hex),
    )
    assert created.status_code == 201, created.text
    plan = created.json()
    confirmed = d.client.post(
        f"/v1/lesson-occurrences/{occurrence_id}/plan-revisions/{plan['revision_no']}/confirm",
        json={"expected_plan_hash": plan["content_hash"]},
        headers=headers(d.subjects[who], uuid4().hex),
    )
    assert confirmed.status_code == 200, confirmed.text
    with d.sessions()() as db:
        pointer = db.execute(
            select(OCCURRENCES.c.approved_plan_revision_id).where(
                OCCURRENCES.c.occurrence_id == occurrence_id
            )
        ).scalar_one()
    return str(pointer), str(plan["content_hash"])


def make_occurrence(
    d: Api, *, who: str = "t1", class_key: str = "a1", approve: bool = True
) -> Occurrence:
    created = d.client.post(
        "/v1/lesson-occurrences",
        json={"class_id": d.classes[class_key], "title": "Bài học vẽ"},
        headers=headers(d.subjects[who], uuid4().hex),
    )
    assert created.status_code == 201, created.text
    occurrence_id = str(created.json()["occurrence_id"])
    if not approve:
        return Occurrence(occurrence_id, "", "", class_key, 0)
    plan_id, plan_hash = _plan(d, occurrence_id, 0, who)
    return Occurrence(occurrence_id, plan_id, plan_hash, class_key, 1)


def reapprove(d: Api, occ: Occurrence) -> None:
    occ.plan_revision_id, occ.plan_hash = _plan(d, occ.occurrence_id, occ.plans)
    occ.plans += 1


def add_child(
    d: Api,
    class_key: str = "a1",
    *,
    age: int = 60,
    origin: str = "SYNTHETIC_DEV",
    state: str = "active",
    enrolled: bool = True,
    organization: str | None = None,
) -> str:
    d.counter += 1
    child_id = f"synthetic-child-{d.token}-{d.counter}"
    name = f"{NAME_PREFIX} {d.token} {d.counter}"
    d.children[child_id] = name
    org = organization or (d.other_organization if class_key == "b1" else d.organization)
    consent = origin == "REAL"
    with d.sessions().begin() as db:
        db.add(
            ManagedProfileModel(
                child_id=child_id,
                organization_id=org,
                class_id=d.classes[class_key],
                display_name=name,
                age_months=age,
                age_revision=1,
                age_source="SYNTHETIC_FIXTURE",
                consent_id=str(uuid4()) if consent else None,
                consent_purpose_ref="synthetic-purpose" if consent else None,
                data_origin=origin,
                state=state,
                created_by="synthetic",
            )
        )
        db.flush()
        if enrolled:
            db.add(
                EnrollmentModel(
                    enrollment_id=str(uuid4()),
                    organization_id=org,
                    class_id=d.classes[class_key],
                    child_id=child_id,
                    state="active",
                    created_by="synthetic",
                )
            )
    return child_id


def withdraw(d: Api, child_id: str) -> None:
    with d.sessions().begin() as db:
        db.execute(
            update(EnrollmentModel)
            .where(EnrollmentModel.child_id == child_id)
            .values(state="withdrawn")
        )


def sel_url(occurrence_id: str, selection_id: str | None = None, suffix: str = "") -> str:
    base = f"/v1/lesson-occurrences/{occurrence_id}/child-selections"
    return base if selection_id is None else f"{base}/{selection_id}{suffix}"


def post_select(d: Api, who: str, occ: Occurrence | str, key: str | None = None) -> Any:
    occurrence_id = occ if isinstance(occ, str) else occ.occurrence_id
    return d.client.post(
        sel_url(occurrence_id), json={}, headers=headers(d.subjects[who], key or uuid4().hex)
    )


def get_sel(d: Api, who: str, occ: Occurrence | str, selection_id: str, **extra: str) -> Any:
    occurrence_id = occ if isinstance(occ, str) else occ.occurrence_id
    return d.client.get(
        sel_url(occurrence_id, selection_id), headers=headers(d.subjects[who], None, **extra)
    )


def post_confirm(
    d: Api,
    who: str,
    occ: Occurrence | str,
    offer: dict[str, Any],
    *,
    revision: int | None = None,
    sha: str | None = None,
    key: str | None = None,
) -> Any:
    occurrence_id = occ if isinstance(occ, str) else occ.occurrence_id
    return d.client.post(
        sel_url(occurrence_id, offer["selection_id"], "/confirmation"),
        json={"expected_selection_sha256": sha or offer["selection_sha256"]},
        headers=headers(
            d.subjects[who],
            key or uuid4().hex,
            **{"If-Match": f'"{revision if revision is not None else offer["revision"]}"'},
        ),
    )


def rows(d: Api, occurrence_id: str) -> list[dict[str, Any]]:
    with d.sessions()() as db:
        return [
            dict(row)
            for row in db.execute(
                select(CHILD_SELECTIONS)
                .where(CHILD_SELECTIONS.c.occurrence_id == occurrence_id)
                .order_by(CHILD_SELECTIONS.c.seq)
            )
            .mappings()
            .all()
        ]


def occurrence_row(d: Api, occurrence_id: str) -> dict[str, Any]:
    with d.sessions()() as db:
        return dict(
            db.execute(select(OCCURRENCES).where(OCCURRENCES.c.occurrence_id == occurrence_id))
            .mappings()
            .one()
        )


def run_tables_snapshot(d: Api) -> dict[str, int]:
    """Row counts of every story, ai_jobs, quota and usage table (nothing may move)."""
    with d.sessions()() as db:
        names = db.execute(
            text(
                "select table_schema || '.' || table_name from information_schema.tables "
                "where table_schema in ('story', 'ai_jobs') or table_name ilike '%quota%' "
                "or table_name ilike '%usage%' or table_name ilike '%capacity%' "
                "order by 1"
            )
        ).scalars()
        counts = {}
        for name in list(names):
            counts[name] = int(db.execute(text(f"select count(*) from {name}")).scalar_one())  # noqa: S608
    assert counts, "the snapshot found no run tables"
    return counts


def child_of(body: dict[str, Any]) -> str:
    assert body["child"] is not None, body
    return str(body["child"]["profile_id"])


def state_of(d: Api, occurrence_id: str) -> list[tuple[str, str, int]]:
    return [(r["kind"], r["state"], r["revision"]) for r in rows(d, occurrence_id)]


def assert_no_child_data(response: Any, d: Api) -> None:
    text_body = response.text
    assert "display_name" not in text_body and "age_months" not in text_body
    assert NAME_PREFIX not in text_body
    assert not any(child in text_body for child in d.children)


# ----------------------------------------------------------------------------- the full flow
def test_full_flow_select_get_confirm_and_nothing_else_moves(
    api: Api, caplog: pytest.LogCaptureFixture
) -> None:
    d = api
    caplog.set_level(logging.DEBUG)
    children = [add_child(d) for _ in range(3)]
    occ = make_occurrence(d)
    before_runs = run_tables_snapshot(d)
    before_occurrence = occurrence_row(d, occ.occurrence_id)

    created = post_select(d, "t1", occ)
    assert created.status_code == 201, created.text
    offer = created.json()
    assert set(offer) == SELECTION_FIELDS
    assert offer["outcome"] == "SELECTED" and offer["state"] == "OPEN"
    assert offer["revision"] == 1 and offer["draw_no"] == 1 and offer["reselect_available"] is True
    assert offer["plan"] == {"revision_no": 1, "plan_hash": occ.plan_hash}
    assert child_of(offer) in children
    assert offer["child"] == {
        "profile_id": child_of(offer),
        "display_name": d.children[child_of(offer)],
        "age_months": 60,
    }
    assert (
        created.headers["ETag"] == '"1"' and created.headers["Cache-Control"] == "private, no-store"
    )
    assert created.headers["Location"] == sel_url(occ.occurrence_id, offer["selection_id"])
    expected_sha = selection_sha256(
        selection_id=offer["selection_id"],
        occurrence_id=occ.occurrence_id,
        plan_revision_id=occ.plan_revision_id,
        plan_hash=occ.plan_hash,
        selected_child_ref=child_of(offer),
        candidate_set_hash=rows(d, occ.occurrence_id)[0]["candidate_set_hash"],
        policy_version=POLICY_VERSION,
    )
    assert offer["selection_sha256"] == expected_sha

    read = get_sel(d, "t1", occ, offer["selection_id"])
    assert read.status_code == 200 and read.json() == offer
    assert read.headers["Cache-Control"] == "private, no-store"
    # a body that carries child data is never answered 304
    assert (
        get_sel(d, "t1", occ, offer["selection_id"], **{"If-None-Match": '"1"'}).status_code == 200
    )

    confirmed = post_confirm(d, "t1", occ, offer)
    assert confirmed.status_code == 200, confirmed.text
    body = confirmed.json()
    assert body["state"] == "CONFIRMED" and body["revision"] == 2
    assert child_of(body) == child_of(offer)
    assert body["confirmation_expires_at"] is not None
    assert confirmed.headers["ETag"] == '"2"'

    stored = rows(d, occ.occurrence_id)
    assert len(stored) == 1
    assert stored[0]["state"] == "CONFIRMED" and stored[0]["confirmed_by"] == d.accounts["t1"]
    assert stored[0]["candidate_count"] == 3 and stored[0]["kind"] == "DRAW"
    assert stored[0]["eligibility_basis"] == "SYNTHETIC_DEV" and stored[0]["draw_no"] == 1
    assert stored[0]["policy_version"] == POLICY_VERSION
    # nothing but the selection row was written: no run, job, quota, claim or occurrence change
    assert run_tables_snapshot(d) == before_runs
    after_occurrence = occurrence_row(d, occ.occurrence_id)
    for column in (
        "revision",
        "state",
        "sample_slot_state",
        "successful_sample_run_ref",
        "approved_plan_revision_id",
        "updated_at",
    ):
        assert after_occurrence[column] == before_occurrence[column], column

    # the offer was read at revision 1: confirming it again with a new key is stale (current 2)
    again = post_confirm(d, "t1", occ, offer)
    assert again.status_code == 409 and again.json()["code"] == "STALE_REVISION"

    # privacy: the selection id only in audit and receipts, no name or child ref anywhere
    with d.sessions()() as db:
        audits = db.scalars(
            select(CoreAuditEntryModel).where(
                CoreAuditEntryModel.resource_id == occ.occurrence_id,
                CoreAuditEntryModel.action.like("lesson.occurrence.child_selection.%"),
            )
        ).all()
        receipts = db.scalars(
            select(Be1CommandReceiptModel).where(
                Be1CommandReceiptModel.organization_id == d.organization,
                Be1CommandReceiptModel.operation_scope.like("lesson-occurrence-child-selection:%"),
            )
        ).all()
    assert sorted(a.action for a in audits) == [
        "lesson.occurrence.child_selection.confirm",
        "lesson.occurrence.child_selection.draw",
    ]
    for audit in audits:
        assert (
            audit.decision == offer["selection_id"] and audit.resource_type == "lesson_occurrence"
        )
        assert audit.actor_ref == d.accounts["t1"]
    assert len(receipts) == 2
    for receipt in receipts:
        assert set(receipt.response_json) == {"selection_id", "outcome", "state", "status"}
    haystack = json.dumps([r.response_json for r in receipts]) + " ".join(
        f"{a.action} {a.decision} {a.resource_id} {a.actor_ref}" for a in audits
    )
    assert NAME_PREFIX not in haystack and not any(child in haystack for child in d.children)
    assert NAME_PREFIX not in caplog.text and not any(child in caplog.text for child in d.children)


# ----------------------------------------------------------------------------- authorization
@pytest.mark.parametrize(
    "who", ["stranger", "tother", "manager", "parent", "platform", "revoked", "inactive", "t2"]
)
def test_not_covered_callers_get_the_uniform_404_on_every_route(api: Api, who: str) -> None:
    d = api
    add_child(d)
    occ = make_occurrence(d)
    offer = post_select(d, "t1", occ).json()
    unknown = post_select(d, "stranger", "no-such-occurrence")
    for response in (
        post_select(d, who, occ),
        get_sel(d, who, occ, offer["selection_id"]),
        post_confirm(d, who, occ, offer),
    ):
        assert response.status_code == 404, (who, response.text)
        assert response.json()["code"] == "RESOURCE_NOT_FOUND"
        assert_no_child_data(response, d)
    assert unknown.status_code == 404 and unknown.json()["code"] == "RESOURCE_NOT_FOUND"
    assert len(rows(d, occ.occurrence_id)) == 1


@pytest.mark.parametrize("who", ["orgt", "g1", "o1", "t4"])
def test_covered_but_not_the_responsible_teacher_is_403_without_child_data(
    api: Api, who: str
) -> None:
    d = api
    add_child(d)
    occ = make_occurrence(d)
    offer = post_select(d, "t1", occ).json()
    for response in (
        post_select(d, who, occ),
        get_sel(d, who, occ, offer["selection_id"]),
        post_confirm(d, who, occ, offer),
    ):
        assert response.status_code == 403, (who, response.text)
        assert response.json()["code"] == "ACTION_NOT_ALLOWED"
        assert_no_child_data(response, d)
    assert state_of(d, occ.occurrence_id) == [("DRAW", "OPEN", 1)]


def test_a_selection_of_another_occurrence_is_404(api: Api) -> None:
    d = api
    add_child(d)
    first, second = make_occurrence(d), make_occurrence(d)
    offer = post_select(d, "t1", first).json()
    assert get_sel(d, "t1", second, offer["selection_id"]).status_code == 404
    assert post_confirm(d, "t1", second, offer).status_code == 404
    assert get_sel(d, "t1", first, str(uuid4())).status_code == 404
    assert get_sel(d, "t1", first, "x" * 40).status_code == 404
    assert post_select(d, "t1", "o" * 40).status_code == 404


def test_a_revoked_assignment_is_404_at_the_next_command_and_read(api: Api) -> None:
    d = api
    add_child(d)
    occ = make_occurrence(d)
    offer = post_select(d, "t1", occ).json()
    with d.sessions().begin() as db:
        db.execute(
            update(OrganizationAssignmentModel)
            .where(OrganizationAssignmentModel.subject == d.subjects["t1"])
            .values(active=False)
        )
    for response in (
        post_select(d, "t1", occ),
        get_sel(d, "t1", occ, offer["selection_id"]),
        post_confirm(d, "t1", occ, offer),
    ):
        assert response.status_code == 404
        assert response.json()["code"] == "RESOURCE_NOT_FOUND"
    assert state_of(d, occ.occurrence_id) == [("DRAW", "OPEN", 1)]


def test_a_reassigned_occurrence_voids_the_former_teachers_live_offer(api: Api) -> None:
    """R2 N-3: case a needs the live row to be the caller's own."""
    d = api
    add_child(d)
    occ = make_occurrence(d)
    first = post_select(d, "t1", occ).json()
    with d.sessions().begin() as db:
        db.execute(
            update(OCCURRENCES)
            .where(OCCURRENCES.c.occurrence_id == occ.occurrence_id)
            .values(responsible_teacher_ref=d.accounts["t4"])
        )
    assert post_select(d, "t1", occ).status_code == 403
    second = post_select(d, "t4", occ)
    assert second.status_code == 201, second.text
    assert second.json()["selection_id"] != first["selection_id"]
    assert child_of(second.json()) == child_of(first)  # the sticky child
    assert [(r["kind"], r["state"], r["teacher_ref"]) for r in rows(d, occ.occurrence_id)] == [
        ("DRAW", "VOID", d.accounts["t1"]),
        ("REOFFER", "OPEN", d.accounts["t4"]),
    ]
    # the former Teacher can no longer use the old offer
    assert post_confirm(d, "t1", occ, first).status_code == 403


def test_a_confirmed_row_of_a_former_teacher_is_404_for_the_new_one(api: Api) -> None:
    """T4B1-IR-03: GET and the CONFIRMED confirm branch check the actor of the row."""
    d = api
    add_child(d)
    occ = make_occurrence(d)
    offer = post_select(d, "t1", occ).json()
    confirmed = post_confirm(d, "t1", occ, offer).json()
    assert confirmed["state"] == "CONFIRMED"
    with d.sessions().begin() as db:
        db.execute(
            update(OCCURRENCES)
            .where(OCCURRENCES.c.occurrence_id == occ.occurrence_id)
            .values(responsible_teacher_ref=d.accounts["t4"])
        )
    seen = get_sel(d, "t4", occ, offer["selection_id"])
    assert seen.status_code == 404 and seen.json()["code"] == "RESOURCE_NOT_FOUND"
    assert_no_child_data(seen, d)
    again = post_confirm(d, "t4", occ, confirmed)
    assert again.status_code == 404 and again.json()["code"] == "RESOURCE_NOT_FOUND"
    assert_no_child_data(again, d)
    assert state_of(d, occ.occurrence_id) == [("DRAW", "CONFIRMED", 2)]


def test_confirming_a_confirmed_offer_whose_child_left_is_a_stale_409(api: Api) -> None:
    """T4B1-IR-02: the CONFIRMED branch revalidates like the OPEN path and keeps the STALE write."""
    d = api
    add_child(d)
    add_child(d)
    occ = make_occurrence(d)
    offer = post_select(d, "t1", occ).json()
    confirmed = post_confirm(d, "t1", occ, offer).json()
    assert confirmed["state"] == "CONFIRMED" and confirmed["revision"] == 2
    # while the child is eligible the same confirm is idempotent (a new key, the same answer)
    same = post_confirm(d, "t1", occ, confirmed, revision=2, sha=offer["selection_sha256"])
    assert same.status_code == 200 and same.json()["state"] == "CONFIRMED"
    withdraw(d, child_of(offer))
    # a revalidating read first shows the computed state and no child, and is never a 304
    read = get_sel(d, "t1", occ, offer["selection_id"], **{"If-None-Match": '"2"'})
    assert read.status_code == 200 and read.json()["state"] == "STALE"
    assert read.json()["child"] is None
    refused = post_confirm(d, "t1", occ, confirmed, revision=2, sha=offer["selection_sha256"])
    assert refused.status_code == 409 and refused.json()["code"] == "STALE_REVISION"
    assert refused.json()["current_version"] == 3
    assert_no_child_data(refused, d)
    assert state_of(d, occ.occurrence_id) == [("DRAW", "STALE", 3)]


# ----------------------------------------------------------------------------- preconditions
def test_preconditions_of_both_commands(api: Api) -> None:
    d = api
    add_child(d)
    # no plan at all, then a draft plan only: 422 LESSON_PLAN_NOT_APPROVED
    bare = make_occurrence(d, approve=False)
    refused = post_select(d, "t1", bare)
    assert refused.status_code == 422 and refused.json()["code"] == "LESSON_PLAN_NOT_APPROVED"
    draft = d.client.post(
        f"/v1/lesson-occurrences/{bare.occurrence_id}/plan-revisions",
        json={
            "expected_head_revision_no": 0,
            "objectives": ["Mục tiêu"],
            "teacher_direction": "Hướng dẫn",
        },
        headers=headers(d.subjects["t1"], uuid4().hex),
    )
    assert draft.status_code == 201
    assert post_select(d, "t1", bare).status_code == 422

    occ = make_occurrence(d)
    offer = post_select(d, "t1", occ).json()
    # the sample slot is claimed (set by SQL): 409 SAMPLE_VIDEO_ALREADY_EXISTS on both commands
    with d.sessions().begin() as db:
        db.execute(
            update(OCCURRENCES)
            .where(OCCURRENCES.c.occurrence_id == occ.occurrence_id)
            .values(
                sample_slot_state="CLAIMED",
                sample_claimed_at=datetime.now(UTC),
                successful_sample_run_ref="synthetic-run-1",
            )
        )
    for response in (post_select(d, "t1", occ), post_confirm(d, "t1", occ, offer)):
        assert response.status_code == 409
        assert response.json()["code"] == "SAMPLE_VIDEO_ALREADY_EXISTS"
        assert_no_child_data(response, d)
    # reading is still allowed
    assert get_sel(d, "t1", occ, offer["selection_id"]).status_code == 200

    # a suspended class and an archived class: 409 INVALID_STATE_TRANSITION (not the BE1 404)
    for state in ("suspended", "archived"):
        other = make_occurrence(d)
        other_offer = post_select(d, "t1", other).json()
        with d.sessions().begin() as db:
            db.execute(
                update(ClassroomModel)
                .where(ClassroomModel.class_id == d.classes["a1"])
                .values(state=state)
            )
        try:
            for response in (
                post_select(d, "t1", other),
                post_confirm(d, "t1", other, other_offer),
            ):
                assert response.status_code == 409, (state, response.text)
                assert response.json()["code"] == "INVALID_STATE_TRANSITION"
        finally:
            with d.sessions().begin() as db:
                db.execute(
                    update(ClassroomModel)
                    .where(ClassroomModel.class_id == d.classes["a1"])
                    .values(state="active")
                )

    # an archived occurrence is read-only too
    archived = make_occurrence(d)
    with d.sessions().begin() as db:
        db.execute(
            update(OCCURRENCES)
            .where(OCCURRENCES.c.occurrence_id == archived.occurrence_id)
            .values(state="ARCHIVED")
        )
    assert post_select(d, "t1", archived).status_code == 409


# ----------------------------------------------------------------------------- the predicate
def _candidates(d: Api, class_key: str = "a1") -> list[str]:
    org = d.other_organization if class_key == "b1" else d.organization
    with d.sessions()() as db:
        return sorted(
            str(c) for c in db.execute(candidate_statement(org, d.classes[class_key])).scalars()
        )


def test_candidate_predicate_matrix_on_postgres(api: Api) -> None:
    d = api
    good = [add_child(d, age=36), add_child(d, age=120), add_child(d, age=60)]
    add_child(d, age=121)
    add_child(d, age=155)
    add_child(d, origin="REAL")  # consent refs set, still never a candidate (X-19)
    add_child(d, origin="LEGACY_UNCLASSIFIED")
    add_child(d, state="inactive")
    add_child(d, enrolled=False)
    withdrawn = add_child(d)
    withdraw(d, withdrawn)
    other_class = add_child(d, "a2")
    foreign = add_child(d, "b1")
    assert _candidates(d) == sorted(good)
    assert other_class not in _candidates(d) and foreign not in _candidates(d)
    assert _candidates(d, "a2") == [other_class]

    # a pending deletion request names the child, the class or the organization
    def request(target: str, state: str = "requested") -> str:
        request_id = str(uuid4())
        with d.sessions().begin() as db:
            db.add(
                DataLifecycleRequestModel(
                    request_id=request_id,
                    organization_id=d.organization,
                    request_type="delete",
                    target_ref=target,
                    state=state,
                    requested_by="synthetic",
                )
            )
        return request_id

    request(good[0])
    assert _candidates(d) == sorted(good[1:])
    completed = request(good[1], "completed")
    assert completed and _candidates(d) == sorted(good[1:])  # a completed request is ignored
    export_id = str(uuid4())
    with d.sessions().begin() as db:
        db.add(
            DataLifecycleRequestModel(
                request_id=export_id,
                organization_id=d.organization,
                request_type="export",
                target_ref=good[1],
                state="requested",
                requested_by="synthetic",
            )
        )
    assert _candidates(d) == sorted(good[1:])  # an export request does not exclude
    request(d.classes["a1"])
    assert _candidates(d) == []
    assert _candidates(d, "a2") == [other_class]  # the class-level request is for a1 only
    request(d.organization)
    assert _candidates(d, "a2") == []


def test_the_candidate_statement_ignores_a_class_that_is_not_active(api: Api) -> None:
    d = api
    add_child(d)
    assert len(_candidates(d)) == 1
    with d.sessions().begin() as db:
        db.execute(
            update(ClassroomModel)
            .where(ClassroomModel.class_id == d.classes["a1"])
            .values(state="suspended")
        )
    try:
        assert _candidates(d) == []
    finally:
        with d.sessions().begin() as db:
            db.execute(
                update(ClassroomModel)
                .where(ClassroomModel.class_id == d.classes["a1"])
                .values(state="active")
            )


def test_a_real_child_is_never_offered_whatever_consent_rows_exist(api: Api) -> None:
    d = api
    add_child(d, origin="REAL")
    add_child(d, origin="REAL")
    occ = make_occurrence(d)
    answer = post_select(d, "t1", occ)
    assert answer.status_code == 201
    body = answer.json()
    assert (
        body["outcome"] == "NO_ELIGIBLE_CHILD"
        and body["state"] == "EMPTY"
        and body["child"] is None
    )
    stored = rows(d, occ.occurrence_id)
    assert [
        (r["kind"], r["state"], r["candidate_count"], r["selected_child_ref"]) for r in stored
    ] == [("EMPTY", "EMPTY", 0, None)]
    assert_no_child_data(answer, d)


def test_gate_off_offers_nobody_even_with_synthetic_children(api: Api) -> None:
    d = api
    add_child(d)
    d.gate_on = False
    occ = make_occurrence(d)
    answer = post_select(d, "t1", occ)
    assert answer.status_code == 201 and answer.json()["outcome"] == "NO_ELIGIBLE_CHILD"
    d.gate_on = True
    assert post_select(d, "t1", occ).json()["outcome"] == "SELECTED"


def test_the_shipped_dependency_follows_the_runtime_settings(
    api_pilot_on: Api,
) -> None:
    d = api_pilot_on
    child = add_child(d)
    occ = make_occurrence(d)
    answer = post_select(d, "t1", occ)
    assert answer.status_code == 201 and child_of(answer.json()) == child
    # the default cap of the settings is two draws
    assert d.app.state.be1_runtime.settings.teacher_sample_max_draws == 2


def test_the_shipped_dependency_offers_nobody_while_the_pilot_flag_is_off(
    api_pilot_off: Api,
) -> None:
    d = api_pilot_off
    add_child(d)
    occ = make_occurrence(d)
    answer = post_select(d, "t1", occ)
    assert answer.status_code == 201
    assert answer.json()["outcome"] == "NO_ELIGIBLE_CHILD" and answer.json()["child"] is None


# ----------------------------------------------------------------------------- the state table
def test_the_draw_is_uniform_over_the_candidates_and_the_index_is_not_stored(api: Api) -> None:
    d = api
    children = sorted(add_child(d) for _ in range(3))
    seen = set()
    for forced in range(3):
        occ = make_occurrence(d)
        d.forced = [forced]
        body = post_select(d, "t1", occ).json()
        seen.add(child_of(body))
        assert child_of(body) == children[forced]
        stored = rows(d, occ.occurrence_id)[0]
        assert "draw_index" not in stored and not any("seed" in key for key in stored)
    assert seen == set(children)


def test_f2_stale_confirm_then_reselect_then_stop(api: Api) -> None:
    """R1 F-2: select, withdraw, confirm 409, reselect, withdraw, confirm 409, STOPPED."""
    d = api
    first_child, second_child = add_child(d), add_child(d)
    occ = make_occurrence(d)
    offer = post_select(d, "t1", occ).json()
    drawn = child_of(offer)
    withdraw(d, drawn)

    # GET sees the stale offer without writing and without the child
    seen = get_sel(d, "t1", occ, offer["selection_id"])
    assert seen.status_code == 200 and seen.json()["state"] == "STALE"
    assert seen.json()["child"] is None and seen.json()["revision"] == 1
    assert state_of(d, occ.occurrence_id) == [("DRAW", "OPEN", 1)]
    # T4B1-IR-01: the stored row is still OPEN revision 1, so a revalidating client gets a 200 with
    # the computed STALE state, never a 304 that would keep the withdrawn child on its screen
    revalidated = get_sel(d, "t1", occ, offer["selection_id"], **{"If-None-Match": '"1"'})
    assert revalidated.status_code == 200 and revalidated.json()["state"] == "STALE"
    assert revalidated.json()["child"] is None

    stale = post_confirm(d, "t1", occ, offer)
    assert stale.status_code == 409 and stale.json()["code"] == "STALE_REVISION"
    assert stale.json()["current_version"] == 2
    assert_no_child_data(stale, d)
    assert state_of(d, occ.occurrence_id) == [("DRAW", "STALE", 2)]  # the write is kept
    # once the STALE write is stored (revision 2) the immutable row may answer 304
    stored = get_sel(d, "t1", occ, offer["selection_id"], **{"If-None-Match": '"2"'})
    assert stored.status_code == 304

    second = post_select(d, "t1", occ)
    assert second.status_code == 201, second.text
    reselected = second.json()
    assert child_of(reselected) == (second_child if drawn == first_child else first_child)
    assert reselected["draw_no"] == 2 and reselected["reselect_available"] is False
    assert state_of(d, occ.occurrence_id) == [("DRAW", "STALE", 2), ("RESELECT", "OPEN", 1)]

    withdraw(d, child_of(reselected))
    stale_again = post_confirm(d, "t1", occ, reselected)
    assert stale_again.status_code == 409 and stale_again.json()["current_version"] == 2
    assert state_of(d, occ.occurrence_id) == [("DRAW", "STALE", 2), ("RESELECT", "STALE", 2)]

    stopped = post_select(d, "t1", occ)
    assert stopped.status_code == 200, stopped.text
    stop = stopped.json()
    assert stop["outcome"] == "NO_ELIGIBLE_CHILD" and stop["state"] == "STOPPED"
    assert (
        stop["selection_id"] is None
        and stop["child"] is None
        and stop["reselect_available"] is False
    )
    assert len(rows(d, occ.occurrence_id)) == 2  # case h writes nothing
    assert_no_child_data(stopped, d)

    # a new eligible child does not reopen the occurrence in v3 (OPEN-3)
    add_child(d)
    again = post_select(d, "t1", occ)
    assert again.status_code == 200 and again.json()["state"] == "STOPPED"
    assert len(rows(d, occ.occurrence_id)) == 2

    # the confirm of the old offer after the stop is refused, never a 500
    assert post_confirm(d, "t1", occ, offer, revision=2).status_code == 409


def test_a_stale_offer_with_an_empty_roster_keeps_the_reselect(api: Api) -> None:
    """Case g: the stale child is gone and nobody else is eligible; the reselect is not spent."""
    d = api
    only = add_child(d)
    occ = make_occurrence(d)
    offer = post_select(d, "t1", occ).json()
    withdraw(d, only)
    empty = post_select(d, "t1", occ)
    assert empty.status_code == 201 and empty.json()["state"] == "EMPTY"
    assert empty.json()["reselect_available"] is True
    assert state_of(d, occ.occurrence_id) == [("DRAW", "STALE", 2), ("EMPTY", "EMPTY", 1)]
    # coalesced: the same empty set again writes nothing
    coalesced = post_select(d, "t1", occ)
    assert coalesced.status_code == 200
    assert coalesced.json()["selection_id"] == empty.json()["selection_id"]
    assert len(rows(d, occ.occurrence_id)) == 2
    # a child appears: the one reselect (draw 2) is available
    add_child(d)
    resumed = post_select(d, "t1", occ)
    assert resumed.status_code == 201 and resumed.json()["draw_no"] == 2
    assert offer["selection_id"] != resumed.json()["selection_id"]


def test_empty_rows_coalesce_and_the_first_draw_follows_a_new_child(api: Api) -> None:
    d = api
    occ = make_occurrence(d)
    first = post_select(d, "t1", occ)
    assert first.status_code == 201 and first.json()["state"] == "EMPTY"
    assert (
        first.json()["outcome"] == "NO_ELIGIBLE_CHILD"
        and first.json()["reselect_available"] is False
    )
    for _ in range(3):
        again = post_select(d, "t1", occ)
        assert again.status_code == 200
        assert again.json()["selection_id"] == first.json()["selection_id"]
    assert len(rows(d, occ.occurrence_id)) == 1
    # reading the empty row works and carries no child
    assert get_sel(d, "t1", occ, first.json()["selection_id"]).json()["state"] == "EMPTY"
    # confirming an empty row is refused
    refused = d.client.post(
        sel_url(occ.occurrence_id, first.json()["selection_id"], "/confirmation"),
        json={"expected_selection_sha256": "a" * 64},
        headers=headers(d.subjects["t1"], uuid4().hex, **{"If-Match": '"1"'}),
    )
    assert refused.status_code == 409 and refused.json()["code"] == "INVALID_STATE_TRANSITION"
    add_child(d)
    drawn = post_select(d, "t1", occ)
    assert drawn.status_code == 201 and drawn.json()["draw_no"] == 1
    assert [r["kind"] for r in rows(d, occ.occurrence_id)] == ["EMPTY", "DRAW"]


def test_one_live_offer_is_returned_again_and_nothing_new_is_written(api: Api) -> None:
    d = api
    add_child(d)
    add_child(d)
    occ = make_occurrence(d)
    first = post_select(d, "t1", occ)
    again = post_select(d, "t1", occ)
    assert (first.status_code, again.status_code) == (201, 200)
    assert again.json() == first.json()
    assert len(rows(d, occ.occurrence_id)) == 1
    with d.sessions()() as db:
        audits = db.scalars(
            select(CoreAuditEntryModel).where(
                CoreAuditEntryModel.resource_id == occ.occurrence_id,
                CoreAuditEntryModel.action.like("lesson.occurrence.child_selection.%"),
            )
        ).all()
    assert len(audits) == 1


def test_expiry_resumes_the_same_child_and_confirm_after_expiry_is_refused(api: Api) -> None:
    d = api
    for _ in range(3):
        add_child(d)
    occ = make_occurrence(d)
    offer = post_select(d, "t1", occ).json()
    drawn = child_of(offer)
    d.clock.advance(901)
    # a read computes EXPIRED and writes nothing
    read = get_sel(d, "t1", occ, offer["selection_id"])
    assert read.json()["state"] == "EXPIRED" and read.json()["child"] is None
    assert state_of(d, occ.occurrence_id) == [("DRAW", "OPEN", 1)]
    # T4B1-IR-01: a client that holds the OPEN body with the child (ETag "1") gets a 200, not a 304
    again = get_sel(d, "t1", occ, offer["selection_id"], **{"If-None-Match": '"1"'})
    assert again.status_code == 200 and again.json()["state"] == "EXPIRED"
    assert again.json()["child"] is None
    # a confirm after the deadline keeps the EXPIRED write and refuses
    late = post_confirm(d, "t1", occ, offer)
    assert late.status_code == 409 and late.json()["code"] == "INVALID_STATE_TRANSITION"
    assert state_of(d, occ.occurrence_id) == [("DRAW", "EXPIRED", 2)]
    resumed = post_select(d, "t1", occ)
    assert resumed.status_code == 201
    body = resumed.json()
    assert child_of(body) == drawn and body["draw_no"] == 1  # the sticky child, not a new draw
    assert [r["kind"] for r in rows(d, occ.occurrence_id)] == ["DRAW", "REOFFER"]
    assert body["selection_id"] != offer["selection_id"]

    # a confirmed offer expires 900 s after the confirmation, then the same child is re-offered
    confirmed = post_confirm(d, "t1", occ, body).json()
    assert confirmed["state"] == "CONFIRMED"
    d.clock.advance(899)
    assert post_select(d, "t1", occ).json()["selection_id"] == body["selection_id"]
    d.clock.advance(2)
    assert get_sel(d, "t1", occ, body["selection_id"]).json()["state"] == "EXPIRED"
    third = post_select(d, "t1", occ)
    assert third.status_code == 201 and child_of(third.json()) == drawn
    assert [(r["kind"], r["state"]) for r in rows(d, occ.occurrence_id)] == [
        ("DRAW", "EXPIRED"),
        ("REOFFER", "EXPIRED"),
        ("REOFFER", "OPEN"),
    ]


def test_a_cancelled_run_reoffers_the_same_child_not_a_new_draw(api: Api) -> None:
    d = api
    for _ in range(3):
        add_child(d)
    occ = make_occurrence(d)
    offer = post_select(d, "t1", occ).json()
    drawn = child_of(offer)
    confirmed = post_confirm(d, "t1", occ, offer).json()
    assert confirmed["state"] == "CONFIRMED"
    run_ref = f"synthetic-run-cancelled-{uuid4().hex}"
    # T-4b2 will consume the offer; here the consumption and a cancelled run are simulated by SQL
    with d.sessions().begin() as db:
        db.execute(
            update(CHILD_SELECTIONS)
            .where(CHILD_SELECTIONS.c.selection_id == offer["selection_id"])
            .values(
                state="CONSUMED",
                revision=3,
                consumed_at=datetime.now(UTC),
                consumed_run_ref=run_ref,
            )
        )
    view = get_sel(d, "t1", occ, offer["selection_id"]).json()
    assert view["state"] == "CONSUMED" and view["child"] is None
    assert view["consumed_run_ref"] == run_ref
    next_offer = post_select(d, "t1", occ)
    assert next_offer.status_code == 201 and child_of(next_offer.json()) == drawn
    assert [r["kind"] for r in rows(d, occ.occurrence_id)] == ["DRAW", "REOFFER"]


def test_plan_reapproval_voids_the_live_offer_and_reoffers_the_same_child(api: Api) -> None:
    d = api
    for _ in range(3):
        add_child(d)
    occ = make_occurrence(d)
    offer = post_select(d, "t1", occ).json()
    drawn = child_of(offer)
    old_plan = occ.plan_revision_id
    reapprove(d, occ)
    assert occ.plan_revision_id != old_plan
    fresh = post_select(d, "t1", occ)
    assert fresh.status_code == 201 and child_of(fresh.json()) == drawn
    assert fresh.json()["plan"]["revision_no"] == 2
    assert [(r["kind"], r["state"], r["plan_revision_id"]) for r in rows(d, occ.occurrence_id)] == [
        ("DRAW", "VOID", old_plan),
        ("REOFFER", "OPEN", occ.plan_revision_id),
    ]
    old = get_sel(d, "t1", occ, offer["selection_id"]).json()
    assert old["state"] == "VOID" and old["child"] is None
    refused = post_confirm(d, "t1", occ, offer, revision=2)
    assert refused.status_code == 409 and refused.json()["code"] == "INVALID_STATE_TRANSITION"
    # confirming the hash of a re-offer of the new plan works
    assert post_confirm(d, "t1", occ, fresh.json()).status_code == 200


def test_confirm_with_a_wrong_hash_or_revision_is_a_stale_409(api: Api) -> None:
    d = api
    add_child(d)
    occ = make_occurrence(d)
    offer = post_select(d, "t1", occ).json()
    wrong_hash = post_confirm(d, "t1", occ, offer, sha="0" * 64)
    assert wrong_hash.status_code == 409 and wrong_hash.json()["code"] == "STALE_REVISION"
    assert wrong_hash.json()["current_version"] == 1
    wrong_revision = post_confirm(d, "t1", occ, offer, revision=7)
    assert wrong_revision.status_code == 409 and wrong_revision.json()["current_version"] == 1
    assert state_of(d, occ.occurrence_id) == [("DRAW", "OPEN", 1)]
    assert post_confirm(d, "t1", occ, offer).status_code == 200


def test_the_cap_of_one_draw_stops_at_the_first_stale_offer(api: Api) -> None:
    d = api
    d.policy = SelectionPolicy(max_draws=1)
    add_child(d)
    add_child(d)
    occ = make_occurrence(d)
    offer = post_select(d, "t1", occ).json()
    assert offer["reselect_available"] is False
    withdraw(d, child_of(offer))
    stopped = post_select(d, "t1", occ)
    assert stopped.status_code == 200 and stopped.json()["state"] == "STOPPED"
    assert state_of(d, occ.occurrence_id) == [("DRAW", "STALE", 2)]


# ----------------------------------------------------------------------------- idempotency
def test_the_same_key_twice_is_one_row_and_a_replay(api: Api) -> None:
    d = api
    add_child(d)
    occ = make_occurrence(d)
    key = uuid4().hex
    first = post_select(d, "t1", occ, key)
    again = post_select(d, "t1", occ, key)
    assert (first.status_code, again.status_code) == (201, 201)
    assert again.json() == first.json()
    assert len(rows(d, occ.occurrence_id)) == 1
    confirm_key = uuid4().hex
    one = post_confirm(d, "t1", occ, first.json(), key=confirm_key)
    two = post_confirm(d, "t1", occ, first.json(), key=confirm_key)
    assert one.status_code == 200 and two.status_code == 200
    assert two.json() == one.json()
    other = post_confirm(
        d,
        "t1",
        occ,
        first.json(),
        revision=2,
        sha=first.json()["selection_sha256"],
        key=confirm_key,
    )
    assert other.status_code == 400 and other.json()["code"] == "INVALID_IDEMPOTENCY_KEY"
    # a confirm of the same revision 2 with a new key is the idempotent success
    same = post_confirm(d, "t1", occ, one.json())
    assert same.status_code == 200 and same.json()["state"] == "CONFIRMED"
    assert len(rows(d, occ.occurrence_id)) == 1


def test_a_null_id_receipt_replays_its_stored_outcome_without_running_the_table(api: Api) -> None:
    """R2 N-4: the stopped answer is replayed, whatever the roster is now."""
    d = api
    first_child = add_child(d)
    occ = make_occurrence(d)
    offer = post_select(d, "t1", occ).json()
    withdraw(d, first_child)
    second_child = add_child(d)
    post_confirm(d, "t1", occ, offer)  # STALE
    reselected = post_select(d, "t1", occ).json()
    assert child_of(reselected) == second_child
    withdraw(d, second_child)
    post_confirm(d, "t1", occ, reselected)  # STALE again
    key = uuid4().hex
    stopped = post_select(d, "t1", occ, key)
    assert stopped.status_code == 200 and stopped.json()["state"] == "STOPPED"
    rows_before = len(rows(d, occ.occurrence_id))
    add_child(d)  # the roster changes between the two calls
    replay = post_select(d, "t1", occ, key)
    assert replay.status_code == 200
    assert replay.json()["state"] == "STOPPED" and replay.json()["selection_id"] is None
    assert len(rows(d, occ.occurrence_id)) == rows_before


# ----------------------------------------------------------------------------- concurrency
def test_eight_concurrent_selections_give_one_live_row_and_one_draw_row(api: Api) -> None:
    d = api
    for _ in range(4):
        add_child(d)
    occ = make_occurrence(d)
    barrier = Barrier(8)

    def call(_: int) -> Any:
        barrier.wait()
        return post_select(d, "t1", occ)

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(call, range(8)))
    statuses = sorted(r.status_code for r in results)
    assert statuses == [200] * 7 + [201], statuses
    assert len({r.json()["selection_id"] for r in results}) == 1
    stored = rows(d, occ.occurrence_id)
    assert len(stored) == 1 and stored[0]["state"] == "OPEN" and stored[0]["kind"] == "DRAW"
    with d.sessions()() as db:
        audits = db.scalar(
            select(func.count())
            .select_from(CoreAuditEntryModel)
            .where(
                CoreAuditEntryModel.resource_id == occ.occurrence_id,
                CoreAuditEntryModel.action.like("lesson.occurrence.child_selection.%"),
            )
        )
    assert audits == 1


def test_two_concurrent_confirms_one_wins_the_other_is_stale_or_a_replay(api: Api) -> None:
    d = api
    add_child(d)
    occ = make_occurrence(d)
    offer = post_select(d, "t1", occ).json()
    barrier = Barrier(2)

    def call(_: int) -> Any:
        barrier.wait()
        return post_confirm(d, "t1", occ, offer)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(call, range(2)))
    assert sorted(r.status_code for r in results) == [200, 409]
    loser = next(r for r in results if r.status_code == 409)
    assert loser.json()["code"] == "STALE_REVISION" and loser.json()["current_version"] == 2
    assert state_of(d, occ.occurrence_id) == [("DRAW", "CONFIRMED", 2)]

    # the same key from two callers: the receipt serializes them, both answers are 200
    other = make_occurrence(d)
    second_offer = post_select(d, "t1", other).json()
    key = uuid4().hex
    barrier = Barrier(2)

    def keyed(_: int) -> Any:
        barrier.wait()
        return post_confirm(d, "t1", other, second_offer, key=key)

    with ThreadPoolExecutor(max_workers=2) as pool:
        pair = list(pool.map(keyed, range(2)))
    assert [r.status_code for r in pair] == [200, 200]
    assert state_of(d, other.occurrence_id) == [("DRAW", "CONFIRMED", 2)]


# ----------------------------------------------------------------------------- the table itself
def _row_values(d: Api, occ: Occurrence, **overrides: Any) -> dict[str, Any]:
    now = datetime.now(UTC)
    values: dict[str, Any] = {
        "selection_id": str(uuid4()),
        "occurrence_id": occ.occurrence_id,
        "plan_revision_id": occ.plan_revision_id,
        "organization_ref": d.organization,
        "class_ref": d.classes[occ.class_key],
        "teacher_ref": d.accounts["t1"],
        "kind": "DRAW",
        "draw_no": 1,
        "policy_version": POLICY_VERSION,
        "eligibility_basis": "SYNTHETIC_DEV",
        "candidate_count": 2,
        "candidate_set_hash": "c" * 64,
        "selected_child_ref": "synthetic-child-x",
        "class_revision": 1,
        "occurrence_revision": 2,
        "state": "OPEN",
        "revision": 1,
        "issued_at": now,
        "expires_at": now + timedelta(minutes=15),
    }
    values.update(overrides)
    return values


def _insert(d: Api, occ: Occurrence, **overrides: Any) -> str:
    values = _row_values(d, occ, **overrides)
    with d.sessions().begin() as db:
        db.execute(insert(CHILD_SELECTIONS).values(**values))
    return str(values["selection_id"])


def _refused(action: Callable[[Session], Any], d: Api, fragment: str) -> None:
    with pytest.raises(DBAPIError) as caught, d.sessions().begin() as db:
        action(db)
    assert fragment in str(caught.value), str(caught.value)[:300]


def test_database_refuses_bad_inserts(api: Api) -> None:
    d = api
    occ = make_occurrence(d)
    other = make_occurrence(d)
    good = _insert(d, occ)
    assert good

    def insert_values(**overrides: Any) -> Callable[[Session], Any]:
        return lambda db: db.execute(
            insert(CHILD_SELECTIONS).values(**_row_values(d, occ, **overrides))
        )

    _refused(insert_values(state="CONFIRMED"), d, "CHILD_SELECTION_INSERT_STATE")
    _refused(insert_values(revision=2), d, "CHILD_SELECTION_INSERT_NOT_FRESH")
    _refused(insert_values(confirmed_at=datetime.now(UTC)), d, "CHILD_SELECTION_INSERT_NOT_FRESH")
    _refused(insert_values(organization_ref="another-org"), d, "CHILD_SELECTION_SCOPE_MISMATCH")
    _refused(insert_values(class_ref="another-class"), d, "CHILD_SELECTION_SCOPE_MISMATCH")
    _refused(insert_values(eligibility_basis="REAL"), d, "ck_sel_basis")
    _refused(insert_values(candidate_set_hash="XYZ"), d, "ck_sel_hash")
    _refused(insert_values(selection_id="sel-1"), d, "ck_sel_id_uuid")
    _refused(insert_values(kind="DRAW", draw_no=2), d, "ck_sel_kind_draw")
    _refused(insert_values(kind="OTHER"), d, "ck_sel_kind")
    _refused(insert_values(candidate_count=0), d, "ck_sel_empty_shape")
    _refused(insert_values(selected_child_ref=None), d, "ck_sel_empty_shape")
    _refused(
        insert_values(expires_at=datetime.now(UTC) - timedelta(days=1)), d, "ck_sel_empty_shape"
    )
    _refused(
        insert_values(
            kind="EMPTY", state="EMPTY", draw_no=None, candidate_count=0, expires_at=None
        ),  # an EMPTY row cannot name a child
        d,
        "ck_sel_empty_shape",
    )
    _refused(
        lambda db: db.execute(
            insert(CHILD_SELECTIONS).values(
                **_row_values(d, other, plan_revision_id=occ.plan_revision_id)
            )
        ),
        d,
        "fk_sel_plan",
    )
    _refused(insert_values(policy_version="Bad Version!"), d, "ck_sel_policy")
    # a second live row, and a second DRAW 1, are refused by the unique indexes
    _refused(insert_values(), d, "uq_sel_live")
    with d.sessions().begin() as db:
        db.execute(
            update(CHILD_SELECTIONS)
            .where(CHILD_SELECTIONS.c.selection_id == good)
            .values(state="EXPIRED", revision=2)
        )
    _refused(insert_values(), d, "uq_sel_draw")
    # a REOFFER of the same draw number is allowed, the empty shape is allowed
    _insert(d, occ, kind="REOFFER", draw_no=1)
    empty = other
    _insert(
        d,
        empty,
        kind="EMPTY",
        state="EMPTY",
        draw_no=None,
        candidate_count=0,
        selected_child_ref=None,
        expires_at=None,
    )


def test_database_refuses_illegal_updates_and_deletes(api: Api) -> None:
    d = api
    occ = make_occurrence(d)
    first = _insert(d, occ)

    def set_values(selection_id: str, **values: Any) -> Callable[[Session], Any]:
        return lambda db: db.execute(
            update(CHILD_SELECTIONS)
            .where(CHILD_SELECTIONS.c.selection_id == selection_id)
            .values(**values)
        )

    for column, value in (
        ("selected_child_ref", "another-child"),
        ("teacher_ref", "account-x"),
        ("candidate_count", 9),
        ("candidate_set_hash", "d" * 64),
        ("plan_revision_id", "p"),
        ("issued_at", datetime.now(UTC)),
        ("expires_at", datetime.now(UTC) + timedelta(days=1)),
        ("kind", "REOFFER"),
        ("draw_no", 2),
    ):
        _refused(set_values(first, **{column: value}, revision=2), d, "CHILD_SELECTION_IMMUTABLE")
    _refused(
        set_values(
            first,
            state="CONFIRMED",
            revision=1,
            confirmed_at=datetime.now(UTC),
            confirmed_by="a",
            confirmation_expires_at=datetime.now(UTC) + timedelta(minutes=1),
        ),
        d,
        "CHILD_SELECTION_REVISION",
    )
    _refused(
        set_values(
            first, state="CONSUMED", revision=2, consumed_at=datetime.now(UTC), consumed_run_ref="r"
        ),
        d,
        "CHILD_SELECTION_STATE_EDGE",
    )
    _refused(set_values(first, state="OPEN", revision=2), d, "CHILD_SELECTION_STATE_EDGE")
    _refused(
        set_values(
            first,
            state="EXPIRED",
            revision=2,
            confirmed_at=datetime.now(UTC),
            confirmed_by="a",
            confirmation_expires_at=datetime.now(UTC) + timedelta(minutes=1),
        ),
        d,
        "CHILD_SELECTION_CONFIRM_COLUMNS",
    )
    _refused(
        set_values(
            first, state="EXPIRED", revision=2, consumed_at=datetime.now(UTC), consumed_run_ref="r"
        ),
        d,
        "CHILD_SELECTION_CONSUME_COLUMNS",
    )
    now = datetime.now(UTC)
    run_ref = f"run-unique-{uuid4().hex}"
    with d.sessions().begin() as db:
        db.execute(
            update(CHILD_SELECTIONS)
            .where(CHILD_SELECTIONS.c.selection_id == first)
            .values(
                state="CONFIRMED",
                revision=2,
                confirmed_at=now,
                confirmed_by="a",
                confirmation_expires_at=now + timedelta(minutes=15),
            )
        )
    _refused(set_values(first, state="OPEN", revision=3), d, "CHILD_SELECTION_STATE_EDGE")
    _refused(set_values(first, state="CONFIRMED", revision=3), d, "CHILD_SELECTION_STATE_EDGE")
    _refused(set_values(first, state="CONSUMED", revision=3), d, "CHILD_SELECTION_CONSUME_COLUMNS")
    _refused(
        set_values(first, state="EXPIRED", revision=3, consumed_at=now, consumed_run_ref="r"),
        d,
        "CHILD_SELECTION_CONSUME_COLUMNS",
    )
    with d.sessions().begin() as db:
        db.execute(
            update(CHILD_SELECTIONS)
            .where(CHILD_SELECTIONS.c.selection_id == first)
            .values(state="CONSUMED", revision=3, consumed_at=now, consumed_run_ref=run_ref)
        )
    # nothing leaves CONSUMED
    _refused(set_values(first, state="EXPIRED", revision=4), d, "CHILD_SELECTION_STATE_EDGE")
    # a consumed run ref is unique across rows
    second = make_occurrence(d)
    other = _insert(d, second)
    with d.sessions().begin() as db:
        db.execute(
            update(CHILD_SELECTIONS)
            .where(CHILD_SELECTIONS.c.selection_id == other)
            .values(
                state="CONFIRMED",
                revision=2,
                confirmed_at=now,
                confirmed_by="a",
                confirmation_expires_at=now + timedelta(minutes=15),
            )
        )
    _refused(
        set_values(other, state="CONSUMED", revision=3, consumed_at=now, consumed_run_ref=run_ref),
        d,
        "uq_sel_consumed_run",
    )
    # delete is refused without the purge flag, whatever the state
    _refused(
        lambda db: db.execute(
            CHILD_SELECTIONS.delete().where(CHILD_SELECTIONS.c.selection_id == first)
        ),
        d,
        "CHILD_SELECTION_DELETE_FORBIDDEN",
    )
    _refused(
        lambda db: db.execute(
            CHILD_SELECTIONS.delete().where(CHILD_SELECTIONS.c.occurrence_id == occ.occurrence_id)
        ),
        d,
        "CHILD_SELECTION_DELETE_FORBIDDEN",
    )
    # the occurrence and the plan that a row references cannot be deleted either
    _refused(
        lambda db: db.execute(
            text("delete from lesson.occurrences where occurrence_id = :o"),
            {"o": occ.occurrence_id},
        ),
        d,
        "OCCURRENCE_DELETE_FORBIDDEN",
    )
    assert len(rows(d, occ.occurrence_id)) == 1


def test_the_purge_function_removes_exactly_one_childs_rows_of_one_organization(api: Api) -> None:
    d = api
    occ = make_occurrence(d)
    other_org_occ = make_occurrence(d, who="tother", class_key="b1")
    child, bystander = "synthetic-purge-child", "synthetic-purge-bystander"
    now = datetime.now(UTC)
    first = _insert(d, occ, selected_child_ref=child)
    with d.sessions().begin() as db:
        db.execute(
            update(CHILD_SELECTIONS)
            .where(CHILD_SELECTIONS.c.selection_id == first)
            .values(state="EXPIRED", revision=2)
        )
    _insert(d, occ, kind="REOFFER", draw_no=1, selected_child_ref=child)
    survivors = [
        _insert(
            d,
            other_org_occ,
            selected_child_ref=child,  # the same ref in another organization
            organization_ref=d.other_organization,
            class_ref=d.classes["b1"],
            teacher_ref=d.accounts["tother"],
        ),
    ]
    occ_two = make_occurrence(d)
    survivors.append(_insert(d, occ_two, selected_child_ref=bystander))
    occ_three = make_occurrence(d)
    survivors.append(
        _insert(
            d,
            occ_three,
            kind="EMPTY",
            state="EMPTY",
            draw_no=None,
            candidate_count=0,
            selected_child_ref=None,
            expires_at=None,
        )
    )
    assert now

    # a plain delete is refused; the purge deletes only the child's rows in that organization
    _refused(
        lambda db: db.execute(
            CHILD_SELECTIONS.delete().where(CHILD_SELECTIONS.c.selected_child_ref == child)
        ),
        d,
        "CHILD_SELECTION_DELETE_FORBIDDEN",
    )
    with d.sessions().begin() as db:
        removed = purge_child_selections(db, d.organization, child)
        assert removed == 2
        # the flag is switched off again: a later delete in the same transaction is refused
        with pytest.raises(DBAPIError), db.begin_nested():
            db.execute(
                CHILD_SELECTIONS.delete().where(CHILD_SELECTIONS.c.selection_id == survivors[1])
            )
    assert rows(d, occ.occurrence_id) == []
    with d.sessions()() as db:
        left = {
            str(sid)
            for sid in db.execute(
                select(CHILD_SELECTIONS.c.selection_id).where(
                    CHILD_SELECTIONS.c.selection_id.in_(survivors)
                )
            ).scalars()
        }
    assert left == set(survivors)
    with d.sessions().begin() as db:
        assert purge_child_selections(db, d.organization, child) == 0
        assert purge_child_selections(db, d.other_organization, child) == 1
    # the draw budget of the occurrence resets with its purged rows (accepted: the child is gone)
    add_child(d)
    assert post_select(d, "t1", occ).status_code == 201


def test_the_downgrade_guard_refuses_while_a_row_exists(api: Api) -> None:
    d = api
    occ = make_occurrence(d)
    _insert(d, occ)
    spec = importlib.util.spec_from_file_location("sel_0001_pg", MIGRATION)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with pytest.raises(DBAPIError) as caught, d.sessions().begin() as db:
        db.execute(text(module.DOWNGRADE_GUARD))
    assert "child selection rows exist" in str(caught.value)
