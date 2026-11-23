"""Read port: which plan is the CURRENT approved plan of a lesson occurrence (V4-A OPEN-A D8).

Story code asks it one question, read-only: "is the plan a Teacher run was pinned to still the
approved plan?" (SRS l.386, l.2690-2699). Lesson owns the answer; Story never writes a Lesson row
and never imports a Lesson table. The adapter lives in the infrastructure layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ApprovedPlanRef:
    """The approved plan of an occurrence: the id of its revision row and its revision number."""

    plan_revision_id: str
    revision_no: int


class ApprovedPlanReadPort(Protocol):
    def approved_plan(self, occurrence_ref: str) -> ApprovedPlanRef | None:
        """The current approved plan of the occurrence, or ``None`` when it has none."""
        ...


__all__ = ["ApprovedPlanReadPort", "ApprovedPlanRef"]
