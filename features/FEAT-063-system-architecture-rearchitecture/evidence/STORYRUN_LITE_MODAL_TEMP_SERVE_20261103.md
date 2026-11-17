# StoryRun-lite temporary Modal serve — 2026-11-03

Status: **BLOCKED at Modal health**. The one synthetic Parent inference flow is **NOT RUN**; actual inference HTTP requests sent: **0**. No result, live ledger or subject confirmation is claimed.

## Configuration and local gates

- Modal CLI 1.6.3 authenticated to the existing `main` environment. The named Qwen Volume, config/tokenizer/processor/index and four model shards, and the named auth Secret were present. The local DPAPI bearer backup was readable as a SecureString; its value was not printed or persisted in evidence. Secret identity/presence does not prove the bearer matches the remote Secret.
- Real ClamAV on loopback returned CLEAN for the selected synthetic PNG (SHA-256 `030EBBDA7604C0B7235AC6E6BB54894443615376C5F85A09805A68F752D81571`) and INFECTED for the in-memory EICAR sample. The previously recorded worker suite had passed 18/18. The task scanner was stopped after use.
- A new PostgreSQL 17.11 task-owned DB `storyrun_lite_6f84a04faaac492eb0a7`, loopback port 5433, user/owner `postgres`, was created and verified; only `story_run_lite@head` was migrated. Existing DBs were not reset or dropped. Synthetic HTTP bootstrap equivalent to collection steps 01–05 returned create run **201**, create upload **201**, upload part **200**, complete **202**, and GET upload **200 READY**. The bootstrap API stopped before attach; the task DB and quarantine remain for inspection. This run used a temporary HTTP helper, not Bruno CLI.

## Modal and code checks

- A temporary `modal serve` used a task-local archive of committed `a88de875ff92e9b4d4fa5cc2f5f8d5fc1f626f58` files, excluding unpublished worktree changes. Modal reported app `ap-r6Ex8GdPrXPylyESiMzmr7` and a regional HTTPS endpoint. A single GET `/health` timed out after 100 seconds. Direct DNS lookup and TLS connection succeeded, but the app listing showed **0 tasks**, the container list was empty and fetched app logs had **0 lines**. These observations do not establish why health failed; model readiness is unverified.
- The actual endpoint has a regional label under `modal.run`; the earlier bridge hostname validator rejected it. Within the existing bridge/test allowlist, validation was extended to valid DNS labels under `modal.run`, with hostname-length and malformed/lookalike rejection retained. Offline bridge/A1 suites after this change: **83 passed, 0 skipped**, 14.71 s; Ruff and repository security validator passed. No live inference was used for this validation.
- Mypy on the two source files returned **2 arg-type errors**: `remove_upload_quarantine` is declared `None` by the repository port but returns `bool` in the SQL repository. Both underlying files match the pre-live snapshot; the `_configured_vision` call is a new diagnostic site, while the exact pre-live total was not measured. Correcting the port is outside the approved source allowlist, so no suppression or out-of-scope edit was made. Mypy is not clean.

## Cleanup and remaining work

The specific temporary app was stopped; Modal reported **stopped, 0 tasks** at `2026-11-03 01:43:48 +07:00`. The serving session, task scanner, bootstrap API and bootstrap console stopped; listeners on the task scanner/API ports were absent. No attach was sent, and there is no post-SENT ambiguity to reconcile. Resolve the health/container startup blocker with the owner before a new live attempt, recheck the scanner and other gates, and retain the one-request/no-retry restriction. No persistent deploy, stage, commit, push or merge occurred. Prior snapshots and reports remain historical.
