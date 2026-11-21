"""Version-pinned lesson feedback with server-side organization authorization."""

from uuid import uuid4

from sqlalchemy import func, select

from sketch2life.domain.platform_admin import AdminError, require_revision
from sketch2life.infrastructure.lesson_library.feedback_tables import (
    FEEDBACK_MESSAGES,
    FEEDBACK_THREADS,
)
from sketch2life.infrastructure.lesson_library.tables import LIBRARY_ITEMS
from sketch2life.infrastructure.persistence.be1_models import (
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.infrastructure.platform_admin.pagination import (
    apply_datetime_cursor,
    cursor_scope,
    next_datetime_cursor,
)


class LessonFeedbackService:
    def __init__(self, admin, parent_lesson=None):
        self.admin, self.db, self.parent_lesson = admin, admin.db, parent_lesson

    def authorize(self, organization_id):
        account = self.admin.identity(admin=False)
        if account.account_role == "parent":
            return account
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
        query = select(FEEDBACK_THREADS).where(
            FEEDBACK_THREADS.c.organization_id == organization_id
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
                    "revision": r["revision"],
                    "created_at": r["created_at"].isoformat(),
                }
                for r in rows[:limit]
            ],
        }

    def thread(self, organization_id, ref, lock=False):
        account = self.authorize(organization_id)
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
        row = self.thread(organization_id, ref)
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
        return {
            "thread_id": ref,
            "organization_id": organization_id,
            "lesson_id": row["lesson_id"],
            "version_id": row["version_id"],
            "revision": row["revision"],
            "limit": limit,
            "next_cursor": next_cursor,
            "items": [
                {
                    "message_id": m["message_id"],
                    "body": m["body"],
                    "from_you": m["actor_ref"] == self.admin.principal.subject,
                    "created_at": m["created_at"].isoformat(),
                }
                for m in messages[:limit]
            ],
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
