from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from sqlalchemy import create_engine, insert
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from sketch2life.infrastructure.lesson_library.service import LessonLibraryService
from sketch2life.infrastructure.lesson_library.tables import (
    LIBRARY_ITEMS,
    LIBRARY_VERSIONS,
    VERSION_ACTIVITIES,
)


@compiles(JSONB, "sqlite")
def _jsonb_as_json_on_sqlite(_type: Any, _compiler: Any, **_kw: Any) -> str:
    return "JSON"


@pytest.fixture
def lesson_library_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.connect() as connection:
        connection.exec_driver_sql("ATTACH DATABASE ':memory:' AS lesson")
    LIBRARY_ITEMS.create(engine)
    LIBRARY_VERSIONS.create(engine)
    VERSION_ACTIVITIES.create(engine)

    with Session(engine) as db:
        yield db
    engine.dispose()


def _seed_lesson(
    db: Session, *, lesson_id: str, state: str, updated_at: datetime,
) -> None:
    version_id = f"{lesson_id}-version"
    db.execute(
        insert(LIBRARY_ITEMS).values(
            lesson_id=lesson_id,
            organization_id="org-test",
            owner_kind="ORGANIZATION",
            created_by="teacher-test",
            state=state,
            visibility="PRIVATE",
            internal_visibility="PRIVATE",
            moderation_state="VISIBLE",
            current_version_id=version_id,
            revision=1,
            created_at=updated_at,
            updated_at=updated_at,
        )
    )
    db.execute(
        insert(LIBRARY_VERSIONS).values(
            version_id=version_id,
            lesson_id=lesson_id,
            version_no=1,
            content_json={"title": lesson_id, "topic": "Nghệ thuật"},
            structured_content_hash="a" * 64,
            review_state="DRAFT",
            authored_by="teacher-test",
            created_at=updated_at,
        )
    )


@pytest.mark.parametrize("manager", [False, True])
def test_organization_lesson_pages_exclude_archived_before_cursor_pagination(
    lesson_library_db: Session, manager: bool,
) -> None:
    db = lesson_library_db
    archived_at = datetime(2026, 11, 26, 4, tzinfo=UTC)
    newest_active_at = datetime(2026, 11, 26, 3, tzinfo=UTC)
    older_active_at = datetime(2026, 11, 26, 2, tzinfo=UTC)
    _seed_lesson(db, lesson_id="archived-newest", state="ARCHIVED", updated_at=archived_at)
    _seed_lesson(db, lesson_id="active-newest", state="ACTIVE", updated_at=newest_active_at)
    _seed_lesson(db, lesson_id="active-older", state="ACTIVE", updated_at=older_active_at)

    service = LessonLibraryService(db, storage=None, parser=None, scanner=None)  # type: ignore[arg-type]
    first = service.list_lessons(
        organization_id="org-test",
        actor="teacher-test",
        manager=manager,
        state=None,
        visibility=None,
        limit=1,
        cursor=None,
    )

    assert [item["lesson_id"] for item in first["items"]] == ["active-newest"]
    assert first["next_cursor"] is not None

    # SQLite drops timezone offsets when reading DateTime columns, so construct the
    # equivalent server cursor from the seeded aware timestamp for the next-page call.
    cursor = service._encode_cursor(newest_active_at, "active-newest")
    second = service.list_lessons(
        organization_id="org-test",
        actor="teacher-test",
        manager=manager,
        state=None,
        visibility=None,
        limit=1,
        cursor=cursor,
    )
    assert [item["lesson_id"] for item in second["items"]] == ["active-older"]
    assert second["next_cursor"] is None

    archived_filter = service.list_lessons(
        organization_id="org-test",
        actor="teacher-test",
        manager=manager,
        state="ARCHIVED",
        visibility=None,
        limit=10,
        cursor=None,
    )
    assert archived_filter["items"] == []
