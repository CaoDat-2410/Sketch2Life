"""Framework-independent lesson occurrence rules (FEAT-066 goal v3, T-3a)."""

from sketch2life.domain.lesson_occurrences.model import (
    AccessOutcome,
    AssignmentFact,
    LessonOccurrenceRuleError,
    decide_create,
    decide_read,
    decide_write,
    normalize_title,
)

__all__ = [
    "AccessOutcome",
    "AssignmentFact",
    "LessonOccurrenceRuleError",
    "decide_create",
    "decide_read",
    "decide_write",
    "normalize_title",
]
