"""Lazy SAM 2.1 image-prompt runtime for the Lightning worker.

This module intentionally imports torch, SAM2, Pillow and NumPy only when the first
segmentation request arrives.  The normal backend/test process therefore remains usable
without the optional GPU stack.  The runtime accepts a validated box and/or points; it never
turns a missing prompt into a full-frame mask.
"""

from __future__ import annotations

import importlib.util
import io
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any

from sketch2life.contracts.schemas.scene_exploration import SourceRegionV1


class Sam21RuntimeError(RuntimeError):
    """Base class for sanitized SAM2 runtime failures."""


class Sam21ConfigurationError(Sam21RuntimeError):
    """A safe, operator-facing configuration failure with a closed reason code."""

    def __init__(
        self,
        message: str,
        *,
        reason_code: str = "RUNTIME_DEPENDENCIES_UNAVAILABLE",
    ) -> None:
        super().__init__(message)
        self.reason_code = reason_code


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
        model_root_text = (
            values.get("SKETCH2LIFE_SAM21_MODEL_DIR", "").strip()
            or values.get("SAM2_MODEL_DIR", "").strip()
            or values.get("SAM2_ROOT", "").strip()
        )
        model_root = Path(model_root_text).expanduser() if model_root_text else None
        checkpoint = _resolve_checkpoint(checkpoint_text, model_root)
        model_config_text = values.get(
            "SKETCH2LIFE_SAM21_MODEL_CONFIG",
            "configs/sam2.1/sam2.1_hiera_s.yaml",
        ).strip()
        return cls(
            checkpoint=checkpoint,
            model_config=_resolve_model_config(model_config_text, model_root),
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
            raise Sam21ConfigurationError(
                "Pillow is unavailable",
                reason_code="PILLOW_UNAVAILABLE",
            ) from exc

        with Image.open(io.BytesIO(image)) as source:
            rgb = source.convert("RGB")
            width, height = rgb.size
            array = self._image_array(rgb)
        predictor = self._get_predictor()
        predictor.set_image(array)

        try:
            import numpy as np
        except ImportError as exc:
            raise Sam21ConfigurationError(
                "NumPy is unavailable",
                reason_code="NUMPY_UNAVAILABLE",
            ) from exc

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
            raise Sam21ConfigurationError(
                "NumPy is unavailable",
                reason_code="NUMPY_UNAVAILABLE",
            ) from exc
        return np.asarray(image)

    def _get_predictor(self) -> Any:
        if self._predictor is not None:
            return self._predictor
        with self._lock:
            if self._predictor is not None:
                return self._predictor
            if self._config.checkpoint is None or not self._config.checkpoint.is_file():
                raise Sam21ConfigurationError(
                    "SAM2.1 checkpoint is not configured",
                    reason_code="CHECKPOINT_NOT_FOUND",
                )
            if not self._config.model_config:
                raise Sam21ConfigurationError(
                    "SAM2.1 model config is not configured",
                    reason_code="MODEL_CONFIG_NOT_FOUND",
                )
            try:
                _add_sam2_source_path()
                import torch
                from sam2.build_sam import build_sam2
                from sam2.sam2_image_predictor import SAM2ImagePredictor
            except ImportError as exc:
                raise Sam21ConfigurationError(
                    "SAM2.1 runtime dependencies are unavailable",
                    reason_code="RUNTIME_DEPENDENCIES_UNAVAILABLE",
                ) from exc
            if self._config.device.startswith("cuda") and not torch.cuda.is_available():
                raise Sam21ConfigurationError(
                    "CUDA is unavailable for SAM2.1",
                    reason_code="CUDA_UNAVAILABLE",
                )
            model = build_sam2(
                self._config.model_config,
                str(self._config.checkpoint),
                device=self._config.device,
                apply_postprocessing=False,
            )
            self._predictor = SAM2ImagePredictor(model)
            return self._predictor


_CHECKPOINT_NAMES = (
    "sam2.1_hiera_small.pt",
    "sam2.1_hiera_small.pth",
    "sam2.1_hiera_s.pt",
    "sam2.1_hiera_s.pth",
    "sam2_hiera_small.pt",
    "sam2_hiera_small.pth",
)


def _resolve_checkpoint(checkpoint_text: str, model_root: Path | None) -> Path | None:
    candidates: list[Path] = []
    if checkpoint_text:
        explicit = Path(checkpoint_text).expanduser()
        candidates.append(explicit if explicit.is_absolute() else Path.cwd() / explicit)
    if model_root is not None:
        root = model_root if model_root.is_dir() else model_root.parent
        candidates.extend(
            candidate
            for base in (root, root / "checkpoints")
            for candidate in (base / name for name in _CHECKPOINT_NAMES)
        )
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    if checkpoint_text:
        explicit = Path(checkpoint_text).expanduser()
        return (explicit if explicit.is_absolute() else Path.cwd() / explicit).resolve()
    return None


def _resolve_model_config(config_text: str, model_root: Path | None) -> str:
    if not config_text:
        return ""
    config_path = Path(config_text).expanduser()
    # Meta's build_sam2 passes this value to Hydra as ``config_name``. Hydra expects
    # the package-relative name (for example ``configs/sam2.1/sam2.1_hiera_s.yaml``),
    # not the absolute filesystem path that operators commonly put in env files.
    if config_path.is_absolute():
        normalized = _config_name_from_absolute_path(config_path)
        if normalized is not None:
            return normalized

    relative_paths = [config_path]
    if config_path.parts[:1] != ("configs",):
        relative_paths.append(Path("configs") / config_path)
    roots = [Path.cwd()]
    if model_root is not None:
        root = model_root if model_root.is_dir() else model_root.parent
        roots.append(root)
        if (root / "sam2").is_dir():
            roots.append(root / "sam2")
    try:
        sam2_spec = importlib.util.find_spec("sam2")
    except (ImportError, ValueError):
        sam2_spec = None
    if sam2_spec is not None and sam2_spec.submodule_search_locations:
        roots.extend(Path(location) for location in sam2_spec.submodule_search_locations)

    for root in roots:
        for relative in relative_paths:
            candidate = root / relative
            if candidate.is_file():
                return _as_hydra_config_name(relative)
    # Keep the Hydra config name when the installed SAM2 package owns the config search path.
    return config_text


def _config_name_from_absolute_path(config_path: Path) -> str | None:
    parts = config_path.parts
    try:
        configs_index = len(parts) - 1 - tuple(reversed(parts)).index("configs")
    except ValueError:
        return None
    return _as_hydra_config_name(Path(*parts[configs_index:]))


def _as_hydra_config_name(path: Path) -> str:
    return path.as_posix().lstrip("/")


def _add_sam2_source_path() -> None:
    """Make a vendored SAM2 checkout importable without requiring a global install."""

    for env_name in ("SKETCH2LIFE_SAM21_MODEL_DIR", "SAM2_MODEL_DIR", "SAM2_ROOT"):
        raw_root = os.getenv(env_name, "").strip()
        if not raw_root:
            continue
        root = Path(raw_root).expanduser()
        if not root.is_dir() or not (root / "sam2").is_dir():
            continue
        resolved_root = str(root.resolve())
        if resolved_root not in sys.path:
            sys.path.insert(0, resolved_root)
        return


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
