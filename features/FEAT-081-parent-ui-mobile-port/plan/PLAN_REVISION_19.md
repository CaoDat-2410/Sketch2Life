# FEAT-081 Plan Revision 19 — synchronize current dev into Parent UI branch

- Status: APPROVED
- Plan revision: 19
- Implementation status: IN_PROGRESS
- Date: 2026-11-19, Asia/Saigon

## Goal

Merge the latest fetched origin/dev into feature/fe-mobile-remediation while retaining the seven feature-only commits and FEAT-081 records.

## Exact inputs

- Target branch: feature/fe-mobile-remediation
- Target starting commit: 5aa9443a772462d247a6018a62aab4e37d2092ae
- Source branch: origin/dev
- Fetched source tip: ba295f1113129fa233ddc762ef29fadd92b996e8
- Common ancestor: 1c9148e88600a101887e477541c4c4893ba1c7df
- Divergence at planning: target has 7 commits not on dev; dev has 16 commits not on target.
- A merge-tree preview found one content conflict: .gitattributes.

## Scope

1. Merge the exact fetched origin/dev tip above into the target branch without rebasing, resetting, squashing, or force-updating either branch.
2. Resolve .gitattributes by retaining every incoming dev rule and the FEAT-081 byte-preservation rules for PLAN_REVISION_5.md and PLAN_REVISION_7.md.
3. Preserve the FEAT-081 feature files that are absent from origin/dev.
4. Record the resulting merge commit and verification limits under FEAT-081 evidence and update its status record.
5. Keep the root checkout, unrelated worktrees, secrets, environment files, runtime services, databases, Firebase, Modal, and Docker untouched.
6. Do not push. This request authorizes local integration only.

## Acceptance criteria

- The merge commit has the starting feature commit and fetched dev tip as its two parents.
- Both tips are ancestors of the resulting target branch.
- No unmerged paths or conflict markers remain; the working tree is clean after recording evidence/status.
- .gitattributes retains the FEAT-081 Rev5/Rev7 preservation rules and all origin/dev additions.
- FEAT-081 Rev5/Rev7 files remain byte-identical to their pre-merge SHA-256 values.
- python tools/validate_repository_security.py passes before the merge commit, as required by repository rules.
- No product tests or runtime/API/AI checks are run; they are outside this merge request and remain unverified.

## Risks

- origin/dev contributes 16 commits and a broad backend, API, SRS, governance, and evidence change set. Auto-merged application/backend changes are integrated but are not runtime-validated here.
- The only merge-tree conflict is .gitattributes; losing either side's rules could alter byte-preservation behavior on later edits.
- No push is authorized, so the remote feature branch will remain unchanged.

## Evidence

- evidence/DEV_SYNC_20261119.md
- The approval for this exact plan revision is appended as Addendum 34 in approvals/TASK_APPROVAL.md.