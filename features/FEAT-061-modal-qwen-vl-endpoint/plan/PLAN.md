# FEAT-048 Modal Qwen3-VL development endpoint

- Status: REVIEW
- Plan revision: 1
- Implementation status: REVIEW

## Goal

Add a backend-only Modal App that serves the project's existing Qwen3-VL Vision V2 HTTP contract, while keeping SAM2.1 and every other inference route out of the deployed App.

## Scope

- Reuse `tools.lightning_vision_v2_server.vision_v2` and the existing V2 request/result contracts rather than duplicate model or mapping logic.
- Expose only `GET /health` and authenticated `POST /v2/vision` through a custom Modal ASGI Web Function. The dashboard's model-catalog Endpoints API is not this custom route.
- Configure the existing approved candidate `Qwen/Qwen3-VL-8B-Instruct` (Qwen3-VL 8B), revision `0c351dd01ed87e9c1b53cbc748cba10e6187ff3b`, BF16, and the repository-pinned `vision-qwen` dependencies.
- Read model files from a named read-only Modal Volume. Do not download or add weights to the repository implicitly.
- Inject `LIGHTNING_DEV_AUTH` using a named Modal Secret. Set model path/device through explicit environment values, with downloads disabled.
- Start with one L40S container maximum, scale to zero, serialize inference through the existing handler, and set finite startup/execution limits.
- Record setup instructions, provider boundary, accepted route list, and pending remote validation in feature-local evidence and context.
- Preserve the existing Lightning launcher/service, SAM2.1 source and checkpoint configuration, backend contracts/provider selection, and production Runpod policy.

## Non-goals

- Creating cloud Modal resources, uploading checkpoints, entering credentials, deploying the App, starting a GPU or calling a live provider.
- Changing model profiles, prompts, decoding, V1 or V2 schemas, model scoring, or the backend's `lightning_dev`/Runpod selection.
- Claiming production readiness, model quality approval, or adopting Modal as a production provider. FEAT-003's quality gate remains `NOT_ENOUGH_EVIDENCE` / `QUALITY_NOT_READY` for the Qwen profile.
- ASR, SAM2.1, segmentation/localization, video/Wan2.2, mobile calls, real child data, or backend/mobile changes.

## Steps

1. Record the owner-directed scope and acceptance criteria; then approve this exact plan revision.
2. Add the narrow Modal ASGI wrapper and deployment image/resource/Volume/Secret configuration.
3. Add operator instructions for creating the empty model Volume, uploading the exact checkpoint directory, creating the auth Secret, and running a local Modal serve/deploy command.
4. Update context, decisions, source register, evidence index, and status. Report remote runtime checks as pending until they can be executed by an authorized account with a compute cap.

## Acceptance criteria

1. The app route table declares only `/health` and `/v2/vision`; no SAM2.1, ASR, video, or Lightning management route is exposed.
2. `/v2/vision` uses the existing authenticated handler and preserves the `LightningVisionRequestV2` 2.0 wire contract and result/profile provenance.
3. The Modal image selects Python 3.12 and installs the existing exact Qwen extra pins from `backend/pyproject.toml`, without installing SAM/ASR extras or copying model weights.
4. The app mounts a named model Volume read-only at the configured Qwen path, requires the named runtime secret, sets BF16/CUDA behavior through the existing server, and never fetches missing weights automatically.
5. The app requests a single L40S with a one-container cap, scale-to-zero behavior, and finite start/compute limits. No live Modal resource is created as part of this local configuration change.
6. Feature evidence identifies the exact model/revision and clearly states that Modal deployment, GPU compatibility, peak VRAM, cold/warm latency, auth, and quality have not been verified remotely.

## Risks and mitigations

- Qwen is 8B and BF16. Historical Qwen-only L4 peak memory is 17,180 MB; this is not Modal evidence. Start with a 48 GB L40S and one container, then measure actual peak memory and latency before changing capacity.
- The Qwen candidate did not meet the prior held-out quality threshold. Restrict this endpoint configuration to synthetic development and keep any product/production promotion outside this feature.
- Modal Web Function HTTP requests have a 150-second platform limit. Existing backend calls use 120 seconds and the first model request may load weights. A real request under the production-shaped timeout remains a blocking acceptance check before integration.
- The account must supply a valid GPU billing method. Setup commands are documentation only; no Modal cloud operation runs from this task.
- The registered Secret must contain `LIGHTNING_DEV_AUTH`; no secret value belongs in repository files or shell history.

## Verification plan

- Inspect the route allow-list, model/profile/revision values, package extras, path mapping, mount read-only option, secret reference, and autoscaling/time limits.
- After a separately authorized account-side smoke run: verify 401/503 behavior, `/health`, one synthetic `/v2/vision` contract response, no SAM route, and capture sanitized cold/warm latency, container GPU peak memory, and cost.
- Do not call remote models or run an additional Qwen quality experiment under this plan.

## Evidence plan

Store implementation notes and copy/paste-safe account setup instructions in this feature's `evidence/` directory. Do not include model artifacts, real image/audio inputs, secrets, raw model output, or local absolute paths.

Implementation is blocked until `approvals/TASK_APPROVAL.md` says `APPROVED` for this plan revision.
