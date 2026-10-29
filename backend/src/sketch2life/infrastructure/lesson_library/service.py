"""Persistence-backed Lesson Library use-case adapter for the v1 HTTP surface."""

from __future__ import annotations

import base64
import hashlib
import json
import math
import re
from datetime import UTC, datetime, timedelta
from io import BytesIO
from tempfile import SpooledTemporaryFile
from typing import Any, Callable
from uuid import NAMESPACE_URL, uuid4, uuid5

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from sketch2life.application.ports.lesson_documents import (
    LessonDocumentParser,
    LessonDocumentRejected,
    MalwareDetected,
    MalwareScanner,
    MalwareScannerUnavailable,
)
from sketch2life.application.ports.object_storage import ObjectStorageFailure, ObjectStoragePort
from sketch2life.contracts.schemas.lesson_library import LessonContentInputV1
from sketch2life.domain.lesson_library.model import (
    LessonLibraryRuleError,
    can_read_as_parent,
    canonical_content_hash,
    next_version_number,
    validate_content,
)
from sketch2life.infrastructure.lesson_library.tables import (
    ACCESS_GRANTS,
    COMMAND_RECEIPTS,
    DOCUMENT_REVISIONS,
    LIBRARY_ITEMS,
    LIBRARY_VERSIONS,
    PARENT_GROUP_MEMBERS,
    PARENT_GROUPS,
    SOURCE_DOCUMENTS,
    UPLOAD_PARTS,
    UPLOAD_SESSIONS,
    VERSION_ACTIVITIES,
)
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    OrganizationAssignmentModel,
)
from sketch2life.infrastructure.persistence.core_models import (
    CoreAggregateRevisionModel,
    CoreAssetMetadataModel,
    CoreAuditEntryModel,
    CoreOutboxEventModel,
)

PART_SIZE_BYTES = 4 * 1024 * 1024
MAX_SOURCE_BYTES = 25_000_000
UPLOAD_TTL = timedelta(hours=24)
INVITATION_TTL = timedelta(days=30)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_UPLOADS = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}


class LessonLibraryError(RuntimeError):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(code)


def fail(status_code: int, code: str, message: str) -> None:
    raise LessonLibraryError(status_code, code, message)


class LessonLibraryService:
    """Durable, non-AI lesson library service.

    Framework-free domain validation is delegated to ``domain.lesson_library``. This
    adapter coordinates the SQLAlchemy unit of work and the replaceable object store.
    """

    def __init__(
        self,
        db: Session,
        *,
        storage: ObjectStoragePort,
        parser: LessonDocumentParser,
        scanner: MalwareScanner,
    ) -> None:
        self.db = db
        self.storage = storage
        self.parser = parser
        self.scanner = scanner

    def create_lesson(
        self, *, organization_id: str, actor: str, content: LessonContentInputV1,
        visibility: str, idempotency_key: str,
    ) -> dict[str, Any]:
        content_data = content.model_dump(mode="json")
        self._validate_content(content_data)

        def execute() -> dict[str, Any]:
            now = datetime.now(UTC)
            lesson_id = str(uuid4())
            version_id = str(uuid4())
            self.db.execute(
                LIBRARY_ITEMS.insert().values(
                    lesson_id=lesson_id,
                    organization_id=organization_id,
                    owner_kind="ORGANIZATION",
                    created_by=actor,
                    state="ACTIVE",
                    visibility=visibility,
                    internal_visibility=visibility,
                    moderation_state="VISIBLE",
                    current_version_id=version_id,
                    revision=1,
                    created_at=now,
                    updated_at=now,
                )
            )
            self._insert_version(
                lesson_id=lesson_id,
                version_id=version_id,
                version_no=1,
                content=content_data,
                actor=actor,
                source_revision_id=None,
                review_state="DRAFT",
                created_at=now,
            )
            self._audit(
                organization_id, actor, "lesson.create", "lesson", lesson_id
            )
            return self._detail(lesson_id, organization_id)

        return self._idempotent(
            organization_id=organization_id,
            actor=actor,
            scope="POST /organizations/{organization_id}/lessons",
            key=idempotency_key,
            payload={"content": content_data, "visibility": visibility},
            execute=execute,
        )

    def list_lessons(
        self, *, organization_id: str, actor: str, manager: bool, state: str | None,
        visibility: str | None, limit: int, cursor: str | None,
    ) -> dict[str, Any]:
        stmt = select(
            LIBRARY_ITEMS.c.lesson_id.label("lesson_id"),
            LIBRARY_ITEMS.c.visibility.label("visibility"),
            LIBRARY_ITEMS.c.updated_at.label("updated_at"),
            LIBRARY_VERSIONS.c.version_id.label("version_id"),
            LIBRARY_VERSIONS.c.version_no.label("version_no"),
            LIBRARY_VERSIONS.c.content_json.label("content_json"),
            LIBRARY_VERSIONS.c.review_state.label("review_state"),
        ).select_from(
            LIBRARY_ITEMS.join(
                LIBRARY_VERSIONS,
                LIBRARY_VERSIONS.c.version_id == LIBRARY_ITEMS.c.current_version_id,
            )
        ).where(LIBRARY_ITEMS.c.organization_id == organization_id)
        if not manager:
            stmt = stmt.where(
                or_(
                    LIBRARY_ITEMS.c.created_by == actor,
                    LIBRARY_ITEMS.c.visibility.in_(("SCHOOL", "PUBLIC")),
                )
            )
        if state is not None:
            stmt = stmt.where(LIBRARY_ITEMS.c.state == state)
        if visibility is not None:
            stmt = stmt.where(LIBRARY_ITEMS.c.visibility == visibility)
        stmt = self._cursor_filter(stmt, cursor, LIBRARY_ITEMS.c.updated_at, LIBRARY_ITEMS.c.lesson_id)
        rows = self.db.execute(
            stmt.order_by(LIBRARY_ITEMS.c.updated_at.desc(), LIBRARY_ITEMS.c.lesson_id.desc())
            .limit(limit + 1)
        ).mappings().all()
        next_cursor = None
        if len(rows) > limit:
            rows = rows[:limit]
            next_cursor = self._encode_cursor(rows[-1]["updated_at"], rows[-1]["lesson_id"])
        items = [self._summary(row) for row in rows]
        return {"contract": "LessonPageV1", "items": items, "next_cursor": next_cursor}

    def get_lesson(
        self, *, organization_id: str, lesson_id: str, actor: str, manager: bool,
    ) -> dict[str, Any]:
        item = self._load_lesson(organization_id, lesson_id)
        if not manager and item["created_by"] != actor and item["visibility"] == "PRIVATE":
            fail(404, "LESSON_NOT_FOUND", "Lesson was not found")
        return self._detail_from_row(item)

    def update_lesson(
        self, *, organization_id: str, lesson_id: str, actor: str,
        expected_revision: int, content: LessonContentInputV1,
    ) -> dict[str, Any]:
        content_data = content.model_dump(mode="json")
        self._validate_content(content_data)
        item = self._load_lesson(organization_id, lesson_id, for_update=True)
        self._require_revision(item["revision"], expected_revision)
        if item["created_by"] != actor:
            fail(404, "LESSON_NOT_FOUND", "Lesson was not found")
        if item["state"] != "ACTIVE":
            fail(409, "INVALID_TRANSITION", "Archived lessons cannot be edited")
        version_no = self._next_version(item["lesson_id"])
        version_id = str(uuid4())
        now = datetime.now(UTC)
        self._insert_version(
            lesson_id=lesson_id,
            version_id=version_id,
            version_no=version_no,
            content=content_data,
            actor=actor,
            source_revision_id=None,
            review_state="DRAFT",
            created_at=now,
        )
        new_revision = expected_revision + 1
        self.db.execute(
            LIBRARY_ITEMS.update().where(LIBRARY_ITEMS.c.lesson_id == lesson_id).values(
                current_version_id=version_id,
                revision=new_revision,
                updated_at=now,
            )
        )
        self._audit(organization_id, actor, "lesson.version.create", "lesson", lesson_id)
        self._commit()
        return self._detail(lesson_id, organization_id)

    def archive_lesson(
        self, *, organization_id: str, lesson_id: str, actor: str,
        manager: bool, expected_revision: int,
    ) -> dict[str, Any]:
        item = self._load_lesson(organization_id, lesson_id, for_update=True)
        self._require_revision(item["revision"], expected_revision)
        if not manager and item["created_by"] != actor:
            fail(404, "LESSON_NOT_FOUND", "Lesson was not found")
        if item["state"] == "ARCHIVED":
            self._commit()
            return self._detail(lesson_id, organization_id)
        now = datetime.now(UTC)
        self.db.execute(
            LIBRARY_ITEMS.update().where(LIBRARY_ITEMS.c.lesson_id == lesson_id).values(
                state="ARCHIVED", archived_at=now, updated_at=now, revision=expected_revision + 1
            )
        )
        self.db.execute(
            ACCESS_GRANTS.update()
            .where(
                ACCESS_GRANTS.c.lesson_id == lesson_id,
                ACCESS_GRANTS.c.state.in_(("ACTIVE", "INVITED", "PENDING_REVIEW")),
            )
            .values(state="REVOKED", revoked_at=now, revision=ACCESS_GRANTS.c.revision + 1)
        )
        self._audit(organization_id, actor, "lesson.archive", "lesson", lesson_id)
        self._commit()
        return self._detail(lesson_id, organization_id)

    def create_lesson_version(
        self, *, organization_id: str, lesson_id: str, actor: str,
        expected_revision: int, source_revision_id: str, content: LessonContentInputV1,
    ) -> dict[str, Any]:
        content_data = content.model_dump(mode="json")
        self._validate_content(content_data)
        item = self._load_lesson(organization_id, lesson_id, for_update=True)
        self._require_revision(item["revision"], expected_revision)
        if item["created_by"] != actor:
            fail(404, "LESSON_NOT_FOUND", "Lesson was not found")
        # The route takes a document revision ID, so resolve and verify its source.
        revision = self.db.execute(
            select(DOCUMENT_REVISIONS).where(
                DOCUMENT_REVISIONS.c.revision_id == source_revision_id
            )
        ).mappings().one_or_none()
        if revision is None:
            fail(404, "RESOURCE_NOT_FOUND", "Document revision was not found")
        source = self.db.execute(
            select(SOURCE_DOCUMENTS).where(
                SOURCE_DOCUMENTS.c.source_document_id == revision["source_document_id"],
                SOURCE_DOCUMENTS.c.lesson_id == lesson_id,
                SOURCE_DOCUMENTS.c.organization_id == organization_id,
                SOURCE_DOCUMENTS.c.uploaded_by == actor,
                SOURCE_DOCUMENTS.c.state == "READY_FOR_REVIEW",
            )
        ).mappings().one_or_none()
        if source is None:
            fail(404, "RESOURCE_NOT_FOUND", "Document revision was not found")
        version_no = self._next_version(lesson_id)
        version_id = str(uuid4())
        now = datetime.now(UTC)
        self._insert_version(
            lesson_id=lesson_id,
            version_id=version_id,
            version_no=version_no,
            content=content_data,
            actor=actor,
            source_revision_id=source_revision_id,
            review_state="DRAFT",
            created_at=now,
        )
        self.db.execute(
            LIBRARY_ITEMS.update().where(LIBRARY_ITEMS.c.lesson_id == lesson_id).values(
                current_version_id=version_id,
                revision=expected_revision + 1,
                updated_at=now,
            )
        )
        self.db.execute(
            DOCUMENT_REVISIONS.update()
            .where(DOCUMENT_REVISIONS.c.revision_id == source_revision_id)
            .values(review_state="CONFIRMED")
        )
        self._audit(organization_id, actor, "lesson.version.from_document", "lesson", lesson_id)
        self._commit()
        row = self._load_version(version_id)
        return self._version_response(row, with_content=True)

    def _validate_content(self, content: dict[str, Any]) -> None:
        try:
            validate_content(content)
        except LessonLibraryRuleError as exc:
            fail(422, "INVALID_REQUEST", "Lesson content does not satisfy the v1 contract")

    def _insert_version(
        self, *, lesson_id: str, version_id: str, version_no: int,
        content: dict[str, Any], actor: str, source_revision_id: str | None,
        review_state: str, created_at: datetime,
    ) -> None:
        self.db.execute(
            LIBRARY_VERSIONS.insert().values(
                version_id=version_id,
                lesson_id=lesson_id,
                version_no=version_no,
                content_json={key: value for key, value in content.items() if key != "activities"},
                structured_content_hash=canonical_content_hash(content),
                review_state=review_state,
                source_document_revision_id=source_revision_id,
                authored_by=actor,
                created_at=created_at,
            )
        )
        for index, activity in enumerate(content["activities"], start=1):
            self.db.execute(
                VERSION_ACTIVITIES.insert().values(
                    activity_id=str(uuid4()),
                    version_id=version_id,
                    activity_order=index,
                    activity_json=activity,
                )
            )

    def _next_version(self, lesson_id: str) -> int:
        current = self.db.scalar(
            select(func.max(LIBRARY_VERSIONS.c.version_no)).where(
                LIBRARY_VERSIONS.c.lesson_id == lesson_id
            )
        )
        return next_version_number(int(current or 0))

    def _load_lesson(
        self, organization_id: str, lesson_id: str, *, for_update: bool = False,
    ) -> Any:
        stmt = select(LIBRARY_ITEMS).where(
            LIBRARY_ITEMS.c.organization_id == organization_id,
            LIBRARY_ITEMS.c.lesson_id == lesson_id,
        )
        if for_update:
            stmt = stmt.with_for_update()
        row = self.db.execute(stmt).mappings().one_or_none()
        if row is None:
            fail(404, "LESSON_NOT_FOUND", "Lesson was not found")
        return row

    def _load_version(self, version_id: str) -> Any:
        row = self.db.execute(
            select(LIBRARY_VERSIONS).where(LIBRARY_VERSIONS.c.version_id == version_id)
        ).mappings().one_or_none()
        if row is None:
            fail(404, "RESOURCE_NOT_FOUND", "Lesson version was not found")
        return row

    def _full_content(self, version: Any) -> dict[str, Any]:
        content = dict(version["content_json"])
        content["activities"] = [
            dict(row["activity_json"])
            for row in self.db.execute(
                select(VERSION_ACTIVITIES.c.activity_json)
                .where(VERSION_ACTIVITIES.c.version_id == version["version_id"])
                .order_by(VERSION_ACTIVITIES.c.activity_order)
            ).mappings()
        ]
        return content

    def _version_response(self, version: Any, *, with_content: bool) -> dict[str, Any]:
        result = {
            "contract": "LessonVersionV1",
            "lesson_id": version["lesson_id"],
            "version_id": version["version_id"],
            "version_no": version["version_no"],
            "review_state": version["review_state"],
            "structured_content_hash": version["structured_content_hash"],
            "source_document_revision_id": version["source_document_revision_id"],
            "authored_principal_ref": version["authored_by"],
            "created_at": version["created_at"],
        }
        if with_content:
            result["content"] = self._full_content(version)
        return result

    def _detail(self, lesson_id: str, organization_id: str) -> dict[str, Any]:
        item = self._load_lesson(organization_id, lesson_id)
        return self._detail_from_row(item)

    def _detail_from_row(self, item: Any) -> dict[str, Any]:
        version = self._load_version(item["current_version_id"])
        return {
            "contract": "LessonDetailV1",
            "lesson_id": item["lesson_id"],
            "organization_id": item["organization_id"],
            "owner_kind": "ORGANIZATION",
            "created_by": item["created_by"],
            "state": item["state"],
            "visibility": item["visibility"],
            "moderation_state": item["moderation_state"],
            "current_version": self._version_response(version, with_content=True),
            "revision": item["revision"],
            "created_at": item["created_at"],
            "updated_at": item["updated_at"],
        }

    def _summary(self, row: Any) -> dict[str, Any]:
        activity_count = self.db.scalar(
            select(func.count()).select_from(VERSION_ACTIVITIES).where(
                VERSION_ACTIVITIES.c.version_id == row["version_id"]
            )
        ) or 0
        return {
            "contract": "LessonSummaryV1",
            "lesson_id": row["lesson_id"],
            "title": row["content_json"].get("title", ""),
            "topic": row["content_json"].get("topic", ""),
            "current_version_no": row["version_no"],
            "review_state": row["review_state"],
            "visibility": row["visibility"],
            "activity_count": int(activity_count),
            "updated_at": row["updated_at"],
        }

    def _idempotent(
        self, *, organization_id: str, actor: str, scope: str, key: str,
        payload: dict[str, Any], execute: Callable[[], dict[str, Any]],
    ) -> dict[str, Any]:
        previous = self._replay(
            organization_id=organization_id, actor=actor, scope=scope,
            key=key, payload=payload,
        )
        if previous is not None:
            return previous
        fingerprint = self._fingerprint(payload)
        identity = {
            "organization_id": organization_id,
            "principal_ref": actor,
            "operation_scope": scope,
            "idempotency_key": key,
        }
        response = execute()
        self.db.execute(
            COMMAND_RECEIPTS.insert().values(
                **identity, request_fingerprint=fingerprint, response_json=self._json_safe(response)
            )
        )
        self._commit()
        return response

    def _replay(
        self, *, organization_id: str, actor: str, scope: str,
        key: str, payload: dict[str, Any],
    ) -> dict[str, Any] | None:
        previous = self.db.execute(
            select(COMMAND_RECEIPTS).where(
                COMMAND_RECEIPTS.c.organization_id == organization_id,
                COMMAND_RECEIPTS.c.principal_ref == actor,
                COMMAND_RECEIPTS.c.operation_scope == scope,
                COMMAND_RECEIPTS.c.idempotency_key == key,
            )
        ).mappings().one_or_none()
        if previous is None:
            return None
        if previous["request_fingerprint"] != self._fingerprint(payload):
            fail(409, "IDEMPOTENCY_KEY_REUSED", "Idempotency-Key was already used for another request")
        return dict(previous["response_json"])

    @staticmethod
    def _fingerprint(payload: dict[str, Any]) -> str:
        normalized = LessonLibraryService._json_safe(payload)
        return hashlib.sha256(
            json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

    def _audit(
        self, organization_id: str, actor: str, action: str,
        resource_type: str, resource_id: str,
    ) -> None:
        self.db.add(
            CoreAuditEntryModel(
                audit_id=str(uuid4()),
                organization_id=organization_id,
                actor_ref=actor,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                decision="allowed",
            )
        )

    def _commit(self) -> None:
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            fail(409, "RESOURCE_CONFLICT", "The request conflicts with existing records")
        except SQLAlchemyError:
            self.db.rollback()
            fail(503, "DEPENDENCY_UNAVAILABLE", "Database is temporarily unavailable")

    @staticmethod
    def _require_revision(current: int, expected: int) -> None:
        if current != expected:
            fail(409, "STALE_REVISION", "The resource changed; reload before retrying")

    @staticmethod
    def _cursor_filter(stmt: Any, cursor: str | None, time_col: Any, id_col: Any) -> Any:
        if cursor is None:
            return stmt
        try:
            decoded = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)).decode("utf-8")
            timestamp, row_id = decoded.split("|", 1)
            created_at = datetime.fromisoformat(timestamp)
            if created_at.tzinfo is None or not row_id:
                raise ValueError
        except (ValueError, UnicodeError):
            fail(422, "INVALID_REQUEST", "Pagination cursor is invalid")
        return stmt.where(or_(time_col < created_at, and_(time_col == created_at, id_col < row_id)))

    @staticmethod
    def _encode_cursor(created_at: datetime, row_id: str) -> str:
        value = f"{created_at.isoformat()}|{row_id}".encode("utf-8")
        return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")

    @staticmethod
    def _json_safe(value: Any) -> Any:
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, dict):
            return {key: LessonLibraryService._json_safe(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [LessonLibraryService._json_safe(item) for item in value]
        return value

    def create_upload_session(
        self, *, organization_id: str, lesson_id: str, actor: str,
        file_name: str, media_type: str, byte_length: int, sha256: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        item = self._load_lesson(organization_id, lesson_id)
        if item["created_by"] != actor or item["state"] != "ACTIVE":
            fail(404, "LESSON_NOT_FOUND", "Lesson was not found")
        safe_name = file_name.replace("\\", "/").rsplit("/", 1)[-1]
        safe_name = "".join(char for char in safe_name if ord(char) >= 32 and ord(char) != 127)
        suffix = "." + safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else ""
        expected_media_type = _ALLOWED_UPLOADS.get(suffix)
        if not safe_name or expected_media_type is None or media_type != expected_media_type:
            fail(415, "UNSUPPORTED_MEDIA_TYPE", "Only unencrypted PDF, DOCX and PPTX are accepted")
        if byte_length < 1 or byte_length > MAX_SOURCE_BYTES:
            fail(413, "REQUEST_TOO_LARGE", "Lesson source files are limited to 25 MB")
        if not _SHA256.fullmatch(sha256):
            fail(422, "INVALID_REQUEST", "SHA-256 must be lowercase hexadecimal")
        expected_parts = math.ceil(byte_length / PART_SIZE_BYTES)

        def execute() -> dict[str, Any]:
            upload_session_id = str(uuid4())
            expires_at = datetime.now(UTC) + UPLOAD_TTL
            self.db.execute(
                UPLOAD_SESSIONS.insert().values(
                    upload_session_id=upload_session_id,
                    organization_id=organization_id,
                    owner_principal_ref=actor,
                    purpose="LESSON_SOURCE",
                    target_ref=lesson_id,
                    safe_file_name=safe_name,
                    expected_media_type=expected_media_type,
                    expected_size_bytes=byte_length,
                    expected_sha256=sha256,
                    chunk_size_bytes=PART_SIZE_BYTES,
                    expected_parts=expected_parts,
                    state="OPEN",
                    expires_at=expires_at,
                )
            )
            return {
                "contract": "UploadSessionV1",
                "upload_session_id": upload_session_id,
                "state": "OPEN",
                "part_size_bytes": PART_SIZE_BYTES,
                "expected_parts": expected_parts,
                "accepted_part_numbers": [],
                "expires_at": expires_at,
            }

        return self._idempotent(
            organization_id=organization_id,
            actor=actor,
            scope=f"POST /organizations/{organization_id}/lessons/{lesson_id}/upload-sessions",
            key=idempotency_key,
            payload={
                "file_name": safe_name,
                "media_type": media_type,
                "byte_length": byte_length,
                "sha256": sha256,
            },
            execute=execute,
        )

    def put_upload_part(
        self, *, upload_session_id: str, actor: str, part_number: int,
        body: bytes, part_sha256: str, range_start: int, range_end: int, range_total: int,
    ) -> dict[str, Any]:
        session = self._load_upload_session(upload_session_id, actor, for_update=False)
        self._require_upload_open(session)
        if not 1 <= part_number <= session["expected_parts"]:
            fail(422, "INVALID_REQUEST", "Part number is outside this upload session")
        start = (part_number - 1) * PART_SIZE_BYTES
        expected_length = min(PART_SIZE_BYTES, session["expected_size_bytes"] - start)
        if (
            range_start != start
            or range_end != start + expected_length - 1
            or range_total != session["expected_size_bytes"]
            or len(body) != expected_length
            or expected_length < 1
        ):
            fail(422, "INVALID_REQUEST", "Content-Range does not match the expected upload part")
        actual_hash = hashlib.sha256(body).hexdigest()
        if not _SHA256.fullmatch(part_sha256) or actual_hash != part_sha256:
            fail(422, "INVALID_SOURCE_DOCUMENT", "Part checksum does not match uploaded bytes")
        prior = self.db.execute(
            select(UPLOAD_PARTS).where(
                UPLOAD_PARTS.c.upload_session_id == upload_session_id,
                UPLOAD_PARTS.c.part_number == part_number,
            )
        ).mappings().one_or_none()
        if prior is not None:
            if prior["sha256"] != actual_hash or prior["byte_size"] != len(body):
                fail(409, "PART_CONFLICT", "This part number already has different bytes")
            return {
                "contract": "UploadPartReceiptV1",
                "part_number": part_number,
                "byte_length": len(body),
                "sha256": actual_hash,
                "accepted": True,
            }
        object_key = f"lesson-library/quarantine/{upload_session_id}/parts/{part_number}/{actual_hash}"
        try:
            self.storage.put_object(
                object_key,
                BytesIO(body),
                content_type="application/octet-stream",
                content_length=len(body),
                metadata={"sha256": actual_hash, "upload-session": upload_session_id},
            )
        except ObjectStorageFailure:
            fail(503, "DEPENDENCY_UNAVAILABLE", "Private storage is temporarily unavailable")
        self.db.execute(
            UPLOAD_PARTS.insert().values(
                upload_session_id=upload_session_id,
                part_number=part_number,
                byte_size=len(body),
                sha256=actual_hash,
                storage_object_ref=object_key,
            )
        )
        self._commit()
        return {
            "contract": "UploadPartReceiptV1",
            "part_number": part_number,
            "byte_length": len(body),
            "sha256": actual_hash,
            "accepted": True,
        }

    def complete_upload(
        self, *, upload_session_id: str, actor: str, idempotency_key: str,
    ) -> dict[str, Any]:
        session = self._load_upload_session(upload_session_id, actor, for_update=True)
        organization_id = session["organization_id"]
        existing_source = self.db.execute(
            select(SOURCE_DOCUMENTS).where(
                SOURCE_DOCUMENTS.c.upload_session_id == upload_session_id
            )
        ).mappings().one_or_none()
        if session["state"] == "COMPLETED" and existing_source is not None:
            return self._source_status(existing_source)

        def execute() -> dict[str, Any]:
            current = self._load_upload_session(upload_session_id, actor, for_update=True)
            self._require_upload_open(current)
            parts = self.db.execute(
                select(UPLOAD_PARTS)
                .where(UPLOAD_PARTS.c.upload_session_id == upload_session_id)
                .order_by(UPLOAD_PARTS.c.part_number)
            ).mappings().all()
            if len(parts) != current["expected_parts"] or [p["part_number"] for p in parts] != list(
                range(1, current["expected_parts"] + 1)
            ):
                fail(409, "UPLOAD_INCOMPLETE", "Upload parts are incomplete")

            full_hash = hashlib.sha256()
            total_bytes = 0
            assembled = SpooledTemporaryFile(max_size=5 * 1024 * 1024, mode="w+b")
            try:
                for part in parts:
                    try:
                        stored = self.storage.get_object(part["storage_object_ref"])
                    except ObjectStorageFailure:
                        fail(503, "DEPENDENCY_UNAVAILABLE", "Private storage is temporarily unavailable")
                    if stored is None:
                        fail(503, "DEPENDENCY_UNAVAILABLE", "An uploaded part is unavailable")
                    try:
                        part_hash = hashlib.sha256()
                        part_size = 0
                        while chunk := stored.body.read(64 * 1024):
                            part_hash.update(chunk)
                            full_hash.update(chunk)
                            assembled.write(chunk)
                            part_size += len(chunk)
                            total_bytes += len(chunk)
                            if total_bytes > MAX_SOURCE_BYTES:
                                fail(413, "REQUEST_TOO_LARGE", "Lesson source files are limited to 25 MB")
                        if part_size != part["byte_size"] or part_hash.hexdigest() != part["sha256"]:
                            fail(422, "INVALID_SOURCE_DOCUMENT", "Stored upload part failed checksum validation")
                    finally:
                        stored.body.close()
                if total_bytes != current["expected_size_bytes"] or full_hash.hexdigest() != current["expected_sha256"]:
                    fail(422, "INVALID_SOURCE_DOCUMENT", "Source file checksum does not match the upload request")
                assembled.seek(0)
                try:
                    scan = self.scanner.scan(assembled)
                except MalwareDetected:
                    current_values = {"state": "FAILED"}
                    self.db.execute(
                        UPLOAD_SESSIONS.update()
                        .where(UPLOAD_SESSIONS.c.upload_session_id == upload_session_id)
                        .values(**current_values)
                    )
                    self._commit()
                    fail(422, "MALWARE_DETECTED", "The uploaded source document was rejected by security scanning")
                except MalwareScannerUnavailable:
                    fail(503, "DEPENDENCY_UNAVAILABLE", "Security scanning is temporarily unavailable")
                assembled.seek(0)
                try:
                    extraction = self.parser.extract(
                        assembled,
                        file_extension="." + current["safe_file_name"].rsplit(".", 1)[-1].lower(),
                    )
                except LessonDocumentRejected as exc:
                    current_values = {"state": "FAILED"}
                    self.db.execute(
                        UPLOAD_SESSIONS.update()
                        .where(UPLOAD_SESSIONS.c.upload_session_id == upload_session_id)
                        .values(**current_values)
                    )
                    self._commit()
                    status_code = 415 if exc.code in {
                        "UNSUPPORTED_MEDIA_TYPE", "ENCRYPTED_DOCUMENT_UNSUPPORTED", "OCR_NOT_SUPPORTED"
                    } else 422
                    fail(status_code, exc.code, "The uploaded document could not be safely extracted")

                if extraction.detected_media_type != current["expected_media_type"]:
                    fail(415, "UNSUPPORTED_MEDIA_TYPE", "File signature does not match the declared media type")
                source_document_id = str(uuid5(NAMESPACE_URL, f"sketch2life:lesson-source:{upload_session_id}"))
                asset_ref = f"lesson-source:{upload_session_id}"
                object_key = self._source_object_key(organization_id, source_document_id)
                assembled.seek(0)
                try:
                    self.storage.put_object(
                        object_key,
                        assembled,
                        content_type=extraction.detected_media_type,
                        content_length=total_bytes,
                        metadata={
                            "sha256": current["expected_sha256"],
                            "source-document": source_document_id,
                            "scan-verdict": scan.verdict,
                        },
                    )
                except ObjectStorageFailure:
                    fail(503, "DEPENDENCY_UNAVAILABLE", "Private storage is temporarily unavailable")

                revision_id = str(uuid4())
                scanned_at = datetime.now(UTC)
                self.db.add(
                    CoreAssetMetadataModel(
                        asset_ref=asset_ref,
                        asset_version=1,
                        organization_id=organization_id,
                        content_sha256=current["expected_sha256"],
                        media_type=extraction.detected_media_type,
                        source_refs=[current["target_ref"]],
                        derived_from_ref=None,
                    )
                )
                self.db.execute(
                    SOURCE_DOCUMENTS.insert().values(
                        source_document_id=source_document_id,
                        lesson_id=current["target_ref"],
                        organization_id=organization_id,
                        uploaded_by=actor,
                        upload_session_id=upload_session_id,
                        asset_ref=asset_ref,
                        asset_version=1,
                        safe_file_name=current["safe_file_name"],
                        file_extension="." + current["safe_file_name"].rsplit(".", 1)[-1].lower(),
                        declared_media_type=current["expected_media_type"],
                        detected_media_type=extraction.detected_media_type,
                        byte_length=total_bytes,
                        asset_sha256=current["expected_sha256"],
                        state="READY_FOR_REVIEW",
                        page_or_slide_count=extraction.page_or_slide_count,
                        page_coverage=list(extraction.page_coverage),
                        warnings=list(extraction.warnings),
                        parser_name=extraction.parser_name,
                        parser_version=extraction.parser_version,
                        scanner_name=scan.scanner_name,
                        scanner_version=scan.scanner_version,
                        scan_verdict=scan.verdict,
                        scanned_at=scanned_at,
                        current_revision_id=revision_id,
                    )
                )
                self.db.execute(
                    DOCUMENT_REVISIONS.insert().values(
                        revision_id=revision_id,
                        source_document_id=source_document_id,
                        revision_no=1,
                        source_sha256=current["expected_sha256"],
                        extracted_fields=extraction.extracted_fields,
                        warnings=list(extraction.warnings),
                        page_coverage=list(extraction.page_coverage),
                        parser_name=extraction.parser_name,
                        parser_version=extraction.parser_version,
                        review_state="NEEDS_REVIEW",
                        created_by=actor,
                    )
                )
                self.db.execute(
                    UPLOAD_SESSIONS.update()
                    .where(UPLOAD_SESSIONS.c.upload_session_id == upload_session_id)
                    .values(
                        state="COMPLETED",
                        final_asset_ref=asset_ref,
                        completed_at=scanned_at,
                    )
                )
                self._audit(
                    organization_id, actor, "lesson.source_document.create",
                    "lesson_source_document", source_document_id,
                )
                return self._source_status(
                    self.db.execute(
                        select(SOURCE_DOCUMENTS).where(
                            SOURCE_DOCUMENTS.c.source_document_id == source_document_id
                        )
                    ).mappings().one()
                )
            finally:
                assembled.close()

        response = self._idempotent(
            organization_id=organization_id,
            actor=actor,
            scope=f"POST /upload-sessions/{upload_session_id}/complete",
            key=idempotency_key,
            payload={"upload_session_id": upload_session_id},
            execute=execute,
        )
        self._delete_upload_parts(upload_session_id)
        return response

    def get_source_document(
        self, *, organization_id: str, lesson_id: str, source_document_id: str, actor: str,
    ) -> dict[str, Any]:
        row = self.db.execute(
            select(SOURCE_DOCUMENTS).where(
                SOURCE_DOCUMENTS.c.organization_id == organization_id,
                SOURCE_DOCUMENTS.c.lesson_id == lesson_id,
                SOURCE_DOCUMENTS.c.source_document_id == source_document_id,
                SOURCE_DOCUMENTS.c.uploaded_by == actor,
            )
        ).mappings().one_or_none()
        if row is None:
            fail(404, "RESOURCE_NOT_FOUND", "Source document was not found")
        return self._source_status(row)

    def get_document_revision(
        self, *, organization_id: str, lesson_id: str,
        source_document_id: str, revision_id: str, actor: str,
    ) -> dict[str, Any]:
        source = self.db.execute(
            select(SOURCE_DOCUMENTS).where(
                SOURCE_DOCUMENTS.c.organization_id == organization_id,
                SOURCE_DOCUMENTS.c.lesson_id == lesson_id,
                SOURCE_DOCUMENTS.c.source_document_id == source_document_id,
                SOURCE_DOCUMENTS.c.uploaded_by == actor,
            )
        ).mappings().one_or_none()
        if source is None:
            fail(404, "RESOURCE_NOT_FOUND", "Document revision was not found")
        revision = self.db.execute(
            select(DOCUMENT_REVISIONS).where(
                DOCUMENT_REVISIONS.c.source_document_id == source_document_id,
                DOCUMENT_REVISIONS.c.revision_id == revision_id,
            )
        ).mappings().one_or_none()
        if revision is None:
            fail(404, "RESOURCE_NOT_FOUND", "Document revision was not found")
        return {
            "contract": "LessonDocumentRevisionPreviewV1",
            "revision_id": revision["revision_id"],
            "extracted_fields": revision["extracted_fields"],
            "warnings": revision["warnings"],
            "page_coverage": revision["page_coverage"],
            "review_state": revision["review_state"],
            "parser_version": revision["parser_version"],
        }

    def _load_upload_session(self, upload_session_id: str, actor: str, *, for_update: bool) -> Any:
        stmt = select(UPLOAD_SESSIONS).where(
            UPLOAD_SESSIONS.c.upload_session_id == upload_session_id,
            UPLOAD_SESSIONS.c.owner_principal_ref == actor,
            UPLOAD_SESSIONS.c.purpose == "LESSON_SOURCE",
        )
        if for_update:
            stmt = stmt.with_for_update()
        session = self.db.execute(stmt).mappings().one_or_none()
        if session is None:
            fail(404, "RESOURCE_NOT_FOUND", "Upload session was not found")
        return session

    def _require_upload_open(self, session: Any) -> None:
        if session["state"] == "COMPLETED":
            fail(409, "INVALID_TRANSITION", "Upload session is already complete")
        if session["state"] != "OPEN":
            fail(409, "INVALID_TRANSITION", "Upload session is no longer open")
        if session["expires_at"] <= datetime.now(UTC):
            self.db.execute(
                UPLOAD_SESSIONS.update()
                .where(UPLOAD_SESSIONS.c.upload_session_id == session["upload_session_id"])
                .values(state="EXPIRED")
            )
            self._commit()
            self._delete_upload_parts(session["upload_session_id"])
            fail(409, "UPLOAD_EXPIRED", "Upload session has expired")

    def _source_status(self, row: Any) -> dict[str, Any]:
        return {
            "contract": "LessonSourceDocumentStatusV1",
            "source_document_id": row["source_document_id"],
            "state": row["state"],
            "safe_file_name": row["safe_file_name"],
            "file_extension": row["file_extension"],
            "page_or_slide_count": row["page_or_slide_count"],
            "warnings": row["warnings"],
            "parser_version": row["parser_version"],
            "asset_sha256": row["asset_sha256"],
            "revision_id": row["current_revision_id"],
        }

    def _delete_upload_parts(self, upload_session_id: str) -> None:
        rows = self.db.execute(
            select(UPLOAD_PARTS.c.storage_object_ref).where(
                UPLOAD_PARTS.c.upload_session_id == upload_session_id
            )
        ).scalars().all()
        for object_key in rows:
            try:
                self.storage.delete_object(object_key)
            except ObjectStorageFailure:
                # Quarantine objects remain unreachable without an active session and are
                # eligible for the storage lifecycle sweeper configured outside this API.
                continue

    @staticmethod
    def _source_object_key(organization_id: str, source_document_id: str) -> str:
        return f"lesson-library/private/{organization_id}/{source_document_id}/original"

    def create_access_grant(
        self, *, organization_id: str, lesson_id: str, actor: str,
        version_id: str, audience_kind: str, audience_ref: str | None,
        capability: str, expires_at: datetime | None, idempotency_key: str,
    ) -> dict[str, Any]:
        item = self._load_lesson(organization_id, lesson_id)
        if item["created_by"] != actor or item["state"] != "ACTIVE":
            fail(404, "LESSON_NOT_FOUND", "Lesson was not found")
        version = self.db.execute(
            select(LIBRARY_VERSIONS).where(
                LIBRARY_VERSIONS.c.version_id == version_id,
                LIBRARY_VERSIONS.c.lesson_id == lesson_id,
            )
        ).mappings().one_or_none()
        if version is None:
            fail(404, "RESOURCE_NOT_FOUND", "Lesson version was not found")
        now = datetime.now(UTC)
        if expires_at is not None and expires_at <= now:
            fail(422, "INVALID_REQUEST", "Grant expiry must be in the future")
        if audience_kind == "PUBLIC":
            state = "PENDING_REVIEW"
        else:
            if version["review_state"] != "APPROVED":
                fail(409, "PUBLICATION_REQUIRED", "Only an approved version can be shared privately")
            if audience_kind == "ORGANIZATION" and audience_ref != organization_id:
                fail(404, "RESOURCE_NOT_FOUND", "The audience organization was not found")
            if audience_kind == "PRINCIPAL":
                if audience_ref == actor:
                    fail(422, "INVALID_REQUEST", "A lesson cannot be shared to its author account")
                state = "INVITED"
            elif audience_kind == "PARENT_GROUP":
                group = self._load_group(audience_ref or "", organization_id)
                if group["state"] != "active":
                    fail(409, "INVALID_TRANSITION", "Parent group is not active")
                state = "ACTIVE"
            elif audience_kind == "ORGANIZATION":
                state = "ACTIVE"
            else:
                fail(422, "INVALID_REQUEST", "Audience kind is not supported")
        if audience_kind == "PUBLIC" and audience_ref is not None:
            fail(422, "INVALID_REQUEST", "Public access does not accept an audience reference")

        def execute() -> dict[str, Any]:
            grant_id = str(uuid4())
            self.db.execute(
                ACCESS_GRANTS.insert().values(
                    access_grant_id=grant_id,
                    lesson_id=lesson_id,
                    version_id=version_id,
                    organization_id=organization_id,
                    audience_kind=audience_kind,
                    audience_ref=audience_ref,
                    capability=capability,
                    state=state,
                    granted_by=actor,
                    expires_at=expires_at,
                    revision=1,
                )
            )
            if audience_kind == "PUBLIC":
                self.db.execute(
                    LIBRARY_VERSIONS.update()
                    .where(LIBRARY_VERSIONS.c.version_id == version_id)
                    .values(review_state="PENDING_REVIEW")
                )
            elif state == "ACTIVE":
                self._recalculate_visibility(lesson_id)
            self._audit(organization_id, actor, "lesson.access_grant.create", "lesson_access_grant", grant_id)
            return self._grant_response(
                self.db.execute(
                    select(ACCESS_GRANTS).where(ACCESS_GRANTS.c.access_grant_id == grant_id)
                ).mappings().one()
            )

        return self._idempotent(
            organization_id=organization_id,
            actor=actor,
            scope=f"POST /organizations/{organization_id}/lessons/{lesson_id}/access-grants",
            key=idempotency_key,
            payload={
                "version_id": version_id,
                "audience_kind": audience_kind,
                "audience_ref": audience_ref,
                "capability": capability,
                "expires_at": expires_at,
            },
            execute=execute,
        )

    def list_access_grants(
        self, *, organization_id: str, audience_kind: str | None,
        state: str | None, lesson_id: str | None, limit: int, cursor: str | None,
    ) -> dict[str, Any]:
        stmt = select(ACCESS_GRANTS).where(ACCESS_GRANTS.c.organization_id == organization_id)
        if audience_kind is not None:
            stmt = stmt.where(ACCESS_GRANTS.c.audience_kind == audience_kind)
        if state is not None:
            stmt = stmt.where(ACCESS_GRANTS.c.state == state)
        if lesson_id is not None:
            stmt = stmt.where(ACCESS_GRANTS.c.lesson_id == lesson_id)
        stmt = self._cursor_filter(stmt, cursor, ACCESS_GRANTS.c.created_at, ACCESS_GRANTS.c.access_grant_id)
        rows = self.db.execute(
            stmt.order_by(ACCESS_GRANTS.c.created_at.desc(), ACCESS_GRANTS.c.access_grant_id.desc())
            .limit(limit + 1)
        ).mappings().all()
        next_cursor = None
        if len(rows) > limit:
            rows = rows[:limit]
            next_cursor = self._encode_cursor(rows[-1]["created_at"], rows[-1]["access_grant_id"])
        return {
            "contract": "LessonAccessGrantPageV1",
            "items": [self._grant_response(row) for row in rows],
            "next_cursor": next_cursor,
        }

    def decide_access_grant(
        self, *, organization_id: str, grant_id: str, actor: str,
        expected_revision: int, decision: str, reason: str | None,
        idempotency_key: str,
    ) -> dict[str, Any]:
        fingerprint_payload = {"decision": decision, "reason": reason, "if_match": expected_revision}
        scope = f"POST /organizations/{organization_id}/access-grants/{grant_id}/decision"
        replay = self._replay(
            organization_id=organization_id, actor=actor, scope=scope,
            key=idempotency_key, payload=fingerprint_payload,
        )
        if replay is not None:
            return replay
        grant = self._load_grant(grant_id, organization_id, for_update=True)
        self._require_revision(grant["revision"], expected_revision)
        if grant["audience_kind"] != "PUBLIC" or grant["state"] != "PENDING_REVIEW":
            fail(409, "INVALID_TRANSITION", "Only pending Public grants can be decided")
        item = self._load_lesson(organization_id, grant["lesson_id"])
        if item["created_by"] == actor:
            fail(403, "FORBIDDEN", "A lesson author cannot approve their own Public request")
        def execute() -> dict[str, Any]:
            now = datetime.now(UTC)
            next_state = "ACTIVE" if decision == "APPROVE" else "CHANGES_REQUESTED"
            self.db.execute(
                ACCESS_GRANTS.update()
                .where(ACCESS_GRANTS.c.access_grant_id == grant_id)
                .values(
                    state=next_state,
                    approved_by=actor if decision == "APPROVE" else None,
                    approved_at=now if decision == "APPROVE" else None,
                    decision_reason=reason,
                    revision=expected_revision + 1,
                )
            )
            self.db.execute(
                LIBRARY_VERSIONS.update()
                .where(LIBRARY_VERSIONS.c.version_id == grant["version_id"])
                .values(
                    review_state="APPROVED" if decision == "APPROVE" else "CHANGES_REQUESTED",
                    approved_at=now if decision == "APPROVE" else None,
                )
            )
            self._recalculate_visibility(grant["lesson_id"])
            self._audit(organization_id, actor, f"lesson.public_review.{decision.lower()}", "lesson_access_grant", grant_id)
            return {
                "contract": "LessonAccessGrantDecisionResponseV1",
                "access_grant_id": grant_id,
                "state": next_state,
                "approved_by": actor if decision == "APPROVE" else None,
                "decided_at": now,
                "revision": expected_revision + 1,
            }

        return self._idempotent(
            organization_id=organization_id,
            actor=actor,
            scope=scope,
            key=idempotency_key,
            payload=fingerprint_payload,
            execute=execute,
        )

    def revoke_access_grant(
        self, *, organization_id: str, lesson_id: str, grant_id: str,
        actor: str, manager: bool, expected_revision: int,
    ) -> dict[str, Any]:
        grant = self._load_grant(grant_id, organization_id, for_update=True)
        if grant["lesson_id"] != lesson_id:
            fail(404, "RESOURCE_NOT_FOUND", "Access grant was not found")
        if not manager and grant["granted_by"] != actor:
            fail(404, "RESOURCE_NOT_FOUND", "Access grant was not found")
        self._require_revision(grant["revision"], expected_revision)
        if grant["state"] == "REVOKED":
            return self._grant_response(grant)
        now = datetime.now(UTC)
        self.db.execute(
            ACCESS_GRANTS.update()
            .where(ACCESS_GRANTS.c.access_grant_id == grant_id)
            .values(state="REVOKED", revoked_at=now, revision=expected_revision + 1)
        )
        self._recalculate_visibility(lesson_id)
        self._audit(organization_id, actor, "lesson.access_grant.revoke", "lesson_access_grant", grant_id)
        self._commit()
        return self._grant_response(
            self.db.execute(select(ACCESS_GRANTS).where(ACCESS_GRANTS.c.access_grant_id == grant_id))
            .mappings().one()
        )

    def _load_grant(self, grant_id: str, organization_id: str, *, for_update: bool = False) -> Any:
        stmt = select(ACCESS_GRANTS).where(
            ACCESS_GRANTS.c.access_grant_id == grant_id,
            ACCESS_GRANTS.c.organization_id == organization_id,
        )
        if for_update:
            stmt = stmt.with_for_update()
        row = self.db.execute(stmt).mappings().one_or_none()
        if row is None:
            fail(404, "RESOURCE_NOT_FOUND", "Access grant was not found")
        return row

    def _recalculate_visibility(self, lesson_id: str) -> None:
        """Keep the denormalized lesson visibility aligned with live access grants."""
        now = datetime.now(UTC)
        active_grants = select(ACCESS_GRANTS.c.audience_kind).where(
            ACCESS_GRANTS.c.lesson_id == lesson_id,
            ACCESS_GRANTS.c.state == "ACTIVE",
            or_(ACCESS_GRANTS.c.expires_at.is_(None), ACCESS_GRANTS.c.expires_at > now),
        )
        kinds = set(self.db.execute(active_grants).scalars().all())
        if "PUBLIC" in kinds:
            visibility = "PUBLIC"
        elif kinds.intersection({"PRINCIPAL", "PARENT_GROUP"}):
            visibility = "SELECTED_AUDIENCE"
        elif "ORGANIZATION" in kinds:
            visibility = "SCHOOL"
        else:
            internal_visibility = self.db.scalar(
                select(LIBRARY_ITEMS.c.internal_visibility).where(
                    LIBRARY_ITEMS.c.lesson_id == lesson_id
                )
            )
            if internal_visibility is None:
                return
            visibility = internal_visibility
        self.db.execute(
            LIBRARY_ITEMS.update()
            .where(LIBRARY_ITEMS.c.lesson_id == lesson_id)
            .values(visibility=visibility, updated_at=now)
        )

    @staticmethod
    def _grant_response(row: Any) -> dict[str, Any]:
        return {
            "contract": "LessonAccessGrantV1",
            "access_grant_id": row["access_grant_id"],
            "lesson_id": row["lesson_id"],
            "version_id": row["version_id"],
            "audience_kind": row["audience_kind"],
            "audience_ref": row["audience_ref"],
            "capability": row["capability"],
            "state": row["state"],
            "granted_by": row["granted_by"],
            "approved_by": row["approved_by"],
            "approved_at": row["approved_at"],
            "expires_at": row["expires_at"],
            "revoked_at": row["revoked_at"],
            "revision": row["revision"],
        }

    def create_parent_group(
        self, *, organization_id: str, actor: str, display_name: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        normalized = display_name.strip()
        if not normalized:
            fail(422, "INVALID_REQUEST", "Group name is required")

        def execute() -> dict[str, Any]:
            group_id = str(uuid4())
            now = datetime.now(UTC)
            self.db.execute(
                PARENT_GROUPS.insert().values(
                    parent_group_id=group_id,
                    organization_id=organization_id,
                    display_name=normalized,
                    state="active",
                    created_by=actor,
                    created_at=now,
                )
            )
            self._audit(organization_id, actor, "parent_group.create", "parent_group", group_id)
            return self._group_response(
                self.db.execute(
                    select(PARENT_GROUPS).where(PARENT_GROUPS.c.parent_group_id == group_id)
                ).mappings().one()
            )

        return self._idempotent(
            organization_id=organization_id,
            actor=actor,
            scope=f"POST /organizations/{organization_id}/parent-groups",
            key=idempotency_key,
            payload={"display_name": normalized},
            execute=execute,
        )

    def list_parent_groups(
        self, *, organization_id: str, limit: int, cursor: str | None,
    ) -> dict[str, Any]:
        stmt = select(PARENT_GROUPS).where(PARENT_GROUPS.c.organization_id == organization_id)
        stmt = self._cursor_filter(stmt, cursor, PARENT_GROUPS.c.created_at, PARENT_GROUPS.c.parent_group_id)
        rows = self.db.execute(
            stmt.order_by(PARENT_GROUPS.c.created_at.desc(), PARENT_GROUPS.c.parent_group_id.desc())
            .limit(limit + 1)
        ).mappings().all()
        next_cursor = None
        if len(rows) > limit:
            rows = rows[:limit]
            next_cursor = self._encode_cursor(rows[-1]["created_at"], rows[-1]["parent_group_id"])
        return {
            "contract": "ParentGroupPageV1",
            "items": [self._group_response(row) for row in rows],
            "next_cursor": next_cursor,
        }

    def invite_parent_to_group(
        self, *, organization_id: str, group_id: str, actor: str,
        parent_principal_ref: str, idempotency_key: str,
    ) -> dict[str, Any]:
        group = self._load_group(group_id, organization_id)
        if group["state"] != "active":
            fail(409, "INVALID_TRANSITION", "Parent group is not active")
        if self.db.scalar(
            select(OrganizationAssignmentModel.assignment_id).where(
                OrganizationAssignmentModel.subject == parent_principal_ref,
                OrganizationAssignmentModel.active.is_(True),
            ).limit(1)
        ):
            fail(422, "INVALID_REQUEST", "Staff accounts cannot be used as Parent audience principals")

        def execute() -> dict[str, Any]:
            prior = self.db.execute(
                select(PARENT_GROUP_MEMBERS).where(
                    PARENT_GROUP_MEMBERS.c.parent_group_id == group_id,
                    PARENT_GROUP_MEMBERS.c.parent_principal_ref == parent_principal_ref,
                ).with_for_update()
            ).mappings().one_or_none()
            now = datetime.now(UTC)
            if prior is not None and prior["state"] in {"invited", "active"}:
                fail(409, "INVITATION_EXISTS", "Parent already has an active group invitation or membership")
            if prior is None:
                membership_id = str(uuid4())
                self.db.execute(
                    PARENT_GROUP_MEMBERS.insert().values(
                        membership_id=membership_id,
                        parent_group_id=group_id,
                        parent_principal_ref=parent_principal_ref,
                        state="invited",
                        invited_by=actor,
                        invited_at=now,
                        expires_at=now + INVITATION_TTL,
                        revision=1,
                    )
                )
            else:
                membership_id = prior["membership_id"]
                self.db.execute(
                    PARENT_GROUP_MEMBERS.update()
                    .where(PARENT_GROUP_MEMBERS.c.membership_id == membership_id)
                    .values(
                        state="invited", invited_by=actor, invited_at=now,
                        expires_at=now + INVITATION_TTL, accepted_at=None,
                        revision=prior["revision"] + 1,
                    )
                )
            self._emit_group_invitation(
                organization_id=organization_id,
                group_id=group_id,
                membership_id=membership_id,
                parent_principal_ref=parent_principal_ref,
            )
            self._audit(organization_id, actor, "parent_group.invite", "parent_group_membership", membership_id)
            return {
                "contract": "ParentGroupInvitationV1",
                "membership_id": membership_id,
                "parent_group_id": group_id,
                "state": "INVITED",
                "invited_at": now,
                "expires_at": now + INVITATION_TTL,
                "accepted_at": None,
            }

        return self._idempotent(
            organization_id=organization_id,
            actor=actor,
            scope=f"POST /organizations/{organization_id}/parent-groups/{group_id}/invitations",
            key=idempotency_key,
            payload={"parent_principal_ref": parent_principal_ref},
            execute=execute,
        )

    def _emit_group_invitation(
        self, *, organization_id: str, group_id: str,
        membership_id: str, parent_principal_ref: str,
    ) -> None:
        aggregate = self.db.get(CoreAggregateRevisionModel, group_id)
        if aggregate is None:
            aggregate = CoreAggregateRevisionModel(
                aggregate_id=group_id, organization_id=organization_id, revision=1
            )
            self.db.add(aggregate)
            self.db.flush()
            revision = 1
        else:
            if aggregate.organization_id != organization_id:
                fail(409, "RESOURCE_CONFLICT", "Group event scope is inconsistent")
            aggregate.revision += 1
            revision = aggregate.revision
        self.db.add(
            CoreOutboxEventModel(
                event_id=str(uuid4()),
                event_type="lesson.parent_group_invited.v1",
                organization_id=organization_id,
                aggregate_id=group_id,
                aggregate_revision=revision,
                payload={
                    "membership_id": membership_id,
                    "parent_principal_ref": parent_principal_ref,
                },
                status="pending",
                attempt_count=0,
            )
        )

    def _load_group(self, group_id: str, organization_id: str) -> Any:
        row = self.db.execute(
            select(PARENT_GROUPS).where(
                PARENT_GROUPS.c.parent_group_id == group_id,
                PARENT_GROUPS.c.organization_id == organization_id,
            )
        ).mappings().one_or_none()
        if row is None:
            fail(404, "RESOURCE_NOT_FOUND", "Parent group was not found")
        return row

    @staticmethod
    def _group_response(row: Any) -> dict[str, Any]:
        return {
            "contract": "ParentGroupV1",
            "parent_group_id": row["parent_group_id"],
            "organization_id": row["organization_id"],
            "display_name": row["display_name"],
            "state": row["state"].upper(),
            "created_at": row["created_at"],
        }

    def list_parent_group_invitations(
        self, *, parent_principal_ref: str, limit: int, cursor: str | None,
    ) -> dict[str, Any]:
        now = datetime.now(UTC)
        stmt = select(PARENT_GROUP_MEMBERS).where(
            PARENT_GROUP_MEMBERS.c.parent_principal_ref == parent_principal_ref,
            PARENT_GROUP_MEMBERS.c.state == "invited",
            PARENT_GROUP_MEMBERS.c.expires_at > now,
        )
        stmt = self._cursor_filter(
            stmt, cursor, PARENT_GROUP_MEMBERS.c.invited_at, PARENT_GROUP_MEMBERS.c.membership_id
        )
        rows = self.db.execute(
            stmt.order_by(
                PARENT_GROUP_MEMBERS.c.invited_at.desc(),
                PARENT_GROUP_MEMBERS.c.membership_id.desc(),
            ).limit(limit + 1)
        ).mappings().all()
        next_cursor = None
        if len(rows) > limit:
            rows = rows[:limit]
            next_cursor = self._encode_cursor(rows[-1]["invited_at"], rows[-1]["membership_id"])
        return {
            "contract": "ParentGroupInvitationPageV1",
            "items": [self._membership_response(row) for row in rows],
            "next_cursor": next_cursor,
        }

    def accept_parent_group_invitation(
        self, *, membership_id: str, actor: str, idempotency_key: str,
    ) -> dict[str, Any]:
        membership = self._load_membership(membership_id, for_update=True)
        if membership["parent_principal_ref"] != actor:
            fail(404, "RESOURCE_NOT_FOUND", "Invitation was not found")
        group = self.db.execute(
            select(PARENT_GROUPS).where(PARENT_GROUPS.c.parent_group_id == membership["parent_group_id"])
        ).mappings().one_or_none()
        if group is None:
            fail(404, "RESOURCE_NOT_FOUND", "Invitation was not found")
        org_id = group["organization_id"]

        def execute() -> dict[str, Any]:
            current = self._load_membership(membership_id, for_update=True)
            now = datetime.now(UTC)
            if current["state"] != "invited":
                if current["state"] == "active":
                    return self._membership_response(current)
                fail(409, "INVALID_TRANSITION", "Invitation is no longer active")
            if current["expires_at"] <= now:
                self.db.execute(
                    PARENT_GROUP_MEMBERS.update()
                    .where(PARENT_GROUP_MEMBERS.c.membership_id == membership_id)
                    .values(state="expired", revision=current["revision"] + 1)
                )
                self._commit()
                fail(409, "INVITATION_EXPIRED", "Invitation has expired")
            self.db.execute(
                PARENT_GROUP_MEMBERS.update()
                .where(PARENT_GROUP_MEMBERS.c.membership_id == membership_id)
                .values(state="active", accepted_at=now, revision=current["revision"] + 1)
            )
            self._audit(org_id, actor, "parent_group.invitation.accept", "parent_group_membership", membership_id)
            return {
                "contract": "ParentGroupMembershipV1",
                "membership_id": membership_id,
                "parent_group_id": current["parent_group_id"],
                "state": "ACTIVE",
                "invited_at": current["invited_at"],
                "expires_at": current["expires_at"],
                "accepted_at": now,
            }

        return self._idempotent(
            organization_id=org_id,
            actor=actor,
            scope=f"POST /me/parent-group-invitations/{membership_id}/accept",
            key=idempotency_key,
            payload={"membership_id": membership_id},
            execute=execute,
        )

    def revoke_parent_group_membership(
        self, *, organization_id: str, group_id: str, membership_id: str,
        actor: str, manager: bool, expected_revision: int,
    ) -> dict[str, Any]:
        group = self._load_group(group_id, organization_id)
        membership = self._load_membership(membership_id, for_update=True)
        if membership["parent_group_id"] != group_id:
            fail(404, "RESOURCE_NOT_FOUND", "Group membership was not found")
        if not manager and membership["parent_principal_ref"] != actor:
            fail(404, "RESOURCE_NOT_FOUND", "Group membership was not found")
        self._require_revision(membership["revision"], expected_revision)
        if membership["state"] == "revoked":
            return self._membership_response(membership)
        self.db.execute(
            PARENT_GROUP_MEMBERS.update()
            .where(PARENT_GROUP_MEMBERS.c.membership_id == membership_id)
            .values(state="revoked", revision=expected_revision + 1)
        )
        self._audit(
            organization_id, actor, "parent_group.membership.revoke",
            "parent_group_membership", membership_id,
        )
        self._commit()
        row = self._load_membership(membership_id)
        return self._membership_response(row)

    def _load_membership(self, membership_id: str, *, for_update: bool = False) -> Any:
        stmt = select(PARENT_GROUP_MEMBERS).where(
            PARENT_GROUP_MEMBERS.c.membership_id == membership_id
        )
        if for_update:
            stmt = stmt.with_for_update()
        row = self.db.execute(stmt).mappings().one_or_none()
        if row is None:
            fail(404, "RESOURCE_NOT_FOUND", "Group membership was not found")
        return row

    @staticmethod
    def _membership_response(row: Any) -> dict[str, Any]:
        return {
            "contract": "ParentGroupMembershipV1",
            "membership_id": row["membership_id"],
            "parent_group_id": row["parent_group_id"],
            "state": row["state"].upper(),
            "invited_at": row["invited_at"],
            "expires_at": row["expires_at"],
            "accepted_at": row["accepted_at"],
        }

    def list_lesson_invitations(
        self, *, parent_principal_ref: str, limit: int, cursor: str | None,
    ) -> dict[str, Any]:
        stmt = select(ACCESS_GRANTS).where(
            ACCESS_GRANTS.c.audience_kind == "PRINCIPAL",
            ACCESS_GRANTS.c.audience_ref == parent_principal_ref,
            ACCESS_GRANTS.c.state == "INVITED",
            or_(ACCESS_GRANTS.c.expires_at.is_(None), ACCESS_GRANTS.c.expires_at > datetime.now(UTC)),
        )
        stmt = self._cursor_filter(stmt, cursor, ACCESS_GRANTS.c.created_at, ACCESS_GRANTS.c.access_grant_id)
        rows = self.db.execute(
            stmt.order_by(ACCESS_GRANTS.c.created_at.desc(), ACCESS_GRANTS.c.access_grant_id.desc())
            .limit(limit + 1)
        ).mappings().all()
        next_cursor = None
        if len(rows) > limit:
            rows = rows[:limit]
            next_cursor = self._encode_cursor(rows[-1]["created_at"], rows[-1]["access_grant_id"])
        return {
            "contract": "LessonInvitationPageV1",
            "items": [self._grant_response(row) for row in rows],
            "next_cursor": next_cursor,
        }

    def respond_to_lesson_invitation(
        self, *, access_grant_id: str, actor: str, accept: bool,
        idempotency_key: str,
    ) -> dict[str, Any]:
        grant = self.db.execute(
            select(ACCESS_GRANTS).where(
                ACCESS_GRANTS.c.access_grant_id == access_grant_id,
                ACCESS_GRANTS.c.audience_kind == "PRINCIPAL",
                ACCESS_GRANTS.c.audience_ref == actor,
            ).with_for_update()
        ).mappings().one_or_none()
        if grant is None:
            fail(404, "RESOURCE_NOT_FOUND", "Invitation was not found")
        item = self._load_lesson(grant["organization_id"], grant["lesson_id"])
        action = "accept" if accept else "decline"
        next_state = "ACTIVE" if accept else "DECLINED"

        def execute() -> dict[str, Any]:
            current = self._load_grant(access_grant_id, grant["organization_id"], for_update=True)
            now = datetime.now(UTC)
            if current["state"] != "INVITED":
                if (accept and current["state"] == "ACTIVE") or (not accept and current["state"] == "DECLINED"):
                    return self._grant_response(current)
                fail(409, "INVALID_TRANSITION", "Invitation is no longer active")
            if current["expires_at"] is not None and current["expires_at"] <= now:
                self.db.execute(
                    ACCESS_GRANTS.update()
                    .where(ACCESS_GRANTS.c.access_grant_id == access_grant_id)
                    .values(state="EXPIRED", revision=current["revision"] + 1)
                )
                self._commit()
                fail(409, "INVITATION_EXPIRED", "Invitation has expired")
            if accept and (item["state"] != "ACTIVE" or item["moderation_state"] != "VISIBLE"):
                fail(409, "INVALID_TRANSITION", "The lesson is not currently available")
            self.db.execute(
                ACCESS_GRANTS.update()
                .where(ACCESS_GRANTS.c.access_grant_id == access_grant_id)
                .values(state=next_state, revision=current["revision"] + 1)
            )
            if accept:
                self._recalculate_visibility(current["lesson_id"])
            self._audit(
                current["organization_id"], actor, f"lesson.invitation.{action}",
                "lesson_access_grant", access_grant_id,
            )
            updated = dict(current)
            updated["state"] = next_state
            updated["revision"] = current["revision"] + 1
            return self._grant_response(updated)

        return self._idempotent(
            organization_id=grant["organization_id"],
            actor=actor,
            scope=f"POST /me/lesson-invitations/{access_grant_id}/{action}",
            key=idempotency_key,
            payload={"access_grant_id": access_grant_id, "action": action},
            execute=execute,
        )

    def _parent_access_rows(
        self, *, parent_principal_ref: str, capability: str,
        source_kind: str | None = None, limit: int = 501, cursor: str | None = None,
    ) -> list[dict[str, Any]]:
        now = datetime.now(UTC)
        base_from = ACCESS_GRANTS.join(
            LIBRARY_ITEMS, LIBRARY_ITEMS.c.lesson_id == ACCESS_GRANTS.c.lesson_id
        ).join(LIBRARY_VERSIONS, LIBRARY_VERSIONS.c.version_id == ACCESS_GRANTS.c.version_id)
        selected = (
            ACCESS_GRANTS.c.access_grant_id.label("grant_id"),
            ACCESS_GRANTS.c.audience_kind.label("grant_audience_kind"),
            ACCESS_GRANTS.c.capability.label("grant_capability"),
            ACCESS_GRANTS.c.expires_at.label("access_expires_at"),
            LIBRARY_ITEMS.c.lesson_id.label("lesson_id"),
            LIBRARY_ITEMS.c.state.label("lesson_state"),
            LIBRARY_ITEMS.c.moderation_state.label("moderation_state"),
            LIBRARY_ITEMS.c.created_at.label("lesson_created_at"),
            LIBRARY_VERSIONS.c.version_id.label("version_id"),
            LIBRARY_VERSIONS.c.version_no.label("version_no"),
            LIBRARY_VERSIONS.c.content_json.label("content_json"),
        )
        allowed_capabilities = ("VIEW", "REUSE") if capability == "VIEW" else (capability,)
        stmt = select(*selected).select_from(base_from).where(
            ACCESS_GRANTS.c.state == "ACTIVE",
            ACCESS_GRANTS.c.capability.in_(allowed_capabilities),
            or_(ACCESS_GRANTS.c.expires_at.is_(None), ACCESS_GRANTS.c.expires_at > now),
            LIBRARY_ITEMS.c.state == "ACTIVE",
            LIBRARY_ITEMS.c.moderation_state == "VISIBLE",
            LIBRARY_VERSIONS.c.review_state == "APPROVED",
        )
        if source_kind == "PUBLIC":
            kinds = ("PUBLIC",)
        elif source_kind == "SHARED":
            kinds = ("PRINCIPAL", "PARENT_GROUP")
        else:
            kinds = ("PUBLIC", "PRINCIPAL", "PARENT_GROUP")
        stmt = stmt.where(ACCESS_GRANTS.c.audience_kind.in_(kinds))
        scoped: list[dict[str, Any]] = []
        if "PUBLIC" in kinds:
            public_stmt = stmt.where(ACCESS_GRANTS.c.audience_kind == "PUBLIC")
            public_stmt = self._cursor_filter(
                public_stmt, cursor, LIBRARY_ITEMS.c.created_at, LIBRARY_ITEMS.c.lesson_id
            )
            scoped.extend(self._rows_as_parent_access(public_stmt, limit))
        if "PRINCIPAL" in kinds:
            direct_stmt = stmt.where(
                ACCESS_GRANTS.c.audience_kind == "PRINCIPAL",
                ACCESS_GRANTS.c.audience_ref == parent_principal_ref,
            )
            direct_stmt = self._cursor_filter(
                direct_stmt, cursor, LIBRARY_ITEMS.c.created_at, LIBRARY_ITEMS.c.lesson_id
            )
            scoped.extend(self._rows_as_parent_access(direct_stmt, limit))
        if "PARENT_GROUP" in kinds:
            group_from = base_from.join(
                PARENT_GROUP_MEMBERS,
                and_(
                    PARENT_GROUP_MEMBERS.c.parent_group_id == ACCESS_GRANTS.c.audience_ref,
                    PARENT_GROUP_MEMBERS.c.parent_principal_ref == parent_principal_ref,
                    PARENT_GROUP_MEMBERS.c.state == "active",
                ),
            ).join(
                PARENT_GROUPS,
                and_(
                    PARENT_GROUPS.c.parent_group_id == PARENT_GROUP_MEMBERS.c.parent_group_id,
                    PARENT_GROUPS.c.state == "active",
                ),
            )
            group_stmt = select(*selected).select_from(group_from).where(
                ACCESS_GRANTS.c.state == "ACTIVE",
                ACCESS_GRANTS.c.audience_kind == "PARENT_GROUP",
                ACCESS_GRANTS.c.capability.in_(allowed_capabilities),
                or_(ACCESS_GRANTS.c.expires_at.is_(None), ACCESS_GRANTS.c.expires_at > now),
                LIBRARY_ITEMS.c.state == "ACTIVE",
                LIBRARY_ITEMS.c.moderation_state == "VISIBLE",
                LIBRARY_VERSIONS.c.review_state == "APPROVED",
            )
            group_stmt = self._cursor_filter(
                group_stmt, cursor, LIBRARY_ITEMS.c.created_at, LIBRARY_ITEMS.c.lesson_id
            )
            scoped.extend(self._rows_as_parent_access(group_stmt, limit))

        best: dict[tuple[str, str], dict[str, Any]] = {}
        for candidate in scoped:
            key = (candidate["lesson_id"], candidate["version_id"])
            prior = best.get(key)
            if prior is None or (candidate["access_source"] == "PUBLIC" and prior["access_source"] != "PUBLIC"):
                best[key] = candidate
        latest: dict[str, dict[str, Any]] = {}
        for candidate in best.values():
            prior = latest.get(candidate["lesson_id"])
            if prior is None or candidate["version_no"] > prior["version_no"]:
                latest[candidate["lesson_id"]] = candidate
        return sorted(
            latest.values(),
            key=lambda row: (row["created_at"], row["lesson_id"]),
            reverse=True,
        )

    def _rows_as_parent_access(self, stmt: Any, limit: int) -> list[dict[str, Any]]:
        rows = self.db.execute(
            stmt.order_by(LIBRARY_ITEMS.c.created_at.desc(), LIBRARY_ITEMS.c.lesson_id.desc())
            .limit(max(limit, 1))
        ).mappings().all()
        result: list[dict[str, Any]] = []
        for row in rows:
            result.append(
                {
                    "lesson_id": row["lesson_id"],
                    "version_id": row["version_id"],
                    "version_no": row["version_no"],
                    "content_json": row["content_json"],
                    "lesson_state": row["state"],
                    "moderation_state": row["moderation_state"],
                    "created_at": row["lesson_created_at"],
                    "access_source": "PUBLIC" if row["grant_audience_kind"] == "PUBLIC" else "SHARED",
                    "access_expires_at": row["access_expires_at"],
                    "grant_id": row["grant_id"],
                    "grant_capability": row["grant_capability"],
                }
            )
        return result

    def list_parent_lessons(
        self, *, parent_principal_ref: str, source: str,
        limit: int, cursor: str | None,
    ) -> dict[str, Any]:
        kind = None if source == "ALL" else source
        rows = self._parent_access_rows(
            parent_principal_ref=parent_principal_ref,
            capability="VIEW",
            source_kind=kind,
            limit=max(200, limit * 5 + 1),
            cursor=cursor,
        )
        if len(rows) > limit:
            rows = rows[:limit]
            next_cursor = self._encode_cursor(rows[-1]["created_at"], rows[-1]["lesson_id"])
        else:
            next_cursor = None
        items: list[dict[str, Any]] = []
        for row in rows:
            full = self._full_content_from_access(row)
            items.append(
                {
                    "contract": "ParentLessonSummaryV1",
                    "lesson_id": row["lesson_id"],
                    "version_id": row["version_id"],
                    "title": full["title"],
                    "topic": full["topic"],
                    "target_age_band_ref": full["target_age_band_ref"],
                    "target_age_band_version": full["target_age_band_version"],
                    "activity_count": len(full["activities"]),
                    "access_source": row["access_source"],
                }
            )
        return {"contract": "ParentLessonPageV1", "items": items, "next_cursor": next_cursor}

    def get_parent_lesson(
        self, *, parent_principal_ref: str, lesson_id: str,
    ) -> dict[str, Any]:
        rows = self._parent_access_rows(
            parent_principal_ref=parent_principal_ref, capability="VIEW", limit=1000
        )
        row = next((item for item in rows if item["lesson_id"] == lesson_id), None)
        if row is None:
            fail(404, "LESSON_NOT_FOUND", "Lesson was not found")
        if not can_read_as_parent(
            moderation_state=row["moderation_state"],
            lesson_state=row["lesson_state"],
            grant_states={row["grant_capability"]},
        ):
            fail(404, "LESSON_NOT_FOUND", "Lesson was not found")
        return self._parent_detail(row)

    def get_parent_lesson_export(
        self, *, parent_principal_ref: str, lesson_id: str,
    ) -> dict[str, Any]:
        rows = self._parent_access_rows(
            parent_principal_ref=parent_principal_ref, capability="DOWNLOAD", limit=1000
        )
        row = next((item for item in rows if item["lesson_id"] == lesson_id), None)
        if row is None:
            fail(404, "LESSON_NOT_FOUND", "Lesson was not found")
        return self._parent_detail(row, export=True)

    def get_upload_session_status(self, *, upload_session_id: str, actor: str) -> dict[str, Any]:
        session = self._load_upload_session(upload_session_id, actor, for_update=False)
        if session["state"] == "OPEN" and session["expires_at"] <= datetime.now(UTC):
            self.db.execute(
                UPLOAD_SESSIONS.update()
                .where(UPLOAD_SESSIONS.c.upload_session_id == upload_session_id)
                .values(state="EXPIRED")
            )
            self._commit()
            self._delete_upload_parts(upload_session_id)
            session = self._load_upload_session(upload_session_id, actor, for_update=False)
        parts = self.db.execute(
            select(UPLOAD_PARTS.c.part_number)
            .where(UPLOAD_PARTS.c.upload_session_id == upload_session_id)
            .order_by(UPLOAD_PARTS.c.part_number)
        ).scalars().all()
        return {
            "contract": "UploadSessionV1",
            "upload_session_id": session["upload_session_id"],
            "state": session["state"],
            "part_size_bytes": session["chunk_size_bytes"],
            "expected_parts": session["expected_parts"],
            "accepted_part_numbers": list(parts),
            "expires_at": session["expires_at"],
        }

    def abort_upload_session(self, *, upload_session_id: str, actor: str) -> dict[str, Any]:
        session = self._load_upload_session(upload_session_id, actor, for_update=True)
        if session["state"] == "ABORTED":
            return self.get_upload_session_status(upload_session_id=upload_session_id, actor=actor)
        if session["state"] != "OPEN":
            fail(409, "INVALID_TRANSITION", "Only an open upload session can be aborted")
        self.db.execute(
            UPLOAD_SESSIONS.update()
            .where(UPLOAD_SESSIONS.c.upload_session_id == upload_session_id)
            .values(state="ABORTED", aborted_at=datetime.now(UTC))
        )
        self._commit()
        self._delete_upload_parts(upload_session_id)
        return self.get_upload_session_status(upload_session_id=upload_session_id, actor=actor)

    def moderate_lesson(
        self, *, lesson_id: str, actor: str, expected_revision: int,
        moderation_state: str, reason: str, idempotency_key: str,
    ) -> dict[str, Any]:
        item = self.db.execute(
            select(LIBRARY_ITEMS).where(LIBRARY_ITEMS.c.lesson_id == lesson_id).with_for_update()
        ).mappings().one_or_none()
        if item is None:
            fail(404, "LESSON_NOT_FOUND", "Lesson was not found")
        normalized_reason = reason.strip()
        if not normalized_reason:
            fail(422, "INVALID_REQUEST", "Moderation reason is required")
        request_payload = {
            "state": moderation_state,
            "reason": normalized_reason,
            "if_match": expected_revision,
        }
        scope = f"PATCH /platform/lessons/{lesson_id}/moderation"
        replay = self._replay(
            organization_id=item["organization_id"], actor=actor, scope=scope,
            key=idempotency_key, payload=request_payload,
        )
        if replay is not None:
            return replay
        self._require_revision(item["revision"], expected_revision)

        def execute() -> dict[str, Any]:
            now = datetime.now(UTC)
            self.db.execute(
                LIBRARY_ITEMS.update()
                .where(LIBRARY_ITEMS.c.lesson_id == lesson_id)
                .values(
                    moderation_state=moderation_state,
                    moderation_reason=normalized_reason,
                    moderated_by=actor,
                    moderated_at=now,
                    revision=expected_revision + 1,
                    updated_at=now,
                )
            )
            self._audit(
                item["organization_id"], actor, f"lesson.moderation.{moderation_state.lower()}",
                "lesson", lesson_id,
            )
            return {
                "contract": "LessonModerationV1",
                "lesson_id": lesson_id,
                "state": moderation_state,
                "reason": normalized_reason,
                "moderator_ref": actor,
                "decided_at": now,
                "revision": expected_revision + 1,
            }

        return self._idempotent(
            organization_id=item["organization_id"],
            actor=actor,
            scope=scope,
            key=idempotency_key,
            payload=request_payload,
            execute=execute,
        )

    def _full_content_from_access(self, row: dict[str, Any]) -> dict[str, Any]:
        version = self._load_version(row["version_id"])
        return self._full_content(version)

    def _parent_detail(self, row: dict[str, Any], *, export: bool = False) -> dict[str, Any]:
        content = self._full_content_from_access(row)
        activity_items = content.pop("activities")
        return {
            "contract": "LessonExportV1" if export else "ParentLessonDetailV1",
            "lesson_id": row["lesson_id"],
            "version_id": row["version_id"],
            "version_no": row["version_no"],
            **content,
            "activities": activity_items,
            "access_source": row["access_source"],
            "access_expires_at": row["access_expires_at"],
        }

