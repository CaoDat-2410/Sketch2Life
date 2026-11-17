# FEAT-023 evidence

Store all objective migration, replacement-selection, Top-5 trace, duration,
offline corpus, Lightning smoke, and security evidence here. Do not store raw
provider output or sensitive child media in publishable evidence.

Current evidence:

- metrics/offline-report.json: 100-case deterministic catalog/matcher report.
- notes/REPLACEMENT_DECISION.md: coverage-based family replacement record.
- notes/VALIDATION_20260914.md: implementation and verification summary.
- fixtures/offline-corpus.v1.json: fixed provider-free offline corpus.
- fixtures/demo-cases.v1.json: baseline and second replaceable image/audio
  input pairs for backend smoke runs.
- notes/DEMO_CASE_02.md: case 02 command, scope and asset verification.

The Lightning smoke report is intentionally not fabricated; it remains a
release-candidate task for the target model runtime.
