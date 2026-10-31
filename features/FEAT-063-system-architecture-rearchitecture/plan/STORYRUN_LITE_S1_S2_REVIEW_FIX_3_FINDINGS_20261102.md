# StoryRun-lite S1→S2 independent review fixes — scoped plan — 2026-11-02

Plan status is controlled by the append-only entry in `approvals/TASK_APPROVAL.md` that names this file's exact SHA-256. This plan does not itself authorize source changes. Do not edit it after approval; any scope change needs a separately approved addendum.

## Authority and preserved baseline

- Authority: the Project owner's direct request in the current thread to fix exactly two P2 findings (upload/cancel lifecycle and expiry) and one P3 finding (OpenAPI/runtime response parity), and to append a matching approval before source edits.
- Repository baseline: branch `feature/feat063-be-foundation`, HEAD `a88de875ff92e9b4d4fa5cc2f5f8d5fc1f626f58`, index empty at scope time. The workspace already contains 135 local Git-visible paths; preserve them unless a path is explicitly allowlisted below.
- Preserve all 35 FEAT-061/FEAT-064 protected paths byte-for-byte, including A2 and the three FEAT-061 documents. Preserve the original S1→S2 baseline manifest and both previous snapshots. The roadmap remains at the owner-approved rebaseline SHA-256 `875E93C59085DA9C38923DB85EEE50D15945CBD38EC27EC0B6389B93B3ECB8D4`; do not edit it or describe B881 bytes as preserved.
- Applicable design limits: V12 §9.4 and §10, the approved S1→S2 execution plan, and this exact review-fix approval. Reuse existing `ABORTED` and `EXPIRED` states. No schema, migration, state, purge worker, durable purge state, or expiry tombstone is added.

## Findings and acceptance criteria

### P2 — cancel closes unfinished uploads for its run

1. Validate actor ownership and `INPUT_PROCESSING` run state inside the same database transaction that creates an upload session; the run row is locked so cancellation cannot race a preflight check.
2. Serialize upload create, part, completion, admission finalization and run cancellation using a consistent `StoryRun`-then-`UploadSession` row-lock order. `PUT` and completion reject a session whose target run is no longer accepting uploads.
3. In the cancellation transaction, move the run to `DELETE_PENDING` and every unfinished `RECEIVING`, `PENDING` or `PROCESSING` upload session for that run to terminal `ABORTED`; increment each upload version and close its admission gate/claim in the same commit.
4. Admission gate opening and worker finalization recheck the run and upload claim under the same lock order. If cancel commits first, no session becomes `READY` and no asset metadata row is created. A late worker removes only its own newly staged asset files and exits; it does not claim that an external provider stopped.
5. After terminal state commits, remove each affected upload's staging parts and snapshot synchronously, best-effort. A database integration test covers cancel racing completion/admission and verifies no orphan `READY` result; filesystem assertions verify successful cleanup.
6. A new upload against a canceled run is rejected. A receiving session's part and complete requests cannot add bytes, open admission, or finish after cancellation.

### P2 — enforce the published expiry

1. Compare `expires_at` with an aware UTC clock (`expires_at <= now`) before GET response, new part acceptance and a new complete reservation. An expired `RECEIVING` session transitions once to `EXPIRED`, increments its version, and has admission gate/claim cleared.
2. GET, part and complete on an expired session return HTTP 410 with `UPLOAD_EXPIRED`. Part writes, snapshot assembly, admission and `READY` asset creation do not occur. Exact finalized idempotency receipt replay remains the original response snapshot.
3. Startup recovery transitions expired `RECEIVING` rows and retries idempotent staging cleanup for existing `EXPIRED` rows. Cleanup runs after state commit and is best-effort; no durable sweeper, purge state or tombstone is introduced.
4. Integration coverage uses controlled DB timestamps, not a real TTL wait. Cover just-before/at-or-after-expiry behavior, GET/PUT/complete, terminal version and replay behavior, startup recovery and part/snapshot cleanup. Never delete an asset already attached to an active StoryRun.

### P3 — make runtime and OpenAPI agree

1. OpenAPI declares PUT part responses 411 `CONTENT_LENGTH_REQUIRED` and 415 `UNSUPPORTED_MEDIA_TYPE`; 428 `PRECONDITION_REQUIRED` for attach, confirmation, cancel, complete and abort; and 410 `UPLOAD_EXPIRED` for expired part/complete as well as GET. Add missing error enum members and declare `If-Match` on confirmation.
2. Every runtime 202 response emits a relative `Location` to the corresponding StoryRun or upload-session GET resource, a uniform positive integer `Retry-After`, the existing ETag and `Cache-Control: no-store`.
3. Contract tests exercise actual status/error responses and all 202 routes, assert headers/ETag, and verify runtime/OpenAPI/Bruno operation parity. README and Bruno remain unmodified if their current instructions do not contradict the contract; if a required edit is outside this plan's allowlist, stop and request a new scope.

## Verification and stop conditions

- Add focused contract, unit where appropriate, PostgreSQL transaction and HTTP-loopback tests. Rerun the recorded offline S1→S2/A1 regression set with the new tests. Loopback calls must target `127.0.0.1` only; make no external network, provider, Modal or GPU calls.
- PostgreSQL tests may run only on a new uniquely named `storyrun_lite_*` database created for this task on loopback after independently verifying the connected owner. If that cannot be proven, skip all PostgreSQL setup/migration and report those tests `NOT RUN`; never connect to, inspect, migrate or clean any existing/default/A2 database. Do not inspect `.env` files.
- Run Ruff, mypy, repository harness, security and architecture validators, plus `git diff --check`. Report actual results and distinguish them from the prior 125-pass report. Do not relax assertions.
- Update only the new review-fix evidence, an append-only status entry, and a new additive local snapshot. Record findings, files, test commands/results, DB ownership/cleanup if used, cleanup limitations, protected-path audit and exact hashes. Leave prior evidence and snapshot directories untouched.
- Final status after acceptance: `FIXED — XONG-CHƯA REVIEW`. This is implementer handoff only; do not claim independent review ACCEPTED or Modal/live readiness.

## Exact allowlist

### Plan and approval/status/evidence/snapshot

- `features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_S1_S2_REVIEW_FIX_3_FINDINGS_20261102.md` (this immutable plan)
- `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md` (append this approval only)
- `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md` (append review-fix status only)
- `features/FEAT-063-system-architecture-rearchitecture/evidence/STORYRUN_LITE_S1_S2_REVIEW_FIX_20261102.md` (new)
- `.claude/handoff/snapshots/STORYRUN_LITE_S1_S2_REVIEW_FIX_20261102/` (new `files.txt`, `hashes.csv`, `diff.patch`; never overwrite a prior snapshot)

### Source and tests

- `backend/src/sketch2life/infrastructure/story_run_lite/repository.py`
- `backend/src/sketch2life/application/services/story_run_lite.py`
- `backend/src/sketch2life/interfaces/http/routers/story_run_lite.py`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/storyrun-lite/openapi.json`
- `backend/tests/contract/test_story_run_lite_api.py`
- `backend/tests/integration/test_story_run_lite_postgres.py`
- `backend/tests/integration/test_story_run_lite_loopback.py`
- `backend/tests/unit/test_story_run_lite_domain.py` only if required by the behavior tests

No other source, migration, database, A2, FEAT-061/FEAT-064, README, Bruno, roadmap, baseline or historical snapshot path is authorized by this plan.
