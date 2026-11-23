"""FEAT-066 T-3c: the Teacher text edit as its own immutable revision, on PostgreSQL.

SRS l.546 (the original file and every earlier text revision stay, the edit is a new immutable
revision), l.1437, l.1696-1699 (keys, revisions, stale fence), l.864-865 (scope). Runs only
against a disposable database whose name contains ``be1_acceptance`` and ``frc08``. Principals
are injected through the ``X-Test-Principal`` header; every identity, class, occurrence,
document and text is synthetic. Documents are written straight into the DDL-A tables (the same
rows the T-3b attach writes: one source document and its extraction revision 1), because the
edit never touches storage, the scanner or the parser.
"""

from __future__ import annotations

import hashlib
import os
import time
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import Barrier
from typing import Any
from uuid import uuid4

import pytest
from fastapi import FastAPI, Header
from fastapi.testclient import TestClient
from sqlalchemy import select, text, update
from sqlalchemy.exc import DBAPIError

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.lesson_occurrences.tables import (
    DOCUMENT_REVISIONS,
    OCCURRENCES,
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
    MAX_REVISION_EDIT_BODY_BYTES,
)

ISSUER = "synthetic-t3c-issuer"
HEX = "a" * 64
TWO_MIB = 2 * 1024 * 1024
LEAK_WORDS = ("bucket", "object_key", "presigned", "amazonaws", "organization_ref", "scanner")
FIRST_TEXT = "Tiêu đề: Vẽ con mèo\nMục tiêu: Nhận biết hình dạng con mèo"


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
    organization, other = f"synthetic-t3c-org-{token}", f"synthetic-t3c-other-{token}"
    d = Api(app, TestClient(app), token, organization, other)

    def label(value: str) -> str:
        return f"synthetic-t3c-{value}-{token}"

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


def make_occurrence(d: Api, who: str = "t1", class_key: str = "a1") -> str:
    response = d.client.post(
        "/v1/lesson-occurrences",
        json={"class_id": d.classes[class_key], "title": "Bài học vẽ"},
        headers=headers(d.subjects[who], uuid4().hex),
    )
    assert response.status_code == 201, response.text
    return str(response.json()["occurrence_id"])


@dataclass
class Doc:
    occurrence_id: str
    document_id: str
    revision_1_id: str

    @property
    def url(self) -> str:
        return f"/v1/lesson-occurrences/{self.occurrence_id}/documents/{self.document_id}"

    @property
    def edit_url(self) -> str:
        return self.url + "/revisions"


def make_document(d: Api, occurrence_id: str, first_text: str = FIRST_TEXT) -> Doc:
    """One source document and its extraction revision 1, as the T-3b attach writes them."""
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
                parser_name="t3c-synthetic",
                parser_version="1",
                extraction_warnings=["MISSING_FIELD_TOPIC"],
                page_coverage=[1, 2, 3],
                created_by=account,
            )
        )
    return Doc(occurrence_id, document_id, revision_id)


def edit(
    d: Api,
    doc: Doc,
    text_value: str,
    head: int,
    *,
    who: str = "t1",
    key: str | None = None,
    **extra: Any,
) -> Any:
    return d.client.post(
        doc.edit_url,
        json={"extracted_text": text_value, "expected_head_revision_no": head, **extra},
        headers=headers(d.subjects[who], key or uuid4().hex),
    )


def revisions(d: Api, document_id: str) -> list[Any]:
    with d.sessions()() as db:
        return list(
            db.execute(
                select(DOCUMENT_REVISIONS)
                .where(DOCUMENT_REVISIONS.c.source_document_id == document_id)
                .order_by(DOCUMENT_REVISIONS.c.revision_no)
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


def receipts(d: Api, doc: Doc) -> list[Any]:
    with d.sessions()() as db:
        return list(
            db.execute(
                text(
                    "SELECT principal_ref, operation_scope, idempotency_key, request_fingerprint,"
                    " response_json FROM be1_command_receipts WHERE operation_scope = :scope"
                ),
                {
                    "scope": "POST /v1/lesson-occurrences/"
                    f"{doc.occurrence_id}/documents/{doc.document_id}/revisions"
                },
            )
            .mappings()
            .all()
        )


def audits(d: Api, doc: Doc) -> list[Any]:
    with d.sessions()() as db:
        return list(
            db.execute(
                text(
                    "SELECT actor_ref, action, resource_type, resource_id, organization_id"
                    " FROM core_audit_entries WHERE action = 'lesson.document_revision.create'"
                    " AND resource_id IN (SELECT document_revision_id FROM"
                    " lesson.document_revisions WHERE source_document_id = :doc)"
                ),
                {"doc": doc.document_id},
            )
            .mappings()
            .all()
        )


def snapshot(d: Api, doc: Doc) -> list[tuple[Any, ...]]:
    """Every column of every revision of the document, for byte-for-byte comparison."""
    return [tuple(row.values()) for row in revisions(d, doc.document_id)]


def unlocked(d: Api, doc: Doc) -> bool:
    """True when no request leaves a row lock on the document or the occurrence behind."""
    with d.engine.connect() as conn:
        try:
            conn.execute(
                text(
                    "SELECT 1 FROM lesson.source_documents WHERE source_document_id = :id"
                    " FOR UPDATE NOWAIT"
                ),
                {"id": doc.document_id},
            )
            conn.execute(
                text(
                    "SELECT 1 FROM lesson.occurrences WHERE occurrence_id = :id FOR UPDATE NOWAIT"
                ),
                {"id": doc.occurrence_id},
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


def new_doc(d: Api) -> Doc:
    return make_document(d, make_occurrence(d))


# ----------------------------------------------------------------------------- happy path
def test_an_edit_is_a_new_immutable_revision_and_leaves_the_extraction_untouched(api: Api) -> None:
    d = api
    doc = new_doc(d)
    before = snapshot(d, doc)
    occurrence_before = occurrence_row(d, doc.occurrence_id)
    edited = "Tiêu đề: Vẽ con mèo (đã sửa)\nBước 1: vẽ đầu tròn"
    response = edit(d, doc, edited, 1, key="k-happy")
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["contract"] == "LessonDocumentRevisionV2"
    assert body["revision_no"] == 2 and body["origin"] == "TEACHER_EDIT"
    assert body["base_revision_no"] == 1 and body["review_state"] == "NEEDS_REVIEW"
    assert body["extracted_text"] == edited and body["text_hash"] == sha(edited)
    assert body["text_length"] == len(edited)
    assert body["parser"] is None and body["warnings"] == [] and body["page_coverage"] == []
    assert body["source_document_id"] == doc.document_id
    assert response.headers["Location"] == f"{doc.edit_url}/2"
    assert response.headers["ETag"] == f'"{sha(edited)}.NEEDS_REVIEW"'
    # revision 1 is byte-identical afterwards (every column), the file row is untouched
    after = snapshot(d, doc)
    assert after[0] == before[0] and len(after) == 2
    stored = revisions(d, doc.document_id)[1]
    assert stored["origin"] == "TEACHER_EDIT" and stored["base_revision_no"] == 1
    assert stored["parser_name"] is None and stored["parser_version"] is None
    assert stored["extraction_warnings"] == [] and stored["page_coverage"] == []
    assert stored["review_state"] == "NEEDS_REVIEW" and stored["reviewed_by"] is None
    assert stored["created_by"] == d.accounts["t1"]
    assert stored["extracted_text"] == edited and stored["extracted_text_hash"] == sha(edited)
    # the occurrence is not changed by a text edit (no state change, no revision bump)
    occurrence_after = occurrence_row(d, doc.occurrence_id)
    for column in ("state", "revision", "updated_at", "approved_plan_revision_id"):
        assert occurrence_after[column] == occurrence_before[column]
    assert unlocked(d, doc) and idle_in_transaction(d) == 0


def test_the_new_revision_is_readable_through_the_t3b_reads(api: Api) -> None:
    d = api
    doc = new_doc(d)
    edited = "Văn bản đã sửa"
    created = edit(d, doc, edited, 1)
    assert created.status_code == 201
    head = d.client.get(doc.url, headers=headers(d.subjects["t1"]))
    assert head.status_code == 200 and head.headers["ETag"] == '"2"'
    assert head.json()["head_revision_no"] == 2
    # warnings and coverage of the file row stay those of the extraction (revision 1)
    assert head.json()["warnings"] == ["MISSING_FIELD_TOPIC"]
    read = d.client.get(doc.edit_url + "/2", headers=headers(d.subjects["t4"]))
    assert read.status_code == 200
    assert read.headers["ETag"] == created.headers["ETag"]
    assert read.json() == created.json()
    listing = d.client.get(doc.edit_url, headers=headers(d.subjects["g1"])).json()
    assert [(i["revision_no"], i["origin"]) for i in listing["items"]] == [
        (2, "TEACHER_EDIT"),
        (1, "EXTRACTION"),
    ]
    assert "extracted_text" not in str(listing)


def test_edits_chain_and_each_names_its_base(api: Api) -> None:
    d = api
    doc = new_doc(d)
    assert edit(d, doc, "bản hai", 1).status_code == 201
    third = edit(d, doc, "bản ba", 2)
    assert third.status_code == 201
    assert third.json()["revision_no"] == 3 and third.json()["base_revision_no"] == 2
    fourth = edit(d, doc, "bản bốn", 3)
    assert fourth.json()["revision_no"] == 4 and fourth.json()["base_revision_no"] == 3
    rows = revisions(d, doc.document_id)
    assert [r["revision_no"] for r in rows] == [1, 2, 3, 4]
    assert [r["extracted_text"] for r in rows[1:]] == ["bản hai", "bản ba", "bản bốn"]
    assert rows[0]["extracted_text"] == FIRST_TEXT  # the extraction is still revision 1


def test_the_text_is_stored_exactly_as_sent(api: Api) -> None:
    d = api
    doc = new_doc(d)
    exact = "  Dòng 1\r\nDòng 2\t\u0001 \n\n  Dòng cuối có khoảng trắng  \n"
    response = edit(d, doc, exact, 1)
    assert response.status_code == 201, response.text
    row = revisions(d, doc.document_id)[1]
    assert row["extracted_text"] == exact and row["extracted_text_hash"] == sha(exact)
    assert response.json()["extracted_text"] == exact
    assert response.json()["text_length"] == len(exact)
    # only the line endings differ: a real edit, not a no-op
    crlf_vs_lf = edit(d, doc, exact.replace("\r\n", "\n"), 2)
    assert crlf_vs_lf.status_code == 201 and crlf_vs_lf.json()["revision_no"] == 3
    trailing = edit(d, doc, exact.replace("\r\n", "\n") + " ", 3)
    assert trailing.status_code == 201 and trailing.json()["revision_no"] == 4


def test_a_text_of_exactly_two_mib_of_utf8_bytes_is_accepted(api: Api) -> None:
    d = api
    doc = new_doc(d)
    big = "é" * (TWO_MIB // 2)
    assert len(big.encode()) == TWO_MIB
    response = edit(d, doc, big, 1)
    assert response.status_code == 201, response.text[:200]
    assert response.json()["text_length"] == TWO_MIB // 2
    with d.sessions()() as db:
        size = db.execute(
            text(
                "SELECT octet_length(extracted_text) FROM lesson.document_revisions"
                " WHERE source_document_id = :d AND revision_no = 2"
            ),
            {"d": doc.document_id},
        ).scalar_one()
    assert size == TWO_MIB
    again = d.client.get(doc.edit_url + "/2", headers=headers(d.subjects["t1"]))
    assert again.status_code == 200 and again.json()["extracted_text"] == big


def test_a_confirmed_head_does_not_block_the_next_edit_which_starts_pending(api: Api) -> None:
    d = api
    doc = new_doc(d)
    with d.sessions().begin() as db:
        db.execute(
            update(DOCUMENT_REVISIONS)
            .where(DOCUMENT_REVISIONS.c.document_revision_id == doc.revision_1_id)
            .values(
                review_state="CONFIRMED",
                reviewed_by=d.accounts["t1"],
                reviewed_at=datetime.now(UTC),
            )
        )
    response = edit(d, doc, "sau khi đã duyệt", 1)
    assert response.status_code == 201 and response.json()["review_state"] == "NEEDS_REVIEW"
    rows = revisions(d, doc.document_id)
    assert rows[0]["review_state"] == "CONFIRMED" and rows[1]["review_state"] == "NEEDS_REVIEW"


# ----------------------------------------------------------------------------- stale fence
def test_a_stale_head_is_409_with_the_current_version_and_changes_nothing(api: Api) -> None:
    d = api
    doc = new_doc(d)
    assert edit(d, doc, "bản hai", 1).status_code == 201
    before = snapshot(d, doc)
    receipts_before = len(receipts(d, doc))
    stale = edit(d, doc, "bản ba từ nền cũ", 1, key="k-stale")
    assert stale.status_code == 409
    body = stale.json()
    assert body["code"] == "STALE_REVISION" and body["message"]
    assert body["current_version"] == 2 and type(body["current_version"]) is int
    assert stale.headers["ETag"] == '"2"'
    ahead = edit(d, doc, "bản ba từ tương lai", 9)
    assert ahead.status_code == 409 and ahead.json()["current_version"] == 2
    assert snapshot(d, doc) == before  # the head is unchanged and nothing was forked
    assert len(receipts(d, doc)) == receipts_before  # a refusal writes no receipt
    assert unlocked(d, doc) and idle_in_transaction(d) == 0
    # the client reloads the head and the same key then works from the new head
    retry = edit(d, doc, "bản ba từ nền cũ", 2, key="k-stale")
    assert retry.status_code == 201 and retry.json()["revision_no"] == 3


def test_two_concurrent_edits_from_one_head_make_exactly_one_revision(api: Api) -> None:
    d = api
    doc = new_doc(d)
    barrier = Barrier(2)

    def attempt(label: str) -> tuple[int, dict[str, Any]]:
        barrier.wait()
        return shape(edit(d, doc, f"bản của {label}", 1, key=f"k-{label}"))

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt, ("one", "two")))
    statuses = sorted(status for status, _ in results)
    assert statuses == [201, 409], results
    loser = next(body for status, body in results if status == 409)
    assert loser["code"] == "STALE_REVISION" and loser["current_version"] == 2
    rows = revisions(d, doc.document_id)
    assert [r["revision_no"] for r in rows] == [1, 2]  # no gap, no fork
    assert unlocked(d, doc) and idle_in_transaction(d) == 0


def test_many_concurrent_edits_leave_contiguous_numbers(api: Api) -> None:
    d = api
    doc = new_doc(d)
    workers = 6
    barrier = Barrier(workers)

    def attempt(index: int) -> int:
        barrier.wait()
        return int(edit(d, doc, f"bản {index}", 1, key=f"k-many-{index}").status_code)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        statuses = list(pool.map(attempt, range(workers)))
    assert sorted(statuses) == [201] + [409] * (workers - 1)
    assert [r["revision_no"] for r in revisions(d, doc.document_id)] == [1, 2]


def test_two_concurrent_requests_with_one_key_make_one_revision(api: Api) -> None:
    d = api
    doc = new_doc(d)
    barrier = Barrier(2)

    def attempt(_: int) -> tuple[int, dict[str, Any]]:
        barrier.wait()
        return shape(edit(d, doc, "cùng một khóa", 1, key="k-twin"))

    with ThreadPoolExecutor(max_workers=2) as pool:
        first, second = list(pool.map(attempt, range(2)))
    assert first == second and first[0] == 201
    assert [r["revision_no"] for r in revisions(d, doc.document_id)] == [1, 2]
    assert len(receipts(d, doc)) == 1 and len(audits(d, doc)) == 1


# ----------------------------------------------------------------------------- idempotency
def test_a_replay_returns_the_first_answer_and_writes_nothing(api: Api) -> None:
    d = api
    doc = new_doc(d)
    first = edit(d, doc, "bản đầu tiên", 1, key="k-replay")
    assert first.status_code == 201
    before = snapshot(d, doc)
    replay = edit(d, doc, "bản đầu tiên", 1, key="k-replay")
    assert shape(replay) == shape(first)
    assert replay.headers["ETag"] == first.headers["ETag"]
    assert replay.headers["Location"] == first.headers["Location"]
    assert snapshot(d, doc) == before
    assert len(receipts(d, doc)) == 1 and len(audits(d, doc)) == 1
    stored = receipts(d, doc)[0]["response_json"]
    assert set(stored) == {"status_code", "document_revision_id", "revision_no", "review_state"}
    assert "bản đầu tiên" not in str(stored)  # references only, never the text


def test_a_replay_after_a_later_edit_still_returns_the_original_revision(api: Api) -> None:
    d = api
    doc = new_doc(d)
    first = edit(d, doc, "bản hai", 1, key="k-old")
    assert edit(d, doc, "bản ba", 2).status_code == 201
    replay = edit(d, doc, "bản hai", 1, key="k-old")  # the fence is stale now, the receipt wins
    assert replay.status_code == 201 and shape(replay) == shape(first)
    assert replay.json()["revision_no"] == 2
    assert [r["revision_no"] for r in revisions(d, doc.document_id)] == [1, 2, 3]


def test_a_replay_after_the_revision_was_confirmed_is_still_the_first_answer(api: Api) -> None:
    d = api
    doc = new_doc(d)
    first = edit(d, doc, "bản sẽ được duyệt", 1, key="k-confirm")
    revision_id = revisions(d, doc.document_id)[1]["document_revision_id"]
    with d.sessions().begin() as db:  # what T-3d does when a plan that pins it is confirmed
        db.execute(
            update(DOCUMENT_REVISIONS)
            .where(DOCUMENT_REVISIONS.c.document_revision_id == revision_id)
            .values(
                review_state="CONFIRMED",
                reviewed_by=d.accounts["t1"],
                reviewed_at=datetime.now(UTC),
            )
        )
    replay = edit(d, doc, "bản sẽ được duyệt", 1, key="k-confirm")
    assert shape(replay) == shape(first)
    assert replay.json()["review_state"] == "NEEDS_REVIEW"
    assert replay.headers["ETag"] == first.headers["ETag"]
    live = d.client.get(doc.edit_url + "/2", headers=headers(d.subjects["t1"]))
    assert live.json()["review_state"] == "CONFIRMED"
    assert live.headers["ETag"] == f'"{sha("bản sẽ được duyệt")}.CONFIRMED"'


def test_the_same_key_with_another_payload_is_400(api: Api) -> None:
    d = api
    doc = new_doc(d)
    assert edit(d, doc, "bản hai", 1, key="k-mismatch").status_code == 201
    other_text = edit(d, doc, "bản khác", 1, key="k-mismatch")
    assert other_text.status_code == 400
    assert other_text.json()["code"] == "INVALID_IDEMPOTENCY_KEY"
    other_head = edit(d, doc, "bản hai", 2, key="k-mismatch")
    assert other_head.status_code == 400
    assert other_head.json()["code"] == "INVALID_IDEMPOTENCY_KEY"
    assert [r["revision_no"] for r in revisions(d, doc.document_id)] == [1, 2]


def test_keys_are_per_caller_and_per_document(api: Api) -> None:
    d = api
    first, second = new_doc(d), new_doc(d)
    assert edit(d, first, "bản hai", 1, key="k-shared").status_code == 201
    # the same key on another document is a different command
    other_doc = edit(d, second, "bản hai", 1, key="k-shared")
    assert other_doc.status_code == 201
    assert other_doc.json()["source_document_id"] == second.document_id
    # a different caller never reads another caller's receipt: the other Teacher is refused
    refused = edit(d, first, "bản hai", 1, who="t4", key="k-shared")
    assert refused.status_code == 403
    assert len(receipts(d, first)) == 1 and len(receipts(d, second)) == 1


# ----------------------------------------------------------------------------- no-op
def test_an_edit_equal_to_the_head_writes_nothing_and_is_200(api: Api) -> None:
    d = api
    doc = new_doc(d)
    before = snapshot(d, doc)
    occurrence_before = occurrence_row(d, doc.occurrence_id)
    response = edit(d, doc, FIRST_TEXT, 1, key="k-noop")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["revision_no"] == 1 and body["origin"] == "EXTRACTION"
    assert body["extracted_text"] == FIRST_TEXT
    assert response.headers["Content-Location"] == f"{doc.edit_url}/1"
    assert "Location" not in response.headers
    assert response.headers["ETag"] == f'"{sha(FIRST_TEXT)}.NEEDS_REVIEW"'
    assert snapshot(d, doc) == before and len(audits(d, doc)) == 0  # no revision, no audit
    assert occurrence_row(d, doc.occurrence_id)["revision"] == occurrence_before["revision"]
    ((receipt),) = receipts(d, doc)  # the receipt is the only row, so a replay means the same
    assert receipt["response_json"]["status_code"] == 200
    assert receipt["response_json"]["revision_no"] == 1


def test_a_no_op_replay_is_the_head_of_that_time_even_after_later_edits(api: Api) -> None:
    d = api
    doc = new_doc(d)
    first = edit(d, doc, FIRST_TEXT, 1, key="k-noop-old")
    assert first.status_code == 200
    assert edit(d, doc, "bản mới", 1).status_code == 201
    replay = edit(d, doc, FIRST_TEXT, 1, key="k-noop-old")
    assert replay.status_code == 200 and shape(replay) == shape(first)
    assert replay.json()["revision_no"] == 1
    assert len(revisions(d, doc.document_id)) == 2


def test_the_stale_check_comes_before_the_no_op_check(api: Api) -> None:
    d = api
    doc = new_doc(d)
    assert edit(d, doc, "bản hai", 1).status_code == 201
    # equal to revision 1 but the head is 2 and the client edited from 1: stale, not a no-op
    stale = edit(d, doc, FIRST_TEXT, 1)
    assert stale.status_code == 409 and stale.json()["current_version"] == 2
    # equal to the current head with the right fence: a no-op
    assert edit(d, doc, "bản hai", 2).status_code == 200


# ----------------------------------------------------------------------------- revision cap
def test_the_fifty_first_revision_is_refused_and_a_no_op_still_answers(api: Api) -> None:
    d = api
    doc = new_doc(d)
    for number in range(2, 51):  # revisions 2..50
        response = edit(d, doc, f"bản số {number}", number - 1)
        assert response.status_code == 201, (number, response.text)
    assert len(revisions(d, doc.document_id)) == 50
    before = snapshot(d, doc)
    refused = edit(d, doc, "bản số 51", 50, key="k-cap")
    assert refused.status_code == 409 and refused.json()["code"] == "RESOURCE_CONFLICT"
    assert "current_version" not in refused.json() or refused.json()["current_version"] is None
    assert snapshot(d, doc) == before
    assert not [r for r in receipts(d, doc) if r["idempotency_key"] == "k-cap"]
    # the head text again is still a harmless no-op, and a stale fence is still stale
    assert edit(d, doc, "bản số 50", 50).status_code == 200
    stale = edit(d, doc, "bản số 51", 49)
    assert stale.status_code == 409 and stale.json()["code"] == "STALE_REVISION"
    assert stale.json()["current_version"] == 50


# ----------------------------------------------------------------------------- scope
def test_only_the_responsible_teacher_writes_and_everyone_else_is_refused_alike(api: Api) -> None:
    d = api
    doc = new_doc(d)
    before = snapshot(d, doc)
    unknown = edit(d, Doc(doc.occurrence_id, str(uuid4()), doc.revision_1_id), "x y", 1)
    assert unknown.status_code == 404
    reference = shape(unknown)
    # another occurrence's document is not reachable through this occurrence
    other_occurrence = make_occurrence(d)
    foreign = edit(d, Doc(other_occurrence, doc.document_id, doc.revision_1_id), "x y", 1)
    assert shape(foreign) == reference
    unknown_occurrence = edit(d, Doc(str(uuid4()), doc.document_id, doc.revision_1_id), "x y", 1)
    assert shape(unknown_occurrence) == reference
    assert edit(d, Doc("o" * 40, doc.document_id, doc.revision_1_id), "x y", 1).status_code == 404
    for who in (
        "t2",  # a Teacher of another class
        "manager",
        "admin_teacher",  # a School Manager who teaches another class
        "tother",
        "stranger",
        "revoked",
        "inactive",
        "parent",
        "platform",
    ):
        refused = edit(d, doc, "x y", 1, who=who)
        assert shape(refused) == reference, who
    for who in ("t4", "g1", "o1", "mixed"):
        forbidden = edit(d, doc, "x y", 1, who=who)
        assert forbidden.status_code == 403, who
        assert forbidden.json()["code"] == "ACTION_NOT_ALLOWED", who
    assert snapshot(d, doc) == before and receipts(d, doc) == []
    assert unlocked(d, doc) and idle_in_transaction(d) == 0
    assert edit(d, doc, "x y", 1).status_code == 201  # the responsible Teacher still can


def test_a_revoked_teacher_cannot_replay_an_old_key(api: Api) -> None:
    d = api
    doc = new_doc(d)
    assert edit(d, doc, "bản hai", 1, key="k-revoke").status_code == 201
    with d.sessions().begin() as db:
        db.execute(
            update(OrganizationAssignmentModel)
            .where(
                OrganizationAssignmentModel.subject == d.subjects["t1"],
                OrganizationAssignmentModel.class_id == d.classes["a1"],
            )
            .values(active=False)
        )
    replay = edit(d, doc, "bản hai", 1, key="k-revoke")  # re-authorised before the receipt is read
    assert replay.status_code == 404


# ----------------------------------------------------------------------------- state
def test_an_archived_occurrence_and_a_deleted_document_are_409(api: Api) -> None:
    d = api
    doc = new_doc(d)
    assert edit(d, doc, "bản hai", 1, key="k-before-archive").status_code == 201
    with d.sessions().begin() as db:  # no route archives an occurrence in v3: set by SQL
        db.execute(
            update(OCCURRENCES)
            .where(OCCURRENCES.c.occurrence_id == doc.occurrence_id)
            .values(state="ARCHIVED")
        )
    before = snapshot(d, doc)
    archived = edit(d, doc, "bản ba", 2)
    assert archived.status_code == 409 and archived.json()["code"] == "INVALID_STATE_TRANSITION"
    # a replay still answers after the archive (it writes nothing)
    replay = edit(d, doc, "bản hai", 1, key="k-before-archive")
    assert replay.status_code == 201 and replay.json()["revision_no"] == 2
    assert snapshot(d, doc) == before
    other = new_doc(d)
    with d.sessions().begin() as db:  # no route deletes a document in v3: set by SQL
        db.execute(
            update(SOURCE_DOCUMENTS)
            .where(SOURCE_DOCUMENTS.c.source_document_id == other.document_id)
            .values(document_state="DELETED", deleted_at=datetime.now(UTC))
        )
    deleted = edit(d, other, "bản hai", 1)
    assert deleted.status_code == 409 and deleted.json()["code"] == "INVALID_STATE_TRANSITION"
    assert len(revisions(d, other.document_id)) == 1
    assert unlocked(d, doc) and unlocked(d, other) and idle_in_transaction(d) == 0


# ----------------------------------------------------------------------------- validation
def test_bad_requests_write_nothing(api: Api) -> None:
    d = api
    doc = new_doc(d)
    before = snapshot(d, doc)
    subject = d.subjects["t1"]
    missing_key = d.client.post(
        doc.edit_url,
        json={"extracted_text": "x", "expected_head_revision_no": 1},
        headers=headers(subject),
    )
    assert missing_key.status_code == 400
    assert {"field": "Idempotency-Key", "code": "REQUIRED"} in missing_key.json()["field_errors"]
    unknown = edit(d, doc, "x", 1, origin="EXTRACTION")
    assert unknown.status_code == 400
    assert any(i["code"] == "UNKNOWN_FIELD" for i in unknown.json()["field_errors"])
    cases = (
        ("   \n\t  ", "EMPTY"),
        ("có NUL \x00 giữa", "INVALID_FORMAT"),
        ("é" * (TWO_MIB // 2) + "a", "TOO_LONG"),
        ("€" * (TWO_MIB // 3 + 1), "TOO_LONG"),
    )
    for value, code in cases:
        response = edit(d, doc, value, 1)
        assert response.status_code == 400, code
        assert response.json()["field_errors"] == [{"field": "extracted_text", "code": code}]
    surrogate = d.client.post(
        doc.edit_url,
        content=b'{"extracted_text":"abc\\ud800def","expected_head_revision_no":1}',
        headers={**headers(subject, "k-sur"), "Content-Type": "application/json"},
    )
    assert surrogate.status_code == 400 and surrogate.json()["code"] == "INVALID_REQUEST"
    assert "ud800" not in surrogate.text
    zero_head = edit(d, doc, "x", 0)
    assert zero_head.status_code == 400
    assert snapshot(d, doc) == before and receipts(d, doc) == []
    assert unlocked(d, doc)


def test_validation_does_not_decide_scope(api: Api) -> None:
    d = api
    doc = new_doc(d)
    # a stranger with a bad text learns the text rule, never whether the document exists
    bad = edit(d, doc, "   ", 1, who="stranger")
    ok = edit(d, doc, "x y", 1, who="stranger")
    assert bad.status_code == 400 and ok.status_code == 404


def test_an_oversize_body_is_413_before_authentication_or_any_database_work(api: Api) -> None:
    d = api
    doc = new_doc(d)
    before = snapshot(d, doc)
    body = b'{"extracted_text":"' + b"a" * MAX_REVISION_EDIT_BODY_BYTES + b'"}'
    # no principal header at all: the guard answers first
    response = d.client.post(
        doc.edit_url, content=body, headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 413 and response.json()["code"] == "MEDIA_TOO_LARGE"
    with_key = d.client.post(
        doc.edit_url,
        content=body,
        headers={**headers(d.subjects["t1"], "k-big"), "Content-Type": "application/json"},
    )
    assert with_key.status_code == 413
    assert snapshot(d, doc) == before and receipts(d, doc) == []
    assert idle_in_transaction(d) == 0
    # a valid text of 2 MiB of control characters is about 12 MiB on the wire and passes the guard
    control = "\u0001" * TWO_MIB
    accepted = edit(d, doc, control, 1)
    assert accepted.status_code == 201, accepted.text[:200]
    assert revisions(d, doc.document_id)[1]["extracted_text"] == control


# ----------------------------------------------------------------------------- immutability
def test_the_database_refuses_to_change_or_delete_an_edited_revision(api: Api) -> None:
    d = api
    doc = new_doc(d)
    assert edit(d, doc, "bản đã sửa", 1).status_code == 201
    revision_id = revisions(d, doc.document_id)[1]["document_revision_id"]
    key = DOCUMENT_REVISIONS.c.document_revision_id

    def attempt(**values: Any) -> str:
        with pytest.raises(DBAPIError) as raised, d.engine.begin() as conn:
            conn.execute(update(DOCUMENT_REVISIONS).where(key == revision_id).values(**values))
        return str(raised.value)

    assert "DOCUMENT_REVISION_IMMUTABLE" in attempt(extracted_text="đổi lén")
    assert "DOCUMENT_REVISION_IMMUTABLE" in attempt(extracted_text_hash=sha("đổi lén"))
    for column, value in (
        ("origin", "EXTRACTION"),
        ("revision_no", 9),
        ("base_revision_no", 5),
        ("parser_name", "forged"),
        ("extraction_warnings", ["X"]),
        ("page_coverage", [1]),
        ("created_by", "someone-else"),
        ("created_at", datetime(2020, 1, 1, tzinfo=UTC)),
        ("source_document_id", str(uuid4())),
    ):
        reason = attempt(**{column: value})
        assert "DOCUMENT_REVISION_IMMUTABLE" in reason or "violates" in reason, column
    with pytest.raises(DBAPIError) as deleted, d.engine.begin() as conn:
        conn.execute(DOCUMENT_REVISIONS.delete().where(key == revision_id))
    assert "DOCUMENT_REVISION_DELETE_FORBIDDEN" in str(deleted.value)
    # the one allowed change: the one-way review stamp, once
    stamp = {"review_state": "CONFIRMED", "reviewed_by": d.accounts["t1"]}
    with d.engine.begin() as conn:
        conn.execute(
            update(DOCUMENT_REVISIONS)
            .where(key == revision_id)
            .values(**stamp, reviewed_at=datetime.now(UTC))
        )
    assert "DOCUMENT_REVISION_REVIEW_ONE_WAY" in attempt(
        review_state="NEEDS_REVIEW", reviewed_by=None, reviewed_at=None
    )
    assert "DOCUMENT_REVISION_REVIEW_ONE_WAY" in attempt(reviewed_by="someone-else")
    row = revisions(d, doc.document_id)[1]
    assert row["extracted_text"] == "bản đã sửa" and row["review_state"] == "CONFIRMED"


def test_a_plan_that_pins_revision_one_is_not_retargeted_by_a_later_edit(api: Api) -> None:
    d = api
    doc = new_doc(d)
    plan_id = str(uuid4())
    with d.sessions().begin() as db:
        db.execute(
            PLAN_REVISIONS.insert().values(
                plan_revision_id=plan_id,
                occurrence_id=doc.occurrence_id,
                revision_no=1,
                source_document_revision_id=doc.revision_1_id,
                objectives=["Nhận biết hình tròn"],
                teacher_direction="Kể chuyện chú mèo",
                content_hash=HEX,
                created_by=d.accounts["t1"],
            )
        )
    before = snapshot(d, doc)
    assert edit(d, doc, "bản hai sau khi chốt kế hoạch", 1).status_code == 201
    with d.sessions()() as db:
        plan = (
            db.execute(select(PLAN_REVISIONS).where(PLAN_REVISIONS.c.plan_revision_id == plan_id))
            .mappings()
            .one()
        )
    assert plan["source_document_revision_id"] == doc.revision_1_id  # exact pin, never "latest"
    assert plan["state"] == "DRAFT"
    assert snapshot(d, doc)[0] == before[0]  # the pinned revision is byte-identical
    pinned = d.client.get(doc.edit_url + "/1", headers=headers(d.subjects["t1"]))
    assert pinned.json()["extracted_text"] == FIRST_TEXT
    # and a draft plan could pin the new revision explicitly: nothing moved it
    assert revisions(d, doc.document_id)[1]["document_revision_id"] != doc.revision_1_id


# ----------------------------------------------------------------------------- audit and leaks
def test_the_audit_entry_names_the_revision_not_the_text_and_nothing_leaks(api: Api) -> None:
    d = api
    doc = new_doc(d)
    secret = "văn bản riêng tư của giáo viên"
    response = edit(d, doc, secret, 1)
    assert response.status_code == 201
    ((audit),) = audits(d, doc)
    assert audit["actor_ref"] == d.accounts["t1"]
    assert audit["action"] == "lesson.document_revision.create"
    assert audit["resource_type"] == "lesson_document_revision"
    assert audit["resource_id"] == revisions(d, doc.document_id)[1]["document_revision_id"]
    assert audit["organization_id"] == d.organization
    assert secret not in str(dict(audit))
    lowered = response.text.lower()
    for word in LEAK_WORDS:
        assert word not in lowered, word
    assert d.organization not in response.text and d.other_organization not in response.text


def test_no_row_lock_survives_any_outcome(api: Api) -> None:
    d = api
    doc = new_doc(d)
    outcomes = [
        edit(d, doc, "bản hai", 1),  # 201
        edit(d, doc, "bản hai", 2),  # 200
        edit(d, doc, "bản ba", 1),  # 409
        edit(d, doc, "x", 2, who="t4"),  # 403
        edit(d, doc, "x", 2, who="stranger"),  # 404
        edit(d, doc, "  ", 2),  # 400
    ]
    assert [o.status_code for o in outcomes] == [201, 200, 409, 403, 404, 400]
    time.sleep(0.05)
    assert unlocked(d, doc) and idle_in_transaction(d) == 0


def test_an_integrity_fault_other_than_a_unique_violation_is_a_503_not_a_stale_409(
    api: Api, monkeypatch: pytest.MonkeyPatch
) -> None:
    d = api
    doc = new_doc(d)
    before = snapshot(d, doc)
    from sketch2life.infrastructure.lesson_occurrences import documents as service_module

    # a wrong hash breaks the CHECK on the stored text hash: an integrity error, not a unique one
    with monkeypatch.context() as patched:
        patched.setattr(service_module, "text_sha256", lambda value: "0" * 64)
        response = edit(d, doc, "bản hai", 1, key="k-check")
    assert response.status_code == 503 and response.json()["code"] == "PROVIDER_UNAVAILABLE"
    assert "current_version" not in response.json() or response.json()["current_version"] is None
    assert snapshot(d, doc) == before and receipts(d, doc) == []
    assert unlocked(d, doc) and idle_in_transaction(d) == 0
    assert edit(d, doc, "bản hai", 1, key="k-check").status_code == 201
