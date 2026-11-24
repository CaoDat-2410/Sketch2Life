"""FEAT-087 M5: keyframe compositor (K0..K5) on synthetic drawings. CPU only, no model."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

MODAL_DIR = Path(__file__).resolve().parents[1]
if str(MODAL_DIR) not in sys.path:
    sys.path.insert(0, str(MODAL_DIR))

import keyframe_compositor as kc

PAPER = (244, 240, 226)
W, H = 1280, 768


def _blob(canvas: np.ndarray, cx: int, cy: int, rx: int, ry: int, color) -> np.ndarray:
    yy, xx = np.ogrid[:H, :W]
    mask = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1.0
    canvas[mask] = color
    return mask


@pytest.fixture()
def scene():
    """Turtle (left, dark green) and leaf (right, dark red) on cream paper, 1280x768 canvas."""
    pixels = np.zeros((H, W, 3), dtype=np.uint8)
    pixels[:] = PAPER
    main_mask = _blob(pixels, 380, 400, 150, 100, (40, 90, 50))
    # inner marks so a mirror is distinguishable from the original
    pixels[360:380, 300:420][main_mask[360:380, 300:420]] = (10, 30, 15)
    pixels[420:440, 330:350][main_mask[420:440, 330:350]] = (200, 40, 40)
    leaf_mask = _blob(pixels, 900, 420, 90, 50, (120, 30, 30))
    drawing = Image.fromarray(pixels)
    main = kc.SubjectLayer("subject-main", main_mask, (230, 300, 530, 500))
    leaf = kc.SubjectLayer("sec-1", leaf_mask, (810, 370, 990, 470))
    return drawing, main, leaf


def _staging(rows):
    scenes = []
    for i, (main_end, sec) in enumerate(rows, start=1):
        scenes.append(
            {
                "scene_index": i,
                "main_end": main_end,
                "secondary_end": sec,
            }
        )
    return {"schema_version": "sketch2life.story-staging.v1", "scenes": scenes}


def _main(position="center-middle", facing="right", scale="same"):
    return {"position": position, "facing": facing, "scale": scale}


def _eat_leaf():
    keep = [{"entity_id": "sec-1", "state": "unchanged"}]
    return _staging(
        [
            (_main("left-middle"), keep),
            (_main("center-middle"), keep),
            (_main("center-middle"), keep),
            (_main("center-middle"), [{"entity_id": "sec-1", "state": "partly_gone"}]),
            (_main("center-middle"), [{"entity_id": "sec-1", "state": "gone"}]),
        ]
    )


def _ink(image: Image.Image, mask: np.ndarray | None = None) -> int:
    px = np.asarray(image.convert("RGB")).astype(int)
    lum = px @ np.array([0.299, 0.587, 0.114])
    ink = lum < (0.299 * PAPER[0] + 0.587 * PAPER[1] + 0.114 * PAPER[2]) - 40
    return int(ink[mask].sum() if mask is not None else ink.sum())


def test_fit_to_canvas_matches_the_existing_story_drawing_layout() -> None:
    drawing = Image.new("RGB", (2000, 1000), "white")
    canvas, transform = kc.fit_to_canvas(drawing)
    assert canvas.size == (1280, 768)
    # fits (1280-192, 768-192) = 1088x576 -> 1088x544, centred on the canvas
    assert transform.scale == pytest.approx(0.544)
    assert (transform.offset_x, transform.offset_y) == (96, 112)
    assert transform.box_to_canvas((0, 0, 2000, 1000)) == (96, 112, 1184, 656)


def test_k0_is_the_original_canvas_and_there_is_one_keyframe_per_scene_plus_one(
    scene,
) -> None:
    drawing, main, leaf = scene
    frames = kc.build_keyframes(
        drawing, main, [leaf], _eat_leaf(), source_facing="right"
    )
    assert len(frames) == 6
    assert np.array_equal(np.asarray(frames[0].image), np.asarray(drawing))
    assert all(frame.image.size == drawing.size for frame in frames)


def test_the_main_sprite_is_pixel_identical_to_the_original_when_only_moved(
    scene,
) -> None:
    drawing, main, leaf = scene
    frames = kc.build_keyframes(
        drawing, main, [leaf], _eat_leaf(), source_facing="right"
    )
    original = np.asarray(drawing)
    for frame in frames[1:]:
        ys, xs = np.nonzero(frame.main_mask)
        oys, oxs = np.nonzero(main.mask)
        assert len(ys) == len(oys)
        out = np.asarray(frame.image)
        shift_y, shift_x = ys.min() - oys.min(), xs.min() - oxs.min()
        assert np.array_equal(out[oys + shift_y, oxs + shift_x], original[oys, oxs]), (
            "sprite pixels changed"
        )


def test_turning_around_mirrors_the_sprite_exactly(scene) -> None:
    drawing, main, leaf = scene
    keep = [{"entity_id": "sec-1", "state": "unchanged"}]
    staging = _staging([(_main("center-middle", facing="left"), keep)] * 5)
    frame = kc.build_keyframes(drawing, main, [leaf], staging, source_facing="right")[1]
    x0, y0, x1, y1 = kc.mask_bbox(main.mask)
    original_crop = np.asarray(drawing)[y0 : y1 + 1, x0 : x1 + 1]
    fx0, fy0, fx1, fy1 = kc.mask_bbox(frame.main_mask)
    placed = np.asarray(frame.image)[fy0 : fy1 + 1, fx0 : fx1 + 1]
    crop_mask = main.mask[y0 : y1 + 1, x0 : x1 + 1]
    assert np.array_equal(
        placed[np.fliplr(crop_mask)], np.fliplr(original_crop)[np.fliplr(crop_mask)]
    )


def test_a_front_facing_source_is_never_mirrored(scene) -> None:
    drawing, main, leaf = scene
    keep = [{"entity_id": "sec-1", "state": "unchanged"}]
    staging = _staging([(_main("center-middle", facing="left"), keep)] * 5)
    frame = kc.build_keyframes(drawing, main, [leaf], staging, source_facing="front")[1]
    assert frame.notes["mirrored"] is False


def test_the_leaf_is_gone_in_the_last_keyframe_and_the_paper_is_clean(scene) -> None:
    drawing, main, leaf = scene
    frames = kc.build_keyframes(
        drawing, main, [leaf], _eat_leaf(), source_facing="right"
    )
    last = frames[5]
    assert _ink(last.image, leaf.mask) == 0
    allowed = np.zeros((H, W), dtype=bool)
    allowed |= last.main_mask
    stray = _ink(last.image) - _ink(last.image, allowed)
    assert stray == 0, "foreign ink outside the main sprite"
    assert tuple(np.asarray(last.image)[5, 5]) == PAPER


def test_partly_gone_leaves_about_half_of_the_leaf_ink(scene) -> None:
    drawing, main, leaf = scene
    frames = kc.build_keyframes(
        drawing, main, [leaf], _eat_leaf(), source_facing="right"
    )
    mask = frames[4].secondary_masks["sec-1"]
    ratio = _ink(frames[4].image, mask) / _ink(drawing, leaf.mask)
    assert 0.35 <= ratio <= 0.65


def test_an_unchanged_secondary_is_pixel_identical_in_place(scene) -> None:
    drawing, main, leaf = scene
    frames = kc.build_keyframes(
        drawing, main, [leaf], _eat_leaf(), source_facing="right"
    )
    for frame in frames[1:4]:
        assert np.array_equal(
            np.asarray(frame.image)[leaf.mask], np.asarray(drawing)[leaf.mask]
        )


def test_a_moved_secondary_lands_in_its_cell_and_leaves_clean_paper_behind(
    scene,
) -> None:
    drawing, main, leaf = scene
    staging = _staging(
        [
            (
                _main("left-middle"),
                [{"entity_id": "sec-1", "state": "moved", "position": "right-bottom"}],
            )
        ]
        + [(_main("left-middle"), [{"entity_id": "sec-1", "state": "unchanged"}])] * 4
    )
    frame = kc.build_keyframes(drawing, main, [leaf], staging, source_facing="right")[1]
    cx, cy = kc.mask_center(frame.secondary_masks["sec-1"])
    assert cx > 2 * W / 3 and cy > 2 * H / 3
    assert _ink(frame.image, leaf.mask & ~frame.secondary_masks["sec-1"]) == 0


def test_scale_steps_are_cumulative_and_clamped(scene) -> None:
    drawing, main, leaf = scene
    keep = [{"entity_id": "sec-1", "state": "unchanged"}]
    staging = _staging([(_main("center-middle", scale="slightly_bigger"), keep)] * 5)
    frames = kc.build_keyframes(drawing, main, [leaf], staging, source_facing="right")
    scales = [frame.notes["main_scale"] for frame in frames[1:]]
    assert (
        scales == sorted(scales) and max(scales) <= 1.15 + 1e-9 and min(scales) >= 1.0
    )
    assert scales[-1] == pytest.approx(1.15)
    shrink = _staging([(_main("center-middle", scale="slightly_smaller"), keep)] * 5)
    assert min(
        f.notes["main_scale"]
        for f in kc.build_keyframes(
            drawing, main, [leaf], shrink, source_facing="right"
        )[1:]
    ) == pytest.approx(0.85)


def test_a_sprite_pushed_to_the_edge_stays_fully_inside_the_canvas(scene) -> None:
    drawing, main, leaf = scene
    keep = [{"entity_id": "sec-1", "state": "unchanged"}]
    staging = _staging([(_main("right-bottom", scale="slightly_bigger"), keep)] * 5)
    for frame in kc.build_keyframes(
        drawing, main, [leaf], staging, source_facing="right"
    )[1:]:
        assert int(frame.main_mask.sum()) > 0
        x0, y0, x1, y1 = kc.mask_bbox(frame.main_mask)
        assert x0 >= 0 and y0 >= 0 and x1 < W and y1 < H


def test_the_result_is_deterministic(scene) -> None:
    drawing, main, leaf = scene
    a = kc.build_keyframes(drawing, main, [leaf], _eat_leaf(), source_facing="right")
    b = kc.build_keyframes(drawing, main, [leaf], _eat_leaf(), source_facing="right")
    assert all(
        np.array_equal(np.asarray(x.image), np.asarray(y.image)) for x, y in zip(a, b)
    )


def test_a_staging_for_an_unknown_secondary_is_refused(scene) -> None:
    drawing, main, leaf = scene
    bad = _staging([(_main(), [{"entity_id": "sec-9", "state": "unchanged"}])] * 5)
    with pytest.raises(kc.KeyframeError) as e:
        kc.build_keyframes(drawing, main, [leaf], bad, source_facing="right")
    assert e.value.code == "KEYFRAME_STAGING_MISMATCH"


def test_an_empty_or_tiny_mask_is_refused_before_composing(scene) -> None:
    drawing, _main, leaf = scene
    empty = kc.SubjectLayer(
        "subject-main", np.zeros((H, W), dtype=bool), (0, 0, 10, 10)
    )
    with pytest.raises(kc.KeyframeError) as e:
        kc.build_keyframes(drawing, empty, [leaf], _eat_leaf(), source_facing="right")
    assert e.value.code == "KEYFRAME_MASK_INVALID"


def test_covering_a_secondary_with_the_main_subject_is_reported_not_hidden(
    scene,
) -> None:
    drawing, main, leaf = scene
    keep = [{"entity_id": "sec-1", "state": "unchanged"}]
    staging = _staging([(_main("right-middle"), keep)] * 5)
    frame = kc.build_keyframes(drawing, main, [leaf], staging, source_facing="right")[1]
    assert frame.notes["overlap"]["sec-1"] > 0.2
    clear = kc.build_keyframes(
        drawing, main, [leaf], _eat_leaf(), source_facing="right"
    )[2]
    assert clear.notes["overlap"]["sec-1"] == 0.0


# ---- findings from the first contact sheet: stay on the page, bite instead of slice -----------


def test_cells_are_placed_inside_the_page_not_the_white_margin(scene) -> None:
    drawing, main, leaf = scene
    page = (200, 100, 1100, 700)  # the fitted drawing inside the 1280x768 canvas
    keep = [{"entity_id": "sec-1", "state": "unchanged"}]
    staging = _staging(
        [(_main("left-middle"), keep)] * 2
        + [(_main("right-bottom", scale="slightly_bigger"), keep)] * 3
    )
    frames = kc.build_keyframes(
        drawing, main, [leaf], staging, source_facing="right", page_box=page
    )
    for frame in frames[1:]:
        x0, y0, x1, y1 = kc.mask_bbox(frame.main_mask)
        assert x0 >= page[0] and y0 >= page[1] and x1 < page[2] and y1 < page[3]
    cx, _ = kc.mask_center(frames[1].main_mask)
    assert (
        page[0] <= cx < page[0] + (page[2] - page[0]) / 3 + 160
    )  # inside the left third of the page


def test_a_moved_object_also_stays_on_the_page(scene) -> None:
    drawing, main, leaf = scene
    page = (200, 100, 1100, 700)
    staging = _staging(
        [
            (
                _main("left-middle"),
                [{"entity_id": "sec-1", "state": "moved", "position": "right-bottom"}],
            )
        ]
        + [(_main("left-middle"), [{"entity_id": "sec-1", "state": "unchanged"}])] * 4
    )
    frame = kc.build_keyframes(
        drawing, main, [leaf], staging, source_facing="right", page_box=page
    )[1]
    _x0, _y0, x1, y1 = kc.mask_bbox(frame.secondary_masks["sec-1"])
    assert x1 < page[2] and y1 < page[3]


def test_a_partly_gone_object_has_a_bite_taken_from_the_side_facing_the_subject(
    scene,
) -> None:
    drawing, main, leaf = scene
    frames = kc.build_keyframes(
        drawing, main, [leaf], _eat_leaf(), source_facing="right"
    )
    kept = frames[4].secondary_masks["sec-1"]
    full = leaf.mask
    removed = full & ~kept
    assert 0.35 <= removed.sum() / full.sum() <= 0.65
    _ys, xs = np.nonzero(removed)
    # the main subject is to the left of the leaf, so the bite is on the leaf's left half
    assert xs.mean() < mask_center_x(full)
    # the bite is round, not a straight slice: a slice leaves every column wholly kept or wholly
    # removed, a round bite leaves many columns partly removed
    partly = (removed.any(axis=0) & kept.any(axis=0)).sum()
    assert partly >= 10


def mask_center_x(mask) -> float:
    return kc.mask_center(mask)[0]
