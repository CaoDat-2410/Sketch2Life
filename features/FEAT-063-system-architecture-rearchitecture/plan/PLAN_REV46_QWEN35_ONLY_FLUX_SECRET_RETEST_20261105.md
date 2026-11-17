# Plan Rev46 ? Qwen3.5-only active profile and FLUX Secret retest

**Approval status:** APPROVED by the owner's direct instruction  
**Execution status:** COMPLETE (Qwen profile and FLUX setup completed; initial terminal image failures were repaired under Rev46A)  
**Date:** 2026-11-05 (Asia/Saigon)  
**Feature:** FEAT-063 ? system architecture rearchitecture

## 1. Owner direction and source of truth

The owner directly requested to remove Qwen 2 from active use and use Qwen 3.5, and supplied a Modal/Hugging Face Secret example for implementation and testing. The owner-created Modal Secret `huggingface-secret` is present in environment `dev`; its contents have not been inspected. The sample's Stable Diffusion model is not the product model selection; FEAT-063 image generation remains pinned to FLUX.3 under the canonical SRS.

Canonical SRS: `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` (current pre-edit synchronized digest `6BADEBAAD6C28239CA9B759CF17C57A0405D7242B45F3411F40B7E8FEBDC8381`).

## 2. Objective

Retire Qwen2.5 from the active FEAT-063 model profile, make Qwen3.5-9B the only Qwen model in the active development profile, adapt the FLUX worker to the Modal Secret the owner created, and test only the still-unverified FLUX image workloads once each.

## 3. Scope

1. Update the active FEAT-063 SRS model rows and clarification so Qwen3.5-9B is the sole active Qwen development model. Mark Qwen2.5 as retired from active use. Preserve earlier evidence and decisions as historical records; do not erase test provenance.
2. Update `deployment/modal/srs_v23/flux_image_app.py` to reference Modal Secret `huggingface-secret` in `dev`, requiring key `HF_TOKEN`. Preserve token injection through Modal Secrets and use it only for downloading the pinned FLUX.3 Image Klein and its prompt upsampler. Do not read, print, copy, or store the Secret value anywhere else.
3. Deploy the FLUX dev app, run one checkpoint-download call, then run one synthetic `parent.sketch-guide.generate` and one synthetic `lesson.visual.generate` call. Validate each worker response and generated image metadata. The outputs are synthetic candidates only and do not become product assets.
4. Use fresh call IDs and scoped FEAT-063 evidence. Do not re-run Qwen3.5, TTS, or ASR workloads that passed in Rev45. Do not retry any ambiguous/unknown result. Stop the task-owned FLUX app after the checks; preserve the shared model and scratch Volumes so weights are not downloaded again.
5. Keep all production workload switches disabled. No LTX/video, no real child data, no token-value access, and no commit/push/merge.

## 4. Acceptance criteria

- **AC-46.1:** Active FEAT-063 SRS/runtime model references use Qwen3.5-9B only for Qwen workloads; Qwen2.5 is explicitly retired from active use and historical evidence remains intact.
- **AC-46.2:** The FLUX app resolves the existing `huggingface-secret` in Modal `dev` and requires `HF_TOKEN`; no secret value enters source, logs, local env files, or evidence.
- **AC-46.3:** The two pinned FLUX.3 checkpoints stage and pass integrity/revision verification, or an exact terminal access/download blocker is recorded.
- **AC-46.4:** Each unverified image workload is called once with synthetic input and returns a contract-valid candidate, or a precise terminal failure is recorded. No repeated successful inference is run.
- **AC-46.5:** Repository security validation, focused tests, lint/compile, and diff checks pass or have exact findings recorded; task-owned Modal app is stopped with zero tasks and Volumes are retained.

## 5. Explicit exclusions

- Stable Diffusion 1.5 substitution; FLUX.3 remains the active SRS image candidate.
- Video workloads, optional SAM2 retry, retesting Qwen3.5/speech successes, production enablement, new product API routes, and real personal/child data.
- Deleting historical evidence or shared Modal Volumes.


## Execution closeout ? 2026-11-05

- Active FEAT-063 Qwen workload configuration uses the pinned Qwen3.5-9B profile only. Qwen2.5 remains only in historical evidence and retained shared model storage.
- Rev46 initially staged the FLUX root checkpoint and prompt upsampler but omitted Diffusers `transformer/` and `vae/`; both image calls failed terminally. The fix and bounded post-fix rerun are recorded in Plan Rev46A and `evidence/AI_QWEN35_FLUX_REV46A_COMPLETION_20261105.md`.
- No successful Qwen3.5, TTS, or ASR workloads were repeated. No video, SAM2, or product API call was made in this plan.
