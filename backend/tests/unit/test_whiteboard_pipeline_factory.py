from __future__ import annotations

from pathlib import Path

from sketch2life.infrastructure.media.whiteboard_pipeline_factory import (
    build_lightning_whiteboard_mvp_pipeline,
    build_whiteboard_mvp_pipeline,
)
from sketch2life.infrastructure.storage.in_memory import InMemoryArtifactStore


class Localizer:
    def localize(self, job):
        from sketch2life.application.services.whiteboard_video_pipeline import LocalizedRegionBatch

        return LocalizedRegionBatch(job.source_hash, ("region-1",))


def test_factory_builds_all_mvp_stage_adapters() -> None:
    pipeline = build_whiteboard_mvp_pipeline(
        localizer=Localizer(),
        mask_path_for=lambda ref: Path(ref),
        stroke_output_path_for=lambda job_id: f"{job_id}.json",
        cutout_path_for=lambda ref: Path(ref),
        render_output_path_for=lambda job_id: f"{job_id}.render.mp4",
        script_for=lambda _: "script",
        synthesize_tts=lambda _script, _path: None,
        tts_output_path_for=lambda job_id: f"{job_id}.wav",
        encode_mp4=lambda _render, _tts, _output: None,
        inspect_mp4=lambda _path: (8.0, "H264_AVC_HIGH_L4_1", 100),
        mp4_output_path_for=lambda job_id: f"{job_id}.mp4",
        artifact_exists=lambda _: True,
    )

    assert pipeline.__class__.__name__ == "WhiteboardVideoPipeline"


class JsonTransport:
    def post_json(self, _path, _payload):
        return {}


def test_lightning_factory_builds_provider_backed_stage_graph(tmp_path) -> None:
    pipeline = build_lightning_whiteboard_mvp_pipeline(
        transport=JsonTransport(),
        artifacts=InMemoryArtifactStore(),
        artifact_root=tmp_path,
        script_for=lambda _: "script",
        synthesize_tts=lambda _script, _path: None,
        encode_mp4=lambda _render, _tts, _output: None,
        inspect_mp4=lambda _path: (8.0, "H264_AVC_HIGH_L4_1", 100),
    )

    assert pipeline.__class__.__name__ == "WhiteboardVideoPipeline"
