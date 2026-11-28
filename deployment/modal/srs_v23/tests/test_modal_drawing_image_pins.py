"""The drawing image carries the same Qwen3.8 runtime pins and Triton shim as the language image."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRAWING = (ROOT / "drawing_vlm_app.py").read_text(encoding="utf-8")


def test_drawing_qwen38_image_pins_torch_triton_and_flash_linear_attention() -> None:
    assert '("torch==2.8.0", "torchvision==0.23.0", "triton==3.4.0")' in DRAWING
    runtime_packages = DRAWING[
        DRAWING.index("_QWEN38_RUNTIME_PACKAGES = (") : DRAWING.index("inference_image = (")
    ]
    assert '"flash-linear-attention==0.5.2"' in runtime_packages
    assert 'else ("torch==2.7.1", "torchvision==0.22.1")' in DRAWING


def test_drawing_kernel_preload_applies_the_triton_shim_before_the_download() -> None:
    preload = DRAWING[DRAWING.index("def _preload_qwen38_fp8_kernel(") :]
    assert preload.index("_ensure_fp8_triton_import_compatibility()") < preload.index("get_kernel(")


def test_drawing_runs_on_l40s_only() -> None:
    assert 'gpu=["L40S", "L4", "A10"]' not in DRAWING
