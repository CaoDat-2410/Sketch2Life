# Plan Rev46A — FLUX.3 component staging fix and failed-flow retest

**Approval status:** APPROVED by the owner's direct instructions to fix the non-video AI flows, ensure they run, use Qwen3.5, and test the supplied Modal/Hugging Face Secret setup.
**Execution status:** COMPLETE
**Date:** 2026-11-05 (Asia/Saigon)
**Feature:** FEAT-063 — system architecture rearchitecture

## 1. Source and observed failure

Canonical source remains `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`; active FEAT-063 Qwen workloads use only the pinned Qwen3.5-9B development profile under Rev46/D-142.

Rev46 successfully staged the pinned FLUX.3 and Qwen3.5 prompt-upsampler source checkpoints with the owner-created `huggingface-secret` Secret. Both first image inferences terminated in the Diffusers FLUX pipeline with `AttributeError: 'NoneType' object has no attribute 'dtype'` because the checkpoint filter staged the original root files but omitted the Diffusers component weights under `transformer/` and `vae/`. The app was stopped with zero tasks. No model IDs, API contracts, or SRS business rules are implicated.

The official Diffusers FLUX.3 docs use the modular pipeline and component folders; the official BFL repository lists the `transformer/` and `vae/` directories. Sources: https://huggingface.co/docs/diffusers/v0.42.0/api/pipelines/flux3 and https://huggingface.co/black-forest-labs/flux-3-image-klein/tree/main.

## 2. Objective

Stage and verify every Diffusers component required by the pinned FLUX.3 ModularPipeline, keep Qwen3.5 as the only active Qwen profile, and make one post-fix inference attempt for each image workload that failed terminally in Rev46.

## 3. Scope

1. Extend the FLUX checkpoint allowlist and completeness verifier to include `transformer/` and `vae/` component configs/weights. If a prior manifest exists but its checkpoint is incomplete under the updated verifier, continue staging missing files instead of reporting `already_present`.
2. Keep `huggingface-secret` with required key `HF_TOKEN`, FLUX.3 Image Klein and its pinned Qwen3.5 prompt upsampler, current opaque worker/API envelope, and all workload flags disabled.
3. Deploy to Modal `dev`; run one checkpoint-staging call for the newly required component files. Use the existing Volume; do not delete Volumes or checkpoints.
4. Only if staging and integrity checks pass, run one new synthetic Parent Sketch Guide inference and one new synthetic lesson-visual inference. These are the only post-fix attempts because their Rev46 calls both failed terminally. Do not retry unknown results; do not re-run any successful Qwen, TTS, ASR, or other workload.
5. Validate image bytes, dimensions, hashes, private DRAFT/review status, and lesson revision/content-hash lineage. Preserve outputs and timing in new Rev46A evidence. Stop the task-owned app and verify zero tasks.

## 4. Acceptance criteria

- **AC-46A.1:** The Modal Volume contains the pinned Diffusers transformer, VAE, text encoder, modular index, and prompt-up sampler components required by the verifier.
- **AC-46A.2:** Worker initialization fails closed if the transformer or any required component is absent; the FLUX request reaches image generation only after checkpoint verification.
- **AC-46A.3:** The post-fix Parent Sketch Guide and lesson visual calls each either pass their complete worker/output contract or produce a precise terminal failure; no call is duplicated.
- **AC-46A.4:** No Qwen story/drawing/deck/suggestion, speech, SAM2, or video inference is called. Token values are never read or persisted.
- **AC-46A.5:** The task-owned Modal app is stopped with zero tasks; repository security validation, focused tests, Ruff, compile, and diff checks pass or have exact findings recorded.

## 5. Explicit exclusions

No model substitution, Qwen2.5 runtime use, FLUX checkpoint deletion, Volume deletion, product API route creation, production enablement, real child data, video/SAM2, successful-workload retests, commit, push, or merge.

## Execution closeout ? 2026-11-05

All acceptance criteria passed. Focused tests: 27 passed; Ruff and compileall passed. The FLUX checkpoint staging call completed in 61.472s. Parent Sketch Guide passed once in 65.772s and lesson visual passed once in 47.206s; both returned verified PNG metadata and private DRAFT/review-required output. The worker app was stopped and Modal reported zero active tasks. Shared model/scratch Volumes were preserved. Full results: `evidence/AI_QWEN35_FLUX_REV46A_COMPLETION_20261105.md`.
