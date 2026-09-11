# P3/P4 offline integration evidence — 2026-09-11

## Scope

Merged the approved offline P3 renderer branch and latest P4 media integration into `codex/feat-018-contract-plan`. P4 was refetched after its follow-up commit and the root replay entrypoint was merged separately. Research-only branches remain outside integration.

## Merge record

- Approval record: `features/FEAT-018-live-image-canvas-flow/approvals/TASK_APPROVAL.md`
- P3 source: `origin/plan/person-3-art-animation-poc` at `68aceeb`; merge commit `2851bb6`.
- P4 source: `origin/feat-018-person-4-media-integration` at `9934a0a`; merge commit `77745c4`.
- P4 follow-up: `ccd1ea5` (`add root replay script entrypoint`); merge commit `da1a369`.
- Working tree after merge/tests: clean.

## Validation

- P3 `pnpm --filter @sketch2life/art-renderer typecheck`: passed.
- P3 `pnpm --filter @sketch2life/art-renderer test`: passed, 6 tests.
- P3 `pnpm --filter @sketch2life/art-renderer build:demo`: passed.
- P4 contract/cache/fallback/scenario/replay suite: passed, 15 tests.
- The P4 replay test now executes the root entrypoint `scripts/replay_learning_media.py` supplied by the latest P4 commit and emits sanitized replay output.

## Boundary

The merge is offline and fixture/replay based. It does not connect live Qwen/ASR producers, Android/mobile UI, production media providers, production assets, or cloud deployment.
