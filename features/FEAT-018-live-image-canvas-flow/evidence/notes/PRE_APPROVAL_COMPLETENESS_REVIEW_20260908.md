# FEAT-018 pre-approval completeness review — 2026-09-08

Status: REVIEW FINDINGS ONLY / NOT AN APPROVAL / NO IMPLEMENTATION AUTHORIZATION

## Scope and evidence boundary

This is a static reconciliation review of FEAT-018's plan, four person plans, contract-freeze
draft, approval record, current FEAT-003/P2-T3 contract implementation, and the existing
FEAT-015/016 fixture flow. It records no provider, GPU, device, real-image, or production
execution. `approvals/TASK_APPROVAL.md` remains `AWAITING_APPROVAL`.

The task cards are useful planning input, but the package is not complete enough to approve until
the following pre-approval changes are reviewed and recorded.

## Required pre-approval changes

### R1 — choose one canonical vision contract

The repository currently contains two incompatible models both named
`VisionUnderstandingResultV1`:

- `backend/src/sketch2life/contracts/schemas/vision.py` is the established P2-T3 result envelope
  and its Qwen adapter currently returns the versioned V2 result path.
- `backend/src/sketch2life/contracts/schemas/understanding.py` is the separate simplified live
  integration model used by the Lightning client.

The current FEAT-018 contract-freeze text incorrectly calls the latter the active backend schema.
Before implementation, the owner must choose and document exactly one of these paths:

1. consume the current P2-T3 V2 contract directly; or
2. introduce a separately named/versioned integration envelope plus an explicit adapter from the
   P2-T3 result, with JSON Schema fixtures and a migration record.

Do not keep two non-identical contracts with the same public name and `1.0` version. The selected
path must specify model revision/profile/config provenance and the retry/repair boundary, not only
the model family name.

### R2 — namespace the FEAT-018 Person 2 task IDs

`P2-T1` through `P2-T5` already name the FEAT-003 research workstream. The FEAT-018 Person 2 plan
uses the same IDs for different tasks, which makes approvals, evidence IDs, and handoffs ambiguous.

Rename the FEAT-018 cards before approval, for example to `FEAT018-P2-T1` through
`FEAT018-P2-T5` (and apply the same feature-qualified convention to all four person plans if task
IDs will be referenced outside their own files). Cross-links must then use those exact IDs.

### R3 — pin catalog provenance before using the 100/20 matrix

The activity matrix relies on a "reviewed P1 worktree" but the repository contains neither the
catalog payloads nor a branch/ref/commit SHA, schema version, or content hashes for that source.

Before approval, add a source-register entry and a feature-local provenance record containing:

- source repository/worktree identifier and immutable commit SHA;
- catalog/objective schema versions and aggregate/content hashes;
- the exact 100-MVP and 20-golden selection rule; and
- review status and the non-production boundary.

This is metadata/provenance only; it does not promote catalog data into the runtime.

### R4 — write an explicit ACT-0004 identity migration

The existing FEAT-015/016 fixture, mobile state, and tests use
`ACT-0004` + `OBJ_MOVEMENT_COORDINATION`; FEAT-018 proposes
`OBJ_OBJECT_PERMANENCE` (with `OBJ_RECEPTIVE_LANGUAGE` secondary). The identity must not be changed
in place or silently.

Before implementation, define a versioned migration fixture/manifest and enumerate every affected
producer, consumer, expected artifact, and test. Preserve the existing fixture as historical
evidence; introduce a new versioned identity only after its P1 catalog/provenance checks and
Gate-B fixtures pass.

### R5 — clarify staged pilot scope

The allocation review recommends an initial 3-5 activity smoke subset, while the main plan and
decision record describe a 20-activity full device pilot. Record both as separate gates:

1. a named 3-5 activity smoke subset with its own acceptance threshold; then
2. the 20-row device/integration acceptance pilot.

The 100 MVP rows remain offline catalog/reference coverage, not device E2E scope.

## Approval record requirements after R1-R5

Only after R1-R5 are reviewed may the owner decide whether to approve a revised FEAT-018 plan. An
approval record must name the exact plan revision, selected contract identity/version, allocation
by person plus shared integration ownership, approved smoke subset, 20-row expansion gate, visual
approval boundary, real-image consent boundary, and unchanged exclusions (no production/cloud,
Runpod, release, real child/personal data, or mobile credentials).

## Explicit non-actions

This review does not change FEAT-018 status, approve any task, change P2-T3 contracts, migrate
ACT-0004, promote catalog data, create assets, invoke Lightning, or authorize device/GPU/provider
execution.
