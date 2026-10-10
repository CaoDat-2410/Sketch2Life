"""Versioned, prototype-only world and scene-state contracts for story video V2."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Digest = str
Box = tuple[float, float, float, float]


class ReviewedEventV2(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    event_id: str = Field(pattern=r"^event-[a-z0-9-]+$")
    segment_id: str = Field(pattern=r"^segment-[1-9][0-9]*$")
    approved_fact_ids: tuple[str, ...] = Field(min_length=1)
    confirmed_anchor_ids: tuple[str, ...] = Field(min_length=1)
    source_quote: str = Field(min_length=1)
    mapping_rule: Literal["EXPLICIT_REVIEWED_EVENT", "EXACT_APPROVED_QUOTE"]
    approval_status: Literal["APPROVED", "NEEDS_APPROVAL"]
    review_ref: str | None = None
    object_ids: tuple[str, ...] = Field(min_length=1)
    action: Literal["STATIC", "TRANSLATE", "SCALE", "ROTATE", "WALK", "RUN", "ADD_OBJECT"]
    target_positions: dict[str, tuple[float, float]] = Field(default_factory=dict)
    target_scales: dict[str, float] = Field(default_factory=dict)
    target_rotations: dict[str, float] = Field(default_factory=dict)
    camera_intent: Literal["HOLD", "PAN", "ZOOM"] = "HOLD"
    transition_intent: Literal["CUT", "CONTINUE"] = "CONTINUE"

    @model_validator(mode="after")
    def check_targets(self) -> ReviewedEventV2:
        if self.approval_status == "APPROVED" and not self.review_ref:
            raise ValueError("approved event requires a separate review reference")
        if not set(self.target_positions).issubset(self.object_ids):
            raise ValueError("event target references an unrelated object")
        if not set(self.target_scales).issubset(self.object_ids) or not set(
            self.target_rotations
        ).issubset(self.object_ids):
            raise ValueError("event transform references an unrelated object")
        if any(not (0 <= x <= 1 and 0 <= y <= 1) for x, y in self.target_positions.values()):
            raise ValueError("event target positions must be normalized")
        if any(not 0 < value <= 3 for value in self.target_scales.values()) or any(
            not -30 <= value <= 30 for value in self.target_rotations.values()
        ):
            raise ValueError("event transform is outside prototype limits")
        return self


class SourceObjectV2(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    object_id: str = Field(min_length=1)
    object_type: str = Field(min_length=1)
    provenance: Literal["SOURCE_DRAWING"] = "SOURCE_DRAWING"
    source_image_ref: str
    source_image_sha256: Digest = Field(pattern=r"^[a-f0-9]{64}$")
    source_mask_ref: str
    source_mask_sha256: Digest = Field(pattern=r"^[a-f0-9]{64}$")
    asset_ref: str
    asset_sha256: Digest = Field(pattern=r"^[a-f0-9]{64}$")
    bbox: Box
    appearance_colors: tuple[str, ...] = ()
    relationship_ids: tuple[str, ...] = ()
    approved_fact_ids: tuple[str, ...] = ()
    confirmed_anchor_ids: tuple[str, ...] = ()


class NarrationObjectV2(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    object_id: str = Field(min_length=1)
    object_type: str = Field(min_length=1)
    provenance: Literal["APPROVED_NARRATION"] = "APPROVED_NARRATION"
    segment_id: str
    approved_fact_ids: tuple[str, ...] = Field(min_length=1)
    requested_appearance: str = Field(min_length=1)
    requested_action: str = Field(min_length=1)
    asset_status: Literal["PENDING", "GENERATED", "APPROVED", "FAILED"] = "PENDING"


class ObjectStateV2(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    object_id: str
    visible: bool = True
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)
    scale: float = Field(default=1, gt=0, le=3)
    rotation_degrees: float = Field(default=0, ge=-30, le=30)
    z_index: int = Field(default=0, ge=0, le=100)
    pose_ref: str | None = None
    action_ref: str | None = None


class CameraStateV2(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    center_x: float = Field(default=0.5, ge=0, le=1)
    center_y: float = Field(default=0.5, ge=0, le=1)
    zoom: float = Field(default=1, ge=1, le=2)


class WorldModelV2(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    contract: Literal["StoryWorldModelV2"] = "StoryWorldModelV2"
    version: Literal["2.0"] = "2.0"
    package_hash: Digest = Field(pattern=r"^[a-f0-9]{64}$")
    source_image_ref: str
    source_image_sha256: Digest = Field(pattern=r"^[a-f0-9]{64}$")
    source_width: int = Field(gt=0)
    source_height: int = Field(gt=0)
    source_objects: tuple[SourceObjectV2, ...] = Field(min_length=1)
    narration_objects: tuple[NarrationObjectV2, ...] = ()
    events: tuple[ReviewedEventV2, ...] = Field(min_length=1)
    initial_states: tuple[ObjectStateV2, ...] = Field(min_length=1)
    background_ref: str | None = None

    @model_validator(mode="after")
    def check_world(self) -> WorldModelV2:
        sources = {obj.object_id for obj in self.source_objects}
        added = {obj.object_id for obj in self.narration_objects}
        if len(sources) != len(self.source_objects) or len(added) != len(self.narration_objects):
            raise ValueError("duplicate object ID")
        if sources & added:
            raise ValueError("source and narration object IDs overlap")
        if len({event.event_id for event in self.events}) != len(self.events):
            raise ValueError("duplicate event ID")
        if len(self.initial_states) != len(sources) or {
            state.object_id for state in self.initial_states
        } != sources:
            raise ValueError("initial states must cover source objects exactly")
        if any(not set(event.object_ids).issubset(sources | added) for event in self.events):
            raise ValueError("event references unknown object")
        if any(obj.source_image_sha256 != self.source_image_sha256 for obj in self.source_objects):
            raise ValueError("source object image hash mismatch")
        return self


class ScenePlanV2(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    scene_id: str
    order: int = Field(ge=1)
    event_ids: tuple[str, ...] = Field(min_length=1)
    segment_ids: tuple[str, ...] = Field(min_length=1)
    source_object_ids: tuple[str, ...]
    new_object_ids: tuple[str, ...]
    action: str
    starting_states: tuple[ObjectStateV2, ...]
    target_states: tuple[ObjectStateV2, ...]
    draw_order: tuple[str, ...]
    camera: CameraStateV2
    transition_intent: Literal["CUT", "CONTINUE"]
    duration_seconds: float = Field(ge=5, le=20)

    @model_validator(mode="after")
    def check_states(self) -> ScenePlanV2:
        start_ids = [state.object_id for state in self.starting_states]
        target_ids = [state.object_id for state in self.target_states]
        if (
            len(set(start_ids)) != len(start_ids)
            or len(set(target_ids)) != len(target_ids)
            or set(start_ids) != set(target_ids)
        ):
            raise ValueError("scene state identities must be unique and unchanged")
        if not set(self.draw_order).issubset(set(start_ids) | set(self.new_object_ids)):
            raise ValueError("draw order references an unknown identity")
        return self


class StoryScenePlanV2(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    contract: Literal["StoryScenePlanV2"] = "StoryScenePlanV2"
    version: Literal["2.0"] = "2.0"
    package_hash: Digest = Field(pattern=r"^[a-f0-9]{64}$")
    scenes: tuple[ScenePlanV2, ...] = Field(min_length=3, max_length=6)
    duration_seconds: float = Field(ge=40, le=60)

    @model_validator(mode="after")
    def check_continuity(self) -> StoryScenePlanV2:
        if tuple(scene.order for scene in self.scenes) != tuple(range(1, len(self.scenes) + 1)):
            raise ValueError("scene order is not contiguous")
        if abs(sum(scene.duration_seconds for scene in self.scenes) - self.duration_seconds) > .01:
            raise ValueError("scene durations do not match total")
        for left, right in zip(self.scenes, self.scenes[1:], strict=False):
            if left.target_states != right.starting_states:
                raise ValueError("scene states are not continuous")
        return self
