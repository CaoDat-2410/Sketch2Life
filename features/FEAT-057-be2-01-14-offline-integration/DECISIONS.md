# FEAT-057 decisions

## Integration candidate — 2026-10-20

- Use a new branch, `feature/be2-01-14-integration`, based on the published task-7 integration branch `feature/be2-01-07`.
- Merge the complete `feature/be2-08-14` tip with history preserved; do not squash or cherry-pick the seven card areas.
- Resolve conflicts using current feature plans, approvals, contracts, tests, and source-register authority. Preserve both branch histories and record every material conflict disposition.
- Keep per-card status, acceptance limits, and external gates intact. A passing aggregate offline run is not full-card acceptance or runtime adoption.
- Run offline checks only. Live Lightning/provider work remains deferred until the user confirms Lightning is operating normally and separately requests that campaign.
- Do not merge to `dev`/`main` or claim a PR to `feature/be2-01-07`: that target already contains the source task-7 commit and the PR diff is empty.

## Integration branch name — 2026-10-20

- Following the owner's instruction, rename the local candidate branch from
  `feature/be2-01-14-integration` to `feature/be2-backend-ai-integration`.
- This is a naming-only change: preserve the same commit history, integration
  scope, evidence, and open acceptance/runtime gates.

## Administrative FEAT number collisions — 2026-10-20

- Preserve the existing feature directory names and all references pinned to them. The independent BE2 allocations reused four administrative FEAT numbers; the exact BE2-to-directory mapping is in `artifacts/FEATURE_ID_COLLISION_MAP.md`.
- Resolve references by BE2 card number plus full directory path. Do not rename reviewed plans, approvals, runners, or evidence as part of this merge.
- The FEAT-030 duplicate already existed in the task-7 baseline and is outside this integration's scope.

## Primary-session handoff synchronization — 2026-10-20

- Continue the existing approved FEAT-057 offline integration allocation; the
  handoff-sync request does not expand runtime, install, DB or acceptance scope.
- Keep exact old matrix/report snapshots under evidence/raw/handoff-sync-20261020;
  retain every per-card recheck receipt and label the latest environment blockers.
- F057-H01: after reproducing the real graph assertion failure, scope the
  foundation migration test to its exact owned head sets. Preserve test IDs,
  case count, skip rules and lineage checks. No product/migration source change;
  preserve the original foundation worktree and frozen A17 bytes.
- Old full source maps remain historical after the single uncommitted test delta;
  fresh focused evidence does not claim a complete 01–14 pack or runtime PASS.
- Main handoff: evidence/notes/PRIMARY_SESSION_HANDOFF_20261020.md. No per-card
  status/approval/acceptance change; no installation or Git publication.

## Offline environment gate — 2026-10-20

- Keep the shared backend venv read-only. Its missing Pillow and python-multipart prevent a complete 08–14 component pack.
- Do not create or install the candidate-local venv until the separately requested owner authorization arrives.
- The requested profile is the backend editable install with dev and image-admission extras only; do not add model/GPU extras or weights.
- Until prerequisites are complete, keep all runner results source-bound to the prior receipt and label this candidate snapshot NOT_RUN/ENVIRONMENT_BLOCKED. Do not mark cards DONE or the batch PASS.

## Offline environment gate resolution — 2026-10-20

- The user's explicit reply “Authorize isolated venv install” is recorded in
  `approvals/LOCAL_ENVIRONMENT_APPROVAL_20261020.md` and supersedes the pending
  install gate above for this integration worktree only.
- Install the backend editable `.[dev,image-admission]` profile into the
  ignored candidate-local `backend/.venv`; leave the shared environment alone.
- Resolve to the package versions captured in the FEAT-057 pre-run inventory:
  Python 3.12.10, pytest 8.4.2, Ruff 0.16.4, mypy 1.20.2, Pydantic 2.13.4,
  SQLAlchemy 2.0.52, Alembic 1.19.1, plus the newly available Pillow,
  python-multipart, and AV 18.1.0 dependencies. Do not install model/GPU
  extras or weights.
- The first unpinned resolution selected newer Pydantic and caused one mypy
  type-check failure in BE2-12. Reproduce it, align to the recorded versions,
  and rerun the exact component pack. The final pinned pack passes without a
  product-source change.
- Preserve SQL collection-only boundaries and all card approval, acceptance,
  and status records. Offline component PASS is not full-card or runtime PASS.
