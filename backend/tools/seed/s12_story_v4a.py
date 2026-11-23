"""Phase A Story v4a seed stage (FEAT-066 SEED-2, stage S12).

Seeds synthetic Vietnamese Phase A StoryRun shapes:
- Parent activity selections (including re-selection ``selection_no`` 1 then 2 before story start)
  and context confirmation starting the first story on ``RUN_STARTED``.
- Story revision review epochs (``review_epoch`` 1 after a spent failed generation and ``2``
  re-confirming the same revision) ending in a ``COMPLETED`` run whose ready video remains replayable.
- A run returned to ``SCRIPT_REVIEW`` after ``SAFETY_BLOCKED`` where ``story_confirmation_required``
  is true.

Reuses S1/S8 organization, teacher, and parent/child FK rows without duplicating them.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from sqlalchemy import Connection, Engine, func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from sketch2life.application.services.parent_activity_selection import (
    ParentActivitySelectionService,
)
from sketch2life.infrastructure.lesson_library.parent_activity_catalog import (
    LessonLibraryParentActivityCatalogAdapter,
)
from sketch2life.infrastructure.lesson_library.service import LessonLibraryService
from sketch2life.infrastructure.lesson_library.tables import (
    ACCESS_GRANTS,
    LIBRARY_ITEMS,
    LIBRARY_VERSIONS,
    VERSION_ACTIVITIES,
)
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    OrganizationModel,
)
from sketch2life.infrastructure.persistence.database import create_core_session_factory
from sketch2life.infrastructure.persistence.parent_models import (
    ParentChildProfileModel,
    ParentProfileRevisionModel,
)
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
)
from sketch2life.infrastructure.story_run_lite import tables as story_tables
from tools.seed import data, s12_story_v4a_data
from tools.seed.stage_common import (
    StageError,
    StageResult,
    run_stage_main,
    seed_principal,
)

SelectionServiceFactory = Callable[[Session], ParentActivitySelectionService]
RunRepoFactory = Callable[[Session], SqlParentStoryRunRepository]


class _UnusedLessonIO:
    """Catalog reads use only SQLAlchemy; asset storage/parser/scanner stay unused here."""


def _default_selection_service(session: Session) -> ParentActivitySelectionService:
    lesson_service = LessonLibraryService(
        session,
        storage=cast(Any, _UnusedLessonIO()),
        parser=cast(Any, _UnusedLessonIO()),
        scanner=cast(Any, _UnusedLessonIO()),
    )
    return ParentActivitySelectionService(
        SqlParentStoryRunRepository(session),
        LessonLibraryParentActivityCatalogAdapter(lesson_service),
    )


def _default_run_repository(session: Session) -> SqlParentStoryRunRepository:
    return SqlParentStoryRunRepository(session)


def _table_count(connection: Connection, column: Any, predicate: Any) -> int:
    return int(connection.scalar(select(func.count(column)).where(predicate)) or 0)


def count_s12_rows(connection: Connection) -> dict[str, int]:
    subjects = [spec.subject for spec in s12_story_v4a_data.PARENT_SPECS]
    profile_ids = [spec.profile_id for spec in s12_story_v4a_data.PARENT_SPECS]
    rev_ids = [spec.profile_revision_id for spec in s12_story_v4a_data.PARENT_SPECS]
    run_ids = list(s12_story_v4a_data.RUN_IDS)
    story_rev_subq = select(story_tables.story_revisions.c.story_revision_id).where(
        story_tables.story_revisions.c.run_id.in_(run_ids)
    )
    video_gen_subq = select(story_tables.video_generations.c.video_generation_id).where(
        story_tables.video_generations.c.story_run_id.in_(run_ids)
    )
    return {
        "be1_adult_identities": _table_count(
            connection, AdultIdentityModel.subject, AdultIdentityModel.subject.in_(subjects)
        ),
        "parent_child_profiles": _table_count(
            connection,
            ParentChildProfileModel.parent_profile_id,
            ParentChildProfileModel.parent_profile_id.in_(profile_ids),
        ),
        "parent_profile_revisions": _table_count(
            connection,
            ParentProfileRevisionModel.profile_revision_id,
            ParentProfileRevisionModel.profile_revision_id.in_(rev_ids),
        ),
        "lesson_library_items": _table_count(
            connection,
            LIBRARY_ITEMS.c.lesson_id,
            LIBRARY_ITEMS.c.lesson_id == s12_story_v4a_data.LESSON_ID,
        ),
        "lesson_library_versions": _table_count(
            connection,
            LIBRARY_VERSIONS.c.version_id,
            LIBRARY_VERSIONS.c.version_id == s12_story_v4a_data.LESSON_VERSION_ID,
        ),
        "lesson_version_activities": _table_count(
            connection,
            VERSION_ACTIVITIES.c.activity_id,
            VERSION_ACTIVITIES.c.version_id == s12_story_v4a_data.LESSON_VERSION_ID,
        ),
        "lesson_access_grants": _table_count(
            connection,
            ACCESS_GRANTS.c.access_grant_id,
            ACCESS_GRANTS.c.access_grant_id == s12_story_v4a_data.LESSON_GRANT_ID,
        ),
        "story_runs": _table_count(
            connection, story_tables.story_runs.c.run_id, story_tables.story_runs.c.run_id.in_(run_ids)
        ),
        "story_run_inputs": _table_count(
            connection,
            story_tables.run_inputs.c.run_input_id,
            story_tables.run_inputs.c.run_id.in_(run_ids),
        ),
        "story_understanding_revisions": _table_count(
            connection,
            story_tables.understanding_revisions.c.understanding_revision_id,
            story_tables.understanding_revisions.c.run_id.in_(run_ids),
        ),
        "story_review_decisions": _table_count(
            connection,
            story_tables.review_decisions.c.decision_id,
            story_tables.review_decisions.c.run_id.in_(run_ids),
        ),
        "story_activity_selections": _table_count(
            connection,
            story_tables.activity_selections.c.selection_id,
            story_tables.activity_selections.c.run_id.in_(run_ids),
        ),
        "story_revisions": _table_count(
            connection,
            story_tables.story_revisions.c.story_revision_id,
            story_tables.story_revisions.c.run_id.in_(run_ids),
        ),
        "story_scenes": _table_count(
            connection,
            story_tables.story_scenes.c.scene_id,
            story_tables.story_scenes.c.story_revision_id.in_(story_rev_subq),
        ),
        "story_revision_reviews": _table_count(
            connection,
            story_tables.story_revision_reviews.c.review_id,
            story_tables.story_revision_reviews.c.run_id.in_(run_ids),
        ),
        "story_video_generations": _table_count(
            connection,
            story_tables.video_generations.c.video_generation_id,
            story_tables.video_generations.c.story_run_id.in_(run_ids),
        ),
        "story_video_generation_scenes": _table_count(
            connection,
            story_tables.video_generation_scenes.c.generation_scene_id,
            story_tables.video_generation_scenes.c.video_generation_id.in_(video_gen_subq),
        ),
        "story_command_receipts": _table_count(
            connection,
            story_tables.story_command_receipts.c.receipt_id,
            story_tables.story_command_receipts.c.resource_ref.in_(run_ids),
        ),
    }


def _require_prerequisites(connection: Connection) -> None:
    org_exists = connection.scalar(
        select(OrganizationModel.organization_id).where(
            OrganizationModel.organization_id == s12_story_v4a_data.REUSED_ORG_ID
        )
    )
    teacher_exists = connection.scalar(
        select(AdultIdentityModel.subject).where(
            AdultIdentityModel.subject == s12_story_v4a_data.REUSED_TEACHER_SUBJECT
        )
    )
    parent_exists = connection.scalar(
        select(AdultIdentityModel.subject).where(
            AdultIdentityModel.subject
            == data.PARENT_SUBJECTS[s12_story_v4a_data.REUSED_PARENT_KEY]
        )
    )
    child_exists = connection.scalar(
        select(ParentChildProfileModel.parent_profile_id).where(
            ParentChildProfileModel.parent_profile_id
            == data.parent_profile_id(s12_story_v4a_data.REUSED_CHILD_KEY)
        )
    )
    if None in (org_exists, teacher_exists, parent_exists, child_exists):
        raise StageError("S12_PREREQUISITES_MISSING")


def _insert_ignore(connection: Connection, target: Any, rows: list[dict[str, Any]]) -> None:
    if rows:
        # A multi-row VALUES needs the same keys in every row, and an absent key must keep its
        # column default, so rows with different key sets go in separate statements.
        groups: dict[frozenset[str], list[dict[str, Any]]] = {}
        for row in rows:
            groups.setdefault(frozenset(row), []).append(row)
        for group in groups.values():
            connection.execute(pg_insert(target).values(group).on_conflict_do_nothing())


def _seed_static_rows(engine: Engine) -> None:
    bundle = s12_story_v4a_data.build_static_fixture_bundle()
    profiles, revisions = s12_story_v4a_data.parent_profile_rows()
    with engine.begin() as connection:
        _insert_ignore(connection, AdultIdentityModel, s12_story_v4a_data.adult_identity_rows())
        _insert_ignore(connection, ParentChildProfileModel, profiles)
        _insert_ignore(connection, ParentProfileRevisionModel, revisions)
        _insert_ignore(
            connection,
            LIBRARY_ITEMS,
            [
                {
                    "lesson_id": s12_story_v4a_data.LESSON_ID,
                    "organization_id": s12_story_v4a_data.REUSED_ORG_ID,
                    "owner_kind": "ORGANIZATION",
                    "created_by": s12_story_v4a_data.REUSED_TEACHER_SUBJECT,
                    "state": "ACTIVE",
                    "visibility": "PUBLIC",
                    "internal_visibility": "SCHOOL",
                    "moderation_state": "VISIBLE",
                    "current_version_id": s12_story_v4a_data.LESSON_VERSION_ID,
                    "revision": 1,
                    "created_at": data.SEED_TIME,
                    "updated_at": data.SEED_TIME,
                }
            ],
        )
        _insert_ignore(
            connection,
            LIBRARY_VERSIONS,
            [
                {
                    "version_id": s12_story_v4a_data.LESSON_VERSION_ID,
                    "lesson_id": s12_story_v4a_data.LESSON_ID,
                    "version_no": 1,
                    "content_json": s12_story_v4a_data.LESSON_CONTENT,
                    "structured_content_hash": s12_story_v4a_data.LESSON_CONTENT_HASH,
                    "review_state": "APPROVED",
                    "authored_by": s12_story_v4a_data.REUSED_TEACHER_SUBJECT,
                    "created_at": data.SEED_TIME,
                    "approved_at": data.SEED_TIME,
                }
            ],
        )
        _insert_ignore(
            connection,
            VERSION_ACTIVITIES,
            [
                {
                    "activity_id": activity_id,
                    "version_id": s12_story_v4a_data.LESSON_VERSION_ID,
                    "activity_order": index,
                    "activity_json": activity_payload,
                }
                for index, (activity_id, activity_payload) in enumerate(
                    zip(
                        s12_story_v4a_data.LESSON_ACTIVITY_IDS,
                        s12_story_v4a_data.LESSON_ACTIVITIES,
                        strict=True,
                    ),
                    start=1,
                )
            ],
        )
        _insert_ignore(
            connection,
            ACCESS_GRANTS,
            [
                {
                    "access_grant_id": s12_story_v4a_data.LESSON_GRANT_ID,
                    "lesson_id": s12_story_v4a_data.LESSON_ID,
                    "version_id": s12_story_v4a_data.LESSON_VERSION_ID,
                    "organization_id": s12_story_v4a_data.REUSED_ORG_ID,
                    "audience_kind": "PUBLIC",
                    "audience_ref": None,
                    "capability": "VIEW",
                    "state": "ACTIVE",
                    "granted_by": s12_story_v4a_data.REUSED_TEACHER_SUBJECT,
                    "approved_by": s12_story_v4a_data.REUSED_MANAGER_SUBJECT,
                    "approved_at": data.SEED_TIME,
                    "revision": 1,
                    "created_at": data.SEED_TIME,
                }
            ],
        )
        # runs.current_video_generation_id and video_generations.story_run_id reference each
        # other, so runs go in without the pointer and it is set after the generations exist.
        current_video_ids = {
            row["run_id"]: row["current_video_generation_id"]
            for row in bundle["runs"]
            if row.get("current_video_generation_id")
        }
        _insert_ignore(
            connection,
            story_tables.story_runs,
            [{**row, "current_video_generation_id": None} for row in bundle["runs"]],
        )
        _insert_ignore(connection, story_tables.run_inputs, bundle["run_inputs"])
        _insert_ignore(connection, story_tables.understanding_revisions, bundle["understandings"])
        _insert_ignore(connection, story_tables.story_command_receipts, bundle["receipts"])
        _insert_ignore(connection, story_tables.review_decisions, bundle["review_decisions"])
        _insert_ignore(connection, story_tables.activity_selections, bundle["activity_selections"])
        _insert_ignore(connection, story_tables.story_revisions, bundle["story_revisions"])
        _insert_ignore(connection, story_tables.story_scenes, bundle["story_scenes"])
        _insert_ignore(
            connection, story_tables.story_revision_reviews, bundle["story_revision_reviews"]
        )
        _insert_ignore(connection, story_tables.video_generations, bundle["video_generations"])
        _insert_ignore(
            connection, story_tables.video_generation_scenes, bundle["video_generation_scenes"]
        )
        for run_id, video_generation_id in current_video_ids.items():
            connection.execute(
                update(story_tables.story_runs)
                .where(
                    story_tables.story_runs.c.run_id == run_id,
                    story_tables.story_runs.c.current_video_generation_id.is_(None),
                )
                .values(current_video_generation_id=video_generation_id)
            )


def _drive_started_parent_run(
    session_factory: sessionmaker[Session],
    *,
    selection_factory: SelectionServiceFactory,
    run_repo_factory: RunRepoFactory,
) -> None:
    """Exercise two Parent activity selections before start, then confirm context to start story."""

    p6 = s12_story_v4a_data.PARENTS_BY_KEY["p6"]
    principal = seed_principal(p6.subject)
    started_run_id = s12_story_v4a_data.RUN_STARTED_ID

    with session_factory() as session:
        repo = run_repo_factory(session)
        run_state = session.scalar(
            select(story_tables.story_runs.c.run_state).where(
                story_tables.story_runs.c.run_id == started_run_id
            )
        )
        if run_state != "PREPARATION_REVIEW":
            return  # already driven: the context was confirmed and the story has started
        selection_service = selection_factory(session)
        # The seeded run starts at revision 1 and each selection adds 1, so a rerun before the
        # confirmation replays both selections with the same fingerprint.
        view = selection_service.select_activity(
            principal=principal,
            run_id=started_run_id,
            expected_revision=1,
            activity_ref=s12_story_v4a_data.activity_ref(0),
            idempotency_key=s12_story_v4a_data.SELECT_STARTED_KEY_1,
        )
        view = selection_service.select_activity(
            principal=principal,
            run_id=started_run_id,
            expected_revision=2,
            activity_ref=s12_story_v4a_data.activity_ref(1),
            idempotency_key=s12_story_v4a_data.SELECT_STARTED_KEY_2,
        )
        repo.confirm_context(
            principal=principal,
            run_id=started_run_id,
            expected_context_revision=view.context_revision,
            expected_context_snapshot_sha256=view.context_snapshot_sha256,
            idempotency_key=s12_story_v4a_data.CONFIRM_CONTEXT_STARTED_KEY,
        )


def run_s12(
    engine: Engine,
    *,
    selection_factory: SelectionServiceFactory = _default_selection_service,
    run_repo_factory: RunRepoFactory = _default_run_repository,
) -> StageResult:
    try:
        with engine.connect() as connection:
            _require_prerequisites(connection)
            before = count_s12_rows(connection)
        _seed_static_rows(engine)
        session_factory = create_core_session_factory(engine)
        _drive_started_parent_run(
            session_factory,
            selection_factory=selection_factory,
            run_repo_factory=run_repo_factory,
        )
        with engine.connect() as connection:
            after = count_s12_rows(connection)
    except StageError:
        raise
    except SQLAlchemyError as exc:
        raise StageError("S12_SEED_FAILED") from exc
    return StageResult(
        name="s12_story_v4a",
        before=before,
        after=after,
        expected=dict(s12_story_v4a_data.EXPECTED),
    )


def main() -> int:
    return run_stage_main(run_s12, stage="s12", stderr_code="S12_SEED_FAILED")


if __name__ == "__main__":
    raise SystemExit(main())
