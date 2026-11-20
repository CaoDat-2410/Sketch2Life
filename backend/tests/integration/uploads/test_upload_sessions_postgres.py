"""FEAT-066 T-2a: generic upload sessions (SRS l.1654-1658, FR-C-12) on PostgreSQL.

Runs only against a disposable database whose name contains ``be1_acceptance`` and
``frc08_v3_t2a``. Object storage is the in-memory port by default; when ``T2A_S3_ENDPOINT``,
``T2A_S3_BUCKET``, ``T2A_S3_ACCESS_KEY`` and ``T2A_S3_SECRET_KEY`` are set the module runs against
the local S3Mock target, after the T-2z guard (``check_s3mock_target``: loopback, endpoint and
bucket equal to ``FRC08_ALLOWED_ENDPOINT`` and ``FRC08_ALLOWED_BUCKET``, bucket containing
``frc08`` and ``v3-t2a``, no ambient ``AWS_*`` variable). Only synthetic bytes are used; no key or
bucket is ever deleted by a fixture (the only deletes are the ones under test).
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from io import BytesIO
from threading import Barrier, Event, Lock
from time import sleep
from typing import Any
from uuid import uuid4

import pytest
from fastapi import FastAPI, Header
from fastapi.testclient import TestClient
from sqlalchemy import func, select, update

from sketch2life.application.ports.core_foundation import LifecycleScope
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.lesson_documents import (
    MalwareDetected,
    MalwareScannerUnavailable,
    MalwareScanResult,
)
from sketch2life.application.ports.object_storage import ObjectStorageFailure, StoredObject
from sketch2life.application.ports.upload_sessions import UploadScope
from sketch2life.application.ports.upload_validation import DOCX_MEDIA_TYPE
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.documents.lesson_parser import DeterministicLessonDocumentParser
from sketch2life.infrastructure.documents.local_test_adapters import (
    LocalTestSignatureMediaValidator,
)
from sketch2life.infrastructure.lesson_library.tables import UPLOAD_PARTS, UPLOAD_SESSIONS
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    Be1CommandReceiptModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.infrastructure.persistence.core_lifecycle_store import (
    SqlCoreRunAssetPurge,
    SqlCoreRunUploadClose,
    build_plan,
)
from sketch2life.infrastructure.persistence.core_models import (
    CoreAssetMetadataModel,
    CoreAuditEntryModel,
)
from sketch2life.infrastructure.story_run_lite import tables as story_tables
from sketch2life.infrastructure.uploads.resolvers import parent_scope_ref
from sketch2life.infrastructure.uploads.service import resolve_asset_key
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult
from tests.synthetic_upload_fixtures import synthetic_jpeg_prefix, synthetic_pdf, synthetic_png
from tools.local_s3mock_target import check_s3_credentials, check_s3mock_target, ensure_task_bucket
from tools.run_be1_lifecycle_consumer import TargetRefused

ISSUER = "synthetic-t2a-issuer"
TASK_TAG = "v3-t2a"
PART = 4 * 1024 * 1024
_S3_VARIABLES = ("T2A_S3_ENDPOINT", "T2A_S3_BUCKET", "T2A_S3_ACCESS_KEY", "T2A_S3_SECRET_KEY")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def png_of(size: int) -> bytes:
    """A synthetic PNG header padded with deterministic filler to ``size`` bytes."""
    header = synthetic_png()
    if size <= len(header):
        return header
    filler = (b"sketch2life-t2a-filler-" * (size // 23 + 1))[: size - len(header)]
    return header + filler


def zip_of(size: int) -> bytes:
    head = b"PK\x03\x04"
    return head + (b"synthetic-zip-t2a-" * (size // 18 + 1))[: size - len(head)]


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
        return StoredObject(BytesIO(content), len(content), content_type, {})

    def delete_object(self, key: str) -> None:
        self.objects.pop(key, None)

    def list_keys(self, prefix: str) -> tuple[str, ...]:
        return tuple(sorted(key for key in self.objects if key.startswith(prefix)))


class FaultStorage:
    """Delegating storage that records puts and can fail them or the reads on demand."""

    def __init__(self, inner: Any) -> None:
        self.inner = inner
        self.puts: list[str] = []
        self.fail_put_containing: str | None = None
        self.fail_get = False
        self._lock = Lock()

    def put_object(self, key: str, body: Any, **kwargs: Any) -> None:
        if self.fail_put_containing is not None and self.fail_put_containing in key:
            raise ObjectStorageFailure("synthetic put failure")
        with self._lock:
            self.puts.append(key)
        self.inner.put_object(key, body, **kwargs)

    def get_object(self, key: str) -> Any:
        if self.fail_get:
            raise ObjectStorageFailure("synthetic get failure")
        return self.inner.get_object(key)

    def delete_object(self, key: str) -> None:
        self.inner.delete_object(key)

    def list_keys(self, prefix: str) -> tuple[str, ...]:
        return self.inner.list_keys(prefix)


class AllowlistScanner:
    """CLEAN for registered SHA-256 digests, MalwareDetected for any other, optional outage."""

    def __init__(self) -> None:
        self.clean: set[str] = set()
        self.unavailable = False
        self.calls = 0
        self.entered = Event()
        self.gate: Event | None = None

    def scan(self, file_obj: Any) -> MalwareScanResult:
        self.calls += 1
        if self.unavailable:
            raise MalwareScannerUnavailable("synthetic outage")
        if self.gate is not None:
            self.entered.set()
            assert self.gate.wait(timeout=30)
        file_obj.seek(0)
        digest = hashlib.sha256(file_obj.read()).hexdigest()
        file_obj.seek(0)
        if digest not in self.clean:
            raise MalwareDetected("synthetic")
        return MalwareScanResult("t2a-allowlist", "1", "CLEAN")


class FakeOccurrenceResolver:
    """Stand-in for the T-3a/T-3b resolver: occurrence -> organization, assignment checked live."""

    def __init__(self, db: Any, occurrences: dict[str, str]) -> None:
        self._db = db
        self._occurrences = occurrences

    def resolve(self, principal: VerifiedPrincipal, target_ref: str) -> UploadScope | None:
        organization_id = self._occurrences.get(target_ref)
        if organization_id is None:
            return None
        assigned = self._db.scalar(
            select(OrganizationAssignmentModel.assignment_id).where(
                OrganizationAssignmentModel.organization_id == organization_id,
                OrganizationAssignmentModel.subject == principal.subject,
                OrganizationAssignmentModel.role == "teacher",
                OrganizationAssignmentModel.active.is_(True),
            )
        )
        if assigned is None:
            return None
        return UploadScope(
            "ORGANIZATION", None, organization_id, f"occurrences/{organization_id}/{target_ref}/"
        )

    def ensure_accepting(self, principal: VerifiedPrincipal, target_ref: str) -> None:
        return None


@dataclass
class UploadApi:
    app: FastAPI
    client: TestClient
    storage: FaultStorage
    scanner: AllowlistScanner
    parent: str
    other_parent: str
    teacher: str
    other_teacher: str
    organization_id: str
    occurrences: dict[str, str] = field(default_factory=dict)
    real_s3: bool = False

    def sessions(self) -> Any:
        return self.app.state.be1_runtime.session_factory


def _s3_storage() -> Any | None:
    if not all(os.environ.get(name) for name in _S3_VARIABLES):
        return None
    endpoint = os.environ["T2A_S3_ENDPOINT"]
    bucket = os.environ["T2A_S3_BUCKET"]
    access_key = os.environ["T2A_S3_ACCESS_KEY"]
    secret_key = os.environ["T2A_S3_SECRET_KEY"]
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
def api(monkeypatch: pytest.MonkeyPatch) -> Iterator[UploadApi]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL to a disposable PostgreSQL database")
    database_name = database_url.rsplit("/", 1)[-1]
    if "be1_acceptance" not in database_name or "frc08_v3_t2a" not in database_name:
        pytest.fail("BE1_TEST_DATABASE_URL must be a disposable frc08_v3_t2a*be1_acceptance db")
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
    organization_id = f"synthetic-t2a-org-{token}"
    parent, other_parent = f"synthetic-t2a-parent-{token}", f"synthetic-t2a-parent2-{token}"
    teacher, other_teacher = f"synthetic-t2a-teacher-{token}", f"synthetic-t2a-teacher2-{token}"
    with runtime.session_factory.begin() as db:
        db.add(
            OrganizationModel(
                organization_id=organization_id, display_name="Synthetic T2A", state="active"
            )
        )
        for subject, role in (
            (parent, "parent"),
            (other_parent, "parent"),
            (teacher, "teacher"),
            (other_teacher, "teacher"),
        ):
            db.add(
                AdultIdentityModel(
                    subject=subject, issuer=ISSUER, state="active", account_role=role
                )
            )
        db.flush()
        db.add(
            OrganizationAssignmentModel(
                assignment_id=str(uuid4()),
                organization_id=organization_id,
                subject=teacher,
                class_id=None,
                role="teacher",
                active=True,
            )
        )

    async def verified(
        x_test_principal: str = Header(alias="X-Test-Principal"),
    ) -> VerifiedPrincipal:
        return VerifiedPrincipal(subject=x_test_principal, issuer=ISSUER, roles=frozenset())

    s3 = _s3_storage()
    storage = FaultStorage(s3 if s3 is not None else InMemoryStorage())
    scanner = AllowlistScanner()
    occurrences: dict[str, str] = {}
    app.state.lesson_library_storage = storage
    app.state.lesson_document_scanner = scanner
    app.state.lesson_document_parser = DeterministicLessonDocumentParser()
    app.state.upload_media_validator = LocalTestSignatureMediaValidator(env="test")
    app.dependency_overrides[get_verified_adult] = verified
    try:
        with TestClient(app) as client:
            yield UploadApi(
                app, client, storage, scanner, parent, other_parent, teacher, other_teacher,
                organization_id, occurrences, real_s3=s3 is not None,
            )
    finally:
        app.dependency_overrides.clear()
        runtime.engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


# ----------------------------------------------------------------------------- helpers
def register_occurrence_resolver(api: UploadApi) -> None:
    occurrences = api.occurrences
    api.app.state.upload_target_resolver_factories = {
        "OCCURRENCE_DOCUMENT": lambda db: FakeOccurrenceResolver(db, occurrences)
    }


def principal_of(subject: str) -> VerifiedPrincipal:
    return VerifiedPrincipal(subject=subject, issuer=ISSUER, roles=frozenset())


def new_run(api: UploadApi, owner: str, state: str = "INPUT_PROCESSING") -> str:
    run_id = str(uuid4())
    now = datetime.now(UTC)
    with api.sessions().begin() as db:
        db.execute(
            story_tables.story_runs.insert().values(
                run_id=run_id,
                actor_scope_kind="PARENT_ACCOUNT",
                actor_scope_ref=parent_scope_ref(principal_of(owner)),
                profile_ref=str(uuid4()),
                run_state=state,
                revision=2,
                version=2,
                created_at=now,
                updated_at=now,
            )
        )
    return run_id


def set_run_state(api: UploadApi, run_id: str, state: str) -> None:
    with api.sessions().begin() as db:
        db.execute(
            update(story_tables.story_runs)
            .where(story_tables.story_runs.c.run_id == run_id)
            .values(run_state=state)
        )


def headers(subject: str, key: str | None = None, **extra: str) -> dict[str, str]:
    result = {"X-Test-Principal": subject}
    if key is not None:
        result["Idempotency-Key"] = key
    result.update(extra)
    return result


def create(
    api: UploadApi,
    subject: str,
    run_id: str,
    data: bytes,
    *,
    media_type: str = "image/png",
    key: str | None = None,
    purpose: str = "RUN_ARTWORK",
    file_name: str | None = None,
    **overrides: Any,
) -> Any:
    body: dict[str, Any] = {
        "purpose": purpose,
        "target_ref": run_id,
        "media_type": media_type,
        "expected_size_bytes": len(data),
        "expected_sha256": sha(data),
    }
    if file_name is not None:
        body["file_name"] = file_name
    body.update(overrides)
    return api.client.post(
        "/v1/upload-sessions", json=body, headers=headers(subject, key or uuid4().hex)
    )


def put_part(
    api: UploadApi,
    subject: str,
    upload_id: str,
    number: int,
    chunk: bytes,
    *,
    part_sha: str | None = None,
    content_type: str = "application/octet-stream",
) -> Any:
    return api.client.put(
        f"/v1/upload-sessions/{upload_id}/parts/{number}",
        content=chunk,
        headers=headers(
            subject, **{"X-Part-SHA256": part_sha or sha(chunk), "Content-Type": content_type}
        ),
    )


def complete(
    api: UploadApi,
    subject: str,
    upload_id: str,
    data: bytes,
    *,
    key: str | None = None,
    size: int | None = None,
    digest: str | None = None,
) -> Any:
    return api.client.post(
        f"/v1/upload-sessions/{upload_id}/complete",
        json={
            "expected_size_bytes": len(data) if size is None else size,
            "expected_sha256": digest or sha(data),
        },
        headers=headers(subject, key or uuid4().hex),
    )


def abort(
    api: UploadApi, subject: str, upload_id: str, etag: str | None, key: str | None = None
) -> Any:
    extra = {} if etag is None else {"If-Match": etag}
    return api.client.delete(
        f"/v1/upload-sessions/{upload_id}", headers=headers(subject, key or uuid4().hex, **extra)
    )


def get_session(api: UploadApi, subject: str, upload_id: str) -> Any:
    return api.client.get(f"/v1/upload-sessions/{upload_id}", headers=headers(subject))


def chunks_of(data: bytes) -> list[bytes]:
    return [data[offset : offset + PART] for offset in range(0, len(data), PART)]


def upload_parts(api: UploadApi, subject: str, upload_id: str, data: bytes) -> None:
    for number, chunk in enumerate(chunks_of(data), start=1):
        response = put_part(api, subject, upload_id, number, chunk)
        assert response.status_code == 200, response.text


def full_upload(
    api: UploadApi,
    subject: str,
    run_id: str,
    data: bytes,
    *,
    media_type: str = "image/png",
    allow: bool = True,
    **create_args: Any,
) -> tuple[str, Any]:
    if allow:
        api.scanner.clean.add(sha(data))
    created = create(api, subject, run_id, data, media_type=media_type, **create_args)
    assert created.status_code == 201, created.text
    upload_id = created.json()["upload_id"]
    upload_parts(api, subject, upload_id, data)
    return upload_id, complete(api, subject, upload_id, data)


def session_row(api: UploadApi, upload_id: str) -> Any:
    with api.sessions()() as db:
        return (
            db.execute(
                select(UPLOAD_SESSIONS).where(UPLOAD_SESSIONS.c.upload_session_id == upload_id)
            )
            .mappings()
            .one()
        )


def part_count(api: UploadApi, upload_id: str) -> int:
    with api.sessions()() as db:
        return int(
            db.scalar(
                select(func.count())
                .select_from(UPLOAD_PARTS)
                .where(UPLOAD_PARTS.c.upload_session_id == upload_id)
            )
            or 0
        )


def asset_rows(api: UploadApi, source_ref: str) -> list[Any]:
    with api.sessions()() as db:
        rows = db.scalars(select(CoreAssetMetadataModel)).all()
        return [row for row in rows if source_ref in row.source_refs]


def chunk_keys(api: UploadApi, prefix: str, upload_id: str) -> tuple[str, ...]:
    return api.storage.list_keys(f"{prefix}upload/{upload_id}/")


def code_of(response: Any) -> str:
    return str(response.json()["code"])


# ----------------------------------------------------------------------------- happy path
def test_artwork_upload_completes_and_creates_a_scoped_asset(api: UploadApi) -> None:
    run_id = new_run(api, api.parent)
    data = png_of(2048)
    api.scanner.clean.add(sha(data))
    created = create(api, api.parent, run_id, data, key="k-create-1")
    assert created.status_code == 201, created.text
    body = created.json()
    assert set(body) == {
        "contract", "upload_id", "purpose", "target_ref", "state", "part_size_bytes",
        "expected_parts", "accepted_parts", "byte_count", "expires_at", "revision", "asset_ref",
        "asset_state", "error_code",
    }
    assert body["state"] == "OPEN" and body["revision"] == 1 and body["byte_count"] == 0
    assert body["part_size_bytes"] == PART and body["expected_parts"] == 1
    assert created.headers["ETag"] == '"1"'
    upload_id = body["upload_id"]

    receipt = put_part(api, api.parent, upload_id, 1, data)
    assert receipt.status_code == 200, receipt.text
    assert receipt.json() == {
        "contract": "GenericUploadPartReceiptV1", "upload_id": upload_id, "part_no": 1,
        "byte_length": len(data), "sha256": sha(data), "accepted": True,
        "accepted_part_count": 1, "byte_count": len(data), "revision": 2,
    }
    assert receipt.headers["ETag"] == '"2"'

    done = complete(api, api.parent, upload_id, data, key="k-complete-1")
    assert done.status_code == 202, done.text
    result = done.json()
    assert result["state"] == "COMPLETED" and result["asset_state"] == "READY"
    assert result["scanner_name"] == "t2a-allowlist" and result["scanner_version"] == "1"
    # SRS l.1692: the client gets an opaque handle; the physical key stays server side.
    assert result["asset_ref"] == f"upl_{upload_id}"
    assert "parent/" not in result["asset_ref"] and run_id not in result["asset_ref"]
    asset_ref = session_row(api, upload_id)["final_asset_ref"]
    assert asset_ref.startswith(f"parent/{run_id}/") and asset_ref.endswith("/original")
    assert done.headers["ETag"] == '"3"'

    stored = api.storage.get_object(asset_ref)
    assert stored is not None and stored.body.read() == data
    assert chunk_keys(api, f"parent/{run_id}/", upload_id) == ()
    (asset,) = asset_rows(api, run_id)
    assert (asset.asset_ref, asset.asset_version) == (asset_ref, 1)
    assert asset.owner_scope_kind == "PARENT_ACCOUNT" and asset.organization_id is None
    assert asset.owner_scope_ref == parent_scope_ref(principal_of(api.parent))
    assert asset.source_refs == [run_id] and asset.content_sha256 == sha(data)
    row = session_row(api, upload_id)
    assert row["state"] == "COMPLETED" and row["final_asset_ref"] == asset_ref
    with api.sessions()() as db:
        scope = parent_scope_ref(principal_of(api.parent))
        assert resolve_asset_key(
            db, result["asset_ref"], owner_scope_kind="PARENT_ACCOUNT",
            owner_scope_ref=scope, organization_id=None,
        ) == asset_ref
        assert resolve_asset_key(
            db, result["asset_ref"], owner_scope_kind="PARENT_ACCOUNT",
            owner_scope_ref=parent_scope_ref(principal_of(api.other_parent)), organization_id=None,
        ) is None
        assert resolve_asset_key(
            db, asset_ref, owner_scope_kind="PARENT_ACCOUNT",
            owner_scope_ref=scope, organization_id=None,
        ) is None  # the physical key is not a handle
    assert (row["scan_verdict"], row["scanner_name"], row["validated_at"] is not None) == (
        "CLEAN", "t2a-allowlist", True,
    )
    assert row["owner_principal_ref"] == api.parent and row["organization_id"] is None
    assert row["owner_scope_kind"] == "PARENT_ACCOUNT"
    with api.sessions()() as db:
        audit = db.scalars(
            select(CoreAuditEntryModel).where(CoreAuditEntryModel.resource_id == upload_id)
        ).all()
    assert [entry.action for entry in audit] == ["upload.complete"]
    assert audit[0].actor_ref == parent_scope_ref(principal_of(api.parent))  # no raw subject

    status = get_session(api, api.parent, upload_id)
    assert status.status_code == 200
    assert status.json()["asset_ref"] == result["asset_ref"]
    assert status.json()["state"] == "COMPLETED"

    replay = complete(api, api.parent, upload_id, data, key="k-complete-1")
    assert replay.status_code == 202 and replay.json() == result
    assert len(asset_rows(api, run_id)) == 1
    other_key = complete(api, api.parent, upload_id, data, key="k-complete-2")
    assert other_key.status_code == 409 and code_of(other_key) == "UPLOAD_SESSION_STATE_CONFLICT"


def test_webp_and_jpeg_are_accepted_for_artwork_and_20_mib_is_five_parts(api: UploadApi) -> None:
    run_id = new_run(api, api.parent)
    webp = b"RIFF" + (20).to_bytes(4, "little") + b"WEBP" + b"VP8 " + b"synthetic-t2a"
    upload_id, done = full_upload(api, api.parent, run_id, webp, media_type="image/webp")
    assert done.status_code == 202, done.text
    jpeg = synthetic_jpeg_prefix()
    _, done = full_upload(
        api, api.parent, new_run(api, api.parent), jpeg, media_type="image/jpeg"
    )
    assert done.status_code == 202, done.text
    big = create(
        api, api.parent, new_run(api, api.parent), b"x", expected_size_bytes=20 * 1024 * 1024
    )
    assert big.status_code == 201 and big.json()["expected_parts"] == 5


def test_resume_after_a_partial_upload_with_out_of_order_parts(api: UploadApi) -> None:
    run_id = new_run(api, api.parent)
    data = png_of(PART + 1000)
    api.scanner.clean.add(sha(data))
    upload_id = create(api, api.parent, run_id, data).json()["upload_id"]
    first, second = chunks_of(data)
    assert put_part(api, api.parent, upload_id, 2, second).status_code == 200
    early = complete(api, api.parent, upload_id, data)
    assert early.status_code == 422 and code_of(early) == "UPLOAD_INCOMPLETE"
    assert session_row(api, upload_id)["state"] == "OPEN"  # retryable: resume is possible
    status = get_session(api, api.parent, upload_id).json()
    assert [part["part_no"] for part in status["accepted_parts"]] == [2]
    assert status["byte_count"] == len(second) and status["revision"] == 2
    assert put_part(api, api.parent, upload_id, 1, first).status_code == 200
    done = complete(api, api.parent, upload_id, data)
    assert done.status_code == 202, done.text
    stored = api.storage.get_object(session_row(api, upload_id)["final_asset_ref"])
    assert stored is not None and stored.body.read() == data


# ----------------------------------------------------------------------------- parts
def test_part_retry_conflict_checksum_length_and_bounds(api: UploadApi) -> None:
    run_id = new_run(api, api.parent)
    data = png_of(PART + 10)
    upload_id = create(api, api.parent, run_id, data).json()["upload_id"]
    first, second = chunks_of(data)
    receipt = put_part(api, api.parent, upload_id, 1, first)
    puts_before = len(api.storage.puts)
    again = put_part(api, api.parent, upload_id, 1, first)
    assert again.status_code == 200 and again.json() == receipt.json()
    assert len(api.storage.puts) == puts_before  # no second storage write
    other = b"\x00" * len(first)
    conflict = put_part(api, api.parent, upload_id, 1, other)
    assert conflict.status_code == 409 and code_of(conflict) == "UPLOAD_PART_CONFLICT"
    mismatch = put_part(api, api.parent, upload_id, 2, second, part_sha="a" * 64)
    assert mismatch.status_code == 422 and code_of(mismatch) == "UPLOAD_CHECKSUM_MISMATCH"
    short = put_part(api, api.parent, upload_id, 2, second[:-1])
    assert short.status_code == 400 and code_of(short) == "INVALID_REQUEST"
    assert short.json()["field_errors"] == [{"field": "body", "code": "INVALID_FORMAT"}]
    out_of_range = put_part(api, api.parent, upload_id, 3, second)
    assert out_of_range.status_code == 400
    assert out_of_range.json()["field_errors"] == [{"field": "part_no", "code": "OUT_OF_RANGE"}]
    zero = put_part(api, api.parent, upload_id, 0, second)
    assert zero.status_code == 400
    bad_header = api.client.put(
        f"/v1/upload-sessions/{upload_id}/parts/2",
        content=second,
        headers=headers(
            api.parent, **{"X-Part-SHA256": "xyz", "Content-Type": "application/octet-stream"}
        ),
    )
    assert bad_header.status_code == 400
    assert bad_header.json()["field_errors"] == [
        {"field": "X-Part-SHA256", "code": "INVALID_FORMAT"}
    ]
    missing_header = api.client.put(
        f"/v1/upload-sessions/{upload_id}/parts/2",
        content=second,
        headers=headers(api.parent, **{"Content-Type": "application/octet-stream"}),
    )
    assert missing_header.status_code == 400
    wrong_type = put_part(api, api.parent, upload_id, 2, second, content_type="image/png")
    assert wrong_type.status_code == 415
    oversize = put_part(api, api.parent, upload_id, 2, b"\x00" * (PART + 1))
    assert oversize.status_code == 413 and code_of(oversize) == "MEDIA_TOO_LARGE"
    assert part_count(api, upload_id) == 1


def test_concurrent_same_part_retries_store_one_object_and_equal_receipts(api: UploadApi) -> None:
    run_id = new_run(api, api.parent)
    data = png_of(3000)
    upload_id = create(api, api.parent, run_id, data).json()["upload_id"]
    barrier = Barrier(2)

    def attempt(_: int) -> Any:
        barrier.wait()
        return put_part(api, api.parent, upload_id, 1, data)

    with ThreadPoolExecutor(max_workers=2) as pool:
        first, second = list(pool.map(attempt, range(2)))
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert part_count(api, upload_id) == 1
    part_puts = [key for key in api.storage.puts if f"/upload/{upload_id}/parts/1" in key]
    assert len(part_puts) == 1


def test_concurrent_different_hash_for_one_part_yields_one_conflict(api: UploadApi) -> None:
    run_id = new_run(api, api.parent)
    data = png_of(3000)
    upload_id = create(api, api.parent, run_id, data).json()["upload_id"]
    variants = [data, b"\x01" * len(data)]
    barrier = Barrier(2)

    def attempt(index: int) -> Any:
        barrier.wait()
        return put_part(api, api.parent, upload_id, 1, variants[index])

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt, range(2)))
    assert sorted(response.status_code for response in results) == [200, 409]
    assert part_count(api, upload_id) == 1


# ----------------------------------------------------------------------------- scope
def test_other_actors_and_scopes_get_the_uniform_404(api: UploadApi) -> None:
    run_id = new_run(api, api.parent)
    data = png_of(500)
    upload_id = create(api, api.parent, run_id, data).json()["upload_id"]
    put_part(api, api.parent, upload_id, 1, data)
    reference = get_session(api, api.parent, "00000000-0000-0000-0000-000000000000")
    assert reference.status_code == 404 and code_of(reference) == "RESOURCE_NOT_FOUND"
    for subject in (api.other_parent, api.teacher, api.other_teacher, "ghost-subject"):
        responses = [
            get_session(api, subject, upload_id),
            put_part(api, subject, upload_id, 1, data),
            complete(api, subject, upload_id, data),
            abort(api, subject, upload_id, '"2"'),
        ]
        for response in responses:
            assert response.status_code == 404, (subject, response.text)
            assert code_of(response) == "RESOURCE_NOT_FOUND"
    # Create: another parent's run, an unknown run, a malformed ref, and a Teacher for artwork.
    assert create(api, api.other_parent, run_id, data).status_code == 404
    assert create(api, api.parent, str(uuid4()), data).status_code == 404
    assert create(api, api.parent, "not-a-run", data).status_code == 404
    assert create(api, api.teacher, run_id, data).status_code == 404
    # Nothing leaked into the owner's session.
    assert get_session(api, api.parent, upload_id).json()["accepted_parts"][0]["part_no"] == 1


def test_lesson_and_generic_sessions_are_invisible_to_each_other(api: UploadApi) -> None:
    run_id = new_run(api, api.parent)
    data = png_of(300)
    generic_id = create(api, api.parent, run_id, data).json()["upload_id"]
    lesson_id = str(uuid4())
    with api.sessions().begin() as db:
        db.execute(
            UPLOAD_SESSIONS.insert().values(
                upload_session_id=lesson_id,
                organization_id=api.organization_id,
                owner_principal_ref=api.teacher,
                purpose="LESSON_SOURCE",
                target_ref=str(uuid4()),
                safe_file_name="plan.pdf",
                expected_media_type="application/pdf",
                expected_size_bytes=10,
                expected_sha256="a" * 64,
                chunk_size_bytes=PART,
                expected_parts=1,
                state="OPEN",
                expires_at=datetime.now(UTC) + timedelta(hours=1),
            )
        )
    assert get_session(api, api.teacher, lesson_id).status_code == 404
    assert api.client.get(
        f"/api/lesson-library/v1/upload-sessions/{generic_id}", headers=headers(api.parent)
    ).status_code == 404
    # The lesson route still serves its own session (organization scope, no owner scope ref).
    lesson_view = api.client.get(
        f"/api/lesson-library/v1/upload-sessions/{lesson_id}", headers=headers(api.teacher)
    )
    assert lesson_view.status_code == 200 and lesson_view.json()["upload_session_id"] == lesson_id


def test_the_client_cannot_set_role_owner_organization_or_unknown_fields(api: UploadApi) -> None:
    run_id = new_run(api, api.parent)
    data = png_of(100)
    for extra in ({"organization_id": "x"}, {"owner_ref": "x"}, {"role": "teacher"}, {"x": 1}):
        response = create(api, api.parent, run_id, data, **extra)
        assert response.status_code == 400, extra
        assert code_of(response) == "INVALID_REQUEST"
        assert response.json()["field_errors"] == [{"field": "<unknown>", "code": "UNKNOWN_FIELD"}]
    for purpose in ("LESSON_SOURCE", "PROFILE_IMAGE", "NOPE"):
        response = create(api, api.parent, run_id, data, purpose=purpose)
        assert response.status_code == 400 and code_of(response) == "INVALID_REQUEST"
    audio = create(api, api.parent, run_id, data, purpose="RUN_AUDIO", media_type="audio/wav")
    assert audio.status_code == 400 and code_of(audio) == "INVALID_REQUEST"
    assert audio.json()["field_errors"] == [{"field": "purpose", "code": "INVALID_FORMAT"}]
    bad_hash = create(api, api.parent, run_id, data, expected_sha256="G" * 64)
    assert bad_hash.status_code == 400
    with api.sessions()() as db:
        assert db.scalar(select(func.count()).select_from(UPLOAD_SESSIONS)) is not None


def test_create_limits_types_and_target_state(api: UploadApi) -> None:
    run_id = new_run(api, api.parent)
    data = png_of(100)
    bad_type = create(api, api.parent, run_id, data, media_type="image/gif")
    assert bad_type.status_code == 415 and code_of(bad_type) == "UNSUPPORTED_MEDIA_TYPE"
    pdf_for_art = create(api, api.parent, run_id, data, media_type="application/pdf")
    assert pdf_for_art.status_code == 415
    too_big = create(api, api.parent, run_id, data, expected_size_bytes=20 * 1024 * 1024 + 1)
    assert too_big.status_code == 413 and code_of(too_big) == "MEDIA_TOO_LARGE"
    exact = create(api, api.parent, run_id, data, expected_size_bytes=20 * 1024 * 1024)
    assert exact.status_code == 201
    for state in ("SUBJECT_REVIEW", "DELETE_PENDING", "DELETED", "FAILED"):
        other_run = new_run(api, api.parent, state=state)
        refused = create(api, api.parent, other_run, data)
        assert refused.status_code == 409, state
        assert code_of(refused) == "INVALID_STATE_TRANSITION"
    missing_key = api.client.post(
        "/v1/upload-sessions",
        json={
            "purpose": "RUN_ARTWORK", "target_ref": run_id, "media_type": "image/png",
            "expected_size_bytes": 100, "expected_sha256": sha(data),
        },
        headers=headers(api.parent),
    )
    assert missing_key.status_code == 400 and code_of(missing_key) == "INVALID_REQUEST"
    for bad_key in ("a b", "k" * 129, "é"):
        try:
            response = api.client.post(
                "/v1/upload-sessions",
                json={
                    "purpose": "RUN_ARTWORK", "target_ref": run_id, "media_type": "image/png",
                    "expected_size_bytes": 100, "expected_sha256": sha(data),
                },
                headers=headers(api.parent, bad_key),
            )
        except UnicodeEncodeError:
            continue
        assert response.status_code == 400 and code_of(response) == "INVALID_REQUEST"


# ----------------------------------------------------------------------------- idempotency
def test_create_replay_mismatch_and_concurrent_same_key(api: UploadApi) -> None:
    run_id = new_run(api, api.parent)
    data = png_of(100)
    first = create(api, api.parent, run_id, data, key="same-key")
    replay = create(api, api.parent, run_id, data, key="same-key")
    assert first.status_code == replay.status_code == 201
    assert first.json() == replay.json()
    different = create(api, api.parent, run_id, png_of(101), key="same-key")
    assert different.status_code == 400 and code_of(different) == "INVALID_IDEMPOTENCY_KEY"
    with api.sessions()() as db:
        count = db.scalar(
            select(func.count()).select_from(UPLOAD_SESSIONS).where(
                UPLOAD_SESSIONS.c.target_ref == run_id
            )
        )
    assert count == 1

    run_two = new_run(api, api.parent)
    barrier = Barrier(2)

    def attempt(_: int) -> Any:
        barrier.wait()
        return create(api, api.parent, run_two, data, key="race-key")

    with ThreadPoolExecutor(max_workers=2) as pool:
        left, right = list(pool.map(attempt, range(2)))
    assert left.status_code == right.status_code == 201
    assert left.json() == right.json()
    with api.sessions()() as db:
        sessions = db.scalar(
            select(func.count()).select_from(UPLOAD_SESSIONS).where(
                UPLOAD_SESSIONS.c.target_ref == run_two
            )
        )
        receipts = db.scalar(
            select(func.count()).select_from(Be1CommandReceiptModel).where(
                Be1CommandReceiptModel.idempotency_key == "race-key",
                Be1CommandReceiptModel.principal_ref == api.parent,
            )
        )
    assert (sessions, receipts) == (1, 1)


def test_complete_same_key_with_another_body_is_an_idempotency_error(api: UploadApi) -> None:
    run_id = new_run(api, api.parent)
    data = png_of(200)
    upload_id, done = full_upload(api, api.parent, run_id, data)
    assert done.status_code == 202
    key = "complete-fixed"
    # A new session for this check, completed once with `key`.
    run_two = new_run(api, api.parent)
    api.scanner.clean.add(sha(data))
    second = create(api, api.parent, run_two, data).json()["upload_id"]
    upload_parts(api, api.parent, second, data)
    assert complete(api, api.parent, second, data, key=key).status_code == 202
    mismatch = complete(api, api.parent, second, data, key=key, size=len(data) + 1)
    assert mismatch.status_code == 400 and code_of(mismatch) == "INVALID_IDEMPOTENCY_KEY"


# ----------------------------------------------------------------------------- abort and expiry
def test_abort_needs_a_strong_if_match_is_idempotent_and_purges_objects(api: UploadApi) -> None:
    run_id = new_run(api, api.parent)
    data = png_of(PART + 5)
    upload_id = create(api, api.parent, run_id, data).json()["upload_id"]
    first, second = chunks_of(data)
    put_part(api, api.parent, upload_id, 1, first)
    prefix = f"parent/{run_id}/"
    assert len(chunk_keys(api, prefix, upload_id)) == 1
    assert abort(api, api.parent, upload_id, None).status_code == 400
    assert abort(api, api.parent, upload_id, "2").status_code == 400
    assert abort(api, api.parent, upload_id, 'W/"2"').status_code == 400
    stale = abort(api, api.parent, upload_id, '"1"')
    assert stale.status_code == 409 and code_of(stale) == "STALE_REVISION"
    assert stale.headers["ETag"] == '"2"' and stale.json()["current_version"] == 2
    done = abort(api, api.parent, upload_id, '"2"', key="abort-1")
    assert done.status_code == 202 and done.json()["state"] == "ABORTED"
    assert done.headers["ETag"] == '"3"'
    assert chunk_keys(api, prefix, upload_id) == ()
    assert part_count(api, upload_id) == 1  # rows stay, so the revision is stable
    replay = abort(api, api.parent, upload_id, '"2"', key="abort-1")
    assert replay.status_code == 202 and replay.json() == done.json()
    again = abort(api, api.parent, upload_id, '"3"', key="abort-2")
    assert again.status_code == 202 and again.json()["state"] == "ABORTED"
    reused = abort(api, api.parent, upload_id, '"3"', key="abort-1")
    assert reused.status_code == 400 and code_of(reused) == "INVALID_IDEMPOTENCY_KEY"
    late_part = put_part(api, api.parent, upload_id, 2, second)
    assert late_part.status_code == 409 and code_of(late_part) == "UPLOAD_SESSION_STATE_CONFLICT"
    late_complete = complete(api, api.parent, upload_id, data)
    assert late_complete.status_code == 409
    assert get_session(api, api.parent, upload_id).json()["state"] == "ABORTED"


def test_completed_session_cannot_be_aborted(api: UploadApi) -> None:
    run_id = new_run(api, api.parent)
    data = png_of(64)
    upload_id, done = full_upload(api, api.parent, run_id, data)
    assert done.status_code == 202
    refused = abort(api, api.parent, upload_id, done.headers["ETag"])
    assert refused.status_code == 409 and code_of(refused) == "UPLOAD_SESSION_STATE_CONFLICT"


def test_an_expired_session_answers_410_on_every_route_and_purges_parts(api: UploadApi) -> None:
    run_id = new_run(api, api.parent)
    data = png_of(PART + 5)
    first, second = chunks_of(data)
    prefix = f"parent/{run_id}/"

    def expired_session() -> str:
        upload_id = create(api, api.parent, run_id, data).json()["upload_id"]
        assert put_part(api, api.parent, upload_id, 1, first).status_code == 200
        with api.sessions().begin() as db:
            db.execute(
                update(UPLOAD_SESSIONS)
                .where(UPLOAD_SESSIONS.c.upload_session_id == upload_id)
                .values(expires_at=datetime.now(UTC) - timedelta(minutes=1))
            )
        return upload_id

    checks: list[Callable[[str], Any]] = [
        lambda upload_id: get_session(api, api.parent, upload_id),
        lambda upload_id: put_part(api, api.parent, upload_id, 2, second),
        lambda upload_id: complete(api, api.parent, upload_id, data),
        lambda upload_id: abort(api, api.parent, upload_id, '"2"'),
    ]
    for check in checks:
        upload_id = expired_session()
        response = check(upload_id)
        assert response.status_code == 410, response.text
        assert code_of(response) == "UPLOAD_SESSION_EXPIRED"
        assert session_row(api, upload_id)["state"] == "EXPIRED"
        assert chunk_keys(api, prefix, upload_id) == ()
        assert part_count(api, upload_id) == 1


# ----------------------------------------------------------------------------- complete failures
def test_content_mismatch_is_terminal_and_leaves_no_asset(api: UploadApi) -> None:
    run_id = new_run(api, api.parent)
    jpeg = synthetic_jpeg_prefix()  # JPEG bytes declared as PNG
    api.scanner.clean.add(sha(jpeg))
    upload_id = create(api, api.parent, run_id, jpeg, media_type="image/png").json()["upload_id"]
    upload_parts(api, api.parent, upload_id, jpeg)
    response = complete(api, api.parent, upload_id, jpeg, key="mismatch-key")
    assert response.status_code == 422 and code_of(response) == "UPLOAD_CONTENT_MISMATCH"
    row = session_row(api, upload_id)
    assert row["state"] == "FAILED" and row["error_code"] == "UPLOAD_CONTENT_MISMATCH"
    assert row["validated_at"] is not None and row["final_asset_ref"] is None
    assert asset_rows(api, run_id) == []
    assert chunk_keys(api, f"parent/{run_id}/", upload_id) == ()
    again = complete(api, api.parent, upload_id, jpeg, key="mismatch-key")
    assert again.status_code == 409 and code_of(again) == "UPLOAD_SESSION_STATE_CONFLICT"
    status = get_session(api, api.parent, upload_id).json()
    assert status["state"] == "FAILED" and status["error_code"] == "UPLOAD_CONTENT_MISMATCH"


def test_signature_check_falls_back_to_the_shared_table_without_a_validator(api: UploadApi) -> None:
    api.app.state.upload_media_validator = None
    run_id = new_run(api, api.parent)
    jpeg = synthetic_jpeg_prefix()
    api.scanner.clean.add(sha(jpeg))
    upload_id = create(api, api.parent, run_id, jpeg, media_type="image/png").json()["upload_id"]
    upload_parts(api, api.parent, upload_id, jpeg)
    response = complete(api, api.parent, upload_id, jpeg)
    assert response.status_code == 422 and code_of(response) == "UPLOAD_CONTENT_MISMATCH"
    good = png_of(80)
    _, done = full_upload(api, api.parent, new_run(api, api.parent), good)
    assert done.status_code == 202


def test_an_infected_file_is_terminal_with_malware_detected(api: UploadApi) -> None:
    run_id = new_run(api, api.parent)
    data = png_of(900)
    upload_id, response = full_upload(api, api.parent, run_id, data, allow=False)
    assert response.status_code == 422 and code_of(response) == "MALWARE_DETECTED"
    row = session_row(api, upload_id)
    assert (row["state"], row["error_code"], row["scan_verdict"]) == (
        "FAILED", "MALWARE_DETECTED", "INFECTED",
    )
    assert asset_rows(api, run_id) == []
    assert api.storage.list_keys(f"parent/{run_id}/") == ()


def test_a_scanner_outage_is_retryable_and_never_creates_an_asset(api: UploadApi) -> None:
    run_id = new_run(api, api.parent)
    data = png_of(900)
    api.scanner.clean.add(sha(data))
    upload_id = create(api, api.parent, run_id, data).json()["upload_id"]
    upload_parts(api, api.parent, upload_id, data)
    api.scanner.unavailable = True
    down = complete(api, api.parent, upload_id, data, key="scan-retry")
    assert down.status_code == 503 and code_of(down) == "PROVIDER_UNAVAILABLE"
    assert down.json()["retryable"] is True
    assert session_row(api, upload_id)["state"] == "OPEN"
    assert asset_rows(api, run_id) == []
    assert not [key for key in api.storage.puts if key.endswith("/original")]
    api.scanner.unavailable = False
    up = complete(api, api.parent, upload_id, data, key="scan-retry")
    assert up.status_code == 202, up.text


def test_storage_failures_are_retryable_and_write_no_row(api: UploadApi) -> None:
    run_id = new_run(api, api.parent)
    data = png_of(PART + 50)
    api.scanner.clean.add(sha(data))
    upload_id = create(api, api.parent, run_id, data).json()["upload_id"]
    first, second = chunks_of(data)
    api.storage.fail_put_containing = "/parts/"
    down = put_part(api, api.parent, upload_id, 1, first)
    assert down.status_code == 503 and code_of(down) == "STORAGE_UNAVAILABLE"
    assert part_count(api, upload_id) == 0
    api.storage.fail_put_containing = None
    upload_parts(api, api.parent, upload_id, data)
    api.storage.fail_put_containing = "/original"
    final_down = complete(api, api.parent, upload_id, data, key="store-retry")
    assert final_down.status_code == 503 and code_of(final_down) == "STORAGE_UNAVAILABLE"
    assert session_row(api, upload_id)["state"] == "OPEN" and asset_rows(api, run_id) == []
    api.storage.fail_put_containing = None
    api.storage.fail_get = True
    read_down = complete(api, api.parent, upload_id, data, key="store-retry")
    assert read_down.status_code == 503 and code_of(read_down) == "STORAGE_UNAVAILABLE"
    api.storage.fail_get = False
    done = complete(api, api.parent, upload_id, data, key="store-retry")
    assert done.status_code == 202, done.text
    assert len(asset_rows(api, run_id)) == 1  # deterministic key: one asset, no orphan


def test_declared_body_that_differs_from_create_is_retryable(api: UploadApi) -> None:
    run_id = new_run(api, api.parent)
    data = png_of(400)
    api.scanner.clean.add(sha(data))
    upload_id = create(api, api.parent, run_id, data).json()["upload_id"]
    upload_parts(api, api.parent, upload_id, data)
    wrong_size = complete(api, api.parent, upload_id, data, size=len(data) + 1)
    assert wrong_size.status_code == 422 and code_of(wrong_size) == "UPLOAD_CHECKSUM_MISMATCH"
    wrong_hash = complete(api, api.parent, upload_id, data, digest="b" * 64)
    assert wrong_hash.status_code == 422 and code_of(wrong_hash) == "UPLOAD_CHECKSUM_MISMATCH"
    assert session_row(api, upload_id)["state"] == "OPEN"
    assert complete(api, api.parent, upload_id, data).status_code == 202


def test_stored_bytes_that_fail_their_hash_end_the_session(api: UploadApi) -> None:
    run_id = new_run(api, api.parent)
    data = png_of(PART + 60)
    api.scanner.clean.add(sha(data))
    upload_id = create(api, api.parent, run_id, data).json()["upload_id"]
    upload_parts(api, api.parent, upload_id, data)
    key = f"parent/{run_id}/upload/{upload_id}/parts/2"
    tampered = b"\x00" * len(chunks_of(data)[1])
    api.storage.put_object(
        key, BytesIO(tampered), content_type="application/octet-stream",
        content_length=len(tampered), metadata={},
    )
    response = complete(api, api.parent, upload_id, data)
    assert response.status_code == 422 and code_of(response) == "UPLOAD_CHECKSUM_MISMATCH"
    row = session_row(api, upload_id)
    assert row["state"] == "FAILED" and row["error_code"] == "UPLOAD_CHECKSUM_MISMATCH"
    assert asset_rows(api, run_id) == []
    assert chunk_keys(api, f"parent/{run_id}/", upload_id) == ()


def test_a_run_that_leaves_input_processing_blocks_parts_and_complete(api: UploadApi) -> None:
    run_id = new_run(api, api.parent)
    data = png_of(PART + 50)
    api.scanner.clean.add(sha(data))
    upload_id = create(api, api.parent, run_id, data).json()["upload_id"]
    first, second = chunks_of(data)
    put_part(api, api.parent, upload_id, 1, first)
    put_part(api, api.parent, upload_id, 2, second)
    set_run_state(api, run_id, "DELETE_PENDING")
    puts = len(api.storage.puts)
    blocked_part = put_part(api, api.parent, upload_id, 1, first)
    assert blocked_part.status_code == 409 and code_of(blocked_part) == "INVALID_STATE_TRANSITION"
    blocked = complete(api, api.parent, upload_id, data)
    assert blocked.status_code == 409 and code_of(blocked) == "INVALID_STATE_TRANSITION"
    assert asset_rows(api, run_id) == [] and len(api.storage.puts) == puts
    assert session_row(api, upload_id)["state"] == "OPEN"


# ----------------------------------------------------------------------------- Teacher documents
def test_teacher_occurrence_documents_use_the_organization_scope(api: UploadApi) -> None:
    occurrence = f"occ-{uuid4().hex[:8]}"
    api.occurrences[occurrence] = api.organization_id
    register_occurrence_resolver(api)
    data = zip_of(30_000)
    api.scanner.clean.add(sha(data))
    created = create(
        api, api.teacher, occurrence, data, purpose="OCCURRENCE_DOCUMENT",
        media_type=DOCX_MEDIA_TYPE, file_name="Giáo án tuần 1.docx",
    )
    assert created.status_code == 201, created.text
    upload_id = created.json()["upload_id"]
    row = session_row(api, upload_id)
    assert row["organization_id"] == api.organization_id
    assert row["owner_scope_kind"] == "ORGANIZATION" and row["owner_scope_ref"] is None
    assert row["safe_file_name"] == "Giáo án tuần 1.docx"
    upload_parts(api, api.teacher, upload_id, data)
    done = complete(api, api.teacher, upload_id, data)
    assert done.status_code == 202, done.text
    assert done.json()["asset_ref"] == f"upl_{upload_id}"
    asset_ref = session_row(api, upload_id)["final_asset_ref"]
    assert asset_ref.startswith(f"occurrences/{api.organization_id}/{occurrence}/")
    (asset,) = asset_rows(api, occurrence)
    assert asset.organization_id == api.organization_id
    assert asset.owner_scope_kind == "ORGANIZATION" and asset.owner_scope_ref == api.organization_id
    # A parent and an unassigned teacher see nothing.
    for subject in (api.parent, api.other_teacher):
        assert get_session(api, subject, upload_id).status_code == 404
        assert create(
            api, subject, occurrence, data, purpose="OCCURRENCE_DOCUMENT",
            media_type=DOCX_MEDIA_TYPE, file_name="a.docx",
        ).status_code == 404


def test_occurrence_documents_without_a_resolver_or_with_bad_input(api: UploadApi) -> None:
    data = synthetic_pdf()
    occurrence = f"occ-{uuid4().hex[:8]}"
    api.occurrences[occurrence] = api.organization_id
    none_registered = create(
        api, api.teacher, occurrence, data, purpose="OCCURRENCE_DOCUMENT",
        media_type="application/pdf", file_name="plan.pdf",
    )
    assert none_registered.status_code == 404
    register_occurrence_resolver(api)

    def make(**overrides: Any) -> Any:
        arguments: dict[str, Any] = {
            "purpose": "OCCURRENCE_DOCUMENT", "media_type": "application/pdf",
            "file_name": "plan.pdf",
        }
        arguments.update(overrides)
        return create(api, api.teacher, occurrence, data, **arguments)

    assert make().status_code == 201
    assert make(file_name=None).status_code == 400
    assert make(file_name="plan.docx").status_code == 415
    assert code_of(make(file_name="plan.exe", media_type="application/x-msdownload")) == (
        "UNSUPPORTED_LESSON_TYPE"
    )
    assert make(media_type="image/png", file_name="a.png").status_code == 415
    exact = make(expected_size_bytes=25_000_000)
    assert exact.status_code == 201 and exact.json()["expected_parts"] == 6
    big = make(expected_size_bytes=25_000_001)
    assert big.status_code == 413 and code_of(big) == "LESSON_FILE_TOO_LARGE"
    assert make(file_name="../../etc/plan.pdf").status_code == 201  # path stripped by safe_name
    row = session_row(api, make(file_name="..\\up\\plan.pdf").json()["upload_id"])
    assert row["safe_file_name"] == "plan.pdf"


def test_a_revoked_teacher_assignment_stops_the_session(api: UploadApi) -> None:
    occurrence = f"occ-{uuid4().hex[:8]}"
    api.occurrences[occurrence] = api.organization_id
    register_occurrence_resolver(api)
    data = synthetic_pdf()
    api.scanner.clean.add(sha(data))
    upload_id = create(
        api, api.teacher, occurrence, data, purpose="OCCURRENCE_DOCUMENT",
        media_type="application/pdf", file_name="plan.pdf",
    ).json()["upload_id"]
    with api.sessions().begin() as db:
        db.execute(
            update(OrganizationAssignmentModel)
            .where(OrganizationAssignmentModel.subject == api.teacher)
            .values(active=False)
        )
    for response in (
        get_session(api, api.teacher, upload_id),
        put_part(api, api.teacher, upload_id, 1, data),
        complete(api, api.teacher, upload_id, data),
        abort(api, api.teacher, upload_id, '"1"'),
    ):
        assert response.status_code == 404
    assert asset_rows(api, occurrence) == []


# ----------------------------------------------------------------------------- FR-C-08
def test_a_completed_upload_keeps_the_run_purge_plan_removable(api: UploadApi) -> None:
    run_id = new_run(api, api.parent)
    data = png_of(PART + 70)
    upload_id, done = full_upload(api, api.parent, run_id, data)
    assert done.status_code == 202
    scope = LifecycleScope("PARENT_ACCOUNT", parent_scope_ref(principal_of(api.parent)))
    sessions = api.sessions()
    purge = SqlCoreRunAssetPurge(sessions, api.storage)
    candidates = purge.closure_candidates(scope, run_id)
    plan = build_plan(candidates, frozenset())
    assert plan.retained == ()
    assert [key.asset_ref for key in plan.removable] == [
        session_row(api, upload_id)["final_asset_ref"]
    ]
    # A leftover chunk object (a failed delete) is swept as an orphan under the run prefix.
    leftover = f"parent/{run_id}/upload/{upload_id}/parts/1"
    api.storage.put_object(
        leftover, BytesIO(b"x"), content_type="application/octet-stream",
        content_length=1, metadata={},
    )
    purge.purge_objects(plan)
    swept = purge.sweep_run_prefix(scope, run_id)
    assert swept.swept_count == 1
    assert api.storage.list_keys(f"parent/{run_id}/") == ()
    purge.delete_rows(plan, frozenset())
    assert asset_rows(api, run_id) == []


def test_run_deletion_closes_open_generic_sessions(api: UploadApi) -> None:
    run_id = new_run(api, api.parent)
    data = png_of(PART + 70)
    open_id = create(api, api.parent, run_id, data).json()["upload_id"]
    put_part(api, api.parent, open_id, 1, chunks_of(data)[0])
    finished_id, done = full_upload(api, api.parent, run_id, png_of(50))
    assert done.status_code == 202
    scope = LifecycleScope("PARENT_ACCOUNT", parent_scope_ref(principal_of(api.parent)))
    closer = SqlCoreRunUploadClose(api.sessions())
    assert closer.plan_close_run_uploads(scope, run_id) == (open_id,)
    assert closer.close_run_uploads(scope, run_id) == 1
    assert closer.plan_close_run_uploads(scope, run_id) == ()
    row = session_row(api, open_id)
    assert (row["state"], row["error_code"]) == ("ABORTED", "RUN_DELETED")
    assert row["aborted_at"] is not None
    assert session_row(api, finished_id)["state"] == "COMPLETED"
    other_scope = LifecycleScope("PARENT_ACCOUNT", parent_scope_ref(principal_of(api.other_parent)))
    assert closer.plan_close_run_uploads(other_scope, run_id) == ()
    late = put_part(api, api.parent, open_id, 2, chunks_of(data)[1])
    assert late.status_code == 409 and code_of(late) == "UPLOAD_SESSION_STATE_CONFLICT"


def test_run_deletion_waits_for_a_complete_in_flight_and_then_closes_nothing(
    api: UploadApi,
) -> None:
    run_id = new_run(api, api.parent)
    data = png_of(700)
    api.scanner.clean.add(sha(data))
    upload_id = create(api, api.parent, run_id, data).json()["upload_id"]
    upload_parts(api, api.parent, upload_id, data)
    scope = LifecycleScope("PARENT_ACCOUNT", parent_scope_ref(principal_of(api.parent)))
    closer = SqlCoreRunUploadClose(api.sessions())
    api.scanner.gate = Event()
    with ThreadPoolExecutor(max_workers=2) as pool:
        completing = pool.submit(complete, api, api.parent, upload_id, data)
        assert api.scanner.entered.wait(timeout=30)  # complete holds the session row lock
        closing = pool.submit(closer.close_run_uploads, scope, run_id)
        sleep(0.8)
        assert not closing.done()  # the close update waits for the lock
        api.scanner.gate.set()
        response = completing.result(timeout=60)
        closed = closing.result(timeout=60)
    assert response.status_code == 202, response.text
    assert closed == 0  # the session was COMPLETED by then: nothing left to abort
    assert session_row(api, upload_id)["state"] == "COMPLETED"
    assert len(asset_rows(api, run_id)) == 1  # seeded by source_refs, so the purge covers it


def test_complete_after_the_close_is_a_state_conflict_and_writes_nothing(api: UploadApi) -> None:
    run_id = new_run(api, api.parent)
    data = png_of(700)
    api.scanner.clean.add(sha(data))
    upload_id = create(api, api.parent, run_id, data).json()["upload_id"]
    upload_parts(api, api.parent, upload_id, data)
    scope = LifecycleScope("PARENT_ACCOUNT", parent_scope_ref(principal_of(api.parent)))
    assert SqlCoreRunUploadClose(api.sessions()).close_run_uploads(scope, run_id) == 1
    puts = len(api.storage.puts)
    response = complete(api, api.parent, upload_id, data)
    assert response.status_code == 409 and code_of(response) == "UPLOAD_SESSION_STATE_CONFLICT"
    assert asset_rows(api, run_id) == [] and len(api.storage.puts) == puts


# ----------------------------------------------------------------------------- no leakage
def test_no_storage_word_appears_in_bodies_headers_or_the_schema(api: UploadApi) -> None:
    run_id = new_run(api, api.parent)
    data = png_of(PART + 20)
    api.scanner.clean.add(sha(data))
    responses = []
    created = create(api, api.parent, run_id, data)
    responses.append(created)
    upload_id = created.json()["upload_id"]
    for number, chunk in enumerate(chunks_of(data), start=1):
        responses.append(put_part(api, api.parent, upload_id, number, chunk))
    responses.append(get_session(api, api.parent, upload_id))
    responses.append(complete(api, api.parent, upload_id, data))
    responses.append(get_session(api, api.other_parent, upload_id))
    responses.append(abort(api, api.parent, upload_id, '"9"'))
    forbidden = ("bucket", "s3", "object_key", "storage_object_ref", "amazonaws", "minio",
                 "x-amz", "signature=", "http://", "https://", "credential", "presigned")
    for response in responses:
        text = (response.text + json.dumps(dict(response.headers))).lower()
        for word in forbidden:
            assert word not in text, (word, response.request.url)
    schema = json.dumps(api.client.get("/openapi.json").json()).lower()
    upload_paths = {
        path: item
        for path, item in json.loads(schema)["paths"].items()
        if path.startswith("/v1/upload-sessions")
    }
    assert len(upload_paths) == 4
    scoped = json.dumps(upload_paths)
    for word in ("bucket", "object_key", "storage_object_ref", "presigned", "credential"):
        assert word not in scoped
