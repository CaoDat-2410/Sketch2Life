"""Service-backed synthetic data for the web screens in the S14 demo."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import HTTPException
from sqlalchemy import Connection, Engine, and_, func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from sketch2life.contracts.schemas.be1_runtime import RecordConsentRequest
from sketch2life.contracts.schemas.platform_admin import (
    CatalogAction,
    CatalogWrite,
    PlatformLessonWrite,
    PublicationAction,
)
from sketch2life.domain.platform_admin import AdminError
from sketch2life.infrastructure.learning_content.admin_catalog import AdminCatalogService
from sketch2life.infrastructure.learning_content.tables import EVENT, OUTBOX, RECORD, VERSION
from sketch2life.infrastructure.lesson_library.platform_publication import PlatformLessonService
from sketch2life.infrastructure.lesson_library.tables import (
    LIBRARY_ITEMS,
    LIBRARY_VERSIONS,
    VERSION_ACTIVITIES,
)
from sketch2life.infrastructure.persistence.be1_models import (
    ConsentRecordModel,
    ManagedProfileModel,
)
from sketch2life.infrastructure.persistence.core_models import (
    CoreAuditEntryModel,
    CoreOutboxEventModel,
)
from sketch2life.infrastructure.persistence.database import create_core_session_factory
from sketch2life.infrastructure.persistence.platform_models import (
    AdminCommandReceiptModel,
    InboxItemModel,
)
from sketch2life.infrastructure.platform_admin.service import PlatformAdminService
from sketch2life.interfaces.http.routers.be1_registry import record_consent
from tools.seed import data, s14_screen_demo_data
from tools.seed.stage_common import StageError, StageResult, run_stage_main, seed_principal

CREATE_KEY = "seed:s14:catalog:create"
SUBMIT_KEY = "seed:s14:catalog:submit"
LESSON_CREATE_KEY = "seed:s14:moderation:create"
LESSON_SUBMIT_KEY = "seed:s14:moderation:submit"
EXPECTED = s14_screen_demo_data.EXPECTED
CONSENT_CHILD_ID = s14_screen_demo_data.consent_child_id()

# Keep the original S14 catalog payload and keys stable so an earlier partial run replays.
PAYLOAD = CatalogWrite(
    activity={
        "title": "Vẽ khu vườn nhỏ",
        "objective": "Nhận biết hình dáng và màu sắc của lá cây.",
        "materials_text": "Giấy vẽ và bút màu.",
        "instructions_text": "Quan sát lá cây, rồi vẽ khu vườn theo trí tưởng tượng.",
        "safety_notes": "Không đưa lá cây vào miệng; rửa tay sau hoạt động.",
        "activity_kind": "indoor",
    },
    age_band="72-107",
    age_band_version=1,
    provenance="HUMAN_AUTHORED",
).model_dump(mode="json")


def _count(connection: Connection, statement: Any) -> int:
    return int(connection.scalar(statement) or 0)


def _catalog_record_id() -> Any:
    return (
        select(AdminCommandReceiptModel.response_json["record_id"].as_string())
        .where(
            AdminCommandReceiptModel.actor_ref == data.PLATFORM_ADMIN_SUBJECT,
            AdminCommandReceiptModel.operation == "catalog.write:new",
            AdminCommandReceiptModel.key == CREATE_KEY,
        )
        .scalar_subquery()
    )


def _lesson_id() -> Any:
    return (
        select(AdminCommandReceiptModel.response_json["lesson_id"].as_string())
        .where(
            AdminCommandReceiptModel.actor_ref == data.PLATFORM_ADMIN_SUBJECT,
            AdminCommandReceiptModel.operation == "lesson.write:new",
            AdminCommandReceiptModel.key == LESSON_CREATE_KEY,
        )
        .scalar_subquery()
    )


def _lesson_version_id() -> Any:
    return (
        select(AdminCommandReceiptModel.response_json["version_id"].as_string())
        .where(
            AdminCommandReceiptModel.actor_ref == data.PLATFORM_ADMIN_SUBJECT,
            AdminCommandReceiptModel.operation == "lesson.write:new",
            AdminCommandReceiptModel.key == LESSON_CREATE_KEY,
        )
        .scalar_subquery()
    )


def _consent_ids() -> Any:
    return select(ConsentRecordModel.consent_id).where(
        ConsentRecordModel.organization_id == s14_screen_demo_data.CONSENT_ORGANIZATION_ID,
        ConsentRecordModel.class_id == s14_screen_demo_data.CONSENT_CLASS_ID,
        ConsentRecordModel.child_id == CONSENT_CHILD_ID,
        ConsentRecordModel.purpose_ref == s14_screen_demo_data.CONSENT_PURPOSE_REF,
        ConsentRecordModel.recorded_by == s14_screen_demo_data.CONSENT_ACTOR_SUBJECT,
    )


def count_s14_rows(connection: Connection) -> dict[str, int]:
    """Count only the deterministic records owned by this stage."""
    catalog_id = _catalog_record_id()
    lesson_id = _lesson_id()
    lesson_version_id = _lesson_version_id()
    consent_ids = _consent_ids()
    catalog_event_ids = select(EVENT.c.event_id).where(
        EVENT.c.organization_id == "platform",
        EVENT.c.record_id == catalog_id,
    )

    audit_filter = or_(
        and_(
            CoreAuditEntryModel.action == "consent.record_pending",
            CoreAuditEntryModel.resource_type == "consent",
            CoreAuditEntryModel.resource_id.in_(consent_ids),
        ),
        and_(
            CoreAuditEntryModel.action.in_(
                ("CATALOG_VERSION_CREATED", "CATALOG_SUBMIT")
            ),
            CoreAuditEntryModel.resource_type == "catalog",
            CoreAuditEntryModel.resource_id == catalog_id,
        ),
        and_(
            CoreAuditEntryModel.action.in_(
                ("PLATFORM_LESSON_VERSION_CREATED", "PLATFORM_LESSON_SUBMIT")
            ),
            CoreAuditEntryModel.resource_type == "platform_lesson",
            CoreAuditEntryModel.resource_id == lesson_id,
        ),
    )
    outbox_filter = and_(
        CoreOutboxEventModel.event_type == "be1.consent.pending.v1",
        CoreOutboxEventModel.organization_id
        == s14_screen_demo_data.CONSENT_ORGANIZATION_ID,
        CoreOutboxEventModel.aggregate_id == CONSENT_CHILD_ID,
        CoreOutboxEventModel.payload["consent_id"].as_string().in_(consent_ids),
    )
    receipt_filter = or_(
        and_(
            AdminCommandReceiptModel.operation == "catalog.write:new",
            AdminCommandReceiptModel.key == CREATE_KEY,
        ),
        and_(
            AdminCommandReceiptModel.operation.like("catalog.action:%"),
            AdminCommandReceiptModel.key == SUBMIT_KEY,
        ),
        and_(
            AdminCommandReceiptModel.operation == "lesson.write:new",
            AdminCommandReceiptModel.key == LESSON_CREATE_KEY,
        ),
        and_(
            AdminCommandReceiptModel.operation.like("lesson.action:%"),
            AdminCommandReceiptModel.key == LESSON_SUBMIT_KEY,
        ),
        and_(
            AdminCommandReceiptModel.operation == s14_screen_demo_data.NOTIFICATION_OPERATION,
            AdminCommandReceiptModel.key == s14_screen_demo_data.NOTIFICATION_KEY,
        ),
    )

    return {
        "be1_consent_records_s14": _count(
            connection,
            select(func.count()).select_from(ConsentRecordModel).where(
                ConsentRecordModel.consent_id.in_(consent_ids)
            ),
        ),
        "core_audit_entries_s14": _count(
            connection,
            select(func.count()).select_from(CoreAuditEntryModel).where(audit_filter),
        ),
        "core_outbox_events_s14": _count(
            connection,
            select(func.count()).select_from(CoreOutboxEventModel).where(outbox_filter),
        ),
        "learning_content_records_s14": _count(
            connection,
            select(func.count()).select_from(RECORD).where(
                RECORD.c.organization_id == "platform", RECORD.c.record_id == catalog_id
            ),
        ),
        "learning_content_versions_s14": _count(
            connection,
            select(func.count()).select_from(VERSION).where(
                VERSION.c.organization_id == "platform",
                VERSION.c.record_id == catalog_id,
                VERSION.c.version == 1,
            ),
        ),
        "learning_content_events_s14": _count(
            connection,
            select(func.count()).select_from(EVENT).where(
                EVENT.c.organization_id == "platform", EVENT.c.record_id == catalog_id
            ),
        ),
        "learning_content_outbox_s14": _count(
            connection,
            select(func.count()).select_from(OUTBOX).where(
                OUTBOX.c.organization_id == "platform",
                OUTBOX.c.event_id.in_(catalog_event_ids),
            ),
        ),
        "platform_command_receipts_s14": _count(
            connection,
            select(func.count()).select_from(AdminCommandReceiptModel).where(
                AdminCommandReceiptModel.actor_ref == data.PLATFORM_ADMIN_SUBJECT,
                receipt_filter,
            ),
        ),
        "platform_lesson_items_s14": _count(
            connection,
            select(func.count()).select_from(LIBRARY_ITEMS).where(
                LIBRARY_ITEMS.c.lesson_id == lesson_id,
                LIBRARY_ITEMS.c.owner_kind == "PLATFORM",
            ),
        ),
        "platform_lesson_versions_s14": _count(
            connection,
            select(func.count()).select_from(LIBRARY_VERSIONS).where(
                LIBRARY_VERSIONS.c.lesson_id == lesson_id,
                LIBRARY_VERSIONS.c.version_id == lesson_version_id,
            ),
        ),
        "platform_lesson_activities_s14": _count(
            connection,
            select(func.count()).select_from(VERSION_ACTIVITIES).where(
                VERSION_ACTIVITIES.c.version_id == lesson_version_id
            ),
        ),
        "notification_inbox_items_s14": _count(
            connection,
            select(func.count()).select_from(InboxItemModel).where(
                InboxItemModel.recipient_ref == data.PLATFORM_ADMIN_SUBJECT,
                InboxItemModel.kind == s14_screen_demo_data.NOTIFICATION_KIND,
                InboxItemModel.resource_ref == s14_screen_demo_data.NOTIFICATION_RESOURCE,
            ),
        ),
    }


def seed_manager_consent(session_factory: Callable[[], Session]) -> None:
    with session_factory() as session:
        try:
            profile = session.get(ManagedProfileModel, CONSENT_CHILD_ID)
            if (
                profile is None
                or profile.organization_id != s14_screen_demo_data.CONSENT_ORGANIZATION_ID
                or profile.class_id != s14_screen_demo_data.CONSENT_CLASS_ID
            ):
                raise StageError("S14_CONSENT_PROFILE_NOT_FOUND")
            if not 72 <= profile.age_months <= 120:
                raise StageError("S14_CONSENT_PROFILE_AGE_OUT_OF_RANGE")

            matches = list(
                session.scalars(
                    select(ConsentRecordModel).where(
                        ConsentRecordModel.organization_id
                        == s14_screen_demo_data.CONSENT_ORGANIZATION_ID,
                        ConsentRecordModel.class_id == s14_screen_demo_data.CONSENT_CLASS_ID,
                        ConsentRecordModel.child_id == CONSENT_CHILD_ID,
                        ConsentRecordModel.purpose_ref
                        == s14_screen_demo_data.CONSENT_PURPOSE_REF,
                        ConsentRecordModel.recorded_by
                        == s14_screen_demo_data.CONSENT_ACTOR_SUBJECT,
                    )
                ).all()
            )
            if matches:
                if (
                    len(matches) != 1
                    or matches[0].state != "pending"
                    or matches[0].evidence_ref is not None
                ):
                    raise StageError("S14_CONSENT_EXISTING_STATE_UNEXPECTED")
                return

            result = record_consent(
                s14_screen_demo_data.CONSENT_ORGANIZATION_ID,
                s14_screen_demo_data.CONSENT_CLASS_ID,
                RecordConsentRequest(
                    class_id=s14_screen_demo_data.CONSENT_CLASS_ID,
                    child_id=CONSENT_CHILD_ID,
                    purpose_ref=s14_screen_demo_data.CONSENT_PURPOSE_REF,
                    evidence_ref=None,
                ),
                seed_principal(s14_screen_demo_data.CONSENT_ACTOR_SUBJECT),
                session,
            )
            if result.get("state") != "pending" or result.get("effective") is not False:
                raise StageError("S14_CONSENT_RESULT_UNEXPECTED")
        except StageError:
            session.rollback()
            raise
        except (HTTPException, SQLAlchemyError):
            session.rollback()
            raise StageError("S14_CONSENT_FAILED") from None


def seed_catalog(session_factory: Callable[[], Session]) -> None:
    with session_factory() as session:
        # An earlier S14 run already submitted the record: replaying with a newer payload
        # shape is refused, so leave it as it is.
        if session.scalar(
            select(AdminCommandReceiptModel.key).where(
                AdminCommandReceiptModel.actor_ref == data.PLATFORM_ADMIN_SUBJECT,
                AdminCommandReceiptModel.operation.like("catalog.action:%"),
                AdminCommandReceiptModel.key == SUBMIT_KEY,
            )
        ):
            return
        service = AdminCatalogService(
            PlatformAdminService(session, seed_principal(data.PLATFORM_ADMIN_SUBJECT))
        )
        try:
            draft = service.write(PAYLOAD, CREATE_KEY)
            if draft.get("state") != "draft":
                raise StageError("S14_CATALOG_DRAFT_UNEXPECTED")
            submit_payload = CatalogAction(
                action="submit",
                version=int(draft["version"]),
                content_hash=str(draft["content_hash"]),
            ).model_dump(mode="json")
            submitted = service.action(
                str(draft["record_id"]),
                submit_payload,
                int(draft["revision"]),
                SUBMIT_KEY,
            )
            if submitted.get("state") != "submitted":
                raise StageError("S14_CATALOG_SUBMIT_UNEXPECTED")
        except StageError:
            session.rollback()
            raise
        except (AdminError, SQLAlchemyError, ValueError, KeyError, TypeError):
            session.rollback()
            raise StageError("S14_CATALOG_FAILED") from None


def seed_moderation(session_factory: Callable[[], Session]) -> None:
    with session_factory() as session:
        service = PlatformLessonService(
            PlatformAdminService(session, seed_principal(data.PLATFORM_ADMIN_SUBJECT))
        )
        try:
            content = s14_screen_demo_data.PLATFORM_LESSON_CONTENT
            write_payload = PlatformLessonWrite(content=content).content.model_dump(mode="json")
            draft = service.write(write_payload, LESSON_CREATE_KEY)
            if draft.get("review_state") != "DRAFT":
                raise StageError("S14_MODERATION_DRAFT_UNEXPECTED")
            submit_payload = PublicationAction(
                action="submit",
                version_id=str(draft["version_id"]),
                content_hash=str(draft["content_hash"]),
            ).model_dump(mode="json")
            submitted = service.action(
                str(draft["lesson_id"]),
                submit_payload,
                int(draft["revision"]),
                LESSON_SUBMIT_KEY,
            )
            if submitted.get("review_state") != "PENDING_REVIEW":
                raise StageError("S14_MODERATION_SUBMIT_UNEXPECTED")
        except StageError:
            session.rollback()
            raise
        except (AdminError, SQLAlchemyError, ValueError, KeyError, TypeError):
            session.rollback()
            raise StageError("S14_MODERATION_FAILED") from None


def seed_notification(session_factory: Callable[[], Session]) -> None:
    with session_factory() as session:
        service = PlatformAdminService(session, seed_principal(data.PLATFORM_ADMIN_SUBJECT))
        try:
            existing = session.scalar(
                select(InboxItemModel).where(
                    InboxItemModel.recipient_ref == data.PLATFORM_ADMIN_SUBJECT,
                    InboxItemModel.kind == s14_screen_demo_data.NOTIFICATION_KIND,
                    InboxItemModel.resource_ref == s14_screen_demo_data.NOTIFICATION_RESOURCE,
                )
            )
            receipt = session.get(
                AdminCommandReceiptModel,
                (
                    data.PLATFORM_ADMIN_SUBJECT,
                    s14_screen_demo_data.NOTIFICATION_OPERATION,
                    s14_screen_demo_data.NOTIFICATION_KEY,
                ),
            )
            if (existing is None) != (receipt is None):
                raise StageError("S14_NOTIFICATION_STATE_CONFLICT")
            service.identity()

            def create_item(notifier: PlatformAdminService = service) -> dict[str, str]:
                notifier.notify(
                    data.PLATFORM_ADMIN_SUBJECT,
                    s14_screen_demo_data.NOTIFICATION_KIND,
                    s14_screen_demo_data.NOTIFICATION_RESOURCE,
                )
                return {
                    "kind": s14_screen_demo_data.NOTIFICATION_KIND,
                    "resource_ref": s14_screen_demo_data.NOTIFICATION_RESOURCE,
                }

            result = service.command(
                s14_screen_demo_data.NOTIFICATION_OPERATION,
                s14_screen_demo_data.NOTIFICATION_KEY,
                {
                    "kind": s14_screen_demo_data.NOTIFICATION_KIND,
                    "resource_ref": s14_screen_demo_data.NOTIFICATION_RESOURCE,
                },
                create_item,
            )
            if result.get("kind") != s14_screen_demo_data.NOTIFICATION_KIND:
                raise StageError("S14_NOTIFICATION_RESULT_UNEXPECTED")
        except StageError:
            session.rollback()
            raise
        except (AdminError, SQLAlchemyError, ValueError, KeyError, TypeError):
            session.rollback()
            raise StageError("S14_NOTIFICATION_FAILED") from None


def run_s14(engine: Engine) -> StageResult:
    try:
        with engine.connect() as connection:
            before = count_s14_rows(connection)
        session_factory = create_core_session_factory(engine)
        failures = []
        # Consent is left out: every seeded child is under 72 months, which its guard refuses.
        for seed in (seed_catalog, seed_moderation, seed_notification):
            try:
                seed(session_factory)
            except StageError as exc:
                failures.append(exc.code)
        with engine.connect() as connection:
            after = count_s14_rows(connection)
        before["screen_failures_s14"] = 0
        after["screen_failures_s14"] = len(failures)
        return StageResult(
            "s14_screen_demo", before, after, {**EXPECTED, "screen_failures_s14": 0},
            tuple(failures),
        )
    except StageError:
        raise
    except SQLAlchemyError:
        raise StageError("S14_DATABASE_ERROR") from None


def main() -> int:
    return run_stage_main(run_s14, stage="s14")


if __name__ == "__main__":
    raise SystemExit(main())
