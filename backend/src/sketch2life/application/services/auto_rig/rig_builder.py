"""Deterministic template rigging and bounded motion planning."""

from __future__ import annotations

import math
import re
import unicodedata
from collections.abc import Iterable
from typing import Literal

from sketch2life.contracts.schemas.auto_rig import (
    RigArchetype,
    RigBoneV1,
    RigDefinitionV1,
    RigDeliveryTier,
    RigInfluenceV1,
    RigTriangleV1,
    RigVertexV1,
    RigVertexWeightsV1,
)
from sketch2life.contracts.schemas.p1_experience import VersionedRefV1
from sketch2life.contracts.schemas.renderer_v2 import (
    BoneKeyframeV2,
    BoneMotionTrackV2,
    BonePoseV2,
    VisualAnimationPlanV2,
)
from sketch2life.contracts.schemas.scene_exploration import SourceRegionV1

_ALIASES: dict[RigArchetype, tuple[str, ...]] = {
    RigArchetype.BUTTERFLY: ("butterfly", "buom", "con buom"),
    RigArchetype.BIRD: ("bird", "chim", "con chim"),
    RigArchetype.FLOWER: ("flower", "hoa", "bong hoa"),
    RigArchetype.TREE_BRANCH: (
        "tree",
        "branch",
        "cay",
        "canh cay",
        "chiec la",
        "la cay",
        "leaf",
    ),
    RigArchetype.FISH: ("fish", "ca", "con ca"),
    RigArchetype.BIPED: (
        "person",
        "human",
        "child",
        "boy",
        "girl",
        "nguoi",
        "em be",
        "be trai",
        "be gai",
    ),
    RigArchetype.RIGID: (
        "car",
        "house",
        "boat",
        "bicycle",
        "xe",
        "nha",
        "thuyen",
        "do choi",
    ),
}


def _plain(value: str) -> str:
    folded = unicodedata.normalize("NFD", value.casefold())
    return " ".join("".join(ch for ch in folded if unicodedata.category(ch) != "Mn").split())


def classify_archetype(label: str, semantic_tags: Iterable[str] = ()) -> RigArchetype:
    haystack = " ".join((_plain(label), *(_plain(tag) for tag in semantic_tags)))
    for archetype, aliases in _ALIASES.items():
        if any(re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", haystack) for alias in aliases):
            return archetype
    organic_markers = (
        "animal",
        "plant",
        "nature",
        "insect",
        "dong vat",
        "thuc vat",
        "tu nhien",
    )
    if any(marker in haystack for marker in organic_markers):
        return RigArchetype.GENERIC_ORGANIC
    if haystack.strip():
        return RigArchetype.UNKNOWN
    return RigArchetype.UNKNOWN


def _bones(archetype: RigArchetype) -> tuple[RigBoneV1, ...]:
    root = RigBoneV1(boneId="root", parentId=None, pivotX=0.5, pivotY=0.55, maxRotationDegrees=8)
    if archetype is RigArchetype.BUTTERFLY:
        return (
            root,
            RigBoneV1(
                boneId="left-wing", parentId="root", pivotX=0.48, pivotY=0.5, maxRotationDegrees=18
            ),
            RigBoneV1(
                boneId="right-wing", parentId="root", pivotX=0.52, pivotY=0.5, maxRotationDegrees=18
            ),
        )
    if archetype is RigArchetype.BIRD:
        return (
            root,
            RigBoneV1(
                boneId="head", parentId="root", pivotX=0.56, pivotY=0.3, maxRotationDegrees=10
            ),
            RigBoneV1(
                boneId="wing", parentId="root", pivotX=0.46, pivotY=0.5, maxRotationDegrees=12
            ),
        )
    if archetype in {RigArchetype.FLOWER, RigArchetype.TREE_BRANCH}:
        return (
            root,
            RigBoneV1(boneId="stem", parentId="root", pivotX=0.5, pivotY=0.8, maxRotationDegrees=8),
            RigBoneV1(
                boneId="crown", parentId="stem", pivotX=0.5, pivotY=0.3, maxRotationDegrees=10
            ),
        )
    if archetype is RigArchetype.FISH:
        return (
            root,
            RigBoneV1(
                boneId="tail", parentId="root", pivotX=0.22, pivotY=0.5, maxRotationDegrees=16
            ),
            RigBoneV1(
                boneId="head", parentId="root", pivotX=0.72, pivotY=0.48, maxRotationDegrees=6
            ),
        )
    if archetype is RigArchetype.BIPED:
        return (
            root,
            RigBoneV1(boneId="head", parentId="root", pivotX=0.5, pivotY=0.2, maxRotationDegrees=8),
            RigBoneV1(
                boneId="left-leg", parentId="root", pivotX=0.42, pivotY=0.72, maxRotationDegrees=10
            ),
            RigBoneV1(
                boneId="right-leg", parentId="root", pivotX=0.58, pivotY=0.72, maxRotationDegrees=10
            ),
        )
    return (root,)


def build_template_rig(
    *, archetype: RigArchetype, source_region: SourceRegionV1, grid_size: int = 5
) -> RigDefinitionV1:
    if grid_size < 2 or grid_size > 16:
        raise ValueError("grid size must be between 2 and 16")
    vertices: list[RigVertexV1] = []
    for row in range(grid_size):
        v = row / (grid_size - 1)
        for column in range(grid_size):
            u = column / (grid_size - 1)
            vertices.append(RigVertexV1(x=u, y=v, u=u, v=v))
    triangles: list[RigTriangleV1] = []
    for row in range(grid_size - 1):
        for column in range(grid_size - 1):
            top_left = row * grid_size + column
            top_right = top_left + 1
            bottom_left = top_left + grid_size
            bottom_right = bottom_left + 1
            triangles.extend(
                (
                    RigTriangleV1(a=top_left, b=bottom_left, c=top_right),
                    RigTriangleV1(a=top_right, b=bottom_left, c=bottom_right),
                )
            )
    bones = _bones(archetype)
    weights = tuple(
        RigVertexWeightsV1(
            vertexIndex=index,
            influences=_influences(archetype, vertex.u, vertex.v, bones),
        )
        for index, vertex in enumerate(vertices)
    )
    return RigDefinitionV1(
        contractName="RigDefinitionV1",
        contractVersion="1.0",
        archetype=archetype,
        sourceRegion=source_region,
        vertices=tuple(vertices),
        triangles=tuple(triangles),
        bones=bones,
        weights=weights,
    )


def _influences(
    archetype: RigArchetype,
    u: float,
    v: float,
    bones: tuple[RigBoneV1, ...],
) -> tuple[RigInfluenceV1, ...]:
    if len(bones) == 1:
        return (RigInfluenceV1(boneId="root", weight=1),)
    selected = "root"
    strength = 0.72
    if archetype is RigArchetype.BUTTERFLY:
        selected = "left-wing" if u < 0.5 else "right-wing"
        strength = min(0.88, 0.55 + abs(u - 0.5) * 0.7)
    elif archetype is RigArchetype.BIRD:
        selected = "head" if v < 0.34 and u > 0.4 else "wing"
    elif archetype in {RigArchetype.FLOWER, RigArchetype.TREE_BRANCH}:
        selected = "crown" if v < 0.48 else "stem"
    elif archetype is RigArchetype.FISH:
        selected = "tail" if u < 0.42 else "head"
    elif archetype is RigArchetype.BIPED:
        if v < 0.34:
            selected = "head"
        elif v > 0.62:
            selected = "left-leg" if u < 0.5 else "right-leg"
        else:
            return (RigInfluenceV1(boneId="root", weight=1),)
    root_weight = round(1 - strength, 6)
    return (
        RigInfluenceV1(boneId="root", weight=root_weight),
        RigInfluenceV1(boneId=selected, weight=round(strength, 6)),
    )


def build_animation_plan(
    *,
    plan_id: str,
    session_id: str,
    experience_spec_ref: VersionedRefV1,
    package_id: str,
    archetype: RigArchetype,
    learning_bridge_vi: str,
    tier: RigDeliveryTier = RigDeliveryTier.FULL_AUTO_RIG,
) -> VisualAnimationPlanV2:
    tracks = _tracks(archetype)
    duration = (
        max(frame.at_seconds for track in tracks for frame in track.keyframes) if tracks else 4
    )
    return VisualAnimationPlanV2(
        contractName="VisualAnimationPlanV2",
        contractVersion="2.0",
        planId=plan_id,
        sessionId=session_id,
        experienceSpecRef=experience_spec_ref,
        packageId=package_id,
        archetype=archetype,
        tier=tier,
        durationSeconds=duration,
        tracks=tracks,
        learningBridgeVi=learning_bridge_vi,
        maxMotionLevel=2,
    )


def _pose(
    *, rotation: float = 0, x: float = 0, y: float = 0, sx: float = 1, sy: float = 1
) -> BonePoseV2:
    return BonePoseV2(rotationDegrees=rotation, translateX=x, translateY=y, scaleX=sx, scaleY=sy)


def _track(
    track_id: str,
    bone_id: str,
    profile: Literal["flutter", "sway", "breathe", "tilt", "swim", "step", "focus"],
    frames: tuple[tuple[float, BonePoseV2], ...],
) -> BoneMotionTrackV2:
    return BoneMotionTrackV2(
        trackId=track_id,
        boneId=bone_id,
        profile=profile,
        keyframes=tuple(BoneKeyframeV2(atSeconds=time, pose=pose) for time, pose in frames),
    )


def _tracks(archetype: RigArchetype) -> tuple[BoneMotionTrackV2, ...]:
    settle = ((0.0, _pose()), (0.8, _pose(y=-0.015)), (1.6, _pose()))
    if archetype is RigArchetype.BUTTERFLY:
        return (
            _track(
                "left-flutter",
                "left-wing",
                "flutter",
                (
                    (0, _pose()),
                    (0.55, _pose(rotation=-12, sx=0.9)),
                    (1.1, _pose()),
                    (1.65, _pose(rotation=-10, sx=0.92)),
                    (2.2, _pose()),
                ),
            ),
            _track(
                "right-flutter",
                "right-wing",
                "flutter",
                (
                    (0, _pose()),
                    (0.55, _pose(rotation=12, sx=0.9)),
                    (1.1, _pose()),
                    (1.65, _pose(rotation=10, sx=0.92)),
                    (2.2, _pose()),
                ),
            ),
            _track(
                "body-bob",
                "root",
                "breathe",
                ((0, _pose()), (1.1, _pose(y=-0.018)), (2.2, _pose())),
            ),
        )
    if archetype is RigArchetype.BIRD:
        return (
            _track(
                "bird-breathe",
                "root",
                "breathe",
                ((0, _pose()), (1.2, _pose(sx=1.015, sy=1.02)), (2.4, _pose())),
            ),
            _track(
                "head-tilt",
                "head",
                "tilt",
                ((0, _pose()), (1.1, _pose(rotation=7)), (2.2, _pose(rotation=-3)), (3.0, _pose())),
            ),
            _track(
                "wing-settle",
                "wing",
                "sway",
                ((0, _pose()), (1.5, _pose(rotation=5)), (3.0, _pose())),
            ),
        )
    if archetype in {RigArchetype.FLOWER, RigArchetype.TREE_BRANCH}:
        return (
            _track(
                "stem-sway",
                "stem",
                "sway",
                ((0, _pose()), (1.4, _pose(rotation=-4)), (2.8, _pose(rotation=4)), (4.2, _pose())),
            ),
            _track(
                "crown-sway",
                "crown",
                "sway",
                ((0, _pose()), (1.4, _pose(rotation=6)), (2.8, _pose(rotation=-5)), (4.2, _pose())),
            ),
        )
    if archetype is RigArchetype.FISH:
        return (
            _track(
                "tail-swim",
                "tail",
                "swim",
                (
                    (0, _pose()),
                    (0.7, _pose(rotation=-12)),
                    (1.4, _pose(rotation=12)),
                    (2.1, _pose(rotation=-8)),
                    (2.8, _pose()),
                ),
            ),
            _track(
                "fish-drift",
                "root",
                "swim",
                ((0, _pose()), (1.4, _pose(x=0.025, y=-0.01)), (2.8, _pose())),
            ),
        )
    if archetype is RigArchetype.BIPED:
        return (
            _track(
                "person-breathe",
                "root",
                "breathe",
                ((0, _pose()), (1.2, _pose(sy=1.015)), (2.4, _pose())),
            ),
            _track(
                "person-head",
                "head",
                "tilt",
                ((0, _pose()), (1.2, _pose(rotation=5)), (2.4, _pose())),
            ),
        )
    return (_track("gentle-focus", "root", "focus", settle),)


def validate_rig_geometry(rig: RigDefinitionV1) -> tuple[str, ...]:
    reasons: list[str] = []
    for triangle in rig.triangles:
        a, b, c = (rig.vertices[index] for index in (triangle.a, triangle.b, triangle.c))
        twice_area = (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)
        if not math.isfinite(twice_area) or abs(twice_area) < 1e-8:
            reasons.append("DEGENERATE_TRIANGLE")
            break
    if any(abs(sum(i.weight for i in item.influences) - 1) > 1e-5 for item in rig.weights):
        reasons.append("WEIGHTS_NOT_NORMALIZED")
    return tuple(reasons)


__all__ = [
    "build_animation_plan",
    "build_template_rig",
    "classify_archetype",
    "validate_rig_geometry",
]
