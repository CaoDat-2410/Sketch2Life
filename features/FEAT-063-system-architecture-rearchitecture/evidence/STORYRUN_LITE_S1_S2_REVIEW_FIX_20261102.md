# StoryRun-lite S1→S2 independent review fixes — implementation evidence — 2026-11-02

## Outcome

**FIXED — XONG-CHƯA REVIEW.** The approved three-finding scope is implemented. Independent review has not happened, and PostgreSQL-backed lifecycle verification is **NOT RUN** because no task-owned database URL was available. The database race and controlled-expiry tests were added but skipped; this report does not claim their runtime acceptance.

Authority and exact scope: `plan/STORYRUN_LITE_S1_S2_REVIEW_FIX_3_FINDINGS_20261102.md`, SHA-256 `D68FFBC1F251E367797DCAD0C6252D08797EA7ED19CC35DC2033B906C9A09D47`, approved in the append-only entry in `approvals/TASK_APPROVAL.md` before source edits.

## Findings addressed

### P2 — upload/cancel lifecycle race

- Upload creation now checks owner and run state while holding the StoryRun lock in the same transaction that creates the upload.
- Upload reads, parts, completion, admission finalization and cancellation use StoryRun→UploadSession lock order. Part/complete and admission gates reject work after cancellation commits.
- Cancellation moves unfinished upload sessions to `ABORTED`, closes admission claims and finalizes pending completion receipts in the transaction. Staging cleanup is attempted after commit and reports cleanup failures for later retry where applicable.
- Added PostgreSQL race coverage for cancellation versus completion/admission, staging cleanup, receipt finalization and new-upload rejection. **NOT RUN**; the test fixture skipped because `STORYRUN_LITE_DATABASE_URL` was absent. No database was created or contacted.

### P2 — upload expiry

- GET, part acceptance and new completion reservations enforce an aware-UTC `expires_at <= now` boundary. A receiving session transitions once to `EXPIRED`, increments its state version and closes its admission claim; later operations return 410 `UPLOAD_EXPIRED`.
- Startup recovery expires overdue receiving sessions and retries staging cleanup for terminal expired sessions without another version bump.
- Added controlled-time PostgreSQL tests for just-before/equality expiry, GET/PUT/complete, idempotent receipt replay and startup cleanup retry. **NOT RUN** for the same database-ownership reason above.

### P3 — OpenAPI/runtime parity

- OpenAPI now declares the required 411, 415, 410 and 428 responses and the confirmation `If-Match` header.
- Every tested runtime 202 route emits a relative `Location`, positive integer `Retry-After`, ETag and `Cache-Control: no-store`.
- Contract tests cover the runtime status/error responses and all 202 routes. Existing Bruno and README contracts did not require edits.

## Verification

- Focused offline S1→S2/A1 regression command over StoryRun-lite domain/worker/photo bridge, API contract, PostgreSQL, loopback and Vision bridge/service tests: **126 passed, 9 skipped**. The nine skips are PostgreSQL cases guarded by the absent task-owned database URL; loopback tests used only `127.0.0.1`.
- Ruff on the three changed Python source files and scoped StoryRun-lite contract/PostgreSQL/domain tests: **passed**.
- Mypy with `--no-incremental` on the three changed production source files: **passed, 3 files**.
- `tools/validate_harness.py --feature features/FEAT-063-system-architecture-rearchitecture`: **HARNESS_VALID**.
- `tools/validate_architecture.py`: **ARCHITECTURE_VALID**.
- `tools/validate_repository_security.py`: **REPOSITORY_SECURITY_VALID**, 6,163 publishable files scanned; environment files excluded.
- `git diff --check`: **passed**; Git reported existing CRLF normalization notices only.

The earlier S1→S2 result of 125 passed / 0 skipped remains historical evidence and is not combined with this review-fix run.

## Preservation and boundaries

- Branch `feature/feat063-be-foundation`; HEAD `a88de875ff92e9b4d4fa5cc2f5f8d5fc1f626f58`; index has zero staged paths.
- Roadmap retained at the owner-approved rebaseline SHA-256 `875E93C59085DA9C38923DB85EEE50D15945CBD38EC27EC0B6389B93B3ECB8D4`. The historical B881 hash is not represented as preserved bytes.
- The review-fix snapshot is additive at `.claude/handoff/snapshots/STORYRUN_LITE_S1_S2_REVIEW_FIX_20261102/`; prior S1→S2 and rebaseline snapshots remain unchanged.
- All 35/35 FEAT-061/FEAT-064 protected paths, including A2, match the pre-review rebaseline snapshot hashes.
- No migration/schema/state change, database operation, Modal/GPU/provider call, external network call, stage, commit, push, merge or deploy occurred.

This is an implementer handoff only. It does not claim independent review acceptance, PostgreSQL transaction verification or live readiness.

## Hash-gate clarification — 2026-11-02

The prior stop compared the final report against `STORYRUN_LITE_S1_S2_20261102/hashes.csv`, which is the pre-rebaseline snapshot and correctly retains historical SHA-256 `6171A9E45D7E09F98AE7FF5D2227C75A1DABCDF17AF12DC4FC160BD2E1D24984`. The owner-approved B rebaseline makes `STORYRUN_LITE_S1_S2_REBASELINE_20261102/hashes.csv` the applicable comparison; it records `FC7ED78A5A9E5CEBDA4FB29F391ABD613E3FD7B326782DF194951EE63704F8AC`, matching the current file and the review-fix snapshot. No report bytes or hash records were changed to resolve this gate.

Status remains **FIXED — XONG-CHƯA REVIEW**. PostgreSQL integration tests remain **NOT RUN** because no task-owned database was available.

## Independent review — round 2 — 2026-11-02

### P2 — expiry rechecked after lock waits

- `get_upload`, `put_part` and `reserve_complete_upload` now obtain their UTC comparison time only after `_owned_upload_with_run` has acquired the required StoryRun then UploadSession row locks.
- Startup recovery locks every `RECEIVING` session without filtering by a pre-lock expiry timestamp, then takes a fresh aware UTC time and checks each locked row. Thus a receiving session that expires while recovery is blocked on another unfinished session is still selected and handled.
- Added controlled-clock PostgreSQL regressions with a lock wait crossing an explicit deadline for GET, PUT and complete. Added a recovery test that blocks on a PENDING session until a separate RECEIVING session expires, then asserts EXPIRED/version/cleanup. These tests were collected but **NOT RUN** because no task-owned loopback database was available.
- The locked-wait test assertions cover 410 `UPLOAD_EXPIRED`, one version increment, no additional part, no snapshot/admission, and exact finalized 410 receipt replay for completion. They do not use a two-hour TTL wait.

### P2 — cancel versus admission finalizer

- Added a barrier-controlled PostgreSQL race between `cancel_run` and `finish_upload_admission` with both winner orders. The cancel-wins case records cancel before the finalizer returns false and checks ABORTED, no asset metadata and cleanup. The admission-wins case records admission commit before cancellation and verifies READY plus both asset metadata rows.
- This race test was collected but **NOT RUN**; database-backed race acceptance remains unverified. No provider/GPU cancellation claim is made.

### P3 — runtime/OpenAPI parity

- OpenAPI now declares `Cache-Control: no-store` on each of the five 202 operations, 422 validation responses on cancel and abort, and a reusable 500 `INTERNAL_ERROR` response on all ten operations.
- Expanded the public Error.code enum to cover literal runtime errors, command receipt errors and upload/StoryRun projected errors. `field_errors` and `retry_after_seconds` allow null, matching emitted runtime bodies.
- Contract tests exercise actual 400, 409, 410, 411, 415, 422, 428 and 500 response envelopes, verify nullability, check all eight validation-capable operations, and assert Location, Retry-After, ETag and Cache-Control across all five runtime 202 routes. Location values target the corresponding StoryRun or upload GET route. The Bruno operation inventory remains aligned; no README/Bruno changes were needed.

### Round 2 verification and limits

- Focused offline S1→S2/A1 regression command: **135 passed, 15 skipped**. All 15 skipped cases are PostgreSQL integration cases guarded by the absent `STORYRUN_LITE_DATABASE_URL`; this is **NOT RUN**, not a pass. The loopback integration tests targeting `127.0.0.1` in that command passed.
- Ruff on the changed repository and scoped contract/PostgreSQL tests: **passed**.
- Mypy (`--no-incremental`) on the changed production repository and router files: **passed, 2 files**.
- `validate_harness.py --feature features/FEAT-063-system-architecture-rearchitecture`: **HARNESS_VALID**.
- `validate_architecture.py`: **ARCHITECTURE_VALID**.
- `validate_repository_security.py`: **REPOSITORY_SECURITY_VALID**, 6,163 publishable files scanned; environment files excluded.
- `git diff --check`: **passed**, with existing CRLF normalization notices only.
- The standalone `backend/tools/run_story_run_lite.py` offline API runner is **NOT RUN**: it requires a database URL and verifies a loopback goal-owned database before startup. No PostgreSQL binaries, service or task-owned URL were available, so no DB was created or contacted.

The old review-fix snapshot remains unchanged. The final additive round-2 snapshot is nested at `.claude/handoff/snapshots/STORYRUN_LITE_S1_S2_REVIEW_FIX_20261102/ROUND2_20261102/`; it was captured after this evidence and status update. The final report and owner-approved roadmap rebaseline remain unchanged. Status remains **FIXED — XONG-CHƯA REVIEW**, pending independent review and database-backed expiry/race verification.


## Independent review - round 3: P3 persisted GET error codes - 2026-11-02

### Outcome and scope

**FIXED — XONG-CHƯA REVIEW.** This round addresses only P3: the OpenAPI `Error.code` enum omitted codes that can be stored on StoryRun or UploadSession and returned by their GET endpoints. Independent review is pending. No approval, plan, source implementation, migration, or database file was changed.

The approved allowlist covers `artifacts/storyrun-lite/openapi.json`, `backend/tests/contract/test_story_run_lite_api.py`, this evidence file, an append-only status entry, and an additive snapshot under the existing review-fix snapshot directory.

### Runtime code inventory

The audit followed the GET projections in `repository.py` (`_run_body`, `_upload_body`, and `_error_for_code`), the production runtime wiring in `composition.py`, StoryRun failure handling in `application/services/story_run_lite.py` and `photo_bridge.py`, the V2 `VisionErrorCode` enum, and the concrete `WindowsJobObjectImageNormalizer` worker and child-process error results. The production runtime wires that concrete normalizer; the service persists its exception code unchanged (up to 64 characters).

Codes that can be stored for StoryRun and projected by GET StoryRun:

`MODEL_INPUT_NOT_ADMITTED`, `STORY_RESULT_PERSISTENCE_UNKNOWN`, `VISION_ADAPTER_FAILURE`, `VISION_ATTEMPT_FAILED`, `VISION_ATTEMPT_HOLD`, `VISION_ENDPOINT_NOT_ALLOWED`, `VISION_INPUT_NOT_VALIDATED`, `VISION_LEDGER_FINALIZATION_UNKNOWN`, `VISION_LOOPBACK_NOT_CONFIGURED`, `VISION_OUTCOME_UNKNOWN`, `VISION_PROHIBITED_CLAIM_DETECTED`, `VISION_RESPONSE_INVALID`, `VISION_RESULT_CAS_LOST`, `VISION_VISION_MODEL_UNAVAILABLE`, `VISION_VISION_PROVIDER_FAILURE`, `VISION_VISION_SCHEMA_INVALID`, `VISION_VISION_TIMEOUT`.

Codes that can be stored for UploadSession and projected by GET UploadSession:

`IMAGE_DECODER_UNAVAILABLE`, `IMAGE_HASH_MISMATCH`, `IMAGE_INFECTED`, `IMAGE_INVALID`, `IMAGE_NORMALIZATION_FAILED`, `IMAGE_TOO_LARGE`, `IMAGE_WORKER_FAILED`, `MODEL_INPUT_TOO_LARGE`, `QUARANTINE_UNAVAILABLE`, `SCANNER_UNAVAILABLE`, `STAGING_UNAVAILABLE`, `UNSUPPORTED_MEDIA_TYPE`, `UPLOAD_EXPIRED`, `UPLOAD_SESSION_STATE_CONFLICT`, `WORKER_GATE_CLOSED`, `WORKER_LIMITS_UNAVAILABLE`, `WORKER_TIMEOUT`.

The existing closed enum was retained and expanded from 37 to 59 values (22 additions); it was not changed to an open-ended string. This includes both review examples: `VISION_LOOPBACK_NOT_CONFIGURED` and `MODEL_INPUT_TOO_LARGE`.

### Contract coverage

Added `test_get_projection_runtime_error_codes_are_declared_by_openapi`. It exercises both GET routes through the HTTP test client with representative persisted error bodies produced by the repository's shared `_error_for_code` projection, verifies each 200 response references the corresponding `StoryRun` or `UploadSession` schema, verifies each `error` references the shared `Error` schema, and checks the complete runtime code sets against `Error.code.enum`.

### Verification and limits

- `backend/.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider tests/contract/test_story_run_lite_api.py`: **20 passed**.
- Ruff on `backend/tests/contract/test_story_run_lite_api.py`: **passed**.
- OpenAPI JSON parse: **OPENAPI_JSON_VALID**.
- `python tools/validate_harness.py --feature features/FEAT-063-system-architecture-rearchitecture`: **HARNESS_VALID**.
- `python tools/validate_repository_security.py`: **REPOSITORY_SECURITY_VALID**, 6,163 publishable files scanned; environment files excluded.
- `python tools/validate_architecture.py`: **ARCHITECTURE_VALID**.
- `git diff --check`: **passed**; Git emitted existing CRLF normalization notices.
- Mypy was attempted on the changed contract test but returned an internal error (mypy 1.20.2) without a type-check verdict. No production Python source changed in this round.
- PostgreSQL tests: **NOT RUN**. No task-owned `STORYRUN_LITE_DATABASE_URL` was available; `DATABASE_URL` and `TEST_DATABASE_URL` were also unset. No database was created, opened, migrated, or queried. The standalone database-backed runner was not run.
- No Modal, GPU, provider, or external network calls were made.

The additive round-3 snapshot is recorded under `.claude/handoff/snapshots/STORYRUN_LITE_S1_S2_REVIEW_FIX_20261102/ROUND3_20261102/`; the Round2 and all earlier snapshots remain unchanged. The snapshot manifest records file hashes and explicitly excludes the hash of its own `hashes.csv` to avoid a self-reference.

Branch remains `feature/feat063-be-foundation`, HEAD remains `a88de875ff92e9b4d4fa5cc2f5f8d5fc1f626f58`, and no paths are staged. The round-2 manifest comparison found only the allowlisted OpenAPI and contract-test changes before this evidence/status append; all 35/35 protected FEAT-061/FEAT-064 paths remained byte-identical. No stage, commit, push, merge, or deployment occurred.


## Independent review - round 4: exercise production GET projections - 2026-11-02

### Outcome and scope

**FIXED — XONG-CHƯA REVIEW.** This round only strengthens the P3 contract tests. OpenAPI and production source are unchanged. The previously approved allowlist permits the contract test, this evidence file, an append-only status entry, and a new additive snapshot; no scope expansion was needed.

### Production projection coverage

Removed the two special GET response cases from `_StubService` and removed the test's direct use of `_error_for_code` to synthesize endpoint responses. The added tests instantiate the real `StoryRunLiteService` and `SqlStoryRunLiteRepository`, pass them to the real FastAPI application, and call each GET route through `TestClient`.

- `test_get_run_projects_saved_error_code_through_production_repository` gives the fake connection a StoryRun row whose persisted `error_code` is `VISION_LOOPBACK_NOT_CONFIGURED`. The real repository `get_run` and `_run_body` project that row into the HTTP response.
- `test_get_upload_projects_saved_error_code_through_production_repository` gives the fake connection a failed UploadSession row whose persisted `error_code` is `MODEL_INPUT_TOO_LARGE`. The real repository `get_upload` and `_upload_body` project it into the HTTP response; the fake connection returns an empty upload-parts list.
- Both tests assert HTTP 200, equality between `response.error.code` and the row's stored `error_code`, and membership in OpenAPI `Error.code.enum`. The separate inventory/schema test remains and still checks all previously enumerated runtime codes.

The fake engine and connections return only prepared rows/result sequences; no PostgreSQL connection is created. These assertions fail if either production projection omits or misreads its row's `error_code`.

### Verification and limits

- `backend/.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider tests/contract/test_story_run_lite_api.py`: **22 passed**.
- Ruff on `backend/tests/contract/test_story_run_lite_api.py`: **passed**.
- `python tools/validate_harness.py --feature features/FEAT-063-system-architecture-rearchitecture`: **HARNESS_VALID**.
- `python tools/validate_repository_security.py`: **REPOSITORY_SECURITY_VALID**, 6,163 publishable files scanned; environment files excluded.
- `python tools/validate_architecture.py`: **ARCHITECTURE_VALID**.
- `git diff --check`: **passed**; Git emitted existing CRLF normalization notices.
- Mypy was attempted on the changed contract test but returned an internal error (mypy 1.20.2) without a type-check verdict. No production Python source changed in this round.
- PostgreSQL tests and the database-backed runner: **NOT RUN**. `STORYRUN_LITE_DATABASE_URL`, `DATABASE_URL`, and `TEST_DATABASE_URL` were unset. No database was created, opened, migrated, or queried.
- No Modal, GPU, provider, or external network calls were made.

The additive round-4 snapshot is `.claude/handoff/snapshots/STORYRUN_LITE_S1_S2_REVIEW_FIX_20261102/ROUND4_20261102/`. Round3 and earlier snapshots are unchanged. The round-3 manifest comparison before the evidence/status append found only the contract test changed; all 35/35 FEAT-061/FEAT-064 protected paths and all 14 previously hashed snapshot files matched. Round4 files.txt and hashes.csv record the full comparison, omitting the hash of hashes.csv itself to avoid self-reference.

Branch remains `feature/feat063-be-foundation`, HEAD remains `a88de875ff92e9b4d4fa5cc2f5f8d5fc1f626f58`, and the index has zero staged paths. Only the allowlisted contract test, this evidence file, and the append-only status file changed since Round3. Status remains **FIXED — XONG-CHƯA REVIEW**, pending independent review round 4. No stage, commit, push, merge, or deployment occurred.


## Owner-reported independent review round 4 verdict - 2026-11-02

The owner reports that the independent review of the P3 production GET projection contract tests was **ACCEPTED** in round 4. This records the verdict supplied in the current owner instruction; it does not alter earlier review evidence or snapshots, and it is not a claim that runtime verification has completed.

At this checkpoint, PostgreSQL integration tests remain **NOT RUN** and mypy still has **no verdict** because mypy 1.20.2 returned an internal error. Both limits remain open for this runtime-verification goal. The S1-S2 plan remains immutable, including its historical prohibition on Modal/provider execution; it is not edited retroactively.

The review-verdict checkpoint is snapshotted additively at `.claude/handoff/snapshots/STORYRUN_LITE_S1_S2_RUNTIME_VERIFY_20261102/STEP1_REVIEW_ACCEPTED_20261102/`. Branch/HEAD and all existing local changes remain unchanged; no database or provider was used for this record.


### Snapshot capture correction - step 1

Two preliminary step-1 captures were preserved unchanged after verification found inventory defects: the first recorded only two Git-visible status keys, and the second enumerated unrelated ignored snapshots outside this task. Neither preliminary capture is an authoritative manifest. The next additive `STEP1_REVIEW_ACCEPTED_FINAL_20261102` snapshot is the authoritative step-1 checkpoint; it will enumerate the 137 Git-visible paths and only task-relevant ignored snapshots, with every manifest hash checked.


## Runtime verification step 2 - PostgreSQL safety gate - 2026-11-02

The PostgreSQL safety gate is **BLOCKED**. `STORYRUN_LITE_DATABASE_URL`, `DATABASE_URL`, and `TEST_DATABASE_URL` are unset. PostgreSQL 17 and 18 Windows services are running, but no owner-verified task-owned `storyrun_lite_*` target or safe connection configuration is available; the PostgreSQL client/`pg_isready` executables are also absent. Connecting to a pre-existing database to discover or provision a target would cross the task's ownership boundary, so no database connection or creation was attempted.

The full StoryRun-lite PostgreSQL integration test file was invoked with the dedicated URL unset, and its fixture skipped before creating an engine: **0 passed, 0 failed, 12 skipped**. No database was created, connected, queried, migrated, or cleaned. This is not PostgreSQL acceptance.

Per the task's stop rule, execution stops here. Bruno local API verification and the live Modal flow are **NOT RUN**; Modal invocation count is **0**. No live-smoke plan/approval was created because its prerequisite gates were not reached. The review round-4 P3 verdict remains **ACCEPTED**; mypy remains without a verdict due the prior mypy 1.20.2 internal error.

Step-2 evidence/status and the unchanged local workspace are captured additively at `.claude/handoff/snapshots/STORYRUN_LITE_S1_S2_RUNTIME_VERIFY_20261102/STEP2_DATABASE_GATE_BLOCKED_20261102/`. The S1-S2 plan and historical snapshots remain unchanged. No source, OpenAPI, database, UI, provider, or network operation occurred.

## Runtime verification closeout snapshot - 2026-11-02

The additive execution record is `features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_POST_REVIEW_RUNTIME_VERIFY_20261102.md` (SHA-256 `7BF55D4B95F8E3887502DC2889BC50D1F531DA172AC4465AAF32CB3DC8E74807`). The final additive closeout snapshot is `.claude/handoff/snapshots/STORYRUN_LITE_S1_S2_RUNTIME_VERIFY_20261102/STEP2_DATABASE_GATE_BLOCKED_CLOSEOUT_20261102/`; it captures the plan, this evidence, status, the full Git-visible inventory, and task-relevant ignored snapshot inventory. It compares against the prior `STEP2_DATABASE_GATE_BLOCKED_20261102` checkpoint. Earlier reports and snapshots are preserved unchanged.

The runtime verification remains blocked at the PostgreSQL ownership gate. The earlier 12 skips are not DB acceptance; Bruno and Modal remain NOT RUN, with zero Modal invocations. Feature implementation status remains **FIXED — XONG-CHƯA REVIEW** for independent review tracking; runtime verification is not complete. No source, database, provider, or external-network operation was performed.