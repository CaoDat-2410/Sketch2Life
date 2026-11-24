"""FEAT-087 M5: turn a ``keyframe_plan`` plus the original drawing into keyframe PNGs.

Any problem with the cut-outs (SAM, overlap, composition) degrades to ``fallback`` mode with a
content-free reason code; only an invalid *plan* is a contract error, because the backend built it.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

import keyframe_compositor as compositor
import keyframe_metrics as metrics
import keyframe_plan as plan_contract
import sam_masks

MAX_OBJECT_COVER = 0.5


@dataclass
class KeyframeSet:
    render_mode: str
    fallback_reason: str | None
    paths: list[Path]
    summaries: list[dict[str, Any]]


def _save(image: Image.Image, path: Path) -> str:
    image.save(path, format="PNG", optimize=False)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare_keyframes(
    source_path: Path,
    plan: dict[str, Any],
    *,
    scene_count: int,
    workdir: Path,
    predictor_factory: Callable[[], Any],
) -> KeyframeSet:
    plan_contract.validate_keyframe_plan(plan, scene_count=scene_count)
    with Image.open(source_path) as opened:
        drawing = opened.convert("RGB")
    canvas, transform = compositor.fit_to_canvas(drawing)
    k0_path = workdir / "keyframe-00.png"
    k0_sha = _save(canvas, k0_path)

    def fallback(reason: str) -> KeyframeSet:
        return KeyframeSet(
            "fallback", reason, [k0_path], [{"index": 0, "sha256": k0_sha}]
        )

    if plan["render_mode"] == "fallback":
        return fallback(plan["fallback_reason"])
    try:
        canvas_array = np.asarray(canvas)
        entities = [plan["main"], *plan["secondaries"]]
        boxes = [
            plan_contract.grid_box_to_canvas(
                entity["box"], source_size=drawing.size, transform=transform
            )
            for entity in entities
        ]
        masks = sam_masks.masks_for_boxes(canvas_array, boxes, predictor_factory())
        main = compositor.SubjectLayer(entities[0]["entity_id"], masks[0], boxes[0])
        secondaries = [
            compositor.SubjectLayer(entity["entity_id"], mask, box)
            for entity, mask, box in zip(
                entities[1:], masks[1:], boxes[1:], strict=True
            )
        ]
        frames = compositor.build_keyframes(
            canvas,
            main,
            secondaries,
            plan["staging"],
            source_facing=plan["source_facing"],
            page_box=transform.page_box(drawing.size),
        )
        if any(
            ratio > MAX_OBJECT_COVER
            for frame in frames[1:]
            for ratio in frame.notes["overlap"].values()
        ):
            return fallback("KEYFRAME_SUBJECT_COVERS_OBJECT")
        paper = frames[0].notes["paper"]
        original_ink = {
            layer.entity_id: max(
                int(metrics.ink_mask(canvas_array, paper)[layer.mask].sum()), 1
            )
            for layer in secondaries
        }
        paths = [k0_path]
        summaries: list[dict[str, Any]] = []
        for index, frame in enumerate(frames):
            path = k0_path if index == 0 else workdir / f"keyframe-{index:02d}.png"
            sha = k0_sha if index == 0 else _save(frame.image, path)
            if index:
                paths.append(path)
            pixels = np.asarray(frame.image)
            ink = metrics.ink_mask(pixels, paper)
            summaries.append(
                {
                    "index": index,
                    "sha256": sha,
                    "mirrored": frame.notes["mirrored"],
                    "main_scale": frame.notes["main_scale"],
                    "secondary_states": frame.notes.get("secondary_states", {}),
                    "secondary_ink_ratio": {
                        key: float(ink[mask].sum()) / original_ink[key]
                        for key, mask in frame.secondary_masks.items()
                    },
                    "stray_ink_ratio": metrics.stray_ink_ratio(
                        pixels,
                        [frame.main_mask, *frame.secondary_masks.values()],
                        paper,
                    ),
                }
            )
        return KeyframeSet("keyframe", None, paths, summaries)
    except (sam_masks.MaskError, compositor.KeyframeError) as exc:
        return fallback(exc.code)
    except Exception:  # noqa: BLE001 - never leak provider text; the video falls back
        return fallback("KEYFRAME_UNEXPECTED_ERROR")
