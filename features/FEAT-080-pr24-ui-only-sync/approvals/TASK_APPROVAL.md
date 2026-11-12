# FEAT-080 task approval

## PR #24 selective UI sync

- Status: APPROVED for the exact scope in Plan FEAT-080.
- Approver: Project owner, direct instruction on 2026-11-12 to selectively bring UI from dev into the existing feature branch, followed by the clarification to take apps/mobile and apps/ui-mobile from dev, remove the target apps/mobile and FEAT-079, and record recoverability under FEAT-067.
- Recorded date: 2026-11-12, Asia/Saigon.
- Feature: FEAT-080 — PR #24 selective UI sync.
- Approved plan: features/FEAT-080-pr24-ui-only-sync/plan/PLAN.md.
- Plan SHA-256 at authorization: 888F363E5EAD7FBB6C9D66C5AAA1840E26F5403AD9DFFBEF6984FADDA80965D9.
- Scope: copy the approved frontend app snapshots from dev to a temporary local branch based on the existing target branch; remove FEAT-079 from the result tree; preserve commit 4f5d7f5f in target branch history; update only the existing target branch and delete the temporary local branch after verification.
- Acceptance criteria: AC1–AC8 in the hash-identified plan.
- Exclusions: dev updates, backend/server/database/migration/deployment/provider/credential changes, force-push/history rewrite, new remote branch, PR merge, tests, and builds.
- Approval basis: the owner's direct instructions authorize the bounded UI snapshot transfer, normal update of the existing target branch, and deletion of the temporary local branch. They do not authorize changing dev or merging PR #24.