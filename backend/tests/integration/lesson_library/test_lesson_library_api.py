"""PostgreSQL-backed HTTP acceptance checks for non-AI Lesson Library workflows."""

from __future__ import annotations

import hashlib
import os
from collections.abc import Iterator
from dataclasses import dataclass
from io import BytesIO
from uuid import uuid4

import pytest
from fastapi import FastAPI, Header
from fastapi.testclient import TestClient

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.object_storage import StoredObject
from sketch2life.application.services.storage_example import StorageExampleService
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.documents.clamav_scanner import ClamAvScanner
from sketch2life.infrastructure.documents.lesson_parser import DeterministicLessonDocumentParser
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult
from sketch2life.interfaces.http.routers.storage_examples import get_storage_example_service


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
        for subject in (teacher, manager, parent, platform_admin):
            db.add(
                AdultIdentityModel(
                    subject=subject,
                    issuer="synthetic-lesson-test-issuer",
                    state="active",
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

    app.dependency_overrides.clear()
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
        headers=_headers(accepted.teacher, **{"If-Match": '"1"'}),
    )
    assert updated.status_code == 200, updated.text
    assert updated.headers["ETag"] == '"2"'
    assert updated.json()["current_version"]["version_no"] == 2

    stale = client.patch(
        lesson_url,
        json={"contract": "UpdateLessonRequestV1", "content": _content("Bản ghi cũ")},
        headers=_headers(accepted.teacher, **{"If-Match": '"1"'}),
    )
    assert stale.status_code == 409
    assert "STALE_REVISION" in stale.text

    forbidden = client.get(
        f"/api/lesson-library/v1/organizations/{accepted.organization_id}/lessons",
        headers=_headers(accepted.parent),
    )
    assert forbidden.status_code == 403

    archived = client.delete(lesson_url, headers=_headers(accepted.teacher, **{"If-Match": '"2"'}))
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
    assert incomplete.status_code == 409
    assert "UPLOAD_INCOMPLETE" in incomplete.text

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
    assert completed.status_code == 200, completed.text
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
        headers=_headers(accepted.teacher, **{"If-Match": '"1"'}),
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
    aborted = client.delete(
        f"/api/lesson-library/v1/upload-sessions/{aborted_session.json()['upload_session_id']}",
        headers=_headers(accepted.teacher),
    )
    assert aborted.status_code == 200, aborted.text
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
            headers=_headers(accepted.teacher, **{"If-Match": '"2"'}),
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
        headers=_headers(accepted.teacher, **{"If-Match": '"2"'}),
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
        headers=_headers(accepted.teacher, **{"If-Match": '"2"'}),
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
        headers=_headers(accepted.manager, **{"If-Match": '"2"'}),
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
