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


def test_drawing_fp8_image_pins_compatible_huggingface_kernels() -> None:
    source = (MODULE_DIR / "drawing_vlm_app.py").read_text(encoding="utf-8")

    assert '"kernels==0.17.2"' in source
    assert '"torch==2.8.0"' in source
    assert '"torchvision==0.23.0"' in source
    assert '"transformers[kernels]==5.22.1"' in source
    assert 'QWEN_TRITON_VERSION = "3.4.0"' in source
