# BE2-01–14 offline integration plan

- Status: APPROVED
- Plan revision: 1
- Implementation status: IN_PROGRESS
- Updated: 2026-10-20 (Asia/Saigon)

## Goal

Create a reviewable branch that combines the published BE2-01–07 snapshot with
the existing BE2-08–14 receiver branch, then establish what passes across the
combined source using offline checks.

## Scope

- Base: `feature/be2-01-07` at `9d1ed184f31ab6b1f18337a1e29bb04fd59aa1b5`.
- Source: `origin/feature/be2-08-14` at `42a6d3122259e6b33133673a2e444deefa45d387`.
- Candidate: `feature/be2-backend-ai-integration` (renamed from the original
  task-range label on 2026-10-20; the commit and integration scope are unchanged).
- Preserve both histories and all per-card approvals, evidence, statuses, and explicit deferrals.
- Resolve only conflicts required to obtain a coherent combined checkout; validate shared contracts, dependency/migration composition, architecture, repository security, and offline tests.
- Save the merge receipt, conflict dispositions, commands, outputs, and test results under this feature's `evidence/` directory.

## Out of scope

- Changing feature behavior or broad refactoring unrelated to an integration failure.
- Treating isolated component evidence as cross-owner acceptance.
- Lightning/provider calls, live service startup, deployment, or production adoption.
- Updating per-card statuses to DONE, merging into `dev`/`main`, or publishing an unrelated PR.

## Steps

1. Preserve the current task-7 and receiver tips and create this candidate from the task-7 branch.
2. Review current per-card plans, approvals, status, handoffs, and source-register authority for BE2-08–14.
3. Merge the receiver branch with a merge commit; resolve conflicts from authoritative current records and document them.
4. Run repository validators, migration/contract composition checks, relevant BE2-01–14 offline test packs, and the combined backend regression suite where the environment permits.
5. Fix only integration defects within approved offline scope; rerun affected checks and then the complete required offline validation set.
6. Record the final branch, exact parents, test results, skips, limitations, and remaining live/owner gates. Leave the candidate ready for review.

## Acceptance criteria

- The candidate contains both exact source tips as ancestors and retains their commit histories.
- The checkout is coherent and has no unresolved conflicts; material resolution choices are documented.
- Existing card approvals, evidence, status labels, and runtime/adoption deferrals are preserved.
- Required offline harness, architecture, repository-security, whitespace, migration/contract, and relevant regression checks have results recorded; failures and skips are explicit.
- No Lightning/live/provider/deployment action is performed or represented as passed.
- FEAT-057 remains an integration candidate; individual cards remain governed by their own acceptance records.

## Risks and mitigations

- Shared source and documentation changed on both branches: inspect conflict hunks against the newer card records and preserve the intent/evidence from both sides.
- Multiple Alembic heads or incompatible dependency pins: identify the owning migrations and plan constraints before any structural change; do not silently rewrite migrations.
- Unit suites pass independently but fail together: run focused combined suites and capture the exact first failure before making a bounded fix.
- Some tests require unavailable services or optional packages: report them as NOT_RUN/skipped; do not substitute live calls or inflate pass counts.

## Verification plan

- `python tools/validate_harness.py`
- `python tools/validate_repository_security.py`
- `python tools/validate_architecture.py`
- `python tools/validate_skeleton.py`
- `git diff --check`
- Run the BE2-08–14 component runners/test inventories and the combined backend suite selected from the merged branch's own handoffs; inspect Alembic heads and validate contract imports.
- Do not invoke Lightning or real provider endpoints.

## Evidence plan

Store an integration report and machine-readable command/result summary under
`evidence/notes/` and `evidence/metrics/`. Preserve raw test output under
`evidence/raw/` when generated; do not include secrets, local absolute paths,
real child data, or temporary database credentials.
