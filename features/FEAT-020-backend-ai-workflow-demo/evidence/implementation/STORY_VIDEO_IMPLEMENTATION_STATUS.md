# Story video implementation status

Updated: 2026-09-30

## Completed in the repository

- Versioned contracts for the approved story package, storyboard, narration,
  illustration, silent scene, assembly and public job status.
- Deterministic storyboard compilation with approved fact/anchor continuity.
- Measured TTS timing as the final scene-duration source of truth.
- Provider-neutral orchestration: narration → storyboard finalization →
  illustration → per-scene motion → assembly → duration gate.
- Idempotent process-local story-video job API with safe public progress.
- Lightning adapter and provider routes with strict response validation.
- Runtime hooks for ElevenLabs, Diffusers image-to-image, official Wan2.2
  TI2V-5B CLI, and FFmpeg assembly; each is lazy-loaded and fails closed when
  its required secret, executable, repository or checkpoint is absent.
- Honest `BLOCKED` results when a model/runtime is not configured.
- Local unit, contract, lint and provider smoke checks for the implemented
  boundaries.

## Not completed in this environment

- A production ElevenLabs credential/voice selection on Lightning (`ELEVENLABS_API_KEY` and `ELEVENLABS_VOICE_ID`).
- Image-generation model and weights on Lightning.
- Wan2.2 TI2V-5B runtime, checkpoint and L4 benchmark.
- Real scene rendering, FFmpeg assembly and final MP4 validation on GPU.
- Mobile playback test against a public Lightning port.

The runtime hooks are not evidence of a successful GPU generation. They still
require the corresponding external credentials, packages and model weights on
the target Lightning machine.

## Acceptance gate

The story-video job must not transition to `READY` until the configured
provider returns real, schema-valid artifacts and final duration validation
passes the approved 40–60 second window. The current provider returns typed
`BLOCKED` responses instead of claiming generated media.
