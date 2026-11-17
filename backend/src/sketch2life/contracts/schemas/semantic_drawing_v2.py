"""Additive local semantic drawing contract; does not migrate production V2 schemas."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sketch2life.contracts.schemas.story_strokes_v2 import ObjectStrokeV2


@dataclass(frozen=True)
class SemanticStroke:
    path: ObjectStrokeV2
    role: Literal["PRIMARY_CONTOUR", "DISTINCTIVE_DETAIL", "OPTIONAL_TEXTURE", "COLOR_REGION"]
    region_id: str
    essential: bool = True


@dataclass(frozen=True)
class DrawingBudget:
    target_seconds: float
    beat_seconds: float
    ink_speed: float = 180.0
    brush_speed: float = 300.0
    travel_speed: float = 600.0
    fps: int = 24


@dataclass(frozen=True)
class TextStoryBeat:
    beat_id: str
    object_id: str
    text: str
    budget_seconds: float
    local_demo_approved: bool
    camera_focus: tuple[float, float]
    transition: str = "DRAW_MORE"
