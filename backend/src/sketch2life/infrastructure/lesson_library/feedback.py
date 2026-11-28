"""Version-pinned lesson feedback with server-side organization authorization."""

from __future__ import annotations

import hashlib
import json
from typing import Any
from uuid import uuid4

from sqlalchemy import and_, func, select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from sketch2life.domain.platform_admin import AdminError, require_revision
from sketch2life.infrastructure.lesson_library.feedback_tables import (
    FEEDBACK_MESSAGES,
    FEEDBACK_THREADS,
)
from sketch2life.infrastructure.lesson_library.service import (
    LessonLibraryError,
    LessonLibraryService,
    fail,
)
from sketch2life.infrastructure.lesson_library.tables import LIBRARY_ITEMS, LIBRARY_VERSIONS
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    Be1CommandReceiptModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.infrastructure.identity.identity_labels import (
    account_profiles,
    safe_display_name,
)
from sketch2life.infrastructure.platform_admin.pagination import (
    apply_datetime_cursor,
    cursor_scope,
    next_datetime_cursor,
)


class LessonFeedbackService:
    def __init__(
        self,
        admin: Any,
        parent_lesson: Any = None,
        identity_provisioner: Any = None,
    ) -> None:
        self.admin, self.db, self.parent_lesson = admin, admin.db, parent_lesson
        self.identity_provisioner = identity_provisioner

    def authorize(self, organization_id):
        account = self.admin.identity(admin=False)
        if account.account_role == "parent":
            return account
        if organization_id == "platform":
            if account.account_role == "platform_admin":
                return account
            raise AdminError("NOT_FOUND", 404)
        org = self.db.get(OrganizationModel, organization_id)
        if org is None or org.state != "active":
            raise AdminError("NOT_FOUND", 404)
        if account.account_role == "platform_admin":
            return account
        assigned = self.db.scalar(
            select(OrganizationAssignmentModel.assignment_id)
            .where(
                OrganizationAssignmentModel.subject == account.subject,
                OrganizationAssignmentModel.organization_id == organization_id,
                OrganizationAssignmentModel.active.is_(True),
                OrganizationAssignmentModel.role.in_(("school_admin", "teacher")),
            )
            .limit(1)
        )
        if not assigned:
            raise AdminError("NOT_FOUND", 404)
        return account

    def list(self, organization_id, limit, cursor):
        account = self.authorize(organization_id)
        query = (
            select(
                FEEDBACK_THREADS,
                LIBRARY_VERSIONS.c.content_json.label("lesson_content_json"),
                LIBRARY_VERSIONS.c.version_no.label("lesson_version_no"),
            )
            .select_from(
                FEEDBACK_THREADS.outerjoin(
                    LIBRARY_VERSIONS,
                    and_(
                        LIBRARY_VERSIONS.c.version_id == FEEDBACK_THREADS.c.version_id,
                        LIBRARY_VERSIONS.c.lesson_id == FEEDBACK_THREADS.c.lesson_id,
                    ),
                )
            )
            .where(FEEDBACK_THREADS.c.organization_id == organization_id)
        )
        if account.account_role == "parent":
            query = query.where(FEEDBACK_THREADS.c.created_by == account.subject)
        total = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        scope = cursor_scope(
            "organization-feedback",
            organization_id,
            account.subject if account.account_role == "parent" else "",
        )
        query = apply_datetime_cursor(
            query,
            created_at_column=FEEDBACK_THREADS.c.created_at,
            reference_column=FEEDBACK_THREADS.c.thread_id,
            scope=scope,
            cursor=cursor,
            dialect=self.db.get_bind().dialect.name,
        )
        rows = self.db.execute(
            query.order_by(FEEDBACK_THREADS.c.created_at.desc(), FEEDBACK_THREADS.c.thread_id)
            .limit(limit + 1)
        ).mappings().all()
        next_cursor = next_datetime_cursor(
            rows,
            limit,
            scope=scope,
            created_at=lambda item: item["created_at"],
            reference=lambda item: item["thread_id"],
        )
        return {
            "total": total,
            "limit": limit,
            "next_cursor": next_cursor,
            "items": [
                {
                    "thread_id": r["thread_id"],
                    "lesson_id": r["lesson_id"],
                    "version_id": r["version_id"],
                    "lesson_title": self._lesson_title(r.get("lesson_content_json")),
                    "version_no": r.get("lesson_version_no"),
                    "revision": r["revision"],
                    "created_at": r["created_at"].isoformat(),
                }
                for r in rows[:limit]
            ],
        }

    def thread(self, organization_id, ref, lock=False, account=None):
        account = account or self.authorize(organization_id)
        query = select(FEEDBACK_THREADS).where(
            FEEDBACK_THREADS.c.thread_id == ref,
            FEEDBACK_THREADS.c.organization_id == organization_id,
        )
        if account.account_role == "parent":
            query = query.where(FEEDBACK_THREADS.c.created_by == account.subject)
        if lock:
            query = query.with_for_update()
        row = self.db.execute(query).mappings().one_or_none()
        if row is None:
            raise AdminError("NOT_FOUND", 404)
        if account.account_role == "parent":
            if self.parent_lesson is None:
                raise AdminError("LESSON_ACCESS_UNAVAILABLE", 403)
            self.parent_lesson(row["lesson_id"])
        return row

    def detail(self, organization_id, ref, limit=25, cursor=None):
        account = self.authorize(organization_id)
        row = self.thread(organization_id, ref, account=account)
        scope = cursor_scope("organization-feedback-messages", organization_id, ref)
        messages_query = apply_datetime_cursor(
            select(FEEDBACK_MESSAGES).where(FEEDBACK_MESSAGES.c.thread_id == ref),
            created_at_column=FEEDBACK_MESSAGES.c.created_at,
            reference_column=FEEDBACK_MESSAGES.c.message_id,
            scope=scope,
            cursor=cursor,
            descending=False,
            dialect=self.db.get_bind().dialect.name,
        )
        messages = self.db.execute(
            messages_query
            .order_by(FEEDBACK_MESSAGES.c.created_at, FEEDBACK_MESSAGES.c.message_id)
            .limit(limit + 1)
        ).mappings().all()
        next_cursor = next_datetime_cursor(
            messages,
            limit,
            scope=scope,
            created_at=lambda message: message["created_at"],
            reference=lambda message: message["message_id"],
        )
        lesson_version = self.db.execute(
            select(
                LIBRARY_VERSIONS.c.content_json,
                LIBRARY_VERSIONS.c.version_no,
            ).where(
                LIBRARY_VERSIONS.c.lesson_id == row["lesson_id"],
                LIBRARY_VERSIONS.c.version_id == row["version_id"],
            )
        ).mappings().one_or_none()
        authors = self._message_authors(
            messages[:limit], include_display_names=account.account_role != "parent"
        )
        return {
            "thread_id": ref,
            "organization_id": organization_id,
            "lesson_id": row["lesson_id"],
            "version_id": row["version_id"],
            "lesson_title": self._lesson_title(
                lesson_version["content_json"] if lesson_version is not None else None
            ),
            "version_no": lesson_version["version_no"] if lesson_version is not None else None,
            "revision": row["revision"],
            "limit": limit,
            "next_cursor": next_cursor,
            "items": [
                {
                    "message_id": m["message_id"],
                    "body": m["body"],
                    "from_you": m["actor_ref"] == self.admin.principal.subject,
                    "author_role": authors.get(m["actor_ref"], ("other", None))[0],
                    "author_display_name": authors.get(m["actor_ref"], ("other", None))[1],
                    "created_at": m["created_at"].isoformat(),
                }
                for m in messages[:limit]
            ],
        }

    @staticmethod
    def _lesson_title(content: Any) -> str | None:
        if not isinstance(content, dict):
            return None
        title = content.get("title")
        return title.strip() if isinstance(title, str) and title.strip() else None

    def _message_authors(
        self, messages: list[Any], *, include_display_names: bool
    ) -> dict[str, tuple[str, str | None]]:
        subjects = list(dict.fromkeys(message["actor_ref"] for message in messages))
        if not subjects:
            return {}
        rows = self.db.execute(
            select(AdultIdentityModel.subject, AdultIdentityModel.account_role).where(
                AdultIdentityModel.subject.in_(subjects)
            )
        ).all()
        roles = {
            row.subject: row.account_role
            if row.account_role in {"parent", "teacher", "school_manager", "platform_admin"}
            else "other"
            for row in rows
        }
        profiles = (
            account_profiles(self.identity_provisioner, subjects)
            if include_display_names
            else {}
        )
        return {
            subject: (
                roles.get(subject, "other"),
                safe_display_name(
                    profiles[subject].display_name if subject in profiles else None,
                    subject=subject,
                ),
            )
            for subject in subjects
        }

    def create(self, organization_id, lesson_id, body, key):
        account = self.authorize(organization_id)
        if account.account_role != "parent" or self.parent_lesson is None:
            raise AdminError("PARENT_REQUIRED", 403)
        lesson = (
            self.db.execute(
                select(LIBRARY_ITEMS).where(
                    LIBRARY_ITEMS.c.lesson_id == lesson_id,
                    LIBRARY_ITEMS.c.organization_id == organization_id,
                )
            )
            .mappings()
            .one_or_none()
        )
        if lesson is None:
            raise AdminError("NOT_FOUND", 404)
        accessible = self.parent_lesson(lesson_id)

        def execute():
            ref = str(uuid4())
            self.db.execute(
                FEEDBACK_THREADS.insert().values(
                    thread_id=ref,
                    organization_id=organization_id,
                    lesson_id=lesson_id,
                    version_id=accessible["version_id"],
                    created_by=account.subject,
                    revision=1,
                )
            )
            self.add_message(ref, body)
            self.admin.audit("LESSON_FEEDBACK_CREATED", "lesson_feedback", ref, organization_id)
            self.admin.notify(lesson["created_by"], "LESSON_FEEDBACK_CREATED", ref)
            return {"thread_id": ref, "revision": 1}

        return self.admin.command(
            "feedback.create:" + lesson_id,
            key,
            {"body": body, "organization_id": organization_id},
            execute,
        )

    def add_message(self, ref, body):
        self.db.execute(
            FEEDBACK_MESSAGES.insert().values(
                message_id=str(uuid4()),
                thread_id=ref,
                actor_ref=self.admin.principal.subject,
                body=body,
            )
        )

    def reply(self, organization_id, ref, body, expected, key):
        self.authorize(organization_id)

        def execute():
            row = self.thread(organization_id, ref, lock=True)
            require_revision(row["revision"], expected)
            self.add_message(ref, body)
            self.db.execute(
                FEEDBACK_THREADS.update()
                .where(FEEDBACK_THREADS.c.thread_id == ref)
                .values(revision=expected + 1)
            )
            self.admin.audit("LESSON_FEEDBACK_REPLIED", "lesson_feedback", ref, organization_id)
            if row["created_by"] != self.admin.principal.subject:
                self.admin.notify(row["created_by"], "LESSON_FEEDBACK_REPLIED", ref)
            return {"thread_id": ref, "revision": expected + 1}

        return self.admin.command(
            "feedback.reply:" + ref,
            key,
            {"body": body, "organization_id": organization_id, "revision": expected},
            execute,
        )


class ParentLessonFeedbackService(LessonFeedbackService):
    """Parent-scoped feedback keyed by lesson, with BE1 command receipts."""

    _OPERATION_PREFIX = "POST /lesson-library/v1/me/lessons/feedback:"

    @classmethod
    def operation_scope(cls, lesson_id: str) -> str:
        lesson_hash = hashlib.sha256(lesson_id.encode("utf-8")).hexdigest()
        return cls._OPERATION_PREFIX + lesson_hash

    @staticmethod
    def command_fingerprint(lesson_id: str, feedback_text: str) -> str:
        canonical = json.dumps(
            {"lesson_id": lesson_id, "feedback_text": feedback_text},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

    def submit(self, lesson_id: str, feedback_text: str, idempotency_key: str) -> dict[str, Any]:
        body = feedback_text.strip()
        if not 1 <= len(body) <= 1200:
            fail(
                400,
                "INVALID_REQUEST",
                "feedback_text must contain 1–1200 characters",
                field_errors=[{"field": "feedback_text", "code": "INVALID_LENGTH"}],
            )
        if not 1 <= len(idempotency_key) <= 128 or any(
            ord(char) < 33 or ord(char) > 126 for char in idempotency_key
        ):
            fail(
                400,
                "INVALID_REQUEST",
                "Idempotency-Key must contain 1–128 visible ASCII characters",
                field_errors=[{"field": "Idempotency-Key", "code": "INVALID_FORMAT"}],
            )

        subject = self.admin.principal.subject
        scope = self.operation_scope(lesson_id)
        fingerprint = self.command_fingerprint(lesson_id, body)
        try:
            item, version_id = self._authorize_lesson(lesson_id)
            organization_id = self._organization_scope(item)
            self._lock_parent_lesson(subject, lesson_id)
            receipt = self._load_receipt(subject, scope, idempotency_key)
            if receipt is not None:
                try:
                    response = self._rebuild_receipt(
                        receipt,
                        subject=subject,
                        lesson_id=lesson_id,
                        organization_id=organization_id,
                        fingerprint=fingerprint,
                    )
                except LessonLibraryError:
                    # Release the per-parent advisory lock held by this transaction.
                    self.db.rollback()
                    raise
                self.db.commit()
                return response

            thread = self._latest_thread(subject, lesson_id, lock=True)
            if thread is None:
                thread_id = str(uuid4())
                revision = 1
                action = "LESSON_FEEDBACK_CREATED"
                self.db.execute(
                    FEEDBACK_THREADS.insert().values(
                        thread_id=thread_id,
                        organization_id=organization_id,
                        lesson_id=lesson_id,
                        version_id=version_id,
                        created_by=subject,
                        revision=revision,
                    )
                )
            else:
                thread_id = thread["thread_id"]
                revision = thread["revision"] + 1
                action = "LESSON_FEEDBACK_FOLLOW_UP"
                self.db.execute(
                    FEEDBACK_THREADS.update()
                    .where(FEEDBACK_THREADS.c.thread_id == thread_id)
                    .values(revision=revision)
                )

            message_id = str(uuid4())
            self.db.execute(
                FEEDBACK_MESSAGES.insert().values(
                    message_id=message_id,
                    thread_id=thread_id,
                    actor_ref=subject,
                    body=body,
                )
            )
            self.admin.audit(action, "lesson_feedback", thread_id, organization_id)
            self.admin.notify(item["created_by"], "LESSON_FEEDBACK_CREATED", thread_id)
            thread_row = self._thread_by_id(thread_id)
            message_row = self._message_by_id(message_id, thread_id, subject)
            response = self._feedback_response(thread_row, message_row, revision=revision)
            self.db.add(
                Be1CommandReceiptModel(
                    principal_ref=subject,
                    operation_scope=scope,
                    idempotency_key=idempotency_key,
                    organization_id=organization_id,
                    request_fingerprint=fingerprint,
                    response_json=LessonLibraryService._json_safe(
                        {
                            "feedback_id": thread_id,
                            "message_id": message_id,
                            "revision": revision,
                        }
                    ),
                )
            )
            self.db.commit()
            return response
        except IntegrityError as exc:
            self.db.rollback()
            if LessonLibraryService._is_remix_receipt_conflict(exc):
                return self._replay_after_receipt_race(
                    subject=subject,
                    lesson_id=lesson_id,
                    idempotency_key=idempotency_key,
                    fingerprint=fingerprint,
                )
            fail(409, "RESOURCE_CONFLICT", "The request conflicts with existing records")
        except SQLAlchemyError:
            self.db.rollback()
            fail(503, "DEPENDENCY_UNAVAILABLE", "Database is temporarily unavailable")

    def state(self, lesson_id: str) -> dict[str, Any]:
        subject = self.admin.principal.subject
        try:
            self._authorize_lesson(lesson_id)
            thread = self._latest_thread(subject, lesson_id)
            if thread is None:
                return {
                    "contract": "ParentLessonFeedbackStateV1",
                    "lesson_id": lesson_id,
                    "feedback": None,
                }
            message = self.db.execute(
                select(FEEDBACK_MESSAGES)
                .where(
                    FEEDBACK_MESSAGES.c.thread_id == thread["thread_id"],
                    FEEDBACK_MESSAGES.c.actor_ref == subject,
                )
                .order_by(
                    FEEDBACK_MESSAGES.c.created_at.desc(),
                    FEEDBACK_MESSAGES.c.message_id.desc(),
                )
                .limit(1)
            ).mappings().one_or_none()
            if message is None:
                fail(503, "DEPENDENCY_UNAVAILABLE", "Feedback history is temporarily unavailable")
            return {
                "contract": "ParentLessonFeedbackStateV1",
                "lesson_id": lesson_id,
                "feedback": self._feedback_response(thread, message),
            }
        except SQLAlchemyError:
            self.db.rollback()
            fail(503, "DEPENDENCY_UNAVAILABLE", "Database is temporarily unavailable")

    def replies(self, lesson_id: str, limit: int = 25, cursor: str | None = None) -> dict[str, Any]:
        subject = self.admin.principal.subject
        try:
            self._authorize_lesson(lesson_id)
            scope = cursor_scope("parent-lesson-feedback-replies", subject, lesson_id)
            query = apply_datetime_cursor(
                select(FEEDBACK_MESSAGES),
                created_at_column=FEEDBACK_MESSAGES.c.created_at,
                reference_column=FEEDBACK_MESSAGES.c.message_id,
                scope=scope,
                cursor=cursor,
                descending=False,
                dialect=self.db.get_bind().dialect.name,
            )
            thread = self._latest_thread(subject, lesson_id)
            if thread is None:
                return {
                    "contract": "ParentLessonFeedbackReplyPageV1",
                    "feedback_id": None,
                    "items": [],
                    "next_cursor": None,
                }
            query = query.where(
                FEEDBACK_MESSAGES.c.thread_id == thread["thread_id"],
                FEEDBACK_MESSAGES.c.actor_ref != thread["created_by"],
            )
            rows = self.db.execute(
                query.order_by(
                    FEEDBACK_MESSAGES.c.created_at,
                    FEEDBACK_MESSAGES.c.message_id,
                ).limit(limit + 1)
            ).mappings().all()
            next_cursor = next_datetime_cursor(
                rows,
                limit,
                scope=scope,
                created_at=lambda row: row["created_at"],
                reference=lambda row: row["message_id"],
            )
            return {
                "contract": "ParentLessonFeedbackReplyPageV1",
                "feedback_id": thread["thread_id"],
                "items": [
                    {
                        "reply_id": row["message_id"],
                        "reply_text": row["body"],
                        "created_at": row["created_at"],
                    }
                    for row in rows[:limit]
                ],
                "next_cursor": next_cursor,
            }
        except AdminError as exc:
            if exc.code == "INVALID_CURSOR":
                fail(
                    400,
                    "INVALID_REQUEST",
                    "cursor must be valid for this feedback page",
                    field_errors=[{"field": "cursor", "code": "INVALID_FORMAT"}],
                )
            raise
        except SQLAlchemyError:
            self.db.rollback()
            fail(503, "DEPENDENCY_UNAVAILABLE", "Database is temporarily unavailable")

    def _authorize_lesson(self, lesson_id: str) -> tuple[Any, str]:
        if self.parent_lesson is None:
            fail(404, "LESSON_NOT_FOUND", "Lesson was not found")
        accessible = self.parent_lesson(lesson_id)
        version_id = accessible.get("version_id") if isinstance(accessible, dict) else None
        if not version_id:
            fail(404, "LESSON_NOT_FOUND", "Lesson was not found")
        item = self.db.execute(
            select(LIBRARY_ITEMS).where(LIBRARY_ITEMS.c.lesson_id == lesson_id)
        ).mappings().one_or_none()
        if item is None:
            fail(404, "LESSON_NOT_FOUND", "Lesson was not found")
        return item, version_id

    @staticmethod
    def _organization_scope(item: Any) -> str:
        organization_id = item["organization_id"]
        return organization_id if organization_id is not None else "platform"

    def _lock_parent_lesson(self, subject: str, lesson_id: str) -> None:
        if self.db.get_bind().dialect.name == "postgresql":
            self.db.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:lock_key, 0))"),
                {"lock_key": f"lesson-feedback:{subject}:{lesson_id}"},
            )

    def _latest_thread(self, subject: str, lesson_id: str, *, lock: bool = False) -> Any:
        query = select(FEEDBACK_THREADS).where(
            FEEDBACK_THREADS.c.created_by == subject,
            FEEDBACK_THREADS.c.lesson_id == lesson_id,
        )
        if lock:
            query = query.with_for_update()
        return self.db.execute(
            query.order_by(
                FEEDBACK_THREADS.c.created_at.desc(),
                FEEDBACK_THREADS.c.thread_id.desc(),
            ).limit(1)
        ).mappings().one_or_none()

    def _load_receipt(self, subject: str, scope: str, key: str) -> Any:
        return self.db.scalar(
            select(Be1CommandReceiptModel).where(
                Be1CommandReceiptModel.principal_ref == subject,
                Be1CommandReceiptModel.operation_scope == scope,
                Be1CommandReceiptModel.idempotency_key == key,
            )
        )

    def _rebuild_receipt(
        self,
        receipt: Be1CommandReceiptModel,
        *,
        subject: str,
        lesson_id: str,
        organization_id: str,
        fingerprint: str,
    ) -> dict[str, Any]:
        stored = LessonLibraryService._remix_receipt_response(
            receipt,
            organization_id=organization_id,
            fingerprint=fingerprint,
        )
        try:
            feedback_id = str(stored["feedback_id"])
            message_id = str(stored["message_id"])
            revision = int(stored["revision"])
        except (KeyError, TypeError, ValueError):
            fail(503, "DEPENDENCY_UNAVAILABLE", "Feedback receipt is temporarily unavailable")
        thread = self.db.execute(
            select(FEEDBACK_THREADS).where(
                FEEDBACK_THREADS.c.thread_id == feedback_id,
                FEEDBACK_THREADS.c.lesson_id == lesson_id,
                FEEDBACK_THREADS.c.created_by == subject,
                FEEDBACK_THREADS.c.organization_id == organization_id,
            )
        ).mappings().one_or_none()
        message = self._message_by_id(message_id, feedback_id, subject)
        if thread is None or message is None:
            fail(503, "DEPENDENCY_UNAVAILABLE", "Feedback receipt is temporarily unavailable")
        return self._feedback_response(thread, message, revision=revision)

    def _replay_after_receipt_race(
        self,
        *,
        subject: str,
        lesson_id: str,
        idempotency_key: str,
        fingerprint: str,
    ) -> dict[str, Any]:
        try:
            item, _version_id = self._authorize_lesson(lesson_id)
            organization_id = self._organization_scope(item)
            receipt = self._load_receipt(
                subject,
                self.operation_scope(lesson_id),
                idempotency_key,
            )
            if receipt is None:
                fail(503, "DEPENDENCY_UNAVAILABLE", "Feedback receipt is temporarily unavailable")
            response = self._rebuild_receipt(
                receipt,
                subject=subject,
                lesson_id=lesson_id,
                organization_id=organization_id,
                fingerprint=fingerprint,
            )
            self.db.commit()
            return response
        except SQLAlchemyError:
            self.db.rollback()
            fail(503, "DEPENDENCY_UNAVAILABLE", "Database is temporarily unavailable")

    def _thread_by_id(self, thread_id: str) -> Any:
        row = self.db.execute(
            select(FEEDBACK_THREADS).where(FEEDBACK_THREADS.c.thread_id == thread_id)
        ).mappings().one_or_none()
        if row is None:
            fail(503, "DEPENDENCY_UNAVAILABLE", "Feedback history is temporarily unavailable")
        return row

    def _message_by_id(self, message_id: str, thread_id: str, subject: str) -> Any:
        return self.db.execute(
            select(FEEDBACK_MESSAGES).where(
                FEEDBACK_MESSAGES.c.message_id == message_id,
                FEEDBACK_MESSAGES.c.thread_id == thread_id,
                FEEDBACK_MESSAGES.c.actor_ref == subject,
            )
        ).mappings().one_or_none()

    def _reply_count(self, thread_id: str, created_by: str) -> int:
        return int(
            self.db.scalar(
                select(func.count()).select_from(FEEDBACK_MESSAGES).where(
                    FEEDBACK_MESSAGES.c.thread_id == thread_id,
                    FEEDBACK_MESSAGES.c.actor_ref != created_by,
                )
            )
            or 0
        )

    def _feedback_response(
        self,
        thread: Any,
        message: Any,
        *,
        revision: int | None = None,
    ) -> dict[str, Any]:
        return {
            "contract": "ParentLessonFeedbackV1",
            "feedback_id": thread["thread_id"],
            "lesson_id": thread["lesson_id"],
            "version_id": thread["version_id"],
            "revision": thread["revision"] if revision is None else revision,
            "feedback_text": message["body"],
            "created_at": thread["created_at"],
            "updated_at": message["created_at"],
            "reply_count": self._reply_count(thread["thread_id"], thread["created_by"]),
        }
