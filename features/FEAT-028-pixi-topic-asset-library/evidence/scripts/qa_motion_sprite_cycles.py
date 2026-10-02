"""Reproducible technical audit for the 37 generated four-frame motion sheets."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[4]
FEATURE_ROOT = REPO_ROOT / "features" / "FEAT-028-pixi-topic-asset-library"
MANIFEST_PATH = FEATURE_ROOT / "assets" / "generated" / "motion-cycle-review-manifest.rev1.json"
PROVENANCE_PATH = FEATURE_ROOT / "evidence" / "notes" / "MOTION_SPRITE_GENERATION_PROVENANCE_20261002.json"
REPORT_PATH = FEATURE_ROOT / "evidence" / "metrics" / "MOTION_CYCLE_QA_20261002.json"
PREVIEW_ALLOWLIST = frozenset(
    {"motion.walker-avian.v1", "motion.walker-corgi.v2", "motion.flyer-songbird.v2"}
)
ALPHA_THRESHOLD = 16
MIN_EDGE_CLEARANCE_PERCENT = 1.5
MAX_NORMALIZED_CENTROID_DELTA = 0.20
THUMBNAIL_SIZE = (32, 32)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _frame_iou(left: Image.Image, right: Image.Image) -> float:
    left_mask = left.resize(THUMBNAIL_SIZE, Image.Resampling.BILINEAR).point(
        lambda value: 255 if value > ALPHA_THRESHOLD else 0
    )
    right_mask = right.resize(THUMBNAIL_SIZE, Image.Resampling.BILINEAR).point(
        lambda value: 255 if value > ALPHA_THRESHOLD else 0
    )
    left_pixels = left_mask.tobytes()
    right_pixels = right_mask.tobytes()
    intersection = sum(a > 0 and b > 0 for a, b in zip(left_pixels, right_pixels, strict=True))
    union = sum(a > 0 or b > 0 for a, b in zip(left_pixels, right_pixels, strict=True))
    return round(intersection / max(1, union), 4)


def _audit_cycle(cycle: dict[str, Any], provenance_by_output: dict[str, dict[str, Any]]) -> dict[str, Any]:
    asset_file = cycle["assetFile"]
    source_path = FEATURE_ROOT / "assets" / "generated" / asset_file
    approved_path = FEATURE_ROOT / "assets" / "approved" / asset_file
    applied_path = FEATURE_ROOT / "assets" / "applied" / asset_file
    source_hash = _sha256(source_path)
    output_id = cycle["generationOutputId"]
    provenance = provenance_by_output.get(output_id)
    hash_matches = source_hash == cycle["sha256"].upper()
    approved_hash = _sha256(approved_path) if approved_path.is_file() else None
    applied_hash = _sha256(applied_path) if applied_path.is_file() else None
    with Image.open(source_path) as source_image:
        image = source_image.convert("RGBA")
    width, height = image.size
    columns, rows = (4, 1) if cycle["layout"] == "STRIP_1X4" else (2, 2)
    frames: list[dict[str, Any]] = []
    masks: list[Image.Image] = []
    for index in range(4):
        column, row = index % columns, index // columns
        x0, x1 = round(column * width / columns), round((column + 1) * width / columns)
        y0, y1 = round(row * height / rows), round((row + 1) * height / rows)
        alpha = image.crop((x0, y0, x1, y1)).getchannel("A")
        thresholded = alpha.point(lambda value: 255 if value > ALPHA_THRESHOLD else 0)
        bounds = thresholded.getbbox()
        cell_width, cell_height = x1 - x0, y1 - y0
        if bounds is None:
            frames.append(
                {
                    "index": index + 1,
                    "cell": [x0, y0, cell_width, cell_height],
                    "alphaBounds": None,
                    "edgeClearancePixels": 0,
                    "normalizedAlphaCentroid": None,
                    "nonEmpty": False,
                }
            )
            masks.append(alpha)
            continue
        left, top, right, bottom = bounds
        mass = sum(thresholded.tobytes()) // 255
        pixels = thresholded.tobytes()
        weighted_x = sum((position % cell_width) for position, value in enumerate(pixels) if value)
        weighted_y = sum((position // cell_width) for position, value in enumerate(pixels) if value)
        centroid = [
            round(weighted_x / max(1, mass) / cell_width, 4),
            round(weighted_y / max(1, mass) / cell_height, 4),
        ]
        edge_clearance = min(left, cell_width - right, top, cell_height - bottom)
        frames.append(
            {
                "index": index + 1,
                "cell": [x0, y0, cell_width, cell_height],
                "alphaBounds": [left, top, right, bottom],
                "edgeClearancePixels": edge_clearance,
                "normalizedAlphaCentroid": centroid,
                "nonEmpty": True,
            }
        )
        masks.append(alpha)
    ious = [
        _frame_iou(masks[index], masks[(index + 1) % 4])
        for index in range(4)
    ]
    occupied = [frame for frame in frames if frame["nonEmpty"]]
    min_clearance = min((frame["edgeClearancePixels"] for frame in occupied), default=0)
    min_clearance_percent = round(
        100 * min_clearance / min(min(frame["cell"][2:]) for frame in occupied), 2
    ) if occupied else 0.0
    centroids = [frame["normalizedAlphaCentroid"] for frame in occupied]
    centroid_delta = 0.0
    if len(centroids) > 1:
        centroid_delta = round(
            max(
                max(abs(left[axis] - right[axis]) for axis in (0, 1))
                for left in centroids
                for right in centroids
            ),
            4,
        )
    corner_alpha = [image.getpixel(point)[3] for point in ((0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1))]
    failures = []
    if not hash_matches or approved_hash != source_hash:
        failures.append("SOURCE_APPROVED_HASH_MISMATCH")
    if len(occupied) != 4:
        failures.append("EMPTY_FRAME")
    if min_clearance_percent < MIN_EDGE_CLEARANCE_PERCENT:
        failures.append("EDGE_CLEARANCE_BELOW_THRESHOLD")
    if any(iou >= 0.98 for iou in ious):
        failures.append("DUPLICATE_OR_NEAR_DUPLICATE_ALPHA_POSE")
    if centroid_delta > MAX_NORMALIZED_CENTROID_DELTA:
        failures.append("ALPHA_CENTROID_DRIFT")
    if not provenance or provenance.get("sourceSha256", "").upper() != source_hash:
        failures.append("GENERATION_PROVENANCE_MISMATCH")
    return {
        "cycleId": cycle["cycleId"],
        "behaviorClassId": cycle["behaviorClassId"],
        "variantId": cycle["variantId"],
        "assetFile": asset_file,
        "generationOutputId": output_id,
        "sourceSha256": source_hash,
        "manifestSha256Matches": hash_matches,
        "approvedSha256": approved_hash,
        "approvedCopyMatchesSource": approved_hash == source_hash,
        "appliedSha256": applied_hash,
        "appliedCopyMatchesSource": applied_hash == source_hash,
        "provenanceOutputIdMatches": bool(provenance),
        "canvas": [width, height],
        "layout": cycle["layout"],
        "frameCount": len(frames),
        "alphaThreshold": ALPHA_THRESHOLD,
        "transparentCanvasCorners": corner_alpha,
        "frames": frames,
        "minimumEdgeClearancePixels": min_clearance,
        "minimumEdgeClearancePercent": min_clearance_percent,
        "alphaShapeIoUFrame01To02To03To04To01": ious,
        "maximumNormalizedAlphaCentroidDelta": centroid_delta,
        "previewAllowlisted": cycle["cycleId"] in PREVIEW_ALLOWLIST,
        "technicalChecks": "PASS" if not failures else "BLOCKED",
        "failureCodes": failures,
    }


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    provenance = json.loads(PROVENANCE_PATH.read_text(encoding="utf-8"))
    records = provenance["records"]
    provenance_by_output = {record["generationOutputId"]: record for record in records}
    results = [_audit_cycle(cycle, provenance_by_output) for cycle in manifest["cycles"]]
    report = {
        "schemaName": "PixiMotionCycleTechnicalQaReport",
        "schemaVersion": "1.0",
        "generatedAt": datetime.now(UTC).isoformat(),
        "manifest": "assets/generated/motion-cycle-review-manifest.rev1.json",
        "provenance": "evidence/notes/MOTION_SPRITE_GENERATION_PROVENANCE_20261002.json",
        "cycleCount": len(results),
        "provenanceRecordCount": len(records),
        "qaProfile": {
            "alphaThreshold": ALPHA_THRESHOLD,
            "minimumEdgeClearancePercent": MIN_EDGE_CLEARANCE_PERCENT,
            "maximumNormalizedAlphaCentroidDelta": MAX_NORMALIZED_CENTROID_DELTA,
            "minimumNonEmptyFrames": 4,
            "alphaShapeIoUThumbnail": list(THUMBNAIL_SIZE),
            "note": "Numerical QA is a local-preview filter, not a claim of rights clearance or production readiness.",
        },
        "previewAllowlist": sorted(PREVIEW_ALLOWLIST),
        "cycles": results,
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    passed = [cycle["cycleId"] for cycle in results if cycle["previewAllowlisted"] and cycle["technicalChecks"] == "PASS"]
    blocked = [cycle["cycleId"] for cycle in results if cycle["previewAllowlisted"] and cycle["technicalChecks"] != "PASS"]
    print(f"cycles={len(results)} provenance={len(records)} preview_passed={passed} preview_blocked={blocked}")
    print(f"report={REPORT_PATH.relative_to(REPO_ROOT).as_posix()}")


if __name__ == "__main__":
    main()
