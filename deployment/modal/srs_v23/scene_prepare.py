"""FEAT-093: prepare one scene's keyframe on C2 (pure core; models are injected).

Steps: fit the child's drawing to the LTX canvas, cut the subjects with SAM masks, stage them for the scene
(compositor), and put them over an AI crayon background plate. Any problem with the plate degrades to the paper
background (``PAPER``), any problem with the masks degrades to the original drawing on the canvas; both carry a
content-free reason code and neither stops the video.
"""

from __future__ import annotations

import io
from collections.abc import Callable
from typing import Any

import numpy as np
from PIL import Image

import keyframe_compositor as compositor
import keyframe_plan as plan_contract
import sam_masks

PLATE_MIN_STD = 6.0  # a flat plate is a failed generation
PLATE_MAX_WHITE_RATIO = 0.92
PLATE_MIN_EDGE = 0.002  # share of pixels with visible local contrast (crayon strokes)


def plate_problem(plate: Image.Image) -> str | None:
    """Content-free reason when the plate cannot be used, else None."""

    pixels = np.asarray(plate.convert("RGB"), dtype=np.float32)
    if pixels.std() < PLATE_MIN_STD:
        return "PLATE_FLAT"
    if float((pixels.min(axis=2) > 245).mean()) > PLATE_MAX_WHITE_RATIO:
        return "PLATE_BLANK"
    gray = pixels.mean(axis=2)
    contrast = (np.abs(np.diff(gray, axis=1)) > 18).mean()
    if contrast < PLATE_MIN_EDGE:
        return "PLATE_NO_TEXTURE"
    return None


def _png(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def prepare_scene(
    drawing_png: bytes,
    *,
    main: dict[str, Any],
    secondaries: list[dict[str, Any]],
    staging: dict[str, Any],
    scene_index: int,
    source_facing: str,
    plate_prompt: str,
    generate_plate: Callable[[str], Image.Image],
    predictor_factory: Callable[[], Any],
) -> dict[str, Any]:
    """Returns ``{"keyframe_png", "background", "reason"}``; ``background`` is ``AI`` or ``PAPER``."""

    with Image.open(io.BytesIO(drawing_png)) as opened:
        drawing = opened.convert("RGB")
    canvas, transform = compositor.fit_to_canvas(drawing)
    try:
        entities = [main, *secondaries]
        boxes = [
            plan_contract.grid_box_to_canvas(entity["box"], source_size=drawing.size, transform=transform)
            for entity in entities
        ]
        masks = sam_masks.masks_for_boxes(np.asarray(canvas), boxes, predictor_factory())
        main_layer = compositor.SubjectLayer(main["entity_id"], masks[0], boxes[0])
        secondary_layers = [
            compositor.SubjectLayer(entity["entity_id"], mask, box)
            for entity, mask, box in zip(secondaries, masks[1:], boxes[1:], strict=True)
        ]
        frames = compositor.build_keyframes(
            canvas,
            main_layer,
            secondary_layers,
            staging,
            source_facing=source_facing,
            page_box=transform.page_box(drawing.size),
        )
        frame = frames[scene_index]
    except (sam_masks.MaskError, compositor.KeyframeError) as error:
        return {"keyframe_png": _png(canvas), "background": "PAPER", "reason": error.code}
    except Exception:  # noqa: BLE001 - never leak provider text
        return {"keyframe_png": _png(canvas), "background": "PAPER", "reason": "SCENE_PREPARE_UNEXPECTED_ERROR"}

    try:
        plate = generate_plate(plate_prompt)
        problem = plate_problem(plate)
        if problem is not None:
            return {"keyframe_png": _png(frame.image), "background": "PAPER", "reason": problem}
        return {"keyframe_png": _png(compositor.apply_background_plate(frame, plate)), "background": "AI", "reason": None}
    except compositor.KeyframeError as error:
        return {"keyframe_png": _png(frame.image), "background": "PAPER", "reason": error.code}
    except Exception:  # noqa: BLE001
        return {"keyframe_png": _png(frame.image), "background": "PAPER", "reason": "PLATE_GENERATION_FAILED"}


__all__ = ["plate_problem", "prepare_scene"]
