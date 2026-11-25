"""PostgreSQL-backed HTTP acceptance checks for non-AI Lesson Library workflows."""

from __future__ import annotations

import hashlib
import os
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from io import BytesIO
from typing import Any
from uuid import uuid4

import pytest
from fastapi import FastAPI, Header
from fastapi.testclient import TestClient
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.lesson_documents import (
    LessonDocumentExtraction,
    MalwareScanResult,
)
from sketch2life.application.ports.object_storage import StoredObject
from sketch2life.application.services.storage_example import StorageExampleService
from sketch2life.contracts.schemas.lesson_occurrences import LessonVersionRefV1
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.documents.clamav_scanner import ClamAvScanner
from sketch2life.infrastructure.documents.lesson_parser import DeterministicLessonDocumentParser
from sketch2life.infrastructure.lesson_library.service import (
    LessonLibraryError,
    LessonLibraryService,
)
from sketch2life.infrastructure.lesson_library.tables import (
    ACCESS_GRANTS,
    COMMAND_RECEIPTS,
    LIBRARY_ITEMS,
    LIBRARY_VERSIONS,
    PARENT_GROUP_MEMBERS,
    PARENT_GROUPS,
    UPLOAD_SESSIONS,
)
from sketch2life.infrastructure.lesson_occurrences.scope import LessonOccurrenceError
from sketch2life.infrastructure.lesson_occurrences.service import LessonOccurrenceService
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.infrastructure.persistence.core_models import (
    CoreAuditEntryModel,
    CoreOutboxEventModel,
)
from sketch2life.infrastructure.persistence.platform_models import PermissionGrantModel
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult
from sketch2life.interfaces.http.routers.lesson_library import get_lesson_library_service
from sketch2life.interfaces.http.routers.storage_examples import get_storage_example_service
from sqlalchemy import MetaData, Table, and_, delete, func, insert, inspect, or_, select, update
from sqlalchemy.sql.elements import ColumnElement


class InMemoryObjectStorage:
    """Deterministic object-storage port for API tests; no external data is used."""

    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, str, dict[str, str]]] = {}

    def put_object(
        self,
        key: str,
        body,
        *,
        content_type: str,
        content_length: int,
        metadata: dict[str, str],
    ) -> None:
        content = body.read()
        if len(content) != content_length:
            raise AssertionError("object storage received a different content length")
        self.objects[key] = (content, content_type, dict(metadata))

    def get_object(self, key: str) -> StoredObject | None:
        item = self.objects.get(key)
        if item is None:
            return None
        content, content_type, metadata = item
        return StoredObject(BytesIO(content), len(content), content_type, metadata)

    def delete_object(self, key: str) -> None:
        self.objects.pop(key, None)

    def list_keys(self, prefix: str) -> tuple[str, ...]:
        # FR-C-08 (port design §5.3): every ObjectStoragePort fake lists keys by prefix.
        return tuple(sorted(key for key in self.objects if key.startswith(prefix)))


@dataclass
class LessonApiAcceptance:
    app: FastAPI
    client: TestClient
    organization_id: str
    teacher: str
    manager: str
    parent: str
    platform_admin: str
    storage: InMemoryObjectStorage


@pytest.fixture
def lesson_api_acceptance(monkeypatch: pytest.MonkeyPatch) -> Iterator[LessonApiAcceptance]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL to a disposable PostgreSQL database")
    database_name = database_url.rsplit("/", 1)[-1]
    if "be1_acceptance" not in database_name:
        pytest.fail("BE1_TEST_DATABASE_URL must point to a disposable *be1_acceptance database")

    organization_id = f"synthetic-lesson-org-{uuid4()}"
    teacher = f"synthetic-teacher-{uuid4()}"
    manager = f"synthetic-manager-{uuid4()}"
    parent = f"synthetic-parent-{uuid4()}"
    platform_admin = f"synthetic-platform-admin-{uuid4()}"
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", database_url)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "local")
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "development")
    monkeypatch.setenv("SKETCH2LIFE_AI_PROVIDER", "disabled")
    monkeypatch.setenv("SKETCH2LIFE_STORAGE_EXAMPLE_ENABLED", "true")
    monkeypatch.setenv("SKETCH2LIFE_STORAGE_EXAMPLE_MAX_UPLOAD_BYTES", "10485760")
    monkeypatch.setenv("SKETCH2LIFE_S3_ENDPOINT", "http://127.0.0.1:9000")
    monkeypatch.setenv("SKETCH2LIFE_S3_BUCKET", "sketch2life-private")
    monkeypatch.setenv("SKETCH2LIFE_S3_ACCESS_KEY", "test-only-access-key")
    monkeypatch.setenv("SKETCH2LIFE_S3_SECRET_KEY", "test-only-secret-key")
    monkeypatch.setenv("SKETCH2LIFE_CLAMAV_HOST", "127.0.0.1")
    monkeypatch.setenv("SKETCH2LIFE_CLAMAV_PORT", "3310")
    monkeypatch.setenv("SKETCH2LIFE_PLATFORM_ADMIN_SUBJECTS", platform_admin)
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()

    app = create_app()
    runtime = app.state.be1_runtime
    if runtime.engine is None or runtime.session_factory is None:
        pytest.fail("Lesson Library PostgreSQL runtime did not initialize")
    with runtime.engine.connect() as connection:
        if not connection.dialect.has_table(connection, "library_items", schema="lesson"):
            pytest.fail("BE1_TEST_DATABASE_URL is missing the Lesson Library migration")

    with runtime.session_factory.begin() as db:
        db.add(
            OrganizationModel(
                organization_id=organization_id,
                display_name="Synthetic Lesson Acceptance Organization",
                state="active",
            )
        )
        for subject, account_role in (
            (teacher, "teacher"),
            (manager, "school_manager"),
            (parent, "parent"),
            (platform_admin, "platform_admin"),
        ):
            db.add(
                AdultIdentityModel(
                    subject=subject,
                    issuer="synthetic-lesson-test-issuer",
                    state="active",
                    account_role=account_role,
                )
            )
        db.flush()
        # FEAT-072: lesson moderation needs the Platform Admin content_admin permission.
        db.add(
            PermissionGrantModel(
                subject=platform_admin,
                permission="content_admin",
                active=True,
                revision=1,
                granted_by=platform_admin,
            )
        )
        db.flush()
        db.add_all(
            [
                OrganizationAssignmentModel(
                    assignment_id=str(uuid4()),
                    organization_id=organization_id,
                    subject=teacher,
                    class_id=None,
                    role="teacher",
                    active=True,
                ),
                OrganizationAssignmentModel(
                    assignment_id=str(uuid4()),
                    organization_id=organization_id,
                    subject=manager,
                    class_id=None,
                    role="school_admin",
                    active=True,
                ),
            ]
        )

    async def verified_test_adult(
        x_test_principal: str = Header(alias="X-Test-Principal"),
    ) -> VerifiedPrincipal:
        return VerifiedPrincipal(
            subject=x_test_principal,
            issuer="synthetic-lesson-test-issuer",
            roles=frozenset(),
            token_id="synthetic-lesson-test-token",
        )

    storage = InMemoryObjectStorage()
    app.state.lesson_library_storage = storage
    app.state.lesson_document_parser = DeterministicLessonDocumentParser()
    app.state.lesson_document_scanner = ClamAvScanner(
        host="127.0.0.1",
        port=3310,
        timeout_seconds=60,
    )
    app.dependency_overrides[get_verified_adult] = verified_test_adult
    app.dependency_overrides[get_storage_example_service] = lambda: StorageExampleService(
        storage,
        max_upload_bytes=10 * 1024 * 1024,
    )

    try:
        with TestClient(app, client=("10.77.0.1", 12345)) as client:
            yield LessonApiAcceptance(
                app,
                client,
                organization_id,
                teacher,
                manager,
                parent,
                platform_admin,
                storage,
            )
    finally:
        app.dependency_overrides.clear()
        inspector = inspect(runtime.engine)
        metadata = MetaData()
        tables: dict[tuple[str, str], Table] = {}
        for schema in inspector.get_schema_names():
            if schema == "information_schema" or schema.startswith("pg_"):
                continue
            for table_name in inspector.get_table_names(schema=schema):
                table = Table(
                    table_name,
                    metadata,
                    schema=schema,
                    autoload_with=runtime.engine,
                )
                tables[(schema, table_name)] = table

        ordered = [
            table
            for table in reversed(metadata.sorted_tables)
            if (table.schema or "public", table.name) in tables
        ]
        with runtime.engine.begin() as connection:
            owned_keys: dict[tuple[str, str], set[tuple[object, ...]]] = {}
            primary_keys = {key: list(table.primary_key.columns) for key, table in tables.items()}

            def key_filter(
                columns: Sequence[ColumnElement[Any]], keys: set[tuple[object, ...]]
            ) -> ColumnElement[bool]:
                return or_(
                    *(
                        and_(*(column == value for column, value in zip(columns, key, strict=True)))
                        for key in keys
                    )
                )

            # Seed ownership only from this fixture's unique organization ID.
            # Some dependent tables (for example lesson version activities) do
            # not carry organization_id, so follow FK edges to find their rows.
            for table_key, table in tables.items():
                if "organization_id" not in table.c:
                    continue
                primary_key = primary_keys[table_key]
                if not primary_key:
                    exists = connection.execute(
                        select(func.count())
                        .select_from(table)
                        .where(table.c.organization_id == organization_id)
                    ).scalar_one()
                    if exists:
                        raise AssertionError(
                            f"fixture-owned table has no primary key: {table.fullname}"
                        )
                    continue
                rows = connection.execute(
                    select(*primary_key).where(table.c.organization_id == organization_id)
                ).all()
                if rows:
                    owned_keys[table_key] = {tuple(row) for row in rows}

            foreign_keys = {
                table_key: inspector.get_foreign_keys(table.name, schema=table.schema)
                for table_key, table in tables.items()
            }
            changed = True
            while changed:
                changed = False
                for child_key, child in tables.items():
                    child_primary_key = primary_keys[child_key]
                    if not child_primary_key:
                        continue
                    for foreign_key_index, foreign_key in enumerate(foreign_keys[child_key]):
                        parent_schema = (
                            foreign_key.get("referred_schema") or child.schema or "public"
                        )
                        parent_name = foreign_key.get("referred_table")
                        parent_key = (parent_schema, parent_name)
                        parent_table = tables.get(parent_key)
                        local_names = foreign_key.get("constrained_columns") or []
                        remote_names = foreign_key.get("referred_columns") or []
                        parent_owned_keys = owned_keys.get(parent_key, set())
                        parent_primary_key = primary_keys.get(parent_key, [])
                        if (
                            parent_table is None
                            or not parent_owned_keys
                            or not parent_primary_key
                            or not local_names
                            or len(local_names) != len(remote_names)
                        ):
                            continue
                        parent_alias = parent_table.alias(
                            f"owned_parent_{len(child_key[1])}_{foreign_key_index}"
                        )
                        join_condition = and_(
                            *(
                                child.c[local_name] == parent_alias.c[remote_name]
                                for local_name, remote_name in zip(
                                    local_names, remote_names, strict=True
                                )
                            )
                        )
                        rows = connection.execute(
                            select(*child_primary_key)
                            .select_from(child.join(parent_alias, join_condition))
                            .where(
                                key_filter(
                                    [parent_alias.c[column.name] for column in parent_primary_key],
                                    parent_owned_keys,
                                )
                            )
                        ).all()
                        if not rows:
                            continue
                        child_owned_keys = owned_keys.setdefault(child_key, set())
                        prior_count = len(child_owned_keys)
                        child_owned_keys.update(tuple(row) for row in rows)
                        changed = changed or len(child_owned_keys) != prior_count

            for table in ordered:
                table_key = (table.schema or "public", table.name)
                rows = owned_keys.get(table_key, set())
                if not rows:
                    continue
                primary_key = primary_keys[table_key]
                for row in rows:
                    connection.execute(delete(table).where(key_filter(primary_key, {row})))

            adults = tables.get(("public", "be1_adult_identities"))
            if adults is not None:
                for subject in (teacher, manager, parent, platform_admin):
                    connection.execute(delete(adults).where(adults.c.subject == subject))

        runtime.engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def _headers(subject: str, **extra: str) -> dict[str, str]:
    return {"X-Test-Principal": subject, **extra}


def _content(title: str = "Bài học bướm tổng hợp") -> dict[str, object]:
    return {
        "locale": "vi-VN",
        "title": title,
        "topic": "Con bướm",
        "target_age_band_ref": "age-3-6",
        "target_age_band_version": 1,
        "objectives": ["Quan sát hình dáng và cánh của bướm"],
        "drawing_subject": "Con bướm",
        "drawing_steps_text": "Vẽ thân, đầu, râu và hai cặp cánh.",
        "subject_learning_notes": "Bướm có sáu chân và hai cặp cánh.",
        "script_direction": "Kể ngắn gọn, khuyến khích trẻ quan sát.",
        "script_following_allowed": True,
        "activities": [
            {
                "title": "Quan sát khu vườn",
                "objective": "Tìm hiểu côn trùng quanh vườn.",
                "materials_text": "Kính lúp tùy chọn",
                "preparation_text": "Chọn khu vực an toàn.",
                "instructions_text": "Quan sát từ xa và mô tả màu sắc.",
                "observation_notes": "Để trẻ tự chọn điều muốn quan sát.",
                "safety_notes": "Không chạm hoặc bắt côn trùng.",
                "activity_kind": "outdoor",
            }
        ],
    }


def _create_lesson(
    accepted: LessonApiAcceptance,
    *,
    title: str = "Bài học bướm tổng hợp",
    visibility: str = "SCHOOL",
) -> dict[str, object]:
    response = accepted.client.post(
        f"/api/lesson-library/v1/organizations/{accepted.organization_id}/lessons",
        json={
            "contract": "CreateLessonRequestV1",
            "content": _content(title),
            "visibility": visibility,
        },
        headers=_headers(
            accepted.teacher,
            **{"Idempotency-Key": f"lesson-create-{uuid4()}"},
        ),
    )
    assert response.status_code == 201, response.text
    return response.json()


def _create_lesson_in_org(
    accepted: LessonApiAcceptance,
    *,
    organization_id: str,
    teacher: str,
    title: str,
    visibility: str = "PRIVATE",
) -> dict[str, object]:
    response = accepted.client.post(
        f"/api/lesson-library/v1/organizations/{organization_id}/lessons",
        json={
            "contract": "CreateLessonRequestV1",
            "content": _content(title),
            "visibility": visibility,
        },
        headers=_headers(teacher, **{"Idempotency-Key": f"lesson-create-{uuid4()}"}),
    )
    assert response.status_code == 201, response.text
    return response.json()


def _revise_lesson(
    accepted: LessonApiAcceptance,
    *,
    lesson_id: str,
    expected_revision: int,
    title: str,
) -> tuple[dict[str, object], int]:
    response = accepted.client.patch(
        f"/api/lesson-library/v1/organizations/{accepted.organization_id}/lessons/{lesson_id}",
        json={"contract": "UpdateLessonRequestV1", "content": _content(title)},
        headers=_headers(
            accepted.teacher,
            **{
                "If-Match": f'"{expected_revision}"',
                "Idempotency-Key": f"version-edit-{uuid4()}",
            },
        ),
    )
    assert response.status_code == 200, response.text
    return response.json(), int(response.headers["ETag"].strip('"'))


def _create_public_grant_in_org(
    accepted: LessonApiAcceptance,
    *,
    organization_id: str,
    teacher: str,
    lesson: dict[str, object],
) -> dict[str, object]:
    response = accepted.client.post(
        f"/api/lesson-library/v1/organizations/{organization_id}/lessons/"
        f"{lesson['lesson_id']}/access-grants",
        json={
            "contract": "CreateLessonAccessGrantRequestV1",
            "version_id": lesson["current_version"]["version_id"],
            "audience_kind": "PUBLIC",
            "audience_ref": None,
            "capability": "VIEW",
            "expires_at": None,
        },
        headers=_headers(teacher, **{"Idempotency-Key": f"public-grant-{uuid4()}"}),
    )
    assert response.status_code == 201, response.text
    return response.json()


def _approve_public_grant_in_org(
    accepted: LessonApiAcceptance,
    *,
    organization_id: str,
    manager: str,
    grant: dict[str, object],
) -> dict[str, object]:
    response = accepted.client.post(
        f"/api/lesson-library/v1/organizations/{organization_id}/access-grants/"
        f"{grant['access_grant_id']}/decision",
        json={
            "contract": "DecideLessonAccessGrantRequestV1",
            "decision": "APPROVE",
            "reason": None,
        },
        headers=_headers(manager, **{"If-Match": '"1"', "Idempotency-Key": f"approve-{uuid4()}"}),
    )
    assert response.status_code == 200, response.text
    return response.json()


def _synthetic_pdf() -> bytes:
    text = (
        b"BT\n/F1 12 Tf\n72 720 Td\n"
        b"(Title: Synthetic Butterfly Lesson) Tj\n0 -16 Td\n"
        b"(Topic: Butterfly) Tj\n0 -16 Td\n"
        b"(Drawing Subject: Butterfly) Tj\n0 -16 Td\n"
        b"(Drawing Steps: Draw the body and wings) Tj\n0 -16 Td\n"
        b"(Subject Notes: Butterflies have two pairs of wings) Tj\n0 -16 Td\n"
        b"(Objectives: Notice butterfly wings) Tj\nET\n"
    )
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Length " + str(len(text)).encode("ascii") + b" >>\nstream\n" + text + b"endstream",
    ]
    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for index, body in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("ascii"))
        pdf.extend(body)
        pdf.extend(b"\nendobj\n")
    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    return bytes(pdf)


def _create_public_grant(
    accepted: LessonApiAcceptance,
    lesson: dict[str, object],
    *,
    capability: str,
) -> dict[str, object]:
    response = accepted.client.post(
        f"/api/lesson-library/v1/organizations/{accepted.organization_id}/lessons/"
        f"{lesson['lesson_id']}/access-grants",
        json={
            "contract": "CreateLessonAccessGrantRequestV1",
            "version_id": lesson["current_version"]["version_id"],
            "audience_kind": "PUBLIC",
            "audience_ref": None,
            "capability": capability,
            "expires_at": None,
        },
        headers=_headers(
            accepted.teacher,
            **{"Idempotency-Key": f"public-grant-{capability.lower()}-{uuid4()}"},
        ),
    )
    assert response.status_code == 201, response.text
    assert response.json()["state"] == "PENDING_REVIEW"
    return response.json()


def _approve_public_grant(
    accepted: LessonApiAcceptance,
    grant: dict[str, object],
) -> dict[str, object]:
    response = accepted.client.post(
        f"/api/lesson-library/v1/organizations/{accepted.organization_id}/access-grants/"
        f"{grant['access_grant_id']}/decision",
        json={
            "contract": "DecideLessonAccessGrantRequestV1",
            "decision": "APPROVE",
            "reason": None,
        },
        headers=_headers(
            accepted.manager,
            **{"If-Match": '"1"', "Idempotency-Key": f"approve-{uuid4()}"},
        ),
    )
    assert response.status_code == 200, response.text
    assert response.json()["state"] == "ACTIVE"
    assert response.headers["ETag"] == '"2"'
    return response.json()


def test_teacher_lesson_crud_revision_guards_and_organization_scope(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    client = accepted.client
    lesson = _create_lesson(accepted, visibility="PRIVATE")
    lesson_id = lesson["lesson_id"]
    lesson_url = (
        f"/api/lesson-library/v1/organizations/{accepted.organization_id}/lessons/{lesson_id}"
    )
    assert lesson["current_version"]["review_state"] == "DRAFT"
    assert client.get(lesson_url, headers=_headers(accepted.teacher)).status_code == 200
    page = client.get(
        f"/api/lesson-library/v1/organizations/{accepted.organization_id}/lessons",
        headers=_headers(accepted.manager),
    )
    assert page.status_code == 200
    assert any(item["lesson_id"] == lesson_id for item in page.json()["items"])

    updated_content = _content("Bài học bướm đã sửa")
    updated = client.patch(
        lesson_url,
        json={"contract": "UpdateLessonRequestV1", "content": updated_content},
        headers=_keyed(accepted.teacher, 1, f"lesson-patch-{uuid4()}"),
    )
    assert updated.status_code == 200, updated.text
    assert updated.headers["ETag"] == '"2"'
    assert updated.json()["current_version"]["version_no"] == 2

    stale = client.patch(
        lesson_url,
        json={"contract": "UpdateLessonRequestV1", "content": _content("Bản ghi cũ")},
        headers=_keyed(accepted.teacher, 1, f"lesson-patch-stale-{uuid4()}"),
    )
    assert stale.status_code == 409
    assert "STALE_REVISION" in stale.text
    # C4 (C-D7): the stale answer carries the current version and the strong ETag.
    assert stale.json()["current_version"] == 2
    assert stale.headers["ETag"] == '"2"'

    forbidden = client.get(
        f"/api/lesson-library/v1/organizations/{accepted.organization_id}/lessons",
        headers=_headers(accepted.parent),
    )
    # CONV-1 (D-066-68 C-D4, D-066-71 CV-5): a Parent account is out of scope here -> 404.
    assert forbidden.status_code == 404

    archived = client.delete(
        lesson_url,
        headers=_headers(
            accepted.teacher, **{"If-Match": '"2"', "Idempotency-Key": f"archive-{uuid4()}"}
        ),
    )
    assert archived.status_code == 200, archived.text
    assert archived.json()["state"] == "ARCHIVED"
    assert archived.headers["ETag"] == '"3"'


def test_teacher_uploads_and_reviews_a_synthetic_pdf_through_http(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    client = accepted.client
    lesson = _create_lesson(accepted)
    pdf = _synthetic_pdf()
    sha256 = hashlib.sha256(pdf).hexdigest()
    lesson_url = (
        f"/api/lesson-library/v1/organizations/{accepted.organization_id}/lessons/"
        f"{lesson['lesson_id']}"
    )
    session_response = client.post(
        lesson_url + "/upload-sessions",
        json={
            "contract": "CreateLessonUploadSessionRequestV1",
            "file_name": "synthetic-butterfly.pdf",
            "media_type": "application/pdf",
            "byte_length": len(pdf),
            "sha256": sha256,
        },
        headers=_headers(accepted.teacher, **{"Idempotency-Key": f"upload-session-{uuid4()}"}),
    )
    assert session_response.status_code == 201, session_response.text
    upload = session_response.json()
    assert upload["expected_parts"] == 1
    upload_id = upload["upload_session_id"]
    status_before_upload = client.get(
        f"/api/lesson-library/v1/upload-sessions/{upload_id}",
        headers=_headers(accepted.teacher),
    )
    assert status_before_upload.status_code == 200
    assert status_before_upload.json()["state"] == "OPEN"

    incomplete = client.post(
        f"/api/lesson-library/v1/upload-sessions/{upload_id}/complete",
        headers=_headers(accepted.teacher, **{"Idempotency-Key": f"upload-complete-{uuid4()}"}),
    )
    # C4 (SRS §9.8 line 871): an incomplete upload is 422 UPLOAD_INCOMPLETE.
    assert incomplete.status_code == 422
    assert incomplete.json()["code"] == "UPLOAD_INCOMPLETE"

    part = client.put(
        f"/api/lesson-library/v1/upload-sessions/{upload_id}/parts/1",
        content=pdf,
        headers=_headers(
            accepted.teacher,
            **{
                "X-Part-SHA256": sha256,
                "Content-Range": f"bytes 0-{len(pdf) - 1}/{len(pdf)}",
                "Content-Type": "application/pdf",
            },
        ),
    )
    assert part.status_code == 200, part.text
    assert part.json()["accepted"] is True
    status_after_part = client.get(
        f"/api/lesson-library/v1/upload-sessions/{upload_id}",
        headers=_headers(accepted.teacher),
    )
    assert status_after_part.json()["accepted_part_numbers"] == [1]

    completed = client.post(
        f"/api/lesson-library/v1/upload-sessions/{upload_id}/complete",
        headers=_headers(accepted.teacher, **{"Idempotency-Key": f"upload-complete-{uuid4()}"}),
    )
    assert completed.status_code == 202, completed.text
    source = completed.json()
    assert source["state"] == "READY_FOR_REVIEW"
    assert source["asset_sha256"] == sha256
    assert source["revision_id"]
    source_url = lesson_url + f"/source-documents/{source['source_document_id']}"
    assert (
        client.get(source_url, headers=_headers(accepted.teacher)).json()["state"]
        == "READY_FOR_REVIEW"
    )
    preview = client.get(
        source_url + f"/revisions/{source['revision_id']}",
        headers=_headers(accepted.teacher),
    )
    assert preview.status_code == 200, preview.text
    assert preview.json()["review_state"] == "NEEDS_REVIEW"
    assert preview.json()["extracted_fields"]["title"] == "Synthetic Butterfly Lesson"

    version = client.post(
        lesson_url + "/versions",
        json={
            "contract": "CreateLessonVersionRequestV1",
            "source_document_revision_id": source["revision_id"],
            "content": _content("Bài học sau khi rà soát tài liệu"),
        },
        headers=_keyed(accepted.teacher, 1, f"version-{uuid4()}"),
    )
    assert version.status_code == 201, version.text
    assert version.json()["version_no"] == 2
    assert version.json()["source_document_revision_id"] == source["revision_id"]
    assert version.json()["review_state"] == "DRAFT"
    assert list(accepted.storage.objects) == [
        f"lesson-library/private/{accepted.organization_id}/{source['source_document_id']}/original"
    ]
    completed_status = client.get(
        f"/api/lesson-library/v1/upload-sessions/{upload_id}",
        headers=_headers(accepted.teacher),
    )
    assert completed_status.status_code == 200
    assert completed_status.json()["state"] == "COMPLETED"

    aborted_session = client.post(
        lesson_url + "/upload-sessions",
        json={
            "contract": "CreateLessonUploadSessionRequestV1",
            "file_name": "synthetic-aborted.pdf",
            "media_type": "application/pdf",
            "byte_length": len(pdf),
            "sha256": sha256,
        },
        headers=_headers(accepted.teacher, **{"Idempotency-Key": f"upload-abort-{uuid4()}"}),
    )
    assert aborted_session.status_code == 201, aborted_session.text
    assert aborted_session.headers["ETag"] == '"1"'
    aborted = client.delete(
        f"/api/lesson-library/v1/upload-sessions/{aborted_session.json()['upload_session_id']}",
        headers=_headers(
            accepted.teacher, **{"If-Match": '"1"', "Idempotency-Key": f"abort-{uuid4()}"}
        ),
    )
    assert aborted.status_code == 202, aborted.text
    assert aborted.json()["state"] == "ABORTED"


def test_manager_public_review_parent_read_export_moderation_and_revocation(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    client = accepted.client
    lesson = _create_lesson(accepted)
    lesson_id = lesson["lesson_id"]
    lesson_base = (
        f"/api/lesson-library/v1/organizations/{accepted.organization_id}/lessons/{lesson_id}"
    )
    view_grant = _create_public_grant(accepted, lesson, capability="VIEW")
    download_grant = _create_public_grant(accepted, lesson, capability="DOWNLOAD")

    parent_page = client.get(
        "/api/lesson-library/v1/me/lessons?source=PUBLIC", headers=_headers(accepted.parent)
    )
    assert parent_page.status_code == 200, parent_page.text
    assert all(item["lesson_id"] != lesson_id for item in parent_page.json()["items"])

    review_queue = client.get(
        f"/api/lesson-library/v1/organizations/{accepted.organization_id}/access-grants"
        "?audience_kind=PUBLIC&state=PENDING_REVIEW",
        headers=_headers(accepted.manager),
    )
    assert review_queue.status_code == 200
    pending = {item["access_grant_id"] for item in review_queue.json()["items"]}
    assert {view_grant["access_grant_id"], download_grant["access_grant_id"]} <= pending

    for grant in (view_grant, download_grant):
        _approve_public_grant(accepted, grant)

    parent_page = client.get(
        "/api/lesson-library/v1/me/lessons?source=PUBLIC", headers=_headers(accepted.parent)
    )
    assert parent_page.status_code == 200
    assert [item["lesson_id"] for item in parent_page.json()["items"]] == [lesson_id]
    detail = client.get(
        f"/api/lesson-library/v1/me/lessons/{lesson_id}", headers=_headers(accepted.parent)
    )
    assert detail.status_code == 200, detail.text
    assert detail.json()["access_source"] == "PUBLIC"
    assert detail.json()["title"] == "Bài học bướm tổng hợp"
    export = client.get(
        f"/api/lesson-library/v1/me/lessons/{lesson_id}/download",
        headers=_headers(accepted.parent),
    )
    assert export.status_code == 200, export.text
    assert export.json()["contract"] == "LessonExportV1"
    assert "attachment;" in export.headers["Content-Disposition"]
    assert export.headers["Cache-Control"] == "private, no-store"

    denied_admin = client.patch(
        f"/api/lesson-library/v1/platform/lessons/{lesson_id}/moderation",
        json={"contract": "ModerateLessonRequestV1", "state": "HIDDEN", "reason": "Synthetic test"},
        headers=_headers(
            accepted.teacher,
            **{"If-Match": '"1"', "Idempotency-Key": f"moderation-denied-{uuid4()}"},
        ),
    )
    assert denied_admin.status_code == 403

    hidden = client.patch(
        f"/api/lesson-library/v1/platform/lessons/{lesson_id}/moderation",
        json={"contract": "ModerateLessonRequestV1", "state": "HIDDEN", "reason": "Synthetic test"},
        headers=_headers(
            accepted.platform_admin,
            **{"If-Match": '"1"', "Idempotency-Key": f"moderation-hide-{uuid4()}"},
        ),
    )
    assert hidden.status_code == 200, hidden.text
    assert hidden.json()["state"] == "HIDDEN"
    assert (
        client.get(
            f"/api/lesson-library/v1/me/lessons/{lesson_id}",
            headers=_headers(accepted.parent),
        ).status_code
        == 404
    )

    visible = client.patch(
        f"/api/lesson-library/v1/platform/lessons/{lesson_id}/moderation",
        json={
            "contract": "ModerateLessonRequestV1",
            "state": "VISIBLE",
            "reason": "Synthetic test restored",
        },
        headers=_headers(
            accepted.platform_admin,
            **{"If-Match": '"2"', "Idempotency-Key": f"moderation-show-{uuid4()}"},
        ),
    )
    assert visible.status_code == 200, visible.text

    for grant in (view_grant, download_grant):
        revoked = client.delete(
            f"{lesson_base}/access-grants/{grant['access_grant_id']}",
            headers=_keyed(accepted.teacher, 2, f"grant-revoke-{uuid4()}"),
        )
        assert revoked.status_code == 200, revoked.text
        assert revoked.json()["state"] == "REVOKED"
    assert (
        client.get(
            f"/api/lesson-library/v1/me/lessons/{lesson_id}",
            headers=_headers(accepted.parent),
        ).status_code
        == 404
    )


def test_direct_parent_and_group_sharing_can_be_accepted_then_revoked(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    client = accepted.client
    lesson = _create_lesson(accepted)
    lesson_id = lesson["lesson_id"]
    lesson_base = (
        f"/api/lesson-library/v1/organizations/{accepted.organization_id}/lessons/{lesson_id}"
    )
    public_grant = _create_public_grant(accepted, lesson, capability="VIEW")
    _approve_public_grant(accepted, public_grant)
    public_revoked = client.delete(
        f"{lesson_base}/access-grants/{public_grant['access_grant_id']}",
        headers=_keyed(accepted.teacher, 2, f"grant-revoke-{uuid4()}"),
    )
    assert public_revoked.status_code == 200, public_revoked.text

    direct = client.post(
        lesson_base + "/access-grants",
        json={
            "contract": "CreateLessonAccessGrantRequestV1",
            "version_id": lesson["current_version"]["version_id"],
            "audience_kind": "PRINCIPAL",
            "audience_ref": accepted.parent,
            "capability": "REUSE",
            "expires_at": None,
        },
        headers=_headers(accepted.teacher, **{"Idempotency-Key": f"direct-share-{uuid4()}"}),
    )
    assert direct.status_code == 201, direct.text
    assert direct.json()["state"] == "INVITED"
    invitations = client.get(
        "/api/lesson-library/v1/me/lesson-invitations", headers=_headers(accepted.parent)
    )
    assert any(
        item["access_grant_id"] == direct.json()["access_grant_id"]
        for item in invitations.json()["items"]
    )
    accepted_invitation = client.post(
        f"/api/lesson-library/v1/me/lesson-invitations/{direct.json()['access_grant_id']}/accept",
        headers=_headers(accepted.parent, **{"Idempotency-Key": f"accept-direct-{uuid4()}"}),
    )
    assert accepted_invitation.status_code == 200, accepted_invitation.text
    assert accepted_invitation.json()["state"] == "ACTIVE"
    shared = client.get(
        "/api/lesson-library/v1/me/lessons?source=SHARED", headers=_headers(accepted.parent)
    )
    assert shared.status_code == 200, shared.text
    assert any(item["lesson_id"] == lesson_id for item in shared.json()["items"])
    assert (
        client.get(
            f"/api/lesson-library/v1/me/lessons/{lesson_id}",
            headers=_headers(accepted.parent),
        ).status_code
        == 200
    )
    direct_revoked = client.delete(
        f"{lesson_base}/access-grants/{direct.json()['access_grant_id']}",
        headers=_keyed(accepted.teacher, 2, f"grant-revoke-{uuid4()}"),
    )
    assert direct_revoked.status_code == 200, direct_revoked.text
    assert (
        client.get(
            f"/api/lesson-library/v1/me/lessons/{lesson_id}",
            headers=_headers(accepted.parent),
        ).status_code
        == 404
    )

    group = client.post(
        f"/api/lesson-library/v1/organizations/{accepted.organization_id}/parent-groups",
        json={"contract": "CreateParentGroupRequestV1", "display_name": "Synthetic parent group"},
        headers=_headers(accepted.manager, **{"Idempotency-Key": f"parent-group-{uuid4()}"}),
    )
    assert group.status_code == 201, group.text
    group_page = client.get(
        f"/api/lesson-library/v1/organizations/{accepted.organization_id}/parent-groups",
        headers=_headers(accepted.manager),
    )
    assert any(
        item["parent_group_id"] == group.json()["parent_group_id"]
        for item in group_page.json()["items"]
    )
    invitation = client.post(
        f"/api/lesson-library/v1/organizations/{accepted.organization_id}/parent-groups/"
        f"{group.json()['parent_group_id']}/invitations",
        json={"contract": "InviteParentToGroupRequestV1", "parent_principal_ref": accepted.parent},
        headers=_headers(accepted.manager, **{"Idempotency-Key": f"group-invite-{uuid4()}"}),
    )
    assert invitation.status_code == 201, invitation.text
    parent_group_invitations = client.get(
        "/api/lesson-library/v1/me/parent-group-invitations",
        headers=_headers(accepted.parent),
    )
    assert any(
        item["membership_id"] == invitation.json()["membership_id"]
        for item in parent_group_invitations.json()["items"]
    )
    membership = client.post(
        f"/api/lesson-library/v1/me/parent-group-invitations/{invitation.json()['membership_id']}/accept",
        headers=_headers(accepted.parent, **{"Idempotency-Key": f"accept-group-{uuid4()}"}),
    )
    assert membership.status_code == 200, membership.text
    assert membership.json()["revision"] == 2
    group_grant = client.post(
        lesson_base + "/access-grants",
        json={
            "contract": "CreateLessonAccessGrantRequestV1",
            "version_id": lesson["current_version"]["version_id"],
            "audience_kind": "PARENT_GROUP",
            "audience_ref": group.json()["parent_group_id"],
            "capability": "VIEW",
            "expires_at": None,
        },
        headers=_headers(accepted.teacher, **{"Idempotency-Key": f"group-share-{uuid4()}"}),
    )
    assert group_grant.status_code == 201, group_grant.text
    group_shared = client.get(
        "/api/lesson-library/v1/me/lessons?source=SHARED", headers=_headers(accepted.parent)
    )
    assert any(item["lesson_id"] == lesson_id for item in group_shared.json()["items"])

    membership_revoked = client.delete(
        f"/api/lesson-library/v1/organizations/{accepted.organization_id}/parent-groups/"
        f"{group.json()['parent_group_id']}/members/{invitation.json()['membership_id']}",
        headers=_headers(
            accepted.manager,
            **{"If-Match": '"2"', "Idempotency-Key": f"group-revoke-{uuid4()}"},
        ),
    )
    assert membership_revoked.status_code == 200, membership_revoked.text
    assert membership_revoked.json()["state"] == "REVOKED"
    assert membership_revoked.json()["revision"] == 3
    assert membership_revoked.headers["ETag"] == '"3"'
    assert all(
        item["lesson_id"] != lesson_id
        for item in client.get(
            "/api/lesson-library/v1/me/lessons?source=SHARED",
            headers=_headers(accepted.parent),
        ).json()["items"]
    )

    declined_grant = client.post(
        lesson_base + "/access-grants",
        json={
            "contract": "CreateLessonAccessGrantRequestV1",
            "version_id": lesson["current_version"]["version_id"],
            "audience_kind": "PRINCIPAL",
            "audience_ref": accepted.parent,
            "capability": "VIEW",
            "expires_at": None,
        },
        headers=_headers(accepted.teacher, **{"Idempotency-Key": f"decline-grant-{uuid4()}"}),
    )
    assert declined_grant.status_code == 201, declined_grant.text
    declined = client.post(
        f"/api/lesson-library/v1/me/lesson-invitations/"
        f"{declined_grant.json()['access_grant_id']}/decline",
        headers=_headers(accepted.parent, **{"Idempotency-Key": f"decline-invitation-{uuid4()}"}),
    )
    assert declined.status_code == 200, declined.text
    assert declined.json()["state"] == "DECLINED"


def test_local_storage_example_upload_download_and_delete_routes(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    pdf = _synthetic_pdf()
    uploaded = accepted.client.post(
        "/api/dev/v1/storage-examples/lesson-source-documents",
        files={"file": ("synthetic-example.pdf", pdf, "application/pdf")},
    )
    assert uploaded.status_code == 201, uploaded.text
    receipt = uploaded.json()
    assert receipt["contract"] == "StorageExampleUploadResponseV1"
    assert receipt["byte_length"] == len(pdf)
    assert receipt["sha256"] == hashlib.sha256(pdf).hexdigest()

    downloaded = accepted.client.get(
        f"/api/dev/v1/storage-examples/lesson-source-documents/{receipt['object_id']}"
    )
    assert downloaded.status_code == 200
    assert downloaded.content == pdf
    assert downloaded.headers["X-Content-SHA256"] == receipt["sha256"]
    deleted = accepted.client.delete(
        f"/api/dev/v1/storage-examples/lesson-source-documents/{receipt['object_id']}"
    )
    assert deleted.status_code == 204
    missing = accepted.client.get(
        f"/api/dev/v1/storage-examples/lesson-source-documents/{receipt['object_id']}"
    )
    assert missing.status_code == 404


def test_parent_group_accept_replays_legacy_receipt_without_repeating_effects(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    client = accepted.client
    group_key = f"b5-group-{uuid4()}"
    invite_key = f"b5-invite-{uuid4()}"
    accept_key = f"b5-accept-{uuid4()}"
    group_response = client.post(
        f"/api/lesson-library/v1/organizations/{accepted.organization_id}/parent-groups",
        json={"contract": "CreateParentGroupRequestV1", "display_name": "Synthetic B5 group"},
        headers=_headers(accepted.manager, **{"Idempotency-Key": group_key}),
    )
    assert group_response.status_code == 201, group_response.text
    group_id = group_response.json()["parent_group_id"]
    invite_response = client.post(
        f"/api/lesson-library/v1/organizations/{accepted.organization_id}/parent-groups/"
        f"{group_id}/invitations",
        json={"contract": "InviteParentToGroupRequestV1", "parent_principal_ref": accepted.parent},
        headers=_headers(accepted.manager, **{"Idempotency-Key": invite_key}),
    )
    assert invite_response.status_code == 201, invite_response.text
    membership_id = invite_response.json()["membership_id"]
    accept_path = f"/api/lesson-library/v1/me/parent-group-invitations/{membership_id}/accept"
    accept_response = client.post(
        accept_path,
        headers=_headers(accepted.parent, **{"Idempotency-Key": accept_key}),
    )
    assert accept_response.status_code == 200, accept_response.text

    legacy_response = dict(accept_response.json())
    legacy_response.pop("revision", None)
    legacy_response.pop("revision_source", None)
    accept_scope = f"POST /me/parent-group-invitations/{membership_id}/accept"
    accept_payload = {"membership_id": membership_id}
    receipt_identity = {
        "organization_id": accepted.organization_id,
        "principal_ref": accepted.parent,
        "operation_scope": accept_scope,
        "idempotency_key": accept_key,
    }
    receipt_conditions = tuple(
        getattr(COMMAND_RECEIPTS.c, key) == value
        for key, value in receipt_identity.items()
    )
    with accepted.app.state.be1_runtime.session_factory.begin() as db:
        db.execute(delete(COMMAND_RECEIPTS).where(*receipt_conditions))
        db.execute(insert(COMMAND_RECEIPTS).values(
            **receipt_identity,
            request_fingerprint=LessonLibraryService._fingerprint(accept_payload),
            response_json=legacy_response,
        ))

    def effect_counts() -> tuple[int, int, int, int]:
        with accepted.app.state.be1_runtime.session_factory.begin() as db:
            receipt_count = db.execute(
                select(func.count())
                .select_from(COMMAND_RECEIPTS)
                .where(*receipt_conditions)
            ).scalar_one()
            member_count = db.execute(
                select(func.count()).select_from(PARENT_GROUP_MEMBERS).where(
                    PARENT_GROUP_MEMBERS.c.membership_id == membership_id
                )
            ).scalar_one()
            audit_count = db.execute(
                select(func.count()).select_from(CoreAuditEntryModel).where(
                    CoreAuditEntryModel.resource_id == membership_id,
                    CoreAuditEntryModel.action == "parent_group.invitation.accept",
                )
            ).scalar_one()
            outbox_count = db.execute(
                select(func.count()).select_from(CoreOutboxEventModel).where(
                    CoreOutboxEventModel.event_type == "lesson.parent_group_invited.v1",
                    CoreOutboxEventModel.payload.contains({"membership_id": membership_id}),
                )
            ).scalar_one()
            return receipt_count, member_count, audit_count, outbox_count

    before = effect_counts()
    replay_response = client.post(
        accept_path,
        headers=_headers(accepted.parent, **{"Idempotency-Key": accept_key}),
    )
    assert replay_response.status_code == 200, replay_response.text
    assert replay_response.json()["revision"] == 2
    assert replay_response.json()["revision_source"] == "reconstructed_from_current_row"
    assert effect_counts() == before == (1, 1, 1, 1)
    with accepted.app.state.be1_runtime.session_factory.begin() as db:
        stored = db.execute(
            select(COMMAND_RECEIPTS.c.response_json).where(*receipt_conditions)
        ).scalar_one()
    assert stored == legacy_response

    conflicting_retry = client.post(
        f"/api/lesson-library/v1/organizations/{accepted.organization_id}/parent-groups/"
        f"{group_id}/invitations",
        json={
            "contract": "InviteParentToGroupRequestV1",
            "parent_principal_ref": f"synthetic-other-parent-{uuid4()}",
        },
        headers=_headers(accepted.manager, **{"Idempotency-Key": invite_key}),
    )
    assert conflicting_retry.status_code == 400
    assert conflicting_retry.json()["code"] == "INVALID_IDEMPOTENCY_KEY"


def test_manager_list_routes_default_to_25_and_preserve_limit_and_cursor_inputs(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance

    class CapturingListService:
        def __init__(self) -> None:
            self.parent_group_calls: list[dict[str, object]] = []
            self.access_grant_calls: list[dict[str, object]] = []

        def list_parent_groups(self, **kwargs: object) -> dict[str, object]:
            self.parent_group_calls.append(kwargs)
            return {
                "contract": "ParentGroupPageV1",
                "items": [],
                "next_cursor": "opaque-next-cursor",
            }

        def list_access_grants(self, **kwargs: object) -> dict[str, object]:
            self.access_grant_calls.append(kwargs)
            return {
                "contract": "LessonAccessGrantPageV1",
                "items": [],
                "next_cursor": "opaque-next-cursor",
            }

    service = CapturingListService()
    accepted.app.dependency_overrides[get_lesson_library_service] = lambda: service
    headers = _headers(accepted.manager)
    parent_groups_url = (
        f"/api/lesson-library/v1/organizations/{accepted.organization_id}/parent-groups"
    )
    access_grants_url = (
        f"/api/lesson-library/v1/organizations/{accepted.organization_id}/access-grants"
    )

    try:
        default_groups = accepted.client.get(parent_groups_url, headers=headers)
        assert default_groups.status_code == 200, default_groups.text
        assert default_groups.json()["next_cursor"] == "opaque-next-cursor"
        assert service.parent_group_calls[-1] == {
            "organization_id": accepted.organization_id,
            "limit": 25,
            "cursor": None,
        }

        continued_groups = accepted.client.get(
            parent_groups_url,
            params={"limit": 100, "cursor": "opaque-group-cursor"},
            headers=headers,
        )
        assert continued_groups.status_code == 200, continued_groups.text
        assert service.parent_group_calls[-1] == {
            "organization_id": accepted.organization_id,
            "limit": 100,
            "cursor": "opaque-group-cursor",
        }

        default_grants = accepted.client.get(access_grants_url, headers=headers)
        assert default_grants.status_code == 200, default_grants.text
        assert default_grants.json()["next_cursor"] == "opaque-next-cursor"
        assert service.access_grant_calls[-1] == {
            "organization_id": accepted.organization_id,
            "audience_kind": None,
            "state": None,
            "lesson_id": None,
            "limit": 25,
            "cursor": None,
        }

        continued_grants = accepted.client.get(
            access_grants_url,
            params={
                "audience_kind": "PUBLIC",
                "state": "PENDING_REVIEW",
                "lesson_id": "synthetic-lesson",
                "limit": 100,
                "cursor": "opaque-grant-cursor",
            },
            headers=headers,
        )
        assert continued_grants.status_code == 200, continued_grants.text
        assert service.access_grant_calls[-1] == {
            "organization_id": accepted.organization_id,
            "audience_kind": "PUBLIC",
            "state": "PENDING_REVIEW",
            "lesson_id": "synthetic-lesson",
            "limit": 100,
            "cursor": "opaque-grant-cursor",
        }

        recorded_parent_calls = len(service.parent_group_calls)
        recorded_grant_calls = len(service.access_grant_calls)
        for url in (parent_groups_url, access_grants_url):
            for invalid_limit in (0, 101):
                invalid_page = accepted.client.get(
                    url, params={"limit": invalid_limit}, headers=headers
                )
                assert invalid_page.status_code == 400
                assert invalid_page.json()["code"] == "INVALID_REQUEST"
        assert len(service.parent_group_calls) == recorded_parent_calls
        assert len(service.access_grant_calls) == recorded_grant_calls
    finally:
        accepted.app.dependency_overrides.pop(get_lesson_library_service, None)


def test_parent_can_still_self_revoke_parent_group_membership(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    """CONV-1 AC10: the Parent self-revoke path survives the 404/403 guard change."""
    accepted = lesson_api_acceptance
    client = accepted.client
    org = accepted.organization_id
    group_response = client.post(
        f"/api/lesson-library/v1/organizations/{org}/parent-groups",
        json={"contract": "CreateParentGroupRequestV1", "display_name": "Synthetic CONV-1 group"},
        headers=_headers(accepted.manager, **{"Idempotency-Key": f"conv1-group-{uuid4()}"}),
    )
    assert group_response.status_code == 201, group_response.text
    group_id = group_response.json()["parent_group_id"]
    invite_response = client.post(
        f"/api/lesson-library/v1/organizations/{org}/parent-groups/{group_id}/invitations",
        json={"contract": "InviteParentToGroupRequestV1", "parent_principal_ref": accepted.parent},
        headers=_headers(accepted.manager, **{"Idempotency-Key": f"conv1-invite-{uuid4()}"}),
    )
    assert invite_response.status_code == 201, invite_response.text
    membership_id = invite_response.json()["membership_id"]
    accept_response = client.post(
        f"/api/lesson-library/v1/me/parent-group-invitations/{membership_id}/accept",
        headers=_headers(accepted.parent, **{"Idempotency-Key": f"conv1-accept-{uuid4()}"}),
    )
    assert accept_response.status_code == 200, accept_response.text
    revision = accept_response.json()["revision"]

    revoked = client.delete(
        f"/api/lesson-library/v1/organizations/{org}/parent-groups/{group_id}/members/"
        f"{membership_id}",
        headers=_headers(
            accepted.parent,
            **{
                "If-Match": f'"{revision}"',
                "Idempotency-Key": "conv1-parent-self-revoke",
            },
        ),
    )
    assert revoked.status_code == 200, revoked.text
    assert revoked.json()["membership_id"] == membership_id
    replay = client.delete(
        f"/api/lesson-library/v1/organizations/{org}/parent-groups/{group_id}/members/"
        f"{membership_id}",
        headers=_headers(
            accepted.parent,
            **{
                "If-Match": f'"{revision}"',
                "Idempotency-Key": "conv1-parent-self-revoke",
            },
        ),
    )
    assert replay.status_code == 200, replay.text
    assert replay.json() == revoked.json()
    assert replay.headers["ETag"] == revoked.headers["ETag"]


def test_parent_group_revoke_preconditions_are_reported(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    """T-10c: revoke requires both headers and reports the strong If-Match precondition."""
    accepted = lesson_api_acceptance
    url = (
        f"/api/lesson-library/v1/organizations/{accepted.organization_id}/parent-groups/"
        f"{uuid4()}/members/{uuid4()}"
    )
    key = f"precondition-{uuid4()}"
    missing = accepted.client.delete(
        url,
        headers=_headers(accepted.manager, **{"Idempotency-Key": key}),
    )
    assert missing.status_code == 428, missing.text
    assert missing.json()["code"] == "PRECONDITION_REQUIRED"
    malformed = accepted.client.delete(
        url,
        headers=_headers(
            accepted.manager,
            **{"If-Match": "W/weak", "Idempotency-Key": f"{key}-malformed"},
        ),
    )
    assert malformed.status_code == 400, malformed.text
    assert malformed.json()["field_errors"] == [{"field": "If-Match", "code": "INVALID_FORMAT"}]
    assert missing.headers["X-Request-ID"] == missing.json()["correlation_id"]


# --- FEAT-066 C4 (package Draft 4): keys, stale revisions, upload-session revision and codes ---


class _CleanScanner:
    """Synthetic CLEAN scanner so complete runs without ClamAV (C4 only)."""

    def scan(self, file_obj: Any) -> MalwareScanResult:
        file_obj.read()
        return MalwareScanResult(scanner_name="synthetic", scanner_version="1", verdict="CLEAN")


class _SyntheticParser:
    """Synthetic PDF parser so complete runs without optional parser packages (C4 only)."""

    def extract(self, file_obj: Any, *, file_extension: str) -> LessonDocumentExtraction:
        file_obj.read()
        return LessonDocumentExtraction(
            detected_media_type="application/pdf",
            parser_name="synthetic",
            parser_version="1",
            page_or_slide_count=1,
            page_coverage=(1,),
            extracted_fields={"title": "Synthetic Butterfly Lesson"},
            warnings=(),
        )


def _add_second_teacher(accepted: LessonApiAcceptance) -> str:
    subject = f"synthetic-teacher-two-{uuid4()}"
    with accepted.app.state.be1_runtime.session_factory.begin() as db:
        db.add(
            AdultIdentityModel(
                subject=subject,
                issuer="synthetic-lesson-test-issuer",
                state="active",
                account_role="teacher",
            )
        )
        db.flush()
        db.add(
            OrganizationAssignmentModel(
                assignment_id=str(uuid4()),
                organization_id=accepted.organization_id,
                subject=subject,
                class_id=None,
                role="teacher",
                active=True,
            )
        )
    return subject


def _set_upload_state(accepted: LessonApiAcceptance, upload_id: str, **values: Any) -> None:
    with accepted.app.state.be1_runtime.session_factory.begin() as db:
        db.execute(
            UPLOAD_SESSIONS.update()
            .where(UPLOAD_SESSIONS.c.upload_session_id == upload_id)
            .values(**values)
        )


def _open_upload(accepted: LessonApiAcceptance, lesson: dict[str, object], pdf: bytes) -> str:
    response = accepted.client.post(
        f"/api/lesson-library/v1/organizations/{accepted.organization_id}/lessons/"
        f"{lesson['lesson_id']}/upload-sessions",
        json={
            "contract": "CreateLessonUploadSessionRequestV1",
            "file_name": "synthetic-c4.pdf",
            "media_type": "application/pdf",
            "byte_length": len(pdf),
            "sha256": hashlib.sha256(pdf).hexdigest(),
        },
        headers=_headers(accepted.teacher, **{"Idempotency-Key": f"c4-upload-{uuid4()}"}),
    )
    assert response.status_code == 201, response.text
    assert response.json()["revision"] == 1
    assert response.headers["ETag"] == '"1"'
    return str(response.json()["upload_session_id"])


def _put_part(accepted: LessonApiAcceptance, upload_id: str, body: bytes) -> Any:
    return accepted.client.put(
        f"/api/lesson-library/v1/upload-sessions/{upload_id}/parts/1",
        content=body,
        headers=_headers(
            accepted.teacher,
            **{
                "X-Part-SHA256": hashlib.sha256(body).hexdigest(),
                "Content-Range": f"bytes 0-{len(body) - 1}/{len(body)}",
                "Content-Type": "application/pdf",
            },
        ),
    )


def _abort(accepted: LessonApiAcceptance, upload_id: str, revision: int, key: str) -> Any:
    return accepted.client.delete(
        f"/api/lesson-library/v1/upload-sessions/{upload_id}",
        headers=_headers(
            accepted.teacher, **{"If-Match": f'"{revision}"', "Idempotency-Key": key}
        ),
    )


def _keyed(subject: str, revision: int, key: str) -> dict[str, str]:
    return _headers(subject, **{"If-Match": f'"{revision}"', "Idempotency-Key": key})


def test_c4_lesson_commands_require_keys_replay_and_hide_other_authors(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    client = accepted.client
    lesson = _create_lesson(accepted, visibility="PRIVATE")
    url = (
        f"/api/lesson-library/v1/organizations/{accepted.organization_id}/lessons/"
        f"{lesson['lesson_id']}"
    )
    body = {"contract": "UpdateLessonRequestV1", "content": _content("Bản sửa C4")}

    missing = client.patch(
        url, json=body, headers=_headers(accepted.teacher, **{"If-Match": '"1"'})
    )
    assert missing.status_code == 400, missing.text
    # C4 routes declare the key without an Ellipsis default, so a missing key is REQUIRED.
    assert missing.json()["field_errors"] == [{"field": "Idempotency-Key", "code": "REQUIRED"}]

    key = f"c4-patch-{uuid4()}"
    first = client.patch(url, json=body, headers=_keyed(accepted.teacher, 1, key))
    assert first.status_code == 200, first.text
    assert first.headers["ETag"] == '"2"'
    # Same key, same payload and the old If-Match: replay, not a stale 409 (CT-2).
    replay = client.patch(url, json=body, headers=_keyed(accepted.teacher, 1, key))
    assert replay.status_code == 200, replay.text
    first_version = first.json()["current_version"]["version_id"]
    assert replay.json()["current_version"]["version_id"] == first_version
    assert client.get(url, headers=_headers(accepted.teacher)).headers["ETag"] == '"2"'
    other = client.patch(
        url,
        json={"contract": "UpdateLessonRequestV1", "content": _content("Khác")},
        headers=_keyed(accepted.teacher, 1, key),
    )
    assert other.status_code == 400, other.text
    assert other.json()["code"] == "INVALID_IDEMPOTENCY_KEY"

    # A non-author with a stale If-Match learns nothing: 404, no version, no ETag (R1-04).
    second_teacher = _add_second_teacher(accepted)
    hidden = client.patch(
        url, json=body, headers=_keyed(second_teacher, 1, f"c4-other-{uuid4()}")
    )
    assert hidden.status_code == 404, hidden.text
    assert "current_version" not in hidden.json()
    assert "ETag" not in hidden.headers

    no_key_archive = client.delete(
        url, headers=_headers(accepted.teacher, **{"If-Match": '"2"'})
    )
    assert no_key_archive.status_code == 400, no_key_archive.text
    archive_key = f"c4-archive-{uuid4()}"
    archived = client.delete(url, headers=_keyed(accepted.teacher, 2, archive_key))
    assert archived.status_code == 200, archived.text
    assert archived.json()["state"] == "ARCHIVED"
    archived_again = client.delete(url, headers=_keyed(accepted.teacher, 2, archive_key))
    assert archived_again.status_code == 200, archived_again.text
    assert archived_again.headers["ETag"] == '"3"'


def test_c4_stale_archive_and_manager_keyed_commands(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    client = accepted.client
    lesson = _create_lesson(accepted)
    url = (
        f"/api/lesson-library/v1/organizations/{accepted.organization_id}/lessons/"
        f"{lesson['lesson_id']}"
    )
    stale = client.delete(url, headers=_keyed(accepted.teacher, 9, f"c4-stale-archive-{uuid4()}"))
    assert stale.status_code == 409, stale.text
    assert stale.json()["current_version"] == 1
    assert stale.headers["ETag"] == '"1"'
    # A stale attempt stores no receipt: the same key then succeeds with the current revision.
    retry_key = f"c4-archive-after-stale-{uuid4()}"
    refused = client.delete(url, headers=_keyed(accepted.teacher, 9, retry_key))
    assert refused.status_code == 409, refused.text
    manager_archive = client.delete(url, headers=_keyed(accepted.manager, 1, retry_key))
    assert manager_archive.status_code == 200, manager_archive.text
    assert manager_archive.json()["state"] == "ARCHIVED"
    teacher_after = client.delete(url, headers=_keyed(accepted.teacher, 1, retry_key))
    # The teacher's key was never stored, so this is a new command on revision 2: stale.
    assert teacher_after.status_code == 409, teacher_after.text
    assert teacher_after.json()["current_version"] == 2


def test_c4_upload_session_revision_abort_states_and_codes(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    client = accepted.client
    lesson = _create_lesson(accepted)
    pdf = _synthetic_pdf()

    upload_id = _open_upload(accepted, lesson, pdf)
    status_read = client.get(
        f"/api/lesson-library/v1/upload-sessions/{upload_id}", headers=_headers(accepted.teacher)
    )
    assert status_read.json()["revision"] == 1
    assert status_read.headers["ETag"] == '"1"'
    no_key = client.delete(
        f"/api/lesson-library/v1/upload-sessions/{upload_id}",
        headers=_headers(accepted.teacher, **{"If-Match": '"1"'}),
    )
    assert no_key.status_code == 400, no_key.text
    stale = _abort(accepted, upload_id, 2, f"c4-abort-stale-{uuid4()}")
    assert stale.status_code == 409, stale.text
    assert stale.json()["code"] == "STALE_REVISION"
    assert stale.json()["current_version"] == 1
    assert stale.headers["ETag"] == '"1"'
    key = f"c4-abort-{uuid4()}"
    aborted = _abort(accepted, upload_id, 1, key)
    assert aborted.status_code == 202, aborted.text
    assert aborted.json()["state"] == "ABORTED"
    assert aborted.json()["revision"] == 2
    assert _abort(accepted, upload_id, 1, key).json() == aborted.json()
    repeat = _abort(accepted, upload_id, 2, f"c4-abort-again-{uuid4()}")
    assert repeat.status_code == 202, repeat.text
    assert repeat.json()["state"] == "ABORTED"
    closed_part = _put_part(accepted, upload_id, pdf)
    assert closed_part.status_code == 409, closed_part.text
    assert closed_part.json()["code"] == "UPLOAD_SESSION_STATE_CONFLICT"

    # Part receipts move the revision; a different body for the same part is a conflict.
    parts_id = _open_upload(accepted, lesson, pdf)
    assert _put_part(accepted, parts_id, pdf).status_code == 200
    after_part = client.get(
        f"/api/lesson-library/v1/upload-sessions/{parts_id}", headers=_headers(accepted.teacher)
    )
    assert after_part.json()["revision"] == 2
    conflict = _put_part(accepted, parts_id, bytes(reversed(pdf)))
    assert conflict.status_code == 409, conflict.text
    assert conflict.json()["code"] == "UPLOAD_PART_CONFLICT"

    for state in ("COMPLETED", "FAILED"):
        closed_id = _open_upload(accepted, lesson, pdf)
        _set_upload_state(accepted, closed_id, state=state)
        refused = _abort(accepted, closed_id, 2, f"c4-abort-{state.lower()}-{uuid4()}")
        assert refused.status_code == 409, refused.text
        assert refused.json()["code"] == "UPLOAD_SESSION_STATE_CONFLICT"

    expired_id = _open_upload(accepted, lesson, pdf)
    _set_upload_state(accepted, expired_id, state="EXPIRED")
    assert _put_part(accepted, expired_id, pdf).status_code == 410
    expired_complete = client.post(
        f"/api/lesson-library/v1/upload-sessions/{expired_id}/complete",
        headers=_headers(accepted.teacher, **{"Idempotency-Key": f"c4-complete-{uuid4()}"}),
    )
    assert expired_complete.status_code == 410, expired_complete.text
    assert expired_complete.json()["code"] == "UPLOAD_SESSION_EXPIRED"
    expired_abort = _abort(accepted, expired_id, 2, f"c4-abort-expired-{uuid4()}")
    assert expired_abort.status_code == 410, expired_abort.text

    # An OPEN session past its expiry is marked EXPIRED first, so its revision moves (R2-03).
    lapsed_id = _open_upload(accepted, lesson, pdf)
    _set_upload_state(accepted, lapsed_id, expires_at=datetime.now(UTC) - timedelta(minutes=1))
    lapsed_stale = _abort(accepted, lapsed_id, 1, f"c4-abort-lapsed-{uuid4()}")
    assert lapsed_stale.status_code == 409, lapsed_stale.text
    assert lapsed_stale.headers["ETag"] == '"2"'
    lapsed = _abort(accepted, lapsed_id, 2, f"c4-abort-lapsed-2-{uuid4()}")
    assert lapsed.status_code == 410, lapsed.text


def test_c4_complete_is_202_and_version_create_is_keyed(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    client = accepted.client
    previous_scanner = accepted.app.state.lesson_document_scanner
    previous_parser = accepted.app.state.lesson_document_parser
    accepted.app.state.lesson_document_scanner = _CleanScanner()
    accepted.app.state.lesson_document_parser = _SyntheticParser()
    try:
        lesson = _create_lesson(accepted)
        pdf = _synthetic_pdf()
        upload_id = _open_upload(accepted, lesson, pdf)
        assert _put_part(accepted, upload_id, pdf).status_code == 200
        completed = client.post(
            f"/api/lesson-library/v1/upload-sessions/{upload_id}/complete",
            headers=_headers(accepted.teacher, **{"Idempotency-Key": f"c4-complete-{uuid4()}"}),
        )
        assert completed.status_code == 202, completed.text
        source = completed.json()
        assert source["state"] == "READY_FOR_REVIEW"
        done = client.get(
            f"/api/lesson-library/v1/upload-sessions/{upload_id}",
            headers=_headers(accepted.teacher),
        )
        assert done.json()["state"] == "COMPLETED"
        assert done.json()["revision"] == 3

        versions_url = (
            f"/api/lesson-library/v1/organizations/{accepted.organization_id}/lessons/"
            f"{lesson['lesson_id']}/versions"
        )
        version_body = {
            "contract": "CreateLessonVersionRequestV1",
            "source_document_revision_id": source["revision_id"],
            "content": _content("Phiên bản từ tài liệu C4"),
        }
        no_key = client.post(
            versions_url,
            json=version_body,
            headers=_headers(accepted.teacher, **{"If-Match": '"1"'}),
        )
        assert no_key.status_code == 400, no_key.text
        key = f"c4-version-{uuid4()}"
        created = client.post(
            versions_url, json=version_body, headers=_keyed(accepted.teacher, 1, key)
        )
        assert created.status_code == 201, created.text
        replayed = client.post(
            versions_url, json=version_body, headers=_keyed(accepted.teacher, 1, key)
        )
        assert replayed.status_code == 201, replayed.text
        assert replayed.json()["version_id"] == created.json()["version_id"]
    finally:
        accepted.app.state.lesson_document_scanner = previous_scanner
        accepted.app.state.lesson_document_parser = previous_parser


# ---------------------------------------------------------------------------------------------
# T-10d (TD-24, FR-PL-05, FR-PL-06): only a PUBLIC lesson needs a Manager decision; a private
# share (school, named Parent, Parent group) works for a version in any review state.
# ---------------------------------------------------------------------------------------------
_FULL_READ = {
    "shared": True,
    "public": False,
    "detail": 200,
    "export": 200,
    "catalog": True,
    "pin": True,
}
_PUBLIC_READ = {**_FULL_READ, "shared": False, "public": True}
_NO_READ = {
    "shared": False,
    "public": False,
    "detail": 404,
    "export": 404,
    "catalog": False,
    "pin": False,
}


def _lesson_base(accepted: LessonApiAcceptance, lesson: dict[str, object]) -> str:
    return (
        f"/api/lesson-library/v1/organizations/{accepted.organization_id}/lessons/"
        f"{lesson['lesson_id']}"
    )


def _share(
    accepted: LessonApiAcceptance,
    lesson: dict[str, object],
    kind: str,
    ref: str | None,
    capability: str = "VIEW",
    *,
    actor: str | None = None,
    version_id: str | None = None,
) -> Any:
    return accepted.client.post(
        _lesson_base(accepted, lesson) + "/access-grants",
        json={
            "contract": "CreateLessonAccessGrantRequestV1",
            "version_id": version_id or lesson["current_version"]["version_id"],
            "audience_kind": kind,
            "audience_ref": ref,
            "capability": capability,
            "expires_at": None,
        },
        headers=_headers(
            actor or accepted.teacher,
            **{"Idempotency-Key": f"t10d-{kind.lower()}-{capability.lower()}-{uuid4()}"},
        ),
    )


def _share_pair(
    accepted: LessonApiAcceptance, lesson: dict[str, object], kind: str, ref: str | None
) -> list[dict[str, Any]]:
    """VIEW (list, detail, catalog, pin) and DOWNLOAD (export) grants for one audience."""
    grants = []
    for capability in ("VIEW", "DOWNLOAD"):
        response = _share(accepted, lesson, kind, ref, capability)
        assert response.status_code == 201, response.text
        grants.append(response.json())
    return grants


def _accept_invitations(accepted: LessonApiAcceptance, grants: list[dict[str, Any]]) -> None:
    for grant in grants:
        response = accepted.client.post(
            f"/api/lesson-library/v1/me/lesson-invitations/{grant['access_grant_id']}/accept",
            headers=_headers(accepted.parent, **{"Idempotency-Key": f"t10d-accept-{uuid4()}"}),
        )
        assert response.status_code == 200, response.text
        assert response.json()["state"] == "ACTIVE"


def _revoke(
    accepted: LessonApiAcceptance,
    lesson: dict[str, object],
    grants: list[dict[str, Any]],
    revision: int,
) -> None:
    for grant in grants:
        response = accepted.client.delete(
            f"{_lesson_base(accepted, lesson)}/access-grants/{grant['access_grant_id']}",
            headers=_keyed(accepted.teacher, revision, f"t10d-revoke-{uuid4()}"),
        )
        assert response.status_code == 200, response.text
        assert response.json()["state"] == "REVOKED"


def _library_service(accepted: LessonApiAcceptance, db: Any) -> LessonLibraryService:
    return LessonLibraryService(
        db,
        storage=accepted.storage,
        parser=accepted.app.state.lesson_document_parser,
        scanner=accepted.app.state.lesson_document_scanner,
    )


def _command_receipt_count(accepted: LessonApiAcceptance) -> int:
    with accepted.app.state.be1_runtime.session_factory.begin() as db:
        return int(db.execute(select(func.count()).select_from(COMMAND_RECEIPTS)).scalar_one())


def _parent_view(
    accepted: LessonApiAcceptance, subject: str, lesson: dict[str, object]
) -> dict[str, object]:
    """Every Parent read path for one lesson, including the Parent StoryRun pin lookup."""
    client = accepted.client
    lesson_id = lesson["lesson_id"]
    headers = _headers(subject)
    shared = client.get("/api/lesson-library/v1/me/lessons?source=SHARED", headers=headers)
    public = client.get("/api/lesson-library/v1/me/lessons?source=PUBLIC", headers=headers)
    assert shared.status_code == 200, shared.text
    assert public.status_code == 200, public.text
    detail = client.get(f"/api/lesson-library/v1/me/lessons/{lesson_id}", headers=headers)
    export = client.get(
        f"/api/lesson-library/v1/me/lessons/{lesson_id}/download", headers=headers
    )
    with accepted.app.state.be1_runtime.session_factory.begin() as db:
        service = _library_service(accepted, db)
        catalog = any(
            row["lesson_id"] == lesson_id
            for row in service.list_parent_activity_catalog(parent_principal_ref=subject)
        )
        try:
            pinned = service.get_parent_lesson(parent_principal_ref=subject, lesson_id=lesson_id)
            pin = pinned["version_id"] == lesson["current_version"]["version_id"] and bool(
                pinned["content_sha256"]
            )
        except LessonLibraryError as exc:
            assert (exc.status_code, exc.code) == (404, "LESSON_NOT_FOUND")
            pin = False
    return {
        "shared": any(item["lesson_id"] == lesson_id for item in shared.json()["items"]),
        "public": any(item["lesson_id"] == lesson_id for item in public.json()["items"]),
        "detail": detail.status_code,
        "export": export.status_code,
        "catalog": catalog,
        "pin": pin,
    }


def _version_review_state(accepted: LessonApiAcceptance, lesson: dict[str, object]) -> str:
    with accepted.app.state.be1_runtime.session_factory.begin() as db:
        return str(
            db.execute(
                select(LIBRARY_VERSIONS.c.review_state).where(
                    LIBRARY_VERSIONS.c.version_id == lesson["current_version"]["version_id"]
                )
            ).scalar_one()
        )


def _request_changes(accepted: LessonApiAcceptance, grant: dict[str, Any]) -> None:
    response = accepted.client.post(
        f"/api/lesson-library/v1/organizations/{accepted.organization_id}/access-grants/"
        f"{grant['access_grant_id']}/decision",
        json={
            "contract": "DecideLessonAccessGrantRequestV1",
            "decision": "REQUEST_CHANGES",
            "reason": "Synthetic change request",
        },
        headers=_headers(
            accepted.manager,
            **{"If-Match": '"1"', "Idempotency-Key": f"t10d-changes-{uuid4()}"},
        ),
    )
    assert response.status_code == 200, response.text
    assert response.json()["state"] == "CHANGES_REQUESTED"


@contextmanager
def _second_tenant(accepted: LessonApiAcceptance) -> Iterator[dict[str, str]]:
    """Another synthetic organization with Teacher, Manager and Parent actors."""
    other_org = f"synthetic-lesson-other-org-{uuid4()}"
    other_teacher = f"synthetic-other-teacher-{uuid4()}"
    other_manager = f"synthetic-other-manager-{uuid4()}"
    other_parent = f"synthetic-other-parent-{uuid4()}"
    with accepted.app.state.be1_runtime.session_factory.begin() as db:
        db.add(
            OrganizationModel(
                organization_id=other_org,
                display_name="Synthetic Other Lesson Organization",
                state="active",
            )
        )
        for subject, role in (
            (other_teacher, "teacher"),
            (other_manager, "school_manager"),
            (other_parent, "parent"),
        ):
            db.add(
                AdultIdentityModel(
                    subject=subject,
                    issuer="synthetic-lesson-test-issuer",
                    state="active",
                    account_role=role,
                )
            )
        db.flush()
        db.add(
            OrganizationAssignmentModel(
                assignment_id=str(uuid4()),
                organization_id=other_org,
                subject=other_teacher,
                class_id=None,
                role="teacher",
                active=True,
            )
        )
        db.add(
            OrganizationAssignmentModel(
                assignment_id=str(uuid4()),
                organization_id=other_org,
                subject=other_manager,
                class_id=None,
                role="school_admin",
                active=True,
            )
        )
    try:
        yield {
            "organization": other_org,
            "teacher": other_teacher,
            "manager": other_manager,
            "parent": other_parent,
        }
    finally:
        with accepted.app.state.be1_runtime.session_factory.begin() as db:
            db.execute(
                delete(OrganizationAssignmentModel).where(
                    OrganizationAssignmentModel.organization_id == other_org
                )
            )
            db.execute(
                delete(OrganizationModel).where(OrganizationModel.organization_id == other_org)
            )
            for subject in (other_teacher, other_manager, other_parent):
                db.execute(delete(AdultIdentityModel).where(AdultIdentityModel.subject == subject))


def test_t10d_a_draft_version_shared_to_a_parent_needs_accept_and_revoke_ends_every_read(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    lesson = _create_lesson(accepted, visibility="PRIVATE")
    assert lesson["current_version"]["review_state"] == "DRAFT"

    grants = _share_pair(accepted, lesson, "PRINCIPAL", accepted.parent)
    assert [grant["state"] for grant in grants] == ["INVITED", "INVITED"]
    assert _version_review_state(accepted, lesson) == "DRAFT"  # a private grant never writes it
    assert _parent_view(accepted, accepted.parent, lesson) == _NO_READ  # before accept

    _accept_invitations(accepted, grants)
    assert _parent_view(accepted, accepted.parent, lesson) == _FULL_READ
    assert _version_review_state(accepted, lesson) == "DRAFT"
    with accepted.app.state.be1_runtime.session_factory.begin() as db:
        pinned = _library_service(accepted, db).get_parent_lesson(
            parent_principal_ref=accepted.parent, lesson_id=lesson["lesson_id"]
        )
        stored_hash = db.execute(
            select(LIBRARY_VERSIONS.c.structured_content_hash).where(
                LIBRARY_VERSIONS.c.version_id == lesson["current_version"]["version_id"]
            )
        ).scalar_one()
    # (i) the Parent StoryRun lesson pin check: get_parent_lesson plus the exact version/hash match
    assert pinned["version_id"] == lesson["current_version"]["version_id"]
    assert pinned["content_sha256"] == stored_hash

    _revoke(accepted, lesson, grants, revision=2)
    assert _parent_view(accepted, accepted.parent, lesson) == _NO_READ


def test_t10d_b_decline_and_expiry_end_every_read_path(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    lesson = _create_lesson(accepted, visibility="PRIVATE")

    declined = _share_pair(accepted, lesson, "PRINCIPAL", accepted.parent)
    for grant in declined:
        response = accepted.client.post(
            f"/api/lesson-library/v1/me/lesson-invitations/{grant['access_grant_id']}/decline",
            headers=_headers(accepted.parent, **{"Idempotency-Key": f"t10d-decline-{uuid4()}"}),
        )
        assert response.status_code == 200, response.text
        assert response.json()["state"] == "DECLINED"
    assert _parent_view(accepted, accepted.parent, lesson) == _NO_READ

    expiring = _share_pair(accepted, lesson, "PRINCIPAL", accepted.parent)
    _accept_invitations(accepted, expiring)
    assert _parent_view(accepted, accepted.parent, lesson) == _FULL_READ
    with accepted.app.state.be1_runtime.session_factory.begin() as db:
        db.execute(
            update(ACCESS_GRANTS)
            .where(
                ACCESS_GRANTS.c.access_grant_id.in_(
                    [grant["access_grant_id"] for grant in expiring]
                )
            )
            .values(expires_at=datetime.now(UTC) - timedelta(minutes=1))
        )
    assert _parent_view(accepted, accepted.parent, lesson) == _NO_READ


def test_t10d_c_parent_group_member_reads_a_draft_version_and_others_do_not(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    client = accepted.client
    org = accepted.organization_id
    lesson = _create_lesson(accepted, visibility="PRIVATE")
    group = client.post(
        f"/api/lesson-library/v1/organizations/{org}/parent-groups",
        json={"contract": "CreateParentGroupRequestV1", "display_name": "Synthetic T-10d group"},
        headers=_headers(accepted.manager, **{"Idempotency-Key": f"t10d-group-{uuid4()}"}),
    )
    assert group.status_code == 201, group.text
    group_id = group.json()["parent_group_id"]
    invitation = client.post(
        f"/api/lesson-library/v1/organizations/{org}/parent-groups/{group_id}/invitations",
        json={"contract": "InviteParentToGroupRequestV1", "parent_principal_ref": accepted.parent},
        headers=_headers(accepted.manager, **{"Idempotency-Key": f"t10d-invite-{uuid4()}"}),
    )
    assert invitation.status_code == 201, invitation.text
    membership_id = invitation.json()["membership_id"]
    member = client.post(
        f"/api/lesson-library/v1/me/parent-group-invitations/{membership_id}/accept",
        headers=_headers(accepted.parent, **{"Idempotency-Key": f"t10d-member-{uuid4()}"}),
    )
    assert member.status_code == 200, member.text

    grants = _share_pair(accepted, lesson, "PARENT_GROUP", group_id)
    assert [grant["state"] for grant in grants] == ["ACTIVE", "ACTIVE"]
    assert _version_review_state(accepted, lesson) == "DRAFT"
    assert _parent_view(accepted, accepted.parent, lesson) == _FULL_READ
    with _second_tenant(accepted) as other:
        assert _parent_view(accepted, other["parent"], lesson) == _NO_READ  # not a member

    def set_group_state(state: str) -> None:
        with accepted.app.state.be1_runtime.session_factory.begin() as db:
            db.execute(
                update(PARENT_GROUPS)
                .where(PARENT_GROUPS.c.parent_group_id == group_id)
                .values(state=state)
            )

    set_group_state("archived")
    assert _parent_view(accepted, accepted.parent, lesson) == _NO_READ
    refused = _share(accepted, lesson, "PARENT_GROUP", group_id)
    assert (refused.status_code, refused.json()["code"]) == (409, "INVALID_STATE_TRANSITION")
    set_group_state("active")
    assert _parent_view(accepted, accepted.parent, lesson) == _FULL_READ

    removed = client.delete(
        f"/api/lesson-library/v1/organizations/{org}/parent-groups/{group_id}"
        f"/members/{membership_id}",
        headers=_headers(
            accepted.manager,
            **{"If-Match": '"2"', "Idempotency-Key": f"t10d-revoke-{uuid4()}"},
        ),
    )
    assert removed.status_code == 200, removed.text
    assert _parent_view(accepted, accepted.parent, lesson) == _NO_READ


def test_t10d_d_school_share_of_a_draft_version_is_active_and_never_reaches_parents(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    lesson = _create_lesson(accepted, visibility="PRIVATE")
    response = _share(accepted, lesson, "ORGANIZATION", accepted.organization_id)
    assert response.status_code == 201, response.text
    assert response.json()["state"] == "ACTIVE"
    assert _version_review_state(accepted, lesson) == "DRAFT"
    detail = accepted.client.get(_lesson_base(accepted, lesson), headers=_headers(accepted.teacher))
    assert detail.status_code == 200
    assert detail.json()["visibility"] == "SCHOOL"
    # a school share is not a Parent grant
    assert _parent_view(accepted, accepted.parent, lesson) == _NO_READ


def test_t10d_e_public_request_still_needs_the_manager_and_parents_read_it_only_after(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    lesson = _create_lesson(accepted, visibility="PRIVATE")
    view = _create_public_grant(accepted, lesson, capability="VIEW")
    download = _create_public_grant(accepted, lesson, capability="DOWNLOAD")
    assert _version_review_state(accepted, lesson) == "PENDING_REVIEW"
    assert _parent_view(accepted, accepted.parent, lesson) == _NO_READ
    for grant in (view, download):
        _approve_public_grant(accepted, grant)
    assert _version_review_state(accepted, lesson) == "APPROVED"
    assert _parent_view(accepted, accepted.parent, lesson) == _PUBLIC_READ


def test_t10d_f_a_declined_public_request_leaves_private_shares_readable_and_shareable(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    lesson = _create_lesson(accepted, visibility="PRIVATE")
    private = _share_pair(accepted, lesson, "PRINCIPAL", accepted.parent)
    _accept_invitations(accepted, private)
    assert _parent_view(accepted, accepted.parent, lesson) == _FULL_READ

    requested = _create_public_grant(accepted, lesson, capability="VIEW")
    assert _version_review_state(accepted, lesson) == "PENDING_REVIEW"
    assert _parent_view(accepted, accepted.parent, lesson) == _FULL_READ  # shared yes, public no

    _request_changes(accepted, requested)
    assert _version_review_state(accepted, lesson) == "CHANGES_REQUESTED"
    assert _parent_view(accepted, accepted.parent, lesson) == _FULL_READ
    again = _share(accepted, lesson, "PRINCIPAL", accepted.parent, "REUSE")
    assert again.status_code == 201, again.text
    assert again.json()["state"] == "INVITED"

    view = _create_public_grant(accepted, lesson, capability="VIEW")
    download = _create_public_grant(accepted, lesson, capability="DOWNLOAD")
    for grant in (view, download):
        _approve_public_grant(accepted, grant)
    assert _version_review_state(accepted, lesson) == "APPROVED"
    after = _parent_view(accepted, accepted.parent, lesson)
    assert after == {**_FULL_READ, "public": True}
    # the private grants are untouched by the decision
    with accepted.app.state.be1_runtime.session_factory.begin() as db:
        states = db.execute(
            select(ACCESS_GRANTS.c.state).where(
                ACCESS_GRANTS.c.access_grant_id.in_([g["access_grant_id"] for g in private])
            )
        ).scalars().all()
    assert set(states) == {"ACTIVE"}


def test_t10d_g_unchanged_refusals_hidden_archived_and_tenant_isolation(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    client = accepted.client
    lesson = _create_lesson(accepted, visibility="PRIVATE")
    lesson_id = lesson["lesson_id"]
    base = _lesson_base(accepted, lesson)

    # share to self, non-author, unknown version, past expiry
    own = _share(accepted, lesson, "PRINCIPAL", accepted.teacher)
    assert (own.status_code, own.json()["code"]) == (400, "INVALID_REQUEST")
    not_author = _share(accepted, lesson, "PRINCIPAL", accepted.parent, actor=accepted.manager)
    assert not_author.status_code in {403, 404}, not_author.text
    unknown = _share(accepted, lesson, "PRINCIPAL", accepted.parent, version_id="unknown-version")
    assert (unknown.status_code, unknown.json()["code"]) == (404, "RESOURCE_NOT_FOUND")
    past = client.post(
        base + "/access-grants",
        json={
            "contract": "CreateLessonAccessGrantRequestV1",
            "version_id": lesson["current_version"]["version_id"],
            "audience_kind": "PRINCIPAL",
            "audience_ref": accepted.parent,
            "capability": "VIEW",
            "expires_at": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
        },
        headers=_headers(accepted.teacher, **{"Idempotency-Key": f"t10d-past-{uuid4()}"}),
    )
    assert (past.status_code, past.json()["code"]) == (400, "INVALID_REQUEST")

    # hide ends Parent reads of a private share; restore brings them back
    grants = _share_pair(accepted, lesson, "PRINCIPAL", accepted.parent)
    _accept_invitations(accepted, grants)
    assert _parent_view(accepted, accepted.parent, lesson) == _FULL_READ
    moderation = f"/api/lesson-library/v1/platform/lessons/{lesson_id}/moderation"
    hidden = client.patch(
        moderation,
        json={"contract": "ModerateLessonRequestV1", "state": "HIDDEN", "reason": "Synthetic test"},
        headers=_keyed(accepted.platform_admin, 1, f"t10d-hide-{uuid4()}"),
    )
    assert hidden.status_code == 200, hidden.text
    assert _parent_view(accepted, accepted.parent, lesson) == _NO_READ
    shown = client.patch(
        moderation,
        json={"contract": "ModerateLessonRequestV1", "state": "VISIBLE", "reason": "Synthetic ok"},
        headers=_keyed(accepted.platform_admin, 2, f"t10d-show-{uuid4()}"),
    )
    assert shown.status_code == 200, shown.text
    assert _parent_view(accepted, accepted.parent, lesson) == _FULL_READ

    # AC-63: another organization neither lists, reads nor shares into this one, and another
    # Parent sees no lesson that was shared to someone else or to the school
    school = _share(accepted, lesson, "ORGANIZATION", accepted.organization_id)
    assert school.status_code == 201, school.text
    with _second_tenant(accepted) as other:
        other_base = f"/api/lesson-library/v1/organizations/{other['organization']}/lessons"
        listed = client.get(other_base, headers=_headers(other["teacher"]))
        assert listed.status_code == 200, listed.text
        assert all(item["lesson_id"] != lesson_id for item in listed.json()["items"])
        crossed = client.get(f"{other_base}/{lesson_id}", headers=_headers(other["teacher"]))
        assert crossed.status_code == 404
        assert client.get(base, headers=_headers(other["teacher"])).status_code in {403, 404}
        cross_share = _share(accepted, lesson, "ORGANIZATION", other["organization"])
        assert (cross_share.status_code, cross_share.json()["code"]) == (404, "RESOURCE_NOT_FOUND")
        foreign = _share(accepted, lesson, "PRINCIPAL", accepted.parent, actor=other["teacher"])
        assert foreign.status_code in {403, 404}, foreign.text
        assert _parent_view(accepted, other["parent"], lesson) == _NO_READ

    current = client.get(base, headers=_headers(accepted.teacher))
    assert current.status_code == 200, current.text
    archived = client.delete(
        base,
        headers=_headers(
            accepted.teacher,
            **{"If-Match": current.headers["ETag"], "Idempotency-Key": f"t10d-archive-{uuid4()}"},
        ),
    )
    assert archived.status_code == 200, archived.text
    assert _parent_view(accepted, accepted.parent, lesson) == _NO_READ
    after_archive = _share(accepted, lesson, "PRINCIPAL", accepted.parent)
    assert (after_archive.status_code, after_archive.json()["code"]) == (404, "RESOURCE_NOT_FOUND")


def test_t10d_h_a_forced_public_grant_on_an_unapproved_version_stays_invisible(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    lesson = _create_lesson(accepted, visibility="PRIVATE")
    grants = [
        _create_public_grant(accepted, lesson, capability="VIEW"),
        _create_public_grant(accepted, lesson, capability="DOWNLOAD"),
    ]
    with accepted.app.state.be1_runtime.session_factory.begin() as db:
        db.execute(
            update(ACCESS_GRANTS)
            .where(ACCESS_GRANTS.c.access_grant_id.in_([g["access_grant_id"] for g in grants]))
            .values(state="ACTIVE")
        )
        db.execute(
            update(LIBRARY_VERSIONS)
            .where(LIBRARY_VERSIONS.c.version_id == lesson["current_version"]["version_id"])
            .values(review_state="DRAFT")
        )
    assert _parent_view(accepted, accepted.parent, lesson) == _NO_READ


def test_t10d_j_an_occurrence_pin_of_a_privately_shared_draft_version_is_still_refused(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    """D8: the occurrence pin keeps its APPROVED gate (T-3a-DEC-6); T-10d does not change it."""
    accepted = lesson_api_acceptance
    lesson = _create_lesson(accepted, visibility="PRIVATE")
    grants = _share_pair(accepted, lesson, "PRINCIPAL", accepted.parent)
    _accept_invitations(accepted, grants)
    assert _parent_view(accepted, accepted.parent, lesson) == _FULL_READ
    with accepted.app.state.be1_runtime.session_factory.begin() as db:
        stored_hash = db.execute(
            select(LIBRARY_VERSIONS.c.structured_content_hash).where(
                LIBRARY_VERSIONS.c.version_id == lesson["current_version"]["version_id"]
            )
        ).scalar_one()
        ref = LessonVersionRefV1(
            lesson_id=str(lesson["lesson_id"]),
            version_id=str(lesson["current_version"]["version_id"]),
            content_sha256=stored_hash,
        )
        teacher = VerifiedPrincipal(
            subject=accepted.teacher,
            issuer="synthetic-lesson-test-issuer",
            roles=frozenset(),
            token_id="synthetic-lesson-test-token",
        )
        with pytest.raises(LessonOccurrenceError) as refused:
            LessonOccurrenceService(db).resolve_lesson_pin(
                principal=teacher, organization_id=accepted.organization_id, ref=ref
            )
    assert (refused.value.status_code, refused.value.code) == (409, "INVALID_STATE_TRANSITION")


def test_versions_keyset_no_duplicates_equal_timestamps(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    lesson = _create_lesson(accepted)
    revision = 1
    for version_no in range(2, 5):
        _, revision = _revise_lesson(
            accepted,
            lesson_id=str(lesson["lesson_id"]),
            expected_revision=revision,
            title=f"Synthetic version {version_no}",
        )
    equal_timestamp = datetime(2026, 11, 24, 12, 0, tzinfo=UTC)
    with accepted.app.state.be1_runtime.session_factory.begin() as db:
        db.execute(
            update(LIBRARY_VERSIONS)
            .where(LIBRARY_VERSIONS.c.lesson_id == lesson["lesson_id"])
            .values(created_at=equal_timestamp)
        )

    base = _lesson_base(accepted, lesson) + "/versions"
    before = _command_receipt_count(accepted)
    cursor = None
    items: list[dict[str, Any]] = []
    while True:
        params: dict[str, str | int] = {"limit": 2}
        if cursor is not None:
            params["cursor"] = cursor
        response = accepted.client.get(
            base, params=params, headers=_headers(accepted.teacher)
        )
        assert response.status_code == 200, response.text
        assert response.headers["Cache-Control"] == "private, no-store"
        items.extend(response.json()["items"])
        cursor = response.json()["next_cursor"]
        if cursor is None:
            break
    after = _command_receipt_count(accepted)

    assert before == after
    assert [item["version_no"] for item in items] == [4, 3, 2, 1]
    assert len({item["version_id"] for item in items}) == len(items)


def test_version_get_returns_exact_hash(lesson_api_acceptance: LessonApiAcceptance) -> None:
    accepted = lesson_api_acceptance
    lesson = _create_lesson(accepted)
    original = lesson["current_version"]
    updated, _revision = _revise_lesson(
        accepted,
        lesson_id=str(lesson["lesson_id"]),
        expected_revision=1,
        title="Synthetic exact version two",
    )
    base = _lesson_base(accepted, lesson) + "/versions"
    before = _command_receipt_count(accepted)
    original_read = accepted.client.get(
        f"{base}/{original['version_id']}", headers=_headers(accepted.teacher)
    )
    current_read = accepted.client.get(
        f"{base}/{updated['current_version']['version_id']}",
        headers=_headers(accepted.teacher),
    )
    after = _command_receipt_count(accepted)

    assert original_read.status_code == current_read.status_code == 200
    assert original_read.headers["Cache-Control"] == "private, no-store"
    assert original_read.json()["version_id"] == original["version_id"]
    assert original_read.json()["structured_content_hash"] == original["structured_content_hash"]
    assert original_read.json()["content"]["title"] == lesson["current_version"]["content"]["title"]
    assert current_read.json()["version_id"] == updated["current_version"]["version_id"]
    assert current_read.json()["content"]["title"] == "Synthetic exact version two"
    assert before == after


def test_version_read_missing_and_cross_tenant_equal_404(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    lesson = _create_lesson(accepted)
    other_lesson = _create_lesson(accepted, title="Synthetic second lesson")
    base = _lesson_base(accepted, lesson) + "/versions"
    missing_version = accepted.client.get(
        f"{base}/missing-version", headers=_headers(accepted.teacher)
    )
    other_lesson_version = accepted.client.get(
        f"{base}/{other_lesson['current_version']['version_id']}",
        headers=_headers(accepted.teacher),
    )
    assert missing_version.status_code == other_lesson_version.status_code == 404
    assert missing_version.json()["code"] == "RESOURCE_NOT_FOUND"
    assert other_lesson_version.json()["code"] == "RESOURCE_NOT_FOUND"
    assert missing_version.json()["message"] == other_lesson_version.json()["message"]

    with _second_tenant(accepted) as other:
        foreign = _create_lesson_in_org(
            accepted,
            organization_id=other["organization"],
            teacher=other["teacher"],
            title="Synthetic foreign lesson",
        )
        foreign_lesson_read = accepted.client.get(
            f"/api/lesson-library/v1/organizations/{accepted.organization_id}/lessons/"
            f"{foreign['lesson_id']}/versions/{foreign['current_version']['version_id']}",
            headers=_headers(accepted.teacher),
        )
        absent_lesson_read = accepted.client.get(
            f"/api/lesson-library/v1/organizations/{accepted.organization_id}/lessons/"
            "missing-lesson/versions/missing-version",
            headers=_headers(accepted.teacher),
        )
        assert foreign_lesson_read.status_code == absent_lesson_read.status_code == 404
        assert foreign_lesson_read.json()["code"] == "RESOURCE_NOT_FOUND"
        assert absent_lesson_read.json()["code"] == "RESOURCE_NOT_FOUND"
        assert foreign_lesson_read.json()["message"] == absent_lesson_read.json()["message"]


def test_public_search_hides_private_school_selected_other_tenant(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    marker = f"T10aVisibility{uuid4().hex}"
    with _second_tenant(accepted) as other:
        private_lesson = _create_lesson_in_org(
            accepted,
            organization_id=other["organization"],
            teacher=other["teacher"],
            title=f"{marker} private",
        )
        school_lesson = _create_lesson_in_org(
            accepted,
            organization_id=other["organization"],
            teacher=other["teacher"],
            title=f"{marker} school",
            visibility="SCHOOL",
        )
        selected_lesson = _create_lesson_in_org(
            accepted,
            organization_id=other["organization"],
            teacher=other["teacher"],
            title=f"{marker} selected",
        )
        selected_grant = accepted.client.post(
            f"/api/lesson-library/v1/organizations/{other['organization']}/lessons/"
            f"{selected_lesson['lesson_id']}/access-grants",
            json={
                "contract": "CreateLessonAccessGrantRequestV1",
                "version_id": selected_lesson["current_version"]["version_id"],
                "audience_kind": "PRINCIPAL",
                "audience_ref": other["parent"],
                "capability": "REUSE",
                "expires_at": None,
            },
            headers=_headers(other["teacher"], **{"Idempotency-Key": f"selected-{uuid4()}"}),
        )
        assert selected_grant.status_code == 201, selected_grant.text
        accepted_invite = accepted.client.post(
            f"/api/lesson-library/v1/me/lesson-invitations/"
            f"{selected_grant.json()['access_grant_id']}/accept",
            headers=_headers(other["parent"], **{"Idempotency-Key": f"selected-accept-{uuid4()}"}),
        )
        assert accepted_invite.status_code == 200, accepted_invite.text

        public_lesson = _create_lesson_in_org(
            accepted,
            organization_id=other["organization"],
            teacher=other["teacher"],
            title=f"{marker} public",
        )
        public_grant = _create_public_grant_in_org(
            accepted,
            organization_id=other["organization"],
            teacher=other["teacher"],
            lesson=public_lesson,
        )
        _approve_public_grant_in_org(
            accepted,
            organization_id=other["organization"],
            manager=other["manager"],
            grant=public_grant,
        )

        before = _command_receipt_count(accepted)
        response = accepted.client.get(
            f"/api/lesson-library/v1/organizations/{accepted.organization_id}/public-lessons",
            params={"q": marker},
            headers=_headers(accepted.teacher),
        )
        after = _command_receipt_count(accepted)

    assert response.status_code == 200, response.text
    assert response.headers["Cache-Control"] == "private, no-store"
    assert [item["lesson_id"] for item in response.json()["items"]] == [public_lesson["lesson_id"]]
    first_item = response.json()["items"][0]
    assert first_item["version_id"] == public_lesson["current_version"]["version_id"]
    assert (
        first_item["structured_content_hash"]
        == public_lesson["current_version"]["structured_content_hash"]
    )
    assert not {
        private_lesson["lesson_id"], school_lesson["lesson_id"], selected_lesson["lesson_id"]
    }.intersection(item["lesson_id"] for item in response.json()["items"])
    assert before == after


def test_filters_before_page_boundary(lesson_api_acceptance: LessonApiAcceptance) -> None:
    accepted = lesson_api_acceptance
    marker = f"T10aFilterBoundary{uuid4().hex}"
    nonmatch = _create_lesson(accepted, title="Unrelated synthetic public item")
    match = _create_lesson(accepted, title=f"{marker} matching public item")
    for lesson in (nonmatch, match):
        grant = _create_public_grant(accepted, lesson, capability="VIEW")
        _approve_public_grant(accepted, grant)
    newer = datetime(2026, 11, 24, 12, 0, tzinfo=UTC)
    older = newer - timedelta(days=1)
    with accepted.app.state.be1_runtime.session_factory.begin() as db:
        db.execute(
            update(LIBRARY_ITEMS)
            .where(LIBRARY_ITEMS.c.lesson_id == nonmatch["lesson_id"])
            .values(updated_at=newer)
        )
        db.execute(
            update(LIBRARY_ITEMS)
            .where(LIBRARY_ITEMS.c.lesson_id == match["lesson_id"])
            .values(updated_at=older)
        )
    public_response = accepted.client.get(
        f"/api/lesson-library/v1/organizations/{accepted.organization_id}/public-lessons",
        params={"q": marker, "limit": 1},
        headers=_headers(accepted.teacher),
    )
    assert public_response.status_code == 200, public_response.text
    assert [item["lesson_id"] for item in public_response.json()["items"]] == [match["lesson_id"]]

    parent_nonmatch = _create_lesson(accepted, title="Unrelated private parent item")
    parent_match = _create_lesson(accepted, title=f"{marker} matching private parent item")
    for lesson in (parent_nonmatch, parent_match):
        grants = _share_pair(accepted, lesson, "PRINCIPAL", accepted.parent)
        _accept_invitations(accepted, grants)
    with accepted.app.state.be1_runtime.session_factory.begin() as db:
        db.execute(
            update(LIBRARY_ITEMS)
            .where(LIBRARY_ITEMS.c.lesson_id == parent_nonmatch["lesson_id"])
            .values(created_at=newer)
        )
        db.execute(
            update(LIBRARY_ITEMS)
            .where(LIBRARY_ITEMS.c.lesson_id == parent_match["lesson_id"])
            .values(created_at=older)
        )
    parent_response = accepted.client.get(
        "/api/lesson-library/v1/me/lessons",
        params={"source": "SHARED", "q": marker, "limit": 1},
        headers=_headers(accepted.parent),
    )
    assert parent_response.status_code == 200, parent_response.text
    assert [item["lesson_id"] for item in parent_response.json()["items"]] == [
        parent_match["lesson_id"]
    ]


def test_cursor_rejects_different_filter(lesson_api_acceptance: LessonApiAcceptance) -> None:
    accepted = lesson_api_acceptance
    marker = f"T10aCursorScope{uuid4().hex}"
    lessons = [_create_lesson(accepted, title=f"{marker} {index}") for index in range(2)]
    for lesson in lessons:
        grant = _create_public_grant(accepted, lesson, capability="VIEW")
        _approve_public_grant(accepted, grant)
    path = f"/api/lesson-library/v1/organizations/{accepted.organization_id}/public-lessons"
    first = accepted.client.get(
        path, params={"q": marker, "limit": 1}, headers=_headers(accepted.teacher)
    )
    assert first.status_code == 200, first.text
    cursor = first.json()["next_cursor"]
    assert cursor
    refused = accepted.client.get(
        path,
        params={"q": f"{marker} changed", "limit": 1, "cursor": cursor},
        headers=_headers(accepted.teacher),
    )
    assert refused.status_code == 400
    assert refused.json()["code"] == "INVALID_REQUEST"


def test_limit_101_invalid_request(lesson_api_acceptance: LessonApiAcceptance) -> None:
    accepted = lesson_api_acceptance
    response = accepted.client.get(
        f"/api/lesson-library/v1/organizations/{accepted.organization_id}/public-lessons?limit=101",
        headers=_headers(accepted.teacher),
    )
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"


def test_revoked_public_grant_not_visible(lesson_api_acceptance: LessonApiAcceptance) -> None:
    accepted = lesson_api_acceptance
    marker = f"T10aEligibility{uuid4().hex}"
    revoked_lesson = _create_lesson(accepted, title=f"{marker} revoked")
    expired_lesson = _create_lesson(accepted, title=f"{marker} expired")
    hidden_lesson = _create_lesson(accepted, title=f"{marker} hidden")
    unapproved_lesson = _create_lesson(accepted, title=f"{marker} unapproved")
    grants: dict[str, dict[str, object]] = {}
    for key, lesson in (
        ("revoked", revoked_lesson),
        ("expired", expired_lesson),
        ("hidden", hidden_lesson),
        ("unapproved", unapproved_lesson),
    ):
        grants[key] = _create_public_grant(accepted, lesson, capability="VIEW")
    for key in ("revoked", "expired", "hidden"):
        _approve_public_grant(accepted, grants[key])

    # Positive control: an eligible approved PUBLIC lesson; and a SCHOOL lesson whose own
    # PUBLIC grant stays pending (never approved) must stay absent.
    eligible_lesson = _create_lesson(accepted, title=f"{marker} eligible")
    _approve_public_grant(
        accepted, _create_public_grant(accepted, eligible_lesson, capability="VIEW")
    )
    pending_lesson = _create_lesson(accepted, title=f"{marker} pending", visibility="SCHOOL")
    _create_public_grant(accepted, pending_lesson, capability="VIEW")

    revoked = accepted.client.delete(
        f"{_lesson_base(accepted, revoked_lesson)}/access-grants/"
        f"{grants['revoked']['access_grant_id']}",
        headers=_keyed(accepted.teacher, 2, f"revoke-public-{uuid4()}"),
    )
    assert revoked.status_code == 200, revoked.text
    with accepted.app.state.be1_runtime.session_factory.begin() as db:
        db.execute(
            update(ACCESS_GRANTS)
            .where(ACCESS_GRANTS.c.access_grant_id == grants["expired"]["access_grant_id"])
            .values(expires_at=datetime.now(UTC) - timedelta(minutes=1))
        )
        db.execute(
            update(ACCESS_GRANTS)
            .where(ACCESS_GRANTS.c.access_grant_id == grants["unapproved"]["access_grant_id"])
            .values(state="ACTIVE")
        )
        db.execute(
            update(LIBRARY_VERSIONS)
            .where(LIBRARY_VERSIONS.c.lesson_id == unapproved_lesson["lesson_id"])
            .values(review_state="DRAFT")
        )
    hidden = accepted.client.patch(
        f"/api/lesson-library/v1/platform/lessons/{hidden_lesson['lesson_id']}/moderation",
        json={
            "contract": "ModerateLessonRequestV1",
            "state": "HIDDEN",
            "reason": "Synthetic visibility test",
        },
        headers=_keyed(accepted.platform_admin, 1, f"hide-public-{uuid4()}"),
    )
    assert hidden.status_code == 200, hidden.text

    before = _command_receipt_count(accepted)
    response = accepted.client.get(
        f"/api/lesson-library/v1/organizations/{accepted.organization_id}/public-lessons",
        params={"q": marker},
        headers=_headers(accepted.teacher),
    )
    after = _command_receipt_count(accepted)
    assert response.status_code == 200, response.text
    assert response.headers["Cache-Control"] == "private, no-store"
    assert [item["lesson_id"] for item in response.json()["items"]] == [
        eligible_lesson["lesson_id"]
    ]
    assert before == after


def test_parent_shared_scope_unchanged(lesson_api_acceptance: LessonApiAcceptance) -> None:
    accepted = lesson_api_acceptance
    marker = f"T10aParentShared{uuid4().hex}"
    lesson = _create_lesson(accepted, title=f"{marker} shared lesson", visibility="PRIVATE")
    grants = _share_pair(accepted, lesson, "PRINCIPAL", accepted.parent)
    _accept_invitations(accepted, grants)
    before = _command_receipt_count(accepted)
    response = accepted.client.get(
        "/api/lesson-library/v1/me/lessons",
        params={"source": "SHARED", "q": marker},
        headers=_headers(accepted.parent),
    )
    after = _command_receipt_count(accepted)
    assert response.status_code == 200, response.text
    assert response.headers["Cache-Control"] == "private, no-store"
    assert [item["lesson_id"] for item in response.json()["items"]] == [lesson["lesson_id"]]
    assert before == after

    _revoke(accepted, lesson, grants, revision=2)
    revoked_page = accepted.client.get(
        "/api/lesson-library/v1/me/lessons",
        params={"source": "SHARED", "q": marker},
        headers=_headers(accepted.parent),
    )
    assert revoked_page.status_code == 200, revoked_page.text
    assert all(item["lesson_id"] != lesson["lesson_id"] for item in revoked_page.json()["items"])


def test_search_case_and_unicode(lesson_api_acceptance: LessonApiAcceptance) -> None:
    accepted = lesson_api_acceptance
    marker = uuid4().hex
    lesson = _create_lesson(accepted, title=f"Bài học về bướm {marker}")
    grant = _create_public_grant(accepted, lesson, capability="VIEW")
    _approve_public_grant(accepted, grant)
    path = f"/api/lesson-library/v1/organizations/{accepted.organization_id}/public-lessons"
    q_response = accepted.client.get(
        path,
        params={"q": f"  BƯỚM {marker.upper()}  "},
        headers=_headers(accepted.teacher),
    )
    topic_response = accepted.client.get(
        path, params={"topic": "  cOn BƯỚM  "}, headers=_headers(accepted.teacher)
    )
    assert q_response.status_code == topic_response.status_code == 200
    assert [item["lesson_id"] for item in q_response.json()["items"]] == [lesson["lesson_id"]]
    # The topic is shared by every synthetic lesson, so only membership is asserted.
    assert lesson["lesson_id"] in [item["lesson_id"] for item in topic_response.json()["items"]]


def test_publication_revocation_between_pages_fails_closed(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    marker = f"T10aRevokeBetweenPages{uuid4().hex}"
    lessons = [_create_lesson(accepted, title=f"{marker} {index}") for index in range(2)]
    grants = [_create_public_grant(accepted, lesson, capability="VIEW") for lesson in lessons]
    for grant in grants:
        _approve_public_grant(accepted, grant)
    newest = datetime(2026, 11, 24, 12, 0, tzinfo=UTC)
    with accepted.app.state.be1_runtime.session_factory.begin() as db:
        db.execute(
            update(LIBRARY_ITEMS)
            .where(LIBRARY_ITEMS.c.lesson_id == lessons[0]["lesson_id"])
            .values(updated_at=newest)
        )
        db.execute(
            update(LIBRARY_ITEMS)
            .where(LIBRARY_ITEMS.c.lesson_id == lessons[1]["lesson_id"])
            .values(updated_at=newest - timedelta(days=1))
        )
    path = f"/api/lesson-library/v1/organizations/{accepted.organization_id}/public-lessons"
    first = accepted.client.get(
        path, params={"q": marker, "limit": 1}, headers=_headers(accepted.teacher)
    )
    assert first.status_code == 200, first.text
    assert first.json()["next_cursor"]
    first_id = first.json()["items"][0]["lesson_id"]
    remaining_index = next(
        index for index, lesson in enumerate(lessons) if lesson["lesson_id"] != first_id
    )
    remaining = lessons[remaining_index]
    revoked = accepted.client.delete(
        f"{_lesson_base(accepted, remaining)}/access-grants/"
        f"{grants[remaining_index]['access_grant_id']}",
        headers=_keyed(accepted.teacher, 2, f"revoke-page-two-{uuid4()}"),
    )
    assert revoked.status_code == 200, revoked.text
    second = accepted.client.get(
        path,
        params={"q": marker, "limit": 1, "cursor": first.json()["next_cursor"]},
        headers=_headers(accepted.teacher),
    )
    assert second.status_code == 200, second.text
    assert all(item["lesson_id"] != remaining["lesson_id"] for item in second.json()["items"])


def test_version_routes_hide_other_authors_private_lessons_and_other_callers(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    private_lesson = _create_lesson(accepted, visibility="PRIVATE")
    base = _lesson_base(accepted, private_lesson) + "/versions"
    version_id = private_lesson["current_version"]["version_id"]
    second_teacher = _add_second_teacher(accepted)

    missing_list = accepted.client.get(
        _lesson_base(accepted, {"lesson_id": "missing-lesson"}) + "/versions",
        headers=_headers(second_teacher),
    )
    hidden_list = accepted.client.get(base, headers=_headers(second_teacher))
    hidden_get = accepted.client.get(f"{base}/{version_id}", headers=_headers(second_teacher))
    missing_get = accepted.client.get(
        _lesson_base(accepted, {"lesson_id": "missing-lesson"}) + f"/versions/{version_id}",
        headers=_headers(second_teacher),
    )
    assert hidden_list.status_code == hidden_get.status_code == 404
    for hidden, missing in ((hidden_list, missing_list), (hidden_get, missing_get)):
        assert hidden.status_code == missing.status_code == 404
        assert hidden.json()["code"] == missing.json()["code"] == "RESOURCE_NOT_FOUND"
        assert hidden.json()["message"] == missing.json()["message"]

    search_path = f"/api/lesson-library/v1/organizations/{accepted.organization_id}/public-lessons"
    paths = (base, f"{base}/{version_id}", search_path)
    with _second_tenant(accepted) as other:
        for caller in (accepted.parent, accepted.manager, other["teacher"], other["parent"]):
            for path in paths:
                refused = accepted.client.get(path, headers=_headers(caller))
                assert refused.status_code in (403, 404), (caller, path, refused.text)
                assert "items" not in refused.json()
                assert "content" not in refused.json()


def test_versions_cursor_replay_against_other_lesson_is_400(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    lesson = _create_lesson(accepted)
    other_lesson = _create_lesson(accepted, title="Synthetic cursor replay target")
    revision = 1
    for version_no in range(2, 4):
        _, revision = _revise_lesson(
            accepted,
            lesson_id=str(lesson["lesson_id"]),
            expected_revision=revision,
            title=f"Synthetic cursor version {version_no}",
        )
    first = accepted.client.get(
        _lesson_base(accepted, lesson) + "/versions",
        params={"limit": 1},
        headers=_headers(accepted.teacher),
    )
    assert first.status_code == 200, first.text
    cursor = first.json()["next_cursor"]
    assert cursor
    replay = accepted.client.get(
        _lesson_base(accepted, other_lesson) + "/versions",
        params={"limit": 1, "cursor": cursor},
        headers=_headers(accepted.teacher),
    )
    assert replay.status_code == 400
    assert replay.json()["code"] == "INVALID_REQUEST"
    with _second_tenant(accepted) as other:
        foreign = _create_lesson_in_org(
            accepted,
            organization_id=other["organization"],
            teacher=other["teacher"],
            title="Synthetic foreign cursor target",
        )
        foreign_replay = accepted.client.get(
            f"/api/lesson-library/v1/organizations/{other['organization']}/lessons/"
            f"{foreign['lesson_id']}/versions",
            params={"limit": 1, "cursor": cursor},
            headers=_headers(other["teacher"]),
        )
        assert foreign_replay.status_code == 400
        assert foreign_replay.json()["code"] == "INVALID_REQUEST"


def test_search_cursor_replay_by_another_teacher_is_400(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    marker = f"T10aCursorActor{uuid4().hex}"
    for index in range(2):
        lesson = _create_lesson(accepted, title=f"{marker} {index}")
        _approve_public_grant(accepted, _create_public_grant(accepted, lesson, capability="VIEW"))
    path = f"/api/lesson-library/v1/organizations/{accepted.organization_id}/public-lessons"
    first = accepted.client.get(
        path, params={"q": marker, "limit": 1}, headers=_headers(accepted.teacher)
    )
    assert first.status_code == 200, first.text
    cursor = first.json()["next_cursor"]
    assert cursor
    second_teacher = _add_second_teacher(accepted)
    replay = accepted.client.get(
        path,
        params={"q": marker, "limit": 1, "cursor": cursor},
        headers=_headers(second_teacher),
    )
    assert replay.status_code == 400
    assert replay.json()["code"] == "INVALID_REQUEST"


def test_search_rejects_control_characters_with_400(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    path = f"/api/lesson-library/v1/organizations/{accepted.organization_id}/public-lessons"
    for params in ({"q": "a\x00b"}, {"topic": "a\x00b"}, {"q": "a\x1fb"}):
        response = accepted.client.get(path, params=params, headers=_headers(accepted.teacher))
        assert response.status_code == 400, response.text
        assert response.json()["code"] == "INVALID_REQUEST"
    parent_response = accepted.client.get(
        "/api/lesson-library/v1/me/lessons",
        params={"source": "PUBLIC", "q": "a\x00b"},
        headers=_headers(accepted.parent),
    )
    assert parent_response.status_code == 400, parent_response.text
