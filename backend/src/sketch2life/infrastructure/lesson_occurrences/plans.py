"""Occurrence plan revisions: create a draft, confirm the head, read (FEAT-066 goal v3, T-3d).

SRS l.547-548 (activities; a Teacher-written activity needs its safety checklist), l.775 (one
approved plan per occurrence), l.1442 (UC-04: the approved plan references a concrete text
revision), l.1659-1660 (create a draft plan revision; confirm with the expected plan hash and the
checklist), l.1696-1699 (idempotency, stale fence, hashes), l.2688-2700 (supersession).

One transaction per command, serialised by a ``FOR UPDATE`` lock on the occurrence row that is taken
only after the caller passed the scope check (an unauthorised caller never locks anything). Lock
order: occurrence, then the rows of this task (plan, activities, one document revision stamp); T-3b
and T-3c take the occurrence (share) before their document rows, so no cycle exists.

Confirm order (T-3d-DEC-7, one transaction): checklist columns of every ``CUSTOM`` activity, the
previous approved plan becomes ``SUPERSEDED``, this plan becomes ``APPROVED`` (the partial unique
index ``uq_plan_one_approved`` forbids the reverse order), the referenced document revision gets
the one-way ``CONFIRMED`` stamp, the occurrence gets the approved pointer and a revision bump, the
audit entry and the receipt. Supersession only marks the old plan: no run, job or deck exists in v3
(§31.8.2), WP-4 owns their cancellation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.contracts.schemas.lesson_occurrences import (
    ConfirmPlanRevisionRequestV1,
    CreatePlanRevisionRequestV1,
    PlanActivityInputV1,
)
from sketch2life.domain.lesson_library.model import canonical_content_hash
from sketch2life.domain.lesson_occurrences.plan import (
    ActivityInput,
    activity_hash_entry,
    canonical_hash,
    confirm_fingerprint,
    create_fingerprint,
    decode_plan_cursor,
    encode_plan_cursor,
    normalize_safety_notes,
    occurrence_state_after_confirm,
    plan_content_hash,
    plan_etag_value,
    plan_request_problems,
)
from sketch2life.domain.lesson_occurrences.safety_checklist import (
    PRODUCTION_REGISTRY,
    ChecklistAnswer,
    ChecklistEntry,
    ChecklistRegistry,
    checklist_result,
    evaluate_checklist,
)
from sketch2life.infrastructure.lesson_library.tables import (
    LIBRARY_ITEMS,
    LIBRARY_VERSIONS,
    VERSION_ACTIVITIES,
)
from sketch2life.infrastructure.lesson_occurrences.documents import DocumentError
from sketch2life.infrastructure.lesson_occurrences.scope import (
    authorize_occurrence,
    not_found,
    require_class_writable,
)
from sketch2life.infrastructure.lesson_occurrences.tables import (
    DOCUMENT_REVISIONS,
    OCCURRENCES,
    PLAN_ACTIVITIES,
    PLAN_REVISIONS,
    SOURCE_DOCUMENTS,
)
from sketch2life.infrastructure.persistence.be1_models import Be1CommandReceiptModel
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel

CREATE_RECEIPT_SCOPE = "POST /v1/lesson-occurrences/{occurrence_id}/plan-revisions"
CONFIRM_RECEIPT_SCOPE = (
    "POST /v1/lesson-occurrences/{occurrence_id}/plan-revisions/{revision_no}/confirm"
)
AUDIT_CREATE_ACTION = "lesson.plan_revision.create"
AUDIT_CONFIRM_ACTION = "lesson.plan.confirm"


@dataclass(frozen=True, slots=True)
class PlanResult:
    """A plan command: the body, its HTTP status (201 create, 200 confirm) and the replay flag."""

    body: dict[str, Any]
    status_code: int
    replayed: bool


def _json_safe(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _db_failure(error: SQLAlchemyError) -> DocumentError:
    """A database fault is never a 500; the checklist trigger is the one named refusal."""
    if "LESSON_PLAN_CHECKLIST_REQUIRED" in str(getattr(error, "orig", error)):
        return DocumentError(409, "INVALID_STATE_TRANSITION")
    return DocumentError(503, "PROVIDER_UNAVAILABLE")


def activity_view(row: RowMapping) -> dict[str, Any]:
    """One activity of a plan body; a copied lesson activity shows its title and instructions."""
    kind = str(row["activity_kind"])
    snapshot = row["activity_snapshot"] if isinstance(row["activity_snapshot"], dict) else {}
    if kind == "CUSTOM":
        title, description = row["custom_title"], row["custom_description"]
    else:
        title, description = snapshot.get("title"), snapshot.get("instructions_text")
    return {
        "plan_activity_id": str(row["plan_activity_id"]),
        "order": int(row["activity_order"]),
        "kind": kind,
        "lesson_activity_id": row["catalog_activity_ref"] if kind == "LESSON" else None,
        "title": title,
        "description": description,
        "snapshot_hash": row["activity_snapshot_hash"],
        "checklist_required": kind == "CUSTOM",
        "checklist_version": row["safety_checklist_version"],
        "confirmed": row["confirmed_at"] is not None,
    }


def plan_body(
    plan: RowMapping,
    activities: list[RowMapping],
    document_ref: dict[str, Any] | None,
    *,
    supersedes_revision_no: int | None = None,
) -> dict[str, Any]:
    pin: dict[str, str] | None = None
    if plan["source_lesson_id"] is not None:
        pin = {
            "lesson_id": plan["source_lesson_id"],
            "version_id": plan["source_lesson_version_id"],
            "content_sha256": plan["source_lesson_version_hash"],
        }
    return {
        "contract": "LessonPlanRevisionV1",
        "occurrence_id": plan["occurrence_id"],
        "revision_no": int(plan["revision_no"]),
        "state": plan["state"],
        "content_hash": plan["content_hash"],
        "document_revision_ref": document_ref,
        "objectives": list(plan["objectives"]),
        "teacher_direction": plan["teacher_direction"],
        "safety_notes": plan["safety_notes"],
        "lesson_version_ref": pin,
        "lesson_version_no": plan["source_lesson_version_no"],
        "activities": [activity_view(row) for row in activities],
        "created_at": plan["created_at"],
        "approved_at": plan["approved_at"],
        "supersedes_revision_no": supersedes_revision_no,
    }


class PlanRevisionService:
    def __init__(self, db: Session, *, checklists: ChecklistRegistry = PRODUCTION_REGISTRY) -> None:
        self.db = db
        self._checklists = checklists

    # ------------------------------------------------------------------ shared reads
    def _require_writable(self, occurrence: RowMapping) -> None:
        if occurrence["state"] == "ARCHIVED":
            raise DocumentError(409, "INVALID_STATE_TRANSITION")
        # T-7b-DEC-9: a suspended or archived class is read-only (SRS l.593, l.1425).
        require_class_writable(self.db, occurrence)

    def _head(self, occurrence_id: str) -> RowMapping | None:
        return (
            self.db.execute(
                select(
                    PLAN_REVISIONS.c.plan_revision_id,
                    PLAN_REVISIONS.c.revision_no,
                    PLAN_REVISIONS.c.content_hash,
                    PLAN_REVISIONS.c.state,
                )
                .where(PLAN_REVISIONS.c.occurrence_id == occurrence_id)
                .order_by(PLAN_REVISIONS.c.revision_no.desc())
                .limit(1)
            )
            .mappings()
            .one_or_none()
        )

    @staticmethod
    def _stale(head: RowMapping | None) -> DocumentError:
        """409 ``STALE_REVISION`` with the head number (0 without a plan) and the head's ETag."""
        if head is None:
            return DocumentError(409, "STALE_REVISION", current_version=0)
        return DocumentError(
            409,
            "STALE_REVISION",
            current_version=int(head["revision_no"]),
            etag=plan_etag_value(str(head["content_hash"]), str(head["state"])),
        )

    def _plan_row(self, occurrence_id: str, revision_no: int) -> RowMapping | None:
        return (
            self.db.execute(
                select(PLAN_REVISIONS).where(
                    PLAN_REVISIONS.c.occurrence_id == occurrence_id,
                    PLAN_REVISIONS.c.revision_no == revision_no,
                )
            )
            .mappings()
            .one_or_none()
        )

    def _activity_rows(self, plan_revision_id: str) -> list[RowMapping]:
        return list(
            self.db.execute(
                select(PLAN_ACTIVITIES)
                .where(PLAN_ACTIVITIES.c.plan_revision_id == plan_revision_id)
                .order_by(PLAN_ACTIVITIES.c.activity_order)
            )
            .mappings()
            .all()
        )

    def _document_ref(self, revision_id: str | None) -> dict[str, Any] | None:
        if revision_id is None:
            return None
        row = (
            self.db.execute(
                select(SOURCE_DOCUMENTS.c.source_document_id, DOCUMENT_REVISIONS.c.revision_no)
                .join(
                    SOURCE_DOCUMENTS,
                    SOURCE_DOCUMENTS.c.source_document_id
                    == DOCUMENT_REVISIONS.c.source_document_id,
                )
                .where(DOCUMENT_REVISIONS.c.document_revision_id == revision_id)
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        return {"document_id": row["source_document_id"], "revision_no": int(row["revision_no"])}

    def _body_of(
        self, plan: RowMapping, *, supersedes_revision_no: int | None = None
    ) -> dict[str, Any]:
        return plan_body(
            plan,
            self._activity_rows(str(plan["plan_revision_id"])),
            self._document_ref(plan["source_document_revision_id"]),
            supersedes_revision_no=supersedes_revision_no,
        )

    def _receipt(
        self, principal: VerifiedPrincipal, scope: str, key: str
    ) -> Be1CommandReceiptModel | None:
        return self.db.get(Be1CommandReceiptModel, (principal.subject, scope, key))

    def _replay(self, receipt: Be1CommandReceiptModel, fingerprint: str) -> dict[str, Any]:
        if receipt.request_fingerprint != fingerprint:
            raise DocumentError(400, "INVALID_IDEMPOTENCY_KEY")
        return self._with_activity_ids(dict(receipt.response_json))

    def _with_activity_ids(self, body: dict[str, Any]) -> dict[str, Any]:
        """Fill ``plan_activity_id`` into a stored replay body written before the field existed
        (V4-A OPEN-B D11b). The activity rows of a revision are immutable, so the id of an activity
        is found by its order; a plan row that is gone leaves the body as stored."""

        activities = body.get("activities")
        if not isinstance(activities, list) or all(
            isinstance(item, dict) and item.get("plan_activity_id") for item in activities
        ):
            return body
        occurrence_id, number = body.get("occurrence_id"), body.get("revision_no")
        if not isinstance(occurrence_id, str) or type(number) is not int:
            return body
        plan = self._plan_row(occurrence_id, number)
        if plan is None:
            return body
        ids = {
            int(row["activity_order"]): str(row["plan_activity_id"])
            for row in self._activity_rows(str(plan["plan_revision_id"]))
        }
        filled: list[Any] = []
        for item in activities:
            if isinstance(item, dict) and not item.get("plan_activity_id"):
                order = item.get("order")
                filled.append(
                    {**item, "plan_activity_id": ids.get(order) if isinstance(order, int) else None}
                )
            else:
                filled.append(item)
        body["activities"] = filled
        return body

    def _authorize_write(
        self, principal: VerifiedPrincipal, occurrence_id: str
    ) -> tuple[RowMapping, str]:
        """Scope first with no lock, then the row lock and the decision again (T-3d-DEC-8)."""
        authorize_occurrence(self.db, principal, occurrence_id, write=True)
        access = authorize_occurrence(self.db, principal, occurrence_id, write=True, lock="update")
        return access.occurrence, access.account_ref

    # ------------------------------------------------------------------ lesson activities
    def _pinned_activities(
        self, principal: VerifiedPrincipal, occurrence: RowMapping
    ) -> tuple[int, dict[str, dict[str, Any]]]:
        """The activities of the occurrence's pinned version, after the integrity check (F-04).

        The pinned version must still be eligible (same organization, ``ACTIVE`` and ``VISIBLE``
        lesson the caller may see, ``APPROVED`` version: 409 ``INVALID_STATE_TRANSITION``) and must
        still hash to the pin (409 ``STALE_REVISION``): library rows carry no immutability
        trigger, so the copy is only trusted after the full-content hash is recomputed.
        """
        found = (
            self.db.execute(
                select(
                    LIBRARY_VERSIONS.c.lesson_id,
                    LIBRARY_VERSIONS.c.version_no,
                    LIBRARY_VERSIONS.c.content_json,
                    LIBRARY_VERSIONS.c.structured_content_hash,
                    LIBRARY_VERSIONS.c.review_state,
                    LIBRARY_ITEMS.c.organization_id,
                    LIBRARY_ITEMS.c.created_by,
                    LIBRARY_ITEMS.c.visibility,
                    LIBRARY_ITEMS.c.state,
                    LIBRARY_ITEMS.c.moderation_state,
                )
                .join(LIBRARY_ITEMS, LIBRARY_ITEMS.c.lesson_id == LIBRARY_VERSIONS.c.lesson_id)
                .where(LIBRARY_VERSIONS.c.version_id == occurrence["source_lesson_version_id"])
            )
            .mappings()
            .one_or_none()
        )
        if (
            found is None
            or found["lesson_id"] != occurrence["source_lesson_id"]
            or found["organization_id"] != occurrence["organization_ref"]
            or found["state"] != "ACTIVE"
            or found["moderation_state"] != "VISIBLE"
            or (found["visibility"] == "PRIVATE" and found["created_by"] != principal.subject)
            or found["review_state"] != "APPROVED"
        ):
            raise DocumentError(409, "INVALID_STATE_TRANSITION")
        rows = (
            self.db.execute(
                select(VERSION_ACTIVITIES.c.activity_id, VERSION_ACTIVITIES.c.activity_json)
                .where(VERSION_ACTIVITIES.c.version_id == occurrence["source_lesson_version_id"])
                .order_by(VERSION_ACTIVITIES.c.activity_order)
            )
            .mappings()
            .all()
        )
        content = dict(found["content_json"])
        content["activities"] = [dict(row["activity_json"]) for row in rows]
        recomputed = canonical_content_hash(content)
        if (
            recomputed != occurrence["source_lesson_version_hash"]
            or recomputed != found["structured_content_hash"]
        ):
            raise DocumentError(409, "STALE_REVISION")
        return int(found["version_no"]), {
            str(row["activity_id"]): dict(row["activity_json"]) for row in rows
        }

    def _document_revision(
        self, occurrence_id: str, document_id: str, revision_no: int
    ) -> tuple[str, str]:
        """Id and text hash of a revision of a non-deleted document of this occurrence, else 404."""
        row = (
            self.db.execute(
                select(
                    DOCUMENT_REVISIONS.c.document_revision_id,
                    DOCUMENT_REVISIONS.c.extracted_text_hash,
                )
                .join(
                    SOURCE_DOCUMENTS,
                    SOURCE_DOCUMENTS.c.source_document_id
                    == DOCUMENT_REVISIONS.c.source_document_id,
                )
                .where(
                    SOURCE_DOCUMENTS.c.source_document_id == document_id,
                    SOURCE_DOCUMENTS.c.occurrence_id == occurrence_id,
                    SOURCE_DOCUMENTS.c.document_state != "DELETED",
                    DOCUMENT_REVISIONS.c.revision_no == revision_no,
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise not_found()
        return str(row["document_revision_id"]), str(row["extracted_text_hash"])

    # ------------------------------------------------------------------ create
    def create_revision(
        self,
        *,
        principal: VerifiedPrincipal,
        occurrence_id: str,
        payload: CreatePlanRevisionRequestV1,
        idempotency_key: str,
    ) -> PlanResult:
        """Write a draft plan revision (immutable content) as head + 1, or refuse."""
        inputs = [_activity_input(item) for item in payload.activities]
        problems = plan_request_problems(
            objectives=payload.objectives,
            teacher_direction=payload.teacher_direction,
            safety_notes=payload.safety_notes,
            activities=inputs,
            custom_allowed=self._checklists.current is not None,
        )
        if problems:
            raise DocumentError(400, "INVALID_REQUEST", field_errors=problems)
        if not 0 < len(occurrence_id) <= 36:
            raise not_found()
        notes = normalize_safety_notes(payload.safety_notes)
        document_ref = (
            payload.document_revision_ref.model_dump(mode="json")
            if payload.document_revision_ref is not None
            else None
        )
        fingerprint = create_fingerprint(
            expected_head_revision_no=payload.expected_head_revision_no,
            document_ref=document_ref,
            objectives=payload.objectives,
            teacher_direction=payload.teacher_direction,
            safety_notes=notes,
            activities=inputs,
        )
        scope = CREATE_RECEIPT_SCOPE.format(occurrence_id=occurrence_id)
        try:
            occurrence, account = self._authorize_write(principal, occurrence_id)
            receipt = self._receipt(principal, scope, idempotency_key)
            if receipt is not None:
                replayed = self._replay(receipt, fingerprint)
                self.db.rollback()
                return PlanResult(replayed, 201, True)
            self._require_writable(occurrence)
            head = self._head(occurrence_id)
            head_no = int(head["revision_no"]) if head is not None else 0
            if payload.expected_head_revision_no != head_no:
                raise self._stale(head)
            document: tuple[str, str] | None = None
            if payload.document_revision_ref is not None:
                document = self._document_revision(
                    occurrence_id,
                    payload.document_revision_ref.document_id,
                    payload.document_revision_ref.revision_no,
                )
            snapshots, version_no = self._resolve_lesson_activities(principal, occurrence, inputs)

            plan_id = str(uuid4())
            now = datetime.now(UTC)
            activity_rows: list[dict[str, Any]] = []
            hash_entries: list[dict[str, Any]] = []
            for order, item in enumerate(inputs, start=1):
                row: dict[str, Any] = {
                    "plan_activity_id": str(uuid4()),
                    "plan_revision_id": plan_id,
                    "activity_order": order,
                    "activity_kind": item.kind,
                }
                if item.kind == "LESSON":
                    snapshot = snapshots[str(item.lesson_activity_id)]
                    row.update(
                        catalog_activity_ref=item.lesson_activity_id,
                        activity_version=version_no,
                        activity_snapshot=snapshot,
                        activity_snapshot_hash=canonical_hash(snapshot),
                    )
                else:
                    row.update(custom_title=item.title, custom_description=item.description)
                activity_rows.append(row)
                hash_entries.append(
                    activity_hash_entry(
                        order=order,
                        kind=item.kind,
                        catalog_activity_ref=row.get("catalog_activity_ref"),
                        activity_version=row.get("activity_version"),
                        title=row.get("custom_title"),
                        description=row.get("custom_description"),
                        snapshot_hash=row.get("activity_snapshot_hash"),
                    )
                )
            lesson_ref = (
                {
                    "lesson_id": occurrence["source_lesson_id"],
                    "version_id": occurrence["source_lesson_version_id"],
                    "version_no": occurrence["source_lesson_version_no"],
                    "content_hash": occurrence["source_lesson_version_hash"],
                }
                if occurrence["source_lesson_id"] is not None
                else None
            )
            content_hash = plan_content_hash(
                occurrence_id=occurrence_id,
                document=(
                    {"document_revision_id": document[0], "text_hash": document[1]}
                    if document is not None
                    else None
                ),
                objectives=payload.objectives,
                teacher_direction=payload.teacher_direction,
                safety_notes=notes,
                lesson_ref=lesson_ref,
                activities=hash_entries,
            )
            self.db.execute(
                PLAN_REVISIONS.insert().values(
                    plan_revision_id=plan_id,
                    occurrence_id=occurrence_id,
                    revision_no=head_no + 1,
                    source_document_revision_id=document[0] if document is not None else None,
                    objectives=list(payload.objectives),
                    teacher_direction=payload.teacher_direction,
                    safety_notes=notes,
                    content_hash=content_hash,
                    source_lesson_id=occurrence["source_lesson_id"],
                    source_lesson_version_id=occurrence["source_lesson_version_id"],
                    source_lesson_version_no=occurrence["source_lesson_version_no"],
                    source_lesson_version_hash=occurrence["source_lesson_version_hash"],
                    created_by=account,
                    created_at=now,
                )
            )
            for row in activity_rows:
                self.db.execute(PLAN_ACTIVITIES.insert().values(**row))
            organization = str(occurrence["organization_ref"])
            self.db.add(
                CoreAuditEntryModel(
                    audit_id=str(uuid4()),
                    organization_id=organization,
                    actor_ref=account,
                    action=AUDIT_CREATE_ACTION,
                    resource_type="lesson_plan_revision",
                    resource_id=plan_id,
                    decision="allowed",
                )
            )
            self.db.flush()
            plan = self._plan_row(occurrence_id, head_no + 1)
            if plan is None:  # pragma: no cover - the row was just flushed
                raise DocumentError(503, "PROVIDER_UNAVAILABLE")
            body = self._body_of(plan)
            self.db.add(
                Be1CommandReceiptModel(
                    principal_ref=principal.subject,
                    operation_scope=scope,
                    idempotency_key=idempotency_key,
                    organization_id=organization,
                    request_fingerprint=fingerprint,
                    response_json=_json_safe(body),
                )
            )
            self.db.commit()
            return PlanResult(body, 201, False)
        except IntegrityError as error:
            # Unreachable behind the occurrence lock; only a unique violation (23505) means
            # "someone else won", any other integrity failure is a fault and never "reload".
            self.db.rollback()
            if getattr(error.orig, "sqlstate", None) != "23505":
                raise DocumentError(503, "PROVIDER_UNAVAILABLE") from None
            winner = self._receipt(principal, scope, idempotency_key)
            if winner is not None:
                replayed = self._replay(winner, fingerprint)
                self.db.rollback()
                return PlanResult(replayed, 201, True)
            current = self._head(occurrence_id)
            self.db.rollback()
            raise self._stale(current) from None
        except SQLAlchemyError as error:
            self.db.rollback()
            raise _db_failure(error) from None
        except BaseException:
            self.db.rollback()
            raise

    def _resolve_lesson_activities(
        self,
        principal: VerifiedPrincipal,
        occurrence: RowMapping,
        inputs: list[ActivityInput],
    ) -> tuple[dict[str, dict[str, Any]], int | None]:
        wanted = [(index, item) for index, item in enumerate(inputs) if item.kind == "LESSON"]
        if not wanted:
            return {}, None
        if occurrence["source_lesson_version_id"] is None:
            raise DocumentError(
                400,
                "INVALID_REQUEST",
                field_errors=[
                    {"field": f"activities[{index}].kind", "code": "NOT_SUPPORTED"}
                    for index, _item in wanted
                ],
            )
        version_no, activities = self._pinned_activities(principal, occurrence)
        unknown = [
            {"field": f"activities[{index}].lesson_activity_id", "code": "INVALID_FORMAT"}
            for index, item in wanted
            if str(item.lesson_activity_id) not in activities
        ]
        if unknown:
            raise DocumentError(400, "INVALID_REQUEST", field_errors=unknown)
        return activities, version_no

    # ------------------------------------------------------------------ confirm
    def confirm_revision(
        self,
        *,
        principal: VerifiedPrincipal,
        occurrence_id: str,
        revision_no: int,
        payload: ConfirmPlanRevisionRequestV1,
        idempotency_key: str,
    ) -> PlanResult:
        """Approve the head revision when the hash and the safety checklist agree (SRS l.1660).

        Precedence: 404, 403, replay, archived 409, plan row 404, state 409 (a ``SUPERSEDED``
        plan is 409 whatever the checklist says), head 409 ``STALE_REVISION``, hash 409
        ``STALE_REVISION``, then the 400 checklist gate. Nothing is written unless all pass.
        """
        if not 0 < len(occurrence_id) <= 36:
            raise not_found()
        entries = [
            ChecklistEntry(
                activity_order=entry.activity_order,
                checklist_version=entry.checklist_version,
                items=tuple(ChecklistAnswer(item.item_id, item.checked) for item in entry.items),
            )
            for entry in payload.checklist
        ]
        fingerprint = confirm_fingerprint(revision_no, payload.expected_plan_hash, entries)
        scope = CONFIRM_RECEIPT_SCOPE.format(occurrence_id=occurrence_id, revision_no=revision_no)
        try:
            occurrence, account = self._authorize_write(principal, occurrence_id)
            receipt = self._receipt(principal, scope, idempotency_key)
            if receipt is not None:
                replayed = self._replay(receipt, fingerprint)
                self.db.rollback()
                return PlanResult(replayed, 200, True)
            self._require_writable(occurrence)
            plan = self._plan_row(occurrence_id, revision_no)
            if plan is None:
                raise not_found()
            organization = str(occurrence["organization_ref"])
            head = self._head(occurrence_id)
            if plan["state"] == "APPROVED":
                if plan["content_hash"] != payload.expected_plan_hash:
                    raise self._stale(head)
                # Already approved with this hash: nothing changes, only the receipt is kept.
                body = self._body_of(plan)
                self._store_receipt(
                    principal, scope, idempotency_key, organization, fingerprint, body
                )
                self.db.commit()
                return PlanResult(body, 200, False)
            if plan["state"] != "DRAFT":
                raise DocumentError(409, "INVALID_STATE_TRANSITION")
            if head is None or int(head["revision_no"]) != revision_no:
                # Only the head can be confirmed: an older draft must never replace a newer
                # approval (SRS l.1699). To use old content the Teacher writes a new revision.
                raise self._stale(head)
            if plan["content_hash"] != payload.expected_plan_hash:
                raise self._stale(head)

            activities = self._activity_rows(str(plan["plan_revision_id"]))
            custom = [row for row in activities if row["activity_kind"] == "CUSTOM"]
            problems = evaluate_checklist(
                custom_orders=[int(row["activity_order"]) for row in custom],
                entries=entries,
                registry=self._checklists,
            )
            if problems:
                raise DocumentError(400, "INVALID_REQUEST", field_errors=problems)

            now = datetime.now(UTC)
            definition = self._checklists.current
            if custom and definition is not None:
                for row in custom:
                    self.db.execute(
                        PLAN_ACTIVITIES.update()
                        .where(PLAN_ACTIVITIES.c.plan_activity_id == row["plan_activity_id"])
                        .values(
                            safety_checklist_version=definition.version,
                            checklist_result=checklist_result(definition),
                            confirmed_by=account,
                            confirmed_at=now,
                        )
                    )
            previous = (
                self.db.execute(
                    PLAN_REVISIONS.update()
                    .where(
                        PLAN_REVISIONS.c.occurrence_id == occurrence_id,
                        PLAN_REVISIONS.c.state == "APPROVED",
                    )
                    .values(state="SUPERSEDED", superseded_at=now)
                    .returning(PLAN_REVISIONS.c.revision_no)
                )
                .scalars()
                .all()
            )
            approved = self.db.execute(
                PLAN_REVISIONS.update()
                .where(
                    PLAN_REVISIONS.c.plan_revision_id == plan["plan_revision_id"],
                    PLAN_REVISIONS.c.state == "DRAFT",
                )
                .values(state="APPROVED", approved_by=account, approved_at=now)
                .returning(PLAN_REVISIONS.c.revision_no)
            ).scalar_one_or_none()
            if approved is None:  # pragma: no cover - the occurrence lock makes this unreachable
                raise DocumentError(409, "INVALID_STATE_TRANSITION")
            if plan["source_document_revision_id"] is not None:
                # The one-way stamp of DDL-A: the Teacher approved the text this plan pins (UC-04).
                self.db.execute(
                    DOCUMENT_REVISIONS.update()
                    .where(
                        DOCUMENT_REVISIONS.c.document_revision_id
                        == plan["source_document_revision_id"],
                        DOCUMENT_REVISIONS.c.review_state == "NEEDS_REVIEW",
                    )
                    .values(review_state="CONFIRMED", reviewed_by=account, reviewed_at=now)
                )
            self.db.execute(
                OCCURRENCES.update()
                .where(OCCURRENCES.c.occurrence_id == occurrence_id)
                .values(
                    approved_plan_revision_id=plan["plan_revision_id"],
                    state=occurrence_state_after_confirm(str(occurrence["state"])),
                    revision=OCCURRENCES.c.revision + 1,
                    updated_at=now,
                )
            )
            self.db.add(
                CoreAuditEntryModel(
                    audit_id=str(uuid4()),
                    organization_id=organization,
                    actor_ref=account,
                    action=AUDIT_CONFIRM_ACTION,
                    resource_type="lesson_plan_revision",
                    resource_id=str(plan["plan_revision_id"]),
                    decision="allowed",
                )
            )
            self.db.flush()
            confirmed = self._plan_row(occurrence_id, revision_no)
            if confirmed is None:  # pragma: no cover - the row was just updated
                raise DocumentError(503, "PROVIDER_UNAVAILABLE")
            body = self._body_of(
                confirmed, supersedes_revision_no=int(previous[0]) if previous else None
            )
            self._store_receipt(principal, scope, idempotency_key, organization, fingerprint, body)
            self.db.commit()
            return PlanResult(body, 200, False)
        except IntegrityError as error:
            self.db.rollback()
            if getattr(error.orig, "sqlstate", None) != "23505":
                raise _db_failure(error) from None
            winner = self._receipt(principal, scope, idempotency_key)
            if winner is not None:
                replayed = self._replay(winner, fingerprint)
                self.db.rollback()
                return PlanResult(replayed, 200, True)
            current = self._head(occurrence_id)
            self.db.rollback()
            raise self._stale(current) from None
        except SQLAlchemyError as error:
            self.db.rollback()
            raise _db_failure(error) from None
        except BaseException:
            self.db.rollback()
            raise

    def _store_receipt(
        self,
        principal: VerifiedPrincipal,
        scope: str,
        key: str,
        organization: str,
        fingerprint: str,
        body: dict[str, Any],
    ) -> None:
        self.db.add(
            Be1CommandReceiptModel(
                principal_ref=principal.subject,
                operation_scope=scope,
                idempotency_key=key,
                organization_id=organization,
                request_fingerprint=fingerprint,
                response_json=_json_safe(body),
            )
        )
        self.db.flush()

    # ------------------------------------------------------------------ reads
    def get_revision(
        self, *, principal: VerifiedPrincipal, occurrence_id: str, revision_no: int
    ) -> dict[str, Any]:
        if not 0 < len(occurrence_id) <= 36:
            raise not_found()
        authorize_occurrence(self.db, principal, occurrence_id)
        plan = self._plan_row(occurrence_id, revision_no)
        if plan is None:
            raise not_found()
        body = self._body_of(plan)
        self.db.rollback()
        return body

    def list_revisions(
        self,
        *,
        principal: VerifiedPrincipal,
        occurrence_id: str,
        limit: int,
        cursor: str | None,
    ) -> dict[str, Any]:
        """Plan revisions newest first (``revision_no`` descending), 25 by default, 100 at most."""
        if not 0 < len(occurrence_id) <= 36:
            raise not_found()
        authorize_occurrence(self.db, principal, occurrence_id)
        after = decode_plan_cursor(cursor) if cursor is not None else None
        statement = select(
            PLAN_REVISIONS.c.plan_revision_id,
            PLAN_REVISIONS.c.revision_no,
            PLAN_REVISIONS.c.state,
            PLAN_REVISIONS.c.content_hash,
            PLAN_REVISIONS.c.created_at,
            PLAN_REVISIONS.c.approved_at,
        ).where(PLAN_REVISIONS.c.occurrence_id == occurrence_id)
        if after is not None:
            statement = statement.where(PLAN_REVISIONS.c.revision_no < after)
        rows = (
            self.db.execute(
                statement.order_by(PLAN_REVISIONS.c.revision_no.desc()).limit(limit + 1)
            )
            .mappings()
            .all()
        )
        page = rows[:limit]
        counts: dict[str, int] = {}
        if page:
            counts = {
                str(plan_id): int(total)
                for plan_id, total in self.db.execute(
                    select(PLAN_ACTIVITIES.c.plan_revision_id, func.count())
                    .where(
                        PLAN_ACTIVITIES.c.plan_revision_id.in_(
                            [row["plan_revision_id"] for row in page]
                        )
                    )
                    .group_by(PLAN_ACTIVITIES.c.plan_revision_id)
                ).all()
            }
        items = [
            {
                "revision_no": int(row["revision_no"]),
                "state": row["state"],
                "content_hash": row["content_hash"],
                "activity_count": counts.get(str(row["plan_revision_id"]), 0),
                "created_at": row["created_at"],
                "approved_at": row["approved_at"],
            }
            for row in page
        ]
        next_cursor = (
            encode_plan_cursor(int(page[-1]["revision_no"])) if len(rows) > limit else None
        )
        self.db.rollback()
        return {"contract": "LessonPlanRevisionPageV1", "items": items, "next_cursor": next_cursor}


def _activity_input(item: PlanActivityInputV1) -> ActivityInput:
    return ActivityInput(
        kind=item.kind,
        lesson_activity_id=item.lesson_activity_id,
        title=item.title,
        description=item.description,
    )


__all__ = [
    "AUDIT_CONFIRM_ACTION",
    "AUDIT_CREATE_ACTION",
    "CONFIRM_RECEIPT_SCOPE",
    "CREATE_RECEIPT_SCOPE",
    "PlanResult",
    "PlanRevisionService",
    "activity_view",
    "plan_body",
]
