# FEAT-027 implementation evidence

Date: 2026-09-16

## Delivered

`vision_payload_normalizer.py` now provides the bounded, provider-agnostic
normalization boundary used by the real CLI Qwen adapter. It accepts reviewed
shape drift without inventing scene claims:

- canonicalizes the five observation collections;
- accepts safe singular aliases and bounded result/output/observations/data
  wrappers;
- maps `id`, text aliases, object references, and Vietnamese language values;
- normalizes IDs and remaps references deterministically;
- converts invalid confidence to `null`;
- supplies nullable action references;
- drops relations/themes whose references cannot be proven safe;
- excludes provider metadata from successful contract payloads;
- keeps unknown-only output as a typed mapping failure.

The final object is always validated by `VisionUnderstandingSuccessV2`. No raw
model output or fixture observation is persisted.

## Verification

- Focused regression: passed, including adapter, schema-path, semantic
  personalization, and workflow dependency tests.
- Adapter regression: passed, including wrapper/reference drift and
  unknown-only false-success coverage.
- Python compile: passed.
- Ruff: passed.
- Architecture: passed (`ARCHITECTURE_VALID`).
- Full backend collection: not clean because the local environment lacks the
  optional `av` package required by two pre-existing image-admission test
  modules. After excluding those two modules, the suite completed with two
  unrelated pre-existing failures: one wall-clock determinism assertion in
  `test_feat018_live_lightning_execution.py` and one stale media-validation
  serialized-hash baseline in `test_media_validation.py`.
- Harness/security: repository-wide gates report the unrelated untracked
  `features/FEAT-026-current-system-srs/` missing evidence paths and external
  PDF artifact.

## Pending external verification

Run the real workflow on Lightning Studio with both existing cases. Success
must be judged from the resulting `BackendWorkflowResultV2` and the nested
vision result, not only the process exit code. A successful VLM branch must
have `status=SUCCEEDED` and pass contract validation; an unrepairable model
response must remain a typed failure with closed diagnostics.
