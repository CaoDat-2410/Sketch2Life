# FEAT-059 evidence index

## Source and baseline

- Local base: `dev@0a7ce768c153f2104cff930569c3eda6e484532c`.
- Child UI remote: `origin/FE_UI_Child@ca3779869dfc1385cbbc7b8ca730f780386af7b2` is contained by the local dev merge.
- P2-T5 candidate: remote `origin/feature/feat018-p2t5-evaluation-harness@c345822d`; 28 commits not in dev, with benchmark/tests/evidence; owner directed that it remain separate from FEAT-059.
- FEAT-048 candidate: remote `origin/feature/feat048-srs-diagram-pack@3d8acb30`; 12 commits not in dev, contributing two Mermaid diagrams in the merge-base diff.
- Root workspace excludes the current Child/Teacher/Admin UI folders; the three packages lack a common root test runner today.
- Backend `app.py` is 869 lines and `create_app()` mounts the BE1 runtime plus local/demo routers; backend tests directly call that factory.

The pre-cleanup OpenAPI snapshot is `metrics/baseline_routes.json` (76 paths and 83 operations). The post-cleanup changed-file manifest and hashes are in `metrics/implemented_file_manifest.json`.

## Verification receipts

- `raw/ACTIVE_UI_CHECKS.txt`: aggregate Child/Teacher/Admin typecheck/build/lint/test run.
- `raw/BACKEND_CORE_TESTS.txt`: health, durable session API, and composition regression tests.
- `raw/ARCHITECTURE_VALIDATION.txt`, `raw/HARNESS_VALIDATION.txt`, `raw/SKELETON_VALIDATION.txt`, `raw/SECURITY_VALIDATION.txt`, and `raw/DIFF_CHECK.txt`: repository validators and whitespace check.

## Interpretation

All scoped checks passed. Child ran 20 tests, Teacher 2, Admin 2, and backend 9. The API route/method mapping matched the baseline. Child lint keeps one existing `react(set-state-in-effect)` warning in `useOfflinePacing`; Teacher build keeps its large-bundle advisory. The Child npm audit reported 47 findings (3 moderate, 44 high) after adding test tooling. Dependency upgrades and live provider/service calls were outside scope.
