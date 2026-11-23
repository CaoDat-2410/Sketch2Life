# FEAT-066 Plan Rev51 — consolidate pending web worktree changes

- Date: 2026-11-17 (Asia/Bangkok).
- Status: APPROVED_FOR_EXECUTION from the owner's direct request to record all pending work in one commit and push it for use on another machine.
- Worktree/branch: codex/fe-ui-web-remediation, upstream origin/codex/fe-ui-web-remediation.
- Goal: commit all current non-ignored changes in this worktree as one new fast-forward commit, then push the branch.

## Included scope

- Web login/portal routing and shared UI organization.
- Platform Admin, School Manager and Teacher web UI changes and related FE/API adapters.
- Manager QA bootstrap ordering fix and its focused backend test.
- FE tests, FEAT-066 plans, approvals, evidence notes and reviewed screenshots currently pending in this worktree.
- Rev48 API inventory/test record already exists in the preceding pushed commit; preserve it and include all newer local records.

## Exclusions and safety

- Never stage or push .env, tmp/qa-test-accounts.local.md, passwords, Firebase/API tokens, service-account material, or other ignored files. Credentials remain available only in the owner's local ignored tmp file.
- Do not modify or reseed Firebase accounts, DB data, SRS, or application code as part of this commit task.
- Preserve the already-pushed Rev48 commit; use a new fast-forward commit, no amend/rebase/force push.
- Run the focused FE tests, production build, lint, repository security, harness, architecture and diff checks before commit/push.
- Review the final staged paths/diff for secrets, unintended files, and cohesion. Stage the complete non-ignored working diff only after inspection.
- Do not include external local reference documents.

## Acceptance

1. One new commit contains every current intended non-ignored worktree change and its records.
2. .env and the QA credential file are absent from the staged diff and remain Git-ignored.
3. All required checks pass; test/build/lint results are recorded in EV-057.
4. Push succeeds to origin/codex/fe-ui-web-remediation and local HEAD matches its upstream.
