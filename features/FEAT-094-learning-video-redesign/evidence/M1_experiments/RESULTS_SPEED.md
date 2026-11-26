# Phase 1: LTX-2.5 speed on one L40S (2026-11-26)

Ephemeral app `ltx_experiments.py`, Modal workspace `siesta-6107`, 1280x768, 24 fps, DistilledPipeline v1.6.2,
fp8-cast. Synthetic inputs only. Raw numbers: `speed_*/report.json`. One run per profile, so differences of a few
seconds are noise.

## Seconds to render one scene (pipeline call plus encoding)

| Profile | first 6 s | 6 s | 10 s | 10 s again | peak GPU memory |
|---|---|---|---|---|---|
| `baseline` (today: CPU offload) | 95.3 | 82.5 | 120.1 | | 20 GB |
| `resident` (transformer stays on the GPU, prompts encoded once) | 51.8 | 50.0 | 89.7 | | 36 GB |
| `decode` (`resident` + decoder `combined_compile`) | 77.7 | 39.5 | 70.0 | 70.5 | 41 GB |
| `compile_chunked` (`resident` + transformer compile + decoder `chunked_compile`) | 72.3 | 44.7 | 78.6 | 79.2 | 36 GB |
| `full` (transformer compile + decoder `combined_compile`) | out of memory | | | | over 44 GB |

Once per container: reading the checkpoints about 40 s; encoding all prompts about 13 s. Decoder compilation costs about
35 s on the first scene only.

## Where a 10 s scene goes (`decode`)

Stage 1 about 14 s, stage 2 about 28 s, video decode about 25 s, audio decode 1.3 s, the rest under 3 s. In `baseline`
the Gemma text encoder alone took 8 to 13 s per scene.

## Items of plan section 9.2

| Item | Result |
|---|---|
| S0 measure | done, table above |
| S1 no offload | adopted for the transformer and VAEs. **Gemma loaded whole ran out of memory**, so it stays streamed |
| S2 encode prompts once | adopted |
| S3 `torch.compile` | the transformer compile cuts the stages by about 17% but cannot be combined with the fast decoder (memory). The decoder compile gives more and is adopted |
| S4 attention backend | no change available: on the L40S the code already picks PyTorch SDPA with every backend; FlashAttention 3 and 4 need Hopper or Blackwell |
| S8 fewer frames | not needed for the target |

## Estimate for a whole video (not measured end to end)

Render with `decode`: about 40 s checkpoint read + 13 s prompts + 35 s first-scene compile + 70 s per 10 s scene:
5 scenes about 7.3 min, 7 scenes about 9.6 min. Scene preparation on the same GPU (option A) and queue time come on top.

Risk: the peak of 41 GB on the first scene leaves about 3 GB free; the worker needs a fallback to `chunked_eager` when
memory runs out.
