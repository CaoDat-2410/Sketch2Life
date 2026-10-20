# FEAT-057 decisions

## Integration candidate — 2026-10-20

- Use a new branch, `feature/be2-01-14-integration`, based on the published task-7 integration branch `feature/be2-01-07`.
- Merge the complete `feature/be2-08-14` tip with history preserved; do not squash or cherry-pick the seven card areas.
- Resolve conflicts using current feature plans, approvals, contracts, tests, and source-register authority. Preserve both branch histories and record every material conflict disposition.
- Keep per-card status, acceptance limits, and external gates intact. A passing aggregate offline run is not full-card acceptance or runtime adoption.
- Run offline checks only. Live Lightning/provider work remains deferred until the user confirms Lightning is operating normally and separately requests that campaign.
- Do not merge to `dev`/`main` or claim a PR to `feature/be2-01-07`: that target already contains the source task-7 commit and the PR diff is empty.

## Administrative FEAT number collisions — 2026-10-20

- Preserve the existing feature directory names and all references pinned to them. The independent BE2 allocations reused four administrative FEAT numbers; the exact BE2-to-directory mapping is in `artifacts/FEATURE_ID_COLLISION_MAP.md`.
- Resolve references by BE2 card number plus full directory path. Do not rename reviewed plans, approvals, runners, or evidence as part of this merge.
- The FEAT-030 duplicate already existed in the task-7 baseline and is outside this integration's scope.
