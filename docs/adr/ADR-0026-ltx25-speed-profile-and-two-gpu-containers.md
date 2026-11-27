# ADR-0026: LTX-2.5 speed profile and at most two L40S containers

- **Status:** Proposed (FEAT-094 phase 2; the owner approved at most two containers on 2026-11-26, option A)
- **Date:** 2026-11-26

## Context

A 10 second scene took about 120 s in the deployed configuration (`OffloadMode.CPU`, one prompt encoded per scene).
The new learning video renders five to seven such scenes one after another. Today the video flow can also keep three
L40S containers busy at once (Qwen, scene preparation, LTX).

Measurements: `features/FEAT-094-learning-video-redesign/evidence/M1_experiments/RESULTS_SPEED.md`.

## Decision

1. The scene renderer keeps the transformer and VAE builds on the GPU (`OffloadMode.NONE`, one resident transformer
   allocation) and streams only the Gemma text encoder through the CPU, which did not fit when loaded whole.
2. All prompts of a video are encoded in one call before the first scene.
3. The video decoder uses `DiffVAEMode.COMBINED_COMPILE`. The transformer is not compiled: together with the compiled
   decoder it ran out of the 44 GB of memory.
4. On a CUDA out-of-memory error the worker rebuilds the pipeline with the previous settings and renders the scene
   again; the event is logged.
5. At most two L40S containers: one for Qwen and one for the video, which prepares every scene frame and then renders.
   Scenes are never rendered in parallel.
6. Preparation and rendering are the same Modal function. Preparation (FLUX.3 klein and SAM 2.1) runs as a child
   process with its own Python environment (`/opt/prep-venv`); the renderer ends that process before it loads LTX, and
   unloads LTX before it starts the process again. The checkpoint is read ahead in the background during preparation.
7. The backend prepares every frame first, then sends the scene prompts, then renders.
8. Both environments of the video image and the serving Qwen (vLLM) image install from committed lock files
   (`deployment/modal/srs_v23/locks/`). Debian packages are not pinned; the video image build refuses an ffmpeg series
   other than 7.1, and the normalisation check of
   `features/FEAT-094-learning-video-redesign/evidence/M2_normalize/` stays the check after a rebuild.
9. The video container is also warmed when the Parent receives the story to review (`SKETCH2LIFE_STORY_VIDEO_WARM_UP`).

## Consequences

- A 10 s scene renders in about 70 s; peak memory about 41 GB, so little headroom remains.
- The first scene of a container pays about 35 s of compilation; the warm-up renders a short scene to pay it early.
- The pipeline attribute that makes the transformer resident is private to the pinned LTX code (`v1.6.2`); a version
  change needs the measurement and a test again.
- Scene preparation no longer overlaps rendering, which adds waiting time (estimated 2 to 3 minutes, not measured).
- An abandoned story review costs one idle video container for up to five minutes after the warm-up.
- Two videos requested at once share the one container and would switch between the two model sets for every call.
- The speech images and the transformers-based text image are still resolved at build time (their direct packages are
  pinned).

## Not decided

A larger GPU (plan item S9) needs a separate approval.
