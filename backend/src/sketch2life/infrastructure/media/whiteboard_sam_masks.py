"""Turn SAM2 object masks into verified, stroke-space scene cue masks."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from sketch2life.contracts.schemas.story_video import StoryboardDrawBeatV1


def predict_stroke_space_masks(
    illustration_path: str | Path,
    stroke_path: str | Path,
    beats: tuple[StoryboardDrawBeatV1, ...],
    predictor,
) -> tuple:
    import numpy as np
    from PIL import Image, ImageFilter

    if not beats:
        raise ValueError("DRAW_BEATS_REQUIRED_FOR_SAM")
    illustration_path = Path(illustration_path)
    stroke_path = Path(stroke_path)
    with illustration_path.open("rb") as source:
        illustration_hash = hashlib.file_digest(source, "sha256").hexdigest()
    with stroke_path.open("rb") as source:
        stroke_hash = hashlib.file_digest(source, "sha256").hexdigest()
    payload = json.loads(stroke_path.read_text(encoding="utf-8"))
    if payload.get("source_hash") != illustration_hash:
        raise ValueError("DRAW_MASK_SOURCE_MISMATCH")
    source_width = int(payload["source_width"])
    source_height = int(payload["source_height"])
    left, top, right, bottom = (int(value) for value in payload["crop_box"])
    if not (0 <= left < right <= source_width and 0 <= top < bottom <= source_height):
        raise ValueError("DRAW_MASK_CROP_INVALID")
    with Image.open(illustration_path) as source:
        image = source.convert("RGB")
    original_width, original_height = image.size
    predictor.set_image(np.asarray(image))

    original_masks = []
    for beat in beats:
        x1, y1, x2, y2 = beat.focus_box
        box = np.asarray([
            x1 * original_width, y1 * original_height,
            x2 * original_width, y2 * original_height,
        ], dtype=np.float32)
        masks, scores, _ = predictor.predict(box=box, multimask_output=True)
        candidates = np.asarray(masks)
        confidence = np.asarray(scores)
        if candidates.ndim != 3 or candidates.shape[1:] != (original_height, original_width):
            raise ValueError("DRAW_MASK_INVALID")
        if confidence.shape != (candidates.shape[0],) or not np.isfinite(confidence).all():
            raise ValueError("DRAW_MASK_INVALID")
        selected = candidates[int(np.argmax(confidence))] > 0.5
        coverage = float(selected.mean())
        if not 0.001 <= coverage <= 0.85:
            raise ValueError("DRAW_MASK_COVERAGE_INVALID")
        bounds = (
            max(0, int(y1 * original_height)), min(original_height, int(y2 * original_height) + 1),
            max(0, int(x1 * original_width)), min(original_width, int(x2 * original_width) + 1),
        )
        within = int(selected[bounds[0]:bounds[1], bounds[2]:bounds[3]].sum())
        if within / int(selected.sum()) < 0.15:
            raise ValueError("DRAW_MASK_BOX_MISMATCH")
        original_masks.append(selected)

    for index, mask in enumerate(original_masks):
        for prior in original_masks[:index]:
            overlap_ratio = int(np.logical_and(mask, prior).sum()) / min(
                int(mask.sum()), int(prior.sum())
            )
            if overlap_ratio > 0.6:
                raise ValueError("DRAW_MASK_OVERLAP")

    output_masks = []
    manifest_masks = []
    for beat, mask in zip(beats, original_masks, strict=True):
        resized = Image.fromarray(mask.astype(np.uint8) * 255).resize(
            (source_width, source_height), Image.Resampling.NEAREST
        )
        cropped = resized.crop((left, top, right, bottom))
        if cropped.size != (payload["width"], payload["height"]):
            raise ValueError("DRAW_MASK_CROP_INVALID")
        if not np.asarray(cropped).any():
            raise ValueError("DRAW_MASK_EMPTY_AFTER_CROP")
        artifact = stroke_path.parent / f"{stroke_path.stem}.{beat.element_id}.sam2-mask.png"
        cropped.save(artifact)
        with artifact.open("rb") as source:
            mask_hash = hashlib.file_digest(source, "sha256").hexdigest()
        expanded = cropped.filter(ImageFilter.MaxFilter(5))
        output_masks.append(np.asarray(expanded) > 0)
        manifest_masks.append({
            "element_id": beat.element_id,
            "mask_ref": str(artifact),
            "mask_sha256": mask_hash,
        })
    manifest = stroke_path.with_suffix(".sam2-masks.json")
    manifest.write_text(json.dumps({
        "model": "facebook/sam2.1-hiera-small",
        "illustration_sha256": illustration_hash,
        "strokes_sha256": stroke_hash,
        "masks": manifest_masks,
    }, sort_keys=True), encoding="utf-8")
    return tuple(output_masks)
