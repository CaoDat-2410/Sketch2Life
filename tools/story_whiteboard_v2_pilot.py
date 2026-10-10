"""Offline synthetic A/B V2 drawing pilots; no Gate or production video claim."""

from __future__ import annotations

import argparse
import json
import time
import tracemalloc
from pathlib import Path
from typing import Literal

from sketch2life.application.services.story_draw_schedule_v2 import build_draw_schedule
from sketch2life.infrastructure.media.object_stroke_engine_v2 import (
    LocalObjectAwareStrokeEngine,
)
from sketch2life.infrastructure.media.whiteboard_renderer_v2 import render_scene_pilot

from tools.story_world_v2_fixture import make_prototype as family_prototype
from tools.story_world_v2_ocean_fixture import make_prototype as ocean_prototype


def render_fixture(
    fixture: str, output_dir: Path, *, duration_seconds: float = 6., fps: int = 12,
    strategy: Literal["legacy", "refined"] = "refined",
) -> dict:
    if fixture == "family":
        result = family_prototype()
    elif fixture == "ocean-png":
        result = ocean_prototype(image_format="PNG")
    elif fixture == "ocean-jpeg":
        result = ocean_prototype(image_format="JPEG")
    else:
        raise ValueError("fixture must be family, ocean-png or ocean-jpeg")
    scene = result.scene_plan.scenes[0]
    tracemalloc.start()
    try:
        start = time.perf_counter()
        engine = LocalObjectAwareStrokeEngine(strategy=strategy)
        objects = tuple(
            engine.extract_object(result.registry, obj.object_id)
            for obj in result.registry.world.source_objects
        )
        extraction_seconds = time.perf_counter() - start
        schedule = build_draw_schedule(scene, objects, duration_seconds=duration_seconds, fps=fps)
        output_dir.mkdir(parents=True, exist_ok=True)
        render_start = time.perf_counter()
        pilot = render_scene_pilot(
            result.registry, scene, objects, schedule,
            video_path=output_dir / f"{fixture}-v2-pilot.mp4",
            contact_sheet_path=output_dir / f"{fixture}-v2-0-25-50-75-100.png",
            fps=fps,
        )
        render_seconds = time.perf_counter() - render_start
        _current, peak_bytes = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    (output_dir / f"{fixture}-strokes.json").write_text(
        json.dumps([item.model_dump(mode="json") for item in objects], ensure_ascii=False,
                   indent=2), encoding="utf-8",
    )
    (output_dir / f"{fixture}-draw-schedule.json").write_text(
        schedule.model_dump_json(indent=2), encoding="utf-8",
    )
    metrics = {
        "fixture": fixture,
        "stroke_strategy": strategy,
        "scene_id": scene.scene_id,
        "source_object_ids": [item.object_id for item in objects],
        "outline_paths": sum(len(item.outline_paths) for item in objects),
        "detail_paths": sum(len(item.detail_paths) for item in objects),
        "color_paths": sum(len(item.color_paths) for item in objects),
        "extraction_seconds": extraction_seconds,
        "render_seconds": render_seconds,
        "python_tracemalloc_peak_bytes": peak_bytes,
        "video_path": pilot.video_path,
        "contact_sheet_path": pilot.contact_sheet_path,
        "fps": pilot.fps,
        "duration_seconds": pilot.duration_seconds,
        "frame_count": pilot.frame_count,
        "final_mae": pilot.final_mae,
        "final_changed_pixels": pilot.final_changed_pixels,
        "source_mask_coverage": pilot.source_mask_coverage,
        "original_to_canonical_mae": pilot.original_to_canonical_mae,
        "decoded_final_mae": pilot.decoded_final_mae,
        "decoded_contact_sheet_path": pilot.decoded_contact_sheet_path,
        "difference_map_paths": list(pilot.difference_map_paths),
        "approval_verification": result.approval_verification,
        "visual_qa": "PENDING_HUMAN_REVIEW",
    }
    (output_dir / f"{fixture}-metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8",
    )
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", choices=("family", "ocean-png", "ocean-jpeg"),
                        required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--duration", type=float, default=6.)
    parser.add_argument("--fps", type=int, default=12)
    parser.add_argument("--strategy", choices=("legacy", "refined"), default="refined")
    args = parser.parse_args()
    print(json.dumps(render_fixture(args.fixture, args.output_dir,
                                   duration_seconds=args.duration, fps=args.fps,
                                   strategy=args.strategy), indent=2))


if __name__ == "__main__":
    main()
