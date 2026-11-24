"""FEAT-087 M5: SAM 2.1 box-prompt masks for the main subject and approved secondary objects.

The predictor is injected (``SAM2ImagePredictor`` in the worker, a fake in tests). Every mask is
checked before use; any rejection becomes a content-free code and the video falls back to the
single-frame render mode instead of compositing a bad cut-out.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np

MIN_SCORE = 0.6
MIN_MASK_PIXELS = 64
MIN_BOX_FILL = 0.02
BOX_SLACK = 0.10
MAX_OUTSIDE_SHARE = 0.25
MAX_PAIR_OVERLAP = 0.30


class MaskError(ValueError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _clamp(box: Sequence[int], width: int, height: int) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = (int(v) for v in box)
    x0, x1 = max(0, min(x0, width)), max(0, min(x1, width))
    y0, y1 = max(0, min(y0, height)), max(0, min(y1, height))
    if x1 <= x0 or y1 <= y0:
        raise MaskError("SAM_BOX_INVALID")
    return x0, y0, x1, y1


def masks_for_boxes(
    image: np.ndarray, boxes: Sequence[Sequence[int]], predictor: Any
) -> list[np.ndarray]:
    """One boolean mask per box, in order, or :class:`MaskError`."""

    height, width = image.shape[:2]
    clamped = [_clamp(box, width, height) for box in boxes]
    predictor.set_image(image)
    masks: list[np.ndarray] = []
    for x0, y0, x1, y1 in clamped:
        raw, scores, _ = predictor.predict(
            box=np.array([x0, y0, x1, y1], dtype=np.float32), multimask_output=False
        )
        if float(np.asarray(scores).reshape(-1)[0]) < MIN_SCORE:
            raise MaskError("SAM_MASK_LOW_CONFIDENCE")
        mask = np.asarray(raw[0]).astype(bool)
        total = int(mask.sum())
        slack_x = round((x1 - x0) * BOX_SLACK)
        slack_y = round((y1 - y0) * BOX_SLACK)
        allowed = np.zeros_like(mask)
        allowed[
            max(0, y0 - slack_y) : min(height, y1 + slack_y),
            max(0, x0 - slack_x) : min(width, x1 + slack_x),
        ] = True
        clipped = mask & allowed
        if total and (total - int(clipped.sum())) / total > MAX_OUTSIDE_SHARE:
            raise MaskError("SAM_MASK_ESCAPES_BOX")
        if int(clipped.sum()) < max(
            MIN_MASK_PIXELS, MIN_BOX_FILL * (x1 - x0) * (y1 - y0)
        ):
            raise MaskError("SAM_MASK_TOO_SMALL")
        masks.append(clipped)
    for i in range(len(masks)):
        for j in range(i + 1, len(masks)):
            shared = int((masks[i] & masks[j]).sum())
            if (
                shared / min(int(masks[i].sum()), int(masks[j].sum()))
                > MAX_PAIR_OVERLAP
            ):
                raise MaskError("SAM_MASKS_OVERLAP")
    return masks
