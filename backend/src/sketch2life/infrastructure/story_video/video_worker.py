"""The Parent video worker process (FEAT-093): ``python -m sketch2life.infrastructure.story_video.video_worker``.

It owns no business state. Each pass lists accepted generations from PostgreSQL and advances them with the existing
``FixtureVideoRunner`` state machine, whose render step is the real pipeline behind ``PipelineVideoRenderer``. Progress
and captions go to ``story.video_generation_progress``. A generation whose run was cancelled (state no longer
``GENERATING``) stops the pipeline between scenes. One worker at a time holds a PostgreSQL advisory lock for its whole
life, so a second copy idles instead of rendering the same video twice; a crash is recovered by the next start, which
resumes generations still in ``GENERATING``.
"""

from __future__ import annotations

import argparse
import logging
import signal
import sys
import threading
from collections.abc import Callable, Sequence
from contextlib import suppress
from types import FrameType
from typing import Any

from sqlalchemy import Engine, text
from sqlalchemy.orm import Session, sessionmaker

from sketch2life.application.ports.object_storage import ObjectStoragePort
from sketch2life.application.ports.story_video import StoryVideoAdapters, VideoRenderRequest
from sketch2life.application.video_pipeline.orchestrator import VideoPipeline
from sketch2life.application.video_pipeline.ports import PipelineResult
from sketch2life.domain.story_video.model import GenerationState
from sketch2life.infrastructure.config.settings import Settings, get_settings
from sketch2life.infrastructure.persistence.database import create_core_engine, create_core_session_factory
from sketch2life.infrastructure.story_video.composition import build_story_video_adapters
from sketch2life.infrastructure.story_video.ffmpeg_assembler import FfmpegAssembler
from sketch2life.infrastructure.story_video.fixture_runner import FixtureVideoRunner
from sketch2life.infrastructure.story_video.modal_narration import ModalNarrationSynthesizer
from sketch2life.infrastructure.story_video.modal_scene_check import ModalSceneCheck
from sketch2life.infrastructure.story_video.modal_scene_preparation import ModalScenePreparation
from sketch2life.infrastructure.story_video.modal_scene_renderer import ModalSceneRenderer
from sketch2life.infrastructure.story_video.modal_timeline import ModalVideoTimelineGenerator
from sketch2life.infrastructure.story_video.pipeline_renderer import PipelineVideoRenderer
from sketch2life.infrastructure.story_video.progress_store import SqlVideoProgressStore
from sketch2life.infrastructure.story_video.repository import SqlStoryVideoRepository
from sketch2life.infrastructure.story_video.sql_source_reader import SqlVideoSourceReader
from sketch2life.infrastructure.story_video.technical_validator import TechnicalVideoValidator

_LOG = logging.getLogger(__name__)
LOCK_NAME = "sketch2life.video-worker.v1"
BATCH = 5


def build_modal_pipeline(check_mode: str = "off") -> VideoPipeline:
    return VideoPipeline(
        scene_check=ModalSceneCheck(),
        check_mode=check_mode,
        timeline_generator=ModalVideoTimelineGenerator(),
        preparation=ModalScenePreparation(),
        renderer=ModalSceneRenderer(),
        narration=ModalNarrationSynthesizer(),
        assembler=FfmpegAssembler(),
        validator=TechnicalVideoValidator(),
    )


def build_runner(
    sessions: sessionmaker[Session],
    storage: ObjectStoragePort,
    adapters: StoryVideoAdapters | None,
    pipeline: VideoPipeline,
) -> FixtureVideoRunner:
    progress = SqlVideoProgressStore(sessions)

    def on_progress(request: VideoRenderRequest, stage: str, scene: int | None, count: int) -> None:
        progress.record(request.generation_id, stage, scene, count)

    def on_result(request: VideoRenderRequest, result: PipelineResult) -> None:
        if result.findings:  # scene numbers and codes only
            _LOG.warning("video_scene_findings generation=%s findings=%s", request.generation_id, dict(result.findings))
        progress.record_captions(request.generation_id, result.captions_vtt, result.cues)

    def is_cancelled(request: VideoRenderRequest) -> bool:
        with sessions() as session:
            record = SqlStoryVideoRepository(session).get_generation(request.generation_id)
        return record is None or GenerationState(record.state) is not GenerationState.GENERATING

    renderer = PipelineVideoRenderer(
        pipeline=pipeline,
        reader=SqlVideoSourceReader(sessions, storage),
        on_progress=on_progress,
        on_result=on_result,
        is_cancelled=is_cancelled,
    )
    return FixtureVideoRunner(sessions, storage, adapters, renderer=renderer)


class VideoWorker:
    def __init__(self, sessions: sessionmaker[Session] | Callable[[], Session], runner: Any) -> None:
        self._sessions = sessions
        self._runner = runner

    def run_once(self, limit: int = BATCH) -> int:
        """Advance every runnable generation to its next settled state; returns how many were handled."""

        with self._sessions() as session:
            records = SqlStoryVideoRepository(session).runnable_generations(limit)
        handled = 0
        for record in records:
            try:
                self._runner.run_to_end(record.generation_id)
            except Exception as error:  # noqa: BLE001 - one bad generation must not stop the others
                _LOG.warning("video_worker_generation_failed kind=%s", type(error).__name__)
            handled += 1
        return handled


def _acquire_lock(engine: Engine) -> Any | None:
    connection = engine.connect().execution_options(isolation_level="AUTOCOMMIT")
    acquired = connection.scalar(text("SELECT pg_try_advisory_lock(hashtextextended(:name, 0))"), {"name": LOCK_NAME})
    if acquired is not True:
        connection.close()
        return None
    return connection


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Parent video worker")
    parser.add_argument("--once", action="store_true", help="one pass and exit")
    parser.add_argument("--interval-seconds", type=int, default=5)
    args = parser.parse_args(argv)
    settings: Settings = get_settings()
    logging.basicConfig(level=settings.log_level.upper(), stream=sys.stdout, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    if settings.story_video_renderer != "modal_dev":
        _LOG.info("video_worker_disabled renderer=%s", settings.story_video_renderer)
        return 0
    from sketch2life.infrastructure.storage.s3_compatible import Boto3S3CompatibleObjectStorage

    engine = create_core_engine()
    lock = _acquire_lock(engine)
    if lock is None:
        _LOG.info("video_worker_idle another worker holds the lock")
        engine.dispose()
        return 0
    try:
        access, secret = settings.s3_access_key, settings.s3_secret_key
        storage = Boto3S3CompatibleObjectStorage(
            bucket=settings.s3_bucket, endpoint_url=settings.s3_endpoint, region_name=settings.s3_region,
            access_key=access.get_secret_value() if access else None,
            secret_key=secret.get_secret_value() if secret else None,
        )
        sessions = create_core_session_factory(engine)
        worker = VideoWorker(
            sessions,
            build_runner(
                sessions,
                storage,
                build_story_video_adapters(settings),
                build_modal_pipeline(settings.story_video_scene_check),
            ),
        )
        if args.once:
            worker.run_once()
            return 0
        stop = threading.Event()

        def request_stop(_signal: int, _frame: FrameType | None) -> Any:
            stop.set()

        signal.signal(signal.SIGTERM, request_stop)
        signal.signal(signal.SIGINT, request_stop)
        while not stop.is_set():
            try:
                worker.run_once()
            except Exception as error:  # noqa: BLE001
                _LOG.warning("video_worker_pass_failed kind=%s", type(error).__name__)
            stop.wait(args.interval_seconds)
        return 0
    finally:
        with suppress(Exception):
            lock.close()
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
