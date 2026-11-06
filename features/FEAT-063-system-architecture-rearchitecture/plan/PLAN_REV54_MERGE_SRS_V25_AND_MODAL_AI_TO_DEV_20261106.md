# FEAT-063 Plan Rev54 - merge SRS v2.5 and Modal AI reliability into dev

**Date:** 2026-11-06 (Asia/Saigon)

**Lifecycle:** APPROVED for the exact integration scope below by the project owner's direct request: merge the SRS and AI branches into `dev`.
**Feature:** FEAT-063 - system architecture rearchitecture.

## Inputs and starting point

- Destination starting commit: local `dev` at `0fc773fafeb6f5443538f283cb891c67d379d9c6`; this is one commit ahead of `origin/dev` at `4749451080f49243464d40a464b8f83a03ae77bb` and is an ancestor of the AI branch.
- SRS branch: `origin/docs/feat063-rev45-srs-code-alignment-20261106` at `fae180dcf3ea2771b41546aa6925b94636821df1`. Alias `origin/docs/feat063-srs-conflict-remediation-20261106` points to the same commit.
- AI branch: `origin/feature/feat063-modal-ai-reliability-20261106` at `c6818490d0d889ab17dc9f8de3830987eb2a230d`.
- Merge base of the two source branches: `4749451080f49243464d40a464b8f83a03ae77bb`.
- Product SRS carried by the SRS branch: FEAT-063 v2.5-draft. It remains unsigned; merging it changes the canonical working pointer and does not constitute product sign-off.

## Goal

Integrate both already-published branches into `dev`, retaining their original commits and content. The AI branch contains Rev52 reliability fixes and Rev53 SAM2 gate retest. The SRS branch publishes the reviewed v2.5-draft and its source-alignment records.

## Approved procedure

1. Create this integration plan and record the owner's approval before integrating source commits.
2. Build on a temporary integration branch from the current local `dev` commit. Fast-forward to the AI branch, which already descends from that `dev` commit.
3. Merge the SRS branch by a regular merge. Resolve only the two known approval-register conflicts by retaining both branches' complete approval histories; preserve each original source commit and message.
4. Record the merge, exact branch/commit IDs, conflict resolution, authority transition to unsigned v2.5-draft, AI test evidence, and SAM2 product-disabled status in FEAT-063 context/source/status/evidence records.
5. Review the merged path list and SRS authority pointers. Run `git diff --check` and `python tools/validate_repository_security.py` before each commit and push. Reuse branch test evidence; this integration task does not add or rerun product tests.
6. Fast-forward local `dev` to the reviewed integration tip, push normally to `origin/dev`, fetch, and verify the remote hash equals local `dev`.

## Acceptance criteria

- **AC54.1 - Exact inputs:** integrate the two branch tips recorded above; do not include the unrelated BE foundation branch or other worktrees.
- **AC54.2 - SRS integrity:** v2.5-draft and its matching Data Table Register are byte-preserved from the reviewed SRS branch; `AGENTS.md` and `docs/context/SRS_AUTHORITY.md` point to v2.5-draft. The SRS remains a draft without sign-off.
- **AC54.3 - AI integrity:** preserve all AI branch commits, code, tests, SAM2 evidence, worker registry status, and original commit authors/messages. `drawing.segment` remains disabled in the product registry.
- **AC54.4 - Conflict resolution:** only the root and FEAT-063 approval registers require manual resolution; retain every entry from both sides and append this integration authorization/closeout without rewriting history.
- **AC54.5 - Scope control:** no AI/API/schema/database/provider/runtime changes beyond those already committed on the selected AI branch; no unrelated branch commits or files.
- **AC54.6 - Validation:** clean whitespace, passing repository security validator, and an explicit review of the two approval-file resolutions and final changed paths.
- **AC54.7 - Publication:** normal fast-forward push to `origin/dev`; remote `dev` must match the final local `dev` commit. No force push or history rewrite.

## Exclusions and evidence limits

- No owner sign-off of the v2.5 SRS, production activation, video inference, new Modal calls, database migration, or unrelated feature merge.
- No claim that SAM2 is product-ready: Rev53's worker call passed, while its synthetic mask quality was partial; keep the product workload disabled.
- AI verification is inherited from the selected branch evidence: 100 Modal tests passed for Rev53, plus the Rev52 backend/Modal results. No suite is rerun as part of this documentation/history integration request.
- The SRS publication branch was originally approved to publish a feature branch, not `dev`; the owner's current direct instruction authorizes this separate integration and normal `dev` publication scope.
