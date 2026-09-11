# FEAT-018 P1 Strict Continuity Polish Plan

- Status: DRAFT — implementation requires owner approval
- Scope: P1 catalog/domain/compiler only
- Out of scope: P2 model/output changes, P3 renderer changes, P4 media/cache changes, mobile UI changes, live provider execution, production API/cloud, Android release, production assets and real child data

## Objective

Guarantee that the off-screen activity selected from a session remains about the same confirmed anchor and learning objective as the original drawing. P1 must reject a semantically unrelated activity before creating an ExperienceSpec.

The existing versioned contracts remain unchanged. The plan uses the current fields in ActivityTemplateV1, ActivityFitEvaluationV1, BridgeSentenceV1 and ExperienceSpecV1.

## Current flow to preserve

1. Gate A supplies an adult-confirmed SemanticAnchorSetV1.
2. P1 receives P1ContextV1 and checks age, readiness, prerequisites, materials, supervision and policy.
3. P1 selects a LearningFocusV1 from the curated objective catalog.
4. P1 evaluates compatible ActivityTemplateV1 records.
5. P1 compiles an immutable ExperienceSpecV1.
6. Gate B locks the exact objective, template, activity, media plans and spec hash.
7. Existing P3/P4 consumers receive the already-locked identity.

## Strict Continuity Gate

A template may be PASS only when all three hard conditions are true:

- the primary confirmed anchor matches supported_anchor_labels;
- the selected objective exists in objective_refs;
- the activity, objective and anchor written into the spec are the same identities used by the fit evaluation.

A high weighted score cannot override a hard mismatch. A missing or ambiguous anchor blocks compilation. No generic activity fallback is allowed.

## P1 tasks

### P1-C1 — Catalog continuity metadata

Review every P1 template used by the 20-golden pilot and ensure supported_anchor_labels and objective_refs describe the actual activity. Add or correct bridge wording in the existing catalog/template adapter without introducing new external fields.

Evidence:
- catalog continuity audit;
- butterfly golden mapping;
- unrelated-activity negative mapping.

### P1-C2 — Strict fit policy

Update the P1 fit policy so drawing relevance, objective alignment and continuity are hard gates before weighted scoring. Keep Montessori eligibility checks unchanged.

Expected reason codes:
- ANCHOR_TEMPLATE_MISMATCH
- OBJECTIVE_TEMPLATE_MISMATCH
- ACTIVITY_IDENTITY_MISMATCH
- BRIDGE_IDENTITY_MISMATCH
- AMBIGUOUS_ANCHOR
- FIT_BELOW_THRESHOLD

### P1-C3 — Bridge sentence validation

Build BridgeSentenceV1 only from the selected anchor, objective and template. Validate that its references agree with the same identities used by the ExperienceSpec. A bridge sentence that cannot be tied to the selected identities blocks compilation.

### P1-C4 — ExperienceSpec and Gate B lock

Compile ExperienceSpecV1 only after strict fit passes. Preserve the existing source artifact hash, exact template/objective/activity refs, media continuity plans and spec hash. Keep Gate B as the final exact-identity lock.

### P1-C5 — Fixture and regression coverage

Add P1-only fixtures/tests:

- butterfly + wings/symmetry + fold-and-print: PASS;
- butterfly + unrelated sorting: REJECT;
- matching anchor + unrelated objective: REJECT;
- ambiguous anchor: BLOCKED;
- bridge sentence with wrong template/objective: BLOCKED;
- video/animation/activity plans with different identity: BLOCKED;
- cache/fallback identity remains represented by the same compiled spec: PASS at the P1 contract boundary.

### P1-C6 — Evidence and policy version

Record the policy change in P1 evidence and increment only the P1 selection policy identifier in policy_versions/selection_policy_version. Do not change contract versions or require downstream code changes.

## Acceptance criteria

- No P1 PASS spec can contain an activity whose anchor labels do not match the confirmed primary anchor.
- No P1 PASS spec can contain an objective that is absent from the selected template objective_refs.
- Butterfly → wings → symmetry → fold-and-print passes.
- Butterfly → unrelated sorting is rejected before Gate B.
- Missing, ambiguous or unconfirmed anchor blocks compilation.
- BridgeSentenceV1, ActivityPlanV1, video_plan and animation_plan carry one consistent identity.
- Existing P2, P3 and P4 branches require no code changes.
- Existing P1, P2, P3, P4 and repository validators remain green.
- Evidence contains no raw image, child data, provider response or credential.

## Validation

Run the P1 unit/fixture suite, the full offline contract suite and repository validators. Verify that the current P3/P4 consumers can still consume the unchanged ExperienceSpec contract. Do not run live providers or production endpoints.

## Risks and limits

This plan guarantees the identity of what P1 emits. It does not repair a downstream consumer that deliberately ignores the compiled ExperienceSpec and chooses a different activity. The current P3/P4 contracts already receive activity/objective/template identity, so no downstream modification is required for this polish.
