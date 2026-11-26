# LTX-2.5 speed notes (L40S, 48 GB)

Source: tips pasted by the owner on 2026-11-26 (third-party text with blog links; the links and claims have **not** been
checked here). The "ours today" column comes from `deployment/modal/srs_v23/video_app.py` and the live logs.

| Tip | Ours today | To do |
|---|---|---|
| Use the distilled model (6-8 steps) | Already distilled (`DistilledPipeline`, distilled transformer) | Confirm the step schedule actually run |
| FP8 or INT8 checkpoint, FP8 tensor cores | bf16 files, FP8 cast at load | Measure a pre-quantised FP8 checkpoint and `fp8-scaled-mm` against the cast |
| Keep everything in 48 GB, avoid CPU offload | `OffloadMode.CPU` | Likely the largest cost; see the memory note below |
| Flash Attention 2 or SageAttention | Not checked | Check the attention backend the pipeline uses |
| Do not unload text encoder and VAE between renders | Offloaded between stages | Keep resident, or encode all scene prompts once |
| Render at base resolution, then upscale | The pipeline has a spatial upsampler; output 1280x768 | Check the base resolution used |
| Switch audio off | Clips are made silent afterwards; an audio VAE is loaded | Check whether the audio branch can be skipped |
| `torch.compile` (1-2 min first run, 15-25% faster) | Not used | Measure; only pays off when the container serves many scenes |
| ComfyUI settings | Not applicable: we call the Python pipeline | - |

Memory note (our estimate, to be measured): the transformer in FP8 is about 22 GB and Gemma 4 12B in bf16 about 24 GB,
which leaves almost nothing of 48 GB for the VAE and activations. Fitting everything probably needs the prompts encoded
once and the text encoder released (or quantised, or run elsewhere), not only an FP8 transformer.

Update from the quality research (`LTX25_QUALITY_RESEARCH.md`): `fp8-scaled-mm` targets Hopper and later with FP8
checkpoints, so it is not expected to help on L40S, and the distilled pipeline has no flag to skip audio.

vLLM, multi-token prediction and the KV cache setting used for Qwen apply to text generation only; a diffusion video
model has no counterpart for them. The items above are the equivalents to benchmark.

Benchmark rule: same keyframe, prompt and seed; record seconds per 6 s scene, peak VRAM and frames side by side, one
change at a time.

Owner's stated setup for such advice: Python pipeline (not ComfyUI), 1280x768, 24 fps, 5-9 scenes of 6-8 s.
