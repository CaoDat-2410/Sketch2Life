# FEAT-066 Goal v4 Phase B T-7e web wiring — Teacher roster paging

- Plan revision: 53
- Date: 2026-11-24
- Status: APPROVED_FOR_IMPLEMENTATION by the owner's direct launch in the task prompt; the matching approval amendment is recorded in `approvals/TASK_APPROVAL.md`.
- Worktree: `D:\GitHub\Sketch2Life\.worktrees\ui`
- Branch: `codex/fe-ui-web-remediation`
- Job: `fe-v4b-web-t7e`

## Goal and contract sources

Implement the T-7e Teacher roster client and empty-state behavior before the Phase B backend is deployed to a shared environment. The contract is `tmp/phase-v4/PHASE_B_FINAL_ROUTE_LIST_20261124.md` §1 and decision D-066-100. The route list is final and follows the backend code. The canonical product baseline remains the unsigned FEAT-063 SRS v2.7-draft identified by `docs/context/SRS_AUTHORITY.md`; this plan does not approve or sign off that SRS.

At the time of planning, D-066-100 exists in the repository-root FEAT-066 decision file and route list, but is absent from this worktree's copy. The worktree decision file will be reconciled with the same D-066-100 record before app implementation.

## Scope and boundaries

- Change only the T-7e web client in `apps/web/src/shared/api/teacherRosterApi.ts`, `apps/web/src/shared/api/cursorPages.ts`, `apps/web/src/modules/teacher/pages/T05ClassesScreen.tsx`, and their named tests `apps/web/src/shared/api/__tests__/teacherRosterApi.test.ts` and `apps/web/src/modules/teacher/pages/__tests__/T05ClassesScreen.test.tsx`.
- Update only this feature's task plan, approval, context, decision, status, evidence index, and evidence note.
- `teacherRosterApi.profiles` follows all cursor pages with `limit=100`, preserves cursor values, de-duplicates `child_id`, and returns `{ items, activeProfileCount }` using the first page's count. A later-page error preserves loaded items and count alongside the safe mapped error.
- The Teacher class screen renders the roster API's filtered items directly. The separate consents read remains for visible consent details; its failure message appears only when that read fails and does not suppress the server-filtered roster. Empty states distinguish zero eligible rows with a positive active count from a class with zero active profiles.
- Remove the roster-specific `CONSENT_NOT_EFFECTIVE` presentation and error carve-out. Update the create success note because synthetic profiles are listed.
- Do not change backend, mobile, School Manager, `modules/school-manager/**`, contracts, credentials, `.env`, `debug.keystore`, model weights, or generated assets. Do not stage, stash, switch branches, commit, or push. Keep run logs in `E:\AI_LOG\CODEX\fe-v4b-web-t7e\` only.

## Acceptance criteria

1. The roster client calls the existing encoded path with `limit=100`, follows `next_cursor` unchanged until completion, takes `active_profile_count` from page one, and de-duplicates by `child_id`.
2. A later page failure stops the walk, keeps the rows already loaded, and surfaces the existing safe API error mapping. Repeated cursors and the page cap stop as `collectCursorPages` already specifies.
3. Empty roster plus a positive active count shows a safe Vietnamese count hint; empty roster plus count zero shows the existing empty text. No per-child exclusion reason is exposed.
4. The roster UI no longer treats `CONSENT_NOT_EFFECTIVE` as a special response. The independent consents read remains and only displays its unavailable message after that call fails.
5. Synthetic create success copy states that the new profile can appear in the roster.
6. Focused API and screen tests pin path/query, cursor passthrough, two-page merge/deduplication, active count on empty results, error mapping for 400/404/403, no special 409 handling, partial-page failure, consent-call failure, empty states, and create success copy.
7. No School Manager screen or module changes.
8. Run and record the actual output of `npm --prefix apps/web run check`, `python tools/validate_harness.py`, `python tools/validate_repository_security.py`, `python tools/validate_architecture.py`, and `git diff --check` from the worktree root. Preserve pre-existing validator gaps without fixing unrelated files.

## Verification and evidence

Use the repository's existing mocked Vitest setup and the requested gates only. Record exact commands, exit codes, concise outputs, baseline discrepancies, and limitations in `evidence/notes/EV-066-060_V4B_WEB_T7E_20261124.md`, then add the note to `evidence/README.md`. Update FEAT-066 context and status after implementation and review. Do not put raw logs in the repository.

## Known contract behavior

Pages are independent statements, not a snapshot; profile rows can change between pages when consent changes. De-duplication is therefore required. The count describes all active class profiles, while `items` contains only synthetic or effectively consented real profiles. School Manager paging parameters remain accepted and ignored.
