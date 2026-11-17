# Plan Rev42 — review and commit the Swagger update

- Feature: FEAT-063 — whole-repository architecture redesign.
- Status: APPROVED under the project owner's direct `coi và commit cho tui` request in the current chat on 2026-10-30.
- Approval record: `approvals/TASK_APPROVAL.md` (this plan's SHA-256 is recorded there).

## Goal

Review the current Swagger/OpenAPI contract, navigation, local QA and overview changes; run their focused verification and repository security check; then create one local commit on `dev`.

## Scope

1. Review all pending changes limited to the FEAT-063 Swagger/OpenAPI work and its evidence, examples, tests and generator/exporter files.
2. Check the contract snapshot and approved plan hashes, focused tests, Ruff, Python compilation, OpenAPI export/live snapshot parity, whitespace and repository security.
3. Stage only the reviewed Swagger/OpenAPI implementation and its FEAT-063 records/artifacts.
4. Create one commit on the current `dev` branch only after all required checks pass, then verify the resulting commit and worktree.

## Acceptance criteria

- AC1: The staged diff contains only the reviewed Swagger/OpenAPI changes and related FEAT-063 records/artifacts; no credentials, real-child data, external source document, machine-local path, or unrelated file is included.
- AC2: The focused checks, exporter/live snapshot comparison, hash checks, `git diff --check`, and mandatory repository security validator pass.
- AC3: Exactly one local commit is created on `dev`, and the final worktree is clean.
- AC4: No push or deployment is performed.

## Verification

- Run the focused Swagger/OpenAPI and upload-size contract tests.
- Run targeted Ruff and Python compilation for changed Python files.
- Regenerate the local-profile OpenAPI artifact and compare it with the served OpenAPI snapshot when the local API is available.
- Verify the approval plan hashes and run `python tools/validate_repository_security.py` immediately before committing.
- Inspect the staged diff and confirm the final branch, commit and worktree state.

## Explicitly excluded

New API routes or behavior outside the previously approved Swagger scope, credentials or real data, database/provider/deployment operations, force/reset operations, and push.
