# Sketch2Life Modal scaffold for SRS v2.3

This folder contains the **dev-only Modal deployment** for the current SRS v2.3 AI workloads. Product dispatch, auth, quota, storage transfer, safety acceptance, and playback remain backend-owned; every `workloads.json` entry stays disabled. The original generic L4/L40S scaffold remains contract-only. Separate private apps implement bounded synthetic POCs for drawing VLM, story/audio, FLUX images, and Wan video feasibility; none is a production model selection.

## Current dev deployment ? 2026-11-05

- The only active FEAT-063 Qwen development profile is `Qwen/Qwen3.5-9B@c202236235762e1c871ad0ccb60c8ee5ba337b9a`. Qwen2.5 is retired from active configuration; older decisions and test reports remain historical.
- Rev45 passed synthetic Qwen3.5 drawing analysis, Parent story/storyboard, Teacher Sketch Deck, lesson suggestion, TTS, and exact-text ASR. These are worker-level results, not production/API readiness. Details: [`AI_NONVIDEO_AI_END_TO_END_20261105.md`](../../../features/FEAT-063-system-architecture-rearchitecture/evidence/AI_NONVIDEO_AI_END_TO_END_20261105.md).
- Rev46A fixed FLUX.3 checkpoint staging by including Diffusers `transformer/` and `vae/` components. One synthetic Parent Sketch Guide and one lesson visual inference passed; both outputs are private DRAFT candidates with human review required. Details: [`AI_QWEN35_FLUX_REV46A_COMPLETION_20261105.md`](../../../features/FEAT-063-system-architecture-rearchitecture/evidence/AI_QWEN35_FLUX_REV46A_COMPLETION_20261105.md).
- The download uses Modal `dev` Secret `huggingface-secret` with required `HF_TOKEN`. Secret values are never read or stored by the runner. Pinned FLUX and Qwen model Volumes remain retained.
- Optional SAM2 remains unverified after its prior GPU-capacity wait. Video was not called; LTX-2.5 remains the SRS target and Wan2.2 is not a substitute.
- All `workloads.json` entries remain disabled. These direct worker checks do not provide authenticated durable product APIs, quota admission, publication, or production safety acceptance. The Rev46A FLUX app is stopped with zero tasks; shared Volumes remain.
- Earlier hosting outcomes are retained as historical records; see [`MODAL_AI_HOSTING_WAVE_20261103.md`](../../../features/FEAT-063-system-architecture-rearchitecture/evidence/MODAL_AI_HOSTING_WAVE_20261103.md).

## Workloads covered

The registry includes ASR, drawing VLM, story/storyboard, the optional Parent Sketch Guide and Teacher Sketch Deck, lesson/activity drafting, optional lesson visuals, optional SAM2 segmentation, per-scene LTX video, consistency validation, Vietnamese TTS, and final video safety. Deterministic drawing preparation, document extraction, and FFmpeg composition remain backend/local worker responsibilities.

Current SRS candidates are not final model choices. In particular, the existing [`../qwen_vision_v2.py`](../qwen_vision_v2.py) is a separate legacy Qwen3-VL dev app and is not used by this SRS v2.3 scaffold.

## Setup for a fresh Modal environment (reference)

The steps below describe initial setup for a new Modal workspace. The current dev workspace has already been authenticated and its environment/Volume v2 resources exist; task-owned apps are stopped after the latest checks. Do not create duplicate Volumes or Secrets there.

1. Install Modal in a local Python environment, then authenticate with `modal setup` and confirm with `modal token info`.
2. Create a Modal `dev` environment (`modal environment create dev`). Do not create production resources for this scaffold.
3. Create these Volumes as **Volume v2** in `dev` when ready to stage reviewed weights and bounded attempt scratch:
   - `sketch2life-dev-model-weights-v2` — mount read-only in future model functions.
   - `sketch2life-dev-job-scratch-v2` — unique single-writer attempt prefixes only.
4. For the gated FLUX.3 checkpoint, create a Modal Secret named `huggingface-secret` with the key `HF_TOKEN`. This Secret is used only by the pinned model-download function; never put its value in source, local tracked files, or client configuration.
5. Put the Modal server token in the ignored local backend environment or runtime secret manager, using [`modal.env.example`](modal.env.example) as a key-name template. Never put it in a mobile/web client or tracked file.
6. From the repository root, deploy the two placeholder apps only after deciding to register them in the Modal `dev` environment:

   ```powershell
   modal deploy --env=dev deployment/modal/srs_v23/l4_app.py
   modal deploy --env=dev deployment/modal/srs_v23/video_app.py
   ```

   The `health` functions are CPU-only deployment checks. The L4/L40S workload functions are intentionally not callable as inference until a model handler, pinned runtime and staging implementation are added and reviewed. Do not use them to test model output.

For temporary code iteration, use `modal serve` only when you later have an approved runnable handler. A persistent deployment is not required for local environment setup.

## Qwen3.5 Modal validation

The active FEAT-063 dev pin is `Qwen/Qwen3.5-9B@c202236235762e1c871ad0ccb60c8ee5ba337b9a`, loaded with Transformers 5.22.1 using `AutoProcessor` and `AutoModelForMultimodalLM`. Synthetic inputs are staged under unique attempt prefixes and removed after terminal outcomes. Rev45 worker results and limits are in the linked execution report above. The profile is for development tests only, not a production default or safety/quality approval.

Qwen2.5 was retired from active FEAT-063 source/configuration by owner direction. Older POCs and evidence remain historical and are not current runtime choices. The existing `../qwen_vision_v2.py` is a separate legacy Qwen3-VL dev app, disabled and not used by this SRS v2.3 scaffold. GPU use incurs Modal charges; shared Volumes persist after apps stop.

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
- Parent Sketch Guide and Teacher Sketch Deck remain session opt-in and use separate compute caps, never video quota. Platform Admin and Teacher may initiate lesson/activity suggestions; Parent can edit authorized drafts only and cannot start generation. All product workloads remain disabled until role enforcement, durable jobs, model access, quality, privacy, quota and safety gates pass.

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

**Rev45 update:** the LMFE Vietnamese Unicode parser fix was deployed and verified with synthetic Qwen3.5 calls for drawing analysis, Parent story/storyboard, Teacher Sketch Deck, and lesson-plan suggestion. Synthetic TTS and exact-text ASR also passed. See [`AI_NONVIDEO_AI_END_TO_END_20261105.md`](../../../features/FEAT-063-system-architecture-rearchitecture/evidence/AI_NONVIDEO_AI_END_TO_END_20261105.md). Both task-used apps are stopped with zero tasks; model and scratch Volumes remain. FLUX.3 Guide/visual calls still need the owner-managed HF Secret; SAM2 was not re-dispatched and its last attempt failed to receive GPU capacity. No video call or production workload enablement.
