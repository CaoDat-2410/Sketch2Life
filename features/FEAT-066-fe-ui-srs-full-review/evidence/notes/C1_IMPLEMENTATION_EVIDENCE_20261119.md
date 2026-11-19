# C1 (C-W1 Manager alignment) implementation evidence, 2026-11-19

Accepted by the goal under the program approval; the final check by the owner is pending.

## Scope and decision

Plan: `plan/PLAN_FEAT066_MGR9_MANAGER_API_INTEGRATION_DRAFT4_20261119.md`. Plan reviews: Draft 2 round 1 NOT READY (2 P1, 5 P2, 6 P3); Draft 3 round 2 NOT READY (1 P1, 2 P2, 7 P3); Draft 4 round 3 READY WITH NOTES (0 P1, 0 P2, 6 P3). All on Sonnet 5.5 high, in a separate session. Implementation review R1: a fresh non-forked subagent (Sonnet 5.5 high; a session could not be started on that turn), ACCEPTABLE WITH NOTES (0 P1, 1 P2, 5 P3). The P2 (the "success clears the key" check could not fail) and P3-1, P3-2, P3-3 were fixed in the tests before the commit; P3-4 and P3-5 need no action.

Decision taken by the goal under the program approval (SRS basis: section 21.1 line 1642 default page size 25, line 1639 one key per logical command, section 9.8 localized messages): C1 is reduced to slice S1 (the parent-group list sends no `limit`, so the server default of 25 applies) and the regression tests of slice S2. The retry-key rule is pinned by tests and not changed. The `INVALID_IDEMPOTENCY_KEY` message and the `be1Client` error-body parsing move to C2. C2 brief: `be1Client.ts` `adminApiRequest` and `adminBe1Request` read `code` and `message` from the top level only; C2 makes both accept the `detail`-wrapped body of `origin/dev` and the CONV-1 top-level body and always shows a Vietnamese message.

## Changes

- `apps/web/src/modules/school-manager/be1/services/managerBusinessService.ts`: no `limit`; `?` appended only for a non-empty query.
- `apps/web/src/modules/school-manager/be1/__tests__/managerBusinessService.test.ts`: one test updated, two added.
- `apps/web/src/modules/school-manager/be1/__tests__/managerBusinessPages.test.tsx`: paging test with a per-cursor mock; key retry test (unknown outcome keeps the key, 4xx clears it, success clears it).
- `apps/web/src/modules/school-manager/pages/__tests__/ManagerScreens.test.tsx` (new): cursor page merge; decision key stable for the same reason and for the same approval, new for a changed reason.

## Checks (from `apps/web`, npm)

| Check | Baseline at `c42d913a` | After |
|---|---|---|
| `npm run test` | 4 files, 18 tests, pass | 5 files, 25 tests, pass (3 runs) |
| `npm run lint` | exit 0, 28 warnings | exit 0, 28 warnings, none new |
| `npm run build` | exit 0 | exit 0 |
| Mutation checks | n/a | restoring `limit=50` fails 3 service tests; removing the success reset of the key fails the key test |

Repository validators on this worktree: security and architecture valid, `git diff --check` clean. The harness validator reports `HARNESS_INVALID` for the owner's untracked folder `features/FEAT-066-brand-logo/` (missing harness paths); this is not part of this task and was left untouched. The UI-copy check (manual): no user-visible string was added or changed; the new strings are in test files only.

The teammate branch `origin/codex/fe-ui-web-remediation` was fetched before the work and equals `c42d913a`; there were no new teammate commits.
