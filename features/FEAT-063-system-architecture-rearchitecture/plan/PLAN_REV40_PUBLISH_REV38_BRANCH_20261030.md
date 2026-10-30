# Plan Rev40 — publish Rev38 on a branch based on current origin/dev

- Feature: FEAT-063 — whole-repository architecture redesign.
- Status: APPROVED for the path-scoped commit and new-branch push below, under the user's 2026-10-30 direct instruction to commit and push.
- Target branch: `codex/feat063-rev38-ui-mockups-20261030`, based on fetched `origin/dev` (`01b25a7850d1887c67891bfa15e76c52c5c04938`).

## Reason for branch adjustment

After fetching, local `dev` and `origin/dev` diverged: local had 849 commits absent from origin and origin had 498 commits absent locally. Git reported a forced update of `origin/dev`. Updating `origin/dev` from local `dev` would require a force push and could replace remote history. This plan publishes only the Rev38 package as a new branch rooted at current `origin/dev`; it does not rewrite or update `origin/dev`.

## Scope

- Apply only the Rev38 UI package and its FEAT-063 records to a temporary worktree based on current `origin/dev`.
- Include 23 screen drafts, nine component boards, shared artwork, prompts/motion notes, indexes, EV-063-31, Rev38 plan/approval, AC-33 consistency correction, and associated context/decision/source/status/evidence-index records.
- Exclude local Rev37 API outputs and approval, Plan Rev39's abandoned `dev`-branch assumption, pytest temporary files, every other feature's changes, and all pre-existing staged changes.
- Create one commit: `feat(FEAT-063): add Rev38 UI mockup drafts`.
- Push only the new branch `codex/feat063-rev38-ui-mockups-20261030` to `origin`.

## Acceptance criteria

- **AC1 — Safe base:** branch starts at the fetched `origin/dev` commit listed above; do not force-push or alter `origin/dev`.
- **AC2 — Conflict safety:** apply tracked Rev38 edits without silently overwriting remote changes; stop on unresolved conflicts.
- **AC3 — Exact scope:** commit includes only the approved Rev38 paths and approval record; exclude unrelated workspace state.
- **AC4 — Security:** run `python tools/validate_repository_security.py` before commit and again before push; stop if it rejects.
- **AC5 — Verify delivery:** confirm the commit exists on the new remote branch and report its hash and branch.

## Procedure

1. Record this plan hash and the owner's direct commit/push instruction in the feature approval register.
2. Create a temporary worktree at fetched `origin/dev`; apply only Rev38 tracked deltas and copy the new Rev38 files.
3. Review conflicts, exact staged paths, and generated-only asset location; run security validation.
4. Commit the scoped package, run security validation again, push the new branch, and verify the remote ref.

## Excluded

Force-pushing `dev`, merging or rebasing the 849/498 divergent histories, committing unrelated staged/worktree changes, visual promotion, product code/API/schema/database changes, tests/builds, or deployment.
