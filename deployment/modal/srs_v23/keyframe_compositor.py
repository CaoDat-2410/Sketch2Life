"""FEAT-087 M5: build keyframes K0..Kn from the *original* drawing (CPU, PIL + numpy).

K0 is the original drawing on the 1280x768 LTX canvas. Every other keyframe re-uses the drawing's
own pixels: the main subject and each approved secondary object are cut out with their SAM masks,
the cut-out regions are painted with the paper colour, and the sprites are pasted back according
to the story staging (move / mirror / small scale step / partly gone / gone). Nothing is
generated, so no foreign object can appear and the strokes stay the child's strokes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from PIL import Image

import keyframe_metrics

CANVAS_WIDTH = 1280
CANVAS_HEIGHT = 768
CANVAS_MARGIN = 96
SCALE_MIN = 0.85
SCALE_MAX = 1.15
_SCALE_STEP = {"same": 1.0, "slightly_bigger": 1.05, "slightly_smaller": 0.95}
_MIN_MAIN_PIXELS = 64
_MIN_SECONDARY_PIXELS = 16
_ERASE_RADIUS = 4
_RESIDUE_RADIUS = 8  # anti-aliased edge ink left right next to a cut-out
_PARTLY_KEEP = 0.5


class KeyframeError(ValueError):
    """Content-free keyframe failure; ``code`` becomes the fallback reason."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class CanvasTransform:
    scale: float
    offset_x: int
    offset_y: int

    def page_box(self, source_size: tuple[int, int]) -> tuple[int, int, int, int]:
        """The fitted drawing's rectangle on the canvas (the rest is white margin)."""

        width, height = source_size
        return (
            self.offset_x,
            self.offset_y,
            self.offset_x + round(width * self.scale),
            self.offset_y + round(height * self.scale),
        )

    def box_to_canvas(
        self, box: tuple[int, int, int, int]
    ) -> tuple[int, int, int, int]:
        x0, y0, x1, y1 = box
        return (
            round(x0 * self.scale + self.offset_x),
            round(y0 * self.scale + self.offset_y),
            round(x1 * self.scale + self.offset_x),
            round(y1 * self.scale + self.offset_y),
        )


@dataclass(frozen=True)
class SubjectLayer:
    entity_id: str
    mask: np.ndarray  # bool, canvas-sized
    box: tuple[int, int, int, int]  # canvas pixels (prompt box used for SAM)


@dataclass
class Keyframe:
    image: Image.Image
    main_mask: np.ndarray
    secondary_masks: dict[str, np.ndarray]
    notes: dict[str, Any] = field(default_factory=dict)


def fit_to_canvas(drawing: Image.Image) -> tuple[Image.Image, CanvasTransform]:
    """Same layout as the worker's conditioning image: whole drawing inside the 1280x768 frame."""

    source_width = drawing.width
    fitted = drawing.convert("RGB")
    fitted.thumbnail(
        (CANVAS_WIDTH - CANVAS_MARGIN * 2, CANVAS_HEIGHT - CANVAS_MARGIN * 2),
        Image.Resampling.LANCZOS,
    )
    canvas = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), "white")
    offset_x = (CANVAS_WIDTH - fitted.width) // 2
    offset_y = (CANVAS_HEIGHT - fitted.height) // 2
    canvas.paste(fitted, (offset_x, offset_y))
    return canvas, CanvasTransform(fitted.width / source_width, offset_x, offset_y)


def mask_bbox(mask: np.ndarray) -> tuple[int, int, int, int]:
    """Inclusive ``(x0, y0, x1, y1)`` of the true pixels."""

    ys, xs = np.nonzero(mask)
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def mask_center(mask: np.ndarray) -> tuple[float, float]:
    x0, y0, x1, y1 = mask_bbox(mask)
    return (x0 + x1) / 2, (y0 + y1) / 2


def cell_center(position: str, box: tuple[int, int, int, int]) -> tuple[float, float]:
    """Centre of a 3x3 cell of ``box`` (x0, y0, x1, y1)."""

    x0, y0, x1, y1 = box
    column, row = position.split("-")
    x = x0 + {"left": 0.5, "center": 1.5, "right": 2.5}[column] * (x1 - x0) / 3
    y = y0 + {"top": 0.5, "middle": 1.5, "bottom": 2.5}[row] * (y1 - y0) / 3
    return x, y


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


@dataclass
class _Sprite:
    pixels: np.ndarray  # h, w, 3 uint8
    mask: np.ndarray  # h, w bool
    origin: tuple[int, int]  # top-left on the canvas in the source drawing

    def transformed(self, *, mirror: bool, scale: float) -> _Sprite:
        pixels, mask = self.pixels, self.mask
        if mirror:
            pixels, mask = pixels[:, ::-1], mask[:, ::-1]
        if abs(scale - 1.0) > 1e-9:
            height, width = mask.shape
            new_size = (max(1, round(width * scale)), max(1, round(height * scale)))
            pixels = np.asarray(
                Image.fromarray(np.ascontiguousarray(pixels)).resize(
                    new_size, Image.Resampling.LANCZOS
                )
            )
            mask = (
                np.asarray(
                    Image.fromarray(
                        np.ascontiguousarray(mask).astype(np.uint8) * 255
                    ).resize(new_size, Image.Resampling.NEAREST)
                )
                > 127
            )
        return _Sprite(
            np.ascontiguousarray(pixels), np.ascontiguousarray(mask), self.origin
        )


def _bite(mask: np.ndarray, side: str) -> np.ndarray:
    """Remove about half of ``mask`` with a round bite centred on its ``side`` edge."""

    height, width = mask.shape
    centre_x = 0.0 if side == "left" else float(width - 1)
    centre_y = (height - 1) / 2
    yy, xx = np.mgrid[:height, :width]
    distance = np.hypot(xx - centre_x, yy - centre_y)
    total = int(mask.sum())
    low, high = 1.0, float(max(width, height)) * 2
    for _ in range(24):
        radius = (low + high) / 2
        removed = int((mask & (distance <= radius)).sum())
        if removed / total < 1 - _PARTLY_KEEP:
            low = radius
        else:
            high = radius
    return mask & (distance > high)


def _cut_sprite(canvas: np.ndarray, layer: SubjectLayer) -> _Sprite:
    x0, y0, x1, y1 = mask_bbox(layer.mask)
    return _Sprite(
        canvas[y0 : y1 + 1, x0 : x1 + 1].copy(),
        layer.mask[y0 : y1 + 1, x0 : x1 + 1].copy(),
        (x0, y0),
    )


def _paste(
    target: np.ndarray,
    sprite: _Sprite,
    *,
    top_left: tuple[float, float],
    page: tuple[int, int, int, int],
) -> np.ndarray:
    """Paste ``sprite`` with its top-left at ``top_left``, clamped inside ``page``."""

    height, width = sprite.mask.shape
    canvas_height, canvas_width = target.shape[:2]
    left, top, right, bottom = page
    x = int(min(max(round(top_left[0]), left), max(left, right - width)))
    y = int(min(max(round(top_left[1]), top), max(top, bottom - height)))
    full = np.zeros((canvas_height, canvas_width), dtype=bool)
    region = target[y : y + height, x : x + width]
    region[sprite.mask] = sprite.pixels[sprite.mask]
    full[y : y + height, x : x + width] = sprite.mask
    return full


def _centered(sprite: _Sprite, center: tuple[float, float]) -> tuple[float, float]:
    height, width = sprite.mask.shape
    return center[0] - width / 2, center[1] - height / 2


def _validated_layer(layer: SubjectLayer, shape: tuple[int, int], minimum: int) -> None:
    if (
        layer.mask.shape != shape
        or layer.mask.dtype != bool
        or int(layer.mask.sum()) < minimum
    ):
        raise KeyframeError("KEYFRAME_MASK_INVALID")


def _paper_colour(canvas: np.ndarray, masks: list[np.ndarray]) -> tuple[int, int, int]:
    occupied = np.zeros(canvas.shape[:2], dtype=bool)
    for mask in masks:
        occupied |= _dilate(mask, 12)
    outside = canvas[~occupied]
    if outside.size == 0:
        return (255, 255, 255)
    return tuple(int(v) for v in np.median(outside, axis=0))  # type: ignore[return-value]


def apply_background_plate(keyframe: Keyframe, plate: Image.Image) -> Image.Image:
    """FEAT-093: put the child's real subjects (main and approved secondaries) on a background plate.

    Pixels inside the subject masks, with a two pixel anti-alias margin, come from the keyframe, which holds the child's
    own drawing pixels; everything else is the plate. Nothing of the child's drawing is regenerated, so the strokes and
    the paper interior of the subjects stay exactly as drawn. The plate is fitted to the 1280x768 canvas.
    """

    base = np.asarray(plate.convert("RGB").resize((CANVAS_WIDTH, CANVAS_HEIGHT), Image.Resampling.LANCZOS)).copy()
    frame = np.asarray(keyframe.image.convert("RGB"))
    if frame.shape[:2] != base.shape[:2]:
        raise KeyframeError("KEYFRAME_PLATE_SIZE_MISMATCH")
    occupied = keyframe.main_mask.copy()
    for mask in keyframe.secondary_masks.values():
        occupied |= mask
    if not occupied.any():
        raise KeyframeError("KEYFRAME_NO_SUBJECT_TO_PLACE")
    occupied = _dilate(occupied, 2)
    base[occupied] = frame[occupied]
    return Image.fromarray(base)


def build_keyframes(
    drawing: Image.Image,
    main: SubjectLayer,
    secondaries: list[SubjectLayer],
    staging: dict[str, Any],
    *,
    source_facing: str,
    page_box: tuple[int, int, int, int] | None = None,
) -> list[Keyframe]:
    """K0 (the original) followed by one keyframe per staged scene end.

    ``page_box`` is the drawing's rectangle on the canvas; cells and clamping use it so sprites
    never leave the page for the white margin. It defaults to the whole canvas.
    """

    canvas = np.asarray(drawing.convert("RGB")).copy()
    shape = canvas.shape[:2]
    page = page_box or (0, 0, shape[1], shape[0])
    _validated_layer(main, shape, _MIN_MAIN_PIXELS)
    for layer in secondaries:
        _validated_layer(layer, shape, _MIN_SECONDARY_PIXELS)
    scenes = staging["scenes"]
    by_id = {layer.entity_id: layer for layer in secondaries}
    if not scenes or any(
        {entry["entity_id"] for entry in scene["secondary_end"]} != set(by_id)
        for scene in scenes
    ):
        raise KeyframeError("KEYFRAME_STAGING_MISMATCH")

    paper = _paper_colour(canvas, [main.mask, *[layer.mask for layer in secondaries]])
    background = canvas.copy()
    ink = keyframe_metrics.ink_mask(canvas, paper)
    layers = (main, *secondaries)
    for layer in layers:
        others = np.zeros(shape, dtype=bool)
        for other in layers:
            if other is not layer:
                others |= other.mask
        erase = _dilate(layer.mask, _ERASE_RADIUS) | (
            _dilate(layer.mask, _RESIDUE_RADIUS) & ink & ~others
        )
        background[erase] = paper

    main_sprite = _cut_sprite(canvas, main)
    sprites = {layer.entity_id: _cut_sprite(canvas, layer) for layer in secondaries}
    frames = [
        Keyframe(
            Image.fromarray(canvas.copy()),
            main.mask.copy(),
            {layer.entity_id: layer.mask.copy() for layer in secondaries},
            {"mirrored": False, "main_scale": 1.0, "paper": paper},
        )
    ]

    scale = 1.0
    secondary_position = {
        key: (sprite.origin[0], sprite.origin[1]) for key, sprite in sprites.items()
    }
    partly_side: dict[str, str] = {}
    for scene in scenes:
        main_end = scene["main_end"]
        scale = min(max(scale * _SCALE_STEP[main_end["scale"]], SCALE_MIN), SCALE_MAX)
        mirrored = (
            source_facing in ("left", "right") and main_end["facing"] != source_facing
        )
        placed_main = main_sprite.transformed(mirror=mirrored, scale=scale)
        main_top_left = _centered(placed_main, cell_center(main_end["position"], page))
        frame = background.copy()
        secondary_masks: dict[str, np.ndarray] = {}
        main_center_x = main_top_left[0] + placed_main.mask.shape[1] / 2
        states: dict[str, str] = {}
        for entry in scene["secondary_end"]:
            entity_id, state = entry["entity_id"], entry["state"]
            states[entity_id] = state
            sprite = sprites[entity_id]
            if state == "gone":
                secondary_masks[entity_id] = np.zeros(shape, dtype=bool)
                continue
            if state == "moved":
                secondary_position[entity_id] = _centered(
                    sprite, cell_center(entry["position"], page)
                )
            if state == "partly_gone":
                width = sprite.mask.shape[1]
                top_left = secondary_position[entity_id]
                side = partly_side.setdefault(
                    entity_id,
                    "left" if main_center_x < top_left[0] + width / 2 else "right",
                )
                sprite = _Sprite(sprite.pixels, _bite(sprite.mask, side), sprite.origin)
            secondary_masks[entity_id] = _paste(
                frame, sprite, top_left=secondary_position[entity_id], page=page
            )
        main_mask = _paste(frame, placed_main, top_left=main_top_left, page=page)
        overlap = {
            entity_id: float((main_mask & mask).sum() / max(int(mask.sum()), 1))
            for entity_id, mask in secondary_masks.items()
        }
        frames.append(
            Keyframe(
                Image.fromarray(frame),
                main_mask,
                secondary_masks,
                {
                    "mirrored": mirrored,
                    "main_scale": scale,
                    "main_cell": main_end["position"],
                    "secondary_states": states,
                    "overlap": overlap,
                    "paper": paper,
                },
            )
        )
    return frames
