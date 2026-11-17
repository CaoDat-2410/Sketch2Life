"""The explicit SAM2 check must exercise inference without real model weights."""

from __future__ import annotations

import sys
from contextlib import nullcontext
from types import SimpleNamespace

import numpy as np
import pytest
from tools.verify_story_sam2 import verify_sam2


class _Predictor:
    def set_image(self, image):
        assert image.shape == (256, 256, 3)

    def predict(self, *, box, multimask_output):
        assert box.tolist() == [48, 48, 208, 208]
        assert multimask_output is True
        return np.ones((1, 256, 256), dtype=bool), np.asarray([0.8]), None


def test_verify_sam2_uses_synthetic_inference(monkeypatch) -> None:
    fake_torch = SimpleNamespace(
        cuda=SimpleNamespace(is_available=lambda: True, get_device_name=lambda _: "L4"),
        inference_mode=nullcontext,
        autocast=lambda *_args, **_kwargs: nullcontext(),
        bfloat16=object(),
    )
    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    result = verify_sam2(_Predictor())
    assert result["ready"] is True
    assert result["masks"] == 1
    assert result["gpu"] == "L4"


def test_verify_sam2_stops_without_cuda(monkeypatch) -> None:
    monkeypatch.setitem(
        sys.modules, "torch", SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: False))
    )
    with pytest.raises(RuntimeError, match="requires the L4 CUDA GPU"):
        verify_sam2(_Predictor())
