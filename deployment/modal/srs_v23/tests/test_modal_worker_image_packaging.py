from __future__ import annotations

from pathlib import Path

import pytest

MODULE_DIR = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "module_name",
    (
        "drawing_segment_app.py",
        "drawing_vlm_app.py",
        "flux_image_app.py",
        "language_audio_app.py",
    ),
)
def test_every_base_image_bundles_worker_observability(module_name: str) -> None:
    source = (MODULE_DIR / module_name).read_text(encoding="utf-8")
    base_image_count = source.count("modal.Image.debian_slim")
    observability_file_count = source.count('"/root/worker_observability.py"')

    assert base_image_count > 0
    assert observability_file_count == base_image_count
