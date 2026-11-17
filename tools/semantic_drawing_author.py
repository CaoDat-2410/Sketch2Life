"""Validate/preview editable versioned JSON packs and optionally render local proof."""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import imageio_ffmpeg  # type: ignore[import-untyped]
import numpy as np
from PIL import Image, ImageDraw
from sketch2life.contracts.schemas.semantic_authoring_v1 import SemanticAuthoringPackV1
from sketch2life.infrastructure.media.semantic_authoring_v1 import compile_pack
from sketch2life.infrastructure.media.semantic_drawing_engine_v2 import SemanticProgress
from sketch2life.infrastructure.media.whiteboard_renderer_v2 import _partial_points

from tools.prepare_whiteboard_slice_step_a import sha, write_json
from tools.refine_butterfly_candidate import contact, on_white
from tools.render_butterfly_video_proof import decode_samples


def view(rgba: Image.Image, scale: float) -> tuple[Image.Image, tuple]:
    size = (max(1, round(rgba.width * scale)), max(1, round(rgba.height * scale)))
    small = rgba.resize(size, Image.Resampling.LANCZOS)
    zoom = (
        min(8.0, 780 / size[0], 380 / size[1])
        if scale < 1
        else min(3.0, 780 / size[0], 380 / size[1])
    )
    enlarged = (round(size[0] * zoom), round(size[1] * zoom))
    origin = ((960 - enlarged[0]) // 2, (540 - enlarged[1]) // 2)
    frame = Image.new("RGB", (960, 540), "white")
    frame.paste(on_white(small).resize(enlarged, Image.Resampling.LANCZOS), origin)
    if scale < 1:
        frame.paste(on_white(small), (840, 40))
    return frame, (
        origin[0],
        origin[1],
        enlarged[0] / rgba.width,
        enlarged[1] / rgba.height,
    )


def run(
    pack_path: Path, output: Path, *, render: bool = False, confirmed: bool = False
) -> dict:
    if render and not confirmed:
        raise ValueError("TECHNICAL_PROOF_PERMISSION_REQUIRED")
    if output.exists() or output.resolve().is_relative_to(
        Path(__file__).resolve().parents[1]
    ):
        raise ValueError("NEW_PRIVATE_OUTPUT_REQUIRED")
    output.mkdir(parents=True)
    pack = SemanticAuthoringPackV1.model_validate_json(pack_path.read_bytes())
    asset, plan, stats = compile_pack(pack_path, output / "needs-review")
    write_json(
        output / "authoring-schema.json", SemanticAuthoringPackV1.model_json_schema()
    )
    write_json(output / "authoring-pack.snapshot.json", pack.model_dump(mode="json"))
    write_json(output / "path-timing.json", plan["rows"])
    write_json(output / "preflight.json", stats)
    previews = []
    for phase in ("OUTLINE", "DETAIL", "COLOR"):
        image = on_white(asset.source)
        draw = ImageDraw.Draw(image)
        for s in plan["strokes"]:
            if s.path.phase == phase:
                draw.line(
                    s.path.points,
                    fill="#de541f" if phase == "COLOR" else "#182734",
                    width=1,
                )
        image.save(output / f"{phase.lower()}-path-preview.png")
        previews.append((phase, image))
    contact(previews, output / "path-contact-sheet.png")
    if not render:
        return stats
    if plan["seconds"] > 180:
        raise ValueError("RENDER_RESOURCE_LIMIT: authored proof exceeds180s")
    started = time.perf_counter()
    frame_count = math.ceil((plan["seconds"] + 1.0) * 24)
    writers = [
        imageio_ffmpeg.write_frames(
            str(output / name),
            (960, 540),
            fps=24,
            codec="libx264",
            pix_fmt_in="rgb24",
            pix_fmt_out="yuv420p",
            macro_block_size=1,
            output_params=["-crf", "16", "-preset", "medium"],
        )
        for name in ("clean.mp4", "pen-debug.mp4")
    ]
    for writer in writers:
        writer.send(None)
    engine = SemanticProgress(asset, plan)
    previous = np.zeros(engine.color.shape, dtype=bool)
    previous_state = None
    early = up_error = 0
    tip_error = 0.0
    max_new_color = 0
    traces = []
    try:
        for frame_index in range(frame_count):
            now = frame_index / 24
            rgba, trace, masks = engine.at(now)
            delta = masks["color"] & ~previous
            max_new_color = max(max_new_color, int(delta.sum()))
            if trace["phase"] in {"OUTLINE", "DETAIL"} and masks["color"].any():
                early += 1
            if trace["state"] == "UP" and previous_state == (engine.index, "UP"):
                up_error += int(delta.sum())
            if trace["state"] == "DOWN":
                stroke = plan["strokes"][engine.index]
                tip_error = max(
                    tip_error,
                    math.dist(
                        trace["tip"],
                        _partial_points(stroke.path, trace["fraction"])[-1],
                    ),
                )
            clean, transform = view(rgba, pack.presentation_scale)
            debug = clean.copy()
            draw = ImageDraw.Draw(debug)
            if trace["tip"]:
                ox, oy, sx, sy = transform
                x, y = ox + trace["tip"][0] * sx, oy + trace["tip"][1] * sy
                color = "#cf4423" if trace["state"] == "DOWN" else "#2780a4"
                draw.ellipse((x - 4, y - 4, x + 4, y + 4), outline=color, width=2)
                draw.line((x, y, x + 12, y - 20), fill=color, width=3)
            draw.text(
                (20, 510),
                f"{now:.2f}s {trace['state']} {trace['phase']} {trace['stroke_id']}",
                fill="#263948",
            )
            for image, writer in zip((clean, debug), writers, strict=True):
                writer.send(np.asarray(image).tobytes())
            traces.append(
                {
                    "frame": frame_index,
                    "seconds": now,
                    **trace,
                    "new_color_pixels": int(delta.sum()),
                    "color_pixels": int(masks["color"].sum()),
                }
            )
            previous, previous_state = masks["color"], (engine.index, trace["state"])
    finally:
        for writer in writers:
            writer.close()
    final, _, masks = engine.at(max(engine.last_time, plan["seconds"] + 0.01))
    exact = final.tobytes() == asset.source.tobytes()
    final.save(output / "final-native.png")
    asset.source.save(output / "source-target.png")
    raw_target, _ = view(asset.source, pack.presentation_scale)
    raw_target.save(output / "target-presentation.png")
    rows = []
    counts = []
    indices = {
        min(frame_count - 1, round(plan["seconds"] * p * 24))
        for p in (0, 0.25, 0.5, 0.75, 1.0)
    }
    indices.add(frame_count - 1)
    for name in ("clean.mp4", "pen-debug.mp4"):
        samples, _meta, count = decode_samples(output / name, indices)
        counts.append(count)
        for p in (0, 0.25, 0.5, 0.75, 1.0):
            frame = min(frame_count - 1, round(plan["seconds"] * p * 24))
            rows.append((f"{name} {p:.0%} @{frame / 24:.2f}s", samples[frame]))
        if name == "clean.mp4":
            samples[frame_count - 1].save(output / "final-decoded.png")
            diff = np.abs(
                np.asarray(samples[frame_count - 1]).astype(float)
                - np.asarray(raw_target)
            )
            mae = float(diff.mean())
            Image.fromarray(np.clip(diff * 8, 0, 255).astype(np.uint8)).save(
                output / "decoded-difference-x8.png"
            )
    contact(rows, output / "contact-sheet-0-25-50-75-100.png", columns=5)
    write_json(output / "frame-execution.json", traces)
    report = stats | {
        "technical": "TECHNICAL_PASS"
        if exact
        and not early
        and not up_error
        and tip_error == 0
        and counts == [frame_count, frame_count]
        else "TECHNICAL_FAIL",
        "visual": "VISUAL_QA_NOT_PASSED",
        "owner": "OWNER_APPROVAL_PENDING",
        "VIDEO_PLAYBACK_DURATION": frame_count / 24,
        "WALL_CLOCK_RENDER_TIME": time.perf_counter() - started,
        "frames": frame_count,
        "decoded_frames": counts,
        "fps": 24,
        "final_native_exact": exact,
        "decoded_rgb_mae": mae,
        "early_color_frames": early,
        "consecutive_pen_up_color_changes": up_error,
        "tip_endpoint_error": tip_error,
        "max_new_color_pixels_per_frame": max_new_color,
        "pack_sha256": sha(pack_path.read_bytes()),
        "source_style": asset.style_profile,
        "audio": False,
        "network": False,
    }
    write_json(output / "result.json", report)
    write_json(
        output / "artifact-sha256.json",
        {
            "files": [
                {
                    "ref": str(p),
                    "sha256": sha(p.read_bytes()),
                    "bytes": p.stat().st_size,
                }
                for p in sorted(output.rglob("*"))
                if p.is_file()
            ]
        },
    )
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pack", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--confirm-local-technical-proof", action="store_true")
    args = parser.parse_args()
    print(
        json.dumps(
            run(
                args.pack,
                args.output_dir,
                render=args.render,
                confirmed=args.confirm_local_technical_proof,
            ),
            indent=2,
        )
    )
