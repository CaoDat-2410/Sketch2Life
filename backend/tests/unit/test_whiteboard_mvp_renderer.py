from __future__ import annotations

import pytest

from sketch2life.infrastructure.media.whiteboard_mvp_renderer import (
    WhiteboardMvpRenderSpec,
    render_progressive_reveal,
)


def test_mvp_render_spec_matches_contract_defaults() -> None:
    spec = WhiteboardMvpRenderSpec()

    spec.validate()

    assert (spec.width, spec.height) == (1280, 720)
    assert spec.fps == 30
    assert spec.duration_seconds == 8.0
    assert spec.max_size_bytes == 12 * 1024 * 1024


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
