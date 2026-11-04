# Sketch2Life Modal scaffold for SRS v2.3

This folder contains the **dev-only Modal deployment** for the current SRS v2.3 AI workloads. Product dispatch, auth, quota, storage transfer, safety acceptance, and playback remain backend-owned; every `workloads.json` entry stays disabled. The original generic L4/L40S scaffold remains contract-only. Separate private apps implement bounded synthetic POCs for drawing VLM, story/audio, FLUX images, and Wan video feasibility; none is a production model selection.

## Current dev deployment — 2026-11-03

- Private apps: `sketch2life-srs23-drawing-vlm-dev`, `sketch2life-srs23-language-audio-dev`, `sketch2life-srs23-flux-image-dev`, and `sketch2life-srs23-video-candidate-dev`.
- All seven pinned checkpoints (Qwen2.5-VL, Qwen story, Whisper, VieNeu TTS, MOSS codec, FLUX.2 Klein, and Wan2.2) are downloaded directly from Hugging Face into the existing Modal Volume v2; retained checkpoint files total 88.59 GiB. **You do not need to download model files to your computer and upload them.**
- VieNeu → Whisper completed one synthetic Vietnamese speech round-trip; Whisper substituted one word. FLUX completed one synthetic three-panel line-guide image inference; queue plus cold-start elapsed about 20 minutes. The corrective Qwen-VL inference is still pending Modal L4 capacity. Qwen story and Wan inference have not run. Wan2.2 is an alternative feasibility candidate only; LTX-2.5 remains the SRS video candidate and is gated.
- The language/audio app is deployed as v2 after a security-scanner cleanup; function IDs and inference behavior are unchanged. Modal billing after model downloads has not been checked. Exact call IDs, artifacts, and limitations: [`MODAL_AI_HOSTING_WAVE_20261103.md`](../../../features/FEAT-063-system-architecture-rearchitecture/evidence/MODAL_AI_HOSTING_WAVE_20261103.md).
- Exact revisions, app/function/call IDs, hashes, results, and limits: [`MODAL_AI_HOSTING_WAVE_20261103.md`](../../../features/FEAT-063-system-architecture-rearchitecture/evidence/MODAL_AI_HOSTING_WAVE_20261103.md).

The canonical AI workload registry is [`workloads.json`](workloads.json). The worker contract accepts only opaque job/generation/attempt references, one manifest path, and integrity metadata. It carries no media bytes, MinIO endpoint, child name/profile ID, Firebase token, or payment data.

## Workloads covered

The registry includes ASR, drawing VLM, story/storyboard, the optional Parent Sketch Guide and Teacher Sketch Deck, lesson/activity drafting, optional lesson visuals, optional SAM2 segmentation, per-scene LTX video, consistency validation, Vietnamese TTS, and final video safety. Deterministic drawing preparation, document extraction, and FFmpeg composition remain backend/local worker responsibilities.

Current SRS candidates are not final model choices. In particular, the existing [`../qwen_vision_v2.py`](../qwen_vision_v2.py) is a separate legacy Qwen3-VL dev app and is not used by this SRS v2.3 scaffold.

## Setup for a fresh Modal environment (reference)

The steps below describe initial setup for a new Modal workspace. The current dev workspace has already been authenticated, its environment and Volume v2 resources exist, and the apps above are deployed; do not create duplicate Volumes or Secrets there.

1. Install Modal in a local Python environment, then authenticate with `modal setup` and confirm with `modal token info`.
2. Create a Modal `dev` environment (`modal environment create dev`). Do not create production resources for this scaffold.
3. Create these Volumes as **Volume v2** in `dev` when ready to stage reviewed weights and bounded attempt scratch:
   - `sketch2life-dev-model-weights-v2` — mount read-only in future model functions.
   - `sketch2life-dev-job-scratch-v2` — unique single-writer attempt prefixes only.
4. Create the `sketch2life-dev-huggingface` Secret only if a selected gated checkpoint needs authenticated download. Do not add a token merely to deploy the current no-model skeleton.
5. Put the Modal server token in the ignored local backend environment or runtime secret manager, using [`modal.env.example`](modal.env.example) as a key-name template. Never put it in a mobile/web client or tracked file.
6. From the repository root, deploy the two placeholder apps only after deciding to register them in the Modal `dev` environment:

   ```powershell
   modal deploy --env=dev deployment/modal/srs_v23/l4_app.py
   modal deploy --env=dev deployment/modal/srs_v23/video_app.py
   ```

   The `health` functions are CPU-only deployment checks. The L4/L40S workload functions are intentionally not callable as inference until a model handler, pinned runtime and staging implementation are added and reviewed. Do not use them to test model output.

For temporary code iteration, use `modal serve` only when you later have an approved runnable handler. A persistent deployment is not required for local environment setup.

## Initial hosted model POC: drawing analysis

The approved synthetic POC lives in Modal `dev`, uses one L4 function, and exposes no HTTP endpoint. It pins `Qwen/Qwen2.5-VL-7B-Instruct` to revision `cc594898137f460bfe9f0759e9844b3ce807cfb5`. The public checkpoint does not need a Hugging Face token. The app creates the named Volume v2 resources only if they are absent:

- `sketch2life-dev-model-weights-v2` stores the pinned checkpoint. The download function mounts it read/write; inference mounts it read-only.
- `sketch2life-dev-job-scratch-v2` stages a single synthetic input under its attempt prefix; the acceptance script removes that prefix after the call.

From the repository root, deploy the private app:

```powershell
$modalVenv = Join-Path $env:LOCALAPPDATA 'Sketch2Life\modal-cli'
& (Join-Path $modalVenv 'Scripts\modal.exe') deploy --env=dev deployment/modal/srs_v23/drawing_vlm_app.py
```

Download weights and run the one synthetic smoke call with the same isolated Modal Python environment:

```powershell
$modalPython = Join-Path $env:LOCALAPPDATA 'Sketch2Life\modal-cli\Scripts\python.exe'
& $modalPython features/FEAT-063-system-architecture-rearchitecture/evidence/scripts/run_drawing_vlm_poc.py --download-model
& $modalPython features/FEAT-063-system-architecture-rearchitecture/evidence/scripts/run_drawing_vlm_poc.py --invoke
```

The drawing inference contract returns a candidate subject and visible features with `NEEDS_ADULT_CONFIRMATION`; it is not a safety verdict or accuracy benchmark. GPU use requires a valid payment method, and the checkpoint Volume remains persistent after the function scales to zero, so storage billing continues while the weights are retained. Separate language/audio, FLUX, and Wan candidate apps are documented in the hosting-wave evidence; their POC results do not approve production models or enable product workloads.

## Data transfer boundary

Docker-local MinIO is not reachable from Modal. The eventual backend worker must validate/hash the private MinIO asset, stage a bounded working copy with the Modal SDK into a unique prefix:

```text
sketch2life/{environment}/{job_id}/{generation_id}/{attempt_id}/
```

Pass only the versioned envelope and manifest reference to Modal. Retrieve outputs through the SDK, verify prefix containment, manifest, SHA-256, byte cap, codec/dimensions/duration and required safety coverage, then persist accepted artifacts in private MinIO/PostgreSQL. Delete attempt scratch on terminal completion and sweep unreferenced prefixes. Do not give Modal MinIO credentials, a Docker-network route, or a long-lived local URL.

SRS limits of 48 MiB input, 256 MiB final MP4, a 300-second transfer deadline and 24-hour orphan cleanup are synthetic-demo proposals that still need SDK validation and benchmark. The 48 MiB input cap is enforced by this scaffold contract; it is not a production acceptance claim.

## Runtime and retries

- PostgreSQL remains the durable job/state owner; Redis/RQ is dispatch transport. The backend, not Modal, owns auth, permission, AI Policy budget reservation, billing/quota admission, human gates and stale-result checks.
- The eventual backend dispatcher should use `Function.spawn()`, persist the Modal call ID, and reconcile results. Modal's result retention is temporary; persist application state/artifacts in the system's own stores.
- Each function starts with `max_containers=1`, `min_containers=0`, and an explicit timeout. L4 uses a 300-second scaffold timeout; each L40S scene uses 1,800 seconds as a provisional ceiling. Benchmark these before live work and keep the full job deadline at the SRS limit.
- `retries=0` disables configured exception retries for these functions; Modal can still replay in-flight work after container crashes/preemption. Later handlers must be idempotent, write to the unique attempt prefix, and let the backend accept at most one fenced result. The SRS per-scene technical retry count remains a separate business rule.
- Parent/Teacher sketch generation remains opt-in and uses separate compute caps, never video quota. Lesson/activity suggestion remains disabled until the requesting roles in SRS Q157/Q159 are resolved.

## Setup references

- [Modal getting started](https://modal.com/docs/guide/getting-started)
- [Modal environments](https://modal.com/docs/guide/environments)
- [Modal Volumes](https://modal.com/docs/guide/volumes)
- [Modal secrets](https://modal.com/docs/guide/secrets)
- [Modal GPU configuration](https://modal.com/docs/guide/gpu)
- [Modal asynchronous job processing](https://modal.com/docs/guide/job-queue)
- [Modal retries](https://modal.com/docs/guide/retries)
- [Modal preemption](https://modal.com/docs/guide/preemption)

The original scaffold itself did not create account resources, secrets, weights, handlers, backend integration, or production settings. The later private dev-only model deployments and weight downloads are tracked separately in FEAT-063 evidence above; they do not establish production readiness.
