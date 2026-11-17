"""Local candidate art and path feasibility only. No encoder, network or approval API."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import time
import tracemalloc
from dataclasses import asdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from sketch2life.application.services.story_world_model import SourceAssetRegistry
from sketch2life.contracts.schemas.story_strokes_v2 import ObjectStrokeV2
from sketch2life.contracts.schemas.story_world_v2 import WorldModelV2
from sketch2life.infrastructure.media.object_stroke_engine_v2 import (
    LocalObjectAwareStrokeEngine,
)
from sketch2life.infrastructure.media.whiteboard_slice_feasibility import (
    PacingAssumptions,
    path_coverage,
    separate_phase_masks,
    timed_pen_paths,
)


def sha(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def checked_bytes(ref: str, expected: str) -> bytes:
    if "://" in ref:
        raise ValueError("LOCAL_PATH_REQUIRED")
    body = Path(ref).read_bytes()
    if sha(body) != expected:
        raise ValueError("IMMUTABLE_ASSET_HASH_MISMATCH")
    return body


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def stroke(phase: str, index: int, points: list | tuple, width: int = 2) -> ObjectStrokeV2:
    return ObjectStrokeV2(
        stroke_id=f"{phase.lower()}-{index:04d}", phase=phase,
        points=tuple((int(x), int(y)) for x, y in points), brush_width=width,
        color_rgb=(50, 45, 40),
    )


def brush_paths(active: np.ndarray) -> tuple[ObjectStrokeV2, ...]:
    """Small mask-contained alternating pencil hatches, no rectangular reveal."""
    paths = []
    for row, y in enumerate(range(0, active.shape[0], 3)):
        xs = np.flatnonzero(active[y])
        if not xs.size:
            continue
        for run in np.split(xs, np.where(np.diff(xs) > 1)[0] + 1):
            coords = [(int(x), y) for x in run]
            if row % 2:
                coords.reverse()
            if len(coords) == 1:
                coords *= 2
            paths.append(stroke("COLOR", len(paths) + 1, coords, 4))
    coverage = path_coverage((active.shape[1], active.shape[0]), tuple(paths))
    ys, xs = np.nonzero(active & ~coverage)
    for y, x in zip(ys, xs, strict=True):
        paths.append(stroke("COLOR", len(paths) + 1, [(x, y), (x, y)], 3))
    return tuple(paths)


def cubic_path(points: list[tuple[int, int]], seed: int) -> list[tuple[int, int]]:
    """Locally authored irregular cubic outline; no generated source characters."""
    output = []
    for i in range(0, len(points) - 1, 3):
        p0, p1, p2, p3 = np.array(points[i:i + 4], dtype=float)
        for t in np.linspace(0, 1, 25):
            p = (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + (
                3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3
            )
            p += .45 * np.array([math.sin(t * 15 + seed), math.cos(t * 19 + seed)])
            xy = (round(p[0]), round(p[1]))
            if not output or output[-1] != xy:
                output.append(xy)
    return output


def make_butterfly(source: Image.Image) -> tuple[Image.Image, dict, dict]:
    """Authored pencil candidate, NEW artwork, not an AI or source-pixel cutout."""
    rgb = np.asarray(source.convert("RGB"), dtype=np.int16)
    selectors = [
        (rgb[:, :, 0] > 180) & (rgb[:, :, 1] > 80) & (rgb[:, :, 1] < 170)
        & (rgb[:, :, 2] < 145),
        (rgb[:, :, 2] > 120) & (rgb[:, :, 0] < 120) & (rgb[:, :, 1] > 85),
        (rgb[:, :, 1] > 145) & (rgb[:, :, 0] < 160) & (rgb[:, :, 2] < 150),
    ]
    palette = [tuple(int(c) for c in np.median(rgb[s], axis=0)) for s in selectors]
    contours = [
        [(60, 40), (46, 14), (18, 3), (10, 19), (2, 40), (26, 56), (60, 45)],
        [(61, 41), (76, 10), (108, 5), (113, 23), (123, 45), (88, 55), (62, 46)],
        [(58, 43), (31, 40), (11, 63), (25, 76), (47, 87), (56, 59), (61, 45)],
        [(63, 45), (87, 40), (113, 61), (99, 77), (77, 87), (65, 61), (63, 45)],
        [(60, 32), (55, 36), (55, 62), (61, 66), (67, 61), (66, 38), (60, 32)],
    ]
    image = Image.new("RGBA", (128, 92), (255, 255, 255, 0))
    array = np.asarray(image).copy()
    rng = np.random.default_rng(22023)
    outlines = []
    authored_regions = []
    for index, contour in enumerate(contours):
        points = cubic_path(contour, index)
        mask = Image.new("L", image.size, 0)
        ImageDraw.Draw(mask).polygon(points, fill=255)
        active = np.asarray(mask) > 0
        base = np.array(palette[index % 2] if index < 4 else (85, 76, 60))
        # Procedural grain and hatch modulation is declared NEW texture, not source recovery.
        yy, xx = np.indices(active.shape)
        grain = rng.normal(0, 8, (*active.shape, 1))
        hatch = (np.sin((xx + yy * .6) * 2.1) * 4)[:, :, None]
        color = np.clip(base + grain + hatch + 18, 0, 255).astype(np.uint8)
        array[active, :3] = color[active]
        array[active, 3] = 255
        outlines.append(stroke("OUTLINE", index + 1, points, 2))
        authored_regions.append({"region": index, "contour": points,
                                "base_source_palette_rgb": base.tolist()})
    image = Image.fromarray(array)
    draw = ImageDraw.Draw(image)
    for path in outlines:
        for i, (a, b) in enumerate(zip(path.points, path.points[1:], strict=False)):
            draw.line((a, b), fill=(58 + i % 5, 51 + i % 3, 45, 255), width=1 + (i % 7 == 0))
    curves = [
        [(59, 34), (54, 19), (47, 17), (44, 20)],
        [(63, 34), (69, 19), (77, 17), (80, 20)],
        [(58, 42), (43, 32), (31, 25), (18, 21)],
        [(64, 43), (79, 30), (92, 24), (105, 22)],
        [(57, 49), (44, 54), (36, 64), (28, 69)],
        [(65, 49), (77, 54), (88, 65), (96, 70)],
    ]
    details = [stroke("DETAIL", i + 1, cubic_path(p, 7 + i), 1)
               for i, p in enumerate(curves)]
    for path in details:
        draw.line(path.points, fill=(62, 55, 47, 255), width=1)
    active = np.asarray(image)[:, :, 3] > 0
    groups = {"OUTLINE": tuple(outlines), "DETAIL": tuple(details),
              "COLOR": brush_paths(active)}
    return image, groups, {"palette_rgb": palette, "regions": authored_regions,
                           "texture": "SEEDED_LOCAL_PROCEDURAL_PENCIL_GRAIN_NOT_SOURCE_PIXELS",
                           "seed": 22023, "geometry": "LOCAL_MANUAL_CUBIC_CONTROL_POINTS"}


def white_composite(source: Image.Image, mask: np.ndarray | None = None) -> Image.Image:
    result = source.copy().convert("RGBA")
    if mask is not None:
        result.putalpha(Image.fromarray((mask * 255).astype(np.uint8)))
    white = Image.new("RGBA", result.size, "white")
    return Image.alpha_composite(white, result).convert("RGB")


def preview_sheet(images: list[tuple[str, Image.Image]], path: Path) -> None:
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 17)
    sheet = Image.new("RGB", (900, math.ceil(len(images) / 3) * 300), "#edf0f2")
    draw = ImageDraw.Draw(sheet)
    for i, (label, image) in enumerate(images):
        x, y = (i % 3) * 300, (i // 3) * 300
        draw.text((x + 8, y + 8), label, font=font, fill="#1b2732")
        copy = image.convert("RGB")
        copy.thumbnail((280, 245))
        sheet.paste(copy, (x + (300 - copy.width) // 2, y + 42))
    sheet.save(path)


def prepare(
    manifest_path: Path, world_path: Path, actions_path: Path, output: Path,
    *, confirm_local_candidate_only: bool,
) -> dict:
    if not confirm_local_candidate_only:
        raise ValueError("LOCAL_CANDIDATE_PERMISSION_REQUIRED")
    repo = Path(__file__).resolve().parents[1]
    if output.resolve().is_relative_to(repo) or output.exists():
        raise ValueError("NEW_PRIVATE_OUTPUT_DIRECTORY_REQUIRED")
    output.mkdir(parents=True)
    started = time.perf_counter()
    tracemalloc.start()
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    source_body = checked_bytes(manifest["source_ref"], manifest["source_image_sha256"])
    source = Image.open(io.BytesIO(source_body)).convert("RGBA")
    for obj in manifest["objects"]:
        checked_bytes(obj["mask_ref"], obj["mask_sha256"])
        checked_bytes(obj["cutout_ref"], obj["cutout_sha256"])
    world = WorldModelV2.model_validate_json(world_path.read_bytes())
    if world.source_image_sha256 != sha(source_body):
        raise ValueError("WORLD_SOURCE_MISMATCH")
    assets = {o.object_id: checked_bytes(o.asset_ref, o.asset_sha256)
              for o in world.source_objects}
    masks = {o.object_id: checked_bytes(o.source_mask_ref, o.source_mask_sha256)
             for o in world.source_objects}
    registry = SourceAssetRegistry(world, assets, masks, source_body)
    draft = json.loads(actions_path.read_text(encoding="utf-8"))
    if draft["source_sha256"] != sha(source_body) or len(draft["actions"]) != 18:
        raise ValueError("REV22_ACTION_INPUT_MISMATCH")
    butterfly, butterfly_groups, art = make_butterfly(source)
    butterfly.save(output / "butterfly-candidate.png")
    enlarged = white_composite(butterfly).resize((512, 368), Image.Resampling.NEAREST)
    enlarged.save(output / "butterfly-candidate-preview.png")
    placement = {"x": 455, "y": 136, "scale": .60, "approval": "NEEDS_PLACEMENT_REVIEW"}
    positioned = source.copy()
    positioned.alpha_composite(butterfly.resize((77, 55), Image.Resampling.LANCZOS),
                              (placement["x"], placement["y"]))
    positioned.convert("RGB").save(output / "butterfly-source-placement-preview.png")
    write_json(output / "butterfly-candidate-manifest.json", {
        "object_id": "local-new-butterfly-01", "approval_status": "NEEDS_ARTWORK_APPROVAL",
        "provenance": "NEW_LOCAL_AUTHORED_ART_NOT_SOURCE_OBJECT", "paid_inference": False,
        "model_used": None, "server_gate_a_b": "NOT_VERIFIED",
        "source_style_sha256": sha(source_body), "source_manifest_sha256": sha(manifest_bytes),
        "asset_sha256": sha((output / "butterfly-candidate.png").read_bytes()),
        "asset_ref": str(output / "butterfly-candidate.png"), "placement": placement,
        "approved_local_content_basis": "Revision22 shortened script owner-approved in chat",
        "art_recipe": art,
    })
    order = list(dict.fromkeys(a["object_id"] for a in draft["actions"]))
    pacing = PacingAssumptions()
    results = []
    phase_images = []
    path_images = []
    for object_id in order:
        if time.perf_counter() - started > 120:
            raise ValueError("PREPARATION_TIME_BUDGET_EXCEEDED")
        object_start = time.perf_counter()
        if object_id == "local-new-butterfly-01":
            image, groups = butterfly, butterfly_groups
            origin, scale = (455, 136), .60
            extract_method = "LOCAL_AUTHORED_PENCIL_PATHS_NEW_CANDIDATE"
            extraction_diagnostics = None
        else:
            # Current existing source extractor, never rewritten for the timing result.
            data = LocalObjectAwareStrokeEngine(strategy="pencil").extract_object(registry, object_id)
            image = Image.open(io.BytesIO(assets[object_id])).convert("RGBA")
            groups = {"OUTLINE": data.outline_paths, "DETAIL": data.detail_paths,
                      "COLOR": data.color_paths}
            spec = next(o for o in world.source_objects if o.object_id == object_id)
            entry = next(o for o in manifest["objects"] if o["object_id"] == object_id)
            origin, scale = tuple(entry["bbox_pixels"][:2]), 1.
            extract_method = data.extraction_method
            extraction_diagnostics = data.processing_diagnostics.model_dump(mode="json")
            checked_bytes(spec.asset_ref, spec.asset_sha256)
        directory = output / object_id
        directory.mkdir()
        phase_masks, counts = separate_phase_masks(image, groups)
        prior = None
        cursor = 0.
        presentation_cursor = 0.
        all_paths = []
        phase_report = {}
        source_rgb = np.asarray(image)[:, :, :3]
        for phase in ("OUTLINE", "DETAIL", "COLOR"):
            paths = groups[phase]
            timing, metrics = timed_pen_paths(paths, pacing, previous_endpoint=prior)
            for row in timing:
                row["pen_up_start"] += cursor
                row["pen_down_start"] += cursor
                row["pen_down_end"] += cursor
            # Explicit scale-adjusted comparison, retaining visibility/lift minima.
            presentation_seconds = sum(
                max(pacing.minimum_down_frames / pacing.fps,
                    row["down_length_pixels"] * scale / (
                        pacing.color_pixels_per_second if phase == "COLOR" else
                        pacing.ink_pixels_per_second
                    )) + (max(pacing.minimum_up_frames / pacing.fps,
                              row["up_length_pixels"] * scale /
                              pacing.pen_up_pixels_per_second)
                          if row["pen_up_from"] is not None else 0.)
                for row in timing
            )
            presentation_cursor += presentation_seconds
            write_json(directory / f"{phase.lower()}-pen-transitions.json", timing)
            cursor += metrics["estimated_seconds"]
            if paths:
                prior = paths[-1].points[-1]
            mask_path = directory / f"{phase.lower()}-phase-mask.png"
            Image.fromarray((phase_masks[phase] * 255).astype(np.uint8)).save(mask_path)
            white_composite(image, phase_masks[phase]).save(directory / f"{phase.lower()}-coverage.png")
            # Diagnostic full path drawing, not a rendered time sequence or substitute art.
            path_preview = white_composite(image)
            draw = ImageDraw.Draw(path_preview)
            for i, path in enumerate(paths):
                draw.line(path.points, fill=((i * 73) % 180, 70, (i * 37) % 180), width=1)
            path_preview.save(directory / f"{phase.lower()}-path-preview.png")
            path_images.append((f"{object_id.split('-')[-1]} {phase}", path_preview))
            points = sum(len(p.points) for p in paths)
            draft_action = next(a for a in draft["actions"]
                                if a["object_id"] == object_id and a["phase"] == phase)
            budget = draft_action["end"] - draft_action["start"]
            draft_action.update(path_ids=[p.stroke_id for p in paths],
                                path_status="PREPARED_REVIEW_REQUIRED",
                                authorised_phase_mask_ref=str(mask_path),
                                phase_mask_sha256=sha(mask_path.read_bytes()),
                                native_asset_sha256=sha(assets[object_id]) if object_id in assets else (
                                    sha((output / "butterfly-candidate.png").read_bytes())),
                                timing_basis="ASSUMPTION_BASED_PATH_TRAVEL_NOT_MEASURED_AUDIO",
                                estimated_seconds=metrics["estimated_seconds"],
                                nominal_window_feasible=metrics["estimated_seconds"] <= budget,
                                asset_status="NEEDS_ARTWORK_APPROVAL" if object_id not in assets else (
                                    "SOURCE_HASH_BOUND"))
            phase_report[phase] = {**metrics, "paths": len(paths), "points": points,
                                   "estimated_seconds_at_presentation_scale": presentation_seconds,
                                   "phase_pixels": int(phase_masks[phase].sum()),
                                   "draft_budget_seconds": budget,
                                   "compression_needed": metrics["estimated_seconds"] / budget,
                                   "zero_length_paths": sum(p.points[0] == p.points[-1]
                                                            and len(set(p.points)) == 1 for p in paths)}
            all_paths.extend(p.model_dump(mode="json") for p in paths)
        write_json(directory / "paths.json", {"object_id": object_id, "origin": origin,
                                               "scale": scale, "paths": all_paths})
        phase_images.extend((f"{object_id.split('-')[-1]} {phase}", white_composite(image, phase_masks[phase]))
                            for phase in ("OUTLINE", "DETAIL", "COLOR"))
        active = np.asarray(image)[:, :, 3] > 0
        completed = phase_masks["COLOR"]
        preview_rgb = np.asarray(Image.open(directory / "color-coverage.png"))
        immutable_rgb_equal = bool(np.array_equal(source_rgb[completed], preview_rgb[completed]))
        results.append({"object_id": object_id, "native_size": image.size,
                        "source_or_new": "SOURCE" if object_id in assets else "NEW_CANDIDATE",
                        "origin": origin, "presentation_scale": scale,
                        "extraction_method": extract_method,
                        "extraction_diagnostics": extraction_diagnostics,
                        "phase_counts": counts, "phases": phase_report,
                        "estimated_seconds_native_pacing": cursor,
                        "estimated_seconds_at_presentation_scale": presentation_cursor,
                        "source_pixel_coverage_fraction": float((completed & active).sum() / active.sum()),
                        "source_rgb_not_recolored": immutable_rgb_equal,
                        "preparation_seconds": time.perf_counter() - object_start,
                        "structural_phase_status": "NEEDS_SOURCE_INK_AND_PATH_REVIEW",
                        "reason": "neutral-ink heuristic excludes colored contours; isolated raster fragments remain"})
    preview_sheet(phase_images, output / "phase-coverage-contact-sheet.png")
    preview_sheet(path_images, output / "stroke-brush-path-contact-sheet.png")
    butterfly_preview = Image.new("RGB", (128, 92), "white")
    bd = ImageDraw.Draw(butterfly_preview)
    for phase, color in (("OUTLINE", "#212121"), ("DETAIL", "#215fc0"), ("COLOR", "#d97a28")):
        for path in butterfly_groups[phase]:
            bd.line(path.points, fill=color, width=1)
    butterfly_preview.resize((512, 368), Image.Resampling.NEAREST).save(
        output / "butterfly-draw-path-preview.png"
    )
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    total = sum(r["estimated_seconds_native_pacing"] for r in results)
    draft.update(status="PREPARED_STEP_A_NOT_RENDER_AUTHORIZED", executable=False,
                 budgets_unverified=True, path_travel_calculated=True,
                 feasibility="TARGET_15S_NOT_FEASIBLE",
                 actual_audio_measured=False, asset_approval="BUTTERFLY_PENDING")
    write_json(output / "draw-action-timeline.prepared.json", draft)
    result = {"status": "STEP_A_PREPARED_REVIEW_REQUIRED", "target_seconds": 15,
              "feasibility": "NOT_FEASIBLE_UNDER_DECLARED_PACING" if total > 15 else (
                  "NEEDS_VISUAL_AND_ASSET_REVIEW"),
              "estimate_basis": "PATH_TRAVEL_PLUS_MIN_VISIBLE_FRAMES_NOT_ACTUAL_DRAWING_OR_AUDIO",
              "pacing_assumptions": asdict(pacing), "pacing_is_owner_approved": False,
              "objects": results, "total_estimated_seconds": total,
              "total_presentation_scale_estimated_seconds": sum(
                  o["estimated_seconds_at_presentation_scale"] for o in results
              ),
              "presentation_scale_note": "butterfly has scale0.60; native timing conservative, frame/lift minima unchanged",
              "cross_object_pen_travel": "not included; total is lower-bound sum, add camera/hold/travel later",
              "preparation_wall_seconds": time.perf_counter() - started,
              "python_tracemalloc_peak_bytes": peak, "process_rss_bytes": None,
              "resource_guards": {"max_canvas_pixels": 1920 * 1080, "max_object_paths": 4096,
                                  "max_phase_points": 200000, "time_budget_seconds": 120},
              "outline_semantics": "Only neutral-dark source ink is exposed by outline/detail masks; color remains in COLOR",
              "visual_qa": "NOT_PASSED_NOT_VIDEO_TESTED", "butterfly_art": "NEEDS_OWNER_REVIEW",
              "full_slice_rendered": False, "audio_used": False, "network_used": False}
    write_json(output / "object-timing-feasibility.json", result)
    # Verify original source and all master masks after read-only preparation.
    checked_bytes(manifest["source_ref"], manifest["source_image_sha256"])
    for obj in manifest["objects"]:
        checked_bytes(obj["mask_ref"], obj["mask_sha256"])
    files = [{"ref": str(p), "sha256": sha(p.read_bytes()), "bytes": p.stat().st_size}
             for p in sorted(output.rglob("*")) if p.is_file()]
    write_json(output / "artifact-sha256.json", {"self_excluded": True, "files": files})
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--world", type=Path, required=True)
    parser.add_argument("--actions", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--confirm-local-candidate-only", action="store_true")
    args = parser.parse_args()
    result = prepare(args.source_manifest, args.world, args.actions, args.output_dir,
                     confirm_local_candidate_only=args.confirm_local_candidate_only)
    print(json.dumps({"status": result["status"], "seconds": result["total_estimated_seconds"],
                      "output": str(args.output_dir)}, indent=2))


if __name__ == "__main__":
    main()
