"""Run the deployed visual check on the ten scenes of the two earlier learning videos (FEAT-094).

    docker cp ../M5_learning_run/learning_run1.mp4 sketch2life-video-worker-1:/tmp/
    docker cp ../M5_learning_run/learning_run2.mp4 sketch2life-video-worker-1:/tmp/
    docker cp learning_run3.mp4 sketch2life-video-worker-1:/tmp/
    docker exec -i sketch2life-video-worker-1 python -u - < check_saved_scenes.py

Calls the Qwen worker once per scene (no video GPU). Writes no business state. Seen by eye in sampled frames before this
run: a hand in run 1 scene 4 and run 2 scene 5, dogs in the background of run 1 scene 5, a blue smear in run 2 scene 3;
run 2 scene 2 (pecking) is correct.
"""

from __future__ import annotations

import os
import subprocess
import time

from sqlalchemy import text

from sketch2life.application.ports.story_video import VideoRenderRequest
from sketch2life.application.video_pipeline.ports import SceneClip
from sketch2life.infrastructure.config.settings import get_settings
from sketch2life.infrastructure.persistence.database import create_core_engine, create_core_session_factory
from sketch2life.infrastructure.storage.s3_compatible import Boto3S3CompatibleObjectStorage
from sketch2life.infrastructure.story_video.modal_scene_check import ModalSceneCheck, clip_edge_changed
from sketch2life.infrastructure.story_video.sql_source_reader import SqlVideoSourceReader


def _storage() -> Boto3S3CompatibleObjectStorage:
    settings = get_settings()
    return Boto3S3CompatibleObjectStorage(
        bucket=settings.s3_bucket,
        endpoint_url=settings.s3_endpoint,
        region_name=settings.s3_region,
        access_key=settings.s3_access_key.get_secret_value() if settings.s3_access_key else None,
        secret_key=settings.s3_secret_key.get_secret_value() if settings.s3_secret_key else None,
    )


check = ModalSceneCheck()
for run in (1, 2):
    for scene in range(1, 6):
        target = f"/tmp/r{run}s{scene}.mp4"
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-ss", str((scene - 1) * 10), "-t", "10", "-i",
             f"/tmp/learning_run{run}.mp4", "-an", "-c:v", "libx264", "-crf", "18", target],
            check=True,
        )
        first = subprocess.run(
            ["ffmpeg", "-loglevel", "error", "-i", target, "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png",
             "pipe:1"],
            capture_output=True,
            check=True,
        ).stdout
        with open(target, "rb") as handle:
            clip = handle.read()
        started = time.monotonic()
        found = check.check(SceneClip(scene, clip, 240), first)
        print(
            f"run {run} scene {scene} edge={clip_edge_changed(clip)} found={list(found)} "
            f"{time.monotonic() - started:.1f}s",
            flush=True,
        )

# The first frames of live run 3 against the drawing: scene 2 has a second, painted hen behind the child's chick.
if os.path.exists("/tmp/learning_run3.mp4"):
    sessions = create_core_session_factory(create_core_engine())
    with sessions() as session:
        row = session.execute(
            text(
                "select video_generation_id, story_run_id, story_revision_id from story.video_generations "
                "where state = 'READY' order by created_at desc limit 1"
            )
        ).one()
    source = SqlVideoSourceReader(sessions, _storage()).read(
        VideoRenderRequest(str(row[0]), str(row[1]), str(row[2]), "", 5, "feat094-learning")
    )
    assert source is not None, "no readable source"
    for scene in range(1, 6):
        frame = subprocess.run(
            ["ffmpeg", "-loglevel", "error", "-ss", str((scene - 1) * 10), "-i", "/tmp/learning_run3.mp4",
             "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "pipe:1"],
            capture_output=True,
            check=True,
        ).stdout
        print(f"run 3 first frame {scene} found={list(check.check_keyframe(source.drawing_png, frame))}", flush=True)
