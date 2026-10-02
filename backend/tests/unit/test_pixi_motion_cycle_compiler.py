from __future__ import annotations

from sketch2life.application.services.pixi_motion_cycle_compiler import select_motion_cycle
from sketch2life.contracts.schemas.pixi_show import PixiShowPlanV1


def _plan(
    *,
    subject_hint: str = "BIRD",
    behavior: str = "FLYER",
    region: dict[str, float] | None = None,
) -> PixiShowPlanV1:
    return PixiShowPlanV1.model_validate(
        {
            "contractName": "PixiShowPlanV1",
            "contractVersion": "1.0",
            "planId": "show-test-1",
            "sessionId": "session-test-1",
            "packageId": "rig-test-1",
            "sourceSha256": "a" * 64,
            "sourceSubjectRegion": region or {"x": 0.35, "y": 0.3, "width": 0.3, "height": 0.35},
            "experienceSpecRef": {"id": "spec-test-1", "version": 1},
            "confirmedSubjectId": "anchor-test-1",
            "visualSubjectHintId": subject_hint,
            "behaviorClass": behavior,
            "durationSeconds": 20,
            "selectedAssetIds": ["asset-flower"],
            "beats": [
                {
                    "beatId": "notice",
                    "startSeconds": 0,
                    "endSeconds": 4,
                    "action": "NOTICE",
                    "targetRole": "SOURCE_SUBJECT",
                },
                {
                    "beatId": "meet-flower",
                    "startSeconds": 5,
                    "endSeconds": 10,
                    "action": "INTERACT",
                    "targetRole": "SUPPLEMENTAL_ASSET",
                    "assetId": "asset-flower",
                    "x": 0.18,
                    "y": 0.8,
                },
                {
                    "beatId": "settle",
                    "startSeconds": 12,
                    "endSeconds": 17,
                    "action": "SETTLE",
                    "targetRole": "SOURCE_SUBJECT",
                },
            ],
            "endingStill": True,
        }
    )


def test_selects_a_compatible_cycle_away_from_source_and_static_sprites() -> None:
    selection = select_motion_cycle(_plan())

    assert selection.cycle_id == "motion.flyer-songbird.v2"
    assert selection.reason_code is None
    assert (selection.x, selection.y) == (0.18, 0.18)
    assert (selection.start_seconds, selection.end_seconds) == (0, 6)


def test_blocks_cycle_placement_when_the_source_fills_the_stage() -> None:
    selection = select_motion_cycle(
        _plan(region={"x": 0.05, "y": 0.05, "width": 0.9, "height": 0.9})
    )

    assert selection.cycle_id is None
    assert selection.reason_code == "NO_SAFE_PLACEMENT"


def test_does_not_invent_motion_when_the_show_planner_selected_stillness() -> None:
    selection = select_motion_cycle(_plan(subject_hint="PLANT", behavior="STATIONARY"))

    assert selection.cycle_id is None
    assert selection.reason_code is None
