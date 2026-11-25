"""FEAT-093: the assembler builds frame-exact commands (fake runner; ffmpeg itself runs in the live check)."""

from __future__ import annotations

from pathlib import Path

import pytest

from sketch2life.application.video_pipeline.age_profile import profile_for_age_months
from sketch2life.application.video_pipeline.caption_plan import Cue
from sketch2life.application.video_pipeline.ports import (
    AssembleJob,
    PlacedChunk,
    SceneClip,
    VideoPipelineError,
)
from sketch2life.application.video_pipeline.story_timeline import parse_timeline
from sketch2life.application.video_pipeline.timeline_planner import assign_timing
from sketch2life.application.video_pipeline.video_plan import apply_stretches, build_video_plan
from sketch2life.infrastructure.story_video.ffmpeg_assembler import FfmpegAssembler


def _plan():
    profile = profile_for_age_months(48)
    scenes = [
        {"title": f"Cảnh {i}", "action": "Rùa đi.", "visual_prompt": "A turtle walks, crayon style.",
         "background_prompt": "A sunny garden, crayon texture.", "narration": "Rùa con bò đi.", "dialogue": [],
         "subjects": ["main"], "interactions": []}
        for i in range(1, 6)
    ]
    timeline = parse_timeline(
        assign_timing(profile, {"title": "Rùa con", "scenes": scenes}), profile=profile, entity_ids={"main"}
    )
    return build_video_plan(timeline, story_sha256="a" * 64, main_entity_id="main")


class _Runner:
    def __init__(self, fail=False, skip_output=False):
        self.commands: list[list[str]] = []
        self.fail, self.skip_output = fail, skip_output

    def __call__(self, command):
        self.commands.append(list(command))
        if self.fail:
            raise VideoPipelineError("VIDEO_ASSEMBLE_FFMPEG_FAILED")
        if command[-1].endswith("final.mp4"):
            if not self.skip_output:
                Path(command[-1]).write_bytes(b"FINAL")
        elif command[-1].endswith(".mp4"):
            Path(command[-1]).write_bytes(b"x")


def _job(plan, chunks=None):
    clips = [SceneClip(s.index, b"clip", s.model_frames) for s in plan.scenes]
    chunks = chunks if chunks is not None else [PlacedChunk(500, b"RIFFwav", 40, 30, 2_000)]
    return AssembleJob(plan=plan, clips=clips, chunks=chunks, cues=[Cue(0, 1000, "Rùa con bò đi.", "narration")])


def test_scene_clips_are_cut_to_planned_frames_and_held() -> None:
    plan = _plan()
    runner = _Runner()

    assert FfmpegAssembler(runner=runner).assemble(_job(plan)) == b"FINAL"

    scene_commands = [c for c in runner.commands if c[-1].endswith(tuple(f"scene-{i}.mp4" for i in range(1, 6)))]
    assert len(scene_commands) == 5
    first = scene_commands[0]
    assert f"trim=end_frame={plan.scenes[0].target_frames}" in first[first.index("-vf") + 1]
    assert "libx264" in first and "-an" in first


def test_a_hold_extends_the_scene_by_cloning_the_last_frame() -> None:
    plan = apply_stretches(_plan(), {1: 36})
    held = next(s for s in plan.scenes if s.hold_frames > 0)
    runner = _Runner()

    FfmpegAssembler(runner=runner).assemble(_job(plan))

    command = next(c for c in runner.commands if c[-1].endswith(f"scene-{held.index}.mp4"))
    assert f"tpad=stop_mode=clone:stop={held.hold_frames}" in command[command.index("-vf") + 1]


def test_the_narration_is_trimmed_placed_normalised_and_faststart() -> None:
    plan = _plan()
    runner = _Runner()

    FfmpegAssembler(runner=runner).assemble(_job(plan))

    mux = runner.commands[-1]
    graph = mux[mux.index("-filter_complex") + 1]
    assert "atrim=start=0.040:duration=2.000" in graph and "adelay=500:all=1" in graph
    assert "loudnorm=I=-16" in graph and f"whole_dur={plan.total_frames / 24:.3f}" in graph
    assert mux[mux.index("-movflags") + 1] == "+faststart" and mux[mux.index("-t") + 1] == f"{plan.total_frames / 24:.3f}"
    assert "copy" in mux and "aac" in mux


def test_missing_clips_missing_narration_and_ffmpeg_failures_are_reported() -> None:
    plan = _plan()
    job = _job(plan)
    incomplete = AssembleJob(plan=plan, clips=job.clips[:-1], chunks=job.chunks, cues=job.cues)
    for assembler, bad, code in (
        (FfmpegAssembler(runner=_Runner()), incomplete, "VIDEO_ASSEMBLE_CLIPS_INCOMPLETE"),
        (FfmpegAssembler(runner=_Runner()), _job(plan, chunks=[]), "VIDEO_ASSEMBLE_NO_NARRATION"),
        (FfmpegAssembler(runner=_Runner(fail=True)), job, "VIDEO_ASSEMBLE_FFMPEG_FAILED"),
        (FfmpegAssembler(runner=_Runner(skip_output=True)), job, "VIDEO_ASSEMBLE_OUTPUT_MISSING"),
    ):
        with pytest.raises(VideoPipelineError) as error:
            assembler.assemble(bad)
        assert error.value.code == code
