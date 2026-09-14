# FEAT-018 P1 Catalog and Gate Integrity Polish Plan

- Status: IMPLEMENTED — approved and validated 2026-09-11
- Parent scope: `P1_STRICT_CONTINUITY_POLISH_PLAN.md` (implemented 2026-09-11)
- Scope: P1 catalog adapter, P1 compiler, P1 tests and feature-local evidence
- Out of scope: P2 observation/model output, P3 renderer, P4 media/cache, shared/mobile/API changes, contract version changes, live providers, production/cloud, Android release and real child data

## Objective

Close the remaining P1-only integrity gaps found during the post-implementation review without requiring any downstream team to change code. The result must make P1 fail closed on catalog metadata contamination, optional context identity drift, duplicate template registration and forged spec identity while preserving the existing `ExperienceSpecV1` contract and all valid consumer inputs.

## Review findings that motivate this plan

The current golden catalog has 20 templates, but the adapter currently places 41 `OBJ_*` objective identifiers and 20 broad area labels such as `sensorial` and `practical_life` into `supported_anchor_labels`. Those values can produce an accidental anchor match even when the drawing subject is unrelated. The compiler also exposes optional selected activity/objective refs in `P1ContextV1` without enforcing them, and `compile()` constructs an approved Gate B decision separately from `approve_gate_b()`. The spec hash is checked, but the deterministic `spec_id` derivation is not independently re-verified. Finally, injected catalogs can silently overwrite duplicate template IDs in the compiler map.

These are P1 domain/catalog concerns. They do not require new fields, new contract versions or changes to P2/P3/P4 consumers.

## Preserved invariants

1. `SemanticAnchorSetV1`, `P1ContextV1`, `ActivityTemplateV1`, `ExperienceSpecV1` and all shared contract versions remain unchanged.
2. P1 continues to use the adult-confirmed primary anchor, one objective and one template.
3. Montessori age, readiness, prerequisite, material, supervision, policy and safety checks remain before fit scoring.
4. `ExperienceSpecV1` remains the identity source for video, original-art animation, activity, bridge and downstream handoff.
5. Existing contexts with optional `selected_*` fields absent remain behaviorally unchanged.
6. P2, P3, P4, shared, mobile and live-provider code require no edits.

## Workstream P1-POL-1 — Catalog anchor-label hygiene

Review and tighten the internal catalog adapter without adding external contract fields:

- Derive `supported_anchor_labels` from meaningful activity text only.
- Exclude objective identifiers (`OBJ_*`) and controlled area taxonomy tokens from anchor labels.
- Normalize case and whitespace, remove empty labels and de-duplicate labels deterministically.
- Keep provenance hash, objective refs, activity versions, review status and `production_eligible=false` unchanged.
- Add a P1 continuity audit that fails if a reviewed template has no meaningful anchor labels, unknown objective refs, unsupported kinds or an empty normalized label set.
- Re-run the 20-golden catalog mapping and record any changed candidate/negative result before accepting the change.

Acceptance:

- No generated template exposes an objective ID or broad area token as an anchor label.
- All 20 golden templates retain at least one meaningful anchor label.
- All objective refs remain known and version-valid.
- Butterfly fold-and-print still selects and passes exactly as before.
- Unrelated sorting remains rejected.

## Workstream P1-POL-2 — Optional context identity lock

Use the already-existing optional fields in `P1ContextV1` as an explicit identity constraint when present:

- If `selected_activity_id` or `selected_activity_version` is provided, the selected template activity must match exactly.
- If `selected_objective_id` or `selected_objective_version` is provided, the selected objective must match exactly.
- A partially supplied pair is blocked with a typed P1 reason; P1 must not infer the missing version or ID.
- The check runs before fit scoring and is re-checked by Gate B.
- Context fields left `None` preserve current fixture behavior.

Proposed P1-only reason codes:

- `CONTEXT_ACTIVITY_ID_MISMATCH`
- `CONTEXT_ACTIVITY_VERSION_MISMATCH`
- `CONTEXT_OBJECTIVE_ID_MISMATCH`
- `CONTEXT_OBJECTIVE_VERSION_MISMATCH`
- `CONTEXT_ACTIVITY_REF_INCOMPLETE`
- `CONTEXT_OBJECTIVE_REF_INCOMPLETE`

Acceptance:

- Matching optional refs pass the existing butterfly flow.
- Any mismatched or partial selected ref blocks before `ExperienceSpecV1` creation.
- Gate B blocks a tampered spec when the current context selected refs no longer match.
- No downstream consumer sees a new field or changed contract version.

## Workstream P1-POL-3 — Single Gate B approval path

Remove duplicate approval construction inside `compile()` while preserving the current output shape:

- Compile the spec only after strict fit passes.
- Pass the compiled spec through the same `approve_gate_b()` identity, context, bridge, hash and catalog checks used for revalidation.
- Return the exact approved decision and handoff from that single path.
- If the defensive re-check unexpectedly blocks, return a typed blocked compilation with no handoff.
- Preserve the existing approved reason `GATE_B_EXACT_IDENTITY_LOCKED` for valid specs.

Acceptance:

- `compile().gate_b` and `approve_gate_b(spec, context)` produce equivalent approved identity refs and reason codes.
- Every blocked defensive check returns no `ActivityHandoffV1`.
- Existing P1/P2/P3/P4 consumers continue to receive the same `ExperienceSpecV1` shape.

## Workstream P1-POL-4 — Spec and catalog integrity fail-fast

Add internal integrity checks without changing schemas:

- Reject duplicate `template_id` registrations rather than silently allowing the last item to overwrite the map.
- Verify that `spec_id` is derived from the canonical pre-ID payload using the current deterministic algorithm.
- Continue checking `spec_sha256` over the canonical finalized payload.
- Keep `activity_ref` duplicates allowed when they represent separately reviewed templates; only exact template identity collisions are invalid.
- Validate objective-title availability for catalog-loaded objective refs; injected fixture compilers may use the objective ID as the deterministic fallback title only when explicitly intended by the fixture.

Proposed P1-only reason codes:

- `DUPLICATE_TEMPLATE_ID`
- `SPEC_ID_MISMATCH`
- `OBJECTIVE_TITLE_MISSING`

Acceptance:

- Duplicate template registration fails before selection.
- A tampered `spec_id` with an otherwise unchanged payload is blocked at Gate B.
- A valid spec remains byte-for-byte deterministic for identical inputs.
- No contract version or downstream identity field changes.

## Workstream P1-POL-5 — Regression and evidence expansion

Add fixture-only tests under the existing P1 suite and update feature-local evidence:

| Case | Expected result |
|---|---|
| Golden catalog contains objective/area label contamination | Audit reports the sanitized label set |
| Optional selected activity/objective refs match | PASS |
| Optional selected activity/objective ID or version mismatches | BLOCKED before fit |
| Partial optional selected ref pair | BLOCKED |
| Compile approval and explicit Gate B re-check | Same approved identity |
| Defensive Gate B block | No handoff |
| Duplicate template ID | Fail fast |
| Tampered spec ID | `SPEC_ID_MISMATCH` |
| Valid butterfly continuity flow | PASS unchanged |
| Unrelated activity, unknown anchor and hard eligibility matrix | Existing REJECT/BLOCKED behavior unchanged |

Evidence files:

- `evidence/metrics/P1_CATALOG_GATE_INTEGRITY_YYYYMMDD.json`
- `evidence/notes/P1_CATALOG_GATE_INTEGRITY_IMPLEMENTATION_YYYYMMDD.md`

Evidence must contain only bounded metadata, hashes, counts and test summaries. No raw images, provider output, credentials or personal data may be added.

## Acceptance criteria

- Objective IDs and broad area taxonomy tokens cannot independently qualify a drawing as an anchor/template match.
- All optional selected context refs are either fully absent, exactly matching or typed-blocked; no silent inference occurs.
- `compile()` and `approve_gate_b()` share one final Gate B decision path.
- Duplicate template IDs, forged spec IDs and forged spec hashes fail closed.
- Valid butterfly and existing P1/P2/P3/P4 offline tests remain green.
- Contract names and versions remain unchanged.
- No P2/P3/P4/shared/mobile source file changes are needed.
- Repository security, harness, architecture, catalog and full offline validators remain green.

## Validation plan

1. Run targeted P1 unit/fixture tests, including the new catalog/context/Gate-B matrix.
2. Run the full backend, root and FEAT-018 offline suites.
3. Run `pnpm -r typecheck` and `pnpm -r test` to prove unchanged downstream consumers.
4. Run Ruff and strict mypy for changed P1 files.
5. Run Montessori domain/golden, skeleton, harness, architecture, team-allocation and repository-security validators.
6. Store all output summaries in feature-local evidence.
7. Do not run live providers, production endpoints, Android release flows or real data.

## Risk and rollback

Catalog label hygiene can change which golden templates appear as candidates, so the catalog audit and golden fixture diff are a required stop gate. If a reviewed golden mapping changes unexpectedly, revert only the P1 catalog/adapter commit and retain the existing strict-continuity implementation. The other workstreams are isolated compiler checks and can be reverted independently. No downstream migration or branch rewrite is permitted.

## Approval gate

This document is `DRAFT` until the project owner explicitly approves implementation. Approval must be recorded in `features/FEAT-018-live-image-canvas-flow/approvals/TASK_APPROVAL.md` before code changes begin.
