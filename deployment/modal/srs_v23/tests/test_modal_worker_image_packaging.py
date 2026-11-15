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
    health_image_count = source.count("health_image =")
    base_image_count = (
        source.count("modal.Image.debian_slim")
        + source.count("modal.Image.from_registry")
        - health_image_count
    )
    observability_file_count = source.count('"/root/worker_observability.py"')
    health_image_block = (
        source.split("health_image =", maxsplit=1)[1].split("@app.function", maxsplit=1)[0]
        if "health_image =" in source
        else ""
    )

    assert base_image_count > 0
    assert observability_file_count == base_image_count + health_image_count
    if health_image_block:
        assert '"/root/contracts.py"' in health_image_block
        assert '"/root/worker_observability.py"' in health_image_block
    if module_name == "language_audio_app.py":
        assert '"nvidia/cuda:12.6.3-devel-ubuntu22.04"' in source
        assert '"wheel==0.45.1"' in source
        assert '"causal-conv1d==1.7.0"' in source
        assert '.apt_install("build-essential", "ninja-build")' in source
        assert 'extra_options="--no-build-isolation"' in source
        assert '"CUDA_HOME": "/usr/local/cuda"' in source
