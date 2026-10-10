"""Provider-neutral whiteboard pipeline boundary for FEAT-018."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from sketch2life.application.services.whiteboard_video_job import (
    WhiteboardVideoPipelineError,
)
from sketch2life.contracts.schemas.whiteboard_video import (
    WhiteboardVideoJobV1,
    WhiteboardVideoResultV1,
)


class WhiteboardVideoStageError(RuntimeError):
    """Typed stage failure that is safe to map to the job contract."""

    def __init__(self, code: str, *, retryable: bool) -> None:
        super().__init__(code)
        self.code = code
        self.retryable = retryable


@dataclass(frozen=True)
class LocalizedRegionBatch:
    source_hash: str
    region_refs: tuple[str, ...]


@dataclass(frozen=True)
class MaskBatch:
    source_hash: str
    mask_refs: tuple[str, ...]


@dataclass(frozen=True)
class StrokeBatch:
    source_hash: str
    stroke_refs: tuple[str, ...]


@dataclass(frozen=True)
class RenderedWhiteboard:
    source_hash: str
    render_ref: str


@dataclass(frozen=True)
class TtsTrack:
    source_hash: str
    tts_ref: str


@dataclass(frozen=True)
class EncodedWhiteboard:
    source_hash: str
    video_artifact_id: str
    mp4_ref: str
    duration_seconds: float
    codec: str
    size_bytes: int


class LocalizerPort(Protocol):
    def localize(self, job: WhiteboardVideoJobV1) -> LocalizedRegionBatch: ...


class SegmenterPort(Protocol):
    def segment(
        self, job: WhiteboardVideoJobV1, regions: LocalizedRegionBatch
    ) -> MaskBatch: ...


class StrokeExtractorPort(Protocol):
    def extract(self, job: WhiteboardVideoJobV1, masks: MaskBatch) -> StrokeBatch: ...


class WhiteboardRendererPort(Protocol):
    def render(self, job: WhiteboardVideoJobV1, strokes: StrokeBatch) -> RenderedWhiteboard: ...


class TtsPort(Protocol):
    def synthesize(self, job: WhiteboardVideoJobV1) -> TtsTrack: ...


class Mp4EncoderPort(Protocol):
    def encode(
        self,
        job: WhiteboardVideoJobV1,
        render: RenderedWhiteboard,
        tts: TtsTrack,
    ) -> EncodedWhiteboard: ...


class WhiteboardSafetyValidatorPort(Protocol):
    def validate(
        self,
        job: WhiteboardVideoJobV1,
        regions: LocalizedRegionBatch,
        masks: MaskBatch,
        strokes: StrokeBatch,
        render: RenderedWhiteboard,
        tts: TtsTrack,
        encoded: EncodedWhiteboard,
    ) -> None: ...


class WhiteboardVideoPipeline:
    """Compose stage adapters while preserving the original source identity."""

    def __init__(
        self,
        *,
        localizer: LocalizerPort,
        segmenter: SegmenterPort,
        stroke_extractor: StrokeExtractorPort,
        renderer: WhiteboardRendererPort,
        tts: TtsPort,
        encoder: Mp4EncoderPort,
        safety_validator: WhiteboardSafetyValidatorPort,
    ) -> None:
        self._localizer = localizer
        self._segmenter = segmenter
        self._stroke_extractor = stroke_extractor
        self._renderer = renderer
        self._tts = tts
        self._encoder = encoder
        self._safety_validator = safety_validator

    def run(self, job: WhiteboardVideoJobV1, update_stage) -> WhiteboardVideoResultV1:
        try:
            update_stage("LOCALIZING", 15)
            regions = self._localizer.localize(job)
            self._check_hash(job, regions.source_hash)

            update_stage("SEGMENTING", 35)
            masks = self._segmenter.segment(job, regions)
            self._check_hash(job, masks.source_hash)

            update_stage("EXTRACTING_STROKES", 55)
            strokes = self._stroke_extractor.extract(job, masks)
            self._check_hash(job, strokes.source_hash)

            update_stage("RENDERING", 70)
            render = self._renderer.render(job, strokes)
            self._check_hash(job, render.source_hash)

            tts = self._tts.synthesize(job)
            self._check_hash(job, tts.source_hash)

            update_stage("ENCODING", 90)
            encoded = self._encoder.encode(job, render, tts)
            self._check_hash(job, encoded.source_hash)
            self._safety_validator.validate(job, regions, masks, strokes, render, tts, encoded)

            return WhiteboardVideoResultV1(
                job_id=job.job_id,
                video_artifact_id=encoded.video_artifact_id,
                mp4_ref=encoded.mp4_ref,
                mask_refs=masks.mask_refs,
                stroke_refs=strokes.stroke_refs,
                tts_ref=tts.tts_ref,
                source_hash=job.source_hash,
                experience_spec_id=job.experience_spec_id,
                learning_thread_ref=job.learning_thread_ref,
                duration_seconds=encoded.duration_seconds,
                codec="H264_AVC_HIGH_L4_1",
                size_bytes=encoded.size_bytes,
            )
        except WhiteboardVideoStageError as error:
            raise WhiteboardVideoPipelineError(error.code, retryable=error.retryable) from error

    @staticmethod
    def _check_hash(job: WhiteboardVideoJobV1, source_hash: str) -> None:
        if source_hash != job.source_hash:
            raise WhiteboardVideoStageError("SOURCE_HASH_MISMATCH", retryable=False)


__all__ = [
    "EncodedWhiteboard",
    "LocalizedRegionBatch",
    "LocalizerPort",
    "MaskBatch",
    "Mp4EncoderPort",
    "RenderedWhiteboard",
    "SegmenterPort",
    "StrokeBatch",
    "StrokeExtractorPort",
    "TtsPort",
    "TtsTrack",
    "WhiteboardRendererPort",
    "WhiteboardSafetyValidatorPort",
    "WhiteboardVideoPipeline",
    "WhiteboardVideoStageError",
]
