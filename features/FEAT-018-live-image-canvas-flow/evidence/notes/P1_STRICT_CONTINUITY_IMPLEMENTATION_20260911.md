# P1 strict continuity polish implementation

- Evidence ID: `EV-018-P1-STRICT-CONTINUITY-20260911`
- Date: 2026-09-11
- Scope: approved P1 application/compiler and fixture-only validation
- Plan: `plan/P1_STRICT_CONTINUITY_POLISH_PLAN.md`
- Approval: `approvals/TASK_APPROVAL.md`, P1 strict continuity polish addendum

## Outcome

The P1 compiler now refuses to create an `ExperienceSpecV1` when the confirmed primary anchor is not exactly compatible with the selected template. Compatibility requires an exact normalized label or semantic tag in `supported_anchor_labels` and a compatible `supported_anchor_kinds` entry. Objective membership, bridge/media/activity identity and the spec hash are checked before Gate B can approve the handoff.

The policy identifier is `P1_STRICT_CONTINUITY_V1`. Existing `ActivityFitEvaluationV1`, `BridgeSentenceV1` and `ExperienceSpecV1` contract versions remain `1.0`; no shared contract field was added.

## Implementation record

- `P1ExperienceCompiler._anchor_template_continuity_failures` is the hard anchor gate. A ranked match score remains useful for candidate ordering, but token/score overlap cannot promote a mismatched kind or label.
- `_fit_evaluation` zeros the affected relevance/continuity dimensions on a hard mismatch and returns `REJECT` below the schema threshold. A high weighted score cannot override anchor or objective mismatch.
- `approve_gate_b` re-checks anchor compatibility, media/activity/fit references, bridge references and `spec_sha256`. Tampered fixture copies therefore close as `BLOCKED`.
- The expanded regression matrix covers all hard eligibility failure reasons, inclusive age boundaries, deterministic ranking and explicit preference, semantic-tag matching, unknown/preferred-template failures, Gate A/session/context/stale checks, every downstream identity surface, rejected-fit recheck, policy propagation, deterministic hashing and frozen-spec immutability.
- Bridge wording is derived from the selected anchor and objective title, while `BridgeSentenceV1` keeps the exact template/objective/anchor references used by the spec.
- The feature-local fixture set adds unsupported-kind, unrelated-objective, bridge-drift and manifest coverage without raw media, child data or credentials.

## Acceptance coverage

| Case | Result | Evidence |
| --- | --- | --- |
| Butterfly + wings/symmetry + fold-and-print | PASS; Gate B approved | `test_butterfly_fold_print_compiles_one_spec_and_gate_b_locks_identity` |
| Butterfly + unrelated sorting | REJECT; Gate B blocked | `test_unrelated_sorting_template_is_rejected_below_fit_threshold` |
| Matching anchor + unrelated objective | REJECT; continuity is zero | `test_matching_anchor_with_unrelated_objective_is_rejected_by_strict_fit` |
| Ambiguous equal anchor candidates | BLOCKED | `test_ambiguous_anchor_blocks_without_preferred_template` |
| Wrong bridge template/objective reference | BLOCKED | `test_gate_b_blocks_bridge_identity_drift`, `test_gate_b_blocks_bridge_objective_drift` |
| Wrong video-plan identity | BLOCKED | `test_gate_b_blocks_media_identity_drift` |
| Wrong spec hash | BLOCKED | `test_gate_b_blocks_spec_hash_drift` |

## Validation

- Targeted P1 suite: 45 passed.
- Full backend offline suite: 953 collected, 948 passed, 5 expected readiness/provider skips, no failures.
- Root offline suite: 33 passed. FEAT-018 replay: 1 passed.
- `pnpm -r typecheck`: passed. `pnpm -r test`: art-renderer 6 passed; mobile 7 passed.
- Ruff and strict mypy for the P1 compiler: passed.
- Montessori domain and golden catalog validators: passed.
- Skeleton, harness, architecture and team-allocation validators: passed.
- Repository security validation: `REPOSITORY_SECURITY_VALID` (914 publishable files scanned; no absolute machine paths).

The P1 change does not execute live providers, call production APIs, alter Android/mobile code, change P2/P3/P4 code, publish assets or use real child data. Downstream consumers still receive the unchanged `ExperienceSpecV1` contract as their identity source.
