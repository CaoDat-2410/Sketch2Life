"""Offline illustrated storytelling proof; independent of original-pixel reconstruction.

Inputs are authored, versioned JSON illustrations and simulated speech beats.
This module neither generates content nor verifies production Gate A/B approval.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Literal

import numpy as np
from PIL import Image, ImageDraw
from pydantic import BaseModel, ConfigDict, Field, model_validator

Point = tuple[float, float]
PAPER = (253, 251, 245)
INK = (65, 59, 58)
WORLD = (1120, 520)


class Line(BaseModel):
    model_config = ConfigDict(extra="forbid")
    points: tuple[Point, ...] = Field(min_length=2)
    width: float = Field(default=2.4, gt=0, le=48)


class Pigment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    region_id: str
    polygon: tuple[Point, ...] = Field(min_length=3)
    color: tuple[int, int, int]
    brush: Line


class Illustration(BaseModel):
    model_config = ConfigDict(extra="forbid")
    object_id: str
    source_image_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    provenance: Literal["LOCAL_AUTHORED_SOURCE_INSPIRED", "LOCAL_AUTHORED_STORY_ADDITION"]
    identity_notes: str
    outline: tuple[Line, ...]
    detail: tuple[Line, ...]
    colors: tuple[Pigment, ...]


class Beat(BaseModel):
    model_config = ConfigDict(extra="forbid")
    beat_id: str
    start: float = Field(ge=0)
    end: float = Field(gt=0)
    narration: str
    object_ids: tuple[str, ...] = Field(min_length=1)
    camera: tuple[float, float, float]


class StorySlice(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Literal["illustrated-story-slice/1.0"] = "illustrated-story-slice/1.0"
    approval: Literal["LOCAL_DEMO_REQUEST_APPROVAL"] = "LOCAL_DEMO_REQUEST_APPROVAL"
    cue_kind: Literal["SIMULATED_TEXT_NO_AUDIO"] = "SIMULATED_TEXT_NO_AUDIO"
    assets: tuple[Illustration, ...]
    beats: tuple[Beat, ...]

    @model_validator(mode="after")
    def validate_timeline(self):
        ids = [a.object_id for a in self.assets]
        if len(ids) != len(set(ids)) or not 3 <= len(self.beats) <= 4:
            raise ValueError("INVALID_ASSET_IDS_OR_BEAT_COUNT")
        seen: set[str] = set()
        cursor = 0.0
        for beat in self.beats:
            if beat.start != cursor or beat.end <= beat.start:
                raise ValueError("NONCONTIGUOUS_BEAT_TIMELINE")
            if not 1 <= beat.camera[2] <= 1.15:
                raise ValueError("CAMERA_ZOOM_BUDGET")
            for obj in beat.object_ids:
                if obj not in ids or obj in seen:
                    raise ValueError("MISSING_OR_REPEATED_DRAW_OBJECT")
                seen.add(obj)
            cursor = beat.end
        if seen != set(ids) or not 15 <= cursor <= 25:
            raise ValueError("UNSCHEDULED_ASSET_OR_DURATION")
        for asset in self.assets:
            regions = [r.region_id for r in asset.colors]
            if len(regions) != len(set(regions)):
                raise ValueError("DUPLICATE_COLOR_REGION")
            lines = list(asset.outline) + list(asset.detail) + [r.brush for r in asset.colors]
            for points in [line.points for line in lines] + [r.polygon for r in asset.colors]:
                if any(not (0 <= x < WORLD[0] and 0 <= y < WORLD[1]) for x, y in points):
                    raise ValueError("ILLUSTRATION_OUTSIDE_CANVAS")
        return self


def length(points: tuple[Point, ...]) -> float:
    return sum(math.dist(a, b) for a, b in zip(points, points[1:]))


def partial(points: tuple[Point, ...], fraction: float) -> list[Point]:
    remaining = length(points) * min(1.0, max(0.0, fraction))
    result = [points[0]]
    for a, b in zip(points, points[1:]):
        distance = math.dist(a, b)
        if distance > remaining:
            t = remaining / distance
            result.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
            break
        result.append(b)
        remaining -= distance
    return result


def smooth(t: float) -> float:
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


@dataclass
class Action:
    action_id: str
    beat_id: str
    object_id: str
    phase: str
    line: Line
    region: Pigment | None
    up_start: float
    down_start: float
    end: float
    up_from: Point


def schedule(story: StorySlice) -> list[Action]:
    assets = {a.object_id: a for a in story.assets}
    result = []
    last: Point = (60.0, 100.0)
    for beat in story.beats:
        # Designed illustrative beats, not time compression of source reconstructions.
        usable = beat.end - beat.start - 0.30
        for phase, offset, share in [("OUTLINE", 0.0, 0.44), ("DETAIL", 0.44, 0.18),
                                     ("COLOR", 0.62, 0.38)]:
            items = []
            for obj in beat.object_ids:
                asset = assets[obj]
                if phase == "COLOR":
                    items.extend((obj, region.brush, region) for region in asset.colors)
                else:
                    items.extend((obj, line, None) for line in getattr(asset, phase.lower()))
            if not items:
                raise ValueError("EMPTY_DRAWING_PHASE")
            budget = usable * share
            up = 0.035
            weights = [max(20.0, length(item[1].points)) for item in items]
            down_budget = budget - up * len(items)
            if down_budget < len(items) / 24:
                raise ValueError("ILLUSTRATED_TIMING_INFEASIBLE")
            cursor = beat.start + usable * offset
            # One frame minimum for each authored path; remainder follows path length.
            extra = down_budget - len(items) / 24
            for i, (obj, line, region) in enumerate(items):
                down = 1 / 24 + extra * weights[i] / sum(weights)
                result.append(Action(f"{beat.beat_id}-{phase}-{i}", beat.beat_id, obj,
                                     phase, line, region, cursor, cursor + up,
                                     cursor + up + down, last))
                cursor += up + down
                last = line.points[-1]
    return result


def line_mask(line: Line, fraction: float = 1.0, *, scale: int = 2) -> Image.Image:
    mask = Image.new("L", (WORLD[0] * scale, WORLD[1] * scale))
    points = [(x * scale, y * scale) for x, y in partial(line.points, fraction)]
    draw = ImageDraw.Draw(mask)
    width = max(1, round(line.width * scale))
    if len(points) > 1:
        draw.line(points, fill=255, width=width, joint="curve")
    radius = width / 2
    for x, y in (points[0], points[-1]):
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=255)
    return mask


class IllustratedCanvas:
    """Monotonic persistent pigment/ink; only the traveled path admits pixels."""

    def __init__(self, story: StorySlice, scale: int = 2):
        self.story, self.actions, self.scale = story, schedule(story), scale
        self.size = (WORLD[0] * scale, WORLD[1] * scale)
        self.ink = np.zeros((self.size[1], self.size[0]), dtype=np.uint8)
        self.paint = np.full((*self.ink.shape, 3), PAPER, dtype=np.uint8)
        self.index, self.last_time = 0, -1.0
        self.region_masks: dict[str, np.ndarray] = {}
        self.textures: dict[str, np.ndarray] = {}
        self.coverage: dict[str, np.ndarray] = {}
        rng = np.random.default_rng(29)
        noise = rng.normal(0, 2.0, self.ink.shape)
        yy, xx = np.indices(self.ink.shape)
        grain = noise + 2.4 * np.sin(xx * 0.8 + yy * 1.25)
        self.region_checks = {}
        for action in self.actions:
            if action.region is None:
                continue
            mask = Image.new("L", self.size)
            ImageDraw.Draw(mask).polygon([(x * scale, y * scale)
                                         for x, y in action.region.polygon], fill=255)
            allowed = np.asarray(mask) > 0
            footprint = np.asarray(line_mask(action.line, scale=scale)) > 0
            missing = int((allowed & ~footprint).sum())
            self.region_checks[action.action_id] = missing
            if missing:
                raise ValueError(f"NEEDS_AUTHORING_REVIEW:{action.action_id}:{missing}")
            self.region_masks[action.action_id] = allowed
            self.coverage[action.action_id] = np.zeros_like(allowed)
            color = np.array(action.region.color, dtype=float)
            # New illustrated pigment, explicitly not original source pixels.
            self.textures[action.action_id] = np.clip(color + grain[:, :, None], 0, 255).astype(
                np.uint8)

    def apply(self, action: Action, fraction: float):
        mask = np.asarray(line_mask(action.line, fraction, scale=self.scale))
        if action.region is None:
            self.ink = np.maximum(self.ink, mask)
        else:
            admitted = (mask > 0) & self.region_masks[action.action_id]
            self.coverage[action.action_id] |= admitted
            self.paint[admitted] = self.textures[action.action_id][admitted]

    def at(self, seconds: float) -> tuple[Image.Image, dict]:
        if seconds < self.last_time:
            raise ValueError("MONOTONIC_TIMELINE_REQUIRED")
        self.last_time = seconds
        while self.index < len(self.actions) and seconds >= self.actions[self.index].end:
            self.apply(self.actions[self.index], 1.0)
            self.index += 1
        trace: dict = {"state": "REST", "tip": None, "action_id": None, "phase": None}
        if self.index < len(self.actions):
            action = self.actions[self.index]
            trace.update(action_id=action.action_id, object_id=action.object_id,
                         phase=action.phase, beat_id=action.beat_id)
            if action.up_start <= seconds < action.down_start:
                t = smooth((seconds - action.up_start) / (action.down_start - action.up_start))
                trace.update(state="UP", tip=[a + t * (b - a) for a, b in
                                             zip(action.up_from, action.line.points[0])])
            elif action.down_start <= seconds < action.end:
                # Linear arc-length with short explicit pen lifts; no phase opacity.
                t = (seconds - action.down_start) / (action.end - action.down_start)
                self.apply(action, t)
                trace.update(state="DOWN", tip=partial(action.line.points, t)[-1], fraction=t)
        canvas = Image.fromarray(self.paint)
        canvas.paste(INK, (0, 0, *self.size), Image.fromarray(self.ink))
        return canvas, trace


def camera_at(story: StorySlice, seconds: float) -> tuple[float, float, float]:
    previous = (560.0, 260.0, 1.0)
    for beat in story.beats:
        if seconds < beat.end:
            t = smooth((seconds - beat.start) / 0.9)
            current = tuple(a + (b - a) * t for a, b in zip(previous, beat.camera))
            if seconds > story.beats[-1].end - 1.5:
                t = smooth((seconds - (story.beats[-1].end - 1.5)) / 1.5)
                return tuple(a + (b - a) * t for a, b in zip(current, (560, 260, 1)))
            return current
        previous = beat.camera
    return 560.0, 260.0, 1.0


def pack_digest(story: StorySlice) -> str:
    return hashlib.sha256(story.model_dump_json().encode()).hexdigest()
