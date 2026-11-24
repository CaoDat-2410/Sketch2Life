"""FEAT-087 M5/G6: automatic, content-free quality metrics for keyframes and rendered frames.

All inputs are HxWx3 uint8 arrays; masks are HxW bool. Nothing here sees story text.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np

INK_DELTA = 40.0
EDGE_THRESHOLD = 25.0
EDGE_IOU_MIN = 0.6
SECONDARY_INK_TOLERANCE = 0.2
STRAY_INK_MAX = 0.01
_LUMA = np.array([0.299, 0.587, 0.114])


def _luma(pixels: np.ndarray) -> np.ndarray:
    return pixels.astype(np.float64) @ _LUMA


def _dilate(mask: np.ndarray, radius: int) -> np.ndarray:
    out = mask.copy()
    for _ in range(radius):
        grown = out.copy()
        grown[1:, :] |= out[:-1, :]
        grown[:-1, :] |= out[1:, :]
        grown[:, 1:] |= out[:, :-1]
        grown[:, :-1] |= out[:, 1:]
        out = grown
    return out


def ink_mask(pixels: np.ndarray, paper: Sequence[int]) -> np.ndarray:
    """Pixels clearly darker than the paper colour."""

    reference = float(np.dot(np.asarray(paper, dtype=np.float64), _LUMA))
    return _luma(pixels) < reference - INK_DELTA


def ink_ratio(
    frame: np.ndarray, original: np.ndarray, region: np.ndarray, paper: Sequence[int]
) -> float:
    """Ink in ``region`` of ``frame`` relative to the ink the original had there."""

    expected = int(ink_mask(original, paper)[region].sum())
    if expected == 0:
        return 0.0
    return float(ink_mask(frame, paper)[region].sum()) / expected


def stray_ink_ratio(
    frame: np.ndarray,
    allowed: Sequence[np.ndarray],
    paper: Sequence[int],
    *,
    margin: int = 6,
) -> float:
    """Share of the frame holding ink outside every allowed region (plus ``margin`` pixels)."""

    union = np.zeros(frame.shape[:2], dtype=bool)
    for mask in allowed:
        union |= mask
    union = _dilate(union, margin)
    return float((ink_mask(frame, paper) & ~union).sum()) / float(union.size)


def _edges(pixels: np.ndarray) -> np.ndarray:
    gray = _luma(pixels)
    gy, gx = np.gradient(gray)
    return np.hypot(gx, gy) > EDGE_THRESHOLD


def edge_iou(a: np.ndarray, b: np.ndarray, region: np.ndarray) -> float:
    """IoU of the edge maps of ``a`` and ``b`` inside ``region`` (0.0 for an empty region)."""

    area = _dilate(region, 2)
    edges_a, edges_b = _edges(a) & area, _edges(b) & area
    union = int((edges_a | edges_b).sum())
    if union == 0:
        return 0.0
    return float((edges_a & edges_b).sum()) / union


def motion_score(frames: Sequence[np.ndarray]) -> float:
    """Mean absolute frame-to-frame change in [0, 1]; 0.0 for a still clip."""

    if len(frames) < 2:
        return 0.0
    diffs = [
        float(
            np.abs(frames[i + 1].astype(np.int16) - frames[i].astype(np.int16)).mean()
        )
        / 255.0
        for i in range(len(frames) - 1)
    ]
    return float(np.mean(diffs))


def frame_report(
    frame: np.ndarray,
    *,
    expected_original: np.ndarray,
    main_mask: np.ndarray,
    secondary_masks: dict[str, np.ndarray],
    expected_secondary_ink: dict[str, float],
    paper: Sequence[int],
) -> dict[str, Any]:
    """Compare a rendered/keyframe image with the keyframe it should match."""

    edge = edge_iou(expected_original, frame, main_mask)
    ratios = {
        key: ink_ratio(frame, expected_original, mask, paper)
        for key, mask in secondary_masks.items()
    }
    stray = stray_ink_ratio(frame, [main_mask, *secondary_masks.values()], paper)
    violations: list[str] = []
    if edge < EDGE_IOU_MIN:
        violations.append("MAIN_EDGE_DRIFT")
    for key, expected in expected_secondary_ink.items():
        if abs(ratios.get(key, 0.0) - expected) > SECONDARY_INK_TOLERANCE:
            violations.append("SECONDARY_INK_MISMATCH")
            break
    if stray > STRAY_INK_MAX:
        violations.append("STRAY_INK")
    return {
        "edge_iou_main": edge,
        "secondary_ink_ratio": ratios,
        "stray_ink_ratio": stray,
        "violations": violations,
        "passed": not violations,
    }
