"""One offline house proof from immutable source pixels and existing source paths."""

from __future__ import annotations

import argparse
import io
import json
import math
import time
from pathlib import Path

import imageio_ffmpeg  # type: ignore[import-untyped]  # Upstream has no typing stubs.
import numpy as np
from PIL import Image, ImageDraw
from sketch2life.contracts.schemas.story_strokes_v2 import ObjectStrokeV2
from sketch2life.infrastructure.media.whiteboard_renderer_v2 import _partial_points

from tools.prepare_whiteboard_slice_step_a import checked_bytes, sha, write_json
from tools.refine_butterfly_candidate import contact, on_white
from tools.render_butterfly_video_proof import decode_samples

FPS = 24
FRAME_SIZE = (960, 540)
PHASES = ("OUTLINE", "DETAIL", "COLOR")


def coverage(size: tuple[int, int], path: ObjectStrokeV2, fraction: float) -> np.ndarray:
    mask = Image.new("L", size, 0)
    if fraction <= 0:
        return np.asarray(mask) > 0
    points = _partial_points(path, fraction)
    draw = ImageDraw.Draw(mask)
    draw.line(points, fill=255, width=path.brush_width, joint="curve")
    radius = max(1, path.brush_width // 2)
    for x, y in (points[0], points[-1]):
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=255)
    return np.asarray(mask) > 0


class SourceProgress:
    """Monotonic spatial footprints; completed source pixels are never repainted."""

    def __init__(self, source: Image.Image, paths: tuple[ObjectStrokeV2, ...],
                 rows: list[dict], allowed: dict[str, np.ndarray]):
        self.source = np.asarray(source.convert("RGBA")).copy()
        self.size = source.size
        self.paths, self.rows, self.allowed = paths, rows, allowed
        self.active = self.source[:, :, 3] > 0
        self.completed = np.zeros(self.active.shape, dtype=bool)
        self.index = 0
        self.last_time = -1.

    def at(self, elapsed: float) -> tuple[Image.Image, dict, np.ndarray, np.ndarray]:
        if elapsed < self.last_time:
            raise ValueError("MONOTONIC_TIMELINE_REQUIRED")
        self.last_time = elapsed
        while self.index < len(self.rows) and elapsed >= self.rows[self.index]["pen_down_end"]:
            path = self.paths[self.index]
            self.completed |= coverage(self.size, path, 1.) & self.allowed[path.phase] & self.active
            self.index += 1
        visible = self.completed.copy()
        brush = np.zeros(self.active.shape, dtype=bool)
        trace: dict = {"state": "REST", "tip": None, "phase": None, "stroke_id": None}
        if self.index < len(self.rows):
            row, path = self.rows[self.index], self.paths[self.index]
            trace.update(phase=path.phase, stroke_id=path.stroke_id)
            if elapsed <= row["pen_up_start"]:
                trace.update(state="IDLE")
            elif elapsed < row["pen_down_start"]:
                fraction = (elapsed - row["pen_up_start"]) / row["pen_up_seconds"]
                trace.update(state="UP", tip=[a + (b - a) * fraction for a, b in
                                              zip(row["pen_up_from"], row["pen_up_to"], strict=True)])
            else:
                fraction = (elapsed - row["pen_down_start"]) / row["pen_down_seconds"]
                brush = coverage(self.size, path, fraction) & self.allowed[path.phase] & self.active
                visible |= brush
                trace.update(state="DOWN", tip=list(_partial_points(path, fraction)[-1]),
                             fraction=fraction)
        array = self.source.copy()
        array[:, :, 3] = np.where(visible, self.source[:, :, 3], 0)
        return Image.fromarray(array), trace, visible, brush


def presentation(image: Image.Image, trace: dict, paths: tuple[ObjectStrokeV2, ...],
                 *, debug: bool) -> Image.Image:
    scale = min(3., 820 / image.width, 400 / image.height)
    size = (round(image.width * scale), round(image.height * scale))
    origin = ((960 - size[0]) // 2, (540 - size[1]) // 2)
    result = Image.new("RGB", FRAME_SIZE, "white")
    result.paste(on_white(image).resize(size, Image.Resampling.LANCZOS), origin)
    if debug:
        draw = ImageDraw.Draw(result)
        if trace["tip"] is not None:
            sx, sy = size[0] / image.width, size[1] / image.height
            x, y = origin[0] + trace["tip"][0] * sx, origin[1] + trace["tip"][1] * sy
            color = "#ca4429" if trace["state"] == "DOWN" else "#277fa6"
            if trace["state"] == "DOWN":
                path = next(p for p in paths if p.stroke_id == trace["stroke_id"])
                draw.line([(origin[0] + a * sx, origin[1] + b * sy)
                           for a, b in _partial_points(path, trace["fraction"])], fill=color, width=1)
            draw.ellipse((x - 4, y - 4, x + 4, y + 4), outline=color, width=2)
            draw.line((x, y, x + 12, y - 20), fill=color, width=3)
        draw.text((24, 505), f"{trace['state']} | {trace['phase']} | {trace['stroke_id']}",
                  fill="#34465a")
    return result


def render(manifest_ref: Path, world_ref: Path, paths_dir: Path, output: Path,
           *, confirmed: bool) -> dict:
    if not confirmed:
        raise ValueError("HOUSE_PROOF_APPROVAL_REQUIRED")
    if output.exists() or output.resolve().is_relative_to(Path(__file__).resolve().parents[1]):
        raise ValueError("NEW_PRIVATE_OUTPUT_REQUIRED")
    manifest = json.loads(manifest_ref.read_bytes())
    world = json.loads(world_ref.read_bytes())
    item = next(o for o in manifest["objects"] if o["object_type"] == "house")
    spec = next(o for o in world["source_objects"] if o["object_id"] == item["object_id"])
    protected = [(manifest["source_ref"], manifest["source_image_sha256"])] + [
        (o["mask_ref"], o["mask_sha256"]) for o in manifest["objects"]
    ]
    for ref, digest in protected:
        checked_bytes(ref, digest)
    asset_body = checked_bytes(spec["asset_ref"], spec["asset_sha256"])
    source = Image.open(io.BytesIO(asset_body)).convert("RGBA")
    original = Image.open(io.BytesIO(checked_bytes(*protected[0]))).convert("RGB")
    master = Image.open(item["mask_ref"]).convert("L")
    crop = original.crop(tuple(item["bbox_pixels"])).convert("RGBA")
    crop.putalpha(master.crop(tuple(item["bbox_pixels"])))
    if crop.tobytes() != source.tobytes():
        raise ValueError("HOUSE_CROP_SOURCE_PIXEL_MISMATCH")
    snapshot = json.loads((paths_dir.parent / "artifact-sha256.json").read_bytes())
    for entry in snapshot["files"]:
        if Path(entry["ref"]).parent == paths_dir:
            checked_bytes(entry["ref"], entry["sha256"])
    paths_body = (paths_dir / "paths.json").read_bytes()
    path_data = json.loads(paths_body)
    if path_data["object_id"] != item["object_id"]:
        raise ValueError("HOUSE_PATH_IDENTITY_MISMATCH")
    paths = tuple(ObjectStrokeV2.model_validate(p) for p in path_data["paths"])
    allowed = {p: np.asarray(Image.open(paths_dir / f"{p.lower()}-phase-mask.png")) > 0
               for p in PHASES}
    rows = [r for p in PHASES for r in json.loads(
        (paths_dir / f"{p.lower()}-pen-transitions.json").read_bytes())]
    if [p.stroke_id for p in paths] != [r["stroke_id"] for r in rows]:
        raise ValueError("HOUSE_PATH_TIMELINE_MISMATCH")
    if any(allowed[p].shape != (source.height, source.width) for p in PHASES):
        raise ValueError("HOUSE_PHASE_MASK_COORDINATE_MISMATCH")
    output.mkdir(parents=True)
    started = time.perf_counter()
    seconds = rows[-1]["pen_down_end"]
    count = math.ceil((seconds + 1.35) * FPS)
    if count > 24 * 180:
        raise ValueError("PROOF_TIME_BUDGET_EXCEEDED")
    animator = SourceProgress(source, paths, rows, allowed)
    names = ("house-clean.mp4", "house-pen-debug.mp4")
    writers = [imageio_ffmpeg.write_frames(
        str(output / name), FRAME_SIZE, fps=FPS, codec="libx264", pix_fmt_in="rgb24",
        pix_fmt_out="yuv420p", macro_block_size=1,
        output_params=["-crf", "16", "-preset", "medium"],
    ) for name in names]
    for writer in writers:
        writer.send(None)
    previous = np.zeros((source.height, source.width), dtype=bool)
    entries = []
    tip_error = 0.
    early_color = 0
    out_of_brush = 0
    max_new_color = 0
    color_start = next(r["pen_down_start"] for r in rows if r["phase"] == "COLOR")
    ink = allowed["OUTLINE"] | allowed["DETAIL"]
    try:
        for index in range(count):
            elapsed = index / FPS
            # Independent sampled-history check includes naturally finished prior path(s).
            prior_completed = animator.completed.copy()
            rgba, trace, visible, brush = animator.at(elapsed)
            newly_finished = animator.completed & ~prior_completed
            delta = visible & ~previous
            out_of_brush += int((delta & ~(brush | newly_finished)).sum())
            if elapsed < color_start:
                early_color += int((visible & ~ink).sum())
            if trace["state"] == "DOWN":
                path = paths[animator.index]
                tip_error = max(tip_error, math.dist(trace["tip"],
                                                     _partial_points(path, trace["fraction"])[-1]))
            if trace["phase"] == "COLOR":
                max_new_color = max(max_new_color, int(delta.sum()))
            for name, writer in zip(names, writers, strict=True):
                writer.send(np.asarray(presentation(rgba, trace, paths,
                                                   debug="debug" in name)).tobytes())
            entries.append({"frame": index, "seconds": elapsed, **trace,
                            "new_source_pixels": int(delta.sum()), "visible_source_pixels": int(visible.sum())})
            previous = visible
    finally:
        for writer in writers:
            writer.close()
    full, _, visible, _ = animator.at(count / FPS)
    exact = full.tobytes() == source.tobytes()
    source.save(output / "source-house-target.png")
    full.save(output / "final-native-rgba.png")
    final_frame = presentation(full, {"tip": None}, paths, debug=False)
    target_frame = presentation(source, {"tip": None}, paths, debug=False)
    final_frame.save(output / "final-raw-frame.png")
    native_diff = np.abs(np.asarray(full).astype(int) - np.asarray(source).astype(int))
    Image.fromarray(np.clip(native_diff[:, :, :3] * 8, 0, 255).astype(np.uint8)).save(
        output / "native-difference-x8.png")
    sampled_times = [0., seconds * .25, seconds * .5, seconds * .75, seconds,
                     2., 4., 10., 20., 32.8, 33., 35., 38., 42., 50., 60.]
    indices = {min(count - 1, round(t * FPS)) for t in sampled_times} | {count - 1}
    phase_previews = []
    stage_previews = []
    decoded = []
    for name in names:
        samples, meta, decoded_count = decode_samples(output / name, indices)
        decoded.append({"file": name, "metadata": meta, "decoded_frames": decoded_count})
        for percent in (0, 25, 50, 75, 100):
            index = min(count - 1, round(seconds * percent / 100 * FPS))
            stage_previews.append((f"{name} {percent}% @{index/FPS:.2f}s", samples[index]))
        for elapsed in sampled_times[5:]:
            index = min(count - 1, round(elapsed * FPS))
            phase_previews.append((f"{name} @{index/FPS:.2f}s", samples[index]))
        if name == names[0]:
            samples[count - 1].save(output / "final-decoded-frame.png")
            difference = np.abs(np.asarray(samples[count - 1]).astype(float) - np.asarray(target_frame))
            decoded_mae = float(difference.mean())
            Image.fromarray(np.clip(difference * 8, 0, 255).astype(np.uint8)).save(
                output / "decoded-difference-x8.png")
    contact(stage_previews, output / "encoded-contact-sheet.png", columns=5)
    contact(phase_previews, output / "phase-temporal-contact-sheet.png", columns=4)
    write_json(output / "frame-execution.json", entries)
    write_json(output / "path-execution.json", rows)
    write_json(output / "source-paths.json", path_data)
    result = {"date": "2026-10-10", "object_id": item["object_id"],
              "approval": "LOCAL_SOURCE_OBJECT_PROOF_NOT_PRODUCTION_GATE", "visual_qa": "NOT_PASSED",
              "source_sha256": manifest["source_image_sha256"], "asset_sha256": spec["asset_sha256"],
              "mask_sha256": item["mask_sha256"], "paths_sha256": sha(paths_body),
              "native_size": source.size, "source_crop_exact": True, "frames": count, "fps": FPS,
              "duration_seconds": count / FPS, "drawing_seconds": seconds,
              "end_hold_seconds": count / FPS - seconds, "path_count": len(paths),
              "pen_lifts": sum(r["pen_up_from"] is not None for r in rows),
              "zero_length_paths": sum(len(set(p.points)) == 1 for p in paths),
              "phase_pixels": {p: int(allowed[p].sum()) for p in PHASES},
              "phase_paths": {p: sum(v.phase == p for v in paths) for p in PHASES},
              "source_pixels": int(animator.active.sum()), "final_visible_pixels": int(visible.sum()),
              "early_color_pixels": early_color, "out_of_brush_pixels": out_of_brush,
              "tip_endpoint_error_native_pixels": tip_error, "max_new_color_pixels_per_frame": max_new_color,
              "final_native_rgba_exact": exact, "decoded_final_rgb_mae": decoded_mae,
              "decoded": decoded, "wall_seconds": time.perf_counter() - started,
              "production_engine_edited": False, "audio": False, "network": False}
    result["technical_status"] = "PASS" if (exact and not early_color and not out_of_brush
                                             and tip_error == 0 and all(d["decoded_frames"] == count
                                                                     for d in decoded)) else "FAIL"
    for ref, digest in protected:
        checked_bytes(ref, digest)
    write_json(output / "timing-and-path-report.json", result)
    write_json(output / "artifact-sha256.json", {"files": [
        {"ref": str(p), "sha256": sha(p.read_bytes()), "bytes": p.stat().st_size}
        for p in sorted(output.iterdir()) if p.is_file()
    ]})
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--world", type=Path, required=True)
    parser.add_argument("--paths-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--confirm-house-proof", action="store_true")
    args = parser.parse_args()
    print(json.dumps(render(args.source_manifest, args.world, args.paths_dir, args.output_dir,
                            confirmed=args.confirm_house_proof), indent=2))
