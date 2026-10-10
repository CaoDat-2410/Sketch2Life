import numpy as np
import pytest
from PIL import Image

from sketch2life.contracts.schemas.semantic_drawing_v2 import DrawingBudget, TextStoryBeat
from sketch2life.infrastructure.media.semantic_drawing_engine_v2 import (
    SemanticProgress,
    SemanticStrokeStrategyV1,
    contours,
    eased,
    footprint,
    integrate_beats,
    optimize,
)


@pytest.fixture(scope="module")
def asset():
    image = Image.new("RGBA", (32, 24), (215, 125, 95, 255))
    for x in range(15, 27):
        for y in range(6, 18):
            image.putpixel((x, y), (70, 160, 190, 255))
    return SemanticStrokeStrategyV1().prepare(image, "fixture-new-id", "SOURCE_DRAWING", "a" * 64)


def test_contours_follow_actual_notched_source_boundary():
    mask = np.ones((12, 16), dtype=bool)
    mask[:5, 6:10] = False
    points = contours(mask)[0]
    assert (6, 5) in points or (10, 5) in points
    assert len(points) > 5


def test_source_bytes_are_not_modified(asset):
    before = asset.source.tobytes()
    schedule = optimize(asset, DrawingBudget(100.0, 100.0))
    SemanticProgress(asset, schedule).at(schedule["seconds"] + 1.0)
    assert before == asset.source.tobytes()


def test_color_regions_cover_all_original_pixels(asset):
    assert np.logical_or.reduce(list(asset.regions.values())).all()


def test_colored_contours_are_not_rejected_by_neutral_rgb_gate(asset):
    assert any(s.role == "PRIMARY_CONTOUR" for s in asset.strokes)
    assert np.asarray(asset.ink)[:, :, 3].sum() > 0
    assert asset.style_profile["ink_provenance"].startswith("TEMPORARY_SOURCE")


def test_final_source_rgba_exact_without_snap(asset):
    schedule = optimize(asset, DrawingBudget(100.0, 100.0))
    frame, _, masks = SemanticProgress(asset, schedule).at(schedule["seconds"] + 0.001)
    assert frame.tobytes() == asset.source.tobytes()
    assert masks["color"].all()


def test_no_early_color(asset):
    schedule = optimize(asset, DrawingBudget(100.0, 100.0))
    row = next(r for r in schedule["rows"] if r["phase"] == "DETAIL")
    _, trace, masks = SemanticProgress(asset, schedule).at(row["pen_down_start"] + 0.001)
    assert trace["phase"] == "DETAIL"
    assert not masks["color"].any()


def test_optimizer_does_not_claim_impossible_small_budget(asset):
    schedule = optimize(asset, DrawingBudget(0.01, 0.01))
    assert schedule["status"] == "TIMING_INFEASIBLE"
    assert schedule["seconds"] > 0.01
    assert schedule["lod"] == "FAST_STORY"
    assert all(s.essential for s in schedule["strokes"])


def test_lod_preserves_all_distinctive_details(asset):
    plan = optimize(asset, DrawingBudget(0.01, 0.01))
    required = {s.path.stroke_id for s in asset.strokes if s.role == "DISTINCTIVE_DETAIL"}
    assert required <= {s.path.stroke_id for s in plan["strokes"]}


def test_same_easing_drives_pen_and_actual_brush(asset):
    plan = optimize(asset, DrawingBudget(100.0, 100.0))
    row = plan["rows"][0]
    _, trace, _ = SemanticProgress(asset, plan).at(row["pen_down_seconds"] * 0.25)
    assert trace["fraction"] == pytest.approx(eased(0.25))
    stroke = plan["strokes"][0]
    tip = [round(v) for v in trace["tip"]]
    assert footprint(asset.source.size, stroke.path, trace["fraction"])[tip[1], tip[0]]


def test_pen_up_no_color_change(asset):
    plan = optimize(asset, DrawingBudget(100.0, 100.0))
    engine = SemanticProgress(asset, plan)
    row = plan["rows"][1]
    _, _, before = engine.at(row["pen_up_start"])
    _, trace, after = engine.at(row["pen_up_start"] + row["pen_up_seconds"] * 0.5)
    assert trace["state"] == "UP"
    assert np.array_equal(before["color"], after["color"])


def test_invalid_region_coverage_requires_review(asset):
    with pytest.raises(ValueError, match="NEEDS_MASK_REVIEW"):
        SemanticStrokeStrategyV1().prepare(
            asset.source,
            "other",
            "SOURCE",
            "a" * 64,
            region_overrides={"bad": np.zeros((24, 32), dtype=bool)},
        )


def test_character_automatic_detail_is_not_claimed_safe(asset):
    result = SemanticStrokeStrategyV1().prepare(
        asset.source, "person", "SOURCE", "a" * 64, protected_identity=True
    )
    assert result.review_status == "NEEDS_IDENTITY_DETAIL_REVIEW"
    assert all(s.essential for s in result.strokes)


def test_simulated_beats_are_persistent_not_server_approval(asset):
    beat = TextStoryBeat("beat-1", asset.object_id, "demo", 8.0, True, (10.0, 12.0))
    timeline = integrate_beats([beat], {asset.object_id: asset})
    assert timeline[0]["scene_state"] == "PERSIST_PREVIOUS_OBJECTS"
    assert timeline[0]["production_gate"] == "NOT_VERIFIED"
    assert timeline[0]["cue_kind"] == "SIMULATED_TEXT_NOT_AUDIO"


@pytest.mark.parametrize("transition", ["ERASE", "PAGE", "WALK"])
def test_unimplemented_story_actions_are_explicit(asset, transition):
    beat = TextStoryBeat("beat", asset.object_id, "demo", 8.0, True, (0.0, 0.0), transition)
    with pytest.raises(ValueError, match="UNSUPPORTED_ACTION"):
        integrate_beats([beat], {asset.object_id: asset})


def test_unapproved_narration_never_renders(asset):
    beat = TextStoryBeat("beat", asset.object_id, "demo", 8.0, False, (0.0, 0.0))
    with pytest.raises(ValueError, match="NEEDS_APPROVAL"):
        integrate_beats([beat], {asset.object_id: asset})


@pytest.mark.parametrize("budget", [0.0, -1.0, float("nan"), float("inf")])
def test_invalid_budget_fails(asset, budget):
    with pytest.raises(ValueError, match="TIMING_INFEASIBLE"):
        optimize(asset, DrawingBudget(budget, 8.0))


def test_no_easing_random_jitter():
    assert eased(0.0) == 0.0
    assert eased(1.0) == 1.0
    assert eased(0.5) == 0.5
    assert eased(0.25) < 0.25


def test_color_paths_are_clipped_to_regions(asset):
    plan = optimize(asset, DrawingBudget(100.0, 100.0))
    engine = SemanticProgress(asset, plan)
    for s in plan["strokes"]:
        if s.path.phase == "COLOR":
            assert not (engine.admit(s, 1.0) & ~asset.regions[s.region_id]).any()
