"""FEAT-098 part C: one batched L40S measurement of the scene renderer, same keyframe, prompt and seed.

Ephemeral Modal app; it deploys nothing and reads only the synthetic keyframe sent in the call. Two containers run side by
side: ``base`` on an image without ``natten`` (as before FEAT-098) and the others on the new image. From the repository
root, after ``download-ltx25-conv-vae`` has staged the convolution VAE:

    modal run -e dev features/FEAT-098-video-narration-and-speed/evidence/benchmark/render_bench.py --out <directory>
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

import modal

REPOSITORY = Path(__file__).resolve().parents[4] if modal.is_local() else Path("/root")
WORKERS = REPOSITORY / "deployment" / "modal" / "srs_v23"
KEYFRAME = "features/FEAT-094-learning-video-redesign/evidence/M1_experiments/inputs/chick_start.png"
# The 10 s scene of the FEAT-094 speed measurement.
PROMPT = (
    "The yellow crayon chick hops forward once and dips its beak down toward the grass, then lifts its head, its three "
    "tail feathers swaying. The movement is smooth and continuous from the first moment to the last. The drawing keeps "
    "its crayon strokes, colours and paper texture exactly as in the first frame. The camera remains static throughout."
)
SEED = 940101
SECONDS = 10.0
REPEATS = 2
NEW_VARIANTS = [("natten", ""), ("conv_vae", "conv_vae"), ("small", "small"), ("fps16", "fps16")]

app = modal.App("sketch2life-feat098-render-bench")
model_volume = modal.Volume.from_name("sketch2life-dev-model-weights-v2", environment_name="dev", version=2)

if modal.is_local():
    sys.path.insert(0, str(WORKERS))
    import video_app

    def _image(image: Any) -> Any:
        return video_app._with_runtime_modules(image).add_local_file(str(WORKERS / "video_app.py"), "/root/video_app.py")

    NEW_IMAGE = _image(video_app._inference_image)
    OLD_IMAGE = _image(
        video_app._inference_image.run_commands("uv pip uninstall --python /opt/LTX-2/.venv/bin/python natten")
    )
else:
    NEW_IMAGE = OLD_IMAGE = None


def _measure(variants: list[tuple[str, str]], keyframe: bytes) -> dict[str, Any]:
    import tempfile
    import traceback

    import render_options
    import torch
    import video_app as worker
    from ltx_speed import ProfileSwitch

    report: dict[str, Any] = {"gpu": torch.cuda.get_device_name(0), "variants": []}
    try:
        import natten

        report["natten"] = str(getattr(natten, "__version__", "installed"))
    except ImportError:
        report["natten"] = None

    def timed(record: dict[str, Any], name: str, call: Any) -> Any:
        torch.cuda.synchronize()
        started = time.perf_counter()
        result = call()
        torch.cuda.synchronize()
        record[name] = round(time.perf_counter() - started, 1)
        return result

    with tempfile.TemporaryDirectory() as directory:
        work = Path(directory)
        start = work / "keyframe.png"
        start.write_bytes(keyframe)
        for name, options in variants:
            record: dict[str, Any] = {"name": name, "options": options, "renders": []}
            report["variants"].append(record)
            try:
                worker._OPTIONS = render_options.parse_options(options)
                worker._PROFILES = ProfileSwitch()
                worker._unload_pipeline()
                # Later variants find the files in the page cache, except the VAE a variant swaps in.
                if len(report["variants"]) == 1 or worker._OPTIONS.conv_vae:
                    timed(record, "read_checkpoints_s", worker._read_checkpoints)
                pipeline = timed(record, "load_s", worker._load_pipeline)
                with torch.inference_mode():
                    timed(record, "prompt_s", lambda: pipeline.prompt_encoder.prepare([PROMPT]))
                timed(record, "compile_s", worker._compile_decoder)
                del pipeline  # a fall back must be able to free it
                for index in range(1, REPEATS + 1):
                    run: dict[str, Any] = {}
                    record["renders"].append(run)
                    raw, clip = work / f"{name}-{index}-raw.mp4", work / f"{name}-{index}.mp4"
                    torch.cuda.reset_peak_memory_stats()
                    plan = timed(
                        run,
                        "render_s",
                        lambda: worker._render_scene(
                            image_path=start,
                            output_path=raw,
                            visual_prompt=PROMPT,
                            seed=SEED,
                            target_duration=SECONDS,
                            prompt_is_compiled=True,
                        ),
                    )
                    timed(
                        run,
                        "normalize_s",
                        lambda: worker._normalize_silent_clip(
                            raw,
                            clip,
                            target_duration=SECONDS,
                            generated_frame_count=int(plan["generated_frame_count"]),
                        ),
                    )
                    worker._validate_scene_file(clip, SECONDS)
                    run["frames_generated"] = plan["generated_frame_count"]
                    run["peak_gpu_gb"] = round(torch.cuda.max_memory_allocated(0) / 1024**3, 1)
                    run["video"] = clip.read_bytes()
                record["speed_profile"] = worker._PROFILES.current
                print(
                    json.dumps({**record, "renders": [{k: v for k, v in r.items() if k != "video"} for r in record["renders"]]}),
                    flush=True,
                )
            except Exception as error:  # a measurement records the failure and goes on
                record["error"] = f"{type(error).__name__}: {error}"[:600]
                print(traceback.format_exc(), flush=True)
    return report


_RESOURCES: dict[str, Any] = {
    "gpu": "L40S",
    "cpu": 8.0,
    "memory": 65_536,
    "volumes": {"/models": model_volume.with_mount_options(read_only=True)},
    "max_containers": 1,
    "scaledown_window": 2,
    "timeout": 1_800,
    "retries": 0,
}


@app.function(image=OLD_IMAGE, **_RESOURCES)
def measure_base(keyframe: bytes) -> dict[str, Any]:
    return _measure([("base", "")], keyframe)


@app.function(image=NEW_IMAGE, **_RESOURCES)
def measure_new(variants: list[tuple[str, str]], keyframe: bytes) -> dict[str, Any]:
    return _measure(variants, keyframe)


@app.local_entrypoint()
def main(out: str, only: str = "") -> None:
    """``only`` limits the run to a comma separated list of variant names."""

    wanted = {name for name in only.split(",") if name}
    keyframe = (REPOSITORY / KEYFRAME).read_bytes()
    calls = []
    if not wanted or "base" in wanted:
        calls.append(("base_image", measure_base.spawn(keyframe)))
    variants = [item for item in NEW_VARIANTS if not wanted or item[0] in wanted]
    if variants:
        calls.append(("new_image", measure_new.spawn(variants, keyframe)))
    target = Path(out)
    target.mkdir(parents=True, exist_ok=True)
    reports: dict[str, Any] = {"keyframe": KEYFRAME, "seed": SEED, "seconds": SECONDS}
    for name, call in calls:
        report = call.get()
        for record in report["variants"]:
            for index, run in enumerate(record["renders"], start=1):
                video = run.pop("video", None)
                if video:
                    (target / f"{record['name']}-{index}.mp4").write_bytes(video)
        reports[name] = report
        (target / "report.json").write_text(json.dumps(reports, indent=2), encoding="utf-8")
    print(json.dumps(reports))
