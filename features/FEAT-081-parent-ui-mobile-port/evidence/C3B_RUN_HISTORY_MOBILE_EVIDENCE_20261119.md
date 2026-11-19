# C3b — Parent run history, cancel and delete screens, mobile evidence (goal v2)

- **Date:** 2026-11-19. **Task:** the owner's added scope "C3b", mobile part, under the goal v2 program approval
  (SHA-256 `5DFC1EDE…4795F8`). Accepted by the goal; owner final check pending. Nothing pushed.
- **Plan:** `PLAN_C3B_PARENT_RUN_HISTORY_DRAFT3_20261119.md` on `feature/feat066-be-integration` (R3 READY WITH NOTES).
  BE half: commit `54558bcc` on `feature/feat066-be-integration` (`GET /v1/story-runs`).

## Decisions (SRS)

- History list on the live route, 25 per page with the server cursor (SRS §21.5 line 1707, §21.1 line 1640); a new
  profile starts a new list; a cursor that does not advance stops paging.
- Cancel and delete follow the server flags (`can_cancel`, `can_delete`; SRS line 1518, D-214 item 1) and the C3
  client (`cancelRunV1` with the run revision, `deleteRunV1`); one key per (action, run, revision), reused for a retry;
  202 patches the item to "Đang xóa"; 409 reloads the list; 404 removes the item.
- Confirmation dialogs say the session content is deleted and cannot be restored (SRS lines 500, 1518–1520).
- The `run-history` capability is available when the API URL is configured; "Hoàn tất" stays unavailable (no route).

## What changed (`apps/ui-mobile`)

`src/parent/domain/types.ts` (`ParentStoryRunSummary`, page without `contract`); `src/parent/infrastructure/http/ParentApi.ts`
(`listStoryRuns` live); `src/parent/application/ports/ParentApplicationModule.ts` (`cancelRunV1`, `deleteRunV1`); new
`src/parent/application/parentRunHistory.ts` (pure helpers); `src/parent/presentation/navigation/useParentPlatformController.ts`
(real run-history state); `src/parent/presentation/screens/StoryHistoryScreen.tsx` (summary rendering, flags, copy);
`tests/parentSrsBehavior.test.ts` (amended on purpose: `listStoryRuns` left the absent-route table; the controller may
call exactly `listRuns`, `cancelRunV1`, `deleteRunV1` under `application.platform.`); new `tests/parentRunHistory.test.ts`.
`ParentExpoApp.tsx` and `ParentVisualPreviewHarness.tsx` are untouched.

## Checks

- `npm test`: 12 files / 112 tests pass; `scripts/validate-ui-copy.mjs`: `UI_COPY_AND_RECOVERY_VALID` (it does not
  scan `src/parent`, so the new strings are checked by source-text tests).
- `npm run typecheck`: exit 0.
- Implementation review (Sonnet 5.5 high, subagent): R1 NOT ACCEPTABLE 0 / 1 P2 (reload message cleared by the reload)
  / 8 P3 → fixed with load sequencing and a source-text guard; R2 ACCEPTABLE WITH NOTES 0 / 0 / 3.
