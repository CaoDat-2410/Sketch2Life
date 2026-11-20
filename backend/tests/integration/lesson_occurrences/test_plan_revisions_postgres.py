"""FEAT-066 T-3d: occurrence plan revisions and confirm, on PostgreSQL.

SRS l.547-548 (activities, the safety checklist), l.775 (one approved plan per occurrence),
l.1442 (UC-04: the approved plan references a concrete text revision), l.1659-1660 (create a draft,
confirm with the expected hash and the checklist), l.1696-1699 (keys, stale fences), l.864-865
(scope). Runs only against a disposable database whose name contains ``be1_acceptance`` and
``frc08``. Principals are injected through the ``X-Test-Principal`` header; every identity, class,
occurrence, document, lesson and text is synthetic. Documents and library lessons are written
straight into their tables (the rows the T-3b attach and the Lesson Library write). The safety
checklist definition used here is a test-only value injected through a dependency override: the
shipped registry is empty.
"""

from __future__ import annotations

import hashlib
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
from sqlalchemy import func, select, text, update
from sqlalchemy.exc import DBAPIError

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.domain.lesson_library.model import canonical_content_hash
from sketch2life.domain.lesson_occurrences.plan import (
    activity_hash_entry,
    canonical_hash,
    plan_content_hash,
)
from sketch2life.domain.lesson_occurrences.safety_checklist import (
    PRODUCTION_REGISTRY,
    ChecklistDefinition,
    ChecklistItem,
    ChecklistRegistry,
)
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.lesson_library.tables import (
    LIBRARY_ITEMS,
    LIBRARY_VERSIONS,
    VERSION_ACTIVITIES,
)
from sketch2life.infrastructure.lesson_occurrences.tables import (
    DOCUMENT_REVISIONS,
    OCCURRENCES,
    PLAN_ACTIVITIES,
    PLAN_REVISIONS,
    SOURCE_DOCUMENTS,
)
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    ClassroomModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult
from sketch2life.interfaces.http.middleware.bounded_image_upload import (
    MAX_PLAN_CONFIRM_BODY_BYTES,
    MAX_PLAN_CREATE_BODY_BYTES,
)
from sketch2life.interfaces.http.routers.lesson_occurrences import get_checklist_registry

ISSUER = "synthetic-t3d-issuer"
LEAK_WORDS = ("bucket", "object_key", "presigned", "amazonaws", "organization_ref", "scanner")
FIRST_TEXT = "Tiêu đề: Vẽ con mèo\nMục tiêu: Nhận biết hình dạng con mèo"
# A test-only checklist definition (never shipped); the shipped registry is empty.
TEST_DEFINITION = ChecklistDefinition(
    "test-v1",
    (
        ChecklistItem("synthetic_a", "Synthetic item A"),
        ChecklistItem("synthetic_b", "Synthetic item B"),
    ),
)
TEST_REGISTRY = ChecklistRegistry((TEST_DEFINITION,))
CHECKED = [
    {"item_id": "synthetic_a", "checked": True},
    {"item_id": "synthetic_b", "checked": True},
]


def sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass
class Api:
    app: FastAPI
    client: TestClient
    token: str
    organization: str
    other_organization: str
    classes: dict[str, str] = field(default_factory=dict)
    subjects: dict[str, str] = field(default_factory=dict)
    accounts: dict[str, str] = field(default_factory=dict)
    registry: ChecklistRegistry = PRODUCTION_REGISTRY

    def sessions(self) -> Any:
        return self.app.state.be1_runtime.session_factory

    @property
    def engine(self) -> Any:
        return self.app.state.be1_runtime.engine


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
    monkeypatch.delenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", raising=False)
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    app = create_app()
    runtime = app.state.be1_runtime
    if runtime.engine is None or runtime.session_factory is None:
        pytest.fail("PostgreSQL runtime did not initialize")
    token = uuid4().hex[:8]
    organization, other = f"synthetic-t3d-org-{token}", f"synthetic-t3d-other-{token}"
    d = Api(app, TestClient(app), token, organization, other)

    def label(value: str) -> str:
        return f"synthetic-t3d-{value}-{token}"

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
            # label, account role, organization, class key (None = organization-wide), role
            ("t1", "teacher", organization, "a1", "teacher"),
            ("t4", "teacher", organization, "a1", "teacher"),  # a second teacher row on a1
            ("t2", "teacher", organization, "a2", "teacher"),
            ("g1", "teacher", organization, "a1", "guide"),
            ("o1", "teacher", organization, "a1", "observer"),
            ("tother", "teacher", other, "b1", "teacher"),
            ("orgt", "teacher", organization, None, "teacher"),  # an organization-wide row
            ("manager", "school_manager", organization, None, "school_admin"),
        )
        for key, role, org, class_key, assignment_role in people:
            subject = label(key)
            d.subjects[key] = subject
            d.accounts[key] = _identity(db, subject, role)
            _assign(db, org, subject, assignment_role, d.classes[class_key] if class_key else None)
        d.subjects["mixed"] = label("mixed")  # observer of a1 and teacher of a2
        d.accounts["mixed"] = _identity(db, label("mixed"), "teacher")
        _assign(db, organization, label("mixed"), "observer", d.classes["a1"])
        _assign(db, organization, label("mixed"), "teacher", d.classes["a2"])
        d.subjects["admin_teacher"] = label("admin_teacher")  # a School Manager who teaches a2
        d.accounts["admin_teacher"] = _identity(db, label("admin_teacher"), "school_manager")
        _assign(db, organization, label("admin_teacher"), "school_admin", None)
        _assign(db, organization, label("admin_teacher"), "teacher", d.classes["a2"])
        d.subjects["inactive"] = label("inactive")
        d.accounts["inactive"] = _identity(db, label("inactive"), "teacher", state="disabled")
        _assign(db, organization, label("inactive"), "teacher", d.classes["a1"])
        d.subjects["revoked"] = label("revoked")
        d.accounts["revoked"] = _identity(db, label("revoked"), "teacher")
        _assign(db, organization, label("revoked"), "teacher", d.classes["a1"], active=False)
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
    app.dependency_overrides[get_checklist_registry] = lambda: d.registry
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


def shape(response: Any) -> tuple[int, dict[str, Any]]:
    body = dict(response.json())
    body.pop("request_id", None)
    body.pop("correlation_id", None)
    return response.status_code, body


@dataclass
class Lesson:
    lesson_id: str
    version_id: str
    content_sha256: str
    version_no: int
    activity_ids: list[str]
    activities: list[dict[str, Any]]


def make_lesson(
    d: Api,
    *,
    creator: str = "t1",
    visibility: str = "SCHOOL",
    activity_count: int = 2,
    review_state: str = "APPROVED",
) -> Lesson:
    """A library lesson with a real full-content hash, as the Lesson Library stores it."""
    lesson_id, version_id = str(uuid4()), str(uuid4())
    content = {"locale": "vi-VN", "title": "Bài vẽ", "objectives": ["Mục tiêu bài học"]}
    activities = [
        {
            "title": f"Hoạt động {n}",
            "objective": f"Mục tiêu {n}",
            "materials_text": "Giấy, bút màu",
            "preparation_text": "",
            "instructions_text": f"Hướng dẫn hoạt động {n}",
            "observation_notes": "",
            "safety_notes": "",
            "activity_kind": "outdoor",
        }
        for n in range(1, activity_count + 1)
    ]
    content_hash = canonical_content_hash({**content, "activities": activities})
    ids = [str(uuid4()) for _ in activities]
    with d.sessions().begin() as db:
        db.execute(
            LIBRARY_ITEMS.insert().values(
                lesson_id=lesson_id,
                organization_id=d.organization,
                created_by=d.subjects[creator],
                visibility=visibility,
                internal_visibility="SCHOOL",
            )
        )
        db.execute(
            LIBRARY_VERSIONS.insert().values(
                version_id=version_id,
                lesson_id=lesson_id,
                version_no=2,
                content_json=content,
                structured_content_hash=content_hash,
                review_state=review_state,
                authored_by=d.subjects[creator],
            )
        )
        for index, (activity_id, activity) in enumerate(zip(ids, activities, strict=True), 1):
            db.execute(
                VERSION_ACTIVITIES.insert().values(
                    activity_id=activity_id,
                    version_id=version_id,
                    activity_order=index,
                    activity_json=activity,
                )
            )
    return Lesson(lesson_id, version_id, content_hash, 2, ids, activities)


def make_occurrence(
    d: Api, who: str = "t1", class_key: str = "a1", lesson: Lesson | None = None
) -> str:
    body: dict[str, Any] = {"class_id": d.classes[class_key], "title": "Bài học vẽ"}
    if lesson is not None:
        body["lesson_version_ref"] = {
            "lesson_id": lesson.lesson_id,
            "version_id": lesson.version_id,
            "content_sha256": lesson.content_sha256,
        }
    response = d.client.post(
        "/v1/lesson-occurrences", json=body, headers=headers(d.subjects[who], uuid4().hex)
    )
    assert response.status_code == 201, response.text
    return str(response.json()["occurrence_id"])


def make_document(d: Api, occurrence_id: str, first_text: str = FIRST_TEXT) -> tuple[str, str]:
    """One source document and its extraction revision 1; returns (document id, revision id)."""
    document_id, revision_id = str(uuid4()), str(uuid4())
    account = d.accounts["t1"]
    with d.sessions().begin() as db:
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
                extracted_text=first_text,
                extracted_text_hash=sha(first_text),
                parser_name="t3d-synthetic",
                parser_version="1",
                extraction_warnings=[],
                page_coverage=[1, 2, 3],
                created_by=account,
            )
        )
    return document_id, revision_id


def plan_url(occurrence_id: str, number: int | None = None, suffix: str = "") -> str:
    base = f"/v1/lesson-occurrences/{occurrence_id}/plan-revisions"
    return base if number is None else f"{base}/{number}{suffix}"


def fields(**overrides: Any) -> dict[str, Any]:
    values: dict[str, Any] = {
        "objectives": ["Nhận biết hình tròn"],
        "teacher_direction": "Câu chuyện về chú mèo đi tìm bạn",
    }
    values.update(overrides)
    return values


def create(
    d: Api,
    occurrence_id: str,
    head: int,
    *,
    who: str = "t1",
    key: str | None = None,
    **overrides: Any,
) -> Any:
    return d.client.post(
        plan_url(occurrence_id),
        json={"expected_head_revision_no": head, **fields(**overrides)},
        headers=headers(d.subjects[who], key or uuid4().hex),
    )


def confirm(
    d: Api,
    occurrence_id: str,
    number: int,
    content_hash: str,
    *,
    who: str = "t1",
    key: str | None = None,
    checklist: list[dict[str, Any]] | None = None,
) -> Any:
    body: dict[str, Any] = {"expected_plan_hash": content_hash}
    if checklist is not None:
        body["checklist"] = checklist
    return d.client.post(
        plan_url(occurrence_id, number, "/confirm"),
        json=body,
        headers=headers(d.subjects[who], key or uuid4().hex),
    )


def entry(order: int, items: list[dict[str, Any]] | None = None, version: str = "test-v1") -> Any:
    return {
        "activity_order": order,
        "checklist_version": version,
        "items": CHECKED if items is None else items,
    }


def custom(title: str = "Vẽ bằng ngón tay", description: str = "Cho trẻ vẽ bằng ngón tay") -> Any:
    return {"kind": "CUSTOM", "title": title, "description": description}


def plans(d: Api, occurrence_id: str) -> list[Any]:
    with d.sessions()() as db:
        return list(
            db.execute(
                select(PLAN_REVISIONS)
                .where(PLAN_REVISIONS.c.occurrence_id == occurrence_id)
                .order_by(PLAN_REVISIONS.c.revision_no)
            )
            .mappings()
            .all()
        )


def activity_rows(d: Api, plan_revision_id: str) -> list[Any]:
    with d.sessions()() as db:
        return list(
            db.execute(
                select(PLAN_ACTIVITIES)
                .where(PLAN_ACTIVITIES.c.plan_revision_id == plan_revision_id)
                .order_by(PLAN_ACTIVITIES.c.activity_order)
            )
            .mappings()
            .all()
        )


def occurrence_row(d: Api, occurrence_id: str) -> Any:
    with d.sessions()() as db:
        return (
            db.execute(select(OCCURRENCES).where(OCCURRENCES.c.occurrence_id == occurrence_id))
            .mappings()
            .one()
        )


def document_revision(d: Api, revision_id: str) -> Any:
    with d.sessions()() as db:
        return (
            db.execute(
                select(DOCUMENT_REVISIONS).where(
                    DOCUMENT_REVISIONS.c.document_revision_id == revision_id
                )
            )
            .mappings()
            .one()
        )


def receipts(d: Api, occurrence_id: str, kind: str = "create") -> list[Any]:
    scope_like = (
        f"POST /v1/lesson-occurrences/{occurrence_id}/plan-revisions"
        if kind == "create"
        else f"POST /v1/lesson-occurrences/{occurrence_id}/plan-revisions/%/confirm"
    )
    with d.sessions()() as db:
        return list(
            db.execute(
                text(
                    "SELECT principal_ref, operation_scope, idempotency_key, request_fingerprint,"
                    " response_json FROM be1_command_receipts WHERE operation_scope LIKE :scope"
                ),
                {"scope": scope_like},
            )
            .mappings()
            .all()
        )


def audits(d: Api, occurrence_id: str, action: str) -> list[Any]:
    with d.sessions()() as db:
        return list(
            db.execute(
                text(
                    "SELECT actor_ref, action, resource_type, resource_id, organization_id"
                    " FROM core_audit_entries WHERE action = :action AND resource_id IN"
                    " (SELECT plan_revision_id FROM lesson.plan_revisions WHERE occurrence_id = :o)"
                ),
                {"action": action, "o": occurrence_id},
            )
            .mappings()
            .all()
        )


def state_snapshot(d: Api, occurrence_id: str) -> Any:
    """Every column of the occurrence, its plans and their activities, for no-write checks."""
    rows = plans(d, occurrence_id)
    return (
        tuple(occurrence_row(d, occurrence_id).values()),
        [tuple(row.values()) for row in rows],
        [
            [tuple(a.values()) for a in activity_rows(d, str(row["plan_revision_id"]))]
            for row in rows
        ],
    )


def unlocked(d: Api, occurrence_id: str) -> bool:
    with d.engine.connect() as conn:
        try:
            conn.execute(
                text(
                    "SELECT 1 FROM lesson.occurrences WHERE occurrence_id = :id FOR UPDATE NOWAIT"
                ),
                {"id": occurrence_id},
            )
        except DBAPIError:
            return False
        finally:
            conn.rollback()
    return True


def idle_in_transaction(d: Api) -> int:
    with d.engine.connect() as conn:
        return int(
            conn.execute(
                text(
                    "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()"
                    " AND state = 'idle in transaction'"
                )
            ).scalar_one()
        )


def approved_plans(d: Api, occurrence_id: str) -> list[int]:
    return [int(r["revision_no"]) for r in plans(d, occurrence_id) if r["state"] == "APPROVED"]


def approve(d: Api, occurrence_id: str, head: int, **overrides: Any) -> dict[str, Any]:
    """Create then confirm a plan revision with no custom activity; returns the confirm body."""
    created = create(d, occurrence_id, head, **overrides)
    assert created.status_code == 201, created.text
    number = created.json()["revision_no"]
    confirmed = confirm(d, occurrence_id, number, created.json()["content_hash"])
    assert confirmed.status_code == 200, confirmed.text
    return dict(confirmed.json())


# ----------------------------------------------------------------------------- create: happy paths
def test_the_first_draft_is_written_immutable_and_hashed_as_the_domain_says(api: Api) -> None:
    d = api
    occurrence_id = make_occurrence(d)
    occurrence_before = occurrence_row(d, occurrence_id)
    response = create(d, occurrence_id, 0, key="k-first", safety_notes="Nhắc trẻ rửa tay")
    assert response.status_code == 201, response.text
    body = response.json()
    expected_hash = plan_content_hash(
        occurrence_id=occurrence_id,
        document=None,
        objectives=["Nhận biết hình tròn"],
        teacher_direction="Câu chuyện về chú mèo đi tìm bạn",
        safety_notes="Nhắc trẻ rửa tay",
        lesson_ref=None,
        activities=[],
    )
    assert body["contract"] == "LessonPlanRevisionV1" and body["content_hash"] == expected_hash
    assert (
        body["revision_no"] == 1
        and body["state"] == "DRAFT"
        and body["occurrence_id"] == occurrence_id
    )
    assert body["document_revision_ref"] is None and body["lesson_version_ref"] is None
    assert body["activities"] == [] and body["approved_at"] is None
    assert response.headers["Location"] == plan_url(occurrence_id, 1)
    assert response.headers["ETag"] == f'"{expected_hash}.DRAFT"'
    ((row,),) = [(r,) for r in plans(d, occurrence_id)]
    assert (
        row["state"] == "DRAFT" and row["revision_no"] == 1 and row["content_hash"] == expected_hash
    )
    assert row["created_by"] == d.accounts["t1"] and row["approved_by"] is None
    assert (
        row["objectives"] == ["Nhận biết hình tròn"] and row["safety_notes"] == "Nhắc trẻ rửa tay"
    )
    assert row["source_document_revision_id"] is None and row["source_lesson_id"] is None
    # writing a draft changes nothing about the occurrence
    occurrence_after = occurrence_row(d, occurrence_id)
    for column in ("state", "revision", "updated_at", "approved_plan_revision_id"):
        assert occurrence_after[column] == occurrence_before[column]
    assert len(audits(d, occurrence_id, "lesson.plan_revision.create")) == 1
    assert len(receipts(d, occurrence_id)) == 1
    assert unlocked(d, occurrence_id) and idle_in_transaction(d) == 0


def test_a_draft_with_a_document_revision_pins_it_and_the_hash_names_its_text(api: Api) -> None:
    d = api
    occurrence_id = make_occurrence(d)
    document_id, revision_id = make_document(d, occurrence_id)
    response = create(
        d, occurrence_id, 0, document_revision_ref={"document_id": document_id, "revision_no": 1}
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["document_revision_ref"] == {"document_id": document_id, "revision_no": 1}
    expected = plan_content_hash(
        occurrence_id=occurrence_id,
        document={"document_revision_id": revision_id, "text_hash": sha(FIRST_TEXT)},
        objectives=["Nhận biết hình tròn"],
        teacher_direction="Câu chuyện về chú mèo đi tìm bạn",
        safety_notes=None,
        lesson_ref=None,
        activities=[],
    )
    assert body["content_hash"] == expected
    assert plans(d, occurrence_id)[0]["source_document_revision_id"] == revision_id
    # creating a draft does not review the text
    assert document_revision(d, revision_id)["review_state"] == "NEEDS_REVIEW"


def test_lesson_activities_copy_the_pinned_version_with_their_snapshot_and_hash(api: Api) -> None:
    d = api
    lesson = make_lesson(d, activity_count=3)
    occurrence_id = make_occurrence(d, lesson=lesson)
    response = create(
        d,
        occurrence_id,
        0,
        activities=[
            {"kind": "LESSON", "lesson_activity_id": lesson.activity_ids[2]},
            {"kind": "LESSON", "lesson_activity_id": lesson.activity_ids[0]},
        ],
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["lesson_version_ref"] == {
        "lesson_id": lesson.lesson_id,
        "version_id": lesson.version_id,
        "content_sha256": lesson.content_sha256,
    }
    assert body["lesson_version_no"] == 2
    assert [a["order"] for a in body["activities"]] == [1, 2]  # request order
    assert body["activities"][0]["title"] == "Hoạt động 3"
    assert body["activities"][0]["description"] == "Hướng dẫn hoạt động 3"
    assert body["activities"][1]["lesson_activity_id"] == lesson.activity_ids[0]
    assert all(a["checklist_required"] is False for a in body["activities"])
    plan = plans(d, occurrence_id)[0]
    assert plan["source_lesson_version_id"] == lesson.version_id
    assert plan["source_lesson_version_hash"] == lesson.content_sha256
    rows = activity_rows(d, str(plan["plan_revision_id"]))
    assert [r["activity_kind"] for r in rows] == ["LESSON", "LESSON"]
    assert rows[0]["catalog_activity_ref"] == lesson.activity_ids[2]
    assert rows[0]["activity_snapshot"] == lesson.activities[2]
    assert rows[0]["activity_snapshot_hash"] == canonical_hash(lesson.activities[2])
    assert rows[0]["activity_version"] == 2 and rows[0]["custom_title"] is None
    entries = [
        activity_hash_entry(
            order=index,
            kind="LESSON",
            catalog_activity_ref=lesson.activity_ids[position],
            activity_version=2,
            title=None,
            description=None,
            snapshot_hash=canonical_hash(lesson.activities[position]),
        )
        for index, position in ((1, 2), (2, 0))
    ]
    assert body["content_hash"] == plan_content_hash(
        occurrence_id=occurrence_id,
        document=None,
        objectives=["Nhận biết hình tròn"],
        teacher_direction="Câu chuyện về chú mèo đi tìm bạn",
        safety_notes=None,
        lesson_ref={
            "lesson_id": lesson.lesson_id,
            "version_id": lesson.version_id,
            "version_no": 2,
            "content_hash": lesson.content_sha256,
        },
        activities=entries,
    )


def test_a_whole_24_activity_lesson_and_every_limit_at_its_maximum_is_accepted(api: Api) -> None:
    d = api
    lesson = make_lesson(d, activity_count=24)
    occurrence_id = make_occurrence(d, lesson=lesson)
    response = create(
        d,
        occurrence_id,
        0,
        objectives=["đ" * 1000] * 12,
        teacher_direction="h" * 2000,
        safety_notes="n" * 2000,
        activities=[{"kind": "LESSON", "lesson_activity_id": i} for i in lesson.activity_ids],
    )
    assert response.status_code == 201, response.text
    assert len(response.json()["activities"]) == 24
    plan = plans(d, occurrence_id)[0]
    assert len(plan["objectives"]) == 12 and len(plan["objectives"][0]) == 1000


def test_custom_activities_at_their_limits_with_a_test_checklist_registry(api: Api) -> None:
    d = api
    d.registry = TEST_REGISTRY
    occurrence_id = make_occurrence(d)
    response = create(
        d,
        occurrence_id,
        0,
        activities=[custom("t" * 160, "d" * 4000), custom("Hai", "Mô tả\nnhiều dòng")],
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert [a["checklist_required"] for a in body["activities"]] == [True, True]
    assert [a["confirmed"] for a in body["activities"]] == [False, False]
    rows = activity_rows(d, str(plans(d, occurrence_id)[0]["plan_revision_id"]))
    assert rows[0]["custom_title"] == "t" * 160 and rows[0]["custom_description"] == "d" * 4000
    assert rows[0]["catalog_activity_ref"] is None and rows[0]["activity_snapshot"] is None
    assert rows[0]["safety_checklist_version"] is None and rows[0]["confirmed_at"] is None


def test_the_next_draft_is_head_plus_one_and_leaves_earlier_revisions_alone(api: Api) -> None:
    d = api
    occurrence_id = make_occurrence(d)
    first = create(d, occurrence_id, 0)
    before = [tuple(r.values()) for r in plans(d, occurrence_id)]
    second = create(d, occurrence_id, 1, teacher_direction="Hướng truyện mới")
    assert second.status_code == 201 and second.json()["revision_no"] == 2
    after = [tuple(r.values()) for r in plans(d, occurrence_id)]
    assert after[0] == before[0] and len(after) == 2
    assert first.json()["content_hash"] != second.json()["content_hash"]
    # identical content is allowed and is a new revision with the same hash
    third = create(d, occurrence_id, 2, teacher_direction="Hướng truyện mới")
    assert third.status_code == 201 and third.json()["revision_no"] == 3
    assert third.json()["content_hash"] == second.json()["content_hash"]


# ----------------------------------------------------------------------------- create: refusals
def test_a_stale_head_is_409_with_the_head_and_writes_nothing(api: Api) -> None:
    d = api
    occurrence_id = make_occurrence(d)
    ahead = create(d, occurrence_id, 3)
    assert ahead.status_code == 409
    assert ahead.json()["code"] == "STALE_REVISION" and ahead.json()["current_version"] == 0
    assert "ETag" not in ahead.headers
    created = create(d, occurrence_id, 0)
    stale = create(d, occurrence_id, 0, teacher_direction="Từ bản cũ")
    assert stale.status_code == 409
    body = stale.json()
    assert body["code"] == "STALE_REVISION" and body["current_version"] == 1
    assert type(body["current_version"]) is int
    assert stale.headers["ETag"] == f'"{created.json()["content_hash"]}.DRAFT"'
    assert [r["revision_no"] for r in plans(d, occurrence_id)] == [1]
    assert len(receipts(d, occurrence_id)) == 1  # refusals write no receipt
    retry = create(d, occurrence_id, 1, teacher_direction="Từ bản mới", key="k-after-stale")
    assert retry.status_code == 201 and retry.json()["revision_no"] == 2


def test_two_concurrent_creates_from_one_head_make_exactly_one_revision(api: Api) -> None:
    d = api
    occurrence_id = make_occurrence(d)
    barrier = Barrier(2)

    def attempt(index: int) -> tuple[int, dict[str, Any]]:
        barrier.wait()
        return shape(
            create(d, occurrence_id, 0, key=f"k-{index}", teacher_direction=f"Hướng số {index}")
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt, (1, 2)))
    assert sorted(status for status, _ in results) == [201, 409], results
    loser = next(body for status, body in results if status == 409)
    assert loser["code"] == "STALE_REVISION" and loser["current_version"] == 1
    assert [r["revision_no"] for r in plans(d, occurrence_id)] == [1]
    assert unlocked(d, occurrence_id) and idle_in_transaction(d) == 0


def test_two_concurrent_requests_with_one_key_make_one_revision(api: Api) -> None:
    d = api
    occurrence_id = make_occurrence(d)
    barrier = Barrier(2)

    def attempt(_: int) -> tuple[int, dict[str, Any]]:
        barrier.wait()
        return shape(create(d, occurrence_id, 0, key="k-twin"))

    with ThreadPoolExecutor(max_workers=2) as pool:
        first, second = list(pool.map(attempt, range(2)))
    assert first == second and first[0] == 201
    assert len(plans(d, occurrence_id)) == 1 and len(receipts(d, occurrence_id)) == 1
    assert len(audits(d, occurrence_id, "lesson.plan_revision.create")) == 1


def test_a_document_reference_must_be_a_live_revision_of_this_occurrence(api: Api) -> None:
    d = api
    occurrence_id = make_occurrence(d)
    other_occurrence = make_occurrence(d)
    document_id, _revision = make_document(d, occurrence_id)
    foreign_document, _ = make_document(d, other_occurrence)
    unknown_occurrence = d.client.get(plan_url(str(uuid4())), headers=headers(d.subjects["t1"]))
    expected = shape(unknown_occurrence)
    for ref in (
        {"document_id": str(uuid4()), "revision_no": 1},
        {"document_id": document_id, "revision_no": 2},
        {"document_id": foreign_document, "revision_no": 1},
    ):
        response = create(d, occurrence_id, 0, document_revision_ref=ref)
        assert response.status_code == 404, ref
        assert shape(response) == expected  # the same body as an unknown occurrence
    with d.sessions().begin() as db:
        db.execute(
            update(SOURCE_DOCUMENTS)
            .where(SOURCE_DOCUMENTS.c.source_document_id == document_id)
            .values(document_state="DELETED", deleted_at=func.now())
        )
    deleted = create(
        d, occurrence_id, 0, document_revision_ref={"document_id": document_id, "revision_no": 1}
    )
    assert deleted.status_code == 404
    assert plans(d, occurrence_id) == []


def test_a_lesson_activity_must_belong_to_the_pinned_version_and_needs_a_pin(api: Api) -> None:
    d = api
    lesson = make_lesson(d)
    other_lesson = make_lesson(d)
    pinned = make_occurrence(d, lesson=lesson)
    foreign = create(
        d,
        pinned,
        0,
        activities=[
            {"kind": "LESSON", "lesson_activity_id": lesson.activity_ids[0]},
            {"kind": "LESSON", "lesson_activity_id": other_lesson.activity_ids[0]},
            {"kind": "LESSON", "lesson_activity_id": str(uuid4())},
        ],
    )
    assert foreign.status_code == 400
    assert foreign.json()["field_errors"] == [
        {"field": "activities[1].lesson_activity_id", "code": "INVALID_FORMAT"},
        {"field": "activities[2].lesson_activity_id", "code": "INVALID_FORMAT"},
    ]
    assert plans(d, pinned) == []
    unpinned = make_occurrence(d)
    refused = create(
        d,
        unpinned,
        0,
        activities=[{"kind": "LESSON", "lesson_activity_id": lesson.activity_ids[0]}],
    )
    assert refused.status_code == 400
    assert refused.json()["field_errors"] == [
        {"field": "activities[0].kind", "code": "NOT_SUPPORTED"}
    ]
    assert plans(d, unpinned) == []


def test_a_tampered_library_version_is_detected_before_anything_is_copied(api: Api) -> None:
    d = api
    lesson = make_lesson(d)
    occurrence_id = make_occurrence(d, lesson=lesson)
    wanted = [{"kind": "LESSON", "lesson_activity_id": lesson.activity_ids[0]}]
    with d.sessions().begin() as db:
        db.execute(
            update(VERSION_ACTIVITIES)
            .where(VERSION_ACTIVITIES.c.activity_id == lesson.activity_ids[0])
            .values(activity_json={**lesson.activities[0], "title": "Đã bị sửa"})
        )
    tampered = create(d, occurrence_id, 0, activities=wanted)
    assert tampered.status_code == 409 and tampered.json()["code"] == "STALE_REVISION"
    assert "current_version" not in tampered.json()
    assert plans(d, occurrence_id) == []
    # a plan that copies nothing from the library does not depend on it
    assert create(d, occurrence_id, 0).status_code == 201


@pytest.mark.parametrize(
    "damage",
    ["unapproved", "archived", "hidden", "private_of_another_author"],
)
def test_a_pinned_version_that_is_no_longer_eligible_cannot_be_copied(
    api: Api, damage: str
) -> None:
    d = api
    lesson = make_lesson(d, creator="t1" if damage != "private_of_another_author" else "t4")
    occurrence_id = make_occurrence(d, lesson=lesson)
    with d.sessions().begin() as db:
        if damage == "unapproved":
            db.execute(
                update(LIBRARY_VERSIONS)
                .where(LIBRARY_VERSIONS.c.version_id == lesson.version_id)
                .values(review_state="CHANGES_REQUESTED")
            )
        elif damage == "archived":
            db.execute(
                update(LIBRARY_ITEMS)
                .where(LIBRARY_ITEMS.c.lesson_id == lesson.lesson_id)
                .values(state="ARCHIVED")
            )
        elif damage == "hidden":
            db.execute(
                update(LIBRARY_ITEMS)
                .where(LIBRARY_ITEMS.c.lesson_id == lesson.lesson_id)
                .values(moderation_state="HIDDEN")
            )
        else:
            db.execute(
                update(LIBRARY_ITEMS)
                .where(LIBRARY_ITEMS.c.lesson_id == lesson.lesson_id)
                .values(visibility="PRIVATE")
            )
    response = create(
        d,
        occurrence_id,
        0,
        activities=[{"kind": "LESSON", "lesson_activity_id": lesson.activity_ids[0]}],
    )
    assert response.status_code == 409 and response.json()["code"] == "INVALID_STATE_TRANSITION"
    assert plans(d, occurrence_id) == []


def test_custom_and_catalog_activities_are_refused_explicitly_without_a_checklist(api: Api) -> None:
    d = api
    occurrence_id = make_occurrence(d)
    response = create(d, occurrence_id, 0, activities=[custom(), {"kind": "CATALOG"}])
    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] == "INVALID_REQUEST"
    assert payload["field_errors"] == [
        {"field": "activities[0].kind", "code": "NOT_SUPPORTED"},
        {"field": "activities[1].kind", "code": "NOT_SUPPORTED"},
    ]
    assert plans(d, occurrence_id) == [] and receipts(d, occurrence_id) == []
    # a plan with no custom activity is unaffected by the missing checklist
    assert create(d, occurrence_id, 0).status_code == 201
    # and CATALOG stays refused even when a checklist exists
    d.registry = TEST_REGISTRY
    still = create(d, occurrence_id, 1, activities=[{"kind": "CATALOG"}])
    assert still.status_code == 400
    assert still.json()["field_errors"] == [
        {"field": "activities[0].kind", "code": "NOT_SUPPORTED"}
    ]


def test_bad_requests_write_nothing(api: Api) -> None:
    d = api
    occurrence_id = make_occurrence(d)
    before = state_snapshot(d, occurrence_id)
    for overrides in (
        {"objectives": []},
        {"objectives": ["x"] * 13},
        {"objectives": ["x" * 1001]},
        {"objectives": ["   "]},
        {"objectives": ["có NUL \x00"]},
        {"teacher_direction": " \n "},
        {"teacher_direction": "d" * 2001},
        {"safety_notes": "n" * 2001},
        {"activities": [{"kind": "LESSON"}] * 25},
        {"activities": [{"kind": "LESSON", "lesson_activity_id": "a", "title": "t"}]},
        {"lesson_version_ref": {"lesson_id": "x", "version_id": "y", "content_sha256": "a" * 64}},
        {"state": "APPROVED"},
    ):
        response = create(d, occurrence_id, 0, **overrides)
        assert response.status_code == 400, overrides
        assert response.json()["code"] == "INVALID_REQUEST"
    missing_key = d.client.post(
        plan_url(occurrence_id),
        json={"expected_head_revision_no": 0, **fields()},
        headers=headers(d.subjects["t1"]),
    )
    assert missing_key.status_code == 400
    assert state_snapshot(d, occurrence_id) == before
    assert receipts(d, occurrence_id) == []


def test_validation_does_not_decide_scope(api: Api) -> None:
    d = api
    occurrence_id = make_occurrence(d)
    response = create(d, occurrence_id, 0, who="stranger", activities=[custom()])
    assert response.status_code == 400  # the request rule answers before any lookup


def test_an_archived_occurrence_accepts_no_new_plan(api: Api) -> None:
    d = api
    occurrence_id = make_occurrence(d)
    with d.sessions().begin() as db:
        db.execute(
            update(OCCURRENCES)
            .where(OCCURRENCES.c.occurrence_id == occurrence_id)
            .values(state="ARCHIVED")
        )
    response = create(d, occurrence_id, 0)
    assert response.status_code == 409 and response.json()["code"] == "INVALID_STATE_TRANSITION"
    assert plans(d, occurrence_id) == []


# ----------------------------------------------------------------------------- idempotency
def test_a_replay_returns_the_first_answer_even_after_the_plan_was_confirmed(api: Api) -> None:
    d = api
    occurrence_id = make_occurrence(d)
    first = create(d, occurrence_id, 0, key="k-replay")
    assert first.status_code == 201
    confirmed = confirm(d, occurrence_id, 1, first.json()["content_hash"])
    assert confirmed.status_code == 200
    again = create(d, occurrence_id, 0, key="k-replay")
    assert again.status_code == 201
    assert again.json() == first.json() and again.json()["state"] == "DRAFT"
    assert again.headers["ETag"] == first.headers["ETag"]
    assert len(plans(d, occurrence_id)) == 1 and len(receipts(d, occurrence_id)) == 1


def test_another_payload_with_the_key_is_refused_and_keys_are_scoped(api: Api) -> None:
    d = api
    occurrence_id = make_occurrence(d)
    other_occurrence = make_occurrence(d)
    assert create(d, occurrence_id, 0, key="k-same").status_code == 201
    clash = create(d, occurrence_id, 0, key="k-same", teacher_direction="Nội dung khác")
    assert clash.status_code == 400 and clash.json()["code"] == "INVALID_IDEMPOTENCY_KEY"
    clash_head = create(d, occurrence_id, 1, key="k-same")
    assert clash_head.status_code == 400
    # the same key on another occurrence is another command
    assert create(d, other_occurrence, 0, key="k-same").status_code == 201
    assert len(plans(d, occurrence_id)) == 1


def test_a_revoked_teacher_cannot_replay_an_old_key(api: Api) -> None:
    d = api
    occurrence_id = make_occurrence(d)
    assert create(d, occurrence_id, 0, key="k-revoke").status_code == 201
    with d.sessions().begin() as db:
        db.execute(
            text(
                "UPDATE be1_organization_assignments SET active = false WHERE subject = :s"
                " AND class_id = :c"
            ),
            {"s": d.subjects["t1"], "c": d.classes["a1"]},
        )
    replay = create(d, occurrence_id, 0, key="k-revoke")
    assert replay.status_code == 404


# ----------------------------------------------------------------------------- scope
NOT_VISIBLE = (
    "t2",
    "tother",
    "manager",
    "admin_teacher",
    "parent",
    "platform",
    "stranger",
    "inactive",
    "revoked",
)
READ_ONLY_ROLES = ("t4", "g1", "o1", "mixed", "orgt")


def test_scope_of_create_and_confirm_is_the_responsible_teacher_only(api: Api) -> None:
    d = api
    occurrence_id = make_occurrence(d)
    created = create(d, occurrence_id, 0)
    content_hash = created.json()["content_hash"]
    unknown = shape(d.client.get(plan_url(str(uuid4())), headers=headers(d.subjects["t1"])))
    assert unknown[0] == 404
    for who in NOT_VISIBLE:
        for response in (
            create(d, occurrence_id, 1, who=who),
            confirm(d, occurrence_id, 1, content_hash, who=who),
        ):
            assert shape(response) == unknown, who
    for who in READ_ONLY_ROLES:
        for response in (
            create(d, occurrence_id, 1, who=who),
            confirm(d, occurrence_id, 1, content_hash, who=who),
        ):
            assert response.status_code == 403, who
            assert response.json()["code"] == "ACTION_NOT_ALLOWED"
    assert [r["revision_no"] for r in plans(d, occurrence_id)] == [1]
    assert plans(d, occurrence_id)[0]["state"] == "DRAFT"
    assert approved_plans(d, occurrence_id) == []
    # no refusal left a receipt behind
    assert len(receipts(d, occurrence_id)) == 1 and receipts(d, occurrence_id, "confirm") == []


def test_unknown_or_over_long_ids_answer_the_uniform_404(api: Api) -> None:
    d = api
    unknown = shape(d.client.get(plan_url(str(uuid4())), headers=headers(d.subjects["t1"])))
    for identifier in (str(uuid4()), "x" * 37, "x" * 200):
        assert shape(create(d, identifier, 0)) == unknown
        assert shape(confirm(d, identifier, 1, "a" * 64)) == unknown


# ----------------------------------------------------------------------------- confirm: happy path
def test_confirm_writes_every_part_in_one_transaction(api: Api) -> None:
    d = api
    occurrence_id = make_occurrence(d)
    document_id, revision_id = make_document(d, occurrence_id)
    created = create(
        d, occurrence_id, 0, document_revision_ref={"document_id": document_id, "revision_no": 1}
    )
    content_hash = created.json()["content_hash"]
    occurrence_before = occurrence_row(d, occurrence_id)
    etag_before = d.client.get(
        f"/v1/lesson-occurrences/{occurrence_id}", headers=headers(d.subjects["t1"])
    ).headers["ETag"]
    response = confirm(d, occurrence_id, 1, content_hash, key="k-confirm")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["state"] == "APPROVED" and body["content_hash"] == content_hash
    assert body["approved_at"] is not None and body["supersedes_revision_no"] is None
    assert response.headers["ETag"] == f'"{content_hash}.APPROVED"'
    assert response.headers["Content-Location"] == plan_url(occurrence_id, 1)
    plan = plans(d, occurrence_id)[0]
    assert plan["state"] == "APPROVED" and plan["approved_by"] == d.accounts["t1"]
    assert plan["approved_at"] is not None and plan["superseded_at"] is None
    # the pinned text revision carries the one-way review stamp
    stamped = document_revision(d, revision_id)
    assert stamped["review_state"] == "CONFIRMED" and stamped["reviewed_by"] == d.accounts["t1"]
    assert stamped["reviewed_at"] is not None
    # the occurrence points at the plan, is APPROVED and its revision and ETag moved
    after = occurrence_row(d, occurrence_id)
    assert after["approved_plan_revision_id"] == plan["plan_revision_id"]
    assert after["state"] == "APPROVED" and after["revision"] == occurrence_before["revision"] + 1
    assert after["updated_at"] >= occurrence_before["updated_at"]
    read = d.client.get(
        f"/v1/lesson-occurrences/{occurrence_id}", headers=headers(d.subjects["t1"])
    )
    assert read.headers["ETag"] != etag_before and read.headers["ETag"] == '"2"'
    summary = read.json()["approved_plan"]
    assert summary["revision_no"] == 1 and summary["plan_hash"] == content_hash
    assert read.json()["state"] == "APPROVED"
    stale_read = d.client.get(
        f"/v1/lesson-occurrences/{occurrence_id}",
        headers=headers(d.subjects["t1"], **{"If-None-Match": etag_before}),
    )
    assert stale_read.status_code == 200  # the old validator no longer matches
    assert len(audits(d, occurrence_id, "lesson.plan.confirm")) == 1
    assert len(receipts(d, occurrence_id, "confirm")) == 1
    assert unlocked(d, occurrence_id) and idle_in_transaction(d) == 0
    # a plan can be listed by the occurrence list filter
    listing = d.client.get(
        "/v1/lesson-occurrences",
        params={"class_id": d.classes["a1"], "state": "APPROVED"},
        headers=headers(d.subjects["t1"]),
    )
    assert occurrence_id in [item["occurrence_id"] for item in listing.json()["items"]]


def test_the_edit_of_a_document_after_the_confirm_never_moves_the_approved_plan(api: Api) -> None:
    d = api
    occurrence_id = make_occurrence(d)
    document_id, revision_id = make_document(d, occurrence_id)
    ref = {"document_id": document_id, "revision_no": 1}
    created = create(d, occurrence_id, 0, document_revision_ref=ref)
    assert confirm(d, occurrence_id, 1, created.json()["content_hash"]).status_code == 200
    edit = d.client.post(
        f"/v1/lesson-occurrences/{occurrence_id}/documents/{document_id}/revisions",
        json={"extracted_text": "Văn bản đã sửa sau khi duyệt", "expected_head_revision_no": 1},
        headers=headers(d.subjects["t1"], uuid4().hex),
    )
    assert edit.status_code == 201 and edit.json()["review_state"] == "NEEDS_REVIEW"
    plan = plans(d, occurrence_id)[0]
    assert plan["source_document_revision_id"] == revision_id and plan["state"] == "APPROVED"
    assert document_revision(d, revision_id)["review_state"] == "CONFIRMED"
    read = d.client.get(plan_url(occurrence_id, 1), headers=headers(d.subjects["t1"]))
    assert read.json()["document_revision_ref"] == ref


def test_a_text_revision_that_is_already_confirmed_keeps_its_first_stamp(api: Api) -> None:
    d = api
    occurrence_id = make_occurrence(d)
    document_id, revision_id = make_document(d, occurrence_id)
    ref = {"document_id": document_id, "revision_no": 1}
    first = create(d, occurrence_id, 0, document_revision_ref=ref)
    assert confirm(d, occurrence_id, 1, first.json()["content_hash"]).status_code == 200
    stamp = document_revision(d, revision_id)
    second = create(d, occurrence_id, 1, document_revision_ref=ref, teacher_direction="Hướng mới")
    assert confirm(d, occurrence_id, 2, second.json()["content_hash"]).status_code == 200
    again = document_revision(d, revision_id)
    assert (again["reviewed_by"], again["reviewed_at"]) == (
        stamp["reviewed_by"],
        stamp["reviewed_at"],
    )


def test_confirm_without_a_document_leaves_every_document_untouched(api: Api) -> None:
    d = api
    occurrence_id = make_occurrence(d)
    _document, revision_id = make_document(d, occurrence_id)
    approve(d, occurrence_id, 0)
    assert document_revision(d, revision_id)["review_state"] == "NEEDS_REVIEW"


def test_a_newly_approved_plan_supersedes_the_previous_one(api: Api) -> None:
    d = api
    occurrence_id = make_occurrence(d)
    first = approve(d, occurrence_id, 0)
    assert approved_plans(d, occurrence_id) == [1]
    second = approve(d, occurrence_id, 1, teacher_direction="Hướng truyện thứ hai")
    assert second["supersedes_revision_no"] == 1 and second["revision_no"] == 2
    rows = plans(d, occurrence_id)
    assert [r["state"] for r in rows] == ["SUPERSEDED", "APPROVED"]
    assert rows[0]["superseded_at"] is not None and rows[0]["approved_at"] is not None
    assert (
        rows[0]["approved_by"] == d.accounts["t1"]
        and rows[0]["content_hash"] == first["content_hash"]
    )
    assert approved_plans(d, occurrence_id) == [2]
    after = occurrence_row(d, occurrence_id)
    assert after["approved_plan_revision_id"] == rows[1]["plan_revision_id"]
    assert after["revision"] == 3 and after["state"] == "APPROVED"
    read = d.client.get(
        f"/v1/lesson-occurrences/{occurrence_id}", headers=headers(d.subjects["t1"])
    )
    assert read.json()["approved_plan"]["revision_no"] == 2
    # the older revision stays readable as SUPERSEDED
    old = d.client.get(plan_url(occurrence_id, 1), headers=headers(d.subjects["t1"]))
    assert old.json()["state"] == "SUPERSEDED"
    assert old.headers["ETag"] == f'"{first["content_hash"]}.SUPERSEDED"'


# ----------------------------------------------------------------------------- confirm: fences
def test_only_the_head_can_be_confirmed_so_an_old_draft_never_replaces_a_newer_approval(
    api: Api,
) -> None:
    d = api
    occurrence_id = make_occurrence(d)
    first = create(d, occurrence_id, 0)
    second = create(d, occurrence_id, 1, teacher_direction="Hướng mới")
    before = state_snapshot(d, occurrence_id)
    stale = confirm(d, occurrence_id, 1, first.json()["content_hash"])
    assert stale.status_code == 409
    body = stale.json()
    assert body["code"] == "STALE_REVISION" and body["current_version"] == 2
    assert stale.headers["ETag"] == f'"{second.json()["content_hash"]}.DRAFT"'
    assert state_snapshot(d, occurrence_id) == before
    ok = confirm(d, occurrence_id, 2, second.json()["content_hash"])
    assert ok.status_code == 200
    # revision 1 stays a DRAFT and can no longer be confirmed once a newer revision is approved
    assert [r["state"] for r in plans(d, occurrence_id)] == ["DRAFT", "APPROVED"]
    late = confirm(d, occurrence_id, 1, first.json()["content_hash"])
    assert late.status_code == 409 and late.json()["code"] == "STALE_REVISION"
    assert approved_plans(d, occurrence_id) == [2]
    assert (
        occurrence_row(d, occurrence_id)["approved_plan_revision_id"]
        == plans(d, occurrence_id)[1]["plan_revision_id"]
    )


def test_a_stale_hash_is_409_with_the_head_and_writes_nothing(api: Api) -> None:
    d = api
    occurrence_id = make_occurrence(d)
    created = create(d, occurrence_id, 0)
    before = state_snapshot(d, occurrence_id)
    wrong = confirm(d, occurrence_id, 1, "0" * 64)
    assert wrong.status_code == 409
    assert wrong.json()["code"] == "STALE_REVISION" and wrong.json()["current_version"] == 1
    assert wrong.headers["ETag"] == f'"{created.json()["content_hash"]}.DRAFT"'
    assert state_snapshot(d, occurrence_id) == before
    assert receipts(d, occurrence_id, "confirm") == []


def test_an_unknown_revision_and_a_revision_of_another_occurrence_are_404(api: Api) -> None:
    d = api
    occurrence_id = make_occurrence(d)
    other = make_occurrence(d)
    created = create(d, other, 0)
    assert confirm(d, occurrence_id, 1, "a" * 64).status_code == 404  # no plan at all
    create(d, occurrence_id, 0)
    assert confirm(d, occurrence_id, 5, "a" * 64).status_code == 404
    through_other = confirm(d, occurrence_id, 1, created.json()["content_hash"])
    assert through_other.status_code == 409  # the hash of the other occurrence's plan is no fence
    assert plans(d, other)[0]["state"] == "DRAFT"
    assert (
        d.client.get(plan_url(occurrence_id, 5), headers=headers(d.subjects["t1"])).status_code
        == 404
    )


def test_confirming_an_approved_plan_again_with_its_hash_changes_nothing(api: Api) -> None:
    d = api
    occurrence_id = make_occurrence(d)
    approved = approve(d, occurrence_id, 0)
    create(d, occurrence_id, 1, teacher_direction="Bản nháp mới")  # a newer draft exists
    before = state_snapshot(d, occurrence_id)
    again = confirm(d, occurrence_id, 1, approved["content_hash"], key="k-noop")
    assert again.status_code == 200 and again.json()["state"] == "APPROVED"
    assert again.json()["supersedes_revision_no"] is None
    assert (
        state_snapshot(d, occurrence_id) == before
    )  # no plan, activity, document or pointer change
    assert len(audits(d, occurrence_id, "lesson.plan.confirm")) == 1  # no second audit row
    wrong = confirm(d, occurrence_id, 1, "f" * 64)
    assert wrong.status_code == 409 and wrong.json()["code"] == "STALE_REVISION"
    assert wrong.json()["current_version"] == 2


def test_a_superseded_plan_is_409_whatever_the_rest_of_the_request_says(api: Api) -> None:
    d = api
    occurrence_id = make_occurrence(d)
    first = approve(d, occurrence_id, 0)
    approve(d, occurrence_id, 1, teacher_direction="Hướng thứ hai")
    before = state_snapshot(d, occurrence_id)
    for response in (
        confirm(d, occurrence_id, 1, first["content_hash"]),
        confirm(d, occurrence_id, 1, "0" * 64),
        confirm(d, occurrence_id, 1, first["content_hash"], checklist=[entry(1)]),
    ):
        assert response.status_code == 409, response.text
        assert response.json()["code"] == "INVALID_STATE_TRANSITION"
    assert state_snapshot(d, occurrence_id) == before


def test_confirm_on_an_archived_occurrence_is_409(api: Api) -> None:
    d = api
    occurrence_id = make_occurrence(d)
    created = create(d, occurrence_id, 0)
    with d.sessions().begin() as db:
        db.execute(
            update(OCCURRENCES)
            .where(OCCURRENCES.c.occurrence_id == occurrence_id)
            .values(state="ARCHIVED")
        )
    response = confirm(d, occurrence_id, 1, created.json()["content_hash"])
    assert response.status_code == 409 and response.json()["code"] == "INVALID_STATE_TRANSITION"
    assert plans(d, occurrence_id)[0]["state"] == "DRAFT"


# ----------------------------------------------------------------------------- confirm: replay
def test_a_confirm_replay_equals_the_first_answer_even_after_the_plan_is_superseded(
    api: Api,
) -> None:
    d = api
    occurrence_id = make_occurrence(d)
    created = create(d, occurrence_id, 0)
    first = confirm(d, occurrence_id, 1, created.json()["content_hash"], key="k-c")
    assert first.status_code == 200
    approve(d, occurrence_id, 1, teacher_direction="Hướng thứ hai")
    replay = confirm(d, occurrence_id, 1, created.json()["content_hash"], key="k-c")
    assert replay.status_code == 200
    assert replay.json() == first.json() and replay.json()["state"] == "APPROVED"
    assert replay.headers["ETag"] == first.headers["ETag"]
    assert len(receipts(d, occurrence_id, "confirm")) == 2  # one per confirmed revision


def test_another_body_with_the_confirm_key_is_refused_and_the_key_is_per_revision(api: Api) -> None:
    d = api
    occurrence_id = make_occurrence(d)
    created = create(d, occurrence_id, 0)
    assert (
        confirm(d, occurrence_id, 1, created.json()["content_hash"], key="k-x").status_code == 200
    )
    clash = confirm(d, occurrence_id, 1, "e" * 64, key="k-x")
    assert clash.status_code == 400 and clash.json()["code"] == "INVALID_IDEMPOTENCY_KEY"
    # the same key for another revision number is another command
    second = create(d, occurrence_id, 1, teacher_direction="Hướng mới")
    assert confirm(d, occurrence_id, 2, second.json()["content_hash"], key="k-x").status_code == 200


def test_a_revoked_teacher_cannot_replay_a_confirm(api: Api) -> None:
    d = api
    occurrence_id = make_occurrence(d)
    created = create(d, occurrence_id, 0)
    assert (
        confirm(d, occurrence_id, 1, created.json()["content_hash"], key="k-rv").status_code == 200
    )
    with d.sessions().begin() as db:
        db.execute(
            text(
                "UPDATE be1_organization_assignments SET active = false WHERE subject = :s"
                " AND class_id = :c"
            ),
            {"s": d.subjects["t1"], "c": d.classes["a1"]},
        )
    assert (
        confirm(d, occurrence_id, 1, created.json()["content_hash"], key="k-rv").status_code == 404
    )


# ----------------------------------------------------------------------------- confirm: concurrency
def test_two_concurrent_confirms_of_the_head_approve_once(api: Api) -> None:
    d = api
    occurrence_id = make_occurrence(d)
    created = create(d, occurrence_id, 0)
    content_hash = created.json()["content_hash"]
    barrier = Barrier(2)

    def attempt(label: str) -> tuple[int, dict[str, Any]]:
        barrier.wait()
        return shape(confirm(d, occurrence_id, 1, content_hash, key=f"k-{label}"))

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt, ("a", "b")))
    assert [status for status, _ in results] == [200, 200], results
    assert approved_plans(d, occurrence_id) == [1]
    assert occurrence_row(d, occurrence_id)["revision"] == 2  # bumped once
    assert len(audits(d, occurrence_id, "lesson.plan.confirm")) == 1
    assert unlocked(d, occurrence_id) and idle_in_transaction(d) == 0


def test_concurrent_confirms_of_the_head_and_of_an_older_draft_leave_one_approval(api: Api) -> None:
    d = api
    occurrence_id = make_occurrence(d)
    first = create(d, occurrence_id, 0)
    second = create(d, occurrence_id, 1, teacher_direction="Hướng mới")
    barrier = Barrier(2)

    def attempt(job: tuple[int, str]) -> tuple[int, dict[str, Any]]:
        number, content_hash = job
        barrier.wait()
        return shape(confirm(d, occurrence_id, number, content_hash, key=f"k-{number}"))

    jobs = [(1, first.json()["content_hash"]), (2, second.json()["content_hash"])]
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = dict(zip((1, 2), pool.map(attempt, jobs), strict=True))
    assert results[1][0] == 409 and results[1][1]["code"] == "STALE_REVISION"
    assert results[2][0] == 200
    assert approved_plans(d, occurrence_id) == [2]


def test_a_create_racing_a_confirm_is_serialised_and_never_leaves_two_approvals(api: Api) -> None:
    d = api
    occurrence_id = make_occurrence(d)
    first = create(d, occurrence_id, 0)
    barrier = Barrier(2)

    def do_confirm(_: int) -> tuple[int, dict[str, Any]]:
        barrier.wait()
        return shape(confirm(d, occurrence_id, 1, first.json()["content_hash"], key="k-race-c"))

    def do_create(_: int) -> tuple[int, dict[str, Any]]:
        barrier.wait()
        return shape(create(d, occurrence_id, 1, key="k-race-n", teacher_direction="Hướng mới"))

    with ThreadPoolExecutor(max_workers=2) as pool:
        confirm_future = pool.submit(do_confirm, 0)
        create_future = pool.submit(do_create, 0)
        confirm_result, create_result = confirm_future.result(), create_future.result()
    # either order is legal: confirm first (both succeed) or create first (the confirm is stale)
    assert create_result[0] == 201
    assert confirm_result[0] in (200, 409)
    expected = [1] if confirm_result[0] == 200 else []
    assert approved_plans(d, occurrence_id) == expected
    pointer = occurrence_row(d, occurrence_id)["approved_plan_revision_id"]
    assert (pointer is not None) == bool(expected)
    assert [r["revision_no"] for r in plans(d, occurrence_id)] == [1, 2]


# ----------------------------------------------------------------------------- safety checklist
def test_a_checklist_is_recorded_for_every_custom_activity_at_confirm(api: Api) -> None:
    d = api
    d.registry = TEST_REGISTRY
    occurrence_id = make_occurrence(d)
    created = create(d, occurrence_id, 0, activities=[custom(), custom("Hai", "Mô tả hai")])
    assert created.status_code == 201, created.text
    response = confirm(
        d,
        occurrence_id,
        1,
        created.json()["content_hash"],
        checklist=[entry(2), entry(1)],
    )
    assert response.status_code == 200, response.text
    assert [a["confirmed"] for a in response.json()["activities"]] == [True, True]
    assert {a["checklist_version"] for a in response.json()["activities"]} == {"test-v1"}
    plan = plans(d, occurrence_id)[0]
    rows = activity_rows(d, str(plan["plan_revision_id"]))
    for row in rows:
        assert row["safety_checklist_version"] == "test-v1"
        assert row["checklist_result"] == {"items": CHECKED}
        assert row["confirmed_by"] == d.accounts["t1"] and row["confirmed_at"] is not None
    assert plan["state"] == "APPROVED"


def test_an_unchecked_item_blocks_the_approval_and_nothing_changes(api: Api) -> None:
    d = api
    d.registry = TEST_REGISTRY
    occurrence_id = make_occurrence(d)
    document_id, revision_id = make_document(d, occurrence_id)
    created = create(
        d,
        occurrence_id,
        0,
        document_revision_ref={"document_id": document_id, "revision_no": 1},
        activities=[custom(), custom("Hai", "Mô tả hai")],
    )
    content_hash = created.json()["content_hash"]
    before = state_snapshot(d, occurrence_id)
    receipts_before = receipts(d, occurrence_id, "confirm")
    partial = [
        {"item_id": "synthetic_a", "checked": True},
        {"item_id": "synthetic_b", "checked": False},
    ]
    response = confirm(d, occurrence_id, 1, content_hash, checklist=[entry(1), entry(2, partial)])
    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] == "INVALID_REQUEST"
    assert payload["field_errors"] == [
        {"field": "checklist[2].items.synthetic_b", "code": "REQUIRED"}
    ]
    assert state_snapshot(d, occurrence_id) == before  # not even the answered activity changed
    assert document_revision(d, revision_id)["review_state"] == "NEEDS_REVIEW"
    assert approved_plans(d, occurrence_id) == []
    assert occurrence_row(d, occurrence_id)["approved_plan_revision_id"] is None
    assert receipts(d, occurrence_id, "confirm") == receipts_before
    assert audits(d, occurrence_id, "lesson.plan.confirm") == []
    assert unlocked(d, occurrence_id)


def test_every_missing_or_wrong_checklist_answer_is_named(api: Api) -> None:
    d = api
    d.registry = TEST_REGISTRY
    occurrence_id = make_occurrence(d)
    lesson = make_lesson(d)
    pinned = make_occurrence(d, lesson=lesson)
    created = create(d, occurrence_id, 0, activities=[custom(), custom("Hai", "Mô tả hai")])
    content_hash = created.json()["content_hash"]
    missing = confirm(d, occurrence_id, 1, content_hash)
    assert missing.status_code == 400
    assert missing.json()["field_errors"] == [
        {"field": "checklist[1].items.synthetic_a", "code": "REQUIRED"},
        {"field": "checklist[1].items.synthetic_b", "code": "REQUIRED"},
        {"field": "checklist[2].items.synthetic_a", "code": "REQUIRED"},
        {"field": "checklist[2].items.synthetic_b", "code": "REQUIRED"},
    ]
    wrong_version = confirm(
        d, occurrence_id, 1, content_hash, checklist=[entry(1, version="test-v0"), entry(2)]
    )
    assert wrong_version.json()["field_errors"] == [
        {"field": "checklist[1].checklist_version", "code": "INVALID_FORMAT"}
    ]
    extras = confirm(
        d,
        occurrence_id,
        1,
        content_hash,
        checklist=[entry(1, CHECKED + [{"item_id": "extra", "checked": True}]), entry(2), entry(3)],
    )
    assert extras.json()["field_errors"] == [
        {"field": "checklist[1].items.extra", "code": "UNKNOWN_FIELD"},
        {"field": "checklist[3]", "code": "UNKNOWN_FIELD"},
    ]
    repeated = confirm(d, occurrence_id, 1, content_hash, checklist=[entry(1), entry(1), entry(2)])
    assert repeated.json()["field_errors"] == [{"field": "checklist[1]", "code": "INVALID_FORMAT"}]
    # an entry for a plan with no custom activity is an unknown field too
    plain = create(d, pinned, 0)
    refused = confirm(d, pinned, 1, plain.json()["content_hash"], checklist=[entry(1)])
    assert refused.status_code == 400
    assert refused.json()["field_errors"] == [{"field": "checklist[1]", "code": "UNKNOWN_FIELD"}]
    assert approved_plans(d, occurrence_id) == [] and approved_plans(d, pinned) == []


def test_a_plan_with_a_custom_activity_cannot_be_confirmed_while_no_checklist_exists(
    api: Api,
) -> None:
    d = api
    d.registry = TEST_REGISTRY
    occurrence_id = make_occurrence(d)
    created = create(d, occurrence_id, 0, activities=[custom()])
    assert created.status_code == 201
    d.registry = PRODUCTION_REGISTRY  # the shipped, empty registry
    response = confirm(d, occurrence_id, 1, created.json()["content_hash"], checklist=[entry(1)])
    assert response.status_code == 400
    # the confirm request has no activities array: the path names the plan activity order
    assert response.json()["field_errors"] == [{"field": "checklist[1]", "code": "NOT_SUPPORTED"}]
    assert approved_plans(d, occurrence_id) == []


def test_a_plan_without_custom_activities_confirms_with_the_empty_shipped_registry(
    api: Api,
) -> None:
    d = api
    lesson = make_lesson(d)
    occurrence_id = make_occurrence(d, lesson=lesson)
    body = approve(
        d,
        occurrence_id,
        0,
        activities=[{"kind": "LESSON", "lesson_activity_id": lesson.activity_ids[0]}],
    )
    assert body["state"] == "APPROVED" and body["activities"][0]["confirmed"] is False
    assert body["activities"][0]["checklist_required"] is False
    assert approve(d, make_occurrence(d), 0)["state"] == "APPROVED"  # zero activities too


# ----------------------------------------------------------------------------- the database guards
def _raises(d: Api, statement: str, params: dict[str, Any], needle: str) -> None:
    with pytest.raises(DBAPIError) as error, d.sessions().begin() as db:
        db.execute(text(statement), params)
    assert needle in str(error.value.orig)


def test_the_database_protects_plans_written_through_the_api(api: Api) -> None:
    d = api
    d.registry = TEST_REGISTRY
    occurrence_id = make_occurrence(d)
    approve(d, occurrence_id, 0)
    assert create(d, occurrence_id, 1, teacher_direction="Bản nháp hai").status_code == 201
    assert (
        create(
            d, occurrence_id, 2, teacher_direction="Bản nháp ba", activities=[custom()]
        ).status_code
        == 201
    )
    rows = plans(d, occurrence_id)
    approved_id, plain_id, custom_id = (str(row["plan_revision_id"]) for row in rows)
    account = d.accounts["t1"]
    approve_sql = (
        "UPDATE lesson.plan_revisions SET state = 'APPROVED', approved_by = :a, approved_at = now()"
        " WHERE plan_revision_id = :p"
    )
    _raises(
        d,
        "UPDATE lesson.plan_revisions SET teacher_direction = 'x' WHERE plan_revision_id = :p",
        {"p": approved_id},
        "PLAN_IMMUTABLE_CONTENT",
    )
    _raises(
        d,
        "UPDATE lesson.plan_revisions SET objectives = '[\"x\"]'::jsonb"
        " WHERE plan_revision_id = :p",
        {"p": plain_id},
        "PLAN_IMMUTABLE_CONTENT",
    )
    _raises(
        d,
        "UPDATE lesson.plan_revisions SET content_hash = repeat('b', 64)"
        " WHERE plan_revision_id = :p",
        {"p": plain_id},
        "PLAN_IMMUTABLE_CONTENT",
    )
    _raises(
        d,
        "DELETE FROM lesson.plan_revisions WHERE plan_revision_id = :p",
        {"p": plain_id},
        "PLAN_REVISION_DELETE_FORBIDDEN",
    )
    _raises(
        d,
        "INSERT INTO lesson.plan_activities (plan_activity_id, plan_revision_id, activity_order,"
        " activity_kind, custom_title, custom_description) VALUES (:id, :p, 9, 'CUSTOM', 't', 'd')",
        {"id": str(uuid4()), "p": approved_id},
        "PLAN_ACTIVITY_PLAN_NOT_DRAFT",
    )
    # a second APPROVED row is refused (one approved plan per occurrence, SRS l.775)
    _raises(d, approve_sql, {"p": plain_id, "a": account}, "uq_plan_one_approved")
    with d.sessions().begin() as db:
        db.execute(
            text(
                "UPDATE lesson.plan_revisions SET state = 'SUPERSEDED', superseded_at = now()"
                " WHERE plan_revision_id = :p"
            ),
            {"p": approved_id},
        )
    # direct approval with an unconfirmed Teacher-written activity is refused by the database
    _raises(d, approve_sql, {"p": custom_id, "a": account}, "LESSON_PLAN_CHECKLIST_REQUIRED")
    # an illegal transition: a superseded plan never becomes approved again
    _raises(d, approve_sql, {"p": approved_id, "a": account}, "PLAN_ILLEGAL_TRANSITION")
    assert [row["state"] for row in plans(d, occurrence_id)] == ["SUPERSEDED", "DRAFT", "DRAFT"]


# ----------------------------------------------------------------------------- reads
def test_the_list_pages_newest_first_without_gap_or_repeat(api: Api) -> None:
    d = api
    occurrence_id = make_occurrence(d)
    lesson = make_lesson(d)
    pinned = make_occurrence(d, lesson=lesson)
    for head in range(5):
        assert create(d, occurrence_id, head, teacher_direction=f"Hướng {head}").status_code == 201
    create(
        d,
        pinned,
        0,
        activities=[{"kind": "LESSON", "lesson_activity_id": a} for a in lesson.activity_ids],
    )
    pages: list[list[int]] = []
    cursor: str | None = None
    while True:
        params: dict[str, Any] = {"limit": 2}
        if cursor:
            params["cursor"] = cursor
        page = d.client.get(
            plan_url(occurrence_id), params=params, headers=headers(d.subjects["t1"])
        )
        assert page.status_code == 200, page.text
        body = page.json()
        assert body["contract"] == "LessonPlanRevisionPageV1" and "ETag" not in page.headers
        pages.append([item["revision_no"] for item in body["items"]])
        cursor = body["next_cursor"]
        if cursor is None:
            break
    assert pages == [[5, 4], [3, 2], [1]]
    first = d.client.get(plan_url(occurrence_id), headers=headers(d.subjects["t1"])).json()[
        "items"
    ][0]
    assert set(first) == {
        "revision_no",
        "state",
        "content_hash",
        "activity_count",
        "created_at",
        "approved_at",
    }
    assert first["state"] == "DRAFT" and first["activity_count"] == 0
    counted = d.client.get(plan_url(pinned), headers=headers(d.subjects["t1"])).json()["items"][0]
    assert counted["activity_count"] == 2
    # a revision created between two pages does not disturb the cursor
    page_one = d.client.get(
        plan_url(occurrence_id), params={"limit": 2}, headers=headers(d.subjects["t1"])
    )
    assert create(d, occurrence_id, 5, teacher_direction="Hướng mới nhất").status_code == 201
    page_two = d.client.get(
        plan_url(occurrence_id),
        params={"limit": 2, "cursor": page_one.json()["next_cursor"]},
        headers=headers(d.subjects["t1"]),
    )
    assert [i["revision_no"] for i in page_two.json()["items"]] == [3, 2]


def test_the_list_limits_and_cursor_are_checked(api: Api) -> None:
    d = api
    occurrence_id = make_occurrence(d)
    for params, field_name in (
        ({"limit": 101}, "limit"),
        ({"limit": 0}, "limit"),
        ({"cursor": "not-a-cursor"}, "cursor"),
    ):
        response = d.client.get(
            plan_url(occurrence_id), params=params, headers=headers(d.subjects["t1"])
        )
        assert response.status_code == 400, params
        assert any(item["field"] == field_name for item in response.json()["field_errors"])
    assert (
        d.client.get(
            plan_url(occurrence_id), params={"limit": 100}, headers=headers(d.subjects["t1"])
        ).status_code
        == 200
    )


def test_reads_are_open_to_the_class_roles_and_closed_to_everyone_else(api: Api) -> None:
    d = api
    occurrence_id = make_occurrence(d)
    created = create(d, occurrence_id, 0)
    unknown = shape(d.client.get(plan_url(str(uuid4())), headers=headers(d.subjects["t1"])))
    for who in ("t1", "t4", "g1", "o1", "mixed", "orgt"):
        listing = d.client.get(plan_url(occurrence_id), headers=headers(d.subjects[who]))
        single = d.client.get(plan_url(occurrence_id, 1), headers=headers(d.subjects[who]))
        assert listing.status_code == 200 and single.status_code == 200, who
        assert single.json()["content_hash"] == created.json()["content_hash"]
    for who in NOT_VISIBLE:
        assert (
            shape(d.client.get(plan_url(occurrence_id), headers=headers(d.subjects[who])))
            == unknown
        )
        assert (
            shape(d.client.get(plan_url(occurrence_id, 1), headers=headers(d.subjects[who])))
            == unknown
        )


def test_a_single_read_has_a_strong_etag_and_304_only_after_authorisation(api: Api) -> None:
    d = api
    occurrence_id = make_occurrence(d)
    created = create(d, occurrence_id, 0)
    etag = f'"{created.json()["content_hash"]}.DRAFT"'
    read = d.client.get(plan_url(occurrence_id, 1), headers=headers(d.subjects["g1"]))
    assert read.status_code == 200 and read.headers["ETag"] == etag
    assert read.headers["Cache-Control"] == "private, no-cache"
    matched = d.client.get(
        plan_url(occurrence_id, 1), headers=headers(d.subjects["g1"], **{"If-None-Match": etag})
    )
    assert matched.status_code == 304 and matched.content == b""
    stranger = d.client.get(
        plan_url(occurrence_id, 1),
        headers=headers(d.subjects["stranger"], **{"If-None-Match": etag}),
    )
    assert stranger.status_code == 404  # never a 304 for a caller without scope
    assert confirm(d, occurrence_id, 1, created.json()["content_hash"]).status_code == 200
    after = d.client.get(
        plan_url(occurrence_id, 1), headers=headers(d.subjects["g1"], **{"If-None-Match": etag})
    )
    assert after.status_code == 200 and after.headers["ETag"] != etag  # the state moved


def test_no_body_leaks_storage_words_organization_ids_or_the_pin_fields_of_the_request(
    api: Api,
) -> None:
    d = api
    lesson = make_lesson(d)
    occurrence_id = make_occurrence(d, lesson=lesson)
    document_id, _ = make_document(d, occurrence_id)
    created = create(
        d,
        occurrence_id,
        0,
        document_revision_ref={"document_id": document_id, "revision_no": 1},
        activities=[{"kind": "LESSON", "lesson_activity_id": lesson.activity_ids[0]}],
    )
    confirmed = confirm(d, occurrence_id, 1, created.json()["content_hash"])
    texts = [
        created.text,
        confirmed.text,
        d.client.get(plan_url(occurrence_id), headers=headers(d.subjects["t1"])).text,
        d.client.get(plan_url(occurrence_id, 1), headers=headers(d.subjects["t1"])).text,
        str([dict(r) for r in receipts(d, occurrence_id)]),
        str([dict(r) for r in receipts(d, occurrence_id, "confirm")]),
    ]
    for payload in texts:
        lowered = payload.lower()
        for word in LEAK_WORDS + (d.organization.lower(),):
            assert word not in lowered, word
    receipt = receipts(d, occurrence_id)[0]
    assert receipt["response_json"]["contract"] == "LessonPlanRevisionV1"


# ----------------------------------------------------------------------------- request size guard
def test_an_oversize_body_is_413_before_authentication_and_writes_nothing(api: Api) -> None:
    d = api
    occurrence_id = make_occurrence(d)
    before = state_snapshot(d, occurrence_id)
    big = b'{"teacher_direction":"' + b"a" * MAX_PLAN_CREATE_BODY_BYTES + b'"}'
    response = d.client.post(
        plan_url(occurrence_id),
        content=big,
        headers={**headers(d.subjects["stranger"], "k-big"), "Content-Type": "application/json"},
    )
    assert response.status_code == 413 and response.json()["code"] == "MEDIA_TOO_LARGE"
    created = create(d, occurrence_id, 0)
    huge = b'{"expected_plan_hash":"' + b"a" * MAX_PLAN_CONFIRM_BODY_BYTES + b'"}'
    confirm_response = d.client.post(
        plan_url(occurrence_id, 1, "/confirm"),
        content=huge,
        headers={**headers(d.subjects["stranger"], "k-big2"), "Content-Type": "application/json"},
    )
    assert confirm_response.status_code == 413
    assert confirm_response.json()["code"] == "MEDIA_TOO_LARGE"
    assert len(plans(d, occurrence_id)) == 1 and created.status_code == 201
    assert before[1] == []  # the oversize create wrote no plan


def test_a_full_size_request_with_control_characters_fits_the_cap_and_is_stored(api: Api) -> None:
    d = api
    lesson = make_lesson(d, activity_count=24)
    occurrence_id = make_occurrence(d, lesson=lesson)
    response = create(
        d,
        occurrence_id,
        0,
        objectives=["\u0001" * 1000] * 12,
        teacher_direction="\u0001" * 2000,
        safety_notes="\u0001" * 2000,
        activities=[{"kind": "LESSON", "lesson_activity_id": i} for i in lesson.activity_ids],
    )
    assert response.status_code == 201, response.text
    assert plans(d, occurrence_id)[0]["objectives"][0] == "\u0001" * 1000


# ----------------------------------------------------------------------------- NUL in ids (review)
def test_a_nul_in_a_body_id_is_a_client_error_not_an_outage(api: Api) -> None:
    d = api
    occurrence_id = make_occurrence(d)
    response = create(
        d, occurrence_id, 0, document_revision_ref={"document_id": "a\u0000b", "revision_no": 1}
    )
    assert response.status_code == 400, response.text
    payload = response.json()
    assert payload["code"] == "INVALID_REQUEST" and payload["retryable"] is False
    assert payload["field_errors"] == [
        {"field": "document_revision_ref.document_id", "code": "INVALID_FORMAT"}
    ]
    assert plans(d, occurrence_id) == []


def test_a_nul_in_a_path_id_is_a_400_on_every_occurrence_route(api: Api) -> None:
    d = api
    occurrence_id = make_occurrence(d)
    who = headers(d.subjects["t1"])
    keyed = headers(d.subjects["t1"], "k-nul")
    nul = "a%00b"
    checks = [
        ("GET", f"/v1/lesson-occurrences/{nul}", None),
        ("GET", f"/v1/lesson-occurrences/{nul}/plan-revisions", None),
        ("GET", f"/v1/lesson-occurrences/{nul}/plan-revisions/1", None),
        ("GET", f"/v1/lesson-occurrences/{nul}/documents", None),
        ("GET", f"/v1/lesson-occurrences/{occurrence_id}/documents/{nul}", None),
        ("GET", f"/v1/lesson-occurrences/{occurrence_id}/documents/{nul}/revisions", None),
        ("GET", f"/v1/lesson-occurrences/{occurrence_id}/documents/{nul}/revisions/1", None),
        (
            "POST",
            f"/v1/lesson-occurrences/{nul}/plan-revisions",
            {"expected_head_revision_no": 0, **fields()},
        ),
        (
            "POST",
            f"/v1/lesson-occurrences/{nul}/plan-revisions/1/confirm",
            {"expected_plan_hash": "a" * 64},
        ),
        ("POST", f"/v1/lesson-occurrences/{nul}/documents", {"asset_ref": "upl_x"}),
        (
            "POST",
            f"/v1/lesson-occurrences/{occurrence_id}/documents/{nul}/revisions",
            {"extracted_text": "x", "expected_head_revision_no": 1},
        ),
    ]
    for method, url, body in checks:
        response = d.client.request(
            method, url, json=body, headers=keyed if method == "POST" else who
        )
        assert response.status_code == 400, (method, url, response.status_code, response.text)
        assert response.json()["code"] == "INVALID_REQUEST", url
        assert response.json()["retryable"] is False
