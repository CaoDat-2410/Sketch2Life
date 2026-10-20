# FEAT-057 evidence

Store the candidate merge receipt, conflict notes, offline command summaries,
test results, and final review handoff here. Keep secrets, local absolute paths,
temporary credentials, and real child data out of this directory.

The active session's runtime access check and verified A17 package hashes are
recorded in `notes/LIGHTNING_SESSION_ACCESS_20261020.md`; this does not replace
the pending named-Studio inventory or A17 run.

The cross-card BE2-01–14 future runtime gates, verified command entrypoints,
dependency order, exact frozen task-01 package identity, and stop conditions are
in `notes/BE2_01_14_RUNTIME_READINESS_20261020.md`; machine-readable task states
are in `metrics/BE2_01_14_RUNTIME_READINESS_20261020.json`. These are planning
receipts only; no Lightning/runtime command was executed.

The 2026-10-20 task 08–14 offline recheck is in
`notes/LOCAL_OFFLINE_RECHECK_20261020.md` and
`metrics/LOCAL_OFFLINE_RECHECK_20261020.json`. Runner summaries are preserved
under each task card's own `evidence/raw/` directory; outcomes do not alter
card acceptance or runtime readiness.

The ready-to-paste prompt for the primary BE2 session is in
notes/MAIN_BE2_SESSION_HANDOFF_PROMPT_20261020.md.

## Primary-session synchronization

Current handoff: `notes/PRIMARY_SESSION_HANDOFF_20261020.md`.
Current matrix: `metrics/offline-test-matrix.json`; exact earlier matrix/report
are retained under `raw/handoff-sync-20261020/MERGE_TIME_*`.
Scoped migration-test correction: `notes/OFFLINE_MIGRATION_GRAPH_FOLLOWUP_20261020.md`.
Final validators, preserved-source checks and snapshot binding:
`metrics/HANDOFF_SYNC_20261020.json`. Raw local scripts/backups remain ignored
under `local/handoff-sync-20261020/`; no old receipt was overwritten.

The 2026-10-20 goal continuation is recorded in
`notes/GOAL_OFFLINE_BASELINE_HANDOFF_20261020.md` and
`metrics/GOAL_OFFLINE_BASELINE_20261020.json`. The initial dirty-worktree
manifest is `metrics/GOAL_BASELINE_20261020.json`; fresh environment and
validator logs are under `raw/goal-offline-20261020/`. The component batch
remains NOT_RUN pending its declared test dependencies and separate install
authorization.

## Final approved offline baseline — 2026-10-20

The prior incomplete snapshot above records the state before environment
authorization. The user authorized the isolated environment in
`approvals/LOCAL_ENVIRONMENT_APPROVAL_20261020.md`. Final source-bound results
and reconciliation are in
`metrics/GOAL_OFFLINE_BASELINE_FINAL_20261020.json`; package/import checks and
final validators are under `raw/goal-offline-20261020/`. Each owning card's
`evidence/README.md` links its final pinned runner receipt and note. BE2-08–14
local offline baseline PASS; card acceptance/status and external runtime
gates remain open.

## Final offline baseline — 2026-10-20

All seven task 08–14 runners passed under the isolated pinned environment. Final result: metrics/GOAL_OFFLINE_BASELINE_FINAL_20261020.json; per-task receipts are in each owning feature evidence folder. SQL execution, PostgreSQL, runtime and Lightning remain NOT_RUN. Current handoff: notes/PRIMARY_SESSION_HANDOFF_20261020.md.
