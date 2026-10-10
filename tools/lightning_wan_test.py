"""One native Wan2.2 TI2V-5B motion test. No installs, no full-story conversion.

Default: inspect only. --download explicitly fetches ~32 GiB of public weights.
--run creates one 73-frame (~3.04s at 24fps) silent draft with 30 diffusion steps.
"""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REVISION = "921dbaf3f1674a56f47e83fb80a34bac8a8f203e"
MODEL_ID = "Wan-AI/Wan2.2-TI2V-5B"


def sdpa_attention(q, k, v, q_lens=None, k_lens=None, dropout_p=0.,
                   softmax_scale=None, q_scale=None, causal=False,
                   window_size=(-1, -1), deterministic=False,
                   dtype=None, version=None):
    """Length-aware SDPA adapter for this batch-one, global-attention test."""
    import torch
    from torch.nn.attention import SDPBackend, sdpa_kernel
    if tuple(window_size) != (-1, -1) or deterministic:
        raise RuntimeError('SDPA test adapter does not support local windows or deterministic mode')
    if q.device.type != 'cuda':
        raise RuntimeError('This adapter requires CUDA fused attention')
    original_dtype = q.dtype
    half_dtypes = (torch.float16, torch.bfloat16)
    target_dtype = v.dtype if v.dtype in half_dtypes else (dtype or torch.bfloat16)
    output = torch.zeros((*q.shape[:-1], v.shape[-1]), device=q.device, dtype=target_dtype)
    # Slice each example rather than constructing a quadratic padding mask.
    # Explicit lengths preserve semantics for padded text and video tokens.
    for index in range(q.shape[0]):
        qn = q.shape[1] if q_lens is None else int(q_lens[index])
        kn = k.shape[1] if k_lens is None else int(k_lens[index])
        if not (0 < qn <= q.shape[1] and 0 < kn <= k.shape[1]):
            raise RuntimeError('Invalid attention sequence lengths')
        query = q[index:index + 1, :qn].transpose(1, 2).to(target_dtype)
        key = k[index:index + 1, :kn].transpose(1, 2).to(target_dtype)
        value = v[index:index + 1, :kn].transpose(1, 2).to(target_dtype)
        if q_scale is not None:
            query = query * q_scale
        # Do not silently use quadratic-memory math attention on the L4.
        with sdpa_kernel([SDPBackend.FLASH_ATTENTION, SDPBackend.EFFICIENT_ATTENTION]):
            attended = torch.nn.functional.scaled_dot_product_attention(
                query, key, value, dropout_p=dropout_p,
                is_causal=causal, scale=softmax_scale)
        output[index, :qn] = attended.transpose(1, 2)[0]
    return output.to(original_dtype)


# Load the real TI2V implementation without executing Wan's eager top-level
# imports of unrelated S2V/Animate pipelines. No missing dependency is mocked.
# The original generate.py and model implementations remain unchanged.
TI2V_BOOTSTRAP = r'''
import importlib, importlib.machinery, pathlib, runpy, sys, types
repo = pathlib.Path(sys.argv[1]).resolve()
cli_args = sys.argv[2:]
if '--task' in cli_args and cli_args[cli_args.index('--task') + 1] != 'ti2v-5B':
    raise SystemExit('This isolated launcher supports only ti2v-5B')
sys.path.insert(0, str(repo))
package = types.ModuleType('wan')
package.__path__ = [str(repo / 'wan')]
package.__package__ = 'wan'
package.__spec__ = importlib.machinery.ModuleSpec('wan', loader=None, is_package=True)
package.__spec__.submodule_search_locations = package.__path__
sys.modules['wan'] = package
package.configs = importlib.import_module('wan.configs')
attention_module = importlib.import_module('wan.modules.attention')
if not (attention_module.FLASH_ATTN_2_AVAILABLE or attention_module.FLASH_ATTN_3_AVAILABLE):
    original_attention = attention_module.flash_attention
    # wan.modules.__init__ has already imported model.py; replace its captured
    # function reference too, before loading the TI2V implementation.
    for name, module in list(sys.modules.items()):
        if name.startswith('wan.') and getattr(module, 'flash_attention', None) is original_attention:
            module.flash_attention = sdpa_attention
    import torch
    probe = torch.randn(2, 8, 2, 128, device='cuda', dtype=torch.bfloat16)
    probe_k = torch.randn(2, 6, 2, 128, device='cuda', dtype=torch.bfloat16)
    probe_v = torch.randn_like(probe_k)
    probe_out = sdpa_attention(probe, probe_k, probe_v, q_lens=[8, 5], k_lens=[6, 4])
    assert probe_out.shape == probe.shape and torch.isfinite(probe_out).all()
    assert torch.count_nonzero(probe_out[1, 5:]) == 0
    for i, (qn, kn) in enumerate(((8, 6), (5, 4))):
        pq = probe[i, :qn].transpose(0, 1).float()
        pk = probe_k[i, :kn].transpose(0, 1).float()
        pv = probe_v[i, :kn].transpose(0, 1).float()
        expected = ((pq @ pk.transpose(-1, -2)) / (128 ** .5)).softmax(-1) @ pv
        torch.testing.assert_close(probe_out[i, :qn].transpose(0, 1).float(),
                                   expected, atol=.03, rtol=.03)
    del probe, probe_k, probe_v, probe_out, pq, pk, pv, expected
    torch.cuda.empty_cache()
    print('WAN_SDPA_OK: fused PyTorch attention; sequence lengths preserved', flush=True)
package.WanTI2V = importlib.import_module('wan.textimage2video').WanTI2V
print('WAN_TI2V_ONLY: real TI2V loaded; S2V/Animate not loaded', flush=True)
sys.argv = [str(repo / 'generate.py'), *cli_args]
runpy.run_path(str(repo / 'generate.py'), run_name='__main__')
'''


def wan_command(repo, arguments):
    bootstrap = inspect.getsource(sdpa_attention) + '\n' + TI2V_BOOTSTRAP
    return [sys.executable, '-c', bootstrap, str(repo), *arguments]


PROMPT = (
    "A colored pencil story illustration gently comes to life. The same young boy "
    "in a blue shirt with an orange pocket, purple shorts and green shoes takes two "
    "small natural steps forward along the garden path, with a gentle arm swing. "
    "Preserve his original face and clothes, the hand-drawn outlines and colored "
    "pencil texture. The red-roof house, flowers and white background stay stable. "
    "Fixed camera. Small restrained movement, no new people or objects, no butterfly, "
    "no changes of art style, no text, no drawing or coloring reveal."
)


def missing_weights(folder):
    names = ["config.json", "Wan2.2_VAE.pth", "models_t5_umt5-xxl-enc-bf16.pth",
             "diffusion_pytorch_model.safetensors.index.json",
             "google/umt5-xxl/spiece.model", "google/umt5-xxl/tokenizer_config.json"]
    names += [f"diffusion_pytorch_model-{i:05}-of-00003.safetensors" for i in (1, 2, 3)]
    return [name for name in names if not (folder / name).is_file() or (folder / name).stat().st_size == 0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path("/teamspace/studios/this_studio/Wan2.2"))
    parser.add_argument("--checkpoint", type=Path,
                        default=Path("/teamspace/studios/this_studio/models/Wan2.2-TI2V-5B"))
    parser.add_argument("--image", type=Path)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    root = Path.cwd().resolve()
    repo = args.repo.resolve()
    checkpoint = args.checkpoint.resolve()
    image = (args.image or root / ".runtime/complete-story-demo/20261010-040933/scene-2.png").resolve()
    if not (repo / "generate.py").is_file():
        raise FileNotFoundError(f"Wan source missing: {repo / 'generate.py'}")
    if not image.is_file():
        raise FileNotFoundError(f"Reviewed test input missing: {image}")
    import torch
    print(f"Python: {sys.executable}; torch: {torch.__version__}", flush=True)
    if not torch.cuda.is_available():
        raise RuntimeError("Run the test on Lightning with its GPU enabled")
    free, total = torch.cuda.mem_get_info()
    print(f"GPU: {torch.cuda.get_device_name(0)}; free/total VRAM: {free/1024**3:.2f}/{total/1024**3:.2f} GiB", flush=True)
    print(f"Image: {image}", flush=True)
    print(f"Checkpoint: {checkpoint}; missing: {missing_weights(checkpoint)}", flush=True)
    print(f"Workspace free disk: {shutil.disk_usage(root).free/1024**3:.1f} GiB", flush=True)
    if total < 22 * 1024**3:
        raise RuntimeError("This native 720-area test targets a 24GB-class GPU; do not launch this configuration")
    if free < 20 * 1024**3 and args.run:
        raise RuntimeError("Not enough free VRAM for this conservative test; stop your own FLUX job first")
    # Imports from the actual installed Wan source are checked before any large download.
    result = subprocess.run(wan_command(repo, ["--help"]),
                            cwd=repo, capture_output=True, text=True, timeout=90)
    if result.returncode:
        print(result.stdout, flush=True)
        print(result.stderr, flush=True)
        raise RuntimeError("Wan dependency/import preflight failed. No weights downloaded and no packages changed.")
    for option in ("--task", "--frame_num", "--sample_steps", "--t5_cpu", "--convert_model_dtype"):
        if option not in result.stdout:
            raise RuntimeError(f"Installed Wan CLI does not expose {option}")
    print("WAN_CLI_IMPORT_OK", flush=True)
    if "WAN_SDPA_OK" in result.stdout:
        print("WAN_SDPA_OK: fused attention smoke test passed on this GPU", flush=True)
    if args.download and missing_weights(checkpoint):
        if not checkpoint.is_dir():
            checkpoint.mkdir(parents=True, exist_ok=True)
        if shutil.disk_usage(checkpoint).free < 65 * 1024**3:
            raise RuntimeError("Need at least 65 GiB free for a conservative checkpoint-download budget")
        os.environ["HF_HUB_OFFLINE"] = "0"
        from huggingface_hub import snapshot_download
        print("Downloading public native Wan weights (~32 GiB); no pip install or login", flush=True)
        snapshot_download(repo_id=MODEL_ID, revision=REVISION, token=False,
            local_dir=str(checkpoint), allow_patterns=["*.json", "*.pth", "*.safetensors", "google/**"])
    absent = missing_weights(checkpoint)
    if not args.run:
        print("PREFLIGHT_DONE. To fetch weights and render the single test, rerun with --download --run.", flush=True)
        return
    if absent:
        raise RuntimeError(f"Checkpoint incomplete: {absent}. Use --download or --checkpoint with a complete native model.")
    out = root / ".runtime/wan-motion-test" / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    out.mkdir(parents=True, exist_ok=False)
    video = out / "boy-walking-wan.mp4"
    command = wan_command(repo, ["--task", "ti2v-5B",
               "--size", "1280*704", "--ckpt_dir", str(checkpoint), "--offload_model", "True",
               "--convert_model_dtype", "--t5_cpu", "--frame_num", "73", "--sample_steps", "30",
               "--base_seed", "42", "--image", str(image), "--prompt", PROMPT, "--save_file", str(video)])
    report = {"model": MODEL_ID, "revision": REVISION, "image": str(image),
              "image_sha256": hashlib.sha256(image.read_bytes()).hexdigest(), "command": command,
              "prompt": PROMPT, "frames": 73, "fps": 24, "steps": 30,
              "quality": "DRAFT_30_STEPS_VS_OFFICIAL_50", "status": "RUNNING",
              "audio": "NONE", "size_note": "720-area preset; native I2V follows input aspect ratio"}
    (out / "test.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("Generating ONE Wan draft clip; L4 runtime has not been benchmarked", flush=True)
    try:
        subprocess.run(command, cwd=repo, check=True)
        if not video.is_file() or video.stat().st_size == 0:
            raise RuntimeError("Wan exited without producing a usable output file")
    except BaseException:
        report["status"] = "FAILED_REQUIRES_REVIEW"
        (out / "test.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        raise
    report["status"] = "GENERATED_PENDING_VISUAL_REVIEW"
    (out / "test.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"DONE: {video}", flush=True)
    print("Review face/hand consistency, motion and stable background; not approved for the full story.")


if __name__ == "__main__":
    main()
