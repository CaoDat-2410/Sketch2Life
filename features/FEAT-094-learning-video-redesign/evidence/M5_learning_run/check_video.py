"""Render the video of the generated learning script on Modal, without writing business state (FEAT-094 phases 4, 5).

    docker exec -i sketch2life-video-worker-1 python -u - < features/.../M5_learning_run/check_video.py

Uses the drawing and subject boxes of the newest synthetic generation and the script saved by ``check_story.py``.
The visual check runs in report mode. Writes ``/tmp/feat094-learning.mp4``.
"""

from __future__ import annotations

import json
import time
from dataclasses import replace

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
base = SqlVideoSourceReader(sessions, storage).read(
    VideoRenderRequest(str(row[0]), str(row[1]), str(row[2]), "", 5, "feat094-learning")
)
assert base is not None, "no readable source"
with open("/tmp/feat094-story.json", encoding="utf-8") as handle:
    saved = json.load(handle)
story, learning = saved["story"], saved["learning"]
source = replace(
    base,
    story={"title": story["title"], **story["story"]},
    learning={
        "title": story["title"],
        "scenes": [
            {**plan, "title": scene["title"], "narration": scene["narration"]}
            for plan, scene in zip(learning["scenes"], story["scenes"], strict=True)
        ],
    },
)

started = time.monotonic()


def progress(stage: str, scene: int | None, count: int) -> None:
    print(f"STAGE {time.monotonic() - started:7.1f}s {stage} {scene or ''}/{count}", flush=True)


result = build_modal_pipeline("report").run(source, progress=progress)
print(f"DONE {time.monotonic() - started:.1f}s bytes={len(result.video)} backgrounds={result.backgrounds}", flush=True)
print("FINDINGS", dict(result.findings), flush=True)
print("PLAN_MS", result.plan.total_ms, "holds", [scene.hold_frames for scene in result.plan.scenes], flush=True)
print("CAPTIONS", result.captions_vtt.replace("\n", " | "), flush=True)
with open("/tmp/feat094-learning.mp4", "wb") as handle:
    handle.write(result.video)
