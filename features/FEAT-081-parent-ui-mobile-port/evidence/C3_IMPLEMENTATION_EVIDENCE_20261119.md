# C3 (C-P2 Parent run lifecycle client) implementation evidence, 2026-11-19

Accepted by the goal under the FEAT-066 goal v2 program approval; the final check by the owner is pending.

Plan: `plan/PLAN_FEAT081_C3_PARENT_LIFECYCLE_CLIENT_DRAFT1_20261119.md`. Review: one independent review of plan and implementation by a fresh non-forked subagent (Sonnet 5.5 high; a session could not be started on that turn). Plan READY WITH NOTES; implementation ACCEPTABLE WITH NOTES (0 P1, 2 P2, 5 P3 counted with the plan notes). Fixed after the review: P2-1 (the server also answers the context, subject, script and story-revision routes with the lifecycle envelope; the client now turns that into a typed `DELETE_PENDING` or `DELETED` error), P2-2 (the live-run guard became the pure function `requireLiveStoryRun` with tests), P3-1 (the key helper now follows the server rule, 0x21 to 0x7E, 1 to 128), P3-2, P3-3 (plan wording), P3-4 (the message of the guard). Left as notes: P3-5 (`cancelRunV1` and `deleteRunV1` are not yet in the `ParentApplicationModule.platform` Pick and have no screen: the history list is `unavailable`; some 400 codes of cancel and delete fall to the generic message).

Parked and recorded: screens that start a cancel or a delete (no list route in the backend; the platform capabilities stay `unavailable`); Bruno requests (the L5 collection guard of task B2 is deferred by the owner).

Checks from `apps/ui-mobile`: `pnpm test` 11 files, 105 tests, pass, UI-copy and recovery validator `UI_COPY_AND_RECOVERY_VALID` (baseline 10 files, 96 tests); `pnpm typecheck` exit 0. Repository validators on this worktree are run before the commit. No new user-visible English string; the new Vietnamese strings are the `DELETED` message and the controller guard message.
