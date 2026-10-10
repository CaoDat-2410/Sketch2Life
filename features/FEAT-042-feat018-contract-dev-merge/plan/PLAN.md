# Merge FEAT-018 contract branch into dev

- Status: APPROVED
- Plan revision: 1
- Implementation status: DONE
- Date: 2026-10-10, Asia/Saigon

## Goal

Integrate existing codex/feat-018-contract-plan into dev without losing current dev behavior, current SRS authority, branch history or local work.

## Scope

The exact remote source f959426 includes whiteboard/story-video, experimental offline tools and UI modules/assets. Merge committed history, reconcile actual conflicts, correct concrete merge/typecheck/regression failures, and record reproducible evidence. Owner explicitly authorizes branch merge. Existing generated assets are imported from already committed history; no new assets are generated, selected or materially edited. Preserve originals/provenance and approval limitations.

## Steps

1. Pin source/dev/base SHAs, inspect source/context/approvals and perform independent backend, mobile and security reviews.
2. Record this plan and direct task approval before merge. Preserve original workspace/runtime hashes.
3. Merge pinned source with no commit in isolated worktree; resolve conflicts additively, retaining latest dev guards and SRS authority. Record each resolution.
4. Run repository security/harness/architecture and offline backend suite, mobile typecheck/tests and renderer regression checks where changes warrant. Repair concrete failures and rerun affected checks. No provider credentials, GPU/model downloads or live requests.
5. Review exact staged tree and merged history; run security immediately before commit. Commit merge and evidence.
6. Refresh origin/dev and verify non-forced advancement. Run security before push, push dev, verify source is ancestor of remote dev and final remote SHA.
7. Record actual publication outcome, preserve protected original workspace bytes, and retain the isolated worktree while its ignored full diagnostic evidence is needed for review; archive later when those local records are no longer needed.

## Acceptance criteria

- AC01: source identity/pins and explicit approval are recorded before integration.
- AC02: remote dev contains the pinned source history and its prior 396b4f6 history without force or lost commits.
- AC03: every conflict is reviewed; dev improvements, versioned contracts, originals and canonical SRS/task hashes are preserved.
- AC04: security/harness/architecture and relevant offline regression checks pass; environmental skips and unresolved device/provider acceptance are explicit.
- AC05: original workspace's eight pending runtime files and its current branch remain unchanged.
- AC06: evidence, actual remote result, context/decisions/status are recorded in this feature.

## Risks and mitigations

Use isolated checkout, no stash/reset/discard on dirty original workspace. Keep domain/application/adapter boundaries; use existing versioned contracts. Incoming legacy product assumptions do not override SRS v3.1. Pin source and guard against dev advancing; never force. Preserve existing asset history and attribution; this merge does not fabricate visual/device/model acceptance.

## Verification plan

Security before every commit/push. Harness/architecture and Git diff check; backend offline unit/contract suite with explicit CPU dependencies; mobile TypeScript and fixture/copy tests; renderer typecheck/tests if affected. Independent incoming code/security/provenance reviews plus final ancestry/hash verification. No live provider or deployment test claims.

## Evidence plan

Own evidence/raw command logs, metrics pinned refs/hashes/test counts, notes review/conflict/validation/publication records. Sanitize machine paths; never publish raw child media, credentials or provider output.
