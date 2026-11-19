# C2 (C-W2 web error envelope) implementation evidence, 2026-11-19

Accepted by the goal under the program approval; the final check by the owner is pending.

Plan: `plan/PLAN_FEAT066_C2_WEB_ERROR_ENVELOPE_DRAFT1_20261119.md`. Review: one independent review of plan and implementation by a fresh non-forked subagent (Sonnet 5.5 high; a session could not be started on that turn). Plan READY WITH NOTES (0 P1, 1 P2, 2 P3); implementation ACCEPTABLE WITH NOTES (0 P1, 1 P2, 5 P3). The P2 (the Teacher AI reader `aiWorkflowService.ts` still read `detail.code` only) was fixed with a test; the trust gate was hardened (blank or oversized message, non-finite retry-after) with tests. Left as notes: the two positional arguments added to `AdminBe1Error` (an options object would be safer), the 401 and 403 fallback texts that keep the legacy wording, the missing 405 entry, and the fact that trust is by body shape (the Parent-profile envelope has the same fields; the web does not call it).

SRS basis: section 9.8 (line 847; `message` row line 854: safe and localized). Decision by the goal: the server message is shown only for the CONV-1 envelope; every other body gets a Vietnamese message by code, then by status. This closes the C2 brief item recorded in the C1 evidence note.

Checks (from `apps/web`, npm), against the C1 state of 5 files and 25 tests: `npm run test` 9 files, 43 tests, pass; `npm run lint` exit 0 with 28 warnings (= baseline); `npm run build` exit 0. Repository security and architecture validators valid, `git diff --check` clean; the harness validator reports the owner's untracked `features/FEAT-066-brand-logo/` (unchanged by this task). No CR bytes, BOM, absolute path or secret in the changed files (reviewer check). UI-copy: the only new strings are the Vietnamese fallback table, copied from the backend table.

The teammate branch `origin/codex/fe-ui-web-remediation` equals `c42d913a` at the time of the work (no new commits).
