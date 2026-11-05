# Plan Rev50 ? repair duplicate local dev commits and integrate FEAT-063 Modal AI

**Status:** APPROVED / IN PROGRESS
**Date:** 2026-11-06 (Asia/Saigon)
**Feature:** FEAT-063 ? system architecture rearchitecture

## 1. Objective and verified baseline

Repair the local `dev` history without renaming or rewriting retained commits, preserve the user's dirty checkout, and integrate the complete selected Modal AI branch plus its pending AI changes. Preserve the latest FEAT-063 SRS v2.4-draft as the canonical SRS while doing so.

- Local `dev` before repair: `575139a5bc1b64be2c5a611b295e5ce2bc9aeb29`; it is 6 commits ahead and 500 behind `origin/dev`.
- `origin/dev`: `c98701b1e500906f396e773c79ec3bba55db2542`.
- The six local-only commits are all patch-equivalent to commits already in `origin/dev` (`git cherry -v origin/dev dev` marks all six `-`). These local copies are the duplicates; the remote history contains the canonical patches.
- Selected Modal branch: `codex/feat063-modal-backend-completion-20261103`, currently 83 commits beyond `origin/dev`; its existing tip and commit messages will remain unchanged.
- Pending Modal working-tree changes: 269 paths captured in `evidence/DEV_DEDUP_MODAL_PENDING_CHANGE_MANIFEST_20261106.md`, SHA-256 `115D388F7F26D580AC61317421D1B917D9836AD9B345D7C4975EE0441E13CBA5`.
- Six `.pytest-temp-modal-*` scratch directories (30 files) are explicitly excluded from the commit and will be retained in the Modal worktree.
- Latest SRS publication branch: `codex/feat063-srs-v24-asbuilt-20261106`, with two published commits beyond `origin/dev`. The owner has directed that this FEAT-063 SRS is the current standard; it must not be regressed to the older SRS snapshot carried by the Modal branch.

## 2. Approved scope

1. Preserve the original dirty primary checkout and all its staged, unstaged, and untracked work. Record its original `dev` SHA, move that checkout to a named backup branch at the same SHA, and verify its worktree status is unchanged.
2. Move the local `dev` ref to the fetched `origin/dev` base once the backup is in place. Do not rewrite, force-push, amend, rebase, or reword any existing commit.
3. In the Modal worktree, add the required plan/approval/evidence records, run `python tools/validate_repository_security.py`, and commit the 269 manifested pending Modal changes as a new commit with a new descriptive message. Do not add the six scratch directories.
4. Fast-forward local `dev` to include the full Modal branch and its pending-change commit.
5. Merge the already-published FEAT-063 SRS v2.4 branch so the newest SRS remains canonical. Resolve only the documented additive record conflicts (root/feature context and source registers, feature decisions/approvals, Data Table Register, evidence index, and status) while retaining both Modal AI records and the v2.4 authority/as-built records. Preserve the original commits and their messages; add a merge commit if Git requires one.
6. Record the final graph, duplicate-patch audit, backup/worktree preservation check, merge conflict disposition, and security validation in FEAT-063 evidence/context/status.

## 3. Acceptance criteria

- **AC50.1:** Local `dev` no longer contains the six redundant local commit copies; each of their equivalent patches is represented once through the existing `origin/dev` history.
- **AC50.2:** The original dirty checkout is preserved byte-for-byte at the worktree/index level, remains reachable on the backup branch, and is not overwritten or cleaned.
- **AC50.3:** Every pre-existing commit on the selected Modal and SRS branches retains its original commit object and subject; no rebase, amend, cherry-pick, squash, or message rewrite occurs.
- **AC50.4:** The pending Modal changes in the manifest are included; `.pytest-temp-modal-*` remains uncommitted and untouched.
- **AC50.5:** FEAT-063 v2.4-draft remains the canonical SRS in the resulting `dev` tree, and both branches' relevant governance/evidence records are retained.
- **AC50.6:** `python tools/validate_repository_security.py` passes before the new commit. Git ancestry, branch state, patch equivalence, and recorded worktree preservation checks pass. No AI/provider calls or product tests are run.
- **AC50.7:** `origin/dev` is not force-updated or otherwise rewritten. This plan authorizes the local repair and merge; it does not authorize pushing the result.

## 4. Explicit exclusions

No force push or remote history rewrite; no modification to existing commit names/messages; no changes to unrelated dirty work in the primary checkout; no tests, API calls, Modal/GPU calls, deployment, model downloads, `.env`/Secret edits, or real child data; no deletion of pytest scratch directories; no independent feature work beyond preserving the already-published FEAT-063 v2.4 SRS authority.

## 5. Owner approval basis

The project owner directly requested that duplicate commits on `dev` be fixed without changing commit names, and selected the complete Modal AI branch plus pending AI work for integration. The owner also previously designated the newest SRS in FEAT-063 as the canonical standard and authorized its publication. This plan preserves all pre-existing commit subjects/objects, removes only the duplicate local copies from the `dev` ancestry, and carries the already-published SRS v2.4 commits forward.
