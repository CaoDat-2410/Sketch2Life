"""Parent activity catalog adapter over the authorized Lesson Library read model."""

from __future__ import annotations

from collections.abc import Sequence

from sketch2life.application.ports.parent_activity_catalog import (
    ParentActivityCatalogPort,
    ParentActivityLesson,
)
from sketch2life.contracts.schemas.lesson_library import ParentLessonDetailV1
from sketch2life.infrastructure.lesson_library.service import LessonLibraryService


class LessonLibraryParentActivityCatalogAdapter(ParentActivityCatalogPort):
    def __init__(self, service: LessonLibraryService) -> None:
        self._service = service

    def list_accessible_lessons(
        self, *, parent_principal_ref: str
    ) -> Sequence[ParentActivityLesson]:
        details = self._service.list_parent_activity_catalog(
            parent_principal_ref=parent_principal_ref,
            limit=500,
        )
        result: list[ParentActivityLesson] = []
        for raw in details:
            lesson = ParentLessonDetailV1.model_validate(raw)
            result.append(
                ParentActivityLesson(
                    lesson_id=lesson.lesson_id,
                    version_id=lesson.version_id,
                    version_no=lesson.version_no,
                    content_sha256=lesson.content_sha256,
                    title=lesson.title,
                    topic=lesson.topic,
                    drawing_subject=lesson.drawing_subject,
                    target_age_band_ref=lesson.target_age_band_ref,
                    target_age_band_version=lesson.target_age_band_version,
                    access_source=lesson.access_source,
                    activities=tuple(
                        item.model_dump(mode="json") for item in lesson.activities
                    ),
                )
            )
        return result


__all__ = ["LessonLibraryParentActivityCatalogAdapter"]
