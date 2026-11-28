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
from typing import Any, Callable, NoReturn
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
    remix_request_fingerprint,
    validate_content,
    verify_remix_source_content,
)
from sketch2life.domain.lesson_library.model import (
    decline_parent_group_invitation as decline_parent_group_invitation_state,
)
from sketch2life.infrastructure.lesson_library.receipt_compat import (
    ReceiptCompatibilityError,
    parent_group_membership_lookup,
    upgrade_parent_group_receipt,
)
from sketch2life.infrastructure.lesson_library.tables import (
    ACCESS_GRANTS,
    COMMAND_RECEIPTS,
    DOCUMENT_REVISIONS,
    LIBRARY_ITEMS,
    LIBRARY_VERSION_LINEAGE,
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
    Be1CommandReceiptModel,
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
_OPAQUE_ID = re.compile(r"^[A-Za-z0-9._:-]{1,256}$")
_SCOPED_CURSOR = re.compile(r"^[A-Za-z0-9_-]+$")
_SCOPED_CURSOR_MAX_BYTES = 1024
_REMIX_OPERATION_SCOPE = "POST /lesson-library/remixes"
_REMIX_RECEIPT_PK = "pk_be1_command_receipts"
_PARENT_GROUP_DECLINE_SCOPE = "POST /lesson-library/v1/me/parent-group-invitations/decline"
_PARENT_GROUP_REVOKE_SCOPE = "DELETE /lesson-library/v1/organizations/parent-groups/members"
_REMIX_SERIALIZATION_RETRIES = 3
_ALLOWED_UPLOADS = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}


class LessonLibraryError(RuntimeError):
    def __init__(
        self, status_code: int, code: str, message: str,
        field_errors: list[dict[str, str]] | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.field_errors = field_errors or []
        super().__init__(code)


class LessonLibraryStaleRevision(LessonLibraryError):
    """409 STALE_REVISION that carries the current revision for the ETag (C-D7)."""

    def __init__(self, current_revision: int) -> None:
        super().__init__(409, "STALE_REVISION", "The resource changed; reload before retrying")
        self.current_revision = current_revision


def fail(
    status_code: int,
    code: str,
    message: str,
    *,
    field_errors: list[dict[str, str]] | None = None,
) -> NoReturn:
    raise LessonLibraryError(status_code, code, message, field_errors)


def _normalize_search_filters(
    *,
    q: str | None,
    topic: str | None,
    target_age_band_ref: str | None,
    target_age_band_version: int | None,
) -> dict[str, Any]:
    normalized_q = None if q is None else q.strip()
    normalized_topic = None if topic is None else topic.strip()
    for field_name, value in (("q", normalized_q), ("topic", normalized_topic)):
        if value is not None and any(ord(char) < 32 or ord(char) == 127 for char in value):
            fail(
                400,
                "INVALID_REQUEST",
                f"{field_name} must not contain control characters",
                field_errors=[{"field": field_name, "code": "INVALID_FORMAT"}],
            )
    if normalized_q == "":
        fail(
            400,
            "INVALID_REQUEST",
            "q must not be empty",
            field_errors=[{"field": "q", "code": "EMPTY"}],
        )
    if normalized_q is not None and len(normalized_q) > 100:
        fail(
            400,
            "INVALID_REQUEST",
            "q must contain at most 100 code points",
            field_errors=[{"field": "q", "code": "TOO_LONG"}],
        )
    if normalized_topic == "":
        fail(
            400,
            "INVALID_REQUEST",
            "topic must not be empty",
            field_errors=[{"field": "topic", "code": "EMPTY"}],
        )
    if normalized_topic is not None and len(normalized_topic) > 120:
        fail(
            400,
            "INVALID_REQUEST",
            "topic must contain at most 120 code points",
            field_errors=[{"field": "topic", "code": "TOO_LONG"}],
        )
    if (target_age_band_ref is None) != (target_age_band_version is None):
        missing_field = (
            "target_age_band_ref" if target_age_band_ref is None else "target_age_band_version"
        )
        fail(
            400,
            "INVALID_REQUEST",
            "target age band reference and version must be provided together",
            field_errors=[{"field": missing_field, "code": "REQUIRED"}],
        )
    if target_age_band_ref is not None and not _OPAQUE_ID.fullmatch(target_age_band_ref):
        fail(
            400,
            "INVALID_REQUEST",
            "target age band reference is invalid",
            field_errors=[{"field": "target_age_band_ref", "code": "INVALID_FORMAT"}],
        )
    if target_age_band_version is not None and target_age_band_version < 1:
        fail(
            400,
            "INVALID_REQUEST",
            "target age band version must be positive",
            field_errors=[{"field": "target_age_band_version", "code": "OUT_OF_RANGE"}],
        )
    return {
        "q": normalized_q,
        "topic": normalized_topic,
        "target_age_band_ref": target_age_band_ref,
        "target_age_band_version": target_age_band_version,
    }


def _escape_like_literal(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _cursor_scope_digest(scope: dict[str, Any]) -> str:
    encoded_scope = json.dumps(
        scope, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded_scope).hexdigest()


def _invalid_scoped_cursor() -> NoReturn:
    raise LessonLibraryError(
        400,
        "INVALID_REQUEST",
        "Pagination cursor is invalid for this request",
        [{"field": "cursor", "code": "INVALID_FORMAT"}],
    )


def _encode_scoped_cursor(
    *, scope: dict[str, Any], sort_value: datetime | int, row_id: str, value_kind: str,
) -> str:
    if value_kind == "datetime" and isinstance(sort_value, datetime):
        encoded_value: str | int = sort_value.isoformat()
    elif value_kind == "integer" and type(sort_value) is int:
        encoded_value = sort_value
    else:
        _invalid_scoped_cursor()
    payload = {
        "v": 1,
        "scope": _cursor_scope_digest(scope),
        "kind": value_kind,
        "key": [encoded_value, row_id],
    }
    cursor = base64.urlsafe_b64encode(
        json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).decode("ascii").rstrip("=")
    if len(cursor.encode("ascii")) > _SCOPED_CURSOR_MAX_BYTES:
        _invalid_scoped_cursor()
    return cursor


def _decode_scoped_cursor(
    *, cursor: str, scope: dict[str, Any], value_kind: str,
) -> tuple[datetime | int, str]:
    try:
        encoded = cursor.encode("ascii")
        if (
            not encoded
            or len(encoded) > _SCOPED_CURSOR_MAX_BYTES
            or not _SCOPED_CURSOR.fullmatch(cursor)
        ):
            raise ValueError
        raw = base64.b64decode(
            encoded + b"=" * (-len(encoded) % 4), altchars=b"-_", validate=True
        )
        payload = json.loads(raw.decode("utf-8"))
        if (
            not isinstance(payload, dict)
            or set(payload) != {"v", "scope", "kind", "key"}
            or payload["v"] != 1
            or payload["scope"] != _cursor_scope_digest(scope)
            or payload["kind"] != value_kind
            or not isinstance(payload["key"], list)
            or len(payload["key"]) != 2
        ):
            raise ValueError
        raw_sort_value, row_id = payload["key"]
        if not isinstance(row_id, str) or not row_id or len(row_id) > 256:
            raise ValueError
        if value_kind == "datetime":
            if not isinstance(raw_sort_value, str):
                raise ValueError
            parsed_value = datetime.fromisoformat(raw_sort_value)
            if parsed_value.tzinfo is None:
                raise ValueError
            sort_value: datetime | int = parsed_value
        elif value_kind == "integer":
            if type(raw_sort_value) is not int or raw_sort_value < 1:
                raise ValueError
            sort_value = raw_sort_value
        else:
            raise ValueError
        return sort_value, row_id
    except (ValueError, UnicodeError, json.JSONDecodeError):
        _invalid_scoped_cursor()


def _scoped_cursor_filter(
    stmt: Any,
    cursor: str | None,
    *,
    scope: dict[str, Any],
    sort_col: Any,
    id_col: Any,
    value_kind: str,
) -> Any:
    if cursor is None:
        return stmt
    sort_value, row_id = _decode_scoped_cursor(
        cursor=cursor, scope=scope, value_kind=value_kind
    )
    return stmt.where(
        or_(sort_col < sort_value, and_(sort_col == sort_value, id_col < row_id))
    )


def _apply_lesson_search_filters(stmt: Any, filters: dict[str, Any] | None) -> Any:
    if filters is None:
        return stmt
    title_col = LIBRARY_VERSIONS.c.content_json["title"].astext
    topic_col = LIBRARY_VERSIONS.c.content_json["topic"].astext
    if filters["q"] is not None:
        pattern = f"%{_escape_like_literal(filters['q'])}%"
        stmt = stmt.where(
            or_(title_col.ilike(pattern, escape="\\"), topic_col.ilike(pattern, escape="\\"))
        )
    if filters["topic"] is not None:
        stmt = stmt.where(
            topic_col.ilike(_escape_like_literal(filters["topic"]), escape="\\")
        )
    if filters["target_age_band_ref"] is not None:
        stmt = stmt.where(
            LIBRARY_VERSIONS.c.content_json["target_age_band_ref"].astext
            == filters["target_age_band_ref"],
            LIBRARY_VERSIONS.c.content_json["target_age_band_version"].astext
            == str(filters["target_age_band_version"]),
        )
    return stmt


def upload_session_revision(state: str, part_count: int) -> int:
    """Derived upload-session revision (FEAT-066 C4, CT-5).

    1 + part rows while OPEN, 2 + part rows in every other state.
    """
    return (1 if state == "OPEN" else 2) + part_count


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
        ).where(
            LIBRARY_ITEMS.c.organization_id == organization_id,
            # Organization lesson lists are used for discovery and selection. Keep
            # archived lessons out of every staff list, including explicit state filters.
            LIBRARY_ITEMS.c.state == "ACTIVE",
        )
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
        expected_revision: int, content: LessonContentInputV1, idempotency_key: str,
    ) -> dict[str, Any]:
        content_data = content.model_dump(mode="json")
        self._validate_content(content_data)
        # C4: lock, replay under the lock, then ownership before the revision check.
        item = self._load_lesson(organization_id, lesson_id, for_update=True)
        scope = f"PATCH /organizations/{organization_id}/lessons/{lesson_id}"
        payload = {"content": content_data, "if_match": expected_revision}
        replay = self._replay(
            organization_id=organization_id, actor=actor, scope=scope,
            key=idempotency_key, payload=payload,
        )
        if replay is not None:
            return replay
        if item["created_by"] != actor:
            fail(404, "LESSON_NOT_FOUND", "Lesson was not found")
        self._require_revision(item["revision"], expected_revision)
        if item["state"] != "ACTIVE":
            fail(409, "INVALID_TRANSITION", "Archived lessons cannot be edited")

        def execute() -> dict[str, Any]:
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
            self.db.execute(
                LIBRARY_ITEMS.update().where(LIBRARY_ITEMS.c.lesson_id == lesson_id).values(
                    current_version_id=version_id,
                    revision=expected_revision + 1,
                    updated_at=now,
                )
            )
            self._audit(organization_id, actor, "lesson.version.create", "lesson", lesson_id)
            return self._detail(lesson_id, organization_id)

        return self._idempotent(
            organization_id=organization_id, actor=actor, scope=scope,
            key=idempotency_key, payload=payload, execute=execute,
        )

    def archive_lesson(
        self, *, organization_id: str, lesson_id: str, actor: str,
        manager: bool, expected_revision: int, idempotency_key: str,
    ) -> dict[str, Any]:
        item = self._load_lesson(organization_id, lesson_id, for_update=True)
        scope = f"DELETE /organizations/{organization_id}/lessons/{lesson_id}"
        payload = {"if_match": expected_revision}
        replay = self._replay(
            organization_id=organization_id, actor=actor, scope=scope,
            key=idempotency_key, payload=payload,
        )
        if replay is not None:
            return replay
        if not manager and item["created_by"] != actor:
            fail(404, "LESSON_NOT_FOUND", "Lesson was not found")
        self._require_revision(item["revision"], expected_revision)

        def execute() -> dict[str, Any]:
            if item["state"] == "ARCHIVED":
                return self._detail(lesson_id, organization_id)
            now = datetime.now(UTC)
            self.db.execute(
                LIBRARY_ITEMS.update().where(LIBRARY_ITEMS.c.lesson_id == lesson_id).values(
                    state="ARCHIVED", archived_at=now, updated_at=now,
                    revision=expected_revision + 1,
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
            return self._detail(lesson_id, organization_id)

        return self._idempotent(
            organization_id=organization_id, actor=actor, scope=scope,
            key=idempotency_key, payload=payload, execute=execute,
        )

    def create_lesson_version(
        self, *, organization_id: str, lesson_id: str, actor: str,
        expected_revision: int, source_revision_id: str, content: LessonContentInputV1,
        idempotency_key: str,
    ) -> dict[str, Any]:
        content_data = content.model_dump(mode="json")
        self._validate_content(content_data)
        item = self._load_lesson(organization_id, lesson_id, for_update=True)
        scope = f"POST /organizations/{organization_id}/lessons/{lesson_id}/versions"
        payload = {
            "source_document_revision_id": source_revision_id,
            "content": content_data,
            "if_match": expected_revision,
        }
        replay = self._replay(
            organization_id=organization_id, actor=actor, scope=scope,
            key=idempotency_key, payload=payload,
        )
        if replay is not None:
            return replay
        if item["created_by"] != actor:
            fail(404, "LESSON_NOT_FOUND", "Lesson was not found")
        self._require_revision(item["revision"], expected_revision)
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

        def execute() -> dict[str, Any]:
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
            self._audit(
                organization_id, actor, "lesson.version.from_document", "lesson", lesson_id
            )
            row = self._load_version(version_id)
            return self._version_response(row, with_content=True)

        return self._idempotent(
            organization_id=organization_id, actor=actor, scope=scope,
            key=idempotency_key, payload=payload, execute=execute,
        )

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

    def _load_lesson_for_version_read(
        self, organization_id: str, lesson_id: str, actor: str,
    ) -> Any:
        row = self.db.execute(
            select(LIBRARY_ITEMS).where(
                LIBRARY_ITEMS.c.organization_id == organization_id,
                LIBRARY_ITEMS.c.lesson_id == lesson_id,
            )
        ).mappings().one_or_none()
        if row is None:
            fail(404, "RESOURCE_NOT_FOUND", "Lesson version was not found")
        assert row is not None
        if row["visibility"] == "PRIVATE" and row["created_by"] != actor:
            fail(404, "RESOURCE_NOT_FOUND", "Lesson version was not found")
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

    def list_lesson_versions(
        self, *, organization_id: str, lesson_id: str, actor: str,
        limit: int, cursor: str | None,
    ) -> dict[str, Any]:
        if not 1 <= limit <= 100:
            fail(400, "INVALID_REQUEST", "limit must be between 1 and 100")
        self._load_lesson_for_version_read(organization_id, lesson_id, actor)
        scope = {
            "actor": actor,
            "route": f"GET /organizations/{organization_id}/lessons/{lesson_id}/versions",
            "source": "OWNING_ORGANIZATION",
            "filters": {},
            "order": "version_no:desc,version_id:desc",
        }
        stmt = select(LIBRARY_VERSIONS).where(LIBRARY_VERSIONS.c.lesson_id == lesson_id)
        stmt = _scoped_cursor_filter(
            stmt,
            cursor,
            scope=scope,
            sort_col=LIBRARY_VERSIONS.c.version_no,
            id_col=LIBRARY_VERSIONS.c.version_id,
            value_kind="integer",
        )
        rows = self.db.execute(
            stmt.order_by(
                LIBRARY_VERSIONS.c.version_no.desc(), LIBRARY_VERSIONS.c.version_id.desc()
            )
            .limit(limit + 1)
        ).mappings().all()
        next_cursor = None
        if len(rows) > limit:
            rows = rows[:limit]
            last = rows[-1]
            next_cursor = _encode_scoped_cursor(
                scope=scope,
                sort_value=int(last["version_no"]),
                row_id=last["version_id"],
                value_kind="integer",
            )
        return {
            "contract": "LessonVersionPageV1",
            "lesson_id": lesson_id,
            "items": [
                {
                    "contract": "LessonVersionSummaryV1",
                    "version_id": row["version_id"],
                    "version_no": row["version_no"],
                    "review_state": row["review_state"],
                    "structured_content_hash": row["structured_content_hash"],
                    "source_document_revision_id": row["source_document_revision_id"],
                    "authored_principal_ref": row["authored_by"],
                    "created_at": row["created_at"],
                }
                for row in rows
            ],
            "next_cursor": next_cursor,
        }

    def get_lesson_version(
        self, *, organization_id: str, lesson_id: str, version_id: str, actor: str,
    ) -> dict[str, Any]:
        self._load_lesson_for_version_read(organization_id, lesson_id, actor)
        version = self.db.execute(
            select(LIBRARY_VERSIONS).where(
                LIBRARY_VERSIONS.c.lesson_id == lesson_id,
                LIBRARY_VERSIONS.c.version_id == version_id,
            )
        ).mappings().one_or_none()
        if version is None:
            fail(404, "RESOURCE_NOT_FOUND", "Lesson version was not found")
        return self._version_response(version, with_content=True)

    def remix_public_lesson(
        self, *, organization_id: str, lesson_id: str, actor: str, actor_issuer: str,
        source_version_id: str, source_content_sha256: str, idempotency_key: str,
    ) -> dict[str, Any]:
        fingerprint = remix_request_fingerprint(
            destination_organization_id=organization_id,
            lesson_id=lesson_id,
            source_version_id=source_version_id,
            source_content_sha256=source_content_sha256,
        )
        for attempt in range(_REMIX_SERIALIZATION_RETRIES):
            try:
                return self._attempt_public_remix(
                    organization_id=organization_id,
                    lesson_id=lesson_id,
                    actor=actor,
                    actor_issuer=actor_issuer,
                    source_version_id=source_version_id,
                    source_content_sha256=source_content_sha256,
                    idempotency_key=idempotency_key,
                    fingerprint=fingerprint,
                )
            except IntegrityError as exc:
                self.db.rollback()
                if self._is_remix_receipt_conflict(exc):
                    return self._replay_public_remix_after_race(
                        organization_id=organization_id,
                        lesson_id=lesson_id,
                        actor=actor,
                        actor_issuer=actor_issuer,
                        source_version_id=source_version_id,
                        source_content_sha256=source_content_sha256,
                        idempotency_key=idempotency_key,
                        fingerprint=fingerprint,
                    )
                fail(409, "RESOURCE_CONFLICT", "The request conflicts with existing records")
            except SQLAlchemyError as exc:
                self.db.rollback()
                last_attempt = attempt + 1 >= _REMIX_SERIALIZATION_RETRIES
                if self._is_retryable_database_error(exc) and not last_attempt:
                    continue
                fail(503, "DEPENDENCY_UNAVAILABLE", "Database is temporarily unavailable")
        fail(503, "DEPENDENCY_UNAVAILABLE", "Database is temporarily unavailable")

    def _attempt_public_remix(
        self, *, organization_id: str, lesson_id: str, actor: str, actor_issuer: str,
        source_version_id: str, source_content_sha256: str, idempotency_key: str,
        fingerprint: str,
    ) -> dict[str, Any]:
        self._require_remix_teacher(organization_id, actor, actor_issuer)
        _source_item, source_version = self._load_public_remix_source(
            lesson_id=lesson_id, source_version_id=source_version_id
        )
        source_content = self._full_content(source_version)
        verified_hash = self._verified_remix_hash(
            source_content,
            stored_hash=source_version["structured_content_hash"],
            requested_hash=source_content_sha256,
        )
        receipt = self._find_remix_receipt(actor, idempotency_key)
        if receipt is not None:
            replay = self._remix_receipt_response(
                receipt,
                organization_id=organization_id,
                fingerprint=fingerprint,
            )
            self.db.commit()
            return replay

        now = datetime.now(UTC)
        derived_lesson_id = str(uuid4())
        derived_version_id = str(uuid4())
        self.db.execute(
            LIBRARY_ITEMS.insert().values(
                lesson_id=derived_lesson_id,
                organization_id=organization_id,
                owner_kind="ORGANIZATION",
                created_by=actor,
                state="ACTIVE",
                visibility="PRIVATE",
                internal_visibility="PRIVATE",
                moderation_state="VISIBLE",
                current_version_id=derived_version_id,
                revision=1,
                created_at=now,
                updated_at=now,
            )
        )
        self._insert_version(
            lesson_id=derived_lesson_id,
            version_id=derived_version_id,
            version_no=1,
            content=source_content,
            actor=actor,
            source_revision_id=None,
            review_state="DRAFT",
            created_at=now,
        )
        self.db.execute(
            LIBRARY_VERSION_LINEAGE.insert().values(
                derived_version_id=derived_version_id,
                source_version_id=source_version_id,
                source_content_hash=verified_hash,
                created_at=now,
            )
        )
        self._audit(
            organization_id, actor, "lesson.remix.create", "lesson", derived_lesson_id
        )
        derived_item = self._load_lesson(organization_id, derived_lesson_id)
        response = {
            "contract": "RemixLessonResponseV1",
            "lesson": self._detail_from_row(derived_item),
            "source": {
                "lesson_id": lesson_id,
                "version_id": source_version_id,
                "content_sha256": verified_hash,
            },
        }
        self.db.add(
            Be1CommandReceiptModel(
                principal_ref=actor,
                operation_scope=_REMIX_OPERATION_SCOPE,
                idempotency_key=idempotency_key,
                organization_id=organization_id,
                request_fingerprint=fingerprint,
                response_json=self._json_safe(response),
            )
        )
        self.db.commit()
        return response

    def _replay_public_remix_after_race(
        self, *, organization_id: str, lesson_id: str, actor: str, actor_issuer: str,
        source_version_id: str, source_content_sha256: str, idempotency_key: str,
        fingerprint: str,
    ) -> dict[str, Any]:
        try:
            self._require_remix_teacher(organization_id, actor, actor_issuer)
            _source_item, source_version = self._load_public_remix_source(
                lesson_id=lesson_id, source_version_id=source_version_id
            )
            source_content = self._full_content(source_version)
            self._verified_remix_hash(
                source_content,
                stored_hash=source_version["structured_content_hash"],
                requested_hash=source_content_sha256,
            )
            receipt = self._find_remix_receipt(actor, idempotency_key)
            if receipt is None:
                fail(503, "DEPENDENCY_UNAVAILABLE", "The concurrent receipt is unavailable")
            response = self._remix_receipt_response(
                receipt,
                organization_id=organization_id,
                fingerprint=fingerprint,
            )
            self.db.commit()
            return response
        except SQLAlchemyError:
            self.db.rollback()
            fail(503, "DEPENDENCY_UNAVAILABLE", "Database is temporarily unavailable")

    def _require_remix_teacher(
        self, organization_id: str, actor: str, actor_issuer: str,
    ) -> None:
        identity = self.db.scalar(
            select(AdultIdentityModel)
            .where(AdultIdentityModel.subject == actor)
            .with_for_update(read=True)
        )
        if (
            identity is None
            or identity.state != "active"
            or identity.account_role != "teacher"
            or identity.issuer != actor_issuer
        ):
            fail(404, "RESOURCE_NOT_FOUND", "The requested resource was not found")
        assignments = self.db.execute(
            select(OrganizationAssignmentModel)
            .where(
                OrganizationAssignmentModel.organization_id == organization_id,
                OrganizationAssignmentModel.subject == actor,
                OrganizationAssignmentModel.role == "teacher",
                OrganizationAssignmentModel.active.is_(True),
            )
            .with_for_update(read=True)
        ).scalars().all()
        if not assignments:
            fail(404, "RESOURCE_NOT_FOUND", "The requested resource was not found")

    def _load_public_remix_source(
        self, *, lesson_id: str, source_version_id: str,
    ) -> tuple[Any, Any]:
        item = self.db.execute(
            select(LIBRARY_ITEMS)
            .where(LIBRARY_ITEMS.c.lesson_id == lesson_id)
            .with_for_update()
        ).mappings().one_or_none()
        if (
            item is None
            or item["state"] != "ACTIVE"
            or item["visibility"] != "PUBLIC"
            or item["moderation_state"] != "VISIBLE"
        ):
            fail(404, "RESOURCE_NOT_FOUND", "The requested resource was not found")

        stmt = (
            select(LIBRARY_VERSIONS)
            .select_from(
                LIBRARY_VERSIONS.join(
                    ACCESS_GRANTS,
                    and_(
                        ACCESS_GRANTS.c.lesson_id == LIBRARY_VERSIONS.c.lesson_id,
                        ACCESS_GRANTS.c.version_id == LIBRARY_VERSIONS.c.version_id,
                    ),
                )
            )
            .where(
                LIBRARY_VERSIONS.c.lesson_id == lesson_id,
                LIBRARY_VERSIONS.c.version_id == source_version_id,
                LIBRARY_VERSIONS.c.review_state == "APPROVED",
                ACCESS_GRANTS.c.audience_kind == "PUBLIC",
                ACCESS_GRANTS.c.audience_ref.is_(None),
                ACCESS_GRANTS.c.capability == "REUSE",
                ACCESS_GRANTS.c.state == "ACTIVE",
                ACCESS_GRANTS.c.approved_by.is_not(None),
                ACCESS_GRANTS.c.approved_at.is_not(None),
                or_(
                    ACCESS_GRANTS.c.expires_at.is_(None),
                    ACCESS_GRANTS.c.expires_at > func.clock_timestamp(),
                ),
            )
            .order_by(ACCESS_GRANTS.c.access_grant_id)
            .with_for_update(of=ACCESS_GRANTS)
        )
        versions = self.db.execute(stmt).mappings().all()
        if not versions:
            fail(404, "RESOURCE_NOT_FOUND", "The requested resource was not found")
        return item, versions[0]

    @staticmethod
    def _verified_remix_hash(
        source_content: dict[str, Any], *, stored_hash: str, requested_hash: str,
    ) -> str:
        try:
            return verify_remix_source_content(
                source_content,
                stored_hash=stored_hash,
                requested_hash=requested_hash,
            )
        except LessonLibraryRuleError:
            fail(409, "STALE_SOURCE_VERSION", "The source version hash is stale")

    def _find_remix_receipt(
        self, actor: str, idempotency_key: str,
    ) -> Be1CommandReceiptModel | None:
        return self.db.execute(
            select(Be1CommandReceiptModel)
            .where(
                Be1CommandReceiptModel.principal_ref == actor,
                Be1CommandReceiptModel.operation_scope == _REMIX_OPERATION_SCOPE,
                Be1CommandReceiptModel.idempotency_key == idempotency_key,
            )
            .with_for_update()
        ).scalar_one_or_none()

    @staticmethod
    def _remix_receipt_response(
        receipt: Be1CommandReceiptModel, *, organization_id: str, fingerprint: str,
    ) -> dict[str, Any]:
        if (
            receipt.organization_id != organization_id
            or receipt.request_fingerprint != fingerprint
        ):
            fail(
                400,
                "INVALID_IDEMPOTENCY_KEY",
                "Idempotency-Key was already used for another request",
            )
        return dict(receipt.response_json)

    @staticmethod
    def _is_remix_receipt_conflict(exc: IntegrityError) -> bool:
        original = exc.orig
        sqlstate = getattr(original, "sqlstate", None) or getattr(original, "pgcode", None)
        diagnostic = getattr(original, "diag", None)
        constraint = getattr(diagnostic, "constraint_name", None)
        return sqlstate == "23505" and constraint == _REMIX_RECEIPT_PK

    @staticmethod
    def _is_retryable_database_error(exc: SQLAlchemyError) -> bool:
        original = getattr(exc, "orig", None)
        sqlstate = getattr(original, "sqlstate", None) or getattr(original, "pgcode", None)
        return sqlstate in {"40001", "40P01"}

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
            fail(400, "INVALID_IDEMPOTENCY_KEY", "Idempotency-Key was already used for another request")
        stored_response = previous["response_json"]
        try:
            if (
                isinstance(stored_response, dict)
                and stored_response.get("contract")
                in {"ParentGroupInvitationV1", "ParentGroupMembershipV1"}
            ):
                response_organization_id = stored_response.get("organization_id")
                if (
                    response_organization_id is not None
                    and response_organization_id != organization_id
                ):
                    raise ReceiptCompatibilityError(
                        "receipt organization does not match operation scope"
                    )
                stored_response = {
                    **stored_response,
                    "organization_id": organization_id,
                }
            lookup = parent_group_membership_lookup(
                organization_id=organization_id,
                principal_ref=actor,
                operation_scope=scope,
                response=stored_response,
            )
            membership_row = None
            if lookup is not None:
                stmt = (
                    select(
                        PARENT_GROUP_MEMBERS.c.membership_id.label("membership_id"),
                        PARENT_GROUP_MEMBERS.c.parent_group_id.label("parent_group_id"),
                        PARENT_GROUP_MEMBERS.c.parent_principal_ref.label("parent_principal_ref"),
                        PARENT_GROUP_MEMBERS.c.revision.label("revision"),
                        PARENT_GROUPS.c.organization_id.label("organization_id"),
                    )
                    .select_from(
                        PARENT_GROUP_MEMBERS.join(
                            PARENT_GROUPS,
                            PARENT_GROUPS.c.parent_group_id
                            == PARENT_GROUP_MEMBERS.c.parent_group_id,
                        )
                    )
                    .where(
                        PARENT_GROUP_MEMBERS.c.membership_id == lookup.membership_id,
                        PARENT_GROUP_MEMBERS.c.parent_group_id == lookup.parent_group_id,
                        PARENT_GROUPS.c.organization_id == lookup.organization_id,
                    )
                )
                if lookup.parent_principal_ref is not None:
                    stmt = stmt.where(
                        PARENT_GROUP_MEMBERS.c.parent_principal_ref.in_(
                            self._parent_audience_refs(lookup.parent_principal_ref)
                        )
                    )
                membership_row = self.db.execute(stmt).mappings().one_or_none()
                if membership_row is None:
                    raise ReceiptCompatibilityError("current membership row is unavailable")
                membership_data = dict(membership_row)
            else:
                membership_data = None
            return upgrade_parent_group_receipt(
                operation_scope=scope,
                response=stored_response,
                membership_row=membership_data,
                organization_id=organization_id,
                principal_ref=(
                    membership_data["parent_principal_ref"]
                    if lookup is not None
                    and lookup.parent_principal_ref is not None
                    and membership_data is not None
                    else actor
                ),
            )
        except ReceiptCompatibilityError as exc:
            raise LessonLibraryError(
                409,
                "IDEMPOTENCY_RECEIPT_INCOMPATIBLE",
                "Stored idempotency receipt cannot be replayed under the current response contract",
            ) from exc

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
            raise LessonLibraryStaleRevision(int(current))

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
    def _teacher_activity_cursor_filter(
        stmt: Any,
        cursor: str | None,
        *,
        time_col: Any,
        activity_order_col: Any,
        id_col: Any,
    ) -> Any:
        if cursor is None:
            return stmt
        try:
            decoded = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)).decode("utf-8")
            timestamp, raw_order, row_id = decoded.split("|", 2)
            created_at = datetime.fromisoformat(timestamp)
            activity_order = int(raw_order)
            if created_at.tzinfo is None or activity_order < 1 or not row_id:
                raise ValueError
        except (ValueError, UnicodeError):
            fail(422, "INVALID_REQUEST", "Pagination cursor is invalid")
        return stmt.where(
            or_(
                time_col < created_at,
                and_(
                    time_col == created_at,
                    or_(
                        activity_order_col > activity_order,
                        and_(activity_order_col == activity_order, id_col > row_id),
                    ),
                ),
            )
        )

    @staticmethod
    def _encode_teacher_activity_cursor(
        created_at: datetime, activity_order: int, row_id: str
    ) -> str:
        value = f"{created_at.isoformat()}|{activity_order}|{row_id}".encode()
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
            fail(413, "LESSON_FILE_TOO_LARGE", "Lesson source files are limited to 25 MB")
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
                "revision": upload_session_revision("OPEN", 0),
            }

        result = self._idempotent(
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
        # A receipt stored before C4 has no revision; a new session had no parts (CT-5).
        return {**result, "revision": result.get("revision", upload_session_revision("OPEN", 0))}

    def put_upload_part(
        self, *, upload_session_id: str, actor: str, part_number: int,
        body: bytes, part_sha256: str, range_start: int, range_end: int, range_total: int,
    ) -> dict[str, Any]:
        # C4 (R1-09): lock the session so no part row lands after a terminal transition.
        session = self._load_upload_session(upload_session_id, actor, for_update=True)
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
                fail(409, "UPLOAD_PART_CONFLICT", "This part number already has different bytes")
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
                fail(422, "UPLOAD_INCOMPLETE", "Upload parts are incomplete")

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
                                fail(
                                    413, "LESSON_FILE_TOO_LARGE",
                                    "Lesson source files are limited to 25 MB",
                                )
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
        # C4 (R1-03): answer by state, whether persisted earlier or set by this request.
        if session["state"] == "EXPIRED":
            fail(410, "UPLOAD_SESSION_EXPIRED", "Upload session has expired")
        if session["state"] != "OPEN":
            fail(409, "UPLOAD_SESSION_STATE_CONFLICT", "Upload session is no longer open")
        if self._expire_if_due(session):
            fail(410, "UPLOAD_SESSION_EXPIRED", "Upload session has expired")

    def _expire_if_due(self, session: Any) -> bool:
        """Mark an OPEN session past its expiry as EXPIRED, commit, purge parts; True if done."""
        if session["state"] != "OPEN" or session["expires_at"] > datetime.now(UTC):
            return False
        changed = self.db.execute(
            UPLOAD_SESSIONS.update()
            .where(
                UPLOAD_SESSIONS.c.upload_session_id == session["upload_session_id"],
                UPLOAD_SESSIONS.c.state == "OPEN",
            )
            .values(state="EXPIRED")
        ).rowcount
        self._commit()
        if not changed:
            # A concurrent complete or abort closed the session first (review C4-IMPL-R1-02).
            return False
        self._delete_upload_parts(session["upload_session_id"])
        return True

    def _upload_status(self, session: Any) -> dict[str, Any]:
        parts = self.db.execute(
            select(UPLOAD_PARTS.c.part_number)
            .where(UPLOAD_PARTS.c.upload_session_id == session["upload_session_id"])
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
            "revision": upload_session_revision(session["state"], len(parts)),
        }

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
        # T-10b takes the item before public-grant rows; keep publication writers in that order.
        item = self._load_lesson(organization_id, lesson_id, for_update=True)
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
            # T-10d (TD-24, FR-PL-05/FR-PL-06): only PUBLIC needs the Manager decision. A
            # private audience (school, named Parent, Parent group) does not read review_state.
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
        stmt = (
            select(
                ACCESS_GRANTS,
                LIBRARY_VERSIONS.c.content_json.label("lesson_content_json"),
                LIBRARY_VERSIONS.c.version_no.label("lesson_version_no"),
            )
            .select_from(
                ACCESS_GRANTS.outerjoin(
                    LIBRARY_VERSIONS,
                    and_(
                        LIBRARY_VERSIONS.c.version_id == ACCESS_GRANTS.c.version_id,
                        LIBRARY_VERSIONS.c.lesson_id == ACCESS_GRANTS.c.lesson_id,
                    ),
                )
            )
            .where(ACCESS_GRANTS.c.organization_id == organization_id)
        )
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
        grant_hint = self._load_grant(grant_id, organization_id)
        item = self.db.execute(
            select(LIBRARY_ITEMS)
            .where(LIBRARY_ITEMS.c.lesson_id == grant_hint["lesson_id"])
            .with_for_update()
        ).mappings().one_or_none()
        if item is None:
            fail(404, "RESOURCE_NOT_FOUND", "Access grant was not found")
        grant = self._load_grant(grant_id, organization_id, for_update=True)
        if grant["lesson_id"] != item["lesson_id"]:
            fail(404, "RESOURCE_NOT_FOUND", "Access grant was not found")
        self._require_revision(grant["revision"], expected_revision)
        if grant["audience_kind"] != "PUBLIC" or grant["state"] != "PENDING_REVIEW":
            fail(409, "INVALID_TRANSITION", "Only pending Public grants can be decided")
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
        actor: str, manager: bool, expected_revision: int, idempotency_key: str,
    ) -> dict[str, Any]:
        grant_hint = self._load_grant(grant_id, organization_id)
        item = self.db.execute(
            select(LIBRARY_ITEMS)
            .where(LIBRARY_ITEMS.c.lesson_id == grant_hint["lesson_id"])
            .with_for_update()
        ).mappings().one_or_none()
        if item is None:
            fail(404, "RESOURCE_NOT_FOUND", "Access grant was not found")
        grant = self._load_grant(grant_id, organization_id, for_update=True)
        if grant["lesson_id"] != item["lesson_id"]:
            fail(404, "RESOURCE_NOT_FOUND", "Access grant was not found")
        scope = (
            f"DELETE /organizations/{organization_id}/lessons/{lesson_id}"
            f"/access-grants/{grant_id}"
        )
        payload = {"if_match": expected_revision}
        replay = self._replay(
            organization_id=organization_id, actor=actor, scope=scope,
            key=idempotency_key, payload=payload,
        )
        if replay is not None:
            return replay
        if grant["lesson_id"] != lesson_id:
            fail(404, "RESOURCE_NOT_FOUND", "Access grant was not found")
        if not manager and grant["granted_by"] != actor:
            fail(404, "RESOURCE_NOT_FOUND", "Access grant was not found")
        self._require_revision(grant["revision"], expected_revision)

        def execute() -> dict[str, Any]:
            if grant["state"] == "REVOKED":
                return self._grant_response(grant)
            now = datetime.now(UTC)
            self.db.execute(
                ACCESS_GRANTS.update()
                .where(ACCESS_GRANTS.c.access_grant_id == grant_id)
                .values(state="REVOKED", revoked_at=now, revision=expected_revision + 1)
            )
            self._recalculate_visibility(lesson_id)
            self._audit(
                organization_id, actor, "lesson.access_grant.revoke",
                "lesson_access_grant", grant_id,
            )
            return self._grant_response(
                self.db.execute(
                    select(ACCESS_GRANTS).where(ACCESS_GRANTS.c.access_grant_id == grant_id)
                ).mappings().one()
            )

        return self._idempotent(
            organization_id=organization_id, actor=actor, scope=scope,
            key=idempotency_key, payload=payload, execute=execute,
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
    def _lesson_title(content: Any) -> str | None:
        if not isinstance(content, dict):
            return None
        title = content.get("title")
        return title.strip() if isinstance(title, str) and title.strip() else None

    @staticmethod
    def _grant_response(row: Any) -> dict[str, Any]:
        return {
            "contract": "LessonAccessGrantV1",
            "access_grant_id": row["access_grant_id"],
            "lesson_id": row["lesson_id"],
            "lesson_title": LessonLibraryService._lesson_title(
                row.get("lesson_content_json")
            ),
            "version_id": row["version_id"],
            "version_no": row.get("lesson_version_no"),
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
            duplicate_refs = self._parent_invitation_duplicate_refs(parent_principal_ref)
            prior_rows = self.db.execute(
                select(PARENT_GROUP_MEMBERS).where(
                    PARENT_GROUP_MEMBERS.c.parent_group_id == group_id,
                    PARENT_GROUP_MEMBERS.c.parent_principal_ref.in_(duplicate_refs),
                )
                .order_by(
                    PARENT_GROUP_MEMBERS.c.invited_at.desc(),
                    PARENT_GROUP_MEMBERS.c.membership_id.desc(),
                )
                .with_for_update()
            ).mappings().all()
            if any(row["state"] in {"invited", "active"} for row in prior_rows):
                fail(409, "INVITATION_EXISTS", "Parent already has an active group invitation or membership")
            prior = next(
                (
                    row
                    for row in prior_rows
                    if row["parent_principal_ref"] == parent_principal_ref
                ),
                None,
            )
            now = datetime.now(UTC)
            if prior is None:
                membership_id = str(uuid4())
                membership_revision = 1
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
                membership_revision = prior["revision"] + 1
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
                "organization_id": organization_id,
                "state": "INVITED",
                "invited_at": now,
                "expires_at": now + INVITATION_TTL,
                "accepted_at": None,
                "revision": membership_revision,
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

    def _load_group(
        self,
        group_id: str,
        organization_id: str,
        *,
        for_update: bool = False,
        not_found_message: str = "Parent group was not found",
    ) -> Any:
        stmt = select(PARENT_GROUPS).where(
            PARENT_GROUPS.c.parent_group_id == group_id,
            PARENT_GROUPS.c.organization_id == organization_id,
        )
        if for_update:
            stmt = stmt.with_for_update()
        row = self.db.execute(stmt).mappings().one_or_none()
        if row is None:
            fail(404, "RESOURCE_NOT_FOUND", not_found_message)
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

    def list_parent_group_members(
        self,
        *,
        organization_id: str,
        group_id: str,
        manager_principal_ref: str,
        state: str | None,
        limit: int,
        cursor: str | None,
    ) -> dict[str, Any]:
        self._load_group(group_id, organization_id)
        if state is None:
            state_filter = None
        elif state == "ACCEPTED":
            state_filter = "active"
        else:
            state_filter = state.lower()
        scope = {
            "operation": (
                "GET /organizations/{organization_id}/parent-groups/{parent_group_id}/members"
            ),
            "organization_id": organization_id,
            "parent_group_id": group_id,
            "manager_principal_ref": manager_principal_ref,
            "state": state_filter,
        }
        # READ COMMITTED gives this count and the following page query separate snapshots.
        # A concurrent membership change can therefore make these two parts briefly disagree.
        count_rows = self.db.execute(
            select(
                PARENT_GROUP_MEMBERS.c.state.label("state"),
                func.count().label("member_count"),
            )
            .where(PARENT_GROUP_MEMBERS.c.parent_group_id == group_id)
            .group_by(PARENT_GROUP_MEMBERS.c.state)
        ).mappings().all()
        counts = {
            "invited": 0,
            "accepted": 0,
            "declined": 0,
            "revoked": 0,
            "expired": 0,
        }
        state_count_keys = {
            "invited": "invited",
            "active": "accepted",
            "declined": "declined",
            "revoked": "revoked",
            "expired": "expired",
        }
        counts.update({
            state_count_keys[row["state"]]: int(row["member_count"])
            for row in count_rows
        })
        counts["total"] = sum(counts.values())

        stmt = select(PARENT_GROUP_MEMBERS).where(
            PARENT_GROUP_MEMBERS.c.parent_group_id == group_id
        )
        if state_filter is not None:
            stmt = stmt.where(PARENT_GROUP_MEMBERS.c.state == state_filter)
        stmt = _scoped_cursor_filter(
            stmt,
            cursor,
            scope=scope,
            sort_col=PARENT_GROUP_MEMBERS.c.invited_at,
            id_col=PARENT_GROUP_MEMBERS.c.membership_id,
            value_kind="datetime",
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
            next_cursor = _encode_scoped_cursor(
                scope=scope,
                sort_value=rows[-1]["invited_at"],
                row_id=rows[-1]["membership_id"],
                value_kind="datetime",
            )
        return {
            "contract": "ParentGroupMemberPageV1",
            "items": [self._parent_group_member_summary_response(row) for row in rows],
            "counts": counts,
            "next_cursor": next_cursor,
        }

    @staticmethod
    def _parent_group_member_summary_response(row: Any) -> dict[str, Any]:
        stored_state = row["state"]
        return {
            "membership_id": row["membership_id"],
            "parent_group_id": row["parent_group_id"],
            "state": "ACCEPTED" if stored_state == "active" else stored_state.upper(),
            "invited_at": row["invited_at"],
            "expires_at": row["expires_at"],
            "accepted_at": row["accepted_at"],
            "revision": row["revision"],
        }

    def list_parent_group_invitations(
        self, *, parent_principal_ref: str, limit: int, cursor: str | None,
    ) -> dict[str, Any]:
        audience_refs = self._parent_audience_refs(parent_principal_ref)
        now = datetime.now(UTC)
        stmt = self._membership_with_organization_stmt().where(
            PARENT_GROUP_MEMBERS.c.parent_principal_ref.in_(audience_refs),
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

    def list_parent_group_memberships(
        self, *, parent_principal_ref: str, limit: int, cursor: str | None,
    ) -> dict[str, Any]:
        audience_refs = self._parent_audience_refs(parent_principal_ref)
        scope = {
            "operation": "GET /me/parent-group-memberships",
            "parent_principal_ref": parent_principal_ref,
            "state": "active",
        }
        stmt = self._membership_with_organization_stmt().where(
            PARENT_GROUP_MEMBERS.c.parent_principal_ref.in_(audience_refs),
            PARENT_GROUP_MEMBERS.c.state == "active",
        )
        stmt = _scoped_cursor_filter(
            stmt,
            cursor,
            scope=scope,
            sort_col=PARENT_GROUP_MEMBERS.c.invited_at,
            id_col=PARENT_GROUP_MEMBERS.c.membership_id,
            value_kind="datetime",
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
            next_cursor = _encode_scoped_cursor(
                scope=scope,
                sort_value=rows[-1]["invited_at"],
                row_id=rows[-1]["membership_id"],
                value_kind="datetime",
            )
        return {
            "contract": "ParentGroupMembershipPageV1",
            "items": [self._membership_response(row) for row in rows],
            "next_cursor": next_cursor,
        }

    def accept_parent_group_invitation(
        self, *, membership_id: str, actor: str, idempotency_key: str,
    ) -> dict[str, Any]:
        membership = self._load_membership(membership_id, for_update=True)
        if membership["parent_principal_ref"] not in self._parent_audience_refs(actor):
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
                "organization_id": org_id,
                "state": "ACTIVE",
                "invited_at": current["invited_at"],
                "expires_at": current["expires_at"],
                "accepted_at": now,
                "revision": current["revision"] + 1,
            }

        return self._idempotent(
            organization_id=org_id,
            actor=actor,
            scope=f"POST /me/parent-group-invitations/{membership_id}/accept",
            key=idempotency_key,
            payload={"membership_id": membership_id},
            execute=execute,
        )

    def decline_parent_group_invitation(
        self, *, membership_id: str, actor: str, actor_issuer: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        # Lock order is parent group then membership for both decline and revoke. This first
        # unlocked read only discovers the immutable group id needed to take that order.
        observed = self._load_membership(
            membership_id, not_found_message="Invitation was not found"
        )
        group = self.db.execute(
            select(PARENT_GROUPS)
            .where(PARENT_GROUPS.c.parent_group_id == observed["parent_group_id"])
            .with_for_update()
        ).mappings().one_or_none()
        if group is None:
            fail(404, "RESOURCE_NOT_FOUND", "Invitation was not found")
        current = self._load_membership(
            membership_id,
            for_update=True,
            not_found_message="Invitation was not found",
        )
        if current["parent_group_id"] != group["parent_group_id"]:
            fail(404, "RESOURCE_NOT_FOUND", "Invitation was not found")
        self._authorize_parent_group_decline(
            actor=actor,
            actor_issuer=actor_issuer,
            membership=current,
        )
        org_id = group["organization_id"]
        operation_scope = self._parent_group_operation_scope(
            _PARENT_GROUP_DECLINE_SCOPE, org_id, group["parent_group_id"], membership_id
        )
        fingerprint = self._parent_group_command_fingerprint(
            method="POST",
            organization_id=org_id,
            group_id=group["parent_group_id"],
            membership_id=membership_id,
        )
        receipt = self._find_parent_group_receipt(actor, operation_scope, idempotency_key)
        if receipt is not None:
            return self._replay_parent_group_receipt(
                receipt, organization_id=org_id, fingerprint=fingerprint
            )

        now = datetime.now(UTC)
        try:
            next_state = decline_parent_group_invitation_state(
                current["state"], invitation_expired=current["expires_at"] <= now
            )
        except LessonLibraryRuleError as exc:
            if exc.code == "INVITATION_EXPIRED":
                fail(409, "INVITATION_EXPIRED", "Invitation has expired")
            fail(409, "INVALID_STATE_TRANSITION", "Invitation is no longer active")
        self.db.execute(
            PARENT_GROUP_MEMBERS.update()
            .where(
                PARENT_GROUP_MEMBERS.c.membership_id == membership_id,
                PARENT_GROUP_MEMBERS.c.revision == current["revision"],
            )
            .values(state=next_state, revision=current["revision"] + 1)
        )
        self._audit(
            org_id,
            actor,
            "parent_group.invitation.decline",
            "parent_group_membership",
            membership_id,
        )
        response = self._membership_response(self._load_membership(membership_id))

        def replay_after_race() -> dict[str, Any]:
            locked_group = self.db.execute(
                select(PARENT_GROUPS)
                .where(PARENT_GROUPS.c.parent_group_id == group["parent_group_id"])
                .with_for_update()
            ).mappings().one_or_none()
            locked_membership = self._load_membership(
                membership_id,
                for_update=True,
                not_found_message="Invitation was not found",
            )
            if (
                locked_group is None
                or locked_group["organization_id"] != org_id
                or locked_membership["parent_group_id"] != group["parent_group_id"]
            ):
                fail(404, "RESOURCE_NOT_FOUND", "Invitation was not found")
            self._authorize_parent_group_decline(
                actor=actor,
                actor_issuer=actor_issuer,
                membership=locked_membership,
            )
            return self._reload_parent_group_receipt(
                actor=actor,
                operation_scope=operation_scope,
                idempotency_key=idempotency_key,
                organization_id=org_id,
                fingerprint=fingerprint,
            )

        return self._commit_parent_group_receipt(
            actor=actor,
            operation_scope=operation_scope,
            idempotency_key=idempotency_key,
            organization_id=org_id,
            fingerprint=fingerprint,
            response=response,
            replay_after_race=replay_after_race,
        )

    def revoke_parent_group_membership(
        self, *, organization_id: str, group_id: str, membership_id: str,
        actor: str, actor_issuer: str, manager: bool, expected_revision: int,
        idempotency_key: str,
    ) -> dict[str, Any]:
        self._load_group(
            group_id,
            organization_id,
            for_update=True,
            not_found_message="Group membership was not found",
        )
        current = self._load_membership(membership_id, for_update=True)
        if current["parent_group_id"] != group_id:
            fail(404, "RESOURCE_NOT_FOUND", "Group membership was not found")
        self._authorize_parent_group_revoke(
            organization_id=organization_id,
            actor=actor,
            actor_issuer=actor_issuer,
            manager=manager,
            membership=current,
        )
        operation_scope = self._parent_group_operation_scope(
            _PARENT_GROUP_REVOKE_SCOPE, organization_id, group_id, membership_id
        )
        fingerprint = self._parent_group_command_fingerprint(
            method="DELETE",
            organization_id=organization_id,
            group_id=group_id,
            membership_id=membership_id,
            expected_revision=expected_revision,
        )
        receipt = self._find_parent_group_receipt(actor, operation_scope, idempotency_key)
        if receipt is not None:
            return self._replay_parent_group_receipt(
                receipt,
                organization_id=organization_id,
                fingerprint=fingerprint,
            )

        self._require_revision(current["revision"], expected_revision)
        if current["state"] == "revoked":
            fail(409, "INVALID_STATE_TRANSITION", "Membership is already revoked")
        self.db.execute(
            PARENT_GROUP_MEMBERS.update()
            .where(
                PARENT_GROUP_MEMBERS.c.membership_id == membership_id,
                PARENT_GROUP_MEMBERS.c.revision == expected_revision,
            )
            .values(state="revoked", revision=expected_revision + 1)
        )
        self._audit(
            organization_id,
            actor,
            "parent_group.membership.revoke",
            "parent_group_membership",
            membership_id,
        )
        response = self._membership_response(self._load_membership(membership_id))

        def replay_after_race() -> dict[str, Any]:
            self._load_group(
                group_id,
                organization_id,
                for_update=True,
                not_found_message="Group membership was not found",
            )
            locked_membership = self._load_membership(membership_id, for_update=True)
            if locked_membership["parent_group_id"] != group_id:
                fail(404, "RESOURCE_NOT_FOUND", "Group membership was not found")
            self._authorize_parent_group_revoke(
                organization_id=organization_id,
                actor=actor,
                actor_issuer=actor_issuer,
                manager=manager,
                membership=locked_membership,
            )
            return self._reload_parent_group_receipt(
                actor=actor,
                operation_scope=operation_scope,
                idempotency_key=idempotency_key,
                organization_id=organization_id,
                fingerprint=fingerprint,
            )

        return self._commit_parent_group_receipt(
            actor=actor,
            operation_scope=operation_scope,
            idempotency_key=idempotency_key,
            organization_id=organization_id,
            fingerprint=fingerprint,
            response=response,
            replay_after_race=replay_after_race,
        )

    def _authorize_parent_group_revoke(
        self,
        *,
        organization_id: str,
        actor: str,
        actor_issuer: str,
        manager: bool,
        membership: Any,
    ) -> None:
        if manager:
            assignments = self.db.execute(
                select(OrganizationAssignmentModel)
                .where(
                    OrganizationAssignmentModel.organization_id == organization_id,
                    OrganizationAssignmentModel.subject == actor,
                    OrganizationAssignmentModel.role == "school_admin",
                    OrganizationAssignmentModel.active.is_(True),
                )
                .with_for_update(read=True)
            ).scalars().all()
            identity = self.db.execute(
                select(AdultIdentityModel)
                .where(AdultIdentityModel.subject == actor)
                .with_for_update(read=True)
            ).scalar_one_or_none()
            if (
                not assignments
                or identity is None
                or identity.state != "active"
                or identity.account_role != "school_manager"
                or identity.issuer != actor_issuer
            ):
                fail(404, "RESOURCE_NOT_FOUND", "Group membership was not found")
            return

        identity = self.db.execute(
            select(AdultIdentityModel)
            .where(AdultIdentityModel.subject == actor)
            .with_for_update(read=True)
        ).scalar_one_or_none()
        if (
            identity is None
            or identity.state != "active"
            or identity.account_role != "parent"
            or identity.issuer != actor_issuer
            or membership["parent_principal_ref"] not in self._parent_audience_refs(actor)
        ):
            fail(404, "RESOURCE_NOT_FOUND", "Group membership was not found")

    def _authorize_parent_group_decline(
        self, *, actor: str, actor_issuer: str, membership: Any,
    ) -> None:
        identity = self.db.execute(
            select(AdultIdentityModel)
            .where(AdultIdentityModel.subject == actor)
            .with_for_update(read=True)
        ).scalar_one_or_none()
        if (
            identity is None
            or identity.state != "active"
            or identity.account_role != "parent"
            or identity.issuer != actor_issuer
            or membership["parent_principal_ref"] not in self._parent_audience_refs(actor)
        ):
            fail(404, "RESOURCE_NOT_FOUND", "Invitation was not found")

    def _find_parent_group_receipt(
        self, actor: str, operation_scope: str, idempotency_key: str,
    ) -> Be1CommandReceiptModel | None:
        return self.db.execute(
            select(Be1CommandReceiptModel)
            .where(
                Be1CommandReceiptModel.principal_ref == actor,
                Be1CommandReceiptModel.operation_scope == operation_scope,
                Be1CommandReceiptModel.idempotency_key == idempotency_key,
            )
            .with_for_update()
        ).scalar_one_or_none()

    def _parent_group_operation_scope(
        self, route_scope: str, organization_id: str, group_id: str, membership_id: str,
    ) -> str:
        resource_hash = self._fingerprint({
            "organization_id": organization_id,
            "parent_group_id": group_id,
            "membership_id": membership_id,
        })
        return f"{route_scope}:{resource_hash}"

    @staticmethod
    def _parent_group_command_fingerprint(
        *,
        method: str,
        organization_id: str,
        group_id: str,
        membership_id: str,
        expected_revision: int | None = None,
    ) -> str:
        payload: dict[str, Any] = {
            "method": method,
            "organization_id": organization_id,
            "parent_group_id": group_id,
            "membership_id": membership_id,
        }
        if expected_revision is not None:
            payload["expected_revision"] = expected_revision
        return LessonLibraryService._fingerprint(payload)

    @staticmethod
    def _is_parent_group_receipt_conflict(exc: IntegrityError) -> bool:
        original = exc.orig
        sqlstate = getattr(original, "sqlstate", None) or getattr(original, "pgcode", None)
        diagnostic = getattr(original, "diag", None)
        constraint = getattr(diagnostic, "constraint_name", None)
        return sqlstate == "23505" and constraint == _REMIX_RECEIPT_PK

    def _parent_group_receipt_response(
        self,
        receipt: Be1CommandReceiptModel,
        *,
        organization_id: str,
        fingerprint: str,
    ) -> dict[str, Any]:
        if (
            receipt.organization_id != organization_id
            or receipt.request_fingerprint != fingerprint
        ):
            fail(
                400,
                "INVALID_IDEMPOTENCY_KEY",
                "Idempotency-Key was already used for another request",
            )
        stored = receipt.response_json
        if not isinstance(stored, dict) or set(stored) != {"body", "etag"}:
            fail(503, "DEPENDENCY_UNAVAILABLE", "Stored command receipt is incompatible")
        body = stored["body"]
        if (
            not isinstance(body, dict)
            or not isinstance(body.get("revision"), int)
            or stored["etag"] != f'"{body["revision"]}"'
        ):
            fail(503, "DEPENDENCY_UNAVAILABLE", "Stored command receipt is incompatible")
        response = dict(body)
        if response.get("contract") == "ParentGroupMembershipV1":
            response_organization_id = response.get("organization_id")
            if (
                response_organization_id is not None
                and response_organization_id != organization_id
            ):
                fail(503, "DEPENDENCY_UNAVAILABLE", "Stored command receipt is incompatible")
            response["organization_id"] = organization_id
        return response

    def _replay_parent_group_receipt(
        self,
        receipt: Be1CommandReceiptModel,
        *,
        organization_id: str,
        fingerprint: str,
    ) -> dict[str, Any]:
        response = self._parent_group_receipt_response(
            receipt,
            organization_id=organization_id,
            fingerprint=fingerprint,
        )
        try:
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            fail(503, "DEPENDENCY_UNAVAILABLE", "Database is temporarily unavailable")
        return response

    def _reload_parent_group_receipt(
        self,
        *,
        actor: str,
        operation_scope: str,
        idempotency_key: str,
        organization_id: str,
        fingerprint: str,
    ) -> dict[str, Any]:
        receipt = self._find_parent_group_receipt(actor, operation_scope, idempotency_key)
        if receipt is None:
            fail(503, "DEPENDENCY_UNAVAILABLE", "The concurrent command receipt is unavailable")
        return self._replay_parent_group_receipt(
            receipt,
            organization_id=organization_id,
            fingerprint=fingerprint,
        )

    def _commit_parent_group_receipt(
        self,
        *,
        actor: str,
        operation_scope: str,
        idempotency_key: str,
        organization_id: str,
        fingerprint: str,
        response: dict[str, Any],
        replay_after_race: Callable[[], dict[str, Any]],
    ) -> dict[str, Any]:
        self.db.add(
            Be1CommandReceiptModel(
                principal_ref=actor,
                operation_scope=operation_scope,
                idempotency_key=idempotency_key,
                organization_id=organization_id,
                request_fingerprint=fingerprint,
                response_json={
                    "body": self._json_safe(response),
                    "etag": f'"{response["revision"]}"',
                },
            )
        )
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            if self._is_parent_group_receipt_conflict(exc):
                try:
                    return replay_after_race()
                except SQLAlchemyError:
                    self.db.rollback()
                    fail(503, "DEPENDENCY_UNAVAILABLE", "Database is temporarily unavailable")
            fail(409, "RESOURCE_CONFLICT", "The request conflicts with existing records")
        except SQLAlchemyError:
            self.db.rollback()
            fail(503, "DEPENDENCY_UNAVAILABLE", "Database is temporarily unavailable")
        return response

    def _load_membership(
        self,
        membership_id: str,
        *,
        for_update: bool = False,
        not_found_message: str = "Group membership was not found",
    ) -> Any:
        stmt = self._membership_with_organization_stmt().where(
            PARENT_GROUP_MEMBERS.c.membership_id == membership_id
        )
        if for_update:
            stmt = stmt.with_for_update(of=PARENT_GROUP_MEMBERS)
        row = self.db.execute(stmt).mappings().one_or_none()
        if row is None:
            fail(404, "RESOURCE_NOT_FOUND", not_found_message)
        return row

    @staticmethod
    def _membership_with_organization_stmt() -> Any:
        return select(
            PARENT_GROUP_MEMBERS,
            PARENT_GROUPS.c.organization_id.label("organization_id"),
        ).select_from(
            PARENT_GROUP_MEMBERS.join(
                PARENT_GROUPS,
                PARENT_GROUPS.c.parent_group_id == PARENT_GROUP_MEMBERS.c.parent_group_id,
            )
        )

    @staticmethod
    def _membership_response(row: Any) -> dict[str, Any]:
        return {
            "contract": "ParentGroupMembershipV1",
            "membership_id": row["membership_id"],
            "parent_group_id": row["parent_group_id"],
            "organization_id": row["organization_id"],
            "state": row["state"].upper(),
            "invited_at": row["invited_at"],
            "expires_at": row["expires_at"],
            "accepted_at": row["accepted_at"],
            "revision": row["revision"],
        }

    def list_lesson_invitations(
        self, *, parent_principal_ref: str, limit: int, cursor: str | None,
    ) -> dict[str, Any]:
        audience_refs = self._parent_audience_refs(parent_principal_ref)
        stmt = select(ACCESS_GRANTS).where(
            ACCESS_GRANTS.c.audience_kind == "PRINCIPAL",
            ACCESS_GRANTS.c.audience_ref.in_(audience_refs),
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
        audience_refs = self._parent_audience_refs(actor)
        grant = self.db.execute(
            select(ACCESS_GRANTS).where(
                ACCESS_GRANTS.c.access_grant_id == access_grant_id,
                ACCESS_GRANTS.c.audience_kind == "PRINCIPAL",
                ACCESS_GRANTS.c.audience_ref.in_(audience_refs),
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

    def _parent_audience_refs(self, parent_principal_ref: str) -> tuple[str, ...]:
        """Return this active Parent's unambiguous subject and account id aliases."""

        identity = self.db.get(AdultIdentityModel, parent_principal_ref)
        if (
            identity is None
            or identity.state != "active"
            or identity.account_role != "parent"
        ):
            return ()
        refs: list[str] = []
        for candidate in (identity.subject, identity.account_id):
            if candidate in refs:
                continue
            other_identity = self.db.scalar(
                select(AdultIdentityModel.subject)
                .where(
                    AdultIdentityModel.subject != parent_principal_ref,
                    or_(
                        AdultIdentityModel.subject == candidate,
                        AdultIdentityModel.account_id == candidate,
                    ),
                )
                .limit(1)
            )
            if other_identity is None:
                refs.append(candidate)
        return tuple(refs)

    def _parent_invitation_duplicate_refs(
        self, parent_principal_ref: str,
    ) -> tuple[str, ...]:
        """Resolve a Manager-supplied Parent reference for duplicate detection only."""

        identities = self.db.execute(
            select(AdultIdentityModel).where(
                or_(
                    AdultIdentityModel.subject == parent_principal_ref,
                    AdultIdentityModel.account_id == parent_principal_ref,
                )
            ).with_for_update()
        ).scalars().all()
        if len(identities) != 1:
            return (parent_principal_ref,)
        identity = identities[0]
        if identity.state != "active" or identity.account_role != "parent":
            return (parent_principal_ref,)
        return self._parent_audience_refs(identity.subject) or (parent_principal_ref,)

    def _parent_access_rows(
        self, *, parent_principal_ref: str, capability: str,
        source_kind: str | None = None, limit: int = 501, cursor: str | None = None,
        search_filters: dict[str, Any] | None = None,
        cursor_scope: dict[str, Any] | None = None,
        sort_by: str = "created_at",
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
            LIBRARY_ITEMS.c.updated_at.label("lesson_updated_at"),
            LIBRARY_VERSIONS.c.version_id.label("version_id"),
            LIBRARY_VERSIONS.c.version_no.label("version_no"),
            LIBRARY_VERSIONS.c.content_json.label("content_json"),
            LIBRARY_VERSIONS.c.structured_content_hash.label("structured_content_hash"),
        )
        sort_col = (
            LIBRARY_ITEMS.c.updated_at if sort_by == "updated_at" else LIBRARY_ITEMS.c.created_at
        )
        allowed_capabilities = ("VIEW", "REUSE") if capability == "VIEW" else (capability,)
        stmt = select(*selected).select_from(base_from).where(
            ACCESS_GRANTS.c.state == "ACTIVE",
            ACCESS_GRANTS.c.capability.in_(allowed_capabilities),
            or_(ACCESS_GRANTS.c.expires_at.is_(None), ACCESS_GRANTS.c.expires_at > now),
            LIBRARY_ITEMS.c.state == "ACTIVE",
            LIBRARY_ITEMS.c.moderation_state == "VISIBLE",
        )
        stmt = _apply_lesson_search_filters(stmt, search_filters)

        def with_cursor(query: Any) -> Any:
            if cursor_scope is not None:
                return _scoped_cursor_filter(
                    query,
                    cursor,
                    scope=cursor_scope,
                    sort_col=sort_col,
                    id_col=LIBRARY_ITEMS.c.lesson_id,
                    value_kind="datetime",
                )
            return self._cursor_filter(query, cursor, sort_col, LIBRARY_ITEMS.c.lesson_id)

        if source_kind == "PUBLIC":
            kinds = ("PUBLIC",)
        elif source_kind == "SHARED":
            kinds = ("PRINCIPAL", "PARENT_GROUP")
        else:
            kinds = ("PUBLIC", "PRINCIPAL", "PARENT_GROUP")
        stmt = stmt.where(ACCESS_GRANTS.c.audience_kind.in_(kinds))
        scoped: list[dict[str, Any]] = []
        if "PUBLIC" in kinds:
            # T-10d: only a PUBLIC lesson needs the Manager-approved version (FR-PL-05, BR-51);
            # a private share (PRINCIPAL, PARENT_GROUP) reads a version in any review state.
            public_stmt = stmt.where(
                ACCESS_GRANTS.c.audience_kind == "PUBLIC",
                LIBRARY_VERSIONS.c.review_state == "APPROVED",
            )
            public_stmt = with_cursor(public_stmt)
            scoped.extend(self._rows_as_parent_access(public_stmt, limit, sort_col=sort_col))
        if "PRINCIPAL" in kinds:
            direct_stmt = stmt.where(
                ACCESS_GRANTS.c.audience_kind == "PRINCIPAL",
                ACCESS_GRANTS.c.audience_ref.in_(
                    self._parent_audience_refs(parent_principal_ref)
                ),
            )
            direct_stmt = with_cursor(direct_stmt)
            scoped.extend(self._rows_as_parent_access(direct_stmt, limit, sort_col=sort_col))
        if "PARENT_GROUP" in kinds:
            audience_refs = self._parent_audience_refs(parent_principal_ref)
            group_from = base_from.join(
                PARENT_GROUP_MEMBERS,
                and_(
                    PARENT_GROUP_MEMBERS.c.parent_group_id == ACCESS_GRANTS.c.audience_ref,
                    PARENT_GROUP_MEMBERS.c.parent_principal_ref.in_(audience_refs),
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
            )
            group_stmt = _apply_lesson_search_filters(group_stmt, search_filters)
            group_stmt = with_cursor(group_stmt)
            scoped.extend(self._rows_as_parent_access(group_stmt, limit, sort_col=sort_col))

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
            key=lambda row: (row[sort_by], row["lesson_id"]),
            reverse=True,
        )

    def _rows_as_parent_access(
        self, stmt: Any, limit: int, *, sort_col: Any
    ) -> list[dict[str, Any]]:
        rows = self.db.execute(
            stmt.order_by(sort_col.desc(), LIBRARY_ITEMS.c.lesson_id.desc())
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
                    "lesson_state": row["lesson_state"],
                    "moderation_state": row["moderation_state"],
                    "created_at": row["lesson_created_at"],
                    "updated_at": row["lesson_updated_at"],
                    "structured_content_hash": row["structured_content_hash"],
                    "access_source": "PUBLIC" if row["grant_audience_kind"] == "PUBLIC" else "SHARED",
                    "access_expires_at": row["access_expires_at"],
                    "grant_id": row["grant_id"],
                    "grant_capability": row["grant_capability"],
                }
            )
        return result

    def list_parent_lessons(
        self, *, parent_principal_ref: str, source: str,
        limit: int, cursor: str | None, q: str | None = None, topic: str | None = None,
        target_age_band_ref: str | None = None,
        target_age_band_version: int | None = None,
    ) -> dict[str, Any]:
        if not 1 <= limit <= 100:
            fail(400, "INVALID_REQUEST", "limit must be between 1 and 100")
        filters = _normalize_search_filters(
            q=q,
            topic=topic,
            target_age_band_ref=target_age_band_ref,
            target_age_band_version=target_age_band_version,
        )
        scope = {
            "actor": parent_principal_ref,
            "route": "GET /me/lessons",
            "source": source,
            "filters": filters,
            "order": "created_at:desc,lesson_id:desc",
        }
        kind = None if source == "ALL" else source
        rows = self._parent_access_rows(
            parent_principal_ref=parent_principal_ref,
            capability="VIEW",
            source_kind=kind,
            limit=max(200, limit * 5 + 1),
            cursor=cursor,
            search_filters=filters,
            cursor_scope=scope,
        )
        if len(rows) > limit:
            rows = rows[:limit]
            next_cursor = _encode_scoped_cursor(
                scope=scope,
                sort_value=rows[-1]["created_at"],
                row_id=rows[-1]["lesson_id"],
                value_kind="datetime",
            )
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

    def search_public_lessons(
        self, *, organization_id: str, actor: str, q: str | None, topic: str | None,
        target_age_band_ref: str | None, target_age_band_version: int | None,
        limit: int, cursor: str | None,
    ) -> dict[str, Any]:
        if not 1 <= limit <= 100:
            fail(400, "INVALID_REQUEST", "limit must be between 1 and 100")
        filters = _normalize_search_filters(
            q=q,
            topic=topic,
            target_age_band_ref=target_age_band_ref,
            target_age_band_version=target_age_band_version,
        )
        scope = {
            "actor": actor,
            "route": f"GET /organizations/{organization_id}/public-lessons",
            "source": "PUBLIC",
            "filters": filters,
            "order": "updated_at:desc,lesson_id:desc",
        }
        rows = self._parent_access_rows(
            parent_principal_ref=actor,
            capability="VIEW",
            source_kind="PUBLIC",
            limit=max(200, limit * 5 + 1),
            cursor=cursor,
            search_filters=filters,
            cursor_scope=scope,
            sort_by="updated_at",
        )
        if len(rows) > limit:
            rows = rows[:limit]
            next_cursor = _encode_scoped_cursor(
                scope=scope,
                sort_value=rows[-1]["updated_at"],
                row_id=rows[-1]["lesson_id"],
                value_kind="datetime",
            )
        else:
            next_cursor = None
        items: list[dict[str, Any]] = []
        for row in rows:
            full = self._full_content_from_access(row)
            items.append(
                {
                    "contract": "PublicLessonSummaryV1",
                    "lesson_id": row["lesson_id"],
                    "version_id": row["version_id"],
                    "structured_content_hash": row["structured_content_hash"],
                    "title": full["title"],
                    "topic": full["topic"],
                    "target_age_band_ref": full["target_age_band_ref"],
                    "target_age_band_version": full["target_age_band_version"],
                    "activity_count": len(full["activities"]),
                    "updated_at": row["updated_at"],
                }
            )
        return {"contract": "PublicLessonPageV1", "items": items, "next_cursor": next_cursor}

    def list_parent_activity_catalog(
        self, *, parent_principal_ref: str, limit: int = 500,
    ) -> list[dict[str, Any]]:
        """Return Parent-readable published/shared lesson versions for internal AI selection."""

        if not 1 <= limit <= 500:
            fail(422, "INVALID_REQUEST", "catalog limit must be between 1 and 500")
        rows = self._parent_access_rows(
            parent_principal_ref=parent_principal_ref,
            capability="VIEW",
            limit=limit,
        )
        return [self._parent_detail(row) for row in rows[:limit]]

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
        if self._expire_if_due(session):
            session = self._load_upload_session(upload_session_id, actor, for_update=False)
        return self._upload_status(session)

    def abort_upload_session(
        self, *, upload_session_id: str, actor: str, expected_revision: int,
        idempotency_key: str,
    ) -> dict[str, Any]:
        """DELETE an upload session (SRS 1658): expected version, idempotent, 202 (C4, CT-14)."""
        session = self._load_upload_session(upload_session_id, actor, for_update=True)
        organization_id = session["organization_id"]
        scope = f"DELETE /upload-sessions/{upload_session_id}"
        payload = {"if_match": expected_revision}
        replay = self._replay(
            organization_id=organization_id, actor=actor, scope=scope,
            key=idempotency_key, payload=payload,
        )
        if replay is not None:
            return replay
        if self._expire_if_due(session):
            session = self._load_upload_session(upload_session_id, actor, for_update=True)
        current = self._upload_status(session)
        self._require_revision(current["revision"], expected_revision)
        if session["state"] == "EXPIRED":
            fail(410, "UPLOAD_SESSION_EXPIRED", "Upload session has expired")
        if session["state"] not in {"OPEN", "ABORTED"}:
            fail(409, "UPLOAD_SESSION_STATE_CONFLICT", "Only an open upload session can be aborted")
        aborting = session["state"] == "OPEN"

        def execute() -> dict[str, Any]:
            if not aborting:
                return current
            self.db.execute(
                UPLOAD_SESSIONS.update()
                .where(UPLOAD_SESSIONS.c.upload_session_id == upload_session_id)
                .values(state="ABORTED", aborted_at=datetime.now(UTC))
            )
            return self._upload_status(
                self._load_upload_session(upload_session_id, actor, for_update=False)
            )

        result = self._idempotent(
            organization_id=organization_id, actor=actor, scope=scope,
            key=idempotency_key, payload=payload, execute=execute,
        )
        if aborting:
            # Storage purge after the commit (C4, R1-12); partial bytes are never used.
            self._delete_upload_parts(upload_session_id)
        return result

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
        version = self._load_version(row["version_id"])
        content = self._full_content(version)
        activity_items = content.pop("activities")
        return {
            "contract": "LessonExportV1" if export else "ParentLessonDetailV1",
            "lesson_id": row["lesson_id"],
            "version_id": row["version_id"],
            "version_no": row["version_no"],
            "content_sha256": version["structured_content_hash"],
            **content,
            "activities": activity_items,
            "access_source": row["access_source"],
            "access_expires_at": row["access_expires_at"],
        }

    def list_teacher_activities(
        self,
        *,
        organization_id: str,
        actor: str,
        manager: bool,
        limit: int,
        cursor: str | None,
    ) -> dict[str, Any]:
        """List activities from current approved versions the caller may read."""
        statement = select(
            LIBRARY_ITEMS.c.lesson_id.label("lesson_id"),
            LIBRARY_ITEMS.c.created_by.label("created_by"),
            LIBRARY_ITEMS.c.visibility.label("visibility"),
            LIBRARY_ITEMS.c.updated_at.label("updated_at"),
            LIBRARY_VERSIONS.c.version_id.label("version_id"),
            LIBRARY_VERSIONS.c.version_no.label("version_no"),
            LIBRARY_VERSIONS.c.structured_content_hash.label("content_sha256"),
            LIBRARY_VERSIONS.c.content_json.label("content_json"),
            VERSION_ACTIVITIES.c.activity_id.label("lesson_activity_id"),
            VERSION_ACTIVITIES.c.activity_order.label("activity_order"),
            VERSION_ACTIVITIES.c.activity_json.label("activity_json"),
        ).select_from(
            LIBRARY_ITEMS.join(
                LIBRARY_VERSIONS,
                LIBRARY_VERSIONS.c.version_id == LIBRARY_ITEMS.c.current_version_id,
            ).join(
                VERSION_ACTIVITIES,
                VERSION_ACTIVITIES.c.version_id == LIBRARY_VERSIONS.c.version_id,
            )
        ).where(
            LIBRARY_ITEMS.c.organization_id == organization_id,
            LIBRARY_ITEMS.c.state == "ACTIVE",
            LIBRARY_ITEMS.c.moderation_state == "VISIBLE",
            LIBRARY_VERSIONS.c.review_state == "APPROVED",
        )
        if not manager:
            statement = statement.where(
                or_(
                    LIBRARY_ITEMS.c.created_by == actor,
                    LIBRARY_ITEMS.c.visibility != "PRIVATE",
                )
            )
        statement = self._teacher_activity_cursor_filter(
            statement,
            cursor,
            time_col=LIBRARY_ITEMS.c.updated_at,
            activity_order_col=VERSION_ACTIVITIES.c.activity_order,
            id_col=VERSION_ACTIVITIES.c.activity_id,
        )
        rows = self.db.execute(
            statement.order_by(
                LIBRARY_ITEMS.c.updated_at.desc(),
                VERSION_ACTIVITIES.c.activity_order.asc(),
                VERSION_ACTIVITIES.c.activity_id.asc(),
            ).limit(limit + 1)
        ).mappings().all()
        next_cursor = None
        if len(rows) > limit:
            rows = rows[:limit]
            last_row = rows[-1]
            next_cursor = self._encode_teacher_activity_cursor(
                last_row["updated_at"],
                last_row["activity_order"],
                last_row["lesson_activity_id"],
            )
        items: list[dict[str, object]] = []
        for row in rows:
            lesson = row.get("content_json")
            activity = row.get("activity_json")
            if not isinstance(lesson, dict) or not isinstance(activity, dict):
                continue
            lesson_title = lesson.get("title")
            lesson_topic = lesson.get("topic")
            activity_fields = {
                key: activity.get(key)
                for key in (
                    "title",
                    "objective",
                    "activity_kind",
                    "materials_text",
                    "preparation_text",
                    "instructions_text",
                    "observation_notes",
                    "safety_notes",
                )
            }
            if (
                not isinstance(lesson_title, str)
                or not isinstance(lesson_topic, str)
                or not isinstance(activity_fields["activity_kind"], str)
                or activity_fields["activity_kind"] not in {"outdoor", "indoor", "mixed"}
                or any(
                    not isinstance(value, str)
                    for key, value in activity_fields.items()
                    if key != "activity_kind"
                )
            ):
                continue
            items.append(
                {
                    "lesson_id": row["lesson_id"],
                    "version_id": row["version_id"],
                    "version_no": row["version_no"],
                    "content_sha256": row["content_sha256"],
                    "lesson_title": lesson_title,
                    "lesson_topic": lesson_topic,
                    "lesson_activity_id": row["lesson_activity_id"],
                    "activity_order": row["activity_order"],
                    **activity_fields,
                }
            )
        return {
            "contract": "TeacherActivityPageV1",
            "items": items,
            "next_cursor": next_cursor,
        }

