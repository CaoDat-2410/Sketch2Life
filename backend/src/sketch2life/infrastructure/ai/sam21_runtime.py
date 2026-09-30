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
from typing import Any, Literal

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
    # Match the renderer's verified-cutout limit; choose another multimask candidate
    # rather than exporting a mask that playback will necessarily reject.
    max_area_fraction: float = 0.75

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


@dataclass(frozen=True, slots=True)
class Sam21Prompt:
    prompt_region: SourceRegionV1 | None
    positive_points: tuple[tuple[float, float], ...]
    negative_points: tuple[tuple[float, float], ...]
    refinement_group: Literal["subject", "part"] = "subject"


@dataclass(frozen=True, slots=True)
class _MaskSelection:
    mask: Any
    confidence: float
    candidate_index: int
    rank_score: float


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
        self._inference_lock = Lock()

    def segment(
        self,
        image: bytes,
        *,
        prompt_region: SourceRegionV1 | None,
        positive_points: tuple[tuple[float, float], ...],
        negative_points: tuple[tuple[float, float], ...],
    ) -> Sam21MaskOutput:
        output = self.segment_many(
            image,
            (Sam21Prompt(prompt_region, positive_points, negative_points),),
        )[0]
        if output is None:
            raise Sam21MaskRejectedError("SAM2 returned no valid mask")
        return output

    def segment_many(
        self,
        image: bytes,
        prompts: tuple[Sam21Prompt, ...],
    ) -> tuple[Sam21MaskOutput | None, ...]:
        """Encode the image once and predict a bounded set of subject/part masks."""
        if not prompts or len(prompts) > 5:
            raise ValueError("SAM2 prompt batch must contain one to five prompts")
        if any(
            prompt.prompt_region is None
            and not prompt.positive_points
            and not prompt.negative_points
            for prompt in prompts
        ):
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

        try:
            import numpy as np
        except ImportError as exc:
            raise Sam21ConfigurationError(
                "NumPy is unavailable",
                reason_code="NUMPY_UNAVAILABLE",
            ) from exc

        outputs: list[Sam21MaskOutput | None] = []
        refinement_count = 0
        refined_groups: set[str] = set()
        accepted_subject_mask: Any | None = None
        with self._inference_lock:
            predictor.set_image(array)
            for prompt in prompts:
                active_prompt = prompt
                if prompt.refinement_group == "part" and accepted_subject_mask is not None:
                    positive_points = tuple(
                        point
                        for point in prompt.positive_points
                        if _mask_contains_point(
                            accepted_subject_mask,
                            point,
                            width=width,
                            height=height,
                        )
                    )
                    active_prompt = Sam21Prompt(
                        prompt_region=prompt.prompt_region,
                        positive_points=positive_points,
                        negative_points=prompt.negative_points,
                        refinement_group=prompt.refinement_group,
                    )
                box = None
                if prompt.prompt_region is not None:
                    box = np.asarray(
                        [
                            prompt.prompt_region.x * width,
                            prompt.prompt_region.y * height,
                            (prompt.prompt_region.x + prompt.prompt_region.width) * width,
                            (prompt.prompt_region.y + prompt.prompt_region.height) * height,
                        ],
                        dtype=np.float32,
                    )
                point_coords, point_labels = _points_as_arrays(
                    active_prompt.positive_points,
                    active_prompt.negative_points,
                    width,
                    height,
                    np,
                )
                try:
                    try:
                        masks, scores, low_res_masks = predictor.predict(
                            point_coords=point_coords,
                            point_labels=point_labels,
                            box=box,
                            multimask_output=True,
                        )
                    except TypeError:
                        kwargs: dict[str, object] = {"multimask_output": True}
                        if point_coords is not None:
                            kwargs["point_coords"] = point_coords
                            kwargs["point_labels"] = point_labels
                        if box is not None:
                            kwargs["box"] = box
                        masks, scores, low_res_masks = predictor.predict(**kwargs)

                    selection = _select_prompt_consistent_candidate(
                        masks,
                        scores,
                        width=width,
                        height=height,
                        prompt=active_prompt,
                        min_area_fraction=self._config.min_area_fraction,
                        max_area_fraction=self._config.max_area_fraction,
                        numpy=np,
                        image=array,
                    )
                    correction_point = _missing_ink_correction_point(
                        array,
                        selection.mask,
                        active_prompt,
                        numpy=np,
                        parent_mask=(
                            accepted_subject_mask
                            if prompt.refinement_group == "part"
                            else None
                        ),
                    )
                    mask_input = _mask_input_for_candidate(
                        low_res_masks,
                        selection.candidate_index,
                        numpy=np,
                    )
                    # A single bounded correction round may improve the subject and one
                    # archetype-ordered part, never more than two extra SAM predictions/image.
                    if (
                        refinement_count < 2
                        and prompt.refinement_group not in refined_groups
                        and correction_point is not None
                        and mask_input is not None
                    ):
                        refined_points = tuple(
                            dict.fromkeys((*prompt.positive_points, correction_point))
                        )
                        refined_coords, refined_labels = _points_as_arrays(
                            refined_points,
                            active_prompt.negative_points,
                            width,
                            height,
                            np,
                        )
                        refinement_count += 1
                        refined_groups.add(prompt.refinement_group)
                        try:
                            refined_masks, refined_scores, _ = predictor.predict(
                                point_coords=refined_coords,
                                point_labels=refined_labels,
                                box=box,
                                mask_input=mask_input,
                                multimask_output=False,
                            )
                            refined = _select_prompt_consistent_candidate(
                                refined_masks,
                                refined_scores,
                                width=width,
                                height=height,
                                prompt=Sam21Prompt(
                                    prompt_region=prompt.prompt_region,
                                    positive_points=refined_points,
                                    negative_points=active_prompt.negative_points,
                                    refinement_group=prompt.refinement_group,
                                ),
                                min_area_fraction=self._config.min_area_fraction,
                                max_area_fraction=self._config.max_area_fraction,
                                numpy=np,
                                image=array,
                            )
                            if refined.rank_score > selection.rank_score:
                                selection = refined
                        except (RuntimeError, TypeError, ValueError):
                            # Refinement is an optional quality pass. A valid initial mask stays
                            # usable if the one bounded pass is unsupported or fails.
                            pass

                    if prompt.refinement_group == "subject":
                        accepted_subject_mask = selection.mask
                    mask = selection.mask
                    confidence = selection.confidence
                    ys, xs = np.where(mask)
                    if len(xs) == 0 or len(ys) == 0:
                        raise Sam21MaskRejectedError("SAM2 returned an empty mask")
                    region = SourceRegionV1(
                        x=float(xs.min() / width),
                        y=float(ys.min() / height),
                        width=float((xs.max() + 1 - xs.min()) / width),
                        height=float((ys.max() + 1 - ys.min()) / height),
                    )
                    output = Image.fromarray((mask.astype("uint8") * 255), mode="L")
                    buffer = io.BytesIO()
                    output.save(buffer, format="PNG", optimize=True)
                    outputs.append(
                        Sam21MaskOutput(
                            source_region=region,
                            confidence=confidence,
                            mask_png=buffer.getvalue(),
                        )
                    )
                except Sam21MaskRejectedError:
                    # A bad part prompt must not discard an already valid parent silhouette.
                    outputs.append(None)
        return tuple(outputs)

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


def _select_prompt_consistent_candidate(
    masks: Any,
    scores: Any,
    *,
    width: int,
    height: int,
    prompt: Sam21Prompt,
    min_area_fraction: float,
    max_area_fraction: float,
    numpy: Any,
    image: Any | None = None,
) -> _MaskSelection:
    """Choose the highest-scoring valid SAM candidate consistent with its prompt."""
    candidates = numpy.asarray(masks)
    if candidates.ndim == 2:
        candidates = candidates[numpy.newaxis, ...]
    if candidates.ndim != 3 or candidates.shape[1:] != (height, width):
        raise Sam21MaskRejectedError("SAM2 returned invalid candidate mask dimensions")
    confidence_scores = numpy.asarray(scores, dtype=float).reshape(-1)
    if len(confidence_scores) != len(candidates):
        raise Sam21MaskRejectedError("SAM2 returned mismatched mask candidate scores")

    box_bounds = None
    if prompt.prompt_region is not None:
        region = prompt.prompt_region
        left = max(0, min(width, int(region.x * width)))
        top = max(0, min(height, int(region.y * height)))
        right = max(left + 1, min(width, int(numpy.ceil((region.x + region.width) * width))))
        bottom = max(top + 1, min(height, int(numpy.ceil((region.y + region.height) * height))))
        box_bounds = (left, top, right, bottom)

    def point_is_inside(mask: Any, point: tuple[float, float]) -> bool:
        x = max(0, min(width - 1, int(point[0] * width)))
        y = max(0, min(height - 1, int(point[1] * height)))
        return bool(mask[y, x])

    valid: list[tuple[float, int, Any, float]] = []
    for index, candidate in enumerate(candidates):
        mask = candidate.astype(bool)
        area_fraction = float(mask.mean())
        if not min_area_fraction <= area_fraction <= max_area_fraction:
            continue
        if any(not point_is_inside(mask, point) for point in prompt.positive_points):
            continue
        if any(point_is_inside(mask, point) for point in prompt.negative_points):
            continue
        prompt_fit = 1.0
        if box_bounds is not None:
            left, top, right, bottom = box_bounds
            in_box = int(mask[top:bottom, left:right].sum())
            if in_box == 0:
                continue
            outside_fraction = 1.0 - in_box / max(1, int(mask.sum()))
            if outside_fraction > 0.45:
                continue
            prompt_fit = 1.0 - outside_fraction
        score = float(confidence_scores[index])
        if not numpy.isfinite(score):
            continue
        boundary_fit = (
            _boundary_alignment_score(image, mask, numpy=numpy) if image is not None else 0.0
        )
        component_fit = _largest_component_fraction(mask, numpy=numpy)
        # Keep SAM's score dominant; prompt fit, connectedness, and source boundaries only
        # resolve close candidates and never modify the accepted source mask.
        rank_score = score + 0.02 * prompt_fit + 0.01 * component_fit + 0.01 * boundary_fit
        valid.append((rank_score, index, mask, score))
    if not valid:
        raise Sam21MaskRejectedError("SAM2 returned no prompt-consistent mask candidate")
    rank_score, selected_index, mask, confidence_score = max(
        valid, key=lambda item: (item[0], -item[1])
    )
    confidence = min(max(confidence_score, 0.0), 1.0)
    return _MaskSelection(mask, confidence, selected_index, rank_score)


def _boundary_alignment_score(image: Any, mask: Any, *, numpy: Any) -> float:
    """Measure source-color contrast along a candidate boundary as a bounded tie-breaker."""

    pixels = numpy.asarray(image)
    binary = numpy.asarray(mask, dtype=bool)
    if pixels.ndim != 3 or pixels.shape[:2] != binary.shape or pixels.shape[2] < 3:
        return 0.0
    contrast_sum = 0.0
    edge_count = 0
    horizontal = binary[:, :-1] != binary[:, 1:]
    if horizontal.any():
        ys, xs = numpy.nonzero(horizontal)
        inside = pixels[ys, xs, :3].astype(numpy.int16)
        outside = pixels[ys, xs + 1, :3].astype(numpy.int16)
        contrast_sum += float(numpy.abs(inside - outside).mean(axis=1).sum())
        edge_count += len(xs)
    vertical = binary[:-1, :] != binary[1:, :]
    if vertical.any():
        ys, xs = numpy.nonzero(vertical)
        inside = pixels[ys, xs, :3].astype(numpy.int16)
        outside = pixels[ys + 1, xs, :3].astype(numpy.int16)
        contrast_sum += float(numpy.abs(inside - outside).mean(axis=1).sum())
        edge_count += len(xs)
    if edge_count == 0:
        return 0.0
    return min(1.0, max(0.0, contrast_sum / edge_count / 255.0))


def _largest_component_fraction(mask: Any, *, numpy: Any) -> float:
    """Return the largest 8-connected component's share using row-run labeling."""

    binary = numpy.asarray(mask, dtype=bool)
    if binary.ndim != 2:
        return 0.0
    total_area = int(binary.sum())
    if total_area == 0:
        return 0.0

    parents: list[int] = []
    areas: list[int] = []

    def find(node: int) -> int:
        root = node
        while parents[root] != root:
            root = parents[root]
        while parents[node] != node:
            parent = parents[node]
            parents[node] = root
            node = parent
        return root

    def union(left: int, right: int) -> None:
        left_root, right_root = find(left), find(right)
        if left_root == right_root:
            return
        parents[right_root] = left_root
        areas[left_root] += areas[right_root]

    previous_runs: list[tuple[int, int, int]] = []
    for row in binary:
        padded = numpy.pad(row, (1, 1), mode="constant", constant_values=False)
        starts = numpy.flatnonzero(padded[1:] & ~padded[:-1]).tolist()
        ends = numpy.flatnonzero(padded[:-1] & ~padded[1:]).tolist()
        current_runs: list[tuple[int, int, int]] = []
        previous_index = 0
        for start, end in zip(starts, ends, strict=True):
            node = len(parents)
            parents.append(node)
            areas.append(end - start)
            while previous_index < len(previous_runs) and previous_runs[previous_index][1] < start:
                previous_index += 1
            overlap_index = previous_index
            while (
                overlap_index < len(previous_runs)
                and previous_runs[overlap_index][0] <= end
            ):
                previous_start, previous_end, previous_node = previous_runs[overlap_index]
                if previous_end >= start and previous_start <= end:
                    union(node, previous_node)
                overlap_index += 1
            current_runs.append((start, end, node))
        previous_runs = current_runs

    largest = max(areas[find(node)] for node in range(len(parents)))
    return min(1.0, max(0.0, largest / total_area))


def _mask_input_for_candidate(low_res_masks: Any, index: int, *, numpy: Any) -> Any | None:
    logits = numpy.asarray(low_res_masks)
    if logits.ndim == 4 and logits.shape[0] == 1:
        logits = logits[0]
    if logits.ndim == 2:
        selected = logits
    elif logits.ndim == 3 and 0 <= index < logits.shape[0]:
        selected = logits[index]
    else:
        return None
    if selected.ndim != 2 or not numpy.isfinite(selected).all():
        return None
    return selected[numpy.newaxis, :, :].astype(numpy.float32, copy=False)


def _missing_ink_correction_point(
    image: Any,
    mask: Any,
    prompt: Sam21Prompt,
    *,
    numpy: Any,
    parent_mask: Any | None = None,
) -> tuple[float, float] | None:
    """Find one coherent ink stroke just outside the selected mask and inside its prompt ROI."""

    pixels = numpy.asarray(image)
    binary = numpy.asarray(mask, dtype=bool)
    if pixels.ndim != 3 or pixels.shape[:2] != binary.shape or pixels.shape[2] < 3:
        return None
    height, width = binary.shape
    rgb = pixels[:, :, :3].astype(numpy.int16)
    ink = (
        ((rgb.max(axis=2) - rgb.min(axis=2) >= 20) & (rgb.min(axis=2) < 245))
        | (rgb.max(axis=2) < 95)
    )
    near_mask = binary.copy()
    for _ in range(2):
        padded = numpy.pad(near_mask, 1, mode="constant", constant_values=False)
        expanded = numpy.zeros_like(near_mask)
        for dy in range(3):
            for dx in range(3):
                expanded |= padded[dy : dy + height, dx : dx + width]
        near_mask = expanded
    missing = ink & ~binary & near_mask
    if parent_mask is not None:
        parent = numpy.asarray(parent_mask, dtype=bool)
        if parent.shape != binary.shape:
            return None
        missing &= parent
    if prompt.prompt_region is not None:
        region = prompt.prompt_region
        left = max(0, min(width, int(region.x * width)))
        top = max(0, min(height, int(region.y * height)))
        right = max(left + 1, min(width, int(numpy.ceil((region.x + region.width) * width))))
        bottom = max(top + 1, min(height, int(numpy.ceil((region.y + region.height) * height))))
        roi = numpy.zeros_like(binary)
        roi[top:bottom, left:right] = True
        missing &= roi
    if not missing.any():
        return None
    ys, xs = numpy.where(missing)
    if len(xs) > 512:
        sample_indices = numpy.linspace(0, len(xs) - 1, 512, dtype=int)
        xs, ys = xs[sample_indices], ys[sample_indices]
    best: tuple[int, int, int] | None = None
    for x, y in zip(xs.tolist(), ys.tolist(), strict=True):
        y0, y1 = max(0, y - 2), min(height, y + 3)
        x0, x1 = max(0, x - 2), min(width, x + 3)
        local_ink = int(ink[y0:y1, x0:x1].sum())
        if local_ink < 3:
            continue
        candidate = (local_ink, -y, -x)
        if best is None or candidate > best:
            best = candidate
    if best is None:
        return None
    x, y = -best[2], -best[1]
    existing_points = (*prompt.positive_points, *prompt.negative_points)
    if any(
        (x / width - px) ** 2 + (y / height - py) ** 2
        < (3 / max(width, height)) ** 2
        for px, py in existing_points
    ):
        return None
    return ((x + 0.5) / width, (y + 0.5) / height)


def _mask_contains_point(
    mask: Any,
    point: tuple[float, float],
    *,
    width: int,
    height: int,
) -> bool:
    binary = mask
    if getattr(binary, "shape", None) != (height, width):
        return False
    x = max(0, min(width - 1, int(point[0] * width)))
    y = max(0, min(height - 1, int(point[1] * height)))
    return bool(binary[y, x])


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
    "Sam21Prompt",
    "Sam21MaskRejectedError",
    "Sam21PromptRequiredError",
    "Sam21RuntimeConfig",
    "Sam21RuntimeError",
]
