# FEAT-066 Goal v4 Phase A web wiring — Teacher

- Plan revision: 52
- Date: 2026-11-23
- Status: APPROVED_FOR_IMPLEMENTATION by the owner's direct launch prompt; exact approval is recorded in `approvals/TASK_APPROVAL.md`.
- Worktree: `D:\GitHub\Sketch2Life\.worktrees\ui`
- Branch: `codex/fe-ui-web-remediation`

## Goal

Wire `apps/web` Teacher flows to the final Goal v4 Phase A contracts. Use the owner-supplied final route list at `tmp/phase-v4/PHASE_A_FINAL_ROUTE_LIST_20261123.md`, its Web Teacher section, the final contract supplied in the launch prompt, and the higher-priority corrections in section 8 of `tmp/phase-v4/fe-wiring/V4A_FE_WIRING_PLAN_DRAFT1.md`. The canonical product baseline remains the unsigned FEAT-063 SRS v2.7-draft identified by `docs/context/SRS_AUTHORITY.md`.

## Scope and boundaries

- Change Teacher web API, service, component, page, copy, and listed Vitest files under `apps/web/src` as needed to meet the criteria below.
- Update only this feature's plan, approval, context, decision, status, evidence index, and evidence note.
- No Parent story screens, mobile work, backend work, contract changes, visual asset generation, credentials, `.env` files, `debug.keystore`, model weights, stage/stash/branch switch, commit, or push.
- Run logs stay in `E:\AI_LOG\CODEX\fe-v4a-web\RUN_LOG.md`; feature evidence is a concise reproducible summary, not a run log.

## Acceptance criteria

1. `TeacherRun` carries optional `story_confirmation_required`; run API errors and parsed envelopes preserve numeric `current_version` when present.
2. Teacher occurrence pages can load a completed run by `sample_video.run_ref` after `active()` returns no run. Existing active-run behavior remains available.
3. The last Teacher gate starts the first story implicitly. The UI polls `SCRIPT_GENERATING` to `SCRIPT_REVIEW`, rereads after subject confirmation, and shows a waiting hint when gates appear complete but the run stays in `PREPARATION_REVIEW`. It does not resend context confirmation.
4. When `story_confirmation_required` is true, the Teacher can confirm the same story again with a fresh idempotency key and the same story revision/hash, then reload the run; rewrite remains an alternative. At the three-request cap, only cancel is offered.
5. Video generation is hidden while confirmation is required. `STALE_REVISION` reloads the run and distinguishes ordinary run staleness from the terminal plan fence; the plan fence tells the Teacher to cancel before creating a new run. A failed queued generation after a plan change tells the Teacher to create a new run.
6. A completed run offers playback only when `video.playback.state` is `AVAILABLE`, with no generate, unsuitable, or complete action.
7. Projection accepts an available sample for a completed run. A projection confirmed before Complete remains a dead end; a post-Complete claim remains playable and supports the allowed repeat/takeover behavior. Complete does not require a prior projection claim.
8. The Teacher plan activity option reads `plan_activity_id` from the confirmed plan; null IDs cannot be selected. The unchanged plan-revision list is not treated as carrying activities.
9. Error copy is Vietnamese and keyed by safe error code, including stale revision, regeneration limit, invalid re-confirmation, store/dependency 503, and plan fence. Server bodies, raw codes, and tokens are never rendered.
10. Safety-blocked presentation follows video state/job code. New blocked rows at `SCRIPT_REVIEW` offer confirm-again and rewrite when allowed; at the cap only cancel. Legacy `SAFETY_BLOCKED` rows can confirm/rewrite first and cannot generate before confirmation. `shouldPoll` is false for script review with failed job, completed, legacy safety-blocked, and other terminal states.
11. Extend the named API contract/response-shape and focused component/service tests to cover both stale-revision causes, same-story re-confirmation with a fresh key, completed-run loading/playback, projection before versus after Complete, confirmation hiding generation, safe error copy, first-story wait behavior, plan activity IDs, and safety-blocked handling.
12. Run and record actual output for all gates from the worktree root: `npm --prefix apps/web run check`, `python tools/validate_harness.py`, `python tools/validate_repository_security.py`, `python tools/validate_architecture.py`, and `git diff --check`.

## Implementation choice

For a `PREPARATION_REVIEW` run whose visible gates appear met but has no start signal, show a waiting hint and do not resend `context-confirmation`. This avoids another state-changing request when the BE contract says an unmet hidden gate leaves the run unchanged.

## Verification and evidence

Use only mocked Vitest API spies/fetch stubs. Store the command, output summary, baseline, and limitations in `evidence/notes/EV-066-059_V4A_WEB_WIRING_20261123.md`, then index it in `evidence/README.md`. Do not store raw run logs in the repository.

## Known source discrepancy

At preflight, `.worktrees/v4` was on `db7e3920`, a descendant of supplied final Phase A commit `930da61e`, and had additional dirty BE files. This work reads the user-provided final contract and route list and does not modify the BE worktree. Report the differing branch tip and any source-level contradiction found during review.
