from __future__ import annotations

import pytest

from sketch2life.contracts.schemas.story_video import StoryboardDrawBeatV1
from sketch2life.infrastructure.media.whiteboard_mvp_renderer import (
    WhiteboardMvpRenderSpec,
    render_progressive_reveal,
    render_stroke_animation,
)


def test_mvp_render_spec_matches_contract_defaults() -> None:
    spec = WhiteboardMvpRenderSpec()

    spec.validate()

    assert (spec.width, spec.height) == (1280, 720)
    assert spec.fps == 30
    assert spec.duration_seconds == 8.0
    assert spec.max_size_bytes == 12 * 1024 * 1024


def test_mvp_render_spec_accepts_storyboard_duration() -> None:
    spec = WhiteboardMvpRenderSpec(duration_seconds=14.0)

    spec.validate()

    assert spec.duration_seconds == 14.0


@pytest.mark.parametrize(
    ("field", "value"),
    [("width", 600), ("height", 600), ("duration_seconds", 4.0)],
)
def test_mvp_render_spec_rejects_contract_violations(field: str, value: object) -> None:
    spec = WhiteboardMvpRenderSpec(**{field: value})

    with pytest.raises(ValueError):
        spec.validate()


def test_mvp_renderer_encodes_h264_artifact(tmp_path) -> None:
    Image = pytest.importorskip("PIL.Image")
    imageio = pytest.importorskip("imageio.v2")

    source = Image.new("RGBA", (64, 64), (255, 120, 0, 255))
    source_path = tmp_path / "cutout.png"
    output_path = tmp_path / "whiteboard.mp4"
    source.save(source_path)

    result = render_progressive_reveal(
        source_path,
        output_path,
        spec=WhiteboardMvpRenderSpec(
            width=1280,
            height=720,
            fps=5,
            duration_seconds=5.0,
        ),
    )

    metadata = imageio.get_reader(output_path).get_meta_data()
    assert result.codec == "H264_AVC_HIGH_L4_1"
    assert result.size_bytes > 0
    assert metadata["size"] == (1280, 720)
    assert metadata["fps"] == 5.0


def test_stroke_renderer_draws_json_strokes_on_whiteboard(tmp_path) -> None:
    imageio = pytest.importorskip("imageio.v2")
    stroke_path = tmp_path / "strokes.json"
    stroke_path.write_text(
        '{"artifact_type":"whiteboard_strokes_v1","width":20,"height":20,'
        '"strokes":[{"stroke_id":"s-1","points":[[2,2],[18,2],[18,18]]}]}',
        encoding="utf-8",
    )
    output_path = tmp_path / "strokes.mp4"

    result = render_stroke_animation(
        stroke_path,
        output_path,
        spec=WhiteboardMvpRenderSpec(width=1280, height=720, fps=5, duration_seconds=5.0),
    )

    metadata = imageio.get_reader(output_path).get_meta_data()
    assert result.codec == "H264_AVC_HIGH_L4_1"
    assert metadata["size"] == (1280, 720)
    reader = imageio.get_reader(output_path)
    middle = reader.get_data(10).astype("int16")
    final = reader.get_data(24).astype("int16")
    middle_blue = (middle[:, :, 2] > middle[:, :, 0] + 35) & (
        middle[:, :, 2] > middle[:, :, 1] + 15
    )
    final_blue = (final[:, :, 2] > final[:, :, 0] + 35) & (
        final[:, :, 2] > final[:, :, 1] + 15
    )
    assert middle_blue.any(), "marker hand should follow the active stroke"
    assert not final_blue.any(), "finished drawing should not retain the marker hand"


def test_stroke_renderer_reveals_source_color_after_drawing(tmp_path) -> None:
    Image = pytest.importorskip("PIL.Image")
    ImageDraw = pytest.importorskip("PIL.ImageDraw")
    imageio = pytest.importorskip("imageio.v2")
    from sketch2life.infrastructure.media.whiteboard_stroke_extraction import (
        extract_image_line_art,
    )

    source = tmp_path / "colored.png"
    image = Image.new("RGB", (160, 100), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((12, 12, 148, 88), outline=(20, 20, 20), width=4)
    draw.ellipse((55, 22, 105, 72), fill=(30, 100, 225))
    image.save(source)
    strokes = tmp_path / "colored.strokes.json"
    extract_image_line_art(source, strokes, source_hash="f" * 64)

    output = tmp_path / "colored.mp4"
    render_stroke_animation(
        strokes,
        output,
        spec=WhiteboardMvpRenderSpec(width=1280, height=720, fps=5, duration_seconds=5.0),
    )
    reader = imageio.get_reader(output)
    middle = reader.get_data(14).astype("int16")
    final = reader.get_data(24).astype("int16")
    reader.close()

    def is_blue(frame):
        return (frame[:, :, 2] > frame[:, :, 0] + 70) & (
            frame[:, :, 2] > frame[:, :, 1] + 65
        )
    assert is_blue(final).sum() > is_blue(middle).sum() * 3

    strokes.with_suffix(".color.png").write_bytes(b"changed")
    with pytest.raises(ValueError, match="color layer hash mismatch"):
        render_stroke_animation(strokes, tmp_path / "tampered.mp4")


def test_stroke_renderer_colors_each_object_after_its_own_outline(tmp_path) -> None:
    import hashlib
    import json

    Image = pytest.importorskip("PIL.Image")
    ImageDraw = pytest.importorskip("PIL.ImageDraw")
    imageio = pytest.importorskip("imageio.v2")

    colored = Image.new("RGBA", (100, 100))
    draw = ImageDraw.Draw(colored)
    draw.rectangle((70, 20, 90, 40), fill=(235, 60, 45, 255))
    draw.rectangle((10, 20, 30, 40), fill=(35, 75, 235, 255))
    strokes = tmp_path / "objects.strokes.json"
    layer = strokes.with_suffix(".color.png")
    colored.save(layer)
    digest = hashlib.sha256(layer.read_bytes()).hexdigest()
    strokes.write_text(
        json.dumps(
            {
                "artifact_type": "whiteboard_strokes_v1",
                "width": 100,
                "height": 100,
                "color_layer_sha256": digest,
                "strokes": [
                    {
                        "stroke_id": "right-first",
                        "color": [235, 60, 45],
                        "points": [[70, 20], [90, 20], [90, 40], [70, 40], [70, 20]],
                    },
                    {
                        "stroke_id": "left-second",
                        "color": [35, 75, 235],
                        "points": [[10, 20], [30, 20], [30, 40], [10, 40], [10, 20]],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "objects.mp4"
    render_stroke_animation(
        strokes,
        output,
        spec=WhiteboardMvpRenderSpec(width=1280, height=720, fps=5, duration_seconds=5),
    )
    reader = imageio.get_reader(output)
    halfway = reader.get_data(11).astype("int16")
    final = reader.get_data(24).astype("int16")
    reader.close()

    def filled_blue(frame):
        return (
            (frame[:, :, 2] > frame[:, :, 0] + 100) & (frame[:, :, 2] > frame[:, :, 1] + 100)
        ).sum()

    def filled_red(frame):
        return (
            (frame[:, :, 0] > frame[:, :, 1] + 100) & (frame[:, :, 0] > frame[:, :, 2] + 100)
        ).sum()

    red_area = (slice(210, 270), slice(790, 845))
    blue_area = (slice(210, 270), slice(430, 485))
    assert filled_red(halfway[red_area]) > 100
    assert filled_blue(halfway[blue_area]) < 100
    assert filled_red(final[red_area]) > 1000
    assert filled_blue(final[blue_area]) > 1000


def test_narration_beats_draw_right_object_before_left_object(tmp_path) -> None:
    import json

    imageio = pytest.importorskip("imageio.v2")
    strokes = tmp_path / "beat-order.json"
    strokes.write_text(json.dumps({
        "artifact_type": "whiteboard_strokes_v1", "width": 100, "height": 100,
        "strokes": [
            {"stroke_id": "left-in-file", "points": [[10, 70], [30, 70]]},
            {"stroke_id": "right-in-file", "points": [[70, 30], [90, 30]]},
        ],
    }), encoding="utf-8")
    beats = (
        StoryboardDrawBeatV1(
            element_id="right", segment_id="segment-1", label="Bên phải",
            focus_box=(0.6, 0.1, 0.98, 0.5), start_seconds=0, end_seconds=2.5,
        ),
        StoryboardDrawBeatV1(
            element_id="left", segment_id="segment-1", label="Bên trái",
            focus_box=(0.02, 0.5, 0.4, 0.9), start_seconds=2.5, end_seconds=5,
        ),
    )
    video = tmp_path / "beat-order.mp4"
    render_stroke_animation(
        strokes, video,
        spec=WhiteboardMvpRenderSpec(width=1280, height=720, fps=5, duration_seconds=5),
        draw_beats=beats,
    )
    reader = imageio.get_reader(video)
    early = reader.get_data(8)
    late = reader.get_data(23)
    reader.close()
    right = (slice(230, 270), slice(790, 845))
    left = (slice(450, 490), slice(430, 485))
    assert (early[right].mean(axis=2) < 150).sum() > 100
    assert (early[left].mean(axis=2) < 150).sum() < 20
    assert (late[left].mean(axis=2) < 150).sum() > 100


def test_narration_beat_without_matching_strokes_blocks_render(tmp_path) -> None:
    import json

    strokes = tmp_path / "missing-beat.json"
    strokes.write_text(json.dumps({
        "artifact_type": "whiteboard_strokes_v1", "width": 100, "height": 100,
        "strokes": [{"stroke_id": "left", "points": [[10, 70], [30, 70]]}],
    }), encoding="utf-8")
    beats = (
        StoryboardDrawBeatV1(
            element_id="left", segment_id="segment-1", label="Bên trái",
            focus_box=(0.02, 0.5, 0.4, 0.9), start_seconds=0, end_seconds=2.5,
        ),
        StoryboardDrawBeatV1(
            element_id="right", segment_id="segment-1", label="Bên phải",
            focus_box=(0.6, 0.1, 0.98, 0.5), start_seconds=2.5, end_seconds=5,
        ),
    )
    with pytest.raises(ValueError, match="DRAW_BEAT_EMPTY"):
        render_stroke_animation(
            strokes, tmp_path / "must-not-render.mp4",
            spec=WhiteboardMvpRenderSpec(width=1280, height=720, fps=5, duration_seconds=5),
            draw_beats=beats,
        )


def test_story_fixture_keeps_multiple_approved_colors_in_final_frame(tmp_path) -> None:
    imageio = pytest.importorskip("imageio.v2")
    from tools.create_story_video_media_fixture import create_fixture
    from tools.story_video_media_smoke import load_fixture

    from sketch2life.infrastructure.media.whiteboard_stroke_extraction import (
        extract_image_line_art,
    )

    source, _locale, _scenes = load_fixture(create_fixture(tmp_path / "fixture"))
    strokes = tmp_path / "full.strokes.json"
    extract_image_line_art(source, strokes, source_hash="a" * 64)
    video = tmp_path / "full-color.mp4"
    render_stroke_animation(
        strokes,
        video,
        spec=WhiteboardMvpRenderSpec(width=1280, height=720, fps=5, duration_seconds=5),
    )
    reader = imageio.get_reader(video)
    frame = reader.get_data(24).astype("int16")
    reader.close()
    red, green, blue = (frame[:, :, channel] for channel in range(3))
    assert ((red > 200) & (green > 140) & (blue < 100)).sum() > 1000
    assert ((green > red + 20) & (green > blue + 10)).sum() > 1000
    assert ((red > green + 20) & (blue > green + 20)).sum() > 100


def test_storyboard_strokes_use_most_of_the_video_canvas(tmp_path) -> None:
    imageio = pytest.importorskip("imageio.v2")
    stroke_path = tmp_path / "wide-strokes.json"
    stroke_path.write_text(
        '{"artifact_type":"whiteboard_strokes_v1","width":400,"height":250,'
        '"strokes":[{"stroke_id":"frame","points":'
        '[[20,20],[380,20],[380,230],[20,230],[20,20]]}]}',
        encoding="utf-8",
    )
    output_path = tmp_path / "wide.mp4"
    render_stroke_animation(
        stroke_path,
        output_path,
        spec=WhiteboardMvpRenderSpec(width=1280, height=720, fps=5, duration_seconds=5.0),
    )
    reader = imageio.get_reader(output_path)
    frame = reader.get_data(24)
    reader.close()
    dark_y, dark_x = (frame[:, :, :3].mean(axis=2) < 100).nonzero()
    assert dark_x.max() - dark_x.min() > 700
    assert dark_y.max() - dark_y.min() > 400


def test_completed_strokes_remain_visible_while_next_stroke_is_drawn(tmp_path) -> None:
    imageio = pytest.importorskip("imageio.v2")
    stroke_path = tmp_path / "two-strokes.json"
    stroke_path.write_text(
        '{"artifact_type":"whiteboard_strokes_v1","width":100,"height":100,'
        '"strokes":['
        '{"stroke_id":"upper","points":[[5,10],[95,10]]},'
        '{"stroke_id":"lower","points":[[5,90],[95,90]]}'
        ']}',
        encoding="utf-8",
    )
    output_path = tmp_path / "two-strokes.mp4"
    render_stroke_animation(
        stroke_path,
        output_path,
        spec=WhiteboardMvpRenderSpec(width=1280, height=720, fps=5, duration_seconds=5.0),
    )
    reader = imageio.get_reader(output_path)
    first = reader.get_data(8)
    halfway = reader.get_data(12)
    final = reader.get_data(24)
    reader.close()
    scale = min(1280 * 0.78 / 100, 720 * 0.82 / 100)
    upper_y = round((720 - 100 * scale) / 2 + 10 * scale)
    lower_y = round((720 - 100 * scale) / 2 + 90 * scale)
    assert (first[upper_y - 3 : upper_y + 4, 450:800, :3] < 120).any()
    assert (first[lower_y - 3 : lower_y + 4, 450:800, :3] > 240).all()
    assert (halfway[upper_y - 3 : upper_y + 4, 450:800, :3] < 120).any()
    assert (final[upper_y - 3 : upper_y + 4, 450:800, :3] < 120).any()
    assert (final[lower_y - 3 : lower_y + 4, 450:800, :3] < 120).any()


def test_zero_length_pen_stroke_renders_an_isolated_dot(tmp_path) -> None:
    imageio = pytest.importorskip("imageio.v2")
    stroke_path = tmp_path / "dot.json"
    stroke_path.write_text(
        '{"artifact_type":"whiteboard_strokes_v1","width":100,"height":100,'
        '"strokes":[{"stroke_id":"dot","points":[[50,50],[50,50]]}]}',
        encoding="utf-8",
    )
    output_path = tmp_path / "dot.mp4"
    render_stroke_animation(
        stroke_path,
        output_path,
        spec=WhiteboardMvpRenderSpec(width=1280, height=720, fps=5, duration_seconds=5.0),
    )
    reader = imageio.get_reader(output_path)
    final = reader.get_data(24)
    reader.close()
    assert (final[357:364, 637:644, :3] < 120).any()


def test_adjacent_short_strokes_have_no_white_seam(tmp_path) -> None:
    imageio = pytest.importorskip("imageio.v2")
    stroke_path = tmp_path / "adjacent.json"
    stroke_path.write_text(
        '{"artifact_type":"whiteboard_strokes_v1","width":400,"height":250,'
        '"strokes":['
        '{"stroke_id":"left","points":[[100,100],[150,100]]},'
        '{"stroke_id":"right","points":[[151,100],[200,100]]}'
        ']}',
        encoding="utf-8",
    )
    output_path = tmp_path / "adjacent.mp4"
    render_stroke_animation(
        stroke_path,
        output_path,
        spec=WhiteboardMvpRenderSpec(width=1280, height=720, fps=5, duration_seconds=5.0),
    )
    reader = imageio.get_reader(output_path)
    final = reader.get_data(24)
    reader.close()
    scale = min(1280 * 0.78 / 400, 720 * 0.82 / 250)
    x = round((1280 - 400 * scale) / 2 + 150.5 * scale)
    y = round((720 - 250 * scale) / 2 + 100 * scale)
    assert final[y, x, :3].mean() < 120


def test_closed_stroke_is_not_reduced_to_a_dot(tmp_path) -> None:
    imageio = pytest.importorskip("imageio.v2")
    stroke_path = tmp_path / "loop.json"
    stroke_path.write_text(
        '{"artifact_type":"whiteboard_strokes_v1","width":100,"height":100,'
        '"strokes":[{"stroke_id":"loop","points":'
        '[[20,20],[80,20],[80,80],[20,80],[20,20]]}]}',
        encoding="utf-8",
    )
    output_path = tmp_path / "loop.mp4"
    render_stroke_animation(
        stroke_path,
        output_path,
        spec=WhiteboardMvpRenderSpec(width=1280, height=720, fps=5, duration_seconds=5.0),
    )
    reader = imageio.get_reader(output_path)
    final = reader.get_data(24)
    reader.close()
    dark = final[:, :, :3].mean(axis=2) < 120
    assert dark.sum() > 1000
