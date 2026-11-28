"""Teacher-cancelled organization run and private lesson shares (SEED-2 Phase C)."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from typing import Any, cast

from sqlalchemy import Connection, Engine, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.lesson_documents import LessonDocumentParser, MalwareScanner
from sketch2life.application.ports.object_storage import ObjectStoragePort
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryLifecycleRecord,
    ParentStoryRunError,
)
from sketch2life.application.ports.story_run_actor import RunActor, RunActorKind
from sketch2life.application.services.parent_story_runs import (
    ParentStoryRunService,
    ParentStoryRunServiceError,
)
from sketch2life.contracts.schemas.lesson_library import LessonContentInputV1
from sketch2life.infrastructure.lesson_library.service import (
    LessonLibraryError,
    LessonLibraryService,
)
from sketch2life.infrastructure.lesson_library.tables import (
    ACCESS_GRANTS,
    LIBRARY_ITEMS,
    LIBRARY_VERSIONS,
    VERSION_ACTIVITIES,
)
from sketch2life.infrastructure.lesson_library.tables import (
    COMMAND_RECEIPTS as LESSON_COMMAND_RECEIPTS,
)
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.infrastructure.persistence.database import create_core_session_factory
from sketch2life.infrastructure.persistence.parent_story_profile_lookup import (
    SqlParentStoryProfileLookup,
)
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
)
from sketch2life.infrastructure.persistence.teacher_run_access import SqlTeacherRunAccess
from sketch2life.infrastructure.story_run_lite import tables as story_tables
from tools.seed import data
from tools.seed.s11_org_run_shares_data import (
    EXPECTED,
    LESSON_CONTENTS,
    LESSON_RECEIPT_KEYS,
    LESSON_TITLES,
    MANAGER_A,
    ORG_A,
    PARENT_GROUP_A1,
    PRIVATE_SHARE_SPECS,
    REVIEW_CHANGE_REASON,
    REVIEW_REQUEST_LESSONS,
    TEACHER_A1,
    TEACHER_CONTEXT_SNAPSHOT,
    TEACHER_PROFILE_REVISION_REF,
    TEACHER_RUN_CANCEL_KEY,
    TEACHER_RUN_CREATED_AT,
    TEACHER_RUN_ID,
    TEACHER_RUN_IDEA,
    TEACHER_RUN_INPUT_ID,
    TEACHER_RUN_PROFILE_REF,
    TEACHER_RUN_REVISION,
    TEACHER_RUN_STATE,
)
from tools.seed.stage_common import (
    StageError,
    StageResult,
    run_stage_main,
    seed_principal,
    stage_key,
)

LessonServiceFactory = Callable[[Session], LessonLibraryService]


def _lesson_key(suffix: str) -> str:
    return stage_key("s11", suffix)


def _teacher_run_cancel_key() -> str:
    return stage_key("s11", TEACHER_RUN_CANCEL_KEY)


def _build_lesson_service(session: Session) -> LessonLibraryService:
    """Build the service without storage/parser/scanner adapters; this stage only authors forms."""

    # LessonLibraryService requires these ports for upload operations, but create_lesson,
    # create_access_grant and decide_access_grant do not call them. No external I/O is available
    # to this stage.
    return LessonLibraryService(
        session,
        storage=cast(ObjectStoragePort, None),
        parser=cast(LessonDocumentParser, None),
        scanner=cast(MalwareScanner, None),
    )


def teacher_run_insert_rows() -> tuple[dict[str, Any], dict[str, Any]]:
    """Rows needed for the fixture run before the real Teacher cancel command accepts it."""

    context = dict(TEACHER_CONTEXT_SNAPSHOT)
    context_sha256 = data.sha256_json(context)
    actor_ref = data.principal_scope_ref(data.SEED_ISSUER, TEACHER_A1)
    run_row = {
        "run_id": TEACHER_RUN_ID,
        "actor_scope_kind": "ORGANIZATION",
        "actor_scope_ref": ORG_A,
        "profile_ref": TEACHER_RUN_PROFILE_REF,
        "child_age_months": 36,
        "run_state": TEACHER_RUN_STATE,
        "revision": TEACHER_RUN_REVISION,
        "version": 1,
        "retryable": False,
        "job_state": None,
        "active_owner_parent_account_id": None,
        "current_input_revision": 1,
        "created_at": TEACHER_RUN_CREATED_AT,
        "updated_at": TEACHER_RUN_CREATED_AT,
    }
    input_row = {
        "run_input_id": TEACHER_RUN_INPUT_ID,
        "run_id": TEACHER_RUN_ID,
        "input_revision": 1,
        "typed_idea": TEACHER_RUN_IDEA,
        "idea_source": "TEXT",
        "source_profile_revision_ref": TEACHER_PROFILE_REVISION_REF,
        "context_revision": 1,
        "context_snapshot": context,
        "context_snapshot_sha256": context_sha256,
        "context_confirmed_by": actor_ref,
        "context_confirmed_at": TEACHER_RUN_CREATED_AT,
        "created_at": TEACHER_RUN_CREATED_AT,
    }
    return run_row, input_row


def _insert_teacher_run(session_factory: Any) -> None:
    run_row, input_row = teacher_run_insert_rows()
    with session_factory.begin() as session:
        session.execute(
            pg_insert(story_tables.story_runs)
            .values(**run_row)
            .on_conflict_do_nothing(index_elements=[story_tables.story_runs.c.run_id])
        )
        session.execute(
            pg_insert(story_tables.run_inputs)
            .values(**input_row)
            .on_conflict_do_nothing(index_elements=[story_tables.run_inputs.c.run_input_id])
        )


def _teacher_cancel_service(
    session: Session, principal: VerifiedPrincipal
) -> ParentStoryRunService:
    identity = session.get(AdultIdentityModel, TEACHER_A1)
    if (
        identity is None
        or identity.state != "active"
        or identity.account_role != "teacher"
        or identity.issuer != principal.issuer
    ):
        raise StageError("S11_TEACHER_IDENTITY_MISSING")
    actor = RunActor(kind=RunActorKind.TEACHER, account_id=identity.account_id)
    repository = SqlParentStoryRunRepository(
        session,
        actor=actor,
        teacher_access=SqlTeacherRunAccess(session),
    )
    return ParentStoryRunService(repository, SqlParentStoryProfileLookup(session))


def cancel_teacher_run(session_factory: Any) -> ParentStoryLifecycleRecord:
    """Insert the synthetic organization fixture, then cancel it through T-13a."""

    _insert_teacher_run(session_factory)
    principal = seed_principal(TEACHER_A1)
    with session_factory() as session:
        service = _teacher_cancel_service(session, principal)
        result = cancel_teacher_run_command(service, principal)
    return result


def cancel_teacher_run_command(
    service: ParentStoryRunService, principal: VerifiedPrincipal
) -> ParentStoryLifecycleRecord:
    """Call T-13a with the stable revision and idempotency key, without route or HTTP wiring."""

    try:
        result = cast(
            ParentStoryLifecycleRecord,
            service.cancel_run(
                principal=principal,
                run_id=TEACHER_RUN_ID,
                expected_revision=TEACHER_RUN_REVISION,
                idempotency_key=_teacher_run_cancel_key(),
            ),
        )
    except (ParentStoryRunError, ParentStoryRunServiceError):
        raise StageError("S11_TEACHER_CANCEL_FAILED") from None
    if result.run_state != "DELETE_PENDING":
        raise StageError("S11_TEACHER_CANCEL_STATE_INVALID")
    return result


def _create_public_review_request(
    service: LessonLibraryService,
    *,
    lesson_id: str,
    version_id: str,
    actor: str,
    lesson_key: str,
) -> str:
    grant = service.create_access_grant(
        organization_id=ORG_A,
        lesson_id=lesson_id,
        actor=actor,
        version_id=version_id,
        audience_kind="PUBLIC",
        audience_ref=None,
        capability="VIEW",
        expires_at=None,
        idempotency_key=_lesson_key(f"lesson-{lesson_key}-submit-review"),
    )
    return str(grant["access_grant_id"])


def _create_private_grant(
    service: LessonLibraryService,
    *,
    lesson_id: str,
    version_id: str,
    actor: str,
    lesson_key: str,
    audience_kind: str,
    audience_ref: str,
    receipt_suffix: str,
) -> dict[str, Any]:
    return service.create_access_grant(
        organization_id=ORG_A,
        lesson_id=lesson_id,
        actor=actor,
        version_id=version_id,
        audience_kind=audience_kind,
        audience_ref=audience_ref,
        capability="VIEW",
        expires_at=None,
        idempotency_key=_lesson_key(receipt_suffix),
    )


def seed_lesson_shares(
    session_factory: Any,
    *,
    service_factory: LessonServiceFactory = _build_lesson_service,
) -> None:
    """Create three new lessons and use LessonLibraryService for review and sharing."""

    with session_factory() as session:
        service = service_factory(session)
        for spec in PRIVATE_SHARE_SPECS:
            lesson_key = spec["lesson_key"]
            actor = spec["author"]
            try:
                lesson = service.create_lesson(
                    organization_id=ORG_A,
                    actor=actor,
                    content=LessonContentInputV1.model_validate(LESSON_CONTENTS[lesson_key]),
                    visibility="PRIVATE",
                    idempotency_key=_lesson_key(f"lesson-{lesson_key}-create"),
                )
                lesson_id = str(lesson["lesson_id"])
                version_id = str(lesson["current_version"]["version_id"])

                if lesson_key in REVIEW_REQUEST_LESSONS:
                    public_review_grant_id = _create_public_review_request(
                        service,
                        lesson_id=lesson_id,
                        version_id=version_id,
                        actor=actor,
                        lesson_key=lesson_key,
                    )
                    if lesson_key == "sunflower":
                        service.decide_access_grant(
                            organization_id=ORG_A,
                            grant_id=public_review_grant_id,
                            actor=MANAGER_A,
                            expected_revision=1,
                            decision="REQUEST_CHANGES",
                            reason=REVIEW_CHANGE_REASON,
                            idempotency_key=_lesson_key("lesson-sunflower-request-changes"),
                        )

                primary_grant = _create_private_grant(
                    service,
                    lesson_id=lesson_id,
                    version_id=version_id,
                    actor=actor,
                    lesson_key=lesson_key,
                    audience_kind=spec["audience_kind"],
                    audience_ref=spec["audience_ref"],
                    receipt_suffix={
                        "chicken": "lesson-chicken-school-grant",
                        "sailing": "lesson-sailing-parent-invite",
                        "sunflower": "lesson-sunflower-parent-group-grant",
                    }[lesson_key],
                )
                if primary_grant["lesson_id"] != lesson_id:
                    raise StageError("S11_LESSON_GRANT_MISMATCH")

                if lesson_key == "sailing":
                    # A direct PRINCIPAL share is correctly stored as INVITED. The active group
                    # grant to seed-pg-a-1 (whose only active member is p1) gives the requested
                    # SELECTED_AUDIENCE visibility without directly rewriting derived state.
                    group_grant = _create_private_grant(
                        service,
                        lesson_id=lesson_id,
                        version_id=version_id,
                        actor=actor,
                        lesson_key=lesson_key,
                        audience_kind="PARENT_GROUP",
                        audience_ref=PARENT_GROUP_A1,
                        receipt_suffix="lesson-sailing-parent-group-grant",
                    )
                    if group_grant["lesson_id"] != lesson_id:
                        raise StageError("S11_LESSON_GRANT_MISMATCH")
            except LessonLibraryError:
                raise StageError("S11_LESSON_COMMAND_FAILED") from None


def _seeded_lesson_ids() -> Any:
    current_titles = LIBRARY_VERSIONS.c.content_json["title"].astext.in_(LESSON_TITLES)
    return (
        select(LIBRARY_ITEMS.c.lesson_id)
        .select_from(
            LIBRARY_ITEMS.join(
                LIBRARY_VERSIONS,
                LIBRARY_ITEMS.c.current_version_id == LIBRARY_VERSIONS.c.version_id,
            )
        )
        .where(
            LIBRARY_ITEMS.c.organization_id == ORG_A,
            LIBRARY_ITEMS.c.created_by.in_({spec["author"] for spec in PRIVATE_SHARE_SPECS}),
            current_titles,
        )
    )


def _seeded_version_ids() -> Any:
    return select(LIBRARY_VERSIONS.c.version_id).where(
        LIBRARY_VERSIONS.c.lesson_id.in_(_seeded_lesson_ids())
    )


def _lesson_receipt_keys() -> tuple[str, ...]:
    return tuple(_lesson_key(key) for key in LESSON_RECEIPT_KEYS)


def _story_receipt_key_hash() -> str:
    return hashlib.sha256(_teacher_run_cancel_key().encode("utf-8")).hexdigest()


def count_stage_rows(connection: Connection) -> dict[str, int]:
    """Count the S11 lessons, their service receipts and the one lifecycle fixture run."""

    def count(statement: Any) -> int:
        return int(connection.execute(statement).scalar_one())

    item_count = count(
        select(func.count())
        .select_from(LIBRARY_ITEMS)
        .where(LIBRARY_ITEMS.c.lesson_id.in_(_seeded_lesson_ids()))
    )
    version_count = count(
        select(func.count())
        .select_from(LIBRARY_VERSIONS)
        .where(LIBRARY_VERSIONS.c.version_id.in_(_seeded_version_ids()))
    )
    activity_count = count(
        select(func.count())
        .select_from(VERSION_ACTIVITIES)
        .where(VERSION_ACTIVITIES.c.version_id.in_(_seeded_version_ids()))
    )
    grant_count = count(
        select(func.count())
        .select_from(ACCESS_GRANTS)
        .where(ACCESS_GRANTS.c.lesson_id.in_(_seeded_lesson_ids()))
    )
    lesson_receipt_count = count(
        select(func.count())
        .select_from(LESSON_COMMAND_RECEIPTS)
        .where(
            LESSON_COMMAND_RECEIPTS.c.organization_id == ORG_A,
            LESSON_COMMAND_RECEIPTS.c.idempotency_key.in_(_lesson_receipt_keys()),
        )
    )
    run_count = count(
        select(func.count())
        .select_from(story_tables.story_runs)
        .where(story_tables.story_runs.c.run_id == TEACHER_RUN_ID)
    )
    input_count = count(
        select(func.count())
        .select_from(story_tables.run_inputs)
        .where(story_tables.run_inputs.c.run_id == TEACHER_RUN_ID)
    )
    story_receipt_count = count(
        select(func.count())
        .select_from(story_tables.story_command_receipts)
        .where(
            story_tables.story_command_receipts.c.actor_scope_kind == "ORGANIZATION",
            story_tables.story_command_receipts.c.actor_scope_ref
            == data.principal_scope_ref(data.SEED_ISSUER, TEACHER_A1),
            story_tables.story_command_receipts.c.operation == "CANCEL_RUN",
            story_tables.story_command_receipts.c.idempotency_scope_kind == "STORY_RUN",
            story_tables.story_command_receipts.c.idempotency_scope_ref == TEACHER_RUN_ID,
            story_tables.story_command_receipts.c.idempotency_key_sha256
            == _story_receipt_key_hash(),
        )
    )
    return {
        "lesson_library_items_s11": item_count,
        "lesson_library_versions_s11": version_count,
        "lesson_version_activities_s11": activity_count,
        "lesson_access_grants_s11": grant_count,
        "lesson_command_receipts_s11": lesson_receipt_count,
        "story_runs_s11": run_count,
        "story_run_inputs_s11": input_count,
        "story_command_receipts_s11": story_receipt_count,
    }


def run_s11(engine: Engine) -> StageResult:
    """Seed the cancel/share fixtures and return S11-owned counts."""

    with engine.connect() as connection:
        before = count_stage_rows(connection)
    session_factory = create_core_session_factory(engine)
    try:
        cancel_teacher_run(session_factory)
        seed_lesson_shares(session_factory)
    except StageError:
        raise
    except SQLAlchemyError:
        raise StageError("S11_DATABASE_ERROR") from None
    except Exception:
        raise StageError("S11_STAGE_FAILED") from None
    with engine.connect() as connection:
        after = count_stage_rows(connection)
    return StageResult(name="s11_org_run_shares", before=before, after=after, expected=EXPECTED)


def main() -> int:
    return run_stage_main(run_s11, stage="s11")


if __name__ == "__main__":
    raise SystemExit(main())
