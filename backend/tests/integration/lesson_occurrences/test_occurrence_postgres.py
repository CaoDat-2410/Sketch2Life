"""FEAT-066 T-3a: lesson occurrence create and reads on PostgreSQL (SRS l.775, l.798, l.1652).

Runs only against a disposable database whose name contains ``be1_acceptance`` and
``frc08``. Principals are injected through the ``X-Test-Principal`` header (the verified
adult dependency is overridden); every identity, class and lesson row is synthetic.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from threading import Barrier
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest
from fastapi import FastAPI, Header
from fastapi.testclient import TestClient
from sqlalchemy import func, select, update

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.lesson_library.tables import (
    LIBRARY_ITEMS,
    LIBRARY_VERSIONS,
    UPLOAD_SESSIONS,
)
from sketch2life.infrastructure.lesson_occurrences.tables import OCCURRENCES
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    Be1CommandReceiptModel,
    ClassroomModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult

ISSUER = "synthetic-t3a-issuer"
HASH = "a1" * 32
STORAGE_WORDS = ("bucket", "object_key", "presigned", "amazonaws", "organization_ref")


@dataclass
class Directory:
    """Synthetic people, classes and lessons; ``subjects`` maps a label to a header value."""

    app: FastAPI
    client: TestClient
    token: str
    organization: str
    other_organization: str
    classes: dict[str, str] = field(default_factory=dict)
    subjects: dict[str, str] = field(default_factory=dict)
    accounts: dict[str, str] = field(default_factory=dict)
    lessons: dict[str, dict[str, str]] = field(default_factory=dict)

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


def _lesson(
    db: Any,
    organization: str,
    creator: str,
    *,
    visibility: str = "SCHOOL",
    review_state: str = "APPROVED",
    state: str = "ACTIVE",
    moderation: str = "VISIBLE",
) -> dict[str, str]:
    lesson_id, version_id = str(uuid4()), str(uuid4())
    content_hash = uuid4().hex + uuid4().hex
    db.execute(
        LIBRARY_ITEMS.insert().values(
            lesson_id=lesson_id,
            organization_id=organization,
            created_by=creator,
            state=state,
            visibility=visibility,
            internal_visibility="SCHOOL",
            moderation_state=moderation,
            current_version_id=None,
        )
    )
    db.execute(
        LIBRARY_VERSIONS.insert().values(
            version_id=version_id,
            lesson_id=lesson_id,
            version_no=3,
            content_json={"title": "Bài"},
            structured_content_hash=content_hash,
            review_state=review_state,
            authored_by=creator,
        )
    )
    return {"lesson_id": lesson_id, "version_id": version_id, "content_sha256": content_hash}


@pytest.fixture
def directory(monkeypatch: pytest.MonkeyPatch) -> Iterator[Directory]:
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
    organization, other = f"synthetic-t3a-org-{token}", f"synthetic-t3a-other-{token}"
    directory = Directory(app, TestClient(app), token, organization, other)
    label = lambda value: f"synthetic-t3a-{value}-{token}"  # noqa: E731
    with runtime.session_factory.begin() as db:
        for org in (organization, other):
            db.add(OrganizationModel(organization_id=org, display_name=org, state="active"))
        db.flush()
        for key, org, state in (
            ("a1", organization, "active"),
            ("a2", organization, "active"),
            ("archived", organization, "archived"),
            ("b1", other, "active"),
        ):
            class_id = f"class-{key}-{token}"
            directory.classes[key] = class_id
            db.add(
                ClassroomModel(
                    class_id=class_id,
                    organization_id=org,
                    display_name=key,
                    state=state,
                    created_by="synthetic",
                )
            )
        db.flush()
        people = (
            # label, role, organization, class key (None = organization-wide), assignment role
            ("t1", "teacher", organization, "a1", "teacher"),
            ("t4", "teacher", organization, "a1", "teacher"),  # a second teacher row on a1
            ("t2", "teacher", organization, "a2", "teacher"),
            ("t3", "teacher", organization, None, "teacher"),
            ("g1", "teacher", organization, "a1", "guide"),
            ("o1", "teacher", organization, "a1", "observer"),
            ("tarch", "teacher", organization, "archived", "teacher"),
            ("tother", "teacher", other, "b1", "teacher"),
            ("manager", "school_manager", organization, None, "school_admin"),
        )
        for key, role, org, class_key, assignment_role in people:
            subject = label(key)
            directory.subjects[key] = subject
            directory.accounts[key] = _identity(db, subject, role)
            _assign(
                db,
                org,
                subject,
                assignment_role,
                directory.classes[class_key] if class_key else None,
            )
        directory.subjects["inactive"] = label("inactive")
        directory.accounts["inactive"] = _identity(
            db, label("inactive"), "teacher", state="disabled"
        )
        _assign(db, organization, label("inactive"), "teacher", directory.classes["a1"])
        directory.subjects["revoked"] = label("revoked")
        directory.accounts["revoked"] = _identity(db, label("revoked"), "teacher")
        _assign(
            db, organization, label("revoked"), "teacher", directory.classes["a1"], active=False
        )
        directory.subjects["parent"] = label("parent")
        directory.accounts["parent"] = _identity(db, label("parent"), "parent")
        directory.subjects["stranger"] = label("stranger")  # no identity row at all
        creator = directory.subjects["t1"]
        directory.lessons["approved"] = _lesson(db, organization, creator)
        directory.lessons["draft"] = _lesson(db, organization, creator, review_state="DRAFT")
        directory.lessons["private_other"] = _lesson(
            db, organization, directory.subjects["t2"], visibility="PRIVATE"
        )
        directory.lessons["private_own"] = _lesson(db, organization, creator, visibility="PRIVATE")
        directory.lessons["hidden"] = _lesson(db, organization, creator, moderation="HIDDEN")
        directory.lessons["archived"] = _lesson(db, organization, creator, state="ARCHIVED")
        directory.lessons["other_org"] = _lesson(db, other, creator)

    async def verified(
        x_test_principal: str = Header(alias="X-Test-Principal"),
    ) -> VerifiedPrincipal:
        return VerifiedPrincipal(subject=x_test_principal, issuer=ISSUER, roles=frozenset())

    app.state.lesson_library_storage = SimpleNamespace()
    app.state.lesson_document_scanner = SimpleNamespace()
    app.dependency_overrides[get_verified_adult] = verified
    try:
        with directory.client:
            yield directory
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


def create(
    d: Directory, who: str, class_key: str = "a1", *, key: str | None = None, **fields: Any
) -> Any:
    body: dict[str, Any] = {"class_id": d.classes.get(class_key, class_key), "title": "Bài học vẽ"}
    body.update(fields)
    return d.client.post(
        "/v1/lesson-occurrences", json=body, headers=headers(d.subjects[who], key or uuid4().hex)
    )


def make(d: Directory, who: str = "t1", class_key: str = "a1", **fields: Any) -> dict[str, Any]:
    response = create(d, who, class_key, **fields)
    assert response.status_code == 201, response.text
    return response.json()  # type: ignore[no-any-return]


def get(d: Directory, who: str, occurrence_id: str, **extra: str) -> Any:
    return d.client.get(
        f"/v1/lesson-occurrences/{occurrence_id}", headers=headers(d.subjects[who], None, **extra)
    )


def listing(d: Directory, who: str, query: str) -> Any:
    return d.client.get(f"/v1/lesson-occurrences?{query}", headers=headers(d.subjects[who]))


def shape(response: Any) -> tuple[int, dict[str, Any]]:
    """Status and envelope without the per-request ids: what a caller can compare."""
    body = dict(response.json())
    body.pop("request_id", None)
    body.pop("correlation_id", None)
    return response.status_code, body


def row(d: Directory, occurrence_id: str) -> Any:
    with d.sessions()() as db:
        return (
            db.execute(select(OCCURRENCES).where(OCCURRENCES.c.occurrence_id == occurrence_id))
            .mappings()
            .one()
        )


def count_for(d: Directory, class_key: str) -> int:
    with d.sessions()() as db:
        return int(
            db.scalar(
                select(func.count())
                .select_from(OCCURRENCES)
                .where(OCCURRENCES.c.class_ref == d.classes[class_key])
            )
            or 0
        )


# ----------------------------------------------------------------------------- create
def test_the_assigned_teacher_creates_an_occurrence(directory: Directory) -> None:
    d = directory
    response = create(
        d, "t1", scheduled_date="2026-11-21", title="  Bài học vẽ con mèo  ", key="k-1"
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert response.headers["Location"] == f"/v1/lesson-occurrences/{body['occurrence_id']}"
    assert response.headers["ETag"] == '"1"'
    assert body["contract"] == "LessonOccurrenceV1"
    assert body["title"] == "Bài học vẽ con mèo" and body["scheduled_date"] == "2026-11-21"
    assert (body["state"], body["revision"]) == ("DRAFT", 1)
    assert body["class_id"] == d.classes["a1"]
    assert body["responsible_teacher_ref"] == d.accounts["t1"]
    assert body["lesson_version_ref"] is None and body["approved_plan"] is None
    assert body["sample_video"] == {"slot_state": "AVAILABLE", "claimed_at": None, "run_ref": None}
    stored = row(d, body["occurrence_id"])
    assert stored["organization_ref"] == d.organization
    assert stored["responsible_teacher_ref"] == stored["created_by"] == d.accounts["t1"]
    assert stored["scheduled_date"] == date(2026, 11, 21)
    text = json.dumps(body).lower()
    assert d.organization not in json.dumps(body)
    for word in STORAGE_WORDS:
        assert word not in text
    with d.sessions()() as db:
        audit = db.scalars(
            select(CoreAuditEntryModel).where(
                CoreAuditEntryModel.resource_id == body["occurrence_id"]
            )
        ).all()
        receipt = db.get(
            Be1CommandReceiptModel, (d.subjects["t1"], "POST /v1/lesson-occurrences", "k-1")
        )
    (entry,) = audit
    assert entry.action == "lesson.occurrence.create" and entry.actor_ref == d.accounts["t1"]
    assert entry.organization_id == d.organization and entry.decision == "allowed"
    assert receipt is not None and receipt.organization_id == d.organization
    assert "organization" not in json.dumps(receipt.response_json)
    assert get(d, "t1", body["occurrence_id"]).json() == body


def test_a_replay_returns_the_first_result_and_another_payload_is_refused(
    directory: Directory,
) -> None:
    d = directory
    first = create(d, "t1", key="replay-key", scheduled_date="2026-12-01")
    assert first.status_code == 201
    again = create(d, "t1", key="replay-key", scheduled_date="2026-12-01", title="  Bài học vẽ  ")
    assert again.status_code == 201 and again.json() == first.json()
    assert again.headers["Location"] == first.headers["Location"] and again.headers["ETag"] == '"1"'
    assert count_for(d, "a1") == 1
    changed = create(d, "t1", key="replay-key", scheduled_date="2026-12-02")
    assert changed.status_code == 400 and changed.json()["code"] == "INVALID_IDEMPOTENCY_KEY"
    assert create(d, "t1", key="replay-key", title="Khác").status_code == 400
    other_key = create(d, "t1", key="replay-key-2", scheduled_date="2026-12-01")
    assert other_key.status_code == 201
    assert other_key.json()["occurrence_id"] != first.json()["occurrence_id"]
    assert count_for(d, "a1") == 2
    # The key is per caller: another Teacher using it creates their own occurrence.
    assert create(d, "t2", "a2", key="replay-key").status_code == 201
    # A refusal writes no receipt, so a later repeat is a fresh attempt.
    assert create(d, "t2", "a1", key="refused-key").status_code == 409
    with d.sessions()() as db:
        assert (
            db.get(
                Be1CommandReceiptModel,
                (d.subjects["t2"], "POST /v1/lesson-occurrences", "refused-key"),
            )
            is None
        )


def test_a_replay_is_served_even_after_the_class_is_archived(directory: Directory) -> None:
    d = directory
    first = create(d, "t2", "a2", key="late-replay")
    assert first.status_code == 201
    with d.sessions().begin() as db:
        db.execute(
            update(ClassroomModel)
            .where(ClassroomModel.class_id == d.classes["a2"])
            .values(state="archived")
        )
    try:
        assert create(d, "t2", "a2", key="late-replay").json() == first.json()
        fresh = create(d, "t2", "a2", key="late-fresh")
        assert fresh.status_code == 409 and fresh.json()["code"] == "INVALID_STATE_TRANSITION"
    finally:
        with d.sessions().begin() as db:
            db.execute(
                update(ClassroomModel)
                .where(ClassroomModel.class_id == d.classes["a2"])
                .values(state="active")
            )


def test_concurrent_creates_with_one_key_make_one_occurrence(directory: Directory) -> None:
    d = directory
    barrier = Barrier(4)

    def attempt(_: int) -> Any:
        barrier.wait(timeout=20)
        return create(d, "t1", key="race-key", scheduled_date="2027-01-01")

    with ThreadPoolExecutor(max_workers=4) as pool:
        responses = list(pool.map(attempt, range(4)))
    assert {response.status_code for response in responses} == {201}
    assert len({response.json()["occurrence_id"] for response in responses}) == 1
    with d.sessions()() as db:
        assert (
            db.scalar(
                select(func.count())
                .select_from(OCCURRENCES)
                .where(
                    OCCURRENCES.c.scheduled_date == date(2027, 1, 1),
                    OCCURRENCES.c.class_ref == d.classes["a1"],
                )
            )
            == 1
        )


# ----------------------------------------------------------------------------- scope table
def test_the_teacher_assignment_decision_table(directory: Directory) -> None:
    d = directory
    unknown = create(d, "t1", "no-such-class")
    assert unknown.status_code == 404 and unknown.json()["code"] == "RESOURCE_NOT_FOUND"
    cases = {
        # in the organization, no teacher row for this class: the 409 branch is reachable
        "t2": (409, "TEACHER_ASSIGNMENT_REQUIRED"),
        "t3": (409, "TEACHER_ASSIGNMENT_REQUIRED"),  # an organization-wide row assigns no class
        "tarch": (409, "TEACHER_ASSIGNMENT_REQUIRED"),
        # in scope by a guide or observer row of this class only
        "g1": (403, "ACTION_NOT_ALLOWED"),
        "o1": (403, "ACTION_NOT_ALLOWED"),
        # everything else is the uniform 404, the same body as an unknown class
        "tother": (404, "RESOURCE_NOT_FOUND"),
        "inactive": (404, "RESOURCE_NOT_FOUND"),
        "revoked": (404, "RESOURCE_NOT_FOUND"),
        "manager": (404, "RESOURCE_NOT_FOUND"),
        "parent": (404, "RESOURCE_NOT_FOUND"),
        "stranger": (404, "RESOURCE_NOT_FOUND"),
    }
    for who, (status, code) in cases.items():
        response = create(d, who)
        assert (response.status_code, response.json()["code"]) == (status, code), who
        if status == 404:
            assert shape(response) == shape(unknown), who
    assert count_for(d, "a1") == 0
    # A Teacher of the class creates; the same Teacher is refused on a class of another row.
    assert create(d, "t1").status_code == 201
    assert create(d, "t1", "a2").status_code == 409
    assert create(d, "t4").status_code == 201  # a second teacher row of the class also qualifies
    assert create(d, "t3", "a2").status_code == 409
    # The caller's organization is the class's organization: an id of another organization is a
    # stranger's 404 whatever role the caller holds elsewhere.
    assert shape(create(d, "t1", "b1")) == shape(unknown)
    assert create(d, "tother", "b1").status_code == 201


def test_an_archived_class_refuses_with_a_state_conflict_after_the_scope_check(
    directory: Directory,
) -> None:
    d = directory
    refused = create(d, "tarch", "archived")
    assert refused.status_code == 409 and refused.json()["code"] == "INVALID_STATE_TRANSITION"
    assert count_for(d, "archived") == 0
    assert create(d, "t1", "archived").status_code == 409
    assert create(d, "t1", "archived").json()["code"] == "TEACHER_ASSIGNMENT_REQUIRED"


def test_request_validation_never_reaches_the_database(directory: Directory) -> None:
    d = directory
    base = headers(d.subjects["t1"], "bad-body")
    for body in (
        {"class_id": d.classes["a1"], "title": "x", "organization_id": d.organization},
        {"class_id": d.classes["a1"], "title": "x", "responsible_teacher_ref": "someone"},
        {"class_id": d.classes["a1"], "title": "x", "scheduled_date": "not-a-date"},
        {"class_id": d.classes["a1"], "title": "   "},
        {"class_id": d.classes["a1"]},
        {"title": "x"},
    ):
        response = d.client.post("/v1/lesson-occurrences", json=body, headers=base)
        assert response.status_code == 400, body
        assert response.json()["code"] == "INVALID_REQUEST" and response.json()["field_errors"]
    missing = d.client.post(
        "/v1/lesson-occurrences",
        json={"class_id": "c", "title": "x"},
        headers=headers(d.subjects["t1"]),
    )
    assert missing.status_code == 400
    assert {"field": "Idempotency-Key", "code": "REQUIRED"} in missing.json()["field_errors"]
    assert count_for(d, "a1") == 0


# ----------------------------------------------------------------------------- lesson pin
def test_an_exact_lesson_pin_is_stored_and_never_resolved_by_latest(directory: Directory) -> None:
    d = directory
    ref = d.lessons["approved"]
    body = make(d, lesson_version_ref=ref)
    assert body["lesson_version_ref"] == ref and body["lesson_version_no"] == 3
    stored = row(d, body["occurrence_id"])
    assert (
        stored["source_lesson_id"],
        stored["source_lesson_version_id"],
        stored["source_lesson_version_hash"],
        stored["source_lesson_version_no"],
    ) == (ref["lesson_id"], ref["version_id"], ref["content_sha256"], 3)
    assert get(d, "t1", body["occurrence_id"]).json()["lesson_version_ref"] == ref
    own = make(d, lesson_version_ref=d.lessons["private_own"])
    assert own["lesson_version_ref"]["lesson_id"] == d.lessons["private_own"]["lesson_id"]


def test_the_lesson_pin_is_fail_closed(directory: Directory) -> None:
    d = directory
    approved = d.lessons["approved"]
    wrong_hash = {**approved, "content_sha256": "b" * 64}
    wrong_pair = {**approved, "version_id": d.lessons["draft"]["version_id"]}
    cases = (
        (wrong_hash, 409, "STALE_REVISION"),
        (d.lessons["draft"], 409, "INVALID_STATE_TRANSITION"),
        (d.lessons["private_other"], 404, "RESOURCE_NOT_FOUND"),
        (d.lessons["hidden"], 404, "RESOURCE_NOT_FOUND"),
        (d.lessons["archived"], 404, "RESOURCE_NOT_FOUND"),
        (d.lessons["other_org"], 404, "RESOURCE_NOT_FOUND"),
        (wrong_pair, 404, "RESOURCE_NOT_FOUND"),
        (
            {"lesson_id": "unknown", "version_id": "unknown", "content_sha256": HASH},
            404,
            "RESOURCE_NOT_FOUND",
        ),
        (
            {"lesson_id": "x" * 200, "version_id": "y" * 200, "content_sha256": HASH},
            404,
            "RESOURCE_NOT_FOUND",
        ),
    )
    for ref, status, code in cases:
        response = create(d, "t1", lesson_version_ref=ref)
        assert (response.status_code, response.json()["code"]) == (status, code), ref
    assert count_for(d, "a1") == 0
    # The same lesson of another organization is unreachable for a Teacher of that organization too.
    assert create(d, "tother", "b1", lesson_version_ref=approved).status_code == 404
    # A replay of a pinned create does not re-run the pin check or move the pin.
    first = create(d, "t1", key="pin-key", lesson_version_ref=approved)
    assert first.status_code == 201
    with d.sessions().begin() as db:
        db.execute(
            update(LIBRARY_ITEMS)
            .where(LIBRARY_ITEMS.c.lesson_id == approved["lesson_id"])
            .values(moderation_state="HIDDEN")
        )
    try:
        assert create(d, "t1", key="pin-key", lesson_version_ref=approved).json() == first.json()
        assert create(d, "t1", lesson_version_ref=approved).status_code == 404
    finally:
        with d.sessions().begin() as db:
            db.execute(
                update(LIBRARY_ITEMS)
                .where(LIBRARY_ITEMS.c.lesson_id == approved["lesson_id"])
                .values(moderation_state="VISIBLE")
            )


# ----------------------------------------------------------------------------- reads
def test_reads_follow_the_current_assignment_and_the_uniform_404(directory: Directory) -> None:
    d = directory
    occurrence = make(d)
    occurrence_id = occurrence["occurrence_id"]
    unknown = get(d, "t1", str(uuid4()))
    assert unknown.status_code == 404 and unknown.json()["code"] == "RESOURCE_NOT_FOUND"
    for who in ("t1", "t4", "g1", "o1", "t3"):  # covering rows, any teacher-family role
        response = get(d, who, occurrence_id)
        assert response.status_code == 200, who
        assert response.json() == occurrence
    for who in ("t2", "tother", "inactive", "revoked", "manager", "parent", "stranger"):
        denied = get(d, who, occurrence_id)
        assert shape(denied) == shape(unknown), who
    assert shape(get(d, "t1", "x" * 37)) == shape(unknown)
    # Revoking the assignment ends access at once (current assignment, not the creator).
    with d.sessions().begin() as db:
        db.execute(
            update(OrganizationAssignmentModel)
            .where(OrganizationAssignmentModel.subject == d.subjects["g1"])
            .values(active=False)
        )
    try:
        assert shape(get(d, "g1", occurrence_id)) == shape(unknown)
    finally:
        with d.sessions().begin() as db:
            db.execute(
                update(OrganizationAssignmentModel)
                .where(OrganizationAssignmentModel.subject == d.subjects["g1"])
                .values(active=True)
            )
    assert get(d, "g1", occurrence_id).status_code == 200


def test_the_strong_etag_changes_with_the_revision_and_gives_304(directory: Directory) -> None:
    d = directory
    occurrence_id = make(d)["occurrence_id"]
    first = get(d, "t1", occurrence_id)
    assert first.headers["ETag"] == '"1"' and first.headers["Cache-Control"] == "private, no-cache"
    unchanged = get(d, "t1", occurrence_id, **{"If-None-Match": '"1"'})
    assert unchanged.status_code == 304 and unchanged.content == b""
    # A stranger never gets a 304: it is answered only after authorisation.
    assert get(d, "t2", occurrence_id, **{"If-None-Match": '"1"'}).status_code == 404
    with d.sessions().begin() as db:
        db.execute(
            update(OCCURRENCES)
            .where(OCCURRENCES.c.occurrence_id == occurrence_id)
            .values(revision=2, state="ARCHIVED")
        )
    moved = get(d, "t1", occurrence_id, **{"If-None-Match": '"1"'})
    assert moved.status_code == 200 and moved.headers["ETag"] == '"2"'
    assert moved.json()["state"] == "ARCHIVED" and moved.json()["revision"] == 2
    assert get(d, "t1", occurrence_id, **{"If-None-Match": '"2"'}).status_code == 304


# ----------------------------------------------------------------------------- list
def test_the_class_list_pages_stably_newest_first(directory: Directory) -> None:
    d = directory
    ids = [make(d, "t2", "a2", title=f"Bài {index}")["occurrence_id"] for index in range(7)]
    other = make(d, "t1", "a1")["occurrence_id"]
    # Rows sharing one timestamp must still page without a gap or a repeat.
    tied = datetime.now(UTC) + timedelta(hours=1)
    ties = [f"tie-{d.token}-{index}" for index in range(5)]
    with d.sessions().begin() as db:
        for occurrence_id in ties:
            db.execute(
                OCCURRENCES.insert().values(
                    occurrence_id=occurrence_id,
                    organization_ref=d.organization,
                    class_ref=d.classes["a2"],
                    responsible_teacher_ref=d.accounts["t2"],
                    created_by=d.accounts["t2"],
                    title="Cùng giờ",
                    created_at=tied,
                    updated_at=tied,
                )
            )
    expected = sorted(ties, reverse=True) + list(reversed(ids))
    seen: list[str] = []
    cursor: str | None = None
    for _ in range(10):
        query = f"class_id={d.classes['a2']}&limit=4" + (f"&cursor={cursor}" if cursor else "")
        page = listing(d, "t2", query)
        assert page.status_code == 200, page.text
        body = page.json()
        assert body["contract"] == "LessonOccurrencePageV1" and "ETag" not in page.headers
        seen.extend(item["occurrence_id"] for item in body["items"])
        cursor = body["next_cursor"]
        if cursor is None:
            break
    assert seen == expected and other not in seen
    # A newer row inserted between two pages sorts before the issued cursor, so it neither
    # shifts nor repeats a row of the next page; an older insert would appear after the cursor.
    first = listing(d, "t2", f"class_id={d.classes['a2']}&limit=3").json()
    newest = datetime.now(UTC) + timedelta(hours=2)
    with d.sessions().begin() as db:
        db.execute(
            OCCURRENCES.insert().values(
                occurrence_id=f"tie-{d.token}-new",
                organization_ref=d.organization,
                class_ref=d.classes["a2"],
                responsible_teacher_ref=d.accounts["t2"],
                created_by=d.accounts["t2"],
                title="Mới nhất",
                created_at=newest,
                updated_at=newest,
            )
        )
    second = listing(
        d, "t2", f"class_id={d.classes['a2']}&limit=3&cursor={first['next_cursor']}"
    ).json()
    assert [item["occurrence_id"] for item in first["items"] + second["items"]] == expected[:6]
    fresh = listing(d, "t2", f"class_id={d.classes['a2']}&limit=1").json()["items"]
    assert fresh[0]["occurrence_id"] == f"tie-{d.token}-new"


def test_list_filters_limits_and_scope(directory: Directory) -> None:
    d = directory
    mine = make(d, "t1", "a1")
    archived = make(d, "t1", "a1")
    with d.sessions().begin() as db:
        db.execute(
            update(OCCURRENCES)
            .where(OCCURRENCES.c.occurrence_id == archived["occurrence_id"])
            .values(state="ARCHIVED")
        )
    both = listing(d, "t1", f"class_id={d.classes['a1']}").json()["items"]
    assert {item["occurrence_id"] for item in both} == {
        mine["occurrence_id"],
        archived["occurrence_id"],
    }
    planning = listing(d, "t1", f"class_id={d.classes['a1']}&state=DRAFT").json()["items"]
    assert [item["occurrence_id"] for item in planning] == [mine["occurrence_id"]]
    assert listing(d, "t1", f"class_id={d.classes['a1']}&limit=100").status_code == 200
    for query, bad_field in (
        (f"class_id={d.classes['a1']}&limit=101", "limit"),
        (f"class_id={d.classes['a1']}&limit=0", "limit"),
        (f"class_id={d.classes['a1']}&cursor=not-a-cursor", "cursor"),
        (f"class_id={d.classes['a1']}&state=DONE", "state"),
        ("limit=5", "class_id"),
    ):
        bad = listing(d, "t1", query)
        assert bad.status_code == 400, query
        assert any(item["field"] == bad_field for item in bad.json()["field_errors"]), query
    unknown = listing(d, "t1", "class_id=no-such-class")
    assert unknown.status_code == 404
    for who in ("t2", "tother", "inactive", "revoked", "manager", "parent", "stranger"):
        assert shape(listing(d, who, f"class_id={d.classes['a1']}")) == shape(unknown), who
    for who in ("g1", "o1", "t3", "t4"):
        assert listing(d, who, f"class_id={d.classes['a1']}").status_code == 200, who
    other_org = listing(d, "t1", f"class_id={d.classes['b1']}")
    assert shape(other_org) == shape(unknown)


# ----------------------------------------------------------------------------- upload carrier
def create_upload(d: Directory, who: str, occurrence_id: str) -> Any:
    data = b"%PDF-1.4 synthetic"
    return d.client.post(
        "/v1/upload-sessions",
        json={
            "purpose": "OCCURRENCE_DOCUMENT",
            "target_ref": occurrence_id,
            "media_type": "application/pdf",
            "expected_size_bytes": len(data),
            "expected_sha256": hashlib.sha256(data).hexdigest(),
            "file_name": "giao-an.pdf",
        },
        headers=headers(d.subjects[who], uuid4().hex),
    )


def test_the_occurrence_upload_target_resolver_is_registered(directory: Directory) -> None:
    d = directory
    occurrence_id = make(d)["occurrence_id"]
    created = create_upload(d, "t1", occurrence_id)
    assert created.status_code == 201, created.text
    with d.sessions()() as db:
        session = (
            db.execute(
                select(UPLOAD_SESSIONS).where(
                    UPLOAD_SESSIONS.c.upload_session_id == created.json()["upload_id"]
                )
            )
            .mappings()
            .one()
        )
    assert session["purpose"] == "OCCURRENCE_DOCUMENT" and session["target_ref"] == occurrence_id
    assert session["organization_id"] == d.organization
    assert session["owner_scope_kind"] == "ORGANIZATION"
    # Read-only roles, other Teachers (also a second Teacher of the class who is not the
    # responsible one), other organizations and unknown ids all get the uniform 404.
    unknown = create_upload(d, "t1", str(uuid4()))
    assert unknown.status_code == 404
    for who in ("g1", "o1", "t4", "t2", "tother", "manager", "parent", "inactive", "revoked"):
        assert shape(create_upload(d, who, occurrence_id)) == shape(unknown), who
    with d.sessions().begin() as db:
        db.execute(
            update(OCCURRENCES)
            .where(OCCURRENCES.c.occurrence_id == occurrence_id)
            .values(state="ARCHIVED")
        )
    archived = create_upload(d, "t1", occurrence_id)
    assert archived.status_code == 409 and archived.json()["code"] == "INVALID_STATE_TRANSITION"
