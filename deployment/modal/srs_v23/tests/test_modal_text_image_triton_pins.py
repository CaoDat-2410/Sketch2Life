"""The text image must carry a Triton that provides ``triton.tools.tensor_descriptor`` (Triton >= 3.4)."""

from __future__ import annotations

import ast
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "language_audio_app.py"


def _text_torch_pins() -> ast.IfExp:
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "_TEXT_TORCH_PINS"
            for target in node.targets
        ):
            assert isinstance(node.value, ast.IfExp)
            return node.value
    raise AssertionError("_TEXT_TORCH_PINS is missing")


def _strings(node: ast.expr) -> tuple[str, ...]:
    assert isinstance(node, ast.Tuple)
    return tuple(
        element.value
        for element in node.elts
        if isinstance(element, ast.Constant) and isinstance(element.value, str)
    )


def test_qwen38_text_image_pins_torch_with_a_triton_that_has_tensor_descriptor() -> None:
    pins = _strings(_text_torch_pins().body)
    assert pins == ("torch==2.8.0", "torchvision==0.23.0", "triton==3.4.0")


def test_qwen35_fallback_keeps_the_previous_torch_pins() -> None:
    pins = _strings(_text_torch_pins().orelse)
    assert pins == ("torch==2.7.1", "torchvision==0.22.1")


def test_text_image_installs_the_selected_pins_before_transformers() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert source.index("*_TEXT_TORCH_PINS") < source.index('"transformers==5.22.1"')
    assert 'from triton.tools.tensor_descriptor import TensorDescriptor' in source


def test_qwen38_text_image_installs_flash_linear_attention_for_the_gated_delta_rule() -> None:
    # Without flash-linear-attention transformers falls back to a reference PyTorch implementation of
    # `fused_recurrent_gated_delta_rule` that is far too slow for a request/response workload.
    source = SOURCE.read_text(encoding="utf-8")
    qwen38_block = source[source.index('if MODAL_QWEN_PROFILE == "qwen38":\n    # flash-linear-attention') :]
    assert '"flash-linear-attention==0.5.2"' in qwen38_block.split("_story_text_image", 1)[0]
