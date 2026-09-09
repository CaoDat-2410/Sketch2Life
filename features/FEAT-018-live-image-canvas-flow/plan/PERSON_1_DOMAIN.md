# FEAT-018 Person 1 — Catalog, objectives, activity selection, Gate B

## Mission

Make activity identity deterministic and auditable. Promote the reviewed Montessori catalog into the main runtime, preserve every record/version/provenance field, map AI observations to candidate activities without treating observations as canonical meaning, and make Gate B approve the exact activity/objective versions.

## Ownership boundary

Person 1 owns catalog/objective data, rule vocabulary, candidate selection inputs, and Gate B identity contracts. Person 1 does not own the VLM adapter, Pixi renderer, provider transport, persistence, or the complete Android shell.

## Task cards

### P1-T1 — Promote and freeze catalog inputs

- Bring the reviewed MVP catalog (100 activities, 20 objectives) and golden overlay (20 activities) into versioned main-repository data paths.
- Record source commit/worktree, schema version, record hash, review status, and `production_eligible=false`.
- Keep the MVP catalog and golden overlay distinct; do not silently replace MVP records with golden overlays.
- Make `ACT-0004` canonical mapping explicit: primary `OBJ_OBJECT_PERMANENCE`, secondary `OBJ_RECEPTIVE_LANGUAGE`.

Deliverables:

- `data/activity-catalog/mvp/activities.v1.json`
- `data/activity-catalog/mvp/learning-objectives.v1.json`
- `data/activity-catalog/golden/v1/activities.v2.json`
- catalog/objective schemas and loader
- migration note for the current hardcoded fixture identity

### P1-T2 — Define adult context and eligibility envelope

Required explicit fields:

- `age_months`
- `readiness_ids`
- `completed_activity_ids`
- `available_material_option_ids`
- `supervision_level`
- `policy_flags`
- `candidate_status`
- selected activity/objective IDs and versions

Rules:

- Never infer age, readiness, supervision, materials, or psychological traits from an image or narration.
- Hard safety/material/prerequisite constraints run before ranking or selection.
- Missing context produces a typed `MISSING_CONTEXT`/`NO_ELIGIBLE_ACTIVITY` result.

### P1-T3 — Observation-to-candidate mapping

- Preserve the original VLM labels and normalized labels separately.
- Define versioned mappings for all 20 golden pilot activities.
- Cover exact match, multiple candidates, unknown observation, contradiction, and adult correction.
- Candidate mapping may propose; only Gate A creates canonical meaning for the session.

### P1-T4 — Gate B contract and stale-version protection

- Gate B approves both `activity_id + activity_version` and `objective_id + objective_version`.
- Reject stale candidate versions, mismatched objective mappings, inactive records, missing safety checks, and unapproved material substitutions.
- Keep the current session/version guard and emit redacted evidence.

### P1-T5 — Catalog harness and pilot pack

- Deterministic CLI validates all 100 MVP records, 20 golden records, objective references, prerequisite graph, safety fields, and mapping parity.
- Produce positive/blocked/malformed/no-context fixtures.
- Run the full 20-activity pilot matrix from `ACTIVITY_PILOT_MATRIX.md`.

## Required evidence

- Catalog validation summary: 100 MVP activities, 20 objectives, 20 golden overlays.
- Per-record hash/provenance and schema version report.
- `ACT-0004` identity correction report.
- 20 pilot mapping cases: valid, ambiguous, unknown, blocked, stale, and corrected-by-adult.
- Gate B approval/rejection evidence for every pilot record.
- No-eligible and missing-context evidence.
- Security scan proving no child data, token, provider endpoint, or raw image in the catalog/evidence.

## Acceptance criteria

- Every MVP/golden record loads through a versioned schema.
- Every golden record resolves to existing objective IDs and versions.
- All 20 pilot rows have at least one positive and one negative eligibility case.
- Gate B cannot approve an activity/objective pair that is stale, inactive, or mismatched.
- The runtime no longer relies on a hardcoded `ACT-0004`/`OBJ_MOVEMENT_COORDINATION` pair.
- All catalog artifacts remain provisional and non-production.

## Handoff contract

P1 publishes a candidate envelope consumed by P2/P4 and a Gate B approval envelope consumed by the mobile flow. P1 must not require another person’s live server to run its harness.

## Definition of done

Catalog files, loader, mapping fixtures, Gate B contract, 20-activity pilot evidence, 100-record validation, and review note are complete and linked from FEAT-018 evidence.

## Contract alignment checklist (mandatory)

Before implementation, read [CONTRACT_FREEZE.md](CONTRACT_FREEZE.md). Person 1 may only publish `P1ContextV1`, `P1FilterResultV1`, and the catalog/objective records named there. Do not rename `activity_id`, `activity_version`, `objective_id`, `objective_version`, `reason_codes`, or `contract_version`.

### Exact inputs

- `RawUnderstandingResultV1` after Gate A confirmation.
- Adult-provided `P1ContextV1`.
- Catalog/objective records at exact versions.
- Session ID and expected session version.

### Exact outputs

- `P1FilterResultV1` with `status`, exact identity/version pair, ordered `reason_codes`, and `contract_version`.
- `IntegrationGateDecisionV1` for Gate B with the same identity/version pair.
- `ActivityHandoffV1` only after Gate B.

### Contract tests owned by P1

- schema extra-field rejection;
- objective/activity version mismatch;
- inactive/stale record;
- missing context and no eligible candidate;
- Gate A absent or stale session;
- full 20-golden and 100-MVP catalog reference validation.

P1 must publish JSON Schema/fixtures before P2, P3, or P4 integrate against the catalog.

## Execution order and stop gates

1. Wait for contract freeze and catalog source promotion approval.
2. Publish schemas and loader fixtures.
3. Run catalog validation before exposing any activity to mobile.
4. Publish the 20-row pilot mapping pack.
5. Integrate only after P2 `RawUnderstandingResultV1` and the shared Gate contract fixtures pass.
6. Stop immediately on identity mismatch, stale version, missing adult context, or untraceable source.

Evidence naming: `P1_<contract-or-scenario>_<YYYYMMDD>.json` plus a redacted `.txt` summary in this feature's evidence directory.

## Revision-2 engine additions — pending approval

P1 additionally owns `FEAT018-P1-E1` through `FEAT018-P1-E5` in `ENGINE_REFINEMENT_PLAN.md`: curated Activity Template Library, one-anchor/one-objective selection, `ExperienceSpecV1` compilation, deterministic fit evaluation and Gate B locking of objective/activity/template/spec versions. The template library is domain-owned; runtime AI cannot invent or mutate pedagogy.