"""Run the real video pipeline on the newest synthetic generation, without writing business state (FEAT-094 phase 2).

    docker exec -i sketch2life-video-worker-1 python - < features/.../M4_two_containers/check_pipeline.py

Reads the confirmed synthetic story and drawing, runs planning, preparation, rendering, narration and assembly on Modal,
writes ``/tmp/feat094-check.mp4`` and prints the time of every stage.
"""

from __future__ import annotations

import time

from sqlalchemy import text

from sketch2life.application.ports.story_video import VideoRenderRequest
from sketch2life.infrastructure.config.settings import get_settings
from sketch2life.infrastructure.persistence.database import create_core_engine, create_core_session_factory
from sketch2life.infrastructure.storage.s3_compatible import Boto3S3CompatibleObjectStorage
from sketch2life.infrastructure.story_video.sql_source_reader import SqlVideoSourceReader
from sketch2life.infrastructure.story_video.video_worker import build_modal_pipeline

settings = get_settings()
storage = Boto3S3CompatibleObjectStorage(
    bucket=settings.s3_bucket,
    endpoint_url=settings.s3_endpoint,
    region_name=settings.s3_region,
    access_key=settings.s3_access_key.get_secret_value() if settings.s3_access_key else None,
    secret_key=settings.s3_secret_key.get_secret_value() if settings.s3_secret_key else None,
)
sessions = create_core_session_factory(create_core_engine())
with sessions() as session:
    row = session.execute(
        text(
            "select video_generation_id, story_run_id, story_revision_id from story.video_generations "
            "where state = 'READY' order by created_at desc limit 1"
        )
    ).one()
request = VideoRenderRequest(str(row[0]), str(row[1]), str(row[2]), "", 5, "feat094-check")
source = SqlVideoSourceReader(sessions, storage).read(request)
assert source is not None, "no readable source"

started = time.monotonic()


def progress(stage: str, scene: int | None, count: int) -> None:
    print(f"STAGE {time.monotonic() - started:7.1f}s {stage} {scene or ''}/{count}", flush=True)


result = build_modal_pipeline().run(source, progress=progress)
print(f"DONE {time.monotonic() - started:.1f}s bytes={len(result.video)} backgrounds={result.backgrounds}", flush=True)
print("CAPTIONS", result.captions_vtt.replace("\n", " | "), flush=True)
with open("/tmp/feat094-check.mp4", "wb") as handle:
    handle.write(result.video)
