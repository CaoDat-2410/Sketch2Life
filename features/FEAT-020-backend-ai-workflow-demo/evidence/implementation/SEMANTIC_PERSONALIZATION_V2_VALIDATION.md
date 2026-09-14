# Semantic Personalization V2 Validation

Date: 2026-09-13
Status: PASS

## Scope validated

- shared age-invariant scene understanding;
- 100 unique semantic profiles;
- concept-family routes for sun/light, moon, flower/plant and nature;
- explicit personalized vs age-baseline fallback modes;
- V2 manifest/spec/band contracts and hashes;
- V1 compatibility;
- CLI V2 default and V1 opt-in;
- no UI, PixiJS runtime or video generation changes.

## Commands

- python -m compileall -q backend/src/sketch2life
- python -m ruff check on all modified source and test files
- python -m mypy --strict on the six modified V2/workflow/CLI modules
- python -m pytest backend/tests/unit/test_semantic_personalization_v2.py backend/tests/unit/test_activity_semantics.py backend/tests/unit/test_p1_experience.py backend/tests/unit/test_p1_online_model_compatibility.py backend/tests/contract/test_health.py backend/tests/e2e/test_lightning_backend_workflow.py -q
- python -m pytest backend/tests -q --basetemp backend/.pytest-temp-v2

## Results

- compile: PASS;
- Ruff: PASS;
- strict mypy: PASS, no issues in six source files;
- targeted suite: PASS, with the real-AI E2E skipped unless SKETCH2LIFE_RUN_REAL_AI_E2E=1;
- full backend suite: PASS when using the workspace-local basetemp. The first default-temp run was blocked by host pytest-of-docao PermissionError, not by an assertion or implementation failure.

The in-memory integration test confirmed one shared scene ID across all four age bands and a deterministic split between personalized and baseline modes for a sun scene. Runtime production/demo acceptance continues to use real ASR/VLM adapters; the in-memory adapter exists only for unit isolation.