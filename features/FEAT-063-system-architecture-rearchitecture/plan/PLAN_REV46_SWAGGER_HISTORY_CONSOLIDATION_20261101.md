# Plan Rev46 — Consolidate Swagger commits on `dev`

## Status

- Lifecycle: APPROVED for the exact local commit and `origin/dev` history update below.
- Feature: FEAT-063 — whole-repository architecture redesign.
- Branch: `dev`.
- Date: 2026-11-01, Asia/Saigon.

## Goal

Commit the completed SRS v2.2 Swagger update and remove the two prior Swagger commits as separate commits at the tip of `dev` by replacing them with one consolidated commit. Preserve their relevant current Swagger implementation and the merge commit that is their parent. Update `origin/dev` only if the expected remote tip is still unchanged.

## Exact history scope

- Current local and remote tip: `6d77d2ad41370f118386d9861fed4cd031ddea67` — `feat(swagger): clarify FE-facing OpenAPI contract`.
- Prior Swagger commit: `f68ed2b579c89e8fb1ee3dcf7e4c8f109acd31d8` — `feat(api-docs): align Swagger with FEAT-063 contract`.
- Parent retained as the new commit base: `111ae547007801d7d171dd12f3ac6f1085d22199` — merge of `dev`.
- `origin/dev` was verified at the same current tip before this plan.

## Scope

1. Include the current SRS v2.2 Swagger projection, its implementation, focused OpenAPI contract expectation updates, and FEAT-063 Plan Rev45/context/decision/source/evidence records.
2. Include this Plan Rev46 and its approval/history evidence in the consolidated commit.
3. Replace only the two identified tip commits with one new commit whose parent is `111ae547007801d7d171dd12f3ac6f1085d22199`.
4. Update `origin/dev` using `git push --force-with-lease` with expected old tip `6d77d2ad41370f118386d9861fed4cd031ddea67`.
5. Preserve unrelated branches and all commits at or below the retained merge parent. Keep the committed Swagger implementation/artifacts needed for the current FE-facing documentation and source contract.

## Acceptance criteria

- AC1: Repository security validation passes before commit; whitespace and targeted Ruff checks pass.
- AC2: One consolidated Swagger commit contains the approved SRS v2.2 FE OpenAPI snapshot and relevant source/governance records.
- AC3: New commit's parent is exactly `111ae547007801d7d171dd12f3ac6f1085d22199`; neither `f68ed2b5` nor `6d77d2ad` is an ancestor of `dev` after the rewrite.
- AC4: Force-with-lease updates `origin/dev` only when its current ref is exactly `6d77d2ad41370f118386d9861fed4cd031ddea67`; remote and local `dev` end at the same new commit.
- AC5: `/docs` and `/openapi.json` remain available with the SRS v2.2 projection (24 operations, 17 paths, four tags), matching the committed snapshot.
- AC6: Backend test suites are not run. No other branch or application/runtime behavior is changed.

## Explicit exclusions

- No deletion or rewrite of commits other than the two exact Swagger commits listed above.
- No API route, handler, authorization, payload, database, provider, deployment, or test-suite changes.
- No merge of unrelated feature branches.

## Procedure

1. Review the complete worktree diff and exact two-commit tip; confirm the remote tip again before rewriting.
2. Run required repository security validation, targeted Ruff, OpenAPI export/parity, and whitespace checks; do not run backend tests.
3. Stage only the Swagger task work, then create one consolidated commit on the retained merge parent.
4. Verify the new parent and operation inventory, then force-with-lease against the exact expected remote tip.
5. Verify `dev` and `origin/dev` match and the removed commits are no longer in the branch ancestry; record commit and push evidence.

## Risk control

The update rewrites the public `dev` branch tip. The force-with-lease expected-old value prevents replacing any concurrent remote update. The change is limited to the two named tip commits and their consolidated replacement; no force push is attempted if the remote tip changes.
