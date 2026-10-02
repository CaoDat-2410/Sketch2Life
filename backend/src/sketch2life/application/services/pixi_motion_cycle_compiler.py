"""Deterministic subject-family cycle selection and collision-safe stage placement."""

from __future__ import annotations

from dataclasses import dataclass

from sketch2life.contracts.schemas.pixi_show import (
    PixiBehaviorClassV1,
    PixiShowPlanV1,
    PixiSubjectHintV1,
)


@dataclass(frozen=True, slots=True)
class PixiMotionCycleSelection:
    cycle_id: str | None
    start_seconds: float
    end_seconds: float
    x: float | None
    y: float | None
    reason_code: str | None = None


_CYCLE_BY_SUBJECT_BEHAVIOR: dict[tuple[PixiSubjectHintV1, PixiBehaviorClassV1], str] = {
    (PixiSubjectHintV1.BIRD, PixiBehaviorClassV1.WALKER): "motion.walker-avian.v1",
    (PixiSubjectHintV1.BIRD, PixiBehaviorClassV1.FLYER): "motion.flyer-songbird.v2",
    (PixiSubjectHintV1.INSECT, PixiBehaviorClassV1.FLYER): "motion.flyer-insect.v1",
    (PixiSubjectHintV1.INSECT, PixiBehaviorClassV1.CRAWLER): "motion.crawler-insect.v1",
    (PixiSubjectHintV1.FISH, PixiBehaviorClassV1.SWIMMER): "motion.swimmer-goldfish.v1",
    (PixiSubjectHintV1.QUADRUPED, PixiBehaviorClassV1.WALKER): "motion.walker-corgi.v2",
    (PixiSubjectHintV1.BIPED, PixiBehaviorClassV1.WALKER): "motion.walker-child.v2",
    (PixiSubjectHintV1.VEHICLE, PixiBehaviorClassV1.ROLLER): "motion.roller-car.v1",
}
_STAGE_CANDIDATES = ((0.18, 0.18), (0.82, 0.18), (0.18, 0.82), (0.82, 0.82))


def select_motion_cycle(plan: PixiShowPlanV1) -> PixiMotionCycleSelection:
    """Choose only a reviewed registry cycle; never infer a class from a filename or free text."""
    cycle_id = _CYCLE_BY_SUBJECT_BEHAVIOR.get((plan.visual_subject_hint_id, plan.behavior_class))
    if cycle_id is None:
        return PixiMotionCycleSelection(None, 0, 0, None, None)

    region = plan.source_subject_region
    supplemental_points = tuple(
        (beat.x, beat.y) for beat in plan.beats if beat.target_role == "SUPPLEMENTAL_ASSET"
    )
    point = next(
        (
            (x, y)
            for x, y in _STAGE_CANDIDATES
            if not (
                region.x - 0.14 <= x <= region.x + region.width + 0.14
                and region.y - 0.14 <= y <= region.y + region.height + 0.14
            )
            and all(
                (x - other_x) ** 2 + (y - other_y) ** 2 >= 0.22**2
                for other_x, other_y in supplemental_points
            )
        ),
        None,
    )
    if point is None:
        return PixiMotionCycleSelection(
            None,
            0,
            0,
            None,
            None,
            "NO_SAFE_PLACEMENT",
        )
    return PixiMotionCycleSelection(
        cycle_id=cycle_id,
        start_seconds=0,
        end_seconds=min(6, plan.duration_seconds - 2),
        x=point[0],
        y=point[1],
    )


__all__ = ["PixiMotionCycleSelection", "select_motion_cycle"]
