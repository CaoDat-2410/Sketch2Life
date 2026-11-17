# FEAT-023 validation — 2026-09-14

## Working-tree implementation checks

- Harness: python tools/validate_harness.py — HARNESS_VALID.
- Targeted regression suite: catalog, semantic personalization, P1 compiler and
  activity semantics — passed.
- Full backend unit suite: passed after setting a writable workspace temp
  directory; five tests were skipped by the existing suite.
- Ruff on changed modules/tests — passed.
- Strict mypy on changed modules — passed.

## Offline corpus

Command:

backend/.venv/Scripts/python.exe -m sketch2life.benchmark.catalog_offline --repo-root . --output features/FEAT-023-catalog-contract-hardening/evidence/metrics/offline-report.json

The report is CatalogOfflineEvaluationReportV1, built from the fixed
provider-free corpus in fixtures/offline-corpus.v1.json.

Observed results:

- 100 scenes across all four age bands;
- 300 selectable profiles on catalog-2026-09-expansion-2;
- 0 no-match scenes;
- 0 concept mismatches and 0 objective mismatches;
- same-seed reproducibility failures: 0;
- different-seed selection changes: 48;
- top activity share: 3%;
- top family share: 8%;
- 81 distinct activities and 37 distinct families selected;
- butterfly candidates: 4 in every age band.

## Release blocker

The real-AI Lightning smoke remains pending. It must be run in the user's
Lightning Studio because the local workspace does not contain the Qwen/Whisper
model weights or the target CUDA runtime. The pending result is a runtime/model
validation gate, not an offline catalog or matcher failure.
