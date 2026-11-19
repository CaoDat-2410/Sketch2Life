# C5 C-A — Platform Admin accounts web slice, implementation evidence (goal v2)

- **Date:** 2026-11-19. **Task:** goal v2 row C5, web part. Accepted by the goal under program approval
  (`GOAL_V2_PHASE_BC_PROGRAM_20261119.md`, SHA-256 `5DFC1EDE…4795F8`); owner final check pending. Nothing pushed.
- **Plan:** `PLAN_CA_ADMIN_ACCOUNTS_SLICE_DRAFT2_20261119.md` on `feature/feat066-be-integration` (review R2 READY WITH
  NOTES). BE half: commit `e9c9a815` on `feature/feat066-be-integration`.
- **Teammate branch:** `origin/codex/fe-ui-web-remediation` fetched before the commit; no new commits.

## Decisions (SRS D-209 copy)

- The account list pages with the server cursor (`next_cursor`), 25 per page; the page keeps a stack of page-start
  cursors for "Trước"/"Tiếp"; a filter change starts again from the first page; after a change the current page
  reloads from its own start cursor (SRS §21.1 line 1640).
- Account create and role/state changes send an `Idempotency-Key`; one key per exact command (create: form content;
  row: account, revision and change), reused only for a retry, dropped after success (§21.4 line 1697).
- No `If-Match` on account changes (O-ACCREV `BLOCKED_OPEN`). Moderation screens unchanged (O-CONTENTADMIN
  `BLOCKED_OPEN`).

## What changed

`shared/api/backendApi.tsx` (`next_cursor`, `cursor`, keys); `modules/platform-admin/services/userService.ts`
(`cursor`, keys, `keyForSignature`); `modules/platform-admin/pages/UsersPage.tsx`; new
`modules/platform-admin/pages/__tests__/UsersPage.cursor.test.tsx`.

## Checks (`apps/web`)

- `npm run test`: 13 files / 61 tests pass.
- `npm run lint`: exit 0, 28 warnings (= baseline).
- `npm run build`: exit 0.
- Implementation review (Sonnet 5.5 high, subagent, BE and web together): R1 NOT ACCEPTABLE 0 / 2 P2 (test gaps) /
  9 P3; fixed; R2 ACCEPTABLE WITH NOTES 0 / 0 / 3.

## Notes

- The "new key for the next change" test also passes without the delete-after-success step, because the two changes
  differ in payload (R2-03); the delete is still in place.
- `keyForSignature` duplicates the C4 Teacher helper; a shared helper is a later clean-up.
