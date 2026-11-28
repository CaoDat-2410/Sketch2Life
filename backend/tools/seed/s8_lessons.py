"""Seed lesson occurrences, document metadata and plan revisions for S8."""

from __future__ import annotations

from typing import Any

from sqlalchemy import Connection, Engine, and_, func, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from sketch2life.contracts.schemas.lesson_occurrences import (
    ConfirmPlanRevisionRequestV1,
    CreateLessonOccurrenceRequestV1,
    CreatePlanRevisionRequestV1,
    EditDocumentRevisionRequestV1,
    LessonVersionRefV1,
    PlanActivityInputV1,
    PlanDocumentRefV1,
)
from sketch2life.domain.lesson_occurrences.documents import text_sha256
from sketch2life.infrastructure.lesson_occurrences.documents import OccurrenceDocumentService
from sketch2life.infrastructure.lesson_occurrences.plans import PlanRevisionService
from sketch2life.infrastructure.lesson_occurrences.presentations import LessonPresentationService
from sketch2life.infrastructure.lesson_occurrences.service import LessonOccurrenceService
from sketch2life.infrastructure.lesson_occurrences.tables import (
    DOCUMENT_REVISIONS,
    OCCURRENCES,
    PLAN_ACTIVITIES,
    PLAN_REVISIONS,
    PRESENTATION_REVISIONS,
    PRESENTATIONS,
    SOURCE_DOCUMENTS,
)
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.infrastructure.persistence.database import create_core_session_factory
from tools.seed import data
from tools.seed.s8_lessons_data import (
    DOCUMENT_EDIT_TEXT,
    DOCUMENTS,
    EXPECTED,
    PLANS,
    DocumentSpec,
    OccurrenceSpec,
    PlanSpec,
    document_revision_id,
    occurrence_key,
    plan_confirm_key,
    plan_create_key,
    presentation_create_key,
    source_document_id,
)
from tools.seed.s8_lessons_data import (
    OCCURRENCES as OCCURRENCE_SPECS,
)
from tools.seed.stage_common import (
    StageError,
    StageResult,
    run_stage_main,
    seed_principal,
)


def _account_id(session: Session, subject: str) -> str:
    identity = session.get(AdultIdentityModel, subject)
    if identity is None or identity.account_role != "teacher" or identity.state != "active":
        raise StageError("S8_TEACHER_IDENTITY_MISSING")
    return identity.account_id


def _pin(lesson_key: str, version_no: int) -> LessonVersionRefV1:
    lesson = data.lesson_id(lesson_key)
    version_id = data.version_id(lesson_key, version_no)
    version = next(
        (row for row in data.library_version_rows() if row["version_id"] == version_id), None
    )
    if version is None or version["lesson_id"] != lesson:
        raise StageError("S8_LESSON_VERSION_MISSING")
    return LessonVersionRefV1(
        lesson_id=lesson,
        version_id=version_id,
        content_sha256=version["structured_content_hash"],
    )


def _create_occurrence(
    session_factory: sessionmaker[Session], spec: OccurrenceSpec
) -> dict[str, Any]:
    session = session_factory()
    try:
        principal = seed_principal(spec.teacher_subject)
        account_id = _account_id(session, spec.teacher_subject)
        # The request model accepts the date only as ISO text (its validator rejects a date object).
        payload = CreateLessonOccurrenceRequestV1.model_validate(
            {
                "class_id": data.class_id("a", spec.class_number),
                "title": spec.title,
                "scheduled_date": spec.scheduled_date.isoformat(),
                "lesson_version_ref": (
                    _pin(spec.lesson_key, spec.lesson_version_no).model_dump(mode="json")
                    if spec.lesson_key is not None and spec.lesson_version_no is not None
                    else None
                ),
            }
        )
        # account_id is resolved here to ensure the real seeded Teacher is present; authorization
        # inside the service performs the authoritative account-id lookup for the write.
        if not account_id:
            raise StageError("S8_TEACHER_IDENTITY_MISSING")
        return (
            LessonOccurrenceService(session)
            .create(
                principal=principal,
                payload=payload,
                idempotency_key=occurrence_key(spec.key),
            )
            .body
        )
    except StageError:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise StageError("S8_OCCURRENCE_CREATE_FAILED") from None
    finally:
        session.close()


def _insert_document_rows(
    session_factory: sessionmaker[Session], spec: DocumentSpec, occurrence_id: str
) -> None:
    document_id = source_document_id(spec.key)
    teacher_subject = next(
        row.teacher_subject for row in OCCURRENCE_SPECS if row.key == spec.occurrence_key
    )
    session = session_factory()
    try:
        with session.begin():
            exists = session.scalar(
                select(SOURCE_DOCUMENTS.c.source_document_id).where(
                    SOURCE_DOCUMENTS.c.source_document_id == document_id
                )
            )
            if exists is not None:
                # The revision trigger refuses a re-insert before ON CONFLICT can skip it.
                return
            account_id = _account_id(session, teacher_subject)
            session.execute(
                pg_insert(SOURCE_DOCUMENTS)
                .values(
                    source_document_id=document_id,
                    occurrence_id=occurrence_id,
                    asset_ref=f"synthetic-asset-{spec.key}",
                    asset_version=1,
                    upload_session_ref=data.seed_uuid_text(f"s8:upload:{spec.key}"),
                    extraction_job_ref=data.seed_uuid_text(f"s8:extraction-job:{spec.key}"),
                    safe_file_name=spec.safe_file_name,
                    file_extension=spec.extension,
                    page_or_slide_count=spec.page_count,
                    document_state="EXTRACTED",
                    deleted_at=None,
                    uploaded_by=account_id,
                    uploaded_at=data.SEED_TIME,
                )
                .on_conflict_do_nothing(index_elements=[SOURCE_DOCUMENTS.c.source_document_id])
            )
            session.execute(
                pg_insert(DOCUMENT_REVISIONS)
                .values(
                    document_revision_id=document_revision_id(spec.key, 1),
                    source_document_id=document_id,
                    revision_no=1,
                    origin="EXTRACTION",
                    base_revision_no=None,
                    extracted_text=spec.extracted_text,
                    extracted_text_hash=text_sha256(spec.extracted_text),
                    parser_name=spec.parser_name,
                    parser_version=spec.parser_version,
                    extraction_warnings=list(spec.warnings),
                    page_coverage=list(spec.page_coverage),
                    review_state="NEEDS_REVIEW",
                    reviewed_by=None,
                    reviewed_at=None,
                    created_by=account_id,
                    created_at=data.SEED_TIME,
                )
                .on_conflict_do_nothing(index_elements=[DOCUMENT_REVISIONS.c.document_revision_id])
            )
            session.execute(
                pg_insert(CoreAuditEntryModel)
                .values(
                    audit_id=data.seed_uuid_text(f"s8:audit:document:{spec.key}"),
                    organization_id=data.org_id("a"),
                    actor_ref=account_id,
                    action="lesson.source_document.create",
                    resource_type="lesson_source_document",
                    resource_id=document_id,
                    decision="allowed",
                )
                .on_conflict_do_nothing(index_elements=[CoreAuditEntryModel.audit_id])
            )
    except Exception:
        session.rollback()
        raise StageError("S8_DOCUMENT_INSERT_FAILED") from None
    finally:
        session.close()


def _edit_o1_document(session_factory: sessionmaker[Session], occurrence_id: str) -> None:
    session = session_factory()
    try:
        spec = next(item for item in DOCUMENTS if item.key == "doc-o1")
        occurrence_spec = next(item for item in OCCURRENCE_SPECS if item.key == "o1")
        result = OccurrenceDocumentService(session, storage=None, parser=None).edit_revision(
            principal=seed_principal(occurrence_spec.teacher_subject),
            occurrence_id=occurrence_id,
            document_id=source_document_id(spec.key),
            payload=EditDocumentRevisionRequestV1(
                extracted_text=DOCUMENT_EDIT_TEXT,
                expected_head_revision_no=1,
            ),
            idempotency_key="seed:s8:doc-o1-edit",
        )
        if result.body["revision_no"] != 2 or result.body["origin"] != "TEACHER_EDIT":
            raise StageError("S8_DOCUMENT_EDIT_UNEXPECTED")
    except StageError:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise StageError("S8_DOCUMENT_EDIT_FAILED") from None
    finally:
        session.close()


def _create_presentation(
    session_factory: sessionmaker[Session],
    occurrence_id: str,
    occurrence_spec: OccurrenceSpec,
) -> dict[str, Any] | None:
    session = session_factory()
    try:
        existing = session.execute(
            select(PRESENTATIONS.c.presentation_id).where(
                PRESENTATIONS.c.occurrence_id == occurrence_id
            )
        ).scalar_one_or_none()
        if existing is not None:
            session.rollback()
            return None
        result = LessonPresentationService(
            session,
            storage=None,
            svg_drafter=None,
        ).create(
            principal=seed_principal(occurrence_spec.teacher_subject),
            occurrence_id=occurrence_id,
            seed="PLAN_ACTIVITIES",
            idempotency_key=presentation_create_key(occurrence_spec.key),
        )
        return result.body
    except Exception:
        session.rollback()
        raise StageError("S8_PRESENTATION_CREATE_FAILED") from None
    finally:
        session.close()


def _lesson_activity_inputs(
    spec: OccurrenceSpec, orders: tuple[int, ...]
) -> list[PlanActivityInputV1]:
    if not orders:
        return []
    if spec.lesson_key is None or spec.lesson_version_no is None:
        raise StageError("S8_PLAN_LESSON_PIN_MISSING")
    target_version_id = data.version_id(spec.lesson_key, spec.lesson_version_no)
    activities = {
        row["activity_order"]: row["activity_id"]
        for row in data.version_activity_rows()
        if row["version_id"] == target_version_id
    }
    if any(order not in activities for order in orders):
        raise StageError("S8_PLAN_ACTIVITY_MISSING")
    return [
        PlanActivityInputV1(kind="LESSON", lesson_activity_id=activities[order]) for order in orders
    ]


def _create_plan(
    session_factory: sessionmaker[Session],
    occurrence_id: str,
    occurrence_spec: OccurrenceSpec,
    plan_spec: PlanSpec,
) -> dict[str, Any]:
    session = session_factory()
    try:
        document_ref = None
        if plan_spec.document_revision_no is not None:
            document_spec = next(
                item for item in DOCUMENTS if item.occurrence_key == plan_spec.occurrence_key
            )
            document_ref = PlanDocumentRefV1(
                document_id=source_document_id(document_spec.key),
                revision_no=plan_spec.document_revision_no,
            )
        payload = CreatePlanRevisionRequestV1(
            expected_head_revision_no=plan_spec.expected_head_revision_no,
            document_revision_ref=document_ref,
            objectives=list(plan_spec.objectives),
            teacher_direction=plan_spec.teacher_direction,
            safety_notes=plan_spec.safety_notes,
            activities=_lesson_activity_inputs(occurrence_spec, plan_spec.activity_orders),
        )
        result = PlanRevisionService(session).create_revision(
            principal=seed_principal(occurrence_spec.teacher_subject),
            occurrence_id=occurrence_id,
            payload=payload,
            idempotency_key=plan_create_key(plan_spec.occurrence_key, plan_spec.revision_no),
        )
        return result.body
    except StageError:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise StageError("S8_PLAN_CREATE_FAILED") from None
    finally:
        session.close()


def _confirm_plan(
    session_factory: sessionmaker[Session],
    occurrence_id: str,
    occurrence_spec: OccurrenceSpec,
    plan_spec: PlanSpec,
    content_hash: str,
) -> None:
    session = session_factory()
    try:
        result = PlanRevisionService(session).confirm_revision(
            principal=seed_principal(occurrence_spec.teacher_subject),
            occurrence_id=occurrence_id,
            revision_no=plan_spec.revision_no,
            payload=ConfirmPlanRevisionRequestV1(expected_plan_hash=content_hash),
            idempotency_key=plan_confirm_key(plan_spec.occurrence_key, plan_spec.revision_no),
        )
        if result.body["state"] != "APPROVED":
            raise StageError("S8_PLAN_CONFIRM_UNEXPECTED")
    except StageError:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise StageError("S8_PLAN_CONFIRM_FAILED") from None
    finally:
        session.close()


def _occurrence_predicate() -> Any:
    return or_(
        *(
            and_(
                OCCURRENCES.c.class_ref == data.class_id("a", spec.class_number),
                OCCURRENCES.c.title == spec.title,
            )
            for spec in OCCURRENCE_SPECS
        )
    )


def count_s8_rows(connection: Connection) -> dict[str, int]:
    occurrence_ids = select(OCCURRENCES.c.occurrence_id).where(_occurrence_predicate())
    document_ids = select(SOURCE_DOCUMENTS.c.source_document_id).where(
        SOURCE_DOCUMENTS.c.occurrence_id.in_(occurrence_ids)
    )
    plan_ids = select(PLAN_REVISIONS.c.plan_revision_id).where(
        PLAN_REVISIONS.c.occurrence_id.in_(occurrence_ids)
    )
    presentation_ids = select(PRESENTATIONS.c.presentation_id).where(
        PRESENTATIONS.c.occurrence_id.in_(occurrence_ids)
    )
    return {
        "lesson_occurrences": int(
            connection.execute(
                select(func.count()).select_from(OCCURRENCES).where(_occurrence_predicate())
            ).scalar_one()
        ),
        "lesson_source_documents": int(
            connection.execute(
                select(func.count())
                .select_from(SOURCE_DOCUMENTS)
                .where(SOURCE_DOCUMENTS.c.occurrence_id.in_(occurrence_ids))
            ).scalar_one()
        ),
        "lesson_document_revisions": int(
            connection.execute(
                select(func.count())
                .select_from(DOCUMENT_REVISIONS)
                .where(DOCUMENT_REVISIONS.c.source_document_id.in_(document_ids))
            ).scalar_one()
        ),
        "lesson_plan_revisions": int(
            connection.execute(
                select(func.count())
                .select_from(PLAN_REVISIONS)
                .where(PLAN_REVISIONS.c.occurrence_id.in_(occurrence_ids))
            ).scalar_one()
        ),
        "lesson_plan_activities": int(
            connection.execute(
                select(func.count())
                .select_from(PLAN_ACTIVITIES)
                .where(PLAN_ACTIVITIES.c.plan_revision_id.in_(plan_ids))
            ).scalar_one()
        ),
        "lesson_presentations": int(
            connection.execute(
                select(func.count())
                .select_from(PRESENTATIONS)
                .where(PRESENTATIONS.c.occurrence_id.in_(occurrence_ids))
            ).scalar_one()
        ),
        "lesson_presentation_revisions": int(
            connection.execute(
                select(func.count())
                .select_from(PRESENTATION_REVISIONS)
                .where(PRESENTATION_REVISIONS.c.presentation_id.in_(presentation_ids))
            ).scalar_one()
        ),
    }


def run_s8(engine: Engine) -> StageResult:
    """Seed S8 through occurrence/plan services and direct metadata-only document rows."""
    try:
        with engine.connect() as connection:
            before = count_s8_rows(connection)
        session_factory = create_core_session_factory(engine)
        occurrences: dict[str, dict[str, Any]] = {}
        specs_by_key = {spec.key: spec for spec in OCCURRENCE_SPECS}
        for spec in OCCURRENCE_SPECS:
            occurrences[spec.key] = _create_occurrence(session_factory, spec)
        for document_spec in DOCUMENTS:
            occurrence_id = str(occurrences[document_spec.occurrence_key]["occurrence_id"])
            _insert_document_rows(session_factory, document_spec, occurrence_id)
            if document_spec.key == "doc-o1":
                _edit_o1_document(session_factory, occurrence_id)
        for plan_spec in PLANS:
            occurrence_spec = specs_by_key[plan_spec.occurrence_key]
            occurrence_id = str(occurrences[plan_spec.occurrence_key]["occurrence_id"])
            body = _create_plan(session_factory, occurrence_id, occurrence_spec, plan_spec)
            if plan_spec.confirm:
                _confirm_plan(
                    session_factory,
                    occurrence_id,
                    occurrence_spec,
                    plan_spec,
                    str(body["content_hash"]),
                )
        presentation_occurrence = next(spec for spec in OCCURRENCE_SPECS if spec.key == "o1")
        _create_presentation(
            session_factory,
            str(occurrences[presentation_occurrence.key]["occurrence_id"]),
            presentation_occurrence,
        )
        with engine.connect() as connection:
            after = count_s8_rows(connection)
        return StageResult("s8_lessons", before, after, EXPECTED)
    except StageError:
        raise
    except SQLAlchemyError:
        raise StageError("S8_DATABASE_ERROR") from None
    except Exception:
        raise StageError("S8_UNEXPECTED_FAILURE") from None


def main() -> int:
    return run_stage_main(run_s8, stage="s8")


if __name__ == "__main__":
    raise SystemExit(main())
