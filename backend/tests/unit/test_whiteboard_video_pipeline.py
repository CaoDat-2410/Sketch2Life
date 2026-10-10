from sketch2life.application.services.whiteboard_video_pipeline import (
    EncodedWhiteboard,
    LocalizedRegionBatch,
    MaskBatch,
    RenderedWhiteboard,
    StrokeBatch,
    TtsTrack,
    WhiteboardVideoPipeline,
    WhiteboardVideoStageError,
)
from sketch2life.application.services.whiteboard_video_job import (
    WhiteboardVideoJobService,
    WhiteboardVideoPipelineError,
)

from test_whiteboard_video_job import HASH, SuccessfulPipeline, make_job, make_service


class FixtureLocalizer:
    def localize(self, job):
        return LocalizedRegionBatch(job.source_hash, ("region-001",))


class FixtureSegmenter:
    def segment(self, job, regions):
        return MaskBatch(regions.source_hash, ("mask-001",))


class FixtureStrokeExtractor:
    def extract(self, job, masks):
        return StrokeBatch(masks.source_hash, ("stroke-001",))


class FixtureRenderer:
    def render(self, job, strokes):
        return RenderedWhiteboard(strokes.source_hash, "render-001")


class FixtureTts:
    def synthesize(self, job):
        return TtsTrack(job.source_hash, "tts-001")


class FixtureEncoder:
    def encode(self, job, render, tts):
        return EncodedWhiteboard(
            source_hash=render.source_hash,
            video_artifact_id="video-001",
            mp4_ref="video/whiteboard.mp4",
            duration_seconds=8,
            codec="H264_AVC_HIGH_L4_1",
            size_bytes=4_000_000,
        )


class FixtureSafetyValidator:
    def validate(self, job, regions, masks, strokes, render, tts, encoded):
        assert encoded.source_hash == job.source_hash


def make_pipeline() -> WhiteboardVideoPipeline:
    return WhiteboardVideoPipeline(
        localizer=FixtureLocalizer(),
        segmenter=FixtureSegmenter(),
        stroke_extractor=FixtureStrokeExtractor(),
        renderer=FixtureRenderer(),
        tts=FixtureTts(),
        encoder=FixtureEncoder(),
        safety_validator=FixtureSafetyValidator(),
    )


def test_composed_pipeline_produces_ready_result() -> None:
    pipeline = make_pipeline()
    service = WhiteboardVideoJobService(pipeline=pipeline)
    job = make_job(service)

    result = service.run(job.job_id)

    assert result.status == "READY"
    assert result.mask_refs == ("mask-001",)
    assert result.stroke_refs == ("stroke-001",)
    assert result.tts_ref == "tts-001"


def test_composed_pipeline_rejects_provenance_drift() -> None:
    class BadSegmenter(FixtureSegmenter):
        def segment(self, job, regions):
            return MaskBatch("b" * 64, ("mask-001",))

    pipeline = WhiteboardVideoPipeline(
        localizer=FixtureLocalizer(),
        segmenter=BadSegmenter(),
        stroke_extractor=FixtureStrokeExtractor(),
        renderer=FixtureRenderer(),
        tts=FixtureTts(),
        encoder=FixtureEncoder(),
        safety_validator=FixtureSafetyValidator(),
    )
    service = WhiteboardVideoJobService(pipeline=pipeline)
    job = make_job(service)

    try:
        service.run(job.job_id)
    except WhiteboardVideoPipelineError as error:
        assert error.code == "SOURCE_HASH_MISMATCH"
        assert error.retryable is False
    else:
        raise AssertionError("provenance drift must fail closed")

    assert service.store.get(job.job_id).status == "FAILED"
