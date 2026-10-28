# Lightning Vision V2 portability assessment for Modal

- Date: 2026-10-28 (Asia/Saigon).
- Request: owner asked to reread the project's Lightning configuration and assess whether it can be moved to a Modal endpoint.
- Method: source inspection and current first-party Modal documentation; no dependency installation, credentials, provider calls, model downloads or deployment.
- Verdict: technically feasible for the existing Vision/ASR/SAM FastAPI service after packaging and configuration work. Runtime stability, combined GPU memory, latency, output quality and cost on Modal are NOT_MEASURED.
- Authorization boundary: this is review evidence. FEAT-038 plan revision 1 and its approval remain limited to the existing Lightning launcher/import fix. A Modal implementation/deployment needs its own scoped plan and approval; this review does not select a new production provider.

## Source and authority

Read `AGENTS.md`, `docs/governance/WORKFLOW.md`, `docs/governance/APPROVAL_POLICY.md`, `docs/context/PROJECT_CONTEXT.md`, `docs/context/SOURCE_REGISTER.md`, FEAT-038 context/plan/approval and ADR-0007. Current source remains the basis for this portability assessment; current canonical SRS v3.1 is not claimed to be fully implemented by this legacy AI service. Windows remains the lightweight inspection environment.

## Findings from the repository

| Concern | Existing implementation | Portability implication |
|---|---|---|
| Entrypoint | `tools/start_lightning_vision_v2.sh` launches `tools.lightning_vision_v2_server:app` with Uvicorn | Ordinary FastAPI ASGI service; this entrypoint does not require a Lightning SDK. A Modal ASGI wrapper can preserve the existing routes. |
| Vision | Qwen3-VL-8B-Instruct, CUDA BF16, persistent subprocess; profile pins the model revision | Preserve the exact profile, processor and schema mapping, not just the model name. |
| ASR | Local faster-whisper large-v3-turbo, CUDA FP16, beam size 5 | Stage the converted Whisper model and matching runtime libraries explicitly. |
| Segmentation | SAM2.1 Hiera small, separate SAM source checkout, checkpoint and YAML configuration | Package the SAM source and verify config/checkpoint resolution. |
| Filesystem | Launcher defaults to a Lightning Studio directory layout; model downloads are disabled for Qwen | Override paths and mount pre-staged model weights. An empty Modal Volume cannot satisfy these settings. |
| Dependencies | `scripts/lightningai/setup.sh` installs `backend[dev,whiteboard-renderer]` only | Copying setup does not install the GPU extras or SAM source. Build a reproducible Linux/CUDA/cuDNN image. |
| Authentication | Server reads `LIGHTNING_DEV_AUTH` at import and verifies a Bearer header; backend sends that header | Inject a Modal Secret before importing the server. Keep provider URL/token backend-only. Modal proxy authentication, if enabled, needs compatible request headers in addition to the existing server check. |
| Backend transport | `UrllibJsonTransport` accepts a generic HTTPS base URL and appends each custom path | A local development trial can reuse the transport with the custom Modal App URL if route/body/auth contracts remain identical. The provider setting is still named `lightning_dev`; there is no registered `modal` provider. |
| Production policy | `Settings.enforce_deployment_provider_policy()` requires Runpod in production | Changing a URL is insufficient for a supported production migration. A provider-policy/architecture change needs separate approval. |

GPU extras currently pin Torch 2.8.0, Transformers 4.57.6, Accelerate 1.10.1, qwen-vl-utils 0.0.14, faster-whisper 1.2.1 and CTranslate2 4.8.1 in `backend/pyproject.toml`. This assessment did not install or verify those packages on Modal.

Relevant routes include `/v2/vision`, `/v1/asr`, `/v2/localize`, `/v2/rig/segment`, activity ranking, preference classification and Pixi show planning. Preserve the matching JSON request/response schemas and version/profile hashes. The old V1 `/v1/vision` route belongs to `tools/lightning_provider_server.py`, not the current Vision V2 app.

## Modal dashboard Endpoints versus a custom HTTP endpoint

The previous chat explanation conflated the dashboard Endpoints product with custom App Web Functions. Current Modal documentation distinguishes them:

- Managed Shared/Dedicated Endpoints serve supported models or compatible custom weights through standard OpenAI/Anthropic-compatible APIs. The current supported-model list does not list this project's Qwen3-VL-8B-Instruct, Whisper or SAM2.1 bundle. Absence from that list does not prove that every custom serving recipe is impossible, but it does not establish compatibility either.
- The existing backend sends custom contract envelopes to its own routes. A managed `/v1/chat/completions` API is not a replacement for `/v2/vision`, `/v1/asr` or `/v2/rig/segment`. Even a supported vision model would need a new adapter and output/provenance validation.
- Deploying the existing FastAPI app through `@modal.asgi_app()` produces an HTTP API under a Modal App while retaining these custom routes. This is the smallest proposed migration for the existing service.

## GPU memory and timing

The Qwen-only historical study in `features/FEAT-003-multimodal-understanding/evidence/P2_T3_PHASE_B_B4_DIRECTION_A_V3_PHASE6_EXECUTION_RECORD.md` records a 17,180 MB peak VRAM sample on Lightning L4. It is not a benchmark of the combined Qwen/ASR/SAM service. The current server caches all three models; Qwen and SAM operations share `_QWEN_MODEL_REQUEST_LOCK`, but ASR has separate state/locking. Serializing requests does not release cached model memory.

Use an isolated Qwen L4 trial as a baseline only, or evaluate a larger-memory GPU for the bundled service. First measure cold start, peak VRAM after all enabled models have loaded, warm latency and sequential/concurrent requests before claiming that a given GPU is sufficient. Initially bound containers and concurrency to control both memory and compute spend; that is a proposed trial configuration, not a measured optimum.

Backend requests default to 120 seconds. Activity ranking is additionally capped at 30 seconds and Pixi show planning at 60 seconds in `backend/src/sketch2life/interfaces/http/app.py`. Lazy model loading makes these routes sensitive to scale-to-zero startup. Modal Web Functions return a 303 result redirect after 150 seconds; that is not proof that the current backend or application deadline can wait indefinitely. Measure the complete path, including model loading and queueing. For long jobs use an explicit submit/status/result contract rather than relying on redirects or merely increasing a worker timeout. Warm containers can reduce startup latency and incur idle resource costs.

## Separate video scope

`tools/lightning_whiteboard_provider.py` is a different app from the Vision V2 entrypoint. Its story pipeline passes local file paths between stages and defaults to temporary package storage. Wan2.2 additionally requires an existing repository, checkpoint and Python environment and can run for much longer than a synchronous Web Function request. Autoscaling does not make those files durable or shared between containers. Assess durable artifact references and asynchronous job handling separately before moving the video pipeline. This review does not claim the complete Lightning environment can be copied as one endpoint.

## Candidate implementation plan and acceptance criteria

This is a proposed follow-up, not an approved implementation plan:

1. Create a separately scoped Modal development feature and record approval for its packaging, synthetic smoke run, GPU type, concurrency and compute cap.
2. Package the current backend modules and FastAPI server in a pinned Python/Linux/CUDA image with the required extras and SAM source. Stage exact checkpoint revisions into a model Volume; supply only runtime secrets.
3. Expose the existing app with `modal.asgi_app`, preserve auth/routes/contracts and bound scale/concurrency. Point a local backend trial at the custom App base URL.
4. Verify missing/wrong auth rejection, a synthetic Vision V2 request, ASR and optional SAM requests, existing contract/profile identity, temporary-media cleanup and shutdown of the Qwen subprocess.
5. Measure cold/warm latency, all-enabled-model peak VRAM, timeout/error behavior, queueing and spend. Record sanitized receipts here or in the approved follow-up feature. Production provider changes and video migration remain separate.

Acceptance requires actual Modal evidence for the enabled workloads and declared budget; static inspection alone cannot establish MODAL_TEST_PASS, model quality or production readiness.

## Primary documentation checked on 2026-10-28

- [Modal Endpoints](https://modal.com/docs/guide/endpoints): managed serving modes, standard APIs and dashboard creation.
- [Supported models](https://modal.com/docs/guide/supported-models): current managed catalog, which must be rechecked before implementation.
- [Dedicated Endpoints](https://modal.com/docs/guide/dedicated-endpoints): compatible custom weights and generated source.
- [Web Functions](https://modal.com/docs/guide/webhooks): existing ASGI apps, lifecycle and authentication.
- [Storing model weights](https://modal.com/docs/guide/model-weights): durable model Volumes and loading lifecycle.
- [Request timeouts](https://modal.com/docs/guide/webhook-timeouts): 150-second response/redirect behavior and explicit polling pattern.
- [GPU acceleration](https://modal.com/docs/guide/gpu): selectable GPU resources.
- [Cold start performance](https://modal.com/docs/guide/cold-start): model initialization, warm capacity and its resource cost.

## Verification

- Read-only inspection used `rg`, `rg --files` and `Get-Content` against tracked source/configuration and feature records. No ignored `.env` or credential files were read.
- An independent source audit confirmed the launcher, dependency gap, memory limitation and separate video service.
- No live Lightning/Modal request, GPU allocation, package installation, model download or benchmark was performed. Existing FEAT-038 remote-startup gate remains pending.
- Documentation consistency checks are recorded in the feature evidence index after execution.
