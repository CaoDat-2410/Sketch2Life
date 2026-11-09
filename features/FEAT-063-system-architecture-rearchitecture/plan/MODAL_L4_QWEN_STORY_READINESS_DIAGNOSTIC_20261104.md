# Modal L4 Qwen story readiness diagnostic

**Status:** APPROVED / IN PROGRESS  
**Date:** 2026-11-04  
**Feature:** FEAT-063  
**Worktree:** `codex/feat063-modal-backend-completion-20261103`

## Goal

Separate Modal GPU scheduling delays from Qwen checkpoint, model-load, and story-inference failures for the current synthetic story worker. Do not infer that a client wait timeout means inference failed.

## Approved scope

1. Read the existing Modal `dev` app and model-volume metadata without exposing local credentials.
2. Start no more than one temporary L4 container at a time using an ephemeral `modal run -` diagnostic app. `modal shell` is unsupported on the Windows host. The probe must match the deployed worker's Python 3.11 image pins (`torch==2.7.1`, `transformers==4.53.0`, `accelerate==1.8.1`), L4 GPU, 4 CPU, 32 GiB memory, and read-only Qwen2.5 checkpoint Volume.
3. Run a model-readiness probe before story inference: GPU visibility, exact model/revision marker, required local checkpoint files, tokenizer/model load, and load duration. This is an internal container probe; the AI worker does not expose an HTTP `/health` route.
4. Only after the readiness probe reports `READY`, deploy the existing language/audio worker if needed and issue at most one new synthetic Parent story request through its existing story worker. Use a fresh job/generation/attempt and a new evidence directory. Wait at most 1,800 seconds and do not retry an unknown call.
5. Record scheduling state, timestamps, container/function/call IDs, model-load result, output validation, and the final Modal app/task state.
6. Stop any task-owned Modal `dev` app after evidence is captured. Retain shared Volumes and checkpoints.

## Exclusions

- No video generation; no real child or personal data.
- No concurrent GPU workers, persistent `min_containers`/`max_containers` change, GPU/provider fallback, or production enablement.
- No model checkpoint selection or promotion; this diagnoses the currently deployed Qwen2.5 story candidate only.
- No code, SRS, business-rule, schema, API, secret, or `.env` changes in this diagnostic slice.
- No retry of any earlier timed-out or unknown call; no commit, push, or merge.

## Acceptance criteria

- The preflight result distinguishes `WAITING_FOR_GPU`, `CHECKPOINT_MISSING_OR_MISMATCHED`, `GPU_UNAVAILABLE`, `MODEL_LOAD_FAILED`, and `READY` using observed evidence.
- Story inference is dispatched only when preflight is `READY`.
- The single story attempt is recorded as `SUCCEEDED`, a concrete worker/model error, or `UNKNOWN_NO_RETRY`; its schema and lineage are checked if output arrives.
- The final report states whether the failure is scheduling/capacity, checkpoint/readiness, model load/runtime, inference/validation, or client observation.
- All task-owned Modal apps are stopped and have zero active tasks at closeout.

## Verification plan

- Confirm the correct app/function/model revision from Modal metadata and the canonical FEAT-063 SRS/approved synthetic candidate records.
- Inspect the exact checkpoint revision directory and marker without downloading model weights to the workstation.
- Use the same dependency pins, L4 resource profile, read-only model Volume, and exact `AutoTokenizer` / `AutoModelForCausalLM` load settings as the current worker. The probe app is temporary and is not a production or persistent deployment.
- Run the existing synthetic story worker contract with a fresh fixture only after readiness.
- Save task-local evidence under `features/FEAT-063-system-architecture-rearchitecture/evidence/`.

## Risks and limits

- Modal may still queue the temporary L4 container; if no container is scheduled, the model has not been tested.
- A successful standalone model load does not prove the full worker contract or product workflow; the separate synthetic story call covers the worker if capacity permits.
- The direct Modal worker test does not prove Parent HTTP API integration or production readiness.
