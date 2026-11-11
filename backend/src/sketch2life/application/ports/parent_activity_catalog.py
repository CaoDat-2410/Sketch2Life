"""Application boundary for Parent-visible, versioned lesson activities."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class ParentActivityLesson:
    lesson_id: str
    version_id: str
    version_no: int
    content_sha256: str
    title: str
    topic: str
    drawing_subject: str
    target_age_band_ref: str | None
    target_age_band_version: int | None
    access_source: str
    activities: Sequence[Mapping[str, Any]]


class ParentActivityCatalogPort(Protocol):
    def list_accessible_lessons(
        self, *, parent_principal_ref: str
    ) -> Sequence[ParentActivityLesson]:
        """List only current, approved lesson versions that the Parent may view."""


__all__ = ["ParentActivityCatalogPort", "ParentActivityLesson"]
