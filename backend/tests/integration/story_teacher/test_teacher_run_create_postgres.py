"""FEAT-066 T-4b2: ``POST /v1/story-runs`` for a Teacher on PostgreSQL (DDL-B2).

SRS l.1445-1449 (UC-05: one confirmed child, the approved plan, one activity), l.1663, l.495 and
l.553 (the Teacher lock; creator provenance only), l.351, l.552 and OD-14 (one sample per
occurrence), l.866 and l.1697-1699 (codes, keys, replay), BR-34 (no child name in a stored value).
Runs only against a disposable database whose name contains ``be1_acceptance`` and ``frc08``.
Principals are injected through the ``X-Test-Principal`` header; every identity, class, child, plan
and run is synthetic. The selection flow of T-4b1 is used as it ships (select, confirm), so the
create is proved on a real confirmed selection.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from threading import Barrier
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi import Depends, FastAPI, Header
from fastapi.testclient import TestClient
from sqlalchemy import insert, select, text, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.domain.lesson_occurrences.safety_checklist import (
    ChecklistDefinition,
    ChecklistItem,
    ChecklistRegistry,
)
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.lesson_occurrences.child_selection import (
    ChildSelectionService,
    SyntheticGate,
)
from sketch2life.infrastructure.lesson_occurrences.tables import (
    CHILD_SELECTIONS,
    OCCURRENCES,
    PLAN_ACTIVITIES,
)
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    ClassroomModel,
    EnrollmentModel,
    ManagedProfileModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.infrastructure.persistence.parent_models import (
    ParentChildProfileModel,
    ParentProfileRevisionModel,
)
from sketch2life.infrastructure.story_run_lite import tables as story_tables
from sketch2life.infrastructure.story_teacher.repository import TeacherStoryRunCreator
from sketch2life.infrastructure.story_video.closeout_store import SqlStoryRunCloseoutStore
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.routers.lesson_occurrences import (
    get_checklist_registry,
    get_child_selection_service,
)
from sketch2life.interfaces.http.routers.story_run_create_dispatch import (
    get_teacher_story_run_creator,
)

ISSUER = "synthetic-t4b2-issuer"
NAME_PREFIX = "Synthetic Kid"
RUNS = story_tables.story_runs
TEST_DEFINITION = ChecklistDefinition("test-v1", (ChecklistItem("synthetic_a", "Synthetic A"),))
CHECKED = [{"item_id": "synthetic_a", "checked": True}]
LOCK_FREE = ("COMPLETED", "FAILED", "ABANDONED", "DELETE_PENDING", "DELETED")
TEACHER_VIEW_KEYS = {
    "run_id",
    "run_revision",
    "run_state",
    "profile_ref",
    "profile_revision_ref",
    "occurrence_id",
    "plan",
    "activity",
    "context_revision",
    "context_confirmed",
    "context_snapshot",
    "context_snapshot_sha256",
    "lesson_pin_snapshot",
    "current_input_revision",
    "understanding_revision",
    "subject_label",
    "candidate",
    "story_revision_id",
    "story_revision_no",
    "story_status",
    "story_sha256",
    "story",
    "job_state",
    "retryable",
    "error_code",
    "created_at",
    "updated_at",
    "video",
    "quota",
    "timeline",
    "story_confirmation_required",
}


class Clock:
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
    classes: dict[str, str] = field(default_factory=dict)
    subjects: dict[str, str] = field(default_factory=dict)
    accounts: dict[str, str] = field(default_factory=dict)
    children: dict[str, str] = field(default_factory=dict)
    counter: int = 0

    def sessions(self) -> Any:
        return self.app.state.be1_runtime.session_factory


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


@pytest.fixture
def api(monkeypatch: pytest.MonkeyPatch) -> Iterator[Api]:
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
    monkeypatch.setenv("SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED", "true")
    monkeypatch.delenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", raising=False)
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    app = create_app()
    runtime = app.state.be1_runtime
    if runtime.engine is None or runtime.session_factory is None:
        pytest.fail("PostgreSQL runtime did not initialize")
    token = uuid4().hex[:8]
    organization, other = f"synthetic-t4b2-org-{token}", f"synthetic-t4b2-other-{token}"
    d = Api(app, TestClient(app), token, organization, other)

    def label(value: str) -> str:
        return f"synthetic-t4b2-{value}-{token}"

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

    def selection_service(db: Session = Depends(get_db)) -> ChildSelectionService:  # noqa: B008
        return ChildSelectionService(db, gate=SyntheticGate(d.gate_on), clock=d.clock)

    def creator(db: Session = Depends(get_db)) -> TeacherStoryRunCreator:  # noqa: B008
        return TeacherStoryRunCreator(db, gate=SyntheticGate(d.gate_on), clock=d.clock)

    app.dependency_overrides[get_verified_adult] = verified
    app.dependency_overrides[get_child_selection_service] = selection_service
    app.dependency_overrides[get_teacher_story_run_creator] = creator
    app.dependency_overrides[get_checklist_registry] = lambda: ChecklistRegistry((TEST_DEFINITION,))
    try:
        with d.client:
            yield d
    finally:
        app.dependency_overrides.clear()
        runtime.engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


# ----------------------------------------------------------------------------- helpers
def headers(subject: str, key: str | None = None, **extra: str) -> dict[str, str]:
    result = {"X-Test-Principal": subject}
    if key is not None:
        result["Idempotency-Key"] = key
    result.update(extra)
    return result


@dataclass
class Occ:
    occurrence_id: str
    plan_revision_id: str
    plan_hash: str
    revision_no: int
    activity_id: str
    class_key: str = "a1"
    who: str = "t1"


def _approve_plan(d: Api, occurrence_id: str, head: int, who: str) -> tuple[str, str, int, str]:
    created = d.client.post(
        f"/v1/lesson-occurrences/{occurrence_id}/plan-revisions",
        json={
            "expected_head_revision_no": head,
            "objectives": ["Nhận biết hình tròn", "Kể chuyện chú mèo"],
            "teacher_direction": "Câu chuyện về chú mèo đi tìm bạn",
            "activities": [
                {"kind": "CUSTOM", "title": "Vẽ bằng ngón tay", "description": "Cho trẻ vẽ"}
            ],
        },
        headers=headers(d.subjects[who], uuid4().hex),
    )
    assert created.status_code == 201, created.text
    plan = created.json()
    confirmed = d.client.post(
        f"/v1/lesson-occurrences/{occurrence_id}/plan-revisions/{plan['revision_no']}/confirm",
        json={
            "expected_plan_hash": plan["content_hash"],
            "checklist": [{"activity_order": 1, "checklist_version": "test-v1", "items": CHECKED}],
        },
        headers=headers(d.subjects[who], uuid4().hex),
    )
    assert confirmed.status_code == 200, confirmed.text
    with d.sessions()() as db:
        pointer = str(
            db.execute(
                select(OCCURRENCES.c.approved_plan_revision_id).where(
                    OCCURRENCES.c.occurrence_id == occurrence_id
                )
            ).scalar_one()
        )
        activity = str(
            db.execute(
                select(PLAN_ACTIVITIES.c.plan_activity_id).where(
                    PLAN_ACTIVITIES.c.plan_revision_id == pointer
                )
            ).scalar_one()
        )
    # V4-A OPEN-B: the create and the confirm responses carry the id the run create accepts
    assert [a["plan_activity_id"] for a in plan["activities"]] == [activity]
    assert [a["plan_activity_id"] for a in confirmed.json()["activities"]] == [activity]
    return pointer, str(plan["content_hash"]), int(plan["revision_no"]), activity


def make_occurrence(d: Api, *, who: str = "t1", class_key: str = "a1", approve: bool = True) -> Occ:
    created = d.client.post(
        "/v1/lesson-occurrences",
        json={"class_id": d.classes[class_key], "title": "Bài học vẽ"},
        headers=headers(d.subjects[who], uuid4().hex),
    )
    assert created.status_code == 201, created.text
    occurrence_id = str(created.json()["occurrence_id"])
    if not approve:
        return Occ(occurrence_id, "", "", 0, "", class_key, who)
    plan_id, plan_hash, number, activity = _approve_plan(d, occurrence_id, 0, who)
    return Occ(occurrence_id, plan_id, plan_hash, number, activity, class_key, who)


def reapprove(d: Api, occ: Occ) -> None:
    occ.plan_revision_id, occ.plan_hash, occ.revision_no, occ.activity_id = _approve_plan(
        d, occ.occurrence_id, occ.revision_no, occ.who
    )


def add_child(
    d: Api, class_key: str = "a1", *, age: int = 60, origin: str = "SYNTHETIC_DEV"
) -> str:
    d.counter += 1
    child_id = f"synthetic-child-{d.token}-{d.counter}"
    name = f"{NAME_PREFIX} {d.token} {d.counter}"
    d.children[child_id] = name
    org = d.other_organization if class_key == "b1" else d.organization
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
                consent_id=None,
                consent_purpose_ref=None,
                data_origin=origin,
                state="active",
                created_by="synthetic",
            )
        )
        db.flush()
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


@dataclass
class Offer:
    selection_id: str
    sha: str
    child_id: str
    revision: int


def confirmed_offer(d: Api, occ: Occ) -> Offer:
    """Select and confirm through the T-4b1 routes (one candidate per class keeps it exact)."""
    base = f"/v1/lesson-occurrences/{occ.occurrence_id}/child-selections"
    chosen = d.client.post(base, json={}, headers=headers(d.subjects[occ.who], uuid4().hex))
    assert chosen.status_code in {200, 201}, chosen.text
    offer = chosen.json()
    assert offer["outcome"] == "SELECTED", offer
    confirmed = d.client.post(
        f"{base}/{offer['selection_id']}/confirmation",
        json={"expected_selection_sha256": offer["selection_sha256"]},
        headers=headers(d.subjects[occ.who], uuid4().hex, **{"If-Match": f'"{offer["revision"]}"'}),
    )
    assert confirmed.status_code == 200, confirmed.text
    body = confirmed.json()
    return Offer(
        body["selection_id"],
        body["selection_sha256"],
        str(body["child"]["profile_id"]),
        int(body["revision"]),
    )


def body_for(occ: Occ, offer: Offer, **override: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "profile_ref": {"kind": "MANAGED_PROFILE", "id": offer.child_id},
        "occurrence_id": occ.occurrence_id,
        "plan": {"revision_no": occ.revision_no, "plan_hash": occ.plan_hash},
        "activity_id": occ.activity_id,
        "selection_id": offer.selection_id,
        "selection_sha256": offer.sha,
    }
    body.update(override)
    return body


def post_create(
    d: Api, who: str, body: dict[str, Any], key: str | None = None, **extra: str
) -> Any:
    return d.client.post(
        "/v1/story-runs", json=body, headers=headers(d.subjects[who], key or uuid4().hex, **extra)
    )


def flow(d: Api, *, who: str = "t1", class_key: str = "a1") -> tuple[Occ, Offer, dict[str, Any]]:
    """A fresh occurrence with an approved plan, one candidate child and a confirmed selection."""
    add_child(d, class_key)
    occ = make_occurrence(d, who=who, class_key=class_key)
    offer = confirmed_offer(d, occ)
    return occ, offer, body_for(occ, offer)


def run_rows(d: Api, occurrence_id: str | None = None) -> list[dict[str, Any]]:
    with d.sessions()() as db:
        statement = select(RUNS).order_by(RUNS.c.created_at)
        if occurrence_id is not None:
            statement = statement.where(RUNS.c.occurrence_ref == occurrence_id)
        else:
            statement = statement.where(RUNS.c.occurrence_ref.is_not(None))
        return [dict(row) for row in db.execute(statement).mappings().all()]


def selection_row(d: Api, selection_id: str) -> dict[str, Any]:
    with d.sessions()() as db:
        return dict(
            db.execute(
                select(CHILD_SELECTIONS).where(CHILD_SELECTIONS.c.selection_id == selection_id)
            )
            .mappings()
            .one()
        )


def occurrence_row(d: Api, occurrence_id: str) -> dict[str, Any]:
    with d.sessions()() as db:
        return dict(
            db.execute(select(OCCURRENCES).where(OCCURRENCES.c.occurrence_id == occurrence_id))
            .mappings()
            .one()
        )


def counts(d: Api, *schemas: str) -> dict[str, int]:
    with d.sessions()() as db:
        names = db.execute(
            text(
                "select table_schema || '.' || table_name from information_schema.tables "
                "where table_schema in ('story', 'ai_jobs') or table_name ilike '%quota%' "
                "or table_name ilike '%usage%' or table_name ilike '%capacity%' "
                "or table_name = 'core_outbox_events' order by 1"
            )
        ).scalars()
        result = {}
        for name in list(names):
            result[name] = int(db.execute(text(f"select count(*) from {name}")).scalar_one())  # noqa: S608
    return result


def sql(d: Api, statement: str, **params: Any) -> None:
    with d.sessions().begin() as db:
        db.execute(text(statement), params)


def set_state(d: Api, run_id: str, state: str, **extra: Any) -> None:
    with d.sessions().begin() as db:
        db.execute(update(RUNS).where(RUNS.c.run_id == run_id).values(run_state=state, **extra))


def assert_body_has_no_child_data(text_body: str, d: Api) -> None:
    assert "display_name" not in text_body
    assert NAME_PREFIX not in text_body
    assert not any(name in text_body for name in d.children.values())


# ----------------------------------------------------------------------------- the happy path
def test_a_teacher_creates_the_run_of_the_confirmed_selection(api: Api) -> None:
    d = api
    occ, offer, body = flow(d)
    before = counts(d)
    occurrence_before = occurrence_row(d, occ.occurrence_id)

    response = post_create(d, "t1", body)
    assert response.status_code == 201, response.text
    view = response.json()["story_run"]
    run_id = view["run_id"]
    assert set(view) == TEACHER_VIEW_KEYS
    assert response.headers["Location"] == f"/v1/story-runs/{run_id}"
    assert "ETag" not in response.headers
    assert view["profile_ref"] == {"kind": "MANAGED_PROFILE", "id": offer.child_id}
    assert view["run_state"] == "INPUT_PROCESSING" and view["run_revision"] == 1
    assert view["occurrence_id"] == occ.occurrence_id
    assert view["plan"] == {"revision_no": occ.revision_no, "plan_hash": occ.plan_hash}
    assert view["activity"]["plan_activity_id"] == occ.activity_id
    assert view["activity"]["kind"] == "CUSTOM"
    assert view["context_revision"] == 1 and view["context_confirmed"] is False
    assert view["profile_revision_ref"] == offer.selection_id
    UUID(view["profile_revision_ref"])  # a canonical selection id: no 500 on any Teacher read
    assert view["context_snapshot"]["schema_version"] == "sketch2life.teacher-context.v1"
    assert view["context_snapshot"]["age_months"] == 60
    assert view["lesson_pin_snapshot"]["schema_version"] == "sketch2life.teacher-run-pin.v1"
    assert_body_has_no_child_data(response.text, d)
    assert offer.child_id in response.text  # the opaque ref, once, as the profile ref

    rows = run_rows(d, occ.occurrence_id)
    assert len(rows) == 1
    row = rows[0]
    assert row["run_id"] == run_id
    assert row["actor_scope_kind"] == "ORGANIZATION" and row["actor_scope_ref"] == d.organization
    assert row["profile_ref"] == offer.child_id and row["child_age_months"] == 60
    assert row["active_owner_teacher_id"] == d.accounts["t1"]
    assert row["created_by_actor_ref"] == d.accounts["t1"]
    assert row["occurrence_ref"] == occ.occurrence_id
    assert row["active_owner_parent_account_id"] is None
    assert row["run_state"] == "INPUT_PROCESSING" and row["current_input_revision"] == 1

    with d.sessions()() as db:
        inputs = (
            db.execute(
                select(story_tables.run_inputs).where(story_tables.run_inputs.c.run_id == run_id)
            )
            .mappings()
            .all()
        )
        receipts = (
            db.execute(
                select(story_tables.story_command_receipts).where(
                    story_tables.story_command_receipts.c.resource_ref == run_id
                )
            )
            .mappings()
            .all()
        )
        audits = db.execute(
            select(
                CoreAuditEntryModel.action,
                CoreAuditEntryModel.decision,
                CoreAuditEntryModel.actor_ref,
            ).where(CoreAuditEntryModel.resource_id == run_id)
        ).all()
    assert len(inputs) == 1
    stored = inputs[0]
    assert (
        stored["input_revision"] == 1
        and stored["source_profile_revision_ref"] == offer.selection_id
    )
    snapshot_text = json.dumps(dict(stored["context_snapshot"])) + json.dumps(
        dict(stored["lesson_pin_snapshot"])
    )
    assert not any(name in snapshot_text for name in d.children.values())
    assert offer.child_id not in snapshot_text
    pin = stored["lesson_pin_snapshot"]
    assert pin["occurrence_id"] == occ.occurrence_id and pin["plan_hash"] == occ.plan_hash
    assert pin["plan_revision_id"] == occ.plan_revision_id
    assert pin["activity"]["plan_activity_id"] == occ.activity_id
    assert (
        hashlib.sha256(
            json.dumps(
                dict(pin), ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode()
        ).hexdigest()
        == stored["lesson_pin_snapshot_sha256"]
    )
    assert len(receipts) == 1
    assert receipts[0]["actor_scope_kind"] == "ORGANIZATION"  # the command scope of T-4a1
    assert receipts[0]["actor_scope_ref"] != d.accounts["t1"]  # a digest, never the account id
    assert audits == [("story.run.create", offer.selection_id, d.accounts["t1"])]

    consumed = selection_row(d, offer.selection_id)
    assert consumed["state"] == "CONSUMED" and consumed["consumed_run_ref"] == run_id
    # nothing else moved: no job, outbox, quota or capacity row, no claim, no occurrence change
    after = counts(d)
    moved = {name for name in after if after[name] != before[name]}
    assert moved == {"story.runs", "story.run_inputs", "story.command_receipts"}
    occurrence_after = occurrence_row(d, occ.occurrence_id)
    assert occurrence_after == occurrence_before
    assert occurrence_after["sample_slot_state"] == "AVAILABLE"


def test_the_teacher_can_read_confirm_and_resume_the_run_with_a_synthetic_child_id(
    api: Api,
) -> None:
    """DEC-7 is retired: a ``synthetic-<hex>`` child id is not a UUID and every read works."""
    d = api
    occ, offer, body = flow(d)
    run_id = post_create(d, "t1", body).json()["story_run"]["run_id"]
    assert offer.child_id.count("-") != 4  # not a UUID

    read = d.client.get(f"/v1/story-runs/{run_id}", headers=headers(d.subjects["t1"]))
    assert read.status_code == 200, read.text
    assert set(read.json()["story_run"]) == TEACHER_VIEW_KEYS
    assert (
        read.headers["ETag"].startswith('"')
        and read.headers["Cache-Control"] == "private, no-cache"
    )
    cached = d.client.get(
        f"/v1/story-runs/{run_id}",
        headers=headers(d.subjects["t1"], **{"If-None-Match": read.headers["ETag"]}),
    )
    assert cached.status_code == 304

    snapshot = read.json()["story_run"]
    confirmed = d.client.post(
        f"/v1/story-runs/{run_id}/context-confirmation",
        json={
            "expected_context_revision": snapshot["context_revision"],
            "context_snapshot_sha256": snapshot["context_snapshot_sha256"],
            "confirmed": True,
        },
        headers=headers(d.subjects["t1"], uuid4().hex),
    )
    # no commit-then-409 any more (T4A1-I-02): the confirmation answers the Teacher view
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["story_run"]["context_confirmed"] is True
    assert set(confirmed.json()["story_run"]) == TEACHER_VIEW_KEYS
    assert run_rows(d, occ.occurrence_id)[0]["revision"] >= 1

    active = d.client.get("/v1/story-runs/active/current", headers=headers(d.subjects["t1"]))
    assert active.status_code == 200
    assert active.json()["story_run"]["run_id"] == run_id
    assert set(active.json()["story_run"]) == TEACHER_VIEW_KEYS
    for who in ("t2", "t4", "revoked"):
        other = d.client.get("/v1/story-runs/active/current", headers=headers(d.subjects[who]))
        assert other.status_code == 200 and other.json()["story_run"] is None, who
    parent = d.client.get("/v1/story-runs/active/current", headers=headers(d.subjects["parent"]))
    assert parent.status_code == 200 and parent.json()["story_run"] is None
    assert "profile_ref" not in parent.text
    manager = d.client.get("/v1/story-runs/active/current", headers=headers(d.subjects["manager"]))
    assert manager.status_code == 404


def test_a_fixture_run_without_an_occurrence_pin_reads_through_the_child_class(api: Api) -> None:
    """A row of T-4a1 or T-13a (no occurrence, Parent snapshots, interim storage) still reads."""
    d = api
    child = add_child(d)
    run_id, now = str(uuid4()), datetime.now(UTC)
    context = {
        "schema_version": "sketch2life.parent-context.v1",
        "profile_revision_ref": str(uuid4()),
        "age_months": 60,
        "interests_summary": "",
        "topic": "",
        "adult_confirmed_idea": "",
    }
    with d.sessions().begin() as db:
        db.execute(
            insert(RUNS).values(
                run_id=run_id,
                actor_scope_kind="ORGANIZATION",
                actor_scope_ref=d.organization,
                profile_ref=child,
                child_age_months=60,
                run_state="INPUT_PROCESSING",
                revision=1,
                version=1,
                retryable=False,
                current_input_revision=1,
                created_at=now,
                updated_at=now,
            )
        )
        db.execute(
            insert(story_tables.run_inputs).values(
                run_input_id=str(uuid4()),
                run_id=run_id,
                input_revision=1,
                source_profile_revision_ref=context["profile_revision_ref"],
                context_revision=1,
                context_snapshot=context,
                context_snapshot_sha256=hashlib.sha256(
                    json.dumps(context, sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest(),
                created_at=now,
            )
        )
    read = d.client.get(f"/v1/story-runs/{run_id}", headers=headers(d.subjects["t1"]))
    assert read.status_code == 200, read.text
    story = read.json()["story_run"]
    assert story["profile_ref"]["id"] == child and story["occurrence_id"] is None
    assert story["plan"] is None and story["context_snapshot"]["schema_version"].startswith(
        "sketch2life.parent-"
    )
    # the child's class rule: a Teacher of another class does not see it
    assert (
        d.client.get(f"/v1/story-runs/{run_id}", headers=headers(d.subjects["t2"])).status_code
        == 404
    )


# ----------------------------------------------------------------------------- replay and keys
def test_a_replay_returns_the_same_run_and_another_body_is_400(api: Api) -> None:
    d = api
    occ, offer, body = flow(d)
    first = post_create(d, "t1", body, key="replay-key-1")
    again = post_create(d, "t1", body, key="replay-key-1")
    assert first.status_code == again.status_code == 201
    assert first.json()["story_run"]["run_id"] == again.json()["story_run"]["run_id"]
    assert len(run_rows(d, occ.occurrence_id)) == 1
    assert selection_row(d, offer.selection_id)["revision"] == offer.revision + 1  # consumed once
    other = post_create(d, "t1", {**body, "activity_id": "other-activity"}, key="replay-key-1")
    assert other.status_code == 400 and other.json()["code"] == "INVALID_IDEMPOTENCY_KEY"
    assert len(run_rows(d, occ.occurrence_id)) == 1


def test_two_teachers_with_one_key_never_collide(api: Api) -> None:
    d = api
    occ1, offer1, body1 = flow(d, who="t1", class_key="a1")
    occ2, offer2, body2 = flow(d, who="t2", class_key="a2")
    first = post_create(d, "t1", body1, key="shared-key")
    second = post_create(d, "t2", body2, key="shared-key")
    assert first.status_code == second.status_code == 201
    assert first.json()["story_run"]["run_id"] != second.json()["story_run"]["run_id"]
    owners = {row["active_owner_teacher_id"] for row in run_rows(d)}
    assert {d.accounts["t1"], d.accounts["t2"]} <= owners  # each Teacher holds one run


def test_a_missing_or_malformed_key_is_the_plain_400(api: Api) -> None:
    d = api
    occ, offer, body = flow(d)
    for key in ("", "bad key", "k" * 129):
        response = d.client.post(
            "/v1/story-runs",
            json=body,
            headers={
                "X-Test-Principal": d.subjects["t1"],
                **({"Idempotency-Key": key} if key else {}),
            },
        )
        assert response.status_code == 400 and response.json()["code"] == "INVALID_REQUEST", key
    assert run_rows(d, occ.occurrence_id) == []
    assert selection_row(d, offer.selection_id)["state"] == "CONFIRMED"


# ----------------------------------------------------------------------------- who may create
def test_the_uniform_404_and_the_403s_and_nothing_is_written(api: Api) -> None:
    d = api
    occ, offer, body = flow(d)
    before = counts(d)
    # a Teacher without cover of the class: 404, the same bytes whoever it is
    not_covering = {}
    for who in ("t2", "tother", "revoked"):
        response = post_create(d, who, body, key="same-key")
        assert response.status_code == 404, who
        not_covering[who] = response.json()
    assert (
        len(
            {
                json.dumps({k: v for k, v in b.items() if k != "correlation_id"})
                for b in not_covering.values()
            }
        )
        == 1
    )
    # covered, but not the responsible Teacher with an exact-class teacher row: 403
    for who in ("t4", "g1", "o1", "orgt"):
        response = post_create(d, who, body)
        assert response.status_code == 403, who
        assert response.json()["code"] == "ACTION_NOT_ALLOWED"
    # everyone who is not an active Teacher meets the Parent handler: today's 400 for the keys it
    # does not know (a Teacher-shaped body is not a Parent body), never a Teacher answer
    for who in ("parent", "manager", "platform", "stranger", "inactive"):
        response = post_create(d, who, body)
        assert response.status_code == 400, who
        assert response.json()["code"] == "INVALID_REQUEST"
        assert response.json()["field_errors"], who
    assert counts(d) == before
    assert run_rows(d, occ.occurrence_id) == []
    assert selection_row(d, offer.selection_id)["state"] == "CONFIRMED"


def test_a_revoked_assignment_is_404_at_the_next_call(api: Api) -> None:
    d = api
    subject = f"synthetic-t4b2-late-{d.token}"
    with d.sessions().begin() as db:
        d.subjects["late"] = subject
        d.accounts["late"] = _identity(db, subject, "teacher")
        _assign(db, d.organization, subject, "teacher", d.classes["a2"])
    add_child(d, "a2")
    occ = make_occurrence(d, who="late", class_key="a2")
    offer = confirmed_offer(d, occ)
    body = body_for(occ, offer)
    with d.sessions().begin() as db:
        db.execute(
            update(OrganizationAssignmentModel)
            .where(OrganizationAssignmentModel.subject == subject)
            .values(active=False)
        )
    response = post_create(d, "late", body)
    assert response.status_code == 404
    assert run_rows(d, occ.occurrence_id) == []
    assert selection_row(d, offer.selection_id)["state"] == "CONFIRMED"


def test_a_suspended_class_refuses_the_create_and_writes_nothing(api: Api) -> None:
    d = api
    occ, offer, body = flow(d, who="t2", class_key="a2")
    with d.sessions().begin() as db:
        db.execute(
            update(ClassroomModel)
            .where(ClassroomModel.class_id == d.classes["a2"])
            .values(state="suspended")
        )
    try:
        response = post_create(d, "t2", body)
        assert response.status_code == 409 and response.json()["code"] == "INVALID_STATE_TRANSITION"
    finally:
        with d.sessions().begin() as db:
            db.execute(
                update(ClassroomModel)
                .where(ClassroomModel.class_id == d.classes["a2"])
                .values(state="active")
            )
    assert run_rows(d, occ.occurrence_id) == []
    assert selection_row(d, offer.selection_id)["state"] == "CONFIRMED"


# ----------------------------------------------------------------------------- the plan and slot
def test_no_approved_plan_is_422(api: Api) -> None:
    d = api
    add_child(d)
    occ = make_occurrence(d, approve=False)
    body = {
        "profile_ref": {"kind": "MANAGED_PROFILE", "id": "synthetic-x"},
        "occurrence_id": occ.occurrence_id,
        "plan": {"revision_no": 1, "plan_hash": "a" * 64},
        "activity_id": str(uuid4()),
        "selection_id": str(uuid4()),
        "selection_sha256": "b" * 64,
    }
    response = post_create(d, "t1", body)
    assert response.status_code == 422 and response.json()["code"] == "LESSON_PLAN_NOT_APPROVED"
    assert response.json()["message"] == "Kế hoạch bài học chưa được duyệt."


def test_the_requested_plan_must_be_the_current_approved_plan(api: Api) -> None:
    d = api
    occ, offer, body = flow(d)
    wrong_hash = post_create(d, "t1", {**body, "plan": {**body["plan"], "plan_hash": "c" * 64}})
    assert wrong_hash.status_code == 409 and wrong_hash.json()["code"] == "STALE_REVISION"
    assert wrong_hash.json()["current_version"] == occ.revision_no
    wrong_revision = post_create(d, "t1", {**body, "plan": {**body["plan"], "revision_no": 9}})
    assert wrong_revision.status_code == 409 and wrong_revision.json()["current_version"] == 1
    assert run_rows(d, occ.occurrence_id) == []


def test_a_selection_made_for_a_superseded_plan_cannot_create_a_run(api: Api) -> None:
    """R1 F-2: the selection of plan 1 stays CONFIRMED after plan 2 is approved."""
    d = api
    occ, offer, body = flow(d)
    stale_body = dict(body)
    reapprove(d, occ)
    assert occ.revision_no == 2
    # the old plan in the body: stale, with the current revision number
    old_plan = post_create(d, "t1", stale_body)
    assert old_plan.status_code == 409 and old_plan.json()["code"] == "STALE_REVISION"
    assert old_plan.json()["current_version"] == 2
    # the new plan in the body but the selection of the old plan: also stale
    fresh_plan = post_create(d, "t1", body_for(occ, offer))
    assert fresh_plan.status_code == 409 and fresh_plan.json()["code"] == "STALE_REVISION"
    assert run_rows(d, occ.occurrence_id) == []
    assert selection_row(d, offer.selection_id)["state"] == "CONFIRMED"


def test_the_selection_hash_the_selection_id_and_the_child_are_bound(api: Api) -> None:
    d = api
    occ, offer, body = flow(d)
    wrong_hash = post_create(d, "t1", {**body, "selection_sha256": "d" * 64})
    assert wrong_hash.status_code == 409 and wrong_hash.json()["code"] == "STALE_REVISION"
    unknown = post_create(d, "t1", {**body, "selection_id": str(uuid4())})
    assert unknown.status_code == 404
    other_child = add_child(d)
    mismatch = post_create(
        d, "t1", {**body, "profile_ref": {"kind": "MANAGED_PROFILE", "id": other_child}}
    )
    assert mismatch.status_code == 400 and mismatch.json()["code"] == "INVALID_REQUEST"
    assert [item["field"] for item in mismatch.json()["field_errors"]] == ["profile_ref.id"]
    assert other_child not in mismatch.text
    # the selection of another occurrence is not this occurrence's
    occ2, offer2, body2 = flow(d, who="t1")
    crossed = post_create(d, "t1", {**body, "selection_id": offer2.selection_id})
    assert crossed.status_code == 404
    assert run_rows(d, occ.occurrence_id) == [] and run_rows(d, occ2.occurrence_id) == []


def test_an_activity_of_another_plan_is_400(api: Api) -> None:
    d = api
    occ, offer, body = flow(d)
    other_occ = make_occurrence(d)
    for activity_id in (other_occ.activity_id, str(uuid4())):
        response = post_create(d, "t1", {**body, "activity_id": activity_id})
        assert response.status_code == 400, activity_id
        assert [item["field"] for item in response.json()["field_errors"]] == ["activity_id"]
    assert run_rows(d, occ.occurrence_id) == []


def test_the_activity_id_read_from_the_plan_response_creates_the_run(api: Api) -> None:
    """V4-A OPEN-B end to end: the web reads the approved plan revision, picks one activity and
    sends its ``plan_activity_id`` as ``activity_id``; an id that is not one of that revision's
    activities is the existing 400 and creates nothing."""
    d = api
    occ, offer, body = flow(d)
    read = d.client.get(
        f"/v1/lesson-occurrences/{occ.occurrence_id}/plan-revisions/{occ.revision_no}",
        headers=headers(d.subjects["t1"]),
    )
    assert read.status_code == 200, read.text
    (activity,) = read.json()["activities"]
    activity_id = activity["plan_activity_id"]
    assert activity_id == occ.activity_id and activity["kind"] == "CUSTOM"
    assert activity["snapshot_hash"] is None  # a CUSTOM activity has an id and no snapshot hash
    wrong = post_create(d, "t1", body_for(occ, offer, activity_id=str(uuid4())))
    assert wrong.status_code == 400 and wrong.json()["code"] == "INVALID_REQUEST"
    assert run_rows(d, occ.occurrence_id) == []
    created = post_create(d, "t1", body_for(occ, offer, activity_id=activity_id))
    assert created.status_code == 201, created.text
    pin = created.json()["story_run"]["lesson_pin_snapshot"]
    assert pin["activity"]["plan_activity_id"] == activity_id


def test_a_multi_child_body_is_422_and_nothing_is_read(api: Api) -> None:
    d = api
    occ, offer, body = flow(d)
    before = counts(d)
    for variant in (
        {**body, "profile_refs": [body["profile_ref"]]},
        {**body, "profile_ref": [body["profile_ref"]]},
        {**body, "profile_ref": {"kind": "MANAGED_PROFILE", "id": [offer.child_id, "x"]}},
    ):
        response = post_create(d, "t1", variant)
        assert (
            response.status_code == 422 and response.json()["code"] == "MULTI_CHILD_NOT_SUPPORTED"
        )
    assert counts(d) == before
    assert selection_row(d, offer.selection_id)["state"] == "CONFIRMED"


def test_a_claimed_sample_slot_refuses_the_create_and_writes_nothing(api: Api) -> None:
    d = api
    occ, offer, body = flow(d)
    with d.sessions().begin() as db:
        db.execute(
            update(OCCURRENCES)
            .where(OCCURRENCES.c.occurrence_id == occ.occurrence_id)
            .values(
                sample_slot_state="CLAIMED",
                sample_claimed_at=datetime.now(UTC),
                successful_sample_run_ref=str(uuid4()),
            )
        )
    before = counts(d)
    response = post_create(d, "t1", body)
    assert response.status_code == 409 and response.json()["code"] == "SAMPLE_VIDEO_ALREADY_EXISTS"
    assert response.json()["message"] == "Buổi học này đã có video mẫu."
    assert counts(d) == before
    assert selection_row(d, offer.selection_id)["state"] == "CONFIRMED"


def _seed_generation(
    d: Api,
    occurrence_id: str,
    *,
    run_state: str,
    generation_state: str,
    safety: str = "PASSED",
    output: bool = True,
) -> str:
    """A Teacher run row (no lock) of the occurrence with a current video generation (SQL)."""
    run_id, revision_id, generation_id = str(uuid4()), str(uuid4()), str(uuid4())
    now = datetime.now(UTC)
    digest = "a" * 64
    with d.sessions().begin() as db:
        db.execute(
            insert(RUNS).values(
                run_id=run_id,
                actor_scope_kind="ORGANIZATION",
                actor_scope_ref=d.organization,
                profile_ref=f"synthetic-seed-{uuid4().hex[:8]}",
                child_age_months=60,
                run_state="SCRIPT_REVIEW",
                revision=1,
                version=1,
                retryable=False,
                occurrence_ref=occurrence_id,
                created_by_actor_ref=d.accounts["t1"],
                current_input_revision=None,
                created_at=now,
                updated_at=now,
            )
        )
        receipt_id = str(uuid4())
        db.execute(
            text(
                "insert into story.command_receipts (receipt_id, actor_scope_kind, actor_scope_ref,"
                " operation, idempotency_scope_kind, idempotency_scope_ref, idempotency_key_sha256,"
                " request_fingerprint_sha256, state, response_status, response_body, resource_ref,"
                " state_version, created_at, finalized_at) values (:id, 'ORGANIZATION', :scope,"
                " 'CONFIRM_STORY_REVISION', 'STORY_RUN', :run, :key, :key, 'FINAL', 200,"
                " '{}'::jsonb, :run, 1, now(), now())"
            ),
            {"id": receipt_id, "scope": "s" * 64, "run": run_id, "key": uuid4().hex + uuid4().hex},
        )
        db.execute(
            text(
                "insert into story.story_revisions (story_revision_id, run_id, revision_no, status,"
                " source_asset_sha256, understanding_revision, context_revision, story_sha256,"
                " language, title, duration_ms, story_content, schema_version, prompt_version,"
                " model_id, model_revision, request_sha256) values (:rev, :run, 1, 'CONFIRMED', :h,"
                " 1, 1, :h, 'vi', 't', 60000, '{}'::jsonb, 's', 'p', 'm', '1', :h)"
            ),
            {"rev": revision_id, "run": run_id, "h": digest},
        )
        review_id = str(uuid4())
        db.execute(
            text(
                "insert into story.story_revision_reviews (review_id, run_id, story_revision_id,"
                " command_receipt_id, actor_scope_kind, actor_scope_ref, decision,"
                " target_story_sha256) values (:review, :run, :rev, :receipt, 'ORGANIZATION',"
                " :scope, 'CONFIRM', :h)"
            ),
            {
                "review": review_id,
                "run": run_id,
                "rev": revision_id,
                "receipt": receipt_id,
                "scope": "s" * 64,
                "h": digest,
            },
        )
        ready = generation_state == "READY"
        blocked = generation_state == "SAFETY_BLOCKED"
        db.execute(
            text(
                "insert into story.video_generations (video_generation_id, story_run_id,"
                " story_revision_id, story_review_id, generation_no, generation_kind, state,"
                " request_idempotency_key_hash, request_fingerprint_sha256, target_script_hash,"
                " compute_reservation_ref, billing_quota_usage_ref, job_ref, output_asset_ref,"
                " output_asset_version, technical_validation_state, consistency_validation_state,"
                " safety_validation_state, admission_started_at, accepted_at, completed_at,"
                " safe_failure_code) values (:gen, :run, :rev, :review, 1, 'INITIAL', :state, :h,"
                " :h, :h, :reservation, :usage, :job, :output, :version, :tech, :cons, :safety,"
                " now(), now(), :completed, :failure)"
            ),
            {
                "gen": generation_id,
                "run": run_id,
                "rev": revision_id,
                "review": review_id,
                "state": generation_state,
                "h": "b" * 64,
                "reservation": f"reservation-{generation_id}",
                "usage": f"usage-{generation_id}",
                "job": f"job-{generation_id}",
                "output": f"synthetic-output-{generation_id}" if output else None,
                "version": 1 if output else None,
                "tech": "PASSED" if ready or blocked else "PENDING",
                "cons": "PASSED" if ready or blocked else "PENDING",
                "safety": "FAILED" if blocked else (safety if ready else "PENDING"),
                "completed": now if ready else None,
                "failure": "SYNTHETIC_FAILURE" if generation_state == "FAILED" else None,
            },
        )
        db.execute(
            update(RUNS)
            .where(RUNS.c.run_id == run_id)
            .values(current_video_generation_id=generation_id, run_state=run_state)
        )
    return run_id


@pytest.mark.parametrize("run_state", ["VIDEO_READY", "COMPLETED"])
def test_an_unprojected_ready_sample_holds_the_slot_even_when_the_run_is_completed(
    api: Api, run_state: str
) -> None:
    """The OD-14 window (R1 F-6): a READY, safety-passed sample refuses a second sample run."""
    d = api
    occ, offer, body = flow(d)
    held = _seed_generation(d, occ.occurrence_id, run_state=run_state, generation_state="READY")
    before = counts(d)
    response = post_create(d, "t1", body)
    assert response.status_code == 409 and response.json()["code"] == "SAMPLE_VIDEO_ALREADY_EXISTS"
    assert counts(d) == before
    assert occurrence_row(d, occ.occurrence_id)["sample_slot_state"] == "AVAILABLE"
    # a cancelled or deleted run releases the hold
    for freed in ("DELETE_PENDING", "DELETED"):
        set_state(d, held, freed)
        created = post_create(d, "t1", body)
        assert created.status_code == 201, (freed, created.text)
        set_state(d, created.json()["story_run"]["run_id"], "FAILED")
        # the selection was consumed by the created run: take a fresh confirmed one
        offer = confirmed_offer(d, occ)
        body = body_for(occ, offer)
        set_state(d, held, run_state)
        assert post_create(d, "t1", body).status_code == 409


@pytest.mark.parametrize(
    "generation",
    [
        {"generation_state": "FAILED", "run_state": "SCRIPT_REVIEW", "output": False},
        # the run state ``SAFETY_BLOCKED`` is a row written before the V4-A exit; a real block now
        # leaves the run at ``SCRIPT_REVIEW`` (owner decision C11)
        {"generation_state": "SAFETY_BLOCKED", "run_state": "SAFETY_BLOCKED", "output": False},
        {"generation_state": "SAFETY_BLOCKED", "run_state": "SCRIPT_REVIEW", "output": False},
    ],
)
def test_a_failed_or_blocked_generation_does_not_hold_the_slot(
    api: Api, generation: dict[str, Any]
) -> None:
    d = api
    occ, offer, body = flow(d)
    _seed_generation(d, occ.occurrence_id, **generation)
    assert post_create(d, "t1", body).status_code == 201


# ----------------------------------------------------------------------------- the selection state
def test_an_unconfirmed_expired_or_used_selection_is_409(api: Api) -> None:
    d = api
    add_child(d)
    occ = make_occurrence(d)
    # an OPEN offer (not confirmed)
    base = f"/v1/lesson-occurrences/{occ.occurrence_id}/child-selections"
    opened = d.client.post(base, json={}, headers=headers(d.subjects["t1"], uuid4().hex)).json()
    body = body_for(
        occ,
        Offer(opened["selection_id"], opened["selection_sha256"], opened["child"]["profile_id"], 1),
    )
    response = post_create(d, "t1", body)
    assert response.status_code == 409 and response.json()["code"] == "INVALID_STATE_TRANSITION"
    assert selection_row(d, opened["selection_id"])["state"] == "OPEN"
    # confirmed, then past its confirmation deadline (the creator's clock)
    confirm = d.client.post(
        f"{base}/{opened['selection_id']}/confirmation",
        json={"expected_selection_sha256": opened["selection_sha256"]},
        headers=headers(d.subjects["t1"], uuid4().hex, **{"If-Match": '"1"'}),
    )
    assert confirm.status_code == 200
    confirmed = Offer(
        opened["selection_id"], opened["selection_sha256"], opened["child"]["profile_id"], 2
    )
    body = body_for(occ, confirmed)
    d.clock.advance(901)
    expired = post_create(d, "t1", body)
    assert expired.status_code == 409 and expired.json()["code"] == "INVALID_STATE_TRANSITION"
    assert run_rows(d, occ.occurrence_id) == []


def test_a_consumed_selection_cannot_create_a_second_run(api: Api) -> None:
    d = api
    occ, offer, body = flow(d)
    first = post_create(d, "t1", body)
    assert first.status_code == 201
    # while the run is active the answer names the active run (a clear 409 for a retry)
    retry = post_create(d, "t1", body)
    assert retry.status_code == 409 and retry.json()["code"] == "ACTIVE_RUN_EXISTS"
    # after the run failed, the CONSUMED selection is still spent
    set_state(d, first.json()["story_run"]["run_id"], "FAILED")
    spent = post_create(d, "t1", body)
    assert spent.status_code == 409 and spent.json()["code"] == "INVALID_STATE_TRANSITION"
    assert len(run_rows(d, occ.occurrence_id)) == 1


def test_a_child_withdrawn_after_the_confirmation_stales_the_selection_and_is_409(api: Api) -> None:
    d = api
    occ, offer, body = flow(d)
    with d.sessions().begin() as db:
        db.execute(
            update(EnrollmentModel)
            .where(EnrollmentModel.child_id == offer.child_id)
            .values(state="withdrawn")
        )
    response = post_create(d, "t1", body)
    assert response.status_code == 409 and response.json()["code"] == "STALE_REVISION"
    assert response.json()["current_version"] == offer.revision + 1
    assert run_rows(d, occ.occurrence_id) == []
    assert selection_row(d, offer.selection_id)["state"] == "STALE"  # the write is kept


def test_a_real_child_or_a_closed_gate_never_creates_a_run(api: Api) -> None:
    d = api
    occ, offer, body = flow(d)
    d.gate_on = False  # the local/test synthetic gate is off
    try:
        response = post_create(d, "t1", body)
        assert response.status_code == 409 and response.json()["code"] == "STALE_REVISION"
    finally:
        d.gate_on = True
    assert run_rows(d, occ.occurrence_id) == []
    # the origin of the profile is the other half of X-19: flip the child to REAL by SQL
    d2occ, offer2, body2 = flow(d)
    with d.sessions().begin() as db:
        db.execute(
            text(
                "update be1_managed_profiles set data_origin = 'LEGACY_UNCLASSIFIED' "
                "where child_id = :c"
            ),
            {"c": offer2.child_id},
        )
    refused = post_create(d, "t1", body2)
    assert refused.status_code == 409 and refused.json()["code"] == "STALE_REVISION"
    assert run_rows(d, d2occ.occurrence_id) == []


# ----------------------------------------------------------------------------- one active run
def test_one_active_run_per_teacher_and_per_occurrence(api: Api) -> None:
    d = api
    occ1, offer1, body1 = flow(d)
    first = post_create(d, "t1", body1)
    assert first.status_code == 201
    occ2, offer2, body2 = flow(d)
    second = post_create(d, "t1", body2)
    assert second.status_code == 409 and second.json()["code"] == "ACTIVE_RUN_EXISTS"
    assert second.json()["message"] == "Đã có một lượt kể chuyện đang hoạt động."
    assert run_rows(d, occ2.occurrence_id) == []
    assert selection_row(d, offer2.selection_id)["state"] == "CONFIRMED"
    # the same occurrence held by another Teacher id (made in SQL): the reserved conflict code
    occ3, offer3, body3 = flow(d, who="t2", class_key="a2")
    now = datetime.now(UTC)
    held_account = f"another-teacher-{uuid4().hex[:12]}"
    with d.sessions().begin() as db:
        db.execute(
            insert(RUNS).values(
                run_id=str(uuid4()),
                actor_scope_kind="ORGANIZATION",
                actor_scope_ref=d.organization,
                profile_ref="synthetic-held",
                child_age_months=60,
                run_state="INPUT_PROCESSING",
                revision=1,
                version=1,
                retryable=False,
                occurrence_ref=occ3.occurrence_id,
                created_by_actor_ref=held_account,
                active_owner_teacher_id=held_account,
                created_at=now,
                updated_at=now,
            )
        )
    conflict = post_create(d, "t2", body3)
    assert conflict.status_code == 409 and conflict.json()["code"] == "TEACHER_ACTIVE_RUN_CONFLICT"
    assert conflict.json()["message"] == "Giáo viên này đang có một lượt kể chuyện đang hoạt động."
    assert selection_row(d, offer3.selection_id)["state"] == "CONFIRMED"


def test_two_teachers_of_two_classes_each_hold_a_run(api: Api) -> None:
    d = api
    occ1, offer1, body1 = flow(d, who="t1", class_key="a1")
    occ2, offer2, body2 = flow(d, who="t2", class_key="a2")
    assert post_create(d, "t1", body1).status_code == 201
    assert post_create(d, "t2", body2).status_code == 201
    held = {row["active_owner_teacher_id"] for row in run_rows(d)}
    assert {d.accounts["t1"], d.accounts["t2"]} <= held


# ----------------------------------------------------------------------------- concurrency
def _parallel(count: int, work: Callable[[int], Any]) -> list[Any]:
    barrier = Barrier(count)

    def wrapped(index: int) -> Any:
        barrier.wait(timeout=30)
        return work(index)

    with ThreadPoolExecutor(max_workers=count) as pool:
        return list(pool.map(wrapped, range(count)))


def test_eight_creates_with_one_key_make_one_run(api: Api) -> None:
    d = api
    occ, offer, body = flow(d)
    results = _parallel(8, lambda _i: post_create(d, "t1", body, key="one-key"))
    codes = sorted(response.status_code for response in results)
    assert codes == [201] * 8, [r.text for r in results if r.status_code != 201]
    assert len({r.json()["story_run"]["run_id"] for r in results}) == 1
    assert len(run_rows(d, occ.occurrence_id)) == 1


def test_eight_creates_with_eight_keys_for_one_selection_make_one_run(api: Api) -> None:
    d = api
    occ, offer, body = flow(d)
    results = _parallel(8, lambda _i: post_create(d, "t1", body))
    statuses = sorted(response.status_code for response in results)
    assert statuses.count(201) == 1 and statuses.count(409) == 7, statuses
    # SRS l.1698: every loser of a double submit by one Teacher gets ACTIVE_RUN_EXISTS (R1 F-1)
    assert [r.json()["code"] for r in results if r.status_code == 409] == ["ACTIVE_RUN_EXISTS"] * 7
    assert len(run_rows(d, occ.occurrence_id)) == 1
    assert selection_row(d, offer.selection_id)["state"] == "CONSUMED"


def test_two_occurrences_of_one_teacher_race_for_the_lock_and_the_loser_is_409(api: Api) -> None:
    d = api
    occ1, offer1, body1 = flow(d)
    occ2, offer2, body2 = flow(d)
    bodies = [body1, body2]
    results = _parallel(2, lambda index: post_create(d, "t1", bodies[index]))
    statuses = sorted(response.status_code for response in results)
    assert statuses == [201, 409], [r.text for r in results]
    loser = next(r for r in results if r.status_code == 409)
    assert loser.json()["code"] == "ACTIVE_RUN_EXISTS"
    owned = [row for row in run_rows(d) if row["active_owner_teacher_id"] == d.accounts["t1"]]
    assert len(owned) == 1
    with d.sessions()() as db:
        orphans = db.execute(
            text(
                "select count(*) from story.run_inputs i left join story.runs r "
                "on r.run_id = i.run_id where r.run_id is null"
            )
        ).scalar_one()
    assert orphans == 0


def test_a_plan_confirm_racing_a_create_is_ordered_by_the_occurrence_lock(api: Api) -> None:
    d = api
    occ, offer, body = flow(d)

    def work(index: int) -> Any:
        if index == 0:
            return post_create(d, "t1", body)
        return d.client.post(
            f"/v1/lesson-occurrences/{occ.occurrence_id}/plan-revisions",
            json={
                "expected_head_revision_no": occ.revision_no,
                "objectives": ["Mục tiêu mới"],
                "teacher_direction": "Hướng dẫn mới",
            },
            headers=headers(d.subjects["t1"], uuid4().hex),
        )

    results = _parallel(2, work)
    assert results[1].status_code == 201  # a plan draft: it does not change the approved pointer
    assert results[0].status_code == 201
    assert len(run_rows(d, occ.occurrence_id)) == 1


# ----------------------------------------------------------------------------- the lock
@pytest.mark.parametrize("terminal", LOCK_FREE)
def test_a_terminal_state_releases_the_lock_and_a_new_run_can_be_created(
    api: Api, terminal: str
) -> None:
    d = api
    occ, offer, body = flow(d)
    run_id = post_create(d, "t1", body).json()["story_run"]["run_id"]
    assert run_rows(d, occ.occurrence_id)[0]["active_owner_teacher_id"] == d.accounts["t1"]
    set_state(d, run_id, terminal)
    row = run_rows(d, occ.occurrence_id)[0]
    assert row["run_state"] == terminal and row["active_owner_teacher_id"] is None
    # the creator is kept for provenance only
    assert (
        row["created_by_actor_ref"] == d.accounts["t1"]
        and row["occurrence_ref"] == occ.occurrence_id
    )
    again_occ, again_offer, again_body = flow(d)
    assert post_create(d, "t1", again_body).status_code == 201


@pytest.mark.parametrize(
    "keeps", ["SAFETY_BLOCKED", "VIDEO_READY", "SCRIPT_REVIEW", "VIDEO_QUEUED"]
)
def test_a_non_terminal_state_keeps_the_lock(api: Api, keeps: str) -> None:
    d = api
    occ, offer, body = flow(d)
    run_id = post_create(d, "t1", body).json()["story_run"]["run_id"]
    set_state(d, run_id, keeps)
    assert run_rows(d, occ.occurrence_id)[0]["active_owner_teacher_id"] == d.accounts["t1"]


def test_the_database_refuses_a_lock_that_breaks_the_pins_or_the_owner_checks(api: Api) -> None:
    d = api
    now = datetime.now(UTC)
    base: dict[str, Any] = {
        "actor_scope_kind": "ORGANIZATION",
        "actor_scope_ref": d.organization,
        "profile_ref": "synthetic-check",
        "child_age_months": 60,
        "revision": 1,
        "version": 1,
        "retryable": False,
        "created_at": now,
        "updated_at": now,
    }
    bad = (
        # a pin without a creator, and a creator without a pin
        ({"occurrence_ref": str(uuid4())}, "ck_story_run_teacher_pins"),
        ({"created_by_actor_ref": "someone"}, "ck_story_run_teacher_pins"),
        # a Teacher lock without an occurrence, in the Parent scope, or beside a Parent lock
        (
            {"active_owner_teacher_id": "a1", "run_state": "INPUT_PROCESSING"},
            "ck_story_run_teacher_owner",
        ),
        (
            {
                "active_owner_teacher_id": "a1",
                "occurrence_ref": "o",
                "created_by_actor_ref": "a1",
                "actor_scope_kind": "PARENT_ACCOUNT",
            },
            "ck_story_run_teacher_owner",
        ),
        (
            {
                "active_owner_teacher_id": "a1",
                "occurrence_ref": "o",
                "created_by_actor_ref": "a1",
                "active_owner_parent_account_id": "p1",
            },
            "ck_story_run_teacher_owner",
        ),
        # a lock on a terminal state
        (
            {
                "active_owner_teacher_id": "a1",
                "occurrence_ref": "o",
                "created_by_actor_ref": "a1",
                "run_state": "COMPLETED",
            },
            "ck_story_run_teacher_lock_state",
        ),
    )
    for values, constraint in bad:
        row = {"run_id": str(uuid4()), "run_state": "INPUT_PROCESSING", **base, **values}
        with pytest.raises(DBAPIError) as refused, d.sessions().begin() as db:
            db.execute(insert(RUNS).values(**row))
        assert constraint in str(refused.value), (values, str(refused.value)[:200])

    # the unique indexes: one lock per Teacher and one active Teacher run per occurrence
    def lock(account: str, occurrence: str) -> dict[str, Any]:
        return {
            "run_id": str(uuid4()),
            "run_state": "INPUT_PROCESSING",
            **base,
            "active_owner_teacher_id": account,
            "occurrence_ref": occurrence,
            "created_by_actor_ref": account,
        }

    tag = uuid4().hex[:10]
    account, occurrence = f"acct-index-{tag}", f"occ-index-{tag}"
    with d.sessions().begin() as db:
        db.execute(insert(RUNS).values(**lock(account, occurrence)))
    for next_account, next_occurrence, index in (
        (account, f"occ-other-{tag}", "uq_story_run_active_teacher"),
        (f"acct-other-{tag}", occurrence, "uq_story_run_active_occurrence"),
    ):
        with pytest.raises(DBAPIError) as refused, d.sessions().begin() as db:
            db.execute(insert(RUNS).values(**lock(next_account, next_occurrence)))
        assert index in str(refused.value)
    # a lock-free row is not limited by either index
    free = lock(account, occurrence)
    free["active_owner_teacher_id"] = None
    free["run_state"] = "FAILED"
    with d.sessions().begin() as db:
        db.execute(insert(RUNS).values(**free))


def test_cancel_and_delete_release_the_lock_in_the_same_update_h1(api: Api) -> None:
    """T-13a hand-off H1: the cancel writes DELETE_PENDING and the trigger frees the lock."""
    d = api
    occ, offer, body = flow(d)
    run_id = post_create(d, "t1", body).json()["story_run"]["run_id"]
    cancelled = d.client.post(
        f"/v1/story-runs/{run_id}/cancel",
        json={"expected_revision": 1},
        headers=headers(d.subjects["t1"], uuid4().hex),
    )
    assert cancelled.status_code == 202, cancelled.text
    row = run_rows(d, occ.occurrence_id)[0]
    assert row["run_state"] == "DELETE_PENDING" and row["active_owner_teacher_id"] is None
    # a new run of the same Teacher: the selection of the cancelled run is spent, a new offer
    # follows
    assert post_create(d, "t1", body).status_code == 409
    occ2, offer2, body2 = flow(d)
    assert post_create(d, "t1", body2).status_code == 201


# ----------------------------------------------------------------------------- idle closeout
def test_the_idle_sweep_completes_or_abandons_a_teacher_run_and_frees_its_lock(api: Api) -> None:
    d = api
    now = datetime.now(UTC)
    old = now - timedelta(hours=169)
    for waiting, target in (("VIDEO_READY", "COMPLETED"), ("SCRIPT_REVIEW", "ABANDONED")):
        occ, offer, body = flow(d)
        run_id = post_create(d, "t1", body).json()["story_run"]["run_id"]
        set_state(d, run_id, waiting, job_state="SUCCEEDED", updated_at=old)
        # the listing the periodic sweep reads names the Teacher run too
        with d.sessions()() as session:
            listed = SqlStoryRunCloseoutStore(session).idle_candidates(now, 100_000)
        assert run_id in {candidate.run_id for candidate in listed}, waiting
        # one second short of 168 hours: not closed
        with d.sessions()() as session:
            short = SqlStoryRunCloseoutStore(session).close_idle(
                run_id, old + timedelta(hours=168) - timedelta(seconds=1)
            )
        assert short.name == "SKIPPED"
        assert run_rows(d, occ.occurrence_id)[0]["active_owner_teacher_id"] == d.accounts["t1"]
        with d.sessions()() as session:
            closed = SqlStoryRunCloseoutStore(session).close_idle(run_id, now)
        assert closed.name == target, waiting
        row = run_rows(d, occ.occurrence_id)[0]
        assert row["run_state"] == target and row["active_owner_teacher_id"] is None
        assert row["finished_at"] is not None


def test_the_idle_sweep_leaves_a_lock_free_fixture_run_alone(api: Api) -> None:
    d = api
    now = datetime.now(UTC)
    run_id = str(uuid4())
    with d.sessions().begin() as db:
        db.execute(
            insert(RUNS).values(
                run_id=run_id,
                actor_scope_kind="ORGANIZATION",
                actor_scope_ref=d.organization,
                profile_ref="synthetic-fixture",
                run_state="SCRIPT_REVIEW",
                revision=1,
                version=1,
                retryable=False,
                created_at=now - timedelta(days=60),
                updated_at=now - timedelta(days=60),
            )
        )
    with d.sessions()() as session:
        outcome = SqlStoryRunCloseoutStore(session).close_idle(run_id, now)
    assert outcome.name == "SKIPPED"


# -------------------------------------------------------------------- access follows the pin
def test_access_follows_the_current_responsible_teacher_and_not_the_creator(api: Api) -> None:
    d = api
    occ, offer, body = flow(d)
    run_id = post_create(d, "t1", body).json()["story_run"]["run_id"]
    url = f"/v1/story-runs/{run_id}"
    assert d.client.get(url, headers=headers(d.subjects["t1"])).status_code == 200
    # another Teacher row of the same class does not see it while it is not responsible
    assert d.client.get(url, headers=headers(d.subjects["t4"])).status_code == 404
    # the occurrence is handed to t4 (SQL; the saga is T-6b): the access moves with the pin
    with d.sessions().begin() as db:
        db.execute(
            update(OCCURRENCES)
            .where(OCCURRENCES.c.occurrence_id == occ.occurrence_id)
            .values(responsible_teacher_ref=d.accounts["t4"])
        )
    assert d.client.get(url, headers=headers(d.subjects["t4"])).status_code == 200
    creator = d.client.get(url, headers=headers(d.subjects["t1"]))
    assert creator.status_code == 404  # created_by_actor_ref never grants access (SRS l.553)
    assert run_rows(d, occ.occurrence_id)[0]["created_by_actor_ref"] == d.accounts["t1"]
    for who in ("parent", "manager", "platform", "stranger", "tother", "t2", "revoked", "inactive"):
        assert d.client.get(url, headers=headers(d.subjects[who])).status_code == 404, who


def test_a_parent_cannot_read_a_teacher_run_and_a_teacher_cannot_read_a_parent_run(
    api: Api,
) -> None:
    d = api
    occ, offer, body = flow(d)
    run_id = post_create(d, "t1", body).json()["story_run"]["run_id"]
    parent = d.client.get(f"/v1/story-runs/{run_id}", headers=headers(d.subjects["parent"]))
    assert parent.status_code == 404
    assert offer.child_id not in parent.text


# ----------------------------------------------------------------------------- the Parent create
def test_the_parent_create_still_works_and_keeps_its_own_lock(api: Api) -> None:
    """The Parent route is the unchanged handler: a Parent body from a Parent still creates."""
    d = api
    parent_subject = d.subjects["parent"]
    profile_id = uuid4()
    with d.sessions().begin() as db:
        db.add(
            ParentChildProfileModel(
                parent_profile_id=profile_id,
                owner_issuer=ISSUER,
                owner_subject=parent_subject,
                state="ACTIVE",
                current_revision_no=1,
            )
        )
        db.add(
            ParentProfileRevisionModel(
                profile_revision_id=uuid4(),
                parent_profile_id=profile_id,
                revision_no=1,
                age_months=72,
                display_name="Synthetic Parent child",
                authored_by_issuer=ISSUER,
                authored_by_subject=parent_subject,
                revision_hash="a" * 64,
            )
        )
    created = d.client.post(
        "/v1/story-runs",
        json={"parent_profile_id": str(profile_id)},
        headers=headers(parent_subject, uuid4().hex),
    )
    assert created.status_code == 201, created.text
    run = created.json()["story_run"]
    assert "parent_profile_id" in run and "profile_ref" not in run and "occurrence_id" not in run
    assert run["parent_profile_id"] == str(profile_id)
    assert run["context_snapshot"]["schema_version"] == "sketch2life.parent-context.v1"
    with d.sessions()() as db:
        row = db.execute(select(RUNS).where(RUNS.c.run_id == run["run_id"])).mappings().one()
    assert row["actor_scope_kind"] == "PARENT_ACCOUNT"
    assert row["active_owner_parent_account_id"] == d.accounts["parent"]
    assert row["active_owner_teacher_id"] is None and row["occurrence_ref"] is None
    assert row["created_by_actor_ref"] is None
    # the Parent lock still answers 409 ACTIVE_RUN_EXISTS, and the Parent reads its own view
    second = d.client.post(
        "/v1/story-runs",
        json={"parent_profile_id": str(profile_id)},
        headers=headers(parent_subject, uuid4().hex),
    )
    assert second.status_code == 409 and second.json()["code"] == "ACTIVE_RUN_EXISTS"
    read = d.client.get(f"/v1/story-runs/{run['run_id']}", headers=headers(parent_subject))
    assert read.status_code == 200 and "parent_profile_id" in read.json()["story_run"]
    active = d.client.get("/v1/story-runs/active/current", headers=headers(parent_subject))
    assert active.json()["story_run"]["run_id"] == run["run_id"]
    # a Teacher cannot read the Parent run
    assert (
        d.client.get(
            f"/v1/story-runs/{run['run_id']}", headers=headers(d.subjects["t1"])
        ).status_code
        == 404
    )


def test_no_child_name_reaches_a_stored_value_a_log_or_the_audit_trail(
    api: Api, caplog: pytest.LogCaptureFixture
) -> None:
    import logging

    caplog.set_level(logging.DEBUG)
    d = api
    occ, offer, body = flow(d)
    response = post_create(d, "t1", body)
    assert response.status_code == 201
    names = list(d.children.values())
    assert not any(name in caplog.text for name in names)
    with d.sessions()() as db:
        for table in (
            "story.runs",
            "story.run_inputs",
            "story.command_receipts",
            "core_audit_entries",
        ):
            dumped = db.execute(text(f"select t::text from {table} t")).scalars().all()  # noqa: S608
            assert not any(name in row for row in dumped for name in names), table
