from __future__ import annotations

import importlib.util
import io
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace

import pytest

MODAL_DIR = Path(__file__).resolve().parents[1]
if str(MODAL_DIR) not in sys.path:
    sys.path.insert(0, str(MODAL_DIR))

MODULE_SPEC = importlib.util.spec_from_file_location(
    "sketch2life_story_image_guides",
    MODAL_DIR / "story_image_guides.py",
)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
story_image_guides = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(story_image_guides)


def test_leaf_guide_is_one_bounded_static_shape_with_one_midvein() -> None:
    safe_svg = story_image_guides.sanitize_leaf_guide_svg()
    root = ET.fromstring(safe_svg)
    namespace = "{http://www.w3.org/2000/svg}"
    paths = root.findall(f"{namespace}path")

    assert root.attrib == {
        "width": "1280",
        "height": "720",
        "viewBox": "0 0 1280 720",
    }
    assert len(paths) == 2  # one leaf silhouette and its single vein
    assert paths[0].attrib["fill"] == "#58b93d"
    assert paths[1].attrib["fill"] == "none"
    assert "M 956 370" in paths[0].attrib["d"]
    assert "M 1018 415" in paths[1].attrib["d"]


def test_leaf_guide_rejects_modified_or_active_svg_content() -> None:
    unsafe_svg = story_image_guides.LEAF_GUIDE_SVG.replace(
        b"</svg>", b"<script>alert(1)</script></svg>"
    )

    with pytest.raises(story_image_guides.StoryImageGuideError):
        story_image_guides.sanitize_leaf_guide_svg(unsafe_svg)


def test_renderer_runtime_preflight_renders_and_decodes_probe(monkeypatch) -> None:
    from PIL import Image

    probe = io.BytesIO()
    Image.new("RGBA", (32, 18), (0, 0, 0, 0)).save(probe, format="PNG")
    requested: dict[str, object] = {}

    def svg2png(**kwargs):
        requested.update(kwargs)
        return probe.getvalue()

    monkeypatch.setitem(
        sys.modules,
        "cairosvg",
        SimpleNamespace(__version__="2.7.1", svg2png=svg2png),
    )

    result = story_image_guides.validate_leaf_guide_renderer_runtime()

    assert result["cairosvg_version"] == "2.7.1"
    assert requested["output_width"] == 32
    assert requested["output_height"] == 18
    assert requested["bytestring"] == story_image_guides.sanitize_leaf_guide_svg()
