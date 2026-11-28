# FEAT-066 Goal v4 Phase B Android Parent T-12a/T-12c/BR-20 plan

Date: 2026-11-24 (Asia/Saigon)
Status: APPROVED_FOR_IMPLEMENTATION after the owner launched this prompt (GIVEN).
Plan revision: 1 for job `fe-v4b-android-t12ac`.

## Authority and scope

- Product baseline: FEAT-063 canonical SRS v2.7-draft; it remains unsigned. FR-C-05/06/07 and BR-20 apply.
- Contract: `tmp/phase-v4/PHASE_B_FINAL_ROUTE_LIST_20261124.md`, sections 2, 3.4 and 4; decision D-066-101.
- Implementation: `apps/ui-mobile` only, on `feature/fe-mobile-remediation` in the mobile worktree.
- Required FEAT-066 records: this plan, task approval amendment, context/decision/status and feature-local evidence.
- Excluded: backend, web, obsolete `apps/mobile`, secrets, `.env`, signing files, screenshots containing support values, logs inside the repository, staging, commits, pushes, stashes and branch changes.

## Acceptance criteria

1. Parent domain types describe context entries and support needs, and distinguish the existing immutable V1 context snapshot from the V2 snapshot with selected entries. `selected_context_entry_ids` stays omitted by default and can represent an explicit empty selection.
2. `ParentApi`, ports and use cases implement the two context-entry routes and two support-needs routes. All writes send a fresh visible-ASCII idempotency key per user action and retain that key for retry. Safe API error parsing accepts the new route and field codes without echoing values.
3. The profile UI lists context entries with kind, text, approximate date, pagination and a validated create form with a 500-character counter. Entry creation uses the fixed `PARENT_ENTERED` source code. BR-20 `DIAGNOSIS_LIKE` errors map to a Vietnamese field message without echoing text.
4. Context confirmation offers an entry picker capped at ten, preserves the old path when the picker is untouched, sends `[]` only for an explicit no-entry choice, and re-reads the run after confirmation before showing V2 selected entries in the review card. Entry-not-found reloads the list; already-confirmed reloads the run without retry; oversized snapshots ask for fewer entries; 503 remains safe.
5. The Parent support-needs screen loads on open and represents value, revision-zero empty, unavailable, and profile-gone states. It edits with the loaded `expected_revision`, handles stale revision/deletion/BR-20 errors safely, and displays the calm unavailable copy for `SUPPORT_NEEDS_UNAVAILABLE`. Decrypted values and drafts remain screen-local, are cleared when leaving, and never enter logs, navigation, analytics, screenshots, or test names.
6. Vitest mocks cover the four routes and their paths, methods, headers and bodies; snapshot union and omitted-versus-empty selection; safe error mapping; unavailable UI; state clearing; and no-echo BR-20 handling. Extend the requested Parent contract/wiring tests and add a focused route pin test. Do not edit the frozen projection JSON.
7. All requested gates are run from the mobile worktree and their actual outputs are recorded in the feature evidence note and the external append-only run log. The test command prints `UI_COPY_AND_RECOVERY_VALID`. Report that no Android lint script or native test suite exists; Gradle assembly is optional.

## Implementation sequence

1. Add types, HTTP methods, ports and use cases.
2. Add context-entry list/create and support-needs screens/actions, wire them through the Parent controller and Expo step switch, and update the preview harness with non-sensitive fixtures.
3. Add BR-20 safe field mapping and V2 snapshot confirmation/re-read behavior.
4. Extend/add mock-only Vitest coverage.
5. Run the requested gates, inspect the final diff for scope/privacy, record evidence and update FEAT-066 context/decision/status.

## Verification commands

- `npm --prefix apps/ui-mobile test`
- `npm --prefix apps/ui-mobile run typecheck`
- `python tools/validate_harness.py`
- `python tools/validate_repository_security.py`
- `python tools/validate_architecture.py`
- `git diff --check`

No backend/API runtime, real credentials/data, Firebase, Android lint, native tests, Gradle assembly, commit, or push is part of this task.
