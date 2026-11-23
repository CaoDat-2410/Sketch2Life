"""FEAT-066 T-3b: occurrence document attach and the 202 extraction job on PostgreSQL.

SRS l.545-546, l.1437, l.1653, l.1692, l.1696-1699, l.1708, TD-15. Runs only against a disposable
database whose name contains ``be1_acceptance`` and ``frc08``. Principals are injected through the
``X-Test-Principal`` header (the verified adult dependency is overridden); every identity, class,
occurrence and file is synthetic and built in memory.

Object storage is the in-memory port by default; when ``T3B_S3_ENDPOINT``, ``T3B_S3_BUCKET``,
``T3B_S3_ACCESS_KEY`` and ``T3B_S3_SECRET_KEY`` are set the module runs against the local S3Mock
target after the T-2z guard (loopback endpoint and bucket equal to ``FRC08_ALLOWED_*``, bucket
containing ``frc08`` and ``v3-t3b``, no ambient ``AWS_*`` variable). The scanner is the T-2z style
allowlist (a SHA-256 is CLEAN only when registered); the parser is a scripted stand-in keyed on the
file hash for every case that needs a document library, and the real parser for the archive
guards that run before any library. ``pypdf`` is not installed in this environment, so no real PDF
is parsed; DOCX and PPTX cases use the real parser when ``python-docx`` and ``python-pptx`` import.
"""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import time
import zipfile
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from threading import Barrier, Event, Lock
from typing import Any
from uuid import uuid4

import pytest
from fastapi import Depends, FastAPI, Header
from fastapi.testclient import TestClient
from sqlalchemy import select, text, update

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.lesson_documents import (
    LessonDocumentExtraction,
    LessonDocumentRejected,
    MalwareDetected,
    MalwareScanResult,
)
from sketch2life.application.ports.object_storage import ObjectStorageFailure, StoredObject
from sketch2life.application.ports.upload_validation import DOCX_MEDIA_TYPE, PPTX_MEDIA_TYPE
from sketch2life.infrastructure.ai_jobs.read_only import build_read_only_job_repository
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.documents.lesson_parser import DeterministicLessonDocumentParser
from sketch2life.infrastructure.documents.local_test_adapters import (
    LocalTestSignatureMediaValidator,
)
from sketch2life.infrastructure.lesson_library.tables import UPLOAD_SESSIONS
from sketch2life.infrastructure.lesson_occurrences.documents import (
    OccurrenceDocumentService,
    ParseGate,
)
from sketch2life.infrastructure.lesson_occurrences.tables import (
    DOCUMENT_REVISIONS,
    OCCURRENCES,
    SOURCE_DOCUMENTS,
)
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    Be1CommandReceiptModel,
    ClassroomModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.infrastructure.persistence.core_models import (
    CoreAssetMetadataModel,
    CoreAuditEntryModel,
)
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.routers.lesson_occurrences import get_document_service
from tools.local_s3mock_target import check_s3_credentials, check_s3mock_target, ensure_task_bucket
from tools.run_be1_lifecycle_consumer import TargetRefused

ISSUER = "synthetic-t3b-issuer"
TASK_TAG = "v3-t3b"
PDF = "application/pdf"
_S3_VARIABLES = ("T3B_S3_ENDPOINT", "T3B_S3_BUCKET", "T3B_S3_ACCESS_KEY", "T3B_S3_SECRET_KEY")
HAS_DOCX = importlib.util.find_spec("docx") is not None
HAS_PPTX = importlib.util.find_spec("pptx") is not None
LEAK_WORDS = (
    "bucket",
    "object_key",
    "storage_object_ref",
    "presigned",
    "amazonaws",
    "organization_ref",
    "organization_id",
    "scanner",
    "occurrences/",
    "/original",
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ----------------------------------------------------------------------------- doubles
class InMemoryStorage:
    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, str]] = {}

    def put_object(
        self, key: str, body: Any, *, content_type: str, content_length: int, metadata: Any
    ) -> None:
        content = body.read()
        assert len(content) == content_length
        self.objects[key] = (content, content_type)

    def get_object(self, key: str) -> StoredObject | None:
        item = self.objects.get(key)
        if item is None:
            return None
        content, content_type = item
        return StoredObject(io.BytesIO(content), len(content), content_type, {})

    def delete_object(self, key: str) -> None:
        self.objects.pop(key, None)

    def list_keys(self, prefix: str) -> tuple[str, ...]:
        return tuple(sorted(key for key in self.objects if key.startswith(prefix)))


class _BrokenBody:
    """A response stream that dies mid-read with a client-library error."""

    def read(self, size: int = -1) -> bytes:
        raise ConnectionResetError("synthetic mid-stream failure")

    def close(self) -> None:
        return None


class FaultStorage:
    """Delegating storage that can fail reads and counts them."""

    def __init__(self, inner: Any) -> None:
        self.inner = inner
        self.fail_get = False
        self.fail_read = False
        self.gets: list[str] = []
        self._lock = Lock()

    def put_object(self, key: str, body: Any, **kwargs: Any) -> None:
        self.inner.put_object(key, body, **kwargs)

    def get_object(self, key: str) -> Any:
        if self.fail_get:
            raise ObjectStorageFailure("synthetic get failure")
        with self._lock:
            self.gets.append(key)
        stored = self.inner.get_object(key)
        if stored is not None and self.fail_read:
            return StoredObject(_BrokenBody(), stored.content_length, stored.content_type, {})
        return stored

    def delete_object(self, key: str) -> None:
        self.inner.delete_object(key)

    def list_keys(self, prefix: str) -> tuple[str, ...]:
        return self.inner.list_keys(prefix)


class AllowlistScanner:
    """CLEAN for registered SHA-256 digests, MalwareDetected for any other (T-2z style)."""

    def __init__(self) -> None:
        self.clean: set[str] = set()
        self.calls = 0

    def scan(self, file_obj: Any) -> MalwareScanResult:
        self.calls += 1
        file_obj.seek(0)
        digest = hashlib.sha256(file_obj.read()).hexdigest()
        file_obj.seek(0)
        if digest not in self.clean:
            raise MalwareDetected("synthetic")
        return MalwareScanResult("t3b-allowlist", "1", "CLEAN")


class ScriptedParser:
    """Scripted result per file hash; any other file goes to the real parser (archive guards)."""

    def __init__(self) -> None:
        self.scripts: dict[str, Any] = {}
        self.calls = 0
        self._lock = Lock()
        self.real = DeterministicLessonDocumentParser()

    def extract(self, file_obj: Any, *, file_extension: str) -> LessonDocumentExtraction:
        with self._lock:
            self.calls += 1
        file_obj.seek(0)
        digest = hashlib.sha256(file_obj.read()).hexdigest()
        file_obj.seek(0)
        script = self.scripts.get(digest)
        if script is None:
            return self.real.extract(file_obj, file_extension=file_extension)
        if isinstance(script, Exception):
            raise script
        if callable(script):
            result = script(file_obj, file_extension)
            assert isinstance(result, LessonDocumentExtraction)
            return result
        assert isinstance(script, LessonDocumentExtraction)
        return script


def extraction(
    text_value: str = "Tiêu đề: Vẽ con mèo\nMục tiêu: Nhận biết hình dạng con mèo",
    *,
    pages: int | None = 3,
    coverage: tuple[int, ...] = (1, 2, 3),
    media: str = PDF,
    warnings: tuple[str, ...] = ("MISSING_FIELD_TOPIC",),
) -> LessonDocumentExtraction:
    return LessonDocumentExtraction(
        detected_media_type=media,
        parser_name="t3b-scripted",
        parser_version="1.2.3",
        page_or_slide_count=pages,
        page_coverage=coverage,
        extracted_fields={},
        warnings=warnings,
        extracted_text=text_value,
    )


# ----------------------------------------------------------------------------- environment
@dataclass
class Staged:
    upload_id: str
    asset_ref: str
    key: str
    data: bytes
    digest: str


@dataclass
class Api:
    app: FastAPI
    client: TestClient
    storage: FaultStorage
    scanner: AllowlistScanner
    parser: ScriptedParser
    token: str
    organization: str
    other_organization: str
    classes: dict[str, str] = field(default_factory=dict)
    subjects: dict[str, str] = field(default_factory=dict)
    accounts: dict[str, str] = field(default_factory=dict)
    real_s3: bool = False
    counter: int = 0

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


def _s3_storage() -> Any | None:
    if not all(os.environ.get(name) for name in _S3_VARIABLES):
        return None
    endpoint = os.environ["T3B_S3_ENDPOINT"]
    bucket = os.environ["T3B_S3_BUCKET"]
    access_key = os.environ["T3B_S3_ACCESS_KEY"]
    secret_key = os.environ["T3B_S3_SECRET_KEY"]
    try:
        check_s3mock_target(endpoint, bucket, task_tag=TASK_TAG, environ=os.environ)
        check_s3_credentials(access_key, secret_key, os.environ)
    except TargetRefused as refused:
        pytest.fail(f"REFUSED code={refused.code}", pytrace=False)
    from sketch2life.infrastructure.storage.s3_compatible import (
        Boto3S3CompatibleObjectStorage,
        build_s3_client,
    )

    client = build_s3_client(
        endpoint_url=endpoint, region_name="us-east-1", access_key=access_key, secret_key=secret_key
    )
    ensure_task_bucket(client, bucket)
    return Boto3S3CompatibleObjectStorage(
        bucket=bucket,
        endpoint_url=endpoint,
        region_name="us-east-1",
        access_key=access_key,
        secret_key=secret_key,
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
    organization, other = f"synthetic-t3b-org-{token}", f"synthetic-t3b-other-{token}"
    s3 = _s3_storage()
    storage = FaultStorage(s3 if s3 is not None else InMemoryStorage())
    scanner, parser = AllowlistScanner(), ScriptedParser()
    d = Api(app, TestClient(app), storage, scanner, parser, token, organization, other)
    d.real_s3 = s3 is not None
    label = lambda value: f"synthetic-t3b-{value}-{token}"  # noqa: E731
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
        # observer of a1 and teacher of a2 in one account (T0.4-DEBT-1)
        d.subjects["mixed"] = label("mixed")
        d.accounts["mixed"] = _identity(db, label("mixed"), "teacher")
        _assign(db, organization, label("mixed"), "observer", d.classes["a1"])
        _assign(db, organization, label("mixed"), "teacher", d.classes["a2"])
        # a School Manager who also teaches a2
        d.subjects["admin_teacher"] = label("admin_teacher")
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

    app.state.lesson_library_storage = storage
    app.state.lesson_document_scanner = scanner
    app.state.lesson_document_parser = parser
    app.state.lesson_document_parse_gate = ParseGate(
        max_concurrent=4, queue_wait_seconds=1.0, deadline_seconds=20.0
    )
    app.state.upload_media_validator = LocalTestSignatureMediaValidator(env="test")
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


def make_occurrence(
    d: Api, who: str = "t1", class_key: str = "a1", title: str = "Bài học vẽ"
) -> str:
    response = d.client.post(
        "/v1/lesson-occurrences",
        json={"class_id": d.classes[class_key], "title": title},
        headers=headers(d.subjects[who], uuid4().hex),
    )
    assert response.status_code == 201, response.text
    return str(response.json()["occurrence_id"])


def pdf_bytes(d: Api, tag: str = "", pad: int = 0) -> bytes:
    d.counter += 1
    marker = f"%t3b {d.token} {d.counter} {tag}\n".encode()
    return b"%PDF-1.4\n" + marker + b"x" * pad + b"\n%%EOF\n"


def zip_stub(d: Api, kind: str) -> bytes:
    """A structurally valid DOCX or PPTX container (no document library can read it)."""
    d.counter += 1
    parts = (
        {"[Content_Types].xml": b"<Types/>", "word/document.xml": b"<w:document/>"}
        if kind == "docx"
        else {"[Content_Types].xml": b"<Types/>", "ppt/presentation.xml": b"<p:presentation/>"}
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, payload in parts.items():
            archive.writestr(name, payload)
        archive.writestr("docProps/tag.txt", f"t3b {d.token} {d.counter}".encode())
    return buffer.getvalue()


def stage(
    d: Api,
    who: str,
    occurrence_id: str,
    data: bytes,
    *,
    name: str = "giao-an.pdf",
    media: str = PDF,
    script: Any = None,
    clean: bool = True,
) -> Staged:
    """Upload ``data`` through the real session routes and return the completed asset handle."""
    digest = sha(data)
    if clean:
        d.scanner.clean.add(digest)
    if script is not None:
        d.parser.scripts[digest] = script
    subject = d.subjects[who]
    created = d.client.post(
        "/v1/upload-sessions",
        json={
            "purpose": "OCCURRENCE_DOCUMENT",
            "target_ref": occurrence_id,
            "media_type": media,
            "expected_size_bytes": len(data),
            "expected_sha256": digest,
            "file_name": name,
        },
        headers=headers(subject, uuid4().hex),
    )
    assert created.status_code == 201, created.text
    upload_id = created.json()["upload_id"]
    part = 4 * 1024 * 1024
    for number, offset in enumerate(range(0, len(data), part), start=1):
        chunk = data[offset : offset + part]
        put = d.client.put(
            f"/v1/upload-sessions/{upload_id}/parts/{number}",
            content=chunk,
            headers=headers(
                subject, **{"X-Part-SHA256": sha(chunk), "Content-Type": "application/octet-stream"}
            ),
        )
        assert put.status_code == 200, put.text
    done = d.client.post(
        f"/v1/upload-sessions/{upload_id}/complete",
        json={"expected_size_bytes": len(data), "expected_sha256": digest},
        headers=headers(subject, uuid4().hex),
    )
    if not clean:
        assert done.status_code == 422, done.text
        return Staged(upload_id, f"upl_{upload_id}", "", data, digest)
    assert done.status_code == 202, done.text
    key = session_value(d, upload_id, "final_asset_ref")
    return Staged(upload_id, done.json()["asset_ref"], str(key), data, digest)


def session_value(d: Api, upload_id: str, column: str) -> Any:
    with d.sessions()() as db:
        return db.scalar(
            select(UPLOAD_SESSIONS.c[column]).where(
                UPLOAD_SESSIONS.c.upload_session_id == upload_id
            )
        )


def set_session(d: Api, upload_id: str, **values: Any) -> None:
    with d.sessions().begin() as db:
        db.execute(
            update(UPLOAD_SESSIONS)
            .where(UPLOAD_SESSIONS.c.upload_session_id == upload_id)
            .values(**values)
        )


def attach(d: Api, who: str, occurrence_id: str, asset_ref: str, *, key: str | None = None) -> Any:
    return d.client.post(
        f"/v1/lesson-occurrences/{occurrence_id}/documents",
        json={"asset_ref": asset_ref},
        headers=headers(d.subjects[who], key or uuid4().hex),
    )


def attach_ok(
    d: Api, occurrence_id: str, data: bytes, *, who: str = "t1", script: Any = None, **kwargs: Any
) -> tuple[dict[str, Any], Staged]:
    staged = stage(d, who, occurrence_id, data, script=script, **kwargs)
    response = attach(d, who, occurrence_id, staged.asset_ref)
    assert response.status_code == 202, response.text
    return response.json(), staged


def get(d: Api, who: str, path: str, **extra: str) -> Any:
    return d.client.get(path, headers=headers(d.subjects[who], None, **extra))


def job(d: Api, who: str, job_id: str, **extra: str) -> Any:
    return get(d, who, f"/v1/jobs/{job_id}", **extra)


COUNT_SQL = {
    "documents": "SELECT count(*) FROM lesson.source_documents",
    "revisions": "SELECT count(*) FROM lesson.document_revisions",
    "jobs": "SELECT count(*) FROM ai_jobs.job",
    "attempts": "SELECT count(*) FROM ai_jobs.attempt",
    "outbox": "SELECT count(*) FROM ai_jobs.outbox",
    "semantic": "SELECT count(*) FROM ai_jobs.semantic_request",
    "ai_receipts": "SELECT count(*) FROM ai_jobs.command_receipt",
    "completions": "SELECT count(*) FROM ai_jobs.completion_receipt",
    "assets": "SELECT count(*) FROM core_asset_metadata",
    "receipts": (
        "SELECT count(*) FROM be1_command_receipts WHERE operation_scope LIKE '%/documents'"
    ),
    "audits": (
        "SELECT count(*) FROM core_audit_entries WHERE action = 'lesson.source_document.create'"
    ),
}


def counts(d: Api) -> dict[str, int]:
    with d.sessions()() as db:
        return {name: int(db.scalar(text(sql)) or 0) for name, sql in COUNT_SQL.items()}


def document_row(d: Api, document_id: str) -> Any:
    with d.sessions()() as db:
        return (
            db.execute(
                select(SOURCE_DOCUMENTS).where(SOURCE_DOCUMENTS.c.source_document_id == document_id)
            )
            .mappings()
            .one()
        )


def revision_rows(d: Api, document_id: str) -> list[Any]:
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


def job_row(d: Api, job_id: str) -> Any:
    with d.sessions()() as db:
        return (
            db.execute(text("SELECT * FROM ai_jobs.job WHERE job_id = :id"), {"id": job_id})
            .mappings()
            .one()
        )


def doc_url(occurrence_id: str, document_id: str | None = None, tail: str = "") -> str:
    base = f"/v1/lesson-occurrences/{occurrence_id}/documents"
    return base if document_id is None else f"{base}/{document_id}{tail}"


# ----------------------------------------------------------------------------- happy paths
def test_the_assigned_teacher_attaches_a_pdf_and_gets_a_finished_job(api: Api) -> None:
    d = api
    occurrence = make_occurrence(d)
    text_value = "Tiêu đề: Vẽ con mèo\nMục tiêu: Nhận biết hình dạng\nBước 1: vẽ đầu tròn"
    staged = stage(
        d,
        "t1",
        occurrence,
        pdf_bytes(d, "happy"),
        script=extraction(text_value, pages=4, coverage=(1, 2, 4)),
    )
    before = counts(d)
    scans_before = d.scanner.calls
    response = attach(d, "t1", occurrence, staged.asset_ref)
    assert response.status_code == 202, response.text
    body = response.json()
    # the attach did not scan again (T-3b-DEC-3): the verdict of the upload stands
    assert d.scanner.calls == scans_before
    assert body["contract"] == "LessonSourceDocumentAcceptedV1"
    assert body["document_revision_no"] == 1
    document_id, job_id = body["source_document_id"], body["job"]["job_id"]
    assert body["job"] == {
        "job_id": job_id,
        "target_kind": "LESSON_SOURCE_DOCUMENT",
        "state": "succeeded",
    }
    leaked = json.dumps(body).lower()
    assert not any(word in leaked for word in LEAK_WORDS) and staged.key not in leaked

    after = counts(d)
    assert after["documents"] == before["documents"] + 1
    assert after["revisions"] == before["revisions"] + 1
    assert after["jobs"] == before["jobs"] + 1 and after["attempts"] == before["attempts"] + 1
    # TD-15: nothing a worker could pick up and nothing the sweeps could count
    for table in ("outbox", "semantic", "ai_receipts", "completions", "assets"):
        assert after[table] == before[table], table
    assert after["receipts"] == before["receipts"] + 1 and after["audits"] == before["audits"] + 1

    document = document_row(d, document_id)
    assert document["occurrence_id"] == occurrence
    assert document["asset_ref"] == staged.key and document["asset_version"] == 1
    assert document["upload_session_ref"] == staged.upload_id
    assert document["extraction_job_ref"] == job_id
    assert document["safe_file_name"] == "giao-an.pdf" and document["file_extension"] == ".pdf"
    assert document["page_or_slide_count"] == 4 and document["document_state"] == "EXTRACTED"
    assert document["uploaded_by"] == d.accounts["t1"]
    (revision,) = revision_rows(d, document_id)
    assert revision["revision_no"] == 1 and revision["origin"] == "EXTRACTION"
    assert revision["base_revision_no"] is None
    assert revision["extracted_text"] == text_value
    assert revision["extracted_text_hash"] == sha(text_value.encode("utf-8"))
    assert (revision["parser_name"], revision["parser_version"]) == ("t3b-scripted", "1.2.3")
    # the scan page (3) is derived from the page count and the coverage, no OCR
    assert revision["extraction_warnings"] == ["MISSING_FIELD_TOPIC", "OCR_NOT_SUPPORTED_PAGES"]
    assert revision["page_coverage"] == [1, 2, 4]
    assert revision["review_state"] == "NEEDS_REVIEW" and revision["created_by"] == d.accounts["t1"]

    row = job_row(d, job_id)
    assert row["job_type"] == "lesson_source_document_extraction"
    assert row["state"] == "succeeded" and row["result_disposition"] == "accepted"
    assert row["job_revision"] == 3 and row["history"] == [
        "created",
        "started",
        "succeeded:accepted",
    ]
    assert row["target_id"] == document_id and row["session_id"] is None
    assert row["subject_refs"] == [] and row["purpose_code"] == "LESSON_SOURCE_EXTRACTION"
    assert row["policy_snapshot_id"] == "lesson.inline.v1"
    assert row["policy_snapshot"]["max_attempts"] == 1
    assert row["policy_snapshot"]["status"] != "PROPOSED"
    assert row["request_ref"]["input_hash"] == staged.digest
    assert row["result_refs"] == [
        {
            "artifact_ref": f"lesson-document-revision:{revision['document_revision_id']}",
            "sha256": revision["extracted_text_hash"],
            "provenance": "parser:t3b-scripted@1.2.3",
        }
    ]
    assert row["organization_id"] == d.organization

    with d.sessions()() as db:
        audit = db.scalars(
            select(CoreAuditEntryModel).where(
                CoreAuditEntryModel.action == "lesson.source_document.create",
                CoreAuditEntryModel.resource_id == document_id,
            )
        ).one()
        assert audit.actor_ref == d.accounts["t1"] and audit.organization_id == d.organization
        assert "giao-an" not in json.dumps(audit.__dict__, default=str)
        receipt = db.get(
            Be1CommandReceiptModel,
            (
                d.subjects["t1"],
                f"POST /v1/lesson-occurrences/{occurrence}/documents",
                db.scalars(
                    select(Be1CommandReceiptModel.idempotency_key).where(
                        Be1CommandReceiptModel.operation_scope
                        == f"POST /v1/lesson-occurrences/{occurrence}/documents"
                    )
                ).one(),
            ),
        )
        assert receipt is not None and receipt.response_json == body

    # the asset row of the upload is unchanged and still unattached to any other document
    with d.sessions()() as db:
        asset = db.get(CoreAssetMetadataModel, (staged.key, 1))
        assert asset is not None and asset.content_sha256 == staged.digest


def test_the_202_carries_the_job_and_the_document_locations(api: Api) -> None:
    d = api
    occurrence = make_occurrence(d)
    staged = stage(d, "t1", occurrence, pdf_bytes(d), script=extraction())
    response = attach(d, "t1", occurrence, staged.asset_ref)
    assert response.status_code == 202
    body = response.json()
    assert response.headers["Location"] == f"/v1/jobs/{body['job']['job_id']}"
    assert response.headers["Content-Location"] == doc_url(occurrence, body["source_document_id"])
    # no header names the object key, the bucket or the opaque handle (SRS l.1692)
    header_text = json.dumps(dict(response.headers)).lower()
    assert staged.key.lower() not in header_text and "occurrences/" not in header_text.replace(
        "/v1/lesson-occurrences/", ""
    )


def _docx_bytes(d: Api) -> tuple[bytes, Any]:
    if HAS_DOCX:
        import docx

        document = docx.Document()
        d.counter += 1
        document.add_paragraph(f"Tiêu đề: Vẽ con mèo {d.counter}")
        document.add_paragraph("Mục tiêu: Nhận biết hình dạng")
        buffer = io.BytesIO()
        document.save(buffer)
        return buffer.getvalue(), None
    return zip_stub(d, "docx"), extraction(pages=None, coverage=(1,), media=DOCX_MEDIA_TYPE)


def _pptx_bytes(d: Api) -> tuple[bytes, Any]:
    if HAS_PPTX:
        import pptx

        presentation = pptx.Presentation()
        d.counter += 1
        slide = presentation.slides.add_slide(presentation.slide_layouts[5])
        slide.shapes.title.text = f"Tiêu đề: Vẽ con mèo {d.counter}"
        presentation.slides.add_slide(presentation.slide_layouts[6])
        buffer = io.BytesIO()
        presentation.save(buffer)
        return buffer.getvalue(), None
    return zip_stub(d, "pptx"), extraction(pages=2, coverage=(1,), media=PPTX_MEDIA_TYPE)


@pytest.mark.parametrize("kind", ["pdf", "docx", "pptx"])
def test_each_document_type_attaches_and_the_stored_text_is_the_parser_text(
    api: Api, kind: str
) -> None:
    d = api
    occurrence = make_occurrence(d)
    if kind == "pdf":
        data, script, name, media = pdf_bytes(d, kind), extraction(), "a.pdf", PDF
    elif kind == "docx":
        (data, script), name, media = _docx_bytes(d), "a.docx", DOCX_MEDIA_TYPE
    else:
        (data, script), name, media = _pptx_bytes(d), "a.pptx", PPTX_MEDIA_TYPE
    body, _staged = attach_ok(d, occurrence, data, script=script, name=name, media=media)
    document_id = body["source_document_id"]
    document = document_row(d, document_id)
    (revision,) = revision_rows(d, document_id)
    assert document["file_extension"] == f".{kind}"
    assert revision["extracted_text"].strip()
    assert revision["extracted_text_hash"] == sha(revision["extracted_text"].encode("utf-8"))
    if kind == "pptx":
        assert document["page_or_slide_count"] == 2
        assert "OCR_NOT_SUPPORTED_PAGES" in revision["extraction_warnings"]
    if kind == "docx":
        assert document["page_or_slide_count"] is None  # a DOCX has no page count (T-3b-DEC-6)
    if script is None:
        assert "Vẽ con mèo" in revision["extracted_text"]  # the real parser read it
    read = get(d, "t1", doc_url(occurrence, document_id, "/revisions/1"))
    assert read.status_code == 200
    assert read.json()["extracted_text"] == revision["extracted_text"]


def test_a_document_with_some_scan_pages_is_accepted_and_marked_without_ocr(api: Api) -> None:
    d = api
    occurrence = make_occurrence(d)
    body, _ = attach_ok(
        d, occurrence, pdf_bytes(d), script=extraction(pages=10, coverage=(2, 5), warnings=())
    )
    read = get(d, "t1", doc_url(occurrence, body["source_document_id"]))
    assert read.status_code == 200
    document = read.json()
    assert document["warnings"] == ["OCR_NOT_SUPPORTED_PAGES"]
    assert document["page_coverage"] == [2, 5] and document["page_or_slide_count"] == 10


def test_vietnamese_text_is_stored_exactly_and_hashed_in_utf8(api: Api) -> None:
    d = api
    occurrence = make_occurrence(d)
    text_value = "Vẽ con mèo xinh đẹp ☺ 🐱\nHướng dẫn: các bước vẽ\tcó dấu tab"
    body, _ = attach_ok(d, occurrence, pdf_bytes(d), script=extraction(text_value))
    (revision,) = revision_rows(d, body["source_document_id"])
    assert revision["extracted_text"] == text_value
    read = get(d, "t1", doc_url(occurrence, body["source_document_id"], "/revisions/1")).json()
    assert read["extracted_text"] == text_value
    assert read["text_hash"] == sha(text_value.encode("utf-8"))
    assert read["text_length"] == len(text_value)


# ----------------------------------------------------------------------------- refusals
def _count_snapshot(d: Api) -> dict[str, int]:
    return counts(d)


def _refused(
    d: Api, occurrence: str, script: Any, status: int, code: str, *, name: str = "a.pdf"
) -> None:
    staged = stage(d, "t1", occurrence, pdf_bytes(d, code), script=script, name=name)
    before = _count_snapshot(d)
    response = attach(d, "t1", occurrence, staged.asset_ref)
    assert response.status_code == status, response.text
    body = response.json()
    assert body["code"] == code and body["message"]
    assert _count_snapshot(d) == before  # no document, revision, job, audit or receipt
    # the session still stands, so the Teacher can replace the file with another upload
    assert session_value(d, staged.upload_id, "state") == "COMPLETED"
    # the failed attempt left nothing that blocks the same asset later
    assert not any(word in response.text.lower() for word in LEAK_WORDS)


@pytest.mark.parametrize(
    ("parser_code", "status", "code"),
    [
        ("ENCRYPTED_DOCUMENT_UNSUPPORTED", 422, "ENCRYPTED_DOCUMENT_UNSUPPORTED"),
        ("OCR_NOT_SUPPORTED", 422, "OCR_NOT_SUPPORTED"),
        ("DOCUMENT_PAGE_LIMIT_EXCEEDED", 422, "DOCUMENT_PAGE_LIMIT_EXCEEDED"),
        ("DOCUMENT_TEXT_LIMIT_EXCEEDED", 422, "DOCUMENT_TEXT_LIMIT_EXCEEDED"),
        ("INVALID_SOURCE_DOCUMENT", 400, "INVALID_FILE_CONTENT"),
        ("DOCUMENT_EXPANSION_LIMIT_EXCEEDED", 400, "INVALID_FILE_CONTENT"),
        ("UNSUPPORTED_MEDIA_TYPE", 415, "UNSUPPORTED_LESSON_TYPE"),
    ],
)
def test_a_file_the_parser_rejects_is_refused_before_any_row_is_written(
    api: Api, parser_code: str, status: int, code: str
) -> None:
    d = api
    occurrence = make_occurrence(d)
    _refused(d, occurrence, LessonDocumentRejected(parser_code), status, code)


def test_a_replacement_file_attaches_after_a_refusal(api: Api) -> None:
    d = api
    occurrence = make_occurrence(d)
    _refused(d, occurrence, LessonDocumentRejected("OCR_NOT_SUPPORTED"), 422, "OCR_NOT_SUPPORTED")
    body, _ = attach_ok(d, occurrence, pdf_bytes(d, "replacement"), script=extraction())
    assert body["document_revision_no"] == 1
    listing = get(d, "t1", doc_url(occurrence)).json()
    assert len(listing["items"]) == 1


def test_an_unexpected_parser_fault_is_unreadable_content_not_a_500(api: Api) -> None:
    d = api
    occurrence = make_occurrence(d)
    _refused(d, occurrence, RuntimeError("boom with secret text"), 400, "INVALID_FILE_CONTENT")


@pytest.mark.parametrize(
    "bad_text",
    ["a\x00b", "lone \ud800 surrogate", "", "   \n\t "],
    ids=["nul", "surrogate", "empty", "blank"],
)
def test_text_that_cannot_be_stored_is_refused_never_a_500_or_a_partial_row(
    api: Api, bad_text: str
) -> None:
    d = api
    occurrence = make_occurrence(d)
    _refused(d, occurrence, extraction(bad_text), 400, "INVALID_FILE_CONTENT")


def test_text_over_two_mebibytes_of_utf8_is_refused(api: Api) -> None:
    d = api
    occurrence = make_occurrence(d)
    oversized = "ê" * (1024 * 1024 + 1)  # 2 MiB + 2 bytes of UTF-8
    _refused(d, occurrence, extraction(oversized), 400, "INVALID_FILE_CONTENT")


def test_a_detected_type_that_differs_from_the_asset_type_is_415(api: Api) -> None:
    d = api
    occurrence = make_occurrence(d)
    _refused(d, occurrence, extraction(media=DOCX_MEDIA_TYPE), 415, "UNSUPPORTED_LESSON_TYPE")


def test_a_file_name_whose_extension_does_not_match_the_asset_type_is_415(api: Api) -> None:
    d = api
    occurrence = make_occurrence(d)
    staged = stage(d, "t1", occurrence, pdf_bytes(d), script=extraction())
    set_session(d, staged.upload_id, safe_file_name="giao-an.docx")
    before = counts(d)
    response = attach(d, "t1", occurrence, staged.asset_ref)
    assert (response.status_code, response.json()["code"]) == (415, "UNSUPPORTED_LESSON_TYPE")
    assert counts(d) == before


def _real_parser_refusal(d: Api, name: str, data: bytes, media: str, code: str) -> None:
    occurrence = make_occurrence(d)
    staged = stage(d, "t1", occurrence, data, name=name, media=media)  # no script: real parser
    before = counts(d)
    response = attach(d, "t1", occurrence, staged.asset_ref)
    assert response.status_code == 400, response.text
    assert response.json()["code"] == code
    assert counts(d) == before


def test_the_real_parser_refuses_an_archive_bomb_a_corrupt_zip_and_a_container_without_parts(
    api: Api,
) -> None:
    d = api
    bomb = io.BytesIO()
    with zipfile.ZipFile(bomb, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", b"<Types/>")
        archive.writestr("word/document.xml", b"<w:document/>")
        archive.writestr("word/filler.bin", b"\x00" * (3 * 1024 * 1024))
    _real_parser_refusal(d, "bomb.docx", bomb.getvalue(), DOCX_MEDIA_TYPE, "INVALID_FILE_CONTENT")
    corrupt = b"PK\x03\x04" + b"this is not a real zip " * 50
    _real_parser_refusal(d, "corrupt.docx", corrupt, DOCX_MEDIA_TYPE, "INVALID_FILE_CONTENT")
    partless = io.BytesIO()
    with zipfile.ZipFile(partless, "w") as archive:
        archive.writestr("[Content_Types].xml", b"<Types/>")
        archive.writestr("unrelated.txt", b"x")
    _real_parser_refusal(
        d, "partless.pptx", partless.getvalue(), PPTX_MEDIA_TYPE, "INVALID_FILE_CONTENT"
    )


def test_an_object_that_changed_after_the_upload_is_refused_as_a_checksum_mismatch(
    api: Api,
) -> None:
    d = api
    occurrence = make_occurrence(d)
    staged = stage(d, "t1", occurrence, pdf_bytes(d, "tamper"), script=extraction())
    original = staged.data
    tampered = original[:-8] + b"TAMPERED"  # same length, other bytes
    assert len(tampered) == len(original) and sha(tampered) != staged.digest
    d.storage.inner.put_object(
        staged.key,
        io.BytesIO(tampered),
        content_type=PDF,
        content_length=len(tampered),
        metadata={},
    )
    before = counts(d)
    response = attach(d, "t1", occurrence, staged.asset_ref)
    assert (response.status_code, response.json()["code"]) == (422, "UPLOAD_CHECKSUM_MISMATCH")
    assert counts(d) == before
    shorter = original[:-5]
    d.storage.inner.put_object(
        staged.key, io.BytesIO(shorter), content_type=PDF, content_length=len(shorter), metadata={}
    )
    again = attach(d, "t1", occurrence, staged.asset_ref)
    assert (again.status_code, again.json()["code"]) == (422, "UPLOAD_CHECKSUM_MISMATCH")


def test_an_object_over_25_megabytes_is_413_and_a_missing_object_is_422(api: Api) -> None:
    d = api
    occurrence = make_occurrence(d)
    staged = stage(d, "t1", occurrence, pdf_bytes(d, "big"), script=extraction())
    huge = b"%PDF-1.4\n" + b"x" * 25_000_100
    d.storage.inner.put_object(
        staged.key, io.BytesIO(huge), content_type=PDF, content_length=len(huge), metadata={}
    )
    before = counts(d)
    response = attach(d, "t1", occurrence, staged.asset_ref)
    assert (response.status_code, response.json()["code"]) == (413, "LESSON_FILE_TOO_LARGE")
    d.storage.inner.delete_object(staged.key)
    missing = attach(d, "t1", occurrence, staged.asset_ref)
    assert (missing.status_code, missing.json()["code"]) == (422, "UPLOAD_INCOMPLETE")
    assert counts(d) == before


def test_a_storage_fault_is_503_and_retryable_and_writes_nothing(api: Api) -> None:
    d = api
    occurrence = make_occurrence(d)
    staged = stage(d, "t1", occurrence, pdf_bytes(d, "fault"), script=extraction())
    before = counts(d)
    d.storage.fail_get = True
    response = attach(d, "t1", occurrence, staged.asset_ref)
    d.storage.fail_get = False
    assert (response.status_code, response.json()["code"]) == (503, "STORAGE_UNAVAILABLE")
    assert response.json()["retryable"] is True
    assert counts(d) == before
    assert attach(d, "t1", occurrence, staged.asset_ref).status_code == 202


def test_a_fault_in_the_middle_of_the_read_is_a_retryable_503_not_a_500(api: Api) -> None:
    d = api
    occurrence = make_occurrence(d)
    staged = stage(d, "t1", occurrence, pdf_bytes(d, "midstream"), script=extraction())
    before = counts(d)
    d.storage.fail_read = True
    response = attach(d, "t1", occurrence, staged.asset_ref)
    d.storage.fail_read = False
    assert (response.status_code, response.json()["code"]) == (503, "STORAGE_UNAVAILABLE")
    assert response.json()["retryable"] is True
    assert counts(d) == before
    assert attach(d, "t1", occurrence, staged.asset_ref).status_code == 202


# ----------------------------------------------------------------------------- scope
def test_every_asset_that_is_not_the_callers_clean_completed_asset_of_this_occurrence_is_one_404(
    api: Api,
) -> None:
    d = api
    first = make_occurrence(d)
    second = make_occurrence(d, title="Bài khác")
    foreign = make_occurrence(d, "tother", "b1")
    mine = stage(d, "t1", first, pdf_bytes(d, "mine"), script=extraction())
    other_occurrence = stage(d, "t1", second, pdf_bytes(d, "second"), script=extraction())
    other_organization = stage(d, "tother", foreign, pdf_bytes(d, "foreign"), script=extraction())
    not_clean = stage(d, "t1", first, pdf_bytes(d, "ni"), script=extraction())
    set_session(d, not_clean.upload_id, scan_verdict="ERROR")
    unscanned = stage(d, "t1", first, pdf_bytes(d, "un"), script=extraction())
    set_session(d, unscanned.upload_id, scan_verdict=None)
    foreign_owner = stage(d, "t1", first, pdf_bytes(d, "fo"), script=extraction())
    set_session(d, foreign_owner.upload_id, owner_principal_ref=d.subjects["t4"])
    failed = stage(d, "t1", first, pdf_bytes(d, "inf"), script=extraction(), clean=False)
    open_session = d.client.post(
        "/v1/upload-sessions",
        json={
            "purpose": "OCCURRENCE_DOCUMENT",
            "target_ref": first,
            "media_type": PDF,
            "expected_size_bytes": 10,
            "expected_sha256": "a" * 64,
            "file_name": "o.pdf",
        },
        headers=headers(d.subjects["t1"], uuid4().hex),
    ).json()["upload_id"]
    before = counts(d)
    refs = {
        "other occurrence": other_occurrence.asset_ref,
        "other organization": other_organization.asset_ref,
        "scan verdict not CLEAN": not_clean.asset_ref,
        "unscanned": unscanned.asset_ref,
        "other owner": foreign_owner.asset_ref,
        "failed session": failed.asset_ref,
        "open session": f"upl_{open_session}",
        "unknown handle": "upl_" + uuid4().hex,
    }
    shapes = {label: shape(attach(d, "t1", first, ref)) for label, ref in refs.items()}
    assert {value[0] for value in shapes.values()} == {404}
    assert len({json.dumps(value[1], sort_keys=True) for value in shapes.values()}) == 1
    assert shapes["unknown handle"][1]["code"] == "RESOURCE_NOT_FOUND"
    assert counts(d) == before
    assert attach(d, "t1", first, mine.asset_ref).status_code == 202


def test_a_non_handle_value_is_a_request_error_not_an_existence_hint(api: Api) -> None:
    d = api
    occurrence = make_occurrence(d)
    staged = stage(d, "t1", occurrence, pdf_bytes(d, "k"), script=extraction())
    response = attach(d, "t1", occurrence, staged.key)  # the object key is not a handle
    assert response.status_code == 400
    assert response.json()["field_errors"] == [{"field": "asset_ref", "code": "INVALID_FORMAT"}]
    assert staged.key not in response.text


def test_the_write_guard_is_the_responsible_teacher_and_everyone_else_is_refused(api: Api) -> None:
    d = api
    occurrence = make_occurrence(d)
    staged = stage(d, "t1", occurrence, pdf_bytes(d, "guard"), script=extraction())
    before = counts(d)
    outcome = {
        who: shape(attach(d, who, occurrence, staged.asset_ref))
        for who in (
            "t4",
            "g1",
            "o1",
            "t2",
            "manager",
            "parent",
            "stranger",
            "tother",
            "inactive",
            "revoked",
            "mixed",
        )
    }
    # in scope but not allowed: 403 (second teacher of the class, guide, observer)
    for who in ("t4", "g1", "o1", "mixed"):
        assert outcome[who][0] == 403, who
        assert outcome[who][1]["code"] == "ACTION_NOT_ALLOWED"
    # outside the caller's scope: the uniform 404
    uniform = {
        json.dumps(outcome[who][1], sort_keys=True)
        for who in ("t2", "manager", "parent", "stranger", "tother", "inactive", "revoked")
    }
    assert {
        outcome[who][0]
        for who in ("t2", "manager", "parent", "stranger", "tother", "inactive", "revoked")
    } == {404}
    assert len(uniform) == 1
    unknown = shape(attach(d, "t1", str(uuid4()), staged.asset_ref))
    assert unknown[0] == 404 and json.dumps(unknown[1], sort_keys=True) in uniform
    assert counts(d) == before
    assert attach(d, "t1", occurrence, staged.asset_ref).status_code == 202


def test_an_archived_occurrence_does_not_accept_a_document(api: Api) -> None:
    d = api
    occurrence = make_occurrence(d)
    staged = stage(d, "t1", occurrence, pdf_bytes(d, "arch"), script=extraction())
    with d.sessions().begin() as db:
        db.execute(
            update(OCCURRENCES)
            .where(OCCURRENCES.c.occurrence_id == occurrence)
            .values(state="ARCHIVED")
        )
    before = counts(d)
    response = attach(d, "t1", occurrence, staged.asset_ref)
    assert (response.status_code, response.json()["code"]) == (409, "INVALID_STATE_TRANSITION")
    assert counts(d) == before


def test_a_session_that_stopped_being_clean_between_snapshot_and_write_is_refused_under_the_lock(
    api: Api,
) -> None:
    """The write transaction re-checks everything the snapshot read."""
    d = api
    occurrence = make_occurrence(d)
    staged = stage(d, "t1", occurrence, pdf_bytes(d, "late"), script=extraction())

    def flip(_file: Any, _extension: str) -> LessonDocumentExtraction:
        set_session(
            d, staged.upload_id, scan_verdict="ERROR"
        )  # after the snapshot, before the write
        return extraction()

    d.parser.scripts[staged.digest] = flip
    before = counts(d)
    response = attach(d, "t1", occurrence, staged.asset_ref)
    assert response.status_code == 404
    assert counts(d) == before


# ----------------------------------------------------------------------------- keys and replay
def test_a_replay_returns_the_first_202_and_writes_nothing(api: Api) -> None:
    d = api
    occurrence = make_occurrence(d)
    staged = stage(d, "t1", occurrence, pdf_bytes(d, "replay"), script=extraction())
    other = stage(d, "t1", occurrence, pdf_bytes(d, "other"), script=extraction())
    first = attach(d, "t1", occurrence, staged.asset_ref, key="replay-key")
    assert first.status_code == 202
    after_first = counts(d)
    calls, gets = d.parser.calls, len(d.storage.gets)
    again = attach(d, "t1", occurrence, staged.asset_ref, key="replay-key")
    assert again.status_code == 202 and again.json() == first.json()
    assert again.headers["Location"] == first.headers["Location"]
    assert counts(d) == after_first
    assert d.parser.calls == calls and len(d.storage.gets) == gets  # no read, no parse
    different = attach(d, "t1", occurrence, other.asset_ref, key="replay-key")
    assert (different.status_code, different.json()["code"]) == (400, "INVALID_IDEMPOTENCY_KEY")
    assert counts(d) == after_first


def test_the_same_asset_with_a_new_key_is_a_conflict_and_a_replay_is_authorised_again(
    api: Api,
) -> None:
    d = api
    occurrence = make_occurrence(d)
    staged = stage(d, "t1", occurrence, pdf_bytes(d, "twice"), script=extraction())
    assert attach(d, "t1", occurrence, staged.asset_ref, key="k-1").status_code == 202
    after = counts(d)
    conflict = attach(d, "t1", occurrence, staged.asset_ref, key="k-2")
    assert (conflict.status_code, conflict.json()["code"]) == (409, "RESOURCE_CONFLICT")
    assert counts(d) == after
    # a replay is re-authorised: the Teacher whose assignment was revoked gets the uniform 404
    with d.sessions().begin() as db:
        db.execute(
            update(OrganizationAssignmentModel)
            .where(
                OrganizationAssignmentModel.subject == d.subjects["t1"],
                OrganizationAssignmentModel.class_id == d.classes["a1"],
            )
            .values(active=False)
        )
    gone = attach(d, "t1", occurrence, staged.asset_ref, key="k-1")
    assert gone.status_code == 404 and gone.json()["code"] == "RESOURCE_NOT_FOUND"


def test_a_replay_still_answers_after_the_occurrence_was_archived(api: Api) -> None:
    d = api
    occurrence = make_occurrence(d)
    staged = stage(d, "t1", occurrence, pdf_bytes(d, "late-replay"), script=extraction())
    first = attach(d, "t1", occurrence, staged.asset_ref, key="late")
    with d.sessions().begin() as db:
        db.execute(
            update(OCCURRENCES)
            .where(OCCURRENCES.c.occurrence_id == occurrence)
            .values(state="ARCHIVED")
        )
    again = attach(d, "t1", occurrence, staged.asset_ref, key="late")
    assert again.status_code == 202 and again.json() == first.json()


def _hold_parse(d: Api, parties: int) -> Barrier:
    return Barrier(parties, timeout=30)


def test_two_concurrent_attaches_of_one_asset_make_one_document_and_one_conflict(api: Api) -> None:
    d = api
    occurrence = make_occurrence(d)
    barrier = _hold_parse(d, 2)

    def meet(_file: Any, _extension: str) -> LessonDocumentExtraction:
        barrier.wait()  # both requests parsed before either one writes
        return extraction()

    staged = stage(d, "t1", occurrence, pdf_bytes(d, "race"), script=meet)
    before = counts(d)
    with ThreadPoolExecutor(2) as pool:
        futures = [
            pool.submit(attach, d, "t1", occurrence, staged.asset_ref, key=f"race-{index}")
            for index in range(2)
        ]
        results = [future.result(timeout=60) for future in futures]
    assert sorted(result.status_code for result in results) == [202, 409]
    loser = next(result for result in results if result.status_code == 409)
    assert loser.json()["code"] == "RESOURCE_CONFLICT"
    after = counts(d)
    assert after["documents"] == before["documents"] + 1
    assert after["jobs"] == before["jobs"] + 1 and after["outbox"] == before["outbox"]
    assert after["receipts"] == before["receipts"] + 1  # no orphan job, revision or receipt


def test_two_concurrent_attaches_with_one_key_return_the_same_202(api: Api) -> None:
    d = api
    occurrence = make_occurrence(d)
    barrier = _hold_parse(d, 2)

    def meet(_file: Any, _extension: str) -> LessonDocumentExtraction:
        barrier.wait()
        return extraction()

    staged = stage(d, "t1", occurrence, pdf_bytes(d, "same-key"), script=meet)
    before = counts(d)
    with ThreadPoolExecutor(2) as pool:
        futures = [
            pool.submit(attach, d, "t1", occurrence, staged.asset_ref, key="one-key")
            for _ in range(2)
        ]
        results = [future.result(timeout=60) for future in futures]
    assert [result.status_code for result in results] == [202, 202]
    assert results[0].json() == results[1].json()
    after = counts(d)
    assert after["documents"] == before["documents"] + 1 and after["jobs"] == before["jobs"] + 1


# ----------------------------------------------------------------------------- locks and limits
def test_a_slow_parse_holds_no_row_lock_and_does_not_block_another_attach(api: Api) -> None:
    d = api
    occurrence = make_occurrence(d)
    started, release = Event(), Event()

    def slow(_file: Any, _extension: str) -> LessonDocumentExtraction:
        started.set()
        assert release.wait(timeout=30)
        return extraction("Tiêu đề: bản chậm")

    slow_asset = stage(d, "t1", occurrence, pdf_bytes(d, "slow"), script=slow)
    quick_asset = stage(d, "t1", occurrence, pdf_bytes(d, "quick"), script=extraction("nhanh"))
    with ThreadPoolExecutor(1) as pool:
        pending = pool.submit(attach, d, "t1", occurrence, slow_asset.asset_ref)
        assert started.wait(timeout=30)
        # while the first request parses: the occurrence and session rows are not locked ...
        with d.sessions().begin() as db:
            db.execute(
                select(OCCURRENCES.c.occurrence_id)
                .where(OCCURRENCES.c.occurrence_id == occurrence)
                .with_for_update(nowait=True)
            ).all()
            db.execute(
                select(UPLOAD_SESSIONS.c.upload_session_id)
                .where(UPLOAD_SESSIONS.c.upload_session_id == slow_asset.upload_id)
                .with_for_update(nowait=True)
            ).all()
        # ... no connection sits idle in a transaction on behalf of the slow request ...
        with d.sessions()() as db:
            idle = db.scalar(
                text(
                    "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database() "
                    "AND state = 'idle in transaction' AND pid <> pg_backend_pid()"
                )
            )
        assert idle == 0
        # ... and another attach on the same occurrence completes meanwhile
        quick = attach(d, "t1", occurrence, quick_asset.asset_ref)
        assert quick.status_code == 202
        release.set()
        slow_response = pending.result(timeout=60)
    assert slow_response.status_code == 202
    assert len(get(d, "t1", doc_url(occurrence)).json()["items"]) == 2


def test_a_parse_over_the_deadline_is_refused_and_a_busy_parser_is_a_retryable_503(
    api: Api,
) -> None:
    d = api
    occurrence = make_occurrence(d)
    release = Event()

    def stuck(_file: Any, _extension: str) -> LessonDocumentExtraction:
        assert release.wait(timeout=30)
        return extraction()

    d.app.state.lesson_document_parse_gate = ParseGate(
        max_concurrent=1, queue_wait_seconds=0.2, deadline_seconds=0.3
    )
    stuck_asset = stage(d, "t1", occurrence, pdf_bytes(d, "stuck"), script=stuck)
    fine = stage(d, "t1", occurrence, pdf_bytes(d, "fine"), script=extraction())
    before = counts(d)
    timeout = attach(d, "t1", occurrence, stuck_asset.asset_ref)
    assert (timeout.status_code, timeout.json()["code"]) == (400, "INVALID_FILE_CONTENT")
    busy = attach(d, "t1", occurrence, fine.asset_ref)
    assert (busy.status_code, busy.json()["code"]) == (503, "PROVIDER_UNAVAILABLE")
    assert busy.headers["Retry-After"] == "5" and busy.json()["retryable"] is True
    assert counts(d) == before
    release.set()
    for _ in range(100):
        retry = attach(d, "t1", occurrence, fine.asset_ref)
        if retry.status_code == 202:
            break
        time.sleep(0.05)
    assert retry.status_code == 202


# ----------------------------------------------------------------------------- atomicity
def test_a_failure_after_the_job_row_rolls_back_every_row(api: Api) -> None:
    d = api
    occurrence = make_occurrence(d)
    staged = stage(d, "t1", occurrence, pdf_bytes(d, "atomic"), script=extraction())

    class ExplodingRecorder:
        def __init__(self, db: Any) -> None:
            from sketch2life.infrastructure.ai_jobs.inline_recorder import SqlInlineJobRecorder

            self.inner = SqlInlineJobRecorder(db.connection())

        def record_succeeded(self, job: Any) -> None:
            self.inner.record_succeeded(job)
            raise RuntimeError("synthetic failure after the job insert")

    def broken_service(db: Any = Depends(get_db)) -> OccurrenceDocumentService:  # noqa: B008
        return OccurrenceDocumentService(
            db,
            storage=d.storage,
            parser=d.parser,
            gate=d.app.state.lesson_document_parse_gate,
            recorder_factory=lambda session: ExplodingRecorder(session),
        )

    d.app.dependency_overrides[get_document_service] = broken_service
    before = counts(d)
    quiet = TestClient(d.app, raise_server_exceptions=False)
    response = quiet.post(
        doc_url(occurrence),
        json={"asset_ref": staged.asset_ref},
        headers=headers(d.subjects["t1"], uuid4().hex),
    )
    assert response.status_code == 500 and response.json()["code"] == "INTERNAL_SERVER_ERROR"
    assert counts(d) == before  # document, revision, job, attempt, audit and receipt: all gone
    d.app.dependency_overrides.pop(get_document_service)
    assert attach(d, "t1", occurrence, staged.asset_ref).status_code == 202


def test_the_finished_job_is_invisible_to_the_dispatch_and_reconciler_queries(api: Api) -> None:
    d = api
    occurrence = make_occurrence(d)
    body, _ = attach_ok(d, occurrence, pdf_bytes(d, "sweep"), script=extraction())
    far_future = datetime.now(UTC) + timedelta(days=30)
    repository = build_read_only_job_repository(d.engine)
    with repository.transaction() as tx:
        assert tx.queued_dispatched_not_started(far_future, timedelta(0), 1000) == ()
        assert tx.overdue_running(far_future, 1000) == ()
        assert tx.due_retries(far_future, 1000) == ()
        assert not tx.has_pending_dispatch(f"{body['job']['job_id']}-a1")
        job = tx.get_job(body["job"]["job_id"])
    assert job is not None and job.state.value == "succeeded" and job.is_terminal
    assert job.retry_not_before is None and len(job.attempts) == 1
    with d.sessions()() as db:
        pending = db.scalar(
            text("SELECT count(*) FROM ai_jobs.outbox WHERE attempt_id = :a"),
            {"a": f"{body['job']['job_id']}-a1"},
        )
    assert pending == 0


# ----------------------------------------------------------------------------- job reads
def test_the_responsible_teacher_and_the_other_teacher_of_the_class_read_the_finished_job(
    api: Api,
) -> None:
    d = api
    occurrence = make_occurrence(d)
    body, _ = attach_ok(d, occurrence, pdf_bytes(d, "jobread"), script=extraction())
    job_id, document_id = body["job"]["job_id"], body["source_document_id"]
    revisions = revision_rows(d, document_id)
    for who in ("t1", "t4"):
        response = job(d, who, job_id)
        assert response.status_code == 200, (who, response.text)
        read = response.json()
        assert read["job_id"] == job_id
        assert read["target_kind"] == "LESSON_SOURCE_DOCUMENT" and read["target_ref"] == document_id
        assert read["state"] == "succeeded" and read["result_disposition"] == "accepted"
        assert read["job_revision"] == 3 and read["attempt_number"] == 1
        assert read["target_revision"] == 1 and read["poll_after_ms"] is None
        assert read["failure"] is None and read["progress"]["kind"] == "unknown"
        assert read["result_refs"] == [
            {
                "artifact_ref": f"lesson-document-revision:{revisions[0]['document_revision_id']}",
                "sha256": revisions[0]["extracted_text_hash"],
            }
        ]
        text_body = json.dumps(read).lower()
        assert "extracted_text" not in text_body and not any(w in text_body for w in LEAK_WORDS)
    etag = job(d, "t1", job_id).headers["ETag"]
    assert job(d, "t1", job_id, **{"If-None-Match": etag}).status_code == 304
    assert job(d, "t1", job_id).headers["Cache-Control"] == "private, no-cache"


def test_nobody_else_reads_the_job_and_every_refusal_is_the_same_404(api: Api) -> None:
    d = api
    occurrence = make_occurrence(d)
    body, _ = attach_ok(d, occurrence, pdf_bytes(d, "jobscope"), script=extraction())
    job_id = body["job"]["job_id"]
    refused = {
        who: shape(job(d, who, job_id))
        for who in (
            "g1",  # guide of the class
            "o1",  # observer of the class
            "t2",  # teacher of another class
            "mixed",  # observer of this class and teacher of another one (T0.4-DEBT-1)
            "manager",  # School Manager (no run-content read)
            "admin_teacher",  # School Manager who teaches another class (T0.4-DEBT-1)
            "tother",  # another organization
            "parent",
            "platform",  # Platform Admin: no job status read (T0.4-DEC-3, open for the owner)
            "stranger",
            "inactive",
            "revoked",
        )
    }
    assert {value[0] for value in refused.values()} == {404}
    assert len({json.dumps(value[1], sort_keys=True) for value in refused.values()}) == 1
    assert shape(job(d, "t1", "lsd-" + uuid4().hex)) == next(iter(refused.values()))
    # the same account reads the job of the class it does teach
    other_occurrence = make_occurrence(d, "t2", "a2")
    other_body, _ = attach_ok(
        d, other_occurrence, pdf_bytes(d, "jobscope2"), who="t2", script=extraction()
    )
    other_job = other_body["job"]["job_id"]
    assert job(d, "mixed", other_job).status_code == 200
    assert job(d, "admin_teacher", other_job).status_code == 404  # a School Manager account
    assert job(d, "mixed", job_id).status_code == 404
    assert job(d, "admin_teacher", job_id).status_code == 404
    assert job(d, "manager", other_job).status_code == 404


def test_revoking_the_assignment_turns_the_job_read_into_a_404_even_with_an_etag(api: Api) -> None:
    d = api
    occurrence = make_occurrence(d)
    body, _ = attach_ok(d, occurrence, pdf_bytes(d, "revoke"), script=extraction())
    job_id = body["job"]["job_id"]
    first = job(d, "t4", job_id)
    assert first.status_code == 200
    with d.sessions().begin() as db:
        db.execute(
            update(OrganizationAssignmentModel)
            .where(
                OrganizationAssignmentModel.subject == d.subjects["t4"],
                OrganizationAssignmentModel.class_id == d.classes["a1"],
            )
            .values(active=False)
        )
    gone = job(d, "t4", job_id, **{"If-None-Match": first.headers["ETag"]})
    assert gone.status_code == 404 and gone.json()["code"] == "RESOURCE_NOT_FOUND"
    assert job(d, "t1", job_id).status_code == 200


def test_a_class_that_is_no_longer_active_gives_no_job_read(api: Api) -> None:
    d = api
    occurrence = make_occurrence(d, "t2", "a2")
    body, _ = attach_ok(
        d, occurrence, pdf_bytes(d, "inactive-class"), who="t2", script=extraction()
    )
    job_id = body["job"]["job_id"]
    assert job(d, "t2", job_id).status_code == 200
    with d.sessions().begin() as db:
        db.execute(
            update(ClassroomModel)
            .where(ClassroomModel.class_id == d.classes["a2"])
            .values(state="archived")
        )
    assert job(d, "t2", job_id).status_code == 404


def test_the_other_job_types_stay_unregistered(api: Api) -> None:
    d = api
    occurrence = make_occurrence(d)
    body, _ = attach_ok(d, occurrence, pdf_bytes(d, "typecheck"), script=extraction())
    job_id = body["job"]["job_id"]
    with d.sessions().begin() as db:
        db.execute(
            text("UPDATE ai_jobs.job SET job_type = 'vision_analysis' WHERE job_id = :id"),
            {"id": job_id},
        )
    assert job(d, "t1", job_id).status_code == 404


# ----------------------------------------------------------------------------- reads
def test_the_document_reads_authorise_like_the_occurrence_and_never_show_storage_words(
    api: Api,
) -> None:
    d = api
    occurrence = make_occurrence(d)
    other = make_occurrence(d, title="Bài 2")
    body, staged = attach_ok(d, occurrence, pdf_bytes(d, "reads"), script=extraction())
    document_id = body["source_document_id"]
    urls = [
        doc_url(occurrence),
        doc_url(occurrence, document_id),
        doc_url(occurrence, document_id, "/revisions"),
        doc_url(occurrence, document_id, "/revisions/1"),
    ]
    for who in ("t1", "t4", "g1", "o1"):  # the read guard of T-3a-DEC-3
        for url in urls:
            response = get(d, who, url)
            assert response.status_code == 200, (who, url, response.text)
            lowered = response.text.lower()
            assert not any(word in lowered for word in LEAK_WORDS), (url, lowered[:200])
            assert staged.key not in response.text and staged.asset_ref not in response.text
    refusals = {
        shape(get(d, who, url))[0]
        for who in (
            "t2",
            "manager",
            "parent",
            "platform",
            "stranger",
            "tother",
            "inactive",
            "revoked",
        )
        for url in urls
    }
    assert refusals == {404}
    bodies = {
        json.dumps(shape(get(d, who, url))[1], sort_keys=True)
        for who in ("t2", "manager", "parent", "stranger", "tother")
        for url in urls
    }
    assert len(bodies) == 1
    # a document is only reachable through its own occurrence
    assert get(d, "t1", doc_url(other, document_id)).status_code == 404
    assert get(d, "t1", doc_url(other, document_id, "/revisions/1")).status_code == 404
    assert get(d, "t1", doc_url(occurrence, str(uuid4()))).status_code == 404
    assert get(d, "t1", doc_url(occurrence, document_id, "/revisions/2")).status_code == 404
    assert get(d, "t1", doc_url(occurrence, "x" * 40)).status_code == 404


def test_the_document_read_shape_and_the_strong_etags(api: Api) -> None:
    d = api
    occurrence = make_occurrence(d)
    body, _ = attach_ok(
        d, occurrence, pdf_bytes(d, "shape"), script=extraction(pages=3, coverage=(1, 3))
    )
    document_id = body["source_document_id"]
    response = get(d, "t1", doc_url(occurrence, document_id))
    document = response.json()
    assert set(document) == {
        "contract",
        "source_document_id",
        "occurrence_id",
        "file_name",
        "file_extension",
        "page_or_slide_count",
        "document_state",
        "head_revision_no",
        "job_ref",
        "warnings",
        "page_coverage",
        "uploaded_at",
    }
    assert document["job_ref"] == body["job"]["job_id"] and document["head_revision_no"] == 1
    assert document["file_name"] == "giao-an.pdf" and document["document_state"] == "EXTRACTED"
    assert response.headers["ETag"] == '"1"'
    assert (
        get(d, "t1", doc_url(occurrence, document_id), **{"If-None-Match": '"1"'}).status_code
        == 304
    )
    assert (
        get(d, "t1", doc_url(occurrence, document_id), **{"If-None-Match": '"2"'}).status_code
        == 200
    )
    # a stranger never gets a 304
    assert (
        get(d, "stranger", doc_url(occurrence, document_id), **{"If-None-Match": '"1"'}).status_code
        == 404
    )
    revision = get(d, "t1", doc_url(occurrence, document_id, "/revisions/1"))
    detail = revision.json()
    assert set(detail) == {
        "contract",
        "source_document_id",
        "revision_no",
        "origin",
        "review_state",
        "base_revision_no",
        "extracted_text",
        "text_hash",
        "text_length",
        "parser",
        "warnings",
        "page_coverage",
        "created_at",
    }
    assert detail["parser"] == {"name": "t3b-scripted", "version": "1.2.3"}
    assert detail["origin"] == "EXTRACTION" and detail["review_state"] == "NEEDS_REVIEW"
    etag = f'"{detail["text_hash"]}.NEEDS_REVIEW"'
    assert revision.headers["ETag"] == etag
    assert (
        get(
            d, "t1", doc_url(occurrence, document_id, "/revisions/1"), **{"If-None-Match": etag}
        ).status_code
        == 304
    )
    # the review stamp changes without the text changing: the validator moves with it
    with d.sessions().begin() as db:
        db.execute(
            text(
                "UPDATE lesson.document_revisions SET review_state = 'CONFIRMED', "
                "reviewed_by = :a, reviewed_at = now() WHERE source_document_id = :d"
            ),
            {"a": d.accounts["t1"], "d": document_id},
        )
    refreshed = get(
        d, "t1", doc_url(occurrence, document_id, "/revisions/1"), **{"If-None-Match": etag}
    )
    assert refreshed.status_code == 200
    assert refreshed.headers["ETag"] == f'"{detail["text_hash"]}.CONFIRMED"'


def test_lists_page_newest_first_without_gaps_and_revisions_hide_their_text(api: Api) -> None:
    d = api
    occurrence = make_occurrence(d)
    ids: list[str] = []
    for index in range(3):
        body, _ = attach_ok(
            d, occurrence, pdf_bytes(d, f"page{index}"), script=extraction(f"bản {index}")
        )
        ids.append(body["source_document_id"])
    first = get(d, "t1", doc_url(occurrence) + "?limit=2").json()
    assert [item["source_document_id"] for item in first["items"]] == [ids[2], ids[1]]
    assert first["next_cursor"]
    second = get(d, "t1", doc_url(occurrence) + f"?limit=2&cursor={first['next_cursor']}").json()
    assert [item["source_document_id"] for item in second["items"]] == [ids[0]]
    assert second["next_cursor"] is None
    assert get(d, "t1", doc_url(occurrence) + "?limit=101").status_code == 400
    bad = get(d, "t1", doc_url(occurrence) + "?cursor=zzzz")
    assert bad.status_code == 400
    assert bad.json()["field_errors"] == [{"field": "cursor", "code": "INVALID_FORMAT"}]
    # a revision cursor is not a document cursor
    revision_cursor = get(d, "t1", doc_url(occurrence, ids[0], "/revisions")).json()
    assert revision_cursor["next_cursor"] is None

    # revision 2 (a Teacher edit row, as T-3c will write it): newest first, text never listed
    edited = "bản sửa của giáo viên"
    with d.sessions().begin() as db:
        db.execute(
            text(
                "INSERT INTO lesson.document_revisions (document_revision_id, source_document_id, "
                "revision_no, origin, base_revision_no, extracted_text, extracted_text_hash, "
                "extraction_warnings, page_coverage, created_by) VALUES (:id, :d, 2, "
                "'TEACHER_EDIT', 1, :t, :h, '[]'::jsonb, '[]'::jsonb, :a)"
            ),
            {
                "id": str(uuid4()),
                "d": ids[0],
                "t": edited,
                "h": sha(edited.encode("utf-8")),
                "a": d.accounts["t1"],
            },
        )
    listing = get(d, "t1", doc_url(occurrence, ids[0], "/revisions?limit=1")).json()
    assert [item["revision_no"] for item in listing["items"]] == [2]
    assert listing["items"][0]["origin"] == "TEACHER_EDIT"
    assert listing["items"][0]["text_length"] == len(edited)
    assert "extracted_text" not in json.dumps(listing) and edited not in json.dumps(listing)
    older = get(
        d, "t1", doc_url(occurrence, ids[0], f"/revisions?limit=1&cursor={listing['next_cursor']}")
    ).json()
    assert [item["revision_no"] for item in older["items"]] == [1]
    detail = get(d, "t1", doc_url(occurrence, ids[0], "/revisions/2")).json()
    assert detail["parser"] is None and detail["base_revision_no"] == 1
    assert detail["extracted_text"] == edited
    assert get(d, "t1", doc_url(occurrence, ids[0])).json()["head_revision_no"] == 2
    assert get(d, "t1", doc_url(occurrence, ids[0])).headers["ETag"] == '"2"'


def test_the_attach_leaves_the_occurrence_unchanged(api: Api) -> None:
    d = api
    occurrence = make_occurrence(d)
    before = get(d, "t1", f"/v1/lesson-occurrences/{occurrence}").json()
    attach_ok(d, occurrence, pdf_bytes(d, "occ"), script=extraction())
    after = get(d, "t1", f"/v1/lesson-occurrences/{occurrence}").json()
    assert after == before  # no state or revision change (T-3b-DEC-9)
