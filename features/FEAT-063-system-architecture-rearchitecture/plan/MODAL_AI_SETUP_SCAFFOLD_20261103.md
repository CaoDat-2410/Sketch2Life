# FEAT-063 Modal AI setup scaffold — 2026-11-03

## Status and authority

- Status: PLANNED; implementation requires the exact task approval recorded in `approvals/TASK_APPROVAL.md`.
- Feature: FEAT-063, using `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` v2.3-draft as the canonical product/AI workflow source.
- Request: owner instruction on 2026-11-03: “tạo mấy đó cho tôi đi, sau đó tôi sẽ setup env sau”.
- Purpose: prepare repository-owned Modal configuration and documentation so the owner can create the Modal dev environment and secrets later.
- Model/hosting decisions: do not resolve pending SRS model candidates, licenses, revisions, image-generation roles, or production settings in this task.

## Approved work proposal

Create a separate SRS v2.3 Modal scaffold under `deployment/modal/srs_v23/` that:

1. Enumerates every AI workload in the current SRS and records proposed execution group, current candidate/model state, input-data restrictions, quota/accounting owner, and implementation readiness.
2. Defines a small versioned, path/hash-only worker envelope. Functions must reject malformed or unknown workloads and must never report AI success until a real workload handler is implemented.
3. Defines two dev-only Modal Apps: an L4 stage scaffold and an L40S video-scene scaffold. Both scale to zero, start with `max_containers=1`, and have explicit bounded invocation timeouts. Model downloads, weights, provider secrets, public HTTP endpoints, and real inference are not part of this task.
4. Provides placeholder-only environment configuration and an owner-facing setup guide for Modal CLI, dev environment, app deployment, model/scratch Volumes, Secret names, and later backend connection.
5. Preserves the existing legacy Qwen3-VL Vision V2 Modal app unchanged and clearly labels it as separate from the SRS v2.3 model baseline.
6. Updates FEAT-063 context/decision/status/source records, the global source register, and adds task-local evidence.

## Exact proposed file scope

- Create `deployment/modal/srs_v23/README.md`.
- Create `deployment/modal/srs_v23/workloads.json`.
- Create `deployment/modal/srs_v23/contracts.py`.
- Create `deployment/modal/srs_v23/l4_app.py`.
- Create `deployment/modal/srs_v23/video_app.py`.
- Create `deployment/modal/srs_v23/modal.env.example`.
- Create this plan and `evidence/MODAL_AI_SETUP_SCAFFOLD_20261103.md`.
- Append one approval entry to `approvals/TASK_APPROVAL.md` and additive updates to `DECISIONS.md`, `CONTEXT.md`, `SOURCE_REGISTER.md`, `status/STATUS.md`, and `docs/context/SOURCE_REGISTER.md`.

No other source paths are in scope without a new plan and approval.

## Acceptance criteria

- AC1: Workload registry covers ASR, drawing VLM, story/storyboard, Parent Sketch Guide, Teacher Sketch Deck, lesson/activity drafting, lesson visuals, optional segmentation, per-scene video, consistency, Vietnamese TTS, and final safety.
- AC2: Registry states which values are SRS candidates, optional, unresolved, or not implemented; it does not promote a model candidate to an approved default.
- AC3: Versioned input/output schemas use opaque job/generation/attempt identifiers, bounded relative asset references, and hashes; no raw media, local MinIO endpoint, child name/profile identifier, Firebase token, or payment data is part of function arguments.
- AC4: Modal app entrypoints are dev-only scaffolds with explicit L4/L40S configuration, scale-to-zero, bounded container count, and fail-closed `NOT_CONFIGURED` behavior.
- AC5: The guide explains that local MinIO cannot be mounted directly by Modal, describes bounded SDK/Volume staging and cleanup, and gives the owner exact next steps without asking for or writing credentials.
- AC6: `modal.env.example` contains placeholders only; no real `.env`, Modal token, model token, or secret is added or changed.
- AC7: Existing legacy Modal source, backend configuration/provider selection, SRS, schema/migrations, APIs, and AI business behavior remain unchanged.
- AC8: Evidence records the exact changed files, source basis, verification performed, and the fact that no Modal account, remote deployment, model call, GPU, product test, or child data was used.

## Verification

- Review the exact diff against the allowlist and current FEAT-063 SRS.
- Run `git diff --check` and the repository security validator after changes; do not run product tests or Modal commands for this task.
- Inspect all environment examples for placeholder-only values and inspect the worker contract for forbidden payload fields.
- No claim of runnable inference, model quality, deployment, or environment readiness is permitted.

## Explicit exclusions

- Selecting or benchmarking model checkpoints or runtime/library versions.
- Implementing inference handlers, prompt templates, model weights, API/backend adapters, durable-job integration, quota admission, or storage transfer code.
- Altering `deployment/modal/qwen_vision_v2.py`, backend settings, provider selection, Docker Compose, actual `.env` files, SRS/ADR content, database, migration, or API contracts.
- Creating Modal resources/secrets, invoking `modal setup`, `modal serve`, `modal run`, or `modal deploy`; GPU spend; provider calls; real child data; commit or push.

## Risks and limits

- SRS v2.3 and the model matrix remain draft/proposed. This scaffold is not production approval.
- GPU function settings and transfer caps must be revalidated against the selected Modal SDK and benchmark before live inference.
- Modal may replay an in-flight input after container crash/preemption; later workers must be idempotent and reconcile results against the application job/attempt ledger.
- Lesson/activity generation roles remain unresolved under SRS Q157/Q159 and must stay disabled until an owner decision.
