# FEAT-025 implementation evidence

Date: 2026-09-15

## Delivered

- `BackendAiWorkflow` no longer imports or constructs infrastructure classes.
- Added application-owned `WorkflowDependencies` and catalog/media/asset ports.
- Added the infrastructure `FileWorkflowCatalogMetadata` adapter for authored
  material and duration metadata.
- Centralized real workflow construction in
  `build_real_workflow_dependencies()` at the CLI composition root.
- Preserved typed `ASSET_CATALOG_MISS` propagation from composition failures.
- Added architecture-boundary, metadata, and composition-root regression tests.
- Corrected Qwen mapping diagnostic typing to the V2 closed enum.

## Verification

- Focused regression suite: passed, including Qwen adapter, schema-path,
  semantic personalization, and workflow dependency tests.
- `python -m compileall -q backend/src backend/tests`: passed.
- Ruff on all changed implementation/test files: passed.
- `python tools/validate_architecture.py`: `ARCHITECTURE_VALID`.
- `python tools/validate_repository_security.py` passed immediately after
  FEAT-025 test-artifact cleanup. A later repository-wide rerun is blocked by
  the separate untracked FEAT-026 artifact
  `Sketch2Life_SRS_Form_qa.pdf`, which the security policy classifies as an
  external-document suffix.
- `python tools/validate_harness.py`: blocked by the same separate untracked
  FEAT-026 feature missing `evidence/raw` and `evidence/metrics`; FEAT-025
  itself has all required harness paths.

## Known unrelated baselines

The broader unit suite still reports the two previously observed baseline
failures in `test_feat018_live_lightning_execution.py` (wall-clock value in a
determinism assertion) and `test_media_validation.py` (pinned serialized hash).
They are outside FEAT-025 and unchanged by this implementation. Full mypy is
blocked by the optional `faster_whisper` import not being installed in this
environment; the refactored modules no longer produce the prior type errors.

Real Lightning Studio smoke remains a separate external-runtime gate.
