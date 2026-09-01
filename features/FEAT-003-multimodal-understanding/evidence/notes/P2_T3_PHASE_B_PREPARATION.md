# P2-T3 Phase B preparation context

- Status: DRAFT / PLANNING ONLY — **not** an approval request and not implementation authority.
- Date: 2026-08-31
- Owner: Person 2
- Governing plan: `../../plan/P2_T3_VISION_RESEARCH_PLAN.md`, Phase B work packages V1–V5.
- Current approval: P2-T3 Phase A only; see `../../approvals/TASK_APPROVAL.md`.

## Purpose

Prepare a reviewable, bounded Phase B approval package for the real Qwen3-VL adapter without
installing a dependency, downloading a model, calling a GPU/provider, or changing a runtime.
Phase B must remain a standalone, synthetic-fixture vision-profile study; it is not P2-T5's public
CLI/end-to-end benchmark and is never a user-facing, Integration Sprint, or Gate A capability.

## Confirmed constraints

- The handbook baseline named in the approved research plan is `Qwen3-VL-8B-Instruct`. A prior L4
  synthetic-shapes smoke test was infrastructure reconnaissance only: it is not benchmark evidence,
  model selection, or a permission to reuse/download the model.
- Phase A must first be implemented and pass its contract/fixture matrix without changing the
  approved provider-neutral boundary. Phase B preserves the fake profiles and their behavior.
- Real candidate provenance must be exact and reproducible: model identifier and immutable
  revision, weight source/hash and license, adapter/runtime/dependency versions, device class,
  precision, structured-output settings, timeout budget, and canonical configuration hash.
- Original images remain immutable and must have an earned P2-T1 `PASS`. Adapter ingress, rather
  than the interface-only port, verifies P2-T1 provenance and source hash before every inference.
- Inputs and benchmark fixtures are synthetic only. No raw model payload, matched policy term,
  provider credential, endpoint, absolute machine path, or real child data enters source, ordinary
  logs, or feature evidence.
- The repository's current platform record is Lightning for development and Runpod for production;
  this note does not choose a cloud provider, image, GPU, or runtime default.

## Phase B gates that remain open

1. **Semantic safety for unknown paraphrases.** The Phase A lexical policy catches known terms only.
   Before Phase B approval, select and document one control. Recommended minimal control: real-model
   output is limited to synthetic fixtures and may enter feature evidence only after project-owner
   review; this permits a technical study but does not claim automated semantic safety or permit
   promotion. `semantic_safety_coverage` and `semantic_safety_recall` remain `NOT_MEASURED`.
2. **Runtime/profile decision package.** Select candidate profiles and exact parameters only after
   recording model revision/license, exact dependency pins, structured-output parameters, timeout,
   and the ADR rationale. No profile may be frozen or become a runtime default in this package.
3. **Phase A completion.** Its fake adapter, policy, manifest, and contract tests must be completed
   and validated before a real adapter is introduced.

## Proposed approval-package sequence

### B0 — dossier and contract-impact review

Write the candidate-profile table and a precise additive contract amendment for real model
provenance. It must define the provenance value object, result-contract versioning/backward
compatibility, catalog expansion, and regression proof that Phase A fake outputs are unchanged.
Do not reserve nullable model-provenance placeholders in the Phase A contract.

### B1 — isolated real runtime

After approval, exact-pin dependencies and create the Qwen adapter/runtime configuration under
`backend/src/sketch2life/infrastructure/ai`. Configuration is constructor-injected and cannot extend
application Settings, API wiring, mobile configuration, or a dynamic per-request catalog. Local and
cloud paths/credentials remain ignored runtime inputs, never committed values.

### B2 — typed GPU preflight

Run one real model load and one synthetic inference through the actual adapter. Record only safe
environment/config identifiers and measured or `NOT_MEASURED` values. Map load/device failures to
`VISION_MODEL_UNAVAILABLE` with `MODEL_LOAD_FAILED` or `DEVICE_UNAVAILABLE`; keep timeout and
provider failures within the already-approved typed error/retry matrix.

### B3 — structured-output mapping study

Measure real output behavior before scoring quality: schema-valid rate, fenced responses,
truncation, extra keys, invalid enum values, duplicate observation IDs, broken references, lossless
unwrap recovery, and typed-failure counts. Constrained decoding is a mitigation only, never proof
of schema or safety correctness.

### B4 — controlled vision-only benchmark

Use a versioned held-out synthetic drawing manifest with immutable hashes and an explicitly
published matching rule. Report schema-valid result rate; entity/action/relation coverage or
accuracy; known-policy trigger rate with policy and match-view versions; per-stage p50/p95 latency;
cold start separately; peak device memory when observable; and each unavailable item as
`NOT_MEASURED`. Do not merge results across profile or policy-match-view versions.

### B5 — recommendation gate

Write a comparison table covering quality, latency, memory, runtime compatibility, typed failures,
policy limitation, and synthetic-only limitation. Recommend either a further controlled experiment
or `NOT_ENOUGH_EVIDENCE`; a profile freeze needs a separate ADR and explicit owner decision.

## Required future evidence

- Phase B approval request with scope/non-goals and the selected semantic-safety control.
- Exact profile/dependency/license/provenance record and contract-compatibility tests.
- GPU preflight result for both success and typed-failure paths.
- Held-out synthetic-fixture manifest metadata/hashes and benchmark report, without payloads or raw
  output text.
- ADR/recommendation explaining whether any profile is eligible for later consideration.

## Explicit non-goals

No Qwen install/download, cloud spend, GPU execution, provider credential, production deployment,
HTTP/API/UI/mobile/session/job/database/queue/storage integration, P2-T4/P2-T5 work, real child
data, canonical understanding, or Gate A decision is authorized by this note.
