from __future__ import annotations

import json

import pytest

from sketch2life.infrastructure.media.whiteboard_stroke_extraction import (
    extract_image_line_art,
    extract_mask_contours,
)


def test_extract_mask_contours_writes_source_bound_artifact(tmp_path) -> None:
    Image = pytest.importorskip("PIL.Image")
    mask_path = tmp_path / "mask.png"
    output_path = tmp_path / "strokes.json"
    image = Image.new("L", (20, 20), 0)
    for x in range(5, 15):
        for y in range(4, 16):
            image.putpixel((x, y), 255)
    image.save(mask_path)

    result = extract_mask_contours(
        mask_path,
        output_path,
        source_hash="a" * 64,
    )
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert result.source_hash == "a" * 64
    assert result.stroke_count == 1
    assert result.point_count > 0
    assert payload["source_hash"] == "a" * 64
    assert payload["strokes"][0]["points"]


def test_extract_mask_contours_rejects_empty_mask(tmp_path) -> None:
    Image = pytest.importorskip("PIL.Image")
    mask_path = tmp_path / "empty.png"
    Image.new("L", (20, 20), 0).save(mask_path)

    with pytest.raises(ValueError, match="MASK_EMPTY"):
        extract_mask_contours(mask_path, tmp_path / "strokes.json", source_hash="a" * 64)


def test_extract_image_line_art_keeps_separate_marks_as_separate_strokes(tmp_path) -> None:
    Image = pytest.importorskip("PIL.Image")
    ImageDraw = pytest.importorskip("PIL.ImageDraw")
    image = Image.new("RGB", (160, 80), "white")
    draw = ImageDraw.Draw(image)
    draw.line((10, 15, 45, 15), fill="black", width=4)
    draw.line((105, 55, 145, 55), fill="black", width=4)
    source = tmp_path / "source.png"
    image.save(source)

    result = extract_image_line_art(source, tmp_path / "strokes.json", source_hash="b" * 64)
    payload = json.loads((tmp_path / "strokes.json").read_text(encoding="utf-8"))

    assert result.stroke_count >= 2
    assert all(
        abs(b[0] - a[0]) <= 1 and abs(b[1] - a[1]) <= 1
        for stroke in payload["strokes"]
        for a, b in zip(stroke["points"], stroke["points"][1:], strict=False)
    )


def test_extract_image_line_art_follows_center_of_thick_pen_stroke(tmp_path) -> None:
    Image = pytest.importorskip("PIL.Image")
    ImageDraw = pytest.importorskip("PIL.ImageDraw")
    image = Image.new("RGB", (160, 80), "white")
    ImageDraw.Draw(image).line((10, 40, 150, 40), fill="black", width=9)
    source = tmp_path / "thick-line.png"
    image.save(source)

    result = extract_image_line_art(source, tmp_path / "strokes.json", source_hash="c" * 64)
    payload = json.loads((tmp_path / "strokes.json").read_text(encoding="utf-8"))
    ys = [point[1] for stroke in payload["strokes"] for point in stroke["points"]]

    assert result.stroke_count == 1
    assert max(ys) - min(ys) <= 2, "a thick pen line should not render as two outlines"


def test_extract_image_line_art_crops_only_blank_outer_margin(tmp_path) -> None:
    Image = pytest.importorskip("PIL.Image")
    ImageDraw = pytest.importorskip("PIL.ImageDraw")
    image = Image.new("RGB", (480, 240), "white")
    ImageDraw.Draw(image).rectangle((100, 45, 330, 190), outline="black", width=5)
    source = tmp_path / "framed.png"
    image.save(source)

    result = extract_image_line_art(source, tmp_path / "strokes.json", source_hash="d" * 64)
    payload = json.loads((tmp_path / "strokes.json").read_text(encoding="utf-8"))

    assert result.width < image.width
    assert result.height < image.height
    assert payload["width"] == result.width
    assert payload["height"] == result.height
    assert payload["source_width"] == image.width
    assert payload["source_height"] == image.height
    left, top, right, bottom = payload["crop_box"]
    assert right - left == result.width
    assert bottom - top == result.height
    assert all(
        0 <= x < result.width and 0 <= y < result.height
        for stroke in payload["strokes"]
        for x, y in stroke["points"]
    )


def test_extract_image_line_art_preserves_colored_marks_and_layer(tmp_path) -> None:
    Image = pytest.importorskip("PIL.Image")
    ImageDraw = pytest.importorskip("PIL.ImageDraw")
    image = Image.new("RGB", (160, 80), "white")
    draw = ImageDraw.Draw(image)
    draw.line((10, 15, 45, 15), fill=(20, 20, 20), width=4)
    draw.line((10, 60, 60, 60), fill=(245, 190, 15), width=5)
    draw.ellipse((85, 15, 135, 65), fill=(30, 110, 220))
    source = tmp_path / "colored.png"
    image.save(source)

    stroke_path = tmp_path / "colored.strokes.json"
    extract_image_line_art(source, stroke_path, source_hash="e" * 64)
    payload = json.loads(stroke_path.read_text(encoding="utf-8"))
    color_layer = stroke_path.with_suffix(".color.png")

    assert color_layer.is_file()
    assert len(payload["color_layer_sha256"]) == 64
    assert any(color[0] > 180 and color[1] > 130 and color[2] < 90
               for color in (stroke["color"] for stroke in payload["strokes"]))
    assert any(color[2] > color[0] + 80
               for color in (stroke["color"] for stroke in payload["strokes"]))
    assert Image.open(color_layer).getchannel("A").getextrema() == (0, 255)
    crop_left, crop_top, _right, _bottom = payload["crop_box"]
    blue_points = [
        point
        for stroke in payload["strokes"]
        if stroke["color"][2] > stroke["color"][0] + 80
        for point in stroke["points"]
    ]
    assert all(
        (point[0] + crop_left - 110) ** 2 + (point[1] + crop_top - 40) ** 2 > 64
        for point in blue_points
    ), "a filled color area should trace its boundary, not draw a center skeleton"


def test_connected_ink_paths_preserve_isolated_dot() -> None:
    np = pytest.importorskip("numpy")
    from sketch2life.infrastructure.media.whiteboard_stroke_extraction import (
        _connected_ink_paths,
    )

    ink = np.zeros((8, 8), dtype=bool)
    ink[1, 1:4] = True
    ink[6, 6] = True

    paths = _connected_ink_paths(ink, preserve_dots=True)

    assert [[6, 6], [6, 6]] in paths
    assert {tuple(point) for path in paths for point in path} == {
        (1, 1), (2, 1), (3, 1), (6, 6)
    }


def test_connected_ink_paths_finish_left_subject_before_right_subject() -> None:
    np = pytest.importorskip("numpy")
    from sketch2life.infrastructure.media.whiteboard_stroke_extraction import (
        _connected_ink_paths,
    )

    ink = np.zeros((12, 12), dtype=bool)
    ink[1:9, 1] = True
    ink[6, 2:5] = True
    ink[2:5, 10] = True

    paths = _connected_ink_paths(ink, preserve_dots=True)

    subject_order = ["left" if path[0][0] < 6 else "right" for path in paths]
    assert subject_order == sorted(subject_order)
    assert subject_order.count("left") >= 2
