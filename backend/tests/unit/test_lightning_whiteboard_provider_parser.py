from __future__ import annotations

import pytest

from tools.lightning_whiteboard_provider import _parse_box


def test_parse_box_scales_1024_coordinates_to_image_size() -> None:
    assert _parse_box("[100, 200, 900, 1000]", 600, 600) == [
        pytest.approx(58.59375),
        pytest.approx(117.1875),
        pytest.approx(527.34375),
        pytest.approx(585.9375),
    ]


def test_parse_box_rejects_missing_box() -> None:
    with pytest.raises(ValueError, match="bounding box"):
        _parse_box("no coordinates", 600, 600)
