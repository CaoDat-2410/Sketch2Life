"""FEAT-094 phase 2: the child process that prepares scene keyframes inside the video container (ADR-0026).

Runs in ``/opt/prep-venv`` (its own torch and diffusers). FLUX.3 klein paints the background plate and SAM 2.1 cuts the
child's subjects; ``scene_prepare`` composes them. The parent talks to it through ``scene_prepare_host``.
"""

from __future__ import annotations

import gc
import json
import re
import sys
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any, TextIO

import scene_prepare
from scene_prepare_host import DEFAULT_PLATE_SEED, REPLY_PREFIX

MODEL_MOUNT = Path("/models")
SAM_COMMIT = "2b90b9f5ceec907a1c18123530e92e794ad901a4"
SAM_CHECKPOINT = MODEL_MOUNT / "sam2.1_hiera_small" / SAM_COMMIT / "sam2.1_hiera_small.pt"
SAM_CONFIG = "configs/sam2.1/sam2.1_hiera_s.yaml"
_flux: Any = None
_sam: Any = None


def plate_model_dir(mount: Path = MODEL_MOUNT) -> str:
    root = mount / "flux_3_image_klein"
    revisions = (
        sorted(path for path in root.iterdir() if (path / "image" / "modular_model_index.json").is_file())
        if root.is_dir()
        else []
    )
    if not revisions:
        raise RuntimeError("PLATE_MODEL_UNAVAILABLE")
    return str(revisions[-1] / "image")


def load_flux() -> Any:
    global _flux
    if _flux is None:
        import torch
        from diffusers import ModularPipeline

        model_dir = plate_model_dir()
        spec = ModularPipeline.from_pretrained(model_dir, local_files_only=True)
        blocks = spec.blocks
        blocks.sub_blocks.pop("prompt_upsampler", None)
        pipeline = blocks.init_pipeline(model_dir)
        pipeline.load_components(dtype={"vae": torch.float32, "default": torch.bfloat16}, local_files_only=True)
        pipeline.to("cuda")
        _flux = pipeline
        gc.collect()
    return _flux


def load_sam() -> Any:
    global _sam
    if _sam is None:
        import sam_masks

        if not SAM_CHECKPOINT.is_file():
            raise sam_masks.MaskError("SAM_CHECKPOINT_UNAVAILABLE")
        import torch
        from sam2.build_sam import build_sam2
        from sam2.sam2_image_predictor import SAM2ImagePredictor

        model = build_sam2(
            SAM_CONFIG,
            str(SAM_CHECKPOINT),
            device="cuda" if torch.cuda.is_available() else "cpu",
            apply_postprocessing=False,
        )
        _sam = SAM2ImagePredictor(model)
    return _sam


def _plate(prompt: str, seed: int) -> Any:
    """A 1280x768 crayon-style background plate."""

    import torch

    pipeline = load_flux()
    with torch.inference_mode():
        return pipeline(
            prompt=prompt,
            height=768,
            width=1280,
            generator=torch.Generator(device="cuda").manual_seed(seed),
            output="images",
        )[0]


def logged_plate(prompt: str, seed: int) -> Any:
    """``_plate`` that records why a plate failed (library error text only; the prompt is never logged)."""

    try:
        return _plate(prompt, seed)
    except Exception as error:  # noqa: BLE001
        _log(
            "scene_plate_failed",
            error_type=type(error).__name__,
            error_text=re.sub(r"\s+", " ", str(error))[:300],
        )
        raise


def _log(event: str, **fields: Any) -> None:
    print(json.dumps({"event": event, **fields}, sort_keys=True), flush=True)


def warm_up(_body: dict[str, Any]) -> dict[str, Any]:
    """Load the plate and mask models; no job data is read and a load failure leaves the paper fallback."""

    loaded = []
    for name, load in (("plate", load_flux), ("mask", load_sam)):
        try:
            load()
        except Exception as error:  # noqa: BLE001
            _log("scene_warm_up_failed", model=name, error_type=type(error).__name__)
        else:
            loaded.append(name)
    _log("scene_warm_up", loaded=loaded)
    return {"loaded": loaded}


def prepare(body: dict[str, Any]) -> dict[str, Any]:
    """Read ``drawing.png`` from the job directory and write ``keyframe.png`` beside it."""

    directory = Path(body["directory"])
    request = body["request"]
    seed = request.get("plate_seed", DEFAULT_PLATE_SEED)
    outcome = scene_prepare.prepare_scene(
        (directory / "drawing.png").read_bytes(),
        main=request["main"],
        secondaries=request["secondaries"],
        staging=request["staging"],
        scene_index=request["scene_index"],
        source_facing=request["source_facing"],
        plate_prompt=request["plate_prompt"],
        generate_plate=lambda prompt: logged_plate(prompt, seed),
        predictor_factory=load_sam,
    )
    (directory / "keyframe.png").write_bytes(outcome["keyframe_png"])
    _log("scene_prepared", scene_index=request["scene_index"], background=outcome["background"], reason=outcome["reason"])
    return {"background": outcome["background"], "reason": outcome["reason"]}


def serve(
    requests: Iterable[str],
    output: TextIO,
    handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]],
) -> None:
    for line in requests:
        if not line.strip():
            continue
        message = json.loads(line)
        try:
            reply = {"id": message["id"], "ok": True, "result": handlers[message["op"]](message["body"])}
        except Exception as error:  # noqa: BLE001 - never send provider text to the parent
            _log("scene_prepare_request_failed", error_type=type(error).__name__)
            reply = {"id": message.get("id"), "ok": False, "error": "SCENE_PREPARE_UNEXPECTED_ERROR"}
        # The leading newline ends any progress line a library left open.
        output.write("\n" + REPLY_PREFIX + json.dumps(reply) + "\n")
        output.flush()


if __name__ == "__main__":
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    serve(sys.stdin, sys.stdout, {"warmup": warm_up, "prepare": prepare})
