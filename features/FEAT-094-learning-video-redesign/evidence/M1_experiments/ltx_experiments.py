"""FEAT-094 phase 1: LTX-2.5 speed measurement (S0-S3) and quality experiments (E1-E3) on one L40S.

Ephemeral Modal app; it deploys nothing and reads only synthetic inputs sent in the call. Run from the repository root:

    modal run -e dev features/FEAT-094-learning-video-redesign/evidence/M1_experiments/ltx_experiments.py \
        --spec <spec.json> --out <directory>

The spec file names one pipeline profile and the scenes to render with it:
``{"profile": {...}, "scenes": [{"name", "image", "prompt", "seconds", "seed", "end_image", "end_strength", "crf"}]}``.
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

app = modal.App("sketch2life-feat094-ltx-experiments")
model_volume = modal.Volume.from_name("sketch2life-dev-model-weights-v2", environment_name="dev", version=2)

if modal.is_local():
    sys.path.insert(0, str(WORKERS))
    import video_app

    IMAGE = video_app._with_speed_module(video_app._inference_image).add_local_file(str(WORKERS / "video_app.py"), "/root/video_app.py")
else:
    IMAGE = None


class _Timed:
    """Delegate to a pipeline block and record the wall time of every call, with the GPU synchronised."""

    def __init__(self, inner: Any, name: str, log: list[tuple[str, float]]) -> None:
        self._inner, self._name, self._log = inner, name, log

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        import torch

        torch.cuda.synchronize()
        started = time.perf_counter()
        result = self._inner(*args, **kwargs)
        torch.cuda.synchronize()
        self._log.append((self._name, round(time.perf_counter() - started, 2)))
        return result

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


class _PromptCache:
    """Encode every prompt of a video in one Gemma load, then serve the pipeline's one-prompt calls from memory."""

    def __init__(self, encoder: Any) -> None:
        self._encoder = encoder
        self._known: dict[str, Any] = {}

    def prepare(self, prompts: list[str]) -> None:
        missing = [prompt for prompt in dict.fromkeys(prompts) if prompt not in self._known]
        if missing:
            self._known.update(zip(missing, self._encoder(missing), strict=True))

    def __call__(self, prompts: list[str], **_kwargs: Any) -> list[Any]:
        self.prepare(list(prompts))
        return [self._known[prompt] for prompt in prompts]


class _TimedDecoder(_Timed):
    """The video decoder returns a lazy iterator: record the time spent producing its chunks."""

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        import torch

        def timed() -> Any:
            spent = 0.0
            torch.cuda.synchronize()
            started = time.perf_counter()
            chunks = self._inner(*args, **kwargs)
            while True:
                try:
                    chunk = next(chunks)
                except StopIteration:
                    break
                finally:
                    torch.cuda.synchronize()
                    spent += time.perf_counter() - started
                yield chunk
                started = time.perf_counter()
            self._log.append((self._name, round(spent, 2)))

        return timed()


def _build_pipeline(profile: dict[str, Any]) -> Any:
    import video_app as worker
    from ltx_core.quantization.fp8_cast import build_policy
    from ltx_pipelines import DistilledPipeline
    from ltx_pipelines.utils.model_paths import ModelPaths
    from ltx_pipelines.utils.types import OffloadMode

    root = Path(worker.MODEL_ROOT)
    files = {part: str(root / name) for name, part in worker.MODEL_FILES.items()}
    arguments: dict[str, Any] = {}
    if profile.get("compile"):
        from ltx_core.model.transformer.compiling import CompilationConfig

        arguments["compilation_config"] = CompilationConfig()
    if profile.get("decode_mode"):
        from ltx_core.model.video_vae.transformer import DiffVAEMode

        arguments["diffvae_optimization"] = DiffVAEMode(profile["decode_mode"])
    pipeline = DistilledPipeline(
        model_paths=ModelPaths.from_split(
            transformer_path=files["transformer"],
            text_encoder_path=files["text_encoder"],
            video_vae_path=files["video_vae"],
            audio_vae_path=files["audio_vae"],
        ),
        spatial_upsampler_path=files["spatial_upsampler"],
        loras=[],
        quantization=build_policy(files["transformer"]),
        offload_mode=OffloadMode.NONE if profile.get("offload") == "none" else OffloadMode.CPU,
        **arguments,
    )
    if profile.get("offload") == "none":
        # Gemma alone ran out of the L40S memory when loaded whole: keep streaming it through the CPU.
        pipeline.prompt_encoder._offload_mode = OffloadMode.CPU
    if profile.get("resident"):
        # The stage then keeps one transformer allocation on the GPU between its calls (pinned v1.6.2 attribute).
        pipeline.stage._active_weights = {}
    return pipeline


@app.function(
    image=IMAGE,
    gpu="L40S",
    cpu=8.0,
    memory=65_536,
    volumes={"/models": model_volume.with_mount_options(read_only=True)},
    max_containers=1,
    scaledown_window=2,
    timeout=3_600,
    retries=0,
)
def render(profile: dict[str, Any], scenes: list[dict[str, Any]]) -> dict[str, Any]:
    import os
    import tempfile
    import traceback

    if profile.get("expandable"):
        os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
    import torch
    import video_app as worker
    from ltx_pipelines.utils.media_io import encode_video
    from ltx_pipelines.utils.types import ImageConditioningInput
    from story_visual_plan import plan_scene_frames

    report: dict[str, Any] = {"profile": profile, "gpu": torch.cuda.get_device_name(0), "scenes": []}
    started = time.perf_counter()
    for name in worker.MODEL_FILES:
        with (Path(worker.MODEL_ROOT) / name).open("rb") as handle:
            while handle.read(64 * 1024 * 1024):
                pass
    report["read_checkpoints_s"] = round(time.perf_counter() - started, 1)
    log: list[tuple[str, float]] = []
    pipeline = _build_pipeline(profile)
    report["default_image_crf"] = pipeline.image_conditioner.default_image_crf
    report["ancestral_sampler"] = pipeline.use_ancestral_sampler
    cache = None
    if profile.get("prompt_cache"):
        cache = _PromptCache(_Timed(pipeline.prompt_encoder, "text_encode_all", log))
        started = time.perf_counter()
        with torch.inference_mode():
            cache.prepare([scene["prompt"] for scene in scenes])
        report["prompt_cache_s"] = round(time.perf_counter() - started, 1)
        pipeline.prompt_encoder = cache
        log.clear()
    else:
        pipeline.prompt_encoder = _Timed(pipeline.prompt_encoder, "text_encode", log)
    for block in ("image_conditioner", "stage", "upsampler", "audio_decoder"):
        inner = getattr(pipeline, block)
        if block == "image_conditioner":
            original_load = inner.load_conditionings
            wrapped = _Timed(inner, block, log)
            wrapped.load_conditionings = original_load
            setattr(pipeline, block, wrapped)
        else:
            setattr(pipeline, block, _Timed(inner, block, log))
    pipeline.video_decoder = _TimedDecoder(pipeline.video_decoder, "video_decoder", log)
    try:
        import natten

        report["natten"] = str(getattr(natten, "__version__", "installed"))
    except ImportError:
        report["natten"] = None
    with tempfile.TemporaryDirectory() as directory:
        work = Path(directory)
        for index, scene in enumerate(scenes):
            record: dict[str, Any] = {"name": scene["name"], "seconds": scene["seconds"]}
            report["scenes"].append(record)
            try:
                log.clear()
                torch.cuda.reset_peak_memory_stats()
                num_frames = int(plan_scene_frames(scene["seconds"])["generated_frame_count"])
                start = work / f"{index}-start.png"
                start.write_bytes(scene["image"])
                crf = scene.get("crf")
                images = [ImageConditioningInput.replace(str(start), frame_idx=0, strength=1.0, crf=crf)]
                if scene.get("end_image") is not None:
                    end = work / f"{index}-end.png"
                    end.write_bytes(scene["end_image"])
                    images.append(
                        ImageConditioningInput.guide(
                            str(end), frame_idx=num_frames - 1, strength=scene["end_strength"], crf=crf
                        )
                    )
                raw = work / f"{index}-raw.mp4"
                clip = work / f"{index}.mp4"
                scene_started = time.perf_counter()
                with torch.inference_mode():
                    result = pipeline(
                        prompt=scene["prompt"],
                        seed=scene["seed"],
                        height=worker.MODEL_FRAME_HEIGHT,
                        width=worker.OUTPUT_WIDTH,
                        frame_rate=worker.FPS,
                        images=images,
                        num_frames=num_frames,
                    )
                    decode_started = time.perf_counter()
                    encode_video(result.video, worker.FPS, None, str(raw), video_chunks_number=None)
                torch.cuda.synchronize()
                record["decode_and_encode_s"] = round(time.perf_counter() - decode_started, 2)
                record["render_s"] = round(time.perf_counter() - scene_started, 1)
                worker._normalize_silent_clip(
                    raw, clip, target_duration=scene["seconds"], generated_frame_count=num_frames
                )
                record["frames"] = num_frames
                record["blocks"] = list(log)
                record["peak_gpu_gb"] = round(torch.cuda.max_memory_allocated(0) / 1024**3, 1)
                record["video"] = clip.read_bytes()
                print(json.dumps({k: v for k, v in record.items() if k != "video"}), flush=True)
            except Exception as error:  # an experiment records the failure and goes on
                record["error"] = f"{type(error).__name__}: {error}"[:600]
                print(traceback.format_exc(), flush=True)
                if "out of memory" in str(error).lower():
                    break
    return report


@app.local_entrypoint()
def main(spec: str, out: str) -> None:
    request = json.loads(Path(spec).read_text(encoding="utf-8"))
    base = Path(spec).resolve().parent
    scenes = []
    for scene in request["scenes"]:
        loaded = dict(scene)
        loaded["image"] = (base / scene["image"]).read_bytes()
        loaded["end_image"] = (base / scene["end_image"]).read_bytes() if scene.get("end_image") else None
        scenes.append(loaded)
    report = render.remote(request["profile"], scenes)
    target = Path(out)
    target.mkdir(parents=True, exist_ok=True)
    for record in report["scenes"]:
        video = record.pop("video", None)
        if video:
            (target / f"{record['name']}.mp4").write_bytes(video)
    (target / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
