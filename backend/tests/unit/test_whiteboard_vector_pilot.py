"""Synthetic authored-path pilot checks; visual acceptance remains human review."""

from __future__ import annotations

import json

import pytest
from tools.story_video_vector_pilot import make_scene

from sketch2life.infrastructure.media.whiteboard_mvp_renderer import WhiteboardMvpRenderSpec
from sketch2life.infrastructure.media.whiteboard_vector_pilot import (
    render_vector_scene,
    validate_vector_scene,
)


def test_authored_synthetic_scene_has_ordered_distinct_objects() -> None:
    scene = validate_vector_scene(make_scene())
    assert len(scene["objects"]) == 6
    assert {obj["id"] for obj in scene["objects"]} == {
        "tree", "house", "figure-left", "figure-middle", "figure-right", "details"
    }
    assert scene["objects"][0]["start"] < scene["objects"][2]["start"]
    assert all(obj["strokes"] for obj in scene["objects"])


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda s: s.update(version=2), "version"),
        (lambda s: s["objects"][1].update(id="tree"), "unique"),
        (lambda s: s["objects"][0].update(end=1.2), "window"),
        (lambda s: s["objects"][0]["strokes"][0].update(points=[[0, 0]]), "points"),
        (lambda s: s["objects"][0]["strokes"][0].update(color="red"), "color"),
        (lambda s: s["objects"][0]["fills"][0].update(color="red"), "color"),
    ],
)
def test_authored_scene_rejects_invalid_geometry(mutation, message) -> None:
    scene = make_scene()
    mutation(scene)
    with pytest.raises(ValueError, match=message):
        validate_vector_scene(scene)


def test_authored_path_reveals_ink_then_color_in_encoded_mp4(tmp_path) -> None:
    imageio = pytest.importorskip("imageio.v2")
    np = pytest.importorskip("numpy")
    scene = {
        "version": 1, "width": 640, "height": 360,
        "objects": [{
            "id": "square", "start": 0.01, "end": 0.9,
            "strokes": [{"points": [[200, 100], [400, 100], [400, 250],
                                    [200, 250], [200, 100]], "width": 2.5}],
            "fills": [{"polygon": [[201, 101], [399, 101], [399, 249], [201, 249]],
                       "color": "#ed7e6e"}],
        }],
    }
    scene_path = tmp_path / "scene.json"
    scene_path.write_text(json.dumps(scene), encoding="utf-8")
    output = tmp_path / "scene.mp4"
    stills = tmp_path / "stills"
    result = render_vector_scene(
        scene_path, output, spec=WhiteboardMvpRenderSpec(fps=4, duration_seconds=5),
        still_directory=stills,
    )
    assert result.codec == "h264"
    assert result.size_bytes > 1_000
    assert len(list(stills.glob("*.png"))) == 3
    reader = imageio.get_reader(output)
    early = reader.get_data(5).astype("int16")
    late = reader.get_data(19).astype("int16")
    reader.close()
    def red(pixels):
        return int(np.logical_and(
            pixels[:, :, 0] > pixels[:, :, 1] + 35,
            pixels[:, :, 0] > pixels[:, :, 2] + 40,
        ).sum())
    assert red(early) == 0
    assert red(late) > 1_000
    with pytest.raises(FileExistsError, match="already exists"):
        render_vector_scene(scene_path, output)
