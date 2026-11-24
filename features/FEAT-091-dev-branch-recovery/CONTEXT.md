# FEAT-091 — Dev branch recovery and worktree integration

## Goal

Restore the primary `<LOCAL_ROOT>` checkout to `dev`, update it from the latest available `origin/dev`, and bring the explicitly selected Parent/Modal work from `<LOCAL_ROOT>\.codex-worktrees\fe` (`feature/fe-mobile-remediation`) into that checkout. Preserve the root checkout's current files and the FE worktree's current tracked and untracked changes.

## Constraints

- Commit changes on `dev`; do not push.
- Keep a recoverable local snapshot of both dirty worktrees until integration is verified.
- Preserve source branch history; do not rewrite or force-push the already published `codex/parent-modal-e2e-20261123` branch.
- Split newly integrated local changes into coherent, reviewable commits of moderate size.
- Do not commit `.env`, credentials, provider tokens, service-account keys, or real child data. Keep protected files recoverable and report exclusions.
- Use the FEAT-063 v2.7-draft SRS as current product authority; retain historical records as historical evidence.
- Run repository security validation before every commit. Do not run broad tests unless needed to resolve a concrete integration issue.

## As-found snapshot (2026-11-24; refreshed after fetch)

- Root checkout: `backup/dev-before-dedup-20261106-575139a5`, 472 porcelain entries after adding this feature record; 26 staged paths, 93 unstaged paths, and 5,101 untracked files. Its HEAD does not contain `deployment/modal/srs_v23/video_app.py`.
- Selected worktree: `feature/fe-mobile-remediation` at `77635688`, 117 porcelain entries (72 unstaged tracked paths and 423 untracked files).
- Published source ref: `origin/codex/parent-modal-e2e-20261123` at `77635688`. After fetching, `origin/dev` is `551ed0ba`; the source ref has four commits not in `origin/dev` and `origin/dev` has 43 commits not in the source ref. Git reports multiple merge bases, so use a normal reviewed merge rather than applying a naïve full-range patch.
- The published source ref contains `video_app.py`; `origin/dev` also contains a different, older blob for that path. The worktree has additional uncommitted edits to `video_app.py` (186 insertions, 101 deletions versus its committed copy).
- Root and FE worktree have 23 same-path dirty changes that need explicit conflict review.
- Root untracked paths include five nested `.codex-worktrees/` checkouts and 3,009 files under `features/FEAT-063-system-architecture-rearchitecture/evidence/.pytest-basetemp-rev37-run2/`. These local checkout/test scratch files must remain on disk but stay out of project commits. Other project evidence and feature files remain in scope, subject to repository security validation.

## Plan

1. Record this approved scope and inspect the dirty-path overlap, fetched remote refs, scratch paths, and protected-file candidates.
2. Preserve the root and FE worktree changes with named local recovery snapshots before switching or merging.
3. Fetch `dev` (completed: `origin/dev` advanced from `a43c2aee` to `551ed0ba`); fast-forward the root checkout's `dev` branch to `origin/dev` without discarding history.
4. Integrate `origin/codex/parent-modal-e2e-20261123` into `dev`, retaining its existing commit ancestry and the already published source branch.
5. Reapply the root dirty changes and selected FE worktree dirty changes; resolve overlapping paths using the latest approved FEAT-063 SRS and preserve non-conflicting content.
6. Group local changes into moderate commits by concern (Parent mobile, backend/contracts/migrations, Modal/video workers, Teacher/presentation, SRS/governance, and feature evidence/docs as needed). Keep unrelated historic records in separate coherent commits.
7. Run `python tools/validate_repository_security.py` before each commit; inspect every staged diff and verify no protected values or real child data are staged.
8. Verify the root checkout is on `dev`, all intended changes are committed, source snapshots remain recoverable, and no push occurred. Record commit hashes and any excluded/protected paths in this feature's evidence and status.

## Acceptance criteria

- `<LOCAL_ROOT>` is checked out on `dev`, fast-forwarded to the fetched `origin/dev` when available.
- The selected published Parent/Modal branch and its requested current FE worktree changes are represented on `dev`.
- Root checkout changes are preserved except for files prohibited by repository security rules; any such exclusions are documented.
- New local changes are separated into coherent commits with descriptive conventional messages; no single new commit intentionally bundles the entire integration.
- No push, force-push, or destructive deletion of either source worktree or its recovery snapshot occurs.
- A concise completion record lists commit hashes, validation outcome, and remaining limitations.

## Risks and handling

- Both worktrees are dirty and contain overlapping files. Preserve snapshots first; resolve overlaps by reviewing both versions rather than resetting either tree.
- `origin/dev` may have advanced since the last fetch. Fetch before fast-forward and re-check ancestry.
- The published Codex branch contains an existing large commit. Preserve its history rather than rewriting the published ref; split additional uncommitted integration changes into focused commits.
- Security validation may block specific evidence or configuration files. Keep them in a recovery snapshot and list them; do not weaken the validator.

## Status

APPROVED — owner explicitly authorized moving the root checkout to `dev`, bringing the selected FE worktree changes, creating multiple commits, and not pushing (2026-11-24).
