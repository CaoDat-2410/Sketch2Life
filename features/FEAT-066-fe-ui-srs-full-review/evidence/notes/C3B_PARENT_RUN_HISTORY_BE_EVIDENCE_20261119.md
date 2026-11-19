# C3b — Parent run-history list, BE evidence (goal v2)

- **Date:** 2026-11-19. **Task:** the owner's added scope "C3b" in `tmp/phase-bc/GOAL_V2_CONTINUATION_C4_C5_20261119.md`,
  under the goal v2 program approval (SHA-256 `5DFC1EDE…4795F8`). Accepted by the goal; owner final check pending.
  Nothing pushed.
- **Plan:** `plan/PLAN_C3B_PARENT_RUN_HISTORY_DRAFT3_20261119.md`. Reviews (Sonnet 5.5, effort high, fresh non-forked
  subagent; starting a session is refused on these automated turns): Draft 1 R1 NOT READY 0 / 7 / 13; Draft 2 R2
  NOT READY 0 / 1 / 6; Draft 3 R3 READY WITH NOTES 0 / 0 / 4 (`tmp/phase-bc/reviews/C3B_DRAFT*_REVIEW_R*.md`).
- **SRS:** repository copy 701,810 B (`443A3CA3…`); cited lines unchanged from the D-209 copy.

## Decisions (with SRS clauses)

| ID | Decision | Clause |
|---|---|---|
| C3B-1 | Parent screens need run history, cancel and delete; "Hoàn tất" has no Parent complete route and stays out | §21.5 line 1707; FR-C-06 line 498 |
| C3B-2 | Cursor paging, default 25, max 100 (`limit` outside → 400 in the family's validation shape, CONV-1 C-D8 rule); newest first, `run_id` desc tie-break (owner scope); a malformed cursor → 400 `INVALID_REQUEST` with `field_errors: null` | §21.1 line 1640; §9.8 |
| C3B-3 | Only the caller's runs; optional `parent_profile_id` of an own profile (any profile state); unknown or foreign → 404 | NFR-02 line 627; AC-27 line 1150; §9.8 404 |
| C3B-4 | Summary only: `run_id`, `parent_profile_id`, `run_state`, `revision`, `deleting`, `can_cancel`, `can_delete`, `created_at`, `updated_at`; models with `extra="forbid"` | owner scope; DTR §6.5 |
| C3B-5 | `DELETED` excluded; `DELETE_PENDING` shown with `deleting: true`, no profile ref, no capability; under a profile filter only live runs | FR-C-08 |
| C3B-6 | `can_cancel` / `can_delete` from `CANCEL_ELIGIBLE_STATES` / `DELETE_ELIGIBLE_STATES` | line 1518; D-214 item 1; line 383 |
| C3B-7 | The route is not in §21.2: "[PROPOSAL]" summary and catalog verification text; projected to the FE spec | §21.2 gap (recorded) |

## What changed

`routers/parent_story_runs.py` (`GET /v1/story-runs`, cursor helpers, eight declared responses incl. 422);
`application/services/parent_story_runs.py` (`list_runs`, ownership check, 503 `PARENT_STORY_RUN_STORE_UNAVAILABLE`);
`application/ports/parent_story_runs.py` (`ParentStoryRunSummary`, `list_runs`); `application/ports/parent_story_profile_lookup.py`
and `infrastructure/persistence/parent_story_profile_lookup.py` (`is_owned_profile`);
`infrastructure/persistence/parent_story_repository.py` (`list_runs`, `run_summary_capabilities`, `_run_summary`);
`contracts/schemas/parent_story_runs.py` (`ParentStoryRunSummaryV1`, `ParentStoryRunHistoryPageV1`);
`openapi_contract.py` (entry; `MOUNTED_OPERATION_COUNT` 134 → 135); `openapi_srs_v22.py` (FE projection); tests: catalog
(operations 153 → 154 at two pins, mounted 135), composition (`/v1/story-runs` GET and POST), request contract (list
cases, route test renamed, capability and cursor unit cases), new `tests/integration/test_parent_story_run_history_postgres.py`.

## Checks

- Fresh database `frc08_be1_acceptance_c3b_20261119182508` on `127.0.0.1:55458` (`alembic upgrade heads` exit 0):
  `test_parent_story_run_history_postgres.py` 2 pass (scope, order with ties, DELETED excluded, DELETE_PENDING with and
  without a profile ref, capabilities, cursor walk, limit and cursor errors, 403, profile filter for an ACTIVE and a
  DELETE_PENDING own profile, foreign and unknown profile → 404).
- Read-only check on the S1 seed database `frc08_seed_d2_20261119151757`: the seed Parent's four runs list with tied
  `created_at`, the `DELETE_PENDING` run as deleting with a null profile ref.
- `pytest tests/unit tests/contract` in a clean environment: 8,569 tests; 83 failing ids, identical to the baseline
  (0 new).
- Ruff and mypy on the touched files: 0 new against the base (mypy errors in the router's `_response` are pre-existing).
- Four validators and `git diff --check`: exit 0.
- Implementation review (Sonnet 5.5 high, subagent, BE and mobile): R1 NOT ACCEPTABLE 0 / 1 P2 (mobile reload message)
  / 8 P3; fixed; R2 ACCEPTABLE WITH NOTES 0 / 0 / 3 (`tmp/phase-bc/reviews/C3B_IMPL_REVIEW_R2.md`). Open P3 notes: the
  history list is not reset on sign-out; two state-label tables (screen and helper); a few offline cases (403 before a
  malformed cursor, over-512 cursor, `field=limit`); the home active-run card refreshes on its next resume.

## Limits

No index covers the `(created_at, run_id)` sort (per-account sets are small). A cursor reused with another filter seeks
inside that filter. The ownership check reuses the store-unavailable code for a database error.
