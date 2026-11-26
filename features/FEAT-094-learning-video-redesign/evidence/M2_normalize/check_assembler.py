"""Run the real assembler and validator on test clips inside the video-worker container (FEAT-094).

    docker exec -i sketch2life-video-worker-1 python - < features/.../M2_normalize/check_assembler.py
"""

from __future__ import annotations

import io
import subprocess
import tempfile
import wave
from pathlib import Path

from sketch2life.application.video_pipeline.age_profile import profile_for_age_months
from sketch2life.application.video_pipeline.caption_plan import Cue
from sketch2life.application.video_pipeline.ports import AssembleJob, PlacedChunk, SceneClip
from sketch2life.application.video_pipeline.story_timeline import parse_timeline
from sketch2life.application.video_pipeline.timeline_planner import assign_timing
from sketch2life.application.video_pipeline.video_plan import build_video_plan
from sketch2life.infrastructure.story_video.ffmpeg_assembler import FfmpegAssembler
from sketch2life.infrastructure.story_video.technical_validator import TechnicalVideoValidator


def clip(frames: int) -> bytes:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "clip.mp4"
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc2=size=1280x720:rate=24",
             "-frames:v", str(frames), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path)],
            check=True,
        )
        return path.read_bytes()


def tone(milliseconds: int) -> bytes:
    output = io.BytesIO()
    with wave.open(output, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(24_000)
        handle.writeframes(b"\x10\x10" * (24 * milliseconds))
    return output.getvalue()


for age in (48, 84, 114):
    profile = profile_for_age_months(age)
    scenes = [
        {"title": f"Cảnh {i}", "action": "Rùa đi.", "visual_prompt": "A turtle walks, crayon style.",
         "background_prompt": "A sunny garden, crayon texture.", "narration": "Rùa con bò đi.", "dialogue": [],
         "subjects": ["main"], "interactions": []}
        for i in range(1, profile.scene_count + 1)
    ]
    timeline = parse_timeline(
        assign_timing(profile, {"title": "Rùa con", "scenes": scenes}), profile=profile, entity_ids={"main"}
    )
    plan = build_video_plan(timeline, story_sha256="a" * 64, main_entity_id="main")
    job = AssembleJob(
        plan=plan,
        clips=[SceneClip(s.index, clip(s.target_frames), s.target_frames) for s in plan.scenes],
        chunks=[PlacedChunk(500, tone(2_000), 0, 0, 2_000)],
        cues=[Cue(0, 1_000, "Rùa con bò đi.", "narration")],
    )
    video = FfmpegAssembler().assemble(job)
    report = TechnicalVideoValidator().validate(video, plan)
    print("age", age, "scenes", len(plan.scenes), "seconds", plan.total_frames / 24, "bytes", len(video),
          "technical_ok", report.technical_ok, report.finding_codes)
