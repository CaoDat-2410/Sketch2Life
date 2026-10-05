"""Application-facing result for a gated Pixi cycle capability issuer."""

from __future__ import annotations

from dataclasses import dataclass

from sketch2life.contracts.schemas.pixi_motion_cycle import (
    PixiSpriteCycleReadV1,
    PixiSpriteCycleReasonCodeV1,
)


@dataclass(frozen=True, slots=True)
class PixiMotionCycleIssue:
    cycle: PixiSpriteCycleReadV1 | None
    reason_code: PixiSpriteCycleReasonCodeV1 | None = None


__all__ = ["PixiMotionCycleIssue"]
