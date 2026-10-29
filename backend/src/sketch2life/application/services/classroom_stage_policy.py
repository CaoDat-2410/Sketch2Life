"""Pure ordered-stage policy for the SRS classroom progression contract."""

from __future__ import annotations

STAGES = (
    "preparation",
    "join",
    "explore_draw",
    "assistance",
    "sharing",
    "knowledge",
    "off_screen",
    "reflection",
    "completion",
)


class StageTransitionError(ValueError):
    """A requested shared-stage transition violates the SRS progression rules."""


def require_next_stage(current: str, requested: str) -> str:
    """Accept exactly the immediate next stage; never permit skips or rewinds."""
    try:
        index = STAGES.index(current)
    except ValueError as exc:
        raise StageTransitionError("Current learning stage is not recognized") from exc
    if index + 1 >= len(STAGES) or STAGES[index + 1] != requested:
        raise StageTransitionError("Only the next ordered learning stage is allowed")
    return requested
