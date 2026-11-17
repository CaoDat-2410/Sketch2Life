# B5 fix02 Studio attempt: environment recovery and retry — 2026-10-16

- Provenance: **USER_REPORTED_REMOTE**; Codex has no direct Studio access.
- State remains **Q01/B5_FIXED_PENDING_RUNTIME_REVIEW**. B5-R01/R02 remain
  **FIXED_PENDING_RUNTIME_REVIEW**; B6 **NOT_STARTED**. No new code finding or approval.
- The package and source are unchanged from the reviewed fix02 checkpoint; no new ZIP needed.

## What actually happened

The user reported the exact runner's three package checksum checks passing, followed by
`source_state=b4r01_snapshot` and `b5fix02_source_verified=43`. The runner prints this state
after applying and verifying the delta: source has advanced from closed B4 to fix02
manifest `cf196e845d30179c2aa2b89e09970ccaf83777aa6d90fac7b29f68d091ad60d0`.
This is host-side source verification, not successful container/test execution.

Receipt path reported by the user:
`features/FEAT-044-be2-ai-job-foundation/evidence/local/b5fix02-runtime-20261015/run-20261015T170629Z-2560`.
Run ID UTC 2026-10-15 17:06:29 corresponds to 2026-10-16 00:06:29 Asia/Saigon.
The Docker image pull completed; Docker then failed to start the runner container because
network `sketch2life-be2-net` was absent. Exact final codes: `outer_runner_exit=125`,
`RUNNER_RESULT=FAIL`, `studio_command_exit=125`. No container suite or fixture runner started.
The printed receipt path does not imply container provenance/test receipts were created.

The user confirmed the Studio had just restarted and identified the existing recovery script:
`/teamspace/studios/this_studio/rebuild_be2_env.sh`.
The local reviewed copy is `evidence/local/studio-env-rebuild-20261015/rebuild_be2_env.sh`, SHA-256
`28950e637d27883bd4df8e5a92a6fc0b6d03284cec0a619a2ca9ce578c4b79d8`.
Prior synthetic-environment recovery authorization applies; no new provisioning scope is added.

## Recovery and exact next step

1. On the same dedicated Studio, run the existing `rebuild_be2_env.sh` and capture its exit.
   It creates missing BE2 network/volumes/containers, starts retained containers, reuses the
   private password and venv volume, runs the constrained dependency installation, then checks
   health, dependency consistency, authenticated PostgreSQL and Redis connectivity.
   It does not reset/delete source, data or volumes or run application migrations. The private
   password file must already exist. Existing resources are matched by name; if a partial or
   incompatible environment fails, diagnose the output rather than replacing credentials,
   deleting volumes or creating another Studio. The log proves missing network, not that all
   Docker data was lost. No recovery success has yet been reported for this attempt.
2. Only after `ENV_REBUILD_RESULT=PASS` and command exit zero, rerun the **same** fix02 runner
   in `$HOME/be2-b5-fix02-package/`. Exact fix02 source follows
   `source_state=b5fix02_snapshot_verify_only`; no second patch application is needed.
   The Docker-125-then-retry path was already covered by the reviewed host checks.
3. Preserve actual output. Expected, not observed: 193 B2–B5 passed and 224 Phase A passed,
   zero suite skips, all suite/tee/outer/Studio exits zero, fixture digest unchanged.
   Review the actual source-bound run before closing B5; do not begin B6 automatically.

Latest reported **source** is now fix02, host-verified. Latest reported **passing runtime**
remains the earlier B4 `f1c6834f` run (104 B2–B4 + 224 Phase A, zero skips). These are distinct
checkpoints. Local review evidence remains 97 passed / 96 PostgreSQL–Redis NOT_RUN and
223 Phase A passed / 1 local Pillow skip. No local backend, tests, package, approved plan,
ADR, approval or real Git index was changed by this recovery documentation step.

See matching metrics JSON and ignored `evidence/local/studio-env-retry-20261016/` receipts.
Current handover §Y supersedes §X only for this environment/source checkpoint. Same 14 cards,
WIP 1, full-card DONE 0; OwnerFence remains ASSUMED_CONTRACT. No commit, push or deploy.
