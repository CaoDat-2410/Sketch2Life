"""Admin adapter for the existing immutable Learning Content lifecycle/store."""

import json
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import func, select

from sketch2life.application.ports.learning_content import ContentEvent
from sketch2life.domain.learning_content import model as domain
from sketch2life.domain.platform_admin import AdminError
from sketch2life.infrastructure.learning_content.sql import SqlContentTransaction
from sketch2life.infrastructure.learning_content.tables import RECORD, REVIEW, VERSION
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.infrastructure.persistence.platform_models import PermissionGrantModel
from sketch2life.infrastructure.platform_admin.pagination import (
    apply_datetime_cursor,
    cursor_scope,
    next_datetime_cursor,
)

SCOPE = "platform"
POLICY = "admin-catalog-review-v1"
AUDIENCE_HASH = domain.content_hash(domain.canonical_json({"scope": "PUBLIC"}))


class AdminCatalogService:
    def __init__(self, admin):
        self.admin, self.db = admin, admin.db

    def transaction(self):
        return SqlContentTransaction(self.db.connection())

    def authority(self, reviewing=False):
        row = self.admin.identity(content=reviewing)
        capabilities = (
            frozenset(domain.Capability)
            if reviewing
            else frozenset({domain.Capability.AUTHOR, domain.Capability.READ})
        )
        return domain.Authority(row.subject, SCOPE, capabilities)

    def load(self, ref, lock=False, version=None):
        content = self.transaction().load(SCOPE, ref, for_update=lock, version=version)
        if content is None:
            raise AdminError("NOT_FOUND", 404)
        return content

    def view(self, content):
        return {
            "is_author": content.authored_by == self.admin.principal.subject,
            "record_id": content.record_id,
            "version": content.version,
            "revision": content.revision,
            "content_hash": content.hash,
            "state": content.state.value,
            "content": json.loads(content.body_json),
            "reviews": [
                {"review_id": r.review_id, "dimension": r.dimension, "decision": r.decision}
                for r in content.reviews
            ],
        }

    def detail(self, ref):
        self.authority()
        return self.view(self.load(ref))

    def list(self, state, limit, cursor):
        self.authority()
        query = (
            select(RECORD.c.record_id)
            .join(
                VERSION,
                (RECORD.c.organization_id == VERSION.c.organization_id)
                & (RECORD.c.record_id == VERSION.c.record_id)
                & (RECORD.c.current_version == VERSION.c.version),
            )
            .where(RECORD.c.organization_id == SCOPE)
        )
        if state:
            query = query.where(VERSION.c.state == state)
        total = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        scope = cursor_scope("platform-catalog", state or "")
        query = apply_datetime_cursor(
            query,
            created_at_column=VERSION.c.created_at,
            reference_column=RECORD.c.record_id,
            scope=scope,
            cursor=cursor,
            dialect=self.db.get_bind().dialect.name,
        )
        rows = self.db.execute(
            query.with_only_columns(RECORD.c.record_id, VERSION.c.created_at)
            .order_by(VERSION.c.created_at.desc(), RECORD.c.record_id)
            .limit(limit + 1)
        ).all()
        next_cursor = next_datetime_cursor(
            rows,
            limit,
            scope=scope,
            created_at=lambda row: row.created_at,
            reference=lambda row: row.record_id,
        )
        return {
            "items": [self.detail(row.record_id) for row in rows[:limit]],
            "total": total,
            "limit": limit,
            "next_cursor": next_cursor,
        }

    def write(self, payload, key, ref=None, expected=None):
        actor = self.authority()

        def execute():
            now = datetime.now(UTC)
            if ref:
                old = self.load(ref, lock=True)
                if old.authored_by != actor.principal_id:
                    raise AdminError("AUTHOR_REQUIRED", 403)
                content = domain.edit(
                    old,
                    actor,
                    payload,
                    now,
                    expected_revision=expected,
                    next_version=old.version + 1,
                )
            else:
                content = domain.create(str(uuid4()), actor, payload, now)
            self.transaction().save(
                content,
                expected_revision=expected,
                event=ContentEvent(
                    str(uuid4()), "catalog.version.created", actor.principal_id, now
                ),
            )
            self.admin.audit("CATALOG_VERSION_CREATED", "catalog", content.record_id)
            return self.view(content)

        return self.command(
            "catalog.write:" + (ref or "new"),
            key,
            {**payload, "expected_revision": expected},
            execute,
        )

    def command(self, operation, key, payload, execute):
        try:
            return self.admin.command(operation, key, payload, execute)
        except domain.ContentError as exc:
            code = str(exc)
            raise AdminError(
                code, 403 if "FORBIDDEN" in code or "SEPARATION" in code else 409
            ) from None

    def action(self, ref, payload, expected, key):
        action = payload["action"]
        actor = self.authority(reviewing=action != "submit")

        def execute():
            content = self.load(ref, lock=True, version=payload["version"])
            if (content.version, content.hash) != (payload["version"], payload["content_hash"]):
                raise AdminError("CONTENT_HASH_MISMATCH")
            now = datetime.now(UTC)
            proof = None
            if action == "submit":
                if content.authored_by != actor.principal_id:
                    raise AdminError("AUTHOR_REQUIRED", 403)
                updated = domain.submit(content, actor, expected_revision=expected)
            elif action == "review":
                if not payload.get("dimension") or not payload.get("decision"):
                    raise AdminError("REVIEW_DIMENSION_REQUIRED", 422)
                proof = domain.ReviewProof(
                    str(uuid4()),
                    payload["dimension"],
                    payload["decision"],
                    content.record_id,
                    content.version,
                    content.hash,
                    content.context_revision,
                    AUDIENCE_HASH,
                    actor.principal_id,
                    POLICY,
                    content.review_revision + 1,
                    reason=payload.get("reason"),
                )
                updated = domain.record_review(
                    content,
                    actor,
                    proof,
                    expected_revision=expected,
                    expected_review_revision=content.review_revision,
                )
            elif action == "publish":
                for review in content.reviews:
                    reviewer = self.db.get(AdultIdentityModel, review.reviewer_id)
                    grant = self.db.get(PermissionGrantModel, (review.reviewer_id, "content_admin"))
                    recorded = self.db.scalar(
                        select(REVIEW.c.permission_revision).where(
                            REVIEW.c.organization_id == SCOPE,
                            REVIEW.c.review_id == review.review_id,
                        )
                    )
                    if (
                        reviewer is None
                        or reviewer.state != "active"
                        or reviewer.account_role != "platform_admin"
                        or grant is None
                        or not grant.active
                        or grant.revision != recorded
                    ):
                        raise AdminError("REVIEW_PERMISSION_REVOKED", 403)
                reviews = {
                    r.dimension: r.review_id for r in content.reviews if r.decision == "approve"
                }
                updated = domain.publish(
                    content,
                    actor,
                    expected_revision=expected,
                    safety_review_id=reviews.get("safety", ""),
                    pedagogical_review_id=reviews.get("pedagogical", ""),
                    policy_version=POLICY,
                    audience_hash=AUDIENCE_HASH,
                )
            else:
                updated = domain.retire(
                    content,
                    actor,
                    now,
                    expected_revision=expected,
                    reason=payload.get("reason") or "",
                    archive=action == "archive",
                )
            self.transaction().save(
                updated,
                expected_revision=expected,
                event=ContentEvent(str(uuid4()), "catalog." + action, actor.principal_id, now),
                permission_revision=(
                    self.db.get(
                        PermissionGrantModel, (actor.principal_id, "content_admin")
                    ).revision
                    if proof
                    else None
                ),
            )
            if proof:
                self.admin.notify(content.authored_by, "CATALOG_REVIEWED", ref)
            self.admin.audit("CATALOG_" + action.upper(), "catalog", ref)
            return self.view(updated)

        return self.command(
            "catalog.action:" + ref, key, {**payload, "expected_revision": expected}, execute
        )
