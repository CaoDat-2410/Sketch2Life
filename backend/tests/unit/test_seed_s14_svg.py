"""Local-only storage guard and sanitizer checks for the SVG demo."""

import pytest

from sketch2life.infrastructure.catalog.svg_assets import SqlSvgSanitizer
from tools.seed import s14_svg
from tools.seed.stage_common import StageError


def test_svg_is_accepted_by_real_sanitizer():
    result = SqlSvgSanitizer().sanitize(s14_svg.PAYLOAD.source_svg.encode())
    assert result.source_bytes
    assert result.canonical_bytes


@pytest.mark.parametrize("endpoint", ["", "https://storage.example.test", "http://localhost:5432"])
def test_storage_refuses_nonlocal_or_reserved_endpoint(monkeypatch, endpoint):
    monkeypatch.setenv("SKETCH2LIFE_S3_ENDPOINT", endpoint)
    monkeypatch.setenv("SKETCH2LIFE_S3_ACCESS_KEY", "synthetic")
    monkeypatch.setenv("SKETCH2LIFE_S3_SECRET_KEY", "synthetic")
    with pytest.raises(StageError, match="^S14_SVG_STORAGE_NOT_LOCAL$"):
        s14_svg.local_storage()
