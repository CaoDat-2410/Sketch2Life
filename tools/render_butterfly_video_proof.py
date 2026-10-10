"""Offline immutable 21-path butterfly proof; no production integration or inference."""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import imageio_ffmpeg  # type: ignore[import-untyped]  # Upstream ships no type stubs.
import numpy as np
from PIL import Image, ImageDraw
from sketch2life.contracts.schemas.story_strokes_v2 import ObjectStrokeV2
from sketch2life.infrastructure.media.whiteboard_renderer_v2 import _partial_points

from tools.prepare_whiteboard_slice_step_a import checked_bytes, sha, write_json
from tools.refine_butterfly_candidate import Candidate, contact, on_white, progress

FPS = 24
FRAME_SIZE = (960, 540)
SMALL_SIZE = (56, 40)
VIEW_SIZE = (448, 320)
ORIGIN = (256, 100)


def load_candidate(directory: Path) -> tuple[Candidate, list[dict], dict]:
    manifest = json.loads((directory / "candidate-manifest-and-diagnostics.json").read_bytes())
    checked_bytes(str(directory / "butterfly-candidate-v2.png"), manifest["candidate_png_sha256"])
    hashes = json.loads((directory / "artifact-sha256.json").read_bytes())["files"]
    for item in hashes:
        checked_bytes(item["ref"], item["sha256"])
    specs = json.loads((directory / "candidate-paths.json").read_bytes())
    paths = tuple(ObjectStrokeV2.model_validate({k: v for k, v in s.items() if k != "part"})
                  for s in specs)
    if len(paths) != 21:
        raise ValueError("BASELINE_21_PATHS_REQUIRED")
    parts = tuple(s["part"] for s in specs)
    masks = {name: Image.open(directory / f"region-{name}.png").convert("L")
             for name in set(parts) if (directory / f"region-{name}.png").exists()}
    layers = [Image.open(directory / name).convert("RGBA") for name in
              ("fill-texture.png", "outline-ink.png", "detail-ink.png", "butterfly-candidate-v2.png")]
    candidate = Candidate(layers[0], layers[1], layers[2], layers[3], paths, parts,
                          masks, manifest["recipe"])
    rows = json.loads((directory / "pen-timeline-smaller.json").read_bytes())
    if [p.stroke_id for p in paths] != [r["stroke_id"] for r in rows]:
        raise ValueError("BASELINE_TIMELINE_PATH_MISMATCH")
    return candidate, rows, manifest


def presentation(rgba: Image.Image, trace: dict, candidate: Candidate, *, debug: bool) -> Image.Image:
    frame = Image.new("RGB", FRAME_SIZE, "white")
    small = rgba.resize(SMALL_SIZE, Image.Resampling.LANCZOS)
    frame.paste(on_white(small).resize(VIEW_SIZE, Image.Resampling.LANCZOS), ORIGIN)
    frame.paste(on_white(small), (840, 40))
    if debug and trace["tip"] is not None:
        sx, sy = VIEW_SIZE[0] / rgba.width, VIEW_SIZE[1] / rgba.height
        tip = (ORIGIN[0] + trace["tip"][0] * sx, ORIGIN[1] + trace["tip"][1] * sy)
        draw = ImageDraw.Draw(frame)
        color = "#c94326" if trace["state"] == "DOWN" else "#237eb1"
        if trace["state"] == "DOWN":
            path = next(p for p in candidate.paths if p.stroke_id == trace["stroke_id"])
            points = _partial_points(path, trace["fraction"])
            draw.line([(ORIGIN[0] + x * sx, ORIGIN[1] + y * sy) for x, y in points],
                      fill=color, width=1)
        draw.ellipse((tip[0] - 4, tip[1] - 4, tip[0] + 4, tip[1] + 4), outline=color, width=2)
        draw.line((tip[0], tip[1], tip[0] + 15, tip[1] - 23), fill=color, width=3)
        draw.text((24, 490), f"{trace['state']} | {trace['phase']} | {trace['stroke_id']}",
                  fill=color)
    return frame


def decode_samples(ref: Path, indices: set[int]) -> tuple[dict[int, Image.Image], dict, int]:
    reader = imageio_ffmpeg.read_frames(str(ref), pix_fmt="rgb24")
    metadata = next(reader)
    samples = {}
    count = 0
    try:
        for count, body in enumerate(reader, 1):
            index = count - 1
            if index in indices:
                samples[index] = Image.frombytes("RGB", FRAME_SIZE, body)
    finally:
        reader.close()
    return samples, metadata, count


def render(directory: Path, source_manifest: Path, output: Path, *, confirmed: bool) -> dict:
    if not confirmed:
        raise ValueError("TECHNICAL_PROOF_APPROVAL_REQUIRED")
    if output.exists() or output.resolve().is_relative_to(Path(__file__).resolve().parents[1]):
        raise ValueError("NEW_PRIVATE_OUTPUT_REQUIRED")
    candidate, rows, manifest = load_candidate(directory)
    source = json.loads(source_manifest.read_bytes())
    protected = [(source["source_ref"], source["source_image_sha256"])] + [
        (item["mask_ref"], item["mask_sha256"]) for item in source["objects"]
    ]
    for ref, digest in protected:
        checked_bytes(ref, digest)
    output.mkdir(parents=True)
    started = time.perf_counter()
    drawing_seconds = rows[-1]["pen_down_end"]
    count = math.ceil((drawing_seconds + 1.35) * FPS)
    writers = []
    names = ("butterfly-clean.mp4", "butterfly-pen-debug.mp4")
    for name in names:
        writer = imageio_ffmpeg.write_frames(str(output / name), FRAME_SIZE, fps=FPS,
                                            codec="libx264", pix_fmt_in="rgb24",
                                            pix_fmt_out="yuv420p", macro_block_size=1,
                                            output_params=["-crf", "16", "-preset", "medium"])
        writer.send(None)
        writers.append(writer)
    traces = []
    previous = {phase: np.zeros((184, 256), dtype=np.uint8)
                for phase in ("OUTLINE", "DETAIL", "COLOR")}
    early_color = 0
    pen_up_changes = 0
    tip_error = 0.
    max_new_color = 0
    color_start = next(r["pen_down_start"] for r in rows if r["phase"] == "COLOR")
    final_raw = None
    try:
        for index in range(count):
            elapsed = index / FPS
            rgba, trace, masks = progress(candidate, rows, elapsed)
            delta = {phase: int(((mask > 0) & (previous[phase] == 0)).sum())
                     for phase, mask in masks.items()}
            if elapsed < color_start and delta["COLOR"]:
                early_color += 1
            # A sampled UP frame can first display completion of the preceding path.
            # Compare to the exact prior pen-down boundary rather than previous video frame.
            if trace["state"] == "UP":
                row = next(r for r in rows if r["stroke_id"] == trace["stroke_id"])
                _, _, boundary = progress(candidate, rows, row["pen_up_start"] + 1e-9)
                pen_up_changes += sum(int(np.count_nonzero(masks[p] != boundary[p]))
                                      for p in masks)
            if trace["state"] == "DOWN":
                path = next(p for p in candidate.paths if p.stroke_id == trace["stroke_id"])
                endpoint = _partial_points(path, trace["fraction"])[-1]
                tip_error = max(tip_error, math.dist(trace["tip"], endpoint))
            max_new_color = max(max_new_color, delta["COLOR"])
            for debug, writer in zip((False, True), writers, strict=True):
                frame = presentation(rgba, trace, candidate, debug=debug)
                writer.send(np.asarray(frame).tobytes())
                if not debug:
                    final_raw = frame
            traces.append({"frame": index, "seconds": elapsed, **trace, "new_pixels": delta})
            previous = masks
    finally:
        for writer in writers:
            writer.close()
    full, _, masks = progress(candidate, rows, drawing_seconds + 1e-8)
    exact = full.tobytes() == candidate.asset.tobytes()
    full.save(output / "final-native-rgba.png")
    full.resize(SMALL_SIZE, Image.Resampling.LANCZOS).save(output / "final-small-rgba.png")
    target = presentation(candidate.asset, {"tip": None}, candidate, debug=False)
    target.save(output / "target-clean-frame.png")
    assert final_raw is not None
    final_raw.save(output / "final-raw-frame.png")
    fractions = (0, .25, .5, .75, 1.)
    indices = {min(count - 1, round(drawing_seconds * fraction * FPS)) for fraction in fractions}
    indices.add(count - 1)
    previews = []
    decoded_info = []
    for name in names:
        samples, metadata, decoded_count = decode_samples(output / name, indices)
        decoded_info.append({"file": name, "frames": decoded_count, "metadata": metadata})
        for fraction in fractions:
            index = min(count - 1, round(drawing_seconds * fraction * FPS))
            previews.append((f"{name}: {fraction:.0%} @ {index / FPS:.2f}s", samples[index]))
        if name == names[0]:
            decoded_final = samples[count - 1]
            decoded_final.save(output / "final-decoded-frame.png")
            difference = np.abs(np.asarray(decoded_final).astype(float) - np.asarray(target))
            decoded_mae = float(difference.mean())
            Image.fromarray(np.clip(difference * 8, 0, 255).astype(np.uint8)).save(
                output / "decoded-difference-x8.png")
    contact(previews, output / "encoded-contact-sheet.png", columns=5)
    write_json(output / "frame-execution.json", traces)
    write_json(output / "path-execution.json", rows)
    result = {"approval": "TECHNICAL_PROOF_ONLY", "visual_qa": "NOT_PASSED_PENDING_OWNER_REVIEW",
              "baseline_asset_sha256": manifest["candidate_png_sha256"],
              "baseline_paths_sha256": sha((directory / "candidate-paths.json").read_bytes()),
              "fps": FPS, "encoded_frames": count, "duration_seconds": count / FPS,
              "drawing_seconds": drawing_seconds, "end_hold_seconds": count / FPS - drawing_seconds,
              "pacing": "UNCHANGED_SMALLER_BASELINE_SCALE_0.22",
              "presentation": "56x40 small artwork,8x close-up and native-size inset; static camera",
              "path_count": len(rows), "pen_lifts": sum(r["pen_up_from"] is not None for r in rows),
              "early_color_frames": early_color, "pen_up_coverage_changes": pen_up_changes,
              "tip_endpoint_error_native_pixels": tip_error, "max_new_color_pixels_per_frame": max_new_color,
              "final_native_rgba_exact": exact,
              "final_raw_presentation_exact": final_raw.tobytes() == target.tobytes(),
              "decoded_final_rgb_mae": decoded_mae, "decoded": decoded_info,
              "wall_seconds": time.perf_counter() - started, "audio": False, "network": False}
    result["technical_status"] = "PASS" if (
        exact and result["final_raw_presentation_exact"] and not early_color
        and not pen_up_changes and tip_error == 0 and all(d["frames"] == count for d in decoded_info)
    ) else "FAIL"
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
    parser.add_argument("--candidate-dir", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--confirm-technical-proof-only", action="store_true")
    args = parser.parse_args()
    print(json.dumps(render(args.candidate_dir, args.source_manifest, args.output_dir,
                            confirmed=args.confirm_technical_proof_only), indent=2))
