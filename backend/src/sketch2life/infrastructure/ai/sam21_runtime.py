"""Lazy SAM 2.1 image-prompt runtime for the Lightning worker.

This module intentionally imports torch, SAM2, Pillow and NumPy only when the first
segmentation request arrives.  The normal backend/test process therefore remains usable
without the optional GPU stack.  The runtime accepts a validated box and/or points; it never
turns a missing prompt into a full-frame mask.
"""

from __future__ import annotations

import io
import os
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any

from sketch2life.contracts.schemas.scene_exploration import SourceRegionV1


class Sam21RuntimeError(RuntimeError):
    """Base class for sanitized SAM2 runtime failures."""


class Sam21ConfigurationError(Sam21RuntimeError):
    pass


class Sam21PromptRequiredError(Sam21RuntimeError):
    pass


class Sam21MaskRejectedError(Sam21RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class Sam21RuntimeConfig:
    checkpoint: Path | None
    model_config: str
    device: str
    min_area_fraction: float = 0.002
    max_area_fraction: float = 0.85

    @classmethod
    def from_env(cls, environ: dict[str, str] | None = None) -> Sam21RuntimeConfig:
        values = os.environ if environ is None else environ
        checkpoint_text = values.get("SKETCH2LIFE_SAM21_CHECKPOINT", "").strip()
        return cls(
            checkpoint=Path(checkpoint_text) if checkpoint_text else None,
            model_config=values.get(
                "SKETCH2LIFE_SAM21_MODEL_CONFIG",
                "configs/sam2.1/sam2.1_hiera_s.yaml",
            ).strip(),
            device=values.get("SKETCH2LIFE_SAM21_DEVICE", "cuda").strip() or "cuda",
        )


@dataclass(frozen=True, slots=True)
class Sam21MaskOutput:
    source_region: SourceRegionV1
    confidence: float
    mask_png: bytes


class Sam21ImageSegmenter:
    """Process-scoped SAM2.1 predictor with serialized lazy initialization."""

    def __init__(
        self,
        config: Sam21RuntimeConfig,
        *,
        predictor: Any | None = None,
    ) -> None:
        self._config = config
        self._predictor = predictor
        self._lock = Lock()

    def segment(
        self,
        image: bytes,
        *,
        prompt_region: SourceRegionV1 | None,
        positive_points: tuple[tuple[float, float], ...],
        negative_points: tuple[tuple[float, float], ...],
    ) -> Sam21MaskOutput:
        if prompt_region is None and not positive_points and not negative_points:
            raise Sam21PromptRequiredError("SAM2 requires a bounded box or point prompt")
        try:
            from PIL import Image
        except ImportError as exc:
            raise Sam21ConfigurationError("Pillow is unavailable") from exc

        with Image.open(io.BytesIO(image)) as source:
            rgb = source.convert("RGB")
            width, height = rgb.size
            array = self._image_array(rgb)
        predictor = self._get_predictor()
        predictor.set_image(array)

        try:
            import numpy as np
        except ImportError as exc:
            raise Sam21ConfigurationError("NumPy is unavailable") from exc

        box = None
        if prompt_region is not None:
            box = np.asarray(
                [
                    prompt_region.x * width,
                    prompt_region.y * height,
                    (prompt_region.x + prompt_region.width) * width,
                    (prompt_region.y + prompt_region.height) * height,
                ],
                dtype=np.float32,
            )
        point_coords, point_labels = _points_as_arrays(
            positive_points, negative_points, width, height, np
        )
        try:
            masks, scores, _ = predictor.predict(
                point_coords=point_coords,
                point_labels=point_labels,
                box=box,
                multimask_output=False,
            )
        except TypeError:
            # Some SAM2 releases omit optional None arguments from the predictor signature.
            kwargs: dict[str, object] = {"multimask_output": False}
            if point_coords is not None:
                kwargs["point_coords"] = point_coords
                kwargs["point_labels"] = point_labels
            if box is not None:
                kwargs["box"] = box
            masks, scores, _ = predictor.predict(**kwargs)

        mask = np.asarray(masks)[0].astype(bool)
        if mask.ndim != 2 or mask.shape != (height, width):
            raise Sam21MaskRejectedError("SAM2 returned an invalid mask shape")
        area_fraction = float(mask.mean())
        if not self._config.min_area_fraction <= area_fraction <= self._config.max_area_fraction:
            raise Sam21MaskRejectedError("SAM2 mask area is outside the safe range")
        ys, xs = np.where(mask)
        if len(xs) == 0 or len(ys) == 0:
            raise Sam21MaskRejectedError("SAM2 returned an empty mask")
        region = SourceRegionV1(
            x=float(xs.min() / width),
            y=float(ys.min() / height),
            width=float((xs.max() + 1 - xs.min()) / width),
            height=float((ys.max() + 1 - ys.min()) / height),
        )
        confidence = float(np.asarray(scores).reshape(-1)[0])
        confidence = min(max(confidence, 0.0), 1.0)
        output = Image.fromarray((mask.astype("uint8") * 255), mode="L")
        buffer = io.BytesIO()
        output.save(buffer, format="PNG", optimize=True)
        return Sam21MaskOutput(
            source_region=region,
            confidence=confidence,
            mask_png=buffer.getvalue(),
        )

    @staticmethod
    def _image_array(image: Any) -> Any:
        try:
            import numpy as np
        except ImportError as exc:
            raise Sam21ConfigurationError("NumPy is unavailable") from exc
        return np.asarray(image)

    def _get_predictor(self) -> Any:
        if self._predictor is not None:
            return self._predictor
        with self._lock:
            if self._predictor is not None:
                return self._predictor
            if self._config.checkpoint is None or not self._config.checkpoint.is_file():
                raise Sam21ConfigurationError("SAM2.1 checkpoint is not configured")
            if not self._config.model_config:
                raise Sam21ConfigurationError("SAM2.1 model config is not configured")
            try:
                import torch
                from sam2.build_sam import build_sam2
                from sam2.sam2_image_predictor import SAM2ImagePredictor
            except ImportError as exc:
                raise Sam21ConfigurationError(
                    "SAM2.1 runtime dependencies are unavailable"
                ) from exc
            if self._config.device.startswith("cuda") and not torch.cuda.is_available():
                raise Sam21ConfigurationError("CUDA is unavailable for SAM2.1")
            model = build_sam2(
                self._config.model_config,
                str(self._config.checkpoint),
                device=self._config.device,
                apply_postprocessing=False,
            )
            self._predictor = SAM2ImagePredictor(model)
            return self._predictor


def _points_as_arrays(
    positive: tuple[tuple[float, float], ...],
    negative: tuple[tuple[float, float], ...],
    width: int,
    height: int,
    numpy: Any,
) -> tuple[Any | None, Any | None]:
    points = (*positive, *negative)
    if not points:
        return None, None
    coords = numpy.asarray([[x * width, y * height] for x, y in points], dtype=numpy.float32)
    labels = numpy.asarray([1] * len(positive) + [0] * len(negative), dtype=numpy.int32)
    return coords, labels


__all__ = [
    "Sam21ConfigurationError",
    "Sam21ImageSegmenter",
    "Sam21MaskOutput",
    "Sam21MaskRejectedError",
    "Sam21PromptRequiredError",
    "Sam21RuntimeConfig",
    "Sam21RuntimeError",
]
