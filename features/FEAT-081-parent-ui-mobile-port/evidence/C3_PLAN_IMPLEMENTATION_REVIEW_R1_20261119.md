# C3 (FEAT-081 Parent run lifecycle client): independent plan + implementation review R1

Reviewer: Sonnet 5.5, high effort (read-only; this report is the only file written).
Scope: plan `features/FEAT-081-parent-ui-mobile-port/plan/PLAN_FEAT081_C3_PARENT_LIFECYCLE_CLIENT_DRAFT1_20261119.md` and the uncommitted diff on `feature/fe-mobile-remediation` (base 82898a51) in `.worktrees/mobile/apps/ui-mobile`.
Backend truth read: `be-integration/backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py`, `parent_ai.py`, `contracts/schemas/parent_story_runs.py`, `api_conventions.py`, `infrastructure/persistence/parent_story_repository.py`, `interfaces/http/app.py` (error handler). SRS D-209 copy lines 383, 1465-1478, 1513-1522, 1673-1674.

## Verdicts

- Plan: READY WITH NOTES (0 P1, 1 P2, 3 P3 attributable to the plan).
- Implementation: ACCEPTABLE WITH NOTES (0 P1, 2 P2, 5 P3 in total, plan items included; none blocks a commit of C3 as scoped).

## Numbers (run from apps/ui-mobile, no install, no git write)

- `pnpm test`: exit 0. 11 test files, 103 tests passed (baseline 10 / 96; +1 file, +7 tests = the new file). `UI_COPY_AND_RECOVERY_VALID`.
- `pnpm typecheck`: exit 0 (tsconfig.typecheck.json extends tsconfig.json; the widened union compiles against `tests/parentApiI2Contract.test.ts:231` and `tests/parentStoryRunProjectionContract.test.ts:244-247`).
- Line endings: all 6 edited files and the 2 untracked files are pure LF (0 CRLF, 0 lone CR, no BOM, final newline present); `git ls-files --eol` shows `i/lf w/lf eol=lf` for the 6 tracked files. No mixed endings introduced.

## Check 1: paths, methods, bodies, headers, response types

Match the backend:
- Cancel: `POST /v1/story-runs/{id}/cancel`, body `{expected_revision}` only. Backend `ParentStoryRunCancelRequestV1` has `extra="forbid"`, `expected_revision: int ge=1` (schemas:32-35); client sends exactly that (ParentApi.ts:262-271). 202 with `ParentStoryRunLifecycleEnvelopeV1` (router:274-310). OK.
- Delete: `DELETE /v1/story-runs/{id}`, no body, `Idempotency-Key`, 202 with the same lifecycle envelope (router:312-336). Client sends no body and no Content-Type (request() adds Content-Type only when body !== undefined, ParentApi.ts:489-495). OK.
- GET `/v1/story-runs/{id}` returns `ParentStoryRunEnvelopeV1 | ParentStoryRunLifecycleEnvelopeV1` (router:140-143, 253-271). The client union matches. `ParentStoryRunLifecycleV1` fields equal the backend projection (run_id, run_state DELETE_PENDING|DELETED, revision, version, lifecycle_request_ref, purge_state PENDING|COMPLETED; schemas:155-169).
- 404/409: the backend flattens the HTTPException detail to a flat envelope and adds `current_version` only on the cancel path (app.py ~449-575); the client reads both flat and nested `current_version` (apiErrorFromResponse). The 409 `current_version` is the run `revision` (repository:489-494). The test fixtures for 404/409 are faithful.

Idempotency key rule (P3-1): server `parse_idempotency_key` (api_conventions.py:59-69) accepts length 1..128 and rejects any char with `ord < 33 or ord > 126`, so the accepted set is 0x21-0x7E and the space (0x20) is rejected with 400 INVALID_REQUEST. The client helper `assertIdempotencyKey(key, 128, true)` (ParentApi.ts:631-637) uses `/^[\x20-\x7E]+$/`, which also accepts the space. So the helper does NOT exactly enforce the server rule. The length bound is correct (1..128).

## Check 2: union widening and the getLatestRun change

Callers of `getStoryRunV1` / `getRunV1` in src: only `ParentLearningUseCases.getRunV1` (line 24, pass-through) and `useParentController.getLatestRun` (line 738). In tests: the two contract tests above, which only inspect calls and typecheck. No other fake of `ParentApiPort` implements `getStoryRunV1`; no polling loop reads `getRunV1`. So nothing else breaks or silently misreads the GET union.

All nine `getLatestRun` callers (controller lines 832, 865, 903, 962, 1012, 1066, 1102, 1176, 1280) sit inside try/catch. Each catch either calls `safeParentFlowErrorMessage(cause)` (code-based, so `DELETE_PENDING` gives "Yêu cầu xóa đang chờ máy chủ xác nhận." and `DELETED` gives "Buổi học đã được xóa.") or falls to a fixed Vietnamese preflight/photo message. Throwing `ParentApplicationError(receipt.lifecycle.run_state, ...)` is therefore right and strictly better than before (`receipt.story_run.run_id` on a lifecycle envelope was a TypeError and a generic message). The message string passed to the constructor (controller:742) is never shown (callers use the code), and it says "đã được yêu cầu xóa" even for DELETED; harmless but inconsistent (P3-4).

P2-1 (scope gap, pre-existing but now visible): the backend returns the lifecycle envelope from other run routes too, and the client still types them as live-run responses:
- `POST /v1/story-runs/{id}/context-confirmation` and `/script-confirmation`: `response_model=ParentStoryRunResult` (router:339-361, 397-420; `_envelope` returns the lifecycle envelope for a purged run).
- `POST /v1/story-runs/{id}/subject-confirmation`: `ParentSubjectConfirmationResponseV1 | ParentStoryRunLifecycleEnvelopeV1` (router:364-394).
- `POST /api/parent/v1/ai/story-runs/{id}/story-revisions`: returns `_lifecycle_body` (parent_ai.py:489, 493-494).
On the client these remain `ParentStoryRunEnvelopeV1` / `ParentStorySubjectConfirmationV1` / `ParentStoryScriptConfirmationV1` (ParentApi.ts:193-224, 234+). Concrete misread: `useParentController.ts:846-849` does `const confirmedRun = result.story_run;` then `setContextRun(confirmedRun); setActiveRun(confirmedRun);` and only then dereferences `confirmedRun.run_id` (TypeError). For a lifecycle answer the run state is set to undefined and the user gets the generic message instead of the lifecycle one. The plan scopes only the GET and does not list this gap under "Not in this task". Recommendation: either handle the lifecycle shape in these four methods and call sites in C3, or add one explicit line to "Not in this task" naming them as parked (the new cancel/delete cannot reach them yet, but a cancel from a second device or a delete race can produce them today).

P2-2 (test gap): the only behavior change in the controller (`getLatestRun` guard, 740-743) has no test. `tests/parentRunLifecycleV1.test.ts` test 4 exercises the type guard on API output, not `getLatestRun` and not the throw. If the `if` block were deleted or the thrown code changed, all 103 tests would still pass. Either extract the lifecycle-to-error step into a small pure function (like the other helpers in parentFlowV1.ts) and test it, or test the controller path.

## Check 3: "Not in this task" claims

True, with detail:
- `listStoryRuns` and the old `cancelStoryRun`/`deleteStoryRun` are `unavailable('run-history')` (ParentApi.ts:247-259). `useParentPlatformController.requestRunLifecycle` is a stub returning `unavailableShareOperation` (lines 47-51); `capabilities.runs` is `createUnavailableCapabilityState('run-history', ...)` (line 22); `runs` is empty.
- `StoryHistoryScreen` does contain the cancel/delete `ConfirmButton`s (lines 82-99) and `ParentExpoApp.tsx:301-302` wires them to `platform.cancelRun/deleteRun`, but the screen returns the unavailable state first when `capability.state === 'unavailable'` (line 25) and would render no run cards with an empty list. So no screen can start cancel or delete today.
- The new V1 use-case methods are not reachable from any controller: `ParentApplicationModule.platform` is a `Pick` listing `cancelRun`/`deleteRun` but not `cancelRunV1`/`deleteRunV1` (ParentApplicationModule.ts:54-65). Consistent with "parked", but C3's V1 use cases are dead code until the wiring task (P3-5).
- The `lifecycle-pending` recovery group has no UI consumer yet (only the map entry and tests reference it).
- The Bruno parking statement is plausible but was not verified (outside the requested files).

## Check 4: tests

Seven tests, all real and would fail on the regressions they target: wrong path or method (asserted as `METHOD pathname`), wrong body (`toEqual({expected_revision: 3})`), missing or renamed header (`Idempotency-Key` read from the actual Headers), body sent on DELETE (`init.body` undefined), local key refusal with fetch call count 0, 404/409 typed errors with `currentVersion: 5`, use-case pass-through and empty-run refusal, recovery group and Vietnamese message for both codes. The mock fetch replies mirror the backend envelope and flat error shapes. No vacuous assertions (the conditional `expect` in test 4 follows an unconditional `toBe(true)`).

Weak points: fixture ids are not UUIDs (`synthetic-run`, `lifecycle_request_ref: 'synthetic-lifecycle'`), harmless because the client does not validate them; no boundary case at exactly 128 chars or with a space (P3-1); the controller path is untested (P2-2); the 409 `INVALID_STATE_TRANSITION` text says "Hồ sơ" (profile) rather than the run (pre-existing wording).

## Check 5: strings, secrets, endings

- User-visible strings added: 'Buổi học đã được xóa.' (parentFlowV1.ts:462), 'Buổi học đã được yêu cầu xóa.' (controller:742, not displayed), 'Chưa chọn buổi học.' (reused). All Vietnamese; no English user-visible string. Error code literals and English JSDoc are code, not UI. `scripts/validate-ui-copy.mjs` passes.
- No secret, token or absolute local path in the diff or tests (the test token is the literal `synthetic-token`; host is `api.example.test`).
- Line endings: see Numbers; all LF.

## Findings

### P1
None.

### P2
- P2-1: The lifecycle envelope also comes back from context-confirmation, subject-confirmation, script-confirmation and story-revisions; client types and `useParentController.ts:846-849` still treat them as live runs and set run state to undefined before a TypeError. Not handled and not recorded as parked in the plan.
- P2-2: The `getLatestRun` change (`useParentController.ts:740-743`) is untested; deleting it keeps 103/103 green.

### P3
- P3-1: Key rule mismatch. Server accepts 0x21-0x7E (api_conventions.py:67); client regex is `[\x20-\x7E]` (ParentApi.ts:633), so a key containing a space passes the local check and is refused by the server with 400. Plan line 7 says "visible ASCII" and line 12 says "printable ASCII" as if they were equal; the JSDoc at ParentApi.ts:261 repeats "printable". Impact is nil with generated keys (`createIdempotencyKey`, line 644), but the test title "refuses a key that the server would refuse" overstates. Fix: `/^[\x21-\x7E]+$/` (check the other routes that share the helper have the same server rule) and add a space case and a 128-character case to test 3.
- P3-2: JSDoc on `deleteStoryRunV1` says "202, no body" (ParentApi.ts:~274) but the response has a body (the lifecycle envelope); only the request has no body. Reword.
- P3-3: The plan attributes "deletes a run in COMPLETED, FAILED or ABANDONED" to the SRS UC-07 and API table. The SRS API row (line 1674) and UC-07 (lines 1465-1470) say completed only; FAILED/ABANDONED come from BE decision D-214 and SRS line 383 (content kept until the user deletes). Cite the backend decision for the wider set. The plan also does not say that `expectedRevision` must be the run's `run_revision` (backend compares `run.revision`, repository:487-494), which the wiring task will need; `StoryHistoryScreen` currently offers delete only for COMPLETED (line ~71), to be aligned later.
- P3-4: The thrown message at controller:742 reads "đã được yêu cầu xóa" also for `DELETED`; never shown, but vary it or drop it so a future reader does not trust it.
- P3-5: V1 methods are not exposed through `ParentApplicationModule.platform`; add a line to "Not in this task" so the wiring step is not forgotten. Unmapped 400s for cancel/delete (INVALID_REQUEST for a bad key, INVALID_IDEMPOTENCY_KEY when a key is replayed for another run, repository:470) fall to the generic message; acceptable now, note for the wiring task.

## Summary (5 lines)

1. The wire contract of cancel, delete and the GET union matches the backend exactly (paths, methods, body `expected_revision`, `Idempotency-Key`, 202 envelope, flat 404/409 errors with `current_version`).
2. The key helper accepts the space (0x20) that the server rejects (server 0x21-0x7E, length 1-128 correct): P3, trivial fix, plus a missing test case.
3. The GET widening breaks no other caller or fake, and throwing a coded `ParentApplicationError` from `getLatestRun` is correct for all nine callers, but it has no test (P2); the other lifecycle-returning routes (context, subject, script confirmation, story-revisions) are still typed as live runs and not recorded as parked (P2).
4. "Not in this task" is true: no screen or controller can start cancel or delete (stubs and unavailable capability confirmed).
5. `pnpm test` 11 files / 103 tests green with UI-copy valid, `pnpm typecheck` exit 0, all files LF, no English UI string or secret. Plan READY WITH NOTES; implementation ACCEPTABLE WITH NOTES (0 P1, 2 P2, 5 P3).
