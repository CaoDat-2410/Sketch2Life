# FEAT-020 Semantic Personalization V2 Context

Status: IMPLEMENTED — VALIDATED
Date: 2026-09-13

## Delivered behavior

The new BackendAiWorkflow.run_v2() path keeps the original V1 run() API intact while adding a versioned V2 result path. The V2 path:

1. validates image and WAV input;
2. invokes the injected real ASR and VLM ports;
3. fuses typed outputs once into one ConfirmedSceneUnderstandingV2;
4. passes the same scene identity and concept graph to every requested age band;
5. matches activities through the 100-profile V2 semantic catalog;
6. applies age-specific hard-rule eligibility and adaptation;
7. ranks personalized modes above fallback modes;
8. emits explicit Gate B mode, story mode, bridge wording, activity handoff telemetry and feedback-placeholder truth;
9. preserves original V1 output inside the V2 result for migration and comparison.

The CLI defaults to --contract-version v2. --contract-version v1 remains available for compatibility.

## V2 contracts

- ConfirmedSceneUnderstandingV2: immutable multimodal scene identity, canonical concept, secondary concepts, provenance and source hashes.
- SemanticActivityProfileV2: versioned concept-family profile derived from the curated 100-activity catalog.
- SemanticActivityMatchV2: exact, alias, concept-family or baseline-fallback evidence.
- ExperienceSpecV2: mode-aware spec with personalized/baseline Gate B and age adaptation.
- BackendWorkflowResultV2: shared scene, per-band V2 spec/mode, personalized/fallback counts, unavailable bands and legacy result.

## Semantic safeguards

- Concept matching is reviewed/catalog-backed; runtime AI does not invent activity IDs or bypass P1 hard rules.
- Negative phrases are scoped so an unrelated competing observation does not erase a valid concept-family match for another observed concept.
- Baseline fallback always uses the canonical scene anchor and is reported as AGE_BASELINE_FALLBACK, never as personalized.
- Story and handoff payloads include experience_mode, story_mode, semantic_match_v2, scene_understanding_id and age_adaptation_v2.
- Feedback decision is PLACEHOLDER_CREATED while feedback_status remains NOT_ATTEMPTED.

## Deferred scope

UI, PixiJS runtime animation, video generation, real caregiver/guide confirmation, durable persistence, and production catalog approval remain deferred.