import importlib.util
import json
import sys
from pathlib import Path

import modal

if modal.is_local():
    recipe_path = Path(__file__).resolve().parents[4] / "deployment/modal/qwen_vision_v2.py"
    spec = importlib.util.spec_from_file_location("qwen_processor_recipe", recipe_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot read deployment recipe")
    recipe = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = recipe
    spec.loader.exec_module(recipe)
    diagnostic_image = recipe.image.env({
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "HF_HUB_DISABLE_TELEMETRY": "1",
    })
else:
    diagnostic_image = None

app = modal.App("sketch2life-qwen-processor-check")
volume = modal.Volume.from_name("sketch2life-qwen3-vl-8b-v1")


@app.function(
    image=diagnostic_image,
    gpu=None,
    cpu=1.0,
    memory=4096,
    secrets=[],
    volumes={"/models": volume.with_mount_options(read_only=True)},
    min_containers=0,
    max_containers=1,
    scaledown_window=2,
    timeout=120,
    retries=0,
)
def check_processor():
    from importlib.metadata import PackageNotFoundError, version

    versions = {}
    for name in ("torch", "torchvision", "transformers", "tokenizers", "Pillow"):
        try:
            versions[name] = version(name)
        except PackageNotFoundError:
            versions[name] = "NOT_INSTALLED"
    print(json.dumps({"package_versions": versions}), flush=True)

    model_path = "/models/qwen3-vl-8b-instruct"
    stage = "IMPORT"
    try:
        import torch
        from transformers import AutoProcessor

        stage = "PROCESSOR_LOAD"
        processor = AutoProcessor.from_pretrained(
            model_path,
            revision="0c351dd01ed87e9c1b53cbc748cba10e6187ff3b",
            dtype=torch.bfloat16,
            device_map="auto",
            local_files_only=True,
        )
    except Exception as exc:
        return {
            "status": "PROCESSOR_CHECK_FAILED",
            "stage": stage,
            "error_type": type(exc).__name__,
            "detail": str(exc).replace(model_path, "<MODEL_DIR>")[:2400],
        }

    return {"status": "PROCESSOR_READY", "processor": type(processor).__name__}


@app.local_entrypoint()
def main():
    result = check_processor.remote()
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if result["status"] != "PROCESSOR_READY":
        raise SystemExit(1)
