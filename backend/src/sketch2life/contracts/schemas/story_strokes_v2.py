"""Versioned, source-bound offline stroke and draw-timing contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ObjectStrokeV2(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    stroke_id: str
    phase: Literal["OUTLINE", "DETAIL", "COLOR"]
    points: tuple[tuple[int, int], ...] = Field(min_length=2)
    brush_width: int = Field(ge=1, le=32)
    color_rgb: tuple[int, int, int]
    pen_up_before: bool = True


class SourceObjectStrokesV2(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    contract: Literal["SourceObjectStrokesV2"] = "SourceObjectStrokesV2"
    version: Literal["2.0"] = "2.0"
    object_id: str
    source_image_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_asset_ref: str
    source_asset_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_mask_ref: str
    source_mask_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    z_index: int = Field(ge=0)
    extraction_method: Literal["MASK_BOUNDARY_AND_LOCAL_CONTRAST_V1"]
    outline_paths: tuple[ObjectStrokeV2, ...] = Field(min_length=1)
    detail_paths: tuple[ObjectStrokeV2, ...] = ()
    color_paths: tuple[ObjectStrokeV2, ...] = Field(min_length=1)
    covered_source_pixels: int = Field(gt=0)

    @model_validator(mode="after")
    def check_phase(self) -> SourceObjectStrokesV2:
        for phase, paths in (
            ("OUTLINE", self.outline_paths), ("DETAIL", self.detail_paths),
            ("COLOR", self.color_paths),
        ):
            if any(path.phase != phase for path in paths):
                raise ValueError("stroke phase mismatch")
            if any(
                not 0 <= x < self.width or not 0 <= y < self.height
                for path in paths for x, y in path.points
            ):
                raise ValueError("stroke point outside source asset")
        return self


class ScheduledStrokeV2(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    object_id: str
    stroke_id: str
    phase: Literal["OUTLINE", "DETAIL", "COLOR"]
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)
    pen_up_seconds: float = Field(ge=0)
    beat_ref: str | None = None

    @model_validator(mode="after")
    def check_time(self) -> ScheduledStrokeV2:
        if self.end_seconds <= self.start_seconds:
            raise ValueError("stroke end must follow start")
        return self


class SceneDrawScheduleV2(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    contract: Literal["SceneDrawScheduleV2"] = "SceneDrawScheduleV2"
    version: Literal["2.0"] = "2.0"
    scene_id: str
    object_order: tuple[str, ...] = Field(min_length=1)
    strokes: tuple[ScheduledStrokeV2, ...] = Field(min_length=1)
    duration_seconds: float = Field(gt=0)
    hold_seconds: float = Field(ge=0)

    @model_validator(mode="after")
    def check_schedule(self) -> SceneDrawScheduleV2:
        if self.strokes[-1].end_seconds + self.hold_seconds > self.duration_seconds + 0.001:
            raise ValueError("draw schedule exceeds scene duration")
        if len({(s.object_id, s.stroke_id) for s in self.strokes}) != len(self.strokes):
            raise ValueError("duplicate scheduled stroke")
        return self
