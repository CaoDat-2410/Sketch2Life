"""CPU check on the deployed inference image: normalise a generated test clip and validate it (FEAT-094).

    modal run -e dev features/FEAT-094-learning-video-redesign/evidence/M2_normalize/check_normalize.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import modal

WORKERS = Path(__file__).resolve().parents[4] / "deployment" / "modal" / "srs_v23" if modal.is_local() else Path("/root")
app = modal.App("sketch2life-feat094-normalize-check")

if modal.is_local():
    sys.path.insert(0, str(WORKERS))
    import video_app

    IMAGE = video_app._with_runtime_modules(video_app._inference_image).add_local_file(str(WORKERS / "video_app.py"), "/root/video_app.py")
else:
    IMAGE = None


@app.function(image=IMAGE, cpu=2.0, timeout=600)
def check(durations: list[float]) -> list[dict[str, Any]]:
    import subprocess
    import tempfile

    import video_app as worker
    from story_visual_plan import plan_scene_frames

    version = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True).stdout.splitlines()[0]
    results: list[dict[str, Any]] = [{"ffmpeg": version}]
    with tempfile.TemporaryDirectory() as directory:
        work = Path(directory)
        for seconds in durations:
            plan = plan_scene_frames(seconds)
            frames = int(plan["generated_frame_count"])
            raw, clip = work / "raw.mp4", work / "clip.mp4"
            subprocess.run(
                ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc2=size=1280x768:rate=24",
                 "-frames:v", str(frames), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(raw)],
                check=True,
            )
            worker._normalize_silent_clip(raw, clip, target_duration=seconds, generated_frame_count=frames)
            probe = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=avg_frame_rate,nb_frames",
                 "-of", "compact", str(clip)], capture_output=True, text=True,
            ).stdout.split()
            try:
                worker._validate_scene_file(clip, seconds, expected_frame_count=int(plan["target_frame_count"]))
                outcome = "VALID"
            except RuntimeError as error:
                outcome = str(error)
            results.append({"seconds": seconds, "generated": frames, "probe": probe, "outcome": outcome})
    return results


@app.local_entrypoint()
def main() -> None:
    # Exact, shorter and longer than the generated 8k+1 frame count.
    for line in check.remote([1.0, 6.0, 148 / 24, 10.0, 250 / 24, 19.5]):
        print("RESULT", line)
