"""One private CPU benchmark batch of the versioned semantic V2 strategy."""

from __future__ import annotations

import argparse
import json
import math
import time
from dataclasses import asdict
from pathlib import Path

import imageio_ffmpeg  # type: ignore[import-untyped]
import numpy as np
from PIL import Image, ImageDraw
from sketch2life.contracts.schemas.semantic_drawing_v2 import (
    DrawingBudget,
    TextStoryBeat,
)
from sketch2life.infrastructure.media.semantic_drawing_engine_v2 import (
    SemanticProgress,
    SemanticStrokeStrategyV1,
    eased,
    integrate_beats,
    optimize,
)

from tools.prepare_whiteboard_slice_step_a import checked_bytes, sha, write_json
from tools.refine_butterfly_candidate import contact, on_white
from tools.render_butterfly_video_proof import decode_samples, load_candidate


def describe(schedule: dict) -> dict:
    return {k: v for k, v in schedule.items() if k != "strokes"} | {
        "paths": [
            {"path": s.path.model_dump(mode="json"), "role": s.role,
             "region_id": s.region_id, "essential": s.essential}
            for s in schedule["strokes"]
        ],
        "path_count": len(schedule["strokes"]),
        "pen_lifts": max(0, len(schedule["strokes"]) - 1),
    }


def encode(asset, schedule, directory: Path, *, integrated=None) -> dict:
    directory.mkdir()
    seconds = schedule["seconds"] if integrated is None else integrated[-1]["end"]
    if seconds > 300:
        return {"status": "RENDER_RESOURCE_LIMIT", "seconds": seconds}
    started = time.perf_counter()
    frames = math.ceil((seconds + 1.0) * 24)
    writers = [
        imageio_ffmpeg.write_frames(
            str(directory / name),
            (960, 540),
            fps=24,
            codec="libx264",
            pix_fmt_in="rgb24",
            pix_fmt_out="yuv420p",
            macro_block_size=1,
            output_params=["-crf", "16", "-preset", "fast"],
        )
        for name in ("clean.mp4", "pen-debug.mp4")
    ]
    for writer in writers:
        writer.send(None)
    engines = (
        [SemanticProgress(asset, schedule)]
        if integrated is None
        else [
            SemanticProgress(entry["asset"], entry["schedule"]) for entry in integrated
        ]
    )
    audits = []
    prior_masks = [np.zeros(e.color.shape, dtype=bool) for e in engines]
    max_new = early = up_violation = 0
    previous_fraction = None
    final_rgba = None
    try:
        for index in range(frames):
            now = index / 24
            trace = {"tip": None, "state": "REST", "phase": None, "stroke_id": None}
            if integrated is None:
                final_rgba, trace, masks = engines[0].at(now)
                scale = min(2.5, 800 / asset.source.width, 380 / asset.source.height)
                size = (
                    round(asset.source.width * scale),
                    round(asset.source.height * scale),
                )
                origin = ((960 - size[0]) // 2, (540 - size[1]) // 2)
                canvas = Image.new("RGB", (960, 540), "white")
                canvas.paste(
                    on_white(final_rgba).resize(size, Image.Resampling.LANCZOS), origin
                )
                transform = (
                    origin[0],
                    origin[1],
                    size[0] / asset.source.width,
                    size[1] / asset.source.height,
                )
                delta = masks["color"] & ~prior_masks[0]
                max_new = max(max_new, int(delta.sum()))
                if trace["phase"] in ("OUTLINE", "DETAIL") and masks["color"].any():
                    early += 1
                if trace["state"] == "UP" and previous_fraction == (
                    engines[0].index,
                    "UP",
                ):
                    up_violation += int(delta.sum())
                previous_fraction = (engines[0].index, trace["state"])
                prior_masks[0] = masks["color"]
            else:
                board = Image.new("RGBA", (594, 336), "white")
                active_entry = integrated[0]
                position = 0
                for entry_index, (entry, engine) in enumerate(
                    zip(integrated, engines, strict=True)
                ):
                    if now < entry["start"]:
                        continue
                    rgba, candidate_trace, _ = engine.at(
                        min(entry["schedule"]["seconds"], now - entry["start"])
                    )
                    board.alpha_composite(
                        rgba.resize(entry["display_size"], Image.Resampling.LANCZOS),
                        entry["origin"],
                    )
                    if entry["start"] <= now <= entry["end"]:
                        active_entry, trace, position = (
                            entry,
                            candidate_trace,
                            entry_index,
                        )
                # Continuous eased focus translation and light zoom; persistent board is never cleared.
                previous_focus = integrated[max(0, position - 1)]["beat"].camera_focus
                focus = active_entry["beat"].camera_focus
                t = eased(min(1.0, max(0.0, now - active_entry["start"])))
                focus = tuple(
                    a + (b - a) * t for a, b in zip(previous_focus, focus, strict=True)
                )
                zoom = 1.0 + 0.04 * eased(min(1.0, now))
                canvas = board.convert("RGB").resize(
                    (960, 540), Image.Resampling.LANCZOS
                )
                cx, cy = 480 + (focus[0] - 297) * 0.1, 270 + (focus[1] - 168) * 0.1
                box = (
                    cx - 480 / zoom,
                    cy - 270 / zoom,
                    cx + 480 / zoom,
                    cy + 270 / zoom,
                )
                canvas = canvas.transform(
                    (960, 540),
                    Image.Transform.EXTENT,
                    box,
                    resample=Image.Resampling.BICUBIC,
                )
                ox, oy = active_entry["origin"]
                sx = (
                    active_entry["display_size"][0] / active_entry["asset"].source.width
                )
                sy = (
                    active_entry["display_size"][1]
                    / active_entry["asset"].source.height
                )
                transform = (
                    (ox * 960 / 594 - box[0]) * zoom,
                    (oy * 540 / 336 - box[1]) * zoom,
                    sx * 960 / 594 * zoom,
                    sy * 540 / 336 * zoom,
                )
            debug = canvas.copy()
            draw = ImageDraw.Draw(debug)
            if trace["tip"]:
                ox, oy, sx, sy = transform
                x, y = ox + trace["tip"][0] * sx, oy + trace["tip"][1] * sy
                color = "#ca4422" if trace["state"] == "DOWN" else "#267ca1"
                draw.ellipse((x - 4, y - 4, x + 4, y + 4), outline=color, width=2)
                draw.line((x, y, x + 12, y - 20), fill=color, width=3)
            draw.text(
                (20, 515),
                f"{now:.2f}s {trace['state']} {trace['phase']} {trace['stroke_id']}",
                fill="#324255",
            )
            for writer, image in zip(writers, (canvas, debug), strict=True):
                writer.send(np.asarray(image).tobytes())
            audits.append({"frame": index, "seconds": now, **trace})
    finally:
        for writer in writers:
            writer.close()
    final_exact = []
    for engine in engines:
        complete, _, masks = engine.at(
            max(engine.last_time, engine.schedule["seconds"] + 0.01)
        )
        final_exact.append(complete.tobytes() == engine.asset.source.tobytes())
    if integrated is None:
        complete.save(directory / "final-native.png")
        asset.source.save(directory / "source-target.png")
    samples = []
    counts = []
    indices = {
        min(frames - 1, round(seconds * p * 24)) for p in (0, 0.25, 0.5, 0.75, 1)
    } | {frames - 1}
    for name in ("clean.mp4", "pen-debug.mp4"):
        decoded, _metadata, count = decode_samples(directory / name, indices)
        counts.append(count)
        for frame in sorted(indices):
            samples.append((f"{name} @{frame / 24:.2f}s", decoded[frame]))
        if name == "clean.mp4":
            decoded[frames - 1].save(directory / "final-decoded.png")
    contact(samples, directory / "contact-sheet.png", columns=3)
    write_json(directory / "frame-execution.json", audits)
    result = {
        "VIDEO_PLAYBACK_DURATION": frames / 24,
        "WALL_CLOCK_RENDER_TIME": time.perf_counter() - started,
        "frames": frames,
        "decoded_frame_counts": counts,
        "final_native_exact": final_exact,
        "max_new_color_pixels_per_frame": max_new,
        "early_color_violations": early,
        "consecutive_pen_up_color_changes": up_violation,
        "technical": "TECHNICAL_PASS"
        if all(final_exact)
        and counts == [frames, frames]
        and early == 0
        and up_violation == 0
        else "TECHNICAL_FAIL",
        "visual": "VISUAL_QA_NOT_PASSED",
        "owner": "OWNER_REVIEW_PENDING",
        "integrated_audit_scope": "per-object final and decode only"
        if integrated
        else "single-object",
    }
    write_json(directory / "render-report.json", result)
    return result


def main(output: Path) -> None:
    if output.exists() or output.resolve().is_relative_to(
        Path(__file__).resolve().parents[1]
    ):
        raise ValueError("NEW_PRIVATE_OUTPUT_REQUIRED")
    manifest_ref = Path(
        "D:/Codex/Sketch2Life/real_family_benchmark_2026-10-09/source-object-manifest.json"
    )
    manifest = json.loads(manifest_ref.read_bytes())
    source_body = checked_bytes(manifest["source_ref"], manifest["source_image_sha256"])
    for item in manifest["objects"]:
        checked_bytes(item["mask_ref"], item["mask_sha256"])
    source = Image.open(manifest["source_ref"]).convert("RGBA")
    output.mkdir(parents=True)
    strategy = SemanticStrokeStrategyV1()
    source_hash = sha(source_body)
    world = json.loads(
        Path(
            "D:/Codex/Sketch2Life/real_schedule_debug_2026-10-09/benchmark-world.json"
        ).read_bytes()
    )
    house = next(o for o in world["source_objects"] if o["object_type"] == "house")
    checked_bytes(house["asset_ref"], house["asset_sha256"])
    house_asset = strategy.prepare(
        Image.open(house["asset_ref"]),
        house["object_id"],
        "SOURCE_DRAWING",
        source_hash,
    )
    garden = next(o for o in manifest["objects"] if o["object_type"] == "garden")
    mask = Image.open(garden["mask_ref"]).crop((450, 180, 555, 265))
    cluster = source.crop((450, 180, 555, 265))
    cluster.putalpha(mask)
    garden_asset = strategy.prepare(
        cluster, "source-garden-cluster", "SOURCE_DERIVED_CROP", source_hash
    )
    candidate, _, _ = load_candidate(
        Path("D:/Codex/Sketch2Life/butterfly_refinement_2026-10-09/review-final")
    )
    regions = {k: np.asarray(v) > 0 for k, v in candidate.region_masks.items()}
    union = np.logical_or.reduce(list(regions.values()))
    regions["ink-only"] = (np.asarray(candidate.asset)[:, :, 3] > 0) & ~union
    butterfly_asset = strategy.prepare(
        candidate.asset,
        "local-new-butterfly-01",
        "NEW_LOCAL_AUTHORED",
        source_hash,
        authored=candidate.paths,
        region_overrides=regions,
    )
    butterfly_asset.style_profile["presentation_scale"] = 0.22
    assets = {
        "A-butterfly": (butterfly_asset, 5.0),
        "B-house": (house_asset, 8.0),
        "C-garden": (garden_asset, 6.0),
    }
    reports: dict = {}
    for name, (asset, target) in assets.items():
        schedule = optimize(asset, DrawingBudget(target, target))
        write_json(
            output / f"{name}-plan.json",
            {
                "schedule": describe(schedule),
                "style": asset.style_profile,
                "review": asset.review_status,
                "provenance": asset.provenance,
            },
        )
        preview = on_white(asset.source)
        draw = ImageDraw.Draw(preview)
        for stroke in schedule["strokes"]:
            if stroke.path.phase != "COLOR":
                draw.line(stroke.path.points, fill="#202020", width=1)
        preview.save(output / f"{name}-paths.png")
        reports[name] = {
            "timing_status": schedule["status"],
            "target": target,
            "feasible_seconds": schedule["seconds"],
            "path_count": len(schedule["strokes"]),
            "pen_lifts": len(schedule["strokes"]) - 1,
            "render": encode(asset, schedule, output / name),
        }
        print(name, schedule["status"], round(schedule["seconds"], 2), flush=True)
    by_id = {asset.object_id: asset for asset, _ in assets.values()}
    beats = [
        TextStoryBeat(
            "demo-house",
            house_asset.object_id,
            "Đây là ngôi nhà của gia đình em.",
            8.0,
            True,
            (430.0, 60.0),
        ),
        TextStoryBeat(
            "demo-flowers",
            garden_asset.object_id,
            "Trong vườn có những bông hoa.",
            6.0,
            True,
            (495.0, 220.0),
        ),
        TextStoryBeat(
            "demo-butterfly",
            butterfly_asset.object_id,
            "Một con bướm bay đến gần hoa.",
            5.0,
            True,
            (494.0, 164.0),
        ),
    ]
    timeline = integrate_beats(beats, by_id)
    origins = [(315, 0), (450, 180), (466, 144)]
    sizes = [house_asset.source.size, garden_asset.source.size, (56, 40)]
    for entry, origin, size in zip(timeline, origins, sizes, strict=True):
        entry.update(
            asset=by_id[entry["beat"].object_id], origin=origin, display_size=size
        )
    write_json(
        output / "D-simulated-beats.json",
        [
            {
                "beat": asdict(e["beat"]),
                "start": e["start"],
                "end": e["end"],
                "cue_kind": e["cue_kind"],
                "production_gate": e["production_gate"],
                "schedule": describe(e["schedule"]),
            }
            for e in timeline
        ],
    )
    reports["D-slice"] = encode(
        house_asset, timeline[0]["schedule"], output / "D-slice", integrated=timeline
    )
    reports["overall"] = "PARTIAL_NOT_END_TO_END_PASS"
    for item in manifest["objects"]:
        checked_bytes(item["mask_ref"], item["mask_sha256"])
    checked_bytes(manifest["source_ref"], source_hash)
    write_json(output / "batch-report.json", reports)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--confirm-local-rebuild-batch", action="store_true")
    args = parser.parse_args()
    if not args.confirm_local_rebuild_batch:
        raise ValueError("LOCAL_BATCH_APPROVAL_REQUIRED")
    main(args.output_dir)
