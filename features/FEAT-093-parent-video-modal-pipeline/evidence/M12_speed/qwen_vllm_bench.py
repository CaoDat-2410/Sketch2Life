"""FEAT-093 Amendment C3: single-stream vLLM benchmark of the pinned Qwen3.8-27B-FP8 checkpoint on Modal L40S.

Run from the repository root:  modal run features/.../M12_speed/qwen_vllm_bench.py --env dev
The prompt and JSON schema are the real Parent story ones, built locally from the worker module. Synthetic input only.
Each configuration runs in its own subprocess of one container so GPU memory is released between engines.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import modal

MODEL_DIR = "/models/qwen3_8_27b_fp8/c3a462cc3d38cf351f3b26cbd763469eeb74ef81"
VLLM_VERSION = "0.34.0"

app = modal.App("sketch2life-qwen-vllm-bench")
volume = modal.Volume.from_name("sketch2life-dev-model-weights-v2", environment_name="dev", version=2)
image = (
    modal.Image.debian_slim(python_version="3.11")
    .uv_pip_install(f"vllm=={VLLM_VERSION}")
    .env({"HF_HUB_OFFLINE": "1", "HF_HUB_DISABLE_TELEMETRY": "1"})
    .add_local_file(__file__, "/root/qwen_vllm_bench.py")
)

BASE: dict[str, Any] = {"max_model_len": 16_384, "gpu_memory_utilization": 0.92, "max_num_seqs": 1}
MTP = {"method": "mtp", "num_speculative_tokens": 3}
CONFIGS: dict[str, dict[str, Any]] = {
    "plain": {},
    "mtp3": {"speculative_config": MTP},
    "mtp3_kvfp8": {"speculative_config": MTP, "kv_cache_dtype": "fp8"},
}


def _run_one(name: str, job_path: str, out_path: str) -> None:
    from vllm import LLM, SamplingParams
    from vllm.sampling_params import StructuredOutputsParams

    job = json.loads(Path(job_path).read_text(encoding="utf-8"))
    started = time.perf_counter()
    llm = LLM(model=MODEL_DIR, **BASE, **CONFIGS[name])
    result: dict[str, Any] = {"config": name, "load_seconds": round(time.perf_counter() - started, 1), "runs": []}
    for label, constrained in (("warmup", True), ("story_json", True), ("story_free", False)):
        params: dict[str, Any] = {"temperature": 0.0, "max_tokens": 64 if label == "warmup" else 4_096}
        if constrained:
            params["structured_outputs"] = StructuredOutputsParams(json=job["schema"])
        started = time.perf_counter()
        output = llm.chat(
            job["messages"],
            SamplingParams(**params),
            chat_template_kwargs={"enable_thinking": False},
            use_tqdm=False,
        )[0].outputs[0]
        seconds = time.perf_counter() - started
        result["runs"].append(
            {
                "label": label,
                "seconds": round(seconds, 2),
                "output_tokens": len(output.token_ids),
                "tokens_per_second": round(len(output.token_ids) / seconds, 2),
                "finish_reason": output.finish_reason,
                "text": output.text if label == "story_json" else None,
            }
        )
        Path(out_path).write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")


@app.function(image=image, gpu="L40S", cpu=8.0, memory=65_536, volumes={"/models": volume.with_mount_options(read_only=True)}, timeout=3_000)
def bench(job: dict[str, Any], names: list[str]) -> list[dict[str, Any]]:
    Path("/tmp/job.json").write_text(json.dumps(job, ensure_ascii=False), encoding="utf-8")
    results = []
    for name in names:
        out = Path(f"/tmp/{name}.json")
        process = subprocess.run(
            [sys.executable, "/root/qwen_vllm_bench.py", name, "/tmp/job.json", str(out)],
            capture_output=True,
            text=True,
            timeout=1_200,
        )
        entry = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {"config": name, "runs": []}
        entry["exit_code"] = process.returncode
        if process.returncode != 0:
            entry["error_tail"] = (process.stderr or process.stdout)[-3_000:]
        entry["log_lines"] = [
            line[-400:]
            for line in (process.stdout + process.stderr).splitlines()
            if any(key in line for key in ("KV cache", "acceptance", "Available KV", "quantization", "Using", "mamba"))
        ][-40:]
        print(json.dumps({k: v for k, v in entry.items() if k not in {"runs", "log_lines", "error_tail"}}), flush=True)
        results.append(entry)
    return results


@app.local_entrypoint()
def main(configs: str = "plain,mtp3,mtp3_kvfp8", out: str = "bench_result.json") -> None:
    repo = Path(__file__).resolve().parents[4]
    worker_dir = repo / "deployment" / "modal" / "srs_v23"
    sys.path[:0] = [str(worker_dir), str(repo / "backend" / "src")]
    import language_audio_app as worker

    request = {
        "confirmed_subject": "rùa",
        "visible_features": ["vỏ xanh lá có các ô hình lục giác", "đầu tròn màu nâu nhạt", "bốn chân xanh nhạt"],
        "child_age_months": 48,
        "adult_confirmed_idea": "con rùa",
        "topic": "Động vật",
        "primary_activity": {
            "title": "Theo dấu chân rùa trên sân",
            "objective": "Trẻ nhận ra đặc điểm di chuyển chậm của rùa.",
            "materials_text": "Phấn màu và vài viên gạch nhỏ",
            "preparation_text": "Người lớn chuẩn bị một khoảng sân phẳng.",
            "instructions_text": "Bé vẽ dấu chân rồi đi chậm theo đường vừa vẽ.",
            "observation_notes": "Quan sát bé giữ thăng bằng.",
            "safety_notes": "Người lớn đi cùng bé.",
            "activity_kind": "OUTDOOR",
        },
    }
    job = {
        "messages": [
            {"role": "system", "content": "Bạn là trợ lý viết nội dung giáo dục ngắn, an toàn và trung thực."},
            {"role": "user", "content": worker._parent_story_prompt(request)},
        ],
        "schema": worker._parent_story_content_json_schema(),
    }
    results = bench.remote(job, [name for name in configs.split(",") if name])
    for entry in results:
        for run in entry["runs"]:
            if run.get("text"):
                try:
                    worker._parse_story_content_output(run["text"])
                    run["gate"] = "PASS"
                except worker.StoryOutputValidationError as error:
                    run["gate"] = f"{error.reason_code}:{error.field_path}"
    target = Path(__file__).with_name(out)
    target.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    for entry in results:
        print(entry["config"], entry.get("exit_code"), "load", entry.get("load_seconds"))
        for run in entry["runs"]:
            print("  ", run["label"], run["output_tokens"], "tok", run["seconds"], "s", run["tokens_per_second"], "tok/s", run.get("gate", ""))
    print("saved", target.name)


if __name__ == "__main__":
    _run_one(*sys.argv[1:4])
