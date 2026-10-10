"""Validated authored override adapter into existing semantic renderer, no auto cleanup."""

from __future__ import annotations

import hashlib
import io
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image

from sketch2life.contracts.schemas.semantic_authoring_v1 import SemanticAuthoringPackV1
from sketch2life.contracts.schemas.semantic_drawing_v2 import SemanticStroke
from sketch2life.contracts.schemas.story_strokes_v2 import ObjectStrokeV2
from sketch2life.infrastructure.media.semantic_drawing_engine_v2 import (
    SemanticAsset,
    contours,
    footprint,
)
from sketch2life.infrastructure.media.whiteboard_slice_feasibility import (
    PacingAssumptions,
    timed_pen_paths,
)


def hashed(ref: str, expected: str, base: Path) -> bytes:
    if "://" in ref:
        raise ValueError("LOCAL_AUTHORING_ONLY")
    p = Path(ref)
    if not p.is_absolute():
        p = base / p
    body = p.read_bytes()
    if hashlib.sha256(body).hexdigest() != expected:
        raise ValueError("SOURCE_ASSET_MISMATCH")
    return body


def continuous_region_paths(
    mask: np.ndarray, name: str, width: int = 8
) -> tuple[ObjectStrokeV2, ...]:
    """Authoring helper: true boundary pass plus connected mask-contained hatches.

    No dot cleanup. Missing pigment goes to review rather than silent generated paths.
    Brush width is explicit authored data, independent of target duration.
    """
    if not 1 <= width <= 32:
        raise ValueError("NEEDS_AUTHORING_REVIEW: invalid brush width")
    h, w = mask.shape
    paths: list[ObjectStrokeV2] = []

    def add(points):
        if len(set(points)) < 2:
            return
        paths.append(
            ObjectStrokeV2(
                stroke_id=f"color-{name}-{len(paths)}",
                phase="COLOR",
                points=tuple(points),
                brush_width=width,
                color_rgb=(0, 0, 0),
            )
        )

    # Boundary traversal covers small/antialias tips by a real contour, not hundreds of dots.
    for p in contours(mask):
        add(p)
    current: list[tuple[int, int]] = []
    step = max(1, width // 2)
    ys = np.flatnonzero(mask.any(axis=1))
    if not len(ys):
        return ()
    row_number = 0
    for y in range(int(ys[0]), int(ys[-1]) + 1, step):
        xs = np.flatnonzero(mask[y])
        runs = np.split(xs, np.where(np.diff(xs) > 1)[0] + 1)
        if row_number % 2:
            runs = runs[::-1]
        for run in runs:
            if len(run) < 2:
                continue  # Boundary pass covers tips; validation decides if sufficient.
            points = [(int(x), y) for x in run]
            if row_number % 2:
                points.reverse()
            if current:
                a, b = current[-1], points[0]
                distance = math.dist(a, b)
                n = max(1, math.ceil(distance))
                bridge = [
                    (round(a[0] + (b[0] - a[0]) * t / n), round(a[1] + (b[1] - a[1]) * t / n))
                    for t in range(n + 1)
                ]
                if distance <= width * 2 and all(mask[py, px] for px, py in bridge):
                    current.extend(bridge[1:])
                else:
                    add(current)
                    current = []
            current.extend(points)
        row_number += 1
    add(current)
    return tuple(paths)


def compile_pack(
    pack_path: Path, review_output: Path | None = None
) -> tuple[SemanticAsset, dict, dict]:
    pack = SemanticAuthoringPackV1.model_validate_json(pack_path.read_bytes())
    source = Image.open(
        io.BytesIO(hashed(pack.asset_ref, pack.asset_sha256, pack_path.parent))
    ).convert("RGBA")
    if max(source.size) > 2048 or source.width * source.height > 512 * 512:
        raise ValueError("NEEDS_AUTHORING_REVIEW: canvas budget")
    active = np.asarray(source)[:, :, 3] > 0
    if not active.any():
        raise ValueError("NEEDS_AUTHORING_REVIEW: empty source")
    regions = {}
    union = np.zeros(active.shape, dtype=bool)
    for region_spec in pack.regions:
        region_image = Image.open(
            io.BytesIO(hashed(region_spec.mask_ref, region_spec.mask_sha256, pack_path.parent))
        ).convert("L")
        if region_image.size != source.size:
            raise ValueError("NEEDS_AUTHORING_REVIEW: mask coordinate mismatch")
        selected = np.asarray(region_image) > 0
        if np.any(selected & ~active):
            raise ValueError("NEEDS_AUTHORING_REVIEW: region outside asset")
        regions[region_spec.region_id] = selected
        union |= selected
    if not np.array_equal(union, active):
        raise ValueError("NEEDS_AUTHORING_REVIEW: regions do not cover asset")
    by_id = {s.path.stroke_id: s for s in pack.strokes}
    ordered = [by_id[i] for i in pack.stroke_order]
    strokes = []
    ink_mask = np.zeros(active.shape, dtype=bool)
    cover = {r: np.zeros(active.shape, dtype=bool) for r in regions}
    for spec in ordered:
        p = spec.path
        if any(not 0 <= x < source.width or not 0 <= y < source.height for x, y in p.points):
            raise ValueError("NEEDS_AUTHORING_REVIEW: path outside canvas")
        mask = footprint(source.size, p, 1.0) & active
        if p.phase == "COLOR":
            if len(set(p.points)) < 2:
                raise ValueError("NEEDS_AUTHORING_REVIEW: color dot cleanup disallowed")
            cover[spec.region_id] |= mask & regions[spec.region_id]
        else:
            ink_mask |= mask
        strokes.append(SemanticStroke(p, spec.role, spec.region_id, spec.essential))
    missing = {name: int((mask & ~cover[name]).sum()) for name, mask in regions.items()}
    if any(missing.values()):
        if review_output is not None:
            review_output.mkdir(parents=True, exist_ok=True)
            for name, mask in regions.items():
                if missing[name]:
                    preview = source.copy()
                    array = np.asarray(preview).copy()
                    array[mask & ~cover[name]] = (255, 0, 140, 255)
                    # Region IDs never become user-controlled filesystem paths.
                    Image.fromarray(array).save(
                        review_output / f"missing-region-{list(regions).index(name)}.png"
                    )
            (review_output / "coverage-review.json").write_text(
                json.dumps(missing), encoding="utf-8"
            )
        raise ValueError("NEEDS_AUTHORING_REVIEW: uncovered region pixels " + json.dumps(missing))
    array = np.asarray(source).copy()
    gray = np.minimum(np.asarray(source.convert("L")), 90)
    array[:, :, :3] = gray[:, :, None]
    array[:, :, 3] = np.where(ink_mask, np.asarray(source)[:, :, 3], 0)
    asset = SemanticAsset(
        pack.object_id,
        source,
        pack.provenance,
        pack.source_image_sha256,
        regions,
        tuple(strokes),
        Image.fromarray(array),
        pack.approval,
        {
            "source_sha256": pack.source_image_sha256,
            "asset_sha256": pack.asset_sha256,
            "ink_provenance": pack.ink_provenance,
            "authoring_version": pack.version,
            "authoring_method": pack.authoring_method,
            "route": pack.route,
            "original_stroke_history_recovered": False,
            "presentation_scale": pack.presentation_scale,
        },
    )
    scale = pack.presentation_scale
    pacing = PacingAssumptions(
        ink_pixels_per_second=180 / scale,
        color_pixels_per_second=300 / scale,
        pen_up_pixels_per_second=600 / scale,
    )
    rows, _ = timed_pen_paths(tuple(s.path for s in ordered), pacing)
    cursor = 0.0
    for row, spec in zip(rows, ordered, strict=True):
        row["pen_up_start"] = cursor
        row["pen_up_seconds"] *= 1.5
        cursor += row["pen_up_seconds"]
        row["pen_down_start"] = cursor
        row["pen_down_seconds"] = max(row["pen_down_seconds"] * 1.5, spec.minimum_down_seconds)
        cursor += row["pen_down_seconds"]
        row["pen_down_end"] = cursor
    plan = {
        "seconds": cursor,
        "rows": rows,
        "strokes": strokes,
        "status": "TIMING_FEASIBLE" if cursor <= pack.target_seconds else "TIMING_INFEASIBLE",
        "target_seconds": pack.target_seconds,
        "lod": "REVIEWED_AUTHORING_ORDER",
    }
    stats = {
        "coverage": {
            name: {"pixels": int(mask.sum()), "missing": missing[name]}
            for name, mask in regions.items()
        },
        "path_count": len(strokes),
        "pen_lifts": len(strokes) - 1,
        "seconds": cursor,
        "timing": plan["status"],
        "approval": pack.approval,
        "owner": "OWNER_APPROVAL_PENDING",
        "phase_paths": {
            phase: sum(s.path.phase == phase for s in strokes)
            for phase in ("OUTLINE", "DETAIL", "COLOR")
        },
        "phase_seconds": {
            phase: sum(
                r["pen_up_seconds"] + r["pen_down_seconds"] for r in rows if r["phase"] == phase
            )
            for phase in ("OUTLINE", "DETAIL", "COLOR")
        },
    }
    return asset, plan, stats


def route_authoring(
    *, automatic_trusted: bool, candidate_available: bool, approved_pack_available: bool
) -> dict:
    """Routing policy only; no inference or fictitious automatic quality guarantee."""
    if automatic_trusted:
        return {"route": "AUTO", "condition": "EXTERNAL_CONFIDENCE_AND_QUALITY_GATE_REQUIRED"}
    if candidate_available:
        return {"route": "REVIEW", "condition": "NEEDS_AUTHORING_REVIEW"}
    if approved_pack_available:
        return {"route": "FALLBACK", "condition": "USE_EXPLICIT_APPROVED_AUTHORING_NOT_V1"}
    return {"route": "REVIEW", "condition": "NEEDS_AUTHORING_REVIEW_NO_AVAILABLE_PACK"}
