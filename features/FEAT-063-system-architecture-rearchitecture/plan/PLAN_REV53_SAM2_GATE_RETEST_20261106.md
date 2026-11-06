# FEAT-063 Plan Rev53 — one-shot SAM 2.1 gate retest

**Date:** 2026-11-06 (Asia/Saigon)
**Canonical product source:** FEAT-063 SRS v2.4-draft, especially the image preparation and optional segmentation requirements in §§6.3, 6.5, 31.12 and the as-built notes in §32.
**Feature branch:** `feature/feat063-modal-ai-reliability-20261106`, based on `dev` at `0fc773fafeb6f5443538f283cb891c67d379d9c6`.

## Baseline and cause

The Rev52 SAM2 attempt returned `MODAL_WORKLOAD_NOT_ALLOWED` before checkpoint verification or GPU inference. `drawing_segment_app.py` calls `parse_worker_input(..., execution_group="l4")`, while `contracts.py::L4_WORKLOADS` omits `drawing.segment`. The worker has its own exact workload check, but that check is reached only after envelope parsing. This is a contract allowlist mismatch, not a checkpoint, model, inference, or GPU-capacity result.

The SRS describes SAM 2.1 segmentation as optional after an image-preparation POC. It does not make segmentation a required V1 feature. The product workload registry must therefore remain disabled after this one-shot feasibility test.

## Goal

Correct the narrow worker-envelope gate and make one bounded synthetic SAM 2.1 inference attempt in Modal `dev`, after CPU-side checkpoint readiness succeeds. Record a verifiable mask result or a stage-specific failure reason, then stop the task app.

## Scope

1. Add only `drawing.segment` to the Modal L4 envelope allowlist used by the dedicated SAM2 worker. Add a focused contract test proving the L4 parser accepts this workload and the video execution group still rejects it.
2. Keep `deployment/modal/srs_v23/workloads.json` `enabled: false`; this task does not enable product dispatch, add an API route, or promote SAM2 beyond an optional development candidate.
3. Use the existing synthetic butterfly drawing fixture, record its SHA-256, stage it under a fresh attempt prefix in the dev scratch Volume, and preserve the source file unchanged.
4. Deploy only `sketch2life-srs23-drawing-segment-dev`. Run the CPU checkpoint preflight once; verify the pinned SAM 2.1 repository revision, checkpoint manifest, byte size and hash before any GPU call. If preflight does not reach a verified terminal result, do not dispatch inference.
5. If preflight passes, call `segment-synthetic-drawing-candidate` at most once with the configured ordered GPU candidates `L40S`, `L4`, `A10`. Wait up to 1,800 seconds for the call result while keeping the worker execution timeout at its existing 600 seconds and retries at zero. Do not extend execution timeout without evidence that a started worker was cut off by that timeout.
6. Validate output schema, attempt lineage, source hash, PNG bytes, output size/hash and that the original synthetic source remains unchanged. Record image quality as a feasibility observation only; no mask is promoted or used to replace the source.
7. Save dispatch intent, safe worker phase logs, checkpoint verification, call timing, outcome, output artifact/hash and cleanup evidence under `evidence/sam2_gate_retest_20261106/`. Update workload registry notes, feature context, decisions, source register and status with the measured result while keeping the registry disabled.
8. Stop the Modal app and verify there are no task-owned active calls or containers. Preserve shared model/scratch Volumes and all existing evidence.

## Acceptance criteria

- **AC53.1 Gate:** the parser accepts `drawing.segment` for the L4 envelope and continues rejecting it for the video execution group; no unrelated workload is added.
- **AC53.2 Product safety:** `workloads.json` keeps `drawing.segment.enabled` false; no public or authenticated product API is added; no production switch changes.
- **AC53.3 Preflight:** the pinned checkpoint is either verified with manifest/hash/size evidence before inference, or the run stops with a safe, stage-specific preflight failure and no GPU dispatch.
- **AC53.4 Bounded inference:** at most one GPU call is dispatched, with no automatic retry and no change to the 600-second worker execution timeout. Queue wait, worker start, model load and inference are distinguishable in the final result.
- **AC53.5 Output/provenance:** success requires valid worker output and derived-mask metadata whose source lineage/hash match the synthetic input; the input remains unchanged. Otherwise record terminal/unknown failure stage without claiming a mask result.
- **AC53.6 Cleanup/evidence:** app and calls are stopped/terminal, full evidence is stored in the feature folder, and shared Volumes are preserved.
- **AC53.7 Validation:** focused tests, Ruff/compile and `git diff --check` pass; `python tools/validate_repository_security.py` passes before each local conventional commit. No push is included.

## Failure handling and limits

- A failure before `worker_started` is classified as dispatch, container startup, GPU admission or unknown based on the available safe Modal events; it is not called an inference timeout.
- A worker failure records only allowlisted phase/error fields, not raw exception text, input image bytes or model output content.
- A single GPU run cannot establish mask quality across drawings or age groups. Any successful output remains a synthetic POC candidate requiring later visual review and a separately approved quality/safety gate.
- If GPU scheduling does not yield a worker within the bounded wait, cancel/confirm the call where Modal permits and stop without retrying.

## Explicit exclusions

No real child artwork/profile/media, product API integration, quota or billing changes, production enablement, video work, GPU timeout increase without worker-timeout evidence, repeated GPU inference, broad dependency/image refactor, secret-value access, shared database write, Volume/checkpoint deletion, merge, push or history rewrite.
