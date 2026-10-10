"""One local path-native butterfly candidate and static progress proof; no video/API."""

from __future__ import annotations

import argparse
import io
import json
import math
import time
from dataclasses import asdict, dataclass
from itertools import pairwise
from pathlib import Path
from typing import Literal

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from sketch2life.contracts.schemas.story_strokes_v2 import ObjectStrokeV2
from sketch2life.infrastructure.media.whiteboard_renderer_v2 import _partial_points
from sketch2life.infrastructure.media.whiteboard_slice_feasibility import (
    PacingAssumptions,
    timed_pen_paths,
)

from tools.prepare_whiteboard_slice_step_a import checked_bytes, sha, write_json

SIZE = (256, 184)
SUPERSAMPLE = 4


@dataclass(frozen=True)
class Candidate:
    fill: Image.Image
    outline: Image.Image
    detail: Image.Image
    asset: Image.Image
    paths: tuple[ObjectStrokeV2, ...]
    parts: tuple[str, ...]
    region_masks: dict[str, Image.Image]
    recipe: dict


def curve(controls: list[tuple[int, int]], *, seed: int, closed: bool = False) -> tuple:
    points: list[tuple[int, int]] = []
    for i in range(0, len(controls) - 1, 3):
        p0, p1, p2, p3 = np.asarray(controls[i:i + 4], dtype=float)
        for t in np.linspace(0, 1, 65):
            p = (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + (
                3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3
            )
            # Slow bounded irregularity, not independently jittered pixels each frame.
            p += .65 * math.sin(math.pi * t) * np.array([
                math.sin(t * 11 + seed), math.cos(t * 9 + seed),
            ])
            xy = (round(p[0]), round(p[1]))
            if not points or points[-1] != xy:
                points.append(xy)
    if closed:
        points[-1] = points[0]
    return tuple(points)


def make_path(
    phase: Literal["OUTLINE", "DETAIL", "COLOR"], name: str, points: tuple, width: int,
) -> ObjectStrokeV2:
    return ObjectStrokeV2(stroke_id=f"{phase.lower()}-{name}", phase=phase, points=points,
                          brush_width=width, color_rgb=(57, 51, 45))


def mask_for_path(path: ObjectStrokeV2, fraction: float = 1.) -> Image.Image:
    """Same arc-length geometry for actual brush coverage and pen endpoint."""
    result = Image.new("L", (SIZE[0] * SUPERSAMPLE, SIZE[1] * SUPERSAMPLE), 0)
    if fraction <= 0:
        return result.resize(SIZE)
    draw = ImageDraw.Draw(result)
    points = _partial_points(path, fraction)
    for i, (a, b) in enumerate(pairwise(points)):
        width = float(path.brush_width)
        if path.phase != "COLOR":
            width *= .92 + .12 * math.sin(i * .21 + len(path.stroke_id))
        draw.line((a[0] * SUPERSAMPLE, a[1] * SUPERSAMPLE,
                   b[0] * SUPERSAMPLE, b[1] * SUPERSAMPLE),
                  fill=255, width=max(1, round(width * SUPERSAMPLE)))
    radius = path.brush_width * SUPERSAMPLE / 2
    for x, y in (points[0], points[-1]):
        xx, yy = x * SUPERSAMPLE, y * SUPERSAMPLE
        draw.ellipse((xx - radius, yy - radius, xx + radius, yy + radius), fill=255)
    return result.resize(SIZE, Image.Resampling.LANCZOS)


def contour_spiral(contour: tuple, mask: Image.Image, direction: int) -> tuple:
    """Shape-following spiral, outer edge inward; no horizontal region scan/fade."""
    vertices = np.asarray(contour[:-1], dtype=float)
    active = np.asarray(mask) > 0
    ys, xs = np.nonzero(active)
    center = np.array([xs.mean(), ys.mean()])
    radius = max(np.linalg.norm(vertices - center, axis=1))
    turns = max(3, math.ceil(radius / 4.5))
    count = turns * len(vertices)
    # Trace the permitted pigment boundary first: AA fringe must be brushed too.
    output = list(contour if direction == 1 else tuple(reversed(contour)))
    for i in range(count + 1):
        phase = (i % len(vertices)) * direction % len(vertices)
        r = .98 * (1 - i / count)
        p = center + r * (vertices[phase] - center)
        xy = (round(p[0]), round(p[1]))
        if not output or output[-1] != xy:
            output.append(xy)
    return tuple(output)


def build_candidate(source: Image.Image) -> Candidate:
    rgb = np.asarray(source.convert("RGB"), dtype=np.int16)
    selectors = [
        (rgb[:, :, 0] > 180) & (rgb[:, :, 1] > 80) & (rgb[:, :, 1] < 170)
        & (rgb[:, :, 2] < 145),
        (rgb[:, :, 2] > 120) & (rgb[:, :, 0] < 120) & (rgb[:, :, 1] > 85),
    ]
    if not all(s.any() for s in selectors):
        raise ValueError("SOURCE_PALETTE_REVIEW_REQUIRED")
    palette = [np.median(rgb[s], axis=0) for s in selectors]
    controls = {
        "upper-left": [(124, 82), (104, 25), (37, 5), (20, 39), (7, 75), (45, 103),
                       (119, 91), (120, 88), (121, 84), (124, 82)],
        "upper-right": [(127, 83), (149, 17), (212, 18), (229, 55), (244, 89),
                        (197, 113), (130, 95), (128, 92), (126, 87), (127, 83)],
        "lower-left": [(120, 92), (79, 83), (28, 122), (48, 151), (75, 181),
                       (114, 144), (123, 101), (124, 97), (122, 95), (120, 92)],
        "lower-right": [(131, 95), (164, 85), (219, 132), (195, 158), (164, 181),
                        (140, 138), (130, 102), (129, 98), (130, 97), (131, 95)],
        "body": [(124, 68), (114, 78), (115, 123), (125, 137), (137, 124),
                 (137, 81), (124, 68)],
    }
    paths, parts, masks = [], [], {}
    vertices = {}
    array = np.zeros((SIZE[1], SIZE[0], 4), dtype=np.uint8)
    rng = np.random.default_rng(24024)
    paper = rng.normal(0, 1, (SIZE[1], SIZE[0]))
    broad = np.asarray(Image.fromarray(np.clip(128 + paper * 30, 0, 255).astype(np.uint8))
                       .filter(ImageFilter.GaussianBlur(.8)), dtype=np.float64) - 128
    yy, xx = np.indices((SIZE[1], SIZE[0]))
    for i, (name, points) in enumerate(controls.items()):
        contour = curve(points, seed=i + 3, closed=True)
        vertices[name] = contour
        large = Image.new("L", (SIZE[0] * SUPERSAMPLE, SIZE[1] * SUPERSAMPLE), 0)
        ImageDraw.Draw(large).polygon([(x * SUPERSAMPLE, y * SUPERSAMPLE)
                                       for x, y in contour], fill=255)
        mask = large.resize(SIZE, Image.Resampling.LANCZOS)
        masks[name] = mask
        active = np.asarray(mask) > 0
        base = palette[0 if "left" in name else 1] if name != "body" else np.array([98, 84, 64])
        # New textured pigment recipe. Original/previous candidate is not changed.
        pigment = np.clip(base + 16 + paper[:, :, None] * 5 + broad[:, :, None] * .35
                          + (np.sin(xx * .45 + yy * .21) * 2)[:, :, None], 0, 255)
        array[active, :3] = pigment.astype(np.uint8)[active]
        array[active, 3] = np.asarray(mask)[active]
        paths.append(make_path("OUTLINE", name, contour, 3))
        parts.append(name)
    antennae = {
        "antenna-left": [(121, 70), (117, 47), (108, 40), (99, 47)],
        "antenna-right": [(129, 70), (140, 44), (155, 46), (157, 53)],
    }
    for i, (name, points) in enumerate(antennae.items()):
        paths.append(make_path("OUTLINE", name, curve(points, seed=19 + i), 2))
        parts.append(name)
    detail_controls = {
        "left-vein-main": [(119, 86), (89, 64), (62, 45), (32, 39)],
        "left-vein-branch": [(83, 61), (64, 66), (47, 71), (29, 62)],
        "right-vein-main": [(131, 88), (163, 60), (188, 43), (216, 56)],
        "right-vein-branch": [(175, 57), (188, 70), (206, 83), (221, 76)],
        "lower-left-main": [(120, 100), (98, 118), (77, 141), (55, 145)],
        "lower-left-branch": [(91, 126), (81, 116), (62, 119), (49, 130)],
        "lower-right-main": [(132, 102), (157, 121), (170, 148), (190, 153)],
        "lower-right-branch": [(160, 127), (171, 121), (188, 126), (204, 141)],
        "body-accent": [(124, 80), (127, 95), (125, 113), (125, 127)],
    }
    for i, (name, points) in enumerate(detail_controls.items()):
        paths.append(make_path("DETAIL", name, curve(points, seed=28 + i), 2))
        parts.append(name)
    for i, name in enumerate(controls):
        paths.append(make_path("COLOR", name, contour_spiral(vertices[name], masks[name],
                                                             1 if i % 2 == 0 else -1), 12))
        parts.append(name)
    fill = Image.fromarray(array)
    ink_layers = []
    for phase in ("OUTLINE", "DETAIL"):
        alpha = np.zeros((SIZE[1], SIZE[0]), dtype=np.uint8)
        for path in paths:
            if path.phase == phase:
                alpha = np.maximum(alpha, np.asarray(mask_for_path(path)))
        ink = np.zeros_like(array)
        shade = np.clip(57 + broad * .20 + paper * 1.5, 40, 72).astype(np.uint8)
        ink[:, :, :3] = shade[:, :, None]
        ink[:, :, 3] = alpha
        ink_layers.append(Image.fromarray(ink))
    asset = Image.alpha_composite(Image.alpha_composite(fill, ink_layers[0]), ink_layers[1])
    recipe = {"palette_rgb": [p.tolist() for p in palette], "supersample": SUPERSAMPLE,
              "controls": controls, "antenna_controls": antennae, "detail_controls": detail_controls,
              "seed": 24024, "new_texture": "LOCAL_PROCEDURAL_PAPER_AND_PENCIL_NOT_SOURCE_PIXELS",
              "color_motion": "OUTER_TO_INNER_COMPONENT_CONTOUR_SPIRALS_ALTERNATING_DIRECTION",
              "alpha_semantics": "fixed native antialias alpha, spatial brush coverage only"}
    return Candidate(fill, ink_layers[0], ink_layers[1], asset, tuple(paths), tuple(parts),
                     masks, recipe)


def schedule_for(candidate: Candidate, scale: float) -> tuple[list[dict], dict]:
    if not .05 <= scale <= 1:
        raise ValueError("INVALID_PRESENTATION_SCALE")
    pacing = PacingAssumptions()
    # Native raster doubled versus old art: express speeds in source-canvas units.
    profile = PacingAssumptions(
        ink_pixels_per_second=pacing.ink_pixels_per_second / scale,
        color_pixels_per_second=pacing.color_pixels_per_second / scale,
        pen_up_pixels_per_second=pacing.pen_up_pixels_per_second / scale,
    )
    rows, metrics = timed_pen_paths(candidate.paths, profile)
    return rows, {**metrics, "source_canvas_pacing": asdict(pacing), "scale": scale,
                  "basis": "PATH_TRAVEL_PLUS_VISIBLE_FRAMES_NOT_MEASURED_NATURAL_SPEED_OR_AUDIO"}


def progress(
    candidate: Candidate, rows: list[dict], elapsed: float,
) -> tuple[Image.Image, dict, dict[str, np.ndarray]]:
    masks = {phase: np.zeros((SIZE[1], SIZE[0]), dtype=np.uint8)
             for phase in ("OUTLINE", "DETAIL", "COLOR")}
    trace: dict = {"state": "IDLE", "tip": None, "stroke_id": None, "phase": None}
    for path, part, row in zip(candidate.paths, candidate.parts, rows, strict=True):
        if elapsed <= row["pen_up_start"]:
            break
        if elapsed < row["pen_down_start"]:
            prior = row["pen_up_from"]
            if prior is not None:
                fraction = (elapsed - row["pen_up_start"]) / row["pen_up_seconds"]
                trace = {"state": "UP", "tip": [a + (b - a) * fraction for a, b in
                         zip(prior, row["pen_up_to"], strict=True)],
                         "stroke_id": path.stroke_id, "phase": path.phase}
            break
        fraction = min(1., (elapsed - row["pen_down_start"]) / row["pen_down_seconds"])
        coverage = np.asarray(mask_for_path(path, fraction))
        if path.phase == "COLOR":
            # Spatial binary footprint × immutable component pigment alpha, not an opacity fade.
            allowed = np.asarray(candidate.region_masks[part]) > 0
            coverage = np.where(allowed & (coverage > 0), 255, 0).astype(np.uint8)
        masks[path.phase] = np.maximum(masks[path.phase], coverage)
        if fraction < 1:
            trace = {"state": "DOWN", "tip": list(_partial_points(path, fraction)[-1]),
                     "stroke_id": path.stroke_id, "phase": path.phase,
                     "fraction": fraction}
            break
        trace = {"state": "REST", "tip": list(path.points[-1]),
                 "stroke_id": path.stroke_id, "phase": path.phase}
    layers = []
    for phase, layer in (("COLOR", candidate.fill), ("OUTLINE", candidate.outline),
                         ("DETAIL", candidate.detail)):
        rgba = np.asarray(layer).copy()
        # Layer alpha already contains AA. Completed mask admits original alpha exactly.
        rgba[:, :, 3] = np.where(masks[phase] > 0, rgba[:, :, 3], 0)
        layers.append(Image.fromarray(rgba))
    visible = Image.alpha_composite(Image.alpha_composite(layers[0], layers[1]), layers[2])
    return visible, trace, masks


def on_white(image: Image.Image) -> Image.Image:
    return Image.alpha_composite(Image.new("RGBA", image.size, "white"), image).convert("RGB")


def contact(images: list[tuple[str, Image.Image]], path: Path, columns: int = 3) -> None:
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 19)
    out = Image.new("RGB", (columns * 400, math.ceil(len(images) / columns) * 350), "#edf0f2")
    draw = ImageDraw.Draw(out)
    for i, (label, image) in enumerate(images):
        x, y = i % columns * 400, i // columns * 350
        draw.text((x + 12, y + 10), label, font=font, fill="#162837")
        copy = image.convert("RGB")
        copy.thumbnail((380, 285))
        out.paste(copy, (x + (400 - copy.width) // 2, y + 52))
    out.save(path)


def prepare(manifest_ref: Path, previous_ref: Path, output: Path, *, confirmed: bool) -> dict:
    if not confirmed:
        raise ValueError("LOCAL_CANDIDATE_APPROVAL_REQUIRED")
    if output.exists() or output.resolve().is_relative_to(Path(__file__).resolve().parents[1]):
        raise ValueError("NEW_PRIVATE_OUTPUT_REQUIRED")
    output.mkdir(parents=True)
    start = time.perf_counter()
    manifest_body = manifest_ref.read_bytes()
    manifest = json.loads(manifest_body)
    source_body = checked_bytes(manifest["source_ref"], manifest["source_image_sha256"])
    for item in manifest["objects"]:
        checked_bytes(item["mask_ref"], item["mask_sha256"])
    source = Image.open(io.BytesIO(source_body)).convert("RGBA")
    candidate = build_candidate(source)
    for name, image in (("butterfly-candidate-v2.png", candidate.asset),
                        ("fill-texture.png", candidate.fill), ("outline-ink.png", candidate.outline),
                        ("detail-ink.png", candidate.detail)):
        image.save(output / name)
    on_white(candidate.asset).resize((512, 368), Image.Resampling.LANCZOS).save(
        output / "butterfly-candidate-preview.png"
    )
    previous = Image.open(previous_ref).convert("RGBA")
    contact([("Old candidate / nearest magnification", on_white(previous).resize((384, 276))),
             ("New candidate / smoothed edge", on_white(candidate.asset))],
            output / "original-candidate-vs-refined.png", 2)
    views = []
    placement = []
    for name, scale in (("standard", .30), ("smaller", .22)):
        width, height = round(SIZE[0] * scale), round(SIZE[1] * scale)
        # Same center as previously proposed77x55 placement near the garden.
        origin = (round(493.5 - width / 2), round(163.5 - height / 2))
        canvas = source.copy()
        canvas.alpha_composite(candidate.asset.resize((width, height), Image.Resampling.LANCZOS),
                               origin)
        canvas.convert("RGB").save(output / f"placement-{name}.png")
        views.append((f"{name}: {width}x{height} source px", canvas))
        rows, stats = schedule_for(candidate, scale)
        write_json(output / f"pen-timeline-{name}.json", rows)
        placement.append({"name": name, "scale": scale, "size": [width, height],
                          "origin": origin, "timing": stats})
    contact(views, output / "placement-size-comparison.png", 2)
    rows, timing = schedule_for(candidate, .30)
    total = timing["estimated_seconds"]
    trace_entries = []
    previews = []
    clean_previews = []
    for percent in (0, 25, 50, 75, 100):
        frame, trace, _masks = progress(candidate, rows, total * percent / 100)
        on_white(frame).save(output / f"progress-{percent:03d}-clean.png")
        debug = on_white(frame)
        draw = ImageDraw.Draw(debug)
        if trace["tip"] is not None:
            x, y = trace["tip"]
            color = "#c34825" if trace["state"] == "DOWN" else "#397ab2"
            active_path = next(p for p in candidate.paths if p.stroke_id == trace["stroke_id"])
            if trace["state"] == "DOWN":
                travelled = _partial_points(active_path, trace["fraction"])
                draw.line(travelled, fill=color, width=1)
            elif trace["state"] == "UP":
                row = next(r for r in rows if r["stroke_id"] == trace["stroke_id"])
                draw.line((*row["pen_up_from"], x, y), fill=color, width=1)
            draw.ellipse((x - 3, y - 3, x + 3, y + 3), outline=color, width=1)
            draw.line((x, y, x + 7, y - 9), fill=color, width=2)
        phase = trace["phase"] or "START"
        label = f"{percent}% / {total * percent / 100:.2f}s / {phase}"
        previews.append((label, debug))
        clean_previews.append((label, on_white(frame)))
        trace_entries.append({"percent": percent, "elapsed": total * percent / 100, **trace})
    contact(previews, output / "progress-0-25-50-75-100-pen.png")
    contact(clean_previews, output / "progress-0-25-50-75-100-clean.png")
    full, _trace, phase_masks = progress(candidate, rows, total + 1e-8)
    exact = full.tobytes() == candidate.asset.tobytes()
    fill_active = np.asarray(candidate.fill)[:, :, 3] > 0
    color_coverage = int((fill_active & (phase_masks["COLOR"] > 0)).sum())
    trajectory_images = []
    for phase in ("OUTLINE", "DETAIL", "COLOR"):
        background = Image.new("RGB", SIZE, "white")
        draw = ImageDraw.Draw(background)
        phase_paths = [p for p in candidate.paths if p.phase == phase]
        for i, path in enumerate(phase_paths):
            path_color = ((40 + i * 43) % 170, 65, (80 + i * 67) % 180)
            draw.line(path.points, fill=path_color, width=1)
            draw.ellipse((path.points[0][0] - 2, path.points[0][1] - 2,
                          path.points[0][0] + 2, path.points[0][1] + 2), fill=path_color)
        background.save(output / f"{phase.lower()}-path-preview.png")
        Image.fromarray(phase_masks[phase]).save(output / f"{phase.lower()}-phase-mask.png")
        trajectory_images.append((f"{phase} trajectories", background))
    contact(trajectory_images, output / "draw-path-contact-sheet.png")
    for name, mask in candidate.region_masks.items():
        mask.save(output / f"region-{name}.png")
    path_rows = [{**p.model_dump(mode="json"), "part": part}
                 for p, part in zip(candidate.paths, candidate.parts, strict=True)]
    write_json(output / "candidate-paths.json", path_rows)
    write_json(output / "progress-tip-traces.json", trace_entries)
    result = {"status": "CANDIDATE_READY_FOR_REVIEW" if exact else "NEEDS_BRUSH_COVERAGE_REVIEW",
              "concept_approval": "APPROVED_CONCEPT_ONLY", "final_asset_approval": "PENDING",
              "paths_approval": "PENDING", "visual_qa": "NOT_PASSED_OWNER_REVIEW_REQUIRED",
              "source_sha256": sha(source_body), "source_manifest_sha256": sha(manifest_body),
              "candidate_png_sha256": sha((output / "butterfly-candidate-v2.png").read_bytes()),
              "previous_png_sha256": sha(previous_ref.read_bytes()),
              "object_id": "local-new-butterfly-01", "candidate_revision": 2,
              "provenance": "NEW_LOCAL_AUTHORED_PENCIL_ART_NOT_SOURCE_OBJECT_OR_AI",
              "model_used": None, "recipe": candidate.recipe,
              "native_size": SIZE, "placements": placement,
              "path_counts": {phase: sum(p.phase == phase for p in candidate.paths)
                              for phase in ("OUTLINE", "DETAIL", "COLOR")},
              "pen_lifts": sum(row["pen_up_from"] is not None for row in rows),
              "zero_length_paths": sum(len(set(p.points)) == 1 for p in candidate.paths),
              "timing_standard": timing, "color_active_pixels": int(fill_active.sum()),
              "color_covered_pixels": color_coverage,
              "color_coverage_fraction": color_coverage / fill_active.sum(),
              "completed_rgba_exact": exact,
              "preparation_wall_seconds": time.perf_counter() - start,
              "tip_geometry": "same arc-length function and path fractions as visible brush",
              "progress_percent_semantics": "percentage of estimated path timeline, not color area",
              "mp4_rendered": False, "tts_used": False, "network_used": False,
              "server_gate_a_b": "NOT_VERIFIED"}
    write_json(output / "candidate-manifest-and-diagnostics.json", result)
    checked_bytes(manifest["source_ref"], manifest["source_image_sha256"])
    for item in manifest["objects"]:
        checked_bytes(item["mask_ref"], item["mask_sha256"])
    write_json(output / "artifact-sha256.json", {"self_excluded": True, "files": [
        {"ref": str(p), "sha256": sha(p.read_bytes()), "bytes": p.stat().st_size}
        for p in sorted(output.rglob("*")) if p.is_file()
    ]})
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--previous-candidate", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--confirm-local-candidate-only", action="store_true")
    args = parser.parse_args()
    result = prepare(args.source_manifest, args.previous_candidate, args.output_dir,
                     confirmed=args.confirm_local_candidate_only)
    print(json.dumps({k: result[k] for k in ("status", "path_counts", "pen_lifts",
                                           "color_coverage_fraction", "completed_rgba_exact")},
                     indent=2))


if __name__ == "__main__":
    main()
