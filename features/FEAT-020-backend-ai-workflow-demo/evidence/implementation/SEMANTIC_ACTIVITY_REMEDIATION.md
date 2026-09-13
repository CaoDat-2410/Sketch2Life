# FEAT-020 Semantic Activity Remediation Evidence

**Date:** 2026-09-13
**Status:** IMPLEMENTED — VALIDATED

## Implemented boundary

- SemanticActivityProfileV1 and SemanticMatchEvidenceV1 provide versioned, auditable semantic evidence.
- ActivitySemanticCatalog loads 100 profiles, validates unique activity coverage and four age-band fallback profiles, then performs deterministic exact/alias/negative/fallback matching.
- BackendAiWorkflow now uses load_p1_template_library(..., include_mvp=True) and the semantic catalog before P1 compilation.
- Match strength is explicit in the manifest; exact/alias matches outrank safe fallbacks, and safe fallback narration does not claim an observed concept.
- AgeMatrixSummaryV1 distinguishes strict success, test-only partial success and fail-closed unavailable bands.
- MVP material groups and scalar/ranged durations are preserved in activity handoff metadata.
- The real-AI acceptance path remains adapter-only. No fixture adapter, UI, video generator or runtime PixiJS asset generation was added.

## Reproducible validation

From repository root:

    backend\.venv\Scripts\python.exe -m compileall -q backend\src\sketch2life backend\tests
    backend\.venv\Scripts\ruff.exe check <remediation source and test files>
    backend\.venv\Scripts\mypy.exe <7 remediation source files>
    backend\.venv\Scripts\python.exe -m pytest backend\tests\unit\test_activity_semantics.py backend\tests\unit\test_p1_experience.py backend\tests\unit\test_p1_online_model_compatibility.py backend\tests\contract\test_health.py backend\tests\e2e\test_lightning_backend_workflow.py -q

Observed results:

- compile/import smoke test: PASS;
- targeted Ruff: PASS;
- strict mypy for the seven remediation source files: PASS;
- targeted tests: PASS; real-AI E2E is skipped unless SKETCH2LIFE_RUN_REAL_AI_E2E=1;
- semantic regression coverage includes bình minh, bướm bay, mặt trăng, negative phrases and safe fallback through Gate B.

The full suite was also attempted. On this Windows host, pytest initially could not create its default system TEMP\pytest-of-* directory (PermissionError: WinError 5), so that result is recorded as an environment permission limitation rather than a feature assertion failure. The feature-targeted suite above does not depend on that system temp directory.

## Expected Lightning behavior

Run the existing real-AI CLI with the model environment configured. A strict all-age run returns SUCCEEDED/BACKEND_CONTEXT_READY only when all requested bands reach a valid handoff. If a test run intentionally uses --report-partial-test-only, the manifest may return PARTIAL_SUCCESS/BACKEND_CONTEXT_PARTIAL and explicitly lists ready_age_bands and unavailable_age_bands.
Governance validation:

- python tools/validate_harness.py: HARNESS_VALID
- python tools/validate_repository_security.py: REPOSITORY_SECURITY_VALID