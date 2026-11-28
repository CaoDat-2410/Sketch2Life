# FEAT-083 continuation evidence — 2026-11-23

Status: INCOMPLETE. No staging, commit, push, provider call, or PostgreSQL test.

Amendment 1 was verified. The sketch-guide route now uses curated builders injected at router composition, with a 404 for an unknown guide. Topic fallback uses app runtime settings and has tests for environment, provider and flag gates. The catalog and topic operations were added to the OpenAPI catalogue and projection. The migration follows `20261123_rv_0001`; Alembic reports 15 down-only and 10 dependency-aware heads. Six migration test files and the composition and guard expectations were updated. The focused migration suite passed 188 tests; the focused guide, topic, OpenAPI, migration and dependency suite passed 174 tests; the legacy-route compatibility suite passed 32 tests.

The full backend baseline and current runs were made with the same Python environment and `--continue-on-collection-errors`. The baseline reported 65 failing/error node IDs and the current run 103, including the same 12 imageio collection errors. The initial difference contains 38 node IDs; migration, OpenAPI, composition and guard failures were subsequently fixed and retested individually, so this is not a final comparison of the latest tree. The raw comparison is `tmp/aiport1/new-failures.txt`.

Unresolved regression examples:

- Eight existing Parent activity worker contract tests fail after the as-specified wholesale Modal workload port. The integration baseline passes those tests. The source worker changes its existing activity schema and parsing; a compatible merge has not been completed.
- Existing Story output tests fail because the imported story schema adds sentence-completeness validation to existing v1 story drafts. The meaning and compatibility of this stricter validation need resolution before changing Phase A behavior.
- The imported Modal story client requires a v3 input including a primary activity and its hash, whereas the integration line's existing story generation uses an earlier worker input. The plan expressly defers attachment of the AI-generated activity set to Phase A. Do not invent activity data to satisfy the worker.
- Ruff reports 37 findings versus 20 on the comparable integration baseline; mypy reports 107 errors versus 35 on the baseline. Some reflect absent optional Modal libraries, but the deltas are not resolved.

Modal tests: 204 passed, 3 skipped, 2 failed because `lmformatenforcer` is absent. Architecture, harness, repository-security and `git diff --check` passed after the latest implementation and test changes. Full backend comparison needs to be rerun after the contract regressions and static findings are resolved. Online PostgreSQL remains NOT RUN; no password-free access was established.
