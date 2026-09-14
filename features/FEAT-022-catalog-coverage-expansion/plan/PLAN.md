# FEAT-022 — Catalog coverage and activity diversity expansion plan

Status: IMPLEMENTED_WITH_LIGHTNING_SMOKE_PENDING

## 1. Objective

Expand the current 100-profile MVP catalog into a governed, coverage-driven catalog of approximately 200-250 selectable approved variants, with an upper operating range of 300. The goal is not to inflate a count. The goal is to give the semantic matcher multiple safe, age-appropriate, materially different candidates for the same child interest while preserving explicit unavailable states when the catalog cannot safely serve a band.

Success is defined by post-filter coverage and recommendation diversity:

> At least 90% of common-scene evaluations must have at least three safe candidates after age, safety, prerequisite, material, supervision, and production-eligibility filtering.

## 2. Scope and non-scope

### In scope

- catalog taxonomy and coverage matrix;
- activity family/core/variant modeling;
- 200-250 authored selectable variants;
- age adaptations for 0-3, 3-6, 6-9, and 9-12;
- learning-objective, difficulty, material, context, and supervision coverage;
- provenance, approval, versioning, and catalog revision rules;
- catalog linting and coverage reports;
- semantic aliases and concept-to-activity mapping;
- diversity-aware candidate selection and observability;
- 100-300 scene evaluation plus a real-AI Lightning smoke run;
- evidence, ADRs, regression tests, and rollback/versioning documentation.

### Out of scope

- PixiJS runtime integration or animation implementation;
- video generation;
- UI integration;
- production caregiver/human-gate persistence;
- generating activities with AI at runtime;
- replacing the original child artwork or source media.

## 3. Baseline and target metrics

### Current baseline to record before changing content

- 100 activity profiles;
- 48 currently unmapped profiles;
- 33 observed concept-age gaps;
- approximately 0.2326 mapped-pair coverage in the current report;
- record the top-1 activity share and family share for the existing evaluation corpus;
- record all `NO_MATCH`, `UNAVAILABLE_AGE_BAND`, prerequisite, material, and safety rejections.

The baseline report must be checked into this feature's evidence directory before catalog edits begin.

### Delivery targets

| Metric | Target |
|---|---:|
| Selectable approved variants | 200-250 first delivery; never below 200 after validation |
| Activity families | at least 60 meaningful families |
| Tier A candidates | 5-8 safe candidates per common concept x age band where applicable |
| Tier B candidates | at least 3 safe candidates per common concept x age band |
| Tier C candidates | at least 2 safe candidates where applicable |
| Common-scene coverage | at least 90% of evaluated common scenes have >=3 safe candidates |
| Objective diversity | every in-scope objective has >=2 candidates per age band where applicable |
| Material support | every eligible variant has an ideal material path and >=1 safe home substitute, or an explicit reviewed no-substitute reason |
| Immediate repeat rate | 0 for the same child/session selection window |
| Dominance | no single activity family exceeds 20% within a common concept x age slice without an explicit catalog-size explanation |
| Unavailable correctness | 100% of empty post-filter slices produce explicit reason codes, never a fabricated activity |

## 4. Catalog shape and allocation

### 4.1 Identity model

Each selectable record must contain:

- immutable `activity_id` and monotonic `version`;
- `activity_family_id` for the shared core;
- `variant_id` describing age, material, or challenge differences;
- `catalog_revision`;
- `production_eligible`, `approval_status`, `provenance`, and reviewer metadata;
- supported age range and age-specific adaptation;
- primary and secondary concept IDs with aliases and parent concepts;
- learning objective(s), difficulty, prerequisites, safety constraints, supervision level;
- ideal materials, home substitutes, setup, cleanup, context, duration, and observation criteria;
- disallowed materials/actions and explicit failure/unavailable reason metadata where relevant.

`activity_id + version` is the contract identity. `activity_family_id` is used for diversity measurement and must not be used to bypass version parity.

### 4.2 Activity family allocation

Start with 60 meaningful activity families and author approximately four age-appropriate variants per family, yielding about 240 selectable variants. The allocation is a planning budget, not permission to create superficial duplicates.

| Concept cluster | Families | Examples of coverage |
|---|---:|---|
| Animals and plants | 12 | animal observation, movement, classification, flower/leaf care, plant parts |
| Family, people, home, community | 8 | family roles, self-care, household sequence, community helpers |
| Transport and built environment | 5 | vehicle classification, route/order, structures, home shapes |
| Weather, nature, water, space | 10 | weather observation, water transfer, sun/moon, sky patterns, nature cycles |
| Color, shape, movement, sound | 12 | sorting, matching, pattern, balance, rhythm, sound source, gross/fine motor |
| Number, language, practical life, science | 13 | counting, quantity, vocabulary, print readiness, measuring, predicting, recording |
| **Total** | **60** | **Approximately 240 selectable age/material/challenge variants** |

Each family must document which age bands it supports. A family may have fewer than four variants only when the rationale is safety or developmental appropriateness; the gap must then be visible in coverage output.

### 4.3 Age adaptation rules

Age adaptation changes the child-facing action and observation, not merely the wording:

- **0-3:** one concrete action, sensory exploration, short duration, direct supervision, no small-part or hazardous-material assumptions;
- **3-6:** sequence of 2-4 actions, naming/classifying, simple cleanup, nearby or direct supervision as appropriate;
- **6-9:** compare, order, measure, label, classify, or record one observation;
- **9-12:** explain relationships, make a prediction, record evidence, identify limits, or extend the investigation.

Every adaptation must specify the expected child action, observable completion signal, duration, supervision, and safety rationale.

## 5. Work breakdown

### Phase 0 — Freeze baseline and taxonomy

1. Run the current coverage evaluator and save a machine-readable baseline plus a human-readable summary under `evidence/metrics/` and `evidence/notes/`.
2. Freeze the canonical concept taxonomy, aliases, parent concepts, and tier metadata for the first catalog revision.
3. Export the 33 gaps, unmapped profiles, single-candidate slices, and top-repeat activities as the backlog.
4. Define what is a meaningful family, meaningful variant, safe candidate, and common scene before authoring begins.

**Gate:** baseline is reproducible, every gap has a stable key, and taxonomy changes are recorded in an ADR.

### Phase 1 — Harden catalog schema and governance

1. Add/validate identity and provenance fields described in section 4.1.
2. Add explicit `DRAFT`, `REVIEW`, `APPROVED`, `DEPRECATED`, and `BLOCKED` statuses.
3. Make only approved, production-eligible, version-compatible records visible to the matcher.
4. Add catalog revision loading so a run can report exactly which revision produced a recommendation.
5. Add schema constraints for age ranges, objective IDs, safety policy, prerequisites, supervision, materials, and non-empty child action.
6. Add duplicate detection using normalized activity intent, not only IDs.

**Gate:** invalid, unapproved, duplicate, unsafe, or identity-inconsistent records fail CI and cannot enter runtime matching.

### Phase 2 — Author the content blueprint

1. Convert the gap report into a matrix of concept family x age band x objective x difficulty x material/context.
2. Prioritize Tier A and Tier B concepts first.
3. For every new family, author a core activity and age adaptations; add material/challenge variants only when they change the real-world setup or challenge.
4. Ensure no concept-age slice is filled by five near-identical activities.
5. Ensure every objective has more than one family candidate in each applicable age band.
6. For each activity, write ideal materials plus a safe home substitute and setup/cleanup instructions.
7. Record a safety review and prerequisite rationale for each age variant.

**Gate:** content review confirms developmental appropriateness, safety, real activity diversity, Vietnamese child-facing wording, and provenance.

### Phase 3 — Implement and validate catalog content

1. Add records in a new catalog revision; preserve the 100-profile baseline unchanged until the new revision passes validation.
2. Run catalog linting for every commit touching catalog data.
3. Run post-filter coverage for all concept-age pairs and all objective-age pairs.
4. Run family/objective/material/context diversity checks.
5. Reject any new revision that lowers existing Tier A/Tier B coverage, introduces identity drift, or increases unsafe/unavailable slices without a reviewed reason.
6. Produce a diff report showing added, changed, deprecated, and newly blocked records.

**Gate:** the candidate revision reaches the minimum counts and does not regress baseline safety or identity invariants.

### Phase 4 — Improve matcher diversity and observability

1. Keep semantic relevance and child-interest alignment as primary ranking signals.
2. Add a diversity penalty or controlled exploration term after hard filters, never before safety/age/prerequisite checks.
3. Penalize recently selected `activity_id` and `activity_family_id` within the same session/child context.
4. Use deterministic seeds for reproducible evaluation while allowing different valid choices across different seeds.
5. Emit score breakdown fields: concept confidence, child-interest alignment, age fit, safety, catalog quality, recency penalty, diversity penalty, and final score.
6. Emit explicit `NO_MATCH` or `UNAVAILABLE_AGE_BAND` with machine-readable reason codes when all candidates are filtered out.
7. Track selection distribution by concept, age, objective, family, and catalog revision.

**Gate:** repeated runs with different seeds choose different valid candidates, while the same seed remains reproducible and unsafe/invalid candidates remain impossible to select.

### Phase 5 — Evaluation corpus and Lightning validation

1. Build a 100-300 case scene corpus covering the prioritized concept families, not just butterfly/flower/sun examples.
2. Include images and Vietnamese child narration representing ambiguous, multi-object, low-quality, and conflict cases.
3. Run each scene through all applicable age bands; do not inject activity recommendations into the input.
4. First run the catalog evaluator against captured semantic contracts to isolate catalog quality from model variance.
5. Run a smaller real-AI Lightning smoke set on the L4, using local Qwen VLM and faster-whisper model directories, and preserve raw outputs plus manifest hashes.
6. Compare baseline and new revision on coverage, top-1 share, family diversity, unavailable reasons, and identity parity.
7. Investigate every unexpected `NO_MATCH`, repeated activity cluster, and age-band regression before approval.

**Gate:** evaluation meets the 90% common-scene / >=3-safe-candidates target, no invalid identity appears, and real-AI output is traceable to the tested catalog revision.

### Phase 6 — Release and rollback

1. Publish the catalog revision as one reviewable commit, not scattered content commits.
2. Run harness and repository security validation before commit/push.
3. Record final metrics, known gaps, and the exact rollback revision.
4. Keep the prior catalog revision loadable for immediate rollback.
5. Mark only the content and validation gates actually achieved; do not mark the feature complete if coverage target or Lightning validation is missing.

## 6. Required tooling and reports

Implement or extend these checks:

- `catalog_lint`: schema, identity, version, provenance, duplicate, safety, prerequisite, and eligibility validation;
- `coverage_report`: raw and post-filter concept-age/objective-age counts, family counts, gaps, and tier status;
- `diversity_report`: top-1 share, family concentration, objective/material/context distribution, and immediate-repeat rate;
- `catalog_diff`: added/changed/deprecated/blocked records between revisions;
- `scene_eval`: 100-300 input cases, per-age outcomes, reason codes, and seed fingerprints;
- `lightning_smoke`: real ASR/VLM run with model provenance and manifest hash.

All reports belong under `features/FEAT-022-catalog-coverage-expansion/evidence/` and must identify catalog revision, code revision, input corpus, seed, and runtime.

## 7. Acceptance criteria

### Content and governance

- [ ] At least 200 and no more than 300 selectable approved variants in the first revision.
- [ ] At least 60 meaningful activity families.
- [ ] Every selectable variant has stable identity, family, variant, catalog revision, provenance, approval, age adaptation, safety, prerequisite, materials, context, supervision, duration, and observation criteria.
- [ ] No runtime path creates, mutates, or silently substitutes an unapproved activity.
- [ ] Every new record has a reviewed Vietnamese child-facing activity description.

### Coverage and personalization

- [ ] Tier A concept-age slices have 5-8 safe candidates where applicable.
- [ ] Tier B concept-age slices have at least 3 safe candidates.
- [ ] Tier C concept-age slices have at least 2 candidates where applicable or an explicit reviewed unavailable reason.
- [ ] At least 90% of common-scene evaluations have at least 3 safe candidates after all policy filters.
- [ ] Every applicable learning objective x age slice has at least 2 candidates from different families.
- [ ] Common concepts do not collapse to one deterministic activity across valid seeds.

### Runtime correctness

- [ ] Same seed is reproducible.
- [ ] Different seeds can choose different valid candidates.
- [ ] Immediate activity/family repetition is prevented within the configured session window.
- [ ] Activity ID/version parity is enforced end-to-end.
- [ ] Empty candidate sets return explicit `NO_MATCH` or `UNAVAILABLE_AGE_BAND`; no fabricated fallback is emitted.
- [ ] Selection score breakdown and catalog revision are present in the workflow result.

### Verification and release

- [ ] Unit tests cover schema, lint, coverage, diversity, filtering, identity parity, unavailable states, and seeded selection.
- [ ] Integration tests cover the workflow across all four age bands.
- [ ] 100-300 scene evaluation is recorded with evidence.
- [ ] Lightning real-AI smoke run is recorded or explicitly marked blocked with the exact environment reason.
- [ ] Full backend tests, Ruff, strict mypy, harness validation, and repository security validation pass.
- [ ] One atomic commit contains the approved catalog revision and implementation; rollback revision is recorded.

## 8. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Inflated count from near-duplicate variants | Count families separately; require changed child action/setup/challenge and duplicate-intent linting |
| Coverage looks good before safety/prerequisite filtering | Make post-filter coverage the release metric |
| Large catalog increases deterministic bias | Family-aware diversity penalty, seeded exploration, and distribution reports |
| New content regresses existing behavior | Keep baseline revision, run catalog diff and regression corpus |
| Age adaptation is only translated text | Require age-specific action, observation, duration, and safety rationale |
| AI invents unsafe or unavailable activities | Approved-only runtime gate and explicit unavailable contract |
| Lightning model variance obscures catalog bugs | Separate contract-level catalog evaluation from real-AI smoke evaluation |
| Content authoring becomes unreviewable | One catalog revision, provenance, reviewer status, and evidence per batch |

## 9. Implementation order after approval

1. Create the baseline evidence and freeze taxonomy.
2. Implement catalog lint/coverage/diversity/diff reports.
3. Harden schema and approved-only loading.
4. Author the highest-impact Tier A/Tier B families and age variants.
5. Integrate diversity-aware selection and reason-code observability.
6. Run the 100-300 scene evaluation, then Lightning smoke.
7. Fix gaps found by metrics, repeat validation, and only then commit/push the revision.
