# StoryRun-lite guarded Modal integration — 2026-11-03

Status: **OFFLINE VERIFIED / LIVE BLOCKED**. The owner reports that no Modal V2 endpoint is running. No Modal request or deployment was made; the live Parent flow, response, confirmation, duration and live ledger are **NOT RUN**. The measured live HTTP inference count is **0**. This is not a successful live flow or a review acceptance.

## Implementation and boundaries

The approved plan is `plan/STORYRUN_LITE_MODAL_LIVE_20261103.md`; the approval is recorded append-only in `approvals/TASK_APPROVAL.md`. The bridge and composition select an explicit, run-bound Modal HTTPS mode; default loopback remains available. Missing/conflicting settings, unsafe target/token and a different run fail closed. Existing A1 guard, ledger, transport and V2 adapter remain in the path, with one bounded send and no automatic resend after SENT/UNKNOWN. Tests use stubs or loopback; they do not prove the remote endpoint's behavior. No migration or A1 source was changed by this task.

Live operation requires `STORYRUN_LITE_VISION_MODE=modal_live`, `STORYRUN_LITE_MODAL_BASE_URL`, `STORYRUN_LITE_MODAL_RUN_ID` and `STORYRUN_LITE_MODAL_TOKEN` supplied securely. The origin must be an approved HTTPS Modal origin, and the UUID must be the exact previously created synthetic run. Create/admit the run first with the appropriate local configuration, then restart with that run pinned; readiness must be rechecked immediately before the one allowed HTTP inference request. Do not put the token in evidence, command logs or chat. An HTTP request limit does not establish how many model generations the remote server performs internally.

## Actual verification

- Offline bridge and A1 guard/transport pytest suites: **78 passed, 0 skipped**, 14.73 s. Ruff on the three changed Python files: **PASS**.
- Loopback PostgreSQL regression: **3 passed, 0 skipped**, 3.64 s, no timeout. Identity verified: PostgreSQL 17.11, task DB `storyrun_lite_cfc0f21fbb7c4b36bc54`, `127.0.0.1:5433`, user/owner `postgres`, StoryRun-lite migration and synthetic legacy fixture. This is regression evidence, not the new clean DB gate required for live smoke.
- Synthetic worker suite: **18 passed, 0 skipped**, 2.70 s. The earlier full PostgreSQL suite **12 passed** and local Bruno **9/9** are historical results, not rerun here.
- Real ClamAV 1.5.4 with existing signatures returned **CLEAN** on the selected synthetic 512×384 PNG, 2,589 bytes, SHA-256 `030EBBDA7604C0B7235AC6E6BB54894443615376C5F85A09805A68F752D81571`; in-memory EICAR returned **INFECTED / CLAMAV_FOUND**, SHA-256 `275A021BBFB6489E54D471899F7DB9D1663FC695EC2FE2A2C4538AABF651FD0F`. The task daemon was stopped after verification, so readiness must be re-established before live smoke.
- Mypy on the two source files returned **2 errors**, both involving the existing repository/port mismatch for `remove_upload_quarantine` (implementation returns `bool`, protocol declares `None`); the current run includes a new call site and does not establish an independently measured pre-change count. Mypy is **not clean**; no unrelated protocol or runtime changes were made to suppress the diagnostics.
- Harness and architecture validators: **PASS**; repository security validator: initially flagged two non-secret constants by name, then **PASS** after the constants were renamed without changing their values or the validator. `git diff --check`: **PASS**, with existing CRLF warnings.
- Live endpoint, matching secret, fresh live-smoke DB, live upload/run/confirmation and live ledger: **NOT RUN**. No simulated result is substituted for live inference. If a request later reaches SENT and its outcome is ambiguous, stop and retain UNKNOWN without retry.

The pre-edit snapshot is `STORYRUN_LITE_MODAL_LIVE_BASELINE_20261103`; the additive closeout snapshot is `STORYRUN_LITE_MODAL_LIVE_OFFLINE_20261103`. Historical S1→S2 snapshots and prohibitions are not rewritten. Existing worktree changes and task databases are retained. No stage, commit, push, merge or deployment occurred.
