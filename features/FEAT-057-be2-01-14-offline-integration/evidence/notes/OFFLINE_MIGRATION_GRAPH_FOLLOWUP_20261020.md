# Offline migration graph follow-up — 2026-10-20

## Scope and source

Source HEAD: `d35f035f87fddfc87b0d72d8929f5b1b843fce0e`, branch
`feature/be2-backend-ai-integration`. The 08–14 recheck receipts describe
the source **before** the uncommitted F057-H01 integration-test fix. No product
module changed. Only `backend/tests/integration/ai_jobs/test_migrations.py` changed after those runs
(`f3e907442ee228ac45c25834ddc91ee7f27678b2178487062b6d4e331df15d22` → `9b507b7f342a8c863062ed4ff6865a6e5012a804c41b360199f7cadaf3c03d46`).
The recorded `source_unchanged=true` applies during each recorded run; its full
source hash map is historical after this single-file change. Those suites were
not rerun on the new test snapshot. Fresh evidence covers the three affected
offline migration nodes and four guard-probe scenarios only.

FEAT-057's approved offline integration plan permits bounded reproducible
integration fixes. F057-H01 is a stale integration-test expectation, not an
environment dependency failure or a product defect. No migration revision,
schema, app/service module, approval or accepted checkpoint was changed.

## Failure, correction and verification

The exact original node
`test_script_graph_keeps_be1_history_and_adds_independent_ai_jobs_branch`
failed once: it required the entire graph to have exactly two heads. The merged
candidate already has nine independent schema heads. The correction requires
the exact head set for each owned branch (`be1_core`, `ai_jobs`); unrelated
schema heads are allowed. Exact BE1 lineage, AI root/branch/dependency checks,
test IDs, test count and skip rules remain intact. Ruff also organized existing
imports in this touched test file.

- Before: 1 FAIL, pytest exit 1 (real two-versus-nine assertion).
- After: 3 PASS, 0 SKIP, pytest exit 0. Nodes: the original graph test,
  `test_plain_head_is_ambiguous_and_refused`, and
  `test_metadata_is_scoped_to_ai_jobs_without_foreign_owner_keys`.
- Guard probes: actual nine-head graph accepted; split AI head, missing AI head,
  and moved BE1 head rejected. Four scenarios PASS.
- Ruff PASS; mypy `--strict --follow-imports=silent` PASS for this test file.
- Independent code review: no actionable findings; owned sets preserve split
  detection and original lineage assertions.

Interpreter: existing backend venv, CPython 3.12.10. Plugin autoload was disabled;
the selected graph/metadata tests do not request the PostgreSQL fixture. Python
audit hooks rejected socket connect/bind/DNS, subprocess and shell calls during
the pytest/probe execution; **no external attempt was recorded**. A preliminary
instrumentation attempt blocked Python's Windows platform metadata subprocess
before collection (exit 4); that is retained locally as an instrumentation
failure, separately from the actual before-fix pytest failure. Caching platform
metadata before the guard resolved it. Initial Ruff import-order failure and
the later passing run are both retained; neither is hidden as an all-green run.

Raw scripts/logs, initial dirty-input byte backups, environment inventory and
receipts remain ignored under `evidence/local/handoff-sync-20261020/`.
Sanitized verification logs and a machine-readable fix receipt are in
`../raw/handoff-sync-20261020/`. See `../metrics/HANDOFF_SYNC_20261020.json`
for integrity and final validators.

## Boundaries

The foundation worktree retains the original test; the frozen A17 ZIP, runner,
manifest and README retain their recorded hashes. This correction belongs to
the integration candidate and is not injected into the A17 package.

No Lightning/Studio, provider, HTTP/app/service, PostgreSQL or Redis execution,
package installation, new credential, staging, commit, push, PR or dev/main merge.
Card approval/status/acceptance records remain unchanged. Integration stays
IN_PROGRESS; the environment-limited pack is not PASS and no card becomes DONE.

