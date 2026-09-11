# P1 catalog and Gate integrity polish implementation

- Evidence ID: `EV-018-P1-CATALOG-GATE-INTEGRITY-20260911`
- Date: 2026-09-11
- Scope: approved P1 catalog/compiler/tests/evidence only
- Plan: `plan/P1_CATALOG_GATE_INTEGRITY_POLISH_PLAN.md`
- Approval: `approvals/TASK_APPROVAL.md`, P1 catalog and Gate integrity polish approval

## Outcome

The P1 boundary now fails closed on catalog metadata contamination, optional context identity drift, duplicate template registration and forged spec identity. Existing `P1ContextV1`, `ActivityTemplateV1`, `ActivityFitEvaluationV1`, `BridgeSentenceV1` and `ExperienceSpecV1` contract versions remain unchanged.

## Implementation record

- The catalog adapter no longer exposes `OBJ_*` objective identifiers or broad area taxonomy values as anchor labels. Labels are normalized, de-duplicated and required to contain a meaningful value; objective refs must resolve to nonempty titles. The 20-template audit changed 41 objective-ID labels and 20 area labels to zero while retaining nonempty labels for all templates.
- Optional `selected_activity_id/version` and `selected_objective_id/version` context fields are exact constraints when present. Partial pairs and mismatches block before fit scoring; absent fields preserve existing behavior. Gate B rechecks the same context identity.
- `compile()` delegates final approval to `approve_gate_b()`, so identity, bridge, catalog, spec ID and spec hash checks run through one path.
- Duplicate template IDs fail at compiler construction. The deterministic pre-ID derivation and finalized `spec_sha256` are both independently verified at Gate B.

## Acceptance coverage

| Case | Result | Test coverage |
| --- | --- | --- |
| Objective/area catalog label contamination | Sanitized; 0 remaining | `test_catalog_anchor_labels_exclude_objectives_and_area_taxonomy` |
| All catalog objective refs have titles | PASS | `test_catalog_objective_refs_all_have_nonempty_titles` |
| Matching optional selected refs | PASS | `test_matching_optional_selected_context_refs_pass` |
| Mismatched/partial selected refs | BLOCKED before fit | `test_optional_selected_context_refs_block_before_fit` |
| Duplicate template ID | Fail fast | `test_duplicate_template_id_fails_fast` |
| Single compile/Gate B path | Same decision | `test_compile_and_explicit_gate_b_share_one_approval_decision` |
| Tampered spec ID/hash | BLOCKED | `test_gate_b_blocks_spec_id_drift`, existing hash drift test |
| Existing butterfly flow | PASS unchanged | `test_butterfly_fold_print_compiles_one_spec_and_gate_b_locks_identity` |

## Validation

- Targeted P1 suite: 59 passed.
- Full backend offline suite: 967 collected, 962 passed, 5 expected readiness/provider skips, no failures.
- Root offline suite: 33 passed. FEAT-018 replay: 1 passed.
- `pnpm -r typecheck`: passed. `pnpm -r test`: art-renderer 6 passed; mobile 7 passed.
- Ruff and strict mypy for changed P1 files: passed.
- Montessori domain/golden, skeleton, harness, architecture and team-allocation validators: passed.
- Repository security validation: `REPOSITORY_SECURITY_VALID`; 917 publishable files scanned; no absolute machine paths, credentials or provider secrets.

No P2/P3/P4/shared/mobile source changed, no contract version changed, and no live provider, production API, Android release or real child data was used.
