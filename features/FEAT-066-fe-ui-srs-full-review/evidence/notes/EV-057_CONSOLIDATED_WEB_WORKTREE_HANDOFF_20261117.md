# FEAT-066 EV-057 — consolidated web remediation worktree

- Date: 2026-11-17 (Asia/Bangkok).
- Plan: plan/PLAN_REV51_WORKTREE_CONSOLIDATION_AND_PUSH_20261117.md.
- Approval: FEAT-066 Revision 51 in approvals/TASK_APPROVAL.md.
- Branch: codex/fe-ui-web-remediation; preserve the already-pushed Rev48 commit.
- Scope: consolidate every current non-ignored worktree change for handoff to another machine.

## Included change groups

- Shared role login and portal routing; removal of the old preview entry.
- Platform Admin account screen, role/status flows, sidebar and responsive layout.
- School Manager navigation, organization/classes/roster/consent/parent-group FE adapters and pages; unsupported actions stay guarded.
- Teacher web route and workflow refinements.
- Shared web files organized under api/auth/components/navigation/styles; the assets folder remains.
- Manager bootstrap ordering fix and its focused backend unit test.
- FE tests, plans, approvals, sanitized evidence notes and reviewed UI screenshots through Rev51.
- Manager 17-route inventory/test evidence remains in the preceding Rev48 commit and is retained in branch history.

## Verification

- Focused FE suite: 4 files, 18 tests passed.
- FE production build: passed.
- Oxlint: exit 0; 28 React warnings remain.
- Selected BE contract/unit suite: 90 passed.
- Repository security validator: passed; environment files, seed-account files, credentials and signing keys excluded.
- Harness validator: passed.
- Architecture validator: passed.
- Initial diff check found an extra approval EOF blank line; it was removed. Re-run diff check passed with only existing CRLF normalization notices.
- Manager test accounts were password-reset in the dev Firebase project in Rev49. Their credentials remain only in the Git-ignored tmp/qa-test-accounts.local.md and are excluded from this commit.

## Boundaries

- .env, tmp/, credentials, tokens, service-account files, external reference documents and ignored build/runtime artifacts are excluded.
- No application test data, child information or account passwords are included in the staged changes.
- No history rewrite or force push; the result will be one new fast-forward commit containing the current pending worktree changes.
