"""Lesson occurrence create and reads (FEAT-066 goal v3, T-3a; SRS l.775, l.798, l.1652, l.1697).

One transaction per command on the request's ``Session``. Authorisation order for create: scope
(404, 403, 409 ``TEACHER_ASSIGNMENT_REQUIRED``), receipt replay, class state (409), lesson pin
(404, 409), insert, audit entry and receipt, commit. Receipts are success-only and keep the first
201 body (no child or storage data in it), so a replay returns "the initial result" (l.1696).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import literal, select, tuple_
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.contracts.schemas.lesson_occurrences import (
    CreateLessonOccurrenceRequestV1,
    LessonVersionRefV1,
)
from sketch2life.domain.lesson_occurrences.model import (
    AccessOutcome,
    decide_read,
    decode_cursor,
    encode_cursor,
    normalize_title,
)
from sketch2life.infrastructure.lesson_library.tables import LIBRARY_ITEMS, LIBRARY_VERSIONS
from sketch2life.infrastructure.lesson_occurrences.scope import (
    LessonOccurrenceError,
    authorize_create,
    authorize_occurrence,
    load_caller_facts,
    not_found,
)
from sketch2life.infrastructure.lesson_occurrences.tables import OCCURRENCES, PLAN_REVISIONS
from sketch2life.infrastructure.persistence.be1_models import (
    Be1CommandReceiptModel,
    ClassroomModel,
)
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel

CREATE_RECEIPT_SCOPE = "POST /v1/lesson-occurrences"
AUDIT_CREATE_ACTION = "lesson.occurrence.create"
MAX_PAGE_SIZE = 100


@dataclass(frozen=True, slots=True)
class CreateResult:
    body: dict[str, Any]
    replayed: bool


def _json_safe(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def create_fingerprint(payload: CreateLessonOccurrenceRequestV1) -> str:
    """SHA-256 of the canonical request: stripped title, date text and the three pin fields."""
    pin = payload.lesson_version_ref
    canonical = json.dumps(
        {
            "class_id": payload.class_id,
            "title": normalize_title(payload.title),
            "scheduled_date": payload.scheduled_date.isoformat()
            if payload.scheduled_date
            else None,
            "lesson_version_ref": pin.model_dump(mode="json") if pin is not None else None,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def occurrence_body(row: RowMapping, plan: RowMapping | None) -> dict[str, Any]:
    """The ``LessonOccurrenceV1`` body: no organization id, storage word or child field."""
    pin: dict[str, str] | None = None
    if row["source_lesson_id"] is not None:
        pin = {
            "lesson_id": row["source_lesson_id"],
            "version_id": row["source_lesson_version_id"],
            "content_sha256": row["source_lesson_version_hash"],
        }
    approved = None
    if plan is not None:
        approved = {
            "revision_no": plan["revision_no"],
            "plan_hash": plan["content_hash"],
            "approved_at": plan["approved_at"],
        }
    return {
        "contract": "LessonOccurrenceV1",
        "occurrence_id": row["occurrence_id"],
        "class_id": row["class_ref"],
        "title": row["title"],
        "scheduled_date": row["scheduled_date"],
        "state": row["state"],
        "revision": row["revision"],
        "responsible_teacher_ref": row["responsible_teacher_ref"],
        "lesson_version_ref": pin,
        "lesson_version_no": row["source_lesson_version_no"],
        "approved_plan": approved,
        "sample_video": {
            "slot_state": row["sample_slot_state"],
            "claimed_at": row["sample_claimed_at"],
            "run_ref": row["successful_sample_run_ref"],
        },
        "created_at": row["created_at"],
    }


class LessonOccurrenceService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------ helpers
    def _approved_plan(self, row: RowMapping) -> RowMapping | None:
        pointer = row["approved_plan_revision_id"]
        if pointer is None:
            return None
        return (
            self.db.execute(
                select(
                    PLAN_REVISIONS.c.revision_no,
                    PLAN_REVISIONS.c.content_hash,
                    PLAN_REVISIONS.c.approved_at,
                ).where(
                    PLAN_REVISIONS.c.plan_revision_id == pointer,
                    PLAN_REVISIONS.c.occurrence_id == row["occurrence_id"],
                )
            )
            .mappings()
            .one_or_none()
        )

    def _view(self, row: RowMapping) -> dict[str, Any]:
        return occurrence_body(row, self._approved_plan(row))

    def _receipt(self, principal: VerifiedPrincipal, key: str) -> Be1CommandReceiptModel | None:
        return self.db.get(Be1CommandReceiptModel, (principal.subject, CREATE_RECEIPT_SCOPE, key))

    @staticmethod
    def _replay(receipt: Be1CommandReceiptModel, fingerprint: str) -> dict[str, Any]:
        if receipt.request_fingerprint != fingerprint:
            raise LessonOccurrenceError(400, "INVALID_IDEMPOTENCY_KEY")
        return dict(receipt.response_json)

    # ------------------------------------------------------------------ lesson pin
    def resolve_lesson_pin(
        self,
        *,
        principal: VerifiedPrincipal,
        organization_id: str,
        ref: LessonVersionRefV1,
    ) -> int:
        """Check the exact pin and return the version number kept for lineage (T-3a-DEC-6).

        Fail-closed eligibility: same organization as the class, an ``ACTIVE`` and ``VISIBLE``
        lesson the caller may see (the ``get_lesson`` rule: creator or not ``PRIVATE``), and an
        ``APPROVED`` version. Not visible: 404. Visible but not approved: 409
        ``INVALID_STATE_TRANSITION``. A hash that differs from the stored one: 409
        ``STALE_REVISION``. Never ``latest``.
        """
        found = (
            self.db.execute(
                select(
                    LIBRARY_VERSIONS.c.version_no,
                    LIBRARY_VERSIONS.c.structured_content_hash,
                    LIBRARY_VERSIONS.c.review_state,
                    LIBRARY_ITEMS.c.organization_id,
                    LIBRARY_ITEMS.c.created_by,
                    LIBRARY_ITEMS.c.visibility,
                    LIBRARY_ITEMS.c.state,
                    LIBRARY_ITEMS.c.moderation_state,
                )
                .join(LIBRARY_ITEMS, LIBRARY_ITEMS.c.lesson_id == LIBRARY_VERSIONS.c.lesson_id)
                .where(
                    LIBRARY_VERSIONS.c.version_id == ref.version_id,
                    LIBRARY_VERSIONS.c.lesson_id == ref.lesson_id,
                )
            )
            .mappings()
            .one_or_none()
        )
        if (
            found is None
            or found["organization_id"] != organization_id
            or found["state"] != "ACTIVE"
            or found["moderation_state"] != "VISIBLE"
            or (found["visibility"] == "PRIVATE" and found["created_by"] != principal.subject)
        ):
            raise not_found()
        if found["structured_content_hash"] != ref.content_sha256:
            raise LessonOccurrenceError(409, "STALE_REVISION")
        if found["review_state"] != "APPROVED":
            raise LessonOccurrenceError(409, "INVALID_STATE_TRANSITION")
        return int(found["version_no"])

    # ------------------------------------------------------------------ create
    def create(
        self,
        *,
        principal: VerifiedPrincipal,
        payload: CreateLessonOccurrenceRequestV1,
        idempotency_key: str,
    ) -> CreateResult:
        authorization = authorize_create(self.db, principal, payload.class_id)
        classroom: ClassroomModel = authorization.classroom
        fingerprint = create_fingerprint(payload)
        existing = self._receipt(principal, idempotency_key)
        if existing is not None:
            replay = self._replay(existing, fingerprint)
            self.db.rollback()
            return CreateResult(replay, replayed=True)
        if classroom.state != "active":
            raise LessonOccurrenceError(409, "INVALID_STATE_TRANSITION")

        pin = payload.lesson_version_ref
        pin_values: dict[str, Any] = {}
        if pin is not None:
            version_no = self.resolve_lesson_pin(
                principal=principal, organization_id=classroom.organization_id, ref=pin
            )
            pin_values = {
                "source_lesson_id": pin.lesson_id,
                "source_lesson_version_id": pin.version_id,
                "source_lesson_version_no": version_no,
                "source_lesson_version_hash": pin.content_sha256,
            }

        occurrence_id = str(uuid4())
        now = datetime.now(UTC)
        row = (
            self.db.execute(
                OCCURRENCES.insert()
                .values(
                    occurrence_id=occurrence_id,
                    organization_ref=classroom.organization_id,
                    class_ref=classroom.class_id,
                    responsible_teacher_ref=authorization.account_ref,
                    created_by=authorization.account_ref,
                    title=normalize_title(payload.title),
                    scheduled_date=payload.scheduled_date,
                    created_at=now,
                    updated_at=now,
                    **pin_values,
                )
                .returning(*OCCURRENCES.c)
            )
            .mappings()
            .one()
        )
        body = occurrence_body(row, None)
        self.db.add(
            CoreAuditEntryModel(
                audit_id=str(uuid4()),
                organization_id=classroom.organization_id,
                actor_ref=authorization.account_ref,
                action=AUDIT_CREATE_ACTION,
                resource_type="lesson_occurrence",
                resource_id=occurrence_id,
                decision="allowed",
            )
        )
        self.db.add(
            Be1CommandReceiptModel(
                principal_ref=principal.subject,
                operation_scope=CREATE_RECEIPT_SCOPE,
                idempotency_key=idempotency_key,
                organization_id=classroom.organization_id,
                request_fingerprint=fingerprint,
                response_json=_json_safe(body),
            )
        )
        try:
            self.db.commit()
        except IntegrityError:
            # A concurrent request with the same key committed first: its occurrence and receipt
            # stand, this transaction (occurrence and audit row included) is rolled back.
            self.db.rollback()
            winner = self._receipt(principal, idempotency_key)
            if winner is None:
                raise LessonOccurrenceError(409, "RESOURCE_CONFLICT") from None
            replay = self._replay(winner, fingerprint)
            self.db.rollback()
            return CreateResult(replay, replayed=True)
        except SQLAlchemyError:
            self.db.rollback()
            raise LessonOccurrenceError(503, "PROVIDER_UNAVAILABLE") from None
        return CreateResult(body, replayed=False)

    # ------------------------------------------------------------------ reads
    def get(self, *, principal: VerifiedPrincipal, occurrence_id: str) -> dict[str, Any]:
        if not 0 < len(occurrence_id) <= 36:
            raise not_found()
        access = authorize_occurrence(self.db, principal, occurrence_id)
        body = self._view(access.occurrence)
        self.db.rollback()
        return body

    def list_page(
        self,
        *,
        principal: VerifiedPrincipal,
        class_id: str,
        state: str | None,
        limit: int,
        cursor: str | None,
    ) -> dict[str, Any]:
        """Occurrence-state list of one class (SRS l.798), not the X-17 history list (T3A-D9)."""
        if not 1 <= limit <= MAX_PAGE_SIZE:
            raise LessonOccurrenceError(
                400, "INVALID_REQUEST", field_errors=[{"field": "limit", "code": "OUT_OF_RANGE"}]
            )
        after = decode_cursor(cursor) if cursor is not None else None
        classroom = self.db.scalar(
            select(ClassroomModel).where(ClassroomModel.class_id == class_id)
        )
        if classroom is None:
            raise not_found()
        facts = load_caller_facts(self.db, principal, classroom.organization_id)
        if facts is None or decide_read(facts.rows, class_id) is not AccessOutcome.PROCEED:
            raise not_found()
        statement = select(OCCURRENCES).where(OCCURRENCES.c.class_ref == class_id)
        if state is not None:
            statement = statement.where(OCCURRENCES.c.state == state)
        if after is not None:
            statement = statement.where(
                tuple_(OCCURRENCES.c.created_at, OCCURRENCES.c.occurrence_id)
                < tuple_(literal(after[0]), literal(after[1]))
            )
        rows = (
            self.db.execute(
                statement.order_by(
                    OCCURRENCES.c.created_at.desc(), OCCURRENCES.c.occurrence_id.desc()
                ).limit(limit + 1)
            )
            .mappings()
            .all()
        )
        page = rows[:limit]
        next_cursor = (
            encode_cursor(page[-1]["created_at"], page[-1]["occurrence_id"])
            if len(rows) > limit
            else None
        )
        items = [self._view(row) for row in page]
        self.db.rollback()
        return {"contract": "LessonOccurrencePageV1", "items": items, "next_cursor": next_cursor}

    def list_teacher_history(
        self,
        *,
        organization_id: str,
        principal: VerifiedPrincipal,
        state: str | None,
        limit: int,
        cursor: str | None,
    ) -> dict[str, Any]:
        """Merge occurrence history across the caller's current, non-archived class scope."""
        facts = load_caller_facts(self.db, principal, organization_id)
        if facts is None:
            raise not_found()
        if not 1 <= limit <= MAX_PAGE_SIZE:
            raise LessonOccurrenceError(
                400,
                "INVALID_REQUEST",
                field_errors=[{"field": "limit", "code": "OUT_OF_RANGE"}],
            )
        readable_class_ids = [
            row.class_id
            for row in self.db.scalars(
                select(ClassroomModel).where(
                    ClassroomModel.organization_id == organization_id,
                    ClassroomModel.state != "archived",
                )
            ).all()
            if decide_read(facts.rows, row.class_id) is AccessOutcome.PROCEED
        ]
        after = decode_cursor(cursor) if cursor is not None else None
        statement = select(OCCURRENCES).select_from(
            OCCURRENCES.join(ClassroomModel, ClassroomModel.class_id == OCCURRENCES.c.class_ref)
        ).where(
            OCCURRENCES.c.organization_ref == organization_id,
            ClassroomModel.organization_id == organization_id,
            ClassroomModel.state != "archived",
            ClassroomModel.class_id.in_(readable_class_ids),
        )
        if state is not None:
            statement = statement.where(OCCURRENCES.c.state == state)
        if after is not None:
            statement = statement.where(
                tuple_(OCCURRENCES.c.created_at, OCCURRENCES.c.occurrence_id)
                < tuple_(literal(after[0]), literal(after[1]))
            )
        rows = (
            self.db.execute(
                statement.order_by(
                    OCCURRENCES.c.created_at.desc(), OCCURRENCES.c.occurrence_id.desc()
                ).limit(limit + 1)
            )
            .mappings()
            .all()
        )
        page = rows[:limit]
        next_cursor = (
            encode_cursor(page[-1]["created_at"], page[-1]["occurrence_id"])
            if len(rows) > limit
            else None
        )
        items = [self._view(row) for row in page]
        self.db.rollback()
        return {"contract": "LessonOccurrencePageV1", "items": items, "next_cursor": next_cursor}


__all__ = [
    "AUDIT_CREATE_ACTION",
    "CREATE_RECEIPT_SCOPE",
    "CreateResult",
    "LessonOccurrenceError",
    "LessonOccurrenceService",
    "create_fingerprint",
    "occurrence_body",
]
