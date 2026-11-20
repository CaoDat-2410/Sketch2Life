"""Platform authoring and independent review over the canonical Lesson tables."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import func, or_, select

from sketch2life.domain.lesson_library.model import canonical_content_hash, validate_content
from sketch2life.domain.platform_admin import AdminError, independent_reviewer, require_revision
from sketch2life.infrastructure.lesson_library.publication_tables import PUBLICATION_REVIEWS
from sketch2life.infrastructure.lesson_library.tables import (
    ACCESS_GRANTS,
    LIBRARY_ITEMS,
    LIBRARY_VERSIONS,
    VERSION_ACTIVITIES,
)
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.infrastructure.persistence.platform_models import PermissionGrantModel
from sketch2life.infrastructure.platform_admin.pagination import (
    apply_datetime_cursor,
    cursor_scope,
    next_datetime_cursor,
)


class PlatformLessonService:
    def __init__(self, admin):
        self.admin, self.db = admin, admin.db

    def item(self, lesson_id, lock=False):
        query = select(LIBRARY_ITEMS).where(
            LIBRARY_ITEMS.c.lesson_id == lesson_id, LIBRARY_ITEMS.c.owner_kind == "PLATFORM"
        )
        if lock:
            query = query.with_for_update()
        row = self.db.execute(query).mappings().one_or_none()
        if row is None:
            raise AdminError("NOT_FOUND", 404)
        return row

    def version(self, version_id):
        row = (
            self.db.execute(
                select(LIBRARY_VERSIONS).where(LIBRARY_VERSIONS.c.version_id == version_id)
            )
            .mappings()
            .one()
        )
        return row

    def detail(self, lesson_id):
        identity = self.admin.identity()
        item = self.item(lesson_id)
        version = self.version(item["current_version_id"])
        now = datetime.now(UTC)
        is_published_version = self.db.scalar(
            select(ACCESS_GRANTS.c.access_grant_id)
            .where(
                ACCESS_GRANTS.c.lesson_id == lesson_id,
                ACCESS_GRANTS.c.version_id == version["version_id"],
                ACCESS_GRANTS.c.audience_kind == "PUBLIC",
                ACCESS_GRANTS.c.capability == "VIEW",
                ACCESS_GRANTS.c.state == "ACTIVE",
                or_(
                    ACCESS_GRANTS.c.expires_at.is_(None),
                    ACCESS_GRANTS.c.expires_at > now,
                ),
            )
            .limit(1)
        ) is not None
        content = dict(version["content_json"])
        content["activities"] = list(
            self.db.scalars(
                select(VERSION_ACTIVITIES.c.activity_json)
                .where(VERSION_ACTIVITIES.c.version_id == version["version_id"])
                .order_by(VERSION_ACTIVITIES.c.activity_order)
            )
        )
        return {
            "lesson_id": lesson_id,
            "is_author": version["authored_by"] == identity.subject,
            "reviews": [
                {"review_id": r["review_id"], "decision": r["decision"], "reason": r["reason"]}
                for r in self.db.execute(
                    select(PUBLICATION_REVIEWS)
                    .where(
                        PUBLICATION_REVIEWS.c.lesson_id == lesson_id,
                        PUBLICATION_REVIEWS.c.version_id == version["version_id"],
                    )
                    .order_by(
                        PUBLICATION_REVIEWS.c.created_at.desc(), PUBLICATION_REVIEWS.c.review_id
                    )
                ).mappings()
            ],
            "revision": item["revision"],
            "version_id": version["version_id"],
            "version_no": version["version_no"],
            "content_hash": version["structured_content_hash"],
            "review_state": version["review_state"],
            "visibility": item["visibility"],
            "moderation_state": item["moderation_state"],
            "is_published_version": is_published_version,
            "content": content,
        }

    def list(self, state, limit, cursor):
        self.admin.identity()
        query = (
            select(LIBRARY_ITEMS.c.lesson_id)
            .join(
                LIBRARY_VERSIONS,
                LIBRARY_ITEMS.c.current_version_id == LIBRARY_VERSIONS.c.version_id,
            )
            .where(LIBRARY_ITEMS.c.owner_kind == "PLATFORM")
        )
        if state:
            query = query.where(LIBRARY_VERSIONS.c.review_state == state)
        total = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        scope = cursor_scope("platform-lessons", state or "")
        query = apply_datetime_cursor(
            query,
            created_at_column=LIBRARY_ITEMS.c.updated_at,
            reference_column=LIBRARY_ITEMS.c.lesson_id,
            scope=scope,
            cursor=cursor,
            dialect=self.db.get_bind().dialect.name,
        )
        rows = self.db.execute(
            query.with_only_columns(LIBRARY_ITEMS.c.lesson_id, LIBRARY_ITEMS.c.updated_at)
            .order_by(LIBRARY_ITEMS.c.updated_at.desc(), LIBRARY_ITEMS.c.lesson_id)
            .limit(limit + 1)
        ).all()
        next_cursor = next_datetime_cursor(
            rows,
            limit,
            scope=scope,
            created_at=lambda row: row.updated_at,
            reference=lambda row: row.lesson_id,
        )
        return {
            "items": [self.detail(row.lesson_id) for row in rows[:limit]],
            "total": total,
            "limit": limit,
            "next_cursor": next_cursor,
        }

    def store_version(self, lesson_id, content, number):
        validate_content(content)
        ref = str(uuid4())
        self.db.execute(
            LIBRARY_VERSIONS.insert().values(
                version_id=ref,
                lesson_id=lesson_id,
                version_no=number,
                content_json={k: v for k, v in content.items() if k != "activities"},
                structured_content_hash=canonical_content_hash(content),
                review_state="DRAFT",
                authored_by=self.admin.principal.subject,
                created_at=datetime.now(UTC),
            )
        )
        for index, activity in enumerate(content["activities"], 1):
            self.db.execute(
                VERSION_ACTIVITIES.insert().values(
                    activity_id=str(uuid4()),
                    version_id=ref,
                    activity_order=index,
                    activity_json=activity,
                )
            )
        return ref

    def write(self, content, key, lesson_id=None, expected_revision=None):
        identity = self.admin.identity()

        def execute():
            ref = lesson_id or str(uuid4())
            number, revision = 1, 1
            if lesson_id:
                item = self.item(ref, lock=True)
                require_revision(item["revision"], expected_revision)
                if item["created_by"] != identity.subject:
                    raise AdminError("AUTHOR_REQUIRED", 403)
                number = (
                    int(
                        self.db.scalar(
                            select(func.max(LIBRARY_VERSIONS.c.version_no)).where(
                                LIBRARY_VERSIONS.c.lesson_id == ref
                            )
                        )
                    )
                    + 1
                )
                revision = item["revision"] + 1
            else:
                self.db.execute(
                    LIBRARY_ITEMS.insert().values(
                        lesson_id=ref,
                        organization_id=None,
                        owner_kind="PLATFORM",
                        created_by=identity.subject,
                        state="ACTIVE",
                        visibility="PRIVATE",
                        internal_visibility="PRIVATE",
                        moderation_state="VISIBLE",
                        revision=1,
                    )
                )
            version_id = self.store_version(ref, content, number)
            self.db.execute(
                LIBRARY_ITEMS.update()
                .where(LIBRARY_ITEMS.c.lesson_id == ref)
                .values(
                    current_version_id=version_id, revision=revision, updated_at=datetime.now(UTC)
                )
            )
            self.admin.audit("PLATFORM_LESSON_VERSION_CREATED", "platform_lesson", ref)
            return self.detail(ref)

        return self.admin.command(
            "lesson.write:" + (lesson_id or "new"),
            key,
            {"content": content, "expected_revision": expected_revision},
            execute,
        )

    def action(self, lesson_id, payload, expected_revision, key):
        action = payload["action"]
        identity = self.admin.identity(
            content=action in {"approve", "request_changes", "publish", "hide", "unpublish"}
        )

        def execute():
            item = self.item(lesson_id, lock=True)
            require_revision(item["revision"], expected_revision)
            version = self.version(item["current_version_id"])
            if (version["version_id"], version["structured_content_hash"]) != (
                payload["version_id"],
                payload["content_hash"],
            ):
                raise AdminError("CONTENT_HASH_MISMATCH")
            now = datetime.now(UTC)
            state = version["review_state"]
            changes = {"revision": item["revision"] + 1, "updated_at": now}
            result = {}
            if action == "submit":
                if item["created_by"] != identity.subject:
                    raise AdminError("AUTHOR_REQUIRED", 403)
                if state not in {"DRAFT", "CHANGES_REQUESTED"}:
                    raise AdminError("INVALID_STATE_TRANSITION")
                self.db.execute(
                    LIBRARY_VERSIONS.update()
                    .where(LIBRARY_VERSIONS.c.version_id == version["version_id"])
                    .values(review_state="PENDING_REVIEW")
                )
            elif action in {"approve", "request_changes"}:
                independent_reviewer(version["authored_by"], identity.subject)
                if state != "PENDING_REVIEW":
                    raise AdminError("INVALID_STATE_TRANSITION")
                if action == "request_changes" and not payload.get("reason"):
                    raise AdminError("REASON_REQUIRED", 422)
                grant = self.db.get(PermissionGrantModel, (identity.subject, "content_admin"))
                review_id = str(uuid4())
                self.db.execute(
                    PUBLICATION_REVIEWS.insert().values(
                        review_id=review_id,
                        lesson_id=lesson_id,
                        version_id=version["version_id"],
                        content_hash=version["structured_content_hash"],
                        reviewer_ref=identity.subject,
                        permission_revision=grant.revision,
                        decision="APPROVE" if action == "approve" else "REQUEST_CHANGES",
                        reason=payload.get("reason"),
                    )
                )
                self.db.execute(
                    LIBRARY_VERSIONS.update()
                    .where(LIBRARY_VERSIONS.c.version_id == version["version_id"])
                    .values(review_state="APPROVED" if action == "approve" else "CHANGES_REQUESTED")
                )
                self.admin.notify(item["created_by"], "LESSON_REVIEWED", lesson_id)
                result["review_id"] = review_id
            elif action == "publish":
                independent_reviewer(version["authored_by"], identity.subject)
                if item["moderation_state"] == "HIDDEN":
                    raise AdminError("LESSON_RESTORE_REQUIRED")
                review = (
                    self.db.execute(
                        select(PUBLICATION_REVIEWS).where(
                            PUBLICATION_REVIEWS.c.review_id == payload.get("review_id")
                        )
                    )
                    .mappings()
                    .one_or_none()
                )
                if (
                    review is None
                    or state != "APPROVED"
                    or review["decision"] != "APPROVE"
                    or (review["lesson_id"], review["version_id"], review["content_hash"])
                    != (lesson_id, version["version_id"], version["structured_content_hash"])
                ):
                    raise AdminError("EXACT_REVIEW_REQUIRED")
                reviewer = self.db.get(AdultIdentityModel, review["reviewer_ref"])
                grant = self.db.get(PermissionGrantModel, (review["reviewer_ref"], "content_admin"))
                if (
                    reviewer is None
                    or reviewer.state != "active"
                    or reviewer.account_role != "platform_admin"
                    or grant is None
                    or not grant.active
                    or grant.revision != review["permission_revision"]
                ):
                    raise AdminError("REVIEW_PERMISSION_REVOKED", 403)
                self.revoke_public(lesson_id, now)
                for capability in ("VIEW", "DOWNLOAD", "REUSE"):
                    self.db.execute(
                        ACCESS_GRANTS.insert().values(
                            access_grant_id=str(uuid4()),
                            lesson_id=lesson_id,
                            version_id=version["version_id"],
                            organization_id="platform",
                            audience_kind="PUBLIC",
                            audience_ref=None,
                            capability=capability,
                            state="ACTIVE",
                            granted_by=item["created_by"],
                            approved_by=identity.subject,
                            approved_at=now,
                            revision=1,
                        )
                    )
                changes.update(visibility="PUBLIC", moderation_state="VISIBLE")
            elif action in {"hide", "unpublish"}:
                if not payload.get("reason"):
                    raise AdminError("REASON_REQUIRED", 422)
                self.revoke_public(lesson_id, now)
                changes.update(
                    visibility="PRIVATE",
                    moderation_state="HIDDEN" if action == "hide" else "VISIBLE",
                    moderation_reason=payload["reason"],
                    moderated_by=identity.subject,
                    moderated_at=now,
                )
            self.db.execute(
                LIBRARY_ITEMS.update()
                .where(LIBRARY_ITEMS.c.lesson_id == lesson_id)
                .values(**changes)
            )
            self.admin.audit("PLATFORM_LESSON_" + action.upper(), "platform_lesson", lesson_id)
            return {**self.detail(lesson_id), **result}

        return self.admin.command(
            "lesson.action:" + lesson_id,
            key,
            {**payload, "expected_revision": expected_revision},
            execute,
        )

    def revoke_public(self, lesson_id, now):
        self.db.execute(
            ACCESS_GRANTS.update()
            .where(
                ACCESS_GRANTS.c.lesson_id == lesson_id,
                ACCESS_GRANTS.c.audience_kind == "PUBLIC",
                ACCESS_GRANTS.c.state == "ACTIVE",
            )
            .values(state="REVOKED", revoked_at=now, revision=ACCESS_GRANTS.c.revision + 1)
        )
