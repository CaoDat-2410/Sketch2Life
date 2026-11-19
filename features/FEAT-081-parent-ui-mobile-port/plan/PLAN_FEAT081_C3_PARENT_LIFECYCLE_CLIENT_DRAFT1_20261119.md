# FEAT-081 C3 (C-P2) Parent run lifecycle client: plan, Draft 1

Status: DRAFT written by the goal under the FEAT-066 goal v2 program approval; reviewed together with its implementation (one independent review of plan and diff). Branch `feature/fe-mobile-remediation`, app `apps/ui-mobile`.

## Basis

SRS (D-209 copy) FR-C-08, UC-07, UC-11 and the API table: a Parent cancels a run that is not finished and deletes a finished run; both are idempotent lifecycle commands. The SRS lines 1465-1470 and 1674 still say "completed" only; the wider delete set (COMPLETED, FAILED, ABANDONED) is backend decision D-214 item 1 and SRS line 383 (the SRS wording edit of task B4 is parked). `expectedRevision` of a cancel is the run's `run_revision`; from DELETE_PENDING on the server reports no run content. Backend (integration branch `feature/feat066-be-integration`, FR-C-08, `parent_story_runs.py`): `POST /v1/story-runs/{id}/cancel` (body `expected_revision`, `Idempotency-Key`, 202), `DELETE /v1/story-runs/{id}` (no body, `Idempotency-Key`, 202), both answer `{request_id, lifecycle}` with `run_state` DELETE_PENDING or DELETED and `purge_state` PENDING or COMPLETED; `GET /v1/story-runs/{id}` answers the same lifecycle envelope instead of the run from DELETE_PENDING on; 404 `RESOURCE_NOT_FOUND`, 409 `STALE_REVISION` (with `current_version`) and `INVALID_STATE_TRANSITION`; the key is 1 to 128 visible ASCII characters, 0x21 to 0x7E, so a space is refused (`parse_idempotency_key`).

## Change (client and application layer)

- `domain/types.ts`: `ParentStoryRunLifecycleV1`, `ParentStoryRunLifecycleEnvelopeV1`, `ParentStoryRunResultV1` (full run or lifecycle) and the guard `isParentStoryRunLifecycleEnvelope`.
- `ParentApi.ts`: `cancelStoryRunV1(runId, expectedRevision, actionIdentity)` and `deleteStoryRunV1(runId, actionIdentity)` with the key checked locally against the server rule (`assertVisibleAsciiKey`); the context, subject, script and story-revision calls turn a lifecycle answer (a run cancelled or deleted meanwhile) into a typed error `DELETE_PENDING` or `DELETED` (`liveRunOrLifecycleError`), because the server answers those routes with the lifecycle envelope too; `getStoryRunV1` returns the union. The old `cancelStoryRun` and `deleteStoryRun` stubs (capability `run-history`, always unavailable) stay.
- `ParentPorts.ts` and `ParentPlatformUseCases.ts`: the two V1 methods (`cancelRunV1`, `deleteRunV1`) with the empty-run check.
- `application/storyRunResult.ts` (new) `requireLiveStoryRun`, used by `useParentController.ts` `getLatestRun`: a lifecycle answer stops the flow with the code `DELETE_PENDING` or `DELETED` instead of reading `story_run` from it; it is a pure function with its own test.
- `parentFlowV1.ts`: recovery group `lifecycle-pending` and a Vietnamese message for `DELETED` (`DELETE_PENDING` already existed). The 404 and 409 states already map to `resource-refresh`, `review-current-state` and the `INVALID_STATE_TRANSITION` message.

## Not in this task (parked, recorded)

- Screens that start a cancel or a delete: the history list (`listStoryRuns`) and the platform capabilities are `unavailable` (no list route exists in the backend), so no screen can offer the buttons yet. `useParentPlatformController.requestRunLifecycle` stays a stub until a list route exists.
- Bruno requests for cancel and delete: the L5 Bruno collection guard (task B2) is deferred by the owner; adding requests to the collection without its guard is not done.

## Tests and checks

New `tests/parentRunLifecycleV1.test.ts` (9 tests, including a space and a 128-character key, `requireLiveStoryRun`, and the lifecycle answers of the four other routes): paths, methods, body and key headers; local key refusal before any request; union narrowing; 404 and 409 typed errors with `current_version`; use cases; recovery group and message. Checks from `apps/ui-mobile`: `pnpm test` (vitest plus the UI-copy and recovery validator), `pnpm typecheck`. Baseline: 10 files, 96 tests, UI-copy valid, typecheck exit 0.
