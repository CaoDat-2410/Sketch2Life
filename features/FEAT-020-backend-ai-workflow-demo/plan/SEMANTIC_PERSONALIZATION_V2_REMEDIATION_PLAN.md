# FEAT-020 — Semantic Personalization V2 Remediation Plan

Status: IMPLEMENTED — VALIDATED

Feature: FEAT-020-backend-ai-workflow-demo
Scope: backend-only semantic understanding, activity recommendation, fit evaluation and truthful telemetry
Contract direction: introduce new V2 contracts; preserve existing V1 contracts for compatibility and comparison

## 1. Owner decisions recorded

The project owner confirmed:

1. One canonical scene understanding must be shared across all requested age bands. Age must change adaptation, not the semantic truth of the drawing.
2. A hybrid semantic engine is acceptable: curated concepts/profiles define eligibility; AI or embeddings may suggest/rank but may not bypass reviewed profiles or hard rules.
3. Safe fallback must be a first-class mode and must not be reported as personalized success.
4. Known semantic routes must be restored, including a solar-system route for a supported sun/moon concept and botanical/nature routes for flower/plant concepts.
5. New V2 contracts must be created instead of silently changing the meaning of the V1 contracts.
6. Video generation, UI, real human gates, persistence and real caregiver feedback remain out of scope for this remediation.

Implementation authorization was recorded in the feature approval record before implementation.

## 2. Problem statement

The current remediation correctly removed lexical false positives and added safe age fallbacks. The next blocker is recall and semantic stability:

- the same scene may receive unrelated primary anchors such as a color token, a noun fragment or grass depending on age-band iteration;
- the current semantic profiles are too close to activity titles and do not cover the concept vocabulary emitted by the real VLM/ASR path;
- a run can be operationally SUCCEEDED while every band is SAFE_FALLBACK;
- V1 bridge text can still imply semantic continuity when the selected mode is a baseline fallback;
- V1 fit scoring allows a fallback semantic score around 55 to pass because objective, continuity and safety dimensions dominate the weighted total;
- the demo feedback decision still uses RECORDED while the observation status is NOT_ATTEMPTED;
- the latest reported 9-12 result regressed from a useful sun/moon route to an unrelated mathematics baseline.

The goal is not to restore lexical matching. The goal is to make semantic recall higher while preserving the current precision, provenance and fail-closed hard rules.

## 3. Target architecture

The target flow is:

    image + narration
        -> media validation
        -> real ASR and real VLM
        -> modality fusion
        -> ConfirmedSceneUnderstandingV2
        -> Gate A / adult confirmation
        -> per-age adaptation and candidate ranking
        -> reviewed semantic eligibility
        -> hard-rule eligibility
        -> Gate B
        -> ExperienceSpecV2
        -> story/scene and activity handoff
        -> explicit personalized or baseline outcome
        -> demo feedback placeholder

The important invariant is:

    one scene understanding identity and one canonical concept graph
    are shared across all age-band sub-runs.

Only the following may vary by age band:

- learning objective and abstraction level;
- activity complexity and presentation steps;
- material and substitution guidance;
- supervision and duration guidance;
- story wording;
- selected activity among eligible candidates;
- fallback baseline when no personalized candidate is eligible.

## 4. Contract V2 design

### 4.1 ConfirmedSceneUnderstandingV2

Create a new provider-neutral contract in the contracts layer. It must contain:

- contract name/version;
- scene understanding ID and canonical scene hash;
- source image/audio artifact references and hashes;
- Gate A confirmation state and adult actor;
- ASR/VLM result identity references, not raw provider output;
- one canonical primary concept;
- ranked secondary concepts;
- observed entities, actions, themes and relationships in sanitized typed form;
- concept provenance per concept;
- cross-modal support count and confidence;
- ambiguity/conflict records;
- normalization policy version;
- immutable source identity.

The contract must reject:

- age-specific primary anchor mutation;
- unsupported or invented concept IDs;
- missing evidence claim IDs;
- raw prompt/model output;
- absolute local paths;
- provider SDK objects.

The scene contract must be built once after fusion and passed unchanged to every age-band adapter.

### 4.2 SemanticActivityMatchV2

Create a new match evidence contract with:

- match mode: PERSONALIZED_EXACT, PERSONALIZED_ALIAS, PERSONALIZED_CONCEPT, AGE_BASELINE_FALLBACK;
- profile ID/version;
- activity ID/version;
- semantic relevance score;
- matched concept IDs;
- matched phrase/alias evidence;
- supporting scene concept IDs;
- negative/ambiguity decisions;
- hard-rule result reference;
- fallback reason when applicable;
- ranking explanation;
- evidence claim IDs;
- policy version.

V1 SemanticMatchEvidenceV1 remains readable for old callers. V2 is the authoritative contract for the new demo path.

### 4.3 ExperienceSpecV2

Create a new spec contract rather than changing the semantics of ExperienceSpecV1. It must add:

- experience mode:
  - PERSONALIZED;
  - AGE_BASELINE_FALLBACK;
- semantic match evidence;
- age adaptation record;
- separate semantic relevance, age fit, readiness, safety and material scores;
- Gate B decision class:
  - PERSONALIZED_APPROVED;
  - BASELINE_APPROVED;
  - BLOCKED;
- mode-aware bridge sentence;
- mode-aware story continuity policy;
- V2 identity/hash rules.

A fallback may be operationally ready for a demo handoff, but it must never be represented as PERSONALIZED.

### 4.4 BackendWorkflowResultV2

Create a V2 result contract with:

- V2 contract identity;
- strict/partial matrix policy;
- age matrix summary;
- one shared scene understanding ID/hash;
- per-band ExperienceSpecV2;
- per-band mode and semantic status;
- top-level personalized band count;
- top-level fallback band count;
- unavailable band list;
- truthful feedback placeholder state;
- manifest hash.

V1 output remains available for compatibility/comparison during migration. The new acceptance command must explicitly select V2 and must not silently downgrade to V1.

## 5. Stable scene understanding implementation

### 5.1 Fusion boundary

Add an application service after ASR/VLM fusion:

- consume only typed AsrSuccessV1 and VisionUnderstandingSuccessV2;
- normalize labels, phrases and concepts once;
- deduplicate entities/themes/actions;
- preserve conflicts instead of selecting a different truth for each age;
- assign one primary concept using deterministic evidence ranking;
- retain a ranked concept set for downstream age adaptation.

### 5.2 Primary concept ranking

Rank candidates using reviewed deterministic signals:

1. cross-modal support from both ASR and VLM;
2. phrase completeness, preferring multi-token concepts over singleton tokens;
3. reviewed concept/profile compatibility;
4. observation confidence;
5. direct scene salience;
6. negative/ambiguous phrase penalties;
7. deterministic stable tie-break.

A single color word, generic noun fragment or isolated token must not become the primary concept when a supported scene concept exists.

The result must be invariant across age bands. A test must assert that all four bands receive the same scene understanding ID and canonical concept set.

### 5.3 Adult Gate A behavior

The demo autopilot may confirm the scene understanding using the existing compatible project-owner actor. It must not alter the canonical concepts per age band. A future UI can replace this with caregiver/guide confirmation without changing V2 contract identity.

## 6. Semantic recall and concept ontology

### 6.1 Concept taxonomy

Create versioned reviewed concept profiles for the 100 activities. Profiles must map activities to concepts rather than only title strings. Initial concept families:

- ANIMAL_BUTTERFLY;
- ANIMAL_MOVEMENT;
- PLANT_FLOWER;
- PLANT_STRUCTURE;
- NATURE_OBSERVATION;
- SUN_LIGHT;
- MOON_PHASE;
- SKY_WEATHER;
- COLOR;
- SHAPE_PATTERN;
- OBJECT_TRANSFER;
- SEQUENCE;
- SOUND_LANGUAGE;
- COUNTING_DATA;
- MATERIAL_TEXTURE;
- HUMAN_ACTION.

Each activity profile must include:

- positive concept IDs;
- accepted parent concepts;
- reviewed aliases;
- accepted anchor kinds;
- negative concepts and ambiguity phrases;
- positive and negative examples;
- age applicability;
- fallback eligibility;
- provenance and review status.

### 6.2 Matching policy

Eligibility order:

1. reviewed exact concept/phrase;
2. reviewed alias;
3. reviewed concept-family match;
4. safe age baseline only when no personalized candidate survives.

AI/embedding suggestions may propose a concept or rank eligible profiles. They may not create IDs, bypass negative concepts, bypass age/readiness/prerequisite/material/supervision/safety rules, or convert a fallback into personalized.

### 6.3 Known routes

Add and test explicit routes:

- SUN_LIGHT or MOON_PHASE -> ACT-0091 where age and hard rules permit;
- PLANT_FLOWER or PLANT_STRUCTURE -> ACT-0055 or another reviewed botanical activity;
- ANIMAL_BUTTERFLY or ANIMAL_MOVEMENT -> reviewed nature/observation activity;
- ambiguous phrase such as BÌNH_MINH must not match pouring activity;
- BƯỚM BAY must not match water-cycle activity.

The route is concept-based, not a token overlap.

## 7. Age-specific adaptation

For each age band:

1. receive the same ConfirmedSceneUnderstandingV2;
2. filter the 100 catalog by hard rules;
3. rank only activities whose V2 semantic profile is eligible;
4. apply age-specific objective/complexity/material/supervision adaptation;
5. prefer personalized candidates over fallback;
6. use seeded variation only among equal-mode/equal-strength candidates;
7. avoid immediate activity repetition;
8. emit V2 mode and evidence.

The age loop must never rebuild the primary scene anchor from raw candidate text.

Expected behavior for the known demo image:

- 0-3 may use a safe baseline if no infant-specific personalized activity is semantically eligible;
- 3-6 may use a transfer/practical-life activity only if a reviewed concept supports it, otherwise explicit baseline wording;
- 6-9 should prefer plant/nature observation when flower/plant concepts are present;
- 9-12 should prefer a reviewed sun/moon/science route when the canonical scene contains a supported sun/moon concept, and must not silently fall back to unrelated mathematics.

## 8. Fit evaluation and Gate B

Replace the V1 weighted-score ambiguity with mode-aware gates.

PERSONALIZED_APPROVED requires:

- a V2 personalized match;
- semantic relevance above the personalized threshold;
- objective alignment;
- all hard rules passing;
- identity/hash continuity passing;
- mode-aware bridge and story validation.

BASELINE_APPROVED requires:

- no eligible personalized candidate;
- explicit age baseline profile;
- all hard rules passing;
- fallback reason and evidence;
- generic bridge/story wording;
- no claim that the activity derives from a confirmed visual concept.

A fallback may produce a ready demo handoff, but it must not be counted in personalized recommendation metrics.

## 9. Story, bridge and telemetry changes

### 9.1 Mode-aware language

Personalized:

    Con bướm và bông hoa trong tranh của con -> cùng quan sát các bộ phận của cây.

Fallback:

    Từ bức tranh của con, mình chuyển sang một hoạt động phù hợp độ tuổi.

The bridge generator, story scene generator and downstream analytics must all consume the same V2 experience mode.

### 9.2 Feedback placeholder

Replace the demo feedback decision value RECORDED with PLACEHOLDER_CREATED, or remove the feedback decision from the demo path. The contract must state:

- no real caregiver observation was received;
- no completion outcome was inferred;
- no history update came from real feedback.

## 10. Tests and acceptance criteria

### 10.1 Contract tests

- V2 contracts reject unknown fields and raw provider output.
- V2 hashes remain stable after serialization.
- source artifact and evidence claim identity is preserved.
- V1 contracts continue to validate existing fixtures.
- V2 fallback cannot be serialized as PERSONALIZED.

### 10.2 Semantic unit tests

- primary concept is invariant across all age bands;
- singleton tokens cannot become the primary concept when a reviewed concept exists;
- bướm bay never selects water-cycle activity;
- bình minh never selects pouring activity;
- mặt trời/mặt trăng reaches the reviewed cosmic route when the concept is present;
- bông hoa reaches botanical/nature observation when the concept is present;
- negative phrases block personalized match but do not hide the explicit baseline fallback;
- concept-family matching is deterministic and provenance-backed.

### 10.3 Recommendation tests

- 100 activities and 100 semantic profiles load with unique IDs;
- every age band has personalized profile coverage or an explicit baseline;
- repeated seed produces stable output;
- different seeds vary only among equally eligible candidates;
- previous activity IDs prevent immediate repetition;
- hard rules cannot be bypassed by semantic suggestions;
- fallback and personalized candidates cannot be mixed under one mode.

### 10.4 Real-AI Lightning acceptance

Run the real ASR/VLM command with the pre-generated replaceable image/WAV. Assert:

- V2 result is schema-valid;
- all requested age bands are explicitly listed;
- one shared scene understanding ID/hash is present across all bands;
- per-band mode is explicit;
- no band claims PERSONALIZED without V2 evidence;
- known scene concepts route to expected reviewed activity families;
- 9-12 does not regress to unrelated mathematics when a sun/moon concept is present;
- strict mode remains fail-closed;
- partial test-only mode remains explicit.

The real-AI test must not require one exact provider wording. It should validate concept family and contract evidence.

## 11. Migration and rollout

Phase A — contracts and invariants:

- add V2 contracts;
- add shared scene understanding;
- add model/hash validators;
- keep V1 tests green.

Phase B — concept catalog:

- author and validate 100 concept profiles;
- add route and negative examples;
- generate a coverage report.

Phase C — selector and Gate B:

- route all age bands through one scene understanding;
- add mode-aware candidate selection;
- add mode-aware fit/gate/story/bridge.

Phase D — real-AI acceptance:

- run Lightning with the same image/WAV;
- capture sanitized V2 manifest;
- compare V1/V2 only for diagnosis;
- verify 9-12 regression and age-invariant scene truth.

Phase E — cleanup:

- update feature context, decisions and evidence;
- update CLI documentation;
- mark the plan implemented only after harness/security/tests pass.

## 12. Explicit non-goals

- no frontend/UI;
- no PixiJS runtime integration;
- no video generation;
- no real caregiver feedback;
- no Firebase Storage/Firestore/Realtime Database;
- no provider credentials in code or mobile;
- no production eligibility claim for provisional catalog activities;
- no lexical fallback reintroduced as semantic personalization.

## 13. Definition of done

The remediation is complete only when:

1. the V2 plan and approval record are approved;
2. V2 contracts and shared scene understanding are implemented;
3. all 100 activities have validated concept profiles or explicit documented baseline coverage;
4. all age bands share one canonical scene understanding;
5. personalized and baseline outcomes are contractually distinct;
6. bridge/story/feedback telemetry are mode truthful;
7. the 9-12 known regression is covered by a real-AI acceptance assertion;
8. targeted and regression tests pass;
9. harness and repository security validators pass;
10. evidence is stored under FEAT-020;
11. implementation is committed once and pushed only after explicit user approval.
